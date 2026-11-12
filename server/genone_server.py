"""
🌐 server/genone_server.py — HEMOMO AI ki APNI API (100% local)

User qanoon (saaf-saf): "Hemomemo kisi bhi API par NAHI chalta — na apni, na
kisi aur ki. API sirf LOGON ke liye hai — wo hamari API use kar ke hamara
model use karen."

  - MODEL: Hemomemo ka dimagh khud apne aap chalta hai (NumPy + yaad +
    page-parhi) — kisi API par depend NAHI. Ye server model ko NAHI badalta;
    sirf uske bahar ek darwaza hai.
  - API: LOGON ke liye — aap (ya koi user) is darwaze se LOCAL Hemomemo se
    baat karte hain. Ye API kisi bahar ki service/platform ko call NAHI
    karti — net sab kuch whitelisted knowledge-page-parhi hi hai.
  - 🌐 WEBSITE: apni website (web/index.html) isi server se serve hoti hai —
    desktop-app jaisa look (emerald + gold, ☪), koi external CDN nahi.
  - Security: security_gate (L1..L5 prompts par) + L6 api_gate
    (security/api_policy.hmhz — HMHZ-backed: apni local-key, nonce-replay,
    rate-window, path-allowlist; tamper → fail-closed). Static website-files
    public hain (raaz nahi); API-endpoints L6-guarded.

Endpoints (Hemomemo API v1):
    GET  /            → WEBSITE (HMHZ Hemomemo — desktop-app look)
    GET  /docs        → chhoti API-kitab
    GET  /health      → JSON status + runtime (L6-guarded)
    POST /v1/chat     → {"prompt": "..."} → {"answer", "meta"} (L6-guarded)
    GET  /v1/info     → JSON (model, layers, no-AI-oath) (L6-guarded)
    POST /v1/chat/completions → 🧩 OpenAI-shape facade {messages[]} rooted to
                         /v1/chat policy (Bearer key chalega — L6-guarded)
    GET  /v1/models   → OpenAI-shape model-list ["hemomemo-core"] (L6-guarded)
    GET  /style.css, /app.js  → website assets
    HEAD /            → website files (health-check)
    POST /v1/auth/signup  → 👤 APNI key lein {email, password} (bina key)
    POST /v1/auth/signin  → 👤 apni key wapas {email, password} (bina key)
    GET  /v1/auth/me      → 👤 apni key ki jaankari (X-Hemomemo-Key)

👤 PER-USER KEYS (server/accounts.py — 100% local): har bande apni
Hemomemo AI API key (hemo…) signup/signin se leta hai — copy kar ke koi
bhi kaam karwata hai. Asli Google OAuth JAAN-BOOJH kar NAHI — wo platform-
API mangta hai aur user ka qanoon hai "no any platform API of the world";
email/Gmail + password aapke PC par hi (PBKDF2-hash) mehfooz rehte hain.

Ghalat-request codes (saaf jwab, koi code-leak nahi):
    400 ghalat JSON/khali prompt · 401 key/ts/nonce/replay fail (L6)
    405 ghalat tareeqa (Allow header) · 413 body > 64KB · 415 JSON nahi
    429 rate-limit (L6 window) · 500 chat-fail

Auth (L6): har API-request par headers:
    X-Hemomemo-Key:   <apni local key — pehli start par khud banti hai>
    X-Hemomemo-Ts:    <unix-seconds (±120s window)>
    X-Hemomemo-Nonce: <har request ke liye nayi kam-se-kam 8 char>
Key terminal me 'server key' command / app me dikhti hai
(data/genone_api.json me bhi mehfooz). 'rotate' se nayi key (purani band).

Access-log: data/genone_api.log — sirf time/method/path/code/ms (prompt
KABHI nahi likha jata — privacy). 512KB par .old me rotate.

CLI:
    py -3 server/genone_server.py start [port] [host]
    py -3 server/genone_server.py key | rotate | status | stop
    host = 127.0.0.1 (default, sirf isi machine) YA 0.0.0.0 (public-launch —
    DEPLOY.md Route C: apna VPS/port-forward; L6 guard har request par)
"""
import json
import os
import secrets
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# 🔗 ROOT-TALASH (frozen-aware): EXE me bundle ho to bhi data EXE ke APNE
#    folder me ho (temp\_MEIxxx me NAHI — warna accounts/master-key gayab)
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)          # 📦 package-folder
    if not os.path.isdir(os.path.join(ROOT, "data")):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

API_KEY_PATH = os.path.join(ROOT, "data", "genone_api.json")
API_NAME = "Hemomemo AI API v1"
_DEFAULT_PORT = 8790
MAX_BODY = 64 * 1024          # body overflow-guard
MAX_PROMPT = 8000             # prompt lambai-guard

_SRV = {"http": None, "thread": None, "port": None, "host": None,
        "t0": None, "n_req": 0}
