# -----------------------------------------------------------------------------
# Utilidades: leer CSV y comparar tablas de R con las de Python
#
# Las uso en todas las comprobaciones, así que las tengo aparte.
# -----------------------------------------------------------------------------


# Leer un CSV en UTF-8 -----------------------------------------------------------
# Los CSV de datos/salida empiezan con un BOM (tres bytes invisibles que
# Python añade para que Excel muestre bien las tildes). R no lo quita solo:
# si no lo borro, la primera columna se llama «ï..sede» en vez de «sede» y
# fallan los cruces. Además leo siempre en UTF-8 para que las tildes y la ñ
# de los nombres (Jaume Jardí, Óscar Ureña…) salgan bien también en Windows.
BOM <- rawToChar(as.raw(c(0xef, 0xbb, 0xbf)))

leer <- function(proyecto, carpeta, archivo) {
  ruta <- file.path(proyecto, "datos", carpeta, archivo)
  if (!file.exists(ruta)) stop("Falta el archivo ", ruta)

  lineas <- readLines(ruta, encoding = "UTF-8", warn = FALSE)
  lineas[1] <- sub(BOM, "", lineas[1], fixed = TRUE, useBytes = TRUE)
  Encoding(lineas) <- "UTF-8"
  read.csv(text = lineas, stringsAsFactors = FALSE, encoding = "UTF-8")
}


# Comparar una tabla calculada en R con la de Python -----------------------------
# tabla_r y tabla_py tienen que compartir la columna «clave» (por ejemplo, el
# jugador o la sede) y las columnas que quiero comparar, con el mismo nombre.
#
# Uno las dos tablas con merge(all = TRUE), es decir, sin perder filas de
# ninguna de las dos. Así detecto dos tipos de error:
#   - una fila que está en una tabla y no en la otra (por ejemplo, un jugador
#     que en R tiene minutos y en Python no aparece): queda con NA;
#   - una fila que está en las dos pero con números distintos.
# Si hay alguna, imprimo las filas que no cuadran y paro el script con
# el mensaje «que».
comparar <- function(tabla_r, tabla_py, clave, columnas, que) {
  juntas <- merge(tabla_r[, c(clave, columnas)], tabla_py[, c(clave, columnas)],
                  by = clave, suffixes = c("_r", "_py"), all = TRUE)

  mal <- rep(FALSE, nrow(juntas))
  for (columna in columnas) {
    en_r  <- juntas[[paste0(columna, "_r")]]
    en_py <- juntas[[paste0(columna, "_py")]]
    # Falta en un lado, o está en los dos pero no vale lo mismo
    mal <- mal | is.na(en_r) | is.na(en_py) | (!is.na(en_r) & !is.na(en_py) & en_r != en_py)
  }

  if (any(mal)) {
    cat("\nNo coinciden R (_r) y Python (_py) en estas filas:\n")
    print(juntas[mal, ], row.names = FALSE)
    stop(que, call. = FALSE)
  }
  invisible(TRUE)
}
