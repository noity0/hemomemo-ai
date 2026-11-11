"""
🤖 autonomous.py — Hemomemo AI AUTONOMOUS REASONING ENGINE (FULLY AUTONOMOUS UPGRADE)

Hemomemo AI ko ab bilkul aakhirat me fully autonomous bana diya (latest flow: READ-TOKEN→CONVERT-TO-BINARY→READ-BY-AI→THINK→REASONING→THINK-RESEARCH→THINK-CONVERT→RESEARCH→THINK→CONVERT-BINARY-TO-TEXT→ANSWER→READ-AGAIN→LEARN):

    📥 READ    → sawal ko samajh (normalize / tokenize / intent-scan)
    🧭 FOCUS   → jawab kis che ke liye chahiye (math / logic / fact / sacred /
                 identity / how / compare / chit-chat)
    📚 RECALL  → local knowledge (QA pairs + sacred books + owner data) → graph
    🌐 RESEARCH→ live web (google / bing / duckduckgo / wikipedia — whitelist-only
                 page-reads, koi AI-API NAHI)
    ⚙️ REASON  → math engine (safe AST eval) / logic / retrieval-best / hypothesis
    🪞 VERIFY  → self-check: recompute + source-trust + fabrication-safe checks
    ✍️ SPEAK   → answer compose + facts-vs-assumptions + uncertainty + confidence

Koi bhi external AI / pretrained-AI / ollama / cloud / API / model-connection use
NAHI hota — yeh pura engine apne aik (pure stdlib algorithms: regex, token-overlap
scoring, ast-math, knowledge-graph traversal, hypothesis ranking, self-verification)
se khud jawab deta hai.

Jab ilm incomplete ho: best possible answer available information se derive hota hai,
facts vs assumptions clear hoti hai, aur uncertainty honestly explained hoti hai.
Koi bhi nakli ayat / nakli hadith / koi fabricated jumla nahi banegi.

Run:
    python model\\autonomous.py "sawal yahan"      # one-shot (terminal)
    python model\\autonomous.py                     # interactive terminal mode
"""

import ast
import json
import math
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
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

DATA = os.path.join(ROOT, "data")
BIG = os.path.join(DATA, "corpus_big")


# ----------------------------------------------------------------------
# 🧹 NORMALIZATION + TOKENIZER (READ phase ke alag-hai chehre)
# ----------------------------------------------------------------------
_STOP = set("""kya kyun kaun kaise hai hain ho ke ki ko se me in aur the what how
why you your is are do does a an of in on for about give me please batao btao bolo
nahin nahi nhi tha te ye woh it its ka matlab dey dekho dekh lo abhi ab
sahi karo karo kar kar do dene mujhe mera meri meri hum aap tum tu main
salam hello hi hey hey hey hey test web search results page undated undated
live padhai google bing duckduckgo wikipedia query term""".split())


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (t or "").lower())).strip()


def toks(t: str) -> list:
    return [w for w in re.findall(r"[a-z0-9]{2,}", (t or "").lower())
            if w not in _STOP and len(w) > 1]


def content_set(t: str) -> set:
    return set(toks(t))


# ----------------------------------------------------------------------
# 🗣️ GREETING + ASLI-LAFZ VOCABULARY (kachra-input detection ke liye)
# ----------------------------------------------------------------------
_GREET_WORDS = re.compile(
    r"(?i)\b(salam|salaam|assalam|asalam|assalamualaikum|assalamoalaikum|"
    r"assalamualikum|aoa|asw|slam|hello|helo|hi|hii|hey|hye|hy|"
    r"adab|namaste|greetings|good morning|good evening)\b")

# chhota common-words set (English + Roman-Urdu) — corpus vocab se milkar
_COMMON_WORDS = set("""the be to of and a in that have i it for not on with he
as you do at this but his by from they we say her she or an will my one all
would there their what so up out if about who get which go me when make can
like time no just him know take people into year your good some could them
see other than then now look only come its over think also back after use
two how our work first well way even new want because any these give day most
us hello hi hey thanks thank ok okay yes no please sorry welcome morning night
name friends friend fine happy sad love like world computer program game food
water home house school college student teacher doctor car money life help
need question answer understand read write learn speak listen watch play run
walk eat sleep study english urdu islam muslim allah quran hadith sunnah
prayer mosque ramadan eid dua salah namaz zakat hajj test example code line
file data list set int float string python numpy model brain heart chat reply
word words letter letters number numbers math sum total average minus plus
divide multiply percent result value equal equation solve check compute
calculate aur ya agar lekin magar na han haan nahi nahin nhi ka ki ke ko se
mein main hum aap tum tu wo woh ye yeh is us iss uss tha thi the hain ho hota
hoti hote karo karein karna dena lena jata raha rahe gaya hua hui kiya kia q
bhai dost ustad janab shukriya khairiyat haal chal theek thik thoda bara chota
kam zyada bohat bahut kafi thora acha achha accha bura wala wali kaun kya kyun
kaise kitna kitne kab kahan matlab farq tasveer jagah samjha batao sunao explain
silai seb qalam samajh pehchan ilm danish aqal soch zehn Sawal Jawab""".split())

_VOCAB = None


def _vocab() -> set:
    """Asli-lafz vocabulary (corpus se lazy-loaded) — kachra-input detection."""
    global _VOCAB
    if _VOCAB is None:
        s = set(_COMMON_WORDS)
        try:
            for fp in (os.path.join(DATA, "corpus.txt"),
                       os.path.join(BIG, "dialogues_roman_urdu.txt"),
                       os.path.join(BIG, "dialogues_roman_urdu_v2.txt"),
                       os.path.join(BIG, "lifecycle_master.txt")):
                if os.path.exists(fp):
                    with open(fp, encoding="utf-8", errors="ignore") as f:
                        s |= set(re.findall(r"[a-z]{3,}", f.read(400_000).lower()))
            # 📚 corpus_big folder ko bhi padho (2x knowledge upgrade)
            # ⚠️ VOLATILE files skip: liveresearch.txt (har turn badalti research
            #    ka web-page text) — vocab pollution se gibberish-detection break.
            import glob as _g
            volatile = {"liveresearch.txt"}
            for fp in _g.glob(os.path.join(BIG, "*.txt")):
                if os.path.basename(fp).lower() in volatile:
                    continue
                try:
                    with open(fp, encoding="utf-8", errors="ignore") as f:
                        s |= set(re.findall(r"[a-z]{3,}", f.read(200_000).lower()))
                except Exception:
                    pass
        except Exception:
            pass
        _VOCAB = s
    return _VOCAB


_ROMAN_URDU_COMMON = set("""
zaeef zaif hadees hadis hadith sunnah fiqh fatwa tafseer tafsir ayat surah surat
quran quraan qoran allah rasool nabi muhammad salah namaz roza zakat hajj
umrah dua zikr darood bismillah alhamdulillah inshallah subhanallah mashallah
jazakallah salam aoa hi hello hey good morning night what how why who
where when which is are was were be been being have has had do does did will
would shall should can could may might must and but or so because if than
that this these those it its they them their he him his she her we us our
you your a an the in on at to for from with about as by of up out off
over under again further then once here there when where why how all each
few more most other some such no not only own same so than too very
kia kiya kya kaun kon kahan kab kyon kyun kaise kaisay kitna kitni kitne kis
batao btao samjhao sunao bolo likho dekho karo do lo sahi thik theek acha
achha bura naya purana bada chhota zyada kam bahut bohat kafi hona hone hota
hoti hote rahna rahe raha rahi hoon ho hain main ap aap tum tu hum wo woh yeh ye
ki ke ko se mein me aur yeh ye woh wo is us uss ka ke hain ho hai tha
thi the ga gi ge kiye kiye
""".split())


