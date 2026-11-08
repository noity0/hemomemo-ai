"""
🔗 hub.py — Hemomemo AI CENTRAL NERVOUS HUB

Poore project ke tamam hisse yahan ek doosre se deeply jure hain:
  brain/      -> 2,000,000 neurons + 1,600,000 glia (senses, synapses, motor, electric)
  model/      -> Hemomemo AI LSTM khud-soch (generation, tokenizer, checkpoints)
  knowledge/  -> Quran guard (read-only hifazat) + quran zone
  data/       -> corpus + corpus_big knowledge files (+ vocab.json)
  evolution/  -> genetic engine (best DNA)
  core/       -> brain state save/load + YEH hub
  server/ + web/ -> local browser chat (no internet)
  model_card.json -> pehchan card

Koi file akeli nahi — sab hub ke zariye milte hain.
No API, no Ollama, no internet — sirf is PC.
"""
import glob
import json
import os
import sys
import threading as _threading

import numpy as np

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARD_PATH = os.path.join(ROOT, "model", "model_card.json")
DATA = os.path.join(ROOT, "data")
BIG = os.path.join(DATA, "corpus_big")
CKPT = os.path.join(ROOT, "model", "checkpoints")
STATE_PATH = os.path.join(ROOT, "core", "brain_hub.npz")
DNA_PATH = os.path.join(ROOT, "core", "best_dna.npz")
PORT = 7812

_HOLDER = {"brain": None, "chat_calls": 0, "bio_steps": 0}
_WARM = {"started": False}          # 🪶 behind-the-scenes warm (pehli call fast)


# ----------------------------------------------------------------------
# 1) BIO-BRAIN (shared — har process me SIRF ek instance)
# ----------------------------------------------------------------------
def get_brain(seed: int = 2027):
    """Shared bio-brain (2M neurons + 1.6M glia). Purani halat auto-load."""
    if _HOLDER["brain"] is None:
        from brain.brain import DigitalBrain
        b = DigitalBrain(seed=seed, learning=True)
        load_light(b)               # pichli baat-chaat ka nasabi haal wapas
        _HOLDER["brain"] = b
    return _HOLDER["brain"]


def sense_from_text(brain, prompt):
    """Prompt ko CHAAR senses me deep-convert (hub-to-brain link):
    vision spot + sound tone + touch pressure + keyboard letters."""
    rng = np.random.default_rng(abs(hash(prompt)) % (2 ** 32))
    brain.senses.vision.draw_spot(int(rng.integers(2, 23)),
                                  int(rng.integers(2, 23)),
                                  radius=int(rng.integers(2, 5)))
    brain.senses.sound.hear_tone(int(rng.integers(0, 8)))
    brain.senses.touch.press(int(rng.integers(0, 12)), int(rng.integers(0, 12)))
    brain.senses.keyboard.feed_text(prompt)


_MOOD = {"arousal": 0.10, "action": "idle_rest", "conf": 0.0,
         "glia_calcium": 0.0, "grid": "-", "beats": 0,
         "brain": "brain on: garam (bg)"}
_MOOD_BUSY = {"on": False}


def _mood_refresh(prompt):
    """BvG thread: brain ka tick + naya mood cache (critical-path se BAHAR)."""
    if _MOOD_BUSY["on"]:
        return
    _MOOD_BUSY["on"] = True
    try:
        b = get_brain()          # pehli bar bg me 10s init — koi block nahi
        sense_from_text(b, prompt)
        action, conf = b.step(1)
        assoc = float(b.neurons.area_rate("association"))
        g = b.glia.stats()
        # ❤️ DIL KA POWER: strength kadar ka arousal-boost (capped, halqa)
        try:
            from core.heart import strength as _hstrength
            _boost = 1.0 + 0.15 * (_hstrength() / 100.0)
        except Exception:
            _boost = 1.0
        _MOOD.update({"arousal": min(1.0, assoc * 90.0 * _boost),
                      "action": action, "conf": round(float(conf), 2),
                      "glia_calcium": round(g["glia_calcium"], 3),
                      "grid": b.grid.phase, "beats": int(b.grid.beats),
                      "brain": "brain on: %s %.2f" % (action, conf)})
    except Exception:
        pass
    finally:
        _MOOD_BUSY["on"] = False


