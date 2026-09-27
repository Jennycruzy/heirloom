# Legacy screen dashboard

Rebuilds every IBM CICS GenApp BMS map from the committed
`catalogue/genapp.json` onto an exact 24×80 grid. The legacy application is
read from source; no mainframe is run.

- Screen tabs for all six maps; SSC1 and SSP1 are marked as modernized.
- A field inspector: hover or click any field for its BMS name, role,
  position, length, attributes and the `ssmap.bms` line that defines it.
- Every action on the screen, with its confirmed or cannot-determine status,
  presentation and business programs, and source evidence.
- Source links open the file in `cicsdev/cics-genapp` at the pinned commit.
  (Files inside a submodule are not browsable under this repository's URL.)
- Deep links: `/dashboard/#SSMAPP1/T-SSP1-4` opens a screen and action.

## Run

The dashboard is served by the application server with the rest of the site:

```sh
python3 modern-app/server.py --port 8080
```

Open <http://127.0.0.1:8080/dashboard/>.

## Test

```sh
node dashboard/test.mjs
```

The test checks the verified catalogue counts, every 24×80 composition, final
cell ownership, cursor attributes, literal placement, source-link URLs, SSP5's
cannot-determine status, and that the catalogue's modern parity field remains
`not-assessed` (the catalogue records the legacy source only).
