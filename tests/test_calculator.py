from src import calculator


def richiesta(**campi):
    base = {
        "dipendente": "Maria Rossi",
        "data": "2025-10-06",
        "categoria": "pasto",
        "importo": 10.0,
        "giorni": 1,
        "km": None,
        "notti": None,
    }
    base.update(campi)
    return base


class TestMassimaleTeorico:
    def test_trasferta_italia(self):
        r = richiesta(categoria="trasferta_italia", giorni=4)
        assert calculator.massimale_teorico(r) == 185.92

    def test_trasferta_estero(self):
        r = richiesta(categoria="trasferta_estero", giorni=3)
        assert calculator.massimale_teorico(r) == 232.41

    def test_pasto(self):
        r = richiesta(categoria="pasto", giorni=5)
        assert calculator.massimale_teorico(r) == 40.0

    def test_chilometrico(self):
        r = richiesta(categoria="chilometrico", km=250)
        assert calculator.massimale_teorico(r) == 105.0

    def test_alloggio(self):
        r = richiesta(categoria="alloggio", notti=2)
        assert calculator.massimale_teorico(r) == 300.0

    def test_trasferta_italia_2026(self):
        r = richiesta(data="2026-03-01", categoria="trasferta_italia", giorni=4)
        assert calculator.massimale_teorico(r) == 200.00

    def test_trasferta_estero_2026(self):
        r = richiesta(data="2026-03-01", categoria="trasferta_estero", giorni=3)
        assert calculator.massimale_teorico(r) == 255.00

    def test_pasto_2026(self):
        r = richiesta(data="2026-03-01", categoria="pasto", giorni=5)
        assert calculator.massimale_teorico(r) == 50.00

    def test_chilometrico_2026(self):
        r = richiesta(data="2026-03-01", categoria="chilometrico", km=250)
        assert calculator.massimale_teorico(r) == 112.50

    def test_alloggio_2026(self):
        r = richiesta(data="2026-03-01", categoria="alloggio", notti=2)
        assert calculator.massimale_teorico(r) == 340.00


class TestCalcola:
    def test_importo_sotto_massimale_tutto_esente(self):
        r = richiesta(categoria="pasto", giorni=5, importo=35.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 35.0
        assert imponibile == 0.0

    def test_importo_sopra_massimale_eccedenza_imponibile(self):
        r = richiesta(categoria="trasferta_italia", giorni=2, importo=120.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 92.96
        assert imponibile == 27.04

    def test_plafond_incapiente_limita_la_quota_esente(self):
        r = richiesta(categoria="alloggio", notti=2, importo=300.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1100.0)
        assert esente == 100.0
        assert imponibile == 200.0

    def test_plafond_esaurito_tutto_imponibile(self):
        r = richiesta(categoria="pasto", giorni=1, importo=8.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1200.0)
        assert esente == 0.0
        assert imponibile == 8.0

    def test_dettaglio_del_calcolo(self):
        r = richiesta(categoria="trasferta_estero", giorni=2, importo=200.0)
        _, _, dettaglio = calculator.calcola(r, esente_gia_riconosciuta=1100.0)
        assert dettaglio == {
            "massimale_teorico": 154.94,
            "esente_teorica": 154.94,
            "capienza_plafond": 100.0,
        }

    def test_plafond_2026_esaurito_tutto_imponibile(self):
        r = richiesta(data="2026-03-01", categoria="pasto", giorni=1, importo=10.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1400.0)
        assert esente == 0.0
        assert imponibile == 10.0

    def test_plafond_2026_incapiente_limita_esente_capienza_piena(self):
        r = richiesta(data="2026-03-01", categoria="pasto", giorni=5, importo=50.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1350.0)
        assert esente == 50.00
        assert imponibile == 0.00

    def test_plafond_2026_incapiente_limita_esente_parziale(self):
        r = richiesta(data="2026-03-01", categoria="pasto", giorni=5, importo=50.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1380.0)
        assert esente == 20.00
        assert imponibile == 30.00

    def test_importo_sopra_massimale_2026(self):
        r = richiesta(data="2026-03-01", categoria="trasferta_italia", giorni=2, importo=120.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 100.00
        assert imponibile == 20.00

    def test_transitional_2025_data_usa_massimali_vecchi(self):
        r = richiesta(data="2025-12-31", categoria="pasto", giorni=1, importo=10.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 8.00
        assert imponibile == 2.00

    def test_transitional_2026_data_usa_massimali_nuovi(self):
        r = richiesta(data="2026-01-01", categoria="pasto", giorni=1, importo=10.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 10.00
        assert imponibile == 0.00
