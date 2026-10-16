# -----------------------------------------------------------------------------
# Resumen: lo que imprimo cuando todas las comprobaciones han pasado
#
# Estas cifras son solo informativas, para ver de un vistazo cómo va la
# temporada. La comprobación de verdad ya está hecha: si algo no cuadrara,
# el script se habría parado antes de llegar aquí.
# -----------------------------------------------------------------------------

imprimir_resumen <- function(partidos, goles, datos) {
  cat("Comprobación en R correcta.\n")

  cat(sprintf("Partidos de liga: %d · Puntos: %d · Goles: %d-%d\n",
              nrow(partidos), sum(partidos$puntos),
              sum(partidos$goles_favor), sum(partidos$goles_contra)))

  # Sobre los goles con goleador del Zaragoza (sin propia puerta)
  cat(sprintf("Goles desde el banquillo: %d de %d\n",
              goles$desde_banquillo, nrow(goles$a_favor)))

  # Sobre todos los goles a favor (con propia puerta)
  a_favor <- goles$todos$sentido == "Favor"
  cat(sprintf("Goles a favor en la segunda parte: %d de %d\n",
              sum(a_favor & goles$todos$parte == 2), sum(a_favor)))

  cat("\nMáximos goleadores:\n")
  print(sort(goles$goleadores, decreasing = TRUE))

  cat("\nAsistencias registradas:\n")
  print(sort(goles$asistentes, decreasing = TRUE))
}
