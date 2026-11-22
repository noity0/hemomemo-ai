"""
🔁 autoreload.py — Hemomemo AI AUTO-BRAIN-RELOAD (har 3 minute)

User qanoon: "brain reload ko auto karo hr 3 min may auto reload" — desktop
app ka 🔄 button ab har-dafa zaroori NAHI: ye daemon-thread har 180s me:
  1) naya hemomaster checkpoint?  → ASLI dimagh-reload (mtime-keyed, asli npz)
  2) helper/deep/verify brains   → apne naye checkpoints (asli)
  3) yaad-memo (learned_chat.txt / liveresearch.txt / corpus) → TAZA index
  4) research-CACHE saaf         → agli talash ASLI web-se (fresh page-parhi)
  5) learner dedup-set taza      → naye seekhe hue jawab foran yaad
SAB live-import se local — koi AI/API/platform connection NAHI (net_guard ON;
web-sirf whitelisted knowledge-pages ki parhi, jaisa live_research karta hai).

chat_once/chat_loop pehli call par start_auto() chala dete hain — app me bhi
ye khud chalta hai (ek dafa manual 🔄 ke baad hamesha AUTO).
"""

import threading
import time

AUTO = {"on": False, "interval": 180.0, "last": None, "count": 0, "err": None}
_LOCK = threading.Lock()
_THREAD = None


def refresh_all(reason: str = "manual"):
    """Poore dimagh/yaad ka ASLI refresh — info-dict. Koi API nahi."""
    from model import generate as G
    info = {"reason": reason, "t": time.strftime("%H:%M:%S")}
    # 1) yaad-memo TAZA (learned_chat/liveresearch/corpus → naya qa-index)
    try:
        G._MEMO["key"] = None
        G._WORDS = None
        G._qa_index()
        info["memory"] = "taza (qa-index + words)"
    except Exception as _e:
        info["memory"] = "skip (%s)" % str(_e)[:50]
    # 2) naya hemomaster checkpoint? _load_model mtime-keyed ASLI-reload
    try:
        ck = G.best_checkpoint()
        if ck:
            G._load_model(ck)
            info["brain"] = "hemomaster: %s" % (
                ck.replace("\\", "/").rsplit("/", 1)[-1][:34])
        else:
            info["brain"] = "checkpoint nahi (RAG-only chal raha)"
    except Exception as _e:
        info["brain"] = "skip (%s)" % str(_e)[:50]
    # 3) teen chhote dimagh (helper/deep/verify) ke naye checkpoints
    for mod, nm in (("model.helper_brain", "helper"),
                    ("model.deep_brain", "deep"),
                    ("model.verify_brain", "verify")):
        try:
            _m = __import__(mod, fromlist=["refresh"])
            _m.refresh()
            info[nm] = "taza"
        except Exception as _e:
            info[nm] = "skip (%s)" % str(_e)[:36]
    # 4) research-CACHE saaf → har talash ASLI-fresh web-se (no API)
    try:
        from model import live_research as L
        L.CACHE.clear()
        L._SEEN = None
        info["research"] = "cache saaf (agli talash live page-parhi)"
    except Exception as _e:
        info["research"] = "skip (%s)" % str(_e)[:50]
    # 5) learner dedup-set taza (naye seekhe jawab foran yaad me aayen)
    try:
        from model import learner as LR
        LR._seen = None
        info["learner"] = "taza"
    except Exception as _e:
        info["learner"] = "skip (%s)" % str(_e)[:50]
    return info


def _loop(interval: float):
    while True:
        time.sleep(max(30.0, float(interval)))
        try:
            with _LOCK:
                _r = refresh_all("auto-3min")
                AUTO["last"] = _r
                AUTO["count"] += 1
                AUTO["err"] = None
        except Exception as _e:
            AUTO["err"] = str(_e)[:80]


def start_auto(interval: float = None):
    """Daemon-thread shuru (sirf ek dafa) — har interval-sec refresh_all."""
    global _THREAD
    with _LOCK:
        if AUTO["on"]:
            return False
        if interval:
            AUTO["interval"] = float(interval)
        _THREAD = threading.Thread(target=_loop, args=(AUTO["interval"],),
                                   daemon=True, name="hemomemo-autoreload")
        _THREAD.start()
        AUTO["on"] = True
        return True


def status():
    return {"on": AUTO["on"], "interval_sec": int(AUTO["interval"]),
            "last": AUTO["last"], "count": AUTO["count"], "err": AUTO["err"],
            "qanoon": "har %ds: dimagh + yaad + research-cache auto-reload "
                      "(online live-parhi — koi AI/API/platform NAHI)"
                      % int(AUTO["interval"])}
