#!/usr/bin/env python3
"""Unified Dashboard Generator (QANOON-Compliant).

Generate HTML dashboard for all integration data.
No external dependencies. No cloud. 100% local.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

class DashboardGenerator:
    """Generate HTML dashboard."""
    
    def __init__(self, root: Path):
        self.root = root
    
    def generate_dashboard(self) -> Path:
        """Generate comprehensive HTML dashboard."""
        # Load data
        file_links = self._load_json(self.root / "data" / "file_links" / "deep_links.json", {})
        engine_report = self._load_json(self.root / "enhancement_system" / "engine" / "engine_report.json", {})
        audit_report = self._load_json(self.root / "data" / "code_audit" / "audit_report.json", {})
        
        html = self._build_html(file_links, engine_report, audit_report)
        
        # Save
        output_path = self.root / "data" / "dashboard" / "index.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"✅ Dashboard generated: {output_path}")
        return output_path
    
    def _load_json(self, path: Path, default) -> dict:
        """Load JSON file with default fallback."""
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default
    
    def _build_html(self, file_links: dict, engine: dict, audit: dict) -> str:
        """Build HTML dashboard content."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hemomemo AI - Unified Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; 
                margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        h1 {{ color: #2d3748; margin-bottom: 10px; }}
        h2 {{ color: #4a5568; margin: 20px 0 10px 0; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .stat-box {{ background: #f7fafc; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #718096; font-size: 0.9em; }}
        .section {{ margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #edf2f7; font-weight: 600; }}
        .qanoon {{ background: #c6f6d5; color: #22543d; padding: 10px; 
                  border-radius: 5px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🚀 Hemomemo AI - Unified Dashboard</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="card">
            <h2>📊 Key Metrics</h2>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value">{file_links.get('file_counts', {}).get('digitalbrain_python', 0)}</div>
                    <div class="stat-label">DigitalBrain Scripts</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{file_links.get('file_counts', {}).get('zip_files', 0)}</div>
                    <div class="stat-label">ZIP Archives</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{engine.get('self_index', {}).get('symbol_count', 0)}</div>
                    <div class="stat-label">Engine Symbols</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{audit.get('analysis', {}).get('score', {}).get('grade', 'N/A')}</div>
                    <div class="stat-label">Code Quality</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🔗 File Links (DigitalBrain ↔ Desktop ↔ App ↔ ZIP)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Source</th>
                        <th>Link Type</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
                    {self._render_file_links(file_links)}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>⚙️ Coding Engine Status</h2>
            <p><strong>Version:</strong> {engine.get('version', 'N/A')}</p>
            <p><strong>Modules:</strong> {engine.get('modules_checked', 0)}</p>
            <p><strong>Security Score:</strong> {engine.get('self_security', {}).get('score', 0)}/100</p>
            <p><strong>Analysis Grade:</strong> {engine.get('self_analysis', {}).get('score', {}).get('grade', 'N/A')}</p>
            <p><strong>Languages:</strong> {', '.join(engine.get('languages', []))}</p>
        </div>
        
        <div class="card">
            <h2>✅ QANOON Compliance</h2>
            <div class="qanoon">
                <strong>100% Local:</strong> No external AI, no cloud, no FFmpeg<br/>
                <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    def _render_file_links(self, file_links: dict) -> str:
        """Render file links table rows."""
        rows = []
        for link_type, links in file_links.get("link_graph", {}).items():
            for link in links[:5]:  # Show first 5
                rows.append(f"""
                    <tr>
                        <td>{link.get('source', '')[:50]}...</td>
                        <td>{link.get('link_type', '')}</td>
                        <td>{link.get('description', '') or link.get('sha256', '')[:20]}</td>
                    </tr>
                """)
        return "".join(rows)

def main():
    """Generate dashboard."""
    dashboard = DashboardGenerator(Path(r"D:\DigitalBrain"))
    dashboard.generate_dashboard()

if __name__ == "__main__":
    main()
