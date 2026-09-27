# Heirloom

> The tests pass. Can the clerk still do their job?

Heirloom is an evidence-driven modernization checker for IBM CICS GenApp. It
reconstructs legacy green screens from source, builds a deliberately small
modern replacement, and then checks whether the replacement preserves the
tasks and workflow meaning—not merely whether its code passes tests.

## Why it matters

A modernization can be technically healthy and still change the business
process. A field can disappear, an identifier can become clerk-entered instead
of system-generated, or an update can skip the legacy retrieve-before-edit
sequence. Conventional unit tests often miss those changes.

Heirloom makes the comparison reviewable:

1. read the pinned GenApp BMS and COBOL source;
2. record screens, fields, actions, rules, and uncertainty in a catalogue;
3. reconstruct the 24×80 screens from that catalogue;
4. implement a scoped modern application;
5. compare exact facts with deterministic checks;
6. use model judgement only for workflow meaning that cannot be reduced to a
   field or length comparison;
7. require source citations and a failing-before/passing-after test for every
   repair.

The legacy application was not run. All legacy claims come from the pinned
source. Modern test records are invented and clearly labelled.

## What is implemented

The modern application covers seven source-confirmed tasks:

- Customer: inquire, add, and update.
- Motor policy: inquire, add, delete, and update.

Customer deletion is intentionally absent because the verified SSC1 workflow
does not expose it. Endowment, house, commercial, and claim workflows are not
part of the modernization scope.

## Evidence at a glance

| Evidence | Measured result |
| --- | --- |
| Workflow differences found before repair | **6 source-proven gaps**: generated identifiers, retrieve-before-edit updates, and composite policy identification |
| First implementation, before review | **10/10** application checks and **14/14** structural parity checks passed, with all six gaps present |
| Repaired application at the review | **15/15** database, API, HTTP, and workflow checks passed |
| Independent final Bob review | **READY** — all six repairs confirmed against cited source and modern code |
| Legacy catalogue validation | 20/20 checks passed |
| Screen reconstruction | 6 screens, each exactly 24×80 |
| Catalogue actions | 20 visible actions: 18 program-confirmed, 2 explicitly uncertain |
| Exact catalogue-to-modern comparison | 14/14 checks passed |
| Current full verification | **118/118** across six suites, including 67 resolved source citations ([record](evidence/verification.json)) |

The six gaps are valuable findings, not planted defects. They concern generated
identifiers, retrieve-before-edit updates, and the customer-plus-policy key used
by motor-policy operations. The untouched first implementation is preserved at
Git tag `stage3-first-pass`; the evidence audit explains every finding before
any fix is attempted.

Start with:

