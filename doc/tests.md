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
Unit tests for `calculator.massimale_teorico` and `calculator.calcola`. No I/O; all inputs constructed inline. The `richiesta()` fixture defaults to `data="2025-10-06"` so all pre-existing expectations use 2025 caps.

- `TestMassimaleTeorico` — one case per category for 2025 caps; five matching cases with `data="2026-03-01"` verifying the 2026 rate set
- `TestCalcola` — covers: amount below cap (all exempt), amount above cap (excess taxable), monthly cap partially consumed, monthly cap exhausted, `dettaglio` dict structure; plus 2026 plafond variants and transitional boundary guard:
  - `test_transitional_2025_data_usa_massimali_vecchi` — `2025-12-31` uses the 2025 cap (pasto 8.00 €)
  - `test_transitional_2026_data_usa_massimali_nuovi` — `2026-01-01` uses the 2026 cap (pasto 10.00 €)

### `test_validator.py`
Unit tests for `validator.valida`. One test per validation rule, each asserting the exact rejection string. Covers all five categories and all required fields.

### `test_app.py`
Integration tests against the Flask test client. A `client` fixture uses `monkeypatch` to redirect `storage.PERCORSO_DATI` to a `tmp_path`, so each test starts with an empty dataset and never touches `data/richieste.json`.

Key scenarios:
- Routing smoke test (all four pages return 200)
- Full write cycle: POST `/nuova` → assert HTML response + verify persisted JSON
- Rejection flow: invalid `importo` → `stato == "respinta"` in storage
- Excess-over-cap: amount above per-diem → correct `quota_imponibile`
- Monthly cap sharing: two requests in same month exhaust the 1 200 € ceiling (2025)
- List filtering by `?dipendente=`
- Summary totals on `/riepilogo`
- Regulatory values visible on `/normativa` (asserts 2026 values: 50.00, 85.00, 1400.00)
- `test_plafond_mensile_2026` — two requests in `2026-01` exhaust the 1 400 € ceiling: alloggio 8 notti → esente 1 350; pasto 8 giorni → capienza 50, imponibile 30

## What is not tested

- `storage.py` I/O (read/write to disk) — covered implicitly by `test_app.py` via monkeypatched path
- Templates / HTML rendering beyond keyword presence checks
