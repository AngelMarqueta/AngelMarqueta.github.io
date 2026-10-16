# Por dónde pasaba el juego de España · Eurocopa femenina 2025

Redes de pases de la selección española en sus seis partidos de la Eurocopa femenina 2025: quién recibía más, qué parejas conectaban más y por quién pasaba el juego. El resultado se publica en [Línea de pase](https://lineadepase.github.io/proyectos/espana-eurocopa-redes/).

## La pregunta

¿Quién unía el juego de España y cómo cambió su forma de circular el balón de la fase de grupos a la final?

## Cómo está organizado

```
espana-eurocopa-redes/
├── codigo/
│   ├── datos.py            descarga fijada a un commit de StatsBomb y nombres de las jugadoras
│   ├── redes.py            pases de la red, grafo, centralidad y resumen de cada partido
│   ├── visualizaciones.py  gráficas y carrusel con el estilo de analisis/comun/estilo.py
│   ├── ejecutar.py         ejecuta todo en orden, comprueba los datos y escribe los resultados
│   └── web.py              página del estudio en proyectos/espana-eurocopa-redes/
├── cuadernos/redes_espana.ipynb   el análisis paso a paso, ejecutado
├── datos/salida/           partidos, jugadoras por partido, medias del torneo y conexiones
├── documentacion/          validación y manifiesto de descargas con su SHA-256
├── graficos/               PNG y SVG: Instagram 1080×1350, Facebook 1200×630, LinkedIn y web 1600×900
├── publicaciones/          carrusel de Instagram y textos para cada red
├── pruebas/                pruebas con partidos inventados de resultado conocido
└── recursos/statsbomb.png  logotipo del proveedor, obligatorio en las gráficas publicadas
```

## Método

1. En cada partido se toman los pases completados en juego de España (sin saques) hasta su primer cambio, para que las once jugadoras estén en el campo todo el tramo.
2. Cada jugadora es un nodo; cada pareja, una flecha con tantos pases como se dieron. La posición de cada jugadora es la media de los sitios donde dio y recibió pases.
3. Por jugadora calculo el grado ponderado (pases dados y recibidos), la intermediación (con distancia 1 / pases, para que más pases signifique más cerca) y el PageRank. Por partido, la centralización de Freeman: de 0 (juego repartido) a 1 (todo por una jugadora).

## Cómo ejecutarlo

Desde esta carpeta:

```
pip install -r requirements.txt
python codigo/ejecutar.py --cache <carpeta privada para los datos>
python codigo/web.py
python -m pytest pruebas
```

## Resultados principales

- Laia Aleixandri, María Méndez, Irene Paredes y Patri Guijarro son las jugadoras con más intermediación media: el juego se ordenaba desde atrás y desde la mediocentro.
- España completó entre 6,4 y 8 pases por minuto en la fase de grupos y entre 5,5 y 6,2 en las eliminatorias.
- La red más repartida fue la de cuartos ante Suiza (centralización 0,27).

## Límites

- Solo pases completados: no entran conducciones ni pérdidas.
- El corte en el primer cambio deja fuera el final de cada partido (entre 46 y 72 minutos analizados).
- La posición media mezcla las fases de ataque y de defensa.
- Seis partidos no bastan para sacar reglas generales.

## Fuentes

- Datos: [StatsBomb Open Data](https://github.com/hudl/open-data), commit `4b73468`, Eurocopa femenina 2025 (competición 53, temporada 315). Su [acuerdo de uso](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf) permite publicar análisis, prohíbe redistribuir los datos y su uso comercial, y pide el logotipo en lo publicado. Los eventos se guardan en una caché privada que no se sube.
- Centralización: L. C. Freeman (1978), *Centrality in social networks: conceptual clarification*, Social Networks 1(3).

## Imagen

La portada del carrusel y la cabecera de la página usan una foto de la selección española antes del España-Bélgica de clasificación para la Eurocopa 2025 (Riazor, julio de 2024), de Estevoaei en [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Partido_Espa%C3%B1a_-_B%C3%A9lxica_en_Riazor,_clasificatorio_Eurocopa_2025_10.jpg), con licencia [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Está recortada y reducida. No es una foto del torneo: no encontré fotos con licencia libre de sus partidos. Por esa licencia, la portada del carrusel se comparte también con CC BY-SA 4.0. Datos completos en `recursos/foto.json`.

Análisis personal. Sin relación con ninguna federación ni competición.
