"""Project scaffolding for several local-first stacks.

Each scaffold writes a complete, runnable starting point with tests and a
README. No package downloads are performed.
"""

import json
import os
import shutil
import subprocess

from . import util
from .generator import camel, kebab, pascal, snake

PROJECT_TYPES = [
    "python-cli",
    "python-lib",
    "python-api",
    "web-static",
    "node-cli",
    "go-cli",
    "rust-cli",
    "data-analysis",
]

GITIGNORE = """__pycache__/
*.pyc
.venv/
venv/
node_modules/
dist/
build/
target/
*.log
.env
"""


def _replace(template, mapping):
    output = template
    for key, value in mapping.items():
        output = output.replace(key, value)
    return output


class Scaffolder:
    """Create complete project skeletons on disk."""

    def __init__(self, root=None):
        self.root = os.path.abspath(root) if root else os.getcwd()

    def create(self, project_type, target, name=None, force=False):
        project_type = project_type.lower()
        if project_type not in PROJECT_TYPES:
            raise ValueError("Unknown project type '%s' (choose from %s)"
                             % (project_type, ", ".join(PROJECT_TYPES)))
        target = os.path.abspath(os.path.join(self.root, target))
        project_name = name or os.path.basename(target.rstrip("\\/")) or "app"

        if os.path.isdir(target) and os.listdir(target) and not force:
            raise FileExistsError(
                "Target directory is not empty: %s (use force=True)" % target)

        files = self._files_for(project_type, project_name)
        written = []
        for relative, content in files.items():
            path = os.path.join(target, relative)
            util.write_text(path, content)
            written.append(relative.replace(os.sep, "/"))

        verification = self._verify(target, written)
        return {
            "project_type": project_type,
            "name": project_name,
            "root": target,
            "file_count": len(written),
            "files": sorted(written),
            "verification": verification,
        }

    # ------------------------------------------------------------------
    def _files_for(self, project_type, name):
        handler = getattr(self, "_scaffold_" + project_type.replace("-", "_"))
        return handler(name)

    def _common_readme(self, name, project_type, run_command, test_command):
        return """# {name}

Local-first `{project_type}` project.

## Features

- 100% local execution
- No external AI platform calls
- No cloud dependencies
- Built-in tests

## Run

```bash
{run_command}
```

## Test

```bash
{test_command}
```

## Layout

```
{tree}
```

## License

Add the licence that applies to this project.
""".format(name=name, project_type=project_type, run_command=run_command,
           test_command=test_command,
           tree="src/  application code\ntests/  automated tests\ndocs/  documentation")

    # -- python --------------------------------------------------------
    def _scaffold_python_cli(self, name):
        package = snake(name)
        module = package.replace("-", "_")
        files = {
            ".gitignore": GITIGNORE,
            "requirements.txt": "# Standard library only by default.\n",
            "README.md": self._common_readme(
                name, "python-cli",
                "python run.py --help", "python -m unittest discover -s tests -v"),
            "run.py": (
                "#!/usr/bin/env python3\n"
                '"""Launcher for %s."""\n\n'
                "import sys\n"
                "from pathlib import Path\n\n"
                'sys.path.insert(0, str(Path(__file__).parent / "src"))\n\n'
                "from %s.cli import main\n\n\n"
                "if __name__ == \"__main__\":\n"
                "    raise SystemExit(main())\n" % (name, module)
            ),
            "src/%s/__init__.py" % module: (
                '"""%s package."""\n\n__version__ = "0.1.0"\n' % name
            ),
            "src/%s/cli.py" % module: _replace(
                PY_CLI_TEMPLATE,
                {"__SNAKE__": module, "__KEBAB__": kebab(name),
                 "__DESC__": "%s command line interface." % name},
            ),
            "src/%s/__main__.py" % module: (
                "from .cli import main\n\n\n"
                "if __name__ == \"__main__\":\n"
                "    raise SystemExit(main())\n"
            ),
            "tests/test_cli.py": _replace(
                PY_CLI_TEST,
                {"__MODULE__": module, "__PASCAL__": pascal(name)},
            ),
            "docs/API.md": "# API\n\nRun `python -m coding_master docs .` to "
                           "regenerate this file.\n",
        }
        return files

    def _scaffold_python_lib(self, name):
        module = snake(name)
        files = {
            ".gitignore": GITIGNORE,
            "requirements.txt": "# Standard library only by default.\n",
            "README.md": self._common_readme(
                name, "python-lib",
                "python -c \"import sys; sys.path.insert(0, 'src'); "
                "import %s; print(%s.greet('world'))\"" % (module, module),
                "python -m unittest discover -s tests -v"),
            "src/%s/__init__.py" % module: (
                '"""%s library."""\n\n'
                "from .core import greet, summarize\n\n"
                '__version__ = "0.1.0"\n\n'
                '__all__ = ["greet", "summarize", "__version__"]\n' % name
            ),
            "src/%s/core.py" % module: PY_LIB_CORE,
            "tests/test_core.py": _replace(
                PY_LIB_TEST, {"__MODULE__": module}),
            "docs/API.md": "# API\n\n- `greet(name)` returns a greeting.\n"
                           "- `summarize(values)` returns count/min/max/mean.\n",
        }
        return files

    def _scaffold_python_api(self, name):
        module = snake(name)
        files = {
            ".gitignore": GITIGNORE,
            "requirements.txt": "# Standard library only (http.server).\n",
            "README.md": self._common_readme(
                name, "python-api", "python app.py",
                "python -m unittest discover -s tests -v"),
            "app.py": _replace(PY_API_TEMPLATE,
                               {"__SNAKE__": module, "__KEBAB__": kebab(name)}),
            "tests/test_app.py": PY_API_TEST,
            "docs/API.md": "# API\n\n- `GET /health` -> service status\n",
        }
        return files

    # -- web -----------------------------------------------------------
    def _scaffold_web_static(self, name):
        return {
            ".gitignore": GITIGNORE,
            "index.html": _replace(WEB_INDEX,
                                   {"__NAME__": name,
                                    "__KEBAB__": kebab(name)}),
            "style.css": WEB_CSS,
            "app.js": WEB_JS,
            "README.md": self._common_readme(
                name, "web-static", "open index.html in a browser",
                "manual smoke test in the browser"),
        }

    def _scaffold_node_cli(self, name):
        module = camel(name)
        files = {
            ".gitignore": GITIGNORE,
            "package.json": json.dumps({
                "name": kebab(name),
                "version": "0.1.0",
                "private": True,
                "description": "%s command line tool" % name,
                "bin": {"%s" % kebab(name): "bin/%s.js" % kebab(name)},
                "scripts": {"start": "node bin/%s.js" % kebab(name),
                            "test": "node --test"},
                "engines": {"node": ">=18"},
            }, indent=2) + "\n",
            "bin/%s.js" % kebab(name): _replace(
                NODE_CLI, {"__CAMEL__": module, "__KEBAB__": kebab(name)}),
            "lib/%s.js" % module: _replace(NODE_LIB,
                                          {"__CAMEL__": module}),
            "test/%s.test.js" % module: _replace(
                NODE_TEST, {"__CAMEL__": module}),
            "README.md": self._common_readme(
                name, "node-cli", "npm start -- --help", "npm test"),
        }
        return files

    # -- systems -------------------------------------------------------
    def _scaffold_go_cli(self, name):
        module = snake(name)
        files = {
            ".gitignore": GITIGNORE,
            "go.mod": "module %s\n\ngo 1.21\n" % module,
            "main.go": _replace(GO_MAIN, {"__KEBAB__": kebab(name)}),
            "README.md": self._common_readme(
                name, "go-cli", "go run .", "go test ./..."),
        }
        return files

    def _scaffold_rust_cli(self, name):
        module = snake(name)
        files = {
            ".gitignore": GITIGNORE,
            "Cargo.toml": (
                "[package]\n"
                'name = "%s"\n'
                'version = "0.1.0"\n'
                'edition = "2021"\n\n'
                "[dependencies]\n" % module
            ),
            "src/main.rs": _replace(RUST_MAIN, {"__KEBAB__": kebab(name)}),
            "README.md": self._common_readme(
                name, "rust-cli", "cargo run", "cargo test"),
        }
        return files

    def _scaffold_data_analysis(self, name):
        module = snake(name)
        files = {
            ".gitignore": GITIGNORE,
            "requirements.txt": "# Standard library only (csv, statistics).\n",
            "README.md": self._common_readme(
                name, "data-analysis", "python analysis.py data/sample.csv",
                "python -m unittest discover -s tests -v"),
            "analysis.py": DATA_ANALYSIS,
            "data/sample.csv": "name,value\nalpha,10\nbeta,20\ngamma,30\n",
            "tests/test_analysis.py": DATA_TEST,
            "docs/API.md": "# API\n\n- `summarize(rows)` computes count, "
                           "min, max and mean.\n",
        }
        return files

    # -- verification --------------------------------------------------
    def _verify(self, target, written):
        results = []
        for relative in written:
            path = os.path.join(target, relative.replace("/", os.sep))
            suffix = os.path.splitext(path)[1].lower()
            if suffix == ".py":
                try:
                    with open(path, "r", encoding="utf-8") as handle:
                        compile(handle.read(), path, "exec")
                    results.append({"file": relative, "status": "ok"})
                except SyntaxError as exc:
                    results.append({"file": relative, "status": "failed",
                                    "detail": str(exc)})
            elif suffix == ".js":
                node = shutil.which("node")
                if not node:
                    results.append({"file": relative, "status": "skipped"})
                    continue
                completed = subprocess.run([node, "--check", path],
                                           capture_output=True, text=True,
                                           timeout=30)
                results.append({
                    "file": relative,
                    "status": "ok" if completed.returncode == 0 else "failed",
                    "detail": (completed.stderr or "").strip()[:300] or None,
                })
            elif suffix == ".go":
                gofmt = shutil.which("gofmt")
                if not gofmt:
                    results.append({"file": relative, "status": "skipped"})
                    continue
                completed = subprocess.run([gofmt, "-e", path],
                                           capture_output=True, text=True,
                                           timeout=30)
                results.append({
                    "file": relative,
                    "status": "ok" if completed.returncode == 0 else "failed",
                    "detail": (completed.stderr or "").strip()[:300] or None,
                })
        return results


