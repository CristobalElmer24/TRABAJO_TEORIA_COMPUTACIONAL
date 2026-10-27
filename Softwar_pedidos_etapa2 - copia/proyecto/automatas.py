"""Etapa 2 - Teoría de Computación (USIL)

A partir de cada expresión regular (ER) de los lexemas del lenguaje de pedidos
se genera, con código:
  1. AFND con transiciones ε (construcción de Thompson)
  2. AFD equivalente (construcción de subconjuntos con ε-cierre)
  3. Tabla de transiciones, lista de transiciones y quíntupla (Q, Σ, δ, q0, F)
  4. Gráfico (SVG) del AFND y del AFD. Los gráficos NO son imágenes: se dibujan
     desde este código fuente.

Soporta la parte de la sintaxis de ER usada en el proyecto:
  literales, [0-9], ( ), (?: ), |, *, +, ?, {n}, {n,m} y \\ para escapar.
"""
from collections import OrderedDict

from analizador import ER, ER_LENGUAJE

EPS = "ε"


# ------------------------------------------------------ 1. Parser de la ER
class _Parser:
    def __init__(self, s):
        self.s, self.i = s, 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else None

    def eat(self):
        c = self.s[self.i]
        self.i += 1
        return c

    def alt(self):
        ramas = [self.cat()]
        while self.peek() == "|":
            self.eat()
            ramas.append(self.cat())
        return ramas[0] if len(ramas) == 1 else ("alt", ramas)

    def cat(self):
        xs = []
        while self.peek() not in (None, "|", ")"):
            xs.append(self.rep())
        return xs[0] if len(xs) == 1 else ("cat", xs)

    def rep(self):
        a = self.atom()
        while self.peek() in ("*", "+", "?", "{"):
            c = self.eat()
            if c == "*":
                a = ("star", a)
            elif c == "+":
                a = ("cat", [a, ("star", a)])
            elif c == "?":
                a = ("alt", [a, ("eps",)])
            else:  # {n} o {n,m}
                j = self.s.index("}", self.i)
                partes = self.s[self.i:j].split(",")
                self.i = j + 1
                n = int(partes[0])
                m = int(partes[1]) if len(partes) > 1 else n
                a = ("cat", [a] * n + [("alt", [a, ("eps",)])] * (m - n))
        return a

    def atom(self):
        c = self.eat()
        if c == "(":
            if self.s.startswith("?:", self.i):
                self.i += 2
            a = self.alt()
            self.eat()  # ')'
            return a
        if c == "[":
            j = self.s.index("]", self.i)
            etiqueta = self.s[self.i:j]
            self.i = j + 1
            return ("sym", etiqueta)       # clase de caracteres: un solo símbolo
        if c == "\\":
            return ("sym", self.eat())
        return ("sym", c)


# --------------------------------------------- 2. ER -> AFND (Thompson)
class _Borrador:
    def __init__(self):
        self.n, self.t = 0, []

    def nuevo(self):
        self.n += 1
        return self.n - 1


def _thompson(ast, B):
    k = ast[0]
    if k in ("sym", "eps"):
        s, e = B.nuevo(), B.nuevo()
        B.t.append((s, ast[1] if k == "sym" else EPS, e))
        return s, e
    if k == "cat":
        s, e = _thompson(ast[1][0], B)
        for x in ast[1][1:]:
            s2, e2 = _thompson(x, B)
            B.t.append((e, EPS, s2))
            e = e2
        return s, e
    if k == "alt":
        s, e = B.nuevo(), B.nuevo()
        for x in ast[1]:
            s1, e1 = _thompson(x, B)
            B.t += [(s, EPS, s1), (e1, EPS, e)]
        return s, e
    if k == "star":
        s, e = B.nuevo(), B.nuevo()
        s1, e1 = _thompson(ast[1], B)
        B.t += [(s, EPS, s1), (e1, EPS, e), (s, EPS, e), (e1, EPS, s1)]
        return s, e
    raise ValueError(k)


def _num(q):
    return int(q[1:])


def afnd(er):
    """Devuelve el AFND de la ER: dict con estados, alfabeto, trans, inicial, finales."""
    B = _Borrador()
    s, e = _thompson(_Parser(er).alt(), B)
    ady = {}
    for a, _, b in B.t:
        ady.setdefault(a, []).append(b)
    orden, vistos, i = [s], {s}, 0
    while i < len(orden):                      # numeración q0, q1, ... por BFS
        for b in ady.get(orden[i], []):
            if b not in vistos:
                vistos.add(b)
                orden.append(b)
        i += 1
    nombre = {x: "q%d" % k for k, x in enumerate(orden)}
    trans = sorted({(nombre[a], c, nombre[b]) for a, c, b in B.t},
                   key=lambda t: (_num(t[0]), t[1], _num(t[2])))
    return {"estados": [nombre[x] for x in orden],
            "alfabeto": sorted({c for _, c, _ in trans if c != EPS}),
            "trans": trans, "inicial": "q0", "finales": [nombre[e]]}


