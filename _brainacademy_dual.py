# -*- coding: utf-8 -*-
"""
_brainacademy_dual.py — DO topic-trainers EK SATH, phir merge, phir a-to-z
apply. (HMHS ka 100% local system; koi API/cloud/external AI nahi.)

Trainer-A (hemomaster_codevid) : coding + video-generation + text
Trainer-B (hemomaster_cmdctrl) : cmd + shell + controlling + safe work
Phir merge  : dono topic-corps ka union par chota pass → EK unified dimagh
              (hemomaster_united_*.npz)
Phir apply  : checkpoints → People/installed package copy; corpus files →
              People (append-only); episodic recall memory dono roots me.*;
              honest report file.

Qanoon: purana data KABHI delete nahi — sab new-files + append-only.
"""
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, r"D:\DigitalBrain")
ROOT_A = r"D:\DigitalBrain"
ROOT_B = r"D:\HemomemoUltra-People"
LOG = os.path.join(ROOT_A, "_brainacademy_dual.log")
PY = sys.executable

CORP_A = [os.path.join(ROOT_A, "data", "corpus_big", "coding_knowledge.txt"),
          os.path.join(ROOT_A, "data", "corpus_big",
                       "coding_deep_master.txt"),
          os.path.join(ROOT_A, "data", "corpus_big",
                       "trainer_knowledge_2h.txt"),
          os.path.join(ROOT_A, "data", "corpus_big",
                       "trainer_lessons_coding_video_text.txt")]
CORP_B = [os.path.join(ROOT_A, "data", "corpus_big",
                       "trainer_knowledge_cmdshell.txt"),
          os.path.join(ROOT_A, "data", "corpus_big", "agent_orders.txt"),
          os.path.join(ROOT_A, "data", "corpus_big", "gamebot_tasks.txt")]
NEW_FILES = [os.path.join(ROOT_A, "data", "corpus_big",
                          "trainer_lessons_coding_video_text.txt"),
             os.path.join(ROOT_A, "data", "corpus_big",
                          "trainer_knowledge_cmdshell.txt")]


def log(s):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), s)
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def topic_args(corpora, prefix, tag, budget, epoch):
    return [PY, "-u", "-X", "utf8",
            os.path.join(ROOT_A, "_trainer_topic.py"),
            "--corpus", ",".join(corpora),
            "--budget", str(budget), "--epoch", str(epoch),
            "--prefix", prefix,
            "--log", os.path.join(ROOT_A, "_brainacademy_%s.log" % tag),
            "--jsonout", os.path.join(ROOT_A, "_brainacademy_%s.json" % tag)]


def learn_pairs_into_memory(root):
    """New lesson files → episodic recall memory (append-only)."""
    from model.memory import EpisodicStore
    mem = EpisodicStore(os.path.join(root, "data"))
    n = 0
    for p in NEW_FILES:
        if not os.path.exists(p):
            continue
        cur = None
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            for ln in f:
                ln = ln.strip()
                if ln.startswith("Sawal:"):
                    cur = ln[6:].strip()
                elif ln.startswith("Jawab:") and cur:
                    try:
                        mem.remember(cur, "task_sekho:" + ln[6:].strip(),
                                     tag="taleem-dual")
                        n += 1
                    except Exception as e:
                        log("remember err (%s): %r" %
                            (os.path.basename(root), e))
                    cur = None
    return n


