# -*- coding: utf-8 -*-
"""_audit_run.py — AUDIT step-1: har tests/test_*.py chalao (120s timeout).
Har test ke liye: PASS/CRASH/TIMEOUT + asserts/testfns count (fake-PASS
scan: 0-assert 'PASS' print karne wale) + output/err ki aakhri lines."""
import glob
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = r"D:\DigitalBrain"
TDIR = os.path.join(ROOT, "tests")
files = sorted(glob.glob(os.path.join(TDIR, "test_*.py")))
print("TEST-FILES: %d" % len(files))
for f in files:
    name = os.path.basename(f)
    try:
        src = open(f, encoding="utf-8", errors="replace").read()
    except Exception as e:
        print("\n=== %s : READ-FAIL %s" % (name, e))
        continue
    n_assert = len(re.findall(r"\bassert\b", src))
    n_testfn = len(re.findall(r"def\s+test_\w+", src))
    try:
        r = subprocess.run([sys.executable, "-Xutf8", f], capture_output=True,
                           timeout=120, cwd=ROOT)
        rc = r.returncode
        out = (r.stdout or b"").decode("utf-8", "replace")
        err = (r.stderr or b"").decode("utf-8", "replace")
        verdict = "PASS" if rc == 0 else "CRASH rc=%d" % rc
        print("\n=== %s : %s | asserts=%d testfns=%d"
              % (name, verdict, n_assert, n_testfn))
        for line in (out.strip().splitlines() or [""])[-3:]:
            print("  out| " + line[:160])
        for line in (err.strip().splitlines() or [""])[-3:]:
            print("  err| " + line[:160])
    except subprocess.TimeoutExpired:
        print("\n=== %s : TIMEOUT (120s)" % name)
    except Exception as e:
        print("\n=== %s : RUNNER-ERROR %s" % (name, e))
print("\nAUDIT-RUN-DONE")
