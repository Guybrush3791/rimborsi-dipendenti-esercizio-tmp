# Data — `data/richieste.json`

Flat JSON array acting as the sole persistence layer. No database, no migrations.

## Record schema

| Field | Type | Notes |
|---|---|---|
| `id` | int | Auto-incremented by `storage.prossimo_id()` |
| `dipendente` | str | Free-text employee name; used as grouping key |
| `data` | str | ISO 8601 date `YYYY-MM-DD`; first 7 chars (`data[:7]`) form the month key |
| `categoria` | str | One of the five keys in `rules.CATEGORIE` |
| `importo` | float | Total amount claimed (€) |
| `giorni` | int\|null | Set for `trasferta_italia`, `trasferta_estero`, `pasto` |
| `km` | float\|null | Set for `chilometrico` |
| `notti` | int\|null | Set for `alloggio` |
| `stato` | str | `"valida"` or `"respinta"` |
| `motivazione` | str | Rejection reason; empty string when valid |
| `quota_esente` | float | IRPEF-exempt portion (€) |
| `quota_imponibile` | float | Taxable portion (€); always `importo − quota_esente` |
| `dettaglio` | obj\|null | Calculation breakdown (see below); `null` for rejected requests |

### `dettaglio` object

```json
{
  "massimale_teorico": 185.92,
  "esente_teorica": 180.0,
  "capienza_plafond": 1200.0
}
```

- `massimale_teorico` — regulatory cap for this request (rate × quantity)
- `esente_teorica` — `min(importo, massimale_teorico)` before applying the monthly cap
- `capienza_plafond` — remaining monthly cap at the moment of calculation (`1200 − already_consumed`)

## Key constraints

- **Immutable records**: there is no edit or delete route. Every submission appends a new record, including rejected ones.
- **Ordering**: records are stored insertion-ordered. The `/richieste` view re-sorts by `(data, id) DESC` at read time.
- **Monthly cap state is derived, not stored**: `storage.esente_riconosciuta_nel_mese()` recomputes the consumed cap on every new request by summing `quota_esente` of all `stato == "valida"` records for the same employee and month. Order of insertion therefore affects the cap distribution across requests in the same month.
