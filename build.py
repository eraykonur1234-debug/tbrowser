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
üretir (Windows'ta .exe, Linux'ta çalıştırılabilir, macOS'ta .app
içeren klasör). Tüm platformlar için GitHub Actions
(.github/workflows/build.yml) otomatik derleme yapar.
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
    with zipfile.ZipFile(zip_yolu, "w", zipfile.ZIP_DEFLATED) as zf:
        for dosya in cikti.rglob("*"):
            if dosya.is_file():
                zf.write(dosya, dosya.relative_to(dist))
    print(f"Dağıtım paketi hazır: {zip_yolu}")
    print("Bu zip dosyasını GitHub Releases'a yükleyebilirsiniz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