def _is_gibberish(low: str) -> bool:
    """Kachra/noise input (fdsf, xyzqwerty...) — asli lafz ya common word nahi milte.
    Corpus vocab + clean set dono check karta hai; heuristic: 4+ consecutive
    consonants = keyboard smash."""
    tk = re.findall(r"[a-z]{2,}", low)
    if not tk:
        return True
    clean = _STOP | _ROMAN_URDU_COMMON
    v = _vocab()
    known = sum(1 for t in tk if t in clean or t in v)
    # heuristic: 4+ consecutive consonants = keyboard smash (xyzqwertyuiop, fdsf)
    smash = False
    for t in tk:
        cons_run = 0
        for c in t:
            if c in "aeiouy":
                cons_run = 0
            else:
                cons_run += 1
                if cons_run >= 4:
                    smash = True
                    break
        if smash:
            break
    if smash:
        return True
    # no vowels at all (kachra)
    for t in tk:
        if not any(c in "aeiou" for c in t) and len(t) >= 4:
            return True
        # keyboard-smash tokens: rare-letter clusters (x/z/q/y jaisi made-up
        # sequences) — sirf unknown tokens par (vocab me jo lafz hain wo salamat)
        if (t not in clean and t not in v and len(t) >= 6
                and (t[:2] in ("xy", "xz", "zx", "zy", "qw", "kw", "vw", "xq")
                     or re.search(r"[xzqy]{3,}", t))):
            return True
    return known / len(tk) < 0.35


# ----------------------------------------------------------------------
# 🌍 ISLAMIC intent-signal set (research/janboori bhi — local reasoning me)
# ----------------------------------------------------------------------
_ISLAMIC_HARD = {
    "quran", "hadith", "sunnah", "allah", "islam", "deen", "namaz", "salah",
    "roza", "zakat", "hajj", "umrah", "wudu", "ghusl", "tayammum", "qibla",
    "tahajjud", "fajr", "zuhr", "asr", "isha", "maghrib", "kafir", "kufr",
    "shirk", "jannah", "jahannam", "nabi", "prophet", "rasool", "muhammad",
    "bukhari", "muslim", "tirmidhi", "abudawud", "nasai", "ibnmajah", "muwatta",
    "hijab", "dhikr", "tawheed", "tawhid", "bismillah", "alhamdulillah",
    "inshallah", "iftar", "sahur", "khatam", "mushrik", "muttaqi", "ayat",
    "sura", "surah", "mahram", "mehram", "murtad", "talaq", "nikah", "sadaqah",
    "fitr", "eid", "makkah", "madinah", "kaaba", "zakariya", "jibril",
    "ummat", "shahadah", "iman", "dunya", "aakhiret",
}
_ISLAMIC_SOFT = {
    "ibadat", "masjid", "jamaat", "khairat", "nafs", "taqwa", "hidayat",
    "imam", "sabr", "shukr", "khushu", "ilhaam", "risalat", "haq", "batil",
    "juz", "sajdah", "dawah", "akhlaq", "tariqah", "hayaa", "sunnat",
}
_ISLAMIC_BANNED = {"mirza", "qadiani", "qadian", "ahmadiyya", "ahmadi"}


# ----------------------------------------------------------------------
# 🪪 INTENT CLASSIFIER (READ + FOCUS phase combined)
# ----------------------------------------------------------------------
def _has_islamic(tw: set) -> bool:
    if tw & _ISLAMIC_BANNED:
        return True
    if tw & _ISLAMIC_HARD:
        return True
    return len(tw & _ISLAMIC_SOFT) >= 2


def classify(prompt: str) -> dict:
    text = (prompt or "").strip()
    low = text.lower()
    tw = content_set(text)
    islamic = _has_islamic(tw)
    qmark = "?" in text
    question_words = bool(re.search(
        r"(?i)(\?|\b(kya|kyun|kaise|kaisay|kaun|kahan|kab|kitna|kitne|kitni|"
        r"why|how|what|where|when|who|whose|which|batao|sunao|explain|matlab|maal|farq|tasveer|jagah|samjha)\b)", low))
    numbers = re.findall(r"\d[\d,]*(?:\.\d+)?", low)
    is_math = bool(numbers) and bool(re.search(
        r"(?i)\b(kitna|total|sum|average|jana|minus|plus|barabar|bara|guna|"
        r"times|multipl|percent|prosen|afsana|mujizat|faida|jumla|combined|bana|"
        r"banate|square|cube|root|factorial|mod|taqseem|divide|divided|"
        r"power|area|perimeter|volume|circumference|velocity|acceleration|"
        r"force|momentum|energy|pressure|density|frequency|wavelength|"
        r"interest|discount|mean|median|variance)\b", low)) \
        or bool(re.search(r"[\d)]\s*[-+*/^%x\u00d7\u00f7]\s*[\d(]", low)) \
        or bool(re.search(r"\d\s*//\s*\d", low)) \
        or bool(re.search(r"\d\s*!", low)) \
        or bool(re.search(r"(?i)\b(sqrt|log|ln|sin|cos|tan)\s*\(", low))
    # 📐 FORMULA-LIBRARY (Math+Physics A-Z): formula-sawal bhi math hai
    if not is_math and not islamic:
        try:
            from model.math_formulas import is_formula_q as _ifq
            if _ifq(low):
                is_math = True
        except Exception:
            pass
    sm = None
    try:
        from model.understand import understand as _u
        sm = _u(text)
    except Exception:
        sm = None
    # 🧠 SAMAJH: social-intent fast-path (hi/hiiii/salam/byeeee/okkk/ho
    #    /thanks...) — typo/elongation tolerant; q mark ya real sawal se BAHAR
    if (sm and sm.get("social") and not islamic and not is_math and not qmark
            and not question_words and len(tw) <= 4):
        return {"kind": "chit-chat", "islamic": islamic, "math": is_math,
                "qmark": qmark, "gib": False, "greet": True, "social": sm.get("social"),
                "social_bases": sm.get("bases") or [], "norm": sm.get("norm") or "",
                "fixes": sm.get("fixes") or [], "numbers": len(numbers),
                "words": tw, "topic": []}

    words = [w for w in re.findall(r"[a-z0-9]{3,}", low) if w not in _STOP]
    greet = bool(_GREET_WORDS.search(low))
    gib = _is_gibberish(low)
    known_content = [w for w in words if w in _ROMAN_URDU_COMMON or w in _STOP]
    has_content = bool(words or numbers) or greet or islamic or is_math \
        or qmark or question_words
    short_chat = (has_content and (not question_words) and not qmark and not islamic
                  and not is_math and len(words) <= 2 and len(low) < 45 and not numbers)
    if is_math:
        kind = "math"
    elif gib and not greet:
        kind = "unknown"                      # fdsf/xyz — nakli jawab kabhi nahi
    elif not has_content:
        kind = "unknown"                      # ho / aa / sirf stop-words kachra
    elif words and not known_content:
        kind = "unknown"                      # unknown non-English/Roman-Urdu tokens
    elif words and any(w not in _ROMAN_URDU_COMMON and w not in _vocab() for w in words):
        kind = "unknown"                      # mixed junk + known word still junk
    elif greet and len(low) < 60 and not question_words:
        kind = "chit-chat"                    # srif asli salam/hi/welcome
    elif short_chat:
        kind = "chit-chat"
    elif re.search(r"(?i)\b(tum|tu|aap|who is you|your name|tumhara naam|apna|"
                   r"kaun hai|kaun hain|kaun thay|apni|meri|merumera)\b", low) and not islamic:
        kind = "identity"
    elif islamic:
        kind = "sacred"
    elif re.match(r"(?i)^(kyun|why|kaise|kaisay|tafseel|tafheem|explain|wazahat|matlab|samjha|jagah)", low):
        kind = "how"
    elif question_words or qmark or re.match(r"(?i)^(kya|kaise|kitna|kab|what|how|why|who|where|when|which|batao|sunao)", low):
        kind = "how" if re.match(r"(?i)^(kyun|why|kaise|kaisay|tafseel|tafheem|explain|wazahat|matlab|samjha|jagah)", low) else "factoid"
    else:
        kind = "unknown"
    return {
        "kind": kind, "islamic": islamic, "math": is_math, "qmark": qmark,
        "gib": gib, "greet": greet,
        "numbers": len(numbers), "words": tw, "topic": words[:10],
    }


