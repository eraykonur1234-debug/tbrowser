#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tbrowser çekirdek mantığı (GUI bağımlı olmayan kısım).

Bu modül yalnızca QtCore/QtNetwork kullanır; pencere, sekme ve
QWebEngineView gibi GUI bileşenleri içermez. Böylece çerez kararı,
reklam engelleme eşleşmesi ve adres çözümleme mantığı birim
testleriyle (ekran olmadan) doğrulanabilir.

Sürüm: 1.0.0
"""

from __future__ import annotations

import re
from collections import deque
from typing import Iterable, Optional
from urllib.parse import quote_plus

from PyQt6.QtCore import QUrl

# ---------------------------------------------------------------------------
# Sürüm ve sabitler
# ---------------------------------------------------------------------------

SURUM = "1.0.0"
UYGULAMA_ADI = "tbrowser"
ARAMA_URL = "https://search.brave.com/search?q="
ANA_SAYFA_URL = "https://search.brave.com/"

# Çerez politikaları
POLITIKA_SOR = "sor"
POLITIKA_IZIN_VER = "izin_ver"
POLITIKA_ENGELLE = "engelle"
GECERLI_POLITIKALAR = (POLITIKA_SOR, POLITIKA_IZIN_VER, POLITIKA_ENGELLE)

# Çerez kararları
KARAR_IZIN = "izin"
KARAR_ENGELLE = "engelle"
KARAR_SOR = "sor"


# ---------------------------------------------------------------------------
# Domain yardımcıları
# ---------------------------------------------------------------------------


def domain_normalize(domain: str | None) -> str:
    """Domain'i karşılaştırma için normalize eder.

    - baş/son boşlukları atar
    - küçük harfe çevirir (domain'ler büyük/küçük harf duyarsızdır)
    - baştaki nokta(lar)ı ve sondaki noktayı atar (".example.com" -> "example.com")

    Boş/None girdi için "" döner.
    """
    if not domain:
        return ""
    d = str(domain).strip().lower()
    d = d.lstrip(".")
    d = d.rstrip(".")
    return d


def _eslesiyor(domain: str, aday: str) -> bool:
    """domain, aday ile birebir ya da alt-domain olarak eşleşiyor mu?

    "sub.example.com" -> "example.com" ile eşleşir,
    "example.com" -> "sub.example.com" ile eşleşmez,
    "fakeexample.com" -> "example.com" ile eşleşmez (nokta sınırı şart).
    """
    return domain == aday or domain.endswith("." + aday)


def domain_karari(
    domain: str | None,
    izin_verilen: Iterable[str],
    engellenen: Iterable[str],
) -> str:
    """Bir domain için çerez kararını döner: "izin" | "engelle" | "sor".

    Kurallar:
    - Boş domain (host-only çerez) sessizce "izin" döner; aksi halde
      her host-only çerezde soru sorulur ve kullanıcı sonsuz bir
      soru döngüsüne girer (1.0 öncesi çerez hatasının bir parçası).
    - Hem izin hem engel listesinde eşleşme varsa en uzun (en özel)
      eşleşme kazanır; eşitlikte engel kazanır (gizlilik öncelikli).
    - Hiçbir listede eşleşme yoksa "sor" döner.
    """
    d = domain_normalize(domain)
    if not d:
        return KARAR_IZIN

    izin_eslesme: Optional[str] = None
    for aday in izin_verilen:
        a = domain_normalize(aday)
        if a and _eslesiyor(d, a):
            if izin_eslesme is None or len(a) > len(izin_eslesme):
                izin_eslesme = a

    engel_eslesme: Optional[str] = None
    for aday in engellenen:
        a = domain_normalize(aday)
        if a and _eslesiyor(d, a):
            if engel_eslesme is None or len(a) > len(engel_eslesme):
                engel_eslesme = a

    if izin_eslesme is not None and engel_eslesme is not None:
        return KARAR_ENGELLE if len(engel_eslesme) >= len(izin_eslesme) else KARAR_IZIN
    if engel_eslesme is not None:
        return KARAR_ENGELLE
    if izin_eslesme is not None:
        return KARAR_IZIN
    return KARAR_SOR


# ---------------------------------------------------------------------------
# Adres çözümleme
# ---------------------------------------------------------------------------


def adres_coz(metin: str | None) -> QUrl:
    """Adres çubuğundaki metni gezinecek QUrl'e çevirir.

    - Boş metin -> ana sayfa
    - Boşluk içeren metin -> Brave araması (örn. "kedi videoları")
    - Şemasız ve noktasız ilk bileşen (örn. "kedi") -> Brave araması
    - Şemasız domain (örn. "example.com/x") -> https:// eklenir
    - Geçersiz URL -> Brave araması
    """
    s = (metin or "").strip()
    if not s:
        return QUrl(ANA_SAYFA_URL)

    if " " in s:
        return QUrl(ARAMA_URL + quote_plus(s))

    alt = s.lower()
    if alt.startswith(("http://", "https://", "about:", "data:", "file://", "view-source:")):
        url = QUrl(s)
        if url.isValid():
            return url
        return QUrl(ARAMA_URL + quote_plus(s))

    ilk_bilesen = s.split("/")[0].split("?")[0].split("#")[0]
    if "." not in ilk_bilesen:
        return QUrl(ARAMA_URL + quote_plus(s))

    url = QUrl("https://" + s)
    if not url.isValid() or not url.host():
        return QUrl(ARAMA_URL + quote_plus(s))
    return url


# ---------------------------------------------------------------------------
# Reklam / takipçi engelleme (saf eşleşme yardımcıları)
# ---------------------------------------------------------------------------

# Not: eski listelerdeki "yandex.ru/metrika" ve "connect.facebook.net/gtm"
# gibi yol içeren girdiler host ile hiç eşleşemediği için düzeltildi.
REKLAM_DOMAINLERI = frozenset(
    {
        "doubleclick.net",
        "googleadservices.com",
        "googlesyndication.com",
        "googletagmanager.com",
        "google-analytics.com",
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
        "mc.yandex.ru",
        "clarity.ms",
        "connect.facebook.net",
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
)

REGEX_KALIPLARI = (
    re.compile(
        r"[/\?\=\&\._](ad|ads|adsystem|adserver|adservice|adframe|adtrack|banner|popunder|popup|sponsor|telemetry|analytics|tracker)[/\?\=\&\._]",
        re.IGNORECASE,
    ),
    re.compile(
        r"(pagead2|googlesyndication|doubleclick|google-analytics|pixel\.facebook|analytics\.tiktok)",
        re.IGNORECASE,
    ),
    re.compile(r"/ad(s)?/(banner|script|view|click|serve|fetch)", re.IGNORECASE),
)


def host_engellendi_mi(host: str | None) -> bool:
    """Host, reklam domaini mi? (birebir veya alt-domain eşleşmesi)"""
    h = domain_normalize(host)
    if not h:
        return False
    for domain in REKLAM_DOMAINLERI:
        if _eslesiyor(h, domain):
            return True
    return False


def url_engellendi_mi(url: str | None) -> bool:
    """URL, reklam kalıplarına uyuyor mu?"""
    if not url:
        return False
    return any(regex.search(url) for regex in REGEX_KALIPLARI)


# ---------------------------------------------------------------------------
# Çerez yöneticisi (1.0 çerez hatası düzeltmesi)
# ---------------------------------------------------------------------------
#
# Eski davranışın hataları (main4/main6/main7):
# 1. Tek `su_anki_domain` değişkeni vardı; birden çok domain çerez
#    gönderdiğinde son domain öncekilerin üzerine yazıyordu. Kullanıcı
#    "İzin Ver"e basınca yalnızca son domain izinli sayılıyor, diğer
#    domainlerin çerezleri kararsız kalıp her seferinde yeniden
#    soruluyordu (sonsuz soru döngüsü).
# 2. Her çerezde soru çubuğu yeniden gösterilip etiketi değiştiriliyordu;
#    sayfa 20 çerez gönderirse çubuk 20 kez titriyordu.
# 3. Domain karşılaştırması büyük/küçük harf duyarsız değildi ve alt
#    domain eşleşmesi yoktu; "Google.com" ile "google.com" farklı
#    sayılıyordu, engellenen site alt domainle çerez gönderince yeniden
#    soruluyordu.
# 4. Boş domain'li (host-only) çerezler "" domain'iyle soruluyordu.
# 5. Kararlar yalnızca bellekte tutuluyordu; tarayıcı her açılışta
#    aynı sitelere yeniden soruyordu.
#
# Bu sınıf kuyruk tabanlıdır: her domain en fazla bir kez sorulur,
# kararlar QSettings ile kalıcı saklanır, domain eşleşmesi normalize
# ve alt-domain duyarlıdır.


class CerezYoneticisi:
    """Çerez izin/engel kararlarını kuyruk ve kalıcılıkla yönetir.

    `ayarlar` parametresi QSettings benzeri bir nesnedir
    (value(key, default) / setValue(key, value)); None verilirse
    kararlar yalnızca bellekte tutulur (testler için uygundur).
    """

    def __init__(self, ayarlar=None):
        self.ayarlar = ayarlar
        self.izin_verilen: set[str] = set()
        self.engellenen: set[str] = set()
        self.varsayilan_politika: str = POLITIKA_SOR
        # domain -> bekleyen çerez listesi
        self.bekleyen: dict[str, list] = {}
        # sorulacak domain'ler (FIFO)
        self.kuyruk: deque[str] = deque()
        self.su_anki_domain: Optional[str] = None
        self._yukle()

    # -- kalıcılık ---------------------------------------------------------

    def _yukle(self) -> None:
        if self.ayarlar is None:
            return
        try:
            izin = self.ayarlar.value("cookies/allowed", []) or []
            engel = self.ayarlar.value("cookies/blocked", []) or []
            politika = self.ayarlar.value("cookies/policy", POLITIKA_SOR) or POLITIKA_SOR
        except Exception:
            return
        self.izin_verilen = {domain_normalize(d) for d in izin if domain_normalize(d)}
        self.engellenen = {domain_normalize(d) for d in engel if domain_normalize(d)}
        if politika in GECERLI_POLITIKALAR:
            self.varsayilan_politika = politika

    def _kaydet(self) -> None:
        if self.ayarlar is None:
            return
        try:
            self.ayarlar.setValue("cookies/allowed", sorted(self.izin_verilen))
            self.ayarlar.setValue("cookies/blocked", sorted(self.engellenen))
            self.ayarlar.setValue("cookies/policy", self.varsayilan_politika)
        except Exception:
            pass

    # -- karar -------------------------------------------------------------

    def karar(self, domain: str | None) -> str:
        """Domain için güncel kararı döner ("izin" | "engelle" | "sor")."""
        if self.varsayilan_politika == POLITIKA_IZIN_VER:
            return KARAR_IZIN
        if self.varsayilan_politika == POLITIKA_ENGELLE:
            return KARAR_ENGELLE
        return domain_karari(domain, self.izin_verilen, self.engellenen)

    # -- cookieAdded akışı ---------------------------------------------------

    def cerez_eklendi(self, cookie, cookie_store) -> str:
        """Yeni çerez için karar verir; "izin" | "engelle" | "sor" döner.

        "sor" durumunda çerez domain kuyruğuna eklenir (aynı domain
        zaten kuyruktaysa yalnızca çerez listesine eklenir, çubuk
        yeniden tetiklenmez).
        """
        domain = domain_normalize(getattr(cookie, "domain", lambda: "")())
        if not domain:
            # Host-only çerez: domain bilinmiyor, sessiz izin ver.
            return KARAR_IZIN

        k = self.karar(domain)
        if k == KARAR_IZIN:
            return KARAR_IZIN
        if k == KARAR_ENGELLE:
            try:
                cookie_store.deleteCookie(cookie)
            except Exception:
                pass
            return KARAR_ENGELLE

        # Soru gerekli: kuyruğa ekle
        self.bekleyen.setdefault(domain, []).append(cookie)
        if domain != self.su_anki_domain and domain not in self.kuyruk:
            self.kuyruk.append(domain)
        return KARAR_SOR

    def sıradaki(self) -> Optional[str]:
        """Sıradaki sorulacak domaini aktif yapar (yoksa None)."""
        if self.su_anki_domain is not None:
            return self.su_anki_domain
        while self.kuyruk:
            d = self.kuyruk.popleft()
            if self.karar(d) != KARAR_SOR:
                # Karar bu arada değişmiş (politika/liste); soruyu atla.
                self.bekleyen.pop(d, None)
                continue
            self.su_anki_domain = d
            return d
        return None

    def izin_ver(self) -> Optional[str]:
        """Aktif domain için izin verir, sıradakini döner."""
        if self.su_anki_domain:
            self.izin_verilen.add(self.su_anki_domain)
            self.engellenen.discard(self.su_anki_domain)
            self.bekleyen.pop(self.su_anki_domain, None)
            self._kaydet()
            self.su_anki_domain = None
        return self.sıradaki()

    def reddet(self, cookie_store) -> Optional[str]:
        """Aktif domainin çerezlerini siler, engeller, sıradakini döner."""
        if self.su_anki_domain:
            self.engellenen.add(self.su_anki_domain)
            self.izin_verilen.discard(self.su_anki_domain)
            for c in self.bekleyen.pop(self.su_anki_domain, []):
                try:
                    cookie_store.deleteCookie(c)
                except Exception:
                    pass
            self._kaydet()
            self.su_anki_domain = None
        return self.sıradaki()

    # -- yardımcılar ---------------------------------------------------------

    def bekleyen_sayisi(self, domain: Optional[str] = None) -> int:
        if domain is not None:
            return len(self.bekleyen.get(domain_normalize(domain), []))
        return sum(len(v) for v in self.bekleyen.values())

    def bekleyen_domain_sayisi(self) -> int:
        return len(self.bekleyen)

    def politika_ayarla(self, politika: str) -> None:
        if politika not in GECERLI_POLITIKALAR:
            raise ValueError(f"Geçersiz çerez politikası: {politika!r}")
        self.varsayilan_politika = politika
        self._kaydet()

    def bekleyenleri_temizle(self, cookie_store) -> None:
        """Kuyruktaki tüm bekleyen çerezleri siler (politika değişiminde)."""
        for cookies in self.bekleyen.values():
            for c in cookies:
                try:
                    cookie_store.deleteCookie(c)
                except Exception:
                    pass
        self.bekleyen.clear()
        self.kuyruk.clear()
        self.su_anki_domain = None

    def kuyrugu_bosalt(self) -> None:
        """Bekleyen çerezleri silmeden soru kuyruğunu boşaltır.

        Politika "her zaman izin ver"e çevrildiğinde kullanılır:
        bekleyen çerezler zaten izinli sayılır, silinmez.
        """
        self.bekleyen.clear()
        self.kuyruk.clear()
        self.su_anki_domain = None

    def temizle(self) -> None:
        """İzin/engel listelerini ve bekleyenleri sıfırlar."""
        self.izin_verilen.clear()
        self.engellenen.clear()
        self.bekleyen.clear()
        self.kuyruk.clear()
        self.su_anki_domain = None
        self._kaydet()
