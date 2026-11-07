"""HEMOMO AGENT-CONSOLE - alag EXE, desktop-app ke sath, USI dimagh se.

Yeh kya hai (user-qanoon):
  "bande ke computer ke Minecraft (TLauncher/SFX/XMLEMC - koi bhi) mein
   ek bot enter karayein - sirf Hemomemo apni API/dimagh se - aur bande
   EXE se AUR Minecraft-chat se bot ko order de."

MODES:
  [1] MC-JOIN : bot KHUD naya player ban kar offline/LAN server par
                enter hota hai (login/enter/join - apna VarInt-protocol)
  [2] MC-DUO  : 2 KIRDAR ek sath (person ke sath multi - 2 characters)
  [3] PC-DIRECT : bande ki SCREEN parhe + control kare - jab tak ESC na
                dab jaye (ESC = foran stop, hifazat pehle)
  [4] PC-WATCH  : sirf dekhe (koi control nahi)

ORDER DO (dono jagah se - ek hi dimagh):
  - YAHIN console mein: chal / peeche / baen / daen / jump / ghum 180 /
    hal / ruk / khatam  (ya koi bhi sawal - dimagh jawab dega)
  - MINECRAFT-CHAT mein: "<aap> Hemomemo chal" - bot andar hi chal padta

DEEPLY-LINKED: yeh EXE desktop-app ke FOLDER mein rehta hai aur USI ka
dimagh istemal karta hai (model/ + data/ isi folder se) - alag API, alag
cloud, doosra AI - KUCH NAHI. Sirf Hemomemo AI system.
"""
from __future__ import annotations

import ctypes
import os
import sys
import threading
import time

# --- frozen: EXE jis folder mein, USI ka dimagh (deeply-linked) ---
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

VK_ESC = 0x1B


def _banner() -> None:
    print("=" * 62)
    print("  HEMOMEO AGENT-CONSOLE  (100%% local - sirf Hemomemo AI system)")
    print("  Minecraft bot-player + PC-aankh/haath | NO any API of the world")
    print("=" * 62)


def _brain_answer(prompt: str) -> str:
    """USI desktop-app ka token-dimagh (isi folder se - deeply-linked)."""
    try:
        from model.understand import default_token_chat
        return default_token_chat().respond_with_memory(prompt, tag="agent")
    except Exception as e:
        print("[dimagh] jawab nahi ban saka (honest): %s" % e)
        return ""


# ------------------------------------------------------------- MC modes
def _mc_order_loop(bot, name: str) -> None:
    """Console-se order do (Minecraft-chat se bhi chalte hain - wahan
    bot khud parser se chalta hai)."""
    print("\nHUKUM do: chal / peeche / baen / daen / jump / ghum 180 / hal / "
          "ruk / khatam  (ya koi bhi sawal)")
    while bot.running and bot.sock:
        try:
            raw = input("%s-order> " % name).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw:
            continue
        from agent.orders import parse, describe
        o = parse(raw)
        print("  " + describe(o))
        if o.action == "ruk":
            bot.say("ruk gaya - sab harkat band.")
            continue
        if o.action == "khatam":
            bot.say("alvida - main nikal raha hoon!")
            break
        if o.action == "hal":
            p = bot.see()
            print("  AANKHEIN: %s" % p)
            bot.say("jagah x=%s y=%s z=%s" % (p["pos"].get("x"),
                                              p["pos"].get("y"),
                                              p["pos"].get("z")))
            continue
        if o.action == "jump":
            bot.move_step(dy=1.0)
            bot.say("chhalang!")
            continue
        if o.action == "ghum":
            ang = o.angle if o.angle is not None else 90.0
            bot.look((bot.pos.get("yaw", 0.0) + ang) % 360.0,
                     bot.pos.get("pitch", 0.0))
            bot.say("%.0f darjy ghum gaya" % ang)
            continue
        if o.action in ("aage", "peeche", "baen", "daen"):
            sign = -1.0 if o.action == "peeche" else 1.0
            dist = o.meters if o.meters is not None else 2.0
            if o.action == "baen":
                bot.look((bot.pos.get("yaw", 0.0) - 90.0) % 360.0,
                         bot.pos.get("pitch", 0.0))
            elif o.action == "daen":
                bot.look((bot.pos.get("yaw", 0.0) + 90.0) % 360.0,
                         bot.pos.get("pitch", 0.0))
            n = bot.walk_forward(dist)
            bot.say("%d qadam chal gaya (%s)" % (n, o.action))
            continue
        if o.action == "chat":
            jawab = _brain_answer(o.raw)
            if jawab:
                print("  dimagh> %s" % jawab[:300])
                bot.say(jawab[:250])
            continue
        print("  (samajh nahi aaya - dobara likhein)")


