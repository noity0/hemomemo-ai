"""HEMOMEO GAME-BOT - TASK/SEKH-SYSTEM (100% local, koi API nahi).

User-qanoon: "bot ko sekho kah kaam kaise karna hai - task aur order
dena ka system starting se end tak, KABHI bhi. Jo ye read kare use
PHIR think kare TOKEN may tor kar samjhe, LEARN kare, aur DATA-MEMORY
may save kare."

Teen kaam (sab local):
  SEKH  : bot ko sikhao  -> "sekho <sawal> = <jawab>"
          (token-think -> episodic-memory + tasks-corpus FILE dono me save)
  KAAM  : bot ko task do -> "kaam <task> phir <agla-qadam> ..."
          (token-read -> qadam-war qadam plan -> starting-se-end chalao
           -> nateeja memory me save -> imandari report)
  AAM   : baqi har baat seedha dimagh (TokenBrain) - pehle jaisa.

Yehi system EXE-console AUR Minecraft-chat DONO jagah chalta hai
(ek hi dimagh, dono raste - koi API-layer nahi).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from model import tokenize as tk

# task-kadam me tor-ne ke jor (Roman-Urdu + English)
_SPLIT_RX = re.compile(r"\s+(?:phir|then|aur|and|baad[- ]?me)\s+", re.I)
_SEKHO_RX = re.compile(r"^\s*sekho[:\s]+(.+)$", re.I)
_KAAM_RX = re.compile(r"^\s*kaam[:\s]+(.+)$", re.I)
_EQ_RX = re.compile(r"\s*(?:=|->|→|:)\s*", )      # "sawal = jawab"


@dataclass
class Step:
    """Ek task-qadam: 'order' (chalega) ya 'ilm' (dimagh jawab dega)."""
    kind: str                  # "order" | "ilm" | "brain"
    text: str
    action: str = ""           # orders-action (order-steps)


@dataclass
class Plan:
    task: str
    steps: List[Step] = field(default_factory=list)
    tokens: int = 0            # token-think: kitne token parhe

    def describe(self) -> str:
        lines = ["plan (%d qadam, %d token parhe):" % (len(self.steps),
                                                       self.tokens)]
        for i, s in enumerate(self.steps, 1):
            lines.append("  %d) [%s] %s" % (i, s.kind, s.text[:90]))
        return "\n".join(lines)


class TaskSystem:
    """Sikhna + kaam-karna - dono data-memory me mehfooz."""

    def __init__(self, memory, corpus_file: str) -> None:
        self.memory = memory                    # EpisodicStore (data/memory)
        self.corpus_file = corpus_file          # data-memFIle (Sawal:/Jawab:)

    # ------------------------------------------------- 1) SEKH (learn)
    def learn(self, sawal: str, jawab: str, tag: str = "gamebot-taleem") -> str:
        """Token-dar-token parho -> samjho -> memory+file dono me rakho."""
        sawal = " ".join((sawal or "").split())
        jawab = " ".join((jawab or "").split())
        if not sawal or not jawab:
            return "[honest] sekho ke liye DONO cheezein chahiye: " \
                   "sekho <sawal> = <jawab>"
        u = tk.understand(sawal + " " + jawab)          # token-think
        n_toks = len(getattr(u, "tokens", []) or [])
        # (a) episodic-memory (foran recall - naye-tareen pehle)
        self.memory.remember(sawal, "task_sekho:" + jawab, tag=tag)
        # (b) data-corpus FILE (daimi - retrieval isse parhta hai)
        try:
            os.makedirs(os.path.dirname(self.corpus_file), exist_ok=True)
            with open(self.corpus_file, "a", encoding="utf-8") as fh:
                fh.write("Sawal: %s\nJawab: %s\n\n" % (sawal, jawab))
        except OSError as e:
            return "[honest] file-save nahi hua (%s) - memory me zaroor hai" % e
        return ("seekh gaya (%d token parhe, samajh gaya): %s = %s "
                "[memory + data-file dono me mehfooz]"
                % (n_toks, sawal[:80], jawab[:80]))

    # ------------------------------------------------- 2) PLAN (tor)
    def plan(self, task: str) -> Plan:
        """Task ko TOKEN-dar-token parho -> qadam-war-qadam todo."""
        task = (task or "").strip()
        u = tk.understand(task)
        p = Plan(task=task, tokens=len(getattr(u, "tokens", []) or []))
        from agent.orders import parse
        for part in [q for q in _SPLIT_RX.split(task) if q.strip()]:
            part = part.strip()
            o = parse(part)
            if o.action != "chat":
                p.steps.append(Step("order", part, action=o.action))
                continue
            # aam-baat: pehle apna task-ilm dekho, warna dimagh
            ilm = self._task_ilm(part)
            p.steps.append(Step("ilm" if ilm else "brain", part, ))
        if not p.steps:
            p.steps.append(Step("brain", task))
        return p

    def _task_ilm(self, q: str) -> str:
        """Apne tasks-corpus se mutaliq ilm (koi web/API nahi)."""
        try:
            from model.memory import KnowledgeRetrieval
            kr = KnowledgeRetrieval(os.path.dirname(self.corpus_file))
            hits = kr.search(q, k=1)
            return hits[0][1][:600] if hits else ""
        except Exception:
            return ""

    # ------------------------------------------------- 3) KAAM (run)
    def run(self, task: str,
            executor: Optional[Callable[[Step], str]] = None,
            tag: str = "gamebot-kaam") -> str:
        """Starting-se-end: har qadam chalao -> report -> memory save.

        executor = har qadam chalane-wala (MC-bot/haath/dimagh). Na do
        to dimagh-khud har qadam ka jawab banati hai (honest)."""
        p = self.plan(task)
        if executor is None:
            def executor(s: Step) -> str:
                from model.understand import default_token_chat
                t, _m = default_token_chat().respond(s.text)
                return (t or "")[:200]
        report = ["kaam: %s" % p.task, p.describe()]
        ok = 0
        for i, s in enumerate(p.steps, 1):
            try:
                r = executor(s)
                r = (r or "").strip()
            except Exception as e:
                r = "[honest] qadam %d fail: %s" % (i, e)
            if r:
                ok += 1
            report.append("qadam %d/%d -> %s" % (i, len(p.steps),
                                                 r or "(kuch nahi)"))
        report.append("KAAM-KHATAM: %d/%d qadam chale "
                      "(starting-se-end, sab local)" % (ok, len(p.steps)))
        # nateeja data-memory me save (kabhi-bhi wapas dekh sakte hain)
        self.memory.remember("kaam:" + p.task, "kaam_khatam:%d/%d"
                             % (ok, len(p.steps)), tag=tag)
        return "\n".join(report)


# ------------------------------------------------------------- ROUTER
def handle(text: str, task_sys: TaskSystem,
           executor: Optional[Callable[[Step], str]] = None
           ) -> Tuple[bool, str]:
    """Kya ye baat task/sekho hai? (True, jawab) ya (False, '')."""
    t = text or ""
    m = _SEKHO_RX.match(t)
    if m:
        parts = _EQ_RX.split(m.group(1), maxsplit=1)
        sawal = parts[0]
        jawab = parts[1] if len(parts) > 1 else ""
        return True, task_sys.learn(sawal, jawab)
    m = _KAAM_RX.match(t)
    if m:
        return True, task_sys.run(m.group(1), executor=executor)
    return False, ""
