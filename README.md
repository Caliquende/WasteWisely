# WasteWisely - Professional Digital Waste Auditor

![WasteWisely Header](assets/header.png)

WasteWisely is a high-performance Windows desktop application designed to identify and clean "digital waste." It goes beyond simple temp file cleaning by intelligently classifying development bloat, sensitive data leaks, and stale project files.

[🇹🇷 Türkçe dökümantasyon için tıklayın (README_TR.md)](README_TR.md)

---

## Key Features

### Performance and UI
- **Offline-First Desktop App:** Built with Python & FastAPI, wrapped in a native `pywebview` window.
- **Native Windows Dialogs:** Integration with system folder pickers for a seamless experience.
- **Dynamic Dashboard:** Real-time data visualization using Donut charts and interactive Treemaps.
- **Multi-Language Support:** Fully localized in English, Turkish, and Arabic (RTL support).

### Intelligent Scanning
- **Heavy Dependencies:** Detects massive `node_modules`, `.venv`, and build directories.
- **Sensitive Leaks:** Scans for exposed `.env`, private keys, and credentials.
- **Smart Staleness Filter:** Large files (>500MB) are only flagged if untouched for 90+ days to avoid deleting active work.
- **System Protection:** Automatically excludes critical Windows system files (`pagefile.sys`, etc.).

### Professional Deployment
- **UAC Elevation:** The installer requests administrative privileges to manage `C:\Program Files`.
- **Safe Installation:** Automatically detects and stops running instances of WasteWisely before updates or uninstallation to prevent file locking errors.
- **Isolated Logging:** Logs are stored in `%TEMP%\WasteWisely` to avoid permission issues.

### Smart Actions
- **Safe Archival:** Instead of direct deletion, archive folders into compressed ZIPs in a hidden `.wastewise_archive` directory. Perfect for "I might need this later" scenarios.
- **Direct Purge:** One-click permanent deletion for verified junk.

---

## Requirements

- Windows recommended for the full desktop and installer flow
- Python 3.9+
- `pip`

Runtime dependencies are listed in `requirements.txt`. Canonical package metadata and optional extras are listed in `pyproject.toml`.

## Installation

### 1. Pre-built Installer (Recommended)
Download and run the `WasteWisely_Installer.exe` from the latest release.

### 2. Manual Setup
```bash
git clone https://github.com/Caliquende/WasteWisely.git
cd WasteWisely
pip install -r requirements.txt
```

---

## Build Dependencies

For packaging and installer work, use the build extras from `pyproject.toml`:

```bash
pip install ".[build]"
```

## Build the Windows .exe

Run the build on Windows from the repository root:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install ".[build]"
python build.py
```

The build script creates both executables in `dist`:

```text
dist\WasteWisely.exe
dist\WasteWisely_Installer.exe
```

`WasteWisely.exe` is the standalone desktop app. `WasteWisely_Installer.exe` is the UAC-enabled installer that copies the app into `C:\Program Files`.

## Usage

### Desktop Application
Launch via the desktop shortcut or:
```bash
python src/main.py app
```

### CLI Mode (Power Users)
```bash
python src/main.py scan C:\YourDir
```

### Background Daemon
Monitor a directory silently in the background:
```bash
python src/main.py daemon C:\Downloads
```

---

## Project Architecture

```
WasteWisely/
├── src/
│   ├── scanner.py      # High-speed directory walker
│   ├── classifier.py   # Business logic for waste categories
│   ├── actions.py      # Secure deletion & ZIP archival
│   ├── api.py          # FastAPI server
│   └── main.py         # App entrypoint & CLI
├── frontend/           # Modern Dark-mode UI (HTML/CSS/JS)
├── installer.py        # Windows Installer wizard (Tkinter)
├── build.py            # Automated build & packaging script
└── tests/              # Comprehensive test suite
```

---

## 🤝 Contributing
Feel free to open issues or submit PRs. This project follows strict QA standards (audited by Can as a Software QA Engineer).

Waiting references on [LinkedIn](https://www.linkedin.com/in/hamdi-can-ernalbanto%C4%9Fullar%C4%B1/)

## Validation

```bash
pytest
python src/main.py scan .
```

Before packaging, also validate the Windows desktop flow and installer update/uninstall behavior.

## Security

This project follows robust security protocols:
- **Dependabot:** Automated dependency and GitHub Actions updates.
- **CodeQL:** Static Application Security Testing (SAST) to detect vulnerabilities.
- **Security Policy:** Defined in [SECURITY.md](./SECURITY.md).
- **Proactive Scanning:** Integrated Bandit and pip-audit in CI/CD pipelines.
- **Pre-commit Hooks:** Local checks for secrets, private keys, and code quality.
