"""HEMOMO 3-MODES CLI - text | code | agent  (100% local, NO AI-API).

Chalana:
  py -3 -m agent.modes text     <- chat mode
  py -3 -m agent.modes code     <- coding-AI mode (code-block jawab)
  py -3 -m agent.modes agent    <- Minecraft bot (direct-play / server)

Dimagh: model.reasoning.Reasoner (retrieval + deterministic-math +
yaad-dasht). Bahar-ki AI koi nahi - koi API nahi.
"""
from __future__ import annotations

import sys


def _build_reasoner():
    try:
        from model.reasoning import Reasoner
        from model.memory import EpisodicStore, KnowledgeRetrieval, make_answer_fn

        know = KnowledgeRetrieval(r"D:\DigitalBrain\data\corpus_big")
        mem = EpisodicStore(r"D:\DigitalBrain\data")
        answer = make_answer_fn(knowledge=know, memory=mem)
        return Reasoner(answer_fn=answer, knowledge=know, memory=memory_safe(mem))
    except Exception:
        from model.reasoning import Reasoner
        return Reasoner()


def memory_safe(mem):
    return mem


def run(mode: str = "text") -> int:
    reasoner = _build_reasoner()
    print(f"HEMOMO AI - mode: {mode} | 100% local | koi AI-API nahi")
    if mode == "agent":
        from agent.mc_bot import direct_play
        direct_play(reasoner.respond_with_memory)
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
        jawab = reasoner.respond_with_memory(q, tag=tag)
        if mode == "code" and jawab and "```" not in jawab:
            jawab = "```\n" + jawab + "\n```"  # coding hamesha code-block
        print("Hemomemo> " + (jawab[:1200] if jawab else "(soch raha hoon...)"))
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "text"
    sys.exit(run(mode))
