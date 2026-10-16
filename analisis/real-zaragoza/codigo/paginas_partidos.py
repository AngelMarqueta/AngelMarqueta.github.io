"""
Páginas de cada partido del Real Zaragoza y pestañas del seguimiento.

Uso (desde la raíz del repositorio):
    python analisis/real-zaragoza/codigo/paginas_partidos.py

También se ejecuta solo al final de actualizar.py, así que después de cada
jornada no hay que acordarse de nada.

Qué genera dentro de proyectos/real-zaragoza/:
    - jornadas.html        La pestaña «Jornada a jornada»: una tarjeta por partido.
    - jornada-N.html       Una página por partido de liga (N = número de jornada).
    - ultimo-partido.html  La pestaña «Último partido»: una crónica corta del último
                           partido (qué pasó, cómo queda el equipo, en qué se salió
                           de lo normal y qué viene), con enlace a su ficha completa.

Cómo está montado:
    Las páginas son HTML estático. No uso ninguna librería de plantillas (tipo
    Jinja) para no añadir dependencias: con f-strings de Python y html.escape()
    es suficiente para un sitio así de pequeño. La cabecera y el pie los copio
    de proyectos/real-zaragoza/index.html; así, si un día cambio el menú o los
    enlaces del pie, las páginas nuevas lo heredan sin tocar este archivo.

Datos que usa (todos de datos/entrada):
    partidos.csv, goles.csv, alineaciones.csv, cambios.csv, tarjetas.csv,
    tiros.csv, proximos.csv, sofascore.csv y video/goles_video.csv +
    video/resumenes_youtube.csv. Si a un partido le falta algo (por ejemplo,
    todavía no he visto el vídeo), esa sección simplemente no sale.
"""

import html
import re
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Rutas. Este archivo vive en analisis/real-zaragoza/codigo/, así que subo
# dos niveles para llegar al proyecto y dos más para la raíz de la web.
# ---------------------------------------------------------------------------
PROYECTO = Path(__file__).resolve().parents[1]
ENTRADA = PROYECTO / "datos" / "entrada"
WEB = PROYECTO.parents[1]
CARPETA_PAGINAS = WEB / "proyectos" / "real-zaragoza"

LIGA = "Primera Federación"

# Nombre con el que sale el Zaragoza en el marcador. Lo dejo en una constante
# para no escribirlo a mano en veinte sitios.
ZARAGOZA = "Real Zaragoza"

# Textos legibles para los códigos que uso en goles_video.csv. En el CSV los
# guardo cortos y sin tildes porque es más cómodo filtrar; en la web, no.
INICIOS = {"ataque_posicional": "Ataque posicional", "transicion": "Transición rápida",
           "balon_parado": "Balón parado", "penalti": "Penalti", "sin_dato": "No se ve"}
CARRILES = {"izquierda": "Izquierda", "centro": "Centro", "derecha": "Derecha", "sin_dato": "No se ve"}
PASES = {"centro_lateral": "Centro lateral", "pase_atras": "Pase atrás", "pase_interior": "Pase raso por dentro",
         "pase_al_espacio": "Pase al espacio", "rechace": "Rechace", "corner": "Córner",
         "falta_lateral": "Falta lateral", "falta_directa": "Falta directa",
         "sin_pase": "Sin pase", "sin_dato": "No se ve"}
ZONAS = {"area_pequena": "Área pequeña", "area_central": "Área grande, centro",
         "area_lateral": "Área grande, lateral", "fuera_area": "Fuera del área",
         "penalti": "Penalti", "sin_dato": "No se ve"}

# Estadísticas de Sofascore que enseño en cada ficha, en este orden.
# El tercer valor dice si es un porcentaje (para pintar el símbolo %) y el
# cuarto cuántos decimales quiero (el xG con dos, el resto sin decimales).
ESTADISTICAS = [
    ("posesion_pct", "Posesión", True, 0),
    ("xg", "Goles esperados (xG)", False, 2),
    ("ocasiones_claras", "Ocasiones claras", False, 0),
    ("tiros", "Tiros", False, 0),
    ("tiros_a_puerta", "Tiros a puerta", False, 0),
    ("tiros_dentro_area", "Tiros dentro del área", False, 0),
    ("corners", "Córners", False, 0),
    ("pases_buenos", "Pases buenos", False, 0),
    ("duelos_ganados_pct", "Duelos ganados", True, 0),
    ("faltas", "Faltas", False, 0),
]

e = html.escape  # alias corto: lo uso en casi todas las líneas que pintan texto


# ---------------------------------------------------------------------------
# Lectura de datos
# ---------------------------------------------------------------------------

def leer(nombre):
    """Lee un CSV de datos/entrada. Si no existe, devuelvo una tabla vacía en
    vez de romper: así una sección sin datos simplemente no se pinta."""
    ruta = ENTRADA / nombre
    if not ruta.exists():
        return pd.DataFrame()
    # encoding="utf-8-sig" lee igual de bien un CSV con o sin BOM (la marca
    # que pone Excel al principio). Así no me salen «Ã±» en vez de «ñ».
    return pd.read_csv(ruta, encoding="utf-8-sig")


def cargar():
    """Junta en un diccionario todas las tablas que necesito."""
    d = {nombre: leer(f"{nombre}.csv") for nombre in
         ("partidos", "goles", "alineaciones", "cambios", "tarjetas", "tiros", "proximos", "sofascore", "clasificacion")}
    d["video"] = leer("video/goles_video.csv")
    d["resumenes"] = leer("video/resumenes_youtube.csv")
    # Solo la liga tiene número de jornada, que es lo que uso para las URL
    p = d["partidos"]
    p = p[p["competicion"] == LIGA].copy()
    p["jornada"] = p["jornada"].astype(int)
    p["fecha"] = pd.to_datetime(p["fecha"])
    d["liga"] = p.sort_values("jornada").reset_index(drop=True)
    return d


