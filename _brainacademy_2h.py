# -*- coding: utf-8 -*-
"""
HEMEMO BRAIN ACADEMY - 2-hour honest trainer (append-only, no deletions).

Tracks:
  A) corpus ingest (append-only) into BOTH DigitalBrain (owner) AND the
     People package copy ("virtual system" - users have no DigitalBrain).
  B) micro-training of the matching hemomaster checkpoint (vocab-match);
     bounded by wall clock; periodic epoch saves as NEW files (never delete).
  C) honest report: corpus counts before/after, checkpoints, sha256.

Rules honored:
  - no API / no cloud / no external AI (numpy + local files only)
  - never deletes previous information/data (append-only + new files)
  - Phase B starts ONLY when the sentinel _GO_TRAIN file exists
    (video-QA must run on a quiet CPU first for honest wall-times).
"""
import hashlib
import json
import os
import shutil
import sys
import time

sys.path.insert(0, r"D:\DigitalBrain")

ROOT_A = r"D:\DigitalBrain"
ROOT_B = r"D:\HemomemoUltra-People"          # user package copy ("virtual system")
GO_SENTINEL = os.path.join(ROOT_A, "_GO_TRAIN")
LOG = os.path.join(ROOT_A, "_brainacademy_2h.log")
BUDGET_S = 7200.0                            # 2 hours hard wall
EPOCH_EVERY = 600.0                          # save a checkpoint every 10 min

def log(s):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), s)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def sh_file(root):
    return os.path.join(root, "data", "corpus_big", "trainer_knowledge_2h.txt")

def corpus_lines(root):
    p = sh_file(root)
    if not os.path.exists(p):
        return []
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        return [ln.strip() for ln in f if ln.strip()]

# ---------------------------------------------------------------- phase A
def phase_a():
    log("PHASE-A ingest (append-only, both roots)")
    src = corpus_lines(ROOT_A)
    log("owner corpus lines: %d" % len(src))
    # learn() into owner memory so episodic + tasksも index gets them
    from agent.tasks import TaskSystem
    from model.memory import EpisodicStore
    mem = EpisodicStore(os.path.join(ROOT_A, "data"))
    ts = TaskSystem(mem, sh_file(ROOT_A))
    learned = 0
    t00 = time.time()
    for ln in src:
        if ln.startswith("Sawal:"):
            cur_q = ln[6:].strip()
        elif ln.startswith("Jawab:") and cur_q:
            try:
                ts.learn(cur_q, ln[6:].strip())
                learned += 1
            except Exception as e:
                log("learn err: %r" % e)
            cur_q = None
    log("phase-A owner learn(): %d pairs in %.0fs" % (learned, time.time() - t00))
    # mirror into People package (users' virtual system): append missing lines
    tgt = corpus_lines(ROOT_B)
    add = [ln for ln in src if ln not in set(tgt)]
    os.makedirs(os.path.dirname(sh_file(ROOT_B)), exist_ok=True)
    with open(sh_file(ROOT_B), "a", encoding="utf-8") as f:
        f.write("\n".join(add) + "\n" if add else "")
    log("phase-A people copy: +%d lines (append-only)" % len(add))
    return learned

