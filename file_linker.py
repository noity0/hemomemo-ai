#!/usr/bin/env python3
"""QANOON-Compliant File Linker + ZIP Manifest Generator.

Deep-links DigitalBrain ↔ Desktop ↔ App ↔ ZIP files.
No external dependencies. No cloud. 100% local.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"D:\DigitalBrain")
DESKTOP = Path(r"C:\Users\user\Desktop")
APP = ROOT / "app"
ZIP_FILES = [
    ROOT / "hemomemo_ultra_latest.zip",
    ROOT / "HemomemoUltra-People.zip",
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_md5(file_path: Path) -> str:
    """Compute MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()

def scan_directory(directory: Path, pattern: str = "*", max_depth: int = 3) -> List[Path]:
    """Recursively scan directory for files matching pattern."""
    results = []
    for current_dir, dirs, files in os.walk(directory):
        depth = current_dir.replace(str(directory), "").count(os.sep)
        if depth > max_depth:
            break
        for file in files:
            if re.match(pattern, file):
                results.append(Path(current_dir) / file)
    return results

def build_file_linker() -> Dict[str, Any]:
    """Build deep link graph between DigitalBrain, Desktop, App, and ZIPs."""
    print("🔗 Building deep file links...")
    
    # 1. Scan DigitalBrain core files
    digitalbrain_files = {
        "python_scripts": scan_directory(ROOT, r"^[^_].*\.py$"),
        "data_files": scan_directory(ROOT, r".*\.(json|csv|db|pkl)$"),
        "docs": scan_directory(ROOT, r".*\.(md|txt|html)$"),
    }
    
    # 2. Scan Desktop
    desktop_files = {
        "scripts": scan_directory(DESKTOP, r".*\.py$") if DESKTOP.exists() else [],
        "config": scan_directory(DESKTOP, r".*\.(json|yaml|yml)$") if DESKTOP.exists() else [],
    }
    
    # 3. Scan App
    app_files = {
        "python": scan_directory(APP, r".*\.py$"),
        "resources": scan_directory(APP, r".*\.(png|ico|jpg|gif)$"),
    }
    
    # 4. ZIP files manifest
    zip_manifest = []
    for zip_file in ZIP_FILES:
        if zip_file.exists():
            manifest_entry = {
                "path": str(zip_file),
                "size_bytes": zip_file.stat().st_size,
                "modified": datetime.fromtimestamp(zip_file.stat().st_mtime).isoformat(),
                "sha256": compute_sha256(zip_file),
                "md5": compute_md5(zip_file),
            }
            zip_manifest.append(manifest_entry)
    
    # 5. Build link graph
    link_graph = {
        "digitalbrain_to_desktop": [],
        "digitalbrain_to_app": [],
        "digitalbrain_to_zip": [],
        "desktop_to_app": [],
    }
    
    # DigitalBrain → Desktop links
    for script in digitalbrain_files["python_scripts"][:10]:  # Sample
        link_graph["digitalbrain_to_desktop"].append({
            "source": str(script),
            "link_type": "reference",
            "description": "Script available in DigitalBrain"
        })
    
    # DigitalBrain → App links
    for script in digitalbrain_files["python_scripts"][:5]:
        link_graph["digitalbrain_to_app"].append({
            "source": str(script),
            "target": str(APP / "hemomemo_app.py"),
            "link_type": "copy",
            "description": "Main app script"
        })
    
    # DigitalBrain → ZIP links
    for zip_info in zip_manifest:
        link_graph["digitalbrain_to_zip"].append({
            "source": zip_info["path"],
            "link_type": "archive",
            "sha256": zip_info["sha256"][:16] + "...",
            "size_mb": round(zip_info["size_bytes"] / (1024 * 1024), 2)
        })
    
    # Desktop → App links
    for config in desktop_files["config"][:5]:
        link_graph["desktop_to_app"].append({
            "source": str(config),
            "target": str(APP / "hemomemo_app.py"),
            "link_type": "reference",
            "description": "Config referenced by app"
        })
    
    return {
        "generated_at": datetime.now().isoformat(),
        "qanoon_compliance": {
            "local_only": True,
            "no_cloud": True,
            "no_external_ai": True,
            "no_ffmpeg": True
        },
        "directories_scanned": {
            "digitalbrain": str(ROOT),
            "desktop": str(DESKTOP),
            "app": str(APP)
        },
        "file_counts": {
            "digitalbrain_python": len(digitalbrain_files["python_scripts"]),
            "digitalbrain_data": len(digitalbrain_files["data_files"]),
            "digitalbrain_docs": len(digitalbrain_files["docs"]),
            "desktop_scripts": len(desktop_files["scripts"]),
            "desktop_config": len(desktop_files["config"]),
            "app_python": len(app_files["python"]),
            "app_resources": len(app_files["resources"]),
            "zip_files": len(zip_manifest)
        },
        "zip_manifest": zip_manifest,
        "link_graph": link_graph,
        "file_samples": {
            "digitalbrain": [str(f) for f in digitalbrain_files["python_scripts"][:20]],
            "desktop": [str(f) for f in desktop_files["scripts"][:10]],
            "app": [str(f) for f in app_files["python"][:10]]
        }
    }

def main():
    linker = build_file_linker()
    
    # Save to data/file_links/
    output_dir = ROOT / "data" / "file_links"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "deep_links.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(linker, f, indent=2)
    
    print(f"✅ Deep links saved to {output_file}")
    print(f"   - DigitalBrain: {linker['file_counts']['digitalbrain_python']} Python scripts")
    print(f"   - Desktop: {linker['file_counts']['desktop_scripts']} scripts")
    print(f"   - App: {linker['file_counts']['app_python']} files")
    print(f"   - ZIPs: {linker['file_counts']['zip_files']} archives")
    print(f"   - Total links: {sum(len(v) for v in linker['link_graph'].values())}")

if __name__ == "__main__":
    main()
