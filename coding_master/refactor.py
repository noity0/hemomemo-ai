"""Safe, local source refactoring.

All operations work on text/AST/tokens only. They never import the target
module, so refactoring untrusted code cannot execute it.
"""

import ast
import io
import keyword
import os
import re
import sys
import tokenize

from . import util

STDLIB = set(getattr(sys, "stdlib_module_names", set())) | {
    "os", "sys", "re", "json", "math", "time", "datetime", "pathlib",
    "typing", "collections", "itertools", "functools", "subprocess",
    "threading", "unittest", "argparse", "csv", "sqlite3", "hashlib",
    "random", "secrets", "shutil", "tempfile", "logging", "socket",
    "http", "urllib", "email", "base64", "struct", "enum", "dataclasses",
    "contextlib", "copy", "glob", "io", "textwrap", "traceback", "uuid",
}


def _import_nodes(tree):
    return [node for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))]


def _alias_text(alias):
    return alias.name if not alias.asname else "%s as %s" % (alias.name,
                                                             alias.asname)


def _render_group(imports, from_imports):
    lines = []
    for node in imports:
        for alias in node.names:
            lines.append("import %s" % _alias_text(alias))
    grouped = {}
    for node in from_imports:
        module = "." * (node.level or 0) + (node.module or "")
        grouped.setdefault(module, []).extend(node.names)
    for module in sorted(grouped):
        names = sorted({_alias_text(alias) for alias in grouped[module]})
        joined = ", ".join(names)
        if len(joined) > 66:
            lines.append("from %s import (" % module)
            for name in names:
                lines.append("    %s," % name)
            lines.append(")")
        else:
            lines.append("from %s import %s" % (module, joined))
    return lines


def _classify(node, local_modules):
    if isinstance(node, ast.ImportFrom) and (node.level or 0) > 0:
        return "local"
    module = node.module if isinstance(node, ast.ImportFrom) else node.names[0].name
    root = (module or "").split(".")[0]
    if root in local_modules:
        return "local"
    if root in STDLIB:
        return "stdlib"
    return "third-party"


