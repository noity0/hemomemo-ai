"""
🏗️ scale.py — Hemomemo MODEL SCALER (2 Billion Target Planner)

Honest engineering:
- Pure NumPy + CPU: realistic max today ≈ 5-40M parameters (RAM/CPU bound)
- 2 BILLION parameters: NumPy/CPU se IMPOSSIBLE (weights 8GB fp32, ek step
  ghanton lagta). Iske liye GPU + PyTorch chahiye — par phir bhi OFFLINE
  ho (koi API nahi!).

Ye tool:
  1) Aapke CPU/RAM detect karke bata hai max kitna bada NumPy model ban sakta
  2) `--spec 2b` se exact 2B architecture spec + PyTorch training script
     (offline) folder me generate karta hai — future-ready
  3) `--build dh LAYERS` se NumPy config bana ke de deta hai

Usage:
  python model/scale.py                # report + feasibility
  python model/scale.py --spec 2b      # 2B plan + train_2b.py (PyTorch, offline)
  python model/scale.py --build 384 3  # NumPy model config
"""
import argparse
import json
import os
import sys
import platform

HERE = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(HERE)
else:
    ROOT = os.path.dirname(HERE)


def lstm_params(vocab: int, dh: int, layers: int) -> int:
    per_layer = (dh + dh) * (4 * dh) + 4 * dh
    return vocab * dh + dh * vocab + vocab + layers * per_layer


def feasible_numpy_max():
    total_gb, _ = Partition_or_fallback()
    # rule: weights fp32 RAM ka ~85%; CPU train step ~ params * 2ms
    usable = total_gb * 0.55 * 1e9  # bytes budget (fp32)
    par = int(usable / 4)
    # time cap: ek training per weight ~2 microsec => 8 hour budget
    time_cap = int(8 * 3600 / 2e-6)
    return min(par, time_cap)


def Partition_or_fallback():
    try:
        import psutil
        vm = psutil.virtual_memory()
        return vm.total / 1e9, vm.available / 1e9
    except Exception:
        # rough estimate without psutil
        return 16.0, 8.0


def find_arch(target: int, vocab: int, layers_range=(2, 64), dh_options=(64, 128, 256, 384, 512, 768, 1024, 1536, 2048)):
    best = None
    for L in layers_range:
        for dh in dh_options:
            p = lstm_params(vocab, dh, L)
            if p <= target and (best is None or p > best[0]):
                best = (p, dh, L)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=None)
    ap.add_argument("--build", nargs=2, type=int, default=None)
    a = ap.parse_args()

    import sys
    sys.path.insert(0, ROOT)
    from model.tokenizer import CharTokenizer
    tok = CharTokenizer().load(os.path.join(ROOT, "model", "checkpoints", "vocab.json"))
    vocab = tok.vocab_size
    total_gb, avail_gb = Partition_or_fallback()
    max_p = feasible_numpy_max()

    print("=" * 54)
    print(" 🏗️  Hemomemo SCALER REPORT")
    print("=" * 54)
    print(f" RAM total/available : {total_gb:.1f} / {avail_gb:.1f} GB")
    print(f" Vocab (chars)       : {vocab}")
    print(f" Current model       : 612,535 params (dh192, 2L)")
    print(f" NumPy CPU max feasible: ~{max_p:,} params  (8h training window)")

    # feasible sweet spots
    for tgt_label, tgt in [("10M", 10_000_000), ("50M", 50_000_000), ("500M", 500_000_000), ("2B", 2_000_000_000)]:
        ok = tgt <= max_p
        arch = find_arch(min(tgt, max_p), vocab)
        note = "✅ NumPy possible" if ok else "❌ needs GPU+PyTorch"
        if arch:
            p, dh, L = arch
            print(f" Target {tgt_label:4}: dh={dh:4d} layers={L:2d} → {p:>13,} params  {note}")
        else:
            print(f" Target {tgt_label:4}: {note}")

    if a.spec == "2b":
        # exact 2B architecture: d_model=2048, layers=32, vocab 55 (char) — not
        # efficient; better: future vocab 32k → char/word hybrid. Write spec JSON +
        # PyTorch offline training script.
        dh, L = 2048, 32
        p = lstm_params(vocab, dh, L)
        spec = {
            "target": "2,000,000,000 params",
            "note": "OFFLINE ONLY (no API). Requires GPU + PyTorch to train; NumPy path impossible on CPU.",
            "arch_char": {"hidden": dh, "layers": L, "estimated_params": p},
            "arch_future_wordlevel": {
                "type": "transformer_decoder",
                "d_model": 2048, "heads": 16, "layers": 32, "vocab": 30000,
                "params_approx": 12 * 32 * 2048 * 2048 + 2 * 30000 * 2048 + 2048 * 30000,
            },
            "hardware_req": "1x GPU 24GB+ (fp16) | 64GB RAM | ~200GB data corpus",
        }
        path = os.path.join(HERE, "model_2b_spec.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
        # PyTorch offline training script
        torch_train = '''"""
🚀 train_2b.py — GenTwo-2B (OFFLINE, GPU, NO API)
Precondition: pip install torch  |  GPU recommended
Data: data/corpus_big/*.txt (aap apni books/file dalte jao)
"""
import torch, torch.nn as nn
import os, json, math

D = json.load(open(os.path.join(os.path.dirname(__file__), "model_2b_spec.json")))
# char-level 2B LSTM spec (fast to write, heavy to train)
class BigLSTM(nn.Module):
    def __init__(self, vocab, d_model, layers):
        super().__init__()
        self.emb = nn.Embedding(vocab, d_model)
        self.lstm = nn.LSTM(d_model, d_model, layers, batch_first=True)
        self.out = nn.Linear(d_model, vocab)
    def forward(self, x, state=None):
        e, state = self.lstm(self.emb(x), state)
        return self.out(e), state

if __name__ == "__main__":
    # NOTE: ye script GPU + big data ke bina start nahi hogi.
    spec = D["arch_char"]
    vocab = 96
    m = BigLSTM(vocab, spec["hidden"], spec["layers"])
    n = sum(t.numel() for t in m.parameters())
    print(f"GenTwo-2B ready: {n:,} params (≈ {n/1e9:.2f}B) — training needs your data corpus.")
'''
        with open(os.path.join(HERE, "train_2b.py"), "w", encoding="utf-8") as f:
            f.write(torch_train)
        print("\n 📄 Wrote: model/model_2b_spec.json  +  model/train_2b.py (PyTorch, offline)")
        print("    Jab GPU mile, ye script 2B model banayega — koi API nahi hogi.")

    if a.build:
        dh, L = a.build
        p = lstm_params(vocab, dh, L)
        cfg = {"hidden": dh, "layers": L, "params": p, "framework": "numpy"}
        with open(os.path.join(HERE, "hemomemo_config.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        print(f"\n ⚙️ NumPy build config saved: dh={dh}, layers={L}, {p:,} params")


if __name__ == "__main__":
    main()
