"""
◈ cognition.py — FUTURISTIC THINKING-FLOW (DigitalBrain ka COGNITION PIPELINE)

Har sawal ab ek NAA-CHANGE MACHINE-FLOW me chalta hai (koi API nahi, koi
doosra AI nahi — sirf yehi NumPy dimagh):

   📥 READ-TOKEN → 🔢 CONVERT-TO-BINARY → 🤖 READ-BY-AI → 💭 THINK → 🧠 REASONING →
                  🔎 THINK-RESEARCH(need-if) → 🔄 THINK-CONVERT → 💭 THINK →
                  🌐 RESEARCH → 💭 THINK → 🔄 CONVERT-BINARY-TO-TEXT → ✍️ ANSWER →
                  📖 READ-AGAIN → 🧬 LEARN


Ye module flow ko TENDER karta hai: har phase ka waqt + chhota sa HUD-port
(chat me dikhaye ga) — aur agar chat me user likh de `flow on/off/auto` to
display change hota hai (default: on, compact).

QA: python -c "from model import cognition; print(cognition.status())"
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

STATE_PATH = os.path.join(ROOT, "data", "flow_state.json")

# ✨ FLOW PHASES — order machine-fan (read-only documentation + HUD label)
# USER-FLOW (user qanoon):
#   READ-TOKEN → CONVERT-TO-BINARY → READ-BY-AI → THINK → REASONING →
#   THINK-RESEARCH(need-if) → THINK-CONVERT → THINK → RESEARCH → THINK →
#   CONVERT-BINARY-TO-TEXT → ANSWER → READ-AGAIN → LEARN
PHASES = ["READ-TOKEN", "CONVERT-TO-BINARY", "READ-BY-AI", "THINK", "REASONING",
          "THINK-RESEARCH", "THINK-CONVERT", "RESEARCH", "THINK",
          "CONVERT-BINARY-TO-TEXT", "ANSWER", "READ-AGAIN", "LEARN"]
_PHASE_GLYPH = {
    "READ-TOKEN": "📥", "CONVERT-TO-BINARY": "🔢", "READ-BY-AI": "🤖",
    "THINK": "💭", "REASONING": "🧠", "THINK-RESEARCH": "🔎",
    "THINK-CONVERT": "🔄", "RESEARCH": "🌐",
    "CONVERT-BINARY-TO-TEXT": "🔄", "ANSWER": "✍️",
    "READ-AGAIN": "📖", "LEARN": "🧬",
}
# legacy aliases (purani stage naam - same phase ka purana label)
_LEGACY_GLYPHS = {
    "READ": "📥", "THINK-TOKENS": "💭", "SYSTEM": "⬇️",
    "THINK": "💭", "ANALYZE": "🧠", "RESEARCH": "🌐",
    "VERIFY": "🧾", "TOKENS-TO-TEXT": "🔄", "ANSWER": "✍️",
}
_PHASE_GLYPH.update(_LEGACY_GLYPHS)

# sawal-kisim ke pehchan (READ phase ka intent-scan)
_Q_RX = re.compile(r"(?i)(\?|\b(kya|kyun|kaise|kaisay|kaun|kahan|kab|kitna|"
                   r"kitne|kitni|why|how|what|where|when|who|whose|which)\b)")
_QM_RX = re.compile(r"(?i)(\b(batao|bata|bt|sunao|dasht|explain|wazahat|do)\b)")


class FlowTracker:
    """Ek sawal ka flow-clock: har phase jeetna + HUD-line banati hai."""

    def __init__(self):
        self.t0 = time.time()
        self.marks = []               # [(phase, dt_seconds, note)]

    def stage(self, name: str, note: str = "") -> None:
        now = time.time()
        dt = now - self.t0
        self.t0 = now
        self.marks.append((name, dt, note))

    def timed(self, name: str, seconds: float, note: str = "") -> None:
        """Meant-time ka phase (haqeeqi waqt jo us call ne liya)."""
        self.marks.append((name, max(0.0, seconds), note))
        self.t0 = time.time()

    def skip(self, name: str, note: str = "") -> None:
        """Phase chala HI NAHI (need nahi pari) — HUD me '×' dikhta hai."""
        self.marks.append((name, -1.0, note or "need nahi"))

    def line(self, verbose: bool = False) -> str:
        """⇄ 📥READ 0.02s 🧭FOCUS <0.01s 📚RECALL 0.46s 🌐RESEARCH× ⚙️THINK 0.44s"""
        out = []
        for name, dt, note in self.marks:
            g = _PHASE_GLYPH.get(name, "◈")
            if dt < 0.0:                                  # skip-ka saani ()
                out.append("%s×" % name)
            elif dt < 0.005:
                out.append("%s%s <0.01s" % (g, name))
            else:
                out.append("%s%s %.2fs" % (g, name, dt))
            if verbose and note:
                out[-1] += " (%s)" % note
        return "⇄ " + " ".join(out) if out else ""

    def called(self, name: str) -> bool:
        for n, _, _ in self.marks:
            if n == name and self._dt(n) > 0:
                return True
        return False

    def _dt(self, name):
        for n, dt, _ in self.marks:
            if n == name:
                return dt
        return 0.0

    def total(self) -> float:
        return sum(dt for _, dt, _ in self.marks)


# ----------------------------------------------------------------------
# READ phase: asli samajh (sirf regex/words — NO API)
# ----------------------------------------------------------------------
def read_intent(prompt: str) -> dict:
    """Sawal ka fingerprint: type, topic-words, sawal-hai-ya-baat."""
    text = (prompt or "").strip()
    low = text.lower()
    toks = re.findall(r"[a-z0-9]{3,}", low)
    kind = "baat"
    if _Q_RX.search(low) or "?" in text:
        kind = "sawal"
    elif _QM_RX.search(low):
        kind = "request"
    # sac / identity / chit-chat ke alag-hai chehre
    if re.search(r"(?i)\b(tum|tu|aap|who is you|your name|tumhara naam|apna)\b", low):
        kind = kind if kind != "baat" else "identity-check"
    islamic = bool(re.search(
        r"(?i)\b(allah|quran|namaz|hadith|dua|ramzan|roza|zakat|namaz|sajda|"
        r"pack|p\w+ +muslim|muslim|islam|sunnah|mecca|madina|masjid)\b", low))
    return {"kind": kind, "words": toks[:12], "n": len(toks),
            "islamic": islamic, "len": len(text), "qmark": int("?" in text)}


def auto_suggestions(intent: dict) -> list:
    """FOCUS phase ka thought-khad: kis raste jawab jayega (HUD note)."""
    sug = []
    if intent.get("islamic"):
        sug.append("sacred → sirf Quran+Hadith books")
    elif not intent.get("words"):
        sug.append("bilkul unknown → yaad/imandari")
    return sug


# ----------------------------------------------------------------------
# switch/state
# ----------------------------------------------------------------------
def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"display": "on", "updated": None}


def save_state(st):
    try:
        st["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def get_display() -> str:
    return load_state().get("display", "on")


def set_display(mode: str):
    mode = (mode or "on").lower().strip()
    if mode not in ("on", "off", "verbose", "auto"):
        mode = "on"
    if mode == "auto":
        mode = "on"
    st = load_state()
    st["display"] = mode
    save_state(st)
    return st


def status():
    st = load_state()
    return {"display": st.get("display", "on"),
            "phases": PHASES,
            "glyphs": {k: v for k, v in _PHASE_GLYPH.items()}}


if __name__ == "__main__":
    print("FLOW:", status()["display"], "phases:", " → ".join(PHASES))
    i = read_intent("photosynthesis kya hai aur kyun zaruri hai")
    print("intent demo:", i)
    print(set_display("on"))
