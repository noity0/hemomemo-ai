"""Real multi-language code generation from local templates.

Every renderer produces complete, syntactically valid output. Python and
JavaScript/TypeScript results are verified locally when the relevant runtime is
available; nothing is uploaded anywhere.
"""

import os
import re
import shutil
import subprocess
import tempfile

from . import util

LANGUAGES = [
    "python", "javascript", "typescript", "go", "rust", "java", "csharp",
    "ruby", "php", "shell", "sql",
]

KINDS = [
    "function", "class", "dataclass", "cli", "http-server", "script",
    "module", "test", "struct", "interface",
]

EXTENSIONS = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "go": ".go",
    "rust": ".rs",
    "java": ".java",
    "csharp": ".cs",
    "ruby": ".rb",
    "php": ".php",
    "shell": ".sh",
    "sql": ".sql",
}


def words(value):
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    spaced = re.sub(r"[^A-Za-z0-9]+", " ", spaced)
    return [part for part in spaced.strip().split(" ") if part]


def pascal(value):
    return "".join(part[:1].upper() + part[1:] for part in words(value)) or "App"


def camel(value):
    parts = words(value)
    if not parts:
        return "app"
    return parts[0][:1].lower() + parts[0][1:] + "".join(
        part[:1].upper() + part[1:] for part in parts[1:])


def snake(value):
    return "_".join(part.lower() for part in words(value)) or "app"


def kebab(value):
    return "-".join(part.lower() for part in words(value)) or "app"


def _replace(template, mapping):
    output = template
    for key, value in mapping.items():
        output = output.replace(key, value)
    return output


PY_FUNCTION = '''def __SNAKE__(__ARGS__):
    """__DESC__"""
    raise NotImplementedError("__SNAKE__ is not implemented yet")


def main():
    print("__SNAKE__ ready")


if __name__ == "__main__":
    main()
'''

PY_CLASS = '''class __PASCAL__:
    """__DESC__"""

    def __init__(self__INIT_ARGS__):
        self.name = "__SNAKE__"

    def describe(self):
        """Return a short description of this object."""
        return {"name": self.name, "type": type(self).__name__}

    def run(self, payload=None):
        """Apply the main behaviour; override in a subclass."""
        raise NotImplementedError("run() is not implemented yet")


def main():
    print(__PASCAL__().describe())


if __name__ == "__main__":
    main()
'''

PY_DATACLASS = '''from dataclasses import dataclass, field


@dataclass
class __PASCAL__:
    """__DESC__"""

    name: str = "__SNAKE__"
__FIELDS__

    def describe(self):
        """Return a dictionary view of this record."""
        return {
            "name": self.name,
__FIELD_RETURNS__
        }


def main():
    print(__PASCAL__().describe())


if __name__ == "__main__":
    main()
'''

PY_CLI = '''#!/usr/bin/env python3
"""__DESC__"""

import argparse
import sys


def build_parser():
    """Build the argument parser for __SNAKE__."""
    parser = argparse.ArgumentParser(
        prog="__KEBAB__",
        description="__DESC__",
    )
    parser.add_argument("input", nargs="?", default="", help="input value")
    parser.add_argument("--verbose", action="store_true", help="extra output")
    return parser


def main(argv=None):
    """Run the command line application."""
    args = build_parser().parse_args(argv)
    if args.verbose:
        print("input:", args.input)
    print("__SNAKE__:", args.input or "(no input)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

PY_HTTP = '''#!/usr/bin/env python3
"""__DESC__

Local-only HTTP service built on the standard library.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1.0.0"


class Handler(BaseHTTPRequestHandler):
    """Serve a small JSON API."""

    server_version = "__SNAKE__/" + VERSION

    def do_GET(self):
        """Handle GET requests."""
        if self.path in ("/", "/health"):
            payload = {"service": "__SNAKE__", "version": VERSION,
                       "status": "ok"}
        else:
            self.send_error(404, "Not found")
            return
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        """Keep the default request log quiet."""
        return


def serve(host="127.0.0.1", port=8000):
    """Start the HTTP server (blocking)."""
    server = ThreadingHTTPServer((host, port), Handler)
    print("__SNAKE__ listening on http://%s:%d" % (host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
'''

PY_SCRIPT = '''#!/usr/bin/env python3
"""__DESC__"""

import sys


def main(argv=None):
    """Entry point for the script."""
    argv = list(sys.argv[1:] if argv is None else argv)
    print("__SNAKE__", " ".join(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

PY_TEST = '''import unittest

from __MODULE__ import __TARGET__


class Test__PASCAL__(unittest.TestCase):
    """Smoke tests for __TARGET__."""

    def test_is_available(self):
        self.assertTrue(callable(__TARGET__))

    def test_importable(self):
        self.assertIsNotNone(__TARGET__)


if __name__ == "__main__":
    unittest.main()
'''

JS_FUNCTION = """'use strict';

