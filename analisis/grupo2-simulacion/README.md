# Simulación del grupo 2 de Primera Federación 2026/27

Simulación Monte Carlo del resto de la temporada del grupo 2: probabilidad de que cada equipo ascienda directamente, juegue el playoff o descienda. El resultado se publica en la sección del Real Zaragoza de [Línea de pase](https://lineadepase.github.io/proyectos/real-zaragoza/simulacion.html).

## La pregunta

Con lo jugado hasta ahora, ¿qué opciones reales tiene el Real Zaragoza de subir, y cuánto pesan todavía las jornadas que quedan?

## Cómo está organizado

```
grupo2-simulacion/
├── codigo/
│   ├── datos.py            resultados, comprobación contra la clasificación publicada y partidos pendientes
│   ├── modelo.py           modelo de Poisson con ataque, defensa y ventaja local, penalizado
│   ├── simulacion.py       10.000 temporadas y desempates según el reglamento
│   ├── visualizaciones.py  gráficas y carrusel con la paleta azul y blanca del Zaragoza
│   ├── ejecutar.py         ejecuta todo en orden
│   └── web.py              página en proyectos/real-zaragoza/simulacion.html
├── cuadernos/simulacion_grupo2.ipynb   el análisis paso a paso, ejecutado
├── datos/salida/           probabilidades, puestos, fuerzas de los equipos y evolución del Zaragoza
├── documentacion/          validación
├── graficos/               PNG y SVG para Instagram, Facebook, LinkedIn y web
├── publicaciones/          carrusel de Instagram y textos para cada red
└── pruebas/                pruebas con ligas inventadas
```

## Datos

Solo usa resultados: quién jugó contra quién, en qué campo y con qué marcador. Los lee de `analisis/real-zaragoza/datos/entrada/grupo2_partidos.csv`, el archivo que ya mantiene el seguimiento, y no utiliza ninguna otra columna. Antes de simular, comprueba que esos resultados reproducen exactamente la clasificación publicada tras la última jornada (`clasificacion.csv`); si no cuadra, se detiene.

## Método

1. **Modelo de goles.** Los goles de cada equipo siguen una Poisson con media `exp(base + casa + ataque propio + defensa rival)` (Maher, 1982).
2. **Penalización.** Con pocas jornadas las fuerzas se acercan a la media del grupo. La fuerza de esa penalización se elige con validación cruzada dejando fuera una jornada cada vez.
3. **Incertidumbre.** En cada simulación se sacan unas fuerzas de la distribución aproximada del modelo, no solo su valor estimado.
4. **Desempates.** Reglamento de Primera Federación (art. 12): puntos; entre empatados, puntos (si son tres o más) y diferencia particular; diferencia general; goles a favor. El juego limpio y el desempate en campo neutral se sortean.
5. **Zonas.** 1.º asciende; 2.º a 5.º, playoff; 16.º a 20.º, descenso (art. 9).

## Cómo ejecutarlo

Desde la raíz del repositorio, después de actualizar los resultados de la jornada:

```
pip install -r analisis/grupo2-simulacion/requirements.txt
python analisis/grupo2-simulacion/codigo/ejecutar.py
python analisis/grupo2-simulacion/codigo/web.py
python -m pytest analisis/grupo2-simulacion/pruebas
```

Tarda menos de un minuto.

## Límites

- No sabe de lesiones, fichajes, sanciones ni cambios de entrenador.
- Supone goles independientes entre los dos equipos: suele dar algo menos de empates de los reales.
- Con pocas jornadas, la validación cruzada muestra que los resultados predicen poco más que un modelo en el que todos los equipos son iguales; por eso la penalización es fuerte y las probabilidades, prudentes.

## Fuentes

- Resultados de Primera Federación 2026/27, grupo 2, tomados de Sofascore y contrastados con la clasificación de BeSoccer.
- [Normas de competición de Primera Federación 2026/27](https://rfef.es/sites/default/files/2026-06/2._CNL_Primera_Federacion_FINAL.pdf), RFEF.
- M. J. Maher (1982), *Modelling association football scores*, Statistica Neerlandica 36(3). M. J. Dixon y S. G. Coles (1997), *Modelling association football scores and inefficiencies in the football betting market*, Applied Statistics 46(2).

## Imagen

La portada del carrusel y la cabecera de la página usan una foto del Real Zaragoza-SD Huesca de la temporada 2024/25 en La Romareda, de WikiUsuario46 en [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Partido_Real_Zaragoza-SD_Huesca,_temporada_24-25_en_la_Romareda.jpg), en dominio público (CC0). Datos completos en `recursos/foto.json`.

Análisis personal. Sin relación con el Real Zaragoza ni con ninguna competición.
