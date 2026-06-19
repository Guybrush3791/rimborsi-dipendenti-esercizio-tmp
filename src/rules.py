"""Parametri normativi per il calcolo dei rimborsi spese.

Fonte: Circolare MEF n. 41/2024 (2025) e n. 18/2026 (dal 01/01/2026).
"""

from datetime import date

SOGLIA_2026 = date(2026, 1, 1)

_MASSIMALI_2025 = {"trasferta_italia": 46.48, "trasferta_estero": 77.47, "pasto": 8.00}
_MASSIMALE_KM_2025 = 0.42
_MASSIMALE_NOTTE_2025 = 150.00
_PLAFOND_2025 = 1200.00

_MASSIMALI_2026 = {"trasferta_italia": 50.00, "trasferta_estero": 85.00, "pasto": 10.00}
_MASSIMALE_KM_2026 = 0.45
_MASSIMALE_NOTTE_2026 = 170.00
_PLAFOND_2026 = 1400.00

# Public names used by templates and riepilogo route (always current/2026 values)
MASSIMALI_GIORNALIERI = _MASSIMALI_2026
MASSIMALE_KM = _MASSIMALE_KM_2026
MASSIMALE_NOTTE = _MASSIMALE_NOTTE_2026
PLAFOND_MENSILE = _PLAFOND_2026

CATEGORIE = {
    "trasferta_italia": "Trasferta in Italia",
    "trasferta_estero": "Trasferta all'estero",
    "pasto": "Rimborso pasto",
    "chilometrico": "Rimborso chilometrico",
    "alloggio": "Rimborso alloggio",
}

CATEGORIE_A_GIORNATE = ("trasferta_italia", "trasferta_estero", "pasto")

RIFERIMENTO_NORMATIVO = "Circolare MEF n. 41/2024 (fino al 31/12/2025) e n. 18/2026 (dal 01/01/2026)"


def _caps(d: date):
    if d >= SOGLIA_2026:
        return _MASSIMALI_2026, _MASSIMALE_KM_2026, _MASSIMALE_NOTTE_2026
    return _MASSIMALI_2025, _MASSIMALE_KM_2025, _MASSIMALE_NOTTE_2025


def plafond_per_data(d: date) -> float:
    return _PLAFOND_2026 if d >= SOGLIA_2026 else _PLAFOND_2025


def plafond_per_mese(mese: str) -> float:
    """mese is 'YYYY-MM'."""
    return plafond_per_data(date.fromisoformat(mese + "-01"))
