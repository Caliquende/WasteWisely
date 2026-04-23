import builtins
import os
import runpy
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest


BUILD_SCRIPT = Path(__file__).resolve().parents[2] / "build.py"


def _fake_win32_modules():
    fake_win32 = types.ModuleType("win32com")
    fake_client = types.ModuleType("win32com.client")
    fake_win32.client = fake_client
    return fake_win32, fake_client


def _arg_value(command, flag):
    index = command.index(flag)
    return command[index + 1]


def test_build_script_exits_when_pyinstaller_is_missing(monkeypatch, capsys):
    original_import = builtins.__import__
    fake_win32, fake_client = _fake_win32_modules()

    def fake_import(name, *args, **kwargs):
        if name == "PyInstaller":
            raise ImportError("missing PyInstaller")
        return original_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "PyInstaller", raising=False)
    monkeypatch.setitem(sys.modules, "win32com", fake_win32)
    monkeypatch.setitem(sys.modules, "win32com.client", fake_client)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(BUILD_SCRIPT), run_name="__main__")

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "Missing build dependencies: PyInstaller" in captured.out
    assert "requirements-build.txt" in captured.out


def test_build_script_exits_when_pywin32_is_missing(monkeypatch, capsys):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "win32com.client":
            raise ImportError("missing pywin32")
        return original_import(name, *args, **kwargs)

    monkeypatch.setitem(sys.modules, "PyInstaller", types.ModuleType("PyInstaller"))
    monkeypatch.delitem(sys.modules, "win32com", raising=False)
    monkeypatch.delitem(sys.modules, "win32com.client", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(BUILD_SCRIPT), run_name="__main__")

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "Missing build dependencies: pywin32" in captured.out
    assert "requirements-build.txt" in captured.out


def test_build_script_cleans_output_dirs_and_runs_both_pyinstaller_commands(monkeypatch):
    fake_win32, fake_client = _fake_win32_modules()
    cleanups = []
    created_dirs = []
    commands = []
    project_root = str(BUILD_SCRIPT.parent)
    build_dir = str(BUILD_SCRIPT.parent / "build")
    dist_dir = str(BUILD_SCRIPT.parent / "dist")
    app_build_dir = str(BUILD_SCRIPT.parent / "build" / "WasteWisely")
    installer_build_dir = str(BUILD_SCRIPT.parent / "build" / "WasteWisely_Installer")
    removed_paths = set()
    original_exists = os.path.exists

    def fake_rmtree(path, ignore_errors=False):
        cleanups.append((path, ignore_errors))
        removed_paths.add(os.path.normpath(path))

    def fake_exists(path):
        normalized = os.path.normpath(path)
        if normalized in removed_paths:
            return False
        return original_exists(path)

    def fake_makedirs(path, exist_ok=False):
        created_dirs.append((path, exist_ok))
        removed_paths.discard(os.path.normpath(path))

    def fake_run(command, check, **kwargs):
        commands.append((command, check, kwargs))

    monkeypatch.setitem(sys.modules, "PyInstaller", types.ModuleType("PyInstaller"))
    monkeypatch.setitem(sys.modules, "win32com", fake_win32)
    monkeypatch.setitem(sys.modules, "win32com.client", fake_client)
    monkeypatch.setattr(shutil, "rmtree", fake_rmtree)
    monkeypatch.setattr(os.path, "exists", fake_exists)
    monkeypatch.setattr(os, "makedirs", fake_makedirs)
    monkeypatch.setattr(subprocess, "run", fake_run)

    runpy.run_path(str(BUILD_SCRIPT), run_name="__main__")

    assert cleanups == [(build_dir, True), (dist_dir, True)]
    assert created_dirs == [
        (build_dir, True),
        (dist_dir, True),
        (app_build_dir, True),
        (installer_build_dir, True),
    ]
    assert len(commands) == 3

    cleanup_command, cleanup_check, cleanup_kwargs = commands[0]
    assert cleanup_check is True
    assert cleanup_command[:3] == ["powershell", "-NoProfile", "-Command"]
    assert "WasteWisely.exe" in cleanup_command[-1]
    assert cleanup_kwargs["stdout"] == subprocess.DEVNULL
    assert cleanup_kwargs["stderr"] == subprocess.DEVNULL

    pyinstaller_commands = [(command, check) for command, check, _ in commands[1:]]

    first_command, first_check = pyinstaller_commands[0]
    assert first_check is True
    assert first_command[:3] == [sys.executable, "-m", "PyInstaller"]
    assert "--name=WasteWisely" in first_command
    assert "--onefile" in first_command
    assert "--windowed" in first_command
    assert _arg_value(first_command, "--specpath") == project_root
    assert _arg_value(first_command, "--workpath") == build_dir
    assert _arg_value(first_command, "--distpath") == dist_dir
    assert "--paths=src" in first_command
    assert "--add-data=frontend;frontend" in first_command
    assert "--hidden-import=api" in first_command
    assert "--hidden-import=actions" in first_command
    assert "--hidden-import=scanner" in first_command
    assert "--hidden-import=classifier" in first_command
    assert "--hidden-import=uvicorn.logging" in first_command
    assert "--hidden-import=uvicorn.protocols.http.auto" in first_command
    assert "--hidden-import=uvicorn.protocols.websockets.auto" in first_command
    assert "--hidden-import=uvicorn.lifespan.on" in first_command
    assert first_command[-1] == "src/main.py"

    second_command, second_check = pyinstaller_commands[1]
    assert second_check is True
    assert second_command[:3] == [sys.executable, "-m", "PyInstaller"]
    assert "--name=WasteWisely_Installer" in second_command
    assert "--onefile" in second_command
    assert "--windowed" in second_command
    assert "--uac-admin" not in second_command
    assert _arg_value(second_command, "--specpath") == project_root
    assert _arg_value(second_command, "--workpath") == build_dir
    assert _arg_value(second_command, "--distpath") == dist_dir
    assert "--add-data=dist/WasteWisely.exe;." in second_command
    assert second_command[-1] == "installer.py"