# ---------------------------------------------------------------------------
# Plantilla: cabecera y pie copiados de index.html
# ---------------------------------------------------------------------------

def plantilla():
    """Devuelve (cabecera, pie) en texto, sacados de la página principal del proyecto.
    Corto por las etiquetas <main> y <footer>, que solo aparecen una vez."""
    texto = (CARPETA_PAGINAS / "index.html").read_text(encoding="utf-8")
    cabecera = texto[:texto.index("<main")]
    pie = texto[texto.index("<footer"):texto.index("</footer>") + len("</footer>")]
    return cabecera, pie


def pagina(titulo, descripcion, cuerpo):
    """Monta una página completa: cabecera con su <title> y su descripción,
    el contenido que le paso y el pie común."""
    cabecera, pie = plantilla()
    cabecera = re.sub(r"<title>.*?</title>", f"<title>{e(titulo)} · Línea de pase</title>", cabecera, count=1)
    cabecera = re.sub(r'<meta name="description" content="[^"]*">',
                      f'<meta name="description" content="{e(descripcion)}">', cabecera, count=1)
    return f"{cabecera}{cuerpo}\n{pie}\n</body>\n</html>\n"


def pestanas(activa):
    """Barra de pestañas del seguimiento. `activa` es la clave de la que se está viendo.
    Uso aria-current="page" para que un lector de pantalla también sepa dónde está."""
    enlaces = [("temporada", "index.html", "Temporada"),
               ("jornadas", "jornadas.html", "Jornada a jornada"),
               ("ultimo", "ultimo-partido.html", "Último partido"),
               ("grupo", "grupo-2.html", "Grupo 2")]
    items = "".join(
        f'<a href="{url}"{" aria-current=\"page\"" if clave == activa else ""}>{texto}</a>'
        for clave, url, texto in enlaces)
    return f'<nav class="pestanas" aria-label="Secciones del seguimiento">{items}</nav>'


def subpestanas(liga, actual=None):
    """Fila de botones J1, J2, J3… para saltar de un partido a otro.
    El color de cada uno indica el resultado (victoria, empate o derrota)."""
    botones = []
    for p in liga.itertuples():
        clase = resultado(p)[1]
        marcado = ' aria-current="page"' if p.jornada == actual else ""
        botones.append(f'<a class="{clase}" href="jornada-{p.jornada}.html"{marcado} '
                       f'title="J{p.jornada} · {e(p.rival)} {p.goles_favor}-{p.goles_contra}">J{p.jornada}</a>')
    return f'<nav class="subpestanas" aria-label="Partidos de liga">{"".join(botones)}</nav>'


# ---------------------------------------------------------------------------
# Pequeñas ayudas
# ---------------------------------------------------------------------------

def resultado(p):
    """Texto y clase CSS del resultado desde el punto de vista del Zaragoza."""
    if p.goles_favor > p.goles_contra:
        return "Victoria", "victoria"
    if p.goles_favor == p.goles_contra:
        return "Empate", "empate"
    return "Derrota", "derrota"


def fecha_larga(fecha):
    """30/08/2026 -> «domingo, 30 de agosto de 2026». Lo hago a mano para no depender
    del idioma del sistema (locale), que en un servidor suele estar en inglés."""
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre"]
    return f"{dias[fecha.weekday()]}, {fecha.day} de {meses[fecha.month - 1]} de {fecha.year}"


def numero(valor, decimales=0, pct=False):
    """Formatea un número a la española (coma decimal) y añade % si hace falta."""
    if pd.isna(valor):
        return "—"
    texto = f"{valor:.{decimales}f}".replace(".", ",")
    return f"{texto} %" if pct else texto


def id_youtube(url):
    """Saca el identificador del vídeo de una URL tipo youtube.com/watch?v=XXXX."""
    m = re.search(r"v=([\w-]{6,})", str(url))
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Secciones de la ficha de un partido
# ---------------------------------------------------------------------------

def bloque_marcador(p):
    """Marcador grande con el local a la izquierda, como se ve en la tele.
    Reutilizo las clases mp-* del marcador en directo de la página principal."""
    local = ZARAGOZA if p.sede == "Casa" else p.rival
    visitante = p.rival if p.sede == "Casa" else ZARAGOZA
    gl, gv = (p.goles_favor, p.goles_contra) if p.sede == "Casa" else (p.goles_contra, p.goles_favor)
    dl, dv = (p.gf_descanso, p.gc_descanso) if p.sede == "Casa" else (p.gc_descanso, p.gf_descanso)

    def equipo(nombre):
        # El escudo solo lo tengo del Zaragoza; para el rival pongo sus iniciales
        if nombre == ZARAGOZA:
            escudo = '<img src="../../assets/real-zaragoza-escudo.png" alt="" width="42" height="42">'
            return f'<span class="mp-equipo zgz"><span class="mp-escudo" aria-hidden="true">{escudo}</span>{e(nombre)}</span>'
        palabras = [w for w in nombre.split() if w not in {"CD", "CF", "UD", "FC", "SD", "CE", "de"}]
        iniciales = "".join(w[0] for w in palabras[:2]).upper()
        return f'<span class="mp-equipo"><span class="mp-escudo" aria-hidden="true">{e(iniciales)}</span>{e(nombre)}</span>'

    texto, clase = resultado(p)
    return f"""
    <div class="ficha-marcador mp-cesped">
      <div class="mp-cab"><span>{LIGA} · Jornada {p.jornada} · {fecha_larga(p.fecha)}</span><span class="mp-estado {clase}">{texto}</span></div>
      <div class="mp-equipos">{equipo(local)}<div><span class="mp-resultado">{gl}<span class="sep">-</span>{gv}</span><div class="mp-sub">Descanso: {dl}-{dv}</div></div>{equipo(visitante)}</div>
    </div>"""


