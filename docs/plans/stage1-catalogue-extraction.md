# Stage 1 Execution Plan — Extract the Real GenApp Task Catalogue (Revised)

## Overview

This plan describes every step required to produce `catalogue/genapp.json` from the pinned
GenApp source at `legacy/cics-genapp` (commit `f6f3f4b2580d31b7d8dcc31ce3e3676f4cceaaaa`).
The legacy application is read from COBOL and BMS source only. It is never run, compiled,
emulated, or executed.

The catalogue records screens, screen elements, tasks, and validation rules with exact
workspace-relative file-and-line citations. No content may be invented. Every ambiguity must
be recorded as "cannot determine."

---

## Source Inventory

Paths are workspace-relative (from repository root).

| File | Lines | Role |
|------|-------|------|
| `legacy/cics-genapp/base/src/ssmap.bms` | 689 | BMS mapset: 6 maps (SSMAPC1, SSMAPP1–SSMAPP5) |
| `legacy/cics-genapp/base/src/lgtestc1.cbl` | 348 | Customer menu presentation (SSC1) |
| `legacy/cics-genapp/base/src/lgtestp1.cbl` | 319 | Motor policy presentation (SSP1) |
| `legacy/cics-genapp/base/src/lgtestp2.cbl` | 301 | Endowment policy presentation (SSP2) |
| `legacy/cics-genapp/base/src/lgtestp3.cbl` | 300 | House policy presentation (SSP3) |
| `legacy/cics-genapp/base/src/lgtestp4.cbl` | 319 | Commercial policy presentation (SSP4) |
| `legacy/cics-genapp/base/src/lgacus01.cbl` | 180 | Add customer business logic |
| `legacy/cics-genapp/base/src/lgicus01.cbl` | 167 | Inquire customer business logic |
| `legacy/cics-genapp/base/src/lgucus01.cbl` | 173 | Update customer business logic |
| `legacy/cics-genapp/base/src/lgapol01.cbl` | 170 | Add policy business logic |
| `legacy/cics-genapp/base/src/lgipol01.cbl` | 140 | Inquire policy business logic |
| `legacy/cics-genapp/base/src/lgupol01.cbl` | 202 | Update policy business logic |
| `legacy/cics-genapp/base/src/lgdpol01.cbl` | 187 | Delete policy business logic |
| `legacy/cics-genapp/base/Reference.md` | 124 | Official transaction and program reference |

No `LGTESTP5` program exists for `SSMAPP5`. See SSP5 entries throughout.

---

## Authoritative Action and Task Counts

These counts are derived from BMS source and COBOL dispatch. They are not assumed.

### 20 screen-defined actions

Every non-commented menu option label visible on a BMS map constitutes one screen-defined action.

| Transaction | Map | Screen-defined actions | Options | Evidence |
|-------------|-----|----------------------|---------|---------|
| SSC1 | SSMAPC1 | 3 | {1, 2, 4} | Option 3 label is blank: `ssmap.bms` lines 22–23, `INITIAL='                '`. No COBOL case for '3'. |
| SSP1 | SSMAPP1 | 4 | {1, 2, 3, 4} | `ssmap.bms` lines 117–124; `lgtestp1.cbl` EVALUATE dispatch |
| SSP2 | SSMAPP2 | 4 | {1, 2, 3, 4} | `ssmap.bms` lines 242–249; `lgtestp2.cbl` EVALUATE dispatch |
| SSP3 | SSMAPP3 | 4 | {1, 2, 3, 4} | `ssmap.bms` lines 351–358; `lgtestp3.cbl` EVALUATE dispatch |
| SSP4 | SSMAPP4 | 3 | {1, 2, 3} | Option 4 commented out: `ssmap.bms` lines 460–461. No COBOL case. |
| SSP5 | SSMAPP5 | 2 | visible: {1, 2} | `ssmap.bms` lines 611–614. Options 3–4 commented out: lines 615–618. |
| **Total** | | **20** | | |

### 18 map-and-program-confirmed executable tasks

A task is map-and-program-confirmed only when a non-blank BMS option label is paired with a
COBOL EVALUATE case in a presentation program that links to a business program.

SSP5 options 1 and 2 have BMS labels but no presentation program (`LGTESTP5` does not exist
in the source tree; `SSP5` is absent from `base/Reference.md` lines 46–57). They are
screen-defined actions but not map-and-program-confirmed tasks.

