import builtins
import sys
import types
from pathlib import Path

import pytest

from src import main as cli_main


def test_resolve_log_path_prefers_localappdata(monkeypatch, tmp_path):
    local_app_data = tmp_path / "LocalAppData"

    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.delenv("TEMP", raising=False)

    assert cli_main.resolve_log_path("wastewise_debug.log") == (
        local_app_data / "WasteWisely" / "logs" / "wastewise_debug.log"
    )


def test_configure_logging_falls_back_to_stderr_when_file_handler_fails(monkeypatch):
    config_calls = {}
    stream_marker = object()

    monkeypatch.setattr(cli_main, "resolve_log_path", lambda name: Path(r"C:\Program Files\WasteWisely") / name)
    monkeypatch.setattr(
        cli_main.logging,
        "FileHandler",
        lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError("denied")),
    )
    monkeypatch.setattr(cli_main.logging, "StreamHandler", lambda stream: stream_marker)
    monkeypatch.setattr(
        cli_main.logging,
        "basicConfig",
        lambda **kwargs: config_calls.update(kwargs),
    )

    cli_main.configure_logging()

    assert config_calls["handlers"] == [stream_marker]
    assert config_calls["level"] == cli_main.logging.DEBUG
    assert config_calls["format"] == cli_main.LOG_FORMAT


def test_main_defaults_to_serve_when_webview_unavailable(monkeypatch):
    called = []

    monkeypatch.setattr(sys, "argv", ["wastewise"])
    monkeypatch.setattr(cli_main, "run_server", lambda: called.append("serve"))
    monkeypatch.setattr(cli_main, "run_app", lambda: called.append("app"))
    monkeypatch.delitem(sys.modules, "webview", raising=False)

    cli_main.main()

    assert called == ["serve"]


def test_main_defaults_to_app_when_webview_available(monkeypatch):
    called = []
    fake_webview = types.SimpleNamespace()

    monkeypatch.setattr(sys, "argv", ["wastewise"])
    monkeypatch.setattr(cli_main, "run_server", lambda: called.append("serve"))
    monkeypatch.setattr(cli_main, "run_app", lambda: called.append("app"))
    monkeypatch.setitem(sys.modules, "webview", fake_webview)
    monkeypatch.setattr(cli_main, "webview", fake_webview, raising=False)

    cli_main.main()

    assert called == ["app"]


def test_main_dispatches_scan_with_explicit_path(monkeypatch, tmp_path):
    called = []

    monkeypatch.setattr(sys, "argv", ["wastewise", "scan", str(tmp_path)])
    monkeypatch.setattr(cli_main, "run_scan", lambda path: called.append(path))

    cli_main.main()

    assert called == [str(tmp_path)]


def test_main_dispatches_scan_with_default_dot_path(monkeypatch):
    called = []

    monkeypatch.setattr(sys, "argv", ["wastewise", "scan"])
    monkeypatch.setattr(cli_main, "run_scan", lambda path: called.append(path))

    cli_main.main()

    assert called == ["."]


def test_main_dispatches_serve_command(monkeypatch):
    called = []

    monkeypatch.setattr(sys, "argv", ["wastewise", "serve"])
    monkeypatch.setattr(cli_main, "run_server", lambda: called.append("serve"))

    cli_main.main()

    assert called == ["serve"]


def test_main_dispatches_app_command(monkeypatch):
    called = []

    monkeypatch.setattr(sys, "argv", ["wastewise", "app"])
    monkeypatch.setattr(cli_main, "run_app", lambda: called.append("app"))

    cli_main.main()

    assert called == ["app"]


def test_main_dispatches_daemon_with_explicit_path(monkeypatch, tmp_path):
    called = []

    monkeypatch.setattr(sys, "argv", ["wastewise", "daemon", str(tmp_path)])
    monkeypatch.setattr(cli_main, "run_daemon", lambda path: called.append(path))

    cli_main.main()

    assert called == [str(tmp_path)]


def test_main_dispatches_daemon_with_default_dot_path(monkeypatch):
    called = []

    monkeypatch.setattr(sys, "argv", ["wastewise", "daemon"])
    monkeypatch.setattr(cli_main, "run_daemon", lambda path: called.append(path))

    cli_main.main()

    assert called == ["."]


def test_resolve_runtime_port_reads_env_and_falls_back_on_invalid_value(monkeypatch):
    monkeypatch.setenv("WASTEWISE_PORT", "9137")
    assert cli_main.resolve_runtime_port() == 9137

    monkeypatch.setenv("WASTEWISE_PORT", "invalid")
    assert cli_main.resolve_runtime_port() == 8000


