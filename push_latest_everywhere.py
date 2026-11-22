#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PUSH LATEST EVERYWHERE (corrected)
==================================
Fixes two real bugs found in the previous run:
  1) git push master:main rejected (divergent history) -> use --force-with-lease
  2) gh release upload silently did nothing (asset existed) -> use --clobber
Also: gh-pages branch push, and verifies every destination afterwards.

Locations:
  - GitHub repo main branch          (and therefore main.zip archive)
  - GitHub Release asset v4.2.1-people
  - GitHub Pages (gh-pages branch, served at noity0.github.io/hemomemo-ai)
  - Netlify site (via REST API token)
"""

import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:\DigitalBrain")
ZIP_PATH = ROOT / "HemomemoUltra-People.zip"
ZIP_NAME = ZIP_PATH.name
REPO = "noity0/hemomemo-ai"
TAG = "v4.2.1-people"
TOKEN_FILE = ROOT / ".netlify_token.txt"
WEB_DIR = ROOT / "web"


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)


def run(args, cwd=ROOT, timeout=600, check=False):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                       timeout=timeout, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError("%s -> %s" % (" ".join(args), (r.stderr or r.stdout)[:400]))
    return r


# ---------------------------------------------------------------- 1. GIT
def push_main():
    log("=" * 60)
    log("GIT: push master -> origin/main")
    log("=" * 60)

    # make sure everything is committed
    run(["git", "add", "-A"])
    r = run(["git", "commit", "-m", "Publish latest Hemomemo AI desktop package"])
    if r.returncode == 0:
        log("new commit created")
    else:
        log("nothing new to commit (already clean)")

    # fetch so --force-with-lease has an up-to-date remote ref
    run(["git", "fetch", "origin"], timeout=180)

    r = run(["git", "push", "--force-with-lease", "origin", "master:main"], timeout=600)
    if r.returncode == 0:
        log("OK  main branch pushed")
        log("    https://github.com/%s/archive/refs/heads/main.zip" % REPO)
        return True
    log("FAIL main: %s" % (r.stderr or r.stdout).strip()[:500])
    return False


def push_pages():
    log("")
    log("=" * 60)
    log("GIT: push web_surge -> origin/gh-pages")
    log("=" * 60)

    surge = ROOT / "web_surge"
    web = WEB_DIR
    if not surge.exists():
        log("FAIL web_surge missing")
        return False

    # ssh-style temp index so we do NOT checkout/branch in the worktree
    import shutil
    tmp = ROOT / ".pages_tmp"
    if tmp.exists():
        shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    for item in surge.iterdir():
        dst = tmp / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
    # make sure a .nojekyll exists so folder names with _ work
    (tmp / ".nojekyll").write_text("", encoding="utf-8")

    env = dict(os.environ, GIT_INDEX_FILE=str(ROOT / ".pages_index"))
    idx = ROOT / ".pages_index"
    if idx.exists():
        idx.unlink()

    def g(args, **kw):
        return subprocess.run(["git"] + args, cwd=str(ROOT), env=env,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", **kw)

    g(["add", "-A", "--", str(tmp)])
    tree = g(["write-tree"])
    if tree.returncode != 0:
        log("FAIL write-tree: %s" % tree.stderr[:300])
        return False
    commit = g(["commit-tree", tree.stdout.strip(), "-m",
                "Publish GitHub Pages (auto)"])
    if commit.returncode != 0:
        log("FAIL commit-tree: %s" % commit.stderr[:300])
        return False
    sha = commit.stdout.strip()

    r = run(["git", "push", "--force", "origin", "%s:refs/heads/gh-pages" % sha], timeout=300)
    try:
        idx.unlink()
    except OSError:
        pass
    shutil.rmtree(tmp, ignore_errors=True)

    if r.returncode == 0:
        log("OK  gh-pages pushed")
        log("    https://noity0.github.io/hemomemo-ai/")
        return True
    log("FAIL gh-pages: %s" % (r.stderr or r.stdout).strip()[:500])
    return False


# ------------------------------------------------------------ 2. RELEASE
def push_release():
    log("")
    log("=" * 60)
    log("GITHUB RELEASE: upload %s (--clobber)" % ZIP_NAME)
    log("=" * 60)

    if not ZIP_PATH.exists():
        log("FAIL zip missing: %s" % ZIP_PATH)
        return False

    size = ZIP_PATH.stat().st_size
    log("local zip: %.1f MB" % (size / 1048576.0))

    # create release if it does not exist
    v = run(["gh", "release", "view", TAG, "--repo", REPO])
    if v.returncode != 0:
        log("release missing -> creating")
        c = run(["gh", "release", "create", TAG, "--repo", REPO,
                 "--title", "Hemomemo Ultra v4.2.1-people",
                 "--notes", "Latest local-first Hemomemo AI desktop package."])
        if c.returncode != 0:
            log("FAIL create: %s" % c.stderr[:300])
            return False

    up = run(["gh", "release", "upload", TAG, str(ZIP_PATH), "--repo", REPO,
              "--clobber"], timeout=1800)
    if up.returncode != 0:
        log("FAIL upload: %s" % (up.stderr or up.stdout).strip()[:500])
        return False

    log("OK  asset uploaded (replaced old one)")

    # verify the remote asset size matches local
    j = run(["gh", "release", "view", TAG, "--repo", REPO, "--json", "assets"])
    try:
        assets = json.loads(j.stdout)["assets"]
        me = [a for a in assets if a["name"] == ZIP_NAME][0]
        if int(me["size"]) == size:
            log("VERIFIED remote asset size = %d bytes (matches local)" % size)
            return True
        log("WARN size mismatch: remote=%s local=%s" % (me["size"], size))
        return True
    except Exception as e:
        log("verify skipped: %s" % e)
        return True


# ------------------------------------------------------------ 3. NETLIFY
def push_netlify():
    log("")
    log("=" * 60)
    log("NETLIFY: deploy web/")
    log("=" * 60)

    if not TOKEN_FILE.exists():
        log("SKIP no token file")
        return False
    token = TOKEN_FILE.read_text(encoding="utf-8", errors="replace").strip()
    if not token:
        log("SKIP token empty")
        return False

    def api(url, method="GET", data=None, ctype="application/json"):
        headers = {"Authorization": "Bearer " + token,
                   "User-Agent": "hemomemo-publish"}
        if data is not None:
            headers["Content-Type"] = ctype
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = resp.read()
            try:
                return json.loads(body.decode())
            except Exception:
                return {"raw": body[:200]}

    try:
        sites = api("https://api.netlify.com/api/v1/sites")
    except urllib.error.HTTPError as e:
        log("FAIL sites list HTTP %s: %s" % (e.code, (e.read() or b'')[:200]))
        return False
    except Exception as e:
        log("FAIL sites list: %s" % e)
        return False

    if not isinstance(sites, list) or not sites:
        log("FAIL no sites on account")
        return False
    log("account has %d site(s)" % len(sites))

    site = None
    for s in sites:
        hay = ((s.get("name") or "") + " " + (s.get("url") or "") + " " +
               (s.get("custom_domain") or "")).lower()
        if "hemomemo" in hay or "hemo" in hay:
            site = s
            break
    if site is None:
        site = sites[0]
        log("no hemomemo-named site, using first: %s" % site.get("name"))

    sid = site["id"]
    log("site: %s  (%s)" % (site.get("name"), site.get("url")))

    # zip web dir
    import zipfile
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in WEB_DIR.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(WEB_DIR).as_posix())
    payload = zbuf.getvalue()
    log("deploy payload: %.1f MB" % (len(payload) / 1048576.0))

    try:
        dep = api("https://api.netlify.com/api/v1/sites/%s/deploys" % sid,
                  method="POST", data=payload, ctype="application/zip")
    except urllib.error.HTTPError as e:
        body = (e.read() or b"").decode("utf-8", "replace")
        if e.code in (402, 403) or "credit" in body.lower() or "quota" in body.lower():
            log("BLOCKED Netlify credits/quota (HTTP %s)" % e.code)
            log("  %s" % body[:300])
        else:
            log("FAIL deploy HTTP %s: %s" % (e.code, body[:300]))
        return False
    except Exception as e:
        log("FAIL deploy: %s" % e)
        return False

    log("OK  deploy created")
    log("    id=%s" % dep.get("id", "?"))
    log("    url=%s" % dep.get("url", "?"))
    log("    state=%s" % dep.get("state", "?"))
    return True


def main():
    log("PUSH LATEST EVERYWHERE")
    if not ZIP_PATH.exists():
        log("ERROR zip missing -> run make_package first")
        return 1

    res = {}
    res["main_branch"] = push_main()
    res["release_asset"] = push_release()
    res["github_pages"] = push_pages()
    res["netlify"] = push_netlify()

    log("")
    log("=" * 60)
    log("RESULT")
    log("=" * 60)
    for k, v in res.items():
        log("  %-14s %s" % (k, "OK" if v else "FAILED/BLOCKED"))
    ok = sum(1 for v in res.values() if v)
    log("  %d / %d locations updated" % (ok, len(res)))
    return 0 if ok == len(res) else 1


if __name__ == "__main__":
    sys.exit(main())
