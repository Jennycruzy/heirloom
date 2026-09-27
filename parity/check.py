"""Deterministic catalogue-to-modern checks for verified SSC1 and SSP1 facts."""

import json
import sys
from collections import OrderedDict
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "modern-app"))

import database


class ModernHtmlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = {}
        self.select_stack = []
        self.options = {}

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "input" and attrs.get("type") == "radio" and attrs.get("name"):
            # A radio group is a task selector: its options are its values in order.
            self.options.setdefault(attrs["name"], []).append(attrs.get("value"))
        elif tag == "input" and "id" in attrs:
            self.inputs[attrs["id"]] = attrs
        elif tag == "select":
            self.select_stack.append(attrs.get("id"))
        elif tag == "option" and self.select_stack and self.select_stack[-1]:
            self.options.setdefault(self.select_stack[-1], []).append(
                attrs.get("value")
            )

    def handle_endtag(self, tag):
        if tag == "select" and self.select_stack:
            self.select_stack.pop()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def result(check_id, description, passed, expected, actual):
    return {
        "id": check_id,
        "description": description,
        "status": "pass" if passed else "fail",
        "expected": expected,
        "actual": actual,
    }


def main():
    catalogue = load_json(ROOT / "catalogue" / "genapp.json")
    mapping = load_json(ROOT / "parity" / "mapping.json")
    parser = ModernHtmlParser()
    parser.feed(
        (ROOT / "modern-app" / "static" / "index.html").read_text(
            encoding="utf-8"
        )
    )

    screens = {screen["transactionId"]: screen for screen in catalogue["screens"]}
    tasks = catalogue["tasks"]
    checks = []

    for transaction_id, specification in mapping.items():
        screen = screens.get(transaction_id)
        checks.append(
            result(
                f"{transaction_id}-map",
                "Catalogue map identity matches the verified mapping",
                bool(screen) and screen["mapName"] == specification["mapName"],
                specification["mapName"],
                screen["mapName"] if screen else None,
            )
        )

        catalogue_operations = [
            task["operation"]
            for task in tasks
            if task["transactionId"] == transaction_id
            and task["legacySupportStatus"] == "map-and-program-confirmed"
        ]
        expected_operations = specification["operations"]
        checks.append(
            result(
                f"{transaction_id}-operations-catalogue",
                "Modern operation scope equals confirmed catalogue tasks",
                catalogue_operations == expected_operations,
                expected_operations,
                catalogue_operations,
            )
        )

        select_id = f"{specification['entity']}-operation"
        html_operations = parser.options.get(select_id, [])
        checks.append(
            result(
                f"{transaction_id}-operations-html",
                "HTML task selector exposes exactly the confirmed operations, in order",
                html_operations == expected_operations,
                expected_operations,
                html_operations,
            )
        )

        catalogue_inputs = {
            element["bmsName"]: element
            for element in screen["elements"]
            if element.get("role") == "input" and not element.get("protected")
        }
        modern_fields = (
            database.CUSTOMER_FIELDS
            if transaction_id == "SSC1"
            else database.MOTOR_POLICY_FIELDS
        )
        expected_fields = OrderedDict(
            (
                modern_name,
                catalogue_inputs[bms_name]["length"],
            )
            for bms_name, modern_name in specification["fields"].items()
        )

        checks.append(
            result(
                f"{transaction_id}-field-set",
                "Mapped catalogue inputs equal the modern database field set",
                expected_fields == modern_fields,
                dict(expected_fields),
                dict(modern_fields),
            )
        )

        numeric_fields = [
            specification["fields"][name]
            for name, element in catalogue_inputs.items()
            if name in specification["fields"] and element.get("numeric")
        ]
        checks.append(
            result(
                f"{transaction_id}-numeric",
                "No numeric-only rule is invented for non-numeric catalogue inputs",
                numeric_fields == [],
                [],
                numeric_fields,
            )
        )

        html_fields = {}
        wrong_types = []
        for field, maximum in expected_fields.items():
            input_id = f"{specification['entity']}-{field}"
            attrs = parser.inputs.get(input_id)
            if attrs:
                html_fields[field] = int(attrs.get("maxlength", "-1"))
                if attrs.get("type") != "text" or attrs.get("name") != field:
                    wrong_types.append(field)
            else:
                html_fields[field] = None

        checks.append(
            result(
                f"{transaction_id}-html-fields",
                "HTML contains every exact field name and catalogue maximum length",
                html_fields == dict(expected_fields),
                dict(expected_fields),
                html_fields,
            )
        )
        checks.append(
            result(
                f"{transaction_id}-html-types",
                "Catalogue data inputs remain unrestricted text controls",
                wrong_types == [],
                [],
                wrong_types,
            )
        )

    passed = sum(check["status"] == "pass" for check in checks)
    report = {
        "generatedOn": date.today().isoformat(),
        "scope": ["SSC1", "SSP1"],
        "method": "deterministic",
        "catalogueChanged": False,
        "legacyExecuted": False,
        "summary": {
            "total": len(checks),
            "passed": passed,
            "failed": len(checks) - passed,
        },
        "checks": checks,
    }
    output = ROOT / "parity" / "result.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"Deterministic parity checks: {passed}/{len(checks)} passed; "
        f"report: {output.relative_to(ROOT)}"
    )
    if passed != len(checks):
        for check in checks:
            if check["status"] == "fail":
                print(f"FAIL {check['id']}: {check['description']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
