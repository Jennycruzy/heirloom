# Stage 1 Customer Screen Manual Check

**Screen:** SSMAPC1 (transaction SSC1 — General Insurance Customer Menu)
**BMS source:** `legacy/cics-genapp/base/src/ssmap.bms` lines 13–106
**Presentation program:** `lgtestc1.cbl`
**Date checked:** 2026-09-26

**Purpose:** Element-by-element verification that every DFHMDF entry in
SSMAPC1 is correctly represented in `catalogue/genapp.json`. Confirms the
four named-field counts (12 / 11 / 10 / 1). Notes every discrepancy found.

---

## 1. Complete element table

Each row corresponds to one DFHMDF macro in source order.
"Named?" indicates whether the field has a BMS label (and thus a name usable
in COBOL I/O). "Prot?" = ASKIP or PROT in ATTRB. "Editable?" = UNPROT.

| # | BMS lines | BMS name | POS (row,col) | LENGTH | ATTRB | INITIAL / note | Named? | Prot? | Role |
|---|-----------|----------|--------------|--------|-------|----------------|--------|-------|------|
| 1 | 14 | — | (1,1) | 4 | ASKIP,BRT | 'SSC1' | No | Yes | title |
| 2 | 15–16 | — | (1,12) | 31 | BRT,ASKIP | 'General Insurance Customer Menu' | No | Yes | title |
| 3 | 18–19 | — | (4,8) | 16 | NORM,ASKIP | '1. Cust Inquiry ' | No | Yes | menuOption |
| 4 | 20–21 | — | (5,8) | 16 | NORM,ASKIP | '2. Cust Add     ' | No | Yes | menuOption |
| 5 | 22–23 | — | (6,8) | 16 | NORM,ASKIP | '                ' | No | Yes | menuOption (blank — option 3 absent) |
| 6 | 24–25 | — | (7,8) | 16 | NORM,ASKIP | '4. Cust Update  ' | No | Yes | menuOption |
| 7 | 27–28 | — | (4,30) | 12 | NORM,ASKIP | 'Cust Number ' | No | Yes | label |
| 8 | 29–30 | **ENT1CNO** | (4,50) | 10 | NORM,UNPROT,IC,FSET | JUSTIFY=(RIGHT,ZERO) | **Yes** | No | input |
| 9 | 31–32 | — | (4,61) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 10 | 34–35 | — | (5,30) | 16 | NORM,ASKIP | 'Cust Name :First' | No | Yes | label |
| 11 | 36–37 | **ENT1FNA** | (5,50) | 10 | NORM,UNPROT,FSET | ' ' | **Yes** | No | input |
| 12 | 38–39 | — | (5,61) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 13 | 40–41 | — | (6,30) | 16 | NORM,ASKIP | '          :Last' | No | Yes | label |
| 14 | 42–43 | **ENT1LNA** | (6,50) | 20 | NORM,UNPROT,FSET | ' ' | **Yes** | No | input |
| 15 | 44–45 | — | (6,71) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 16 | 47–48 | — | (7,30) | 12 | NORM,ASKIP | 'DOB         ' | No | Yes | label |
| 17 | 49–50 | **ENT1DOB** | (7,50) | 10 | NORM,UNPROT,FSET | ' ' | **Yes** | No | input |
| 18 | 51–52 | — | (7,61) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 19 | 53–54 | — | (7,63) | 12 | NORM,ASKIP | '(yyyy-mm-dd)' | No | Yes | hint |
| 20 | 56–57 | — | (8,30) | 12 | NORM,ASKIP | 'House Name  ' | No | Yes | label |
| 21 | 58–59 | **ENT1HNM** | (8,50) | 20 | NORM,UNPROT,FSET | ' ' | **Yes** | No | input |
| 22 | 60–61 | — | (8,71) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 23 | 63–64 | — | (9,30) | 12 | NORM,ASKIP | 'House Number' | No | Yes | label |
| 24 | 65–66 | **ENT1HNO** | (9,50) | 4 | NORM,UNPROT,FSET | ' ' | **Yes** | No | input |
| 25 | 67–68 | — | (9,55) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 26 | 70–71 | — | (10,30) | 12 | NORM,ASKIP | 'Postcode    ' | No | Yes | label |
| 27 | 72–73 | **ENT1HPC** | (10,50) | 8 | NORM,UNPROT,FSET | ' ' | **Yes** | No | input |
| 28 | 74–75 | — | (10,59) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 29 | 77–78 | — | (11,30) | 12 | NORM,ASKIP | 'Phone: Home ' | No | Yes | label |
| 30 | 79–80 | **ENT1HP1** | (11,50) | 20 | NORM,UNPROT,FSET | ' ', JUSTIFY=(BLANK) | **Yes** | No | input |
| 31 | 81–82 | — | (11,71) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 32 | 84–85 | — | (12,30) | 12 | NORM,ASKIP | 'Phone: Mob  ' | No | Yes | label |
| 33 | 86–87 | **ENT1HP2** | (12,50) | 20 | NORM,UNPROT,FSET | ' ', JUSTIFY=(BLANK) | **Yes** | No | input |
| 34 | 88–89 | — | (12,71) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 35 | 91–92 | — | (13,30) | 12 | NORM,ASKIP | 'Email  Addr ' | No | Yes | label |
| 36 | 93–94 | **ENT1HMO** | (13,50) | 27 | NORM,UNPROT,FSET | ' ', JUSTIFY=(BLANK) | **Yes** | No | input |
| 37 | 95–96 | — | (13,78) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 38 | 98–99 | — | (22,8) | 14 | NORM,ASKIP | 'Select Option ' | No | Yes | label |
| 39 | 100–101 | **ENT1OPT** | (22,24) | 1 | NORM,NUM,UNPROT,FSET | VALIDN=(MUSTENTER) | **Yes** | No | option |
| 40 | 102–103 | — | (22,26) | 1 | PROT,ASKIP | ' ' | No | Yes | separator |
| 41 | 105–106 | **ERRFLD** | (24,8) | 40 | BRT,ASKIP,PROT | ' ' | **Yes** | Yes | error |

