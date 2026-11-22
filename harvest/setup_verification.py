"""
🛠️ setup_verification.py — SACRED-SETUP KI ASLI JAANCHA (koi fake-download nahi)

Pehle ye module "Quran downloading..." likh kar KHALI {} / [] files likhta tha
(fake). Ab sach par chalta hai:
  1. Asli corpus files (7 Sahih hadith + harvest_quran + sacred_facts) check.
  2. Jo master JSON khaali/0-bytes/fake-artifact hai — usay ASLI local corpus
     se dobara banao (koi internet nahi).
  3. Poori report chhapta hai — jo nahi mila wo SAAF likhta hai.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(HERE)
else:
    ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
CORPUS = os.path.join(DATA, "corpus_big")

HADITH_LABELS = {
    "bukhari": "Sahih al-Bukhari", "muslim": "Sahih Muslim",
    "abudawud": "Sunan Abi Dawud", "tirmidhi": "Jami' at-Tirmidhi",
    "nasai": "Sunan an-Nasa'i", "ibnmajah": "Sunan Ibn Majah",
    "malik": "Muwatta Malik",
}


def _jawab_count(path: str) -> int:
    """File me kitni asli 'Jawab:' entries (real content ginnat)."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return sum(1 for ln in f if ln.strip().lower().startswith("jawab:"))
    except OSError:
        return 0


def _is_fake(path: str) -> bool:
    """File gayab, 0-bytes, ya khaali {} / [] — fake artifact."""
    if not os.path.exists(path):
        return True
    if os.path.getsize(path) < 3:
        return True
    try:
        with open(path, encoding="utf-8") as f:
            body = f.read(512).strip()
        return body in ("{}", "[]")
    except OSError:
        return True


def _build_masters():
    """Masters ko ASLI local corpus se banao (counts asli file-se)."""
    report = {}
    quran_path = os.path.join(CORPUS, "harvest_quran.txt")
    qn = _jawab_count(quran_path) if os.path.exists(quran_path) else 0
    quran_master = {
        "name": "Al-Quran (harvest corpus — clearquran, asli local file)",
        "file": os.path.relpath(quran_path, ROOT),
        "ayat_entries": qn,
        "policy": "sirf pure-sunni sources (harvest/source_policy.py)",
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(os.path.join(DATA, "quran_master.json"), "w", encoding="utf-8") as f:
        json.dump(quran_master, f, ensure_ascii=False, indent=1)
    report["quran_master.json"] = "%d ayat entries" % qn

    files, counts = [], {}
    if os.path.isdir(CORPUS):
        for fn in sorted(os.listdir(CORPUS)):
            if fn.startswith("hadith_") and fn.endswith(".txt"):
                book = fn.split("_")[1].lower()
                c = _jawab_count(os.path.join(CORPUS, fn))
                counts[book] = c
                files.append({"book": book, "hadiths": c,
                              "file": os.path.relpath(os.path.join(CORPUS, fn), ROOT)})
    buk = [h for h in files if h["book"] == "bukhari"]
    bukhari_master = {
        "name": HADITH_LABELS["bukhari"],
        "hadiths": buk[0]["hadiths"] if buk else 0,
        "files": [os.path.relpath(os.path.join(ROOT, h["file"]), ROOT) for h in buk],
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(os.path.join(DATA, "bukhari_master.json"), "w", encoding="utf-8") as f:
        json.dump(bukhari_master, f, ensure_ascii=False, indent=1)
    report["bukhari_master.json"] = "%d ahadith" % bukhari_master["hadiths"]

    hadith_master = {"books": HADITH_LABELS, "count": len(files),
                     "files": files,
                     "updated": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(DATA, "hadith_master.json"), "w", encoding="utf-8") as f:
        json.dump(hadith_master, f, ensure_ascii=False, indent=1)
    report["hadith_master.json"] = "%d corpus-files: %s" % (
        len(files), ", ".join("%s=%d" % (k, v) for k, v in counts.items()))
    return report


def download_data():
    """(purana naam sambhala) — ab ASLI: local corpus check + masters ki
    asli-tarkeeb. Internet download NAHI hota — sach hi chapta hai."""
    real = []
    if os.path.isdir(CORPUS):
        for fn in sorted(os.listdir(CORPUS)):
            if (fn.startswith("hadith_") or fn in ("harvest_quran.txt",
                                                   "sacred_facts.txt")) \
                    and fn.endswith(".txt"):
                kb = os.path.getsize(os.path.join(CORPUS, fn)) // 1024
                if kb > 1:
                    real.append("%s (%dKB)" % (fn, kb))
    print("ASLI sacred corpus maujood: %d files" % len(real))
    for r in real:
        print("  ✓", r)
    if not real:
        print("⚠ corpus nahi mila — scripts/install_sacred_texts.py chalayein")
        return {}
    rep = _build_masters()
    print("MASTERS (asli local data se baney):")
    for k, v in rep.items():
        print("  ✓ %s → %s" % (k, v))
    return rep


if __name__ == "__main__":
    try:
        import sys as _s
        _s.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    download_data()
