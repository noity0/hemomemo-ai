"""
🔤 tokenizer.py — Character-level Tokenizer (self-built vocab)

Corpus padh kar apni vocabulary banata hai. Koi API nahin.
"""
import os
import json

import sys as _sys
if getattr(_sys, "frozen", False):
    DATA_PATH = os.path.join(os.path.dirname(_sys.executable), "data",
                             "corpus.txt")   # 📦 EXE apna folder
    if not os.path.exists(DATA_PATH):
        DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "data", "corpus.txt")
else:
    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "data", "corpus.txt")


class CharTokenizer:
    def __init__(self):
        self.stoi = {}
        self.itos = []
        self.fit_from_scratch(set())

    @property
    def vocab_size(self):
        return len(self.itos)

    def fit_from_scratch(self, extra_chars=frozenset()):
        """\"\\n\" + corpus chars se vocab banao (deterministic order)."""
        chars = {"\n"}
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, "r", encoding="utf-8", errors="ignore") as f:
                chars |= set(f.read())
        chars |= set(extra_chars)
        chars = sorted(chars)
        self.itos = chars
        self.stoi = {c: i for i, c in enumerate(chars)}
        return self

    # ------------------------------------------------------------------
    def encode(self, text: str) -> list[int]:
        return [self.stoi.get(c, 0) for c in text]

    def decode(self, ids) -> str:
        out = []
        for i in ids:
            if 0 <= int(i) < len(self.itos):
                out.append(self.itos[int(i)])
        return "".join(out)

    # ------------------------------------------------------------------
    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"itos": self.itos}, f, ensure_ascii=False)

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        self.itos = d["itos"]
        self.stoi = {c: i for i, c in enumerate(self.itos)}
        return self
