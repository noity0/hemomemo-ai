#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CLEAN PUSH - publish latest source to GitHub main + gh-pages
============================================================
Why this exists:
  The repo history contains 190 MB .npz checkpoints and 356 MB .zip files.
  GitHub hard-rejects any push with a file > 100 MB, so `git push master:main`
  can never succeed. Fix: build ONE clean commit (orphan, no parents) from the
  current working tree, excluding big binaries, and force-push that as main.

  The .zip is NOT needed in git: every download link on the site points at
  the GitHub Release asset (v4.2.1-people), which is uploaded separately.

Also pushes gh-pages (site) from web_surge/ with the same clean technique.

Usage:  python D:\DigitalBrain\clean_push_main.py
"""

import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:\DigitalBrain")
REPO = "noity0/hemomemo-ai"
MAX_MB = 90.0

IGNORE_EXTRA = """
# ── publishing: never commit ship-artifacts / model weights ──
*.zip
*.npz
*.exe
*.mp4
*.7z
*.iso
model/checkpoints/
data/corpus_big/_unfiltered/
data/corpus_big/_old_broken/
.data_pages/
"""


def log(m):
    print(m, flush=True)


def run(args, cwd=ROOT, timeout=600, check=False, env=None):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True, text=True,
                       timeout=timeout, encoding="utf-8", errors="replace", env=env)
    if check and r.returncode != 0:
        raise RuntimeError("%s\n%s\n%s" % (" ".join(args), r.stdout[-800:], r.stderr[-800:]))
    return r


# ─────────────────────────────────────────────────────────── helpers
def strip_big_from_index():
    """Unstage any file whose on-disk size exceeds MAX_MB."""
    listing = run(["git", "diff", "--cached", "--name-only", "-z"]).stdout
    names = [n for n in listing.split("\0") if n]
    big = []
    for name in names:
        p = ROOT / name
        try:
            if p.is_file() and p.stat().st_size > MAX_MB * 1024 * 1024:
                big.append((name, p.stat().st_size))
        except OSError:
            pass
    if big:
        log("  removing %d oversized file(s) from the commit:" % len(big))
        for name, size in big:
            log("    - %-70s %7.1f MB" % (name, size / 1048576.0))
            run(["git", "rm", "--cached", "--ignore-unmatch", "--", name])
    return len(big)


def make_clean_commit(message):
    """Build an orphan commit from the current index (working tree untouched)."""
    tree = run(["git", "write-tree"], check=True).stdout.strip()
    c = run(["git", "commit-tree", tree, "-m", message], check=True)
    return c.stdout.strip()


def gh_pages_commit():
    """One-commit gh-pages tree from web_surge/ (never touches the worktree)."""
    src = ROOT / "web_surge"
    if not src.exists():
        raise RuntimeError("web_surge/ missing")

    stage = ROOT / ".data_pages"
    if stage.exists():
        shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)

    for item in src.iterdir():
        if item.name.lower().endswith((".zip", ".exe", ".npz", ".mp4")):
            continue                      # never ship binaries through Pages
        dst = stage / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)

    (stage / ".nojekyll").write_text("", encoding="utf-8")

    # temp index so the real index/branch state is untouched
    idx = ROOT / ".pages_index"
    if idx.exists():
        idx.unlink()
    env = dict(os.environ, GIT_INDEX_FILE=str(idx))

    def g(args, **kw):
        return subprocess.run(["git"] + args, cwd=str(ROOT), env=env,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", **kw)

    g(["add", "-A", "--", "."])
    tree = g(["write-tree"])
    if tree.returncode != 0:
        raise RuntimeError("write-tree: " + tree.stderr[:400])
    c = g(["commit-tree", tree.stdout.strip(), "-m", "GitHub Pages (auto publish)"])
    if c.returncode != 0:
        raise RuntimeError("commit-tree: " + c.stderr[:400])
    sha = c.stdout.strip()

    try:
        idx.unlink()
    except OSError:
        pass
    shutil.rmtree(stage, ignore_errors=True)
    return sha


# ─────────────────────────────────────────────────────────── main
def main():
    log("=" * 62)
    log("CLEAN PUSH -> origin/main  (+ gh-pages)")
    log("=" * 62)

    if not (ROOT / ".git").exists():
        log("ERROR: not a git repo")
        return 1

    # 0) drop redundant copies of the big zip from the deploy folders
    for dup in (ROOT / "web" / "HemomemoUltra-People.zip",
                ROOT / "web_surge" / "HemomemoUltra-People.zip"):
        if dup.exists():
            dup.unlink()
            log("removed duplicate %s" % dup)

    # 1) extend .gitignore
    gi = ROOT / ".gitignore"
    txt = gi.read_text(encoding="utf-8", errors="replace") if gi.exists() else ""
    if "never commit ship-artifacts" not in txt:
        gi.write_text(txt.rstrip() + "\n" + IGNORE_EXTRA, encoding="utf-8")
        log("updated .gitignore")

    # 2) rebuild the index from scratch against the working tree
    log("rebuilding index ...")
    run(["git", "rm", "-r", "--cached", ".", "-q"])
    run(["git", "add", "-A", "."])
    n = strip_big_from_index()
    log("staged files: %d (dropped %d oversized)" % (
        len([x for x in run(["git", "diff", "--cached", "--name-only"]).stdout.splitlines() if x]), n))

    # 3) orphan commit
    sha = make_clean_commit("Hemomemo AI - latest source (clean publish, no binaries)")
    log("clean commit: %s" % sha[:12])

    # 4) keep the old history reachable locally, then move master to the clean commit
    run(["git", "branch", "-f", "old-history", sha])  # placeholder, replaced below
    old = run(["git", "rev-parse", "master"]).stdout.strip()
    run(["git", "branch", "-f", "old-history", old])
    run(["git", "update-ref", "refs/heads/master", sha])
    run(["git", "reset", "-q", "--mixed", "HEAD"])
    log("local master -> clean commit (old history kept in branch old-history)")

    # 5) push
    log("pushing main ...")
    r = run(["git", "push", "--force", "origin", "%s:refs/heads/main" % sha], timeout=1800)
    ok_main = r.returncode == 0
    log("  main: %s" % ("OK" if ok_main else "FAIL -> " + (r.stderr or r.stdout).strip()[:400]))

    log("building gh-pages ...")
    try:
        psha = gh_pages_commit()
        r2 = run(["git", "push", "--force", "origin", "%s:refs/heads/gh-pages" % psha], timeout=900)
        ok_pages = r2.returncode == 0
        log("  gh-pages: %s" % ("OK" if ok_pages else "FAIL -> " + (r2.stderr or r2.stdout).strip()[:400]))
    except Exception as e:
        ok_pages = False
        log("  gh-pages FAIL: %s" % e)

    # 6) verify
    log("verifying remote refs ...")
    ls = run(["git", "ls-remote", "--heads", "origin"], timeout=180)
    want_main = sha
    want_pages = None
    for line in ls.stdout.splitlines():
        if line.endswith("refs/heads/main"):
            log("  remote main     = %s %s" % (line.split()[0][:12],
                                              "MATCH" if line.startswith(want_main) else "MISMATCH"))
        if line.endswith("refs/heads/gh-pages"):
            want_pages = line.split()[0]
            log("  remote gh-pages = %s" % want_pages[:12])

    log("")
    log("DONE  main=%s  gh-pages=%s" % ("OK" if ok_main else "FAIL",
                                       "OK" if ok_pages else "FAIL"))
    return 0 if (ok_main and ok_pages) else 1


if __name__ == "__main__":
    sys.exit(main())
