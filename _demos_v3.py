# -*- coding: utf-8 -*-
"""3 demo mp4s with v3 photoreal engine (user-judge previews)."""
import sys
import time

sys.path.insert(0, r"D:\DigitalBrain")
import agent.video_gen as vg                       # noqa: E402

DEMOS = [
    ("cinematic golden sunset samandar calm waves birds boat dhup", "golden"),
    ("neon city night barish bokeh skyline tokyo", "neon"),
    ("dark storm toofan bijli barish mountains epic", "storm"),
]

for pr, st in DEMOS:
    t0 = time.time()
    try:
        p = vg.generate_video(pr, 9.0, style=st)
        m = vg.video_meta(p)
        print("DEMO[%s] -> %s | dur=%s fps=%s | wall=%.1fs"
              % (st, p, m["duration"], m["fps"], time.time() - t0))
    except Exception as e:
        print("DEMO[%s] FAILED: %r" % (st, e))

print("DEMOS DONE")
