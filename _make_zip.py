"""Build a complete ZIP of D:\\HemomemoUltra-People into D:\\DigitalBrain\\HemomemoUltra-People.zip.
Skips junctions/symlinks (connection_hub -> D:\\DigitalBrain), __pycache__, .git.
"""
import os
import stat
import zipfile
import sys

SRC = r"D:\HemomemoUltra-People"
OUT = r"D:\DigitalBrain\HemomemoUltra-People.zip"
TMP = r"D:\DigitalBrain\HemomemoUltra-People.tmp.zip"

SKIP_DIRS = {"__pycache__", ".git", "connection_hub"}


def is_reparse(path):
    try:
        st = os.lstat(path)
        if os.path.islink(path):
            return True
        attrs = getattr(st, "st_file_attributes", 0)
        return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    except OSError:
        return True


print(f"Zipping {SRC} -> {OUT}", flush=True)
count = 0
try:
    with zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, dirs, files in os.walk(SRC):
            keep = []
            for d in dirs:
                full = os.path.join(root, d)
                if d in SKIP_DIRS or is_reparse(full):
                    print(f"  SKIP-DIR {os.path.relpath(full, SRC)}", flush=True)
                    continue
                keep.append(d)
            dirs[:] = keep
            for f in files:
                full = os.path.join(root, f)
                if is_reparse(full):
                    continue
                rel = os.path.relpath(full, SRC)
                try:
                    z.write(full, rel)
                    count += 1
                    if count % 200 == 0:
                        print(f"  {count} files...", flush=True)
                except (PermissionError, FileNotFoundError) as e:
                    print(f"  SKIP {rel}: {e}", flush=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    os.replace(TMP, OUT)
    size_mb = os.path.getsize(OUT) / (1024 * 1024)
    print(f"ZIP-OK: {OUT} | files: {count} | size: {size_mb:.1f} MB", flush=True)
except Exception as e:
    print(f"ZIP-FAILED: {e}", flush=True)
    sys.exit(1)
