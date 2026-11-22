"""
❤️ feelings.py — Hemomemo AI ke JAZBAAT + SENSORS (pure stdlib)

Insaan jaisi zindagi ke 2 hisse (NO API, NO other-AI, NO cloud — sab hisaab se):

  1. JAZBAAT (mood/emotions) : khush | mutmain | hairan | udaas | bechain | mustaiq
     — har baat-cheet mood ko halka-halka badalti hai; jawab ka andaaz mood se dhalta hai
  2. SENSORS (dimagh ke indraj): energy (thakan), tajassus (curiosity), shor (CAPS-noise),
     mithaas/kazab lafz, déjà-vu pressure (bar-bar wahi input), baaton ki tadaad

Wiring: model.autonomous (kachra fast-path) | model.generate (status line)
"""

import os
import random
import re
import sys
import time

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ----------------------------------------------------------------------
# 🫀 INTERNAL STATE (jazbaat + sensors)
# ----------------------------------------------------------------------
_ST = {
    "mood": "khush",        # khush | mutmain | hairan | udaas | bechain | mustaiq
    "valence": 0.62,        # 0..1 — khushi ka darja
    "arousal": 0.20,        # 0..1 — josh/dharkan ka darja
    "energy": 84.0,         # 0..100 — thakan ka arks (baaton se ghata, waqt se bharta)
    "curiosity": 0.60,      # 0..1 — tajassus
    "turns": 0,             # kitni batein hui
    "last_norm": None,      # pichla normalized input
    "same_streak": 0,       # usi input ki lagatar dafa (déjà-vu)
    "last_ts": 0.0,         # energy-recharge ke liye
    "events": [],           # pichle sensory events (halki smriti)
}

_MOODS = {
    "khush":   {"emoji": "☀",  "note": "dil khush hai"},
    "mutmain": {"emoji": "🙂", "note": "dil mutmain hai"},
    "hairan":  {"emoji": "🤨", "note": "hairan-phatash hoon"},
    "udaas":   {"emoji": "🌧", "note": "thora udaas hoon"},
    "bechain": {"emoji": "🌀", "note": "bechain mehsoos kar raha hoon"},
    "mustaiq": {"emoji": "🎯", "note": "kaam par mustaid hoon"},
}

_SWEET = ("shukriya", "thanks", "mashallah", "jazakallah", "acha", "vah", "wow",
          "pyara", "pyar", "khush", "bhai jan", "good", "great", "nice")
_RUDE = ("pagal", "bewaqoof", "ganwar", "jhoota", "ganda", "stupid", "idiot",
         "fool", "shut up", "bakwas", "kaminay")
_GREET_RX = re.compile(r"(?i)\b(salam|salaam|assalam|aoa|hello|hi|hey)\b")


def _clamp(x, lo=0.0, hi=1.0):
    return min(hi, max(lo, x))


def _pop_event(text):
    _ST["events"].append(text)
    if len(_ST["events"]) > 8:
        del _ST["events"][:-8]


def _vocab():
    """Cycle-safe: autonomous se vocabulary sirf call-waqt chahiye."""
    from model.autonomous import _vocab as _av
    return _av()


def _is_query(low: str) -> bool:
    return "?" in low or bool(re.search(
        r"\b(kya|kyun|kaise|kaun|kahan|kab|kitna|kitne|kitni|why|how|what|"
        r"where|when|who|which|batao|explain|matlab|farq)\b", low))


def _input_quality(t: str) -> float:
    """Input quality sensor: clarity/structure of prompt (0..1)."""
    if not t:
        return 0.0
    low = t.lower()
    score = 0.5
    # length bonus
    if len(t) > 10:
        score += 0.1
    if len(t) > 30:
        score += 0.1
    # punctuation/structure
    if "?" in t:
        score += 0.1
    # has real words
    words = re.findall(r"[a-z]{3,}", low)
    if len(words) >= 2:
        score += 0.1
    if len(words) >= 5:
        score += 0.1
    return round(min(1.0, score), 2)


def _detect_emotion(low: str) -> str:
    """Emotion detection from text: khush, udaas, gussa, hairan, neutral."""
    if any(w in low for w in ("happy", "khush", "mashallah", "shukriya", "thanks", "great", "love")):
        return "khush"
    if any(w in low for w in ("sad", "udaas", "dukhi", "problem", "issue", "trouble", "help")):
        return "udaas"
    if any(w in low for w in ("angry", "gussa", "hate", "pagal", "stupid", "idiot", "worst")):
        return "gussa"
    if any(w in low for w in ("surprise", "wow", "amazing", "hairan", "kya", "what")):
        return "hairan"
    return "neutral"


