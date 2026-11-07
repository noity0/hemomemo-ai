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
from typing import Callable, Optional

# --- Minecraft protocol version (client khud batata hai) ---
PROTOCOL_VERSION = 763  # 1.20.1 (badal sakte hain: 767=1.21 etc.)

STATE_STATUS = 1
STATE_LOGIN = 2
STATE_PLAY = 3


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
            self.sock.sendall(pack_packet(0x05, _mc_string(msg[:256])))  # 0x05=chat (1.20.x)
            return True
        except OSError:
            return False

    # --- 3) sun'na + Hemomemo-dimagh se jawab ---
    def _handle_play(self, pid: int, payload: bytes) -> None:
        if pid == 0x0F:  # keepalive (1.20.x) -> wapas bhejo
            if len(payload) >= 8:
                self.sock.sendall(pack_packet(0x0F, payload[:8]))  # echo same id
            return
        if pid == 0x30:  # system/chat message (1.20.x)
            try:
                text = _read_mc_string(payload)
                self._on_chat(text)
            except Exception:
                pass
            return

    def _on_chat(self, raw: str) -> None:
        self._log("chat: " + raw[:200])
        # bot ko address kiya gaya? (Hemomemo / hemomemo / @bot)
        low = raw.lower()
        if "hemomemo" in low or self.username.lower() in low:
            sawal = raw
            for token in ("<", ">", "[", "]"):
                sawal = sawal.replace(token, " ")
            jawab = ""
            try:
                jawab = (self.answer_fn(sawal.strip()) or "").strip()
            except Exception:
                jawab = ""
            if not jawab:
                jawab = "Main Hemomemo AI hoon - 100% local. Batao kis game me madad karoon?"
            self.say(jawab[:250])

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
