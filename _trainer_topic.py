# -*- coding: utf-8 -*-
"""
_trainer_topic.py — TOPIC-trainer (1 focused corpus, honest wall-budget).

100% local: numpy + local files only. No API, no cloud, no external AI.
Append-only: epoch saves are NEW files (never delete/rename old ones).
Usage:
  py -3 -u -X utf8 _trainer_topic.py --corpus a.txt,b.txt --budget 1200 \
      --epoch 300 --prefix hemomaster_codevid --log _x.log --jsonout _x.json
"""
import argparse
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, r"D:\DigitalBrain")
ROOT = r"D:\DigitalBrain"
_LOGH = None


def log(s):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), s)
    print(line, flush=True)
    with open(_LOGH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    global _LOGH
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--budget", type=float, default=1200.0)
    ap.add_argument("--epoch", type=float, default=300.0)
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--jsonout", required=True)
    a = ap.parse_args()
    _LOGH = a.log

    from model.generate import _tok
    from model.nn import LSTMBrain
    import numpy as np

    tok = _tok()
    V = tok.vocab_size
    CK = os.path.join(ROOT, "model", "checkpoints")
    cks = [os.path.join(CK, f) for f in os.listdir(CK)
           if f.startswith("hemomaster") and f.endswith(".npz")
           and ".tmp." not in f]
    cks.sort(key=os.path.getmtime, reverse=True)
    pick = None
    for c in cks:
        with np.load(c) as d:
            v = int(d["embed"].shape[0])
        if v == V:
            pick = c
            break
        log("skip %s (vocab %d)" % (os.path.basename(c), v))
    if pick is None:
        log("ABORT: koi vocab-matched hemomaster nahi (fail-closed)")
        sys.exit(1)
    h = int(np.load(pick)["embed"].shape[1])
    brain = LSTMBrain(V, d_h=h)
    brain.load(pick)
    brain.lr = 0.004
    log("topic-trainer %s | base=%s vocab=%d d_h=%d lr=0.004" %
        (a.prefix, os.path.basename(pick), V, h))

    raw = ""
    for p in a.corpus.split(","):
        p = p.strip()
        if p and os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                raw += "\n\n" + f.read().strip()
        else:
            log("corpus missing: %s" % p)
    raw = raw.encode("ascii", "ignore").decode("ascii")
    ids = tok.encode(raw)
    SEQ, STRIDE = 96, 48
    wins = [ids[i:i + SEQ + 1]
            for i in range(0, len(ids) - SEQ - 1, STRIDE)]
    log("windows=%d from %d chars | budget=%.0fs epoch=%.0fs" %
        (len(wins), len(raw), a.budget, a.epoch))
    if not wins:
        log("ABORT: koi window nahi bani (empty corpus)")
        sys.exit(1)

    rng = np.random.default_rng(101)
    steps, losses, saved = 0, [], []
    t0 = time.time()
    last_ep = t0
    while time.time() - t0 < a.budget:
        try:
            loss = brain.train_step(wins[rng.integers(0, len(wins))])
            losses.append(float(loss))
        except Exception as e:
            log("step skip: %r" % (e,))
            continue
        steps += 1
        if time.time() - last_ep >= a.epoch:
            ep = os.path.join(CK, "%s_%d.npz" % (a.prefix, int(time.time())))
            brain.save(ep)
            saved.append(ep)
            last_ep = time.time()
            log("epoch saved: %s (steps=%d loss=%.4f)" %
                (os.path.basename(ep), steps,
                 sum(losses[-200:]) / max(1, len(losses[-200:]))))
        if steps % 200 == 0 and steps:
            log("step %d loss %.4f (%.0fs/%.0fs)" %
                (steps, sum(losses[-100:]) / max(1, len(losses[-100:])),
                 time.time() - t0, a.budget))
    fin = os.path.join(CK, "%s_%d.npz" % (a.prefix, int(time.time())))
    brain.save(fin)
    wall = time.time() - t0
    log("TOPIC-DONE %s steps=%d wall=%.0fs final=%s epochs=%d" %
        (a.prefix, steps, wall, os.path.basename(fin), len(saved) + 1))
    json.dump({"prefix": a.prefix, "base": pick, "final": fin,
               "steps": steps, "wall_s": wall, "vocab": V, "d_h": h,
               "avg_loss_last100": sum(losses[-100:]) /
                                    max(1, len(losses[-100:])),
               "epochs": saved + [fin],
               "corpus": a.corpus,
               "sha256": {os.path.basename(fin): sha256(fin)[:16]}},
              open(a.jsonout, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
