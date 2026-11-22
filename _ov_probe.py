# -*- coding: utf-8 -*-
"""Prompt-override wiring check + SS-1600x900 speed bench (v3.1)."""
import os
import sys
import time

sys.path.insert(0, r"D:\DigitalBrain")
import agent.video_gen as vg                       # noqa: E402
import PIL.Image                                    # noqa: E402

PRINT = sys.stdout.write


def prev(prompt, style, out):
    """Same pipeline as still_preview(), but with a custom output name."""
    st, seed = vg._parse_scene(prompt, style, vg.W, vg.H)
    shot = vg._Shot(st, seed, 10.0, vg.SSW, vg.SSH, 0,
                    pal_over=vg._prompt_overrides(prompt))
    img, _ = vg._render(shot, 0.9, vg.FPS_DEFAULT, None, 22)
    path = os.path.join(vg.video_root(), out)
    PIL.Image.fromarray(img).save(path)
    PRINT("saved %s\n" % path)


PRINT("== prompt-override table ==\n")
for pr, tag in [
    ("golden samandar boat birds parwaz", "birds"),
    ("neon city barish night", "rain"),
    ("storm toofan bijli", "flash"),
    ("winter pahar barfbari", "snow"),
    ("night jugnu forest", "firefly"),
    ("desert dhool sandstorm", "dust"),
    ("night meteor tootandas sitaray", "meteor+stars"),
    ("chand ke gird halo", "halo"),
    ("tokyo skyline buildings towers", "city"),
    ("subah dhund mist fog", "fog-delta"),
]:
    PRINT("%-38s -> %s\n" % (pr, vg._prompt_overrides(pr)))

PRINT("== visual previews ==\n")
prev("cinematic golden sunset ocean calm", "golden", "_ov_base.png")
prev("golden sunset samandar boat birds parwaz", "golden", "_ov_birds.png")
prev("neon city barish night tokyo", "neon", "_ov_night_rain.png")
prev("winter pahar barfbari chand halo", "winter", "_ov_snow.png")

PRINT("== speed bench (12 frames, SS 1600x900) ==\n")
st, seed = vg._parse_scene("cinematic golden sunset ocean calm waves",
                           "golden", vg.W, vg.H)
shot = vg._Shot(st, seed, 10.0, vg.SSW, vg.SSH, 0)
p16 = None
t0 = time.time()
for i in range(12):
    img, p16 = vg._render(shot, i / 24.0, 24, p16, i)
d = time.time() - t0
PRINT("12 frames: %.2fs -> %.1f ms/frame\n" % (d, d * 1000.0 / 12.0))
PRINT("DONE")
