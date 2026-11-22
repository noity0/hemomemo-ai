"""HEMOMO 3-MODES CLI - text | code | agent  (100% local, NO AI-API).

Chalana:
  py -3 -m agent.modes text              <- chat mode
  py -3 -m agent.modes code              <- coding-AI mode (code-block jawab)
  py -3 -m agent.modes agent             <- Minecraft bot (direct-play)
  py -3 -m agent.modes mc <host> [port]  <- Minecraft server JOIN (khud)
  py -3 -m agent.modes duo <host> [port] <- 2 KIRDAR (multi-play person ke sath)
  py -3 -m agent.modes pc-watch          <- screen-AANKH (dekhe + bataye)
  py -3 -m agent.modes pc-play           <- dekhe + chalaye (aankh+haath)

Dimagh: model.understand.TokenBrain (token-dar-token soch) + yaad + ilm +
composer. Bahar-ki AI koi nahi - koi API nahi.
"""
from __future__ import annotations

import sys


def _build_brain():
    """Shared token-dimagh (yaad + ilm + composer-fallback)."""
    try:
        from model.understand import default_token_chat
        return default_token_chat()
    except Exception:
        try:
            from model.reasoning import Reasoner
            return Reasoner()
        except Exception:
            return None


def run(mode: str = "text", arg1: str = "", arg2: str = "") -> int:
    brain = _build_brain()
    answer = brain.respond_with_memory if brain is not None else (lambda q, **k: "")
    print(f"HEMOMO AI - mode: {mode} | 100% local | koi AI-API nahi")

    # ---------------- AGENT: Minecraft server JOIN (khud) ----------------
    if mode == "mc":
        if not arg1:
            print("host dein: py -3 -m agent.modes mc <host> [port]")
            return 2
        from agent.mc_bot import MinecraftBot
        port = int(arg2) if arg2.isdigit() else 25565
        bot = MinecraftBot(answer_fn=answer, username="HemomemoAI")
        if bot.join_server(arg1, port):
            bot.play()
            print("HUKUM: 'hal' (aankhein) | 'chal' (aage) | 'khatam'")
            while True:
                try:
                    c = input("hukum> ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    break
                if c == "khatam":
                    break
                if c == "hal":
                    print(bot.see())
                elif c == "chal":
                    print("qadam:", bot.walk_forward(2.0))
                elif c:
                    bot.say(c)
            bot.leave()
        return 0

    # ---------------- AGENT: 2 KIRDAR multi-play ----------------
    if mode == "duo":
        if not arg1:
            print("host dein: py -3 -m agent.modes duo <host> [port]")
            return 2
        from agent.mc_bot import duo_play
        port = int(arg2) if arg2.isdigit() else 25565
        duo_play(answer, arg1, port)
        return 0

    # ---------------- AGENT: PC aankh (sirf dekhna) ----------------
    if mode == "pc-watch":
        from agent.pc_eye import watch_and_report
        watch_and_report(6, 2.0)
        return 0

    # ---------------- AGENT: PC aankh + haath ----------------
    if mode == "pc-play":
        from agent.pc_eye import play_with_eyes
        print("(pc-play: aankh se dekhta, dimagh ke hukum se WASD/mouse)")
        play_with_eyes(10, 1.0, act=_pc_act)
        return 0

    # ---------------- TEXT / CODE chat ----------------
    if mode == "agent":
        from agent.mc_bot import direct_play
        direct_play(answer)
        return 0

    tag = "text" if mode == "text" else "code"
    print("(khatam/exit likh kar band karein)")
    while True:
        try:
            q = input("aap> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q.lower() in ("khatam", "exit", "quit"):
            break
        jawab = answer(q, tag=tag)
        if mode == "code" and jawab and "```" not in jawab:
            jawab = "```\n" + jawab + "\n```"  # coding hamesha code-block
        print("Hemomemo> " + (jawab[:1200] if jawab else "(soch raha hoon...)"))
    return 0


def _pc_act(eye_desc: dict, hand) -> None:
    """Local-faisla: harkat zyada -> sabar; sannata -> halka dekho (demo).
    Yeh demo-loop hai - asli game-khel user ke hukum se hai."""
    mv = float(eye_desc.get("harkat", 0.0))
    if mv < 1.0:
        hand.mouse_look(8.0, 0.0)        # aankhein ghumao
    # zyada harkat par kuch nahi (har cheez pehle samjho)


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "text"
    a1 = sys.argv[2] if len(sys.argv) > 2 else ""
    a2 = sys.argv[3] if len(sys.argv) > 3 else ""
    sys.exit(run(m, a1, a2))
