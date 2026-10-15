"""
Goles del Real Zaragoza vistos en vídeo + estadísticas de Sofascore.

Uso (desde la raíz del repositorio):
    python analisis/real-zaragoza/codigo/goles_video.py

Qué hace, paso a paso:
    1. Lee los goles que he apuntado viendo los resúmenes de YouTube
       (datos/entrada/video/goles_video.csv) y las estadísticas de cada
       partido sacadas de Sofascore (datos/entrada/sofascore.csv).
    2. Comprueba que los goles del vídeo cuadran con la ficha oficial
       (goles.csv). Si falta o sobra alguno, se para y avisa.
    3. Hace las tablas resumen (conteos por tipo de jugada, carril, zona de
       remate y último pase) y las guarda en datos/salida/video/.
    4. Dibuja los gráficos en proyectos/real-zaragoza/graficos/video/, que son
       los que usa la página «Los 26 goles, vistos uno a uno».

Criterios que sigo al apuntar cada gol (importante para leer bien los datos):
    - El carril es siempre desde el punto de vista del equipo que ATACA. Así
      «derecha» significa lo mismo en un gol a favor y en uno en contra. Ojo:
      un gol en contra que llega por la izquierda del rival entra por el
      costado derecho de la defensa del Zaragoza.
    - Las coordenadas (tiro_x, tiro_y, pase_x, pase_y) son una estimación a ojo
      sobre el fotograma, en metros, en un campo de 105 x 68 (las medidas
      habituales de un campo de Primera Federación). La x va de la portería
      propia (0) a la rival (105) y la y desde la banda derecha (0) hasta la
      izquierda (68). El error puede ser de varios metros; por eso solo las
      relleno cuando la jugada se ve bien.
    - Si algo no se ve en el resumen pongo «sin_dato». No me invento nada:
      un hueco es más honesto que un dato inventado.

Librerías: pandas para las tablas y matplotlib para los gráficos. Nada más,
para que se pueda ejecutar con lo que ya pide requirements.txt.
"""

from pathlib import Path

import matplotlib

# Backend «Agg»: matplotlib dibuja en memoria y guarda el PNG sin abrir ninguna
# ventana. Hace falta cuando el script se ejecuta en un servidor sin pantalla
# (por ejemplo, en la tarea automática de cada jornada).
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Arc, Rectangle

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
# Path(__file__) es la ruta de este mismo archivo. Con .parents[1] subo de
# codigo/ a real-zaragoza/, y desde ahí construyo el resto. Así el script
# funciona igual lo ejecute desde donde lo ejecute.
PROYECTO = Path(__file__).resolve().parents[1]
ENTRADA = PROYECTO / "datos" / "entrada"
SALIDA = PROYECTO / "datos" / "salida" / "video"
WEB = PROYECTO.parents[1]                       # raíz del repositorio de la web
GRAFICOS = WEB / "proyectos" / "real-zaragoza" / "graficos" / "video"

# ---------------------------------------------------------------------------
# Colores y estilo
# ---------------------------------------------------------------------------
# El Zaragoza va en azul (el de la camiseta) y el rival en naranja, que es el
# color de acento de la web. Los tonos claros los uso para la segunda serie
# de un mismo equipo (por ejemplo, xG frente a goles).
AZUL = "#213e96"          # Real Zaragoza
AZUL_CLARO = "#8fa9ce"
NARANJA = "#ff6a2b"       # rival
NARANJA_CLARO = "#ffb48f"
GRIS = "#b7bfb6"          # rejillas, líneas de referencia y «no se ve»
TINTA = "#11264a"         # texto principal
TINTA_SUAVE = "#4b607e"   # texto secundario
CESPED = "#2f6b45"        # fondo de los campos

# rcParams son los valores por defecto de matplotlib. Cambiándolos aquí una
# vez me ahorro repetir el mismo formato en cada gráfico.
plt.rcParams.update({
    "font.family": "DejaVu Sans",     # viene con matplotlib y tiene tildes y ñ
    "font.size": 10,
    "axes.titlesize": 12.5,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",     # títulos alineados a la izquierda, como en la web
    "axes.edgecolor": GRIS,
    "axes.labelcolor": TINTA_SUAVE,
    "xtick.color": TINTA_SUAVE,
    "ytick.color": TINTA_SUAVE,
    "axes.spines.top": False,         # quito los bordes de arriba y de la derecha:
    "axes.spines.right": False,       # no aportan nada y ensucian
    "figure.facecolor": "white",
    "legend.frameon": False,
})

