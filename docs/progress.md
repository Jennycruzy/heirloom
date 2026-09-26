# Heirloom Progress

No stage may be marked passed until a deterministic check has actually been run and recorded.

---

## Stage 1 — Read the old system

**Completed: 2026-09-26**

Sources: IBM CICS GenApp pinned submodule (commit `f6f3f4b2`),
`ssmap.bms` (689 lines), five presentation COBOLs, business-logic COBOLs,
`base/Reference.md`. The legacy application was not run.

**Action counts:**
- 20 screen-defined actions (6 screens, all option slots visible in BMS)
- 18 map-and-program-confirmed executable tasks
- 2 screen-only-cannot-determine (SSMAPP5: no `LGTESTP5` found)

**Artefacts:**
- Catalogue: [`catalogue/genapp.json`](../catalogue/genapp.json)
- Schema: [`catalogue/schema.json`](../catalogue/schema.json)
- Validation result: [`catalogue/validation-result.json`](../catalogue/validation-result.json)
- Source review: [`docs/stage1-source-review.md`](stage1-source-review.md)
- Manual check: [`docs/stage1-customer-manual-check.md`](stage1-customer-manual-check.md)

**Validation:** All 20 checks in `catalogue/validation-result.json` passed.
No unresolved catalogue mismatch found in the SSMAPC1 manual check.

---

## Stage 2 — Show the old screens

Not started.

---

## Stage 3 — Modernize (first pass)

Not started.

---

## Stage 4 — The certain layer

Not started.

---

## Stage 5 — The judgement layer and parallel subagents

Not started.

---

## Stage 6 — The fix loop and the pull request

Not started.

---

## Stage 7 — The dashboard and hosting

Not started.

---

## Stage 8 — CI and measurement

Not started.

---

## Stage 9 — Submission

Not started.
