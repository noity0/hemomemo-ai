# -*- coding: utf-8 -*-
r"""
☪ Hemomemo AI — DESKTOP APP (app/genone_app.py)
======================================================
Poora LOCAL desktop app: koi AI API key NAHI, koi AI-model/cloud/ollama/
MCP connection NAHI. Ye app seedha aapke D:\DigitalBrain folder ke live
modules se juda hai — terminal/session me jo bhi changes karo (code,
corpus, checkpoints, formulas) wo is app me 🔄 Reload se foran apply.

Run:  py -3 app\genone_app.py   (ya Desktop shortcut / .bat)
"""
import os
import re
import sys
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
C_BG      = "#0b1512"   # window background
C_PANEL   = "#101f19"   # sidebar / header
C_CARD    = "#152820"   # cards
C_CARD2   = "#1a3128"   # hover / input
C_BORDER  = "#26473a"   # card borders
C_ACCENT  = "#2fbf8f"   # emerald
C_GOLD    = "#d9b45b"   # gold
C_TEXT    = "#e9f3ee"
C_DIM     = "#8fb0a2"
C_USERBG  = "#1f5c46"   # user bubble
C_AIBG    = "#182b23"   # ai bubble
C_DANGER  = "#c05b5b"

F_FONT    = ("Segoe UI", 11)
F_SMALL   = ("Segoe UI", 9)
F_BOLD    = ("Segoe UI", 11, "bold")
F_H1      = ("Segoe UI", 17, "bold")
F_H2      = ("Segoe UI", 13, "bold")
F_MONO    = ("Consolas", 9)

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


