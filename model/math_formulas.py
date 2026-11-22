# -*- coding: utf-8 -*-
"""📐 Hemomemo AI — FORMULA LIBRARY ENGINE (model/math_formulas.py)

data/corpus_big/formulas_master.txt (Math A-Z + Physics A-Z, ~210 formulas)
ko parhta hai, sawal se formula milata hai, numbers plug kar ke HAL nikalta
hai (numbers kam hon to TEACH-mode: formula + variables + misaal).

Sab kuch LOCAL: koi API, koi internet, koi AI-model connection NAHI.
Safe AST evaluator — koi eval()/exec() nahi.
"""
import ast
import math
import os
import sys
import re

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORMULA_FILE = os.path.join(ROOT, "data", "corpus_big", "formulas_master.txt")

# Bunyadi sawanih (constants) — sirf tab auto-judte hain jab Vars me
# "constant" likha ho (warna h = height, c = specific heat user se lenge).
CONSTANTS = {
    "pi": math.pi, "e": math.e,
    "c": 2.99792458e8, "g": 9.81, "G": 6.674e-11, "h": 6.62607015e-34,
    "k": 8.988e9, "eps0": 8.8541878128e-12, "Eps0": 8.8541878128e-12,
    "mu0": 1.25663706212e-6, "Mu0": 1.25663706212e-6,
    "Na": 6.02214076e23, "R": 8.314462618, "kb": 1.380649e-23,
    "Kb": 1.380649e-23, "sigma": 5.670374419e-8, "Sigma": 5.670374419e-8,
    "atm": 101325.0, "Atm": 101325.0, "Me": 9.1093837015e-31,
    "Mp": 1.67262192369e-27, "Ec": 1.602176634e-19,
    "K": 8.988e9,   # Coulomb constant (Constants-block var)
}
_AUTO_CONST = {"pi", "e"}
_FUNCS = {
    "sqrt": math.sqrt, "log": math.log10, "log10": math.log10, "ln": math.log,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "abs": abs,
}


def _fact(n):
    n = int(n)
    if n < 0 or n > 170:
        raise ValueError("fact-limit")
    return float(math.factorial(n))


def _ncr(n, r):
    return float(math.comb(int(n), int(r)))


def _npr(n, r):
    return float(math.perm(int(n), int(r)))


_FUNCS["fact"] = _fact
_FUNCS["ncr"] = _ncr
_FUNCS["npr"] = _npr

_STOPW = {"ka", "ki", "ke", "se", "ka", "the", "of", "a", "an", "for", "and",
          "formula", "nikalo", "nikalna", "batao", "kya", "hai"}


# ----------------------------------------------------------------------
# 📖 LOADER — formulas_master.txt parse
# ----------------------------------------------------------------------
_CACHE = None


