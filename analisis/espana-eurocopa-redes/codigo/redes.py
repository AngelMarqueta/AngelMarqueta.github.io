"""
Construcción de las redes de pases y medidas de centralidad.

Una red de pases es un grafo dirigido: cada jugadora es un nodo y cada flecha
A → B pesa tantos pases completados como A dio a B. Sigo la convención más
habitual:

* Solo pases completados en juego (en StatsBomb, un pase sin «outcome» es un
  pase que llegó a su destino). Quito los saques de banda, de esquina, de
  puerta, de falta y de centro, porque no son decisiones de circulación.
* Solo hasta el primer cambio de España. Así las once jugadoras están en el
  campo todo el tramo y la red se puede comparar entre ellas.
* La posición de cada jugadora es la media de los sitios donde dio y recibió
  pases en ese tramo.

Medidas por jugadora:
* pases_red: pases dados más recibidos dentro de la red (grado ponderado).
* intermediacion: cuántos de los caminos más cortos entre compañeras pasan por
  ella. Para que «más pases» sea «más cerca», la distancia de cada flecha es
  1 / número de pases.
* pagerank: importancia de recibir de jugadoras que a su vez reciben mucho.

Medida del equipo:
* centralizacion: lo concentrado que está el juego en una jugadora. Va de 0
  (todas igual de conectadas) a 1 (todo pasa por una). Fórmula de Freeman con
  el grado ponderado: suma de (máximo − valor de cada una) / ((n − 1) · máximo).
"""
import networkx as nx
import numpy as np
import pandas as pd

REINICIOS = {"Throw-in", "Corner", "Goal Kick", "Free Kick", "Kick Off"}


def instante(evento):
    """
    Momento de un evento como (parte, minuto con decimales).

    Se compara la pareja y no solo el minuto porque StatsBomb sigue contando el
    descuento de la primera parte (minuto 46, 47…) y la segunda vuelve a
    empezar en el 45: un cambio en el descanso y un pase en el 46 de la
    primera parte tienen minutos que no se pueden comparar por sí solos.
    """
    return (evento["period"], evento["minute"] + evento["second"] / 60)


def minuto_corte(eventos, equipo):
    """Instante del primer cambio del equipo; si no hubo cambios, el final del partido."""
    cambios = [e for e in eventos if e["type"]["name"] == "Substitution" and e["team"]["name"] == equipo]
    if not cambios:
        return max(instante(e) for e in eventos if e["period"] <= 2)
    return min(instante(e) for e in cambios)


def pases_de_red(eventos, equipo):
    """Pases completados en juego entre jugadoras del equipo antes del primer cambio."""
    corte = minuto_corte(eventos, equipo)
    filas = []
    for e in eventos:
        if e["type"]["name"] != "Pass" or e["team"]["name"] != equipo:
            continue
        pase = e["pass"]
        if "outcome" in pase or "recipient" not in pase:
            continue          # pase fallado, fuera de juego o sin receptora
        if pase.get("type", {}).get("name") in REINICIOS:
            continue
        if e["period"] > 2 or instante(e) >= corte:
            continue
        filas.append({
            "pasadora": e["player"]["name"],
            "receptora": pase["recipient"]["name"],
            "x": e["location"][0], "y": e["location"][1],
            "x_fin": pase["end_location"][0], "y_fin": pase["end_location"][1],
        })
    return pd.DataFrame(filas, columns=["pasadora", "receptora", "x", "y", "x_fin", "y_fin"]), corte


def posiciones_medias(pases):
    """Media de los puntos donde cada jugadora da (origen) y recibe (destino) pases."""
    dados = pases[["pasadora", "x", "y"]].rename(columns={"pasadora": "jugadora"})
    recibidos = pases[["receptora", "x_fin", "y_fin"]].rename(columns={"receptora": "jugadora", "x_fin": "x", "y_fin": "y"})
    puntos = pd.concat([dados, recibidos])
    return puntos.groupby("jugadora").agg(x=("x", "mean"), y=("y", "mean"), toques=("x", "size"))


def grafo(pases):
    g = nx.DiGraph()
    for (origen, destino), n in pases.groupby(["pasadora", "receptora"]).size().items():
        if origen != destino:
            g.add_edge(origen, destino, pases=int(n), distancia=1 / n)
    return g


def centralizacion(valores):
    """Centralización de Freeman sobre un conjunto de valores no negativos."""
    valores = np.asarray(valores, dtype=float)
    if len(valores) < 2 or valores.max() == 0:
        return 0.0
    return float((valores.max() - valores).sum() / ((len(valores) - 1) * valores.max()))


def medidas(g):
    """Tabla por jugadora con las tres medidas de centralidad."""
    grado = dict(g.degree(weight="pases"))
    intermediacion = nx.betweenness_centrality(g, weight="distancia", normalized=True)
    pagerank = nx.pagerank(g, weight="pases")
    tabla = pd.DataFrame({"pases_red": grado, "intermediacion": intermediacion, "pagerank": pagerank})
    tabla.index.name = "jugadora"
    return tabla.sort_values("pases_red", ascending=False)


def analizar_partido(partido, equipo):
    """Red, posiciones y medidas de un partido. Devuelve también un resumen del equipo."""
    pases, corte = pases_de_red(partido["eventos"], equipo)
    # Minutos jugados hasta el corte, contando el descuento de la primera parte si el corte es posterior.
    descuento_1 = max((e["minute"] + e["second"] / 60 for e in partido["eventos"] if e["period"] == 1), default=45) - 45
    minutos_red = corte[1] if corte[0] == 1 else corte[1] + descuento_1
    g = grafo(pases)
    tabla = medidas(g).join(posiciones_medias(pases))
    parejas = pases.groupby(["pasadora", "receptora"]).size()
    resumen = {
        "partido_id": partido["partido_id"],
        "fecha": partido["fecha"],
        "fase": partido["fase"],
        "rival": partido["rival"],
        "resultado": f"{partido['goles_espana']}-{partido['goles_rival']}",
        "parte_corte": corte[0],
        "minuto_corte": round(corte[1], 1),
        "minutos_red": round(minutos_red, 1),
        "pases_red": int(len(pases)),
        "pases_por_minuto": round(len(pases) / minutos_red, 2),
        "jugadoras": int(g.number_of_nodes()),
        "conexiones": int(g.number_of_edges()),
        "densidad": round(nx.density(g), 3),
        "centralizacion": round(centralizacion(tabla.pases_red), 3),
        "pareja_principal": " → ".join(parejas.idxmax()) if len(parejas) else "",
        "pases_pareja_principal": int(parejas.max()) if len(parejas) else 0,
        "jugadora_mas_central": tabla.intermediacion.idxmax() if len(tabla) else "",
    }
    return pases, g, tabla, resumen
