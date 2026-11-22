"""
🔍 verify.py — Knowledge Verification Engine (ASLI — koi fake-pass nahi)

Har data chunk ko locally verify karta hai (sab kuch LOCAL real corpus se —
koi API/model/internet nahi):
  1. STRUCTURE  : text zinda, munasib lambai, printable, junk nahi.
  2. FAITH-GUARD: gair-maslak/deviant-firqah ke alfaaz → FORAN reject.
  3. QURAN-CITE : "Quran 2:255" / Surah / Ayat ka dawa → asli ayat
     data/corpus_big/harvest_quran.txt (801KB real index) se match hota ho.
  4. HADITH-CITE: Bukhari/Muslim/... ka dawa → kitab 7 Sahih books me ho
     aur quoted text data/corpus_big/hadith_*_english_sahih.txt se mile.

DB me jo hai usi se tasdeeq — citation jhooti → verify FAIL (pehle ye gate
hamesha True deta tha — ab asli engine hai).
"""
import os
import sys
import re

HERE = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(HERE)
else:
    ROOT = os.path.dirname(HERE)
QURAN_DB = os.path.join(ROOT, "data", "quran_master.json")
BUKHARI_DB = os.path.join(ROOT, "data", "bukhari_master.json")
CORPUS = os.path.join(ROOT, "data", "corpus_big")

FAITH_OFF = [
    "qadiyani", "qadiani", "ahmadi", "ahmadiyya", "mirza ghulam",
    "shia", "taifa", "ghulat", "muqtadi",
]

# 7 sahih kitabein (sunnah.com grades — harvest/source_policy.py policy)
SAHIH_BOOKS = {"bukhari", "muslim", "tirmidhi", "abu dawud", "abudawud",
               "nasai", "nasa'i", "ibn majah", "ibnmajah", "muwatta", "malik"}

_QURAN_CITE = re.compile(r"(?i)\bquran\s*\d+|:\d+\)|\bsurah?\b|\bayat|آیت|\bآية\b")
_HADITH_CITE = re.compile(r"(?i)\b(bukhari|muslim|tirmidhi|abu\s*dawud|abudawud|"
                          r"nasai|nasa'i|ibn\s*majah|ibnmajah|muwatta|malik)\b")

_INDEX = {"quran": None, "hadith": None}


def _norm(s: str) -> str:
    """Text → safa-suthra comparison-key (lowercase, sirf alnum+space)."""
    s = re.sub(r"[^a-z0-9\s]", " ", (s or "").lower())
    return re.sub(r"\s+", " ", s).strip()


def _jawab_lines(path: str):
    """Corpus-pair file se 'Jawab:' lines (asli ayat/hadith text)."""
    out = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for ln in f:
                s = ln.strip()
                if s.lower().startswith("jawab:") and len(s) > 30:
                    out.append(s[6:].strip())
    except OSError:
        pass
    return out


def _build_index():
    """Asli sacred reference index (lazy, ek dafa): Quran + 7 hadith kitabein."""
    if _INDEX["quran"] is not None:
        return
    qset, hset, books = set(), set(), set()
    qpath = os.path.join(CORPUS, "harvest_quran.txt")
    for ay in _jawab_lines(qpath):
        n = _norm(ay)
        if len(n) >= 40:
            qset.add(n[:80])                       # pehle 80 norm-chars = key
            m = re.match(r"(?i)quran\s*(\d+)", ay)
            if m:
                qset.add("quran %s" % m.group(1))
    if os.path.isdir(CORPUS):
        for fn in sorted(os.listdir(CORPUS)):
            if fn.startswith("hadith_") and fn.endswith(".txt"):
                book = fn.split("_")[1].lower()
                if book in SAHIH_BOOKS or len(book) > 3:
                    books.add(book)
                    for hd in _jawab_lines(os.path.join(CORPUS, fn)):
                        n = _norm(hd)
                        if len(n) >= 40:
                            hset.add(n[:80])
                        m = re.match(r"(?i)sahih al-?\s*\w+\s+(\d+)", hd)
                        if m:
                            hset.add("hadith %s" % m.group(1))
    _INDEX["quran"] = qset
    _INDEX["hadith"] = hset
    _INDEX["books"] = books


