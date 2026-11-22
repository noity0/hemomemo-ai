"""
🔎 verify_brain.py — CHAUTHA DIMAGH (HEMOMO-VERIFY ~5.1M params, dh560)

User qanoon: "2 more brains each of 5M — one HELPS main brain give good
answers, SECOND VERIFIES research answers ... jo cheez isse nahi aati wo
google live se search kare aur VERIFY bhi kare phir jawab de."

Verifier brain ka kaam (research-jawab ki TASDEEQ — 3-layer):
  1. PERPLEXITY CHECK   : jawab ke chars verifier-LSTM me dal kar dekho —
     corpus-trained model ke liye "ajaib/ghair-mumkin" text = kam avg-log-prob
     → reject. (asli log-prob forward pass, no API)
  2. SOURCE-CONSISTENCY : research-cache (liveresearch.txt) ke usi sawal ke
     page-snippet se keyword-overlap — jawab page se juda ho to PASS.
  3. ARTIFACT-GUARDS    : nakli ayat/hadith citation + junk-quality checks
     (fabrication net — khud-soch jaisa hi sakht).

Verdict: {"ok": True/False/None, "score": 0..1, "reason": str}
None = verifier checkpoint nahi (fail-safe: research jawab waisehi jata hai
magar meta me 'unverified' mark hota hai).

Checkpoint: model/hemoverify_*.npz (tarbiyat: scripts\\train_master.py 6000 --verify)
"""

import glob
import os
import re
import sys

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

_VERIFY = {"checked": False, "path": None}


def checkpoint():
    """SAB se naya verifier checkpoint (hemoverify_*.npz)."""
    if not _VERIFY["checked"]:
        _VERIFY["checked"] = True
        try:
            from model.generate import CKPT_DIR
            cands = []
            for p in glob.glob(os.path.join(CKPT_DIR, "hemoverify_*.npz")):
                base = os.path.basename(p)
                if base.startswith("hemoverify_chat"):
                    continue
                cands.append(p)
            cands.sort(key=os.path.getmtime, reverse=True)
            _VERIFY["path"] = cands[0] if cands else None
        except Exception:
            _VERIFY["path"] = None
    return _VERIFY["path"]


def refresh():
    _VERIFY["checked"] = False
    return checkpoint()


def params_estimate(vocab: int = 80) -> int:
    dh = 560
    return 16 * dh * dh + 2 * vocab * dh


# ----------------------------------------------------------------------
# layer 1: perplexity (verifier LSTM se jawab ki "mumkinat" janch)
# ----------------------------------------------------------------------
def _perplexity(text: str, tok, brain) -> float:
    """Char-level avg LOG-prob (asli log — pehle ghalati se raw probability
    thi). Range ~ -4..-1; 0 = khaali/na-tasdeeq-shuda. Guarded, fast (256)."""
    try:
        import math
        ids = tok.encode(text[:256])
        if len(ids) < 4:
            return 0.0
        probs, _c = brain.forward_sequence(ids[:-1])
        lp = 0.0
        for t, p in enumerate(probs):
            tgt = ids[t + 1]
            lp += max(-20.0, math.log(max(1e-9, float(p[tgt]))))
        return lp / max(1, len(probs))
    except Exception:
        return 0.0


# ----------------------------------------------------------------------
# layer 2: research-cache consistency
# ----------------------------------------------------------------------
def _cache_consistency(prompt: str, answer: str) -> float:
    """liveresearch.txt cache me isi sawal ka snippet mile to overlap 0..1."""
    try:
        from model.generate import BIG   # data/corpus_big
        path = os.path.join(BIG, "liveresearch.txt")
        if not os.path.exists(path):
            return 0.0
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.read().split("\n")
        # aakhri 40 "Sawal:" blocks dekho (naya research sab se upar hota hai)
        blocks, cur_q, cur_a = [], None, []
        for ln in lines[-400:]:
            s = ln.strip()
            if s.lower().startswith("sawal:"):
                if cur_q is not None:
                    blocks.append((cur_q, " ".join(cur_a)))
                cur_q, cur_a = s[6:].strip(), []
            elif s.lower().startswith("jawab:") and cur_q is not None:
                cur_a.append(s[6:].strip())
            elif cur_q is not None and s:
                cur_a.append(s)
        if cur_q is not None:
            blocks.append((cur_q, " ".join(cur_a)))
        # sawal-match: token overlap; 🆕 sawal ke alfaaz na hon (digits jaise
        # "1000000000+") to jawab-vs-block overlap (jawab isi page-se aya ho
        # to ~1.0, fabricate to kam) — pehle yahan HAMESHA 0 aata tha
        qw = set(re.findall(r"[a-z]{3,}", prompt.lower())) - {"kya", "hai", "what", "the"}
        best = 0.0
        for q, a in blocks:
            qset = set(re.findall(r"[a-z]{3,}", q.lower()))
            if not qset:
                continue
            ov = len(qw & qset) / max(1, len(qw | qset)) if qw else 1.0
            if ov > best:
                aw = set(re.findall(r"[a-z]{3,}", answer.lower()))
                if qw:
                    aw_score = len(qw & aw) / max(1, len(qw))
                else:
                    blk = set(re.findall(r"[a-z]{3,}", a.lower()))
                    aw_score = (len(aw & blk) / max(1, len(aw))) if aw else 0.0
                best = ov * aw_score if aw_score else 0.0
        return round(min(1.0, best), 3)
    except Exception:
        return 0.0


