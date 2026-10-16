# -----------------------------------------------------------------------------
# Comprobación 3: goles, asistencias y goles desde el banquillo
#
# a) Goles y asistencias por jugador
#    - Goles: solo los del Zaragoza («Favor») que no son en propia puerta.
#      Un gol en propia puerta de un rival cuenta en el marcador, pero no se
#      lo apunto a ningún jugador del Zaragoza. Por eso puede haber menos
#      goleadores que goles.
#    - Asistencias: todas las que hay apuntadas. Solo salen de una fuente y
#      no están todas, así que es un mínimo, no un total exacto.
#    Comparo con datos/salida/participacion_goles.csv.
#
# b) Goles desde el banquillo
#    Un gol es «desde el banquillo» si el goleador aparece entrando en los
#    cambios de ese partido en un minuto anterior (o igual) al del gol.
#    Comparo cuántos hay con los goles que Python marca como «Suplente» en
#    la columna rol_goleador de datos/salida/goles.csv.
#
# Devuelvo los goles a favor y las tablas de goleadores y asistentes, que
# usa el resumen del final.
# -----------------------------------------------------------------------------

comprobar_goles <- function(datos) {
  goles <- datos$goles
  cambios <- datos$cambios

  # --- a) Goles y asistencias ------------------------------------------------
  # En la entrada, propia_puerta viene como «si» o «no»
  propia <- tolower(goles$propia_puerta) == "si"
  a_favor <- goles[goles$sentido == "Favor" & !propia, ]

  # table() cuenta cuántas veces aparece cada nombre
  goleadores <- table(a_favor$jugador)
  con_asistencia <- !is.na(goles$asistencia) & goles$asistencia != ""
  asistentes <- table(goles$asistencia[con_asistencia])

  # Una fila por jugador que haya marcado o asistido; 0 si no tiene de algo
  participacion <- data.frame(jugador = union(names(goleadores), names(asistentes)))
  participacion$goles <- as.integer(ifelse(participacion$jugador %in% names(goleadores),
                                           goleadores[participacion$jugador], 0))
  participacion$asistencias <- as.integer(ifelse(participacion$jugador %in% names(asistentes),
                                                 asistentes[participacion$jugador], 0))

  comparar(participacion, datos$py_particip, clave = "jugador",
           columnas = c("goles", "asistencias"),
           que = "Los goles o asistencias por jugador no coinciden con Python")

  # --- b) Goles desde el banquillo -------------------------------------------
  desde_banquillo <- 0
  for (i in seq_len(nrow(a_favor))) {
    gol <- a_favor[i, ]
    # Minuto en que el goleador entró en ese partido (vacío si era titular).
    # Si apareciera más de una vez, me quedo con la primera, igual que Python.
    entra <- cambios$minuto[cambios$partido_id == gol$partido_id &
                            cambios$entra == gol$jugador]
    if (length(entra) > 0 && entra[1] <= gol$minuto) {
      desde_banquillo <- desde_banquillo + 1
    }
  }

  en_python <- sum(datos$py_goles$rol_goleador == "Suplente", na.rm = TRUE)
  if (desde_banquillo != en_python) {
    stop(sprintf("Goles desde el banquillo: R cuenta %d y Python %d",
                 desde_banquillo, en_python), call. = FALSE)
  }

  list(a_favor = a_favor, todos = goles, goleadores = goleadores,
       asistentes = asistentes, desde_banquillo = desde_banquillo)
}
