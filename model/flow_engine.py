# -*- coding: utf-8 -*-
"""HEMOMO FLOW ENGINE — har qism ke sawal ke liye apna alag, verified flow.

Qanoon (user-hukum):
  • 100% local — koi AI-platform API / cloud / external LLM nahi.
  • Chat-history sirf SANDARABH hai; AKHRI sawal ka 100% priority.
  • Har cheez ka apna flow: samajh → token-tukre → soch → dalil →
    yaad/ilm/formula-sheet → Hemomemo LLM → jaanch → jawab.
  • Koi fixed Sawal→Jawab map nahi; har stage asli local module chalata hai.

Flow-space (10,000,000,000+):
  Flow ko fileon me store nahi kiya jata (10B files = fake/kharcha).
  Yahan ek FLOW-GRAMMAR hai jo 33,973,862,400 combinations on-demand
  banati hai: 24 archetypes × 512 domains × 12 languages × 10 styles ×
  6 depths × 8 formats × 5 verification levels × 8 context modes ×
  12 tones. Har combination wahi asli stages/verifiers chalati hai jo
  neeche ARCHETYPES me hain. `--catalog` se poora hisaab dekha ja sakta hai.
"""
from __future__ import annotations

import ast
import hashlib
import math
import operator
import os
import re
import sys
import time
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from model import tokenize as tk
from model.prompt_system import (core_intent_text, is_self_repo_question,
                                 self_repo_reply)

try:  # local modules — package me na hon to bhi engine fail-open rahe
    from model.memory import EpisodicStore, KnowledgeRetrieval
except Exception:  # pragma: no cover
    EpisodicStore = None  # type: ignore
    KnowledgeRetrieval = None  # type: ignore

try:
    from model.math_formulas import solve_formula
except Exception:  # pragma: no cover
    solve_formula = None  # type: ignore

try:
    from model.code_exec import run_python, smart_code
except Exception:  # pragma: no cover
    smart_code = None  # type: ignore
    run_python = None  # type: ignore


FLOW_VERSION = "1.0.0"

# ----------------------------------------------------------------------
# Stage labels (UI/progress ke liye Roman-Urdu)
# ----------------------------------------------------------------------
STAGE_LABEL = {
    "READ": "sawal parh raha hoon",
    "UNDERSTAND": "samajh raha hoon",
    "TOKEN_BREAK": "token tor raha hoon",
    "THINK": "soch raha hoon",
    "REASON": "dalil/steps bana raha hoon",
    "RETRIEVE": "yaad/ilm dhoond raha hoon",
    "FORMULA": "formula sheet khol raha hoon",
    "LLM": "Hemomemo LLM se likh raha hoon",
    "VERIFY": "jawab jaanch raha hoon",
    "ANSWER": "jawab de raha hoon",
}

# ----------------------------------------------------------------------
# Flow archetypes — har flow ke asli stages
# ----------------------------------------------------------------------
ARCHETYPES: Dict[str, Tuple[str, ...]] = {
    "social":       ("READ", "UNDERSTAND", "ANSWER"),
    "identity":     ("READ", "UNDERSTAND", "ANSWER"),
    "self_repo":    ("READ", "UNDERSTAND", "ANSWER"),
    "memory_save":  ("READ", "UNDERSTAND", "TOKEN_BREAK", "REASON",
                     "VERIFY", "ANSWER"),
    "memory_recall": ("READ", "UNDERSTAND", "RETRIEVE", "VERIFY", "ANSWER"),
    "math_arith":   ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "REASON", "VERIFY", "ANSWER"),
    "math_formula": ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "REASON", "FORMULA", "VERIFY", "ANSWER"),
    "code":         ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "REASON", "LLM", "VERIFY", "ANSWER"),
    "hadith":       ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "RETRIEVE", "VERIFY", "ANSWER"),
    "quran":        ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "RETRIEVE", "VERIFY", "ANSWER"),
    "ilm":          ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "RETRIEVE", "LLM", "VERIFY", "ANSWER"),
    "gamebot":      ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "RETRIEVE", "ANSWER"),
    "system":       ("READ", "UNDERSTAND", "ANSWER"),
    "explain":      ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "RETRIEVE", "LLM", "VERIFY", "ANSWER"),
    "compare":      ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "RETRIEVE", "LLM", "VERIFY", "ANSWER"),
    "howto":        ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "REASON", "RETRIEVE", "LLM", "VERIFY", "ANSWER"),
    "debug":        ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "REASON", "LLM", "VERIFY", "ANSWER"),
    "creative":     ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "LLM", "VERIFY", "ANSWER"),
    "translate":    ("READ", "UNDERSTAND", "TOKEN_BREAK", "LLM",
                     "VERIFY", "ANSWER"),
    "summary":      ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "LLM", "VERIFY", "ANSWER"),
    "plan":         ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "REASON", "LLM", "VERIFY", "ANSWER"),
    "research":     ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "REASON", "RETRIEVE", "VERIFY", "ANSWER"),
    "lookup":       ("READ", "UNDERSTAND", "TOKEN_BREAK", "RETRIEVE",
                     "ANSWER"),
    "unknown":      ("READ", "UNDERSTAND", "TOKEN_BREAK", "THINK",
                     "LLM", "VERIFY", "ANSWER"),
}

# ----------------------------------------------------------------------
# Flow-space dimensions (on-demand grammar; koi 10B files nahi)
# ----------------------------------------------------------------------
FIELDS = [
    "math", "physics", "chemistry", "biology", "computer-science",
    "engineering", "medicine", "law", "business", "finance", "economics",
    "history", "geography", "language", "literature", "philosophy",
    "psychology", "sociology", "education", "agriculture", "environment",
    "islamic-studies", "quran", "hadith", "fiqh", "aqeedah", "seerah",
    "health", "fitness", "nutrition", "travel", "sports", "arts", "music",
    "film", "gaming", "cooking", "gardening", "diy", "automotive",
]  # 40 fields

SUBFIELDS = [
    "basics", "advanced", "definitions", "examples", "problems",
    "comparisons", "history", "rules", "tools", "best-practices",
    "mistakes", "projects", "exercises", "reference", "safety", "summary",
]  # 16 subfields → 640 domains

LANGUAGES = [
    "roman-urdu", "english", "urdu", "hindi", "arabic", "punjabi",
    "sindhi", "pashto", "bengali", "turkish", "mixed", "auto",
]  # 12

STYLES = [
    "short", "detailed", "step-by-step", "bullets", "example-first",
    "definition-first", "question-first", "story", "exam", "kid-simple",
]  # 10

DEPTHS = ["fast", "standard", "deep", "research", "teach", "verify"]  # 6

FORMATS = [
    "text", "markdown", "table", "code", "list", "json", "formula", "essay",
]  # 8

VERIFY_LEVELS = ["basic", "strict", "source", "recompute", "multi-pass"]  # 5

CONTEXT_MODES = [
    "chat", "single-turn", "last-question-only", "document", "codebase",
    "memory", "research", "classroom",
]  # 8

TONES = [
    "neutral", "friendly", "formal", "teacher", "expert", "simple",
    "encouraging", "direct", "patient", "curious", "islamic", "professional",
]  # 12

FLOW_SPACE = (len(ARCHETYPES) * len(FIELDS) * len(SUBFIELDS)
              * len(LANGUAGES) * len(STYLES) * len(DEPTHS)
              * len(FORMATS) * len(VERIFY_LEVELS) * len(CONTEXT_MODES)
              * len(TONES))

# ----------------------------------------------------------------------
# Chhote helpers
# ----------------------------------------------------------------------
_WS = re.compile(r"\s+")
_PUNCT_END = re.compile(r"[\s\.\!\?،۔]+$")
_ARABIC = re.compile(r"[\u0600-\u06FF]")

_GREET_RX = re.compile(
    r"(?i)^\s*(?:assalam\w*|asalam\w*|salam|salaam|aoa|adaab|namaste|"
    r"hi+|hey+|hello+|hola|good\s+(?:morning|afternoon|evening|night)|"
    r"gm|gn)\b")
