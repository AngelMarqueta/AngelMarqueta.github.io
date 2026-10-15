"""
Informe completo en HTML para la web.

El informe usa la hoja de estilos de la web y las imágenes de la carpeta
graficos/, así que queda integrado en la página del proyecto. Las
conclusiones las escribo yo en textos/conclusiones.html; aquí solo se
montan junto con las cifras, los gráficos y las tablas.
"""

from html import escape

import pandas as pd

from cargar_datos import CARPETA_TEXTOS

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def numero(valor, decimales=0):
    """Formato español: coma decimal y punto de miles."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def fecha_larga(fecha):
    return f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


def tabla_html(df, columnas, numericas=(), resaltar=None):
    """
    Convierte una tabla de pandas en HTML con las clases de la web.
    columnas: diccionario {columna original: título que se muestra}.
    resaltar: función que recibe la fila y dice si va en negrita (fila propia).
    """
    cabecera = "".join(
        f'<th class="n">{escape(t)}</th>' if c in numericas else f"<th>{escape(t)}</th>"
        for c, t in columnas.items()
    )
    filas = []
    for _, fila in df.iterrows():
        celdas = []
        for c in columnas:
            valor = fila[c]
            if pd.isna(valor) or valor == "":
                texto = "—"
            elif isinstance(valor, float):
                texto = numero(valor, 0 if valor.is_integer() else 2)
            else:
                texto = escape(str(valor))
            clase = ' class="n"' if c in numericas else ""
            celdas.append(f"<td{clase}>{texto}</td>")
        propia = ' class="propio"' if resaltar and resaltar(fila) else ""
        filas.append(f"<tr{propia}>{''.join(celdas)}</tr>")
    return (f'<div class="tarjeta tabla"><table><thead><tr>{cabecera}</tr></thead>'
            f'<tbody>{"".join(filas)}</tbody></table></div>')


def figura(archivo, texto_alternativo, pie):
    return (f'<figure class="figura"><img src="graficos/{archivo}" alt="{escape(texto_alternativo)}" '
            f'loading="lazy"><figcaption>{escape(pie)}</figcaption></figure>')


def generar(ruta, partidos, goles, jugadores, clasificacion, sede, incidencias, fuentes):
    """Escribe informe-completo.html en la carpeta del proyecto de la web."""
    ultima_fecha = partidos["fecha"].max()
    jornada = int(partidos["jornada"].max())
    zgz = clasificacion[clasificacion["equipo"] == "Real Zaragoza"].iloc[0]
    goles_favor = goles[goles["sentido"] == "Favor"]
    desde_banquillo = int((goles["rol_goleador"] == "Suplente").sum())
    de_jugadores = int((goles["rol_goleador"] != "").sum())

    conclusiones = (CARPETA_TEXTOS / "conclusiones.html").read_text(encoding="utf-8")

    kpis = [
        ("Posición", f"{zgz.posicion}.º"),
        ("Puntos", f"{zgz.puntos} de {3 * len(partidos)}"),
        ("Goles", f"{partidos['goles_favor'].sum()}–{partidos['goles_contra'].sum()}"),
        ("Porterías a cero", int(partidos["porteria_cero"].sum())),
        ("Goles desde el banquillo", f"{desde_banquillo} de {de_jugadores}"),
    ]
    kpis_html = "".join(f'<div class="kpi"><span>{k}</span><b>{v}</b></div>' for k, v in kpis)

    tabla_goles = goles_favor.assign(
        propia=goles_favor["propia_puerta"].map({True: "Sí", False: ""}),
        penal=goles_favor["penalti"].map({True: "Sí", False: ""}),
    )
    tabla_goles_html = tabla_html(
        tabla_goles,
        {"jornada": "J", "rival": "Rival", "minuto_texto": "Min.", "jugador": "Goleador",
         "asistencia": "Asistencia", "rol_goleador": "Rol", "penal": "Penalti", "propia": "P. p."},
    )

    tabla_jugadores_html = tabla_html(
        jugadores[jugadores["minutos"] >= 180],
        {"jugador": "Jugador", "partidos": "PJ", "titularidades": "Titular", "minutos": "Minutos",
         "goles": "Goles", "asistencias": "Asist.", "participaciones_por_90": "G+A por 90"},
        numericas=("partidos", "titularidades", "minutos", "goles", "asistencias", "participaciones_por_90"),
    )

    tabla_clasificacion_html = tabla_html(
        clasificacion,
        {"posicion": "#", "equipo": "Equipo", "pj": "PJ", "g": "G", "e": "E", "p": "P",
         "gf": "GF", "gc": "GC", "dg": "DG", "puntos": "Pts"},
        numericas=("posicion", "pj", "g", "e", "p", "gf", "gc", "dg", "puntos"),
        resaltar=lambda f: f["equipo"] == "Real Zaragoza",
    )

    tabla_sede_html = tabla_html(
        sede,
        {"sede": "Sede", "partidos": "PJ", "puntos": "Puntos", "goles_favor": "GF",
         "goles_contra": "GC", "porterias_cero": "Porterías a cero", "puntos_por_partido": "Puntos por partido"},
        numericas=("partidos", "puntos", "goles_favor", "goles_contra", "porterias_cero", "puntos_por_partido"),
    )

    incidencias = incidencias.assign(
        jornada_texto=incidencias["jornada"].map(lambda j: "General" if j == 0 else f"J{j}"))
    tabla_incidencias_html = tabla_html(
        incidencias, {"jornada_texto": "Partido", "campo": "Dato", "problema": "Problema", "decision": "Qué hago"})

    lista_fuentes = "".join(
        f'<li><a href="{escape(u)}" rel="noopener" target="_blank">{escape(u)}</a></li>' for u in fuentes)

    html = f"""<!doctype html>
