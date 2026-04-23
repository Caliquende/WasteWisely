import argparse
import ctypes
import logging
import logging.handlers
import os
import shutil
import sys
import tempfile
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox

LOG_FILENAME = "wastewisely_installer_debug.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
EVENT_SOURCE = "WasteWiselyInstaller"
APP_NAME = "WasteWisely"
APP_EXE_NAME = "WasteWisely.exe"
SHORTCUT_NAME = "WasteWisely.lnk"
import subprocess


def resolve_log_path(log_name: str) -> Path:
    base_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or tempfile.gettempdir()
    return Path(base_dir) / APP_NAME / "logs" / log_name


def configure_logging() -> None:
    handlers = []
    try:
        log_path = resolve_log_path(LOG_FILENAME)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    except OSError:
        handlers.append(logging.StreamHandler(sys.stderr))

    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
        handlers=handlers,
        force=True,
    )


configure_logging()

try:
    nt_handler = logging.handlers.NTEventLogHandler(EVENT_SOURCE)
    nt_handler.setLevel(logging.ERROR)
    nt_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(nt_handler)
except Exception:
    pass


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught installer exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


class InstallError(RuntimeError):
    """Installer domain error."""


@dataclass
class InstallResult:
    install_dir: Path
    exe_path: Path
    shortcut_path: Path | None


def detect_existing_install(install_dir: str | Path) -> bool:
    target_dir = Path(install_dir).expanduser().resolve()
    return (target_dir / APP_EXE_NAME).exists()


def is_admin():
    if os.environ.get("WW_SKIP_ADMIN_CHECK") == "1":
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def default_install_dir() -> Path:
    base_dir = Path(os.environ.get("ProgramFiles") or "C:\\Program Files")
    return base_dir / APP_NAME


def resolve_desktop_dir() -> Path:
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        return Path(user_profile) / "Desktop"
    return Path.home() / "Desktop"


def protected_install_roots() -> list[Path]:
    env_names = ("ProgramFiles", "ProgramW6432", "CommonProgramFiles", "SystemRoot", "windir")
    roots = []
    for env_name in env_names:
        value = os.environ.get(env_name)
        if value:
            roots.append(Path(value))
    return roots


def path_requires_admin(install_dir: Path) -> bool:
    install_path = install_dir.resolve()
    for root in protected_install_roots():
        try:
            resolved_root = root.resolve()
        except OSError:
            continue
        if install_path == resolved_root or resolved_root in install_path.parents:
            return True
    return False


def resolve_bundled_app() -> Path:
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / APP_EXE_NAME)

    script_dir = Path(__file__).resolve().parent
    candidates.append(script_dir / "dist" / APP_EXE_NAME)
    candidates.append(Path("dist") / APP_EXE_NAME)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def write_silent_error(message: str) -> None:
    logging.error(message)
    if sys.stderr is not None:
        sys.stderr.write(f"{message}\n")


