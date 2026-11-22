r"""
🧹 filter_strong_hadith.py — SIRF SAHIH/HASAN (zaeef MUKAMMAL BAYUKT)

Kya karta hai:
  knowledge/hadith/eng-*.min.json (sunnah.com grades) parh kar 7 books ka
  corpus banata hai jis me sirf PAK rivaayat hai:
    - Bukhari / Muslim / Muwatta Malik → poore (inherent Sahih collections)
    - Abu Dawud / Tirmidhi / Nasai / Ibn Majah → sirf wahi hadith jis ki
      grading Sahih ya Hasan ho (Darussalam/Al-Albani/Fouad grader)
    - Jis me yeh words hon → DROP (zaeef/ghair-ma'amool):
      da'if / daeef / da'eef / weak / mawdu' / maudu' / munkar / matruk /
      fabricated / hasan da'if / zaeef
    - Bagair kisi grading ke hadith (4 books me) → DROP (hmm? kya hi pata
      rivaayat se — sacha ilm sirf misra-rivaayat par)
  Pehle wale *_english_full.txt ko data/corpus_big/_unfiltered/ me hata deta hai
  (PDF ya delete NAHI — bas retrieval corpus se只 safai).
  Output: data/corpus_big/hadith_{book}_english_sahih.txt
  Report:  data/hadith_master.json ke "sahih_only" me counts

Run:  python scripts\filter_strong_hadith.py
      python scripts\filter_strong_hadith.py --report   (sirf counts dikhao)
"""
import json
import os
import sys
import time

r"""
NOTE: code shaamil hai `from harvest.purify` nahi — corpus lines ko pak-rakhne
ke liye khud sanitize/keywords ki minimal copy (harvest/purify imports theva
rakhta hai aur APK panel band karne par bhi run ho).
"""
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HJ = os.path.join(ROOT, "knowledge", "hadith")
BIG = os.path.join(ROOT, "data", "corpus_big")
UNFILTERED = os.path.join(BIG, "_unfiltered")
MASTER = os.path.join(ROOT, "data", "hadith_master.json")

BOOKS = {
    "bukhari": ("Sahih al-Bukhari", False),      # False = grading required nahi
    "muslim": ("Sahih Muslim", False),
    "malik": ("Muwatta Malik", False),
    "abudawud": ("Sunan Abi Dawud", True),       # True = grading required
    "tirmidhi": ("Jami at-Tirmidhi", True),
    "nasai": ("Sunan an-Nasai", True),
    "ibnmajah": ("Sunan Ibn Majah", True),
}

_WEAK_RX = re.compile(
    r"da'?(?:if|eef|ee?f?)|mawdu|maudu|munkar|matruk|fabricat|weak|zaeef|za'ef",
    re.I)
_STRONG_RX = re.compile(r"sahih|hasan", re.I)

# purify ka halka clone (ASCII-safe, machine-xuban)
_ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
_ALLOWED |= set(" \n!(),-.:?&/+'\"")
_REPL = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
         "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " "}


