# 🗑️ WasteWise — Digital Waste Auditor

A smart tool that scans your file system to detect **digital waste** and provides cleaning suggestions.

[🇹🇷 Türkçe dökümantasyon için tıklayın (README_TR.md)](README_TR.md)

## ✨ Features

| Category | Detected Items |
|---|---|
| 📦 **Heavy Dependencies** | `node_modules`, `.venv`, `target`, `build`, etc. |
| 🔑 **Sensitive Leaks** | `.env`, `.pem`, `id_rsa`, `credentials.json` |
| 👻 **Ghost Files** | `.DS_Store`, `Thumbs.db`, `.log`, `.tmp` |
| 🕸️ **Stale Projects** | Large files/projects untouched for 90+ days |
| 💾 **Large Files** | 500 MB+ files |

## 🚀 Installation

```bash
cd WasteWise
pip install -r requirements.txt
```

### Desktop / Build Tools
```bash
pip install -r requirements-build.txt
```

## 💻 Usage

### Desktop App (Recommended)
Run the bundled installer `dist/WasteWise_Installer.exe` or launch via:
```bash
python src/main.py app
```

### CLI Scan
```bash
python src/main.py scan C:\path\to\scan
```

### Web Dashboard
```bash
python src/main.py serve
# Open http://localhost:8000 in your browser
```

## 🧪 Tests
```bash
python -m pytest tests -v
```

## 📁 Project Structure
```
WasteWise/
├── src/
│   ├── scanner.py      # File system scanning engine
│   ├── classifier.py   # Waste classification logic
│   ├── actions.py      # Secure delete/archive actions
│   ├── api.py          # FastAPI backend
│   └── main.py         # CLI & App entrypoint
├── frontend/
│   ├── index.html      # Dashboard UI
│   ├── style.css       # Premium dark theme
│   └── app.js          # Frontend controller
├── tests/
│   ├── test_scanner.py
│   └── test_classifier.py
├── docs/
│   ├── spec.md         # Product specification
│   └── architecture.md # Technical architecture
├── requirements.txt
└── README.md
```
