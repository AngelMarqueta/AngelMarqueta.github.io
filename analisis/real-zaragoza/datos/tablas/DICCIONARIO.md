# Diccionario de datos · Real Zaragoza 2026/27

Qué es cada tabla del proyecto y qué significa cada columna. Este archivo lo genera `codigo/preparar_tablas.py`; no lo edites a mano.

## partidos

Un partido oficial por fila (liga y copa) con el resultado final y al descanso. Archivo: `datos/entrada/partidos.csv` (7 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Identificador del partido. En liga coincide con el número de jornada; en copa empieza en 101. | Número entero | 1 |
| `competicion` | Competición: «Primera Federación» o «Copa del Rey». | Texto | Primera Federación |
| `jornada` | Número de jornada de liga. Vacío en copa. | Número entero | 1 |
| `fecha` | Fecha del partido (año-mes-día). | Texto | 2026-08-30 |
| `sede` | «Casa» si el Zaragoza juega de local y «Fuera» si es visitante. | Texto | Fuera |
| `rival` | Nombre del rival. | Texto | Gimnàstic de Tarragona |
| `goles_favor` | Goles del Real Zaragoza. | Número entero | 0 |
| `goles_contra` | Goles del rival. | Número entero | 2 |
| `gf_descanso` | Goles del Zaragoza al descanso. | Número entero | 0 |
| `gc_descanso` | Goles del rival al descanso. | Número entero | 1 |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://www.fotmob.com/es/matches/real-zaragoza-vs-gimnas… |

## goles

Un gol por fila, a favor o en contra, con minuto, goleador y asistencia. Archivo: `datos/entrada/goles.csv` (26 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Partido al que pertenece el gol (ver tabla partidos). | Número entero | 1 |
| `sentido` | «Favor» si lo marca el Zaragoza y «Contra» si lo marca el rival. | Texto | Contra |
| `jugador` | Goleador. En los goles en propia puerta, el jugador que la mete. | Texto | Sinan Bakis |
| `minuto` | Minuto del gol sin el descuento (un gol en el 45+7 tiene 45 aquí). | Número entero | 2 |
| `anadido` | Minutos de descuento (el 7 del 45+7). 0 si no hay. | Número entero | 0 |
| `parte` | 1 = primera parte, 2 = segunda parte. | Número entero | 1 |
| `penalti` | «si» si el gol es de penalti. | Texto | no |
| `propia_puerta` | «si» si es en propia puerta. | Texto | no |
| `asistencia` | Jugador que da el último pase. Vacío si no consta: no significa que no la haya. | Texto | Jaume Jardí |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://www.fotmob.com/es/matches/real-zaragoza-vs-gimnas… |

## alineaciones

Once inicial del Zaragoza en cada partido: un titular por fila. Archivo: `datos/entrada/alineaciones.csv` (77 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Partido (ver tabla partidos). | Número entero | 1 |
| `jugador` | Titular, escrito como en la web del club. | Texto | Westerveld |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://www.realzaragoza.com/partidos/temporada-2026-2027… |

## cambios

Sustituciones del Zaragoza: quién entra, quién sale y en qué minuto. Archivo: `datos/entrada/cambios.csv` (35 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Partido (ver tabla partidos). | Número entero | 1 |
| `minuto` | Minuto del cambio. | Número entero | 55 |
| `entra` | Jugador que entra. | Texto | Iker Vadillo |
| `sale` | Jugador que sale. | Texto | Marcos Cuenca |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://www.realzaragoza.com/partidos/temporada-2026-2027… |

## tarjetas

Tarjetas que ven los jugadores del Zaragoza. Archivo: `datos/entrada/tarjetas.csv` (23 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Partido (ver tabla partidos). | Número entero | 1 |
| `jugador` | Jugador amonestado o expulsado. | Texto | Lucas Terrer |
| `tarjeta` | «Amarilla» o «Roja». | Texto | Amarilla |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://futboltotal.futbol/partido/gimnastic-vs-zaragoza-… |

## tiros

Tiros y posesión de cada partido, con una nota cuando el desglose no cuadra. Archivo: `datos/entrada/tiros.csv` (7 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Partido (ver tabla partidos). | Número entero | 1 |
| `tiros_zaragoza` | Tiros totales del Zaragoza. | Número entero | 33 |
| `tiros_rival` | Tiros totales del rival. | Número entero | 10 |
| `a_puerta_zaragoza` | Tiros a puerta del Zaragoza. | Número entero | 9 |
| `a_puerta_rival` | Tiros a puerta del rival. | Número entero | 4 |
| `posesion_pct` | Posesión del Zaragoza, en %. | Número entero | 75 |
| `completo` | «si» si a puerta + fuera + bloqueados suman el total; «no» si no cuadra. | Texto | no |
| `fuente` | Fuente que me quedo para ese partido. | Texto | Web del club |
| `nota` | Explicación de la comprobación de los tiros. | Texto | 9 a puerta y 16 fuera suman 25; no hay bloqueados publicados |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://www.realzaragoza.com/partidos/temporada-2026-2027… |

## estadisticas

Otras estadísticas de partido de fuentes públicas, en formato largo (una métrica por fila). Archivo: `datos/entrada/estadisticas.csv` (116 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Partido (ver tabla partidos). | Número entero | 2 |
| `periodo` | «Partido», «1.ª parte» o «2.ª parte». | Texto | Partido |
| `metrica` | Nombre de la métrica (posesión, córners, faltas…). | Texto | posesion_pct |
| `zaragoza` | Valor del Zaragoza. | Número entero | 67 |
| `valor_rival` | Valor del rival. | Número entero | 33 |
| `calidad` | «ok» si lo he podido contrastar; otro valor si hay dudas. | Texto | ok |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://www.besoccer.com/match/real-zaragoza/antequera/20… |

## sofascore

Estadísticas de Sofascore de cada partido, xG incluido, en formato largo (una métrica por fila). Archivo: `datos/entrada/sofascore.csv` (248 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Partido (ver tabla partidos). | Número entero | 1 |
| `evento_sofascore` | Identificador del partido en Sofascore. | Número entero | 16599367 |
| `metrica` | Métrica. Las que acaban en _ok son aciertos y las que acaban en _total, intentos. | Texto | posesion_pct |
| `zaragoza` | Valor del Zaragoza. | Número decimal | 73.0 |
| `valor_rival` | Valor del rival. | Número decimal | 27.0 |
| `fuente_url` | Dirección de la API de Sofascore de la que copié el dato. | Texto | https://www.sofascore.com/api/v1/event/16599367/statistics |

## clasificacion

Clasificación del grupo 2 después de cada jornada apuntada. Archivo: `datos/entrada/clasificacion.csv` (40 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `tras_jornada` | Jornada después de la cual se toma la clasificación. | Número entero | 6 |
| `posicion` | Puesto en la tabla. | Número entero | 1 |
| `equipo` | Equipo. | Texto | Real Zaragoza |
| `pj` | Partidos jugados. | Número entero | 6 |
| `g` | Partidos ganados. | Número entero | 5 |
| `e` | Partidos empatados. | Número entero | 0 |
| `p` | Partidos perdidos. | Número entero | 1 |
| `gf` | Goles a favor. | Número entero | 12 |
| `gc` | Goles en contra. | Número entero | 6 |
| `puntos` | Puntos. | Número entero | 15 |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://www.fotmob.com/es-419/teams/8394/overview |

## proximos

Próximos partidos del calendario. Archivo: `datos/entrada/proximos.csv` (4 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `jornada` | Jornada. | Número entero | 8 |
| `competicion` | Competición. | Texto | Primera Federación |
| `fecha` | Fecha prevista (puede cambiar). | Texto | 2026-10-18 |
| `sede` | «Casa» o «Fuera». | Texto | Fuera |
| `rival` | Rival. | Texto | Real Murcia |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://www.fotmob.com/es-419/teams/8394/overview |

## partidos_rivales

Resultados del próximo rival esta temporada, para la previa. Archivo: `datos/entrada/partidos_rivales.csv` (7 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `equipo` | Equipo del que son los resultados. | Texto | Real Murcia |
| `jornada` | Jornada. | Número entero | 1 |
| `fecha` | Fecha. | Texto | 2026-08-29 |
| `local` | Equipo local. | Texto | Hércules |
| `visitante` | Equipo visitante. | Texto | Real Murcia |
| `goles_local` | Goles del local. | Número entero | 1 |
| `goles_visitante` | Goles del visitante. | Número entero | 2 |
| `fuente_url` | Página de la que saqué el dato. | Texto | https://futbolme.com/resultados-directo/equipo/real-murci… |

## incidencias

Diferencias entre fuentes y qué dato me quedo. Es el registro de decisiones del proyecto. Archivo: `datos/entrada/incidencias.csv` (36 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `jornada` | Jornada afectada (0 si afecta a todo el proyecto). | Número entero | 0 |
| `campo` | Dato o tabla afectada. | Texto | Cobertura |
| `problema` | Qué no cuadra. | Texto | No hay datos públicos fiables de coordenadas, tracking, d… |
| `decision` | Qué he hecho con ello. | Texto | No se estiman ni se rellenan |

## goles_video

Cada gol de liga apuntado viendo los resúmenes en YouTube: cómo nace, por dónde llega y desde dónde se remata. Archivo: `datos/entrada/video/goles_video.csv` (26 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `gol_id` | Jornada y número de gol del partido (6-02 = segundo gol de la J6). | Texto | 1-01 |
| `partido_id` | Partido (ver tabla partidos). | Número entero | 1 |
| `jornada` | Jornada de liga. | Número entero | 1 |
| `rival` | Rival. | Texto | Gimnàstic de Tarragona |
| `sede` | «Casa» o «Fuera». | Texto | Fuera |
| `sentido` | «Favor» o «Contra». | Texto | Contra |
| `minuto` | Minuto en texto, con el descuento (45+7). | Texto | 2 |
| `marcador` | Resultado justo después del gol, siempre Zaragoza-rival. | Texto | 0-1 |
| `goleador` | Quién marca. | Texto | Sinan Bakis |
| `asistencia` | Quién da el último pase, si consta. | Texto | Jaume Jardí |
| `inicio` | Cómo empieza la jugada: ataque posicional, transición, balón parado, penalti o sin dato. | Texto | balon_parado |
| `detalle_inicio` | La misma idea en una frase corta. | Texto | falta lateral |
| `carril` | Izquierda, centro o derecha DEL EQUIPO QUE ATACA. | Texto | derecha |
| `ultimo_pase` | Tipo de último pase: centro lateral, pase atrás, pase raso por dentro, al espacio, rechace, córner, falta… | Texto | falta_lateral |
| `zona_remate` | Zona del último toque: área pequeña, área grande (centro o lateral), fuera del área o penalti. | Texto | area_pequena |
| `remate` | Con qué se remata: pie, cabeza o propia puerta. | Texto | sin_dato |
| `revision_fvs` | Si se ve una revisión en el monitor (FVS). | Texto | no_se_ve |
| `defensores_area` | Defensores dentro del área en el momento del último pase, solo si se ven todos. | Número entero | 7 |
| `atacantes_area` | Atacantes dentro del área en ese mismo momento. | Número entero | 5 |
| `tiro_x` | Posición estimada del remate, en metros hacia la portería rival (0 a 105). | Número entero | 99 |
| `tiro_y` | Posición estimada del remate, en metros desde la banda derecha del que ataca (0 a 68). | Número entero | 30 |
| `pase_x` | Posición estimada del último pase (x). | Número entero | 78 |
| `pase_y` | Posición estimada del último pase (y). | Número entero | 8 |
| `segundos_video` | Dónde está la jugada en el resumen, en segundos. | Texto | 17-26 |
| `confianza` | Alta, media o baja: lo bien que se ve la jugada. | Texto | media |
| `nota` | Lo que se ve en el vídeo, explicado en una o dos frases. | Texto | Falta desde la derecha del ataque del Nàstic. El balón ca… |

## resumenes_youtube

Vídeos de resumen que he usado para apuntar los goles. Archivo: `datos/entrada/video/resumenes_youtube.csv` (8 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Partido (ver tabla partidos). | Número entero | 1 |
| `jornada` | Jornada. | Número entero | 1 |
| `rival` | Rival. | Texto | Gimnàstic de Tarragona |
| `canal` | Canal de YouTube que publica el resumen. | Texto | Real Federación Española Fútbol |
| `titulo` | Título del vídeo. | Texto | Resumen #PrimeraFederación \| Gimnàstic 2-0 Real Zaragoza … |
| `duracion` | Duración (minutos:segundos). | Texto | 4:03 |
| `url` | Enlace al vídeo. | Texto | https://www.youtube.com/watch?v=psvkPAyTRhk |

## jugadores

Tabla calculada: minutos y participación en goles de cada jugador en liga. Archivo: `datos/salida/jugadores.csv` (25 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `jugador` | Jugador. | Texto | Jaume Jardí |
| `partidos` | Partidos jugados. | Número entero | 7 |
| `titularidades` | Partidos como titular. | Número entero | 6 |
| `minutos` | Minutos jugados, sin contar el descuento. | Número entero | 554 |
| `goles` | Goles. | Número entero | 4 |
| `asistencias` | Asistencias (solo las que constan). | Número entero | 4 |
| `participaciones_con_minutos` | Goles + asistencias. | Número entero | 8 |
| `participaciones_por_90` | Goles + asistencias por cada 90 minutos jugados. | Número decimal | 1.3 |
| `minutos_por_participacion` | Minutos que tarda de media en participar en un gol. Vacío si no ha participado en ninguno. | Número entero | 69 |

## minutos_partido

Tabla calculada: minutos de cada jugador en cada partido de liga. Archivo: `datos/salida/minutos_partido.csv` (112 filas).

| Columna | Qué es | Tipo | Ejemplo |
|---|---|---|---|
| `partido_id` | Partido (ver tabla partidos). | Número entero | 1 |
| `jugador` | Jugador. | Texto | Westerveld |
| `rol` | «Titular» o «Suplente». | Texto | Titular |
| `entra` | Minuto en el que entra (0 si es titular). | Número entero | 0 |
| `sale` | Minuto en el que sale (90 si acaba el partido). | Número entero | 90 |
| `minutos` | Minutos jugados. | Número entero | 90 |