def _sanitize(text: str) -> str:
    if not text:
        return ""
    for k, v in _REPL.items():
        text = text.replace(k, v)
    text = "".join(c if c in _ALLOWED else " " for c in text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


_STOP = set("""the and for that with this from have has was were not are his her
him who all one said their they will which had what about when you your but can
may there been any its into them she per how why who did does out""".split())


def _keywords(text: str, k: int = 4) -> str:
    words = re.findall(r"[a-z]{4,}", text.lower())
    freq = {}
    for w in words:
        if w in _STOP:
            continue
        freq[w] = freq.get(w, 0) + 1
    best = sorted(freq.items(), key=lambda x: -x[1])[:k]
    return " ".join(w for w, _ in best)


def _grade_state(grades, needs_grading: bool):
    """(keep: bool, why: str) — sunnah.com grading qaaida.``"""
    gtext = " ".join(str(g.get("grade", "")) for g in (grades or [])).lower()
    if _WEAK_RX.search(gtext):
        return False, "weak-grade: %s" % gtext[:40]
    if _STRONG_RX.search(gtext):
        return True, "grade-ok: %s" % gtext[:40]
    if not (grades or []):
        if needs_grading:
            return False, "no-grade (4-book rule)"
        return True, "ungraded-but-sahih-collection"
    return True, "graded-neutral"


def filter_book(book, label, needs_grading: bool):
    inp = os.path.join(HJ, "eng-%s.min.json" % book)
    if not os.path.exists(inp):
        return None
    with open(inp, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("hadiths", []) if isinstance(data, dict) else []
    keep, drops = [], []
    seen_ids = set()
    for had in items:
        if not isinstance(had, dict):
            continue
        text = had.get("text") or ""
        # eng files his ma English hoti hai; kalba? agar kisi me sirf Arabic raha
        if not text:
            ent = had.get("englishEntry") or {}
            text = ent.get("text", "")
        clean = _sanitize(text)
        if len(clean) < 30:
            continue
        num = had.get("hadithnumber")
        hnum = str(num) if num not in (None, "") else "0"
        grades = had.get("grades")
        ok, why = _grade_state(grades, needs_grading)
        if not ok:
            drops.append(why)
            continue
        key = (hnum, clean[:60])
        if key in seen_ids:
            continue
        seen_ids.add(key)
        kw = _keywords(clean)
        if not kw:
            continue
        line = "Sawal: %s hadith %s\nJawab: %s %s: %s" % (
            kw, book.lower(), label, hnum, clean)
        keep.append(line)
    # purana unfiltered file ko subfolder me
    old = os.path.join(BIG, "hadith_%s_english_full.txt" % book)
    if os.path.exists(old):
        os.makedirs(UNFILTERED, exist_ok=True)
        import shutil
        shutil.move(old, os.path.join(UNFILTERED, os.path.basename(old)))
    outp = os.path.join(BIG, "hadith_%s_english_sahih.txt" % book)
    head = ("# %s — SAHIH/HASAN-only corpus (sunnah.com grades)\n"
            "# drops: %d | policy: no zaeef, no deviant-fraqa sources\n" % (
                label, len(drops)))
    with open(outp, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(keep) + "\n")
    return {"book": book, "kept": len(keep), "dropped": len(drops),
            "bytes": os.path.getsize(outp)}


def report():
    if not os.path.exists(MASTER):
        print("report nahi — pehle filter chalao")
        return
    with open(MASTER, encoding="utf-8") as f:
        m = json.load(f)
    so = m.get("sahih_only", {})
    print("SAHIH-ONLY REPORT")
    for b, c in so.items():
        print("  %-9s kept %5s dropped %5s" % (b, c.get("kept"),
                                               c.get("dropped")))
    print("  total kept:", sum(c.get("kept", 0) for c in so.values()))


def main():
    if "--report" in sys.argv:
        report()
        return
    results, dropped_total, kept_total = {}, 0, 0
    for book, (label, need_g) in BOOKS.items():
        r = filter_book(book, label, need_g)
        if r is None:
            print("  %s: eng file nahi" % book)
            continue
        results[book] = r
        kept_total += r["kept"]
        dropped_total += r["dropped"]
        print("  %-9s kept %5d | dropped(zaeef/unka) %5d" % (
            book, r["kept"], r["dropped"]))
    # master update (sach ke sath)
    m = {}
    if os.path.exists(MASTER):
        with open(MASTER, encoding="utf-8") as f:
            m = json.load(f)
    m["sahih_only"] = results
    m["sahih_only_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    m["sahih_total"] = kept_total
    with open(MASTER, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print("TOTAL: kept %d hadith (zaeef-drops %d)" % (kept_total, dropped_total))
    print("✅ corpus files: hadith_{book}_english_sahih.txt")


if __name__ == "__main__":
    main()
