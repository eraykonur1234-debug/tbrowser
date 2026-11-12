# Değişiklik Günlüğü

Tüm önemli değişiklikler bu dosyada belgelenir.
Biçim: [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) — Sürümleme: [SemVer](https://semver.org/lang/tr/)

## [1.0.0] - 2026-11-12

### Düzeltildi — Çerez hatası
- **Sonsuz soru döngüsü düzeltildi:** Eski sürümlerde tek bir `su_anki_domain` değişkeni vardı; birden çok site çerez gönderdiğinde son domain öncekilerin üzerine yazıyordu. "İzin Ver" yalnızca son siteyi hatırlıyor, diğer siteler her seferinde yeniden soruluyordu. 1.0'da her domain için FIFO kuyruk kullanılıyor; her site en fazla bir kez sorulur.
- **Çubuk titremesi düzeltildi:** Her çerezde soru çubuğu yeniden gösterilip etiketi değişiyordu. Artık aynı domainin çerezleri birikir, çubuk yalnızca sıradaki domain için gösterilir ve bekleyen çerez sayısı yazılır.
- **Domain eşleşmesi düzeltildi:** Karşılaştırma artık küçük harf duyarsız ve alt-domain duyarlı (`sub.example.com`, izinli `example.com` ile eşleşir; `fakeexample.com` eşleşmez). En özel eşleşme kazanır, eşitlikte engel önceliklidir.
- **Host-only çerezler:** Boş domain'li çerezler artık `""` domain'iyle sorulmuyor; sessizce izin veriliyor.
- **Kalıcılık eklendi:** Site bazlı izin/engel kararları ve varsayılan politika QSettings ile saklanıyor; tarayıcı her açılışta aynı sitelere yeniden sormuyor.

### Eklendi
- Çerez politikası ayarı (sor / her zaman izin ver / her zaman engelle) ve geçmiş temizleme.
- Ana sayfa (⌂) butonu, yükleme çubuğu, yenile/durdur düğmesi.
- Klavye kısayolları: Ctrl+T (yeni sekme), Ctrl+W (kapat), Ctrl+L (adres çubuğu), Ctrl+R (yenile), Esc (durdur).
- Popup / `target="_blank"` bağlantıları yeni sekmede açılır.
- Adres çubuğunda arama desteği: boşluk içeren veya noktasız metin Brave Search ile aranır.
- AdBlocker durumu ve pencere konumu kalıcı saklanır; engellenen sayısı butonda gösterilir.
- Birim testleri (`tests/`), PyInstaller derleme betiği (`build.py`, `tbrowser.spec`) ve GitHub Actions ile otomatik Windows/Linux/macOS derlemesi.

### Değişti
- Tek giriş noktası: `tbrowser.py` (GUI) + `tbrowser_core.py` (çekirdek mantık). `main4.py`/`main6.py`/`main7.py` eski prototipler olarak arşivde tutulur.
- AdBlocker: ana sayfa (main frame) engellenmez; yol içeren ölü filtre girdileri düzeltildi; kozmetik filtre AdBlocker kapatılınca kaldırılır.
- Sekme kapatma: son sekme kapatılınca yeni sekme açılır, widget bellekten temizlenir.

### Kaldırıldı
- Yok.
