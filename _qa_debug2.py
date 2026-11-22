# -*- coding: utf-8 -*-
import time, json
from security import guard as G

KEY = "hemof7b9da7ee8fa5bb385ea9cc38e8097b955f6e3f499c49d74"

for path in ("/v1/chat", "/v1/info", "/v1/models", "/health"):
    hdr = {"x-hemomemo-key": KEY, "x-hemomemo-ts": str(int(time.time())),
           "x-hemomemo-nonce": "dbg%d" % (int(time.time() * 1000) % 10 ** 8)}
    ok, why = G.api_gate(hdr, path, '{"prompt":"tum kaun ho"}' if path == "/v1/chat" else "")
    print("GATE %-12s -> ok=%s why=%s" % (path, ok, why))

# layer-level: what does the L6 VM itself say for /v1/chat with full flags
seed, why = G._l6_api("/v1/chat", 1, 1, 1, time.time())
print("L6 _l6_api(/v1/chat,1,1,1) -> seed=%s why=%s" % (seed, why))
seed, why = G._l6_api("/v1/info", 1, 1, 1, time.time())
print("L6 _l6_api(/v1/info,1,1,1) -> seed=%s why=%s" % (seed, why))

# key check
from server import accounts as ACC
print("accounts.valid_key(user):", ACC.valid_key(KEY))
import server.accounts as A
print([x for x in dir(A) if not x.startswith('_')][:40])
