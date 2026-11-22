"""mcp_link.py - Hemomemo MCP-CLIENT (local stdio only - no AI-API)
=================================================================
Model Context Protocol client: LOCAL MCP-servers se baat (subprocess
+ stdio JSON-RPC). Koi network/AI-platform connection NAHI - servers
aap khud data/mcp_servers.json me likhte ho, har server opt-in.

data/mcp_servers.json (user apne local servers likhe):
  {"servers": [
     {"name": "files", "command": "python", "args": ["-m", "mcp_file_server"],
      "enabled": false}
  ]}

Commands:
  mcp servers           - config me kaun kaun (enabled/disabled)
  mcp tools [server]    - us server ke tools (initialize + tools/list)
  mcp call <server> <tool> {json-args}
  mcp resources [server]

Qanoon: MCP = sirf LOCAL tool-bridge; net_guard ke AI-BLOCK ka ye
module khud bhi itaat karta hai - koi remote/AI-server config ko
HARD-REJECT karta hai (command me ai/openai/anthropic/ollama waghera).
"""
import json
import os
import re
import subprocess
import threading
import time
import queue

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(_ROOT, "data", "mcp_servers.json")
_TIMEOUT = 12.0
_INIT_TIMEOUT = 20.0

_FORBIDDEN_RX = re.compile(
    r"(?i)openai|anthropic|claude|gemini|generativelanguage|ollama|lmstudio"
    r"|openrouter|cohere|mistral|deepseek|huggingface|groq|perplexity"
    r"|api2d|together\.|replicate|elevenlabs|stability|runway")


def _cfg():
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d.get("servers") or []
    except Exception:
        return []


def _find(name):
    for s in _cfg():
        if s.get("name", "").lower() == (name or "").lower():
            return s
    return None


def _reject_server(s):
    """AI-platform/local-daemon config ko HARD-REJECT (qanoon)."""
    blob = json.dumps(s, ensure_ascii=False)
    if _FORBIDDEN_RX.search(blob):
        return ("AI-platform/daemon-server config QANOON ke khilaf hai - "
                "REJECT (sirf aam local-tool servers chal sakte hain)")
    return None


class _Proc:
    """Ek MCP-server-process + line-JSON-RPC pipe."""

    def __init__(self, spec):
        self.p = subprocess.Popen(
            [spec.get("command", "")] + list(spec.get("args", [])),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=_ROOT,
            creationflags=(0x08000000 if os.name == "nt" else 0))
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._reader, daemon=True)
        self.t.start()
        self._id = 0

    def _reader(self):
        for line in self.p.stdout:
            try:
                self.q.put(json.loads(line.decode("utf-8", "replace")))
            except Exception:
                pass

    def _req(self, method, params=None, timeout=_TIMEOUT):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method,
               "params": params or {}}
        self.p.stdin.write((json.dumps(msg) + "\n").encode("utf-8"))
        self.p.stdin.flush()
        end = time.time() + timeout
        while time.time() < end:
            try:
                m = self.q.get(timeout=max(0.1, end - time.time()))
            except queue.Empty:
                break
            if m.get("id") == self._id:
                return m
            # notifications/other-ids chhoro (log-flood nahi)
        return None

    def close(self):
        try:
            self.p.stdin.close()
        except Exception:
            pass
        try:
            self.p.terminate()
        except Exception:
            pass


def _init(proc):
    r = proc._req("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "HemomemoAI", "version": "4.2"}},
        timeout=_INIT_TIMEOUT)
    if not r or "result" not in r:
        return False
    try:
        proc.p.stdin.write((json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}
        ) + "\n").encode("utf-8"))
        proc.p.stdin.flush()
    except Exception:
        pass
    return True


def list_servers():
    out = []
    for s in _cfg():
        rej = _reject_server(s)
        out.append("  - %s [%s]%s  (%s %s)"
                   % (s.get("name"), "ON" if s.get("enabled") else "OFF",
                      ("  <-REJECT: %s" % rej) if rej else "",
                      s.get("command"), " ".join(s.get("args", []))))
    return out


def list_tools(name):
    s = _find(name)
    if not s:
        return "Server '%s' config me nahi (dekho: mcp servers)" % name, {}
    rej = _reject_server(s)
    if rej:
        return "[mcp] %s" % rej, {"source": "mcp", "state": "rejected"}
    if not s.get("enabled"):
        return "[mcp] '%s' OFF hai - config me enabled: true karo" % s.get("name"), \
            {"source": "mcp", "state": "disabled"}
    proc = None
    try:
        proc = _Proc(s)
        if not _init(proc):
            return "[mcp] '%s' initialize nahi hua (server chal nahi/protocol-galta)" \
                % s.get("name"), {"source": "mcp", "state": "init-fail"}
        r = proc._req("tools/list")
        tools = ((r or {}).get("result") or {}).get("tools") or []
        if not tools:
            return "[mcp] '%s' me koi tool nahi mila." % s.get("name"), \
                {"source": "mcp", "state": "empty"}
        txt = "[mcp] %s ke tools (%d):\n" % (s.get("name"), len(tools)) + \
            "\n".join("  - %s: %s" % (t.get("name"),
                                      (t.get("description") or "")[:80])
                      for t in tools)
        return txt, {"source": "mcp", "state": "ok", "n": len(tools)}
    except Exception as e:
        return "[mcp] Masla: %s" % str(e)[:200], {"source": "mcp",
                                                  "state": "error"}
    finally:
        if proc:
            proc.close()


