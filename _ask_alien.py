# -*- coding: utf-8 -*-
"""API se sach ka jawab - 'what is alien' (local-only, honest response)."""
import json
import secrets
import time
import urllib.request

BASE = "http://127.0.0.1:8790"
KEY = "hemocb611813be32eaa154ca5aba57f55aa47caedadf0889f73a"

r = urllib.request.Request(
    BASE + "/v1/chat",
    data=json.dumps({"prompt": "what is alien"}).encode("utf-8"),
    method="POST")
r.add_header("Content-Type", "application/json")
r.add_header("X-Hemomemo-Key", KEY)
r.add_header("X-Hemomemo-Ts", str(int(time.time())))
r.add_header("X-Hemomemo-Nonce", secrets.token_hex(8))
try:
    with urllib.request.urlopen(r, timeout=120) as h:
        print("status:", h.status)
        print(h.read().decode("utf-8", "replace"))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, "::", e.read().decode("utf-8", "replace")[:300])
except Exception as e:
    print("ERR %r" % (e,))