def load_all(refresh=False):
    """File se tamam formula-blocks parse karo (cached)."""
    global _CACHE
    if _CACHE is not None and not refresh:
        return _CACHE
    blocks = []
    try:
        with open(FORMULA_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().split("\n")
    except OSError:
        _CACHE = []
        return _CACHE
    cur = None
    for ln in lines:
        s = ln.strip()
        low = s.lower()
        if low.startswith("sawal:"):
            if cur:
                blocks.append(cur)
            cur = {"name": s[6:].strip(), "keywords": "", "formula": "",
                   "field": "", "vars": {}, "detail": ""}
            # "Name — keywords" split (em-dash)
            if "—" in cur["name"]:
                head, tail = cur["name"].split("—", 1)
                cur["name"] = head.strip()
                cur["keywords"] = tail.strip()
            # "(roman)" part bhi keywords me shamil
            m = re.search(r"\(([^)]+)\)", cur["name"])
            if m:
                cur["keywords"] = (cur["keywords"] + " " + m.group(1)).strip()
                cur["name"] = re.sub(r"\s*\([^)]+\)", "", cur["name"]).strip()
        elif cur is None:
            continue
        elif low.startswith("formula:"):
            cur["formula"] = s[8:].strip()
        elif low.startswith("field:"):
            cur["field"] = s[6:].strip()
        elif low.startswith("vars:"):
            for part in s[5:].split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    cur["vars"][k.strip()] = v.strip()
        elif low.startswith("detail:"):
            cur["detail"] = s[7:].strip()
        elif not s:
            if cur:
                blocks.append(cur)
                cur = None
    if cur:
        blocks.append(cur)
    # sirf sahi blocks rakho + expr-vars precompute (matcher speed)
    final = []
    for b in blocks:
        if not (b.get("formula") and "=" in b.get("formula", "")):
            continue
        # file-header ka FORMAT-TEMPLATE (<Naam>/<lhs>/<shoba>) formula NAHI
        blob = "%s %s %s" % (b.get("name", ""), b.get("field", ""),
                             b.get("formula", ""))
        if "<naam>" in blob.lower() or "<lhs>" in blob.lower():
            continue
        lhs, expr, evars = _split_formula(b)
        b["_lhs"], b["_expr"], b["_evars"] = lhs, expr, evars
        final.append(b)
    _CACHE = final
    return _CACHE


def _split_formula(block):
    """lhs = expr (pehle '=' par); expr ke var-tokens (order me)."""
    f = block.get("formula", "")
    if "=" not in f:
        return None, None, []
    lhs, expr = f.split("=", 1)
    lhs, expr = lhs.strip(), expr.strip()
    seen, order = set(), []
    for tok in re.findall(r"[A-Za-z_][A-Za-z_0-9]*", expr):
        if tok in _FUNCS:          # sirf function-names chhodo —
            continue               # constants (h/T/R/c) ASLI vars hain, solve
        if tok not in seen:        # waqt meaning se auto hota hai
            seen.add(tok)
            order.append(tok)
    return lhs, expr, order


def _is_auto_const(var, meaning):
    """pi/e hamesha auto; baqi constants sirf tab jab meaning 'constant'
    bhi bole AUR usme digit ho (misal '8.99e9 (constant)') — warna
    'spring constant' k jaisa user-var ghalat-bashi auto na ho jaye."""
    if var in _AUTO_CONST:
        return True
    meaning = meaning or ""
    return var in CONSTANTS and "constant" in meaning.lower() \
        and any(ch.isdigit() for ch in meaning)


def _pretty(expr):
    t = expr.replace("**", "^").replace("*", " × ").replace("pi", "π")
    t = t.replace("sqrt(", "√(").replace("log10(", "log(")
    t = re.sub(r"\s+", " ", t).strip()
    return t


# ----------------------------------------------------------------------
# 🎯 MATCHER — sawal ↔ formula
# ----------------------------------------------------------------------
def _topic_base(block, low):
    """Topical score: block ke keywords/name-words sawal me TOKEN-BOUNDARY se
    mile (ya jura-hua digit-match jaise mc2 ~ mc^2)."""
    base = 0.0
    # ⚠️ SET: keyword file me do dafa likha ho to score DOUBLE nahi hota —
    # (warna "volume volume" wale block par chat ka "volume" 2.0 ban jata hai)
    for w in sorted(set(re.findall(r"[a-z0-9]+", (block.get("keywords") or "").lower()))):
        if len(w) < 3 or w in _STOPW:
            continue
        if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(w), low):
            base += 1.0
        elif len(w) >= 3 and any(ch.isdigit() for ch in w) and re.search(
                "[^a-z0-9]{0,2}".join(re.escape(ch) for ch in w), low):
            base += 1.2            # jura-hua match (jaise mc2 ~ mc^2)
    for w in set(re.findall(r"[a-z0-9]+", (block.get("name") or "").lower())):
        if len(w) < 3 or w in _STOPW:
            continue
        if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(w), low):
            base += 0.6
    return base


def _score(block, low, join, assignments, free):
    base = _topic_base(block, low)
    if base < 0.5:
        return 0.0                 # topical match ke baghair koi bonus NAHI
    # variable-fit bonus: sawal ke assignments formula ke vars par bhoanse
    evars = block.get("_evars") or []
    hit = sum(1 for a in assignments if a in evars)
    sc = base + 0.6 * hit
    user_vars = [v for v in evars
                 if not _is_auto_const(v, block["vars"].get(v, ""))]
    if user_vars and hit and len(assignments) + len(free) == len(user_vars):
        sc += 0.4                  # perfect plug-and-solve fit
    return sc


_SOLVE_RE = re.compile(
    r"(?i)\b(nikalo|nikal|nikaal|nikalna|calculate|calc|solve|evaluate|"
    r"compute|kitna|kitne|kitni|find|hoga|hongi)\b")


# 🛡 PROMPT-SAMAJH GUARD (16-Nov): info/about/github-repo sawal par formula
# KABHI nahi — ('details about github repo noity0' ko kabhi Spring T=8.11
# jaisa jawab nahi milna chahiye, chahe input me YAAD/numbers leak ho).
_INFO_RX = re.compile(
    r"(?i)\b(?:about|details|detail|github|repo|repository|noity0)\b")
_KYA_RX = re.compile(
    r"(?i)\b(?:kya\s+hai|what\s+is|what\s+are|matlab\s+kya)\b")


def _info_blocked(low):
    """Formula-engine ka intent-guard:
    • about/details/github/repo/noity0 lafz → hamesha BLOCK (ye lafz asli
      math-sawal me nahi aate).
    • 'X kya hai' / 'what is X' → sirf tab formula jab koi formula-topic lafz
      sach-much mojood ho ('circle ka area kya hai' ✓ chalta rahega;
      'github repo noity0 kya hai' ✗ aur 'photosynthesis kya hai' ✗ — wo
      ilm-sawal hain)."""
    if _INFO_RX.search(low):
        return True
    if _KYA_RX.search(low):
        topic = any(_topic_base(b, low) >= 0.5 for b in load_all())
        return not topic
    return False


