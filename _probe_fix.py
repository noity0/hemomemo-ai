# -*- coding: utf-8 -*-
"""_probe_fix.py — OpenCode-ki-REAL-shape probe (deep-fix verification).

System me "0-9"-jaisa pattern jaan-boojh kar rakha hai (jo pehle
nonsense-calculator-fallback jala raha tha). Sraf fix ke baad bhi jawab
asli brain ka hona chahiye — "hisab: 0-9 = -9" NAHI.
"""
import json
import time
import urllib.request

KEY = "hemof7b9da7ee8fa5bb385ea9cc38e8097b955f6e3f499c49d74"
BODY = {"model": "hemomemo-core", "messages": [
    {"role": "system",
     "content": "You are an expert coding agent. Numbers 0-9 and symbols "
                "may appear. Task expressions like 0-9 and 1-2 must be "
                "computed by tools. Keep tool_call disabled."},
    {"role": "user", "content": "tum kaun ho, apni banai kisne?"}]}

data = json.dumps(BODY).encode("utf-8")
r = urllib.request.Request("http://127.0.0.1:8791/v1/chat/completions",
                           data=data, method="POST")
r.add_header("Content-Type", "application/json")
r.add_header("Authorization", "Bearer " + KEY)
t0 = time.time()
with urllib.request.urlopen(r, timeout=300) as h:
    j = json.loads(h.read().decode("utf-8"))
print("wall: %.1fs" % (time.time() - t0))
ans = j["choices"][0]["message"]["content"]
print("ANSWER:", ans[:500])
print("DEGEN-CHECK: 'hisab: 0-9 = -9' present?",
      "hisab: 0-9 = -9" in str(ans))
