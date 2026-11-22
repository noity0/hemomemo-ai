# -*- coding: utf-8 -*-
"""_patch_opencode_ctx.py — hemomemo-Core ka context-limit theek karo.

Masla: limit.context = 8000 chota tha — OpenCode ka apna sab-badal-system
(compaction, template wala summary) pehle message par hi chal jata tha aur
chote local dimagh se template-poora summary nahi banta — fail.

Fix (imandari, config-guide ke mutabiq):
  hemomemo-core limit.context 8000 → 16000, output 1200 → 2000
  compaction: buffer 25%, keep.tokens 4000 (agar kabhi zaroorat bhi ho to
  summary+recentteen poori 16k window me fit ho jaye).
freellmapi + baqi sab kuch bilkul NAHI chhera jata.
"""
import json

KEYS = (r"D:\Opencode\config\opencode\opencode.json",
        r"C:\Users\user\.config\opencode\opencode.json")

for path in KEYS:
    d = json.load(open(path, encoding="utf-8"))
    m = d["provider"]["hemomemo"]["models"]["hemomemo-core"]["limit"]
    old_c, old_o = m.get("context"), m.get("output")
    m["context"] = 16000
    m["output"] = 2000
    c = d.setdefault("compaction", {})
    c.setdefault("auto", True)
    c["keep"] = {"tokens": 4000}
    c["buffer"] = "25%"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    chk = json.load(open(path, encoding="utf-8"))
    h = chk["provider"]["hemomemo"]["models"]["hemomemo-core"]["limit"]
    print("%s\n  context %s -> %s | output %s -> %s | buffer=%s keep=%s | "
          "freellmapi salamat: %s" %
          (path, old_c, h["context"], old_o, h["output"],
           chk["compaction"]["buffer"], chk["compaction"]["keep"]["tokens"],
           "freellmapi" in chk["provider"]))
