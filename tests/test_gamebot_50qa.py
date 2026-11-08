#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GAME-BOT 50-QA - sirf CONTROL/READ imtihaan (100% offline, honest).

50 checks: order-parser (20) + Eye-read (12) + Hand-hifazat (6) +
console/spec/app-hisba (6) + dimagh-control-sawal (6).

Imandari-qanoon: koi asli mouse/keyboard NAHI bheja jata (sirf padhna),
koi asli screenshot ke ilawa synthetic-frames - nateejay jaise hain
waise bataye jate hain (PASS/FAIL).
"""
from __future__ import annotations

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                  # noqa: E402
from agent.orders import parse, describe, Order     # noqa: E402
from agent.pc_eye import Eye, Hand, _VK             # noqa: E402
from agent import console_app                       # noqa: E402

RES = []


def chk(no, name, ok, note=""):
    RES.append((no, name, bool(ok), note))


def _src(rel):
    try:
        return open(os.path.join(ROOT, rel), "r", encoding="utf-8",
                    errors="ignore").read()
    except OSError:
        return ""


# ══════════════════════════ A) ORDER-PARSER (20) ══════════
p = parse("chal")
chk(1, "chal -> aage", p.action == "aage", describe(p))
p = parse("chal 5")
chk(2, "chal 5 -> aage + 5.0m", p.action == "aage" and p.meters == 5.0, describe(p))
p = parse("aage 3")
chk(3, "aage 3 -> aage + 3.0m", p.action == "aage" and p.meters == 3.0, describe(p))
p = parse("peeche")
chk(4, "peeche -> peeche", p.action == "peeche", describe(p))
p = parse("peeche 4")
chk(5, "peeche 4 -> peeche + 4.0m", p.action == "peeche" and p.meters == 4.0,
    describe(p))
chk(6, "baen -> baen", parse("baen").action == "baen")
chk(7, "left -> baen (English)", parse("left").action == "baen")
chk(8, "daen -> daen", parse("daen").action == "daen")
chk(9, "right -> daen (English)", parse("right").action == "daen")
chk(10, "jump -> jump", parse("jump").action == "jump")
chk(11, "chalang -> jump (Roman)", parse("chalang").action == "jump")
chk(12, "ruk -> ruk", parse("ruk").action == "ruk")
chk(13, "stop -> ruk (English)", parse("stop").action == "ruk")
chk(14, "hal -> hal (aankhein)", parse("hal").action == "hal")
chk(15, "dekho -> hal (Roman)", parse("dekho").action == "hal")
p = parse("ghum")
chk(16, "ghum -> ghum (bina darjy)", p.action == "ghum" and p.angle is None)
p = parse("ghum 180")
chk(17, "ghum 180 -> 180 darjy", p.action == "ghum" and p.angle == 180.0,
    describe(p))
p = parse("ghum 400")
chk(18, "ghum 400 -> 40 darjy (mod-360)", p.angle == 40.0, describe(p))
chk(19, "khatam -> khatam", parse("khatam").action == "khatam")
chk(20, "aam-baat -> chat (dimagh)", parse("kya hai ilm").action == "chat")

# ══════════════════════════ B) EYE - READ (12) ════════════
eye = Eye()
chk(21, "Eye grid=4", eye.grid == 4)
dark = np.zeros((80, 120, 3), dtype=np.uint8)
d = eye.describe(frame=dark)
chk(22, "dark-frame: error nahi", "error" not in d, str(d)[:60])
chk(23, "dark-frame: raushni 0.0", d.get("raushni") == 0.0)
chk(24, "grid 4-row", len(d.get("grid", [])) == 4)
chk(25, "grid 4-col", all(len(r) == 4 for r in d.get("grid", [])))
chk(26, "size [120,80]", d.get("size") == [120, 80])
chk(27, "ghalba_rang 3-hissa", len(d.get("ghalba_rang", [])) == 3)
chk(28, "pehla-frame harkat 0.0", d.get("harkat") == 0.0)
bright = np.full((80, 120, 3), 255, dtype=np.uint8)
d2 = eye.describe(frame=bright)
chk(29, "bright-frame: raushni 255.0", d2.get("raushni") == 255.0)
chk(30, "harkat > 0 (badal gaya)", d2.get("harkat", 0) > 0.0)
say_b = Eye()
say_b.grab = lambda: bright          # synthetic-frame (asli grab nahi)
chk(31, "see_say bright -> 'raoshan'", "raoshan" in say_b.see_say(),
    say_b.see_say()[:60])
say_d = Eye()
say_d.grab = lambda: dark            # synthetic-frame (asli grab nahi)
chk(32, "see_say dark -> 'taareekh-raat'", "taareekh-raat" in say_d.see_say(),
    say_d.see_say()[:60])

# ══════════════════════════ C) HAND - HIFAZAT (6) ═════════
need = ("w", "a", "s", "d", "space", "enter")
chk(33, "_VK me w/a/s/d/space/enter", all(k in _VK for k in need))
chk(34, "_VK['w'] == 0x57", _VK.get("w") == 0x57)
chk(35, "_VK sab int VK-code", all(isinstance(v, int) for v in _VK.values()))
h = Hand()
chk(36, "Hand.key(ghair-mojood) -> False (kuch nahi bheja)",
    h.key("khoi-chabi-xyz-9") is False)
meths = ("walk_forward", "jump", "mouse_look", "mouse_click", "key")
chk(37, "Hand methods mojood", all(callable(getattr(h, m, None)) for m in meths))
chk(38, "VK_ESC=0x1B + _esc_dabaa() bool (read-only)",
    console_app.VK_ESC == 0x1B and isinstance(console_app._esc_dabaa(), bool))

# ══════════════════════════ D) CONSOLE/SPEC/APP (6) ═══════
con_src = _src("agent/console_app.py")
chk(39, "banner: 'HEMOMEO GAME-BOT' (naam-tabadil)", "HEMOMEO GAME-BOT" in con_src)
chk(40, "console: pc_direct/pc_watch/mc_join mojood",
    all(callable(getattr(console_app, f, None))
        for f in ("pc_direct", "pc_watch", "mc_join")))
chk(41, "pc-direct poora-control: k <key>/click/peeche/baen/daen",
    all(w in con_src for w in ("k ", "click", "peeche", "baen", "daen")))
spec_src = _src("Hemomemo-GameBot.spec")
chk(42, "GameBot-spec: naam + PIL/numpy bundle",
    "name='Hemomemo-GameBot'" in spec_src and "PIL" in spec_src
    and "numpy" in spec_src)
mk_src = _src("scripts/make_package.py")
chk(43, "package: Hemomemo-GameBot.exe + START-GAMEBOT.bat",
    "Hemomemo-GameBot.exe" in mk_src and "START-GAMEBOT.bat" in mk_src)
app_src = _src("app/genone_app.py")
chk(44, "app: live-hub page HATA (Surat-e-Hal nahi)",
    "Surat-e-Hal" not in app_src and "_build_status(" not in app_src)

# ══════════════════════════ E) DIMAGH - CONTROL-SAWAL (6) ═
def _brain():
    from model.understand import default_token_chat
    return default_token_chat()


from model.memory import EpisodicStore, KnowledgeRetrieval  # noqa: E402
import tempfile                                             # noqa: E402
kr = KnowledgeRetrieval(os.path.join(ROOT, "data", "corpus_big"))
br = _brain()
_ok_src = {"math", "formula", "pehchaan", "yaad", "yaad-se", "ilm", "imandari",
           "composer", "soch-pipeline", "live-research", "coding-local",
           "deep-soch", "tarbiyat", "adab"}


def _qa(no, q):
    t, m = br.respond(q)          # (text, meta) - respond_with_memory isi
    src = (m or {}).get("source", "?")   # par mabni hai (wrapper)
    tok = (m or {}).get("tokens", 0) or 0
    chk(no, "dimagh: %s" % q, bool(t and t.strip()) and src in _ok_src
        and tok > 0, "src=%s tok=%s" % (src, tok))


chk(45, "dimagh respond_with_memory mojood (console-raasta)",
    callable(getattr(br, "respond_with_memory", None)))
_qa(46, "Hemomemo bot chal")
_qa(47, "game bot kya hai")
_qa(48, "bot ko order kaise doon")
_qa(49, "bot ruk kaise kare")
_qa(50, "minecraft kya hai")

# ══════════════════════════ NATEEJA ═══════════════════════
print("=" * 62)
fails = [r for r in RES if not r[2]]
for no, name, ok, note in RES:
    print("  %s [%2d] %s%s" % ("PASS" if ok else "FAIL", no, name,
                               (" | " + note) if note and not ok else ""))
print("=" * 62)
print("GAMEBOT-50QA: PASS=%d FAIL=%d (of %d)"
      % (len(RES) - len(fails), len(fails), len(RES)))
sys.exit(1 if fails else 0)
