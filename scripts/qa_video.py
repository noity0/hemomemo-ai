# -*- coding: utf-8 -*-
"""VIDEO-QA v2 — 25 checks (Hemomemo seedance-engine v2.1).

Imandari-qaaidaa: REAL PASS/FAIL — koi farzee adad nahi.
Faisl non-farzi-awaz: `py -3 -u -X utf8 _qa_video.py` (background behtar).
"""

import os
import sys
import time
import glob

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.abspath(__file__))
VDIR = os.path.join(ROOT, "data", "videos")

_results = []


def chk(no, label, ok, note=""):
    _results.append((no, ok))
    print("PASS [%d] %s" % (no, label) if ok else
          "FAIL [%d] %s :: %s" % (no, label, note), flush=True)


def main():
    t_all = time.time()
    import agent.video_gen as vg
    os.makedirs(VDIR, exist_ok=True)

    # 1-2: module + dir
    try:
        import agent.video_gen  # noqa: F811
        chk(1, "video_gen module import", True)
    except Exception as e:
        chk(1, "video_gen module import", False, str(e))
        return
    chk(2, "video dir (data/videos) exist", os.path.isdir(VDIR))

    # 3: koi social-media/bahar-machine ki cheez nahi (source-scan)
    src = open(os.path.join(ROOT, "agent", "video_gen.py"), "r",
               encoding="utf-8", errors="ignore").read().lower()
    bad = [m for m in ("urllib", "socket", "requests", "getpass",
                       "smtp", "telnet", "ftp://", "http://") if m in src]
    chk(3, "video module me bahar-taraf ki koi shay NAHI", not bad, str(bad))

    # 4-8: 5s base video
    t0 = time.time()
    try:
        p5 = vg.generate_video("cinematic neon city night rain", 5.0, style="auto")
        wall5 = time.time() - t0
        m5 = vg.video_meta(p5)
        chk(4, "5s video generate (wall %.0fs)" % wall5, True)
        head = open(p5, "rb").read(16)
        chk(5, "mp4 magic (ftyp at offset 4)", head[4:8] == b"ftyp",
            str(head[:8]))
        chk(6, "5s duration ~5 (>=4.9)", m5["duration"] >= 4.9,
            str(m5["duration"]))
        chk(7, "5s size > 50KB", m5["size"] > 50 * 1024, str(m5["size"]))
        chk(8, "fps 24", abs(m5["fps"] - 24.0) < 1.0, str(m5["fps"]))
    except Exception as e:
        chk(4, "5s video generate", False, str(e))
        chk(5, "mp4 magic", False)
        chk(6, "duration", False)
        chk(7, "size", False)
        chk(8, "fps", False)

    # 9: 10s + speed-limit (engine v3.1: 528 ms/frame measured @1600x900
    #    -> 240 frames ~= 127s + overhead; cap with 1.75x margin)
    try:
        t0 = time.time()
        p10 = vg.generate_video("cinematic mountain sunrise daur", 10.0)
        wall10 = time.time() - t0
        m10 = vg.video_meta(p10)
        chk(9, "10s dur~10 + wall<240s (wall=%.0fs)" % wall10,
            m10["duration"] >= 9.9 and wall10 < 240.0,
            "dur=%s wall=%.1f" % (m10["duration"], wall10))
    except Exception as e:
        chk(9, "10s dur~10 + speed", False, str(e))

    # 10: 15s
    try:
        p15 = vg.generate_video("ocean boat lehar shaam", 15.0, style="ocean")
        m15 = vg.video_meta(p15)
        chk(10, "15s generate + dur~15", m15["duration"] >= 14.9,
            str(m15["duration"]))
    except Exception as e:
        chk(10, "15s generate", False, str(e))

    # 11: text2script
    try:
        sc = vg.text2script("neon city night")
        chk(11, "script text2script gair-khaali", bool((sc or "").strip()),
            repr(sc)[:60])
    except Exception as e:
        chk(11, "script text2script", False, str(e))

    # 12: determinism (same prompt+dur → same filename)
    try:
        p1 = vg.generate_video("determinism scene", 5.0)
        p2 = vg.generate_video("determinism scene", 5.0)
        chk(12, "same-prompt → same file (overwrite-rasm)",
            os.path.basename(p1) == os.path.basename(p2),
            "%s vs %s" % (os.path.basename(p1), os.path.basename(p2)))
    except Exception as e:
        chk(12, "determinism", False, str(e))

    # 13: mukhtalif prompt → mukhtalif file
    try:
        pa = vg.generate_video("prompt-A forest jungle", 5.0)
        pb = vg.generate_video("prompt-B desert dune", 5.0)
        chk(13, "alag-prompt → alag file",
            os.path.basename(pa) != os.path.basename(pb))
    except Exception as e:
        chk(13, "alag-prompt", False, str(e))

    # 14: custom fps
    try:
        pf = vg.generate_video("custom fps farq", 8.0, fps=12)
        mf = vg.video_meta(pf)
        chk(14, "custom fps 12 dur~8",
            abs(mf["duration"] - 8.0) < 0.4 and abs(mf["fps"] - 12) < 0.6,
            str(mf))
    except Exception as e:
        chk(14, "custom fps", False, str(e))

    # 15-19: har style render-ok (5s each)
    style_checks = [
        (15, "noir", "noir street bheega"),
        (16, "space", "space galaxy sitaron"),
        (17, "winter", "barf sardi mountain"),
        (18, "neon", "neon city tokyo shahar"),
        (19, "golden", "golden suraj registan"),
    ]
    for no, stl, pr in style_checks:
        try:
            ps = vg.generate_video(pr, 5.0, style=stl)
            ms = vg.video_meta(ps)
            chk(no, "style %s render + dur~5" % stl,
                ms["duration"] >= 4.9 and ms["size"] > 20 * 1024, str(ms))
        except Exception as e:
            chk(no, "style %s render" % stl, False, str(e))

    # 20: koi .raw cheez baqi nahi (engine v2 pipe-only)
    time.sleep(1.0)
    raws = glob.glob(os.path.join(VDIR, "*.raw"))
    chk(20, "koi .raw file baqi NAHI (pipe-engine)", len(raws) == 0,
        str([os.path.basename(x) for x in raws][:4]))

    # 21: video_meta ghalbi-kaam
    try:
        mi = vg.video_meta(os.path.join(VDIR, "koi-nahin.mp4"))
        chk(21, "video_meta ghair-mojood par ghalba",
            isinstance(mi, dict) and "error" in mi)
    except Exception as e:
        chk(21, "video_meta ghalba", False, str(e))

    # 22: 60s video (engine v3.1 speed test: 1440 frames x 0.528s ~= 760s;
    #     cap 900s = measured + 15% margin)
    try:
        t0 = time.time()
        p60 = vg.generate_video("epic long cinematic toofan", 60.0, style="storm")
        wall60 = time.time() - t0
        m60 = vg.video_meta(p60)
        chk(22, "60s dur~60 + wall<900s (wall=%.0fs)" % wall60,
            m60["duration"] >= 59.5 and wall60 < 900.0,
            "dur=%s wall=%.1f" % (m60["duration"], wall60))
    except Exception as e:
        chk(22, "60s generate", False, str(e))

    # 23: min/max clamp kaad: 5s..3000s (50 minutes)
    chk(23, "DUR-limits (5s..3000s) sahi",
        vg.MIN_DUR <= 5.0 and vg.MAX_DUR == 3000.0,
        "%s..%s" % (vg.MIN_DUR, vg.MAX_DUR))

    # 24: preview PNG
    try:
        png = vg.still_preview("neon city raat cinematic")
        chk(24, "still_preview PNG bana", os.path.isfile(png),
            os.path.basename(png))
    except Exception as e:
        chk(24, "still_preview", False, str(e))

    # 25: multi-shot: 30s video → dur + size (engine v2.1 ko shots banta hain)
    try:
        p30 = vg.generate_video("cinematic multi-shot darya jungle raat", 30.0)
        m30 = vg.video_meta(p30)
        chk(25, "30s multi-shot dur~30 + size>300KB",
            m30["duration"] >= 29.9 and m30["size"] > 300 * 1024, str(m30))
    except Exception as e:
        chk(25, "30s multi-shot", False, str(e))

    # Faisl
    pass_n = sum(1 for _, ok in _results if ok)
    fail_n = len(_results) - pass_n
    print("=" * 60)
    print("VIDEO-QA v2: PASS=%d FAIL=%d (of %d)  [%.1f min]" %
          (pass_n, fail_n, len(_results), (time.time() - t_all) / 60.0))


if __name__ == "__main__":
    main()
