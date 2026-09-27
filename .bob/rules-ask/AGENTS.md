# Ask Mode — Documentation Context

This file provides guidance to agents when working with code in this repository.

## Repo Context
- This repository contains the runnable Heirloom application, dashboard,
  catalogue, parity tooling, deployment files, and standard-library tests.
- The primary documentation is `SECURITY.MD` (note: uppercase `.MD` extension).
- `README.md` targets hackathon participants; `SECURITY.MD` has the definitive credential rules.

## Key Non-Obvious Structure Detail
- `.bobignore` mirrors `.gitignore` patterns but serves a different purpose: it tells Bob not to log matching content to session history. The two files are intentionally separate and both must be maintained.
- `bob_sessions/` is deliberately **not** in `.gitignore` because exported session reports are required for project submission — only live session files from other AI tools are excluded.

---

## Heirloom — Context

- **What Heirloom is.** Heirloom checks whether a modernized application preserves every task, field, and visible input rule defined by the IBM CICS GenApp green-screen source.
- **Where to find GenApp source.** The legacy COBOL and SSMAP source is in the Git submodule at `legacy/cics-genapp`.
- **Provenance record.** `docs/data-sources.md` is the authoritative record of the GenApp repository URL, the pinned gitlink commit SHA, and the EPL-2.0 licence notice.
- **Findings language.** All human-facing findings must be written in plain English.
- **Sample data.** GenApp customer, policy, and commercial records are IBM fictional sample data — they do not represent real persons or businesses.
- **IBM endorsement.** IBM does not endorse Heirloom.
