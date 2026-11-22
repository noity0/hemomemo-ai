"""Security scanner: secrets, unsafe calls and injection patterns.

Pure pattern matching over local files. Findings include severity, the exact
line and a remediation hint. Nothing is sent anywhere.
"""

import math
import os
import re
from datetime import datetime

from . import util

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# (rule id, severity, compiled pattern, message, remediation)
LINE_RULES = [
    (
        "private-key", "critical",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
        "Private key material committed to the tree",
        "Remove the key, rotate it, and load it from a local secret store.",
    ),
    (
        "aws-access-key", "critical",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "AWS access key id detected",
        "Revoke the key in IAM and use environment variables.",
    ),
    (
        "google-api-key", "critical",
        re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
        "Google API key detected",
        "Revoke and restrict the key, then load it from the environment.",
    ),
    (
        "github-token", "critical",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
        "GitHub token detected",
        "Revoke the token and store it outside the repository.",
    ),
    (
        "slack-token", "critical",
        re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
        "Slack token detected",
        "Revoke the token in the Slack admin console.",
    ),
    (
        "jwt-token", "high",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        "Hard-coded JWT detected",
        "Move tokens to runtime configuration; never commit them.",
    ),
    (
        "eval-call", "high",
        re.compile(r"(?<![\w.\-])eval\s*\("),
        "eval() executes arbitrary code",  # nosec - rule text

        "Replace eval with an explicit parser or lookup table.",
    ),
    (
        "exec-call", "high",
        re.compile(r"(?<![\w.\-])exec\s*\("),
        "exec() executes arbitrary code",  # nosec - rule text

        "Avoid exec; call named functions instead.",
    ),
    (
        "pickle-load", "high",
        re.compile(r"\bpickle\.loads?\s*\("),
        "Pickle deserialisation can execute arbitrary code",
        "Use JSON or another data-only format for untrusted input.",
    ),
    (
        "unsafe-yaml", "high",
        re.compile(r"\byaml\.load\s*\((?![^)]*SafeLoader)"),
        "yaml.load without SafeLoader can build arbitrary objects",
        "Use yaml.safe_load() or pass Loader=yaml.SafeLoader.",
    ),
    (
        "os-system", "high",
        re.compile(r"\bos\.(?:system|popen)\s*\("),
        "Shell execution through os.system/os.popen",
        "Use subprocess.run with a list of arguments and shell=False.",
    ),
    (
        "shell-true", "high",
        re.compile(r"\bshell\s*=\s*True\b"),
        "subprocess called with shell=True",  # nosec - rule text

        "Pass an argument list and keep shell=False.",
    ),
    (
        "sql-injection", "high",
        re.compile(r"\.execute\s*\(\s*(?:f[\"']|[A-Za-z_]\w*\s*%|[\"'][^\"']*[\"']\s*%|[\"'][^\"']*[\"']\s*\+)"),
        "SQL built by string interpolation",
        "Use parameterised queries: execute(sql, params).",
    ),
    (
        "weak-hash", "medium",
        re.compile(r"\bhashlib\.(?:md5|sha1)\s*\("),
        "Weak hash algorithm (md5/sha1)",
        "Use sha256 or better, with a salt for passwords.",
    ),
    (
        "insecure-random", "medium",
        re.compile(r"\brandom\.(?:random|randint|choice)\s*\("),
        "Non-cryptographic randomness",
        "Use secrets.token_hex()/secrets.choice() for security values.",
    ),
    (
        "tls-verify-off", "high",
        re.compile(r"\bverify\s*=\s*False\b"),
        "TLS certificate verification disabled",
        "Remove verify=False; fix the trust chain instead.",  # nosec - rule text

    ),
    (
        "flask-debug", "medium",
        re.compile(r"\bdebug\s*=\s*True\b"),
        "Debug mode enabled (interactive debugger exposure)",
        "Disable debug in production; use environment flags.",
    ),
    (
        "bind-all", "low",
        re.compile(r"[\"']0\.0\.0\.0[\"']"),
        "Service binds to every interface",
        "Bind to 127.0.0.1 unless remote access is intended.",
    ),
    (
        "chmod-777", "medium",
        re.compile(r"\bchmod\s*\(?\s*(?:0o?777|777)\b"),
        "World-writable permissions",
        "Grant the minimum permissions required.",
    ),
    (
        "mktemp", "low",
        re.compile(r"\btempfile\.mktemp\s*\("),
        "Race-prone temporary file creation",
        "Use tempfile.mkstemp() or NamedTemporaryFile().",
    ),
]

