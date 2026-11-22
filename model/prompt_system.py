# -*- coding: utf-8 -*-
"""prompt_system.py - Hemomemo CHAT-YAAD + CODE-SAMAJH PROMPT-SYSTEM
====================================================================
(100% local — koi AI-API nahi; sirf prompt-imiarti rules)

USER-HUKUM (15-Nov):
  1) 🗒 CHAT-YAAD: usi chat ke UPAR-WALE SARE messages AI-ki memory me rahen;
     agla jawab dene se pehle AI unhe parhta hai.
  2) 🎯 90%-PRIORITY: jawab ka neze-haqq hamesha AKHRI user-message hai
     (jo sawal abhi poocha gaya); pichli baat sirf 10% sandarabh —
     "ye/wo/mera/wala" jaise ishare aur rawabat samajhne ke liye.
  3) 🧩 CODE-SAMAJH: coding-hukum par system-prompt lagta hai — hukum ko
     heading/text na banaya jaye, ASLI CODE bana-kar chala-kar dikhaya jaye,
     aur coding-error aye to AI KHUD theek-kar-kay dobara chalaye.
"""
import re

_MAX_TURNS = 30          # kitne pichle turns yaad me rakhe jayen
_MAX_TURN_CHARS = 240    # har turn ki shakal chat-yaad me
_MAX_CTX = 5000          # poore yaad-preamble ki hadd

_YAAD_HEAD = ("[CHAT-YAAD] isi chat ke pichle messages (purana -> naya); "
              "ye sirf 10% SANDARABH hai:\n")

_YAAD_RULES = (
    "\n\n[QANOON] (1) Jawab ka 90% markaz AKHRI SAWAL hai — jo sab-se-"
    "neeche/taaza poocha gaya; usi ka jawab do.\n"
    "(2) Pichli baat sirf ishare-samajhne ke liye hai (ye/wo/mera/us-wala/"
    "pichla) — purana jawab dobara na dohrao.\n"
    "(3) Agar akhri sawal 'aur / phir / wahi / continue / next / usko bhi' "
    "jaisa ho to pichli-baat ko aage-barhao.\n"
    "(4) Agar akhri sawal NAYA-topic ho to purani-baat chhorkar naye-sawal "
    "par jawab do.\n"
    "[CHAT-YAAD-KHATAM]\n"
)

_CODE_RX = re.compile(
    r"(?i)(?:^|\b)(code|python|program|script|coding|function|def |bug|"
    r"error|ghalti|debug|compile|py file|\.py\b|code fix|error fix|"
    r"factorial|table\s+of\s*\d|square\s+of\s*\d|cube\s+of\s*\d)")

_CODE_SYSTEM = (
    "[CODE-SYSTEM] Ye CODING-hukum hai — ye rules follow karo:\n"
    "- Hukum ko HEADING/naqli-text na banao: ASLI CODE banao.\n"
    "- Code hamesha ```python code-block me do (1-line samajh + code + "
    "chala-kar ASLI output).\n"
    "- Code me try/except rakho; chalne-wala chota-sachcha code do.\n"
    "- Coding-ERROR aye to KHUD theek karo (fancy-quotes -> \" '\", "
    "unicode-digits -> 0-9, pasted line-numbers hatao) aur DOBARA chalao — "
    "jawab me theek-shuda code + nateeja do.\n"
    "- 100% local raasta (no AI-API) — code_exec ke sath.\n"
    "[CODE-SYSTEM-KHATAM]\n"
)

_CONT_RX = re.compile(
    r"(?i)^\s*(?:aur|phir|wahi|wo\s+(?:wala|wali|bhi)|us\s+(?:ko|se|wale)|"
    r"continue|next|or\s+(?:wo|phir)|uskay\s+baad|agey\s+barho|"
    r"mazeed|thora\s+aur)\b")


def is_continuation(text):
    """'aur wo wala bhi' jaisa sawal (pichli-baat-ka aage) — clarification
    ki zaroorat NAHI; chat-yaad se jawab hoga."""
    return bool(_CONT_RX.match((text or "").strip()))


def is_code_request(text):
    """Kya ye message coding-masla hai? (prompt-system ka trigger)"""
    t = (text or "").strip()
    if not t:
        return False
    if _CODE_RX.search(t):
        return True
    # pichla-turn me code-block ho aur ye-sawal us-par continuation ho
    return False


def code_system_prompt(text):
    """Coding-hukum par [CODE-SYSTEM] rules (warna khali-string)."""
    return _CODE_SYSTEM if is_code_request(text) else ""


