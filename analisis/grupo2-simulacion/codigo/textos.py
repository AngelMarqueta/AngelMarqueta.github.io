"""
Textos de las publicaciones de la simulación.

Como las probabilidades cambian cada jornada, los textos se escriben a partir
de los resultados en lugar de redactarse a mano. Uso, después de ejecutar.py:
    python analisis/grupo2-simulacion/codigo/textos.py
"""
import json
from pathlib import Path

import pandas as pd

ESTUDIO = Path(__file__).resolve().parents[1]
ENLACE = "https://lineadepase.github.io/proyectos/real-zaragoza/simulacion.html"


def pct(valor):
    return f"{valor * 100:.0f} %"


def main():
    salida = ESTUDIO / "datos" / "salida"
    tabla = pd.read_csv(salida / "probabilidades.csv")
    evolucion = pd.read_csv(salida / "evolucion_zaragoza.csv")
    validacion = json.loads((ESTUDIO / "documentacion" / "validacion.json").read_text(encoding="utf-8"))
    j = validacion["tras_jornada"]
    z = tabla[tabla.equipo == "Real Zaragoza"].iloc[0]
    rivales = tabla[tabla.equipo != "Real Zaragoza"].sort_values("ascenso_o_playoff", ascending=False).head(2)
    inicio = evolucion.iloc[0]
    favorito = z.ascenso_o_playoff >= tabla.ascenso_o_playoff.max()
    lectura = "Es el equipo con más opciones, pero lejos de tenerlo hecho" if favorito else "No es el que más opciones tiene"
    lectura_fb = "Es el equipo con más opciones del grupo, pero" if favorito else "Aun así,"
    if validacion["penalizacion"] >= 16:
        leccion = (f"Con {j} jornadas, la mejor opción es una penalización fuerte: el modelo con fuerzas de equipo "
                   "apenas predice mejor que uno en el que todos son iguales.")
    else:
        leccion = f"Con {j} jornadas, los resultados ya separan a los equipos: la penalización elegida es {validacion['penalizacion']}."
    carpeta = ESTUDIO / "publicaciones"
    carpeta.mkdir(parents=True, exist_ok=True)

    (carpeta / "instagram.txt").write_text(f"""¿Y si el grupo 2 se jugara 10.000 veces?

Línea de pase ha simulado el resto de la temporada de Primera Federación con un modelo de goles ajustado a los resultados de las {j} primeras jornadas.

El Real Zaragoza acaba primero en el {pct(z.ascenso_directo)} de las simulaciones y entre los cinco primeros en el {pct(z.ascenso_o_playoff)}. {lectura}: le siguen {rivales.iloc[0].equipo} ({pct(rivales.iloc[0].ascenso_o_playoff)}) y {rivales.iloc[1].equipo} ({pct(rivales.iloc[1].ascenso_o_playoff)}).

Tras la jornada {int(inicio.jornada)}, esa probabilidad era del {pct(inicio.ascenso_o_playoff)}.

Desliza para ver cada puesto posible, el grupo entero y cómo ha cambiado.

La simulación se actualiza después de cada jornada. Método y código: enlace en la bio.

#RealZaragoza #PrimeraFederacion #AnaliticaDeportiva #Python #LineaDePase
""", encoding="utf-8")

    (carpeta / "facebook.txt").write_text(f"""¿Qué opciones tiene de verdad el Real Zaragoza de subir?

Línea de pase ha simulado 10.000 veces lo que queda de temporada en el grupo 2 de Primera Federación, con un modelo de goles ajustado a los resultados de las {j} primeras jornadas.

· Primero (ascenso directo): {pct(z.ascenso_directo)}
· Del segundo al quinto (playoff): {pct(z.playoff)}
· Descenso: {pct(z.descenso)}

{lectura_fb} en el {pct(1 - z.ascenso_o_playoff)} de las temporadas simuladas se queda fuera de los cinco primeros. Quedan {38 - j} jornadas.

Todos los equipos, el método y el código:
{ENLACE}
""", encoding="utf-8")

    (carpeta / "linkedin.txt").write_text(f"""Con {j} jornadas jugadas, la clasificación dice menos de lo que parece. Línea de pase lo ha medido con una simulación Monte Carlo del grupo 2 de Primera Federación, programada en Python:

· Modelo de Poisson con ataque, defensa y ventaja local (Maher, 1982), ajustado solo con los resultados de los partidos.
· Penalización de las fuerzas hacia la media, elegida con validación cruzada dejando fuera una jornada cada vez. {leccion}
· 10.000 temporadas, con incertidumbre en los parámetros y desempates según el reglamento de la RFEF (puntos y diferencia particular entre empatados, diferencia general, goles a favor).
· Comprobación previa: los resultados tienen que reproducir la clasificación publicada, o el programa se detiene.

Tras la jornada {j}, el Real Zaragoza asciende directamente en el {pct(z.ascenso_directo)} de las simulaciones y acaba entre los cinco primeros en el {pct(z.ascenso_o_playoff)}.

La simulación se actualiza después de cada jornada:
{ENLACE}

#AnaliticaDeportiva #Python #MonteCarlo #Estadistica #RealZaragoza
""", encoding="utf-8")
    print("Textos escritos en", carpeta.relative_to(ESTUDIO.parents[1]))


if __name__ == "__main__":
    main()
