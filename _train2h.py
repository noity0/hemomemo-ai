# -*- coding: utf-8 -*-
"""_train2h.py — TIME-BASED master training (user ka hukum: 2 GHANTAY, sab ilm
+ coding-knowledge ke sath). train_master ki machinery dobara istemal karta hai
(corpus_text, tokenizer, LSTMBrain, archive-qanoon) magar STOP **waqt** par —
har 15-min mid-save, aakhir me FINAL checkpoint + khud-soch samples.
100% OFFLINE — koi API, koi cloud, koi doosra AI NAHI."""
import glob
import json
import os
import shutil
import sys
import time

import numpy as np

sys.path.insert(0, r"D:\DigitalBrain")
os.chdir(r"D:\DigitalBrain")

import scripts.train_master as tm            # noqa: E402  (machinery)
from model.tokenizer import CharTokenizer    # noqa: E402
from model.nn import LSTMBrain               # noqa: E402

BUDGET_S = float(os.environ.get("TRAIN_SECONDS", "7200"))   # 2 ghantay
PREFIX = "hemomaster"
DH = tm.DH                    # 660 — master dimagh (~7M params)
SEQ_LEN = tm.SEQ_LEN

t_all = time.time()
try:
    with open(os.path.join(tm.DATA, "_trainer_pid.json"), "w",
              encoding="utf-8") as f:
        json.dump({"pid": os.getpid(),
                   "started": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "model": PREFIX, "budget_s": BUDGET_S}, f)
except Exception:
    pass

combined, nfiles = tm.corpus_text()
# 💻 CODING-FOCUS (env CODING_FOCUS=1): coding-corpus ko 3x weight — 20-min
# coding-only deep-training (ethical-hacking defensive + agents + full-stack)
if os.environ.get("CODING_FOCUS") == "1":
    cadd = ""
    ncod = 0
    for cf in glob.glob(os.path.join(tm.DATA, "corpus_big", "*coding*.txt")):
        try:
            with open(cf, "r", encoding="utf-8", errors="ignore") as f:
                cadd += f.read() + "\n\n"
            ncod += 1
        except Exception:
            pass
    combined = combined + (cadd * 2)      # asli 1x + ye 2x = 3x weight
    print("💻 CODING-FOCUS: %d coding-files 3x-weight (+%s chars)"
          % (ncod, f"{len(cadd) * 2:,}"), flush=True)
# 🎮 GAMES-FOCUS (env GAMES_FOCUS=1): games/minecraft + live-harvest 3x weight
if os.environ.get("GAMES_FOCUS") == "1":
    gadd = ""
    ngame = 0
    for pat in ("*games*.txt", "harvest_live.txt"):
        for gf in glob.glob(os.path.join(tm.DATA, "corpus_big", pat)):
            try:
                with open(gf, "r", encoding="utf-8", errors="ignore") as f:
                    gadd += f.read() + "\n\n"
                ngame += 1
            except Exception:
                pass
    combined = combined + (gadd * 2)      # asli 1x + ye 2x = 3x weight
    print("🎮 GAMES-FOCUS: %d games/ilm-files 3x-weight (+%s chars)"
          % (ngame, f"{len(gadd) * 2:,}"), flush=True)
print("📚 MASTER corpus: %d files | %s chars (coding-knowledge shamil)"
      % (nfiles, f"{len(combined):,}"), flush=True)
tok = CharTokenizer()
tok.fit_from_scratch(set(combined))
ids = tok.encode("\n\n" + combined + "\n\n")
ids_np = np.asarray(ids, dtype=np.int32)
n_windows = len(ids) - SEQ_LEN - 1
os.makedirs(tm.CKPT_DIR, exist_ok=True)
tok.save(os.path.join(tm.CKPT_DIR, "vocab.json"))
print("🔤 vocab: %d chars | windows: %s" % (tok.vocab_size, f"{n_windows:,}"),
      flush=True)

# 🗄️ archive-qanoon (SIRF EK MODEL) — sirf isi dimagh ke purane checkpoints
os.makedirs(tm.ARCHIVE, exist_ok=True)
for f in glob.glob(os.path.join(tm.CKPT_DIR, "*.npz")):
    base = os.path.basename(f)
    if not base.startswith(PREFIX):
        continue
    if base.startswith("%s_mid" % PREFIX) or base.startswith("%s_chat" % PREFIX):
        continue
    shutil.move(f, os.path.join(tm.ARCHIVE, base))