| taskId | name | operation | optionKey | transaction | legacySupportStatus |
|--------|------|-----------|-----------|-------------|---------------------|
| T-SSC1-1 | Inquire Customer | inquire | '1' | SSC1 | map-and-program-confirmed |
| T-SSC1-2 | Add Customer | add | '2' | SSC1 | map-and-program-confirmed |
| T-SSC1-4 | Update Customer | update | '4' | SSC1 | map-and-program-confirmed |
| T-SSP1-1 | Inquire Motor Policy | inquire | '1' | SSP1 | map-and-program-confirmed |
| T-SSP1-2 | Add Motor Policy | add | '2' | SSP1 | map-and-program-confirmed |
| T-SSP1-3 | Delete Motor Policy | delete | '3' | SSP1 | map-and-program-confirmed |
| T-SSP1-4 | Update Motor Policy | update | '4' | SSP1 | map-and-program-confirmed |
| T-SSP2-1 | Inquire Endowment Policy | inquire | '1' | SSP2 | map-and-program-confirmed |
| T-SSP2-2 | Add Endowment Policy | add | '2' | SSP2 | map-and-program-confirmed |
| T-SSP2-3 | Delete Endowment Policy | delete | '3' | SSP2 | map-and-program-confirmed |
| T-SSP2-4 | Update Endowment Policy | update | '4' | SSP2 | map-and-program-confirmed |
| T-SSP3-1 | Inquire House Policy | inquire | '1' | SSP3 | map-and-program-confirmed |
| T-SSP3-2 | Add House Policy | add | '2' | SSP3 | map-and-program-confirmed |
| T-SSP3-3 | Delete House Policy | delete | '3' | SSP3 | map-and-program-confirmed |
| T-SSP3-4 | Update House Policy | update | '4' | SSP3 | map-and-program-confirmed |
| T-SSP4-1 | Inquire Commercial Policy | inquire | '1' | SSP4 | map-and-program-confirmed |
| T-SSP4-2 | Add Commercial Policy | add | '2' | SSP4 | map-and-program-confirmed |
| T-SSP4-3 | Delete Commercial Policy | delete | '3' | SSP4 | map-and-program-confirmed |

### 2 screen-only / cannot-determine SSP5 actions

| taskId | name | operation | optionKey | transaction | legacySupportStatus |
|--------|------|-----------|-----------|-------------|---------------------|
| T-SSP5-1 | Inquire Policy Claim | inquire | '1' | SSP5 | screen-only-cannot-determine |
| T-SSP5-2 | Add Policy Claim | add | '2' | SSP5 | screen-only-cannot-determine |

Both are included in the `tasks` array. Their `legacySupportStatus` records the absence of a
presentation program and the absence of `SSP5` from `base/Reference.md`. They do not claim
executability.

---

## SSMAPC1 Field Counts (Explicit)

These four counts are distinct and must each be validated separately.

| Count | Number | Members |
|-------|--------|---------|
| Named fields total | 12 | ENT1CNO, ENT1FNA, ENT1LNA, ENT1DOB, ENT1HNM, ENT1HNO, ENT1HPC, ENT1HP1, ENT1HP2, ENT1HMO, ENT1OPT, ERRFLD |
| Editable named fields (UNPROT) | 11 | ENT1CNO, ENT1FNA, ENT1LNA, ENT1DOB, ENT1HNM, ENT1HNO, ENT1HPC, ENT1HP1, ENT1HP2, ENT1HMO, ENT1OPT |
| Clerk data-entry fields (UNPROT, not the menu option) | 10 | ENT1CNO, ENT1FNA, ENT1LNA, ENT1DOB, ENT1HNM, ENT1HNO, ENT1HPC, ENT1HP1, ENT1HP2, ENT1HMO |
| Protected display/error fields (PROT or ASKIP) | 1 | ERRFLD |

ENT1OPT is editable (UNPROT) but is the menu option selector, not a clerk data-entry field.
ERRFLD has `ATTRB=(BRT,ASKIP,PROT)` — it is a display-only output field.

---

## Catalogue Data Model

### Top-level structure of catalogue/genapp.json

```
{
  "provenance": { ... },
  "screens": [ { ...screen objects... } ],
  "tasks": [ { ...task objects... } ]
}
```

### provenance object

| Field | Type | Value |
|-------|------|-------|
| `repository` | string | `"https://github.com/cicsdev/cics-genapp"` |
| `commit` | string | `"f6f3f4b2580d31b7d8dcc31ce3e3676f4cceaaaa"` |
| `extractionDate` | string | ISO-8601 date of extraction run |
| `statement` | string | `"The IBM CICS GenApp source was read from the pinned submodule. The legacy application was not run, compiled, emulated, or executed in any environment."` |

### screen object

Each screen corresponds to one DFHMDI in `ssmap.bms`.

| Field | Type | Notes |
|-------|------|-------|
| `mapsetName` | string | Always `"SSMAP"` |
| `mapName` | string | e.g. `"SSMAPC1"` |
| `transactionId` | string | e.g. `"SSC1"` — from INITIAL='SSxx' on line 1 of map |
| `title` | string | From title DFHMDF INITIAL text |
| `size` | object | `{"rows": 24, "cols": 80}` |
| `presentationProgram` | string or `"cannot-determine"` | From `base/Reference.md` or `"cannot-determine"` for SSP5 |
| `sourceRef` | object | `{"file": "legacy/cics-genapp/base/src/ssmap.bms", "lineStart": N, "lineEnd": N}` pointing to DFHMDI line |
| `elements` | array | Every active DFHMDF in source order (see below) |

### element object (within screen.elements)

`elements` contains every non-commented DFHMDF in source order. This is sufficient to
reconstruct the 24×80 screen layout. Named fields (with a BMS symbolic name) also appear in
a derived `fields` view for rules and parity checks.

