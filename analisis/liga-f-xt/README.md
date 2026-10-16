# Liga F 2023/24: crear peligro antes del tiro

Investigación sobre quién acerca el balón a las zonas de gol con pases y conducciones, medido con un modelo propio de amenaza esperada (xT). El resultado se publica en [Línea de pase](https://lineadepase.github.io/proyectos/liga-f-xt/).

Es un análisis histórico: la temporada 2023/24 terminó en 2024 y no describe la forma actual de ninguna jugadora.

## La pregunta

Los goles y las asistencias solo cuentan la última acción. ¿Qué jugadoras mueven el balón hacia sitios desde los que se marca más, aunque no aparezcan en esas estadísticas?

## Cómo está organizado

```
liga-f-xt/
├── codigo/
│   ├── datos.py            descarga fijada a un commit de StatsBomb, filtros y minutos jugados
│   ├── modelo.py           ajuste del xT, valoración fuera de muestra y agregación por jugadora
│   ├── visualizaciones.py  gráficas y carrusel con el estilo de analisis/comun/estilo.py
│   └── ejecutar.py         ejecuta todo en orden y escribe el informe
├── cuadernos/analisis_xt.ipynb   el análisis paso a paso, ejecutado
├── datos/salida/           resultados agregados (no contiene eventos de StatsBomb)
├── documentacion/          informe, validación y manifiesto de descargas con su SHA-256
├── graficos/               PNG y SVG: Instagram 1080×1350, Facebook 1200×630, LinkedIn y web 1600×900
├── publicaciones/          carrusel de Instagram y textos para cada red
├── pruebas/                pruebas del modelo con soluciones conocidas
└── recursos/statsbomb.png  logotipo del proveedor, obligatorio en las gráficas publicadas
```

## Método, en corto

1. Selecciono las acciones de juego abierto de los 240 partidos: 168.296 pases, conducciones y tiros.
2. Divido el campo en 12 × 8 zonas. Para cada zona calculo la probabilidad de tirar y marcar desde ella y la de mover el balón a cada una de las demás. El valor de cada zona (xT) se obtiene resolviendo ese sistema por iteración.
3. Cada pase o conducción completados suman el valor del destino menos el del origen.
4. Para no valorar un partido con un modelo que ya lo ha visto, separo los partidos en cinco grupos y valoro cada grupo con un modelo ajustado en los otros cuatro.
5. Sumo por jugadora, divido por sus minutos (reconstruidos con alineaciones, cambios y expulsiones) y exijo 900 minutos. El intervalo de cada jugadora sale de 1.000 remuestras de sus partidos.

El detalle, las comprobaciones de sensibilidad y los límites están en [el informe](documentacion/informe.md).

## Cómo ejecutarlo

Desde esta carpeta:

```
pip install -r requirements.txt
python codigo/ejecutar.py --cache <carpeta privada para los datos>
python -m pytest pruebas
```

La primera ejecución descarga unos 600 MB de eventos y alineaciones. Esa carpeta no se sube al repositorio: el acuerdo de StatsBomb no permite redistribuir sus datos.

## Límites

- No es una nota de calidad: mide la progresión con balón, no la defensa ni los movimientos sin balón.
- No ajusta por el equipo, el rival ni el marcador. Ocho de las diez primeras juegan en el Barcelona.
- Los pases fallidos no restan en la medida principal; con penalización, la ordenación cambia bastante (correlación de rangos 0,46).
- Sin tracking: no se sabe dónde estaban las defensoras.

## Fuentes

- Datos: [StatsBomb Open Data](https://github.com/hudl/open-data), commit `4b73468`. Su [acuerdo de uso](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf) permite publicar análisis, prohíbe redistribuir los datos y su uso comercial, y pide el logotipo en lo publicado.
- Método: [Karun Singh, *Introducing Expected Threat*](https://karun.in/blog/expected-threat.html). Implementación propia.

## Imagen

La portada del carrusel y la cabecera de la página usan una foto de Caroline Graham Hansen con el FC Barcelona (Brann-Barcelona, marzo de 2024), de MichaelEmilio en [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Brann_-_Bar%C3%A7a_Femen%C3%AD_CG3A7081_(cropped).jpg), con licencia [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Está recortada y reducida. Por esa licencia, la portada del carrusel, que la incluye, se comparte también con CC BY-SA 4.0. Datos completos en `recursos/foto.json`.

Análisis personal. Sin relación con ningún club ni competición.
