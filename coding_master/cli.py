"""Command line interface: ``python -m coding_master <command>``."""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime

from . import __version__, util
from .analyzer import Analyzer
from .docs import DocGenerator
from .generator import CodeGenerator, KINDS, LANGUAGES
from .indexer import CodeIndex
from .refactor import Refactorer
from .scaffold import PROJECT_TYPES, Scaffolder
from .security import SecurityScanner
from .tests_gen import TestGenerator


def _emit(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _resolve(path):
    return os.path.abspath(path or ".")


# ------------------------------------------------------------------ commands


def command_index(args):
    root = _resolve(args.path)
    index = CodeIndex(root).build(include_data=args.include_data,
                                  max_files=args.max_files)
    summary = index.summary()
    if args.search:
        summary["matches"] = index.search(args.search)
    if args.output:
        index.save(args.output)
        summary["output"] = os.path.abspath(args.output)
    _emit(summary)
    return 0


def command_analyze(args):
    root = _resolve(args.path)
    report = Analyzer(root).analyze(include_data=args.include_data,
                                    max_files=args.max_files)
    if args.output:
        util.write_json(args.output, report)
        report["output"] = os.path.abspath(args.output)
    trimmed = {
        "root": report["root"],
        "score": report["score"],
        "summary": report["summary"],
        "recommendations": report["recommendations"],
        "top_issues": report["issues"][: args.top],
        "duplicates": len(report["duplicates"]),
    }
    if args.output:
        trimmed["output"] = report["output"]
    _emit(trimmed)
    return 0


def command_security(args):
    root = _resolve(args.path)
    report = SecurityScanner(root).scan(include_data=args.include_data,
                                        max_files=args.max_files)
    if args.output:
        util.write_json(args.output, report)
        report["output"] = os.path.abspath(args.output)
    trimmed = {
        "root": report["root"],
        "score": report["score"],
        "passed": report["passed"],
        "summary": report["summary"],
        "findings": report["findings"][: args.top],
    }
    if args.output:
        trimmed["output"] = report["output"]
    _emit(trimmed)

    thresholds = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    blocking = thresholds[args.fail_on]
    worst = min((thresholds[item["severity"]] for item in report["findings"]),
                default=99)
    return 1 if worst <= blocking else 0


def command_generate(args):
    generator = CodeGenerator()
    fields = [item.strip() for item in (args.fields or "").split(",")
              if item.strip()]
    result = generator.generate(
        args.kind, args.name, language=args.language,
        description=args.description, fields=fields, args=args.arguments,
        module=args.module, target=args.target, output_dir=args.out,
        verify=not args.no_verify,
    )
    content = result.pop("content")
    if not args.out:
        result["content"] = content
    _emit(result)
    return 0 if result.get("verified") is not False else 1


def command_tests(args):
    root = os.getcwd()
    target = _resolve(args.path)
    if not os.path.isfile(target):
        print("error: not a file: %s" % target)
        return 2
    generator = TestGenerator(root)
    output = args.output
    if not output:
        stem = os.path.splitext(os.path.basename(target))[0]
        output = os.path.join(root, "tests", "test_%s.py" % stem)
    result = generator.write(target, output, framework=args.framework,
                             module=args.module)
    result.pop("content", None)
    _emit(result)
    return 0


def command_docs(args):
    root = _resolve(args.path)
    generator = DocGenerator(root)
    result = {}
    if args.output:
        generator.write_api(args.output)
        result["api"] = os.path.abspath(args.output)
    if args.readme:
        generator.write_readme(args.readme, args.name)
        result["readme"] = os.path.abspath(args.readme)
    if not args.output and not args.readme:
        print(generator.document_tree(max_files=args.max_files))
        return 0
    _emit(result)
    return 0


def command_refactor(args):
    target = _resolve(args.path)
    if not os.path.isfile(target):
        print("error: not a file: %s" % target)
        return 2
    operations = []
    if args.organize_imports:
        operations.append({"op": "organize_imports"})
    if args.remove_unused:
        operations.append({"op": "remove_unused_imports"})
    if args.format:
        operations.append({"op": "format"})
    if args.rename:
        if ":" not in args.rename:
            print("error: --rename expects OLD:NEW")
            return 2
        old, new = args.rename.split(":", 1)
        operations.append({"op": "rename", "old": old, "new": new})
    if not operations:
        operations.append({"op": "format"})
    result = Refactorer(os.getcwd()).apply(target, operations,
                                           write=args.write)
    content = result.pop("content")
    if not args.write:
        result["preview"] = content[:4000]
    _emit(result)
    return 0


def command_scaffold(args):
    scaffolder = Scaffolder()
    try:
        result = scaffolder.create(args.project_type, args.target,
                                   name=args.name, force=args.force)
    except (ValueError, FileExistsError, OSError) as exc:
        print("error: %s" % exc)
        return 2
    _emit(result)
    failed = [item for item in result["verification"]
              if item["status"] == "failed"]
    return 1 if failed else 0


def command_audit(args):
    root = _resolve(args.path)
    output = os.path.abspath(args.output or os.path.join(root, "audit"))
    os.makedirs(output, exist_ok=True)

    index = CodeIndex(root).build(include_data=args.include_data,
                                  max_files=args.max_files)
    index.save(os.path.join(output, "index.json"))

    analyzer = Analyzer(root)
    analysis = analyzer.analyze(include_data=args.include_data,
                                max_files=args.max_files)
    util.write_json(os.path.join(output, "analysis.json"), analysis)

    scanner = SecurityScanner(root)
    security = scanner.scan(include_data=args.include_data,
                            max_files=args.max_files)
    util.write_json(os.path.join(output, "security.json"), security)

    docs = DocGenerator(root)
    util.write_text(os.path.join(output, "API.md"),
                    docs.document_tree(max_files=args.max_files))

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": root,
        "index": index.summary(),
        "analysis": {
            "score": analysis["score"],
            "summary": analysis["summary"],
            "recommendations": analysis["recommendations"],
            "top_issues": analysis["issues"][: args.top],
        },
        "security": {
            "score": security["score"],
            "passed": security["passed"],
            "summary": security["summary"],
            "findings": security["findings"][: args.top],
        },
        "artifacts": sorted(os.path.basename(path) for path in [
            os.path.join(output, "index.json"),
            os.path.join(output, "analysis.json"),
            os.path.join(output, "security.json"),
            os.path.join(output, "API.md"),
        ]),
        "qanoon": {
            "local_only": True,
            "no_external_ai": True,
            "no_cloud_dependencies": True,
            "no_ffmpeg": True,
        },
    }
    report_path = os.path.join(output, "audit_report.json")
    util.write_json(report_path, report)
    report["report"] = report_path
    report["security"]["findings"] = len(report["security"]["findings"])
    report["analysis"]["top_issues"] = len(report["analysis"]["top_issues"])
    _emit(report)
    return 0 if security["passed"] else 1


