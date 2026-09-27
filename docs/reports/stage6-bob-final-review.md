# Stage 6 — Bob Final Review

**Date:** 2026-09-27
**Branch:** `fix/source-proven-parity-gaps`
**Baseline tag:** `stage3-first-pass` → commit `d66643878eb3db8edc76e316467c32a82dc9cb1e`
**Reviewer:** Bob (IBM AI assistant)

---

## Safe starting check

Branch confirmed: `fix/source-proven-parity-gaps`. Working tree clean.
Tag `stage3-first-pass` exists and resolves to commit `d666438`. ✓

---

## Evidence boundary

The IBM CICS GenApp source was read from the pinned submodule at commit
`f6f3f4b2`. The legacy application was not run, compiled, emulated, or
executed. Every conclusion below is derived from reading source text and
from running the four automated checks in this session. Browser-evidence
images are accepted as human-confirmed supplementary evidence.

---

## Six repair behaviors

### 1. Customer Add does not accept a clerk-supplied customer number

**Result: Confirmed**

The legacy source shows that `lgtestc1.cbl` line 115 (`Move 0 To CA-CUSTOMER-NUM`) explicitly
zeroes the customer number before calling `LGACUS01`, meaning the business
layer (`lgacdb01.cbl` line 279: `INSERT INTO CUSTOMER … VALUES ( DEFAULT, …)`)
assigns the identifier, not the clerk.

The repaired implementation matches this. `database.py` lines 224–244 define
`add_customer()` using an `add_fields` dictionary that excludes
`customer_number` (lines 225–229). The server rejects any payload key named
`customer_number` on this path because it is not in `add_fields`. The assigned
identifier is returned to the caller. The UI layer (`app.js` lines 128–137)
submits only fields where `field !== "customer_number"` and populates the form
with the server-assigned value afterward. `workflows.mjs` lines 18–21 confirms
this by filtering out the generated field from the enabled set for any Add
operation.

**Legacy citation:** `lgtestc1.cbl` lines 113–115; `lgapdb01.cbl` line 279.
**Modern citation:** `database.py` lines 224–244; `app.js` lines 128–137; `workflows.mjs` lines 18–21.
**Browser evidence:** `heirloom_stage6_generated_customer_number.jpeg` — customer-number field locked, server-assigned value displayed.

---

### 2. Customer Update loads the existing record before editing is enabled

**Result: Confirmed**

The legacy source shows that `lgtestc1.cbl` lines 148–174 implement a strict
two-step sequence: first `LGICUS01` is called to populate all SSMAPC1 fields
from the database (lines 149–157), the map is sent to the terminal (lines
168–171), and only then are the clerk's edits received (line 172–174) before
`LGUCUS01` is called (lines 176–193). The clerk always sees the current record
before editing.

The repaired implementation matches this. `workflows.mjs` lines 25–27 sets the
initial update phase to `"load"`, which `enabledFields()` maps to
`["customer_number"]` only — all other fields are disabled. `app.js` lines
141–153 show that when `intent === "load-update"` the form submits a GET
request, populates the form with the returned record, then calls `markLoaded()`
(line 146) to transition the workflow to the `"edit"` phase, re-enabling the
editable fields. The PUT request is only sent once the phase is `"submit-update"`
(lines 155–162). A customer update therefore cannot proceed without a prior
successful GET.

**Legacy citation:** `lgtestc1.cbl` lines 148–174.
**Modern citation:** `workflows.mjs` lines 25–31; `app.js` lines 141–162.
**Browser evidence:** `heirloom_stage6_customer_update_load.jpeg` — record loaded and fields populated before editing is possible.

---

### 3. Motor-policy Add does not accept a clerk-supplied policy number

**Result: Confirmed**

The legacy source shows that `lgtestp1.cbl` `WHEN '2'` (lines 97–133) does not
move a clerk-entered policy number into the COMMAREA before calling `LGAPOL01`.
`lgapdb01.cbl` line 279 inserts with `DEFAULT` for `POLICYNUMBER`, meaning the
database assigns the identifier.

