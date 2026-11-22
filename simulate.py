"""
🧠 simulate.py — Live Brain Simulation

Brain ko activity ke saath chalata hai aur aap browser/terminal me dekh sakte hain:
- ASCII voltage grid
- senses feed karo (keyboard/text input)
- motor decisions live dekho
"""
import sys
from brain.brain import DigitalBrain


def run_live(steps: int = 300, text: str = "", spot: bool = True, tone: int | None = None):
    brain = DigitalBrain()
    if spot:
        brain.senses.vision.draw_spot(12, 12)
    if tone is not None:
        brain.senses.sound.hear_tone(tone)
    if text:
        brain.senses.keyboard.feed_text(text)

    print("🧠 LIVE SIMULATION — %s neurons firing (electric)" % "{:,}".format(brain.neurons.n))
    for s in range(steps):
        brain.step()
        if s % (steps // 10 or 1) == 0:
            print(f"[t={heart(brain)}] {bar(brain)} {brain.motor.last_summary()}")
    print("\nSenses:", brain.sense_summary())
    print("Stats:", pretty(brain.stats()))
    from core.state import save_brain
    p = save_brain(brain)
    print(f"💾 Saved: {p}")


def heart(brain):
    return brain.grid.heart_phase


def bar(brain):
    ch = {"resting": ".·.", "excited": "⚡⚡⚡", "refractory": "·  ·"}
    return ch.get(brain.grid.phase, "?")


def pretty(stats):
    return ", ".join(f"{k}={v}" for k, v in stats.items())


if __name__ == "__main__":
    run_live()
