# Stage 8 automated verification record

Date: 27 September 2026

## One command, published result

`python3 scripts/verify.py` runs every check and writes
[`evidence/verification.json`](../../evidence/verification.json). The record
names the commit it ran against, whether the working tree was clean, the pinned
GenApp commit, and each suite's measured pass count and duration. The landing
page reads this file; it never shows a number that was not produced by a run.
`.github/workflows/verify.yml` runs the same command on every push.

| Suite | Result | Checks |
| --- | --- | --- |
| Citations | pass | 67/67 |
| Parity | pass | 14/14 |
| Application | pass | 20/20 |
| Workflows | pass | 5/5 |
| Screens | pass | 1/1 (6 screens, 24×80 each) |
| Syntax | pass | 6/6 |
| **Total** | **pass** | **113/113** |

## New citation check

`scripts/check_citations.py` makes every published citation checkable without
judgement:

- every legacy citation in `evidence/findings.json`, and every
  `sourceEvidence` entry in the catalogue, must fall inside the pinned GenApp
  file;
- every first-pass citation must fall inside the file as it was at tag
  `stage3-first-pass`;
- every named regression check must exist in the test file it names.

A deliberately broken line range and a misnamed check were both reported as
failures before the checker was accepted.

## Defects found and fixed while automating

These are defects in the Heirloom site itself, not GenApp parity findings. The
six parity findings and the authoritative catalogue are unchanged.

1. **Every dashboard source link returned 404.** Links pointed at
   `github.com/Jennycruzy/heirloom/blob/main/legacy/cics-genapp/...`, but
   GitHub does not serve submodule files under the parent repository. Legacy
   links now open `cicsdev/cics-genapp` at the pinned commit `f6f3f4b2`; both
   URL forms were checked (404 before, 200 after) and `dashboard/test.mjs`
   now asserts the working form.
2. **Updating a missing customer returned 400 instead of 404.** Motor-policy
   updates already mapped a missing record to 404. The new check
   `test_updating_a_missing_customer_is_not_found` failed against the previous
   server (`400 != 404`) and passes after the fix.
3. **Two servers were needed to see the project locally.** The application
   server now serves the landing page, workspace, dashboard and evidence from
   one origin, through an explicit file allowlist, with security headers and
   HEAD support. New checks cover routing, private files, headers and health.

## Workspace interface

The clerk workspace moved to `/app/` and now uses a segmented task control.
The parity checker reads a radio group's values in order exactly as it read a
`<select>`'s options, and all 14 structural checks still pass against the new
markup. Every field keeps its exact name, text type and catalogue maximum
length. No confirmation step was added to motor delete, because the legacy
program deletes immediately and adding a step would itself change the
workflow.