def bloque_kpis(p, liga, sofa):
    """Cuatro cifras rápidas: puntos, puntos acumulados, y el xG de cada equipo."""
    puntos = {"victoria": 3, "empate": 1, "derrota": 0}[resultado(p)[1]]
    # Puntos acumulados hasta esta jornada incluida
    acumulados = sum({"victoria": 3, "empate": 1, "derrota": 0}[resultado(x)[1]]
                     for x in liga.itertuples() if x.jornada <= p.jornada)
    s = sofa.get(p.partido_id, {})
    xg = s.get("xg")
    cifras = [("Puntos", puntos), ("Puntos acumulados", acumulados),
              ("xG Zaragoza", numero(xg[0], 2) if xg else "—"),
              ("xG rival", numero(xg[1], 2) if xg else "—")]
    return '<div class="kpis">' + "".join(f'<div class="kpi"><span>{k}</span><b>{v}</b></div>' for k, v in cifras) + "</div>"


def bloque_goles(p, goles, tarjetas):
    """Lista de goles en orden y tarjetas del Zaragoza."""
    g = goles[goles["partido_id"] == p.partido_id].sort_values(["parte", "minuto", "anadido"])
    filas = []
    for x in g.itertuples():
        minuto = f"{x.minuto}+{int(x.anadido)}" if x.anadido else f"{x.minuto}"
        extra = " (penalti)" if x.penalti == "si" else (" (en propia puerta)" if x.propia_puerta == "si" else "")
        asistencia = f'<span class="mp-asist">Asistencia: {e(x.asistencia)}</span>' if isinstance(x.asistencia, str) and x.asistencia else ""
        lado = "favor" if x.sentido == "Favor" else "contra"
        quien = ZARAGOZA if lado == "favor" else p.rival
        filas.append(f'<li class="gol-{lado}"><span class="mp-min">{minuto}\'</span>{e(x.jugador)}{extra} '
                     f'<small>· {e(quien)}</small>{asistencia}</li>')
    lista = f'<ul class="lista-goles">{"".join(filas)}</ul>' if filas else '<p class="nota">Sin goles.</p>'

    t = tarjetas[tarjetas["partido_id"] == p.partido_id]
    if len(t):
        items = "".join(f'<li><span class="mp-tarjeta{" roja" if x.tarjeta == "Roja" else ""}" aria-label="{e(x.tarjeta)}"></span>{e(x.jugador)}</li>'
                        for x in t.itertuples())
        tarjetas_html = f'<ul class="mp-tarjetas">{items}</ul>'
    else:
        tarjetas_html = '<p class="nota">Sin tarjetas.</p>'
    return f"""
    <div class="tarjeta">
      <h3>Goles</h3>{lista}
      <h3>Tarjetas del Real Zaragoza</h3>{tarjetas_html}
    </div>"""


def bloque_estadisticas(p, sofa, tiros):
    """Barras enfrentadas Zaragoza-rival con las estadísticas de Sofascore.
    Si Sofascore no tiene el partido, uso al menos los tiros y la posesión de tiros.csv."""
    s = dict(sofa.get(p.partido_id, {}))
    if not s:
        t = tiros[tiros["partido_id"] == p.partido_id]
        if t.empty:
            return ""
        t = t.iloc[0]
        s = {"posesion_pct": (t.posesion_pct, 100 - t.posesion_pct),
             "tiros": (t.tiros_zaragoza, t.tiros_rival),
             "tiros_a_puerta": (t.a_puerta_zaragoza, t.a_puerta_rival)}
    filas = []
    for clave, nombre, pct, dec in ESTADISTICAS:
        if clave not in s:
            continue
        z, r = s[clave]
        if pd.isna(z) or pd.isna(r):
            continue
        total = (z + r) or 1  # evito dividir entre cero si los dos valen 0
        filas.append(f"""<div class="mp-stat"><dt>{nombre}</dt><dd class="v">{numero(z, dec, pct)}</dd>
          <dd class="mp-barra"><span style="width:{100 * z / total:.1f}%"></span><span style="width:{100 * r / total:.1f}%"></span></dd>
          <dd class="v">{numero(r, dec, pct)}</dd></div>""")
    if not filas:
        return ""
    return f"""
    <div class="tarjeta">
      <h3>Estadísticas</h3>
      <p class="leyenda"><span><i style="background:var(--cesped)"></i>Real Zaragoza (izquierda)</span><span><i style="background:var(--muted)"></i>{e(p.rival)}</span></p>
      <dl class="mp-stats">{"".join(filas)}</dl>
      <p class="mp-pie">Fuente: Sofascore. Su modelo de xG no es público; lo uso para comparar partidos entre sí.</p>
    </div>"""


def campo_svg(goles_partido):
    """Medio campo en SVG con el punto de remate de cada gol del partido.
    Uso las mismas coordenadas que goles_video.csv (metros, campo de 105 x 68,
    atacando hacia la derecha). En SVG la y crece hacia abajo, así que la
    invierto (68 - y) para que la banda izquierda quede arriba."""
    puntos = []
    for x in goles_partido.itertuples():
        if pd.isna(x.tiro_x):
            continue
        cx, cy = x.tiro_x, 68 - x.tiro_y
        # Flecha del último pase, si lo tengo apuntado
        if not pd.isna(x.pase_x):
            puntos.append(f'<line x1="{x.pase_x}" y1="{68 - x.pase_y}" x2="{cx}" y2="{cy}" class="pase"/>')
        clase = "favor" if x.sentido == "Favor" else "contra"
        puntos.append(f'<circle cx="{cx}" cy="{cy}" r="1.6" class="{clase}"><title>{e(x.minuto)}\' · {e(x.goleador)}</title></circle>')
    if not puntos:
        return ""
    return f"""<svg class="campo-mini" viewBox="51 -2 57 72" role="img" aria-label="Medio campo con el punto aproximado de remate de cada gol">
      <defs><linearGradient id="zgz-mitad"><stop offset="0" stop-color="#213e96"/><stop offset=".5" stop-color="#213e96"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff"/></linearGradient></defs>
      <rect x="51" y="-2" width="57" height="72" class="cesped"/>
      <g class="lineas"><rect x="52.5" y="0" width="52.5" height="68"/><path d="M105 13.85H88.5V54.15H105M105 24.85H99.5V43.15H105"/>
      <path d="M52.5 24.85A9.15 9.15 0 0 1 52.5 43.15"/><path d="M88.5 26.7A9.15 9.15 0 0 0 88.5 41.3"/><path d="M105 30.34h1.5v7.32H105"/></g>
      {"".join(puntos)}
    </svg>"""


