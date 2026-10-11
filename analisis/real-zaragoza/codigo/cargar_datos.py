"""
Lectura de los datos de partida.

Los CSV de datos/entrada los relleno a mano después de cada partido a partir
de las fichas públicas (web del club, FotMob, futboltotal y BeSoccer). Este
módulo solo los lee y deja cada columna con el tipo que toca. Los cálculos
están en calculos.py.
"""

from pathlib import Path

import pandas as pd

# Rutas del proyecto: este archivo está en analisis/real-zaragoza/codigo/
CARPETA_PROYECTO = Path(__file__).resolve().parents[1]
CARPETA_ENTRADA = CARPETA_PROYECTO / "datos" / "entrada"
CARPETA_SALIDA = CARPETA_PROYECTO / "datos" / "salida"
CARPETA_TEXTOS = CARPETA_PROYECTO / "textos"

# Raíz del repositorio de la web (dos niveles por encima del proyecto)
RAIZ_WEB = CARPETA_PROYECTO.parents[1]

# La liga es la competición principal; el resto (Copa del Rey, etc.)
# se guarda aparte y no cuenta para puntos ni clasificación.
LIGA = "Primera Federación"


def _leer(nombre):
    """Lee un CSV de la carpeta de entrada."""
    return pd.read_csv(CARPETA_ENTRADA / nombre, encoding="utf-8")


def _si_no(columna):
    """Convierte una columna con 'si'/'no' en True/False."""
    return columna.astype(str).str.strip().str.lower().eq("si")


def cargar_todo():
    """Devuelve un diccionario con todas las tablas de entrada ya preparadas."""
    datos = {}

    partidos = _leer("partidos.csv")
    partidos["fecha"] = pd.to_datetime(partidos["fecha"])
    datos["partidos"] = partidos.sort_values("fecha").reset_index(drop=True)

    goles = _leer("goles.csv")
    goles["penalti"] = _si_no(goles["penalti"])
    goles["propia_puerta"] = _si_no(goles["propia_puerta"])
    # Si un gol no tiene asistencia registrada la celda viene vacía (NaN)
    goles["asistencia"] = goles["asistencia"].fillna("")
    goles["anadido"] = goles["anadido"].fillna(0).astype(int)
    datos["goles"] = goles

    datos["alineaciones"] = _leer("alineaciones.csv")
    datos["cambios"] = _leer("cambios.csv")
    datos["tarjetas"] = _leer("tarjetas.csv")

    tiros = _leer("tiros.csv")
    tiros["completo"] = _si_no(tiros["completo"])
    datos["tiros"] = tiros

    datos["estadisticas"] = _leer("estadisticas.csv")

    # De la clasificación me quedo con la última jornada que haya apuntado
    clasificacion = _leer("clasificacion.csv")
    ultima = clasificacion["tras_jornada"].max()
    datos["clasificacion"] = (
        clasificacion[clasificacion["tras_jornada"] == ultima]
        .sort_values("posicion")
        .reset_index(drop=True)
    )

    proximos = _leer("proximos.csv")
    proximos["fecha"] = pd.to_datetime(proximos["fecha"])
    datos["proximos"] = proximos

    datos["incidencias"] = _leer("incidencias.csv")

    return datos
