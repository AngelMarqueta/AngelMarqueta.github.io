# Real Zaragoza 2026/27: seguimiento con datos públicos

Código y datos del seguimiento del Real Zaragoza en Primera Federación (grupo 2). El resultado se publica en [Línea de pase](https://lineadepase.github.io/proyectos/real-zaragoza/).

## Cómo está organizado

```
real-zaragoza/
├── datos/
│   ├── entrada/   CSV que relleno a mano después de cada partido
│   └── salida/    tablas calculadas por el script (no se tocan a mano)
├── codigo/
│   ├── actualizar.py      script principal: ejecuta todo en orden
│   ├── cargar_datos.py    lectura de los CSV de entrada
│   ├── comprobaciones.py  cruces entre tablas para detectar errores
│   ├── calculos.py        puntos, tramos, minutos, participación en goles…
│   ├── graficos.py        gráficos del informe
│   ├── informe.py         página del informe completo
│   ├── previa.py          previa del próximo partido
│   ├── tarjeta_dato.py    imagen de «El dato de la jornada» para LinkedIn
│   └── comprobar.R        repite los cálculos en R y los compara
├── textos/
│   ├── conclusiones.html  conclusiones del informe, escritas a mano
│   └── dato_jornada.json  texto de la tarjeta de la semana
└── TABLEAU.md             cómo montar el panel en Tableau Public
```

El script escribe también en la web:

- `datos/zaragoza.json`: datos del panel interactivo.
- `proyectos/real-zaragoza/informe-completo.html` y la carpeta `graficos/`.

El marcador de la página del proyecto lee `datos/sofascore.json` (calendario mantenido a mano) y las fichas de `datos/zaragoza.json`. Muestra el último resultado revisado, con goles, tarjetas y estadísticas al pulsar, hasta el martes a las 8:00 si hay partido entre semana o hasta el miércoles a las 8:00 en caso contrario. Después muestra el siguiente encuentro. Los cambios de tarjeta siguen la hora de Madrid y se revisan mientras la página permanece abierta.

La hora programada nunca se usa para afirmar que el partido ha empezado o terminado. El seguimiento en directo se abre en Sofascore. El 12 de octubre de 2026 el módulo incrustado devolvió un error, por lo que no se activa hasta verificar un proveedor operativo. Las fichas revisadas siguen funcionando sin ese módulo. «Dónde verlo» muestra solo los canales incluidos en `tv`; un campo vacío se presenta como emisión pendiente de confirmar.

Las páginas y sus plantillas conservan el selector de tema, los gráficos ampliables, el índice del informe, los resultados táctiles y la firma **Ángel Marqueta Alonso**. Al actualizar otra jornada, se parte siempre de la versión actual del repositorio para no recuperar plantillas anteriores.

## Datos de entrada

| Archivo | Qué contiene |
|---|---|
| `partidos.csv` | Fecha, rival, sede, resultado final y al descanso de cada partido (liga y copa) |
| `goles.csv` | Cada gol: minuto, parte, goleador, asistencia, penalti y propia puerta |
| `alineaciones.csv` | Once inicial de cada partido |
| `cambios.csv` | Minuto, jugador que entra y jugador que sale |
| `tarjetas.csv` | Tarjetas del Zaragoza |
| `tiros.csv` | Tiros, tiros a puerta y posesión, con aviso si el dato está incompleto |
| `estadisticas.csv` | Estadísticas completas de los partidos que las tienen (incluso por partes) |
| `clasificacion.csv` | Clasificación del grupo tras cada jornada apuntada |
| `proximos.csv` | Próximos partidos |
| `partidos_rivales.csv` | Resultados del próximo rival, para la previa |
| `incidencias.csv` | Diferencias entre fuentes y qué dato me quedo |
| `sofascore.csv` | Estadísticas de cada partido en Sofascore, xG incluido (una fila por métrica) |
| `video/goles_video.csv` | Cada gol de liga apuntado viendo los resúmenes de YouTube: tipo de jugada, carril, último pase, zona de remate… |
| `video/resumenes_youtube.csv` | Los vídeos que he usado para cada jornada |
| `avanzadas_j4_provisional.csv` | xG y otras métricas de un solo partido, de una fuente poco fiable (no se usan) |

Fuentes, por este orden: web oficial del club, FotMob, futboltotal y BeSoccer. Cuando dos fuentes no coinciden lo apunto en `incidencias.csv`. Si un dato no aparece en ninguna fuente fiable, se queda vacío: nunca lo relleno con un cero.

## Cómo se actualiza

1. Añadir el partido nuevo a los CSV de `datos/entrada` (y la clasificación de esa jornada).
2. Ejecutar desde la raíz del repositorio:
   ```
   pip install -r analisis/real-zaragoza/requirements.txt
   python analisis/real-zaragoza/codigo/actualizar.py
   Rscript analisis/real-zaragoza/codigo/comprobar.R
   ```
3. Si alguna comprobación falla, el script para y no cambia nada de la web.
   Para los goles en vídeo y el xG, después de apuntar los goles de la jornada en `video/goles_video.csv` y sus estadísticas en `sofascore.csv`:
   ```
   python analisis/real-zaragoza/codigo/goles_video.py
   ```
4. Revisar `textos/conclusiones.html` y los textos de la página del proyecto.
5. Previa del siguiente partido: añadir los resultados del rival a `partidos_rivales.csv` y ejecutar `python analisis/real-zaragoza/codigo/previa.py <jornada>`.

Los partidos de copa van en los mismos archivos con su competición; no cuentan para los puntos ni para la clasificación.

## Límites

- Los minutos no cuentan el descuento: un titular que juega todo el partido suma 90.
- Las asistencias salen de una sola fuente y no están todas.
- No hay datos públicos fiables de eventos con coordenadas, tracking ni presión.
- Los datos de vídeo están apuntados a ojo a partir de resúmenes de pocos segundos. Las posiciones del mapa de remates son estimaciones con un error de varios metros y cada gol lleva su nivel de confianza.

Análisis personal. Sin relación con el Real Zaragoza ni con ninguna competición.