| Field | Type | Notes |
|-------|------|-------|
| `elementId` | string | `E-<MAPNAME>-<NNN>` (zero-padded, source order) |
| `sourceOrder` | integer | 1-based position within the map's element list |
| `bmsName` | string or null | Symbolic name if present; null for anonymous DFHMDF |
| `role` | string | One of: `"title"`, `"menuOption"`, `"label"`, `"hint"`, `"input"`, `"option"`, `"error"`, `"separator"`, `"cannot-determine"` |
| `row` | integer | From POS=(row,col) |
| `col` | integer | From POS=(row,col) |
| `length` | integer | From LENGTH= |
| `attrb` | string | Raw ATTRB value(s) from BMS source |
| `protected` | boolean | true if ATTRB contains PROT or ASKIP |
| `numeric` | boolean | true if ATTRB contains NUM |
| `validn` | string or null | e.g. `"MUSTENTER"` or null |
| `initialValue` | string or null | From INITIAL= (stripped) or null |
| `xinitValue` | string or null | From XINIT= or null (hex initial value) |
| `justify` | string or null | e.g. `"RIGHT,ZERO"` or null |
| `sourceRef` | object | `{"file": "...", "lineStart": N, "lineEnd": N, "excerpt": "..."}` |

**Role assignment rules (deterministic from BMS attributes):**
- `"title"`: anonymous DFHMDF at row 1, ATTRB contains BRT, non-blank INITIAL
- `"menuOption"`: anonymous DFHMDF at rows 4–7 with INITIAL matching pattern `[1-4]\. ` or blank
- `"label"`: anonymous DFHMDF with ASKIP attribute and non-blank INITIAL at rows 4–21, not matching title or menuOption
- `"hint"`: anonymous DFHMDF with INITIAL containing `(yyyy-mm-dd)` or similar format strings
- `"input"`: named DFHMDF with ATTRB containing UNPROT (excluding OPT and ERR fields)
- `"option"`: named DFHMDF for the Select Option input (VALIDN=MUSTENTER, row 22)
- `"error"`: named DFHMDF at row 24 with ATTRB containing PROT and BRT
- `"separator"`: anonymous DFHMDF with LENGTH=1 and INITIAL=' '
- `"cannot-determine"`: any element not matching the above patterns

**Shared-label cases — do not infer mechanically:**

Two cases in SSMAPP4 where a single label DFHMDF precedes two named input fields on the
same row. The `humanLabel` for both fields is recorded as the shared literal with a note
explaining it is a shared label, not a per-field label:

| Label (ssmap.bms line) | Field 1 | Field 2 |
|------------------------|---------|---------|
| `'Latitude/Longitude'` (line 509–510) | ENP4LAT (line 511) | ENP4LON (line 515) |
| `'Fire Peril/Prem'` (line 534–535) | ENP4FPE (line 536) | ENP4FPR (line 540) |
| `'Crime Peril/Prem'` (line ~545–546) | ENP4CPE | ENP4CPR |
| `'Flood Peril/Prem'` (line ~556–557) | ENP4XPE | ENP4XPR |
| `'Weather Peril/Prem'` (line ~567–568) | ENP4WPE | ENP4WPR |

For these fields: `humanLabel` = the shared literal text; `labelNote` = `"shared-label"`;
`labelSource` points to the label DFHMDF lines. No invented label may substitute.

### task object

| Field | Type | Notes |
|-------|------|-------|
| `taskId` | string | Pattern `^T-(SSC1\|SSP[1-5])-[1-4]$` — matches transaction and option number |
| `name` | string | Plain-English task name |
| `outcome` | string | Plain-English description of what the task achieves |
| `transactionId` | string | e.g. `"SSC1"` |
| `mapName` | string | e.g. `"SSMAPC1"` |
| `operation` | string | One of: `"inquire"`, `"add"`, `"update"`, `"delete"` |
| `optionKey` | string | The single character entered by the clerk: `"1"`, `"2"`, `"3"`, or `"4"` |
| `allowedOptions` | array of strings | Exact set for this transaction (see below) |
| `legacySupportStatus` | string | `"map-and-program-confirmed"` or `"screen-only-cannot-determine"` |
| `modernParityStatus` | string | Always `"not-assessed"` in Stage 1 — no modern app exists |
| `presentationProgram` | string or null | COBOL presentation program name; null for SSP5 |
| `businessPrograms` | array of strings | Business program(s) linked; empty for SSP5 |
| `sourceEvidence` | array of objects | `{"file": "...", "lineStart": N, "lineEnd": N, "excerpt": "..."}` |
| `navigationVariants` | array or null | SSP4-1 only: the four REQUEST-ID derivation paths |

**Allowed option sets (exact, not generic 1–4):**

| Transaction | allowedOptions |
|-------------|----------------|
| SSC1 | `["1", "2", "4"]` |
| SSP1 | `["1", "2", "3", "4"]` |
| SSP2 | `["1", "2", "3", "4"]` |
| SSP3 | `["1", "2", "3", "4"]` |
| SSP4 | `["1", "2", "3"]` |
| SSP5 | `["1", "2"]` — visible BMS only; runtime enforcement cannot determine |

### rule object (within task.rules or element.rules)

