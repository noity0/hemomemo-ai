#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CODE-DIMAGH tests - token-se asli code-banai (honest, offline).

6 checks: c++/python print-templates + math/hadith na bigde + UR/EN raste.
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

from model.understand import TokenBrain          # noqa: E402
from model.memory import EpisodicStore           # noqa: E402

b = TokenBrain(generate_fn=None, knowledge=None,
               memory=EpisodicStore(tempfile.mkdtemp()))
RES = []


def chk(no, name, ok, note=""):
    RES.append((no, name, bool(ok), note))


t, m = b.respond("code i love you in c++")
chk(1, "code i love you in c++ -> asli C++ (cout)",
    m["source"] == "code" and "cout" in t and "i love you" in t
    and "#include <iostream>" in t, m["source"])
t, m = b.respond("python me i love you ka code")
chk(2, "python me ... ka code -> print()",
    m["source"] == "code" and "print(" in t and "i love you" in t,
    m["source"])
t, m = b.respond("code hello world in python")
chk(3, "code hello world in python", m["source"] == "code"
    and "hello world" in t, m["source"])
t, m = b.respond("code hjhjkghfgh in c#")
chk(4, "c# zaban (screenshot-bug) -> Console.WriteLine",
    m["source"] == "code" and "Console.WriteLine" in t
    and "hjhjkghfgh" in t, m["source"])
t, m = b.respond("code hello in rust")
chk(5, "rust -> println!", m["source"] == "code" and "println!" in t,
    m["source"])
t, m = b.respond("code hello in go")
chk(6, "go -> fmt.Println", m["source"] == "code" and "fmt.Println" in t,
    m["source"])
t, m = b.respond("code salam in php")
chk(7, "php -> <?php echo", m["source"] == "code" and "echo" in t
    and "<?php" in t, m["source"])
t, m = b.respond("code hi in html")
chk(8, "html -> poora page (h1)", m["source"] == "code"
    and "<!DOCTYPE html>" in t and "<h1>hi</h1>" in t, m["source"])
t, m = b.respond("code hi in sql")
chk(9, "sql -> SELECT", m["source"] == "code" and "SELECT" in t, m["source"])
t, m = b.respond("code hi in assembly")
chk(10, "assembly -> syscall print", m["source"] == "code"
    and "syscall" in t, m["source"])
t, m = b.respond("code hi in cobol")
chk(11, "cobol -> DISPLAY", m["source"] == "code" and "DISPLAY" in t,
    m["source"])
t, m = b.respond("code hi in hemolang")
chk(12, "ghair-maujood zaban -> imandari-listing",
    "nahi" in t and "jaanta hoon" in t, m["source"])
t, m = b.respond("java me salam ka code")
chk(13, "roman-rasta (java me ... ka code) -> System.out",
    m["source"] == "code" and "System.out" in t, m["source"])
t, m = b.respond("2 + 2")
chk(14, "math bigda nahi (2+2=4)", m["source"] == "math" and "= 4" in t,
    m["source"])
t, m = b.respond("hadith batao")
chk(15, "hadith code na bane (bina-knowledge imandari/ilm)",
    m["source"] in ("ilm", "imandari"), m["source"])
t, m = b.respond("who is sex")
chk(16, "purana-bug salam (identity-dump nahi)",
    m["source"] in ("ilm", "imandari")
    and "name" not in t.lower()[:60], m["source"])

print("=" * 62)
fails = [r for r in RES if not r[2]]
for no, name, ok, note in RES:
    print("  %s [%d] %s%s" % ("PASS" if ok else "FAIL", no, name,
                              (" | " + note) if note and not ok else ""))
print("=" * 62)
print("CODE-TESTS: %d | PASS: %d | FAIL: %d"
      % (len(RES), len(RES) - len(fails), len(fails)))
sys.exit(1 if fails else 0)
