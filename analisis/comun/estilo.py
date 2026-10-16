"""
Estilo común de las gráficas de Línea de pase.

Todas las investigaciones nuevas dibujan con estas piezas para que una gráfica
de Instagram, una de LinkedIn y la web parezcan de la misma casa: los colores
salen de assets/estilo.css (verde césped, blanco cal y el naranja del balón
como único acento) y las tipografías son las de la web, Big Shoulders Display
para los titulares y Archivo para el texto.

Uso básico:

    from estilo import lienzo, guardar
    fig, area = lienzo("instagram", "Título", "Subtítulo",
                       pie="Liga F 2023/24 · Fuente: StatsBomb Open Data")
    ax = fig.add_axes(area)
    ...
    guardar(fig, carpeta, "nombre")      # escribe nombre.png y nombre.svg

Para el Real Zaragoza se usa paleta="zaragoza", la adaptación azul y blanca
que ya tiene su sección en la web (assets/real-zaragoza.css).
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from PIL import Image

CARPETA = Path(__file__).resolve().parent
RAIZ_WEB = CARPETA.parents[1]

# ---------------------------------------------------------------------------
# Colores (los mismos nombres que las variables de assets/estilo.css)
# ---------------------------------------------------------------------------
PALETAS = {
    "web": {
        "papel": "#f7f9f5",
        "panel": "#ffffff",
        "tinta": "#0f2418",
        "tinta_suave": "#4d6356",
        "linea": "#dbe3dc",
        "principal": "#1f6b3e",      # verde césped
        "noche": "#0f3d25",          # fondo de la cabecera
        "franja": "#14492d",         # franjas del corte del césped
        "cal": "#f4f7f1",            # texto sobre el césped
        "acento": "#ff6a2b",         # naranja del balón: solo para destacar
        "acento_texto": "#c2410c",   # el mismo naranja, legible sobre blanco
        "acento_suave": "#ffe3d5",
        "apagado": "#b8c4bb",
    },
    "zaragoza": {
        "papel": "#f5f8fd",
        "panel": "#ffffff",
        "tinta": "#0f1f3a",
        "tinta_suave": "#4b607e",
        "linea": "#d6e0f0",
        "principal": "#213e96",
        "noche": "#142e7c",
        "franja": "#1b3788",
        "cal": "#ffffff",
        "acento": "#213e96",
        "acento_texto": "#213e96",
        "acento_suave": "#e6eaf7",
        "apagado": "#b1bfd2",
    },
}

# Tamaños en píxeles de cada formato (a 100 ppp).
FORMATOS = {
    "instagram": (1080, 1350),
    "facebook": (1200, 630),
    "linkedin": (1600, 900),
    "web": (1600, 900),
}

PX = 100 / 72   # píxeles por punto tipográfico a 100 ppp

TITULAR = "Big Shoulders Display"
TEXTO = "Archivo"


def registrar_fuentes():
    """Da de alta en Matplotlib las fuentes guardadas en comun/fuentes."""
    for archivo in (CARPETA / "fuentes").glob("*.ttf"):
        font_manager.fontManager.addfont(str(archivo))


def colores(paleta="web"):
    return PALETAS[paleta]


def preparar(paleta="web"):
    """Ajustes generales de Matplotlib para que los ejes sigan la identidad."""
    registrar_fuentes()
    c = colores(paleta)
    plt.rcParams.update({
        "font.family": TEXTO,
        "font.size": 11,
        "text.color": c["tinta"],
        "axes.labelcolor": c["tinta_suave"],
        "axes.edgecolor": c["linea"],
        "axes.facecolor": c["papel"],
        "xtick.color": c["tinta_suave"],
        "ytick.color": c["tinta_suave"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "path",       # el SVG lleva las letras dibujadas: se ve igual sin las fuentes instaladas
    })
    return c


def estilo_ejes(ax, paleta="web", rejilla="x"):
    """Ejes limpios: sin marco superior ni derecho y con una rejilla suave."""
    c = colores(paleta)
    ax.set_facecolor(c["papel"])
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.spines["left"].set_color(c["linea"])
    ax.spines["bottom"].set_color(c["linea"])
    if rejilla:
        ax.grid(axis=rejilla, color=c["linea"], linewidth=0.8)
        ax.set_axisbelow(True)
    ax.tick_params(length=0)
    return ax


def _cabecera(fig, alto_px, alto_banda, c, etiqueta, paleta):
    """Banda superior con el césped a franjas y la marca, como en la web."""
    fraccion = alto_banda / alto_px
    banda = fig.add_axes([0, 1 - fraccion, 1, fraccion])
    banda.set_xlim(0, 1)
    banda.set_ylim(0, 1)
    banda.axis("off")
    banda.add_patch(Rectangle((0, 0), 1, 1, color=c["noche"]))
    # Las franjas del corte del césped ocupan el 7,5 % de cada 15 %.
    for inicio in [i * 0.15 for i in range(7)]:
        banda.add_patch(Rectangle((inicio, 0), 0.075, 1, color=c["franja"]))
    banda.text(0.04, 0.5, "Línea de pase", fontfamily=TITULAR, fontweight=800,
               fontsize=alto_banda * 0.30, color=c["cal"], va="center")
    if etiqueta:
        banda.text(0.96, 0.5, etiqueta.upper(), fontsize=alto_banda * 0.13,
                   fontweight=600, color=c["cal"], alpha=0.85, va="center", ha="right")
    if paleta == "web":
        # Un punto naranja: el balón de la marca.
        banda.scatter([0.025], [0.5], s=alto_banda * 0.9, color=c["acento"], zorder=3)
    return fraccion


def lienzo(formato, titulo, subtitulo="", pie="", etiqueta="", paleta="web",
           logo_fuente=None, lectura=""):
    """
    Crea la figura con cabecera, titular, subtítulo y pie de fuente.

    «lectura» es una nota breve (cómo leer la gráfica o su límite principal) que
    se coloca justo encima del pie, sin pisar los ejes.

    Devuelve la figura y el rectángulo libre [x, y, ancho, alto] (en fracción
    de la figura) donde se dibuja la gráfica. Ese rectángulo ya deja sitio
    debajo para las etiquetas del eje horizontal.
    """
    c = preparar(paleta)
    ancho_px, alto_px = FORMATOS[formato]
    vertical = alto_px > ancho_px
    fig = plt.figure(figsize=(ancho_px / 100, alto_px / 100), dpi=100, facecolor=c["papel"])

    margen = 60 / ancho_px
    banda = _cabecera(fig, alto_px, 86 if vertical else 70, c, etiqueta, paleta)

    # Titular y subtítulo, medidos en píxeles para que no dependan del formato.
    tam_titulo = 52 if vertical else (40 if ancho_px >= 1600 else 34)
    lineas_titulo = titulo.count("\n") + 1
    y = 1 - banda - 34 / alto_px
    fig.text(margen, y, titulo, fontfamily=TITULAR, fontweight=800, fontsize=tam_titulo,
             color=c["tinta"], va="top", linespacing=0.95)
    y -= (lineas_titulo * tam_titulo * PX * 1.12 + 22) / alto_px
    if subtitulo:
        tam_sub = 17 if vertical else 15
        fig.text(margen, y, subtitulo, fontsize=tam_sub, color=c["tinta_suave"], va="top",
                 linespacing=1.45)
        y -= ((subtitulo.count("\n") + 1) * tam_sub * PX * 1.45 + 26) / alto_px

    # Pie: fuente, temporada y método a la izquierda; logo del proveedor a la derecha.
    alto_pie = 92 if vertical else 74
    fig.add_artist(plt.Line2D([margen, 1 - margen], [alto_pie / alto_px] * 2,
                              color=c["linea"], linewidth=1))
    if pie:
        fig.text(margen, (alto_pie - 18) / alto_px, pie, fontsize=11 if vertical else 10,
                 color=c["tinta_suave"], va="top", linespacing=1.55)
    if logo_fuente:
        imagen = Image.open(logo_fuente)
        proporcion = imagen.width / imagen.height
        alto_logo = 34 / alto_px
        ancho_logo = alto_logo * proporcion * alto_px / ancho_px
        ax_logo = fig.add_axes([1 - margen - ancho_logo, (alto_pie - 60) / alto_px,
                                ancho_logo, alto_logo])
        ax_logo.imshow(imagen)
        ax_logo.axis("off")

    suelo = alto_pie + 18
    if lectura:
        tam_lectura = 12 if vertical else 11
        lineas = lectura.count("\n") + 1
        alto_lectura = lineas * tam_lectura * PX * 1.5
        fig.text(margen, (suelo + alto_lectura) / alto_px, lectura, fontsize=tam_lectura,
                 color=c["tinta_suave"], va="top", linespacing=1.5)
        suelo += alto_lectura + 12
    suelo += 62   # sitio para los números y el título del eje horizontal
    area = [margen + 0.01, suelo / alto_px, 1 - 2 * margen - 0.02, y - suelo / alto_px - 16 / alto_px]
    return fig, area


def nota(fig, texto, y_px, paleta="web", tam=11):
    """Texto pequeño de lectura o método, a la altura indicada en píxeles."""
    c = colores(paleta)
    alto_px = fig.get_figheight() * 100
    ancho_px = fig.get_figwidth() * 100
    fig.text(60 / ancho_px, y_px / alto_px, texto, fontsize=tam, color=c["tinta_suave"],
             va="top", linespacing=1.5)


def guardar(fig, carpeta, nombre):
    """Guarda la figura en PNG (redes) y SVG (web), con el fondo del lienzo."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    fig.savefig(carpeta / f"{nombre}.png", dpi=100, facecolor=fig.get_facecolor())
    fig.savefig(carpeta / f"{nombre}.svg", facecolor=fig.get_facecolor())
    plt.close(fig)
    return carpeta / f"{nombre}.png"


