"""
Descarga de los datos de StatsBomb Open Data y lectura de los partidos de España.

La descarga está fijada a un commit concreto del repositorio de StatsBomb para
que el análisis se pueda repetir con los mismos archivos. Lo descargado se
guarda en una carpeta de caché privada: el acuerdo de StatsBomb no permite
redistribuir sus datos, así que esa carpeta nunca se sube a Git.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

COMMIT = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
BASE = f"https://raw.githubusercontent.com/hudl/open-data/{COMMIT}"

COMPETICION, TEMPORADA = 53, 315          # Eurocopa femenina 2025
EQUIPO = "Spain Women's"


def descargar(ruta, cache):
    """Devuelve el contenido de un archivo del repositorio y su registro de procedencia."""
    destino = Path(cache) / ruta
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        for intento in range(3):
            try:
                peticion = Request(f"{BASE}/{ruta}", headers={"User-Agent": "LineaDePase/1.0"})
                with urlopen(peticion, timeout=60) as respuesta:
                    contenido = respuesta.read()
                temporal = destino.with_suffix(destino.suffix + ".tmp")
                temporal.write_bytes(contenido)
                temporal.replace(destino)
                break
            except Exception as error:
                # Un 403 o un 429 significa que no debemos insistir.
                if getattr(error, "code", None) in (403, 429) or intento == 2:
                    raise
                time.sleep(2 ** intento)
    contenido = destino.read_bytes()
    registro = {
        "ruta": ruta,
        "url": f"{BASE}/{ruta}",
        "sha256": hashlib.sha256(contenido).hexdigest(),
        "bytes": len(contenido),
        "fecha_descarga_utc": datetime.fromtimestamp(destino.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"),
    }
    return contenido, registro


def partidos_de_espana(cache):
    """Los partidos de España en el torneo, ordenados por fecha, con sus eventos y alineaciones."""
    contenido, registro = descargar(f"data/matches/{COMPETICION}/{TEMPORADA}.json", cache)
    manifiesto = [registro]
    partidos = json.loads(contenido)
    propios = [p for p in partidos if EQUIPO in (p["home_team"]["home_team_name"], p["away_team"]["away_team_name"])]
    propios.sort(key=lambda p: p["match_date"])

    resultado = []
    for p in propios:
        eventos, reg_e = descargar(f"data/events/{p['match_id']}.json", cache)
        alineaciones, reg_a = descargar(f"data/lineups/{p['match_id']}.json", cache)
        manifiesto += [reg_e, reg_a]
        local = p["home_team"]["home_team_name"]
        rival = p["away_team"]["away_team_name"] if local == EQUIPO else local
        resultado.append({
            "partido_id": p["match_id"],
            "fecha": p["match_date"],
            "fase": p["competition_stage"]["name"],
            "rival": rival.replace(" Women's", ""),
            "local": local == EQUIPO,
            "goles_espana": p["home_score"] if local == EQUIPO else p["away_score"],
            "goles_rival": p["away_score"] if local == EQUIPO else p["home_score"],
            "eventos": json.loads(eventos),
            "alineaciones": json.loads(alineaciones),
        })
    return resultado, manifiesto, len(partidos)


def nombres_cortos(alineaciones):
    """
    StatsBomb guarda el nombre completo («Olga  Carmona García»); para las
    gráficas uso el apodo deportivo si existe («Olga Carmona»).
    """
    nombres = {}
    for equipo in alineaciones:
        for jugadora in equipo["lineup"]:
            apodo = jugadora.get("player_nickname")
            nombres[jugadora["player_name"]] = apodo if apodo else " ".join(jugadora["player_name"].split())
    return nombres