# ---------------------------------------------------------------- templates

PY_CLI_TEMPLATE = '''"""__DESC__"""

import argparse
import sys


def build_parser():
    """Build the command line parser."""
    parser = argparse.ArgumentParser(prog="__KEBAB__",
                                     description="__DESC__")
    parser.add_argument("input", nargs="?", default="", help="input value")
    parser.add_argument("--verbose", action="store_true", help="extra output")
    return parser


def main(argv=None):
    """Run the command line application."""
    args = build_parser().parse_args(argv)
    if args.verbose:
        print("input:", args.input)
    print("__KEBAB__:", args.input or "(no input)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

PY_CLI_TEST = '''import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.__MODULE__.cli import build_parser, main


class TestCli(unittest.TestCase):
    def test_parser_defaults(self):
        args = build_parser().parse_args([])
        self.assertEqual(args.input, "")
        self.assertFalse(args.verbose)

    def test_parser_input(self):
        args = build_parser().parse_args(["hello", "--verbose"])
        self.assertEqual(args.input, "hello")
        self.assertTrue(args.verbose)

    def test_main_returns_zero(self):
        self.assertEqual(main(["hello"]), 0)


if __name__ == "__main__":
    unittest.main()
'''

PY_LIB_CORE = '''"""Core helpers for the library."""

