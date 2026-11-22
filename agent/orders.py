"""HEMOMO ORDERS - bot ke hukum ka dimagh (100% local, koi API nahi).

User-qanoon: "banda EXE se order de + Minecraft chat se bhi de."

Har hukum token-dar-token parha jata hai (model.tokenize) -> ek pakka
KADAM nikalta hai:
  aage / peeche / baen / daen / jump / ruk / hal(aankhein) / ghum / chat / khatam

Jhoot-maari nahi: jo hukum samajh na aaye wo 'unknown' bataya jata hai -
bananda-kadam NahiN. Yehi parser EXE-console AUR Minecraft-chat dono
jagah chalta hai (ek hi dimagh, dono raste).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from model import tokenize as tk

# --- hukum-shinakht: har kadam ke lafz (Roman-Urdu + English dono) ---
_ORDER_WORDS = {
    "aage":   {"chal", "aage", "aagay", "walk", "forward", "go", "chalo",
               "jao", "aao"},
    "peeche": {"peeche", "piche", "back", "backward", "peehey", "hatto"},
    "baen":   {"baen", "bain", "left", "bayen"},
    "daen":   {"daen", "dayen", "right", "dahina"},
    "jump":   {"jump", "chalang", "chhalang", "ud", "uud", "kood"},
    "ruk":    {"ruk", "ruko", "stop", "khara", "khare", "stand", "bas",
               "rukja", "rukjao"},
    "hal":    {"hal", "dekho", "dekh", "see", "aankh", "aankhein", "eyes",
               "kahan", "where", "position", "jagah", "report"},
    "ghum":   {"ghum", "ghumao", "look", "turn", "mudo", "mudo", "face"},
    "khatam": {"khatam", "quit", "exit", "nikal", "leave", "chhodo", "bye",
               "alvida"},
}

# pehli-kadam wale (hukum pehle - warna dimagh chat samajhta)
# NOTE: baen/daen ghum se PEHLE - "baen mudo" (ghumao-baen) mein dararaf
# (direction) ghoomna se pehle aata hai ("ghum" akeLA ho tab hi ghum).
_PRIORITY = ("ruk", "khatam", "hal", "jump", "baen", "daen",
             "peeche", "aage", "ghum")


@dataclass
class Order:
    action: str = "unknown"          # upar wale ya "chat" / "unknown"
    raw: str = ""
    tokens: List[str] = field(default_factory=list)
    angle: Optional[float] = None     # "ghum 180" jaisa
    meters: Optional[float] = None    # "chal 5" jaisa


def parse(text: str) -> Order:
    """Hukum parho -> pakka kadam (token-dar-token)."""
    o = Order(raw=(text or "").strip())
    o.tokens = tk.word_tokens(text)
    if not o.tokens:
        return o
    tset = set(o.tokens)
    # pehle khaas-hukum (ruk/khatam hamesha pehle - hifazat)
    for act in _PRIORITY:
        if tset & _ORDER_WORDS[act]:
            o.action = act
            break
    # koi hukum-lafz nahi -> yeh aam-baat hai -> dimagh se jawab (chat)
    if o.action == "unknown":
        o.action = "chat"
    # aurguments: pahla adad (darjy / meter)
    nums = tk.numbers(text)
    if o.action == "ghum" and nums:
        o.angle = nums[0] % 360.0
    if o.action in ("aage", "peeche") and nums:
        o.meters = max(0.5, min(20.0, nums[0]))   # imandari-hadd 20m
    return o


def describe(o: Order) -> str:
    """Hukum ka insani-hisab (console/log ke liye)."""
    if o.action == "unknown":
        return "hukum samajh nahi aaya: %s" % o.raw[:60]
    extra = ""
    if o.angle is not None:
        extra += " (%.0f darjy)" % o.angle
    if o.meters is not None:
        extra += " (%.1f meter)" % o.meters
    return "hukum: %s%s" % (o.action, extra)
