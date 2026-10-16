"""Presentación común del seguimiento; conserva las guías al regenerar las páginas."""
from pathlib import Path
import re, json
TEXTOS=Path(__file__).resolve().parent.parent/'textos'
def navegacion(activa):
    if activa=='ultimo': activa='jornadas'
    enlaces=[('temporada','index.html','Resumen'),('previa','previa.html','Previa'),('evolucion','evolucion.html','Evolución'),('plantilla','plantilla.html','Plantilla'),('jornadas','jornadas.html','Jornadas'),('grupo','grupo-2.html','Primera Federación · Grupo 2')]
    return '<nav class="pestanas" aria-label="Secciones del seguimiento">'+''.join('<a href="'+url+'"'+(' aria-current="page"' if clave==activa else '')+'>'+label+'</a>' for clave,url,label in enlaces)+'</nav>'
def enriquecer(html, nombre='', jornada=None):
    activa={'index.html':'temporada','previa.html':'previa','evolucion.html':'evolucion','plantilla.html':'plantilla','grupo-2.html':'grupo','jornadas.html':'jornadas','ultimo-partido.html':'jornadas'}.get(nombre,'jornadas' if nombre.startswith('jornada-') else '')
    if not nombre:
        actual=re.search(r'<a href="([^"]+)" aria-current="page">',html[html.find('<nav class="pestanas"'):])
        if actual: activa={'index.html':'temporada','previa.html':'previa','evolucion.html':'evolucion','plantilla.html':'plantilla','jornadas.html':'jornadas','grupo-2.html':'grupo'}.get(actual[1],activa)
    menu=navegacion(activa)
    if '<nav class="pestanas"' in html: html=re.sub(r'<nav class="pestanas"[\s\S]*?</nav>',lambda m:menu,html,count=1)
    else: html=re.sub(r'(<p class="migas">[\s\S]*?</p>)',lambda m:m[0]+menu,html,count=1)
    html=html.replace('real-zaragoza.css?v=20261016a','real-zaragoza.css?v=20261016b')
    if 'data-guia="lectura"' not in html:
        guias=json.loads((TEXTOS/'guias_graficos.json').read_text(encoding='utf-8'))
        def explicar(m):
            figure=m[0]; src=re.search(r'src="([^"]+)"',figure)
            guia=guias.get(src[1].split('/')[-1]) if src else None
            if not guia:return figure
            title,desc=guia
            return '<div class="guia-grafico" data-guia="lectura"><h3>'+title+'</h3>'+figure+'<p>'+desc+'</p></div>'
        html=re.sub(r'<figure class="figura">[\s\S]*?</figure>',explicar,html)
    if 'graficos/grupo2/' in html and 'data-grupo-organizado' not in html:
        html=html.replace('/ Grupo 2</p>','/ Primera Federación · Grupo 2</p>').replace('El grupo 2, con datos','Primera Federación · Grupo 2')
        html=html.replace('Sirve para poner al Real Zaragoza en contexto: no solo cuántos puntos lleva, sino si los merece.','Lo uso para comparar resultados y ocasiones, y entender mejor a los rivales del Zaragoza.')
        # La explicación larga y las tablas son opcionales. Las gráficas se agrupan por pregunta.
        html=re.sub(r'(<h2 id="t-lectura">Lectura del grupo</h2>)([\s\S]*?)(</section>)',lambda m:m[1]+'<p>Empiezo por tres preguntas: quién genera más peligro, cómo se relaciona con los resultados y qué peso tiene la posesión. Elige el bloque que te interese.</p><details class="desplegable"><summary>Leer mi análisis de los equipos</summary>'+m[2]+'</details>'+m[3],html,count=1)
        html=re.sub(r'(<h2 id="t-tabla">La tabla, con xG</h2>)([\s\S]*?)(</section>)',lambda m:m[1]+'<details class="desplegable"><summary>Abrir la clasificación y comparar las cifras de los 20 equipos</summary>'+m[2]+'</details>'+m[3],html,count=1)
        pattern=r'(<h2 id="t-graficos">El grupo, en seis gráficos</h2>)([\s\S]*?)(</section>)'
        def grupos(m):
            figures=re.findall(r'<div class="guia-grafico" data-guia="lectura">[\s\S]*?</div>',m[2])
            byname={re.search(r'src="[^"]*/([^/"]+)"',f)[1]:f for f in figures}
            sets=[('Ocasiones: quién genera y quién concede',['dominio.png','evolucion_xg.png']),('Resultados: puntos y acierto',['puntos_esperados.png','eficacia.png']),('Con balón: posesión, volumen y calidad',['tiros_calidad.png','posesion_peligro.png'])]
            out=m[1]+'<div data-grupo-organizado="true"><p>No hace falta verlos todos de golpe. Abre cada bloque para leer las dos gráficas y mi explicación.</p>'
            for i,(title,files) in enumerate(sets):out+='<details class="desplegable"'+(' open' if i==0 else '')+'><summary>'+title+'</summary>'+''.join(byname[n] for n in files)+'</details>'
            return out+'</div>'+m[3]
        html=re.sub(pattern,grupos,html,count=1)
        html=html.replace('Derecha: acierto del portero y la defensa.','Derecha: diferencia entre xG en contra y goles recibidos.')
    if nombre=='previa.html' and jornada is not None and 'id="mi-previa"' not in html:
        ruta=TEXTOS/f'previa_j{jornada}.json'
        if ruta.exists():
            extra=json.loads(ruta.read_text(encoding='utf-8'))
            html=re.sub(r'<p class="entradilla">.*?</p>',extra['fecha_html']+extra['entradilla'],html,count=1)
            html=html.replace('  <section class="seccion graficos"',extra['cuerpo']+'  <section class="seccion graficos"',1)
            html=html.replace('<p>Resultados del Real Murcia:',extra['fuentes']+'<p>Resultados del Real Murcia:',1)
    return html
