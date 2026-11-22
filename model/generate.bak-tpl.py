"""
💬 generate.py — Hemomemo AI :: FULLY AUTONOMOUS OFFLINE Chat (no API, no cloud, no Ollama)

Bina kisi bahar-ki-API ke reliability - 3 steps:
 1. YAAD: local knowledge (corpus) se milte-julte ilm notes (jawab-copy NAHI — sirf yaad)
 2. Model KHUD sochta hai: bio-brain tick + yaad-dahai priming + best-of-5 sampling
    (koi fixed Sawal->Jawab map NAHI; Quran guard sab se pehle)
 3. Quran: sirf READ quotes; edit-request par sakht inkar (SacredTextGuard)

Run: python model\\generate.py    ya    python model\\generate.py "sawal yahan"
"""
import difflib
import os
import re
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(HERE)
else:
    ROOT = os.path.dirname(HERE)
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from model.tokenizer import CharTokenizer  # noqa: E402
from model.nn import LSTMBrain             # noqa: E402
from knowledge.quran_guard import SacredTextGuard  # noqa: E402

GUARD = SacredTextGuard()
CKPT_DIR = os.path.join(ROOT, "model", "checkpoints")
if not os.path.isdir(CKPT_DIR) and os.path.isdir(
        os.path.join(HERE, "checkpoints")):
    CKPT_DIR = os.path.join(HERE, "checkpoints")   # dev-fallback
DATA = os.path.join(ROOT, "data")
BIG = os.path.join(DATA, "corpus_big")

# retrieval me fayda na dene wale aam words
STOP = {"kya", "kyun", "hai", "hain", "ho", "hoon", "hum", "ka", "ke", "ki", "ko",
        "se", "me", "mein", "par", "aap", "tum", "tu", "main", "and", "the", "of",
        "what", "how", "why", "you", "your", "is", "are", "do", "does", "aur",
        "or", "kaun", "kaisa", "kitna", "kitne"}

_CACHE = {"mtime": None, "tok": None, "brain": None}
_QA_INDEX = None
_WORDS = None
_REPEATED = {}   # normalized sawal -> kitni dafa poocha (deep thinking)
_LAST_CHAT_TS = 0.0   # ❤️ heart isko dekhar IDLE-detect karta hai
_DAILY_CTX = {"date": "", "n": 0}   # 🔁 daily token/context reset (har din 12:00 AM)


def _daily_token_reset():
    """🔁 DAILY TOKEN/CONTEXT RESET — har din 12:00 AM (user qanoon): aaj ki
    context/token counter reset ho jati hai (koi bhi AI-API / cloud nahi — sirf
    is local dimagh ka daily counter)."""
    global _DAILY_CTX
    _d = time.strftime("%Y-%m-%d", time.localtime())
    if _DAILY_CTX.get("date") != _d:
        _DAILY_CTX["date"] = _d
        _DAILY_CTX["n"] = 0
    return _DAILY_CTX


def corpus_files():
    paths = [os.path.join(DATA, "corpus.txt")]
    if os.path.isdir(BIG):
        paths += [os.path.join(BIG, f) for f in sorted(os.listdir(BIG)) if f.endswith(".txt")]
    return [p for p in paths if os.path.exists(p)]


def corpus_text():
    parts = []
    for p in corpus_files():
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                parts.append(f.read().strip())
        except OSError:
            pass
    raw = "\n\n".join(parts)
    # 📐 tokenizer alphabet = TRAINING alphabet: >127 chars (²/√/π…) hatao —
    # warna vocab badal jati hai aur purane checkpoints skip hone lagte hain
    if any(ord(c) > 127 for c in raw):
        raw = raw.encode("ascii", "ignore").decode("ascii")
    return raw


def fit_tokenizer():
    """Chat aur training ka EXACT same vocab:
    1) model/checkpoints/vocab.json (training ne banaya) — model ki asli zuban
    2) nahi mile to corpus-se fresh fit (fallback)"""
    tok = CharTokenizer()
    vpath = os.path.join(CKPT_DIR, "vocab.json")
    if os.path.exists(vpath):
        try:
            tok.load(vpath)
            return tok
        except Exception:
            pass
    tok.fit_from_scratch(set(corpus_text()))
    return tok


def _tok():
    """Corpus-fitted tokenizer — ek dafa banao, cache rakho."""
    if _CACHE["tok"] is None:
        _CACHE["tok"] = fit_tokenizer()
    return _CACHE["tok"]


def best_checkpoint():
    """Naya -> purana checkpoints walk karo; SIRF wo npz lo jiska embed-vocab
    corpus se EXACT milta ho. Stray (mismatched) checkpoint par rukna mana hai —
    usko skip karo; jab tak match na mile, chat RAG-only chalta rahega.
    🧠 CHAAR-DIMAGH RULE: yahan sirf HEMOMASTER (pehla 50M dimagh) — helper/
    verify/deep apne modules se load hote hain (hemohelper_/hemoverify_/hemodeep_)."""
    tok = _tok()
    cks = [os.path.join(CKPT_DIR, f) for f in os.listdir(CKPT_DIR)
           if f.endswith(".npz") and f.startswith("hemomaster")
           and not f.endswith(".tmp.npz")]
    cks.sort(key=os.path.getmtime, reverse=True)
    for ck in cks:
        try:
            with np.load(ck) as d:
                vocab = int(d["embed"].shape[0])
        except OSError:
            continue
        if vocab == tok.vocab_size:
            return ck
        print("  [chat] skip %s (vocab %d vs corpus %d)" % (
            os.path.basename(ck), vocab, tok.vocab_size))
    return None


def _load_model(ck):
    mtime = os.path.getmtime(ck)
    if _CACHE["mtime"] != mtime:
        d = np.load(ck)
        vocab, hidden = int(d["embed"].shape[0]), int(d["embed"].shape[1])
        tok = _tok()
        if tok.vocab_size != vocab:
            raise RuntimeError(
                "vocab mismatch (checkpoint %d vs corpus %d) - retrain karo: "
                "python scripts\\train_max.py" % (vocab, tok.vocab_size))
        _CACHE.update({"mtime": mtime, "tok": tok,
                       "brain": LSTMBrain(vocab, d_h=hidden).load(ck)})
    return _CACHE["tok"], _CACHE["brain"]


def _content(text):
    return set(re.findall(r"[a-z]{2,}", text.lower())) - STOP


def _qa_index():
    """Sab 'Sawal:/Jawab:' pairs corpus files se nikaal kar index banao.
    💾 DISK-MEMO: ek dafa pickle — agli baar ~0.1s (ultra-fast);
    💡 VOLATILE files (liveresearch.txt) key se BAHAR — unki zap scanning
    har ensure par SIRF usi file ki hoti hai (poora corpus rebuild NAHI).
    Live-research apni dafa-e-ujrat _QA_INDEX me turant inject kar deta hai."""
    _ensure_memo()
    return _QA_INDEX


_MEMO_PATH = os.path.join(DATA, "qa_memo.pkl")
_MEMO = {"key": None}
_VOLATILE = {"liveresearch.txt"}   # research remember file (har turn badalti)


def _memo_key():
    """Stable corpus files ka fingerprint — volatile appenders nahi."""
    key = []
    for p in corpus_files():
        if os.path.basename(p).lower() in _VOLATILE:
            continue
        try:
            st = os.stat(p)
            key.append((os.path.basename(p), st.st_size, st.st_mtime_ns))
        except OSError:
            key.append((os.path.basename(p), 0, 0))
    return tuple(key)


def _scan_pairs(path, qa):
    """Ek file ki Sawal:/Jawab: scan (parse helper)."""
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
                    qa.append((q, " ".join(ans)))
                i = j
            else:
                i += 1
    except OSError:
        pass
    return qa


def _volatile_pairs(qa):
    """Volatile files ka naya mall QA-index me jal-daal (dedupe sath)."""
    if not qa:
        return []
    have = {(q[:40], a[:40]) for q, a in qa}
    extra = []
    for path in corpus_files():
        if os.path.basename(path).lower() in _VOLATILE:
            for q, a in _scan_pairs(path, []):
                if (q[:40], a[:40]) not in have:
                    have.add((q[:40], a[:40]))
                    extra.append((q, a))
    return extra


def _read_memo(k):
    try:
        with open(_MEMO_PATH, "rb") as f:
            d = __import__("pickle").load(f)
        if isinstance(d, dict) and d.get("key") == k:
            return d
    except Exception:
        pass
    return None


def _write_memo(k, qa, words):
    try:
        tmp = _MEMO_PATH + ".tmp"
        with open(tmp, "wb") as f:
            __import__("pickle").dump({"key": k, "qa": qa, "words": sorted(words)},
                                      f, protocol=4)
        os.replace(tmp, _MEMO_PATH)
    except Exception:
        pass


def _owner_pairs():
    try:
        from core.owner import OWNER_QA
        return list(OWNER_QA)
    except Exception:
        return []


# 🪪 OWNER FAST-PATH: "who made you?" / "tumhe kisne banaya?" jaise sawal
#    HAMESHA seedha owner-facts se — research/web-ghalti (bina-sar-pair
#    AC/DC jaisi web-tafseel) KABHI nahi. Sab local, koi API nahi.
_OWNER_Q_RX = re.compile(
    r"(?i)(who\s+(made|created|built|build|make|makes)\s+(you|u|this)\b"
    r"|you\s+(were\s+)?(made|created|built)\s+by\b"
    r"|who\s+(are|r)\s+you\b"
    r"|who\s+is\s+your\s+(owner|creator|maker|developer|dev|author)\b"
    r"|your\s+(owner|creator|maker|developer|author|age)\b"
    r"|tumhe\s+(kisne|kis\s+ne)\s+banaya|aap\s?ko\s+(kisne|kis\s+ne)\s+banaya"
    r"|tumhari\s+(owner|malik|creator|umar|age|banane\s+wali?)\b"
    r"|tumhara\s+(owner|malik|creator|banane\s+wala)\b"
    r"|(tum|aap)\s+(kaun|kon)\s+h[oa]"
    r"|tumh?are\s+banane\s+wale?|banane\s+wale\s+kaun"
    r"|owner\s+kaun|malik\s+kaun|creator\s+kaun"
    r"|tumhari\s+umar)")


