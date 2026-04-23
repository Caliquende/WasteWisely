# 🗑️ WasteWise — Dijital Atık Denetçisi

[🇺🇸 Click for English documentation (README.md)](README.md)

Dosya sisteminizi tarayarak **dijital atıkları** tespit eden ve temizlik önerileri sunan akıllı araç.

## ✨ Özellikler

| Kategori | Tespit Edilen |
|---|---|
| 📦 **Ağır Bağımlılıklar** | `node_modules`, `.venv`, `target`, `build` vb. |
| 🔑 **Hassas Sızıntılar** | `.env`, `.pem`, `id_rsa`, `credentials.json` |
| 👻 **Hayalet Dosyalar** | `.DS_Store`, `Thumbs.db`, `.log`, `.tmp` |
| 🕸️ **Unutulmuş Projeler** | 6+ aydır dokunulmamış git repoları |
| 💾 **Büyük Dosyalar** | 50 MB+ dosyalar |

## 🚀 Kurulum

```bash
cd WasteWise
pip install -r requirements.txt
```

### Geliştirme ve UI Testleri
```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
```

### Desktop / Build Araçları
```bash
pip install -r requirements-build.txt
```

## 💻 Kullanım

### CLI ile Tarama
```bash
cd src
python main.py scan C:\Users\Can\work
```

### Web Dashboard
```bash
cd src
python api.py
# Tarayıcıda http://localhost:8000 adresini aç
```

### Varsayılan Başlatma
```bash
python src/main.py
```

Not:
- `pywebview` yüklüyse desktop app açılır.
- Değilse güvenli varsayılan olarak yerel web sunucusu (`serve`) başlar.

## 🧪 Testler
```bash
cd WasteWise
python -m pytest tests -v
```

## 📁 Proje Yapısı
```
WasteWise/
├── src/
│   ├── scanner.py      # Dosya sistemi tarama motoru
│   ├── classifier.py   # Atık sınıflandırma mantığı
│   ├── actions.py      # Güvenli silme/arşivleme
│   ├── api.py          # FastAPI backend
│   └── main.py         # CLI arayüzü
├── frontend/
│   ├── index.html      # Dashboard HTML
│   ├── style.css       # Premium dark theme
│   └── app.js          # Frontend controller
├── tests/
│   ├── test_scanner.py
│   └── test_classifier.py
├── docs/
│   ├── spec.md         # Ürün spesifikasyonu
│   └── architecture.md # Teknik mimari
├── requirements.txt
└── README.md
```