GENERIC_SECRET = re.compile(
    r"(?i)\b(api[_-]?key|apikey|secret|password|passwd|token|access[_-]?key)\b"
    r"\s*[:=]\s*([\"'])([^\"']{8,})\2"
)

PLACEHOLDER_MARKERS = (
    "your", "example", "sample", "placeholder", "changeme", "change-me",
    "dummy", "xxxx", "****", "<", ">", "${", "{{", "}}", "os.environ",
    "os.getenv", "getenv(", "process.env", "env[", "none", "null", "todo",
    "insert", "replace", "redacted", "fake", "test-key", "test_key",
)

TEXT_LIMIT = 2 * 1024 * 1024


def _looks_like_placeholder(value):
    lowered = value.strip().lower()
    if len(lowered) < 8:
        return True
    if lowered == "*" * len(lowered):
        return True
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def _entropy(value):
    if not value:
        return 0.0
    counts = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    total = len(value)
    score = 0.0
    for count in counts.values():
        probability = count / total
        score -= probability * math.log2(probability)
    return score


class SecurityScanner:
    """Scan local files for secrets and dangerous constructs."""

    def __init__(self, root):
        self.root = os.path.abspath(root)

    def scan_file(self, path, findings):
        relpath = util.relpath(self.root, path) if os.path.isabs(path) else path
        try:
            if os.path.getsize(path) > TEXT_LIMIT:
                return
            text = util.read_text(path)
        except OSError:
            return

        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or "nosec" in line.lower():
                continue
            for rule, severity, pattern, message, remediation in LINE_RULES:
                if not pattern.search(line):
                    continue
                findings.append({
                    "rule": rule,
                    "severity": severity,
                    "file": relpath,
                    "line": number,
                    "message": message,
                    "remediation": remediation,
                    "excerpt": stripped[:160],
                })

            match = GENERIC_SECRET.search(line)
            if match:
                value = match.group(3)
                if not _looks_like_placeholder(value) and _entropy(value) >= 2.5:
                    findings.append({
                        "rule": "hardcoded-credential",
                        "severity": "high",
                        "file": relpath,
                        "line": number,
                        "message": "Possible hard-coded %s"
                                   % match.group(1).replace("_", " "),
                        "remediation": "Load the value from the environment "
                                       "or a local secret store.",
                        "excerpt": stripped[:160],
                    })

    def scan(self, include_data=False, max_files=None):
        findings = []
        scanned = 0
        for path in util.iter_files(self.root, include_data=include_data,
                                    max_files=max_files):
            scanned += 1
            self.scan_file(path, findings)

        findings.sort(key=lambda item: (SEVERITY_ORDER.get(item["severity"], 9),
                                        item["file"], item["line"]))
        counts = {key: 0 for key in SEVERITY_ORDER}
        for finding in findings:
            counts[finding["severity"]] += 1

        weights = {"critical": 25, "high": 12, "medium": 5, "low": 1}
        penalty = sum(weights.get(item["severity"], 0) for item in findings)
        score = util.clamp(100 - penalty, 0, 100)

        return {
            "root": self.root,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary": {
                "files_scanned": scanned,
                "findings": len(findings),
                "by_severity": counts,
                "rules": sorted({item["rule"] for item in findings}),
            },
            "score": score,
            "passed": counts["critical"] == 0 and counts["high"] == 0,
            "findings": findings,
        }

    def scan_to_file(self, path):
        report = self.scan()
        util.write_json(path, report)
        return report