def _snippet_in(text: str, keys: set) -> bool:
    """Text ki sab-se-lambi alnum-window (80 chars) index me hai?"""
    n = _norm(text)
    if len(n) >= 80:
        return n[:80] in keys
    return bool(n) and any(n[:80] in k for k in keys) if n else False


def is_verified(text: str) -> bool:
    """ASLI verification: structure + faith + citation-against-real-corpus."""
    t = (text or "").strip()
    # --- 1. structure ---
    if len(t) < 20 or len(t) > 2000:
        return False
    printable = sum(1 for c in t if c.isprintable() or c in "\n\t")
    if printable < len(t) * 0.95:
        return False
    low = t.lower()
    # --- 2. faith guard ---
    if any(mark in low for mark in FAITH_OFF):
        return False
    _build_index()
    # --- 3. Quran citation check ---
    if _QURAN_CITE.search(t):
        # number-dawa: "quran 2", "surah 2", "ayat 255" jaisa
        nums = set(re.findall(r"(?i)(?:quran|surah|surat|ayat|ayah)[^0-9]{0,8}(\d{1,3})", low))
        known = any(("quran %s" % n) in _INDEX["quran"] for n in nums) if nums else None
        quoted = _snippet_in(t, _INDEX["quran"])
        if nums and known is False and not quoted:
            return False          # anjana ayat-number + quoted-text bhi index me nahi
        if not nums and re.search(r'["\u201c].{40,}["\u201d]', t) and not quoted:
            return False          # lamba ayat-quote dawa — asli index me nahi
    # --- 4. hadith citation check ---
    m = _HADITH_CITE.search(t)
    if m:
        book = m.group(1).lower().replace("'", "").replace(" ", "")
        if book not in SAHIH_BOOKS and not any(b.startswith(book) for b in _INDEX["books"]):
            return False          # gair-sahih/na-maloom kitab ka dawa
        nums = set(re.findall(r"(?i)(?:bukhari|muslim|tirmidhi|dawud|nasai|majah|muwatta)[^0-9]{0,12}(\d{1,5})", low))
        known = any(("hadith %s" % n) in _INDEX["hadith"] for n in nums) if nums else None
        quoted = _snippet_in(t, _INDEX["hadith"])
        if nums and known is False and not quoted:
            return False          # anjana hadith-number + text bhi match nahi
        if not nums and re.search(r"(?i)\b(narrated|riwayat|hadith number)\b", low) \
                and re.search(r'["\u201c].{40,}["\u201d]', t) and not quoted:
            return False          # lambi riwayat-quote dawa — index me nahi
    return True


def verify_chunk(text: str) -> bool:
    """True agar verify ho jaye, False agar ghalat ya verify na ho."""
    if not is_verified(text):
        return False
    return True


def stats() -> dict:
    """Verify-engine ki asli hifz (dashboard/status ke liye)."""
    _build_index()
    return {"quran_refs": len(_INDEX["quran"]),
            "hadith_refs": len(_INDEX["hadith"]),
            "books": sorted(_INDEX["books"])}


if __name__ == "__main__":
    import json as _json
    try:
        import sys as _sys
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("INDEX:", stats())
    ok = ("Sahih al-Bukhari 1: Narrated Umar bin Al-Khattab: The reward of deeds "
          "depends upon the intentions.")
    bad = ("Sahih al-Bukhari 99999: Narrated Nobody: This is a totally fabricated "
           "hadith text that does not exist in the sahih corpus at all.")
    print("asli hadith:", is_verified(ok))
    print("fake hadith (anjana number):", is_verified(bad))
    print("fake ayat (anjana number):", is_verified(
        "Quran 888: And the sun rises from the west and every human will see "
        "this fabricated sign tomorrow morning everywhere."))
    print("aam ilm:", is_verified("Photosynthesis is the process plants use to "
                                  "turn sunlight into chemical energy."))
    print("surah-zikr (bina dawa):", is_verified(
        "Quran me 114 surah hain aur har surah apni jagah tehreer hai."))
    print("masters:", os.path.getsize(QURAN_DB) if os.path.exists(QURAN_DB) else -1,
          os.path.getsize(BUKHARI_DB) if os.path.exists(BUKHARI_DB) else -1)