def mc_join(host: str, port: int = 25565, name: str = "HemomemoAI",
            duo: bool = False) -> int:
    """Bot KHUD login/enter/join karta hai (offline/LAN - koi auth-API nahi)."""
    from agent.mc_bot import MinecraftBot, duo_play
    if duo:
        return duo_play(_brain_answer, host, port)
    bot = MinecraftBot(answer_fn=_brain_answer, username=name)
    if not bot.join_server(host, port):
        print("[honest] server par enter nahi ho saka - host/port/offline-mode dekho")
        return 1
    bot.play()
    try:
        _mc_order_loop(bot, name)
    finally:
        bot.leave()
    return 0


# ------------------------------------------------------------- PC modes
def _esc_dabaa() -> bool:
    """ESC dabaa hua? (Windows GetAsyncKeyState - stdlib)."""
    return bool(ctypes.windll.user32.GetAsyncKeyState(VK_ESC) & 0x8000)


def pc_direct(seconds_max: float = 0.0) -> int:
    """SCREEN parho + CONTROL karo - jab tak ESC na dab jaye (foran stop).

    Har round: aankh (screenshot-tahlil) -> aap ke console-hukum chalaye
    (chal=walk_forward, ghum=mouse_look, jump=space, ruk=kuch nahi)."""
    from agent.pc_eye import Eye, Hand
    eye, hand = Eye(), Hand()
    print("\nPC-DIRECT: screen parh raha hoon + aap ke hukum chala raha hoon.")
    print("  HUKUM: chal / jump / ghum <darjy> / ruk |  ** ESC = foran STOP **")
    orders_q: list = []
    stop = {"now": False}

    def _stdin():
        while not stop["now"]:
            try:
                q = input("pc-hukum> ").strip()
                orders_q.append(q)
            except (EOFError, KeyboardInterrupt):
                stop["now"] = True

    threading.Thread(target=_stdin, daemon=True).start()
    n = 0
    while not stop["now"]:
        if _esc_dabaa():
            print("\n** ESC dab gaya - FORAN STOP (hifazat pehle) **")
            break
        n += 1
        d = eye.describe()
        if "error" not in d:
            print("[%d] %s" % (n, eye.see_say()))
        # console-hukum chalao
        while orders_q:
            raw = orders_q.pop(0)
            from agent.orders import parse, describe
            o = parse(raw)
            print("  " + describe(o))
            if o.action == "aage":
                hand.walk_forward(1.0)
            elif o.action == "jump":
                hand.jump()
            elif o.action == "ghum":
                hand.mouse_look(o.angle if o.angle is not None else 30.0)
            elif o.action == "khatam" or _esc_dabaa():
                stop["now"] = True
                break
        time.sleep(1.0)
    print("PC-DIRECT khatam - %d round dekha/chalaya. (ESC-se-stop salam)" % n)
    return 0


def pc_watch(rounds: int = 6, pause: float = 2.0) -> int:
    """SIRF dekhe - koi control nahi (aankh bina haath)."""
    from agent.pc_eye import watch_and_report
    watch_and_report(rounds, pause)
    return 0


# ------------------------------------------------------------------ main
def main(argv: list) -> int:
    _banner()
    print("  [1] MC-JOIN  (bot khud naya player - multi aap ke sath)")
    print("  [2] MC-DUO   (2 KIRDAR ek sath)")
    print("  [3] PC-DIRECT (screen parhe + control - ESC tak)")
    print("  [4] PC-WATCH  (sirf dekhe)")
    print("=" * 62)
    if len(argv) >= 3:
        mode, host = argv[1], argv[2]
        port = int(argv[3]) if len(argv) > 3 and argv[3].isdigit() else 25565
        if mode == "mc":
            return mc_join(host, port)
        if mode == "duo":
            return mc_join(host, port, duo=True)
        if mode == "pc":
            return pc_direct()
        if mode == "watch":
            return pc_watch()
    try:
        ch = input("Chunahein [1/2/3/4]: ").strip()
    except (EOFError, KeyboardInterrupt):
        return 0
    if ch in ("1", "2"):
        hp = input("Minecraft server host:port (misal: 127.0.0.1:25565): ").strip()
        host, _, prt = hp.partition(":")
        port = int(prt) if prt.isdigit() else 25565
        return mc_join(host or "127.0.0.1", port, duo=(ch == "2"))
    if ch == "3":
        return pc_direct()
    if ch == "4":
        return pc_watch()
    print("kuch nahi chuna - khatam. (100% local, koi kaam nahi hua)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