def test_run_server_invokes_uvicorn_with_expected_arguments(monkeypatch):
    calls = {}
    fake_uvicorn = types.SimpleNamespace(
        run=lambda *args, **kwargs: calls.update({"args": args, "kwargs": kwargs})
    )

    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    cli_main.run_server(port=9123)

    assert calls["args"] == ("api:app",)
    assert calls["kwargs"] == {
        "host": "127.0.0.1",
        "port": 9123,
        "reload": False,
        "app_dir": str(cli_main._src_dir),
    }


def test_run_server_exits_cleanly_when_uvicorn_is_missing(monkeypatch, capsys):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "uvicorn":
            raise ImportError("missing uvicorn")
        return original_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "uvicorn", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(SystemExit) as exc_info:
        cli_main.run_server()

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "uvicorn yuklu degil" in captured.out


def test_run_app_exits_when_webview_is_missing(monkeypatch, capsys):
    monkeypatch.delitem(sys.modules, "webview", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        cli_main.run_app()

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "pywebview kurulu degil" in captured.out


def test_run_app_starts_server_thread_and_opens_desktop_window(monkeypatch):
    calls = {"sleep": []}

    class FakeThread:
        instance = None

        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon
            self.started = False
            FakeThread.instance = self

        def start(self):
            self.started = True

    fake_webview = types.SimpleNamespace(
        create_window=lambda *args, **kwargs: calls.update(
            {"window_args": args, "window_kwargs": kwargs}
        ),
        start=lambda: calls.update({"webview_started": True}),
    )

    monkeypatch.setattr(cli_main.threading, "Thread", FakeThread)
    monkeypatch.setattr(cli_main.time, "sleep", lambda seconds: calls["sleep"].append(seconds))
    monkeypatch.setattr(cli_main, "run_server", lambda: calls.update({"server_target": "run"}))
    monkeypatch.setitem(sys.modules, "webview", fake_webview)
    monkeypatch.setattr(cli_main, "webview", fake_webview, raising=False)

    cli_main.run_app()

    assert FakeThread.instance is not None
    assert FakeThread.instance.target is cli_main.run_server
    assert FakeThread.instance.daemon is True
    assert FakeThread.instance.started is True
    assert calls["sleep"] == [1.5]
    assert calls["window_args"] == ("WasteWisely Desktop", "http://127.0.0.1:8000")
    assert calls["window_kwargs"] == {"width": 1200, "height": 800}
    assert calls["webview_started"] is True


def test_run_app_uses_environment_port_in_desktop_window(monkeypatch):
    calls = {}

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            return None

    fake_webview = types.SimpleNamespace(
        create_window=lambda *args, **kwargs: calls.update(
            {"window_args": args, "window_kwargs": kwargs}
        ),
        start=lambda: calls.update({"webview_started": True}),
    )

    monkeypatch.setenv("WASTEWISE_PORT", "9456")
    monkeypatch.setattr(cli_main.threading, "Thread", FakeThread)
    monkeypatch.setattr(cli_main.time, "sleep", lambda seconds: None)
    monkeypatch.setitem(sys.modules, "webview", fake_webview)
    monkeypatch.setattr(cli_main, "webview", fake_webview, raising=False)

    cli_main.run_app()

    assert calls["window_args"] == ("WasteWisely Desktop", "http://127.0.0.1:9456")


def test_run_daemon_warns_without_toast_dependency_and_exits_on_keyboard_interrupt(
    monkeypatch, tmp_path, capsys
):
    original_import = builtins.__import__

    class FakeThread:
        instance = None

        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon
            self.started = False
            FakeThread.instance = self

        def start(self):
            self.started = True

    def fake_import(name, *args, **kwargs):
        if name == "win10toast":
            raise ImportError("missing win10toast")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(cli_main.threading, "Thread", FakeThread)
    monkeypatch.setattr(cli_main.time, "sleep", lambda seconds: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "win10toast", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        cli_main.run_daemon(str(tmp_path))

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert FakeThread.instance is not None
    assert FakeThread.instance.daemon is True
    assert FakeThread.instance.started is True
    assert "win10toast kurulu degil" in captured.out
    assert "Daemon kapatiliyor" in captured.out


def test_run_daemon_emits_desktop_notification_for_large_waste(monkeypatch, tmp_path, capsys):
    toast_calls = {}
    sleep_state = {"daemon_passes": 0}

    class StopDaemonLoop(BaseException):
        pass

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            try:
                self.target()
            except StopDaemonLoop:
                return

    class FakeToaster:
        def show_toast(self, title, msg, duration, threaded):
            toast_calls.update(
                {
                    "title": title,
                    "msg": msg,
                    "duration": duration,
                    "threaded": threaded,
                }
            )

    class FakeScanner:
        def __init__(self, target_path):
            self.target_path = target_path

        def scan(self):
            return [{"kind": "fake"}]

    class FakeClassifier:
        def __init__(self, raw_data):
            self.raw_data = raw_data

        def classify(self):
            return None

        def get_summary(self):
            return {
                "total_waste_size": 60 * 1024 * 1024,
                "total_waste_count": 3,
                "total_waste_size_human": "60 MB",
            }

    def fake_sleep(seconds):
        if seconds == 30:
            if sleep_state["daemon_passes"] == 0:
                sleep_state["daemon_passes"] += 1
                return
            raise StopDaemonLoop()
        raise KeyboardInterrupt()

    monkeypatch.setitem(sys.modules, "win10toast", types.SimpleNamespace(ToastNotifier=FakeToaster))
    monkeypatch.setitem(sys.modules, "scanner", types.SimpleNamespace(Scanner=FakeScanner))
    monkeypatch.setitem(sys.modules, "classifier", types.SimpleNamespace(Classifier=FakeClassifier))
    monkeypatch.setattr(cli_main.threading, "Thread", FakeThread)
    monkeypatch.setattr(cli_main.time, "sleep", fake_sleep)

    with pytest.raises(SystemExit) as exc_info:
        cli_main.run_daemon(str(tmp_path))

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert toast_calls == {
        "title": "WasteWisely Atik Alarmi!",
        "msg": "Sisteminizde 3 adet, 60 MB boyutunda atik bulundu.",
        "duration": 5,
        "threaded": True,
    }
    assert "[DAEMON-ALERT]" in captured.out


def test_run_daemon_skips_toast_when_waste_is_below_threshold(monkeypatch, tmp_path, capsys):
    toast_calls = []
    sleep_state = {"daemon_passes": 0}

    class StopDaemonLoop(BaseException):
        pass

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            try:
                self.target()
            except StopDaemonLoop:
                return

    class FakeToaster:
        def show_toast(self, title, msg, duration, threaded):
            toast_calls.append((title, msg, duration, threaded))

    class FakeScanner:
        def __init__(self, target_path):
            self.target_path = target_path

        def scan(self):
            return [{"kind": "fake"}]

    class FakeClassifier:
        def __init__(self, raw_data):
            self.raw_data = raw_data

        def classify(self):
            return None

        def get_summary(self):
            return {
                "total_waste_size": 10 * 1024 * 1024,
                "total_waste_count": 1,
                "total_waste_size_human": "10 MB",
            }

    def fake_sleep(seconds):
        if seconds == 30:
            if sleep_state["daemon_passes"] == 0:
                sleep_state["daemon_passes"] += 1
                return
            raise StopDaemonLoop()
        raise KeyboardInterrupt()

    monkeypatch.setitem(sys.modules, "win10toast", types.SimpleNamespace(ToastNotifier=FakeToaster))
    monkeypatch.setitem(sys.modules, "scanner", types.SimpleNamespace(Scanner=FakeScanner))
    monkeypatch.setitem(sys.modules, "classifier", types.SimpleNamespace(Classifier=FakeClassifier))
    monkeypatch.setattr(cli_main.threading, "Thread", FakeThread)
    monkeypatch.setattr(cli_main.time, "sleep", fake_sleep)

    with pytest.raises(SystemExit) as exc_info:
        cli_main.run_daemon(str(tmp_path))

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert toast_calls == []
    assert "[DAEMON] Sistem temiz. Birikim yok." in captured.out


def test_run_daemon_logs_loop_exceptions_without_crashing(monkeypatch, tmp_path, capsys):
    sleep_state = {"daemon_passes": 0}

    class StopDaemonLoop(BaseException):
        pass

    class FakeThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            try:
                self.target()
            except StopDaemonLoop:
                return

    class FakeScanner:
        def __init__(self, target_path):
            self.target_path = target_path

        def scan(self):
            raise RuntimeError("boom")

    class FakeClassifier:
        def __init__(self, raw_data):
            self.raw_data = raw_data

        def classify(self):
            return None

        def get_summary(self):
            return {}

    def fake_sleep(seconds):
        if seconds == 30:
            if sleep_state["daemon_passes"] == 0:
                sleep_state["daemon_passes"] += 1
                return
            raise StopDaemonLoop()
        raise KeyboardInterrupt()

    monkeypatch.setitem(sys.modules, "win10toast", types.SimpleNamespace(ToastNotifier=lambda: None))
    monkeypatch.setitem(sys.modules, "scanner", types.SimpleNamespace(Scanner=FakeScanner))
    monkeypatch.setitem(sys.modules, "classifier", types.SimpleNamespace(Classifier=FakeClassifier))
    monkeypatch.setattr(cli_main.threading, "Thread", FakeThread)
    monkeypatch.setattr(cli_main.time, "sleep", fake_sleep)

    with pytest.raises(SystemExit) as exc_info:
        cli_main.run_daemon(str(tmp_path))

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "[DAEMON-ERROR] boom" in captured.out
