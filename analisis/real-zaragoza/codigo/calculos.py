"""
Cálculos a partir de los datos de partida: puntos, tramos de los goles,
minutos de cada jugador, participación en goles y clasificación.

Cada función recibe tablas de pandas y devuelve una tabla nueva, sin tocar
la original, para poder revisar cada paso por separado.
"""

import numpy as np
import pandas as pd

from cargar_datos import LIGA

# Duración que doy a cada partido para contar minutos. El descuento no
# se suma: un titular que juega todo el partido cuenta como 90 minutos.
MINUTOS_PARTIDO = 90

# Tramos de 15 minutos. Un gol en el 45+3 cuenta en el 31-45 y uno en el
# 90+2 en el 76-90, que es donde se marcó de verdad.
TRAMOS = ["01–15", "16–30", "31–45+", "46–60", "61–75", "76–90+"]


def solo_liga(tabla):
    """Filtra una tabla que tenga columna 'competicion' para quedarse con la liga."""
    return tabla[tabla["competicion"] == LIGA].copy()


# ---------------------------------------------------------------------------
# Partidos
# ---------------------------------------------------------------------------

def preparar_partidos(partidos):
    """Añade puntos, resultado, diferencia de goles y puntos acumulados en liga."""
    p = partidos.copy()

    gana = p["goles_favor"] > p["goles_contra"]
    empata = p["goles_favor"] == p["goles_contra"]
    p["puntos"] = np.select([gana, empata], [3, 1], default=0)
    p["resultado"] = np.select([gana, empata], ["Victoria", "Empate"], default="Derrota")
    p["diferencia_goles"] = p["goles_favor"] - p["goles_contra"]
    p["porteria_cero"] = p["goles_contra"] == 0

    # Los puntos acumulados solo tienen sentido en liga; en copa quedan vacíos
    es_liga = p["competicion"] == LIGA
    p["puntos_acumulados"] = p["puntos"].where(es_liga).cumsum().where(es_liga)

    return p


def resumen_por_sede(partidos_liga):
    """Puntos, goles y porterías a cero en casa y fuera."""
    r = (
        partidos_liga.groupby("sede")
        .agg(
            partidos=("partido_id", "size"),
            puntos=("puntos", "sum"),
            goles_favor=("goles_favor", "sum"),
            goles_contra=("goles_contra", "sum"),
            porterias_cero=("porteria_cero", "sum"),
        )
        .reset_index()
    )
    r["puntos_por_partido"] = (r["puntos"] / r["partidos"]).round(2)
    return r


# ---------------------------------------------------------------------------
# Goles
# ---------------------------------------------------------------------------

def _tramo(minuto):
    """Devuelve el tramo de 15 minutos de un gol a partir del minuto base."""
    if minuto <= 15:
        return "01–15"
    if minuto <= 30:
        return "16–30"
    if minuto <= 45:
        return "31–45+"
    if minuto <= 60:
        return "46–60"
    if minuto <= 75:
        return "61–75"
    return "76–90+"


def preparar_goles(goles, cambios, partidos):
    """
    Añade a cada gol el minuto en texto (45+7), su tramo y si el goleador
    era titular o había salido desde el banquillo.
    """
    g = goles.copy()

    g["minuto_texto"] = g["minuto"].astype(str) + np.where(
        g["anadido"] > 0, "+" + g["anadido"].astype(str), ""
    )
    g["tramo"] = g["minuto"].apply(_tramo)

    # Un goleador es «Suplente» si aparece entrando en los cambios de ese
    # partido antes del gol. Solo lo miro en los goles del Zaragoza que no
    # son en propia puerta.
    def rol(fila):
        if fila["sentido"] != "Favor" or fila["propia_puerta"]:
            return ""
        entrada = cambios[
            (cambios["partido_id"] == fila["partido_id"])
            & (cambios["entra"] == fila["jugador"])
        ]
        if len(entrada) and entrada["minuto"].iloc[0] <= fila["minuto"]:
            return "Suplente"
        return "Titular"

    g["rol_goleador"] = g.apply(rol, axis=1)

    # Añado datos del partido para que la tabla se entienda sola
    g = g.merge(
        partidos[["partido_id", "competicion", "jornada", "fecha", "sede", "rival"]],
        on="partido_id",
        how="left",
    )
    return g


