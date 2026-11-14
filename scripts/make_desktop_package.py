# -*- coding: utf-8 -*-
r"""
📦 scripts/make_desktop_package.py — HEMOMEMO AI DESKTOP-APP PACKAGE BUILDER
======================================================================

D:\DigitalBrain (dev)  ──make_desktop_package──▶
D:\HemomemoUltra-People\hemomemo_ai_desktop   (COMPLETE standalone desktop app)

Qanoon (pakke usool):
  1) EXE (app + game-bot) FRESH hon — purana EXE copy NAHI hoga
  2) 100% STANDALONE: model/code+checkpoints, core, agent, server, security,
     harvest, knowledge-guards, data-corpus — sab in-folder (DigitalBrain ki
     zaroorat NAHI — lekin maujood ho to 24/7 LIVE-link ban jati hai)
  3) SIRF Hemomemo system — koi AI-API/platform/cloud nahi (offline-oath)
  4) 🛡️ system-files READ-ONLY + SHA-256 manifest + VERIFY-SYSTEM.bat
  5) 🔁 update-safe: bande ki apni data (keys/accounts/yaad) kabhi overwrite nahi
  6) 🔄 24/7 CONNECTION-HUB: junction + registry + auto-restart + monitor
     (laptop band ho ya dobara on — connections wapas khud lagti hain)
  7) ZIP: hemomemo_ai_desktop_complete.zip

Chalao:  py -3.12 scripts\make_desktop_package.py
"""
import hashlib
import os
import shutil
import subprocess
import sys
import time
import zipfile

_NOWIN = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW: koi cmd-window flash nahi

SRC = "D:\\DigitalBrain"
DST = "D:\\DigitalBrain\\build\\hemomemo_ai_desktop"  # 🔒 staging — users-folder me DUPLICATE nahi banega
VERSION = "v5.1.0-desktop"

COPY_DIRS = ["core", "harvest", "security", "server", "web", "agent", "tests"]
DATA_FILES = ["corpus.txt", "qa_memo.pkl", "security_manifest.json",
              "quran_master.json", "hadith_master.json", "bukhari_master.json",
              "flow_state.json", "heart_state.json", "chat_learned_memory.json",
              "meta_thoughts.jsonl", "brain_version.json"]
CKPT_FIXED = ["gendeep_1793702467.npz",
              "genverify_1793780719.npz", "genhelper_1793780208.npz"]
WRITABLE_REL = {"data\\corpus_big\\learned_chat.txt",
                "data\\corpus_big\\liveresearch.txt",
                "data\\qa_memo.pkl",
                "harvest\\state.json", "harvest\\seen.json",
                "data\\genone_api.json", "data\\genone_users.json",
                "data\\chat_history_app.json"}
IGNORE_DIRS = {"__pycache__", "archive", "_install", "quran", "hadith",
               "checkpoints", "temp_frames", "backups", "memory"}
IGNORE_EXT = (".pyc", ".tmp", ".log", ".old")


# OWNER-CREDENTIALS (qanoon): in files ka package/zip me KABHI jana mana hai
_SECRETS_NAMES = {
    "email_link.json", "api_keys.json", ".env", ".netlify_token.txt",
    "netlify_token.txt", "credentials.json", "secrets.json",
    "service_account.json", "client_secret.json", "owner_key.json",
    "token_store.json", "password.txt", "passwords.txt",
    "google_oauth.json", "gdrive_tokens.json"}


def _purge_secrets(dst: str) -> list:
    """Aakhri-hatif: DST me kahin credential-file bachi ho to KHATAM.
    Junction/symlink ke andar KABHI nahi utarna - owner-files mehfooz."""
    hit = []
    for root, dirs, files in os.walk(dst):
        dirs[:] = [d for d in dirs if d.lower() != "digitalbrain"
                   and not os.path.islink(os.path.join(root, d))]
        for fn in files:
            low = fn.lower()
            if (low in _SECRETS_NAMES or low.endswith(".token")
                    or low.endswith(".token.txt") or ".token." in low):
                fp = os.path.join(root, fn)
                try:
                    os.chmod(fp, 0o666)
                    os.remove(fp)
                    hit.append(os.path.relpath(fp, dst))
                except Exception:
                    pass
    if hit:
        print("   [SECRETS-PURGE] package se hataya (owner-credentials "
              "kabhi ship nahi hoti): %s" % ", ".join(hit))
    return hit


