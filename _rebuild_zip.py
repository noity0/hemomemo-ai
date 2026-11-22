# -*- coding: utf-8 -*-
"""Hemomemo AI :: Rebuild ZIP package with latest v4 video engine and 13-stage cognitive flow."""
import os
import zipfile
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\DigitalBrain"
ZIP_PATH = os.path.join(ROOT, "hemomemo_ultra_latest.zip")

INCLUDE_DIRS = ["model", "agent", "core", "server", "app", "web", "knowledge", "harvest"]
INCLUDE_FILES = ["README.md", "requirements.txt", "Hemomemo-AI.bat", "brain_manifest.json"]

print("📦 Packaging Hemomemo AI Ultra-Max into hemomemo_ultra_latest.zip...")

with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for fname in INCLUDE_FILES:
        fpath = os.path.join(ROOT, fname)
        if os.path.exists(fpath):
            zf.write(fpath, fname)
            print(f"  + file: {fname}")
            
    for dname in INCLUDE_DIRS:
        dpath = os.path.join(ROOT, dname)
        if os.path.isdir(dpath):
            for root, dirs, files in os.walk(dpath):
                dirs[:] = [d for d in dirs if d != "__pycache__" and d != "corpus_big"]
                for file in files:
                    if file.endswith((".log", ".tmp", ".pyc", ".npz")):
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, ROOT)
                    zf.write(full_path, rel_path)
            print(f"  + folder: {dname}/")

print(f"✅ Success! Created: {ZIP_PATH}")
print(f"   Size: {os.path.getsize(ZIP_PATH) / 1024 / 1024:.2f} MB")
