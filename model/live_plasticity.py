"""
⚡ live_plasticity.py — REAL-TIME NEUROPLASTICITY (baat karte waqt seekhna)

Kya karta hai:
  Chat ke har pak-jawab par dimagh ke WAAZAN (LSTM weights) me HALKI
  tabdeeli (Hebbian-style reinforcement) — asli machinery: brain.train_step
  (truncated BPTT, pure NumPy) — train_master jaisa hi, bas CHHOTA dose.

  TEACHING RULE (imandar sirf):
    SIRF pak-evidence par seekh:
      - yaad-se        → kitab ka asli text (Bukhari/Muslim/Quran verified) ✅
      - live-research  → whitelist-net ka asli text ✅
      - khud-soch      → sirf tab jab metacognition verdict "pak-yakeen" ho
      - imaandari / tarbiyat / nakli-shakwal → NAHI (jhoot na seekhe)
    Teaching pair corpus-format me: "\nSawal: q\nJawab: a\n"
    (brain agli dafa yehi sawal pohanchay to yad-raste jawab)

 SAFETY (qanoon — koi override nahi):
    - LR cap 0.0025 (chhota dose — bade weights nahi bigdati)
    - Har turn max 1-3 micro-steps (tier ke mutabiq)
    - 1.5s cooldown between plastic turns
    - Aur jab training (train_master process) CHAL RAHI ho → loading khud
      apne copy par, saving separate file genmaster_chat.npz (training ka
      genmaster_mid.npz chhedta nahi — do stream alag)
    - Save har 20 turn ke baad (tmp + os.replace — atomic)

 Connects: model.generate (khud wehe chat brain instance) — live update
           core.hub.get_brain → bio-side pe chhota "experience" pulse
 status(): hub ke liye counters
"""
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
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from model.tokenizer import CharTokenizer   # noqa: E402

CKPT_DIR = os.path.join(ROOT, "model", "checkpoints")
CHAT_NPZ = os.path.join(CKPT_DIR, "genmaster_chat.npz")
LR_CAP = 0.0025
COOLDOWN = 1.5
SAVE_EVERY = 20
WIN = 33                                    # SEQ_LEN+1 (train_master wala)

_ST = {"turns": 0, "steps": 0, "saved": 0, "skipped": 0, "last": 0.0,
       "last_source": "", "last_loss": None}
_LEARN_BUSY = {"on": False}          # ⚡ BG-learn guard (ek waqt ek)


def _do_learn(prompt, answer, source, tier):
    """BG thread ka asli kaam — chat thread kabhi block NAHI hota."""
    global _ST
    try:
        tok, brain = _load_pair()
        if tok is None or brain is None:
            _ST["skipped"] += 1
            return
        steps = {"low": 1, "mid": 2, "high": 3}.get(tier, 1)
        ids = tok.encode(_teach_text(prompt, answer))
        if len(ids) < WIN:
            ids = ids + tok.encode("\n" * (WIN - len(ids)))
        brain.lr = min(LR_CAP, brain.lr if getattr(brain, "lr", 0) else LR_CAP)
        losses = []
        for k in range(steps):
            i = (k % max(1, len(ids) - WIN))
            losses.append(brain.train_step(ids[i:i + WIN]))
        _ST["turns"] += 1
        _ST["steps"] += steps
        _ST["last"] = time.time()
        _ST["last_source"] = source
        if losses:
            _ST["last_loss"] = round(float(sum(losses) / len(losses)), 4)
        _bio_pulse()
        if _ST["turns"] % SAVE_EVERY == 0:
            save_chat(brain)
    except Exception:
        _ST["skipped"] += 1
    finally:
        _LEARN_BUSY["on"] = False


def status():
    return {"turns": _ST["turns"], "micro_steps": _ST["steps"],
            "saves": _ST["saved"], "skipped": _ST["skipped"],
            "file": os.path.relpath(CHAT_NPZ, ROOT),
            "lr_cap": LR_CAP, "cooldown": COOLDOWN}


def _load_pair():
    """model.generate ka wahi tok/brain jispe chat chal rahe ho (live weights)."""
    from model import generate as G
    ck = G.best_checkpoint()
    if ck is None:
        return None, None
    tok, brain = G._load_model(ck)
    return tok, brain


def _teach_text(prompt: str, answer: str):
    return "\nSawal: %s\nJawab: %s\n" % (prompt.strip(), answer.strip())


def _bio_pulse():
    try:
        from core.hub import get_brain
        b = get_brain()
        if b is not None:
            b.decisions.append({"t": b.t, "act": "live_plastic",
                                "note": "chat se seekha"})
    except Exception:
        pass


def learn_turn(prompt: str, answer: str, source: str, tier: str = "low",
               doubt: float = 0.0):
    """Ek chat-turn ka halka reinforcement — ⚡ BACKGROUND THREAD me hota hai
    (chat ke jawab ka waqt par ZERO asar); returns dict|None (status ke liye)."""
    now = time.time()
    if now - _ST["last"] < COOLDOWN:
        _ST["skipped"] += 1
        return None
    if not prompt or not answer or len(answer) < 40:
        _ST["skipped"] += 1
        return None
    # 🪞 teaching eligibility (metacognition sath)
    teach = False
    if source in ("yaad-se", "live-research"):
        teach = True
    elif source == "khud-soch" and doubt <= 0.25:
        teach = True                     # sirf pak-yakeen khud-soch
    if not teach:
        _ST["skipped"] += 1
        return None
    if _LEARN_BUSY["on"]:                # ⚡ pichla learn chal raha? naye skip
        _ST["skipped"] += 1
        return None
    _LEARN_BUSY["on"] = True
    _ST["last"] = now
    threading.Thread(target=_do_learn, args=(prompt, answer, source, tier),
                     daemon=True).start()
    return {"taught": "queued", "source": source}


def save_chat(brain=None):
    """WAAZAN chat-file me sanjr (tmp+rename atomic; trainer-file alag)."""
    try:
        if brain is None:
            _, brain = _load_pair()
            if brain is None:
                return False
        tmp = CHAT_NPZ + ".tmp"
        brain.save(tmp)
        os.replace(tmp, CHAT_NPZ)       # atomic
        _ST["saved"] += 1
        return True
    except Exception:
        return False


if __name__ == "__main__":
    print(status())
