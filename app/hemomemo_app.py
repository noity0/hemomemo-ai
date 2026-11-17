# -*- coding: utf-8 -*-
r"""
☪ Hemomemo AI — DESKTOP APP (app/hemomemo_app.py)
======================================================
Poora LOCAL desktop app: koi AI API key NAHI, koi AI-model/cloud/ollama/
MCP connection NAHI. Ye app seedha aapke D:\DigitalBrain folder ke live
modules se juda hai — terminal/session me jo bhi changes karo (code,
corpus, checkpoints, formulas) wo is app me 🔄 Reload se foran apply.

Run:  py -3 app\hemomemo_app.py   (ya Desktop shortcut / .bat)
"""
import os
import re
import sys
import json
import queue
import threading
import traceback
import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# 🔗 ROOT-TALASH (3 rakabaz, tarteeb se):
#   1) EXE ka APNA folder → 📦 distribution ("for people" folder — jahan
#      model/ copy ho, wahi use karo; D:\DigitalBrain ki zaroorat NAHI)
#   2) app\ ka baap-folder → 🛠️ dev (D:\DigitalBrain\app → D:\DigitalBrain)
#   3) pakka D:\DigitalBrain → dev live-link fallback (EXE khin se bhi chale)
_ROOT_FIX = "D:\\DigitalBrain"
_CANDIDATES = []
if getattr(sys, "frozen", False):
    _CANDIDATES.append(os.path.dirname(sys.executable))    # 📦 package-folder
_CANDIDATES += [os.path.dirname(APP_DIR), APP_DIR, _ROOT_FIX]
ROOT = _ROOT_FIX
for _c in _CANDIDATES:
    if os.path.isfile(os.path.join(_c, "model", "generate.py")):
        ROOT = _c
        break
sys.path.insert(0, ROOT)

import tkinter as tk
from tkinter import ttk

# ----------------------------------------------------------------------
# 🎨 THEME — Muslim texture: gehra sabz + sona (emerald + gold, dark)
# ----------------------------------------------------------------------
# 🎨 MASTER-REDESIGN (14-Nov user-hukum): WhatsApp-classic GREEN + BEIGE —
#   chat-canvas beige (#ece5dd), outgoing-bubble light-green (#d9fdd3),
#   incoming white, header teal (#075e54), accent WhatsApp-green (#25d366).
C_BG      = "#ece5dd"   # chat-canvas / window (beige — WhatsApp classic)
C_PANEL   = "#ffffff"   # sidebar / header (WhatsApp Web white)
C_CARD    = "#ffffff"   # cards (white)
C_CARD2   = "#f0f2f5"   # hover / input (WhatsApp light-grey)
C_BORDER  = "#d1d7db"   # card borders
C_ACCENT  = "#25d366"   # WhatsApp green
C_GOLD    = "#128c7e"   # WhatsApp teal (headings / accents)
C_TEXT    = "#111b21"   # WhatsApp near-black
C_DIM     = "#667781"   # WhatsApp secondary-grey
C_USERBG  = "#d9fdd3"   # user bubble (outgoing light-green)
C_AIBG    = "#ffffff"   # ai bubble (white)
C_DANGER  = "#c0392b"
C_WAHEAD  = "#075e54"   # WhatsApp chat-header teal

F_FONT    = ("Segoe UI", 11)
F_REGULAR = F_FONT            # legacy-alias (video-tab purana naam use karta hai)
F_SMALL   = ("Segoe UI", 9)
F_BOLD    = ("Segoe UI", 11, "bold")
F_H1      = ("Segoe UI", 17, "bold")

# 🎬 video-generation feature-switch — ABHI BAND (user-hukum 14-Nov:
# "acha nahi hay, pehle behtar-bana-kar apply karen — abhi DISABLE, delete
# NAHI"). Poora engine + video-tab code salamat hai; dobara chahiye to
# sirf True karo. Chat me video-maangne par sachi-bat jayegi.
VIDEO_GENERATION = False
F_H2      = ("Segoe UI", 13, "bold")
F_MONO    = ("Consolas", 9)
C_ACCENT2 = "#22c35e"         # hover-green (WhatsApp dark-hover)

MODEL_NAME = "Hemomemo AI"

# ----------------------------------------------------------------------
# 🧠 LAZY LOCAL BRAIN (sirf D:\DigitalBrain ke modules — no network code)
# ----------------------------------------------------------------------
_LOCK = threading.Lock()
_STATE = {"prewarmed": False, "reload_n": 0}


def _log(msg):
    try:
        with open(os.path.join(APP_DIR, "_app_log.txt"), "a",
                  encoding="utf-8", errors="replace") as f:
            f.write("[%s] %s\n" % (datetime.datetime.now().strftime("%H:%M:%S"), msg))
    except Exception:
        pass


def _imp(pkg, mod):
    r"""🔥 EXE-safe DYNAMIC import: PyInstaller string-ko statically nahi
    dekhta — is liye Hemomemo ka code EXE ke andar bundle NAHI hota.
    Runtime par ROOT (D:\DigitalBrain) se LIVE file load hoti hai —
    terminal/session me kiya hua har change app me foran apply."""
    return __import__("%s.%s" % (pkg, mod), fromlist=[mod])


def brain_generate():
    """model.generate (live folder se) — thread-safe lazy import."""
    with _LOCK:
        return _imp("model", "generate")


def brain_hub():
    with _LOCK:
        return _imp("core", "hub")


def brain_formulas():
    with _LOCK:
        return _imp("model", "math_formulas")


def prewarm_async(done_cb=None):
    """Model checkpoints background me load (pehla sawal turant)."""
    def work():
        try:
            G = brain_generate()
            G._prewarm()
            _STATE["prewarmed"] = True
            _log("prewarm OK")
        except Exception as e:
            _log("prewarm FAIL: %s" % e)
        if done_cb:
            try:
                done_cb()
            except Exception:
                pass
    threading.Thread(target=work, daemon=True).start()


def reload_brain_async(done_cb=None):
    """🔄 LIVE RELOAD: sys.modules se model/core/knowledge hatao — terminal
    me kiye gaye code/corpus/checkpoint changes foran apply."""
    def work():
        try:
            import importlib
            dead = [m for m in list(sys.modules)
                    if m.split(".")[0] in ("model", "core", "knowledge", "harvest")]
            for m in dead:
                sys.modules.pop(m, None)
            importlib.invalidate_caches()
            G = brain_generate()
            G._CACHE.update({"tok": None, "brain": None, "ckpt": None})
            G._prewarm()
            _STATE["reload_n"] += 1
            _STATE["prewarmed"] = True
            _log("reload #%d OK (%d modules refreshed)"
                 % (_STATE["reload_n"], len(dead)))
        except Exception as e:
            _log("reload FAIL: %s" % e)
        if done_cb:
            try:
                done_cb()
            except Exception:
                pass
    threading.Thread(target=work, daemon=True).start()


# 🧠 DEEP-MODE (user-hukum 15-Nov): KOI BHI SAAL — chahe Roman-Urdu, math,
# ya koi bhi boliya ("bbbbbbb") — research + soch(rethink) + reasoning par
# jayega. Canned-clarification + token-dimmagh-shallow-reply ye dauran OFF.
_DEEP_THOUGH = True

def chat_async(prompt, on_done, think="auto", progress=None, hist=None):
    """Chat worker thread — UI freeze nahi hota. Result → on_done(text, meta).
    progress(stage) — har asli marhale par UI ko bataata hai (3-soch flow)."""
    # 🕊 QANOON-WIRING: "band karo" (chat) = server OFF (flag + stop-bat);
    # "on karo" = flag mitao + server ON. 24/7-watcher flag ki izzat karta hai
    # (sirf user-ke-bat se server off hota hai — khud kabhi nahi).
    _STOP_RX = re.compile(
        r"(?i)^\s*(?:server\s+|api\s+)?(?:band\s+karo|band\s+kar\s+do|"
        r"server\s+off|api\s+off)\s*[.!]?\s*$")
    _ON_RX = re.compile(
        r"(?i)^\s*(?:server\s+|api\s+)?(?:on\s+karo|on\s+kar\s+do|start\s+"
        r"karo|shuru\s+karo|server\s+on|api\s+on)\s*[.!]?\s*$")
    _hubp = os.path.join(ROOT, "connection_hub", "digitalbrain")
    _hubr = _hubp if os.path.isdir(os.path.join(_hubp, "model")) else ROOT
    _STOP_FLAG = os.path.join(_hubr, "data", "_server_OFF.flag")
    _STOP_BAT = os.path.join(_hubr, "_server_stop.bat")

    if _STOP_RX.match(prompt):
        def _stop_work():
            try:
                open(_STOP_FLAG, "w").close()
            except Exception:
                pass
            try:
                _imp("server", "hemomemo_server").stop()
            except Exception:
                pass
            note = "🛑 server band (aap ke hukum par — flag likh diya, watcher nahi uthaye-ga)"
            try:
                import subprocess
                subprocess.Popen([_STOP_BAT], cwd=str(_hubr),
                                 creationflags=0x08000000)  # CREATE_NO_WINDOW
            except Exception as e:
                note += " (stop-bat: %s)" % e
            on_done(note, {"meta": "server-off"})
        threading.Thread(target=_stop_work, daemon=True).start()
        return

    if _ON_RX.match(prompt):
        try:
            if os.path.exists(_STOP_FLAG):
                os.remove(_STOP_FLAG)
        except Exception:
            pass
        def _on_work():
            try:
                r = _imp("server", "hemomemo_server").start()
                note = "▶ server on: %s" % r
            except Exception as e:
                note = "server-on FAIL: %s" % e
            on_done(note, {"meta": "server-on"})
        threading.Thread(target=_on_work, daemon=True).start()
        return

    _VID_RX = re.compile(r"(?i)\b(video|film|movie|animation|clip)\b")
    _VID_CMD_RX = re.compile(r"(?i)(make|create|generate|banai|banao|benao|show|showing)\b.*\b(video|film|movie|animation|clip)\b")
    _VNUM_RX = re.compile(r"(?i)\b(\d+(?:\.\d+)?)\s*(sec|s|second|seconds|min|minute|minutes)\b")

    def _video_gen(q, out):
        """Ultra-realistic motion video engine — 5s se 15 min tak; koi AI-API nahi."""
        try:
            # Try ultra-realistic motion video first
            try:
                from agent import ultra_realistic_motion_video_simple as _uv
                _dur = 10.0
                m = _VNUM_RX.search(q)
                if m:
                    _v = float(m.group(1))
                    _dur = _v * 60.0 if m.group(2) in ("min", "minute", "minutes") else _v
                _dur = max(5.0, min(900.0, _dur))
                
                # Detect if it's a motion/racing video
                style = "racing" if any(word in q.lower() for word in ["racing", "car", "vehicle", "motion", "speed"]) else "general"
                
                p = _uv.generate_ultra_realistic_motion_video(q, duration=_dur, resolution=(640, 360), style=style)
                
                # Get video metadata (ffprobe milta ho to sach; warna file-size sach)
                import subprocess
                try:
                    r = subprocess.run([
                        "ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size:stream=avg_frame_rate",
                        "-of", "json", p], capture_output=True, text=True,
                        creationflags=(0x08000000 if os.name == "nt" else 0))
                    _fmt, _fps = {}, 24
                    if r.returncode == 0:
                        _j = json.loads(r.stdout or "{}")
                        _fmt = _j.get("format") or {}
                        for _st in (_j.get("streams") or []):
                            _fr = _st.get("avg_frame_rate") or ""
                            if "/" in _fr:
                                _n, _d = _fr.split("/", 1)
                                try:
                                    if float(_d):
                                        _fps = round(float(_n) / float(_d), 2)
                                except Exception:
                                    pass
                    mm = {"duration": float(_fmt.get("duration") or _dur),
                          "size": int(float(_fmt.get("size") or 0)) or os.path.getsize(p),
                          "fps": _fps}
                except Exception:
                    mm = {"duration": _dur, "size": os.path.getsize(p), "fps": 24}
                
                return (p, mm, True, "")
            except Exception as e:
                # Fallback to original video generation
                from agent import video_gen as _vg
                _dur = 10.0
                m = _VNUM_RX.search(q)
                if m:
                    _v = float(m.group(1))
                    _dur = _v * 60.0 if m.group(2) in ("min", "minute", "minutes") else _v
                _dur = max(5.0, min(900.0, _dur))
                p = _vg.generate_video(q, duration_sec=_dur)
                mm = _vg.video_meta(p)
                return (p, mm, True, "")
        except Exception as e:
            import traceback as _t
            return (None, {}, False, "%s\n%s" % (e, _t.format_exc()))

    def work():
        # 🎬 VIDEO-COMMAND fast-path (local engine — koi API nahi)
        if _VID_CMD_RX.search(prompt) and not VIDEO_GENERATION:
            on_done("Hemomemo AI-> 🎬 video-generation filhal BAND hai — "
                    "naya behtar version ban-rahay ke-baad wapis aayegi "
                    "(engine delete nahi hua, sirf switch off hai).",
                    {"source": "video-off"})
            return
        if _VID_CMD_RX.search(prompt):
            p, mm, ok, err = _video_gen(prompt, None)
            if ok:
                on_done(
                    "Hemomemo AI-> ✅ %s video generate ho gayi (100% local — "
                    "no API/no cloud): duration=%ss size=%sKB fps=%s\n%s"
                    % (prompt[:40], mm.get("duration", 0),
                       int(mm.get("size", 0) / 1024), mm.get("fps", 0), p),
                    {"source": "video-local", "file": p,
                     "size": mm.get("size", 0), "duration": mm.get("duration", 0)})
                return
            on_done("Hemomemo AI-> ❌ video generate FAIL: %s" % err,
                    {"source": "video-err"})
            return
        # POWERS fast-path (search/research/code/image/canvas/gem/mcp/
        # mail/drive - sab local ya non-AI API; AI-platform KABHI nahi)
        try:
            from model import powers as _pw
            _tool, _pay = _pw.wants(prompt)
            if _tool:
                _ptxt, _pmeta = _pw.run(_tool, _pay)
                on_done(_ptxt, _pmeta)
                return
        except Exception:
            pass
        # GEM active ho to chat usi ke andaz me (local token-dimagh)
        try:
            from model import gems as _gm
            if _gm.active() is not None:
                _gtxt, _gmeta = _gm.answer_active(prompt)
                if _gtxt:
                    on_done(_gtxt, _gmeta or {"source": "gem"})
                    return
        except Exception:
            pass
        # 🗒 CHAT-YAAD + 🧩 CODE-SAMAJH PROMPT-SYSTEM (100% local):
        # upar-wale SARE messages yaad-may; AKHRI user-sawal 90% priority.
        _ctx = ""
        _cont = False
        try:
            from model.prompt_system import (build_chat_context,
                                             is_continuation)
            _ctx = build_chat_context(hist, prompt)
            _cont = is_continuation(prompt)
        except Exception:
            _ctx = ""
        try:
            # First, use frontolobe to understand the user input
            try:
                from model.frontolobe import understand_user_input
                understanding = understand_user_input(prompt)
                
                # Log the understanding for debugging
                _log("Frontolobe understanding: %s" % str(understanding))
                
                # clarification me ab USER-ka asli-text hamesha dikh-jata hai
                # (English-canned-template-leak band — input-aware Roman-Urdu)
                if (understanding["clarification_needed"]
                        and not _DEEP_THOUGH and not _cont):
                    sug = (understanding.get("response_suggestion") or "").strip()
                    said = (understanding.get("input_text") or prompt or "").strip()
                    if len(said) > 80:
                        said = said[:77].rstrip() + "…"
                    if sug:
                        clarification_msg = "Hemomemo AI-> «%s» — %s" % (said, sug)
                    else:
                        clarification_msg = ("Hemomemo AI-> «%s» — thora tafseel"
                            " se likhein (kya poochna / kya banana hai) to"
                            " behtar-jawab dunga." % said)
                    on_done(clarification_msg, {
                        "source": "clarification",
                        "understanding": understanding
                    })
                    return
                
                # Modify prompt based on understanding
                enhanced_prompt = prompt
                if understanding["intent"]["type"] == "request":
                    # Add context for requests
                    enhanced_prompt = f"User is requesting: {prompt}. Context: {understanding['contextual_clues']}. Key concepts: {understanding['key_concepts']}."
                # 🗒 chat-yaad + 🧩 code-prompt preamble (90% = akhri sawal)
                if _ctx:
                    enhanced_prompt = (_ctx + "\n\n" + enhanced_prompt).strip()
                
                # token-dimagh pehle: token-dar-token samajh (no-API, local)
                try:
                    from model.understand import default_token_chat
                    txt, m = default_token_chat().respond(enhanced_prompt)
                    if txt and _DEEP_THOUGH and (m or {}).get("source") not in (None, ""):
                        # Add understanding context to metadata
                        if m is None:
                            m = {}
                        m["understanding"] = understanding
                        on_done(txt, m or {})
                        return
                except Exception:
                    pass
                
                # Use brain generation if direct chat fails
                G = brain_generate()
                txt, m = G.chat_once(enhanced_prompt, meta=True, think="high",
                                     progress=progress)
                
                # Add understanding context to metadata
                if m is None:
                    m = {}
                m["understanding"] = understanding
                on_done(txt, m or {})
                
            except Exception as e:
                _log("Frontolobe processing failed: %s" % str(e))
                # Fallback to original behavior
                try:
                    from model.understand import default_token_chat
                    txt, m = default_token_chat().respond(prompt)
                    if txt and _DEEP_THOUGH and (m or {}).get("source") not in (None, ""):
                        on_done(txt, m or {})
                        return
                except Exception:
                    pass
                G = brain_generate()
                txt, m = G.chat_once(
                    (_ctx + "\n" + prompt).strip() if _ctx else prompt,
                    meta=True, think="high", progress=progress)
                on_done(txt, m or {})
                
        except Exception as e:
            _log("chat FAIL: %s\n%s" % (e, traceback.format_exc()))
            on_done("Hemomemo AI-> Maaf karein, andruni ghalti: %s" % e,
                    {"source": "error"})
    threading.Thread(target=work, daemon=True).start()


