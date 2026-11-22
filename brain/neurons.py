"""
⚡ neurons.py — Electric Neuron Population (config-scale; default 2,000,000)

Har neuron ka apna membrane voltage (mV) hota hai.
Jab voltage threshold cross karta hai -> SPIKE (action potential) fire hota hai.
Yahi "electricity" ka core model hai.
"""
import numpy as np

# Scalable config: HMHS_N_TOTAL / HMHS_N_GLIA / HMHS_FAN_OUT env vars
# Default 2,000,000 neurons | 20B formula server-RAM par khula
from .config import N_TOTAL, AREAS


class NeuralArray:
    """Configurable electric neuron population (scale brain/config.py se)."""

    def __init__(self, n_total: int = N_TOTAL, dt_ms: float = 1.0, seed: int = 42):
        self.n = n_total
        self.dt = dt_ms  # milliseconds
        self.rng = np.random.default_rng(seed)

        # ---- Electric state (membrane) ----
        self.v = self.rng.uniform(-70.0, -60.0, self.n).astype(np.float32)  # mV
        self.u = np.zeros(self.n, dtype=np.float32)  # recovery current
        self.gain = self.rng.uniform(0.5, 1.5, self.n).astype(np.float32)  # excitability
        self.v_threshold = np.full(self.n, -55.0, dtype=np.float32)  # mV
        self.v_reset = np.full(self.n, -70.0, dtype=np.float32)      # mV
        self.leak_rate = self.rng.uniform(0.985, 0.998, self.n).astype(np.float32)

        # Spike bookkeeping
        self.spikes = np.zeros(self.n, dtype=bool)   # is timestep ke spikes
        self.spike_count = np.zeros(self.n, dtype=np.int64)  # lifetime count
        self.rate_smooth = np.zeros(self.n, dtype=np.float32)  # smoothed firing rate
        self.refractory = np.zeros(self.n, dtype=np.int32)  # refractory ticks left

        # Homeostasis targets
        self.v_min = np.full(self.n, -85.0, dtype=np.float32)
        self.v_max = np.full(self.n,  +40.0, dtype=np.float32)
        self.target_rate = self.rng.uniform(0.02, 0.10, self.n).astype(np.float32)

    # ------------------------------------------------------------------
    @property
    def total_spikes(self) -> int:
        return int(self.spike_count.sum())

    def area_spikes(self, area: str) -> int:
        lo, hi = AREAS[area]
        return int(self.spike_count[lo:hi].sum())

    def area_rate(self, area: str) -> float:
        lo, hi = AREAS[area]
        sub = self.rate_smooth[lo:hi]
        return float(sub.mean()) if sub.size else 0.0

    # ------------------------------------------------------------------
    def inject_current(self, idx: np.ndarray, amount: np.ndarray):
        """Senses ya synapses neurons me electric current inject karte hain."""
        self.v[idx] += amount.astype(np.float32)
        np.clip(self.v[idx], self.v_min[idx], self.v_max[idx], out=self.v[idx])

    # ------------------------------------------------------------------
    def step(self, external_current: np.ndarray | None = None):
        """1 timestep (dt ms) simulation: electric flow + spikes."""
        # external current
        if external_current is not None:
            self.inject_current(np.arange(self.n), external_current)

        # Izhikevich-style recovery coupling (u follows v, decay ke saath)
        self.u += 0.04 * (self.v * self.v + 5.0 * self.v + 140.0 - self.u) * 0.001
        self.u *= 0.98
        # 🩹 recovery current ki limit — warna u 4,000+ bhaag jata hai (spike-storm)
        np.clip(self.u, -50.0, 50.0, out=self.u)
        # leak + recovery feedback (rest par sukoon, sense par fire)
        self.v = self.v * self.leak_rate + self.u * 0.02 + self.gain * 0.05

        # refractory neurons can't fire
        ready = (self.refractory <= 0)
        self.refractory[~ready] -= 1

        # threshold crossing -> spike!
        self.spikes[: self.n] = ready & (self.v >= self.v_threshold)
        fired = self.spikes
        # reset fired neurons (electric discharge)
        self.v[fired] = self.v_reset[fired]
        self.u[fired] = self.u[fired] * 0.5
        self.refractory[fired] = 2  # 2 ms refractory period
        self.spike_count[fired] += 1

        # smoothed firing rate (exponential moving average)
        self.rate_smooth = 0.995 * self.rate_smooth + 0.005 * fired.astype(np.float32)

    # ------------------------------------------------------------------
    def homeostasis(self):
        """⚡ Electric balance: over-excited neurons cool, dead ones energize."""
        # cooling: agar neuron target rate se zyada fire kar(ra)ha hai
        hot = self.rate_smooth > self.target_rate * 3.0
        self.v_threshold[hot] += 0.05          # threshold raise
        self.v_threshold[hot] = np.minimum(self.v_threshold[hot], -35.0)

        # energizing: bilkul soye hue neurons ko thoda boost
        dead = self.rate_smooth < self.target_rate * 0.05
        self.v_threshold[dead] -= 0.02          # threshold lower
        self.v_threshold[dead] = np.maximum(self.v_threshold[dead], -60.0)
        self.gain[dead] *= 1.001
        self.gain = np.clip(self.gain, 0.3, 2.5)

        # voltage physical bounds
        np.clip(self.v, self.v_min, self.v_max, out=self.v)

    # ------------------------------------------------------------------
    def ascii_activity(self, cols: int = 60) -> str:
        """Poore brain ki activity ka ASCII grid."""
        chunks = np.array_split(self.rate_smooth, cols)
        col_avg = np.array([c.mean() if c.size else 0.0 for c in chunks])
        hi = col_avg.max() if col_avg.max() > 0 else 1.0
        chars = " .:-=+*#%@"
        row = "".join(chars[min(int(x / hi * (len(chars) - 1)), len(chars) - 1)] for x in col_avg)
        return row


if __name__ == "__main__":
    brain = NeuralArray()
    # 2 second random electrical storm ka test
    for t in range(2000):
        noise = brain.rng.normal(0.0, 0.35, brain.n).astype(np.float32)
        brain.step(noise)
        if t % 500 == 0:
            brain.homeostasis()
    print(f"Neurons: {brain.n:,} | Total spikes in 2s: {brain.total_spikes:,}")
    print("Activity:", brain.ascii_activity())
