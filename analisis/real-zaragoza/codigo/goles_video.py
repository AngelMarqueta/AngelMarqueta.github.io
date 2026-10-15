"""
Goles del Real Zaragoza vistos en vídeo + estadísticas de Sofascore.

Uso (desde la raíz del repositorio):
    python analisis/real-zaragoza/codigo/goles_video.py

Qué hace:
    1. Lee los goles que he apuntado viendo los resúmenes de YouTube
       (datos/entrada/video/goles_video.csv) y las estadísticas de cada
       partido sacadas de Sofascore (datos/entrada/sofascore.csv).
    2. Comprueba que los goles del vídeo cuadran con goles.csv.
    3. Hace las tablas resumen y las guarda en datos/salida/video/.
    4. Dibuja todos los gráficos en proyectos/real-zaragoza/graficos/video/.

Cómo apunto cada gol:
    - El carril es siempre desde el punto de vista del equipo que ataca.
      Así "derecha" significa lo mismo en un gol a favor y en uno en contra.
    - Las coordenadas (tiro_x, tiro_y, pase_x, pase_y) son una estimación a ojo
      sobre el fotograma, en metros, en un campo de 105 x 68. La x va de la
      portería propia (0) a la rival (105) y la y desde la banda derecha (0)
      hasta la izquierda (68). El error puede ser de varios metros, por eso solo
      las relleno cuando la jugada se ve bien.
    - Si algo no se ve en el resumen pongo "sin_dato" y no me lo invento.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin ventana, solo guardo los PNG
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Arc, Rectangle

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
PROYECTO = Path(__file__).resolve().parents[1]
ENTRADA = PROYECTO / "datos" / "entrada"
SALIDA = PROYECTO / "datos" / "salida" / "video"
WEB = PROYECTO.parents[1]
GRAFICOS = WEB / "proyectos" / "real-zaragoza" / "graficos" / "video"

# ---------------------------------------------------------------------------
# Colores y estilo (los mismos que el resto de la web)
# ---------------------------------------------------------------------------
VERDE = "#1f6b3e"        # a favor
VERDE_CLARO = "#8db89b"
NARANJA = "#ff6a2b"      # en contra
NARANJA_CLARO = "#ffb48f"
GRIS = "#b7bfb6"
TINTA = "#0f2418"
TINTA_SUAVE = "#4d6356"
CESPED = "#2f6b45"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12.5,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.edgecolor": GRIS,
    "axes.labelcolor": TINTA_SUAVE,
    "xtick.color": TINTA_SUAVE,
    "ytick.color": TINTA_SUAVE,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "legend.frameon": False,
})

# Textos que salen en los gráficos (los códigos del CSV son cortos y sin tildes)
INICIOS = {
    "ataque_posicional": "Ataque posicional",
    "transicion": "Transición rápida",
    "balon_parado": "Balón parado",
    "penalti": "Penalti",
    "sin_dato": "No se ve",
}
CARRILES = {"izquierda": "Izquierda", "centro": "Centro", "derecha": "Derecha", "sin_dato": "No se ve"}
ZONAS = {
    "area_pequena": "Área pequeña",
    "area_central": "Área grande, centro",
    "area_lateral": "Área grande, lateral",
    "fuera_area": "Fuera del área",
    "penalti": "Penalti",
    "sin_dato": "No se ve",
}
PASES = {
    "centro_lateral": "Centro lateral",
    "pase_atras": "Pase atrás",
    "pase_interior": "Pase raso por dentro",
    "pase_al_espacio": "Pase al espacio",
    "rechace": "Rechace",
    "corner": "Córner",
    "falta_lateral": "Falta lateral",
    "falta_directa": "Falta directa",
    "sin_pase": "Sin pase (conducción o penalti)",
    "sin_dato": "No se ve",
}
NOMBRES_CORTOS = {
    "Gimnàstic de Tarragona": "Nàstic",
    "Antequera CF": "Antequera",
    "Juventud Torremolinos CF": "Torremolinos",
    "FC Cartagena": "Cartagena",
    "UD Ibiza": "Ibiza",
    "CD Teruel": "Teruel",
    "Atlético Madrileño": "At. Madrileño",
}


# ---------------------------------------------------------------------------
# Lectura y comprobaciones
# ---------------------------------------------------------------------------

def minuto_numerico(texto):
    """'45+7' -> 45.7 para ordenar; el descuento no pasa del minuto siguiente."""
    base, _, extra = str(texto).partition("+")
    return int(base) + (min(int(extra), 9) / 10 if extra else 0)


def cargar():
    goles = pd.read_csv(ENTRADA / "video" / "goles_video.csv", encoding="utf-8")
    goles["minuto_num"] = goles["minuto"].apply(minuto_numerico)
    goles["rival_corto"] = goles["rival"].map(NOMBRES_CORTOS).fillna(goles["rival"])
    sofa = pd.read_csv(ENTRADA / "sofascore.csv", encoding="utf-8")
    oficiales = pd.read_csv(ENTRADA / "goles.csv", encoding="utf-8")
    partidos = pd.read_csv(ENTRADA / "partidos.csv", encoding="utf-8")
    return goles, sofa, oficiales, partidos


def comprobar(goles, oficiales):
    """Los goles que he visto tienen que ser los mismos que los de la ficha oficial.
    Si no cuadran prefiero que el script se pare a dibujar algo mal."""
    vistos = goles.groupby(["partido_id", "sentido"]).size()
    fichas = oficiales.groupby(["partido_id", "sentido"]).size()
    distintos = vistos.sub(fichas, fill_value=0)
    distintos = distintos[distintos != 0]
    if not distintos.empty:
        raise SystemExit(f"Los goles del vídeo no cuadran con goles.csv:\n{distintos}")
    # Las coordenadas tienen que caer dentro del campo
    for col, maximo in (("tiro_x", 105), ("pase_x", 105), ("tiro_y", 68), ("pase_y", 68)):
        fuera = goles[(goles[col] < 0) | (goles[col] > maximo)]
        if not fuera.empty:
            raise SystemExit(f"{col} fuera del campo en {list(fuera['gol_id'])}")


def sofascore_ancho(sofa):
    """Paso Sofascore de formato largo (una fila por métrica) a una fila por partido."""
    ancho = sofa.pivot_table(index="partido_id", columns="metrica",
                             values=["zaragoza", "valor_rival"], aggfunc="first")
    ancho.columns = [f"{m}_{'zgz' if lado == 'zaragoza' else 'rival'}" for lado, m in ancho.columns]
    return ancho.reset_index()


# ---------------------------------------------------------------------------
# Tablas resumen
# ---------------------------------------------------------------------------

def conteo(goles, columna, etiquetas):
    """Cuántos goles a favor y en contra hay por cada valor de una columna."""
    t = (goles.groupby([columna, "sentido"]).size().unstack(fill_value=0)
         .reindex(columns=["Favor", "Contra"], fill_value=0))
    t = t.reindex([k for k in etiquetas if k in t.index])
    t.index = [etiquetas[k] for k in t.index]
    return t


# ---------------------------------------------------------------------------
# Dibujo del campo
# ---------------------------------------------------------------------------

def campo(ax, mitad=True, color_lineas="white", fondo=CESPED):
    """Dibuja un campo de 105 x 68 (o solo la mitad de ataque, de x=52,5 a 105)."""
    x0 = 52.5 if mitad else 0
    ax.add_patch(Rectangle((x0 - 2, -2), 105 - x0 + 4, 72, color=fondo, zorder=0))
    # Franjas del césped, para que se lea como un campo
    for i, x in enumerate(np.arange(x0, 105, 105 / 18)):
        if i % 2 == 0:
            ax.add_patch(Rectangle((x, 0), 105 / 18, 68, color="white", alpha=0.035, zorder=0))
    lw = 1.3
    kw = dict(color=color_lineas, lw=lw, zorder=1)
    ax.plot([x0, 105, 105, x0, x0], [0, 0, 68, 68, 0], **kw)
    if not mitad:
        ax.plot([52.5, 52.5], [0, 68], **kw)
        ax.plot([0, 16.5, 16.5, 0], [13.85, 13.85, 54.15, 54.15], **kw)
        ax.plot([0, 5.5, 5.5, 0], [24.85, 24.85, 43.15, 43.15], **kw)
    else:
        ax.plot([52.5, 52.5], [0, 68], **kw)
    ax.add_patch(Arc((52.5, 34), 18.3, 18.3, theta1=-90 if mitad else 0, theta2=90 if mitad else 360, **kw))
    # Área grande, área pequeña, punto de penalti, semicírculo y portería
    ax.plot([105, 88.5, 88.5, 105], [13.85, 13.85, 54.15, 54.15], **kw)
    ax.plot([105, 99.5, 99.5, 105], [24.85, 24.85, 43.15, 43.15], **kw)
    ax.scatter([94], [34], s=6, color=color_lineas, zorder=1)
    ax.add_patch(Arc((94, 34), 18.3, 18.3, theta1=127, theta2=233, **kw))
    ax.plot([105, 106.5, 106.5, 105], [30.34, 30.34, 37.66, 37.66], **kw)
    ax.set_xlim(x0 - 2, 108)
    ax.set_ylim(-2, 70)
    ax.set_aspect("equal")
    ax.axis("off")


def guardar(fig, nombre):
    GRAFICOS.mkdir(parents=True, exist_ok=True)
    fig.savefig(GRAFICOS / nombre, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Gráficos de los goles
# ---------------------------------------------------------------------------

def barras_espejo(tabla, titulo, subtitulo, nombre):
    """Barras horizontales: a favor hacia la derecha y en contra hacia la izquierda.
    Así se ve de un vistazo en qué se parece y en qué no lo que hace y lo que encaja."""
    fig, ax = plt.subplots(figsize=(8, 0.55 * len(tabla) + 1.6))
    y = np.arange(len(tabla))[::-1]
    ax.barh(y, tabla["Favor"], color=VERDE, height=0.6, label="A favor")
    ax.barh(y, -tabla["Contra"], color=NARANJA, height=0.6, label="En contra")
    for yi, (f, c) in zip(y, tabla[["Favor", "Contra"]].values):
        if f:
            ax.text(f + 0.15, yi, str(f), va="center", color=VERDE, fontweight="bold")
        if c:
            ax.text(-c - 0.15, yi, str(c), va="center", ha="right", color=NARANJA, fontweight="bold")
    ax.set_yticks(y, tabla.index)
    limite = max(tabla.values.max(), 1) + 1.5
    ax.set_xlim(-limite, limite)
    ax.axvline(0, color=GRIS, lw=1)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    # El subtítulo va debajo del título, con un poco de aire para que no se pisen
    ax.set_title(titulo, pad=22)
    ax.text(0, 1.03, subtitulo, transform=ax.transAxes, color=TINTA_SUAVE, fontsize=9)
    ax.legend(loc="lower right", ncol=2, bbox_to_anchor=(1, -0.12))
    guardar(fig, nombre)


def carriles_en_campo(goles, nombre):
    """El carril por el que llega cada gol, pintado sobre el campo.
    Dos campos: los goles del Zaragoza y los que le marcan."""
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6))
    for ax, sentido, color, titulo in ((axes[0], "Favor", VERDE, "Goles del Real Zaragoza"),
                                       (axes[1], "Contra", NARANJA, "Goles que encaja")):
        campo(ax)
        g = goles[goles["sentido"] == sentido]
        total = len(g)
        # Tres bandas: derecha abajo (y 0-22,7), centro y la izquierda arriba
        bandas = {"derecha": (0, 22.67), "centro": (22.67, 45.33), "izquierda": (45.33, 68)}
        for carril, (y0, y1) in bandas.items():
            n = (g["carril"] == carril).sum()
            ax.add_patch(Rectangle((52.5, y0), 52.5, y1 - y0, color=color,
                                   alpha=0.12 + 0.55 * n / max(total, 1), zorder=0.5, lw=0))
            ax.text(70, (y0 + y1) / 2, f"{n}", color="white", fontsize=22, fontweight="bold",
                    ha="center", va="center", zorder=3)
            ax.text(76, (y0 + y1) / 2, CARRILES[carril].lower(), color="white", fontsize=10,
                    va="center", zorder=3)
        sin = (g["carril"] == "sin_dato").sum()
        ax.set_title(f"{titulo} ({total})", color=TINTA)
        ax.text(53, -5.5, f"Ataque hacia la derecha. Sin carril claro en el vídeo: {sin}",
                fontsize=8.5, color=TINTA_SUAVE)
    fig.suptitle("¿Por dónde llegan los goles?", x=0.02, ha="left", fontweight="bold", fontsize=13)
    guardar(fig, nombre)


def mapa_remates(goles, nombre):
    """Dónde se remató cada gol y desde dónde llegó el último pase.
    Las posiciones son estimaciones a ojo sobre el vídeo (error de varios metros)."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.9))
    for ax, sentido, color, titulo in ((axes[0], "Favor", VERDE_CLARO, "A favor"),
                                       (axes[1], "Contra", NARANJA, "En contra")):
        campo(ax)
        g = goles[(goles["sentido"] == sentido) & goles["tiro_x"].notna()]
        for fila in g.itertuples():
            # Flecha del último pase, si lo tengo
            if pd.notna(fila.pase_x):
                ax.annotate("", xy=(fila.tiro_x, fila.tiro_y), xytext=(fila.pase_x, fila.pase_y),
                            arrowprops=dict(arrowstyle="->", color="white", lw=1, alpha=0.75), zorder=2)
            # Cuadrado para la cabeza, círculo para el pie; los de confianza baja, más transparentes
            marcador = "s" if fila.remate == "cabeza" else "o"
            alfa = 0.95 if fila.confianza in ("alta", "media") else 0.45
            ax.scatter(fila.tiro_x, fila.tiro_y, s=110, marker=marcador, color=color,
                       edgecolor="white", lw=1.2, alpha=alfa, zorder=3)
            ax.text(fila.tiro_x - 1.2, fila.tiro_y + 2.2, f"J{fila.jornada}", fontsize=7.5,
                    color="white", ha="right", zorder=4)
        sin = (goles["sentido"] == sentido).sum() - len(g)
        ax.set_title(f"{titulo}: {len(g)} goles con posición", color=TINTA)
        ax.text(53, -5.5, f"Sin posición fiable: {sin}. Círculo, pie; cuadrado, cabeza. "
                          f"Flecha, último pase.", fontsize=8.5, color=TINTA_SUAVE)
    fig.suptitle("Dónde se rematan los goles (estimación a partir del vídeo)",
                 x=0.02, ha="left", fontweight="bold", fontsize=13)
    guardar(fig, nombre)


