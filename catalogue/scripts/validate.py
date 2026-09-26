#!/usr/bin/env python3
"""
Validate catalogue/genapp.json against catalogue/schema.json.
Runs CHK-01 through CHK-20 and writes catalogue/validation-result.json.

Run from workspace root:
  .venv/bin/python catalogue/scripts/validate.py
"""
import json
import os
import sys
import datetime

try:
    import jsonschema
    from jsonschema import validate as jvalidate, Draft7Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install -r catalogue/scripts/requirements.txt")
    sys.exit(1)

WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOGUE_PATH = os.path.join(WORKSPACE, "catalogue", "genapp.json")
SCHEMA_PATH = os.path.join(WORKSPACE, "catalogue", "schema.json")
RESULT_PATH = os.path.join(WORKSPACE, "catalogue", "validation-result.json")

ALLOWED_OPTIONS = {
    "SSC1":  ["1", "2", "4"],
    "SSP1":  ["1", "2", "3", "4"],
    "SSP2":  ["1", "2", "3", "4"],
    "SSP3":  ["1", "2", "3", "4"],
    "SSP4":  ["1", "2", "3"],
    "SSP5":  ["1", "2"],
}


def run():
    checks = []
    overall = "pass"

    def record(chk_id, desc, passed, detail=""):
        nonlocal overall
        status = "pass" if passed else "fail"
        if not passed:
            overall = "fail"
        checks.append({"id": chk_id, "description": desc, "status": status, "detail": detail})
        marker = "✓" if passed else "✗"
        print(f"  {marker} {chk_id}: {desc}" + (f" — {detail}" if detail and not passed else ""))

    print("Running CHK-01 through CHK-20 ...")

    # CHK-01: Parse genapp.json
    cat = None
    try:
        with open(CATALOGUE_PATH, encoding="utf-8") as f:
            cat = json.load(f)
        record("CHK-01", "catalogue/genapp.json parses as valid JSON", True)
    except Exception as ex:
        record("CHK-01", "catalogue/genapp.json parses as valid JSON", False, str(ex))

    # CHK-02: Parse schema.json
    schema = None
    try:
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            schema = json.load(f)
        record("CHK-02", "catalogue/schema.json parses as valid JSON", True)
    except Exception as ex:
        record("CHK-02", "catalogue/schema.json parses as valid JSON", False, str(ex))

    # CHK-03: Schema validation
    if cat and schema:
        try:
            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(cat))
            if errors:
                msgs = "; ".join(f"{e.json_path}: {e.message}" for e in errors[:5])
                record("CHK-03", "genapp.json validates against schema.json (Draft 7)", False, msgs)
            else:
                record("CHK-03", "genapp.json validates against schema.json (Draft 7)", True)
        except Exception as ex:
            record("CHK-03", "genapp.json validates against schema.json (Draft 7)", False, str(ex))
    else:
        record("CHK-03", "genapp.json validates against schema.json (Draft 7)", False, "Skipped — parse failed")

    if cat is None:
        # All remaining checks require a parsed catalogue
        for i in range(4, 21):
            checks.append({"id": f"CHK-{i:02d}", "description": "skipped", "status": "fail", "detail": "Catalogue parse failed"})
        overall = "fail"
    else:
        # Collect all sourceRef objects from the catalogue
        def collect_source_refs(obj):
            refs = []
            if isinstance(obj, dict):
                if "file" in obj and "lineStart" in obj and "lineEnd" in obj and "excerpt" in obj:
                    refs.append(obj)
                for v in obj.values():
                    refs.extend(collect_source_refs(v))
            elif isinstance(obj, list):
                for item in obj:
                    refs.extend(collect_source_refs(item))
            return refs

        all_refs = collect_source_refs(cat)

        # CHK-04: Source files exist
        missing_files = set()
        for ref in all_refs:
            fpath = os.path.join(WORKSPACE, ref["file"])
            if not os.path.isfile(fpath):
                missing_files.add(ref["file"])
        record("CHK-04", "Every cited source file exists", len(missing_files) == 0,
               f"Missing: {sorted(missing_files)}" if missing_files else "")

        # Pre-load source files for line checks
        file_lines = {}
        for ref in all_refs:
            fp = ref["file"]
            if fp not in file_lines:
                full = os.path.join(WORKSPACE, fp)
                if os.path.isfile(full):
                    with open(full, encoding="latin-1") as f:
                        file_lines[fp] = f.readlines()

        # CHK-05: Line ranges valid
        bad_ranges = []
        for ref in all_refs:
            fp = ref["file"]
            ls = ref["lineStart"]
            le = ref["lineEnd"]
            if fp in file_lines:
                n = len(file_lines[fp])
                if ls < 1 or le < ls or le > n:
                    bad_ranges.append(f"{fp}:{ls}-{le} (file has {n} lines)")
        record("CHK-05", "Every cited line range is within the file's line count", len(bad_ranges) == 0,
               f"Bad ranges: {bad_ranges[:5]}" if bad_ranges else "")

        # CHK-06: Excerpt present in cited range
        bad_excerpts = []
        for ref in all_refs:
            fp = ref["file"]
            ls = ref["lineStart"]
            le = ref["lineEnd"]
            excerpt = ref["excerpt"].strip()
            if not excerpt:
                continue
            if fp not in file_lines:
                continue
            block = "".join(file_lines[fp][ls-1:le])
            # Use first 20 chars of excerpt for matching (tolerates truncation)
            needle = excerpt[:20].strip()
            if needle and needle not in block:
                bad_excerpts.append(f"{fp}:{ls}-{le} excerpt '{needle}' not found")
        record("CHK-06", "Every excerpt appears within its cited line range", len(bad_excerpts) == 0,
               f"Mismatches: {bad_excerpts[:5]}" if bad_excerpts else "")

        # CHK-07: Duplicate taskIds
        task_ids = [t["taskId"] for t in cat.get("tasks", [])]
        dupe_tasks = [tid for tid in set(task_ids) if task_ids.count(tid) > 1]
        record("CHK-07", "No duplicate taskIds", len(dupe_tasks) == 0,
               f"Duplicates: {dupe_tasks}" if dupe_tasks else "")

        # CHK-08: Duplicate elementIds within each screen
        dupe_elems = []
        for scr in cat.get("screens", []):
            eids = [e["elementId"] for e in scr.get("elements", [])]
            for eid in set(eids):
                if eids.count(eid) > 1:
                    dupe_elems.append(f"{scr['mapName']}/{eid}")
        record("CHK-08", "No duplicate elementIds within any screen", len(dupe_elems) == 0,
               f"Duplicates: {dupe_elems[:5]}" if dupe_elems else "")

        # CHK-09: Duplicate fieldIds across all screens
        all_fids = []
        for scr in cat.get("screens", []):
            for el in scr.get("elements", []):
                if el.get("fieldId"):
                    all_fids.append(el["fieldId"])
        dupe_fids = [fid for fid in set(all_fids) if all_fids.count(fid) > 1]
        record("CHK-09", "No duplicate fieldIds across all screens", len(dupe_fids) == 0,
               f"Duplicates: {dupe_fids[:5]}" if dupe_fids else "")

        # CHK-10: Exactly 6 screens
        n_screens = len(cat.get("screens", []))
        record("CHK-10", "Exactly 6 screen objects", n_screens == 6,
               f"Found {n_screens}" if n_screens != 6 else "")

        # CHK-11: Exactly 20 task objects
        n_tasks = len(cat.get("tasks", []))
        record("CHK-11", "Exactly 20 task objects", n_tasks == 20,
               f"Found {n_tasks}" if n_tasks != 20 else "")

        # CHK-12: Exactly 18 map-and-program-confirmed tasks
        n_confirmed = sum(1 for t in cat["tasks"] if t.get("legacySupportStatus") == "map-and-program-confirmed")
        record("CHK-12", "Exactly 18 map-and-program-confirmed tasks", n_confirmed == 18,
               f"Found {n_confirmed}" if n_confirmed != 18 else "")

        # CHK-13: Exactly 2 screen-only-cannot-determine tasks
        n_screen_only = sum(1 for t in cat["tasks"] if t.get("legacySupportStatus") == "screen-only-cannot-determine")
        record("CHK-13", "Exactly 2 screen-only-cannot-determine tasks", n_screen_only == 2,
               f"Found {n_screen_only}" if n_screen_only != 2 else "")

        # CHK-14: All tasks have modernParityStatus == "not-assessed"
        bad_parity = [t["taskId"] for t in cat["tasks"] if t.get("modernParityStatus") != "not-assessed"]
        record("CHK-14", "All tasks have modernParityStatus == not-assessed", len(bad_parity) == 0,
               f"Bad: {bad_parity}" if bad_parity else "")

        # CHK-15: All element coordinates within 24x80 grid
        coord_errors = []
        for scr in cat.get("screens", []):
            for el in scr.get("elements", []):
                r, c, ln = el.get("row"), el.get("col"), el.get("length")
                if r and c and ln:
                    if not (1 <= r <= 24):
                        coord_errors.append(f"{el['elementId']} row={r} out of 1-24")
                    if not (1 <= c <= 80):
                        coord_errors.append(f"{el['elementId']} col={c} out of 1-80")
                    if c + ln - 1 > 80:
                        coord_errors.append(f"{el['elementId']} col+length-1={c+ln-1} > 80")
        record("CHK-15", "All element coordinates within 24x80 grid", len(coord_errors) == 0,
               f"Errors: {coord_errors[:5]}" if coord_errors else "")

        # Find SSMAPC1
        ssmapc1 = next((s for s in cat["screens"] if s["mapName"] == "SSMAPC1"), None)
        if ssmapc1 is None:
            for i in range(16, 20):
                checks.append({"id": f"CHK-{i:02d}", "description": "skipped", "status": "fail", "detail": "SSMAPC1 not found"})
            overall = "fail"
        else:
            els = ssmapc1.get("elements", [])

            # CHK-16: SSMAPC1 named field count == 12
            named = [e for e in els if e.get("bmsName") is not None]
            record("CHK-16", "SSMAPC1 has exactly 12 named fields (bmsName not null)", len(named) == 12,
                   f"Found {len(named)}: {[e['bmsName'] for e in named]}" if len(named) != 12 else f"Found: {[e['bmsName'] for e in named]}")

            # CHK-17: SSMAPC1 editable named fields == 11
            editable = [e for e in named if not e.get("protected", True)]
            record("CHK-17", "SSMAPC1 has exactly 11 editable named fields (UNPROT)", len(editable) == 11,
                   f"Found {len(editable)}: {[e['bmsName'] for e in editable]}" if len(editable) != 11 else "")

            # CHK-18: SSMAPC1 data-entry fields (UNPROT, role != option) == 10
            data_entry = [e for e in editable if e.get("role") != "option"]
            record("CHK-18", "SSMAPC1 has exactly 10 clerk data-entry fields (UNPROT, not option)", len(data_entry) == 10,
                   f"Found {len(data_entry)}: {[e['bmsName'] for e in data_entry]}" if len(data_entry) != 10 else "")

            # CHK-19: SSMAPC1 protected named fields == 1
            protected_named = [e for e in named if e.get("protected", False)]
            record("CHK-19", "SSMAPC1 has exactly 1 protected named field (error/display)", len(protected_named) == 1,
                   f"Found {len(protected_named)}: {[e['bmsName'] for e in protected_named]}" if len(protected_named) != 1 else "")

        # CHK-20: Per-transaction allowedOptions exact sets
        bad_options = []
        for task in cat.get("tasks", []):
            trans = task.get("transactionId")
            expected = ALLOWED_OPTIONS.get(trans)
            actual = task.get("allowedOptions", [])
            if expected is not None and sorted(actual) != sorted(expected):
                bad_options.append(f"{task['taskId']}: expected {expected}, got {actual}")
        record("CHK-20", "Per-transaction allowedOptions match exact sets", len(bad_options) == 0,
               f"Mismatches: {bad_options[:5]}" if bad_options else "")

    # Write result
    result = {
        "runTimestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "overallStatus": overall,
        "checks": checks
    }
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\noverallStatus: {overall}")
    print(f"Written: {RESULT_PATH}")
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    sys.exit(run())