print("🗄️ purane %s checkpoints -> archive/" % PREFIX, flush=True)

brain = LSTMBrain(tok.vocab_size, d_h=DH, seed=2026)
mid = os.path.join(tm.CKPT_DIR, "%s_mid.npz" % PREFIX)
# 🏆 NEWEST-warm-start: mid aur archive ke final me se JO NAYA ho wahi lo —
# chained-run 2h ke FINAL par build ho (purane mid par nahi)
_cands = []
if os.path.exists(mid):
    _cands.append(mid)
if os.path.isdir(tm.ARCHIVE):
    for _f in glob.glob(os.path.join(tm.ARCHIVE, "%s_*.npz" % PREFIX)):
        _b = os.path.basename(_f)
        if _b.startswith("%s_mid" % PREFIX) or _b.startswith("%s_chat" % PREFIX):
            continue
        _cands.append(_f)
warm = max(_cands, key=os.path.getmtime) if _cands else None
if warm:
    try:
        _d = np.load(warm, mmap_mode="r")
        if (int(_d["embed"].shape[0]) == tok.vocab_size
                and int(_d["embed"].shape[1]) == DH):
            brain.load(warm)     # 🔁 WARM-START: naya-tareen soch
            print("🔁 WARM-START: %s (naya-tareen)" % os.path.basename(warm),
                  flush=True)
        else:
            print("(warm-start shape-mismatch: %s)" % os.path.basename(warm),
                  flush=True)
    except Exception as e:
        print("(warm-start skip: %s)" % e, flush=True)
params = (brain.embed.size + brain.W_out.size + brain.b_out.size +
          sum(L.W.size + L.b.size for L in brain.layers))
print("🧠 HEMOMO-MASTER: %s params (dh%d) | budget: %.0f min"
      % (f"{params:,}", DH, BUDGET_S / 60.0), flush=True)


def sched(frac):
    """LR schedule (elapsed-fraction par — train_master jaisa hi)."""
    if frac <= 0.50:
        return 0.010
    if frac <= 0.75:
        return 0.007
    return 0.004


rng = np.random.default_rng(2026)
deadline = t_all + BUDGET_S
last_mid = t_all
step, losses = 0, []
print("🚀 TARBIYAT SHURU (2 ghantay)…", flush=True)
while time.time() < deadline:
    brain.lr = sched((time.time() - t_all) / BUDGET_S)
    i = int(rng.integers(0, n_windows))
    losses.append(brain.train_step(ids_np[i:i + SEQ_LEN + 1].tolist()))
    step += 1
    if step % 200 == 0:
        print("  step %d | loss %.4f | %.0fs | %.0f min baki"
              % (step, float(np.mean(losses[-200:])), time.time() - t_all,
                 (deadline - time.time()) / 60.0), flush=True)
    if time.time() - last_mid >= 900:        # har 15 min mid-save
        brain.save(mid)
        last_mid = time.time()
        print("  💾 mid-save (step %d) — hifazat ho gayi" % step, flush=True)

final = os.path.join(tm.CKPT_DIR, "%s_%d.npz" % (PREFIX, int(time.time())))
brain.save(final)
print("💾 FINAL saved: %s | steps: %d | loss: %.4f"
      % (os.path.basename(final), step, float(np.mean(losses[-500:]))),
      flush=True)

print("\n🪄 KHUD-SOCH SAMPLES (apna dimagh, template nahi):", flush=True)
for q in ("salam", "Ilm kya hai", "what is code", "fibonacci steps",
          "coding rules", "Quran parho", "kya haal hai", "what is an api"):
    p = "\nSawal: " + q + "\nJawab:"
    out = brain.sample(p, tok, max_new=180, temperature=0.5)
    out = out.split("\nSawal:")[0].split("\n")[0].strip()
    print("  [%s] -> %s" % (q, out[:150]), flush=True)

print("\n🏁 2-HOUR TRAINING MUKAMMAL: %.1f min | steps: %d"
      % ((time.time() - t_all) / 60.0, step), flush=True)
