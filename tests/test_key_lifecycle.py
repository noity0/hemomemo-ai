"""HEMOMO KEY-LIFECYCLE TEST - API key 100% sahi kaam karne ka saboot.

Ye test ASLI packaged app (Hemomemo-Ultra-Brain.exe) ke live API par chalta hai:
  1) signup            -> nayi hemo key milti hai
  2) chat (key se)     -> 200 + jawab (L6: key+ts+nonce)
  3) /v1/auth/me       -> account jaankari
  4) new-key x2        -> 3 keys (hadd poori)
  5) new-key (4th)     -> 429 (free-hadd)
  6) replay-nonce      -> 401 (dobara-wahi-nonce mana)
  7) ghalat key        -> 401
  8) purana ts         -> 401
  9) signin            -> wahi 3 keys wapas
Imandari: har step ka asli result - koi jhoot nahi.
"""
import json
import time
import urllib.request
import urllib.error

API = "http://127.0.0.1:8790"
PASS = 0
FAIL = 0

def req(method, path, body=None, key=None, ts=None, nonce=None):
    headers = {"Content-Type": "application/json",
               "User-Agent": "hemomemo-keytest/1.0"}
    if key:
        headers["X-Hemomemo-Key"] = key
        headers["X-Hemomemo-Ts"] = str(ts if ts is not None else int(time.time()))
        headers["X-Hemomemo-Nonce"] = nonce or ("ntest" + str(time.time_ns()))
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, headers=headers, method=method)
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
        print(f"  PASS [{name}]")
    else:
        FAIL += 1
        print(f"  FAIL [{name}] {note}")

# 1) signup -> pehli APNI key
email = "keytest%d@gmail.com" % (int(time.time()) % 1000000)
c, b = req("POST", "/v1/auth/signup", {"email": email, "password": "raaz786"})
j = json.loads(b) if c == 200 else {}
KEY = j.get("key", "")
check("signup->hemokey", c == 200 and KEY.startswith("hemo"), f"c={c} b={b[:90]}")

# 2) chat (key se) — L6 poora
time.sleep(0.3)
c, b = req("POST", "/v1/chat", {"prompt": "salam, aap kaun ho?"}, key=KEY)
j = json.loads(b) if c == 200 else {}
ans = str(j.get("answer", ""))
check("chat-with-key", c == 200 and len(ans) > 0, f"c={c} b={b[:90]}")

# 3) /v1/auth/me
c, b = req("GET", "/v1/auth/me", key=KEY)
j = json.loads(b) if c == 200 else {}
check("me-endpoint", c == 200 and j.get("email") == email and j.get("key") == KEY,
      f"c={c} b={b[:90]}")

# 4) new-key x2 (hadd: 3)
c2, b2 = req("POST", "/v1/auth/key/new", {}, key=KEY)
j2 = json.loads(b2) if c2 == 200 else {}
K2 = j2.get("key", "")
c3, b3 = req("POST", "/v1/auth/key/new", {}, key=K2 or KEY)
j3 = json.loads(b3) if c3 == 200 else {}
K3 = j3.get("key", "")
check("new-key-2", c2 == 200 and K2.startswith("hemo"), f"c={c2} b={b2[:90]}")
check("new-key-3", c3 == 200 and K3.startswith("hemo"), f"c={c3} b={b3[:90]}")

# 5) chauthi key -> 429 (free-hadd)
c4, b4 = req("POST", "/v1/auth/key/new", {}, key=K3 or KEY)
check("key-limit-429", c4 == 429, f"c={c4} b={b4[:90]}")

# 6) replay-nonce (wahi nonce dobara) -> 401
fixed_nonce = "replaytest123456"
c5, b5 = req("POST", "/v1/chat", {"prompt": "salam"}, key=KEY, nonce=fixed_nonce)
c6, b6 = req("POST", "/v1/chat", {"prompt": "salam"}, key=KEY, nonce=fixed_nonce)
check("replay-nonce-401", c5 == 200 and c6 == 401, f"first={c5} second={c6}")

# 7) ghalat key -> 401
c7, b7 = req("POST", "/v1/chat", {"prompt": "salam"}, key="hemo" + "0" * 48)
check("wrong-key-401", c7 == 401, f"c={c7}")

# 8) purana ts (>120s) -> 401
c8, b8 = req("POST", "/v1/chat", {"prompt": "salam"}, key=KEY,
             ts=int(time.time()) - 500)
check("old-ts-401", c8 == 401, f"c={c8}")

# 9) signin -> wahi 3 keys wapas
c9, b9 = req("POST", "/v1/auth/signin", {"email": email, "password": "raaz786"})
j9 = json.loads(b9) if c9 == 200 else {}
keys9 = j9.get("keys", [])
check("signin-same-keys", c9 == 200 and len(keys9) == 3 and KEY in keys9,
      f"c={c9} keys={len(keys9)}")

# 10) ghalat password -> 403
c10, b10 = req("POST", "/v1/auth/signin", {"email": email, "password": "ghalat"})
check("wrong-pass-403", c10 == 403, f"c={c10}")

print("=" * 50)
print(f"KEY-TESTS: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
import sys
sys.exit(0 if FAIL == 0 else 1)