def bloque_video(p, video, resumenes):
    """Cómo fueron los goles según lo que apunté viendo el resumen, el mini campo
    y el vídeo del resumen incrustado (con youtube-nocookie, que no deja cookies
    hasta que alguien le da al play)."""
    g = video[video["partido_id"] == p.partido_id] if len(video) else video
    r = resumenes[resumenes["partido_id"] == p.partido_id] if len(resumenes) else resumenes
    if g.empty and r.empty:
        return ""
    tabla = ""
    if not g.empty:
        filas = "".join(
            f"<tr><td>{e(x.minuto)}'</td><td>{e(x.marcador)}</td><td>{e(x.goleador)}</td>"
            f"<td>{INICIOS.get(x.inicio, x.inicio)}</td><td>{CARRILES.get(x.carril, x.carril)}</td>"
            f"<td>{PASES.get(x.ultimo_pase, x.ultimo_pase)}</td><td>{ZONAS.get(x.zona_remate, x.zona_remate)}</td>"
            f"<td>{e(x.confianza)}</td></tr>"
            for x in g.itertuples())
        notas = "".join(f"<li><b>{e(x.minuto)}'</b> {e(x.nota)}</li>" for x in g.itertuples() if isinstance(x.nota, str))
        tabla = f"""
      <div class="tarjeta tabla" tabindex="0" role="region" aria-label="Detalle de los goles, tabla desplazable"><table>
        <thead><tr><th>Min.</th><th>Marcador</th><th>Goleador</th><th>Jugada</th><th>Carril</th><th>Último pase</th><th>Remate</th><th>Confianza</th></tr></thead>
        <tbody>{filas}</tbody></table></div>
      <p class="nota">Marcador visto desde el Zaragoza (Zaragoza-rival). El carril es el del equipo que ataca.</p>
      <div class="video-goles">{campo_svg(g)}<ul class="notas-goles">{notas}</ul></div>
      <p class="leyenda"><span><i class="zgz-mitad"></i>Gol del Zaragoza</span><span><i class="rival-naranja"></i>Gol del rival</span><span>Posición estimada a ojo; cada equipo ataca hacia la derecha</span></p>"""
    reproductor = ""
    if not r.empty:
        vid = id_youtube(r.iloc[0]["url"])
        if vid:
            reproductor = f"""
      <div class="video-resumen"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" title="{e(r.iloc[0]['titulo'])}" loading="lazy" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></div>
      <p class="nota">Resumen de {e(r.iloc[0]['canal'])} en YouTube.</p>"""
    return f"""
  <section class="seccion" aria-labelledby="t-video-{p.jornada}">
    <p class="etiqueta">Visto en vídeo</p>
    <h2 id="t-video-{p.jornada}">Cómo fueron los goles</h2>{tabla}{reproductor}
  </section>"""


def bloque_alineacion(p, alineaciones, cambios):
    """Once inicial y cambios del Zaragoza."""
    once = alineaciones[alineaciones["partido_id"] == p.partido_id]["jugador"].tolist()
    if not once:
        return ""
    c = cambios[cambios["partido_id"] == p.partido_id].sort_values("minuto")
    lista_cambios = "".join(f"<li><span class=\"mp-min\">{int(x.minuto)}'</span>Entra {e(x.entra)} · sale {e(x.sale)}</li>"
                            for x in c.itertuples()) or "<li>Sin cambios apuntados.</li>"
    return f"""
    <div class="tarjeta">
      <h3>Once inicial</h3><ul class="once">{"".join(f"<li>{e(j)}</li>" for j in once)}</ul>
      <h3>Cambios</h3><ul class="cambios">{lista_cambios}</ul>
    </div>"""


