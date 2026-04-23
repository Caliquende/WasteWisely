"""
WasteWisely CLI - Komut satiri arayuzu.
Hem bagimsiz tarama hem de API sunucusu baslatma destegi.
"""
import sys
import time
import argparse
import threading
import os
import logging
import logging.handlers
import tempfile
from pathlib import Path

LOG_FILENAME = "wastewise_debug.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
EVENT_SOURCE = "WasteWiselyApp"


def resolve_log_path(log_name: str) -> Path:
    base_dir = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or tempfile.gettempdir()
    return Path(base_dir) / "WasteWisely" / "logs" / log_name


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
    nt_handler.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger().addHandler(nt_handler)
except Exception:
    pass

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception in main.py", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
except ImportError:
    pass

try:
    import webview
except ImportError:
    pass

# BUG-4 FIX: ensure src/ is always on sys.path regardless of working directory
_src_dir = Path(__file__).resolve().parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from scanner import Scanner
from classifier import Classifier


def resolve_default_command(webview_available: bool | None = None) -> str:
    """Secilecek varsayilan komutu tek yerde tanimlar."""
    if webview_available is None:
        webview_available = 'webview' in sys.modules
    return "app" if webview_available else "serve"


def resolve_runtime_port() -> int:
    """Runtime port'unu env uzerinden alir; gecersizse guvenli varsayilana doner."""
    try:
        return int(os.environ.get("WASTEWISE_PORT", "8000"))
    except ValueError:
        return 8000


def run_scan(target_path: str):
    """CLI uzerinden tarama yapar ve sonuclari gosterir (Rich destekli)."""
    target = Path(target_path).resolve()

    if 'rich' not in sys.modules:
        print("Rich kurulu degil. Tam CLI deneyimi icin 'pip install -r requirements.txt' calistirin.")
        # Fallback to simple scan
        scanner = Scanner(str(target))
        classifier = Classifier(scanner.scan())
        print(f"Tarama bitti: {classifier.get_summary()['total_waste_size_human']} atik bulundu.")
        return

    console = Console()
    console.print(Panel(f"WasteWisely Tarama: [bold cyan]{target}[/]", expand=False))

    scanner = Scanner(str(target))
    
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(description="Dosya sistemi taraniyor...", total=None)
        raw_data = scanner.scan()
        
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(description="Atiklar siniflandiriliyor...", total=None)
        classifier = Classifier(raw_data)
        classifier.classify()
        summary = classifier.get_summary()

    table = Table(title="Bulunan Atik Kategorileri")
    table.add_column("Kategori", style="cyan")
    table.add_column("Oge Sayisi", justify="right", style="magenta")
    table.add_column("Boyut", justify="right", style="green")
    table.add_column("Risk", justify="center")

    risk_colors = {'critical': '[red]Kritik[/red]', 'medium': '[yellow]Orta[/yellow]', 'low': '[green]Dusuk[/green]'}

    for cat_key, cat_data in summary['categories'].items():
        if cat_data['count'] > 0:
            table.add_row(
                cat_data['name'],
                str(cat_data['count']),
                cat_data['total_size_human'],
                risk_colors.get(cat_data['risk'], '')
            )
            
    console.print(table)
    console.print(f"\n[bold]Toplam Atik:[/bold] {summary['total_waste_count']} oge ({summary['total_waste_size_human']})")
    console.print("[dim]Daha fazla detay ve aksiyon icin 'python src/main.py serve' veya 'app' komutunu kullanin.[/dim]\n")


def run_server(port=None):
    """API sunucusunu baslatir."""
    if port is None:
        port = resolve_runtime_port()
    try:
        import uvicorn
        print(f"[*] WasteWisely API & Dashboard baslatiliyor: http://127.0.0.1:{port}")
        uvicorn.run("api:app", host="127.0.0.1", port=port, reload=False, app_dir=str(_src_dir))
    except ImportError:
        print("[x] uvicorn yuklu degil. 'pip install uvicorn[standard]' calistirin.")
        sys.exit(1)

