# Panel en Tableau Public

Guía para montar el panel del Zaragoza en Tableau Public con las tablas que genera `actualizar.py`. Tableau Public es gratuito, pero hay que crear una cuenta y publicar desde Tableau Public Desktop.

## Archivos

Todos están en `datos/salida/` (UTF-8):

| Archivo | Una fila por… |
|---|---|
| `partidos_liga.csv` | partido de liga |
| `goles.csv` | gol (a favor y en contra) |
| `minutos_partido.csv` | jugador y partido |
| `jugadores.csv` | jugador (totales) |
| `clasificacion.csv` | equipo |

## Conexión

1. Abrir Tableau Public Desktop → *Archivo de texto* → `partidos_liga.csv`.
2. Arrastrar `goles.csv` y relacionarlo por `partido_id`.
3. Arrastrar `minutos_partido.csv` y relacionarlo también por `partido_id`.
4. `jugadores.csv` y `clasificacion.csv` van como fuentes de datos aparte (no se relacionan).

## Campos calculados

- **Puntos por partido:** `SUM([Puntos]) / COUNTD([Partido Id])`
- **Diferencia de goles:** `SUM([Goles Favor]) - SUM([Goles Contra])`
- **Gol desde el banquillo:** `[Rol Goleador] = "Suplente"`
- **Cuota de tiros:** `SUM([Tiros Zaragoza]) / (SUM([Tiros Zaragoza]) + SUM([Tiros Rival]))` (formato porcentaje)

## Hojas

1. **Puntos acumulados:** `Jornada` en columnas, `Puntos Acumulados` en filas, línea.
2. **Marcadores:** `Jornada` en columnas, `Goles Favor` y `Goles Contra` en barras dobles.
3. **Goles por tramo:** `Tramo` en columnas, recuento de goles, color por `Sentido`.
4. **Minutos:** `jugadores.csv`, `Jugador` en filas, `Minutos` en barras, ordenado de mayor a menor.
5. **Clasificación:** tabla con `Posicion`, `Equipo`, `Puntos`; resaltar al Real Zaragoza.

## Panel

- Filtro de `Sede` (Casa / Fuera) aplicado a las hojas 1 a 3.
- Mismos colores que la web: verde `#2f6b45` (a favor) y naranja `#d9480f` (en contra).
- Título: «Real Zaragoza 2026/27 · Segundo palo». Fuente al pie: «Datos públicos: web del club, FotMob, futboltotal y BeSoccer».

## Publicar

*Archivo → Guardar en Tableau Public*. Después, en el perfil de Tableau Public, copiar el enlace y añadirlo a la web.

Cada semana, después de ejecutar `actualizar.py`, basta con abrir el libro, *Datos → Actualizar* y volver a guardarlo en Tableau Public.
