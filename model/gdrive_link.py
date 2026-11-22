"""gdrive_link.py - Hemomemo GOOGLE-WORKSPACE (Drive+Docs - no AI-API)
==================================================================
User-qanoon: Google-Workspace (Gmail/Docs/Drive) ALLOWED - ye storage/
docs APIs hain, AI-platform NAHI. Koi AI-api-key kabhi nahi lagti.

AUTH: OAuth2 refresh-token (data/google_oauth.json - OWNER-file, zip me
KABHI nahi). net_guard me oauth2/drive/docs.googleapis.com allowed hain
(BANNED_AI_RX phir-bhi Gemini/generativelanguage HARD-BLOCK karta hai).

Setup (ek-dafa):
  1) console.cloud.google.com -> project -> APIs ON: Drive API, Docs API
  2) OAuth client (Desktop app) -> client_id + client_secret
  3) Hemomemo me: "drive setup" -> browser-consent -> refresh-token
     khud data/google_oauth.json me save ho jata (localhost:8899 loopback)

Commands (powers.py):
  drive list [n]         - files dikhao
  drive upload <path>    - file chadhaao
  drive download <name>  - file neeche laao (data/drive_downloads)
  doc read <id|naam>     - Google-Doc ka text parho
  drive setup            - OAuth-flow (browser) - ek-dafa
"""
import json
import os
import re
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

try:
    from harvest import net_guard
    net_guard.install()
except Exception:
    net_guard = None

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(_ROOT, "data", "google_oauth.json")
_DL_DIR = os.path.join(_ROOT, "data", "drive_downloads")
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPE = ("https://www.googleapis.com/auth/drive.file "
          "https://www.googleapis.com/auth/documents.readonly")
_LOOP_PORT = 8899
_mem = {"token": "", "exp": 0}


def _cfg():
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            c = json.load(f)
        if isinstance(c, dict) and c.get("client_id") \
                and (c.get("refresh_token") or c.get("client_secret")):
            return c
    except Exception:
        pass
    return None


def _http(url, data=None, headers=None, method=None, timeout=25.0,
          raw=False):
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
    return b if raw else json.loads(b.decode("utf-8", "replace"))


def _access():
    """Refresh-token -> access-token (cache jab tak valid)."""
    c = _cfg()
    if not c or not c.get("refresh_token"):
        return None
    if _mem["token"] and time.time() < _mem["exp"] - 60:
        return _mem["token"]
    body = urllib.parse.urlencode({
        "client_id": c["client_id"], "client_secret": c["client_secret"],
        "refresh_token": c["refresh_token"], "grant_type": "refresh_token"
    }).encode()
    try:
        j = _http(_TOKEN_URL, data=body, method="POST",
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
        _mem["token"] = j.get("access_token", "")
        _mem["exp"] = time.time() + j.get("expires_in", 3600)
        return _mem["token"]
    except Exception as e:
        raise RuntimeError("token-refresh fail: %s" % str(e)[:160])


_SET_HELP = ("[drive] OAuth setup chahiye (ek-dafa, ~3 min):\n"
             "1) console.cloud.google.com -> project -> APIs ON: "
             "Drive API + Docs API\n"
             "2) 'OAuth client ID' (Desktop app) -> client_id/secret copy\n"
             "3) yahan likho: drive setup\n"
             "   -> browser consent kholta hai -> consent do -> token "
             "khud save (data/google_oauth.json)\n"
             "Phir 'drive list' / 'drive upload <path>' / 'doc read <naam>' "
             "chal padega.")


def authorize_flow():
    """Browser-consent + localhost:8899 loopback -> tokens save."""
    c = _cfg() or {}
    cid, csec = c.get("client_id", ""), c.get("client_secret", "")
    if not cid or not csec:
        return _SET_HELP, {"source": "drive", "state": "need-client"}
    url = ("https://accounts.google.com/o/oauth2/v2/auth?%s"
           % urllib.parse.urlencode({
               "client_id": cid, "redirect_uri":
                   "http://localhost:%d/" % _LOOP_PORT,
               "response_type": "code", "scope": _SCOPE,
               "access_type": "offline", "prompt": "consent"}))
    got = {}

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(
                urllib.parse.urlparse(self.path).query)
            got["code"] = (q.get("code") or [""])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Hemomemo AI: token mil gaya - window band karo.")
        def log_message(self, *a):
            pass

    srv = HTTPServer(("localhost", _LOOP_PORT), H)
    webbrowser.open(url)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    t0 = time.time()
    while not got.get("code") and time.time() - t0 < 120:
        time.sleep(0.4)
    srv.shutdown()
    if not got.get("code"):
        return ("[drive] Consent na mila (120s timeout) - 'drive setup' "
                "dobara chalao.", {"source": "drive", "state": "timeout"})
    body = urllib.parse.urlencode({
        "code": got["code"], "client_id": cid, "client_secret": csec,
        "redirect_uri": "http://localhost:%d/" % _LOOP_PORT,
        "grant_type": "authorization_code"}).encode()
    j = _http(_TOKEN_URL, data=body, method="POST",
              headers={"Content-Type": "application/x-www-form-urlencoded"})
    c["refresh_token"] = j.get("refresh_token", c.get("refresh_token", ""))
    c["access_token"] = j.get("access_token", "")
    os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)
    _mem["token"], _mem["exp"] = "", 0
    return ("[drive] OAuth mukammal - refresh-token save ho gaya. "
            "Ab 'drive list' chalao.", {"source": "drive", "state": "linked"})


