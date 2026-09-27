---
name: heirloom-parity-review
description: Review a modern Heirloom workflow against pinned IBM CICS GenApp source, preserving uncertainty and requiring failing-before/passing-after evidence for repairs
---

# Heirloom parity review

Use this skill when asked to compare, review, or repair a modern Heirloom
workflow against the legacy source.

1. Establish the evidence boundary.
   - Treat `catalogue/genapp.json` as the authoritative extracted catalogue.
   - Read cited COBOL and BMS files under the pinned `legacy/cics-genapp`
     submodule; never claim the mainframe was run.
   - Read `references/review-checklist.md` before classifying anything.

2. Separate exact facts from workflow meaning.
   - Use deterministic checks for operations, fields, maximum lengths, input
     types, and known required or numeric flags.
   - Use semantic judgement only for workflow sequence and meaning.
   - If the source is insufficient or contradictory, record `cannot determine`.

3. Require repair evidence.
   - Cite exact legacy and modern file lines for every finding.
   - Add a regression check that fails before changing implementation.
   - Repair only the proven difference.
   - Rerun the same check and the full relevant suites.
   - Preserve the before and after results in `docs/reports/`.

Write findings in plain language suitable for a judge. Never manufacture a gap,
invent a validation rule, alter the authoritative catalogue to make a check
pass, or present invented records as mainframe data.
