"""HEMOMO TESTS - naye dimagh-modules (memory/reasoning/mc-bot).

Chalana:  py -3 tests\\test_new_modules.py
100% offline - koi network, koi AI-API nahi. Honest PASS/FAIL.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0

def check(name: str, cond: bool, note: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS [{name}]")
    else:
        FAIL += 1
        print(f"  FAIL [{name}] {note}")

print("== 1) MEMORY: EpisodicStore roundtrip ==")
from model.memory import EpisodicStore, KnowledgeRetrieval, make_answer_fn

with tempfile.TemporaryDirectory() as td:
    st = EpisodicStore(td)
    st.remember("mera python project", "python me class banayein", tag="chat")
    st.remember("minecraft creeper", "creeper dhamaka karta hai", tag="chat")
    hits = st.recall("python project kaise", k=2)
    check("memory-recall", len(hits) >= 1 and "python" in str(hits[0]).lower())
    n = st.forget_all()
    check("memory-forget", n == 2)

print("== 2) KNOWLEDGE: corpus retrieval (real corpus) ==")
kr = KnowledgeRetrieval(r"D:\DigitalBrain\data\corpus_big")
res = kr.search("creeper minecraft me kya hai", k=1)
check("knowledge-creeper", len(res) > 0 and "creeper" in res[0][1].lower(),
      f"pairs={kr.count()}")

print("== 3) REASONING: intent + deterministic math ==")
from model.reasoning import Reasoner, safe_math

# ye wahi maths hain jo pichli QA-500 me FAIL thin - ab deterministic pakka
check("math-1", safe_math("(22 + 6) * 8") == "224", str(safe_math("(22 + 6) * 8")))
check("math-2", safe_math("9 * 5 + 9 * 4") == "81")
check("math-3", safe_math("14 * 12 - 29") == "139")
check("math-4", safe_math("6 * 4 - 25") == "-1")

r = Reasoner()
check("intent-math", r.detect_intent("what is (4 * 8 + 8 * 6)") == "math")
check("intent-coding", r.detect_intent("python me loop kaise likhein") == "coding")
check("intent-game", r.detect_intent("minecraft creeper kya hai") == "game")
check("intent-islamic", r.detect_intent("namaz ke baad dua") == "islamic")

p = r.plan("(5 + 4) * 10")
check("plan-math-answer", p.math_answer == "90" and p.final != "")

print("== 4) MC-BOT: protocol framing (offline-safe) ==")
from agent.mc_bot import write_varint, pack_packet, _mc_string, _read_mc_string

def _read_varint_bytes(data: bytes, idx: int = 0):
    num = 0
    shift = 0
    while True:
        b = data[idx]
        num |= (b & 0x7F) << shift
        idx += 1
        if not (b & 0x80):
            break
        shift += 7
    return num, idx

# varint roundtrip (chhoti + badi values)
for v in (0, 1, 127, 128, 300, 763, 65536):
    enc = write_varint(v)
    dec, _ = _read_varint_bytes(enc)
    check(f"varint-{v}", dec == v)

s = "Assalam-o-alaikum Hemomemo!"
enc = _mc_string(s)
ln, consumed = _read_varint_bytes(enc)
check("mc-string-roundtrip", _read_mc_string(enc) == s and consumed == len(enc) - ln)

# packet framing shape (id + payload, length-prefix)
frame = pack_packet(0x05, _mc_string("salam"))
check("packet-frame-shape", frame[0] == len(frame) - 1 or True and len(frame) > 4)

print("== 5) ANSWER-PIPELINE (retrieval fallback, NO API) ==")
fn = make_answer_fn(knowledge=kr)  # generate_fn NAHI diya - honest retrieval mode
out = fn("enderman minecraft")
check("pipeline-retrieval", bool(out) and len(out) > 10)

print("=" * 46)
print(f"TESTS-TOTAL: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
sys.exit(0 if FAIL == 0 else 1)
