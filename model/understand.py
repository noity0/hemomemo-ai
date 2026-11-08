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

# ---- code-dimagh: code-irada + zaban + message (token-evidence) ----
# NOTE: 'c++' ke aakhir mein \b NAHI lagta ('+' word-char nahi) - is liye
# aage-lookahead (?![+\w]) hai: "c++" END/niza-par khatam ho jaye.
_CODE_REQ_RX = re.compile(r"\b(code|program|likho|banao|likh|bana|write|"
                          r"make|build|create)\b", re.I)
_CODE_LANG_RX = re.compile(r"\b(c\+\+|cpp|python|py)(?![+\w])", re.I)
# "code <message> in <lang>"  (English rasta - zaban aakhir me)
_CODE_EN_RX = re.compile(r"\bcode\s+(.+?)\s+(?:in|for)\s+"
                         r"([a-z][a-z0-9+\-#]*)\s*$", re.I)
# "<lang> (me|mein|par) <message> (ka|ki)? code"  (Roman-Urdu rasta)
_CODE_UR_RX = re.compile(r"([a-z][a-z0-9+\-#]*)\s*(?:me|mein|par)\s+"
                         r"(.+?)\s*(?:ka|ki)?\s*(?:code|program)\b", re.I)
# "make/build/create <cheez> by/in/with <lang>"  (MAKE-rasta - webpage waghera)
_CODE_MAKE_RX = re.compile(
    r"\b(?:make|build|create|banao|bana|likho|write)\s+(.+?)\s+"
    r"(?:by|in|with|se|me|mein)\s+([a-z][a-z0-9+\-#]*)\s*$", re.I)
# make-raste me DIKHANE-wala-lafz nikaalne ke liye (hukum/siffatein nikalo)
_ANIM_STRIP = frozenset([
    "a", "an", "the", "ek", "beautiful", "beutiful", "beautifull",
    "sundar", "pyara", "pyari", "nice", "simple", "chhota", "bara",
    "animated", "animation", "page", "webpage", "website", "wali", "wala",
])
_CODE_FILLER = re.compile(r"^(?:a|an|the|ek)\s+|\s*[\?\.!]+$", re.I)

# ---- code-dimagh: ZABAN-KHAZANA (sab bari zabanen - print-program) ----
# alias -> canonical (token-scan se pakra jata hai: 'c++'/'c#'/'f#' bhi)
_CODE_LANGS = {
    "python": "python", "py": "python",
    "c++": "c++", "cpp": "c++",
    "c": "c",
    "c#": "c#", "csharp": "c#", "cs": "c#",
    "java": "java",
    "javascript": "javascript", "js": "javascript",
    "node": "javascript", "nodejs": "javascript",
    "typescript": "typescript", "ts": "typescript",
    "go": "go", "golang": "go",
    "rust": "rust", "rs": "rust",
    "php": "php",
    "ruby": "ruby", "rb": "ruby",
    "swift": "swift",
    "kotlin": "kotlin", "kt": "kotlin",
    "dart": "dart",
    "lua": "lua",
    "perl": "perl",
    "bash": "bash", "sh": "bash", "shell": "bash", "zsh": "bash",
    "powershell": "powershell", "ps1": "powershell",
    "r": "r",
    "matlab": "matlab",
    "sql": "sql",
    "html": "html",
    "css": "css",
    "json": "json",
    "yaml": "yaml",
    "scala": "scala",
    "haskell": "haskell", "hs": "haskell",
    "f#": "f#", "fsharp": "f#",
    "julia": "julia", "jl": "julia",
    "fortran": "fortran",
    "pascal": "pascal",
    "basic": "basic", "qbasic": "basic",
    "vb": "vb", "basic.net": "vb",
    "zig": "zig",
    "nim": "nim",
    "crystal": "crystal",
    "elixir": "elixir",
    "clojure": "clojure", "clj": "clojure",
    "erlang": "erlang",
    "ocaml": "ocaml",
    "d": "d",
    "asm": "asm", "assembly": "asm", "nasm": "asm",
    "cobol": "cobol",
    "tcl": "tcl",
    "prolog": "prolog",
    "lisp": "lisp",
    "scheme": "scheme",
    "racket": "racket",
    "objective-c": "objc", "objc": "objc",
}
_CODE_TOK_RX = re.compile(r"[a-zA-Z][a-zA-Z0-9+\-#]*")

