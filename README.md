# tbrowser v1.0.0

[![Test ve Derleme](https://github.com/eraykonur1234-debug/tbrowser/actions/workflows/build.yml/badge.svg)](https://github.com/eraykonur1234-debug/tbrowser/actions/workflows/build.yml)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-green.svg)
![PyQt6](https://img.shields.io/badge/Arayüz-PyQt6%20%2F%20Chromium-41cd52.svg)

Türkler tarafından geliştirilmiş; hızlı, hafif ve gizlilik odaklı masaüstü web tarayıcısı!

tbrowser, Chromium altyapısının gücünü minimalist ve koyu temalı bir arayüzle buluşturarak internette reklamsız, takipsiz ve özgürce gezinmenizi sağlar.

![tbrowser](https://github.com/user-attachments/assets/2bf52ac9-78ee-47e5-abea-403ba9897c0c)

---

## Hemen İndirin ve Deneyin!

Python veya ek bir kurulumla uğraşmanıza gerek yok! İşletim sisteminize uygun paketi indirip açarak doğrudan çalıştırabilirsiniz:

**👉 [GitHub Releases — v1.0.0 indir](https://github.com/eraykonur1234-debug/tbrowser/releases/tag/v1.0.0)**

| Platform | İndirilecek Paket | Çalıştırılacak Dosya |
| --- | --- | --- |
| **Windows** | `tbrowser-v1.0.0-windows-*.zip` | `tbrowser/tbrowser.exe` |
| **Linux** | `tbrowser-v1.0.0-linux-*.zip` | `tbrowser/tbrowser` |
| **macOS** | `tbrowser-v1.0.0-macos-*.zip` | `tbrowser/tbrowser` |

> Eski sürümler (`main4.py` / `main6.py` / `main7.py`) arşiv amaçlı korunmaktadır; 1.0 sürümü `tbrowser.py` + `tbrowser_core.py` üzerinden geliştirilmekte ve yalnızca GitHub Releases üzerinden dağıtılmaktadır.

---

## Öne Çıkan Özellikler

- **Dahili Reklam & Takipçi Engelleyici:** Ağ seviyesinde engelleme (`QWebEngineUrlRequestInterceptor`) + sayfa içi kozmetik filtreleme. Engellenen istek sayısı üstteki kalkan butonunda gösterilir, tek tıkla açılıp kapatılabilir.
- **Gelişmiş Çerez Yönetimi (1.0 düzeltmesi):**
  - Çoklu site çerezleri FIFO kuyrukla sıraya alınır — her site en fazla **bir kez** sorulur, sorular kaybolmaz.
  - İzin/engel kararları alt-domain duyarlıdır ve `QSettings` ile kalıcı saklanır.
  - Engellenen sitelerin çerezleri `setCookieFilter` ile daha kaydedilmeden önlenir.
  - Ayarlar penceresinden varsayılan çerez politikası seçilebilir (*Her site için sor* / *Her zaman izin ver* / *Her zaman engelle*).
- **Modern Koyu Tema:** Göz yormayan koyu arayüz, yükleme ilerleme çubuğu ve durdur/yenile düğmesi.
- **Çoklu Sekme & Popup Desteği:** Popup ve yeni pencere bağlantıları otomatik olarak yeni sekmede açılır; son sekme kapatıldığında yeni sekme başlatılır.
- **İndirme Yöneticisi:** Dosya indirmelerini anlık yüzde ve MB bilgisiyle takip edin.
- **Brave Search Entegrasyonu:** Varsayılan olarak Brave Arama Motoru ile açılır; adres çubuğuna yazılan arama sorguları doğrudan Brave Search ile aranır.

---

## Klavye Kısayolları

| Kısayol | İşlev |
| --- | --- |
| `Ctrl+T` | Yeni sekme aç |
| `Ctrl+W` | Geçerli sekmeyi kapat |
| `Ctrl+L` | Adres çubuğuna odaklan |
| `Ctrl+R` | Sayfayı yenile |
| `Esc` | Yüklemeyi durdur |

---

## Kaynaktan Çalıştırma

```bash
pip install -r requirements.txt
python tbrowser.py
```

## Kaynaktan Derleme (PyInstaller)

```bash
pip install -r requirements.txt
python build.py --clean
```

Çıktı: `release/` klasöründeki zip dosyası. Tüm platformlar (Windows, Linux, macOS) için otomatik derleme ve testler GitHub Actions üzerinden çalışır (`.github/workflows/build.yml`).

## Testler

```bash
pip install pytest
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v
```

---

## Görüş ve Geri Bildirimleriniz

tbrowser 1.0 artık kararlı sürümdür; geri bildirimleriniz yeni sürümlerin şekillenmesinde doğrudan rol oynayacaktır:

- **E-posta:** eraykonur1234@gmail.com
- **GitHub Issues:** [Hata Bildir / Öneri Paylaş](https://github.com/eraykonur1234-debug/tbrowser/issues)

## Lisans

MIT — bkz. [LICENSE](LICENSE). Tüm değişiklikler için [CHANGELOG.md](CHANGELOG.md).
