"""GUI ve PyQt6 entegrasyon duman testleri.

Qt sistem kütüphanelerinin bulunmadığı minimalist konteynerlerde yalnızca
shared library eksikliği durumunda atlanır; CI'da (CI=true) mutlaka koşar.
"""

import os

import pytest


def _gui_yukle():
    try:
        from PyQt6.QtWidgets import QApplication  # noqa: F401
        import tbrowser

        return tbrowser
    except ImportError as exc:
        if os.environ.get("CI"):
            raise
        if "cannot open shared object file" in str(exc):
            pytest.skip(f"Sistem Qt kütüphaneleri yok: {exc}")
        raise


def test_gui_pencere_ve_cerez_akisi(tmp_path):
    tbrowser = _gui_yukle()
    from PyQt6.QtCore import QSettings, QUrl
    from PyQt6.QtNetwork import QNetworkCookie
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    ayar_dosyasi = str(tmp_path / "ayarlar.ini")
    ayarlar = QSettings(ayar_dosyasi, QSettings.Format.IniFormat)

    win = tbrowser.Tarayici(ayarlar=ayarlar, ilk_url=QUrl("about:blank"))
    try:
        assert win.tabs.count() == 1

        # Yeni sekme ve kapatma
        win.yeni_sekme_ekle(QUrl("about:blank"), "Test")
        assert win.tabs.count() == 2
        win.sekme_kapat(1)
        assert win.tabs.count() == 1

        # Son sekme kapatıldığında yeni boş sekme açılmalı
        win.sekme_kapat(0)
        assert win.tabs.count() == 1

        # Çerez kuyruğu akışı (gerçek QNetworkCookie ile)
        c1 = QNetworkCookie(b"a", b"1")
        c1.setDomain(".site1.example")
        c2 = QNetworkCookie(b"b", b"2")
        c2.setDomain(".site2.example")

        win.cerez_eklendi_kontrol(c1)
        win.cerez_eklendi_kontrol(c2)
        assert win.cerez_bar.isHidden() is False
        assert "site1.example" in win.cerez_label.text()

        win.cerez_izin_ver()
        assert win.cerez_bar.isHidden() is False
        assert "site2.example" in win.cerez_label.text()

        win.cerez_reddet()
        assert win.cerez_bar.isHidden() is True
        assert "site1.example" in win.cerez_yoneticisi.izin_verilen
        assert "site2.example" in win.cerez_yoneticisi.engellenen

        # AdBlocker aç/kapat
        onceki = win.adblocker.aktif
        win.toggle_adblock_button()
        assert win.adblocker.aktif is (not onceki)

        # Ayarlar penceresi oluşturulabilmeli
        dlg = tbrowser.AyarlarPenceresi(win)
        assert dlg.chk_adblock.isChecked() is win.adblocker.aktif
        dlg.close()

        app.processEvents()
    finally:
        win.close()
        app.processEvents()
