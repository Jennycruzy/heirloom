# Stage 1 Source Review

**Author:** Heirloom extraction agent
**Date:** 2026-09-26
**Sources read:** `legacy/cics-genapp/base/src/ssmap.bms` (689 lines),
`lgtestc1.cbl` (348 lines), `lgtestp1.cbl` (319 lines),
`lgtestp2.cbl` (301 lines), `lgtestp3.cbl` (300 lines),
`lgtestp4.cbl` (319 lines), business-logic COBOLs,
`base/Reference.md`.

**Constraint:** The legacy application was not run, compiled, emulated,
or executed in any environment. Every conclusion is derived from
reading source text only.

---

## 1. Extraction method

Three complementary techniques were used.

**BMS map parsing.**  Each `DFHMDI` macro in `ssmap.bms` defines one
terminal screen (map). Within each map every `DFHMDF` macro defines one
field. Named fields (those with a label before `DFHMDF`) are
user-visible and carry a BMS name used in COBOL I/O. The `ATTRB`,
`LENGTH`, `INITIAL`, `VALIDN`, and `JUSTIFY` parameters were read
verbatim. Commented-out lines (`*` in column 7) were noted and excluded.

**COBOL EVALUATE tracing.**  Each presentation program (`lgtestc1.cbl`,
`lgtestp1.cbl` through `lgtestp4.cbl`) contains one `EVALUATE` block
that dispatches on the option digit entered by the clerk. The `WHEN`
branches enumerate every executable action for that transaction. Each
branch was traced to confirm which business-logic program it calls
(`LGACUS01`, `LGICUS01`, etc.) and which COMMAREA fields it moves.

**COMMAREA copybook analysis.**  The `CA-*` data names referenced in the
MOVE statements were cross-checked against the field sizes declared in
the COMMAREA structure to identify discrepancies (see §6).

---

## 2. Screen and action counts

### 2a. Screen count — 6

| Map name | Transaction | Title |
|----------|-------------|-------|
| SSMAPC1 | SSC1 | General Insurance Customer Menu |
| SSMAPP1 | SSP1 | General Insurance Motor Policy Menu |
| SSMAPP2 | SSP2 | General Insurance Endowment Policy Menu |
| SSMAPP3 | SSP3 | General Insurance House Policy Menu |
| SSMAPP4 | SSP4 | General Insurance Commercial Policy Menu |
| SSMAPP5 | SSP5 | Policy Claim Menu |

Source: `ssmap.bms` lines 13, 112, 237, 346, 449, 606.

### 2b. Screen-defined action count — 20

Every option slot visible in any BMS map was counted as one
screen-defined action. This includes two options in SSMAPP5 whose
backing program was not found.

### 2c. Map-and-program-confirmed count — 18

Actions confirmed by both a BMS `INITIAL` label **and** a `WHEN` branch
in the corresponding presentation COBOL.

The two exceptions are T-SSP5-1 (Claim Inquiry) and T-SSP5-2 (Claim Add)
in SSMAPP5. Both have BMS option labels but no `LGTESTP5` file exists
anywhere in the source tree and `base/Reference.md` does not list SSP5.

---

## 3. Missing actions: SSC1 option 3, SSP4 option 4

**SSC1 option 3 — absent.**  The menu-option label at row 6 of SSMAPC1
(`ssmap.bms` lines 22–23) is blank (`INITIAL='                '`).
`lgtestc1.cbl` contains no `WHEN '3'` branch.  The option slot exists
in the BMS file but carries no label and has no COBOL dispatch.

**SSP4 option 4 — commented out.**  `ssmap.bms` lines 460–461 contain a
commented-out `DFHMDF` for the "4. Comm Update" label.
`lgtestp4.cbl` contains no `WHEN '4'` branch.

Both absent actions are excluded from the catalogue task list.

---

## 4. SSP5 — screen only, cannot determine

