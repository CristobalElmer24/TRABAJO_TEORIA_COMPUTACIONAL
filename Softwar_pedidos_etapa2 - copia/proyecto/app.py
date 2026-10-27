from flask import Flask, render_template, request, jsonify
import analizador as A
import automatas as AU

app = Flask(__name__)


def arbol_json(n):
    return {"etq": n.etq, "lexema": n.lexema,
            "hijos": [arbol_json(h) for h in n.hijos]}


def a_json(r):
    return {"entrada": r["entrada"], "valido": r["valido"],
            "mensaje": r["mensaje"], "pos": r["pos"], "pedido": r["pedido"],
            "tokens": [{"token": t, "lexema": l, "pos": p} for t, l, p in r["tokens"]],
            "traza": [{"pila": p, "entrada": e, "accion": a} for p, e, a in r["traza"]],
            "arbol": arbol_json(r["arbol"]) if r["arbol"] else None}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analizar", methods=["POST"])
def analizar():
    datos = request.get_json(silent=True) or {}
    lineas = [l for l in str(datos.get("texto", "")).splitlines() if l.strip()]
    return jsonify([a_json(A.analizar(l)) for l in lineas])


@app.route("/api/automatas")
def automatas():
    """Etapa 2: ER, AFND, AFD, tabla, transiciones y quíntupla de cada token."""
    return jsonify(AU.datos())


@app.route("/api/archivo", methods=["POST"])
def archivo():
    f = request.files.get("archivo")
    if not f:
        return jsonify({"error": "No se recibió archivo"}), 400
    texto = f.read().decode("utf-8", errors="ignore")
    return jsonify([a_json(A.analizar(l)) for l in texto.splitlines() if l.strip()])


if __name__ == "__main__":
    app.run(debug=True)