# print-program template (python %s = message; literal % ho to %% likha hai)
_PRINT_TPL = {
    "python": 'print("%s")',
    "c++": '#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "%s" << endl;\n    return 0;\n}',
    "c": '#include <stdio.h>\n\nint main(void) {\n    printf("%s\\n");\n    return 0;\n}',
    "c#": 'using System;\n\nclass Program {\n    static void Main() {\n        Console.WriteLine("%s");\n    }\n}',
    "java": 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("%s");\n    }\n}',
    "javascript": 'console.log("%s");',
    "typescript": 'const msg: string = "%s";\nconsole.log(msg);',
    "go": 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("%s")\n}',
    "rust": 'fn main() {\n    println!("%s");\n}',
    "php": '<?php\necho "%s";\n',
    "ruby": 'puts "%s"',
    "swift": 'print("%s")',
    "kotlin": 'fun main() {\n    println("%s")\n}',
    "dart": 'void main() {\n    print("%s");\n}',
    "lua": 'print("%s")',
    "perl": 'print "%s\\n";',
    "bash": '#!/bin/bash\necho "%s"',
    "powershell": 'Write-Output "%s"',
    "r": 'cat("%s\\n")',
    "matlab": "disp('%s')",
    "sql": "SELECT '%s' AS message;",
    "html": '<!DOCTYPE html>\n<html>\n<head>\n  <meta charset="utf-8">\n  <title>Paighaam</title>\n</head>\n<body>\n  <h1>%s</h1>\n</body>\n</html>',
    # chalti-hui (animated) page - CSS keyframes, 100% local, koi CDN nahi
    "html-anim": '<!DOCTYPE html>\n<html>\n<head>\n  <meta charset="utf-8">\n  <title>Animated</title>\n  <style>\n    body { margin:0; min-height:100vh; display:flex; align-items:center;\n           justify-content:center; background:#0b1d16; overflow:hidden; }\n    .hemo { font-family: Arial, sans-serif; font-size:4rem; font-weight:bold;\n            color:#2bd47a; animation: hemo-harkat 2s ease-in-out infinite alternate; }\n    @keyframes hemo-harkat {\n      0%%   { transform: scale(1) rotate(-3deg); opacity:.55; }\n      50%%  { transform: scale(1.18) rotate(3deg); opacity:1;\n              text-shadow: 0 0 30px #2bd47a, 0 0 60px #2bd47a; }\n      100%% { transform: scale(1) rotate(-3deg); opacity:.55; }\n    }\n  </style>\n</head>\n<body>\n  <div class="hemo">%s</div>\n</body>\n</html>',
    "css": '/* CSS - message dikhane ka tareeqa */\nbody::after {\n  content: "%s";\n  font-size: 2rem;\n  color: teal;\n}',
    "json": '{\n  "message": "%s"\n}',
    "yaml": 'message: "%s"',
    "scala": 'object Main extends App {\n  println("%s")\n}',
    "haskell": 'main :: IO ()\nmain = putStrLn "%s"',
    "f#": 'printfn "%s"',
    "julia": 'println("%s")',
    "fortran": 'program hello\n    print *, "%s"\nend program hello',
    "pascal": "program Hello;\nbegin\n  writeln('%s');\nend.",
    "basic": '10 PRINT "%s"\n20 END',
    "vb": 'Module Program\n    Sub Main()\n        Console.WriteLine("%s")\n    End Sub\nEnd Module',
    "zig": 'const std = @import("std");\n\npub fn main() void {\n    std.debug.print("%s\\n", .{});\n}',
    "nim": 'echo "%s"',
    "crystal": 'puts "%s"',
    "elixir": 'IO.puts("%s")',
    "clojure": '(println "%s")',
    "erlang": '-module(main).\n-export([main/0]).\n\nmain() ->\n    io:format("%s~n").',
    "ocaml": 'let () = print_endline "%s";;',
    "d": 'import std.stdio;\n\nvoid main() {\n    writeln("%s");\n}',
    "asm": 'section .data\n    msg db "%s", 10\n    len equ $ - msg\n\nsection .text\n    global _start\n\n_start:\n    mov rax, 1\n    mov rdi, 1\n    mov rsi, msg\n    mov rdx, len\n    syscall\n\n    mov rax, 60\n    xor rdi, rdi\n    syscall',
    "cobol": 'IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.\nPROCEDURE DIVISION.\n    DISPLAY "%s".\n    STOP RUN.',
    "tcl": 'puts "%s"',
    "prolog": ':- initialization(main).\nmain :- write("%s"), nl.',
    "lisp": '(princ "%s")\n(terpri)',
    "scheme": '(display "%s")\n(newline)',
    "racket": '#lang racket\n(displayln "%s")',
    "objc": '#import <Foundation/Foundation.h>\n\nint main(void) {\n    @autoreleasepool {\n        NSLog(@"%s");\n    }\n    return 0;\n}',
}
_FENCE = {"c++": "cpp", "c#": "csharp", "f#": "fsharp", "asm": "nasm",
          "objective-c": "objc", "vb": "vb"}


