# -----------------------------------------------------------------------------
# Comprobación 1: puntos y resumen por sede (casa / fuera)
#
# Con el resultado de cada partido calculo los puntos (3 por victoria, 1 por
# empate, 0 por derrota) y si el Zaragoza dejó la portería a cero. Después
# sumo por sede y comparo con datos/salida/resumen_sede.csv.
#
# Devuelvo la tabla de partidos con los puntos, porque el resumen del final
# la usa.
# -----------------------------------------------------------------------------

comprobar_sede <- function(datos) {
  partidos <- datos$partidos

  # Puntos de cada partido
  partidos$puntos <- ifelse(partidos$goles_favor > partidos$goles_contra, 3,
                     ifelse(partidos$goles_favor == partidos$goles_contra, 1, 0))

  # Portería a cero: 1 si no encajó ningún gol, 0 si encajó alguno.
  # Uso el mismo nombre de columna que Python (porterias_cero) para poder
  # compararlas directamente.
  partidos$porterias_cero <- as.integer(partidos$goles_contra == 0)

  # Sumo por sede. aggregate() con la fórmula cbind(...) ~ sede suma cada
  # columna por separado para «Casa» y para «Fuera».
  sede <- aggregate(cbind(puntos, goles_favor, goles_contra, porterias_cero) ~ sede,
                    data = partidos, FUN = sum)

  # Número de partidos en cada sede
  sede$partidos <- as.integer(table(partidos$sede)[sede$sede])

  comparar(sede, datos$py_sede, clave = "sede",
           columnas = c("partidos", "puntos", "goles_favor", "goles_contra", "porterias_cero"),
           que = "Los puntos, goles o porterías a cero por sede no coinciden con Python")

  partidos
}
