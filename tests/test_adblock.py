"""AdBlocker eşleşme testleri."""

from tbrowser_core import host_engellendi_mi, url_engellendi_mi


def test_host_birebir_ve_alt_domain():
    assert host_engellendi_mi("doubleclick.net") is True
    assert host_engellendi_mi("sub.doubleclick.net") is True
    assert host_engellendi_mi("DOUBLECLICK.NET") is True


def test_host_sahte_eslesme_yok():
    assert host_engellendi_mi("notdoubleclick.net") is False
    assert host_engellendi_mi("example.com") is False
    assert host_engellendi_mi("") is False
    assert host_engellendi_mi(None) is False


def test_url_kaliplari():
    assert url_engellendi_mi("https://example.com/pagead2.js") is True
    assert url_engellendi_mi("https://example.com/ads/banner") is True
    assert url_engellendi_mi("https://example.com/haberler/son-dakika") is False
    assert url_engellendi_mi("") is False
