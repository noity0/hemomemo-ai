import sys; sys.path.insert(0, r'D:\DigitalBrain')
import agent.video_gen as vg

for i, (name, dur, fps) in enumerate([
    ("15min support", 60.0, 24),
    ("determinism same-prompt", 5.0, 24),
    ("different prompt diff path", 5.0, 24),
    ("custom fps 12", 8.0, 12),
], 11):
    try:
        if name == "15min support":
            r = vg.generate_video("epic 15 min movie scene", duration_sec=60.0, fps=24)
            print("%d. %s: OK (%s)" % (i, name, r))
        elif name == "determinism same-prompt":
            r1 = vg.generate_video("same prompt determinism", duration_sec=5.0, fps=24)
            r2 = vg.generate_video("same prompt determinism", duration_sec=5.0, fps=24)
            print("%d. %s: %s" % (i, name, "SAME" if os.path.basename(r1) == os.path.basename(r2) else "DIFF"))
        elif name == "different prompt diff path":
            r1 = vg.generate_video("prompt-A", duration_sec=5.0, fps=24)
            r2 = vg.generate_video("prompt-B-different", duration_sec=5.0, fps=24)
            print("%d. %s: %s" % (i, name, "DIFF" if os.path.basename(r1) != os.path.basename(r2) else "SAME"))
        elif name == "custom fps 12":
            r = vg.generate_video("custom fps 12 test", duration_sec=8.0, fps=12)
            mm = vg.video_meta(r)
            print("%d. %s: dur=%.1f" % (i, name, mm.get("duration", 0)))
    except Exception as e:
        print("%d. %s: FAIL %s" % (i, name, e))