<html lang="es" class="tema-real-zaragoza">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Informe completo: Real Zaragoza 2026/27 · Línea de pase</title>
<meta name="description" content="Informe completo del seguimiento del Real Zaragoza 2026/27 con datos públicos.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Big+Shoulders+Display:wght@700;800&display=swap">
<script src="../../assets/tema.js"></script>
<link rel="stylesheet" href="../../assets/estilo.css">
<link rel="stylesheet" href="../../assets/real-zaragoza.css?v=20261014e">
<script src="../../assets/mejoras.js" defer></script>
<link rel="icon" href="../../assets/icono.svg" type="image/svg+xml">
</head>
<body>
<header class="cabecera">
  <div class="envoltorio">
    <a class="marca" href="../../index.html" aria-label="Línea de pase, inicio">
      <svg viewBox="0 0 64 48" aria-hidden="true"><defs><linearGradient id="lp-cesped" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#2f6b45"/><stop offset="1" stop-color="#3f8f5c"/></linearGradient><clipPath id="lp-campo"><rect x="2" y="2" width="60" height="44" rx="8"/></clipPath></defs><rect x="2" y="2" width="60" height="44" rx="8" fill="url(#lp-cesped)" stroke="#f4f7f1" stroke-opacity=".55" stroke-width="2"/><g clip-path="url(#lp-campo)" fill="#fff" fill-opacity=".08"><rect x="2" y="0" width="7.5" height="48"/><rect x="17" y="0" width="7.5" height="48"/><rect x="32" y="0" width="7.5" height="48"/><rect x="47" y="0" width="7.5" height="48"/></g><g fill="none" stroke="#fff" stroke-opacity=".75" stroke-width="1.8"><rect x="6" y="6" width="52" height="36" rx="2"/><path d="M32 6v36"/><circle cx="32" cy="24" r="6"/><path d="M58 15h-8v18h8"/></g><path d="M13 34C23 20 35 18 47 23" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-dasharray="0.1 5.6"/><circle cx="12" cy="35" r="3.8" fill="#14261d" stroke="#fff" stroke-width="1.4"/><circle cx="50" cy="24" r="4.6" fill="#ff7a2f" stroke="#fff" stroke-width="1.4"/></svg>
      Línea de pase
    </a>
    <nav class="nav" aria-label="Principal">
      <a href="../../index.html">Inicio</a>
      <a href="../index.html" aria-current="page">Proyectos</a>
      <a href="../../videos/index.html">Vídeos</a>
      <a href="../../sobre-mi/index.html">Sobre mí</a>
    </nav>
  </div>
</header>

