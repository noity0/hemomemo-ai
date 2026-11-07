# -*- coding: utf-8 -*-
r"""
📦 scripts/make_package.py — HEMOMO AI "FOR PEOPLE" PACKAGE BUILDER
======================================================================

D:\DigitalBrain (HEAD/development system)  ──make_package──▶
D:\HemomemoUltra-People (standalone folder — kisi bhi laptop chale,
DigitalBrain ki zaroorat NAHI)

Kya karta hai (asli, imandar):
  1) EXE fresh build (PyInstaller, icon ☪ ke sath) → dist\ → package
  2) RUNTIME files copy: model(code+checkpoints) + core + knowledge(guards)
     + harvest + security + server + web + data(corpus/ilm) — SIRF jo
     chalne ke liye chahiye (540MB quran/hadith raw-archives aur dev-training
     files package me NAHI — runtime unhe parhta hi nahi)
  3) 🛡️ PROTECT: system/knowledge/model files READ-ONLY (+R) — log edit
     nahi kar sakte; PROTECTED_MANIFEST.sha256 (hash-list) sath me —
     VERIFY-SYSTEM.bat (PowerShell) kisi bhi PC par tasdeeq karta hai.
     In-app L3 (8 security-files ka SHA manifest) fail-closed bhi hai.
  4) 🔁 UPDATE-SAFE: bande ki apni cheezein (data\genone_api.json,
     data\genone_users.json, learned_chat.txt, liveresearch.txt, qa_memo.pkl,
     harvester state) purani folder me hain to OVERWRITE NAHI hoti — log ki
     key/accounts/memory update ke baad bhi salamat.
  5) START-HEMOMO.bat + README-HEMOMO.md (log ke liye Roman-Urdu guide)

Chalao:  py -3 scripts\make_package.py           (purana package → update)
         py -3 scripts\make_package.py --fresh   (pehle poora saaf karo)
"""
import hashlib
import os
import shutil
import subprocess
import sys
import time

SRC = "D:\\DigitalBrain"
DST = "D:\\HemomemoUltra-People"
VERSION = "v4.2.0-people"

# copy hone wale poore folders (code) — andar se dev-filth chhaant ke
COPY_DIRS = ["core", "harvest", "security", "server", "web", "agent", "tests"]

# data me jo RUNTIME zaroori hai
DATA_FILES = ["corpus.txt", "qa_memo.pkl", "security_manifest.json",
              "quran_master.json", "hadith_master.json", "bukhari_master.json",
              "flow_state.json", "heart_state.json", "chat_learned_memory.json",
              "meta_thoughts.jsonl"]
CORPUS_BIG = None   # saari *.txt (learned_chat/liveresearch writable rehte)

# model checkpoints: GENMASTER = naya-tareen FINAL (dynamic, neeche) +
# baqi 3 dimagh fixed
CKPT_KEEP = ["gendeep_1793702467.npz",
             "genverify_1793780719.npz", "genhelper_1793780208.npz"]

IGNORE_DIRS = {"__pycache__", "archive", "_install", "quran", "hadith",
               "checkpoints"}   # checkpoints alag-tareeqe se
IGNORE_EXT = (".pyc", ".tmp", ".log", ".old", ".zip")


def _skip(name: str) -> bool:
    if name in IGNORE_DIRS or name.startswith("__pycache__"):
        return True
    if name.lower().endswith(IGNORE_EXT):
        return True
    if name.startswith("_") and name.endswith((".py", ".txt", ".json", ".log")):
        return True                      # dev temp/test files (_*.py etc.)
    return False


def _hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _readonly(path: str, ro: bool = True):
    try:
        os.chmod(path, (0o444 if ro else 0o666) if os.name != "nt" else
                 (0o444 if ro else 0o666))
    except Exception:
        pass
    try:
        subprocess.run(["attrib", "+R" if ro else "-R", path],
                       capture_output=True)
    except Exception:
        pass