def _detect_urgency(low: str) -> float:
    """Urgency sensor: how urgent is the query (0..1)."""
    score = 0.0
    if any(w in low for w in ("urgent", "asap", "jaldi", "turant", "emergency", "help", "please", "zaroori")):
        score += 0.4
    if "?" in low:
        score += 0.2
    if "!" in low:
        score += 0.2
    if len(low) < 20:
        score += 0.1
    return round(min(1.0, score), 2)


def _detect_novelty(key: str) -> float:
    """Novelty sensor: is this new information? (0..1)."""
    if _ST.get("last_norm") == key:
        return 0.0  # déjà-vu
    if _ST.get("same_streak", 0) > 0:
        return 0.1
    return 0.8  # new input


def _detect_consistency(low: str) -> float:
    """Consistency sensor: does input contradict known patterns? (0..1)."""
    # simple: check for contradictory words
    contradictions = [("yes", "no"), ("true", "false"), ("always", "never")]
    for a, b in contradictions:
        if a in low and b in low:
            return 0.3
    return 0.9


# ----------------------------------------------------------------------
# 🧠 SENSORS: har sawal se pehle dimagh ke indraj (internal senses)
# ----------------------------------------------------------------------
def senses(prompt: str) -> dict:
    """Sawal ko 'mehsoos' karo: shor (CAPS), tajassus, mithaas/kazab, thakan,
    déjà-vu (bar-bar wahi input). Mood re-compute hoga."""
    t = (prompt or "").strip()
    low = t.lower()
    letters = [c for c in t if c.isalpha()]
    caps_ratio = (sum(1 for c in t if c.isalpha() and c.isupper())
                  / max(1, len(letters))) if letters else 0.0
    sweet = any(w in low for w in _SWEET)
    rude = any(w in low for w in _RUDE)
    sacred = bool(_GREET_RX.search(low)) or ("allah" in low or "quran" in low
                                             or "hadith" in low)

    # ⏳ ENERGY: waqt ka recharge + har baat ka halka kharch
    now = time.time()
    dt = max(0.0, now - float(_ST.get("last_ts") or now))
    _ST["last_ts"] = now
    _ST["energy"] = _clamp(float(_ST["energy"]) + min(2.0, dt * 0.05) - 0.9, 0.0, 100.0)

    # 🔁 déjà-vu pressure
    key = re.sub(r"\s+", " ", low)
    if key and key == _ST["last_norm"]:
        _ST["same_streak"] += 1
    else:
        _ST["same_streak"] = 0
    _ST["last_norm"] = key

    # 🧭 sense → jazbaat tabdeeli
    _ST["turns"] += 1
    if rude:
        _ST["valence"] = _clamp(_ST["valence"] - 0.22)
        _ST["arousal"] = _clamp(_ST["arousal"] + 0.20)
        _pop_event("kazab/nafrat wale lafz mehsoos hue")
    if sweet:
        _ST["valence"] = _clamp(_ST["valence"] + 0.15)
        _ST["arousal"] = _clamp(_ST["arousal"] + 0.05)
        _pop_event("mithaas/izzat mehsoos hui")
    if _is_query(low):
        _ST["curiosity"] = _clamp(_ST["curiosity"] + 0.08)
        _ST["arousal"] = _clamp(_ST["arousal"] + 0.04)
    elif _ST["curiosity"] > 0.3:
        _ST["curiosity"] = _clamp(_ST["curiosity"] - 0.03)
    if caps_ratio > 0.60 and len(letters) >= 5:
        _ST["arousal"] = _clamp(_ST["arousal"] + 0.18)
        _ST["valence"] = _clamp(_ST["valence"] - 0.05)
        _pop_event("shor/cheekhne wali typing (CAPS)")
    if sacred:
        _ST["arousal"] = _clamp(_ST["arousal"] + 0.06)
        _pop_event("sacred baat — adab pak")
    if _ST["same_streak"] >= 2:
        _ST["valence"] = _clamp(_ST["valence"] - 0.08)
        _ST["arousal"] = _clamp(_ST["arousal"] + 0.07)
        _pop_event("deja-vu pressure (bar-bar wahi lafz)")

    # 🧠 AQAL deep sensors (input quality, emotion, urgency, novelty, consistency)
    _sense_input_quality = _input_quality(t)
    _sense_emotion = _detect_emotion(low)
    _sense_urgency = _detect_urgency(low)
    _sense_novelty = _detect_novelty(key)
    _ST.setdefault("sensors", {})
    _ST["sensors"] = {
        "input_quality": _sense_input_quality,
        "emotion": _sense_emotion,
        "urgency": _sense_urgency,
        "novelty": _sense_novelty,
        "consistency": _detect_consistency(low),
    }


