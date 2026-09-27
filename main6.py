import sys
import os
import re
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
    QWebEngineScript,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QDialog,
    QCheckBox,
    QGroupBox,
    QMessageBox,
)


# --- GELİŞMİŞ & REGEX DESTEKLİ ADBLOCKER MEKANİZMASI ---
class AdBlocker(QWebEngineUrlRequestInterceptor):

    def __init__(self):
        super().__init__()
        self.aktif = True  # AdBlocker varsayılan açık

        # 1. Tam Domain ve Alt Domain Taraması
        self.reklam_domainleri = {
            "doubleclick.net",
            "googleadservices.com",
            "googlesyndication.com",
            "adnxs.com",
            "amazon-adsystem.com",
            "adservice.google.com",
            "criteo.com",
            "outbrain.com",
            "taboola.com",
            "popads.net",
            "popcash.net",
            "adroll.com",
            "scorecardresearch.com",
            "analytics.google.com",
            "hotjar.com",
            "yandex.ru/metrika",
            "clarity.ms",
            "connect.facebook.net/gtm",
            "adform.net",
            "yieldmanager.com",
            "pubmatic.com",
            "rubiconproject.com",
            "smartadserver.com",
            "openx.net",
            "exponential.com",
            "quantserve.com",
            "exoclick.com",
            "a-ads.com",
            "propellerads.com",
            "juicyads.com",
            "trafficjunky.net",
            "adsterra.com",
            "coinzilla.com",
            "buyads.com",
            "carbonads.net",
            "adblade.com",
            "revcontent.com",
            "media.net",
            "mgid.com",
            "zedo.com",
            "adthis.com",
            "addthis.com",
            "moatads.com",
            "adtech.de",
            "serving-sys.com",
            "bidswitch.net",
            "casalemedia.com",
            "indexww.com",
            "teads.tv",
            "mathtag.com",
            "mopub.com",
            "inmobi.com",
            "unityads.unity3d.com",
            "applovin.com",
            "ironsrc.com",
            "vungle.com",
            "tapjoy.com",
            "chartboost.com",
            "fyber.com",
            "flurry.com",
            "bugsnag.com",
            "sentry.io",
            "mixpanel.com",
            "segment.io",
            "amplitude.com",
            "heap.io",
            "mouseflow.com",
            "inspectlet.com",
            "crazyegg.com",
            "optimizely.com",
            "vwo.com",
        }

        # 2. Test Sitelerini Yakalayan Regex (Düzenli İfade) Kalıpları
        self.regex_kaliplari = [
            re.compile(
                r"[/\?\=&\._](ad|ads|adsystem|adserver|adservice|adframe|adtrack|banner|popunder|popup|sponsor|telemetry|analytics|tracker)[/\?\=&\._]",
                re.IGNORECASE,
            ),
            re.compile(
                r"(pagead2|googlesyndication|doubleclick|google-analytics|pixel\.facebook|analytics\.tiktok)",
                re.IGNORECASE,
            ),
            re.compile(
                r"/ad(s)?/(banner|script|view|click|serve|fetch)", re.IGNORECASE
            ),
        ]

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        if not self.aktif:
            return

        url = info.requestUrl().toString()
        host = info.requestUrl().host()

        # Domain Kontrolü
        for domain in self.reklam_domainleri:
            if domain in host or host.endswith("." + domain):
                info.block(True)
                return

        # Regex Kalıp Kontrolü
        for regex in self.regex_kaliplari:
            if regex.search(url):
                info.block(True)
                return


