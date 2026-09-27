# Plan Mode — Architecture Rules

This file provides guidance to agents when working with code in this repository.

## Architecture constraint
This repo contains the completed scoped Heirloom application. Any additional
architecture planned on top of it must:
- Keep all credentials in `.env` (never committed); document them in `.env.example`.
- Not create files with "credential", "secret", or "password" in the name — they are gitignored globally and will silently disappear from git tracking.
- Not create `config.json`, `config.yaml`, `config.yml`, `secrets.json`, or `database.yml` — all are gitignored by the security block.

## Security-Driven Gitignore Gaps
The `.gitignore` patterns are intentionally broad: `*token*`, `*secret*`, `*password*`, `*credentials*`. Any file whose name contains these strings will be untracked. Plan filenames accordingly.

---

## Heirloom — Architecture Constraints

- **Legacy source is read-only.** Heirloom reads GenApp COBOL and SSMAP source from `legacy/cics-genapp`. It does not run a mainframe or execute GenApp in any environment.
- **Gaps must be grounded.** Every gap must be substantiated by evidence from both `legacy/cics-genapp` source and the real modernized app. Planning a gap without that evidence is not permitted.
- **EPL-2.0 compliance.** EPL-2.0 copyright notices must be retained for any material derived from GenApp source. IBM does not endorse Heirloom.
- **Stage tracker is authoritative.** `docs/progress.md` is the only authoritative record of stage status. Do not plan or claim a stage as passed unless deterministic checks have confirmed it.
- **No real personal data.** All test and sample data must come from IBM GenApp fictional records or invented data. Never plan use of real personal or business records.