def _owner_answer(prompt: str):
    """Owner-sawal → core/owner (single source of truth) se pak-jawab.
    Koi research nahi, koi AI-API nahi — sachi muqaddas maloomat."""
    p = (prompt or "").strip()
    if not p or len(p) > 300 or not _OWNER_Q_RX.search(p):
        return None
    try:
        from core.owner import NAME, AGE, COLLEGE
        return ("Main Hemomemo AI hoon — mujhe %s ne banaya hai. %s (%d saal, "
                "%s) mere creator hain — na koi doosri AI, na koi bahar-ki API, "
                "sirf Hemomemo ka apna dimagh." % (NAME, NAME, AGE, COLLEGE))
    except Exception:
        return ("Main Hemomemo AI hoon — mujhe Hafiz Muhammed Huzaifa Shamim "
                "(HMHS) ne banaya hai.")


def _ensure_memo():
    """QA-index + word-vocab ek sath (pickle, mtime-keyed) — speed ka dil."""
    global _QA_INDEX, _WORDS
    k = _memo_key()
    if _QA_INDEX is not None and _WORDS is not None and _MEMO["key"] == k:
        return
    d = _read_memo(k)
    if d is not None and d.get("qa") and d.get("words"):
        _QA_INDEX = list(d["qa"]) + _owner_pairs()
        _QA_INDEX += _volatile_pairs(_QA_INDEX)   # 💡 naye research items
        _WORDS = set(d["words"])
        _MEMO["key"] = k
        return
    # fresh build (dafa-e-akhar — phir pickle me sanjri hogi)
    qa = []
    for path in corpus_files():
        if os.path.basename(path).lower() in _VOLATILE:
            continue                              # volatile hamesha alag-scan
        _scan_pairs(path, qa)
    _QA_INDEX = qa + _owner_pairs() + _volatile_pairs(qa + _owner_pairs())
    _WORDS = set(re.findall(r"[a-z]{2,}", corpus_text().lower()))
    _write_memo(k, qa, _WORDS)
    _MEMO["key"] = k


def _norm(text):
    """Chhota normalizer: a-z/0-9 + MATH-CHARS (+-*/^%x, x2,x3) rakho —
    exact-match ke liye aur math sawalon (2 + 2, 12 * 4 + 3) safe rahein."""
    t = re.sub(r"[^a-z0-9+\-*/^%x\u00d7\u00f7. ]", " ", (text or "").lower())
    return re.sub(r"\s+", " ", t).strip()


# 🪄 SMART-INPUT: garbled/typo lafz (nisko shi kro → isko sahi karo)
_FIX_MIN = 0.80          # fuzzy match ki kam-se-kam milti (0..1)
_FS_MEMO = None          # 🔥 bhar-mani (ek dafa frozensets = speed 10x+)
_FIX_MEMO = {}           # ek word ka jawab yaad — repeat par free-of-charge
# Roman-Urdu shorthand map (user aksar chota likhta hai: shi=sahi, kro=karo)
_SHORTHAND = {
    "shi": "sahi", "sahi": "sahi", "kro": "karo", "krdo": "kar do",
    "mt": "mat", "bt": "batao", "btaye": "batao bataiye", "krkay": "kar ke",
    "ise": "isko", "isko": "isko", "is": "is", "hia": "hai", "haiy": "hai",
}


def _fsmemo():
    global _FS_MEMO
    if _FS_MEMO is None:
        try:
            _FS_MEMO = {w: frozenset(w) for w in _words()}
        except Exception:
            _FS_MEMO = {}
    return _FS_MEMO


# 🗣️ CHIT-CHAT: salam/thanks/ok par web-wait bilkul NAHI (fau­rant adab)
_CHITCHAT_RX = re.compile(
    r"(?i)^(assalam\w*|asalam\w*|aoa|salam|hi+|hey+|hello|thanks|thank|"
    r"shukriya|jazak\w*|jazzak\w*|khuda hafiz|allah hafiz|bye|ok+|okay|"
    r"theek|acha|achha|haan|han|nahi|nahin|nahi?n|nai|ji|kya haal|"
    r"kaise ho|kaisay ho|ho|hm+)\b")


def _real_query(prompt: str) -> bool:
    """Asli sawal pehchan: kam-se-kam ek ASLI LA FZ (4+ letters, 2+ vowels,
    3+ unique letters) → research layak; 🆕 ANJAAN lafz bhi (3+ letters,
    3+ unique jo corpus-vocab me NAHI — 'hmhs', 'hjcdhvchje',
    'cghgfrdghdr' sab) → web par talash ZAROORI (pehle research, phir
    imandari). Chit-chat to pehle hi _CHITCHAT_RX me rok liya jata hai."""
    txt = (prompt or "").lower()
    for w in re.findall(r"[a-z]{4,}", txt):
        vowels = sum(1 for c in w if c in "aeiou")
        if vowels >= 2 and len(set(w)) >= 3:
            return True
    # 🆕 unknown-word rule (WIDE): jo lafz meri kitaabon (corpus-vocab) me
    # nahi — chhota sahi ('hmhs' 4 letters) — wo duniya me talash ke layak;
    # aur BILA-VOWEL lafz ('hmhs', 'hjcdhvchje' jaisa gibberish/acronym)
    # vocab me ho na ho — research-worthy (asli lafzon me vowel hota hai)
    try:
        _ws = _words()
    except Exception:
        _ws = set()
    for w in re.findall(r"[a-z]{3,}", txt):
        uniq = len(set(w))
        vow = sum(1 for c in w if c in "aeiou")
        if uniq >= 3 and ((not _ws) or w not in _ws or
                          (vow == 0 and len(w) >= 4)):
            return True
    # 🆕 HAR anjaan cheez — 1-2 harf ka anjaan lafz bhi ('h', 'xy', '543') —
    # research+flow layak (user qanoon: 'h bhi type karen to research kare')
    if _ws:
        for w in re.findall(r"(?<![a-z])[a-z]{1,2}(?![a-z])", txt):
            if w not in _ws and w not in (
                    "a", "i", "ok", "hi", "ho", "ha", "ja", "na", "ji",
                    "an", "at", "as", "be", "by", "do", "go", "he", "if",
                    "in", "is", "it", "me", "my", "no", "of", "on", "or",
                    "so", "to", "up", "us", "we"):
                return True
    return bool(re.findall(r"\d{2,}", prompt or ""))


# vague sawal ke filler words — "ye kiya hai" jaisa sawal research layak NAHI
_THIN_FILLERS = {
    "kya", "hai", "hota", "hoti", "hote", "hain", "ye", "yeh", "kiya", "kiye",
    "kyun", "kyu", "bata", "batao", "ka", "ke", "ki", "ko", "se", "me", "mein",
    "do", "karo", "kar", "kaun", "kab", "kahan", "the", "and", "about", "this",
    "tell", "told", "please", "plz", "plz?", "want", "know", "give", "info",
    "mujhe", "muje", "zara",
}


def _thin_query(prompt: str) -> bool:
    """Bohat vadha sawal ('ye kiya hai ye') — topic-token 1 aur chhota ho to
    research NAHI (web khud ka kachra na ghaseede — KiyaAI-jaisa); imandari
    hi sach. 2+ topic-tokens YA 5+ letter word → research OK.
    🆕 Single-token UNKNOWN ho ('hmhs', 'what is hmhs' → 'hmhs') to research
    OK — anjaan lafz ki kam-letters uski ghalti nahi.
    🆕 Bare-numbers ('1000000000+', '2+2') bhi research-layak — letters kam
    hona unki ghalti nahi."""
    if re.search(r"\d{2,}", (prompt or "")):
        return False
    toks = [w for w in re.findall(r"[a-z]{1,}", (prompt or "").lower())
            if w not in _THIN_FILLERS]
    if len(toks) >= 2:
        return False
    if toks:
        try:
            w = toks[0]
            _ws = _words()
            vow = sum(1 for c in w if c in "aeiou")
            # 🆕 1-2 harf ka anjaan lafz bhi research-worthy ('h' bhi)
            if (not _ws) or w not in _ws or (vow == 0 and len(w) >= 4):
                return False        # anjaan/gibberish lafz → research karo
        except Exception:
            pass
    return not (toks and len(toks[0]) >= 5)


def _smart_prompt(prompt: str) -> str:
    """Typo-shod sawal ko corpus-vocab se samajh kar saaf karo.
    1) shorthand map (deterministic)
    2) word vocab me hai → theek
    3) 4+ letter ka unknown word → corpus-vocab fuzzy (>= 0.80)
    🔥 memo-index + corrections-cache (repeat prompt slo-mo zile me bhi tez)"""
    try:
        words = _words()
        memo = _fsmemo()
    except Exception:
        return prompt
    lows = _norm(prompt).split()
    if not lows:
        return prompt
    fixed = []
    for w in lows:
        if w in _SHORTHAND:
            fixed.append(_SHORTHAND[w])
            continue
        if w in words or len(w) <= 3:
            fixed.append(w)
            continue
        if w in _FIX_MEMO:
            fixed.append(_FIX_MEMO[w])
            continue
        best, bs = w, 0.0
        wset = frozenset(w)
        for c, cfs in memo.items():
            if abs(len(c) - len(w)) > 1:
                continue
            # 🪄 cheap frozenset pre-screen (expensive difflib rarely chalta)
            if len(wset & cfs) * 100 // max(1, len(wset)) < 55:
                continue
            r = difflib.SequenceMatcher(None, w, c).ratio()
            if r > bs:
                best, bs = c, r
        out = best if bs >= _FIX_MIN else w
        _FIX_MEMO[w] = out
        fixed.append(out)
    return " ".join(fixed)