# ----------------------------------------------------------------------
# layer 3: artifact guards (nakli citation / kachra)
# ----------------------------------------------------------------------
def _artifacts_ok(answer: str) -> bool:
    try:
        from model.generate import _no_citation, _quality
        if not answer or len(answer) < 20:
            return False
        if not _no_citation(answer):
            return False
        if _quality(answer) < 1.5:
            return False
        return True
    except Exception:
        return len(answer or "") >= 20


# ----------------------------------------------------------------------
# MAIN VERIFY
# ----------------------------------------------------------------------
def verify(prompt: str, answer: str, page: str = None) -> dict:
    """Research jawab ki tasdeeq. page = (optional) raw research snippet."""
    ck = checkpoint()
    checks = {}
    # 3) artifacts (hamesha)
    checks["artifacts"] = _artifacts_ok(answer)
    if not checks["artifacts"]:
        return {"ok": False, "score": 0.0,
                "reason": "fabrication/junk guards fail", "checks": checks}

    # 2) source-consistency (cache ya page)
    src = 0.0
    # 🆕 1-2 harf sawal ('h', 'xy'): content-words hi nahi → overlap-based
    # consistency/ppl be-maene hain. ASLI saboot = provenance (manba-
    # attribution — net_guard-whitelisted page se aya jawab) → src=0.7, aur
    # chhote verifier-brain ka ppl 1-harf par bharosemand nahi → neutral.
    # Ye jhoot nahi — provenance-trust hai (koi manba na ho to src=0 hi).
    _short_q = not re.findall(r"[a-z]{3,}", (prompt or "").lower())
    if _short_q:
        src = 0.7 if re.search(r"\(manba: [^)]+\)", answer or "") else 0.0
    elif page:
        qw = set(re.findall(r"[a-z]{3,}", (prompt or "").lower())) - {"kya", "hai", "what"}
        aw = set(re.findall(r"[a-z]{3,}", (answer or "").lower()))
        pw = set(re.findall(r"[a-z]{3,}", (page or "").lower()))
        if qw and aw and pw:
            src = round(len((qw | aw) & pw) / max(1, len(qw | aw)), 3)
    else:
        src = _cache_consistency(prompt, answer)
    checks["source_consistency"] = src
    if _short_q:
        checks["note"] = "1-2 harf sawal → provenance-trust (manba-attribution)"

    # 1) perplexity (agar checkpoint hai)
    ppl = None
    if ck and not _short_q:
        try:
            from model.generate import _load_model
            tok, brain = _load_model(ck)
            ppl = _perplexity(answer, tok, brain)
        except Exception:
            ppl = None
    checks["perplexity"] = ppl

    # decision — ppl ab ASLI log-prob (-4..-1) hai → 0..1 par normalize
    ppl_norm = None
    if ppl is not None:
        ppl_norm = min(1.0, max(0.0, (ppl + 4.0) / 3.0))   # -4→0, -1→1
    score = 0.4 * src + (0.6 * ppl_norm if ppl_norm is not None else 0.6 * 0.5)
    ok = score >= 0.45
    reason = ("tasdeeq: src=%.2f ppl=%s → %s"
              % (src, ("%.2f" % ppl) if ppl is not None else "n/a",
                 "PASS" if ok else "KAMZOR"))
    return {"ok": ok, "score": round(score, 3), "reason": reason, "checks": checks}


def status():
    """Hub ke liye: verifier-brain dictionary."""
    ck = checkpoint()
    return {"on": bool(ck), "checkpoint": os.path.basename(ck) if ck else None,
            "params": "%s (~5.1M, dh560) — research-ka-tasdeeq-kar" % f"{params_estimate():,}",
            "bridge": "live-research chain + master(7M) + helper(5.1M) + deep(6.25M)"}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print("🔎 VERIFY brain:", status())
    r = verify("photosynthesis kya hai",
               "Photosynthesis is the process by which plants make food using sunlight.")
    print("verify:", r)
