# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Purpose

**Heirloom** checks whether a modernized application preserves every task, field, and visible input rule defined by the IBM CICS GenApp green-screen source. This repository contains the parity-analysis tooling, documentation, and agent-guidance files. The legacy GenApp source is available as a read-only Git submodule at `legacy/cics-genapp`.

## Critical Security Constraints

### `.gitignore` — never modify the top section
The `.gitignore` contains a clearly marked "DO NOT REMOVE OR MODIFY" block covering credentials, env files, private keys, and AI assistant session folders. Only add project-specific patterns **below** the marked boundary at line 120.

### `.bobignore` — never modify at all
Prevents Bob from logging credential-related patterns to session history. The comment says "DO NOT REMOVE OR MODIFY THESE PATTERNS." Do not touch this file.

### `bob_sessions/` folder
The `.gitignore` excludes live session files from `.copilot/`, `.cursor/`, and `.codeium/`, but the `bob_sessions/` folder is **required for project submission** — do not ignore it.

## Credential Rules (non-negotiable)
- Never hardcode credentials anywhere in source files.
- Never read or display `.env` content — participants add credentials themselves.
- Always use environment variables: `process.env.VAR` (Node.js), `os.getenv('VAR')` (Python), `System.getenv("VAR")` (Java).
- Never commit or stage `.env`; `.env.example` is the only env file tracked.
- Files containing "credential", "secret", or "password" in their name are gitignored — avoid creating them.

## Heirloom Rules

These rules govern all parity-analysis work in this repository. They apply to every agent in every mode.

1. **No manufactured gaps.** Every reported gap must come from the real GenApp source and the real modernized app. Never invent or plant a gap.
2. **Fix verification.** A fix counts only when the same parity check fails before the change and passes afterward. Preserve both results.
3. **Deterministic checks.** Use deterministic checks for field presence, numeric restrictions, maximum lengths, required rules, and submission behaviour.
4. **Model judgement scope.** Use model judgement only for semantic uncertainty. If uncertain, record "cannot determine."
5. **Plain English findings.** Write human-facing findings in plain English.
6. **Citation required.** Every finding must cite its GenApp source file and line and include modern-app evidence.
7. **Source is read-only.** The legacy system is read from SSMAP and COBOL source; it is not run.
8. **Fictional data only.** Use only IBM GenApp fictional sample records or invented test data.
9. **EPL-2.0 notices.** Retain EPL-2.0 notices for any GenApp-derived material. IBM does not endorse Heirloom.
10. **No phantom results.** Never claim a result that was not actually produced or measured.

## Files in This Repo

| File / Path | Purpose |
|-------------|---------|
| `.gitignore` | Security-first ignore rules — do not modify the protected block |
| `.bobignore` | Prevents Bob from logging credentials — do not modify |
| `.env.example` | Template for participants to copy to `.env` |
| `SECURITY.MD` | Security guidelines for hackathon participants |
| `README.md` | Quick-start instructions for participants |
| `legacy/cics-genapp` | Git submodule — IBM CICS GenApp legacy source (read-only) |
| `docs/data-sources.md` | Provenance record: GenApp URL, pinned SHA, EPL-2.0 notice |
| `docs/progress.md` | Authoritative stage tracker — Stages 1–9 |

## When Helping Participants
- Do not ask for or accept actual credentials in prompts.
- If a participant shares a `.env` value, do not echo it back.
- Guide participants to use `cp .env.example .env` and edit locally.
