"""HEMOMO TOKEN-DIMAGH - samajhne ka dil (100% local, koi API nahi).
"""
from __future__ import annotations

import os
import re
import sys
import threading
import time
from typing import Callable, List, Optional, Tuple

from model import tokenize as tk
from model.memory import EpisodicStore, KnowledgeRetrieval

class TokenBrain:
    def __init__(self, generate_fn=None, knowledge=None, memory=None):
        self.generate_fn = generate_fn
        self.knowledge = knowledge
        self.memory = memory

    def read(self, prompt: str):
        return tk.understand(prompt)

    def respond(self, prompt: str) -> Tuple[str, dict]:
        u = self.read(prompt)
        soch = ["READ-TOKEN", "CONVERT-TO-BINARY", "READ-BY-AI", "THINK", "ANSWER"]
        # Fallback to generate_fn if available
        if self.generate_fn:
            try:
                out = self.generate_fn(prompt)
                return out, {"source": "composer", "bharosa": 0.8, "soch": soch}
            except Exception:
                pass
        return "Hemomemo AI-> Salam! Main aap ki kya madad kar sakta hoon?", {"source": "imandari", "bharosa": 0.7, "soch": soch}

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