def chat_async(prompt, on_done, think="auto", progress=None):
    """Chat worker thread — UI freeze nahi hota. Result → on_done(text, meta).
    progress(stage) — har asli marhale par UI ko bataata hai (3-soch flow)."""
    _VID_RX = re.compile(r"(?i)\b(video|film|movie|animation|clip)\b")
    _VID_CMD_RX = re.compile(r"(?i)(make|create|generate|banai|banao|benao|show|showing)\b.*\b(video|film|movie|animation|clip)\b")
    _VNUM_RX = re.compile(r"(?i)\b(\d+(?:\.\d+)?)\s*(sec|s|second|seconds|min|minute|minutes)\b")

    def _video_gen(q, out):
        """Local video engine — 5s se 15 min tak; koi AI-API nahi."""
        try:
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
        try:
            # token-dimagh pehle: token-dar-token samajh (no-API, local)
            try:
                from model.understand import default_token_chat
                txt, m = default_token_chat().respond(prompt)
                if txt and (m or {}).get("source") not in (None, ""):
                    on_done(txt, m or {})
                    return
            except Exception:
                pass
            G = brain_generate()
            txt, m = G.chat_once(prompt, meta=True, think=think,
                                 progress=progress)
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
            self._ico_path = os.path.join(d, "genone.ico")
            with open(self._ico_path, "wb") as _f:
                _f.write(ico)
            self._ppm_path = os.path.join(d, "genone.ppm")
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
                ("video", "🎬", " Video Generation")]:
            b = tk.Button(side, text="%s%s" % (icon, label), font=F_BOLD,
                           bg=C_PANEL, fg=C_DIM, activebackground=C_CARD2,
                           activeforeground=C_TEXT, relief="flat", bd=0,
                           anchor="w", padx=18, pady=10, cursor="hand2",
                           command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=10, pady=2)
            self._nav_btns[key] = b
            # 🖱️ hover: sirf jab select nahi (selected gold rehta hai)
            b.bind("<Enter>", lambda e, k=key: (
                self._nav_btns[k].configure(bg=C_CARD) if
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

    # ================================================================ #
    # 🌐 APNI LOCAL API — AUTO-START + neeche global status-bar         #
    # ================================================================ #
    def _autostart_server(self):
        """🌐 Hemomemo ki APNI local API khud ON (127.0.0.1) — app khulte hi
        browser 127.0.0.1 par 'refused' na de. Ye SIRF Hemomemo ka apna
        local darwaza hai — kisi platform/AI ki API se koi taluq NAHI."""
        def work():
            try:
                api = _imp("server", "genone_server")
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
            api = _imp("server", "genone_server")
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
    # ==================================================================
    def _build_api(self):
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
        def work():
            try:
                api = _imp("server", "genone_server")
                r = api.start() if what == "on" else api.stop()
                txt = str(r)
            except Exception as e:
                txt = "FAIL: %s" % e
            self.after(0, lambda: self._api_lbl.configure(
                text=txt, fg=C_ACCENT if "ok" in txt else C_DANGER))
            self.after(0, self.refresh_api)
        self._api_lbl.configure(text="… %s ho raha hai" % what)
        threading.Thread(target=work, daemon=True).start()

    def _api_show_key(self):
        def work():
            try:
                api = _imp("server", "genone_server")
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
            api = _imp("server", "genone_server")
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
            api = _imp("server", "genone_server")
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
                api = _imp("server", "genone_server")
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
        on = os.path.isdir(ROOT)
        self._live_lbl.configure(
            text=("🟢 LIVE • %s" % ROOT) if on else "🔴 folder nahi mila",
            fg=C_ACCENT if on else C_DANGER)

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
            _imp("server", "genone_server").stop()
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

        wrap = tk.Frame(f, bg=C_CARD, highlightthickness=1,
                        highlightbackground=C_BORDER)
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        self.chat = tk.Text(wrap, wrap="word", bg=C_AIBG, fg=C_TEXT,
                            font=F_FONT, relief="flat", padx=16, pady=14,
                            state="disabled", cursor="arrow",
                            insertbackground=C_TEXT, spacing1=4, spacing3=6)
        self.chat.grid(row=0, column=0, sticky="nsew")
        self._sb = ttk.Scrollbar(wrap, command=self.chat.yview)
        self._sb.grid(row=0, column=1, sticky="ns")
        self.chat.configure(yscrollcommand=self._chat_scroll)

        # tags: bubbles + naam-labels + chips
        self.chat.tag_configure("who_u", justify="right", foreground=C_ACCENT,
                                font=("Segoe UI", 9, "bold"), rmargin=22,
                                spacing1=10, spacing3=1)
        self.chat.tag_configure("who_a", justify="left", foreground=C_GOLD,
                                font=("Segoe UI", 9, "bold"), lmargin1=16,
                                spacing1=10, spacing3=1)
        self.chat.tag_configure("user", justify="right", background=C_USERBG,
                                foreground="#ffffff", lmargin1=180,
                                lmargin2=180, rmargin=14, font=F_FONT,
                                spacing1=2, spacing3=3)
        self.chat.tag_configure("ai", justify="left", background=C_CARD2,
                                foreground=C_TEXT, lmargin1=14, lmargin2=14,
                                rmargin=180, font=F_FONT, spacing1=2,
                                spacing3=3)
        self.chat.tag_configure("chip", justify="left", foreground=C_DIM,
                                font=F_SMALL, lmargin1=16, spacing3=12)
        self.chat.tag_configure("think", justify="left", foreground=C_GOLD,
                                font=("Segoe UI", 10, "italic"), lmargin1=16)
        self.chat.tag_configure("welcome", justify="left", foreground=C_DIM,
                                font=F_SMALL, lmargin1=6, spacing3=14)
        # 💻 code-block tags (Hemomemo Coding-AI ke ```fences pyare dikhte hain)
        self.chat.tag_configure("code_hdr", justify="left", foreground="#06231a",
                                background=C_GOLD, font=("Segoe UI", 8, "bold"),
                                lmargin1=14, spacing1=8, spacing3=0)
        self.chat.tag_configure("code_blk", justify="left", wrap="char",
                                foreground="#d7e6dd", background="#0b1f16",
                                lmargin1=14, lmargin2=14, rmargin=180,
                                font=("Consolas", 10), spacing1=0, spacing3=10)

        # ⬇ floating jump-button (jab upar scroll kar lo)
        self._jump = tk.Button(wrap, text="⬇ sab se neeche", font=F_SMALL,
                               bg=C_GOLD, fg="#06231a", relief="flat",
                               activebackground="#e8c774", cursor="hand2",
                               command=self._chat_bottom,
                               highlightthickness=0, bd=0)
        self._jump.place(relx=1.0, rely=1.0, x=-16, y=-14, anchor="se")
        self._jump.place_forget()

        self._welcome()

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

        # input row
        inp = tk.Frame(f, bg=C_BG)
        inp.grid(row=2, column=0, sticky="ew")
        inp.grid_columnconfigure(0, weight=1)
        self._ph = "Apna sawal likhein… (Roman Urdu / English)"
        self.entry = tk.Entry(inp, font=F_FONT, bg=C_CARD2, fg=C_DIM,
                              relief="flat", insertbackground=C_ACCENT)
        self.entry.grid(row=0, column=0, sticky="ew", ipady=9, padx=(0, 8))
        self.entry.insert(0, self._ph)
        self.entry.bind("<FocusIn>", self._ph_clear)
        self.entry.bind("<FocusOut>", self._ph_set)
        self.entry.bind("<Return>", lambda e: self._send())
        self.entry.bind("<Escape>", self._esc_clear)
        self.entry.focus_set()
        self.send_btn = tk.Button(inp, text="Bhejo ➤", font=F_BOLD,
                                  bg=C_ACCENT, fg="#06231a", relief="flat",
                                  activebackground="#3ad8a5", cursor="hand2",
                                  command=self._send, width=12)
        self.send_btn.grid(row=0, column=1, ipady=7)
        self._hover(self.send_btn, C_ACCENT, "#3ad8a5")

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
        self.chat.see("end")

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
            self.chat.configure(state="normal")
            self.chat.delete("1.0", "end")
            for _e in self._hist:
                self._bubble(_e.get("text") or "", _e.get("who") or "ai")
            self.chat.configure(state="disabled")
            self.chat.see("end")
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
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self._hist_clear()
        self._welcome()

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

    def _welcome(self):
        self.chat.configure(state="normal")
        self.chat.insert("end", " ☪  %s me khush-amdeed!\n" % MODEL_NAME,
                         "welcome")
        self.chat.insert("end",
                         " Ye app aapke D:\\DigitalBrain se SEEDHA juda hai — koi API key "
                         "nahi, koi AI/cloud/MCP connection nahi. Sab kuch local NumPy "
                         "dimagh (4 brains), 331 formulas, Quran/Hadith ilm, aqal aur "
                         "jazbaat ke sath. Neeche likh kar bhejo — terminal me kiye "
                         "gay changes 🔄 Brain Reload se yahan live lagte hain.\n\n",
                         "welcome")
        self.chat.configure(state="disabled")

    def _mk_copy_btn(self, val, label="📋 copy"):
        """📋 chat-ke-andar chhota copy-button (Text-widget me window_create).
        val = jo clipboard jana hai; label = button par likha."""
        b = tk.Button(self.chat, text=label, font=("Segoe UI", 8),
                      bg="#12291d", fg=C_GOLD, relief="flat", bd=0,
                      highlightthickness=0, activebackground=C_GOLD,
                      activeforeground="#06231a", cursor="hand2")
        b.configure(command=lambda: self._btn_copy(b, val, label))
        return b

    def _btn_copy(self, btn, val, label):
        """📋 chat-copy-buttons ka clipboard-helper (feedback button-par hi)."""
        try:
            self.clipboard_clear()
            self.clipboard_append(val or "")
            btn.configure(text="✅ copy ho gaya")
            self.after(1200, lambda: btn.configure(text=label))
        except Exception:
            pass

    def _bubble(self, text, who):
        stick = self._near_bottom()
        self.chat.configure(state="normal")
        if who == "user":
            self.chat.insert("end", "  ✦ Aap\n", "who_u")
            self.chat.insert("end", " %s \n" % text.strip(), "user")
        else:
            self.chat.insert("end", "  ✦ Hemomemo AI\n", "who_a")
            # 💻 CODE-BLOCK SYSTEM: ```lang ... ``` fences → pyare code-blocks
            #    (monospace + dark card + gold language-label); baaki aam jawab.
            _parts = re.split(r"```([A-Za-z0-9+#_-]*)[ \t]*\r?\n(.*?)```",
                              (text or "").strip(), flags=re.S)
            if len(_parts) == 1:
                self.chat.insert("end", " %s \n" % text.strip(), "ai")
            else:
                for _i, _seg in enumerate(_parts):
                    _m = _i % 3
                    if _m == 0:                       # aam text
                        if _seg.strip():
                            self.chat.insert("end",
                                             " %s \n" % _seg.strip(), "ai")
                    elif _m == 1:                     # zaban (label)
                        _lang = (_seg or "").strip() or "code"
                        self.chat.insert("end",
                                         " ─── 💻 %s ───\n" % _lang,
                                         "code_hdr")
                    else:                             # asli code + copy-code
                        _code = _seg.rstrip("\n")
                        self.chat.insert("end", "\n" + _code + "\n",
                                         "code_blk")
                        self.chat.insert("end", " ")
                        self.chat.window_create("end", window=self._mk_copy_btn(
                            _code, "📋 copy code"))
                        self.chat.insert("end", "\n", "ai")
            # 📋 copy-whole-message button (har AI-jawab ke neeche)
            self.chat.insert("end", " ")
            self.chat.window_create("end", window=self._mk_copy_btn(
                (text or "").strip(), "📋 copy message"))
            self.chat.insert("end", "\n", "ai")
        if stick:
            self.chat.see("end")
        self.chat.configure(state="disabled")

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
            stick = self._near_bottom()
            self.chat.configure(state="normal")
            self.chat.insert("end", "   " + "  •  ".join(bits) + "\n", "chip")
            if stick:
                self.chat.see("end")
            self.chat.configure(state="disabled")
        except Exception:
            pass

    def _think_start(self):
        self.chat.configure(state="normal")
        self._think_at = self.chat.index("end-1c")
        self._think_n = 0
        self._think_stage_txt = ""
        self._think_step()
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _think_step(self):
        self._think_n += 1
        dots = "٫" * (1 + (self._think_n % 3))
        stage = getattr(self, "_think_stage_txt", "") or \
            self._think_stages[self._think_stage_i % len(self._think_stages)]
        self._think_stage_i = getattr(self, "_think_stage_i", 0) + 1
        try:
            self.chat.delete(self._think_at, "%s lineend +1char" % self._think_at)
            self.chat.insert(self._think_at, " %s%s "
                             "(local dimagh — no API)" % (stage, dots), "think")
            if self._near_bottom():
                self.chat.see("end")
        except Exception:
            return
        self._think_id = self.after(450, self._think_step)

    def _think_stage(self, stage):
        """🌐 3-SOCH FLOW: har asli marhale par sawal-ke-neeche animation badle
        (soch-1 → ilm → soch-2 → research → soch-3 → seekh). Thread-safe."""
        self._think_stage_txt = stage
        try:
            self.chat.configure(state="normal")
            self.chat.delete(self._think_at, "%s lineend +1char" % self._think_at)
            dots = "٫" * (1 + (self._think_n % 3))
            self.chat.insert(self._think_at, " %s%s (local dimagh — no API)"
                             % (stage, dots), "think")
            if self._near_bottom():
                self.chat.see("end")
            self.chat.configure(state="disabled")
        except Exception:
            pass

    def _think_stop(self):
        if self._think_id:
            try:
                self.after_cancel(self._think_id)
            except Exception:
                pass
            self._think_id = None
        try:
            self.chat.configure(state="normal")
            self.chat.delete(self._think_at, "%s lineend +1char" % self._think_at)
            self.chat.configure(state="disabled")
        except Exception:
            pass

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

        chat_async(q, done, think=self._think_mode, progress=prog)

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
        """🎬 HEMOMO VIDEO-GENERATION TAB (local engine — 100% Hemomemo AI,
        koi external AI-API / UE5 / Higgsfield nahi. ffmpeg + PIL local)."""
        f = self._page("video")
        f.grid_columnconfigure(0, weight=1)

        card = self._card(f, row=0)
        tk.Label(card, text="🎬 Hemomemo AI — Text → Video (100% Local)",
                 font=F_H1, bg=C_CARD, fg=C_GOLD).pack(
            anchor="w", padx=16, pady=(14, 2))
        tk.Label(card, text="Prompt → local script → procedural frames → "
                 "ffmpeg → mp4. 5s se 15 min tak (15 min = 900s). "
                 "No AI-API · No Cloud · No MCP · koi platform-key nahi.",
                 font=F_FONT, bg=C_CARD, fg=C_TEXT, wraplength=900,
                 justify="left", anchor="w").pack(fill="x", padx=16, pady=(2, 10))

        # 📝 prompt row
        self._vid_prompt_var = tk.StringVar(value="cinematic hero running through neon city rain")
        tk.Entry(card, textvariable=self._vid_prompt_var, font=F_FONT,
                 bg=C_CARD2, fg=C_TEXT, relief="flat",
                 insertbackground=C_ACCENT).pack(
            fill="x", padx=16, pady=6, ipady=9)

        # ⚙️ controls row: duration / fps / style
        self._vid_dur_var = tk.IntVar(value=10)
        self._vid_fps_var = tk.IntVar(value=24)
        self._vid_style_var = tk.StringVar(value="auto")
        c = tk.Frame(card, bg=C_CARD); c.pack(fill="x", padx=16, pady=4)
        tk.Label(c, text="⏱ duration (sec):", font=F_FONT, bg=C_CARD,
                 fg=C_TEXT).pack(side="left")
        tk.Spinbox(c, from_=5, to=900, increment=5, font=F_FONT,
                   bg=C_CARD2, fg=C_TEXT, relief="flat",
                   textvariable=self._vid_dur_var, width=6).pack(
            side="left", padx=(6, 16))
        tk.Label(c, text="🎞 fps:", font=F_FONT, bg=C_CARD,
                 fg=C_TEXT).pack(side="left")
        tk.Spinbox(c, from_=8, to=60, increment=4, font=F_FONT,
                   bg=C_CARD2, fg=C_TEXT, relief="flat",
                   textvariable=self._vid_fps_var, width=4).pack(
            side="left", padx=(6, 16))
        for st in ("auto", "ocean", "desert", "neon", "space", "rain"):
            pass
        tk.Label(c, text="🎨 style:", font=F_FONT, bg=C_CARD,
                 fg=C_TEXT).pack(side="left")
        style_box = tk.Frame(c, bg=C_CARD); style_box.pack(side="left", padx=(6, 0))
        for st in ("auto", "ocean", "desert", "neon", "space", "rain"):
            tk.Radiobutton(style_box, text=st, font=F_SMALL, bg=C_CARD,
                           fg=C_TEXT, variable=self._vid_style_var,
                           value=st, activebackground=C_CARD,
                           activeforeground=C_GOLD).pack(side="left", padx=4)

        # ▶ generate row
        b = tk.Frame(card, bg=C_CARD); b.pack(fill="x", padx=16, pady=8)
        self._vid_gen_btn = tk.Button(
            b, text="▶ Generate Video", font=F_BOLD, bg=C_CARD2, fg=C_GOLD,
            relief="flat", cursor="hand2", activebackground=C_BORDER,
            command=self._video_gen_now)
        self._vid_gen_btn.pack(side="left", ipady=4, padx=(0, 8))
        tk.Button(b, text="🗂 Video-Folder kholo", font=F_BOLD,
                   bg=C_CARD2, fg=C_TEXT, relief="flat",
                   cursor="hand2", activebackground=C_BORDER,
                   command=self._video_open_dir).pack(side="left", ipady=4)
        tk.Label(b, text="… mp4 local data/videos/ me banayegi (no cloud)",
                 font=F_SMALL, bg=C_CARD, fg=C_DIM).pack(
            side="left", padx=(12, 0), anchor="center")

        # 📤 result row
        self._vid_res = tk.Label(card, text="", font=F_FONT, bg=C_CARD,
                                  fg=C_DIM, anchor="w", justify="left",
                                  wraplength=900)
        self._vid_res.pack(fill="x", padx=16, pady=(4, 12))

    def _video_gen_now(self):
        """▶ generate button → background thread me video_gen.generate_video()
        (thread-safe UI freeze nahi hota)."""
        self._vid_gen_btn.configure(state="disabled", text="…")
        self._vid_res.configure(text="🎬 video ban rahi hai (local engine)…",
                                fg=C_GOLD)
        prompt = self._vid_prompt_var.get().strip() or "cinematic epic scene"
        dur = self._vid_dur_var.get()
        fps = self._vid_fps_var.get()
        style = self._vid_style_var.get()
        d = {"prompt": prompt, "duration": dur, "fps": fps, "style": style}

        def work():
            try:
                from agent import video_gen as _vg
                out = _vg.generate_video(prompt, duration_sec=float(dur),
                                          fps=fps, style=style)
                mm = _vg.video_meta(out)
                self.after(0, lambda: self._video_done(out, mm))
            except Exception as e:
                import traceback
                self.after(0, lambda e=e: self._video_fail(e))

        threading.Thread(target=work, daemon=True).start()

    def _video_done(self, out, mm):
        self._vid_gen_btn.configure(state="normal", text="▶ Generate Video")
        self._vid_res.configure(
            text=("✅ video ban gayi — 100% local (Hemomemo engine):\n"
                  "    file: %s\n    duration: %ss   size: %sKB   fps: %s\n"
                  "    (data/videos/ me mehfooz — aap ka apna PC, koi cloud nahi)"
                  % (out, mm.get("duration"),
                     int(mm.get("size", 0) / 1024), mm.get("fps"))),
            fg=C_ACCENT)

    def _video_fail(self, e):
        self._vid_gen_btn.configure(state="normal", text="▶ Generate Video")
        self._vid_res.configure(text="❌ video FAIL: %s" % e, fg=C_DANGER)

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
             "7.07M params · dh660 · khud-soch"),
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
            ("📦 Version", "v4.1.0 — 4-dimagh network (master 7.07M + deep "
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