# ---------------------------------------------------------------------------
# Etiquetas
# ---------------------------------------------------------------------------
# En el CSV guardo códigos cortos y sin tildes (balon_parado, area_pequena…)
# porque son más cómodos para filtrar y no dan problemas de codificación.
# Estos diccionarios los traducen al texto que sale en los gráficos. El orden
# de cada diccionario es también el orden en el que salen las barras.
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
# Nombres cortos para que quepan en el eje x sin solaparse
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
    """Convierte el minuto en texto a un número para poder ordenar y dibujar.

    '45+7' -> 45.7 y '90+12' -> 90.9. El descuento lo meto como décimas y con
    un tope de 9, para que un gol en el 45+7 nunca quede después de uno en el 46.
    """
    base, _, extra = str(texto).partition("+")   # partition separa por el primer «+»
    return int(base) + (min(int(extra), 9) / 10 if extra else 0)


def cargar():
    """Lee los CSV que necesito y añade dos columnas de ayuda a los goles."""
    # utf-8-sig lee bien el archivo tenga o no la marca BOM que añade Excel al
    # guardar. Si leyera con «utf-8» a secas y alguien lo guardase desde Excel,
    # el nombre de la primera columna llegaría con un carácter invisible delante.
    goles = pd.read_csv(ENTRADA / "video" / "goles_video.csv", encoding="utf-8-sig")
    goles["minuto_num"] = goles["minuto"].apply(minuto_numerico)
    # map() cambia cada rival por su nombre corto; fillna() deja el nombre
    # original si un rival nuevo todavía no está en NOMBRES_CORTOS
    goles["rival_corto"] = goles["rival"].map(NOMBRES_CORTOS).fillna(goles["rival"])
    sofa = pd.read_csv(ENTRADA / "sofascore.csv", encoding="utf-8-sig")
    oficiales = pd.read_csv(ENTRADA / "goles.csv", encoding="utf-8-sig")
    partidos = pd.read_csv(ENTRADA / "partidos.csv", encoding="utf-8-sig")
    return goles, sofa, oficiales, partidos


def comprobar(goles, oficiales):
    """Control de calidad antes de dibujar nada.

    1. Los goles que he visto tienen que ser los mismos que los de la ficha
       oficial: mismo número de goles a favor y en contra en cada partido.
    2. Las coordenadas tienen que caer dentro del campo.

    Si algo falla, el script se para con SystemExit y un mensaje claro.
    Prefiero eso a publicar un gráfico con un gol de menos sin darme cuenta.
    """
    # groupby + size cuenta cuántas filas hay por partido y sentido
    vistos = goles.groupby(["partido_id", "sentido"]).size()
    fichas = oficiales.groupby(["partido_id", "sentido"]).size()
    # Resto una serie de la otra; fill_value=0 sirve para los partidos que solo
    # aparecen en una de las dos (por ejemplo, uno que aún no he visto)
    distintos = vistos.sub(fichas, fill_value=0)
    distintos = distintos[distintos != 0]
    if not distintos.empty:
        raise SystemExit(f"Los goles del vídeo no cuadran con goles.csv:\n{distintos}")

    for col, maximo in (("tiro_x", 105), ("pase_x", 105), ("tiro_y", 68), ("pase_y", 68)):
        fuera = goles[(goles[col] < 0) | (goles[col] > maximo)]
        if not fuera.empty:
            raise SystemExit(f"{col} fuera del campo en {list(fuera['gol_id'])}")