def command_doctor(args):
    root = _resolve(args.path)
    tools = ["python", "node", "npm", "git", "bash", "go", "gofmt", "rustc",
             "cargo", "java", "php", "ruby"]
    available = {}
    for tool in tools:
        resolved = shutil.which(tool)
        available[tool] = resolved or None

    python_ok = sys.version_info >= (3, 9)
    packages = {}
    for module in ("coding_master.indexer", "coding_master.analyzer",
                   "coding_master.security", "coding_master.generator",
                   "coding_master.tests_gen", "coding_master.docs",
                   "coding_master.refactor", "coding_master.scaffold"):
        try:
            __import__(module)
            packages[module] = "ok"
        except Exception as exc:  # pragma: no cover - defensive
            packages[module] = "error: %s" % exc

    report = {
        "root": root,
        "engine_version": __version__,
        "python": {
            "version": sys.version.split()[0],
            "supported": python_ok,
        },
        "tools": available,
        "modules": packages,
        "capabilities": {
            "languages": LANGUAGES,
            "kinds": KINDS,
            "project_types": PROJECT_TYPES,
        },
        "qanoon": {
            "local_only": True,
            "stdlib_only": all(value == "ok" for value in packages.values()),
        },
    }
    _emit(report)
    return 0 if python_ok else 1


def command_version(args):
    _emit({"engine": "ULTIMATE CODING MASTER", "version": __version__,
           "languages": LANGUAGES, "kinds": KINDS})
    return 0