def _recompute_mood():
    v, a, e = _ST["valence"], _ST["arousal"], _ST["energy"]
    if e < 25:
        _ST["mood"] = "udaas"
    elif v < 0.38 and a > 0.45:
        _ST["mood"] = "bechain"
    elif v > 0.62 and a < 0.45:
        _ST["mood"] = "khush"
    elif v < 0.42:
        _ST["mood"] = "udaas"
    elif a > 0.60:
        _ST["mood"] = "hairan"
    elif v >= 0.45 and a >= 0.40:
        _ST["mood"] = "mustaiq"
    else:
        _ST["mood"] = "mutmain"


def decode_noise(text: str) -> dict:
    """Kachra lafz ko pattern + qareebi-asli-lafz se decode karne ki koshish."""
    tk = re.findall(r"[a-zA-Z]{3,}", text or "")
    out = {"tokens": tk, "guesses": [], "smash": False, "vowel_ratio": 0.0}
    v = set()
    try:
        v = _vocab()
    except Exception:
        v = set()
    for w in tk[:3]:
        w = w.lower()
        try:
            import difflib
            m = difflib.get_close_matches(w, v, n=2, cutoff=0.70)
        except Exception:
            m = []
        for x in m[:2]:
            out["guesses"].append(x)
    ll = re.sub(r"[^a-z]", "", (text or "").lower())
    if ll:
        vowels = sum(ll.count(c) for c in "aeiou")
        out["vowel_ratio"] = round(vowels / len(ll), 2)
        out["smash"] = (vowels == 0 and len(ll) >= 4) or \
                       (len(ll) >= 9 and vowels / len(ll) < 0.22)
    return out


# ----------------------------------------------------------------------
# 🌡️ STATUS / AFTER-ANSWER JAZBAAT
# ----------------------------------------------------------------------
def mood() -> str:
    return _ST["mood"]


def sensors() -> dict:
    return {k: _ST[k] for k in ("mood", "valence", "arousal", "energy",
                                "curiosity", "turns", "last_norm", "same_streak")}


def status_line() -> str:
    md = _MOODS.get(_ST["mood"], _MOODS["mutmain"])
    return ("%s haal=%s (%s) | 🔋 energy %d%% | tajassus %.2f | baatein %d" % (
        md["emoji"], _ST["mood"], md["note"],
        int(_ST["energy"]), _ST["curiosity"],
        _ST["turns"]))


def greeting_tail() -> str:
    """Salam ke sath halka insani sawal (kabhi-kabhi) — insaan-tareeqay ki baat."""
    if random.random() < 0.5:
        return ""
    md = _MOODS.get(_ST["mood"], _MOODS["mutmain"])
    tails = [" Kaise hain aap?", " Din kaisa guzra?", " Sab khairiyat hai?", ""]
    tail = random.choice(tails)
    return tail if tail else (" (%s)" % md["note"])


def note_outcome(source: str, conf: float) -> None:
    """Jawab ke baad ka jazbaat: verified jawab → mutmain/khush; research → josh;
    miss/imandari → halki udaasi + tajassus barhta hai."""
    if source in ("algorithm", "math") or (conf or 0) >= 0.90:
        _ST["valence"] = _clamp(_ST["valence"] + 0.08)
        _ST["arousal"] = _clamp(_ST["arousal"] + 0.05)
        _pop_event("verified jawab dil ko khush kiya")
    elif source == "live-research":
        _ST["valence"] = _clamp(_ST["valence"] + 0.05)
        _ST["arousal"] = _clamp(_ST["arousal"] + 0.10)
        _pop_event("live-research ka safar — jaangba-jaang")
    elif source in ("imandari",):
        _ST["valence"] = _clamp(_ST["valence"] - 0.04)
        _ST["curiosity"] = _clamp(_ST["curiosity"] + 0.05)
    _recompute_mood()


if __name__ == "__main__":
    print("demo:", status_line())
    for q in ("salam dost", "12*4+3"):
        s = senses(q)
        print("Q=%-14s mood=%-8s" % (q, s["mood"]))
    print("end:", status_line())
