"""HEMOMO API-ENDPOINTS TEST — HAR darwaza asli-chal-kar sabit.

Live server (http://127.0.0.1:8790 — naya code) par har endpoint ka imandari
test. Sab 100% LOCAL: koi AI-API-key nahi, koi AI-endpoint nahi, koi
AI-connection nahi (/v1/chat/completions sirf OpenAI-SHAPE facade hai —
jawab apna NumPy dimagh deta hai; server chat-path me koi bahar-call nahi
karta — Select-String sabit).

  /health, /v1/info, /v1/models      → 200 (key se) · 401 (bina/ghalat key)
  /v1/chat (POST)                    → 200 · 400 (khali/bad-JSON/khali-prompt)
                                       415 (bad Content-Type) · 401 (ghalat key)
  /v1/chat (GET)                     → 405
  /v1/chat/completions (POST)        → 200 chat.completion · SSE stream ·
                                       400 (khali body/bad-JSON/khali messages)
  /v1/auth/me                        → 200 (apni key) · 401 (ghalat)
  anjaan-rasta                       → 404 (GET) · 405 (POST)
  rate-limit (429)                   → in-process api_gate (asli guard-code,
                                       61st request BLOCK) — live flood NAHI
                                       (shared 60-req window user-ki hai).
Imandari: har check ka asli result — koi jhoot nahi.
"""
import json
import os
import sys
import time
import secrets
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

API = "http://127.0.0.1:8790"
PASS = 0
FAIL = 0


def req(method, path, body=None, key=None, ctype="application/json",
        auth_bearer=None):
    headers = {"User-Agent": "hemomemo-apitest/1.0"}
    if ctype:
        headers["Content-Type"] = ctype
    if key:
        headers["X-Hemomemo-Key"] = key
        headers["X-Hemomemo-Ts"] = str(int(time.time()))
        headers["X-Hemomemo-Nonce"] = "apit" + secrets.token_hex(8)
    if auth_bearer:
        headers["Authorization"] = "Bearer " + auth_bearer
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    r = urllib.request.Request(API + path, data=data, headers=headers,
                               method=method)
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)


