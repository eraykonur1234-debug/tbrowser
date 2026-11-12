#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tbrowser v1.0.0 — hızlı, hafif ve gizlilik odaklı masaüstü web tarayıcısı.

Kullanım:
    python tbrowser.py

Derleme (PyInstaller):
    python build.py

Not: main4.py / main6.py / main7.py eski prototiplerdir; 1.0 sürümü
bu dosyada (tbrowser.py) ve tbrowser_core.py'de toplanmıştır.
"""

from __future__ import annotations

import os
import sys

try:
    from PyQt6.QtCore import QSettings, QUrl, Qt
    from PyQt6.QtGui import QKeySequence, QShortcut
    from PyQt6.QtWebEngineCore import (
        QWebEngineDownloadRequest,
        QWebEnginePage,
        QWebEngineProfile,
        QWebEngineScript,
        QWebEngineUrlRequestInfo,
        QWebEngineUrlRequestInterceptor,
    )
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QFileDialog,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - kurulum hatası mesajı
    print(
        "Hata: PyQt6 bulunamadı.\n"
        "Kurulum:  pip install -r requirements.txt\n"
        f"Detay: {exc}",
        file=sys.stderr,
    )
    sys.exit(1)

from tbrowser_core import (
    ANA_SAYFA_URL,
    KARAR_SOR,
    POLITIKA_ENGELLE,
    POLITIKA_IZIN_VER,
    POLITIKA_SOR,
    SURUM,
    UYGULAMA_ADI,
    CerezYoneticisi,
    adres_coz,
    host_engellendi_mi,
    url_engellendi_mi,
)

# ---------------------------------------------------------------------------
# AdBlocker (ağ seviyesi engelleme)
# ---------------------------------------------------------------------------


class AdBlocker(QWebEngineUrlRequestInterceptor):
    """Reklam/takipçi isteklerini ağ seviyesinde engeller.

    Kullanıcının bilerek gittiği ana sayfa (main frame) engellenmez;
    yalnızca alt kaynak istekleri (script, iframe, piksel vb.) kesilir.
    """

    def __init__(self):
        super().__init__()
        self.aktif = True
        self.engellenen_sayac = 0

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        if not self.aktif:
            return
        # Ana çerçeve: kullanıcı doğrudan bu adrese gittiyse engelleme.
        if info.resourceType() in (
            QWebEngineUrlRequestInfo.ResourceType.ResourceTypeMainFrame,
            QWebEngineUrlRequestInfo.ResourceType.ResourceTypeNavigationPreloadMainFrame,
        ):
            return

        url = info.requestUrl().toString()
        host = info.requestUrl().host()
        if host_engellendi_mi(host) or url_engellendi_mi(url):
            info.block(True)
            self.engellenen_sayac += 1


# ---------------------------------------------------------------------------
# Sekme görünümü (popup / target=_blank desteği)
# ---------------------------------------------------------------------------


class TarayiciView(QWebEngineView):
    """Yeni pencere isteklerini yeni sekme olarak açan görünüm."""

    def __init__(
        self,
        ana_pencere,
        profile: QWebEngineProfile | None = None,
        parent=None,
    ):
        if profile is not None:
            super().__init__(profile, parent)
        else:
            super().__init__(parent)
        self.ana_pencere = ana_pencere

    def createWindow(self, windowType):
        aktif = windowType != QWebEnginePage.WebWindowType.WebBrowserBackgroundTab
        yeni = TarayiciView(self.ana_pencere, self.ana_pencere.profile)
        self.ana_pencere.yeni_sekme_ekle(view=yeni, aktif=aktif)
        return yeni


# ---------------------------------------------------------------------------
# Ayarlar penceresi
# ---------------------------------------------------------------------------


class AyarlarPenceresi(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_win = parent
        self.setWindowTitle(f"{UYGULAMA_ADI} - Ayarlar")
        self.resize(420, 340)
        self.setStyleSheet(
            """
            QDialog { background-color: #1e1e2e; color: #cdd6f4; }
            QLabel { color: #cdd6f4; font-size: 13px; }
            QGroupBox { color: #89b4fa; font-weight: bold; border: 1px solid #45475a; border-radius: 6px; margin-top: 10px; padding-top: 10px; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px; }
            QPushButton:hover { background-color: #45475a; }
            QCheckBox { color: #cdd6f4; font-weight: bold; }
            QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 4px; }
            """
        )

        layout = QVBoxLayout()

        # Reklam engelleyici
        group_adblock = QGroupBox("Reklam Engelleyici")
        adblock_layout = QVBoxLayout()
        self.chk_adblock = QCheckBox("AdBlocker Etkinleştir")
        self.chk_adblock.blockSignals(True)
        self.chk_adblock.setChecked(self.main_win.adblocker.aktif)
        self.chk_adblock.blockSignals(False)
        # toggled(bool) kullan: stateChanged(int) PartiallyChecked durumunda
        # bool(state) True dönerdi (eski hata).
        self.chk_adblock.toggled.connect(self.main_win.toggle_adblock_from_settings)
        adblock_layout.addWidget(self.chk_adblock)
        group_adblock.setLayout(adblock_layout)

        # Çerez politikası
        group_cookie = QGroupBox("Çerezler")
        cookie_layout = QVBoxLayout()
        cookie_layout.addWidget(QLabel("Yeni sitelerin çerezlerinde varsayılan davranış:"))
        self.combo_cookie = QComboBox()
        self.combo_cookie.addItem("Her site için sor", POLITIKA_SOR)
        self.combo_cookie.addItem("Her zaman izin ver", POLITIKA_IZIN_VER)
        self.combo_cookie.addItem("Her zaman engelle", POLITIKA_ENGELLE)
        mevcut = self.main_win.cerez_yoneticisi.varsayilan_politika
        idx = self.combo_cookie.findData(mevcut)
        self.combo_cookie.blockSignals(True)
        self.combo_cookie.setCurrentIndex(idx if idx >= 0 else 0)
        self.combo_cookie.blockSignals(False)
        self.combo_cookie.currentIndexChanged.connect(self._cookie_politikasi_degisti)
        cookie_layout.addWidget(self.combo_cookie)
        cookie_layout.addWidget(
            QLabel("Site bazlı izin/engel kararlarınız hatırlanır.")
        )
        group_cookie.setLayout(cookie_layout)

        # Temizlik
        group_temizle = QGroupBox("Temizlik")
        temizle_layout = QVBoxLayout()
        btn_cerez_temizle = QPushButton("Tüm çerezleri ve site izinlerini sıfırla")
        btn_cerez_temizle.clicked.connect(self._cerezleri_temizle)
        btn_gecmis_temizle = QPushButton("Geçmişi ve ziyaret edilenleri temizle")
        btn_gecmis_temizle.clicked.connect(self._gecmisi_temizle)
        temizle_layout.addWidget(btn_cerez_temizle)
        temizle_layout.addWidget(btn_gecmis_temizle)
        group_temizle.setLayout(temizle_layout)

        layout.addWidget(group_adblock)
        layout.addWidget(group_cookie)
        layout.addWidget(group_temizle)
        layout.addWidget(QLabel(f"{UYGULAMA_ADI} v{SURUM}"))
        layout.addStretch()

        btn_kapat = QPushButton("Kapat")
        btn_kapat.clicked.connect(self.close)
        layout.addWidget(btn_kapat)

        self.setLayout(layout)

    def _cookie_politikasi_degisti(self, _index: int) -> None:
        politika = self.combo_cookie.currentData()
        self.main_win.cerez_politikasini_ayarla(politika)

    def _cerezleri_temizle(self) -> None:
        self.main_win.cookie_store.deleteAllCookies()
        self.main_win.cerez_yoneticisi.temizle()
        self.main_win.cerez_bar_guncelle()
        QMessageBox.information(
            self, "Başarılı", "Tüm çerezler ve site izinleri temizlendi!"
        )

    def _gecmisi_temizle(self) -> None:
        temizlendi = False
        # Ziyaret edilen bağlantılar (profil seviyesi)
        clear_links = getattr(self.main_win.profile, "clearAllVisitedLinks", None)
        if callable(clear_links):
            try:
                clear_links()
                temizlendi = True
            except Exception:
                pass
        # Açık sekmelerin geçmişi
        for i in range(self.main_win.tabs.count()):
            view = self.main_win.tabs.widget(i)
            if view is not None:
                try:
                    view.history().clear()
                    temizlendi = True
                except Exception:
                    pass
        QMessageBox.information(
            self,
            "Başarılı",
            "Geçmiş temizlendi!" if temizlendi else "Temizlenecek geçmiş bulunamadı.",
        )


# ---------------------------------------------------------------------------
# Ana pencere
# ---------------------------------------------------------------------------


class Tarayici(QMainWindow):
    def __init__(self, ayarlar=None, ilk_url: QUrl | None = None):
        super().__init__()
        self.setWindowTitle(f"{UYGULAMA_ADI} v{SURUM}")
        self.resize(1200, 800)

        # Kalıcı ayarlar (çerez kararları, pencere konumu, adblock durumu)
        self.ayarlar = ayarlar if ayarlar is not None else QSettings(UYGULAMA_ADI, UYGULAMA_ADI)

        self.setStyleSheet(
            """
            QMainWindow { background-color: #1e1e2e; }
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                background: #2b2b3b; color: #a6adc8; padding: 8px 15px;
                border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px;
            }
            QTabBar::tab:selected { background: #11111b; color: #cdd6f4; font-weight: bold; }
            QLineEdit {
                background-color: #313244; color: #cdd6f4; border: 1px solid #45475a;
                border-radius: 12px; padding: 6px 12px; font-size: 13px;
            }
            QPushButton {
                background-color: #313244; color: #cdd6f4; border: 1px solid #45475a;
                border-radius: 6px; padding: 6px 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #45475a; }
            QStatusBar { background-color: #11111b; color: #a6adc8; }
            QProgressBar { background-color: #11111b; border: none; height: 3px; text-align: center; }
            QProgressBar::chunk { background-color: #89b4fa; width: 10px; }
            """
        )

        # Profil + AdBlocker
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )
        self.adblocker = AdBlocker()
        try:
            self.adblocker.aktif = bool(
                self.ayarlar.value("adblock/enabled", True, type=bool)
            )
        except Exception:
            self.adblocker.aktif = bool(self.ayarlar.value("adblock/enabled", True))
        self.profile.setUrlRequestInterceptor(self.adblocker)
        self._adblock_script = None
        self._adblock_script_uygula()

        # İndirme + çerez yöneticileri
        self.profile.downloadRequested.connect(self.indirme_isleyicisi)
        self.cookie_store = self.profile.cookieStore()
        self.cerez_yoneticisi = CerezYoneticisi(self.ayarlar)
        self._cerez_filtresi_cb = self._cerez_filtresi
        self.cookie_store.setCookieFilter(self._cerez_filtresi_cb)
        self.cookie_store.cookieAdded.connect(self.cerez_eklendi_kontrol)

        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.sekme_kapat)
        self.tabs.currentChanged.connect(self.sekme_degisti)

        # Üst bar butonları
        self.btn_geri = QPushButton("◄")
        self.btn_ileri = QPushButton("►")
        self.btn_yenile = QPushButton("↻")
        self.btn_ana_sayfa = QPushButton("⌂")
        self.btn_yeni_sekme = QPushButton("+")
        self.btn_ayarlar = QPushButton("⚙️")

        self.btn_adblock = QPushButton()
        self.adblock_buton_guncelle()
        self.btn_adblock.clicked.connect(self.toggle_adblock_button)
        self.btn_ayarlar.clicked.connect(self.ayarlari_ac)

        self.btn_geri.clicked.connect(self.mevcut_browser_geri)
        self.btn_ileri.clicked.connect(self.mevcut_browser_ileri)
        self.btn_yenile.clicked.connect(self.yenile_veya_durdur)
        self.btn_ana_sayfa.clicked.connect(self.ana_sayfaya_git)
        self.btn_yeni_sekme.clicked.connect(lambda: self.yeni_sekme_ekle())

        # Adres çubuğu
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Adres veya arama yazın…")
        self.url_bar.returnPressed.connect(self.git_url)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.btn_geri)
        top_bar.addWidget(self.btn_ileri)
        top_bar.addWidget(self.btn_yenile)
        top_bar.addWidget(self.btn_ana_sayfa)
        top_bar.addWidget(self.url_bar)
        top_bar.addWidget(self.btn_adblock)
        top_bar.addWidget(self.btn_ayarlar)
        top_bar.addWidget(self.btn_yeni_sekme)

        # Yükleme çubuğu
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.hide()

        # Çerez izin çubuğu
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

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)
        main_layout.addWidget(self.progress)
        main_layout.addWidget(self.cerez_bar)
        main_layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.statusBar().showMessage(f"{UYGULAMA_ADI} v{SURUM} güvenli modda hazır")

        # Klavye kısayolları
        self._kisayol("Ctrl+T", lambda: self.yeni_sekme_ekle())
        self._kisayol("Ctrl+W", self._aktif_sekmeyi_kapat)
        self._kisayol("Ctrl+L", self._adres_cubuguna_odaklan)
        self._kisayol("Ctrl+R", self.mevcut_browser_yenile)
        self._kisayol("Escape", self.mevcut_browser_durdur)

        # Pencere konumunu geri yükle
        try:
            geo = self.ayarlar.value("window/geometry")
            if geo is not None:
                self.restoreGeometry(geo)
        except Exception:
            pass

        # İlk sekme
        baslangic = ilk_url if ilk_url is not None else QUrl(ANA_SAYFA_URL)
        baslik = "tbrowser" if ilk_url is not None else "Brave Search"
        self.yeni_sekme_ekle(baslangic, baslik)

    # -- AdBlocker -----------------------------------------------------------

    def _adblock_script_uygula(self) -> None:
        """Kozmetik filtreleme scriptini aktif duruma göre ekler/kaldırır."""
        scripts = self.profile.scripts()
        if self.adblocker.aktif:
            if self._adblock_script is None:
                script = QWebEngineScript()
                script.setSourceCode(
                    """
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
                )
                script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
                script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
                script.setRunsOnSubFrames(True)
                self._adblock_script = script
                scripts.insert(script)
        else:
            if self._adblock_script is not None:
                try:
                    scripts.remove(self._adblock_script)
                except Exception:
                    pass
                self._adblock_script = None

    def toggle_adblock_button(self) -> None:
        self.adblocker.aktif = not self.adblocker.aktif
        self._adblock_durumunu_kaydet()
        self._adblock_script_uygula()
        self.adblock_buton_guncelle()
        view = self._aktif_view()
        if view is not None:
            view.reload()

    def toggle_adblock_from_settings(self, checked: bool) -> None:
        self.adblocker.aktif = bool(checked)
        self._adblock_durumunu_kaydet()
        self._adblock_script_uygula()
        self.adblock_buton_guncelle()
        view = self._aktif_view()
        if view is not None:
            view.reload()

    def _adblock_durumunu_kaydet(self) -> None:
        try:
            self.ayarlar.setValue("adblock/enabled", self.adblocker.aktif)
        except Exception:
            pass

    def adblock_buton_guncelle(self) -> None:
        if self.adblocker.aktif:
            self.btn_adblock.setText(
                f"🛡️ AdBlocker Açık ({self.adblocker.engellenen_sayac})"
            )
            self.btn_adblock.setStyleSheet(
                "color: #a6e3a1; font-weight: bold; border: 1px solid #a6e3a1;"
            )
        else:
            self.btn_adblock.setText("🛡️ AdBlocker Kapalı")
            self.btn_adblock.setStyleSheet(
                "color: #f38ba8; font-weight: bold; border: 1px solid #f38ba8;"
            )

    def ayarlari_ac(self) -> None:
        AyarlarPenceresi(self).exec()

    # -- Sekmeler --------------------------------------------------------------

    def _kisayol(self, tus: str, slot) -> QShortcut:
        sc = QShortcut(QKeySequence(tus), self)
        sc.activated.connect(slot)
        return sc

    def yeni_sekme_ekle(
        self,
        qurl: QUrl | None = None,
        label: str = "Yeni Sekme",
        view: TarayiciView | None = None,
        aktif: bool = True,
    ) -> None:
        if view is None:
            view = TarayiciView(self, self.profile)
            view.setUrl(qurl if qurl is not None else QUrl(ANA_SAYFA_URL))
        elif qurl is not None:
            view.setUrl(qurl)

        i = self.tabs.addTab(view, label)
        if aktif:
            self.tabs.setCurrentIndex(i)

        view.urlChanged.connect(
            lambda qurl, browser=view: self.url_guncelle(qurl, browser)
        )
        view.titleChanged.connect(
            lambda title, browser=view: self.baslik_guncelle(title, browser)
        )
        view.loadProgress.connect(
            lambda p, browser=view: self.yukleme_guncelle(p, browser)
        )
        view.loadStarted.connect(lambda browser=view: self.yukleme_basladi(browser))
        view.loadFinished.connect(lambda _ok, browser=view: self.yukleme_bitti(browser))

    def sekme_kapat(self, i: int) -> None:
        view = self.tabs.widget(i)
        self.tabs.removeTab(i)
        if view is not None:
            try:
                view.stop()
            except Exception:
                pass
            view.deleteLater()
        if self.tabs.count() == 0:
            self.yeni_sekme_ekle(QUrl(ANA_SAYFA_URL), "Brave Search")

    def _aktif_sekmeyi_kapat(self) -> None:
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self.sekme_kapat(idx)

    def sekme_degisti(self, _i: int) -> None:
        view = self._aktif_view()
        if view is not None:
            self.url_bar.setText(view.url().toString())

    def _aktif_view(self) -> QWebEngineView | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    # -- Gezinti -----------------------------------------------------------------

    def git_url(self) -> None:
        view = self._aktif_view()
        if view is None:
            return
        view.setUrl(adres_coz(self.url_bar.text()))

    def ana_sayfaya_git(self) -> None:
        view = self._aktif_view()
        if view is not None:
            view.setUrl(QUrl(ANA_SAYFA_URL))

    def url_guncelle(self, q: QUrl, browser: QWebEngineView) -> None:
        if browser == self.tabs.currentWidget():
            self.url_bar.setText(q.toString())

    def baslik_guncelle(self, title: str, browser: QWebEngineView) -> None:
        i = self.tabs.indexOf(browser)
        if i != -1:
            kisa = title[:15] + "..." if len(title) > 15 else (title or "Yeni Sekme")
            self.tabs.setTabText(i, kisa)

    def mevcut_browser_geri(self) -> None:
        view = self._aktif_view()
        if view is not None:
            view.back()

    def mevcut_browser_ileri(self) -> None:
        view = self._aktif_view()
        if view is not None:
            view.forward()

    def mevcut_browser_yenile(self) -> None:
        view = self._aktif_view()
        if view is not None:
            view.reload()

    def mevcut_browser_durdur(self) -> None:
        view = self._aktif_view()
        if view is not None:
            view.stop()

    def yenile_veya_durdur(self) -> None:
        view = self._aktif_view()
        if view is None:
            return
        # Yükleme sürüyorsa durdur, değilse yenile
        if self.progress.isVisible():
            view.stop()
        else:
            view.reload()

    def _adres_cubuguna_odaklan(self) -> None:
        self.url_bar.setFocus()
        self.url_bar.selectAll()

    # -- Yükleme göstergesi -------------------------------------------------------

    def yukleme_basladi(self, browser: QWebEngineView) -> None:
        if browser == self.tabs.currentWidget():
            self.progress.setValue(0)
            self.progress.show()
            self.btn_yenile.setText("✕")

    def yukleme_guncelle(self, p: int, browser: QWebEngineView) -> None:
        if browser == self.tabs.currentWidget():
            self.progress.setValue(p)

    def yukleme_bitti(self, browser: QWebEngineView) -> None:
        if browser == self.tabs.currentWidget():
            self.progress.setValue(100)
            self.progress.hide()
            self.btn_yenile.setText("↻")
            self.adblock_buton_guncelle()

    # -- Çerezler (1.0 düzeltmesi) --------------------------------------------------

    def _cerez_filtresi(self, req) -> bool:
        try:
            host = req.origin.host()
            if self.adblocker.aktif and req.thirdParty and host_engellendi_mi(host):
                return False
            return self.cerez_yoneticisi.cerez_filtre_izni(host)
        except Exception:
            return True

    def cerez_eklendi_kontrol(self, cookie) -> None:
        karar = self.cerez_yoneticisi.cerez_eklendi(cookie, self.cookie_store)
        if karar == KARAR_SOR:
            self.cerez_bar_guncelle()

    def cerez_bar_guncelle(self) -> None:
        domain = self.cerez_yoneticisi.sıradaki()
        if domain is None:
            self.cerez_bar.hide()
            return
        sayi = self.cerez_yoneticisi.bekleyen_sayisi(domain)
        self.cerez_label.setText(
            f"'{domain}' sitesine ait {sayi} çerez kaydedilsin mi? "
            "(Kararınız hatırlanacak)"
        )
        self.cerez_bar.show()

    def cerez_izin_ver(self) -> None:
        domain = self.cerez_yoneticisi.su_anki_domain
        self.cerez_yoneticisi.izin_ver()
        if domain:
            self.statusBar().showMessage(
                f"{domain} için çerezlere izin verildi.", 4000
            )
        self.cerez_bar_guncelle()

    def cerez_reddet(self) -> None:
        domain = self.cerez_yoneticisi.su_anki_domain
        self.cerez_yoneticisi.reddet(self.cookie_store)
        if domain:
            self.statusBar().showMessage(
                f"{domain} çerezleri engellendi ve silindi.", 4000
            )
        self.cerez_bar_guncelle()

    def cerez_politikasini_ayarla(self, politika: str) -> None:
        self.cerez_yoneticisi.politika_ayarla(politika)
        if politika == POLITIKA_ENGELLE:
            # Otomatik engel: bekleyen çerezleri sil
            self.cerez_yoneticisi.bekleyenleri_temizle(self.cookie_store)
        elif politika == POLITIKA_IZIN_VER:
            # Otomatik izin: bekleyen çerezler kalır, sorular boşaltılır
            self.cerez_yoneticisi.kuyrugu_bosalt()
        self.cerez_bar_guncelle()

    # -- İndirmeler -------------------------------------------------------------------

    def indirme_isleyicisi(self, download) -> None:
        indirilenler = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(indirilenler, exist_ok=True)
        dosya_adi = download.downloadFileName() or "indirilen-dosya"
        varsayilan_yol = os.path.join(indirilenler, dosya_adi)

        dosya_yolu, _ = QFileDialog.getSaveFileName(
            self, "Dosyayı Kaydet", varsayilan_yol
        )
        if not dosya_yolu:
            download.cancel()
            return

        download.setDownloadDirectory(os.path.dirname(dosya_yolu))
        download.setDownloadFileName(os.path.basename(dosya_yolu))
        # download parametresi varsayılan argümanla yakalanır (geç bağlama hatası yok)
        download.receivedBytesChanged.connect(
            lambda download=download: self.indirme_durumu_guncelle(download)
        )
        download.isFinishedChanged.connect(
            lambda download=download: self.indirme_bitti(download)
        )
        download.accept()

    def indirme_durumu_guncelle(self, download) -> None:
        alinan = download.receivedBytes() / (1024 * 1024)
        toplam = download.totalBytes() / (1024 * 1024)
        if toplam > 0:
            yuzde = (download.receivedBytes() / download.totalBytes()) * 100
            self.statusBar().showMessage(
                f"İndiriliyor: %{yuzde:.1f} ({alinan:.1f} MB / {toplam:.1f} MB)"
            )
        else:
            self.statusBar().showMessage(f"İndiriliyor: {alinan:.1f} MB")

    def indirme_bitti(self, download) -> None:
        try:
            durum = download.state()
            if durum == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                self.statusBar().showMessage("İndirme tamamlandı!", 5000)
                return
            if durum == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
                sebep = download.interruptReasonString() or "Bilinmeyen hata"
                self.statusBar().showMessage(f"İndirme başarısız: {sebep}", 6000)
                return
        except Exception:
            pass
        try:
            if download.isFinished():
                self.statusBar().showMessage("İndirme tamamlandı!", 5000)
        except Exception:
            pass

    # -- Kapanış ------------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt isimlendirmesi)
        try:
            self.ayarlar.setValue("window/geometry", self.saveGeometry())
        except Exception:
            pass
        try:
            self.profile.setUrlRequestInterceptor(None)
        except Exception:
            pass
        try:
            self.cookie_store.setCookieFilter()
        except Exception:
            pass
        try:
            self.cookie_store.cookieAdded.disconnect(self.cerez_eklendi_kontrol)
        except Exception:
            pass
        super().closeEvent(event)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            try:
                reconf(encoding="utf-8", errors="replace")
            except Exception:
                pass

    args = sys.argv[1:] if argv is None else argv
    if "--version" in args:
        print(f"{UYGULAMA_ADI} {SURUM}")
        return 0

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setApplicationName(UYGULAMA_ADI)
    app.setOrganizationName(UYGULAMA_ADI)
    app.setApplicationVersion(SURUM)
    app.setDesktopFileName(UYGULAMA_ADI)

    if "--smoke-test" in args:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            ayar = QSettings(os.path.join(tmp, "smoke.ini"), QSettings.Format.IniFormat)
            window = Tarayici(ayarlar=ayar, ilk_url=QUrl("about:blank"))
            window.show()
            app.processEvents()
            window.close()
        return 0

    window = Tarayici()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
