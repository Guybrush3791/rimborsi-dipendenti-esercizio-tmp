# Plan: Apply Circolare MEF 18/2026 – Change 1 (updated caps + monthly plafond)

## Context

`src/rules.py` currently holds a single flat set of 2025 constants (Circolare MEF n. 41/2024).
Circolare MEF n. 18/2026 raises all daily caps and the monthly plafond starting 01/01/2026.
The transitional regime requires cap selection based on the request's `data` field (date incurred),
not submission date. This plan makes the calculator date-aware while keeping the 2025 paths intact
for backward compatibility.

Scope: Section 2 only — updated caps and plafond. Sections 3–5 are out of scope.

## New values

| Constant            | 2025 (MEF 41/2024) | 2026 (MEF 18/2026) |
|---------------------|---------------------|---------------------|
| trasferta_italia    | 46.48 €/day         | 50.00 €/day         |
| trasferta_estero    | 77.47 €/day         | 85.00 €/day         |
| pasto               | 8.00 €/day          | 10.00 €/day         |
| chilometrico        | 0.42 €/km           | 0.45 €/km           |
| alloggio            | 150.00 €/night      | 170.00 €/night      |
| monthly plafond     | 1 200.00 €          | 1 400.00 €          |

## Data flow

```
richiesta["data"]  ──►  date.fromisoformat()  ──►  _caps(d) / plafond_per_data(d)
                                                          │
                                              ┌───────────┴───────────┐
                                         d < 2026-01-01         d >= 2026-01-01
                                         2025 cap set            2026 cap set
                                              │                        │
                              massimale_teorico()              massimale_teorico()
                              calcola()                        calcola()
                                              │
                                    riepilogo route
                              plafond_per_mese(mese) ──► percentuale_plafond
```

## Changes

### 1. `src/rules.py`

Add versioned cap sets and two selector functions. Keep the existing flat names pointing at 2026
values so templates and the riepilogo route continue to work without changes.

```python
from datetime import date

SOGLIA_2026 = date(2026, 1, 1)

_MASSIMALI_2025      = {"trasferta_italia": 46.48, "trasferta_estero": 77.47, "pasto": 8.00}
_MASSIMALE_KM_2025   = 0.42
_MASSIMALE_NOTTE_2025 = 150.00
_PLAFOND_2025        = 1200.00

_MASSIMALI_2026      = {"trasferta_italia": 50.00, "trasferta_estero": 85.00, "pasto": 10.00}
_MASSIMALE_KM_2026   = 0.45
_MASSIMALE_NOTTE_2026 = 170.00
_PLAFOND_2026        = 1400.00

# Public names used by templates and riepilogo route (always current/2026 values)
MASSIMALI_GIORNALIERI = _MASSIMALI_2026
MASSIMALE_KM          = _MASSIMALE_KM_2026
MASSIMALE_NOTTE       = _MASSIMALE_NOTTE_2026
PLAFOND_MENSILE       = _PLAFOND_2026

def _caps(d: date):
    if d >= SOGLIA_2026:
        return _MASSIMALI_2026, _MASSIMALE_KM_2026, _MASSIMALE_NOTTE_2026
    return _MASSIMALI_2025, _MASSIMALE_KM_2025, _MASSIMALE_NOTTE_2025

def plafond_per_data(d: date) -> float:
    return _PLAFOND_2026 if d >= SOGLIA_2026 else _PLAFOND_2025

def plafond_per_mese(mese: str) -> float:
    """mese is 'YYYY-MM'."""
    return plafond_per_data(date.fromisoformat(mese + "-01"))
```

Also update `RIFERIMENTO_NORMATIVO` to:
```python
RIFERIMENTO_NORMATIVO = "Circolare MEF n. 41/2024 (fino al 31/12/2025) e n. 18/2026 (dal 01/01/2026)"
```

### 2. `src/calculator.py`

Parse `richiesta["data"]` in both functions; use `rules._caps()` and `rules.plafond_per_data()`
instead of the flat module constants. No change to public signatures.

`massimale_teorico(richiesta)`:
```python
from datetime import date as _date
d = _date.fromisoformat(richiesta["data"])
massimali, massimale_km, massimale_notte = rules._caps(d)
# then use massimali[categoria], massimale_km, massimale_notte
# instead of rules.MASSIMALI_GIORNALIERI, rules.MASSIMALE_KM, rules.MASSIMALE_NOTTE
```

`calcola(richiesta, esente_gia_riconosciuta)`:
```python
d = _date.fromisoformat(richiesta["data"])
plafond = rules.plafond_per_data(d)
capienza = max(plafond - esente_gia_riconosciuta, 0.0)
```

### 3. `src/app.py` — riepilogo route only

Replace the `percentuale_plafond` line (currently line 120–122):
```python
# before
"percentuale_plafond": min(round(dati["esente"] / rules.PLAFOND_MENSILE * 100), 100),
# after
"percentuale_plafond": min(round(dati["esente"] / rules.plafond_per_mese(mese) * 100), 100),
```

The `plafond` passed to the template header stays `rules.PLAFOND_MENSILE` (always the 2026 value,
which is what the display note should show).

### 4. `src/templates/normativa.html`

Extend the source note (line 5) to mention effective date and transitional regime:
```html
<p class="nota">Parametri applicati dal sistema. Fonte: {{ rules.RIFERIMENTO_NORMATIVO }}.<br>
In vigore dal 01/01/2026; per spese con data di competenza fino al 31/12/2025 si applicano i
massimali della Circolare MEF n. 41/2024.</p>
```

No structural change needed — the template already iterates `rules.MASSIMALI_GIORNALIERI` etc.,
which now point at 2026 values.

## Test impact

### `tests/test_calculator.py` — all 5 existing tests remain green

