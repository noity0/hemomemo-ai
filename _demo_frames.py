# -*- coding: utf-8 -*-
"""Extract 1 middle frame from each demo mp4 for visual check."""
import subprocess as sp

VID = r"D:\DigitalBrain\data\videos"
JOBS = [
    ("hemomemo_233001.mp4", "_demo_golden.png"),
    ("hemomemo_313824.mp4", "_demo_neon.png"),
    ("hemomemo_976240.mp4", "_demo_storm.png"),
]
for src, out in JOBS:
    r = sp.run(["ffmpeg", "-y", "-ss", "4", "-i", VID + "\\" + src,
                "-frames:v", "1", VID + "\\" + out], capture_output=True)
    print(out, "rc=", r.returncode)