def drive_list(n=10):
    tok = _access()
    j = _http("https://drive.googleapis.com/drive/v3/files?pageSize=%d"
              "&fields=files(id,name,mimeType,size)&orderBy=modifiedTime desc"
              % max(1, min(50, n)),
              headers={"Authorization": "Bearer %s" % tok})
    files = j.get("files") or []
    if not files:
        return "[drive] Drive me koi file nahi mili.", \
            {"source": "drive", "state": "empty"}
    txt = "[drive] Haaliya %d files:\n" % len(files) + "\n".join(
        "  - %s%s\n      %s" % (f.get("name", "")[:60],
                                " (folder)" if "folder" in
                                (f.get("mimeType") or "") else "",
                                f.get("id", ""))
        for f in files)
    return txt, {"source": "drive", "state": "ok", "n": len(files)}


def drive_upload(path):
    tok = _access()
    path = os.path.abspath(os.path.expanduser((path or "").strip().strip('"')))
    if not os.path.isfile(path):
        return "[drive] File nahi mili: %s" % path, \
            {"source": "drive", "state": "missing"}
    boundary = "hemomemo%d" % (time.time() * 1000)
    meta = json.dumps({"name": os.path.basename(path)}).encode()
    with open(path, "rb") as f:
        blob = f.read()
    body = (("--%s\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n"
             % boundary).encode() + meta +
            ("\r\n--%s\r\nContent-Type: application/octet-stream\r\n\r\n"
             % boundary).encode() + blob +
            ("\r\n--%s--" % boundary).encode())
    j = _http("https://drive.googleapis.com/upload/drive/v3/files"
              "?uploadType=multipart",
              data=body, method="POST",
              headers={"Authorization": "Bearer %s" % tok,
                       "Content-Type":
                           "multipart/related; boundary=%s" % boundary})
    return ("[drive] Upload ho gayi: %s (id: %s)"
            % (j.get("name"), j.get("id")),
            {"source": "drive", "state": "uploaded", "id": j.get("id")})


