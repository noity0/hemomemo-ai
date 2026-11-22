"""Metrics, complexity analysis and code-smell detection.

Python files are analysed from the AST; other languages get line-based
heuristics. No code is imported or executed.
"""

import ast
import hashlib
import io
import os
import re
import tokenize
from datetime import datetime

from . import util
from .indexer import REGEX_SYMBOLS, _complexity

SEVERITY_WEIGHTS = {
    "critical": 10.0,
    "high": 5.0,
    "medium": 1.2,
    "low": 0.3,
    "info": 0.05,
}

MAX_FUNCTION_LINES = 60
MAX_FILE_LINES = 600
MAX_PARAMETERS = 6
MAX_COMPLEXITY = 15
MAX_NESTING = 4
MAX_LINE_LENGTH = 120

TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")


def _max_depth(node, depth=0):
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef, ast.Lambda)):
            continue
        deeper = isinstance(child, (
            ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith,
            ast.Try, ast.Match, ast.ExceptHandler,
        ))
        best = max(best, _max_depth(child, depth + (1 if deeper else 0)))
    return best


def _is_mutable_default(node):
    if isinstance(node, (ast.List, ast.Dict, ast.Set, ast.ListComp,
                         ast.DictComp, ast.SetComp)):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in ("list", "dict", "set", "bytearray")
    return False


def _function_token_hash(text, node):
    """Stable hash of a function body's tokens (comments/space ignored)."""
    lines = text.splitlines()
    start = max(0, node.lineno - 1)
    end = min(len(lines), node.end_lineno or node.lineno)
    segment = "\n".join(lines[start:end])
    try:
        tokens = []
        for token in tokenize.generate_tokens(io.StringIO(segment).readline):
            if token.type in (tokenize.NAME, tokenize.OP, tokenize.NUMBER,
                              tokenize.STRING):
                tokens.append(token.string)
    except (tokenize.TokenError, IndentationError):
        return None
    if len(tokens) < 12:
        return None
    return hashlib.sha256(" ".join(tokens).encode("utf-8")).hexdigest()[:20]


def _python_metrics(text, path, issues):
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        issues.append({
            "rule": "syntax-error", "severity": "critical",
            "file": path, "line": exc.lineno or 1,
            "message": "File does not parse: %s" % exc.msg,
            "symbol": None,
        })
        return None

    functions = 0
    classes = 0
    complexities = []
    duplicate_candidates = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes += 1
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
            complexity = _complexity(node)
            complexities.append(complexity)
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            args = node.args
            parameter_count = (len(args.posonlyargs) + len(args.args) +
                               len(args.kwonlyargs))
            qualname = node.name

            if length > MAX_FUNCTION_LINES:
                issues.append({
                    "rule": "long-function", "severity": "medium",
                    "file": path, "line": node.lineno, "symbol": qualname,
                    "message": "Function is %d lines (limit %d)"
                               % (length, MAX_FUNCTION_LINES),
                })
            if complexity > MAX_COMPLEXITY:
                issues.append({
                    "rule": "high-complexity", "severity": "medium",
                    "file": path, "line": node.lineno, "symbol": qualname,
                    "message": "Cyclomatic complexity %d (limit %d)"
                               % (complexity, MAX_COMPLEXITY),
                })
            depth = _max_depth(node)
            if depth > MAX_NESTING:
                issues.append({
                    "rule": "deep-nesting", "severity": "medium",
                    "file": path, "line": node.lineno, "symbol": qualname,
                    "message": "Nesting depth %d (limit %d)"
                               % (depth, MAX_NESTING),
                })
            if parameter_count > MAX_PARAMETERS:
                issues.append({
                    "rule": "too-many-parameters", "severity": "low",
                    "file": path, "line": node.lineno, "symbol": qualname,
                    "message": "%d parameters (limit %d)"
                               % (parameter_count, MAX_PARAMETERS),
                })
            for default in list(args.defaults) + [d for d in args.kw_defaults if d]:
                if _is_mutable_default(default):
                    issues.append({
                        "rule": "mutable-default", "severity": "high",
                        "file": path, "line": node.lineno, "symbol": qualname,
                        "message": "Mutable default argument (shared state bug)",
                    })
                    break
            if not node.name.startswith("_") and not ast.get_docstring(node):
                issues.append({
                    "rule": "missing-docstring", "severity": "info",
                    "file": path, "line": node.lineno, "symbol": qualname,
                    "message": "Public function has no docstring",
                })
            digest = _function_token_hash(text, node)
            if digest:
                duplicate_candidates.append({
                    "hash": digest, "file": path, "line": node.lineno,
                    "symbol": qualname, "lines": length,
                })
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append({
                "rule": "bare-except", "severity": "high",
                "file": path, "line": node.lineno, "symbol": None,
                "message": "Bare 'except:' swallows every error",
            })

    code_lines = comments = blanks = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            blanks += 1
        elif stripped.startswith("#"):
            comments += 1
        else:
            code_lines += 1

    return {
        "language": "python",
        "lines": len(text.splitlines()),
        "code_lines": code_lines,
        "comment_lines": comments,
        "blank_lines": blanks,
        "functions": functions,
        "classes": classes,
        "max_complexity": max(complexities) if complexities else 0,
        "avg_complexity": round(sum(complexities) / len(complexities), 2)
                          if complexities else 0.0,
        "duplicate_candidates": duplicate_candidates,
    }


