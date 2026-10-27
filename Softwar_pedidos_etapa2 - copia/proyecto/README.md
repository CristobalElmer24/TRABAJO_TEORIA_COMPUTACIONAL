# Analizador léxico y sintáctico de pedidos (Teoría de Computación – USIL)

Valida códigos de pedido con el formato `PED-NNN-UBICACIÓN-ÍTEM(+ÍTEM)*`
(mesa, para llevar y delivery) con expresiones regulares, AFND/AFD y análisis LR (SLR(1)).

## Etapa 1
Interfaz web (`templates/index.html`), servidor Flask (`app.py`), ingreso de pedidos
escritos o por archivo `.txt`, generación de tokens y lexemas.

## Etapa 2
Sección 7 de la interfaz y archivo `automatas.py`. Para cada lexema/token se genera con código:
1. ER (expresión regular)
2. AFND con transiciones ε (Thompson) — gráfico SVG dibujado por código, no es imagen
3. AFD (construcción de subconjuntos)
4. Tabla de transiciones
5. Transiciones δ
6. Quíntupla (Q, Σ, δ, q0, F)

Ruta de la API: `GET /api/automatas`.

## Ejecutar
    pip install -r requirements.txt
    python app.py          # http://localhost:5000
    python -m unittest     # pruebas (AFND y AFD verificados contra re.fullmatch)

## Archivos
- `app.py` – rutas Flask (`/`, `/api/analizar`, `/api/archivo`, `/api/automatas`)
- `analizador.py` – ER, AFD, AFND, gramática, tabla LR, analizador léxico y sintáctico
- `automatas.py` – Etapa 2: ER → AFND → AFD, tabla, transiciones, quíntupla y gráficos SVG
- `templates/index.html` – interfaz
- `test_analizador.py`, `test_automatas.py` – pruebas