def find_formula(q, strict=False):
    """Sawal ke liye behtareen formula (ya None). Score >= 1.0 zaroori.
    strict=True → sirf ASLI math/formula sawal:
      • strong match (score >= 2.0, misal "simple interest", "pythagoras
        theorem", "coulomb law" — rozmarra chat me aisa combo nahi aata), YA
      • assignment (r = 5), YA
      • numbers + solve-ka-lafz (nikalo/kitna/calculate…)
    Is se normal baat-cheet (tension/kaam/speed/energy/power jaise lafz)
    me formula library KABHI nahi khulti — sirf math sawal par."""
    low = (q or "").lower()
    # 🎯 90%-CORE (defense-in-depth): YAAD-preamble/wrapper scorer aur
    #    number-extraction KABHI na dekhe (aam-taur par caller pehle hi
    #    core_intent_text laga-chuka hota hai — yahan bhi qaim, hamesha).
    #    Case asli rakha (T/E jaise uppercase-vars ke assignments match rahein).
    _core_txt = q
    try:
        from model.prompt_system import core_intent_text as _coreq
        _core_txt = _coreq(q or "") or q
        low = _core_txt.lower()
    except Exception:
        pass
    if _info_blocked(low):        # 🛡 info-sawal → formula KABHI nahi
        return None
    join = "".join(re.findall(r"[a-z0-9]", low))
    assignments, free = _extract_numbers(_core_txt)
    best, best_sc = None, 0.0
    for b in load_all():
        sc = _score(b, low, join, assignments, free)
        if sc > best_sc:
            best, best_sc = b, sc
    if best is None or best_sc < 1.0:
        return None
    if strict:
        if best_sc >= 2.0:
            return best
        intent = bool(assignments) or (
            bool(free) and bool(_SOLVE_RE.search(low)))
        return best if intent else None
    return best


def is_formula_q(q):
    """classify() ke liye: kya ye ASLI formula/math-sawal hai?
    Normal baat-cheet me formula nahi khulta (strict gate)."""
    return find_formula(q, strict=True) is not None# ----------------------------------------------------------------------
# 🧮 SAFE EVALUATOR (no eval/exec — sirf safe AST nodes)
# ----------------------------------------------------------------------
def _eval_node(n, names):
    if isinstance(n, ast.Constant):
        if isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return float(n.value)
        return None
    if isinstance(n, ast.Name):
        return names.get(n.id)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
        v = _eval_node(n.operand, names)
        if v is None:
            return None
        return -v if isinstance(n.op, ast.USub) else v
    if isinstance(n, ast.BinOp) and isinstance(
            n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
                   ast.Mod, ast.FloorDiv)):
        l, r = _eval_node(n.left, names), _eval_node(n.right, names)
        if l is None or r is None:
            return None
        try:
            if isinstance(n.op, ast.Add):
                return l + r
            if isinstance(n.op, ast.Sub):
                return l - r
            if isinstance(n.op, ast.Mult):
                return l * r
            if isinstance(n.op, ast.Div):
                return None if r == 0 else l / r
            if isinstance(n.op, ast.Mod):
                return None if r == 0 else l % r
            if isinstance(n.op, ast.FloorDiv):
                return None if r == 0 else l // r
            if isinstance(n.op, ast.Pow):
                if abs(r) > 200:
                    return None
                return l ** r
        except Exception:
            return None
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
        fn = _FUNCS.get(n.func.id)
        if fn is None or len(n.args) != 1:
            return None
        v = _eval_node(n.args[0], names)
        if v is None:
            return None
        try:
            return float(fn(v))
        except Exception:
            return None
    return None


def _safe_eval(expr, names):
    try:
        node = ast.parse(expr.replace("^", "**"), mode="eval").body
    except Exception:
        return None
    return _eval_node(node, names)


