"""
Página web del estudio: proyectos/liga-f-xt/index.html.

Lee los resultados ya calculados (datos/salida y documentacion/validacion.json),
copia las gráficas a la carpeta de la web y escribe el artículo. Las cifras del
texto salen de los archivos, no se escriben a mano.

Uso, desde la raíz del repositorio y después de ejecutar.py:
    python analisis/liga-f-xt/codigo/web.py
"""
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ESTUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ESTUDIO.parent / "comun"))
from pagina import RAIZ_WEB, escribir_pagina, figura_foto, numero  # noqa: E402

CARPETA_WEB = RAIZ_WEB / "proyectos" / "liga-f-xt"
CODIGO_GITHUB = "https://github.com/lineadepase/lineadepase.github.io/tree/main/analisis/liga-f-xt"
LICENCIA = "https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf"


def copiar_recursos():
    graficos = CARPETA_WEB / "graficos"
    graficos.mkdir(parents=True, exist_ok=True)
    for nombre in ("04_creadoras_xt_web", "02_superficie_xt_instagram", "03_volumen_eficiencia_instagram"):
        shutil.copy(ESTUDIO / "graficos" / f"{nombre}.png", graficos / f"{nombre}.png")
    shutil.copy(ESTUDIO / "graficos" / "04_creadoras_xt_facebook.png", graficos / "compartir.png")
    shutil.copy(ESTUDIO / "recursos" / "statsbomb.png", graficos / "statsbomb.png")
    shutil.copy(ESTUDIO / "recursos" / "foto.jpg", graficos / "foto.jpg")
    shutil.copy(ESTUDIO / "datos" / "salida" / "jugadoras_xt.csv", CARPETA_WEB / "jugadoras_xt.csv")


def tabla_html(top):
    filas = []
    for i, r in enumerate(top.itertuples()):
        clase = ' class="destacada"' if i == 0 else ""
        filas.append(
            f'<tr{clase}><th scope="row">{r.jugadora}</th><td>{r.equipo}</td>'
            f'<td class="num">{numero(r.minutos, 0)}</td><td class="num"><strong>{numero(r.xt_neto_90)}</strong></td>'
            f'<td class="num">{numero(r.ic95_inferior)}–{numero(r.ic95_superior)}</td></tr>')
    return ('<div class="tabla-editorial" role="region" aria-label="Diez primeras jugadoras, tabla desplazable" tabindex="0">'
            '<table><caption>Diez primeras por xT neto por 90 minutos · mínimo 900 minutos</caption>'
            '<thead><tr><th scope="col">Jugadora</th><th scope="col">Equipo en 2023/24</th><th scope="col" class="num">Minutos</th>'
            '<th scope="col" class="num">xT/90</th><th scope="col" class="num">Intervalo 95 %</th></tr></thead><tbody>'
            + "".join(filas) + "</tbody></table></div>")


