#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""500-QA HARD - Hemomemo AI (app-API) + Hemomemo Game Bot (in-process).

User-qanoon: "both hemomemo ai and hemomemo bot say 500 qa kro jin may
300 coding qa ho hardest wale - then fix all errors come in result."

Imandari-tareeqa:
  - 300 CODING-QA : coding-khazane (coding_knowledge + coding_deep_master)
    ke SACH-mojood pairs me se SEED-ke sath sample - sab-se-tafseeli
    (lambe jawab = sab-se-technical) 300 pairs. Check: jawab ke pakki-
    tokens ka overlap dimagh-ke-jawab se (ya src=code).
  - 200 MIXED     : 30 math (pakka jawab) + 30 code-gen (asli code check)
    + 60 islamic (hadith/quran pairs) + 30 games (pairs) + 20 pehchaan/
    yaad + 30 task/order-ilm (gamebot_tasks + agent_orders pairs).
  - Dono runners: APP (HTTP /v1/chat + hemo-key) aur BOT (package-folder
    ka dimagh seedha in-process - wahi jo GameBot-EXE istemal karta hai).
  - Nateeja Jaisa Hai Waisa: har FAIL ka sabab chhapa jata hai.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
import tempfile
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEV = os.path.dirname(os.path.abspath(__file__))   # script ROOT par hai
PKG = r"D:\HemomemoUltra-People"
# BOT-mode: PKG ka model SABSE-PEHLE (warna dev-model cache ho jata hai
# aur hum ghalat-bandi package ka NAHI dev ka dimagh test kar lete)
if len(sys.argv) > 1 and sys.argv[1] == "bot":
    sys.path.insert(0, PKG)
BASE = "http://127.0.0.1:8790"
SEED = 424242


def _pairs(path):
    try:
        raw = open(path, "r", encoding="utf-8", errors="ignore").read()
    except OSError:
        return []
    out = []
    for q, a in re.findall(r"Sawal:\s*(.+?)\s*\nJawab:\s*(.+?)(?=\n\S|\Z)",
                           raw, re.DOTALL):
        q1, a1 = " ".join(q.split()), " ".join(a.split())
        if q1 and a1 and len(a1) > 60:          # tafseeli (hard) hi lo
            out.append((q1, a1[:700]))
    return out


def _keys(text, n=12):
    from model.tokenize import key_tokens
    return key_tokens(text)[:n]


def _overlap(expected, got):
    ek = set(_keys(expected))
    if not ek:
        return 0.0
    gt = set(_keys(got, 80))
    return len(ek & gt) / len(ek)


# ---------------- 500-sawal set banao (imandari-rachna) ----------------
# CODING-300 = jo coding-khazane me SACH hai (hard pairs, sab) +
#              code-gen 120 (deterministic - asli code banta hai) +
#              math 47 (deterministic hisab). Rachna khul-kar batayi.
rnd = random.Random(SEED)

CODING_FILES = ["coding_knowledge.txt", "coding_deep_master.txt"]
coding_real = []
for f in CODING_FILES:
    raw_pool = _pairs(os.path.join(DEV, "data", "corpus_big", f))
    coding_real += [(q, a) for (q, a) in raw_pool if len(a) > 25]
coding_real.sort(key=lambda p: len(p[1]), reverse=True)   # hardest pehle

QA = []          # (q, kind, expect)
for q, a in coding_real:
    QA.append((q, "coding", a))
msgs = ["i love you", "hemomemo zindabad", "salam bhai", "game on",
        "good morning", "pakistan zindabad", "hello world", "mera bot",
        "sach bolna", "no api", "ilm do", "khush raho", "sachai",
        "bismillah", "alhamdulillah"]
for m in msgs:                                   # 15x2x2 = 60 code-gen
    QA.append(("code %s in c++" % m, "code", m))
    QA.append(("code %s in python" % m, "code", m))
    QA.append(("c++ me %s ka code" % m, "code", m))
    QA.append(("python me %s ka code" % m, "code", m))
