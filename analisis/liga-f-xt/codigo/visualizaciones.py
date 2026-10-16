"""
Gráficas del estudio de xT con la identidad de Línea de pase.

El estilo (colores, tipografías, cabecera y pie) sale de analisis/comun/estilo.py,
el mismo para todas las investigaciones. Aquí solo se decide qué se dibuja:

    01 · las diez jugadoras con más xT neto por 90 minutos, con su intervalo
    02 · la superficie de xT: cuánto vale tener el balón en cada zona
    03 · volumen frente a eficiencia: muchas acciones no es lo mismo que mucho valor
    04 · la gráfica principal adaptada a Facebook, LinkedIn y la web

Además, crear_carrusel() monta el carrusel de Instagram con una portada y un
cierre de límites alrededor de las tres primeras gráficas.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, PowerNorm

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun"))
from estilo import cierre, colores, estilo_ejes, guardar, lienzo, portada  # noqa: E402
from pagina import credito_corto  # noqa: E402

PIE = "Liga F 2023/24 · Fuente: StatsBomb Open Data\nModelo propio de xT (12 × 8 zonas) · Mínimo 900 minutos · Sin tracking"
ETIQUETA = "Investigación 01 · Liga F"


def _ranking(ax, tabla, c, tam_etiqueta=13, con_equipo=True):
    """Puntos con su intervalo bootstrap; la primera jugadora en naranja."""
    posiciones = np.arange(len(tabla))
    lider = tabla.xt_neto_90.idxmax()
    color_punto = [c["acento"] if i == lider else c["principal"] for i in tabla.index]
    ax.hlines(posiciones, tabla.ic95_inferior, tabla.ic95_superior, color=c["apagado"], linewidth=4,
              capstyle="round")
    ax.scatter(tabla.xt_neto_90, posiciones, s=110, color=color_punto, zorder=3,
               edgecolor=c["papel"], linewidth=1.5)
    if con_equipo:
        etiquetas = [f"{r.jugadora}\n{r.equipo}" for r in tabla.itertuples()]
    else:
        etiquetas = list(tabla.jugadora)
    ax.set_yticks(posiciones, etiquetas, fontsize=tam_etiqueta, linespacing=1.3)
    for etiqueta in ax.get_yticklabels():
        etiqueta.set_color(c["tinta"])
    ax.set_xlabel("xT neto por 90 minutos", fontsize=12, labelpad=10)
    estilo_ejes(ax, rejilla="x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", pad=12)


def crear_figuras(ranking, modelo, puntos, logo, carpeta):
    c = colores()
    elegibles = ranking[ranking.elegible_900].head(10).iloc[::-1]

    # 01 · Ranking principal --------------------------------------------------
    fig, area = lienzo("instagram", "Quién acerca el balón\na las zonas de peligro",
                       "xT neto por 90 minutos en pases completados y conducciones.\n"
                       "Cada partido se valora con un modelo ajustado en los demás.",
                       pie=PIE, etiqueta=ETIQUETA, logo_fuente=logo,
                       lectura="Línea: intervalo bootstrap del 95 % entre los partidos de cada jugadora.\n"
                               "Ocho de las diez juegan en el Barcelona: el equipo también cuenta.")
    area[0] += 0.24
    area[2] -= 0.24
    ax = fig.add_axes(area)
    _ranking(ax, elegibles, c)
    guardar(fig, carpeta, "01_creadoras_xt_instagram")

    # 02 · Superficie de xT ---------------------------------------------------
    fig, area = lienzo("instagram", "El valor depende\nde dónde está el balón",
                       "Probabilidad de que la jugada acabe en gol desde cada zona.\n"
                       "Ajustado con toda la temporada para explicar el método.",
                       pie=PIE, etiqueta=ETIQUETA, logo_fuente=logo,
                       lectura="xT de una acción completada = valor del destino − valor del origen.\n"
                               "No mide los movimientos sin balón ni la calidad de la decisión.")
    # El campo ocupa todo el ancho; la escala de color va debajo.
    ancho_campo = area[2] * 0.94
    alto_campo = ancho_campo * (80 / 120) * fig.get_figwidth() / fig.get_figheight()
    y_campo = area[1] + 0.085
    ax = fig.add_axes([area[0] + (area[2] - ancho_campo) / 2, y_campo, ancho_campo, alto_campo])
    mapa = LinearSegmentedColormap.from_list("cesped", ["#e8f0e9", "#9cc5a8", c["principal"], c["noche"]])
    valores = modelo["valor"].reshape(modelo["ny"], modelo["nx"])
    # Escala con raíz cuadrada: casi todo el valor está cerca de la portería y,
    # con una escala lineal, el resto del campo se vería del mismo color.
    imagen = ax.imshow(valores, origin="upper", extent=[0, 120, 80, 0], cmap=mapa, aspect="equal",
                       norm=PowerNorm(gamma=0.5, vmin=0, vmax=valores.max()))
    linea = dict(color=c["cal"], lw=2, alpha=0.9)
    ax.plot([0, 120, 120, 0, 0], [0, 0, 80, 80, 0], **linea)
    ax.plot([60, 60], [0, 80], **linea)
    ax.add_patch(plt.Circle((60, 40), 9.15, fill=False, **linea))
    for lado in (0, 120):
        signo = 1 if lado == 0 else -1
        ax.plot([lado, lado + 18 * signo, lado + 18 * signo, lado], [18, 18, 62, 62], **linea)
        ax.plot([lado, lado + 6 * signo, lado + 6 * signo, lado], [30, 30, 50, 50], **linea)
    ax.set_xlim(-1, 121)
    ax.set_ylim(81, -1)
    ax.axis("off")
    fig.text(area[0], y_campo + alto_campo + 0.012, "Dirección de ataque  →", fontsize=15,
             fontweight=700, color=c["acento_texto"])
    barra = fig.add_axes([area[0] + 0.2, area[1] + 0.02, area[2] - 0.4, 0.012])
    leyenda = fig.colorbar(imagen, cax=barra, orientation="horizontal")
    leyenda.outline.set_visible(False)
    leyenda.ax.tick_params(labelsize=11, length=0)
    leyenda.set_label("Valor de la zona (probabilidad de gol)", fontsize=12, labelpad=8)
    guardar(fig, carpeta, "02_superficie_xt_instagram")

    # 03 · Volumen frente a eficiencia ----------------------------------------
    fig, area = lienzo("instagram", "Más balón no siempre\nes más peligro",
                       "Cada punto es una jugadora con al menos 900 minutos.\n"
                       "Eje horizontal: cuántas veces lo intenta. Vertical: cuánto valor suma.",
                       pie=PIE, etiqueta=ETIQUETA, logo_fuente=logo,
                       lectura="El volumen depende del puesto y del equipo.\n"
                               "Este gráfico no ajusta por posesión, rival ni marcador.")
    area[0] += 0.03
    area[2] -= 0.03
    ax = fig.add_axes(area)
    todas = ranking[ranking.elegible_900]
    volumen = todas.acciones / todas.minutos * 90
    ax.scatter(volumen, todas.xt_neto_90, s=46, color=c["principal"], alpha=0.45, edgecolors="none")
    destacadas = todas.head(4)
    ax.scatter(destacadas.acciones / destacadas.minutos * 90, destacadas.xt_neto_90, s=80,
               color=c["acento"], zorder=3, edgecolor=c["papel"], linewidth=1.2)
    for r in destacadas.itertuples():
        ax.annotate(r.jugadora, (r.acciones / r.minutos * 90, r.xt_neto_90), xytext=(8, 4),
                    textcoords="offset points", fontsize=12, color=c["tinta"], fontweight=600)
    ax.set_xlabel("Pases y conducciones intentados por 90 minutos", fontsize=12, labelpad=10)
    ax.set_ylabel("xT neto por 90 minutos", fontsize=13, labelpad=10)
    estilo_ejes(ax, rejilla="both")
    ax.margins(x=0.12, y=0.06)
    guardar(fig, carpeta, "03_volumen_eficiencia_instagram")

    # 04 · Adaptaciones horizontales ------------------------------------------
    seis = elegibles.tail(6)
    for formato in ("facebook", "linkedin", "web"):
        fig, area = lienzo(formato, "Crear peligro antes del tiro",
                           "Liga F 2023/24 · xT neto por 90 minutos · mínimo 900 minutos",
                           pie="Fuente: StatsBomb Open Data · Intervalo: bootstrap del 95 % por partidos, modelo fijo\n"
                               "Exploratorio: no ajusta por contexto táctico ni mide la aportación sin balón",
                           etiqueta=ETIQUETA, logo_fuente=logo)
        area[0] += 0.20
        area[2] -= 0.20
        ax = fig.add_axes(area)
        _ranking(ax, seis, c, tam_etiqueta=12 if formato == "facebook" else 14, con_equipo=False)
        guardar(fig, carpeta, f"04_creadoras_xt_{formato}")


def crear_carrusel(ranking, carpeta_graficos, carpeta):
    """Carrusel de Instagram: portada, tres gráficas y cierre con los límites."""
    import json
    import shutil

    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    lider = ranking[ranking.elegible_900].iloc[0]
    cifra = f"{lider.xt_neto_90:.2f}".replace(".", ",")
    recursos = Path(__file__).resolve().parents[1] / "recursos"
    foto = json.loads((recursos / "foto.json").read_text(encoding="utf-8"))
    fig = portada("Quién crea más peligro\ncon el balón en la Liga F",
                  cifra=cifra,
                  cifra_texto=f"xT neto por 90 minutos de\n{lider.jugadora}, la más alta\n(mínimo 900 minutos)",
                  etiqueta=ETIQUETA, antetitulo="Liga F 2023/24 · Amenaza esperada (xT)",
                  foto=recursos / "foto.jpg", credito=credito_corto(foto), foco=(0.5, 0.35))
    guardar(fig, carpeta, "01_portada")
    for origen, destino in [("02_superficie_xt_instagram", "02_como_funciona"),
                            ("01_creadoras_xt_instagram", "03_resultados"),
                            ("03_volumen_eficiencia_instagram", "04_volumen")]:
        for extension in ("png", "svg"):
            shutil.copy(Path(carpeta_graficos) / f"{origen}.{extension}", carpeta / f"{destino}.{extension}")
    fig = cierre("Lo que este\nestudio no dice",
                 ["No es una nota de calidad:\nmide la progresión con balón.",
                  "No ajusta por el equipo,\nel rival ni el marcador.",
                  "No ve las carreras sin balón\nni la posición de las defensas.",
                  "Es la temporada 2023/24,\nno la actual."])
    guardar(fig, carpeta, "05_limites")
