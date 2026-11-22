"""HEMOMO MINECRAFT BOT - apna local game-player (NO AI-API, kabhi nahi).

Kya karta hai:
  1) SERVER-MODE : offline-mode / LAN Minecraft server se judta hai
     (handshake -> login -> chat). Bot chat parhta/likhta hai aur
     Hemomemo ke apne dimagh se jawab deta hai (apna composer inject hota hai).
  2) DIRECT-MODE : bina server ke - aap terminal me type karo, bot
     Hemomemo ke dimagh se khelta-hua jawab deta hai (sath khelna).

Imandari-hadd (honest limits):
  - Encryption sirf online-mode (Mojang-auth) servers par chahiye hoti hai -
    wo BAHAR ka auth hai, is liye support NAHI (offline/LAN servers ok).
  - Block-level khel (dig/build) ke liye server-side plugin (jaise mcpi /
    Raspberry-Jam) chahiye hota hai - wo hook neeche OPTIONAL diya gaya hai.

Ye file kisi bhi waqt koi bahar-ki-AI se baat NAHI karti - sirf
aap ke PC ka socket (server se khelne ke liye) aur aap ka terminal.
"""
from __future__ import annotations

import json
import socket
import struct
import sys
import threading
import time
from typing import Callable, Optional, Tuple

# --- Minecraft protocol version (client khud batata hai) ---
PROTOCOL_VERSION = 763  # 1.20.1 (badal sakte hain: 767=1.21 etc.)

STATE_STATUS = 1
STATE_LOGIN = 2
STATE_PLAY = 3

# server->client "apni jagah" packet-ids (version-bound, best-effort):
# 1.19.2~0x2E | 1.20.1~0x36 | 1.20.2+~0x3E - hum LENIENT parhte hain (jo mile)
_S2C_POSITION_IDS = {0x2E, 0x34, 0x35, 0x36, 0x3E, 0x40}


# ---------------- VarInt / framing ----------------
def write_varint(value: int) -> bytes:
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def read_varint(sock: socket.socket) -> Optional[int]:
    num = 0
    for i in range(5):
        chunk = sock.recv(1)
        if not chunk:
            return None
        b = chunk[0]
        num |= (b & 0x7F) << (7 * i)
        if not (b & 0x80):
            break
    return num


def pack_packet(packet_id: int, payload: bytes) -> bytes:
    body = write_varint(packet_id) + payload
    return write_varint(len(body)) + body


def unpack_packet(sock: socket.socket):
    """(packet_id, payload) ya None."""
    length = read_varint(sock)
    if not length or length > 2_000_000:
        return None
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
    # packet-id varint parho
    pid = 0
    shift = 0
    idx = 0
    while True:
        b = data[idx]
        pid |= (b & 0x7F) << shift
        idx += 1
        if not (b & 0x80):
            break
        shift += 7
    return pid, data[idx:]


def _mc_string(s: str) -> bytes:
    raw = s.encode("utf-8")
    return write_varint(len(raw)) + raw


def _read_mc_string(payload: bytes) -> str:
    ln = 0
    shift = 0
    idx = 0
    while True:
        b = payload[idx]
        ln |= (b & 0x7F) << shift
        idx += 1
        if not (b & 0x80):
            break
        shift += 7
    return payload[idx:idx + ln].decode("utf-8", errors="replace")


