"""Documentation generation from Python source and project layout."""

import ast
import os
from datetime import datetime

from . import util


def _signature(node):
    args = node.args
    parts = []
    positional = list(args.posonlyargs) + list(args.args)
    defaults = list(args.defaults)
    offset = len(positional) - len(defaults)
    for index, arg in enumerate(positional):
        text = arg.arg
        if arg.annotation is not None:
            text += ": " + ast.unparse(arg.annotation)
        if index >= offset:
            text += " = " + ast.unparse(defaults[index - offset])
        parts.append(text)
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        parts.append("*")
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        text = arg.arg
        if arg.annotation is not None:
            text += ": " + ast.unparse(arg.annotation)
        if default is not None:
            text += " = " + ast.unparse(default)
        parts.append(text)
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    returns = ""
    if node.returns is not None:
        returns = " -> " + ast.unparse(node.returns)
    return "(%s)%s" % (", ".join(parts), returns)


def _arg_table(node):
    args = node.args
    rows = []
    positional = list(args.posonlyargs) + list(args.args)
    defaults = list(args.defaults)
    offset = len(positional) - len(defaults)
    for index, arg in enumerate(positional):
        default = ast.unparse(defaults[index - offset]) \
            if index >= offset else "required"
        rows.append((arg.arg, ast.unparse(arg.annotation)
                     if arg.annotation else "", default))
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        rows.append((arg.arg, ast.unparse(arg.annotation) if arg.annotation else "",
                     ast.unparse(default) if default is not None else "required"))
    if args.vararg:
        rows.append(("*" + args.vararg.arg, "", "variadic"))
    if args.kwarg:
        rows.append(("**" + args.kwarg.arg, "", "keyword variadic"))
    if not rows:
        return []
    lines = ["| Argument | Type | Default |", "| --- | --- | --- |"]
    for name, annotation, default in rows:
        lines.append("| `%s` | `%s` | `%s` |"
                     % (name, annotation or "-", default.replace("|", "\\|")))
    return lines