def _generic_metrics(text, path, language):
    lines = text.splitlines()
    code = comment = blank = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank += 1
        elif stripped.startswith(("#", "//", "/*", "*", "--", "<!--")):
            comment += 1
        else:
            code += 1
    functions = classes = 0
    patterns = REGEX_SYMBOLS.get(language, [])
    compiled = [(re.compile(pattern), kind) for pattern, kind in patterns]
    for line in lines:
        for pattern, kind in compiled:
            if pattern.match(line):
                if kind in ("function", "method"):
                    functions += 1
                elif kind in ("class", "struct", "interface", "type", "trait",
                              "enum", "module"):
                    classes += 1
                break
    return {
        "language": language,
        "lines": len(lines),
        "code_lines": code,
        "comment_lines": comment,
        "blank_lines": blank,
        "functions": functions,
        "classes": classes,
        "max_complexity": None,
        "avg_complexity": None,
        "duplicate_candidates": [],
    }


class Analyzer:
    """Analyse a file or a whole tree and produce a scored report."""

    def __init__(self, root):
        self.root = os.path.abspath(root)

    def analyze_file(self, path):
        relpath = util.relpath(self.root, path) if os.path.isabs(path) else path
        issues = []
        try:
            text = util.read_text(path)
        except OSError as exc:
            return {
                "file": relpath, "language": util.language_for(path),
                "error": str(exc), "issues": [{
                    "rule": "unreadable", "severity": "critical",
                    "file": relpath, "line": 1,
                    "message": "Cannot read file: %s" % exc, "symbol": None,
                }],
            }

        language = util.language_for(path)
        if language == "python":
            metrics = _python_metrics(text, relpath, issues)
        else:
            metrics = _generic_metrics(text, relpath, language)

        if metrics is None:
            metrics = {
                "language": language, "lines": util.count_lines(text),
                "code_lines": 0, "comment_lines": 0, "blank_lines": 0,
                "functions": 0, "classes": 0, "max_complexity": None,
                "avg_complexity": None, "duplicate_candidates": [],
            }

        if metrics["lines"] > MAX_FILE_LINES:
            issues.append({
                "rule": "large-file", "severity": "low", "file": relpath,
                "line": 1, "symbol": None,
                "message": "File has %d lines (limit %d)"
                           % (metrics["lines"], MAX_FILE_LINES),
            })

        long_lines = [(number, len(line))
                      for number, line in enumerate(text.splitlines(), 1)
                      if len(line) > MAX_LINE_LENGTH]
        if long_lines:
            first_line, first_length = long_lines[0]
            issues.append({
                "rule": "long-line", "severity": "low", "file": relpath,
                "line": first_line, "symbol": None,
                "message": "%d line(s) exceed %d characters (first is %d)"
                           % (len(long_lines), MAX_LINE_LENGTH, first_length),
            })

        for number, line in enumerate(text.splitlines(), 1):
            if TODO_RE.search(line):
                issues.append({
                    "rule": "todo-comment", "severity": "info",
                    "file": relpath, "line": number, "symbol": None,
                    "message": "Unresolved marker: %s"
                               % TODO_RE.search(line).group(1),
                })

        result = dict(metrics)
        result["file"] = relpath
        result["issues"] = issues
        return result

    def analyze(self, include_data=False, max_files=None):
        files = []
        all_issues = []
        duplicates = {}
        for path in util.iter_files(self.root, include_data=include_data,
                                    max_files=max_files):
            result = self.analyze_file(path)
            files.append(result)
            all_issues.extend(result.get("issues", []))
            for candidate in result.get("duplicate_candidates", []):
                duplicates.setdefault(candidate["hash"], []).append(candidate)

        duplicate_groups = [
            {"hash": digest, "locations": sorted(items,
                                                 key=lambda i: (i["file"], i["line"]))}
            for digest, items in duplicates.items() if len(items) > 1
        ]

        severity_counts = {key: 0 for key in SEVERITY_WEIGHTS}
        for issue in all_issues:
            severity_counts[issue["severity"]] = severity_counts.get(
                issue["severity"], 0) + 1

        total_lines = sum(item["lines"] for item in files)
        weighted = sum(SEVERITY_WEIGHTS.get(issue["severity"], 0)
                       for issue in all_issues)
        per_kloc = weighted / max(1.0, total_lines / 1000.0)
        score = util.clamp(round(100 - per_kloc * 2.0, 1), 0.0, 100.0)
        if severity_counts.get("critical"):
            score = min(score, 69.0)
        elif severity_counts.get("high"):
            score = min(score, 84.0)
        grade = "A" if score >= 90 else "B" if score >= 80 else \
                "C" if score >= 70 else "D" if score >= 60 else "F"

        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        all_issues.sort(key=lambda item: (order.get(item["severity"], 9),
                                          item["file"], item["line"]))

        rule_counts = {}
        for issue in all_issues:
            rule_counts[issue["rule"]] = rule_counts.get(issue["rule"], 0) + 1

        recommendations = []
        for rule, count in sorted(rule_counts.items(),
                                  key=lambda pair: -pair[1])[:8]:
            recommendations.append("%s: %d occurrence(s)" % (rule, count))

        return {
            "root": self.root,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": {
                "files": len(files),
                "lines": total_lines,
                "code_lines": sum(item.get("code_lines", 0) for item in files),
                "functions": sum(item.get("functions", 0) for item in files),
                "classes": sum(item.get("classes", 0) for item in files),
                "issues": len(all_issues),
                "issues_by_severity": severity_counts,
                "rules": dict(sorted(rule_counts.items())),
            },
            "score": {"value": score, "grade": grade},
            "issues": all_issues,
            "duplicates": duplicate_groups,
            "recommendations": recommendations,
            "files": files,
        }

    def analyze_to_file(self, path):
        report = self.analyze()
        util.write_json(path, report)
        return report
