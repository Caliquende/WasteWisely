import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = ROOT / "dist"
APP_EXE = DIST_DIR / "WasteWisely.exe"
INSTALLER_EXE = DIST_DIR / "WasteWisely_Installer.exe"

pytestmark = pytest.mark.skipif(
    os.name != "nt" or os.environ.get("WW_RUN_WINDOWS_SMOKE") != "1",
    reason="Windows smoke yalniz Windows'ta ve WW_RUN_WINDOWS_SMOKE=1 ile kosar.",
)


def _get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_health(port, timeout=30):
    deadline = time.time() + timeout
    last_error = None
    url = f"http://127.0.0.1:{port}/api/health"
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(0.5)
    raise AssertionError(f"Health endpoint hazir olmadi: {url} last_error={last_error}")


def _stop_process(proc):
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], check=False)
        proc.wait(timeout=10)


def _stop_running_binary_by_path(binary_path):
    if os.name != "nt":
        return

    escaped_path = str(Path(binary_path).resolve()).replace("'", "''")
    binary_name = Path(binary_path).name.replace("'", "''")
    command = (
        f"$target = [System.IO.Path]::GetFullPath('{escaped_path}');"
        f"$procs = Get-CimInstance Win32_Process -Filter \"Name='{binary_name}'\" -ErrorAction SilentlyContinue | "
        "Where-Object { $_.ExecutablePath -and ([System.IO.Path]::GetFullPath($_.ExecutablePath) -eq $target) };"
        "if ($procs) { $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force } }"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _assert_frontend_shell_loads(port):
    url = f"http://127.0.0.1:{port}"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.locator("#btn-start-scan").wait_for(timeout=15000)
        page.locator("#nav-results").wait_for(timeout=15000)
        assert page.locator("#btn-start-scan").is_visible()
        assert page.locator("#nav-results").is_visible()
        browser.close()


@pytest.fixture(scope="session")
def built_binaries():
    if (
        os.environ.get("WW_FORCE_SMOKE_REBUILD") == "1"
        or not APP_EXE.exists()
        or not INSTALLER_EXE.exists()
    ):
        subprocess.run([sys.executable, "build.py"], cwd=ROOT, check=True)
    assert APP_EXE.exists(), f"Eksik binary: {APP_EXE}"
    assert INSTALLER_EXE.exists(), f"Eksik binary: {INSTALLER_EXE}"
    return {"app": APP_EXE, "installer": INSTALLER_EXE}


def test_windows_build_produces_expected_binaries(built_binaries):
    assert built_binaries["app"].exists()
    assert built_binaries["installer"].exists()


def test_windows_packaged_server_serves_health_and_frontend(built_binaries):
    port = _get_free_port()
    env = os.environ.copy()
    env["WASTEWISE_PORT"] = str(port)
    _stop_running_binary_by_path(built_binaries["app"])
    proc = subprocess.Popen([str(built_binaries["app"]), "serve"], cwd=ROOT, env=env)

    try:
        payload = _wait_for_health(port)
        _assert_frontend_shell_loads(port)
    finally:
        _stop_process(proc)

    assert payload == {"status": "ok", "service": "WasteWisely"}


def test_windows_silent_installer_creates_runnable_install(tmp_path, built_binaries):
    fake_local_appdata = tmp_path / "LocalAppData"
    fake_userprofile = tmp_path / "UserProfile"
    fake_desktop = fake_userprofile / "Desktop"
    fake_desktop.mkdir(parents=True)

    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(fake_local_appdata)
    env["USERPROFILE"] = str(fake_userprofile)

    subprocess.run(
        [str(built_binaries["installer"]), "--silent"],
        cwd=ROOT,
        env=env,
        check=True,
        timeout=60,
    )

    installed_exes = list(fake_local_appdata.rglob("WasteWisely.exe"))
    assert len(installed_exes) == 1, f"Beklenen tek kurulu exe, bulunanlar: {installed_exes}"
    installed_exe = installed_exes[0]
    shortcut = fake_desktop / "WasteWisely.lnk"
    assert fake_local_appdata in installed_exe.parents, f"Kurulum kullanici yazilabilir dizinde degil: {installed_exe}"
    assert "Program Files" not in str(installed_exe), f"Kurulum halen Program Files altina gidiyor: {installed_exe}"
    assert installed_exe.exists(), f"Kurulan exe yok: {installed_exe}"
    assert shortcut.exists(), f"Kisayol yok: {shortcut}"

    port = _get_free_port()
    env["WASTEWISE_PORT"] = str(port)
    _stop_running_binary_by_path(installed_exe)
    proc = subprocess.Popen([str(installed_exe), "serve"], cwd=ROOT, env=env)

    try:
        payload = _wait_for_health(port)
        _assert_frontend_shell_loads(port)
    finally:
        _stop_process(proc)

    assert payload == {"status": "ok", "service": "WasteWisely"}


def test_windows_silent_installer_accepts_explicit_install_dir(tmp_path, built_binaries):
    explicit_install_dir = tmp_path / "CustomInstallRoot" / "WasteWisely"
    fake_userprofile = tmp_path / "UserProfile"
    fake_desktop = fake_userprofile / "Desktop"
    fake_desktop.mkdir(parents=True)

    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(tmp_path / "LocalAppData")
    env["USERPROFILE"] = str(fake_userprofile)

    subprocess.run(
        [str(built_binaries["installer"]), "--silent", "--install-dir", str(explicit_install_dir)],
        cwd=ROOT,
        env=env,
        check=True,
        timeout=60,
    )

    installed_exe = explicit_install_dir / "WasteWisely.exe"
    shortcut = fake_desktop / "WasteWisely.lnk"
    assert installed_exe.exists(), f"Kurulan exe yok: {installed_exe}"
    assert shortcut.exists(), f"Kisayol yok: {shortcut}"