from statistics import mean


def greet(name):
    """Return a friendly greeting for name."""
    cleaned = (name or "").strip()
    if not cleaned:
        return "Hello!"
    return "Hello, %s!" % cleaned


def summarize(values):
    """Return count, minimum, maximum and mean for numeric values."""
    numbers = [float(value) for value in values]
    if not numbers:
        return {"count": 0, "min": None, "max": None, "mean": None}
    return {
        "count": len(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": mean(numbers),
    }
'''

PY_LIB_TEST = '''import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from __MODULE__ import greet, summarize


class TestGreet(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(greet("world"), "Hello, world!")

    def test_empty(self):
        self.assertEqual(greet(""), "Hello!")


class TestSummarize(unittest.TestCase):
    def test_numbers(self):
        result = summarize([1, 2, 3])
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["min"], 1.0)
        self.assertEqual(result["max"], 3.0)
        self.assertEqual(result["mean"], 2.0)

    def test_empty(self):
        self.assertEqual(summarize([])["count"], 0)


if __name__ == "__main__":
    unittest.main()
'''

PY_API_TEMPLATE = '''#!/usr/bin/env python3
"""Local JSON API for __KEBAB__."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "0.1.0"


def build_payload(path):
    """Return (status, payload) for a request path."""
    if path in ("/", "/health"):
        return 200, {"service": "__KEBAB__", "version": VERSION,
                     "status": "ok"}
    return 404, {"error": "not found", "path": path}


class Handler(BaseHTTPRequestHandler):
    """Serve the local JSON API."""

    server_version = "__KEBAB__/" + VERSION

    def do_GET(self):
        status, payload = build_payload(self.path)
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


def serve(host="127.0.0.1", port=8000):
    """Start the server (blocking)."""
    server = ThreadingHTTPServer((host, port), Handler)
    print("__KEBAB__ listening on http://%s:%d" % (host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
'''

PY_API_TEST = '''import unittest

from app import Handler, build_payload


class TestPayloads(unittest.TestCase):
    def test_health(self):
        status, payload = build_payload("/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")

    def test_missing(self):
        status, payload = build_payload("/nope")
        self.assertEqual(status, 404)
        self.assertIn("error", payload)

    def test_handler_is_http(self):
        self.assertTrue(hasattr(Handler, "do_GET"))


if __name__ == "__main__":
    unittest.main()
'''

WEB_INDEX = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__NAME__</title>
  <meta name="description" content="__NAME__ - a local-first web application.">
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="site-header">
    <h1>__NAME__</h1>
    <p class="tagline">Runs entirely in your browser. No tracking.</p>
  </header>
  <main>
    <section aria-labelledby="demo-title">
      <h2 id="demo-title">Local demo</h2>
      <form id="demo-form">
        <label for="name">Your name</label>
        <input id="name" name="name" autocomplete="name" placeholder="Ada">
        <button type="submit">Greet</button>
      </form>
      <p id="output" role="status" aria-live="polite"></p>
    </section>
  </main>
  <footer>
    <p>&copy; <span id="year"></span> __NAME__</p>
  </footer>
  <script src="app.js"></script>
</body>
</html>
'''

WEB_CSS = ''':root {
  color-scheme: light dark;
  --accent: #0f766e;
  --surface: #ffffff;
  --text: #14201f;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background: #f4f7f6;
  color: var(--text);
  line-height: 1.6;
}

.site-header,
main,
footer {
  max-width: 52rem;
  margin: 0 auto;
  padding: 1.5rem;
}

.site-header {
  border-bottom: 1px solid #d7e0de;
}

h1 {
  margin: 0;
  font-size: 2rem;
}

.tagline {
  color: #4b5f5c;
}

form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: end;
}

label {
  flex-basis: 100%;
  font-weight: 600;
}

input,
button {
  padding: 0.6rem 0.8rem;
  font-size: 1rem;
  border-radius: 0.4rem;
  border: 1px solid #b9c7c4;
}

button {
  background: var(--accent);
  border-color: var(--accent);
  color: #ffffff;
  cursor: pointer;
}

button:hover {
  filter: brightness(1.1);
}

#output {
  min-height: 1.6rem;
  font-weight: 600;
}

footer {
  color: #4b5f5c;
  font-size: 0.9rem;
}
'''

WEB_JS = """'use strict';

const form = document.getElementById('demo-form');
const input = document.getElementById('name');
const output = document.getElementById('output');
const year = document.getElementById('year');

if (year) {
  year.textContent = String(new Date().getFullYear());
}

if (form && input && output) {
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const name = input.value.trim();
    output.textContent = name ? `Hello, ${name}!` : 'Hello!';
  });
}
"""

NODE_CLI = """#!/usr/bin/env node
'use strict';

