r"""
🧠 train_master.py — HEMOMO-MASTER TRAINER (50M params, 100% OFFLINE)

Upgrade kaam (no API, no cloud, no Ollama, kisi doosre AI se koi rabta NAHI):
  1. data/corpus.txt + data/corpus_big/*.txt (Quran + 7 Hadith English corpus
     + poora ilm) mila kar MASTER corpus banata hai
  2. Poore master corpus se FRESH tokenizer → checkpoints/vocab.json
  3. Purane checkpoints archive/ me (SIRF EK MODEL qanoon)
  4. Naya HEMOMO-MASTER model: dh=1739, 2 layers = 50,014,104 params (NumPy float32)
  5. Lambi tarbiyat: STEPS me LR schedule (0.010 → 0.007 → 0.004),
     har 1000 step par intermediate save + live sample (khud-soch ka saboot)
  6. Aakhir me kai Sawal samples (template nahi — model khud likhta hai)

Run:  python scripts\train_master.py           # default 8000 steps
      python scripts\train_master.py 12000     # bada round
NOTE: Pure NumPy BPTT. Sab kuch is PC par — koi bahar connection nahi.
"""
import glob
import json
import os
import re
import shutil
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from model.tokenizer import CharTokenizer  # noqa: E402
from model.nn import LSTMBrain             # noqa: E402

DATA = os.path.join(ROOT, "data")
BIG = os.path.join(DATA, "corpus_big")
CKPT_DIR = os.path.join(ROOT, "model", "checkpoints")
ARCHIVE = os.path.join(CKPT_DIR, "archive")

DH = 1739           # 🚀 MASTER 50M target: 16*1739^2 + 8*1739 + 2*464*1739 + 464 = 50,014,104
DH_HELPER = 560     # 🤝 helper 5.1M | DH_VERIFY = 560 tasdeeq (same formula)
SEQ_LEN = 32        # windows RAM-light: numpy array + random index (koi copies nahi)


def corpus_text():
    """Sab knowledge files mila kar MASTER corpus.
    🚫 VOLATILE files exclude: liveresearch.txt — yeh research-jawab ka
    running NOOT hai (web ke Urdu/Hindi kachre se non-ASCII ghus javata
    hai → vocab bigadta hai aur warm-resume kharab hota). Ye SIRF chat-yaad
    (retrieval) ke liye hai — training corpus pak ASCII rehta hai."""
    paths = [os.path.join(DATA, "corpus.txt")]
    if os.path.isdir(BIG):
        paths += [os.path.join(BIG, f) for f in sorted(os.listdir(BIG))
                  if f.endswith(".txt")]
    blocked = {"liveresearch.txt"}
    parts, n = [], 0
    for p in paths:
        base = os.path.basename(p).lower()
        if base in blocked:
            continue
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                parts.append(f.read().strip())
            n += 1
    text = "\n\n".join(parts)
    # 🧼 SANITIZE: sirf azad-vocab chars rakho (ASCII + newline) —
    # kisi bhi naya gair-standard char (emoji/Devanagari/vichitra/em-dash)
    # vocab me ghuste hi nahi → checkpoint-vocab HAMESHA compatible
    # (generate.corpus_text() bhi yahi ASCII-strip karta hai — 91 chars match)
    allowed = re.compile(r"[^\x20-\x7e\n]")
    text = allowed.sub(" ", text)
    text = re.sub(r"[ \t]{3,}", "  ", text)
    return text, n