The repaired implementation matches this. `database.py` lines 285–307 define
`add_motor_policy()` using an `add_fields` dictionary that excludes
`policy_number` (lines 286–290). `workflows.mjs` line 20 identifies
`policy_number` as the generated field for the `motor` entity. `app.js`
lines 176–187 submit only `motorFields.filter(field !== "policy_number")` and
display the server-assigned policy number from the response.

**Legacy citation:** `lgtestp1.cbl` lines 97–125; `lgapdb01.cbl` lines 270–279.
**Modern citation:** `database.py` lines 285–307; `app.js` lines 176–187; `workflows.mjs` line 20.

---

### 4. Motor inquiry uses customer number and policy number together

**Result: Confirmed**

The legacy source shows that `lgtestp1.cbl` `WHEN '1'` lines 68–75 moves both
`ENP1CNOO` (customer number) and `ENP1PNOO` (policy number) into the COMMAREA
before calling `LGIPOL01`. The evidence audit cites `lgipdb01.cbl` lines
563–570 as filtering by both values in the SELECT.

The repaired implementation matches this. `database.py` lines 310–325 define
`inquire_motor_policy()` with an optional `customer_number` parameter; when
provided, the SELECT uses `WHERE policy_number = ? AND customer_number = ?`
(lines 320–323). `server.py` lines 97–104 show the GET route reads
`customer_number` from the query string and raises a 400 error if it is absent
or blank (`_customer_number()` at lines 130–134), making it effectively
required. `app.js` lines 189–204 always pass both identifiers when forming
the motor URL via `motorUrl()` (lines 107–110). `workflows.mjs` lines 22–24
confirm that the enabled fields for `inquire` are `["policy_number", "customer_number"]`.
The regression test `test_motor_inquiry_requires_matching_customer_and_policy`
(run in this session, passed) confirms a wrong customer number returns 404.

**Legacy citation:** `lgtestp1.cbl` lines 68–75.
**Modern citation:** `database.py` lines 310–325; `server.py` lines 97–104, 130–134; `app.js` lines 107–110, 189–204; `workflows.mjs` lines 22–24.

---

### 5. Motor Update uses both identifiers and loads the existing record before editing is enabled

**Result: Confirmed**

The legacy source shows that `lgtestp1.cbl` `WHEN '4'` lines 169–219 implement
the same two-step pattern: both identifiers are passed to `LGIPOL01` (lines
171–172), the populated screen is sent to the terminal (lines 192–195), the
clerk's edits are received (lines 196–198), and then both identifiers plus the
edited fields are passed to `LGUPOL01` (lines 200–219).

The repaired implementation matches this. `workflows.mjs` lines 25–31 give the
motor update workflow the same load-then-edit phase structure as customer
update. `app.js` lines 193–204 handle the `load-update` intent identically
to customer: a GET is issued using both identifiers via `motorUrl()`, the form
is populated, and the workflow transitions to `"edit"` phase. Lines 207–217
then send the PUT only after the load phase is complete. For the PUT itself,
`update_motor_policy()` in `database.py` lines 328–351 requires
`customer_number` in the payload (`nonblank=("customer_number",)`, line 333;
explicit check lines 335–336) and the UPDATE SQL filters by both
`policy_number` and `customer_number` (lines 341–343).

**Legacy citation:** `lgtestp1.cbl` lines 169–219.
**Modern citation:** `workflows.mjs` lines 25–31; `app.js` lines 193–217; `database.py` lines 328–351.
**Browser evidence:** `heirloom_stage6_motor_update_load.jpeg` — record loaded with both identifiers before editing enabled.

---

### 6. Motor Delete uses customer number and policy number together

**Result: Confirmed**

The legacy source shows that `lgtestp1.cbl` `WHEN '3'` lines 135–146 moves
both `ENP1CNOO` (customer number) and `ENP1PNOO` (policy number) into the
COMMAREA before calling `LGDPOL01`. The evidence audit cites `lgdpdb01.cbl`
lines 148–153 and 186–194 as filtering the DELETE by both columns.

