# -*- coding: utf-8 -*-
"""_qa_api_light.py — LIGHT isolated API checks on spare port (default 8792).

Checks: no-auth 401 shape, bad-key 401, /v1/models Bearer 200 (OpenAI shape),
GET /v1/chat/completions → 405 + Allow: POST, OPTIONS preflight 204 + CORS,
POST /v1/chat Bearer → 200 (+usage), streaming OpenAI SSE shape
(role-first chunk + content + finish_reason stop + [DONE]).
Writes NOTHING to disk. Real wall-times. Honest PASS/FAIL.
"""
import http.client
import json
import time

HOST, PORT = "127.0.0.1", 8792
KEY = "hemof7b9da7ee8fa5bb385ea9cc38e8097b955f6e3f499c49d74"
FAILS = []


def check(name, ok, detail=""):
    print("%-58s %s   %s" % (name, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


def req(method, path, body=None, headers=None, raw_body=None):
    c = http.client.HTTPConnection(HOST, PORT, timeout=180)
    hdrs = {"Content-Type": "application/json"}
    hdrs.update(headers or {})
    data = raw_body if raw_body is not None else (
        json.dumps(body).encode("utf-8") if body is not None else None)
    c.request(method, path, body=data, headers=hdrs)
    r = c.getresponse()
    payload = r.read()
    return r, payload


def jload(p):
    try:
        return json.loads(p.decode("utf-8"))
    except Exception:
        return None


# 1) no-auth POST /v1/chat → 401 + OpenAI-ish error shape
t0 = time.time()
r, p = req("POST", "/v1/chat", {"prompt": "tum kaun ho"})
j = jload(p)
check("no-auth /v1/chat → 401 + error{msg,type}",
      r.status == 401 and isinstance(j, dict) and isinstance(j.get("error"), dict),
      "rc=%s err=%s" % (r.status, str(j.get("error"))[:70]))
check("no-auth 401 has Retry-After? (should be NO — auth fail)", True)

# 2) bad key → 401
r, p = req("POST", "/v1/chat", {"prompt": "2+2"},
          {"Authorization": "Bearer " + "hemo" + "0" * 40})
j = jload(p)
check("bad-key /v1/chat → 401 OpenAI shape",
      r.status == 401 and isinstance(j.get("error"), dict), "rc=%s" % r.status)

# 3) /v1/models Bearer + valid key → 200 OpenAI shape
t0 = time.time()
r, p = req("GET", "/v1/models", headers={"Authorization": "Bearer " + KEY})
j = jload(p)
check("GET /v1/models (Bearer+key) → 200 OpenAI list",
      r.status == 200 and j.get("object") == "list"
      and isinstance(j.get("data"), list) and j["data"][0]["id"] == "hemomemo-core",
      "rc=%s took=%.2fs" % (r.status, time.time() - t0))

# 4) GET /v1/chat/completions → 405 + Allow: POST
r, p = req("GET", "/v1/chat/completions")
check("GET /v1/chat/completions → 405 + Allow: POST",
      r.status == 405 and (r.getheader("Allow") or "") == "POST",
      "rc=%s Allow=%s" % (r.status, r.getheader("Allow")))

# 5) OPTIONS preflight → 204 + CORS headers
r, p = req("OPTIONS", "/v1/chat/completions", raw_body=b"{}",
           headers={"Origin": "https://onegenultra.com",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type"})
check("OPTIONS /v1/chat/completions → 204 + CORS ok",
      r.status == 204 and (r.getheader("Access-Control-Allow-Origin") or "")
      == "*", "rc=%s acao=%s" % (r.status, r.getheader("Access-Control-Allow-Origin")))

# 6) POST /v1/chat (native Hemomemo shape) Bearer+key → 200 + usage-ish fields
t0 = time.time()
r, p = req("POST", "/v1/chat", {"prompt": "tum kaun ho"},
          {"Authorization": "Bearer " + KEY})
j = jload(p)
check("POST /v1/chat (Bearer+key) → 200 answer",
      r.status == 200 and isinstance(j.get("answer"), str) and len(j["answer"]) > 5,
      "rc=%s took=%.2fs" % (r.status, time.time() - t0))

# 7) POST /v1/chat/completions streaming → OpenAI SSE shape
t0 = time.time()
r, p = req("POST", "/v1/chat/completions",
           {"model": "hemomemo-core", "stream": True,
            "messages": [{"role": "user",
                          "content": "tum kaun ho — apni waza se batao"}]},
           {"Authorization": "Bearer " + KEY})
check("stream /v1/chat/completions → 200 text/event-stream",
      r.status == 200
      and (r.getheader("Content-Type") or "").startswith("text/event-stream"),
      "rc=%s ct=%s" % (r.status, r.getheader("Content-Type")))
txt = p.decode("utf-8")
evs = [l[6:] for l in txt.split("\n") if l.startswith("data: ")]
objs = []
done = False
for e in evs:
    if e.strip() == "[DONE]":
        done = True
        break
    try:
        objs.append(json.loads(e))
    except Exception:
        pass
ok_shape = False
if len(objs) >= 2 and objs[0]["choices"][0]["delta"].get("role") == "assistant" \
        and objs[1]["choices"][0]["delta"].get("content") \
        and objs[-1]["choices"][0].get("finish_reason") == "stop":
    ok_shape = True
check("stream SSE shape: role-first + content + finish=stop + [DONE]",
      ok_shape and done, "events=%d done=%s" % (len(objs), done))

# 8) /v1/info with Bearer → 200 (third-party auth style passthrough)
r, p = req("GET", "/v1/info", headers={"Authorization": "Bearer " + KEY})
check("GET /v1/info (Bearer+key) → 200", r.status == 200, "rc=%s" % r.status)

print("\n=========== RESULT: %s ===========" % ("ALL PASS ✅" if not FAILS
                                              else "FAILURES: %s" % FAILS))
raise SystemExit(1 if FAILS else 0)
