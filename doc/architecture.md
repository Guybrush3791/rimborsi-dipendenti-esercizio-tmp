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
Pure constants. Single source of truth for all regulatory parameters (Circolare MEF n. 41/2024). **Update only this file when limits change** — everything else derives from it at runtime.

Key values:
- `MASSIMALI_GIORNALIERI` — per-diem caps by category (€/day)
- `MASSIMALE_KM = 0.42` — mileage rate (€/km)
- `MASSIMALE_NOTTE = 150.00` — hotel cap (€/night)
- `PLAFOND_MENSILE = 1200.00` — monthly IRPEF-exemption ceiling per employee
- `CATEGORIE_A_GIORNATE` — tuple of categories that use `giorni` as the quantity multiplier

### `validator.py`
Pure function `valida(richiesta) → (bool, str)`. Returns `(True, "")` or `(False, reason)`. Checks: non-empty `dipendente`, known `categoria`, positive `importo`, valid ISO date, and that the category-specific quantity field (`giorni`/`km`/`notti`) is a positive number.

### `calculator.py`
Two pure functions, no side effects:
- `massimale_teorico(richiesta)` — computes the regulatory cap: `rate × quantity`
- `calcola(richiesta, esente_gia_riconosciuta) → (quota_esente, quota_imponibile, dettaglio)` — caps the exempt portion first against the theoretical max, then against the remaining monthly cap (`PLAFOND_MENSILE − esente_gia_riconosciuta`)

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
