"""code_exec.py - Hemomemo PYTHON CODE-EXECUTION (100% local, no AI-API)
====================================================================
User ka diya hua Python-code IS laptop par chalta hai (temp-file +
subprocess + timeout). net-guard exec-code ke andar bhi ON hota hai
(AI-platform hosts HARD-BLOCK wahan bhi).

SECURITY:
  - code sirf LOCAL chalta hai (aap ke PC ka python)
  - timeout (default 15s) - atka-code khud mar jata hai
  - output limit (64KB)
  - net_guard inject: banaya-hua code bhi whitelist-firewall me rehta hai
"""
import os
import re
import subprocess
import sys
import tempfile
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TMP_DIR = os.path.join(_ROOT, "data", "code_exec_tmp")
_MAX_OUT = 65536
_GUARD_PRE = (
    "# Hemomemo auto-guard (qanoon: no-AI-API)\n"
    "try:\n"
    "    from harvest import net_guard as _ng\n"
    "    _ng.install()\n"
    "except Exception:\n"
    "    pass\n")


_SMART_MAP = {
    "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    "\u2013": "-", "\u2014": "-", "\u00a0": " ", "\u2026": "...",
    "\u2192": "->", "\u061b": ";",
}


def fix_common(code):
    """🩹 Aam coding-errors ka khud-ilaaj (100% local, safe textual-fix):
    fancy-quotes -> seedhe-quotes, unicode-digits -> ASCII 0-9,
    en/em-dash -> '-', non-breaking-space -> space, paste-hui
    line-numbers ('12: ') hatao. -> fixed_code"""
    c = code or ""
    for k, v in _SMART_MAP.items():
        c = c.replace(k, v)
    for _blk in (0x0660, 0x06F0, 0x0966):   # arabic/extended/devanagari digits
        for i in range(10):
            c = c.replace(chr(_blk + i), chr(48 + i))
    c = re.sub(r"(?m)^\s*\d{1,4}:\s?", "", c)
    return c


def run_python(code, timeout=15.0):
    """Python-code chalao -> (ok, output, error, took_s).
    🩹 CODING-ERROR-AUTO-FIX (user-hukum): pehli-koshish FAIL ho aur
    fix_common() kuch theek-kar sake to theek-karke DOBARA chalao."""
    code = (code or "").strip()
    if not code:
        return False, "", "khali-code", 0.0
    ok, out, err, took = _run_python_once(code, timeout)
    if not ok:
        fixed = fix_common(code)
        if fixed.strip() and fixed.strip() != code:
            ok2, out2, err2, took2 = _run_python_once(fixed, timeout)
            if ok2:
                return True, out2, "", took + took2
            return (False, out2,
                    ("auto-fix bhi fail: " + (err2 or err)).strip()[:2000],
                    took + took2)
    return ok, out, err, took


def _run_python_once(code, timeout=15.0):
    """Aik-dafa python-chalao -> (ok, output, error, took_s)."""
    code = (code or "").strip()
    if not code:
        return False, "", "khali-code", 0.0
    os.makedirs(_TMP_DIR, exist_ok=True)
    path = os.path.join(_TMP_DIR, "exec_%d.py" % int(time.time() * 1000))
    with open(path, "w", encoding="utf-8") as f:
        f.write(_GUARD_PRE + code + "\n")
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, "-Xutf8", path],
            capture_output=True, timeout=timeout, cwd=_ROOT)
        out = (r.stdout or b"").decode("utf-8", "replace")[:_MAX_OUT]
        err = (r.stderr or b"").decode("utf-8", "replace")[:_MAX_OUT]
        ok = (r.returncode == 0)
        return ok, out, ("" if ok else err), time.time() - t0
    except subprocess.TimeoutExpired:
        return False, "", "TIMEOUT: %ss me khatam nahi hua" % timeout, \
            time.time() - t0
    except Exception as e:
        return False, "", str(e)[:300], time.time() - t0
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def run_python_text(code, timeout=15.0):
    """Chat-ready jawab -> (text, meta)."""
    ok, out, err, took = run_python(code, timeout=timeout)
    if ok:
        body = out if out.strip() else "(code chala - koi output nahi)"
        txt = ("[python-exec] OK (%.1fs, 100%% local):\n```\n%s\n```"
               % (took, body.rstrip()[:4000]))
        return txt, {"source": "code-exec", "ok": True, "took": round(took, 2)}
    why = err.strip() or "unknown"
    txt = ("[python-exec] FAIL (%.1fs):\n```\n%s\n```\n"
           "(code theek karke dobara 'python' hukum do.)" % (took, why[:2500]))
    return txt, {"source": "code-exec", "ok": False,
                 "error": why[:300]}


# ------------------------------------------------- code-GEN (samajh-fix)
# 🆕 User-hukum (15-Nov): 'code i love pakistan with pakistani flag' jaisa
# hukum heading/text na bane — ASLI CODE bane (100% local, koi AI-API nahi).