def build_chat_context(hist, current, max_turns=_MAX_TURNS):
    """Chat-yaad preamble banao (100% local).

    hist: [{"who": "user"/"ai", "text": ...}, ...] (purana -> naya)
    current: abhi-ka user-sawal (hist ka aakhri user-turn isi se milta hai)
    -> str (khali agar yaad ke-qabil kuch nahi)
    """
    turns = []
    for t in (hist or []):
        who = (t.get("who") or "").strip()
        txt = (t.get("text") or "").strip()
        if who in ("user", "ai") and txt:
            turns.append((who, txt))
    # aakhri user-turn = current sawal hi hai — wo YAAD me nahi, 90%-core me
    while turns and turns[-1][0] == "user" and turns[-1][1] == (current or "").strip():
        turns.pop()
        break
    # sirf current-sawal tha (koi pichli-baat nahi) -> yaad khali
    if not turns:
        return code_system_prompt(current)
    turns = turns[-max_turns:]
    lines = []
    for who, txt in turns:
        if len(txt) > _MAX_TURN_CHARS:
            txt = txt[:237].rstrip() + "..."
        lines.append(("User: " if who == "user" else "AI:   ") + txt)
    yaad = _YAAD_HEAD + "\n".join(lines) + _YAAD_RULES
    csys = code_system_prompt(current)
    if csys:
        yaad += "\n" + csys
    if len(yaad) > _MAX_CTX:
        yaad = yaad[-_MAX_CTX:]
    return yaad.strip()


# ----------------------------------------------------------------------
# 🎯 90%-CORE (prompt-samajh fix, 16-Nov): intent/math/formula sirf AKHRI
#    user-sawal par chalein — [CHAT-YAAD]/[CODE-SYSTEM] preamble aur
#    frontolobe-wrapper KABHI intent me na ghusen.
#    (Asli-bug: YAAD-preamble poora-blob ke sath intent me chala jata tha —
#    pichli-baat ke numbers (m = 10, k = 6) ne 'details about github repo
#    noity0' ko purana Spring T = 8.11 jawab dikha diya tha.)
# ----------------------------------------------------------------------
_YAAD_END = "[CHAT-YAAD-KHATAM]"
_CODE_END = "[CODE-SYSTEM-KHATAM]"

_USER_REQ_RX = re.compile(
    r"(?i)^\s*user\s+is\s+requesting\s*:\s*(.*?)(?:\.\s*context\s*:|"
    r"\.\s*key\s+concepts\s*:|\s*$)", re.S)


def core_intent_text(text):
    """Blob se sirf 90%-core (akhri user-sawal) nikalo (100% local).

    • [CHAT-YAAD] … [CHAT-YAAD-KHATAM] preamble hatao
    • [CODE-SYSTEM] … [CODE-SYSTEM-KHATAM] hatao
    • frontolobe-wrapper 'User is requesting: X. Context: …' → X
    • koi marker nahi (khara-sawal) → jaisa-hai-waisa wapas
    """
    t = (text or "").strip()
    if not t:
        return ""
    low = t.lower()
    if _YAAD_END.lower() in low:
        i = low.rfind(_YAAD_END.lower())
        t = t[i + len(_YAAD_END):].strip()
        low = t.lower()
    if _CODE_END.lower() in low:
        i = low.rfind(_CODE_END.lower())
        t = t[i + len(_CODE_END):].strip()
    m = _USER_REQ_RX.match(t)
    if m and (m.group(1) or "").strip():
        t = m.group(1).strip()
    return t.strip()


# ----------------------------------------------------------------------
# 🏠 SELF-KNOWLEDGE: apna GitHub-repo (noity0 = owner-username) —
#    'details about github repo noity0' jaisa sawal formula/unknown/research
#    NAHI — seedha sacha owner-jawab (100% local facts).
# ----------------------------------------------------------------------
_SELF_REPO_RX = re.compile(
    r"(?i)(?:\b(?:noity0|hemomemo)\b[^?\n]{0,80}?\b(?:github|repo|repository)\b"
    r"|\b(?:github|repo|repository)\b[^?\n]{0,80}?\b(?:noity0|hemomemo)\b"
    r"|\b(?:mera|meri|apna|apni|hamara|hamari|tumhara|tumhari|your|aap\s*ka)\s+"
    r"(?:github\s+)?repo\b)")

_SELF_REPO_REPLY = (
    "Ye mera apna GitHub repo hai: github.com/noity0/hemomemo-ai "
    "(username: noity0) — isi app (Hemomemo AI) ka poora local code isi me "
    "hai: dimagh (NumPy), chat, math/formula library, Coding-AI, GameBot, "
    "ilm-corpus, yaad-dasht aur apni local API (127.0.0.1:8790). "
    "100% local — koi cloud/AI-API nahi. Install, code ya features ke bare "
    "me kuch aur poochna ho to batao.")


def is_self_repo_question(text):
    """Kya ye sawal MERE apne GitHub-repo ke bare me hai?"""
    return bool(_SELF_REPO_RX.search((text or "").lower()))


def self_repo_reply():
    """Apne-repo ka sacha jawab (owner-facts, koi internet/API nahi)."""
    return _SELF_REPO_REPLY
