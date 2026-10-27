import unittest
from analizador import analizar

VALIDAS = ["PED-045-M12-C03", "PED-102-D-B02+S01", "PED-007-L-C01+B02+S03",
           "PED-999-M5-S99", "PED-001-D-C00+C01+B10+S20"]
INVALIDAS = ["PED45-M12-C03", "PED-45-M12-C03", "PED-045-X12-C03", "PED-045-M12-Z99",
             "PED-045-M12-", "PED-045-M123-C03", "PED-045-M-C03", "PED-045-M12-C3",
             "PED-045-M12-C03+", "PED-045-D-C03++B02", "ped-045-M12-C03"]


class Pruebas(unittest.TestCase):
    def test_validas(self):
        for c in VALIDAS:
            self.assertTrue(analizar(c)["valido"], c)

    def test_invalidas(self):
        for c in INVALIDAS:
            self.assertFalse(analizar(c)["valido"], c)

    def test_pedido_estructurado(self):
        p = analizar("PED-102-D-B02+S01")["pedido"]
        self.assertEqual((p["correlativo"], p["canal"], p["items"]), ("102", "Delivery", ["B02", "S01"]))


if __name__ == "__main__":
    unittest.main()