| Field | Type | Notes |
|-------|------|-------|
| `ruleId` | string | `R-<SCOPE>-<NNN>` where SCOPE is a taskId or elementId |
| `type` | string | `"required"`, `"numeric"`, `"maxLength"`, `"allowedValues"`, `"formatHint"`, `"transformRule"`, or `"validationCode"` |
| `certainty` | string | `"explicit"` (directly in source), `"inferred"` (reasonably derived), or `"cannot-determine"` |
| `plainEnglish` | string | Human-readable description of the rule |
| `sourceRef` | object | `{"file": "...", "lineStart": N, "lineEnd": N, "excerpt": "..."}` |

---

## Sub-Task 1 — Create catalogue/schema.json

**Intent**
Define the JSON Schema that `catalogue/genapp.json` must satisfy. Written first so the
catalogue is built to a spec.

**Expected Outcomes**
- `catalogue/schema.json` passes JSON parse.
- Schema declares and enforces the data model above.
- `taskId` pattern: `^T-(SSC1|SSP[1-5])-[1-4]$`
- `elementId` pattern: `^E-[A-Z0-9]+-[0-9]{3}$`
- `fieldId` (on named elements): `^F-[A-Z0-9]+-[0-9]{3}$`
- `legacySupportStatus` enum: `["map-and-program-confirmed", "screen-only-cannot-determine"]`
- `modernParityStatus` enum: `["not-assessed"]` (only valid value in Stage 1)
- `operation` enum: `["inquire", "add", "update", "delete"]`
- `role` enum: `["title", "menuOption", "label", "hint", "input", "option", "error", "separator", "cannot-determine"]`
- `certainty` enum: `["explicit", "inferred", "cannot-determine"]`
- Every `sourceRef` must contain `file` (string), `lineStart` (integer ≥ 1), `lineEnd` (integer ≥ lineStart), `excerpt` (string).
- `size` must have `rows: 24` and `cols: 80` (const).

**Todo List**
- [ ] Create `catalogue/` directory.
- [ ] Write `catalogue/schema.json`.

**Status** — `[ ] pending`

---

## Sub-Task 2 — catalogue/genapp.json: provenance block

**Intent**
Populate the `provenance` object. No BMS or COBOL reading required.

**Expected Outcomes**
`catalogue/genapp.json` with valid `provenance` block, empty `screens: []` and `tasks: []`.

**Todo List**
- [ ] Write initial `catalogue/genapp.json` with provenance block.

**Status** — `[ ] pending`

---

## Sub-Task 3 — Populate screens array (metadata only)

**Intent**
Write one screen object per DFHMDI with metadata and an empty `elements` array.
`elements` is populated in Sub-Task 4.

**Screen objects to write:**

| mapName | transactionId | title | presentationProgram | DFHMDI lineStart |
|---------|---------------|-------|---------------------|-----------------|
| SSMAPC1 | SSC1 | General Insurance Customer Menu | LGTESTC1 | 13 |
| SSMAPP1 | SSP1 | General Insurance Motor Policy Menu | LGTESTP1 | 112 |
| SSMAPP2 | SSP2 | General Insurance Endowment Policy Menu | LGTESTP2 | 237 |
| SSMAPP3 | SSP3 | General Insurance House Policy Menu | LGTESTP3 | 346 |
| SSMAPP4 | SSP4 | General Insurance Commercial Policy Menu | LGTESTP4 | 449 |
| SSMAPP5 | SSP5 | General Insurance Policy Claim Menu | cannot-determine | 606 |

Title text for SSMAPP2: `ssmap.bms` lines 239–240, `INITIAL='General Insurance Endowment Policy Menu '` (stripped).
Title text for SSMAPP3: `ssmap.bms` lines 348–349, `INITIAL='General Insurance House Policy Menu '` (stripped).

**Todo List**
- [ ] Read `ssmap.bms` lines 1–689 and `base/Reference.md` lines 46–57.
- [ ] Write six screen objects with exact `sourceRef` line numbers.
- [ ] Record SSP5 `presentationProgram: "cannot-determine"` with `note` field explaining the absence.

**Status** — `[ ] pending`

---

## Sub-Task 4 — Populate elements arrays

**Intent**
For each screen, record every non-commented DFHMDF in source order as an `elements` entry.
This is the complete screen content required to reconstruct each 24×80 display.

**Extraction rules**
- Read every non-commented DFHMDF line (BMS comment lines begin with `*` in column 7).
- Assign `elementId` in source order: `E-SSMAPC1-001`, `E-SSMAPC1-002`, …
- For named fields (DFHMDF with a symbolic name), also assign `fieldId`: `F-SSMAPC1-001` in
  named-field sequence order within the map.
- `lineStart` = line of the DFHMDF macro name; `lineEnd` = last continuation line before the
  next DFHMDF or comment.
- `excerpt` = the first physical line of the DFHMDF entry (truncated to 60 chars).

**Label-to-input association (humanLabel derivation)**

For each named input element, inspect the immediately preceding anonymous DFHMDF elements:
- If exactly one label DFHMDF precedes the input with no other named field intervening,
  `humanLabel` = its INITIAL text (stripped); `labelSource` points to that element's lines.
