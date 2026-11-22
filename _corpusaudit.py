# -*- coding: utf-8 -*-
"""QA-CORPUS deep-audit (read-only): hard-pairs count har data-file me."""
import io
import os
import re

BIG = r"D:\DigitalBrain\data\corpus_big"
for f in ["coding_knowledge.txt", "coding_deep_master.txt",
          "games_knowledge.txt", "agent_orders.txt", "gamebot_tasks.txt"]:
    p = os.path.join(BIG, f)
    try:
        c = io.open(p, encoding="utf-8", errors="ignore").read()
    except Exception as e:
        print("%-28s FAIL %s" % (f, e))
        continue
    pairs = re.findall(r"Sawal:\s*(.+?)\s*\nJawab:\s*(.+?)(?=\n\S|\Z)", c)
    hard = [q for q, a in pairs if len(a) > 60]
    print("%-28s pairs=%5d hard(>60)=%4d" % (f, len(pairs), len(hard)))
