"""
Pruebas de la simulación con ligas inventadas.

Ejecutar desde la carpeta del estudio:  python -m pytest pruebas
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codigo"))
from datos import clasificacion_desde_resultados, matriz_goles, partidos_pendientes  # noqa: E402
from modelo import ajustar, probabilidades_1x2  # noqa: E402
from simulacion import ordenar, resumir, simular  # noqa: E402


def liga(resultados):
    return pd.DataFrame(resultados, columns=["jornada", "local", "visitante", "goles_local", "goles_visitante"])


def test_clasificacion_desde_resultados():
    tabla = clasificacion_desde_resultados(liga([(1, "A", "B", 2, 0), (1, "C", "D", 1, 1), (2, "B", "C", 0, 3)]))
    assert tabla.loc["A", "puntos"] == 3
    assert tabla.loc["C", "puntos"] == 4
    assert tabla.loc["B", "gc"] == 5
    assert tabla.pj.sum() == 6


def test_partidos_pendientes_doble_vuelta():
    equipos, pendientes = partidos_pendientes(liga([(1, "A", "B", 1, 0), (1, "C", "D", 0, 0)]))
    # 4 equipos a doble vuelta = 12 partidos; se han jugado 2.
    assert len(pendientes) == 10
    assert ("A", "B") not in set(zip(pendientes.local, pendientes.visitante))
    assert ("B", "A") in set(zip(pendientes.local, pendientes.visitante))


def test_desempate_a_dos_por_diferencia_particular():
    # A y B empatan a puntos; B ganó el partido entre ellos aunque A tiene mejor diferencia general.
    goles = np.full((2, 2, 2), np.nan)
    goles[0, 1] = (0, 1)   # A 0-1 B
    goles[1, 0] = (0, 0)   # B 0-0 A
    orden = ordenar(np.array([10, 10]), np.array([15, 3]), np.array([30, 20]), goles, np.array([0.1, 0.9]))
    assert orden == [1, 0]


def test_desempate_a_tres_por_puntos_entre_ellos():
    # Tres empatados: C ganó a A y a B; A ganó a B.
    goles = np.full((3, 3, 2), np.nan)
    goles[2, 0] = (1, 0)
    goles[2, 1] = (1, 0)
    goles[0, 1] = (2, 1)
    orden = ordenar(np.array([20, 20, 20]), np.array([9, 9, 0]), np.array([20, 20, 10]), goles, np.zeros(3))
    assert orden == [2, 0, 1]


def test_probabilidades_1x2_suman_uno_y_son_simetricas():
    local, empate, visitante = probabilidades_1x2(np.array([1.3, 2.0]), np.array([1.3, 0.5]))
    assert np.allclose(local + empate + visitante, 1, atol=1e-6)
    assert local[0] == pytest.approx(visitante[0])
    assert local[1] > visitante[1]


def test_el_modelo_distingue_al_equipo_fuerte():
    rng = np.random.default_rng(1)
    equipos = ["Fuerte", "Medio", "Flojo", "Otro"]
    filas = []
    marca = {"Fuerte": 2.5, "Medio": 1.2, "Flojo": 0.5, "Otro": 1.2}
    for vuelta in range(6):
        for a in equipos:
            for b in equipos:
                if a != b:
                    filas.append((vuelta, a, b, rng.poisson(marca[a]), rng.poisson(marca[b])))
    modelo = ajustar(liga(filas), equipos, penalizacion=1)
    ataque = dict(zip(equipos, modelo["theta"][2:6]))
    assert ataque["Fuerte"] > ataque["Medio"] > ataque["Flojo"]


def test_temporada_terminada_no_tiene_azar():
    # Si ya no queda nada por jugar, todas las simulaciones dan la misma tabla.
    partidos = liga([(1, "A", "B", 3, 0), (2, "B", "A", 0, 2)])
    equipos, pendientes = partidos_pendientes(partidos)
    assert pendientes.empty
    modelo = ajustar(partidos, equipos, 4)
    puestos, puntos = simular(modelo, matriz_goles(partidos, equipos), pendientes, n=50)
    tabla, distribucion = resumir(puestos, puntos, equipos)
    assert distribucion.loc["A", 1] == 1
    assert tabla.set_index("equipo").loc["A", "ascenso_directo"] == 1