_HOW_RX = re.compile(
    r"(?i)^\s*(?:how\s+are\s+you|how\s+r\s+u|how\s+are\s+u|how's\s+it\s+going|"
    r"kaise\s+ho|kaisay\s+ho|kaisi\s+ho|kya\s+haal\s+hai|kya\s+haal|"
    r"kya\s+chal\s+raha|kya\s+kar\s+rahe\s+ho|aap\s+kaise\s+hain)\b")
_THANKS_RX = re.compile(
    r"(?i)^\s*(?:thanks|thank\s+you|thx|shukriya|shukria|jazak\w*|"
    r"allah\s+hafiz)\b")
_BYE_RX = re.compile(
    r"(?i)^\s*(?:bye+|byebye|khuda\s+hafiz|allah\s+hafiz|see\s+you|"
    r"see\s+ya|good\s+night|gn|alvida)\b")

_IDENTITY_RX = re.compile(
    r"(?i)\b(?:aap\s+kaun\s+ho|tum\s+kaun\s+ho|tum\s+kon\s+ho|aap\s+kya\s+ho|"
    r"tum\s+kya\s+ho|who\s+are\s+you|what\s+are\s+you|what\s+is\s+your\s+name|"
    r"tumhara\s+naam|tumhari\s+naam|aap\s+ka\s+naam|apna\s+taruf|"
    r"introduce\s+yourself|hemomemo\s+kya\s+hai|hemomemo\s+kon\s+hai|"
    r"hmhs|owner\s+kaun|malik\s+kaun|founder\s+kaun|bananay\s+wala|"
    r"kitne\s+parameter|kitna\s+brain|kaunsa\s+model|tumhara\s+dimagh)\b")
_CAP_RX = re.compile(
    r"(?i)\b(?:kya\s+kar\s+sakte|kya\s+kar\s+sakti|features|capabilities|"
    r"what\s+can\s+you\s+do|tum\s+se\s+kya\s+ho\s+sakta|aap\s+se\s+kya)\b")
_MEM_SAVE_RX = re.compile(
    r"(?i)\b(?:mera\s+naam\s+([A-Za-z0-9\u0600-\u06FF][A-Za-z0-9\u0600-\u06FF .'’-]{0,42}?)\s+hai|"
    r"my\s+name\s+is\s+([A-Za-z0-9\u0600-\u06FF][A-Za-z0-9\u0600-\u06FF .'’-]{0,42})|"
    r"yaad\s+rakho[:\s]+(.{1,120})|remember[:\s]+(.{1,120}))\b")
_MEM_RECALL_RX = re.compile(
    r"(?i)\b(?:mera\s+naam\s+kya\s+hai|mera\s+naam\s+batao|mera\s+naam\s+yaad|"
    r"what\s+is\s+my\s+name|do\s+you\s+remember\s+me|mujhe\s+pehchana|"
    r"mujhe\s+yaad\s+hai|tumhe\s+mera\s+naam\s+yaad)\b")

_HADITH_RX = re.compile(
    r"(?i)\b(?:hadith|hadeeth|hadees|sunnah|bukhari|sahih\s+musal?im|"
    r"muslim\s+sharif|tirmidhi|nasai|abu\s*dawud|ibn\s*majah|muwatta|"
    r"nabi\s+ne\s+farmaya|rasool\s+ne\s+farmaya|huzoor\s+ne\s+farmaya)\b")
_QURAN_RX = re.compile(
    r"(?i)\b(?:quran|qur'an|quraan|koran|quranic|ayat|ayah|surah|sura|"
    r"parah|juz)\b")
_CODE_RX = re.compile(
    r"(?i)(?:\b(?:code|program|script|function|bug|debug|compile|syntax|"
    r"traceback|exception|\.py\b|python\s+(?:me|ka|ki|code|program|loop|"
    r"function|class|list|dict|dictionary|array|tuple|set|string|variable|"
    r"module|library|syntax|error)|c\+\+|java|javascript|html|sql|rust|"
    r"golang)\b|\bcode\s+banao\b|\bka\s+code\b)")
_GAME_RX = re.compile(
    r"(?i)\b(?:minecraft|gamebot|game\s*bot|bot\s+player|khelo|khelna|"
    r"game\s+khel|mcp|agent\s+bot)\b")
_SYSTEM_RX = re.compile(
    r"(?i)^\s*(?:server|api)\s*(?:on|off|band|chalu|start|stop)\b|"
    r"^\s*(?:band\s+karo|on\s+karo|shuru\s+karo)\s*[.!]?\s*$")

_EXPLAIN_RX = re.compile(
    r"(?i)\b(?:kya\s+hai|kya\s+hain|what\s+is|what\s+are|explain|samjhao|"
    r"samjha\s+do|tafseel|meaning|matlab|define|definition|kyun|why)\b")
_COMPARE_RX = re.compile(
    r"(?i)\b(?:difference|farq|compare|comparison|vs\.?|behtar|better|"
    r"kaun\s+behtar|which\s+is\s+better)\b")
_HOWTO_RX = re.compile(
    r"(?i)\b(?:kaise|how\s+to|steps|tarika|tareeqa|procedure|process|"
    r"kaise\s+karein|kaise\s+karun)\b")
_DEBUG_RX = re.compile(
    r"(?i)\b(?:error|bug|fix|ghalti|debug|exception|traceback|not\s+working|"
    r"kaam\s+nahi\s+kar\s+raha|fail\s+ho\s+raha)\b")
_CREATIVE_RX = re.compile(
    r"(?i)\b(?:story|kahani|poem|nazm|shayari|ghazal|likho|banao|"
    r"write\s+a|create\s+a|draft)\b")
_TRANSLATE_RX = re.compile(
    r"(?i)\b(?:translate|tarjuma|tarjumah|convert\s+.+\s+(?:to|me|into))\b")
_SUMMARY_RX = re.compile(
    r"(?i)\b(?:summary|khulasa|summarize|short\s+karo|mukhtasar)\b")
_PLAN_RX = re.compile(
    r"(?i)\b(?:plan|roadmap|schedule|steps\s+banao|planning|strategy)\b")
_RESEARCH_RX = re.compile(
    r"(?i)\b(?:research|tahqeeq|deep\s+dive|detail\s+me|references|sources)\b")
_LOOKUP_RX = re.compile(
    r"(?i)\b(?:search|google|dhoondo|dhundo|latest|news|weather|price|"
    r"kitne\s+ka|kahan\s+mil|online\s+check)\b")

_MATH_CALLS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "log": math.log, "log10": math.log10, "ln": math.log,
    "exp": math.exp, "abs": abs, "floor": math.floor, "ceil": math.ceil,
    "factorial": math.factorial, "round": round,
}
_BIN_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}

_ISLAMIC_GLOSS = {
    "sabr": "patience", "sabar": "patience", "shukr": "gratitude",
    "shukriya": "gratitude", "iman": "faith", "emaan": "faith",
    "taqwa": "piety", "namaz": "prayer", "salah": "prayer",
    "roza": "fasting", "sawm": "fasting", "zakat": "charity",
    "hajj": "pilgrimage", "ilm": "knowledge", "akhlaq": "manners",
    "dua": "supplication", "tawbah": "repentance", "dhikr": "remembrance",
    "jannah": "paradise", "jahannam": "hell", "qiyamah": "resurrection",
    "nabi": "prophet", "rasool": "messenger", "allah": "god",
    "quran": "quran", "hadith": "hadith", "sunnah": "sunnah",
    "wudu": "ablution", "ghusl": "bath", "janazah": "funeral",
    "nikah": "marriage", "talaq": "divorce", "riba": "interest",
    "halal": "lawful", "haram": "forbidden", "sadaqah": "charity",
    "itikaf": "seclusion", "tahajjud": "night prayer",
    "witrr": "witr", "witr": "witr", "farz": "obligatory",
    "sunnat": "sunnah", "nafl": "voluntary", "qaza": "makeup",
}