- If a single label DFHMDF precedes two adjacent named input fields (shared label), set
  `humanLabel` = the shared text for both fields; add `"labelNote": "shared-label"` on each.
  Applies to: ENP4LAT/ENP4LON (label `ssmap.bms` lines 509–510), ENP4FPE/ENP4FPR (lines
  534–535), ENP4CPE/ENP4CPR, ENP4XPE/ENP4XPR, ENP4WPE/ENP4WPR.
- If the mapping cannot be determined from source, `humanLabel: null`; `labelNote: "cannot-determine"`.
- Never invent a cleaner label.

**Named field counts per screen (from BMS source):**

| Screen | Named fields total | Editable (UNPROT) | Data-entry (UNPROT, not option) | Protected display/error |
|--------|--------------------|-------------------|----------------------------------|------------------------|
| SSMAPC1 | 12 | 11 | 10 | 1 (ERRFLD) |
| SSMAPP1 | 15 | 14 | 13 | 1 (ERP1FLD) |
| SSMAPP2 | 13 | 12 | 11 | 1 (ERP2FLD) |
| SSMAPP3 | 12 | 11 | 10 | 1 (ERP3FLD) |
| SSMAPP4 | 22 | 21 | 20 | 1 (ERP4FLD) |
| SSMAPP5 | 10 | 9 | 8 | 1 (ERP5FLD) |

**Todo List**
- [ ] For each map, read every non-commented DFHMDF line block in `ssmap.bms`.
- [ ] Assign `elementId` in source order; assign `fieldId` to named fields only.
- [ ] Apply label association rules, using shared-label notation where applicable.
- [ ] Record `protected` and `numeric` strictly from ATTRB; do not infer.
- [ ] Record `validn: "MUSTENTER"` for the 6 OPT fields (lines 101, 226, 335, 438, 595, 681).
- [ ] Confirm SSMAPC1 element count, named field count, editable count, data-entry count, and protected count before writing.

**Status** — `[ ] pending`

---

## Sub-Task 5 — Populate tasks array

**Intent**
Write all 20 task records (18 map-and-program-confirmed + 2 SSP5 screen-only).

**Source evidence for each task (exact line ranges):**

| taskId | BMS label line(s) | COBOL dispatch lines |
|--------|-------------------|---------------------|
| T-SSC1-1 | ssmap.bms 18–19 | lgtestc1.cbl 86–111 |
| T-SSC1-2 | ssmap.bms 20–21 | lgtestc1.cbl 113–146 |
| T-SSC1-4 | ssmap.bms 24–25 | lgtestc1.cbl 148–207 |
| T-SSP1-1 | ssmap.bms 117–118 | lgtestp1.cbl 68–95 |
| T-SSP1-2 | ssmap.bms 119–120 | lgtestp1.cbl 97–133 |
| T-SSP1-3 | ssmap.bms 121–122 | lgtestp1.cbl 135–167 |
| T-SSP1-4 | ssmap.bms 123–124 | lgtestp1.cbl 169–234 |
| T-SSP2-1 | ssmap.bms 242–243 | lgtestp2.cbl (confirm line range at write time) |
| T-SSP2-2 | ssmap.bms 244–245 | lgtestp2.cbl (confirm line range at write time) |
| T-SSP2-3 | ssmap.bms 246–247 | lgtestp2.cbl (confirm line range at write time) |
| T-SSP2-4 | ssmap.bms 248–249 | lgtestp2.cbl (confirm line range at write time) |
| T-SSP3-1 | ssmap.bms 351–352 | lgtestp3.cbl (confirm line range at write time) |
| T-SSP3-2 | ssmap.bms 353–354 | lgtestp3.cbl (confirm line range at write time) |
| T-SSP3-3 | ssmap.bms 355–356 | lgtestp3.cbl (confirm line range at write time) |
| T-SSP3-4 | ssmap.bms 357–358 | lgtestp3.cbl (confirm line range at write time) |
| T-SSP4-1 | ssmap.bms 454–455 | lgtestp4.cbl 73–154 (with navigationVariants) |
| T-SSP4-2 | ssmap.bms 456–457 | lgtestp4.cbl 156–195 |
| T-SSP4-3 | ssmap.bms 458–459 | lgtestp4.cbl 197–234 |
| T-SSP5-1 | ssmap.bms 611–612 | no COBOL source |
| T-SSP5-2 | ssmap.bms 613–614 | no COBOL source |

**SSP4-1 navigationVariants** (from `lgtestp4.cbl` lines 74–120):
- `01ICOM`: both customer and policy numbers provided
- `02ICOM`: policy number only
- `03ICOM`: customer number only
- `05ICOM`: postcode only

**SSP5 task records:**
- `legacySupportStatus: "screen-only-cannot-determine"`
- `modernParityStatus: "not-assessed"`
- `presentationProgram: null`
- `businessPrograms: []`
- `sourceEvidence`: BMS label entries only; no COBOL evidence
- `note`: `"LGTESTP5 does not exist in the source tree. SSP5 is absent from base/Reference.md lines 46–57. Executability cannot be determined from available source."`