_PY_TRUE_RX = re.compile(
    r"(?i)^(?:def\s|class\s|import\s|from\s|print\s*\(|@\w)")
_PY_MULTI_RX = re.compile(
    r"(?im)^\s*(?:def\s|class\s|import\s|from\s|print\s*\(|for\s|while\s|"
    r"if\s|with\s|return\b)|\)\s*[:=]|\w+\s*=\s*\S")
_PY_ASSIGN_RX = re.compile(r"^[A-Za-z_]\w*\s*=\s*\S")
_MATH_ONLY_RX = re.compile(r"^\s*[\d\s\.\+\-\*/%x\(\)]+\s*$")
_FLAG_WORDS = ("flag", "jhanda", "jhandah", "parcham", "parchami",
               "pakistan flag", "pak flag")


def looks_like_python(code):
    """Asli python-code lagta hai (chalana hai) ya DESCRIPTION hai (banana hai)?"""
    c = (code or "").strip()
    if not c:
        return False
    if _PY_TRUE_RX.match(c):
        return True
    if _PY_ASSIGN_RX.match(c):
        return True
    if "\n" in c and _PY_MULTI_RX.search(c):
        return True
    return False


_PAK_FLAG = [
    "     +---+------------------------------+",
    "     |###|                              |",
    "     |###|            (                 |",
    "     |###|          ( (                |",
    "     |###|           ( (   GREEN  (c)  |",
    "     |###|          ( (                |",
    "     |###|            (                 |",
    "     +---+------------------------------+",
]


def gen_program(desc):
    """Description -> chota-sachka python-program (print/math/jhanda)."""
    d = (desc or "").strip().strip("?!.,").strip()
    if not d:
        d = "hello hemomemo"
    low = d.lower()
    # 1) sirf-math ho to seedha calc
    if _MATH_ONLY_RX.match(d) and re.search(r"[\+\-\*/%x]", low):
        expr = d.replace("x", "*")
        return ('print("Jawab:", %s)' % expr)
    # 1b) table / factorial jaise mashhoor-chote-program bhi samajhta hai
    m = re.search(r"(?i)\btable\s*(?:of|ka)?\s*:?\s*(\d{1,3})\b", d)
    if m:
        n = int(m.group(1))
        return ('n = %d\nprint("Table of", n)\nfor i in range(1, 11):\n'
                '    print(n, "x", i, "=", n * i)' % n)
    m = re.search(r"(?i)\bfactorial\s*(?:of|ka)?\s*:?\s*(\d{1,3})\b", d)
    if m:
        return ('import math\nprint("Factorial:", math.factorial(%d))'
                % int(m.group(1)))
    # 2) waran-hi headline (pehla-harf bara)
    text = d[0].upper() + d[1:]
    lines = [
        '# Hemomemo auto-code (100% local, koi AI-API nahi)',
        '# aap ne kaha: "%s"' % d,
        'text = %r' % text,
        'print(text)',
    ]
    # 3) jhanda ka zikr -> Pakistan-flag ASCII bhi chhapo
    if any(w in low for w in _FLAG_WORDS):
        lines.append('print()')
        lines.append('for _r in %r:' % _PAK_FLAG)
        lines.append('    print(_r)')
    return "\n".join(lines)


# ---------------- multi-zaban code-gen (CODE-AI, 100% local) ----------------
_LANG_KEY = {
    "python": "python", "py": "python", "python3": "python",
    "c++": "cpp", "cpp": "cpp", "c plus plus": "cpp",
    "c#": "csharp", "csharp": "csharp", "c sharp": "csharp",
    "java": "java", "rust": "rust", "go": "go", "golang": "go",
    "php": "php", "html": "html", "sql": "sql",
    "assembly": "asm", "asm": "asm", "cobol": "cobol",
}
_SLOT_IN_RX = re.compile(r"(?i)\bin\s+([a-z0-9+#\-]{2,12})\s*$")
_SLOT_ME_RX = re.compile(r"(?i)^([a-z0-9+#\-]{2,12})\s+me\s+")


def _lang_slot(payload):
    """'... in <zaban>' / '<zaban> me ...' ka slot nikalo:
    -> (lang-key ('' agar zaban pehchani nahi), baqi-text, slot-mila?)"""
    m = _SLOT_IN_RX.search(payload)
    if m:
        return _LANG_KEY.get(m.group(1).lower(), ""), \
            payload[:m.start()].strip(), True
    m = _SLOT_ME_RX.match(payload)
    if m:
        return _LANG_KEY.get(m.group(1).lower(), ""), \
            payload[m.end():].strip(), True
    return "", payload, False


def _c_str(t):
    """C-family string-literal (\\ aur " escape)."""
    return '"%s"' % (t or "").replace("\\", "\\\\").replace('"', '\\"')