class DocGenerator:
    """Produce Markdown API docs and README files from local code."""

    def __init__(self, root):
        self.root = os.path.abspath(root)

    def document_file(self, path):
        text = util.read_text(path)
        tree = ast.parse(text, filename=path)
        relative = util.relpath(self.root, path)
        lines = ["# `%s`" % relative, ""]
        module_doc = ast.get_docstring(tree, clean=True)
        if module_doc:
            lines.extend([module_doc, ""])

        classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
        functions = [node for node in tree.body
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

        public_classes = [node for node in classes if not node.name.startswith("_")]
        public_functions = [node for node in functions
                            if not node.name.startswith("_")]

        if public_classes:
            lines.extend(["## Classes", ""])
            for klass in public_classes:
                lines.extend(["### `%s`" % klass.name, ""])
                doc = ast.get_docstring(klass, clean=True)
                if doc:
                    lines.extend([doc, ""])
                init = next((child for child in klass.body
                             if isinstance(child, ast.FunctionDef)
                             and child.name == "__init__"), None)
                if init is not None and init.args.args:
                    lines.extend(["```python", "class %s%s" % (
                        klass.name, _signature(init)), "```", ""])
                for child in klass.body:
                    if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    if child.name.startswith("_") and child.name != "__init__":
                        continue
                    lines.extend(["#### `%s%s`" % (child.name, _signature(child)),
                                  ""])
                    child_doc = ast.get_docstring(child, clean=True)
                    if child_doc:
                        lines.extend([child_doc, ""])
                    table = _arg_table(child)
                    if table:
                        lines.extend(table + [""])

        if public_functions:
            lines.extend(["## Functions", ""])
            for function in public_functions:
                lines.extend(["### `%s%s`" % (function.name,
                                              _signature(function)), ""])
                doc = ast.get_docstring(function, clean=True)
                if doc:
                    lines.extend([doc, ""])
                table = _arg_table(function)
                if table:
                    lines.extend(table + [""])

        if not public_classes and not public_functions:
            lines.extend(["_No public classes or functions in this module._", ""])

        return "\n".join(lines).rstrip() + "\n"

    def document_tree(self, max_files=200):
        modules = []
        for path in util.iter_files(self.root, exts={".py"}, max_files=max_files):
            relative = util.relpath(self.root, path)
            if relative.startswith(("tests/", "test_")) or "/test_" in relative:
                continue
            try:
                modules.append(self.document_file(path))
            except SyntaxError:
                continue
        header = ["# API Reference", "",
                  "Generated %s by ULTIMATE CODING MASTER."
                  % datetime.now().strftime("%Y-%m-%d %H:%M"),
                  "", "---", ""]
        return "\n".join(header) + "\n\n---\n\n".join(modules)

    def readme(self, project_name=None):
        name = project_name or os.path.basename(self.root.rstrip("\\/")) or "project"
        language_counts = {}
        entry_points = []
        test_files = 0
        for path in util.iter_files(self.root, max_files=5000):
            language = util.language_for(path)
            if language in ("text", "json", "yaml", "toml", "ini",
                            "markdown", "gitignore"):
                continue
            language_counts[language] = language_counts.get(language, 0) + 1
            relative = util.relpath(self.root, path)
            base = os.path.basename(path).lower()
            if base in ("main.py", "app.py", "cli.py", "server.py", "run.py"):
                entry_points.append(relative)
            if relative.startswith("tests/") or base.startswith("test_"):
                test_files += 1

        order = sorted(language_counts.items(), key=lambda pair: -pair[1])
        languages = ", ".join("%s (%d files)" % (language, count)
                              for language, count in order[:8]) or "none detected"

        has_pyproject = os.path.isfile(os.path.join(self.root, "pyproject.toml"))
        has_requirements = os.path.isfile(os.path.join(self.root,
                                                       "requirements.txt"))
        has_package_json = os.path.isfile(os.path.join(self.root,
                                                       "package.json"))
        has_cargo = os.path.isfile(os.path.join(self.root, "Cargo.toml"))
        has_go_mod = os.path.isfile(os.path.join(self.root, "go.mod"))

        install = []
        run = []
        test = []
        if has_requirements:
            install.extend(["```bash", "python -m venv .venv",
                            ".venv\\Scripts\\activate",
                            "pip install -r requirements.txt", "```"])
        elif has_pyproject:
            install.extend(["```bash", "pip install -e .", "```"])
        if has_package_json:
            install.extend(["```bash", "npm install", "```"])
            run.extend(["```bash", "npm start", "```"])
        if has_cargo:
            run.extend(["```bash", "cargo run", "```"])
            test.extend(["```bash", "cargo test", "```"])
        if has_go_mod:
            run.extend(["```bash", "go run .", "```"])
            test.extend(["```bash", "go test ./...", "```"])
        if entry_points:
            run.extend(["```bash", "python %s" % entry_points[0], "```"])
        if test_files:
            test.extend(["```bash",
                         "python -m unittest discover -s tests -v", "```"])

        lines = [
            "# %s" % name,
            "",
            "Local-first project generated by ULTIMATE CODING MASTER.",
            "",
            "## Overview",
            "",
            "- Languages: %s" % languages,
            "- Entry points: %s" % (", ".join(sorted(set(entry_points))[:6])
                                    or "none detected"),
            "- Test files: %d" % test_files,
            "",
            "## Features",
            "",
            "- 100%% local execution",
            "- No external AI platform calls",
            "- No cloud dependencies",
            "",
        ]
        if install:
            lines.extend(["## Installation", ""] + install + [""])
        if run:
            lines.extend(["## Usage", ""] + run + [""])
        if test:
            lines.extend(["## Tests", ""] + test + [""])
        lines.extend([
            "## Project Layout",
            "",
            "```",
            "app/       application code",
            "tests/     automated tests",
            "docs/      documentation",
            "```",
            "",
            "## License",
            "",
            "See the LICENSE file in this repository.",
            "",
        ])
        return "\n".join(lines)

    def write_api(self, path):
        util.write_text(path, self.document_tree())
        return path

    def write_readme(self, path, project_name=None):
        util.write_text(path, self.readme(project_name))
        return path
