"""
✋ motor.py — CONTROL SYSTEM (Motor Cortex)

Motor area (AREAS["motor"]) ke neurons ka firing pattern = brain ki DECISION.
10 action channels hain. Highest-firing channel jeetta hai (winner-take-all).
"""
import numpy as np

from .neurons import AREAS
from .config import MOTOR_N   # brain size ka 10% (AREAS["motor"] width)
ACTIONS = 10


class MotorCortex:
    """Brain ke decisions aur actions decode karta hai."""

    ACTION_NAMES = [
        "approach", "withdraw", "grab", "release",
        "turn_left", "turn_right", "speak", "listen",
        "type_text", "idle_rest",
    ]

    def __init__(self):
        self.idx_lo, self.idx_hi = AREAS["motor"]
        self.last_action = "idle_rest"
        self.action_history: dict[str, int] = {n: 0 for n in self.ACTION_NAMES}
        self.confidence_log: list[float] = []

    # ------------------------------------------------------------------
    def decode(self, motor_rates: np.ndarray) -> tuple[str, float]:
        """Motor rates (3000,) -> (action, confidence)"""
        chunk = MOTOR_N // ACTIONS
        channel_rates = np.array([
            motor_rates[i * chunk:(i + 1) * chunk].mean()
            for i in range(ACTIONS)
        ])
        winner = int(np.argmax(channel_rates))
        total = channel_rates.sum()
        conf = float(channel_rates[winner] / total) if total > 0 else 0.0
        if conf < 0.15:
            action = "idle_rest"
        else:
            action = self.ACTION_NAMES[winner]
        self.last_action = action
        self.action_history[action] = self.action_history.get(action, 0) + 1
        self.confidence_log.append(conf)
        return action, conf

    # ------------------------------------------------------------------
    def last_summary(self) -> str:
        return f"✋ action: {self.last_action} (confidence {max(self.confidence_log[-1:], [0])[0]:.2f})"
