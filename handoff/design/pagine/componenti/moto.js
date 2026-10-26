// AstroLog · le animazioni (vedi DECISIONI · Animazioni). Poche, con uno scopo; ferme col movimento ridotto.
// Animazioni sul DOM con la Web Animations API: non toccano lo stato e non restano a meta' nelle catture.
window.ALmoto = (function () {
  const rm = () => typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  const an = (el, kf, o) => (!el || rm() || !el.animate) ? null : el.animate(kf, Object.assign({ duration: 400, easing: 'cubic-bezier(.2,.7,.2,1)', fill: 'backwards' }, o));
  const tutti = (root, sel) => root ? [...root.querySelectorAll(sel)] : [];
  return {
    rm,
    numero: root => tutti(root, '[data-an=big]').forEach(e => an(e, [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], { duration: 450 })),
    barre: root => tutti(root, '[data-an=barra]').forEach((e, i) => an(e, [{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }], { duration: 600, delay: Math.min(i, 10) * 30 })),
    righe: root => tutti(root, '[data-an=riga]').forEach((e, i) => an(e, [{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }], { duration: 300, delay: Math.min(i, 12) * 40 })),
    apri: (root, tel) => { const v = root && root.querySelector('[data-an=velo]'), p = root && root.querySelector('[data-an=pannello]');
      if (tel) an(p, [{ transform: 'translateY(100%)' }, { transform: 'none' }], { duration: 320 });
      else { an(v, [{ backgroundColor: 'rgba(8,8,10,0)' }, { backgroundColor: 'rgba(8,8,10,.62)' }], { duration: 250 }); an(p, [{ opacity: 0, transform: 'translateY(16px)' }, { opacity: 1, transform: 'none' }], { duration: 250 }); } },
    chiudi: (root, tel, fatto) => { const v = root && root.querySelector('[data-an=velo]'), p = root && root.querySelector('[data-an=pannello]');
      if (rm() || !p || !p.animate) { fatto(); return; }
      let a; if (tel) a = p.animate([{ transform: 'none' }, { transform: 'translateY(100%)' }], { duration: 200, easing: 'ease-in', fill: 'forwards' });
      else { v && v.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 160, fill: 'forwards' }); a = p.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(10px)' }], { duration: 160, easing: 'ease-in', fill: 'forwards' }); }
      a.onfinish = fatto; },
    scivola: (root, dir) => { const p = root && root.querySelector('[data-an=pannello]'); an(p && p.firstElementChild, [{ opacity: 0, transform: 'translateX(' + dir * 24 + 'px)' }, { opacity: 1, transform: 'none' }], { duration: 300 }); },
    disegna: root => tutti(root, '[data-an=grafico]').forEach(e => an(e, [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }], { duration: 800, easing: 'cubic-bezier(.3,.6,.2,1)' })),
    mini: root => tutti(root, '[data-an=mini]').forEach((e, i) => an(e, [{ clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0 0 0)' }], { duration: 600, delay: i * 50 })),
    conta: (el, da, a) => { if (!el || rm() || da == null || da === a) return; const t0 = performance.now(), resto = el.textContent.replace(/^\d+/, '');
      const f = now => { const k = Math.min(1, (now - t0) / 300); el.textContent = Math.round(da + (a - da) * k) + resto; if (k < 1) requestAnimationFrame(f); }; requestAnimationFrame(f); },
    rect: root => { const o = {}; tutti(root, '[data-k]').forEach(e => { o[e.dataset.k] = (e.closest('section') || e).getBoundingClientRect(); }); return o; },
    flip: (prima, root) => { if (!prima || rm()) return; tutti(root, '[data-k]').forEach(e => { const s = e.closest('section') || e, r0 = prima[e.dataset.k], r = s.getBoundingClientRect();
      if (!r0) { an(s, [{ opacity: 0 }, { opacity: 1 }], { duration: 300 }); return; } const dx = r0.left - r.left, dy = r0.top - r.top; if (Math.abs(dx) + Math.abs(dy) > 1) an(s, [{ transform: 'translate(' + dx + 'px,' + dy + 'px)' }, { transform: 'none' }], { duration: 300 }); }); }
  };
})();
