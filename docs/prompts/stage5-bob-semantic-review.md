# Bob task — Stage 5 semantic review

Review Heirloom Stage 3 for semantic parity with the verified IBM CICS GenApp
source. This is a focused review, not an implementation task.

## Evidence boundary

- The legacy application was read from source; it was not run, compiled,
  emulated, or executed.
- `catalogue/genapp.json` is authoritative and must not be edited.
- `parity/result.json` contains the completed deterministic checks. Do not
  repeat field-set, maximum-length, numeric-flag, or route-count checks unless
  necessary to support a semantic finding.
- Modernized scope is only SSC1 customer and SSP1 motor policy.
- Do not review or propose endowment, house, commercial, claim, or SSP5
  modernization.
- Do not manufacture a gap. If the source does not determine an answer, record
  `cannot determine`.
- Do not claim the mainframe was run or that invented seed data came from
  GenApp.

## Parallel review

Use exactly two read-only subagents in parallel. The subagents must not edit
files; only the parent agent may write the final report:

1. **SSC1 reviewer** — compare the modern customer inquire, add, and update
   workflows with `catalogue/genapp.json` and the cited SSMAPC1/LGTESTC1/
   business-program source. Pay particular attention to the user sequence for
   update, identifier handling, postcode uppercasing, messages, and whether any
   required-field or date-format behavior is actually source-supported.
2. **SSP1 reviewer** — compare the modern motor-policy inquire, add, delete,
   and update workflows with `catalogue/genapp.json` and the cited SSMAPP1/
   LGTESTP1/business-program source. Pay particular attention to update and
   delete sequencing, customer references, identifier handling, messages, and
   whether numeric or date semantics are actually source-supported.

Each subagent must inspect the relevant files directly and return only
evidence-backed findings with exact workspace-relative file and line ranges.
Together they must explicitly cover all seven task IDs: T-SSC1-1, T-SSC1-2,
T-SSC1-4, T-SSP1-1, T-SSP1-2, T-SSP1-3, and T-SSP1-4. Do not spawn additional
subagents.

## Files to inspect

- `catalogue/genapp.json`
- `parity/mapping.json`
- `parity/result.json`
- `modern-app/database.py`
- `modern-app/server.py`
- `modern-app/static/index.html`
- `modern-app/static/app.js`
- `modern-app/tests/test_modern_app.py`
- `docs/reports/stage3-parity.md`
- Relevant files under `legacy/cics-genapp/base/src/` cited by the catalogue

## Classification

Classify every candidate finding as exactly one of:

- `confirmed-gap` — modern behavior conflicts with explicit source evidence.
- `confirmed-match` — modern behavior agrees with explicit source evidence.
- `cannot-determine` — the available source does not establish the semantic
  behavior.
- `out-of-scope` — not part of SSC1 or SSP1.

A `confirmed-gap` must include:

- the affected catalogue task ID;
- observed modern behavior;
- expected behavior;
- exact legacy source citation;
- exact modern source citation;
- smallest safe correction;
- a deterministic regression test that would fail before the correction.

Do not call style preferences, extra convenience, missing unverified
validation, or unsupported workflows parity gaps.

## Deliverable

Create exactly one file: `docs/reports/stage5-bob-semantic-review.md`.

The report must contain:

1. evidence boundary;
2. subagent names and their separate review scopes;
3. a table of all findings and classifications;
4. a seven-row task coverage table showing that every in-scope task was
   reviewed, even when it produced no gap;
5. detailed evidence for each `confirmed-gap` or `cannot-determine` item;
6. a final count by classification;
7. a clear recommendation for Stage 6:
   - `NO_FIX_REQUIRED`, or
   - a numbered list containing only confirmed fixes.

Do not modify application code, tests, the catalogue, parity results, or any
other file. Do not commit, tag, push, deploy, or open a pull request. Do not
claim tests were run unless you actually ran them and include the exact command
and result.
