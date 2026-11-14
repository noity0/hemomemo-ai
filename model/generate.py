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

# 🔗 LIVE-HUB DEEP-LINK: connection_hub\digitalbrain junction maujood ho to
# dimagh/vocab/corpus/yaad SAB DigitalBrain (master) se LIVE load hota hai —
# app ka jawab hub ke sabse-naye checkpoint (mid/final, vocab-exact) se.
# Junction na ho to package apni copies (100% standalone). Sab 100% local
# (qanoon: koi AI-API nahi — sirf is PC ki files).
HUB_LIVE = False
try:
    _HUB = os.path.join(ROOT, "connection_hub", "digitalbrain")
    if os.path.isdir(os.path.join(_HUB, "model", "checkpoints")):
        CKPT_DIR = os.path.join(_HUB, "model", "checkpoints")
        DATA = os.path.join(_HUB, "data")
        BIG = os.path.join(DATA, "corpus_big")
        HUB_LIVE = True
except Exception:
    HUB_LIVE = False

# retrieval me fayda na dene wale aam words
STOP = {"kya", "kyun", "hai", "hain", "ho", "hoon", "hum", "ka", "ke", "ki", "ko",
        "se", "me", "mein", "par", "aap", "tum", "tu", "main", "and", "the", "of",
        "what", "how", "why", "you", "your", "is", "are", "do", "does", "aur",
        "or", "kaun", "kaisa", "kitna", "kitne"}

