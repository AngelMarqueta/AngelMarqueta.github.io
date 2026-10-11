"""
Previa del próximo partido del Real Zaragoza.

Compara al Zaragoza con su próximo rival a partir de los resultados de los
dos equipos: clasificación, últimos partidos, rendimiento en casa y fuera y
rivales comunes. Los resultados del rival están en
datos/entrada/partidos_rivales.csv (los copio de futbolme y BeSoccer).

Uso (desde la raíz del repositorio), indicando la jornada:
    python analisis/real-zaragoza/codigo/previa.py 8

Escribe proyectos/real-zaragoza/previa.html. Cada semana se sobrescribe con
el siguiente rival.
"""

import sys
from html import escape

import pandas as pd

import calculos
from cargar_datos import CARPETA_ENTRADA, RAIZ_WEB, cargar_todo
from informe import fecha_larga, tabla_html

ZARAGOZA = "Real Zaragoza"


# ---------------------------------------------------------------------------
# Partidos del rival desde su punto de vista
# ---------------------------------------------------------------------------

def partidos_del_rival(rival):
    """Pasa los partidos del rival (local/visitante) a goles a favor y en contra."""
    todos = pd.read_csv(CARPETA_ENTRADA / "partidos_rivales.csv", parse_dates=["fecha"])
    p = todos[todos["equipo"] == rival].copy()
    if p.empty:
        raise SystemExit(f"No hay partidos de {rival} en partidos_rivales.csv")

    en_casa = p["local"] == rival
    p["sede"] = en_casa.map({True: "Casa", False: "Fuera"})
    p["rival"] = p["visitante"].where(en_casa, p["local"])
    p["goles_favor"] = p["goles_local"].where(en_casa, p["goles_visitante"])
    p["goles_contra"] = p["goles_visitante"].where(en_casa, p["goles_local"])
    # Reutilizo la misma función que para el Zaragoza (puntos, resultado...)
    p["competicion"] = "Primera Federación"
    p["partido_id"] = p["jornada"]
    return calculos.preparar_partidos(p.sort_values("jornada"))


# ---------------------------------------------------------------------------
# Piezas de la página
# ---------------------------------------------------------------------------

def racha(partidos, ultimos=5):
    """Últimos resultados como fichas V / E / D, del más antiguo al más reciente."""
    letras = {"Victoria": ("V", "victoria"), "Empate": ("E", "empate"), "Derrota": ("D", "derrota")}
    fichas = []
    for p in partidos.tail(ultimos).itertuples():
        letra, clase = letras[p.resultado]
        titulo = f"J{p.jornada} · {p.sede.lower()} · {p.rival} {p.goles_favor}-{p.goles_contra}"
        fichas.append(f'<span class="ficha-resultado {clase}" title="{escape(titulo)}">{letra}</span>')
    return f'<div class="racha">{"".join(fichas)}</div>'


def resumen_sede(partidos, sede):
    """Puntos y goles en casa o fuera, en una frase."""
    p = partidos[partidos["sede"] == sede]
    if p.empty:
        return "sin partidos todavía"
    return (f"{int(p['puntos'].sum())} puntos de {3 * len(p)} en {len(p)} partidos "
            f"({int(p['goles_favor'].sum())}-{int(p['goles_contra'].sum())} en goles)")


def rivales_comunes(zaragoza, rival):
    """Partidos de los dos equipos contra el mismo rival."""
    filas = []
    for p in zaragoza.itertuples():
        mismo = rival[rival["rival"] == p.rival]
        for q in mismo.itertuples():
            filas.append({
                "rival": p.rival,
                "zaragoza": f"{p.goles_favor}-{p.goles_contra} ({p.sede.lower()})",
                "otro": f"{q.goles_favor}-{q.goles_contra} ({q.sede.lower()})",
            })
    return pd.DataFrame(filas)


def claves(nombre_rival, sede_zgz, zaragoza, rival, clasificacion):
    """Frases con los datos más llamativos. Solo cifras, sin pronósticos."""
    fila_z = clasificacion[clasificacion["equipo"] == ZARAGOZA].iloc[0]
    fila_r = clasificacion[clasificacion["equipo"] == nombre_rival].iloc[0]
    sede_rival = "Casa" if sede_zgz == "Fuera" else "Fuera"
    donde = "en casa" if sede_rival == "Casa" else "fuera"

    frases = [
        f"El Zaragoza es {fila_z.posicion}.º con {fila_z.puntos} puntos y el {escape(nombre_rival)} "
        f"{fila_r.posicion}.º con {fila_r.puntos}: {abs(fila_z.puntos - fila_r.puntos)} puntos de diferencia.",
        f"El {escape(nombre_rival)} juega {donde}, donde lleva {resumen_sede(rival, sede_rival)}.",
        f"El Zaragoza, {('fuera' if sede_zgz == 'Fuera' else 'en casa')}, lleva "
        f"{resumen_sede(zaragoza, sede_zgz)}.",
    ]
    goleada = rival.loc[(rival["goles_contra"] - rival["goles_favor"]).idxmax()]
    if goleada["goles_contra"] - goleada["goles_favor"] >= 3:
        frases.append(f"Su peor resultado: {goleada['goles_favor']}-{goleada['goles_contra']} "
                      f"ante el {escape(goleada['rival'])} en la jornada {goleada['jornada']}.")
    return "".join(f"<li>{f}</li>" for f in frases)


# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------

def generar(jornada):
    datos = cargar_todo()
    proximo = datos["proximos"][datos["proximos"]["jornada"] == jornada]
    if proximo.empty:
        raise SystemExit(f"La jornada {jornada} no está en proximos.csv")
    proximo = proximo.iloc[0]
    nombre_rival = proximo["rival"]

    zaragoza = calculos.solo_liga(calculos.preparar_partidos(datos["partidos"]))
    rival = partidos_del_rival(nombre_rival)
    clasificacion = calculos.preparar_clasificacion(datos["clasificacion"])

    comunes = rivales_comunes(zaragoza, rival)
    tabla_comunes = (tabla_html(comunes, {"rival": "Rival", "zaragoza": "Real Zaragoza", "otro": nombre_rival})
                     if not comunes.empty else "<p>Todavía no tienen rivales en común.</p>")

    entorno = clasificacion[clasificacion["equipo"].isin([ZARAGOZA, nombre_rival])]
    tabla_clasificacion = tabla_html(
        entorno, {"posicion": "#", "equipo": "Equipo", "pj": "PJ", "g": "G", "e": "E", "p": "P",
                  "gf": "GF", "gc": "GC", "puntos": "Pts"},
        numericas=("posicion", "pj", "g", "e", "p", "gf", "gc", "puntos"),
        resaltar=lambda f: f["equipo"] == ZARAGOZA)

    local, visitante = ((ZARAGOZA, nombre_rival) if proximo["sede"] == "Casa"
                        else (nombre_rival, ZARAGOZA))
    fuentes = sorted(set(rival["fuente_url"]))

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Previa: {escape(local)} – {escape(visitante)} · Línea de pase</title>
<meta name="description" content="Previa con datos del {escape(local)} – {escape(visitante)}, jornada {jornada} de Primera Federación.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Big+Shoulders+Display:wght@700;800&display=swap">
<link rel="stylesheet" href="../../assets/estilo.css">
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
      <a href="../../index.html#proyectos">Proyectos</a>
      <a href="../../index.html#sobre-mi">Sobre mí</a>
      <a href="https://www.linkedin.com/in/angel-marqueta-alonso-a8831164" rel="noopener" target="_blank">LinkedIn</a>
      <a href="https://github.com/AngelMarqueta" rel="noopener" target="_blank">GitHub</a>
    </nav>
  </div>
</header>

<main class="envoltorio">
  <p class="migas"><a href="../../index.html#proyectos">Proyectos</a> / <a href="index.html">Real Zaragoza 2026/27</a> / Previa</p>
  <section class="cab-proyecto">
    <p class="etiqueta">Previa · Jornada {jornada} · {fecha_larga(proximo['fecha'])}</p>
    <h1>{escape(local)} – {escape(visitante)}</h1>
    <p class="entradilla">Lo que dicen los resultados de los dos equipos antes del partido. Son datos de pocas jornadas: sirven para situarse, no para adivinar el resultado.</p>
  </section>

  <section class="seccion lectura">
    <p class="etiqueta">Claves</p>
    <h2>Los datos del partido</h2>
    <ul class="claves">{claves(nombre_rival, proximo['sede'], zaragoza, rival, clasificacion)}</ul>
  </section>

  <section class="seccion graficos" aria-label="Forma y clasificación">
    <div>
      <p class="etiqueta">Forma</p>
      <h2>Últimos cinco partidos</h2>
      <div class="tarjeta">
        <h3>Real Zaragoza</h3>{racha(zaragoza)}
        <h3>{escape(nombre_rival)}</h3>{racha(rival)}
        <p class="nota">Del más antiguo al más reciente. Pasa el ratón por encima para ver el resultado.</p>
      </div>
    </div>
    <div>
      <p class="etiqueta">Clasificación</p>
      <h2>Tras la jornada {clasificacion['tras_jornada'].iloc[0]}</h2>
      {tabla_clasificacion}
    </div>
  </section>

  <section class="seccion">
    <p class="etiqueta">Rivales comunes</p>
    <h2>Contra los mismos equipos</h2>
    {tabla_comunes}
    <p class="nota">Cada equipo desde su punto de vista: primero sus goles y luego los del rival.</p>
  </section>

  <section class="seccion lectura">
    <p class="etiqueta">Fuentes</p>
    <p>Resultados del {escape(nombre_rival)}: {", ".join(f'<a href="{escape(u)}" rel="noopener" target="_blank">futbolme</a>' for u in fuentes)}, contrastados con BeSoccer. Datos del Zaragoza: los mismos del <a href="informe-completo.html">informe completo</a>.</p>
    <div class="enlaces"><a class="boton" href="index.html">Volver al panel</a></div>
  </section>
</main>

<footer class="pie">
  <div class="envoltorio">
    <p>Análisis personal con datos públicos. Línea de pase no tiene relación con el Real Zaragoza ni con ningún otro club o competición.</p>
    <p>© {proximo['fecha'].year} Ángel G. Marqueta Alonso</p>
  </div>
</footer>
</body>
</html>
"""
    ruta = RAIZ_WEB / "proyectos" / "real-zaragoza" / "previa.html"
    ruta.write_text(html, encoding="utf-8")
    print(f"Previa generada: {local} – {visitante} (jornada {jornada}).")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        raise SystemExit("Uso: python previa.py <jornada>")
    generar(int(sys.argv[1]))
