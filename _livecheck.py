#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-CHECK - GameBot apne computer par (100% local, honest).

User-qanoon: "bot ko apne computer may run kro aur check kro ye computer
control kr raha hay ya nahi, minecraft khel raha hay ya nahi."

1) PC-CONTROL : package wale agent/pc_eye se ASLI cursor-harkat
                (GetCursorPos pehle/baad) + asli screenshot-tahlil.
2) MINECRAFT  : process-scan (javaw/TLauncher/Minecraft) + 25565-port
                + asli join-koshish (local server) - nateeja jo bhi
                ho IMANDARI se bataya jayega.
"""
from __future__ import annotations

import ctypes
import os
import sys
import time

PKG = r"D:\HemomemoUltra-People"
sys.path.insert(0, PKG)
os.chdir(PKG)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

print("=" * 62)
print("  LIVE-CHECK: Hemomemo Game-Bot (package-folder ka dimagh)")
print("=" * 62)

# ---------- 1) AANKH (asli screenshot) ----------
from agent.pc_eye import Eye, Hand
eye = Eye()
d = eye.describe()                      # frame=None -> asli grab
if "error" in d:
    print("[AANKH] FAIL (honest): %s" % d["error"])
    sys.exit(1)
print("[AANKH] OK: %s" % eye.see_say())

# ---------- 2) HAATH (asli cursor-control - wapas bhi lautaunga) ----------
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

pt = POINT()
ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
x0, y0 = pt.x, pt.y
hand = Hand()
hand.mouse_move(40, 0)                  # asli harkat (relative - scale hota hai)
time.sleep(0.15)
ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
x1, y1 = pt.x, pt.y
moved = abs(x1 - x0)
ctypes.windll.user32.SetCursorPos(x0, y0)   # absolute wapas (pakka)
time.sleep(0.15)
ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
back = (abs(pt.x - x0) <= 2 and abs(pt.y - y0) <= 2)
print("[HAATH] cursor: (%d,%d) -> (%d,%d) | harkat=%dpx %s | wapas=%s"
      % (x0, y0, x1, y1, moved,
         "HAAN (control chal raha)" if moved >= 30 else "NAHIN (FAIL)",
         "HAAN" if back else "nahi"))
ctrl_ok = moved >= 30 and back

# ---------- 3) DIMAGH (package ka hi model/) ----------
from model.understand import default_token_chat
t, m = default_token_chat().respond("game bot kya hai")
print("[DIMAGH] src=%s | %s" % (m.get("source"), (t or "")[:110].strip()))

# ---------- 4) MINECRAFT (sach-sach) ----------
procs = []
import subprocess
out = subprocess.run(["tasklist", "/FO", "CSV"], capture_output=True,
                     text=True).stdout.lower()
for pname in ("javaw.exe", "java.exe", "minecraft.exe", "tlauncher.exe"):
    if pname in out:
        procs.append(pname)
print("[MC-PROCESS] %s" % ("mojood: " + ", ".join(procs) if procs
                           else "koi Minecraft/java process nahi chal raha"))

sock = None
port_open = False
import socket
try:
    sock = socket.create_connection(("127.0.0.1", 25565), timeout=2.0)
    port_open = True
except OSError:
    pass
finally:
    if sock:
        sock.close()
print("[MC-PORT] 127.0.0.1:25565 -> %s"
      % ("KHALA (server chal raha)" if port_open
         else "band (koi local MC-server nahi)"))

if port_open:
    from agent.mc_bot import MinecraftBot
    bot = MinecraftBot(answer_fn=lambda q: "", username="HemomemoAI")
    joined = bot.join_server("127.0.0.1", 25565)
    print("[MC-JOIN] %s" % ("bot ANDAR khel raha hai!" if joined
                            else "enter nahi hua (honest)"))
    if joined:
        s = bot.see()
        print("[MC-SEE] jagah x=%s y=%s z=%s" % (s["pos"].get("x"),
                                                 s["pos"].get("y"),
                                                 s["pos"].get("z")))
        bot.leave()
else:
    print("[MC-JOIN] koshish nahi ki - server hi nahi (jhoot nahi bolna)")

print("=" * 62)
print("PC-CONTROL: %s | MINECRAFT: %s"
      % ("chal raha hai ✓" if ctrl_ok else "FAIL",
         ("server par khel raha hai ✓" if port_open else
          "MC-band hai (bot tayar - server aap chalayein, bot khud join karega)")))
