# -*- coding: utf-8 -*-
"""Reproduce OOB per failing QA combo with full traceback (frame 0-3 only)."""
import sys
import traceback

sys.path.insert(0, r"D:\DigitalBrain")
import numpy as np                          # noqa: E402
import agent.video_gen as vg                # noqa: E402

COMBOS = [
    ("ocean boat lehar shaam", "ocean", 24, 10),   # QA check-10
    ("prompt-A forest jungle", "auto", 24, 4),     # QA check-13
    ("prompt-B desert dune", "auto", 24, 4),
    ("custom fps farq", "auto", 12, 4),            # QA check-14
    ("cinematic multi-shot darya jungle raat", "auto", 24, 8),  # QA 25
    ("cinematic mountain sunrise daur", "auto", 24, 4),  # QA check-9 (passes)
]

for prompt, style, fps, nf in COMBOS:
    label = "%s/%s@%dfps" % (style, prompt[:26], fps)
    try:
        st, seed = vg._parse_scene(prompt, style, vg.W, vg.H)
        shot = vg._Shot(st, seed, 10.0, vg.SSW, vg.SSH, 0, fps,
                        pal_over=vg._prompt_overrides(prompt))
        print("--- %s : style=%s seed=%d" % (label, shot.style, seed))
        img = None
        for i in range(nf):
            img, _ = vg._render(shot, i / float(fps), fps, None, i)
        print("    frames OK", img.shape)
    except Exception:
        print("    CRASH on %s" % label)
        traceback.print_exc()
        break
