r"""
📖 prepare_quran.py — QURAN-MAJEED SAFE IMPORT (read-only knowledge)

Jab aap QuranShareef-with-Urdu-Translation file de ke "add karo" bolo, ye script:
  1. File ko knowledge/quran/ me copy kare
  2. SHA-256 fingerprint + manifest banaye
  3. Windows read-only attribute laga de (koi bhi vapas se likh na sake)
  4. Ayah-by-ayah index (index.JSONL) banaye — retrieval ke liye ONLY
  5. Training corpus (data/corpus.txt) par kabhi likhega NAHI ← sabse ghatiya glati

Usage:
  python scripts/prepare_quran.py D:\path\to\quran-urdu.txt
"""
import json
import os
import re
import shutil
import stat
import sys
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
QURAN_DIR = os.path.join(ROOT, "knowledge", "quran")
os.makedirs(QURAN_DIR, exist_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_read_only(path):
    os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)


def extract_records(src_path):
    """Simple structure: 'SURAH:AYAH|text' lines ya plain text wali lines.
    Return list of dicts {surah, ayah, text}."""
    recs = []
    pat = re.compile(r"^(\d{1,3})\s*[:\-]\s*(\d{1,3})\s*[\|,]\s*(.+)$")
    with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pat.match(line)
            if m:
                recs.append({"surah": m.group(1), "ayah": m.group(2), "text": m.group(3)})
            else:
                recs.append({"surah": "", "ayah": "", "text": line})
    return recs


def main(src_path):
    if not os.path.exists(src_path):
        print("❌ Source file nahi mili:", src_path)
        return
    basename = os.path.basename(src_path)
    dst = os.path.join(QURAN_DIR, basename)
    if os.path.exists(dst):
        print("⚠️ Pehle se hai:", dst, "| iska use karunga.")
    else:
        shutil.copy2(src_path, dst)

    # 1) fingerprint + manifest + read-only
    digest = sha256(dst)
    make_read_only(dst)
    from datetime import datetime
    manifest = {
        "file": basename, "sha256": digest,
        "locked_on": datetime.utcnow().isoformat(),
        "rule": "IMMUTABLE — AI is file ko kabhi modify nahi kar sakta",
    }
    with open(os.path.join(QURAN_DIR, "quran_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 2) retrieval-only index (trainings corpus NAHI)
    recs = extract_records(dst)
    idx_path = os.path.join(QURAN_DIR, "index.jsonl")
    with open(idx_path, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"🕌 Quran import SAFE:")
    print(f"   file        : {dst}")
    print(f"   sha256      : {digest[:16]}…  (locked, read-only)")
    print(f"   ayah records: {len(recs):,}")
    print(f"   index (READ): {idx_path}")
    print("   ➜ data/corpus.txt untouched — trainings weigth se dua-ta-alluq NAHI.")
    print("   ➜ AI in ayahs ko SIRF padh kar de sakta hai, likhna sakta nahi.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prepare_quran.py <quran-file>")
        sys.exit(1)
    main(sys.argv[1])
