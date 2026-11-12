#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tbrowser derleme betiği.

Kullanım:
    pip install -r requirements.txt
    python build.py [--clean]

Çıktı:
    dist/tbrowser/          — çalıştırılabilir klasör
    release/tbrowser-v1.0.0-<isletimsistemi>-<mimari>.zip — dağıtım paketi

Not: PyInstaller, çalıştırıldığı işletim sisteminin ikili dosyasını
üretir (Windows'ta .exe, Linux'ta çalıştırılabilir, macOS'ta ikili dosya).
Tüm platformlar için GitHub Actions (.github/workflows/build.yml)
otomatik derleme yapar.
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from tbrowser_core import SURUM

KOK = Path(__file__).resolve().parent


def isletimsistemi_adi() -> str:
    s = sys.platform
    if s.startswith("win"):
        return "windows"
    if s == "darwin":
        return "macos"
    return "linux"


def arsiv_olustur(kaynak_klasor: Path, hedef_zip: Path) -> None:
    if hedef_zip.exists():
        hedef_zip.unlink()

    # Unix'te (özellikle macOS QtWebEngineCore.framework sembolik bağları
    # ve çalıştırma izinleri için) sistemin zip aracını kullan.
    zip_bin = shutil.which("zip") if sys.platform != "win32" else None
    if zip_bin:
        sonuc = subprocess.run(
            [zip_bin, "-ry", "-q", str(hedef_zip), kaynak_klasor.name],
            cwd=str(kaynak_klasor.parent),
        )
        if sonuc.returncode == 0:
            return

    with zipfile.ZipFile(hedef_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for dosya in kaynak_klasor.rglob("*"):
            if dosya.is_file():
                zf.write(dosya, dosya.relative_to(kaynak_klasor.parent))


def main() -> int:
    parser = argparse.ArgumentParser(description="tbrowser derleme betiği")
    parser.add_argument("--clean", action="store_true", help="Önceki çıktıyı temizle")
    args = parser.parse_args()

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("Hata: PyInstaller bulunamadı. Kurulum: pip install pyinstaller", file=sys.stderr)
        return 1

    dist = KOK / "dist"
    build_dir = KOK / "build"
    release = KOK / "release"
    if args.clean:
        for p in (dist, build_dir):
            if p.exists():
                shutil.rmtree(p)

    print(f"tbrowser v{SURUM} derleniyor ({isletimsistemi_adi()}/{platform.machine()})…")
    sonuc = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "tbrowser.spec", "--noconfirm"],
        cwd=str(KOK),
    )
    if sonuc.returncode != 0:
        print("Derleme başarısız oldu.", file=sys.stderr)
        return sonuc.returncode

    cikti = dist / "tbrowser"
    if not cikti.exists():
        print(f"Hata: beklenen çıktı bulunamadı: {cikti}", file=sys.stderr)
        return 1

    release.mkdir(exist_ok=True)
    zip_adi = f"tbrowser-v{SURUM}-{isletimsistemi_adi()}-{platform.machine()}.zip"
    zip_yolu = release / zip_adi
    arsiv_olustur(cikti, zip_yolu)
    print(f"Dağıtım paketi hazır: {zip_yolu}")
    print("Bu zip dosyasını GitHub Releases'a yükleyebilirsiniz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
