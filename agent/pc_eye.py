"""HEMOMO SCREEN-EYE + HAND - Hemomemo AI ki aankhein aur haath (100% local).

User-qanoon: "AI player ki aankhon se dekhe, use control kare, use kare."

EYE (aankh):
  - screenshot (PIL ImageGrab - Windows built-in)
  - local tahlil (NumPy): raushni-grid 4x4, ghalba-rang, harkat (pichle frame
    se farq) - koi cloud-vision NAHI, sirf apna numpy-soch

HAND (haath):
  - mouse harkat/click, keyboard tap - Windows SendInput (ctypes stdlib)
  - koi pyautogui/autoit nahi - pure Windows API, Win 7 se 11 Pro tak

Yeh module SIRF usi PC par user ke apne hukum se chalta hai - app ke andar
se khud-ba-khud kuch control nahi hota (START par user karta hai).
Koi API, koi network, koi doosra AI - NAHI.
"""
from __future__ import annotations

import ctypes
import time
from typing import Dict, Optional, Tuple

try:
    import numpy as np
except ImportError:
    np = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None


# ---------------------------------------------------------------- EYE
class Eye:
    """Screen ki aankh: dekho (screenshot) + samjho (numpy-tahlil)."""

    def __init__(self, grid: int = 4) -> None:
        self.grid = grid
        self._last = None          # pichla gray-frame (harkat ke liye)
        self.last_grab_s = 0.0

    def grab(self):
        """Screenshot -> numpy RGB (ya None agar PIL/numpy nahi)."""
        if ImageGrab is None or np is None:
            return None
        img = ImageGrab.grab()
        self.last_grab_s = time.time()
        return np.asarray(img)[:, :, :3]     # RGB (alpha chhodo)

    def describe(self, frame=None) -> Dict:
        """Dekhe hue ki samajh - raushni + rang + harkat (sab local)."""
        f = self.grab() if frame is None else frame
        if f is None:
            return {"error": "PIL/numpy nahi - aankh nahi khuli (honest)"}
        h, w = f.shape[0], f.shape[1]
        gray = f.mean(axis=2)
        g = self.grid
        cells = []
        for r in range(g):
            row = []
            for c in range(g):
                blk = gray[r * h // g:(r + 1) * h // g,
                           c * w // g:(c + 1) * w // g]
                row.append(round(float(blk.mean()), 1))
            cells.append(row)
        # ghalba-rang (coarse: 32-step quantize)
        q = (f // 32).reshape(-1, 3)
        vals, counts = np.unique(q, axis=0, return_counts=True)
        dom = (vals[counts.argmax()] * 32 + 16).tolist()
        # harkat (pichle frame se)
        motion = 0.0
        if self._last is not None and self._last.shape == gray.shape:
            motion = float(np.abs(gray - self._last).mean())
        self._last = gray
        return {"size": [w, h], "raushni": round(float(gray.mean()), 1),
                "grid": cells, "ghalba_rang": dom,
                "harkat": round(motion, 2), "ts": self.last_grab_s}

    def see_say(self) -> str:
        """Aankh ka insani-hisab (dimagh/UI ko dikhane ke liye)."""
        d = self.describe()
        if "error" in d:
            return d["error"]
        bright = d["raushni"]
        mood = ("raoshan" if bright > 170 else
                "dhamakeeli" if bright > 110 else
                "dhuskan" if bright > 55 else "taareekh-raat")
        mv = d["harkat"]
        move = ("kharch-harkat zyada" if mv > 8 else
                "halke-halke harkat" if mv > 1.5 else "sannata")
        return ("aankh: %dx%d | mahol %s (raushni %s) | %s"
                % (d["size"][0], d["size"][1], mood, bright, move))


# ---------------------------------------------------------------- HAND
_VK = {"space": 0x20, "enter": 0x0D, "esc": 0x1B, "tab": 0x09, "shift": 0x10,
       "ctrl": 0x11, "alt": 0x12, "up": 0x26, "down": 0x28, "left": 0x25,
       "right": 0x27, "w": 0x57, "a": 0x41, "s": 0x53, "d": 0x44, "e": 0x45,
       "f": 0x46, "r": 0x52, "q": 0x51, "1": 0x31, "2": 0x32, "3": 0x33,
       "4": 0x34, "5": 0x35, "win": 0x5B, "lwin": 0x5B, "rwin": 0x5C}

class Hand:
    """Haath: mouse + keyboard (Windows SendInput - ctypes, koi lib nahi)."""

    def __init__(self) -> None:
        self.user32 = ctypes.windll.user32
        self._mk = {}

    # ---- keyboard ----
    def key(self, name: str, hold_s: float = 0.0) -> bool:
        """Ek key dabao (w/a/s/d/space/1-5/enter.../f/q/arjumal-key)."""
        n = str(name).lower().strip()
        vk = _VK.get(n)
        if vk is None and len(n) == 1 and n.isalpha():
            vk = 0x41 + ord(n) - ord("a")      # ASCII-A-Z → real VK (A=0x41…Z=0x5A)
        if vk is None:
            return False
        self._tap(vk, hold_s)
        return True

    def _tap(self, vk: int, hold_s: float = 0.0) -> None:
        self._send_key(vk, True)
        if hold_s:
            time.sleep(min(hold_s, 2.0))
        self._send_key(vk, False)

    def _send_key(self, vk: int, down: bool) -> None:
        class _KI(ctypes.Structure):
            _fields_ = [("wVk", ctypes.c_ushort),
                        ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class _INPUT(ctypes.Structure):
            class _U(ctypes.Union):
                _fields_ = [("ki", _KI)]
            _anonymous_ = ("u",)
            _fields_ = [("type", ctypes.c_ulong), ("u", _U)]
        inp = _INPUT()
        inp.type = 1  # KEYBOARD
        inp.ki.wVk = vk
        inp.ki.dwFlags = 0 if down else 2  # KEYEVENTF_KEYUP
        self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

    def walk_forward(self, seconds: float = 1.0) -> bool:
        """Minecraft/any-game: W daba kar aage chalna."""
        vk = _VK["w"]
        self._send_key(vk, True)
        try:
            time.sleep(min(seconds, 10.0))
        finally:
            self._send_key(vk, False)
        return True

    def jump(self) -> bool:
        return self.key("space")

    # ---- mouse ----
    def mouse_move(self, dx: int, dy: int) -> None:
        """Relative mouse harkat (game-look ke liye)."""
        self.user32.mouse_event(0x0001, int(dx), int(dy), 0, 0)  # MOUSEEVENTF_MOVE

    def mouse_look(self, yaw_deg: float, pitch_deg: float = 0.0,
                   sens: float = 2.0) -> None:
        """Game-camera ghumao (Minecraft look)."""
        self.mouse_move(int(yaw_deg * sens), int(pitch_deg * sens))

    def mouse_click(self, button: str = "left") -> None:
        flags = {"left": (0x0002, 0x0004), "right": (0x0008, 0x0010),
                 "mid": (0x0020, 0x0040)}.get(button, (0x0002, 0x0004))
        self.user32.mouse_event(flags[0], 0, 0, 0, 0)
        self.user32.mouse_event(flags[1], 0, 0, 0, 0)

    def type_text(self, text: str, hold_s: float = 0.0) -> bool:
        """Keyboard se text likho (chat/game-input me).
        Pure Windows SendInput — no AI API, no cloud. Har printable char dabao."""
        ok = True
        for ch in (text or ""):
            if not ch.isprintable():
                continue
            if not self.key(ch, hold_s):
                ok = False
        return ok

    def scroll(self, amount: int = 1, axis: str = "vertical") -> bool:
        """Scroll (mouse wheel) — vertical/horizontal dono. Positive = aage."""
        try:
            self.user32.mouse_event(0x0004, 0, int(amount), 0, 0)  # WHEEL
            return True
        except Exception:
            return False

    def hotkey(self, combo: str) -> bool:
        """Hotkey: 'ctrl+s' / 'alt+f4' / 'win+d' / 'ctrl+shift+esc' jaisa.
        Modifiers rakh kar key dabao — pure Windows SendInput."""
        combo = str(combo or "").strip().lower().replace("_", "-")
        order: list = []
        rest = combo
        for m, mv in (("ctrl", 0x11), ("control", 0x11), ("alt", 0x12),
                      ("shift", 0x10), ("win", 0x5B), ("windows", 0x5B)):
            if m in rest:
                order.append(mv)
                rest = rest.replace(m, "")
        rest = rest.strip()
        vk = _VK.get(rest)
        if vk is None and len(rest) == 1 and rest.isalpha():
            vk = 0x41 + ord(rest) - ord("a")
        if vk is None:
            for m in reversed(order):
                self._send_key(m, False)
            return False
        for m in order:
            self._send_key(m, True)
        self._tap(vk, 0.06)
        for m in reversed(order):
            self._send_key(m, False)
        return True

    def close_window(self, title: str = "") -> bool:
        """Window dhoondho (title substring / empty = first-enumerated).
        → WM_CLOSE. Koi window nahi mila → False (honest)."""
        user32 = self.user32
        title = str(title or "").strip()
        hits: list = []

        @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)
        def _enum(hwnd, lparam):      # EnumWindows callback
            try:
                n = user32.GetWindowTextW(ctypes.c_void_p(hwnd))
            except Exception:
                return 1
            if not n:
                return 1
            if not title or title == "*" or title.lower() in n.lower():
                hits.append((hwnd, n))
            return 1

        try:
            user32.EnumWindows(_enum, 0)
        except Exception:
            return False
        if not hits:
            return False
        hwnd, _t = hits[0]
        try:
            user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0010, 0, 0)  # WM_CLOSE
            time.sleep(1.0)
            return True
        except Exception:
            return False

    def close_active(self) -> bool:
        """Foreground window ko khud-muhabbat band karo (WM_CLOSE)."""
        user32 = self.user32
        try:
            fg = user32.GetForegroundWindow()
        except Exception:
            return False
        try:
            user32.PostMessageW(ctypes.c_void_p(fg), 0x0010, 0, 0)
            time.sleep(1.0)
            return True
        except Exception:
            return False


# ------------------------------------------------- aankh+haath agent-loop
def watch_and_report(rounds: int = 5, pause_s: float = 2.0,
                     say=print) -> int:
    """PC-WATCH: aankh se dekho + batao (koi control nahi - sirf dekhna)."""
    eye = Eye()
    for i in range(rounds):
        say("[%d/%d] %s" % (i + 1, rounds, eye.see_say()))
        time.sleep(pause_s)
    return rounds


def play_with_eyes(rounds: int = 10, pause_s: float = 1.0, say=print,
                   act=None) -> int:
    """PC-PLAY: dekho -> dimagh faisla -> haath chalao (user ke hukum se).

    act(eye_desc, hand) - aap ka local-faisla-fun (koi API nahi)."""
    eye, hand = Eye(), Hand()
    for i in range(rounds):
        d = eye.describe()
        say("[%d] %s" % (i + 1, eye.see_say()))
        if act is not None:
            try:
                act(d, hand)
            except Exception as e:
                say("act-fail (honest): %s" % e)
        time.sleep(pause_s)
    return rounds


if __name__ == "__main__":
    # seedha chalao: py -3 agent\\pc_eye.py   -> sirf dekhta hai (report)
    watch_and_report(3, 1.5)
