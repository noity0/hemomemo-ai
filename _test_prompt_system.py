# -*- coding: utf-8 -*-
"""_test_prompt_system.py — chat-yaad + code-prompt + error-auto-fix test."""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from model import prompt_system as ps          # noqa: E402
from model import code_exec                    # noqa: E402

fails = []

def chk(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond:
        fails.append(name)

# chat-yaad: pichle turns sandarabh + akhri-sawal 90% (asli-sawal yaad me NAHI)
hist = [
    {"who": "user", "text": "pakistan ka flag kis mulk ka hai?"},
    {"who": "ai", "text": "Ye Pakistan ka sabz-jhanda hai (sitar-chand)."},
    {"who": "user", "text": "code table of 7"},
    {"who": "ai", "text": "[code-gen] table ban gaya..."},
    {"who": "user", "text": "aur factorial of 5 bhi"},
]
cur = "aur factorial of 5 bhi"
ctx = ps.build_chat_context(hist, cur)
chk("ctx khali nahi (pichli-baat maujood)", bool(ctx))
chk("ctx me [CHAT-YAAD] header", "[CHAT-YAAD]" in ctx)
chk("ctx me pichla user-turn", "pakistan ka flag kis mulk ka hai?" in ctx)
chk("ctx me pichla AI-turn", "sabz-jhanda" in ctx)
chk("ctx me [QANOON] 90%-akhri-sawal rule", "90%" in ctx and "AKHRI" in ctx)
chk("ctx me CURRENT-sawal yaad me NAHI (90% core alag)",
    "aur factorial of 5 bhi" not in ctx.split("[QANOON]")[0])
chk("ctx code-prompt trigger (table=code)", "[CODE-SYSTEM]" in ctx)

# sirf-current (koi pichli-baat nahi) + non-code -> yaad khali
chk("sirf-current non-code -> ctx khali",
    ps.build_chat_context([{"who": "user", "text": "salam bhai"}],
                          "salam bhai") == "")

# code-detector
chk("is_code_request('code i love pakistan')", ps.is_code_request("code i love pakistan"))
chk("is_code_request('mere python me error aa raha')", ps.is_code_request("mere python me error aa raha"))
chk("is_code_request('salam kaise ho') == False", not ps.is_code_request("salam kaise ho"))
chk("code_system_prompt khali non-code par", ps.code_system_prompt("salam") == "")

# continuation (canned-clarification skip)
chk("is_continuation('aur wo wala bhi')", ps.is_continuation("aur wo wala bhi"))
chk("is_continuation('pakistan ka darulhukumat?') == False",
    not ps.is_continuation("pakistan ka darulhukumat?"))

# 🩹 coding-error auto-fix: fancy-quotes wala code khud theek-ho-chalta hai
ok, out, err, took = code_exec.run_python('print(\u201csalam-duniya\u201d)')
chk("auto-fix fancy-quotes -> exec-OK", ok and "salam-duniya" in out)
chk("fix_common line-numbers hatata hai",
    "x = 1" in code_exec.fix_common("12: x = 1"))
chk("fix_common unicode-digits -> ASCII",
    code_exec.fix_common("\u0661\u0660") == "10")

print()
if fails:
    print("ALL-TESTS: FAIL (%d) -> %s" % (len(fails), fails))
    sys.exit(1)
print("ALL-TESTS: SAB-PASS")
