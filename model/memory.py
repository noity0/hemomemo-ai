"""HEMOMO MEMORY - yaad-dasht ka dil (100% local, koi API nahi).

Do hisse:
1) EpisodicStore  - guzri hui baatein yaad rakhna (JSONL, aap ke PC par)
2) KnowledgeRetrieval - Sawal:/Jawab: corpus se sab-se-mutaaliq jawab dhoondna

Koi cloud, koi embed-API, koi doosra model - NAHI. Sirf token-overlap +
recency - Hemomemo ka apna apna tareeqa.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from typing import Callable, Iterable, List, Optional, Tuple

_WORD = re.compile(r"[a-z0-9]+", re.UNICODE)

def _tokens(text: str) -> List[str]:
    return _WORD.findall((text or "").lower())

def _overlap(query_toks: List[str], cand_toks: List[str]) -> float:
    if not query_toks or not cand_toks:
        return 0.0
    q = set(query_toks)
    c = set(cand_toks)
    if not q or not c:
        return 0.0
    hit = len(q & c)
    return hit / max(1.0, float(len(q)))  # kitne sawal-ke-lafz milay


class EpisodicStore:
    """Har baat (sawal+jawab) ko PC par JSONL me mehfooz karta hai.

    File: <data_dir>/memory/episodic.jsonl  (har line = ek JSON record)
    Recall: token-overlap + recency-boost (nayi yaad zyada wazni).
    """

    def __init__(self, data_dir: str, max_recall: int = 5) -> None:
        self.data_dir = data_dir
        self.mem_dir = os.path.join(data_dir, "memory")
        os.makedirs(self.mem_dir, exist_ok=True)
        self.path = os.path.join(self.mem_dir, "episodic.jsonl")
        self.max_recall = max_recall
        self._lock = threading.Lock()

    # --- yaddasht likhna ---
    def remember(self, user: str, bot: str, tag: str = "chat") -> None:
        rec = {
            "ts": time.time(),
            "iso": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tag": tag,
            "user": (user or "")[:2000],
            "bot": (bot or "")[:4000],
        }
        line = json.dumps(rec, ensure_ascii=False)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    # --- yaddasht parhna ---
    def _iter(self) -> Iterable[dict]:
        if not os.path.exists(self.path):
            return []
        out = []
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except OSError:
            return []
        return out

    def recall(self, query: str, k: Optional[int] = None) -> List[dict]:
        """Sab-se-mutaaliq purani baatein (nayi wali pehle wazni)."""
        k = k or self.max_recall
        qt = _tokens(query)
        now = time.time()
        scored: List[Tuple[float, dict]] = []
        for rec in self._iter():
            toks = _tokens(rec.get("user", "") + " " + rec.get("bot", ""))
            base = _overlap(qt, toks)
            age_h = max(0.0, (now - float(rec.get("ts", now))) / 3600.0)
            recency = 1.0 / (1.0 + age_h / 24.0)  # 24-ghante halke boost
            scored.append((base * 2.0 + recency * 0.3, rec))
        scored.sort(key=lambda p: p[0], reverse=True)
        return [rec for sc, rec in scored[:k] if sc > 0.0]

    def session_summary(self, last_n: int = 20) -> dict:
        recs = list(self._iter())[-last_n:]
        return {
            "total_memories": len(list(self._iter())),
            "shown": len(recs),
            "items": recs,
        }

    def forget_all(self) -> int:
        """Poora episodic-yad saaf (user ki marzi se)."""
        n = len(list(self._iter()))
        with self._lock:
            try:
                os.remove(self.path)
            except OSError:
                pass
        return n


class KnowledgeRetrieval:
    """corpus_big ke Sawal:/Jawab: pairs me se mutaliq ilm nikalna."""

    def __init__(self, corpus_dir: str, files: Optional[List[str]] = None) -> None:
        self.corpus_dir = corpus_dir
        self.files = files or ["games_knowledge.txt", "coding_knowledge.txt",
                               "coding_deep_master.txt", "harvest_live.txt"]
        self._pairs: List[Tuple[str, str, List[str]]] = []
        self._loaded_from: Optional[str] = None
        self._lock = threading.Lock()

    def _load(self) -> None:
        with self._lock:
            if self._loaded_from == self.corpus_dir:
                return
            pairs: List[Tuple[str, str, List[str]]] = []
            for fn in self.files:
                fp = os.path.join(self.corpus_dir, fn)
                if not os.path.isfile(fp):
                    continue
                try:
                    raw = open(fp, "r", encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                qs = re.findall(r"Sawal:\s*(.+?)\s*\nJawab:\s*(.+?)(?=\n\S|\Z)",
                                raw, re.DOTALL)
                for q, a in qs:
                    q1 = " ".join(str(q).split())
                    a1 = " ".join(str(a).split())[:1200]
                    if q1 and a1:
                        pairs.append((q1, a1, _tokens(q1 + " " + a1)))
            self._pairs = pairs
            self._loaded_from = self.corpus_dir

    def search(self, query: str, k: int = 3) -> List[Tuple[str, str, float]]:
        """(sawal, jawab, score) - sab-se-mutaaliq pehle."""
        self._load()
        qt = _tokens(query)
        if not qt:
            return []
        scored = []
        for q, a, toks in self._pairs:
            sc = _overlap(qt, toks)
            if sc > 0.0:
                scored.append((q, a, sc))
        scored.sort(key=lambda p: p[2], reverse=True)
        return scored[:k]

    def count(self) -> int:
        self._load()
        return len(self._pairs)


def make_answer_fn(generate_fn: Optional[Callable[[str], str]] = None,
                   knowledge: Optional[KnowledgeRetrieval] = None,
                   memory: Optional[EpisodicStore] = None) -> Callable[[str], str]:
    """Local answer pipeline: retrieval-context + apna dimagh (generate_fn).

    generate_fn = Hemomemo ka apna composer (model.generate). Koi bhi
    bahar-ki AI yahan KABHI nahi lagti - agar na ho to retrieval-based
    jawab hi kaafi samjha diya jata hai (honest mode).
    """
    def answer(prompt: str) -> str:
        ctx_bits: List[str] = []
        if knowledge is not None:
            for q, a, _sc in knowledge.search(prompt, k=2):
                ctx_bits.append(a)
        if generate_fn is not None:
            try:
                out = generate_fn(prompt)
                if out and out.strip():
                    if ctx_bits:
                        return out.strip() + "\n\n" + ctx_bits[0][:400]
                    return out.strip()
            except Exception:
                pass
        if ctx_bits:
            return ctx_bits[0][:800]
        return ""
    return answer
