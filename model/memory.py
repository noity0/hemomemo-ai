"""HEMOMO MEMORY - yaad-dasht ka dil (100% local, koi API nahi).

Do hisse:
1) EpisodicStore  - guzri hui baatein yaad rakhna (JSONL, aap ke PC par)
2) KnowledgeRetrieval - Sawal:/Jawab: corpus se sab-se-mutaaliq jawab dhoondna

Koi cloud, koi embed-API, koi doosra model - NAHI. Sirf token-overlap +
recency - Hemomemo ka apna apna tareeqa.
"""
from __future__ import annotations

import json
import math
import os
import re
import threading
import time
from typing import Callable, Iterable, List, Optional, Tuple

_WORD = re.compile(r"[a-z0-9]+", re.UNICODE)
# harvest-junk pehchan (kabhi jawab na bane - "trouble accessing" waghera)
_JUNK_RX = re.compile(r"trouble accessing|unusual traffic|captcha|"
                      r"access denied|not recognized|enable javascript",
                      re.I)

def _tokens(text: str) -> List[str]:
    return _WORD.findall((text or "").lower())

# 🛡 aam-baat ke lafz (ilm ka saboot NAHI): in par 1.0 score dena hi
# "hi" → GameBot-orders / "how are you" → dictionary jaisa ghalat-jawab tha.
# 🆕 request-verbs (batao/sunao/likho/do) bhi content NAHI — warna
# "hadith batao" me "batao" match ho kar Dhikr jaisa ghalat jawab aata tha.
_STOP = {
    "a", "an", "the", "is", "are", "was", "were", "am", "be", "been",
    "i", "me", "my", "you", "your", "we", "our", "he", "she", "it", "they",
    "this", "that", "these", "those", "to", "of", "in", "on", "at", "for",
    "with", "and", "or", "but", "if", "then", "than", "so", "as", "by",
    "from", "do", "does", "did", "have", "has", "had", "can", "could",
    "will", "would", "should", "may", "might", "must", "not", "no", "yes",
    "ok", "okay", "hi", "hello", "hey", "hola", "salam", "salaam",
    "assalam", "aoa", "thanks", "thank", "please", "how", "what", "who",
    "why", "when", "where", "which", "kaise", "kya", "kaun", "kahan",
    "kab", "hai", "ho", "hun", "hoon", "hain", "ha", "hain", "ka", "ki",
    "ke", "ko", "se", "me", "mein", "mera", "meri", "mujhe", "aap", "tum",
    "tumhara", "apna", "batao", "bata", "bataiye", "bataye", "sunao",
    "suno", "likho", "likhein", "likh", "do", "dedo", "de", "dijiye",
    "karo", "karein", "kijiye", "kar", "chahiye", "chahiyay", "koi",
    "kuch", "ye", "yeh", "wo", "woh", "us", "is", "es", "par", "pr",
    "tak", "sath", "liye", "wala", "wali", "wale", "ek", "bhi", "hi",
    "hota", "hoti", "hote", "acha", "achha", "theek", "thik", "baray",
    "bare", "mutaliq", "bara", "bare", "kis", "konsa", "kaunsa",
    "karne", "karna", "karun", "karon", "sakta", "sakti", "sakte",
    "hoga", "hogi", "honge", "hua", "hui", "hue", "raha", "rahi",
    "rahe", "jay", "jaye", "ja", "mil", "mila", "mile", "dikhao",
    "dikha", "show", "tell", "give", "explain", "define", "meaning",
    "matlab", "tafseel", "detail", "about", "on", "of", "for", "any",
}


def _content_tokens(text: str) -> List[str]:
    """Sirf maani-khez lafz (request-verbs/aam-lafz nikaal kar)."""
    out = []
    for w in _tokens(text):
        if len(w) < 3:
            continue
        if w in _STOP:
            continue
        out.append(w)
    return out


