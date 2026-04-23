import sys
import os
import subprocess
import shutil

print("[*] Building WasteWisely standalone executable...")

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(ROOT, "build")
DIST_DIR = os.path.join(ROOT, "dist")
APP_BUILD_DIR = os.path.join(BUILD_DIR, "WasteWisely")
INSTALLER_BUILD_DIR = os.path.join(BUILD_DIR, "WasteWisely_Installer")
APP_EXE = os.path.join(DIST_DIR, "WasteWisely.exe")
INSTALLER_EXE = os.path.join(DIST_DIR, "WasteWisely_Installer.exe")


def stop_running_binary(binary_path):
    if os.name != "nt":
        return

    escaped_path = os.path.abspath(binary_path).replace("'", "''")
    binary_name = os.path.basename(binary_path).replace("'", "''")
    command = (
        f"$target = [System.IO.Path]::GetFullPath('{escaped_path}');"
        f"$procs = Get-CimInstance Win32_Process -Filter \"Name='{binary_name}'\" -ErrorAction SilentlyContinue | "
        "Where-Object { $_.ExecutablePath -and ([System.IO.Path]::GetFullPath($_.ExecutablePath) -eq $target) };"
        "if ($procs) { $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force } }"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def recreate_dir(path):
    import time
    for _ in range(5):
        shutil.rmtree(path, ignore_errors=True)
        if not os.path.exists(path):
            break
        time.sleep(1)
    
    if os.path.exists(path):
        # Try one last time with errors enabled to see what's wrong
        try:
            shutil.rmtree(path)
        except Exception as e:
            raise RuntimeError(f"Failed to clean directory: {path}. Error: {e}")
    os.makedirs(path, exist_ok=True)

# Ensure dist and build dirs are clean
stop_running_binary(APP_EXE)
stop_running_binary(INSTALLER_EXE)
recreate_dir(BUILD_DIR)
recreate_dir(DIST_DIR)
os.makedirs(APP_BUILD_DIR, exist_ok=True)

missing = []

try:
    import PyInstaller  # noqa: F401
except ImportError:
    missing.append("PyInstaller")

try:
    import win32com.client  # noqa: F401
except ImportError:
    missing.append("pywin32")

if missing:
    print(f"[!] Missing build dependencies: {', '.join(missing)}")
    print("[!] Install them with: pip install -r requirements-build.txt")
    sys.exit(1)

pyinstaller_cmd = [
    sys.executable, "-m", "PyInstaller",
    "--clean",
    "--name=WasteWisely",
    "--onefile",
    "--windowed", # Don't open console when double clicked (UI runs in pywebview)
    "--specpath", ROOT,
    "--workpath", BUILD_DIR,
    "--distpath", DIST_DIR,
    "--paths=src",
    "--add-data=frontend;frontend",
    "--hidden-import=api",
    "--hidden-import=actions",
    "--hidden-import=scanner",
    "--hidden-import=classifier",
    "--hidden-import=uvicorn.logging",
    "--hidden-import=uvicorn.loops",
    "--hidden-import=uvicorn.loops.auto",
    "--hidden-import=uvicorn.protocols",
    "--hidden-import=uvicorn.protocols.http",
    "--hidden-import=uvicorn.protocols.http.auto",
    "--hidden-import=uvicorn.protocols.websockets",
    "--hidden-import=uvicorn.protocols.websockets.auto",
    "--hidden-import=uvicorn.lifespan",
    "--hidden-import=uvicorn.lifespan.on",
    "--hidden-import=uvicorn.lifespan.off",
    "src/main.py"
]

print(f"[*] Running command: {' '.join(pyinstaller_cmd)}")
subprocess.run(pyinstaller_cmd, check=True)

print("\n[*] Building install.exe...")
os.makedirs(INSTALLER_BUILD_DIR, exist_ok=True)
installer_cmd = [
    sys.executable, "-m", "PyInstaller",
    "--clean",
    "--name=WasteWisely_Installer",
    "--onefile",
    "--windowed",
    "--uac-admin",
    "--specpath", ROOT,
    "--workpath", BUILD_DIR,
    "--distpath", DIST_DIR,
    "--add-data=dist/WasteWisely.exe;.",
    "installer.py"
]

subprocess.run(installer_cmd, check=True)

print("\n[*] Build complete! Check the 'dist' directory for WasteWisely.exe and WasteWisely_Installer.exe")