Total elements in table: **41** (matching the source; unnamed separators and labels included).

---

## 2. Named-field count assertions

The catalogue must record exactly the following counts for SSMAPC1.
Each count is confirmed against the BMS table above.

### 2a. Total named fields — 12 (CHK-16)

Fields with a BMS label (rows 8, 11, 14, 17, 21, 24, 27, 30, 33, 36, 39, 41 above):

| # | BMS name | Row | Col | Length | Protected |
|---|----------|-----|-----|--------|-----------|
| 1 | ENT1CNO | 4 | 50 | 10 | No |
| 2 | ENT1FNA | 5 | 50 | 10 | No |
| 3 | ENT1LNA | 6 | 50 | 20 | No |
| 4 | ENT1DOB | 7 | 50 | 10 | No |
| 5 | ENT1HNM | 8 | 50 | 20 | No |
| 6 | ENT1HNO | 9 | 50 | 4 | No |
| 7 | ENT1HPC | 10 | 50 | 8 | No |
| 8 | ENT1HP1 | 11 | 50 | 20 | No |
| 9 | ENT1HP2 | 12 | 50 | 20 | No |
| 10 | ENT1HMO | 13 | 50 | 27 | No |
| 11 | ENT1OPT | 22 | 24 | 1 | No |
| 12 | ERRFLD | 24 | 8 | 40 | **Yes** |

**Count: 12. Confirmed.**

### 2b. Editable named fields (UNPROT) — 11 (CHK-17)

All named fields except ERRFLD (PROT): ENT1CNO through ENT1OPT = 11.

**Count: 11. Confirmed.**

### 2c. Clerk data-entry fields (UNPROT, not option) — 10 (CHK-18)

Editable fields minus ENT1OPT (role = option): 11 − 1 = 10.

Fields: ENT1CNO, ENT1FNA, ENT1LNA, ENT1DOB, ENT1HNM, ENT1HNO,
ENT1HPC, ENT1HP1, ENT1HP2, ENT1HMO.

**Count: 10. Confirmed.**

### 2d. Protected named fields — 1 (CHK-19)

Only ERRFLD has PROT.

