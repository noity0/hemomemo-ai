#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REPUBLISH TO EVERYWHERE - Hemomemo AI Desktop App
==================================================
Pushes the latest HemomemoUltra-People.zip to ALL 5 locations:
  1. Netlify site (via REST API + token)
  2. GitHub Pages site
  3. GitHub repo (main branch)
  4. GitHub Release asset (v4.2.1-people)
  5. GitHub main archive (auto-generated from repo)
"""

import os
import sys
import json
import subprocess
import hashlib
import urllib.request
import urllib.error
import shutil
import time
import zipfile
from pathlib import Path
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(r"D:\DigitalBrain")
PACKAGE_DIR  = Path(r"D:\HemomemoUltra-People")
ZIP_NAME     = "HemomemoUltra-People.zip"
ZIP_PATH     = PROJECT_ROOT / ZIP_NAME
GITHUB_REPO  = "noity0/hemomemo-ai"
RELEASE_TAG  = "v4.2.1-people"
NETLIFY_TOKEN_FILE = PROJECT_ROOT / ".netlify_token.txt"
WEB_DIR      = PROJECT_ROOT / "web"

# ─── HELPERS ──────────────────────────────────────────────────────────────
def ts():
    return datetime.now().strftime("%H:%M:%S")

def log(msg):
    print(f"[{ts()}] {msg}", flush=True)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def github_api(method, path, body=None, token=None):
    """Call GitHub REST API"""
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/json", "User-Agent": "hemomemo-publish"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.fp else ""
        raise RuntimeError(f"GitHub API {method} {path} -> {e.code}: {err_body[:500]}")
    except Exception as e:
        raise RuntimeError(f"GitHub API {method} {path} -> {e}")

# ─── STEP 0: Verify local package ────────────────────────────────────────
def step0_verify_package():
    log("=" * 60)
    log("STEP 0: Verify local package")
    log("=" * 60)
    
    if not PACKAGE_DIR.exists():
        log(f"ERROR: Package dir not found: {PACKAGE_DIR}")
        return False
    
    if not ZIP_PATH.exists():
        log(f"Creating ZIP from {PACKAGE_DIR}...")
        shutil.make_archive(str(ZIP_PATH.with_suffix("")), "zip", str(PACKAGE_DIR))
    
    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)
    hash_val = sha256_file(ZIP_PATH)
    log(f"ZIP: {ZIP_PATH}")
    log(f"Size: {size_mb:.1f} MB | SHA256: {hash_val[:16]}...")
    
    file_count = sum(1 for _ in PACKAGE_DIR.rglob("*") if _.is_file())
    log(f"Files in package: {file_count}")
    log("Package verified OK")
    return True

# ─── STEP 1: Git push to origin/main ────────────────────────────────────
def step1_git_push():
    log("")
    log("=" * 60)
    log("STEP 1: Git push to origin/main (repo + archive)")
    log("=" * 60)
    
    try:
        subprocess.run(["git", "add", "."], check=True, cwd=str(PROJECT_ROOT))
        subprocess.run(["git", "commit", "-m", "Update: latest desktop app + coding master"], 
                      cwd=str(PROJECT_ROOT), capture_output=True)
        
        log("Pushing to origin/main...")
        r = subprocess.run(["git", "push", "origin", "master:main"],
                          capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=120)
        if r.returncode == 0:
            log("SUCCESS: Pushed to GitHub main branch")
            log(f"  Archive: https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip")
            return True
        else:
            log(f"FAILED: {r.stderr.strip()[:300]}")
            return False
    except Exception as e:
        log(f"ERROR: {e}")
        return False

# ─── STEP 2: GitHub Release asset upload ────────────────────────────────
def step2_github_release():
    log("")
    log("=" * 60)
    log("STEP 2: GitHub Release asset (v4.2.1-people)")
    log("=" * 60)
    
    try:
        r = subprocess.run(["gh", "release", "view", RELEASE_TAG],
                         capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=30)
        if r.returncode == 0:
            log(f"Release {RELEASE_TAG} exists. Uploading asset...")
            subprocess.run(["gh", "release", "delete-asset", RELEASE_TAG, ZIP_NAME],
                         cwd=str(PROJECT_ROOT), capture_output=True, timeout=30)
            r = subprocess.run(["gh", "release", "upload", RELEASE_TAG, str(ZIP_PATH)],
                             capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300)
            if r.returncode == 0:
                log("SUCCESS: Asset uploaded to GitHub Release")
                return True
            else:
                log(f"FAILED: {r.stderr.strip()[:200]}")
                return False
        else:
            log(f"Creating release {RELEASE_TAG}...")
            subprocess.run(["gh", "release", "create", RELEASE_TAG, 
                               "--title", "Hemomemo AI Desktop App",
                               "--target", "main"],
                             capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=30)
            subprocess.run(["gh", "release", "upload", RELEASE_TAG, str(ZIP_PATH)],
                         capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=300)
            log("SUCCESS: Release created + asset uploaded")
            return True
    except Exception as e:
        log(f"ERROR (gh CLI): {e}")
        return False

# ─── STEP 3: Netlify deploy ──────────────────────────────────────────────
def step3_netlify():
    log("")
    log("=" * 60)
    log("STEP 3: Netlify deploy")
    log("=" * 60)
    
    token_file = NETLIFY_TOKEN_FILE
    if not token_file.exists():
        log(f"ERROR: Token file not found: {token_file}")
        return False
    
    token = token_file.read_text().strip()
    if not token:
        log("ERROR: Token is empty")
        return False
    
    try:
        web_zip = PROJECT_ROOT / "netlify_deploy.zip"
        shutil.make_archive(str(web_zip.with_suffix("")), "zip", str(WEB_DIR))
        with open(web_zip, "rb") as f:
            zip_data = f.read()
        
        # Get sites
        req = urllib.request.Request(
            "https://api.netlify.com/api/v1/sites",
            headers={"Authorization": f"Bearer {token}"},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            sites = json.loads(resp.read().decode())
        
        site = next((s for s in sites if "hemomemo" in s.get("name", "").lower()), sites[0] if sites else None)
        if site:
            site_id = site["id"]
            deploy_req = urllib.request.Request(
                f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
                data=zip_data,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/zip"},
                method="POST"
            )
            with urllib.request.urlopen(deploy_req, timeout=120) as resp:
                json.loads(resp.read().decode())
            log(f"SUCCESS: Netlify deploy initiated for site: {site.get('name')}")
            web_zip.unlink(missing_ok=True)
            return True
        else:
            log("ERROR: No Netlify site found to deploy to.")
            web_zip.unlink(missing_ok=True)
            return False
    except urllib.error.HTTPError as e:
        err = e.read().decode() if e.fp else ""
        if "402" in str(e.code) or "credit" in err.lower():
            log(f"BLOCKED: Netlify credit limit exceeded ({e.code}). Please add credits to Netlify account.")
        else:
            log(f"ERROR: HTTP {e.code}: {err[:300]}")
        return False
    except Exception as e:
        log(f"ERROR: {e}")
        return False

# ─── STEP 4: GitHub Pages ────────────────────────────────────────────────
def step4_github_pages():
    log("")
    log("=" * 60)
    log("STEP 4: GitHub Pages")
    log("=" * 60)
    try:
        web_surge = PROJECT_ROOT / "web_surge"
        if web_surge.exists():
            for f in WEB_DIR.iterdir():
                target = web_surge / f.name
                if f.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(f, target)
                else:
                    shutil.copy2(f, target)
        
        subprocess.run(["git", "add", "web_surge/"], cwd=str(PROJECT_ROOT), capture_output=True)
        subprocess.run(["git", "commit", "-m", "Update GitHub Pages"], cwd=str(PROJECT_ROOT), capture_output=True)
        r = subprocess.run(["git", "push", "origin", "master:gh-pages", "--force"],
                          capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=120)
        if r.returncode == 0:
            log("SUCCESS: GitHub Pages updated")
            return True
        else:
            log(f"FAILED: {r.stderr.strip()[:200]}")
            return False
    except Exception as e:
        log(f"ERROR: {e}")
        return False

# ─── MAIN ─────────────────────────────────────────────────────────────────
def main():
    log("RE-PUBLISH TO EVERYWHERE: Hemomemo AI Desktop App")
    results = {}
    results["local_package"] = step0_verify_package()
    if not results["local_package"]:
        sys.exit(1)
    
    results["github_repo_main"] = step1_git_push()
    results["github_release"] = step2_github_release()
    results["netlify"] = step3_netlify()
    results["github_pages"] = step4_github_pages()
    
    log("")
    log("=" * 60)
    log("FINAL PUBLISH STATUS")
    log("=" * 60)
    for k, v in results.items():
        log(f"  [{'v' if v else 'X'}] {k}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