def ficha(p, d, sofa, activa, titulo_extra=""):
    """Cuerpo completo de la página de un partido. Lo uso tanto para jornada-N.html
    como para ultimo-partido.html; lo único que cambia es la pestaña activa y la
    entrada de arriba."""
    liga = d["liga"]
    anterior = liga[liga["jornada"] == p.jornada - 1]
    siguiente = liga[liga["jornada"] == p.jornada + 1]
    navegacion = []
    if len(anterior):
        a = anterior.iloc[0]
        navegacion.append(f'<a class="boton" href="jornada-{a.jornada}.html">← J{a.jornada} · {e(a.rival)}</a>')
    if len(siguiente):
        s = siguiente.iloc[0]
        navegacion.append(f'<a class="boton" href="jornada-{s.jornada}.html">J{s.jornada} · {e(s.rival)} →</a>')

    # Fuentes del partido: la ficha que apunté en partidos.csv, Sofascore y el vídeo
    fuentes = [f'<li><a href="{e(p.fuente_url)}" target="_blank" rel="noopener">Ficha del partido</a></li>']
    if p.partido_id in sofa:
        fila = d["sofascore"][d["sofascore"]["partido_id"] == p.partido_id].iloc[0]
        # Enlazo la respuesta de su API: es justo el dato que he copiado, sin interpretaciones
        fuentes.append(f'<li><a href="{e(fila.fuente_url)}" target="_blank" rel="noopener">Estadísticas de Sofascore (datos en bruto)</a></li>')
    r = d["resumenes"][d["resumenes"]["partido_id"] == p.partido_id] if len(d["resumenes"]) else []
    for x in (r.itertuples() if len(r) else []):
        fuentes.append(f'<li><a href="{e(x.url)}" target="_blank" rel="noopener">Resumen de {e(x.canal)}</a></li>')

    return f"""<main class="envoltorio">
  <p class="migas"><a href="../index.html">Proyectos</a> / <a href="index.html">Real Zaragoza 2026/27</a> / Jornada {p.jornada}</p>
  {pestanas(activa)}
  {subpestanas(liga, p.jornada)}
  <section class="seccion primera" aria-labelledby="t-partido">
    <p class="etiqueta">{titulo_extra or f"Jornada {p.jornada}"}</p>
    <h1 id="t-partido">{"Real Zaragoza – " + e(p.rival) if p.sede == "Casa" else e(p.rival) + " – Real Zaragoza"}</h1>
    {bloque_marcador(p)}
    {bloque_kpis(p, liga, sofa)}
    <div class="graficos">{bloque_goles(p, d["goles"], d["tarjetas"])}{bloque_estadisticas(p, sofa, d["tiros"])}{bloque_alineacion(p, d["alineaciones"], d["cambios"])}</div>
  </section>
  {bloque_video(p, d["video"], d["resumenes"])}
  <section class="seccion lectura" aria-label="Fuentes y navegación">
    <h2>Fuentes</h2><ul>{"".join(fuentes)}</ul>
    <div class="enlaces">{"".join(navegacion)}<a class="boton lleno" href="jornadas.html">Todas las jornadas</a></div>
  </section>
</main>"""


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

def sofascore_por_partido(sofa_largo):
    """Paso sofascore.csv (una fila por métrica) a un diccionario
    {partido_id: {metrica: (zaragoza, rival)}}, que es más cómodo de consultar."""
    resultado_dict = {}
    for x in sofa_largo.itertuples():
        resultado_dict.setdefault(x.partido_id, {})[x.metrica] = (x.zaragoza, x.valor_rival)
    return resultado_dict


def pagina_jornadas(d, sofa):
    """Pestaña «Jornada a jornada»: una tarjeta por partido, del más reciente al más antiguo."""
    tarjetas = []
    acumulado = 0
    puntos_tras = {}
    for p in d["liga"].itertuples():           # primero recorro en orden para los puntos acumulados
        acumulado += {"victoria": 3, "empate": 1, "derrota": 0}[resultado(p)[1]]
        puntos_tras[p.jornada] = acumulado
    for p in d["liga"].sort_values("jornada", ascending=False).itertuples():
        texto, clase = resultado(p)
        xg = sofa.get(p.partido_id, {}).get("xg")
        linea_xg = f"xG {numero(xg[0], 2)} – {numero(xg[1], 2)}" if xg else "xG sin datos"
        tarjetas.append(f"""
      <a class="tarjeta-jornada {clase}" href="jornada-{p.jornada}.html">
        <span class="tj-cab">J{p.jornada} · {p.fecha.strftime('%d/%m/%Y')} · {"En casa" if p.sede == "Casa" else "Fuera"}</span>
        <span class="tj-rival">{e(p.rival)}</span>
        <span class="tj-marcador">{p.goles_favor}–{p.goles_contra}</span>
        <span class="tj-pie">{texto} · {puntos_tras[p.jornada]} puntos · {linea_xg}</span>
      </a>""")
    cuerpo = f"""<main class="envoltorio">
  <p class="migas"><a href="../index.html">Proyectos</a> / <a href="index.html">Real Zaragoza 2026/27</a> / Jornada a jornada</p>
  {pestanas("jornadas")}
  {subpestanas(d["liga"])}
  <section class="seccion primera" aria-labelledby="t-jornadas">
    <p class="etiqueta">Archivo de temporada</p>
    <h1 id="t-jornadas">Jornada a jornada</h1>
    <p class="entradilla">Cada partido de liga tiene su propia ficha: marcador, goles, tarjetas, alineación, estadísticas de Sofascore y, cuando lo he visto, cómo fueron los goles con el resumen en vídeo.</p>
    <p class="nota">Marcador desde el punto de vista del Real Zaragoza: goles a favor–goles en contra. Los puntos son acumulados.</p>
    <div class="rejilla-jornadas">{"".join(tarjetas)}</div>
    <p class="nota"><a href="../../analisis/real-zaragoza/datos/salida/partidos_liga.csv" download>Descargar los partidos de liga (CSV)</a> · <a href="../../analisis/real-zaragoza/datos/tablas/datos_real_zaragoza.xlsx" download>Todas las tablas en Excel</a></p>
  </section>
</main>"""
    (CARPETA_PAGINAS / "jornadas.html").write_text(
        pagina("Real Zaragoza 2026/27, jornada a jornada",
               "Fichas de cada partido de liga del Real Zaragoza 2026/27: marcador, goles, estadísticas y vídeo.", cuerpo),
        encoding="utf-8")


def pagina_partido(p, d, sofa):
    cuerpo = ficha(p, d, sofa, "jornadas")
    titulo = f"J{p.jornada}: {ZARAGOZA} {p.goles_favor}-{p.goles_contra} {p.rival}" if p.sede == "Casa" \
        else f"J{p.jornada}: {p.rival} {p.goles_contra}-{p.goles_favor} {ZARAGOZA}"
    (CARPETA_PAGINAS / f"jornada-{p.jornada}.html").write_text(
        pagina(titulo, f"Ficha de la jornada {p.jornada} del Real Zaragoza 2026/27 ante {p.rival}.", cuerpo),
        encoding="utf-8")


