# Test suite — `tests/`

pytest. No external dependencies beyond `requirements.txt`. Run with:

```bash
pytest                          # all tests
pytest tests/test_calculator.py # single file
pytest tests/test_calculator.py::TestCalcola::test_plafond_incapiente_limita_la_quota_esente
```

`pyproject.toml` sets `pythonpath = ["."]` so `src.*` imports resolve from the project root.

## Files

### `test_calculator.py`
Unit tests for `calculator.massimale_teorico` and `calculator.calcola`. No I/O; all inputs constructed inline.

- `TestMassimaleTeorico` — one case per category, verifying the rate × quantity formula and rounding
- `TestCalcola` — covers: amount below cap (all exempt), amount above cap (excess taxable), monthly cap partially consumed (cap limits exempt portion), monthly cap exhausted (all taxable), and `dettaglio` dict structure

### `test_validator.py`
Unit tests for `validator.valida`. One test per validation rule, each asserting the exact rejection string. Covers all five categories and all required fields.

### `test_app.py`
Integration tests against the Flask test client. A `client` fixture uses `monkeypatch` to redirect `storage.PERCORSO_DATI` to a `tmp_path`, so each test starts with an empty dataset and never touches `data/richieste.json`.

Key scenarios:
- Routing smoke test (all four pages return 200)
- Full write cycle: POST `/nuova` → assert HTML response + verify persisted JSON
- Rejection flow: invalid `importo` → `stato == "respinta"` in storage
- Excess-over-cap: amount above per-diem → correct `quota_imponibile`
- Monthly cap sharing: two requests in same month exhaust the 1 200 € ceiling
- List filtering by `?dipendente=`
- Summary totals on `/riepilogo`
- Regulatory values visible on `/normativa`

## What is not tested

- `storage.py` I/O (read/write to disk) — covered implicitly by `test_app.py` via monkeypatched path
- Templates / HTML rendering beyond keyword presence checks