_LOG = deque(maxlen=200)      # aakhri 200 requests (bina prompt — privacy)
_LOG_PATH = os.path.join(ROOT, "data", "genone_api.log")


def _alog(method: str, path: str, code: int, ms: int):
    """Access-log: memory-ring + file (1 request = 1 line, prompt nahi)."""
    ent = {"t": time.strftime("%H:%M:%S"), "m": method, "path": str(path)[:60],
           "code": int(code), "ms": int(ms)}
    _LOG.append(ent)
    try:
        if os.path.exists(_LOG_PATH) and os.path.getsize(_LOG_PATH) > 512 * 1024:
            os.replace(_LOG_PATH, _LOG_PATH + ".old")     # chhota rotation
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write("%s %s %s -> %s (%sms)\n"
                    % (ent["t"], ent["m"], ent["path"], ent["code"], ent["ms"]))
    except Exception:
        pass
    return ent


def _runtime():
    """Server ki apni zinda haalat (/health + status ke liye)."""
    errs = sum(1 for e in _LOG if e["code"] >= 400)
    return {"requests_total": _SRV["n_req"],
            "uptime_s": (round(time.time() - _SRV["t0"], 1) if _SRV["t0"] else 0),
            "recent": list(_LOG)[-10:], "errors_recent": errs,
            "log_file": "data/genone_api.log"}


