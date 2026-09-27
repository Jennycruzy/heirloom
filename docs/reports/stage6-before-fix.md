# Stage 6 regression evidence — before repair

Date: 27 September 2026
Branch: `fix/source-proven-parity-gaps`
Baseline: first-pass implementation preserved at tag `stage3-first-pass`

## Application regression command

```sh
python3 -m unittest discover -s modern-app/tests -v
```

Result: **15 tests run; 3 failures and 2 errors.**

| Check | Pre-fix result |
| --- | --- |
| Customer Add assigns the identifier | Error: `Missing field(s): customer_number` |
| Motor Add assigns the identifier | Error: `Missing field(s): policy_number` |
| Motor inquiry requires matching customer and policy | Failed: returned 200 instead of 404 |
| Motor delete protects another customer's policy | Failed: returned 200 instead of 404 |
| Motor update uses customer and policy as its key | Failed: returned 200 instead of 404 |

The other 10 existing application checks remained passing.

## Browser workflow regression command

```sh
node modern-app/tests/test_workflows.mjs
```

Result: **failed** with `ERR_MODULE_NOT_FOUND` for
`modern-app/static/workflows.mjs`. The first-pass UI has no explicit workflow
state for system-generated identifiers or retrieve-before-edit updates.

## Evidence boundary

These failures were recorded before changing application implementation. The
tests correspond only to source-proven findings documented in
`docs/reports/stage5-evidence-audit.md`. No uncertain date, numeric,
required-field, or delete-not-found behavior is included.