# ------------------------------------------------ 3. AFND -> AFD (subconjuntos)
def _cierre(T, S):
    res, pila = set(S), list(S)
    while pila:
        x = pila.pop()
        for y in T.get((x, EPS), ()):
            if y not in res:
                res.add(y)
                pila.append(y)
    return res


def afd(nfa):
    T = {}
    for a, c, b in nfa["trans"]:
        T.setdefault((a, c), set()).add(b)
    ini = frozenset(_cierre(T, {nfa["inicial"]}))
    nombres, orden, trans, i = {ini: "q0"}, [ini], [], 0
    while i < len(orden):
        S = orden[i]
        i += 1
        for c in nfa["alfabeto"]:
            N = set()
            for s in S:
                N |= T.get((s, c), set())
            if not N:
                continue                        # estado de error implícito
            N = frozenset(_cierre(T, N))
            if N not in nombres:
                nombres[N] = "q%d" % len(nombres)
                orden.append(N)
            trans.append((nombres[S], c, nombres[N]))
    fin = set(nfa["finales"])
    return {"estados": [nombres[S] for S in orden], "alfabeto": nfa["alfabeto"],
            "trans": trans, "inicial": "q0",
            "finales": [nombres[S] for S in orden if fin & S],
            "subconjuntos": {nombres[S]: sorted(S, key=_num) for S in orden}}


# ------------------------------------------- 4. Simulación (para verificar)
def _coincide(etiqueta, ch):
    return ch in "0123456789" if etiqueta == "0-9" else etiqueta == ch


def afd_acepta(d, cadena):
    T = {}
    for a, c, b in d["trans"]:
        T.setdefault(a, []).append((c, b))
    s = d["inicial"]
    for ch in cadena:
        sig = [b for c, b in T.get(s, []) if _coincide(c, ch)]
        if not sig:
            return False
        s = sig[0]
    return s in d["finales"]


def afnd_acepta(n, cadena):
    T = {}
    for a, c, b in n["trans"]:
        T.setdefault((a, c), set()).add(b)
    cur = _cierre(T, {n["inicial"]})
    for ch in cadena:
        sig = set()
        for (a, c), bs in T.items():
            if a in cur and c != EPS and _coincide(c, ch):
                sig |= bs
        cur = _cierre(T, sig)
    return bool(cur & set(n["finales"]))


# ------------------------------- 5. Quíntupla, tabla y lista de transiciones
def _agrupar(a):
    g = OrderedDict()
    for s, c, t in a["trans"]:
        g.setdefault((s, c), []).append(t)
    return g


def quintupla(a, tipo):
    Q = ", ".join(a["estados"])
    sigma = ", ".join(a["alfabeto"])
    if tipo == "afnd":
        sigma += ", " + EPS
    d = "δ: Q × Σ → P(Q)" if tipo == "afnd" else "δ: Q × Σ → Q"
    return [("Q", "{" + Q + "}"), ("Σ", "{" + sigma + "}"),
            ("δ", d + " (ver tabla de transiciones)"),
            ("q0", a["inicial"]), ("F", "{" + ", ".join(a["finales"]) + "}")]


def tabla(a, tipo):
    cols = list(a["alfabeto"]) + ([EPS] if tipo == "afnd" else [])
    g = _agrupar(a)
    filas = []
    for q in a["estados"]:
        marca = ("→" if q == a["inicial"] else "") + ("*" if q in a["finales"] else "")
        celdas = []
        for c in cols:
            ts = g.get((q, c), [])
            celdas.append("—" if not ts else
                          (ts[0] if tipo == "afd" else "{" + ", ".join(ts) + "}"))
        filas.append({"estado": (marca + " " if marca else "") + q, "celdas": celdas})
    return {"cols": cols, "filas": filas}


def transiciones(a, tipo):
    out = []
    for (s, c), ts in _agrupar(a).items():
        der = ts[0] if tipo == "afd" else "{" + ", ".join(ts) + "}"
        out.append("δ(%s, %s) = %s" % (s, c, der))
    return out


