import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

KOK = str(Path(__file__).resolve().parent.parent)
if KOK not in sys.path:
    sys.path.insert(0, KOK)
