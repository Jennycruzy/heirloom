# Stage 3 — First modernization

Granite supplied the initial implementation outline on 2026-09-27. This
checked version replaces its guessed model with the committed catalogue data.

## Scope

- SSC1 customer: inquire, add, update (no customer delete task exists).
- SSP1 motor policy: inquire, add, delete, update.
- Python 3.11 standard library, `sqlite3`, and browser-native HTML/CSS/JS.
- Files under `modern-app/`; port 8080 so the Stage 2 dashboard can remain on 8000.
- Invented fictional seed records, labelled as such. No personal data.

## Verified data model

Customer fields: customer number (10), first name (10), last name (20), DOB
(10), house name (20), house number (4), postcode (8), home phone (20), mobile
phone (20), and email (27). Postcode is uppercased. The displayed date hint is
not treated as proven format validation.

Motor-policy fields: policy number (10), customer number (10), issue date
(10), expiry date (10), car make (20), car model (20), car value (6),
registration (7), car colour (8), CC (8), manufacture date (10), number of
accidents (6), and policy premium (6). Catalogue numeric flags are false for
these data fields, so no digits-only rule is invented. Displayed date hints
remain hints only.

## Files and batches

1. `modern-app/database.py` and `modern-app/seed.py`: schema, CRUD, reset, and
   explicitly invented deterministic records.
2. `modern-app/server.py`: static serving and JSON routes for only the seven
   confirmed tasks.
3. `modern-app/static/index.html`, `styles.css`, and `app.js`: accessible task
   UI for customer and motor policy work.
4. `modern-app/tests/`: database, API, validation, and HTTP-level tests using
   `unittest` only.
5. Run tests and manual browser checks, then commit and tag `stage3-first-pass`
   before any parity repair.

## Acceptance

- `python3 -m unittest discover -s modern-app/tests -v` passes.
- `python3 modern-app/server.py --port 8080` serves the application.
- At least one customer task and one motor-policy task work end to end.
- No field, rule, result, or seed-data provenance is claimed without evidence.

## Non-goals and risks

Endowment, house, commercial, and claim workflows are not modernized. Date
format enforcement is not invented. A later parity run may expose honest first-
pass gaps; none will be planted.