def call_tool(name, tool, args):
    s = _find(name)
    if not s:
        return "Server '%s' config me nahi" % name, {}
    rej = _reject_server(s)
    if rej:
        return "[mcp] %s" % rej, {"source": "mcp", "state": "rejected"}
    if not s.get("enabled"):
        return "[mcp] '%s' OFF hai (config me enabled: true)" % s.get("name"), \
            {"source": "mcp", "state": "disabled"}
    proc = None
    try:
        proc = _Proc(s)
        if not _init(proc):
            return "[mcp] init-fail: %s" % s.get("name"), \
                {"source": "mcp", "state": "init-fail"}
        r = proc._req("tools/call", {"name": tool, "arguments": args or {}})
        res = (r or {}).get("result") or {}
        if "error" in (r or {}):
            return "[mcp] tool-ERROR: %s" % json.dumps(
                r["error"])[:300], {"source": "mcp", "state": "tool-error"}
        content = res.get("content") or []
        parts = [c.get("text", "") for c in content
                 if isinstance(c, dict) and c.get("type") == "text"]
        body = "\n".join(p for p in parts if p) or \
            (json.dumps(res, ensure_ascii=False)[:400])
        return "[mcp] %s.%s ->\n%s" % (s.get("name"), tool, body[:1500]), \
            {"source": "mcp", "state": "ok"}
    except Exception as e:
        return "[mcp] Masla: %s" % str(e)[:200], {"source": "mcp",
                                                  "state": "error"}
    finally:
        if proc:
            proc.close()


def list_resources(name):
    s = _find(name)
    if not s:
        return "Server '%s' config me nahi" % name, {}
    proc = None
    try:
        proc = _Proc(s)
        if not _init(proc):
            return "[mcp] init-fail: %s" % s.get("name"), \
                {"source": "mcp", "state": "init-fail"}
        r = proc._req("resources/list")
        items = ((r or {}).get("result") or {}).get("resources") or []
        if not items:
            return "[mcp] koi resources nahi.", {"source": "mcp",
                                                 "state": "empty"}
        return ("[mcp] %s resources:\n" % s.get("name")) + \
            "\n".join("  - %s (%s)" % (x.get("uri"), x.get("name", ""))
                      for x in items[:20]), \
            {"source": "mcp", "state": "ok", "n": len(items)}
    except Exception as e:
        return "[mcp] Masla: %s" % str(e)[:200], {"source": "mcp",
                                                  "state": "error"}
    finally:
        if proc:
            proc.close()


def run_command(rest):
    rest = (rest or "").strip()
    low = rest.lower()
    if not low or low.startswith(("madad", "help")):
        return ("[mcp] Hukum: mcp servers | mcp tools <server> | "
                "mcp resources <server> | mcp call <server> <tool> "
                "{\"arg\": 1}\n(sirf LOCAL servers - config: "
                "data/mcp_servers.json, opt-in enabled)", 
                {"source": "mcp", "state": "help"})
    if low.startswith("servers"):
        sv = list_servers()
        if not sv:
            return ("[mcp] Abhi koi server config nahi. data/mcp_servers.json "
                    "me apne LOCAL servers likho (sab opt-in; AI-platform "
                    "server config REJECT ho jayegi).",
                    {"source": "mcp", "state": "empty"})
        return "[mcp] Config servers:\n" + "\n".join(sv), \
            {"source": "mcp", "state": "list"}
    m = re.match(r"(?i)^tools\s+([\w-]+)$", rest)
    if m:
        return list_tools(m.group(1))
    m = re.match(r"(?i)^resources\s+([\w-]+)$", rest)
    if m:
        return list_resources(m.group(1))
    m = re.match(r"(?i)^call\s+([\w-]+)\s+([\w.-]+)\s*(.*)$", rest)
    if m:
        raw = m.group(3).strip()
        try:
            args = json.loads(raw) if raw else {}
        except Exception:
            return ("[mcp] Args theek JSON do: mcp call files read "
                    "{\"path\": \"x.txt\"}", {"source": "mcp",
                                              "state": "bad-json"})
        return call_tool(m.group(1), m.group(2), args)
    return "[mcp] Samajh nahi aaya - 'mcp' likho (madad dikhegi).", \
        {"source": "mcp", "state": "help"}


if __name__ == "__main__":
    print(run_command("servers")[0])
