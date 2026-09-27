# Heirloom Progress

No stage may be marked passed until a deterministic check has actually been run and recorded.

---

## Stage 1 — Build a source-derived legacy catalogue

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

## Stage 2 — Reconstruct the legacy screens exactly

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

## Stage 3 — Build and preserve the first modern implementation

**Completed: 2026-09-27**

The Python 3.11 standard-library application modernizes only the seven
source-confirmed SSC1 customer and SSP1 motor-policy tasks. It uses SQLite and
browser-native HTML, CSS, and JavaScript. Seed records are explicitly invented
hackathon test data and are not represented as mainframe records.

**Verified:**
- Customer inquire, add, and update are implemented; customer delete is
  deliberately absent.
- Motor-policy inquire, add, update, and delete are implemented.
- `python3 -m unittest discover -s modern-app/tests -v` passed all 10 database,
  validation, API, static-file, and HTTP lifecycle checks.
- `node --check modern-app/static/app.js` passed.
- Human browser checks confirmed customer inquiry, motor-policy inquiry, and
  customer creation.
- The untouched first pass is preserved by Git tag `stage3-first-pass` at
  commit `d666438`.

**Artefacts:**
- Application guide: [`modern-app/README.md`](../modern-app/README.md)
- Data layer: [`modern-app/database.py`](../modern-app/database.py)
- HTTP server: [`modern-app/server.py`](../modern-app/server.py)
- Automated tests: [`modern-app/tests/test_modern_app.py`](../modern-app/tests/test_modern_app.py)
- Parity report: [`docs/reports/stage3-parity.md`](reports/stage3-parity.md)
- First-run evidence: [`watsonx_sessions/heirloom_stage3_modern_app_first_run.jpeg`](../watsonx_sessions/heirloom_stage3_modern_app_first_run.jpeg)
- Customer inquiry: [`watsonx_sessions/heirloom_stage3_customer_inquiry.jpeg`](../watsonx_sessions/heirloom_stage3_customer_inquiry.jpeg)
- Motor-policy inquiry: [`watsonx_sessions/heirloom_stage3_motor_policy_inquiry.jpeg`](../watsonx_sessions/heirloom_stage3_motor_policy_inquiry.jpeg)
- Customer creation: [`watsonx_sessions/heirloom_stage3_customer_add.jpeg`](../watsonx_sessions/heirloom_stage3_customer_add.jpeg)

The assessment is source-grounded: the legacy application was not run, and the
authoritative Stage 1 catalogue was not altered. No intentional or observed
gap was introduced.

---

## Stage 4 — Compare exact facts with machine checks

**Completed: 2026-09-27**

Deterministic checks now compare the committed SSC1 and SSP1 catalogue with the
modern database definitions and browser form. No model judgement is used and
the catalogue is not modified.

**Verified:**
- `python3 parity/check.py` passed all 14 checks.
- Confirmed task operations match the UI exactly: three customer actions and
  four motor-policy actions.
- Both BMS input sets map exactly to the modern field sets and maximum lengths.
- No numeric-only restriction is invented for catalogue fields marked
  non-numeric.
- Every browser input has the exact API name, text type, and verified maximum
  length.
- The 10 Stage 3 application tests and the Stage 2 dashboard tests still pass.

**Artefacts:**
- Checker: [`parity/check.py`](../parity/check.py)
- Explicit BMS mapping: [`parity/mapping.json`](../parity/mapping.json)
- Machine-readable result: [`parity/result.json`](../parity/result.json)
- Usage and scope: [`parity/README.md`](../parity/README.md)

The previously committed Stage 1 validation result remains 20/20 passed. Its
optional validator was not rerun during Stage 4 because `jsonschema` is not
installed in the current standard-library application environment.

---

## Stage 5 — Review workflow meaning with independent AI reviewers

**Completed: 2026-09-27**

Bob launched separate SSC1 and SSP1 semantic reviewers. The SSC1 reviewer
completed; the SSP1 reviewer stalled and was stopped, so its unresolved items
were completed by a direct evidence audit rather than represented as finished.
The original Bob report is preserved unchanged alongside the audit.

**Outcome:**
- Five semantic matches confirmed.
- Six source-proven gaps identified: generated customer and policy numbers,
  inquire-first update flows, and composite customer-plus-policy identification
  for motor inquiry, update, and delete.
- Date, numeric, additional required-field, and delete-not-found semantics were
  not invented where the source did not establish them.
- No application code was changed during Stage 5.

**Artefacts:**
- Bob task: [`docs/prompts/stage5-bob-semantic-review.md`](prompts/stage5-bob-semantic-review.md)
- Bob recovery instruction: [`docs/prompts/stage5-bob-finish-now.md`](prompts/stage5-bob-finish-now.md)
- Original Bob report: [`docs/reports/stage5-bob-semantic-review.md`](reports/stage5-bob-semantic-review.md)
- Evidence audit: [`docs/reports/stage5-evidence-audit.md`](reports/stage5-evidence-audit.md)
- Bob session evidence: [`bob_sessions/jenny_builds_task05_parallel_semantic_review.png`](../bob_sessions/jenny_builds_task05_parallel_semantic_review.png)
- Bob final-result evidence: [`bob_sessions/jenny_builds_task05_semantic_review_result.png`](../bob_sessions/jenny_builds_task05_semantic_review_result.png)

