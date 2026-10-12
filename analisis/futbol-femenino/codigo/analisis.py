"""
Fútbol femenino en España: ¿dónde empezar un programa de iniciación?

Cruzo las licencias federadas de fútbol del CSD (2023 y 2025) con la
población femenina del INE a 1 de enero de 2025 y calculo, para cada
comunidad autónoma:

    - licencias femeninas por cada 1.000 mujeres,
    - porcentaje de mujeres sobre el total de licencias de fútbol,
    - crecimiento de las licencias femeninas entre 2023 y 2025.

Criterio de selección: comunidades por debajo de la media española en los
dos primeros indicadores y que ya estén creciendo. De esas, me quedo con
las dos que tienen más mujeres, porque es donde un programa llega a más gente.

Uso (desde la raíz del repositorio):
    python analisis/futbol-femenino/codigo/analisis.py
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon

# ---------------------------------------------------------------------------
# Rutas y parámetros
# ---------------------------------------------------------------------------

CARPETA = Path(__file__).resolve().parents[1]
ENTRADA = CARPETA / "datos" / "entrada"
SALIDA = CARPETA / "datos" / "salida"
MAPA_WEB = CARPETA.parents[1] / "proyectos" / "futbol-femenino" / "mapa.png"

# Ceuta y Melilla salen en el mapa, pero no compiten por las plazas del
# programa: son ciudades con muy poca población y su tasa se dispara.
CIUDADES = {"Ceuta", "Melilla"}
NO_TERRITORIAL = "Sin territorializar"
COMUNIDADES_ELEGIDAS = 2


# ---------------------------------------------------------------------------
# 1. Carga de datos
# ---------------------------------------------------------------------------

def cargar_datos():
    """Lee las licencias del CSD y la población del INE."""
    licencias = pd.read_csv(ENTRADA / "licencias_futbol_csd.csv")
    poblacion = pd.read_csv(ENTRADA / "poblacion_mujeres_ine_2025.csv")
    return licencias, poblacion


# ---------------------------------------------------------------------------
# 2. Comprobaciones
# ---------------------------------------------------------------------------

def comprobar(licencias, poblacion):
    """
    Los datos los he copiado de los PDF del CSD, así que compruebo que cada
    serie suma su total de España. Si algo falla, prefiero que el programa
    pare a sacar conclusiones con un número mal copiado.
    """
    for (anio, sexo), serie in licencias.groupby(["anio", "sexo"]):
        espana = serie.loc[serie["territorio"] == "España", "licencias"].iloc[0]
        resto = serie.loc[serie["territorio"] != "España", "licencias"].sum()
        if espana != resto:
            raise ValueError(f"Licencias {sexo} {anio}: las comunidades suman {resto} y España {espana}")

    espana = poblacion.loc[poblacion["territorio"] == "España", "mujeres_1_enero_2025"].iloc[0]
    resto = poblacion.loc[poblacion["territorio"] != "España", "mujeres_1_enero_2025"].sum()
    if espana != resto:
        raise ValueError(f"Población: las comunidades suman {resto} y España {espana}")


# ---------------------------------------------------------------------------
# 3. Indicadores
# ---------------------------------------------------------------------------

def calcular_indicadores(licencias, poblacion):
    """Una fila por territorio con los tres indicadores."""
    tabla = licencias.pivot_table(index="territorio", columns=["sexo", "anio"],
                                  values="licencias", aggfunc="sum")
    tabla.columns = [f"{sexo.lower()}_{anio}" for sexo, anio in tabla.columns]
    tabla = tabla.reset_index()

    # Las licencias «sin territorializar» (seis en 2025) cuentan para el total
    # de España, pero no se pueden asignar a ninguna comunidad.
    tabla = tabla[tabla["territorio"] != NO_TERRITORIAL]
    tabla = tabla.merge(poblacion[["territorio", "mujeres_1_enero_2025"]], on="territorio")

    tabla["total_2025"] = tabla["mujeres_2025"] + tabla["hombres_2025"]
    tabla["por_mil_mujeres"] = tabla["mujeres_2025"] / tabla["mujeres_1_enero_2025"] * 1000
    tabla["pct_femenino"] = tabla["mujeres_2025"] / tabla["total_2025"] * 100
    tabla["crecimiento_pct"] = (tabla["mujeres_2025"] / tabla["mujeres_2023"] - 1) * 100
    tabla["aumento_licencias"] = tabla["mujeres_2025"] - tabla["mujeres_2023"]

    return tabla.sort_values("por_mil_mujeres").reset_index(drop=True)


def seleccionar(indicadores):
    """Aplica el criterio de selección y devuelve candidatas y elegidas."""
    espana = indicadores[indicadores["territorio"] == "España"].iloc[0]
    comunidades = indicadores[~indicadores["territorio"].isin(CIUDADES | {"España"})].copy()

    comunidades["cumple"] = (
        (comunidades["por_mil_mujeres"] < espana["por_mil_mujeres"])
        & (comunidades["pct_femenino"] < espana["pct_femenino"])
        & (comunidades["crecimiento_pct"] > 0)
    )
    candidatas = comunidades[comunidades["cumple"]].sort_values("mujeres_1_enero_2025", ascending=False)
    elegidas = candidatas.head(COMUNIDADES_ELEGIDAS)
    return espana, comunidades, candidatas, elegidas


# ---------------------------------------------------------------------------
# 4. Mapa
# ---------------------------------------------------------------------------

# Códigos del GeoJSON y nombre que uso en las tablas
CODIGOS = {
    "01": "Andalucía", "02": "Aragón", "03": "Asturias", "04": "Illes Balears",
    "05": "Canarias", "06": "Cantabria", "07": "Castilla y León", "08": "Castilla-La Mancha",
    "09": "Cataluña", "10": "Comunitat Valenciana", "11": "Extremadura", "12": "Galicia",
    "13": "Comunidad de Madrid", "14": "Región de Murcia", "15": "Navarra", "16": "País Vasco",
    "17": "La Rioja", "18": "Ceuta", "19": "Melilla",
}

# Dónde va cada etiqueta (longitud, latitud) y con qué nombre. Las
# comunidades pequeñas llevan el nombre fuera y la cifra dentro.
ETIQUETAS = {
    "Galicia": (-7.9, 42.75, "Galicia"), "Asturias": (-5.95, 43.25, None),
    "Cantabria": (-4.0, 43.15, None), "País Vasco": (-2.6, 43.05, None),
    "Navarra": (-1.65, 42.62, None), "La Rioja": (-2.55, 42.3, None),
    "Castilla y León": (-4.75, 41.8, "Castilla y León"), "Aragón": (-0.75, 41.45, "Aragón"),
    "Cataluña": (1.55, 41.85, "Cataluña"), "Comunidad de Madrid": (-3.72, 40.45, "Madrid"),
    "Castilla-La Mancha": (-3.0, 39.4, "C.-La Mancha"), "Extremadura": (-6.15, 39.2, "Extremadura"),
    "Comunitat Valenciana": (2.2, 38.4, "C. Valenciana"), "Región de Murcia": (-1.45, 38.0, "Murcia"),
    "Andalucía": (-4.6, 37.45, "Andalucía"), "Illes Balears": (2.95, 39.2, None),
}
NOMBRES_FUERA = {
    "Asturias": (-5.95, 43.75), "Cantabria": (-4.0, 43.7), "País Vasco": (-2.45, 43.7),
    "Navarra": (-0.2, 43.1), "La Rioja": (-2.55, 41.95), "Illes Balears": (2.95, 39.75),
}


def _poligonos(geometria):
    partes = geometria["coordinates"] if geometria["type"] == "MultiPolygon" else [geometria["coordinates"]]
    return [np.array(p[0]) for p in partes]


def _coma(valor):
    return f"{valor:.2f}".replace(".", ",")


def dibujar_mapa(indicadores, elegidas, ruta):
    """Coropleta de licencias femeninas por cada 1.000 mujeres."""
    tasa = dict(zip(indicadores["territorio"], indicadores["por_mil_mujeres"]))
    geo = json.loads((ENTRADA / "comunidades.geojson").read_text(encoding="utf-8"))

    plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]
    paleta = plt.get_cmap("YlOrRd")
    escala = Normalize(2, 10)  # por encima de 10 (Ceuta y Melilla) todo va al color máximo

    fig = plt.figure(figsize=(10, 8), dpi=150)
    ax = fig.add_axes([0.03, 0.08, 0.80, 0.78])
    ax_canarias = fig.add_axes([0.63, 0.15, 0.17, 0.10])

    for f in geo["features"]:
        nombre = CODIGOS[f["properties"]["cod_ccaa"]]
        if nombre in CIUDADES:
            continue  # demasiado pequeñas para verse; van en una nota
        destino = ax_canarias if nombre == "Canarias" else ax
        color = paleta(escala(min(tasa[nombre], 10)))
        for p in _poligonos(f["geometry"]):
            destino.add_patch(Polygon(p, closed=True, fc=color, ec="white", lw=0.8))
            if nombre in set(elegidas["territorio"]):
                destino.add_patch(Polygon(p, closed=True, fill=False, ec="#8b2e16", lw=2.2, zorder=3))

    for nombre, (x, y, rotulo) in ETIQUETAS.items():
        valor = tasa[nombre]
        color_texto = "white" if valor >= 6.5 else "#1d2733"
        texto = f"{rotulo}\n{_coma(valor)}" if rotulo else _coma(valor)
        ax.text(x, y, texto, ha="center", va="center", fontsize=10.5, fontweight="bold",
                color=color_texto, linespacing=1.1, zorder=4)
    # La Comunidad Valenciana es estrecha: la etiqueta va en el mar, unida con una línea
    ax.plot([-0.45, 1.3], [39.3, 38.6], color="#1d2733", lw=0.9, zorder=4)

    for nombre, (x, y) in NOMBRES_FUERA.items():
        ax.text(x, y, nombre.replace("Illes Balears", "Baleares"), ha="center", fontsize=9,
                color="#1d2733", zorder=4)

    ax.set_xlim(-9.6, 4.6)
    ax.set_ylim(35.7, 44.2)
    ax.set_aspect(1 / np.cos(np.radians(40)))  # corrige la deformación por la latitud
    ax.axis("off")

    ax_canarias.set_xlim(-18.3, -13.3)
    ax_canarias.set_ylim(27.5, 29.5)
    ax_canarias.set_aspect(1 / np.cos(np.radians(28)))
    ax_canarias.set_xticks([])
    ax_canarias.set_yticks([])
    for borde in ax_canarias.spines.values():
        borde.set_color("#b0b8c0")
    ax_canarias.set_title(f"Canarias {_coma(tasa['Canarias'])}", fontsize=10, pad=3)

    fig.text(0.715, 0.11, f"Ceuta {_coma(tasa['Ceuta'])} · Melilla {_coma(tasa['Melilla'])}",
             ha="center", fontsize=9.5, color="#1d2733")

    ax.legend(handles=[Line2D([], [], color="#8b2e16", lw=2.5, label="Comunidades propuestas")],
              loc="upper right", frameon=False, fontsize=11, bbox_to_anchor=(1.02, 1.0))

    eje_color = fig.add_axes([0.86, 0.22, 0.022, 0.5])
    barra = fig.colorbar(plt.cm.ScalarMappable(norm=escala, cmap=paleta), cax=eje_color, extend="max")
    barra.ax.tick_params(labelsize=9)
    barra.set_label("Licencias femeninas por cada 1.000 mujeres", fontsize=9.5)

    fig.text(0.04, 0.95, "Licencias femeninas de fútbol por cada 1.000 mujeres",
             fontsize=19, fontweight="bold", color="#1f3a5a")
    fig.text(0.04, 0.915, "Comunidades autónomas, 2025", fontsize=12, color="#6b7783")
    fig.text(0.04, 0.03, "Fuente: CSD (Estadística de Deporte Federado 2025) e INE. "
             "Elaboración propia: Ángel Marqueta Alonso.", fontsize=8.5, color="#6b7783")

    fig.savefig(ruta, dpi=150, facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5. Programa principal
# ---------------------------------------------------------------------------

def main():
    licencias, poblacion = cargar_datos()
    comprobar(licencias, poblacion)

    indicadores = calcular_indicadores(licencias, poblacion)
    espana, comunidades, candidatas, elegidas = seleccionar(indicadores)

    SALIDA.mkdir(parents=True, exist_ok=True)
    indicadores.round(2).to_csv(SALIDA / "indicadores.csv", index=False, encoding="utf-8-sig")
    comunidades.round(2).to_csv(SALIDA / "criterio_seleccion.csv", index=False, encoding="utf-8-sig")
    dibujar_mapa(indicadores, elegidas, SALIDA / "mapa.png")
    dibujar_mapa(indicadores, elegidas, MAPA_WEB)  # el mismo mapa, para la web

    # Cifras que uso en el texto de la web
    pct_mujeres = elegidas["mujeres_1_enero_2025"].sum() / espana["mujeres_1_enero_2025"] * 100
    pct_licencias = elegidas["mujeres_2025"].sum() / espana["mujeres_2025"] * 100
    pct_aumento = elegidas["aumento_licencias"].sum() / espana["aumento_licencias"] * 100
    minimo = comunidades.loc[comunidades["por_mil_mujeres"].idxmin()]
    maximo = comunidades.loc[comunidades["por_mil_mujeres"].idxmax()]

    print(f"España 2025: {espana['mujeres_2025']:,.0f} licencias femeninas "
          f"({espana['crecimiento_pct']:+.1f} % desde 2023), {espana['pct_femenino']:.2f} % del total, "
          f"{espana['por_mil_mujeres']:.2f} por cada 1.000 mujeres")
    print(f"Rango entre comunidades: {minimo['territorio']} {minimo['por_mil_mujeres']:.2f} – "
          f"{maximo['territorio']} {maximo['por_mil_mujeres']:.2f} "
          f"(×{maximo['por_mil_mujeres'] / minimo['por_mil_mujeres']:.1f})")
    print(f"Cumplen el criterio: {len(candidatas)} de {len(comunidades)} comunidades: "
          + ", ".join(candidatas["territorio"]))
    print(f"Elegidas: {', '.join(elegidas['territorio'])} · {pct_mujeres:.1f} % de las mujeres, "
          f"{pct_licencias:.1f} % de las licencias femeninas y {pct_aumento:.1f} % del aumento 2023-2025")


if __name__ == "__main__":
    main()
