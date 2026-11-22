# -*- coding: utf-8 -*-
"""DEEP-CHECK (read-only): DigitalBrain source ↔ package ↔ repo ↔ site.

User-qanoon: har jagah SAB-SE-NAYA same ho — koi purana/jhoota copy nahi.
Report: missing-file list, hash-mismatch list, brain-freshness, scripts."""
import hashlib
import json
import os
import time
import urllib.request

SRC = r"D:\DigitalBrain"
PKG = r"D:\HemomemoUltra-People"
REPO_RAW = "https://raw.githubusercontent.com/noity0/hemomemo-ai/main/"

COMPARE = [
    "model/understand.py", "model/tokenize.py", "model/generate.py",
    "model/memory.py", "model/feelings.py", "model/autonomous.py",
    "model/cognition.py", "model/think_level.py", "model/compose.py",
    "core/hub.py", "core/brain_hub.py" if os.path.exists(
        os.path.join(SRC, "core", "brain_hub.py")) else "core/hub.py",
    "agent/console_app.py", "agent/browser_cloud.py", "agent/orders.py",
    "agent/mc_bot.py", "agent/pc_eye.py", "agent/tasks.py",
    "server/hemomemo_server.py", "security/guard.py", "accounts.py",
    "core/owner.py", "app/hemomemo_app.py",
]


def sha(p):
    h = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            for ch in iter(lambda: f.read(65536), b""):
                h.update(ch)
        return h.hexdigest()[:12]
    except Exception:
        return "MISSING"


def mt(p):
    try:
        return time.strftime("%m-%d %H:%M",
                             time.localtime(os.path.getmtime(p)))
    except Exception:
        return "-"


print("=" * 70)
print("A) SOURCE ↔ PACKAGE hash-match")
print("=" * 70)
diffs, miss = [], []
for rel in COMPARE:
    if "/" not in rel or rel.endswith("hub.py") and not os.path.exists(
            os.path.join(SRC, rel)):
        continue
    s, k = os.path.join(SRC, rel), os.path.join(PKG, rel)
    hs, hk = sha(s), sha(k)
    tag = "OK" if hs == hk else "DIFF"
    if hs == "MISSING" or hk == "MISSING":
        tag, miss_m = "MISS", True
        miss.append(rel)
    elif hs != hk:
        diffs.append(rel)
    print("  %-28s %-6s src=%s pkg=%s" % (rel, tag,
                                          hs if hs != "MISSING" else "-----",
                                          hk if hk != "MISSING" else "-----"))

print()
print("DIFF-LIST: %d" % len(diffs))
for d in diffs:
    print("   -", d)

print()
print("=" * 70)
print("B) BRAIN-freshness")
print("=" * 70)
ck = os.path.join(SRC, "model", "checkpoints")
pkgck = os.path.join(PKG, "model", "checkpoints")
for label, d in (("SRC", ck), ("PKG", pkgck)):
    g = [(f, os.path.getsize(os.path.join(d, f)), os.path.getmtime(
        os.path.join(d, f))) for f in os.listdir(d)
        if f.startswith("hemomaster_") and f.endswith(".npz")]
    g.sort(key=lambda x: -x[2])
    for f, s, m in g[:2]:
        print("  %s %-30s %5.1f MB  %s" % (label, f, s / 1048576, mt(
            os.path.join(d, f))))

print()
print("=" * 70)
print("C) PACKAGE root-kits (EXE/BAT/PNG)")
print("=" * 70)
for rel in ["Hemomemo-Ultra-Brain.exe", "Hemomemo-GameBot.exe",
            "START-HEMOMO.bat", "UPDATE-BRAIN.bat", "README.md",
            "agent/browser_cloud.py", "web/index.html"]:
    p = os.path.join(PKG, rel)
    ok = os.path.exists(p)
    print("  %-30s %s  %s" % (rel, "YA" if ok else "GHAIB",
                              "%.1f MB" % (os.path.getsize(p) / 1048576)
                              if ok and rel.endswith(".exe") else
                              (mt(p) if ok else "-")))

print()
print("=" * 70)
print("D) SITES (3x) + manifest")
print("=" * 70)
for p in ("D:/DigitalBrain/web/index.html",
          "D:/DigitalBrain/web_surge/index.html",
          "D:/DigitalBrain/public/index.html"):
    print("  %-42s %s" % (p, sha(p)))
print("  manifest: %s" % sha(os.path.join(SRC, "web", "brain_manifest.json")))

print()
print("=" * 70)
print("E) REPO (main) — keyfile freshness")
print("=" * 70)
for rel in ("index.html", "README.md", "model/understand.py",
            "agent/browser_cloud.py", "scripts/qa700_hard.py",
            "public/brain_manifest.json"):
    url = REPO_RAW + rel
    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            data = r.read()
        print("  %-30s remote %8d B  sha=%s (AAMUDA)" % (
            rel, len(data), hashlib.sha256(data).hexdigest()[:12]))
    except Exception as e:
        print("  %-30s REMOTE-ABSENT (%s)" % (rel, e))

print()
print("DEEP-CHECK tamam (%s)" % time.strftime("%H:%M:%S"))
print("Legend: hash=pehle-12 darjy | DIFF=source-pak-upgrade-lamp")