# ------------------------------------------------ 6. Gráfico SVG (por código)
def svg(a, uid):
    est, R, GX, GY = a["estados"], 18, 92, 72
    ady = {}
    for s, _, t in a["trans"]:
        ady.setdefault(s, set()).add(t)
    nivel, cola = {a["inicial"]: 0}, [a["inicial"]]
    for q in cola:
        for t in sorted(ady.get(q, ()), key=_num):
            if t not in nivel:
                nivel[t] = nivel[q] + 1
                cola.append(t)
    filas, pos = {}, {}
    for q in est:
        n = nivel.get(q, 0)
        pos[q] = (56 + n * GX, 70 + filas.get(n, 0) * GY)
        filas[n] = filas.get(n, 0) + 1
    W = 56 + max(nivel.values()) * GX + 56
    H = 70 + (max(filas.values()) - 1) * GY + 70
    aristas = OrderedDict()
    for s, c, t in a["trans"]:
        aristas.setdefault((s, t), []).append(c)
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
         'font-family="Consolas,monospace" font-size="12">' % (W, H, W, H),
         '<defs><marker id="f%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
         'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
         'class="g-flecha"/></marker></defs>' % uid]
    x0, y0 = pos[a["inicial"]]
    o.append('<line x1="%d" y1="%d" x2="%d" y2="%d" class="g-linea" marker-end="url(#f%s)"/>'
             % (x0 - 44, y0, x0 - R - 1, y0, uid))
    for (s, t), cs in aristas.items():
        etq = ",".join(sorted(set(cs), key=lambda z: (z == EPS, z)))
        (x1, y1), (x2, y2) = pos[s], pos[t]
        if s == t:
            o.append('<path d="M%d,%d C%d,%d %d,%d %d,%d" class="g-linea" fill="none" '
                     'marker-end="url(#f%s)"/>' % (x1 - 9, y1 - R + 2, x1 - 34, y1 - 58,
                                                    x1 + 34, y1 - 58, x1 + 9, y1 - R + 2, uid))
            lx, ly = x1, y1 - 52
        else:
            span = abs(nivel.get(t, 0) - nivel.get(s, 0))
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1
            L = (dx * dx + dy * dy) ** .5 or 1
            off = 0 if (span == 1 and dy == 0) else -(22 + 9 * span)
            cx, cy = mx + off * (-dy / L), my + off * (dx / L)
            if span == 1 and dy != 0:
                cx, cy = mx, my

            def borde(px, py):
                ux, uy = cx - px, cy - py
                u = (ux * ux + uy * uy) ** .5 or 1
                return px + R * ux / u, py + R * uy / u
            (ax, ay), (bx, by) = borde(x1, y1), borde(x2, y2)
            # la flecha llega al borde del nodo destino
            o.append('<path d="M%.1f,%.1f Q%.1f,%.1f %.1f,%.1f" class="g-linea" fill="none" '
                     'marker-end="url(#f%s)"/>' % (ax, ay, cx, cy, bx, by, uid))
            lx, ly = .25 * ax + .5 * cx + .25 * bx, .25 * ay + .5 * cy + .25 * by - 4
        o.append('<text x="%.1f" y="%.1f" text-anchor="middle" class="g-etq">%s</text>'
                 % (lx, ly, etq.replace("&", "&amp;").replace("<", "&lt;")))
    for q in est:
        x, y = pos[q]
        fin = q in a["finales"]
        o.append('<circle cx="%d" cy="%d" r="%d" class="g-nodo"/>' % (x, y, R))
        if fin:
            o.append('<circle cx="%d" cy="%d" r="%d" class="g-nodo g-fin"/>' % (x, y, R - 4))
        o.append('<text x="%d" y="%d" text-anchor="middle" class="g-q">%s</text>' % (x, y + 4, q))
    o.append("</svg>")
    return "".join(o)


# ----------------------------------------------------- 7. Paquete para la web
def _vista(a, tipo, uid):
    return {"estados": a["estados"], "alfabeto": a["alfabeto"], "inicial": a["inicial"],
            "finales": a["finales"], "quintupla": quintupla(a, tipo),
            "tabla": tabla(a, tipo), "transiciones": transiciones(a, tipo),
            "svg": svg(a, uid), "subconjuntos": a.get("subconjuntos")}


_CACHE = None


def datos():
    """ER, AFND y AFD de cada token y del lenguaje completo (se calcula una vez)."""
    global _CACHE
    if _CACHE is None:
        items = list(ER.items()) + [("LENGUAJE_COMPLETO", ER_LENGUAJE)]
        res = []
        for k, (nombre, er) in enumerate(items):
            n = afnd(er)
            d = afd(n)
            res.append({"token": nombre, "er": er,
                        "afnd": _vista(n, "afnd", "n%d" % k),
                        "afd": _vista(d, "afd", "d%d" % k)})
        _CACHE = res
    return _CACHE


if __name__ == "__main__":
    for it in datos():
        print(it["token"], it["er"], "| AFND:", len(it["afnd"]["estados"]),
              "estados | AFD:", len(it["afd"]["estados"]), "estados")