# ---------------------------------------------------------------------------
# Pestaña «Último partido»
# ---------------------------------------------------------------------------
# No quiero que sea una copia de la ficha de la jornada (esa ya existe en
# «Jornada a jornada»). Aquí cuento el partido como una crónica corta:
# qué pasó, cómo llega el equipo, en qué se salió de lo normal comparado con
# el resto de la temporada y qué viene después. Para el detalle completo
# (alineación, todas las estadísticas, vídeo) hay un botón a la ficha.

PUNTOS = {"victoria": 3, "empate": 1, "derrota": 0}


def goles_ordenados(p, goles):
    """Goles del partido en orden cronológico, con el marcador que deja cada uno
    (siempre Zaragoza-rival) y el minuto en número para poder dibujarlos."""
    g = goles[goles["partido_id"] == p.partido_id].sort_values(["parte", "minuto", "anadido"]).copy()
    a_favor = en_contra = 0
    filas = []
    for x in g.itertuples():
        if x.sentido == "Favor":
            a_favor += 1
        else:
            en_contra += 1
        # El descuento lo sumo como décimas con tope de 9, igual que en goles_video.py,
        # para que un 45+7 quede antes que un 46
        minuto_num = x.minuto + min(int(x.anadido), 9) / 10
        texto = f"{x.minuto}+{int(x.anadido)}" if x.anadido else str(x.minuto)
        filas.append({"sentido": x.sentido, "jugador": x.jugador, "minuto": texto, "minuto_num": minuto_num,
                      "penalti": x.penalti == "si", "propia": x.propia_puerta == "si",
                      "marcador": f"{a_favor}-{en_contra}"})
    return filas


def cronica(p, goles_partido, sofa):
    """Tres o cuatro frases que resumen el partido, escritas a partir de los datos.

    No es un texto «inteligente»: son reglas sencillas (¿remontó?, ¿marcó al
    final?, ¿mereció más según el xG?) que convierten los números en frases.
    Así la crónica se escribe sola cada jornada y nunca dice nada que no esté
    en los datos.
    """
    texto, clase = resultado(p)
    donde = "en casa ante el" if p.sede == "Casa" else "en el campo del"
    frases = [f"{texto} {p.goles_favor}-{p.goles_contra} {donde} {e(p.rival)}."]

    # ¿Fue por detrás en algún momento? Miro el peor marcador que tuvo durante el partido
    peor = max((int(g["marcador"].split("-")[1]) - int(g["marcador"].split("-")[0]) for g in goles_partido), default=0)
    if peor >= 2 and clase != "derrota":
        frases.append(f"Llegó a ir {peor} goles por detrás y aun así sacó {'los tres puntos' if clase == 'victoria' else 'un punto'}.")
    elif peor == 1 and clase == "victoria":
        frases.append("Remontó después de ir perdiendo.")

    # Goles en el tramo final (del 85 en adelante)
    finales = [g for g in goles_partido if g["minuto_num"] >= 85]
    favor_final = [g for g in finales if g["sentido"] == "Favor"]
    contra_final = [g for g in finales if g["sentido"] == "Contra"]
    if favor_final:
        quienes = ", ".join(sorted({g["jugador"] for g in favor_final}))
        frases.append(f"Marcó {len(favor_final)} {'gol' if len(favor_final) == 1 else 'goles'} a partir del minuto 85 ({e(quienes)}).")
    if contra_final:
        frases.append(f"Encajó {len(contra_final)} {'gol' if len(contra_final) == 1 else 'goles'} en ese mismo tramo final.")

    # Goleadores del Zaragoza (sin contar los goles en propia puerta del rival)
    goleadores = {}
    for g in goles_partido:
        if g["sentido"] == "Favor" and not g["propia"]:
            goleadores[g["jugador"]] = goleadores.get(g["jugador"], 0) + 1
    if goleadores:
        partes = [f"{e(j)}{f' ({n})' if n > 1 else ''}" for j, n in goleadores.items()]
        frases.append(f"Goles del Zaragoza: {', '.join(partes)}.")

    # Lo que dice el xG
    xg = sofa.get(p.partido_id, {}).get("xg")
    if xg:
        z, r = xg
        if z - r >= 1:
            juicio = "fue claramente mejor en ocasiones"
        elif r - z >= 1:
            juicio = "el rival generó bastante más peligro"
        else:
            juicio = "las ocasiones estuvieron bastante igualadas"
        frases.append(f"Según el xG de Sofascore ({numero(z, 2)} a {numero(r, 2)}), {juicio}.")
    return " ".join(frases)


