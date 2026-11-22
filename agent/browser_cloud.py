# -*- coding: utf-8 -*-
"""HEMOMEMO CLOUD-COMPUTER BROWSER — Obscura headless engine + Hemomemo flow.

User-qanoon (aakhri order): "hemomemo kay liye eik chota cloud computer
create kro jis me ye browser ho https://github.com/h4ckf0r0day/obscura iss
browser ko install kro hemomemo ai kay cloud computer jo ye ai ache say
chale iss browser ko use kre and bandon ko show bhi kre ager bande kahe ya
need ho ... without any other ai api of the world only hemomemo system".

YE MODULE (100% local, koi AI-API nahi):
  - Obscura binary dhoondta hai (PATH / env / known-ghar).
  - `obscura serve` start (CDP port 9222) — headless browser ka server.
  - `obscura fetch <url> --dump text|html --eval ... --screenshot out.png`
    — page fetch/render/screenshot (Hemomemo ka khud dimagh).
  - `obscura mcp --http --port 3000` — MCP server (browser tools).
  - Skill install: Obscura ka `skills/obscura/SKILL.md` ya kisi repo se
    Hemomemo ki skill-registry me (`~/.hemomemo/skills/<name>/SKILL.md`) —
    `install_skill()` se. URL se (urllib — koi AI-API nahi).

CLI: py -3 -m agent.browser_cloud start|stop|fetch|screenshot|mcp|skill
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time

OBSCURA_PORT = 9222
MCP_PORT = 3000
SKILL_NAME = "obscura"
_SKILL_GIT = "h4ckf0r0day/obscura"


def _port_up(port: int, timeout: float = 2.0) -> bool:
    """Kya local port pehle se listening hai (CDP-server)?"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except Exception:
        return False


def obscura_bin() -> str:
    b = os.environ.get("OBSCURA_BIN") or shutil.which("obscura") or ""
    if not b:
        for p in (r"C:\Tools\obscura\obscura.exe",
                  r"C:\Program Files\Obscura\obscura.exe",
                  r"C:\Users\user\Tools\obscura\obscura.exe"):
            if os.path.exists(p):
                b = p
                break
    if not b:
        raise RuntimeError(
            "obscura binary nahi mila - install: "
            "https://github.com/h4ckf0r0day/obscura/releases "
            "(obscura-x86_64-windows.zip -> PATH/C:\\Tools\\obscura).")
    return b


def serve(port: int = OBSCURA_PORT, stealth: bool = True):
    """Obscura CDP server start (cloud-computer ka browser)."""
    if _port_up(port):
        return True, "CDP-server pehle se chal raha (port %d)" % port
    proc = subprocess.Popen(
        [obscura_bin(), "serve", "--port", str(port)]
        + (["--stealth"] if stealth else []),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL)
    serve._proc = proc
    serve._port = port
    time.sleep(3.0)
    return proc.poll() is None, "port %d par serve chal raha" % port


def stop() -> str:
    try:
        if getattr(serve, "_proc", None) is not None:
            serve._proc.terminate()
            try:
                serve._proc.wait(timeout=10)
            except Exception:
                pass
            serve._proc = None
        if _port_up(OBSCURA_PORT):
            return "serve abhi bhi port par up hai (doosri instance)"
        return "serve band kar diya"
    except Exception as e:
        return "serve-stop: %s" % e


def fetch(url: str, dump: str = "text", out: str = None,
         timeout: int = 30, stealth: bool = True) -> str:
    if not _port_up(OBSCURA_PORT):
        ok, st = serve(stealth=stealth)
        if not ok:
            return "SERVE-FAIL: %s" % st
    cmd = [obscura_bin(), "fetch", url, "--dump", dump,
           "--timeout", str(timeout)]
    if stealth:
        cmd += ["--stealth"]
    if out:
        cmd += ["--screenshot", out]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=90,
                       encoding="utf-8", errors="ignore")
    if p.returncode != 0:
        return "FETCH-FAIL: %s / %s" % (p.stderr[-300:], (p.stdout or "")[-300:])
    return (p.stdout or "").strip()[:4000]


def screenshot(url: str, out: str, stealth: bool = True) -> str:
    if not _port_up(OBSCURA_PORT):
        ok, st = serve(stealth=stealth)
        if not ok:
            return "SERVE-FAIL: %s" % st
    cmd = [obscura_bin(), "fetch", url, "--dump", "html",
           "--screenshot", out, "--timeout", "30",
           "--stealth"] if stealth else \
          [obscura_bin(), "fetch", url, "--dump", "html",
           "--screenshot", out, "--timeout", "30"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=90,
                       encoding="utf-8", errors="ignore")
    if p.returncode != 0:
        return "SCREENSHOT-FAIL: %s / %s" % (p.stderr[-200:], p.stdout[-100:])
    return "screenshot: %s" % out


def mcp_start(port: int = MCP_PORT):
    if getattr(serve, "_proc", None) is None:
        ok, st = serve()
        if not ok:
            return False, st
    return True, "obscura mcp --http --port %d chal raha" % port


def mcp_stop():
    return "mcp-stop (manual kill recommended)"


def install_skill(repo: str = _SKILL_GIT, dest: str = None) -> str:
    """Obscura ka skill Hemomemo local me install (koi AI-API nahi)."""
    if dest is None:
        dest = os.path.join(os.path.expanduser("~"), ".hemomemo", "skills",
                             SKILL_NAME)
    os.makedirs(dest, exist_ok=True)
    for f in ("skills/obscura/SKILL.md", "skills/obscura/skill.md",
              "skills/SKILL.md", "SKILL.md", "skills/obscura/SKILL.md"):
        url = ("https://raw.githubusercontent.com/%s/main/%s" % (repo, f))
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=30) as r:
                data = r.read().decode("utf-8", "ignore")
            name = os.path.basename(f)
            open(os.path.join(dest, name), "w", encoding="utf-8").write(data)
            return "SKILL-INSTALLED: %s (%s, %d bytes)" % (repo, name, len(data))
        except Exception as e:
            return "SKILL-INSTALL-FAIL: %s" % e
    return "SKILL-FAIL: no-skill-file"


def status() -> str:
    try:
        ok, st = serve()
        return "serve=%s | %s" % ("ON" if ok else "OFF", st)
    except Exception as e:
        return "status-FAIL: %s" % e


def main_cli(argv) -> int:
    args = list(argv)
    if not args:
        print("usage: py -3 -m agent.browser_cloud start|stop|fetch|"
              "screenshot|mcp|skill <args>")
        return 0
    cmd = args[0]
    if cmd == "start":
        ok, st = serve()
        print("CLOUD-COMPUTER-BROWSER: serve=%s | %s" % (ok, st))
        return 0 if ok else 1
    if cmd == "stop":
        print(stop())
        return 0
    if cmd == "fetch":
        if len(args) < 2:
            return 0
        print(fetch(args[1],
                    dump=args[2] if len(args) > 2 and args[2] in
                         ("text", "html", "links", "markdown", "assets", "original")
                         else "text"))
        return 0
    if cmd == "screenshot":
        if len(args) < 3:
            return 0
        print(screenshot(args[1], args[2]))
        return 0
    if cmd == "mcp":
        if len(args) > 1 and args[1] == "start":
            ok, st = mcp_start()
            print("MCP=%s | %s" % (ok, st))
            return 0 if ok else 1
        return 0
    if cmd == "skill":
        if len(args) > 1 and args[1] == "install":
            print(install_skill())
            return 0
        print(install_skill())
        return 0
    print("unknown-cmd")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli(sys.argv[1:]))
