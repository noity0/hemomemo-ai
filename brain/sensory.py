"""
👁️👂✋⌨️ sensory.py — SENSE-able System (4 senses)

Brain duniya ko 4 tarah se mehsoos karta hai:
1. Vision    — light grid (ASCII/artificial camera)
2. Sound     — frequency bands (synthetic audio/whistle detector)
3. Touch     — contact map (pressure points)
4. Keyboard  — ASLI computer keyboard (real PC sense! aap type karo, brain sunta hai)

Har sense sensory neurons (brain ka 20% area) me Poisson-rate encoding karta hai.
"""
import numpy as np

from .config import SENSIVE_N, PER_SENSE   # brain ke size ke hisaab se (4 senses)


class Vision:
    """Light grid sense: 25x25 pixels (625 light receptors)."""

    def __init__(self, width: int = 25, height: int = 25, seed: int = 1):
        self.w, self.h = width, height
        self.rng = np.random.default_rng(seed)
        self.frame = np.zeros((self.h, self.w), dtype=np.float32)  # 0..1 brightness

    def draw_spot(self, x: int, y: int, radius: int = 4, intensity: float = 1.0):
        """Ek roshni ka daagh banao (stimulus)."""
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        dist2 = (xx - x) ** 2 + (yy - y) ** 2
        self.frame += intensity * np.exp(-dist2 / (2 * radius ** 2)).astype(np.float32)
        np.clip(self.frame, 0, 1, out=self.frame)

    def clear(self):
        self.frame[:] = 0.0

    def encode(self, n_slots: int = PER_SENSE):
        """Frame rate-coding me normalize karke neurons me bhejo."""
        flat = self.frame.reshape(-1)
        idx = np.linspace(0, flat.size - 1, n_slots).astype(int)
        return flat[idx] * 8.0  # current strength


class Sound:
    """Sound sense: 8 frequency bands (bass..treble)."""

    def __init__(self, bands: int = 8, seed: int = 2):
        self.bands = bands
        self.rng = np.random.default_rng(seed)
        self.energy = np.zeros(bands, dtype=np.float32)  # 0..1 per band

    def hear_tone(self, band: int, intensity: float = 1.0):
        self.energy[band % self.bands] += intensity
        np.clip(self.energy, 0, 1, out=self.energy)

    def hear_noise(self, intensity: float = 0.4):
        self.energy += self.rng.uniform(0, intensity, self.bands).astype(np.float32)
        np.clip(self.energy, 0, 1, out=self.energy)

    def clear(self):
        self.energy[:] = 0.0

    def encode(self, n_slots: int = PER_SENSE):
        idx = np.linspace(0, self.bands - 1, n_slots).astype(int)
        return self.energy[idx] * 10.0


class Touch:
    """Touch sense: 12x12 contact grid (144 pressure receptors)."""

    def __init__(self, width: int = 12, height: int = 12, seed: int = 3):
        self.w, self.h = width, height
        self.rng = np.random.default_rng(seed)
        self.map = np.zeros((self.h, self.w), dtype=np.float32)

    def press(self, x: int, y: int, force: float = 1.0):
        self.map[y % self.h, x % self.w] += force
        np.clip(self.map, 0, 1, out=self.map)

    def clear(self):
        self.map[:] = 0.0

    def encode(self, n_slots: int = PER_SENSE):
        flat = self.map.reshape(-1)
        idx = np.linspace(0, flat.size - 1, n_slots).astype(int)
        return flat[idx] * 9.0


class KeyboardSense:
    """⌨️ ASLI keyboard sense: aap PC par jo likho wo brain sunta hai!
    Har letter ek frequency-band pattern me convert hota hai."""
    ALPHABET = "abcdefghijklmnopqrstuvwxyz"

    def __init__(self):
        self.buffer: list[str] = []

    def feed_text(self, text: str):
        """Browser/camera nahi — yeh branch khud target tab ka console input use karti hai."""
        for ch in text.lower():
            if ch in self.ALPHABET or ch == " ":
                self.buffer.append(ch)
        if len(self.buffer) > 64:
            self.buffer = self.buffer[-64:]

    def clear(self):
        self.buffer.clear()

    def encode(self, n_slots: int = PER_SENSE):
        """Recent letters ko rate-pattern me encode karo."""
        cur = np.zeros(n_slots, dtype=np.float32)
        for i, ch in enumerate(self.buffer[-8:]):  # last 8 chars
            key = self.ALPHABET.index(ch) if ch in self.ALPHABET else 26
            start = int(key / 27 * n_slots)
            cur[start:start + 40] += 1.0  # burst
        return cur * 4.0


class SensorySystem:
    """Chaaron senses ka ein system + decoding into sensory neurons."""

    def __init__(self):
        self.vision = Vision()
        self.sound = Sound()
        self.touch = Touch()
        self.keyboard = KeyboardSense()

        # boundary indices within [0..SENSIVE_N)
        self.vision_slice = (0, PER_SENSE)
        self.sound_slice = (PER_SENSE, 2 * PER_SENSE)
        self.touch_slice = (2 * PER_SENSE, 3 * PER_SENSE)
        self.keybd_slice = (3 * PER_SENSE, SENSIVE_N)

    def encode_all(self) -> np.ndarray:
        """Length-50000 current vector banao jo sensory neurons me inject hoga."""
        out = np.zeros(SENSIVE_N, dtype=np.float32)
        a, b = self.vision_slice
        out[a:b] = self.vision.encode()
        a, b = self.sound_slice
        out[a:b] = self.sound.encode()
        a, b = self.touch_slice
        out[a:b] = self.touch.encode()
        a, b = self.keybd_slice
        out[a:b] = self.keyboard.encode()
        # per-neuron current barabar rakhne ke liye scale (reference: 1,250 slots/sense)
        out *= 1_250 / PER_SENSE
        return out
