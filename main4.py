import sys
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
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
)


# --- DAHİLİ ADBLOCKER MEKANİZMASI ---
class AdBlocker(QWebEngineUrlRequestInterceptor):

    def __init__(self):
        super().__init__()
        # Popüler reklam, takipçi ve analitik sunucularının filtre listesi
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
            "adroll.com",
            "scorecardresearch.com",
            "analytics.google.com",
            "hotjar.com",
        }
        self.engellenen_sayaci = 0

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        host = info.requestUrl().host()

        # Reklam domaini kontrolü
        for domain in self.reklam_domainleri:
            if domain in host or domain in url:
                info.block(True)  # İsteği ağ seviyesinde kes
                self.engellenen_sayaci += 1
                break


class Tarayici(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TBrowser")
        self.resize(1200, 800)

        # Çerez izin listeleri
        self.izin_verilen_domainler = set()
        self.engellenen_domainler = set()
        self.bekleyen_cerezler = []

        # Koyu Tema (Dark Mode) Stili
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

        # Genel Profil ve AdBlocker Aktifleştirme
        self.profile = QWebEngineProfile.defaultProfile()
        self.adblocker = AdBlocker()
        self.profile.setUrlRequestInterceptor(self.adblocker)

        # İndirme Yöneticisi ve Çerezler
        self.profile.downloadRequested.connect(self.indirme_isleyicisi)
        self.cookie_store = self.profile.cookieStore()
        self.cookie_store.cookieAdded.connect(self.cerez_eklendi_kontrol)

        # Sekme Yöneticisi
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.sekme_kapat)
        self.tabs.currentChanged.connect(self.sekme_degisti)

        # Navigasyon ve AdBlock Butonları
        btn_geri = QPushButton("◄")
        btn_ileri = QPushButton("►")
        btn_yenile = QPushButton("↻")
        btn_yeni_sekme = QPushButton("+")

        # Brave Kalkanı Mantığında AdBlocker Göstergesi
        self.btn_adblock = QPushButton(
            f"🛡️ Engellenen: {self.adblocker.engellenen_sayaci}"
        )
        self.btn_adblock.setStyleSheet(
            "color: #f38ba8; font-weight: bold; border: 1px solid #f38ba8;"
        )

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
        top_bar.addWidget(btn_yeni_sekme)

        # Çerez İzin Onay Barı
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

        self.statusBar().showMessage("Tpro Browser Güvenli Modda Hazır")

        # İlk Sekme
        self.yeni_sekme_ekle(
            QUrl("https://search.brave.com/"), "brave search"
        )

    def yeni_sekme_ekle(
        self, qurl=QUrl("https://search.brave.com/"), label="brave search"
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
        # Her sayfa yüklendiğinde engellenen reklam sayısını güncelle
        browser.loadFinished.connect(self.adblock_sayac_guncelle)

    def adblock_sayac_guncelle(self):
        self.btn_adblock.setText(
            f"🛡️ Engellenen: {self.adblocker.engellenen_sayaci}"
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
                f"{self.su_anki_domain} çerezleri engellendi ve silindi.",
                4000,
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
            import os

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
