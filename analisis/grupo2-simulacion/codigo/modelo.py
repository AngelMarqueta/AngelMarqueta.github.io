"""
Modelo de goles: Poisson con ataque, defensa y ventaja de jugar en casa.

Para un partido entre el local L y el visitante V:

    goles de L ~ Poisson(exp(base + casa + ataque[L] + defensa[V]))
    goles de V ~ Poisson(exp(base        + ataque[V] + defensa[L]))

Un ataque alto significa que el equipo marca más de lo normal; una defensa
alta, que encaja más. Es el modelo clásico de Maher (1982) que después
afinaron Dixon y Coles (1997).

Con solo siete jornadas, cada equipo ha jugado siete partidos y las
estimaciones bailan mucho. Por eso los ataques y las defensas llevan una
penalización que los acerca a cero (a la media del grupo): solo se separan
de ella si los resultados lo justifican. La fuerza de esa penalización se
elige con validación cruzada por jornadas: ajusto el modelo sin una jornada,
mido lo bien que predice esa jornada y me quedo con la que mejor predice.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln
from scipy.stats import poisson


def diseno(locales, visitantes, equipos):
    """
    Matriz de diseño: una fila por goles a explicar (dos por partido).
    Columnas: base, casa, ataque de cada equipo, defensa de cada equipo.
    """
    n = len(equipos)
    indice = {e: i for i, e in enumerate(equipos)}
    filas = np.zeros((2 * len(locales), 2 + 2 * n))
    for k, (l, v) in enumerate(zip(locales, visitantes)):
        i, j = indice[l], indice[v]
        filas[2 * k, [0, 1, 2 + i, 2 + n + j]] = 1          # goles del local
        filas[2 * k + 1, [0, 2 + j, 2 + n + i]] = 1         # goles del visitante
    return filas


def ajustar(partidos, equipos, penalizacion):
    """Máxima verosimilitud penalizada. Devuelve los parámetros y su covarianza aproximada."""
    X = diseno(partidos.local, partidos.visitante, equipos)
    y = np.column_stack([partidos.goles_local, partidos.goles_visitante]).ravel()
    n = len(equipos)
    penal = np.r_[0.0, 0.0, np.full(2 * n, penalizacion)]   # base y casa no se penalizan

    def objetivo(theta):
        eta = X @ theta
        mu = np.exp(eta)
        valor = -(y * eta - mu - gammaln(y + 1)).sum() + 0.5 * (penal * theta ** 2).sum()
        gradiente = -X.T @ (y - mu) + penal * theta
        return valor, gradiente

    inicio = np.zeros(X.shape[1])
    inicio[0] = np.log(max(y.mean(), 0.1))
    resultado = minimize(objetivo, inicio, jac=True, method="L-BFGS-B")
    assert resultado.success, resultado.message
    theta = resultado.x
    mu = np.exp(X @ theta)
    hessiana = X.T @ (X * mu[:, None]) + np.diag(penal)
    # Con penalización la hessiana es invertible aunque ataques y defensas
    # compartan un grado de libertad con la base.
    covarianza = np.linalg.inv(hessiana)
    return {"theta": theta, "covarianza": covarianza, "equipos": list(equipos), "penalizacion": penalizacion}


def tasas(modelo, locales, visitantes, theta=None):
    """Goles esperados del local y del visitante en cada partido."""
    theta = modelo["theta"] if theta is None else theta
    X = diseno(locales, visitantes, modelo["equipos"])
    mu = np.exp(X @ theta)
    return mu[0::2], mu[1::2]


def log_verosimilitud(modelo, partidos):
    """Log-verosimilitud media por partido de los resultados exactos."""
    a, b = tasas(modelo, partidos.local, partidos.visitante)
    return float((poisson.logpmf(partidos.goles_local, a) + poisson.logpmf(partidos.goles_visitante, b)).mean())


def elegir_penalizacion(partidos, equipos, opciones=(0.5, 1, 2, 4, 8, 16, 32, 64)):
    """Validación cruzada dejando fuera una jornada cada vez."""
    puntuaciones = {}
    for opcion in opciones:
        valores = []
        for jornada in sorted(partidos.jornada.unique()):
            entrenamiento = partidos[partidos.jornada != jornada]
            prueba = partidos[partidos.jornada == jornada]
            modelo = ajustar(entrenamiento, equipos, opcion)
            valores.append(log_verosimilitud(modelo, prueba))
        puntuaciones[opcion] = float(np.mean(valores))
    mejor = max(puntuaciones, key=puntuaciones.get)
    return mejor, puntuaciones


def probabilidades_1x2(lambda_local, lambda_visitante, maximo=10):
    """Probabilidad de victoria local, empate y victoria visitante."""
    goles = np.arange(maximo + 1)
    pa = poisson.pmf(goles[:, None], np.atleast_1d(lambda_local)[None, :])
    pb = poisson.pmf(goles[:, None], np.atleast_1d(lambda_visitante)[None, :])
    conjunta = pa[:, None, :] * pb[None, :, :]
    local = np.tril(np.ones((maximo + 1, maximo + 1)), -1)[:, :, None]
    empate = np.eye(maximo + 1)[:, :, None]
    return ((conjunta * local).sum((0, 1)), (conjunta * empate).sum((0, 1)),
            (conjunta * local.transpose(1, 0, 2)).sum((0, 1)))
