# -*- coding: utf-8 -*-
# _server_watch.pyw - Hemomemo local-server 24/7 WATCHER (windowless, 0% CPU)
# - har 5-min: agar _server_OFF.flag nahi AUR port 8790 band ho -> server start
# - matlab: server crash ho jaye to khud wapas; user ne "band karo" kaha ho
#   (flag) to KABHI nahi chumpta - sirf bat-se off, 24/7 on.
import os
import socket
import subprocess
import time

PY = r"C:\Users\user\AppData\Local\Programs\Python\Python312\pythonw.exe"
SRC = r"D:\DigitalBrain"
SERVER = os.path.join(SRC, "server", "hemomemo_server.py")
FLAG = os.path.join(SRC, "data", "_server_OFF.flag")
LOG = os.path.join(SRC, "data", "_server_24x7.log")


def _note(msg):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ") + msg + "\n")
    except Exception:
        pass


def _port_open():
    s = socket.socket()
    s.settimeout(1.0)
    try:
        return s.connect_ex(("127.0.0.1", 8790)) == 0
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


while True:
    try:
        if not os.path.exists(FLAG) and not _port_open():
            subprocess.Popen([PY, "-Xutf8", SERVER], cwd=SRC,
                             creationflags=0x08000000)  # CREATE_NO_WINDOW
            _note("server-start (24x7 watcher)")
    except Exception:
        pass
    time.sleep(300)
