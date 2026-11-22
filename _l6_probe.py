# -*- coding: utf-8 -*-
"""L6-probe: /v1/models / /v1/chat / bad-path — HMHZ policy verdict (local)."""
import secrets
import sys
import time

sys.path.insert(0, r"D:\DigitalBrain")
from security import guard                    # noqa: E402

KEY = "hemocb611813be32eaa154ca5aba57f55aa47caedadf0889f73a"

for path in ("/v1/models", "/v1/chat", "/v1/aata"):
    hdr = {"x-hemomemo-key": KEY,
           "x-hemomemo-ts": str(int(time.time())),
           "x-hemomemo-nonce": secrets.token_hex(8)}
    ok, why = guard.api_gate(hdr, path, "")
    print("gate %-11s -> %s | %s" % (path, ok, why[:70]))

# decoded policy - dekho path-literals
try:
    from security import hmhz as _h
    import os
    code = _h.decode(open(guard.API_POLICY_PATH, encoding="utf-8").read())
    txt = repr(code)
    lit = sorted(set(__import__("re").findall(r"/v1/[a-z/]+", txt)))
    print("policy path-literals:", lit)
    print("policy tail:", txt[-260:])
except Exception as e:
    print("decode probe err: %r" % (e,))