# --- AYARLAR PENCERESİ ---
class AyarlarPenceresi(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_win = parent
        self.setWindowTitle("tbrowser - Ayarlar")
        self.resize(400, 260)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            QLabel { color: #cdd6f4; font-size: 13px; }
            QGroupBox { color: #89b4fa; font-weight: bold; border: 1px solid #45475a; border-radius: 6px; margin-top: 10px; padding-top: 10px; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px; }
            QPushButton:hover { background-color: #45475a; }
            QCheckBox { color: #cdd6f4; font-weight: bold; }
        """)

        layout = QVBoxLayout()

        # AdBlocker Ayarları
        group_adblock = QGroupBox("Reklam Engelleyici")
        adblock_layout = QVBoxLayout()
        self.chk_adblock = QCheckBox("AdBlocker Etkinleştir")
        self.chk_adblock.setChecked(self.main_win.adblocker.aktif)
        self.chk_adblock.stateChanged.connect(
            self.main_win.toggle_adblock_from_settings
        )
        adblock_layout.addWidget(self.chk_adblock)
        group_adblock.setLayout(adblock_layout)

        # Gizlilik Ayarları
        group_cookie = QGroupBox("Çerezler ve Temizlik")
        cookie_layout = QVBoxLayout()

        btn_temizle = QPushButton("Tüm Çerezleri ve Geçmişi Sıfırla")
        btn_temizle.clicked.connect(self.cerezleri_temizle)

        cookie_layout.addWidget(btn_temizle)
        group_cookie.setLayout(cookie_layout)

        layout.addWidget(group_adblock)
        layout.addWidget(group_cookie)
        layout.addStretch()

        btn_kapat = QPushButton("Kapat")
        btn_kapat.clicked.connect(self.close)
        layout.addWidget(btn_kapat)

        self.setLayout(layout)

    def cerezleri_temizle(self):
        self.main_win.cookie_store.deleteAllCookies()
        self.main_win.izin_verilen_domainler.clear()
        self.main_win.engellenen_domainler.clear()
        QMessageBox.information(
            self, "Başarılı", "Tüm çerezler ve site izinleri temizlendi!"
        )


class Tarayici(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("tbrowser")
        self.resize(1200, 800)

        # Çerez izin listeleri
        self.izin_verilen_domainler = set()
        self.engellenen_domainler = set()
        self.bekleyen_cerezler = []

        # Koyu Tema Stili
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background: #2b2b3b;
                color: #a6adc8;
                padding: 8px 15px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #11111b;
                color: #cdd6f4;
                font-weight: bold;
            }
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QStatusBar {
                background-color: #11111b;
                color: #a6adc8;
            }
        """)

        # Kalıcı Profil Ayarları
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )

        self.adblocker = AdBlocker()
        self.profile.setUrlRequestInterceptor(self.adblocker)

        # --- COSMETIC FILTERING (SAYFA İÇİ REKLAM GİZLEME JS ENJEKSİYONU) ---
        self.adblock_script_ekle()

        # İndirme ve Çerez Yöneticileri
        self.profile.downloadRequested.connect(self.indirme_isleyicisi)
        self.cookie_store = self.profile.cookieStore()
        self.cookie_store.cookieAdded.connect(self.cerez_eklendi_kontrol)

        # Sekme Yöneticisi
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.sekme_kapat)
        self.tabs.currentChanged.connect(self.sekme_degisti)

        # Butonlar
        btn_geri = QPushButton("◄")
        btn_ileri = QPushButton("►")
        btn_yenile = QPushButton("↻")
        btn_yeni_sekme = QPushButton("+")
        btn_ayarlar = QPushButton("⚙️")

        # AdBlocker Geçiş Butonu
        self.btn_adblock = QPushButton()
        self.adblock_buton_guncelle()
        self.btn_adblock.clicked.connect(self.toggle_adblock_button)
        btn_ayarlar.clicked.connect(self.ayarlari_ac)

        btn_geri.clicked.connect(self.mevcut_browser_geri)
        btn_ileri.clicked.connect(self.mevcut_browser_ileri)
        btn_yenile.clicked.connect(self.mevcut_browser_yenile)
        btn_yeni_sekme.clicked.connect(lambda: self.yeni_sekme_ekle())

        # Adres Çubuğu
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.git_url)

        # Üst Bar Düzeni
        top_bar = QHBoxLayout()
        top_bar.addWidget(btn_geri)
        top_bar.addWidget(btn_ileri)
        top_bar.addWidget(btn_yenile)
        top_bar.addWidget(self.url_bar)
        top_bar.addWidget(self.btn_adblock)
        top_bar.addWidget(btn_ayarlar)
        top_bar.addWidget(btn_yeni_sekme)

        # Çerez İzin Barı
        self.cerez_bar = QWidget()
        self.cerez_bar.setStyleSheet(
            "background-color: #313244; border-radius: 8px; padding: 5px;"
        )
        cerez_layout = QHBoxLayout()

        self.cerez_label = QLabel("Bu siteye ait çerezler kaydedilsin mi?")
        self.cerez_label.setStyleSheet("color: #cdd6f4; font-weight: bold;")

        btn_cerez_izin = QPushButton("İzin Ver")
        btn_cerez_izin.setStyleSheet(
            "background-color: #a6e3a1; color: #11111b; font-weight: bold;"
        )
        btn_cerez_izin.clicked.connect(self.cerez_izin_ver)

        btn_cerez_red = QPushButton("Reddet")
        btn_cerez_red.setStyleSheet(
            "background-color: #f38ba8; color: #11111b; font-weight: bold;"
        )
        btn_cerez_red.clicked.connect(self.cerez_reddet)

        cerez_layout.addWidget(self.cerez_label)
        cerez_layout.addStretch()
        cerez_layout.addWidget(btn_cerez_izin)
        cerez_layout.addWidget(btn_cerez_red)
        self.cerez_bar.setLayout(cerez_layout)
        self.cerez_bar.hide()

        # Ana Düzen
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.cerez_bar)
        main_layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.statusBar().showMessage("tbrowser Güvenli Modda Hazır")

        # İlk Sekme
        self.yeni_sekme_ekle(QUrl("https://search.brave.com/"), "Brave Search")

    def adblock_script_ekle(self):
        script = QWebEngineScript()
        js_code = """
        (function() {
            var style = document.createElement('style');
            style.innerHTML = `
                [id*="google_ads"], [class*="ad-box"], [class*="ad-container"],
                [class*="sponsored"], iframe[src*="doubleclick"], iframe[src*="ad"],
                .ad-banner, .ad-slot, .ad-wrapper, div[id^="dfp-ad"] {
                    display: none !important;
                    visibility: hidden !important;
                    height: 0 !important;
                }
            `;
            document.head.appendChild(style);
        })();
        """
        script.setSourceCode(js_code)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        self.profile.scripts().insert(script)

    # --- ADBLOCKER AÇ / KAPAT MANTIĞI ---
    def toggle_adblock_button(self):
        self.adblocker.aktif = not self.adblocker.aktif
        self.adblock_buton_guncelle()
        if self.tabs.currentWidget():
            self.tabs.currentWidget().reload()

    def toggle_adblock_from_settings(self, state):
        self.adblocker.aktif = bool(state)
        self.adblock_buton_guncelle()
        if self.tabs.currentWidget():
            self.tabs.currentWidget().reload()

    def adblock_buton_guncelle(self):
        if self.adblocker.aktif:
            self.btn_adblock.setText("🛡️ AdBlocker Açık")
            self.btn_adblock.setStyleSheet(
                "color: #a6e3a1; font-weight: bold; border: 1px solid #a6e3a1;"
            )
        else:
            self.btn_adblock.setText("🛡️ AdBlocker Kapalı")
            self.btn_adblock.setStyleSheet(
                "color: #f38ba8; font-weight: bold; border: 1px solid #f38ba8;"
            )

    def ayarlari_ac(self):
        dlg = AyarlarPenceresi(self)
        dlg.exec()

    def yeni_sekme_ekle(
        self, qurl=QUrl("https://search.brave.com/"), label="Yeni Sekme"
    ):
        browser = QWebEngineView()
        browser.setUrl(qurl)

        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

        browser.urlChanged.connect(
            lambda qurl, browser=browser: self.url_guncelle(qurl, browser)
        )
        browser.titleChanged.connect(
            lambda title, browser=browser: self.baslik_guncelle(title, browser)
        )

    # --- Çerez Mantığı ---
    def cerez_eklendi_kontrol(self, cookie):
        domain = cookie.domain().lstrip(".")

        if domain in self.izin_verilen_domainler:
            return
        elif domain in self.engellenen_domainler:
            self.cookie_store.deleteCookie(cookie)
            return

        self.su_anki_domain = domain
        self.bekleyen_cerezler.append(cookie)

        self.cerez_label.setText(
            f"'{domain}' sitesine ait çerezler kaydedilsin mi?"
        )
        self.cerez_bar.show()

    def cerez_izin_ver(self):
        if hasattr(self, "su_anki_domain"):
            self.izin_verilen_domainler.add(self.su_anki_domain)
            self.statusBar().showMessage(
                f"{self.su_anki_domain} için çerezlere izin verildi.", 4000
            )
        self.bekleyen_cerezler.clear()
        self.cerez_bar.hide()

    def cerez_reddet(self):
        if hasattr(self, "su_anki_domain"):
            self.engellenen_domainler.add(self.su_anki_domain)
            for cookie in self.bekleyen_cerezler:
                self.cookie_store.deleteCookie(cookie)
            self.statusBar().showMessage(
                f"{self.su_anki_domain} çerezleri engellendi ve silindi.", 4000
            )
        self.bekleyen_cerezler.clear()
        self.cerez_bar.hide()

    # --- İndirme Mantığı ---
    def indirme_isleyicisi(self, download):
        varsayilan_yol = (
            download.downloadDirectory() + "/" + download.downloadFileName()
        )
        dosya_yolu, _ = QFileDialog.getSaveFileName(
            self, "Dosyayı Kaydet", varsayilan_yol
        )

        if dosya_yolu:
            klasor = os.path.dirname(dosya_yolu)
            dosya_adi = os.path.basename(dosya_yolu)

            download.setDownloadDirectory(klasor)
            download.setDownloadFileName(dosya_adi)
            download.accept()

            download.receivedBytesChanged.connect(
                lambda: self.indirme_durumu_guncelle(download)
            )
            download.finished.connect(
                lambda: self.statusBar().showMessage(
                    "İndirme Tamamlandı!", 5000
                )
            )

    def indirme_durumu_guncelle(self, download):
        alinan = download.receivedBytes() / (1024 * 1024)
        toplam = download.totalBytes() / (1024 * 1024)
        if toplam > 0:
            yuzde = (download.receivedBytes() / download.totalBytes()) * 100
            self.statusBar().showMessage(
                f"İndiriliyor: %{yuzde:.1f} ({alinan:.1f} MB / {toplam:.1f} MB)"
            )
        else:
            self.statusBar().showMessage(f"İndiriliyor: {alinan:.1f} MB")

    def sekme_kapat(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)

    def sekme_degisti(self, i):
        mevcut_browser = self.tabs.currentWidget()
        if mevcut_browser:
            self.url_bar.setText(mevcut_browser.url().toString())

    def git_url(self):
        url = self.url_bar.text()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        self.tabs.currentWidget().setUrl(QUrl(url))

    def url_guncelle(self, q, browser):
        if browser == self.tabs.currentWidget():
            self.url_bar.setText(q.toString())

    def baslik_guncelle(self, title, browser):
        i = self.tabs.indexOf(browser)
        if i != -1:
            self.tabs.setTabText(
                i, title[:15] + "..." if len(title) > 15 else title
            )

    def mevcut_browser_geri(self):
        self.tabs.currentWidget().back()

    def mevcut_browser_ileri(self):
        self.tabs.currentWidget().forward()

    def mevcut_browser_yenile(self):
        self.tabs.currentWidget().reload()


app = QApplication(sys.argv)
window = Tarayici()
window.show()
sys.exit(app.exec())
