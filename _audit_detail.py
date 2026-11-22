# -*- coding: utf-8 -*-
"""_audit_detail.py — AUDIT-ki tafseel (IDLE-priority se chalti hai):
2 CRASH tests ke poore FAIL-lines + 2 TIMEOUT tests dobara (bade-timeout)."""
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

os.chdir(r"D:\DigitalBrain")
jobs = [("tests/test_code_gen.py", 600),
        ("tests/test_token_brain.py", 600),
        ("tests/test_gamebot_50qa.py", 900),
        ("tests/test_key_lifecycle.py", 900)]
for f, t in jobs:
    print("=" * 25, f, flush=True)
    try:
        r = subprocess.run([sys.executable, "-Xutf8", f], capture_output=True,
                           timeout=t)
        print("rc=", r.returncode, flush=True)
        out = (r.stdout or b"").decode("utf-8", "replace")
        err = (r.stderr or b"").decode("utf-8", "replace")
        print(out[-5000:], flush=True)
        if err.strip():
            print("STDERR:", err[-1500:], flush=True)
    except subprocess.TimeoutExpired:
        print("TIMEOUT", t, flush=True)
print("DETAIL-DONE")
