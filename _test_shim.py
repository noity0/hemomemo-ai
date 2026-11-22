# -*- coding: utf-8 -*-
"""Isolated test: new OpenAI-shape routes on spare port 8791 (no brain calls).
Covers: 401-shape (no auth), /v1/models list (Bearer master), 413-shape (big
body), /docs. Real chat-through-shim test runs later (after video-QA)."""
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = r"D:\DigitalBrain"
PORT = 8791
BASE = "http://127.0.0.1:%d" % PORT
KEY = str(json.load(open(os.path.join(ROOT, "data", "hemomemo_api.json"),
                         encoding="utf-8"))["key"])


def req(method, path, body=None, key=None, big=False):
    data = None
    if big:
        data = b"x" * (11 * 1024 * 1024)          # 11MB > 64KB cap
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
    r = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None and not big:
        r.add_header("Content-Type", "application/json")
    if key:
        r.add_header("Authorization", "Bearer %s" % key)
    try:
        with urllib.request.urlopen(r, timeout=30) as h:
            return h.status, h.read().decode("utf-8", "replace")[:300]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:
        return -1, "%r" % (e,)


# launch isolated server (new code with shims)
proc = subprocess.Popen(
    [sys.executable, "-X", "utf8",
     os.path.join("server", "hemomemo_server.py"), "start", str(PORT),
     "127.0.0.1"],
    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
ready = False
for _ in range(40):
    try:
        c, b = req("GET", "/docs")
        if c == 200:
            ready = True
            break
    except Exception:
        pass
    time.sleep(0.5)
else:
    print("child output:", (proc.stdout or b"").read()[:400])
print("server ready:", ready, "(pid %s)" % proc.pid)
if ready:
    c, b = req("POST", "/v1/chat/completions", {"messages": [
        {"role": "user", "content": "hi"}]})
    print("[no-auth 401-shape] ", c, "::", b)
    c, b = req("GET", "/v1/models", key=KEY)
    print("[models list]        ", c, "::", b)
    c, b = req("POST", "/v1/chat/completions",
               {"messages": [{"role": "user", "content": "x"}]}, big=True)
    print("[big-body 413-shape] ", c, "::", b)
proc.terminate()
try:
    proc.wait(timeout=10)
except Exception:
    proc.kill()
print("ISOLATED TEST DONE")