All use the fixture default `data="2025-10-06"`. After the change, `_caps()` will return 2025
values for that date, so all hardcoded expectations (185.92, 232.41, 40.0, 105.0, 300.0, 92.96,
154.94, …) remain correct. The `test_plafond_esaurito_tutto_imponibile` test uses
`esente_gia_riconosciuta=1200.0` = the 2025 plafond → still correct.

### `tests/test_app.py` — one test breaks, rest stay green

| Test | Status |
|---|---|
| `test_registrazione_richiesta_valida` | green (2025 date) |
| `test_registrazione_richiesta_respinta` | green |
| `test_eccedenza_oltre_massimale_diventa_imponibile` | green (2025 date, 8.00/day) |
| `test_plafond_mensile_condiviso_tra_richieste` | green (2025 date, 1200 plafond) |
| `test_elenco_filtra_per_dipendente` | green |
| `test_riepilogo_mostra_totali` | green |
| **`test_normativa_mostra_massimali_vigenti`** | **RED** — asserts old values |

## New tests

### Add to `tests/test_calculator.py`

**`TestMassimaleTeorico` — 2026 date variants** (use `data="2026-03-01"`):
```
test_trasferta_italia_2026 : 4 giorni × 50.00 = 200.00
test_trasferta_estero_2026 : 3 giorni × 85.00 = 255.00
test_pasto_2026            : 5 giorni × 10.00 = 50.00
test_chilometrico_2026     : 250 km × 0.45   = 112.50
test_alloggio_2026         : 2 notti × 170.00 = 340.00
```

**`TestCalcola` — 2026 plafond:**
```
test_plafond_2026_esaurito_tutto_imponibile
  pasto, giorni=1, importo=10.00, gia=1400.0, data="2026-03-01"
  → esente=0.0, imponibile=10.0

test_plafond_2026_incapiente_limita_esente  (two sub-cases)
  pasto, giorni=5, importo=50.00, data="2026-03-01"
  gia=1350.0 → capienza=50, esente=50.00, imponibile=0.00
  gia=1380.0 → capienza=20, esente=20.00, imponibile=30.00

test_importo_sopra_massimale_2026
  trasferta_italia, giorni=2, importo=120.00, gia=0, data="2026-03-01"
  → teorico=100.00, esente=100.00, imponibile=20.00
```

**Transitional regime guard:**
```
test_transitional_2025_data_usa_massimali_vecchi
  pasto, giorni=1, importo=10.00, data="2025-12-31", gia=0
  → teorico=8.00, esente=8.00, imponibile=2.00

test_transitional_2026_data_usa_massimali_nuovi
  pasto, giorni=1, importo=10.00, data="2026-01-01", gia=0
  → teorico=10.00, esente=10.00, imponibile=0.00
```

### Update/add in `tests/test_app.py`

**Update failing test:**
```python
def test_normativa_mostra_massimali_vigenti(client):
    testo = client.get("/normativa").get_data(as_text=True)
    assert "50.00" in testo
    assert "85.00" in testo
    assert "1400.00" in testo
```

**New integration test:**
```python
def test_plafond_mensile_2026(client):
    # alloggio: 8 notti × 170.00 = 1360 teorico; importo 1350 → esente 1350
    nuova_richiesta_pasto(client, data="2026-01-15", categoria="alloggio",
                          notti="8", importo="1350.00", giorni="")
    # pasto: 8 giorni × 10.00 = 80 teorico; capienza = 1400-1350 = 50 → esente 50, imponibile 30
    nuova_richiesta_pasto(client, data="2026-01-20", importo="80.00", giorni="8")
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 1350.00
    assert richieste[1]["quota_esente"] == 50.00
    assert richieste[1]["quota_imponibile"] == 30.00
```

### 5. Documentation (`doc/` folder)

The `doc/` folder already exists locally (not yet pushed) with `architecture.md`, `tests.md`,
and other files. Three doc changes:

**`doc/circolare-mef-18-2026.md`** _(new file)_ — dedicated page for this regulatory update:
- Reference: Circolare MEF n. 18/2026, Section 2 (attach: `attach/ENG_circolare_mef_18_2026.pdf`)
- Old vs new values table (same as above)
- Transitional regime explanation: `richiesta["data"]` determines cap set; boundary 2026-01-01
- Files changed and why (`rules.py`, `calculator.py`, `app.py`, `normativa.html`)
- Note that Sections 3–5 are not yet implemented

**`doc/architecture.md`** _(update)_ — add a note that `rules.py` now contains versioned cap sets
(`_MASSIMALI_2025` / `_MASSIMALI_2026`) and the two selector functions `_caps(d)` and
`plafond_per_data(d)` / `plafond_per_mese(mese)`. The existing flat public names
(`MASSIMALI_GIORNALIERI` etc.) still point at current-year values for template use.

**`doc/tests.md`** _(update)_ — document the new test categories added:
- 2026 cap variants in `TestMassimaleTeorico`
- 2026 plafond behaviour in `TestCalcola`
- Transitional regime guard tests (boundary at 2026-01-01)
- New integration test `test_plafond_mensile_2026` in `test_app.py`

## What does NOT change

- `src/storage.py` — no logic depends on cap values
- `src/validator.py` — validation rules unchanged for change 1
- `src/templates/elenco.html`, `nuova_richiesta.html`, `base.html`, `riepilogo.html`
- `data/` — untouched

## Verification

```bash
pytest tests/ -v
```

Key assertions:
- All pre-existing tests pass (2025-date requests use 2025 caps)
- New 2026-date tests pass (transitional boundary works at 2026-01-01)
- Monthly plafond switches correctly at the 2026 boundary
- Normativa page shows 2026 values (50.00, 85.00, 1400.00)