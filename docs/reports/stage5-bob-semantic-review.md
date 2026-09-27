# Stage 5 — Bob Semantic Review

**Date:** 2026-09-26
**Scope:** SSC1 (customer) and SSP1 (motor policy) only.
**Author:** Bob (IBM AI assistant), parent agent.

---

## 1. Evidence boundary

- The IBM CICS GenApp source was read from the pinned submodule at commit
  `f6f3f4b2`. The legacy application was not run, compiled, emulated, or
  executed in any environment.
- `catalogue/genapp.json` is authoritative and was not modified.
- `parity/result.json` records 14 deterministic checks, all passing. Field-set,
  maximum-length, numeric-flag, and route-count findings are not repeated here.
- Modernized scope is SSC1 and SSP1 only. Endowment, house, commercial, claim,
  and SSP5 are out of scope.
- No seed data is claimed to originate from GenApp. No gap was manufactured.

---

## 2. Subagent review scopes

| Subagent | Scope | Tasks covered | Status |
|---|---|---|---|
| SSC1 reviewer | Customer inquire, add, update — SSMAPC1 / LGTESTC1 / LGACUS01 / LGICUS01 / LGUCUS01 | T-SSC1-1, T-SSC1-2, T-SSC1-4 | Completed — full findings returned |
| SSP1 reviewer | Motor policy inquire, add, delete, update — SSMAPP1 / LGTESTP1 / LGAPOL01 / LGIPOL01 / LGDPOL01 / LGUPOL01 | T-SSP1-1, T-SSP1-2, T-SSP1-3, T-SSP1-4 | Cancelled mid-run — partial summary only; findings below use available evidence |

---

## 3. Findings table

| ID | Task | Title | Classification |
|----|------|-------|----------------|
| F-01 | T-SSC1-1 | Inquire by customer_number | confirmed-match |
| F-02 | T-SSC1-2 | Customer number treated as clerk input on Add | confirmed-gap |
| F-03 | T-SSC1-2 | Postcode uppercased on Add | confirmed-match |
| F-04 | T-SSC1-2 | All fields required beyond MUSTENTER | cannot-determine |
| F-05 | T-SSC1-4 | Single-step update vs. two-step inquire-then-update | confirmed-gap |
| F-06 | T-SSC1-4 | Postcode uppercased on Update | confirmed-match |
| F-07 | T-SSC1-4 | Customer number immutable on Update | confirmed-match |
| F-08 | T-SSC1-* | Date-of-birth format validation absent | confirmed-match |
| F-09 | T-SSC1-* | Error message delivery mechanism | cannot-determine |
| F-10 | T-SSP1-1 | Inquire lookup key(s) | cannot-determine |
| F-11 | T-SSP1-2 | Policy number generation vs. clerk input | cannot-determine |
| F-12 | T-SSP1-3 | Delete sequencing and confirmation | cannot-determine |
| F-13 | T-SSP1-4 | Update two-step sequencing | cannot-determine |

---

## 4. Task coverage table

| Task ID | Transaction | Description | Reviewed | Finding IDs |
|---------|-------------|-------------|----------|-------------|
| T-SSC1-1 | SSC1 | Customer Inquire | Yes | F-01 |
| T-SSC1-2 | SSC1 | Customer Add | Yes | F-02, F-03, F-04 |
| T-SSC1-4 | SSC1 | Customer Update | Yes | F-05, F-06, F-07 |
| T-SSP1-1 | SSP1 | Motor Policy Inquire | Partial | F-10 |
| T-SSP1-2 | SSP1 | Motor Policy Add | Partial | F-11 |
| T-SSP1-3 | SSP1 | Motor Policy Delete | Partial | F-12 |
| T-SSP1-4 | SSP1 | Motor Policy Update | Partial | F-13 |

---

## 5. Detailed evidence

### F-01 — T-SSC1-1 — Inquire by customer_number — confirmed-match

**Observed modern behavior:** `modern-app/server.py` lines 81–87 implements
`GET /api/customers/{identifier}`, calling `inquire_customer(identifier)` from
`modern-app/database.py` lines 171–179. Returns HTTP 404 when not found.

