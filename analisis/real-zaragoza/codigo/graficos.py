"""
Gráficos del informe. Uso los mismos colores que la web (verde césped y
naranja) para que todo se vea igual.
"""

import matplotlib

matplotlib.use("Agg")  # sin ventana: solo guardo los PNG
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from calculos import TRAMOS

# Colores de la web
VERDE = "#1f6b3e"
VERDE_CLARO = "#8db89b"
NARANJA = "#ff6a2b"
GRIS = "#b7bfb6"
TINTA = "#0f2418"
TINTA_SUAVE = "#4d6356"

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

# Nombres cortos para que quepan en el eje
NOMBRES_CORTOS = {
    "Gimnàstic de Tarragona": "Nàstic",
    "Juventud Torremolinos CF": "Torremolinos",
    "Atlético Madrileño": "At. Madrileño",
}


def _corto(rival):
    if rival in NOMBRES_CORTOS:
        return NOMBRES_CORTOS[rival]
    # Quito siglas tipo CF, CD, UD, FC para acortar
    palabras = [p for p in rival.split() if p not in {"CF", "CD", "UD", "FC", "SD", "CE"}]
    return " ".join(palabras)


def _enteros(ax):
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))


def _barras_dobles(ax, etiquetas, a, b, color_a, color_b, nombre_a, nombre_b):
    """Dos barras por categoría, una al lado de la otra."""
    x = np.arange(len(etiquetas))
    barras_a = ax.bar(x - 0.19, a, 0.38, color=color_a, label=nombre_a)
    barras_b = ax.bar(x + 0.19, b, 0.38, color=color_b, label=nombre_b)
    ax.set_xticks(x, etiquetas)
    return barras_a, barras_b