def bio_think(prompt, steps: int = 1):
    """⚡ ZERO-BLOCK mood: pehle se bachai-hui halat TURANT de do, naya tick
    background thread me (chat kabi so-ta nahi). No API, no cloud, sirf local."""
    _HOLDER["bio_steps"] += 1
    if not _WARM["started"]:
        _WARM["started"] = True
        _threading.Thread(target=_mood_refresh, args=(prompt,),
                          daemon=True).start()
    elif not _MOOD_BUSY["on"]:
        _threading.Thread(target=_mood_refresh, args=(prompt,),
                          daemon=True).start()
    try:                      # ❤️ chat shuru hote hi dil ki dhadkan (idempotent)
        from core.heart import start as _heart_start
        _heart_start()
    except Exception:
        pass
    return dict(_MOOD)


def latest_arousal():
    """Aakhri mood ki arousal (heart isay idle-bpm chunta hai)."""
    try:
        return float(_MOOD.get("arousal", 0.0))
    except Exception:
        return 0.0


# ----------------------------------------------------------------------
# 2) think() — POORA SYSTEM EK SAWAL PAR (hub ka dil)
# ----------------------------------------------------------------------
def think(prompt, max_new: int = None):
    """Quran guard + bio-brain + yaad-dahai + LSTM khud-soch — sab hub me julay.
    (max_new=None = tier-mutabiq MAX output — user-qanoon: token-limit max)"""
    from model.generate import chat_once   # yahan import (circular se bachaw)
    _HOLDER["chat_calls"] += 1
    text, meta = chat_once(prompt, max_new=max_new, meta=True)
    b = _HOLDER["brain"]
    if b is not None and isinstance(meta, dict):
        bio = {"grid": b.grid.phase, "beats": int(b.grid.beats),
               "glia_calcium": round(float(b.glia.calcium.mean()), 3),
               "decisions": len(b.decisions),
               "steps": int(b.t)}
        meta = dict(meta)
        meta["bio"] = bio
    # har 25 baat-chaat par brain halka save (deep state continuity)
    if _HOLDER["chat_calls"] % 25 == 0:
        try:
            save_light()
        except Exception:
            pass
    return text, meta


# ----------------------------------------------------------------------
# 3) LIGHT STATE (neurons+glia sirf — 25M synapses NIMAT ho save me)
# ----------------------------------------------------------------------
def save_light(brain=None):
    b = brain if brain is not None else _HOLDER["brain"]
    if b is None:
        return None
    np.savez_compressed(
        STATE_PATH,
        v=b.neurons.v, u=b.neurons.u, gain=b.neurons.gain,
        v_threshold=b.neurons.v_threshold,
        spike_count=b.neurons.spike_count,
        rate_smooth=b.neurons.rate_smooth,
        calcium=b.glia.calcium, t=b.t)
    return STATE_PATH


def load_light(brain=None) -> bool:
    b = brain if brain is not None else _HOLDER["brain"]
    if b is None or not os.path.exists(STATE_PATH):
        return False
    try:
        with np.load(STATE_PATH) as d:
            if int(d["v"].shape[0]) != int(b.neurons.n):
                return False               # purana size — naye brain se mismatch
        b.neurons.v = d["v"]; b.neurons.u = d["u"]; b.neurons.gain = d["gain"]
        b.neurons.v_threshold = d["v_threshold"]
        b.neurons.spike_count = d["spike_count"]
        b.neurons.rate_smooth = d["rate_smooth"]
        b.glia.calcium = d["calcium"]
        b.t = int(d["t"])
        return True
    except Exception:
        return False