**Todo List**
- [ ] Read `lgtestp2.cbl` and `lgtestp3.cbl` EVALUATE dispatch to confirm exact line ranges.
- [ ] Write all 20 task objects.
- [ ] Confirm `allowedOptions` per transaction matches the exact sets in the Counts section.
- [ ] Set `modernParityStatus: "not-assessed"` on every task.

**Status** — `[ ] pending`

---

## Sub-Task 6 — Populate rules

**Intent**
Record every validation rule explicitly present in BMS attributes or COBOL source.
Use `"cannot-determine"` for any rule not readable from source.

**BMS-derived rules (explicit, deterministic)**

| Rule type | Basis | Fields affected | Source |
|-----------|-------|-----------------|--------|
| `required` | `VALIDN=(MUSTENTER)` | All 6 OPT fields | `ssmap.bms` lines 101, 226, 335, 438, 595, 681 |
| `numeric` | `NUM` in ATTRB | All 6 OPT fields | Same lines as above |
| `maxLength` | `LENGTH=N` on UNPROT element | Every editable element | Per-element source line |
| `rightZeroJustify` | `JUSTIFY=(RIGHT,ZERO)` | ENT1CNO, ENP*PNO, ENP*CNO, numeric value fields | Per-element source line |

**COBOL-derived rules (explicit)**

| Rule | Certainty | Source lines | Excerpt |
|------|-----------|--------------|---------|
| SSC1 allowed options: {1,2,4}; other values trigger error | explicit | `lgtestc1.cbl` EVALUATE + OTHER | `EVALUATE ENT1OPTO ... WHEN OTHER` |
| SSP1–3 allowed options: {1,2,3,4}; other values trigger error | explicit | `lgtestp1.cbl` EVALUATE + OTHER (same structure in 2,3) | `EVALUATE ENP1OPTO ... WHEN OTHER` |
| SSP4 allowed options: {1,2,3}; no update dispatch | explicit | `lgtestp4.cbl` EVALUATE | No WHEN '4' case |
| Add Customer: COMMAREA length ≥ WS-CA-HEADER-LEN + WS-CUSTOMER-LEN | explicit | `lgacus01.cbl` lines 108–115 | `IF EIBCALEN < ...` |
| Update Customer: REQUEST-ID must = '01UCUS' | explicit | `lgucus01.cbl` line 110 | `IF CA-REQUEST-ID NOT = '01UCUS'` |
| Delete Policy: REQUEST-ID ∈ {'01DEND','01DMOT','01DHOU','01DCOM'} | explicit | `lgdpol01.cbl` lines 119–122 | `EVALUATE CA-REQUEST-ID WHEN ...` |
| Update Policy COMMAREA lengths by type | explicit | `lgupol01.cbl` lines 113–141 | EVALUATE with per-type length checks |
| Customer postcode uppercased before storage | explicit | `lgtestc1.cbl` lines 126–127 | `MOVE FUNCTION UPPER-CASE(CA-POSTCODE)` |
| Commercial inquiry REQUEST-ID derivation | explicit | `lgtestp4.cbl` lines 74–120 | IF/ELSE chain |

**Rules recorded as cannot-determine**

| Rule | Reason | Source evidence |
|------|--------|----------------|
| Date field format validation (yyyy-mm-dd) | BMS hint text present at adjacent label elements; no COBOL format check found before DB layer | Hint elements at ssmap.bms lines 53–54, 146–147, 155–156, 206–207, 648 |
| Required-ness of individual data-entry fields | No COBOL blank checks for detail fields in presentation programs | Reviewed lgtestc1.cbl, lgtestp1–4.cbl |
| SSP5 rules | No presentation program source available | ssmap.bms only |

**Email length discrepancy (record as explicit discrepancy, not a rule)**
BMS `ENT1HMO` at `ssmap.bms` line 93–94: `LENGTH=27`.
COMMAREA `CA-EMAIL-ADDRESS PIC X(100)` (from `lgcmarea.cpy`).
The BMS field is shorter than the COMMAREA slot. Record the BMS length as the screen-entry
maximum. The COMMAREA capacity is larger. This is a factual discrepancy, not a rule
inference.

**Todo List**
- [ ] For each OPT element write `required` and `numeric` rule objects with exact lineStart/lineEnd.
- [ ] For each editable element write a `maxLength` rule object citing the LENGTH= line.
- [ ] Write COBOL-derived rules with excerpts confirmed against the source file.
- [ ] Write cannot-determine rule objects with source evidence citations.
- [ ] Write the email length discrepancy as a `note` field on ENT1HMO, not as a rule.

**Status** — `[ ] pending`

---

## Sub-Task 7 — Create docs/stage1-source-review.md

**Intent**
Human-readable record of the extraction method, both action counts, all ambiguities, and
the limitations of source-read-only analysis.

**Expected Outcomes**
`docs/stage1-source-review.md` contains:
1. Extraction method: BMS parsing, COBOL EVALUATE tracing, COMMAREA copybook analysis.
2. Both action counts: 20 screen-defined, 18 map-and-program-confirmed.
3. SSP5: map and two BMS options present, no LGTESTP5, not in Reference.md.
4. SSC1 option 3 absent: blank label lines 22–23; no COBOL case.
5. SSP4 option 4 absent: commented out lines 460–461; no COBOL case.
6. Date format ambiguity: hint text present; no COBOL validation before DB.
7. Email length discrepancy: BMS 27 vs COMMAREA 100.
8. Individual field required-ness: cannot determine.
9. Shared-label ambiguity in SSMAPP4.
10. Explicit statement: the legacy application was not run.

