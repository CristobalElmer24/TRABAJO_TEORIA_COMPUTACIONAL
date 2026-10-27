import random
import re
import unittest

import automatas as AU
from analizador import ER, ER_LENGUAJE


def _muestras(n=1500):
    random.seed(7)
    alfa = list("PEDMLCBS+-0123456789")
    base = ["PED-045-M12-C03", "PED-102-D-B02+S01", "PED-007-L-C01+B02+S03", "M12", "D", "L",
            "C03", "045", "PED", "-", "+", ""]
    out = list(base)
    for _ in range(n):
        s = list(random.choice(base))
        for _ in range(random.randint(0, 3)):
            op = random.choice("ids")
            if op == "i":
                s.insert(random.randint(0, len(s)), random.choice(alfa))
            elif op == "d" and s:
                s.pop(random.randrange(len(s)))
            elif s:
                s[random.randrange(len(s))] = random.choice(alfa)
        out.append("".join(s))
    return out


class PruebasEtapa2(unittest.TestCase):
    def test_afnd_afd_equivalen_a_la_er(self):
        for nombre, er in list(ER.items()) + [("LENGUAJE", ER_LENGUAJE)]:
            n = AU.afnd(er)
            d = AU.afd(n)
            for w in _muestras():
                esperado = re.fullmatch(er, w) is not None
                self.assertEqual(AU.afnd_acepta(n, w), esperado, (nombre, w))
                self.assertEqual(AU.afd_acepta(d, w), esperado, (nombre, w))

    def test_afd_es_determinista(self):
        for it in AU.datos():
            vistos = set()
            for s, c, t in [tuple(x.split("|")) for x in
                            ["%s|%s|%s" % tr for tr in AU.afd(AU.afnd(it["er"]))["trans"]]]:
                self.assertNotIn((s, c), vistos)
                vistos.add((s, c))

    def test_paquete_completo(self):
        datos = AU.datos()
        self.assertEqual(len(datos), 7)
        for it in datos:
            for k in ("afnd", "afd"):
                v = it[k]
                self.assertTrue(v["svg"].startswith("<svg"))
                self.assertEqual(len(v["quintupla"]), 5)
                self.assertTrue(v["transiciones"])


if __name__ == "__main__":
    unittest.main()
