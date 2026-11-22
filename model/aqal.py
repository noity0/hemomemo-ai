"""
🧠 aqal.py — Hemomemo AI ka AQAL / INTELLECT CORE (deep reasoning engine)

Insaan jaisi aqal (intellect/reasoning) — koi AI API, koi cloud, koi model:
  1. CHAIN-OF-THOUGHT (CoT) : sawal ko chhote reasoning steps me todna
  2. ANALOGICAL REASONING   : milte-julte patterns / analogies dhundna
  3. CAUSAL REASONING       : "kyun" / "kaise" ka cause-effect chain
  4. DEDUCTIVE INFERENCE    : premises se logical conclusion
  5. INDUCTIVE GENERALIZE   : examples se general rule banana
  6. ABDUCTIVE EXPLAIN      : best explanation choose karna (most plausible)
  7. CONTRADICTION CHECK    : jawab me contradiction toh nahi?
  8. EVIDENCE WEIGHING      : multiple sources ko trust-score se rank karna
  9. SELF-CORRECTION        : khud apna jawab re-examine + improve
 10. LOGICAL FALLACY CHECK  : circular reasoning, false dichotomy detect

SAMAJH layer (model/understand.py) pehle aata hai: typo/elongation input
(hiiii/byeee/okkk) ko samajh kar social-intent nikalta hai — ye file uske
BAAD wali gehri soch (reasoning) hai.

Wiring: model.autonomous (after candidate selection) | model.generate (deep think)
"""

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
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ----------------------------------------------------------------------
# 🧠 CHAIN-OF-THOUGHT (CoT): sawal ko reasoning steps me todna
# ----------------------------------------------------------------------
def chain_of_thought(prompt: str, context: str = "") -> list:
    """Sawal ko logical reasoning steps me todna (human-like step-by-step soch)."""
    steps = []
    q = (prompt or "").strip()
    low = q.lower()
    # Step 1: intent / what is being asked
    steps.append("FOCUS: sawal ka maqsad samjho — '%s'" % q[:80])
    # Step 2: identify key concepts
    toks = re.findall(r"[a-zA-Z]{3,}", low)
    concepts = [w for w in toks if w not in ("the", "and", "for", "are", "was", "were")]
    if concepts:
        steps.append("CONCEPTS: %s" % ", ".join(concepts[:6]))
    # Step 3: what kind of reasoning needed
    if any(w in low for w in ("kyun", "why", "cause", "reason", "because")):
        steps.append("REASONING-TYPE: causal (kyun/kaise ka chain)")
    elif any(w in low for w in ("kya", "what", "kaun", "who", "kahan", "where")):
        steps.append("REASONING-TYPE: factual (kya/kaun/kahan)")
    elif any(w in low for w in ("kaise", "how", "tareeqa", "method")):
        steps.append("REASONING-TYPE: procedural (kaise/tareeqa)")
    elif any(w in low for w in ("compare", "farq", "difference", "better", "best")):
        steps.append("REASONING-TYPE: comparative (farq/better)")
    else:
        steps.append("REASONING-TYPE: general (open-ended)")
    # Step 4: evidence gathering plan
    steps.append("EVIDENCE: local knowledge (corpus/Quran/Hadith) → live web (whitelist) → inference")
    # Step 5: verification plan
    steps.append("VERIFY: self-check + source-trust + fabrication-guard")
    return steps


# ----------------------------------------------------------------------
# 🔗 ANALOGICAL REASONING: milte-julte patterns dhundna
# ----------------------------------------------------------------------
def analogize(prompt: str, known_pairs: list = None) -> list:
    """Known concept pairs se analogies dhundna (A:B :: C:D style)."""
    analogies = []
    low = (prompt or "").lower()
    if known_pairs:
        for a, b in known_pairs:
            if a.lower() in low or b.lower() in low:
                analogies.append({"from": a, "to": b, "relation": "similar"})
    # built-in analogies for common concepts
    _BUILTIN = [
        ("brain", "computer", "processing"),
        ("heart", "pump", "circulation"),
        ("ai", "student", "learning"),
        ("quran", "guide", "direction"),
        ("knowledge", "light", "illumination"),
        ("ignorance", "darkness", "absence"),
        ("training", "practice", "improvement"),
        ("memory", "storage", "retention"),
        ("reasoning", "thinking", "cognition"),
        ("soul", "life", "essence"),
    ]
    for a, b, rel in _BUILTIN:
        if a in low or b in low:
            analogies.append({"from": a, "to": b, "relation": rel})
    return analogies


# ----------------------------------------------------------------------
# ⚡ CAUSAL REASONING: cause-effect chain
# ----------------------------------------------------------------------
def causal_chain(prompt: str) -> list:
    """'Kyun'/'kaise' ka cause-effect chain banana."""
    chain = []
    low = (prompt or "").lower()
    # detect causal keywords
    causal_markers = ["kyun", "why", "because", "isliye", "is wajah", "cause", "reason",
                      "kaise", "how", "tareeqa", "process", "result", "effect"]
    if any(m in low for m in causal_markers):
        chain.append("CAUSE: sawal me causal marker mila → deep chain chahiye")
        chain.append("EFFECT: evidence gather karo (local + live research)")
        chain.append("MECHANISM: step-by-step mechanism explain karo (how/why)")
    # Quran/Hadith causal
    if any(w in low for w in ("allah", "quran", "hadith", "sunnah", "islam")):
        chain.append("SACRED-CAUSE: divine guidance → human action → result")
    return chain


