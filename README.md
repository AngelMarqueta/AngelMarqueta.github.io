# Línea de pase

Análisis de datos en fútbol. Web personal de proyectos de analítica deportiva de Ángel Marqueta Alonso.

Web: https://lineadepase.github.io/

## Proyectos

- **Real Zaragoza 2026/27**: seguimiento semanal con datos públicos (resultados, goles, tiros, minutos y clasificación) y panel interactivo.
- **Fútbol femenino en datos**: licencias federativas (CSD) y población (INE) para decidir dónde empezar un programa de iniciación.

## Estructura

- `index.html`: portada.
- `proyectos/index.html`, `videos/index.html` y `sobre-mi/index.html`: una página por sección, con el mismo menú y pie que la portada.
- `proyectos/`: además de la página de la sección, una carpeta por proyecto.
- `datos/zaragoza.json`: datos que lee el panel del Zaragoza. Lo genera el script de `analisis/real-zaragoza`.
- `assets/estilo.css`: estilos comunes.
- `analisis/`: código y datos de cada análisis. Ver [analisis/real-zaragoza](analisis/real-zaragoza/README.md) y [analisis/futbol-femenino](analisis/futbol-femenino/README.md).

Análisis personales hechos con datos públicos. Sin relación con ningún club ni competición.
