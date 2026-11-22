"""
🎓 train.py — Hemomemo AI ka Rozgaar (Training Loop, PURE LOCAL)

Corpus se char sequences bana kar LSTM ko backprop se train karta hai.
Koi API, koi cloud, koi key NAHI. Checkpoints model/checkpoints me save.
"""
import os
import time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sysdir = os.path.dirname(HERE)
os.chdir(sysdir)
import sys
sys.path.insert(0, sysdir)

from model.tokenizer import CharTokenizer  # noqa: E402
from model.nn import LSTMBrain             # noqa: E402

DATA_PATH = os.path.join(HERE, "..", "data", "corpus.txt")
CKPT_DIR = os.path.join(HERE, "checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)


def build_dataset(seq_len: int = 24, stride: int = 6):
    tok = CharTokenizer()
    with open(DATA_PATH, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    ids = tok.encode("\n\n" + text + "\n\n")
    seqs = [ids[i:i + seq_len + 1] for i in range(0, len(ids) - seq_len - 1, stride)]
    return tok, seqs


def train(steps: int = 400, seq_len: int = 24, d_h: int = 128,
          resume: bool = True, verbose_every: int = 50):
    tok, seqs = build_dataset(seq_len)
    brain = LSTMBrain(tok.vocab_size, d_h=d_h)
    ckpts = sorted([f for f in os.listdir(CKPT_DIR) if f.startswith("hemomemo") and f.endswith(".npz")])
    if resume and ckpts:
        brain.load(os.path.join(CKPT_DIR, ckpts[-1]))
        print(f"↩️  Resume: {ckpts[-1]}")
    print(f"🎓 Hemomemo training start | vocab {tok.vocab_size} | seqs {len(seqs)} | steps {steps}")
    rng = np.random.default_rng(7)
    t0 = time.time()
    running = []
    for s in range(1, steps + 1):
        ids = seqs[rng.integers(0, len(seqs))]
        loss = brain.train_step(ids)
        running.append(loss)
        if s % verbose_every == 0 or s == steps:
            el = time.time() - t0
            print(f"  step {s:4d} | loss {np.mean(running[-verbose_every:]):.4f} | {el:.0f}s")
    path = os.path.join(CKPT_DIR, f"hemomemo_{int(time.time())}.npz")
    brain.save(path)
    tok.save(os.path.join(CKPT_DIR, "vocab.json"))
    print(f"💾 Saved checkpoint: {path}")
    # sample demo
    sample = brain.sample("Main Hemomemo hoon", tok, max_new=90)
    print("✍️ Sample:", sample.replace("\n", " | "))
    return brain, tok


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--hidden", type=int, default=128)
    a = ap.parse_args()
    train(steps=a.steps, d_h=a.hidden)