def drive_download(name):
    tok = _access()
    q = urllib.parse.urlencode({"q": "name = '%s'" % name.replace("'", "\\'"),
                                "pageSize": 5,
                                "fields": "files(id,name,mimeType)"})
    j = _http("https://drive.googleapis.com/drive/v3/files?%s" % q,
              headers={"Authorization": "Bearer %s" % tok})
    files = [f for f in (j.get("files") or [])
             if "folder" not in (f.get("mimeType") or "")]
    if not files:
        return "[drive] '%s' na mile (sahi naam do - dekho: drive list)" % name, \
            {"source": "drive", "state": "missing"}
    f = files[0]
    blob = _http("https://drive.googleapis.com/drive/v3/files/%s?alt=media"
                 % f["id"], headers={"Authorization": "Bearer %s" % tok},
                 raw=True)
    os.makedirs(_DL_DIR, exist_ok=True)
    dst = os.path.join(_DL_DIR, f.get("name") or "file.bin")
    with open(dst, "wb") as fh:
        fh.write(blob)
    return ("[drive] Download: %s (%.1f KB) -> %s"
            % (f.get("name"), len(blob) / 1024.0, dst),
            {"source": "drive", "state": "downloaded", "file": dst})


def doc_read(ref):
    tok = _access()
    doc_id = (ref or "").strip()
    if not re.match(r"^[\w-]{20,}$", doc_id):
        q = urllib.parse.urlencode(
            {"q": "name contains '%s' and mimeType = "
                  "'application/vnd.google-apps.document'"
                  % (ref or "").replace("'", "\\'"), "pageSize": 3})
        j = _http("https://drive.googleapis.com/drive/v3/files?%s" % q,
                  headers={"Authorization": "Bearer %s" % tok})
        files = j.get("files") or []
        if not files:
            return ("[drive] Doc '%s' na mila (id ya sahi naam do; "
                    "dekho: drive list)" % ref[:40],
                    {"source": "docs", "state": "missing"})
        doc_id = files[0]["id"]
    j = _http("https://docs.googleapis.com/v1/documents/%s" % doc_id,
              headers={"Authorization": "Bearer %s" % tok})
    parts = []
    for el in ((j.get("body") or {}).get("content") or []):
        p = (el.get("paragraph") or {}).get("elements") or []
        parts.append("".join((e.get("textRun") or {}).get("content", "")
                             for e in p))
    text = "\n".join(x.rstrip() for x in parts if x.strip())
    if not text.strip():
        return "[docs] Doc khali hai: %s" % (j.get("title") or doc_id[:30]), \
            {"source": "docs", "state": "empty"}
    return "[docs] '%s' (%d harf):\n%s" % (j.get("title", doc_id[:30]),
                                           len(text), text[:3000]), \
        {"source": "docs", "state": "ok", "doc": j.get("title")}


def run_command(rest):
    rest = (rest or "").strip()
    low = rest.lower()
    if low.startswith("setup") or low in ("auth", "link"):
        return authorize_flow()
    if not _cfg() or not (_cfg().get("refresh_token")):
        return _SET_HELP, {"source": "drive", "state": "no-config"}
    try:
        if low.startswith("list"):
            m = re.match(r"(?i)list\s*(\d*)", rest)
            return drive_list(int(m.group(1) or 10))
        if low.startswith("upload"):
            return drive_upload(rest[6:].strip())
        if low.startswith("download"):
            return drive_download(rest[8:].strip())
        if low.startswith("doc"):
            return doc_read(rest[3:].strip())
    except RuntimeError as e:
        if "invalid_grant" in str(e) or "401" in str(e):
            return ("[drive] Token expire/revoke ho gaya - 'drive setup' "
                    "dobara chalao.", {"source": "drive", "state": "re-auth"})
        return "[drive] Masla: %s" % str(e)[:200], {"source": "drive",
                                                    "state": "error"}
    except Exception as e:
        return "[drive] Masla: %s" % str(e)[:200], {"source": "drive",
                                                    "state": "error"}
    return ("[drive] Hukum: drive list | drive upload <path> | "
            "drive download <naam> | doc read <id|naam> | drive setup",
            {"source": "drive", "state": "help"})


if __name__ == "__main__":
    print(run_command("list")[0][:200])