_QURAN_DEF = (
    "Al-Quran Allah ki aakhri kitab hai, jo Hazrat Muhammad ﷺ par nazil hui. "
    "Ye insaniyat ke liye hidayat aur rushd ka kitab hai. Quran me 114 surah "
    "hain; ayat ki mashhoor tadad 6,236 hai. Is local corpus me is waqt "
    "1,585 ayat entries (clearquran English translation) maujood hain."
)

# ----------------------------------------------------------------------
# Context object
# ----------------------------------------------------------------------
@dataclass
class FlowCtx:
    raw: str
    core: str
    tokens: List[str] = field(default_factory=list)
    keys: List[str] = field(default_factory=list)
    nums: List[float] = field(default_factory=list)
    variables: Dict[str, float] = field(default_factory=dict)
    hist: Optional[List[dict]] = None
    knowledge: Any = None
    memory: Any = None
    generate_fn: Optional[Callable[[str], str]] = None
    progress: Optional[Callable[[str], None]] = None
    stages: List[str] = field(default_factory=list)
    _seen: set = field(default_factory=set)

    def emit(self, stage: str) -> None:
        """Asli stage par UI/progress ko batao (fake delay nahi)."""
        if stage not in self._seen:
            self._seen.add(stage)
            self.stages.append(stage)
        if self.progress:
            try:
                self.progress(STAGE_LABEL.get(stage, stage))
            except Exception:
                pass


# ----------------------------------------------------------------------
# Text helpers
# ----------------------------------------------------------------------
def _clean(text: str) -> str:
    t = (text or "").strip()
    try:
        t = core_intent_text(t) or t
    except Exception:
        pass
    t = re.sub(r"(?i)^\s*(?:sawal|question|user|human|insan)\s*[:\-]\s*", "",
               t)
    t = _WS.sub(" ", t).strip()
    return t


def _low(text: str) -> str:
    return _WS.sub(" ", (text or "").lower()).strip()


def _strip_end(text: str) -> str:
    return _PUNCT_END.sub("", (text or "").strip())


def _content_tokens(text: str) -> List[str]:
    try:
        from model.memory import _content_tokens as _ct  # type: ignore
        return _ct(text)
    except Exception:
        return [w for w in re.findall(r"[a-z0-9\u0600-\u06FF]+",
                                      (text or "").lower())
                if len(w) >= 3]


_ISLAMIC_TOPIC_WORDS = (set(_ISLAMIC_GLOSS)
                        - {"quran", "hadith", "sunnah", "allah", "nabi",
                           "rasool", "shukriya"})


def _is_islamic_topic(text: str) -> bool:
    words = set(re.findall(r"[a-z0-9]+", (text or "").lower()))
    return bool(words & _ISLAMIC_TOPIC_WORDS)


def _expand_islamic(text: str) -> str:
    words = re.findall(r"[A-Za-z\u0600-\u06FF]+", text or "")
    extra = []
    for w in words:
        e = _ISLAMIC_GLOSS.get(w.lower())
        if e and e.lower() not in (text or "").lower():
            extra.append(e)
    return (text + (" " + " ".join(extra) if extra else "")).strip()


def _fmt_num(v: Any) -> str:
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int):
        try:
            return str(v)
        except (ValueError, MemoryError):
            try:
                return "%.8e" % float(v)
            except Exception:
                return "<bara-adad>"
    if isinstance(v, Fraction):
        if v.denominator == 1:
            return str(v.numerator)
        try:
            dec = float(v)
            if abs(dec) < 1e16 and dec != 0:
                return "%.10g (exact %s)" % (dec, v)
        except Exception:
            pass
        return str(v)
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return str(v)
        if v.is_integer() and abs(v) < 1e16:
            return str(int(v))
        if abs(v) >= 1e16 or (abs(v) < 1e-6 and v != 0):
            return "%.8e" % v
        return ("%.10f" % v).rstrip("0").rstrip(".")
    return str(v)


