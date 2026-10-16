"""
Página web del estudio: proyectos/espana-eurocopa-redes/index.html.

Lee los resultados de datos/salida, copia las gráficas a la web y escribe el
artículo. Las cifras salen de los archivos.

Uso, desde la carpeta del estudio y después de ejecutar.py:
    python codigo/web.py
"""
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ESTUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ESTUDIO.parent / "comun"))
from pagina import RAIZ_WEB, escribir_pagina, figura_foto, numero  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from visualizaciones import FASE, RIVAL, nombre_completo  # noqa: E402

CARPETA = "espana-eurocopa-redes"
CODIGO_GITHUB = f"https://github.com/lineadepase/lineadepase.github.io/tree/main/analisis/{CARPETA}"
LICENCIA = "https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf"


def copiar_recursos():
    destino = RAIZ_WEB / "proyectos" / CARPETA / "graficos"
    destino.mkdir(parents=True, exist_ok=True)
    for nombre in ("01_red_final_instagram", "05_seis_redes_web", "03_intermediacion_instagram",
                   "04_ritmo_concentracion_instagram"):
        shutil.copy(ESTUDIO / "graficos" / f"{nombre}.png", destino / f"{nombre}.png")
    shutil.copy(ESTUDIO / "graficos" / "05_seis_redes_facebook.png", destino / "compartir.png")
    shutil.copy(ESTUDIO / "recursos" / "statsbomb.png", destino / "statsbomb.png")
    shutil.copy(ESTUDIO / "recursos" / "foto.jpg", destino / "foto.jpg")
    shutil.copy(ESTUDIO / "datos" / "salida" / "jugadoras_torneo.csv", destino.parent / "jugadoras_torneo.csv")
    shutil.copy(ESTUDIO / "datos" / "salida" / "partidos.csv", destino.parent / "partidos.csv")


# La final terminó en empate y se decidió en la tanda de penaltis (Inglaterra ganó 3-1).
PENALTIS = {"Final": " (pen. 1-3)"}


def tabla_partidos(resumen):
    filas = "".join(
        f'<tr><th scope="row">{FASE[r.fase]}</th><td>{RIVAL[r.rival]}</td><td class="num">{r.resultado}{PENALTIS.get(r.fase, "")}</td>'
        f'<td class="num">{numero(r.minutos_red, 0)}</td><td class="num">{r.pases_red}</td>'
        f'<td class="num">{numero(r.pases_por_minuto, 1)}</td><td class="num">{numero(r.centralizacion, 2)}</td>'
        f'<td>{nombre_completo(r.jugadora_mas_central)}</td></tr>'
        for r in resumen.itertuples())
    return ('<div class="tabla-editorial" role="region" aria-label="Resumen por partido, tabla desplazable" tabindex="0">'
            '<table><caption>La red de España en cada partido, hasta su primer cambio</caption><thead><tr>'
            '<th scope="col">Fase</th><th scope="col">Rival</th><th scope="col" class="num">Resultado</th>'
            '<th scope="col" class="num">Minutos</th><th scope="col" class="num">Pases</th>'
            '<th scope="col" class="num">Pases/min</th><th scope="col" class="num">Concentración</th>'
            '<th scope="col">Más intermediación</th></tr></thead><tbody>' + filas + "</tbody></table></div>")


