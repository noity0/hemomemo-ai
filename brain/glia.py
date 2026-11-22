"""
🧬 glia.py — GLIAL CELLS (1,600,000 "neuroglial" support cells @ 2M neurons)

Glia neurons ki madadgar cells hain — apni marzi se fire NAHI karti, magar
brain ka aaram aur tarbiyat iski zimmedari hai:
 1. WATCH      — apne paas wale neuron ki activity dekhti hai (calcium wave)
 2. TRIAGE     — zyada garam neuron ko thanda karti hai (inhibitory gliotransmitter)
 3. NOURISH    — soye hue neuron ko halki taqat deti hai (nutrition current)
 4. MODULATION — brain ka mood (arousal) nikalti hai: chat thinking me
                 sampling temperature isi se thoda mukhtalif hota hai.

Har glial cell random-target neuron ke paas baithi hai (taqreeban 0.8 glia/neuron).
Sab kuch NumPy — no API, no internet, no Ollama.
"""
import numpy as np

from .config import N_GLIA   # brain ke size ke hisaab se (default 1,600,000)


class GlialSystem:
    """1.6M glial support cells — neurons ko dekhti aur theek karti hain."""

    def __init__(self, n_neurons: int, n_glia: int = N_GLIA, seed: int = 17):
        self.n_neurons = n_neurons
        self.n_glia = n_glia
        self.rng = np.random.default_rng(seed)
        # har glial cell ka target neuron (paas baithne wala)
        self.target = self.rng.integers(0, n_neurons, size=n_glia, dtype=np.int32)
        # per-glia internal state
        self.calcium = self.rng.uniform(0.05, 0.15, n_glia).astype(np.float32)
        self.activity = np.zeros(n_glia, dtype=np.float32)
        self.total_release = 0   # kitne dafa gliotransmitter nikla
        self._mod = np.zeros(n_neurons, dtype=np.float32)  # reusable buffer

    # ------------------------------------------------------------------
    def step(self, neuron_rate: np.ndarray) -> np.ndarray:
        """neuron_rate (n,) dekho -> per-neuron modulation current (n,)"""
        local = neuron_rate[self.target]              # glia apne neuron ko dekhti hai
        self.activity = 0.90 * self.activity + 0.10 * local

        # calcium wave: activity se ubharta hai, dheere dheere bikharta hai
        self.calcium += 0.002 * (self.activity > 0.02) - 0.0012
        np.clip(self.calcium, 0.0, 1.0, out=self.calcium)

        hot = self.activity > (self.activity.mean() * 2.0 + 0.01)
        tired = self.activity < 0.0025

        mod = self._mod
        mod.fill(0.0)
        if hot.any():
            idx = self.target[hot]
            w = (-0.03 * self.calcium[hot]).astype(np.float64)
            mod += np.bincount(idx, weights=w, minlength=self.n_neurons
                               ).astype(np.float32)
            self.total_release += int(hot.sum())
        if tired.any():
            idx = self.target[tired]
            w = (0.012 + 0.02 * self.calcium[tired]).astype(np.float64)
            mod += np.bincount(idx, weights=w, minlength=self.n_neurons
                               ).astype(np.float32)
        return mod

    # ------------------------------------------------------------------
    def stats(self) -> dict:
        return {
            "glia": self.n_glia,
            "glia_calcium": float(self.calcium.mean()),
            "glia_release": self.total_release,
        }


if __name__ == "__main__":
    n = 2_000_000
    import numpy as _np
    rate = _np.zeros(n, dtype=np.float32)
    rate[:1000] = 0.05  # sensory area garam
    g = GlialSystem(n)
    for _ in range(20):
        mod = g.step(rate)
    print("Glia stats:", g.stats())
    print("mod nonzero:", int((mod != 0).sum()), "| max:", float(mod.max()))
