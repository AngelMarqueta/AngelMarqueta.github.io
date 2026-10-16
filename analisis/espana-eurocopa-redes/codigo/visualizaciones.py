"""
Gráficas de las redes de pases de España con la identidad de Línea de pase.

    01 · la red de la final, en un campo vertical (ataque hacia arriba)
    02 · las seis redes del torneo, una por partido
    03 · quién unía el juego: intermediación de cada jugadora, partido a partido
    04 · ritmo y concentración del juego en cada partido
    05 · las seis redes en formato horizontal para Facebook, LinkedIn y la web

crear_carrusel() monta el carrusel de Instagram con portada y cierre.
"""
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as efectos
import numpy as np
from mplsoccer import VerticalPitch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comun"))
from estilo import TITULAR, cierre, colores, estilo_ejes, guardar, lienzo, portada  # noqa: E402
from pagina import credito_corto  # noqa: E402

PIE = ("Eurocopa femenina 2025 · Fuente: StatsBomb Open Data\n"
       "Pases completados en juego hasta el primer cambio de España · Elaboración propia")
ETIQUETA = "Investigación 02 · Eurocopa 2025"

# Cómo se conoce a cada jugadora en España (StatsBomb usa el nombre completo y sin algunas tildes).
CORTO = {
    "Adriana Nanclares": "Nanclares", "Aitana Bonmati": "Aitana", "Alexia Putellas": "Alexia",
    "Athenea del Castillo": "Athenea", "Cata Coll": "Cata Coll", "Claudia Pina": "Pina",
    "Cristina Martín-Prieto": "Martín-Prieto", "Esther Gonzalez": "Esther", "Irene Paredes": "Paredes",
    "Jana Fernandez": "Jana", "Laia Aleixandri": "Aleixandri", "Leila Ouahabi": "Ouahabi",
    "Lucía García": "Lucía García", "Maite Zubieta": "Zubieta", "Mariona Caldentey": "Mariona",
    "María Méndez": "Méndez", "Olga Carmona": "Olga", "Ona Batlle": "Ona Batlle",
    "Patri Guijarro": "Patri", "Salma Paralluelo": "Salma", "Vicky López": "Vicky López",
}
COMPLETO = {"Aitana Bonmati": "Aitana Bonmatí", "Esther Gonzalez": "Esther González",
            "Jana Fernandez": "Jana Fernández"}

RIVAL = {"Portugal": "Portugal", "Belgium": "Bélgica", "Italy": "Italia", "Switzerland": "Suiza",
         "Germany": "Alemania", "England": "Inglaterra"}
FASE = {"Group Stage": "Fase de grupos", "Quarter-finals": "Cuartos", "Semi-finals": "Semifinal",
        "Final": "Final"}

MINIMO_PASES = 4   # una conexión se dibuja si la pareja se dio al menos 4 pases


def nombre_completo(nombre):
    return COMPLETO.get(nombre, nombre)


def corto(nombre):
    return CORTO.get(nombre, nombre.split()[-1])


def _campo(c):
    return VerticalPitch(pitch_type="statsbomb", pitch_color=c["noche"], line_color=c["cal"],
                         linewidth=1.2, line_alpha=0.35, stripe=True, stripe_color=c["franja"],
                         pad_top=2, pad_bottom=2, pad_left=2, pad_right=2)