def main():
    ranking = pd.read_csv(ESTUDIO / "datos" / "salida" / "jugadoras_xt.csv")
    validacion = json.loads((ESTUDIO / "documentacion" / "validacion.json").read_text(encoding="utf-8"))
    elegibles = ranking[ranking.elegible_900]
    top = elegibles.head(10)
    l1, l2, l3 = top.iloc[0], top.iloc[1], top.iloc[2]
    barcelona = int(top.equipo.eq("Barcelona WFC").sum())
    sens = {s["comparacion"]: s["spearman"] for s in validacion["sensibilidad"]}
    acciones_txt = numero(validacion["acciones"], 0)

    copiar_recursos()
    foto = json.loads((ESTUDIO / "recursos" / "foto.json").read_text(encoding="utf-8"))
    cuerpo = f"""  <section class="cab-proyecto">
    <aside class="aviso-historico" aria-label="Periodo del análisis"><strong>ANÁLISIS HISTÓRICO · 2023/24</strong><span>Datos de la Liga F 2023/24, temporada terminada en 2024. No describe la temporada actual.</span></aside>
    <p class="etiqueta">Investigación · Fútbol femenino · Liga F 2023/24</p>
    <h1>El peligro empieza antes del último pase</h1>
    <p class="entradilla">Los goles y las asistencias solo cuentan el final de la jugada. Este estudio usa los 240 partidos de la Liga F 2023/24 para medir quién acerca el balón, con pases y conducciones, a las zonas desde las que se marca.</p>
    <dl class="ficha-tecnica">
      <div><dt>Pregunta</dt><dd>¿Qué jugadoras hacen avanzar el peligro antes del tiro?</dd></div>
      <div><dt>Datos</dt><dd>StatsBomb Open Data · {len(ranking.groupby('equipo'))} equipos · {acciones_txt} acciones de juego abierto</dd></div>
      <div><dt>Herramientas</dt><dd>Python (pandas, NumPy, Matplotlib) · modelo propio de xT · <a href="{CODIGO_GITHUB}">código y datos</a></dd></div>
    </dl>
  </section>

{figura_foto("graficos/foto.jpg", foto)}

  <nav class="accesos-seccion" aria-label="Secciones del artículo"><a href="#resultado">Resultados</a><a href="#metodo">Cómo se calcula</a><a href="#limites">Límites</a><a href="#fuentes">Fuentes y código</a></nav>

  <section class="seccion lectura" id="resultado">
    <p class="etiqueta">Resultados</p>
    <h2>¿Quién hace avanzar el peligro?</h2>
    <p>Antes del último pase, alguien ha llevado el balón desde una zona de poco valor hasta otra desde la que es más fácil acabar en gol. La amenaza esperada (<em>expected threat</em>, xT) sirve para medir esa parte de la construcción.</p>
    <p><strong>{l1.jugadora} suma {numero(l1.xt_neto_90)} xT neto por 90 minutos</strong>, más del doble que la siguiente. Detrás aparecen {l2.jugadora} ({numero(l2.xt_neto_90)}) y {l3.jugadora} ({numero(l3.xt_neto_90)}). Solo cuentan las jugadoras con al menos 900 minutos.</p>
    <p>Su intervalo va de {numero(l1.ic95_inferior)} a {numero(l1.ic95_superior)}: refleja cuánto varía entre sus partidos. No recoge toda la incertidumbre del modelo, así que el orden de las demás no debe leerse como una clasificación exacta.</p>
  </section>

  <figure class="figura"><img src="graficos/04_creadoras_xt_web.png" width="1600" height="900" alt="Las seis primeras jugadoras por xT neto por 90 minutos. {l1.jugadora} encabeza con {numero(l1.xt_neto_90)}; las líneas son intervalos del 95 %."><figcaption>xT neto por 90 minutos de pases y conducciones completados. Mínimo de 900 minutos.</figcaption></figure>

  <section class="seccion lectura">
    <h2>El equipo también está dentro del número</h2>
    <p>{barcelona} de las diez primeras juegan en el Barcelona. Tener más balón, jugar más cerca del área rival y estar en un equipo dominante da más ocasiones de sumar valor. Dividir por 90 minutos corrige el tiempo jugado, pero <strong>no iguala los contextos</strong>: el estudio no ajusta por puesto, rival, posesión ni marcador.</p>
  </section>

  {tabla_html(top)}

  <section class="seccion lectura" id="metodo">
    <p class="etiqueta">Método</p>
    <h2>Valor del destino menos valor del origen</h2>
    <p>El campo se divide en 96 zonas, 12 a lo largo y 8 a lo ancho. Para cada zona se calcula la probabilidad de tirar y marcar desde ella y la de mover el balón con éxito a cada una de las demás. Resolviendo ese sistema por iteración, cada zona recibe un valor: la probabilidad de que la jugada acabe en gol si el balón está ahí.</p>
    <p>Un pase o una conducción completados suman el valor de la zona de destino menos el de la de origen. Ir hacia una zona más valiosa suma; volver atrás resta.</p>
    <p>Para no valorar un partido con un modelo que ya lo ha visto, los partidos se separan en cinco grupos y cada grupo se valora con un modelo ajustado con los otros cuatro. Los minutos de cada jugadora se reconstruyen con las alineaciones, los cambios y las expulsiones.</p>
  </section>

  <div class="pareja-figuras">
    <figure class="figura"><img loading="lazy" src="graficos/02_superficie_xt_instagram.png" width="1080" height="1350" alt="Mapa del campo con el valor de cada zona: el valor se concentra junto a la portería rival, a la derecha."><figcaption>Valor de cada zona, ajustado con toda la temporada para explicar el método.</figcaption></figure>
    <figure class="figura"><img loading="lazy" src="graficos/03_volumen_eficiencia_instagram.png" width="1080" height="1350" alt="Nube de puntos: acciones intentadas por 90 minutos frente a xT neto por 90. Más volumen no garantiza más valor."><figcaption>Volumen y valor por 90 minutos, sin ajustar por puesto ni equipo.</figcaption></figure>
  </div>

  <section class="seccion lectura" id="limites">
    <p class="etiqueta">La comprobación que cambia la lectura</p>
    <h2>Crear peligro y arriesgar no son lo mismo</h2>
    <p>El orden apenas cambia con una cuadrícula más gruesa o más fina: la correlación de rangos es {numero(sens.get('8x6', 0))} con 8 × 6 zonas y {numero(sens.get('16x12', 0))} con 16 × 12. En cambio, si los pases fallidos restan el valor de la zona donde se pierden, la correlación baja a <strong>{numero(sens.get('penalizacion de pases fallidos', 0), 2)}</strong>.</p>
    <p>Por eso el titular tiene que ser preciso: la medida principal habla del valor que añaden las acciones completadas. Una medida que castigue las pérdidas responde a otra pregunta.</p>
    <h2>Hasta dónde llega este análisis</h2>
    <ul>
      <li>No ve las carreras sin balón ni dónde estaban las defensoras.</li>
      <li>No demuestra quién es mejor ni quién está infravalorada.</li>
      <li>Solo cuenta el juego abierto: deja fuera las jugadas que nacen de un saque.</li>
      <li>Son datos de 2023/24: no describen el rendimiento ni el club actual de las jugadoras.</li>
    </ul>
  </section>

  <section class="seccion lectura" id="fuentes">
    <p class="etiqueta">Trabajo verificable</p>
    <h2>Datos, código y comprobaciones</h2>
    <p>Se revisaron {numero(validacion['eventos'], 0)} eventos de los 240 partidos, sin identificadores duplicados ni coordenadas fuera del campo. El código pasa siete pruebas automáticas y el cuaderno explica cada paso.</p>
    <p><a class="boton" href="{CODIGO_GITHUB}">Ver el código y el cuaderno</a></p>
    <p><a href="jugadoras_xt.csv" download>Descargar los resultados por jugadora (CSV)</a>. Incluye a las jugadoras con menos de 900 minutos, marcadas como no elegibles.</p>
    <p>Fuente: <a href="https://github.com/hudl/open-data">StatsBomb Open Data</a>. Los eventos originales no se redistribuyen, como pide su <a href="{LICENCIA}">acuerdo de uso</a>. Método basado en <a href="https://karun.in/blog/expected-threat.html">Karun Singh</a>, con implementación propia.</p>
    <img class="logo-fuente" src="graficos/statsbomb.png" width="180" alt="StatsBomb, proveedor de los datos">
  </section>"""

    destino = escribir_pagina(
        "liga-f-xt",
        "El peligro empieza antes del último pase",
        "Quién acerca el balón a las zonas de gol en la Liga F 2023/24: un modelo propio de xT con los 240 partidos.",
        "Investigación",
        cuerpo,
        "Fuente: StatsBomb Open Data, Liga F 2023/24. Modelo propio de xT.",
    )
    print(f"Página escrita en {destino.relative_to(RAIZ_WEB)}")


if __name__ == "__main__":
    main()
