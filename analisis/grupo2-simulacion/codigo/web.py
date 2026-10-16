"""
Página de la simulación dentro de la sección del Real Zaragoza:
proyectos/real-zaragoza/simulacion.html (cuelga de la pestaña «Grupo 2»).

Uso, desde la raíz del repositorio y después de ejecutar.py:
    python analisis/grupo2-simulacion/codigo/web.py
"""
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ESTUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ESTUDIO.parent / "comun"))
from pagina import RAIZ_WEB, escribir_pagina_zaragoza, figura_foto, numero  # noqa: E402

CODIGO_GITHUB = "https://github.com/lineadepase/lineadepase.github.io/tree/main/analisis/grupo2-simulacion"
EQUIPO = "Real Zaragoza"


def pct(valor):
    if 0 < valor < 0.005:
        return "<1 %"
    return f"{valor * 100:.0f} %"


def copiar_recursos():
    destino = RAIZ_WEB / "proyectos" / "real-zaragoza" / "graficos" / "simulacion"
    destino.mkdir(parents=True, exist_ok=True)
    for nombre in ("05_puesto_zaragoza_web", "04_veinte_equipos_web", "03_evolucion_zaragoza_instagram"):
        shutil.copy(ESTUDIO / "graficos" / f"{nombre}.png", destino / f"{nombre}.png")
    shutil.copy(ESTUDIO / "graficos" / "05_puesto_zaragoza_facebook.png", destino / "compartir.png")
    shutil.copy(ESTUDIO / "datos" / "salida" / "probabilidades.csv", destino / "probabilidades.csv")
    shutil.copy(ESTUDIO / "recursos" / "foto.jpg", destino / "foto.jpg")


def tabla_html(tabla):
    filas = []
    for i, r in enumerate(tabla.itertuples(), start=1):
        clase = ' class="destacada"' if r.equipo == EQUIPO else ""
        filas.append(f'<tr{clase}><td class="num">{i}</td><th scope="row">{r.equipo}</th>'
                     f'<td class="num">{numero(r.puntos_medios, 1)}</td><td class="num">{pct(r.ascenso_directo)}</td>'
                     f'<td class="num">{pct(r.playoff)}</td><td class="num">{pct(r.descenso)}</td></tr>')
    return ('<div class="tabla-editorial" role="region" aria-label="Probabilidades de los 20 equipos, tabla desplazable" tabindex="0">'
            '<table><caption>Probabilidades al final de la temporada</caption><thead><tr>'
            '<th scope="col" class="num">#</th><th scope="col">Equipo</th><th scope="col" class="num">Puntos medios</th>'
            '<th scope="col" class="num">Ascenso directo</th><th scope="col" class="num">Playoff</th>'
            '<th scope="col" class="num">Descenso</th></tr></thead><tbody>' + "".join(filas) + "</tbody></table></div>")


