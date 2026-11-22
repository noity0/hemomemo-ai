"""HEMOMO API 20-QA LIVE TEST - app-ki-generate-ki-hui key se chat.

Flow (bilkul waise jaise user ne kaha):
  1) packaged app chal rahi hai (127.0.0.1:8790)
  2) APP KHUD nayi hemo... key generate karta hai (signup endpoint)
  3) usi key se 20 sawal (QA) API-par chat hoti hai
  4) har jawab imandari-se PASS/FAIL (topical criteria) - koi jhoot nahi
"""
import json
import sys
import time
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
API = "http://127.0.0.1:8790"


def req(method, path, body=None, key=None, ts=None, nonce=None):
    headers = {"Content-Type": "application/json",
               "User-Agent": "hemomemo-qa20/1.0"}
    if key:
        headers["X-Hemomemo-Key"] = key
        headers["X-Hemomemo-Ts"] = str(ts if ts is not None else int(time.time()))
        headers["X-Hemomemo-Nonce"] = nonce or ("qa20" + str(time.time_ns()))
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "ignore")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:200]}
    except Exception as e:
        return 0, {"raw": str(e)}


# ---- 1) app se NAYI key (hemo...) ----
email = "qa20live%d@gmail.com" % (int(time.time()) % 1000000)
c, j = req("POST", "/v1/auth/signup", {"email": email, "password": "raaz786"})
KEY = j.get("key", "")
print("KEY-GEN: c=%d key=%s..." % (c, KEY[:12]))
assert c == 200 and KEY.startswith("hemo"), "app ne key nahi banai: %s" % j

# ---- 2) 20 QA (har tarah - wahi jo app ke chips mein bhi hain) ----
QA = [
    # (sawal, source-hone-chahiye, keywords-mei-se-kitne-chahiye, keywords)
    ("salam",                       None,          1, ["alaikum", "salam", "sun", "khush"]),
    ("aap kaun ho?",                "pehchaan",    1, ["hemomemo", "hmhs"]),
    ("2 + 2",                       "math",        1, ["4"]),
    ("circle ka area, r = 5",       "formula",     2, ["formula", "78.53", "area"]),
    ("E = mc^2, m = 2",             "formula",     2, ["formula", "joule"]),
    ("hadith batao",                "ilm",         1, ["hadith", "sunnah", "nabi", "muhammad", "ilm-khazane"]),
    ("minecraft creeper kya hai",   "ilm",         1, ["creeper", "blast", "explode", "mob", "dhamaka"]),
    ("python me loop kaise likhein","ilm",         1, ["for", "loop", "range", "def", "while"]),
    ("who is sex",                  None,          0, []),  # ban-input dump NAHI hona chahiye (koi bhi source - bas mutaliq ho)
    ("namaz kitni farz hai",        "ilm",         1, ["salah", "namaz", "prayer", "farz", "five", "paanch"]),
    ("quran mein kitni surahs hain","ilm",         1, ["114", "surah", "ilm-khazane", "wazah"]),
    ("mera naam Bilal hai",         "yaad",        1, ["bilal", "yaad"]),
    ("mera naam kya hai?",          "yaad",        1, ["bilal"]),
    ("c++ me function kaise banayein","ilm",       1, ["int", "void", "return", "function", "def", "ilm-khazane"]),
    ("enderman kahan spawn hota hai","ilm",        1, ["enderman", "spawn", "end", "dark", "ilm-khazane"]),
    ("roza kis maheene mein hai",   "ilm",         1, ["ramadan", "ramzan", "sawm", "roza", "ilm-khazane"]),
    ("zakat ka nisab kya hai",      "ilm",         1, ["zakat", "nisab", "maal", "silver", "chandi", "ilm-khazane"]),
    ("14 * 12 - 29",                "math",        1, ["139"]),
    ("(22 + 6) * 8",                "math",        1, ["224"]),
    ("dua before sleeping",         "ilm",         1, ["dua", "sleep", "sote", "ilm-khazane"]),
]

ok = bad = 0
fails = []
print("\n== 20-QA LIVE (app-ki-key se) ==")
for i, (q, want_src, min_hits, kws) in enumerate(QA, 1):
    c, j = req("POST", "/v1/chat", {"prompt": q}, key=KEY)
    ans = str(j.get("answer", "")) if isinstance(j, dict) else ""
    src = (j.get("meta", {}) or {}).get("source", "?") if isinstance(j, dict) else "?"
    if q == "who is sex":
        # imandari ntiha: purana ban-input dump NAHI - mutaliq/adab jawab
        good = (c == 200 and ans and
                "HMHS Muslim Texture" not in ans and
                "I am HMHS" not in ans and len(ans) > 15)
    elif want_src == "math":
        good = c == 200 and src == want_src and any(k in ans for k in kws)
    elif want_src is None:
        good = c == 200 and bool(ans.strip())
    else:
        hits = sum(1 for k in kws if k.lower() in ans.lower())
        good = c == 200 and hits >= min_hits
    ok += good
    bad += (not good)
    tag = "PASS" if good else "FAIL"
    print("  %s [%2d] %-32s src=%-9s c=%d" % (tag, i, q[:32], src, c))
    if not good:
        print("       jawab: %s" % ans[:170].replace("\n", " | "))
        fails.append((q, c, src, ans[:120]))

print("=" * 56)
print("20-QA: PASS=%d FAIL=%d (of %d)" % (ok, bad, len(QA)))
if fails:
    print("\nFIX-LIST:")
    for q, c, src, a in fails:
        print("  - %s (c=%d src=%s) %s" % (q, c, src, a[:90]))
sys.exit(0 if bad == 0 else 1)
