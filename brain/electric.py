"""
⚡ electric.py — ELECTRICITY ENGINE (Voltage Grid + Heartbeat)

Brain ki apni "power grid": main current, heartbeat, voltage phases.
- RESTING电位 (-70 mV)
- EXCITED / FIRE phase
- REFRACTORY (recharge)
Homeostasis module isko balance rakhta hai.
"""
import numpy as np


class ElectricGrid:
    """Power grid + heartbeat oscillator."""

    def __init__(self, seed: int = 99):
        self.rng = np.random.default_rng(seed)
        self.main_voltage = 70.0        # mV grid baseline
        self.heart_phase = 0.0
        self.heart_freq_hz = 2.0        # heartbeat rate (≈ theta rhythm)
        self.beats = 0
        self.phase = "resting"          # resting | excited | refractory
        self.flux_history: list[float] = []

    # ------------------------------------------------------------------
    def heartbeat(self, dt_ms: float) -> float:
        """Theta-rhythm oscillator; har beat par grid 'pulse' deta hai."""
        self.heart_phase += self.heart_freq_hz * dt_ms / 1000.0
        if self.heart_phase >= 1.0:
            self.heart_phase -= 1.0
            self.beats += 1
        # sinusoidal drive: -1..+1
        return float(np.sin(2 * np.pi * self.heart_phase))

    # ------------------------------------------------------------------
    def grid_drive(self) -> float:
        """Global electric bias jo har neuron ko halka push karta hai."""
        return self.heartbeat(1.0) * 0.15

    # ------------------------------------------------------------------
    def set_phase(self, mean_v: float):
        """Grid ke phase ko label karo (viz ke liye)."""
        if mean_v > 35:
            self.phase = "excited"
        elif mean_v < -60:
            self.phase = "resting"
        else:
            self.phase = "refractory"

    # ------------------------------------------------------------------
    def flux(self, rates: np.ndarray) -> float:
        """Total electric flux (activity) ka measure."""
        f = float(rates.sum())
        self.flux_history.append(f)
        if len(self.flux_history) > 300:
            self.flux_history.pop(0)
        return f
