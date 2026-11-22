# -*- coding: utf-8 -*-
"""Real generate_video() replay of the 4 QA-failing combos.
Engine now embeds the crash location, so RuntimeError carries file+line."""
import sys
import time

sys.path.insert(0, r"D:\DigitalBrain")
import agent.video_gen as vg                # noqa: E402

COMBOS = [
    ("ocean boat lehar shaam", 15.0, "ocean", 24, "p10"),
    ("prompt-A forest jungle", 5.0, "auto", 24, "p13a"),
    ("prompt-B desert dune", 5.0, "auto", 24, "p13b"),
    ("custom fps farq", 8.0, "auto", 12, "p14"),
    ("cinematic multi-shot darya jungle raat", 30.0, "auto", 24, "p25"),
]

for prompt, dur, style, fps, tag in COMBOS:
    t0 = time.time()
    try:
        p = vg.generate_video(prompt, dur, style=style, fps=fps)
        m = vg.video_meta(p)
        print("%s OK dur=%s wall=%.0fs -> %s" % (tag, m["duration"],
                                                 time.time() - t0, p))
    except Exception as e:
        print("%s CRASH wall=%.0fs" % (tag, time.time() - t0))
        print(str(e))
    print("-" * 60)
print("REPLAY DONE")
