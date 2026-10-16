"""
Simulación del grupo 2 de Primera Federación 2026/27.

Uso, desde la raíz del repositorio:
    python analisis/grupo2-simulacion/codigo/ejecutar.py

Pasos:
1. Lee los resultados y comprueba que reproducen la clasificación publicada.
2. Elige la penalización del modelo con validación cruzada por jornadas.
3. Ajusta el modelo y simula 10.000 veces el resto de la temporada.
4. Repite la simulación con los datos que había en cada jornada anterior
   (desde la 3) para ver cómo ha cambiado la previsión.
5. Escribe tablas, gráficas, carrusel y el registro de validación.

Se ejecuta en unos segundos; está pensado para repetirse después de cada jornada.
"""
import json
import platform
from importlib import metadata
from pathlib import Path

import numpy as np
import pandas as pd

from datos import comprobar_contra_clasificacion, leer_resultados, matriz_goles, partidos_pendientes
from modelo import ajustar, elegir_penalizacion, log_verosimilitud, probabilidades_1x2, tasas
from simulacion import resumir, simular
from visualizaciones import EQUIPO, crear_carrusel, crear_figuras

RAIZ = Path(__file__).resolve().parents[1]
SIMULACIONES = 10_000


def referencia_sin_equipos(partidos, equipos):
    """Log-verosimilitud de un modelo que solo sabe que el local marca más (sin fuerzas de equipo)."""
    valores = []
    for jornada in sorted(partidos.jornada.unique()):
        entrenamiento = partidos[partidos.jornada != jornada]
        prueba = partidos[partidos.jornada == jornada]
        modelo = ajustar(entrenamiento, equipos, 1e6)       # penalización enorme: todos los equipos iguales
        valores.append(log_verosimilitud(modelo, prueba))
    return float(np.mean(valores))


def main():
    salida, doc = RAIZ / "datos" / "salida", RAIZ / "documentacion"
    salida.mkdir(parents=True, exist_ok=True)
    doc.mkdir(parents=True, exist_ok=True)

    partidos = leer_resultados()
    jornada = comprobar_contra_clasificacion(partidos)
    equipos, pendientes = partidos_pendientes(partidos)
    penalizacion, puntuaciones = elegir_penalizacion(partidos, equipos)
    referencia = referencia_sin_equipos(partidos, equipos)
    modelo = ajustar(partidos, equipos, penalizacion)
    print(f"Tras la jornada {jornada}: {len(partidos)} partidos jugados y {len(pendientes)} pendientes. "
          f"Penalización elegida: {penalizacion}", flush=True)

    puestos, puntos = simular(modelo, matriz_goles(partidos, equipos), pendientes, n=SIMULACIONES)
    tabla, distribucion = resumir(puestos, puntos, equipos)

    # Fuerzas estimadas de cada equipo (en goles por partido frente a un rival medio, en campo neutral).
    n = len(equipos)
    base, casa = modelo["theta"][:2]
    fuerzas = pd.DataFrame({
        "equipo": equipos,
        "goles_a_favor_esperados": np.exp(base + casa / 2 + modelo["theta"][2:2 + n]),
        "goles_en_contra_esperados": np.exp(base + casa / 2 + modelo["theta"][2 + n:]),
    }).sort_values("goles_a_favor_esperados", ascending=False)

    # Probabilidades de los próximos partidos pendientes del Zaragoza.
    propios = pendientes[(pendientes.local == EQUIPO) | (pendientes.visitante == EQUIPO)].copy()
    a, b = tasas(modelo, propios.local, propios.visitante)
    p1, px, p2 = probabilidades_1x2(a, b)
    propios = propios.assign(goles_local_esperados=a, goles_visitante_esperados=b,
                             victoria_local=p1, empate=px, victoria_visitante=p2)

    # Evolución: misma simulación con los datos de cada jornada anterior. La última
    # jornada es la simulación principal, para que la gráfica y las cifras coincidan.
    def fila_evolucion(corte, resumen):
        fila = resumen[resumen.equipo == EQUIPO].iloc[0]
        return {"jornada": corte, "ascenso_directo": fila.ascenso_directo,
                "ascenso_o_playoff": fila.ascenso_o_playoff, "descenso": fila.descenso,
                "puntos_medios": fila.puntos_medios}

    evolucion = []
    for corte in range(3, jornada):
        hasta = partidos[partidos.jornada <= corte]
        _, pend = partidos_pendientes(hasta)
        m = ajustar(hasta, equipos, penalizacion)
        pu, pt = simular(m, matriz_goles(hasta, equipos), pend, n=4_000, semilla=corte)
        t, _ = resumir(pu, pt, equipos)
        evolucion.append(fila_evolucion(corte, t))
    evolucion.append(fila_evolucion(jornada, tabla))
    evolucion = pd.DataFrame(evolucion)

    tabla.round(4).to_csv(salida / "probabilidades.csv", index=False)
    distribucion.round(4).rename_axis("equipo").to_csv(salida / "distribucion_puestos.csv")
    fuerzas.round(3).to_csv(salida / "fuerzas_equipos.csv", index=False)
    propios.round(3).to_csv(salida / "partidos_zaragoza.csv", index=False)
    evolucion.round(4).to_csv(salida / "evolucion_zaragoza.csv", index=False)

    fila = tabla[tabla.equipo == EQUIPO].iloc[0]
    validacion = {
        "tras_jornada": jornada,
        "partidos_jugados": len(partidos),
        "partidos_pendientes": len(pendientes),
        "clasificacion_reproducida": True,
        "simulaciones": SIMULACIONES,
        "penalizacion": penalizacion,
        "validacion_cruzada_log_verosimilitud": puntuaciones,
        "referencia_sin_fuerzas_de_equipo": referencia,
        "mejora_sobre_referencia": puntuaciones[penalizacion] - referencia,
        "ventaja_local_multiplicativa": float(np.exp(casa)),
        "suma_probabilidades_por_puesto": float(distribucion.sum(axis=0).round(6).min()),
        "error_muestreo_maximo_pp": float(100 * 0.5 / np.sqrt(SIMULACIONES) * 1.96),
        "zaragoza": {k: float(fila[k]) for k in ("ascenso_directo", "playoff", "descenso", "puntos_medios")},
        "python": platform.python_version(),
        "dependencias": {p: metadata.version(p) for p in ("pandas", "numpy", "scipy", "matplotlib")},
    }
    assert np.allclose(distribucion.sum(axis=0), 1) and np.allclose(distribucion.sum(axis=1), 1)
    (doc / "validacion.json").write_text(json.dumps(validacion, ensure_ascii=False, indent=2), encoding="utf-8")

    crear_figuras(tabla, distribucion, evolucion, jornada, SIMULACIONES, RAIZ / "graficos")
    crear_carrusel(tabla, jornada, RAIZ / "graficos", RAIZ / "publicaciones" / "instagram")

    pd.set_option("display.width", 200)
    print(tabla[["equipo", "ascenso_directo", "playoff", "descenso", "puntos_medios"]].round(3).to_string(index=False))
    print(evolucion.round(3).to_string(index=False))
    print(json.dumps({k: validacion[k] for k in ("penalizacion", "referencia_sin_fuerzas_de_equipo",
                                                 "mejora_sobre_referencia", "ventaja_local_multiplicativa")}, indent=2))


if __name__ == "__main__":
    main()
