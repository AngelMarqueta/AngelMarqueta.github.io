# -----------------------------------------------------------------------------
# Real Zaragoza 2026/27: comprobación en R
#
# Para qué sirve
#   Todo el análisis se calcula en Python (actualizar.py). Este script repite
#   los cálculos más importantes en R, partiendo de los mismos CSV de entrada,
#   y los compara con lo que Python ha guardado en datos/salida. Si los dos
#   lenguajes llegan a cifras distintas, algo está mal (en los datos o en uno
#   de los dos códigos) y el script para con un error que dice qué no cuadra.
#
# Qué compruebo (solo partidos de liga)
#   1. Puntos, goles y porterías a cero, en casa y fuera   -> R/sede.R
#   2. Minutos jugados por cada jugador                    -> R/minutos.R
#   3. Goles, asistencias y goles desde el banquillo       -> R/goles.R
#   Al final enseño un pequeño resumen                     -> R/resumen.R
#
# Cómo está organizado
#   comprobar.R        este archivo: busca la carpeta, carga las piezas y las
#                      ejecuta en orden
#   R/utilidades.R     leer CSV en UTF-8 y comparar una tabla de R con la de
#                      Python
#   R/datos.R          carga los CSV de entrada y de salida y se queda con la
#                      liga
#   R/sede.R, R/minutos.R, R/goles.R   una comprobación cada uno
#   R/resumen.R        lo que se imprime cuando todo cuadra
#
# Uso (desde la raíz del repositorio, después de actualizar.py):
#   Rscript analisis/real-zaragoza/codigo/comprobar.R
# También se puede abrir en RStudio y pulsar «Source».
#
# Solo usa R base: no hace falta instalar ningún paquete.
# -----------------------------------------------------------------------------


# --- 1. Dónde está el proyecto -----------------------------------------------
# Necesito la carpeta del proyecto (analisis/real-zaragoza) para encontrar los
# datos y las piezas de R/. La busco de tres maneras, de la más fiable a la
# menos:
#   a) con Rscript, R guarda la ruta del script en el argumento --file=;
#   b) con source() (el botón «Source» de RStudio), la ruta está en ofile;
#   c) si no, supongo que la carpeta de trabajo es la raíz del repositorio.
buscar_carpeta_codigo <- function() {
  argumentos <- commandArgs(trailingOnly = FALSE)
  con_file <- grep("^--file=", argumentos, value = TRUE)
  if (length(con_file) > 0) {
    return(dirname(normalizePath(sub("^--file=", "", con_file[1]))))
  }
  for (marco in rev(sys.frames())) {
    if (!is.null(marco$ofile)) return(dirname(normalizePath(marco$ofile)))
  }
  file.path(getwd(), "analisis", "real-zaragoza", "codigo")
}

carpeta_codigo <- buscar_carpeta_codigo()
proyecto <- normalizePath(file.path(carpeta_codigo, ".."))

if (!dir.exists(file.path(proyecto, "datos", "salida"))) {
  stop("No encuentro la carpeta datos/salida en ", proyecto, ". ",
       "Ejecuta el script desde la raíz del repositorio y después de actualizar.py.")
}


# --- 2. Cargo las piezas -------------------------------------------------------
# Cada archivo de R/ solo define funciones; aquí no se calcula nada todavía.
# No uso source(..., encoding = "UTF-8") porque, si el ordenador no tiene
# configurado UTF-8, R intenta convertir las tildes de los comentarios y se
# deja el archivo a medias. Leo el texto tal cual y lo ejecuto con eval().
cargar_pieza <- function(archivo) {
  texto <- readLines(file.path(carpeta_codigo, "R", archivo), encoding = "UTF-8", warn = FALSE)
  eval(parse(text = texto, keep.source = FALSE, encoding = "UTF-8"), envir = globalenv())
}

for (pieza in c("utilidades.R", "datos.R", "sede.R", "minutos.R", "goles.R", "resumen.R")) {
  cargar_pieza(pieza)
}


# --- 3. Ejecuto las comprobaciones en orden -----------------------------------
# Si una falla, stop() corta el script ahí y las siguientes no se ejecutan.
datos <- cargar_datos(proyecto)

partidos_r <- comprobar_sede(datos)
comprobar_minutos(datos)
goles_r <- comprobar_goles(datos)

imprimir_resumen(partidos_r, goles_r, datos)