The repaired implementation matches this. `database.py` lines 354–372 define
`delete_motor_policy()` which, when `customer_number` is supplied, first calls
`inquire_motor_policy()` with both identifiers (line 355–358) and raises an
error if the composite lookup returns nothing, then issues `DELETE … WHERE
policy_number = ? AND customer_number = ?` (lines 367–371). `server.py` lines
115–125 pass the `customer_number` query parameter (required by
`_customer_number()`) to `delete_motor_policy()`. `app.js` lines 219–222 use
`motorUrl()` which always includes both identifiers. `workflows.mjs` lines
22–24 confirm that delete enables only `["policy_number", "customer_number"]`.
The regression test `test_motor_delete_does_not_remove_another_customers_policy`
(run in this session, passed) confirms a wrong customer number returns 404.

**Legacy citation:** `lgtestp1.cbl` lines 135–146.
**Modern citation:** `database.py` lines 354–372; `server.py` lines 115–125; `app.js` lines 219–222; `workflows.mjs` lines 22–24.

---

## Automated check results

All four checks were run in this review session.

### `python3 -m unittest discover -s modern-app/tests -v`

```
Ran 15 tests in 5.753s
OK
```

15 of 15 tests passed. Includes `test_add_customer_assigns_identifier`,
`test_add_motor_policy_assigns_identifier`,
`test_motor_inquiry_requires_matching_customer_and_policy`,
`test_motor_delete_does_not_remove_another_customers_policy`,
`test_motor_update_uses_customer_and_policy_as_the_key`, and ten others.

### `node modern-app/tests/test_workflows.mjs`

```
Workflow regression tests passed.
```

All workflow assertions passed, including: customer Add locks `customer_number`;
motor Add locks `policy_number`; motor inquire and delete enable only the two
identifiers; customer and motor update enforce load-then-edit sequencing.

### `python3 parity/check.py`

```
Stage 4 deterministic checks: 14/14 passed; report: parity/result.json
```

All 14 deterministic checks passed. The repairs did not alter the authoritative
catalogue, task set, field set, input types, or verified maximum lengths.

### `git diff --check`

No whitespace errors. Exit code 0.

---

## Scope safeguards

**Customer delete was not added.** A search for `delete_customer` and
`DELETE … customer` across `server.py`, `database.py`, and `app.js` returned
no matches. The function does not exist.

**Authoritative catalogue unchanged.** `git diff stage3-first-pass..HEAD --
catalogue/genapp.json catalogue/schema.json` produced no output. Both files
are byte-for-byte identical to the first-pass baseline.

**No date, numeric, or additional required-field rule was added.** An
inspection of all lines added to `database.py`, `app.js`, and `index.html`
found no date-format validation, numeric-only constraint, or additional
`MUSTENTER`-style rule beyond what was already present.

**First-pass recoverable.** Tag `stage3-first-pass` resolves to commit
`d66643878eb3db8edc76e316467c32a82dc9cb1e` and is present in the repository.

**Browser-evidence files exist.** All three files named in the after-fix report
are present:
- `browser_evidence/heirloom_stage6_customer_update_load.jpeg` ✓
- `browser_evidence/heirloom_stage6_motor_update_load.jpeg` ✓
- `browser_evidence/heirloom_stage6_generated_customer_number.jpeg` ✓

---

## Remaining uncertainty

**Policy-number generation sequence.** The modern application assigns policy
numbers using `_next_identifier()` (`database.py` lines 194–202), which scans
existing numeric values and adds one. The legacy system uses a DB2 identity
column (`lgapdb01.cbl` line 279: `VALUES ( DEFAULT, …)`). Both assign the
number without clerk input, which is the source-proven behavior. The exact
numbering sequence and format differ and are not claimed to match.

**Motor delete not-found semantics.** As noted in the Stage 5 evidence audit,
`lgdpdb01.cbl` lines 196–202 contain ambiguous comment and SQLCODE handling
regarding whether a missing record is a success or an error. The modern
implementation raises a 404 for a missing record. This specific edge case
remains `cannot-determine` from source reading alone and no claim is made
that it matches legacy behavior.

---

## Overall result

**READY**

All six source-proven repairs are confirmed by independent inspection of the
legacy COBOL source and the repaired implementation. All four automated checks
pass. The scope safeguards are satisfied. No unsupported rule was introduced.
