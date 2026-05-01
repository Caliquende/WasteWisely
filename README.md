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

### New Marketplace Demo
- **Customer storefront:** Campaign slider, category navigation, search, sorting, favorites, comparison, product detail URLs, cart, and sandbox checkout.
- **Role dashboards:** Admin, seller, marketing, finance, and support dashboards for marketplace operations.
- **Local demo assets:** Product images live under `public/demo-products` so the UI does not depend on external image URLs at runtime.
- **Local Express API:** `server/index.mjs` serves marketplace seed data and sandbox demo orders.
- **Language toggle:** The marketplace UI is English-first with Turkish localization in `src/i18n.ts`.

---

## Requirements

- Windows recommended for the full desktop and installer flow
- Python 3.9+
- `pip`
- Node.js 20+ and `npm` for the marketplace demo

Runtime dependencies are listed in `requirements.txt`. Canonical package metadata and optional extras are listed in `pyproject.toml`.
Marketplace runtime and build dependencies are listed in `package.json`.

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

### Marketplace Demo
```powershell
npm install
npm run dev
```

Default local addresses:

- Customer storefront: `http://localhost:5173`
- API: `http://localhost:4000`
- Health check: `http://localhost:4000/api/health`

Demo routes:

- `http://localhost:5173` - public customer storefront
- `http://localhost:5173/musteri` - customer storefront alias
- `http://localhost:5173/lilabook-pro-14` - product detail page example
- `http://localhost:5173/admin` - admin control dashboard
- `http://localhost:5173/satici1` - seller catalog and stock use-case
- `http://localhost:5173/satici2` - seller performance and payout use-case
- `http://localhost:5173/marketing1` - marketing campaign use-case
- `http://localhost:5173/marketing2` - marketing SEO and moderation use-case
- `http://localhost:5173/finans1` - finance payment and refund use-case
- `http://localhost:5173/finans2` - finance payout and reconciliation use-case
- `http://localhost:5173/destek1` - support order/refund use-case
- `http://localhost:5173/destek2` - support live support and seller question use-case

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
├── public/             # Marketplace static assets and demo product images
├── server/             # Marketplace Express API
├── installer.py        # Windows Installer wizard (Tkinter)
├── build.py            # Automated build & packaging script
├── package.json        # Marketplace scripts and Node dependencies
└── tests/              # Comprehensive test suite
```

Marketplace extension points:

- `server/index.mjs`: demo API boundary that can later connect to real backend services.
- `src/api.ts`: frontend API adapter layer.
- `src/data.ts`: frontend types and fallback seed data.
- `src/i18n.ts`: English and Turkish UI copy.
- `src/App.tsx`: demo screen flows, routes, product detail behavior, and dashboard interactions.
- `src/App.css`: responsive UI and dashboard layout.

---

## 🤝 Contributing
Feel free to open issues or submit PRs. This project follows strict QA standards (audited by Can as a Software QA Engineer).

Waiting references on [LinkedIn](https://www.linkedin.com/in/hamdi-can-ernalbanto%C4%9Fullar%C4%B1/)

## Validation

```bash
pytest
python src/main.py scan .
npm run lint
npm run build
```

Before packaging, also validate the Windows desktop flow and installer update/uninstall behavior.

The marketplace is intentionally a demo delivery, not a production marketplace backend. Payment, shipping, invoice, analytics, and compliance integrations are mock or sandbox boundaries and need production review before go-live.

## Security

This project follows robust security protocols:
- **Dependabot:** Automated dependency and GitHub Actions updates.
- **CodeQL:** Static Application Security Testing (SAST) to detect vulnerabilities.
- **Security Policy:** Defined in [SECURITY.md](./SECURITY.md).
- **Proactive Scanning:** Integrated Bandit and pip-audit in CI/CD pipelines.
- **Marketplace Scanning:** CI includes npm audit, secret scanning, and unsafe JS pattern detection for the marketplace demo.
- **Pre-commit Hooks:** Local checks for secrets, private keys, and code quality.

