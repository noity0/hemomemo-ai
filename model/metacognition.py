"""
🪞 metacognition.py — INTROSPECTIVE SELF-DOUBT (apni hi soch par nazar)

Kya karta hai:
  Har jawab dene ke BAAD brain khud apna jawab monitor karta hai (soch:
  "kya jo maine kaha wo sach tha? kitna bharosa hai?"):
    - SOURCE ka behtareen-laikin: yaad-se = kitab-corpus ka asli copy
      (Quran/Hadith verified) → sab kam-doubt
    - live-research = whitelist-net ka fresh text → thora doubt
    - khud-soch = jawaan model ka apna text → sab zyada doubt
    - imaandari/tarbiyat = "nahi janta" khulasa
  Signals (0..1):
    relevance (sawal-jawab match), yaad-score, lambai/safai,
    fabrication-risk (nakli ayat/hadith = foran shak)
    → DOUBT score + VERDICT (pak-yakeen / kamzor / shak)
  Agli dafa 'shak' par: generate.py jawab upgrade karta hai (yaad/grace).

Log: data/meta_thoughts.jsonl  (har metacog-soch ka record — hub status me)
"""
import hashlib
import json
import os
import re
import sys
import time

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LOG_PATH = os.path.join(ROOT, "data", "meta_thoughts.jsonl")
_MAX_LOG = 5000

_NEAR_SHORT = re.compile(r"[.!?]")
# 🪞 self-instrument signals: jawab apne sim-dekhne ko batao
_SOURCE_DOUBT = {
    "yaad-se":       0.08,   # kitab ka asli copy — verified
    "live-research": 0.22,   # whitelist-net, fresh ilm
    "khud-soch":     0.32,   # jawaan model ka apna
    "imaandari":     0.60,   # "nahi janta" — imandari magar kam-ilm
    "tarbiyat":      0.55,
}


def _counters():
    try:
        n = 0
        with open(LOG_PATH, encoding="utf-8", errors="ignore") as f:
            n = sum(1 for _ in f)
        return {"thoughts": n, "log": os.path.relpath(LOG_PATH, ROOT)}
    except OSError:
        return {"thoughts": 0, "log": os.path.relpath(LOG_PATH, ROOT)}


def _log_thought(rec):
    """Chhota append-only log (rotates around _MAX_LOG)."""
    try:
        if os.path.exists(LOG_PATH) and _counters()["thoughts"] >= _MAX_LOG:
            os.remove(LOG_PATH)
    except OSError:
        pass
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def evaluate(prompt: str, answer: str, source: str,
             yaad_top: float = 0.0, relevance: float = -1.0):
    """Jawab ki khud-janch (0..1 doubt). Returns:
    {doubt, verdict, action, signals:{...}} — verdict:
      pak-yakeen (<0.25) | kamzor (0.25..0.55) | shak (>0.55)"""
    answer = answer or ""
    src = source if source in _SOURCE_DOUBT else "khud-soch"
    doubt = _SOURCE_DOUBT[src]

    rel = relevance
    if rel < 0:
        qs = set(re.findall(r"[a-z]{2,}", (prompt or "").lower()))
        ts = set(re.findall(r"[a-z]{2,}", answer.lower()))
        rel = (len(qs & ts) / len(qs)) if qs else 0.0
    if rel < 0.20:
        doubt += 0.25
    elif rel < 0.35:
        doubt += 0.10
    if src == "yaad-se" and yaad_top >= 0.30:
        doubt -= 0.08                       # kitab-corpus ne khud support ki

    plain = len(_NEAR_SHORT.split(answer)) if _NEAR_SHORT.search(answer) else 0
    if src == "khud-soch" and len(answer) < 70:
        doubt += 0.20
    if src == "khud-soch" and plain <= 1 and len(answer) < 110:
        doubt += 0.15
    # fabrication-risk guard (nakli ayat/hadith) — sakht shak
    try:
        from model.generate import _no_citation
        if not _no_citation(answer):
            doubt += 0.50
    except Exception:
        pass

    doubt = max(0.0, min(1.0, round(doubt, 3)))
    if doubt < 0.25:
        verdict, action = "pak-yakeen", "ok"
    elif doubt <= 0.55:
        verdict, action = "kamzor", "ok (rehqat mein behtar)"
    else:
        verdict, action = "shak", "dobara soch / yaad ya grace se pak jawab"

    signs = {"source_doubt": _SOURCE_DOUBT[src], "relevance": round(rel, 2),
             "yaad_top": round(yaad_top, 2), "chars": len(answer)}
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
           "prompt": (prompt or "")[:60], "source": src,
           "doubt": doubt, "verdict": verdict, **signs}
    _log_thought(rec)
    return {"doubt": doubt, "verdict": verdict, "action": action,
            "signals": signs, "prompt_sha": hashlib.sha1(
                (prompt or "").encode('utf-8', "ignore")).hexdigest()[:8]}


if __name__ == "__main__":
    r = evaluate("sabr kya hai", "Sabr is patience: stay calm.", "yaad-se",
                 0.6)
    print(r)
    print(_counters())