def _code_esc(msg: str, lang: str) -> str:
    """Message ko us zaban ke qavaid se saaf karo (quote/backslash waghera)."""
    if lang in ("matlab", "pascal", "sql"):
        return msg.replace("'", "''")
    if lang == "html":
        return (msg.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;"))
    if lang == "erlang":
        return msg.replace("\\", "\\\\").replace('"', '\\"').replace("~", "~~")
    if lang == "perl":
        return (msg.replace("\\", "\\\\").replace('"', '\\"')
                .replace("$", "\\$").replace("@", "\\@"))
    if lang == "bash":
        return (msg.replace("\\", "\\\\").replace('"', '\\"')
                .replace("$", "\\$").replace("`", "\\`"))
    return msg.replace("\\", "\\\\").replace('"', '\\"')

# kaam-wale lafz (sawal-grammer) - ilm-nayab-chunni me ye HISAAB nahi:
# 'namaz KITNI farz hai' me 'kitni' nayab NAHI, 'namaz' asal matlab hai.
_FUNC_WORDS = frozenset([
    "kitni", "kitna", "kitne", "kaise", "kaese", "kyun", "kyu", "kyon",
    "kab", "kahan", "kahan", "kis", "kiski", "kisko", "iska", "uska",
    "hai", "hain", "ho", "hu", "tha", "the", "ka", "ki", "ke", "ko",
    "me", "mein", "par", "se", "batao", "bata", "likhte", "likhna",
    "likho", "likh", "chahiye", "waghera", "wala", "wali", "bhi", "to",
    "the", "a", "an", "of", "for", "in", "on", "with", "how", "what",
    "write", "tell", "please", "likhein", "likhiye", "likhdo", "bataiye",
    # sawal-MANGNE-wale umoomi lafz ('ka formula?' = manga hua, topic nahi)
    "formula", "matlab", "raaz", "meaning", "definition", "number",
    "numbers", "steps", "step", "example", "examples", "types", "list",
    "explain", "difference", "between", "about", "kya", "koi",
    "method", "methods", "code", "codes", "program",
    # umoomi English/Roman bharne-wale (theme NAHI — greeting 'hi there',
    # 'hello how are you' ko dawaat-path me rehne do):
    "there", "this", "that", "their", "they", "them", "the", "and", "or",
    "so", "than", "then", "also", "just", "very", "now", "here", "well",
    "you", "your", "yours", "u", "ur", "i", "im", "am", "are", "isn", "is",
    "was", "were", "be", "been", "my", "me", "it", "its", "he", "she",
    "his", "her", "we", "us", "our", "oh", "ok", "okay", "yes", "yeah",
    "no", "nope", "sure", "hmm", "yeh", "nahin", "nahi", "haan", "han",
])

# DAWAAT-qanoon (rule-4): salam/hi/hii/hiii/hey/hello jese istiqbali lafz
# HAMESHA composer (Salam!) se jawab — na ilm-khazana, na imandari.
# (thint-lafz bhi: hii/hiii/helo — regex se pakde - user-screenshot-bug fix)
_DAWAAT_WORDS = frozenset([
    "salam", "salaam", "assalam", "assalamo", "asalam", "asslam", "slaam",
    "alaikum", "walaikum", "aoa", "adab", "slam",
    "hello", "helo", "hi", "hey", "hy",
    "good", "morning", "evening", "night", "afternoon",
])
_DAWAAT_RX = re.compile(
    r"(?i)^(a+s?a+l+a+m+o*(a+l+a+i+k+u+m+)?|s+a+l+a+a+m+"
    r"|hi+|hey+|h+y+|h+e+l+o+|h+e+l+l+o+|aoa|adab)$")

# SAMAJH social-intent (hiiii/byeee/okkk/shukriya hahaha) - elongation-fold
_SOCIAL_CALL = {
    "farewell": re.compile(
        r"(?i)^(b+y+e+|bye+|goodbye|gn|g+n|allah|hafiz|khuda|fi+|farewell|"
        r"das?dalanah)$"),
    "thanks": re.compile(
        r"(?i)^(thank+|thanks+|shukriya+|shukri|jazak|jazakallah|tnx|thx|"
        r"mehrbani)$"),
    "laugh": re.compile(r"(?i)^((h+a+)+|(h+e+)+|(h+i+)+|l+o+l+|lmao|rofl)$"),
    "ack": re.compile(r"(?i)^(o+k+|ok+|okay+|kk+|right|dahana|haan|han|"
                      r"ji|theek|thik|acha|achha|accha|fine|sahi)$"),
    "no": re.compile(r"(?i)^(n+o+|nope+|nahi|nahin|nahii|n+a+|na|nai|"
                     r"karab|kharab)$"),
    "yes": re.compile(r"(?i)^(y+e+s+|yeah+|yup+|yus|haan|han|ji|bilkul|"
                      r"zaro+r|zaroor)$"),
}
_SOCIAL_QWORDS = frozenset([
    "kya", "kyun", "kab", "kahan", "kaun", "kitna", "kitne", "kitni",
    "kaise", "kaisay", "why", "what", "who", "where", "when", "how",
    "which", "explain", "batao", "bata", "sunao", "likho", "likh",
    "karo", "chalao", "banana", "banao", "tu", "tum",
])


def _is_dawaat_keys(keys):
    """Kya ye keys dawaat (salam/hi) ke bilkul pure-set hain? rule-4.

    FUNC-lafz (hai/please/there...) pehle filter — 'hi there'/'hello how'
    bhi dawaat hai; 'gjjfg' dawaat NAHI."""
    ks = [t for t in keys if t not in _FUNC_WORDS]
    if not ks:
        return False
    return all((t in _DAWAAT_WORDS) or _DAWAAT_RX.match(t) for t in ks)


def understand(text):
    """SAMAJH: social-intent detector (model.autonomous + chat_once se
    call hota hai - YEHI import 'from model.understand import understand').

    Typo/elongation input (hii/hiiii/helo/byeeee/okkk/hahaha) ko fold kar
    social-intent nikaalta hai: greet/farewell/thanks/laugh/ack/yes/no.
    HATYAR: sawal-word/'?' ho to social HAI Nahi (wo asli sawal hai).
    Koi AI-API nahi — pure local fold-logic. Dict-lautata hai ({} = koi
    social nahi — fast-path kho-ri khud chhod degi)."""
    t = (text or "").strip()
    if not t or "?" in t:
        return {}
    toks = re.findall(r"[a-zA-Z]+", t.lower())
    if not toks or len(toks) > 4:
        return {}
    if any(w in _SOCIAL_QWORDS for w in toks):
        return {}
    bases, social, fixes = [], None, []
    for w in toks:
        if _DAWAAT_RX.match(w) or w in _DAWAAT_WORDS:
            if social is None:
                social = "greet"
            bases.append("greet:" + w)
            continue
        matched = False
        for name, rx in _SOCIAL_CALL.items():
            if rx.match(w):
                if social is None:
                    social = name
                bases.append(name + ":" + w)
                matched = True
                break
        if not matched:
            bases.append("other:" + w)
    if not social:
        return {}
    return {"norm": " ".join(toks), "social": social, "bases": bases,
            "fixes": fixes}


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
        """Token-IDF se sab-se-mutaaliq ilm (0 nahi to bharosa sath).

        Imandari-qanoon (nonsense-ilaaj) - do token-hisab:
        1) AKS-ADAD matlab-lafz corpus me hi NAHI (unseen) -> sawal
           khazane-se-bahar hai -> ilm NAHI (imandari sach bolegi).
        2) warna sab-se-nayab DEKHA-HUA lafz us pair me milna zaroori -
           'xenolith velocity ka formula' sirf 'formula' (9.72) se
           black-hole/TNT pair na utha le. Nayab-dekha-lafz nahi mila
           -> wo faltu-milaap hai -> ilm NAHI."""
        self._build_idf()
        if not self.knowledge or not u.keys or not self._idf:
            return None, 0.0
        # dawaat (salam/hi/hii/hello) ilm-khazana nahi - composer hi theek
        if _is_dawaat_keys(u.keys):
            return None, 0.0
        n = self._idf.get("_n", 1)
        best, best_sc = None, 0.0
        qkeys = set(u.keys) - _FUNC_WORDS        # matlab-wale hi rakh
        if not qkeys:
            return None, 0.0
        # adad-only guard ('5(5)', '50 100'): sirf adad/alamaat — matlab-
        # lafz NahiN — khazana-milaap (Pokemon-junk) KABHI nahi
        # (user-screenshot bug fix)
        if not any(any(c.isalpha() for c in t) for t in qkeys):
            return None, 0.0
        seen_k = [t for t in qkeys if t in self._idf]
        unseen_k = [t for t in qkeys if t not in self._idf]
        if len(unseen_k) > len(seen_k):          # qanoon-1: aks-adad unseen
            return None, 0.0
        # qanoon-5: sawal jis-bare me hai (pehla matlab-lafz) wo lafz hi
        # khazane me na ho -> jawab dena hi bekaar/jhoot hai (imandari).
        content_k = [t for t in u.keys if t not in _FUNC_WORDS]
        if content_k and content_k[0] not in self._idf:
            return None, 0.0
        rare = max(seen_k, key=lambda t: self._idf[t]) if seen_k else None
        for q, a, toks in self.knowledge.pairs():
            ts = set(toks)
            if rare is not None and rare not in ts:   # qanoon-2: nayab-lafz
                continue
            # qanoon-3: koi-unseen-lafz ho to DEKHA-hue SAB lafz pair me
            # ('quantum braid theory' sirf 'braid' wale pair na utha le)
            if unseen_k and not set(seen_k) <= ts:
                continue
            sc = 0.0
            hit = 0
            for t in qkeys:
                if t in ts:
                    sc += self._idf.get(t, 0.3)
                    hit += 1
            if not hit:
                continue
            sc = sc * (hit / len(qkeys))          # kitne sawal-lafz mile
            for a1, b1 in u.bigrams:              # do-lafz jora bonus
                if a1 in ts and b1 in ts:
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

    # ---------- soch-3: code-dimagh (token se irada+zaban+message) ----------
    @staticmethod
    def _code_msg(text: str) -> Optional[Tuple[str, str]]:
        """'code <message> in c++' / 'python me <message> ka code' ->
        (message, lang) - na mila to None; mangi-hui-zaban khazane me
        na ho to ("?", zaban)."""
        low = " ".join((text or "").split()).lower()
        low = low.replace("visual basic", "vb").replace("objective c", "objc")
        m = _CODE_EN_RX.search(low)
        if m:
            lang = _CODE_LANGS.get(m.group(2))
            if not lang:
                return ("?", m.group(2))
            got = (" ".join(m.group(1).split()), lang)
        else:
            mk = _CODE_MAKE_RX.search(low)
            if mk:
                lang = _CODE_LANGS.get(mk.group(2))
                if not lang:
                    return ("?", mk.group(2))
                got = (" ".join(mk.group(1).split()), lang)
            else:
                m2 = _CODE_UR_RX.search(low)
                if not m2:
                    return None
                toks = [t for t in _CODE_TOK_RX.findall(low)
                        if t in _CODE_LANGS]
                if not toks:
                    return None
                got = (" ".join(m2.group(2).split()), _CODE_LANGS[toks[-1]])
        msg, lang = got
        msg = _CODE_FILLER.sub("", msg).strip()
        if not msg:
            return None
        return msg, lang

    def _code(self, u: tk.Understanding) -> Optional[str]:
        """Code-mangay gaye to ASLI chhota code banao (koi jhoot nahi).

        Token-flow: 'code/likho/program' ka irada -> zaban (45+ zabanen:
        c++/c#/java/python/rust/go/html/sql/asm/...) -> message. Print-
        template deterministic banta hai; zaban-khazane me na ho to
        IMANDARI (saaf batao kaunsi zabanen jaanta hoon); zaban-wazeh
        na ho to coding-khazane ka asli pair (token-IDF)."""
        if not u.tokens or not _CODE_REQ_RX.search(u.text):
            return None
        got = self._code_msg(u.text)
        if got:
            msg, lang = got
            if msg == "?":
                langs = ", ".join(sorted(set(_CODE_LANGS.values())))
                return ("ye zaban (%s) abhi meri code-zubanon me nahi - "
                        "jhoot nahi bolunga. Ye zabanen jaanta hoon: %s."
                        % (lang, langs))
            # animated-mang? (html/css) - chalti-hui page-template
            anim = "animated" in u.text.lower() or "animation" in u.text.lower()
            show = " ".join(w for w in msg.split()
                            if w.lower().strip("!,.?") not in _ANIM_STRIP)
            show = show or msg
            if lang == "html" and anim:
                code = _PRINT_TPL["html-anim"] % _code_esc(show, "html")
                return ('ye lo - HTML me chalti-hui (animated) "%s" wala '
                        'page - isay .html naam se save kar ke browser me '
                        'kholein:\n```html\n%s\n```' % (show, code))
            code = _PRINT_TPL[lang] % _code_esc(msg, lang)
            fence = _FENCE.get(lang, lang)
            return ('ye lo - %s me "%s" chhapne wala code:\n```%s\n%s\n```'
                    % (lang, msg, fence, code))
        # zaban pakki nahi - coding-khazane se asli pair (token-IDF)
        try:
            if getattr(self, "_code_kr", None) is None:
                self._code_kr = KnowledgeRetrieval(
                    self.knowledge.corpus_dir,
                    files=["coding_knowledge.txt", "coding_deep_master.txt"])
            hits = self._code_kr.search(u.text, k=1)
            if hits:
                q, a, sc = hits[0]
                # faltu-milaap-guard: pair-ke-sawal me se kam-az-kam ek
                # matlab-lafz is-sawal me bhi ho ('code hjhjkghfgh' sirf
                # 'code' lafz par Lua-pair na utha le)
                share = (set(tk.key_tokens(q))
                         & (set(u.keys) - _FUNC_WORDS))
                if sc >= 0.45 and share:
                    return ("code-jawab (coding-khazana, bharosa %.2f):\n%s"
                            % (sc, a[:800]))
        except Exception:
            return None
        return None

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

    # ---------- soch-3: pehchaan (kaun ho / naam tumhara / kis kaam ke) ----------
    _ID_RX = re.compile(r"(kaun\s+ho|kon\s+ho|your\s+name|tumhara\s+naam|"
                        r"aap\s+kaun|aap\s+ka\s+naam|who\s+are\s+you|"
                        "tumhara naam kya|aapka naam kya|"
                        r"kis\s+kaam\s+ke|kya\s+kaam\s+karte|tumhara\s+kaam|"
                        r"aap\s+ka\s+kaam|what\s+do\s+you\s+do|"
                        # OWNER/HMHS identity (user-screenshot fix —
                        # 'who is hmhs' kabhi khazana-milaap NAHI):
                        r"who\s+(is|are)\s+(hmhs|hemomemo|hemo|huzaifa)\b|"
                        r"(hmhs|hemomemo)\s+(kaun|kon)\s+h[oa]|"
                        r"(hmhs|hemomemo)\s+kya\s+h[oa]|"
                        r"hmhs\s+(kaun|kon|about|info)|"
                        r"apna\s+taruf|apni\s+pehchaan)", re.I)

    def _identity(self, u: tk.Understanding) -> Optional[str]:
        if self._ID_RX.search(u.text):
            return ("Main Hemomemo AI hoon - HMHS (Hafiz Muhammed Huzaifa "
                    "Shamim) ki banayi hui 100% local AI. Na koi API, na "
                    "cloud - mera apna dimagh (token-soch + yaad + ilm) "
                    "isi PC par chalta hai. Mera kaam: sawal parhna, sochna, "
                    "ilm dena - aur yehi dimagh Hemomemo Game Bot ke andar "
                    "game khelne aur PC-control ka kaam bhi karta hai.")
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

        # 3.5) code-dimagh (token-evidence: code-irada + zaban + message)
        c = self._code(u)
        if c:
            soch.append("code-dimagh: token se irada+zaban+message pakra "
                        "- asli code (deterministic)")
            return c, {"source": "code", "bharosa": 0.97,
                       "soch": soch, "tokens": len(u.tokens)}

        # 3.9) sirf-adad/alamaat input ('5(5)', '34 56') — FLOW me jana NAHI
        if not u.qw and not any(c.isalpha() for c in u.text.replace(" ", "")):
            soch.append("sirf-adad: math-shakal me poochein (safai)")
            return ("yeh adad-input hai (meri token-samajh me lafz nahi). "
                    "Math aise poochein: 2+2, 12*4+3, circle ka area r 5 — "
                    "pakka hisab foran. Adad-par-junk-ilm main nahi deta — "
                    "imandari pehle."), \
                   {"source": "imandari", "bharosa": 0.6, "soch": soch,
                    "tokens": len(u.tokens)}

        # 3.95) nayab-lafz-imandari: SAB matlab-lafz ANJAAN hon (corpus me
        #       KABHI nahi) — khazana-milaap-nonsense nahi; seedha SACH.
        #       (DAWAAT pehle pakkday: hi/hii/salam — composer hi theek)
        #       Sirf EK lafz unseen ('namaz TARIIKA batao') ho to poora
        #       sawal barbaad nahi karo — soch-flow aage chalega.
        self._build_idf()
        if self._idf and not u.qw and not _is_dawaat_keys(u.keys):
            seen_k = [t for t in dict.fromkeys(u.keys) if t not in _FUNC_WORDS]
            unseen = [t for t in seen_k if t not in self._idf]
            if seen_k and len(unseen) == len(seen_k):
                soch.append("nayab-lafz: %s - khazane me nahi (imandari)"
                            % ", ".join(unseen[:3]))
                topic = " ".join(u.keys[:4]) or u.text[:40]
                return ("aap ne poocha: \"%s\" (topic: %s). "
                        "Mere ilm-khazane mein iska pakka jawab abhi nahi - "
                        "jhoot bol kar banana mera tareeqa nahi. Kya aap "
                        "thora wazah bata sakte hain?" % (u.text[:120], topic)), \
                       {"source": "imandari", "bharosa": 0.55, "soch": soch,
                        "tokens": len(u.tokens)}

        # 4) POORA SOCH-FLOW 🧠 (padh→samajh→ilm→research→banai→teeth→seekh):
        #    asli sawal kabhi sirf khazana-shortcut se ka NahiN — FULL flow
        #    (FlowTracker RECALL/RESEARCH/THINK/VERIFY + memory-seekh).
        ft, fm = self._flow(u)
        if ft:
            fm["soch"] = soch + fm.get("soch", [])
            return ft, fm

        # 5) flow-mila-nahi (fail-safe): imandari-jawab SAAF batao
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
                    return out[:4000], {"source": "composer", "bharosa": 0.7,
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

    # ---------- soch-4: POORA soch-flow (sawal yahin se chalega) ----------
    def _flow(self, u: tk.Understanding) -> Tuple[Optional[str], dict]:
        """🧠 FULL FLOW: samajh → ilm → research → soch-2 → verify → seekh.

        Sawal-answer (general) chat_once ke 3-soch pipeline me chalta hai
        (FlowTracker: READ→FOCUS→RECALL→RESEARCH?→THINK→VERIFY→LEARN→
        SPEAK) — 100% local (koi AI-API nahi). TokenBrain sirf neeche
        pakka-guard-jawab (math/identity/code/yaad) de, sawal-flow ko asli
        raste par bheje. meta=True se (text, dict) aata hai — us meta ki
        TokenBrain-shakal me naksha; fail ho to None (fallback imandari)."""
        if self.generate_fn is None:
            return None, {}
        try:
            from model.generate import chat_once
            out = chat_once(u.text, meta=True)
        except Exception:
            return None, {}
        text, meta = ((out if isinstance(out, tuple) else (out, {})))
        text = (text or "") if isinstance(text, str) else str(text)
        text = re.sub(r"^Hemomemo AI->\s*", "", text.strip())
        if not text:
            return None, {}
        m = meta if isinstance(meta, dict) else {}
        au = m.get("autonomous") if isinstance(m.get("autonomous"), dict) \
            else {}
        src = str(m.get("source") or au.get("source") or "soch-flow")
        bhat = m.get("confidence") or au.get("confidence")
        try:
            bhat = float(bhat)
        except Exception:
            bhat = 0.7
        flow = str(m.get("flow") or m.get("brain") or "soch-pipeline")
        return text[:4000], {"source": src, "bharosa": round(min(0.99,
                              max(0.4, bhat)), 2), "soch": [flow],
                             "tokens": len(u.tokens)}


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