# ---------------- Bot ----------------
class MinecraftBot:
    """Hemomemo ka game-player bot (100% local brain).

    answer_fn = Hemomemo ka apna jawab-dene-wala (model.reasoning Reasoner).
    """

    def __init__(self, answer_fn: Callable[[str], str],
                 username: str = "HemomemoAI",
                 protocol_version: int = PROTOCOL_VERSION,
                 verbose: bool = True) -> None:
        self.answer_fn = answer_fn
        self.username = username
        self.protocol_version = protocol_version
        self.verbose = verbose
        self.sock: Optional[socket.socket] = None
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._pending_keepalive = 0
        # --- player-ki-AANKHEIN (server jo bheje, hum parhte hain) ---
        self.pos: dict = {"x": None, "y": None, "z": None,
                          "yaw": 0.0, "pitch": 0.0, "on_ground": True}
        self.chat_log: list = []          # aakhri chat (aankh ka ilm)
        self.health: Optional[float] = None

    # --- log ---
    def _log(self, msg: str) -> None:
        if self.verbose:
            print("[hemomemo-bot] " + msg, flush=True)

    # --- 1) server se judna ---
    def join_server(self, host: str, port: int = 25565, timeout: float = 8.0) -> bool:
        try:
            self.sock = socket.create_connection((host, port), timeout=timeout)
            self.sock.settimeout(0.5)  # non-blocking-ish read loop
        except OSError as e:
            self._log(f"server-judna fail: {e}")
            self.sock = None
            return False
        # handshake: ver | host | port | next-state=login
        hs = (write_varint(self.protocol_version) + _mc_string(host)
              + struct.pack(">H", port) + write_varint(STATE_LOGIN))
        self.sock.sendall(pack_packet(0x00, hs))
        # login start: username
        self.sock.sendall(pack_packet(0x00, _mc_string(self.username)))
        self._log(f"login bheja: {self.username} -> {host}:{port}")
        # login success (0x02) ya disconnect (0x00) ka intezar (thodi der)
        t0 = time.time()
        while time.time() - t0 < timeout:
            pkt = unpack_packet(self.sock)
            if pkt is None:
                continue
            pid, payload = pkt
            if pid == 0x02:  # login success
                self._log("server ne login qubool kar liya - khel shuru!")
                return True
            if pid == 0x00:  # disconnect (login-phase)
                self._log("server ne mana kiya: " + _read_mc_string(payload)[:200])
                return False
        self._log("login-waqt khatam")
        return False

    # --- 2) chat bhejna (play-state) ---
    def say(self, msg: str) -> bool:
        if not self.sock:
            return False
        try:
            # 0x05 = Chat Message (1.20.x C2S) - apne version-map se
            self.sock.sendall(pack_packet(self._C2S["chat"],
                                          _mc_string(msg[:256])))
            return True
        except OSError:
            return False

    # --- 3) sun'na + Hemomemo-dimagh se jawab (player-ki-aankhein) ---
    def _handle_play(self, pid: int, payload: bytes) -> None:
        # keepalive: LENIENT - jis pid par aaya, usi pid par wapas (version-azad)
        if len(payload) == 8 and pid not in (0x30, 0x31, 0x03, 0x02):
            try:
                self.sock.sendall(pack_packet(pid, payload))
                return
            except OSError:
                return
        if pid in (0x30, 0x31, 0x64, 0x6F):  # chat (1.19.x/1.20.x system/chat)
            try:
                text = _read_mc_string(payload)
                self._on_chat(text)
            except Exception:
                pass
            return
        # player-position (server -> hum): id version-bound - best-effort parhna
        if pid in _S2C_POSITION_IDS:
            try:
                self._read_self_position(payload)
            except Exception:
                pass
            return

    def _read_self_position(self, payload: bytes) -> None:
        """Apni jagah parho (x,y,z double + yaw/pitch float + ...) - aankh."""
        import struct as _s
        if len(payload) < 33:
            return
        x, y, z = _s.unpack(">ddd", payload[0:24])
        yaw, pitch = _s.unpack(">ff", payload[24:32])
        self.pos.update({"x": round(x, 2), "y": round(y, 2),
                         "z": round(z, 2), "yaw": round(yaw, 1),
                         "pitch": round(pitch, 1)})
        # teleport-confirm (C2S 0x00 varint id) - server sabar rahe
        try:
            tid = payload[32] if len(payload) > 32 else 0
            self.sock.sendall(pack_packet(0x00, write_varint(tid)))
        except OSError:
            pass

    # --- player-ke-HAATH: harkat (server-authoritative - imandari-hadd) ---
    _C2S = {"chat": 0x05, "pos": 0x15, "rot": 0x16, "ground": 0x17}

    def look(self, yaw: float, pitch: float) -> bool:
        """Game-camera ghumao (Set Player Rotation - 1.20.x shape)."""
        import struct as _s
        if not self.sock:
            return False
        self.pos["yaw"], self.pos["pitch"] = yaw, pitch
        body = (_s.pack(">ff", yaw, pitch)
                + (b"\x01" if self.pos.get("on_ground") else b"\x00"))
        try:
            self.sock.sendall(pack_packet(self._C2S["rot"], body))
            return True
        except OSError:
            return False

    def move_step(self, dx: float = 0.0, dy: float = 0.0,
                  dz: float = 0.0) -> bool:
        """Apni jagah aage/peeche bhejo (Set Player Position)."""
        import struct as _s
        if not self.sock or self.pos.get("x") is None:
            return False
        self.pos["x"] = round(self.pos["x"] + dx, 2)
        self.pos["y"] = round(self.pos["y"] + dy, 2)
        self.pos["z"] = round(self.pos["z"] + dz, 2)
        body = (_s.pack(">ddd", self.pos["x"], self.pos["y"], self.pos["z"])
                + (b"\x01" if self.pos.get("on_ground") else b"\x00"))
        try:
            self.sock.sendall(pack_packet(self._C2S["pos"], body))
            return True
        except OSError:
            return False

    def walk_forward(self, meters: float = 2.0, steps: int = 4) -> int:
        """Aage chalna (yaw ke rukh mein) - chhote qadam, server hi haqeeqi
        jagah tay karta hai (anti-cheat wale theek karte - imandari)."""
        import math as _m
        yaw = _m.radians(self.pos.get("yaw", 0.0))
        dx, dz = -_m.sin(yaw) * (meters / steps), _m.cos(yaw) * (meters / steps)
        n = 0
        for _ in range(steps):
            if self.move_step(dx=dx, dz=dz):
                n += 1
            time.sleep(0.05)
        return n

    def see(self) -> dict:
        """AANKHEIN kholo: apni jagah + sehat + aakhri chat (sab local-parha)."""
        return {"name": self.username, "pos": dict(self.pos),
                "health": self.health, "chat_tail": list(self.chat_log[-5:])}

    def _on_chat(self, raw: str) -> None:
        self._log("chat: " + raw[:200])
        self.chat_log.append(raw[:300])
        if len(self.chat_log) > 50:               # aankh ka daayra (50 chat)
            self.chat_log.pop(0)
        # bot ko address kiya gaya? (Hemomemo / hemomemo / @bot)
        low = raw.lower()
        if "hemomemo" not in low and self.username.lower() not in low:
            return
        # sender ka naam nikaalo ("<Ali> ...")
        sawal = raw
        for token in ("<", ">", "[", "]"):
            sawal = sawal.replace(token, " ")
        # 1) HUKUM? (EXE-console wala hi parser - ek dimagh, dono raste)
        try:
            from agent.orders import parse, describe
            o = parse(sawal)
            self._log(describe(o))
            if o.action == "ruk":
                self.say("ruk gaya - sab harkat band. (%s)" % self.username)
                return
            if o.action == "khatam":
                self.say("alvida - main nikal raha hoon!")
                self.leave()
                return
            if o.action == "hal":
                s = self.see()
                p = s["pos"]
                self.say("aankhein: jagah x=%s y=%s z=%s | rukh %.0f darjy"
                         % (p.get("x"), p.get("y"), p.get("z"),
                            float(p.get("yaw") or 0)))
                return
            if o.action == "jump":
                # jump = chhota upar-harkat (server-authoritative)
                self.move_step(dy=1.0)
                self.say("chhalang!")
                return
            if o.action == "ghum":
                ang = o.angle if o.angle is not None else 90.0
                self.look((self.pos.get("yaw", 0.0) + ang) % 360.0,
                          self.pos.get("pitch", 0.0))
                self.say("%.0f darjy ghum gaya" % ang)
                return
            if o.action in ("aage", "peeche", "baen", "daen"):
                sign = -1.0 if o.action == "peeche" else 1.0
                dist = o.meters if o.meters is not None else 2.0
                if o.action == "baen":
                    self.look((self.pos.get("yaw", 0.0) - 90.0) % 360.0,
                              self.pos.get("pitch", 0.0))
                elif o.action == "daen":
                    self.look((self.pos.get("yaw", 0.0) + 90.0) % 360.0,
                              self.pos.get("pitch", 0.0))
                n = self.walk_forward(dist)
                self.say("%d qadam chal gaya (%s)" % (n, o.action))
                return
            # 2) aam-baat -> Hemomemo-dimagh se jawab
            jawab = ""
            try:
                jawab = (self.answer_fn(sawal.strip()) or "").strip()
            except Exception:
                jawab = ""
            if not jawab:
                jawab = "Main Hemomemo AI hoon - 100% local. Hukum dein: chal / ruk / hal / ghum / jump."
            self.say(jawab[:250])
        except Exception as e:
            self._log("order-parhne mein masla (honest): %s" % e)

    def _loop(self) -> None:
        while self.running and self.sock:
            try:
                pkt = unpack_packet(self.sock)
                if pkt:
                    self._handle_play(*pkt)
            except socket.timeout:
                continue
            except OSError:
                break

    # --- 4) khelna shuru (background sun'na) ---
    def play(self) -> None:
        if not self.sock:
            self._log("pehle join_server() chalao")
            return
        self.running = True
        self.say(f"Assalam-o-alaikum! Main {self.username} hoon - Hemomemo AI (100% local).")
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def leave(self) -> None:
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass
        self._log("server chhoda")

    # --- 5) OPTIONAL: mcpi hook (block-level khel, agar mojood ho) ---
    def try_mcpi(self, host: str = "localhost") -> bool:
        """Raspberry-Jam/mcpi style local API (agar Minecraft me plugin ho)."""
        try:
            from mcpi.minecraft import Minecraft  # type: ignore
            mc = Minecraft.create(address=host)
            mc.postToChat("Hemomemo AI jud gaya - 100% local dimagh!")
            self._log("mcpi hook chal - block-level khel mumkin")
            return True
        except Exception:
            self._log("mcpi nahi mila (optional hai) - chat-mode kaafi hai")
            return False


