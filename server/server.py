"""
🌐 server.py — Hemomemo AI LOCAL BROWSER SERVER

Chalao:   python server\\server.py
Browser:  http://127.0.0.1:7812

Sakht qawaid (bina tabdeeli):
 - SIRF is PC (localhost 127.0.0.1) par sunta hai — page bhi is hi PC se aata hai
 - No API, no Ollama, no external model — jawabi kaam chat_once (same engine)
 - No internet connection ki zaroorat nahi
"""
import json
import os
import sys

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # noqa: E402

from core.hub import heartbeat_check, status, think  # noqa: E402
from core.owner import summary as owner_summary      # noqa: E402

INDEX_PATH = os.path.join(ROOT, "web", "index.html")
PORT = 7812


class Handler(BaseHTTPRequestHandler):
    # ------------------------------------------------------------------
    def _send(self, code: int, ctype: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError):
            pass

    # ------------------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                with open(INDEX_PATH, "rb") as f:
                    self._send(200, "text/html; charset=utf-8", f.read())
            except OSError:
                self._send(404, "text/plain; charset=utf-8", "index nahi mila".encode())
        elif path == "/health":
            hb = heartbeat_check()
            self._send(200, "application/json; charset=utf-8", json.dumps(
                hb, ensure_ascii=False).encode("utf-8"))
        elif path == "/status":
            self._send(200, "application/json; charset=utf-8", json.dumps(
                status(), ensure_ascii=False).encode("utf-8"))
        elif path == "/favicon.ico":
            self._send(204, "image/x-icon", b"")
        else:
            self._send(404, "text/plain; charset=utf-8", b"not found")

    # ------------------------------------------------------------------
    def do_POST(self):
        if self.path.split("?", 1)[0] != "/chat":
            self._send(404, "text/plain; charset=utf-8", b"not found")
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            data = json.loads(raw.decode("utf-8"))
            msg = str(data.get("message") or "").strip()
        except Exception:
            self._send(400, "application/json; charset=utf-8", json.dumps(
                {"error": "badalat JSON nahi (e.g. {\"message\": \"salam\"})"}).encode("utf-8"))
            return
        if not msg:
            self._send(400, "application/json; charset=utf-8", json.dumps(
                {"error": "message khaali hai"}).encode("utf-8"))
            return
        try:
            text, meta = think(msg)
        except Exception as e:   # kisi bhi surat girna mana
            self._send(200, "application/json; charset=utf-8", json.dumps(
                {"reply": ("Maaf karein, dimagh me chhota badha aya, dobara poochein. "
                           f"(detail: {e})"), "meta": None},
                ensure_ascii=False).encode("utf-8"))
            return
        self._send(200, "application/json; charset=utf-8", json.dumps(
            {"reply": text, "meta": meta}, ensure_ascii=False).encode("utf-8"))

    def log_message(self, fmt, *args):   # console saaf rakhne ke liye
        pass


def run_server(host: str = "127.0.0.1", port: int = PORT):
    print("=" * 56)
    print(" 🌐 Hemomemo AI LOCAL SERVER — sirf is PC par (no internet)")
    print(f"    Browser me kholein:  http://127.0.0.1:{port}")
    print(" 🪪  Owner: " + owner_summary())
    print("    Band karne ke liye:  yahin Ctrl+C dabayein")
    print("=" * 56)
    try:
        srv = ThreadingHTTPServer((host, port), Handler)
    except OSError as e:
        print(f" ❌ Port {port} busy lagta hai ({e}). Dusra port try karein:")
        print(f"    python server\\server.py --port 7822")
        return
    srv.daemon_threads = True
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n 👋 Server band ho gaya. Allah hafiz!")
    finally:
        srv.server_close()


if __name__ == "__main__":
    port = PORT
    if "--port" in sys.argv:
        i = sys.argv.index("--port")
        if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
            port = int(sys.argv[i + 1])
    run_server(port=port)
