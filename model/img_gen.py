"""img_gen.py - Hemomemo IMAGE-GENERATION (100% LOCAL procedural - no AI-API)
=========================================================================
Koi AI-model/API/cloud NAHI: tasveer pure-math se banti hai (NumPy + PIL)
- text-hash se seed, words se palette/style. Har prompt = alag art.

Styles: aurora | waves | rings | maze | particles | gradient (auto-pick)

Save: data/generated/img_<stamp>.png  (app isko UI me dikhla sakti hai)
"""
import hashlib
import os
import re
import time

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUT_DIR = os.path.join(_ROOT, "data", "generated")

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except Exception:
    _PIL_OK = False

_STYLES = ("aurora", "waves", "rings", "maze", "particles", "gradient")

_PALETTES = {
    "sunset":  [(255, 94, 58), (255, 149, 0), (86, 204, 242), (26, 32, 64)],
    "ocean":   [(0, 121, 190), (0, 180, 216), (7, 78, 99), (3, 4, 15)],
    "jungle":  [(27, 94, 32), (129, 199, 132), (255, 213, 79), (10, 20, 10)],
    "royal":   [(94, 53, 177), (225, 190, 231), (255, 213, 79), (20, 10, 40)],
    "fire":    [(183, 28, 28), (255, 111, 0), (255, 196, 0), (15, 5, 5)],
    "ice":     [(144, 202, 249), (227, 242, 253), (25, 118, 210), (8, 18, 32)],
}
_WORDS = {"sunset": ("sham", "suraj", "sunset", "evening", "orange"),
          "ocean": ("samandar", "ocean", "sea", "pani", "water", "blue"),
          "jungle": ("jungle", "tree", "darkhat", "green", "sabz"),
          "royal": ("shahi", "royal", "purple", "king", "badshah"),
          "fire": ("aag", "fire", "lahu", "red", "lava"),
          "ice": ("barf", "ice", "snow", "thanda", "winter")}


def _seed(text):
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def _pick_palette(text, rng):
    low = (text or "").lower()
    for pal, words in _WORDS.items():
        if any(w in low for w in words):
            return _PALETTES[pal]
    return _PALETTES[["sunset", "ocean", "jungle", "royal", "fire",
                      "ice"][int(rng.integers(0, 6))]]