def _overlap(query_toks: List[str], cand_toks: List[str]) -> float:
    """Query ke *maani-khez* lafzon ki coverage — aam lafz ginte nahi.

    Qanoon: ek akela aam/2-harf lafz kabhi ilm ka saboot nahi. Isi liye
    "hi"/"you"/"kaise ho" par corpus ka koi bhi lamba jawab match nahi hota.
    Ek 4-harf ka asli topic-lafz (misal "sabr", "quran") ab qabool hai,
    lekin sirf 0.55 score par — 5+ harf wale lafz zyada wazni hain.
    """
    if not query_toks or not cand_toks:
        return 0.0
    q = {w for w in query_toks if len(w) >= 3 and w not in _STOP}
    if not q:
        return 0.0
    c = set(cand_toks)
    hit = q & c
    if not hit:
        return 0.0
    strong = {w for w in hit if len(w) >= 5}
    if not strong:
        # sirf 3-4 harf wale hit: do hit ya akela 4-harf topic
        if len(hit) >= 2:
            return min(0.75, len(hit) / float(len(q)))
        only = next(iter(hit))
        if len(only) == 4:
            return 0.55
        return 0.0
    return len(hit) / float(len(q))  # kitne asli sawal-lafz milay


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
        bad = 0
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        bad += 1
                        continue
        except OSError:
            return []
        if bad:
            # 🛡 S6 corruption-bachaw: kharab-file ki asli-copy `.corrupt`
            #     me mehfooz (kabhi delete nahi — bande ka data salamat)
            #     aur valid-lines ke sath kaam jari rehta hai.
            try:
                bak = self.path + ".corrupt"
                if not os.path.exists(bak):
                    with open(self.path, "rb") as src, open(bak, "wb") as dst:
                        dst.write(src.read())
            except OSError:
                pass
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

    def facts(self, prefix: str, limit: int = 5) -> List[str]:
        """Token-dimagh ke liye: 'user_naam=…' jaise mehfooz haqaiq (naye pehle)."""
        out = []
        for rec in reversed(list(self._iter())):
            b = str(rec.get("bot", ""))
            if b.startswith(prefix):
                out.append(b[len(prefix):])
                if len(out) >= limit:
                    break
        return out

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
    """corpus_big ke Sawal:/Jawab: pairs me se mutaliq ilm nikalna.

    🆕 domain-routing: hadith/quran/code/game/general alag. Isi liye
    "hadith batao" ab Dhikr-jaisa random-corpus jawab nahi deta — sirf
    hadith-corpus se sahih hadith + source aata hai.
    """

    _GAME_FILES = {"games_knowledge.txt", "agent_orders.txt",
                   "gamebot_tasks.txt"}
    _DOMAIN_WORDS = {
        "hadith": {"hadith", "hadeeth", "hadees", "sunnah", "bukhari",
                   "sahih", "muslim", "tirmidhi", "nasai", "abu", "dawud",
                   "ibn", "majah", "muwatta", "nabi", "rasool", "huzoor",
                   "farmaya"},
        "quran": {"quran", "quranic", "quraan", "koran", "ayat", "ayah",
                  "surah", "sura", "parah", "juz"},
    }

    def __init__(self, corpus_dir: str, files: Optional[List[str]] = None) -> None:
        self.corpus_dir = corpus_dir
        self.files = files or ["games_knowledge.txt", "coding_knowledge.txt",
                               "coding_deep_master.txt", "harvest_live.txt",
                               "agent_orders.txt", "gamebot_tasks.txt",
                               "hadith_bukhari_english_sahih.txt",
                               "hadith_muslim_english_sahih.txt",
                               "hadith_nasai_english_sahih.txt",
                               "hadith_abudawud_english_sahih.txt",
                               "hadith_tirmidhi_english_sahih.txt",
                               "hadith_ibnmajah_english_sahih.txt",
                               "hadith_malik_english_sahih.txt",
                               "harvest_quran.txt"]
        # (sawal, jawab, file, content-token-set, lafz-tadad)
        self._pairs: List[Tuple[str, str, str, set, int]] = []
        self._index: dict = {}          # lafz → pair-indices (inverted index)
        self._loaded_from: Optional[str] = None
        self._loaded_files: set = set()
        self._df: dict = {}
        self._N = 0
        self._lock = threading.Lock()

    def _domain_files(self, domain: str) -> List[str]:
        d = (domain or "general").lower()
        hadith = [f for f in self.files if f.startswith("hadith_")]
        quran = [f for f in self.files if f == "harvest_quran.txt"]
        code = [f for f in self.files if f.startswith("coding_")]
        game = [f for f in self.files if f in self._GAME_FILES]
        general = [f for f in self.files
                   if f.startswith("coding_") or f == "harvest_live.txt"]
        if d == "hadith":
            return hadith
        if d == "quran":
            return quran
        if d == "islamic":
            return hadith + quran
        if d == "code":
            return code
        if d == "game":
            return game
        if d == "general":
            # aam ilm: GameBot orders/commands KABHI nahi
            return general
        return list(self.files)

    def _ensure(self, domain: str) -> None:
        """Sirf is domain ki files parho (pehli query tez rahe)."""
        files = self._domain_files(domain)
        with self._lock:
            if self._loaded_from != self.corpus_dir:
                self._pairs = []
                self._index = {}
                self._df = {}
                self._N = 0
                self._loaded_files = set()
                self._loaded_from = self.corpus_dir
            for fn in files:
                if fn in self._loaded_files:
                    continue
                self._loaded_files.add(fn)
                fp = os.path.join(self.corpus_dir, fn)
                if not os.path.isfile(fp):
                    continue
                try:
                    raw = open(fp, "r", encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                # 🆕 split-based parse (regex lookahead 4.6MB hadith par slow
                # tha; ye linear hai — pehli hadith-query 8s se ~1s).
                for chunk in raw.split("Sawal:")[1:]:
                    if "Jawab:" not in chunk:
                        continue
                    q, a = chunk.split("Jawab:", 1)
                    a = a.split("Sawal:", 1)[0]
                    q1 = " ".join(str(q).split())
                    a1 = " ".join(str(a).split())[:1200]
                    if not q1 or not a1 or _JUNK_RX.search(a1):
                        continue
                    # index ke liye pehle 600 harf kaafi hain (hadith ka
                    # asal bayan shuru me hota hai) — load tez + RAM kam.
                    toks = _tokens(q1 + " " + a1[:600])
                    tset = {w for w in toks
                            if len(w) >= 3 and w not in _STOP}
                    if not tset:
                        continue
                    idx = len(self._pairs)
                    self._pairs.append((q1, a1, fn, tset, max(1, len(toks))))
                    for w in tset:
                        self._df[w] = self._df.get(w, 0) + 1
                        self._index.setdefault(w, []).append(idx)
            self._N = max(1, len(self._pairs))

    def _load(self) -> None:
        self._ensure("all")

    def warmup(self) -> None:
        """Peeche-peeche (background thread) aam domains tayyar karo."""
        for d in ("general", "hadith", "quran", "code", "game"):
            try:
                self._ensure(d)
            except Exception:
                pass

    def _idf(self, w: str) -> float:
        return math.log((self._N + 1.0) / (self._df.get(w, 0) + 1.0)) + 1.0

    def _domain_match(self, fn: str, domain: str) -> bool:
        d = (domain or "general").lower()
        if d in ("all", "*"):
            return True
        if d == "hadith":
            return fn.startswith("hadith_")
        if d == "quran":
            return fn == "harvest_quran.txt"
        if d == "islamic":
            return fn.startswith("hadith_") or fn == "harvest_quran.txt"
        if d == "code":
            return fn.startswith("coding_")
        if d == "game":
            return fn in self._GAME_FILES
        # general: GameBot orders/commands aur deeni corpus alag domains
        return (not fn.startswith("hadith_")
                and fn != "harvest_quran.txt"
                and fn not in ("agent_orders.txt", "gamebot_tasks.txt"))

    def _score(self, qt: List[str], tset: set, q: str, a: str,
               wlen: int) -> float:
        if not qt or not tset:
            return 0.0
        qset = set(qt)
        hit = qset & tset
        if not hit:
            return 0.0
        strong = {w for w in hit if len(w) >= 5}
        if not strong and len(hit) < 2:
            return 0.0
        den = sum(self._idf(w) for w in qset) or 1.0
        num = sum(self._idf(w) for w in hit)
        coverage = num / den
        low = a.lower()
        phrase = " ".join(qt)
        bonus = 0.0
        if phrase and (phrase in low or phrase in q.lower()):
            bonus += 0.20
        # sawal ke title me lafz = zyada mutaliq
        title = q.lower()
        title_hit = sum(1 for w in hit if w in title)
        if title_hit:
            bonus += min(0.15, 0.15 * title_hit / float(len(hit)))
        # 🆕 lafz ki kasafat (density): chhoti hadith jo seedha topic par ho
        # usay lambi kahani se pehle rakho. Warna "sabr" par 5,000-harf
        # hadith jeet jati thi jisme patience sirf ek dafa aaya tha.
        if wlen:
            tf = sum(low.count(w) for w in hit)
            density = tf / float(wlen)
            bonus += min(0.22, density * 3.0)
        return min(1.0, coverage + bonus)

    def search_ex(self, query: str, k: int = 3,
                  domain: str = "general") -> List[Tuple[str, str, float, str]]:
        """(sawal, jawab, score, file) — domain ke andar best matches."""
        self._ensure(domain)
        qt = _content_tokens(query)
        dwords = self._DOMAIN_WORDS.get((domain or "").lower(), set())
        if dwords:
            # domain-word akela ho to generic jawab (search nahi)
            qt = [w for w in qt if w not in dwords]
        if not qt:
            return []
        # inverted index: sirf un pairs ko dekho jin me query-lafz hain
        cand = set()
        for w in qt:
            cand.update(self._index.get(w, ()))
        scored: List[Tuple[str, str, float, str]] = []
        seen = set()
        for i in cand:
            try:
                q, a, fn, tset, wlen = self._pairs[i]
            except (IndexError, ValueError):
                continue
            if not self._domain_match(fn, domain):
                continue
            sc = self._score(qt, tset, q, a, wlen)
            if sc < 0.30:
                continue
            key = a[:160]
            if key in seen:
                continue
            seen.add(key)
            scored.append((q, a, sc, fn))
        scored.sort(key=lambda p: p[2], reverse=True)
        return scored[:max(1, int(k))]

    def search(self, query: str, k: int = 3) -> List[Tuple[str, str, float]]:
        """Purana API: (sawal, jawab, score) — general domain."""
        return [(q, a, sc) for q, a, sc, _fn in
                self.search_ex(query, k=k, domain="general")]

    def generic_ex(self, domain: str) -> Optional[Tuple[str, str, float, str]]:
        """Domain ka pehla reliable pair (generic 'hadith batao' ke liye)."""
        self._ensure(domain)
        fallback = None
        for q, a, fn, tset, wlen in self._pairs:
            if not self._domain_match(fn, domain):
                continue
            if fallback is None:
                fallback = (q, a, 0.5, fn)
            if (domain or "").lower() == "hadith" and re.search(
                    r"Sahih al-Bukhari\s+1\s*:", a):
                return (q, a, 1.0, fn)
            if (domain or "").lower() == "quran" and re.search(
                    r"Quran\s+1\s*:", a):
                return (q, a, 1.0, fn)
            if fallback is not None:
                return fallback
        return fallback

    def count(self) -> int:
        self._load()
        return len(self._pairs)

    def pairs(self):
        """Token-dimagh ke liye: (sawal, jawab, tokens) ki poori suchi."""
        self._load()
        return [(q, a, sorted(tset)) for q, a, _fn, tset, _wlen in self._pairs]


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
