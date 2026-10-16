"""
Gráficas de la simulación, con la adaptación azul y blanca del Real Zaragoza.

    01 · dónde puede acabar el Zaragoza: probabilidad de cada puesto final
    02 · los 20 equipos: ascenso directo, playoff, zona media y descenso
    03 · cómo ha cambiado la previsión del Zaragoza jornada a jornada
    04 · los 20 equipos en formato horizontal (Facebook, LinkedIn y web)
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from matplotlib.patches import Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun"))
from estilo import cierre, colores, estilo_ejes, guardar, lienzo, portada  # noqa: E402
from pagina import credito_corto  # noqa: E402

PALETA = "zaragoza"
EQUIPO = "Real Zaragoza"


def _pie(jornada, n):
    simulaciones = f"{n:,}".replace(",", ".")
    return (f"Primera Federación 2026/27, grupo 2 · Tras la jornada {jornada} · Resultados oficiales\n"
            f"Modelo de Poisson con ataque, defensa y ventaja local · {simulaciones} simulaciones")


def _zonas(c):
    """Colores de las cuatro zonas de la tabla."""
    return {"ascenso_directo": c["noche"], "playoff": "#5b7fd1", "medio": "#d6e0f0", "descenso": "#8a96ab"}


def _pct(valor):
    return f"{valor * 100:.0f} %"


def crear_figuras(tabla, distribucion, evolucion, jornada, n, carpeta):
    c = colores(PALETA)
    zonas = _zonas(c)
    fila = tabla[tabla.equipo == EQUIPO].iloc[0]

    # 01 y 05 · Puesto final del Zaragoza ---------------------------------------
    def puesto(formato, nombre):
        vertical = formato == "instagram"
        titulo = "¿Dónde acabará\nel Real Zaragoza?" if vertical else "¿Dónde acabará el Real Zaragoza?"
        separador = "\n" if vertical else " "
        simulaciones = f"{n:,}".replace(",", ".")
        fig, area = lienzo(formato, titulo,
                           f"Probabilidad de cada puesto final según {simulaciones} simulaciones{separador}del resto de la temporada.",
                           pie=_pie(jornada, n), etiqueta="Investigación 03 · Grupo 2", paleta=PALETA,
                           lectura=f"Ascenso directo: {_pct(fila.ascenso_directo)} · Playoff: {_pct(fila.playoff)} · "
                                   f"Descenso: {_pct(fila.descenso)}{separador if vertical else ' · '}"
                                   f"Puntos finales: entre {fila.puntos_p10:.0f} y {fila.puntos_p90:.0f} en 8 de cada 10 simulaciones.")
        ax = fig.add_axes(area)
        puestos = np.arange(1, 21)
        valores = distribucion.loc[EQUIPO].values
        color = [zonas["ascenso_directo"] if p == 1 else zonas["playoff"] if p <= 5 else
                 zonas["descenso"] if p >= 16 else zonas["medio"] for p in puestos]
        ax.bar(puestos, valores * 100, color=color, width=0.75)
        for p, v in zip(puestos, valores):
            if v >= 0.03:
                ax.text(p, v * 100 + 0.4, f"{v * 100:.0f}", ha="center", fontsize=12, color=c["tinta"], fontweight=600)
        ax.set_xticks(puestos)
        ax.set_xlabel("Puesto final", fontsize=12, labelpad=8)
        ax.set_ylabel("Probabilidad (%)", fontsize=12)
        ax.set_ylim(0, valores.max() * 100 * 1.25)
        estilo_ejes(ax, PALETA, rejilla="y")
        for x0, x1, texto in ((0.5, 1.5, "Ascenso"), (1.5, 5.5, "Playoff"), (15.5, 20.5, "Descenso")):
            ax.axvspan(x0, x1, color=c["acento_suave"], alpha=0.5, zorder=0)
            ax.text((x0 + x1) / 2, valores.max() * 100 * 1.18, texto, ha="center", fontsize=12,
                    fontweight=700, color=c["tinta_suave"])
        guardar(fig, carpeta, nombre)

    puesto("instagram", "01_puesto_zaragoza_instagram")
    for formato in ("facebook", "linkedin", "web"):
        puesto(formato, f"05_puesto_zaragoza_{formato}")

    # 02 y 04 · Los 20 equipos ----------------------------------------------------
    def veinte(formato, nombre, titulo, subtitulo, tam):
        fig, area = lienzo(formato, titulo, subtitulo, pie=_pie(jornada, n), etiqueta="Investigación 03 · Grupo 2",
                           paleta=PALETA,
                           lectura="Ordenados por los puntos medios al final de la temporada. "
                                   "Ascenso directo: 1.º · Playoff: 2.º a 5.º · Descenso: 16.º a 20.º")
        area[0] += 0.20 if formato == "instagram" else 0.13
        area[2] -= 0.20 if formato == "instagram" else 0.13
        ax = fig.add_axes(area)
        orden = tabla.iloc[::-1]
        y = np.arange(len(orden))
        izquierda = np.zeros(len(orden))
        medio = 1 - orden.ascenso_directo - orden.playoff - orden.descenso
        for clave, valores_zona in (("ascenso_directo", orden.ascenso_directo), ("playoff", orden.playoff),
                                    ("medio", medio), ("descenso", orden.descenso)):
            ax.barh(y, valores_zona * 100, left=izquierda * 100, color=zonas[clave], height=0.72,
                    edgecolor=c["papel"], linewidth=0.6)
            izquierda += valores_zona.values
        ax.set_yticks(y, orden.equipo, fontsize=tam)
        for etiqueta in ax.get_yticklabels():
            etiqueta.set_color(c["tinta"])
            if etiqueta.get_text() == EQUIPO:
                etiqueta.set_fontweight(700)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Probabilidad (%)", fontsize=12)
        estilo_ejes(ax, PALETA, rejilla=None)
        ax.spines["left"].set_visible(False)
        leyenda = [("Ascenso directo", "ascenso_directo"), ("Playoff", "playoff"), ("Zona media", "medio"),
                   ("Descenso", "descenso")]
        for k, (texto, clave) in enumerate(leyenda):
            ax.add_patch(Rectangle(
                (k * 25, len(orden) - 0.1), 3, 0.6, color=zonas[clave], clip_on=False))
            ax.text(k * 25 + 4, len(orden) + 0.2, texto, fontsize=tam, va="center", color=c["tinta"])
        guardar(fig, carpeta, nombre)

    veinte("instagram", "02_veinte_equipos_instagram", "Cómo puede acabar\nel grupo 2",
           "Probabilidad de cada equipo de acabar en cada zona de la tabla.", 12)
    for formato in ("linkedin", "web"):
        veinte(formato, f"04_veinte_equipos_{formato}", "Cómo puede acabar el grupo 2",
               f"Primera Federación 2026/27 · Probabilidades tras la jornada {jornada}", 11)

    # 03 · Evolución del Zaragoza --------------------------------------------------
    fig, area = lienzo("instagram", "Jornada a jornada",
                       "Probabilidad del Real Zaragoza de ascender directamente\n"
                       "y de acabar entre los cinco primeros, con los datos de cada momento.",
                       pie=_pie(jornada, n), etiqueta="Investigación 03 · Grupo 2", paleta=PALETA,
                       lectura="Cada punto repite la simulación solo con los resultados disponibles en esa jornada.")
    ax = fig.add_axes(area)
    ax.plot(evolucion.jornada, evolucion.ascenso_o_playoff * 100, color=c["principal"], lw=3.5, marker="o",
            markersize=10, label="Entre los cinco primeros")
    ax.plot(evolucion.jornada, evolucion.ascenso_directo * 100, color=c["noche"], lw=3.5, marker="o",
            markersize=10, linestyle="--", label="Ascenso directo (1.º)")
    for serie in ("ascenso_o_playoff", "ascenso_directo"):
        for x, v in zip(evolucion.jornada, evolucion[serie]):
            ax.text(x, v * 100 + 2.5, f"{v * 100:.0f} %", ha="center", fontsize=12, color=c["tinta"], fontweight=600)
    ax.set_xticks(evolucion.jornada, [f"J{j}" for j in evolucion.jornada])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Probabilidad (%)", fontsize=12)
    estilo_ejes(ax, PALETA, rejilla="y")
    ax.legend(frameon=False, fontsize=12, loc="upper left")
    guardar(fig, carpeta, "03_evolucion_zaragoza_instagram")


def crear_carrusel(tabla, jornada, carpeta_graficos, carpeta):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    fila = tabla[tabla.equipo == EQUIPO].iloc[0]
    recursos = Path(__file__).resolve().parents[1] / "recursos"
    foto = json.loads((recursos / "foto.json").read_text(encoding="utf-8"))
    fig = portada("Probabilidades de ascenso\ndel grupo 2 de\nPrimera Federación",
                  cifra=_pct(fila.ascenso_o_playoff),
                  cifra_texto=f"de que el Real Zaragoza acabe entre\nlos cinco primeros, tras la jornada {jornada}",
                  etiqueta="Investigación 03 · Grupo 2", paleta=PALETA,
                  antetitulo="Real Zaragoza · 10.000 simulaciones",
                  foto=recursos / "foto.jpg", credito=credito_corto(foto), foco=(0.5, 0.6))
    guardar(fig, carpeta, "01_portada")
    for origen, destino in (("01_puesto_zaragoza_instagram", "02_puesto"), ("02_veinte_equipos_instagram", "03_grupo"),
                            ("03_evolucion_zaragoza_instagram", "04_evolucion")):
        for extension in ("png", "svg"):
            shutil.copy(Path(carpeta_graficos) / f"{origen}.{extension}", carpeta / f"{destino}.{extension}")
    fig = cierre("Lo que la\nsimulación no sabe",
                 ["No sabe de lesiones, fichajes\nni cambios de entrenador.",
                  f"Con {jornada} jornadas, la fuerza de\ncada equipo todavía es muy incierta.",
                  "Supone que los goles de cada\nequipo son independientes.",
                  "Probabilidad no es pronóstico:\nun 20 % pasa una de cada cinco veces."],
                 paleta=PALETA)
    guardar(fig, carpeta, "05_limites")
