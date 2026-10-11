"""
Comprobaciones de los datos antes de publicar nada.

Como los datos se copian a mano de varias fuentes, es fácil equivocarse en
un minuto o en un nombre. Estas comprobaciones cruzan unas tablas con otras
(goles con marcadores, cambios con alineaciones, tarjetas con estadísticas,
clasificación con nuestros partidos) y paran el programa si algo no cuadra.
"""

import numpy as np

from cargar_datos import LIGA


class DatosIncoherentes(Exception):
    """Error que lanzo cuando dos tablas no cuadran entre sí."""


def _exigir(condicion, mensaje):
    if not condicion:
        raise DatosIncoherentes(mensaje)


def comprobar_goles(partidos, goles):
    """Los goles apuntados uno a uno tienen que sumar el marcador final y el del descanso."""
    for p in partidos.itertuples():
        del_partido = goles[goles["partido_id"] == p.partido_id]
        favor = del_partido[del_partido["sentido"] == "Favor"]
        contra = del_partido[del_partido["sentido"] == "Contra"]

        _exigir(len(favor) == p.goles_favor and len(contra) == p.goles_contra,
                f"Partido {p.partido_id} ({p.rival}): los goles no suman el {p.goles_favor}-{p.goles_contra}")
        _exigir((favor["parte"] == 1).sum() == p.gf_descanso
                and (contra["parte"] == 1).sum() == p.gc_descanso,
                f"Partido {p.partido_id} ({p.rival}): no cuadra el resultado al descanso")

    # Nadie se asiste a sí mismo
    con_asistencia = goles[goles["asistencia"] != ""]
    _exigir((con_asistencia["asistencia"] != con_asistencia["jugador"]).all(),
            "Hay un gol en el que el goleador figura también como asistente")


def comprobar_alineaciones(alineaciones, cambios, goles):
    """Once de 11, cambios posibles y goleadores en el campo en el minuto del gol."""
    for partido_id, once in alineaciones.groupby("partido_id"):
        titulares = set(once["jugador"])
        _exigir(len(titulares) == 11, f"Partido {partido_id}: el once no tiene 11 jugadores")

        cambios_partido = cambios[cambios["partido_id"] == partido_id]
        _exigir(cambios_partido["sale"].isin(titulares | set(cambios_partido["entra"])).all(),
                f"Partido {partido_id}: sale del campo alguien que no estaba jugando")
        _exigir(not cambios_partido["entra"].isin(titulares).any(),
                f"Partido {partido_id}: entra un jugador que ya era titular")

        # Cada goleador del Zaragoza tenía que estar en el campo
        goles_partido = goles[(goles["partido_id"] == partido_id)
                              & (goles["sentido"] == "Favor")
                              & (~goles["propia_puerta"])]
        for gol in goles_partido.itertuples():
            entra = cambios_partido.loc[cambios_partido["entra"] == gol.jugador, "minuto"]
            sale = cambios_partido.loc[cambios_partido["sale"] == gol.jugador, "minuto"]
            inicio = 0 if gol.jugador in titulares else (entra.iloc[0] if len(entra) else None)
            fin = sale.iloc[0] if len(sale) else 90
            _exigir(inicio is not None and inicio <= gol.minuto <= fin,
                    f"Partido {partido_id}: {gol.jugador} marca en el {gol.minuto} sin estar en el campo")