class Refactorer:
    """Import organisation, unused-import removal, rename and formatting."""

    def __init__(self, root):
        self.root = os.path.abspath(root)

    # -- imports -------------------------------------------------------
    def organize_imports(self, source, local_modules=None):
        local_modules = set(local_modules or ())
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            raise ValueError("Cannot parse source: %s" % exc)
        nodes = _import_nodes(tree)
        if not nodes:
            return {"content": source, "changed": False, "import_count": 0,
                    "groups": {"stdlib": 0, "third-party": 0, "local": 0,
                               "future": 0}}

        groups = {"future": [], "stdlib": [], "third-party": [], "local": []}
        for node in nodes:
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                groups["future"].append(node)
            else:
                groups[_classify(node, local_modules)].append(node)

        blocks = []
        for key in ("future", "stdlib", "third-party", "local"):
            selected = groups[key]
            if not selected:
                continue
            plain = [node for node in selected if isinstance(node, ast.Import)]
            froms = [node for node in selected if isinstance(node, ast.ImportFrom)]
            block = _render_group(plain, froms)
            if block:
                blocks.append(block)

        rendered = []
        for index, block in enumerate(blocks):
            if index:
                rendered.append("")
            rendered.extend(block)

        lines = source.splitlines()
        ranges = [(node.lineno - 1, (node.end_lineno or node.lineno) - 1)
                  for node in nodes]
        first = min(start for start, _end in ranges)
        output = []
        inserted = False
        for index, line in enumerate(lines):
            if any(start <= index <= end for start, end in ranges):
                if not inserted and index == first:
                    output.extend(rendered)
                    inserted = True
                continue
            output.append(line)

        content = self._cleanup("\n".join(output))
        counts = {key: len(value) for key, value in groups.items()}
        return {
            "content": content,
            "changed": content != self._cleanup(source),
            "import_count": len(nodes),
            "groups": counts,
        }

    def remove_unused_imports(self, source):
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            raise ValueError("Cannot parse source: %s" % exc)
        nodes = _import_nodes(tree)
        if not nodes:
            return {"content": source, "changed": False, "removed": [],
                    "kept": 0}

        ranges = [(node.lineno - 1, (node.end_lineno or node.lineno) - 1)
                  for node in nodes]

        def in_import(row):
            index = row - 1
            return any(start <= index <= end for start, end in ranges)

        used = set()
        try:
            for token in tokenize.generate_tokens(io.StringIO(source).readline):
                if token.type == tokenize.NAME and not in_import(token.start[0]):
                    used.add(token.string)
        except (tokenize.TokenError, IndentationError):
            used = set(re.findall(r"[A-Za-z_]\w*", source))

        removed = []
        kept = 0
        replacements = {}
        removals = set()

        for node in nodes:
            bindings = []
            for alias in node.names:
                if alias.name == "*":
                    bindings.append(("*", alias))
                    continue
                bound = alias.asname or alias.name.split(".")[0]
                bindings.append((bound, alias))

            if any(bound == "*" for bound, _alias in bindings):
                kept += 1
                continue

            used_bindings = [(bound, alias) for bound, alias in bindings
                             if bound in used]
            if not used_bindings:
                for index in range(node.lineno - 1,
                                   (node.end_lineno or node.lineno)):
                    removals.add(index)
                for bound, _alias in bindings:
                    removed.append(bound)
                continue

            kept += 1
            if len(used_bindings) != len(bindings):
                drop = {bound for bound, _alias in bindings} - \
                       {bound for bound, _alias in used_bindings}
                removed.extend(sorted(drop))
                if isinstance(node, ast.Import):
                    replacement = ["import %s" % _alias_text(alias)
                                   for _bound, alias in used_bindings]
                else:
                    module = "." * (node.level or 0) + (node.module or "")
                    names = ", ".join(_alias_text(alias)
                                      for _bound, alias in used_bindings)
                    replacement = ["from %s import %s" % (module, names)]
                replacements[node.lineno - 1] = replacement

        lines = source.splitlines()
        output = []
        for index, line in enumerate(lines):
            if index in replacements:
                output.extend(replacements[index])
                for follow in range(index + 1,
                                    (index + 1) + self._span_extra(index, nodes)):
                    if follow < len(lines):
                        removals.add(follow)
                continue
            if index in removals:
                continue
            output.append(line)

        content = self._cleanup("\n".join(output))
        return {
            "content": content,
            "changed": content != self._cleanup(source),
            "removed": sorted(set(removed)),
            "kept": kept,
        }

    @staticmethod
    def _span_extra(start_index, nodes):
        for node in nodes:
            if node.lineno - 1 == start_index:
                return (node.end_lineno or node.lineno) - node.lineno
        return 0

    # -- rename --------------------------------------------------------
    def rename(self, source, old, new):
        if not re.match(r"^[A-Za-z_]\w*$", old or "") or keyword.iskeyword(old):
            raise ValueError("Old name must be a valid identifier")
        if not re.match(r"^[A-Za-z_]\w*$", new or "") or keyword.iskeyword(new):
            raise ValueError("New name must be a valid identifier")

        replacements = {}
        count = 0
        try:
            tokens = list(tokenize.generate_tokens(
                io.StringIO(source).readline))
        except (tokenize.TokenError, IndentationError) as exc:
            raise ValueError("Cannot tokenize source: %s" % exc)

        for token in tokens:
            if token.type != tokenize.NAME or token.string != old:
                continue
            row, column = token.start
            replacements.setdefault(row - 1, []).append(column)
            count += 1

        if not count:
            return {"content": source, "changed": False, "replacements": 0}

        lines = source.splitlines()
        for row, columns in replacements.items():
            line = lines[row]
            for column in sorted(columns, reverse=True):
                line = line[:column] + new + line[column + len(old):]
            lines[row] = line

        content = "\n".join(lines) + ("\n" if source.endswith("\n") else "")
        return {"content": content, "changed": True, "replacements": count}

    # -- formatting ----------------------------------------------------
    def format_source(self, source):
        original = source
        source = source.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.rstrip() for line in source.split("\n")]
        output = []
        blank_run = 0
        changed_lines = 0
        for line in lines:
            if not line:
                blank_run += 1
                if blank_run > 2:
                    changed_lines += 1
                    continue
            else:
                blank_run = 0
            output.append(line)
        while output and not output[0]:
            output.pop(0)
        while output and not output[-1]:
            output.pop()
        content = "\n".join(output) + "\n"
        changed = content != original
        if changed and not changed_lines:
            changed_lines = abs(len(content.splitlines()) -
                                len(original.splitlines())) or 1
        return {
            "content": content,
            "changed": changed,
            "changed_lines": changed_lines,
        }

    @staticmethod
    def _cleanup(source):
        lines = [line.rstrip() for line in source.replace("\r\n", "\n")
                 .replace("\r", "\n").split("\n")]
        output = []
        blanks = 0
        for line in lines:
            if not line:
                blanks += 1
                if blanks > 2:
                    continue
            else:
                blanks = 0
            output.append(line)
        while output and not output[0]:
            output.pop(0)
        while output and not output[-1]:
            output.pop()
        return "\n".join(output) + "\n"

    # -- orchestration -------------------------------------------------
    def apply(self, path, operations=None, write=False):
        """Apply a list of operations to one file.

        operations examples::

            {"op": "organize_imports"}
            {"op": "remove_unused_imports"}
            {"op": "format"}
            {"op": "rename", "old": "foo", "new": "bar"}
        """
        operations = operations or [{"op": "format"}]
        original = util.read_text(path)
        content = original
        applied = []

        for operation in operations:
            name = operation.get("op")
            if name == "organize_imports":
                result = self.organize_imports(
                    content, operation.get("local_modules"))
                content = result["content"]
                applied.append({"op": name,
                                "imports": result["import_count"],
                                "changed": result["changed"]})
            elif name == "remove_unused_imports":
                result = self.remove_unused_imports(content)
                content = result["content"]
                applied.append({"op": name, "removed": result["removed"],
                                "changed": result["changed"]})
            elif name == "format":
                result = self.format_source(content)
                content = result["content"]
                applied.append({"op": name, "changed": result["changed"]})
            elif name == "rename":
                result = self.rename(content, operation["old"],
                                     operation["new"])
                content = result["content"]
                applied.append({"op": name, "old": operation["old"],
                                "new": operation["new"],
                                "replacements": result["replacements"]})
            else:
                raise ValueError("Unknown refactor operation: %s" % name)

        changed = content != original
        if write and changed:
            util.write_text(path, content)

        return {
            "file": util.relpath(self.root, path) if os.path.isabs(path) else path,
            "changed": changed,
            "written": bool(write and changed),
            "operations": applied,
            "before_lines": util.count_lines(original),
            "after_lines": util.count_lines(content),
            "content": content,
        }
