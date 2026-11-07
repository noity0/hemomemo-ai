"""HEMOMO TOKENIZER - Hemomemo AI ka apna token-system (100% local).

Qanoon: "har lafz token mein tute, dimagh token-dar-token parhe aur soche."

Kya karta hai:
  - normalize(): input ko saaf (Roman-Urdu + English dono)
  - word_tokens(): lafz-tokens
  - sub_tokens(): har lafz ke tukde (kanne/narm tukmat) - mushabih lafz pakarna
  - key_tokens(): matlab-wale lafz (ke/ki/ka/ka the/ka the hata kar)
  - bigrams(): do-lafz jore ("who is", "kya hai", "kaun hai")
  - qword(): sawal-lafz (who/what/kya/kaun/kaise/kab/kahan/kitna/kyun)
  - numbers(): digits + "r = 5" jaise maan (variable)
  - understand(): poora parhna - dimagh ke liye tayyar samajh

Koi bahar-ki cheez nahi - sirf Hemomemo ke apne niyam. Koi API nahi.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple

# ---- sawal-lafz (sawal pehchanne ke) ----
_QWORDS = ("who", "what", "why", "when", "where", "how", "which", "whom",
           "kya", "kaun", "kaunsa", "kaise", "kab", "kahan", "kitna", "kitni",
           "kitne", "kyun", "kyunke", "kon", "kyu", "kabhi", "kahan-hai")

# ---- matlab-khali lafz (yeh tokens soch nahi badalte) ----
_STOP = {
    "the", "a", "an", "is", "are", "am", "was", "were", "of", "to", "in", "on",
    "at", "for", "and", "or", "but", "so", "if", "then", "else", "do", "does",
    "did", "done", "ka", "ke", "ki", "ko", "kse", "se", "me", "mein", "par",
    "hai", "hain", "ho", "hoon", "hun", "tha", "thi", "the", "hota", "hoti",
    "karte", "karna", "kar", "karo", "batao", "bata", "likho", "karo",
    "please", "pls", "muje", "mujhe", "mera", "meri", "apna", "apni", "tum",
    "tumhara", "tumhari", "aap", "aapka", "aapki", "kya", "baare", "baray",
}

# ---- pehchaan: domain-signals (token-level) ----
_MATH_SIG = ("+", "-", "*", "/", "=", "^", "(", ")", "%", "sq", "area",
             "perimeter", "mohit", "masahat", "circle", "daira", "energy",
             "hisab", "calculate", "solve")
_CODE_SIG = ("python", "javascript", "java", "kotlin", "c++", "cpp", "sql",
             "html", "css", "bash", "rust", "golang", "php", "ruby", "code",
             "function", "class", "loop", "array", "list", "variable",
             "compile", "syntax", "error", "bug", "script", "program")
_GAME_SIG = ("minecraft", "creeper", "enderman", "nether", "end", "redstone",
             "biome", "mob", "spawn", "server", "game", "player", "roblox",
             "fortnite", "pokemon", "chess", "ludo", "speedrun", "mod",
             "skin", "block", "craft")
_ISLAMIC_SIG = ("allah", "quran", "namaz", "salah", "roza", "sawm", "zakat",
                "hajj", "umrah", "wudu", "ghusl", "hadith", "sunnah", "dua",
                "ramadan", "eid", "tawheed", "sabr", "shukr", "hijab",
                "halal", "haram", "surah", "ayat", "iman", "islam")
_MEMORY_SIG = ("yaad", "rakho", "rakhna", "naam", "mera", "name", "remember",
               "save", "mahfooz")

_WORD_RX = re.compile(r"[a-z0-9\u0600-\u06FF\u0C00-\u0C7F]+", re.UNICODE)
_NUM_RX = re.compile(r"(-?\d+(?:\.\d+)?)")

# formula-var pakadna: "r = 5", "m=2", "r 5"
_VAR_RX = re.compile(r"([a-zA-Z])\s*(?:=|hoga|hai|:)\s*(-?\d+(?:\.\d+)?)")


def normalize(text: str) -> str:
    """Input ko dimagh-ke-laiq saaf shakal (chhota + khan-dar)."""
    t = (text or "").strip().lower()
    t = t.replace("’", "'").replace("`", "'")
    return t


def word_tokens(text: str) -> List[str]:
    """Har lafz ek token (naam/adad dono)."""
    return _WORD_RX.findall(normalize(text))


def key_tokens(text: str) -> List[str]:
    """Sirf matlab-wale tokens (khali-lafz nikal kar)."""
    return [t for t in word_tokens(text) if t not in _STOP]


def bigrams(text: str) -> List[Tuple[str, str]]:
    """Do-lafz ke jore - 'who is' / 'kya hai' jaisa soch."""
    ts = word_tokens(text)
    return [(ts[i], ts[i + 1]) for i in range(len(ts) - 1)]


def sub_tokens(word: str, n: int = 3) -> List[str]:
    """Lafz ke chhote tukde (n-gram) - mushabih/adhure lafz bhi pakde.
    'circel' ~ 'circle' - tukde milte hain (fuzzy-dimagh)."""
    w = (word or "").strip()
    if len(w) <= n:
        return [w] if w else []
    return [w[i:i + n] for i in range(len(w) - n + 1)]


def qword(text: str) -> str:
    """Sawal-lafz mojood? -> wahi lafz, warna ''."""
    ts = set(word_tokens(text))
    bg = set(bigrams(text))
    for q in _QWORDS:
        if q in ts:
            return q
    for a, b in bg:
        if (a, b) in {("who", "is"), ("what", "is"), ("kya", "hai"),
                      ("kaun", "hai"), ("kya", "hai")}:
            return a + " " + b
    return ""


def numbers(text: str) -> List[float]:
    """Input ke saare adad (math-soch ke liye)."""
    return [float(x) for x in _NUM_RX.findall(text or "")]


def vars_of(text: str) -> dict:
    """"r = 5" jaise maan nikalo -> {'r': 5.0} (formula-soch ke liye)."""
    out = {}
    for k, v in _VAR_RX.findall(text or ""):
        try:
            out[k.lower()] = float(v)
        except ValueError:
            continue
    return out


@dataclass
class Understanding:
    """Dimagh ka parha-hua natija - ek sawal ka poora token-naksha."""
    text: str = ""
    tokens: List[str] = field(default_factory=list)
    keys: List[str] = field(default_factory=list)
    bigrams: List[Tuple[str, str]] = field(default_factory=list)
    qw: str = ""
    nums: List[float] = field(default_factory=list)
    variables: dict = field(default_factory=dict)
    intents: List[str] = field(default_factory=list)  # token-votes
    lang: str = "roman"   # roman | english | mix
    domain: str = "general"


def domain_votes(text: str) -> List[Tuple[str, int]]:
    """Har domain ko token-votes (kitne tokens us domain ki baat karte)."""
    ts = word_tokens(text)
    votes = {"math": 0, "coding": 0, "game": 0, "islamic": 0, "memory": 0}
    for t in ts:
        if t in _MATH_SIG:
            votes["math"] += 1
        if t in _CODE_SIG:
            votes["coding"] += 1
        if t in _GAME_SIG:
            votes["game"] += 1
        if t in _ISLAMIC_SIG:
            votes["islamic"] += 1
        if t in _MEMORY_SIG:
            votes["memory"] += 1
    return [(k, v) for k, v in votes.items() if v > 0]


def understand(text: str) -> Understanding:
    """POORA PARHNA: input -> token-naksha (dimagh isi se sochta hai)."""
    u = Understanding(text=(text or "").strip())
    u.tokens = word_tokens(text)
    u.keys = key_tokens(text)
    u.bigrams = bigrams(text)
    u.qw = qword(text)
    u.nums = numbers(text)
    u.variables = vars_of(text)
    u.intents = domain_votes(text)
    eng = sum(1 for t in u.tokens if t in
              {"what", "who", "how", "why", "the", "is", "are", "you",
               "your", "name", "give", "tell", "write", "make"})
    rom = sum(1 for t in u.tokens if t in
              {"kya", "kaun", "kaise", "hai", "hain", "batao", "mera",
               "karo", "likho", "aap", "tum"})
    if eng and not rom:
        u.lang = "english"
    elif eng and rom:
        u.lang = "mix"
    return u
