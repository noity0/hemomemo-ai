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


def run_python(code, timeout=15.0):
    """Python-code chalao -> (ok, output, error, took_s)."""
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