def get_brain_modulation():
    """🧠 Neural-LSTM Fusion: Brain ke neurons ka current flow (arousal/focus)
    model ki sochne ki quwwat (temperature/top-p) ko control karta hai."""
    try:
        b = get_brain()
        # Arousal: model kitna 'active' hona chahiye
        assoc = b.neurons.area_rate("association")
        arousal = min(1.0, float(assoc) * 100.0)
        
        # Focus: High arousal = Low temp (taez/sahi), Low arousal = High temp (creative/explore)
        temp = 0.95 - (arousal * 0.6) 
        return {"temp": max(0.2, temp), "top_p": 0.8 + (arousal * 0.15)}
    except:
        return {"temp": 0.5, "top_p": 0.9}


class DeepThinkingEngine:
    """🧠 Hemomemo AI Thinking Engine (3.2M parameters + Neural-Control)"""
    def __init__(self):
        self.brain = None
        self.model = None

    def think(self, prompt, max_new=None):
        # 1. Brain ko excite karo aur modulation lo
        from model.generate import chat_once
        
        # 2. Modulation lo
        mod = get_brain_modulation()
        
        # 3. Model ko Neural-Control ke sath run karo
        # think() already triggers bio_think internally via the orchestration
        # (max_new=None = tier-mutabiq MAX output — token-limit user-qanoon)
        text, meta = chat_once(prompt, max_new=max_new, meta=True, temperature=mod["temp"])
        return text, meta
