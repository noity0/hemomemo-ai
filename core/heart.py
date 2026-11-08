"""
❤️ heart.py — DIGITALBRAIN KA DIL (heartbeat + strength + yaad-consolidation)

Dil kya karta hai (bio-design — NO API, NO CLOUD, NO OTHER AI, pure NumPy):
  1. PULSE  : adaptive BPM dhadkan (aaram 60 bpm, kaam/arousal me 80-100)
  2. PUMP   : har dhadkan par bio-brain ko halka attention-pulse (senses +
              decisions me 'heart pulse' experience) — dimagh sota nahi
  3. POWER  : hub.bio_think ka arousal ab dil ki STRENGTH se boost hota hai
              (capped, honest multiplier — koi baghair dhadkan ke boost nahi)
  4. CONSOLIDATION : jis waqt chat IDLE ho (>60s), dil apka LSTM par HALKE
              haqeeqi BPTT steps chalata hai — asli corpus ke qatatik (jaise
              sleep consolidation) — yaad mazboot hogi — battery saver:
              sirf tab jab training/trainer CPU par nahi (checkpoint mtime
              recent change hua? → digh darji)
  5. STRENGTH: 0..100 — sirf ASLI mehnat se barhta hai (pack-evidence wale
              plasticity micro-steps + consolidation steps); kabhi faltu nahi

  6. AUTONOMOUS-IBADAT: 🤖 fully local reasoning engine (model/autonomous.py) —
               jab wo khud-se verified confident (>=0.60) jawab deta hai, dil ko
               uske liye asli strength micro-step milta hai (confidence-weighted,
               honest gain); koi AI-api / ai-model / ai-platform / cloud boost NAHI

State      : data/heart_state.json  (beats, strength, bpm barhta rehta hai)
Wiring     : core.hub (bio_think boost + status) | model.generate (chat start) | model/autonomous (engine answers)
CLI        : python core\\heart.py            (zindagi dekho)
"""
import json
import os
import sys
import threading
import time

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

STATE_PATH = os.path.join(ROOT, "data", "heart_state.json")
_IDLE_AFTER = 60.0          # chat ki khamoshi kitni der ho to consolidation
_CONSOL_EVERY = 8           # har 8 dhadkan baad consolidation ki koshish
_AROUSAL_CAP = 0.15         # bio arousal par dil ka max-boost (capped hona)
_SAVE_EVERY = 10

_AUT = {"answered": False, "count": 0, "conf": 0.0, "kind": ""}

_ST = {"beats": 0, "strength": 0.0, "bpm": 62, "started": None,
       "last_beat": None, "last_pump": 0.0, "consol": 0, "session": 0,
       "aut_gains": 0}

_TH = {"on": False, "stop": False}      # heartbeat thread flags
_LOCK = threading.Lock()


# ----------------------------------------------------------------------
def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            for k in ("beats", "strength", "bpm", "started", "last_beat",
                      "consol", "aut_gains"):
                if k in d:
                    _ST[k] = d[k]
        if not isinstance(_ST.get("strength"), (int, float)):
            _ST["strength"] = 0.0
    except Exception:
        pass
    return _ST


def save_state():
    try:
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(_ST, f, ensure_ascii=False)
        os.replace(tmp, STATE_PATH)
    except Exception:
        pass


# ----------------------------------------------------------------------
def _target_bpm() -> int:
    """Aaram me 62 — kaam/arousal tez. Arousal hub-latest me hota, sasta."""
    try:
        from core.hub import latest_arousal
        a = latest_arousal()
    except Exception:
        a = 0.0
    return int(62 + min(0.5, max(0.0, a)) * 76)      # 62..100 bpm


def strength() -> int:
    """Dil ki quwat 0..100 — sirf PARHNE wala (pure) function. Gain sirf
    note_autonomous()/consolidation step me hota hai — read par boost NAHI
    (pehle yahan bhi += ho raha tha — har status-check par strength barhti
    thi — jhoot; ab khatam)."""
    try:
        from model.live_plasticity import status as _ps
        steps = int(_ps().get("micro_steps", 0))
    except Exception:
        steps = 0
    gained = _ST["consol"] * 0.5 + steps * 1.5
    return int(min(100.0, max(0.0, _ST["strength"] + gained)))


def note_autonomous(answered: bool, confidence: float = 0.0, kind: str = "") -> dict:
    """🤖 Autonomous engine → dil ki ibadat (local, no AI).

    answered=True aur confidence>=0.60 hone par (khud AST/math/web-research/
    hypothesis self-verify se verified jawab) dil ki strength me ek asli
    confidence-weighted micro-step hota hai; koi fabricated/nahi jawab nahi
    count hoti. Kabhi kisi AI-api/model se strength nahi badhategi.
    """
    with _LOCK:
        _AUT["answered"] = bool(answered)
        _AUT["count"] = int(_AUT.get("count") or 0) + 1
        _AUT["conf"] = float(confidence or 0.0)
        _AUT["kind"] = kind or ""
        if answered and float(confidence or 0.0) >= 0.60:
            _ST["strength"] = min(100.0, _ST["strength"] + 0.5 * float(confidence))
            _ST["aut_gains"] = int(_ST.get("aut_gains") or 0) + 1
    return dict(_AUT)


def bio_pulse(beat_no: int):
    """Dhadkan → bio-brain ko halka experience (dimagh jaga rehta hai)."""
    try:
        from core.hub import get_brain
        b = get_brain()
        if b is not None:
            b.senses.sound.hear_tone((beat_no % 8) + 1)     # dhadkan-awaaz
            b.decisions.append({"t": b.t, "act": "heart_pulse",
                                "note": "dil ka dhadkan #%d" % beat_no})
    except Exception:
        pass


