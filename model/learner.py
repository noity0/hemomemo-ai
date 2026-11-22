"""
📚 learner.py — AUTO-LEARNING HAR CHAT SE (verified-only, no API)

User qanoon: "AI har text/chat se khud seekhe — aur verify bhi kare."

KAISA SEEKHTA HAI (asli, imandar):
  1. SIRF TASDEEQ-SHUDA jawab yaad me jata hai:
     - algorithm/formula (conf 1.0, AST-solved)
     - live-research (verify-brain se PASS ya source-consistent)
     - yaad-se / local-knowledge / helper-soch (retrieval se, high-quality)
     - adab/samajh (deterministic rules)
     ❌ imandari/tarbiyat/grace/security → NAHI (wo 'mujhe nahi pata' hain —
        jhooti yaad banane ka jhanjhat nahi)
  2. QA-pair format me data/corpus_big/learned_chat.txt me jata hai — WAHI
     jagah jahan se chat-retrieval (yaad) parhta hai → agli dafa wahi sawal
     aaya to dimagh khud yaad se jawab dega (asli seekh — retrieval-level).
  3. Dedup (sha1) — ek hi jawab baar-baar nahi likha jata.
  4. live_research apna _remember bhi karta hai (web-jawab cache) — ye learner
     uske UPAR poori chat (sawal+asli diya gaya jawab) yaad rakhta hai.

API: learn_from_chat(prompt, answer, meta) -> dict | None ; stats()
"""
import hashlib
import os
import sys
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(HERE)
else:
    ROOT = os.path.dirname(HERE)
STORE = os.path.join(ROOT, "data", "corpus_big", "learned_chat.txt")

# in sources ke jawab hi yaad me ja sakte hain (verified/honest sirf)
_TRUSTED = {"algorithm", "formula-library", "live-research", "yaad-se",
            "local-knowledge", "helper-soch", "adab", "samajh"}
_MIN_LEN, _MAX_LEN = 25, 900
_seen = None          # lazy sha1-set


def _load_seen():
    global _seen
    if _seen is not None:
        return _seen
    _seen = set()
    try:
        with open(STORE, encoding="utf-8", errors="ignore") as f:
            for ln in f:
                if ln.startswith("# h:"):
                    _seen.add(ln[4:].strip())
    except OSError:
        pass
    return _seen


def _kws(prompt: str) -> str:
    ws = re.findall(r"[a-z0-9]{3,}", (prompt or "").lower())
    return " ".join(ws[:6]) or (prompt or "sawal")[:40]


def learn_from_chat(prompt: str, answer: str, meta: dict = None):
    """Ek chat ka verified-jawab yaad me daalo → dict (naya likha?) ya None."""
    global _seen
    meta = meta or {}
    src = str(meta.get("source", ""))
    ans = re.sub(r"\s+", " ", (answer or "")).strip()
    # "Hemomemo AI-> " prefix hatao (kora jawab chahiye)
    ans = re.sub(r"^Hemomemo AI->\s*", "", ans)
    if not prompt or not ans or len(ans) < _MIN_LEN or len(ans) > _MAX_LEN:
        return None
    # 🎯 1-2 heruf ke sawal (b/by/zz) yaad me KABHI nahi — wiktionary-trivia
    #    replay acha nahi lagta; aise sawalon ka jawab hamesha taza banta hai
    if len(str(prompt).strip()) <= 2:
        return None
    if src not in _TRUSTED:
        return None
    # verify-check: research par verify-brain ka faisla dekho (KAMZOR → nahi)
    ver = meta.get("verify")
    if isinstance(ver, dict) and ver.get("ok") is False:
        return None
    if src == "live-research" and isinstance(ver, str):
        # 🆕 web-adopted jawab ("web jawab" note) ASLI research-haqeeqat hai —
        # seekho; sirf sach-me KAMZOR research-jawab / web-bhi-khamosh skip
        if "web jawab" not in ver and ("KAMZOR" in ver or "khamosh" in ver):
            return None
    seen = _load_seen()
    h = hashlib.sha1(ans.encode("utf-8")).hexdigest()
    if h in seen:
        return None
    seen.add(h)
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    new_file = not os.path.exists(STORE)
    with open(STORE, "a", encoding="utf-8") as f:
        if new_file:
            f.write("# learned_chat.txt — AUTO-LEARNING (sirf verified jawab; "
                    "learner.py; no API)\n")
        f.write("# h: %s | %s\n" % (h[:12], time.strftime("%Y-%m-%d %H:%M")))
        f.write("Sawal: %s\n" % _kws(prompt))
        f.write("Jawab: %s\n\n" % ans)
    return {"learned": True, "source": src, "hash": h[:12], "store": STORE}


def stats() -> dict:
    """Hub ke liye — kitni asli seekh hui."""
    n = hits = 0
    try:
        with open(STORE, encoding="utf-8", errors="ignore") as f:
            for ln in f:
                if ln.startswith("# h:"):
                    n += 1
    except OSError:
        pass
    return {"learned_pairs": n, "store": "data/corpus_big/learned_chat.txt",
            "trusted_sources": sorted(_TRUSTED),
            "policy": "sirf verified/high-confidence jawab (no fake yaad)"}


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("stats:", stats())
    r = learn_from_chat("circle ka area, r = 5", "Jawab: 78.54 (A = πr²)", {
        "source": "algorithm"})
    print("learn-test:", r)