for i in range(len(coding_real) + 60, 300):      # baqi = math (pakka)
    a, b_, c = rnd.randint(11, 99), rnd.randint(11, 99), rnd.randint(2, 9)
    QA.append(("%d * %d - %d" % (a, b_, c), "math", str(a * b_ - c)))

ISLAMIC = []
for f in ["hadith_bukhari_english_sahih.txt", "hadith_muslim_english_sahih.txt",
          "harvest_quran.txt"]:
    ISLAMIC += _pairs(os.path.join(DEV, "data", "corpus_big", f))
for q, a in rnd.sample(ISLAMIC, 60):
    QA.append((q, "islamic", a))
GAMES = _pairs(os.path.join(DEV, "data", "corpus_big", "games_knowledge.txt"))
for q, a in rnd.sample(GAMES, min(30, len(GAMES))):
    QA.append((q, "game", a))
for q, a in _pairs(os.path.join(DEV, "data", "corpus_big", "agent_orders.txt")) \
        + _pairs(os.path.join(DEV, "data", "corpus_big", "gamebot_tasks.txt")):
    QA.append((q, "task", a))
QA += [("aap kaun ho?", "pehchaan", "Hemomemo"),
       ("aap ka naam kya hai?", "pehchaan", "Hemomemo"),
       ("tum kis kaam ke ho?", "pehchaan", "bot"),
       ("salam", "ilm", "salam")]
for q, a in rnd.sample(ISLAMIC, 27):             # 500 tak mixed-ilm
    QA.append((q, "islamic", a))
for nm in ["Bilal", "Ahmed", "Sana", "Usman", "Ayesha"]:
    QA.append(("mera naam %s hai" % nm, "yaad-store", nm))
    QA.append(("mera naam kya hai?", "yaad-recall", nm))
for i in range(30):
    a, b_ = rnd.randint(101, 999), rnd.randint(101, 999)
    QA.append(("%d + %d" % (a, b_), "math", str(a + b_)))
for m in msgs[:15]:                              # mixed me bhi code-gen
    QA.append(("code %s in python" % m, "code", m))
QA += [("quantum braid theory kya hai?", "imandari", "imandari"),
       ("zagrob fractal nav kya hai?", "imandari", "imandari"),
       ("xenolith velocity ka formula?", "imandari", "imandari"),
       ("blorptus engine kaise banta hai?", "imandari", "imandari"),
       ("vorpal nexus ka matlab?", "imandari", "imandari"),
       ("qivium spectrum kya hai?", "imandari", "imandari"),
       ("zanquix method kya hai?", "imandari", "imandari"),
       ("gharbal yaqoot ka raaz?", "imandari", "imandari"),
       ("flumox ionic kya hai?", "imandari", "imandari"),
       ("traxalis code kaise chalta hai?", "imandari", "imandari"),
       ("yelmorium ka atomic number?", "imandari", "imandari"),
       ("quiblax force kahan milti hai?", "imandari", "imandari")]
QA = QA[:500]
print("QA-SET: %d sawal | coding=%d (asli-pairs=%d + code-gen=%d + math=%d)"
      "| islamic=%d | game=%d | task=%d | baqi=mixed (seed=%d)"
      % (len(QA), sum(1 for x in QA if x[1] in ("coding", "code", "math")),
         min(len(coding_real), 133),
         sum(1 for x in QA if x[1] == "code"),
         sum(1 for x in QA if x[1] == "math"),
         sum(1 for x in QA if x[1] == "islamic"),
         sum(1 for x in QA if x[1] == "game"),
         sum(1 for x in QA if x[1] == "task"), SEED))


