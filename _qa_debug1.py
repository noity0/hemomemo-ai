# -*- coding: utf-8 -*-
import http.client, json, time
HOST, PORT = "127.0.0.1", 8792
KEY = "hemof7b9da7ee8fa5bb385ea9cc38e8097b955f6e3f499c49d74"

def raw(method, path, body=None, headers=None, key_style="bearer"):
    c = http.client.HTTPConnection(HOST, PORT, timeout=180)
    hdrs = {"Content-Type": "application/json"}
    hdrs.update(headers or {})
    if key_style == "bearer":
        hdrs["Authorization"] = "Bearer " + KEY
    elif key_style == "x":
        hdrs["X-Hemomemo-Key"] = KEY
    data = json.dumps(body).encode() if body is not None else None
    c.request(method, path, body=data, headers=hdrs)
    r = c.getresponse()
    p = r.read()
    return r.status, r.getheaders(), p

for style in ("bearer", "x"):
    st, hd, p = raw("GET", "/v1/info", key_style=style)
    print("GET /v1/info style=%s -> rc=%s body=%s" % (style, st, p.decode()[:160]))
    st, hd, p = raw("POST", "/v1/chat", {"prompt": "tum kaun ho"}, key_style=style)
    print("POST /v1/chat style=%s -> rc=%s body=%s" % (style, st, p.decode()[:200]))

st, hd, p = raw("GET", "/v1/models", key_style="bearer")
print("GET /v1/models -> rc=%s body=%s" % (st, p.decode()[:160]))