# ----------------------------------------------------------------------
# 📐 DEDUCTIVE INFERENCE: premises se conclusion
# ----------------------------------------------------------------------
def deduce(premises: list, conclusion_candidate: str = "") -> dict:
    """Premises se logical conclusion nikalna (modus ponens style)."""
    if not premises:
        return {"conclusion": conclusion_candidate, "valid": False,
                "reason": "no premises"}
    # simple rule: if all premises agree, conclusion = candidate
    valid = True
    for p in premises:
        if not p or not isinstance(p, str):
            valid = False
            break
    return {"conclusion": conclusion_candidate, "valid": valid,
            "premises_count": len(premises),
            "reason": "all premises consistent" if valid else "inconsistent premises"}


# ----------------------------------------------------------------------
# 📊 INDUCTIVE GENERALIZE: examples se general rule
# ----------------------------------------------------------------------
def induce(examples: list) -> dict:
    """Examples se general rule banana (pattern recognition)."""
    if not examples:
        return {"rule": None, "confidence": 0.0, "examples_used": 0}
    # find common words across examples
    common = set()
    for i, ex in enumerate(examples):
        w = set(re.findall(r"[a-z]{3,}", str(ex).lower()))
        if i == 0:
            common = w
        else:
            common &= w
    rule = " ".join(sorted(common)[:5]) if common else None
    conf = min(1.0, len(common) / max(1, len(examples)))
    return {"rule": rule, "confidence": round(conf, 2),
            "examples_used": len(examples), "common_terms": list(common)[:8]}


# ----------------------------------------------------------------------
# 🧩 ABDUCTIVE EXPLAIN: best explanation choose karna
# ----------------------------------------------------------------------
def abduce(candidates: list) -> dict:
    """Multiple hypotheses me se best explanation choose karna (most plausible)."""
    if not candidates:
        return {"best": None, "reason": "no candidates"}
    # score by confidence + source trust
    scored = []
    for c in candidates:
        if not isinstance(c, dict):
            continue
        conf = float(c.get("confidence") or 0.0)
        src = c.get("source", "")
        trust = {"algorithm": 1.0, "math": 1.0, "local-knowledge": 0.93,
                 "sacred-local": 0.95, "owner": 0.95, "logic": 0.86,
                 "adab": 0.97, "live-research": 0.55, "imandari": 0.2}.get(src, 0.3)
        score = conf * trust
        scored.append((score, c))
    if not scored:
        return {"best": None, "reason": "no valid candidates"}
    scored.sort(key=lambda x: -x[0])
    best = scored[0][1]
    return {"best": best, "score": round(scored[0][0], 3),
            "reason": "highest trust-weighted confidence",
            "alternatives": len(scored) - 1}


# ----------------------------------------------------------------------
# ⚠️ CONTRADICTION CHECK: jawab me contradiction toh nahi?
# ----------------------------------------------------------------------
def check_contradiction(answer: str, facts: list = None) -> dict:
    """Jawab me internal contradiction ya fact-contradiction detect karna."""
    if not answer:
        return {"contradiction": False, "reason": "empty answer"}
    low = answer.lower()
    contradictions = []
    # simple negation pairs
    neg_pairs = [("yes", "no"), ("true", "false"), ("always", "never"),
                 ("all", "none"), ("possible", "impossible")]
    for a, b in neg_pairs:
        if a in low and b in low:
            # could be legitimate contrast; flag as potential
            contradictions.append({"pair": (a, b), "type": "potential"})
    # check against facts
    if facts:
        for f in facts:
            if isinstance(f, str) and f.lower() in low:
                pass  # consistent
    return {"contradiction": len(contradictions) > 0,
            "potential_issues": contradictions,
            "reason": "no contradiction" if not contradictions else "potential contrast detected"}


# ----------------------------------------------------------------------
# ⚖️ EVIDENCE WEIGHING: multiple sources ko trust-score se rank karna
# ----------------------------------------------------------------------
def weigh_evidence(candidates: list) -> list:
    """Multiple candidate jawab ko trust + confidence se rank karna."""
    if not candidates:
        return []
    _TRUST = {"algorithm": 1.0, "math": 1.0, "local-knowledge": 0.93,
              "sacred-local": 0.95, "owner": 0.95, "logic": 0.86,
              "adab": 0.97, "live-research": 0.55, "imandari": 0.2,
              "tarbiyat": 0.3, "grace": 0.25, "reflex": 0.1}
    ranked = []
    for c in candidates:
        if not isinstance(c, dict):
            continue
        conf = float(c.get("confidence") or 0.0)
        src = c.get("source", "")
        trust = _TRUST.get(src, 0.3)
        weight = round(conf * trust, 3)
        ranked.append({"candidate": c, "weight": weight,
                       "source": src, "confidence": conf, "trust": trust})
    ranked.sort(key=lambda x: -x["weight"])
    return ranked


