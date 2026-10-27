"""Analizador léxico y sintáctico de pedidos de restaurante.
Lenguaje: PED-NNN-UBICACION-ITEM(+ITEM)*
"""
import re
from collections import OrderedDict

# ---------------------------------------------------------------- 1. ER
ER = OrderedDict([
    ("T_PREFIJO",   r"PED"),
    ("T_NUM",       r"[0-9]{3}"),
    ("T_UBICACION", r"M[0-9]{1,2}|D|L"),
    ("T_ITEM",      r"(?:C|B|S)[0-9]{2}"),
    ("T_GUION",     r"-"),
    ("T_MAS",       r"\+"),
])

# ------------------------------------------------- 2. AFD (nivel carácter)
DIG = set("0123456789")
CAT = set("CBS")


def _build_dfa():
    d = {}

    def add(s, syms, t):
        for c in syms:
            d[(s, c)] = t
    add("q0", "P", "q1"); add("q1", "E", "q2"); add("q2", "D", "q3")
    add("q3", "-", "q4"); add("q4", DIG, "q5"); add("q5", DIG, "q6")
    add("q6", DIG, "q7"); add("q7", "-", "q8")
    add("q8", "M", "q9"); add("q8", "DL", "q11")
    add("q9", DIG, "q10"); add("q10", DIG, "q11"); add("q10", "-", "q12")
    add("q11", "-", "q12")
    add("q12", CAT, "q13"); add("q13", DIG, "q14"); add("q14", DIG, "q15")
    add("q15", "+", "q16"); add("q16", CAT, "q13")
    return d


DFA_DELTA = _build_dfa()
DFA_START, DFA_FINAL = "q0", {"q15"}
DFA_STATES = ["q%d" % i for i in range(17)]


def dfa_run(cadena):
    """Devuelve (aceptada, traza, posicion_error)."""
    s, traza = DFA_START, []
    for i, c in enumerate(cadena):
        t = DFA_DELTA.get((s, c))
        traza.append((s, c, t))
        if t is None:
            return False, traza, i
        s = t
    return s in DFA_FINAL, traza, (None if s in DFA_FINAL else len(cadena))


# ------------------------------------------------------------ 3. AFND
EPS = "ε"


def nfa_ubicacion():
    """AFND (Thompson) de M[0-9]{1,2} | D | L"""
    T = {}

    def a(s, c, t):
        T.setdefault((s, c), set()).add(t)
    a("q0", EPS, "q1"); a("q0", EPS, "q5"); a("q0", EPS, "q7")
    a("q1", "M", "q2")
    for c in DIG:
        a("q2", c, "q3"); a("q3", c, "q4")
    a("q3", EPS, "q9"); a("q4", EPS, "q9")
    a("q5", "D", "q6"); a("q6", EPS, "q9")
    a("q7", "L", "q8"); a("q8", EPS, "q9")
    return T, "q0", {"q9"}


def eclose(T, S):
    st, res = list(S), set(S)
    while st:
        x = st.pop()
        for y in T.get((x, EPS), ()):
            if y not in res:
                res.add(y); st.append(y)
    return res


def nfa_accepts(nfa, w):
    T, q0, F = nfa
    cur = eclose(T, {q0})
    for c in w:
        nxt = set()
        for s in cur:
            nxt |= T.get((s, c), set())
        cur = eclose(T, nxt)
    return bool(cur & F)


def subset_construction(nfa, alfabeto):
    T, q0, F = nfa
    start = frozenset(eclose(T, {q0}))
    names, rows, work = {start: "A"}, [], [start]
    while work:
        S = work.pop(0)
        row = {}
        for c in alfabeto:
            N = set()
            for s in S:
                N |= T.get((s, c), set())
            N = frozenset(eclose(T, N))
            if not N:
                continue
            if N not in names:
                names[N] = chr(ord("A") + len(names)); work.append(N)
            row[c] = names[N]
        rows.append((names[S], S, row, bool(S & F)))
    return rows


# ------------------------------------------------------- 4. Analizador léxico
class ErrorLexico(Exception):
    def __init__(self, msg, pos):
        super().__init__(msg); self.pos = pos


