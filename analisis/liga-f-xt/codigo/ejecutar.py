"""Ejecuta la investigación sin escribir en la web ni en otros análisis."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd

from datos import COMMIT, descargar, obtener_temporada, preparar
from modelo import ajustar, puntuar, resumir, validacion_cruzada
from visualizaciones import crear_carrusel, crear_figuras

RAIZ = Path(__file__).resolve().parents[1]


def markdown_tabla(df, columnas):
    cabecera = '| ' + ' | '.join(columnas) + ' |\n| ' + ' | '.join(['---'] * len(columnas)) + ' |\n'
    return cabecera + '\n'.join('| ' + ' | '.join(f'{v:.3f}' if isinstance(v, float) else str(v) for v in fila) + ' |' for fila in df[columnas].itertuples(index=False, name=None))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=RAIZ / 'datos/privados')
    args = parser.parse_args()
    salida = RAIZ / 'datos/salida'
    doc = RAIZ / 'documentacion'
    for carpeta in (salida, doc, RAIZ / 'recursos', RAIZ / 'publicaciones'):
        carpeta.mkdir(parents=True, exist_ok=True)
    print('Obteniendo 240 partidos, eventos y alineaciones...', flush=True)
    partidos, archivos, manifiesto = obtener_temporada(args.cache)
    acciones, minutos, auditoria = preparar(partidos, archivos)
    print(f'{len(acciones):,} acciones seleccionadas. Ajustando cinco pliegues...', flush=True)
    puntos, pliegues = validacion_cruzada(acciones)
    ranking, por_partido = resumir(puntos, minutos)
    modelo = ajustar(acciones)
    elegibles = ranking[ranking.elegible_900]
    assert len(elegibles) >= 50
    sensibilidades = []
    referencia = elegibles.set_index(['jugadora_id','equipo']).xt_neto_90
    for nx, ny in [(8,6),(16,12)]:
        alternativo, diag = validacion_cruzada(acciones, nx, ny)
        tabla, _ = resumir(alternativo, minutos, bootstrap=100)
        comparacion = tabla[tabla.elegible_900].set_index(['jugadora_id','equipo']).xt_neto_90
        comun = pd.concat([referencia.rename('base'),comparacion.rename('alternativa')],axis=1).dropna()
        sensibilidades.append({'comparacion': f'{nx}x{ny}', 'n':len(comun),
                               'spearman':float(comun['base'].rank().corr(comun.alternativa.rank())),
                               'top10_comunes':len(set(referencia.nlargest(10).index) & set(comparacion.nlargest(10).index)),
                               'max_celdas_vacias':max(d['celdas_vacias'] for d in diag)})
    # Comprobación temporal: entrenar con la primera mitad y valorar la segunda.
    orden = sorted(partidos, key=lambda p:(p['match_date'],p['kick_off'],p['match_id']))
    primeros = {p['match_id'] for p in orden[:120]}
    ultimos = {p['match_id'] for p in orden[120:]}
    temporal = ajustar(acciones[acciones.partido_id.isin(primeros)])
    pt = puntuar(acciones[acciones.partido_id.isin(ultimos)], temporal)
    mt = minutos[minutos.partido_id.isin(ultimos)]
    rt, _ = resumir(pt, mt, bootstrap=100)
    rc, _ = resumir(puntos[puntos.partido_id.isin(ultimos)], mt, bootstrap=100)
    juntas = rt[rt.minutos >=450].merge(rc[rc.minutos>=450],on=['jugadora_id','equipo'],suffixes=('_temporal','_cv'))
    sensibilidades.append({'comparacion':'entrenamiento primera mitad / evaluacion segunda mitad', 'n':len(juntas),
                           'spearman':float(juntas.xt_neto_90_temporal.rank().corr(juntas.xt_neto_90_cv.rank()))})
    # Efecto de penalizar pérdidas frente al criterio principal de acciones completadas.
    sensibilidades.append({'comparacion':'penalizacion de pases fallidos', 'n':len(elegibles),
                           'spearman':float(elegibles.xt_neto_90.rank().corr((90*elegibles.xt_con_perdidas/elegibles.minutos).rank()))})
    faltantes = puntos.merge(minutos[['partido_id','jugadora_id']],on=['partido_id','jugadora_id'],how='left',indicator=True)
    sin_minutos = faltantes[faltantes['_merge'].eq('left_only')]
    totales_equipo = minutos.groupby(['partido_id','equipo']).minutos.sum()
    assert totales_equipo.max() <= 990.01
    validacion = {'partidos':len(partidos),'equipos':16,'eventos':int(auditoria.eventos.sum()),
                  'acciones':len(acciones),'movimientos':len(puntos),'tiros':int(acciones.tipo.eq('Shot').sum()),
                  'goles_juego_abierto':int(acciones.gol.sum()),'eventos_duplicados':int(auditoria.duplicados.sum()),
                  'acciones_sin_coordenadas':int(auditoria.sin_coordenadas.sum()),
                  'coordenadas_invalidas':int(auditoria.coordenadas_invalidas.sum()),
                  'intervalos_posicion_invertidos':int(auditoria.intervalos_posicion_invertidos.sum()),
                  'jugadoras_equipo_elegibles':len(elegibles),'movimientos_sin_minutos_reglamentarios':len(sin_minutos),
                  'minutos_equipo_min':float(totales_equipo.min()),'minutos_equipo_max':float(totales_equipo.max()),
                  'pliegues':pliegues,'sensibilidad':sensibilidades,
                  'convergencia_modelo_completo':{k:modelo[k] for k in ('iteraciones','error','celdas_vacias')},
                  'python':platform.python_version(), 'dependencias':{n:importlib.metadata.version(n) for n in ('numpy','pandas','matplotlib','Pillow','nbformat','nbclient','ipykernel')}}
    ranking.to_csv(salida/'jugadoras_xt.csv', index=False)
    # Solo agregados por jugadora-equipo. No se distribuyen eventos, alineaciones
    # ni una tabla de acciones con coordenadas procedente del proveedor.
    auditoria.to_csv(salida/'cobertura_validacion.csv',index=False)
    pd.DataFrame(modelo['valor'].reshape(8,12)).to_csv(salida/'superficie_xt.csv',index=False)
    tipos = puntos.groupby('tipo').agg(acciones=('evento_id','size'),completadas=('exito','sum'),xt_neto=('xt_neto','sum'),xt_positivo=('xt_positivo','sum'))
    tipos.to_csv(salida/'resumen_tipos.csv')
    (doc/'validacion.json').write_text(json.dumps(validacion,ensure_ascii=False,indent=2),encoding='utf-8')
    logo, reg = descargar('img/SB%20-%20Icon%20Lockup%20-%20Colour%20positive.png', args.cache)
    manifiesto.append(reg)
    _, reg = descargar('LICENSE.pdf', args.cache)
    manifiesto.append(reg)
    (doc/'manifiesto_descargas.json').write_text(json.dumps({'commit':COMMIT,'archivos':manifiesto},ensure_ascii=False,indent=2),encoding='utf-8')
    ruta_logo = RAIZ/'recursos/statsbomb.png'
    ruta_logo.write_bytes(logo)
    crear_figuras(ranking,modelo,puntos,ruta_logo,RAIZ/'graficos')
    crear_carrusel(ranking,RAIZ/'graficos',RAIZ/'publicaciones/instagram')
    top = elegibles.head(10)
    lider = top.iloc[0]
    contexto_top = int(top.equipo.eq('Barcelona WFC').sum())
    informe = f'''# Crear peligro antes del tiro: Liga F 2023/24

Línea de pase · Investigación exploratoria · Ángel Marqueta Alonso

## Resultado principal

En esta especificación, **{lider.jugadora} ({lider.equipo})** encabeza el xT neto por 90 entre las {len(elegibles)} jugadoras-equipo con al menos 900 minutos: **{lider.xt_neto_90:.3f} xT/90**. Su intervalo bootstrap condicional es [{lider.ic95_inferior:.3f}, {lider.ic95_superior:.3f}]. No es una clasificación global de calidad ni de talento.

{markdown_tabla(top, ['jugadora','equipo','minutos','xt_neto','xt_neto_90','ic95_inferior','ic95_superior'])}

Hay {contexto_top} jugadoras del Barcelona entre las diez primeras: el contexto colectivo pesa y la tasa por 90 no lo elimina. La estabilidad frente a cambios de cuadrícula es alta (correlaciones de rangos de {sensibilidades[0]['spearman']:.3f} y {sensibilidades[1]['spearman']:.3f}), pero penalizar pérdidas cambia mucho la ordenación (correlación {sensibilidades[-1]['spearman']:.3f}). La conclusión defendible es sobre progresión completada en este contexto, no sobre eficiencia global o superioridad universal.

![Aportación de movimiento](../graficos/01_creadoras_xt_instagram.png)

## Datos y cobertura

Se descargaron los {len(partidos)} partidos (16 equipos, 30 partidos por equipo), sus eventos y alineaciones. El control cuenta {validacion['eventos']:,} eventos y selecciona {len(acciones):,} acciones de juego abierto: {validacion['tiros']:,} tiros y {len(puntos):,} pases/conducciones. Se observaron {validacion['goles_juego_abierto']} goles en los tiros seleccionados. Duplicados: {validacion['eventos_duplicados']}; coordenadas inválidas: {validacion['coordenadas_invalidas']}; acciones excluidas por ausencia de coordenadas: {validacion['acciones_sin_coordenadas']}.

Se filtra `play_pattern = Regular Play`, pases sin tipo de reinicio y tiros `Open Play`. Es una definición conservadora de juego abierto que excluye también fases clasificadas como originadas en un reinicio. Las unidades espaciales StatsBomb son 120 × 80; no se presentan como metros. Su orientación coloca a cada equipo atacando hacia x=120; no se vuelve a invertir por parte o localía.

## Modelo y criterio de comparación

Se divide el campo en 12 × 8 celdas. N(i) cuenta tiros y movimientos intentados desde la celda i. r(i)=goles(i)/N(i); Q(i,j)=movimientos completados de i a j/N(i). Se resuelve V=r+QV por iteración, con tolerancia 1e-10. Los pases fallidos tienen transición a un estado absorbente de valor cero. Es una variante empírica de xT inspirada en Karun Singh; usa goles observados, no xG del proveedor. No es el modelo oficial de StatsBomb ni VAEP.

La aportación principal de un movimiento completado es V(destino)−V(origen). Se conservan diferencias negativas y movimientos dentro de celda (valor cero). Los pases fallidos no suman en el criterio principal; el archivo de resultados incluye por separado el diagnóstico que resta V(origen) a esos fallos. Las conducciones se consideran completadas por construcción del evento; una pérdida posterior no se les atribuye automáticamente. No es una medida completa de riesgo, regate o pérdida.

Cada partido se puntúa con un modelo entrenado en los otros cuatro de cinco pliegues, con semilla fija. Son 192 partidos de ajuste y 48 de valoración por pliegue. La partición es aleatoria por partido: sirve para estimación retrospectiva y NO se presenta como predicción futura. El mapa ilustrativo sí se ajusta con toda la temporada y no produce el ranking.

## Minutos e incertidumbre

Se reconstruyen los minutos a partir del once inicial, sustituciones, expulsiones y salidas permanentes de los eventos, truncando el descuento a los límites de 45/90. Las salidas médicas temporales no descuentan tiempo de participación. Se detectaron {validacion['intervalos_posicion_invertidos']} intervalos posicionales con final anterior al inicio; por ello NO se usan los intervalos de posición como denominador. Las alineaciones proporcionan las identidades y los equipos. Se comprueba que ninguna jugadora supera 90 minutos ni equipo 990. No se mezclan equipos si una jugadora cambia de club. Hay {len(sin_minutos)} movimientos de jugadoras sin minutos reglamentarios positivos (por ejemplo, entradas en descuento); no se incluyen en las tasas por 90, pero sí en el ajuste espacial y el resumen de acciones. Los minutos de equipo van de {totales_equipo.min():.2f} a {totales_equipo.max():.2f}.

Los intervalos remuestrean 1.000 veces partidos de cada jugadora y recalculan el cociente de sumas de xT y minutos. Condicionan los modelos ya ajustados: no incorporan incertidumbre de entrenamiento, dependencia entre rivales, multiplicidad ni selección del top. El solapamiento no prueba igualdad y la ordenación no implica diferencias estadísticamente demostradas.

## Sensibilidad

```json
{json.dumps(sensibilidades,ensure_ascii=False,indent=2)}
```

Las correlaciones son de rangos de tasas, no medidas de acierto predictivo. La comprobación temporal usa los primeros 120 partidos para ajustar y los últimos 120 para valorar; compara esa valoración con el xT cruzado de esos mismos últimos partidos, para jugadoras con 450 minutos en ese tramo. No contrasta la probabilidad de gol con resultados futuros.

## Límites que cambian la interpretación

- El xT depende de celda, selección de acciones y muestra de goles; hay ruido y discontinuidades en los bordes. No se alisa ni interpola.
- No ajusta por rol, posesión, rival, marcador o fortaleza del equipo. No permite afirmar quién es mejor o quién está infravalorada económicamente.
- No observa carreras sin balón ni posiciones de todas las defensoras. No separa causalmente la habilidad de quien pasa, quien recibe y el contexto.
- El valor probabilístico pertenece al universo simplificado de acciones seleccionadas, no a una probabilidad calibrada de marcar en la siguiente posesión real.
- Se analiza 2023/24; no describe la forma actual de las jugadoras ni su club en 2026/27.

## Fuentes, permisos y reproducción

Datos: https://github.com/hudl/open-data · commit `{COMMIT}`. Manifiesto con fecha UTC, URL, tamaño y SHA-256 en `documentacion/manifiesto_descargas.json`. Acuerdo: https://github.com/hudl/open-data/blob/{COMMIT}/LICENSE.pdf (8 de septiembre de 2023). Permite divulgar análisis; restringe redistribuir los datos y la explotación comercial. Este paquete contiene resultados agregados y código, no los eventos ni las alineaciones originales. La descarga queda en caché privada. Las gráficas publicadas llevan el logotipo de StatsBomb, como pide el acuerdo.

Método: https://karun.in/blog/expected-threat.html y https://socceraction.readthedocs.io/en/latest/documentation/valuing_actions/xT.html. Implementación propia, sin copiar código de esas páginas.

No se utilizan fotografías: mapas, puntos e intervalos permiten explicar el resultado sin incorporar imágenes de derechos inciertos.
'''
    (doc/'informe.md').write_text(informe,encoding='utf-8')
    entorno = '\n'.join(f'{n}=={v}' for n,v in validacion['dependencias'].items())+'\n'
    (RAIZ/'requirements.txt').write_text(entorno,encoding='utf-8')
    print(top[['jugadora','equipo','xt_neto_90']].to_string(index=False),flush=True)
    print(json.dumps({k:v for k,v in validacion.items() if k not in ('pliegues',)},ensure_ascii=False,indent=2),flush=True)


if __name__ == '__main__':
    main()
