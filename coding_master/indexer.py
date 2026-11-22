"""Static code indexer: symbols, imports and reverse dependencies.

Python files are parsed with :mod:`ast`; other languages are indexed with
line-oriented regex patterns. Nothing is executed or imported, so indexing an
untrusted tree is safe.
"""

import ast
import hashlib
import json
import os
import re
from datetime import datetime

from . import util

# ---------------------------------------------------------------- python AST


def _unparse(node):
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - very old/invalid nodes
        return ""


def _arguments(args):
    """Return a compact description of an ast.arguments node."""
    if not isinstance(args, ast.arguments):
        return []
    positional = list(args.posonlyargs) + list(args.args)
    defaults = list(args.defaults)
    default_offset = len(positional) - len(defaults)
    described = []
    for index, arg in enumerate(positional):
        default = None
        if index >= default_offset:
            default = _unparse(defaults[index - default_offset])
        described.append({
            "name": arg.arg,
            "annotation": _unparse(arg.annotation) if arg.annotation else None,
            "default": default,
            "kind": "positional",
        })
    if args.vararg:
        described.append({"name": "*" + args.vararg.arg, "annotation": None,
                          "default": None, "kind": "vararg"})
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        described.append({
            "name": arg.arg,
            "annotation": _unparse(arg.annotation) if arg.annotation else None,
            "default": _unparse(default) if default is not None else None,
            "kind": "keyword_only",
        })
    if args.kwarg:
        described.append({"name": "**" + args.kwarg.arg, "annotation": None,
                          "default": None, "kind": "kwarg"})
    return described


def _complexity(node):
    """McCabe-style complexity, ignoring nested scopes."""
    count = 1

    def visit(current):
        nonlocal count
        for child in ast.iter_child_nodes(current):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef,
                                  ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                                  ast.ExceptHandler, ast.IfExp,
                                  ast.comprehension, ast.Assert)):
                count += 1
            elif isinstance(child, ast.BoolOp):
                count += max(0, len(child.values) - 1)
            elif isinstance(child, ast.Match):
                count += max(1, len(child.cases))
            visit(child)

    visit(node)
    return count


def _symbol(kind, name, qualname, node, source_lines):
    start = getattr(node, "lineno", 0)
    end = getattr(node, "end_lineno", start) or start
    return {
        "kind": kind,
        "name": name,
        "qualname": qualname,
        "line": start,
        "end_line": end,
        "lines": max(0, end - start + 1),
        "args": _arguments(getattr(node, "args", None)) if kind in
                ("function", "method", "async_function", "async_method") else [],
        "doc": ast.get_docstring(node, clean=True) if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else None,
        "complexity": _complexity(node) if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)) else None,
        "decorators": [_unparse(item) for item in
                       getattr(node, "decorator_list", [])],
    }


def _walk_defs(body, prefix="", inside_class=False):
    symbols = []
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_async = isinstance(node, ast.AsyncFunctionDef)
            if inside_class:
                kind = "async_method" if is_async else "method"
            else:
                kind = "async_function" if is_async else "function"
            qualname = prefix + node.name
            symbols.append(_symbol(kind, node.name, qualname, node, None))
        elif isinstance(node, ast.ClassDef):
            qualname = prefix + node.name
            symbols.append(_symbol("class", node.name, qualname, node, None))
            symbols.extend(_walk_defs(node.body, qualname + ".", True))
    return symbols


def _imports(tree):
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append({"module": alias.name, "name": None,
                              "alias": alias.asname, "line": node.lineno})
        elif isinstance(node, ast.ImportFrom):
            module = "." * (node.level or 0) + (node.module or "")
            for alias in node.names:
                found.append({"module": module, "name": alias.name,
                              "alias": alias.asname, "line": node.lineno})
    return found


def _module_name(relpath):
    name = relpath[:-3] if relpath.endswith(".py") else relpath
    name = name.replace("/", ".")
    if name.endswith(".__init__"):
        name = name[: -len(".__init__")]
    return name


def _parse_python(path, relpath, text):
    entry = {
        "language": "python",
        "lines": util.count_lines(text),
        "bytes": len(text.encode("utf-8", "replace")),
        "module": _module_name(relpath),
        "module_doc": None,
        "symbols": [],
        "imports": [],
        "error": None,
        "has_main_guard": False,
        "sha256": hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16],
    }
    try:
        tree = ast.parse(text, filename=relpath)
    except SyntaxError as exc:
        entry["error"] = {"message": exc.msg, "line": exc.lineno}
        return entry

    entry["module_doc"] = ast.get_docstring(tree, clean=True)
    entry["symbols"] = _walk_defs(tree.body)
    entry["imports"] = _imports(tree)
    for node in tree.body:
        if isinstance(node, ast.If):
            test = _unparse(node.test)
            if "__name__" in test and "__main__" in test:
                entry["has_main_guard"] = True
    return entry