# ----------------------------------------------------------------------
# 🔢 NUMBER EXTRACTION — assignments (r=5) + free numbers
# ----------------------------------------------------------------------
def _extract_numbers(q):
    """'r=5, h=2' assignments pehle; baqi free numbers order me."""
    assignments = {}
    rest = q or ""
    for m in re.finditer(
            r"\b([A-Za-z]{1,4})\s*=\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)", rest):
        assignments[m.group(1)] = float(m.group(2))
        rest = rest.replace(m.group(0), " ")
    free = [float(x) for x in re.findall(
        r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", rest)]
    return assignments, free


def _fmt(v):
    if v is None:
        return "?"
    r = round(float(v), 8)
    if r == int(r) and abs(r) < 1e16:
        return str(int(r))
    if abs(r) >= 1e7 or (abs(r) < 1e-4 and r != 0):
        return "%.4g" % r
    return ("%.8f" % r).rstrip("0").rstrip(".")


# ----------------------------------------------------------------------
# ⚗️ SOLVE — plug-and-solve ya teach
# ----------------------------------------------------------------------
def solve_formula(q):
    """(answer_text, steps, conf, verified, tags) — ya None."""
    block = find_formula(q)
    if not block:
        return None
    lhs, expr, evars = block["_lhs"], block["_expr"], block["_evars"] or []
    if not expr:
        return None
    tag = ["formula:%s" % re.sub(r"[^a-z0-9]+", "-",
                                 (block.get("name") or "f").lower()).strip("-")]
    steps = ["📐 Formula: %s — %s" % (block.get("name"), block.get("field"))]

    # 🎯 90%-CORE: numbers bhi SIRF akhri-sawal se (YAAD-preamble ke purane
    #    numbers 'Diya gaya' me kabhi na ghusen — imandari qanoon). Case asli
    #    (T/E jaise uppercase-vars ke assignments match rahein).
    _num_q = q
    try:
        from model.prompt_system import core_intent_text as _coreq
        _num_q = _coreq(q or "") or q
    except Exception:
        pass
    assignments, free = _extract_numbers(_num_q)
    names, used_free, missing, given = dict(CONSTANTS), 0, [], []
    for var in evars:
        meaning = block["vars"].get(var, "")
        if var in assignments:
            names[var] = assignments[var]
            given.append("%s = %s" % (var, _fmt(assignments[var])))
            continue
        if _is_auto_const(var, meaning):
            continue
        if used_free < len(free):
            names[var] = free[used_free]
            given.append("%s = %s" % (var, _fmt(free[used_free])))
            used_free += 1
            continue
        missing.append(var)

    val = None
    if not missing:
        val = _safe_eval(expr, names)

    if val is not None and not math.isnan(val) and not math.isinf(val):
        steps.append("Formula: %s" % block.get("formula"))
        if given:
            steps.append("Diya gaya: %s" % ", ".join(given))
        steps.append("Hisaab: %s = %s" % (_pretty(expr), _fmt(val)))
        ans = "Jawab: %s = %s" % (lhs, _fmt(val))
        return ans, steps, 1.0, True, tag

    # ------- TEACH-MODE: formula sikhao + misaal dikhao -------
    parts = ["Jawab: 📐 Formula — %s (%s)" % (block.get("name"), block.get("field"))]
    parts.append("%s = %s" % (lhs, _pretty(expr)))
    if block["vars"]:
        parts.append("• Vars: " + "; ".join(
            "%s = %s" % (k, v) for k, v in block["vars"].items()))
    if block.get("detail"):
        parts.append("• Tafseel: %s" % block["detail"])
    # misaal: har user-var ko misali qeemat de kar dikhao
    ex_names, ex_give = dict(CONSTANTS), []
    samples = [2.0, 3.0, 4.0, 5.0]
    si = 0
    ok = True
    for var in evars:
        meaning = block["vars"].get(var, "")
        if var in assignments:
            ex_names[var] = assignments[var]
            ex_give.append("%s=%s" % (var, _fmt(assignments[var])))
            continue
        if _is_auto_const(var, meaning):
            continue
        if si < len(samples):
            ex_names[var] = samples[si]
            ex_give.append("%s=%s" % (var, _fmt(samples[si])))
            si += 1
        else:
            ok = False
    if ok and ex_give:
        exv = _safe_eval(expr, ex_names)
        if exv is not None and not math.isnan(exv) and not math.isinf(exv):
            parts.append("• Misaal: %s → %s = %s"
                         % (", ".join(ex_give), lhs, _fmt(exv)))
    if missing:
        parts.append("• %s ki qeemat batao (jaise %s = 5) to main foran hal "
                     "nikal dunga." % (missing[0], missing[0]))
    steps.append("Teach-mode: numbers kam the — formula + misaal sikhaya")
    return "\n".join(parts), steps, 0.8, True, tag


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    fs = load_all()
    print("FORMULAS-LOADED: %d" % len(fs))
    tests = [
        "circle ka area nikaalo r = 5",
        "triangle ka area, b = 10 aur h = 4",
        "force nikalo m = 10 aur a = 3",
        "E = mc^2, m = 2",
        "12 * 4 + 3",
        "simple interest 5000 par 5 percent 2 saal",
        "speed nikalo d = 100 t = 20",
        "pythagoras a = 3 b = 4",
        "quadratic formula a=1 b=-3 c=2",
        "sphere ka volume r = 3",
        "photosynthesis kya hai",
        "half life lam = 0.05",
    ]
    for t in tests:
        r = solve_formula(t)
        print("-", t, "=>", (r[0].split("\n")[0] if r else "None"))
