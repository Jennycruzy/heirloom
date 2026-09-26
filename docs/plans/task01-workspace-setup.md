# Workspace Preparation Plan — Heirloom Task 01

## Overview

This plan prepares the Heirloom repository workspace so that AI agents working in it understand both the inherited IBM Hackathon security constraints and the Heirloom-specific rules governing parity analysis of the IBM CICS GenApp modernization.

No application code is written. No catalogue is extracted. No credentials are added. Nothing is staged, committed, or pushed. The work is purely documentation, submodule registration, and agent-guidance files. After all changes are made, a full `git diff` and `git status` will be shown for review.

---

## Sub-Task 1 — Update root AGENTS.md

**Intent**  
Retain every existing template security rule verbatim and append a new "Heirloom Rules" section that governs how agents must behave when performing parity analysis. Update the Purpose section to describe Heirloom's mission rather than a generic hackathon template.

**Expected Outcomes**  
- All existing credential and `.gitignore`/`.bobignore` rules are preserved word-for-word.  
- A new `## Heirloom Rules` section exists containing all ten parity-analysis rules from the task brief.  
- The "Purpose" section describes Heirloom.  
- The "Files in This Repo" table gains rows for `legacy/cics-genapp`, `docs/data-sources.md`, and `docs/progress.md`.

**Todo List**  
- [ ] Replace the Purpose paragraph to describe Heirloom's mission.  
- [ ] Add a `## Heirloom Rules` section with all ten parity-analysis rules.  
- [ ] Extend the file table with the three new paths.

**Relevant Context**  
- [`AGENTS.md`](AGENTS.md) — current file, lines 1–40.

**Status** — `[ ] pending`

---

## Sub-Task 2 — Add legacy/cics-genapp Git submodule

**Intent**  
Register the IBM CICS GenApp repository as a Git submodule at `legacy/cics-genapp`. This makes the legacy COBOL/SSMAP source available locally for agents and tools without copying files into the repo itself. The parent repository's gitlink entry pins the exact submodule commit; `.gitmodules` records only the path and URL.

**Expected Outcomes**  
- `.gitmodules` contains an entry with `path = legacy/cics-genapp` and `url = https://github.com/cicsdev/cics-genapp.git`.  
- The parent repo's gitlink object pins the submodule at the HEAD commit at add-time.  
- Running `git submodule update --init` reproducibly checks out that exact commit.  
- The exact pinned commit SHA is captured (via `git submodule status`) for use in Sub-Task 3.

**Todo List**  
- [ ] Run: `git submodule add https://github.com/cicsdev/cics-genapp.git legacy/cics-genapp`  
- [ ] Run: `git submodule status legacy/cics-genapp` to capture the exact pinned commit SHA for `docs/data-sources.md`.

**Relevant Context**  
- No existing `.gitmodules` file.  
- The gitlink (not `.gitmodules`) is what pins the submodule to a specific commit. `.gitmodules` only stores path and URL.  
- The `legacy/` prefix keeps the submodule clearly separate from `src/`, `docs/`, and `bob_sessions/`.

**Status** — `[ ] pending`

---

## Sub-Task 3 — Create docs/data-sources.md

**Intent**  
Provide a single authoritative provenance record: where the legacy source comes from, what license it carries, and what Heirloom does (and does not) do with it. Every future finding citation depends on this document.

**Expected Outcomes**  
- File exists at `docs/data-sources.md`.  
- Contains all five required items:
  1. GenApp repository URL (`https://github.com/cicsdev/cics-genapp`).
  2. The exact pinned gitlink commit SHA (filled in from Sub-Task 2 output).
  3. A concise EPL-2.0 notice — states that IBM CICS GenApp is licensed under the Eclipse Public License 2.0, links to `https://www.eclipse.org/legal/epl-2.0/`, and points to the upstream licence file in the submodule. Does **not** copy the full licence text and does **not** imply IBM endorses Heirloom.
  4. A statement that GenApp sample records are IBM fictional data and must not be treated as real personal or business records.
  5. A statement that Heirloom reads GenApp source files and does not run a mainframe.

**Todo List**  
- [ ] Create the `docs/` directory.  
- [ ] Write `docs/data-sources.md` with the five items above, inserting the SHA captured in Sub-Task 2.

**Relevant Context**  
- Sub-Task 3 depends on Sub-Task 2 (needs the pinned SHA).  
- EPL-2.0 licence file in the submodule will be at `legacy/cics-genapp/LICENSE` once checked out.

**Status** — `[ ] pending`

---

## Sub-Task 4 — Create docs/progress.md

**Intent**  
Establish an honest, auditable progress tracker for the nine Heirloom stages. All stages begin as "Not started." No stage may be marked passed until a deterministic check has actually been run and recorded. Task 01 is not marked complete here.

**Expected Outcomes**  
- File exists at `docs/progress.md`.  
- Contains exactly nine stage headings with the names below, each followed by "Not started."  
- No stage claims any result.

**Stage names (exact):**

| Heading | Name |
|---------|------|
| Stage 1 | Read the old system |
| Stage 2 | Show the old screens |
| Stage 3 | Modernize (first pass) |
| Stage 4 | The certain layer |
| Stage 5 | The judgement layer and parallel subagents |
| Stage 6 | The fix loop and the pull request |
| Stage 7 | The dashboard and hosting |
| Stage 8 | CI and measurement |
| Stage 9 | Submission |

**Todo List**  
- [ ] Write `docs/progress.md` with the nine stage headings (exact names above) and "Not started." under each.

**Status** — `[ ] pending`

---

## Sub-Task 5 — Create bob_sessions/.gitkeep