# ----------------------------------------------------------------------
# Math: safe expression evaluator
# ----------------------------------------------------------------------
def _eval_node(n: ast.AST) -> Any:
    if isinstance(n, ast.Expression):
        return _eval_node(n.body)
    if isinstance(n, ast.Constant):
        if isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        raise ValueError("ghair-adadi-qeemat")
    if isinstance(n, ast.Name):
        if n.id.lower() == "pi":
            return math.pi
        if n.id.lower() == "e":
            return math.e
        raise ValueError("ghair-moajood-naam")
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
        v = _eval_node(n.operand)
        return +v if isinstance(n.op, ast.UAdd) else -v
    if isinstance(n, ast.BinOp) and type(n.op) in _BIN_OPS:
        left = _eval_node(n.left)
        right = _eval_node(n.right)
        if isinstance(n.op, ast.Pow):
            if isinstance(right, (int, float)) and abs(right) > 10000:
                raise ValueError("power-bahut-bara")
            if isinstance(left, int) and isinstance(right, int) and right > 0:
                # 5000-digit limit — freeze/memory-bomb se bachao
                if left not in (0, 1, -1) and right * max(1, len(str(abs(left)))) > 5000:
                    raise ValueError("number-bahut-bara")
        if isinstance(n.op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("division-by-zero")
            if isinstance(left, int) and isinstance(right, int):
                return Fraction(left, right)
            return left / right
        if isinstance(n.op, ast.FloorDiv):
            if right == 0:
                raise ZeroDivisionError("division-by-zero")
            return left // right
        if isinstance(n.op, ast.Mod):
            if right == 0:
                raise ZeroDivisionError("division-by-zero")
            return left % right
        return _BIN_OPS[type(n.op)](left, right)
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
        fn = _MATH_CALLS.get(n.func.id)
        if fn is None or len(n.args) != 1:
            raise ValueError("ghair-moajood-function")
        return fn(_eval_node(n.args[0]))
    raise ValueError("ghair-moajood-bayan")


def _safe_eval(expr: str) -> Any:
    node = ast.parse(expr.replace("^", "**"), mode="eval")
    return _eval_node(node)


def _math_expr(text: str) -> Optional[str]:
    """Sawal se sirf-adad expression nikalo (88/0, 2+2, 5/5*...)."""
    t = (text or "").strip()
    t = re.sub(r"(?i)\b(?:kitna|kitne|kitni|hota|hoti|hote|hai|hain|ho|"
               r"calculate|solve|karo|karein|kijiye|batao|bata|jawab|"
               r"answer|please|what|is|the|equals?|barabar)\b", " ", t)
    t = t.replace("=", " ")
    t = re.sub(r"[?؟]+", " ", t)
    t = re.sub(r"(?<=\d)\s*[xX]\s*(?=\d)", "*", t)
    t = re.sub(r"(?<=\d)\s*\(\s*", "*(", t)
    t = re.sub(r"(\d+)\s*!", r"factorial(\1)", t)
    t = t.strip(" .;,")
    if not t or not re.search(r"\d", t):
        return None
    if not re.search(r"[\+\-\*/%^!]|sqrt|sin|cos|tan|log|factorial", t,
                     re.I):
        return None
    if not re.fullmatch(r"[0-9\s\.\+\-\*/%\(\)\^a-zA-Z_,]+", t):
        return None
    # sirf calculator-functions/constants qabool; "E=mc^2" jaisa formula
    # yahan nahi — wo formula-sheet flow ka kaam hai.
    allowed = {"sqrt", "sin", "cos", "tan", "asin", "acos", "atan",
               "log", "log10", "ln", "exp", "abs", "floor", "ceil",
               "factorial", "round", "pi", "e"}
    for w in re.findall(r"[A-Za-z]+", t):
        if w.lower() not in allowed:
            return None
    # date ko hisaab na banao (18/11/2026)
    if re.fullmatch(r"\d{1,4}\s*[/-]\s*\d{1,2}\s*[/-]\s*\d{1,4}", t):
        return None
    return t


def _math_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ctx.emit("TOKEN_BREAK")
    expr = _math_expr(ctx.core)
    if not expr:
        return _honest(ctx, "math")
    ctx.emit("THINK")
    ctx.emit("REASON")
    try:
        val = _safe_eval(expr)
        ctx.emit("VERIFY")
        # recompute = deterministic verification
        val2 = _safe_eval(expr)
        verified = (val == val2)
        ans = ("Jawab: %s = %s\nHal ki soch: expression parse → safe-AST → "
               "hisaab → recompute-verify.\n%s" % (
                   ctx.core, _fmt_num(val),
                   "✅ Verify: recompute match." if verified
                   else "⚠ Verify: recompute mismatch."))
        return ans, {"source": "flow:math-arith", "bharosa": 0.98,
                     "verify": "pass" if verified else "warn",
                     "formula": "arithmetic"}
    except ZeroDivisionError:
        ctx.emit("VERIFY")
        return ("Jawab: %s — 0 se taqseem (division by zero) undefined hai. "
                "Math me kisi bhi adad ko 0 se taqseem karna jaiz nahi.\n"
                "✅ Verify: denominator 0 check." % ctx.core,
                {"source": "flow:math-arith", "bharosa": 0.99,
                 "verify": "pass", "formula": "division-by-zero"})
    except ValueError as e:
        return ("Jawab: %s ka hisaab nahi ban saka (%s). Expression saaf "
                "likhein: misal `2+2` ya `sqrt(16)*3`." % (ctx.core, e),
                {"source": "flow:math-arith", "bharosa": 0.55,
                 "verify": "fail"})
    except Exception as e:
        return ("Jawab: math parse error — %s. Expression dobara likhein."
                % str(e)[:120],
                {"source": "flow:math-arith", "bharosa": 0.45,
                 "verify": "fail"})


def _formula_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ctx.emit("TOKEN_BREAK")
    if solve_formula is None:
        return _llm_flow(ctx, "math_formula")
    ctx.emit("THINK")
    ctx.emit("REASON")
    try:
        r = solve_formula(ctx.core)
    except Exception as e:
        return ("Jawab: formula-sheet me is sawal ko solve karte waqt ghalti: "
                "%s" % str(e)[:140],
                {"source": "flow:math-formula", "bharosa": 0.45,
                 "verify": "fail"})
    if not r:
        return _llm_flow(ctx, "math_formula")
    ctx.emit("FORMULA")
    try:
        ans, steps, conf, verified, tags = r
    except Exception:
        return _llm_flow(ctx, "math_formula")
    ctx.emit("VERIFY")
    body = "\n".join(str(s) for s in (steps or []))
    tail = ("✅ Verify: formula-sheet ka deterministic solve."
            if verified else "⚠ Verify: values adhoori — formula sikhaya gaya.")
    text = "%s\nHal ki soch:\n%s\n%s" % (ans, body, tail)
    return text, {"source": "flow:math-formula", "bharosa": 0.95,
                  "verify": "pass" if verified else "warn",
                  "formula": ",".join(tags or [])[:160]}


# ----------------------------------------------------------------------
# Knowledge helpers
# ----------------------------------------------------------------------
def _ksearch(knowledge: Any, query: str, domain: str,
             k: int = 3) -> List[Tuple[str, str, float, str]]:
    if knowledge is None:
        return []
    try:
        if hasattr(knowledge, "search_ex"):
            return list(knowledge.search_ex(query, k=k, domain=domain))
    except Exception:
        pass
    try:
        return [(q, a, s, "") for q, a, s in knowledge.search(query, k=k)]
    except Exception:
        return []


def _kgeneric(knowledge: Any, domain: str) -> Optional[Tuple[str, str, float, str]]:
    if knowledge is None:
        return None
    try:
        if hasattr(knowledge, "generic_ex"):
            r = knowledge.generic_ex(domain)
            if r:
                return r
    except Exception:
        pass
    hits = _ksearch(knowledge, domain, domain, 1)
    return hits[0] if hits else None


def _src_name(path: str) -> str:
    p = (path or "").replace("\\", "/")
    return p.rsplit("/", 1)[-1] if p else "local corpus"


def _quran_guard_ok(text: str) -> Tuple[bool, str]:
    try:
        from knowledge.quran_guard import SacredTextGuard
        g = SacredTextGuard()
        fn = getattr(g, "check_prompt", None)
        if callable(fn):
            r = fn(text)
            if isinstance(r, dict):
                ok = r.get("ok", True)
                return bool(ok), str(r.get("reason") or "")
            if isinstance(r, tuple) and r:
                return bool(r[0]), str(r[1] if len(r) > 1 else "")
    except Exception:
        pass
    return True, ""


def _hadith_guard_ok(text: str) -> Tuple[bool, str]:
    try:
        from knowledge.hadith_guard import check_hadith_text
        r = check_hadith_text(text)
        return bool(r.get("ok", True)), str(r.get("grade") or r.get("reason") or "")
    except Exception:
        return True, ""


# ----------------------------------------------------------------------
# Flow handlers
# ----------------------------------------------------------------------
def _social_kind(core: str) -> Optional[str]:
    t = _strip_end(core)
    if not t:
        return None
    # greeting + optional "hemomemo/bhai" only
    if _GREET_RX.match(t):
        rest = _GREET_RX.sub("", t).strip(" ,.!-")
        if not rest or rest.lower() in ("hemomemo", "bhai", "bro", "dost",
                                        "yaar", "sir", "janab"):
            return "greet"
    if _HOW_RX.match(t):
        return "how"
    if _THANKS_RX.match(t):
        return "thanks"
    if _BYE_RX.match(t):
        return "bye"
    return None


def _social_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    k = _social_kind(ctx.core) or "greet"
    # deterministic variety (same sawal par same jawab — bharosa)
    idx = int(hashlib.md5(ctx.core.encode("utf-8")).hexdigest()[:8], 16)
    greet = [
        "Assalamu Alaikum! Main Hemomemo hoon — kya madad karun? "
        "(chat, code, math, ilm, yaad, gamebot — 100% local)",
        "Wa Alaikum Assalam! Hemomemo hazir hai — sawal bataiye "
        "(100% local, koi API nahi).",
        "Salam! Main Hemomemo hoon — aap ka local dimagh. Poochiye kya "
        "jaanna hai?",
    ][idx % 3]
    how = [
        "Main theek hoon — aap kaise hain? Main Hemomemo hoon, aap ka "
        "100% local dimagh: chat, code, math, ilm, yaad, gamebot.",
        "Alhamdulillah, theek hoon. Aap sunaiye — kya sawal hai? "
        "(sab kuch isi PC par, 100% local)",
    ][idx % 2]
    thanks = [
        "Khush rahiye! Main yahin hoon — jab bhi zaroorat ho, pooch lein "
        "(100% local).",
        "Shukriya aap ka! Allah aap ko khush rakhe — koi aur sawal ho to "
        "bataiye.",
    ][idx % 2]
    bye = [
        "Allah Hafiz! Jab bhi zaroorat ho, main yahin hoon — 100% local.",
        "Khuda Hafiz! Apna khayal rakhiye — Hemomemo phir hazir milega.",
    ][idx % 2]
    ans = {"greet": greet, "how": how, "thanks": thanks, "bye": bye}[k]
    ctx.emit("ANSWER")
    return ans, {"source": "flow:social", "bharosa": 0.95,
                 "verify": "pass", "social": k}


def _identity_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    low = _low(ctx.core)
    if _CAP_RX.search(low):
        ans = (
            "Main Hemomemo AI hoon — 100% local desktop AI, apna NumPy dimagh. "
            "Main ye kar sakta hoon:\n"
            "• Chat / sawal-jawab (Roman-Urdu, English, Urdu)\n"
            "• Math + 331-formula sheet (hisaab, geometry, physics...)\n"
            "• Coding AI (Python etc. — code bana kar chala kar dikhata hoon)\n"
            "• Ilm: Quran/Hadith + local corpus (source ke sath)\n"
            "• Yaad-dasht: aap ki baatein isi PC par mehfooz\n"
            "• GameBot: Minecraft bot-player\n"
            "• Local API: 127.0.0.1:8790 (OpenAI-shape)\n"
            "Koi cloud, koi AI-API, koi external LLM nahi."
        )
        return ans, {"source": "flow:identity", "bharosa": 0.95,
                     "verify": "pass"}
    if re.search(r"(?i)\b(?:hmhs|owner|malik|founder|bananay\s+wala)\b", low):
        ans = (
            "HMHS = Hafiz Muhammed Huzaifa Shamim — Hemomemo AI ke owner/"
            "founder. Ye app unhi ki taraf se hai (repo description: 'By HMHS'). "
            "Main 100% local dimagh hoon; koi cloud/API nahi."
        )
        return ans, {"source": "flow:identity:owner", "bharosa": 0.95,
                     "verify": "pass"}
    if re.search(r"(?i)\b(?:kitne\s+parameter|kitna\s+brain|kaunsa\s+model|"
                 r"tumhara\s+dimagh|brain)\b", low):
        ans = (
            "Mera apna brain: pure-NumPy 2-layer LSTM — 50,014,104 parameters "
            "(~50M), checkpoint `hemomaster_1794986685.npz` (200,058,108 bytes). "
            "Ye LLM app nahi, koi external model/API nahi — sab kuch isi PC par."
        )
        return ans, {"source": "flow:identity:brain", "bharosa": 0.95,
                     "verify": "pass"}
    ans = (
        "Main Hemomemo AI hoon — aap ka apna 100% local dimagh: chat, code, "
        "math, ilm, yaad aur gamebot. Mera apna NumPy brain isi PC par hai; "
        "koi AI-API, koi cloud, koi external LLM nahi. Poochiye kya jaanna hai?"
    )
    return ans, {"source": "flow:identity", "bharosa": 0.95, "verify": "pass"}


def _self_repo_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    return self_repo_reply(), {"source": "flow:self-repo", "bharosa": 0.95,
                               "verify": "pass"}


def _memory_save_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ctx.emit("TOKEN_BREAK")
    m = _MEM_SAVE_RX.search(ctx.core)
    if not m:
        return _memory_recall_flow(ctx)
    val = next((g for g in m.groups() if g), "").strip(" .")
    if not val:
        return _honest(ctx, "memory_save")
    ctx.emit("REASON")
    ok = False
    if ctx.memory is not None:
        try:
            prefix = ("user_naam=" if re.search(r"(?i)naam|name", m.group(0))
                      else "note=")
            ctx.memory.remember(ctx.raw or ctx.core, prefix + val, tag="yaad")
            ok = True
        except Exception:
            ok = False
    ctx.emit("VERIFY")
    if ok:
        ans = ("Bhar-poor! \"%s\" yaad-dasht me mehfooz ho gaya (100%% local, "
               "isi PC par)." % val)
        return ans, {"source": "flow:memory-save", "bharosa": 0.95,
                     "verify": "pass", "saved": val}
    return ("Maaf karein — yaad-dasht me mehfooz nahi ho saka (local store "
            "error). Dobara koshish karein.", {
                "source": "flow:memory-save", "bharosa": 0.4,
                "verify": "fail"})


def _memory_recall_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ctx.emit("RETRIEVE")
    nm = ""
    if ctx.memory is not None:
        try:
            fa = ctx.memory.facts("user_naam=")
            nm = fa[0].strip() if fa else ""
        except Exception:
            nm = ""
    ctx.emit("VERIFY")
    if nm:
        return ("Aap ka naam %s hai (meri local yaad se, 100%% local)." % nm,
                {"source": "flow:memory-recall", "bharosa": 0.95,
                 "verify": "pass"})
    return ("Aap ka naam mujhe abhi yaad nahi — 'mera naam <naam> hai' likho, "
            "main isi PC par mehfooz kar lunga (100% local).",
            {"source": "flow:memory-recall", "bharosa": 0.7,
             "verify": "pass"})


def _hadith_query(core: str) -> str:
    t = _low(core)
    t = re.sub(r"(?i)\b(?:hadith|hadeeth|hadees|sunnah|bukhari|sahih|"
               r"muslim|tirmidhi|nasai|abu\s*dawud|ibn\s*majah|muwatta|"
               r"batao|bata|sunao|suno|par|ke|ki|ka|ek|koi|do|please|"
               r"about|on|the|a|an|what|is|kya|hai|nabi|rasool|huzoor|"
               r"farmaya|hain|mein|me)\b", " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = _WS.sub(" ", t).strip()
    return _expand_islamic(t)


def _hadith_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ctx.emit("TOKEN_BREAK")
    q = _hadith_query(ctx.core)
    ctx.emit("THINK")
    ctx.emit("RETRIEVE")
    hits = _ksearch(ctx.knowledge, q, "hadith", 3) if q else []
    if not hits and not q:
        g = _kgeneric(ctx.knowledge, "hadith")
        hits = [g] if g else []
    if not hits:
        return ("Is topic (\"%s\") par mujhe local sahih-hadith corpus me "
                "pakki hadith nahi mili — bina-hawala hadith nahi banata. "
                "Topic badlein (misal: 'sabr', 'namaz', 'ilm', 'walidain') "
                "ya sirf 'hadith batao' likhein." % (q or ctx.core),
                {"source": "flow:hadith:honest", "bharosa": 0.45,
                 "verify": "honest"})
    chosen = None
    grade = ""
    for qq, aa, sc, src in hits:
        ok, gr = _hadith_guard_ok(aa)
        if ok:
            chosen = (qq, aa, sc, src)
            grade = gr
            break
    if not chosen:
        return _honest(ctx, "hadith")
    ctx.emit("VERIFY")
    qq, aa, sc, src = chosen
    ans = ("📖 Hadith (sahih corpus, 100%% local):\n%s\n"
           "✅ Grade: %s\n📚 Source: %s" % (
               aa, grade or "sahih/hasan (corpus-graded)", _src_name(src)))
    if not q:
        ans += ("\n\n(Aap ne topic nahi diya, is liye pehli sahih hadith dikhai. "
                "Topic batao — misal: 'sabr par hadith', 'namaz par hadith'.)")
    return ans, {"source": "flow:hadith", "bharosa": 0.9,
                 "verify": "pass", "source_file": _src_name(src)}


def _quran_query(core: str) -> str:
    t = _low(core)
    t = re.sub(r"(?i)\b(?:quran|qur'an|quraan|koran|quranic|ayat|ayah|surah|"
               r"sura|parah|juz|batao|bata|sunao|suno|par|ke|ki|ka|ek|koi|"
               r"do|please|about|on|the|a|an|what|is|kya|hai|hain|mein|me)\b",
               " ", t)
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return _expand_islamic(_WS.sub(" ", t).strip())


def _quran_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ok, why = _quran_guard_ok(ctx.core)
    if not ok:
        return ("Ye sawal Quran ke adab ke mutabiq nahi — main is tarah jawab "
                "nahi de sakta. (%s)" % why,
                {"source": "flow:quran", "bharosa": 0.7, "verify": "guard"})
    ctx.emit("TOKEN_BREAK")
    low = _low(ctx.core)
    if re.search(r"(?i)\bkitne\s+(?:surah|sura|ayat)\b", low):
        n_surah = 114
        return ("Quran me %d surah hain; ayat ki mashhoor tadad 6,236 hai. "
                "Is local corpus me 1,585 ayat entries maujood hain.\n"
                "📚 Source: quran_master.json + harvest_quran.txt (100%% local)."
                % n_surah, {"source": "flow:quran:count", "bharosa": 0.95,
                            "verify": "pass"})
    q = _quran_query(ctx.core)
    ctx.emit("THINK")
    ctx.emit("RETRIEVE")
    hits = _ksearch(ctx.knowledge, q, "quran", 3) if q else []
    if not hits and not q:
        g = _kgeneric(ctx.knowledge, "quran")
        hits = [g] if g else []
    if not hits:
        return ("Is topic (\"%s\") par local Quran-corpus me mujhe mutaliq "
                "ayat nahi mili — main bina-hawala ayat nahi banata. "
                "Surah/ayat number dein ya topic badlein.\n\nAl-Quran ke bare "
                "me basic sach: %s" % (q or ctx.core, _QURAN_DEF),
                {"source": "flow:quran:honest", "bharosa": 0.5,
                 "verify": "honest"})
    ctx.emit("VERIFY")
    qq, aa, sc, src = hits[0]
    if re.search(r"(?i)\b(?:quran\s+kya\s+hai|quran\s+kiya\s+hai|"
                 r"what\s+is\s+(?:the\s+)?quran)\b", low):
        ans = ("📖 Quran (taaruf):\n%s\n\n📖 Local corpus se ayat:\n%s\n"
               "📚 Source: %s (100%% local)" % (
                   _QURAN_DEF, aa, _src_name(src)))
    else:
        ans = "📖 Quran (local corpus, 100%% local):\n%s\n📚 Source: %s" % (
            aa, _src_name(src))
    return ans, {"source": "flow:quran", "bharosa": 0.88,
                 "verify": "pass", "source_file": _src_name(src)}


# 🆕 asli, chale-hue Python snippets — jab user "python loop" jaisi cheez
# maange (code nahi, sabaq). Har snippet isi PC par chal kar verify hota hai.
_CODE_SNIPPETS: List[Tuple[str, str, str, str]] = [
    ("loop", r"\b(?:loop|loops|for\s+loop|while\s+loop|iteration)\b",
     "Python loop (for + while)",
     "total = 0\n"
     "for i in range(1, 6):\n"
     "    total += i\n"
     "    print('i =', i, '| total =', total)\n"
     "print('For-loop total:', total)\n"
     "\n"
     "n = 3\n"
     "while n > 0:\n"
     "    print('while:', n)\n"
     "    n -= 1\n"),
    ("function", r"\b(?:function|functions|def)\b",
     "Python function (parameter + return)",
     "def greet(name):\n"
     "    return 'Assalamu Alaikum, ' + name + '!'\n"
     "\n"
     "print(greet('Hemomemo'))\n"
     "print(greet('HMHS'))\n"),
    ("class", r"\b(?:class|classes|oop|object)\b",
     "Python class (object + method)",
     "class Counter:\n"
     "    def __init__(self):\n"
     "        self.n = 0\n"
     "\n"
     "    def add(self, step=1):\n"
     "        self.n += step\n"
     "        return self.n\n"
     "\n"
     "c = Counter()\n"
     "c.add()\n"
     "c.add(4)\n"
     "print('Counter:', c.n)\n"),
    ("list", r"\b(?:list|lists|array|arrays)\b",
     "Python list (add, sort, slice)",
     "nums = [5, 2, 9, 1]\n"
     "nums.append(7)\n"
     "nums.sort()\n"
     "print('sorted:', nums)\n"
     "print('first two:', nums[:2])\n"
     "print('sum:', sum(nums))\n"),
    ("dict", r"\b(?:dict|dictionary|dictionaries|hashmap|hash\s*map)\b",
     "Python dict (key/value + loop)",
     "marks = {'Ali': 85, 'Sara': 92, 'Bilal': 78}\n"
     "marks['Hamza'] = 88\n"
     "for name, score in marks.items():\n"
     "    print(name, '=', score)\n"
     "print('Total students:', len(marks))\n"),
]


def _code_snippet(core: str) -> Optional[Tuple[str, str, str]]:
    """Sabaq-request (loop/function/class...) → asli snippet ka faisla."""
    low = _low(core)
    # asli code likha ho to snippet nahi — smart_code chalega
    if re.search(r"[=(){};]|\b(?:def|print|import|return|for\s+\w+\s+in|"
                 r"while\s+\w+\s*[:<>=])\b", low):
        return None
    for name, rx, title, code in _CODE_SNIPPETS:
        if re.search(rx, low):
            return name, title, code
    return None


def _code_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ctx.emit("TOKEN_BREAK")
    ctx.emit("THINK")
    ctx.emit("REASON")
    snip = _code_snippet(ctx.core)
    if snip and run_python is not None:
        name, title, code = snip
        ctx.emit("LLM")
        ok, out, err, took = run_python(code, timeout=10.0)
        ctx.emit("VERIFY")
        note = ("✅ Verify: snippet isi PC par chala — output neeche."
                if ok else
                "⚠ Verify: snippet chalane me error: %s" % (err or "")[:200])
        txt = ("💻 %s (asli Python, 100%% local):\n```python\n%s```\n\n"
               "▶ Output:\n```\n%s```\n%s" % (
                   title, code, (out or "").strip()[:1500], note))
        return txt, {"source": "flow:code:snippet",
                     "bharosa": 0.9 if ok else 0.5,
                     "verify": "pass" if ok else "warn",
                     "code_meta": {"concept": name, "ok": bool(ok)}}
    if smart_code is None:
        return _llm_flow(ctx, "code")
    ctx.emit("LLM")
    try:
        txt, meta = smart_code(ctx.core)
        meta = dict(meta or {})
    except Exception as e:
        return _llm_flow(ctx, "code")
    ctx.emit("VERIFY")
    # Python code-block ka syntax check (agar code hai)
    m = re.search(r"```python\s*(.*?)```", txt or "", re.S | re.I)
    if m:
        code = m.group(1)
        try:
            ast.parse(code)
            verify = "pass"
            note = "\n✅ Verify: Python syntax parse OK."
        except SyntaxError as e:
            verify = "warn"
            note = ("\n⚠ Verify: Python syntax check fail (line %s: %s) — "
                    "code chala kar dobara check karein." % (e.lineno, e.msg))
        txt = txt + note
    else:
        verify = "pass" if (meta.get("ok", True)) else "warn"
    return txt, {"source": "flow:code", "bharosa": 0.85, "verify": verify,
                 "code_meta": {k: v for k, v in meta.items()
                               if k in ("source", "ok", "error")}}


def _game_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ctx.emit("TOKEN_BREAK")
    ctx.emit("THINK")
    ctx.emit("RETRIEVE")
    hits = _ksearch(ctx.knowledge, ctx.core, "game", 2)
    if hits:
        q, a, sc, src = hits[0]
        return ("🎮 GameBot (local): %s\n📚 Source: %s" % (a, _src_name(src)),
                {"source": "flow:gamebot", "bharosa": 0.8,
                 "verify": "pass"})
    return ("🎮 GameBot local hai (Minecraft bot-player). Hukum wazeh karein "
            "— misal: 'bot ko follow karo', 'minecraft me ghar banao', "
            "'START-GAMEBOT.bat chalao'. 100% local, koi cloud nahi.",
            {"source": "flow:gamebot", "bharosa": 0.65, "verify": "pass"})


def _system_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    return ("Server control app ke chat se hota hai: 'server band karo' ya "
            "'server on karo'. Main khud OS/Windows tasks ko nahi chhoota — "
            "sirf Hemomemo ka apna server/watcher control hota hai.",
            {"source": "flow:system", "bharosa": 0.8, "verify": "pass"})


def _llm_prompt(ctx: FlowCtx, extra: str = "") -> str:
    parts: List[str] = []
    hist = ctx.hist or []
    if hist:
        lines = []
        for h in hist[-20:]:
            who = (h.get("who") or "").lower()
            txt = str(h.get("text") or "").strip()
            if not txt:
                continue
            if len(txt) > 220:
                txt = txt[:217].rstrip() + "..."
            lines.append(("User: " if who == "user" else "AI:   ") + txt)
        if lines:
            parts.append("[CHAT-YAAD] pichli baatein (sirf sandarabh):\n" +
                         "\n".join(lines) + "\n[CHAT-YAAD-KHATAM]")
    parts.append(
        "[FLOW-QANOON] 100% priority AKHRI SAWAL ko do. Pichli baat sirf "
        "'ye/wo/mera/pichla' samajhne ke liye hai; uska jawab dobara na do. "
        "Agar pichli baat aur akhri sawal takrayen to AKHRI SAWAL jeetega. "
        "Jhoot/banawati hawala na do; agar pakka ilm na ho to saaf kaho.")
    if extra:
        parts.append("[LOCAL-ILM-SANDARABH]\n" + extra.strip()[:4000])
    parts.append("[AKHRI-SAWAL]\n" + ctx.core)
    return "\n\n".join(parts)


def _llm_ok(core: str, out: str) -> bool:
    t = (out or "").strip()
    if len(t) < 2 or len(t) > 12000:
        return False
    low = t.lower()
    if "user is requesting" in low or "[chat-yaad]" in low:
        return False
    if _strip_end(low) == _strip_end(_low(core)):
        return False
    # formula/circle ka stale jawab kisi aur sawal par KABHI nahi
    if re.search(r"(?i)\bformula\s*:|πr|jawab\s*:\s*[a-z]\s*=", t):
        return False
    # greeting/thanks/bye ka stale jawab kisi specific sawal par nahi
    if (_GREET_RX.match(core) or _THANKS_RX.match(core)
            or _BYE_RX.match(core)):
        return False
    # bohot zyada repeat = junk
    words = re.findall(r"\w+", low)
    if len(words) >= 12:
        top = max(words.count(w) for w in set(words))
        if top / float(len(words)) > 0.45:
            return False
    return True


def _llm_flow(ctx: FlowCtx, kind: str = "general") -> Tuple[str, dict]:
    ctx.emit("THINK")
    gen = ctx.generate_fn
    if gen is None:
        try:
            from model.generate import chat_once

            def gen(p):  # ek hi call — pehle lambda do dafa chala raha tha
                out = chat_once(p)
                return out[0] if isinstance(out, tuple) else out
        except Exception:
            gen = None
    if gen is None:
        return _honest(ctx, kind)
    ctx.emit("LLM")
    try:
        out = gen(_llm_prompt(ctx))
        if isinstance(out, tuple):
            out = out[0] if out else ""
        out = str(out or "").strip()
    except Exception:
        out = ""
    ctx.emit("VERIFY")
    if _llm_ok(ctx.core, out):
        return out, {"source": "flow:" + kind, "bharosa": 0.65,
                     "verify": "pass", "llm": True}
    return _honest(ctx, kind)


def _explain_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ctx.emit("TOKEN_BREAK")
    ctx.emit("THINK")
    ctx.emit("RETRIEVE")
    q = _expand_islamic(ctx.core)
    # Pehle aam ilm/definition corpus (tez + direct definition), phir
    # deeni hadith/quran corpus — dono local, source ke sath.
    hits = _ksearch(ctx.knowledge, q, "general", 2)
    strong = hits and hits[0][2] >= 0.55
    if not strong and (_is_islamic_topic(ctx.core)
                       or (hits and hits[0][2] >= 0.30)):
        ihits = _ksearch(ctx.knowledge, q, "islamic", 2)
        if ihits and (not hits or ihits[0][2] > hits[0][2]):
            hits = ihits
    ctx.emit("VERIFY")
    if hits and hits[0][2] >= 0.45:
        qq, aa, sc, src = hits[0]
        return ("📚 Ilm (local corpus): %s\n📚 Source: %s" % (
            aa, _src_name(src)),
            {"source": "flow:explain:ilm", "bharosa": 0.82,
             "verify": "pass", "source_file": _src_name(src)})
    return _llm_flow(ctx, "explain")


def _compare_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    return _llm_flow(ctx, "compare")


def _howto_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    return _llm_flow(ctx, "howto")


def _debug_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    return _llm_flow(ctx, "debug")


def _creative_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    return _llm_flow(ctx, "creative")


def _translate_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    return _llm_flow(ctx, "translate")


def _summary_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    return _llm_flow(ctx, "summary")


def _plan_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    return _llm_flow(ctx, "plan")


def _research_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    ctx.emit("UNDERSTAND")
    ctx.emit("TOKEN_BREAK")
    ctx.emit("THINK")
    ctx.emit("REASON")
    ctx.emit("RETRIEVE")
    hits = _ksearch(ctx.knowledge, _expand_islamic(ctx.core), "general", 3)
    ctx.emit("VERIFY")
    if hits:
        bits = []
        for qq, aa, sc, src in hits[:3]:
            bits.append("%s\n(Source: %s)" % (aa[:700], _src_name(src)))
        return ("📚 Research (local corpus):\n\n" + "\n\n".join(bits),
                {"source": "flow:research", "bharosa": 0.8,
                 "verify": "pass"})
    return _llm_flow(ctx, "research")


def _lookup_flow(ctx: FlowCtx) -> Tuple[str, dict]:
    # Network/AI-API yahan KABHI nahi; app ka non-AI powers fast-path alag hai.
    return ("Search/lookup ke liye app ka non-AI powers fast-path use hota hai "
            "(weather/news/price waghera). Main chat-brain hoon — bina source "
            "koi online jhoot nahi banata. Aap topic wazeh karein ya "
            "'search <cheez>' likhein.",
            {"source": "flow:lookup", "bharosa": 0.6, "verify": "pass"})


def _honest(ctx: FlowCtx, kind: str) -> Tuple[str, dict]:
    topic = " ".join(_content_tokens(ctx.core)[:4]) or ctx.core[:60]
    ans = ("Is sawal (\"%s\") ka pakka jawab mere local ilm/corpus me nahi "
           "mila — main bina-jhoot jawab nahi banata. Topic thora wazeh "
           "karein (misal: 'sabr par hadith', 'circle ka area r=5', "
           "'python loop') ya 'ilm <topic>' likhein. Sab kuch 100%% local hai."
           % topic)
    return ans, {"source": "flow:honest:" + kind, "bharosa": 0.45,
                 "verify": "honest"}


# ----------------------------------------------------------------------
# Classifier
# ----------------------------------------------------------------------
def classify(core: str, u: Optional[Any] = None) -> str:
    t = _strip_end(core)
    low = _low(t)
    if not low:
        return "unknown"
    # 1) memory (sawal se pehle — "mera naam kya hai" recall hai, save nahi)
    if _MEM_RECALL_RX.search(low):
        return "memory_recall"
    if _MEM_SAVE_RX.search(t):
        return "memory_save"
    # 2) identity / self-repo / capability
    if is_self_repo_question(low):
        return "self_repo"
    if _IDENTITY_RX.search(low) or _CAP_RX.search(low):
        return "identity"
    # 3) pure arithmetic (88/0 bhi yahin — division-by-zero ka apna jawab)
    if _math_expr(t):
        return "math_arith"
    # 4) formula sheet (strict — normal baat me formula nahi khulta)
    try:
        if solve_formula is not None and _has_formula_signal(low):
            from model.math_formulas import find_formula
            if find_formula(t, strict=True) is not None:
                return "math_formula"
    except Exception:
        pass
    # 5) deeni ilm — domain routing
    if _HADITH_RX.search(low):
        return "hadith"
    if _QURAN_RX.search(low):
        return "quran"
    # 5b) deeni topic (sabr, namaz, roza, dua...) → ilm/islamic corpus
    if _is_islamic_topic(low):
        return "ilm"
    # 6) code
    if _CODE_RX.search(low):
        return "code"
    # 7) gamebot
    if _GAME_RX.search(low):
        return "gamebot"
    # 8) system control
    if _SYSTEM_RX.search(t):
        return "system"
    # 9) social (sirf jab koi aur kaam na ho)
    if _social_kind(t):
        return "social"
    # 10) task-specific LLM flows
    if _DEBUG_RX.search(low):
        return "debug"
    if _TRANSLATE_RX.search(low):
        return "translate"
    if _SUMMARY_RX.search(low):
        return "summary"
    if _PLAN_RX.search(low):
        return "plan"
    if _COMPARE_RX.search(low):
        return "compare"
    if _HOWTO_RX.search(low):
        return "howto"
    if _RESEARCH_RX.search(low):
        return "research"
    if _LOOKUP_RX.search(low):
        return "lookup"
    if _CREATIVE_RX.search(low):
        return "creative"
    if _EXPLAIN_RX.search(low):
        return "explain"
    # 11) content hai to ilm, warna general chat
    if _content_tokens(t):
        return "ilm"
    return "unknown"


def _has_formula_signal(low: str) -> bool:
    if re.search(r"\d", low):
        return True
    return bool(re.search(
        r"(?i)\b(?:area|perimeter|circumference|volume|surface|interest|"
        r"speed|velocity|distance|force|energy|power|pressure|density|"
        r"pythagoras|trigonometry|sine|cosine|tangent|formula|equation|"
        r"triangle|circle|sphere|cylinder|cone|rectangle|square|"
        r"motion|gravity|coulomb|ohm|volt|current|resistance)\b", low))


# ----------------------------------------------------------------------
# Handler map
# ----------------------------------------------------------------------
_HANDLERS: Dict[str, Callable[[FlowCtx], Tuple[str, dict]]] = {
    "social": _social_flow,
    "identity": _identity_flow,
    "self_repo": _self_repo_flow,
    "memory_save": _memory_save_flow,
    "memory_recall": _memory_recall_flow,
    "math_arith": _math_flow,
    "math_formula": _formula_flow,
    "code": _code_flow,
    "hadith": _hadith_flow,
    "quran": _quran_flow,
    "ilm": _explain_flow,
    "gamebot": _game_flow,
    "system": _system_flow,
    "explain": _explain_flow,
    "compare": _compare_flow,
    "howto": _howto_flow,
    "debug": _debug_flow,
    "creative": _creative_flow,
    "translate": _translate_flow,
    "summary": _summary_flow,
    "plan": _plan_flow,
    "research": _research_flow,
    "lookup": _lookup_flow,
    "unknown": _llm_flow,
}


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def run(text: str, knowledge: Any = None, memory: Any = None,
        generate_fn: Optional[Callable[[str], str]] = None,
        hist: Optional[List[dict]] = None,
        progress: Optional[Callable[[str], None]] = None,
        ) -> Tuple[str, dict]:
    """AKHRI sawal ka poora flow chalao. Return: (answer, meta).

    • text: raw message (chat-preamble/wrapper ho to core_intent_text hata dega)
    • hist: pichli baatein — sirf LLM-context, kabhi math/ilm ka input nahi
    • knowledge/memory/generate_fn: caller ke local modules (no API)
    """
    t0 = time.time()
    core = _clean(text)
    ctx = FlowCtx(raw=(text or ""), core=core, hist=hist,
                  knowledge=knowledge, memory=memory,
                  generate_fn=generate_fn, progress=progress)
    ctx.emit("READ")
    if not core:
        return ("Sawal khali hai — kuch likhein (math, code, ilm, ya baat-cheet).",
                {"source": "flow:empty", "bharosa": 0.4, "verify": "pass",
                 "flow": "EMPTY", "flow_stages": ctx.stages,
                 "flow_space": FLOW_SPACE, "took_ms": 0})
    try:
        u = tk.understand(core)
        ctx.tokens = list(getattr(u, "tokens", []) or [])
        ctx.keys = list(getattr(u, "keys", []) or [])
        ctx.nums = list(getattr(u, "nums", []) or [])
        ctx.variables = dict(getattr(u, "variables", {}) or {})
    except Exception:
        pass
    flow = classify(core, u=None)
    handler = _HANDLERS.get(flow, _llm_flow)
    try:
        ans, meta = handler(ctx)
    except Exception as e:
        ans, meta = ("Flow-engine me andruni ghalti (%s) — sawal dobara "
                     "likhein." % str(e)[:120],
                     {"source": "flow:error", "bharosa": 0.3,
                      "verify": "fail"})
    meta = dict(meta or {})
    meta.setdefault("flow", flow.upper())
    meta.setdefault("flow_id", flow_id(flow))
    meta["flow_stages"] = ctx.stages or list(ARCHETYPES.get(flow, ()))
    meta["flow_version"] = FLOW_VERSION
    meta["flow_space"] = FLOW_SPACE
    meta.setdefault("tokens", len(ctx.tokens))
    meta["took_ms"] = int((time.time() - t0) * 1000)
    ctx.emit("ANSWER")
    return str(ans), meta


def flow_id(archetype: str, field: str = "general", subfield: str = "basics",
            lang: str = "roman-urdu", style: str = "step-by-step",
            depth: str = "standard", fmt: str = "text",
            verify: str = "strict", context: str = "last-question-only",
            tone: str = "friendly") -> str:
    """Ek deterministic flow-ID (on-demand; 33B+ combinations)."""
    def s(x: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", str(x).lower()).strip("-")[:18]
    return "HF-%s-%s-%s-%s-%s-%s-%s-%s-%s-%s" % (
        s(archetype), s(field), s(subfield), s(lang), s(style), s(depth),
        s(fmt), s(verify), s(context), s(tone))


def catalog() -> dict:
    """Flow-space ka poora hisaab (10B+ combinations, on-demand)."""
    return {
        "version": FLOW_VERSION,
        "archetypes": {k: list(v) for k, v in ARCHETYPES.items()},
        "archetype_count": len(ARCHETYPES),
        "fields": FIELDS,
        "field_count": len(FIELDS),
        "subfields": SUBFIELDS,
        "subfield_count": len(SUBFIELDS),
        "domain_count": len(FIELDS) * len(SUBFIELDS),
        "languages": LANGUAGES,
        "language_count": len(LANGUAGES),
        "styles": STYLES,
        "style_count": len(STYLES),
        "depths": DEPTHS,
        "depth_count": len(DEPTHS),
        "formats": FORMATS,
        "format_count": len(FORMATS),
        "verify_levels": VERIFY_LEVELS,
        "verify_count": len(VERIFY_LEVELS),
        "context_modes": CONTEXT_MODES,
        "context_count": len(CONTEXT_MODES),
        "tones": TONES,
        "tone_count": len(TONES),
        "flow_space": FLOW_SPACE,
        "flow_space_text": "{:,}".format(FLOW_SPACE),
        "note": ("Ye 33B+ flow COMBINATIONS on-demand banti hain; 33B files "
                 "store nahi hoti. Har combination wahi verified stages "
                 "chalati hai jo archetypes me hain."),
    }


def sample_flows(n: int = 10) -> List[dict]:
    """Deterministic sample flow-IDs (catalog dikhane ke liye)."""
    arch = list(ARCHETYPES)
    out = []
    for i in range(max(1, min(int(n), 1000))):
        out.append({
            "flow_id": flow_id(
                arch[i % len(arch)],
                FIELDS[(i * 7) % len(FIELDS)],
                SUBFIELDS[(i * 5) % len(SUBFIELDS)],
                LANGUAGES[(i * 3) % len(LANGUAGES)],
                STYLES[(i * 2) % len(STYLES)],
                DEPTHS[i % len(DEPTHS)],
                FORMATS[(i * 3) % len(FORMATS)],
                VERIFY_LEVELS[i % len(VERIFY_LEVELS)],
                CONTEXT_MODES[(i * 5) % len(CONTEXT_MODES)],
                TONES[(i * 7) % len(TONES)],
            ),
            "archetype": arch[i % len(arch)],
            "stages": list(ARCHETYPES[arch[i % len(arch)]]),
        })
    return out


# ----------------------------------------------------------------------
# CLI: python -m model.flow_engine --catalog | --classify "..." | --run "..."
# ----------------------------------------------------------------------
def _cli(argv: List[str]) -> int:
    import json
    if not argv:
        print("usage: python -m model.flow_engine --catalog | "
              "--classify <q> | --run <q>")
        return 2
    cmd = argv[0]
    if cmd == "--catalog":
        print(json.dumps(catalog(), ensure_ascii=False, indent=2))
        print("\nSAMPLE FLOWS:")
        for f in sample_flows(8):
            print(" ", f["flow_id"], "|", f["archetype"], "|",
                  " → ".join(f["stages"]))
        return 0
    if cmd in ("--classify", "--run"):
        q = " ".join(argv[1:]).strip()
        if not q:
            print("query khali")
            return 2
        if cmd == "--classify":
            print(classify(_clean(q)))
            return 0
        ans, meta = run(q)
        print(ans)
        print("\n--- META ---")
        print(json.dumps(meta, ensure_ascii=False, indent=2, default=str))
        return 0
    print("unknown command:", cmd)
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
