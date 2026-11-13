# -*- coding: utf-8 -*-
r"""_apply_training_everywhere.py — TRAINING KE BAAD SAB JAGAH A→Z APPLY
(name, data, information — trained dimagh har jagah pahunchta hai):

  1) py scripts/make_package.py        → D:\HemomemoUltra-People (desktop app
     folder ROOT: naya checkpoint + NAYA EXE-verify + starter-files)
  2) py scripts/make_desktop_package.py → \hemomemo_ai_desktop (connection-hub
     + guide + VERIFY + zip)
  3) hemomemo_ai_complete_final.zip    → poore desktop-folder ka mukammal ZIP
  4) web\hemomemo zip copy             → release-upload assets tayyar
  5) _publish_final.ps1                → ZIP→GitHub-release + repo-push
     (agent+sites+qa700) + GitHub-PAGES build + Netlify deploy (hemomemo-ai.netlify.app)

Qanoon: 100% LOCAL chain — koi AI-API nahi (sirf apne git/netlify/gadh ka
apna upload-tareeqa jaisa pehle tha).
"""
import json
import os
import subprocess
import sys
import time
import zipfile

SRC = "D:\\DigitalBrain"
ROOTPKG = "D:\\HemomemoUltra-People"
LOG = os.path.join(SRC, "data", "_apply_training.log")


def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def run(cmd, cwd=None, timeout=7200, shell=False):
    log("▶ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd or SRC, timeout=timeout, shell=shell)
    log("  rc=%s" % r.returncode)
    return r.returncode == 0


def zdir(src_dir, zpath, skip_first=("web",)):
    """poore folder ka zip - *.zip aur __pycache__ chhoor kar."""
    # OWNER-CREDENTIALS (qanoon): zip me KABHI nahi - belt-and-suspenders
    _SECRETS = {
        "email_link.json", "api_keys.json", ".env", ".netlify_token.txt",
        "netlify_token.txt", "credentials.json", "secrets.json",
        "service_account.json", "client_secret.json", "owner_key.json",
        "token_store.json", "password.txt", "passwords.txt",
        "google_oauth.json", "gdrive_tokens.json"}
    if os.path.exists(zpath):
        os.remove(zpath)
    n = 0
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, dirs, files in os.walk(src_dir):
            _keep = []
            for d in dirs:
                if d in ("__pycache__", "temp_frames"):
                    continue
                # 🔗 junction/digitalbrain ke andar KABHI NAHI ghussna
                #    (warna poora D:\DigitalBrain zip me chala jata hai)
                if os.path.islink(os.path.join(root, d)) \
                        or d.lower() == "digitalbrain":
                    continue
                _keep.append(d)
            dirs[:] = _keep
            for fn in files:
                if fn.lower().endswith(".zip"):
                    continue               # zip-ghatchia (recursion) nahi
                _low = fn.lower()
                if _low in _SECRETS or _low.endswith(".token") \
                        or _low.endswith(".token.txt") or ".token." in _low:
                    continue               # owner-credentials zip me KABHI nahi
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, src_dir)
                z.write(fp, os.path.relpath(fp, os.path.dirname(src_dir)))
                n += 1
    return n


