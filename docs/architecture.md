# WasteWisely - Teknik Mimari Tasarımı

**Sürüm:** 1.0.0  
**Durum:** Onaylandı  
**Sorumlu:** solution-architect

## 1. Bağlam ve Kapsam
WasteWisely, yerel dosya sistemini analiz ederek atık tespiti yapacak bir araçtır. İlk aşamada güçlü bir CLI engine (çekirdek) üzerine inşa edilecek, ardından basit bir yerel web arayüzü ile desteklenecektir.

## 2. Önerilen Teknoloji Yığını
- **Dil:** Python 3.10+ (Zengin kütüphane desteği ve hızlı prototipleme için).
- **Core Libraries:**
    - `pathlib`: Modern dosya yolu yönetimi.
    - `scout`: (Kurgusal veya mevcut hızlı tarama pattern'i) Recursive dosya tarama.
    - `GitPython`: Git reposu tarihlerini ve durumlarını okumak için.
- **Arayüz (Opsiyonel/Faz 2):** FastAPI (Backend) + React/Vite (Frontend).

## 3. Modüler Yapı
1. **Scanner Module:** Dosya ağacını gezer, metadata (size, mtime) toplar.
2. **Classifier Module:** Toplanan verileri PRD'deki kurallara (Forgotten Repo, Heavy Deps vb.) göre sınıflandırır.
3. **Action Module:** Silme, arşivleme (zip) ve raporlama işlemlerini yönetir.
4. **Storage (Memory-based):** Başlangıçta veriler bellek üzerinde tutulacak, büyük taramalar için opsiyonel bir SQLite katmanı eklenecektir.

## 4. Karar Gerekçesi
- **Neden Python?** Dosya meta-verileriyle çalışmak ve AI tabanlı sınıflandırma (ileride) için Python en esnek ortamı sunar. Ayrıca `os` ve `pathlib` kütüphaneleri Windows/Linux uyumluluğunu kolaylaştırır.

## 5. Riskler ve Doğrulama
- **Risk:** Sembolik linkler (Symlinks) nedeniyle sonsuz döngüye girme.
- **Önlem:** `follow_symlinks=False` varsayılan olarak kullanılacak.
- **Doğrulama:** Farklı boyutlarda (100 dosya vs 100.000 dosya) stres testleri yapılacaktır.

## 6. Uygulama Adımları
1. Proje yapısının (`src/`, `tests/`) kurulması.
2. `Scanner` sınıfının `pathlib` ile implementasyonu.
3. Git reposu durumunu kontrol eden `GitClassifier` modülünün eklenmesi.
4. CLI arayüzünün (argparse) yazılması.
