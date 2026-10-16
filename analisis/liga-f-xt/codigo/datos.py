"""Descarga reproducible y selección explícita de acciones de juego abierto."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

import pandas as pd

COMMIT = '4b73468fc5b0f1950f9f66fada70ad3a4f9327cb'
BASE = f'https://raw.githubusercontent.com/hudl/open-data/{COMMIT}'


def descargar(ruta, cache):
    """Reutiliza la caché. Solo reintenta errores transitorios; respeta 403/429."""
    destino = Path(cache) / ruta
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        for intento in range(3):
            try:
                with urlopen(Request(f'{BASE}/{ruta}', headers={'User-Agent': 'LineaDePase-research/1.0'}), timeout=60) as respuesta:
                    contenido = respuesta.read()
                temporal = destino.with_suffix(destino.suffix + '.tmp')
                temporal.write_bytes(contenido)
                temporal.replace(destino)
                break
            except Exception as error:
                if getattr(error, 'code', None) in (403, 429) or intento == 2:
                    raise
                time.sleep(2 ** intento)
    contenido = destino.read_bytes()
    registro = {'ruta': ruta, 'url': f'{BASE}/{ruta}', 'sha256': hashlib.sha256(contenido).hexdigest(),
                'fecha_descarga_utc': datetime.fromtimestamp(destino.stat().st_mtime, timezone.utc).isoformat(),
                'bytes': len(contenido)}
    return contenido, registro


def obtener_temporada(cache):
    contenido, registro = descargar('data/matches/182/281.json', cache)
    partidos = json.loads(contenido)
    assert len(partidos) == 240 and len({p['match_id'] for p in partidos}) == 240
    rutas = [f'data/{tipo}/{p["match_id"]}.json' for p in partidos for tipo in ('events', 'lineups')]
    archivos = {}
    manifiesto = [registro]
    with ThreadPoolExecutor(max_workers=3) as grupo:
        for ruta, (contenido, registro) in zip(rutas, grupo.map(lambda r: descargar(r, cache), rutas)):
            archivos[ruta] = json.loads(contenido)
            manifiesto.append(registro)
    return partidos, archivos, manifiesto


def reloj_minutos(texto, periodo):
    """Minutos reglamentarios: el descuento se trunca a 45 o 90."""
    minutos, segundos = map(float, texto.split(':'))
    return min(max(minutos + segundos / 60, 0 if periodo == 1 else 45), 45 if periodo == 1 else 90)


def minutos_eventos(eventos):
    """Minutos de participación por once, sustitución y expulsión.

    Las salidas médicas temporales no descuentan minutos de participación.
    Se evita depender de intervalos posicionales que contienen relojes invertidos.
    """
    activos, acumulados = {}, {}
    for e in sorted(eventos, key=lambda e: (e['period'], e['timestamp'], e['index'])):
        if e['period'] not in (1, 2):
            continue
        tipo = e['type']['name']
        horas, minutos, segundos = map(float, e['timestamp'].split(':'))
        reloj = (0 if e['period'] == 1 else 45) + min(45, horas*60 + minutos + segundos/60)
        if tipo == 'Starting XI':
            for p in e['tactics']['lineup']:
                activos[p['player']['id']] = 0.0
        pid = e.get('player', {}).get('id')
        tarjeta = e.get('bad_behaviour', {}).get('card', {}).get('name') or e.get('foul_committed', {}).get('card', {}).get('name')
        cerrar = tipo == 'Substitution' or tarjeta in ('Red Card', 'Second Yellow') or (tipo == 'Player Off' and e.get('player_off', {}).get('permanent', False))
        if cerrar and pid in activos:
            inicio = activos.pop(pid)
            assert reloj >= inicio
            acumulados[pid] = acumulados.get(pid, 0) + reloj - inicio
        if tipo == 'Substitution':
            nuevo = e['substitution']['replacement']['id']
            assert nuevo not in activos
            activos[nuevo] = reloj
    for pid, inicio in activos.items():
        acumulados[pid] = acumulados.get(pid, 0) + 90 - inicio
    return acumulados


def preparar(partidos, archivos):
    acciones, minutos, auditoria = [], [], []
    identificadores = set()
    for partido in partidos:
        mid = partido['match_id']
        eventos = archivos[f'data/events/{mid}.json']
        repetidos = sum(e['id'] in identificadores for e in eventos) + len(eventos) - len({e['id'] for e in eventos})
        identificadores.update(e['id'] for e in eventos)
        assert not repetidos, f'Eventos duplicados en {mid}'
        cuenta = {'partido_id': mid, 'fecha': partido['match_date'], 'jornada': partido['match_week'],
                  'eventos': len(eventos), 'duplicados': repetidos, 'sin_coordenadas': 0,
                  'coordenadas_invalidas': 0, 'acciones_seleccionadas': 0, 'intervalos_posicion_invertidos': 0}
        for e in eventos:
            tipo = e['type']['name']
            if tipo not in ('Pass', 'Carry', 'Shot') or e['period'] not in (1, 2):
                continue
            if e.get('play_pattern', {}).get('name') != 'Regular Play':
                continue
            # Solo pases normales, no saques, centros de falta u otros reinicios.
            if tipo == 'Pass' and 'type' in e.get('pass', {}):
                continue
            if tipo == 'Shot' and e['shot'].get('type', {}).get('name') != 'Open Play':
                continue
            inicio = e.get('location')
            final = e.get(tipo.lower(), {}).get('end_location') if tipo != 'Shot' else inicio
            if not inicio or not final:
                cuenta['sin_coordenadas'] += 1
                continue
            if not all(0 <= p[0] <= 120 and 0 <= p[1] <= 80 for p in (inicio, final)):
                cuenta['coordenadas_invalidas'] += 1
                continue
            cuenta['acciones_seleccionadas'] += 1
            acciones.append({'partido_id': mid, 'fecha': partido['match_date'], 'evento_id': e['id'],
                             'jugadora_id': e['player']['id'], 'jugadora': e['player']['name'],
                             'equipo_id': e['team']['id'], 'equipo': e['team']['name'],
                             'tipo': tipo, 'x': inicio[0], 'y': inicio[1], 'fin_x': final[0], 'fin_y': final[1],
                             'exito': tipo == 'Carry' or (tipo == 'Pass' and 'outcome' not in e['pass']),
                             'gol': tipo == 'Shot' and e['shot']['outcome']['name'] == 'Goal'})
        participacion = minutos_eventos(eventos)
        for equipo in archivos[f'data/lineups/{mid}.json']:
            for jugadora in equipo['lineup']:
                for posicion in jugadora['positions']:
                    inicio = reloj_minutos(posicion['from'], posicion['from_period'])
                    fin = 90.0 if posicion['to'] is None else reloj_minutos(posicion['to'], posicion['to_period'])
                    if fin < inicio:
                        cuenta['intervalos_posicion_invertidos'] += 1
                total = participacion.get(jugadora['player_id'], 0)
                assert 0 <= total <= 90
                if total:
                    minutos.append({'partido_id': mid, 'jugadora_id': jugadora['player_id'],
                                    'jugadora': jugadora.get('player_nickname') or jugadora['player_name'],
                                    'equipo': equipo['team_name'], 'minutos': total})
        auditoria.append(cuenta)
    acciones, minutos, auditoria = pd.DataFrame(acciones), pd.DataFrame(minutos), pd.DataFrame(auditoria)
    assert auditoria['coordenadas_invalidas'].sum() == 0
    assert not acciones.isna().any().any()
    assert not minutos.duplicated(['partido_id', 'jugadora_id']).any()
    equipos = {p[lado]['home_team_id' if lado == 'home_team' else 'away_team_id'] for p in partidos for lado in ('home_team', 'away_team')}
    assert len(equipos) == 16
    # Cada equipo debe haber disputado 30 partidos, no solo figurar en el catálogo.
    apariciones = [p[lado]['home_team_id' if lado == 'home_team' else 'away_team_id'] for p in partidos for lado in ('home_team', 'away_team')]
    assert set(pd.Series(apariciones).value_counts()) == {30}
    return acciones, minutos, auditoria