def main(steps: int = 8000, dh: int = None, deep: bool = False,
         helper: bool = False, verify: bool = False):
    """deep=True → DUSRA dimagh (dh620 ~6.25M) hemodeep_*.npz — pehle brain
    (hemomaster = pehla 50M dimagh | hemodeep = dusra rescue | hemohelper =
    madadgar | hemoverify = research-tasdeeq — sab bridge: 2M tissues)."""
    t_all = time.time()
    # 🧠🧠🧠🧠 CHAAR-DIMAGH NETWORK (sab aapas me jure — core/hub bridge):
    #   hemomaster = pehla dimagh (DH=1739 ~50M) | hemodeep = dusra rescue
    #   hemohelper = madadgar (560 ~5.1M) | hemoverify = tasdeeq-kar (560 ~5.1M)
    dh = int(dh or (620 if deep else (560 if (helper or verify) else DH)))
    if deep:
        prefix = "hemodeep"
    elif helper:
        prefix = "hemohelper"
    elif verify:
        prefix = "hemoverify"
    else:
        prefix = "hemomaster"
    # ❤️-safety: apna pid likho — heart isko dekh kar trainer active samajhta
    # hai aur consolidation ko rok deta hai (CPU-ko-do-hath-e-mehnat nahi)
    try:
        with open(os.path.join(DATA, "_trainer_pid.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"pid": os.getpid(),
                       "started": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "model": prefix}, f)
    except Exception:
        pass
    combined, nfiles = corpus_text()

    # agar hadith corpus files abhi aa rahi hain (installer background) —
    # phir bhi jahan tak content maujood hai utna he master ilm hai
    print("📚 MASTER corpus: %d files | %s chars" % (nfiles, f"{len(combined):,}"),
          flush=True)
    bad = sorted({c for c in combined if ord(c) > 127})
    if bad:
        print("⚠️ non-ASCII chars (%d): %s" % (len(bad),
              [hex(ord(c)) for c in bad[:12]]), flush=True)
    else:
        print("✅ corpus pure ASCII", flush=True)

    tok = CharTokenizer()
    tok.fit_from_scratch(set(combined))
    ids = tok.encode("\n\n" + combined + "\n\n")
    ids_np = np.asarray(ids, dtype=np.int32)     # RAM-light (koi window copy nahi)
    n_windows = len(ids) - SEQ_LEN - 1
    os.makedirs(CKPT_DIR, exist_ok=True)
    tok.save(os.path.join(CKPT_DIR, "vocab.json"))
    print("🔤 vocab: %d chars | windows: %s" % (tok.vocab_size, f"{n_windows:,}"),
          flush=True)

    os.makedirs(ARCHIVE, exist_ok=True)
    for f in glob.glob(os.path.join(CKPT_DIR, "*.npz")):
        base = os.path.basename(f)
        # 🔒 SAME-PREFIX ARCHIVE: sirf isi dimagh ke purane checkpoints archive —
        # doosre dimagh (hemohelper/hemoverify/hemodeep/hemomaster) ko chhedna nahi
        if not base.startswith(prefix):
            continue
        if (base.startswith("%s_mid" % prefix) or base.startswith("%s_chat" % prefix)):
            continue
        shutil.move(f, os.path.join(ARCHIVE, base))
    print("🗄️ %s ke purane checkpoints -> archive/ (har dimagh apni jagah)" % prefix,
          flush=True)

    brain = LSTMBrain(tok.vocab_size, d_h=dh, seed=2026)
    mid = os.path.join(CKPT_DIR, "%s_mid.npz" % prefix)
    if os.path.exists(mid):
        try:
            _d = np.load(mid, mmap_mode="r")
            _vc = int(_d["embed"].shape[0])
            _hc = int(_d["embed"].shape[1])
            if _vc == tok.vocab_size and _hc == dh:
                brain.load(mid)             # 🔁 WARM-START: pichli tarbiyat se
                print("🔁 jan-bujh kar WARM-START: %s (purani soch) load hui"
                      % os.path.basename(mid), flush=True)
            else:
                print("⚠️ warm-start SKIP: checkpoint (%d ch, dh%d) ≠ naya "
                      "(%d ch, dh%d) — fresh tarbiyat" % (
                          _vc, _hc, tok.vocab_size, dh), flush=True)
        except Exception as e:
            print("(warm-start fail — fresh tarbiyat: %s)" % e, flush=True)
    params = (brain.embed.size + brain.W_out.size + brain.b_out.size +
              sum(L.W.size + L.b.size for L in brain.layers))
    wbytes = ((brain.embed.size + brain.W_out.size +
               sum(L.W.size for L in brain.layers)) * 4)
    mb = wbytes / 1e6
    _role = ("DEEP" if deep else "HELPER" if helper else
             "VERIFY" if verify else "MASTER")
    print("🧠 HEMOMO-%s: %s params (dh%d, 2 layers, %.1f MB float32)" % (
        _role, f"{params:,}", dh, mb), flush=True)

    # LR schedule (bade model ke liye thoda soft start)
    half, thr = steps // 2, int(steps * 0.75)
    def sched(s):
        if s <= half:
            return 0.010
        if s <= thr:
            return 0.007
        return 0.004

    rng = np.random.default_rng(2026)
    t0, running = time.time(), []
    per_step = None
    print("⏱️ ETA parh rahe hain (pehle 100 steps)...")
    for s in range(1, steps + 1):
        brain.lr = sched(s)
        i = int(rng.integers(0, n_windows))
        loss = brain.train_step(ids_np[i:i + SEQ_LEN + 1].tolist())
        running.append(loss)
        if s == 100:
            per_step = (time.time() - t0) / 100.0
            eta = per_step * steps / 3600.0
            print("⚡ %0.2fs/step → ETA ≈ %.1f ghante" % (per_step, eta), flush=True)
        if s % 200 == 0:
            print("  step %d | loss %.4f | %.0fs" % (
                s, np.mean(running[-200:]), time.time() - t0), flush=True)
        if s % 1000 == 0:
            mids = os.path.join(CKPT_DIR, "%s_mid.npz" % prefix)
            brain.save(mids)
            demo = brain.sample("\nSawal: ilm kya hai\nJawab:", tok,
                                max_new=120, temperature=0.5)
            demo = demo.split("\nSawal:")[0].replace("\n", " ").strip()
            print("  💾 mid-save (step %d) | 🔊 khud-soch: %s" % (s, demo[:120]),
                  flush=True)

    final = os.path.join(CKPT_DIR, "%s_%d.npz" % (prefix, int(time.time())))
    brain.save(final)
    print("💾 FINAL HEMOMO-MASTER saved: %s" % os.path.basename(final), flush=True)
    print("📊 final loss: %.4f" % np.mean(running[-500:]), flush=True)

    # 🪄 khud-soch samples (template NAHI — master ka apna dimagh)
    print("\n🪄 MASTER SAMPLES (Sawal -> apna sochna):", flush=True)
    for q in ["salam", "Aap ka naam kya hai", "Ilm kya hai", "Quran parho",
              "hadith batao", "Dil pareshan hai", "kya haal hai",
              "sabr kya hai"]:
        p = "\nSawal: " + q + "\nJawab:"
        out = brain.sample(p, tok, max_new=180, temperature=0.5)
        out = out.split("\nSawal:")[0].split("\n")[0].strip()
        print("  [%s] -> %s" % (q, out[:150]), flush=True)

    print("\n🏁 TOTAL: %.1f min" % ((time.time() - t_all) / 60.0), flush=True)


if __name__ == "__main__":
    steps, dh, deep = 8000, None, False
    helper, verify = False, False
    for a in sys.argv[1:]:
        if a.isdigit():
            steps = int(a)
        elif a.startswith("--dh="):
            dh = int(a.split("=", 1)[1])
        elif a == "--deep":
            deep = True
        elif a == "--helper":
            helper = True
        elif a == "--verify":
            verify = True
    main(steps=steps, dh=dh, deep=deep, helper=helper, verify=verify)
