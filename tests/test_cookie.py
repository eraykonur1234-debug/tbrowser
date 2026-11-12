"""Çerez yöneticisi testleri (1.0 çerez hatası düzeltmesi)."""

import pytest

from tbrowser_core import (
    KARAR_ENGELLE,
    KARAR_IZIN,
    KARAR_SOR,
    POLITIKA_ENGELLE,
    POLITIKA_IZIN_VER,
    CerezYoneticisi,
    domain_karari,
    domain_normalize,
)


class SahteCookie:
    def __init__(self, domain):
        self._domain = domain

    def domain(self):
        return self._domain


class SahteStore:
    def __init__(self):
        self.silinenler = []

    def deleteCookie(self, cookie):
        self.silinenler.append(cookie)

    def deleteAllCookies(self):
        pass


class SahteAyarlar:
    def __init__(self):
        self.veriler = {}

    def value(self, key, default=None, type=None):
        return self.veriler.get(key, default)

    def setValue(self, key, value):
        self.veriler[key] = value


# --- normalize ------------------------------------------------------------


def test_normalize():
    assert domain_normalize(".Example.COM") == "example.com"
    assert domain_normalize("  example.com. ") == "example.com"
    assert domain_normalize("") == ""
    assert domain_normalize(None) == ""


# --- karar ------------------------------------------------------------------


def test_karar_bos_domain_sessiz_izin():
    # Host-only çerezler sonsuz soru döngüsüne girmemeli
    assert domain_karari("", set(), set()) == KARAR_IZIN
    assert domain_karari(None, set(), set()) == KARAR_IZIN


def test_karar_bilinmeyen_sor():
    assert domain_karari("example.com", set(), set()) == KARAR_SOR


def test_karar_izin_ve_alt_domain():
    assert domain_karari("example.com", {"example.com"}, set()) == KARAR_IZIN
    assert domain_karari("sub.example.com", {"example.com"}, set()) == KARAR_IZIN
    assert domain_karari("EXAMPLE.com", {"example.com"}, set()) == KARAR_IZIN


def test_karar_engelle_ve_alt_domain():
    assert domain_karari("sub.example.com", set(), {"example.com"}) == KARAR_ENGELLE


def test_karar_sahte_eslesme_yok():
    # "fakeexample.com" -> "example.com" ile eşleşmemeli (nokta sınırı)
    assert domain_karari("fakeexample.com", {"example.com"}, set()) == KARAR_SOR


def test_karar_en_ozel_eslesme_kazanir():
    # İzin genel, engel özel -> engel kazanır
    assert (
        domain_karari("sub.example.com", {"example.com"}, {"sub.example.com"})
        == KARAR_ENGELLE
    )
    # Engel genel, izin özel -> izin kazanır
    assert (
        domain_karari("sub.example.com", {"sub.example.com"}, {"example.com"})
        == KARAR_IZIN
    )


# --- yönetici akışı ----------------------------------------------------------


def test_bos_domain_cerezi_sessiz_izin():
    y = CerezYoneticisi()
    store = SahteStore()
    assert y.cerez_eklendi(SahteCookie(""), store) == KARAR_IZIN
    assert y.bekleyen_sayisi() == 0


