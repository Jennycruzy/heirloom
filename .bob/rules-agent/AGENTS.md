# Agent Mode — Coding Rules

This file provides guidance to agents when working with code in this repository.

## This Repo Has No Application Code Yet
This is a bare template. When adding application code:
- `.gitignore` already covers Node.js, Python, and Java build artifacts — no need to add standard entries.
- `.env.example` must be kept in sync with any new env vars you introduce; never put real values in it.
- Add project-specific `.gitignore` patterns only **after** the "DO NOT REMOVE ABOVE PATTERNS" comment (line 120).

## Forbidden Modifications
- Do **not** edit the protected block in `.gitignore` (lines 1–120).
- Do **not** edit `.bobignore` at all.

## Credential Safety in Generated Code
Always generate credential access via environment variables, never inline values:
```js
// Node.js
const key = process.env.IBM_CLOUD_API_KEY;
```
```python
# Python
key = os.getenv('IBM_CLOUD_API_KEY')
```
```java
// Java
String key = System.getenv("IBM_CLOUD_API_KEY");
```

---

## Heirloom — Agent Rules

These rules apply to all parity-analysis coding work in this repository.

- **Source location.** Read legacy COBOL and SSMAP source from `legacy/cics-genapp`. Never run a mainframe or execute GenApp.
- **No manufactured gaps.** Never invent or plant a gap. Every gap must come from evidence in `legacy/cics-genapp` source and the real modernized app.
- **Deterministic checks.** Use deterministic checks for field presence, numeric restrictions, maximum lengths, required rules, and submission behaviour. Do not use model judgement for these.
- **Semantic uncertainty.** Use model judgement only when the semantics of a field or rule genuinely cannot be determined from source. Record "cannot determine" explicitly when uncertain.
- **Citation required.** Every finding must cite the exact GenApp source file and line number alongside concrete modern-app evidence.
- **Fix verification.** A fix is valid only when the same parity check fails before the change and passes afterward. Preserve and record both results.
- **Plain English.** Write all human-facing findings in plain English.
- **Fictional data only.** Use only IBM GenApp fictional sample records or invented test data. Never use real personal or business data.
- **EPL-2.0 notices.** Retain EPL-2.0 copyright notices for any GenApp-derived material. IBM does not endorse Heirloom.
- **No phantom results.** Never claim a result that was not actually produced or measured.
