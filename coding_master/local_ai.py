#!/usr/bin/env python3
"""Local AI Code Suggestor (QANOON-Compliant).

Simple heuristic-based code suggestions.
No external AI. No cloud. 100% local.
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List

class LocalAISuggestor:
    """Generate local code improvement suggestions."""
    
    def __init__(self, root: Path):
        self.root = root
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single Python file and suggest improvements."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tree = ast.parse(content)
            suggestions = []
            
            # 1. Check for bare except
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    suggestions.append({
                        "type": "bare_except",
                        "line": node.lineno,
                        "suggestion": "Use specific exception instead of bare except",
                        "severity": "medium"
                    })
            
            # 2. Check for mutable default arguments
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for default in node.args.defaults + node.args.kw_defaults:
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            suggestions.append({
                                "type": "mutable_default",
                                "line": node.lineno,
                                "suggestion": "Use None as default, initialize in function body",
                                "severity": "medium"
                            })
                            break
            
            # 3. Check for missing docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        suggestions.append({
                            "type": "missing_docstring",
                            "line": node.lineno,
                            "suggestion": f"Add docstring to {node.name}",
                            "severity": "low"
                        })
            
            # 4. Check for overly long functions
            lines = content.splitlines()
            func_start = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    end_line = node.end_lineno
                    func_lines = end_line - node.lineno + 1
                    if func_lines > 60:
                        suggestions.append({
                            "type": "long_function",
                            "line": node.lineno,
                            "suggestion": f"Function {node.name} is {func_lines} lines (limit: 60)",
                            "severity": "medium"
                        })
            
            return {
                "file": str(file_path),
                "suggestions": suggestions,
                "count": len(suggestions)
            }
        
        except Exception as e:
            return {
                "file": str(file_path),
                "suggestions": [],
                "count": 0,
                "error": str(e)
            }
    
    def generate_report(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Generate comprehensive report for multiple files."""
        all_suggestions = []
        for file_path in file_paths:
            result = self.analyze_file(file_path)
            all_suggestions.append(result)
        
        total_suggestions = sum(s["count"] for s in all_suggestions)
        
        return {
            "generated_at": datetime.now().isoformat(),
            "total_files_analyzed": len(file_paths),
            "total_suggestions": total_suggestions,
            "files": all_suggestions,
            "qanoon_compliance": {
                "local_only": True,
                "no_external_ai": True,
                "no_cloud": True
            }
        }

# Need to import datetime
from datetime import datetime
