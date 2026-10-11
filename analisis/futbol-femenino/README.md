# Fútbol femenino: ¿dónde empezar un programa de iniciación?

Actividad colaborativa del módulo 1 del Máster en Big Data Deportivo. El resultado está en [Línea de pase](https://angelmarqueta.github.io/proyectos/futbol-femenino/).

## La pregunta

El fútbol femenino crece, pero sigue siendo una de cada diez licencias. Si una entidad quisiera probar un programa de iniciación en dos comunidades, ¿por dónde empezaría?

## Datos

| Archivo | Origen |
|---|---|
| `datos/entrada/licencias_futbol_csd.csv` | CSD, Estadística de Deporte Federado. Edición 2025 (tablas 4, 4.1 y 4.2) y edición 2023 (tabla 8.4.2): licencias de fútbol por sexo y comunidad |
| `datos/entrada/poblacion_mujeres_ine_2025.csv` | INE, tabla 67988: mujeres a 1 de enero de 2025 por comunidad, con el código de cada serie |
| `datos/entrada/comunidades.geojson` | Límites de las comunidades autónomas del proyecto *click_that_hood* de Code for Germany |

Las cifras del CSD las he copiado de los PDF. Por eso el script comprueba antes de nada que cada serie suma el total de España.

## Método

Para cada comunidad calculo:

- licencias femeninas por cada 1.000 mujeres,
- porcentaje de mujeres sobre todas las licencias de fútbol,
- crecimiento de las licencias femeninas entre 2023 y 2025.

Me quedo con las comunidades que están por debajo de la media española en los dos primeros indicadores y que, además, ya crecen. Cumplen ocho de diecisiete. De esas elijo las dos con más mujeres: Andalucía y la Comunitat Valenciana. Ceuta y Melilla aparecen en el mapa, pero no entran en la selección.

## Cómo ejecutarlo

Desde la raíz del repositorio:

```
pip install -r analisis/futbol-femenino/requirements.txt
python analisis/futbol-femenino/codigo/analisis.py
```

Genera `datos/salida/indicadores.csv`, `datos/salida/criterio_seleccion.csv` y el mapa, que también se copia a la web.

## Límites

- Una licencia no es una persona: alguien puede tener más de una.
- Las licencias no recogen el fútbol que se juega fuera de las federaciones.
- La estadística no separa por edades, así que la tasa se calcula sobre todas las mujeres.
- Una tasa baja no demuestra que haya mujeres queriendo apuntarse: eso habría que preguntarlo.
