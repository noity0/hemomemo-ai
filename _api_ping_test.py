# -*- coding: utf-8 -*-
"""Local Hemomemo-API test (127.0.0.1:8790 - host-only, koi cloud nahi)."""
import json
import secrets
import time
import urllib.request

BASE = "http://127.0.0.1:8790"
KEY = "hemocb611813be32eaa154ca5aba57f55aa47caedadf0889f73a"


def req(method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if body is not None:
        r.add_header("X-Hemomemo-Key", KEY)
        r.add_header("X-Hemomemo-Ts", str(int(time.time())))
        r.add_header("X-Hemomemo-Nonce", secrets.token_hex(8))
    try:
        with urllib.request.urlopen(r, timeout=90) as h:
            return h.status, h.read().decode("utf-8", "replace")[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except Exception as e:
        return -1, "%r" % (e,)


c, b = req("GET", "/health")
print("[health] %s :: %s" % (c, b))
time.sleep(2.0)
c, b = req("POST", "/v1/chat", {"prompt": "salam app kaun ho tum"})
print("[chat]   %s :: %s" % (c, b))