---

## Stage 6 — Repair only proven gaps and obtain final review

**Completed: 2026-09-27**

The six source-proven Stage 5 workflow differences have been repaired on the
dedicated `fix/source-proven-parity-gaps` branch. The first pass remains
recoverable at tag `stage3-first-pass`.

**Verified so far:**
- Pre-fix evidence captured the expected five failing/erroring application
  checks and the missing browser workflow state.
- Post-fix application suite: 15/15 passed.
- Browser workflow regression test passed.
- Catalogue parity suite remained 14/14 passed.
- Python compilation, JavaScript syntax checks, and whitespace checks passed.

**Human browser confirmation:** passed for customer retrieve-before-edit,
motor-policy retrieve-before-edit with both identifiers, and application-
assigned customer numbers. The three screenshots are stored in
`browser_evidence/` and linked from the after-fix report.

**Final independent review:** Bob inspected the cited legacy source, repaired
implementation, automated results, and browser evidence. All six repairs were
confirmed, all four requested checks passed, and the overall result was
`READY`. The report retains two honest, non-blocking uncertainties: the exact
legacy identifier sequence and the ambiguous motor-delete not-found behavior.

**Artefacts:**
- Before evidence: [`docs/reports/stage6-before-fix.md`](reports/stage6-before-fix.md)
- After evidence: [`docs/reports/stage6-after-fix.md`](reports/stage6-after-fix.md)
- Final Bob review: [`docs/reports/stage6-bob-final-review.md`](reports/stage6-bob-final-review.md)
- Bob `READY` evidence: [`bob_sessions/jenny_builds_task06_final_repair_review.png`](../bob_sessions/jenny_builds_task06_final_repair_review.png)

---

## Stage 7 — Present the evidence and deploy the judge dashboard

**Completed: 2026-09-27**

The repaired application and source-reconstruction dashboard are deployed on
an isolated VPS service behind Nginx and HTTPS:

- Judge entry point: <https://heirloom.54-154-121-30.sslip.io/>
- Reconstructed screens: <https://heirloom.54-154-121-30.sslip.io/dashboard/>

The deployment uses invented seed records only. Direct external checks returned
HTTP 200 for the home page, dashboard, and a composite-key motor-policy API
request. The TLS certificate is configured for automatic renewal. Existing VPS
applications were not stopped or replaced.

**Artefact:**
- Deployment record: [`docs/reports/stage7-deployment.md`](reports/stage7-deployment.md)

---

## Stage 8 — Automate checks and publish measured results

**Completed: 2026-09-27**

`python3 scripts/verify.py` runs every suite and publishes the measured result
to `evidence/verification.json`, which the public verification page reads.
CircleCI runs the same command on every push. A new citation check confirms
that all 67 published source references resolve to real lines.

**Verified:**
- Full verification: 118/118 across six suites (citations 67/67, parity 14/14,
  application 21/21, workflows 5/5, screens, syntax 10/10).
- Dashboard source links, previously 404 because they pointed at submodule
  paths inside this repository, now open the pinned upstream GenApp file.
- Updating a missing customer now returns 404; its new check failed before the
  fix (`400 != 404`) and passes after.
- The structural parity checks remain 14/14 against the redesigned workspace.
- Observed timing: an informal controlled retry of an SSP1 evidence lookup
  took 50 seconds by manual source review and 30 seconds with the earlier
  dashboard, a 20-second (40%) reduction. The initial attempt took two minutes
  both ways, so this is reported as one observation, not a general claim.

**Artefacts:**
- Verification command: [`scripts/verify.py`](../scripts/verify.py)
- Citation check: [`scripts/check_citations.py`](../scripts/check_citations.py)
- Findings with citations: [`evidence/findings.json`](../evidence/findings.json)
- Published result: [`evidence/verification.json`](../evidence/verification.json)
- CI configuration: [`.circleci/config.yml`](../.circleci/config.yml)
- Record: [`docs/reports/stage8-verification.md`](reports/stage8-verification.md)
- Timing measurement and limitations: [`docs/reports/stage8-measurements.md`](reports/stage8-measurements.md)

---

## Stage 9 — Assemble and verify the submission package

**Completed: 2026-09-27**

Jenny Builds completed the LabLab project submission before submissions
closed. The submitted package points judges to the HTTPS application, the
source-reconstruction dashboard, the public GitHub repository, Bob evidence,
source-linked reports, measured results, and the preserved first-pass tag.

The team is a solo team. Submission-ready Bob evidence is stored as ten PNG
files using the `jenny_builds_taskNN_description.png` naming convention. Local
form-writing drafts under `submission/` remain intentionally uncommitted.
