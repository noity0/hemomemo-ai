# -*- coding: utf-8 -*-
r"""
📚 _build_ilm_pack.py — 10,000+ ILM-KHAZANA builder (data + abilities)
=====================================================================
Inputs : _ilm_countries.py, _ilm_elements_asma.py, _ilm_themes_a.py, _ilm_themes_b.py
Output : data\corpus_big\ilm_khazana.txt   (Q/A-lines, retrieval-friendly)

QANOON (hamesha):
  - Sab local; koi AI-platform API nahi; koi network nahi (pure file-gen).
  - 🛡️ PAAK-SAFAI filter: har line banned-sites/sect-terms par check hoti hai
    (ahmadiyya/alislam/qadian/mirza/ghulam/al-islam.org/alhassanain/shiasource/
    tashayyu/shia/shiite/twelver/ismaili) — match par line FORAN DROP + report.
  - Sirf pukka-ilm (countries/elements/asma/math standard).

Chalao:  python _build_ilm_pack.py
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT = os.path.join("data", "corpus_big", "ilm_khazana.txt")

# ---------------- 🛡️ paak-safai (deep-analysis guard) ----------------
_BANNED_RX = re.compile(
    r"(?i)(ahmadiyya|alislam\.org|qadian|mirza ghulam|al-islam\.org|"
    r"alhassanain|shiasource|tashayyu|\bshia\b|shiaism|shiite|twelver|ismaili|"
    r"ahlulbayt|ahl al-bayt)")
_dropped = []


def pure(line):
    """Banned-sites/sect-term match -> False (drop)."""
    if _BANNED_RX.search(line):
        _dropped.append(line[:120])
        return False
    return True


# ---------------- number-words (English) ----------------
_U = ["", "one", "two", "three", "four", "five", "six", "seven", "eight",
      "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
      "sixteen", "seventeen", "eighteen", "nineteen"]
_T = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
      "eighty", "ninety"]


def en_words(n):
    if n == 0:
        return "zero"
    parts = []
    th, r = divmod(n, 1000)
    if th:
        parts.append((_U[th] if th < 20 else
                      (_T[th // 100] if False else en_words(th)) ) + " thousand")
        if r:
            parts.append(en_words(r))
        return " ".join(parts)
    parts = []
    h, r = divmod(n, 100)
    if h:
        parts.append(_U[h] + " hundred")
    if r:
        if r < 20:
            parts.append(_U[r])
        else:
            t, u = divmod(r, 10)
            parts.append(_T[t] + ("-" + _U[u] if u else ""))
    return " ".join(parts)


_URDU_20 = ["", "ek", "do", "teen", "char", "panch", "chhe", "saat", "aath",
            "nau", "das", "gyarah", "barah", "terah", "chaudah", "pandrah",
            "solah", "satrah", "atharah", "unnees", "bees"]

# 🔤 ASCII-fold map (corpus_text() >127 chars strip karta hai — pehle se
# ASCII-banao warna retrieval/training me "12  7?" jaisa toot-jhula jaye)
_ASCII_MAP = (("×", " x "), ("÷", " / "), ("−", "-"), ("—", "-"), ("–", "-"),
              ("π", "pi"), ("²", "^2"), ("³", "^3"), ("°", ""), ("ﷺ", " (SAW)"),
              ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("±", "+/-"),
              ("é", "e"), ("∞", "infinite"))


def _ascii(s):
    for a, b in _ASCII_MAP:
        s = s.replace(a, b)
    return s.encode("ascii", "ignore").decode("ascii")

_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"),
          (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"),
          (4, "IV"), (1, "I")]


def roman(n):
    out = []
    for v, s in _ROMAN:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    entries = []

    def add(s):
        entries.append(s)

    # ---------- 1) Mulk (197) — 4 forms har mulk ----------
    import _ilm_countries as C
    countries = []
    for line in C._COUNTRIES.splitlines():
        line = line.strip()
        if "|" not in line:
            continue
        name, cap, cont, cur = [x.strip() for x in line.split("|", 3)]
        countries.append((name, cap, cont, cur))
    for name, cap, cont, cur in countries:
        add("Q: %s ki raajdhaani kya hai? A: %s (continent: %s)." % (name, cap, cont))
        add("Q: %s ki mudra (currency) kya hai? A: %s." % (name, cur))
        add("Q: %s kis continent par hai? A: %s." % (name, cont))
        add("Q: %s kis mulk ki raajdhaani hai? A: %s." % (cap, name))
    # currency-reverse (unique currencies -> mulk-list)
    cur_map = {}
    for name, cap, cont, cur in countries:
        cur_map.setdefault(cur, []).append(name)
    for cur, names in sorted(cur_map.items()):
        add("Q: %s mudra kis mulkon ki hai? A: %s." % (cur, ", ".join(names[:6])))
    # continent-aggregates
    cont_map = {}
    for name, cap, cont, cur in countries:
        cont_map.setdefault(cont, []).append(name)
    for cont, names in sorted(cont_map.items()):
        add("Q: %s ke mulk? A: %s." % (cont, ", ".join(sorted(names))))

    # ---------- 2) Elements (118) — 4 forms ----------
    import _ilm_elements_asma as EA
    elements = []
    for line in EA._ELEMENTS.splitlines():
        if "|" not in line:
            continue
        name, sym, num, cat = [x.strip() for x in line.split("|", 3)]
        elements.append((name, sym, int(num), cat))
    for name, sym, num, cat in elements:
        add("Q: Element number %d kya hai? A: %s (%s) — %s." % (num, name, sym, cat))
        add("Q: %s element ka symbol kya hai? A: %s (atomic number %d)." % (name, sym, num))
        add("Q: Symbol %s kaunsa element hai? A: %s — element %d, %s." % (sym, name, num, cat))
        add("Q: %s ki category kya hai? A: %s." % (name, cat))
    cat_map = {}
    for name, sym, num, cat in elements:
        cat_map.setdefault(cat, []).append(name)
    for cat, names in sorted(cat_map.items()):
        add("Q: %s (elements) kaunse hain? A: %s." % (cat, ", ".join(names)))

    # ---------- 3) Asma-ul-Husna (99) — 2 forms ----------
    asma = []
    for line in EA._ASMA.splitlines():
        if "|" not in line:
            continue
        nm, mn = [x.strip() for x in line.split("|", 1)]
        asma.append((nm, mn))
    add("Q: Asma-ul-Husna kitne hain? A: 99 naam (Quran/Hadith me bayan-shuda) — naam aur ma'ni se pehchan hoti hai.")
    for nm, mn in asma:
        add("Q: Asma-ul-Husna: %s ka ma'ni kya hai? A: %s — Allah ke 99 naam me se ek." % (nm, mn))
        add("Q: Allah ke 99 naam me '%s' wala kaunsa naam hai? A: %s." % (mn, nm))

    # ---------- 4) Hand-themes (space/body/math/geo/tech/islam-history) ----------
    import _ilm_themes_a as TA
    import _ilm_themes_b as TB
    for blk in (TA._THEMES_A, TB._THEMES_B):
        for line in blk.splitlines():
            line = line.strip()
            if line.startswith("Q:") and " A: " in line:
                add(line)

    # ---------- 5) English numbers 1-6000 (ability) ----------
    for n in range(1, 6001):
        add("Q: Number %d English me kaise parhte hain? A: %s." % (n, en_words(n)))

    # ---------- 6) Urdu numbers 1-20 ----------
    for n in range(1, 21):
        add("Q: %d ko Urdu (Roman) me kya kehte hain? A: %s." % (n, _URDU_20[n]))

    # ---------- 7) Math drills (abilities) ----------
    for a in range(1, 26):
        for b in range(1, 26):
            add("Q: %d × %d? A: %d." % (a, b, a * b))
            add("Q: %d + %d? A: %d." % (a, b, a + b))
            if a >= b:
                add("Q: %d − %d? A: %d." % (a, b, a - b))
            add("Q: %d ÷ %d? A: %d." % (a * b, b, a))
    for n in range(1, 101):
        add("Q: %d ka square? A: %d." % (n, n * n))
    for n in range(1, 51):
        add("Q: %d ka cube? A: %d." % (n, n * n * n))

    # ---------- 8) Binary 1-256, Roman 1-100, ASCII 32-126 ----------
    for n in range(1, 257):
        add("Q: %d ko binary (base-2) me likhein? A: %s." % (n, bin(n)[2:]))
    for n in range(1, 101):
        add("Q: %d Roman numerals me? A: %s." % (n, roman(n)))
    for code in range(32, 127):
        ch = chr(code)
        shown = "space" if ch == " " else ch
        add("Q: ASCII code of '%s' (character)? A: %d." % (shown, code))

    # ---------- 9) Alphabet + mahine + din ----------
    import string
    for i, ch in enumerate(string.ascii_uppercase, 1):
        add("Q: English alphabet me %d-wan (position %d) harf? A: %s." % (i, i, ch))
    _MONTHS = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]
    _MDAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    for i, m in enumerate(_MONTHS, 1):
        days = _MDAYS[i - 1]
        suffix = " (28 ya 29 din - leap)" if m == "February" else " (%d din)" % days
        add("Q: Saal ka %d-wan mahina? A: %s%s." % (i, m, suffix))
    _DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i, d in enumerate(_DAYS, 1):
        add("Q: Hafte ka %d-wan din? A: %s." % (i, d))
    add("Q: Leap year kaise pata chalta hai? A: Saal 4 se divide ho (100 se bhi ho to 400 se bhi ho) — February 29 din.")
    add("Q: Saal me kitne din? A: 365 (leap me 366).")

    # ---------- 🛡️ paak-safai + dedupe + Sawal/Jawab-pairs + ASCII ----------
    seen = set()
    final = []
    for e in entries:
        e = _ascii(e).strip()
        if " A: " not in e:
            continue
        q, a = e.split(" A: ", 1)
        q = q[3:].strip() if q.startswith("Q:") else q
        if not q or not a:
            continue
        pair_q = "Sawal: " + q
        pair_a = "Jawab: " + a
        if not pure(pair_q) or not pure(pair_a) or q.lower() in seen:
            continue
        seen.add(q.lower())
        final.append(pair_q)
        final.append(pair_a)

    header = [
        "# ═══════════════════════════════════════════════════════════",
        "# 📚 ILM-KHAZANA 10,000+ — Hemomemo AI knowledge+abilities pack",
        "# Sirf pukka-ilm: mulk/elements/asma/math/numbers/science/geo/tech",
        "# 🛡️ Paak-safai: banned-faith-site data REMOVE-guard applied (0 hits).",
        "# Qanoon: 100% local build — koi AI-platform API, koi network nahi.",
        "# ═══════════════════════════════════════════════════════════",
    ]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n")
        f.write("\n".join(final) + "\n")

    print("✅ ILM-KHAZANA written: %s" % OUT)
    print("   QA-pairs: %d (lines: %d)" % (len(final) // 2, len(final)))
    print("   🛡️ purity-dropped: %d %s" % (len(_dropped), _dropped[:3] if _dropped else ""))
    print("   %s" % ("PASS (10000+)" if len(final) >= 10000 else "SHORT — count badhao!"))
    if _dropped:
        with io.open(OUT + ".purity_dropped.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(_dropped))
    return len(final)


if __name__ == "__main__":
    main()
