"""
🧬 upgrade_max.py — HEMOMO-MAX UPGRADE (dh448, ~3.28M params, bara corpus)

train_max.py ke aage ka upgrade:
  - corpus: data/corpus.txt + data/corpus_big/* (ab takreeban 45KB)
  - hidden 352 -> 448 (params ~3.28M)
  - 6000 steps, mid saves @1500 aur @4000
  - aakhir me sirf EK checkpoint rehta hai, purane archive/ me chale jate hain

Run:  python scripts\\upgrade_max.py
NOTE: No API, No Ollama, No internet — pure NumPy, sab local.
"""
import glob
import os
import shutil
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from model.tokenizer import CharTokenizer  # noqa: E402
from model.nn import LSTMBrain             # noqa: E402

DATA = os.path.join(ROOT, "data")
BIG = os.path.join(DATA, "corpus_big")
CKPT_DIR = os.path.join(ROOT, "model", "checkpoints")
ARCHIVE = os.path.join(CKPT_DIR, "archive")

STEPS = 6000
SEQ_LEN, STRIDE = 32, 6
DH = 448
MID1, MID2 = 1500, 4000


def corpus_text():
    paths = [os.path.join(DATA, "corpus.txt")]
    if os.path.isdir(BIG):
        paths += [os.path.join(BIG, f) for f in sorted(os.listdir(BIG)) if f.endswith(".txt")]
    parts, n = [], 0
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                parts.append(f.read().strip())
            n += 1
    return "\n\n".join(parts), n


def main():
    combined, nfiles = corpus_text()
    print(f"📚 corpus: {nfiles} files | {len(combined):,} chars", flush=True)

    bad = sorted({c for c in combined if ord(c) > 127})
    if bad:
        print(f"⚠️ non-ASCII chars ({len(bad)}): {[hex(ord(c)) for c in bad[:12]]}", flush=True)
    else:
        print("✅ corpus pure ASCII hai", flush=True)

    tok = CharTokenizer()
    tok.fit_from_scratch(set(combined))
    ids = tok.encode("\n\n" + combined + "\n\n")
    seqs = [ids[i:i + SEQ_LEN + 1] for i in range(0, len(ids) - SEQ_LEN - 1, STRIDE)]
    os.makedirs(CKPT_DIR, exist_ok=True)
    tok.save(os.path.join(CKPT_DIR, "vocab.json"))
    print(f"🔤 vocab: {tok.vocab_size} chars | windows: {len(seqs):,}", flush=True)

    os.makedirs(ARCHIVE, exist_ok=True)
    for f in glob.glob(os.path.join(CKPT_DIR, "*.npz")):
        shutil.move(f, os.path.join(ARCHIVE, os.path.basename(f)))
    print("🗄️ purane checkpoints -> archive/", flush=True)

    brain = LSTMBrain(tok.vocab_size, d_h=DH, seed=2027)
    params = brain.embed.size + brain.W_out.size + brain.b_out.size + sum(
        L.W.size + L.b.size for L in brain.layers)
    brain.lr = 0.01
    print(f"🧠 HEMOMO-MAX UPGRADE params: {params:,} (dh{DH}, 2 layers, NumPy)", flush=True)

    def sched(s):
        if s <= 2400:
            return 0.010
        if s <= 4200:
            return 0.007
        return 0.004

    rng = np.random.default_rng(101)
    t0, running = time.time(), []
    mids = {}
    for s in range(1, STEPS + 1):
        brain.lr = sched(s)
        loss = brain.train_step(seqs[rng.integers(0, len(seqs))])
        running.append(loss)
        if s % 200 == 0:
            print(f"  step {s} | loss {np.mean(running[-200:]):.4f} | {time.time()-t0:.0f}s", flush=True)
        for name, at in (("hemomax_up_mid1.npz", MID1), ("hemomax_up_mid2.npz", MID2)):
            if s == at:
                mids[name] = os.path.join(CKPT_DIR, name)
                brain.save(mids[name])
                print(f"  💾 {name} saved (chat try karein: python model\\generate.py)", flush=True)

    final = os.path.join(CKPT_DIR, f"hemomax_up_{int(time.time())}.npz")
    brain.save(final)
    for name, p in mids.items():
        if os.path.exists(p):
            shutil.move(p, os.path.join(ARCHIVE, name))
    print(f"💾 FINAL HEMOMO-MAX (upgraded): {final}", flush=True)
    print(f"📊 final loss: {np.mean(running[-500:]):.4f}", flush=True)

    print("\n🪄 SAMPLES:", flush=True)
    for q in ["salam", "Aap ka naam kya hai", "Ilm kya hai", "Dil pareshan hai", "STDP kya hai"]:
        p = "\nSawal: " + q + "\nJawab:"
        out = brain.sample(p, tok, max_new=180, temperature=0.5)
        out = out.split("\nSawal:")[0].split("\n")[0].strip()
        print(f"  [{q}] -> {out}", flush=True)


if __name__ == "__main__":
    main()
