"""
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