def resumen(partidos, goles, participacion, ruta):
    """Marcadores, puntos acumulados, goles por tramo y participación en goles."""
    fig, ax = plt.subplots(2, 2, figsize=(13, 8.5))
    etiquetas = [f"J{j}\n{_corto(r)}" for j, r in zip(partidos["jornada"], partidos["rival"])]

    # 1. Marcadores
    _barras_dobles(ax[0, 0], etiquetas, partidos["goles_favor"], partidos["goles_contra"],
                   VERDE, NARANJA, "A favor", "En contra")
    ax[0, 0].set_title(f"Marcadores: {partidos['goles_favor'].sum()} goles a favor "
                       f"y {partidos['goles_contra'].sum()} en contra")
    ax[0, 0].legend()
    _enteros(ax[0, 0])

    # 2. Puntos acumulados, con la referencia de 2 puntos por partido
    n = len(partidos)
    ax[0, 1].plot(partidos["jornada"], partidos["puntos_acumulados"], "o-", color=VERDE, lw=3,
                  label="Real Zaragoza")
    ax[0, 1].plot([0, n], [0, 2 * n], "--", color=GRIS, lw=1.5, label="Ritmo de 2 puntos por partido")
    ax[0, 1].set_xticks(range(0, n + 1))
    ax[0, 1].set_xlabel("Jornada")
    ax[0, 1].set_ylim(0, 3 * n)
    ax[0, 1].set_title(f"{int(partidos['puntos'].sum())} puntos de {3 * n}")
    ax[0, 1].legend(loc="upper left")

    # 3. Goles por tramo de 15 minutos
    tramos = goles.groupby(["tramo", "sentido"]).size().unstack(fill_value=0).reindex(TRAMOS, fill_value=0)
    for col in ("Favor", "Contra"):
        if col not in tramos:
            tramos[col] = 0
    _barras_dobles(ax[1, 0], TRAMOS, tramos["Favor"], tramos["Contra"],
                   VERDE, NARANJA, "A favor", "En contra")
    ax[1, 0].set_title("¿Cuándo llegan los goles? (el descuento va con su parte)")
    ax[1, 0].legend()
    _enteros(ax[1, 0])

    # 4. Goles y asistencias por jugador
    p = participacion.iloc[::-1]
    ax[1, 1].barh(p["jugador"], p["goles"], color=VERDE, label="Goles")
    ax[1, 1].barh(p["jugador"], p["asistencias"], left=p["goles"], color=VERDE_CLARO,
                  label="Asistencias registradas")
    ax[1, 1].xaxis.set_major_locator(MaxNLocator(integer=True))
    ax[1, 1].set_title("Participación en goles")
    ax[1, 1].legend(loc="lower right")

    fig.text(0.01, 0.005, "Elaboración propia con datos públicos (web del club, FotMob, futboltotal y BeSoccer).",
             fontsize=8.5, color=TINTA_SUAVE)
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def tiros(tiros_partidos, partidos, estadisticas, ruta):
    """Tiros de cada partido y, si hay un partido con datos por partes, su detalle."""
    t = tiros_partidos.merge(partidos[["partido_id", "jornada", "rival", "goles_favor"]], on="partido_id")
    t = t.sort_values("jornada")

    por_partes = estadisticas[(estadisticas["periodo"] != "Partido")
                              & (estadisticas["metrica"].isin(["tiros", "tiros_puerta"]))]
    hay_partes = not por_partes.empty
    fig, ax = plt.subplots(1, 2 if hay_partes else 1, figsize=(13 if hay_partes else 8, 4.8),
                           gridspec_kw={"width_ratios": [1.6, 1]} if hay_partes else None)
    ax_tiros = ax[0] if hay_partes else ax

    etiquetas = [f"J{j}\n{_corto(r)}" for j, r in zip(t["jornada"], t["rival"])]
    barras_z, barras_r = _barras_dobles(ax_tiros, etiquetas, t["tiros_zaragoza"], t["tiros_rival"],
                                        VERDE, GRIS, "Zaragoza", "Rival")
    # Los partidos en los que el desglose de tiros no cuadra van más claros
    for i, completo in enumerate(t["completo"]):
        if not completo:
            barras_z[i].set_alpha(0.45)
            barras_r[i].set_alpha(0.45)
    for i, (n_tiros, n_goles) in enumerate(zip(t["tiros_zaragoza"], t["goles_favor"])):
        ax_tiros.text(i - 0.19, n_tiros + 0.6, f"{n_goles} g", ha="center", fontsize=9, color=VERDE)
    ax_tiros.set_title(f"Tiros: {t['tiros_zaragoza'].sum()} del Zaragoza y {t['tiros_rival'].sum()} de los rivales\n"
                       "(más claro: el desglose de tiros no cuadra · «g» = goles)")
    ax_tiros.legend()
    _enteros(ax_tiros)

    if hay_partes:
        partido_id = por_partes["partido_id"].iloc[0]
        rival = partidos.loc[partidos["partido_id"] == partido_id, "rival"].iloc[0]
        tabla = por_partes[por_partes["partido_id"] == partido_id].pivot(
            index="periodo", columns="metrica", values="zaragoza")
        _barras_dobles(ax[1], ["1.ª parte", "2.ª parte"], tabla["tiros"], tabla["tiros_puerta"],
                       VERDE, VERDE_CLARO, "Tiros", "A puerta")
        ax[1].set_title(f"{_corto(rival)}: tiros del Zaragoza por parte")
        ax[1].legend()
        _enteros(ax[1])

    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def contexto(clasificacion, goles, rivales_jugados, ruta):
    """Clasificación actual y cuántos goles llegan desde el banquillo."""
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw={"width_ratios": [1.6, 1]})

    c = clasificacion.iloc[::-1]
    colores = [VERDE if e == "Real Zaragoza" else (NARANJA if e in rivales_jugados else GRIS)
               for e in c["equipo"]]
    ax[0].barh(c["equipo"], c["puntos"], color=colores)
    for i, puntos in enumerate(c["puntos"]):
        ax[0].text(puntos + 0.2, i, str(puntos), va="center", fontsize=9)
    ax[0].xaxis.set_major_locator(MaxNLocator(integer=True))
    ax[0].set_title(f"Clasificación tras la jornada {clasificacion['tras_jornada'].iloc[0]} (puntos)")
    ax[0].text(0.98, 0.02, "Naranja: rivales ya jugados", transform=ax[0].transAxes,
               ha="right", fontsize=9, color=NARANJA)

    roles = goles[goles["rol_goleador"] != ""]["rol_goleador"].value_counts().reindex(
        ["Titular", "Suplente"], fill_value=0)
    ax[1].bar(roles.index, roles.values, color=[VERDE, VERDE_CLARO])
    for i, n in enumerate(roles.values):
        ax[1].text(i, n + 0.1, str(n), ha="center", fontsize=12, fontweight="bold")
    ax[1].set_title(f"{roles['Suplente']} de {roles.sum()} goles\nllegan desde el banquillo")
    _enteros(ax[1])

    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def equipos_y_minutos(clasificacion, jugadores, ruta):
    """Goles a favor y en contra de todos los equipos, y minutos de la plantilla."""
    fig, ax = plt.subplots(1, 2, figsize=(13, 5.6))

    for e in clasificacion.itertuples():
        es_zgz = e.equipo == "Real Zaragoza"
        ax[0].scatter(e.gf, e.gc, s=140 if es_zgz else 50, color=VERDE if es_zgz else GRIS,
                      edgecolor="white", zorder=3 if es_zgz else 2)
        if es_zgz:
            # Si otro equipo tiene los mismos goles, lo digo para que no quede escondido debajo
            iguales = clasificacion[(clasificacion["gf"] == e.gf) & (clasificacion["gc"] == e.gc)
                                    & (clasificacion["equipo"] != e.equipo)]["equipo"].tolist()
            texto = "Real Zaragoza" + (f" (y {', '.join(iguales)})" if iguales else "")
            ax[0].annotate(texto, (e.gf, e.gc), xytext=(-6, 8), ha="right",
                           textcoords="offset points", fontsize=9, color=VERDE, fontweight="bold")
    ax[0].axvline(clasificacion["gf"].mean(), color=GRIS, ls="--", lw=1)
    ax[0].axhline(clasificacion["gc"].mean(), color=GRIS, ls="--", lw=1)
    ax[0].invert_yaxis()  # arriba, los que menos encajan
    ax[0].set_xlabel("Goles a favor")
    ax[0].set_ylabel("Goles en contra (arriba = menos)")
    ax[0].set_title("Ataque y defensa de los 20 equipos")

    con_minutos = jugadores[jugadores["minutos"] >= 180].sort_values("minutos")
    participaciones = con_minutos["goles"] + con_minutos["asistencias"]
    ax[1].barh(con_minutos["jugador"], con_minutos["minutos"],
               color=[VERDE if p > 0 else GRIS for p in participaciones])
    for i, (minutos, p) in enumerate(zip(con_minutos["minutos"], participaciones)):
        if p:
            ax[1].text(minutos + 5, i, f"{p} G+A", va="center", fontsize=9, color=VERDE)
    ax[1].set_title("Minutos jugados (180 o más) y goles + asistencias")

    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
