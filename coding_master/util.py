"""Shared helpers for the local coding master engine.

QANOON: standard library only. No network, no external AI, no FFmpeg.
"""

import json
import os
import re

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", "dist", "build", ".venv", "venv",
    ".pytest_cache", ".mypy_cache", ".idea", ".vscode", "file_links",
    "data", ".next", "target", "bin", "obj", ".tox", ".eggs",
}

CODE_EXTS = {
    ".py", ".pyw", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rs",
    ".java", ".kt", ".c", ".h", ".cpp", ".cc", ".hpp", ".cs", ".rb", ".php",
    ".swift", ".sql", ".sh", ".ps1", ".bat", ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml", ".md", ".xml", ".ini", ".cfg",
    ".dockerfile", ".mk", ".gradle",
}

LANG_BY_EXT = {
    ".py": "python", ".pyw": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ts": "typescript", ".tsx": "tsx", ".jsx": "jsx",
    ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin",
    ".c": "c", ".h": "c", ".cpp": "cpp", ".cc": "cpp", ".hpp": "cpp",
    ".cs": "csharp", ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".sql": "sql", ".sh": "shell", ".ps1": "powershell", ".bat": "batch",
    ".html": "html", ".css": "css", ".scss": "scss",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".md": "markdown", ".xml": "xml", ".ini": "ini", ".cfg": "ini",
}

TEXT_EXTS = CODE_EXTS | {".txt", ".env", ".gitignore", ".editorconfig"}

MAX_FILE_BYTES = 2 * 1024 * 1024


def language_for(path):
    """Return a language name for a path (by basename or extension)."""
    base = os.path.basename(path).lower()
    if base in ("dockerfile", "containerfile"):
        return "docker"
    if base in ("makefile", "gnumakefile"):
        return "makefile"
    if base in ("gemfile", "rakefile"):
        return "ruby"
    if base == ".gitignore":
        return "gitignore"
    return LANG_BY_EXT.get(os.path.splitext(base)[1], "text")


def is_text_file(path):
    ext = os.path.splitext(path)[1].lower()
    base = os.path.basename(path).lower()
    if base in ("dockerfile", "makefile", ".gitignore", ".env"):
        return True
    return ext in TEXT_EXTS


def read_text(path):
    """Read a text file, tolerating broken encodings and BOMs."""
    with open(path, "rb") as handle:
        raw = handle.read()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def write_text(path, text):
    """Write text with LF newlines, creating parent directories."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(normalized)
    return path


def write_json(path, data):
    return write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def iter_files(root, exts=None, max_files=None, include_data=False):
    """Yield absolute paths of text/code files under root.

    Skips vendor, build and cache directories. ``include_data`` allows the
    (usually huge) ``data`` tree when explicitly requested.
    """
    wanted = set(exts) if exts else None
    count = 0
    skip = set(SKIP_DIRS)
    if include_data:
        skip.discard("data")

    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in skip and not d.startswith("."))
        for name in sorted(files):
            if name.startswith(".") and name not in (".gitignore", ".env"):
                continue
            path = os.path.join(current, name)
            ext = os.path.splitext(name)[1].lower()
            if wanted is not None:
                if ext not in wanted and name.lower() not in wanted:
                    continue
            elif not is_text_file(path):
                continue
            try:
                if os.path.getsize(path) > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield path
            count += 1
            if max_files is not None and count >= max_files:
                return


def relpath(root, path):
    try:
        return os.path.relpath(path, root).replace(os.sep, "/")
    except ValueError:
        return path.replace(os.sep, "/")


def count_lines(text):
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def slugify(value):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "item"


def clamp(value, low, high):
    return max(low, min(high, value))


def snippet(text, line, radius=0):
    lines = text.splitlines()
    index = line - 1
    if index < 0 or index >= len(lines):
        return ""
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return "\n".join(lines[start:end]).strip()