const { __CAMEL__ } = require('../lib/__CAMEL__');

function main(argv) {
  if (argv.includes('--help')) {
    console.log('usage: __KEBAB__ [input]');
    return 0;
  }
  console.log(__CAMEL__(argv.join(' ')));
  return 0;
}

if (require.main === module) {
  process.exit(main(process.argv.slice(2)));
}

module.exports = { main };
"""

NODE_LIB = """'use strict';

/**
 * Return a greeting for the given input.
 */
function __CAMEL__(value) {
  const cleaned = String(value || '').trim();
  return cleaned ? `Hello, ${cleaned}!` : 'Hello!';
}

module.exports = { __CAMEL__ };
"""

NODE_TEST = """'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { __CAMEL__ } = require('../lib/__CAMEL__');

test('greets a value', () => {
  assert.strictEqual(__CAMEL__('world'), 'Hello, world!');
});

test('handles empty input', () => {
  assert.strictEqual(__CAMEL__(''), 'Hello!');
});
"""

GO_MAIN = '''package main

import (
	"flag"
	"fmt"
)

func main() {
	verbose := flag.Bool("verbose", false, "extra output")
	flag.Parse()

	input := ""
	if flag.NArg() > 0 {
		input = flag.Arg(0)
	}
	if *verbose {
		fmt.Println("input:", input)
	}
	fmt.Printf("__KEBAB__: %s\\n", input)
}
'''

RUST_MAIN = '''use std::env;

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.iter().any(|arg| arg == "--help") {
        println!("usage: __KEBAB__ [input]");
        return;
    }
    println!("__KEBAB__: {}", args.join(" "));
}
'''

DATA_ANALYSIS = '''#!/usr/bin/env python3
"""Summarise a CSV file using only the standard library."""

import csv
import json
import sys
from statistics import mean


def summarize(rows):
    """Return count, min, max and mean for the 'value' column."""
    values = []
    for row in rows:
        try:
            values.append(float(row["value"]))
        except (KeyError, TypeError, ValueError):
            continue
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
    }


def load_rows(path):
    """Load CSV rows as dictionaries."""
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main(argv=None):
    """Run the analysis and print a JSON report."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: python analysis.py <file.csv>")
        return 2
    report = summarize(load_rows(argv[0]))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

DATA_TEST = '''import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis import load_rows, summarize


class TestSummarize(unittest.TestCase):
    def test_values(self):
        result = summarize([{"value": "1"}, {"value": "3"}])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["min"], 1.0)
        self.assertEqual(result["max"], 3.0)
        self.assertEqual(result["mean"], 2.0)

    def test_empty(self):
        self.assertEqual(summarize([])["count"], 0)

    def test_sample_file(self):
        path = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "data", "sample.csv")
        rows = load_rows(path)
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
'''
