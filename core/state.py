"""
💾 state.py — Brain State Save/Load

Poore brain ka electric state (.npz me) save/load karta hai.
Evolving best brain ko yaad rakhne ke liye.
"""
import numpy as np
import os

import sys as _sys
if getattr(_sys, "frozen", False):
    SAVE_DIR = os.path.join(os.path.dirname(_sys.executable), "core")
else:
    SAVE_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(SAVE_DIR, exist_ok=True)


def save_brain(brain, name: str = "brain_state"):
    p = os.path.join(SAVE_DIR, f"{name}.npz")
    np.savez_compressed(
        p,
        v=brain.neurons.v,
        u=brain.neurons.u,
        gain=brain.neurons.gain,
        v_threshold=brain.neurons.v_threshold,
        spike_count=brain.neurons.spike_count,
        rate_smooth=brain.neurons.rate_smooth,
        weights=brain.synapses.weights.astype(np.float32),
        t=brain.t,
    )
    return p


def load_brain(brain, name: str = "brain_state") -> bool:
    p = os.path.join(SAVE_DIR, f"{name}.npz")
    if not os.path.exists(p):
        return False
    data = np.load(p)
    if int(data["v"].shape[0]) != int(brain.neurons.n):
        return False   # purane size ka saved state — naye brain (2M) se mismatch
    brain.neurons.v = data["v"]
    brain.neurons.u = data["u"]
    brain.neurons.gain = data["gain"]
    brain.neurons.v_threshold = data["v_threshold"]
    brain.neurons.spike_count = data["spike_count"]
    brain.neurons.rate_smooth = data["rate_smooth"]
    brain.synapses.weights = data["weights"]
    brain.t = int(data["t"])
    return True