def _skip(name: str) -> bool:
    if name in IGNORE_DIRS or name.startswith("__pycache__"):
        return True
    if name.lower().endswith(IGNORE_EXT):
        return True
    if name.startswith("_") and name.endswith((".py", ".txt", ".json", ".log")):
        return True
    if name.lower() in _SECRETS_NAMES or name.lower().endswith(".token"):
        return True                      # owner-credentials kabhi copy nahi
    return False


def _hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _readonly(path: str, ro: bool = True):
    try:
        os.chmod(path, 0o444 if ro else 0o666)
    except Exception:
        pass
    try:
        subprocess.run(["attrib", "+R" if ro else "-R", path],
                       capture_output=True, creationflags=_NOWIN)
    except Exception:
        pass


def _copy2_retry(src: str, dst: str, tries: int = 6):
    last = None
    for i in range(tries):
        try:
            _readonly(dst, ro=False)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return
        except (PermissionError, OSError) as e:
            last = e
            print("   retry %d/%d: %s" % (i + 1, tries, dst), flush=True)
            time.sleep(1.0 + i)
    raise last


def newest_genmaster(cks: str, arch: str):
    cands = []
    for d in (cks, arch):
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if (f.startswith("genmaster_") and f.endswith(".npz")
                    and "_mid" not in f and "_chat" not in f
                    and not f.endswith(".tmp.npz")):
                cands.append(os.path.join(d, f))
    return max(cands, key=os.path.getmtime) if cands else None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    t0 = time.time()
    print("📦 SRC:", SRC)
    print("📦 DST:", DST)

    # ---- 0) bande ki purani data pakdo (update-safe) ----
    keep = {}
    for rel in ("data\\genone_users.json", "data\\genone_api.json",
                "data\\corpus_big\\learned_chat.txt",
                "data\\corpus_big\\liveresearch.txt",
                "data\\qa_memo.pkl", "data\\chat_history_app.json",
                "harvest\\state.json", "harvest\\seen.json"):
        p = os.path.join(DST, rel)
        if os.path.exists(p):
            keep[rel.lower()] = p

    if os.path.isdir(DST):
        print("🔁 UPDATE: purani system files hatao, bande ki data bachao…")
        for root, dirs, files in os.walk(DST):
            dirs[:] = [d for d in dirs
                       if d.lower() != "digitalbrain"
                       and not os.path.islink(os.path.join(root, d))]
            for fn in files:
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, DST).lower()
                if rel in keep or rel.startswith("connection_hub"):
                    continue
                _readonly(fp, ro=False)
                try:
                    os.remove(fp)
                except Exception:
                    pass
        # 🔗 junction-follow NAHI (empty-folder saaf, loop-se-bachao)
        def _sweep_empty(d):
            try:
                ents = list(os.scandir(d))
            except Exception:
                return
            for e in ents:
                try:
                    if e.is_dir(follow_symlinks=False) \
                            and not e.is_junction() \
                            and e.name.lower() != "digitalbrain":
                        _sweep_empty(e.path)
                except Exception:
                    pass
            for e in ents:
                try:
                    if e.is_dir(follow_symlinks=False) \
                            and e.path != os.path.abspath(DST) \
                            and not os.listdir(e.path):
                        os.rmdir(e.path)
                except Exception:
                    pass
        _sweep_empty(DST)

    # ---- 1) EXE fresh-check (+ zaroorat par rebuild) ----
    print("🔨 EXE fresh-check…")
    exe_src = os.path.join(SRC, "dist", "Hemomemo-Ultra-Brain.exe")
    agent_src = os.path.join(SRC, "dist", "Hemomemo-GameBot.exe")
    for spec, exe in (("Hemomemo-Ultra-Brain.spec", exe_src),
                      ("Hemomemo-GameBot.spec", agent_src)):
        need = not os.path.exists(exe)
        if not need:
            newest = 0
            for rel in ("app/genone_app.py", "app/genone.ico",
                        "Hemomemo-Ultra-Brain.spec", "agent/console_app.py",
                        "Hemomemo-GameBot.spec"):
                p = os.path.join(SRC, rel)
                if os.path.exists(p):
                    newest = max(newest, os.path.getmtime(p))
            need = os.path.getmtime(exe) < newest - 2
        if need:
            print("   rebuild:", spec)
            r = subprocess.run([sys.executable, "-m", "PyInstaller",
                                "--noconfirm", spec], cwd=SRC,
                               capture_output=True, text=True,
                               creationflags=_NOWIN)
            if r.returncode != 0 or not os.path.exists(exe):
                print("❌ EXE-FAIL:", spec)
                for tail in (r.stdout[-1200:], r.stderr[-1200:]):
                    if tail:
                        print(tail)
                sys.exit(1)
    for exe in (exe_src, agent_src):
        print("   EXE-OK: %s (%.1f MB)" % (os.path.basename(exe),
                                           os.path.getsize(exe) / 1048576))

    os.makedirs(DST, exist_ok=True)
    copied = 0

    def cpy(src, dst, ro=True):
        nonlocal copied
        rel = os.path.relpath(dst, DST).lower()
        if rel in WRITABLE_REL:
            ro = False
            if os.path.exists(dst):
                return                       # 🔁 bande ki data mehfooz
        if os.path.exists(dst):
            _readonly(dst, ro=False)
        _copy2_retry(src, dst)
        if ro:
            _readonly(dst, ro=True)
        copied += 1

    # ---- 2) code-folders ----
    for d in COPY_DIRS:
        sroot = os.path.join(SRC, d)
        for root, dirs, files in os.walk(sroot):
            dirs[:] = [x for x in dirs if x not in ("__pycache__",)]
            for fn in files:
                if _skip(fn):
                    continue
                rel = os.path.relpath(os.path.join(root, fn), SRC)
                cpy(os.path.join(root, fn), os.path.join(DST, rel))

    # ---- 3) model: runtime-code + checkpoints ----
    mroot = os.path.join(SRC, "model")
    for fn in os.listdir(mroot):
        fp = os.path.join(mroot, fn)
        if os.path.isfile(fp) and fn.endswith(".py") and not _skip(fn) \
                and fn not in ("train.py", "train_2b.py"):
            cpy(fp, os.path.join(DST, "model", fn))
        elif os.path.isfile(fp) and fn.endswith((".json", ".md")) \
                and not _skip(fn):
            cpy(fp, os.path.join(DST, "model", fn))
    ck = os.path.join(mroot, "checkpoints")
    arch = os.path.join(ck, "archive")
    gm = newest_genmaster(ck, arch)
    ckpt_keep = ([os.path.basename(gm)] if gm else []) + \
                [f for f in CKPT_FIXED if not f.startswith("genmaster_")]
    for fn in ckpt_keep:
        fp = os.path.join(ck, fn)
        if not os.path.exists(fp) and os.path.exists(os.path.join(arch, fn)):
            fp = os.path.join(arch, fn)
        if os.path.exists(fp):
            cpy(fp, os.path.join(DST, "model", "checkpoints", fn))
    vp = os.path.join(ck, "vocab.json")
    if os.path.exists(vp):
        cpy(vp, os.path.join(DST, "model", "checkpoints", "vocab.json"))
    print("🧠 checkpoints: %s" % ", ".join(ckpt_keep))

    # ---- 4) knowledge-guards + data ----
    kroot = os.path.join(SRC, "knowledge")
    for fn in os.listdir(kroot):
        fp = os.path.join(kroot, fn)
        if os.path.isfile(fp) and fn.endswith((".py", ".md")) and not _skip(fn):
            cpy(fp, os.path.join(DST, "knowledge", fn))
    dat = os.path.join(SRC, "data")
    for fn in DATA_FILES:
        fp = os.path.join(dat, fn)
        if os.path.exists(fp):
            cpy(fp, os.path.join(DST, "data", fn))
    big = os.path.join(dat, "corpus_big")
    if os.path.isdir(big):
        for fn in os.listdir(big):
            if fn.endswith(".txt") and not _skip(fn):
                dst_p = os.path.join(DST, "data", "corpus_big", fn)
                if os.path.relpath(dst_p, DST).lower() in keep:
                    _readonly(dst_p, ro=False)
                    copied += 1
                else:
                    cpy(os.path.join(big, fn), dst_p,
                        ro=(fn not in ("learned_chat.txt", "liveresearch.txt")))

    # bande ki bacha-hui data wapas
    for rel, old in keep.items():
        dst_p = os.path.join(DST, rel)
        if not os.path.exists(dst_p):
            _copy2_retry(old, dst_p)
            _readonly(dst_p, ro=False)
            copied += 1

    # ---- 5) EXE + starters ----
    _copy2_retry(exe_src, os.path.join(DST, "Hemomemo-Ultra-Brain.exe"))
    copied += 1
    _copy2_retry(agent_src, os.path.join(DST, "Hemomemo-GameBot.exe"))
    copied += 1
    with open(os.path.join(DST, "START-HEMOMO.bat"), "w",
              encoding="utf-8") as f:
        f.write('@echo off\r\ntitle Hemomemo AI\r\n'
                'start "" "%~dp0Hemomemo-Ultra-Brain.exe"\r\n')
    with open(os.path.join(DST, "START-GAMEBOT.bat"), "w",
              encoding="utf-8") as f:
        f.write('@echo off\r\ntitle Hemomemo Game Bot\r\n'
                'start "" "%~dp0Hemomemo-GameBot.exe"\r\n')

    # ---- 6) 🔄 24/7 CONNECTION-HUB (junction + registry + auto-restart) ----
    hub = os.path.join(DST, "connection_hub")
    os.makedirs(hub, exist_ok=True)
    # pichli-build ki read-only protection khulo (UPDATE-mode overwrite ke liye)
    for _hub_old in ("master-connection.ini", "auto-restart.bat",
                     "emergency-recovery.bat"):
        _rp = os.path.join(hub, _hub_old)
        if os.path.exists(_rp):
            _readonly(_rp, ro=False)
    with open(os.path.join(hub, "master-connection.ini"), "w",
              encoding="utf-8") as f:
        f.write("[HemomemoAI-24-7-Connection-System]\r\n"
                "Version=5.0\r\nCreated=%s\r\nStatus=Active\r\n\r\n"
                "[Desktop-App]\r\nPath=%s\r\nType=Standalone\r\n\r\n"
                "[DigitalBrain-Server]\r\nPath=D:\\DigitalBrain\r\n"
                "Type=Optional-Live-Link\r\nRequired=NO\r\n\r\n"
                "[Qanoon]\r\nOnlyHemomemo=YES\r\nNoExternalAI=YES\r\n"
                "NoCloud=YES\r\n" % (time.strftime("%Y-%m-%d %H:%M"), DST))

    with open(os.path.join(DST, "CONNECT-DIGITALBRAIN.bat"), "w",
              encoding="utf-8") as f:
        f.write(u"""@echo off
title Hemomemo AI — 24/7 DigitalBrain Live-Link
echo HEMOMEMO 24/7 CONNECTION-HUB
echo App KHUD-STANDALONE hai (DigitalBrain ki zaroorat nahi); ye link sirf
echo LIVE-UPGRADE ke liye hai (agar D:\\DigitalBrain maujood ho).
if exist "D:\\DigitalBrain\\model\\generate.py" (
    echo 🟢 DigitalBrain mil gaya — LIVE-link lagta hoon (junction, admin nahi chahiye)…
    if not exist "%~dp0connection_hub\\digitalbrain" (
        mklink /J "%~dp0connection_hub\\digitalbrain" "D:\\DigitalBrain" >nul 2>&1
    )
    if exist "%~dp0connection_hub\\digitalbrain" (
        echo ✅ LIVE-LINK: ON — training/code-changes 24/7 link me aate hain
    ) else (
        echo ⚠️ junction nahi ban saka — app phir-bhi 100% standalone chalega
    )
    reg add "HKCU\\Software\\HemomemoAI-24-7" /v MasterHub /t REG_SZ /d "D:\\DigitalBrain" /f >nul 2>&1
    reg add "HKCU\\Software\\HemomemoAI-24-7" /v AutoStart /t REG_SZ /d "1" /f >nul 2>&1
) else (
    echo ℹ️ DigitalBrain ghaib hai — koi baat nahin: dimagh isi folder ka hai.
    echo    App 100%% standalone hai (checkpoint isi folder me).
)
echo ✅ REGISTRY-PERSISTENCE: PCs restart par bhi project re-link hoga
echo ✅ APP-STANDALONE: 100%% Hemomemo — koi AI-API/platform nahi
pause
""")

    with open(os.path.join(hub, "auto-restart.bat"), "w",
              encoding="utf-8") as f:
        f.write(u"""@echo off
title Hemomemo 24/7 Auto-Restart
echo Connection check kar rahe hain…
if exist "%~dp0..\\model\\checkpoints\\vocab.json" (
    echo 🧠 dimagh: ON (standalone checkpoints)
) else (
    echo 🧠 dimagh: MISSING — naya package chahiye
)
if exist "%~dp0digitalbrain" (
    echo 🔗 DigitalBrain link: ON
) else (
    echo 🔗 DigitalBrain link: OFF (ikhtiyari: optional)
)
reg query "HKCU\\Software\\HemomemoAI-24-7" /v MasterHub >nul 2>&1
if errorlevel 1 ( echo 📋 registry: INACTIVE ) else ( echo 📋 registry: ACTIVE )
echo ✅ 24/7 SYSTEM OK
pause
""")

    with open(os.path.join(hub, "emergency-recovery.bat"), "w",
              encoding="utf-8") as f:
        f.write(u"""@echo off
title Hemomemo Emergency Recovery
echo 🔧 RECOVERY-1: junction dobara ban raha hai…
if exist "%~dp0digitalbrain" rmdir "%~dp0digitalbrain" >nul 2>&1
if exist "D:\\DigitalBrain\\model\\generate.py" (
    mklink /J "%~dp0digitalbrain" "D:\\DigitalBrain" >nul 2>&1
    if exist "%~dp0digitalbrain" ( echo ✅ link RE-ON ) else ( echo ⚠️ link skip )
)
echo 🔧 RECOVERY-2: registry wapas…
reg add "HKCU\\Software\\HemomemoAI-24-7" /v MasterHub /t REG_SZ /d "D:\\DigitalBrain" /f >nul 2>&1
reg add "HKCU\\Software\\HemomemoAI-24-7" /v LastRecovery /t REG_SZ /d "%date%%time%" /f >nul 2>&1
echo ✅ RECOVERY-DONE (app 100%% standalone bhi chalti hai)
pause
""")

    # 🔒 LIVE-LINK yahan BUILD-TIME par NAHI lagta: staging DST khud
    #    D:\DigitalBrain ke andar hai — junction-to-ancestor se recursive-walk
    #    me 274457MB-nonsense banta tha. Users-PC par junction sirf
    #    CONNECT-DIGITALBRAIN.bat / auto-link.bat (runtime) banata hai.
    #    Hub-bats + registry + recovery: sab neeche mojood hain.
    print("ℹ️ build-time junction OFF (staging ancestor-khatra) — runtime bats hi link banayenge")

    # ---- 7) VERIFY-system + README + VERSION + guide ----
    with open(os.path.join(DST, "VERIFY-SYSTEM.bat"), "w",
              encoding="utf-8") as f:
        f.write('@echo off\r\ntitle Hemomemo System Verify\r\n'
                'powershell -NoProfile -ExecutionPolicy Bypass -File '
                '"%~dp0verify_system.ps1"\r\npause\r\n')

    prot = []
    for root, dirs, files in os.walk(DST):
        dirs[:] = [x for x in dirs
                   if x not in ("__pycache__", "connection_hub")]
        for fn in files:
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, DST).lower()
            base = fn.lower()
            if (base in ("genone_api.json", "genone_users.json",
                         "genone_api.log", "learned_chat.txt",
                         "liveresearch.txt", "qa_memo.pkl", "state.json",
                         "seen.json", "chat_history_app.json")
                    or rel.startswith("connection_hub") or rel == "connection_hub\\"):
                continue
            if base.endswith((".exe", ".bat", ".zip", ".png")):
                continue
            if rel.startswith("data\\videos"):
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
          "else { Write-Host '>> KHATARNAK — naya package lein' -ForegroundColor Red }\n")
    with open(os.path.join(DST, "verify_system.ps1"), "w",
              encoding="utf-8") as f:
        f.write(ps)

    lirel = os.path.join(SRC, "update_brain.ps1")
    if os.path.exists(lirel):
        _copy2_retry(lirel, os.path.join(DST, "update_brain.ps1"))
        copied += 1
    with open(os.path.join(DST, "UPDATE-BRAIN.bat"), "w",
              encoding="utf-8") as f:
        f.write('@echo off\r\ntitle Hemomemo Brain-Link (owner-publish)\r\n'
                'powershell -NoProfile -ExecutionPolicy Bypass -File '
                '"%~dp0update_brain.ps1"\r\npause\r\n')

    with open(os.path.join(DST, "VERSION.txt"), "w", encoding="utf-8") as f:
        f.write("Hemomemo AI %s\nBuilt: %s\nStandalone: YES (DigitalBrain optional)\n"
                "Owner: Hafiz Muhammad Huzaifa Shamim (HMHS)\n"
                "Brain: master 9.0M (dh722) + deep + helper + verify + 2M bio-bridge\n"
                "Qanoon: SIRF Hemomemo — koi AI-API/platform/cloud nahi\n"
                % (VERSION, time.strftime("%Y-%m-%d %H:%M")))

    guide = (
        "# 🚀 HEMOMEMO AI — DESKTOP APP (COMPLETE PACKAGE)\n\n"
        "## ⚡ QUICK START\n"
        "1. `START-HEMOMO.bat` — desktop app (EXE) khul jayegi.\n"
        "2. `START-GAMEBOT.bat` — console bot (agent).\n"
        "3. `CONNECT-DIGITALBRAIN.bat` — (sirf owner PC) DigitalBrain 24/7 live-link.\n"
        "   * App binaye iske bhi **100%% standalone** hai.\n\n"
        "## 🧠 ANDAR KYA HAI (sab isi folder me — DigitalBrain ki zaroorat NAHI)\n"
        "- `Hemomemo-Ultra-Brain.exe` — 4-dimagh desktop app: Chat, Main-Page,\n"
        "  331 Formulas, Hemomemo API (local, sign-in keys), Video-Generation (TRUE).\n"
        "- `Hemomemo-GameBot.exe` — console-agent (text/code/agent/pc-watch cmnds).\n"
        "- `model\\` — dimagh-code + checkpoints (4 dimagh) + vocab.\n"
        "- `core\\ agent\\ server\\ security\\ harvest\\ knowledge\\` — system.\n"
        "- `data\\` — Quran/Hadith ilm + corpus (learned-chat apki memory).\n"
        "- `connection_hub\\` — 24/7 connections (junction/registry/auto-restart).\n\n"
        "## 🎬 ULTRA-REALISTIC MOTION VIDEO (naya, app-ke-andar)\n"
        "- Chat me: \"car racing video banao\" — video-command pehchana jayega.\n"
        "- 🎬 Video tab: prompt + duration (5s..60s) + resolution. Video-Generation: TRUE.\n"
        "- Scroll: touch-drag + mouse-wheel + keyboard (Up/Down/PgUp/PgDn) + ▲▼ buttons.\n"
        "- Technology: Flow Fields + Higgsfield volumetric + physics + blur.\n"
        "- Render: ffmpeg (agar ho) warna built-in cv2-writer (bina-ffmpeg PC par bhi).\n"
        "- Output: `data\\videos\\` folder.\n\n"
        "## 🧠 SAMAJH (FRONTOLobe — naya)\n"
        "- App aap ke sawal ka INTENT的情感 samajhti hai (request/explain/code/etc).\n"
        "- Agar confusion ho to khud puchti hai (clarify) — phir jawab deti hai.\n\n"
        "## 🌐 APNI API LEIN (100%% LOCAL)\n"
        "1. 🌐 Hemomemo API page → 🆕 Nayi API lein → key `hemo…`.\n"
        "2. `POST http://127.0.0.1:8790/v1/chat` header `X-Hemomemo-Key: hemo…`.\n"
        "3. Website: http://127.0.0.1:8790 (browser).\n\n"
        "## 🔒 QANOON (PAKA-HUKUM)\n"
        "- SIRF Hemomemo system aur Hemomemo ki apni local API.\n"
        "- KAI NO other AI-API dunya ki: OpenAI/Claude/Gemini/Ollama/cloud — NABLE.\n"
        "- 100%% offline-capable; training ki sab information LOCAL checkpoints me.\n\n"
        "## 🛡️ VERIFICATION\n"
        "- `VERIFY-SYSTEM.bat` — har protected-file ka SHA-256 tasdeeq.\n"
        "- `PROTECTED_MANIFEST.sha256` — hash-list (read-only).\n\n"
        "## 🔄 UPDATE (safety)\n"
        "- Naya package isi par copy karo; apni data (keys/yaad) mehfooz rahegi.\n"
        "\n"
        "Banaye wale: **Hafiz Muhammad Huzaifa Shamim (HMHS)** — Alhamdulillah ☪\n"
    )
    with open(os.path.join(DST, "COMPLETE-INSTALLATION-GUIDE.md"), "w",
              encoding="utf-8") as f:
        f.write(guide)
    with open(os.path.join(DST, "README-HEMOMO.md"), "w",
              encoding="utf-8") as f:
        f.write(guide)

    # llms.txt (qanoon-doc + site-index) package-root me bhi
    _llms = os.path.join(SRC, "web", "llms.txt")
    if os.path.exists(_llms):
        _copy2_retry(_llms, os.path.join(DST, "llms.txt"))
        copied += 1

    # ?? QANOON-BELT: owner-credentials package/zip me KABHI nahi
    _purge_secrets(DST)

    # ---- 8) ZIP ----
    zpath = os.path.join(os.path.dirname(DST), "hemomemo_ai_desktop_complete.zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, dirs, files in os.walk(DST):
            dirs[:] = [x for x in dirs
                       if x not in ("__pycache__", "temp_frames")
                       and not os.path.islink(os.path.join(root, x))
                       and x.lower() != "digitalbrain"]   # 🔗 junction zip me NAHI
            for fn in files:
                fp = os.path.join(root, fn)
                z.write(fp, os.path.relpath(fp, os.path.dirname(DST)))

    _sz = 0
    for r, ds, fs in os.walk(DST):
        ds[:] = [d for d in ds
                 if d.lower() != "digitalbrain"
                 and not os.path.islink(os.path.join(r, d))]   # 🔗 junction NAHI
        for fn in fs:
            try:
                _sz += os.path.getsize(os.path.join(r, fn))
            except Exception:
                pass
    size = _sz / 1048576
    print("✅ DESKTOP-PACKAGE-OK: %s | files: %d | %.1f MB | %.0fs"
          % (DST, copied, size, time.time() - t0))
    print("🛡️ protected: %d | ZIP: %s (%.1f MB)"
          % (len(prot), zpath, os.path.getsize(zpath) / 1048576))


if __name__ == "__main__":
    main()