def _grid(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x / max(1, w - 1), y / max(1, h - 1)


def _aurora(px, py, rng, cols):
    t = rng.uniform(0, 6.28, 3)
    a = (np.sin(px * 4.0 + t[0]) + np.cos(py * 3.0 - t[1])) * 0.5 + 0.5
    b = (np.sin((px + py) * 2.5 + t[2]) * 0.5 + 0.5)
    band = np.exp(-((py - 0.35 - 0.18 * np.sin(px * 5 + t[1])) ** 2) * 14.0)
    img = np.stack([np.clip(a * cols[0][i] + b * cols[3][i], 0, 255)
                    for i in range(3)], -1)
    glow = np.array(cols[2], np.float32)
    for i in range(3):
        img[..., i] = np.clip(img[..., i] * (1 - band) + glow[i] * band, 0, 255)
    return img


def _waves(px, py, rng, cols):
    ph = rng.uniform(0, 6.28, 3)
    v = (np.sin(px * 8.0 + ph[0]) * np.sin(py * 6.0 + ph[1])
         + np.sin((px * py) * 20.0 + ph[2])) * 0.5 + 0.5
    return np.stack([np.clip(v * cols[i % 4][i % 3]
                             + (1 - v) * cols[3][i % 3], 0, 255)
                     for i in range(3)], -1)


def _rings(px, py, rng, cols):
    cx, cy = rng.uniform(0.3, 0.7, 2)
    d = np.sqrt((px - cx) ** 2 + (py - cy) ** 2)
    v = (np.sin(d * 40.0) * 0.5 + 0.5) * np.exp(-d * 1.2)
    return np.stack([np.clip(v * cols[0][i] + (1 - v) * cols[3][i], 0, 255)
                     for i in range(3)], -1)


def _maze(px, py, rng, cols):
    cell = int(rng.integers(14, 30))
    a = ((px * cell).astype(np.int32) % 2 == 0)
    b = ((py * cell).astype(np.int32) % 2 == 0)
    wall = (a ^ b).astype(np.float32)
    wall = np.clip(wall + 0.25 * np.sin(px * 60 + py * 60), 0, 1)
    return np.stack([np.clip(wall * cols[0][i] + (1 - wall) * cols[3][i],
                             0, 255) for i in range(3)], -1)


def _particles(px, py, rng, cols):
    img = np.zeros((px.shape[0], px.shape[1], 3), np.float32)
    img[..., 0], img[..., 1], img[..., 2] = cols[3]
    for _ in range(160):
        cx, cy = rng.uniform(0, 1, 2)
        r = rng.uniform(0.005, 0.05)
        c = cols[int(rng.integers(0, 4))]
        d = np.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        m = np.exp(-(d / max(r, 1e-4)) ** 2)
        for i in range(3):
            img[..., i] = np.clip(img[..., i] + m * c[i] * 0.55, 0, 255)
    return img


def _gradient(px, py, rng, cols):
    ang = rng.uniform(0, 3.14)
    v = np.clip(px * np.cos(ang) + py * np.sin(ang), 0, 1)
    out = np.stack([np.clip((1 - v) * cols[0][i] + v * cols[2][i], 0, 255)
                    for i in range(3)], -1)
    swirl = np.sin(px * 3 + py * 4) * 0.5 + 0.5
    for i in range(3):
        out[..., i] = np.clip(out[..., i] * (0.85 + 0.3 * swirl), 0, 255)
    return out


_FNS = {"aurora": _aurora, "waves": _waves, "rings": _rings,
        "maze": _maze, "particles": _particles, "gradient": _gradient}


def generate(prompt, w=512, h=512, style="auto", save=True):
    """Text -> procedural PNG -> path (no network, no AI)."""
    if not _PIL_OK:
        return None, "PIL ghayab (pip install pillow)"
    rng = np.random.default_rng(_seed(prompt or "hemomemo"))
    st = style if style in _FNS else \
        _STYLES[int(rng.integers(0, len(_STYLES)))]
    cols = _pick_palette(prompt or "", rng)
    px, py = _grid(w, h)
    arr = _FNS[st](px, py, rng, cols)
    img = Image.fromarray(arr.astype(np.uint8), "RGB")
    if save:
        os.makedirs(_OUT_DIR, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        safe = re.sub(r"[^a-z0-9_-]", "_", (prompt or "art")[:40].lower())
        path = os.path.join(_OUT_DIR, "img_%s_%s.png" % (safe, stamp))
        img.save(path)
        return path, st
    return img, st


def _font(sz):
    for f in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except Exception:
            continue
    return ImageFont.load_default()


def quote_card(text, w=1024, h=512):
    """Text-card banao (gradient-bg + likha-hua text) -> path."""
    if not _PIL_OK:
        return None, "PIL ghayab"
    rng = np.random.default_rng(_seed(text or "card"))
    cols = _pick_palette(text or "", rng)
    px, py = _grid(w, h)
    arr = _gradient(px, py, rng, cols)
    img = Image.fromarray(arr.astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)
    import textwrap
    lines = []
    for raw in (text or "").splitlines():
        lines.extend(textwrap.wrap(raw, 42) or [""])
    f = _font(34)
    lh = 44
    y = max(30, (h - lh * len(lines)) // 2)
    for ln in lines:
        d.text((60, y), ln, fill=(255, 255, 255), font=f)
        y += lh
    os.makedirs(_OUT_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(_OUT_DIR, "card_%s.png" % stamp)
    img.save(path)
    return path, "card"


def generate_text(prompt, size=512, style="auto"):
    """Chat-ready -> (text, meta)."""
    p = (prompt or "").strip() or "hemomemo art"
    path, st = generate(p, w=size, h=size, style=style)
    if not path:
        return "[image-gen] FAIL: %s" % st, {"source": "image-gen",
                                             "error": st}
    kb = os.path.getsize(path) // 1024
    txt = ("[image-gen] Tasveer ban gayi (100%% LOCAL procedural - "
           "koi AI-API/model nahi):\n  style: %s\n  size: %dx%d (%d KB)\n"
           "  file: %s" % (st, size, size, kb, path))
    return txt, {"source": "image-gen", "style": st, "file": path,
                 "size": os.path.getsize(path)}
