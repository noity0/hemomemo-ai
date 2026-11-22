# -*- coding: utf-8 -*-
"""_qa_8790.py — verify NEW People EXE (8790) with user key: models + chat."""
import http.client, json, time

HOST, PORT = "127.0.0.1", 8790
KEY = "hemof7b9da7ee8fa5bb385ea9cc38e8097b955f6e3f499c49d74"
FAILS = []


def check(name, ok, detail=""):
    print("%-56s %s   %s" % (name, "PASS" if ok else "FAIL", detail))
    if not ok:
        FAILS.append(name)


def req(method, path, body=None, headers=None):
    c = http.client.HTTPConnection(HOST, PORT, timeout=180)
    hdrs = {"Content-Type": "application/json"}
    hdrs.update(headers or {})
    data = json.dumps(body).encode("utf-8") if body is not None else None
    c.request(method, path, body=data, headers=hdrs)
    r = c.getresponse()
    p = r.read()
    return r, p


H = {"Authorization": "Bearer " + KEY}

r, p = req("GET", "/v1/models", headers=H)
j = json.loads(p.decode("utf-8") or "{}")
check("NEW 8790: GET /v1/models → 200 OpenAI list",
      r.status == 200 and j.get("data", [{}])[0].get("id") == "hemomemo-core",
      "rc=%s" % r.status)

r, p = req("GET", "/v1/info", headers=H)
check("NEW 8790: GET /v1/info → 200", r.status == 200, "rc=%s" % r.status)

r, p = req("POST", "/v1/chat", {"prompt": "tum kaun ho"},
          {"Authorization": "Bearer " + KEY})
j = json.loads(p.decode("utf-8") or "{}")
check("NEW 8790: POST /v1/chat → 200 real answer",
      r.status == 200 and isinstance(j.get("answer"), str) and len(j["answer"]) > 5,
      "rc=%s ans=%.60s" % (r.status, str(j.get("answer"))[:60]))

r, p = req("POST", "/v1/chat/completions",
          {"model": "hemomemo-core", "stream": True,
           "messages": [{"role": "user", "content": "tum kaun ho"}]},
          H)
check("NEW 8790: stream /v1/chat/completions → 200 SSE",
      r.status == 200 and (r.getheader("Content-Type") or "").startswith("text/event-stream"),
      "rc=%s ct=%s" % (r.status, r.getheader("Content-Type")))

print("\n=========== 8790 RESULT: %s ===========" % ("ALL PASS" if not FAILS else FAILS))
raise SystemExit(1 if FAILS else 0)