def sofascore_ancho(sofa):
    """Paso Sofascore de formato largo a formato ancho.

    En el CSV hay una fila por partido y métrica (formato «largo», cómodo para
    ir añadiendo métricas). Para dibujar me viene mejor una fila por partido con
    una columna por métrica (formato «ancho»): xg_zgz, xg_rival, tiros_zgz…
    pivot_table hace justo esa transformación.
    """
    ancho = sofa.pivot_table(index="partido_id", columns="metrica",
                             values=["zaragoza", "valor_rival"], aggfunc="first")
    # pivot_table deja columnas de dos niveles (lado, métrica); las aplano a un
    # solo nombre del tipo «métrica_zgz» o «métrica_rival»
    ancho.columns = [f"{m}_{'zgz' if lado == 'zaragoza' else 'rival'}" for lado, m in ancho.columns]
    return ancho.reset_index()


# ---------------------------------------------------------------------------
# Tablas resumen
# ---------------------------------------------------------------------------

def conteo(goles, columna, etiquetas):
    """Tabla de frecuencias: cuántos goles a favor y en contra hay por cada
    valor de una columna (por ejemplo, por carril).

    Devuelve una tabla con dos columnas, «Favor» y «Contra», y una fila por
    categoría, ya con el texto bonito y en el orden del diccionario de etiquetas.
    """
    t = (goles.groupby([columna, "sentido"]).size()
         .unstack(fill_value=0)                                   # sentido pasa a columnas
         .reindex(columns=["Favor", "Contra"], fill_value=0))     # siempre en este orden
    # Me quedo con las categorías que existen, en el orden que yo quiero
    t = t.reindex([k for k in etiquetas if k in t.index])
    t.index = [etiquetas[k] for k in t.index]
    return t


# ---------------------------------------------------------------------------
# Dibujo del campo
# ---------------------------------------------------------------------------

def campo(ax, mitad=True, color_lineas="white", fondo=CESPED):
    """Dibuja un campo de 105 x 68 metros (o solo el medio campo de ataque,
    de x = 52,5 a 105) sobre unos ejes de matplotlib.

    Las medidas son las reglamentarias: área grande de 16,5 m de fondo y
    40,3 m de ancho, área pequeña de 5,5 x 18,3, punto de penalti a 11 m y
    círculo central y semicírculo del área de 9,15 m de radio.
    """
    x0 = 52.5 if mitad else 0
    ax.add_patch(Rectangle((x0 - 2, -2), 105 - x0 + 4, 72, color=fondo, zorder=0))
    # Franjas del césped (muy suaves), para que se lea como un campo de verdad
    for i, x in enumerate(np.arange(x0, 105, 105 / 18)):
        if i % 2 == 0:
            ax.add_patch(Rectangle((x, 0), 105 / 18, 68, color="white", alpha=0.035, zorder=0))
    kw = dict(color=color_lineas, lw=1.3, zorder=1)      # estilo común de todas las líneas
    ax.plot([x0, 105, 105, x0, x0], [0, 0, 68, 68, 0], **kw)   # contorno
    ax.plot([52.5, 52.5], [0, 68], **kw)                         # línea de medio campo
    if not mitad:
        # Áreas de la portería propia, solo si dibujo el campo entero
        ax.plot([0, 16.5, 16.5, 0], [13.85, 13.85, 54.15, 54.15], **kw)
        ax.plot([0, 5.5, 5.5, 0], [24.85, 24.85, 43.15, 43.15], **kw)
    # Círculo central: entero o solo la mitad que cae en mi medio campo
    ax.add_patch(Arc((52.5, 34), 18.3, 18.3, theta1=-90 if mitad else 0, theta2=90 if mitad else 360, **kw))
    # Área grande, área pequeña, punto de penalti, semicírculo y portería
    ax.plot([105, 88.5, 88.5, 105], [13.85, 13.85, 54.15, 54.15], **kw)
    ax.plot([105, 99.5, 99.5, 105], [24.85, 24.85, 43.15, 43.15], **kw)
    ax.scatter([94], [34], s=6, color=color_lineas, zorder=1)
    ax.add_patch(Arc((94, 34), 18.3, 18.3, theta1=127, theta2=233, **kw))
    ax.plot([105, 106.5, 106.5, 105], [30.34, 30.34, 37.66, 37.66], **kw)
    ax.set_xlim(x0 - 2, 108)
    ax.set_ylim(-2, 70)
    ax.set_aspect("equal")    # un metro mide lo mismo en horizontal que en vertical
    ax.axis("off")            # sin ejes ni números: es un dibujo, no un gráfico de dispersión