def cronologia(goles, nombre):
    """Cada partido en una fila y cada gol en su minuto, con el color de cómo nació."""
    colores = {"ataque_posicional": "#3f8f5c", "transicion": "#2b6cb0", "balon_parado": "#d69e2e",
               "penalti": "#805ad5", "sin_dato": GRIS}
    fig, ax = plt.subplots(figsize=(10, 4.2))
    jornadas = sorted(goles["jornada"].unique())
    for j in jornadas:
        ax.axhline(j, color=GRIS, lw=0.6, zorder=0)
    for fila in goles.itertuples():
        x = min(fila.minuto_num, 95)
        # Los goles a favor van un poco por encima de la línea y los de en contra por debajo
        y = fila.jornada - 0.18 if fila.sentido == "Favor" else fila.jornada + 0.18
        ax.scatter(x, y, s=95, color=colores[fila.inicio], marker="o" if fila.sentido == "Favor" else "X",
                   edgecolor="white", lw=0.8, zorder=3)
    etiquetas = [f"J{j} · {goles.loc[goles['jornada'] == j, 'rival_corto'].iloc[0]}" for j in jornadas]
    ax.set_yticks(jornadas, etiquetas)
    ax.invert_yaxis()
    ax.set_xlim(0, 97)
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_xlabel("Minuto (el descuento se dibuja al final de cada parte)")
    for x in (45, 90):
        ax.axvline(x, color=GRIS, lw=1, ls=":")
    # Leyenda hecha a mano: colores por inicio y forma por sentido
    from matplotlib.lines import Line2D
    elementos = [Line2D([], [], marker="o", ls="", color=c, markersize=8, label=INICIOS[k])
                 for k, c in colores.items() if k in set(goles["inicio"])]
    elementos += [Line2D([], [], marker="o", ls="", color=TINTA_SUAVE, markersize=8, label="A favor"),
                  Line2D([], [], marker="X", ls="", color=TINTA_SUAVE, markersize=8, label="En contra")]
    ax.legend(handles=elementos, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=4, fontsize=8.5)
    ax.set_title("Los 26 goles de liga, minuto a minuto")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    guardar(fig, nombre)


