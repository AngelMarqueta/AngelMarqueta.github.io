"""
Simulación Monte Carlo del resto de la temporada.

En cada simulación:
1. Saco unas fuerzas de ataque y defensa de la distribución del modelo
   (su estimación más la incertidumbre). Así una racha corta no se toma
   como si fuera la fuerza real del equipo.
2. Juego todos los partidos pendientes con goles de Poisson.
3. Ordeno la tabla final con el reglamento de Primera Federación (artículo 12):
   puntos; si hay empate, los puntos entre los empatados (cuando son tres o
   más), la diferencia de goles entre ellos, la diferencia general y los goles
   a favor. El juego limpio y el partido de desempate no se pueden simular:
   si todo lo anterior coincide, se sortea.

Con 10.000 simulaciones, la probabilidad de cada puesto tiene un error de
muestreo de como mucho medio punto porcentual (para una probabilidad del 50 %).
"""
import numpy as np

from modelo import tasas


def _diferencias_entre(grupo, goles):
    """Puntos y diferencia de goles de los equipos de «grupo» en sus partidos entre ellos."""
    puntos = np.zeros(len(grupo))
    diferencia = np.zeros(len(grupo))
    for a_pos, a in enumerate(grupo):
        for b_pos, b in enumerate(grupo):
            if a == b:
                continue
            ga, gb = goles[a, b]
            if np.isnan(ga):
                continue
            puntos[a_pos] += 3 if ga > gb else (1 if ga == gb else 0)
            puntos[b_pos] += 3 if gb > ga else (1 if ga == gb else 0)
            diferencia[a_pos] += ga - gb
            diferencia[b_pos] += gb - ga
    return puntos, diferencia


def ordenar(puntos, diferencia, a_favor, goles, azar):
    """Devuelve los índices de los equipos del primero al último."""
    orden = []
    for valor in sorted(set(puntos), reverse=True):
        grupo = [i for i in range(len(puntos)) if puntos[i] == valor]
        if len(grupo) == 1:
            orden += grupo
            continue
        p_entre, d_entre = _diferencias_entre(grupo, goles)
        if len(grupo) == 2:
            p_entre = np.zeros(2)          # con dos equipos, el reglamento empieza por la diferencia
        claves = [(-p_entre[k], -d_entre[k], -diferencia[i], -a_favor[i], azar[i]) for k, i in enumerate(grupo)]
        orden += [i for _, i in sorted(zip(claves, grupo))]
    return orden


def simular(modelo, goles_jugados, pendientes, n=10_000, semilla=2027):
    """
    Devuelve una matriz n × equipos con el puesto final (1 = primero) de cada
    equipo en cada simulación, y los puntos finales.
    """
    rng = np.random.default_rng(semilla)
    equipos = modelo["equipos"]
    indice = {e: i for i, e in enumerate(equipos)}
    li = np.array([indice[e] for e in pendientes.local], dtype=int)
    vi = np.array([indice[e] for e in pendientes.visitante], dtype=int)
    sorteos = rng.multivariate_normal(modelo["theta"], modelo["covarianza"], size=n)

    puestos = np.zeros((n, len(equipos)), dtype=int)
    puntos_finales = np.zeros((n, len(equipos)))
    for s in range(n):
        a, b = tasas(modelo, pendientes.local, pendientes.visitante, theta=sorteos[s])
        goles = goles_jugados.copy()
        goles[li, vi, 0] = rng.poisson(a)
        goles[li, vi, 1] = rng.poisson(b)
        gl, gv = goles[..., 0], goles[..., 1]
        mascara = ~np.isnan(gl)
        victoria = np.where(mascara, gl > gv, False)
        empate = np.where(mascara, gl == gv, False)
        derrota = np.where(mascara, gl < gv, False)
        puntos = 3 * victoria.sum(1) + empate.sum(1) + 3 * derrota.sum(0) + empate.sum(0)
        a_favor = np.nansum(gl, 1) + np.nansum(gv, 0)
        en_contra = np.nansum(gv, 1) + np.nansum(gl, 0)
        orden = ordenar(puntos, a_favor - en_contra, a_favor, goles, rng.random(len(equipos)))
        puestos[s, orden] = np.arange(1, len(equipos) + 1)
        puntos_finales[s] = puntos
    return puestos, puntos_finales


def resumir(puestos, puntos_finales, equipos):
    """Probabilidades por equipo: ascenso directo (1.º), playoff (2.º-5.º) y descenso (16.º-20.º)."""
    import pandas as pd

    tabla = pd.DataFrame({
        "equipo": equipos,
        "ascenso_directo": (puestos == 1).mean(0),
        "playoff": ((puestos >= 2) & (puestos <= 5)).mean(0),
        "descenso": (puestos >= 16).mean(0),
        "puesto_medio": puestos.mean(0),
        "puntos_medios": puntos_finales.mean(0),
        "puntos_p10": np.percentile(puntos_finales, 10, axis=0),
        "puntos_p90": np.percentile(puntos_finales, 90, axis=0),
    })
    tabla["ascenso_o_playoff"] = tabla.ascenso_directo + tabla.playoff
    distribucion = pd.DataFrame(
        np.array([[(puestos[:, i] == p).mean() for p in range(1, len(equipos) + 1)] for i in range(len(equipos))]),
        index=equipos, columns=range(1, len(equipos) + 1))
    return tabla.sort_values("puntos_medios", ascending=False).reset_index(drop=True), distribucion
