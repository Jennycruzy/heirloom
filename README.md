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
| Legacy catalogue validation | 20/20 checks passed |
| Screen reconstruction | 6 screens, each exactly 24×80 |
| Catalogue actions | 20 visible actions: 18 program-confirmed, 2 explicitly uncertain |
| First modern application | 10 database/API/HTTP tests passed |
| Exact catalogue-to-modern comparison | 14/14 checks passed |
| Workflow-meaning review | 5 matches and 6 source-proven gaps identified before repair |

The six gaps are valuable findings, not planted defects. They concern generated
identifiers, retrieve-before-edit updates, and the customer-plus-policy key used
by motor-policy operations. The untouched first implementation is preserved at
Git tag `stage3-first-pass`; the evidence audit explains every finding before
any fix is attempted.

Start with:

- [Project progress and evidence](docs/progress.md)
- [One-page guide for judges](docs/judge-guide.md)
- [Verified legacy catalogue](catalogue/genapp.json)
- [Deterministic parity result](parity/result.json)
- [Workflow evidence audit](docs/reports/stage5-evidence-audit.md)
- [Bob review evidence](bob_sessions/heirloom_stage5_bob_final_result.jpeg)

## Run locally

Requirements: Python 3.11 and a modern browser. The application itself has no
external Python or JavaScript dependency.

```bash
python3 modern-app/seed.py
python3 modern-app/server.py --port 8080
```

Open <http://127.0.0.1:8080/>. The invented inquiry identifiers are
`CUST000001` and `POL001`.

To view the source-reconstructed screen dashboard in a second terminal:

```bash
python3 -m http.server 8000
```

Open <http://127.0.0.1:8000/dashboard/>.

## Verify

```bash
python3 parity/check.py
python3 -m unittest discover -s modern-app/tests -v
node dashboard/test.mjs
```

The Stage 1 catalogue validator additionally uses the pinned validation setup
documented under `catalogue/scripts/`; its committed result is
`catalogue/validation-result.json`.

## How AI was used

- IBM Bob performed source-oriented planning and semantic review with separate
  customer and motor-policy reviewers.
- watsonx.ai Granite supplied documented fallback drafts while Bob usage was
  reserved for evidence-heavy review.
- Deterministic scripts, source citations, browser checks, and human review
  verify generated work. Original model output and correction audits are both
  retained when a review is incomplete.

No model result is treated as proof by itself.

## Repository map

| Path | Purpose |
| --- | --- |
| `legacy/cics-genapp/` | Read-only IBM GenApp submodule pinned to a known commit |
| `catalogue/` | Source-derived screens, tasks, rules, schema, and validation result |
| `dashboard/` | Exact 24×80 legacy-screen reconstruction |
| `modern-app/` | Scoped standard-library modernization and tests |
| `parity/` | Deterministic catalogue-to-modern comparisons |
| `docs/reports/` | Human-readable findings and evidence audits |
| `bob_sessions/` | IBM Bob evidence required for the project record |
| `watsonx_sessions/` | watsonx generation and browser evidence |

## Current status

Source extraction, screen reconstruction, first implementation, deterministic
comparison, and workflow review are complete. Evidence-driven repairs, final
independent review, deployment, CI, measurements, and submission packaging are
still in progress; [docs/progress.md](docs/progress.md) is the authoritative
status record.

## Security and provenance

See [SECURITY.MD](SECURITY.MD) for credential rules and
[docs/data-sources.md](docs/data-sources.md) for the pinned GenApp source and
EPL-2.0 provenance. IBM does not endorse Heirloom.