def tipo_por_sentido(goles, nombre):
    """Barras al 100 %: qué parte de los goles sale de cada tipo de jugada."""
    t = conteo(goles, "inicio", INICIOS)
    pct = t / t.sum() * 100
    colores = ["#3f8f5c", "#2b6cb0", "#d69e2e", "#805ad5", GRIS]
    fig, ax = plt.subplots(figsize=(9, 2.8))
    izquierda = np.zeros(2)
    for (tipo, fila), c in zip(pct.iterrows(), colores):
        ax.barh(["En contra", "A favor"], fila[["Contra", "Favor"]].values, left=izquierda,
                color=c, label=tipo, height=0.55)
        for i, v in enumerate(fila[["Contra", "Favor"]].values):
            if v >= 8:
                n = int(t.loc[tipo, ["Contra", "Favor"][i]])
                ax.text(izquierda[i] + v / 2, i, f"{n}", ha="center", va="center",
                        color="white", fontweight="bold")
        izquierda += fila[["Contra", "Favor"]].values
    ax.set_xlim(0, 100)
    ax.set_xlabel("% de los goles")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.35), ncol=5, fontsize=8.5)
    ax.set_title("Cómo nacen los goles (el número es la cantidad de goles)")
    guardar(fig, nombre)


def participacion(goles, nombre):
    """Goles y pases de gol de cada jugador en los goles a favor que he visto."""
    favor = goles[goles["sentido"] == "Favor"]
    g = favor[~favor["remate"].eq("propia_puerta")]["goleador"].value_counts()
    a = favor["asistencia"].dropna().value_counts()
    t = pd.DataFrame({"Goles": g, "Asistencias": a}).fillna(0).astype(int)
    t["Total"] = t.sum(axis=1)
    t = t.sort_values(["Total", "Goles"], ascending=True)
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(t) + 1.2))
    ax.barh(t.index, t["Goles"], color=VERDE, label="Goles")
    ax.barh(t.index, t["Asistencias"], left=t["Goles"], color=VERDE_CLARO, label="Último pase")
    for i, (nombre_j, fila) in enumerate(t.iterrows()):
        ax.text(fila["Total"] + 0.1, i, str(fila["Total"]), va="center", fontweight="bold", color=TINTA)
    ax.set_xticks(range(0, t["Total"].max() + 2))
    ax.set_title("Quién participa en los goles del Zaragoza")
    ax.legend(loc="lower right")
    ax.tick_params(axis="y", length=0)
    guardar(fig, nombre)