def main():
    salida = ESTUDIO / "datos" / "salida"
    tabla = pd.read_csv(salida / "probabilidades.csv")
    evolucion = pd.read_csv(salida / "evolucion_zaragoza.csv")
    distribucion = pd.read_csv(salida / "distribucion_puestos.csv", index_col=0)
    validacion = json.loads((ESTUDIO / "documentacion" / "validacion.json").read_text(encoding="utf-8"))
    jornada = validacion["tras_jornada"]
    z = tabla[tabla.equipo == EQUIPO].iloc[0]
    inicio = evolucion.iloc[0]
    favorito = z.ascenso_o_playoff >= tabla.ascenso_o_playoff.max()
    titular = "Favorito, pero lejos de estar decidido" if favorito else "Todo por decidir"
    frase = "Es el equipo con más opciones del grupo, pero" if favorito else "Aun así,"
    puesto_probable = int(distribucion.loc[EQUIPO].idxmax())
    p_puesto = distribucion.loc[EQUIPO].max()
    if validacion["penalizacion"] >= 16:
        lectura_penalizacion = "La respuesta fue acercarlas mucho: a estas alturas, los resultados dicen poco de la fuerza real de cada equipo."
    else:
        lectura_penalizacion = "Con las jornadas jugadas, los resultados ya permiten separar a los equipos con cierta confianza."
    copiar_recursos()
    foto = json.loads((ESTUDIO / "recursos" / "foto.json").read_text(encoding="utf-8"))

    cuerpo = f"""  <section class="cab-proyecto">
    <p class="etiqueta">Investigación · Simulación Monte Carlo</p>
    <h1>¿Y si el grupo 2 se jugara 10.000 veces?</h1>
    <p class="entradilla">Este estudio simula 10.000 veces el resto de la temporada de Primera Federación con un modelo de goles ajustado a los resultados. Tras la jornada {jornada}, el Real Zaragoza acaba entre los cinco primeros en el {pct(z.ascenso_o_playoff)} de las simulaciones.</p>
    <dl class="ficha-tecnica">
      <div><dt>Pregunta</dt><dd>¿Qué probabilidad tiene cada equipo de ascender, jugar el playoff o descender?</dd></div>
      <div><dt>Datos</dt><dd>Resultados de los {validacion['partidos_jugados']} partidos jugados · {validacion['partidos_pendientes']} partidos pendientes</dd></div>
      <div><dt>Herramientas</dt><dd>Python (pandas, NumPy, SciPy) · <a href="{CODIGO_GITHUB}">código y datos</a></dd></div>
    </dl>
  </section>

{figura_foto("graficos/simulacion/foto.jpg", foto)}

  <section class="seccion lectura">
    <p class="etiqueta">Resultados</p>
    <h2>{titular}</h2>
    <p>El Zaragoza termina primero en el <strong>{pct(z.ascenso_directo)}</strong> de las simulaciones y entre el segundo y el quinto en el <strong>{pct(z.playoff)}</strong>. {frase} en el {pct(1 - z.ascenso_o_playoff)} de las temporadas simuladas se queda fuera de los cinco primeros. El riesgo de descenso es del {pct(z.descenso)}.</p>
    <p>En 8 de cada 10 simulaciones acaba con entre {z.puntos_p10:.0f} y {z.puntos_p90:.0f} puntos. Quedan {38 - jornada} jornadas: la tabla de hoy cuenta, pero todavía queda casi toda la temporada.</p>
  </section>

  <figure class="figura"><img src="graficos/simulacion/05_puesto_zaragoza_web.png" width="1600" height="900" alt="Probabilidad de cada puesto final del Real Zaragoza. El más probable es el {puesto_probable}.º, con un {pct(p_puesto)}."><figcaption>Probabilidad de cada puesto final del Real Zaragoza.</figcaption></figure>

  <section class="seccion lectura">
    <h2>Cómo ha cambiado</h2>
    <p>Con los datos de la jornada {int(inicio.jornada)}, la probabilidad de acabar entre los cinco primeros era del {pct(inicio.ascenso_o_playoff)}. Los resultados desde entonces la han llevado al {pct(z.ascenso_o_playoff)}.</p>
  </section>

  <figure class="figura"><img loading="lazy" src="graficos/simulacion/03_evolucion_zaragoza_instagram.png" width="1080" height="1350" alt="Evolución jornada a jornada de la probabilidad del Real Zaragoza de ascender directamente y de acabar entre los cinco primeros." style="max-width:min(560px,100%);margin-inline:auto"></figure>

  <figure class="figura"><img loading="lazy" src="graficos/simulacion/04_veinte_equipos_web.png" width="1600" height="900" alt="Probabilidades de ascenso directo, playoff, zona media y descenso de los 20 equipos del grupo 2."><figcaption>Los 20 equipos, ordenados por los puntos medios al final de la temporada.</figcaption></figure>

  {tabla_html(tabla)}

  <section class="seccion lectura">
    <p class="etiqueta">Método</p>
    <h2>Un modelo de goles y 10.000 temporadas</h2>
    <p>Cada equipo tiene una fuerza de ataque y otra de defensa, y el local juega con ventaja. Los goles de cada equipo en un partido siguen una distribución de Poisson cuya media depende de su ataque, de la defensa del rival y de quién juega en casa. Es el modelo clásico de Maher, el punto de partida de casi todos los modelos de resultados.</p>
    <p>Con {jornada} jornadas cada equipo ha jugado {jornada} partidos, y una racha corta puede engañar. Por eso las fuerzas se acercan a la media del grupo salvo que los resultados lo justifiquen. Cuánto se acercan se decide con validación cruzada: el modelo se ajusta dejando fuera una jornada cada vez y se elige la opción que mejor predice la jornada que falta. {lectura_penalizacion}</p>
    <p>En cada simulación se sortean unas fuerzas dentro de su margen de incertidumbre, se juegan los {validacion['partidos_pendientes']} partidos pendientes y la tabla se ordena con el reglamento de la competición: puntos, puntos y diferencia de goles entre los empatados, diferencia general y goles a favor. Antes de simular, el programa comprueba que los resultados reproducen exactamente la clasificación publicada tras la jornada {jornada}; si no, se detiene.</p>
    <h2>Lo que la simulación no sabe</h2>
    <ul>
      <li>No sabe de lesiones, fichajes, sanciones ni cambios de entrenador.</li>
      <li>Supone que los goles de cada equipo en un partido son independientes; este tipo de modelo suele dar algo menos de empates de los que hay.</li>
      <li>El juego limpio y el partido de desempate no se pueden simular: si todo lo demás coincide, se sortea.</li>
      <li>Una probabilidad no es un pronóstico: un 20 % ocurre una de cada cinco veces.</li>
    </ul>
    <p>Se actualiza después de cada jornada.</p>
  </section>

  <section class="seccion lectura">
    <p class="etiqueta">Trabajo verificable</p>
    <h2>Datos, código y comprobaciones</h2>
    <p>Siete pruebas automáticas verifican el cálculo de la clasificación, los desempates a dos y a tres, las probabilidades de cada resultado y que el modelo distingue a un equipo fuerte en una liga inventada.</p>
    <p><a class="boton" href="{CODIGO_GITHUB}">Ver el código</a> · <a href="graficos/simulacion/probabilidades.csv" download>Descargar las probabilidades (CSV)</a></p>
    <p>Resultados: Sofascore, contrastados con la clasificación de BeSoccer tras cada jornada. Reglamento: <a href="https://rfef.es/sites/default/files/2026-06/2._CNL_Primera_Federacion_FINAL.pdf">normas de competición de Primera Federación 2026/27</a> (ascenso del primero, playoff del segundo al quinto y descenso del 16.º al 20.º).</p>
  </section>"""
    destino = escribir_pagina_zaragoza(
        "simulacion.html",
        f"Simulación del grupo 2 (J{jornada})",
        f"10.000 simulaciones del resto de la temporada del grupo 2 de Primera Federación: probabilidades de ascenso, playoff y descenso tras la jornada {jornada}.",
        '<a href="grupo-2.html">Primera Federación · Grupo 2</a> / Simulación',
        cuerpo,
        "",
    )
    print(f"Página escrita en {destino.relative_to(RAIZ_WEB)}")


if __name__ == "__main__":
    main()