def dibujar_red(ax, pases, tabla, c, escala=1.0, etiquetas=True, minimo=MINIMO_PASES):
    """Dibuja una red sobre un eje con campo vertical ya preparado."""
    pitch = _campo(c)
    pitch.draw(ax=ax)
    parejas = pases.groupby(["pasadora", "receptora"]).size().reset_index(name="n")
    # Se suman los dos sentidos de cada pareja para dibujar una sola línea.
    parejas["clave"] = parejas.apply(lambda f: tuple(sorted((f.pasadora, f.receptora))), axis=1)
    lineas = parejas.groupby("clave").n.sum()
    lineas = lineas[lineas >= minimo]
    maximo = lineas.max() if len(lineas) else 1
    for (a, b), n in lineas.sort_values().items():
        if a not in tabla.index or b not in tabla.index:
            continue
        pitch.lines(tabla.loc[a, "x"], tabla.loc[a, "y"], tabla.loc[b, "x"], tabla.loc[b, "y"],
                    lw=(0.6 + 7 * n / maximo) * escala, color=c["cal"], alpha=0.25 + 0.6 * n / maximo,
                    zorder=1, ax=ax)
    central = tabla.intermediacion.idxmax()
    tamanos = 120 + 1400 * (tabla.pases_red / tabla.pases_red.max()) ** 1.2
    colores_nodo = [c["acento"] if j == central else c["cal"] for j in tabla.index]
    pitch.scatter(tabla.x, tabla.y, s=tamanos * escala ** 2, color=colores_nodo,
                  edgecolors=c["noche"], linewidth=1.5 * escala, zorder=3, ax=ax)
    if etiquetas:
        for jugadora, fila in tabla.iterrows():
            # En campo vertical, x de StatsBomb es la altura y la y es el ancho.
            texto = ax.annotate(corto(jugadora), (fila.y, fila.x), xytext=(0, -16 * escala - 6),
                                textcoords="offset points", ha="center", va="top", fontsize=11 * escala,
                                fontweight=600, color=c["cal"], zorder=5)
            # Un borde del color del césped para que el nombre se lea aunque cruce una línea.
            texto.set_path_effects([efectos.withStroke(linewidth=3, foreground=c["noche"])])
    return central


