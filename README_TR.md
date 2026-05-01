# WasteWisely - Profesyonel Dijital Atık Denetçisi

![WasteWisely Header](assets/header.png)

WasteWisely, "dijital atıkları" tespit etmek ve temizlemek için tasarlanmış yüksek performanslı bir Windows masaüstü uygulamasıdır. Sadece geçici dosyaları silmekle kalmaz; yazılım geliştirme kalıntılarını, hassas veri sızıntılarını ve bayatlamış büyük dosyaları akıllıca sınıflandırır.

[🇺🇸 Click for English documentation (README.md)](README.md)

---

## Temel Özellikler

### Performans ve Arayüz
- **Native Desktop App:** Python & FastAPI tabanlı, `pywebview` ile sarmalanmış bağımsız pencere deneyimi.
- **Yerel Windows Diyalogları:** Sistem klasör seçicileriyle tam entegrasyon.
- **Dinamik Dashboard:** Donut grafikler ve etkileşimli Treemap (Alan Haritası) ile veri görselleştirme.
- **Çoklu Dil Desteği:** Türkçe, İngilizce ve Arapça (RTL desteği dahil) tam lokalizasyon.

### Akıllı Tarama Motoru
- **Ağır Bağımlılıklar:** `node_modules`, `.venv` ve devasa build klasörlerini saptar.
- **Hassas Sızıntılar:** Açıkta kalan `.env`, private key ve kimlik bilgilerini tarar.
- **Bayatlık Filtresi:** 500MB üzerindeki büyük dosyalar, eğer son 90 gün içinde dokunulmamışsa "atık" olarak işaretlenir.
- **Sistem Koruması:** `pagefile.sys` gibi kritik Windows sistem dosyalarını otomatik olarak hariç tutar.

### Kurumsal Kurulum ve Güvenlik
- **UAC Yetki Yükseltme:** Installer, `C:\Program Files` dizinine yazabilmek için otomatik olarak Yönetici İzni ister.
- **Güvenli Kurulum:** Güncelleme veya kaldırma sırasında çalışan WasteWisely süreçlerini otomatik tespit eder ve sonlandırır.
- **İzole Loglama:** Yetki hatalarını önlemek için loglar `%TEMP%\WasteWisely` dizininde tutulur.

### Akıllı Aksiyonlar
- **Güvenli Arşivleme:** Doğrudan silmek yerine, dosyaları gizli bir `.wastewise_archive` dizini içinde ZIP olarak saklayın. "Ya lazım olursa?" durumları için idealdir.
- **Kalıcı Temizlik:** Doğrulanmış çöpler için tek tıkla kalıcı silme.

---

## Gereksinimler

- Tam masaüstü ve installer akışı için Windows önerilir
- Python 3.9+
- `pip`

Runtime bağımlılıkları `requirements.txt` içinde listelenir. Ana paket metadata'sı ve opsiyonel ekstra bağımlılıklar `pyproject.toml` içinde tutulur.

## Kurulum

### 1. Hazır Yükleyici (Önerilen)
En güncel sürümdeki `WasteWisely_Installer.exe` dosyasını indirin ve çalıştırın.

### 2. Manuel Kurulum
```bash
git clone https://github.com/Caliquende/WasteWisely.git
cd WasteWisely
pip install -r requirements.txt
```

---

## Build Bağımlılıkları

Paketleme ve installer çalışmaları için `pyproject.toml` içindeki build ekstra bağımlılıklarını kullanın:

```bash
pip install ".[build]"
```

## Windows .exe Üretme

Build işlemini Windows üzerinde repo kök dizininden çalıştırın:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install ".[build]"
python build.py
```

Build scripti iki çıktıyı `dist` klasörüne üretir:

```text
dist\WasteWisely.exe
dist\WasteWisely_Installer.exe
```

`WasteWisely.exe` bağımsız masaüstü uygulamasıdır. `WasteWisely_Installer.exe`, uygulamayı `C:\Program Files` altına kuran UAC yetkili installer dosyasıdır.

## Kullanım

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

## Proje Mimarisi

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

## 🤝 Katkıda Bulunma
Issue açmaktan veya PR göndermekten çekinmeyin. Bu proje, Yazılım QA Mühendisi Can tarafından denetlenmiş sıkı QA standartlarını takip eder.

[LinkedIn](https://www.linkedin.com/in/hamdi-can-ernalbanto%C4%9Fullar%C4%B1/) üzerinden referanslarınızı bekliyorum.

## Doğrulama

```bash
pytest
python src/main.py scan .
```

Paketlemeden önce Windows masaüstü akışını ve installer güncelleme/kaldırma davranışını da doğrulayın.

## Güvenlik

Bu proje kapsamlı güvenlik protokollerini takip eder:
- **Dependabot:** Otomatik bağımlılık ve GitHub Actions güncellemeleri.
- **CodeQL:** Güvenlik açıklarını tespit etmek için Statik Uygulama Güvenlik Testi (SAST).
- **Güvenlik Politikası:** [SECURITY.md](./SECURITY.md) dosyasında tanımlanmıştır.
- **Proaktif Tarama:** CI/CD süreçlerine entegre Bandit ve pip-audit araçları.
- **Pre-commit Kancaları:** Şifre sızıntısı ve kod kalitesi için yerel kontroller.