# -------------------------------------------------------------------- parser


def build_parser():
    parser = argparse.ArgumentParser(
        prog="coding_master",
        description="Local, dependency-free code intelligence and generation.",
    )
    subparsers = parser.add_subparsers(dest="command")

    def add_path(sub, default="."):
        sub.add_argument("path", nargs="?", default=default,
                         help="file or directory (default: current directory)")

    def add_common(sub):
        sub.add_argument("--include-data", action="store_true",
                         help="include the data/ tree")
        sub.add_argument("--max-files", type=int, default=None,
                         help="stop after N files")
        sub.add_argument("--output", "-o", default=None,
                         help="write the full JSON report here")
        sub.add_argument("--top", type=int, default=20,
                         help="show the first N findings")

    index = subparsers.add_parser("index", help="build a symbol index")
    add_path(index)
    add_common(index)
    index.add_argument("--search", default=None, help="search symbol names")
    index.set_defaults(func=command_index)

    analyze = subparsers.add_parser("analyze", help="metrics and code smells")
    add_path(analyze)
    add_common(analyze)
    analyze.set_defaults(func=command_analyze)

    security = subparsers.add_parser("security", help="secrets and unsafe calls")
    add_path(security)
    add_common(security)
    security.add_argument("--fail-on", default="critical",
                          choices=["critical", "high", "medium", "low"],
                          help="exit non-zero at this severity or worse")
    security.set_defaults(func=command_security)

    generate = subparsers.add_parser("generate", help="generate a code file")
    generate.add_argument("kind", choices=KINDS)
    generate.add_argument("name")
    generate.add_argument("--language", "-l", default="python",
                          choices=LANGUAGES)
    generate.add_argument("--description", "-d", default=None)
    generate.add_argument("--fields", default=None,
                          help="comma separated field names")
    generate.add_argument("--arguments", default=None,
                          help="function argument list, e.g. 'a, b=2'")
    generate.add_argument("--module", default=None,
                          help="module to import in generated tests")
    generate.add_argument("--target", default=None,
                          help="symbol name used by generated tests")
    generate.add_argument("--out", default=None, help="output directory")
    generate.add_argument("--no-verify", action="store_true")
    generate.set_defaults(func=command_generate)

    tests = subparsers.add_parser("tests", help="generate unit tests")
    tests.add_argument("path")
    tests.add_argument("--output", "-o", default=None)
    tests.add_argument("--framework", default="unittest",
                       choices=["unittest", "pytest"])
    tests.add_argument("--module", default=None)
    tests.set_defaults(func=command_tests)

    docs = subparsers.add_parser("docs", help="generate Markdown docs")
    add_path(docs)
    docs.add_argument("--output", "-o", default=None, help="API.md path")
    docs.add_argument("--readme", default=None, help="README path")
    docs.add_argument("--name", default=None, help="project name for README")
    docs.set_defaults(func=command_docs)

    refactor = subparsers.add_parser("refactor", help="safe source rewrites")
    refactor.add_argument("path")
    refactor.add_argument("--organize-imports", action="store_true")
    refactor.add_argument("--remove-unused", action="store_true")
    refactor.add_argument("--format", action="store_true")
    refactor.add_argument("--rename", default=None, metavar="OLD:NEW")
    refactor.add_argument("--write", action="store_true",
                          help="write changes (default: preview)")
    refactor.set_defaults(func=command_refactor)

    scaffold = subparsers.add_parser("scaffold", help="create a project")
    scaffold.add_argument("project_type", choices=PROJECT_TYPES)
    scaffold.add_argument("target")
    scaffold.add_argument("--name", default=None)
    scaffold.add_argument("--force", action="store_true")
    scaffold.set_defaults(func=command_scaffold)

    audit = subparsers.add_parser("audit", help="index + analysis + security")
    add_path(audit)
    add_common(audit)
    audit.set_defaults(func=command_audit)

    doctor = subparsers.add_parser("doctor", help="environment check")
    add_path(doctor)
    doctor.set_defaults(func=command_doctor)

    version = subparsers.add_parser("version", help="engine version")
    version.set_defaults(func=command_version)

    return parser


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
