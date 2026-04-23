# 🗑️ WasteWisely — Profesyonel Dijital Atık Denetçisi

WasteWisely, "dijital atıkları" tespit etmek ve temizlemek için tasarlanmış yüksek performanslı bir Windows masaüstü uygulamasıdır. Sadece geçici dosyaları silmekle kalmaz; yazılım geliştirme kalıntılarını, hassas veri sızıntılarını ve bayatlamış büyük dosyaları akıllıca sınıflandırır.

[🇺🇸 Click for English documentation (README.md)](README.md)

---

## ✨ Temel Özellikler

### 🚀 Performans ve Arayüz
- **Native Desktop App:** Python & FastAPI tabanlı, `pywebview` ile sarmalanmış bağımsız pencere deneyimi.
- **Yerel Windows Diyalogları:** Sistem klasör seçicileriyle tam entegrasyon.
- **Dinamik Dashboard:** Donut grafikler ve etkileşimli Treemap (Alan Haritası) ile veri görselleştirme.
- **Çoklu Dil Desteği:** Türkçe, İngilizce ve Arapça (RTL desteği dahil) tam lokalizasyon.

### 🔍 Akıllı Tarama Motoru
- **Ağır Bağımlılıklar:** `node_modules`, `.venv` ve devasa build klasörlerini saptar.
- **Hassas Sızıntılar:** Açıkta kalan `.env`, private key ve kimlik bilgilerini tarar.
- **Bayatlık Filtresi:** 500MB üzerindeki büyük dosyalar, eğer son 90 gün içinde dokunulmamışsa "atık" olarak işaretlenir.
- **Sistem Koruması:** `pagefile.sys` gibi kritik Windows sistem dosyalarını otomatik olarak hariç tutar.

### 🛡️ Kurumsal Kurulum ve Güvenlik
- **UAC Yetki Yükseltme:** Installer, `C:\Program Files` dizinine yazabilmek için otomatik olarak Yönetici İzni ister.
- **Güvenli Kurulum:** Güncelleme veya kaldırma sırasında çalışan WasteWisely süreçlerini otomatik tespit eder ve sonlandırır.
- **İzole Loglama:** Yetki hatalarını önlemek için loglar `%TEMP%\WasteWisely` dizininde tutulur.

---

## 💻 Kurulum

### 1. Hazır Yükleyici (Önerilen)
En güncel sürümdeki `WasteWisely_Installer.exe` dosyasını indirin ve çalıştırın.

### 2. Manuel Kurulum
```bash
git clone https://github.com/Caliquende/WasteWisely.git
cd WasteWisely
pip install -r requirements.txt
pip install -r requirements-build.txt
```

---

## 🛠️ Kullanım

### Masaüstü Uygulaması
Masaüstü kısayolundan veya şu komutla başlatın:
```bash
python src/main.py app
```

### CLI Modu (İleri Seviye)
```bash
python src/main.py scan C:\HedefDizin
```

### Arka Plan Takip (Daemon)
Bir dizini arka planda sessizce izlemek için:
```bash
python src/main.py daemon C:\Downloads
```

---

## 📁 Proje Mimarisi

```
WasteWisely/
├── src/
│   ├── scanner.py      # Yüksek hızlı dizin tarayıcı
│   ├── classifier.py   # Atık kategorizasyon mantığı
│   ├── actions.py      # Güvenli silme ve ZIP arşivleme
│   ├── api.py          # FastAPI backend sunucusu
│   └── main.py         # Uygulama giriş noktası ve CLI
├── frontend/           # Modern Dark-mode UI (HTML/CSS/JS)
├── installer.py        # Windows Kurulum Sihirbazı (Tkinter)
├── build.py            # Otomatik derleme ve paketleme scripti
└── tests/              # Kapsamlı test paketi
```

---

Bu proje Software Consulting Agent Company kalite denetimlerinden geçmiştir.
