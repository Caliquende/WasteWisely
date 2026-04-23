# Validation Journal

## 2026-04-23 - Windows smoke and packaging validation

- Root cause confirmed:
  - PyInstaller analysis could not resolve local top-level modules from `src/`.
  - `build/WasteWisely/warn-WasteWisely.txt` previously contained:
    - `missing module named classifier - imported by ... src\main.py`
    - `missing module named scanner - imported by ... src\main.py`
  - Dynamic `uvicorn.run("api:app", ...)` path also lacked explicit packaging coverage.

- Fix applied:
  - `build.py` now adds `--paths=src`
  - `build.py` now adds hidden imports: `api`, `actions`, `scanner`, `classifier`
  - `WasteWisely.spec` aligned with the same local-module packaging contract
  - `installer.py` gained `--silent` mode for smoke automation
  - `src/main.py` gained `WASTEWISE_PORT` runtime override for isolated binary smoke

- Evidence:
  - `python build.py` -> success, produced `dist/WasteWisely.exe` and `dist/WasteWisely_Installer.exe`
  - `Select-String build\WasteWisely\warn-WasteWisely.txt -Pattern "missing module named api|missing module named actions|missing module named scanner|missing module named classifier"` -> no matches
  - `$env:WW_RUN_WINDOWS_SMOKE='1'; python -m pytest tests\e2e\test_windows_smoke.py -q -rA`
    - `PASSED test_windows_build_produces_expected_binaries`
    - `PASSED test_windows_desktop_binary_serves_health_endpoint`
    - `SKIPPED test_windows_silent_installer_creates_runnable_install`
    - skip reason: shell not elevated, real installer smoke requires admin/UAC
  - `python -m pytest tests -q -rA` -> `71 passed, 3 skipped`

- Residual risk:
  - Real installer end-to-end smoke is still gated by elevated execution. The contract is implemented and smoke-tested up to the UAC boundary; full installer proof requires an elevated shell.

## 2026-04-23 - Cyclical regression/fix/sanity loop

- Root causes confirmed during repeated cycles:
  - `tests/sanity/test_build_contract.py` drifted behind the real `build.py` contract after Windows packaging hardening:
    - it still assumed relative cleanup paths
    - it assumed only two `subprocess.run(...)` calls
    - it used a too-narrow `subprocess.run` test double that broke once stdout/stderr kwargs were passed
  - Packaged frontend resolution was incomplete:
    - health endpoint from `WasteWisely.exe serve` came up
    - Playwright could not find `#btn-start-scan`
    - cause: `src/api.py` only looked for `frontend/` in source layout and ignored PyInstaller `_MEIPASS`

- Fixes applied:
  - `tests/sanity/test_build_contract.py`
    - aligned with absolute `build/dist` paths
    - tracks the pre-cleanup PowerShell process-stop call
    - validates `--specpath/--workpath/--distpath`
    - mocks cleanup/recreation behavior explicitly
  - `build.py`
    - now stops the exact packaged `dist/WasteWisely.exe` before rebuild
    - verifies cleanup happened instead of silently ignoring stale directories
    - pre-creates target work directories
  - `src/api.py`
    - added `resolve_frontend_dir()`
    - supports both source layout and PyInstaller bundle root via `_MEIPASS`
  - `tests/integration/test_api_frontend_resolution.py`
    - locks the bundle-vs-source frontend resolution contract
  - `tests/e2e/test_windows_smoke.py`
    - smoke now launches packaged binary with `serve`
    - validates `/api/health`
    - uses Playwright to assert packaged frontend shell loads
    - kills stale packaged binaries by exact path before launch

- Evidence:
  - Initial repeated cycle:
    - `regression -> sanity -> regression -> sanity -> regression -> sanity`
    - reproduced `tests/sanity/test_build_contract.py::test_build_script_cleans_output_dirs_and_runs_both_pyinstaller_commands`
  - Post-fix cycle:
    - repeated `regression -> sanity -> regression -> sanity` all green
  - Targeted contract validation:
    - `python -m pytest tests\\integration\\test_api_frontend_resolution.py tests\\sanity\\test_build_contract.py -q -rA` -> `6 passed`
  - Real Windows smoke with rebuild:
    - `$env:WW_RUN_WINDOWS_SMOKE='1'; $env:WW_FORCE_SMOKE_REBUILD='1'; python -m pytest tests\\e2e\\test_windows_smoke.py -q -rA`
    - `PASSED test_windows_build_produces_expected_binaries`
    - `PASSED test_windows_packaged_server_serves_health_and_frontend`
    - `SKIPPED test_windows_silent_installer_creates_runnable_install`
    - skip reason: shell not elevated, installer still needs admin/UAC
  - Final suite:
    - `python -m pytest tests -q -rA` -> `74 passed, 3 skipped`

- Residual risk:
  - Real packaged `app` / pywebview boot is still not directly asserted by the Windows smoke. The smoke now validates the packaged server and packaged frontend shell through Playwright, which is more deterministic, but desktop-window boot remains covered indirectly by integration tests rather than a native GUI harness.