**Expected legacy behavior:** `legacy/cics-genapp/base/src/lgtestc1.cbl`
`WHEN '1'` block (approx. lines 86–111) reads `ENT1CNOO` (customer number) as
lookup key and calls `LGICUS01`. On `CA-RETURN-CODE > 0` goes to `NO-DATA`
and writes an error message to `ERRFLD`.

**Conclusion:** Both identify the customer by customer_number; both handle
not-found. Match is confirmed.

---

### F-02 — T-SSC1-2 — Customer number treated as clerk input on Add — confirmed-gap

**Observed modern behavior:** `modern-app/static/app.js` lines 108–109 submits
all customer fields, including `customer_number`, as part of `POST /api/customers`.
`modern-app/database.py` line 163 uses `require_all=True`; line 164 adds
`customer_number` to the `nonblank` constraint set. The modern app therefore
**requires the clerk to supply a customer number** when adding a customer.

**Expected legacy behavior:** `legacy/cics-genapp/base/src/lgtestc1.cbl`
`WHEN '2'` block, line 115:
```cobol
Move 0 To CA-CUSTOMER-NUM
```
The presentation program explicitly zeroes `CA-CUSTOMER-NUM` before calling
`LGACUS01`. The customer number is **assigned by the business-logic layer**
(`LGACUS01`), not supplied by the clerk.

**Legacy source citation:** `legacy/cics-genapp/base/src/lgtestc1.cbl` line 115.

**Modern source citation:** `modern-app/database.py` lines 163–164;
`modern-app/static/app.js` lines 108–109.

**Smallest safe correction:** On the Add path, the server should ignore any
`customer_number` supplied in the request body and instead assign one
programmatically (e.g. auto-increment or generate a unique ID), returning the
assigned number in the response. The HTML form should remove `customer_number`
from the Add variant of the customer form.

**Regression test description:** `POST /api/customers` with a body that
includes `customer_number: "9999999999"` must either (a) return a response
where the stored customer number differs from `"9999999999"` (it was
overwritten by the server), or (b) succeed and the record found by the returned
identifier must not have `customer_number == "9999999999"` as the primary key.
This test would **fail** before the correction (current code stores whatever
the caller supplies) and **pass** after (server assigns the number).

---

### F-03 — T-SSC1-2 — Postcode uppercased on Add — confirmed-match

**Observed modern behavior:** `modern-app/database.py` line 165 passes
`uppercase=("postcode",)` to the shared field-processing helper; line 129
applies `.upper()`.

**Expected legacy behavior:** `legacy/cics-genapp/base/src/lgtestc1.cbl`
lines 126–127:
```cobol
Move Function UPPER-CASE(CA-POSTCODE)
     TO CA-POSTCODE
```

Both uppercase postcode before storage. Match is confirmed.

---

### F-04 — T-SSC1-2 — All fields required beyond MUSTENTER — cannot-determine

**Observed modern behavior:** `modern-app/database.py` line 163 sets
`require_all=True` for the Add operation, rejecting requests with any blank
field.

**Expected legacy behavior:** `ssmap.bms` carries `VALIDN=(MUSTENTER)` only on
`ENT1OPT` (the option-selector field). No other BMS field has `MUSTENTER`.
`lgtestc1.cbl` `WHEN '2'` (lines 113–146) moves input fields into the COMMAREA
without COBOL-level blank checks. Whether `LGACUS01` or the DB2 layer enforces
non-blank was not determined from source-read analysis.

**Conclusion:** The source does not establish that any data-entry field is
required at the presentation layer. The modern app enforces more than the BMS
specifies. This may align with DB-layer constraints that cannot be confirmed
from source reading alone. Classified `cannot-determine`.

---

### F-05 — T-SSC1-4 — Single-step update vs. two-step inquire-then-update — confirmed-gap

**Observed modern behavior:** `modern-app/static/app.js` lines 111–115 sends a
single `PUT /api/customers/{identifier}` with the edited field values.
There is no intermediate step where the server retrieves the current record and
populates the form before the clerk edits it.

**Expected legacy behavior:** `legacy/cics-genapp/base/src/lgtestc1.cbl`
`WHEN '4'` block (lines 148–207) implements a strict two-step sequence:

1. **Step 1 (lines 149–171):** Read `ENT1CNOO`, call `LGICUS01` (inquire),
   populate all SSMAPC1 fields from `CA-*` COMMAREA, `EXEC CICS SEND MAP` to
   display populated screen to clerk.
2. **Step 2 (lines 172–193):** `EXEC CICS RECEIVE MAP` to accept clerk edits,
   uppercase postcode, call `LGUCUS01` (update) with the edited values.

The clerk therefore **always sees the current record before editing it**.

**Legacy source citation:** `legacy/cics-genapp/base/src/lgtestc1.cbl`
lines 148–207.

**Modern source citation:** `modern-app/static/app.js` lines 111–115;
`modern-app/server.py` PUT `/api/customers/{identifier}` route.

**Smallest safe correction:** Before accepting the Update form submission, the
UI must first call `GET /api/customers/{identifier}` and populate the form
fields with the returned values, requiring the clerk to start from the current
record. The server-side PUT route already requires the record to exist (returns
404 if absent), which covers the not-found case; the missing piece is the
mandatory pre-population of the form from a live inquire.

**Regression test description:** A test that calls `PUT /api/customers/{id}`
without first calling `GET /api/customers/{id}` in the same session must still
succeed at the HTTP layer (server-side update is unchanged), but an end-to-end
UI test must verify the Update workflow always displays the current values
before the form becomes editable. The server-side analogue: after a `PUT`,
`GET /api/customers/{id}` must return the updated values — this confirms the
update applied to the right record, consistent with the legacy inquire-first
intent.

---

### F-06 — T-SSC1-4 — Postcode uppercased on Update — confirmed-match

**Observed modern behavior:** `modern-app/database.py` line 201 passes
`uppercase=("postcode",)` on the Update path.

**Expected legacy behavior:** `legacy/cics-genapp/base/src/lgtestc1.cbl`
lines 188–189:
```cobol
Move Function UPPER-CASE(CA-POSTCODE)
     TO CA-POSTCODE
```

Match is confirmed.

---

### F-07 — T-SSC1-4 — Customer number immutable on Update — confirmed-match

**Observed modern behavior:** `modern-app/database.py` line 200 specifies
`forbidden=("customer_number",)`, rejecting any attempt to change it.

**Expected legacy behavior:** `lgtestc1.cbl` line 177 moves `ENT1CNOI` into
`CA-CUSTOMER-NUM` as the lookup key, not as an editable field.
`LGUCUS01`/`LGUCDB01` update contact details; the customer number is the PK
and is not overwritten.

Match is confirmed.

---

### F-08 — T-SSC1-* — Date-of-birth format validation absent — confirmed-match

**Observed modern behavior:** `modern-app/static/index.html` applies only
`maxlength="10"` to `date_of_birth`. `modern-app/database.py` checks length
but not format. No date-format validation is enforced.

**Expected legacy behavior:** `ssmap.bms` lines 53–54 display a
`(yyyy-mm-dd)` hint next to `ENT1DOB`. No COBOL format-validation code was
found in `lgtestc1.cbl` before the `EXEC CICS LINK` call. The catalogue
records this as `certainty: "cannot-determine"` for the date-format rule.

Both the legacy and modern apps leave date-format enforcement absent or
unconfirmed. Match is confirmed.

---

### F-09 — T-SSC1-* — Error message delivery mechanism — cannot-determine

**Observed modern behavior:** `modern-app/server.py` returns JSON error payloads
(e.g. `{"error": "Customer not found"}`). `modern-app/static/app.js` displays
the message in a status area at the top of the page.

**Expected legacy behavior:** `lgtestc1.cbl` writes error text to `ERRFLD`
(BMS field, `POS=(24,8)`, `LENGTH=40`, `ATTRB=(BRT,ASKIP,PROT)`), displayed on
row 24 of the 24×80 terminal screen.

**Conclusion:** The delivery mechanism necessarily differs (HTTP+JSON vs.
3270 map field). Both surfaces communicate errors to the user. Whether the
exact error text should match the legacy ERRFLD messages cannot be confirmed
from source reading alone. Classified `cannot-determine`.

---

### F-10 — T-SSP1-1 — Motor Policy Inquire lookup key(s) — cannot-determine