def punto_zaragoza(ax, x, y, tamano=11, alfa=1.0):
    """Círculo partido por la mitad, azul y blanco, para los goles del Zaragoza.

    matplotlib permite rellenar medio marcador con fillstyle="left": la mitad
    izquierda toma markerfacecolor y la derecha markerfacecoloralt.
    """
    ax.plot(x, y, marker="o", markersize=tamano, fillstyle="left", markerfacecolor=AZUL,
            markerfacecoloralt="white", markeredgecolor="white", markeredgewidth=1.2,
            alpha=alfa, ls="", zorder=3)


def guardar(fig, nombre):
    """Guarda la figura en la carpeta de gráficos de la web y la cierra.
    dpi=160 da una imagen nítida en pantallas de alta resolución sin pesar
    demasiado; bbox_inches="tight" recorta el margen blanco sobrante."""
    GRAFICOS.mkdir(parents=True, exist_ok=True)
    fig.savefig(GRAFICOS / nombre, dpi=160, bbox_inches="tight")
    plt.close(fig)   # sin esto, matplotlib guarda todas las figuras en memoria


# ---------------------------------------------------------------------------
# Gráficos de los goles
# ---------------------------------------------------------------------------

def barras_espejo(tabla, titulo, subtitulo, nombre):
    """Gráfico de barras divergente (o «en espejo»): a favor hacia la derecha y
    en contra hacia la izquierda, con el eje en el cero.

    Lo prefiero a dos barras una al lado de la otra porque se compara de un
    vistazo lo que el Zaragoza hace y lo que le hacen en cada categoría.
    """
    fig, ax = plt.subplots(figsize=(8, 0.55 * len(tabla) + 1.6))   # el alto crece con las categorías
    y = np.arange(len(tabla))[::-1]          # [::-1] para que la primera categoría quede arriba
    ax.barh(y, tabla["Favor"], color=AZUL, height=0.6, label="A favor")
    ax.barh(y, -tabla["Contra"], color=NARANJA, height=0.6, label="En contra")   # negativo = a la izquierda
    # Etiqueta con el número al final de cada barra (solo si no es cero)
    for yi, (f, c) in zip(y, tabla[["Favor", "Contra"]].values):
        if f:
            ax.text(f + 0.15, yi, str(f), va="center", color=AZUL, fontweight="bold")
        if c:
            ax.text(-c - 0.15, yi, str(c), va="center", ha="right", color=NARANJA, fontweight="bold")
    ax.set_yticks(y, tabla.index)
    # Límites simétricos, para que el cero quede en el centro del gráfico
    limite = max(tabla.values.max(), 1) + 1.5
    ax.set_xlim(-limite, limite)
    ax.axvline(0, color=GRIS, lw=1)
    ax.set_xticks([])                        # los números ya están en las barras
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

    Divido el medio campo en tres bandas iguales de 22,67 m (68 / 3) y coloreo
    cada una con más intensidad cuantos más goles llegan por ella. Es un mapa
    de calor muy sencillo, pero se entiende sin leer ningún eje.
    """
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6))
    for ax, sentido, color, titulo in ((axes[0], "Favor", AZUL, "Goles del Real Zaragoza"),
                                       (axes[1], "Contra", NARANJA, "Goles que encaja")):
        campo(ax)
        g = goles[goles["sentido"] == sentido]
        total = len(g)
        # La y empieza en la banda derecha del que ataca, así que la derecha queda
        # abajo y la izquierda arriba, como si miraras el partido desde la grada
        bandas = {"derecha": (0, 22.67), "centro": (22.67, 45.33), "izquierda": (45.33, 68)}
        for carril, (y0, y1) in bandas.items():
            n = (g["carril"] == carril).sum()
            # alpha (opacidad) entre 0,12 y 0,67 según el peso de ese carril
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
    """Mapa de remates: dónde se remató cada gol y desde dónde llegó el último pase.

    Las posiciones son estimaciones a ojo sobre el vídeo (con un error de varios
    metros), así que el gráfico sirve para ver zonas, no para medir distancias.
    Los goles con confianza baja salen más transparentes.
    """
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.9))
    for ax, sentido, titulo in ((axes[0], "Favor", "A favor"), (axes[1], "Contra", "En contra")):
        campo(ax)
        # notna() descarta los goles sin posición: no los dibujo en ningún sitio
        g = goles[(goles["sentido"] == sentido) & goles["tiro_x"].notna()]
        for fila in g.itertuples():
            # Flecha del último pase, si lo tengo apuntado
            if pd.notna(fila.pase_x):
                ax.annotate("", xy=(fila.tiro_x, fila.tiro_y), xytext=(fila.pase_x, fila.pase_y),
                            arrowprops=dict(arrowstyle="->", color="white", lw=1, alpha=0.75), zorder=2)
            alfa = 0.95 if fila.confianza in ("alta", "media") else 0.45
            if sentido == "Favor":
                # Los del Zaragoza, con el círculo azul y blanco (cuadrado si es de cabeza)
                if fila.remate == "cabeza":
                    ax.plot(fila.tiro_x, fila.tiro_y, marker="s", markersize=10, fillstyle="left",
                            markerfacecolor=AZUL, markerfacecoloralt="white", markeredgecolor="white",
                            alpha=alfa, ls="", zorder=3)
                else:
                    punto_zaragoza(ax, fila.tiro_x, fila.tiro_y, alfa=alfa)
            else:
                ax.scatter(fila.tiro_x, fila.tiro_y, s=110, marker="s" if fila.remate == "cabeza" else "o",
                           color=NARANJA, edgecolor="white", lw=1.2, alpha=alfa, zorder=3)
            # Jornada al lado de cada punto, para poder buscar el gol en la tabla
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
    """Línea de tiempo: cada partido en una fila y cada gol en su minuto.

    El color dice cómo nació la jugada y la forma dice de quién es el gol
    (círculo, del Zaragoza; aspa, del rival). Sirve para ver de un vistazo en
    qué tramos de partido se concentran los goles.
    """
    colores = {"ataque_posicional": "#3f8f5c", "transicion": "#2b6cb0", "balon_parado": "#d69e2e",
               "penalti": "#805ad5", "sin_dato": GRIS}
    fig, ax = plt.subplots(figsize=(10, 4.2))
    jornadas = sorted(goles["jornada"].unique())
    for j in jornadas:
        ax.axhline(j, color=GRIS, lw=0.6, zorder=0)     # una línea guía por partido
    for fila in goles.itertuples():
        x = min(fila.minuto_num, 95)                      # el descuento largo no se sale del gráfico
        # Los goles a favor van un poco por encima de la línea y los de en contra por debajo,
        # para que no se tapen cuando caen en el mismo minuto
        y = fila.jornada - 0.18 if fila.sentido == "Favor" else fila.jornada + 0.18
        ax.scatter(x, y, s=95, color=colores[fila.inicio], marker="o" if fila.sentido == "Favor" else "X",
                   edgecolor="white", lw=0.8, zorder=3)
    etiquetas = [f"J{j} · {goles.loc[goles['jornada'] == j, 'rival_corto'].iloc[0]}" for j in jornadas]
    ax.set_yticks(jornadas, etiquetas)
    ax.invert_yaxis()                                     # la jornada 1 arriba, como en un calendario
    ax.set_xlim(0, 97)
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_xlabel("Minuto (el descuento se dibuja al final de cada parte)")
    for x in (45, 90):
        ax.axvline(x, color=GRIS, lw=1, ls=":")           # descanso y final
    # La leyenda la monto a mano con Line2D porque mezcla dos cosas a la vez:
    # colores (tipo de jugada) y formas (a favor o en contra)
    elementos = [Line2D([], [], marker="o", ls="", color=c, markersize=8, label=INICIOS[k])
                 for k, c in colores.items() if k in set(goles["inicio"])]
    elementos += [Line2D([], [], marker="o", ls="", color=TINTA_SUAVE, markersize=8, label="A favor"),
                  Line2D([], [], marker="X", ls="", color=TINTA_SUAVE, markersize=8, label="En contra")]
    ax.legend(handles=elementos, loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=4, fontsize=8.5)
    ax.set_title(f"Los {len(goles)} goles de liga, minuto a minuto")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    guardar(fig, nombre)


def tipo_por_sentido(goles, nombre):
    """Barras apiladas al 100 %: qué parte de los goles sale de cada tipo de jugada.

    Como el Zaragoza ha marcado 16 y encajado 10, comparar cantidades engaña;
    en porcentaje las dos barras miden lo mismo y se ve el reparto. Dentro de
    cada tramo pongo el número real de goles para no perder la referencia.
    """
    t = conteo(goles, "inicio", INICIOS)
    pct = t / t.sum() * 100                   # t.sum() suma por columnas: total a favor y en contra
    colores = ["#3f8f5c", "#2b6cb0", "#d69e2e", "#805ad5", GRIS]
    fig, ax = plt.subplots(figsize=(9, 2.8))
    izquierda = np.zeros(2)                   # dónde empieza el siguiente tramo de cada barra
    for (tipo, fila), c in zip(pct.iterrows(), colores):
        ax.barh(["En contra", "A favor"], fila[["Contra", "Favor"]].values, left=izquierda,
                color=c, label=tipo, height=0.55)
        for i, v in enumerate(fila[["Contra", "Favor"]].values):
            if v >= 8:                        # en tramos muy estrechos el número no cabe
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
    """Barras apiladas por jugador: goles más últimos pases en los goles a favor.

    El gol en propia puerta no cuenta para nadie del Zaragoza, así que lo quito.
    """
    favor = goles[goles["sentido"] == "Favor"]
    g = favor[~favor["remate"].eq("propia_puerta")]["goleador"].value_counts()   # ~ = «no»
    a = favor["asistencia"].dropna().value_counts()
    t = pd.DataFrame({"Goles": g, "Asistencias": a}).fillna(0).astype(int)
    t["Total"] = t.sum(axis=1)
    t = t.sort_values(["Total", "Goles"], ascending=True)   # el que más participa, arriba
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(t) + 1.2))
    ax.barh(t.index, t["Goles"], color=AZUL, label="Goles")
    ax.barh(t.index, t["Asistencias"], left=t["Goles"], color=AZUL_CLARO, label="Último pase")
    for i, (_, fila) in enumerate(t.iterrows()):
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
    """xG frente a goles, partido a partido y acumulado.

    El xG (goles esperados) es la suma de la probabilidad de gol de cada tiro
    según el modelo de Sofascore. Si las barras (xG) y los puntos (goles) se
    parecen, el equipo marca más o menos lo que genera; si los goles van muy por
    encima, está teniendo acierto (o suerte) por encima de lo normal.
    """
    s = sofa.merge(partidos[["partido_id", "jornada", "rival", "goles_favor", "goles_contra"]], on="partido_id")
    s["rival_corto"] = s["rival"].map(NOMBRES_CORTOS).fillna(s["rival"])
    x = np.arange(len(s))
    # Dos paneles: el de la izquierda más ancho (partido a partido) y el acumulado a la derecha
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.5, 4.6), gridspec_kw={"width_ratios": [1.8, 1]})
    ax.bar(x - 0.2, s["xg_zgz"], 0.38, color=AZUL_CLARO, label="xG Zaragoza")
    ax.bar(x + 0.2, s["xg_rival"], 0.38, color=NARANJA_CLARO, label="xG rival")
    # Los goles del Zaragoza, con su círculo azul y blanco
    ax.plot(x - 0.2, s["goles_favor"], marker="o", markersize=8, fillstyle="left", markerfacecolor=AZUL,
            markerfacecoloralt="white", markeredgecolor=AZUL, ls="", zorder=3, label="Goles Zaragoza")
    ax.scatter(x + 0.2, s["goles_contra"], color=NARANJA, zorder=3, s=40, label="Goles rival")
    ax.set_xticks(x, [f"J{j}\n{r}" for j, r in zip(s["jornada"], s["rival_corto"])], fontsize=8.5)
    ax.set_ylim(0, max(s[["xg_zgz", "xg_rival", "goles_favor", "goles_contra"]].max()) + 1.1)
    ax.set_title("xG y goles por partido")
    ax.legend(loc="upper center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, -0.2))
    # Acumulado: cumsum() va sumando partido a partido. Línea continua para los
    # goles y discontinua para el xG del mismo equipo
    j = s["jornada"]
    ax2.plot(j, s["xg_zgz"].cumsum(), color=AZUL, ls="--", label="xG a favor")
    ax2.plot(j, s["goles_favor"].cumsum(), color=AZUL, label="Goles a favor")
    ax2.plot(j, s["xg_rival"].cumsum(), color=NARANJA, ls="--", label="xG en contra")
    ax2.plot(j, s["goles_contra"].cumsum(), color=NARANJA, label="Goles en contra")
    ax2.set_xticks(j, [f"J{v}" for v in j])
    ax2.set_title("Acumulado")
    ax2.legend(fontsize=8)
    guardar(fig, nombre)


def tiros_y_area(sofa, partidos, nombre):
    """Tiros de cada equipo separados en dentro y fuera del área (barras apiladas).
    Un tiro desde dentro del área tiene, de media, muchas más opciones de gol."""
    s = sofa.merge(partidos[["partido_id", "jornada", "rival"]], on="partido_id")
    s["rival_corto"] = s["rival"].map(NOMBRES_CORTOS).fillna(s["rival"])
    x = np.arange(len(s))
    fig, ax = plt.subplots(figsize=(10, 4))
    # bottom= apila la segunda barra encima de la primera
    ax.bar(x - 0.2, s["tiros_dentro_area_zgz"], 0.38, color=AZUL, label="Zaragoza, dentro del área")
    ax.bar(x - 0.2, s["tiros_fuera_area_zgz"], 0.38, bottom=s["tiros_dentro_area_zgz"],
           color=AZUL_CLARO, label="Zaragoza, fuera del área")
    ax.bar(x + 0.2, s["tiros_dentro_area_rival"], 0.38, color=NARANJA, label="Rival, dentro del área")
    ax.bar(x + 0.2, s["tiros_fuera_area_rival"], 0.38, bottom=s["tiros_dentro_area_rival"],
           color=NARANJA_CLARO, label="Rival, fuera del área")
    ax.set_xticks(x, [f"J{j}\n{r}" for j, r in zip(s["jornada"], s["rival_corto"])], fontsize=8.5)
    ax.set_title("Tiros: cuántos desde dentro del área (Sofascore)")
    ax.legend(ncol=2, fontsize=8)
    guardar(fig, nombre)


def xg_por_tiro(sofa, partidos, nombre):
    """xG por tiro (xG total / número de tiros): la calidad media de cada disparo.

    Es una forma sencilla de separar «tirar mucho» de «tirar bien». Un 0,10 es
    un tiro con un 10 % de probabilidad de gol de media.
    """
    s = sofa.merge(partidos[["partido_id", "jornada", "rival"]], on="partido_id")
    s["rival_corto"] = s["rival"].map(NOMBRES_CORTOS).fillna(s["rival"])
    zgz = s["xg_zgz"] / s["tiros_zgz"]
    riv = s["xg_rival"] / s["tiros_rival"]
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(s["jornada"], zgz, color=AZUL, label="Real Zaragoza")
    ax.plot(s["jornada"], riv, marker="o", color=NARANJA, label="Rival")
    # Los puntos del Zaragoza, otra vez con el círculo azul y blanco
    ax.plot(s["jornada"], zgz, marker="o", markersize=8, fillstyle="left", markerfacecolor=AZUL,
            markerfacecoloralt="white", markeredgecolor=AZUL, ls="", zorder=3)
    for xj, a, b in zip(s["jornada"], zgz, riv):
        # La etiqueta del valor más alto va encima del punto y la del otro debajo, para que no choquen
        arriba = max(a, b)
        for valor, color in ((a, AZUL), (b, NARANJA)):
            dy = 0.012 if valor == arriba else -0.03
            ax.text(xj, valor + dy, f"{valor:.2f}".replace(".", ","), ha="center", fontsize=8, color=color)
    ax.set_xticks(s["jornada"], [f"J{j}\n{r}" for j, r in zip(s["jornada"], s["rival_corto"])], fontsize=8.5)
    ax.set_ylim(0, max(zgz.max(), riv.max()) + 0.08)
    ax.set_title("xG por tiro: calidad media de cada disparo")
    ax.legend()
    guardar(fig, nombre)


def juego_y_duelos(sofa, partidos, nombre):
    """Cuatro pequeños gráficos (small multiples) con el estilo de juego:
    posesión, centros, duelos ganados y entradas en el último tercio.
    La última métrica Sofascore solo la da desde la jornada 6."""
    s = sofa.merge(partidos[["partido_id", "jornada"]], on="partido_id")
    j = s["jornada"]
    # sharex=True: los cuatro paneles comparten el eje de jornadas
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.4), sharex=True)

    ax = axes[0, 0]
    ax.bar(j, s["posesion_pct_zgz"], color=AZUL)
    ax.axhline(50, color=GRIS, ls=":")          # referencia del 50 %
    ax.set_title("Posesión (%)")
    ax.set_ylim(0, 100)

    ax = axes[0, 1]
    ax.bar(j - 0.2, s["centros_total_zgz"], 0.38, color=AZUL_CLARO, label="Intentados")
    ax.bar(j + 0.2, s["centros_ok_zgz"], 0.38, color=AZUL, label="Buenos")
    ax.set_title("Centros del Zaragoza")
    ax.legend(fontsize=8)

    ax = axes[1, 0]
    ax.plot(j, s["duelos_ganados_pct_zgz"], color=AZUL)
    ax.plot(j, s["duelos_ganados_pct_zgz"], marker="o", markersize=8, fillstyle="left",
            markerfacecolor=AZUL, markerfacecoloralt="white", markeredgecolor=AZUL, ls="")
    ax.axhline(50, color=GRIS, ls=":")
    ax.set_title("Duelos ganados (%)")
    ax.set_ylim(30, 70)

    ax = axes[1, 1]
    if "entradas_ultimo_tercio_zgz" in s:       # por si en otra temporada no existe la columna
        ax.bar(j - 0.2, s["entradas_ultimo_tercio_zgz"], 0.38, color=AZUL, label="Zaragoza")
        ax.bar(j + 0.2, s["entradas_ultimo_tercio_rival"], 0.38, color=NARANJA, label="Rival")
        ax.legend(fontsize=8, loc="upper left")   # arriba a la izquierda no tapa las barras
    ax.set_title("Entradas en el último tercio (solo J6 y J7)")

    for a in axes[1]:
        a.set_xticks(j, [f"J{v}" for v in j])
    fig.suptitle("Cómo juega el Zaragoza, partido a partido (Sofascore)", x=0.02, ha="left",
                 fontweight="bold", fontsize=13)
    fig.tight_layout()                          # recoloca los paneles para que no se solapen
    guardar(fig, nombre)


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    goles, sofa_largo, oficiales, partidos = cargar()
    comprobar(goles, oficiales)
    sofa = sofascore_ancho(sofa_largo)

    # Tablas resumen, para quien quiera los números sin mirar los gráficos.
    # Las guardo en UTF-8 con BOM (utf-8-sig) para que Excel enseñe bien las tildes.
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

    # Gráficos (cada función guarda su PNG)
    barras_espejo(tablas["inicio"], "Cómo empieza la jugada de cada gol",
                  f"Goles de liga, jornadas 1 a {goles['jornada'].max()}", "inicio.png")
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

    # Un pequeño resumen por pantalla, para comprobar de un vistazo que todo cuadra
    favor = goles[goles["sentido"] == "Favor"]
    contra = goles[goles["sentido"] == "Contra"]
    print(f"Goles vistos: {len(goles)} ({len(favor)} a favor y {len(contra)} en contra)")
    print("Inicio de la jugada:\n", tablas["inicio"])
    print("Carril:\n", tablas["carril"])
    print(f"xG total: {sofa['xg_zgz'].sum():.2f} a favor y {sofa['xg_rival'].sum():.2f} en contra")
    print(f"Gráficos en {GRAFICOS}")


if __name__ == "__main__":
    main()