def main():
    resumen = pd.read_csv(ESTUDIO / "datos" / "salida" / "partidos.csv")
    torneo = pd.read_csv(ESTUDIO / "datos" / "salida" / "jugadoras_torneo.csv")
    habituales = torneo[torneo.redes >= 3].sort_values("intermediacion_media", ascending=False)
    cuatro = [nombre_completo(j) for j in habituales.jugadora.head(4)]
    final = resumen[resumen.fase == "Final"].iloc[0]
    semi = resumen[resumen.fase == "Semi-finals"].iloc[0]
    grupos = resumen[resumen.fase == "Group Stage"].pases_por_minuto
    eliminatorias = resumen[resumen.fase != "Group Stage"].pases_por_minuto
    repartida = resumen.loc[resumen.centralizacion.idxmin()]
    copiar_recursos()
    foto = json.loads((ESTUDIO / "recursos" / "foto.json").read_text(encoding="utf-8"))

    cuerpo = f"""  <section class="cab-proyecto">
    <p class="etiqueta">Investigación · Fútbol femenino · Eurocopa 2025</p>
    <h1>Por dónde pasaba el juego de España</h1>
    <p class="entradilla">Las redes de pases de los seis partidos de la selección en la Eurocopa femenina 2025 muestran quién unía el juego y cómo cambió la circulación de la fase de grupos a la final.</p>
    <dl class="ficha-tecnica">
      <div><dt>Pregunta</dt><dd>¿Quién conectaba el juego de España y cómo cambió durante el torneo?</dd></div>
      <div><dt>Datos</dt><dd>StatsBomb Open Data · 6 partidos · {resumen.pases_red.sum():,} pases completados en las redes</dd></div>
      <div><dt>Herramientas</dt><dd>Python (pandas, NetworkX, mplsoccer) · <a href="{CODIGO_GITHUB}">código y datos</a></dd></div>
    </dl>
  </section>

{figura_foto("graficos/foto.jpg", foto)}

  <nav class="accesos-seccion" aria-label="Secciones del artículo"><a href="#resultado">Resultados</a><a href="#partidos">Partido a partido</a><a href="#metodo">Cómo se calcula</a><a href="#fuentes">Fuentes y código</a></nav>

  <section class="seccion lectura" id="resultado">
    <p class="etiqueta">Resultados</p>
    <h2>El juego se ordenaba desde atrás</h2>
    <p>Una red de pases dibuja cada partido como un mapa de conexiones: un círculo por jugadora, en su posición media, y una línea más gruesa cuantos más pases se dan dos compañeras. La pregunta interesante no es quién toca más el balón, sino <strong>por quién pasan los caminos</strong> entre las demás. Eso mide la intermediación.</p>
    <p>Las cuatro jugadoras con más intermediación media fueron {cuatro[0]}, {cuatro[1]}, {cuatro[2]} y {cuatro[3]}: centrales y mediocentro. España ordenaba el juego desde atrás y dejaba a las atacantes para terminarlo.</p>
  </section>

  <figure class="figura"><img src="graficos/01_red_final_instagram.png" width="1080" height="1350" alt="Red de pases de España en la final ante Inglaterra hasta el primer cambio. {nombre_completo(final.jugadora_mas_central)}, en naranja, es la jugadora con más intermediación." style="max-width:min(560px,100%);margin-inline:auto"><figcaption>La final: {final.pases_red} pases completados hasta el minuto {numero(final.minuto_corte, 0)}, cuando España hizo su primer cambio.</figcaption></figure>

  <figure class="figura"><img loading="lazy" src="graficos/03_intermediacion_instagram.png" width="1080" height="1350" alt="Intermediación de cada jugadora en cada partido y su media del torneo. Destacan {cuatro[0]} y {cuatro[1]}." style="max-width:min(560px,100%);margin-inline:auto"><figcaption>Cada punto es un partido; la barra, la media del torneo. Solo jugadoras con tres redes o más.</figcaption></figure>

  <section class="seccion lectura" id="partidos">
    <p class="etiqueta">Partido a partido</p>
    <h2>Menos pases cuando subió el nivel</h2>
    <p>En la fase de grupos España completó entre {numero(grupos.min(), 1)} y {numero(grupos.max(), 1)} pases por minuto. En las eliminatorias bajó a entre {numero(eliminatorias.min(), 1)} y {numero(eliminatorias.max(), 1)}, ante rivales de más nivel y en partidos más cerrados. Con seis partidos no se puede separar qué parte se debe al rival y qué parte a la propia España.</p>
    <p>La red más repartida fue la de {FASE[repartida.fase].lower()} ante {RIVAL[repartida.rival]} (concentración {numero(repartida.centralizacion, 2)}). En la semifinal y la final el juego volvió a concentrarse más ({numero(semi.centralizacion, 2)} y {numero(final.centralizacion, 2)}).</p>
  </section>

  <figure class="figura"><img loading="lazy" src="graficos/05_seis_redes_web.png" width="1600" height="900" alt="Las seis redes de pases de España en la Eurocopa 2025, una por partido."><figcaption>Las seis redes, hasta el primer cambio de cada partido. En naranja, la jugadora con más intermediación.</figcaption></figure>

  {tabla_partidos(resumen)}

  <figure class="figura"><img loading="lazy" src="graficos/04_ritmo_concentracion_instagram.png" width="1080" height="1350" alt="Pases por minuto y concentración del juego en cada partido de España." style="max-width:min(560px,100%);margin-inline:auto"></figure>

  <section class="seccion lectura" id="metodo">
    <p class="etiqueta">Método</p>
    <h2>De los eventos a la red</h2>
    <p>En cada partido se cuentan los pases completados en juego de España, sin saques de banda, esquina, puerta, falta ni centro, y solo hasta su primer cambio: así las once jugadoras están en el campo todo el tramo y la red se puede comparar entre ellas. La posición de cada una es la media de los sitios donde dio y recibió pases.</p>
    <p>La intermediación cuenta qué parte de los caminos más cortos entre compañeras pasa por cada jugadora. Para que «más pases» signifique «más cerca», la distancia entre dos jugadoras es uno dividido por los pases que se dieron. La concentración del equipo es la centralización de Freeman sobre los pases dados y recibidos: 0 si todas están igual de conectadas y 1 si todo pasa por una.</p>
    <h2>Hasta dónde llega este análisis</h2>
    <ul>
      <li>Solo cuenta pases completados: ni conducciones ni pérdidas.</li>
      <li>El corte en el primer cambio deja fuera el final de cada partido: se analizan entre {numero(resumen.minutos_red.min(), 0)} y {numero(resumen.minutos_red.max(), 0)} minutos.</li>
      <li>La posición media mezcla las fases de ataque y de defensa.</li>
      <li>Seis partidos describen un torneo, no un estilo permanente.</li>
    </ul>
  </section>

  <section class="seccion lectura" id="fuentes">
    <p class="etiqueta">Trabajo verificable</p>
    <h2>Datos, código y comprobaciones</h2>
    <p>El programa comprueba en cada partido que no haya eventos duplicados ni coordenadas fuera del campo, que antes del primer cambio solo aparezcan titulares y que los pases de la red cuadren con la suma de las conexiones. Siete pruebas automáticas con partidos inventados verifican el corte, el grafo y las medidas.</p>
    <p><a class="boton" href="{CODIGO_GITHUB}">Ver el código y el cuaderno</a></p>
    <p>Descargar <a href="partidos.csv" download>el resumen por partido</a> y <a href="jugadoras_torneo.csv" download>las medias por jugadora</a> (CSV).</p>
    <p>Fuente: <a href="https://github.com/hudl/open-data">StatsBomb Open Data</a>, Eurocopa femenina 2025. Los eventos originales no se redistribuyen, como pide su <a href="{LICENCIA}">acuerdo de uso</a>.</p>
    <img class="logo-fuente" src="graficos/statsbomb.png" width="180" alt="StatsBomb, proveedor de los datos">
  </section>"""
    cuerpo = cuerpo.replace(f"{resumen.pases_red.sum():,}", numero(resumen.pases_red.sum(), 0))
    destino = escribir_pagina(
        CARPETA,
        "Por dónde pasaba el juego de España",
        "Redes de pases de la selección española en la Eurocopa femenina 2025: quién unía el juego y cómo cambió la circulación.",
        "Investigación",
        cuerpo,
        "Fuente: StatsBomb Open Data, Eurocopa femenina 2025. Redes de pases de elaboración propia.",
    )
    print(f"Página escrita en {destino.relative_to(RAIZ_WEB)}")


if __name__ == "__main__":
    main()
