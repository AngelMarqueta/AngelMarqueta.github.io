"""
Actualiza todo el análisis del Real Zaragoza 2026/27.

Uso (desde la raíz del repositorio):
    python analisis/real-zaragoza/codigo/actualizar.py

Pasos:
    1. Lee los CSV de datos/entrada.
    2. Comprueba que todo cuadra. Si algo falla, para y no toca la web.
    3. Calcula las tablas y las guarda en datos/salida.
    4. Dibuja los gráficos.
    5. Genera el JSON del panel de la web y el informe completo.

Después de cada partido solo hay que añadir filas a los CSV de entrada,
revisar textos/conclusiones.html y volver a ejecutar este archivo.
"""

import json
import sys

import pandas as pd

import calculos
import comprobaciones
import graficos
import informe
from cargar_datos import CARPETA_SALIDA, LIGA, RAIZ_WEB, cargar_todo

# Dónde escribe en la web
JSON_WEB = RAIZ_WEB / "datos" / "zaragoza.json"
CARPETA_PROYECTO_WEB = RAIZ_WEB / "proyectos" / "real-zaragoza"
CARPETA_GRAFICOS = CARPETA_PROYECTO_WEB / "graficos"


def a_registros(df, columnas):
    """Pasa una tabla a lista de diccionarios para el JSON (NaN → null, fechas → texto)."""
    t = df[columnas].copy()
    for c in t.columns:
        if pd.api.types.is_datetime64_any_dtype(t[c]):
            t[c] = t[c].dt.strftime("%Y-%m-%d")
    t = t.astype(object).where(pd.notna(t), None)
    return t.to_dict(orient="records")


def guardar_csv(df, nombre):
    # utf-8-sig para que Excel abra bien las tildes
    df.to_csv(CARPETA_SALIDA / nombre, index=False, encoding="utf-8-sig")


def main():
    # 1. Datos de partida
    datos = cargar_todo()

    # 2. Preparación y comprobaciones
    partidos = calculos.preparar_partidos(datos["partidos"])
    goles = calculos.preparar_goles(datos["goles"], datos["cambios"], partidos)
    try:
        comprobaciones.comprobar_todo(datos, partidos, goles)
    except comprobaciones.DatosIncoherentes as error:
        print(f"ERROR: {error}")
        print("No se ha actualizado nada. Revisa los CSV de datos/entrada.")
        sys.exit(1)

    # 3. Cálculos (la liga por un lado y la copa por otro)
    liga = calculos.solo_liga(partidos)
    copa = partidos[partidos["competicion"] != LIGA]
    goles_liga = calculos.solo_liga(goles)

    ids_liga = set(liga["partido_id"])
    alineaciones_liga = datos["alineaciones"][datos["alineaciones"]["partido_id"].isin(ids_liga)]
    minutos = calculos.minutos_por_partido(alineaciones_liga, datos["cambios"])
    participacion = calculos.participacion_en_goles(goles_liga)
    jugadores = calculos.tabla_jugadores(minutos, goles_liga)
    clasificacion = calculos.preparar_clasificacion(datos["clasificacion"])
    sede = calculos.resumen_por_sede(liga)

    liga["posicion_rival"] = liga["rival"].apply(lambda r: calculos.posicion_de(r, clasificacion))
    liga = liga.merge(datos["tiros"], on="partido_id", how="left")
    proximos = datos["proximos"].copy()
    proximos["posicion_rival"] = proximos["rival"].apply(lambda r: calculos.posicion_de(r, clasificacion))

    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    guardar_csv(liga, "partidos_liga.csv")
    guardar_csv(copa, "partidos_copa.csv")
    guardar_csv(goles, "goles.csv")
    guardar_csv(minutos, "minutos_partido.csv")
    guardar_csv(jugadores, "jugadores.csv")
    guardar_csv(participacion, "participacion_goles.csv")
    guardar_csv(sede, "resumen_sede.csv")
    guardar_csv(clasificacion, "clasificacion.csv")
    guardar_csv(proximos, "proximos.csv")

    # 4. Gráficos
    CARPETA_GRAFICOS.mkdir(parents=True, exist_ok=True)
    rivales_jugados = {e for e in clasificacion["equipo"]
                       if any(e in r or r in e for r in liga["rival"])}
    graficos.resumen(liga, goles_liga, participacion, CARPETA_GRAFICOS / "resumen.png")
    graficos.tiros(datos["tiros"], liga, datos["estadisticas"], CARPETA_GRAFICOS / "tiros.png")
    graficos.contexto(clasificacion, goles_liga, rivales_jugados, CARPETA_GRAFICOS / "contexto.png")
    graficos.equipos_y_minutos(clasificacion, jugadores, CARPETA_GRAFICOS / "equipos_minutos.png")

    # 5. Web: JSON del panel e informe completo
    panel = {
        "corte": liga["fecha"].max().strftime("%Y-%m-%d"),
        "jornada": int(liga["jornada"].max()),
        "clasificacion_tras": int(clasificacion["tras_jornada"].iloc[0]),
        "partidos": a_registros(liga, [
            "partido_id", "jornada", "fecha", "sede", "rival", "goles_favor", "goles_contra",
            "resultado", "puntos", "puntos_acumulados", "posicion_rival", "tiros_zaragoza",
            "tiros_rival", "posesion_pct", "completo"]),
        "goles": a_registros(goles_liga, [
            "partido_id", "rival", "sede", "sentido", "minuto_texto", "tramo", "jugador",
            "asistencia", "rol_goleador", "penalti", "propia_puerta"]),
        "jugadores": a_registros(jugadores, [
            "jugador", "partidos", "titularidades", "minutos", "goles", "asistencias"]),
        "clasificacion": a_registros(clasificacion, [
            "posicion", "equipo", "pj", "g", "e", "p", "gf", "gc", "puntos"]),
        "proximos": a_registros(proximos, [
            "jornada", "competicion", "fecha", "sede", "rival", "posicion_rival"]),
        "copa": a_registros(copa, [
            "partido_id", "competicion", "fecha", "sede", "rival", "goles_favor", "goles_contra", "resultado"]),
    }
    JSON_WEB.parent.mkdir(parents=True, exist_ok=True)
    JSON_WEB.write_text(json.dumps(panel, ensure_ascii=False, indent=1), encoding="utf-8")

    # Todas las URLs usadas, sin repetir y en el orden en que aparecen
    fuentes = []
    for tabla in ("partidos", "goles", "alineaciones", "cambios", "tarjetas", "tiros",
                  "estadisticas", "clasificacion", "proximos"):
        for url in datos[tabla]["fuente_url"].dropna():
            if url not in fuentes:
                fuentes.append(url)

    informe.generar(CARPETA_PROYECTO_WEB / "informe-completo.html", liga, goles_liga, jugadores,
                    clasificacion, sede, datos["incidencias"], fuentes)

    # Resumen por pantalla
    zgz = clasificacion[clasificacion["equipo"] == "Real Zaragoza"].iloc[0]
    print(f"Datos hasta la jornada {panel['jornada']} ({panel['corte']}).")
    print(f"Real Zaragoza: {zgz.posicion}.º con {zgz.puntos} puntos, "
          f"{liga['goles_favor'].sum()} goles a favor y {liga['goles_contra'].sum()} en contra.")
    print(f"Goles desde el banquillo: {(goles_liga['rol_goleador'] == 'Suplente').sum()} "
          f"de {(goles_liga['rol_goleador'] != '').sum()}.")
    print(f"Partidos de copa: {len(copa)}.")
    print("Comprobaciones superadas. Web actualizada.")


if __name__ == "__main__":
    main()
