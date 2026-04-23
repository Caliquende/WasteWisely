from pathlib import Path
import sys
import types

import pytest

import installer


def _install_bundle(tmp_path):
    bundle_dir = tmp_path / "bundle"
    source_exe = bundle_dir / "WasteWisely.exe"
    source_exe.parent.mkdir(parents=True)
    source_exe.write_text("binary", encoding="utf-8")
    return bundle_dir


def _install_env(tmp_path, monkeypatch):
    local_app_data = tmp_path / "LocalAppData"
    program_files = tmp_path / "Program Files"
    user_profile = tmp_path / "User"
    desktop = user_profile / "Desktop"
    desktop.mkdir(parents=True)

    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setenv("ProgramFiles", str(program_files))
    monkeypatch.setenv("USERPROFILE", str(user_profile))

    return {
        "local_app_data": local_app_data,
        "program_files": program_files,
        "user_profile": user_profile,
        "desktop": desktop,
    }


def _patch_shortcut_creation(monkeypatch):
    shortcut_state = {}

    class FakeShortcut:
        def __init__(self, shortcut_path):
            self.shortcut_path = shortcut_path
            self.Targetpath = None
            self.WorkingDirectory = None
            self.IconLocation = None

        def save(self):
            shortcut_state["path"] = self.shortcut_path
            shortcut_state["target"] = self.Targetpath
            shortcut_state["working_directory"] = self.WorkingDirectory
            shortcut_state["icon"] = self.IconLocation
            shortcut_state["saved"] = True
            Path(self.shortcut_path).write_text("shortcut", encoding="utf-8")

    class FakeShell:
        def CreateShortCut(self, shortcut_path):
            shortcut_state["created_path"] = shortcut_path
            shortcut_state["saved"] = False
            return FakeShortcut(shortcut_path)

    dispatch_calls = []
    fake_client = types.SimpleNamespace(
        Dispatch=lambda name: dispatch_calls.append(name) or FakeShell()
    )
    fake_win32com = types.SimpleNamespace(client=fake_client)

    monkeypatch.setitem(sys.modules, "win32com", fake_win32com)
    monkeypatch.setitem(sys.modules, "win32com.client", fake_client)

    return dispatch_calls, shortcut_state


def test_installer_resolve_log_path_prefers_localappdata(monkeypatch, tmp_path):
    local_app_data = tmp_path / "LocalAppData"

    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.delenv("TEMP", raising=False)

    assert installer.resolve_log_path("wastewise_installer_debug.log") == (
        local_app_data / "WasteWisely" / "logs" / "wastewise_installer_debug.log"
    )


def test_default_install_dir_uses_localappdata_programs(monkeypatch, tmp_path):
    local_app_data = tmp_path / "LocalAppData"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    assert installer.default_install_dir() == local_app_data / "Programs" / "WasteWisely"


def test_install_defaults_to_localappdata_without_requiring_admin(tmp_path, monkeypatch):
    bundle_dir = _install_bundle(tmp_path)
    env = _install_env(tmp_path, monkeypatch)
    dispatch_calls, shortcut_state = _patch_shortcut_creation(monkeypatch)

    monkeypatch.setattr(installer, "is_admin", lambda: False, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_dir), raising=False)

    result = installer.install()

    install_dir = env["local_app_data"] / "Programs" / "WasteWisely"
    dest_exe = install_dir / "WasteWisely.exe"
    shortcut_path = env["desktop"] / "WasteWisely.lnk"

    assert result.install_dir == install_dir
    assert result.exe_path == dest_exe
    assert result.shortcut_path == shortcut_path
    assert dest_exe.read_text(encoding="utf-8") == "binary"
    assert not (env["program_files"] / "WasteWisely" / "WasteWisely.exe").exists()
    assert dispatch_calls == ["WScript.Shell"]
    assert shortcut_state == {
        "created_path": str(shortcut_path),
        "path": str(shortcut_path),
        "target": str(dest_exe),
        "working_directory": str(install_dir),
        "icon": str(dest_exe),
        "saved": True,
    }


