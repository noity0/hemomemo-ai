# -*- coding: utf-8 -*-
"""_train_deep5h.py — DEEP 3-GHANTAY (180-MIN) MASTER TRAINING (user-ka-hukum)

sare cheezein evolve jo pehle me thi (ek-sath, har theme 2x wazani):
  💻 coding-knowledge + agent-lessons          (pehle: comprehensive/united)
  🎮 games/minecraft + live-harvest            (pehle: cmdctrl/duo)
  🎬 video/genai-knowledge + research          (pehle: codevid/vid/research)
  💬 dialogues roman-urdu + english-basics     (pehle: dialogues/english)
  📐 formulas + lifecycle + deen-ilm           (pehle: trainer knowledge)
  🧠 live-yaad (learned_chat + liveresearch + meta_thoughts + qa_memo text)

Qanoon: 100% OFFLINE — koi AI-API, koi cloud, koi doosra AI NAHI.
Har 4-min MID-SAVE (laptop-bakaida-checkpoints salamat) + FINAL ckpt +
khud-soch samples + phir _apply_training_everywhere.py KHUD chal jata hai
(sab jagah a→z: checkpoints → desktop-app → zip → repo → sites).
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, r"D:\DigitalBrain")
os.chdir(r"D:\DigitalBrain")

import scripts.train_master as tm            # noqa: E402
from model.tokenizer import CharTokenizer    # noqa: E402
from model.nn import LSTMBrain               # noqa: E402

BUDGET_S = float(os.environ.get("TRAIN_SECONDS", "10800"))   # 3 GHANTAY
PREFIX = "hemomaster"
DH = int(os.environ.get("TRAIN_DH", str(tm.DH)))   # TRAIN_DH override (50M master: 1739; default=train_master.DH)
SEQ_LEN = tm.SEQ_LEN
RESULT = os.path.join(tm.DATA, "_training5h_result.json")

t_all = time.time()
try:
    with open(os.path.join(tm.DATA, "_trainer_pid.json"), "w",
              encoding="utf-8") as f:
        json.dump({"pid": os.getpid(),
                   "started": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "model": PREFIX, "budget_s": BUDGET_S,
                   "trainer": "deep5h"}, f)
except Exception:
    pass

combined, nfiles = tm.corpus_text()
print("📚 MASTER corpus: %d files | %s chars (base ilm — sab andar)"
      % (nfiles, f"{len(combined):,}"), flush=True)

# 🔁 sab pehle-wale mahfooz 2x-wazani ke sath (evolve — purana na ho)
BIG = os.path.join(tm.DATA, "corpus_big")
THEMES = {
    "💻 coding + agent": ["*coding*.txt",
                          "trainer_lessons_coding_video_text.txt"],
    "🎮 games + harvest": ["*games*.txt", "harvest_live.txt",
                           "gamebot_tasks.txt", "agent_orders.txt"],
    "🎬 video/genai + research": ["*video*.txt", "*vidai*.txt",
                                  "*research*.txt", "harvest_ilm.txt"],
    "💬 guftagu/dialogues": ["dialogues_roman_urdu*.txt", "trainer_*.txt"],
    "🇬🇧 english": ["english_basics*.txt"],
    "📐 formulas + lifecycle": ["formulas_master.txt", "lifecycle_master.txt",
                                "ilm_akhlaq.txt", "knowledge_ilm_deen.txt",
                                "sacred_facts.txt"],
}
added_n, added_c = 0, 0
for label, pats in THEMES.items():
    add = ""
    for pat in pats:
        for cf in glob.glob(os.path.join(BIG, pat)):
            try:
                with open(cf, "r", encoding="utf-8", errors="ignore") as f:
                    add += f.read() + "\n\n"
            except Exception:
                pass
    # 🧠 live-yaad bhi theme ke hisab se (learned_chat sirf chat-theme me 3x)
    combined += add * 2                     # 1x(base) + 2x = 3x wazani
    added_n += 1
    added_c += len(add) * 2
    print("   🔁 %s: 3x-wazani (+%s chars)" % (label, f"{len(add) * 2:,}"),
          flush=True)
# 🧠 live-memories (meanings: app ki seekh + meta-thoughts bhi evolve ho)
for mf in ("learned_chat.txt", "liveresearch.txt"):
    fp = os.path.join(BIG, mf)
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                combined += f.read() * 2    # apni yaad bhi 3x
        except Exception:
            pass
print("📚 FINAL corpus (2x-themes ke baad): %s chars"
      % f"{len(combined):,}", flush=True)

tok = CharTokenizer()
tok.fit_from_scratch(set(combined))
ids = tok.encode("\n\n" + combined + "\n\n")
ids_np = np.asarray(ids, dtype=np.int32)
n_windows = len(ids) - SEQ_LEN - 1
os.makedirs(tm.CKPT_DIR, exist_ok=True)
tok.save(os.path.join(tm.CKPT_DIR, "vocab.json"))
print("🔤 vocab: %d chars | windows: %s" % (tok.vocab_size,
                                            f"{n_windows:,}"), flush=True)

# 🗄️ archive-qanoon (SIRF EK MODEL chain) — purane finals archive me
# 🔓 RO-proof: read-only flag khulo, duplicate-archive ho to newer wala rakho
def _unro(fp):
    try:
        os.chmod(fp, 0o666)
    except Exception:
        pass
    try:
        subprocess.run(["attrib", "-R", fp], capture_output=True)
    except Exception:
        pass


os.makedirs(tm.ARCHIVE, exist_ok=True)
for f in glob.glob(os.path.join(tm.CKPT_DIR, "*.npz")):
    base = os.path.basename(f)
    if not base.startswith(PREFIX):
        continue
    _unro(f)                                 # source pehle khuli (unlinkShown)
    if base.endswith(".tmp.npz"):
        try:
            os.remove(f)
        except Exception:
            pass
        continue
    if base.startswith("%s_mid" % PREFIX) or base.startswith("%s_chat" % PREFIX):
        continue
    dst = os.path.join(tm.ARCHIVE, base)
    if os.path.exists(dst):
        _unro(dst)
        if os.path.getmtime(f) > os.path.getmtime(dst):
            try:
                os.remove(dst)
                shutil.move(f, dst)
            except Exception:
                pass
        else:
            try:
                os.remove(f)                 # purani nakal — folder saaf
            except Exception:
                pass
    else:
        shutil.move(f, dst)
print("🗄️ purane %s finals -> archive/" % PREFIX, flush=True)

brain = LSTMBrain(tok.vocab_size, d_h=DH, seed=2026)
mid = os.path.join(tm.CKPT_DIR, "%s_mid.npz" % PREFIX)
_mid_slots = [os.path.join(tm.CKPT_DIR, "%s_mid_a.npz" % PREFIX),
              os.path.join(tm.CKPT_DIR, "%s_mid_b.npz" % PREFIX)]
_mid_i = 0
_cands = [mid]                                   # classic mid-slot
for _f in glob.glob(os.path.join(tm.CKPT_DIR, "%s_mid_*.npz" % PREFIX)):
    _cands.append(_f)                            # rotation-slots (a/b)
for _f in glob.glob(os.path.join(tm.ARCHIVE, "%s_*.npz" % PREFIX)):
    _b = os.path.basename(_f)
    if _b.startswith("%s_mid" % PREFIX) or _b.startswith("%s_chat" % PREFIX):
        continue
    _cands.append(_f)
# mehfooz-warm-start: naya-tareen pehle — load-fail par agla-candidate
# (aadha-likha rotation-slot poore-dimagh ko KABHI zaya nahi hone deta)
warm_loaded = None
for _w in sorted(set(_cands), key=os.path.getmtime, reverse=True):
    if not os.path.exists(_w):
        continue
    try:
        _d = np.load(_w, mmap_mode="r")
        if (int(_d["embed"].shape[0]) == tok.vocab_size
                and int(_d["embed"].shape[1]) == DH):
            brain.load(_w)                       # 🔁 WARM-START
            warm_loaded = _w
            break
    except Exception as _e:
        print("(warm-skip %s: %s)" % (os.path.basename(_w), _e), flush=True)
if warm_loaded:
    print("🔁 WARM-START: %s" % os.path.basename(warm_loaded), flush=True)
else:
    print("(warm-start: koi-candidate-nahi) fresh soch se shuru", flush=True)
params = (brain.embed.size + brain.W_out.size + brain.b_out.size +
          sum(L.W.size + L.b.size for L in brain.layers))
print("🧠 HEMOMO-MASTER: %s params (dh%d) | budget: %.0f min"
      % (f"{params:,}", DH, BUDGET_S / 60.0), flush=True)


def sched(frac):
    if frac <= 0.50:
        return 0.010
    if frac <= 0.75:
        return 0.007
    return 0.004


rng = np.random.default_rng(2026)
deadline = t_all + BUDGET_S
last_mid = t_all - 700   # pehla-mid-save tarbiyat-ke-sirf-~3.3-min-baad
                         # (killer-cycle ~15.5-min — pehla-save us-se-pehle!)
step, losses = 0, []
print("🚀 DEEP 3-GHANTAY (180-MIN) TARBIYAT SHURU…", flush=True)
while time.time() < deadline:
    brain.lr = sched((time.time() - t_all) / BUDGET_S)
    i = int(rng.integers(0, n_windows))
    losses.append(brain.train_step(ids_np[i:i + SEQ_LEN + 1].tolist()))
    step += 1
    if step % 300 == 0:
        print("  step %d | loss %.4f | %.0f min baki"
              % (step, float(np.mean(losses[-300:])),
                 (deadline - time.time()) / 60.0), flush=True)
    if time.time() - last_mid >= 240:          # har 4 min mid-save (rotation)
        brain.save(_mid_slots[_mid_i % 2])     # purane-slot-ko-likho, naya-salamat
        _mid_i += 1
        last_mid = time.time()
        print("  💾 mid-save (step %d) — laptop band bhi → tarbiyat salamat"
              % step, flush=True)

final = os.path.join(tm.CKPT_DIR, "%s_%d.npz" % (PREFIX, int(time.time())))
brain.save(final)
final_loss = float(np.mean(losses[-500:])) if losses else -1.0
print("💾 FINAL saved: %s | steps: %d | loss: %.4f"
      % (os.path.basename(final), step, final_loss), flush=True)

print("\n🪄 KHUD-SOCH SAMPLES (apna dimagh):", flush=True)
for q in ("salam", "Ilm kya hai", "what is code", "fibonacci steps",
          "coding rules", "Quran parho", "kya haal hai", "what is an api",
          "how to make a racing car game", "what is a neural network"):
    try:
        p = "\nSawal: " + q + "\nJawab:"
        out = brain.sample(p, tok, max_new=180, temperature=0.5)
        out = out.split("\nSawal:")[0].split("\n")[0].strip()
        print("  [%s] -> %s" % (q, out[:150]), flush=True)
    except Exception as e:
        print("  [%s] sample-fail: %s" % (q, e), flush=True)

try:
    with open(RESULT, "w", encoding="utf-8") as f:
        json.dump({"ok": True,
                   "trainer": "deep5h",
                   "final": os.path.basename(final),
                   "steps": step, "final_loss": final_loss,
                   "minutes": (time.time() - t_all) / 60.0,
                   "corpus_chars": len(combined),
                   "finished": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
except Exception:
    pass
print("\n🏁 DEEP 3-GHANTAY (180-MIN) TRAINING MUKAMMAL: %.1f min | steps: %d"
      % ((time.time() - t_all) / 60.0, step), flush=True)

# ============================================================
# 🚀 AUTO-APPLY: training khatam → sab jagah a→z (zip/repo/sites)
# TRAIN_AUTO_APPLY=0 ho to SKIP — publish-task task-by-task alag-se
# ============================================================
if os.environ.get("TRAIN_AUTO_APPLY", "1") == "0":
    print("\n⏭️ AUTO-APPLY SKIP (TRAIN_AUTO_APPLY=0) — publish-task"
          " alag-se honge", flush=True)
else:
    print("\n🚀 AUTO-APPLY: _apply_training_everywhere.py chal raha hai…", flush=True)
    try:
        r = subprocess.run([sys.executable, "-Xutf8",
                            r"D:\DigitalBrain\_apply_training_everywhere.py"],
                           cwd=r"D:\DigitalBrain", timeout=3600)
        print("🚀 AUTO-APPLY finished (rc=%s)" % r.returncode, flush=True)
    except Exception as e:
        print("🚀 AUTO-APPLY FAIL: %s — APPLY-TRAINING-EVERYWHERE.bat se"
              " khud chalao" % e, flush=True)