# ---------------------------------------------------------------------------
# Gráficos con Sofascore
# ---------------------------------------------------------------------------

def xg_por_partido(sofa, partidos, nombre):
    """xG y goles de cada partido: barras para el xG y puntos para los goles."""
    s = sofa.merge(partidos[["partido_id", "jornada", "rival", "goles_favor", "goles_contra"]], on="partido_id")
    s["rival_corto"] = s["rival"].map(NOMBRES_CORTOS).fillna(s["rival"])
    x = np.arange(len(s))
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.5, 4.6), gridspec_kw={"width_ratios": [1.8, 1]})
    ax.bar(x - 0.2, s["xg_zgz"], 0.38, color=VERDE_CLARO, label="xG Zaragoza")
    ax.bar(x + 0.2, s["xg_rival"], 0.38, color=NARANJA_CLARO, label="xG rival")
    ax.scatter(x - 0.2, s["goles_favor"], color=VERDE, zorder=3, s=40, label="Goles Zaragoza")
    ax.scatter(x + 0.2, s["goles_contra"], color=NARANJA, zorder=3, s=40, label="Goles rival")
    ax.set_xticks(x, [f"J{j}\n{r}" for j, r in zip(s["jornada"], s["rival_corto"])], fontsize=8.5)
    ax.set_ylim(0, max(s[["xg_zgz", "xg_rival", "goles_favor", "goles_contra"]].max()) + 1.1)
    ax.set_title("xG y goles por partido")
    ax.legend(loc="upper center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, -0.2))
    # A la derecha, lo acumulado: si la línea de goles va por encima del xG, se marca más de lo esperado
    j = s["jornada"]
    ax2.plot(j, s["xg_zgz"].cumsum(), color=VERDE, ls="--", label="xG a favor")
    ax2.plot(j, s["goles_favor"].cumsum(), color=VERDE, label="Goles a favor")
    ax2.plot(j, s["xg_rival"].cumsum(), color=NARANJA, ls="--", label="xG en contra")
    ax2.plot(j, s["goles_contra"].cumsum(), color=NARANJA, label="Goles en contra")
    ax2.set_xticks(j, [f"J{v}" for v in j])
    ax2.set_title("Acumulado")
    ax2.legend(fontsize=8)
    guardar(fig, nombre)


def tiros_y_area(sofa, partidos, nombre):
    """Tiros dentro y fuera del área de los dos equipos, partido a partido."""
    s = sofa.merge(partidos[["partido_id", "jornada", "rival"]], on="partido_id")
    s["rival_corto"] = s["rival"].map(NOMBRES_CORTOS).fillna(s["rival"])
    x = np.arange(len(s))
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(x - 0.2, s["tiros_dentro_area_zgz"], 0.38, color=VERDE, label="Zaragoza, dentro del área")
    ax.bar(x - 0.2, s["tiros_fuera_area_zgz"], 0.38, bottom=s["tiros_dentro_area_zgz"],
           color=VERDE_CLARO, label="Zaragoza, fuera del área")
    ax.bar(x + 0.2, s["tiros_dentro_area_rival"], 0.38, color=NARANJA, label="Rival, dentro del área")
    ax.bar(x + 0.2, s["tiros_fuera_area_rival"], 0.38, bottom=s["tiros_dentro_area_rival"],
           color=NARANJA_CLARO, label="Rival, fuera del área")
    ax.set_xticks(x, [f"J{j}\n{r}" for j, r in zip(s["jornada"], s["rival_corto"])], fontsize=8.5)
    ax.set_title("Tiros: cuántos desde dentro del área (Sofascore)")
    ax.legend(ncol=2, fontsize=8)
    guardar(fig, nombre)


def xg_por_tiro(sofa, partidos, nombre):
    """xG por tiro: una forma sencilla de ver si las ocasiones son buenas o solo muchas."""
    s = sofa.merge(partidos[["partido_id", "jornada", "rival"]], on="partido_id")
    s["rival_corto"] = s["rival"].map(NOMBRES_CORTOS).fillna(s["rival"])
    zgz = s["xg_zgz"] / s["tiros_zgz"]
    riv = s["xg_rival"] / s["tiros_rival"]
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(s["jornada"], zgz, marker="o", color=VERDE, label="Real Zaragoza")
    ax.plot(s["jornada"], riv, marker="o", color=NARANJA, label="Rival")
    for xj, a, b in zip(s["jornada"], zgz, riv):
        # La etiqueta del que está más arriba va encima y la del otro debajo, para que no choquen
        arriba, abajo = (a, b) if a >= b else (b, a)
        for valor, color in ((a, VERDE), (b, NARANJA)):
            dy = 0.012 if valor == arriba else -0.03
            ax.text(xj, valor + dy, f"{valor:.2f}".replace(".", ","), ha="center", fontsize=8, color=color)
    ax.set_xticks(s["jornada"], [f"J{j}\n{r}" for j, r in zip(s["jornada"], s["rival_corto"])], fontsize=8.5)
    ax.set_ylim(0, max(zgz.max(), riv.max()) + 0.08)
    ax.set_title("xG por tiro: calidad media de cada disparo")
    ax.legend()
    guardar(fig, nombre)


def juego_y_duelos(sofa, partidos, nombre):
    """Cuatro indicadores de cómo se juega cada partido: posesión, centros,
    duelos ganados y entradas en el último tercio (esta solo desde la J6)."""
    s = sofa.merge(partidos[["partido_id", "jornada"]], on="partido_id")
    j = s["jornada"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.4), sharex=True)
    ax = axes[0, 0]
    ax.bar(j, s["posesion_pct_zgz"], color=VERDE)
    ax.axhline(50, color=GRIS, ls=":")
    ax.set_title("Posesión (%)")
    ax.set_ylim(0, 100)
    ax = axes[0, 1]
    ax.bar(j - 0.2, s["centros_total_zgz"], 0.38, color=VERDE_CLARO, label="Intentados")
    ax.bar(j + 0.2, s["centros_ok_zgz"], 0.38, color=VERDE, label="Buenos")
    ax.set_title("Centros del Zaragoza")
    ax.legend(fontsize=8)
    ax = axes[1, 0]
    ax.plot(j, s["duelos_ganados_pct_zgz"], marker="o", color=VERDE)
    ax.axhline(50, color=GRIS, ls=":")
    ax.set_title("Duelos ganados (%)")
    ax.set_ylim(30, 70)
    ax = axes[1, 1]
    if "entradas_ultimo_tercio_zgz" in s:
        ax.bar(j - 0.2, s["entradas_ultimo_tercio_zgz"], 0.38, color=VERDE, label="Zaragoza")
        ax.bar(j + 0.2, s["entradas_ultimo_tercio_rival"], 0.38, color=NARANJA, label="Rival")
        ax.legend(fontsize=8)
    ax.set_title("Entradas en el último tercio (solo J6 y J7)")
    for a in axes[1]:
        a.set_xticks(j, [f"J{v}" for v in j])
    fig.suptitle("Cómo juega el Zaragoza, partido a partido (Sofascore)", x=0.02, ha="left",
                 fontweight="bold", fontsize=13)
    fig.tight_layout()
    guardar(fig, nombre)


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    goles, sofa_largo, oficiales, partidos = cargar()
    comprobar(goles, oficiales)
    sofa = sofascore_ancho(sofa_largo)

    # Tablas resumen para quien quiera los números sin gráficos
    SALIDA.mkdir(parents=True, exist_ok=True)
    tablas = {
        "inicio": conteo(goles, "inicio", INICIOS),
        "carril": conteo(goles, "carril", CARRILES),
        "zona_remate": conteo(goles, "zona_remate", ZONAS),
        "ultimo_pase": conteo(goles, "ultimo_pase", PASES),
    }
    for nombre_tabla, t in tablas.items():
        t.to_csv(SALIDA / f"{nombre_tabla}.csv", encoding="utf-8-sig", index_label=nombre_tabla)
    sofa.to_csv(SALIDA / "sofascore_partidos.csv", encoding="utf-8-sig", index=False)

    # Gráficos
    barras_espejo(tablas["inicio"], "Cómo empieza la jugada de cada gol",
                  "Goles de liga, jornadas 1 a 7", "inicio.png")
    barras_espejo(tablas["zona_remate"], "Desde dónde se remata",
                  "Zona del último toque", "zona_remate.png")
    barras_espejo(tablas["ultimo_pase"], "Cómo es el último pase",
                  "Pase que deja el balón al goleador", "ultimo_pase.png")
    carriles_en_campo(goles, "carriles.png")
    mapa_remates(goles, "mapa_remates.png")
    cronologia(goles, "cronologia.png")
    tipo_por_sentido(goles, "tipo_por_sentido.png")
    participacion(goles, "participacion.png")
    xg_por_partido(sofa, partidos, "xg.png")
    tiros_y_area(sofa, partidos, "tiros_area.png")
    xg_por_tiro(sofa, partidos, "xg_por_tiro.png")
    juego_y_duelos(sofa, partidos, "juego.png")

    # Un pequeño resumen por pantalla
    favor = goles[goles["sentido"] == "Favor"]
    contra = goles[goles["sentido"] == "Contra"]
    print(f"Goles vistos: {len(goles)} ({len(favor)} a favor y {len(contra)} en contra)")
    print("Inicio de la jugada:\n", tablas["inicio"])
    print("Carril:\n", tablas["carril"])
    print(f"xG total: {sofa['xg_zgz'].sum():.2f} a favor y {sofa['xg_rival'].sum():.2f} en contra")
    print(f"Gráficos en {GRAFICOS}")


if __name__ == "__main__":
    main()