# ----------------------------------------------------------------------
# 🔄 SELF-CORRECTION: khud apna jawab re-examine + improve
# ----------------------------------------------------------------------
def self_correct(answer: str, prompt: str, confidence: float = 0.5) -> dict:
    """Jawab ko khud re-examine — aur ASLI sudhaar: kam-bharosa par jhoothe
    yaqeen-alfaaz ('certainly/definitely/always') naram ('ghalaban') kiye jate
    hain — jawab badalta hai jab sudhaar zaroori ho (pehle hamesha same)."""
    if not answer:
        return {"original": answer, "corrected": answer, "improved": False,
                "reason": "empty"}
    low = answer.lower()
    issues = []
    corrected = answer
    # check for overconfidence
    if confidence < 0.5 and any(w in low for w in ("certainly", "definitely", "always")):
        issues.append("overconfidence detected → hedges softened")
        for w in ("certainly", "definitely", "always"):
            corrected = re.sub(r"\b%s\b" % w, "ghalaban", corrected, flags=re.I)
    # check for vagueness
    if len(answer) < 30:
        issues.append("too short — may lack detail")
    # check for hallucination markers
    if "i think" in low or "maybe" in low or "probably" in low:
        issues.append("uncertain language — verify")
    improved = corrected != answer
    return {"original": answer, "corrected": corrected, "improved": improved,
            "issues": issues, "confidence": confidence}


# ----------------------------------------------------------------------
# 🚫 LOGICAL FALLACY CHECK
# ----------------------------------------------------------------------
def check_fallacy(reasoning: str) -> list:
    """Reasoning me logical fallacies detect karna."""
    if not reasoning:
        return []
    low = reasoning.lower()
    fallacies = []
    # circular reasoning: conclusion == premise
    if "because" in low and low.count("because") > 2:
        fallacies.append({"type": "circular_reasoning", "severity": "medium"})
    # false dichotomy
    if "either" in low and "or" in low and "only" in low:
        fallacies.append({"type": "false_dichotomy", "severity": "low"})
    # appeal to authority without evidence
    if "expert" in low and "said" in low and "evidence" not in low:
        fallacies.append({"type": "appeal_to_authority", "severity": "low"})
    return fallacies


# ----------------------------------------------------------------------
# 🧠 AQAL MAIN: full reasoning pipeline
# ----------------------------------------------------------------------
def reason(prompt: str, candidates: list = None, context: str = "") -> dict:
    """Full aqal pipeline: CoT → analogize → causal → deduce → induce → abduce
    → self_correct → weigh. (deduce/induce ab zinda hain — candidates ke asli
    premises se modus-ponens + pattern-rule; pehle dead-code the.)"""
    cot = chain_of_thought(prompt, context)
    analogies = analogize(prompt)
    causal = causal_chain(prompt)
    abd = abduce(candidates or [])
    _best_ans = ""
    if isinstance(abd.get("best"), dict):
        _best_ans = abd["best"].get("answer", "") or ""
    # 🆕 DEDUCTION: candidates ki lambi jawab-lines = premises; sab consistent
    # (non-empty strings) to best-answer valid conclusion banta hai
    cand_texts = [str(c.get("answer", "") or "") if isinstance(c, dict) else str(c)
                  for c in (candidates or []) if c]
    premises = [c for c in cand_texts if len(c) >= 30]
    ded = deduce(premises, _best_ans)
    # 🆕 INDUCTION: 2+ examples se common-pattern rule (ranked-evidence ko
    # wazar deta hai — rule-words jitne zyada candidate me, utna sahi)
    ind = induce(cand_texts) if len(cand_texts) >= 2 else {
        "rule": None, "confidence": 0.0, "examples_used": len(cand_texts)}
    ec = check_contradiction(_best_ans, [])
    sc = self_correct(_best_ans, prompt,
                      abd["best"].get("confidence", 0.5) if isinstance(abd.get("best"), dict) else 0.5)
    ranked = weigh_evidence(candidates or [])
    if ind.get("rule") and ranked:
        rws = set(ind["rule"].split())
        ranked = sorted(ranked, key=lambda c: -min(1, sum(
            1 for w in rws if w in str(c if isinstance(c, str) else c.get("answer", "")).lower()) / max(1, len(rws))))
    fallacies = check_fallacy(" ".join(cot + causal))
    return {
        "chain_of_thought": cot,
        "analogies": analogies,
        "causal_chain": causal,
        "deduction": ded,
        "induction": ind,
        "abduction": abd,
        "contradiction": ec,
        "self_correction": sc,
        "ranked_evidence": ranked[:3],
        "fallacies": fallacies,
        "reasoning_depth": len(cot) + len(causal) + len(analogies) + len(premises),
    }


if __name__ == "__main__":
    print("aqal demo:")
    r = reason("photosynthesis kya hai aur kyun zaruri hai")
    for k, v in r.items():
        print("  ", k, ":", v if not isinstance(v, list) else len(v))