def duo_play(answer_fn: Callable[[str], str], host: str, port: int = 25565,
             names: Tuple[str, str] = ("HemomemoAI", "HemomemoAI-2")) -> int:
    """MULTI-PLAY: 2 KIRDAR ek sath server par - dono Hemomemo-dimagh wale.

    - dono join karte hain (person ke sath 3 players bante hain)
    - dono aapas mein baat karte + person ke sawalon ke jawab dete hain
    - yehi hai "multi with person as 2 characters"
    """
    bots: list = []
    for nm in names[:2]:
        b = MinecraftBot(answer_fn=answer_fn, username=nm)
        if b.join_server(host, port):
            b.play()
            bots.append(b)
            time.sleep(0.5)
    if not bots:
        print("[duo] koi bot join nahi hua (host/port dekho)")
        return 0
    print("[duo] %d kirdar andar - person ke sath khel shuru!" % len(bots))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for b in bots:
            b.leave()
    return len(bots)


def direct_play(answer_fn: Callable[[str], str], bot_name: str = "HemomemoAI") -> None:
    """DIRECT-MODE: bina server ke - aap type karo, bot sath khelta hai."""
    print(f"=== {bot_name} DIRECT-PLAY (100% local) - 'khatam' likh kar band karo ===")
    hist: list = []
    while True:
        try:
            q = input("aap> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q.lower() in ("khatam", "quit", "exit"):
            break
        jawab = answer_fn(q)
        if not jawab:
            jawab = "(dimagh soch raha hai - thora aur wazah sawal do)"
        print(f"{bot_name}> {jawab[:500]}")
        hist.append((q, jawab[:120]))
    print(f"direct-play khatam - {len(hist)} baatein yaad mein mehfooz hain.")


if __name__ == "__main__":
    # seedha chalane par: py -3 agent\mc_bot.py <host> <username>
    if len(sys.argv) >= 2 and sys.argv[1] != "direct":
        host = sys.argv[1]
        user = sys.argv[2] if len(sys.argv) > 2 else "HemomemoAI"

        def _local_answer(prompt: str) -> str:
            try:
                sys.path.insert(0, r"D:\DigitalBrain")
                from model.reasoning import Reasoner  # type: ignore
                return Reasoner().respond(prompt)
            except Exception:
                return ""

        bot = MinecraftBot(answer_fn=_local_answer, username=user)
        if bot.join_server(host):
            bot.play()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                bot.leave()
    else:
        def _direct_answer(prompt: str) -> str:
            try:
                sys.path.insert(0, r"D:\DigitalBrain")
                from model.reasoning import Reasoner  # type: ignore
                return Reasoner().respond(prompt)
            except Exception:
                return ""
        direct_play(_direct_answer)