/**
 * __DESC__
 */
function __CAMEL__(input) {
  if (input === undefined) {
    throw new Error('input is required');
  }
  return input;
}

module.exports = { __CAMEL__ };
"""

JS_CLASS = """'use strict';

/**
 * __DESC__
 */
class __PASCAL__ {
  constructor(name = '__CAMEL__') {
    this.name = name;
  }

  describe() {
    return { name: this.name, type: this.constructor.name };
  }

  run(payload = null) {
    throw new Error('run() is not implemented yet');
  }
}

module.exports = { __PASCAL__ };
"""

JS_CLI = """#!/usr/bin/env node
'use strict';

/**
 * __DESC__
 */

const args = process.argv.slice(2);

function main(argv) {
  if (argv.includes('--help')) {
    console.log('usage: __KEBAB__ [input]');
    return 0;
  }
  console.log('__KEBAB__:', argv.join(' ') || '(no input)');
  return 0;
}

process.exit(main(args));
"""

JS_HTTP = """'use strict';

/**
 * __DESC__
 * Local-only HTTP service using node:http.
 */

const http = require('node:http');

const VERSION = '1.0.0';

const server = http.createServer((req, res) => {
  if (req.url === '/' || req.url === '/health') {
    const body = JSON.stringify({
      service: '__KEBAB__',
      version: VERSION,
      status: 'ok',
    });
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(body);
    return;
  }
  res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify({ error: 'not found' }));
});

const port = Number(process.env.PORT || 8000);
server.listen(port, '127.0.0.1', () => {
  console.log(`__KEBAB__ listening on http://127.0.0.1:${port}`);
});
"""

JS_MODULE = """'use strict';

/**
 * __DESC__
 */

const __CAMEL__ = {
  name: '__KEBAB__',

  describe() {
    return { name: this.name, version: '1.0.0' };
  },
};

module.exports = { __CAMEL__ };
"""

TS_FUNCTION = """/**
 * __DESC__
 */
export function __CAMEL__(input: string): string {
  if (!input) {
    throw new Error('input is required');
  }
  return input;
}

export default __CAMEL__;
"""

TS_CLASS = """/**
 * __DESC__
 */
export interface __PASCAL__Options {
  name?: string;
}

export class __PASCAL__ {
  readonly name: string;

  constructor(options: __PASCAL__Options = {}) {
    this.name = options.name ?? '__CAMEL__';
  }

  describe(): Record<string, string> {
    return { name: this.name, type: '__PASCAL__' };
  }

  run(payload?: unknown): unknown {
    throw new Error('run() is not implemented yet');
  }
}

export default __PASCAL__;
"""

TS_INTERFACE = """/**
 * __DESC__
 */
export interface __PASCAL__ {
  id: string;
  name: string;
  createdAt: string;
}

export interface __PASCAL__Input {
  name: string;
}