def linea_goles_svg(goles_partido):
    """Línea de tiempo del partido: un eje de 0 a 95 minutos con un círculo por gol.

    Los del Zaragoza (azul y blanco) van por encima del eje y los del rival
    (naranja) por debajo. Si dos goles del mismo equipo caen a menos de seis
    minutos (por ejemplo, 90+9 y 90+12), el segundo se apila un escalón más
    lejos del eje para que no se tapen. El marcador que deja cada gol va a la
    derecha del círculo.

    En el móvil este dibujo queda demasiado pequeño, así que debajo genero
    también una lista sencilla (minuto, goleador y marcador) y con CSS enseño
    una cosa u otra según el ancho de la pantalla.
    """
    if not goles_partido:
        return ""
    eje, paso = 95, 30                                 # altura del eje y separación entre escalones
    x = lambda m: 30 + min(m, 95) / 95 * 900           # minuto -> posición horizontal
    marcas = "".join(f'<line x1="{x(m)}" x2="{x(m)}" y1="{eje - 5}" y2="{eje + 5}" class="marca"/>'
                     f'<text x="{x(m)}" y="{eje + 22}" text-anchor="middle">{m}\'</text>' for m in (0, 15, 30, 45, 60, 75, 90))
    puntos, ultimo = [], {"Favor": [], "Contra": []}
    for g in goles_partido:
        favor = g["sentido"] == "Favor"
        # Escalón: cuántos goles del mismo lado hay ya a menos de 6 minutos
        nivel = sum(1 for m in ultimo[g["sentido"]] if abs(m - g["minuto_num"]) < 6)
        ultimo[g["sentido"]].append(g["minuto_num"])
        cy = eje - 30 - nivel * paso if favor else eje + 45 + nivel * paso
        cx = x(g["minuto_num"])
        etiqueta = f'{g["minuto"]}\' {g["jugador"]}{" (pen.)" if g["penalti"] else ""}{" (p. p.)" if g["propia"] else ""} · {g["marcador"]}'
        puntos.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="11" class="{"favor" if favor else "contra"}">'
                      f'<title>{e(etiqueta)}</title></circle>'
                      f'<text x="{cx + 16:.1f}" y="{cy + 5}" class="marcador">{g["marcador"]}</text>')
    # Alto del dibujo según cuántos escalones hayan hecho falta
    niveles_arriba = max([sum(1 for m in ultimo["Favor"] if abs(m - n) < 6) for n in ultimo["Favor"]] + [1])
    niveles_abajo = max([sum(1 for m in ultimo["Contra"] if abs(m - n) < 6) for n in ultimo["Contra"]] + [1])
    alto_arriba = 30 + (niveles_arriba - 1) * paso + 22
    alto_abajo = 45 + (niveles_abajo - 1) * paso + 22
    svg = f"""<svg class="linea-goles" viewBox="0 {eje - alto_arriba} 1000 {alto_arriba + alto_abajo}" role="img" aria-label="Goles del partido minuto a minuto">
      <defs><linearGradient id="zgz-mitad"><stop offset="0" stop-color="#213e96"/><stop offset=".5" stop-color="#213e96"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff"/></linearGradient></defs>
      <line x1="30" x2="930" y1="{eje}" y2="{eje}" class="eje"/>{marcas}{"".join(puntos)}
    </svg>"""
    lista = "".join(
        f'<li class="{"favor" if g["sentido"] == "Favor" else "contra"}"><span class="mp-min">{g["minuto"]}\'</span>'
        f'{e(g["jugador"])}{" (pen.)" if g["penalti"] else ""}{" (p. p.)" if g["propia"] else ""}'
        f'<b>{g["marcador"]}</b></li>' for g in goles_partido)
    return svg + f'<ol class="goles-movil" aria-label="Goles del partido">{lista}</ol>'


def comparativa_temporada(p, sofa):
    """Tabla con las cifras del partido frente a la media de la temporada del Zaragoza.
    La media es de todos los partidos de liga que tengo en Sofascore, este incluido."""
    filas_metricas = [("xg", "xG a favor", 0, 2, False), ("xg", "xG en contra", 1, 2, False),
                      ("tiros", "Tiros", 0, 0, False), ("tiros_a_puerta", "Tiros a puerta", 0, 0, False),
                      ("tiros", "Tiros del rival", 1, 0, False), ("posesion_pct", "Posesión", 0, 0, True),
                      ("duelos_ganados_pct", "Duelos ganados", 0, 0, True)]
    este = sofa.get(p.partido_id)
    if not este:
        return ""
    filas = []
    for clave, nombre, lado, dec, pct in filas_metricas:
        if clave not in este:
            continue
        valores = [v[clave][lado] for v in sofa.values() if clave in v]
        media = sum(valores) / len(valores)
        valor = este[clave][lado]
        # Flecha según si está por encima o por debajo de la media (con un margen
        # del 5 % para no marcar como «diferente» lo que es prácticamente igual)
        if valor > media * 1.05:
            flecha = '<span class="sube">▲ por encima</span>'
        elif valor < media * 0.95:
            flecha = '<span class="baja">▼ por debajo</span>'
        else:
            flecha = '<span>≈ en la media</span>'
        filas.append(f"<tr><th scope=\"row\">{nombre}</th><td class=\"n\">{numero(valor, dec, pct)}</td>"
                     f"<td class=\"n\">{numero(media, dec if dec else 1, pct)}</td><td>{flecha}</td></tr>")
    return f"""<div class="tarjeta tabla" tabindex="0" role="region" aria-label="Comparación con la media de la temporada"><table>
      <thead><tr><th>Dato</th><th class="n">Este partido</th><th class="n">Media de la temporada</th><th></th></tr></thead>
      <tbody>{"".join(filas)}</tbody></table></div>"""


def situacion(p, d):
    """Puntos, posición antes y después y la racha de los últimos cinco partidos."""
    liga = d["liga"][d["liga"]["jornada"] <= p.jornada]
    puntos = sum(PUNTOS[resultado(x)[1]] for x in liga.itertuples())
    clasif = d["clasificacion"]

    def puesto(jornada):
        fila = clasif[(clasif["tras_jornada"] == jornada) & (clasif["equipo"] == ZARAGOZA)]
        return int(fila.iloc[0]["posicion"]) if len(fila) else None

    antes, ahora = puesto(p.jornada - 1), puesto(p.jornada)
    if ahora and antes:
        if ahora < antes:
            cambio = f"sube del {antes}.º al {ahora}.º"
        elif ahora > antes:
            cambio = f"baja del {antes}.º al {ahora}.º"
        else:
            cambio = f"se mantiene {ahora}.º"
    elif ahora:
        cambio = f"{ahora}.º"
    else:
        cambio = "sin clasificación apuntada"
    # Racha: los cinco últimos resultados, del más antiguo al más reciente
    letras = {"victoria": "V", "empate": "E", "derrota": "D"}
    racha = "".join(f'<span class="racha-{resultado(x)[1]}" title="J{x.jornada} · {e(x.rival)} {x.goles_favor}-{x.goles_contra}">{letras[resultado(x)[1]]}</span>'
                    for x in liga.tail(5).itertuples())
    return f"""<div class="kpis">
      <div class="kpi"><span>Puntos tras la jornada {p.jornada}</span><b>{puntos}</b></div>
      <div class="kpi"><span>Clasificación</span><b>{ahora}.º</b><small>{cambio}</small></div>
      <div class="kpi"><span>Últimos cinco partidos</span><div class="racha-ultimos">{racha}</div></div>
    </div>""" if ahora else ""


