"""Calcolo della quota esente e della quota imponibile di una richiesta."""

from datetime import date as _date

from src import rules


def massimale_teorico(richiesta):
    """Massimale di esenzione applicabile alla richiesta, in base alla categoria."""
    categoria = richiesta["categoria"]
    d = _date.fromisoformat(richiesta["data"])
    massimali, massimale_km, massimale_notte = rules._caps(d)
    if categoria in rules.CATEGORIE_A_GIORNATE:
        return round(massimali[categoria] * richiesta["giorni"], 2)
    if categoria == "chilometrico":
        return round(massimale_km * richiesta["km"], 2)
    if categoria == "alloggio":
        return round(massimale_notte * richiesta["notti"], 2)
    raise ValueError(f"categoria non gestita: {categoria}")


def calcola(richiesta, esente_gia_riconosciuta):
    """Restituisce (quota_esente, quota_imponibile, dettaglio).

    `esente_gia_riconosciuta` è la quota esente già riconosciuta al dipendente
    nel mese della richiesta, ai fini del plafond mensile.
    """
    importo = richiesta["importo"]
    teorico = massimale_teorico(richiesta)
    esente_teorica = min(importo, teorico)
    d = _date.fromisoformat(richiesta["data"])
    plafond = rules.plafond_per_data(d)
    capienza = max(plafond - esente_gia_riconosciuta, 0.0)
    esente = round(min(esente_teorica, capienza), 2)
    imponibile = round(importo - esente, 2)
    dettaglio = {
        "massimale_teorico": teorico,
        "esente_teorica": round(esente_teorica, 2),
        "capienza_plafond": round(capienza, 2),
    }
    return esente, imponibile, dettaglio