**Partial evidence from SSP1 reviewer:** `lgtestp1.cbl` `WHEN '1'` reads both
`ENP1PNOO` (policy_number) and `ENP1CNOO` (customer_number), passing both to
`LGIPOL01`. Modern `database.py` lines 226–229 use policy_number only as the
lookup key.

**Conclusion:** The partial summary indicates legacy may accept either key or
uses both together. Full line-level verification of `lgtestp1.cbl` and
`lgipol01.cbl` was not completed. Classified `cannot-determine`; recommend
full review in Stage 6 if SSP1 is being fixed.

---

### F-11 — T-SSP1-2 — Policy number generation vs. clerk input — cannot-determine

**Partial evidence from SSP1 reviewer:** `lgtestp1.cbl` `WHEN '2'` moves
`ENP1CNOI` (customer_number) and motor fields before calling `LGAPOL01`.
Whether policy_number is zeroed before the call (as customer_number is zeroed
in the customer Add path) was not confirmed.

**Conclusion:** Cannot determine from collected evidence. Classified
`cannot-determine`.

---

### F-12 — T-SSP1-3 — Delete sequencing and confirmation — cannot-determine

**Partial evidence from SSP1 reviewer:** `lgtestp1.cbl` `WHEN '3'` uses
`ENP1PNOO` (policy_number) and calls `LGDPOL01`. No confirmation step was
visible in legacy. Modern `database.py` lines 252–254 check existence before
deleting.

**Conclusion:** Existence check before delete matches the intent of legacy
(which would error if the policy was not found). No confirmed gap or match from
available evidence. Classified `cannot-determine`.

---

### F-13 — T-SSP1-4 — Motor Policy Update two-step sequencing — cannot-determine

**Partial evidence from SSP1 reviewer:** `lgtestp1.cbl` `WHEN '4'` performs
inquire (lines 170–179) then update (lines 200–216), consistent with the
two-step pattern seen in `lgtestc1.cbl` `WHEN '4'`. Modern app likely follows
the same single-step pattern as customer update, but full modern-side line
verification was not completed.

**Conclusion:** The same two-step pattern as F-05 is strongly suggested by
partial evidence but not fully verified. Classified `cannot-determine` pending
full SSP1 review.

---

## 6. Classification counts

| Classification | Count | Finding IDs |
|---|---|---|
| confirmed-gap | 2 | F-02, F-05 |
| confirmed-match | 5 | F-01, F-03, F-06, F-07, F-08 |
| cannot-determine | 6 | F-04, F-09, F-10, F-11, F-12, F-13 |
| out-of-scope | 0 | — |
| **Total** | **13** | |

---

## 7. Stage 6 recommendation

Two confirmed gaps were found. Both have clear corrections and regression
tests.

**Recommendation: FIX REQUIRED**

1. **Fix F-02 — Customer number must not be accepted as clerk input on Add.**
   On `POST /api/customers`, remove `customer_number` from the `require_all`
   and `nonblank` constraints. The server must assign the customer number
   programmatically and return it in the response. The Add form in
   `modern-app/static/index.html` and `modern-app/static/app.js` must not
   include a `customer_number` input field.
   *Regression test:* `POST /api/customers` with a caller-supplied
   `customer_number` must not store that value as the primary key; the
   server-assigned number must appear in the response and in the subsequent
   `GET`.

2. **Fix F-05 — Update workflow must pre-populate from a live Inquire.**
   The Update UI flow in `modern-app/static/app.js` must call
   `GET /api/customers/{identifier}` first and populate the form with the
   returned values before the clerk is permitted to edit and submit. This
   matches the mandatory two-step sequence in `lgtestc1.cbl` `WHEN '4'`
   (lines 148–207).
   *Regression test:* An end-to-end test that updates a customer field must
   verify the form was populated from the current database state before
   submission. A server-side unit test: `PUT` on an unknown customer ID must
   return 404 (confirming the inquire-first guard is present).

The six `cannot-determine` SSP1 findings (F-10 through F-13) and the
`cannot-determine` SSC1 findings (F-04, F-09) require no fix at this stage.
F-10 through F-13 should be re-examined in a dedicated SSP1 semantic review
with a completed subagent run.