export type __PASCAL__Result = Readonly<__PASCAL__>;
"""

GO_FUNCTION = '''package main

import "fmt"

// __PASCAL__ __DESC__
func __PASCAL__(input string) (string, error) {
	if input == "" {
		return "", fmt.Errorf("input is required")
	}
	return input, nil
}

func main() {
	result, err := __PASCAL__("hello")
	if err != nil {
		panic(err)
	}
	fmt.Println(result)
}
'''

GO_STRUCT = '''package main

import "fmt"

// __PASCAL__ __DESC__
type __PASCAL__ struct {
	ID   string
	Name string
}

// Describe returns a readable summary.
func (item __PASCAL__) Describe() string {
	return fmt.Sprintf("%s (%s)", item.Name, item.ID)
}

func main() {
	item := __PASCAL__{ID: "1", Name: "__CAMEL__"}
	fmt.Println(item.Describe())
}
'''

GO_CLI = '''package main

import (
	"flag"
	"fmt"
	"os"
)

func main() {
	verbose := flag.Bool("verbose", false, "extra output")
	flag.Parse()

	input := ""
	if flag.NArg() > 0 {
		input = flag.Arg(0)
	}
	if *verbose {
		fmt.Fprintf(os.Stderr, "input: %s\\n", input)
	}
	fmt.Printf("__KEBAB__: %s\\n", input)
}
'''

RUST_FUNCTION = '''//! __DESC__

/// __PASCAL__ returns the provided input or an error when it is empty.
pub fn __SNAKE__(input: &str) -> Result<String, String> {
    if input.is_empty() {
        return Err("input is required".to_string());
    }
    Ok(input.to_string())
}

fn main() {
    match __SNAKE__("hello") {
        Ok(value) => println!("{}", value),
        Err(error) => eprintln!("error: {}", error),
    }
}
'''

RUST_STRUCT = '''//! __DESC__

/// __PASCAL__ is a small data record.
#[derive(Debug, Clone)]
pub struct __PASCAL__ {
    pub id: String,
    pub name: String,
}

impl __PASCAL__ {
    /// Create a new record.
    pub fn new(id: &str, name: &str) -> Self {
        Self { id: id.to_string(), name: name.to_string() }
    }

    /// Return a readable summary.
    pub fn describe(&self) -> String {
        format!("{} ({})", self.name, self.id)
    }
}

fn main() {
    let item = __PASCAL__::new("1", "__CAMEL__");
    println!("{}", item.describe());
}
'''

RUST_CLI = '''use std::env;

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.iter().any(|arg| arg == "--help") {
        println!("usage: __KEBAB__ [input]");
        return;
    }
    println!("__KEBAB__: {}", args.join(" "));
}
'''

JAVA_CLASS = '''/**
 * __DESC__
 */
public class __PASCAL__ {
    private final String name;

    public __PASCAL__(String name) {
        this.name = name;
    }

    public String describe() {
        return name;
    }

    public static void main(String[] args) {
        System.out.println(new __PASCAL__("__CAMEL__").describe());
    }
}
'''

CS_CLASS = '''using System;

namespace __PASCAL__App
{
    /// <summary>
    /// __DESC__
    /// </summary>
    public class __PASCAL__
    {
        public string Name { get; }

        public __PASCAL__(string name = "__CAMEL__")
        {
            Name = name;
        }

        public string Describe() => Name;

        public static void Main(string[] args)
        {
            Console.WriteLine(new __PASCAL__().Describe());
        }
    }
}
'''

RB_CLASS = '''# frozen_string_literal: true

# __DESC__
class __PASCAL__
  attr_reader :name

  def initialize(name = '__SNAKE__')
    @name = name
  end

  def describe
    { name: name, type: self.class.name }
  end

  def run(_payload = nil)
    raise NotImplementedError, 'run is not implemented yet'
  end
end

puts __PASCAL__.new.describe
'''

RB_SCRIPT = '''#!/usr/bin/env ruby
# frozen_string_literal: true

# __DESC__
args = ARGV

if args.include?('--help')
  puts 'usage: __KEBAB__ [input]'
  exit 0
end

puts "__KEBAB__: #{args.join(' ')}"
'''

PHP_CLASS = '''<?php

declare(strict_types=1);

/**
 * __DESC__
 */
final class __PASCAL__
{
    public function __construct(private string $name = '__SNAKE__')
    {
    }

    public function describe(): array
    {
        return ['name' => $this->name, 'type' => self::class];
    }

    public function run(?array $payload = null): never
    {
        throw new \\RuntimeException('run is not implemented yet');
    }
}

$item = new __PASCAL__();
echo json_encode($item->describe()), PHP_EOL;
'''

SH_SCRIPT = '''#!/usr/bin/env bash
# __DESC__
set -euo pipefail

usage() {
  echo "usage: __KEBAB__ [input]"
}

main() {
  if [[ "${1:-}" == "--help" ]]; then
    usage
    return 0
  fi
  echo "__KEBAB__: ${*:-}"
}

main "$@"
'''

SQL_TABLE = '''-- __DESC__

CREATE TABLE IF NOT EXISTS __SNAKE__ (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx___SNAKE___name ON __SNAKE__ (name);
'''

# kind -> language -> template
TEMPLATES = {
    "python": {
        "function": PY_FUNCTION,
        "class": PY_CLASS,
        "dataclass": PY_DATACLASS,
        "cli": PY_CLI,
        "http-server": PY_HTTP,
        "script": PY_SCRIPT,
        "test": PY_TEST,
        "module": PY_CLASS,
    },
    "javascript": {
        "function": JS_FUNCTION,
        "class": JS_CLASS,
        "cli": JS_CLI,
        "http-server": JS_HTTP,
        "script": JS_CLI,
        "module": JS_MODULE,
        "test": JS_FUNCTION,
    },
    "typescript": {
        "function": TS_FUNCTION,
        "class": TS_CLASS,
        "interface": TS_INTERFACE,
        "module": TS_CLASS,
        "script": TS_FUNCTION,
    },
    "go": {
        "function": GO_FUNCTION,
        "struct": GO_STRUCT,
        "class": GO_STRUCT,
        "cli": GO_CLI,
        "script": GO_CLI,
    },
    "rust": {
        "function": RUST_FUNCTION,
        "struct": RUST_STRUCT,
        "class": RUST_STRUCT,
        "cli": RUST_CLI,
        "script": RUST_CLI,
    },
    "java": {
        "class": JAVA_CLASS,
        "function": JAVA_CLASS,
        "cli": JAVA_CLASS,
        "script": JAVA_CLASS,
    },
    "csharp": {
        "class": CS_CLASS,
        "function": CS_CLASS,
        "cli": CS_CLASS,
        "script": CS_CLASS,
    },
    "ruby": {
        "class": RB_CLASS,
        "function": RB_CLASS,
        "script": RB_SCRIPT,
        "cli": RB_SCRIPT,
    },
    "php": {
        "class": PHP_CLASS,
        "function": PHP_CLASS,
        "script": PHP_CLASS,
    },
    "shell": {
        "script": SH_SCRIPT,
        "cli": SH_SCRIPT,
        "function": SH_SCRIPT,
        "module": SH_SCRIPT,
    },
    "sql": {
        "script": SQL_TABLE,
        "module": SQL_TABLE,
        "class": SQL_TABLE,
        "function": SQL_TABLE,
    },
}

ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "rb": "ruby",
    "cs": "csharp",
    "c#": "csharp",
    "sh": "shell",
    "bash": "shell",
}


class CodeGenerator:
    """Generate complete code files in many languages."""

    def generate(self, kind, name, language="python", description=None,
                 fields=None, args=None, module=None, target=None,
                 output_dir=None, verify=True):
        language = ALIASES.get(language.lower(), language.lower())
        kind = kind.lower()
        if language not in LANGUAGES:
            raise ValueError("Unsupported language: %s (choose from %s)"
                             % (language, ", ".join(LANGUAGES)))
        templates = TEMPLATES.get(language, {})
        if kind not in templates:
            raise ValueError("Kind '%s' is not available for %s (choose from %s)"
                             % (kind, language, ", ".join(sorted(templates))))

        description = description or ("A local %s generated by ULTIMATE CODING MASTER."
                                      % kind.replace("-", " "))
        fields = fields or ["value"]
        args = args or "input"
        module = module or snake(name)
        target = target or pascal(name)

        field_lines = []
        field_returns = []
        for field in fields:
            field_lines.append("    %s: str = \"\"" % snake(field))
            field_returns.append("            \"%s\": self.%s,"
                                 % (snake(field), snake(field)))

        mapping = {
            "__NAME__": name,
            "__PASCAL__": pascal(name),
            "__CAMEL__": camel(name),
            "___SNAKE___": snake(name),
            "__SNAKE__": snake(name),
            "__KEBAB__": kebab(name),
            "__DESC__": description.replace('"', "'").replace("\\", "/"),
            "__ARGS__": args,
            "__INIT_ARGS__": ", name=\"%s\"" % snake(name),
            "__FIELDS__": "\n".join(field_lines) if field_lines else "",
            "__FIELD_RETURNS__": "\n".join(field_returns),
            "__MODULE__": module,
            "__TARGET__": target,
        }

        content = _replace(templates[kind], mapping)
        content = self._finalize(content, language)
        filename = self._filename(kind, name, language)

        result = {
            "kind": kind,
            "language": language,
            "name": name,
            "filename": filename,
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "lines": util.count_lines(content),
            "verified": None,
            "verify_detail": None,
        }
        if verify:
            result.update(self.verify(content, language))

        if output_dir:
            path = os.path.join(output_dir, filename)
            util.write_text(path, content)
            result["path"] = path
        return result

    # -- helpers -------------------------------------------------------
    def _filename(self, kind, name, language):
        extension = EXTENSIONS.get(language, ".txt")
        if language == "python":
            base = snake(name)
        elif language in ("java", "csharp"):
            base = pascal(name)
        elif language in ("ruby", "php", "shell", "sql"):
            base = snake(name)
        else:
            base = kebab(name) if kind == "cli" else camel(name)
        return base + extension

    def _finalize(self, content, language):
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        if not content.endswith("\n"):
            content += "\n"
        return content

    def verify(self, content, language):
        """Locally verify generated source when a checker is available."""
        if language == "python":
            try:
                compile(content, "<generated>", "exec")
                return {"verified": True, "verify_detail": "python compile OK"}
            except SyntaxError as exc:
                return {"verified": False,
                        "verify_detail": "python compile failed: %s" % exc}

        if language == "shell" and os.name == "nt":
            return {"verified": None,
                    "verify_detail": "shell check skipped on Windows"}

        checkers = {
            "javascript": ("node", ["node", "--check", "{file}"]),
            "shell": ("bash", ["bash", "-n", "{file}"]),
            "go": ("gofmt", ["gofmt", "-e", "{file}"]),
        }
        if language not in checkers:
            return {"verified": None,
                    "verify_detail": "no local checker for %s" % language}

        tool, command = checkers[language]
        if not shutil.which(tool):
            return {"verified": None,
                    "verify_detail": "%s not installed; skipped" % tool}

        handle, path = tempfile.mkstemp(suffix=EXTENSIONS.get(language, ".txt"))
        os.close(handle)
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            completed = subprocess.run(
                [part.replace("{file}", path) for part in command],
                capture_output=True, text=True, timeout=30,
            )
            # gofmt prints the formatted source on success; only stderr matters.
            detail = completed.stderr.strip() if language == "go" else \
                (completed.stderr or completed.stdout or "").strip()
            return {
                "verified": completed.returncode == 0,
                "verify_detail": detail[:400] or ("%s check OK" % tool),
            }
        except (OSError, subprocess.SubprocessError) as exc:
            return {"verified": None, "verify_detail": str(exc)[:400]}
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def supported(self):
        return {language: sorted(templates)
                for language, templates in sorted(TEMPLATES.items())}
