"""End-to-end tests for the local ULTIMATE CODING MASTER engine.

Run directly::

    python tests/test_coding_master.py -v

or through discovery::

    python -m unittest discover -s tests -p "test_coding_master.py" -v
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from coding_master.analyzer import Analyzer
from coding_master.docs import DocGenerator
from coding_master.generator import CodeGenerator
from coding_master.indexer import CodeIndex
from coding_master.refactor import Refactorer
from coding_master.scaffold import Scaffolder
from coding_master.security import SecurityScanner
from coding_master.tests_gen import TestGenerator


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(textwrap.dedent(content).lstrip("\n"))


SAMPLE = '''"""Sample module used by the engine tests."""

import json
import os
from collections import OrderedDict


def greet(name):
    """Return a greeting for name."""
    cleaned = (name or "").strip()
    if not cleaned:
        return "Hello!"
    return "Hello, %s!" % cleaned


def summary(values):
    """Return a tiny statistical summary."""
    numbers = [float(value) for value in values]
    if not numbers:
        return {"count": 0}
    return {"count": len(numbers), "min": min(numbers),
            "max": max(numbers), "mean": sum(numbers) / len(numbers)}


class Greeter:
    """A small greeting object."""

    def __init__(self, name="world"):
        self.name = name

    def greet(self):
        """Return the greeting for the stored name."""
        return greet(self.name)

    def rename(self, name):
        """Replace the stored name."""
        self.name = name
        return self
'''

RISKY = '''"""Deliberately risky module for scanner tests."""

import os
import subprocess
import sys

AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
PASSWORD = "hunter2hunter2hunter2"


def nested(value):
    if value:
        if value > 1:
            if value > 2:
                if value > 3:
                    if value > 4:
                        return eval(value)
    return None


def run_command(command):
    subprocess.run(command, shell=True)
    os.system(command)


def gather():
    try:
        return 1
    except:
        return 0


def append_item(items=[]):
    items.append(1)
    return items


def classify(value):
    score = 0
''' + "".join("    if value > %d:\n        score += 1\n" % index
              for index in range(16)) + '''    return score


def long_function():
    total = 0
''' + "".join("    total += %d\n" % index for index in range(70)) + '''    return total
'''


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="coding_master_test_")
        write(os.path.join(self.tmp, "sample.py"), SAMPLE)
        write(os.path.join(self.tmp, "risky.py"), RISKY)
        write(os.path.join(self.tmp, "app.js"),
              "export function hello(name) { return `Hi ${name}`; }\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- index ---------------------------------------------------------
    def test_index_finds_symbols_and_imports(self):
        index = CodeIndex(self.tmp).build()
        summary = index.summary()
        self.assertEqual(summary["parse_errors"], 0)
        self.assertGreaterEqual(summary["file_count"], 3)
        names = {symbol["qualname"] for symbol in index.symbols()}
        self.assertIn("greet", names)
        self.assertIn("Greeter", names)
        self.assertIn("Greeter.greet", names)
        self.assertTrue(index.search("greet"))

        json_path = os.path.join(self.tmp, "index.json")
        index.save(json_path)
        loaded = CodeIndex.load(json_path)
        self.assertEqual(loaded.summary()["symbol_count"],
                         summary["symbol_count"])

    # -- analyzer ------------------------------------------------------
    def test_analyzer_detects_smells(self):
        report = Analyzer(self.tmp).analyze()
        rules = {issue["rule"] for issue in report["issues"]}
        for expected in ("bare-except", "mutable-default", "deep-nesting",
                         "long-function", "high-complexity"):
            self.assertIn(expected, rules)
        self.assertGreaterEqual(report["summary"]["files"], 3)
        self.assertLessEqual(report["score"]["value"], 100)
        self.assertIn(report["score"]["grade"], "ABCDF")

    # -- security ------------------------------------------------------
    def test_security_detects_secrets_and_unsafe_calls(self):
        report = SecurityScanner(self.tmp).scan()
        rules = {finding["rule"] for finding in report["findings"]}
        for expected in ("aws-access-key", "hardcoded-credential",
                         "eval-call", "shell-true", "os-system"):
            self.assertIn(expected, rules)
        self.assertFalse(report["passed"])
        self.assertGreater(report["summary"]["by_severity"]["critical"], 0)

    def test_security_ignores_placeholders(self):
        target = os.path.join(self.tmp, "safe.py")
        write(target, '''
            API_KEY = "your-api-key-here"
            password = "changeme"
            token = os.environ.get("TOKEN")
        ''')
        report = SecurityScanner(self.tmp).scan()
        files = {finding["file"] for finding in report["findings"]}
        self.assertNotIn("safe.py", files)

    # -- generator -----------------------------------------------------
    def test_generate_python_and_javascript(self):
        generator = CodeGenerator()
        python = generator.generate("cli", "demo tool", language="python")
        self.assertTrue(python["verified"], python["verify_detail"])
        self.assertIn("def main", python["content"])

        javascript = generator.generate("http-server", "demo api",
                                        language="javascript")
        self.assertIn("http.createServer", javascript["content"])
        if shutil.which("node"):
            self.assertTrue(javascript["verified"],
                            javascript["verify_detail"])

        dataclass = generator.generate("dataclass", "person",
                                       fields=["email", "age"])
        self.assertIn("@dataclass", dataclass["content"])
        self.assertIn("email: str", dataclass["content"])

        with self.assertRaises(ValueError):
            generator.generate("nope", "x")
        with self.assertRaises(ValueError):
            generator.generate("http-server", "x", language="go")

    def test_generator_matrix_compiles(self):
        from coding_master.generator import TEMPLATES
        generator = CodeGenerator()
        python_kinds = sorted(TEMPLATES["python"])
        for kind in python_kinds:
            result = generator.generate(kind, "matrix " + kind,
                                        language="python")
            self.assertTrue(result["verified"],
                            "python %s: %s" % (kind, result["verify_detail"]))

        if shutil.which("node"):
            for kind in sorted(TEMPLATES["javascript"]):
                result = generator.generate(kind, "matrix " + kind,
                                            language="javascript")
                self.assertTrue(result["verified"],
                                "javascript %s: %s"
                                % (kind, result["verify_detail"]))

        if shutil.which("gofmt"):
            for kind in sorted(TEMPLATES["go"]):
                result = generator.generate(kind, "matrix " + kind,
                                            language="go")
                self.assertTrue(result["verified"],
                                "go %s: %s" % (kind, result["verify_detail"]))

    # -- tests generation ---------------------------------------------
    def test_generated_tests_run_and_pass(self):
        generator = TestGenerator(self.tmp)
        result = generator.generate(os.path.join(self.tmp, "sample.py"))
        self.assertGreater(result["tests"], 0)
        test_dir = os.path.join(self.tmp, "tests")
        os.makedirs(test_dir, exist_ok=True)
        path = os.path.join(test_dir, "test_sample.py")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(result["content"])

        completed = subprocess.run([sys.executable, path], capture_output=True,
                                   text=True, timeout=90)
        self.assertEqual(completed.returncode, 0,
                         completed.stdout + completed.stderr)
        self.assertIn("OK", completed.stderr + completed.stdout)

    # -- docs ----------------------------------------------------------
    def test_docs_contain_api(self):
        docs = DocGenerator(self.tmp)
        api = docs.document_file(os.path.join(self.tmp, "sample.py"))
        self.assertIn("## Classes", api)
        self.assertIn("### `greet", api)
        self.assertIn("Return a greeting", api)
        readme = docs.readme("demo")
        self.assertIn("# demo", readme)
        self.assertIn("python (2 files)", readme)

    # -- refactor ------------------------------------------------------
    def test_remove_unused_imports_and_organize(self):
        source = textwrap.dedent('''\
            """Doc."""

            import sys
            import os
            from collections import OrderedDict
            import json

            print(os.getcwd())
        ''')
        refactor = Refactorer(self.tmp)
        removed = refactor.remove_unused_imports(source)
        self.assertEqual(removed["content"].count("import"), 1)
        self.assertIn("import os", removed["content"])
        self.assertIn("sys", removed["removed"])
        self.assertIn("OrderedDict", removed["removed"])

        organized = refactor.organize_imports(removed["content"])
        self.assertIn("import os", organized["content"])
        self.assertNotIn("json", organized["content"])

    def test_partial_import_removal(self):
        source = "from os import path, getcwd\n\nprint(path.join('a', 'b'))\n"
        result = Refactorer(self.tmp).remove_unused_imports(source)
        self.assertIn("from os import path", result["content"])
        self.assertNotIn("getcwd", result["content"])

    def test_rename_only_touches_code_tokens(self):
        source = 'x = 1\nprint("x")\n# x\nprint(x)\n'
        result = Refactorer(self.tmp).rename(source, "x", "value")
        self.assertIn('print("x")', result["content"])
        self.assertIn("# x", result["content"])
        self.assertIn("value = 1", result["content"])
        self.assertIn("print(value)", result["content"])
        self.assertEqual(result["replacements"], 2)

    def test_format_source(self):
        source = "x = 1   \n\n\n\n\ny = 2\n\n"
        result = Refactorer(self.tmp).format_source(source)
        self.assertEqual(result["content"], "x = 1\n\n\ny = 2\n")

    # -- scaffold ------------------------------------------------------
    def test_scaffold_python_cli_runs(self):
        target = os.path.join(self.tmp, "cli_project")
        result = Scaffolder().create("python-cli", target, name="demo-cli")
        self.assertGreater(result["file_count"], 5)
        self.assertFalse([item for item in result["verification"]
                          if item["status"] == "failed"])

        completed = subprocess.run(
            [sys.executable, "run.py", "--help"], cwd=target,
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0,
                         completed.stdout + completed.stderr)

        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=target, capture_output=True, text=True, timeout=90)
        self.assertEqual(completed.returncode, 0,
                         completed.stdout + completed.stderr)

    def test_scaffold_python_lib_api_and_web(self):
        for project_type in ("python-lib", "python-api", "web-static",
                             "data-analysis"):
            target = os.path.join(self.tmp, project_type)
            result = Scaffolder().create(project_type, target)
            self.assertGreater(result["file_count"], 2)
            self.assertFalse([item for item in result["verification"]
                              if item["status"] == "failed"],
                             "%s failed verification" % project_type)

        api_dir = os.path.join(self.tmp, "python-api")
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=api_dir, capture_output=True, text=True, timeout=90)
        self.assertEqual(completed.returncode, 0,
                         completed.stdout + completed.stderr)

        data_dir = os.path.join(self.tmp, "data-analysis")
        completed = subprocess.run(
            [sys.executable, "analysis.py", "data/sample.csv"], cwd=data_dir,
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0,
                         completed.stdout + completed.stderr)
        self.assertIn('"count": 3', completed.stdout)

    def test_scaffold_refuses_non_empty_target(self):
        target = os.path.join(self.tmp, "occupied")
        os.makedirs(target)
        write(os.path.join(target, "keep.txt"), "keep me\n")
        with self.assertRaises(FileExistsError):
            Scaffolder().create("python-cli", target)
        result = Scaffolder().create("python-cli", target, force=True)
        self.assertGreater(result["file_count"], 0)
        self.assertTrue(os.path.isfile(os.path.join(target, "keep.txt")))

    # -- cli -----------------------------------------------------------
    def test_cli_index_and_security_exit_codes(self):
        index_path = os.path.join(self.tmp, "cli_index.json")
        completed = subprocess.run(
            [sys.executable, "-m", "coding_master", "index", self.tmp,
             "--output", index_path],
            cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(completed.returncode, 0,
                         completed.stdout + completed.stderr)
        self.assertTrue(os.path.isfile(index_path))
        with open(index_path, encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertGreater(data["summary"]["symbol_count"], 0)

        completed = subprocess.run(
            [sys.executable, "-m", "coding_master", "security", self.tmp,
             "--fail-on", "high"],
            cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(completed.returncode, 1,
                         completed.stdout + completed.stderr)

        completed = subprocess.run(
            [sys.executable, "-m", "coding_master", "doctor"],
            cwd=ROOT, capture_output=True, text=True, timeout=90)
        self.assertEqual(completed.returncode, 0,
                         completed.stdout + completed.stderr)
        self.assertIn('"stdlib_only": true', completed.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