SSMAPP5 (`ssmap.bms` lines 606–648) defines two option slots:

```
INITIAL='1. Claim Inq  '   (line 611)
INITIAL='2. Claim Add  '   (line 614)
```

Options 3 and 4 are commented out (lines 615–618).

No file named `LGTESTP5.cbl` (or any case variant) exists in
`legacy/cics-genapp/base/src/`. The transaction `SSP5` does not appear
in `base/Reference.md` lines 46–57.

Tasks T-SSP5-1 and T-SSP5-2 are catalogued as
`legacySupportStatus: "screen-only-cannot-determine"`. No further
analysis is possible without the missing COBOL program.

---

## 5. Date format ambiguity

Several BMS fields display a `(yyyy-mm-dd)` hint immediately to the
right of the date input field (e.g. `ssmap.bms` lines 53–54, 146–147,
etc.). This confirms the expected display format.

However, no COBOL validation code enforcing this format was found in
`lgtestc1.cbl`, `lgtestp1.cbl`, `lgtestp2.cbl`, `lgtestp3.cbl`, or
`lgtestp4.cbl` before the `EXEC CICS LINK` call to the DB layer.
Whether the DB layer enforces the format could not be determined from
source-read alone.

**Certainty recorded as:** `"cannot-determine"` for date-format rules
in the catalogue.

---

## 6. Email length discrepancy

`ssmap.bms` line 93:
```
ENT1HMO DFHMDF POS=(13,50),LENGTH=27,...
```

The COMMAREA declaration (referenced as `CA-EMAIL-ADDRESS`) is 100
characters (`PIC X(100)`).

The BMS field silently truncates any email address longer than 27
characters at the terminal input layer. A COBOL `MOVE ENT1HMOI TO
CA-EMAIL-ADDRESS` will pad the remaining 73 characters with spaces —
not raise an error. This discrepancy is logged in the catalogue element
for `ENT1HMO`.

---

## 7. Field required-ness — cannot determine

The BMS `VALIDN=(MUSTENTER)` attribute is present only on the
option-selector field (`ENT1OPT`, `ENP1OPT`, etc.) in each screen.
No other field carries `MUSTENTER`.

Whether any data-entry field is semantically required was not
determinable from the presentation-layer COBOL without running or
tracing all business-logic programs (`LGACUS01`, `LGICUS01`, etc.).

**Certainty recorded as:** `"cannot-determine"` for required-field rules.

---

## 8. Shared-label ambiguity in SSMAPP4

SSMAPP4 (`ssmap.bms` lines 449–603) reuses single label fields for
paired peril and premium inputs:

- `Latitude/Longitude` (line 509–510) labels both `ENP4LAT` and
  `ENP4LON`.
- `Fire/Crime/Flood/Weather Peril/Prem` (lines 512–533) labels each
  adjacent pair of peril and premium fields.

The catalogue records each BMS-named input field individually and cites
the shared label as the `humanLabel` for the first field of each pair.

---

## 9. Postcode uppercase rule

`lgtestc1.cbl` lines 126–127 (Add path) and 188–189 (Update path):
```cobol
Move Function UPPER-CASE(CA-POSTCODE) TO CA-POSTCODE
```

This is the only COBOL-level input transformation found in the
presentation programs. The postcode value is forced to uppercase
before being passed to the business-logic layer. The BMS field itself
(`ENT1HPC`, LENGTH=8) accepts any character.

---

## 10. Limitations of source-read-only analysis

- The legacy application was not run. Field-level validation that occurs
  inside the business-logic COBOLs or the CICS DB2 layer cannot be
  confirmed from reading the presentation programs alone.
- Cross-reference between map field lengths and COMMAREA sizes was
  performed manually; only the email discrepancy was found.
- SSMAPP5 tasks cannot be confirmed without `LGTESTP5`.
- Date-format enforcement cannot be confirmed.
- Required-field rules (other than MUSTENTER) cannot be confirmed.
