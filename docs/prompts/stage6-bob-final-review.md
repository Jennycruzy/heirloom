# Final review: Stage 6 source-proven repairs

Perform one independent, evidence-based review of the Stage 6 repair branch.
Do not launch subagents. Do not modify application code, tests, the catalogue,
or existing documentation. You may create only this report:
`docs/reports/stage6-bob-final-review.md`.

## Safe starting check

1. Run `git status --short --branch`.
2. The required branch is `fix/source-proven-parity-gaps`.
3. If another branch is active and the working tree is clean, switch to the
   required branch.
4. If the working tree has unrelated changes, stop and report that condition;
   do not discard or overwrite anything.
5. Confirm that tag `stage3-first-pass` exists and points to commit `d666438`.

## Evidence to inspect

- `docs/reports/stage5-evidence-audit.md`
- `docs/reports/stage6-before-fix.md`
- `docs/reports/stage6-after-fix.md`
- `git diff stage3-first-pass..HEAD`
- the legacy source lines cited in the Stage 5 evidence audit
- the three Stage 6 images in `browser_evidence/`

Do not rely only on the reports. Check the cited legacy source and the repaired
implementation directly.

## Review questions

Independently determine whether the implementation now supports each behavior:

1. Customer Add does not accept a clerk-supplied customer number; the
   application assigns it.
2. Customer Update loads the existing record before editing is enabled.
3. Motor-policy Add does not accept a clerk-supplied policy number; the
   application assigns it.
4. Motor inquiry uses customer number and policy number together.
5. Motor Update uses both identifiers and loads the existing record before
   editing is enabled.
6. Motor Delete uses customer number and policy number together.

For generated identifiers, review only the source-proven responsibility for
assigning the number. Do not claim that the modern numbering sequence or exact
format matches the legacy system unless the cited source proves it.

Also verify that:

- customer delete was not added;
- the authoritative catalogue was not changed by this repair branch;
- no unsupported date, numeric, or additional required-field rule was added;
- the first pass remains recoverable at tag `stage3-first-pass`;
- every automated and browser-evidence file named in the after-fix report
  exists.

## Checks to run

Run these commands and record their actual results:

```sh
python3 -m unittest discover -s modern-app/tests -v
node modern-app/tests/test_workflows.mjs
python3 parity/check.py
git diff --check
```

Do not report a check as passed unless you ran it successfully.

## Required report format

Write in plain language suitable for a hackathon judge. Avoid unexplained
internal labels. For each of the six behaviors, write:

- `Confirmed`, `Not confirmed`, or `Cannot determine`
- a short reason
- exact legacy-source and modern-file line references

Then list the four check results, the scope safeguards, and any remaining
uncertainty. Finish with exactly one overall result:

- `READY` — all six repairs are supported and all four checks pass;
- `FIX REQUIRED` — at least one definite defect remains; or
- `CANNOT DETERMINE` — evidence is insufficient for a required conclusion.

Save the report at `docs/reports/stage6-bob-final-review.md` and return the same
report in the response. Make no other file changes and do not commit or push.
