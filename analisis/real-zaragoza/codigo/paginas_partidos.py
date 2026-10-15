"""
Páginas de cada partido del Real Zaragoza y pestañas del seguimiento.

Uso (desde la raíz del repositorio):
    python analisis/real-zaragoza/codigo/paginas_partidos.py

También se ejecuta solo al final de actualizar.py, así que después de cada
jornada no hay que acordarse de nada.

Qué genera dentro de proyectos/real-zaragoza/:
    - jornadas.html        La pestaña «Jornada a jornada»: una tarjeta por partido.
    - jornada-N.html       Una página por partido de liga (N = número de jornada).
    - ultimo-partido.html  La pestaña «Último partido»: la misma ficha que el último
                           partido jugado, con el próximo rival al final.

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
         ("partidos", "goles", "alineaciones", "cambios", "tarjetas", "tiros", "proximos", "sofascore")}
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
               ("ultimo", "ultimo-partido.html", "Último partido")]
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
      <p class="leyenda"><span><i class="zgz-mitad"></i>Gol del Zaragoza</span><span><i style="background:var(--senal)"></i>Gol del rival</span><span>Posición estimada a ojo; cada equipo ataca hacia la derecha</span></p>"""
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


def pagina_ultimo(d, sofa):
    """Pestaña «Último partido»: la ficha del último partido de liga, más el siguiente rival."""
    # itertuples() me da cada fila con sus columnas como atributos (p.rival, p.jornada…),
    # igual que en el resto del archivo; con iloc[[-1]] me quedo solo con la última fila.
    p = next(d["liga"].iloc[[-1]].itertuples())
    cuerpo = ficha(p, d, sofa, "ultimo", titulo_extra=f"Último partido · Jornada {p.jornada}")
    # Añado el próximo partido justo antes de cerrar el <main>
    proximos = d["proximos"].copy()
    if len(proximos):
        siguiente = proximos.sort_values("fecha").iloc[0]
        fecha = pd.to_datetime(siguiente.fecha)
        bloque = f"""  <section class="seccion lectura" aria-labelledby="t-siguiente">
    <p class="etiqueta">Lo que viene</p><h2 id="t-siguiente">Próximo partido</h2>
    <p>Jornada {int(siguiente.jornada)}: {"Real Zaragoza – " + e(siguiente.rival) if siguiente.sede == "Casa" else e(siguiente.rival) + " – Real Zaragoza"}, {fecha_larga(fecha)}.</p>
    <div class="enlaces"><a class="boton lleno" href="previa.html">Ver la previa</a></div>
  </section>
</main>"""
        cuerpo = cuerpo.replace("</main>", bloque)
    (CARPETA_PAGINAS / "ultimo-partido.html").write_text(
        pagina(f"Último partido del Real Zaragoza: J{p.jornada} ante {p.rival}",
               "La ficha completa del último partido de liga del Real Zaragoza 2026/27.", cuerpo),
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
