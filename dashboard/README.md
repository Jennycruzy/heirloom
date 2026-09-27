# Heirloom Stage 2 dashboard

This dashboard reconstructs IBM CICS GenApp screens from the committed
`catalogue/genapp.json`. The legacy application is read from source; no
mainframe is run.

## Run

From the repository root:

```sh
python3 -m http.server 8000
```

Open <http://localhost:8000/dashboard/>.

## Test

From the repository root:

```sh
node dashboard/test.mjs
```

The test checks the verified Stage 1 counts, every 24×80 composition, final
cell ownership, cursor attributes, literal placement, evidence URLs, SSP5's
cannot-determine status, and that modern parity remains not assessed.

## Current scope

Stage 2 proves source extraction and screen reconstruction only. Modernization
and browser parity checks have not yet been implemented, so this dashboard does
not show modern-app pass or fail results.
