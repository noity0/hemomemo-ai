# -*- coding: utf-8 -*-
"""Test the LANCZOS fix on 5s video."""
import sys
import time

sys.path.insert(0, r"D:\DigitalBrain")
import agent.video_gen as vg

t0 = time.time()
p = vg.generate_video("cinematic golden sunset ocean calm", 5.0)
m = vg.video_meta(p)
print("5s test: wall=%.1fs, dur=%.1fs, fps=%d" % (time.time()-t0, m["duration"], m["fps"]))
print("SUCCESS" if m["duration"] >= 4.9 else "FAIL", p)