- [Live judge site](https://heirloom.54-154-121-30.sslip.io/)
- [Live clerk workspace](https://heirloom.54-154-121-30.sslip.io/app/)
- [Live reconstructed legacy screens](https://heirloom.54-154-121-30.sslip.io/dashboard/)
- [Findings with citations](evidence/findings.json)
- [Project progress and evidence](docs/progress.md)
- [One-page guide for judges](docs/judge-guide.md)
- [Verified legacy catalogue](catalogue/genapp.json)
- [Deterministic parity result](parity/result.json)
- [Workflow evidence audit](docs/reports/stage5-evidence-audit.md)
- [Final Bob review](docs/reports/stage6-bob-final-review.md)
- [Bob READY evidence](bob_sessions/jenny_builds_task06_final_repair_review.png)

## Run locally

Requirements: Python 3.11+ and a modern browser; Node.js 18+ only for the
browser-module tests. The application has no external Python or JavaScript
dependency.

```bash
git clone --recurse-submodules https://github.com/Jennycruzy/heirloom.git
cd heirloom
python3 modern-app/seed.py
python3 modern-app/server.py --port 8080
```

One server provides everything from a single origin:

| URL | What it shows |
| --- | --- |
| <http://127.0.0.1:8080/> | Overview: the question, the result, and the way into each section |
| <http://127.0.0.1:8080/findings/> | The six findings, each with legacy, first-pass and regression-check citations |
| <http://127.0.0.1:8080/method/> | The seven steps and who decides what: scripts, models or people |
| <http://127.0.0.1:8080/verification/> | The latest measured result of every check |
| <http://127.0.0.1:8080/dashboard/> | All six GenApp maps rebuilt on a 24×80 grid, with a field inspector |
| <http://127.0.0.1:8080/app/> | The repaired clerk workspace with a live legacy trace |

The invented identifiers are customers `CUST000001` and `CUST000002`, and
policy `POL001` held by `CUST000001`. Try
`/app/#motor/inquire/POL001/CUST000002`: the policy belongs to another
customer, so it is not found (finding F-10).

## Verify

```bash
python3 scripts/verify.py
```

This runs every check and publishes the measured result to
[`evidence/verification.json`](evidence/verification.json), which the
[verification page](https://heirloom.54-154-121-30.sslip.io/verification/)
reads. The record names the commit it ran against and whether the working tree
was clean. The same command runs on CircleCI for every push
(`.circleci/config.yml`).

| Suite | What it proves |
| --- | --- |
| Citations | Every legacy, first-pass and regression-check citation in `evidence/findings.json` and every catalogue source reference resolves to real lines |
| Parity | Catalogue operations, fields, lengths and numeric flags equal the modern database and browser form (no model) |
| Application | Database, validation, API, HTTP routing, file allowlist and security-header checks |
| Workflows | Generated identifiers and retrieve-before-edit rules in the browser workflow |
| Screens | Every catalogue screen composes to an exact 24×80 grid |
| Syntax | Every browser JavaScript module parses |

Individual suites can still be run directly (`python3 parity/check.py`,
`python3 -m unittest discover -s modern-app/tests -v`,
`node dashboard/test.mjs`, `node modern-app/tests/test_workflows.mjs`). The
Stage 1 catalogue validator additionally uses the pinned validation setup
documented under `catalogue/scripts/`; its committed result is
`catalogue/validation-result.json`.

## How AI was used

- IBM Bob performed source-oriented planning, launched separate customer and
  motor-policy semantic reviewers, and independently reviewed the repaired
  branch against cited COBOL, tests, and browser evidence before returning
  `READY`.
- watsonx.ai Granite supplied documented fallback drafts while Bob usage was
  reserved for evidence-heavy review.
- Deterministic scripts, source citations, browser checks, and human review
  verify generated work. Original model output and correction audits are both
  retained when a review is incomplete.

No model result is treated as proof by itself.

## IBM Bob workspace configuration

The repository includes project rules for Bob's Agent, Ask, and Plan modes,
plus a reusable `heirloom-parity-review` Skill and a restricted
`Heirloom Evidence Reviewer` custom mode. The Skill encodes the evidence,
uncertainty, citation, and failing-before/passing-after workflow used by the
project. These reusable additions document the workflow for future reviews;
they are not claimed as retroactive evidence for earlier sessions.

- [Parity-review Skill](.bob/skills/heirloom-parity-review/SKILL.md)
- [Custom review mode](.bob/custom_modes.yaml)
- [Submission-ready Bob PNG manifest](bob_sessions/README.md)

## Repository map

| Path | Purpose |
| --- | --- |
| `legacy/cics-genapp/` | Read-only IBM GenApp submodule pinned to a known commit |
| `catalogue/` | Source-derived screens, tasks, rules, schema, and validation result |
| `evidence/` | Machine-readable findings with citations, and the published verification record |
| `site/` | Overview, Findings, Method and Verification pages, and the shared design system (IBM Plex, OFL) |
| `dashboard/` | Exact 24×80 legacy-screen reconstruction and field inspector |
| `modern-app/` | Scoped standard-library modernization, site server, and tests |
| `parity/` | Deterministic catalogue-to-modern comparisons |
| `scripts/` | One-command verification and citation checks |
| `deploy/` | systemd unit and Nginx site for the public deployment |
| `docs/reports/` | Human-readable findings and evidence audits |
| `bob_sessions/` | IBM Bob evidence required for the project record |
| `watsonx_sessions/` | watsonx generation and browser evidence |

## Current status

Source extraction, screen reconstruction, first implementation, deterministic
comparison, evidence-driven repairs, human browser checks, Bob's final
independent review, the HTTPS judge deployment, and automated verification
with published results are complete. The LabLab project was submitted by the
solo team Jenny Builds before submissions closed;
[docs/progress.md](docs/progress.md) is the authoritative status record.

## Security and provenance

See [SECURITY.MD](SECURITY.MD) for credential rules and
[docs/data-sources.md](docs/data-sources.md) for the pinned GenApp source and
EPL-2.0 provenance. IBM does not endorse Heirloom.