<main class="envoltorio" data-informe>
  <p class="migas"><a href="../index.html">Proyectos</a> / <a href="index.html">Real Zaragoza 2026/27</a> / Informe completo</p>
  <section class="cab-proyecto">
    <img class="escudo-seccion" src="../../assets/real-zaragoza-escudo.png" alt="Escudo del Real Zaragoza" width="52" height="52">
    <p class="etiqueta">Informe completo · Primera Federación, grupo 2</p>
    <h1>Real Zaragoza 2026/27 tras la jornada {jornada}</h1>
    <p class="entradilla corte-visible">Datos de los {len(partidos)} partidos de liga jugados hasta el {fecha_larga(ultima_fecha)}. Todo sale de fuentes públicas, contrastadas entre sí.</p>
  </section>

  <section class="seccion">
    <div class="kpis">{kpis_html}</div>
  </section>

  <section class="seccion lectura">
    <p class="etiqueta">Conclusiones</p>
    <h2>Qué dicen los datos</h2>
    {conclusiones}
  </section>

  <section class="seccion">
    <p class="etiqueta">Gráficos</p>
    <h2>Resultados y goles</h2>
    {figura("resumen.png", "Marcadores, puntos acumulados, goles por tramo y participación en goles por jugador", "Marcadores, puntos acumulados, goles por tramo de 15 minutos y goles y asistencias por jugador.")}
    <h2>Tiros</h2>
    {figura("tiros.png", "Tiros del Real Zaragoza y de sus rivales en cada partido", "Tiros por partido. Más claros, los partidos en los que el desglose de tiros no cuadra.")}
    <h2>Clasificación y banquillo</h2>
    {figura("contexto.png", "Clasificación por puntos y goles de titulares frente a suplentes", "Clasificación actual y goles marcados por titulares y por jugadores que salieron desde el banquillo.")}
    <h2>El grupo y la plantilla</h2>
    {figura("equipos_minutos.png", "Goles a favor y en contra de los 20 equipos y minutos de los jugadores", "Izquierda: ataque y defensa de los 20 equipos. Derecha: minutos de los jugadores con 180 o más.")}
  </section>

  <section class="seccion">
    <p class="etiqueta">Tablas</p>
    <h2>Goles a favor</h2>
    {tabla_goles_html}
    <p class="nota">«Suplente» quiere decir que el goleador había entrado desde el banquillo. Las asistencias son las que recoge futboltotal, que no las apunta todas.</p>
    <h2>Minutos de la plantilla</h2>
    {tabla_jugadores_html}
    <p class="nota">Jugadores con 180 minutos o más. Los minutos no cuentan el descuento: un titular que juega todo el partido suma 90.</p>
    <h2>Casa y fuera</h2>
    {tabla_sede_html}
    <h2>Clasificación tras la jornada {clasificacion['tras_jornada'].iloc[0]}</h2>
    {tabla_clasificacion_html}
  </section>

  <section class="seccion">
    <p class="etiqueta">Calidad de los datos</p>
    <h2>Incidencias y decisiones</h2>
    <p class="lectura">Cuando dos fuentes no coinciden, lo apunto aquí junto con el dato que me quedo. Un dato que no encuentro queda vacío: nunca lo convierto en un cero.</p>
    {tabla_incidencias_html}
  </section>

  <section class="seccion lectura">
    <p class="etiqueta">Método</p>
    <h2>Cómo está hecho</h2>
    <p>Los datos de cada partido los copio a mano de las fichas públicas. Un script de Python los cruza entre sí (goles con marcadores, cambios con alineaciones, tarjetas con estadísticas y clasificación con resultados) y no genera nada si algo no cuadra. Después calcula las tablas, dibuja los gráficos y monta esta página. Un segundo script en R repite los cálculos principales para comprobar que salen igual.</p>
    <div class="enlaces">
      <a class="boton lleno" href="https://github.com/lineadepase/lineadepase.github.io/tree/main/analisis/real-zaragoza" rel="noopener" target="_blank">Código y datos en GitHub</a>
      <a class="boton" href="index.html">Volver al panel</a>
    </div>
    <h2>Fuentes</h2>
    <ul class="fuentes">{lista_fuentes}</ul>
  </section>
</main>

<footer class="pie">
  <div class="envoltorio">
    <p>Análisis personal con datos públicos. Línea de pase no tiene relación con el Real Zaragoza ni con ningún otro club o competición.</p>
    <p><a href="../../sobre-mi/index.html#contacto">Contacto</a> · <a href="https://www.linkedin.com/in/angel-marqueta-alonso-a8831164" rel="noopener" target="_blank">LinkedIn</a> · <a href="https://www.youtube.com/@lineadepasefutbol" rel="noopener" target="_blank">YouTube</a> · <a href="https://www.instagram.com/lineadepasefutbol/" rel="noopener" target="_blank">Instagram</a> · <a href="https://www.facebook.com/profile.php?id=61594945036383" rel="noopener" target="_blank">Facebook</a> · © {ultima_fecha.year} Ángel Marqueta Alonso</p>
  </div>
</footer>
</body>
</html>
"""
    ruta.write_text(html, encoding="utf-8")