# ---------------------------------------------------------------- phase B
def phase_b():
    from model.generate import _tok, corpus_text
    from model.nn import LSTMBrain
    import numpy as np

    data_dir = os.path.join(ROOT_A, "data")
    CK = os.path.join(ROOT_A, "model", "checkpoints")
    tok = _tok()
    log("phase-B vocab=%d" % tok.vocab_size)
    # pick matching checkpoint (newest matching vocab; fail-closed)
    cks = [os.path.join(CK, f) for f in os.listdir(CK)
           if f.startswith("hemomaster") and f.endswith(".npz")
           and not f.endswith(".tmp.npz")
           and ".tmp." not in f]
    cks.sort(key=os.path.getmtime, reverse=True)
    pick = None
    for c in cks:
        with np.load(c) as d:
            v = int(d["embed"].shape[0])
        if v == tok.vocab_size:
            pick = c
            break
        log("phase-B skip %s (vocab %d)" % (os.path.basename(c), v))
    if pick is None:
        log("phase-B ABORT: no vocab-matched hemomaster")
        return
    h = int(np.load(pick)["embed"].shape[1])
    brain = LSTMBrain(tok.vocab_size, d_h=h)
    brain.load(pick)
    brain.lr = 0.004
    log("phase-B resume from %s (vocab %d, dh %d)" % (os.path.basename(pick),
                                                      tok.vocab_size, h))
    # rebuild windows from the GROWN corpus (trainer file + all corpus files)
    import re as _re
    raw = ""
    big = os.path.join(ROOT_A, "data", "corpus_big")
    parts = [os.path.join(ROOT_A, "data", "corpus.txt")]
    if os.path.isdir(big):
        parts += [os.path.join(big, f) for f in sorted(os.listdir(big))
                  if f.endswith(".txt")]
    for p in parts:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                raw += "\n\n" + f.read().strip()
    if any(ord(c) > 127 for c in raw):
        raw = raw.encode("ascii", "ignore").decode("ascii")
    ids = tok.encode(raw)
    SEQ = 96
    STEP_STRIDE = 48
    wins = [ids[i:i + SEQ + 1]
            for i in range(0, len(ids) - SEQ - 1, STEP_STRIDE)]
    log("phase-B windows: %d from %d chars" % (len(wins), len(raw)))
    rng = np.random.default_rng(77)
    nstep = 0
    losses = []
    epoch_saved = 0
    last_epoch = None
    train_t0 = None                             # wall-budget starts at REAL training
    while True:
        if train_t0 is None and not os.path.exists(GO_SENTINEL):
            log("phase-B wait: _GO_TRAIN sentinel nahi (video-QA pehle)")
            time.sleep(60)
            continue
        if train_t0 is None:
            train_t0 = time.time()
            last_epoch = train_t0
        if time.time() - train_t0 > BUDGET_S:
            log("phase-B wall budget reached")
            break
        try:
            loss = brain.train_step(wins[rng.integers(0, len(wins))])
            losses.append(float(loss))
            nstep += 1
        except Exception as e:
            # window ko chhoda honestly (data-serious begrer)
            log("phase-B step skip: %r" % (e,))
            continue
        if time.time() - last_epoch >= EPOCH_EVERY:
            ep = os.path.join(CK, "hemomaster_%d.npz" % int(time.time()))
            brain.save(ep)
            epoch_saved += 1
            last_epoch = time.time()
            log("phase-B epoch saved: %s (steps=%d, loss=%.4f)" %
                (os.path.basename(ep), nstep,
                 sum(losses[-200:]) / max(1, len(losses[-200:]))))
        if nstep % 100 == 0 and nstep:
            log("phase-B step %d loss %.4f (%.0fs)" %
                (nstep, sum(losses[-100:]) / max(1, len(losses[-100:])),
                 time.time() - train_t0))
    fin = os.path.join(CK, "hemomaster_%d.npz" % int(time.time()))
    try:
        brain.save(fin)
    except Exception as e:
        fin = pick
        log("final save err: %r" % e)
    log("phase-B done: steps=%d final=%s epochs=%d" %
        (nstep, os.path.basename(fin), epoch_saved))
    return fin

# ---------------------------------------------------------------- phase C
def phase_c(fin):
    log("PHASE-C apply everywhere")
    # 1) new brain (vocab-matched) into People copy - append, no replace
    if fin:
        dst = os.path.join(ROOT_B, "model", "checkpoints",
                           os.path.basename(fin))
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(fin, dst)
            log("phase-C people brain: %s (sha256 %s...)" % (dst, sha256(dst)[:12]))
        except Exception as e:
            log("phase-C brain copy err: %r" % e)
    # 2) corpus diff already appended in phase-A; verify
    log("phase-C people corpus lines: %d" % len(corpus_lines(ROOT_B)))
    # 3) report file
    rep = os.path.join(ROOT_A, "_brainacademy_report.json")
    with open(rep, "w", encoding="utf-8") as f:
        json.dump({"trainer_knowledge_lines": len(corpus_lines(ROOT_A)),
                   "log": LOG,
                   "final": fin,
                   "wall_budget_s": BUDGET_S}, f, indent=1)
    log("PHASE-C DONE (report: %s)" % rep)

if __name__ == "__main__":
    log("=== HEMEMO BRAIN ACADEMY 2H START ===")
    phase_a()
    fin = phase_b()
    if os.path.exists(GO_SENTINEL):
        os.remove(GO_SENTINEL)
    phase_c(fin)
    log("=== BRAIN ACADEMY DONE ===")
