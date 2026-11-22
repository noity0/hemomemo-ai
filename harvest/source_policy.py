"""
🛡️ source_policy.py — SACRED-TEXT SAFETY GUARD (Qadiani-current WITHOUT)

Sakht qawaid (koi tabdeeli nahi):
  1. Sirf yehen whitelisted hosts se data aata hai (raw.githubusercontent.com,
     cdn.jsdelivr.net) — sunnah.com + tanzil se aage standard datasets
  2. Yeh words/texts kisi bhi file me ho to install MANA hota hai:
     Ahmadiyya / Qadiani / Mirza Ghulam / alislam.org / aaiil.org
  3. Qadiani fraqay ke translators (Muhammad Ali (Lahore), Sher Ali,
     Umm Muhammad, Rashad Khalifa) wale editions bhi MANA hain
  4. Quran ko sirf PARHNA hai — kabhi edit nahi (knowledge/quran_guard.py dekhein)

Yeh module install_sacred_texts.py aur harvester (dono) istemal karte hain.
"""

import os
import re

# ✅ Whitelisted hosts — siwaaye in ke data aana hota to MANA
ALLOWED_HOSTS = (
    "raw.githubusercontent.com",
    "cdn.jsdelivr.net",
)

# ❌ Ban host/domain black-list (Qadiani + sifeh (deviant)fraqa sites)
BANNED_HOSTS = (
    "alislam.org",
    "aaiil.org",
    "ahmadiyyat",
    "khatam-e-nubuwwat-ke dushman",
    "qadian",
)

# ❌ In ke naam wale translator/edition MANA hain (Qadiani/Rashad Khalifa fiqaat)
BANNED_AUTHOR_RX = re.compile(
    r"(?i)(maulana\s+)?muhammad\s+ali\b(?!\s+khan)"   # Lahore Ahmadi translator
    r"|(?<!\w)sher\s+ali(?!\w)"                       # Qadiani translator
    r"|(?<!\w)umm(u)?\s*muhammad(?!\w)"               # Ahmadi edition (see README)
    r"|(?<!\w)ahmadi(?!\w)"
    r"|(?<!\w)ahmadiyya(?!\w)"
    r"|(?<!\w)qadiani?(?!\w)"
    r"|(?<!\w)rashad\s+khalifa(?!\w)"
    r"|mirza\s+ghulam"
)

# ❌ Text me bhi ban words scan hote hain — ho to skip + report
FORBIDDEN_RX = re.compile(
    r"(?i)ahmadiyya|(?<!\w)qadiani?(?!\w)|mirza\s+ghulam|alislam\.org|aaiil\.org"
)


def host_allowed(url: str) -> bool:
    """Kya URL whitelisted host ka hai?"""
    low = url.lower()
    if any(b in low for b in BANNED_HOSTS):
        return False
    return any(h in low for h in ALLOWED_HOSTS)


def text_forbidden(text: str):
    """Ban word mile to match-object wapas (warna None)."""
    if not text:
        return None
    m = FORBIDDEN_RX.search(text)
    return m


def author_forbidden(author: str) -> bool:
    """Translator ka naam forbidden to True."""
    return bool(author and BANNED_AUTHOR_RX.search(author))


def assert_clean(text: str) -> str:
    """Text me ban word mila to Exception (install script me skip hota hai)."""
    m = text_forbidden(text)
    if m:
        raise ValueError("FORBIDDEN source content: %s" % m.group(0))
    return text


def scan_files(folder: str, ext: str = ".json") -> dict:
    """Ek folder ke tamam files me forbidden words scan karo.
    Report: {'scanned': n, 'hits': {file: match}, 'bytes': total}"""
    scanned, hits, total = 0, {}, 0
    if not os.path.isdir(folder):
        return {"scanned": 0, "hits": {}, "bytes": 0}
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(ext):
            continue
        p = os.path.join(folder, fn)
        try:
            total += os.path.getsize(p)
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                m = text_forbidden(f.read())
            scanned += 1
            if m:
                hits[fn] = m.group(0)
        except OSError:
            pass
    return {"scanned": scanned, "hits": hits, "bytes": total}