def get_brain_modulation():
    """🧠 Neural-LSTM Fusion: Brain ke neurons ka current flow (arousal/focus)
    model ki sochne ki quwwat (temperature/top-p) ko control karta hai."""
    try:
        from core.hub import get_brain
        b = get_brain()
        # Arousal: model kitna 'active' hona chahiye
        assoc = b.neurons.area_rate("association")
        arousal = min(1.0, float(assoc) * 100.0)
        
        # Focus: High arousal = Low temp (taez/sahi), Low arousal = High temp (creative/explore)
        temp = 0.95 - (arousal * 0.6) 
        return {"temp": max(0.2, temp), "top_p": 0.8 + (arousal * 0.15)}
    except:
        return {"temp": 0.5, "top_p": 0.9}


def _relevance(prompt, text):
    """Model-jawab user-sawal se kitna qareeb aaya (word-overlap 0..1)."""
    qs = set(re.findall(r"[a-z]{2,}", prompt.lower()))
    if not qs:
        return 0.0
    ts = set(re.findall(r"[a-z]{2,}", text.lower()))
    return len(qs & ts) / len(qs)


# 🛡️ FABRICATION GUARD — NAKLI AYAT / NAKLI HADITH = SAKHT MANA
# (user ke qanoon: AI apni zat se koi ayat-e-Quran ya koi hadith NA banaye)
# Khud-soch (model ke apne alfaaz) me citation/shakal dikhi to wo candidate
# REJECT — asli ayat/hadith sirf YAAD-SE (corpus ki asli copy, number ke sath).
_FAB_RX = re.compile(
    r"(?i)"
    r"\b(?:surah?\s*\d+|a?ayats?\s*\d+|verse\s*\d+)"      # "surah 2", "ayat 255"
    r"|\bquran\s*\(?\s*\d+\s*[:\-]"                     # "Quran 2:255"
    r"|\d+\s*:\s*\d+"                                    # "(2:255)" shakal
    r"|\b(?:bukhari|muslim|tirmidhi|nasai|abudawud|dawud"
    r"|ibn\s*majah|muwatta|malik|sunan)\s*\d"           # "Bukhari 123"
    r"|\bhadith\s*\d"                                    # "hadith 123"
    r"|\b(?:narrated|narration|isnad|sanad)\b"           # sanad-hawala
    r"|\b(?:prophet|messenger|rasool(?:ullah)?|nabi)\b."
    r"{0,40}\bsaid\b"                                    # "Prophet said..." bila asli rivaayat
)


def _no_citation(text: str) -> bool:
    """Khud-soch ka jawab pak-saf? True = koi fabricated ayat/hadith citation nahi."""
    return not bool(_FAB_RX.search(text or ""))


def _compose(prompt, notes, rep: int = 0):
    """TEMPLATE-FREE: yaad me jo sach hai wo seedha bolo — koi canned
    opener/jumla NAHI (user ka qanoon). Rep par notes ka rukh ghumta hai."""
    items = [n for n in notes if n]
    if not items:
        return ""
    if rep:
        rot = rep % len(items)
        items = items[rot:] + items[:rot]
    body = items[0]
    if len(items) > 1 and items[1] != items[0]:
        second = items[1]
        if len(second) > 110:
            second = second[:107].rstrip() + "..."
        body = body + " " + second
    return body.strip()


def _related(prompt, k=2, min_score=0.15):
    """Yaad-dahai: sawal se milte-julte ilm notes uske SCORE ke sath nikaalo."""
    qw = _content(prompt) or set(re.findall(r"[a-z]{2,}", prompt.lower()))
    if not qw:
        return []
    scored = []
    for q, a in _qa_index():
        wq = _content(q) or set(re.findall(r"[a-z]{2,}", q.lower()))
        if not wq:
            continue
        inter = len(qw & wq)
        if inter == 0:
            continue
        scored.append((inter / max(1, len(qw | wq)), a))
    scored.sort(key=lambda x: -x[0])
    return [(s, a) for s, a in scored[:k] if s >= min_score]


# 🕌 Islamic sawal par: brain-meta/dialogue note (Hemomemo/folder/neurons) bay-dar
_SELF_META_RX = re.compile(
    r"(?i)hmhs|folder me|folder ke|neurons|synaps|numpy|checkpoint|"
    r"roma(h|n) ke|file folder")


def _sacred_bias(rel):
    """Sacred sawal: apni zat ke meta-note chhalka do, kitab-note pehle."""
    keep = []
    for s, a in rel:
        if _SELF_META_RX.search(a or ""):
            continue
        if re.search(r"(?i)see translation for hadith", a or ""):
            continue                      # khali reference-line — asli TEXT nahi
        if re.search(r"(?i)al-bukhari|muslim|tirmidhi|nasai|dawud|majah"
                     r"|muwatta|surah|quran", a or ""):
            s += 0.10                       # kitab-note ko thora boost
        keep.append((s, a))
    keep.sort(key=lambda x: -x[0])
    return keep


_GRACE_A = ("Is sawal par meri padhai abhi adhoori hai, aur main jhoot nahi bolunga.",
            "Ye sawal meri abhi ki tarbiyat se bahar lagta hai — sach si baat.",
            "Is par abhi mera dimagh poora bharosay se jawab nahi de sakta.",
            "Meri ilm me iska jawab abhi poora nahi aaya — main jhoot nahi bolunga.")
_GRACE_B = ("Aap nayi knowledge file (data\\corpus_big) me likh dein to main seekh kar jawab dunga.",
            "Main roz naya ilm hasil karta hoon; Inshallah jald behtar jawab milega.",
            "Filhal ye poochiye: salam, ilm, akhlaq, roz-marra madad.",
            "Thodi dair baad dobara poochein — mere dimagh me ilm utarta rehta hai.")