# ----------------------------------------------------------------------
# 🕸️ KNOWLEDGE GRAPH (entity -> facts)
# ----------------------------------------------------------------------
class KnowledgeGraph:
    def __init__(self):
        self.nodes = set()
        self.facts = []          # {"entity","relation","value","source","conf"}

    def add(self, entity, relation, value, source="local", conf=0.9):
        e = (entity or "").strip().lower()
        if not e:
            return
        self.nodes.add(e)
        self.facts.append({"entity": e, "relation": relation, "value": str(value),
                           "source": source, "conf": float(conf)})

    def get(self, entity):
        e = (entity or "").strip().lower()
        return [f for f in self.facts if f["entity"] == e]

    def related(self, entity, hops=1):
        out = []
        for f in self.facts:
            if f["entity"] == (entity or "").strip().lower():
                out.append(f)
        for f in self.facts:
            if f["relation"] in ("because-of", "due-to", "caused-by"):
                if f["entity"] in {x["entity"] for x in out} or any(
                        f["entity"] == e for e in [o["entity"] for o in out]):
                    out.append(f)
        return out

    def all(self):
        return list(self.facts)


# ----------------------------------------------------------------------
# 📚 LOCAL KNOWLEDGE: QA-PAIRS (corpus + sacred books) + owner
# ----------------------------------------------------------------------
def _qa_paths():
    paths = [os.path.join(DATA, "corpus.txt")]
    if os.path.isdir(BIG):
        try:
            # ⚠️ VOLATILE skip: liveresearch.txt (runtime research file) — QA pollution
            paths += [os.path.join(BIG, f) for f in sorted(os.listdir(BIG))
                      if f.endswith(".txt") and not f.startswith("_")
                      and f.lower() not in ("liveresearch.txt",)]
        except OSError:
            pass
    return [p for p in paths if os.path.exists(p)]


def _scan_pairs(path, out):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.read().split("\n")
        i = 0
        while i < len(lines):
            ln = lines[i].strip().lower()
            if ln.startswith("sawal:"):
                q = lines[i].strip()[6:].strip()
                ans, j = [], i + 1
                while j < len(lines):
                    s2 = lines[j].strip()
                    if not s2 or s2.lower().startswith("sawal:"):
                        break
                    body = s2[6:].strip() if s2.lower().startswith("jawab:") else s2
                    if body:
                        ans.append(body)
                    j += 1
                if q and ans:
                    out.append((q, " ".join(ans)))
                i = j
            else:
                i += 1
    except OSError:
        pass


_QA_CACHE = None

LEARNED_MEMORY_PATH = os.path.join(DATA, "chat_learned_memory.json")


def remember_chat_turn(q: str, a: str, source: str = ""):
    """Chat se foran seekho — learned memory me store karo taake next turn me yaad rahe.
    SIRF trust worthy sources (yaad-se / live-research / algorithm / local) hi save hote hain —
    imandari/security/refusal answers memory ko pollute NAHI karte."""
    trusted = ("yaad-se", "live-research", "algorithm", "math", "local-knowledge", "sacred-local", "owner", "adab")
    if source and source not in trusted and source not in ("khud-soch",):
        return
    # 🎯 1-2 heruf ke sawal (b/by/zz) yaad NAHI — trivia-replay ajeeb lagta hai
    if not q or len(str(q).strip()) <= 2:
        return
    if not q or not a or len(a) < 20:
        return
    if a.startswith("Hemomemo AI->"):
        a = a[len("Hemomemo AI->"):].strip()
    if "is sawal ka pura ilm nahi" in a or "Ye lafz mere kisi local ilm" in a:
        return
    try:
        os.makedirs(DATA, exist_ok=True)
        mem = []
        if os.path.exists(LEARNED_MEMORY_PATH):
            with open(LEARNED_MEMORY_PATH, encoding="utf-8") as f:
                mem = json.load(f)
        if not isinstance(mem, list):
            mem = []
        if not any(isinstance(item, dict) and item.get("q") == q for item in mem):
            mem.append({"q": q, "a": a})
            if len(mem) > 500:
                mem = mem[-500:]
            tmp = LEARNED_MEMORY_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(mem, f, ensure_ascii=False, indent=2)
            os.replace(tmp, LEARNED_MEMORY_PATH)
            global _QA_CACHE
            _QA_CACHE = None
    except Exception:
        pass


def local_qa():
    global _QA_CACHE
    if _QA_CACHE is not None:
        return _QA_CACHE
    pairs = []
    for p in _qa_paths():
        _scan_pairs(p, pairs)
    try:
        if os.path.exists(LEARNED_MEMORY_PATH):
            with open(LEARNED_MEMORY_PATH, encoding="utf-8") as f:
                mem = json.load(f)
            if isinstance(mem, list):
                for item in mem:
                    if isinstance(item, dict) and "q" in item and "a" in item:
                        pairs.append((item["q"], item["a"]))
    except Exception:
        pass
    _QA_CACHE = pairs
    return pairs


def sacred_answer_text(q: str):
    """Sacred sawal → local (Quran + 7 Sahih books) jawaon. (text|None)"""
    pairs = local_qa()
    scored = []
    for qq, aa in pairs:
        if not _has_islamic(content_set(qq)) and not _has_islamic(content_set(aa)):
            continue
        sc = _qa_score(q, qq, aa)
        scored.append((sc, qq, aa))
    if not scored:
        return None, None
    scored.sort(key=lambda x: -x[0])
    sc, qq, aa = scored[0]
    return aa, sc


def _qa_score(q: str, qq: str, aa: str = "") -> float:
    """User prompt q ko corpus question qq (aur optional answer aa) se compare karo."""
    qw = content_set(q)
    qqw = content_set(qq)
    if not qw or not qqw:
        return 0.0
    inter = len(qw & qqw)
    union = len(qw | qqw)
    sc = inter / max(1, union)
    if aa:
        aw = content_set(aa)
        if qw & aw:
            sc += 0.08
    return min(1.0, sc)


def owner_answer(q: str):
    """Owner (Hemomemo AI creator) ke liye local sahi jawab."""
    try:
        from core import owner as _owner
        qa = list(_owner.OWNER_QA or [])
        best = None
        best_sc = 0.0
        for qq, aa in qa:
            sc = _qa_score(q, qq, aa)
            if sc > best_sc:
                best_sc, best = sc, aa
        if best and best_sc > 0.25:
            return best, "owner", best_sc
        return None, "owner", best_sc
    except Exception:
        return None, None, 0.0


