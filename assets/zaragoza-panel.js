(function () {
  const fmt = n => n.toLocaleString('es-ES', {maximumFractionDigits: 2});
  const fecha = s => { const [y, m, d] = s.split('-'); return `${+d}/${+m}`; };
  const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  let datos, sede = 'Todos';

  fetch('../../datos/zaragoza.json').then(r => r.json()).then(d => {
    datos = d;
    document.getElementById('corte').textContent = `Datos hasta la jornada ${d.jornada} (${fecha(d.corte)}/${d.corte.slice(0, 4)})`;
    tablas();
    pintar();
    document.querySelectorAll('.filtro button').forEach(b => b.addEventListener('click', () => {
      sede = b.dataset.sede;
      document.querySelectorAll('.filtro button').forEach(x => x.setAttribute('aria-pressed', x === b));
      pintar();
    }));
    document.addEventListener('tema-cambiado', pintar);
    let t; window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(pintar, 150); });
  }).catch(() => {
    const destino = document.getElementById('estado-datos');
    if (destino) destino.textContent = 'No he podido cargar los datos. Prueba a recargar o consulta el informe completo.';
  });

  function filtrados() {
    return datos.partidos.filter(p => sede === 'Todos' || p.sede === sede);
  }

  function pintar() {
    const ps = filtrados();
    const ids = new Set(ps.map(p => p.partido_id));
    const goles = datos.goles.filter(g => ids.has(g.partido_id));
    const pts = d3.sum(ps, p => p.puntos), gf = d3.sum(ps, p => p.goles_favor), gc = d3.sum(ps, p => p.goles_contra);
    const pos = datos.clasificacion.find(c => c.equipo === 'Real Zaragoza');
    const kpis = [
      ['Posición', sede === 'Todos' ? `${pos.posicion}.º` : '—'],
      ['Puntos', `${pts}<small style="font-size:.9rem;font-weight:600"> en ${ps.length} PJ</small>`],
      ['Puntos por partido', ps.length ? fmt(pts / ps.length) : '—'],
      ['Goles a favor', gf],
      ['Goles en contra', gc],
      ['Porterías a cero', ps.filter(p => p.goles_contra === 0).length]
    ];
    if (document.getElementById('kpis')) document.getElementById('kpis').innerHTML = kpis.map(([k, v]) => `<div class="kpi"><span>${k}</span><b>${v}</b></div>`).join('');

    if (document.querySelector('#g-puntos')) lineaPuntos(ps);
    barrasPareadas('#g-goles', ps.map(p => ({et: `J${p.partido_id}`, a: p.goles_favor, b: p.goles_contra, tip: `J${p.partido_id} · ${p.sede === 'Casa' ? 'vs' : 'en'} ${p.rival}: ${p.goles_favor}-${p.goles_contra}`})), css('--cesped'), css('--senal'));
    const tramos = ['01–15', '16–30', '31–45+', '46–60', '61–75', '76–90+'];
    barrasPareadas('#g-tramos', tramos.map(t => {
      const a = goles.filter(g => g.tramo === t && g.sentido === 'Favor').length;
      const b = goles.filter(g => g.tramo === t && g.sentido === 'Contra').length;
      return {et: t, a, b, tip: `${t}': ${a} a favor, ${b} en contra`};
    }), css('--cesped'), css('--senal'));
    barrasPareadas('#g-tiros', ps.map(p => ({et: `J${p.partido_id}`, a: p.tiros_zaragoza, b: p.tiros_rival, parcial: !p.completo, tip: `J${p.partido_id} · ${p.rival}: ${p.tiros_zaragoza} a ${p.tiros_rival}${p.completo ? '' : ' (dato parcial)'}`})), css('--cesped'), css('--muted'));
  }

  function marco(sel, alto) {
    const el = document.querySelector(sel);
    el.innerHTML = '';
    const ancho = Math.max(260, el.clientWidth);
    const m = {t: 10, r: 10, b: 26, l: 30};
    const svg = d3.select(el).append('svg').attr('width', ancho).attr('height', alto);
    const g = svg.append('g').attr('transform', `translate(${m.l},${m.t})`);
    let tip = el.parentNode.querySelector('.tip');
    if (!tip) { tip = document.createElement('div'); tip.className = 'tip'; tip.hidden = true; el.parentNode.appendChild(tip); }
    const mostrar = (ev, txt) => {
      const r = el.parentNode.getBoundingClientRect();
      tip.textContent = txt; tip.hidden = false;
      const x = Math.min(ev.clientX - r.left + 10, r.width - tip.offsetWidth - 6);
      tip.style.left = Math.max(6, x) + 'px'; tip.style.top = (ev.clientY - r.top - 34) + 'px';
    };
    return {el, g, w: ancho - m.l - m.r, h: alto - m.t - m.b, mostrar, ocultar: () => tip.hidden = true};
  }

  function ejes(f, x, y) {
    f.g.append('g').attr('transform', `translate(0,${f.h})`).call(d3.axisBottom(x).tickSizeOuter(0)).call(s => s.select('.domain').attr('stroke', css('--linea')));
    f.g.append('g').call(d3.axisLeft(y).ticks(5).tickFormat(d3.format('d')).tickSize(-f.w)).call(s => { s.select('.domain').remove(); s.selectAll('line').attr('stroke', css('--linea')); });
  }

  function lineaPuntos(ps) {
    const f = marco('#g-puntos', 230);
    let acum = 0;
    const serie = ps.map(p => ({j: `J${p.partido_id}`, v: (acum += p.puntos), p}));
    const x = d3.scalePoint().domain(serie.map(d => d.j)).range([0, f.w]).padding(.4);
    const y = d3.scaleLinear().domain([0, Math.max(3, d3.max(serie, d => d.v) || 0)]).nice().range([f.h, 0]);
    ejes(f, x, y);
    f.g.append('path').datum(serie).attr('fill', 'none').attr('stroke', css('--cesped')).attr('stroke-width', 2.5)
      .attr('d', d3.line().x(d => x(d.j)).y(d => y(d.v)));
    f.g.selectAll('circle').data(serie).join('circle').attr('cx', d => x(d.j)).attr('cy', d => y(d.v)).attr('r', 5)
      .attr('fill', d => d.p.puntos ? 'url(#zgz-mitad)' : css('--senal')).attr('stroke', d => d.p.puntos ? '#213e96' : css('--panel')).attr('stroke-width', 2)
      .attr('tabindex', 0).attr('role', 'img').attr('aria-label', d => `${d.j} · ${d.p.rival}: ${d.v} puntos acumulados`)
      .on('pointerdown mousemove', (ev, d) => f.mostrar(ev, `${d.j} · ${d.p.rival} (${d.p.goles_favor}-${d.p.goles_contra}): ${d.v} pts`)).on('mouseleave blur', f.ocultar)
      .on('focus', (ev,d) => { const r=ev.target.getBoundingClientRect(); f.mostrar({clientX:r.x,clientY:r.y}, `${d.j} · ${d.p.rival}: ${d.v} pts`); });
  }

  function barrasPareadas(sel, filas, cA, cB) {
    if (!document.querySelector(sel)) return;
    const f = marco(sel, 230);
    const x = d3.scaleBand().domain(filas.map(d => d.et)).range([0, f.w]).padding(.25);
    const xi = d3.scaleBand().domain(['a', 'b']).range([0, x.bandwidth()]).padding(.08);
    const y = d3.scaleLinear().domain([0, Math.max(1, d3.max(filas, d => Math.max(d.a, d.b)))]).nice().range([f.h, 0]);
    ejes(f, x, y);
    const grupo = f.g.selectAll('.gr').data(filas).join('g').attr('transform', d => `translate(${x(d.et)},0)`)
      .attr('opacity', d => d.parcial ? .45 : 1);
    grupo.selectAll('rect').data(d => [['a', d.a, cA, d], ['b', d.b, cB, d]]).join('rect')
      .attr('x', d => xi(d[0])).attr('width', xi.bandwidth()).attr('y', d => y(d[1])).attr('height', d => f.h - y(d[1]))
      .attr('rx', 2).attr('fill', d => d[2])
      .attr('tabindex', 0).attr('role','img').attr('aria-label', d=>d[3].tip)
      .on('pointerdown mousemove', (ev, d) => f.mostrar(ev, d[3].tip)).on('mouseleave blur', f.ocultar)
      .on('focus', (ev,d) => { const r=ev.target.getBoundingClientRect(); f.mostrar({clientX:r.x,clientY:r.y},d[3].tip); });
  }

  function tablas() {
    const max = d3.max(datos.jugadores, j => j.minutos);
    if (document.querySelector('#t-jugadores tbody')) document.querySelector('#t-jugadores tbody').innerHTML = datos.jugadores.slice().sort((a, b) => b.minutos - a.minutos).map(j =>
      `<tr><td>${j.jugador}</td><td class="n">${j.partidos}</td><td class="n">${j.titularidades}</td><td><span class="barra" style="width:${Math.round(j.minutos / max * 90)}px;background:var(--cesped)"></span>${j.minutos}'</td><td class="n">${j.goles}</td><td class="n">${j.asistencias}</td></tr>`).join('');
    if (document.querySelector('#t-clasif tbody')) document.querySelector('#t-clasif tbody').innerHTML = datos.clasificacion.map(c =>
      `<tr${c.equipo === 'Real Zaragoza' ? ' class="propio"' : ''}><td class="n">${c.posicion}</td><td>${c.equipo}</td><td class="n">${c.pj}</td><td class="n">${c.gf - c.gc > 0 ? '+' : ''}${c.gf - c.gc}</td><td class="n">${c.puntos}</td></tr>`).join('');
    const hoy = new Intl.DateTimeFormat('sv-SE', {timeZone:'Europe/Madrid'}).format(new Date());
    const proximos = datos.proximos.filter(p => p.fecha >= hoy);
    if (!proximos.length && document.getElementById('nota-calendario')) document.getElementById('nota-calendario').textContent = 'No hay fechas futuras en el calendario publicado. Consulta el proveedor de resultados para las últimas novedades.';
    if (document.querySelector('#t-proximos tbody')) document.querySelector('#t-proximos tbody').innerHTML = proximos.map(p =>
      `<tr><td>${p.jornada}</td><td>${fecha(p.fecha)}</td><td>${p.rival}</td><td>${p.sede}</td><td class="n">${p.posicion_rival ? p.posicion_rival + '.º' : '—'}</td></tr>`).join('');
  }
})();
