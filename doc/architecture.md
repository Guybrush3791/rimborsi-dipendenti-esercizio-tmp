# Architecture — `src/`

Flask web app for HR expense reimbursement. Five modules with a strict dependency order; no circular imports.

## Dependency graph

```
app.py
 ├── rules.py        (leaf — pure constants)
 ├── validator.py → rules.py
 ├── calculator.py → rules.py
 └── storage.py      (leaf — pure I/O)
```

## Module responsibilities

### `rules.py`
Regulatory parameters for two normative regimes (Circolare MEF n. 41/2024 for 2025, n. 18/2026 from 01/01/2026). **Update only this file when limits change** — everything else derives from it at runtime.

Versioned cap sets (private):
- `_MASSIMALI_2025` / `_MASSIMALI_2026` — per-diem caps by category
- `_MASSIMALE_KM_2025` / `_MASSIMALE_KM_2026` — mileage rate (€/km)
- `_MASSIMALE_NOTTE_2025` / `_MASSIMALE_NOTTE_2026` — hotel cap (€/night)
- `_PLAFOND_2025 = 1200.00` / `_PLAFOND_2026 = 1400.00` — monthly IRPEF-exemption ceiling

Public names (always point at current/2026 values — used by templates and the riepilogo route):
- `MASSIMALI_GIORNALIERI`, `MASSIMALE_KM`, `MASSIMALE_NOTTE`, `PLAFOND_MENSILE`
- `CATEGORIE_A_GIORNATE` — tuple of categories that use `giorni` as the quantity multiplier

Selector functions:
- `_caps(d: date)` — returns `(massimali, massimale_km, massimale_notte)` for the cap set applicable to date `d` (boundary: `SOGLIA_2026 = 2026-01-01`)
- `plafond_per_data(d: date)` — returns the monthly plafond for date `d`
- `plafond_per_mese(mese: str)` — convenience wrapper; `mese` is `'YYYY-MM'`

### `validator.py`
Pure function `valida(richiesta) → (bool, str)`. Returns `(True, "")` or `(False, reason)`. Checks: non-empty `dipendente`, known `categoria`, positive `importo`, valid ISO date, and that the category-specific quantity field (`giorni`/`km`/`notti`) is a positive number.

### `calculator.py`
Two pure functions, no side effects:
- `massimale_teorico(richiesta)` — parses `richiesta["data"]`, calls `rules._caps(d)` to get the date-appropriate rate set, then computes the cap: `rate × quantity`
- `calcola(richiesta, esente_gia_riconosciuta) → (quota_esente, quota_imponibile, dettaglio)` — caps the exempt portion first against the theoretical max, then against the remaining monthly cap (`rules.plafond_per_data(d) − esente_gia_riconosciuta`). The date determines which plafond applies (2025 or 2026).

### `storage.py`
All file I/O. Reads and writes `data/richieste.json`. Key helpers:
- `carica() / salva(richieste)` — full load/dump of the JSON array
- `mese(richiesta)` — extracts `YYYY-MM` from `data[:7]`
- `esente_riconosciuta_nel_mese(richieste, dipendente, mese)` — sums `quota_esente` of valid requests for the employee in that month; called before each new calculation to enforce the cap

### `app.py`
Flask routes. The core write path is `_registra(form)`:

```
form data
  → build raw dict
  → validator.valida()        # reject early if invalid
  → storage.esente_riconosciuta_nel_mese()   # current cap usage
  → calculator.calcola()      # compute exempt/taxable split
  → storage.salva()           # append and persist
```

Routes:

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Redirect to `/richieste` |
| GET/POST | `/nuova` | Submit a new request; POST renders result inline (no redirect) |
| GET | `/richieste` | List all requests; filter by `?dipendente=` and `?mese=` |
| GET | `/riepilogo` | Monthly totals per employee with cap usage % |
| GET | `/normativa` | Displays current `rules.py` constants |

## Templates & static

Jinja2 templates in `src/templates/`; `base.html` provides the shared layout. `src/static/` holds CSS and vanilla JS (no build step).