def test_install_uses_explicit_install_dir_and_can_skip_shortcut(tmp_path, monkeypatch):
    bundle_dir = _install_bundle(tmp_path)
    _install_env(tmp_path, monkeypatch)
    custom_install_dir = tmp_path / "Apps" / "WasteWisely Custom"

    monkeypatch.setattr(installer, "is_admin", lambda: False, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_dir), raising=False)

    result = installer.install(
        install_dir=custom_install_dir,
        create_shortcut=False,
    )

    dest_exe = custom_install_dir / "WasteWisely.exe"
    assert result.install_dir == custom_install_dir.resolve()
    assert result.exe_path == dest_exe.resolve()
    assert result.shortcut_path is None
    assert dest_exe.read_text(encoding="utf-8") == "binary"


def test_install_raises_error_when_source_exe_is_missing(tmp_path, monkeypatch):
    _install_env(tmp_path, monkeypatch)
    missing_source = tmp_path / "missing" / "WasteWisely.exe"

    monkeypatch.setattr(installer, "is_admin", lambda: False, raising=False)
    monkeypatch.setattr(installer, "resolve_bundled_app", lambda: missing_source)

    with pytest.raises(installer.InstallError) as exc_info:
        installer.install()

    assert "Kaynak dosya bulunamadı" in str(exc_info.value)


def test_install_requires_admin_only_for_protected_paths(tmp_path, monkeypatch):
    bundle_dir = _install_bundle(tmp_path)
    env = _install_env(tmp_path, monkeypatch)
    protected_target = env["program_files"] / "WasteWisely"

    monkeypatch.setattr(installer, "is_admin", lambda: False, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_dir), raising=False)

    with pytest.raises(installer.InstallError) as exc_info:
        installer.install(install_dir=protected_target)

    assert "yönetici izni gerektiriyor" in str(exc_info.value)


def test_remove_existing_install_deletes_installed_exe_shortcut_and_empty_dir(tmp_path, monkeypatch):
    env = _install_env(tmp_path, monkeypatch)
    install_dir = env["local_app_data"] / "Programs" / "WasteWisely"
    install_dir.mkdir(parents=True)
    dest_exe = install_dir / "WasteWisely.exe"
    dest_exe.write_text("binary", encoding="utf-8")
    shortcut_path = env["desktop"] / "WasteWisely.lnk"
    shortcut_path.write_text("shortcut", encoding="utf-8")

    removed = installer.remove_existing_install(install_dir)

    assert removed == [dest_exe, shortcut_path, install_dir]
    assert not dest_exe.exists()
    assert not shortcut_path.exists()
    assert not install_dir.exists()


def test_main_runs_silent_install_with_explicit_options_without_launching_gui(monkeypatch, tmp_path):
    calls = []
    custom_install_dir = tmp_path / "Silent Install"
    custom_desktop_dir = tmp_path / "Desktop"

    monkeypatch.setattr(
        installer,
        "install",
        lambda **kwargs: calls.append(kwargs) or installer.InstallResult(
            install_dir=Path(kwargs["install_dir"]),
            exe_path=Path(kwargs["install_dir"]) / "WasteWisely.exe",
            shortcut_path=Path(kwargs["desktop_dir"]) / "WasteWisely.lnk",
        ),
    )
    monkeypatch.setattr(installer, "launch_gui", lambda: calls.append("gui"))

    with pytest.raises(SystemExit) as exc_info:
        installer.main(
            [
                "--silent",
                "--install-dir",
                str(custom_install_dir),
                "--desktop-dir",
                str(custom_desktop_dir),
                "--remove-existing",
                "--no-desktop-shortcut",
            ]
        )

    assert exc_info.value.code == 0
    assert calls == [
        {
            "install_dir": str(custom_install_dir),
            "create_shortcut": False,
            "desktop_dir": str(custom_desktop_dir),
            "remove_existing": True,
            "silent": True,
        }
    ]