def _h_esc(t):
    """HTML-escape (& < >)."""
    return ((t or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _lang_templates(lang, text):
    """Zaban -> asli-code (rule-based, text-verbatim, koi API nahi)."""
    t = (text or "").strip() or "hello hemomemo"
    if lang == "python":
        lines = ["print(%r)" % t]
        if any(w in t.lower() for w in _FLAG_WORDS):
            lines += ["print()", "for _r in %r:" % _PAK_FLAG, "    print(_r)"]
        return "\n".join(lines)
    if lang == "cpp":
        return ("#include <iostream>\nusing namespace std;\n\n"
                "int main() {\n    cout << %s << endl;\n    return 0;\n}"
                % _c_str(t))
    if lang == "csharp":
        return ("using System;\n\nclass Program {\n    static void Main() {\n"
                "        Console.WriteLine(%s);\n    }\n}" % _c_str(t))
    if lang == "java":
        return ("public class Main {\n    public static void main"
                "(String[] args) {\n        System.out.println(%s);\n    }\n}"
                % _c_str(t))
    if lang == "rust":
        return "fn main() {\n    println!(%s);\n}" % _c_str(t)
    if lang == "go":
        return ("package main\n\nimport \"fmt\"\n\nfunc main() {\n"
                "    fmt.Println(%s)\n}" % _c_str(t))
    if lang == "php":
        return "<?php\necho %s;\n?>" % _c_str(t)
    if lang == "html":
        return ("<!DOCTYPE html>\n<html>\n<head>\n"
                "    <meta charset=\"utf-8\">\n    <title>Hemomemo</title>\n"
                "</head>\n<body>\n    <h1>%s</h1>\n</body>\n</html>"
                % _h_esc(t))
    if lang == "sql":
        return ("-- Hemomemo (100%% local)\nSELECT '%s' AS message;"
                % t.replace("'", "''"))
    if lang == "asm":
        msg = t.replace('"', "")
        return ('; linux x86-64 (nasm): "%s" chhapo\nsection .data\n'
                '    msg db "%s", 10\n    len equ $ - msg\n\nsection .text\n'
                'global _start\n_start:\n    mov rax, 1     ; syscall: write\n'
                '    mov rdi, 1     ; stdout\n    mov rsi, msg\n'
                '    mov rdx, len\n    syscall\n'
                '    mov rax, 60    ; syscall: exit\n    xor rdi, rdi\n'
                '    syscall' % (msg, msg))
    if lang == "cobol":
        return ("IDENTIFICATION DIVISION.\nPROGRAM-ID. HEMOMEMO.\n"
                "PROCEDURE DIVISION.\n    DISPLAY \"%s\".\n    STOP RUN."
                % t.replace('"', ""))
    return ""


def smart_code(payload, timeout=15.0):
    """'code <x>' ka samajh-fix:
    - x asli-python lagta hai -> seedha chalao (purana python-hukum jaisa)
    - '... in <zaban>' / '<zaban> me ...' -> us-zaban ka ASLI code banao
      (python chal-kar bhi dikhao; baqi zabanon ka code dekhne-ke-liye)
    - zaban nahi pehchani -> imandari listing (bina-jhoot)
    - warna x ek BAYAN hai -> usi ka python-code BANAO + chala-kar nateeja"""
    code = (payload or "").strip()
    if not code:
        return ("[code] khali hukum — 'code <kuch bhi>' likho ya "
                "'python <code>'"), {"source": "code-gen"}
    if looks_like_python(code):
        return run_python_text(code, timeout)
    lang, text, slot = _lang_slot(code)
    if slot and not lang:
        return ("[code-gen] Maaf-khwah — '%s' zaban main nahi jaanta hoon. "
                "Ye zabanein jaanta hoon: python, c++, c#, java, rust, go, "
                "php, html, sql, assembly, cobol — inhi me likho: "
                "'code <baat> in <zaban>'." % (text or code),
                {"source": "code-gen", "ok": True})
    if lang:
        prog = _lang_templates(lang, text or code)
        if lang == "python":
            exec_txt, meta = run_python_text(prog, timeout)
            head = ("[code-gen] '%s' — samajh gaya, ye code banaya "
                    "(100%% local):\n```python\n%s\n```" % (code[:140], prog))
            return head + "\n" + exec_txt, {"source": "code-gen",
                                            "ok": bool(meta.get("ok"))}
        txt = ("[code-gen] '%s' — %s ka asli-code (100%% local; is-PC par "
               "compiler/interpreter nahi, apne tool me chalao):\n```\n%s\n```"
               % (code[:140], lang.upper(), prog))
        return txt, {"source": "code-gen", "ok": True}
    prog = gen_program(code)
    exec_txt, meta = run_python_text(prog, timeout)
    head = ("[code-gen] '%s' — samajh gaya, ye code banaya (100%% local):\n"
            "```python\n%s\n```" % (code[:140], prog))
    return head + "\n" + exec_txt, {"source": "code-gen",
                                    "ok": bool(meta.get("ok"))}