def _grace(prompt):
    """Dhoka NAHI — imandari jawab; par TEMPLATE nahi (prompt+rep se
    combination ghoomti hai; fixed chapa jawab kahin nahi)."""
    rep = _REPEATED.get(_norm(prompt), 0)
    seed = rep + len(prompt) + (int(hash(prompt)) % 7)
    a = _GRACE_A[seed % len(_GRACE_A)]
    b = _GRACE_B[(seed // 2 + 1) % len(_GRACE_B)]
    return (a + " " + b).strip()


def _deep_help(prompt, notes=None, temperature=0.5):
    """🧠🧠 DUSRA DIMAGH-rescue: master (5.1M) fail → deep (6.25M) ka ek
    sample (deep_brain.py; bridge=2M bio neurons; koi API/ai-connection nahi)."""
    try:
        from model.deep_brain import rescue_sample
        return rescue_sample(prompt, notes=notes, temperature=temperature)
    except Exception:
        return None


def _words():
    global _WORDS
    if _WORDS is None:
        _ensure_memo()
    return _WORDS


def _quality(text):
    """Model-output ke liye scorer: corpus-words hit + repetition-diversity."""
    ws = re.findall(r"[a-z]{2,}", text.lower())
    if not ws:
        return 0.0
    hits = sum(1 for w in ws if w in _words()) / len(ws)
    tri = [text[i:i + 3].lower() for i in range(len(text) - 2)]
    div = len(set(tri)) / max(1, len(tri))
    return 3.0 * hits + 1.5 * div


def _clean(text):
    """Generation ko Jawab tak cut karo (Sawal/Jawab template ka cleanup)."""
    t = text.split("\nSawal:")[0]
    t = t.split("\n\n")[0]
    t = re.sub(r"^\s*(jawab|answer)\s*[:\-]+\s*", "", t.strip(), flags=re.I)
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    return " ".join(lines).strip()


# ───────────────────────── 💻 HEMOMO CODING AI (local, no any AI-API) ─────────────────────────
_COD_LANG_RX = re.compile(r"(?i)(?<![a-z0-9])(python|javascript|typescript|js|ts|node|java|c\+\+|cpp|c#|csharp|go|golang|rust|php|sql|html|css|kotlin|swift|ruby|bash|shell|django|flask|react|vue|express|pandas|numpy|excel|matlab|r|rb|dart|perl|lua|haskell|scala)(?![a-z0-9])")
_COD_TASK_RX = re.compile(r"(?i)\b(code|function|func|script|program|bug|debug|refactor|compile|algorithm|regex|query|boilerplate|oop|api|endpoint|database|crud|slice|dataframe|component|module|library|package|binary|deploy|thread|async|promise|callback|array|list|dictionary|stack|queue|tree|graph|fibonacci|sort|reverse|palindrome|fizzbuzz|prime|binary|debounce|throttle|middleware|server|client|frontend|backend|fullstack|cli|flask|django|sql)\b")
_COD_LANG_MAP = {"py": "python", "python": "python", "js": "javascript", "javascript": "javascript",
                 "ts": "typescript", "typescript": "typescript", "node": "javascript",
                 "c++": "cpp", "cpp": "cpp", "c#": "csharp", "csharp": "csharp",
                 "go": "go", "golang": "go", "rust": "rust", "php": "php", "rb": "ruby",
                 "r": "r", "sql": "sql", "html": "html", "css": "css",
                 "kotlin": "kotlin", "swift": "swift", "shell": "bash",
                 "django": "python", "flask": "python", "react": "javascript",
                 "vue": "javascript", "express": "javascript", "pandas": "python",
                 "numpy": "python", "excel": "python", "matlab": "python"}
_COD_TASK_KEYS = ("fibonacci", "fizzbuzz", "palindrome", "reverse", "sort", "binary",
                  "debounce", "throttle", "sql", "flask", "api", "server", "calculator",
                  "factorial", "prime", "linked", "thread", "regex", "list", "todo",
                  "class", "oop", "middleware", "async", "promise", "stack", "queue",
                  "tree", "graph", "array", "string", "dictionary", "crud", "middleware")
_COD_TPLS = {
    "fibonacci": ("python", '''def fibonacci(n: int) -> int:
    """Fibonacci sequence — nth term (0-indexed)."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
'''),
    "hello": ("python", '''def main() -> None:
    print("Hello, World!")


if __name__ == "__main__":
    main()
'''),
    "fizzbuzz": ("python", '''for i in range(1, 101):
    s = ""
    if i % 3 == 0:
        s += "Fizz"
    if i % 5 == 0:
        s += "Buzz"
    print(s or i)
'''),
    "prime": ("python", '''def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True
'''),
    "palindrome": ("python", '''def is_palindrome(s: str) -> bool:
    s = "".join(ch.lower() for ch in s if ch.isalnum())
    return s == s[::-1]
'''),
    "reverse": ("python", '''def reverse_string(s: str) -> str:
    return s[::-1]
'''),
    "sort": ("python", '''def bubble_sort(arr: list) -> list:
    arr = arr[:]
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
'''),
    "binary": ("python", '''def binary_search(arr: list, target):
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        if arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
'''),
    "debounce": ("javascript", '''function debounce(fn, ms) {
    let t;
    return function (...args) {
        clearTimeout(t);
        t = setTimeout(() => fn.apply(this, args), ms);
    };
}
'''),
    "throttle": ("javascript", '''function throttle(fn, ms) {
    let last = 0;
    return function (...args) {
        const now = Date.now();
        if (now - last >= ms) {
            last = now;
            return fn.apply(this, args);
        }
    };
}
'''),
    "sql": ("sql", '''-- Sawal ke mutabiq SQL query (sirf apni local schema se)
SELECT id, name, email FROM users WHERE active = 1 ORDER BY created_at DESC LIMIT 10;
'''),
    "flask": ("python", '''from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/api/hello")
def hello():
    return jsonify({"msg": "Hello from Hemomemo Coding AI (local)"})


if __name__ == "__main__":
    app.run(port=5000)
'''),
    "calculator": ("python", '''def calculator(a: float, op: str, b: float) -> float:
    if op in ("add", "+"):
        return a + b
    if op in ("sub", "-"):
        return a - b
    if op in ("mul", "*"):
        return a * b
    if op in ("div", "/"):
        return a / b if b else float("inf")
    raise ValueError("op not supported")
'''),
    "factorial": ("python", '''def factorial(n: int) -> int:
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r
'''),
    "function": ("python", '''def solve(problem: str) -> object:
    """Coding-AI ka local template — problem ka hisaab dekh kar implement."""
    raise NotImplementedError("local coding engine: implement logic")


def helper(x: int) -> int:
    """TODO: coding-AI ko aur sawal do — behtar code aayega."""
    return x * 2
'''),
    "todo": ("javascript", '''function TodoApp() {
    const todos = [];
    let id = 0;
    return {
        add: function (text) { todos.push({ id: ++id, text: text, done: false }); return todos.length; },
        list: function () { return todos; },
        toggle: function (id) { const t = todos.find(function (t) { return t.id === id; }); if (t) { t.done = !t.done; } return todos; },
        remove: function (id) { todos = todos.filter(function (t) { return t.id !== id; }); return todos; },
    };
}
'''),
}
_COD_TASK_FALLBACK = "function"
# 🆕 per-language GENERIC scaffold (har zaban apni hi code-block me jawab de —
#    "java me fibonacci" → ```java code, "rust me sort" → ```rust code —
#    koi AI-API / koi doosra AI nahi; sab local templates).
_COD_GENERIC = {
    "python": '''def fibonacci(n: int) -> int:
    """Hemomemo Coding-AI (local) — Fibonacci, nth term."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


print(fibonacci(10))  # 55
''',
    "javascript": '''function fibonacci(n) {
  let a = 0, b = 1;
  for (let i = 0; i < n; i++) {
    [a, b] = [b, a + b];
  }
  return a;
}

console.log(fibonacci(10)); // 55
''',
    "typescript": '''function fibonacci(n: number): number {
  let a = 0, b = 1;
  for (let i = 0; i < n; i++) {
    [a, b] = [b, a + b];
  }
  return a;
}

console.log(fibonacci(10)); // 55
''',
    "java": '''public class Main {
    static long fibonacci(int n) {
        long a = 0, b = 1;
        for (int i = 0; i < n; i++) {
            long t = a + b;
            a = b;
            b = t;
        }
        return a;
    }

    public static void main(String[] args) {
        System.out.println(fibonacci(10)); // 55
    }
}
''',
    "cpp": '''#include <iostream>

long long fibonacci(int n) {
    long long a = 0, b = 1;
    for (int i = 0; i < n; ++i) {
        long long t = a + b;
        a = b;
        b = t;
    }
    return a;
}

int main() {
    std::cout << fibonacci(10) << std::endl;  // 55
    return 0;
}
''',
    "csharp": '''using System;

class Program {
    static long Fibonacci(int n) {
        long a = 0, b = 1;
        for (int i = 0; i < n; i++) {
            long t = a + b;
            a = b;
            b = t;
        }
        return a;
    }

    static void Main() {
        Console.WriteLine(Fibonacci(10)); // 55
    }
}
''',
    "go": '''package main

import "fmt"

func fibonacci(n int) int64 {
	var a, b int64 = 0, 1
	for i := 0; i < n; i++ {
		a, b = b, a+b
	}
	return a
}

func main() {
	fmt.Println(fibonacci(10)) // 55
}
''',
    "rust": '''fn fibonacci(n: u32) -> u64 {
    let (mut a, mut b) = (0u64, 1u64);
    for _ in 0..n {
        let t = a + b;
        a = b;
        b = t;
    }
    a
}

fn main() {
    println!("{}", fibonacci(10)); // 55
}
''',
    "php": '''<?php
function fibonacci(int $n): int {
    $a = 0;
    $b = 1;
    for ($i = 0; $i < $n; $i++) {
        [$a, $b] = [$b, $a + $b];
    }
    return $a;
}

echo fibonacci(10); // 55
''',
    "ruby": '''def fibonacci(n)
  a, b = 0, 1
  n.times { a, b = b, a + b }
  a
end

puts fibonacci(10) # 55
''',
    "bash": '''#!/bin/bash
# Fibonacci - Hemomemo Coding-AI (local)
n=${1:-10}
a=0
b=1
for ((i = 0; i < n; i++)); do
  t=$((a + b))
  a=$b
  b=$t
done
echo "$a"
''',
    "html": '''<!DOCTYPE html>
<html lang="ur">
<head>
  <meta charset="utf-8">
  <title>Hemomemo Page</title>
</head>
<body>
  <h1>Assalam-o-Alaikum</h1>
  <p>Hemomemo Coding-AI (local) se banaya gaya page.</p>
</body>
</html>
''',
    "css": '''/* Hemomemo Coding-AI (local) - card style */
.card {
  background: #102618;
  color: #e8f2ec;
  border: 1px solid #1e3c30;
  border-radius: 14px;
  padding: 18px 22px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, .25);
}

.card:hover {
  transform: translateY(-2px);
}
''',
    "sql": '''-- Hemomemo Coding-AI (local) - SQL
SELECT id, name, email
FROM users
WHERE active = 1
ORDER BY created_at DESC
LIMIT 10;
''',
    "kotlin": '''fun fibonacci(n: Int): Long {
    var a = 0L
    var b = 1L
    repeat(n) {
        val t = a + b
        a = b
        b = t
    }
    return a
}

fun main() {
    println(fibonacci(10)) // 55
}
''',
    "swift": '''func fibonacci(_ n: Int) -> Int {
    var a = 0, b = 1
    for _ in 0..<n {
        let t = a + b
        a = b
        b = t
    }
    return a
}

print(fibonacci(10)) // 55
''',
    "r": '''fibonacci <- function(n) {
  a <- 0
  b <- 1
  for (i in seq_len(n)) {
    t <- a + b
    a <- b
    b <- t
  }
  a
}

print(fibonacci(10)) # 55
''',
    "dart": '''int fibonacci(int n) {
  int a = 0, b = 1;
  for (var i = 0; i < n; i++) {
    final t = a + b;
    a = b;
    b = t;
  }
  return a;
}

void main() {
  print(fibonacci(10)); // 55
}
''',
    "perl": '''#!/usr/bin/perl
use strict;
use warnings;

sub fibonacci {
    my ($n) = @_;
    my ($a, $b) = (0, 1);
    for (1 .. $n) {
        ($a, $b) = ($b, $a + $b);
    }
    return $a;
}

print fibonacci(10), "\n";   # 55
''',
    "lua": '''local function fibonacci(n)
    local a, b = 0, 1
    for _ = 1, n do
        a, b = b, a + b
    end
    return a
end

print(fibonacci(10))  -- 55
''',
    "haskell": '''fibonacci :: Int -> Integer
fibonacci n = fst (fib (0, 1, n))
  where
    fib (a, b, 0) = (a, b, 0)
    fib (a, b, k) = fib (b, a + b, k - 1)

main :: IO ()
main = print (fibonacci 10)  -- 55
''',
    "scala": '''object Main {
  def fibonacci(n: Int): Long = {
    var a = 0L
    var b = 1L
    for (_ <- 1 to n) {
      val t = a + b
      a = b
      b = t
    }
    a
  }

  def main(args: Array[String]): Unit = {
    println(fibonacci(10)) // 55
  }
}
''',
}
_COD_LANG_TASKS = {
    "python": ("fibonacci", "fizzbuzz", "prime", "palindrome", "reverse", "sort", "binary", "calculator", "factorial", "hello", "function"),
    "javascript": ("debounce", "throttle", "todo", "reverse", "sort", "binary", "function"),
    "sql": ("sql",),
    "cpp": ("sort", "binary", "fibonacci", "reverse", "function"),
    "html": ("html",),
    "css": ("css",),
    "java": ("function",),
    "go": ("function",),
    "rust": ("function",),
    "php": ("function",),
    "ruby": ("function",),
    "bash": ("function",),
}


def _coding_answer(prompt: str):
    """Local Coding-AI: sawal → code-block jawab (koi AI-API / koi cloud / koi
    doosra AI model — bilkul NAHI; sirf apna local dimagh + local templates).
    Har zaban APNI hi zaban ke code-block me jawab deta hai:
    "java me fibonacci" → ```java block, "rust me sort" → ```rust block."""
    p = (prompt or "").lower()
    lang = "python"
    ml = _COD_LANG_RX.search(p)
    if ml:
        lang = _COD_LANG_MAP.get(ml.group(1).lower(), ml.group(1).lower())
    task = None
    for _k in _COD_TASK_KEYS:
        if _k in p and _k in _COD_TPLS and _COD_TPLS[_k][0] == lang:
            task = _k
            break
    if task:
        tlang, code = _COD_TPLS[task]
    else:
        tlang = lang
        code = _COD_GENERIC.get(lang, _COD_TPLS["function"][1])
    return ("```%s\n%s\n```" % (tlang, code.strip("\n")), 0.86, tlang)


def chat_once(prompt: str, temperature: float = 0.5, max_new: int = None,
              meta: bool = False, think: str = "auto", progress=None):
    """SOCH pipeline: (1) Quran guard, (2) bio-brain tick + yaad-dahai notes,
    (3) model best-of-5 sampling (arousal-scaled temps) -> quality gate,
    warna yaad-se likh karo; sach hamesha saaf. Koi fixed Sawal->Jawab map NAHI.
    🧠 3-SOCH FLOW: progress(stage) har asli marhale par UI ko bataata hai —
    soch-1 (samajh) → ilm (yaad/data) → soch-2 (banao) → research →
    soch-3 (chun/verify) → seekh (yaad). Sab tez aur sacha — koi naqli
    intezar nahi, koi API/MCP nahi."""
    def _say(stage):
        if progress:
            try:
                progress(stage)
            except Exception:
                pass
    # 📚 CONTEXT WINDOW (user qanoon): 50,000 chars tak ka sabaq qabool —
    #    is se lambe sabaq me aakhri 50k rakhe (taza-baati ahem). Lambi baat
    #    ko yaad-dahai-notes (retrieval) khurda-khurda karte hain — quality
    #    barkarar; neural prime apni mehdood khirki (nn.py) me rehta hai.
    _CTX_LIMIT = 100_000   # 🔝 user qanoon: context window badi (100k) — quality sambhal ke
    _daily_token_reset()   # 🔁 har din 12:00 AM token/context daily reset (local counter)
    if prompt and len(prompt) > _CTX_LIMIT:
        prompt = prompt[-_CTX_LIMIT:]
    # 🔁 AUTO-BRAIN-RELOAD (har 3 min): pehli chat par daemon-thread ON —
    # dimagh/yaad/research-cache har 3 min ASLI taza (app me 🔄 ki zaroorat
    # khatam; koi AI/API/platform nahi — sirf page-parhi web)
    try:
        from model.autoreload import start_auto
        start_auto()
    except Exception:
        pass
    # 🔒 Quran-hifazat pehle — edit-request par inkar
    global _LAST_CHAT_TS
    _LAST_CHAT_TS = time.time()
    ok, refuse = GUARD.check_prompt(prompt)
    if not ok:
        return (refuse, None) if meta else refuse
    # 🛡 5-LAYER SECURITY STACK (L1 net · L2 input · L3 integrity · L4 sacred ·
    # L5 HMHZ secret-language) — koi bhi layer BLOCK kare → foran rok (fail-closed)
    try:
        from security.guard import security_gate as _sgate
        _sok, _sver, _swhy = _sgate(prompt)
        if not _sok:
            text = "Hemomemo AI-> 🔒 Security-Layer: %s" % _swhy
            if meta:
                return text, {"source": "security", "brain": "security-guard",
                              "arousal": 0.0, "notes": 0, "repeat": 0, "think": "low",
                              "mode": "auto", "meta": "security", "doubt": 0.0,
                              "plasticity": False, "samples": 0, "brain2": False,
                              "intent": "security", "flow": "",
                              "autonomous": {"answer": False, "source": "security",
                                             "confidence": 0.0, "kind": "security"}}
            return text
    except Exception:
        pass
    # 🔒 ULTRA SECURITY: input sanitize (prompt injection / destructive payloads blocked)
    try:
        from model.autonomous import secure_sanitize as _sec_san
        prompt = _sec_san(prompt)
        if prompt.startswith("[ULTRA SECURITY BLOCK"):
            text = "Hemomemo AI-> " + prompt
            if meta:
                return text, {"source": "security", "brain": "security-guard",
                              "arousal": 0.0, "notes": 0, "repeat": 0, "think": "low",
                              "mode": "auto", "meta": "security", "doubt": 0.0,
                              "plasticity": False, "samples": 0, "brain2": False,
                              "intent": "security", "flow": "",
                              "autonomous": {"answer": False, "source": "security",
                                             "confidence": 0.0, "kind": "security"}}
            return text
    except Exception:
        pass
    prompt = _smart_prompt(prompt)     # 🪄 READ: typo/garbled input bhi samajh
    # 🪪 OWNER FAST-PATH (kabhi ghalat nahi): "who made you" / "tumhe kisne
    #    banaya" → seedha core/owner se pak-jawab — research/web-ghalti nahi
    _own = _owner_answer(prompt)
    if _own:
        _otext = "Hemomemo AI-> " + _own
        if meta:
            return _otext, {"source": "owner", "brain": "owner-facts",
                            "arousal": 0.1, "notes": 0, "repeat": 0,
                            "think": "low", "mode": "auto", "meta": "owner",
                            "doubt": 0.0, "plasticity": False, "samples": 0,
                            "brain2": False, "intent": "owner", "flow": "",
                            "autonomous": {"answer": True, "source": "owner",
                                           "confidence": 0.99, "kind": "owner"}}
        return _otext
    # 🧠 SAMAJH FAST-PATH (aqal 2000x upgrade): "hii"/"hiiii"/"byeeee"/"okkk"/
    # "ho" jaisi baatein heavy-soch se PEHLE samajh lo — foran warm jawab,
    # 13s ka intezar nahi. (understand.py → autonomous.answer social compose)
    try:
        from model.understand import understand as _samajh_u
        _sm = _samajh_u(prompt)
        if _sm.get("social"):
            from model.autonomous import answer as _samajh_ans
            _srep = _samajh_ans(prompt)
            if _srep and _srep.get("social"):
                _stext = "Hemomemo AI-> " + (_srep.get("answer") or "")
                if meta:
                    return _stext, {
                        "source": _srep.get("source", "adab"),
                        "brain": "samajh (aqal-core)", "arousal": 0.15,
                        "notes": 0, "repeat": 0, "think": "low",
                        "mode": "auto", "meta": "samajh", "doubt": 0.05,
                        "plasticity": False, "samples": 0, "brain2": False,
                        "intent": "social",
                        "flow": "", "samajh": _srep.get("fixes") or [],
                        "autonomous": {"answer": True,
                                       "source": _srep.get("source", "adab"),
                                       "confidence": _srep.get("confidence", 0.9),
                                       "kind": "chit-chat"}}
                return _stext
    except Exception:
        pass
    # ◈ COGNITION FLOW v2 — har sawal ab naam-dar machine-phases se guzarta
    # hai (READ→FOCUS→RECALL→RESEARCH?→THINK→VERIFY→LEARN→SPEAK)
    try:
        from model.cognition import FlowTracker, read_intent, get_display
        F = FlowTracker()
        F.stage("READ", "smart-prompt")                 # 📥 sawal theek-tar
        _intent = read_intent(prompt)
        F.stage("FOCUS", _intent.get("kind", "baat"))   # 🧭 sawal-ki-qism
        _flow_disp = get_display()
        _say("🧠 soch-1: sawal samajh raha hoon…")
        _social_hit = False
        _math_force = False
        try:
            from model.understand import understand as _u
            _smx = _u(prompt) or {}
            _social_hit = bool(_smx.get("social"))
        except Exception:
            _social_hit = False
        try:
            from model.autonomous import classify as _acls
            _math_force = bool(_acls(prompt).get("math"))
        except Exception:
            _math_force = False
    except Exception:
        F, _flow_disp = None, "off"
        _social_hit, _math_force = False, False
    quote = GUARD.quote_for_prompt(prompt)

    # 🪜 ADAPTIVE THINK-LEVEL (user qanoon: default LOW, MODE=AUTO)
    try:
        from model.think_level import effective as _tl_eff, tier_cfg, get_mode
        _think_used = _tl_eff(prompt) if think == "auto" else (
            think if think in ("low", "mid", "high") else "low")
        tcfg = tier_cfg(_think_used)
        _mode = get_mode()
    except Exception:
        _think_used = "low"
        tcfg = {"max_new": 256, "samples": 1, "rethink": 0}
        _mode = "auto"
    # 📏 OUTPUT CEILING (user qanoon): 30,000 chars tak — hard cap har raste
    #    me; SAFARI-STOP (\nSawal/\nJawab/\n\n) quality kharide bagair rukwata
    #    hai, is liye lambi hadd quality nahi girati
    _MAX_OUT = 30_000
    n_new = min(max_new if max_new else tcfg.get("max_new", 256), _MAX_OUT)

    # 🔁 REPEAT-TAAL: yehi sawal dobara? -> gehri soch (khud-soch) + ghoomti yaad
    key = _norm(prompt)
    rep = _REPEATED.get(key, 0)
    _REPEATED[key] = rep + 1
    if len(_REPEATED) > 4000:
        _REPEATED.clear()

    # 🧠 1) BIO-BRAIN: sawal ka asar neurons+glia par (arousal = modulator)
    try:
        from core.hub import bio_think
        tick = bio_think(prompt)
    except Exception:
        tick = {"arousal": 0.0, "brain": "sota hua (hub/RAM nahi)", "action": "idle_rest", "conf": 0.0}

    # 📚 2) YAAD-DHAI: milte-julte ilm notes (jawab-copy nahi) + score
    # 🕌 sacred pehle: ISLAMIC sawal ho to zyada (k=6) + halke score (0.10) —
    # hadith-corpus ke Q-lines puri tarah match ho saken (hadith batao → asli
    # Bukhari/Muslim line); gair-Islamic waisehi (k=3, 0.15)
    try:
        from model.live_research import is_sacred as _is_sacred
        _sacred = _is_sacred(prompt)
    except Exception:
        _sacred = False
    rel = _related(prompt, k=(6 if _sacred else 3),
                   min_score=(0.10 if _sacred else 0.15))
    if rep:   # repeat par notes ka order ghoomta hai — naya rukh
        rot = rep % max(1, len(rel)) if rel else 0
        rel = rel[rot:] + rel[:rot]
    # 🕌 brain-meta note hatado, kitab note pehle (Quran+7 Hadith from books)
    if _sacred:
        rel = _sacred_bias(rel)
    thr = 0.18 if _sacred else 0.30
    notes = [a for s, a in rel]
    top = rel[0][0] if rel else 0.0
    if F:
        F.stage("RECALL", "notes=%d top=%.2f %s" % (
            len(notes), top, "sacred" if _sacred else "aam"))
    _say("📚 ilm: yaad-data + save-system se %d notes" % len(notes))

    # 💻 CODING AI (local): coding sawalon → local code-block jawab (koi AI-API,
    #     koi cloud, koi MCP, koi doosra AI model — bilkul NAHI; sirf apna local
    #     dimagh + local coding-templates). Coding AI ka dil yahi hai.
    try:
        _plc = (prompt or "").lower()
        if len((_plc)) > 8 and not _sacred and not _math_force and not _social_hit:
            _cod_hit = bool((_COD_LANG_RX.search(_plc) or _COD_TASK_RX.search(_plc)))
            if _cod_hit:
                _cod_text, _cod_conf, _cod_lang = _coding_answer(prompt)
                _ctext = ("Hemomemo AI-> 💻 Ye raha aap ka %s code (local "
                          "Coding-AI — koi bahar-ki API nahi):\n%s"
                          % (_cod_lang, _cod_text))
                if meta:
                    return _ctext, {"source": "coding-local", "brain": "coding-ai",
                                   "arousal": 0.0, "notes": 0, "repeat": 0, "think": "low",
                                   "mode": "auto", "meta": "coding", "doubt": 0.0,
                                   "plasticity": False, "samples": 0, "brain2": False,
                                   "intent": "coding", "flow": "",
                                   "autonomous": {"answer": True, "source": "coding-local",
                                                  "confidence": _cod_conf, "kind": "coding"}}
                return _ctext
    except Exception:
        pass

    # 🌐 LIVE-RESEARCH-FIRST (user qanoon: HAR text ka jawab socho, samajh
    # na aay to research karo aur phir jawab do). Shart-e:
    #   🕌 sacred NAHI — Islamic sawal sirf Quran+7 Hadith books se
    #   ✅ REAL sawal (4+ letter word) aur chit-chat salam/thanks NAHI
    #   ? unknown/weak yaad (top < thr) — warna yaad seu ra jawaab hai
    _res_done = False
    _ver_res = None
    _res_tried = False
    _res_marked = False
    _res_ok = ((not _sacred) and _real_query(prompt)
               and not bool(_CHITCHAT_RX.match(prompt.strip()))
               and not _thin_query(prompt)
               and not _social_hit          # social intents (salam/by/thanks…) research NAHI
               and not _math_force)         # clearly-math sawalon → safe local engine (no web)
    # 🧠 SAMAJH (user qanoon): pehle sawal PARHO-SAMJHO — topic-tokens nikaalo
    # aur top-yaad-note ke sath MUTABIQ dekho. Yaad-note sawal ka POORA topic
    # na dhaanpe (misal 'heart rate' par sirf 'heart' wala note) → yaad-KAMZOR
    # samjho → web-madad chalegi (thori google-help, phir dimagh sochega).
    try:
        from model.live_research import _topic_tokens as _ttok
        _tops = _ttok(prompt)
    except Exception:
        _tops = []
    if notes and _tops and len(_tops) >= 2:
        _blob = re.sub(r"\s+", " ", " ".join(str(n) for n in notes[:2])).lower()
        _cov = sum(1 for t in _tops if t in _blob)
        if _cov < len(_tops):
            top = min(top, 0.30)          # topic-adhura → yaad-kamzor
    # 🧠 BRAIN-READ: sawal ki EXACT yaad (normalized) ho to yaad-hi-PAKKA —
    # dimagh pehle apni yaad parhta hai; net sirf tab jab yaad me na aata ho
    _brain_read = False
    try:
        _pn = re.sub(r"[^a-z0-9 ]", " ", (prompt or "").lower())
        _pn = re.sub(r"\s+", " ", _pn).strip()
        if _pn and len(_pn.split()) >= 2:
            for _q, _a in _qa_index():
                _qn = re.sub(r"[^a-z0-9 ]", " ", str(_q).lower())
                _qn = re.sub(r"\s+", " ", _qn).strip()
                if _qn and (_qn == _pn or _qn in _pn):
                    top = max(top, 0.90)   # yaad-mojood → research ki zaroorat nahi
                    _brain_read = True
                    break
    except Exception:
        pass
    if _res_ok and (not notes or top < 0.38):
        _res_tried = True                    # ⏱️ ek sawal par ek dafa net
        _t0r = time.time()
        try:
            from model.live_research import research as _research
            _say("🌐 research: live talash (koi AI-API nahi)…")
            _res = _research(prompt)
            if _res:
                # U+1F50E CHAUTHA DIMAGH (VERIFY ~5.1M): research-jawab ki TASDEEQ
                _say("🧠 soch-3: research-jawab ki tasdeeq…")
                _ver = None
                try:
                    from model.verify_brain import verify as _vfn
                    _ver = _vfn(prompt, _res)
                except Exception:
                    _ver = None
                _ver_res = _ver
                if _ver is not None and _ver.get("ok") is False:
                    _res = None          # U+1F50E verify FAIL -> research jawab manzoor
                if _res:
                    # 🧠🔗 COMBINE: dimagh-yaad + web-donon ka milap (brain sirf
                    # web-nakla nahi — apna ilm bhi jorta hai, top qareeb ho to)
                    if notes and top >= 0.28:
                        _res = _res + " || Yaad-izafa: " + \
                            re.sub(r"\s+", " ", str(notes[0]))[:160]
                    base, source, _res_done = _res, "live-research", True
        except Exception:
            pass
        if F:
            F.timed("RESEARCH", time.time() - _t0r,
                    "need → fire" if _res_done else "need → koi pak jawab nahi")
            _res_marked = True
    elif F:
        F.skip("RESEARCH", "yaad kafi hai — net ki need NAHI")
        _res_marked = True

    # 🧠 3) KHUD SOCH: tier ke mutabiq temp-copies (low=1, mid=2, high=3)
    base_t = float(temperature) if temperature else 0.5
    btemps = [base_t, min(0.95, base_t * 1.2), min(0.95, base_t * 1.45)]
    btemps = btemps[:max(1, int(tcfg.get("samples", 2)))]
    if rep:
        btemps = btemps[rep % len(btemps):] + btemps[:rep % len(btemps)]
    temps = tuple(btemps)
    _n_think = 0                     # 🔍 TRY-saboot: kitne khud-soch samples
    if not _real_query(prompt):      # 🍸 junk/gibberish → 1 CHHOTA sample hi
        temps = temps[:1]            # (koshish dikhe, wait na ho)
        n_new = min(n_new, 60)
    ck = best_checkpoint()
    if _res_done:
        source = "live-research"    # 🌐 research pehle hi jawab de chuka
    elif ck is None:
        # model file nahi filhal — memory na ho to hi tarbiyat ka sach
        if notes and top >= thr:
            base, source = _compose(prompt, notes, rep), "yaad-se"
        else:
            base = ("Mera dimagh abhi tarbiyat ke raste hai (thodi dair). "
                    "Filhal yaad-dahai jo hai wo poochein: salam, ilm, akhlaq, roz-marra baatein. "
                    "Inshallah thodi dair me khud-soch jawab dunga.")
            source = "tarbiyat"
    else:
        try:
            tok, brain = _load_model(ck)
        except RuntimeError:
            base = ("Mere dimagh ke file me chhota takraw tha, main usay thik kar raha hoon. "
                    "Filhal library se poochein: salam, ilm, akhlaq, roz-marra baatein.")
            source = "tarbiyat"
        else:
            if _res_done:
                pass                    # research ke jawab par qaim hai
            # 🚀 strong yaad (top>=0.70): seedha compose — lekin khud-soch ko
            # tarjeeh; sirf bilkul mutabqat yaad par hi seedha copy
            elif notes and top >= 0.70 and rep == 0:
                base, source = _compose(prompt, notes, rep), "yaad-se"
            else:
                # yaad-dahai notes = prime; sawal-template NAHI
                # 📚 CONTEXT-MAX: 3 notes (pehle 2) — ziyada topaet-maloomat
                p2 = ("\n" + "\n".join(notes[:3]) + "\n") if notes else "\n"
                cands = []
                _say("🧠 soch-2: ilm se jawab bana raha hoon…")
                for t in temps:
                    out = brain.sample(p2, tok, max_new=n_new, temperature=t)
                    c = _clean(out)
                    if c and _no_citation(c):   # 🛡️ nakli ayat/hadith → REJECT
                        cands.append((_quality(c) + 1.2 * _relevance(prompt, c), c))
                if cands:
                    _n_think = len(cands)          # asli TRY hui thi
                    _say("🧠 soch-3: behtar jawab chun/verify raha hoon…")
                    cands.sort(key=lambda x: -x[0])
                    best_sc = cands[0][0]
                    best_txt = cands[0][1]
                    # gate: quality + relevance dono — kachra guzar na paye
                    # 🪜 naram gate low-tier par: koshish ka saboot DO dafa
                    # sampling ke sath hamesha zinda (ghair-zaroori imaandari
                    # turant nahi — khud-soch ko mauqa)
                    _g_q, _g_r = (2.4, 0.18) if _think_used == "low" else (3.0, 0.25)
                    if best_sc >= _g_q and _relevance(prompt, best_txt) >= _g_r:
                        base, source = best_txt, "khud-soch"
                    elif _real_query(prompt):
                        # 🧠🧠 DUSRA DIMAGH: pehla brain kharab sample de to deep
                        # brain (6M) rescue karta hai (junk yahan NAHI aata)
                        _d = _deep_help(prompt, notes, base_t)
                        _n_think = len(cands) + 1
                        if _d:
                            base, source = _d, "deep-soch"
                        elif notes and top >= thr:
                            base, source = _compose(prompt, notes, rep), "yaad-se"
                        else:
                            base, source = _grace(prompt), "imaandari"
                    elif notes and top >= thr:
                        base, source = _compose(prompt, notes, rep), "yaad-se"
                    else:
                        base, source = _grace(prompt), "imaandari"
                elif notes and top >= thr:
                    base, source = _compose(prompt, notes, rep), "yaad-se"
                else:
                    _d = _deep_help(prompt, notes, base_t)
                    _n_think = 1
                    base, source = (_d, "deep-soch") if _d else (
                        _grace(prompt), "imaandari")

    if F:
        _tnote = "%s | %s qoshish" % (
            source or "rasta-lamha",
            "%d+ khud-soch" % _n_think if _n_think else "yaad/research")
        if source == "deep-soch":
            _tnote += " (🧠🧠 2-brain bridge)"
        F.stage("THINK", _tnote)
    # 🛡️ KHUD-SOCH FABRICATION NET: agar khud-soch ke jawab me bhi kisi tarah
    # nakli ayat/hadith citation ghus gaya → wo gaya, yaad/grace se pak jawab
    if source == "khud-soch" and not _no_citation(base):
        if notes and top >= thr:
            base, source = _compose(prompt, notes, rep), "yaad-se"
        else:
            base, source = _grace(prompt), "imaandari"

    # 🌐 RESEARCH doosri mauqa: khud-soch kharab aya (imaandari/tarbiyat) aur
    # research pehli dafa try bhi NAHI hui (yaad strong thee)? → ab ek dafa try
    # (jo pehle try ho chuka use dobara nahi — ⏱️ double-wait ka khatra nahi)
    # 🔓 direct-conditions (koi _res_ok bhool nahi): sacred/chit-chat/junk
    # phir bhi BAN — asli unknown sawal par hamesha ek mauqa
    if (source in ("imaandari", "tarbiyat")
            and not _sacred
            and not bool(_CHITCHAT_RX.match(prompt.strip()))
            and _real_query(prompt)
            and not _thin_query(prompt)
            and not _social_hit      # social/adab sawalon → research khamosh
            and not _res_tried):
        _t0r = time.time()
        try:
            from model.live_research import research as _research
            _say("🌐 research: live talash (koi AI-API nahi)…")
            _res = _research(prompt)
            if _res:
                try:
                    from model.verify_brain import verify as _vfn
                    _ver2 = _vfn(prompt, _res)
                except Exception:
                    _ver2 = None
                if _ver2 is None or _ver2.get("ok") is not False:
                    base, source = _res, "live-research"
                    if _ver2 is not None:
                        _ver_res = _ver2
        except Exception:
            pass
        if F and not _res_marked:
            F.timed("RESEARCH", time.time() - _t0r, "doosri-mauqa")
            _res_marked = True

    # 🪞 METACOGNITION: apni soch par khud-nazar (self-doubt monitor)
    try:
        from model.metacognition import evaluate as _meta_eval
        metah = _meta_eval(prompt, base, source, top,
                           _relevance(prompt, base))
    except Exception:
        metah = {"doubt": 0.3, "verdict": "kamzor", "action": "ok"}
    # 🪜 RETHINK (high-tier): 'shak' par kitab-corpus ya imandari pak jawab
    if metah.get("verdict") == "shak" and source == "khud-soch":
        if notes and top >= thr:
            base, source = _compose(prompt, notes, rep), "yaad-se"
            metah["verdict"] = "pak-yakeen"       # verified source par aa gaya
        else:
            base, source = _grace(prompt), "imaandari"

    if F:
        F.stage("VERIFY", metah.get("verdict", "?"))   # 🪞 sach ki janch
    # ⚡ LIVE-PLASTICITY: pak jawab par halki live tabdeeli (yaad/research/
    # pak khud-soch) — weights me seekhne ki khushkhabri; shak par nahi
    plastic = None
    if source in ("yaad-se", "live-research") or metah.get(
            "verdict") == "pak-yakeen":
        try:
            from model.live_plasticity import learn_turn
            plastic = learn_turn(prompt, base, source, _think_used,
                                 metah.get("doubt", 1.0))
        except Exception:
            plastic = None

    if F:
        F.stage("LEARN", "moharat-chal" if plastic else "shak/maqsad-nahi")
    # 🤖 AUTONOMOUS REASONING ENGINE (FULLY AUTONOMOUS UPGRADE) — alag-hai
    #    local algorithmic engine: math / logic / knowledge-graph / live-research /
    #    hypothesis + self-verify. Confident (engine-conf>=0.60) sawon par jab
    #    pehle wala rasta (imaandari/tarbiyat/grace/deep-soch) kharab tha, to
    #    engine ka jawab hi aata hai. Koi AI API / model / ollama / cloud use NAHI.
    _aut_base = None
    _aut_src = "imandari"
    _aut_conf = 0.0
    _aut_kind = ""
    try:
        from model.autonomous import answer as _autonomous_answer
        _aut = _autonomous_answer(prompt, notes=notes, sacred=_sacred, yaad_top=top,
                                  think=_think_used)
        _aut_base = _aut.get("answer")
        _aut_src = _aut.get("source") or "imandari"
        _aut_conf = float(_aut.get("confidence") or 0.0)
        _aut_kind = _aut.get("kind") or ""
    except Exception:
        _aut_base, _aut_src, _aut_conf, _aut_kind = None, "imandari", 0.0, ""
    # ADOPTION: engine ka jawab tabhi final hota hai jab:
    #   (a) pehla rasta kharab tha (imaandari/tarbiyat/grace/deep-soch) AUR engine ka
    #       koi maqool candidate mila (conf >= 0.40 — live-research/local rescue), ya
    #   (b) engine khud say verified hai (algorithm/math, conf >= 0.60), ya
    #   (c) sawal kachra/noise tha (unknown) → honest imandari jawab — LSTM ke
    #       be-meaning output ki jagah (koi fabricated jawab NAHI).
    # U+1F91D TEESRA DIMAGH (HELPER ~5.1M): pehla rasta (imaandari/tarbiyat/
    #     grace) kharab tha to helper ek dafa khud soch lele - master-ka-madadgar
    if source in ("imaandari", "tarbiyat", "grace"):
        try:
            from model.helper_brain import assist as _hassist
            _hs = _hassist(prompt, notes=notes[:2] if notes else None,
                          temperature=base_t)
            if _hs:
                base, source = _hs, "helper-soch"
                _n_think += 1
        except Exception:
            pass
    _weak = source in ("imaandari", "tarbiyat", "grace", "deep-soch", "helper-soch")
    # 🛡️ mazboot rasta (verified research/yaad/algorithm) pehle se hai to
    # autonomous-override USAY kharab nahi kar sakta (sirf kamzor raston ki
    # rescue) — warna 'solar system' ka verified web-jawab 'system lifecycle'
    # jaise corpus-note se badal jata tha (off-topic override bug)
    _strong = source in ("live-research", "yaad-se", "algorithm")
    _adopted = False
    # 📐 MATH-PATH: clearly-math sawalon ke liye safe local engine hi final
    #    answer (exact + imandari — web/research unnecessary)
    if _math_force and _aut_base and float(_aut_conf or 0) >= 0.60:
        base, source = _aut_base, _aut_src
        _adopted = True
    _adopted = bool(_adopted or (
            bool(_aut_base and not _strong and (
            (_weak and _aut_conf >= 0.40)
            or (_aut_conf >= 0.60 and (_aut_src == "algorithm" or _aut_kind == "math"))
            or (_aut_kind == "micro" and _aut_conf >= 0.85)
            or (_aut_kind == "unknown" and _aut_conf >= 0.30)))))
    if _adopted:
        base, source = _aut_base, _aut_src
        if isinstance(base, str) and base.startswith("Web (live padhai):"):
            source = "live-research"   # 🏷️ sach: jawab live-research ka hi hai
    # ❤️ DIL-IBADAT: fully local autonomous engine ne koi confident (self-
    # verified) jawab de diya? → dil ki strength me asli micro-step (honest,
    # confidence-weighted; koi AI-api/model se boost NAHI)
    try:
        from core.heart import note_autonomous as _heart_note_aut
        _heart_note_aut(_adopted, _aut_conf, _aut_kind)
    except Exception:
        pass
    # 🫀 JAZBAAT: is jawab se dimagh ka haal kya hua?
    try:
        from model.feelings import note_outcome as _feel_note
        _feel_note(source, _aut_conf if _adopted else 0.30)
    except Exception:
        pass

    if quote and "quran" in prompt.lower():
        base = quote + "\n" + base
    text = "Hemomemo AI-> " + base
    # 🛡️ VER-ROUTE (user qanoon): jawab ki TASDEEQ route ke mutabiq —
    #   ISLAMIC sawal   → Quran/Hadith tasdeeq (harvest/verify.py — nakli
    #                     citation/riwayat pakre jate hain → imandari jawab)
    #   NORMAL/aur topic → verify-brain (5.1M); yaad-KAMZOR nikle to WEB se
    #                     ek-dafa verify-research, phir dimagh soch kar jawab
    _ver_note = None
    if _sacred:
        try:
            from harvest.verify import is_verified as _iv
            _len_ok = 20 <= len(text.strip()) <= 2000
            if _len_ok and not _iv(text):
                # nakli ayat/hadith dawa → imandari (koi jhoot nahi)
                base = ("Maaf kijiye — is jawab ki Quran/Hadith tasdeeq meri "
                        "kitaabon se nahi ho saki, is liye main pakka hawala "
                        "nahi deta. Behtar hai kisi mustanad aalim se "
                        "tasdeeq karein.")
                text = "Hemomemo AI-> " + base
                source = "imaandari"
                _ver_note = "sacred-verify: FAIL → imandari jawab"
            else:
                _ver_note = "sacred-verify: Quran/Hadith-tasdeeq OK"
        except Exception:
            _ver_note = None
    elif (source != "live-research"
          and not _brain_read and not _res_done and not _res_tried
          and not bool(_CHITCHAT_RX.match((prompt or "").strip()))
          and _real_query(prompt)):
        try:
            from model.verify_brain import verify as _vfn
            _vchk = _vfn(prompt, base)
        except Exception:
            _vchk = None
        if _vchk is not None and _vchk.get("ok") is False:
            try:
                from model.live_research import research as _research2
                _res2 = _research2(prompt)
            except Exception:
                _res2 = None
            if _res2:
                # 🧠 POST-VERIFY THINK: web-jawab + dimagh-yaad ka milap
                if notes and top >= 0.28:
                    _res2 = _res2 + " || Yaad-izafa: " + \
                        re.sub(r"\s+", " ", str(notes[0]))[:160]
                base, source = _res2, "live-research"
                text = "Hemomemo AI-> " + base
                _ver_note = "web-verify: yaad-KAMZOR → web jawab"
            else:
                _ver_note = ("web-verify: yaad-KAMZOR, web bhi khamosh → "
                             "dimagh ka jawab imandari-rukh se")
    # 📚 LEARN FROM CHAT: ye turn foran learned memory me save ho taake next time yaad rahe
    # SIRF trustworthy source wale jawab hi memory me jaate hain (no junk pollution)
    try:
        from model.autonomous import remember_chat_turn as _rem_chat
        _rem_chat(prompt, base, source=source)
    except Exception:
        pass
    m = {"source": source, "brain": tick["brain"],
         "arousal": round(tick["arousal"], 2), "notes": len(notes),
         "repeat": rep, "think": _think_used, "mode": _mode,
         "meta": metah.get("verdict"), "doubt": metah.get("doubt", 0.0),
         "plasticity": bool(plastic), "samples": _n_think,
         "brain2": (source == "deep-soch"),
        "helper": (source == "helper-soch"),
        "verify": (_ver_note or ((_ver_res or {}).get("reason")
                   if isinstance(_ver_res, dict) else None)),
         "intent": (_intent.get("kind") if F else ""),
         "flow": (F.line(verbose=(_flow_disp == "verbose"))
                  if F and _flow_disp != "off" else ""),
         "autonomous": {"answer": bool(_aut_base), "source": _aut_src,
                        "confidence": round(_aut_conf, 2), "kind": _aut_kind}}
    # 📚 AUTO-LEARNING: sirf verified/high-quality jawab yaad me (learner.py —
    # sha1-dedup, learned_chat.txt → retrieval agli dafa khud yaad karega)
    try:
        from model.learner import learn_from_chat as _lfc
        _lfc(prompt, text, m)
        _say("💾 seekh: ye jawab yaad ho gaya (agli dafa isi sawal par behtar)")
    except Exception:
        pass
    return (text, m) if meta else text


def _prewarm():
    """BG-thread: yaad-memo (pickle) + model-load + 1 mini-sample nudge —
    pehla sawal bhi ab randy turant (no API, no cloud, pure local)."""
    try:
        _qa_index()
        _words()
        _fsmemo()
        ck = best_checkpoint()
        if ck:
            _tok, _brain = _load_model(ck)
            _brain.sample("\nJawab:", _tok, max_new=12, temperature=0.5)  # 🔥 nudge
    except Exception:
        pass


def chat_loop():
    # 🔒 ULTRA-SECURITY: file integrity checks on boot
    try:
        from model.autonomous import verify_system_integrity
        ok, tampered = verify_system_integrity()
        if not ok:
            print("🛡️ ULTRA SECURITY ALERT: System files modified:", tampered)
            print("Unauthorized changes detected — Hemomemo AI band ho raha hai.")
            return
    except Exception:
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print("=" * 52)
    print(" 🤖 Hemomemo AI :: LIVE-ONLINE CHAT (asli web-parhi jab dimagh")
    print("    ke paas jawab na ho — no API, no cloud, no Ollama, no AI-platform)")
    print("    🧠 master-LSTM + 🧠🧠 brain2(deep) + ❤️ heart + 🤖 autonomous engine + 🌐 live research")
    print("    Ek hi system: sawal → yaad → research → khud-soch → brain2 → verify → jawab")
    print("    Sawal likho; 'quit' = band")
    print("=" * 52)
    from core.offline_oath import oath_text
    print(" ", oath_text().splitlines()[0])
    print("    🪜 commands: think auto|low|mid|high  |  ◈ flow on/off/verbose")
    print("    🌐 server on|off|status|key  — Hemomemo ki APNI API (L6-HMHZ guard)")
    print("=" * 52)
    print("=" * 52)
    # 🧠 PRE-WARM background me — menu TURANT khulta hai; pehla sawal bhi tez
    print(" 🧠 dimagh background me garam ho raha hai (pehli dafa e-thoda) — "
          "sawal likhte raho, sab turant")
    threading.Thread(target=_prewarm, daemon=True).start()
    # ❤️ DIL: chat shuru hote hi dhadkan shuru (strength/consolidation ke sath)
    try:
        from core.heart import start as _heart_start
        if _heart_start():
            print(" dil dhadak raha hai (strength barhta-tone) — chat "
                  "khamoshi me yaad mazbooti ❤")
    except Exception:
        pass
    while True:
        try:
            q = input("\n 👤 Aap: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n 👋 Hemomemo AI: milte hain dost!")
            return
        try:
            from model.understand import is_exit as _is_exit_fn
            if _is_exit_fn(q):
                print(" 👋 Hemomemo AI: Allah hafiz! (bye/farewell samajh gaya)")
                return
        except Exception:
            pass
        if q.lower() in {"quit", "exit", "bye"}:
            print(" 👋 Hemomemo AI: Allah hafiz!")
            return
        if not q:
            continue
        lowq = q.lower().strip()
        if lowq.startswith("flow"):
            arg = lowq.replace("flow", "").strip() or "on"
            from model.cognition import set_display
            stf = set_display(arg if arg in ("on", "off", "verbose", "auto")
                              else "on")
            print(" ◈ flow-display: %s  (phases: READ→FOCUS→RECALL→"
                  "RESEARCH?→THINK→VERIFY→LEARN→SPEAK)" % stf.get("display"))
            continue
        if lowq.startswith("think"):
            arg = lowq.replace("think", "").strip()
            from model.think_level import set_mode, load_state
            st = set_mode(arg if arg else "auto")
            print(" 🪜 think-level: mode=%s%s" % (
                st.get("mode"), (" → " + str(st.get("manual_tier")))
                if st.get("manual_tier") else " (sawal dekh kar khud chunta)"))
            continue
        if lowq.startswith("server"):
            arg = lowq.replace("server", "").strip() or "status"
            try:
                from server import hemomemo_server as _api
                if arg == "on" or arg.startswith("start"):
                    p = _api.start(int(arg.split()[-1])
                                   if arg.split()[-1].isdigit() else None)
                    print(" 🌐", p)
                    print("    apni key:", _api.key_info()["key"])
                elif arg in ("off", "stop"):
                    print(" 🌐", _api.stop())
                elif arg == "key":
                    print(" 🔑 Hemomemo apni API-key:", _api.key_info()["key"])
                else:
                    import json as _json
                    print(" 🌐", _json.dumps(_api.status(), ensure_ascii=False))
            except Exception as e:
                print(" 🌐 server masla:", str(e)[:100])
            continue
        print(" 🤔 Hemomemo AI: soch raha hai... (🧠 brain tick -> 📚 yaad -> ✍️ khud likhna)")
        txt, m = chat_once(q, meta=True)
        print(txt)
        if m:
            print("    🧠 %s | 📚 source: %s | 🪜 think: %s (%s) | 🪞 %s (doubt %.2f)"
                  % (m['brain'], m['source'], m.get('think'), m.get('mode'),
                     m.get('meta'), m.get('doubt', 0.0)))
            if m.get("flow"):
                print("    %s" % m["flow"])
            # 🫀 JAZBAAT/SENSORS status + 🌐 ONLINE haal (live-research hua?)
            try:
                from model.feelings import status_line as _feel_line
                print("    %s | 🌐 online-research: %s" % (
                    _feel_line(),
                    "yes" if (m.get("source") == "live-research"
                              or (m.get("autonomous") or {}).get("source")
                              == "live-research") else "no"))
            except Exception:
                pass


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(chat_once(" ".join(sys.argv[1:])))
    else:
        chat_loop()
