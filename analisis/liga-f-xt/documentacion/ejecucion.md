# Registro de ejecución y verificación

Última ejecución completa: 16 de octubre de 2026, Python 3.13.

## Pruebas automatizadas

`python -m pytest pruebas`: 7 pruebas aprobadas (bordes del campo, minutos con descuento, cambios y expulsiones, movimientos hacia atrás, separación de partidos entre grupos, solución analítica conocida y ausencia de goles).

## Ejecución con los datos reales

- `codigo/ejecutar.py` termina sin errores con los 240 partidos y los 480 archivos de eventos y alineaciones.
- La tabla de jugadoras coincide con la de la ejecución anterior en todas las columnas.
- El cuaderno `cuadernos/analisis_xt.ipynb` se ejecuta de principio a fin sin errores y recalcula la misma tabla que el programa.
- Las gráficas se han revisado a tamaño real: títulos, ejes, notas, fuente y logotipo legibles, sin solapes. Tamaños: Instagram 1080 × 1350, Facebook 1200 × 630, LinkedIn y web 1600 × 900.

## Incidencias resueltas

- Un intervalo de posición del proveedor terminaba antes de empezar. Por eso los minutos no salen de esos intervalos: se reconstruyen con el once inicial, los cambios, las expulsiones y las salidas definitivas.
- 40 movimientos son de jugadoras sin minutos reglamentarios (por ejemplo, entradas en el descuento). Cuentan para ajustar el modelo, pero no para las tasas por 90 minutos.
- En la superficie de xT casi todo el valor está junto a la portería; el mapa usa una escala de raíz cuadrada para que se distingan también las zonas alejadas. Los números no cambian.