**Intent**  
Ensure the `bob_sessions/` directory is tracked by Git (required for project submission) even though it contains no session exports yet.

**Expected Outcomes**  
- `bob_sessions/.gitkeep` exists as an empty file.  
- `git status` shows it as an untracked new file (not ignored).

**Todo List**  
- [ ] Create `bob_sessions/` directory.  
- [ ] Create empty `bob_sessions/.gitkeep`.

**Relevant Context**  
- [`AGENTS.md` line 18](AGENTS.md) — existing rule that `bob_sessions/` must not be gitignored.  
- `.gitignore` does not ignore `bob_sessions/`; no `.gitignore` changes are needed.

**Status** — `[ ] pending`

---

## Sub-Task 6 — Update mode-specific AGENTS.md files

**Intent**  
Append Heirloom-specific sections to each Bob mode file where relevant, while preserving all existing template security content verbatim.

**Expected Outcomes**

`.bob/rules-agent/AGENTS.md`:  
- All existing content retained unchanged.  
- New `## Heirloom — Agent Rules` section added, covering:
  - Read legacy source (COBOL, SSMAP) from `legacy/cics-genapp`; never run a mainframe.
  - Never manufacture or plant a gap; every gap must come from real source evidence.
  - Use deterministic checks for field presence, numeric restrictions, maximum lengths, required rules, and submission behaviour.
  - Use model judgement only for semantic uncertainty; record "cannot determine" when uncertain.
  - Always cite the GenApp source file and line number alongside modern-app evidence.
  - A fix is valid only when the same parity check fails before the change and passes afterward; preserve both results.
  - Write human-facing findings in plain English.
  - Use only IBM GenApp fictional sample records or invented test data; never real personal data.
  - Retain EPL-2.0 notices for any GenApp-derived material.
  - Never claim a result that was not actually produced or measured.

`.bob/rules-ask/AGENTS.md`:  
- All existing content retained unchanged.  
- New `## Heirloom — Context` section added, covering:
  - What Heirloom is and where GenApp source lives (`legacy/cics-genapp`).
  - `docs/data-sources.md` is the authoritative provenance record.
  - Findings must be written in plain English.
  - GenApp sample records are IBM fictional data.

`.bob/rules-plan/AGENTS.md`:  
- All existing content retained unchanged.  
- New `## Heirloom — Architecture Constraints` section added, covering:
  - The legacy source is read-only; Heirloom does not run a mainframe.
  - Gaps must be grounded in both `legacy/cics-genapp` source and the real modern app.
  - EPL-2.0 notices must be preserved for GenApp-derived material.
  - `docs/progress.md` is the only authoritative stage tracker; do not claim a stage passed unless deterministic checks confirm it.
  - IBM does not endorse Heirloom.

**Todo List**  
- [ ] Append `## Heirloom — Agent Rules` section to `.bob/rules-agent/AGENTS.md`.  
- [ ] Append `## Heirloom — Context` section to `.bob/rules-ask/AGENTS.md`.  
- [ ] Append `## Heirloom — Architecture Constraints` section to `.bob/rules-plan/AGENTS.md`.

**Relevant Context**  
- [`.bob/rules-agent/AGENTS.md`](.bob/rules-agent/AGENTS.md) — lines 1–29  
- [`.bob/rules-ask/AGENTS.md`](.bob/rules-ask/AGENTS.md) — lines 1–13  
- [`.bob/rules-plan/AGENTS.md`](.bob/rules-plan/AGENTS.md) — lines 1–13

**Status** — `[ ] pending`

---

## Execution Order

Sub-Task 2 must run before Sub-Task 3 (SHA dependency). All other sub-tasks are independent of each other.

```
Sub-Task 2  (git submodule add → capture SHA)
    └─→  Sub-Task 3  (docs/data-sources.md — needs SHA)
Sub-Task 1  (root AGENTS.md — independent)
Sub-Task 4  (docs/progress.md — independent)
Sub-Task 5  (bob_sessions/.gitkeep — independent)
Sub-Task 6  (mode-specific AGENTS.md files — independent)
```

After all sub-tasks complete: show `git diff` and `git status` in full. Do not stage, commit, or push.

---

## Files Changed / Created

| Path | Action | Note |
|------|--------|------|
| `AGENTS.md` | Updated | Purpose updated + Heirloom Rules section + file table extended |
| `.gitmodules` | Created | Records submodule path and URL only |
| `legacy/cics-genapp` | Created | Git submodule; pinned commit recorded by parent gitlink |
| `docs/data-sources.md` | Created | URL, gitlink SHA, EPL-2.0 notice, fictional data, no-mainframe |
| `docs/progress.md` | Created | Stages 1–9 with exact names, all "Not started." |
| `bob_sessions/.gitkeep` | Created | Empty file to track the directory |
| `.bob/rules-agent/AGENTS.md` | Updated | Heirloom section appended |
| `.bob/rules-ask/AGENTS.md` | Updated | Heirloom section appended |
| `.bob/rules-plan/AGENTS.md` | Updated | Heirloom section appended |

**Files NOT changed:** `.gitignore`, `.bobignore`, `SECURITY.MD`, `README.md`

---

## Commands to Be Run

```bash
# Sub-Task 2 — register submodule
git submodule add https://github.com/cicsdev/cics-genapp.git legacy/cics-genapp

# Sub-Task 2 — capture pinned commit SHA for docs/data-sources.md
git submodule status legacy/cics-genapp

# After all sub-tasks — review only, no staging or committing
git diff
git status
```

No other shell commands are needed. All remaining work is file creation and editing.