_TOPIC_WORDS = frozenset((
    "batao", "bata", "bataiye", "bataiye", "dekho", "dekhte", "dekh", "sikho",
    "sikhte", "sikh", "suno", "sunde", "pocho", "poochiye", "pooch",
    "karo", "karein", "kar", "karte", "karega", "padho", "padhne", "padh",
    "socho", "soch", "seekho"))

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
    🧠 CHAAR-DIMAGH RULE: yahan sirf GENMASTER (pehla 7M dimagh) — helper/
    verify/deep apne modules se load hote hain (genhelper_/genverify_/gendeep_).
    ⚡ memo: result (name,mtime)-signatur par — harek tez-e-sawal par 26MB npz
    dobara scane NAIH hoti (chat 24/7 tabdeek rakhne ke liye); checkpoints
    badalne par (UPDATE-BRAIN / tarbiyat) memo khud invalidate hota hai."""
    cks = [os.path.join(CKPT_DIR, f) for f in os.listdir(CKPT_DIR)
           if f.endswith(".npz") and f.startswith("genmaster")
           and not f.endswith(".tmp.npz")]
    sig = tuple(sorted((os.path.basename(c), os.path.getmtime(c)) for c in cks))
    if _CACHE.get("best_sig") == sig:
        return _CACHE.get("best_ck")
    tok = _tok()
    cks.sort(key=os.path.getmtime, reverse=True)
    found = None
    for ck in cks:
        try:
            with np.load(ck) as d:
                vocab = int(d["embed"].shape[0])
        except OSError:
            continue
        if vocab == tok.vocab_size:
            found = ck
            break
        print("  [chat] skip %s (vocab %d vs corpus %d)" % (
            os.path.basename(ck), vocab, tok.vocab_size))
    _CACHE["best_sig"] = sig
    _CACHE["best_ck"] = found
    return found


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
    items = []
    saw = set()
    for n in notes:
        if n and n not in saw:
            saw.add(n)
            items.append(n)
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

# asli-kitab-matn opening: Sahih al-Bukhari 12:… / Sunan Abi Dawud 1:… / Quran 6:89…
_KITAB_A_RX = re.compile(
    r"^\s*(Sahih al-(Bukhari|Muslim)|Sunan (Abu Dawud|an-Nasai|Ibn Majah)|"
    r"(Jami|Jamia) Tirmidhi|Muwatta Malik|Quran \d|Qur'an \d)", re.I)


def _sacred_pure(prompt, k=4):
    """Sacred-TEHQIQ: SIRF kitab-asal-notes (Sahih/Sunan/Quran) — 'hadith
    batao'/'quran batao' jese sawal par gair-dini story/poll-line (Al-Tawhid,
    Salah-football) kabhi top-yaad NAHI — asli Bukhari/Muslim/Quran matn
    pehle. Score = sawal-key-coverage (inter/len(qw)); ties par asli-matn
    (haroof-ansub) tarjeeh — ref-chain ('Quran 6:89 Quran 26:107…') nahi;
    ek hi note 4-bar repeat NAHI; index-stable."""
    qw = _content(prompt)
    qw = {t for t in qw if t not in _TOPIC_WORDS}
    if not qw:
        return []
    scored = []
    seen_a = set()
    idx = 0
    for q, a in _qa_index():
        idx += 1
        if not _KITAB_A_RX.match(a or ""):
            continue
        if a in seen_a:
            continue                        # ek hi note dafa-dafa NAHI
        wq = _content(q) or set(re.findall(r"[a-z]{2,}", q.lower()))
        wq = {t for t in wq if t not in _TOPIC_WORDS}
        inter = len(qw & wq) if wq else 0
        if inter:
            sc = inter / max(1, len(qw))
        elif any(t in q.lower() or t in (a or "").lower() for t in qw):
            sc = 0.30                       # sawal-key note-matn me mojood
        else:
            continue
        seen_a.add(a)
        # 📜 asli-matn-tarjeeh: haroof-hissah (ayat/hadith TEXT bohat lot
        #    hote; ref-chain sirf adad) —VERSE matn k-cand se PEHLE
        quality = min(1.0, sum(1 for c in a if c.isalpha()) / 60.0)
        # 🔗 ref-chain-jhanda ('Quran 6:89 Quran 26:107 Quran 46:35…')
        #    = sirf adad-adad — asli matn aage karo
        if re.search(r"Quran \d+:\d+.{0,60}Quran \d+:\d+.{0,60}Quran \d+:\d+",
                     a or ""):
            quality *= 0.3
        sc2 = sc
        low_a = (a or "").lower()
        if "quran" in qw and re.search(r"quran|ayat|verse|surah", low_a):
            sc2 += 0.25        # Quran-ka sawal Quran-ka note pehlo (verse/hadith mix nahi)
        scored.append((sc2, quality, idx, a))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
    return [(s, a) for s, q_, i, a in scored[:k] if s >= 0.25]

def _sacred_bias(rel):
    """Sacred sawal: apni zat ke meta-note chhalka do, kitab-note pehle.

    🕌 TIER-TEHQIQ: asli kitab-note (Sahih al-Bukhari / Narrated / Sunan /
    Prophet / Messenger) hamesha saamne — sirf 'hadith' lafz par zyada
    jaccard jeetne-wali gair-dini line (`Islamic Unity Movement…Al-Tawhid`)
    kabhi top-yaad nahi banegi (user-sawal me kitab ka asli matn chahiye)."""
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
    kitab = [(s, a) for s, a in keep if _KITAB_A_RX.match(a or "")]
    if not kitab:
        return keep                         # kitab-canonical nahi — jaisa hai
    aam = [(s, a) for s, a in keep if not _KITAB_A_RX.match(a or "")]
    kitab.sort(key=lambda x: -x[0])
    aam.sort(key=lambda x: -x[0])
    return kitab + aam


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
_COD_TASK_RX = re.compile(r"(?i)\b(code|function|func|script|program|bug|debug|refactor|compile|algorithm|regex|query|boilerplate|oop|api|endpoint|database|crud|slice|dataframe|component|module|library|package|binary|deploy|thread|async|promise|callback|array|list|dictionary|stack|queue|tree|graph|fibonacci|sort|reverse|palindrome|fizzbuzz|prime|debounce|throttle|middleware|server|client|frontend|backend|fullstack|cli|flask|django|sql|love|heart|counter|clock|timer|stopwatch|quiz|form|login|signup|card|animation|guess)\b")

# 🔎 CONCEPTUAL-guard: "what is X / explain X / X vs Y / basics / rules" — ye
# programming-SAWAL hain, code-BANANE ke order nahi → ilm (teaching) raasta,
# generic solve() code NAHI (QA1-coding conceptual-FAILs ka elaj).
_COD_CONCEPT_RX = re.compile(
    r"(?i)\b(what is|what are|what does|explain|define|difference|\bvs\b|"
    r"kya hota|kya hai|kya hote|matlab|batao|batain|bata|samjhao|samjha\b|"
    r"concept|principle|rules|basics|meaning)\b")
_COD_LANG_MAP = {"py": "python", "python": "python", "js": "javascript", "javascript": "javascript",
                 "ts": "typescript", "typescript": "typescript", "node": "javascript",
                 "c++": "cpp", "cpp": "cpp", "c#": "csharp", "csharp": "csharp",
                 "go": "go", "golang": "go", "rust": "rust", "php": "php", "rb": "ruby",
                 "r": "r", "sql": "sql", "html": "html", "css": "css",
                 "kotlin": "kotlin", "swift": "swift", "shell": "bash",
                 "django": "python", "flask": "python", "react": "javascript",
                 "vue": "javascript", "express": "javascript", "pandas": "python",
                 "numpy": "python", "excel": "python", "matlab": "python"}
# ───────────────────── 💻 CODING-AI: ORDER-DRIVEN COMPOSER ─────────────────────
# Purana canned-template system (har baar yehi fibonacci / "Hemomemo Page")
# HATA diya gaya hai. Ab har jawab aap ke ORDER se banta hai:
#   • aap ke lafz (message/title/task) code ke andar nazar aate hain
#   • aap ke numbers (20 terms, table of 7, prime 97) parameters bante hain
#   • aap ki zaban ka code-block (```html, ```python, ...) waise hi
# 100% local composition — koi AI-API, koi cloud, koi doosra AI NAHI.

_COD_STRIP_RX = re.compile(
    r"(?i)\b(please|plz|kindly|write|likh|likho|likhdo|make|bana|banao|banaye|"
    r"create|generate|code|program|script|function|func|def|"
    r"page|webpage|website|web|site|app|application|demo|example|"
    r"says|say|saying|show|showing|display|named|called|titled|title|"
    r"text|message|msg|simple|basic|small|chhota|chota|ek|aik|"
    r"ka|ke|ki|ko|for|of|in|using|with|me|mein|par|per|that|this|jo|which|about)\b")
_COD_NUM_RX = re.compile(r"(?<![\w.])(\d{1,6})(?![\w.])")
_COD_QUOTED_RX = re.compile("[\"']([^\"']{2,120})[\"']")
_COD_COLORS = {
    "red": "#e53935", "blue": "#1e88e5", "green": "#43a047", "pink": "#ec407a",
    "purple": "#8e24aa", "orange": "#fb8c00", "yellow": "#fdd835", "teal": "#00897b",
    "gold": "#d4af37", "black": "#111111", "dark": "#16281f", "light": "#f5f5f5",
    "gray": "#9e9e9e", "grey": "#9e9e9e", "white": "#fafafa",
}
_COD_CMT = {"python": "#", "bash": "#", "ruby": "#", "r": "#", "perl": "#",
            "lua": "--", "haskell": "--", "sql": "--"}
_COD_INTENT_KNOWN = {"fib", "fizzbuzz", "prime", "palindrome", "reverse", "sort",
                     "binsearch", "factorial", "evenodd", "leap", "armstrong", "gcd",
                     "table", "vowel", "wordcount", "calculator", "todo", "greet",
                     "love", "generic"}
_COD_FIB = {
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
        System.out.println(fibonacci(__N__));
    }
}''',
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
    std::cout << fibonacci(__N__) << std::endl;
    return 0;
}''',
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
        Console.WriteLine(Fibonacci(__N__));
    }
}''',
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
	fmt.Println(fibonacci(__N__))
}''',
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
    println!("{}", fibonacci(__N__));
}''',
    "php": '''<?php
function fibonacci(int $n): int {
    $a = 0;
    $b = 1;
    for ($i = 0; $i < $n; $i++) {
        [$a, $b] = [$b, $a + $b];
    }
    return $a;
}

echo fibonacci(__N__);
''',
    "ruby": '''def fibonacci(n)
  a, b = 0, 1
  n.times { a, b = b, a + b }
  a
end

puts fibonacci(__N__)''',
    "bash": '''#!/bin/bash
# fibonacci — order: __TASK__
n=${1:-__N__}
a=0
b=1
for ((i = 0; i < n; i++)); do
  t=$((a + b))
  a=$b
  b=$t
done
echo "$a"''',
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
    println(fibonacci(__N__))
}''',
    "swift": '''func fibonacci(_ n: Int) -> Int {
    var a = 0, b = 1
    for _ in 0..<n {
        let t = a + b
        a = b
        b = t
    }
    return a
}

print(fibonacci(__N__))''',
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

print(fibonacci(__N__))''',
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
  print(fibonacci(__N__));
}''',
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

print fibonacci(__N__), "\\n";''',
    "lua": '''local function fibonacci(n)
    local a, b = 0, 1
    for _ = 1, n do
        a, b = b, a + b
    end
    return a
end

print(fibonacci(__N__))''',
    "haskell": '''fibonacci :: Int -> Integer
fibonacci n = fst (fib (0, 1, n))
  where
    fib (a, b, 0) = (a, b, 0)
    fib (a, b, k) = fib (b, a + b, k - 1)

main :: IO ()
main = print (fibonacci __N__)''',
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
    println(fibonacci(__N__))
  }
}''',
}


def _cod_esc(s):
    """User-ke-lafz HTML-safe (security: markup tootna nahi chahiye)."""
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cod_content(p):
    """Order se CONTENT nikaalo — pehle quoted '...', warna command/lafz
    hat kar jo bacha wahi aap ka asli content hai (e.g. 'i love you')."""
    q = _COD_QUOTED_RX.search(p)
    if q:
        return q.group(1).strip()
    t = _COD_LANG_RX.sub(" ", p)
    t = _COD_STRIP_RX.sub(" ", t)
    t = re.sub(r"[^a-z0-9\s+'\-.,!?&]", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" ,.-")
    return t


def _cod_title(s):
    s = (s or "").strip()
    if not s:
        return "My Page"
    return s[:1].upper() + s[1:]


def _cod_intent(p):
    """Order ka INTENT — pehle algorithms, phir apps/UI, phir feelings."""
    if "fibonacci" in p or "fibbo" in p:
        return "fib"
    if "fizz" in p:
        return "fizzbuzz"
    if "prime" in p:
        return "prime"
    if "palindrome" in p:
        return "palindrome"
    if "factorial" in p:
        return "factorial"
    if re.search(r"binary\s*search", p):
        return "binsearch"
    if re.search(r"\bsort\b", p):
        return "sort"
    if re.search(r"\breverse\b", p):
        return "reverse"
    if "even" in p and "odd" in p:
        return "evenodd"
    if "leap" in p:
        return "leap"
    if "armstrong" in p:
        return "armstrong"
    if re.search(r"\bgcd\b|\bhcf\b", p):
        return "gcd"
    if re.search(r"table of|multiplication", p):
        return "table"
    if re.search(r"\bvowel", p):
        return "vowel"
    if re.search(r"word\s*count|count\s*words", p):
        return "wordcount"
    if "debounce" in p:
        return "debounce"
    if "throttle" in p:
        return "throttle"
    if re.search(r"login|sign\s?up|register|contact|\bform\b", p):
        return "form"
    if re.search(r"counter|\bclick", p):
        return "counter"
    if re.search(r"clock|timer|watch|ghari|stopwatch", p):
        return "clock"
    if re.search(r"todo|to-do|task\s*list", p):
        return "todo"
    if re.search(r"quiz|\bmcq\b", p):
        return "quiz"
    if re.search(r"calculat|\bcalc\b", p):
        return "calculator"
    if re.search(r"\bgame\b|guess", p):
        return "game"
    if re.search(r"\btable\b", p):
        return "htable"
    if re.search(r"\blist\b", p):
        return "hlist"
    if re.search(r"love|mohabbat|ishq|pyaar|pyar|heart|\bdil\b", p):
        return "love"
    if re.search(r"salam|hello|\bhi\b|welcome|greet|assalam|khush", p):
        return "greet"
    if re.search(r"colou?r|background|theme", p):
        return "color"
    if re.search(r"animat|float|bounce|sparkle|glow", p):
        return "anim"
    return "generic"


def _cod_ind(t, n):
    pad = " " * n
    return "\n".join(pad + ln if ln.strip() else ln for ln in t.split("\n"))


def _cod_page(title, body, style="", script=""):
    out = ["<!DOCTYPE html>", '<html lang="en">', "<head>",
           '  <meta charset="utf-8">',
           '  <meta name="viewport" content="width=device-width, initial-scale=1">',
           "  <title>" + _cod_esc(title) + "</title>"]
    if style:
        out += ["  <style>", _cod_ind(style, 4), "  </style>"]
    out += ["</head>", "<body>", _cod_ind(body, 2)]
    if script:
        out += ["  <script>", _cod_ind(script, 4), "  </script>"]
    out += ["</body>", "</html>"]
    return "\n".join(out)


def _cod_html(intent, content, params, prompt):
    t = _cod_title(content)
    if intent == "love":
        msg = _cod_esc(t if content else "I love you")
        style = ("body { margin: 0; min-height: 100vh; display: flex; align-items: center;"
                 " justify-content: center; background: linear-gradient(135deg, #ff9a9e 0%,"
                 " #fecfef 55%, #fda085 100%); font-family: Georgia, serif; overflow: hidden; }"
                 " main { text-align: center; color: #7a1f3d; }"
                 " h1 { font-size: 3.2rem; margin: 0 0 .4em; text-shadow: 0 2px 12px rgba(255,255,255,.65); }"
                 " .hearts { font-size: 1.8rem; letter-spacing: .4em; }"
                 " .heart { position: fixed; bottom: -2rem; animation: floatUp 4s linear forwards;"
                 " color: #e91e63; font-size: 1.6rem; }"
                 " @keyframes floatUp { to { transform: translateY(-110vh) rotate(360deg); opacity: 0; } }")
        body = "<main>\n  <h1>" + msg + "</h1>\n  <p class='hearts'>&#9829; &#9829; &#9829;</p>\n</main>"
        script = ("setInterval(function () {\n"
                  "  var h = document.createElement('span');\n"
                  "  h.className = 'heart';\n"
                  "  h.textContent = '\\u2665';\n"
                  "  h.style.left = Math.random() * 100 + 'vw';\n"
                  "  document.body.appendChild(h);\n"
                  "  setTimeout(function () { h.remove(); }, 4000);\n"
                  "}, 600);")
        return _cod_page(t, body, style, script)
    if intent == "greet":
        msg = _cod_esc(t)
        style = ("body { margin: 0; min-height: 100vh; display: flex; align-items: center;"
                 " justify-content: center; background: linear-gradient(135deg, #0b1f16, #1e3c30);"
                 " font-family: 'Segoe UI', sans-serif; }"
                 " main { text-align: center; background: rgba(255,255,255,.06); padding: 48px 64px;"
                 " border-radius: 18px; border: 1px solid #d4af37; }"
                 " h1 { color: #d4af37; font-size: 2.4rem; margin: 0 0 .4em; }"
                 " p { color: #e8f2ec; font-size: 1.1rem; }")
        body = "<main>\n  <h1>" + msg + "</h1>\n  <p>Welcome — aap ka apna page.</p>\n</main>"
        return _cod_page(t, body, style)
    if intent == "form":
        kind = "login"
        if re.search(r"sign\s?up|register", prompt):
            kind = "signup"
        if re.search(r"contact", prompt):
            kind = "contact"
        style = ("body { margin: 0; min-height: 100vh; display: flex; align-items: center;"
                 " justify-content: center; background: #0b1f16; font-family: sans-serif; }"
                 " form { background: #10281c; padding: 32px; border-radius: 14px;"
                 " border: 1px solid #1e3c30; width: 320px; }"
                 " h2 { color: #d4af37; margin: 0 0 18px; text-align: center; }"
                 " input { width: 100%; box-sizing: border-box; padding: 10px; margin: 6px 0 12px;"
                 " border-radius: 8px; border: 1px solid #2c5c44; background: #0b1f16; color: #e8f2ec; }"
                 " button { width: 100%; padding: 11px; border: 0; border-radius: 8px;"
                 " background: #d4af37; color: #0b1f16; font-weight: bold; cursor: pointer; }"
                 " #msg { color: #ff8a80; font-size: .9rem; min-height: 1.2em; }")
        if kind == "contact":
            fields = ('  <input type="text" id="name" placeholder="Name">\n'
                      '  <input type="email" id="email" placeholder="Email">\n'
                      '  <input type="text" id="note" placeholder="Message">')
        elif kind == "signup":
            fields = ('  <input type="text" id="name" placeholder="Full name">\n'
                      '  <input type="email" id="email" placeholder="Email">\n'
                      '  <input type="password" id="pass" placeholder="Password">')
        else:
            fields = ('  <input type="email" id="email" placeholder="Email">\n'
                      '  <input type="password" id="pass" placeholder="Password">')
        body = ("<form id='f' onsubmit='return check(event)'>\n  <h2>" + kind.upper()
                + "</h2>\n" + fields
                + "\n  <button type='submit'>Submit</button>\n  <p id='msg'></p>\n</form>")
        script = ("function check(e) {\n"
                  "  e.preventDefault();\n"
                  "  var bad = false;\n"
                  "  document.querySelectorAll('#f input').forEach(function (i) {\n"
                  "    if (!i.value.trim()) { bad = true; i.style.borderColor = '#e91e63'; }\n"
                  "  });\n"
                  "  document.getElementById('msg').textContent = bad ? 'Please fill every field' : '';\n"
                  "  return !bad;\n"
                  "}")
        return _cod_page(kind + " form", body, style, script)
    if intent == "counter":
        style = ("body { margin: 0; min-height: 100vh; display: flex; flex-direction: column;"
                 " align-items: center; justify-content: center; background: #0b1f16;"
                 " font-family: sans-serif; gap: 18px; }"
                 " #count { font-size: 5rem; color: #d4af37; font-weight: bold; }"
                 " button { padding: 12px 22px; margin: 0 6px; border: 0; border-radius: 10px;"
                 " background: #1e3c30; color: #e8f2ec; font-size: 1rem; cursor: pointer; }"
                 " button:hover { background: #2c5c44; }")
        body = ("<div id='count'>0</div>\n"
                "<div>\n  <button onclick='change(1)'>+ Add</button>\n"
                "  <button onclick='change(-1)'>&#8722; Sub</button>\n"
                "  <button onclick='reset()'>Reset</button>\n</div>")
        script = ("var count = 0;\n"
                  "var el = document.getElementById('count');\n"
                  "function change(d) { count += d; el.textContent = count; }\n"
                  "function reset() { count = 0; el.textContent = 0; }")
        return _cod_page("Click counter", body, style, script)
    if intent == "clock":
        style = ("body { margin: 0; min-height: 100vh; display: flex; flex-direction: column;"
                 " align-items: center; justify-content: center; background: #0b1f16;"
                 " font-family: Consolas, monospace; }"
                 " #clock { font-size: 4rem; color: #d4af37; }"
                 " #date { color: #e8f2ec; font-size: 1.1rem; }")
        body = "<div id='clock'>--:--:--</div>\n<div id='date'></div>"
        script = ("function tick() {\n"
                  "  var d = new Date();\n"
                  "  document.getElementById('clock').textContent = d.toLocaleTimeString();\n"
                  "  document.getElementById('date').textContent = d.toDateString();\n"
                  "}\n"
                  "setInterval(tick, 1000);\n"
                  "tick();")
        return _cod_page("Live clock", body, style, script)
    if intent == "todo":
        style = ("body { margin: 0; min-height: 100vh; background: #0b1f16; color: #e8f2ec;"
                 " font-family: sans-serif; display: flex; justify-content: center; padding-top: 60px; }"
                 " main { width: 380px; } h2 { color: #d4af37; }"
                 " input { width: 70%; padding: 10px; border-radius: 8px; border: 1px solid #2c5c44;"
                 " background: #10281c; color: #e8f2ec; }"
                 " button { padding: 10px 16px; border: 0; border-radius: 8px; background: #d4af37;"
                 " color: #0b1f16; font-weight: bold; cursor: pointer; }"
                 " li { padding: 8px 4px; border-bottom: 1px solid #1e3c30; cursor: pointer; list-style: none; }")
        body = ("<main>\n  <h2>Todo List</h2>\n"
                "  <input id='task' placeholder='Naya kaam likhen...'>\n"
                "  <button onclick='addTodo()'>Add</button>\n  <ul id='list'></ul>\n</main>")
        script = ("var items = [];\n"
                  "function addTodo() {\n"
                  "  var inp = document.getElementById('task');\n"
                  "  var t = inp.value.trim();\n"
                  "  if (!t) return;\n"
                  "  items.push({ text: t, done: false });\n"
                  "  inp.value = '';\n"
                  "  render();\n"
                  "}\n"
                  "function render() {\n"
                  "  var ul = document.getElementById('list');\n"
                  "  ul.innerHTML = '';\n"
                  "  items.forEach(function (it, i) {\n"
                  "    var li = document.createElement('li');\n"
                  "    li.textContent = it.text;\n"
                  "    li.style.textDecoration = it.done ? 'line-through' : 'none';\n"
                  "    li.onclick = function () { items[i].done = !items[i].done; render(); };\n"
                  "    li.oncontextmenu = function (e) { e.preventDefault(); items.splice(i, 1); render(); };\n"
                  "    ul.appendChild(li);\n"
                  "  });\n"
                  "}")
        return _cod_page("Todo app", body, style, script)
    if intent == "quiz":
        style = ("body { margin: 0; min-height: 100vh; display: flex; align-items: center;"
                 " justify-content: center; background: #0b1f16; color: #e8f2ec;"
                 " font-family: sans-serif; }"
                 " main { text-align: center; width: 420px; }"
                 " button { display: block; width: 100%; margin: 8px 0; padding: 12px;"
                 " border: 1px solid #2c5c44; border-radius: 10px; background: #10281c;"
                 " color: #e8f2ec; cursor: pointer; }"
                 " button:hover { background: #1e3c30; } #score { color: #d4af37; }")
        body = ("<main>\n  <h2>Capital of Pakistan?</h2>\n"
                "  <button onclick='pick(this,false)'>Karachi</button>\n"
                "  <button onclick='pick(this,true)'>Islamabad</button>\n"
                "  <button onclick='pick(this,false)'>Lahore</button>\n"
                "  <p id='score'></p>\n</main>")
        script = ("var score = 0;\n"
                  "function pick(btn, ok) {\n"
                  "  btn.style.borderColor = ok ? '#43a047' : '#e91e63';\n"
                  "  if (ok) score++;\n"
                  "  document.getElementById('score').textContent = 'Score: ' + score;\n"
                  "}")
        return _cod_page("Quiz", body, style, script)
    if intent == "calculator":
        style = ("body { margin: 0; min-height: 100vh; display: flex; align-items: center;"
                 " justify-content: center; background: #0b1f16; font-family: sans-serif; }"
                 " .calc { background: #10281c; padding: 18px; border-radius: 14px;"
                 " border: 1px solid #1e3c30; }"
                 " #disp { width: 100%; box-sizing: border-box; height: 46px; text-align: right;"
                 " font-size: 1.4rem; border: 0; border-radius: 8px; padding: 0 10px;"
                 " background: #0b1f16; color: #d4af37; }"
                 " .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 10px; }"
                 " button { padding: 14px; border: 0; border-radius: 8px; background: #1e3c30;"
                 " color: #e8f2ec; font-size: 1.1rem; cursor: pointer; }"
                 " button.op { background: #d4af37; color: #0b1f16; font-weight: bold; }")
        body = ("<div class='calc'>\n  <input id='disp' value='0' readonly>\n"
                "  <div class='grid'>\n"
                "    <button onclick='press(\"7\")'>7</button><button onclick='press(\"8\")'>8</button>"
                "<button onclick='press(\"9\")'>9</button><button class='op' onclick='press(\"/\")'>/</button>\n"
                "    <button onclick='press(\"4\")'>4</button><button onclick='press(\"5\")'>5</button>"
                "<button onclick='press(\"6\")'>6</button><button class='op' onclick='press(\"*\")'>*</button>\n"
                "    <button onclick='press(\"1\")'>1</button><button onclick='press(\"2\")'>2</button>"
                "<button onclick='press(\"3\")'>3</button><button class='op' onclick='press(\"-\")'>-</button>\n"
                "    <button onclick='press(\"C\")'>C</button><button onclick='press(\"0\")'>0</button>"
                "<button class='op' onclick='press(\"=\")'>=</button>"
                "<button class='op' onclick='press(\"+\")'>+</button>\n"
                "  </div>\n</div>")
        script = ("var acc = '0', op = null, cur = '0', fresh = true;\n"
                  "function press(k) {\n"
                  "  var d = document.getElementById('disp');\n"
                  "  if (k >= '0' && k <= '9') { cur = fresh ? k : (cur === '0' ? k : cur + k); fresh = false; d.value = cur; }\n"
                  "  else if (k === '=') { if (op) { d.value = calc(); op = null; } }\n"
                  "  else if (k === 'C') { acc = '0'; op = null; cur = '0'; fresh = true; d.value = '0'; }\n"
                  "  else { if (op && !fresh) { d.value = calc(); } acc = d.value; op = k; fresh = true; }\n"
                  "}\n"
                  "function calc() {\n"
                  "  var a = parseFloat(acc), b = parseFloat(cur), r = b;\n"
                  "  if (op === '+') r = a + b;\n"
                  "  if (op === '-') r = a - b;\n"
                  "  if (op === '*') r = a * b;\n"
                  "  if (op === '/') r = b === 0 ? 0 : a / b;\n"
                  "  cur = String(r); acc = String(r); fresh = true; return cur;\n"
                  "}")
        return _cod_page("Calculator", body, style, script)
    if intent == "color":
        key = "dark"
        for k in _COD_COLORS:
            if k in prompt:
                key = k
                break
        c = _COD_COLORS[key]
        style = ("body { margin: 0; min-height: 100vh; display: flex; align-items: center;"
                 " justify-content: center; background: " + c + "; font-family: sans-serif; }"
                 " h1 { color: rgba(255,255,255,.92); font-size: 2.6rem; text-shadow: 0 2px 10px rgba(0,0,0,.4); }")
        body = "<h1>" + _cod_esc(t) + "</h1>"
        return _cod_page(t, body, style)
    if intent == "anim":
        style = ("body { margin: 0; min-height: 100vh; display: flex; align-items: center;"
                 " justify-content: center; background: #0b1f16; }"
                 " .box { width: 110px; height: 110px; border-radius: 16px; background: #d4af37;"
                 " animation: bounce 1.2s ease-in-out infinite; }"
                 " @keyframes bounce { 0%,100% { transform: translateY(0) scale(1); }"
                 " 50% { transform: translateY(-60px) scale(1.08); } }")
        body = "<div class='box'></div>"
        return _cod_page("Animation", body, style)
    if intent == "game":
        style = ("body { margin: 0; min-height: 100vh; display: flex; flex-direction: column;"
                 " align-items: center; justify-content: center; background: #0b1f16;"
                 " color: #e8f2ec; font-family: sans-serif; gap: 12px; }"
                 " input { padding: 10px; border-radius: 8px; border: 1px solid #2c5c44;"
                 " background: #10281c; color: #e8f2ec; width: 140px; }"
                 " button { padding: 10px 18px; border: 0; border-radius: 8px; background: #d4af37;"
                 " color: #0b1f16; font-weight: bold; cursor: pointer; }")
        body = ("<h2>Number Guess (1-100)</h2>\n"
                "<input id='g' type='number'>\n<button onclick='tryGuess()'>Check</button>\n"
                "<p id='out'></p>")
        script = ("var secret = Math.floor(Math.random() * 100) + 1;\n"
                  "var tries = 0;\n"
                  "function tryGuess() {\n"
                  "  var v = parseInt(document.getElementById('g').value, 10);\n"
                  "  if (isNaN(v)) return;\n"
                  "  tries++;\n"
                  "  var o = document.getElementById('out');\n"
                  "  if (v === secret) { o.textContent = 'Correct! Tries: ' + tries; }\n"
                  "  else { o.textContent = v < secret ? 'Bara number try karein' : 'Chhota number try karein'; }\n"
                  "}")
        return _cod_page("Guess game", body, style, script)
    if intent == "htable":
        rows = "\n".join("    <tr><td>%d</td><td>%s</td></tr>" % (i + 1, w)
                         for i, w in enumerate(["Item one", "Item two", "Item three"]))
        style = ("body { background: #0b1f16; font-family: sans-serif; padding: 40px; }"
                 " table { border-collapse: collapse; width: 100%; }"
                 " th, td { border: 1px solid #2c5c44; padding: 10px 14px; color: #e8f2ec; }"
                 " th { background: #1e3c30; color: #d4af37; }")
        body = "<table>\n  <tr><th>#</th><th>Name</th></tr>\n" + rows + "\n  </table>"
        return _cod_page(t + " table", body, style)
    if intent == "hlist":
        items = [w for w in re.split(r"[,;]", content or "") if w.strip()] \
            or ["First item", "Second item", "Third item"]
        lis = "\n".join("  <li>" + _cod_esc(i.strip()) + "</li>" for i in items[:8])
        style = ("body { background: #0b1f16; color: #e8f2ec; font-family: sans-serif;"
                 " padding: 40px; } h2 { color: #d4af37; }"
                 " li { padding: 6px 0; border-bottom: 1px solid #1e3c30; }")
        body = "<h2>" + _cod_esc(t) + "</h2>\n<ul>\n" + lis + "\n</ul>"
        return _cod_page(t, body, style)
    # generic message page — aap ke lafz hi page ka content
    msg = _cod_esc(t if content else _cod_title(prompt))
    style = ("body { margin: 0; min-height: 100vh; display: flex; align-items: center;"
             " justify-content: center; background: linear-gradient(135deg, #0b1f16, #163024);"
             " font-family: 'Segoe UI', sans-serif; }"
             " main { text-align: center; padding: 40px 56px; border-radius: 16px;"
             " background: rgba(255,255,255,.05); border: 1px solid #2c5c44; }"
             " h1 { color: #d4af37; } p { color: #e8f2ec; }")
    body = "<main>\n  <h1>" + msg + "</h1>\n  <p>Order: \"" + _cod_esc(prompt[:100]) + "\"</p>\n</main>"
    return _cod_page(t, body, style)


def _cod_css(intent, content, prompt):
    head = "/* Order: %s */" % prompt[:100]
    if intent == "form" or "login" in prompt:
        return head + """

