# -*- coding: utf-8 -*-
"""_test_codefix.py — code-understanding fix ka live-test (sab local)."""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from model import powers, code_exec  # noqa: E402

fails = []

def chk(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    if not cond:
        fails.append(name)

# T0: wants() routing — bare 'code <desc>' ab code-power hai
w = powers.wants("code i love pakistan with pakistani flag")
chk("wants('code i love pakistan...') -> ('code', ...)",
    w and w[0] == "code" and "pakistan" in (w[1] or ""))
w2 = powers.wants("code chalao print(7*6)")
chk("wants('code chalao print(7*6)') -> ('code', ...)", w2 and w2[0] == "code")
w3 = powers.wants("python print('salam')")
chk("wants('python print(...)') -> ('code', ...)", w3 and w3[0] == "code")
w4 = powers.wants("canvas banao dil")
chk("wants('canvas banao dil') -> canvas parhi rehna chahiye",
    w4 and w4[0] == "canvas")

# T1: user ka asli-mamla — desc -> ASLI-CODE (+ PAK-flag) heading NAHI
t1, m1 = code_exec.smart_code("i love pakistan with pakistani flag")
chk("T1 code-gen source", m1.get("source") == "code-gen")
chk("T1 code-block hai (```python)", "```python" in t1)
chk("T1 PAK-flag ASCII aya", ("###" in t1 and "+" in t1 and "|" in t1))
chk("T1 exec-OK", "OK" in t1)
chk("T1 headline print hua (text= line)", "text = " in t1)
print("-- T1 output (pehla 700) --")
print(t1[:700])

# T2: asli-python seedha chalta hai (purana rasta salamat)
t2, m2 = code_exec.smart_code("print(2+3)")
chk("T2 direct-exec (code-exec source)", m2.get("source") == "code-exec")
chk("T2 output 5", "5" in t2)

# T3: sirf-math desc -> calc
t3, m3 = code_exec.smart_code("25x4")
chk("T3 math-calc Jawab:100", "100" in t3)

# T4: table/factorial samajh
t4, _m4 = code_exec.smart_code("code table of 7")
chk("T4 table-of-7 (70 aya)", "70" in t4)
t5, _m5 = code_exec.smart_code("code factorial of 5")
chk("T5 factorial-5 (120 aya)", "120" in t5)

# T6: khali-hukum
t6, _m6 = code_exec.smart_code("")
chk("T6 khali par madadgar-jawab", "khali" in t6 or "likho" in t6)

# T7: poora-dispatcher rasta (powers.run)
t7, _m7 = powers.run("code", "i love pakistan with pakistani flag")
chk("T7 powers.run code-gen", "```python" in t7 and "OK" in t7)

print()
if fails:
    print("ALL-TESTS: FAIL (%d) -> %s" % (len(fails), fails))
    sys.exit(1)
print("ALL-TESTS: SAB-PASS")
