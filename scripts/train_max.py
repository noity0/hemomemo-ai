"""
🧠 train_max.py — HEMOMO-MAX FINAL TRAINER (sirf EK model, 100% offline)

Kya karta hai:
 1. data/corpus.txt + data/corpus_big/*.txt mila kar barа corpus banaata hai
 2. Poore corpus se fresh tokenizer banata hai → checkpoints/vocab.json
 3. Purane checkpoints archive/ me chala deta hai (rule: SIRF EK MODEL)
 4. Naya 2M-param model (dh352, 2 layers) HEMOMO-MAX tarbiyat deta hai
 5. Step 2400 par intermediate save (tab bhi chat try kar sakte hain)
 6. Aakhir me Sawal/Jawab samples print karta hai

Run:  python scripts\train_max.py
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

STEPS = 4800
SEQ_LEN, STRIDE = 32, 6


def corpus_text():
    """Sab knowledge files mila kar combined corpus banao."""
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
    print(f"🔤 vocab: {tok.vocab_size} chars | training windows: {len(seqs):,}", flush=True)

    os.makedirs(ARCHIVE, exist_ok=True)
    for f in glob.glob(os.path.join(CKPT_DIR, "*.npz")):
        shutil.move(f, os.path.join(ARCHIVE, os.path.basename(f)))
    print("🗄️ purane checkpoints -> archive/ (SIRF EK MODEL rule)", flush=True)

    brain = LSTMBrain(tok.vocab_size, d_h=352, seed=1500)
    params = brain.embed.size + brain.W_out.size + brain.b_out.size + sum(
        L.W.size + L.b.size for L in brain.layers)
    brain.lr = 0.01
    print(f"🧠 HEMOMO-MAX params: {params:,} (dh352, 2 layers, NumPy)", flush=True)

    def sched(s):
        if s <= 2400:
            return 0.010
        if s <= 3600:
            return 0.007
        return 0.004

    rng = np.random.default_rng(101)
    t0, running = time.time(), []
    mid = None
    for s in range(1, STEPS + 1):
        brain.lr = sched(s)
        loss = brain.train_step(seqs[rng.integers(0, len(seqs))])
        running.append(loss)
        if s % 200 == 0:
            print(f"  step {s} | loss {np.mean(running[-200:]):.4f} | {time.time()-t0:.0f}s", flush=True)
        if s == 2400:
            mid = os.path.join(CKPT_DIR, "hemomax_mid.npz")
            brain.save(mid)
            print("  💾 intermediate save (chat try karein: python model\\generate.py)", flush=True)

    final = os.path.join(CKPT_DIR, f"hemomax_{int(time.time())}.npz")
    brain.save(final)
    if mid and os.path.exists(mid):
        shutil.move(mid, os.path.join(ARCHIVE, os.path.basename(mid)))
    print(f"💾 FINAL HEMOMO-MAX saved: {final}", flush=True)
    print(f"📊 final loss: {np.mean(running[-500:]):.4f}", flush=True)

    print("\n🪄 SAMPLES (Sawal/Jawab):", flush=True)
    for q in ["salam", "Aap ka naam kya hai", "Ilm kya hai", "Dil pareshan hai", "Quran parho"]:
        p = "\nSawal: " + q + "\nJawab:"
        out = brain.sample(p, tok, max_new=180, temperature=0.5)
        out = out.split("\nSawal:")[0].split("\n")[0].strip()
        print(f"  [{q}] -> {out}", flush=True)


if __name__ == "__main__":
    main()
