"""
🧠 nn.py — Pure NumPy LSTM (Hemomemo ke brain cells)

2-layer char-level LSTM. Tension-free: no torch, no API, no cloud.
Sab weight matrices numpy arrays. Forward + manual backward (BPTT-lite).
"""
import os
import time

import numpy as np


def sigmoid(x):
    return 0.5 * (1.0 + np.tanh(0.5 * x))


def dsigmoid(y):
    return y * (1.0 - y)


class Layer:
    """Ek LSTM layer (input x -> h, cell c)."""

    def __init__(self, d_in: int, d_h: int, rng: np.random.Generator):
        self.d_in, self.d_h = d_in, d_h
        scale = 1.0 / np.sqrt(d_in + d_h)
        # combined gate matrix: 4 * d_h
        self.W = rng.normal(0, scale, (d_in + d_h, 4 * d_h)).astype(np.float32)
        self.b = np.zeros(4 * d_h, dtype=np.float32)

    # ------------------------------------------------------------------
    def forward(self, x: np.ndarray, h_prev: np.ndarray, c_prev: np.ndarray):
        n = x.shape[0]
        z = np.concatenate([x, h_prev], axis=1) @ self.W + self.b  # (n, 4h)
        gates = np.split(z, 4, axis=1)
        i_gate = sigmoid(gates[0])
        f_gate = sigmoid(gates[1])
        o_gate = sigmoid(gates[2])
        g_t = np.tanh(gates[3])
        c_t = f_gate * c_prev + i_gate * g_t
        h_t = o_gate * np.tanh(c_t)
        cache = (x, h_prev, c_prev, i_gate, f_gate, o_gate, g_t, c_t)
        return h_t, c_t, cache

    def backward_last_step(self, cache, dh: np.ndarray, dc: np.ndarray,
                           dW: np.ndarray, db: np.ndarray):
        """Sirf aakhri step ka quick gradient (truncated BPTT) — fast & stable."""
        x, h_prev, c_prev, i_g, f_g, o_g, g_t, c_t = cache
        tanh_c = np.tanh(c_t)
        do = dh * tanh_c
        dc_total = dc + dh * o_g * (1.0 - tanh_c ** 2)
        di = dc_total * g_t
        df = dc_total * c_prev
        dc_prev = dc_total * f_g
        dg = dc_total * i_g
        dh_prev = None  # truncated: propagate nahi karte purane steps

        # gate pre-activations gradients (sigmoid/tanh derivatives)
        di_pre = di * dsigmoid(i_g)
        df_pre = df * dsigmoid(f_g)
        do_pre = do * dsigmoid(o_g)
        dg_pre = dg * (1.0 - g_t ** 2)
        dz = np.concatenate([di_pre, df_pre, do_pre, dg_pre], axis=1)  # (n, 4h)

        # gradients
        zx = np.concatenate([x, h_prev], axis=1)
        dW += zx.T @ dz
        db += dz.sum(axis=0)
        dx = dz @ self.W[: self.d_in, :].T
        return dx, dh_prev, dc_prev, dW, db


