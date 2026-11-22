"""HEMOMO AGENT-POWERS TESTS - mc-bot aankhein/harkat + pc-eye + modes.

Chalana:  py -3 tests\\test_agent_powers.py
100% offline-safe: asli screen/mouse/server ko chhua NAHI jata
(structure + synthetic-frame hi parha jata hai) - honest PASS/FAIL.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

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


print("== 1) MC-BOT: framing (offline-safe) ==")
from agent.mc_bot import (MinecraftBot, write_varint, pack_packet,
                          _mc_string, _read_mc_string, duo_play)


def _rvint(data: bytes, idx: int = 0):
    num, shift = 0, 0
    while True:
        b = data[idx]
        num |= (b & 0x7F) << shift
        idx += 1
        if not (b & 0x80):
            break
        shift += 7
    return num, idx


for v in (0, 1, 127, 128, 300, 763, 65536):
    enc = write_varint(v)
    dec, _ = _rvint(enc)
    check("varint-%d" % v, dec == v)

s = "Assalam-o-alaikum Hemomemo!"
enc = _mc_string(s)
ln, used = _rvint(enc)
check("mc-string-roundtrip", _read_mc_string(enc) == s and used == len(enc) - ln)

print("== 2) MC-BOT: aankhein + harkat (fail-closed, bina server) ==")
b = MinecraftBot(answer_fn=lambda q: "test-jawab", username="HemomemoAI")
st = b.see()
check("see-structure", st["name"] == "HemomemoAI" and "pos" in st
      and "chat_tail" in st)
check("move-fail-closed", b.move_step(dx=1.0) is False)
check("look-fail-closed", b.look(45.0, 10.0) is False)
check("say-fail-closed", b.say("salam") is False)
b.pos.update({"x": 10.0, "y": 64.0, "z": -5.0, "yaw": 90.0})
check("see-pos", b.see()["pos"]["x"] == 10.0)
b._on_chat("<Ali> salam Hemomemo!")
check("chat-log-aankh", len(b.see()["chat_tail"]) == 1)

print("== 3) PC-EYE: aankh (synthetic frame - asli screen nahi) ==")
import numpy as np
from agent.pc_eye import Eye, Hand, watch_and_report, play_with_eyes

eye = Eye()
frame = np.zeros((200, 320, 3), dtype=np.uint8)
frame[:, :] = [120, 90, 60]
d1 = eye.describe(frame)
check("eye-size", d1["size"] == [320, 200])
check("eye-raushni", abs(d1["raushni"] - 90.0) < 1.0)
d2 = eye.describe(frame)
check("eye-sannata", d2["harkat"] == 0.0)
frame[0:50, :] = [255, 255, 255]
d3 = eye.describe(frame)
check("eye-harkat", d3["harkat"] > 0)
check("eye-grid", len(d1["grid"]) == 4 and len(d1["grid"][0]) == 4)
say_lines = []
watch_and_report(2, 0.1, say=say_lines.append)
check("watch-report", len(say_lines) == 2 and all("aankh" in l for l in say_lines))

print("== 4) HAND: structure (koi asli click NAHI) ==")
h = Hand()
for m in ("key", "walk_forward", "jump", "mouse_move", "mouse_look",
          "mouse_click"):
    check("hand-%s" % m, callable(getattr(h, m, None)))

print("== 5) MODES: sab hukum wired ==")
from agent import modes
check("modes-run", callable(modes.run))
check("modes-act", callable(modes._pc_act))

print("== 6) ORDERS: EXE-console + MC-chat ka hukum-dimagh ==")
from agent.orders import parse, describe
from agent import console_app as ca

_ot = [("Hemomemo chal", "aage"), ("ruk jao", "ruk"),
       ("Hemomemo jump", "jump"), ("ghum 180", "ghum"),
       ("chal 5", "aage"), ("hal batao", "hal"),
       ("khatam", "khatam"), ("peeche jao", "peeche"),
       ("baen mudo", "baen"), ("daen mudo", "daen"),
       ("minecraft creeper kya hai", "chat")]
for t, want in _ot:
    o = parse(t)
    check("order-%s" % t[:18], o.action == want,
          "mila=%s" % o.action)
o = parse("ghum 180")
check("order-ghum-angle", o.action == "ghum" and o.angle == 180.0)
o = parse("chal 5")
check("order-meter", o.action == "aage" and o.meters == 5.0)
check("console-structure", callable(ca.pc_direct) and callable(ca.pc_watch)
      and callable(ca.mc_join) and callable(ca._esc_dabaa)
      and callable(ca._brain_answer) and callable(ca.main))

print("=" * 50)
print("AGENT-TESTS: %d | PASS: %d | FAIL: %d" % (PASS + FAIL, PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)
