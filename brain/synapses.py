"""
🔌 synapses.py — Electric Connections (2M × 25 = 50M synapses) + STDP Learning

Neurons aapas me synapses se jude hain. Har synapse ka weight = electric signal strength.
Spike ek neuron se dusre me delay ke saath propagate hota hai.
STDP (Spike-Timing-Dependent Plasticity) se brain khud seekhta hai.
"""
import numpy as np

from .config import FAN_OUT   # har neuron ke targets (scale-able, default 25)
MAX_DELAY_STEPS = 4       # conduction delay (ms in 1ms steps)


class Synapses:
    """CSR-style sparse connectivity: fast aur memory-safe (dense nahi)."""

    def __init__(self, n_total: int, fan_out: int = FAN_OUT, seed: int = 7):
        self.n = n_total
        self.fan_out = fan_out
        self.rng = np.random.default_rng(seed)

        # targets: har neuron ke liye fan_out random successors
        self.targets = self.rng.integers(0, n_total, size=(n_total, fan_out), dtype=np.int32)
        # weights: excitatory/inhibitory mix, small start (float32 direct -> RAM-friendly)
        w = 0.5 * self.rng.random((n_total, fan_out), dtype=np.float32)
        inhibitory_frac = 0.20
        mask = self.rng.random((n_total, fan_out), dtype=np.float32) < inhibitory_frac
        w[mask] *= -1.0  # -ve = inhibitory synapse
        self.weights = w
        del mask

        # delays (1..MAX_DELAY_STEPS ms)
        self.delay_buf = self.rng.integers(1, MAX_DELAY_STEPS + 1, size=(n_total, fan_out), dtype=np.int8)
        self._gate = 0  # STDP throttle counter

        # delay buffers: each delay slot me arriving spikes
        self.queue = [np.zeros(n_total, dtype=np.float32) for _ in range(MAX_DELAY_STEPS + 1)]

        # STDP traces
        self.pre_trace = np.zeros(n_total, dtype=np.float32)
        self.post_trace = np.zeros(n_total, dtype=np.float32)
        self.learning_enabled = True
        self.eta = 0.004  # learning rate

    # ------------------------------------------------------------------
    def transmit(self, fired_mask: np.ndarray):
        """Jin neurons ne spike kiya unka signal delay-queue me daalo (fast bincount)."""
        fired_idx = np.flatnonzero(fired_mask).astype(np.int64)
        if fired_idx.size:
            k = fired_idx.size * self.fan_out
            # flattened synapse slots of fired neurons
            slots = (fired_idx[:, None] * self.fan_out + np.arange(self.fan_out, dtype=np.int64)).ravel()
            dly = self.delay_buf.ravel()[slots]
            order = np.argsort(dly, kind="stable")        # sort subset by delay
            slots = slots[order]
            dly = dly[order]
            starts = np.searchsorted(dly, np.arange(1, MAX_DELAY_STEPS + 1))
            total = dly.size
            ends = np.append(starts[1:], total)
            tgt_all = self.targets.ravel()
            wts_all = self.weights.ravel()
            for d in range(1, MAX_DELAY_STEPS + 1):
                s, e = int(starts[d - 1]), int(ends[d - 1])
                if s == e:
                    continue
                sl = slots[s:e]
                counts = np.bincount(
                    tgt_all[sl], weights=wts_all[sl].astype(np.float64), minlength=self.n)
                self.queue[d] += counts.astype(np.float32)
            self.pre_trace[fired_idx] += 1.0

        self._advance_queues()

    def _advance_queues(self):
        for i in range(MAX_DELAY_STEPS, 0, -1):
            self.queue[i] = self.queue[i - 1]
        self.queue[1] = np.zeros(self.n, dtype=np.float32)

    # ------------------------------------------------------------------
    def synaptic_current(self) -> np.ndarray:
        """Is timestep me sab neurons ko milne wala electric current (queue[1])."""
        return self.queue[1]

    # ------------------------------------------------------------------
    def stdp(self, fired_mask: np.ndarray):
        """Learn karo: jo neurons milke fire karte hain unki connection strong hoti hai."""
        if not self.learning_enabled:
            return
        self._gate += 1
        if self._gate % 10 != 0:   # har 10th step par hi learn (250k par speed)
            return
        post_fired_idx = np.flatnonzero(fired_mask).astype(np.int64)
        if post_fired_idx.size == 0:
            self.pre_trace *= 0.95
            self.post_trace *= 0.95
            return

        self.post_trace[post_fired_idx] += 1.0

        # strengthen: pre fired shortly before post
        pre_hot = self.pre_trace > 0.5
        if pre_hot.any():
            rows = np.flatnonzero(pre_hot)
            if rows.size > 50_000:      # bara brain: STDP tick par 50k rows limit
                rows = rows[:50_000]
            contrib = np.isin(self.targets[rows], post_fired_idx)
            if contrib.any():
                r_idx, c_idx = np.nonzero(contrib)
                self.weights[rows[r_idx], c_idx] += self.eta * 0.8
                self.weights[rows[r_idx], c_idx] = np.clip(
                    self.weights[rows[r_idx], c_idx], -2.0, 2.0)

        # weaken: post fired shortly before pre (anti-Hebbian part)
        pre_hot2 = self.pre_trace > 0.1
        rows2 = np.flatnonzero(pre_hot2)
        if rows2.size > 50_000:         # bara brain: limit (anti-Hebbian)
            rows2 = rows2[:50_000]
        contrib2 = np.isin(self.targets[rows2], post_fired_idx)
        if contrib2.any():
            r2, c2 = np.nonzero(contrib2)
            self.weights[rows2[r2], c2] -= self.eta * 0.5
            self.weights[rows2[r2], c2] = np.clip(
                self.weights[rows2[r2], c2], -2.0, 2.0)

        # decay traces
        self.pre_trace *= 0.95
        self.post_trace *= 0.95

    # ------------------------------------------------------------------
    def stats(self) -> dict:
        w = self.weights
        return {
            "synapses": int(self.n * self.fan_out),
            "avg_weight": float(w.mean()),
            "exc_frac": float((w > 0).mean()),
        }