def crear_figuras(partidos_red, resumen, por_jugadora, logo, carpeta):
    """
    partidos_red: lista de (partido, pases, tabla) con nombres ya cortos
    resumen:      DataFrame con una fila por partido
    por_jugadora: DataFrame con una fila por jugadora y partido
    """
    c = colores()
    final = next(x for x in partidos_red if x[0]["fase"] == "Final")
    partido, pases, tabla = final
    central = tabla.intermediacion.idxmax()
    fila_final = resumen[resumen.fase == "Final"].iloc[0]

    # 01 · La red de la final ---------------------------------------------------
    fig, area = lienzo("instagram", "La final, pase a pase",
                       f"España {partido['goles_espana']}-{partido['goles_rival']} Inglaterra (1-3 en los penaltis) · "
                       f"{fila_final.pases_red} pases hasta el primer cambio (min. {fila_final.minuto_corte:.0f})\n"
                       "Círculo: posición media y volumen de pases · Línea: 4 pases o más entre la pareja",
                       pie=PIE, etiqueta=ETIQUETA, logo_fuente=logo,
                       lectura=f"En naranja, la jugadora con más intermediación: por ella pasaban más caminos\n"
                               f"cortos entre compañeras. En la final fue {nombre_completo(central)}.")
    area[1] -= 0.035
    area[3] += 0.035
    ax = fig.add_axes(area)
    dibujar_red(ax, pases, tabla, c)
    ax.annotate("", xy=(1.02, 0.75), xytext=(1.02, 0.25), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=c["acento_texto"], lw=2))
    ax.text(1.045, 0.5, "Ataque de España", rotation=90, transform=ax.transAxes, va="center",
            fontsize=12, color=c["acento_texto"], fontweight=700)
    guardar(fig, carpeta, "01_red_final_instagram")

    # 02 · Seis redes (Instagram, 2 × 3) -----------------------------------------
    def seis_redes(formato, filas, columnas, nombre, titulo, subtitulo, escala, tam_rotulo):
        separador = "\n" if formato == "instagram" else " "
        fig, area = lienzo(formato, titulo, subtitulo, pie=PIE, etiqueta=ETIQUETA, logo_fuente=logo,
                           lectura=f"Círculo: posición media; tamaño según los pases dados y recibidos.{separador}"
                                   "En naranja, la jugadora con más intermediación de cada partido.")
        if formato != "instagram":
            area[1] -= 0.04
            area[3] += 0.04
        else:
            area[1] += 0.02
            area[3] -= 0.02
        hueco_x, hueco_y = 0.015, 0.05
        ancho = (area[2] - hueco_x * (columnas - 1)) / columnas
        alto = (area[3] - hueco_y * filas) / filas
        for i, (p, pa, t) in enumerate(partidos_red):
            fila, columna = divmod(i, columnas)
            x0 = area[0] + columna * (ancho + hueco_x)
            y0 = area[1] + (filas - 1 - fila) * (alto + hueco_y)
            ax = fig.add_axes([x0, y0, ancho, alto])
            central_i = dibujar_red(ax, pa, t, c, escala=escala, etiquetas=False)
            r = resumen[resumen.partido_id == p["partido_id"]].iloc[0]
            fase = FASE[p["fase"]].replace("Fase de grupos", "Grupos") if formato in ("instagram", "facebook") else FASE[p["fase"]]
            ax.set_title(f"{fase} · {RIVAL[p['rival']]} {p['goles_espana']}-{p['goles_rival']}",
                         fontsize=tam_rotulo, fontweight=700, color=c["tinta"], loc="left", pad=4)
            ax.text(0.0, -0.035, f"{r.pases_por_minuto:.1f} pases/min · eje: {corto(central_i)}".replace(".", ",", 1),
                    transform=ax.transAxes, fontsize=tam_rotulo - 2, color=c["tinta_suave"], va="top")
        guardar(fig, carpeta, nombre)

    seis_redes("instagram", 2, 3, "02_seis_redes_instagram", "Seis partidos,\nseis redes",
               "La red de España en cada partido, hasta su primer cambio.", 0.42, 13)
    for formato in ("facebook", "linkedin", "web"):
        seis_redes(formato, 1, 6, f"05_seis_redes_{formato}", "Así circulaba el balón en España",
                   "Eurocopa femenina 2025 · Red de pases de cada partido hasta el primer cambio",
                   0.28 if formato == "facebook" else 0.36, 10 if formato == "facebook" else 12)

    # 03 · Quién unía el juego -------------------------------------------------
    habituales = por_jugadora.groupby("jugadora").filter(lambda d: len(d) >= 3)
    orden = habituales.groupby("jugadora").intermediacion.mean().sort_values()
    fig, area = lienzo("instagram", "Quién unía\nel juego de España",
                       "Intermediación en cada partido: parte de los caminos más cortos\n"
                       "entre compañeras que pasan por ella. Jugadoras con 3 redes o más.",
                       pie=PIE, etiqueta=ETIQUETA, logo_fuente=logo,
                       lectura="Punto: un partido. Barra: media del torneo.\n"
                               f"Las dos con más intermediación media: {nombre_completo(orden.index[-1])} y {nombre_completo(orden.index[-2])}.")
    area[0] += 0.17
    area[2] -= 0.17
    ax = fig.add_axes(area)
    for i, jugadora in enumerate(orden.index):
        valores = habituales[habituales.jugadora == jugadora].intermediacion
        ruido = np.linspace(-0.15, 0.15, len(valores))
        ax.scatter(valores, i + ruido, s=34, color=c["principal"], alpha=0.55, edgecolors="none", zorder=2)
        destacada = i >= len(orden) - 2
        ax.plot([0, orden[jugadora]], [i, i], color=c["acento"] if destacada else c["apagado"],
                lw=5, solid_capstyle="round", zorder=1)
    ax.set_yticks(range(len(orden)), [nombre_completo(j) for j in orden.index], fontsize=13)
    for etiqueta in ax.get_yticklabels():
        etiqueta.set_color(c["tinta"])
    ax.set_xlabel("Intermediación (0 = ningún camino pasa por ella)", fontsize=12, labelpad=10)
    estilo_ejes(ax, rejilla="x")
    ax.spines["left"].set_visible(False)
    guardar(fig, carpeta, "03_intermediacion_instagram")

    # 04 · Ritmo y concentración -----------------------------------------------
    fig, area = lienzo("instagram", "En las eliminatorias,\nEspaña pasó menos",
                       "Pases completados por minuto en la red de cada partido\n"
                       "y concentración del juego (0 = repartido, 1 = todo por una jugadora).",
                       pie=PIE, etiqueta=ETIQUETA, logo_fuente=logo,
                       lectura="Los minutos son los jugados hasta el primer cambio de España,\n"
                               "descuento de la primera parte incluido.")
    alto_total = area[3]
    ax1 = fig.add_axes([area[0] + 0.03, area[1] + alto_total * 0.52, area[2] - 0.03, alto_total * 0.44])
    ax2 = fig.add_axes([area[0] + 0.03, area[1], area[2] - 0.03, alto_total * 0.36])
    etiquetas_x = [f"{RIVAL[r]}\n{FASE[f].replace('Fase de grupos', 'Grupos')}" for r, f in zip(resumen.rival, resumen.fase)]
    x = np.arange(len(resumen))
    ax1.bar(x, resumen.pases_por_minuto, color=c["principal"], width=0.6)
    for xi, v in zip(x, resumen.pases_por_minuto):
        ax1.text(xi, v + 0.12, f"{v:.1f}".replace(".", ","), ha="center", fontsize=13, fontweight=700, color=c["tinta"])
    ax1.set_xticks(x, etiquetas_x, fontsize=11)
    ax1.set_ylabel("Pases por minuto", fontsize=12)
    ax1.set_ylim(0, resumen.pases_por_minuto.max() * 1.18)
    estilo_ejes(ax1, rejilla="y")
    ax2.plot(x, resumen.centralizacion, color=c["acento"], lw=3, marker="o", markersize=9)
    for xi, v in zip(x, resumen.centralizacion):
        ax2.text(xi, v + 0.035, f"{v:.2f}".replace(".", ","), ha="center", fontsize=12, color=c["tinta"])
    ax2.set_xticks(x, etiquetas_x, fontsize=11)
    ax2.set_ylim(0, 0.7)
    ax2.set_ylabel("Concentración", fontsize=12)
    estilo_ejes(ax2, rejilla="y")
    guardar(fig, carpeta, "04_ritmo_concentracion_instagram")
    return central