def stop_running_app(exe_path: Path) -> None:
    """Uygulama calisiyorsa zorla kapatir."""
    if os.name != "nt":
        return
    
    if not exe_path.exists():
        return

    binary_name = exe_path.name
    escaped_path = str(exe_path.resolve()).replace("'", "''")
    
    # PowerShell ile spesifik path'teki executable'i bul ve kapat
    command = (
        f"$target = [System.IO.Path]::GetFullPath('{escaped_path}');"
        f"$procs = Get-CimInstance Win32_Process -Filter \"Name='{binary_name}'\" -ErrorAction SilentlyContinue | "
        "Where-Object { $_.ExecutablePath -and ([System.IO.Path]::GetFullPath($_.ExecutablePath) -eq $target) };"
        "if ($procs) { $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force } }"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Kapanmasi icin cok kisa bir sure bekle
        import time
        time.sleep(0.5)
    except Exception as e:
        logging.warning(f"Uygulama kapatilamadi: {e}")

def create_desktop_shortcut(dest_exe: Path, desktop_dir: Path | None = None) -> Path:
    import win32com.client

    desktop = desktop_dir or resolve_desktop_dir()
    desktop.mkdir(parents=True, exist_ok=True)
    shortcut_path = desktop / SHORTCUT_NAME
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.Targetpath = str(dest_exe)
    shortcut.WorkingDirectory = str(dest_exe.parent)
    shortcut.IconLocation = str(dest_exe)
    shortcut.save()
    return shortcut_path


def remove_existing_install(install_dir: str | Path, desktop_dir: str | Path | None = None) -> list[Path]:
    target_dir = Path(install_dir).expanduser().resolve()
    removed = []

    dest_exe = target_dir / APP_EXE_NAME
    if dest_exe.exists():
        stop_running_app(dest_exe)
        dest_exe.unlink()
        removed.append(dest_exe)

    shortcut_dir = Path(desktop_dir).expanduser().resolve() if desktop_dir else resolve_desktop_dir()
    shortcut_path = shortcut_dir / SHORTCUT_NAME
    if shortcut_path.exists():
        shortcut_path.unlink()
        removed.append(shortcut_path)

    if target_dir.exists() and not any(target_dir.iterdir()):
        target_dir.rmdir()
        removed.append(target_dir)

    return removed


def install(
    install_dir: str | Path | None = None,
    *,
    create_shortcut: bool = True,
    desktop_dir: str | Path | None = None,
    remove_existing: bool = False,
    silent: bool = False,
) -> InstallResult:
    target_dir = Path(install_dir) if install_dir else default_install_dir()
    target_dir = target_dir.expanduser().resolve()
    source_exe = resolve_bundled_app()

    if path_requires_admin(target_dir) and not is_admin():
        raise InstallError(
            f"Seçilen hedef yönetici izni gerektiriyor: {target_dir}"
        )

    if not source_exe.exists():
        raise InstallError(f"Kaynak dosya bulunamadı: {source_exe}")

    if remove_existing and detect_existing_install(target_dir):
        remove_existing_install(target_dir, desktop_dir)

    target_dir.mkdir(parents=True, exist_ok=True)
    dest_exe = target_dir / APP_EXE_NAME

    if dest_exe.exists():
        stop_running_app(dest_exe)

    logging.info("Installing %s to %s", source_exe, dest_exe)
    shutil.copy2(source_exe, dest_exe)

    shortcut_path = None
    if create_shortcut:
        shortcut_path = create_desktop_shortcut(
            dest_exe,
            Path(desktop_dir).expanduser().resolve() if desktop_dir else None,
        )

    return InstallResult(
        install_dir=target_dir,
        exe_path=dest_exe,
        shortcut_path=shortcut_path,
    )


class InstallerWizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WasteWisely Kurulum Sihirbazı")
        self.root.geometry("620x360")
        self.root.resizable(False, False)

        icon_path = self._get_resource_path("assets/icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self.root.eval("tk::PlaceWindow . center")

        self.install_dir_var = tk.StringVar(value=str(default_install_dir()))
        self.create_shortcut_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Kurulum hedefini seçin.")
        self.existing_install_var = tk.StringVar(value="")
        self.step_index = 0
        self.frames = []
        self.back_btn = None
        self.next_btn = None
        self.remove_existing_btn = None

        self._build_ui()
        self.install_dir_var.trace_add("write", self._on_install_dir_changed)
        self.refresh_existing_install_notice()
        self._show_step(0)

    def _build_ui(self):
        container = tk.Frame(self.root, padx=24, pady=20)
        container.pack(fill="both", expand=True)

        self.frames = [
            self._build_welcome_step(container),
            self._build_location_step(container),
            self._build_summary_step(container),
        ]

        footer = tk.Frame(self.root, padx=24, pady=16)
        footer.pack(fill="x", side="bottom")

        self.back_btn = tk.Button(footer, text="Geri", command=self.go_back, width=12)
        self.back_btn.pack(side="left")

        self.next_btn = tk.Button(
            footer,
            text="İleri",
            command=self.go_next,
            width=12,
            bg="#0ea5e9",
            fg="white",
        )
        self.next_btn.pack(side="right")

    def _build_welcome_step(self, parent):
        frame = tk.Frame(parent)
        tk.Label(
            frame,
            text="WasteWisely Kurulum Sihirbazına Hoş Geldiniz",
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", pady=(0, 16))
        tk.Label(
            frame,
            text=(
                "Bu sihirbaz WasteWisely uygulamasını kullanıcı hesabınıza kurar.\n"
                "Varsayılan hedef dizin kullanıcı-yazılabilir bir konumdur; isterseniz değiştirebilirsiniz."
            ),
            justify="left",
            font=("Segoe UI", 11),
        ).pack(anchor="w")
        return frame

    def _build_location_step(self, parent):
        frame = tk.Frame(parent)
        tk.Label(frame, text="Kurulum Konumu", font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0, 12))
        tk.Label(
            frame,
            text="Kurulum klasörünü seçin. Önerilen varsayılan yol yönetici izni gerektirmez.",
            justify="left",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(0, 12))

        path_row = tk.Frame(frame)
        path_row.pack(fill="x", pady=(0, 12))
        tk.Entry(path_row, textvariable=self.install_dir_var, font=("Segoe UI", 10)).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 8),
        )
        tk.Button(path_row, text="Gözat...", command=self.browse_install_dir, width=12).pack(side="right")

        tk.Checkbutton(
            frame,
            text="Masaüstüne kısayol oluştur",
            variable=self.create_shortcut_var,
            font=("Segoe UI", 10),
        ).pack(anchor="w")

        tk.Label(
            frame,
            textvariable=self.existing_install_var,
            justify="left",
            fg="#b45309",
            font=("Segoe UI", 10),
            wraplength=560,
        ).pack(anchor="w", pady=(16, 8))

        self.remove_existing_btn = tk.Button(
            frame,
            text="Mevcut Kurulumu Kaldır",
            command=self.remove_existing_install_from_ui,
            width=22,
            state="disabled",
        )
        self.remove_existing_btn.pack(anchor="w")
        return frame

    def _build_summary_step(self, parent):
        frame = tk.Frame(parent)
        tk.Label(frame, text="Kurulum Özeti", font=("Segoe UI", 15, "bold")).pack(anchor="w", pady=(0, 12))
        tk.Label(
            frame,
            textvariable=self.status_var,
            justify="left",
            font=("Segoe UI", 10),
            wraplength=560,
        ).pack(anchor="w")
        return frame

    def _show_step(self, index: int):
        self.step_index = index
        for i, frame in enumerate(self.frames):
            if i == index:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

        self.back_btn.config(state="normal" if index > 0 else "disabled")
        if index < len(self.frames) - 1:
            self.next_btn.config(text="İleri")
            if index == len(self.frames) - 2:
                self.next_btn.config(text="Kur")
        else:
            self.next_btn.config(text="Kapat")

        if index == 2:
            shortcut_text = "Evet" if self.create_shortcut_var.get() else "Hayır"
            self.status_var.set(
                f"Kurulum klasörü:\n{Path(self.install_dir_var.get()).expanduser()}\n\n"
                f"Masaüstü kısayolu: {shortcut_text}\n\n"
                "Kurulum başlatılınca uygulama dosyaları seçilen klasöre kopyalanacak."
            )

    def browse_install_dir(self):
        current = Path(self.install_dir_var.get()).expanduser()
        initial = current if current.exists() else current.parent
        chosen = filedialog.askdirectory(
            title="Kurulum klasörünü seçin",
            initialdir=str(initial),
            mustexist=False,
        )
        if chosen:
            self.install_dir_var.set(chosen)

    def _on_install_dir_changed(self, *_args):
        self.refresh_existing_install_notice()

    def refresh_existing_install_notice(self):
        install_dir = Path(self.install_dir_var.get()).expanduser()
        exists = detect_existing_install(install_dir)
        if exists:
            self.existing_install_var.set(
                "Bu klasörde mevcut bir WasteWisely kurulumu bulundu. İsterseniz yeniden kurmadan önce kaldırabilirsiniz."
            )
            self.remove_existing_btn.config(state="normal")
        else:
            self.existing_install_var.set("Seçilen klasörde mevcut bir WasteWisely kurulumu bulunmadı.")
            self.remove_existing_btn.config(state="disabled")

    def remove_existing_install_from_ui(self):
        install_dir = Path(self.install_dir_var.get()).expanduser()
        if not detect_existing_install(install_dir):
            self.refresh_existing_install_notice()
            return

        confirmed = messagebox.askyesno(
            "Kurulumu Kaldır",
            f"{install_dir} altındaki mevcut WasteWisely dosyaları silinsin mi?",
        )
        if not confirmed:
            return

        try:
            removed = remove_existing_install(install_dir)
        except Exception as exc:
            logging.error("Remove existing install failed", exc_info=exc)
            messagebox.showerror("Kaldırma Hatası", f"Detay:\n{exc}")
            return

        removed_text = "\n".join(str(path) for path in removed) or "Silinecek dosya bulunamadı."
        messagebox.showinfo("Kaldırma Tamamlandı", removed_text)
        self.refresh_existing_install_notice()

    def go_back(self):
        if self.step_index > 0:
            self._show_step(self.step_index - 1)

    def go_next(self):
        if self.step_index < len(self.frames) - 2:
            self._show_step(self.step_index + 1)
            return

        if self.step_index == len(self.frames) - 2:
            self.perform_install()
            return

        self.root.destroy()

    def perform_install(self):
        install_dir = Path(self.install_dir_var.get()).expanduser()
        if not str(install_dir).strip():
            messagebox.showerror("Hata", "Lütfen bir kurulum klasörü seçin.")
            return

        try:
            result = install(
                install_dir=install_dir,
                create_shortcut=self.create_shortcut_var.get(),
                remove_existing=False,
                silent=False,
            )
        except InstallError as exc:
            messagebox.showerror("Kurulum Hatası", str(exc))
            return
        except Exception as exc:
            logging.error("Installer UI failure", exc_info=exc)
            messagebox.showerror("Kurulum Hatası", f"Detay:\n{exc}")
            return

        shortcut_text = (
            f"\nMasaüstü kısayolu: {result.shortcut_path}" if result.shortcut_path else ""
        )
        self.status_var.set(
            f"Kurulum tamamlandı.\n\nUygulama: {result.exe_path}{shortcut_text}"
        )
        self._show_step(len(self.frames) - 1)
        self.back_btn.config(state="disabled")
        self.next_btn.config(text="Kapat")

    def run(self):
        self.root.mainloop()

    def _get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)