def main():
    log("=== DUAL TOPIC-TRAINING START ===")
    log("Trainer-A: coding+video+text | Trainer-B: cmd+shell+control+safe")
    t_start = time.time()

    pa = subprocess.Popen(topic_args(CORP_A, "hemomaster_codevid",
                                     "codevid", 1200, 300), cwd=ROOT_A)
    pb = subprocess.Popen(topic_args(CORP_B, "hemomaster_cmdctrl",
                                     "cmdctrl", 1200, 300), cwd=ROOT_A)
    log("spawned A (pid %s) + B (pid %s) — eik sath chal rahe" %
        (pa.pid, pb.pid))
    rc_a, rc_b = pa.wait(), pb.wait()
    log("trainer-A rc=%s | trainer-B rc=%s" % (rc_a, rc_b))

    ra = os.path.join(ROOT_A, "_brainacademy_codevid.json")
    rb = os.path.join(ROOT_A, "_brainacademy_cmdctrl.json")
    ja = json.load(open(ra, encoding="utf-8")) if os.path.exists(ra) else {}
    jb = json.load(open(rb, encoding="utf-8")) if os.path.exists(rb) else {}
    if ja.get("final"):
        log("A-final: %s (steps=%s loss=%.4f)" %
            (os.path.basename(ja["final"]), ja.get("steps", -1),
             ja.get("avg_loss_last100", -1)))
    if jb.get("final"):
        log("B-final: %s (steps=%s loss=%.4f)" %
            (os.path.basename(jb["final"]), jb.get("steps", -1),
             jb.get("avg_loss_last100", -1)))

    # ------------------------------------------------------------ merge
    fin = None
    if rc_a == 0 and rc_b == 0 and ja.get("final") and jb.get("final"):
        log("MERGE: dono topics ka union corpus par 360s pass "
            "(ek unified dimagh me dono ilm)")
        pm = subprocess.Popen(topic_args(CORP_A + CORP_B, "hemomaster_united",
                                         "united", 360, 300), cwd=ROOT_A)
        pm.wait()
        old = os.path.join(ROOT_A, "_brainacademy_united.json")
        if os.path.exists(old):
            jm = json.load(open(old, encoding="utf-8"))
            fin = jm.get("final")
            if fin:
                log("unified brain: %s (steps=%s)" %
                    (os.path.basename(fin), jm.get("steps", -1)))
    else:
        log("merge SKIP (ek trainer fail hua) — jo hua wo pas se apply hoga")

    # ------------------------------------------------------------ apply
    log("APPLY: a-to-z har jagah (append-only)")
    applied = {}
    # 1) checkpoints → People (installed package) copy
    CK_A = os.path.join(ROOT_A, "model", "checkpoints")
    CK_B = os.path.join(ROOT_B, "model", "checkpoints")
    os.makedirs(CK_B, exist_ok=True)
    copied = []
    for f in sorted(os.listdir(CK_A)):
        if f.startswith(("hemomaster_codevid", "hemomaster_cmdctrl",
                         "hemomaster_united")) and f.endswith(".npz"):
            dst = os.path.join(CK_B, f)
            if not os.path.exists(dst):
                shutil.copy2(os.path.join(CK_A, f), dst)
                copied.append(f)
    applied["people_checkpoints"] = copied
    log("people checkpoints copied: %d files" % len(copied))
    # unified dimagh ko People me Clearly naya-ban-chahta hoon — copy2 upar
    # ho chuka (hemomaster_united_* prefix me shamil).
    # 2) corpus files → People corpus (append-only diff)
    for src in NEW_FILES + [os.path.join(ROOT_A, "data", "corpus_big",
                                         "trainer_knowledge_2h.txt")]:
        if not os.path.exists(src):
            continue
        dst = os.path.join(ROOT_B, "data", "corpus_big",
                           os.path.basename(src))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(src, "r", encoding="utf-8", errors="ignore") as f:
            sl = [x.strip() for x in f if x.strip()]
        tl = set()
        if os.path.exists(dst):
            with open(dst, "r", encoding="utf-8", errors="ignore") as f:
                tl = set(x.strip() for x in f if x.strip())
        add = [x for x in sl if x not in tl]
        with open(dst, "a", encoding="utf-8") as f:
            f.write("\n".join(add) + ("\n" if add else ""))
        log("people corpus %s: +%d lines" % (os.path.basename(src), len(add)))
    # 3) episodic recall memory dono roots me (a-to-z apply)
    try:
        n = learn_pairs_into_memory(ROOT_A)
        log("owner memory +remember: %d pairs" % n)
        applied["owner_remember"] = n
        n2 = learn_pairs_into_memory(ROOT_B)
        log("people memory +remember: %d pairs" % n2)
        applied["people_remember"] = n2
    except Exception as e:
        log("memory apply err (honest): %r" % (e,))
    # 4) honest report
    rep = os.path.join(ROOT_A, "_brainacademy_dual_report.json")
    json.dump({"trainer_A": ja, "trainer_B": jb, "unified_final": fin,
               "apply": applied, "total_wall_s": time.time() - t_start,
               "law": "100% local — no external AI/API/cloud; append-only"},
              open(rep, "w", encoding="utf-8"), indent=1)
    log("DUAL-DONE total wall=%.0fs | report: %s" %
        (time.time() - t_start, rep))


if __name__ == "__main__":
    main()
