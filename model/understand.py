"""HEMOMO TOKEN-DIMAGH - samajhne ka dil (100% local, koi API nahi).

Soch-loop: READ-TOKEN -> routing (math/formula/code/pehchaan/yaad/ilm)
-> ANSWER. Composer sirf aam-baat ka fallback hai (pehle dimagh khud
sochta hai — stub nahi).
"""
from __future__ import annotations

import ast
import math
import operator
import os
import re
import sys
import threading
import time
from typing import Callable, List, Optional, Tuple

from model import tokenize as tk
from model.code_exec import smart_code
from model.memory import EpisodicStore, KnowledgeRetrieval

# ---------------- soch-loop ke auzar (100% local, no-API) -----------------
_SAFE_BIN = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv, ast.Pow: operator.pow,
}
_MATH_RX = re.compile(r"^[\d\s\.\+\-\*/%x\(\)\^]+$")
_MATH_OP_RX = re.compile(r"[\+\-\*/%x\^]")
_CODE_REQ_RX = re.compile(r"(?i)^(?:code|code banao|code likho)\b\s*(.*)$")
_CODE_KA_RX = re.compile(r"(?i)\s+ka\s+code\b\s*:?\s*$")
_ID_RX = re.compile(
    r"(?i)\b(?:aap\s+kaun\s+ho|tum\s+kaun\s+ho|aap\s+kya\s+ho|tum\s+kya\s+ho|"
    r"who\s+are\s+you|what\s+is\s+your\s+name|tumhara\s+naam|tumhari\s+naam|"
    r"aap\s+ka\s+naam|apna\s+taruf)\b")
_YAAD_SAVE_RX = re.compile(
    r"(?i)\bmera\s+naam\s+([a-z0-9]+(?:\s+[a-z0-9]+){0,2})\s+hai\b")
_YAAD_RECALL_RX = re.compile(r"(?i)\bmera\s+naam\s+kya\s+hai\b")
_EMC2_RX = re.compile(r"(?i)\be\s*=\s*mc\s*\^?\s*2\b")
_CIRCLE_RX = re.compile(r"(?i)\b(?:circle|daira)\b")
_CIRCLE_PERIM_RX = re.compile(r"(?i)\b(?:mohit|perimeter|circumference)\b")
_TRIANGLE_RX = re.compile(r"(?i)\b(?:triangle|masallas)\b")
_C_LIGHT = 299792458.0
# sawal-lafz jo ilm-topic NAHI hain (search me ghusna nahi chahiye)
_ASK_WORDS = {
    "kaise", "likhein", "batao", "likho", "banao", "doon", "kare", "chal",
    "ruk", "ko", "ki", "ka", "ke", "who", "is", "kaun", "kya", "hai",
    "what", "how", "kitni", "kitna", "mujhe", "mera", "meri", "aap", "tum",
}


def _safe_eval(expr: str) -> float:
    """Sirf math-hisaab (AST-safe: adad + - * / % ** aur qawfi).
    Koi import/call/name nahi — 100% bandh-hua."""
    node = ast.parse(expr, mode="eval")

    def ev(n):
        if (isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                and not isinstance(n.value, bool)):
            return n.value
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = ev(n.operand)
            return v if isinstance(n.op, ast.UAdd) else -v
        if isinstance(n, ast.BinOp) and type(n.op) in _SAFE_BIN:
            l, r = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(r) > 1000:
                raise ValueError("bahut-bara-taqaat")
            return _SAFE_BIN[type(n.op)](l, r)
        raise ValueError("ghair-moajood-bayan")

    return ev(node.body)


def _math_text(text: str) -> str:
    """'9x5' -> '9*5', '^' -> '**' (hisab ke liye)."""
    e = text.replace("^", "**")
    e = re.sub(r"(?i)(\d)\s*x\s*(\d)", r"\1*\2", e)
    return e


def _num_fmt(v: float) -> str:
    """4.0 -> '4', 3.5 -> '3.5', bara-adad -> scientific."""
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        return str(int(v))
    if abs(v) < 1e15:
        return ("%.6f" % v).rstrip("0").rstrip(".")
    return "%.4e" % v


def _formula(low: str, u) -> Optional[Tuple[str]]:
    """Chote-hisabi-formulas (100% local tabela: circle/emc2/triangle)."""
    if _CIRCLE_RX.search(low):
        r = u.variables.get("r") or (u.nums[0] if u.nums else None)
        if r and r > 0:
            if _CIRCLE_PERIM_RX.search(low):
                return ("Circle ka mohit (r = %s) = %.4f — formula: 2πr"
                        % (r, 2.0 * math.pi * r),)
            return ("Circle ka area (r = %s) = %.4f — formula: A = πr²"
                    % (r, math.pi * r * r),)
    if _EMC2_RX.search(low):
        m = u.variables.get("m") or (u.nums[0] if u.nums else None)
        if m and m > 0:
            return ("E = m × c² = %.4e joule (m = %s, c = %s m/s)"
                    % (m * _C_LIGHT * _C_LIGHT, m, _C_LIGHT),)
    if _TRIANGLE_RX.search(low):
        b = u.variables.get("b") or (u.nums[0] if len(u.nums) > 0 else None)
        h = u.variables.get("h") or (u.nums[1] if len(u.nums) > 1 else None)
        if b and h and b > 0 and h > 0:
            return ("Triangle ka area (b = %s, h = %s) = %.4f — formula: ½bh"
                    % (b, h, 0.5 * b * h),)
    return None


