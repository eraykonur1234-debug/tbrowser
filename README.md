# tbrowser v1.0.0

Türkler tarafından geliştirilmiş; hızlı, hafif ve gizlilik odaklı masaüstü web tarayıcısı!

tbrowser, Chromium altyapısının gücünü minimalist bir arayüzle buluşturarak internette reklamsız ve özgürce gezinmenizi sağlar.

![tbrowser](https://github.com/user-attachments/assets/2bf52ac9-78ee-47e5-abea-403ba9897c0c)

## Hemen İndirin ve Deneyin!

Python veya ek bir kurulumla uğraşmanıza gerek yok! İndirdiğiniz paketi açıp çalıştırmanız yeterlidir:

**👉 [GitHub Releases — v1.0.0 indir](https://github.com/eraykonur1234-debug/tbrowser/releases/tag/v1.0.0)**

- **Windows:** `tbrowser-v1.0.0-windows-*.zip` içindeki `tbrowser.exe`
- **Linux:** `tbrowser-v1.0.0-linux-*.zip` içindeki `tbrowser`
- **macOS:** `tbrowser-v1.0.0-macos-*.zip` içindeki `tbrowser`

> Eski sürümler (v0.4 / v0.6 / v0.7) Google Drive bağlantıları arşiv amaçlı korunmaktadır; yeni sürümler yalnızca GitHub Releases üzerinden dağıtılır.

## Öne Çıkan Özellikler

- **Dahili Reklam & Takipçi Engelleyici:** Ağ seviyesinde entegre engelleme sistemi sayesinde reklamlarla boğuşmadan hızlı gezinti. Engellenen sayısı butonda gösterilir, tek tıkla açılıp kapatılır.
- **Gelişmiş Çerez Yönetimi (1.0 düzeltmesi):** Her site en fazla bir kez sorulur, kararınız hatırlanır. Varsayılan politika ayarlardan değiştirilebilir (sor / her zaman izin ver / her zaman engelle).
- **Modern Koyu Tema:** Göz yormayan estetik koyu arayüz.
- **Çoklu Sekme Desteği:** Sekmeler arasında takılmadan geçiş, popup bağlantıları yeni sekmede açılır.
- **İndirme Yöneticisi:** Dosya indirmelerinizi anlık yüzde ve durum bilgisiyle takip edin.
- **Brave Search Entegrasyonu:** Varsayılan olarak gizliliğinizi koruyan Brave Arama Motoru ile açılır; adres çubuğuna yazdığınız arama sorguları da Brave ile aranır.
- **Klavye Kısayolları:** `Ctrl+T` yeni sekme, `Ctrl+W` kapat, `Ctrl+L` adres çubuğu, `Ctrl+R` yenile, `Esc` durdur.

## Kaynaktan Çalıştırma

```bash
pip install -r requirements.txt
python tbrowser.py
```

## Kaynaktan Derleme

```bash
pip install -r requirements.txt
python build.py --clean
```

Çıktı: `release/` klasöründeki zip dosyası. Tüm platformlar için otomatik derleme GitHub Actions ile yapılır (`.github/workflows/build.yml`).

## Testler

```bash
pip install pytest
QT_QPA_PLATFORM=offscreen pytest tests/ -v
```

## Çerez Politikası Nasıl Çalışır?

1. Bir site ilk kez çerez gönderdiğinde üstte bir soru çubuğu belirir.
2. **İzin Ver** veya **Reddet** dediğinizde kararınız o site için hatırlanır; bir daha sorulmaz.
3. Aynı anda birden çok site çerez gönderirse sorular sırayla (kuyruk) gösterilir; hiçbiri kaybolmaz.
4. Ayarlar (⚙️) penceresinden varsayılan politikayı değiştirebilir, tüm çerezleri ve geçmişi temizleyebilirsiniz.

## Görüş ve Geri Bildirimleriniz Çok Değerli!

tbrowser 1.0 artık kararlı sürümdür; ancak geri bildirimleriniz hâlâ sonraki sürümlerin şekillenmesinde doğrudan rol oynayacaktır. Hataları, eksikleri ve önerilerinizi paylaşın:

- **E-posta:** eraykonur1234@gmail.com
- **GitHub Issues:** [Hata Bildir](https://github.com/eraykonur1234-debug/tbrowser/issues)

Şimdiden vakit ayırıp denediğiniz ve destek olduğunuz için teşekkürler!

## Lisans

MIT — bkz. [LICENSE](LICENSE). Değişiklik geçmişi için [CHANGELOG.md](CHANGELOG.md).
