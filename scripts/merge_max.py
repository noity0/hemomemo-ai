"""
🧬 merge_max.py — HEMOMO-MAX BUILDER (single final model)

Kya karta hai:
 1. Hemomemo-5.0 (dh192) + GenTwo-2M (dh352) ke weights ko ek container
    (HEMOMO-MAX: dh352, 2 layers, ~2.02M params) me BLEND karta hai
 2. Agar GenTwo-2M abhi train ho raha hai to namumkin 30 sec ke gap se
    ka intakez karta hai (max 30 min)
 3. Phir HEMOMO-MAX ko 4500 steps aur tarbiyat deta hai
 4. checkpoints/ me sirf HEMOMO-MAX rehta hai — purane archive/ me chale jaate
 5. Salam/'Main HMHS'/'Ilm' ke samples dega

NOTE: ye "combine" weight-blending hai (model fusion), full transfer ain
nahi — dh192 weights ko upsample karke dh352 me dala jata hai.
"""
import sys, os, time, glob, json, shutil
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # D:\DigitalBrain
os.chdir(HERE)
sys.path.insert(0, HERE)

from model.tokenizer import CharTokenizer
from model.nn import LSTMBrain
from model.train import build_dataset, CKPT_DIR

ARCHIVE = os.path.join(CKPT_DIR, "archive")
os.makedirs(ARCHIVE, exist_ok=True)

def find(predicate):
    return sorted(glob.glob(os.path.join(CKPT_DIR, predicate)))

def wait_for(pattern, max_minutes=30):
    """GenTwo-2M ka intezar (deep-learning job finish hone taak)."""
    deadline = time.time() + max_minutes * 60
    while time.time() < deadline:
        fs = find(pattern)
        if fs:
            return fs[-1]
        print(f"⏳ {pattern} ka intezar... ({int((deadline-time.time())/60)} min bache)", flush=True)
        time.sleep(30)
    return None

def blend_old_into(brain, old, w=0.3):
    """Shape-safe upsample-blend: old weights ko tile karke naye me milao."""
    # layers
    for i in range(2):
        oldW = old.layers[i].W
        rows = int(np.ceil(brain.layers[i].W.shape[0] / oldW.shape[0]))
        cols = int(np.ceil(brain.layers[i].W.shape[1] / oldW.shape[1]))
        tiled = np.tile(oldW, (rows, cols))[: brain.layers[i].W.shape[0], : brain.layers[i].W.shape[1]]
        brain.layers[i].W = (1 - w) * brain.layers[i].W + w * tiled
    # embed (same vocab, dh differs)
    cols = int(np.ceil(brain.embed.shape[1] / old.embed.shape[1]))
    tiledE = np.tile(old.embed, (1, cols))[:, : brain.embed.shape[1]]
    brain.embed = (1 - w) * brain.embed + w * tiledE

def blend2m_into(brain, src2m, w=0.5):
    """Same-shape dh352 donor seedha blend (GenTwo-2M)."""
    import copy
    donor = LSTMBrain(brain.vocab, d_h=352).load(src2m)
    for i in range(2):
        brain.layers[i].W = (1 - w) * brain.layers[i].W + w * donor.layers[i].W
        brain.layers[i].b = (1 - w) * brain.layers[i].b + w * donor.layers[i].b
    brain.embed = (1 - w) * brain.embed + w * donor.embed
    brain.W_out = (1 - w) * brain.W_out + w * donor.W_out
    brain.b_out = (1 - w) * brain.b_out + w * donor.b_out


