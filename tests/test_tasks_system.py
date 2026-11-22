#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TASK/SEKH-SYSTEM tests - Game-Bot ka kaam-sikhna (honest, offline).

12 checks: sekho (memory+file) / plan (token+qadam) / kaam (start->end,
memory-save) / router (dono raste).
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from model.memory import EpisodicStore, KnowledgeRetrieval  # noqa: E402
from agent.tasks import TaskSystem, handle, Plan            # noqa: E402

RES = []


def chk(no, name, ok, note=""):
    RES.append((no, name, bool(ok), note))


tmp = tempfile.mkdtemp()
mem = EpisodicStore(tmp)
corpus = os.path.join(tmp, "corpus_big", "gamebot_tasks.txt")
ts = TaskSystem(mem, corpus)

# ---- SEKH (1-4)
out = ts.learn("game me gadda kaise khodo", "w se aage chalo, mouse se dekho")
chk(1, "sekho -> 'seekh gaya' + token-ginti", "seekh gaya" in out, out[:80])
recs = mem.recall("gadda khodo", k=3)
chk(2, "sekho -> episodic-memory me mehfooz",
    any("task_sekho:" in str(r.get("bot", "")) for r in recs))
chk(3, "sekho -> data-file (Sawal:/Jawab:)",
    os.path.exists(corpus)
    and "Sawal: game me gadda kaise khodo" in open(corpus, encoding="utf-8").read())
chk(4, "sekho adhoora -> honest-mana",
    "[honest]" in ts.learn("", ""))

# ---- PLAN (5-8)
p = ts.plan("chal 3 phir jump")
chk(5, "plan: 2 qadam (phir se toota)", len(p.steps) == 2 and p.tokens > 0,
    p.describe())
chk(6, "plan qadam-1 = order aage",
    p.steps[0].kind == "order" and p.steps[0].action == "aage")
chk(7, "plan qadam-2 = order jump", p.steps[1].action == "jump")
p2 = ts.plan("kaam kya hai minecraft")
chk(8, "plan: aam-baat par ilm/brain qadam", p2.steps[0].kind in ("ilm", "brain"),
    p2.describe())

# ---- KAAM (9-10)
chal = []


def fake_exec(s):
    chal.append(s.text)
    return "qadam-chala: %s" % s.text


rep = ts.run("chal 2 phir ruk", executor=fake_exec)
chk(9, "kaam: starting-se-end (2 qadam sahi tarteeb)",
    chal == ["chal 2", "ruk"] and "KAAM-KHATAM: 2/2" in rep, rep[:120])
recs2 = mem.recall("kaam chal ruk", k=3)
chk(10, "kaam -> nateeja memory me save",
    any("kaam_khatam" in str(r.get("bot", "")) for r in recs2))

# ---- ROUTER (11-12)
hua, jawab = handle("sekho test-q = test-jawab", ts)
chk(11, "router: 'sekho' pakra (True)", hua and "seekh gaya" in jawab)
hua2, _ = handle("aam baat - task nahi", ts)
chk(12, "router: aam-baat chhori (False -> dimagh)",
    hua2 is False)

# ---- NATEEJA
print("=" * 62)
fails = [r for r in RES if not r[2]]
for no, name, ok, note in RES:
    print("  %s [%2d] %s%s" % ("PASS" if ok else "FAIL", no, name,
                               (" | " + note) if note and not ok else ""))
print("=" * 62)
print("TASK-TESTS: %d | PASS: %d | FAIL: %d"
      % (len(RES), len(RES) - len(fails), len(fails)))
sys.exit(1 if fails else 0)
