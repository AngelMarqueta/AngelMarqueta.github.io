"""
Tarjeta para LinkedIn de la serie «El dato de la jornada» (1080 × 1350 px).

El texto de cada semana está en textos/dato_jornada.json. Así, para la
siguiente jornada solo cambio ese archivo y vuelvo a ejecutar:
    python analisis/real-zaragoza/codigo/tarjeta_dato.py

La imagen se guarda en datos/salida/dato_jornada.png (no se publica en la web).
"""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from cargar_datos import CARPETA_SALIDA, CARPETA_TEXTOS, RAIZ_WEB

LOGO = RAIZ_WEB / "assets" / "logo.png"

# Colores de la web
PAPEL = "#f5f6f2"
TINTA = "#14261d"
TINTA_SUAVE = "#55635b"
VERDE = "#2f6b45"
NARANJA = "#d9480f"
LINEA = "#d9ddd4"


def dibujar(dato, ruta):
    """Dibuja la tarjeta. 'dato' es el diccionario de dato_jornada.json."""
    plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]
    fig = plt.figure(figsize=(7.2, 9), dpi=150)  # 7,2 × 150 = 1080 px de ancho
    fig.patch.set_facecolor(PAPEL)

    fig.text(0.08, 0.92, "EL DATO DE LA JORNADA", fontsize=13, color=NARANJA, fontweight="bold")
    fig.text(0.08, 0.885, dato["contexto"], fontsize=12, color=TINTA_SUAVE)

    fig.text(0.08, 0.60, dato["cifra"], fontsize=96, fontweight="bold", color=VERDE)
    for i, linea in enumerate(dato["titular"]):
        fig.text(0.08, 0.52 - 0.045 * i, linea, fontsize=22, fontweight="bold", color=TINTA)

    y = 0.52 - 0.045 * len(dato["titular"]) - 0.035
    for linea in dato["detalle"]:
        fig.text(0.08, y, linea, fontsize=13, color=TINTA_SUAVE)
        y -= 0.035

    fig.add_artist(Line2D([0.08, 0.92], [0.12, 0.12], color=LINEA, lw=1.2))
    # Logo de la web abajo a la izquierda y, a su lado, el nombre y las fuentes
    eje_logo = fig.add_axes([0.08, 0.042, 0.075, 0.056])
    eje_logo.imshow(plt.imread(LOGO))
    eje_logo.axis("off")
    fig.text(0.175, 0.08, "Línea de pase · angelmarqueta.github.io", fontsize=11.5, color=TINTA)
    fig.text(0.175, 0.055, dato["fuentes"], fontsize=9.5, color=TINTA_SUAVE)

    fig.savefig(ruta, dpi=150, facecolor=PAPEL)
    plt.close(fig)


def main():
    dato = json.loads((CARPETA_TEXTOS / "dato_jornada.json").read_text(encoding="utf-8"))
    CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_SALIDA / "dato_jornada.png"
    dibujar(dato, ruta)
    print(f"Tarjeta guardada en {ruta}")


if __name__ == "__main__":
    main()
