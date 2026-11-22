# -*- coding: utf-8 -*-
"""Reproduce multi-shot OOB with full traceback (transition frames only)."""
import sys
import traceback

sys.path.insert(0, r"D:\DigitalBrain")
import numpy as np                          # noqa: E402
import agent.video_gen as vg                # noqa: E402

st, seed = vg._parse_scene("cinematic storm barish toofan", "storm",
                           vg.W, vg.H)
fps = 24
shot_dur = 7.5                              # 15s -> 2 shots
s0 = vg._Shot(st, seed, shot_dur, vg.SSW, vg.SSH, 0, fps)
s1 = vg._Shot(st, seed, shot_dur, vg.SSW, vg.SSH, 1, fps)
tr = 0.7
prev16 = None
try:
    for k in range(24):
        tl = (shot_dur - tr) + k * 0.02
        f0, prev16 = vg._render(s0, tl, fps, prev16, k)
        f2, _ = vg._render(s1, tl - (shot_dur - tr), fps, None, k)
        al = (tl - (shot_dur - tr)) / tr
        frame = np.clip(f0.astype(np.float32) * (1 - al) +
                        f2.astype(np.float32) * al, 0, 255).astype(np.uint8)
        print("t=%.2f ok shape=%s" % (tl, frame.shape))
except Exception:
    traceback.print_exc()
    print("PROBE: CRASH REPRODUCED")
else:
    print("PROBE: all transition frames OK (bug not in this path)")
