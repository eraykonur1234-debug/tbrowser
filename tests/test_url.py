"""Adres çözümleme testleri."""

from tbrowser_core import adres_coz


def test_bos_ana_sayfa():
    assert adres_coz("").host() == "search.brave.com"
    assert adres_coz(None).host() == "search.brave.com"


def test_arama_sorgusu():
    url = adres_coz("kedi videoları")
    assert url.host() == "search.brave.com"
    assert "kedi" in url.toString()


def test_noktasiz_tek_kelime_arama():
    assert adres_coz("kedi").host() == "search.brave.com"


def test_semasiz_domain():
    url = adres_coz("example.com/yol")
    assert url.scheme() == "https"
    assert url.host() == "example.com"


def test_tam_url_korunur():
    url = adres_coz("https://example.com/sayfa?x=1")
    assert url.host() == "example.com"
    assert url.query() == "x=1"