class LSTMBrain:
    """2-layer LSTM char model: embeddings -> LSTM -> LSTM -> logits."""

    def __init__(self, vocab_size: int, d_h: int = 128, layers: int = 2, seed: int = 2026):
        self.vocab = vocab_size
        self.d_h = d_h
        self.n_layers = layers
        self.rng = np.random.default_rng(seed)
        self.embed = (self.rng.normal(0, 0.1, (vocab_size, d_h))).astype(np.float32)
        self.layers = [Layer(d_h, d_h, self.rng) for _ in range(layers)]
        self.W_out = (self.rng.normal(0, 1 / np.sqrt(d_h), (d_h, vocab_size))).astype(np.float32)
        self.b_out = np.zeros(vocab_size, dtype=np.float32)
        self.lr = 0.02

    # ------------------------------------------------------------------
    def forward_sequence(self, ids: list[int]):
        """Poora sequence chalao. Return (probs per step, caches)."""
        n = len(ids)
        h1 = np.zeros((1, self.d_h), dtype=np.float32)
        c1 = np.zeros((1, self.d_h), dtype=np.float32)
        h2 = np.zeros((1, self.d_h), dtype=np.float32)
        c2 = np.zeros((1, self.d_h), dtype=np.float32)
        probs, caches = [], []
        for t in range(n):
            e = self.embed[ids[t]][None, :]  # (1, d_h)
            h1, c1, cch1 = self.layers[0].forward(e, h1, c1)
            h2, c2, cch2 = self.layers[1].forward(h1, h2, c2)
            logits = h2 @ self.W_out + self.b_out
            logits -= logits.max()
            p = np.exp(logits)
            p /= p.sum()
            probs.append(p[0])
            caches.append((cch1, cch2, e, logits))
        return probs, caches

    # ------------------------------------------------------------------
    def train_step(self, ids: list[int]):
        """Next-char prediction; loss + updated weights (truncated BPTT)."""
        probs, caches = self.forward_sequence(ids[:-1])
        target = ids[1:]
        n = len(target)
        # loss + dlogits
        dlogits = []
        for t in range(n):
            p = probs[t].copy()
            p[target[t]] -= 1.0
            dlogits.append(p)
        dW_out = np.zeros_like(self.W_out)
        db_out = np.zeros_like(self.b_out)
        dW_layers = [np.zeros_like(L.W) for L in self.layers]
        db_layers = [np.zeros_like(L.b) for L in self.layers]
        dH_prev = np.zeros((1, self.d_h), dtype=np.float32)
        dC_prev = np.zeros((1, self.d_h), dtype=np.float32)
        for t in range(n - 1, -1, -1):
            cch1, cch2, e, _ = caches[t]
            # output layer
            h2 = cch2[1]  # cch2 = (x, h_prev, ...) => h is cch2[1]
            dW_out += h2.T @ dlogits[t][None, :]
            db_out += dlogits[t]
            dh2 = dlogits[t] @ self.W_out.T + dH_prev
            # layer-2 backward (single-step)
            dh2, dH_out1, dC_out1, dW_layers[1], db_layers[1] = self.layers[1].backward_last_step(
                cch2, dh2, dC_prev, dW_layers[1], db_layers[1])
            # layer-1 gets gradient from dh2 input side
            dh1_in = dh2 + dH_out1 if dH_out1 is not None else dh2
            dh1_in, dH_skip, dC_skip, dW_layers[0], db_layers[0] = self.layers[0].backward_last_step(
                cch1, dh1_in, dC_prev, dW_layers[0], db_layers[0])
            # embed gradient
            self.embed[ids[t]] -= self.lr * dh1_in[0]
            dH_prev = dH_skip * 0.5 if dH_skip is not None else dH_prev
            dC_prev = dC_skip * 0.5
        # simple SGD step
        self.W_out -= self.lr * dW_out
        self.b_out -= self.lr * db_out
        for i, L in enumerate(self.layers):
            L.W -= self.lr * dW_layers[i]
            L.b -= self.lr * db_layers[i]
        loss = -np.mean([np.log(max(probs[t][target[t]], 1e-9)) for t in range(n)])
        return float(loss)

    # ------------------------------------------------------------------
    def _char(self, nid, h1, c1, h2, c2):
        """EK char ka bohat lean forward (2 layers) — caches/softmax NAHI."""
        L0, L1 = self.layers[0], self.layers[1]
        dh = self.d_h
        e = self.embed[nid][None, :]
        z0 = np.concatenate([e, h1], axis=1) @ L0.W + L0.b
        ig = sigmoid(z0[:, :dh]); fg = sigmoid(z0[:, dh:2 * dh])
        og = sigmoid(z0[:, 2 * dh:3 * dh]); gg = np.tanh(z0[:, 3 * dh:])
        c1 = fg * c1 + ig * gg
        h1 = og * np.tanh(c1)
        z1 = np.concatenate([h1, h2], axis=1) @ L1.W + L1.b
        ig = sigmoid(z1[:, :dh]); fg = sigmoid(z1[:, dh:2 * dh])
        og = sigmoid(z1[:, 2 * dh:3 * dh]); gg = np.tanh(z1[:, 3 * dh:])
        c2 = fg * c2 + ig * gg
        h2 = og * np.tanh(c2)
        return h1, c1, h2, c2

    def prime(self, ids):
        """Prompt ko garam karo — sirf states (no caches, no softmax)."""
        n = np.zeros((1, self.d_h), dtype=np.float32)
        h1, c1, h2, c2 = n, n.copy(), n.copy(), n.copy()
        for tid in ids:
            h1, c1, h2, c2 = self._char(tid, h1, c1, h2, c2)
        return h1, c1, h2, c2

    def sample(self, prompt: str, tok, max_new: int = 120, temperature: float = 0.8):
        """⚡ ULTRA-FAST sampling: prime bina-cache + gemv har char par +
        searchsorted sampling + SAFARI-STOP (\\nSawal/\\nJawab/\\n\\n par band)."""
        # 📚 CONTEXT-MAX: prime-window 96 → 160 chars (LSTM state char-dar-char
        #    chalta hai — lambi prime se ziyada topaet-maloomat; 160 se oopar
        #    train-distribution se dur jata tha, is liye yahi ceiling)
        ids = tok.encode("\n" + prompt)[-160:] or [0]
        max_new = min(int(max_new), 30_000)   # 📏 output-ceiling (user qanoon: 30k)
        h1, c1, h2, c2 = self.prime(ids)
        temp = max(float(temperature), 0.05)
        out = []
        tail = ""
        itos = getattr(tok, "itos", None)
        rng = np.random.default_rng(int(abs(hash(prompt)) % (2 ** 31)))
        stops = ("\nSawal", "\nJawab", "\n\n")
        for _ in range(max_new):
            # logits (80-vocab) — sasta gemv
            lg = h2.reshape(-1) @ self.W_out + self.b_out
            lg /= temp
            lg -= lg.max()
            cdf = np.cumsum(np.exp(lg))
            nid = int(np.searchsorted(cdf, rng.random() * cdf[-1]))
            if nid >= self.vocab:
                nid = self.vocab - 1
            out.append(nid)
            ch = itos[nid] if itos is not None else tok.decode([nid])
            tail = (tail + ch)[-48:]
            if any(s in tail for s in stops):
                break
            h1, c1, h2, c2 = self._char(nid, h1, c1, h2, c2)
        return tok.decode(out)

    # ------------------------------------------------------------------
    def save(self, path):
        # 🛡️ seedha-likho: os.replace AV-lock (WinError-5 persistent,
        # 5-retry-bhi-fail) se mar-jata-tha; seedha-overwrite-write chalta
        # hai. Atomicity-ab-rotation-se-aati-hai (trainer do mid-slots
        # istemal-karta-hai — har-save purane-slot-ko-likhta-hai, naya-slot
        # salamat) + warm-start multi-candidate-fallback.
        np.savez(
            path,
            embed=self.embed, W_out=self.W_out, b_out=self.b_out,
            W0=self.layers[0].W, b0=self.layers[0].b,
            W1=self.layers[1].W, b1=self.layers[1].b,
        )

    def load(self, path):
        d = np.load(path)
        self.embed = d["embed"]; self.W_out = d["W_out"]; self.b_out = d["b_out"]
        self.layers[0].W = d["W0"]; self.layers[0].b = d["b0"]
        self.layers[1].W = d["W1"]; self.layers[1].b = d["b1"]
        return self