def participacion_en_goles(goles_liga):
    """Goles y asistencias registradas por jugador (sin goles en propia puerta)."""
    a_favor = goles_liga[(goles_liga["sentido"] == "Favor") & (~goles_liga["propia_puerta"])]
    goles_jug = a_favor["jugador"].value_counts().rename("goles")

    con_asistencia = goles_liga[goles_liga["asistencia"] != ""]
    asist_jug = con_asistencia["asistencia"].value_counts().rename("asistencias")

    t = pd.concat([goles_jug, asist_jug], axis=1).fillna(0).astype(int)
    t.index.name = "jugador"
    t = t.reset_index()
    t["participaciones"] = t["goles"] + t["asistencias"]
    return t.sort_values(["participaciones", "goles", "jugador"], ascending=[False, False, True])


# ---------------------------------------------------------------------------
# Minutos
# ---------------------------------------------------------------------------

def minutos_por_partido(alineaciones, cambios):
    """
    Minutos de cada jugador en cada partido con alineación conocida.

    Titular: del 0 al minuto en que sale (90 si no sale).
    Suplente: del minuto en que entra al 90.
    No hay expulsiones del Zaragoza hasta ahora; si las hubiera, habría que
    tratarlas como una salida sin cambio.
    """
    filas = []
    for partido_id, once in alineaciones.groupby("partido_id"):
        cambios_partido = cambios[cambios["partido_id"] == partido_id]
        salidas = dict(zip(cambios_partido["sale"], cambios_partido["minuto"]))
        entradas = dict(zip(cambios_partido["entra"], cambios_partido["minuto"]))

        for jugador in once["jugador"]:
            sale = salidas.get(jugador, MINUTOS_PARTIDO)
            filas.append([partido_id, jugador, "Titular", 0, sale, sale])

        for jugador, entra in entradas.items():
            filas.append([partido_id, jugador, "Suplente", entra, MINUTOS_PARTIDO,
                          MINUTOS_PARTIDO - entra])

    return pd.DataFrame(
        filas, columns=["partido_id", "jugador", "rol", "entra", "sale", "minutos"]
    )


def tabla_jugadores(minutos, goles_liga):
    """
    Une los minutos (solo partidos con alineación) con los goles y asistencias.

    En la tabla salen los goles y asistencias de toda la liga, pero los ratios
    por 90 los calculo solo con los partidos de los que tengo minutos: si no,
    un gol en un partido sin alineación inflaría el ratio. Además, solo a
    partir de 180 minutos, porque con menos un gol suelto lo dispara.
    """
    t = (
        minutos.groupby("jugador")
        .agg(
            partidos=("partido_id", "nunique"),
            titularidades=("rol", lambda r: int((r == "Titular").sum())),
            minutos=("minutos", "sum"),
        )
        .reset_index()
    )

    total = participacion_en_goles(goles_liga)
    t = t.merge(total[["jugador", "goles", "asistencias"]], on="jugador", how="left")

    con_minutos = participacion_en_goles(goles_liga[goles_liga["partido_id"].isin(minutos["partido_id"])])
    t = t.merge(con_minutos[["jugador", "participaciones"]], on="jugador", how="left")
    t[["goles", "asistencias", "participaciones"]] = (
        t[["goles", "asistencias", "participaciones"]].fillna(0).astype(int))

    suficiente = t["minutos"] >= 180
    t["participaciones_por_90"] = np.where(
        suficiente, (t["participaciones"] / t["minutos"] * 90).round(2), np.nan)
    t["minutos_por_participacion"] = np.where(
        suficiente & (t["participaciones"] > 0), (t["minutos"] / t["participaciones"]).round(0), np.nan)
    t = t.rename(columns={"participaciones": "participaciones_con_minutos"})
    return t.sort_values(["minutos", "jugador"], ascending=[False, True]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Clasificación y calendario
# ---------------------------------------------------------------------------

def preparar_clasificacion(clasificacion):
    """Diferencia de goles, puntos por partido y puesto en ataque y defensa."""
    c = clasificacion.copy()
    c["dg"] = c["gf"] - c["gc"]
    c["puntos_por_partido"] = (c["puntos"] / c["pj"]).round(2)
    # method="min": si dos equipos empatan a goles, comparten puesto
    c["puesto_ataque"] = c["gf"].rank(ascending=False, method="min").astype(int)
    c["puesto_defensa"] = c["gc"].rank(ascending=True, method="min").astype(int)
    return c


def posicion_de(rival, clasificacion):
    """
    Busca la posición de un rival en la clasificación. Los nombres no siempre
    coinciden («Gimnàstic de Tarragona» frente a «Gimnàstic»), así que pruebo
    primero el nombre exacto y luego si uno contiene al otro.
    """
    nombres = clasificacion.set_index("equipo")["posicion"]
    if rival in nombres:
        return int(nombres[rival])
    for equipo, posicion in nombres.items():
        if equipo in rival or rival in equipo:
            return int(posicion)
    return None
