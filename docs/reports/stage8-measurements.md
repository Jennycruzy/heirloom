# Stage 8 observed evidence-retrieval measurement

Date: 27 September 2026

## Question measured

Identify the four actions available on the legacy SSP1 motor-policy screen.

The manual path used VS Code search in
`legacy/cics-genapp/base/src/ssmap.bms`. The Heirloom path used the public
source-reconstruction dashboard's Screen and Task selectors.

## Results

| Attempt | Manual source review | Heirloom dashboard | Difference |
| --- | ---: | ---: | ---: |
| Initial attempt | 2:00 | 2:00 | 0:00 |
| Controlled retry | 0:50 | 0:30 | 0:20 faster with Heirloom |

On the controlled retry, the dashboard reduced observed lookup time from 50
seconds to 30 seconds: a 20-second or 40% reduction.

## Honest boundary

This is one participant performing a small, informal lookup twice, not a
scientific productivity study. The initial attempt included additional
navigation and familiarity effects and showed no difference. The controlled
retry excluded setup time but still benefits from prior exposure to the task.
The project therefore reports this only as an observed demonstration, not a
general claim that Heirloom makes every modernization review 40% faster.

The stronger measured project outcome is independent of timing: Heirloom found
six source-proven workflow differences in a seven-task modernization after the
first implementation had already passed ten application checks and all fourteen
structural parity checks.
