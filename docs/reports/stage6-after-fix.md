# Stage 6 regression evidence — after repair

Date: 27 September 2026  
Branch: `fix/source-proven-parity-gaps`  
Preserved baseline: tag `stage3-first-pass` at commit `d666438`

## Repairs made

Only the six source-proven workflow differences from the Stage 5 evidence
audit were repaired:

1. Customer Add now receives its customer number from the application.
2. Customer Update loads the existing record before fields can be edited.
3. Motor-policy Add now receives its policy number from the application.
4. Motor inquiry identifies a record with customer number and policy number.
5. Motor Update uses both identifiers and loads the record before editing.
6. Motor Delete uses both identifiers.

The familiar invented fixtures `CUST000001`, `CUST000002`, `POL001`, and
`POL002` remain deterministic seed data. Their fixture-only insertion path is
separate from the live Add operations.

## Automated application and API checks

```sh
python3 -m unittest discover -s modern-app/tests -v
```

Result: **15 tests run; 15 passed.**

This includes generated identifiers, retrieve-before-edit support, composite
motor-policy identification, validation, database operations, HTTP routes,
and full customer and policy lifecycles.

## Browser workflow checks

```sh
node modern-app/tests/test_workflows.mjs
```

Result: **passed.** Add hides the generated identifier from clerk entry;
customer and policy updates have separate load and edit steps; motor inquiry
and delete require both identifiers.

## Catalogue parity checks

```sh
python3 parity/check.py
```

Result: **14/14 passed.** The repairs did not alter the authoritative catalogue,
task set, field set, input types, or verified maximum lengths.

## Syntax and repository checks

Python compilation, JavaScript syntax checks, and `git diff --check` all
completed successfully.

## Human browser confirmation

All three repaired browser behaviors were confirmed by a person:

- Customer Update loaded `CUST000001` before enabling editable fields.
- Motor Update loaded `POL001` only with customer `CUST000001`, then enabled
  editable fields while keeping the policy number locked.
- Customer Add kept the customer-number field locked and returned the
  application-assigned number `0000000001`.

Evidence:

- [`heirloom_stage6_customer_update_load.jpeg`](../../browser_evidence/heirloom_stage6_customer_update_load.jpeg)
- [`heirloom_stage6_motor_update_load.jpeg`](../../browser_evidence/heirloom_stage6_motor_update_load.jpeg)
- [`heirloom_stage6_generated_customer_number.jpeg`](../../browser_evidence/heirloom_stage6_generated_customer_number.jpeg)

## Remaining review

The automated repair and human browser confirmation are complete. Stage 6 is
not marked complete until the final focused Bob review is recorded.