**Status** — `[ ] pending`

---

## Sub-Task 8 — Create docs/stage1-customer-manual-check.md

**Intent**
Manual field-by-field check of SSMAPC1 against `ssmap.bms` lines 13–110 and its programs.
Provides human-readable evidence that the catalogue's SSMAPC1 entries are correct.

**Expected Outcomes**
- Complete element table for SSMAPC1: every DFHMDF (named and anonymous), with elementId,
  role, BMS name, POS, LENGTH, ATTRB, INITIAL, fieldId if applicable, humanLabel if applicable.
- Four named-field count assertions (12 / 11 / 10 / 1) all confirmed against BMS source.
- Comparison of each catalogue entry against BMS source; any mismatch recorded explicitly.
- Postcode uppercase rule from `lgtestc1.cbl` lines 126–127 noted.
- Email BMS/COMMAREA length discrepancy noted.
- An explicit statement that no unresolved catalogue mismatch was found (or a list of those
  that were found, blocking Sub-Task 9).

**Status** — `[ ] pending`

---

## Sub-Task 9 — Create catalogue/scripts/validate.py and run validation

**Intent**
A checked-in Python script performs all validation checks and writes
`catalogue/validation-result.json`. `docs/progress.md` Stage 1 may be updated only when
every check in `validation-result.json` shows `"status": "pass"`.

**Script location:** `catalogue/scripts/validate.py`

**Dependency:** `jsonschema` library. Pin version in
`catalogue/scripts/requirements.txt` as `jsonschema==4.23.0`. Install with:
```
pip install -r catalogue/scripts/requirements.txt
```
No unpinned install instruction may appear in the plan or in any script.

**Checks the script must perform:**

| Check | ID | Assertion |
|-------|----|-----------|
| JSON parse: genapp.json | CHK-01 | File parses without error |
| JSON parse: schema.json | CHK-02 | File parses without error |
| Schema validation | CHK-03 | genapp.json validates against schema.json using jsonschema Draft 7 |
| Source files exist | CHK-04 | Every `file` path in every `sourceRef` exists relative to workspace root |
| Line ranges valid | CHK-05 | Every `lineStart`/`lineEnd` pair is within the line count of the cited file |
| Excerpt present | CHK-06 | Every `excerpt` string appears within the cited lineStart–lineEnd range |
| Duplicate taskIds | CHK-07 | No two task objects share a taskId |
| Duplicate elementIds | CHK-08 | No two element objects in any screen share an elementId |
| Duplicate fieldIds | CHK-09 | No two elements with a fieldId share that fieldId across all screens |
| Screen count | CHK-10 | Exactly 6 screen objects |
| Screen-defined action count | CHK-11 | Exactly 20 task objects |
| Map-and-program-confirmed count | CHK-12 | Exactly 18 tasks with `legacySupportStatus == "map-and-program-confirmed"` |
| Screen-only count | CHK-13 | Exactly 2 tasks with `legacySupportStatus == "screen-only-cannot-determine"` |
| modernParityStatus | CHK-14 | All tasks have `modernParityStatus == "not-assessed"` |
| Grid coordinates — elements | CHK-15 | For every element: 1 ≤ row ≤ 24; 1 ≤ col ≤ 80; col + length − 1 ≤ 80 |
| SSMAPC1 named field count | CHK-16 | Exactly 12 elements in SSMAPC1 with a non-null `bmsName` |
| SSMAPC1 editable count | CHK-17 | Exactly 11 SSMAPC1 elements with `bmsName` non-null and `protected == false` |
| SSMAPC1 data-entry count | CHK-18 | Exactly 10 SSMAPC1 elements with `bmsName` non-null, `protected == false`, and `role != "option"` |
| SSMAPC1 protected count | CHK-19 | Exactly 1 SSMAPC1 element with `bmsName` non-null and `protected == true` |
| Allowed options exact | CHK-20 | Each task's `allowedOptions` matches the exact set for its transactionId |

**Output file:** `catalogue/validation-result.json`

Schema of `validation-result.json`:
```json
{
  "runTimestamp": "<ISO-8601 datetime>",
  "overallStatus": "pass" | "fail",
  "checks": [
    {
      "id": "CHK-01",
      "description": "...",
      "status": "pass" | "fail",
      "detail": "..."
    }
  ]
}
```

**Todo List**
- [ ] Create `catalogue/scripts/` directory.
- [ ] Write `catalogue/scripts/requirements.txt` with `jsonschema==4.23.0`.
- [ ] Write `catalogue/scripts/validate.py` implementing all 20 checks.
- [ ] Run: `pip install -r catalogue/scripts/requirements.txt`
- [ ] Run: `python3 catalogue/scripts/validate.py`
- [ ] Confirm `validation-result.json` exists and `overallStatus == "pass"`.

**Status** — `[ ] pending`

---

## Sub-Task 10 — Update docs/progress.md

