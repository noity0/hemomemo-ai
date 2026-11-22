# -*- coding: utf-8 -*-
"""_train_50m_launch.pyw — 50M-trainer ka WINDOWLESS SUPERVISOR (resume-loop).

pythonw chupchaap background me:
  - apna-deadline: ab + TRAIN_SECONDS (env, setdefault 10800 = 3h)
  - trainer CHILD-process me (native-crash bhi sirf-child mara, supervisor bacha)
  - child bina-completion-marker mare → 30s me RELAUNCH (warm-start
    hemomaster_mid.npz se — mehfooz-atomic-save ki-wajah-se hamesha-salamat)
  - completion-marker: naya hemomaster_<epoch>.npz (final) + RESULT fresh
    → break (auto-apply trainer-child ke-andar khud chal-chuka-hoga)
  - budget < 600s bach-jaye aur completion nahi → mehfooz-exit
    (chhota-run aadha-model publish kar-dega — KABHI nahi)
  - ek-waqt ek-supervisor: data/_train_50m_sup.lock (PID-liveness-check)
  - 100% local — koi AI-API nahi (qanoon).

Maut-ki-jad (research): machine WATCHDOG LiveKernelEvent 0x1a8 storms
din-bhar-detected — stall-window me bhari-processes terminate. Isliye:
child-process-alag + atomic-save + resume-loop = har-maut sirf ≤15-min.
"""
import glob
import os
import subprocess
import sys
import time

ROOT = r"D:\DigitalBrain"
LOG = os.path.join(ROOT, "data", "_trainer_50m.log")
CKPT_DIR = os.path.join(ROOT, "model", "checkpoints")
RESULT = os.path.join(ROOT, "data", "_training5h_result.json")
TRAINER = os.path.join(ROOT, "_train_deep5h.py")
LOCK = os.path.join(ROOT, "data", "_train_50m_sup.lock")

os.environ.setdefault("TRAIN_DH", "1739")
os.environ.setdefault("TRAIN_SECONDS", "10800")
os.environ.setdefault("TRAIN_AUTO_APPLY", "0")   # publish task-by-task (manual)
DEADLINE = time.time() + float(os.environ["TRAIN_SECONDS"])
T0 = time.time()

PYW = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
if not os.path.exists(PYW):
    PYW = sys.executable


def sup_log(msg):
    try:
        with open(LOG, "a", encoding="utf-8", errors="replace") as f:
            f.write("[sup %s] %s\n" % (time.strftime("%H:%M:%S"), msg))
    except Exception:
        pass


def pid_alive(pid):
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "PID eq %d" % pid, "/NH", "/FO", "CSV"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW).stdout or ""
        return ("pythonw.exe" in out or "python.exe" in out)
    except Exception:
        return True   # unsure → duplicate-risk se bachne ke liye exit


# ek-waqt-ek-supervisor
if os.path.exists(LOCK):
    try:
        with open(LOCK, "r", encoding="utf-8") as f:
            old = int(f.read().strip() or "0")
        if old and old != os.getpid() and pid_alive(old):
            sup_log("duplicate-supervisor (PID %d zinda) — khamosh-exit" % old)
            sys.exit(0)
    except Exception:
        pass
try:
    with open(LOCK, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
except Exception:
    pass


def new_final_since(t0):
    """Naya-tareen FINAL hemomaster_<epoch>.npz (mid/chat/tmp chhor-ke)."""
    best = None
    try:
        for p in glob.glob(os.path.join(CKPT_DIR, "hemomaster_*.npz")):
            base = os.path.basename(p)
            if (base == "hemomaster_mid.npz" or "_mid" in base
                    or "_chat" in base or base.endswith(".tmp.npz")):
                continue
            m = os.path.getmtime(p)
            if m > t0 + 1 and (best is None or m > best[1]):
                best = (p, m)
    except Exception:
        return None
    return best[0] if best else None


def result_fresh(t0):
    try:
        return os.path.exists(RESULT) and os.path.getmtime(RESULT) > t0
    except Exception:
        return False


sup_log("SUPERVISOR shuru | budget %.0f min | PID %d"
        % ((DEADLINE - T0) / 60.0, os.getpid()))

while True:
    remaining = DEADLINE - time.time()
    if remaining <= 0:
        if new_final_since(T0):
            sup_log("budget-khatam, FINAL-mojood — mehfooz-exit"
                    " (apply-chain tasdeeq hogi)")
        else:
            sup_log("budget-khatam bina-completion — mehfooz-exit"
                    " (mid salamat; agli-relaunch par resume)")
        break
    if remaining < 600:
        sup_log("baqi %.0fs < 600 — chhota-run aadha-publish karega,"
                " mehfooz-exit (mid salamat)" % remaining)
        break

    env = dict(os.environ)
    env["TRAIN_SECONDS"] = str(int(remaining))
    env["TRAIN_DH"] = "1739"
    sup_log("child-launch | TRAIN_SECONDS=%d | warm-start mid se"
            % int(remaining))
    try:
        lhand = open(LOG, "a", encoding="utf-8", errors="replace")
    except Exception:
        lhand = None
    flags = (subprocess.CREATE_NO_WINDOW |
             subprocess.CREATE_NEW_PROCESS_GROUP |
             subprocess.CREATE_BREAKAWAY_FROM_JOB)   # job-se-bahir (restart-proof)
    try:
        p = subprocess.Popen(
            [PYW, "-Xutf8", TRAINER],
            cwd=ROOT,
            stdout=lhand if lhand else subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            env=env, close_fds=True, creationflags=flags)
    except Exception:
        flags = (subprocess.CREATE_NO_WINDOW |
                 subprocess.CREATE_NEW_PROCESS_GROUP)   # breakaway-mana → seedha
        try:
            p = subprocess.Popen(
                [PYW, "-Xutf8", TRAINER],
                cwd=ROOT,
                stdout=lhand if lhand else subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                env=env, close_fds=True, creationflags=flags)
        except Exception as e:
            if lhand:
                try:
                    lhand.close()
                except Exception:
                    pass
            sup_log("Popen FAIL: %s — 60s me dobara" % e)
            time.sleep(60)
            continue
    if lhand:
        try:
            lhand.close()          # child-ke-paas-virasat-me-handle-hai
        except Exception:
            pass

    rc = p.wait()
    final = new_final_since(T0)
    done = bool(final) and (rc == 0 or result_fresh(T0))
    if done:
        sup_log("🏁 MUKAMMAL: %s (rc=%s) — auto-apply child-me chal-chuka"
                % (os.path.basename(final), rc))
        break
    sup_log("child-bina-completion-mar-gaya (rc=%s, final=%s)"
            " — 30s me relaunch" % (rc,
                                    os.path.basename(final) if final else "-"))
    time.sleep(30)

try:
    os.remove(LOCK)
except Exception:
    pass
sup_log("SUPERVISOR khatam")