def main():
    ok = {}
    t0 = time.time()
    log("==== APPLY-EVERYWHERE SHURU (training ke baad) ====")

    # 1) root desktop-folder (D:\HemomemoUltra-People) — naya dimagh + EXE
    ok["make_package"] = run([sys.executable, "-Xutf8",
                              os.path.join(SRC, "scripts", "make_package.py")])

    # 2) hemomemo_ai_desktop subfolder (connection-hub + guide + zip)
    ok["make_desktop_package"] = run(
        [sys.executable, "-Xutf8",
         os.path.join(SRC, "scripts", "make_desktop_package.py")])

    # 🛑 IMANDARI-GUARD: agar koi package ban hi nahi rahi to aage MAT barho —
    # adhura zip/publish qanoon ke mutabiq risala nahi (purane salamat rehte)
    if not (ok.get("make_package") and ok.get("make_desktop_package")):
        log("❌ PACKAGE-FAIL — chain yahin RUKI (adhura zip/publish NAHI;"
            " purane zips/release salamat). Fix karke dobara chalao.")
        return

    # 3) poore desktop-folder ka mukammal zip (aap ka hukum: desktop folder
    #    + all files ek zip me — repo aur sites par jany wale)
    try:
        zpath = os.path.join(ROOTPKG, "hemomemo_ai_complete_final.zip")
        n = zdir(ROOTPKG, zpath)
        log("✅ ZIP: hemomemo_ai_complete_final.zip (%d files, %.1f MB)"
            % (n, os.path.getsize(zpath) / 1048576))
        ok["zip"] = True
    except Exception as e:
        log("❌ ZIP fail: %s" % e)
        ok["zip"] = False

    # 4) web-release asset copy (upload-zip ki purani jagah par)
    try:
        zsrc = os.path.join(ROOTPKG, "hemomemo_ai_complete_final.zip")
        zdst = os.path.join(SRC, "web", "HemomemoUltra-People.zip")
        import shutil
        shutil.copy2(zsrc, zdst)
        log("✅ web-zip copy: %s (%.1f MB)"
            % (zdst, os.path.getsize(zdst) / 1048576))
        ok["web_copy"] = True
    except Exception as e:
        log("❌ web-zip copy fail: %s" % e)
        ok["web_copy"] = False

    # 5) 🚀 PUBLISH: ZIP→release + repo-push + PAGES + NETLIFY (2 sites)
    ok["publish"] = run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", os.path.join(SRC, "_publish_final.ps1")])

    # 6) summary
    summary = {"when": time.strftime("%Y-%m-%d %H:%M:%S"),
               "took_min": (time.time() - t0) / 60.0,
               "results": ok,
               "all_ok": all(ok.values())}
    try:
        with open(os.path.join(SRC, "data", "_apply_training_summary.json"),
                  "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=1)
    except Exception:
        pass
    log("==== APPLY-DONE %s ====" % ("SAB OK ✅" if summary["all_ok"]
                                     else "kuch fail — upar log dekho"))

    # 7) 🔥 PENDING-9M: agar flag hai (user-ka-hukum) — master ko 9M-params
    #    (dh722) par upgrade-trainer khud launch karo (us ki aakhiri APPLY
    #    chain khud-ba-khud dobara sab jagah lagayegi)
    flag = os.path.join(SRC, "data", "_pending_9m.json")
    if os.path.exists(flag):
        try:
            os.remove(flag)                  # ek dafa hi chain (no-loop)
        except Exception:
            pass
        log("🔥 PENDING-9M dh paci mila — master 9M-parameters upgrade"
            " training launch (dh722 @ 180-min)…")
        try:
            lhand = open(os.path.join(SRC, "data", "_trainer_9m.log"),
                         "a", encoding="utf-8")
            env = {**os.environ, "TRAIN_DH": "722"}
            subprocess.Popen(
                [sys.executable, "-Xutf8",
                 os.path.join(SRC, "_train_deep5h.py")],
                cwd=SRC, stdout=lhand, stderr=subprocess.STDOUT,
                creationflags=subprocess.DETACHED_PROCESS |
                subprocess.CREATE_NEW_PROCESS_GROUP,
                env=env)
            lhand.close()
            log("🚀 9M-TRAINER khud chal padta hai (detached) — khatam par dobara"
                " APPLY-EVERYWHERE aap-k-hukum ke mutabiq khud hogi")
        except Exception as e:
            log("❌ 9M-launch FAIL: %s — py -3.12 _train_deep5h.py"
                " (TRAIN_DH=722) khud chalao" % e)


if __name__ == "__main__":
    main()
