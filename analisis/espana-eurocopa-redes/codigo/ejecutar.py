"""
Ejecuta el estudio completo de las redes de pases de España en la Eurocopa 2025.

Uso, desde la carpeta del estudio:
    python codigo/ejecutar.py --cache <carpeta privada para los datos>

Escribe:
    datos/salida/partidos.csv            una fila por partido: ritmo, densidad, concentración…
    datos/salida/jugadoras_partido.csv   una fila por jugadora y partido: centralidad y posición media
    datos/salida/jugadoras_torneo.csv    medias del torneo por jugadora
    datos/salida/conexiones.csv          pases entre cada pareja en cada partido
    documentacion/validacion.json        comprobaciones de los datos
    documentacion/manifiesto_descargas.json
    graficos/ y publicaciones/instagram/
"""
import argparse
import json
import platform
from importlib import metadata
from pathlib import Path

import pandas as pd

from datos import COMMIT, EQUIPO, descargar, nombres_cortos, partidos_de_espana
from redes import analizar_partido
from visualizaciones import COMPLETO, crear_carrusel, crear_figuras

RAIZ = Path(__file__).resolve().parents[1]


def comprobar(partidos, resultados, total_partidos_torneo):
    """Comprobaciones que, si fallan, detienen el análisis."""
    assert total_partidos_torneo == 31, "La Eurocopa 2025 tuvo 31 partidos"
    assert len(partidos) == 6, "España jugó seis partidos"
    validacion = {"partidos_torneo": total_partidos_torneo, "partidos_espana": len(partidos), "por_partido": []}
    for partido, (pases, g, tabla, resumen) in zip(partidos, resultados):
        ids = [e["id"] for e in partido["eventos"]]
        once = next(e for e in partido["eventos"] if e["type"]["name"] == "Starting XI" and e["team"]["name"] == EQUIPO)
        titulares = {j["player"]["name"] for j in once["tactics"]["lineup"]}
        en_red = set(pases.pasadora) | set(pases.receptora)
        comprobacion = {
            "rival": partido["rival"],
            "eventos": len(ids),
            "eventos_duplicados": len(ids) - len(set(ids)),
            "pases_red": int(len(pases)),
            "jugadoras_en_red": len(en_red),
            "todas_titulares": en_red <= titulares,
            "coordenadas_fuera": int(((pases[["x", "x_fin"]] < 0) | (pases[["x", "x_fin"]] > 120)).any(axis=1).sum()
                                     + ((pases[["y", "y_fin"]] < 0) | (pases[["y", "y_fin"]] > 80)).any(axis=1).sum()),
            "suma_grado_igual_doble_pases": int(tabla.pases_red.sum()) == 2 * int(len(pases)),
        }
        # Antes del primer cambio solo pueden aparecer las titulares.
        assert comprobacion["eventos_duplicados"] == 0
        assert comprobacion["todas_titulares"], f"Hay suplentes en la red ante {partido['rival']}"
        assert comprobacion["coordenadas_fuera"] == 0
        assert comprobacion["suma_grado_igual_doble_pases"]
        assert len(pases) >= 200, "Muestra demasiado pequeña para una red"
        validacion["por_partido"].append(comprobacion)
    return validacion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=RAIZ / "datos" / "privados")
    args = parser.parse_args()
    salida, doc = RAIZ / "datos" / "salida", RAIZ / "documentacion"
    salida.mkdir(parents=True, exist_ok=True)
    doc.mkdir(parents=True, exist_ok=True)

    print("Descargando los partidos de España…", flush=True)
    partidos, manifiesto, total = partidos_de_espana(args.cache)
    resultados = [analizar_partido(p, EQUIPO) for p in partidos]
    validacion = comprobar(partidos, resultados, total)

    resumenes, filas_jugadoras, filas_conexiones, para_graficos = [], [], [], []
    for partido, (pases, g, tabla, resumen) in zip(partidos, resultados):
        nombres = nombres_cortos(partido["alineaciones"])
        pases = pases.assign(pasadora=pases.pasadora.map(nombres), receptora=pases.receptora.map(nombres))
        tabla = tabla.rename(index=nombres)
        resumen = dict(resumen, jugadora_mas_central=nombres[resumen["jugadora_mas_central"]],
                       pareja_principal=" → ".join(nombres[n] for n in resumen["pareja_principal"].split(" → ")))
        resumenes.append(resumen)
        para_graficos.append((partido, pases, tabla))
        filas_jugadoras.append(tabla.reset_index().assign(partido_id=partido["partido_id"], rival=partido["rival"],
                                                          fase=partido["fase"]))
        conexiones = pases.groupby(["pasadora", "receptora"]).size().reset_index(name="pases")
        filas_conexiones.append(conexiones.assign(partido_id=partido["partido_id"], rival=partido["rival"]))

    resumen = pd.DataFrame(resumenes)
    por_jugadora = pd.concat(filas_jugadoras, ignore_index=True)
    torneo = (por_jugadora.groupby("jugadora")
              .agg(redes=("partido_id", "size"), pases_red_media=("pases_red", "mean"),
                   intermediacion_media=("intermediacion", "mean"), pagerank_medio=("pagerank", "mean"))
              .sort_values("intermediacion_media", ascending=False).reset_index())
    torneo["nombre"] = torneo.jugadora.map(lambda n: COMPLETO.get(n, n))

    resumen.to_csv(salida / "partidos.csv", index=False)
    por_jugadora.round(4).to_csv(salida / "jugadoras_partido.csv", index=False)
    torneo.round(4).to_csv(salida / "jugadoras_torneo.csv", index=False)
    pd.concat(filas_conexiones, ignore_index=True).to_csv(salida / "conexiones.csv", index=False)

    ruta_logo = RAIZ / "recursos" / "statsbomb.png"
    _, registro_licencia = descargar("LICENSE.pdf", args.cache)
    manifiesto.append(registro_licencia)
    (doc / "manifiesto_descargas.json").write_text(
        json.dumps({"commit": COMMIT, "archivos": manifiesto}, ensure_ascii=False, indent=2), encoding="utf-8")

    validacion["python"] = platform.python_version()
    validacion["dependencias"] = {p: metadata.version(p) for p in
                                  ("pandas", "numpy", "networkx", "matplotlib", "mplsoccer")}
    (doc / "validacion.json").write_text(json.dumps(validacion, ensure_ascii=False, indent=2), encoding="utf-8")

    central_final = crear_figuras(para_graficos, resumen, por_jugadora, ruta_logo, RAIZ / "graficos")
    crear_carrusel(resumen, central_final, RAIZ / "graficos", RAIZ / "publicaciones" / "instagram")

    pd.set_option("display.width", 200)
    print(resumen[["fecha", "rival", "resultado", "minutos_red", "pases_red", "pases_por_minuto",
                   "centralizacion", "jugadora_mas_central"]].to_string(index=False))
    print(torneo[torneo.redes >= 3].head(8).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