def status():
    """Sare folders/files ka live inventory (deep connection ka inkishaf)."""
    out = {}

    # pehchan card
    try:
        with open(CARD_PATH, encoding="utf-8") as f:
            card = json.load(f)
        out["identity"] = {k: card.get(k) for k in ("name", "codename", "version",
                                                    "architecture", "offline")}
    except Exception:
        out["identity"] = "card nahi mila"

    # owner data file (Hafiz Muhammed Huzaifa Shamim) — core/owner.py se linked
    try:
        from core.owner import owner_dict
        od = owner_dict()
        out["owner"] = {
            "file": od["file"],
            "exists": od["file_exists"],
            "name": od["name"], "age": od["age"],
            "college": od["college"], "residence": od["residence"],
        }
    except Exception:
        out["owner"] = {
            "file": "owner_data.txt",
            "exists": os.path.exists(os.path.join(ROOT, "owner_data.txt")),
            "name": "Hafiz Muhammed Huzaifa Shamim",
        }

    # knowledge files (corpus + corpus_big)
    corpus = [os.path.join(DATA, "corpus.txt")]
    if os.path.isdir(BIG):
        corpus += sorted(glob.glob(os.path.join(BIG, "*.txt")))
    fout = []
    total = 0
    for p in corpus:
        if os.path.exists(p):
            sz = os.path.getsize(p)
            fout.append({"file": os.path.relpath(p, ROOT), "chars": sz})
            total += sz
    out["knowledge_files"] = {"count": len(fout), "chars": total,
                              "list": [f["file"] for f in fout]}

    # checkpoints + archive + archive mids
    npz = sorted(glob.glob(os.path.join(CKPT, "*.npz")), key=os.path.getmtime)
    out["model"] = {
        "active_checkpoint": os.path.basename(npz[-1]) if npz else None,
        "checkpoints": len(npz),
        "archived": len(glob.glob(os.path.join(CKPT, "archive", "*.npz"))),
        "vocab_json": os.path.exists(os.path.join(CKPT, "vocab.json")),
    }

    # quran zone + guard
    out["quran_zone"] = {
        "guard_module": os.path.exists(os.path.join(ROOT, "knowledge", "quran_guard.py")),
        "note": "READ-ONLY hifazat — Quran kabhi edit nahi hota",
    }

    # 📚 SACRED KNOWLEDGE STORE (poora Quran + 7 hadith books, sab languages)
    out["knowledge_store"] = {
        "quran_editions": len(glob.glob(os.path.join(
            ROOT, "knowledge", "quran", "translations", "*.json"))),
        "quran_editions_index": os.path.exists(os.path.join(
            ROOT, "knowledge", "quran", "editions_index.json")),
        "hadith_files": len([p for p in glob.glob(os.path.join(
            ROOT, "knowledge", "hadith", "*.json"))
            if os.path.basename(p) != "hadith_index.json"]),
        "hadith_index": os.path.exists(os.path.join(
            ROOT, "knowledge", "hadith", "hadith_index.json")),
        "policy": "Qadiani/Ahmadi sources MANA (harvest/source_policy.py)",
        "installer": "scripts/install_sacred_texts.py",
    }
    # 🛡️ live-net firewall + sahih-filter ke live numbers
    try:
        from harvest import net_guard
        out["net_guard"] = net_guard.status()
    except Exception:
        out["net_guard"] = {"note": "harvest/net_guard.py load nahi hua"}
    try:
        with open(os.path.join(ROOT, "data", "hadith_master.json"),
                  encoding="utf-8") as _f:
            _hm = json.load(_f)
        _so = _hm.get("sahih_only", {})
        out["hadith_sahih_only"] = {
            "total_kept": sum(c.get("kept", 0) for c in _so.values()),
            "total_dropped": sum(c.get("dropped", 0) for c in _so.values()),
            "policy": "sirf Sahih/Hasan (sunnah.com grades) — zaeef drop",
        }
    except Exception:
        out["hadith_sahih_only"] = {"note": "data/hadith_master.json nahi mila"}
    # 🪜🪞⚡ adaptive think-levels + metacognition + live-plasticity
    try:
        from model import think_level as _tl
        out["think_level"] = _tl.status()
    except Exception:
        out["think_level"] = {"note": "model/think_level.py nahi"}
    try:
        from model import metacognition as _mc
        out["metacognition"] = _mc._counters()
    except Exception:
        out["metacognition"] = {"note": "model/metacognition.py nahi"}
    try:
        from model import live_plasticity as _lp
        out["live_plasticity"] = _lp.status()
    except Exception:
        out["live_plasticity"] = {"note": "model/live_plasticity.py nahi"}
    try:
        from core import heart as _heart
        out["heart"] = _heart.status()
    except Exception:
        out["heart"] = {"note": "core/heart.py nahi"}
    try:
        from model import deep_brain as _db
        out["deep_brain"] = _db.status()
    except Exception:
        out["deep_brain"] = {"note": "model/deep_brain.py nahi"}
    try:
        from model import helper_brain as _hbr
        out["helper_brain"] = _hbr.status()
    except Exception:
        out["helper_brain"] = {"note": "model/helper_brain.py nahi"}
    try:
        from model import verify_brain as _vbr
        out["verify_brain"] = _vbr.status()
    except Exception:
        out["verify_brain"] = {"note": "model/verify_brain.py nahi"}
    try:
        from model.generate import best_checkpoint as _bcp
        _mck = _bcp()
        out["master_brain"] = {
            "on": bool(_mck),
            "checkpoint": os.path.basename(_mck) if _mck else None,
            "params": "7.07M (~dh660) — pehla dimagh (khud-soch)",
            "bridge": "2M bio-neurons + aqal-core + feelings"}
    except Exception:
        out["master_brain"] = {"note": "model/generate.py nahi"}
    try:
        from model import cognition as _cg
        out["cognition_flow"] = _cg.status()
    except Exception:
        out["cognition_flow"] = {"note": "model/cognition.py nahi"}
    try:
        from model import math_formulas as _mfl
        out["formula_library"] = {
            "file": "data/corpus_big/formulas_master.txt",
            "formulas": len(_mfl.load_all()),
            "kaam": "math+physics A-Z — plug-and-solve math solving me"}
    except Exception:
        out["formula_library"] = {"note": "model/math_formulas.py nahi"}
    try:
        from core.offline_oath import OATH_LINES
        out["offline_oath"] = "PERMANENT — " + OATH_LINES[0].split("(")[-1]
    except Exception:
        out["offline_oath"] = {"note": "core/offline_oath.py nahi"}

    # bio brain (live ho to stats, warna 'on-demand')
    b = _HOLDER["brain"]
    if b is not None:
        out["bio_brain"] = {"neurons": b.neurons.n,
                            "synapses": b.synapses.n * b.synapses.fan_out,
                            "glia": b.glia.n_glia,
                            "sim_steps": b.t,
                            "total_spikes": int(b.neurons.spike_count.sum()),
                            "grid": b.grid.phase,
                            "decisions": len(b.decisions)}
    else:
        out["bio_brain"] = "soya hua (pehli sawal par khud jaag jayega)"

    # evolution DNA
    out["evolution"] = {"best_dna": os.path.exists(DNA_PATH)}

    # hub state files
    out["state"] = {"light_state": os.path.exists(STATE_PATH),
                    "chat_calls": _HOLDER["chat_calls"],
                    "bio_steps": _HOLDER["bio_steps"]}

    # server
    out["server"] = {"host": "127.0.0.1", "port": PORT,
                     "page": "http://127.0.0.1:%d" % PORT}

    # 🛡 5-layer security stack (L1..L5 — HMHZ secret-language included)
    try:
        from security import guard as _sg
        out["security"] = _sg.status()
    except Exception as _se:
        out["security"] = {"note": "security/guard.py load nahi hua: %s" % _se}

    # 📚 auto-learner (verified-only chat learning)
    try:
        from model import learner as _lr
        out["learner"] = _lr.stats()
    except Exception as _le:
        out["learner"] = {"note": "model/learner.py load nahi hua: %s" % _le}

    # 🔁 auto-brain-reload (har 3 min: dimagh + yaad + research-cache)
    try:
        from model import autoreload as _ar
        out["autoreload"] = _ar.status()
    except Exception as _ae:
        out["autoreload"] = {"note": "model/autoreload.py load nahi hua: %s" % _ae}
    return out


