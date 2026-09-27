"""Run every Heirloom check and publish the measured result.

Usage:
    python3 scripts/verify.py            # run and write evidence/verification.json
    python3 scripts/verify.py --no-write # run only

The exit status is non-zero when any suite fails. The published file records
what was actually run, when, against which commit, and whether the working
tree had uncommitted changes, so a reader can tell exactly what it covers.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence" / "verification.json"
JAVASCRIPT_SOURCES = [
    "dashboard/app.mjs",
    "dashboard/lib.mjs",
    "modern-app/static/app.js",
    "modern-app/static/workflows.mjs",
    "site/assets/landing.mjs",
    "site/assets/screen.mjs",
]


def run_command(arguments):
    started = time.monotonic()
    completed = subprocess.run(
        arguments, cwd=ROOT, capture_output=True, text=True, check=False
    )
    elapsed = round((time.monotonic() - started) * 1000)
    return completed, elapsed


def suite(name, description, command, parse):
    completed, elapsed = run_command(command)
    output = completed.stdout + completed.stderr
    passed, total = parse(output, completed.returncode)
    status = "pass" if completed.returncode == 0 and passed == total else "fail"
    result = {
        "name": name,
        "description": description,
        "command": " ".join(command).replace(sys.executable, "python3"),
        "status": status,
        "passed": passed,
        "total": total,
        "durationMs": elapsed,
    }
    if status == "fail":
        result["output"] = output[-4000:]
    return result


def fraction(pattern):
    def parse(output, _returncode):
        match = re.search(pattern, output)
        if not match:
            return 0, 1
        return int(match.group(1)), int(match.group(2))

    return parse


def parse_unittest(output, returncode):
    match = re.search(r"Ran (\d+) tests?", output)
    total = int(match.group(1)) if match else 0
    failed = 0
    summary = re.search(r"FAILED \(([^)]*)\)", output)
    if summary:
        failed = sum(int(value) for value in re.findall(r"=(\d+)", summary.group(1)))
    if returncode != 0 and failed == 0:
        failed = max(total, 1)
    return total - failed, max(total, 1)


def parse_dashboard(output, returncode):
    return (1, 1) if returncode == 0 and "Dashboard core tests passed" in output else (0, 1)


def git(*arguments):
    completed = subprocess.run(
        ["git", *arguments], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def run_all():
    python = sys.executable
    suites = [
        suite(
            "citations",
            "Every legacy, first-pass and regression-check citation resolves",
            [python, "scripts/check_citations.py"],
            fraction(r"Citation checks: (\d+)/(\d+)"),
        ),
        suite(
            "parity",
            "Catalogue facts equal the modern database and browser form",
            [python, "parity/check.py"],
            fraction(r"checks: (\d+)/(\d+) passed"),
        ),
        suite(
            "application",
            "Database, validation, API and HTTP checks for the modern app",
            [python, "-m", "unittest", "discover", "-s", "modern-app/tests"],
            parse_unittest,
        ),
        suite(
            "workflows",
            "Browser workflow rules: generated identifiers and retrieve-before-edit",
            ["node", "modern-app/tests/test_workflows.mjs"],
            fraction(r"Workflow regression tests passed: (\d+)/(\d+)"),
        ),
        suite(
            "screens",
            "Every catalogue screen composes to an exact 24x80 grid",
            ["node", "dashboard/test.mjs"],
            parse_dashboard,
        ),
    ]

    syntax_failures = []
    started = time.monotonic()
    for source in JAVASCRIPT_SOURCES:
        completed, _ = run_command(["node", "--check", source])
        if completed.returncode != 0:
            syntax_failures.append(f"{source}: {completed.stderr.strip()}")
    syntax = {
        "name": "syntax",
        "description": "Every browser JavaScript module parses",
        "command": "node --check <file>",
        "status": "fail" if syntax_failures else "pass",
        "passed": len(JAVASCRIPT_SOURCES) - len(syntax_failures),
        "total": len(JAVASCRIPT_SOURCES),
        "durationMs": round((time.monotonic() - started) * 1000),
    }
    if syntax_failures:
        syntax["output"] = "\n".join(syntax_failures)
    suites.append(syntax)
    return suites


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-write", action="store_true")
    arguments = parser.parse_args()

    if shutil.which("node") is None:
        print("node is required for the browser and screen checks", file=sys.stderr)
        return 2

    source_commit = git("rev-parse", "HEAD")
    # The record itself is excluded: republishing it must not mark the tree dirty.
    working_tree_clean = git(
        "status", "--porcelain", "--", ".", f":!{OUTPUT.relative_to(ROOT)}"
    ) == ""
    suites = run_all()
    passed = sum(item["passed"] for item in suites)
    total = sum(item["total"] for item in suites)
    ok = all(item["status"] == "pass" for item in suites)

    for item in suites:
        mark = "PASS" if item["status"] == "pass" else "FAIL"
        print(f"{mark}  {item['name']:<12} {item['passed']:>3}/{item['total']:<3} {item['description']}")
        if item["status"] == "fail":
            print(item.get("output", ""))
    print(f"\n{'All checks passed' if ok else 'Checks failed'}: {passed}/{total}")

    if not arguments.no_write:
        report = {
            "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "sourceCommit": source_commit,
            "workingTreeClean": working_tree_clean,
            "legacyCommit": git("-C", "legacy/cics-genapp", "rev-parse", "HEAD"),
            "legacyExecuted": False,
            "status": "pass" if ok else "fail",
            "summary": {"passed": passed, "total": total},
            "suites": suites,
        }
        OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Published {OUTPUT.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
