"""xT empírico: tiros, movimientos intentados y pérdida absorbente de valor cero.

No incorpora xG de StatsBomb ni información sobre el desenlace de la posesión
para puntuar un movimiento. Las conducciones no equivalen a regates ganados.
"""
import numpy as np
import pandas as pd


def celdas(x, y, nx=12, ny=8):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if not (np.isfinite(x).all() and np.isfinite(y).all() and
            ((x >= 0) & (x <= 120) & (y >= 0) & (y <= 80)).all()):
        raise ValueError('Coordenadas fuera del campo')
    return np.minimum((y / 80 * ny).astype(int), ny - 1) * nx + np.minimum((x / 120 * nx).astype(int), nx - 1)


def ajustar(acciones, nx=12, ny=8):
    n = nx * ny
    origen = celdas(acciones.x, acciones.y, nx, ny)
    total = np.bincount(origen, minlength=n).astype(float)
    tiros = acciones.tipo.eq('Shot').to_numpy()
    goles = np.bincount(origen[acciones.gol.to_numpy()], minlength=n).astype(float)
    movimientos = (~tiros) & acciones.exito.to_numpy()
    destino = celdas(acciones.fin_x, acciones.fin_y, nx, ny)
    transiciones = np.zeros((n, n))
    np.add.at(transiciones, (origen[movimientos], destino[movimientos]), 1)
    denominador = np.where(total > 0, total, 1)
    # Q ya incluye P(mover) y P(completar); los fallos no transfieren valor.
    q = transiciones / denominador[:, None]
    recompensa = goles / denominador
    valor = np.zeros(n)
    for iteracion in range(10000):
        nuevo = recompensa + q @ valor
        error = float(np.max(np.abs(nuevo - valor)))
        valor = nuevo
        if error < 1e-10:
            break
    else:
        raise ValueError('El modelo no converge')
    assert np.isfinite(valor).all() and valor.min() >= 0 and valor.max() <= 1 + 1e-9
    assert np.max(q.sum(axis=1)) <= 1 + 1e-9
    assert np.max(np.abs(valor - recompensa - q @ valor)) < 1e-9
    return {'valor': valor, 'q': q, 'total': total, 'nx': nx, 'ny': ny,
            'iteraciones': iteracion + 1, 'error': error, 'celdas_vacias': int((total == 0).sum())}


def puntuar(acciones, modelo):
    movimientos = acciones[acciones.tipo.ne('Shot')].copy()
    origen = celdas(movimientos.x, movimientos.y, modelo['nx'], modelo['ny'])
    destino = celdas(movimientos.fin_x, movimientos.fin_y, modelo['nx'], modelo['ny'])
    diferencia = modelo['valor'][destino] - modelo['valor'][origen]
    movimientos['xt_neto'] = np.where(movimientos.exito, diferencia, 0.0)
    movimientos['xt_positivo'] = movimientos.xt_neto.clip(lower=0)
    # Diagnóstico separado: resta V(origen) al pase fallido. No es VAEP.
    movimientos['xt_con_perdidas'] = np.where(movimientos.exito, diferencia, -modelo['valor'][origen])
    return movimientos


def validacion_cruzada(acciones, nx=12, ny=8):
    ids = np.sort(acciones.partido_id.unique())
    ids = np.random.default_rng(20261016).permutation(ids)
    pliegues = np.array_split(ids, 5)
    resultado, diagnosticos = [], []
    for numero, ids_prueba in enumerate(pliegues):
        prueba = acciones.partido_id.isin(ids_prueba)
        entrenamiento = acciones.loc[~prueba]
        assert set(entrenamiento.partido_id).isdisjoint(ids_prueba)
        modelo = ajustar(entrenamiento, nx, ny)
        puntos = puntuar(acciones.loc[prueba], modelo)
        puntos['pliegue'] = numero
        resultado.append(puntos)
        diagnosticos.append({'pliegue': numero, 'partidos_entrenamiento': int(entrenamiento.partido_id.nunique()),
                             'partidos_evaluacion': len(ids_prueba), 'iteraciones': modelo['iteraciones'],
                             'error': modelo['error'], 'celdas_vacias': modelo['celdas_vacias'],
                             'ids_evaluacion': [int(i) for i in ids_prueba]})
    resultado = pd.concat(resultado, ignore_index=True)
    assert not resultado.evento_id.duplicated().any()
    return resultado, diagnosticos


def resumir(puntos, minutos, bootstrap=1000):
    claves = ['partido_id', 'jugadora_id']
    por_partido = puntos.groupby(claves).agg(xt_neto=('xt_neto', 'sum'), xt_positivo=('xt_positivo', 'sum'),
                                           xt_con_perdidas=('xt_con_perdidas', 'sum'), acciones=('evento_id', 'size'))
    tabla = minutos.merge(por_partido, on=claves, how='left', validate='one_to_one')
    metricas = ['xt_neto', 'xt_positivo', 'xt_con_perdidas', 'acciones']
    tabla[metricas] = tabla[metricas].fillna(0)
    # Las acciones sin minutos pueden corresponder a sustituciones en descuento;
    # se exige que su denominador cero no contribuya al ranking por 90.
    filas = []
    rng = np.random.default_rng(20261016)
    for (jid, equipo), grupo in tabla.groupby(['jugadora_id', 'equipo']):
        total_minutos = grupo.minutos.sum()
        seleccion = rng.integers(0, len(grupo), size=(bootstrap, len(grupo)))
        tasas = 90 * grupo.xt_neto.to_numpy()[seleccion].sum(axis=1) / grupo.minutos.to_numpy()[seleccion].sum(axis=1)
        bajo, alto = np.quantile(tasas, [.025, .975])
        filas.append({'jugadora_id': jid, 'jugadora': grupo.jugadora.iloc[0], 'equipo': equipo,
                      'partidos': len(grupo), 'minutos': total_minutos,
                      **{m: grupo[m].sum() for m in metricas}, 'xt_neto_90': 90 * grupo.xt_neto.sum() / total_minutos,
                      'ic95_inferior': bajo, 'ic95_superior': alto,
                      'xt_por_100_acciones': 100 * grupo.xt_neto.sum() / max(grupo.acciones.sum(), 1),
                      'elegible_900': total_minutos >= 900})
    return pd.DataFrame(filas).sort_values('xt_neto_90', ascending=False), tabla