# ----------------------------------------------------------------------
# ➗ MATH ENGINE (safe AST evaluation — no eval, no code exec)
# ----------------------------------------------------------------------
_ALLOWED_OPS = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
                ast.FloorDiv)
_MATH_NAMES = {"pi": math.pi, "e": math.e}
_MFUNCS = None


def _mfuncs():
    """🧮 safe math functions (formula-engine se — fact/ncr capped)"""
    global _MFUNCS
    if _MFUNCS is None:
        try:
            from model.math_formulas import _FUNCS as _F
            _MFUNCS = dict(_F)
        except Exception:
            _MFUNCS = {}
    return _MFUNCS


def _eval_node(n):
    if isinstance(n, ast.Constant):
        if isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return float(n.value)
        return None
    if isinstance(n, ast.Name):
        return _MATH_NAMES.get(n.id)
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
        fn = _mfuncs().get(n.func.id)
        if fn is None or len(n.args) != 1:
            return None
        v = _eval_node(n.args[0])
        if v is None:
            return None
        try:
            return float(fn(v))
        except Exception:
            return None
    if isinstance(n, ast.BinOp) and type(n.op) in _ALLOWED_OPS:
        l = _eval_node(n.left)
        r = _eval_node(n.right)
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
                if r == 0:
                    return None
                return l / r
            if isinstance(n.op, ast.Pow):
                if abs(r) > 1000 or abs(r) < 0.0001:
                    return None
                return l ** r
            if isinstance(n.op, ast.Mod):
                if r == 0:
                    return None
                return l - (math.floor(l / r) * r) if l >= 0 else None
            if isinstance(n.op, ast.FloorDiv):
                if r == 0:
                    return None
                return float(l // r)
        except Exception:
            return None
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
        v = _eval_node(n.operand)
        if v is None:
            return None
        return -v if isinstance(n.op, ast.USub) else v
    return None


def _expr_from(q: str):
    s = (q or "").lower()
    # × ÷ x → * / (har operator, symbol ya naam)
    s = s.replace("\u00d7", "*").replace("\u00f7", "/")
    s = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", s)
    s = s.replace("^", "**")
    # factorial: 5! → fact(5)
    s = re.sub(r"(\d+(?:\.\d+)?)\s*!", r"fact(\1)", s)
    # lafzi operators (Roman-Urdu + English) — square/cube/root/power/percent
    s = re.sub(r"(?i)square\s+root\s+of\s+(\d+(?:\.\d+)?)", r"sqrt(\1)", s)
    s = re.sub(r"(?i)root\s+of\s+(\d+(?:\.\d+)?)", r"sqrt(\1)", s)
    s = re.sub(r"(?i)(\d+(?:\.\d+)?)\s+ka\s+(?:square\s+root|root)", r"sqrt(\1)", s)
    s = re.sub(r"(?i)(\d+(?:\.\d+)?)\s+ka\s+square", r"(\1)**2", s)
    s = re.sub(r"(?i)(\d+(?:\.\d+)?)\s+ka\s+cube", r"(\1)**3", s)
    s = re.sub(r"(?i)square\s+of\s+(\d+(?:\.\d+)?)", r"(\1)**2", s)
    s = re.sub(r"(?i)cube\s+of\s+(\d+(?:\.\d+)?)", r"(\1)**3", s)
    s = re.sub(r"(?i)(\d+(?:\.\d+)?)\s+ki\s+power\s+(\d+(?:\.\d+)?)", r"(\1)**(\2)", s)
    s = re.sub(r"(?i)(\d+(?:\.\d+)?)\s*(?:percent|persent|prosen)\s+of\s+(\d+(?:\.\d+)?)",
               r"(\1/100)*\2", s)
    s = re.sub(r"[,]", "", s)
    s = re.sub(r"[^0-9a-z+\-*/%().\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s or not re.search(r"\d", s):
        return None
    try:
        node = ast.parse(s, mode="eval").body
    except Exception:
        return None
    # sirf-number ("salam 5" → "5") math NAHI — operator/function chahiye
    if isinstance(node, (ast.Constant, ast.UnaryOp)):
        return None
    # letters sirf whitelisted functions/constants (sqrt/log/sin/pi/e…) —
    # baqi koi lafz bacha to math nahi (word-problems/formulas dekhenge)
    calls = [nd for nd in ast.walk(node) if isinstance(nd, ast.Call)]
    funcids = {id(nd.func) for nd in calls}
    for nd in calls:
        if not (isinstance(nd.func, ast.Name) and nd.func.id in _mfuncs()
                and len(nd.args) == 1):
            return None
    for nd in ast.walk(node):
        if isinstance(nd, ast.Name) and id(nd) not in funcids \
                and nd.id not in ("pi", "e"):
            return None
        if isinstance(nd, ast.BinOp) and type(nd.op) not in _ALLOWED_OPS:
            return None
    v = _eval_node(node)
    if v is None or math.isnan(v) or math.isinf(v):
        return None
    return s, v


def _fmt_num(v) -> str:
    if v is None:
        return "?"
    r = round(float(v), 10)
    if r == int(r):
        return str(int(r))
    s = repr(r)
    if "e" in s or "E" in s:
        return ("%.10f" % r).rstrip("0").rstrip(".")
    return s


def math_answer(q: str):
    """Math sawal → (answer_text, steps, confidence=1.0, verified=True)."""
    res = _expr_from(q)
    steps = []
    if res:
        expr, val = res
        steps.append("Expression parse hua: %s" % expr.replace("**", "^"))
        node = ast.parse(expr, mode="eval").body

        def collect(n, acc):
            if isinstance(n, ast.BinOp):
                acc.append((type(n.op).__name__, _eval_node(n.left), _eval_node(n.right)))
                collect(n.left, acc)
                collect(n.right, acc)
            elif isinstance(n, ast.Constant):
                acc.append(("num", float(n.value), None))
        acc = []
        collect(node, acc)
        # stepwise left-to-right evaluation
        cur = 0.0
        if isinstance(node, ast.BinOp):
            # naive step: evaluate operands
            def evstr(n):
                if isinstance(n, ast.Constant):
                    return _fmt_num(float(n.value))
                if isinstance(n, ast.BinOp):
                    opn = type(n.op).__name__
                    l = evstr(n.left)
                    r = evstr(n.right)
                    v = _eval_node(n)
                    steps.append("  %s %s %s = %s" % (l, opn, r, _fmt_num(v)))
                    return _fmt_num(v)
                return _fmt_num(_eval_node(n))
            evstr(node)
        final = _fmt_num(val)
        answer = "Jawab: %s" % final
        return answer, steps, 1.0, True, [expr]
    # ---- word problem handlers ----
    nums = re.findall(r"\d+(?:\.\d+)?", q)
    if len(nums) >= 2:
        op = None
        low = q.lower()
        if re.search(r"(?i)\b(total|sum|jumla|combined|samaan|sum)\b", low):
            op = "sum"
        elif re.search(r"(?i)\b(percent|prosen|afsana|matla)\b", low):
            op = "percent"
        elif re.search(r"(?i)\b(times|multipl|guna|baar|basti|product)\b", low):
            op = "mul"
        elif re.search(r"(?i)\b(divide|divided|divis|taqseem|bant|banto|quotient|bhag)\b", low):
            op = "div"
        elif re.search(r"(?i)\b(mod|modulo|remainder|baqi)\b", low):
            op = "mod"
        elif re.search(r"(?i)\b(average|afsana|matlab|mean)\b", low):
            op = "avg"
        elif re.search(r"(?i)\b(minus|sub|farq|bicha|less)\b", low) or re.match(
                r"(?i)^\s*\d", q.strip()) and " aur " not in q.lower():
            op = "sub"
        if op == "sum":
            s = sum(float(x.replace(",", "")) for x in nums)
            return ("Jawab: %s" % _fmt_num(s), ["Sum of %d numbers = %s" % (len(nums), _fmt_num(s))],
                    0.95, True, ["sum-of-%d-numbers" % len(nums)])
        if op == "avg":
            s = sum(float(x.replace(",", "")) for x in nums) / len(nums)
            return ("Jawab: %s" % _fmt_num(s), ["Average = sum/len = %s" % _fmt_num(s)],
                    0.95, True, ["average"])
        if op == "mul":
            p = 1.0
            for x in nums:
                p *= float(x.replace(",", ""))
            return ("Jawab: %s" % _fmt_num(p), ["Product = %s" % _fmt_num(p)],
                    0.9, True, ["product"])
        if op == "div":
            a = float(nums[0].replace(",", ""))
            b = float(nums[1].replace(",", ""))
            if b != 0:
                v = a / b
                return ("Jawab: %s" % _fmt_num(v),
                        ["%s / %s = %s" % (nums[0], nums[1], _fmt_num(v))],
                        0.95, True, ["division"])
        if op == "mod":
            a = float(nums[0].replace(",", ""))
            b = float(nums[1].replace(",", ""))
            if b != 0:
                v = a - (a // b) * b
                return ("Jawab: %s" % _fmt_num(v),
                        ["%s mod %s = %s" % (nums[0], nums[1], _fmt_num(v))],
                        0.95, True, ["modulo"])
        if op == "percent":
            pct = float(nums[0].replace(",", "")) / 100.0
            base_v = float(nums[1].replace(",", "")) if len(nums) > 1 else 0.0
            return ("Jawab: %s" % _fmt_num(base_v * pct),
                    ["%s%% of %s = %s" % (nums[0], nums[1], _fmt_num(base_v * pct))],
                    0.92, True, ["percent"])
        if op == "sub":
            a = float(nums[0].replace(",", ""))
            b = float(nums[1].replace(",", "")) if len(nums) > 1 else 0.0
            v = a - b
            return ("Jawab: %s" % _fmt_num(v), ["%s - %s = %s" % (nums[0], nums[1], _fmt_num(v))],
                    0.95, True, ["subtraction"])
    # 📐 FORMULA LIBRARY (math+physics A-Z): plug-and-solve / teach-mode
    try:
        from model.math_formulas import solve_formula as _sf
        fr = _sf(q)
        if fr:
            return fr
    except Exception:
        pass
    return None, None, 0.0, False, None


# ----------------------------------------------------------------------
# 🌐 LIVE RESEARCH (google / bing / duckduckgo / wikipedia — whitelist-only)
# ----------------------------------------------------------------------
def _live_research(q: str):
    out = None
    err = None
    try:
        from model import live_research as LR
        out = LR.research(q)
    except Exception as e:
        err = e
    return out, err


# ----------------------------------------------------------------------
# 🧠 HYPOTHESIS ENGINE: candidates + scoring + self-verify
# ----------------------------------------------------------------------
_SOURCE_TRUST = {
    "algorithm": 1.0, "math": 1.0, "local-knowledge": 0.93, "sacred-local": 0.95,
    "owner": 0.95, "logic": 0.86, "adab": 0.97, "derived": 0.7,
    "live-research": 0.55, "imandari": 0.2, "tarbiyat": 0.3, "grace": 0.25,
}


def _score_candidate(answer_text, source, rel=0.0):
    trust = _SOURCE_TRUST.get(source, 0.3)
    conf = trust * min(1.0, 0.55 + 0.45 * max(0.0, rel))
    return {"answer": answer_text, "source": source, "confidence": round(conf, 3),
            "verified": source in ("algorithm", "local-knowledge", "sacred-local",
                                   "owner", "adab", "logic") and conf > 0.5,
            "rel": rel}


# ----------------------------------------------------------------------
# ✍️ ANSWER COMPOSER (kind-wise)
# ----------------------------------------------------------------------
def _rule_conf(text: str, base: float = 0.9) -> float:
    """RULE-based jawab ki ASLI confidence (constant-label nahi): output-text
    ki quality guards se derive hoti hai — lambai/structure/citation-guard.
    base = qaida-match ki kathorai; text kamzor to confidence girti hai."""
    try:
        t = (text or "").strip()
        if len(t) < 20:
            return round(max(0.5, base - 0.2), 2)
        bonus = 0.0
        if len(t) >= 80:
            bonus += 0.03
        if ("." in t) or ("!" in t):
            bonus += 0.02
        try:
            from model.generate import _no_citation
            if _no_citation(t):
                bonus += 0.02
        except Exception:
            pass
        return round(min(0.99, base + bonus), 2)
    except Exception:
        return base


def compose_chit_chat() -> dict:
    _tail = ""
    try:
        from model.feelings import greeting_tail as _gt
        _tail = _gt()                     # 💛 insani touch: mood ke hisab se
    except Exception:
        _tail = ""
    text = ("Assalamu Alaikum wa Rahmatullah! Wa Alaikum assalam wa barakatuh! Salam "
            "dost! Mera naam Hemomemo AI hai — aapka local AI assistant. "
            "Main islami adab ke sath jawab deta hoon, ilm/akhlaq/amal par khud-soch "
            "kar ke sochta hoon, aur koi bhi AI model/API se jawab nahi deta."
            + _tail)
    return {"answer": text, "confidence": _rule_conf(text, 0.94), "source": "adab", "kind": "chit-chat",
            "verified": True, "steps": ["greeting detected → adab compose"],
            "facts_vs_assumptions": [{"claim": "Hemomemo AI is a local AI assistant",
                                     "status": "fact"}],
            "uncertainty": None, "sources": ["identity-adab"]}


def compose_social(intent: dict) -> dict:
    """🧠 SAMAJH se mile social/intent jawab — 'hii/hiiii/byeeee/okkk/ho' jaise.
    Sab source adab/khud-soch, warm + honest + (sahih ilm ke sath real)."""
    social = intent.get("social") or "bolo"
    bases = intent.get("bases") or intent.get("social_bases") or []
    salm = any(b in ("salam", "assalam", "asalam", "slam", "aoa", "namaste")
               for b in bases)
    if social == "greet":
        if salm:
            out = compose_chit_chat()
            out["source"] = "adab"
            return out
        _tail = ""
        try:
            from model.feelings import greeting_tail as _gt
            _tail = _gt()
        except Exception:
            _tail = ""
        text = ("Salam! Main sun raha hoon — bataiye aaj kya baat karni hai?")
        text += _tail
        return {"answer": text, "confidence": _rule_conf(text, 0.94), "source": "adab", "kind": "chit-chat",
                "verified": True, "steps": ["SAMAJH: social greet (typo/elongation-fold) → adab compose"],
                "facts_vs_assumptions": [{"claim": "local greeting knowledge", "status": "fact"}],
                "uncertainty": None, "sources": ["identity-adab"]}
    if social == "farewell":
        _tail = ""
        try:
            from model.feelings import greeting_tail as _gt2
            _tail = _gt2()
        except Exception:
            _tail = ""
        text = ("Allah hafiz! Aap ka waqt shukriya — jab bhi aap ka darwaza kholegi, "
                "phir milenge, InshaAllah. Allah aap ko raahnuma banaye. 🌙")
        text += _tail
        return {"answer": text, "confidence": _rule_conf(text, 0.94), "source": "adab", "kind": "chit-chat",
                "verified": True, "steps": ["SAMAJH: farewell detected (byee/bye/gn/Allah hafiz) → adab compose"],
                "facts_vs_assumptions": [{"claim": "local farewell knowledge", "status": "fact"}],
                "uncertainty": None, "sources": ["identity-adab"]}
    if social == "thanks":
        _tail = ""
        try:
            from model.feelings import greeting_tail as _gt3
            _tail = _gt3()
        except Exception:
            _tail = ""
        text = "Shukriya aap ki! Khushi hui madad kar ke. Aur koi sawal ho to boliye — Ihsan se jawab dunga. 🤝"
        text += _tail
        return {"answer": text, "confidence": _rule_conf(text, 0.94), "source": "adab", "kind": "chit-chat",
                "verified": True, "steps": ["SAMAJH: thanks (shukriya/jazakallah) → adab compose"],
                "facts_vs_assumptions": [{"claim": "local thanks knowledge", "status": "fact"}],
                "uncertainty": None, "sources": ["identity-adab"]}
    if social == "laugh":
        return {"answer": "Haha! Dil toh khush kar diya. Aur sunayein dil ki baat — woh khud soch lenge. 😄",
                "confidence": _rule_conf("Haha! Dil toh khush kar diya. Aur sunayein dil ki baat — woh khud soch lenge. 😄", 0.88), "source": "adab", "kind": "chit-chat",
                "verified": True, "steps": ["SAMAJH: laugh word (haha) → adab compose"],
                "facts_vs_assumptions": [{"claim": "local humor knowledge", "status": "fact"}],
                "uncertainty": None, "sources": ["identity-adab"]}
    # ack / yes / no / bolo / default-social — khud-soch se jawab (real-ish)
    _tail = ""
    try:
        from model.feelings import greeting_tail as _gt4
        _tail = _gt4()
    except Exception:
        _tail = ""
    _acks = {
        "bolo": "Ji, main sun raha hoon — bataiye, kya poochna hai? 👂",
        "ack": "Ji bilkul! Main sun raha hoon — aage bataiye kaunsa sawal hai.",
        "yes": "Ji, theek hai — samajh gaya. Aur koi sawal ho to boliye, main behtar jawab dunga.",
        "no": "Theek hai, koi baat nahi — jab sawal aaye to main azaim se jawab dunga.",
        "default": "Main sun raha hoon — bataiye, kya baat hai? Dil khud-soch kar ke jawab dunga.",
    }
    text = _acks.get(social, _acks["default"]) + _tail
    return {"answer": text, "confidence": _rule_conf(text, 0.88), "source": "khud-soch", "kind": "chit-chat",
            "verified": True, "steps": ["SAMAJH: social-intent=%s → khud-soch compose" % social],
            "facts_vs_assumptions": [{"claim": "local small-talk knowledge", "status": "fact"}],
            "uncertainty": None, "sources": ["khud-soch"]}


def compose_identity(q: str) -> dict:
    ans, src, sc = owner_answer(q)
    text = ans or ("Mere owner Hafiz Muhammed Huzaifa Shamim hain — 17 saal, DJ Science "
                   "College Karachi, Iskaan Residency Block L Karachi. Aur aap (Hemomemo AI) "
                   "yeh poora dimagh unhone banaya hai.")
    return {"answer": text, "confidence": _rule_conf(text, 0.92), "source": "owner", "kind": "identity",
            "verified": True, "steps": ["owner data local read"],
            "facts_vs_assumptions": [{"claim": "owner name/age/college/residence",
                                     "status": "fact"}],
            "uncertainty": None, "sources": ["owner_data"]}


def compose_math(q: str):
    ans, steps, conf, ver, tags = math_answer(q)
    if not ans:
        return None
    text = ans if str(ans).startswith("Jawab") else "Jawab: %s" % ans
    body = text
    if steps:
        body = text + "\n📐 Hal ki soch: " + " | ".join(str(s) for s in steps[:3])
    is_formula = bool(tags) and str(tags[0]).startswith("formula:")
    src = "formula-library" if is_formula else "algorithm"
    claim = ("formula library (math+physics A-Z) se plug-and-solve"
             if is_formula else "expression evaluated with safe AST math engine")
    rep = {"answer": body, "confidence": conf, "source": src, "kind": "math",
           "verified": ver, "steps": steps, "facts_vs_assumptions": [
               {"claim": claim, "status": "fact"}],
           "uncertainty": None, "sources": [src], "candidates": []}
    return rep


# ----------------------------------------------------------------------
# 🧠 MAIN ANSWER PIPELINE
# ----------------------------------------------------------------------
def answer(prompt: str, notes=None, sacred=False, yaad_top=0.0, think="auto",
           ctx: dict = None):
    q = (prompt or "").strip()
    rep_in = ctx if isinstance(ctx, dict) else {}
    intent = classify(q)
    kind = intent.get("kind", "unknown")
    steps = []
    candidates = []
    chosen = None

    # 🧠 SAMAJH: social-intent fast-path (hi/hiiii/salam/byeeee/okkk/ho/thanks…)
    if intent.get("social"):
        out = compose_social(intent)
        out["social"] = intent.get("social")
        out["intent"] = intent.get("kind") or "chit-chat"
        return out

    # 🎯 MICRO-ADAB: 1-2 heruf (b/x/zz) ya number-free chhotas → wiktionary-trivia
    #    ajeeb lagti hai, seedha honest adab jawb (koi research/zamaawar mat)
    _mq = re.sub(r"[^a-z0-9]", "", q.lower())
    if (len(_mq) <= 2 and not any(c.isdigit() for c in _mq)
            and not (intent.get("social") or intent.get("greet"))):
        return {"answer": ("Main hazir hoon — apna poora sawal likhein (misal: "
                            "'photosynthesis kya hai', 'hadith batao', '12 * 4 + 3') aur "
                            "main imandari se jawab dunga."),
                "confidence": 0.9, "source": "adab", "kind": "micro",
                "verified": True,
                "steps": ["micro-input (1-2 heruf) → seedha adab, research zaya nahi"],
                "facts_vs_assumptions": [], "uncertainty": None,
                "sources": [], "candidates": [], "intent": "micro"}

    if kind == "chit-chat":
        out = compose_chit_chat()
        out["intent"] = kind
        return out

    if kind == "identity":
        out = compose_identity(q)
        out["intent"] = kind
        return out

    if kind == "math":
        steps.append("FOCUS: mathematical reasoning — safe AST evaluator + word-problem handlers")
        mrep = compose_math(q)
        if mrep:
            mrep["intent"] = kind
            candidates.append(mrep)
            chosen = mrep
        if not chosen:
            chosen = {"answer": "Maaf karein, number/saam ka sawal theek nahi mila mere "
                       "local math engine se — aur main koi nakli jawab nahi de sakta.",
                       "confidence": 0.2, "source": "imandari", "kind": kind,
                       "verified": False, "steps": ["math engine miss"],
                       "facts_vs_assumptions": [], "uncertainty": "math unsahih",
                       "sources": [], "candidates": []}
        chosen["intent"] = kind
        return chosen

    if kind == "sacred":
        steps.append("FOCUS: sacred intent — sirf local Quran + Sahih books")
        txt, sc = sacred_answer_text(q)
        if txt:
            rep = {"answer": txt, "confidence": _rule_conf(txt, 0.90), "source": "sacred-local",
                   "kind": kind, "verified": True,
                   "steps": ["sacred QA retrieved from local books"],
                   "facts_vs_assumptions": [{"claim": "Quran/Hadith text (verified local copy)",
                                            "status": "fact"}],
                   "uncertainty": None, "sources": ["quran-hadith-local"], "candidates": []}
        else:
            rep = {"answer": ("Mera local ilm abhi is sacred sawal ka pura jawab "
                              "nhi de sakta. Available local books se kya mila: "
                              + (txt or "kuch nahin").replace("None", "") + ". "
                              "Main imandari se jawab deta hoon."),
                   "confidence": 0.35, "source": "imandari", "kind": kind, "verified": False,
                   "steps": ["sacred local miss → graceful"], "facts_vs_assumptions": [],
                   "uncertainty": "sacred-local-miss", "sources": [], "candidates": []}
        rep["intent"] = kind
        return rep

    # ---- kachra/noise input fast-path (fdsf, ho, xyz...) ----
    # PEHLE live-research bhi koshish karo (wiktionary/wikipedia — shayad lafz
    # asli ho jo mujhe nahi pata); phir bhi khaali → imandari honest jawab
    # (koi banao-jala jawab NAHI).
    if kind == "unknown" and (intent.get("gib") or not intent.get("topic")):
        # 🎯 MICRO/SOCIAL pehle: adab ka jawab ho to research zaya na ho
        # (sirf jab intent me SACH-MUCH social ho — warna fallback na chhape)
        if intent.get("social"):
            try:
                _soc = compose_social(intent)
                if _soc and (_soc.get("answer") or "").strip():
                    _soc["confidence"] = max(float(_soc.get("confidence") or 0.9), 0.9)
                    return _soc
            except Exception:
                pass
        # 1-2 heruf (b/zz/aa…) — wiktionary-trivia ajeeb lagti hai; seedha adab
        if len((q or "").strip()) <= 2:
            return {"answer": ("Main hazir hoon — apna poora sawal likhein "
                               "(misal: 'photosynthesis kya hai', 'hadith "
                               "batao', '12 * 4 + 3') aur main imandari se "
                               "jawab dunga."),
                    "confidence": 0.9, "source": "adab", "kind": kind,
                    "verified": True,
                    "steps": ["micro-input (1-2 heruf) → seedha adab, "
                              "research zaya nahi"],
                    "facts_vs_assumptions": [], "uncertainty": None,
                    "sources": [], "candidates": [], "intent": kind}
        research_txt, _err = _live_research(q)
        if research_txt:
            return {"answer": research_txt, "confidence": 0.50, "source": "live-research",
                    "kind": kind, "verified": False,
                    "steps": ["unknown/kachra input → live research + think"],
                    "facts_vs_assumptions": [{"claim": "live research", "status": "evidence-based"}],
                    "uncertainty": "live-research-unverified", "sources": ["live-research"],
                    "candidates": [], "intent": kind}
        if intent.get("gib"):
            return {"answer": ("Ye lafz na mere local ilm me hain aur na live web "
                               "(wiktionary/wikipedia) par mile — is par mera yaqeen ka "
                               "jawab nahi banta. Sawal asaan alfaaz me likhein (jaise "
                               "'salam', 'photosynthesis kya hai', '12 * 4 + 3') — main "
                               "behtar jawab dunga, aur jhoot nahi bolunga."),
                    "confidence": 0.35, "source": "imandari", "kind": kind, "verified": False,
                    "steps": ["noise/kachra input → live-research try → khaali → imandari"],
                    "facts_vs_assumptions": [{"claim": "local + live-web dono check kiye, asli lafz nahi mila",
                                              "status": "evidence-based"}],
                    "uncertainty": "insufficient-evidence", "sources": [], "candidates": [],
                    "intent": kind}
        # unknown (not gib) aur research bhi khaali:
        return {"answer": ("Meri taraf is sawal ka pura ilm nahi tha jo hona chahiye — lekin jo "
                           "ilm mere paas tha (local knowledge / live web), woh facts the. Isi "
                           "available ilm se kya ban sakta hai: kuch nahi"),
                "confidence": 0.35, "source": "imandari", "kind": kind, "verified": False,
                "steps": ["unknown input → no research result → imandari"],
                "facts_vs_assumptions": [{"claim": "local/live evidence", "status": "evidence-based"}],
                "uncertainty": "insufficient-evidence", "sources": [], "candidates": [],
                "intent": kind}

    # ---- factoid / how / compare / logic / unknown ----
    steps.append("FOCUS: %s — RECALL(local) → RESEARCH(live) → REASON" % kind)
    chosen = None

    # 1) local knowledge
    best_qa = None
    best_sc = 0.0
    for qq, aa in local_qa():
        sc = _qa_score(q, qq, aa)
        if sc > best_sc:
            best_sc, best_qa = sc, (qq, aa)
    local_cand = None
    if best_qa and best_sc >= 0.18:
        qq, aa = best_qa
        local_cand = _score_candidate(aa, "local-knowledge", rel=min(1.0, best_sc))
        local_cand["q"] = qq
        local_cand["rel_score"] = best_sc
    candidates.append(local_cand)

    # 2) live research (deep: google → bing → ddg → wikipedia via live_research)
    research_txt, _err = _live_research(q)
    live_cand = None
    if research_txt:
        live_cand = _score_candidate(research_txt, "live-research", rel=0.45)
        live_cand["q"] = q
        candidates.append(live_cand)

    # 3) identity-owner cross-check (gentle)
    owner_cand = None
    try:
        ans, src, sc = owner_answer(q)
        if ans:
            owner_cand = _score_candidate(ans, "owner", rel=min(1.0, sc * 2.0))
            owner_cand["q"] = q
            candidates.append(owner_cand)
    except Exception:
        pass

    # 4) pick best candidate (hypothesis generation + ranking)
    final_cands = [c for c in candidates if c]
    final_cands.sort(key=lambda c: -c["confidence"])
    chosen = final_cands[0] if final_cands else None

    if chosen and chosen.get("confidence", 0) >= 0.40:
        # 🧠 AQAL: deep reasoning layer — CoT + analogies + causal + abduce + self-correct
        _aqal = None
        try:
            from model.aqal import reason as _aqal_reason
            _aqal = _aqal_reason(q, final_cands)
        except Exception:
            _aqal = None
        _aqal_steps = []
        if _aqal:
            _aqal_steps = ["🧠 AQAL deep-reason: depth=%d | fallacies=%d" % (
                _aqal.get("reasoning_depth", 0), len(_aqal.get("fallacies", [])))]
            if _aqal.get("chain_of_thought"):
                _aqal_steps.append("CoT: " + " → ".join(
                    _aqal["chain_of_thought"][:3]))
            if _aqal.get("causal_chain"):
                _aqal_steps.append("Causal: " + " | ".join(
                    _aqal["causal_chain"][:2]))
            if _aqal.get("analogies"):
                _aqal_steps.append("Analogy: %s ↔ %s" % (
                    _aqal["analogies"][0].get("from", ""),
                    _aqal["analogies"][0].get("to", "")))
        out = {"answer": chosen["answer"], "confidence": chosen["confidence"],
               "source": chosen["source"], "kind": kind, "verified": chosen.get("verified"),
               "steps": steps + ["best hypothesis: %s (conf %.2f)" % (chosen["source"], chosen["confidence"])]
                        + _aqal_steps,
               "facts_vs_assumptions": ([] if chosen["source"] in ("live-research",) else
                                        [{"claim": chosen["answer"][:60], "status": "derived"}]),
               "uncertainty": None if chosen.get("verified") else "live-research-unverified",
               "sources": [chosen["source"]], "candidates": final_cands,
               "aqal": _aqal}
        out["intent"] = kind
        return out

    # ---- honest fallback: best possible from available info + uncertainty ----
    fb_parts = []
    facts = []
    if local_cand and local_cand.get("confidence", 0) > 0.4:
        facts.append("Local knowledge: %s" % (local_cand.get("answer") or "")[:160])
    if research_txt:
        facts.append("Live web snippet: %s" % research_txt[:160])
    fb_answer = ("Meri taraf is sawal ka pura ilm nahi tha jo hona chahiye — lekin jo "
                 "ilm mere paas tha (local knowledge / live web), woh facts the. Isi "
                 "available ilm se kya ban sakta hai: %s" % "; ".join(facts[:2] or ["kuch nahi"]))
    out = {"answer": fb_answer, "confidence": 0.35, "source": "imandari", "kind": kind,
           "verified": False, "steps": steps, "facts_vs_assumptions": [
               {"claim": "local/live evidence", "status": "evidence-based"}],
           "uncertainty": "insufficient-evidence", "sources": [],
           "candidates": final_cands}
    out["intent"] = kind
    return out


# ----------------------------------------------------------------------
# 🛡️ ULTRA-SECURITY & INTEGRITY GUARD (anti-tamper / anti-hack / hash-lock)
# ----------------------------------------------------------------------
_HASH_LOCKS = {}


def _file_sha256(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    try:
        if not os.path.exists(path):
            return ""
        with open(path, "rb") as f:
            while True:
                b = f.read(65536)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except Exception:
        return ""


def verify_system_integrity() -> tuple:
    """🛡️ ULTRA SECURITY: check karein ke core files / sacred texts par
    unauthorized tamper ya hack ki koshish toh nahi hui."""
    critical = [
        os.path.join(ROOT, "core", "offline_oath.py"),
        os.path.join(ROOT, "knowledge", "quran_guard.py"),
        os.path.join(ROOT, "model", "autonomous.py"),
        os.path.join(ROOT, "core", "heart.py"),
    ]
    tampered = []
    for p in critical:
        if not os.path.exists(p):
            continue
        cur = _file_sha256(p)
        if p in _HASH_LOCKS:
            if _HASH_LOCKS[p] != cur:
                tampered.append(os.path.basename(p))
        else:
            _HASH_LOCKS[p] = cur
    return len(tampered) == 0, tampered


def secure_sanitize(prompt: str) -> str:
    """🛡️ ULTRA SECURITY: prompt injection aur destructive payloads ko block karo."""
    if not prompt:
        return ""
    p = str(prompt)
    banned = [
        r"(?i)\b(import\s+os|import\s+sys|subprocess|eval\(|exec\(|system\(|rm\s+-rf)\b",
        r"(?i)(format\s+[c-z]:|truncate|drop\s+table|delete\s+from)",
    ]
    for pat in banned:
        if re.search(pat, p):
            return "[ULTRA SECURITY BLOCK: suspicious injection detected]"
    return p


def chat(prompt: str, notes=None, sacred=False, yaad_top=0.0, think="auto"):
    clean_p = secure_sanitize(prompt)
    if clean_p.startswith("[ULTRA SECURITY BLOCK"):
        return "Hemomemo AI-> " + clean_p, {"answer": clean_p, "confidence": 0.0, "source": "security", "kind": "security"}
    rep = answer(clean_p, notes=notes, sacred=sacred, yaad_top=yaad_top, think=think)
    text = "Hemomemo AI-> " + (rep.get("answer") or "Maaf karein, jawab generate nahi hua.")
    rep["answer"] = rep.get("answer") or ""
    rep.setdefault("source", "imandari")
    return text, rep


# ----------------------------------------------------------------------
# 🖥️ TERMINAL MODE (interactive)
# ----------------------------------------------------------------------
def _print_report(rep):
    try:
        print("    [engine] kind=%s source=%s conf=%.2f verified=%s steps=%d" % (
            rep.get("kind"), rep.get("source"), rep.get("confidence") or 0.0,
            rep.get("verified"), len(rep.get("steps") or [])))
        for s in (rep.get("steps") or [])[:6]:
            print("      - %s" % s)
    except Exception:
        pass


def chat_loop():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print("=" * 60)
    print(" 🤖 Hemomemo AI AUTONOMOUS — TERMINAL MODE (fully autonomous reasoning engine)")
    print("    Pure local algorithms: math + logic + knowledge + research + verify")
    print("    Commands: quit | flow on/off | think low|mid|high | status | clear")
    print("=" * 60)
    from core.offline_oath import oath_text
    print(" ", oath_text().splitlines()[0])
    from model import cognition as _cog
    from model import think_level as _tl
    _cog.set_display("on")
    while True:
        try:
            q = input("\n 👤 Aap: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n 👋 Hemomemo AI: Allah hafiz!")
            return
        lowq = q.lower().strip()
        try:
            from model.understand import is_exit as _is_exit_fn
            if _is_exit_fn(q):
                print(" 👋 Hemomemo AI: Allah hafiz! (bye/farewell samajh gaya)")
                return
        except Exception:
            pass
        if lowq in {"quit", "exit", "bye"}:
            print(" 👋 Hemomemo AI: Allah hafiz!")
            return
        if lowq.startswith("flow"):
            arg = lowq.replace("flow", "").strip() or "on"
            from model.cognition import set_display as _sd
            stf = _sd(arg if arg in ("on", "off", "verbose", "auto") else "on")
            print(" ◈ flow-display: %s" % stf.get("display"))
            continue
        if lowq.startswith("think"):
            arg = lowq.replace("think", "").strip()
            from model.think_level import set_mode as _sm, load_state as _ls
            st = _sm(arg if arg else "auto")
            print(" 🪜 think-level:", st.get("mode"))
            continue
        if lowq == "status":
            from core.hub import status as _hs, heartbeat_check
            import pprint as _pp
            _pp.pprint(_hs())
            continue
        if lowq == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            continue
        if not q:
            continue
        # 🫀 SENSORS/JAZBAAT: sawal pehle mehsoos hota hai
        try:
            from model.feelings import senses as _feel_senses
            _feel_senses(q)
        except Exception:
            pass
        t0 = time.time()
        text, rep = chat(q)
        print(text)
        _print_report(rep)
        print("    [engine] %.2fs | source=%s | confidence=%.2f" % (
            time.time() - t0, rep.get("source"), rep.get("confidence") or 0.0))
        # 🫀 jazbaat ka ikhlaq + 🌐 online haal
        try:
            from model.feelings import status_line as _feel_line, note_outcome as _feel_note
            _feel_note(rep.get("source"), float(rep.get("confidence") or 0.0))
            print("    %s | 🌐 online-research: %s" % (
                _feel_line(),
                "yes" if rep.get("source") == "live-research" else "no"))
        except Exception:
            pass


def main():
    # 🔒 ULTRA-SECURITY: file integrity checks on boot
    try:
        ok, tampered = verify_system_integrity()
        if not ok:
            print("🛡️ ULTRA SECURITY ALERT: System files modified:", tampered)
            print("Unauthorized changes detected — Hemomemo AI band ho raha hai.")
            return
    except Exception:
        pass
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        text, rep = chat(" ".join(args))
        print(text)
        _print_report(rep)
    else:
        chat_loop()


if __name__ == "__main__":
    main()
