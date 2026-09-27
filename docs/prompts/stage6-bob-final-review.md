# Final review: Stage 6 source-proven repairs

Review the current branch `fix/source-proven-parity-gaps` against the preserved
first pass at tag `stage3-first-pass`. Do not change files. Do not launch
subagents. Return one concise report and save the same report as
`docs/reports/stage6-bob-final-review.md`.

Use these as the authoritative review inputs:

- `docs/reports/stage5-evidence-audit.md`
- `docs/reports/stage6-before-fix.md`
- `docs/reports/stage6-after-fix.md`
- the Git diff from `stage3-first-pass` to the current branch
- the source lines cited by the Stage 5 evidence audit

Confirm whether each of these six repairs now matches the cited source:

1. Customer Add receives an application-assigned customer number.
2. Customer Update loads the existing record before editing.
3. Motor-policy Add receives an application-assigned policy number.
4. Motor inquiry uses customer number and policy number together.
5. Motor Update uses both identifiers and loads before editing.
6. Motor Delete uses both identifiers.

Also confirm that:

- customer delete was not added;
- the authoritative catalogue was not changed;
- no unsupported date, numeric, or required-field rule was invented;
- the first pass remains preserved at tag `stage3-first-pass`;
- the automated and browser evidence claimed in the after-fix report exists.

Use plain judge-facing language. Avoid unexplained internal labels. For each
item, state `confirmed`, `not confirmed`, or `cannot determine`, followed by a
short reason and exact file/line evidence. Finish with exactly one overall
result: `READY`, `FIX REQUIRED`, or `CANNOT DETERMINE`.
