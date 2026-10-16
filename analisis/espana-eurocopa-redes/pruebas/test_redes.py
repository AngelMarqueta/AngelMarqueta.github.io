"""
Pruebas de las redes de pases con partidos inventados, donde sé el resultado.

Ejecutar desde la carpeta del estudio:  python -m pytest pruebas
"""
import sys
from pathlib import Path

import networkx as nx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codigo"))
from redes import analizar_partido, centralizacion, grafo, minuto_corte, pases_de_red  # noqa: E402

EQUIPO = "Rojas"


def pase(minuto, de, a, parte=1, tipo=None, fallado=False, equipo=EQUIPO, x=50.0, y=40.0):
    evento = {"id": f"{parte}-{minuto}-{de}-{a}", "type": {"name": "Pass"}, "team": {"name": equipo},
              "player": {"name": de}, "period": parte, "minute": int(minuto), "second": 0,
              "location": [x, y],
              "pass": {"recipient": {"name": a}, "end_location": [x + 5, y]}}
    if tipo:
        evento["pass"]["type"] = {"name": tipo}
    if fallado:
        evento["pass"]["outcome"] = {"name": "Incomplete"}
    return evento


def cambio(minuto, parte=2, equipo=EQUIPO):
    return {"id": f"c{minuto}", "type": {"name": "Substitution"}, "team": {"name": equipo},
            "period": parte, "minute": minuto, "second": 0}


def test_solo_cuentan_pases_completados_en_juego():
    eventos = [pase(1, "A", "B"), pase(2, "A", "B", fallado=True), pase(3, "A", "B", tipo="Throw-in"),
               pase(4, "A", "B", equipo="Azules"), pase(5, "B", "A"), cambio(60)]
    pases, _ = pases_de_red(eventos, EQUIPO)
    assert len(pases) == 2


def test_el_corte_respeta_el_descuento_de_la_primera_parte():
    # Cambio en el descanso (minuto 45 de la segunda parte). Un pase en el 46 de la
    # primera parte es anterior y debe contar; uno en el 50 de la segunda, no.
    eventos = [pase(46, "A", "B", parte=1), cambio(45, parte=2), pase(50, "A", "B", parte=2)]
    assert minuto_corte(eventos, EQUIPO) == (2, 45.0)
    pases, _ = pases_de_red(eventos, EQUIPO)
    assert len(pases) == 1


def test_sin_cambios_se_usa_todo_el_partido():
    eventos = [pase(10, "A", "B"), pase(80, "B", "A", parte=2)]
    assert minuto_corte(eventos, EQUIPO) == (2, 80.0)


def test_grafo_pesos_y_distancias():
    eventos = [pase(i, "A", "B") for i in range(4)] + [pase(10, "B", "C")] + [cambio(60)]
    pases, _ = pases_de_red(eventos, EQUIPO)
    g = grafo(pases)
    assert g["A"]["B"]["pases"] == 4
    assert g["A"]["B"]["distancia"] == pytest.approx(0.25)


def test_intermediacion_de_una_cadena():
    # A → B → C: todos los caminos de A a C pasan por B.
    eventos = [pase(1, "A", "B"), pase(2, "B", "C"), cambio(60)]
    partido = {"partido_id": 1, "fecha": "2025-01-01", "fase": "Final", "rival": "Azules",
               "goles_espana": 1, "goles_rival": 0, "eventos": eventos}
    pases, g, tabla, resumen = analizar_partido(partido, EQUIPO)
    assert tabla.intermediacion.idxmax() == "B"
    assert tabla.loc["B", "pases_red"] == 2
    assert tabla.pases_red.sum() == 2 * len(pases)
    assert resumen["jugadora_mas_central"] == "B"


def test_centralizacion_extremos():
    assert centralizacion([5, 5, 5, 5]) == 0
    assert centralizacion([3, 1, 1, 1]) == pytest.approx(2 / 3)
    assert centralizacion([4, 0, 0, 0]) == 1
    # Con una estrella, el valor coincide con la fórmula general de Freeman.
    g = nx.star_graph(4)
    grados = [d for _, d in g.degree()]
    assert centralizacion(grados) == pytest.approx(1.0 * sum(max(grados) - d for d in grados) / ((len(grados) - 1) * max(grados)))


def test_posiciones_medias():
    eventos = [pase(1, "A", "B", x=10, y=20), pase(2, "A", "B", x=30, y=20), cambio(60)]
    partido = {"partido_id": 1, "fecha": "", "fase": "", "rival": "", "goles_espana": 0, "goles_rival": 0,
               "eventos": eventos}
    _, _, tabla, _ = analizar_partido(partido, EQUIPO)
    # A da pases desde x=10 y x=30; B los recibe en x=15 y x=35.
    assert tabla.loc["A", "x"] == pytest.approx(20)
    assert tabla.loc["B", "x"] == pytest.approx(25)