class JSApi:
    """Frontend tarafindan cagrilabilecek yerel fonksiyonlar."""
    def select_folder(self):
        if 'webview' not in sys.modules:
            return None
        # webview.active_window() veya windows[0] kullanilabilir
        active_window = webview.windows[0] if webview.windows else None
        if not active_window:
            return None
        
        result = active_window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return result[0] if isinstance(result, (list, tuple)) else result
        return None

def run_app():
    """Masaustu uygulamasini baslatir (pywebview)."""
    if 'webview' not in sys.modules:
        print("[x] pywebview kurulu degil. 'pip install -r requirements-build.txt' veya 'pip install .[desktop]' calistirin.")
        sys.exit(1)

    port = resolve_runtime_port()
        
    print("[*] Masaustu penceresi hazirlaniyor...")
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    time.sleep(1.5)  # Sunucunun kalkmasi icin kisa bekleme
    js_api = JSApi()
    
    icon_path = _get_resource_path("assets/icon.ico")
    webview.create_window('WasteWisely Desktop', f'http://127.0.0.1:{port}', js_api=js_api, width=1200, height=800)
    
    # Start webview with icon if possible (pywebview handles icon via start on some platforms, but EXE icon is usually enough)
    webview.start()

def _get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def run_daemon(target_path: str):
    """Arka planda klasoru izleyen ve belli araliklarla tarama yapan akilli daemon modu."""
    print(f"[*] WasteWisely Daemon modunda calisiyor. Izlenen dizin: {target_path}")
    print("[*] Arka planda atik birikimi takip edilecek...")
    
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
    except ImportError:
        toaster = None
        print("[!] win10toast kurulu degil. Masaustu bildirimleri kapali.")
        
    target = Path(target_path).resolve()

    def daemon_loop():
        while True:
            try:
                # 1 saatte bir (veya demo icin daha sik) tarama yap.
                # Demo amaciyla sadece gerceklesme anini loglayalim.
                # Fakat normalde: time.sleep(3600)
                time.sleep(30) # Demo hizli tarama
                
                print(f"\n[DAEMON] Otomatik arka plan taramasi basladi: {time.ctime()}")
                from scanner import Scanner
                from classifier import Classifier
                
                sc = Scanner(str(target))
                raw = sc.scan()
                cl = Classifier(raw)
                cl.classify()
                summ = cl.get_summary()
                
                total_mb = summ['total_waste_size'] / (1024 * 1024)
                
                if total_mb > 50: # Eger 50MB uzeri atik varsa uyar
                    msg = f"Sisteminizde {summ['total_waste_count']} adet, {summ['total_waste_size_human']} boyutunda atik bulundu."
                    print(f"[DAEMON-ALERT] {msg}")
                    if toaster:
                        # threaded=True gives background notification without blocking
                        toaster.show_toast("WasteWisely Atik Alarmi!", msg, duration=5, threaded=True)
                else:
                    print("[DAEMON] Sistem temiz. Birikim yok.")
            except Exception as e:
                print(f"[DAEMON-ERROR] {e}")

    daemon_thread = threading.Thread(target=daemon_loop, daemon=True)
    daemon_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Daemon kapatiliyor...")
        sys.exit(0)

def main():
    # BUG-5 FIX: argparse description uses only ASCII
    parser = argparse.ArgumentParser(
        prog="wastewise",
        description="WasteWisely - Dijital Atik Denetcisi",
    )
    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="Dizini tara ve atiklari listele")
    scan_parser.add_argument("path", nargs="?", default=".", help="Taranacak dizin (varsayilan: .)")

    subparsers.add_parser("serve", help="Web dashboard'u baslatir (Browser)")
    subparsers.add_parser("app", help="Masaustu uygulamasini baslatir (Desktop App)")
    
    daemon_parser = subparsers.add_parser("daemon", help="Arka planda sessiz takip modunu baslatir")
    daemon_parser.add_argument("path", nargs="?", default=".", help="Izlenecek dizin")

    args = parser.parse_args()

    # Güvenli varsayilan: desktop bagimliligi varsa app, yoksa serve.
    if args.command is None:
        args.command = resolve_default_command()

    if args.command == "scan":
        run_scan(args.path)
    elif args.command == "serve":
        run_server()
    elif args.command == "app":
        run_app()
    elif args.command == "daemon":
        run_daemon(args.path)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