def comprobar_tiros(tiros, goles, estadisticas):
    """Tiros ≥ tiros a puerta ≥ goles, y desglose de tiros completo cuando lo hay."""
    _exigir((tiros["tiros_zaragoza"] >= tiros["a_puerta_zaragoza"]).all(),
            "Hay un partido con más tiros a puerta que tiros")

    # Los goles en propia puerta del rival no son tiros del Zaragoza, así que no cuentan aquí
    goles_propios = (goles[(goles["sentido"] == "Favor") & (~goles["propia_puerta"])]
                     .groupby("partido_id").size())
    for fila in tiros.itertuples():
        marcados = goles_propios.get(fila.partido_id, 0)
        _exigir(fila.a_puerta_zaragoza >= marcados,
                f"Partido {fila.partido_id}: más goles ({marcados}) que tiros a puerta ({fila.a_puerta_zaragoza})")

    # Donde tengo el desglose completo (tabla de estadísticas con calidad «ok»),
    # a puerta + fuera + bloqueados tiene que dar el total.
    partido = estadisticas[(estadisticas["periodo"] == "Partido") & (estadisticas["calidad"] == "ok")]
    for partido_id, filas in partido.groupby("partido_id"):
        valores = filas.set_index("metrica")
        if {"tiros", "tiros_puerta", "tiros_fuera", "tiros_bloqueados"} <= set(valores.index):
            for lado in ("zaragoza", "valor_rival"):
                suma = sum(valores.loc[m, lado] for m in ("tiros_puerta", "tiros_fuera", "tiros_bloqueados"))
                _exigir(valores.loc["tiros", lado] == suma,
                        f"Partido {partido_id}: el desglose de tiros no suma el total")

    # Si un partido está separado por partes, las partes suman el total
    por_partes = estadisticas[estadisticas["periodo"] != "Partido"]
    for (partido_id, metrica), filas in por_partes.groupby(["partido_id", "metrica"]):
        if metrica == "posesion_pct":
            continue  # los porcentajes no se suman
        total = estadisticas[(estadisticas["partido_id"] == partido_id)
                             & (estadisticas["periodo"] == "Partido")
                             & (estadisticas["metrica"] == metrica)]
        if len(total):
            _exigir(np.allclose(filas[["zaragoza", "valor_rival"]].sum().values,
                                total[["zaragoza", "valor_rival"]].iloc[0].values),
                    f"Partido {partido_id}: las partes no suman el total en {metrica}")


def comprobar_tarjetas(tarjetas, estadisticas):
    """Las amarillas apuntadas una a una coinciden con las de las estadísticas del partido."""
    amarillas = estadisticas[(estadisticas["periodo"] == "Partido") & (estadisticas["metrica"] == "amarillas")]
    for fila in amarillas.itertuples():
        apuntadas = ((tarjetas["partido_id"] == fila.partido_id) & (tarjetas["tarjeta"] == "Amarilla")).sum()
        _exigir(apuntadas == fila.zaragoza,
                f"Partido {fila.partido_id}: {apuntadas} amarillas apuntadas y {fila.zaragoza} en las estadísticas")


def comprobar_clasificacion(clasificacion, partidos_liga):
    """La clasificación cuadra por dentro y la fila del Zaragoza coincide con nuestros partidos."""
    c = clasificacion
    _exigir(c["gf"].sum() == c["gc"].sum(), "Clasificación: goles a favor y en contra no suman lo mismo")
    _exigir(c["g"].sum() == c["p"].sum(), "Clasificación: victorias y derrotas no suman lo mismo")
    _exigir((c["pj"] == c["g"] + c["e"] + c["p"]).all(), "Clasificación: PJ no es G + E + P")
    _exigir((c["puntos"] == 3 * c["g"] + c["e"]).all(), "Clasificación: los puntos no son 3G + E")

    zgz = c[c["equipo"] == "Real Zaragoza"].iloc[0]
    jugados = partidos_liga[partidos_liga["jornada"] <= c["tras_jornada"].iloc[0]]
    _exigir((zgz.pj, zgz.gf, zgz.gc, zgz.puntos)
            == (len(jugados), jugados["goles_favor"].sum(), jugados["goles_contra"].sum(), jugados["puntos"].sum()),
            "La fila del Zaragoza en la clasificación no coincide con sus partidos")


def comprobar_todo(datos, partidos, goles):
    """Lanza todas las comprobaciones. Si alguna falla, para con un mensaje claro."""
    comprobar_goles(partidos, goles)
    comprobar_alineaciones(datos["alineaciones"], datos["cambios"], goles)
    comprobar_tiros(datos["tiros"], goles, datos["estadisticas"])
    comprobar_tarjetas(datos["tarjetas"], datos["estadisticas"])
    comprobar_clasificacion(datos["clasificacion"], partidos[partidos["competicion"] == LIGA])
