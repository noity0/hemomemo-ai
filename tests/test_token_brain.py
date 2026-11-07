"""HEMOMO TOKEN-DIMAGH TESTS - token-system + samajh (100% offline).

Chalana:  py -3 tests\\test_token_brain.py
Har sawal token-dar-token parha jata hai - criteria TOPICAL hain (lafzi
nahi), kyunke dimagh ka jawab mutaliq hona chahiye, lafzi-copy nahi.
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

from model.tokenize import word_tokens, key_tokens, qword, numbers, vars_of, sub_tokens
from model.understand import TokenBrain
from model.memory import EpisodicStore, KnowledgeRetrieval

PASS = 0
FAIL = 0


def check(name, cond, note=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  PASS [%s]" % name)
    else:
        FAIL += 1
        print("  FAIL [%s] %s" % (name, note))


print("== 1) TOKENIZER: todo-samjho ==")
check("word-tokens", word_tokens("Mera naam Hemomemo hai") ==
      ["mera", "naam", "hemomemo", "hai"])
check("key-tokens", key_tokens("python me loop kaise likhein") ==
      ["python", "loop", "kaise", "likhein"])
check("qword-kaun", qword("aap kaun ho?") == "kaun")
check("qword-who", qword("who is sex").startswith("who"))
check("numbers", numbers("circle r = 5 aur 2.5") == [5.0, 2.5])
check("vars", vars_of("E = mc^2, m = 2") == {"m": 2.0})
check("sub-fuzzy", "cir" in sub_tokens("circle") and
      set(sub_tokens("circle")) & set(sub_tokens("circel")) != set())

print("== 2) TOKEN-DIMAGH: poora soch-loop ==")
kr = KnowledgeRetrieval(os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), "data", "corpus_big"))
mem = EpisodicStore(tempfile.mkdtemp())
brain = TokenBrain(generate_fn=None, knowledge=kr, memory=mem)

# math (deterministic - pakka sahi)
t, m = brain.respond("2 + 2")
check("math-2+2", m["source"] == "math" and "4" in t)
t, m = brain.respond("9 * 5 + 9 * 4")
check("math-9x5+9x4", m["source"] == "math" and "81" in t)

# formula (deterministic)
t, m = brain.respond("circle ka area, r = 5")
check("formula-circle", m["source"] == "formula" and "78.5398" in t)
t, m = brain.respond("E = mc^2, m = 2")
check("formula-emc2", m["source"] == "formula" and "joule" in t)

# pehchaan
t, m = brain.respond("aap kaun ho?")
check("identity-ur", m["source"] == "pehchaan" and "Hemomemo" in t)
t, m = brain.respond("what is your name")
check("identity-en", m["source"] == "pehchaan" and "Hemomemo" in t)

# yaad-flow (already-flow)
t, m = brain.respond("mera naam Ahmed hai")
check("yaad-save", m["source"] == "yaad" and "Ahmed" in t)
t, m = brain.respond("mera naam kya hai?")
check("yaad-recall", m["source"] == "yaad" and "Ahmed" in t)

# ilm (token-IDF retrieval) - TOPICAL criteria
t, m = brain.respond("minecraft creeper kya hai")
check("ilm-creeper", m["source"] == "ilm" and
      ("creeper" in t.lower()))
t, m = brain.respond("namaz kitni farz hai")
check("ilm-namaz", m["source"] == "ilm" and
      ("salah" in t.lower() or "namaz" in t.lower() or "prayer" in t.lower()))
t, m = brain.respond("python me loop kaise likhein")
check("ilm-python-loop", m["source"] == "ilm" and
      ("loop" in t.lower() or "for" in t.lower() or "def" in t.lower()))

# samajh ka sab-se-ahem imtihaan: ban-input jawab KHATAM
# (pehle "who is sex" par identity-dump aata tha - ab mutaliq/samajh-dar jawab)
t, m = brain.respond("who is sex")
bad_old_dump = "HMHS Muslim Texture" in t   # purana ghalat jawab
check("samajh-unknown-topic", m["source"] in ("ilm", "imandari")
      and not bad_old_dump and len(t) > 20, "source=%s" % m["source"])

# khaali input - adab
t, m = brain.respond("")
check("khaali-input", "sun" in t.lower() or bool(t))

print("=" * 50)
print("TOKEN-TESTS: %d | PASS: %d | FAIL: %d" % (PASS + FAIL, PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
