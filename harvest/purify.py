"""
🧹 purify.py — harvester ka safai karne wala module

Internet se aye text ko machine ki zuban (ASCII, Roman) me ghar bana deta hai:
 - ao na fancy harf (—, ‘, “, é, Urdu/Arabic script) → hatao ya badlo
 - sirf machine ki allowed letters bachatay hain
 - khat, tab, zaed space saaf

Yeh Quran folder ko koi zoom nahi deta — sirf nayi yaad ka kaam hai.
"""
import re

# machine ki asli 69-harf zuban + kuch aage ke letters (digits) — future train ke liye
ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
ALLOWED |= set(" \n!(),-.:?&/+'\"")   # sawal-aghar marks


# Pehle mushkil unicode ke asaan roop
_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u02bc": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00ad": "",
    "\u2026": "...", "\u00a0": " ",
    "\u061f": "?",
}


def sanitize(text: str) -> str:
    """Text ko ASCII-safe, saaf, parh-wand banata hai."""
    if not text:
        return ""
    for k, v in _REPLACEMENTS.items():
        text = text.replace(k, v)
    # sirf allowed chars (Arabic/Urdu script + baqi sab hata jayega)
    text = "".join(c if c in ALLOWED else " " for c in text)
    # kathin space aur khali qatal
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [ln.strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln).strip()


_STOP = {
    "the", "and", "for", "that", "with", "this", "from", "have", "has",
    "was", "were", "not", "are", "his", "her", "him", "who", "all",
    "one", "said", "their", "they", "will", "which", "had", "what",
    "about", "when", "you", "your", "but", "can", "may", "there",
    "been", "whoever", "any", "its", "himself", "into", "than", "them",
    "would", "she", "per", "how", "why", "who", "did", "does", "out",
}


def keywords(text: str, k: int = 5) -> str:
    """Text ke apne mahaaz-harf (keywords) — naye sawal ke liye le azan."""
    words = re.findall(r"[a-z]{4,}", text.lower())
    freq = {}
    for w in words:
        if w in _STOP:
            continue
        freq[w] = freq.get(w, 0) + 1
    best = sorted(freq.items(), key=lambda x: -x[1])[:k]
    return " ".join(w for w, _ in best)
