# -----------------------------------------------------------------------------
# Datos: cargo lo que necesito de datos/entrada y de datos/salida
#
# - De datos/entrada saco los datos «en bruto», los que relleno a mano, para
#   calcularlo todo otra vez desde cero en R.
# - De datos/salida saco lo que ha calculado Python, para compararlo.
#
# Todo se queda en una lista («datos») que paso a cada comprobación.
# -----------------------------------------------------------------------------

# Solo comparo la liga: la copa no suma puntos y Python la guarda aparte.
# Escribo la ó como ó para que la comparación funcione aunque el
# ordenador no tenga configurado UTF-8 (pasa a veces en Windows).
LIGA <- "Primera Federación"

cargar_datos <- function(proyecto) {
  # Entrada: lo que apunto después de cada partido
  partidos     <- leer(proyecto, "entrada", "partidos.csv")
  goles        <- leer(proyecto, "entrada", "goles.csv")
  alineaciones <- leer(proyecto, "entrada", "alineaciones.csv")
  cambios      <- leer(proyecto, "entrada", "cambios.csv")

  # Me quedo con los partidos de liga y, con su partido_id, filtro el resto
  # de tablas. Es importante filtrar también alineaciones y cambios: si no,
  # en cuanto apunte un partido de copa sus minutos se sumarían aquí y no
  # en Python, y la comprobación fallaría sin que haya ningún error real.
  partidos <- partidos[partidos$competicion == LIGA, ]
  ids_liga <- partidos$partido_id

  # Salida: lo que ha calculado Python. goles.csv de salida lleva todos los
  # goles (liga y copa), así que también lo filtro por competición.
  py_goles <- leer(proyecto, "salida", "goles.csv")

  list(
    partidos     = partidos,
    goles        = goles[goles$partido_id %in% ids_liga, ],
    alineaciones = alineaciones[alineaciones$partido_id %in% ids_liga, ],
    cambios      = cambios[cambios$partido_id %in% ids_liga, ],

    py_sede      = leer(proyecto, "salida", "resumen_sede.csv"),
    py_jugadores = leer(proyecto, "salida", "jugadores.csv"),
    py_particip  = leer(proyecto, "salida", "participacion_goles.csv"),
    py_goles     = py_goles[py_goles$competicion == LIGA, ]
  )
}