def launch_gui():
    InstallerWizard().run()


def main(argv=None):
    parser = argparse.ArgumentParser(description="WasteWisely installer")
    parser.add_argument("--silent", action="store_true", help="GUI olmadan kurulumu baslat")
    parser.add_argument("--install-dir", help="Kurulum klasoru")
    parser.add_argument("--desktop-dir", help="Kisayolun olusturulacagi masaustu klasoru")
    parser.add_argument(
        "--no-desktop-shortcut",
        action="store_true",
        help="Masaustu kisayolu olusturma",
    )
    parser.add_argument(
        "--remove-existing",
        action="store_true",
        help="Kurulumdan once ayni klasordeki mevcut WasteWisely dosyalarini sil",
    )
    args = parser.parse_args(argv)

    if args.silent:
        try:
            install(
                install_dir=args.install_dir,
                create_shortcut=not args.no_desktop_shortcut,
                desktop_dir=args.desktop_dir,
                remove_existing=args.remove_existing,
                silent=True,
            )
        except InstallError as exc:
            write_silent_error(f"Kurulum Hatası: {exc}")
            raise SystemExit(1)
        except Exception as exc:
            logging.error("Silent installer failure", exc_info=exc)
            write_silent_error(f"Kurulum Hatası: {exc}")
            raise SystemExit(1)
        raise SystemExit(0)

    launch_gui()


if __name__ == "__main__":
    main()
