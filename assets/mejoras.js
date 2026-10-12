(() => {
  'use strict';
  const root = document.documentElement;
  const sistema = matchMedia('(prefers-color-scheme: dark)');
  const oscuro = () => root.dataset.theme ? root.dataset.theme === 'dark' : sistema.matches;
  const nav = document.querySelector('.nav');
  if (nav) {
    const label = document.createElement('label'); label.className = 'selector-tema'; label.textContent = 'Tema ';
    const select = document.createElement('select'); select.setAttribute('aria-label','Tema de la web');
    [['auto','Sistema'],['light','Claro'],['dark','Oscuro']].forEach(([value,text]) => select.add(new Option(text,value)));
    select.value = root.dataset.theme || 'auto'; label.append(select); nav.append(label);
    select.addEventListener('change', () => {
      if (select.value === 'auto') delete root.dataset.theme; else root.dataset.theme=select.value;
      try { if (select.value==='auto') localStorage.removeItem('lineadepase-tema'); else localStorage.setItem('lineadepase-tema',select.value); } catch (_) {}
      document.dispatchEvent(new Event('tema-cambiado'));
    });
    sistema.addEventListener('change', () => { if (!root.dataset.theme) document.dispatchEvent(new Event('tema-cambiado')); });
  }
  const main = document.querySelector('main');
  if (main) {
    main.id ||= 'contenido';
    const skip = document.createElement('a'); skip.href='#'+main.id; skip.className='saltar'; skip.textContent='Saltar al contenido'; document.body.prepend(skip);
  }
  const informe = document.querySelector('[data-informe]');
  if (informe) {
    const index = document.createElement('nav'); index.className='indice'; index.setAttribute('aria-label','Índice del informe');
    const title = document.createElement('p'); title.className='etiqueta'; title.textContent='En este informe';index.append(title);
    const list = document.createElement('ul');
    informe.querySelectorAll('h2').forEach((h,n) => {
      h.id ||= 'apartado-'+(n+1); const li=document.createElement('li'),a=document.createElement('a');a.href='#'+h.id;a.textContent=h.textContent;li.append(a);list.append(li);
    });
    index.append(list); informe.querySelector('.cab-proyecto').after(index);
  }
  document.querySelectorAll('.racha').forEach(racha => {
    const result=document.createElement('p'); result.className='detalle-racha';result.setAttribute('aria-live','polite');result.textContent='Selecciona un partido para ver el resultado.';racha.after(result);
    racha.querySelectorAll('[title]').forEach(span => {
      const b=document.createElement('button');b.type='button';b.className=span.className;b.textContent=span.textContent;
      const detalle=span.title;b.setAttribute('aria-label',detalle);b.setAttribute('aria-pressed','false');
      b.addEventListener('click',()=>{racha.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));result.textContent=detalle;});span.replaceWith(b);
    });
  });
  const dialog = document.createElement('dialog');dialog.className='ampliacion';dialog.setAttribute('aria-labelledby','titulo-ampliacion');
  dialog.innerHTML='<div class="barra-ampliacion"><h2 id="titulo-ampliacion"></h2><div class="controles-ampliacion"><button type="button" data-zoom="menos" aria-label="Reducir gráfico">−</button><output aria-label="Nivel de ampliación">100 %</output><button type="button" data-zoom="mas" aria-label="Ampliar gráfico">+</button><button type="button" data-cerrar autofocus>Cerrar</button></div></div><div class="zona-ampliacion"><div class="contenido-ampliacion"></div></div>';
  document.body.append(dialog);
  const contenido=dialog.querySelector('.contenido-ampliacion'),nivel=dialog.querySelector('output');let zoom=100,origin;
  function ajustar() { contenido.style.width=zoom+'%';nivel.textContent=zoom+' %';dialog.querySelector('[data-zoom="menos"]').disabled=zoom<=100;dialog.querySelector('[data-zoom="mas"]').disabled=zoom>=250; }
  dialog.querySelector('[data-cerrar]').addEventListener('click',()=>dialog.close());
  dialog.querySelector('[data-zoom="menos"]').addEventListener('click',()=>{zoom=Math.max(100,zoom-50);ajustar();});
  dialog.querySelector('[data-zoom="mas"]').addEventListener('click',()=>{zoom=Math.min(250,zoom+50);ajustar();});
  dialog.addEventListener('close',()=>{document.body.classList.remove('modal-abierto');origin?.focus();});
  dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
  function ampliar(source,title,button) {
    if (!source) return;
    origin=button;contenido.replaceChildren();const copy=source.cloneNode(true);
    copy.querySelectorAll('[id]').forEach(e=>e.removeAttribute('id'));copy.removeAttribute('id');
    if(copy.tagName.toLowerCase()==='svg') {
      copy.setAttribute('viewBox',`0 0 ${source.getAttribute('width')} ${source.getAttribute('height')}`);
      copy.removeAttribute('width');copy.removeAttribute('height');copy.querySelectorAll('[tabindex]').forEach(e=>e.removeAttribute('tabindex'));
    }
    copy.setAttribute('aria-label',title);contenido.append(copy);dialog.querySelector('h2').textContent=title;zoom=100;ajustar();document.body.classList.add('modal-abierto');dialog.showModal();
  }
  document.querySelectorAll('.grafico,.figura img').forEach(source => {
    const dynamic=source.classList.contains('grafico');const holder=dynamic?source.parentElement:source.closest('figure');
    const title=dynamic?holder.querySelector('h3').textContent:source.alt;
    const b=document.createElement('button');b.type='button';b.className='ampliar-grafico';b.textContent='Ampliar gráfico';b.setAttribute('aria-label','Ampliar: '+title);
    b.addEventListener('click',()=>ampliar(dynamic?source.querySelector('svg'):source,title,b));holder.append(b);
  });
  const corte=document.querySelector('[data-corte]');
  if(corte)fetch('../../datos/zaragoza.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>{
    corte.textContent='Datos del análisis hasta el '+new Date(d.corte+'T12:00:00').toLocaleDateString('es-ES')+' · Jornada '+d.jornada;
  }).catch(()=>{});
})();