def _copy2_retry(src: str, dst: str, tries: int = 6):
    """🔒 WinError-32-proof copy: read-only cheeni khulo, phir backoff-retry
    (AV / purana Hemomemo-process kabhi file lock kar leta hai)."""
    last = None
    for i in range(tries):
        try:
            _readonly(dst, ro=False)          # purani read-only file khulo
            shutil.copy2(src, dst)
            return
        except (PermissionError, OSError) as e:
            last = e
            print("   ⏳ copy-retry %d/%d: %s" % (i + 1, tries, dst))
            time.sleep(1.0 + i)               # 1s, 2s, 3s… backoff
    raise last


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    fresh = "--fresh" in sys.argv
    t0 = time.time()
    print("📦 SRC:", SRC)
    print("📦 DST:", DST)

    # ---- 0) purana package?
    if os.path.isdir(DST) and fresh:
        print("🧹 --fresh: purana package hatao…")
        subprocess.run(["attrib", "-R", os.path.join(DST, "*.*"),
                        "/S", "/D"], capture_output=True)
        shutil.rmtree(DST, ignore_errors=True)
    users_saved = os.path.join(DST, "data", "genone_users.json")
    key_saved = os.path.join(DST, "data", "genone_api.json")
    keep = {}
    for p in (users_saved, key_saved,
              os.path.join(DST, "data", "corpus_big", "learned_chat.txt"),
              os.path.join(DST, "data", "corpus_big", "liveresearch.txt"),
              os.path.join(DST, "data", "qa_memo.pkl"),
              os.path.join(DST, "harvest", "STATE.json"),
              os.path.join(DST, "harvest", "seen.json")):
        if os.path.exists(p):
            rel = os.path.relpath(p, DST)
            keep[rel] = p
    if os.path.isdir(DST):
        # UPDATE: purani writable files hatao (nayi aayengi), bande ki data bachao
        print("🔁 UPDATE-mode: purani system files hatao, log ki data bachao…")
        for root, dirs, files in os.walk(DST):
            for fn in files:
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, DST)
                if rel in keep:
                    continue
                _readonly(fp, ro=False)
                try:
                    os.remove(fp)
                except Exception:
                    pass
        # khali folder bhi saaf (quran/hadith-archive waghera ka naam-reza na bache)
        for root, dirs, files in os.walk(DST, topdown=False):
            if os.path.abspath(root) != os.path.abspath(DST) \
                    and not os.listdir(root):
                try:
                    os.rmdir(root)
                except Exception:
                    pass
            for dn in dirs:
                _readonly(os.path.join(root, dn), ro=False)

    # ---- 1) EXE fresh build (icon ☪ ke sath)
    print("🔨 EXE build (PyInstaller)…")
    exe_src = os.path.join(SRC, "dist", "Hemomemo-Ultra-Brain.exe")
    r = subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm",
                        "Hemomemo-Ultra-Brain.spec"], cwd=SRC,
                       capture_output=True, text=True)
    # sachi-taza-check: EXE kam-az-kam sab se nayi source jaisa naya ho
    src_latest = 0
    for rel in ("app/genone_app.py", "app/genone.ico",
                "Hemomemo-Ultra-Brain.spec", "server/genone_server.py",
                "server/accounts.py"):
        p = os.path.join(SRC, rel)
        if os.path.exists(p):
            src_latest = max(src_latest, os.path.getmtime(p))
    fresh = (r.returncode == 0 and os.path.exists(exe_src)
             and os.path.getmtime(exe_src) >= src_latest - 2)
    if not fresh:
        print("❌ EXE build FAIL ya PURANA (rc=%s)" % r.returncode)
        for tail in (r.stdout[-1500:], r.stderr[-1500:]):
            if tail:
                print(tail)
        sys.exit(1)
    print("   EXE-OK (%.1f MB, built %s)"
          % (os.path.getsize(exe_src) / 1048576,
             time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(exe_src)))))

    # ---- 1b) GAMEBOT-EXE (Hemomemo-GameBot - console, isi-folder ka dimagh)
    print("🔨 GAMEBOT-EXE build (Hemomemo-GameBot)…")
    agent_src = os.path.join(SRC, "dist", "Hemomemo-GameBot.exe")
    ra = subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm",
                         "Hemomemo-GameBot.spec"], cwd=SRC,
                        capture_output=True, text=True)
    src_latest_a = 0
    for rel in ("agent/console_app.py", "agent/orders.py", "agent/mc_bot.py",
                "Hemomemo-GameBot.spec", "model/understand.py",
                "model/tokenize.py"):
        p = os.path.join(SRC, rel)
        if os.path.exists(p):
            src_latest_a = max(src_latest_a, os.path.getmtime(p))
    fresh_a = (ra.returncode == 0 and os.path.exists(agent_src)
               and os.path.getmtime(agent_src) >= src_latest_a - 2)
    if not fresh_a:
        print("❌ AGENT-EXE build FAIL ya PURANA (rc=%s)" % ra.returncode)
        for tail in (ra.stdout[-1200:], ra.stderr[-1200:]):
            if tail:
                print(tail)
        sys.exit(1)
    print("   AGENT-EXE-OK (%.1f MB, built %s)"
          % (os.path.getsize(agent_src) / 1048576,
             time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(agent_src)))))

    os.makedirs(DST, exist_ok=True)

    # ---- 2) files copy
    copied = 0
    # ye files bande ki APNI hain — hamesha writable; purani ho to overwrite NAHI
    WRITABLE_REL = {"data\\corpus_big\\learned_chat.txt",
                    "data\\corpus_big\\liveresearch.txt",
                    "data\\qa_memo.pkl",
                    "harvest\\STATE.json", "harvest\\seen.json",
                    "data\\genone_api.json", "data\\genone_users.json"}

    def cpy(src, dst, ro=True):
        nonlocal copied
        rel = os.path.relpath(dst, DST).lower()
        if rel in {w.lower() for w in WRITABLE_REL}:
            ro = False
            if os.path.exists(dst):
                return                  # 🔁 update-safe: user-data mehfooz
        if os.path.exists(dst):
            _readonly(dst, ro=False)    # purani read-only cheeni pehle khulo
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        _copy2_retry(src, dst)
        if ro:
            _readonly(dst, ro=True)
        copied += 1

    for d in COPY_DIRS:
        sroot = os.path.join(SRC, d)
        for root, dirs, files in os.walk(sroot):
            dirs[:] = [x for x in dirs if x not in ("__pycache__",)]
            for fn in files:
                if _skip(fn):
                    continue
                rel = os.path.relpath(os.path.join(root, fn), SRC)
                cpy(os.path.join(root, fn), os.path.join(DST, rel))

    # model: code (train scripts dev-hain — package me nahi) + checkpoints
    mroot = os.path.join(SRC, "model")
    for fn in os.listdir(mroot):
        fp = os.path.join(mroot, fn)
        if os.path.isfile(fp) and fn.endswith(".py") and not _skip(fn) \
                and fn not in ("train.py", "train_2b.py"):
            cpy(fp, os.path.join(DST, "model", fn))
        elif os.path.isfile(fp) and fn.endswith((".json", ".md")) and not _skip(fn):
            cpy(fp, os.path.join(DST, "model", fn))
    ck = os.path.join(mroot, "checkpoints")
    arch = os.path.join(ck, "archive")

    def newest_genmaster():
        # 🧠 naya-tareen FINAL genmaster (checkpoints/ + archive/) — mid/chat/tmp
        # nahi, sirf final (training har baar naya timestamp-wala final banata hai)
        cands = []
        for d in (ck, arch):
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if (f.startswith("genmaster_") and f.endswith(".npz")
                        and "_mid" not in f and "_chat" not in f
                        and not f.endswith(".tmp.npz")):
                    cands.append(os.path.join(d, f))
        return max(cands, key=os.path.getmtime) if cands else None

    gm = newest_genmaster()
    ckpt_keep = ([os.path.basename(gm)] if gm else []) + \
                [f for f in CKPT_KEEP if not f.startswith("genmaster_")]
    for fn in ckpt_keep:
        fp = os.path.join(ck, fn)
        if not os.path.exists(fp) and os.path.exists(os.path.join(arch, fn)):
            fp = os.path.join(arch, fn)      # training-archive fallback (active
        if os.path.exists(fp):               #  training ka mid-archive surakshit)
            cpy(fp, os.path.join(DST, "model", "checkpoints", fn))
    vp = os.path.join(ck, "vocab.json")      # tokenizer-exact vocab bhi sath
    if os.path.exists(vp):
        cpy(vp, os.path.join(DST, "model", "checkpoints", "vocab.json"))

    # knowledge: sirf guards + README (raw quran/hadith archives runtime me
    # NAHI parhte jate — 540MB faltu bhaar nahi)
    kroot = os.path.join(SRC, "knowledge")
    for fn in os.listdir(kroot):
        fp = os.path.join(kroot, fn)
        if os.path.isfile(fp) and fn.endswith((".py", ".md")) and not _skip(fn):
            cpy(fp, os.path.join(DST, "knowledge", fn))

    # data (runtime ilm)
    dat = os.path.join(SRC, "data")
    for fn in DATA_FILES:
        fp = os.path.join(dat, fn)
        if os.path.exists(fp):
            cpy(fp, os.path.join(DST, "data", fn))
    big = os.path.join(dat, "corpus_big")
    for fn in os.listdir(big):
        if fn.endswith(".txt") and not _skip(fn):
            rel_keep = os.path.relpath(os.path.join(big, fn), SRC)
            dst_p = os.path.join(DST, "data", "corpus_big", fn)
            if rel_keep in keep:            # bande ki memory — purani copy
                # 📌 keep[rel_keep] == dst_p (ek hi jagah) — delete-loop ne file
                #    bacha li thi, to khud-par-khud copy (WinError 32) nahi karni;
                #    sirf writable qaim rakho (app nayi seekh likhe)
                _readonly(dst_p, ro=False)
                copied += 1
            else:
                cpy(os.path.join(big, fn), dst_p,
                    ro=(fn not in ("learned_chat.txt", "liveresearch.txt")))

    # bande ki bacha-hui data wapas (update-safe)
    for rel, old in keep.items():
        dst_p = os.path.join(DST, rel)
        if not os.path.exists(dst_p) and rel not in (
                "data\\corpus_big\\learned_chat.txt",
                "data\\corpus_big\\liveresearch.txt",
                "data\\qa_memo.pkl",
                "harvest\\STATE.json", "harvest\\seen.json"):
            os.makedirs(os.path.dirname(dst_p), exist_ok=True)
            _copy2_retry(old, dst_p)
            _readonly(dst_p, ro=False)
            copied += 1

    # EXE + bat + README + version + hash-manifest
    _copy2_retry(exe_src, os.path.join(DST, "Hemomemo-Ultra-Brain.exe"))
    copied += 1
    # GAMEBOT-EXE (Minecraft bot + PC-aankh console) - isi folder mein
    _copy2_retry(agent_src, os.path.join(DST, "Hemomemo-GameBot.exe"))
    copied += 1

    with open(os.path.join(DST, "START-HEMOMO.bat"), "w",
              encoding="utf-8") as f:
        f.write('@echo off\r\ntitle Hemomemo AI\r\n'
                'start "" "%~dp0Hemomemo-Ultra-Brain.exe"\r\n')
    with open(os.path.join(DST, "START-GAMEBOT.bat"), "w",
              encoding="utf-8") as f:
        f.write('@echo off\r\ntitle Hemomemo Game Bot (Minecraft bot + PC-aankh)\r\n'
                'start "" "%~dp0Hemomemo-GameBot.exe"\r\n')

    # ---- BRAIN-LINK: owner-published-dimagh ka rasta (sirf file-sync,
    #      koi AI/model/platform API nahi; app bina iske bhi 100% local)
    _cks = []
    _ck_dir = os.path.join(SRC, "model", "checkpoints")
    if os.path.isdir(_ck_dir):
        _cks = [os.path.join(_ck_dir, f) for f in os.listdir(_ck_dir)
                if f.startswith("genmaster_") and f.endswith(".npz")]
    if _cks:
        _ck = max(_cks, key=os.path.getmtime)
        _bname = os.path.basename(_ck)
        _bh = hashlib.sha256(open(_ck, "rb").read()).hexdigest()
        _ver = _bname.rsplit("_", 1)[-1].replace(".npz", "")
        try:
            os.makedirs(os.path.join(DST, "data"), exist_ok=True)
            with open(os.path.join(DST, "data", "brain_version.json"),
                      "w", encoding="utf-8") as f:
                import json as _json
                _json.dump({"version": _ver, "file": _bname,
                            "sha256": _bh}, f, indent=1)
        except OSError:
            pass
    _upd = os.path.join(SRC, "update_brain.ps1")
    if os.path.exists(_upd):
        _copy2_retry(_upd, os.path.join(DST, "update_brain.ps1"))
        copied += 1
    with open(os.path.join(DST, "UPDATE-BRAIN.bat"), "w",
              encoding="utf-8") as f:
        f.write('@echo off\r\ntitle Hemomemo Brain-Link (owner-published)\r\n'
                'powershell -NoProfile -ExecutionPolicy Bypass -File '
                '"%~dp0update_brain.ps1"\r\npause\r\n')
    with open(os.path.join(DST, "VERIFY-SYSTEM.bat"), "w",
              encoding="utf-8") as f:
        f.write('@echo off\r\ntitle Hemomemo System Verify\r\n'
                'powershell -NoProfile -ExecutionPolicy Bypass -File '
                '"%~dp0verify_system.ps1"\r\npause\r\n')

    # sha256 manifest (protected files)
    prot = []
    for root, dirs, files in os.walk(DST):
        dirs[:] = [x for x in dirs if x not in ("__pycache__",)]
        for fn in files:
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, DST).lower()
            if fn in ("genone_api.json", "genone_users.json",
                      "genone_api.log", "learned_chat.txt",
                      "liveresearch.txt", "qa_memo.pkl", "STATE.json",
                      "seen.json", "PROTECTED_MANIFEST.sha256",
                      "verify_system.ps1") or rel.startswith("harvest\\"):
                continue
            if fn.endswith((".exe", ".bat")):
                continue
            prot.append((_hash(fp), rel))
            _readonly(fp, ro=True)
    prot.sort()
    with open(os.path.join(DST, "PROTECTED_MANIFEST.sha256"), "w",
              encoding="utf-8") as f:
        f.write("# Hemomemo AI — PROTECTED SYSTEM FILES (SHA-256)\n"
                "# Ye list read-only hai; file badli to hash nahi milega.\n")
        for h, rel in prot:
            f.write("%s  %s\n" % (h, rel))

    # PowerShell verifier (kisi bhi PC par — python ki zaroorat nahi)
    ps = ("$ok = $true\n"
          "Write-Host '== Hemomemo AI — SYSTEM VERIFY ==' -ForegroundColor Green\n"
          "foreach ($line in Get-Content '$PSScriptRoot\\PROTECTED_MANIFEST.sha256') {\n"
          "  if ($line -match '^([0-9a-f]{64})  (.+)$') {\n"
          "    $p = Join-Path $PSScriptRoot $Matches[2]\n"
          "    if (-not (Test-Path $p)) { Write-Host ('GAYIB  ' + $Matches[2]) -ForegroundColor Red; $ok = $false; continue }\n"
          "    $h = (Get-FileHash $p -Algorithm SHA256).Hash.ToLower()\n"
          "    if ($h -eq $Matches[1]) { Write-Host ('SAABIT ' + $Matches[2]) -ForegroundColor DarkGray }\n"
          "    else { Write-Host ('TABDEELI ' + $Matches[2]) -ForegroundColor Red; $ok = $false }\n"
          "  }\n"
          "}\n"
          "if ($ok) { Write-Host '>> SAB SAABIT — system pakka hai' -ForegroundColor Green }\n"
          "else { Write-Host '>> KHATARNAK — system files me tabdeeli! naya package lein' -ForegroundColor Red }\n")
    with open(os.path.join(DST, "verify_system.ps1"), "w",
              encoding="utf-8") as f:
        f.write(ps)

    with open(os.path.join(DST, "VERSION.txt"), "w", encoding="utf-8") as f:
        f.write("Hemomemo AI %s\nBuilt: %s\nHead: D:\\DigitalBrain "
                "(development system)\nOwner: Hafiz Muhammed Huzaifa Shamim "
                "(HMHS)\n" % (VERSION, time.strftime("%Y-%m-%d %H:%M")))

    readme = r"""# ☪ Hemomemo AI — FOR PEOPLE PACKAGE

Ye folder MUKAMMAL standalone hai — aapke PC par **D:\DigitalBrain jaisa
koi development-folder zaroori NAHI**. 100% local — **koi platform/API
(cloud/OpenAI/Gemini/…) nahi**.

## Chalao
1. `START-HEMOMO.bat` (ya seedha `Hemomemo-Ultra-Brain.exe`) — app khulegi.
2. App khulte hi **Hemomemo ki APNI local API khud ON** ho jati hai
   (127.0.0.1:8790) — browser me `http://127.0.0.1:8790` kholo (website).

## Apni API key lein (har bande ki apni)
- App → 🌐 **Hemomemo API** page → **👤 Apni API lein (Sign-in)**
  → Gmail/Email + password → **🆕 Nayi API lein** → key `hemo…` milti hai
  → **📋 Key copy**.
- API-use (developers ke liye):
  `POST http://127.0.0.1:8790/v1/chat`
  headers: `X-Hemomemo-Key: <aap ki hemo… key>`, `X-Hemomemo-Ts: <unix-seconds>`,
  `X-Hemomemo-Nonce: <nayi har request par>`
  body: `{"prompt": "sawal"}`
- `GET /health`, `GET /v1/info`, `GET /v1/auth/me` — wahi key se.
- ⚠️ Sign-in **100% local** hai (email+password isi PC par mehfooz,
  PBKDF2-hash). Asli Google-OAuth JAAN-BOOJH kar nahi hai — wo Google ki
  API mangta hai aur Hemomemo ka qanoon hai: **NO any platform API of the world**.

## Agent-hukum (Minecraft + PC-aankhein — sab 100% local)
- `py -3 -m agent.modes text`            — chat (token-dimagh se samajh)
- `py -3 -m agent.modes code`            — coding AI (code-block jawab)
- `py -3 -m agent.modes agent`           — bot direct-play (aap ke sath)
- `py -3 -m agent.modes mc <host> [port]`  — Minecraft server par KHUD join
- `py -3 -m agent.modes duo <host> [port]` — 2 KIRDAR multi-play
- `py -3 -m agent.modes pc-watch`        — screen-AANKH (dekhe + bataye)
- `py -3 -m agent.modes pc-play`         — dekhe + WASD/mouse chalaye

## Hifazat (ye system aap ki amanat hai)
- `model/`, `core/`, `knowledge/`, `security/`, `server/`, `web/`,
  `data/corpus*` — sab **READ-ONLY** hain; edit karne ki koshish na karo.
- Tasdeeq: `VERIFY-SYSTEM.bat` chalao — har file ka SHA-256
  `PROTECTED_MANIFEST.sha256` se milta hai. Tabdeeli ho to laal warning.
- App ke andar bhi L3-integrity khud check karti hai (8 security-files —
  koi chhed-chhar → model fail-closed block).

## Apni yaad/data
- `data/genone_users.json` (aap ki key/accounts), `data/genone_api.json`,
  `data/corpus_big/learned_chat.txt` (app ki nayi seekh) — ye aap ki hain;
  update me bhi mehfooz rehti hain.

## Update
Naya version aaye (is folder ka naya copy) to purane folder par rakh do —
aap ki key/accounts/yaad mehfooz rehti hai. Sirf system files naye ban
jate hain.

Banane wale: **Hafiz Muhammed Huzaifa Shamim (HMHS)** — Alhamdulillah ☪
"""
    with open(os.path.join(DST, "README-HEMOMO.md"), "w",
              encoding="utf-8") as f:
        f.write(readme)

    size = sum(os.path.getsize(os.path.join(r, fn))
               for r, _, fs in os.walk(DST) for fn in fs) / 1048576
    print("✅ PACKAGE-OK: %s  |  files: %d  |  size: %.1f MB  |  %.0fs"
          % (DST, copied, size, time.time() - t0))
    print("   🛡️ protected files: %d (read-only + SHA-256 manifest)" % len(prot))
    print("   Chalao: %s\\START-HEMOMO.bat" % DST)


if __name__ == "__main__":
    main()