def tokenizar(texto):
    """Tokeniza la cadena aplicando las ER. Devuelve lista (token, lexema, pos)."""
    toks, i = [], 0
    n = len(texto)
    while i < n:
        for nombre in ("T_PREFIJO", "T_GUION", "T_MAS", "T_ITEM",
                       "T_UBICACION", "T_NUM"):
            m = re.compile(ER[nombre]).match(texto, i)
            if m and m.end() > i:
                # T_NUM (3 dígitos) solo se acepta tras PED-
                if nombre == "T_NUM" and not (toks and toks[-1][0] == "T_GUION"
                                               and len(toks) == 2):
                    continue
                if nombre in ("T_UBICACION", "T_ITEM") and \
                        (m.end() < n and texto[m.end()] not in "-+"):
                    continue
                toks.append((nombre, m.group(), i)); i = m.end(); break
        else:
            raise ErrorLexico("Símbolo o patrón no reconocido «%s»" % texto[i], i)
    return toks


# --------------------------------------------------- 5. Gramática y SLR(1)
PRODS = [
    ("S'", ["Pedido"]),
    ("Pedido", ["PREFIJO", "GUION", "NUM", "GUION", "Ubicacion", "GUION", "ListaItems"]),
    ("Ubicacion", ["UBIC"]),
    ("ListaItems", ["ITEM"]),
    ("ListaItems", ["ITEM", "MAS", "ListaItems"]),
]
TERMINALES = ["PREFIJO", "GUION", "NUM", "UBIC", "ITEM", "MAS", "$"]
NOTERM = ["Pedido", "Ubicacion", "ListaItems"]
MAPA = {"T_PREFIJO": "PREFIJO", "T_GUION": "GUION", "T_NUM": "NUM",
        "T_UBICACION": "UBIC", "T_ITEM": "ITEM", "T_MAS": "MAS"}
FOLLOW = {"Pedido": {"$"}, "Ubicacion": {"GUION"}, "ListaItems": {"$"}}


def _closure(items):
    items, ch = set(items), True
    while ch:
        ch = False
        for (p, d) in list(items):
            r = PRODS[p][1]
            if d < len(r) and r[d] in NOTERM:
                for k, (l, _) in enumerate(PRODS):
                    if l == r[d] and (k, 0) not in items:
                        items.add((k, 0)); ch = True
    return frozenset(items)


def _goto(I, X):
    return _closure({(p, d + 1) for (p, d) in I
                     if d < len(PRODS[p][1]) and PRODS[p][1][d] == X})


def construir_lr():
    I0 = _closure({(0, 0)})
    estados, trans, work = [I0], {}, [I0]
    while work:
        I = work.pop(0)
        for X in [s for s in (TERMINALES[:-1] + NOTERM)]:
            J = _goto(I, X)
            if J:
                if J not in estados:
                    estados.append(J); work.append(J)
                trans[(estados.index(I), X)] = estados.index(J)
    action, goto = {}, {}
    for i, I in enumerate(estados):
        for (p, d) in I:
            r = PRODS[p][1]
            if d < len(r):
                if r[d] in TERMINALES:
                    action[(i, r[d])] = ("s", trans[(i, r[d])])
            else:
                if p == 0:
                    action[(i, "$")] = ("acc",)
                else:
                    for a in FOLLOW[PRODS[p][0]]:
                        action[(i, a)] = ("r", p)
        for A in NOTERM:
            if (i, A) in trans:
                goto[(i, A)] = trans[(i, A)]
    return estados, action, goto


ESTADOS, ACTION, GOTO = construir_lr()


def prod_str(p):
    return "%s → %s" % (PRODS[p][0], " ".join(PRODS[p][1]))


class Nodo:
    def __init__(self, etq, hijos=None, lexema=None):
        self.etq, self.hijos, self.lexema = etq, hijos or [], lexema