# ---------------------------------------------------------------------------
# Diapositivas de texto para los carruseles de Instagram (1080 × 1350)
# ---------------------------------------------------------------------------
def _fondo_cesped(fig, c):
    """Fondo completo de césped a franjas, como la portada de la web."""
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 1, 1, color=c["noche"]))
    for inicio in [i * 0.15 for i in range(7)]:
        ax.add_patch(Rectangle((inicio, 0), 0.075, 1, color=c["franja"]))
    return ax


def portada(titulo, entradilla, cifra="", cifra_texto="", etiqueta="", paleta="web"):
    """Primera diapositiva: titular grande sobre césped y, si hay, la cifra clave."""
    c = preparar(paleta)
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100, facecolor=c["noche"])
    ax = _fondo_cesped(fig, c)
    ax.text(0.06, 0.94, "Línea de pase", fontfamily=TITULAR, fontweight=800, fontsize=30,
            color=c["cal"], va="top")
    if etiqueta:
        ax.text(0.94, 0.935, etiqueta.upper(), fontsize=13, fontweight=600, color=c["cal"],
                alpha=0.85, va="top", ha="right")
    ax.text(0.06, 0.80, titulo, fontfamily=TITULAR, fontweight=800, fontsize=78,
            color=c["cal"], va="top", linespacing=0.92)
    lineas = titulo.count("\n") + 1
    y = 0.80 - lineas * 78 * PX * 1.08 / 1350 - 0.045
    ax.text(0.06, y, entradilla, fontsize=21, color=c["cal"], alpha=0.92, va="top",
            linespacing=1.45)
    if cifra:
        # En la paleta del Zaragoza el acento es el mismo azul del fondo: la cifra va en blanco.
        ax.text(0.06, 0.22, cifra, fontfamily=TITULAR, fontweight=800, fontsize=120,
                color=c["acento"] if paleta == "web" else c["cal"], va="bottom")
        ax.text(0.06, 0.20, cifra_texto, fontsize=18, color=c["cal"], va="top", linespacing=1.45)
    ax.text(0.06, 0.04, "Desliza →", fontsize=16, fontweight=600, color=c["cal"], alpha=0.8)
    return fig


