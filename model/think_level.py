"""
🪜 think_level.py — ADAPTIVE THINKING LEVELS (auto / low / mid / high)

Qanoon (user ne set kiya):
  1. DEFAULT tier = LOW (chhoti/normal baat → fast jawab, zyada soch nahi)
  2. MODE = AUTO (default): sawal ki tafliqa dekh kar tier khud chunta hai
     - low: chhota sawal / salam / haan-nahin / simple yaad-milta jawab
     - mid: aam sawal ("kya hai", "batao", farq, tarika ...)
     - high: mushkil ("kyun", banane ke tareeqay, code/math/science,
       lambi chain-wali sawal)
  3. Manual override: set_mode("low"|"mid"|"high"|"auto") —
     chat me:  think auto | think low | think mid | think high
  4. TIER asar: kitna lamba soche (max_new) + kitne sampling copies
     + kitni baar rethink (metacognition ke baad dobara sochna)

State: data/think_state.json
"""
import json
import os
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
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

STATE_PATH = os.path.join(ROOT, "data", "think_state.json")
_DEFAULT = {"mode": "auto", "manual_tier": None, "updated": None}

# tier kaaji: kitna sochna hai (har tier ka mustaqil setup)
# 📏 OUTPUT-LIMIT upgrade (user qanoon): 10M-token ceiling tak ja sakte —
#    per-tier default barhaya gaya (SAFARI-STOP \nSawal/\nJawab/\n\n par
#    model khud rukta hai, is liye lambi limit quality nahi girati).
TIERS = {
    "low":  {"max_new": 512, "samples": 2, "rethink": 0, "desc": "turant (fast, 2 khud-soch koshish)"},
    "mid":  {"max_new": 1024, "samples": 2, "rethink": 1, "desc": "aam sawal (do soch)"},
    "high": {"max_new": 2048, "samples": 2, "rethink": 2, "desc": "gehra sochna (mushkil kaam)"},
}

# ❗ HIGH prompts (mushkil kaam)
_HIGH_RX = re.compile(
    r"(?i)\b(?:kyun|why|kaise\s+banaye|bana\s+do|banadena|bana\s+dena|"
    r"explain|wazahat|tafseel|tafheem|code|python|javascript|algorithm|"
    r"math|physics|chemistry|probability|solve|analysis|engineer|"
    r"system|architecture|r*(?:esearch)|economy|politics|"
    r"philosophy|theory|design|build|script|program)\b")
# 🔹 MID prompts (aam sawal)
_MID_RX = re.compile(
    r"(?i)\b(?:kya\s+hai|kya\s+hota|kya\s+hoti|batao|batay|faraq|farq|"
    r"difference|tarika|tareeqa|madad|help|meaning|matlab|"
    r"hadith|quran|sun|sunayiye|parh|parho|study|kam|kaam|bimari|"
    r"health|sehat|paisa|job|school|college)\b")
_LAST = {"t": 0.0, "tier": "low"}


def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            st = json.load(f)
        if not isinstance(st, dict):
            return dict(_DEFAULT)
        return {**_DEFAULT, **st}
    except Exception:
        return dict(_DEFAULT)


def save_state(st):
    try:
        st["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def get_mode():
    return load_state().get("mode", "auto")


def set_mode(mode: str):
    """auto | low | mid | high — manual tier ya auto-classify."""
    mode = (mode or "auto").lower().strip()
    if mode not in ("auto", "low", "mid", "high"):
        mode = "auto"
    st = load_state()
    st["mode"] = mode
    st["manual_tier"] = None if mode == "auto" else mode
    save_state(st)
    return st


def _norm_words(prompt):
    return re.findall(r"[a-z]{2,}", (prompt or "").lower())


def classify(prompt: str) -> str:
    """Sawal ki tafliqa se tier: low / mid / high."""
    words = _norm_words(prompt)
    n = len(words)
    text = (prompt or "").lower()
    if _HIGH_RX.search(text) or n >= 30 or text.count("?") >= 2:
        return "high"
    if _MID_RX.search(text) or n >= 13:
        return "mid"
    return "low"


def effective(prompt: str = None):
    """Auto mode → classify(prompt); manual → pakka tier (kam-se-kam low)."""
    st = load_state()
    mode = st.get("mode", "auto")
    if mode == "auto":
        tier = classify(prompt or "")
    else:
        tier = mode if mode in TIERS else "low"
    t = time.time()
    if t - _LAST["t"] > 0.9:
        _LAST["t"], _LAST["tier"] = t, tier
    return tier


def tier_cfg(tier: str):
    if tier not in TIERS:
        tier = "low"
    return TIERS[tier]


def status():
    st = load_state()
    return {"mode": st.get("mode", "auto"),
            "manual_tier": st.get("manual_tier"),
            "tiers": {k: v["desc"] for k, v in TIERS.items()}}


if __name__ == "__main__":
    for q in ("salam", "kya haal hai", "Allah kahan hai",
              "python me program kaise banaye", "namaz kya hoti hai"):
        print("%-34s -> %s" % (q, classify(q)))
