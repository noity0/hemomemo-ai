"""
🤝 helper_brain.py — TEESRA DIMAGH (HEMOMO-HELPER ~5.1M params, dh560)

User qanoon: "2 more brains each of 5M — one for HELPING main brain +
thinking engine to give good answers, second for VERIFYING research answers;
dono main brain se CONNECT; main brain 7M."

Helper brain ka kaam:
  • jab master (7M) ka khud-soch gate FAIL ho → helper ek dafa khud-sample
    karta hai ("1 dafa hor socho" courtesy) → 'helper-soch' jawab
  • master + aqal-core (model/aqal.py) ke candidates ko dosri ray deta hai
  • bridge: 250k bio-neuron tissues (core/hub) + deep-brain (dh620) network

Checkpoint: model/hemohelper_*.npz  (tarbiyat: scripts\\train_master.py 6000 --helper)
No API, no cloud, no AI-model connection — pure NumPy.
"""

import glob
import os
import sys

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

_HELPER = {"checked": False, "path": None}


def checkpoint():
    """SAB se naya helper checkpoint (hemohelper_*.npz, chat.npz chor kar)."""
    if not _HELPER["checked"]:
        _HELPER["checked"] = True
        try:
            from model.generate import CKPT_DIR
            cands = []
            for p in glob.glob(os.path.join(CKPT_DIR, "hemohelper_*.npz")):
                base = os.path.basename(p)
                if base.startswith("hemohelper_chat"):
                    continue
                cands.append(p)
            cands.sort(key=os.path.getmtime, reverse=True)
            _HELPER["path"] = cands[0] if cands else None
        except Exception:
            _HELPER["path"] = None
    return _HELPER["path"]


def refresh():
    """Naye checkpoint ke baad dobara dekho."""
    _HELPER["checked"] = False
    return checkpoint()


def params_estimate(vocab: int = 80) -> int:
    """LSTMBrain param-count (helper: dh=560) — 16dh^2 + 2*vocab*dh."""
    dh = 560
    return 16 * dh * dh + 2 * vocab * dh


def assist(prompt, notes=None, temperature: float = 0.5, max_new: int = 130):
    """MASTER ke jawab kharab aya? HELPER ek dafa khud sochta hai.
    Return: (text) ya None (fail / helper checkpoint nahi). Sab quality-guards."""
    ck = checkpoint()
    if not ck:
        return None
    try:
        from model.generate import (_load_model, _clean, _no_citation,
                                    _quality, _relevance)
        tok, brain = _load_model(ck)
        p2 = ("\n" + "\n".join((notes or [])[:2]) + "\n") if notes else "\n"
        out = brain.sample(p2, tok, max_new=max_new,
                           temperature=min(0.85, temperature * 1.1))
        c = _clean(out)
        if c and _no_citation(c) and len(c) >= 24:
            sc = _quality(c) + _relevance(prompt, c)
            if _quality(c) >= 2.2 and sc >= 2.6:
                return c
    except Exception:
        return None
    return None


def status():
    """Hub ke liye: helper-brain dictionary."""
    ck = checkpoint()
    return {"on": bool(ck), "checkpoint": os.path.basename(ck) if ck else None,
            "params": "%s (~5.1M, dh560) — master-ka-madadgar" % f"{params_estimate():,}",
            "bridge": "master(7M)+aqal-core+deep(6.25M)+verify(5.1M)+2M bio-neurons"}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("🤝 HELPER brain:", status())
    r = assist("ilm kya hai")
    print("sample:", (r or "(helper checkpoint nahi / fail)")[:160])