def check(name, cond, note=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  PASS [%s]" % name)
    else:
        FAIL += 1
        print("  FAIL [%s] %s" % (name, note))


# 0) setup — apni key (signup, 100% local accounts)
email = "apitest%d@gmail.com" % (int(time.time()) % 1000000)
c, b = req("POST", "/v1/auth/signup",
           json.dumps({"email": email, "password": "raaz786"}))
j = json.loads(b) if c == 200 else {}
KEY = j.get("key", "")
check("signup-apni-key", c == 200 and KEY.startswith("hemo"),
      "c=%s b=%s" % (c, b[:80]))

# 1) /health — zinda-halat
c, b = req("GET", "/health", key=KEY)
jh = {}
try:
    jh = json.loads(b)
except Exception:
    pass
check("health-200-key-se", c == 200 and isinstance(jh, dict) and len(jh) > 0,
      "c=%s b=%s" % (c, b[:80]))
c, b = req("GET", "/health")
check("health-bina-key-401", c == 401, "c=%s b=%s" % (c, b[:80]))
c, b = req("GET", "/health", key="hemo" + "9" * 48)
check("health-ghalat-key-401", c == 401, "c=%s" % c)

# 2) /v1/info — no-AI-oath wali jaankari
c, b = req("GET", "/v1/info", key=KEY)
ji = {}
try:
    ji = json.loads(b)
except Exception:
    pass
check("info-200", c == 200 and isinstance(ji, dict) and len(ji) > 0,
      "c=%s b=%s" % (c, b[:80]))

# 3) /v1/models — OpenAI-shape list (sirf hemomemo-core)
c, b = req("GET", "/v1/models", key=KEY)
check("models-200-core", c == 200 and "hemomemo-core" in b,
      "c=%s b=%s" % (c, b[:80]))
c, b = req("GET", "/v1/models", key="hemo" + "8" * 48)
check("models-ghalat-key-401", c == 401, "c=%s" % c)
c, b = req("GET", "/v1/models", auth_bearer=KEY)
check("models-bearer-shim-200", c == 200 and "hemomemo-core" in b,
      "c=%s b=%s" % (c, b[:80]))

# 4) /v1/chat (GET galat-method)
c, b = req("GET", "/v1/chat", key=KEY)
check("chat-get-405", c == 405, "c=%s b=%s" % (c, b[:80]))

# 5) /v1/chat (POST) — saaf errors
c, b = req("POST", "/v1/chat", json.dumps({"prompt": "salam"}), key=KEY,
           ctype="text/plain")
check("chat-bad-ctype-415", c == 415, "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/v1/chat", None, key=KEY)
check("chat-khali-body-400", c == 400, "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/v1/chat", "{nope-ghalat-json", key=KEY)
check("chat-bad-json-400", c == 400, "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/v1/chat", json.dumps([1, 2, 3]), key=KEY)
check("chat-json-list-400", c == 400, "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/v1/chat", json.dumps({"prompt": "   "}), key=KEY)
check("chat-khali-prompt-400", c == 400, "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/v1/chat", json.dumps({"prompt": "salam"}), key="hemo" + "7" * 48)
check("chat-ghalat-key-401", c == 401, "c=%s" % c)

# 6) /v1/chat (POST) — asli dimagh (LOCAL)
c, b = req("POST", "/v1/chat",
           json.dumps({"prompt": "2+2 kitne hote hain? sirf jawab do"}), key=KEY)
jc = json.loads(b) if c == 200 else {}
check("chat-200-local-dimagh", c == 200 and len(str(jc.get("answer", ""))) > 0
      and isinstance(jc.get("meta", {}), dict),
      "c=%s b=%s" % (c, b[:90]))

# 7) /v1/chat/completions — OpenAI-shape facade (LOCAL dimagh)
c, b = req("POST", "/v1/chat/completions", None, key=KEY)
check("cpl-khali-body-400", c == 400, "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/v1/chat/completions", "{nope", key=KEY)
check("cpl-bad-json-400", c == 400, "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/v1/chat/completions", json.dumps([1]), key=KEY)
check("cpl-json-list-400", c == 400, "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/v1/chat/completions", json.dumps({"messages": []}), key=KEY)
check("cpl-khali-messages-400", c == 400, "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/v1/chat/completions", key="hemo" + "6" * 48,
           body=json.dumps({"messages": [{"role": "user", "content": "salam"}]}))
check("cpl-ghalat-key-401", c == 401, "c=%s" % c)
c, b = req("POST", "/v1/chat/completions", json.dumps(
    {"model": "hemomemo-core",
     "messages": [{"role": "user", "content": "salam, aap kaun ho?"}]}),
    key=KEY)
jj = json.loads(b) if c == 200 else {}
_ch = (jj.get("choices") or [{}])[0]
check("cpl-200-openai-shape",
      c == 200 and jj.get("object") == "chat.completion"
      and len(str(_ch.get("message", {}).get("content", ""))) > 0,
      "c=%s b=%s" % (c, b[:90]))
c, b = req("POST", "/v1/chat/completions", json.dumps(
    {"stream": True,
     "messages": [{"role": "user", "content": "salam"}]}), key=KEY)
check("cpl-stream-sse", c == 200 and "data: [DONE]" in b,
      "c=%s b=%s" % (c, b[:90]))

# 8) anjaan-rasta — asli fail-closed behavior (imandari):
#    - maanoos-shakal anjaan-rasta → saaf 404
#    - anjaan 2-hissa-rasta → L6-HMHZ path-policy BLOCK → 401 (koi path-leak
#      nahi — ye suraksha-hi-sahi hai; policy kabhi kamzor nahi karte)
c, b = req("GET", "/v1/auth/xyz", key=KEY)
check("anjaan-auth-rasta-404", c == 404, "c=%s b=%s" % (c, b[:80]))
c, b = req("GET", "/healthz", key=KEY)
check("anjaan-rasta-404", c == 404, "c=%s" % c)
c, b = req("GET", "/anjaan/rasta", key=KEY)
check("anjaan-2seg-block-401", c == 401 and "BLOCK" in b,
      "c=%s b=%s" % (c, b[:80]))
c, b = req("POST", "/anjaan/rasta", "{}", key=KEY)
check("anjaan-post-405", c == 405, "c=%s" % c)

# 9) /v1/auth/me — apni key ki jaankari
c, b = req("GET", "/v1/auth/me", key=KEY)
jm = json.loads(b) if c == 200 else {}
check("me-200", c == 200 and jm.get("email") == email and jm.get("key") == KEY,
      "c=%s b=%s" % (c, b[:80]))
c, b = req("GET", "/v1/auth/me", key="hemo" + "5" * 48)
check("me-ghalat-key-401", c == 401, "c=%s" % c)

# 10) rate-limit 429 — asli guard-code, in-process (live-flood nahi: shared
#     60-req/10-min window user-ki-app-ki budget hai — kharch nahi karte)
try:
    from security.guard import api_gate
    from server import accounts as _acc          # noqa: F401 (import-path saabit)
    ok60 = True
    blocked = False
    why = ""
    for i in range(1, 90):
        hdr = {"x-hemomemo-key": KEY,
               "x-hemomemo-ts": str(int(time.time())),
               "x-hemomemo-nonce": secrets.token_hex(8)}
        ok, why = api_gate(hdr, "/v1/info", "")
        if ok:
            if i > 60:
                ok60 = False
            continue
        if "rate-limit" in why:
            blocked = (i == 61)
            break
        ok60 = False
        break
    check("rate-60-window-ok", ok60, "i=%s why=%s" % (i, why[:60]))
    check("rate-61st-block", blocked, "i=%s why=%s" % (i, why[:60]))
except Exception as e:
    check("rate-60-window-ok", False, "exc=%s" % str(e)[:80])
    check("rate-61st-block", False, "exc=%s" % str(e)[:80])

print("=" * 50)
print("API-ENDPOINT-TESTS: %d | PASS: %d | FAIL: %d" % (PASS + FAIL, PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
