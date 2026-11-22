#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MEMORY-CORRUPTION-RECOVERY test (S6) — 100% offline.

Saboot: kharab-JSONL (aadhi-likhi/ghalat lines) par:
  1) valid-yaadein BACHI rehti hain (recall/facts kaam karte hain)
  2) kharab-file ki asli-copy `.corrupt` backup ban jaati hai (data-bachaw)
  3) naya remember() phir se likhna jari rehta hai
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from model.memory import EpisodicStore  # noqa: E402

RES = []


def chk(no, name, ok, note=""):
    RES.append((no, name, bool(ok), note))


d = tempfile.mkdtemp()
st = EpisodicStore(d)
st.remember("mera naam Bilal hai", "user_naam=Bilal", tag="yaad")
st.remember("mujhe cricket pasand hai", "user_pasand=cricket", tag="yaad")

# 🧨 kharabi: file ke beech me aadhi/ghalat line ghusa do (crash-jaisa)
with open(st.path, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()
lines.insert(1, '{"ts": 1, "user": "AADHI-LIKHI-LINE...', )  # ghalat JSON
with open(st.path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

fa = st.facts("user_naam=")
chk(1, "kharabi ke bawajood valid-yaad bachi (Bilal)",
    any("Bilal" in x for x in fa), str(fa))
rec = st.recall("cricket")
chk(2, "recall bhi chalta hai (koi crash nahi)", len(rec) >= 1, str(len(rec)))
chk(3, "kharab-file ki `.corrupt` backup bani",
    os.path.exists(st.path + ".corrupt"), st.path + ".corrupt")
st.remember("naya hukum chala", "user_naya=ok", tag="yaad")
fa2 = st.facts("user_naya=")
chk(4, "remember() kharabi-ke-baad bhi likhta hai",
    any("ok" in x for x in fa2), str(fa2))

print("=" * 62)
fails = [r for r in RES if not r[2]]
for no, name, ok, note in RES:
    print("  %s [%d] %s%s" % ("PASS" if ok else "FAIL", no, name,
                              (" | " + note) if note and not ok else ""))
print("=" * 62)
print("MEMORY-RECOVERY: %d | PASS: %d | FAIL: %d"
      % (len(RES), len(RES) - len(fails), len(fails)))
sys.exit(1 if fails else 0)
