Stop all subagents and make no further tool calls. Use only the evidence and
findings already collected in this session. Do not restart either review and do
not inspect additional files.

Discard every proposed change except the single required deliverable. Create
only `docs/reports/stage5-bob-semantic-review.md`, following the original
classification and citation requirements. Do not modify application code,
tests, catalogue files, parity files, configuration, or documentation other
than that one report. Do not commit or push.

If a task lacks enough collected evidence, classify it `cannot-determine`
rather than doing more research. Finish the report now and return a concise
summary with the classification counts and Stage 6 recommendation.
