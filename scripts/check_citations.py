"""Check that every published citation points at real, existing source lines.

Three kinds of citation are checked without model judgement:

- legacy citations in ``evidence/findings.json`` and every ``sourceEvidence``
  entry in ``catalogue/genapp.json`` must fall inside the pinned GenApp file;
- first-pass citations must fall inside the file as it was at the preserved
  ``stage3-first-pass`` tag;
- every named regression check must exist in the test file it names.
"""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = ROOT / "legacy" / "cics-genapp"
CATALOGUE_PREFIX = "legacy/cics-genapp/"


def line_count(text):
    return len(text.splitlines())


def check_range(label, reference, lines, problems):
    start, end = reference["lineStart"], reference["lineEnd"]
    if not (isinstance(start, int) and isinstance(end, int)):
        problems.append(f"{label}: line numbers must be integers")
    elif not 1 <= start <= end <= lines:
        problems.append(
            f"{label}: lines {start}-{end} fall outside a {lines}-line file"
        )


def legacy_text(relative_path):
    path = (LEGACY_ROOT / relative_path).resolve()
    if not path.is_relative_to(LEGACY_ROOT.resolve()) or not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def first_pass_text(ref, relative_path):
    completed = subprocess.run(
        ["git", "show", f"{ref}:{relative_path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout if completed.returncode == 0 else None


def regression_check_exists(check):
    path = ROOT / check["file"]
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        return f"def {check['name']}(" in text
    return f'check("{check["name"]}"' in text


def run():
    problems = []
    counted = 0

    if not (LEGACY_ROOT / "base").is_dir():
        return {
            "passed": 0,
            "total": 0,
            "problems": [
                "legacy/cics-genapp is empty; run: git submodule update --init"
            ],
        }

    findings = json.loads((ROOT / "evidence" / "findings.json").read_text())
    first_pass_ref = findings["source"]["firstPassRef"]
    file_cache = {}

    def cached(kind, key, loader):
        cache_key = (kind, key)
        if cache_key not in file_cache:
            file_cache[cache_key] = loader()
        return file_cache[cache_key]

    references = []
    for finding in findings["findings"]:
        for reference in finding["legacyEvidence"]:
            references.append(("legacy", finding["id"], reference))
        for reference in finding["firstPassEvidence"]:
            references.append(("first-pass", finding["id"], reference))
        for check in finding["regressionChecks"]:
            counted += 1
            if not regression_check_exists(check):
                problems.append(
                    f"{finding['id']}: regression check {check['name']!r} "
                    f"not found in {check['file']}"
                )
    for item in findings["uncertain"]:
        for reference in item.get("legacyEvidence", []):
            references.append(("legacy", item["title"], reference))

    catalogue = json.loads((ROOT / "catalogue" / "genapp.json").read_text())
    for task in catalogue["tasks"]:
        for reference in task["sourceEvidence"]:
            file_path = reference["file"]
            if not file_path.startswith(CATALOGUE_PREFIX):
                problems.append(f"{task['taskId']}: {file_path} is not legacy source")
                continue
            references.append(
                (
                    "legacy",
                    task["taskId"],
                    {**reference, "file": file_path.removeprefix(CATALOGUE_PREFIX)},
                )
            )

    for kind, owner, reference in references:
        counted += 1
        file_path = reference["file"]
        label = f"{owner} {kind} {file_path}"
        if kind == "legacy":
            text = cached(kind, file_path, lambda: legacy_text(file_path))
        else:
            text = cached(
                kind, file_path, lambda: first_pass_text(first_pass_ref, file_path)
            )
        if text is None:
            problems.append(f"{label}: file not found")
            continue
        check_range(label, reference, line_count(text), problems)

    return {"passed": counted - len(problems), "total": counted, "problems": problems}


def main():
    result = run()
    for problem in result["problems"]:
        print(f"FAIL {problem}")
    print(f"Citation checks: {result['passed']}/{result['total']} passed.")
    if result["problems"]:
        raise SystemExit(1)


if __name__ == "__main__":
    sys.exit(main())