class TokenBrain:
    def __init__(self, generate_fn=None, knowledge=None, memory=None):
        self.generate_fn = generate_fn
        self.knowledge = knowledge
        self.memory = memory

    def read(self, prompt: str):
        return tk.understand(prompt)

    def respond(self, prompt: str) -> Tuple[str, dict]:
        """POORA SOCH-LOOP: token -> routing -> jawab (100% local).
        Composer sirf aam-baat ka fallback hai."""
        text = (prompt or "").strip()
        u = self.read(text)
        toks = list(u.tokens) if u else []
        n_tok = len(toks)
        low = text.lower()
        keys = [k for k in (u.keys if u else []) if k not in _ASK_WORDS]
        soch = ["READ-TOKEN", "CONVERT-TO-BINARY", "READ-BY-AI", "THINK",
                "ANSWER"]

        def meta(src, bharosa, extra=None):
            m = {"source": src, "bharosa": bharosa, "soch": soch,
                 "tokens": n_tok}
            if extra:
                m.update(extra)
            return m

        # 1) MATH — sirf-adad-hisaab (2 + 2 = 4)
        if _MATH_RX.match(text) and _MATH_OP_RX.search(text):
            try:
                val = _safe_eval(_math_text(text))
                return ("%s = %s (math, 100%% local)" % (text, _num_fmt(val)),
                        meta("math", 0.95))
            except Exception:
                pass  # hisab na bana — agla-rasta

        # 2) FORMULA — apna tabela (circle/emc2/triangle)
        f = _formula(low, u)
        if f:
            return f[0], meta("formula", 0.9)

        # 3) CODE — 'code <x>' / '<x> ka code' -> asli-code (100% local)
        if _CODE_REQ_RX.match(text) or _CODE_KA_RX.search(text):
            m = _CODE_REQ_RX.match(text)
            payload = m.group(1) if m else _CODE_KA_RX.sub("", text)
            payload = payload.strip(" ?:!.,\t")
            try:
                t2, m2 = smart_code(payload)
                m2 = dict(m2 or {})
                m2["source"] = "code"
                m2.setdefault("tokens", n_tok)
                return t2, m2
            except Exception as e:
                return ("[code] code-banai me kharabi: %s" % str(e)[:200],
                        meta("code", 0.4))

        # 4) PEHCHAAN — kaun main hoon
        if _ID_RX.search(low):
            return ("Main Hemomemo AI hoon — aap ka apna 100% local dimagh: "
                    "chat, code, math, ilm, yaad, gamebot — sab isi PC par, "
                    "koi AI-API nahi.", meta("pehchaan", 0.9))

        # 5) YAAD — naam recall/save (apni yaad-dasht, JSONL)
        if self.memory:
            if _YAAD_RECALL_RX.search(low):
                nm = ""
                try:
                    fa = self.memory.facts("user_naam=")
                    nm = fa[0].strip() if fa else ""
                except Exception:
                    nm = ""
                if nm:
                    return ("Aap ka naam %s hai (meri yaad se, 100%% local)."
                            % nm, meta("yaad", 0.85))
                return ("Aap ka naam mujhe abhi yaad nahi — 'mera naam <naam> "
                        "hai' likho, main mehfooz karunga.", meta("yaad", 0.7))
            m_nm = _YAAD_SAVE_RX.search(text)
            if m_nm:
                nm = m_nm.group(1).strip()
                try:
                    self.memory.remember(text, "user_naam=" + nm, tag="yaad")
                except Exception:
                    pass
                return ("Bhar-poor! Aap ka naam %s — yaad-dasht me mehfooz "
                        "(100%% local)." % nm, meta("yaad", 0.9))

        # 6) ILM — apna corpus (token-overlap), sawal-lafz chhaan-kar
        if self.knowledge and keys:
            try:
                hits = self.knowledge.search(" ".join(keys), k=1)
            except Exception:
                hits = []
            if hits and hits[0][2] >= 0.5:
                return ("📚 ilm (apna corpus, 100%% local): %s" % hits[0][1],
                        meta("ilm", 0.75))
            if {"python", "loop"} <= set(keys):
                return ("Python me loop: `for i in range(5): print(i)` — ya "
                        "`while shart: ...` (100% local, chala-kar dekho).",
                        meta("ilm", 0.7))

        # 7) COMPOSER — aam-baat ka fallback (purana rasta)
        if self.generate_fn:
            try:
                out = self.generate_fn(prompt)
                if out and str(out).strip():
                    return str(out), meta("composer", 0.6)
            except Exception:
                pass

        # 8) IMANDARI — bina-jhoot, topic-echo ke sath
        topic = " ".join(keys[:3]) if keys else (toks[0] if toks
                                                 else "ye mauzu")
        return ('Is mauzu ("%s") par mere paas abhi pakki-ilm nahi — '
                'bina-jhoot baat nahi karta. Code, math, yaad ya ilm poocho '
                '— sab 100%% local chalta hai.' % topic,
                meta("imandari", 0.5))

    def respond_with_memory(self, prompt: str, tag: str = "chat") -> str:
        text, _ = self.respond(prompt)
        return text

_SHARED = {"brain": None}

def default_token_chat() -> TokenBrain:
    if _SHARED["brain"] is not None:
        return _SHARED["brain"]
    def composer(prompt: str) -> str:
        try:
            from model.generate import chat_once
            out = chat_once(prompt)
            return out[0] if isinstance(out, tuple) else out
        except Exception:
            return ""
    know = KnowledgeRetrieval(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "corpus_big"))
    mem = EpisodicStore(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
    _SHARED["brain"] = TokenBrain(generate_fn=composer, knowledge=know, memory=mem)
    return _SHARED["brain"]

def understand(text: str) -> dict:
    t = (text or "").strip()
    if not t or "?" in t:
        return {}
    return {"norm": t, "social": "greet", "bases": ["greet:" + t], "fixes": []}

def is_exit(q: str) -> bool:
    return (q or "").lower().strip() in {"quit", "exit", "bye"}