# --------------------------------------------------------- regex languages

REGEX_SYMBOLS = {
    "javascript": [
        (r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", "function"),
        (r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)", "class"),
        (r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:function|\()", "function"),
    ],
    "typescript": [
        (r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", "function"),
        (r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+([A-Za-z_$][\w$]*)", "class"),
        (r"^\s*(?:export\s+)?interface\s+([A-Za-z_$][\w$]*)", "interface"),
        (r"^\s*(?:export\s+)?type\s+([A-Za-z_$][\w$]*)", "type"),
    ],
    "go": [
        (r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(", "function"),
        (r"^\s*type\s+([A-Za-z_]\w*)\s+struct\b", "struct"),
        (r"^\s*type\s+([A-Za-z_]\w*)\s+interface\b", "interface"),
    ],
    "rust": [
        (r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)", "function"),
        (r"^\s*(?:pub\s+)?struct\s+([A-Za-z_]\w*)", "struct"),
        (r"^\s*(?:pub\s+)?enum\s+([A-Za-z_]\w*)", "enum"),
        (r"^\s*(?:pub\s+)?trait\s+([A-Za-z_]\w*)", "trait"),
    ],
    "java": [
        (r"^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?class\s+([A-Za-z_]\w*)", "class"),
        (r"^\s*(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\], ]+\s+([A-Za-z_]\w*)\s*\(", "method"),
    ],
    "kotlin": [
        (r"^\s*(?:data\s+|sealed\s+|abstract\s+)?class\s+([A-Za-z_]\w*)", "class"),
        (r"^\s*fun\s+(?:<[^>]+>\s*)?([A-Za-z_]\w*)", "function"),
    ],
    "csharp": [
        (r"^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?(?:sealed\s+)?class\s+([A-Za-z_]\w*)", "class"),
        (r"^\s*(?:public|private|protected|internal)\s+(?:static\s+)?[\w<>\[\], ]+\s+([A-Za-z_]\w*)\s*\(", "method"),
    ],
    "c": [
        (r"^[A-Za-z_][\w \*]*?\b([A-Za-z_]\w*)\s*\([^;]*\)\s*\{", "function"),
        (r"^\s*struct\s+([A-Za-z_]\w*)", "struct"),
    ],
    "cpp": [
        (r"^[A-Za-z_][\w:<>\*& ]*?\b([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:const\s*)?\{", "function"),
        (r"^\s*(?:class|struct)\s+([A-Za-z_]\w*)", "class"),
    ],
    "ruby": [
        (r"^\s*def\s+(self\.)?([A-Za-z_]\w*[!?=]?)", "method"),
        (r"^\s*class\s+([A-Za-z_]\w*)", "class"),
        (r"^\s*module\s+([A-Za-z_]\w*)", "module"),
    ],
    "php": [
        (r"^\s*(?:public|private|protected)?\s*(?:static\s+)?function\s+([A-Za-z_]\w*)", "function"),
        (r"^\s*(?:abstract\s+|final\s+)?class\s+([A-Za-z_]\w*)", "class"),
    ],
    "swift": [
        (r"^\s*(?:public|private|internal)?\s*(?:static\s+)?func\s+([A-Za-z_]\w*)", "function"),
        (r"^\s*(?:public|private|internal)?\s*(?:class|struct|enum|protocol)\s+([A-Za-z_]\w*)", "type"),
    ],
    "shell": [
        (r"^\s*(?:function\s+)?([A-Za-z_]\w*)\s*\(\)\s*\{", "function"),
    ],
}

SKIP_LANGS = {"json", "yaml", "toml", "markdown", "text", "html", "css", "scss",
              "xml", "ini", "gitignore"}


def _parse_regex(path, relpath, text, language):
    entry = {
        "language": language,
        "lines": util.count_lines(text),
        "bytes": len(text.encode("utf-8", "replace")),
        "module": relpath,
        "module_doc": None,
        "symbols": [],
        "imports": [],
        "error": None,
        "has_main_guard": False,
        "sha256": hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16],
    }
    patterns = REGEX_SYMBOLS.get(language)
    if not patterns:
        return entry
    compiled = [(re.compile(pattern), kind) for pattern, kind in patterns]
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("//", "#", "/*", "*")):
            continue
        for pattern, kind in compiled:
            match = pattern.match(line)
            if not match:
                continue
            groups = [group for group in match.groups() if group]
            if not groups:
                continue
            name = groups[-1]
            entry["symbols"].append({
                "kind": kind,
                "name": name,
                "qualname": name,
                "line": number,
                "end_line": number,
                "lines": 1,
                "args": [],
                "doc": None,
                "complexity": None,
                "decorators": [],
            })
            break
    return entry


# ----------------------------------------------------------------- index


class CodeIndex:
    """Build, query and persist an index of a source tree."""

    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.files = {}
        self.generated_at = None

    # -- build ---------------------------------------------------------
    def build(self, include_data=False, max_files=None, exts=None):
        self.files = {}
        for path in util.iter_files(self.root, exts=exts, max_files=max_files,
                                    include_data=include_data):
            relpath = util.relpath(self.root, path)
            language = util.language_for(path)
            try:
                text = util.read_text(path)
            except OSError as exc:
                self.files[relpath] = {
                    "language": language, "lines": 0, "bytes": 0,
                    "module": relpath, "module_doc": None, "symbols": [],
                    "imports": [], "error": {"message": str(exc), "line": None},
                    "has_main_guard": False, "sha256": None,
                }
                continue
            if language == "python":
                entry = _parse_python(path, relpath, text)
            elif language in SKIP_LANGS:
                entry = {
                    "language": language,
                    "lines": util.count_lines(text),
                    "bytes": len(text.encode("utf-8", "replace")),
                    "module": relpath, "module_doc": None, "symbols": [],
                    "imports": [], "error": None, "has_main_guard": False,
                    "sha256": hashlib.sha256(
                        text.encode("utf-8", "replace")).hexdigest()[:16],
                }
            else:
                entry = _parse_regex(path, relpath, text, language)
            self.files[relpath] = entry

        self.generated_at = datetime.now().isoformat(timespec="seconds")
        return self

    # -- queries -------------------------------------------------------
    def symbols(self):
        for relpath, entry in self.files.items():
            for symbol in entry["symbols"]:
                item = dict(symbol)
                item["file"] = relpath
                item["language"] = entry["language"]
                yield item

    def search(self, term, limit=100):
        needle = term.lower()
        results = []
        for symbol in self.symbols():
            haystack = "%s %s" % (symbol["qualname"], symbol["file"])
            if needle in haystack.lower():
                results.append({
                    "name": symbol["name"],
                    "qualname": symbol["qualname"],
                    "kind": symbol["kind"],
                    "file": symbol["file"],
                    "line": symbol["line"],
                    "language": symbol["language"],
                })
                if len(results) >= limit:
                    break
        return results

    def references(self, name):
        """Find files that import or mention ``name``."""
        needle = re.compile(r"\b%s\b" % re.escape(name))
        hits = []
        for path in util.iter_files(self.root, exts={".py", ".js", ".ts",
                                                      ".tsx", ".jsx", ".go",
                                                      ".rs", ".java", ".cs"}):
            try:
                text = util.read_text(path)
            except OSError:
                continue
            if needle.search(text):
                hits.append(util.relpath(self.root, path))
        return hits

    def reverse_imports(self):
        reverse = {}
        for relpath, entry in self.files.items():
            for item in entry["imports"]:
                module = item["module"].lstrip(".")
                if not module:
                    continue
                reverse.setdefault(module, []).append(relpath)
                parts = module.split(".")
                for index in range(1, len(parts)):
                    reverse.setdefault(".".join(parts[:index]), []).append(relpath)
        return {key: sorted(set(value)) for key, value in reverse.items()}

    def dependency_graph(self):
        graph = {}
        for relpath, entry in self.files.items():
            modules = set()
            for item in entry["imports"]:
                module = item["module"].lstrip(".")
                if module:
                    modules.add(module.split(".")[0])
            graph[relpath] = sorted(modules)
        return graph

    def summary(self):
        symbols = list(self.symbols())
        by_kind = {}
        by_language = {}
        for symbol in symbols:
            by_kind[symbol["kind"]] = by_kind.get(symbol["kind"], 0) + 1
            by_language[symbol["language"]] = by_language.get(symbol["language"], 0) + 1
        return {
            "root": self.root,
            "generated_at": self.generated_at,
            "file_count": len(self.files),
            "symbol_count": len(symbols),
            "total_lines": sum(entry["lines"] for entry in self.files.values()),
            "parse_errors": sum(1 for entry in self.files.values() if entry["error"]),
            "by_kind": dict(sorted(by_kind.items())),
            "by_language": dict(sorted(by_language.items())),
            "entry_points": sorted(
                path for path, entry in self.files.items()
                if entry.get("has_main_guard")),
        }

    # -- persistence ---------------------------------------------------
    def to_dict(self):
        return {
            "schema": "coding_master.index/1",
            "root": self.root,
            "generated_at": self.generated_at,
            "summary": self.summary(),
            "files": self.files,
            "reverse_imports": self.reverse_imports(),
        }

    def save(self, path):
        util.write_json(path, self.to_dict())
        return path

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        index = cls(data.get("root", "."))
        index.files = data.get("files", {})
        index.generated_at = data.get("generated_at")
        return index
