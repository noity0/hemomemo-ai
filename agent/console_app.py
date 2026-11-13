"""HEMOMEO GAME-BOT - alag EXE, desktop-app ke sath, USI dimagh se.

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
    print("  HEMOMEO GAME-BOT  (100% local - sirf Hemomemo AI system)")
    print("  Game bot-player (Minecraft/koi bhi game) + PC-aankh/haath")
    print("  NO any API of the world - aap ke control mein, ESC = stop")
    print("=" * 62)


def _brain_answer(prompt: str) -> str:
    """USI desktop-app ka token-dimagh (isi folder se - deeply-linked).

    Pehle TASK/SEKH-system dekho ("sekho ...", "kaam ...") - ye bhi
    100% local hai (token-think + data-memory). Warna seedha dimagh."""
    # SEARCH-API fast-path (web-search - koi AI-API nahi)
    try:
        from model import search_api as _sa
        _sw, _sq = _sa.wants_search(prompt)
        if _sw:
            _stxt, _sm = _sa.search_text(_sq)
            print(_stxt[:800])
            return _stxt[:800]
    except Exception:
        pass
    # GMAIL fast-path (inbox/email - app-password wala)
    try:
        from model import gmail_link as _gl
        _mw, _md = _gl.wants_mail(prompt)
        if _mw:
            _mtxt, _mm = (_gl.read_inbox_text() if _mw == "read"
                          else _gl.send_from_command(_md))
            print(_mtxt[:800])
            return _mtxt[:800]
    except Exception:
        pass
    try:
        from agent import tasks as _t
        from model.memory import EpisodicStore
        if not getattr(_brain_answer, "_sys", None):
            _brain_answer._sys = _t.TaskSystem(
                EpisodicStore(os.path.join(ROOT, "data")),
                os.path.join(ROOT, "data", "corpus_big", "gamebot_tasks.txt"))
        hua, jawab = _t.handle(prompt, _brain_answer._sys)
        if hua and jawab:
            print(jawab[:800])
            return jawab
    except Exception as e:
        print("[task-system masla - honest] %s" % e)
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
    print("\nPC-DIRECT: koi bhi GAME/app - poora READ + CONTROL (aap hukmi).")
    print("  HUKUM: chal / peeche / baen / daen / jump / ghum <darjy> /")
    print("         k <key> (misal: k f, k 1, k space) / click / rclick |")
    print("         type <text> / close / open <app> / scroll / press <key> /")
    print("         hotkey <combo> (misal: alt+f4, ctrl+s, win+d) / dblclick /")
    print("         move <dx dy> / win |")
    print("  ** ESC = foran STOP (sab control aap ke haath) **")
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
        # console-hukum chalao (poora control - aap hukmi, ESC stop)
        while orders_q:
            raw = orders_q.pop(0)
            low = raw.lower()
            if low.startswith("k "):
                kn = low[2:].strip()
                if hand.key(kn):
                    print("  key '%s' dabai" % kn)
                else:
                    print("  [honest] key '%s' map mein nahi" % kn)
                continue
            if low in ("click", "rclick"):
                hand.mouse_click("left" if low == "click" else "right")
                print("  mouse-%s dabai" % ("left" if low == "click" else "right"))
                continue
            # ---- FULL PC-CONTROL ALLOWANCE (user-demand: hr cheez par control)
            words = low.split(None, 1)
            kw = words[0] if words else ""
            rest = words[1].strip() if len(words) > 1 else ""
            if kw in ("type", "typekar", "dikdo", "likho", "likh"):
                hand.type_text(rest or "x")
                print("  typed: %r" % (rest or "")[:50])
                continue
            if kw in ("close", "band"):
                ok = hand.close_active() if not rest else hand.close_window(rest)
                print("  close-window: %s (%s)"
                      % (rest or "active", "ho gaya" if ok else "nahi mili"))
                continue
            if kw == "open":
                app = rest or "notepad"
                try:
                    if hasattr(os, "startfile"):
                        os.startfile(app)
                    else:
                        import subprocess
                        subprocess.Popen(app)
                    print("  open: %s" % app)
                except Exception as _e:
                    print("  [honest] open nahi hua: %s" % _e)
                continue
            if kw == "scroll":
                try:
                    hand.scroll(int(rest or 1))
                    print("  scroll: %s" % (rest or 1))
                except Exception:
                    print("  [honest] scroll nahi hua")
                continue
            if kw in ("scrollup", "scrolldown"):
                hand.scroll(3 if kw == "scrollup" else -3)
                print("  scroll-%s dabai" % kw)
                continue
            if kw in ("dblclick", "dclick"):
                hand.mouse_click("left")
                hand.mouse_click("left")
                print("  dblclick-left dabai")
                continue
            if low.startswith("press ") or kw == "press":
                k2 = low[6:].strip() if low.startswith("press ") else (rest or "enter")
                if hand.key(k2):
                    print("  key '%s' dabai" % k2)
                continue
            if kw == "hotkey":
                if hand.hotkey(rest or "ctrl+s"):
                    print("  hotkey: %s" % (rest or "ctrl+s"))
                continue
            if kw == "move":
                try:
                    nums = [float(x) for x in rest.replace(",", " ").split()[:2]]
                    hand.mouse_move(int(nums[0]) if len(nums) > 0 else 0,
                                   int(nums[1]) if len(nums) > 1 else 0)
                    print("  move: (%s, %s)" % (nums[0] if len(nums) > 0 else 0,
                                              nums[1] if len(nums) > 1 else 0))
                except Exception:
                    print("  [honest] move nahi hua")
                continue
            if kw == "win":
                hand.key("win")
                print("  win-key dabai")
                continue
            from agent.orders import parse, describe
            o = parse(raw)
            print("  " + describe(o))
            if o.action == "aage":
                hand.walk_forward(1.0)
            elif o.action == "peeche":
                hand.key("s", 1.0)
            elif o.action == "baen":
                hand.key("a", 1.0)
            elif o.action == "daen":
                hand.key("d", 1.0)
            elif o.action == "jump":
                hand.jump()
            elif o.action == "ghum":
                hand.mouse_look(o.angle if o.angle is not None else 30.0)
            elif o.action == "chat":
                jawab = _brain_answer(raw)     # task/sekho/aam-baat dono
                print("  dimagh> %s" % (jawab or "(khamosh)")[:300])
            elif o.action == "khatam" or _esc_dabaa():
                stop["now"] = True
                break
        time.sleep(1.0)
    print("PC-DIRECT khatam - %d round dekha/chalaya. (ESC-se-stop salam)" % n)
    return 0


def pc_watch(rounds: int = 0, pause: float = 2.0) -> int:
    """SIRF dekhe - koi control nahi (aankh bina haath).

    rounds=0 (menu-se) -> JAB-TAK-ESC dekhta rahe (6-qadam-wala mehdooda
    demo nahi). ESC = foran stop. CLI-se: `GameBot.exe watch 10` = 10
    round ka chhota imtihaan."""
    from agent.pc_eye import Eye
    eye = Eye()
    print("\nPC-WATCH: sirf dekh raha hoon (koi control nahi).")
    print("  ** ESC = foran STOP ** %s"
          % ("" if rounds else "(jab tak ESC na dabey)"))
    n = 0
    while True:
        if rounds and n >= rounds:
            break
        if _esc_dabaa():
            print("\n** ESC dab gaya - FORAN STOP **")
            break
        n += 1
        d = eye.describe()
        print("[%d] %s" % (n, eye.see_say() if "error" not in d
                           else d["error"]))
        time.sleep(pause)
    print("PC-WATCH khatam - %d round dekha. (aankh salam)" % n)
    return 0


# ------------------------------------------------------------------ main
def main(argv: list) -> int:
    _banner()
    # CLI-modes (automation ke liye - jaise pehle):
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
            return pc_watch(rounds=(int(host) if host.isdigit() else 0))
        if mode == "browser":
            from agent import browser_cloud as _bc
            url = argv[2] if len(argv) > 2 else "https://example.com"
            return _bc.main_cli(["fetch", url])
    # MENU-LOOP: bot KHUD band NAHI hota - mode khatam to WAPAS menu.
    # Band sirf bande apni marzi se (0 = Khatam). Galti par bhi honest
    # message + wapas menu (crash-exit nahi - hifazat pehle).
    while True:
        print("  [1] MC-JOIN  (bot khud naya player - multi aap ke sath)")
        print("  [2] MC-DUO   (2 KIRDAR ek sath)")
        print("  [3] PC-DIRECT (koi bhi game: parhe + control - ESC tak)")
        print("  [4] PC-WATCH  (sirf dekhe - jab tak ESC na dabey)")
        print("  [5] BROWSER    (Obscura browser - cloud-computer me serve+fetch)")
        print("  [0] KHATAM    (aap khud band karein)")
        print("=" * 62)
        try:
            ch = input("Chunahein [0/1/2/3/4/5]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nalvida - (console band hua). 100% local, salam!")
            return 0
        if ch == "0":
            print("alvida - Hemomemo Game Bot band (aap ke hukum par).")
            return 0
        try:
            if ch in ("1", "2"):
                hp = input("Minecraft server host:port (misal: "
                           "127.0.0.1:25565): ").strip()
                host, _, prt = hp.partition(":")
                port = int(prt) if prt.isdigit() else 25565
                mc_join(host or "127.0.0.1", port, duo=(ch == "2"))
            elif ch == "3":
                pc_direct()
            elif ch == "4":
                pc_watch()
            elif ch == "5":
                hp = input("Browser-URL (example: https://example.com): ").strip()
                if hp:
                    from agent import browser_cloud as _bc2
                    return _bc2.main_cli(["fetch", hp])
            else:
                print("kuch nahi chuna - dobara chunahein.")
        except Exception as e:
            print("[honest] masla aaya: %s" % e)
        print("-" * 62)
        print("  (mode khatam - WAPAS MENU: bot band NAHI hua)")
        print("-" * 62)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