def _trainer_busy() -> bool:
    """🏋️ trainer PID zinda hai? → dil DUSHMANI nahi, CPU aapkay aatan karta.
    (data/_trainer_pid.json + Windows kernel32 OpenProcess — no subprocess)"""
    pid = 0
    try:
        with open(os.path.join(ROOT, "data", "_trainer_pid.json"),
                  encoding="utf-8") as f:
            pid = int(json.load(f).get("pid", 0))
    except Exception:
        return False                      # pid-file nahi → dil azaad
    if pid <= 0:
        return False
    try:
        import ctypes
        k32 = ctypes.windll.kernel32      # PROCESS_QUERY_LIMITED_INFORMATION
        h = k32.OpenProcess(0x1000, False, pid)
        if not h:
            return False                  # process khatam ho chuka
        try:
            code = ctypes.c_uint()
            k32.GetExitCodeProcess(h, ctypes.byref(code))
            return bool(code.value == 259)   # STILL_ACTIVE
        finally:
            k32.CloseHandle(h)
    except Exception:
        return False                      # unsure → interference se bacho


def _consolidate_once() -> bool:
    """🧠 YAAD-MAZBOOTI: IDLE chat + no-trainer par 1 tiny BPTT step asli
    corpus ke ek win par → weights gahra jata hai (sleep-style discipline)."""
    try:
        import model.generate as G
        # 💭 chat ka akhri istikmal? (generate ko call ka waqt bhi milna chahiye)
        last_chat = float(getattr(G, "_LAST_CHAT_TS", 0.0) or 0.0)
        if last_chat and (time.time() - last_chat) < _IDLE_AFTER:
            return False
        # 🏋️ trainer CPU par? haal me checkpoint badla? → choro (no begara CPU)
        ck = G.best_checkpoint()
        if not ck:
            return False
        if _trainer_busy():
            return False                  # ❤️ trainer ki hifazat pehle
        try:
            if (time.time() - os.path.getmtime(ck)) < 90:
                return False
        except OSError:
            return False
        from model.live_plasticity import _LEARN_BUSY, COOLDOWN
        if _LEARN_BUSY["on"] or (time.time() - _ST["last_pump"]) < COOLDOWN:
            return False
        _LEARN_BUSY["on"] = True
        try:
            tok, brain = G._load_model(ck)
            txts = list(G._qa_index())                       # ASLI yaad hi
            if not txts:
                return False
            q, a = txts[hash(str(_ST["beats"])) % len(txts)]
            pair = "\nSawal: %s\nJawab: %s\n" % (q, a)
            ids = tok.encode(pair)
            win = 33
            if len(ids) < win:
                ids = ids + tok.encode("\n" * (win - len(ids)))
            if len(ids) > win:
                i = hash(str(_ST["consol"] + 1)) % max(1, len(ids) - win)
                ids = ids[i:i + win]
            brain.lr = 0.0015                                # 🪫 chhota dose
            brain.train_step(ids)
            _ST["consol"] += 1
            _ST["last_pump"] = time.time()
            # 💾 heart-apne-memory ki saanjhi (atomic, chat file alag to nahi —
            # chat ki file hi "zinda" model hai)
            from model.live_plasticity import save_chat
            return save_chat(brain)
        finally:
            _LEARN_BUSY["on"] = False
    except Exception:
        return False


def _loop():
    while not _TH["stop"]:
        _ST["bpm"] = _target_bpm()
        interval = 60.0 / max(50, _ST["bpm"])
        time.sleep(interval)
        with _LOCK:
            _ST["beats"] += 1
            _ST["session"] += 1
            _ST["last_beat"] = time.strftime("%H:%M:%S")
        bio_pulse(_ST["beats"])
        try:
            el = time.time()
            if _ST["beats"] % _CONSOL_EVERY == 0:
                if _consolidate_once():
                    save_state()
                elif _ST["beats"] % (_CONSOL_EVERY * 5) == 0:
                    save_state()
            if el and _ST["beats"] % _SAVE_EVERY == 0:
                save_state()
        except Exception:
            pass


def start():
    """Dil ka dhadkan shuru (idempotent — chat/hub dono call karen to bhi 1)."""
    load_state()
    if _TH["on"]:
        return False
    _TH["on"] = True
    _TH["stop"] = False
    if _ST["started"] is None:
        _ST["started"] = time.strftime("%Y-%m-%d %H:%M")
    t = threading.Thread(target=_loop, daemon=True, name="digital-heart")
    t.start()
    return True


def stop():
    _TH["stop"] = True
    save_state()


def status():
    load_state()
    _TH["on"] = bool(_TH["on"]) and not _TH["stop"]
    return {"on": _TH["on"] or _TH.get("alive", False),
            "bpm": _ST["bpm"], "beats": _ST["beats"],
            "strength": strength(), "started": _ST.get("started"),
            "last_beat": _ST.get("last_beat"),
            "consolidations": _ST["consol"],
            "autonomous": {"answered": bool(_AUT.get("answered")),
                           "count": int(_AUT.get("count") or 0),
                           "confidence": float(_AUT.get("conf") or 0.0),
                           "kind": _AUT.get("kind") or ""}}


if __name__ == "__main__":
    start()
    print("❤️ DigitalBrain ka dil dhadak raha hai — (Ctrl+C = band)")
    try:
        while True:
            time.sleep(2)
            s = status()
            print("  ❤️ bpm %d | beats %d | strength %d/100 | consol %d" % (
                s["bpm"], s["beats"], s["strength"], s["consolidations"]))
    except KeyboardInterrupt:
        stop()
        print(" 🫀 dil kitne beat ke sath so gaya — state saved")
