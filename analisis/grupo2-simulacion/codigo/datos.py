"""
Resultados del grupo 2 de Primera Federación 2026/27.

La simulación solo usa resultados: quién jugó contra quién, en qué campo y
cuántos goles marcó cada uno. Los lee del archivo que ya mantiene el
seguimiento del Real Zaragoza (analisis/real-zaragoza/datos/entrada/
grupo2_partidos.csv), del que aprovecha únicamente las columnas del resultado.

Antes de simular, compruebo que la clasificación que sale de esos resultados
coincide punto por punto con la clasificación publicada tras la última jornada
(clasificacion.csv, contrastada con BeSoccer y FotMob). Si no coincide, algo
falta o sobra y el programa se detiene.
"""
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ_WEB = Path(__file__).resolve().parents[3]
ENTRADA = RAIZ_WEB / "analisis" / "real-zaragoza" / "datos" / "entrada"


def leer_resultados(ruta=ENTRADA / "grupo2_partidos.csv"):
    """Una fila por partido jugado, desde el punto de vista del equipo local."""
    filas = pd.read_csv(ruta)
    locales = filas[filas.sede == "Casa"]
    partidos = pd.DataFrame({
        "jornada": locales.jornada.astype(int),
        "fecha": locales.fecha,
        "local": locales.equipo,
        "visitante": locales.rival,
        "goles_local": locales.goles_favor.astype(int),
        "goles_visitante": locales.goles_contra.astype(int),
    }).sort_values(["jornada", "fecha", "local"]).reset_index(drop=True)
    return partidos


def clasificacion_desde_resultados(partidos):
    """Puntos, partidos y goles de cada equipo a partir de los resultados."""
    filas = []
    for p in partidos.itertuples():
        for equipo, gf, gc in ((p.local, p.goles_local, p.goles_visitante),
                               (p.visitante, p.goles_visitante, p.goles_local)):
            filas.append({"equipo": equipo, "pj": 1, "gf": gf, "gc": gc,
                          "puntos": 3 if gf > gc else (1 if gf == gc else 0)})
    return pd.DataFrame(filas).groupby("equipo").sum()


def comprobar_contra_clasificacion(partidos, ruta=ENTRADA / "clasificacion.csv"):
    """Compara con la última clasificación publicada. Devuelve la jornada comprobada."""
    publicada = pd.read_csv(ruta)
    ultima = int(publicada.tras_jornada.max())
    assert ultima == partidos.jornada.max(), (
        f"La clasificación llega a la jornada {ultima} y los resultados a la {partidos.jornada.max()}")
    publicada = publicada[publicada.tras_jornada == ultima].set_index("equipo")
    calculada = clasificacion_desde_resultados(partidos)
    assert set(publicada.index) == set(calculada.index), "Los equipos no coinciden"
    for columna in ("pj", "gf", "gc", "puntos"):
        diferencias = (publicada[columna] - calculada[columna]).abs()
        assert diferencias.sum() == 0, f"La columna {columna} no cuadra: {diferencias[diferencias > 0].to_dict()}"
    return ultima


def partidos_pendientes(partidos):
    """
    Todos los cruces que faltan por jugar. En una liga a doble vuelta cada
    equipo recibe una vez a cada rival, así que lo pendiente es el conjunto
    de parejas (local, visitante) que todavía no aparecen. El orden del
    calendario no hace falta para saber cómo acaba la tabla.
    """
    equipos = sorted(set(partidos.local) | set(partidos.visitante))
    jugados = set(zip(partidos.local, partidos.visitante))
    pendientes = [(a, b) for a, b in permutations(equipos, 2) if (a, b) not in jugados]
    assert len(jugados) + len(pendientes) == len(equipos) * (len(equipos) - 1)
    return equipos, pd.DataFrame(pendientes, columns=["local", "visitante"])


def matriz_goles(partidos, equipos):
    """Matriz 20 × 20 con los goles del local (fila) contra el visitante (columna); NaN si no se ha jugado."""
    indice = {e: i for i, e in enumerate(equipos)}
    goles = np.full((len(equipos), len(equipos), 2), np.nan)
    for p in partidos.itertuples():
        goles[indice[p.local], indice[p.visitante]] = (p.goles_local, p.goles_visitante)
    return goles