**Count: 1. Confirmed.**

---

## 3. Catalogue entry comparison

Each named field in `catalogue/genapp.json` (SSMAPC1 elements with
`bmsName != null`) was compared against the BMS table above.

| BMS name | Cat. row | BMS row | Match? | Cat. col | BMS col | Match? | Cat. len | BMS len | Match? | Cat. protected | BMS protected | Match? |
|----------|----------|---------|--------|----------|---------|--------|----------|---------|--------|----------------|---------------|--------|
| ENT1CNO | 4 | 4 | ✓ | 50 | 50 | ✓ | 10 | 10 | ✓ | false | false | ✓ |
| ENT1FNA | 5 | 5 | ✓ | 50 | 50 | ✓ | 10 | 10 | ✓ | false | false | ✓ |
| ENT1LNA | 6 | 6 | ✓ | 50 | 50 | ✓ | 20 | 20 | ✓ | false | false | ✓ |
| ENT1DOB | 7 | 7 | ✓ | 50 | 50 | ✓ | 10 | 10 | ✓ | false | false | ✓ |
| ENT1HNM | 8 | 8 | ✓ | 50 | 50 | ✓ | 20 | 20 | ✓ | false | false | ✓ |
| ENT1HNO | 9 | 9 | ✓ | 50 | 50 | ✓ | 4 | 4 | ✓ | false | false | ✓ |
| ENT1HPC | 10 | 10 | ✓ | 50 | 50 | ✓ | 8 | 8 | ✓ | false | false | ✓ |
| ENT1HP1 | 11 | 11 | ✓ | 50 | 50 | ✓ | 20 | 20 | ✓ | false | false | ✓ |
| ENT1HP2 | 12 | 12 | ✓ | 50 | 50 | ✓ | 20 | 20 | ✓ | false | false | ✓ |
| ENT1HMO | 13 | 13 | ✓ | 50 | 50 | ✓ | 27 | 27 | ✓ | false | false | ✓ |
| ENT1OPT | 22 | 22 | ✓ | 24 | 24 | ✓ | 1 | 1 | ✓ | false | false | ✓ |
| ERRFLD | 24 | 24 | ✓ | 8 | 8 | ✓ | 40 | 40 | ✓ | true | true | ✓ |

**All 12 named-field entries match the BMS source. No mismatch found.**

---

## 4. Known discrepancies and special rules

### 4a. Postcode uppercase transformation

`lgtestc1.cbl` lines 126–127 (Add path):
```cobol
Move Function UPPER-CASE(CA-POSTCODE) TO CA-POSTCODE
```

And lines 188–189 (Update path, identical). Before calling the
business-logic layer, the COBOL presentation program converts the
postcode to uppercase. The BMS field `ENT1HPC` does not restrict
character case; the enforced uppercase is applied programmatically.
This rule is catalogued against the ENT1HPC element.

### 4b. Email BMS/COMMAREA length discrepancy

`ENT1HMO` BMS LENGTH = **27** (`ssmap.bms` line 93).
COMMAREA field `CA-EMAIL-ADDRESS` = **PIC X(100)** (100 characters).

Any email address longer than 27 characters cannot be entered on this
screen. The COBOL MOVE will silently space-pad the remaining 73
characters. No error is raised. This discrepancy is recorded in the
catalogue element for `ENT1HMO`.

### 4c. Option 3 absent

The menu-option label at row 6, col 8 (`ssmap.bms` lines 22–23) is
blank (`INITIAL='                '`). There is no `WHEN '3'` branch in
`lgtestc1.cbl`. Option slot 3 is physically present in the BMS map but
carries no text and routes to no program. This is noted in the catalogue
element with a `note` field.

---

## 5. Conclusion

**No unresolved catalogue mismatch was found.**

All 12 named fields in SSMAPC1 match the BMS source exactly (position,
length, protection attribute). The four count assertions (12 / 11 / 10 / 1)
are confirmed. The two discrepancies noted (email length and postcode
uppercase) are already documented in `catalogue/genapp.json` and in
`docs/stage1-source-review.md`. There are no blocking issues preventing
Stage 1 from being marked complete.
