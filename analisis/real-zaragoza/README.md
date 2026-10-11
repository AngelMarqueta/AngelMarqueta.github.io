# Real Zaragoza 2026/27: seguimiento con datos públicos

Código y datos del seguimiento del Real Zaragoza en Primera Federación (grupo 2). El resultado se publica en [Segundo palo](https://angelmarqueta.github.io/proyectos/real-zaragoza/).

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
│   └── comprobar.R        repite los cálculos en R y los compara
└── textos/
    └── conclusiones.html  conclusiones del informe, escritas a mano
```

El script escribe también en la web:

- `datos/zaragoza.json`: datos del panel interactivo.
- `proyectos/real-zaragoza/informe-completo.html` y la carpeta `graficos/`.

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
| `incidencias.csv` | Diferencias entre fuentes y qué dato me quedo |
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
4. Revisar `textos/conclusiones.html` y los textos de la página del proyecto.

Los partidos de copa van en los mismos archivos con su competición; no cuentan para los puntos ni para la clasificación.

## Límites

- Los minutos no cuentan el descuento: un titular que juega todo el partido suma 90.
- Las asistencias salen de una sola fuente y no están todas.
- No hay datos públicos fiables de eventos con coordenadas, tracking ni presión.

Análisis personal. Sin relación con el Real Zaragoza ni con ninguna competición.