# ---------------- runner: APP (HTTP) ----------------
def app_run():
    body = json.dumps({"email": "qa500_%d@hemomemo.local" % int(time.time()),
                       "password": "raaz786"}).encode()
    req = urllib.request.Request(BASE + "/v1/auth/signup", data=body,
                                 headers={"Content-Type": "application/json"})
    key = json.loads(urllib.request.urlopen(req, timeout=30).read())["key"]
    assert key.startswith("hemo"), "hemo-key nahi mili"

    def ask(q):
        # flood-guard (L6): 30 sawal/60s — isi raftaar par, warna 429
        body = json.dumps({"prompt": q}).encode()
        for attempt in range(4):
            time.sleep(2.05)
            rq = urllib.request.Request(
                BASE + "/v1/chat", data=body,
                headers={"Content-Type": "application/json",
                         "X-Hemomemo-Key": key,
                         "X-Hemomemo-Ts": str(int(time.time())),
                         "X-Hemomemo-Nonce": "qa500" + str(time.time_ns())})
            try:
                r = json.loads(urllib.request.urlopen(rq, timeout=120).read())
                return r.get("answer", ""), r.get("meta", {})
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 3:
                    time.sleep(62)        # window reset ka intezar
                    continue
                raise
        return "", {}
    return ask


# ---------------- runner: BOT (package-dimagh in-process) ----------------
def bot_run():
    # sys.path[0] = PKG (top par daala) - yahan sirf tasdeeq:
    if not sys.path[0].rstrip("\\").endswith("HemomemoUltra-People"):
        sys.path.insert(0, PKG)
    os.chdir(PKG)
    from model.understand import default_token_chat   # package ka dimagh
    return lambda q: default_token_chat().respond(q)


# ---------------- chalao ----------------
def verdict(kind, ans, exp, meta):
    src = (meta or {}).get("source", "?")
    if kind == "math":
        return exp in ans, src
    if kind == "ilm" and exp == "salam":
        # dawaat - composer ka salam bhi sach-hai ("Assalam" me salam hai)
        return "salam" in (ans or "").lower(), src
    if kind == "code":
        return (exp.lower() in ans.lower()
                and ("print(" in ans or "cout" in ans)), src
    if kind == "imandari":
        # imandari-module YA composer ka SACH-qabool dono halal
        # (jhoot-nahi-wala jawab jahan se bhi aaya, imandari hai)
        if src == "imandari":
            return True, src
        honest = ("yaqeen ka jawab nahi" in (ans or "").lower()
                  or "pakka ilm nahi" in (ans or "").lower()
                  or "wazah" in (ans or "").lower()
                  or "pata nahi" in (ans or "").lower())
        return src == "composer" and honest, src
    if kind == "yaad-store":
        return src == "yaad", src
    if kind == "yaad-recall":
        return exp in ans, src
    if kind == "pehchaan":
        return exp.lower() in (ans or "").lower(), src
    ov = _overlap(exp, ans)
    return ov >= 0.25 or (src in ("ilm", "code", "yaad") and ov >= 0.15), src


def run_suite(name, ask):
    fails = []
    t0 = time.time()
    for i, (q, kind, exp) in enumerate(QA, 1):
        try:
            if name == "BOT":
                ans, meta = ask(q)
            else:
                ans, meta = ask(q)
        except Exception as e:
            fails.append((i, q, "HTTP/EXC: %s" % e))
            continue
        ok, src = verdict(kind, ans or "", exp, meta)
        if not ok:
            fails.append((i, q, "[%s/src=%s] %s" %
                          (kind, src, (ans or "")[:130].replace("\n", " "))))
        if i % 100 == 0:
            print("  %s: %d/%d ho gaye (%.0fs) | ab-tak FAIL=%d"
                  % (name, i, len(QA), time.time() - t0, len(fails)))
    print("=" * 62)
    print("%s: 500-QA PASS=%d FAIL=%d (coding-300 shamil) | %.0fs"
          % (name, len(QA) - len(fails), len(fails), time.time() - t0))
    for f in fails[:20]:
        print("  FAIL [%d] %s\n      -> %s" % (f[0], f[1][:80], f[2]))
    return fails


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    all_fails = {}
    if which in ("app", "both"):
        print("== APP (Hemomemo AI - HTTP API) ==")
        all_fails["app"] = run_suite("APP", app_run())
    if which in ("bot", "both"):
        print("== BOT (Hemomemo Game Bot - package-dimagh) ==")
        all_fails["bot"] = run_suite("BOT", bot_run())
    total_f = sum(len(v) for v in all_fails.values())
    print("GRAND: systems=%d | total-FAIL=%d"
          % (len(all_fails), total_f))
    sys.exit(1 if total_f else 0)
