# -*- coding: utf-8 -*-
import io, os, re, sys, pickle, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"D:\DigitalBrain\data\corpus_big\learned_chat.txt"
t = open(p, encoding="utf-8").read()
blocks = re.split(r"(?=# h: )", t)
kept, dropped = [], 0
for b in blocks:
    if not b.strip():
        continue
    m = re.search(r"Sawal:\s*(.+)", b)
    q = (m.group(1).strip() if m else "ok")
    bad = (len(q) <= 2 or "Web ( live" in b or "Security-Layer" in b
           or ("Hal ki soch" in b and re.match(r"^[\d+\-*/^%!xX]", q) is not None))
    if bad:
        dropped += 1
        continue
    kept.append(b)
open(p, "w", encoding="utf-8").write("".join(kept))
print("LEARNED-CLEANUP dropped=%d kept=%d" % (dropped, len(kept)))
p2 = r"D:\DigitalBrain/data/qa_memo.pkl"
d = pickle.load(open(p2, "rb"))
qa = d.get("qa", [])
qa2 = [e for e in qa if not (isinstance(e, (tuple, list)) and len(str(e[0]).strip()) <= 2)]
d["qa"] = qa2
pickle.dump(d, open(p2, "wb"))
print("QA-MEMO purged: %d -> %d" % (len(qa), len(qa2)))
p3 = r"D:\DigitalBrain/data/hemomemo_users.json"
u = json.load(open(p3, encoding="utf-8"))
bad = [k for k in u.get("users", {}) if ("qa" in k.lower() or "test" in k.lower())]
for k in bad:
    del u["users"][k]
json.dump(u, open(p3, "w", encoding="utf-8"), indent=1)
print("QA-USERS removed:", bad)