def main():
    # 0) tokenizer (corpus-se hi bana, koi mismatch)
    tok = CharTokenizer()  # corpus-based fresh vocab
    with open(os.path.join(HERE, "data", "corpus.txt"), encoding="utf-8", errors="ignore") as f:
        corpus = f.read()
    ids_check = tok.encode(corpus)
    tok.save(os.path.join(CKPT_DIR, "vocab.json"))
    print(f"🔤 vocab rebuilt: {tok.vocab_size} chars", flush=True)

    # 1) GenTwo-2M ka wait
    src2m = wait_for("gen2m_*.npz", max_minutes=35)
    print("🧩 donors:", flush=True)

    # 2) HEMOMO-MAX container
    brain = LSTMBrain(tok.vocab_size, d_h=352, seed=3131)  # fresh start

    # 3) blend GenTwo-2M (same shape, high trust: 0.5)
    if src2m:
        print(f"   GenTwo-2M : {os.path.basename(src2m)} → blend 0.50", flush=True)
        blend2m_into(brain, src2m, w=0.5)
    else:
        print("   GenTwo-2M nahi mila — fresh-only", flush=True)

    # 4) blend Hemomemo-5.0 (dh192, less trust: 0.2)
    g5 = find("hemomemo_*.npz")
    if g5:
        src5 = max(g5, key=os.path.getmtime)
        print(f"   Hemomemo-5.0: {os.path.basename(src5)} → blend 0.20", flush=True)
        # IMPORTANT: old vocab (63 chars) se load
        d = np.load(src5)
        vsize_old = d["embed"].shape[0]
        old = LSTMBrain(vsize_old, d_h=192).load(src5)
        # agar vocab size badha hai: embed tile rows太多的manual handling — plain blend skip if size differs
        if vsize_old == tok.vocab_size:
            blend_old_into(brain, old, w=0.2)
        else:
            # vocab-mismatch: layer-W hi blend karte (vocab-neutral) + embed fresh
            for i in range(2):
                oldW = old.layers[i].W
                rows = int(np.ceil(brain.layers[i].W.shape[0] / oldW.shape[0]))
                cols = int(np.ceil(brain.layers[i].W.shape[1] / oldW.shape[1]))
                tiled = np.tile(oldW, (rows, cols))[: brain.layers[i].W.shape[0], :brain.layers[i].W.shape[1]]
                brain.layers[i].W = 0.8 * brain.layers[i].W + 0.2 * tiled
            print("   (vocab mismatch: embed blend skip, sirf layer-W blend)", flush=True)

    # 5) final training HEMOMO-MAX
    _, seqs = build_dataset(seq_len=28, stride=4)
    rng = np.random.default_rng(999)
    t0, running = time.time(), []
    print("🏋️ HEMOMO-MAX training start (4500 steps)...", flush=True)
    for s in range(1, 4501):
        ids = seqs[rng.integers(0, len(seqs))]
        if s > 3500:
            brain.lr = 0.004
        loss = brain.train_step(ids)
        running.append(loss)
        if s % 750 == 0:
            print(f"  MAX step {s} | loss {np.mean(running[-750:]):.4f} | {time.time()-t0:.0f}s", flush=True)

    # 6) save + archive purane
    src_keep = os.path.join(CKPT_DIR, f"hemomax_{int(time.time())}.npz")
    brain.save(src_keep)
    tok.save(os.path.join(CKPT_DIR, "vocab.json"))
    for oldf in glob.glob(os.path.join(CKPT_DIR, "gen*.npz")):
        if oldf != src_keep:
            shutil.move(oldf, os.path.join(ARCHIVE, os.path.basename(oldf)))
    print(f"\n💾 HEMOMO-MAX saved: {src_keep}", flush=True)
    print(f"📁 Old checkpoints moved to: archive/", flush=True)
    params = brain.embed.size + brain.W_out.size + brain.b_out.size + sum(L.W.size + L.b.size for L in brain.layers)
    print(f"🧠 Params: {params:,} | (dh=352, layers=2)", flush=True)

    # 7) samples
    print("\n🪄 SAMPLES:", flush=True)
    for q in ["Salam dost", "Main HMHS", "Ilm farz", "Aap ka naam"]:
        out = brain.sample(q, tok, max_new=140, temperature=0.5).replace("\n", " ")
        print(f"  [{q}] -> {out}", flush=True)


if __name__ == "__main__":
    main()