def cierre(titulo, puntos, enlace="lineadepase.github.io", paleta="web"):
    """Última diapositiva: límites del estudio y dónde leerlo completo."""
    c = preparar(paleta)
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100, facecolor=c["papel"])
    _cabecera(fig, 1350, 86, c, "", paleta)
    fig.text(0.06, 0.87, titulo, fontfamily=TITULAR, fontweight=800, fontsize=60,
             color=c["tinta"], va="top", linespacing=0.95)
    y = 0.87 - (titulo.count("\n") + 1) * 60 * PX * 1.05 / 1350 - 0.04
    for punto in puntos:
        fig.text(0.06, y, "—", fontsize=20, color=c["acento_texto"], va="top", fontweight=700)
        fig.text(0.11, y, punto, fontsize=20, color=c["tinta"], va="top", linespacing=1.4)
        y -= ((punto.count("\n") + 1) * 20 * PX * 1.4 + 30) / 1350
    fig.add_artist(Rectangle((0, 0), 1, 0.13, color=c["noche"], transform=fig.transFigure))
    fig.text(0.06, 0.065, "Estudio completo, código y método", fontsize=17, color=c["cal"],
             va="center")
    fig.text(0.94, 0.065, enlace, fontfamily=TITULAR, fontweight=800, fontsize=30,
             color=c["cal"], va="center", ha="right")
    return fig
