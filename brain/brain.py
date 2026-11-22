"""
🧠 brain.py — Poora Digital Brain (Assembly)

2,000,000 neurons + 1,600,000 glial cells + 50M synapses + 4 senses + motor cortex + electric grid.
Senses -> neurons fire -> synapses propagate -> glia modulate -> motor decode -> ACTION.
"""
import numpy as np

from .neurons import NeuralArray, N_TOTAL, AREAS
from .synapses import Synapses
from .glia import GlialSystem
from .sensory import SensorySystem, SENSIVE_N
from .motor import MotorCortex
from .electric import ElectricGrid


class DigitalBrain:
    """Complete sense-able, control-able, evolving electric brain."""

    def __init__(self, seed: int = 42, learning: bool = True):
        self.rng = np.random.default_rng(seed)
        self.neurons = NeuralArray(N_TOTAL, seed=seed)
        self.synapses = Synapses(N_TOTAL, seed=seed + 1)
        self.senses = SensorySystem()
        self.motor = MotorCortex()
        self.grid = ElectricGrid(seed=seed + 2)
        self.glia = GlialSystem(N_TOTAL, seed=seed + 3)
        self.synapses.learning_enabled = learning

        self.t = 0  # sim step counter
        self.decisions: list[tuple[int, str, float]] = []

    # ------------------------------------------------------------------
    def inject_senses(self):
        """Senses ke codes ko sensory neurons me current bana do."""
        current = np.zeros(N_TOTAL, dtype=np.float32)
        sens = self.senses.encode_all()
        lo, hi = AREAS["sensory"]
        current[lo:lo + SENSIVE_N] = sens
        # grid ka global electric bias (heartbeat)
        current += self.grid.grid_drive()
        return current

    # ------------------------------------------------------------------
    def step(self, n: int = 1):
        """Brain ko n timesteps chalao."""
        for i in range(n):
            ext = self.inject_senses() if i == 0 else None
            self.neurons.step(ext)
            self.synapses.transmit(self.neurons.spikes)
            # synaptic current inject for the *next* step
            nxt = self.synapses.synaptic_current()
            if (i + 1) < n:
                self.neurons.inject_current(np.arange(N_TOTAL), nxt)
            if self.synapses.learning_enabled:
                self.synapses.stdp(self.neurons.spikes)
            self.t += 1

        self.neurons.homeostasis()
        # 🧬 glia: support cells watch karo + gliotransmitter modulation
        mod = self.glia.step(self.neurons.rate_smooth)
        if mod.any():
            self.neurons.inject_current(np.arange(N_TOTAL), mod)
        self.grid.set_phase(float(self.neurons.v.mean()))

        # motor decode
        lo, hi = AREAS["motor"]
        action, conf = self.motor.decode(self.neurons.rate_smooth[lo:hi])
        self.decisions.append((self.t, action, conf))
        self.grid.flux(self.neurons.rate_smooth)
        return action, conf

    # ------------------------------------------------------------------
    def react_to(self, stimulus_fn):
        """Ek stimulus do, brain react karega (single step)."""
        stimulus_fn()  # senses set karo
        return self.step(1)

    # ------------------------------------------------------------------
    def visualize(self) -> str:
        return self.neurons.ascii_activity()

    # ------------------------------------------------------------------
    def stats(self) -> dict:
        s = {
            "steps": self.t,
            "neurons": N_TOTAL,
            "synapses": N_TOTAL * self.synapses.fan_out,
            "total_spikes": self.neurons.total_spikes,
            "sensory_rate": self.neurons.area_rate("sensory"),
            "motor_rate": self.neurons.area_rate("motor"),
            "grid_phase": self.grid.phase,
            "heartbeats": self.grid.beats,
            "last_action": self.motor.last_action,
        }
        s.update(self.synapses.stats())
        s.update(self.glia.stats())
        return s

    # ------------------------------------------------------------------
    def sense_summary(self) -> str:
        k = len(self.senses.keyboard.buffer)
        v = float(self.senses.vision.frame.sum())
        s = float(self.senses.sound.energy.sum())
        t = float(self.senses.touch.map.sum())
        return (f"👁️ vision:{v:.1f}  🔊 sound:{s:.1f}  ✋ touch:{t:.1f}  "
                f"⌨️ keys:{k}")


if __name__ == "__main__":
    brain = DigitalBrain()
    # Test: spot dikhao, sound sunao => check decision
    brain.senses.vision.draw_spot(12, 12)
    brain.senses.sound.hear_tone(3)
    for _ in range(25):
        brain.step()
    print("Senses:", brain.sense_summary())
    print("Stats:", brain.stats())
    print("Viz:", brain.visualize())