def heartbeat_check():
    """Har subsystem on/off ka takazni check (TRUE=theek)."""
    checks = {}
    checks["identity"] = os.path.exists(CARD_PATH)
    corpus = glob.glob(os.path.join(BIG, "*.txt")) if os.path.isdir(BIG) else []
    checks["corpus"] = len(corpus) > 0 and os.path.exists(os.path.join(DATA, "corpus.txt"))
    checks["vocab"] = os.path.exists(os.path.join(CKPT, "vocab.json"))
    checks["quran_guard"] = os.path.exists(
        os.path.join(ROOT, "knowledge", "quran_guard.py"))
    checks["quran_translations"] = len(glob.glob(os.path.join(
        ROOT, "knowledge", "quran", "translations", "*.json"))) >= 300
    checks["hadith_books"] = len(glob.glob(os.path.join(
        ROOT, "knowledge", "hadith", "*.json"))) >= 20
    checks["brain_code"] = os.path.exists(os.path.join(ROOT, "brain", "brain.py"))
    checks["model_code"] = os.path.exists(os.path.join(ROOT, "model", "generate.py"))
    checks["web_page"] = os.path.exists(os.path.join(ROOT, "web", "index.html"))
    try:
        from core.owner import owner_file_exists
        checks["owner_data"] = owner_file_exists()
    except Exception:
        checks["owner_data"] = os.path.exists(os.path.join(ROOT, "owner_data.txt"))
    b = _HOLDER["brain"]
    checks["bio_brain"] = ("on" if b is not None else "soya (on-demand)")
    return {"ok": all([
        checks["identity"], checks["corpus"], checks["vocab"],
        checks["quran_guard"], checks["brain_code"], checks["model_code"],
        checks["owner_data"]]),
        "checks": checks, "name": "Hemomemo AI",
        "offline": True, "port": PORT}


if __name__ == "__main__":
    import pprint
    pprint.pprint(status())
