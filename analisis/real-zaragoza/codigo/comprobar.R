# -----------------------------------------------------------------------------
# Real Zaragoza 2026/27: comprobación en R
#
# Repito los cálculos principales en R, partiendo de los mismos CSV de
# entrada, y los comparo con lo que ha guardado Python en datos/salida.
# Si algo no coincide, el script para con un error.
#
# Uso (desde la raíz del repositorio, después de actualizar.py):
#   Rscript analisis/real-zaragoza/codigo/comprobar.R
#
# Solo usa R base, no hace falta instalar paquetes.
# -----------------------------------------------------------------------------

# Carpeta del proyecto a partir de la ruta de este script
argumentos <- commandArgs(trailingOnly = FALSE)
ruta_script <- sub("^--file=", "", argumentos[grep("^--file=", argumentos)])
proyecto <- normalizePath(file.path(dirname(ruta_script), ".."))

# Leo siempre en UTF-8 y quito el BOM si lo hay (los CSV de salida lo llevan
# para que Excel muestre bien las tildes). Sin esto, en Windows o con otra
# configuración regional las tildes se rompen.
BOM <- rawToChar(as.raw(c(0xef, 0xbb, 0xbf)))

leer <- function(carpeta, archivo) {
  lineas <- readLines(file.path(proyecto, "datos", carpeta, archivo),
                      encoding = "UTF-8", warn = FALSE)
  lineas[1] <- sub(BOM, "", lineas[1], fixed = TRUE, useBytes = TRUE)
  Encoding(lineas) <- "UTF-8"
  read.csv(text = lineas, stringsAsFactors = FALSE, encoding = "UTF-8")
}

partidos     <- leer("entrada", "partidos.csv")
goles        <- leer("entrada", "goles.csv")
alineaciones <- leer("entrada", "alineaciones.csv")
cambios      <- leer("entrada", "cambios.csv")

py_sede      <- leer("salida", "resumen_sede.csv")
py_jugadores <- leer("salida", "jugadores.csv")
py_goles     <- leer("salida", "goles.csv")
py_particip  <- leer("salida", "participacion_goles.csv")

# Solo liga. Escribo la tilde como \u00f3 para que funcione aunque el
# sistema no esté configurado en UTF-8.
LIGA <- "Primera Federaci\u00f3n"
partidos <- partidos[partidos$competicion == LIGA, ]
goles <- goles[goles$partido_id %in% partidos$partido_id, ]

# --- Puntos y resumen por sede -------------------------------------------------
partidos$puntos <- ifelse(partidos$goles_favor > partidos$goles_contra, 3,
                   ifelse(partidos$goles_favor == partidos$goles_contra, 1, 0))
partidos$porteria_cero <- as.integer(partidos$goles_contra == 0)

sede <- aggregate(cbind(puntos, goles_favor, goles_contra, porteria_cero) ~ sede,
                  data = partidos, FUN = sum)
sede$partidos <- as.integer(table(partidos$sede)[sede$sede])

comparado <- merge(sede, py_sede, by = "sede", suffixes = c("_r", "_py"))
stopifnot(
  "Los puntos por sede no coinciden con Python" = all(comparado$puntos_r == comparado$puntos_py),
  "Los goles a favor por sede no coinciden"     = all(comparado$goles_favor_r == comparado$goles_favor_py),
  "Los goles en contra por sede no coinciden"   = all(comparado$goles_contra_r == comparado$goles_contra_py),
  "Las porterías a cero no coinciden"           = all(comparado$porteria_cero == comparado$porterias_cero)
)

# --- Minutos de cada jugador ---------------------------------------------------
# Titular: del 0 al minuto en que sale (90 si no sale).
# Suplente: del minuto en que entra al 90.
filas <- list()
for (id in unique(alineaciones$partido_id)) {
  once <- alineaciones$jugador[alineaciones$partido_id == id]
  cp <- cambios[cambios$partido_id == id, ]
  sale <- ifelse(once %in% cp$sale, cp$minuto[match(once, cp$sale)], 90)
  filas[[length(filas) + 1]] <- data.frame(jugador = once, minutos = sale)
  filas[[length(filas) + 1]] <- data.frame(jugador = cp$entra, minutos = 90 - cp$minuto)
}
minutos <- aggregate(minutos ~ jugador, data = do.call(rbind, filas), FUN = sum)

comparado <- merge(minutos, py_jugadores[, c("jugador", "minutos")], by = "jugador",
                   suffixes = c("_r", "_py"), all = TRUE)
stopifnot("Los minutos por jugador no coinciden con Python" =
            all(comparado$minutos_r == comparado$minutos_py))

# --- Goles y asistencias -------------------------------------------------------
propia <- tolower(goles$propia_puerta) == "si"
a_favor <- goles[goles$sentido == "Favor" & !propia, ]
goleadores <- table(a_favor$jugador)
asistentes <- table(goles$asistencia[!is.na(goles$asistencia) & goles$asistencia != ""])

r_particip <- data.frame(jugador = union(names(goleadores), names(asistentes)))
r_particip$goles <- as.integer(ifelse(r_particip$jugador %in% names(goleadores),
                                      goleadores[r_particip$jugador], 0))
r_particip$asistencias <- as.integer(ifelse(r_particip$jugador %in% names(asistentes),
                                            asistentes[r_particip$jugador], 0))
comparado <- merge(r_particip, py_particip, by = "jugador", suffixes = c("_r", "_py"), all = TRUE)
stopifnot("Goles o asistencias por jugador no coinciden con Python" =
            all(comparado$goles_r == comparado$goles_py) &&
            all(comparado$asistencias_r == comparado$asistencias_py))

# Goles desde el banquillo: el goleador entra en un cambio antes del gol
desde_banquillo <- 0
for (i in seq_len(nrow(a_favor))) {
  g <- a_favor[i, ]
  entra <- cambios$minuto[cambios$partido_id == g$partido_id & cambios$entra == g$jugador]
  if (length(entra) && entra[1] <= g$minuto) desde_banquillo <- desde_banquillo + 1
}
stopifnot("Los goles desde el banquillo no coinciden con Python" =
            desde_banquillo == sum(py_goles$rol_goleador == "Suplente", na.rm = TRUE))

# --- Resumen ---------------------------------------------------------------
cat("Comprobación en R correcta.\n")
cat(sprintf("Partidos de liga: %d · Puntos: %d · Goles: %d-%d\n",
            nrow(partidos), sum(partidos$puntos),
            sum(partidos$goles_favor), sum(partidos$goles_contra)))
cat(sprintf("Goles desde el banquillo: %d de %d\n", desde_banquillo, nrow(a_favor)))
cat(sprintf("Goles a favor en la segunda parte: %d de %d\n",
            sum(goles$sentido == "Favor" & goles$parte == 2), sum(goles$sentido == "Favor")))
cat("\nMáximos goleadores:\n")
print(sort(goleadores, decreasing = TRUE))
cat("\nAsistencias registradas:\n")
print(sort(asistentes, decreasing = TRUE))
