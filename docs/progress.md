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

**Completed: 2026-09-27**

The dependency-free dashboard loads the committed Stage 1 catalogue at runtime
and reconstructs every legacy map on an exact 24×80 character grid. The old
system is still read from source; no mainframe was run.

**Verified:**
- `node dashboard/test.mjs` passed: 6 screens, 20 actions, 18 confirmed tasks,
  and 2 cannot-determine actions.
- Every catalogue screen composes to exactly 24 rows of 80 characters.
- Customer screen SSMAPC1 rendered recognisably.
- Motor-policy screen SSMAPP1 rendered recognisably.
- No modern parity pass/fail result is shown; Stage 1 remains `not-assessed`.

**Artefacts:**
- Dashboard: [`dashboard/index.html`](../dashboard/index.html)
- Renderer library: [`dashboard/lib.mjs`](../dashboard/lib.mjs)
- Deterministic tests: [`dashboard/test.mjs`](../dashboard/test.mjs)
- SSC1 evidence: [`watsonx_sessions/heirloom_stage2_ssc1_reconstruction.jpeg`](../watsonx_sessions/heirloom_stage2_ssc1_reconstruction.jpeg)
- SSP1 evidence: [`watsonx_sessions/heirloom_stage2_ssp1_reconstruction.jpeg`](../watsonx_sessions/heirloom_stage2_ssp1_reconstruction.jpeg)

Watsonx.ai Granite was used as the documented fallback after Bobcoin usage was
reserved for later Bob tasks. Granite generation evidence is stored in
`watsonx_sessions/`; small runtime and accessibility defects were corrected
locally and the corrected files were tested before this stage was marked complete.

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