def test_kuyruk_fifo_ve_tek_soru():
    y = CerezYoneticisi()
    store = SahteStore()
    # İki farklı domain hızla çerez gönderir
    assert y.cerez_eklendi(SahteCookie("a.com"), store) == KARAR_SOR
    assert y.cerez_eklendi(SahteCookie("b.com"), store) == KARAR_SOR
    # Aynı domainin ikinci çerezi kuyruğu büyütmez, yalnızca birikir
    assert y.cerez_eklendi(SahteCookie("a.com"), store) == KARAR_SOR
    assert y.bekleyen_sayisi("a.com") == 2
    assert y.bekleyen_domain_sayisi() == 2

    # Sıradaki: önce a.com
    assert y.sıradaki() == "a.com"
    # a.com aktifken yeni çerez kuyruğu değiştirmez
    y.cerez_eklendi(SahteCookie("a.com"), store)
    assert y.su_anki_domain == "a.com"

    # İzin ver -> sıradaki b.com olur (eski hatada b.com kayboluyordu)
    assert y.izin_ver() == "b.com"
    assert "a.com" in y.izin_verilen
    # a.com artık sessiz izin
    assert y.cerez_eklendi(SahteCookie("a.com"), store) == KARAR_IZIN

    # b.com'u reddet -> çerezler silinir, kuyruk biter
    assert y.reddet(store) is None
    assert "b.com" in y.engellenen
    assert len(store.silinenler) == 1
    # b.com artık otomatik engel
    assert y.cerez_eklendi(SahteCookie("b.com"), store) == KARAR_ENGELLE


def test_kalici_karar_yeniden_yuklenir():
    ayarlar = SahteAyarlar()
    y1 = CerezYoneticisi(ayarlar)
    store = SahteStore()
    y1.cerez_eklendi(SahteCookie("ornek.com"), store)
    y1.sıradaki()
    y1.izin_ver()

    y2 = CerezYoneticisi(ayarlar)
    assert y2.karar("ornek.com") == KARAR_IZIN
    assert y2.cerez_eklendi(SahteCookie("ornek.com"), store) == KARAR_IZIN


def test_politika_izin_ver_ve_engelle():
    y = CerezYoneticisi()
    store = SahteStore()
    y.politika_ayarla(POLITIKA_IZIN_VER)
    assert y.cerez_eklendi(SahteCookie("x.com"), store) == KARAR_IZIN
    y.politika_ayarla(POLITIKA_ENGELLE)
    assert y.cerez_eklendi(SahteCookie("x.com"), store) == KARAR_ENGELLE
    with pytest.raises(ValueError):
        y.politika_ayarla("gecersiz")


def test_temizle():
    ayarlar = SahteAyarlar()
    y = CerezYoneticisi(ayarlar)
    store = SahteStore()
    y.cerez_eklendi(SahteCookie("a.com"), store)
    y.sıradaki()
    y.izin_ver()
    y.temizle()
    assert y.izin_verilen == set()
    assert y.karar("a.com") == KARAR_SOR


def test_qsettings_tek_string_ve_json_yukleme():
    # QSettings INI/Registry tek elemanlı listeyi string olarak dönebilir
    ayarlar = SahteAyarlar()
    ayarlar.veriler["cookies/allowed"] = "tek-site.com"
    ayarlar.veriler["cookies/blocked"] = '["yasak.com"]'
    y = CerezYoneticisi(ayarlar)
    assert y.karar("tek-site.com") == KARAR_IZIN
    assert y.karar("yasak.com") == KARAR_ENGELLE


def test_cerez_filtre_izni():
    y = CerezYoneticisi()
    store = SahteStore()
    # Bilinmeyen site -> filtre izin verir (sonra cookieAdded ile sorulur)
    assert y.cerez_filtre_izni("yeni.com") is True

    y.cerez_eklendi(SahteCookie("yasak.com"), store)
    y.sıradaki()
    y.reddet(store)
    assert y.cerez_filtre_izni("yasak.com") is False
    assert y.cerez_filtre_izni("sub.yasak.com") is False

    y.politika_ayarla(POLITIKA_IZIN_VER)
    assert y.cerez_filtre_izni("yasak.com") is True
    y.politika_ayarla(POLITIKA_ENGELLE)
    assert y.cerez_filtre_izni("herhangi.com") is False


def test_kuyrugu_bosalt_silmez():
    y = CerezYoneticisi()
    store = SahteStore()
    y.cerez_eklendi(SahteCookie("a.com"), store)
    assert y.sıradaki() == "a.com"
    y.kuyrugu_bosalt()
    assert store.silinenler == []
    assert y.bekleyen_sayisi() == 0
    assert y.su_anki_domain is None