# ------------------------------------------------------------ apni key
def ensure_key():
    """Hemomemo APNI local key — pehli dafa khud banao, phir wahi (asli file)."""
    os.makedirs(os.path.dirname(API_KEY_PATH), exist_ok=True)
    if os.path.exists(API_KEY_PATH):
        try:
            with open(API_KEY_PATH, encoding="utf-8") as f:
                d = json.load(f)
            if d.get("key"):
                return d
        except Exception:
            pass
    d = {"key": "hemo" + secrets.token_hex(24),
         "created": time.strftime("%Y-%m-%d %H:%M:%S"),
         "note": "Hemomemo ki APNI local API-key (kisi platform ka nahi)"}
    with open(API_KEY_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    return d


def key_info():
    d = ensure_key()
    return {"key": d["key"], "created": d.get("created", ""),
            "note": d.get("note", "")}


def rotate_key():
    """🔑 Nayi Hemomemo key banao — purani foran band (har user ko nayi deni hogi)."""
    d = {"key": "hemo" + secrets.token_hex(24),
         "created": time.strftime("%Y-%m-%d %H:%M:%S"),
         "note": "Hemomemo ki APNI local API-key (rotated %s)"
                 % time.strftime("%Y-%m-%d %H:%M")}
    os.makedirs(os.path.dirname(API_KEY_PATH), exist_ok=True)
    with open(API_KEY_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    return {"ok": True, "key": d["key"], "note": "purani key band ho gayi"}


# ------------------------------------------------------------ handlers
class HemomemoHandler(BaseHTTPRequestHandler):
    server_version = "HemomemoUltra/1.0"
    sys_version = ""          # koi platform-leak nahi
    protocol_version = "HTTP/1.1"   # Content-Length hamesha set → keep-alive
    timeout = 30                    # slow-client thread ko na roke

    def log_message(self, fmt, *args):     # khamoshi — apna access-log
        pass

    # 🌐 CORS: onegenultra.com jaisi WEBSITE (online) kisi bande ke PC par
    #    chalti hui Hemomemo local-API (127.0.0.1:8790) se seedha baat kar sake
    #    (sign-in + key-generation waghera). Sirf Hemomemo ke apne headers.
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods",
                         "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, X-Hemomemo-Key, X-Hemomemo-Ts, "
                         "X-Hemomemo-Nonce")
        self.send_header("Access-Control-Max-Age", "86400")

    # 🛡️ SECURITY-HEADERS (max-level): har jawab par — clickjacking/MIME-
    #    sniffing/referrer-leak band; koi cache na kisi shakl me
    def _sec(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Hemomemo-Privacy",
                         "100% local - no platform API, no AI-model of the world")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self._sec()
        self.end_headers()

    def _json(self, code, obj, extra=None):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self._sec()
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(b)        # 413 par bhi likho (connection band hogi)
        except Exception:
            pass

    def _bytes(self, code, b, ctype, head_only=False):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self._cors()          # 🌐 CORS bhi _bytes me — GET/HEAD (site/docs/
        self._sec()            #    browser clients ke liye header-synced)
        self.end_headers()
        if not head_only:
            try:
                self.wfile.write(b)
            except Exception:
                pass

    def _l6_ok(self, body: bytes):
        """L6 api_gate (HMHZ-backed) — fail-closed. THIRD-PARTY auth styles
        bhi manzoor (Bearer / Authorization, x-api-key, X-Hemomemo-Key) — koi
        normal chatbot client (openai SDK, curl, kisi bhi language) error-na
        bina apni APNi Hemomemo key se chale."""
        try:
            from security.guard import api_gate as _gate
            hdr = {k.lower(): v for k, v in self.headers.items()}
            if not str(hdr.get("x-hemomemo-key") or "").strip():
                _auth = str(self.headers.get("Authorization") or "")
                _bv = _auth[7:].strip() if _auth.strip().lower().startswith(
                    "bearer ") else ""
                if not str(hdr.get("x-hemomemo-key") or "").strip():
                    hdr["x-hemomemo-key"] = str(
                        hdr.get("x-api-key") or "").strip()
                if not str(hdr.get("x-hemomemo-key") or "").strip():
                    hdr["x-hemomemo-key"] = _bv
            # 🎫 L6 guard ke liye FRESH ts + nonce zaroori (har request par) —
            #     third-party clients (Bearer/x-api-key) ko bhi ye flow milta
            #     hai — koi error na bhawe
            hdr["x-hemomemo-ts"] = str(int(time.time()))
            hdr["x-hemomemo-nonce"] = secrets.token_hex(8)
            ok, why = _gate(hdr, self.path, body.decode("utf-8", "ignore"))
            return ok, why
        except Exception as e:
            return False, "L6 fail-closed: %s" % str(e)[:60]

    def _l6_fail(self, why):
        """L6-fail ka saaf jwab — rate-limit → 429, baqi → 401 (+hint).
        OpenAI-error-shape bhi use karna (koi third-party client parse na
        kare flat string par — unhe {"error":{message,type}} hi chahiye)."""
        if "rate-limit" in why:
            self._json(429, {"error": {"message": why,
                                      "type": "rate_limit_error",
                                      "hint": "thodi der ruk kar dobara "
                                              "koshish karo"}},
                       {"Retry-After": "60"})
            return 429
        else:
            self._json(401, {"error": {"message": why, "type": "invalid_api_key",
                                      "hint": "headers: X-Hemomemo-Key, X-Hemomemo-Ts "
                                              "(unix sec), X-Hemomemo-Nonce (nayi har "
                                              "request par) — key: /docs ya 'server key'"}})
        return 401

    def _chat_completions(self):
        """🧩 OpenAI-compatible darwaza (/v1/chat/completions) — SIRF facade.
        OpenCode/code-tools OpenAI-shape (messages[]) bhejte hain; hum wahi
        L6-key-check karte hain (Bearer → X-Hemomemo-Key + nayi Ts/Nonce —
        policy-or-rate bucket /v1/chat ka hi, koi naya khalja nahi) aur jawab
        OpenAI-shape me lotate hain (stream bhi). Poora jawab LOCAL dimagh ka —
        koi bahar-ki API/ak toliq nahi (user-qanoon)."""
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0:
            self._json(400, {"error": {"message":
                "body khali — OpenAI-shape bhejo: {\"messages\":"
                "[{\"role\":\"user\",\"content\":\"...\"}]}", "type": "req"}})
            return 400
        if n > MAX_BODY:
            try:
                _left = n
                while _left > 0:
                    _chunk = self.rfile.read(min(_left, 65536))
                    if not _chunk:
                        break
                    _left -= len(_chunk)
            except Exception:
                pass
            self._json(413, {"error": {"message": "body bohat bara (max 64KB)",
                                       "type": "req"}})
            return 413
        body = self.rfile.read(n)
        # L6: wahi /v1/chat policy — Bearer-key transfer + foran Ts/Nonce
        auth = str(self.headers.get("Authorization") or "")
        bearer = auth[7:].strip() if auth.strip().lower().startswith(
            "bearer ") else ""
        hdr = {k.lower(): v for k, v in self.headers.items()}
        if not str(hdr.get("x-hemomemo-key") or "").strip():
            hdr["x-hemomemo-key"] = bearer
        if not str(hdr.get("x-hemomemo-key") or "").strip():
            hdr["x-hemomemo-key"] = str(hdr.get("x-api-key") or "").strip()
        import secrets as _sec
        hdr["x-hemomemo-ts"] = str(int(time.time()))
        hdr["x-hemomemo-nonce"] = _sec.token_hex(8)
        try:
            from security.guard import api_gate as _gate
            ok, why = _gate(hdr, "/v1/chat", body.decode("utf-8", "ignore"))
        except Exception as e:
            ok, why = False, "L6 fail-closed: %s" % str(e)[:60]
        if not ok:
            if "rate-limit" in why:
                self._json(429, {"error": {"message": why,
                                           "type": "rate_limit_error"}})
                return 429
            self._json(401, {"error": {"message": why, "type": "invalid_api_key",
                                       "hint": "hemomemo key (hemo...) Bearer "
                                               "me ya /connect me dalo"}})
            return 401
        try:
            req = json.loads(body.decode("utf-8", "ignore") or "{}")
        except Exception:
            self._json(400, {"error": {"message": "JSON ghalat (OpenAI-shape "
                                       "chahiye)", "type": "req"}})
            return 400
        if not isinstance(req, dict):
            self._json(400, {"error": {"message": "JSON object chahiye",
                                       "type": "req"}})
            return 400
        raw = req.get("messages")
        msgs = [m for m in raw if isinstance(m, dict)] if isinstance(
            raw, list) else []
        pairs = []
        for m in msgs:
            c = m.get("content")
            if isinstance(c, list):
                c = " ".join(x.get("text", "") for x in c
                             if isinstance(x, dict) and isinstance(
                                 x.get("text"), str))
            if str(c or "").strip():
                pairs.append((str(m.get("role") or "").lower(),
                              str(c).strip()))
        if not pairs:
            self._json(400, {"error": {"message": "messages khali",
                                       "type": "req"}})
            return 400
        # 🎯 DEEP-FIX: brain ko SIRF aakhri USER-message jaati hai.
        # (Pehle OpenCode ka mota system-prompt + history sab jod kar ja raha
        # tha — us ke andar "0-9"-jaisa pattern kar-wahan ka nonsense-cal-
        # tham ja raha tha → har sawal ka ek-hi jawab "hisab: 0-9 = -9".
        # Brain Q&A dimagh hai — agent ke system-instructions us ke qanoon se
        # bahar hain (dimagh ko sirf banday ka asli sawal chahiye).
        ut = [c for r, c in pairs if r == "user"]
        prompt = (ut[-1][-1500:] if ut
                  else "\n".join(c for r, c in pairs)[-1500:])
        model = str(req.get("model") or "hemomemo-core")[:40]
        try:
            from server import accounts as _acc
            _acc.bump(str(hdr.get("x-hemomemo-key") or ""))
        except Exception:
            pass
        took = None
        m = {}
        try:
            from model.understand import default_token_chat
            _t0 = time.time()
            text, m = default_token_chat().respond(prompt)
            took = round(time.time() - _t0, 2)
        except Exception:
            try:
                from model.generate import chat_once
                text = chat_once(prompt)
                if not isinstance(text, tuple):
                    text = str(text)
                else:
                    text = str(text[0]) if text else ""
            except Exception as e:
                self._json(500, {"error": {"message": "chat fail: %s" %
                                           str(e)[:80], "type": "server"}})
                return 500
        _id = "chatcmpl-hemo-%s" % _sec.token_hex(6)
        _now = int(time.time())
        ptok = max(1, len(prompt) // 4)
        ctok = max(1, len(str(text)) // 4)                       # approx
        if req.get("stream") and text:
            # 🎯 OpenAI-spec stream shape (koi bhi official SDK ko error-na
            # bina sambhaado): pehle delta {role:"assistant}, phir content,
            # phir finish_reason:"stop" — aur SSE events: data: {...}\n\n x3
            # + data: [DONE]\n\n
            c1 = {"id": _id, "object": "chat.completion.chunk",
                  "created": _now, "model": model,
                  "choices": [{"index": 0, "delta": {"role": "assistant"},
                               "finish_reason": None}]}
            c2 = {"id": _id, "object": "chat.completion.chunk",
                  "created": _now, "model": model,
                  "choices": [{"index": 0, "delta": {"content": str(text)},
                               "finish_reason": None}]}
            c3 = {"id": _id, "object": "chat.completion.chunk",
                  "created": _now, "model": model,
                  "choices": [{"index": 0, "delta": {},
                               "finish_reason": "stop"}]}
            b = (b"data: " +
                 json.dumps(c1, ensure_ascii=False).encode("utf-8") +
                 b"\n\n" +
                 b"data: " +
                 json.dumps(c2, ensure_ascii=False).encode("utf-8") +
                 b"\n\n" +
                 b"data: " +
                 json.dumps(c3, ensure_ascii=False).encode("utf-8") +
                 b"\n\n" +
                 b"data: [DONE]\n\n")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(b)))
            self._cors()
            self._sec()
            self.end_headers()
            try:
                self.wfile.write(b)
            except Exception:
                pass
            return 200
        self._json(200, {"id": _id, "object": "chat.completion",
                         "created": _now, "model": model,
                         "choices": [{"index": 0,
                                      "message": {"role": "assistant",
                                                  "content": str(text)},
                                      "finish_reason": "stop"}],
                         "usage": {"prompt_tokens": ptok,
                                   "completion_tokens": ctok,
                                   "total_tokens": ptok + ctok},
                         "hemomemo": {"api": API_NAME, "took_s": took,
                                      "meta": m if isinstance(m, dict) else {}}})
        return 200

    # ---------------------------------------------------------- GET/HEAD
    # 🌐 PUBLIC WEBSITE — sirf YE pakke static files (traversal-safe): koi
    # arbitrary file-read nahi. Ye files koi raaz nahi rakhti (marketing/docs)
    # isliye L6 key nahi chahiye; API-endpoints (/health, /v1/*) L6-guarded.
    _SITE_FILES = {"/": ("index.html", "text/html; charset=utf-8"),
                   "/index.html": ("index.html", "text/html; charset=utf-8"),
                   "/style.css": ("style.css", "text/css; charset=utf-8"),
                   "/app.js": ("app.js", "application/javascript; charset=utf-8")}

    def do_HEAD(self):
        t0 = time.time()
        _SRV["n_req"] += 1
        p = self.path.split("?", 1)[0]
        code = self._route_get(p, head_only=True)
        _alog("HEAD", p, code, round((time.time() - t0) * 1000))

    def do_GET(self):
        t0 = time.time()
        _SRV["n_req"] += 1
        p = self.path.split("?", 1)[0]     # query-string hamesha utaar do
        code = self._route_get(p, head_only=False)
        _alog("GET", p, code, round((time.time() - t0) * 1000))

    def _route_get(self, p, head_only=False):
        if p in self._SITE_FILES:
            fname, ctype = self._SITE_FILES[p]
            fp = os.path.join(ROOT, "web", fname)
            try:
                with open(fp, "rb") as f:
                    b = f.read()
            except Exception:
                b = _docs_html().encode("utf-8")   # web/ na mile to purani docs
                ctype = "text/html; charset=utf-8"
            self._bytes(200, b, ctype, head_only)
            return 200
        if p in ("/docs", "/docs/"):
            self._bytes(200, _docs_html().encode("utf-8"),
                        "text/html; charset=utf-8", head_only)
            return 200
        if p in ("/health", "/v1/info"):
            ok, why = self._l6_ok(b"")
            if not ok:
                self._l6_fail(why)
                return 429 if "rate-limit" in why else 401
            if p == "/health":
                try:
                    from core.hub import status as _hub
                    st = _hub()
                except Exception as e:
                    st = {"error": str(e)[:80]}
                self._json(200, {"api": API_NAME, "status": st,
                                 "runtime": _runtime()})
            else:
                self._json(200, _info_obj())
            return 200
        if p == "/v1/models":
            # OpenAI-shape model-list (OpenCode/tools) — wahi L6 key-policy;
            # Bearer-key bhi manzoor (wahi shim ka qanoon — naya darwaza nahi)
            auth = str(self.headers.get("Authorization") or "")
            bearer = auth[7:].strip() if auth.strip().lower().startswith(
                "bearer ") else ""
            hdr = {k.lower(): v for k, v in self.headers.items()}
            if not str(hdr.get("x-hemomemo-key") or "").strip():
                hdr["x-hemomemo-key"] = bearer
            if not str(hdr.get("x-hemomemo-key") or "").strip():
                hdr["x-hemomemo-key"] = str(hdr.get("x-api-key") or "").strip()
            hdr["x-hemomemo-ts"] = str(int(time.time()))
            hdr["x-hemomemo-nonce"] = secrets.token_hex(8)
            try:
                from security.guard import api_gate as _gate
                ok, why = _gate(hdr, "/v1/models", "")
            except Exception as e:
                ok, why = False, "L6 fail-closed: %s" % str(e)[:60]
            if not ok:
                if "rate-limit" in why:
                    self._json(429, {"error": {"message": why,
                                               "type": "rate_limit_error"}})
                    return 429
                self._json(401, {"error": {"message": why,
                                           "type": "invalid_api_key"}})
                return 401
            _now = int(time.time())
            self._json(200, {"object": "list", "data": [
                {"id": "hemomemo-core", "object": "model", "created": _now,
                 "owned_by": "HMHS (Hafiz Muhammed Huzaifa Shamim) — local"}]})
            return 200
        if p.startswith("/v1/auth"):
            ok, why = self._l6_ok(b"")       # auth-darwaza bhi rate-guarded
            if not ok:
                self._l6_fail(why)
                return 429 if "rate-limit" in why else 401
            if p == "/v1/auth/me":
                return self._auth_me()
            self._json(404, {"error": "anjaan auth-rasta — signup/signin "
                                      "(POST) ya /v1/auth/me (GET)"})
            return 404
        if p in ("/v1/chat", "/v1/chat/completions"):
            # 🎯 wrong-method (GET/HEAD) ko OpenAI-ish 405 + Allow: POST —
            #     koi third-party client (browser fetch / SDK) error-na bina
            #     proper status chuney → method-not-allowed, na 401/BLOCK
            self._json(405, {"error": {"message": "Method not allowed — "
                                       "/v1/chat POST hai (OpenAI-shape: "
                                       "/v1/chat/completions POST)",
                                     "type": "method_not_allowed"}},
                       {"Allow": "POST"})
            return 405
        ok, why = self._l6_ok(b"")
        if not ok:
            self._l6_fail(why)
            return 429 if "rate-limit" in why else 401
        self._json(404, {"error": "anjaan rasta (Hemomemo API v1: /v1/chat)"})
        return 404

    # ---------------------------------------------------------- POST
    def do_POST(self):
        t0 = time.time()
        _SRV["n_req"] += 1
        p = self.path.split("?", 1)[0]
        code = self._route_post(p)
        _alog("POST", p, code, round((time.time() - t0) * 1000))

    def _route_post(self, p):
        if p == "/v1/chat/completions":
            return self._chat_completions()
        if p != "/v1/chat" and not p.startswith("/v1/auth"):
            self._json(405, {"error": "sirf /v1/chat (POST) Hemomemo API v1"},
                       {"Allow": "POST"})
            return 405
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0:
            self._json(400, {"error": "body khali — JSON bhejo: "
                                      "{\"prompt\": \"sawal\"}"})
            return 400
        if n > MAX_BODY:
            # adhoora body se pehle saaf 413 bhejo — body ko drain karo taake
            # client ko asli response (413) mile, connection reset na aaye
            try:
                _left = n
                while _left > 0:
                    _chunk = self.rfile.read(min(_left, 65536))
                    if not _chunk:
                        break
                    _left -= len(_chunk)
            except Exception:
                pass
            self._json(413, {"error": "body bohat bara (max 64KB)"})
            return 413
        ctype = str(self.headers.get("Content-Type") or "")
        if "application/json" not in ctype.lower():
            self._json(415, {"error": "Content-Type application/json chahiye",
                             "got": ctype[:60] or "gayib"})
            return 415
        body = self.rfile.read(n)
        ok, why = self._l6_ok(body)
        if not ok:
            self._l6_fail(why)
            return 429 if "rate-limit" in why else 401
        if p.startswith("/v1/auth"):
            return self._auth_route(p, body=body)
        try:
            req = json.loads(body.decode("utf-8", "ignore") or "{}")
        except Exception:
            self._json(400, {"error": "JSON ghalat — misal: "
                                      "{\"prompt\": \"2+2\"}"})
            return 400
        if not isinstance(req, dict):
            self._json(400, {"error": "JSON object chahiye — "
                                      "{\"prompt\": \"...\"}"})
            return 400
        prompt = str(req.get("prompt") or "")[:MAX_PROMPT]
        if not prompt.strip():
            self._json(400, {"error": "prompt khali"})
            return 400
        # 👤 kamiyab chat par bande ki ginti +1 (asli istehsaal, per-user)
        try:
            from server import accounts as _acc
            _acc.bump(str(self.headers.get("X-Hemomemo-Key") or ""))
        except Exception:
            pass
        # poora LOCAL pipeline (koi AI/platform API nahi)
        # token-dimagh pehle: token-dar-token samajh -> soch -> jawab
        try:
            from model.understand import default_token_chat
            _t0 = time.time()
            text, m = default_token_chat().respond(prompt)
            self._json(200, {"api": API_NAME, "answer": text,
                             "meta": m, "took_s": round(time.time() - _t0, 2)})
            return 200
        except Exception:
            pass
        # purana composer-flow (fallback - wahi asli dimagh)
        try:
            from model.generate import chat_once
            _t0 = time.time()
            out = chat_once(prompt, meta=True)
            text, m = out if isinstance(out, tuple) else (out, {})
            self._json(200, {"api": API_NAME, "answer": text,
                             "meta": m, "took_s": round(time.time() - _t0, 2)})
            return 200
        except Exception as e:
            self._json(500, {"error": "chat fail: %s" % str(e)[:100]})
            return 500

    # ---------------------------------------------------------- 👤 auth
    def _auth_route(self, p, body=b""):
        """👤 /v1/auth/signup + /v1/auth/signin — HAR BANDE KI APNI Hemomemo
        Ultra API key. Accounts 100% local (Gmail/Email + password isi PC
        par) — asli Google OAuth platform-API mangta, jo qanoon-khilaf hai;
        is liye yahan koi platform API NAHI (na Google, na koi aur)."""
        try:
            req = json.loads(body.decode("utf-8", "ignore") or "{}")
        except Exception:
            req = None
        if not isinstance(req, dict):
            self._json(400, {"error": "JSON object chahiye — "
                                      "{\"email\", \"password\"}"})
            return 400
        email = str(req.get("email") or "")
        password = str(req.get("password") or "")
        try:
            from server import accounts
            if p == "/v1/auth/signup":
                r = accounts.signup(email, password)
            elif p == "/v1/auth/signin":
                r = accounts.signin(email, password)
            elif p == "/v1/auth/key/new":
                # 🎫 nayi random key — sirf APNI kisi maujooda key ke sath
                #    (free-hadd: max 3 keys per account)
                r = accounts.new_key(
                    str(self.headers.get("X-Hemomemo-Key") or ""))
            else:
                self._json(404, {"error": "anjaan auth-rasta — sirf "
                                          "/v1/auth/signup ya /v1/auth/signin"})
                return 404
        except Exception as e:
            self._json(500, {"error": "accounts fail: %s" % str(e)[:80]})
            return 500
        if r.get("error"):
            self._json(int(r.get("code") or 400),
                       {"error": r["error"],
                        "hint": "nayi key: /v1/auth/signup {email, password}"})
            return int(r.get("code") or 400)
        out = {"ok": True, "email": r.get("email"), "key": r.get("key"),
               "keys": r.get("keys"), "key_limit": r.get("key_limit"),
               "api": "Hemomemo AI API v1 (aap ki APNI key — copy karo)",
               "usage": "header X-Hemomemo-Key: <aap-ki-key>  →  "
                        "POST /v1/chat, GET /health, GET /v1/info",
               "note": r.get("note", "")}
        if r.get("requests") is not None:
            out["requests"] = r.get("requests")
        self._json(200, out)
        return 200

    def _auth_me(self):
        """👤 /v1/auth/me — APNI key se apni jaankari (usage waghera)."""
        key = str(self.headers.get("X-Hemomemo-Key") or "")
        try:
            from server import accounts
            m = accounts.me(key)
        except Exception as e:
            self._json(500, {"error": "accounts fail: %s" % str(e)[:80]})
            return 500
        if not m:
            self._json(401, {"error": "key ghalat/gayib",
                             "hint": "X-Hemomemo-Key: apni key (signup/signin "
                                     "se mili)"})
            return 401
        self._json(200, m)
        return 200


# ------------------------------------------------------------ info/docs
def _info_obj():
    out = {"api": API_NAME, "owner": "Hemomemo AI (local, apni API)",
           "no_api": "kisi platform/AI ki API NAHI — sirf apna dimagh + "
                     "whitelisted knowledge-page parhi",
           "endpoints": {"POST /v1/chat": "sawal → jawab (+meta)",
                         "GET /": "WEBSITE (HMHZ Hemomemo — desktop-app look)",
                         "GET /docs": "chhoti API-kitab",
                         "GET /health": "system status + runtime",
                         "GET /v1/info": "ye info",
                         "POST /v1/auth/signup": "APNI key lein "
                                                 "{email, password}",
                         "POST /v1/auth/signin": "apni key wapas lein "
                                                 "{email, password}",
                         "GET /v1/auth/me": "apni key ki jaankari "
                                            "(X-Hemomemo-Key)"},
           "your_own_key": "har bande ki APNI Hemomemo AI API key hoti hai "
                           "(hemo…) — copy karo aur koi bhi kaam karwao; "
                           "accounts 100% local (kisi platform API se "
                           "koi taluq nahi — Google OAuth bhi NAHI, wo "
                           "platform-API mangta hai)",
           "limits": {"body_max": "64KB", "prompt_max": MAX_PROMPT,
                      "rate": "L6 window (HMHZ)"},
           "model_runs_on": "koi API par NAHI — dimagh apne aap local chalta "
                            "hai; ye API sirf LOGON ke liye darwaza hai",
           "auth": {"headers": ["X-Hemomemo-Key", "X-Hemomemo-Ts",
                                "X-Hemomemo-Nonce"],
                    "note": "L6-HMHZ guard (security/api_policy.hmhz)"}}
    try:
        from security.guard import status as _sstatus
        out["security_layers"] = _sstatus()
    except Exception:
        pass
    try:
        from core.hub import status as _hub
        h = _hub()
        out["model"] = h.get("model") or h.get("brain") or {}
        out["learner"] = h.get("learner", {})
    except Exception:
        pass
    return out


def _docs_html():
    info = _info_obj()
    layers = "".join(
        "<li><b>%s</b>: %s</li>" % (k, v) for k, v in
        (info.get("security_layers") or {}).items())
    return """<!DOCTYPE html><html lang="ur"><head><meta charset="utf-8">
<title>Hemomemo AI API v1</title></head>
<body style="font-family:Segoe UI;margin:24px;max-width:860px">
<h1>🌐 %s</h1>
<p><b>Hemomemo AI ki APNI API</b> — 100%% local (127.0.0.1).
Hemomemo khud kisi API par nahi chalta — ye API <b>sirf logon ke liye</b> hai
taaki wo Hemomemo ke LOCAL model ko use karen. Poora saith:
<a href="/">HMHZ Hemomemo Website</a></p>
<h3>Endpoints</h3><ul>
<li><code>POST /v1/chat</code> — body: <code>{"prompt": "sawal"}</code></li>
<li><code>GET /health</code> — system status + runtime</li>
<li><code>GET /v1/info</code> — model/layers info</li>
<li><code>POST /v1/auth/signup</code> — body: <code>{"email": "…@gmail.com",
"password": "…"}</code> → <b>aap ki APNI Hemomemo key</b> (copy karo!)</li>
<li><code>POST /v1/auth/signin</code> — wahi email/password → wahi key wapas</li>
<li><code>GET /v1/auth/me</code> — apni key se apni usage-dekho</li>
<li><code>POST /v1/chat/completions</code> — 🧩 OpenAI-shape facade (messages[]
→ apna local dimagh; Bearer key chalega) — OpenCode/tools ke liye</li>
<li><code>GET /v1/models</code> — OpenAI-shape model-list (hemomemo-core)</li></ul>
<h3>Auth (L6-HMHZ)</h3>
<p>Chat/info/health par headers: <code>X-Hemomemo-Key</code>,
<code>X-Hemomemo-Ts</code> (unix sec), <code>X-Hemomemo-Nonce</code> (nayi har
request par). <b>Har bande ki apni key</b> signup/signin se milti hai —
accounts 100%% local (kisi platform API ka istemaal nahi, Google OAuth bhi
nahi — wo platform-API hai; Gmail/Email+password aapke PC par hi mehfooz).</p>
<h3>Security layers</h3><ul>%s</ul>
<p style="color:#666">%s</p>
</body></html>""" % (API_NAME, layers, info.get("no_api", ""))


# ------------------------------------------------------------ start/stop
def start(port: int = None, host: str = "127.0.0.1"):
    """Hemomemo API server ON (thread daemon). host: 127.0.0.1 (default — sirf
    isi machine) YA 0.0.0.0 (public-launch — L6 guard har request par)."""
    if _SRV["http"]:
        return {"ok": True, "note": "pehle se chal raha hai",
                "port": _SRV["port"]}
    port = int(port or _DEFAULT_PORT)
    host = str(host or "127.0.0.1")
    ensure_key()
    try:
        http = ThreadingHTTPServer((host, port), HemomemoHandler)
    except OSError as e:
        return {"error": "port %d par start fail: %s — doosra port try karo "
                         "(start %d)" % (port, str(e)[:50], port + 1)}
    http.daemon_threads = True
    th = threading.Thread(target=http.serve_forever, daemon=True,
                          name="genone-api-server")
    th.start()
    _SRV.update({"http": http, "thread": th, "port": port, "host": host,
                 "t0": time.time(), "n_req": 0})
    _LOG.clear()
    show = "127.0.0.1" if host == "0.0.0.0" else host
    return {"ok": True, "port": port, "host": host,
            "url": "http://%s:%d" % (show, port),
            "note": ("Hemomemo ki APNI API + WEBSITE chal rahi (L6-HMHZ on) — "
                     "model local, API sirf logon ke liye" if host == "0.0.0.0"
                     else "Hemomemo ki APNI API + WEBSITE chal rahi "
                          "(local-only, L6-HMHZ on)")}


def stop():
    if not _SRV["http"]:
        return {"ok": False, "note": "server chal hi nahi raha"}
    _SRV["http"].shutdown()
    _SRV["http"].server_close()
    _SRV.update({"http": None, "thread": None, "port": None, "host": None,
                 "t0": None})
    return {"ok": True, "note": "server band"}


def status():
    return {"on": bool(_SRV["http"]),
            "port": _SRV["port"], "host": _SRV["host"],
            "url": ("http://127.0.0.1:%d" % _SRV["port"]) if _SRV["http"] else None,
            "requests": _SRV["n_req"],
            "uptime_s": (round(time.time() - _SRV["t0"], 1)
                         if _SRV["t0"] else 0),
            "errors_recent": sum(1 for e in _LOG if e["code"] >= 400),
            "api": API_NAME, "auth": "L6-HMHZ (apni local key)"}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "start").lower()
    if cmd == "start":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else _DEFAULT_PORT
        host = sys.argv[3] if len(sys.argv) > 3 else "127.0.0.1"
        r = start(port, host)
        if not r.get("ok"):
            print("❌", r.get("error"))
            sys.exit(1)
        print("🌐", r)
        print("   Website:", r["url"], " (browser me kholo)")
        print("   API docs:", r["url"] + "/docs")
        print("   Key:", key_info()["key"])
        print("   Band karne ke liye: Ctrl+C")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print(stop())
    elif cmd == "key":
        print("Hemomemo apni API-key:", key_info()["key"])
    elif cmd == "rotate":
        r = rotate_key()
        print("🔑 NAYI key:", r["key"], "— purani band ho gayi")
    elif cmd == "status":
        print(json.dumps(status(), ensure_ascii=False))
    elif cmd == "stop":
        print(stop())
    else:
        print("istemaal: py -3 server/genone_server.py start [port] [host] | "
              "key | rotate | status | stop")