def parse_lr(tokens):
    """Análisis LR. Devuelve (aceptada, traza, arbol, mensaje)."""
    entrada = [MAPA[t[0]] for t in tokens] + ["$"]
    lex = [t[1] for t in tokens] + ["$"]
    pila, simb, nodos, i, traza = [0], [], [], 0, []
    while True:
        s, a = pila[-1], entrada[i]
        act = ACTION.get((s, a))
        pila_txt = " ".join(str(x) for x in _intercalar(pila, simb))
        rest = " ".join(entrada[i:])
        if act is None:
            esp = sorted({t for (st, t) in ACTION if st == s})
            traza.append((pila_txt, rest, "ERROR"))
            return False, traza, None, \
                "Se esperaba %s pero llegó «%s»" % (" o ".join(esp), a)
        if act[0] == "s":
            traza.append((pila_txt, rest, "d%d" % act[1]))
            pila.append(act[1]); simb.append(a)
            nodos.append(Nodo(a, lexema=lex[i])); i += 1
        elif act[0] == "r":
            p = act[1]; L, R = PRODS[p]
            traza.append((pila_txt, rest, "r%d: %s" % (p, prod_str(p))))
            k = len(R)
            hijos = nodos[-k:]
            del pila[-k:], simb[-k:], nodos[-k:]
            nodos.append(Nodo(L, hijos)); simb.append(L)
            pila.append(GOTO[(pila[-1], L)])
        else:
            traza.append((pila_txt, rest, "acc"))
            return True, traza, nodos[0], "Pedido válido"


def _intercalar(pila, simb):
    out = [pila[0]]
    for s, e in zip(simb, pila[1:]):
        out += [s, e]
    return out


# ------------------------------------------------------- 6. Integración
def analizar(texto):
    texto = texto.strip()
    res = {"entrada": texto, "valido": False, "tokens": [], "traza": [],
           "arbol": None, "mensaje": "", "pos": None, "pedido": None}
    ok, _, pos = dfa_run(texto)
    try:
        toks = tokenizar(texto)
    except ErrorLexico as e:
        res["mensaje"] = "Error léxico: %s (posición %d)" % (e, e.pos)
        res["pos"] = e.pos
        return res
    res["tokens"] = toks
    acept, traza, arbol, msg = parse_lr(toks)
    res["traza"], res["arbol"] = traza, arbol
    if acept:
        res["valido"], res["mensaje"] = True, msg
        res["pedido"] = {
            "correlativo": toks[2][1], "ubicacion": toks[4][1],
            "canal": ("Mesa " + toks[4][1][1:]) if toks[4][1][0] == "M"
                     else ("Delivery" if toks[4][1] == "D" else "Para llevar"),
            "items": [t[1] for t in toks[6:] if t[0] == "T_ITEM"]}
    else:
        res["mensaje"] = "Error sintáctico: " + msg
        if not ok and pos is not None:
            res["pos"] = pos
    return res


if __name__ == "__main__":
    for c in ["PED-045-M12-C03", "PED-102-D-B02+S01", "PED-007-L-C01+B02+S03",
              "PED45-M12-C03", "PED-045-X12-C03", "PED-045-M12-Z99", "PED-045-M12-"]:
        r = analizar(c)
        print(c, "->", r["valido"], r["mensaje"])


# ------------------------------------- 7. AFND del lenguaje completo (ε-AFND)
def nfa_lenguaje():
    """AFND con transiciones ε del lenguaje completo (25 estados)."""
    T = {}

    def a(s, c, t):
        T.setdefault((s, c), set()).add(t)
    for s, c, t in [("s0", "P", "s1"), ("s1", "E", "s2"), ("s2", "D", "s3"), ("s3", "-", "s4"),
                    ("s7", "-", "u0"), ("u0", EPS, "u1"), ("u0", EPS, "u5"), ("u0", EPS, "u7"),
                    ("u1", "M", "u2"), ("u3", EPS, "u9"), ("u4", EPS, "u9"), ("u5", "D", "u6"),
                    ("u6", EPS, "u9"), ("u7", "L", "u8"), ("u8", EPS, "u9"), ("u9", "-", "i0"),
                    ("i0", EPS, "i1"), ("i0", EPS, "i2"), ("i0", EPS, "i3"), ("i1", "C", "i4"),
                    ("i2", "B", "i4"), ("i3", "S", "i4"), ("i6", "+", "i0")]:
        a(s, c, t)
    for c in DIG:
        for s, t in [("s4", "s5"), ("s5", "s6"), ("s6", "s7"), ("u2", "u3"),
                     ("u3", "u4"), ("i4", "i5"), ("i5", "i6")]:
            a(s, c, t)
    return T, "s0", {"i6"}


ER_LENGUAJE = r"PED-[0-9]{3}-(?:M[0-9]{1,2}|D|L)-(?:C|B|S)[0-9]{2}(?:\+(?:C|B|S)[0-9]{2})*"
