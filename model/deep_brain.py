"""
🧠🧠 deep_brain.py — DUSRA DIMAGH (HEMOMO-DEEP ~6.25M params, dh620)

MASTER brain (5.1M) ke SATH — "second brain first brain se CONNECT":
  • agar pehla dimagh ka khud-soch gate FAIL ho (kachra/kamzor samples) to
    DEEP brain ek dafa khud-sample karta hai → 'deep-soch' jawab
  • BRIDGE = bio-hub ke 2,000,000 neuron tissuess + glia — dono dimagh ka
    arousal/spiritual-state ek hub se milta hai (koi API, koi AI nahi)
  • deep ka jawab WOHI guards: _clean + _no_citation + _quality + _relevance
  • checkpoint: model/gendeep_*.npz (gendep_mid warm-resume trainer me)

Tarbiyat: python scripts\\train_master.py 6000 --deep   (dh620)
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

_DEEP = {"checked": False, "path": None}


def checkpoint():
    """SAB se naya deep checkpoint (gendeep_*.npz, chat.npz chor kar)."""
    if not _DEEP["checked"]:
        _DEEP["checked"] = True
        try:
            from model.generate import CKPT_DIR
            cands = []
            for p in glob.glob(os.path.join(CKPT_DIR, "gendeep_*.npz")):
                base = os.path.basename(p)
                if base.startswith("gendeep_chat"):
                    continue                      # chat-live file alag
                cands.append(p)
            cands.sort(key=os.path.getmtime, reverse=True)
            _DEEP["path"] = cands[0] if cands else None
        except Exception:
            _DEEP["path"] = None
    return _DEEP["path"]


def refresh():
    """Trainer ke naye checkpoint ke baad dobara dekho."""
    _DEEP["checked"] = False
    return checkpoint()


def params_estimate(dh: int = 620, vocab: int = 80) -> int:
    """LSTMBrain ka param-count (simplify: 2 layers + embed + head)."""
    return 2 * 4 * (dh * dh + dh * dh) + 2 * vocab * dh


def rescue_sample(prompt, notes=None, temperature: float = 0.5,
                  max_new: int = 130):
    """DEEP brain ka ek sample — WAQT-beta (sirf jab pehla brain fail ho).
    Return: (text) ya None (fail/deep nahi mila). Sab guards yahan hi."""
    ck = checkpoint()
    if not ck:
        return None
    try:
        from model.generate import (_load_model, _clean, _no_citation,
                                    _quality, _relevance, _words)
        tok, brain = _load_model(ck)
        p2 = ("\n" + "\n".join((notes or [])[:2]) + "\n") if notes else "\n"
        out = brain.sample(p2, tok, max_new=max_new,
                           temperature=min(0.9, temperature * 1.25))
        c = _clean(out)
        if c and _no_citation(c) and len(c) >= 24:
            sc = _quality(c) + _relevance(prompt, c)
            if _quality(c) >= 2.2 and sc >= 2.6:
                return c
    except Exception:
        return None
    return None


def status():
    """Hub ke liye: deep-brain dictionary."""
    ck = checkpoint()
    return {"on": bool(ck), "checkpoint": os.path.basename(ck) if ck else None,
            "params": "%s (~6.25M, dh620)" % f"{params_estimate():,}",
            "bridge": "2M bio-neuron tissues (core/hub)"}


if __name__ == "__main__":
    import sys as _s
    try:
        _s.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    s = status()
    print("🧠 DEEP brain:", s)
    r = rescue_sample("ilm kya hai")
    print("sample:", (r or "(deep checkpoint nahi / fail)")[:160])