def pagina_ultimo(d, sofa):
    """Pestaña «Último partido»: crónica corta del partido más reciente, cómo deja al equipo,
    comparación con la temporada y el siguiente rival. El detalle está en la ficha de la jornada."""
    # itertuples() me da cada fila con sus columnas como atributos (p.rival, p.jornada…);
    # con iloc[[-1]] me quedo solo con la última fila
    p = next(d["liga"].iloc[[-1]].itertuples())
    goles_partido = goles_ordenados(p, d["goles"])
    titulo = f"Real Zaragoza {p.goles_favor}-{p.goles_contra} {p.rival}" if p.sede == "Casa" \
        else f"{p.rival} {p.goles_contra}-{p.goles_favor} Real Zaragoza"
    # En el h1 el resultado va en un <span> con white-space:nowrap, para que en el
    # móvil no quede «4-» en una línea y «4» en la siguiente
    gl, gv = (p.goles_favor, p.goles_contra) if p.sede == "Casa" else (p.goles_contra, p.goles_favor)
    local, visitante = (ZARAGOZA, p.rival) if p.sede == "Casa" else (p.rival, ZARAGOZA)
    titulo_html = f'{e(local)} <span class="sin-corte">{gl}-{gv}</span> {e(visitante)}'

    # Notas del vídeo, si ya he visto el partido: solo las de confianza media o alta
    notas = ""
    v = d["video"][d["video"]["partido_id"] == p.partido_id] if len(d["video"]) else d["video"]
    if len(v):
        items = "".join(f"<li><b>{e(x.minuto)}' · {e(x.goleador)}.</b> {e(x.nota)}</li>"
                        for x in v.itertuples() if x.confianza in ("alta", "media") and isinstance(x.nota, str))
        if items:
            notas = f"""
  <section class="seccion lectura" aria-labelledby="t-vistos">
    <p class="etiqueta">Visto en el resumen</p><h2 id="t-vistos">Cómo llegaron los goles</h2>
    <ul class="notas-goles">{items}</ul>
  </section>"""

    # Próximo partido
    siguiente_html = ""
    if len(d["proximos"]):
        s = d["proximos"].sort_values("fecha").iloc[0]
        cruce = f"Real Zaragoza – {e(s.rival)}" if s.sede == "Casa" else f"{e(s.rival)} – Real Zaragoza"
        siguiente_html = f"""
  <section class="seccion lectura" aria-labelledby="t-siguiente">
    <p class="etiqueta">Lo que viene</p><h2 id="t-siguiente">Próximo partido</h2>
    <p class="proximo">Jornada {int(s.jornada)} · <b>{cruce}</b> · {fecha_larga(pd.to_datetime(s.fecha))}</p>
    <div class="enlaces"><a class="boton lleno" href="previa.html">Leer la previa</a><a class="boton" href="jornada-{p.jornada}.html">Ficha completa de la jornada {p.jornada}</a><a class="boton" href="jornadas.html">Todas las jornadas</a></div>
  </section>"""

    cuerpo = f"""<main class="envoltorio">
  <p class="migas"><a href="../index.html">Proyectos</a> / <a href="index.html">Real Zaragoza 2026/27</a> / Último partido</p>
  {pestanas("ultimo")}
  <section class="seccion primera" aria-labelledby="t-ultimo">
    <p class="etiqueta">Último partido · Jornada {p.jornada} · {fecha_larga(p.fecha)}</p>
    <h1 id="t-ultimo">{titulo_html}</h1>
    <p class="entradilla">{cronica(p, goles_partido, sofa)}</p>
    {bloque_marcador(p)}
    {linea_goles_svg(goles_partido)}
    <p class="leyenda"><span><i class="zgz-mitad"></i>Gol del Zaragoza</span><span><i class="rival-naranja"></i>Gol del rival</span><span>El número es el marcador después de cada gol</span></p>
  </section>

  <section class="seccion" aria-labelledby="t-situacion">
    <p class="etiqueta">Cómo queda el equipo</p><h2 id="t-situacion">Después de la jornada {p.jornada}</h2>
    {situacion(p, d)}
  </section>

  <section class="seccion" aria-labelledby="t-comparativa">
    <p class="etiqueta">¿Fue un partido normal?</p><h2 id="t-comparativa">Frente a la media de la temporada</h2>
    <p class="nota">Cifras del Zaragoza en este partido comparadas con su media en liga (datos de Sofascore).</p>
    {comparativa_temporada(p, sofa)}
  </section>
  {notas}
  {siguiente_html}
</main>"""
    (CARPETA_PAGINAS / "ultimo-partido.html").write_text(
        pagina(f"Último partido del Real Zaragoza: {titulo}",
               f"Crónica con datos del último partido del Real Zaragoza: {titulo}.", cuerpo),
        encoding="utf-8")


def main():
    d = cargar()
    sofa = sofascore_por_partido(d["sofascore"]) if len(d["sofascore"]) else {}
    pagina_jornadas(d, sofa)
    for p in d["liga"].itertuples():
        pagina_partido(p, d, sofa)
    pagina_ultimo(d, sofa)
    print(f"Páginas de partido: {len(d['liga'])} + jornadas.html + ultimo-partido.html")


if __name__ == "__main__":
    main()