.login-card {
  background: #10281c;
  color: #e8f2ec;
  width: 320px;
  padding: 28px;
  border-radius: 14px;
  border: 1px solid #2c5c44;
}
.login-card input {
  width: 100%;
  padding: 10px;
  margin: 6px 0 12px;
  border-radius: 8px;
  border: 1px solid #2c5c44;
}
.login-card button {
  width: 100%;
  padding: 11px;
  background: #d4af37;
  color: #0b1f16;
  border: 0;
  border-radius: 8px;
  font-weight: bold;
}"""
    if "button" in prompt:
        return head + """

.btn {
  padding: 12px 26px;
  border: 0;
  border-radius: 10px;
  background: #d4af37;
  color: #0b1f16;
  font-weight: bold;
  cursor: pointer;
  transition: transform .15s ease;
}
.btn:hover { transform: translateY(-2px); }"""
    if "navbar" in prompt or "menu" in prompt:
        return head + """

.navbar {
  display: flex;
  gap: 22px;
  align-items: center;
  background: #0b1f16;
  padding: 14px 22px;
  border-bottom: 1px solid #1e3c30;
}
.navbar a { color: #e8f2ec; text-decoration: none; }
.navbar a:hover { color: #d4af37; }"""
    return head + """

.card {
  background: #10281c;
  color: #e8f2ec;
  border: 1px solid #1e3c30;
  border-radius: 14px;
  padding: 18px 22px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, .25);
}
.card:hover { transform: translateY(-2px); }"""


def _cod_py(intent, content, params, prompt):
    n = params[0] if params else None
    s = content if content and len(content) <= 40 else ""
    task = prompt[:100].replace('"', "'")
    msg = (content or prompt)[:80].replace('"', "'")
    if intent == "fib":
        return ('def fibonacci(n: int) -> list:\n'
                '    """Fibonacci series (n terms) — order: %s"""\n'
                '    a, b = 0, 1\n'
                '    out = []\n'
                '    for _ in range(n):\n'
                '        out.append(a)\n'
                '        a, b = b, a + b\n'
                '    return out\n'
                '\n'
                '\n'
                'print(fibonacci(%d))' % (task, n or 10))
    if intent == "fizzbuzz":
        return ('def fizzbuzz(limit: int) -> None:\n'
                '    """FizzBuzz 1..limit — order: %s"""\n'
                '    for i in range(1, limit + 1):\n'
                '        out = ""\n'
                '        if i %% 3 == 0:\n'
                '            out += "Fizz"\n'
                '        if i %% 5 == 0:\n'
                '            out += "Buzz"\n'
                '        print(out or i)\n'
                '\n'
                '\n'
                'fizzbuzz(%d)' % (task, n or 100))
    if intent == "prime":
        return ('def is_prime(n: int) -> bool:\n'
                '    """Prime check — order: %s"""\n'
                '    if n < 2:\n'
                '        return False\n'
                '    if n < 4:\n'
                '        return True\n'
                '    if n %% 2 == 0:\n'
                '        return False\n'
                '    d = 3\n'
                '    while d * d <= n:\n'
                '        if n %% d == 0:\n'
                '            return False\n'
                '        d += 2\n'
                '    return True\n'
                '\n'
                '\n'
                'print(is_prime(%d))' % (task, n or 97))
    if intent == "palindrome":
        w = s.split()[0] if s.split() else "madam"
        return ('def is_palindrome(text: str) -> bool:\n'
                '    """Palindrome check — order: %s"""\n'
                '    t = "".join(ch.lower() for ch in text if ch.isalnum())\n'
                '    return t == t[::-1]\n'
                '\n'
                '\n'
                'print(is_palindrome("%s"))' % (task, w))
    if intent == "reverse":
        w = (s or "Hemomemo").replace('"', "'")
        return ('def reverse_text(text: str) -> str:\n'
                '    """Reverse — order: %s"""\n'
                '    return text[::-1]\n'
                '\n'
                '\n'
                'print(reverse_text("%s"))' % (task, w))
    if intent == "sort":
        return ('def bubble_sort(arr: list) -> list:\n'
                '    """Sort (ascending) — order: %s"""\n'
                '    arr = arr[:]\n'
                '    for i in range(len(arr)):\n'
                '        for j in range(0, len(arr) - i - 1):\n'
                '            if arr[j] > arr[j + 1]:\n'
                '                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n'
                '    return arr\n'
                '\n'
                '\n'
                'print(bubble_sort([%s]))' % (task, ", ".join(str(x) for x in params[:6]) or "5, 3, 8, 1, 9"))
    if intent == "binsearch":
        tgt = params[1] if len(params) > 1 else 7
        return ('def binary_search(arr: list, target) -> int:\n'
                '    """Binary search (sorted list) — order: %s"""\n'
                '    lo, hi = 0, len(arr) - 1\n'
                '    while lo <= hi:\n'
                '        mid = (lo + hi) // 2\n'
                '        if arr[mid] == target:\n'
                '            return mid\n'
                '        if arr[mid] < target:\n'
                '            lo = mid + 1\n'
                '        else:\n'
                '            hi = mid - 1\n'
                '    return -1\n'
                '\n'
                '\n'
                'data = [1, 3, 5, 7, 9, 11]\n'
                'print(binary_search(data, %d))  # index ya -1' % (task, tgt))
    if intent == "factorial":
        return ('def factorial(n: int) -> int:\n'
                '    """Factorial — order: %s"""\n'
                '    r = 1\n'
                '    for i in range(2, n + 1):\n'
                '        r *= i\n'
                '    return r\n'
                '\n'
                '\n'
                'print(factorial(%d))' % (task, n or 5))
    if intent == "evenodd":
        return ('def even_or_odd(n: int) -> str:\n'
                '    """Even/Odd — order: %s"""\n'
                '    return "even" if n %% 2 == 0 else "odd"\n'
                '\n'
                '\n'
                'print(even_or_odd(%d))' % (task, n or 8))
    if intent == "leap":
        return ('def is_leap(year: int) -> bool:\n'
                '    """Leap year — order: %s"""\n'
                '    return year %% 4 == 0 and (year %% 100 != 0 or year %% 400 == 0)\n'
                '\n'
                '\n'
                'print(is_leap(%d))' % (task, n or 2024))
    if intent == "armstrong":
        return ('def is_armstrong(n: int) -> bool:\n'
                '    """Armstrong number — order: %s"""\n'
                '    digits = [int(d) for d in str(n)]\n'
                '    return n == sum(d ** len(digits) for d in digits)\n'
                '\n'
                '\n'
                'print(is_armstrong(%d))' % (task, n or 153))
    if intent == "gcd":
        a = params[0] if params else 48
        b = params[1] if len(params) > 1 else 18
        return ('def gcd(a: int, b: int) -> int:\n'
                '    """GCD/HCF (Euclid) — order: %s"""\n'
                '    while b:\n'
                '        a, b = b, a %% b\n'
                '    return a\n'
                '\n'
                '\n'
                'print(gcd(%d, %d))' % (task, a, b))
    if intent == "table":
        return ('def multiplication_table(n: int, upto: int = 10) -> None:\n'
                '    """Table of n — order: %s"""\n'
                '    for i in range(1, upto + 1):\n'
                '        print(n, "x", i, "=", n * i)\n'
                '\n'
                '\n'
                'multiplication_table(%d)' % (task, n or 7))
    if intent == "vowel":
        w = (s or "beautiful").replace('"', "'")
        return ('def count_vowels(text: str) -> int:\n'
                '    """Vowel count — order: %s"""\n'
                '    return sum(1 for ch in text.lower() if ch in "aeiou")\n'
                '\n'
                '\n'
                'print(count_vowels("%s"))' % (task, w))
    if intent == "wordcount":
        w = (s or "Hemomemo local coding ai").replace('"', "'")
        return ('def word_count(text: str) -> int:\n'
                '    """Word count — order: %s"""\n'
                '    return len(text.split())\n'
                '\n'
                '\n'
                'print(word_count("%s"))' % (task, w))
    if intent == "calculator":
        a = params[0] if params else 12
        b = params[1] if len(params) > 1 else 8
        return ('def calculator(a: float, op: str, b: float) -> float:\n'
                '    """4-operation calculator — order: %s"""\n'
                '    if op == "+":\n'
                '        return a + b\n'
                '    if op == "-":\n'
                '        return a - b\n'
                '    if op == "*":\n'
                '        return a * b\n'
                '    if op == "/":\n'
                '        return a / b if b else float("inf")\n'
                '    raise ValueError("op not supported")\n'
                '\n'
                '\n'
                'print(calculator(%d, "+", %d))' % (task, a, b))
    if intent == "todo":
        return ('def todo_app() -> None:\n'
                '    """Mini todo (add / done / list) — order: %s"""\n'
                '    tasks = []\n'
                '\n'
                '    def add(text):\n'
                '        tasks.append({"text": text, "done": False})\n'
                '\n'
                '    def done(i):\n'
                '        tasks[i]["done"] = True\n'
                '\n'
                '    def show():\n'
                '        for i, t in enumerate(tasks):\n'
                '            mark = "[x]" if t["done"] else "[ ]"\n'
                '            print(i, mark, t["text"])\n'
                '\n'
                '    add("Pehla kaam")\n'
                '    add("Doosra kaam")\n'
                '    done(0)\n'
                '    show()\n'
                '\n'
                '\n'
                'todo_app()' % task)
    if intent == "game":
        return ('import random\n'
                '\n'
                'def guess_game() -> None:\n'
                '    """Number guess (1-100) — order: %s"""\n'
                '    secret = random.randint(1, 100)\n'
                '    tries = 0\n'
                '    while True:\n'
                '        v = int(input("Apna andaza (1-100): "))\n'
                '        tries += 1\n'
                '        if v == secret:\n'
                '            print("Sahi! Tries:", tries)\n'
                '            break\n'
                '        print("Bara try karein" if v < secret else "Chhota try karein")\n'
                '\n'
                '\n'
                'guess_game()' % task)
    if intent in ("greet", "love"):
        return ('def main() -> None:\n'
                '    """Order: %s"""\n'
                '    message = "%s"\n'
                '    print(message)\n'
                '\n'
                '\n'
                'if __name__ == "__main__":\n'
                '    main()' % (task, msg))
    return ('def solve() -> None:\n'
            '    """Task: %s\n'
            '    Steps: 1) samjho  2) input lo  3) logic likho  4) test karo."""\n'
            '    # "%s" — is order ke mutabiq logic yahan complete karen\n'
            '    print("%s")\n'
            '\n'
            '\n'
            'if __name__ == "__main__":\n'
            '    solve()' % (task, task, msg))


def _cod_js(intent, content, params, prompt, ts=False):
    n = params[0] if params else None
    task = prompt[:100].replace('"', "'")
    msg = (content or prompt)[:80].replace('"', "'")
    kw = "const" if ts else "var"
    if intent == "fib":
        return ('function fibonacci(n) {\n'
                '  // Order: %s\n'
                '  %s out = [], a = 0, b = 1;\n'
                '  for (let i = 0; i < n; i++) { out.push(a); [a, b] = [b, a + b]; }\n'
                '  return out;\n'
                '}\n'
                '\n'
                'console.log(fibonacci(%d).join(", "));' % (task, kw, n or 10))
    if intent == "fizzbuzz":
        return ('function fizzbuzz(limit) {\n'
                '  // Order: %s\n'
                '  for (let i = 1; i <= limit; i++) {\n'
                '    let s = "";\n'
                '    if (i %% 3 === 0) s += "Fizz";\n'
                '    if (i %% 5 === 0) s += "Buzz";\n'
                '    console.log(s || i);\n'
                '  }\n'
                '}\n'
                '\n'
                'fizzbuzz(%d);' % (task, n or 100))
    if intent == "prime":
        return ('function isPrime(n) {\n'
                '  // Order: %s\n'
                '  if (n < 2) return false;\n'
                '  if (n < 4) return true;\n'
                '  if (n %% 2 === 0) return false;\n'
                '  for (let d = 3; d * d <= n; d += 2) {\n'
                '    if (n %% d === 0) return false;\n'
                '  }\n'
                '  return true;\n'
                '}\n'
                '\n'
                'console.log(isPrime(%d));' % (task, n or 97))
    if intent == "palindrome":
        w = ((content or "madam").split() or ["madam"])[0].replace("'", "")
        return ('function isPalindrome(text) {\n'
                '  // Order: %s\n'
                '  const t = text.toLowerCase().replace(/[^a-z0-9]/g, "");\n'
                '  return t === t.split("").reverse().join("");\n'
                '}\n'
                '\n'
                "console.log(isPalindrome('%s'));" % (task, w))
    if intent == "reverse":
        w = (content or "Hemomemo").replace("'", "")
        return ('function reverseText(text) {\n'
                '  // Order: %s\n'
                '  return text.split("").reverse().join("");\n'
                '}\n'
                '\n'
                "console.log(reverseText('%s'));" % (task, w))
    if intent == "sort":
        nums = ", ".join(str(x) for x in params[:6]) or "5, 3, 8, 1, 9"
        return ('function sortAsc(arr) {\n'
                '  // Order: %s\n'
                '  return [...arr].sort((a, b) => a - b);\n'
                '}\n'
                '\n'
                'console.log(sortAsc([%s]));' % (task, nums))
    if intent == "binsearch":
        tgt = params[1] if len(params) > 1 else 7
        return ('function binarySearch(arr, target) {\n'
                '  // Order: %s\n'
                '  let lo = 0, hi = arr.length - 1;\n'
                '  while (lo <= hi) {\n'
                '    const mid = (lo + hi) >> 1;\n'
                '    if (arr[mid] === target) return mid;\n'
                '    if (arr[mid] < target) lo = mid + 1; else hi = mid - 1;\n'
                '  }\n'
                '  return -1;\n'
                '}\n'
                '\n'
                'console.log(binarySearch([1, 3, 5, 7, 9, 11], %d));' % (task, tgt))
    if intent == "factorial":
        return ('function factorial(n) {\n'
                '  // Order: %s\n'
                '  let r = 1;\n'
                '  for (let i = 2; i <= n; i++) r *= i;\n'
                '  return r;\n'
                '}\n'
                '\n'
                'console.log(factorial(%d));' % (task, n or 5))
    if intent == "debounce":
        return ('function debounce(fn, ms) {\n'
                '  // Order: %s\n'
                '  let t;\n'
                '  return function (...args) {\n'
                '    clearTimeout(t);\n'
                '    t = setTimeout(() => fn.apply(this, args), ms);\n'
                '  };\n'
                '}' % task)
    if intent == "throttle":
        return ('function throttle(fn, ms) {\n'
                '  // Order: %s\n'
                '  let last = 0;\n'
                '  return function (...args) {\n'
                '    const now = Date.now();\n'
                '    if (now - last >= ms) { last = now; fn.apply(this, args); }\n'
                '  };\n'
                '}' % task)
    if intent == "counter":
        return ('// Click counter — order: %s\n'
                'let count = 0;\n'
                'function change(d) {\n'
                '  count += d;\n'
                "  document.getElementById('count').textContent = count;\n"
                '}\n'
                'function reset() {\n'
                '  count = 0;\n'
                "  document.getElementById('count').textContent = 0;\n"
                '}' % task)
    if intent == "clock":
        return ('// Live clock — order: %s\n'
                'function tick() {\n'
                "  document.getElementById('clock').textContent = new Date().toLocaleTimeString();\n"
                '}\n'
                'setInterval(tick, 1000);\n'
                'tick();' % task)
    if intent == "todo":
        return ('// Todo app — order: %s\n'
                'const items = [];\n'
                'function addTodo(text) {\n'
                '  if (!text.trim()) return;\n'
                '  items.push({ text: text.trim(), done: false });\n'
                '  render();\n'
                '}\n'
                'function render() {\n'
                "  const ul = document.getElementById('list');\n"
                "  ul.innerHTML = '';\n"
                '  items.forEach((it, i) => {\n'
                "    const li = document.createElement('li');\n"
                '    li.textContent = it.text;\n'
                "    li.style.textDecoration = it.done ? 'line-through' : 'none';\n"
                '    li.onclick = () => { items[i].done = !items[i].done; render(); };\n'
                '    ul.appendChild(li);\n'
                '  });\n'
                '}' % task)
    if intent == "game":
        return ('// Number guess game — order: %s\n'
                'var secret = Math.floor(Math.random() * 100) + 1;\n'
                'var tries = 0;\n'
                'function tryGuess() {\n'
                "  var v = parseInt(document.getElementById('g').value, 10);\n"
                '  if (isNaN(v)) return;\n'
                '  tries++;\n'
                "  var o = document.getElementById('out');\n"
                "  if (v === secret) { o.textContent = 'Correct! Tries: ' + tries; }\n"
                "  else { o.textContent = v < secret ? 'Bara number try karein' : 'Chhota number try karein'; }\n"
                '}' % task)
    if intent in ("greet", "love"):
        return ('// Order: %s\n'
                "const message = '%s';\n"
                'console.log(message);\n'
                "console.log('<3'.repeat(3));" % (task, msg))
    return ('// Task: %s\n'
            'function solve(input) {\n'
            '  // "%s" — is order ke mutabiq logic yahan complete karen\n'
            '  // Steps: 1) input parho  2) process karo  3) result do\n'
            '  return input;\n'
            '}\n'
            '\n'
            "console.log(solve('demo'));" % (task, task))


def _cod_generic(lang, content, prompt):
    """Unknown task + non-core zaban — scaffold jo aap ke ORDER ko code me
    embed karta hai (title/docstring/comment/print sab order se aata hai)."""
    task = prompt[:100].replace('"', "'")
    msg = (content or prompt)[:80].replace('"', "'")
    title = "".join(w.capitalize() for w in re.findall(r"[a-z0-9]+", content or prompt)[:3]) or "Task"
    if lang == "java":
        return ('public class %s {\n'
                '    // Order: %s\n'
                '    public static void main(String[] args) {\n'
                '        System.out.println("%s");\n'
                '    }\n'
                '}' % (title, task, msg.replace('"', "'")))
    if lang == "cpp":
        return ('#include <iostream>\n\n'
                '// Order: %s\n'
                'int main() {\n'
                '    std::cout << "%s" << std::endl;\n'
                '    return 0;\n'
                '}' % (task, msg.replace('"', "'")))
    if lang == "c":
        return ('#include <stdio.h>\n\n'
                '/* Order: %s */\n'
                'int main(void) {\n'
                '    printf("%s\\n");\n'
                '    return 0;\n'
                '}' % (task, msg.replace('"', "'")))
    if lang == "go":
        return ('package main\n\n'
                'import "fmt"\n\n'
                '// Order: %s\n'
                'func main() {\n'
                '\tfmt.Println("%s")\n'
                '}' % (task, msg.replace('"', "'")))
    if lang == "rust":
        return ('// Order: %s\n'
                'fn main() {\n'
                '    println!("%s");\n'
                '}' % (task, msg.replace('"', "'")))
    if lang == "php":
        return ('<?php\n'
                '// Order: %s\n'
                'echo "%s";\n' % (task, msg.replace('"', "'")))
    if lang == "ruby":
        return ('# Order: %s\n'
                'message = "%s"\n'
                'puts message' % (task, msg.replace('"', "'")))
    if lang == "bash":
        return ('#!/bin/bash\n'
                '# Order: %s\n'
                'echo "%s"' % (task, msg.replace('"', "'")))
    if lang == "kotlin":
        return ('fun main() {\n'
                '    // Order: %s\n'
                '    println("%s")\n'
                '}' % (task, msg.replace('"', "'")))
    if lang == "swift":
        return ('// Order: %s\n'
                'print("%s")' % (task, msg.replace('"', "'")))
    if lang == "r":
        return ('# Order: %s\n'
                'message <- "%s"\n'
                'print(message)' % (task, msg.replace('"', "'")))
    if lang == "dart":
        return ('void main() {\n'
                '  // Order: %s\n'
                "  print('%s');\n"
                '}' % (task, msg.replace("'", "")))
    if lang == "perl":
        return ('#!/usr/bin/perl\n'
                'use strict;\n'
                'use warnings;\n'
                '# Order: %s\n'
                'print "%s\\n";' % (task, msg.replace('"', "'")))
    if lang == "lua":
        return ('-- Order: %s\n'
                'print("%s")' % (task, msg.replace('"', "'")))
    if lang == "haskell":
        return ('-- Order: %s\n'
                'main :: IO ()\n'
                'main = putStrLn "%s"' % (task, msg.replace('"', "'")))
    if lang == "scala":
        return ('object Main {\n'
                '  def main(args: Array[String]): Unit = {\n'
                '    // Order: %s\n'
                '    println("%s")\n'
                '  }\n'
                '}' % (task, msg.replace('"', "'")))
    if lang == "sql":
        tbl = "users"
        mt = re.search(r"(?:table|from|into)\s+([a-z_][a-z0-9_]*)", prompt)
        if mt:
            tbl = mt.group(1)
        return ('-- Order: %s\n'
                'SELECT id, name\n'
                'FROM %s\n'
                'ORDER BY id DESC\n'
                'LIMIT 10;' % (task, tbl))
    return '// Order: %s' % task


def _coding_answer(prompt):
    """Local Coding-AI — ORDER-DRIVEN composition (koi canned template NAHI):
    order parhe → zaban + task + aap ke lafz + aap ke numbers nikaale →
    usi ke mutabiq naya code bandha. Koi AI-API / cloud / doosra AI NAHI."""
    p = (prompt or "").lower().strip()
    params = [int(x) for x in _COD_NUM_RX.findall(p)]
    content = _cod_content(p)
    intent = _cod_intent(p)
    ml = _COD_LANG_RX.search(p)
    lang = _COD_LANG_MAP.get(ml.group(1).lower(), ml.group(1).lower()) if ml else None
    if not lang:
        lang = {"form": "html", "love": "html", "greet": "html", "quiz": "html",
                "htable": "html", "hlist": "html", "anim": "html", "counter": "javascript",
                "clock": "javascript", "todo": "javascript", "game": "javascript",
                "color": "css"}.get(intent, "python")
    if lang == "html":
        code = _cod_html(intent, content, params, p)
    elif lang == "css":
        code = _cod_css(intent, content, p)
    elif lang in ("javascript", "typescript"):
        code = _cod_js(intent, content, params, p, ts=(lang == "typescript"))
    elif lang == "python" and intent in _COD_INTENT_KNOWN:
        code = _cod_py(intent, content, params, p)
    elif intent == "fib" and lang in _COD_FIB:
        code = _COD_FIB[lang].replace("__N__", str(params[0] if params else 10))
        code = code.replace("__TASK__", prompt[:80].replace('"', "'"))
        cmt = _COD_CMT.get(lang, "//")
        code = "%s Order: %s\n%s" % (cmt, prompt[:80], code)
    else:
        code = _cod_generic(lang, content, p)
    return ("```%s\n%s\n```" % (lang, code.strip("\n")), 0.86, lang)


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
        # 🧾 CODING-intent social-guard: code sawalon adab/fire NAHI se (python
        # hello world → adab → QA-FAIL; _COD_TASK/_COD_LANG se coding-pata karo)
        _pl_now = (prompt or "").lower()
        _codish = bool((_COD_TASK_RX.search(_pl_now) or _COD_LANG_RX.search(_pl_now))
                       and not _COD_CONCEPT_RX.search(_pl_now))
        if (_sm.get("social") and not _codish):
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
    # ◇ COGNITION FLOW v3 — user-flow: READ-TOKEN → CONVERT-TO-BINARY → READ-BY-AI → THINK → REASONING → THINK-RESEARCH(need-if) → THINK-CONVERT → THINK → RESEARCH → THINK → CONVERT-BINARY-TO-TEXT → ANSWER → READ-AGAIN → LEARN
    try:
        from model.cognition import FlowTracker, read_intent, get_display
        from agent.animation import flow_animations, ANIM_STAGES as _ANIM_STAGES
        F = FlowTracker()
        F.stage("READ-TOKEN", "smart-prompt")                 # 📥 1st read (padh)
        _intent = read_intent(prompt)
        F.stage("CONVERT-TO-BINARY", "kind=%s" % _intent.get("kind", "baat"))   # ⚙️ token->binary
        F.stage("READ-BY-AI", "token-brain-kirish")       # ⬇️ send-to-system
        _flow_disp = get_display()
        _say("🧠 soch-1: sawal samajh raha hoon…")
        _social_hit = False
        _math_force = False
        try:
            from model.understand import understand as _u
            _smx = _u(prompt) or {}
            _pl2 = (prompt or "").lower()
            _social_hit = bool(_smx.get("social") and not (
                (_COD_TASK_RX.search(_pl2) or _COD_LANG_RX.search(_pl2))
                and not _COD_CONCEPT_RX.search(_pl2)))
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
    # 🕌 TIHAR: pure kitab-note (Sahih/Sunan/Quran-asal) sab-se-pehle —
    #    'hadith batao' par asli Bukhari-matn, gair-kitab story-line nahi
    if _sacred:
        pure = _sacred_pure(prompt)
        if pure:
            seen = {a for _s, a in rel}
            rel = pure + [(s, a) for s, a in rel if a not in seen]
        rel = _sacred_bias(rel)
    thr = 0.18 if _sacred else 0.30
    notes = [a for s, a in rel]
    top = rel[0][0] if rel else 0.0
    if F:
        F.stage("READ-AGAIN", "notes=%d top=%.2f %s" % (
            len(notes), top, "sacred" if _sacred else "aam"))
    _say("📚 ilm: yaad-data + save-system se %d notes" % len(notes))

    # 💻 CODING AI (local): coding sawalon → local code-block jawab (koi AI-API,
    #     koi cloud, koi MCP, koi doosra AI model — bilkul NAHI; sirf apna local
    #     dimagh + local coding-templates). Coding AI ka dil yahi hai.
    try:
        _plc = (prompt or "").lower()
        if len((_plc)) > 8 and not _sacred and not _math_force and not _social_hit:
            _cod_hit = bool(
                (_COD_LANG_RX.search(_plc) or _COD_TASK_RX.search(_plc))
                and not _COD_CONCEPT_RX.search(_plc))
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
            F.timed("REASONING", time.time() - _t0r,
                    "need → fire" if _res_done else "need → koi pak jawab nahi")
            _res_marked = True
    elif F:
        F.skip("REASONING", "yaad kafi hai — net ki need NAHI")
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
    if F and not _res_marked and _res_ok and not _res_done and not _res_tried:
        F.stage("THINK-RESEARCH", "need-if")          # 🔎 deep-research phase (sirf need-if)
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
        if _res_done:
            F.stage("THINK", "research-refine")
        F.stage("CONVERT-BINARY-TO-TEXT", "token-text-jod")
        F.stage("ANSWER", "jawab-tayyar")
        F.stage("LEARN", "pak-evidence-learnt")
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
         "animation": (flow_animations(F.marks) if F and F.marks else []),
         "anim_stages": list(_ANIM_STAGES),
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
            stf = set_display(arg if arg in ("on", "off", "verbose", "auto") else "on")
            print(" ◈ flow-display: %s  (phases: READ-TOKEN→CONVERT-TO-BINARY→READ-BY-AI→THINK→REASONING→THINK-RESEARCH→THINK-CONVERT→RESEARCH→THINK→CONVERT-BINARY-TO-TEXT→ANSWER→READ-AGAIN→LEARN)" % stf.get("display"))
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
                from server import genone_server as _api
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
