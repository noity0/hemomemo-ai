# -*- coding: utf-8 -*-
"""_frozenfix.py — frozen-aware ROOT patch (EXE folder = Hemomemo folder).

User qanoon: checkpoints / history / data Hemomemo ke APNE folder me save ho —
temp (_MEIPASS) me NAHI — takay link sab se jura rahe.
Pattern wahi jo security/guard.py me already proven hai."""
import io
import os
import py_compile
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\DigitalBrain"

# 2-level pattern: ROOT = dirname(dirname(abspath(__file__)))
TWO = "ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"
TWO_NEW = (
    'if getattr(sys, "frozen", False):\n'
    '    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)\n'
    '    if not (os.path.isdir(os.path.join(ROOT, "model"))\n'
    '            or os.path.isdir(os.path.join(ROOT, "data"))):\n'
    '        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n'
    'else:\n'
    '    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))'
)
# 1-level pattern: HERE = ... \n ROOT = dirname(HERE)
ONE = ('HERE = os.path.dirname(os.path.abspath(__file__))\n'
       'ROOT = os.path.dirname(HERE)')
ONE_NEW = (
    'HERE = os.path.dirname(os.path.abspath(__file__))\n'
    'if getattr(sys, "frozen", False):\n'
    '    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)\n'
    '    if not (os.path.isdir(os.path.join(ROOT, "model"))\n'
    '            or os.path.isdir(os.path.join(ROOT, "data"))):\n'
    '        ROOT = os.path.dirname(HERE)\n'
    'else:\n'
    '    ROOT = os.path.dirname(HERE)'
)

TARGETS_2 = [
    r"core\owner.py", r"core\offline_oath.py", r"core\hub.py", r"core\heart.py",
    r"harvest\harvester.py", r"harvest\net_guard.py", r"server\server.py",
    r"model\verify_brain.py", r"model\understand.py", r"model\think_level.py",
    r"model\metacognition.py", r"model\math_formulas.py", r"model\live_research.py",
    r"model\live_plasticity.py", r"model\helper_brain.py", r"model\deep_brain.py",
    r"model\cognition.py", r"model\autonomous.py", r"model\aqal.py", r"model\feelings.py",
]
TARGETS_1 = [
    r"model\generate.py", r"model\scale.py", r"model\learner.py", r"model\train.py",
    r"harvest\verify.py", r"harvest\setup_verification.py",
    r"knowledge\quran_guard.py", r"knowledge\hadith_guard.py", r"security\hmhz.py",
]


def ensure_sys(text: str) -> str:
    if re.search(r"^import sys\b", text, re.M):
        return text
    m = re.search(r"^import os\b.*$", text, re.M)
    if m:
        return text[:m.end()] + "\nimport sys" + text[m.end():]
    lines = text.splitlines(keepends=True)
    for i, ln in enumerate(lines):
        if ln.startswith("import "):
            lines.insert(i, "import sys\n")
            return "".join(lines)
    return "import sys\n" + text


import re  # noqa: E402

patched, skipped, failed = [], [], []
for rel in TARGETS_2 + TARGETS_1:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        failed.append((rel, "gayib"))
        continue
    src = open(p, encoding="utf-8").read()
    if 'getattr(sys, "frozen"' in src or 'getattr(_sys, "frozen"' in src:
        skipped.append(rel)
        continue
    new = src
    if TWO in new:
        new = new.replace(TWO, TWO_NEW, 1)
    elif ONE in new:
        new = new.replace(ONE, ONE_NEW, 1)
    else:
        failed.append((rel, "pattern-nahi-mila"))
        continue
    new = ensure_sys(new)
    open(p, "w", encoding="utf-8", newline="").write(new)
    try:
        py_compile.compile(p, doraise=True)
        patched.append(rel)
    except Exception as e:
        failed.append((rel, "compile: %s" % str(e)[:60]))

print("PATCHED: %d" % len(patched))
for r in patched:
    print("  ok:", r)
print("SKIPPED (pehle se frozen-aware): %d" % len(skipped))
for r in skipped:
    print("  skip:", r)
print("FAILED: %d" % len(failed))
for r, why in failed:
    print("  FAIL:", r, "->", why)

# ── specials: tokenizer.py DATA_PATH + core/state.py SAVE_DIR + generate CKPT ──
# (1) tokenizer.py
p = os.path.join(ROOT, r"model\tokenizer.py")
s = open(p, encoding="utf-8").read()
if 'getattr(_sys, "frozen"' not in s:
    old = ('DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '
           '"..", "data", "corpus.txt")')
    new = (
        'import sys as _sys\n'
        'if getattr(_sys, "frozen", False):\n'
        '    DATA_PATH = os.path.join(os.path.dirname(_sys.executable), "data",\n'
        '                             "corpus.txt")   # 📦 EXE apna folder\n'
        '    if not os.path.exists(DATA_PATH):\n'
        '        DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),\n'
        '                                  "..", "data", "corpus.txt")\n'
        'else:\n'
        '    DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),\n'
        '                             "..", "data", "corpus.txt")')
    assert old in s, "tokenizer pattern nahi mila"
    s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)
    py_compile.compile(p, doraise=True)
    print("  ok: model\\tokenizer.py (DATA_PATH frozen-aware)")
else:
    print("  skip: model\\tokenizer.py")

# (2) core/state.py
p = os.path.join(ROOT, r"core\state.py")
s = open(p, encoding="utf-8").read()
if 'getattr(_sys, "frozen"' not in s:
    old = ('SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '
           '"..", "core")\nos.makedirs(SAVE_DIR, exist_ok=True)')
    new = (
        'import sys as _sys\n'
        'if getattr(_sys, "frozen", False):\n'
        '    SAVE_DIR = os.path.join(os.path.dirname(_sys.executable), "core")\n'
        'else:\n'
        '    SAVE_DIR = os.path.dirname(os.path.abspath(__file__))\n'
        'os.makedirs(SAVE_DIR, exist_ok=True)')
    assert old in s, "state pattern nahi mila"
    s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)
    py_compile.compile(p, doraise=True)
    print("  ok: core\\state.py (SAVE_DIR frozen-aware)")
else:
    print("  skip: core\\state.py")

# (3) generate.py CKPT_DIR — checkpoints Hamesha EXE folder me
p = os.path.join(ROOT, r"model\generate.py")
s = open(p, encoding="utf-8").read()
old = 'CKPT_DIR = os.path.join(HERE, "checkpoints")'
new = ('CKPT_DIR = os.path.join(ROOT, "model", "checkpoints")\n'
       'if not os.path.isdir(CKPT_DIR) and os.path.isdir(\n'
       '        os.path.join(HERE, "checkpoints")):\n'
       '    CKPT_DIR = os.path.join(HERE, "checkpoints")   # dev-fallback')
if old in s and 'CKPT_DIR = os.path.join(ROOT, "model", "checkpoints")' not in s:
    s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)
    py_compile.compile(p, doraise=True)
    print("  ok: model\\generate.py (CKPT_DIR frozen-aware)")
else:
    print("  skip: model\\generate.py CKPT_DIR")

print("FROZEN-FIX-DONE")
