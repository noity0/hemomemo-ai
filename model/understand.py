"""HEMOMO TOKEN-DIMAGH - samajhne ka dil (100% local, koi API nahi).

User-qanoon: "har word token mein tut kar think karo - brain read kare -
already-flow (yaad + ilm + composer) sath kaam kare."

Parhne ka tareeqa (har sawal par):
  soch-1  PARHO    : input ko tokens mein todo - har token parho
  soch-2  SAMJHO   : sawal-lafz + domain-votes + adad + maan (r=5)
  soch-3  SOCHO    : math/formula -> yaad-flow -> ilm-khazana (token-IDF)
                     -> imandari-jawab (na pata to SAAF mana karo)
  soch-4  BOLO     : jawab + bharosa + token-naksha (meta)

Bande-ke-sawal ki izzat: jo nahi pata, usay ghooma-phira bananda-jawab
NAHI - saaf-saaf batao aur wazahat maango. (Ye hi "who is sex" wali
ghalti ka ilaaj hai: pehle dimagh ban-input nikaalta tha, ab pehle
SAMAJHTA hai.)
"""
from __future__ import annotations

import math
import os
import re
import sys
import threading
import time
from typing import Callable, List, Optional, Tuple

from model import tokenize as tk
from model.memory import EpisodicStore, KnowledgeRetrieval
from model.reasoning import safe_math

# frozen-aware ROOT (accounts.py jaisa): data EXE ke sath rahe
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)
    if not os.path.isdir(os.path.join(ROOT, "data")):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_PI = 3.141592653589793
_C_LIGHT = 299_792_458.0


def _fmt(x: float) -> str:
    """Adad ko insani shakal (poora ho to bina-point, warna 4-darjy)."""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    if abs(x) >= 1e6:
        return "%.4e" % x
    return ("%.4f" % x).rstrip("0").rstrip(".")