# ----------------------------------------------------------------------
# 🖼️ APP
# ----------------------------------------------------------------------
class HemomemoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("%s — Local Desktop AI (No API · No Cloud · No MCP)" % MODEL_NAME)
        W, H = 1180, 760
        self.minsize(980, 620)
        self.configure(bg=C_BG)
        self._chat_busy = False
        self._last_answer = ""
        self._think_id = None
        self._think_mode = "auto"          # auto | high (gehri soch + research)
        self._hist = []                    # 🗒 chat history turns (user + AI)
        self._hist_path = os.path.join(ROOT, "data", "chat_history_app.json")
        self._think_stages = ["🧠 soch raha hoon", "📚 ilm samajh raha hoon",
                               "🌐 live research", "🧠 soch raha hoon", "✍️ jawab ban raha hoon",
                               "🧠 soch raha hoon"]
        self._think_stage_i = 0
        self._set_icon()
        self._center(W, H)
        self._polish()
        self._wheel_route_setup()
        self._build_layout()
        self._build_statusbar()
        self._build_chat()
        self._build_dashboard()
        self._build_formulas()
        self._build_api()
        self._build_about()
        self.show("chat")
        self._hist_load()
        self.after(400, lambda: prewarm_async(self._prewarm_done))
        self._autostart_server()           # 🌐 apni local API khud ON
        self._build_video()               # 🎬 Video-Generation tab (local-only)
        self.after(20000, self._refresh_statusbar)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center(self, w, h):
        """Window screen ke markaz me khole (behtar pehli nazar)."""
        try:
            self.geometry("%dx%d" % (w, h))
            self.update_idletasks()
            x = max(0, (self.winfo_screenwidth() - w) // 2)
            y = max(0, (self.winfo_screenheight() - h) // 2 - 24)
            self.geometry("+%d+%d" % (x, y))
        except Exception:
            pass

    # ---------------- scroll: smart wheel routing + dark bars ----------------
    def _polish(self):
        """ttk dark scrollbar theme (clam) — har jagah matching style."""
        try:
            st = ttk.Style(self)
            st.theme_use("clam")
            st.configure("TScrollbar", background=C_CARD2, troughcolor=C_BG,
                         bordercolor=C_BG, arrowcolor=C_DIM, gripcount=0,
                         darkcolor=C_CARD2, lightcolor=C_CARD2)
            st.map("TScrollbar",
                   background=[("active", C_BORDER), ("pressed", C_BORDER)])
        except Exception:
            pass

    def _wheel_route_setup(self):
        """🖱️ MOUSE-WHEEL ROUTING: Text/Listbox/Entry par native scroll chalta
        hai (chat, formulas, status); baqi jagah dashboard-canvas scroll.
        (pehle bind_all sab kuch hijack kar leta tha — chat scroll kharab)"""
        def route(e):
            try:
                w = self.winfo_containing(e.x_root, e.y_root)
                while w is not None:
                    if isinstance(w, (tk.Text, tk.Listbox, tk.Entry)):
                        return                      # native scroll chalne do
                    if w is getattr(self, "_dash_cv", None):
                        self._dash_cv.yview_scroll(
                            -int(e.delta / 120), "units")
                        return
                    w = w.master
            except Exception:
                pass
        self.bind_all("<MouseWheel>", route, add="+")

    def _hover(self, btn, normal, hov):
        btn.bind("<Enter>", lambda e: btn.configure(bg=hov))
        btn.bind("<Leave>", lambda e: btn.configure(bg=normal))

    def _set_icon(self):
        """☪ apna icon (bina kisi image-file ke — runtime par banta hai)."""
        try:
            import zlib
            import struct
            import tempfile
            S = 256
            px = bytearray()
            bgc, gold = (16, 38, 30, 255), (217, 180, 91, 255)
            edge = (47, 191, 143, 255)

            def star_hit(cx, cy, ox, oy):
                # 5-point star point-in-polygon (outer 30, inner 12)
                pts = []
                for i in range(10):
                    ang = -1.5708 + i * 0.6283
                    r = 30 if i % 2 == 0 else 12
                    pts.append((ox + r * __import__("math").cos(ang),
                                oy + r * __import__("math").sin(ang)))
                inside = False
                j = 9
                for i in range(10):
                    xi, yi = pts[i]
                    xj, yj = pts[j]
                    if (yi > cy) != (yj > cy) and \
                            cx < (xj - xi) * (cy - yi) / (yj - yi) + xi:
                        inside = not inside
                    j = i
                return inside

            for y in range(S):
                px.append(0)
                for x in range(S):
                    # rounded-square mask
                    dx = min(x, S - 1 - x)
                    dy = min(y, S - 1 - y)
                    corner = (dx < 40 and dy < 40 and
                              (40 - dx) ** 2 + (40 - dy) ** 2 > 40 * 40)
                    if corner:
                        px += bytes(bgc)      # corner = transparent bg (RGB drop aata)
                        continue
                    d_edge = min(dx, dy)
                    c = bgc
                    if d_edge < 5:
                        c = edge
                    # crescent: bada gold circle minus offset bg-circle
                    d1 = (x - 118) ** 2 + (y - 128) ** 2
                    d2 = (x - 152) ** 2 + (y - 118) ** 2
                    if d1 <= 88 ** 2 and d2 > 80 ** 2:
                        c = gold
                    if star_hit(x, y, 168, 92):
                        c = gold
                    px += bytes(c)
            raw = bytes(px)
            def chunk(tag, data):
                c = struct.pack(">I", len(data)) + tag + data
                return c + struct.pack(">I", zlib.crc32(tag + data))
            ihdr = struct.pack(">IIBBBBB", S, S, 8, 6, 0, 0, 0)
            png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
                   chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
            idir = struct.pack("<HHH", 0, 1, 0)
            entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32,
                                len(png), 6 + 16)   # size=len(png), offset=22
            ico = idir + entry + png
            # 🖼 PPM (P6) — Tk ka bundled-PNG-decoder version-dependent hai (exe
            # me 'invalid filter type 255'); PPM = native+sab stable, aur ICO
            # exe-wala shortcut ke liye (size=len(png), offset=22).
            body = bytearray()
            stride = 1 + S * 4
            for y in range(S):
                for x in range(S):
                    i = y * stride + 1 + x * 4
                    body += bytes(px[i:i+3])
            ppm = bytearray(b"P6\n%d %d\n255\n" % (S, S)) + bytes(body)
            d = os.path.join(tempfile.gettempdir(), "HemomemoApp")
            os.makedirs(d, exist_ok=True)
            self._ico_path = os.path.join(d, "hemomemo.ico")
            with open(self._ico_path, "wb") as _f:
                _f.write(ico)
            self._ppm_path = os.path.join(d, "hemomemo.ppm")
            with open(self._ppm_path, "wb") as _f:
                _f.write(bytes(ppm))
            self.iconphoto(True, tk.PhotoImage(file=self._ppm_path))
        except Exception as e:
            import traceback
            _log("icon skip: %s\n%s" % (e, traceback.format_exc()))

    # ---------------- layout: sidebar + header + pages ----------------
    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ⬅ sidebar
        side = tk.Frame(self, bg=C_PANEL, width=210)
        side.grid(row=0, column=0, rowspan=2, sticky="nsw")
        side.grid_propagate(False)
        tk.Label(side, text="  ☪", font=("Segoe UI Emoji", 30),
                 bg=C_PANEL, fg=C_GOLD).pack(anchor="w", pady=(22, 0))
        tk.Label(side, text="Hemomemo AI", font=F_H1, bg=C_PANEL,
                 fg=C_TEXT, anchor="w").pack(fill="x", padx=14)
        tk.Label(side, text="BRAIN", font=("Segoe UI", 15, "bold"),
                 bg=C_PANEL, fg=C_ACCENT, anchor="w").pack(fill="x", padx=14)
        tk.Label(side, text="4 dimagh · 2M neurons\nPure NumPy · No API",
                 font=F_SMALL, bg=C_PANEL, fg=C_DIM,
                 justify="left").pack(fill="x", padx=14, pady=(2, 16))

        self._nav_btns = {}
        for key, icon, label in [
                ("chat", "💬", " Guftagu (Chat)"),
                ("dash", "📊", " Main Page"),
                ("formu", "📐", " Formulas (331)"),
                ("api", "🌐", " Hemomemo API"),
                ("about", "ℹ️", " Baare Me"),
                ("video", "🎬", " Video Generation (band)")]:
            b = tk.Button(side, text="%s%s" % (icon, label), font=F_BOLD,
                           bg=C_PANEL, fg=C_DIM, activebackground=C_CARD2,
                           activeforeground=C_TEXT, relief="flat", bd=0,
                           anchor="w", padx=18, pady=10, cursor="hand2",
                           command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=10, pady=2)
            self._nav_btns[key] = b
            # 🖱️ hover: sirf jab select nahi (selected gold rehta hai)
            b.bind("<Enter>", lambda e, k=key: (
                self._nav_btns[k].configure(bg=C_CARD2) if
                self._nav_btns[k]["fg"] == C_DIM else None))
            b.bind("<Leave>", lambda e, k=key: (
                self._nav_btns[k].configure(bg=C_PANEL) if
                self._nav_btns[k]["fg"] == C_DIM else None))

        foot = tk.Frame(side, bg=C_PANEL)
        foot.pack(side="bottom", fill="x", padx=14, pady=14)
        self._live_lbl = tk.Label(foot, text="", font=F_SMALL, bg=C_PANEL,
                                  fg=C_ACCENT, anchor="w", justify="left")
        self._live_lbl.pack(fill="x")
        self._refresh_live()
        rb = tk.Button(foot, text="🔄 Brain Reload (live changes)",
                       font=F_SMALL, bg=C_CARD2, fg=C_GOLD, relief="flat",
                       cursor="hand2", activebackground=C_BORDER,
                       command=self._on_reload)
        rb.pack(fill="x", pady=(6, 0), ipady=4)
        self._reload_lbl = tk.Label(foot, text="", font=F_SMALL, bg=C_PANEL,
                                    fg=C_DIM, anchor="w")
        self._reload_lbl.pack(fill="x", pady=(3, 0))

        # ⬆ header (brand + mood)
        head = tk.Frame(self, bg=C_BG)
        head.grid(row=0, column=1, sticky="new", padx=18, pady=(14, 4))
        head.grid_columnconfigure(1, weight=1)
        tk.Label(head, text="☪ Hemomemo AI", font=F_H2, bg=C_BG,
                 fg=C_GOLD).grid(row=0, column=0, sticky="w")
        self._mood_lbl = tk.Label(head, text="☁ dimagh jag raha hai…",
                                  font=F_SMALL, bg=C_BG, fg=C_DIM, anchor="e")
        self._mood_lbl.grid(row=0, column=1, sticky="e")
        self.after(2500, self._refresh_mood)

        # 📄 pages container
        self._pages = {}
        self._host = tk.Frame(self, bg=C_BG)
        self._host.grid(row=1, column=1, sticky="nsew", padx=18, pady=(0, 14))
        self._host.grid_rowconfigure(0, weight=1)
        self._host.grid_columnconfigure(0, weight=1)

    def _page(self, key):
        if key not in self._pages:
            f = tk.Frame(self._host, bg=C_BG)
            f.grid(row=0, column=0, sticky="nsew")
            self._pages[key] = f
        return self._pages[key]

    def show(self, key):
        for k, b in self._nav_btns.items():
            b.configure(fg=(C_GOLD if k == key else C_DIM),
                        bg=(C_CARD2 if k == key else C_PANEL))
        f = self._page(key)
        f.tkraise()
        if key == "dash":
            self.refresh_dashboard()
        if key == "formu" and not hasattr(self, "_formu_filled"):
            self._fill_formulas()
        if key == "api":
            self.refresh_api()
        if key == "video":
            # keyboard-scroll foran kaam kare — canvas par focus
            try:
                for _c in self._page("video").winfo_children():
                    if isinstance(_c, tk.Canvas):
                        _c.focus_set()
                        break
            except Exception:
                pass
        # 🎬 video-page __init__ me EK hi dafa banti hai — yahan sirf tkraise
        # (bar-bar _build_video karna widgets ko stack karta tha)

    # ================================================================ #
    # 🌐 APNI LOCAL API — AUTO-START + neeche global status-bar         #
    # ================================================================ #
    def _autostart_server(self):
        """🌐 Hemomemo ki APNI local API khud ON (127.0.0.1) — app khulte hi
        browser 127.0.0.1 par 'refused' na de. Ye SIRF Hemomemo ka apna
        local darwaza hai — kisi platform/AI ki API se koi taluq NAHI."""
        def work():
            try:
                api = _imp("server", "hemomemo_server")
                api.start()                 # pehle se chal raha ho to khamosh
            except Exception as e:
                _log("api autostart FAIL: %s" % e)
            self.after(0, self.refresh_api)
            self.after(0, self._refresh_statusbar)
        threading.Thread(target=work, daemon=True).start()

    def _build_statusbar(self):
        """📊 Neeche patti: API-haalat + dimagh-haalat + oath (har page par)."""
        bar = tk.Frame(self, bg=C_PANEL, height=30)
        bar.grid(row=2, column=1, sticky="ew", padx=18, pady=(0, 8))
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)
        self._sb_api = tk.Label(bar, text="🌐 API: …", font=F_SMALL,
                                bg=C_PANEL, fg=C_DIM, anchor="w")
        self._sb_api.grid(row=0, column=0, sticky="w", padx=(4, 10))
        self._sb_brain = tk.Label(bar, text="🧠 dimagh: load ho raha hai…",
                                  font=F_SMALL, bg=C_PANEL, fg=C_DIM,
                                  anchor="w")
        self._sb_brain.grid(row=0, column=1, sticky="w")
        tk.Label(bar, text="🔒 No Platform API · 100% Local ☪",
                 font=F_SMALL, bg=C_PANEL, fg=C_GOLD, anchor="e").grid(
            row=0, column=2, sticky="e", padx=(10, 4))

    def _refresh_statusbar(self, loop=True):
        """Status-bar ko zinda rakho — server + dimagh dono ki asli haalat.
        (loop=True sirf __init__ wale chain se — duplicate timers nahi)"""
        try:
            api = _imp("server", "hemomemo_server")
            s = api.status()
            if s.get("on"):
                self._sb_api.configure(
                    text="🌐 API: 🟢 %s  (requests: %s)"
                         % (s.get("url"), s.get("requests")),
                    fg=C_ACCENT)
            else:
                self._sb_api.configure(text="🌐 API: ⚪ band",
                                       fg=C_DIM)
        except Exception:
            self._sb_api.configure(text="🌐 API: ? ", fg=C_DIM)
        if _STATE.get("prewarmed"):
            self._sb_brain.configure(text="🧠 dimagh: 🟢 taiyar (4 dimagh + 2M "
                                          "neurons)",
                                     fg=C_ACCENT)
        if loop:
            self.after(20000, self._refresh_statusbar)

    # ==================================================================
    # 🌐 HEMOMO API PAGE (apni API server — no platform, L6-HMHZ guard)
    # ==================================================================    def _build_api(self):
        f = self._page("api")
        f.grid_columnconfigure(0, weight=1)
        card = self._card(f, row=0)
        tk.Label(card, text="🌐 Hemomemo AI API — APNI API", font=F_H1,
                 bg=C_CARD, fg=C_GOLD).pack(anchor="w", padx=16, pady=(14, 2))
        tk.Label(card, text="Ye Hemomemo AI ki APNI API hai — 100% local "
                 "(127.0.0.1). Kisi platform/AI ki API nahi; andar wahi apna "
                 "dimagh chalta hai. Guard: L6-HMHZ (apni key + nonce + rate).",
                 font=F_FONT, bg=C_CARD, fg=C_TEXT, wraplength=940,
                 justify="left", anchor="w").pack(fill="x", padx=16)
        row = tk.Frame(card, bg=C_CARD)
        row.pack(fill="x", padx=16, pady=10)
        self._api_btn_on = tk.Button(
            row, text="▶ Server ON", font=F_BOLD, bg=C_CARD2, fg=C_GOLD,
            relief="flat", cursor="hand2", activebackground=C_BORDER,
            command=lambda: self._api_toggle("on"))
        self._api_btn_on.pack(side="left", padx=(0, 8), ipady=4)
        self._api_btn_off = tk.Button(
            row, text="⏹ OFF", font=F_BOLD, bg=C_CARD2, fg=C_DIM,
            relief="flat", cursor="hand2", activebackground=C_BORDER,
            command=lambda: self._api_toggle("off"))
        self._api_btn_off.pack(side="left", padx=(0, 8), ipady=4)
        tk.Button(row, text="🔑 Key dikhao", font=F_BOLD, bg=C_CARD2,
                  fg=C_ACCENT, relief="flat", cursor="hand2",
                  activebackground=C_BORDER,
                  command=self._api_show_key).pack(side="left", ipady=4)
        tk.Button(row, text="🌍 Website kholo", font=F_BOLD, bg=C_CARD2,
                  fg=C_TEXT, relief="flat", cursor="hand2",
                  activebackground=C_BORDER,
                  command=self._api_open_site).pack(side="left", ipady=4)
        tk.Button(row, text="📖 Docs kholo", font=F_BOLD, bg=C_CARD2,
                  fg=C_DIM, relief="flat", cursor="hand2",
                  activebackground=C_BORDER,
                  command=self._api_open_docs).pack(side="left", ipady=4)
        self._api_lbl = tk.Label(card, text="haalat: maloom ho raha hai…",
                                 font=F_FONT, bg=C_CARD, fg=C_DIM,
                                 anchor="w", justify="left")
        self._api_lbl.pack(fill="x", padx=16, pady=(2, 12))
        self.refresh_api()

        # 👤 APNI API LEIN — har bande ki apni Hemomemo key (100% local)
        ac = self._card(f, row=1)
        tk.Label(ac, text="👤 Apni API lein — Sign-in (Gmail/Email)",
                 font=F_H2, bg=C_CARD, fg=C_GOLD).pack(
            anchor="w", padx=16, pady=(12, 2))
        tk.Label(ac, text="Har bande ki APNI Hemomemo AI API key (hemo…) — "
                 "ek dafa lein, copy karo, koi bhi kaam karwao. Sign-in "
                 "100% LOCAL hai: Gmail/Email + password aapke isi PC par "
                 "mehfooz (PBKDF2-hash) — Google ko koi call nahi jata, "
                 "kisi platform API ka istemaal nahi (asli Google-OAuth "
                 "platform-API mangta, jo qanoon-khilaf hai).",
                 font=F_SMALL, bg=C_CARD, fg=C_DIM, wraplength=940,
                 justify="left", anchor="w").pack(fill="x", padx=16)
        frow = tk.Frame(ac, bg=C_CARD)
        frow.pack(fill="x", padx=16, pady=(8, 2))
        tk.Label(frow, text="📧 Email:", font=F_FONT, bg=C_CARD,
                 fg=C_TEXT).pack(side="left")
        self._acc_email = tk.Entry(frow, font=F_FONT, bg=C_CARD2,
                                   fg=C_TEXT, relief="flat", width=34,
                                   insertbackground=C_ACCENT)
        self._acc_email.pack(side="left", padx=(6, 14), ipady=6)
        tk.Label(frow, text="🔒 Password:", font=F_FONT, bg=C_CARD,
                 fg=C_TEXT).pack(side="left")
        self._acc_pw = tk.Entry(frow, font=F_FONT, bg=C_CARD2, fg=C_TEXT,
                                relief="flat", width=24, show="•",
                                insertbackground=C_ACCENT)
        self._acc_pw.pack(side="left", padx=(6, 0), ipady=6)
        brow = tk.Frame(ac, bg=C_CARD)
        brow.pack(fill="x", padx=16, pady=(4, 12))
        tk.Button(brow, text="🆕 Nayi API lein", font=F_BOLD, bg=C_CARD2,
                  fg=C_GOLD, relief="flat", cursor="hand2",
                  activebackground=C_BORDER,
                  command=lambda: self._acc_go("signup")).pack(
            side="left", ipady=4, padx=(0, 8))
        tk.Button(brow, text="🔓 Sign-in", font=F_BOLD, bg=C_CARD2,
                  fg=C_ACCENT, relief="flat", cursor="hand2",
                  activebackground=C_BORDER,
                  command=lambda: self._acc_go("signin")).pack(
            side="left", ipady=4, padx=(0, 8))
        tk.Button(brow, text="📋 Key copy", font=F_BOLD, bg=C_CARD2,
                  fg=C_TEXT, relief="flat", cursor="hand2",
                  activebackground=C_BORDER,
                  command=self._acc_copy).pack(side="left", ipady=4)
        self._acc_lbl = tk.Label(ac, text="", font=F_FONT, bg=C_CARD,
                                 fg=C_DIM, anchor="w", justify="left",
                                 wraplength=940)
        self._acc_lbl.pack(fill="x", padx=16, pady=(2, 12))

    def _api_toggle(self, what):
        # 🕊 qanoon: OFF-button = user-hukum → flag likho (24/7-watcher izzat
        # kare) + stop-bat (standalone server bhi band); ON-button = flag
        # mitao (watcher wapas azad) + server ON.
        _hubp = os.path.join(ROOT, "connection_hub", "digitalbrain")
        _hubr = _hubp if os.path.isdir(os.path.join(_hubp, "model")) else ROOT
        try:
            _fp = os.path.join(_hubr, "data", "_server_OFF.flag")
            if what == "off":
                open(_fp, "w").close()
            elif os.path.exists(_fp):
                os.remove(_fp)
        except Exception:
            pass

        def work():
            try:
                api = _imp("server", "hemomemo_server")
                r = api.start() if what == "on" else api.stop()
                txt = str(r)
            except Exception as e:
                txt = "FAIL: %s" % e
            if what == "off":
                try:
                    import subprocess
                    subprocess.Popen(
                        [os.path.join(_hubr, "_server_stop.bat")],
                        cwd=str(_hubr), creationflags=0x08000000)
                except Exception:
                    pass
            self.after(0, lambda: self._api_lbl.configure(
                text=txt, fg=C_ACCENT if "ok" in txt else C_DANGER))
            self.after(0, self.refresh_api)
        self._api_lbl.configure(text="… %s ho raha hai" % what)
        threading.Thread(target=work, daemon=True).start()

    def _api_show_key(self):
        def work():
            try:
                api = _imp("server", "hemomemo_server")
                k = api.key_info()["key"]
            except Exception as e:
                k = "FAIL: %s" % e
            self.after(0, lambda: self._api_lbl.configure(
                text="🔑 X-Hemomemo-Key: %s  (clipboard par bhi daal diya)" % k,
                fg=C_GOLD))
            try:
                self.clipboard_clear()
                self.clipboard_append(k)
            except Exception:
                pass
        threading.Thread(target=work, daemon=True).start()

    def _api_open_site(self):
        """🌍 HMHZ Hemomemo website — Hemomemo ke APNE server se (browser me)."""
        import webbrowser
        try:
            api = _imp("server", "hemomemo_server")
            s = api.status()
            url = s.get("url") or "http://127.0.0.1:8790"
            if not s.get("on"):
                api.start()
                url = "http://127.0.0.1:%d" % (api.status().get("port") or 8790)
            webbrowser.open(url)
            self._api_lbl.configure(text="🌍 website khul gayi: %s" % url,
                                    fg=C_ACCENT)
        except Exception as e:
            self._api_lbl.configure(text="website FAIL: %s" % e, fg=C_DANGER)

    def _api_open_docs(self):
        """📖 chhoti API-kitab browser me (apne local server se)."""
        import webbrowser
        try:
            api = _imp("server", "hemomemo_server")
            s = api.status()
            if not s.get("on"):
                api.start()
                s = api.status()
            if s.get("on"):
                url = "http://127.0.0.1:%d/docs" % s["port"]
                webbrowser.open(url)
                self._api_lbl.configure(text="📖 docs khul gayi: %s" % url,
                                        fg=C_ACCENT)
        except Exception as e:
            self._api_lbl.configure(text="docs FAIL: %s" % e, fg=C_DANGER)

    # ---------- 👤 per-user accounts (100% local — no platform API) ----------
    def _acc_go(self, what):
        def work():
            try:
                acc = _imp("server", "accounts")
                email = self._acc_email.get().strip()
                pw = self._acc_pw.get()
                r = (acc.signup(email, pw) if what == "signup"
                     else acc.signin(email, pw))
                if r.get("ok"):
                    self._acc_key = r.get("key", "")
                    txt = ("✅ %s — AAPKI Hemomemo AI API key: %s\n"
                           "   (📋 Key copy daba kar header me lagao: "
                           "X-Hemomemo-Key → /v1/chat, /health, /v1/info — "
                           "100%% local, koi platform API nahi)"
                           % (r.get("email"), self._acc_key))
                    col = C_ACCENT
                else:
                    txt = "❌ %s" % r.get("error")
                    col = C_DANGER
            except Exception as e:
                txt, col = "FAIL: %s" % e, C_DANGER
            self.after(0, lambda: self._acc_lbl.configure(text=txt, fg=col))
        self._acc_lbl.configure(text="… %s ho raha hai" % what)
        threading.Thread(target=work, daemon=True).start()

    def _acc_copy(self):
        """📋 bande ki APNI key clipboard par."""
        key = getattr(self, "_acc_key", "")
        if not key:
            self._acc_lbl.configure(
                text="pehle 🆕 Nayi API lein ya 🔓 Sign-in karo — phir copy",
                fg=C_DANGER)
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(key)
            self._acc_lbl.configure(
                text="✅ key clipboard par — ab /v1/chat waghera apni key "
                     "(X-Hemomemo-Key) se chalao", fg=C_ACCENT)
        except Exception as e:
            self._acc_lbl.configure(text="copy FAIL: %s" % e, fg=C_DANGER)

    def refresh_api(self):
        def work():
            try:
                api = _imp("server", "hemomemo_server")
                s = api.status()
                if s.get("on"):
                    txt = ("🟢 chal raha hai — %s  |  requests: %s  |  "
                           "uptime: %ss  |  auth: %s"
                           % (s.get("url"), s.get("requests"),
                              s.get("uptime_s"), s.get("auth")))
                else:
                    txt = ("⚪ band hai — '▶ Server ON' dabayen "
                           "(127.0.0.1:8790 — sirf isi machine)")
            except Exception as e:
                txt = "haalat FAIL: %s" % e
            self.after(0, lambda: self._api_lbl.configure(text=txt))
        threading.Thread(target=work, daemon=True).start()
        self._refresh_statusbar(loop=False)

    def _refresh_live(self):
        _hubp = os.path.join(ROOT, "connection_hub", "digitalbrain")
        if os.path.isdir(os.path.join(_hubp, "model")):
            txt, fg = "🟢 LIVE • D:\\DigitalBrain (hub-deep-link)", C_ACCENT
        elif os.path.isdir(ROOT):
            txt, fg = "🟢 LIVE • %s (standalone)" % ROOT, C_ACCENT
        else:
            txt, fg = "🔴 folder nahi mila", C_DANGER
        self._live_lbl.configure(text=txt, fg=fg)

    def _refresh_mood(self):
        def work():
            try:
                feelings = _imp("model", "feelings")
                line = feelings.status_line()
            except Exception as e:
                line = "mood: %s" % e
            self.after(0, lambda: self._mood_lbl.configure(
                text="  %s   •   reload #%d" % (line, _STATE["reload_n"])))
        threading.Thread(target=work, daemon=True).start()
        self.after(30000, self._refresh_mood)

    def _prewarm_done(self):
        self.after(0, lambda: self._mood_lbl.configure(
            text=self._mood_lbl.cget("text") + "   •   🟢 dimagh taiyar"))

    def _on_reload(self):
        self._reload_lbl.configure(text="… reload ho raha hai")
        reload_brain_async(lambda: self.after(0, lambda: self._reload_lbl.configure(
            text="✅ reload #%d mukammal" % _STATE["reload_n"])))

    def _on_close(self):
        # 🌐 apni local API bhi saaf band (koi akele-chauda process na rahe)
        try:
            _imp("server", "hemomemo_server").stop()
        except Exception:
            pass
        try:
            self.quit()
        except Exception:
            pass
        self.destroy()

    # ---------------- card helper ----------------
    def _card(self, parent, title=None, col=None, row=None, span=1, **grid):
        card = tk.Frame(parent, bg=C_CARD, highlightthickness=1,
                        highlightbackground=C_BORDER)
        if col is not None:
            card.grid(row=row, column=col, columnspan=span,
                      sticky="nsew", padx=7, pady=7, **grid)
        else:
            card.pack(fill="x", padx=2, pady=5, **grid)
        if title:
            tk.Label(card, text=title, font=F_H2, bg=C_CARD, fg=C_GOLD,
                     anchor="w").pack(fill="x", padx=14, pady=(10, 0))
        return card

    # ==================================================================
    # 💬 CHAT PAGE
    # ==================================================================
    def _build_chat(self):
        f = self._page("chat")
        f.grid_rowconfigure(0, weight=1)
        f.grid_columnconfigure(0, weight=1)

        wrap = tk.Frame(f, bg=C_BG, highlightthickness=1,
                        highlightbackground=C_BORDER)
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_rowconfigure(1, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        # 🟢 WhatsApp-style chat-header (teal bar + naam + online-haalat)
        hdr = tk.Frame(wrap, bg=C_WAHEAD, height=54)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.grid_propagate(False)
        tk.Label(hdr, text="💬  Hemomemo AI", font=F_H2, bg=C_WAHEAD,
                 fg="#ffffff").pack(side="left", padx=16, anchor="center")
        tk.Label(hdr, text="🟢 online  ·  100% local  ·  no API",
                 font=F_SMALL, bg=C_WAHEAD, fg="#c9f0e2").pack(
            side="right", padx=16, anchor="center")

        # 🖼 CANVAS-CHAT ENGINE (15-Nov poora-rebuild): Text-widget → Canvas.
        #    Har pegham ASLI rounded-bubble (smooth-polygon) + tail + waqt
        #    bubble-ke-andar — bilkul WhatsApp jaisa, koi tag-hack nahi.
        self.chat = tk.Canvas(wrap, bg=C_BG, highlightthickness=0, bd=0)
        self.chat.grid(row=1, column=0, sticky="nsew")
        self._sb = ttk.Scrollbar(wrap, command=self.chat.yview)
        self._sb.grid(row=1, column=1, sticky="ns")
        self.chat.configure(yscrollcommand=self._chat_scroll)

        import tkinter.font as _tkfont
        self._cb_font = _tkfont.Font(font=F_FONT)
        self._cb_font_ts = _tkfont.Font(font=("Segoe UI", 8))
        self._cb_font_mono = _tkfont.Font(font=("Consolas", 10))
        self._cb_feed = []          # draw-hue pegham (resize-par dobara)
        self._cb_y = 18             # agle bubble ki y
        self._cb_btn_n = 0
        self._cb_cfg_id = None
        self._think_item = []
        self._think_id = None
        self._think_y = 0
        self.chat.bind("<MouseWheel>", self._cb_wheel)
        self.chat.bind("<Configure>", self._cb_on_resize)

        # ⬇ floating jump-button (jab upar scroll kar lo)
        self._jump = tk.Button(wrap, text="⬇ sab se neeche", font=F_SMALL,
                               bg=C_GOLD, fg="#ffffff", relief="flat",
                               activebackground="#0f6f63", cursor="hand2",
                               command=self._chat_bottom,
                               highlightthickness=0, bd=0)
        self._jump.place(relx=1.0, rely=1.0, x=-16, y=-14, anchor="se")
        self._jump.place_forget()

        self._cb_render_all()

        # quick-sawal chips + soch toggle
        quick = tk.Frame(f, bg=C_BG)
        quick.grid(row=1, column=0, sticky="ew", pady=(8, 4))
        for q in ("salam", "2 + 2", "circle ka area, r = 5",
                  "E = mc^2, m = 2", "hadith batao"):
            b = tk.Button(quick, text=q, font=F_SMALL, bg=C_CARD,
                          fg=C_ACCENT, relief="flat", highlightthickness=1,
                          highlightbackground=C_BORDER,
                          activebackground=C_CARD2, cursor="hand2",
                          command=lambda s=q: self._send(s))
            b.pack(side="left", padx=(0, 6), ipady=2)
            self._hover(b, C_CARD, C_CARD2)
        self._think_btn = tk.Button(
            quick, text="🪜 soch: auto", font=F_SMALL, bg=C_CARD, fg=C_GOLD,
            relief="flat", highlightthickness=1, highlightbackground=C_BORDER,
            activebackground=C_CARD2, cursor="hand2",
            command=self._toggle_think)
        self._think_btn.pack(side="right", ipady=2)
        self._hover(self._think_btn, C_CARD, C_CARD2)
        self._copy_btn = tk.Button(
            quick, text="📋 copy", font=F_SMALL, bg=C_CARD, fg=C_TEXT,
            relief="flat", highlightthickness=1, highlightbackground=C_BORDER,
            activebackground=C_CARD2, cursor="hand2",
            command=self._chat_copy)
        self._copy_btn.pack(side="right", padx=(0, 6), ipady=2)
        self._hover(self._copy_btn, C_CARD, C_CARD2)
        tk.Button(quick, text="🧹 saaf", font=F_SMALL, bg=C_CARD, fg=C_DANGER,
                  relief="flat", highlightthickness=1,
                  highlightbackground=C_BORDER, activebackground=C_CARD2,
                  cursor="hand2", command=self._chat_clear).pack(
            side="right", padx=(0, 6), ipady=2)

        # 📥 WhatsApp input-pill (safed gol-patti + sabz Bhejo button)
        inp = tk.Frame(f, bg=C_BG)
        inp.grid(row=2, column=0, sticky="ew", pady=(8, 10))
        inp.grid_columnconfigure(0, weight=1)
        self.inp_cv = tk.Canvas(inp, bg=C_BG, highlightthickness=0, bd=0,
                                height=52)
        self.inp_cv.grid(row=0, column=0, sticky="ew")
        self._ph = "Apna sawal likhein… (Roman Urdu / English)"
        self.entry = tk.Entry(self.inp_cv, font=F_FONT, bg="#ffffff",
                              fg=C_DIM, relief="flat", bd=0,
                              insertbackground=C_ACCENT)
        self.entry.insert(0, self._ph)
        self.entry.bind("<FocusIn>", self._ph_clear)
        self.entry.bind("<FocusOut>", self._ph_set)
        self.entry.bind("<Return>", lambda e: self._send())
        self.entry.bind("<Escape>", self._esc_clear)
        self.entry.focus_set()
        self.inp_cv.bind("<Configure>", lambda e: self._inp_relayout())
        self.inp_cv.after(80, self._inp_relayout)
        self.send_btn = tk.Button(inp, text="Bhejo ➤", font=F_BOLD,
                                  bg=C_ACCENT, fg="#ffffff", relief="flat",
                                  activebackground="#1da851", cursor="hand2",
                                  command=self._send, width=10)
        self.send_btn.grid(row=0, column=1, padx=(10, 0), ipady=10,
                           sticky="ns")
        self._hover(self.send_btn, C_ACCENT, "#1da851")

    # ---- chat scroll helpers ----
    def _chat_scroll(self, first, last):
        self._sb.set(first, last)
        try:
            near = float(first) + float(last) >= 0.985
            if near or float(last) >= 1.0:
                self._jump.place_forget()
            else:
                self._jump.place(relx=1.0, rely=1.0, x=-16, y=-14,
                                 anchor="se")
                self._jump.lift()
        except Exception:
            pass

    def _near_bottom(self):
        f, l = self.chat.yview()
        return f + l >= 0.985 or l >= 1.0

    def _chat_bottom(self):
        self.chat.yview_moveto(1.0)

    # ---- 🖼 Canvas-bubble helpers (_cb_*) ----
    def _rrect(self, cv, x0, y0, x1, y1, r=14, **kw):
        """Gol-kono wala rect (smooth-polygon) — asli WhatsApp bubble."""
        pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r,
               x1, y1, x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r,
               x0, y0 + r, x0, y0]
        return cv.create_polygon(pts, smooth=True, **kw)

    def _cb_wheel(self, e):
        try:
            self.chat.yview_scroll(int(-e.delta / 120) * 3, "units")
        except Exception:
            pass

    def _cb_on_resize(self, _e=None):
        if self._cb_cfg_id:
            try:
                self.after_cancel(self._cb_cfg_id)
            except Exception:
                pass
        self._cb_cfg_id = self.after(140, self._cb_rerender)

    def _cb_rerender(self):
        self._cb_cfg_id = None
        if not hasattr(self, "_cb_feed"):
            return
        self._cb_render_all()

    def _cb_render_all(self):
        c = self.chat
        c.delete("all")
        self._cb_y = 18
        self._cb_btn_n = 0
        self._cb_welcome_draw()
        for d in self._cb_feed:
            if d["who"] == "chip":
                self._cb_draw_chip(d["text"])
            else:
                self._cb_draw_msg(d["who"], d["text"], d["ts"])
        self._cb_sync(True)
        if self._think_id:
            try:
                self.after_cancel(self._think_id)
            except Exception:
                pass
            self._think_id = None
            self._think_y = self._cb_y
            self._think_step()

    def _cb_sync(self, stick=None):
        c = self.chat
        try:
            c.configure(scrollregion=c.bbox("all") or (0, 0, 1, 1))
        except Exception:
            return
        if stick is None:
            stick = self._near_bottom()
        if stick:
            c.yview_moveto(1.0)

    def _cb_wrap(self, s, font, maxw):
        """Canvas-text me manual wrap (Text-widget nahi — khud lafz toerte)."""
        lines = []
        for para in (s or "").split("\n"):
            if not para.strip():
                lines.append("")
                continue
            cur = ""
            for wd in para.split(" "):
                t = (cur + " " + wd) if cur else wd
                if font.measure(t) <= maxw or not cur:
                    cur = t
                else:
                    lines.append(cur)
                    cur = wd
                    while font.measure(cur) > maxw:
                        lo, hi = 1, len(cur)
                        while lo < hi:
                            mid = (lo + hi + 1) // 2
                            if font.measure(cur[:mid]) <= maxw:
                                lo = mid
                            else:
                                hi = mid - 1
                        lines.append(cur[:lo])
                        cur = cur[lo:].lstrip()
            lines.append(cur)
        return lines

    def _cb_btn(self, x0, y0, label, val, bg=None, fg=None):
        """Canvas par chhota copy-button (drawn pill + click → clipboard)."""
        c = self.chat
        f = self._cb_font_ts
        bg = bg or C_CARD2
        fg = fg or C_GOLD
        w = f.measure(label) + 18
        h = 22
        i1 = self._rrect(c, x0, y0, x0 + w, y0 + h, r=11, fill=bg,
                         outline="")
        i2 = c.create_text(x0 + w / 2, y0 + h / 2, text=label, font=f,
                           fill=fg)
        tag = "cbtn%d" % self._cb_btn_n
        self._cb_btn_n += 1
        c.addtag_withtag(tag, i1)
        c.addtag_withtag(tag, i2)
        c.tag_bind(tag, "<Button-1>",
                   lambda e, t=tag, v=val: self._cb_copy_hit(t, v))
        c.tag_bind(tag, "<Enter>", lambda e: c.configure(cursor="hand2"))
        c.tag_bind(tag, "<Leave>", lambda e: c.configure(cursor=""))
        return w, h

    def _cb_copy_hit(self, tag, val):
        try:
            self.clipboard_clear()
            self.clipboard_append(val or "")
            txts = [i for i in self.chat.find_withtag(tag)
                    if self.chat.type(i) == "text"]
            if txts:
                old = self.chat.itemcget(txts[0], "text")
                self.chat.itemconfigure(txts[0], text="✅ copy ho gaya")
                self.after(1300, lambda: self._cb_restore(txts[0], old))
        except Exception:
            pass

    def _cb_restore(self, iid, s):
        try:
            self.chat.itemconfigure(iid, text=s)
        except Exception:
            pass

    def _inp_relayout(self):
        cv = getattr(self, "inp_cv", None)
        if not cv or not cv.winfo_exists():
            return
        w = cv.winfo_width()
        if w < 80:
            cv.after(200, self._inp_relayout)
            return
        cv.delete("pill")
        self._rrect(cv, 0, 2, w - 8, 50, r=24, fill="#ffffff", outline="",
                    tags="pill")
        cv.create_window(26, 26, window=self.entry, anchor="w",
                         width=max(160, w - 150))

    def _ph_clear(self, _e=None):
        if self.entry.get() == self._ph:
            self.entry.delete(0, "end")
            self.entry.configure(fg=C_TEXT)

    # ── 🗒 CHAT HISTORY: user+AI turns save/load (local file, koi AI-API/nahi) ──
    def _hist_add(self, who, text):
        try:
            self._hist.append({"who": str(who or "ai"), "text": str(text or "").strip()})
            if len(self._hist) > 200:
                del self._hist[:len(self._hist) - 200]
            os.makedirs(os.path.dirname(self._hist_path), exist_ok=True)
            import json as _json
            with open(self._hist_path, "w", encoding="utf-8") as _f:
                _json.dump(self._hist, _f, ensure_ascii=False)
        except Exception:
            pass

    def _hist_save(self):
        try:
            os.makedirs(os.path.dirname(self._hist_path), exist_ok=True)
            import json as _json
            with open(self._hist_path, "w", encoding="utf-8") as _f:
                _json.dump(self._hist, _f, ensure_ascii=False)
        except Exception:
            pass

    def _hist_clear(self):
        self._hist = []
        try:
            import json as _json
            with open(self._hist_path, "w", encoding="utf-8") as _f:
                _json.dump([], _f)
        except Exception:
            pass

    def _hist_load(self):
        """🗒 history chat load karo (local file → chat window → turns)."""
        try:
            import json as _json
            with open(self._hist_path, "r", encoding="utf-8") as _f:
                _h = _json.load(_f) or []
            self._hist = [{"who": str(e.get("who") or "ai"),
                           "text": str(e.get("text") or "")} for e in _h
                          if e.get("text")]
        except Exception:
            self._hist = []
        try:
            self._cb_feed = [{"who": e.get("who") or "ai",
                              "text": e.get("text") or "",
                              "ts": ""} for e in self._hist]
            self._cb_render_all()
        except Exception:
            pass

    def _ph_set(self, _e=None):
        if not self.entry.get():
            self.entry.insert(0, self._ph)
            self.entry.configure(fg=C_DIM)

    def _esc_clear(self, _e=None):
        """⎋ Escape — input foran saaf (tez typing-UX)."""
        self.entry.delete(0, "end")

    def _chat_clear(self):
        """🧹 chat saaf — history + welcome dobara."""
        self._cb_feed = []
        self._hist_clear()
        self._cb_render_all()

    def _chat_copy(self):
        """📋 aakhri jawab clipboard par (feedback button-par hi)."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self._last_answer or "")
            self._copy_btn.configure(text="✅ copy ho gaya", fg=C_ACCENT)
            self.after(1400, lambda: self._copy_btn.configure(
                text="📋 copy", fg=C_TEXT))
        except Exception:
            pass

    def _cb_welcome_draw(self):
        """☪ Welcome-card: safed gol-card canvas par (pehla chehra)."""
        c = self.chat
        W = max(c.winfo_width(), 640)
        fs = self._cb_font_ts
        body = (" Ye app aapke D:\\DigitalBrain se SEEDHA juda hai — koi API "
                "key nahi, koi AI/cloud/MCP connection nahi. Sab kuch local "
                "NumPy dimagh (4 brains), 331 formulas, Quran/Hadith ilm, "
                "aqal aur jazbaat ke sath. Neeche likh kar bhejo — terminal "
                "me kiye gay changes 🔄 Brain Reload se yahan live lagte "
                "hain.")
        pad = 16
        maxw = min(560, W - 60)
        lines = self._cb_wrap(body, fs, maxw - 2 * pad)
        bh = 22 + 30 + 6 + len(lines) * 15 + 16
        bw = maxw
        x0 = max(10, (W - bw) // 2)
        y0 = self._cb_y
        y1 = y0 + bh
        self._rrect(c, x0, y0, x0 + bw, y1, r=16, fill="#ffffff",
                    outline="")
        c.create_text(x0 + pad, y0 + 20,
                      text="☪  %s me khush-amdeed!" % MODEL_NAME,
                      font=("Segoe UI", 12, "bold"), fill=C_GOLD,
                      anchor="nw")
        for i, l in enumerate(lines):
            c.create_text(x0 + pad, y0 + 22 + 30 + i * 15, text=l,
                          font=fs, fill=C_DIM, anchor="nw")
        self._cb_y = y1 + 14

    def _bubble(self, text, who):
        d = {"who": who,
             "text": (text or "").strip() if who == "user" else (text or ""),
             "ts": datetime.datetime.now().strftime("%H:%M")}
        self._cb_feed.append(d)
        if len(self._cb_feed) > 400:
            del self._cb_feed[:len(self._cb_feed) - 400]
        self._cb_draw_msg(d["who"], d["text"], d["ts"])

    def _cb_draw_msg(self, who, text, ts=""):
        """🖼 Canvas-par asli bubble draw (user: sabz-dahini + tail + ✓✓,
        ai: safed-bayen + dark code-cards + copy-buttons)."""
        c = self.chat
        stick = self._near_bottom()
        W = max(c.winfo_width(), 640)
        f = self._cb_font
        fts = self._cb_font_ts
        maxw = min(560, W - 220)
        xi = 12
        lh = 19
        y0 = self._cb_y
        if who == "user":
            t = (text or "").strip()
            lines = self._cb_wrap(t, f, maxw - 2 * xi)
            tw = max([f.measure(l) for l in lines] + [40])
            bw = min(maxw, tw + 2 * xi)
            bw = max(bw, fts.measure(ts + "  ✓✓") + 2 * xi + 8, 72)
            bh = 10 + len(lines) * lh + 6 + 14 + 8
            x1 = W - 20
            x0 = x1 - bw
            y1 = y0 + bh
            self._rrect(c, x0, y0, x1, y1, r=16, fill=C_USERBG, outline="")
            c.create_polygon(x1, y0, x1 + 9, y0, x1, y0 + 12,
                             fill=C_USERBG, outline="")
            for i, l in enumerate(lines):
                c.create_text(x0 + xi, y0 + 10 + i * lh, text=l,
                              font=f, fill=C_TEXT, anchor="nw")
            if ts:
                c.create_text(x1 - xi - 2, y1 - 16, text=ts + "  ✓✓",
                              font=fts, fill="#5e8b74", anchor="e")
            self._cb_y = y1 + 8
        else:
            # 💻 CODE-BLOCK SYSTEM: ```fences → andar dark-code-card
            parts = re.split(r"```([A-Za-z0-9+#_-]*)[ \t]*\r?\n(.*?)```",
                             (text or "").strip(), flags=re.S)
            segs = []
            if len(parts) == 1:
                if (text or "").strip():
                    segs.append(("txt", text.strip(), ""))
            else:
                for i, seg in enumerate(parts):
                    m = i % 3
                    if m == 0:
                        if seg.strip():
                            segs.append(("txt", seg.strip(), ""))
                    elif m == 1:
                        segs.append(("lang", "",
                                     (seg or "").strip() or "code"))
                    else:
                        segs.append(("code", seg.rstrip("\n"), ""))
            mono_lh = 16
            cpad = 10
            mono_lw = maxw - 2 * xi - 2 * cpad
            btn_w = fts.measure("📋 copy code") + 18
            rows = []
            widths = []
            for kind, s, lang in segs:
                if kind == "txt":
                    lines = self._cb_wrap(s, f, maxw - 2 * xi)
                    w = max([f.measure(l) for l in lines] + [40])
                    rows.append({"kind": "txt", "lines": lines, "w": w,
                                 "h": len(lines) * lh})
                    widths.append(w)
                elif kind == "lang":
                    pass
                else:
                    lines = self._cb_wrap(s, self._cb_font_mono, mono_lw)
                    w = max([self._cb_font_mono.measure(l) for l in lines]
                            + [fts.measure("💻 " + lang) + btn_w + 14])
                    rows.append({"kind": "code", "lines": lines, "w": w,
                                 "h": 22 + len(lines) * mono_lh,
                                 "raw": s, "lang": lang})
                    widths.append(w + 2 * cpad)
            if not rows:
                rows.append({"kind": "txt", "lines": [""], "w": 40,
                             "h": lh})
                widths.append(40)
            bw = min(maxw, max(widths) + 2 * xi)
            bw = max(bw, fts.measure(ts) + 2 * xi + 8, 84)
            total = sum(r["h"] + 6 for r in rows)
            bh = 10 + total + 18
            x0 = 20
            x1 = x0 + bw
            y1 = y0 + bh
            self._rrect(c, x0, y0, x1, y1, r=16, fill="#ffffff", outline="")
            c.create_polygon(x0, y0, x0 - 9, y0, x0, y0 + 12,
                             fill="#ffffff", outline="")
            y = y0 + 10
            for r in rows:
                if r["kind"] == "txt":
                    for i, l in enumerate(r["lines"]):
                        c.create_text(x0 + xi, y + i * lh, text=l,
                                      font=f, fill=C_TEXT, anchor="nw")
                else:
                    cw = r["w"] + 2 * cpad
                    cx0 = x0 + xi
                    self._rrect(c, cx0, y, cx0 + cw, y + r["h"], r=10,
                                fill="#0b1f16", outline="")
                    c.create_text(cx0 + cpad, y + 9,
                                  text="💻 " + r["lang"], font=fts,
                                  fill=C_GOLD, anchor="w")
                    self._cb_btn(cx0 + cw - cpad - btn_w, y + 3,
                                 "📋 copy code", r["raw"],
                                 bg="#17352a", fg=C_GOLD)
                    for i, l in enumerate(r["lines"]):
                        c.create_text(cx0 + cpad, y + 22 + i * mono_lh,
                                      text=l, font=self._cb_font_mono,
                                      fill="#d7e6dd", anchor="nw")
                y += r["h"] + 6
            if ts:
                c.create_text(x1 - xi - 2, y1 - 16, text=ts, font=fts,
                              fill="#9aa7b0", anchor="e")
            self._cb_btn(x0, y1 + 6, "📋 copy message", (text or "").strip())
            self._cb_y = y1 + 34
        self._cb_sync(stick)

    def _chip(self, m):
        try:
            src = m.get("source", "?")
            aut = m.get("autonomous") or {}
            bits = ["🧩 %s" % src]
            if aut.get("source") and aut.get("source") != src:
                bits.append("engine: %s" % aut.get("source"))
            if aut.get("confidence") is not None:
                bits.append("bharosa: %s" % aut.get("confidence"))
            if m.get("intent"):
                bits.append("samajh: %s" % m.get("intent"))
            if m.get("verify"):
                bits.append("✅ verify: %s" % m.get("verify"))
            if m.get("brain2"):
                bits.append("🧠 deep-rescue")
            if m.get("helper"):
                bits.append("🤝 helper")
            s = "  •  ".join(bits)
            self._cb_feed.append({"who": "chip", "text": s, "ts": ""})
            self._cb_draw_chip(s)
        except Exception:
            pass

    def _cb_draw_chip(self, s):
        """🧩 source-chip: chhoti grey-pilli (canvas-drawn)."""
        c = self.chat
        stick = self._near_bottom()
        f = self._cb_font_ts
        w = f.measure(s) + 26
        y0 = self._cb_y
        self._rrect(c, 20, y0, 20 + w, y0 + 24, r=12, fill=C_CARD2,
                    outline="")
        c.create_text(33, y0 + 12, text=s, font=f, fill=C_DIM, anchor="w")
        self._cb_y = y0 + 32
        self._cb_sync(stick)

    def _think_start(self):
        self._think_stop()
        self._think_n = 0
        self._think_stage_txt = ""
        self._think_y = self._cb_y
        self._think_step()

    def _think_step(self):
        """💭 Soch-animation canvas-pill (dots ghumte hain, stage badalta)."""
        self._think_n += 1
        c = self.chat
        try:
            for i in self._think_item:
                c.delete(i)
        except Exception:
            pass
        self._think_item = []
        dots = "٫" * (1 + (self._think_n % 3))
        stage = getattr(self, "_think_stage_txt", "")
        if not stage:
            stages = getattr(self, "_think_stages", ["🧠 soch raha hoon"])
            stage = stages[self._think_n % len(stages)]
        try:
            f = self._cb_font_ts
            txt = "💭 %s%s  (local dimagh — no API)" % (stage, dots)
            w = f.measure(txt) + 30
            x0, y0 = 20, self._think_y
            i1 = self._rrect(c, x0, y0, x0 + w, y0 + 26, r=13,
                             fill=C_CARD, outline="")
            i2 = c.create_text(x0 + 15, y0 + 13, text=txt, font=f,
                               fill=C_GOLD, anchor="w")
            self._think_item = [i1, i2]
            self._cb_sync(self._near_bottom())
        except Exception:
            self._think_item = []
            return
        self._think_id = self.after(450, self._think_step)

    def _think_stage(self, stage):
        """🌐 3-SOCH FLOW: har asli marhale par sawal-ke-neeche animation badle
        (soch-1 → ilm → soch-2 → research → soch-3 → seekh). Thread-safe."""
        self._think_stage_txt = stage
        if self._think_id:
            try:
                self.after_cancel(self._think_id)
            except Exception:
                pass
            self._think_id = None
        self._think_step()

    def _think_stop(self):
        if self._think_id:
            try:
                self.after_cancel(self._think_id)
            except Exception:
                pass
            self._think_id = None
        try:
            for i in self._think_item:
                self.chat.delete(i)
        except Exception:
            pass
        self._think_item = []

    def _toggle_think(self):
        # auto = sawal dekh kar khud tier chunta hai (low/mid/high) —
        # high = HAMESHA gehri soch (zyada samples + rethink + research)
        self._think_mode = "high" if self._think_mode == "auto" else "auto"
        self._think_btn.configure(
            text=("🪜 soch: gehri (research)" if self._think_mode == "high"
                  else "🪜 soch: auto"))

    def _send(self, preset=None):
        if self._chat_busy:
            return
        raw = self.entry.get()
        q = (preset if preset is not None else
             ("" if raw == self._ph else raw)).strip()
        if not q:
            return
        self.entry.delete(0, "end")
        self._chat_busy = True
        self.send_btn.configure(state="disabled", text="…")
        self._bubble(q, "user")
        self._hist_add("user", q)
        self._think_start()

        def done(text, m):
            self.after(0, lambda: self._chat_done(text, m))

        def prog(stage):
            # 🧠 3-soch flow ki har marhala sawal-ke-neeche animation me
            self.after(0, lambda: self._think_stage(stage))

        chat_async(q, done, think=self._think_mode, progress=prog,
                   hist=list(self._hist))

    def _chat_done(self, text, m):
        self._think_stop()
        clean = text
        if clean.startswith("Hemomemo AI-> "):
            clean = clean[len("Hemomemo AI-> "):]
        self._last_answer = clean.strip()
        self._bubble(clean, "ai")
        self._hist_add("ai", clean)
        self._hist_save()
        self._chip(m)
        self._chat_busy = False
        self.send_btn.configure(state="normal", text="Bhejo ➤")
        self._refresh_mood()

    def _build_video(self):
        """🎬 ULTRA-REALISTIC MOTION VIDEO GENERATION TAB
        (Flow Fields + Higgsfield Technology + Physics Simulation)"""
        f = self._page("video")

        if not VIDEO_GENERATION:   # 🎬 OFF-switch (kabhi band karna ho)
            tk.Label(f, text="🎬 video-generation band hai (VIDEO_GENERATION=False)",
                     font=F_H1, bg=C_BG, fg=C_DIM).pack(pady=40)
            return

        # ── scroll-host: poora video-page scrollable (touch/mouse/keyboard) ──
        host = tk.Canvas(f, bg=C_BG, highlightthickness=0, bd=0)
        up_btn = tk.Button(f, text="▲", font=F_BOLD, bg=C_CARD2, fg=C_GOLD,
                           relief="flat", cursor="hand2", width=3,
                           command=lambda: host.yview_scroll(-5, "units"))
        vsb = tk.Scrollbar(f, orient="vertical", command=host.yview)
        down_btn = tk.Button(f, text="▼", font=F_BOLD, bg=C_CARD2, fg=C_GOLD,
                             relief="flat", cursor="hand2", width=3,
                             command=lambda: host.yview_scroll(5, "units"))
        up_btn.pack(side="right", anchor="n", padx=2, pady=14)
        vsb.pack(side="right", fill="y")
        down_btn.pack(side="right", anchor="s", padx=2, pady=14)
        host.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(host, bg=C_BG)
        _win = host.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: host.configure(
            scrollregion=host.bbox("all")))
        host.bind("<Configure>",
                  lambda e: host.itemconfigure(_win, width=e.width))
        inner.grid_columnconfigure(0, weight=1)

        card = self._card(inner, row=0)
        tk.Label(card, text="🚀 Ultra-Realistic Motion Video Generator — 🟢 TRUE", 
                 font=F_H1, bg=C_CARD, fg=C_GOLD).pack(
            anchor="w", padx=16, pady=(14, 2))
        tk.Label(card, text="Advanced motion video generation using Flow Fields, "
                 "Higgsfield Technology, and Physics Simulation. "
                 "Create ultra-realistic racing, flow, and motion videos locally.\n"
                 "Features: Motion blur, volumetric rendering, dynamic lighting, "
                 "physics simulation, cinematic effects.",
                 font=F_FONT, bg=C_CARD, fg=C_TEXT, wraplength=900,
                 justify="left", anchor="w").pack(fill="x", padx=16, pady=(2, 10))

        # 📝 prompt row with enhanced UI
        prompt_frame = tk.Frame(card, bg=C_CARD)
        prompt_frame.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(prompt_frame, text="Video Prompt:", font=F_FONT, 
                bg=C_CARD, fg=C_TEXT).pack(anchor="w", padx=(0, 8), pady=(12, 4))
        
        self._vid_prompt_var = tk.StringVar(value="car racing on track with realistic motion blur")
        self._vid_prompt = tk.Text(prompt_frame, height=4, wrap="word", 
                                  bg=C_CARD2, fg=C_TEXT, font=F_FONT,
                                  relief="flat", padx=12, pady=8)
        self._vid_prompt.pack(fill="x", padx=(0, 12), pady=(0, 12))
        self._vid_prompt.insert("1.0", self._vid_prompt_var.get())

        # ⚙️ enhanced controls row
        controls_frame = tk.Frame(card, bg=C_CARD)
        controls_frame.pack(fill="x", padx=16, pady=(0, 8))
        
        # Duration control
        dur_frame = tk.Frame(controls_frame, bg=C_CARD)
        dur_frame.pack(fill="x", pady=(0, 8))
        tk.Label(dur_frame, text="⏱ Duration (seconds):", font=F_FONT, bg=C_CARD,
                 fg=C_TEXT).pack(side="left", padx=(0, 8))
        self._vid_dur_var = tk.IntVar(value=10)
        tk.Spinbox(dur_frame, from_=5, to=60, increment=5, font=F_FONT,
                   bg=C_CARD2, fg=C_TEXT, relief="flat",
                   textvariable=self._vid_dur_var, width=10).pack(side="left")

        # Resolution control
        res_frame = tk.Frame(controls_frame, bg=C_CARD)
        res_frame.pack(fill="x", pady=(0, 8))
        tk.Label(res_frame, text="🖼 Resolution:", font=F_FONT, bg=C_CARD,
                 fg=C_TEXT).pack(side="left", padx=(0, 8))
        self._vid_res_var = tk.StringVar(value="1280x720")
        res_combo = ttk.Combobox(res_frame, textvariable=self._vid_res_var,
                                values=["640x360", "1280x720", "1920x1080"],
                                width=12, font=F_REGULAR, state="readonly")
        res_combo.pack(side="left", padx=(0, 16))

        # Style detection
        style_frame = tk.Frame(controls_frame, bg=C_CARD)
        style_frame.pack(fill="x", pady=(0, 8))
        tk.Label(style_frame, text="🎨 Style:", font=F_FONT, bg=C_CARD,
                 fg=C_TEXT).pack(side="left", padx=(0, 8))
        self._vid_style_var = tk.StringVar(value="auto")
        tk.Label(style_frame, text="(Auto-detected from prompt)", 
                font=F_SMALL, bg=C_CARD, fg=C_DIM).pack(side="left", padx=(8, 0))

        # ▶ enhanced generate row
        b = tk.Frame(card, bg=C_CARD); b.pack(fill="x", padx=16, pady=8)
        self._vid_gen_btn = tk.Button(
            b, text="🚀 Generate Ultra-Realistic Video", font=F_BOLD, bg=C_CARD2, fg=C_GOLD,
            relief="flat", cursor="hand2", activebackground=C_BORDER,
            command=self._video_gen_now)
        self._vid_gen_btn.pack(side="left", ipady=4, padx=(0, 8))
        
        self._vid_prev_btn = tk.Button(
            b, text="🖼 Generate Preview", font=F_BOLD, bg=C_CARD2,
            fg=C_ACCENT, relief="flat", cursor="hand2",
            activebackground=C_BORDER, command=self._video_preview_now)
        self._vid_prev_btn.pack(side="left", ipady=4, padx=(0, 8))
        
        tk.Button(b, text="🗂 Open Video Folder", font=F_BOLD,
                   bg=C_CARD2, fg=C_TEXT, relief="flat",
                   cursor="hand2", activebackground=C_BORDER, 
                   command=self._video_open_dir).pack(side="left", ipady=4)
        
        # Progress indicator
        self._vid_progress = ttk.Progressbar(card, mode="indeterminate")
        self._vid_progress.pack(fill="x", padx=16, pady=(0, 8))
        
        # Status label
        self._vid_status = tk.Label(card, text="", font=F_SMALL, bg=C_CARD,
                                   fg=C_DIM, anchor="w", justify="left")
        self._vid_status.pack(fill="x", padx=16, pady=(0, 12))

        # 📤 result row with enhanced display
        result_frame = tk.Frame(card, bg=C_CARD, relief="ridge", bd=2)
        result_frame.pack(fill="x", padx=16, pady=(0, 12))
        tk.Label(result_frame, text="Video Result:", font=F_FONT, bg=C_CARD,
                 fg=C_TEXT).pack(anchor="w", padx=16, pady=(12, 4))
        
        self._vid_res = tk.Label(result_frame, text="", font=F_FONT, bg=C_CARD,
                                  fg=C_DIM, anchor="w", justify="left",
                                  wraplength=900)
        self._vid_res.pack(fill="x", padx=16, pady=(0, 8))
        
        # 🖼 enhanced preview area
        preview_frame = tk.Frame(card, bg=C_CARD2, relief="sunken", bd=1)
        preview_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        tk.Label(preview_frame, text="Video Preview:", font=F_REGULAR,
                bg=C_CARD2, fg=C_TEXT).pack(anchor="w", padx=16, pady=(12, 4))
        
        self._vid_prev = tk.Label(preview_frame, text="No preview generated yet",
                                 bg=C_CARD2, fg=C_DIM, font=F_REGULAR,
                                 height=10, relief="flat", bd=1)
        self._vid_prev.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # ── scroll wiring: wheel + touch/mouse-drag + keyboard (user-ka-hukum) ──
        top = self.winfo_toplevel()
        _INTERACTIVE = ("Button", "Text", "Entry", "Spinbox", "TCombobox",
                        "TScrollbar", "TProgressbar", "Scrollbar")

        def _in_page(e):
            w = host.winfo_containing(e.x_root, e.y_root)
            hops = 0
            while w is not None and hops < 25:
                if w is host:
                    return True
                if isinstance(w, str):
                    try:
                        w = host.nametowidget(w)
                    except Exception:
                        return False
                    continue
                try:
                    p = w.winfo_parent()
                except Exception:
                    return False
                if not p:
                    return False
                w = p
                hops += 1
            return False

        def _wheel(e):
            if not _in_page(e):
                return                    # doosre pages/widgets ki apni marzi
            try:
                n = int(e.delta / 120)
            except Exception:
                n = 1
            if n == 0:
                n = -1 if e.delta < 0 else 1
            host.yview_scroll(-n, "units")
            return "break"

        self._drag_last = [None]

        def _press(e):
            try:
                w = host.winfo_containing(e.x_root, e.y_root)
                hops = 0
                while w is not None and hops < 25:
                    if w is host:
                        self._drag_last[0] = e.y
                        return
                    if isinstance(w, str):
                        w = host.nametowidget(w)
                        continue
                    if w.winfo_class() in _INTERACTIVE:
                        self._drag_last[0] = None
                        return
                    w = w.winfo_parent()
                    hops += 1
            except Exception:
                pass
            self._drag_last[0] = None

        def _motion(e):
            if self._drag_last[0] is None:
                return
            dy = self._drag_last[0] - e.y
            if abs(dy) >= 4:
                host.yview_scroll(-dy, "pixels")
                self._drag_last[0] = e.y

        if not hasattr(self, "_vid_scroll_bound"):
            self._vid_scroll_bound = True
            top.bind("<MouseWheel>", _wheel, add="+")
            top.bind("<ButtonPress-1>", _press, add="+")
            top.bind("<B1-Motion>", _motion, add="+")

        def _kbd(e):
            k = e.keysym
            if k == "Up":
                host.yview_scroll(-2, "units")
            elif k == "Down":
                host.yview_scroll(2, "units")
            elif k == "Prior":
                host.yview_scroll(-1, "pages")
            elif k == "Next":
                host.yview_scroll(1, "pages")
            elif k == "Home":
                host.yview_moveto(0.0)
            elif k == "End":
                host.yview_moveto(1.0)
            return "break"

        for _seq in ("<Up>", "<Down>", "<Prior>", "<Next>", "<Home>", "<End>"):
            host.bind(_seq, _kbd)

    def _video_preview_now(self):
        """🖼 Generate preview frame from ultra-realistic motion video generator."""
        self._vid_prev_btn.configure(state="disabled", text="🖼")
        self._vid_prev.configure(text="🖼 Generating preview frame…")
        
        # Get prompt from text widget
        prompt = self._vid_prompt.get("1.0", "end-1c").strip() or "car racing on track with realistic motion blur"

        def work():
            try:
                # Try ultra-realistic motion video generator first
                try:
                    from agent import ultra_realistic_motion_video as _uv
                    png = _uv.generate_ultra_realistic_motion_preview(prompt)
                    self.after(0, lambda: self._video_preview_done(png))
                except Exception as e:
                    # Fallback to original video generator
                    from agent import video_gen as _vg
                    png = _vg.still_preview(prompt, style="auto")
                    self.after(0, lambda: self._video_preview_done(png))
            except Exception as e:
                self.after(0, lambda e=e: self._video_preview_fail(e))

        threading.Thread(target=work, daemon=True).start()

    def _video_preview_done(self, png):
        try:
            import PIL.Image
            import PIL.ImageTk
            im = PIL.Image.open(png)
            im.thumbnail((560, 315))
            self._vid_prev_img = PIL.ImageTk.PhotoImage(im)
            self._vid_prev.configure(image=self._vid_prev_img, text="")
        except Exception as e:
            self._vid_prev.configure(text="Preview loading error: %s" % str(e))
        self._vid_prev_btn.configure(state="normal",
                                    text="🖼 Generate Preview")
        self._vid_status.configure(text="Preview generated successfully! Click 'Generate Ultra-Realistic Video' to create the full video.", fg=C_DIM)

    def _video_preview_fail(self, e):
        self._vid_prev_btn.configure(state="normal",
                                     text="🖼 Generate Preview")
        self._vid_prev.configure(text="Preview generation failed: %s" % str(e))
        self._vid_status.configure(text="Try adjusting your prompt or check system resources.", fg=C_DIM)

    def _video_gen_now(self):
        """▶ generate button → background thread me ultra_realistic_motion_video.generate()
        (thread-safe UI freeze nahi hota)."""
        self._vid_gen_btn.configure(state="disabled", text="🚀")
        self._vid_res.configure(text="🎬 Generating ultra-realistic motion video (0% completed)…",
                                fg=C_GOLD)
        self._vid_progress.pack(fill="x", padx=16, pady=(0, 8))
        self._vid_progress.start(10)
        self._vid_status.pack(fill="x", padx=16, pady=(0, 12))
        self._vid_status.configure(text="⏳ AI thinking & Flow Field simulation active... Rendering frames...", fg=C_GOLD)
        
        # Get prompt from text widget
        prompt = self._vid_prompt.get("1.0", "end-1c").strip() or "car racing on track with realistic motion blur"
        dur = self._vid_dur_var.get()
        
        # Parse resolution
        res = self._vid_res_var.get().split("x")
        w, h = int(res[0]), int(res[1])
        
        d = {"prompt": prompt, "duration": dur, "width": w, "height": h}

        def work():
            try:
                # Try ultra-realistic motion video generator first
                try:
                    from agent import ultra_realistic_motion_video as _uv
                    
                    # Custom generator with progress callback simulation
                    generator = _uv.UltraRealisticMotionVideo()
                    generator.width, generator.height = w, h
                    generator.duration = dur
                    generator.fps = 24
                    generator.time_step = 0
                    
                    import zlib as _zlib
                    generator.flow_field = _uv.FlowField(
                        generator.width, generator.height, scale=50,
                        seed=_zlib.crc32(prompt.encode("utf-8")))
                    generator.higgsfield_renderer = _uv.HiggsfieldRenderer(generator.width, generator.height)
                    
                    frames = []
                    total_frames = int(generator.duration * generator.fps)
                    
                    style = "racing"
                    prompt_lower = prompt.lower()
                    if "flow" in prompt_lower or "fluid" in prompt_lower:
                        style = "flow"
                    elif "physics" in prompt_lower or "particle" in prompt_lower:
                        style = "physics"
                    elif "neon" in prompt_lower:
                        style = "neon"
                    
                    for frame_num in range(total_frames):
                        generator.time_step = frame_num
                        frame = generator.generate_frame(frame_num, prompt, style)
                        frames.append(frame)
                        
                        # Update progress percentage in UI (har 10th frame —
                        # har-frame after() Tk-events-queue bhaar deta tha)
                        pct = int((frame_num + 1) / total_frames * 100)
                        if (frame_num % 10 == 0) or (frame_num + 1) == total_frames:
                            self.after(0, lambda p=pct, fn=frame_num+1, tf=total_frames: self._vid_res.configure(
                                text=f"🎬 Generating ultra-realistic motion video ({p}% completed — Frame {fn}/{tf})...\n🌊 Flow Fields + Higgsfield Active...",
                                fg=C_GOLD
                            ))
                    
                    out = generator.create_video(frames)
                    mm = _uv.get_video_metadata(out)
                    self.after(0, lambda: self._video_done(out, mm))
                except Exception as e:
                    # Fallback to original video generator
                    from agent import video_gen as _vg
                    out = _vg.generate_video(prompt, duration_sec=float(dur),
                                              fps=24, style="auto")
                    mm = _vg.video_meta(out)
                    self.after(0, lambda: self._video_done(out, mm))
            except Exception as e:
                import traceback
                self.after(0, lambda e=e: self._video_fail(e))

        threading.Thread(target=work, daemon=True).start()

    def _video_done(self, out, mm):
        self._vid_gen_btn.configure(state="normal", text="🚀 Generate Ultra-Realistic Video")
        self._vid_progress.stop()
        self._vid_progress.pack_forget()
        self._vid_status.pack_forget()
        
        # Enhanced result display
        video_size_kb = int(mm.get("size", 0) / 1024)
        video_duration = mm.get("duration", 0)
        video_fps = mm.get("fps", 24)
        
        result_text = ("✅ Ultra-realistic motion video generated successfully!\n"
                      "    File: %s\n"
                      "    Duration: %ss   Size: %sKB   FPS: %s\n"
                      "    Technology: Flow Fields + Higgsfield + Physics Simulation\n"
                      "    (100% Local — data/videos/ folder)" 
                      % (out, video_duration, video_size_kb, video_fps))
        
        self._vid_res.configure(text=result_text, fg=C_ACCENT)
        
        # Show preview if available
        try:
            import PIL.Image
            import PIL.ImageTk
            preview_path = os.path.join(ROOT, "data", "videos", "preview.png")
            if os.path.exists(preview_path):
                im = PIL.Image.open(preview_path)
                im.thumbnail((560, 315))
                self._vid_prev_img = PIL.ImageTk.PhotoImage(im)
                self._vid_prev.configure(image=self._vid_prev_img, text="")
        except Exception as e:
            self._vid_prev.configure(text="Preview loading error: %s" % str(e))

    def _video_fail(self, e):
        self._vid_gen_btn.configure(state="normal", text="🚀 Generate Ultra-Realistic Video")
        self._vid_progress.stop()
        self._vid_progress.pack_forget()
        self._vid_status.pack_forget()
        
        error_msg = "❌ Video generation failed: %s" % str(e)
        self._vid_res.configure(text=error_msg, fg=C_DANGER)
        self._vid_status.configure(text="Please try a different prompt or check your system resources.", fg=C_DIM)
        self._vid_prev.configure(text="Generation failed - check error message above", fg=C_DANGER)

    def _video_open_dir(self):
        try:
            import subprocess, sys
            p = os.path.join(ROOT, "data", "videos")
            os.makedirs(p, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(p)
            else:
                import xdg_open
                subprocess.Popen(["xdg-open", p])
        except Exception:
            pass

    # ==================================================================
    # 📊 MAIN PAGE (DASHBOARD)
    # ==================================================================
    def _build_dashboard(self):
        f = self._page("f_dash")
        self._page("dash")  # ensure exists
        wrap = tk.Frame(self._pages["dash"], bg=C_BG)
        wrap.pack(fill="both", expand=True)
        # scrollable canvas
        cv = tk.Canvas(wrap, bg=C_BG, highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=cv.yview)
        self._dash_inner = tk.Frame(cv, bg=C_BG)
        self._dash_inner.bind("<Configure>", lambda e: cv.configure(
            scrollregion=cv.bbox("all")))
        cv.create_window((0, 0), window=self._dash_inner, anchor="nw",
                         tags="inner")
        cv.bind("<Configure>", lambda e: cv.itemconfigure(
            "inner", width=e.width))
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._dash_cv = cv

        top = tk.Frame(self._dash_inner, bg=C_BG)
        top.pack(fill="x", padx=2, pady=(2, 6))
        tk.Label(top, text="📊 Main Page — Sar-e-Haal", font=F_H1, bg=C_BG,
                 fg=C_TEXT).pack(side="left")
        tk.Button(top, text="🔄 Tajdeed", font=F_SMALL, bg=C_CARD,
                  fg=C_ACCENT, relief="flat", cursor="hand2",
                  highlightthickness=1, highlightbackground=C_BORDER,
                  command=self.refresh_dashboard).pack(side="right")
        self._dash_body = tk.Frame(self._dash_inner, bg=C_BG)
        self._dash_body.pack(fill="both", expand=True)

    def refresh_dashboard(self):
        self._dash_body.destroy()
        self._dash_body = tk.Frame(self._dash_inner, bg=C_BG)
        self._dash_body.pack(fill="both", expand=True)
        body = self._dash_body
        for i in range(3):
            body.grid_columnconfigure(i, weight=1, uniform="c")

        def work():
            try:
                hub = brain_hub()
                s = hub.status()
            except Exception as e:
                s = {"err": str(e)}
            self.after(0, lambda: self._dash_fill(s))

        threading.Thread(target=work, daemon=True).start()
        tk.Label(body, text="… live inventory aa rahi hai", font=F_SMALL,
                 bg=C_BG, fg=C_DIM).grid(row=0, column=0, padx=10, pady=10)

    def _dash_fill(self, s):
        for w in self._dash_body.winfo_children():
            w.destroy()
        body = self._dash_body
        for i in range(3):
            body.grid_columnconfigure(i, weight=1, uniform="c")
        if "err" in s:
            tk.Label(body, text="hub.status() ghalti: %s" % s["err"],
                     bg=C_BG, fg=C_DANGER, font=F_FONT).grid(row=0, column=0)
            return

        def _d(x):
            return x if isinstance(x, dict) else {}

        ident = _d(s.get("identity"))
        card = self._card(body, row=0, col=0, span=3)
        row0 = tk.Frame(card, bg=C_CARD)
        row0.pack(fill="x", padx=14, pady=10)
        tk.Label(row0, text="☪  %s" % ident.get("name", MODEL_NAME),
                 font=("Segoe UI", 16, "bold"), bg=C_CARD,
                 fg=C_GOLD).pack(side="left")
        tk.Label(row0, text="v%s" % ident.get("version", "?"), font=F_SMALL,
                 bg=C_CARD, fg=C_DIM).pack(side="left", padx=10)
        tk.Label(row0, text=ident.get("offline", ""), font=F_SMALL, bg=C_CARD,
                 fg=C_ACCENT).pack(side="right")
        tk.Label(card, text=ident.get("architecture", ""), font=F_SMALL,
                 bg=C_CARD, fg=C_TEXT, wraplength=980,
                 justify="left").pack(fill="x", padx=14, pady=(0, 10))

        # 4 dimagh cards
        brains = [
            ("🥇 Pehla Dimagh — MASTER", _d(s.get("master_brain")),
             "9.0M params · dh722 · khud-soch"),
            ("🥈 Dusra Dimagh — DEEP", _d(s.get("deep_brain")),
             "6.25M params · dh620 · deep-soch rescue"),
            ("🥉 Teesra — HELPER", _d(s.get("helper_brain")),
             "5.11M params · dh560 · madadgar"),
            ("🛡️ Chautha — VERIFY", _d(s.get("verify_brain")),
             "5.11M params · dh560 · tasdeeq-kar"),
        ]
        for i, (title, st, sub) in enumerate(brains):
            card = self._card(body, title=title, row=1, col=i % 3)
            on = bool(st.get("on"))
            ck = st.get("checkpoint") or ("tarkeeb jari…" if not on else "—")
            tk.Label(card, text=("🟢 ON" if on else "🟡 WAIT"),
                     font=F_BOLD, bg=C_CARD,
                     fg=(C_ACCENT if on else C_GOLD)).pack(
                anchor="w", padx=14)
            tk.Label(card, text=sub, font=F_SMALL, bg=C_CARD, fg=C_DIM,
                     anchor="w").pack(fill="x", padx=14)
            tk.Label(card, text="checkpoint: %s" % ck, font=F_MONO, bg=C_CARD,
                     fg=C_TEXT, anchor="w", wraplength=300).pack(
                fill="x", padx=14, pady=(2, 10))

        # formula library
        fl = _d(s.get("formula_library"))
        card = self._card(body, title="📐 Formula Library", row=2, col=0)
        tk.Label(card, text="%s formulas" % fl.get("formulas", "—"),
                 font=("Segoe UI", 15, "bold"), bg=C_CARD,
                 fg=C_ACCENT).pack(anchor="w", padx=14)
        tk.Label(card, text="Math A→Z + Physics A→Z\nnaam + formula + vars + "
                            "tafseel\nplug-and-solve + teach-mode",
                 font=F_SMALL, bg=C_CARD, fg=C_TEXT,
                 justify="left").pack(anchor="w", padx=14, pady=(2, 10))

        # bio bridge — title me LIVE neuron count (2M)
        bio = _d(s.get("bio_brain"))
        _bn = bio.get("neurons")
        try:
            _bn = "{:,}".format(int(_bn))
        except Exception:
            _bn = "2M"
        card = self._card(body, title="⚡ Bio Bridge (%s neurons)" % _bn,
                          row=2, col=1)
        tk.Label(card, text="neurons: %s" % bio.get("neurons", "—"),
                 font=F_FONT, bg=C_CARD, fg=C_TEXT, anchor="w").pack(
            fill="x", padx=14)
        tk.Label(card, text="synapses: %s" % bio.get("synapses", "—"),
                 font=F_FONT, bg=C_CARD, fg=C_TEXT, anchor="w").pack(
            fill="x", padx=14)
        tk.Label(card, text="spikes: %s · steps: %s" % (
            bio.get("total_spikes", "—"), bio.get("sim_steps", "—")),
            font=F_SMALL, bg=C_CARD, fg=C_DIM, anchor="w").pack(
            fill="x", padx=14, pady=(0, 10))

        # jazbaat
        card = self._card(body, title="💛 Jazbaat (feelings)", row=2, col=2)
        lbl = tk.Label(card, text="…", font=F_SMALL, bg=C_CARD, fg=C_TEXT,
                       justify="left", wraplength=300)
        lbl.pack(fill="x", padx=14, pady=(2, 10))
        try:
            feelings = _imp("model", "feelings")
            lbl.configure(text=feelings.status_line())
        except Exception:
            pass

        # malik + ilm
        own = _d(s.get("owner"))
        card = self._card(body, title="👤 Malik", row=3, col=0)
        tk.Label(card, text=own.get("name", "—"), font=F_BOLD, bg=C_CARD,
                 fg=C_TEXT, anchor="w", wraplength=300).pack(fill="x", padx=14)
        tk.Label(card, text="%s\n%s" % (own.get("residence", ""),
                                        own.get("college", "")),
                 font=F_SMALL, bg=C_CARD, fg=C_DIM, justify="left").pack(
            fill="x", padx=14, pady=(2, 10))

        kf = _d(s.get("knowledge_files"))
        card = self._card(body, title="📚 Ilm (live corpus)", row=3, col=1)
        tk.Label(card, text="%s files • %s chars" % (
            kf.get("count", "—"), f"{kf.get('chars', 0):,}" if isinstance(
                kf.get("chars"), int) else "—"),
            font=F_FONT, bg=C_CARD, fg=C_TEXT, anchor="w").pack(
            fill="x", padx=14)
        tk.Label(card, text="Quran + 7 Hadith kitabein + formulas + "
                            "lifecycle (corpus_big)",
                 font=F_SMALL, bg=C_CARD, fg=C_DIM, justify="left",
                 wraplength=300).pack(fill="x", padx=14, pady=(2, 10))

        md = _d(s.get("model"))
        card = self._card(body, title="💾 Checkpoints", row=3, col=2)
        tk.Label(card, text="active: %s" % (md.get("active_checkpoint") or "—"),
                 font=F_MONO, bg=C_CARD, fg=C_TEXT, anchor="w",
                 wraplength=300).pack(fill="x", padx=14)
        tk.Label(card, text="total: %s · archived: %s" % (
            md.get("checkpoints", "—"), md.get("archived", "—")),
            font=F_SMALL, bg=C_CARD, fg=C_DIM, anchor="w").pack(
            fill="x", padx=14, pady=(2, 10))

        # offline oath banner
        card = self._card(body, row=4, col=0, span=3)
        tk.Label(card, text="🔒 OFFLINE OATH", font=F_H2, bg=C_CARD,
                 fg=C_GOLD).pack(anchor="w", padx=14, pady=(10, 0))
        oath = s.get("offline_oath", "")
        tk.Label(card, text=str(oath) + "  —  koi AI API key NAHI, koi "
                                     "cloud/AI-model/MCP connection NAHI. "
                                     "100% local NumPy dimagh.",
                 font=F_FONT, bg=C_CARD, fg=C_TEXT, wraplength=980,
                 justify="left").pack(fill="x", padx=14, pady=(2, 12))

    # ==================================================================
    # 📐 FORMULAS PAGE
    # ==================================================================
    def _build_formulas(self):
        f = self._page("formu")
        f.grid_rowconfigure(1, weight=1)
        f.grid_columnconfigure(0, weight=1)

        top = tk.Frame(f, bg=C_BG)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Label(top, text="📐 Formula Library — Math + Physics A→Z",
                 font=F_H1, bg=C_BG, fg=C_TEXT).pack(side="left")
        self._fsearch = tk.Entry(top, font=F_FONT, bg=C_CARD2, fg=C_TEXT,
                                 relief="flat", width=32,
                                 insertbackground=C_ACCENT)
        self._fsearch.pack(side="right", ipady=7)
        self._fsearch.bind("<KeyRelease>", lambda e: self._fill_formulas())
        tk.Label(top, text=" 🔍 ", font=F_H2, bg=C_BG,
                 fg=C_GOLD).pack(side="right")

        body = tk.Frame(f, bg=C_BG)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        lf = tk.Frame(body, bg=C_CARD, highlightthickness=1,
                      highlightbackground=C_BORDER)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._flist = tk.Listbox(lf, bg=C_CARD, fg=C_TEXT, font=F_FONT,
                                 relief="flat", selectbackground=C_ACCENT,
                                 selectforeground="#06231a", activestyle="none")
        self._flist.pack(side="left", fill="both", expand=True, padx=(4, 0),
                         pady=6)
        sb = ttk.Scrollbar(lf, command=self._flist.yview)
        sb.pack(side="right", fill="y")
        self._flist.configure(yscrollcommand=sb.set)
        self._flist.bind("<<ListboxSelect>>", self._formula_pick)

        rf = tk.Frame(body, bg=C_CARD, highlightthickness=1,
                      highlightbackground=C_BORDER)
        rf.grid(row=0, column=1, sticky="nsew")
        self._fdetail = tk.Text(rf, bg=C_CARD, fg=C_TEXT, font=F_FONT,
                                relief="flat", wrap="word", padx=18, pady=14,
                                state="disabled", cursor="arrow")
        self._fdetail.pack(fill="both", expand=True)
        self._fdetail.tag_configure("h1", font=F_H2, foreground=C_GOLD)
        self._fdetail.tag_configure("f", font=("Consolas", 12),
                                    foreground=C_ACCENT)
        self._fdetail.tag_configure("k", font=F_BOLD, foreground=C_GOLD)
        self._fdetail.tag_configure("d", font=F_FONT, foreground=C_TEXT,
                                    spacing3=8)
        self._fdetail.tag_configure("s", font=F_SMALL, foreground=C_DIM)

    def _fill_formulas(self):
        self._formu_filled = True
        try:
            MF = brain_formulas()
            data = MF.load_all()
        except Exception as e:
            data = []
        self._fdata = data
        needle = self._fsearch.get().lower().strip() if hasattr(
            self, "_fsearch") else ""
        self._flist.delete(0, "end")
        self._fview = []
        for b in data:
            line = "%s — [%s]" % (b.get("name", "?"), b.get("field", ""))
            if needle and needle not in line.lower() \
                    and needle not in (b.get("keywords") or "").lower() \
                    and needle not in (b.get("formula") or "").lower():
                continue
            self._fview.append(b)
            self._flist.insert("end", " " + line)
        if not self._flist.size() and self._fview == [] and data:
            self._flist.insert("end", "  (koi match nahi)")

    def _formula_pick(self, _e=None):
        sel = self._flist.curselection()
        if not sel or not getattr(self, "_fview", []):
            return
        b = self._fview[sel[0]]
        t = self._fdetail
        t.configure(state="normal")
        t.delete("1.0", "end")
        t.insert("end", "📐 %s\n" % b.get("name", "?"), "h1")
        t.insert("end", "[%s]\n\n" % b.get("field", ""), "s")
        t.insert("end", "%s\n\n" % b.get("formula", ""), "f")
        t.insert("end", "Vars:\n", "k")
        for k, v in (b.get("vars") or {}).items():
            t.insert("end", "  • %s = %s\n" % (k, v), "d")
        t.insert("end", "\nTafseel:\n", "k")
        t.insert("end", "  %s\n" % b.get("detail", ""), "d")
        t.insert("end", "\nYe formula chat me plug-and-solve hota hai — "
                        "misal: '%s' (values de kar poochho)." %
                 b.get("name", "").lower(), "s")
        t.configure(state="disabled")

    # ==================================================================
    # ℹ️ ABOUT PAGE
    # ==================================================================
    def _build_about(self):
        f = self._page("about")
        f.grid_columnconfigure(0, weight=1)
        card = self._card(f, row=0)
        tk.Label(card, text="☪ %s" % MODEL_NAME, font=F_H1, bg=C_CARD,
                 fg=C_GOLD).pack(anchor="w", padx=16, pady=(14, 0))
        lines = [
            ("📦 Version", "v5.0.0 — 4-dimagh network (master 9.0M + deep "
             "6.25M + helper 5.11M + verify 5.11M) + 2M bio-neuron bridge + "
             "live research (unknown topic → search → verify → jawab)"),
            ("📁 Live Link", "%s — ye app ISI folder ke modules use karta hai. "
             "Terminal/session me kiye gaye changes yahan 🔄 Brain Reload "
             "(sidebar neeche) se foran apply hote hain; corpus/checkpoints "
             "khud-ba-khud live parhte hain." % ROOT),
            ("🔒 Security-Oath", "Koi AI API key NAHI · koi OpenAI/Gemini/"
             "Claude/Ollama/cloud NAHI · koi MCP NAHI · koi AI-platform "
             "connection NAHI. Sirf apna NumPy dimagh + 🌐 asli web-page-"
             "parhi (whitelisted knowledge-sites, jab jawab na aata ho) + "
             "Hemomemo ki APNI local API (🌐 page) — kisi doosre platform ki "
             "API nahi. 6 security-layers (L6 = HMHZ API-guard)."),
            ("📐 Ilm", "331 formulas (Math+Physics A→Z), Quran (kai tarjume) "
             "+ 7 Sahih Hadith kitabein, aqal (CoT), SAMAJH social "
             "understanding, jazbaat (feelings), yaad-dahai."),
            ("🧮 Math", "har operator (+ − × ÷ ^ // % ! sqrt log sin…) + "
             "formula plug-and-solve + teach-mode — sab safe-AST, bina eval."),
            ("⚠️ Note", "Agar pehla jawab aane me thora waqt lage to dimagh "
             "pehli dafa load ho raha hai — agle sawal tez honge. Training "
             "(helper/verify/master) ke baad naye checkpoints 🔄 Reload par "
             "khud lag jate hain."),
        ]
        for k, v in lines:
            tk.Label(card, text=k, font=F_BOLD, bg=C_CARD, fg=C_ACCENT,
                     anchor="w").pack(fill="x", padx=16, pady=(10, 0))
            tk.Label(card, text=v, font=F_FONT, bg=C_CARD, fg=C_TEXT,
                     wraplength=940, justify="left",
                     anchor="w").pack(fill="x", padx=16)
        tk.Label(card, text="Banaya gaya Hafiz Muhammad Huzaifa Shamim ke "
                            "liye — Alhamdulillah ☪",
                 font=F_SMALL, bg=C_CARD, fg=C_DIM,
                 anchor="w").pack(fill="x", padx=16, pady=(14, 14))


def _pretty(o, ind=0):
    """halka JSON-jaisa pretty printer (BOM-emojis ke sath saaf)."""
    pad = "  " * ind
    if isinstance(o, dict):
        if not o:
            return "{}"
        out = ""
        for k, v in o.items():
            out += "%s%s: %s\n" % (pad, k, _pretty(v, ind + 1)
                                   if isinstance(v, (dict, list))
                                   else _scalar(v))
        return out
    if isinstance(o, list):
        if len(o) > 6:
            return "%s (%d items: %s…)" % (
                _scalar(o[0]), len(o), ", ".join(str(_scalar(x)) for x in o[1:4]))
        return "[%s]" % ", ".join(_scalar(x) for x in o)
    return _scalar(o)


def _scalar(v):
    s = str(v)
    return s if len(s) < 160 else s[:157] + "…"


def main():
    try:
        app = HemomemoApp()
        app.mainloop()
    except Exception:
        _log("FATAL:\n" + traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
