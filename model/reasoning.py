"""HEMOMO REASONING - sochne ka loop (100% local, koi API nahi).

Input ko parhta hai -> irada pehchanta hai -> yaadasht + ilm nikalta hai
-> mansoora (plan) banata hai -> jawab-tayyar karta hai.

Ye LLM nahi hai - ye Hemomemo ka apna niyam-soch (rule + retrieval +
deterministic-math + local-LSTM composer) hai.
"""
from __future__ import annotations

import ast
import operator as op
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

# safe math evaluator (sirf calculator-ops, koi code-execute nahi)
_OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.FloorDiv: op.floordiv,
        ast.Mod: op.mod, ast.Pow: op.pow, ast.USub: op.neg,
        ast.UAdd: op.pos}

def _ev(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_ev(node.left), _ev(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_ev(node.operand))
    raise ValueError("unsupported")

def safe_math(expr: str) -> Optional[str]:
    """Sirf digits/operators wale maths ko pakka sahi jawab (deterministic)."""
    expr = expr.strip().replace("x", "*").replace("×", "*").replace("÷", "/")
    if not re.fullmatch(r"[\d\s\+\-\*/\(\)\.]+", expr):
        return None
    try:
        val = _ev(ast.parse(expr, mode="eval").body)
        if isinstance(val, float) and val.is_integer():
            val = int(val)
        return str(val)
    except Exception:
        return None


CODE_HINTS = ("python", "javascript", "java ", "kotlin", "c++", "cpp", "sql",
              "html", "css", "bash", "rust", "golang", "go ", "php", "ruby",
              "function", "class ", "loop", "array", "list", "api", "regex",
              "code", "program", "script", "bug", "error", "compile", "syntax")

GAME_HINTS = ("minecraft", "creeper", "enderman", "nether", "ender", "redstone",
              "biome", "mob", "spawn", "server", "game", "player", "roblox",
              "fortnite", "pokemon", "chess", "ludo", "speedrun", "mod", "skin")

ISLAMIC_HINTS = ("allah", "quran", "namaz", "salah", "roza", "sawm", "zakat",
                 "hajj", "umrah", "wudu", "ghusl", "hadith", "sunnah", "dua",
                 "ramadan", "eid", "tawheed", "sabr", "shukr", "hijab", "halal")

@dataclass
class Plan:
    intent: str
    steps: List[str] = field(default_factory=list)
    math_answer: Optional[str] = None
    context: List[str] = field(default_factory=list)
    final: str = ""


class Reasoner:
    """Hemomemo ka sochne-wala dimagh-module.

    answer_fn = Hemomemo ka local composer (injection se - testable).
    """

    def __init__(self, answer_fn: Optional[Callable[[str], str]] = None,
                 knowledge=None, memory=None) -> None:
        self.answer_fn = answer_fn
        self.knowledge = knowledge
        self.memory = memory

    # 1) irada pehchan
    def detect_intent(self, prompt: str) -> str:
        p = (prompt or "").lower()
        # pehle math-hisssa dhoondo (prompt ke andar chhupa math)
        m = re.search(r"\(?[\d]+[\d\s\+\-\*x×÷/\(\)]*[\d\)]", p)
        if m and safe_math(m.group(0).strip()):
            return "math"
        if any(h in p for h in ISLAMIC_HINTS):
            return "islamic"
        if any(h in p for h in CODE_HINTS):
            return "coding"
        if any(h in p for h in GAME_HINTS):
            return "game"
        return "general"

    # 2) context uthana (yaad + ilm)
    def gather(self, prompt: str) -> List[str]:
        ctx: List[str] = []
        if self.knowledge is not None:
            try:
                for _q, a, _s in self.knowledge.search(prompt, k=2):
                    ctx.append(a[:500])
            except Exception:
                pass
        if self.memory is not None:
            try:
                for rec in self.memory.recall(prompt, k=2):
                    ctx.append("pehle kaha: " + str(rec.get("user", ""))[:200])
            except Exception:
                pass
        return ctx

    # 3) mansoora banao
    def plan(self, prompt: str) -> Plan:
        intent = self.detect_intent(prompt)
        pl = Plan(intent=intent)
        pl.context = self.gather(prompt)
        if intent == "math":
            m = re.search(r"([\d\s\+\-\*x×÷/\(\)\.]+)", prompt)
            expr = m.group(1).strip() if m else prompt
            val = safe_math(expr)
            pl.math_answer = val
            pl.steps = ["math-expression parhi", "deterministic hisaab kiya",
                        "pakka jawab diya (guess nahi)"]
            pl.final = f"{expr} = {val}" if val is not None else ""
            return pl
        if intent == "coding":
            pl.steps = ["coding-sawal parha", "knowledge-retrieval se mutaliq code-ilm nikala",
                        "code-block jawab banaya (local)"]
        elif intent == "game":
            pl.steps = ["game-sawal parha (minecraft/games)",
                        "games-knowledge se mutaliq jawab nikala",
                        "agent-kheli style me jawab diya"]
        elif intent == "islamic":
            pl.steps = ["islami sawal parha", "adab ke sath, ilm ke dayre me jawab",
                        "yaqini-ilm ke ilawa ehtiyaat batayi"]
        else:
            pl.steps = ["sawal parha", "yaad+ilm se context jama kiya",
                        "apne dimagh se jawab banaya"]
        if self.answer_fn is not None:
            try:
                out = self.answer_fn(prompt)
                if out:
                    if pl.context:
                        pl.final = out.strip() + "\n\n" + pl.context[0][:400]
                    else:
                        pl.final = out.strip()
                    return pl
            except Exception:
                pass
        pl.final = (pl.context[0][:800] if pl.context else "")
        return pl

    # 4) seedha jawab
    def respond(self, prompt: str) -> str:
        pl = self.plan(prompt)
        return pl.final

    def respond_with_memory(self, prompt: str, tag: str = "chat") -> str:
        out = self.respond(prompt)
        if self.memory is not None and out:
            try:
                self.memory.remember(prompt, out, tag=tag)
            except Exception:
                pass
        return out
