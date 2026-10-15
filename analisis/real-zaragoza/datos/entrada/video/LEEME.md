# Goles apuntados viendo los resúmenes

Cada fila de `goles_video.csv` es un gol de liga del Real Zaragoza (a favor o en contra). Lo apunto viendo el resumen de la RFEF en YouTube, fotograma a fotograma en la jugada del gol. Los vídeos están en `resumenes_youtube.csv`.

| Columna | Qué es |
|---|---|
| `gol_id` | Jornada y número de gol del partido (6-02 = segundo gol de la J6) |
| `sentido` | `Favor` o `Contra` |
| `marcador` | Resultado después del gol, siempre Zaragoza-rival |
| `inicio` | `ataque_posicional`, `transicion`, `balon_parado`, `penalti` o `sin_dato` |
| `carril` | `izquierda`, `centro` o `derecha` **del equipo que ataca** |
| `ultimo_pase` | `centro_lateral`, `pase_atras`, `pase_interior`, `pase_al_espacio`, `rechace`, `corner`, `falta_lateral`, `falta_directa`, `sin_pase` |
| `zona_remate` | `area_pequena`, `area_central`, `area_lateral`, `fuera_area`, `penalti` |
| `remate` | `pie`, `cabeza`, `propia_puerta` |
| `revision_fvs` | Si se ve revisión en el monitor (`si`, `chequeo_cuarto_arbitro`, `no_se_ve`) |
| `defensores_area`, `atacantes_area` | Jugadores dentro del área en el momento del último pase, solo cuando se ven todos |
| `tiro_x`, `tiro_y`, `pase_x`, `pase_y` | Posición estimada en metros (campo de 105 x 68). La x va hacia la portería rival y la y desde la banda derecha (0) a la izquierda (68) del que ataca |
| `segundos_video` | Dónde está la jugada en el resumen |
| `confianza` | `alta`, `media` o `baja` |

Lo que no se ve en el vídeo queda como `sin_dato` o vacío. No relleno nada por suponer.
