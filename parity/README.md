# Deterministic parity checks

This checker compares verified SSC1 and SSP1 catalogue facts with the modern
data model and browser form. A task list may be a `<select>` or a radio group;
either way its values must equal the confirmed operations, in order. It does
not use model judgement and does not modify the catalogue.

Run from the repository root:

```sh
python3 parity/check.py
```

The command checks:

- confirmed task operations;
- BMS-to-modern field mappings;
- exact field sets and maximum lengths;
- catalogue numeric flags;
- browser input names, types, and maximum lengths.

The machine-readable result is written to `parity/result.json`. Application
behavior is independently covered by `modern-app/tests/test_modern_app.py`.

The mapping file contains explicit modern names for the legacy BMS inputs. The
lengths and numeric flags are always read from the authoritative catalogue,
not duplicated in the checker.