def crear_carrusel(resumen, central_final, carpeta_graficos, carpeta):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    final = resumen[resumen.fase == "Final"].iloc[0]
    import json
    recursos = Path(__file__).resolve().parents[1] / "recursos"
    foto = json.loads((recursos / "foto.json").read_text(encoding="utf-8"))
    fig = portada("Las redes de pases\nde España en la Eurocopa",
                  cifra=f"{final.pases_red}",
                  cifra_texto=f"pases completados en la final antes\ndel primer cambio, con {nombre_completo(central_final)}\ncomo eje de la red",
                  etiqueta=ETIQUETA, antetitulo="Eurocopa femenina 2025 · Selección española",
                  foto=recursos / "foto.jpg", credito=credito_corto(foto), foco=(0.45, 0.42))
    guardar(fig, carpeta, "01_portada")
    for origen, destino in [("01_red_final_instagram", "02_final"), ("02_seis_redes_instagram", "03_seis_redes"),
                            ("03_intermediacion_instagram", "04_quien_unia"),
                            ("04_ritmo_concentracion_instagram", "05_ritmo")]:
        for extension in ("png", "svg"):
            shutil.copy(Path(carpeta_graficos) / f"{origen}.{extension}", carpeta / f"{destino}.{extension}")
    fig = cierre("Lo que estas\nredes no dicen",
                 ["Solo cuentan pases completados:\nni conducciones ni pérdidas.",
                  "Cortan en el primer cambio:\nfalta el final de cada partido.",
                  "La posición media mezcla\nataque y defensa.",
                  "Seis partidos no bastan\npara sacar reglas generales."])
    guardar(fig, carpeta, "06_limites")
