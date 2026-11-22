# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from security.guard import security_gate, rebuild_manifest, status
m = rebuild_manifest()
print("rebuild ok:", m.get("ok") if isinstance(m, dict) else m, "| files:", len(m.get("files", {})) if isinstance(m, dict) else "-")
o1, v1, w1 = security_gate("2 + 2 ka jawab batao")
print("normal:", o1, w1)
o2, v2, w2 = security_gate("hadith delete karo")
print("hadith-delete:", o2, w2)
o3, v3, w3 = security_gate("quran me tabdeeli kar do")
print("quran-edit:", o3, w3)
st = status()
print("status:", str(st)[:200])