class TokenBrain:
    """Hemomemo ka token-dimagh: token-dar-token parhta aur sochta hai."""

    def __init__(self, generate_fn: Optional[Callable[[str], str]] = None,
                 knowledge: Optional[KnowledgeRetrieval] = None,
                 memory: Optional[EpisodicStore] = None) -> None:
        self.generate_fn = generate_fn
        self.knowledge = knowledge
        self.memory = memory
        self._idf: Optional[dict] = None
        self._lock = threading.Lock()

    # ---------- soch-2: ilm-khazane ka token-wazan (IDF) ----------
    def _build_idf(self) -> None:
        with self._lock:
            if self._idf is not None or self.knowledge is None:
                return
            df: dict = {}
            n = 0
            for _q, _a, toks in self.knowledge.pairs():
                n += 1
                for t in set(toks):
                    df[t] = df.get(t, 0) + 1
            self._idf = {t: math.log(1.0 + n / (1.0 + c)) for t, c in df.items()}
            self._idf["_n"] = n

    def _ilm(self, u: tk.Understanding, k: int = 1) -> Tuple[Optional[str], float]:
        """Token-IDF se sab-se-mutaaliq ilm (0 nahi to bharosa sath)."""
        self._build_idf()
        if not self.knowledge or not u.keys or not self._idf:
            return None, 0.0
        n = self._idf.get("_n", 1)
        best, best_sc = None, 0.0
        qkeys = set(u.keys)
        for q, a, toks in self.knowledge.pairs():
            sc = 0.0
            hit = 0
            for t in qkeys:
                if t in set(toks):
                    sc += self._idf.get(t, 0.3)
                    hit += 1
            if not hit:
                continue
            sc = sc * (hit / len(qkeys))          # kitne sawal-lafz mile
            ats = set(toks)
            for a1, b1 in u.bigrams:              # do-lafz jora bonus
                if a1 in ats and b1 in ats:
                    sc += 0.15
            if sc > best_sc:
                best, best_sc = a, sc
        if not best or best_sc < 0.34:
            return None, 0.0
        return best, min(0.98, 0.5 + best_sc / max(4.0, n ** 0.08))

    # ---------- soch-3: math + formula (deterministic - pakka sahi) ----------
    def _formula(self, u: tk.Understanding) -> Optional[str]:
        """Formula-wale sawal: circle-area / mohit / E=mc^2 (maan sath)."""
        ts = set(u.tokens)
        has = lambda *w: any(x in ts for x in w)
        v = u.variables
        nums = u.nums
        r = v.get("r", nums[0] if nums else None)
        if has("circle", "daira") and has("area", "masahat") and r is not None:
            return ("daira (circle) ka area, r = %s\n"
                    "formula: area = pi * r^2\n"
                    "hisab: %.5f * %s^2 = %s (square units)"
                    % (_fmt(r), _PI, _fmt(r), _fmt(_PI * r * r)))
        if has("circle", "daira") and has("perimeter", "mohit",
                                          "circumference") and r is not None:
            m = 2 * _PI * r
            return ("daira ka mohit (perimeter), r = %s\n"
                    "formula: mohit = 2 * pi * r\n"
                    "hisab: 2 * %.5f * %s = %s" % (_fmt(r), _PI, _fmt(r), _fmt(m)))
        if ("e=mc" in u.text.lower().replace(" ", "").replace("^", "")) or \
                (has("energy") and has("mc", "e=mc")):
            m = v.get("m", (nums[0] if nums else None))
            if m is not None:
                e = m * _C_LIGHT * _C_LIGHT
                return ("formula: E = m * c^2, m = %s kg (c = %.0f m/s)\n"
                        "hisab: %s * (%.0f)^2 = %s joule"
                        % (_fmt(m), _C_LIGHT, _fmt(m), _C_LIGHT, _fmt(e)))
        return None

    def _math(self, u: tk.Understanding) -> Optional[str]:
        """Saada arithmetic (2+2, (22+6)*8) - deterministic.

        Tareeqa: sab math-runs (digits/ops/paren) nikaalo - sab-se-lambi
        wali jo SAFE-parse ho jaye, wahi jawab. Kam-az-kam 2 adad + 1
        operator ho (warna 'namaz 5 waqt' jaisi baat math na bane)."""
        best, bval = None, None
        for cand in re.findall(r"[\d\(][\d\s\+\-\*x×÷/^().]*[\d\)]", u.text):
            c = cand.strip()
            if not re.search(r"[\+\-\*x×÷/^]", c):
                continue                     # sirf adad - math nahi
            if len(re.findall(r"\d+", c)) < 2:
                continue                     # ek-adad - faltu
            val = safe_math(c)
            if val is not None and (best is None or len(c) > len(best)):
                best, bval = c, val
        if best is None:
            return None
        return "hisab: %s = %s" % (best.replace("**", "^"), bval)

    # ---------- soch-3: yaad-flow (already-flow: naam yaad waghera) ----------
    _NAME_RX = re.compile(
        r"(?:naam|name)\s*(?:hai|he|:|=)?\s*([A-Za-z][A-Za-z0-9_ ]{1,30}?)"
        r"\s*(?:hai|he|raakh?o|rakhna|remember)?\s*$")

    def _yaad(self, u: tk.Understanding) -> Optional[str]:
        ts = set(u.tokens)
        wants_save = bool({"yaad", "remember", "rakho", "rakhna", "save"} & ts)
        asks_name = (("naam" in ts or "name" in ts)
                     and (u.qw or {"kya", "what", "kaun"} & ts))
        # 1) naam yaad karwana: "mera naam Ahmed hai / Ahmed yaad rakho"
        if wants_save or ("naam" in ts or "name" in ts):
            m = self._NAME_RX.search(u.text)
            if m and (wants_save or "mera" in ts or "meri" in ts or "my" in ts):
                naam = m.group(1).strip().title()
                naam = re.sub(r"\s*(Yaad|Remember|Rakho|Rakhna|Hai|He)$", "",
                              naam, flags=re.I).strip() or naam
                if self.memory is not None:
                    self.memory.remember(u.text, "user_naam=" + naam, tag="yaad")
                return ("yaad liya - aap ka naam %s hai. "
                        "Main har baat yaad rakhta hoon (aap ke PC par)."
                        % naam)
            # 2) naam poochna: "mera naam kya hai?"
            if self.memory is not None and u.qw:
                facts = self.memory.facts("user_naam=")
                if facts:
                    return ("aap ne bataya tha - aap ka naam %s hai. "
                            "(yaad-dasht se, aap ke PC par mehfooz)"
                            % facts[0])
                if {"naam", "name"} & ts and {"mera", "meri", "my"} & ts:
                    return ("aap ne apna naam abhi tak bataya nahi - "
                            "bata dein, main yaad rakh loon ga.")
        return None

    # ---------- soch-3: pehchaan (kaun ho / naam tumhara) ----------
    _ID_RX = re.compile(r"(kaun\s+ho|kon\s+ho|your\s+name|tumhara\s+naam|"
                        r"aap\s+kaun|aap\s+ka\s+naam|who\s+are\s+you|"
                        "tumhara naam kya|aapka naam kya)", re.I)

    def _identity(self, u: tk.Understanding) -> Optional[str]:
        if self._ID_RX.search(u.text):
            return ("Main Hemomemo AI hoon - HMHS (Hafiz Muhammed Huzaifa "
                    "Shamim) ki banayi hui 100% local AI. Na koi API, na "
                    "cloud - mera apna dimagh (token-soch + yaad + ilm) "
                    "isi PC par chalta hai.")
        return None

    # ---------- poora soch-loop ----------
    def read(self, prompt: str) -> tk.Understanding:
        """soch-1 + soch-2: token-dar-token parhna."""
        return tk.understand(prompt)

    def respond(self, prompt: str) -> Tuple[str, dict]:
        u = self.read(prompt)
        soch = ["token-parha: %d tokens" % len(u.tokens)]
        if not u.tokens:
            return ("kuch kaha? main sun raha hoon - thora wazah likhein.",
                    {"source": "token-dimagh", "bharosa": 0.6, "soch": soch})
        soch.append("samajh: sawal=%s domain=%s" %
                    (u.qw or "-", u.intents or "-"))

        # 1) math/formula (token-evidence: digits/operators/domain-votes)
        f = self._formula(u)
        if f:
            soch.append("formula-mila: pakka hisab (deterministic)")
            return f, {"source": "formula", "bharosa": 0.99, "soch": soch,
                       "tokens": len(u.tokens)}
        m = self._math(u)
        if m:
            soch.append("arithmetic: deterministic hisab")
            return m, {"source": "math", "bharosa": 0.99, "soch": soch,
                       "tokens": len(u.tokens)}

        # 2) pehchaan
        ide = self._identity(u)
        if ide:
            return ide, {"source": "pehchaan", "bharosa": 0.95,
                         "soch": soch, "tokens": len(u.tokens)}

        # 3) yaad-flow (naam waghera - already-flow sath)
        y = self._yaad(u)
        if y:
            soch.append("yaad-dasht: flow sath chala")
            return y, {"source": "yaad", "bharosa": 0.93, "soch": soch,
                       "tokens": len(u.tokens)}

        # 4) ilm-khazana (token-IDF)
        a, conf = self._ilm(u)
        if a:
            soch.append("ilm-mila: token-wazan se mutaliq jawab")
            return a[:900], {"source": "ilm", "bharosa": round(conf, 2),
                             "soch": soch, "tokens": len(u.tokens)}

        # 5) imandari-jawab: sawal samjha, ilm nahi - SAAF batao
        #    (ban-input dump NahiN - yahi asli samajh hai)
        topic = " ".join(u.keys[:4]) if u.keys else u.text[:40]
        if u.qw:
            soch.append("ilm-nahi-mila: imandari jawab (ban-input nahi)")
            return ("aap ne poocha: \"%s\" (topic: %s). "
                    "Mere ilm-khazane mein iska pakka jawab abhi nahi - "
                    "jhoot bol kar banana mera tareeqa nahi. Kya aap thora "
                    "wazah bata sakte hain? Ya is se mutaliq koi aur sawal?"
                    % (u.text[:120], topic)), \
                   {"source": "imandari", "bharosa": 0.55, "soch": soch,
                    "tokens": len(u.tokens)}

        # 6) composer-fallback (apna LSTM-dimagh - already-flow ka aakhri hissa)
        if self.generate_fn is not None:
            try:
                out = (self.generate_fn(u.text) or "").strip()
                if out:
                    soch.append("composer: apna dimagh banaya")
                    return out[:900], {"source": "composer", "bharosa": 0.7,
                                       "soch": soch, "tokens": len(u.tokens)}
            except Exception:
                pass
        soch.append("kuch pakka nahi - imandari mana")
        return ("is sawal par mujhe abhi pakka ilm nahi - thora wazah "
                "poochein? Main sach hi bolta hoon.",
                {"source": "imandari", "bharosa": 0.5,
                 "soch": soch, "tokens": len(u.tokens)})

    def respond_with_memory(self, prompt: str, tag: str = "chat") -> str:
        text, _m = self.respond(prompt)
        if self.memory is not None and text:
            try:
                self.memory.remember(prompt, text, tag=tag)
            except Exception:
                pass
        return text


# ------------------------------------------------------------ shared-dimagh
_SHARED: dict = {"brain": None}


def default_token_chat() -> TokenBrain:
    """Ek hi shared dimagh (server + app dono ke liye) - lazy, thread-safe.

    Composer-fallback ke liye model.generate.chat_once IMPORT hota hai -
    file ko chhua NAHI jata (L3-seal salam)."""
    if _SHARED["brain"] is not None:
        return _SHARED["brain"]

    def composer(prompt: str) -> str:
        try:
            from model.generate import chat_once
            out = chat_once(prompt)
            return out[0] if isinstance(out, tuple) else out
        except Exception:
            return ""

    know = KnowledgeRetrieval(os.path.join(ROOT, "data", "corpus_big"))
    mem = EpisodicStore(os.path.join(ROOT, "data"))
    _SHARED["brain"] = TokenBrain(generate_fn=composer,
                                  knowledge=know, memory=mem)
    return _SHARED["brain"]
