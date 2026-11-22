# -*- coding: utf-8 -*-
"""_zip_web.py — package-root ko fresh zip (chain-ke-zdir jaisa hi) + web-copy.
make_package ke baad chalao. Qanoon: sirf desktop-package zip, credentials NAHI
(zdir skip karta hai; _purge_secrets pehle-se package me chal-chuka)."""
import os
import shutil
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _apply_training_everywhere import ROOTPKG, SRC, zdir  # noqa: E402

zpath = os.path.join(ROOTPKG, "hemomemo_ai_complete_final.zip")
# 🛡 NESTED-ZIP-BUG-ka-hal: purani zip pehle MITAO (warna zdir usi ko andar
# zip kar-deta hai — 216MB faltu, zip 460MB ho-jati). Qanoon: zip me zip NAHI.
if os.path.exists(zpath):
    os.remove(zpath)
    print("STALE-ZIP removed:", zpath)
for _f in os.listdir(ROOTPKG):
    if _f.endswith(".zip"):
        try:
            os.remove(os.path.join(ROOTPKG, _f))
            print("STALE-ZIP removed:", _f)
        except Exception:
            pass
n = zdir(ROOTPKG, zpath)
mb = os.path.getsize(zpath) / 1048576.0
print("ZIP-OK: %s (%d files, %.1f MB)" % (zpath, n, mb))

dst = os.path.join(SRC, "web", "HemomemoUltra-People.zip")
shutil.copy2(zpath, dst)
print("WEB-COPY-OK: %s (%.1f MB)" % (dst, os.path.getsize(dst) / 1048576.0))
