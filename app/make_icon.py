# app/make_icon.py — Hemomemo app icon (☪ chaand + sitara, emerald + gold)
# PIL se multi-size .ico banao — EXE build me icon="app\\hemomemo.ico"
import math
import os
from PIL import Image, ImageDraw

S = 256
BG = (11, 21, 18, 255)        # C_BG dark-emerald
PANEL = (16, 38, 30, 255)     # rounded bg
GOLD = (217, 180, 91, 255)
EDGE = (47, 191, 143, 255)    # emerald
DARKHOLE = (11, 21, 18, 255)

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# rounded-square background
d.rounded_rectangle([2, 2, S - 3, S - 3], radius=52, fill=PANEL,
                    outline=EDGE, width=6)

# crescent: bada gold circle − offset bg-circle
d.ellipse([58, 34, 202, 178], fill=GOLD)
d.ellipse([92, 22, 216, 146], fill=DARKHOLE)

# 5-point star (gold) — upar daaya corner
cx, cy, r_out, r_in = 176, 86, 34, 14
pts = []
for i in range(10):
    ang = -math.pi / 2 + i * math.pi / 5
    r = r_out if i % 2 == 0 else r_in
    pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
d.polygon(pts, fill=GOLD)

os.makedirs("app", exist_ok=True)
img.save("app/hemomemo.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                    (64, 64), (128, 128), (256, 256)])
img.save("app/hemomemo_preview.png")
print("ICON-OK app/hemomemo.ico + preview")