**Intent**
Mark Stage 1 complete. Blocked until Sub-Tasks 1–9 all pass and
`docs/stage1-customer-manual-check.md` records no unresolved catalogue mismatch.

**Expected Outcomes**
Stage 1 entry updated to include:
- Completion date.
- Both action counts: 20 screen-defined, 18 map-and-program-confirmed.
- Links to `catalogue/genapp.json`, `catalogue/validation-result.json`,
  `docs/stage1-source-review.md`, `docs/stage1-customer-manual-check.md`.
- Statement: `"All 20 checks in catalogue/validation-result.json passed."` (or list failures if any remain).

**Status** — `[ ] pending`

---

## Execution Order

```
Sub-Task 1  (schema.json)
Sub-Task 2  (provenance block)
Sub-Task 3  (screen metadata)
Sub-Task 4  (elements arrays — depends on Sub-Task 3)
Sub-Task 5  (tasks — depends on Sub-Tasks 3, 4)
Sub-Task 6  (rules — depends on Sub-Tasks 4, 5)
Sub-Task 7  (stage1-source-review.md — depends on Sub-Tasks 2–6)
Sub-Task 8  (customer manual check — depends on Sub-Task 4)
Sub-Task 9  (validate.py + validation-result.json — depends on Sub-Tasks 1–8)
Sub-Task 10 (progress.md — blocked on Sub-Task 9 pass + manual check clean)
```

---

## Files to Create / Modify

| Path | Action | Depends on |
|------|--------|-----------|
| `catalogue/schema.json` | Create | Sub-Task 1 |
| `catalogue/genapp.json` | Create | Sub-Tasks 2–6 |
| `catalogue/scripts/requirements.txt` | Create | Sub-Task 9 |
| `catalogue/scripts/validate.py` | Create | Sub-Task 9 |
| `catalogue/validation-result.json` | Generated by script | Sub-Task 9 |
| `docs/stage1-source-review.md` | Create | Sub-Task 7 |
| `docs/stage1-customer-manual-check.md` | Create | Sub-Task 8 |
| `docs/progress.md` | Update Stage 1 only | Sub-Task 10 |

**Files NOT changed:** `.gitignore`, `.bobignore`, `SECURITY.MD`, `README.md`,
`legacy/cics-genapp` (submodule is read-only).

---

## Acceptance Criteria

Stage 1 is complete when all of the following are true:

1. `catalogue/genapp.json` parses as valid JSON (CHK-01).
2. `catalogue/schema.json` parses as valid JSON (CHK-02).
3. `catalogue/genapp.json` validates against `catalogue/schema.json` (CHK-03).
4. Every cited source file exists (CHK-04).
5. Every cited line range is within the file and the excerpt appears in that range (CHK-05, CHK-06).
6. No duplicate taskId, elementId, or fieldId (CHK-07, CHK-08, CHK-09).
7. Exactly 6 screens (CHK-10).
8. Exactly 20 task records (CHK-11).
9. Exactly 18 map-and-program-confirmed tasks (CHK-12).
10. Exactly 2 screen-only-cannot-determine tasks (CHK-13).
11. All tasks have `modernParityStatus: "not-assessed"` (CHK-14).
12. All element coordinates within the 24×80 grid (CHK-15).
13. SSMAPC1 named/editable/data-entry/protected counts: 12/11/10/1 (CHK-16–19).
14. Per-transaction `allowedOptions` exact sets confirmed (CHK-20).
15. `catalogue/validation-result.json` exists with `overallStatus: "pass"`.
16. `docs/stage1-source-review.md` is present and records both action counts with derivation.
17. `docs/stage1-customer-manual-check.md` records no unresolved catalogue mismatch.
18. `docs/progress.md` Stage 1 updated with completion date and validation summary.
19. No content invented; every ambiguity recorded as "cannot determine."
20. No modern application was created, accessed, or assumed.

---

## Confirmed Ambiguities and Limitations

| Item | Status | Source evidence |
|------|--------|----------------|
| SSP5 (Policy Claim Menu) | screen-only-cannot-determine | `ssmap.bms` line 606–686; no LGTESTP5; absent from `base/Reference.md` lines 46–57 |
| SSC1 option 3 | absent — blank label | `ssmap.bms` lines 22–23: `INITIAL='                '`; no COBOL case |
| SSP4 option 4 (Update Commercial) | absent — commented out | `ssmap.bms` lines 460–461 (BMS comment markers); no COBOL dispatch |
| Date format validation | cannot determine | Hint elements present; no COBOL format check before DB layer |
| Individual field required-ness | cannot determine | No COBOL blank checks in presentation programs |
| Email field BMS vs COMMAREA length | factual discrepancy | `ssmap.bms` ENT1HMO `LENGTH=27`; COMMAREA `CA-EMAIL-ADDRESS PIC X(100)` |
| SSP4 inquiry REQUEST-ID variants | explicit | `lgtestp4.cbl` lines 74–120 — four derivation paths |
| Shared label — Lat/Lon and Peril/Prem pairs | shared-label notation | `ssmap.bms` lines 509–510, 534–535 and equivalent lines for Crime, Flood, Weather pairs |
