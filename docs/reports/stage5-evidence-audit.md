# Stage 5 evidence audit

Date: 27 September 2026

## Purpose

This audit preserves `stage5-bob-semantic-review.md` as Bob's original output
while checking its findings against exact source lines. Bob's SSC1 subagent
completed, but its SSP1 subagent was interrupted. No application fix is made
in this document.

The legacy application was read from source and was not run.

## Bob findings retained as confirmed

### F-02 — customer number is generated on add

Confirmed. `lgtestc1.cbl:113-138` sets `CA-CUSTOMER-NUM` to zero, calls the
add program, and displays the returned number. `lgacdb01.cbl:170-179` obtains
the next customer number before insertion. The modern add path instead
requires and stores a caller-supplied identifier (`modern-app/database.py:
159-168`).

### F-05 — customer update is inquire-first

Confirmed. `lgtestc1.cbl:148-193` inquires, populates and sends the screen,
receives the clerk's edits, and then updates. The modern UI sends PUT directly
when Update is selected (`modern-app/static/app.js:98-116`).

## Correction to F-04

The Bob report says `require_all=True` rejects blank fields. It actually
requires every field key to be present but permits blank values except for
explicit identifier constraints (`modern-app/database.py:91-131` and
`159-166`). The browser sends every field key. This is not a confirmed parity
gap and no additional required-field rule should be added.

## Completed SSP1 evidence

### F-10 — motor inquiry uses a composite identifier — confirmed gap

The legacy presentation program passes both customer and policy numbers
(`lgtestp1.cbl:68-75`). The motor query explicitly filters by both values
(`lgipdb01.cbl:563-570`). The modern inquiry filters only by policy number
(`modern-app/database.py:222-230`), and its UI disables customer number during
inquiry (`modern-app/static/app.js:81-96`).

### F-11 — policy number is generated on add — confirmed gap

The legacy Add path does not copy a clerk-entered policy number before calling
the add program (`lgtestp1.cbl:97-125`). The database insert uses `DEFAULT` for
`POLICYNUMBER`, obtains the generated identity, and returns it
(`lgapdb01.cbl:257-313`). The modern add path instead requires and stores a
caller-supplied policy number (`modern-app/database.py:209-219`).

### F-12 — motor delete uses customer and policy numbers — confirmed gap

The legacy presentation program passes both identifiers
(`lgtestp1.cbl:135-145`), and the DELETE filters by both
(`lgdpdb01.cbl:148-153` and `186-194`). The modern delete accepts only policy
number (`modern-app/database.py:251-260`), and its UI disables customer number
during delete (`modern-app/static/app.js:81-96`).

The legacy source comment and SQLCODE handling disagree about whether a missing
record is success or error (`lgdpdb01.cbl:196-202`). That specific not-found
semantic remains `cannot-determine` and must not be invented.

### F-13 — motor update uses composite identifiers and is inquire-first — confirmed gap

The legacy update first passes both identifiers to inquiry, displays the
record, receives edits, then updates (`lgtestp1.cbl:169-219`). The update
cursor filters by customer and policy numbers (`lgupdb01.cbl:126-143`). The
modern UI performs a direct PUT (`modern-app/static/app.js:128-148`); although
customer number is in its body, the database targets the record only by policy
number (`modern-app/database.py:233-248`).

## Corrected classification summary

| Classification | Items |
| --- | --- |
| Confirmed gaps | F-02, F-05, F-10, F-11, F-12, F-13 |
| Confirmed matches | F-01, F-03, F-06, F-07, F-08 |
| Cannot determine | F-09 and motor-delete missing-record semantics |
| Not a confirmed gap | F-04 required-field concern |

## Stage 6 fix boundary

Stage 6 should address only these source-proven behaviors:

1. generate customer numbers during customer add;
2. require an inquire-first customer update flow;
3. generate policy numbers during motor-policy add;
4. use both customer and policy numbers for motor inquiry, delete, and update;
5. require an inquire-first motor update flow.

Each fix must have a deterministic regression check recorded failing before
the change and passing afterward. No date, numeric, additional required-field,
or delete-not-found rule should be invented.
