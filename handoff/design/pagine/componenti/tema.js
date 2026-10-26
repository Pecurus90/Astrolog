// AstroLog · token del linguaggio bento. La fonte dei colori e' il foglio (astrolog.css, sez. 1): qui i colori
// con un significato sono var(--…) del foglio; restano qui solo i valori che servono ai conti (testo, carte, accento, esiti).
// Due modi × cinque accenti. I colori con un significato (esiti, filtri, pianeti, Luna) non cambiano con l'accento.
(function () {
  const DARK = { font: "'Outfit',sans-serif", page: '#c9c9cf', frame: '#0d0d10', card: '#18181c', card2: '#222228', line: '#2e2e35', text: '#f4f4f6', muted: '#a6a6b0', navOn: '#f4f4f6', navOnFg: '#0d0d10',
    hBg: '#18181c', hFg: '#f4f4f6', hMu: '#a6a6b0', hTrack: '#26262c', tipBg: '#2c2c33', tipFg: '#f4f4f6', sparkOff: '#34343c', track: '#2c2c33',
    pills: [['#1f3a2b', '#8fe3b0'], ['#3a3318', '#f5d76e'], ['#3f201d', '#ff9d8f']], warn: '#f5d76e', bad: '#ff8a7a',
    pal: ['var(--setup-2)', 'var(--setup-3)', 'var(--setup-4)', 'var(--setup-5)'], pl: ['var(--pianeta-0)', 'var(--pianeta-1)', 'var(--pianeta-2)', 'var(--pianeta-3)', 'var(--pianeta-4)', 'var(--pianeta-5)', 'var(--pianeta-6)'], band: { c: 'var(--banda-colore)', o: ['var(--banda-0)', 'var(--banda-1)', 'var(--banda-2)', 'var(--banda-3)', 'var(--banda-4)'] },
    tipi: { exo: 'var(--tipo-exo)', ecl: 'var(--tipo-ecl)', var: 'var(--tipo-var)', aavso: 'var(--tipo-var)', neo: 'var(--tipo-neo)', sn: 'var(--tipo-sn)', cometa: 'var(--tipo-cometa)', evento: 'var(--tipo-evento)' }, FC: ['var(--filtro-0)', 'var(--filtro-1)', 'var(--filtro-2)', 'var(--filtro-3)', 'var(--filtro-4)', 'var(--filtro-5)', 'var(--filtro-6)', 'var(--filtro-7)', 'var(--filtro-8)', 'var(--filtro-9)'], spot: 'var(--macchia)',
    foto: 'var(--foto-fondo)', umid: 'var(--umidita)', strum: ['var(--strumento-1)', 'var(--strumento-2)', 'var(--strumento-3)', 'var(--strumento-4)'], inchiostro: 'var(--inchiostro)' };
  const LIGHT = { font: "'Plus Jakarta Sans',sans-serif", page: '#dcdde2', frame: '#f4f4f2', card: '#ffffff', card2: '#f2f2ef', line: '#e4e4e0', text: '#17181c', muted: '#5d5f66', navOnFg: '#ffffff',
    hBg: '#ffffff', hFg: '#17181c', hMu: '#5d5f66', hTrack: '#eef0f3', tipBg: '#17181c', tipFg: '#ffffff', sparkOff: '#dedfe3', track: '#e8e9ec',
    pills: [['#e1f2e7', '#1a6b42'], ['#fbefd6', '#8a5600'], ['#fbe3df', '#b02a1c']], warn: '#956600', bad: '#bf4232',
    pal: ['var(--setup-2)', 'var(--setup-3)', 'var(--setup-4)', 'var(--setup-5)'], pl: ['var(--pianeta-0)', 'var(--pianeta-1)', 'var(--pianeta-2)', 'var(--pianeta-3)', 'var(--pianeta-4)', 'var(--pianeta-5)', 'var(--pianeta-6)'], band: { c: 'var(--banda-colore)', o: ['var(--banda-0)', 'var(--banda-1)', 'var(--banda-2)', 'var(--banda-3)', 'var(--banda-4)'] },
    tipi: { exo: 'var(--tipo-exo)', ecl: 'var(--tipo-ecl)', var: 'var(--tipo-var)', aavso: 'var(--tipo-var)', neo: 'var(--tipo-neo)', sn: 'var(--tipo-sn)', cometa: 'var(--tipo-cometa)', evento: 'var(--tipo-evento)' }, FC: ['var(--filtro-0)', 'var(--filtro-1)', 'var(--filtro-2)', 'var(--filtro-3)', 'var(--filtro-4)', 'var(--filtro-5)', 'var(--filtro-6)', 'var(--filtro-7)', 'var(--filtro-8)', 'var(--filtro-9)'], spot: 'var(--macchia)',
    foto: 'var(--foto-fondo)', umid: 'var(--umidita)', strum: ['var(--strumento-1)', 'var(--strumento-2)', 'var(--strumento-3)', 'var(--strumento-4)'], inchiostro: 'var(--inchiostro)' };
  const ACC = {
    'originale': { d: ['#b9a6ff', '#15111f', '#5a5378'], l: ['#1f5c3d', '#0f2a1c'], lightGreen: true },
    'ambra · blu notte': { d: ['#e9a23b', '#1f1406', '#6b5530'], l: ['#1e3a6e', '#0f2142'] },
    'turchese · petrolio': { d: ['#5ad1c8', '#06201e', '#2f5a57'], l: ['#0f4c5c', '#08303a'] },
    'corallo · terracotta': { d: ['#ff9a7a', '#2a0f06', '#6b3c2e'], l: ['#8f3a22', '#5e2416'] },
    'ghiaccio · indaco': { d: ['#9cc9ff', '#081a2e', '#3b4f6b'], l: ['#2f3a8f', '#1a2160'] } };
  const PREDEFINITO = 'ambra · blu notte';
  function tema(modo, accento) {
    const dk = (modo || 'scuro') === 'scuro', acc = ACC[accento ?? PREDEFINITO] || ACC['originale']; let t;
    if (dk) { const [a, fg, m] = acc.d; t = { ...DARK, accent: a, hPill: a, hPillFg: fg, calOnFg: fg, monthBar: m }; }
    else { const [a, deep] = acc.l; t = { ...LIGHT, accent: a, navOn: a, hPill: a, hPillFg: '#ffffff', calOnFg: '#ffffff', monthBar: a,
      ...(acc.lightGreen ? { page: '#dfe4de', frame: '#f3f5f1', card2: '#f1f4ef', line: '#e2e7e0', text: '#15211a', muted: '#5b6a61', hFg: '#15211a', hMu: '#5b6a61', hTrack: '#eef2ee', tipBg: '#15211a', sparkOff: '#dbe3dd', track: '#e5ece7' } : {}) }; }
    // Dal foglio (var): cambiano con modo e accento sull'involucro data-modo / data-accento
    Object.assign(t, { hBar: 'var(--prot-barra)', spark: 'var(--barretta)', calOn: 'var(--giorno-su)', ring: 'var(--anello)', todoBg: 'var(--da-confermare-fondo)', todoFg: 'var(--da-confermare-testo)' });
    t.pal = ['var(--setup-1)', ...t.pal]; t.warnFg = dk ? '#1a1606' : '#ffffff'; t.pillOkBg = t.pills[0][0]; t.pillOkFg = t.pills[0][1]; t.dk = dk;
    t.modo = dk ? 'scuro' : 'chiaro'; t.acc = ACC[accento ?? PREDEFINITO] ? (accento ?? PREDEFINITO).split(' ')[0] : 'originale';
    return t;
  }
  // Filtri: etichetta e tinta (indice in FC, piu' indici = strisce oblique da 3 px, null = sconosciuto tratteggiato, 'tenue' = nessun filtro)
  const FD = { l: ['L', 3], r: ['R', 5], g: ['G', 6], b: ['B', 4], ha: ['Hα', 0], hb: ['Hβ', 7], oiii: ['OIII', 1], sii: ['SII', 2], colori: ['a colori', [5, 6, 4]], 'colori-lp': ['a colori LP', 8], 'colori-uvir': ['a colori UV/IR', 9], 'ha-oiii': ['Hα + OIII', [0, 1]], 'sii-oiii': ['SII + OIII', [2, 1]], tri: ['tri band', [0, 7, 1]], quad: ['quad band', [0, 7, 1, 2]], ignoto: ['Filtro non indicato', null], senza: ['nessun filtro', 'tenue'] };
  // Colore della curva di un filtro (una linea ha un colore solo): la prima banda, quad band in Hβ per distinguerla da Hα
  const FL = { colori: 5, 'ha-oiii': 0, 'sii-oiii': 2, tri: 0, quad: 7 };
  const strisce = (t, k) => 'repeating-linear-gradient(135deg,' + k.map((j, i) => t.FC[j] + ' ' + i * 3 + 'px ' + (i + 1) * 3 + 'px').join(',') + ')';
  const tinta = (t, k) => { const c = (FD[k] || FD.ignoto)[1]; return { bg: c == null ? 'transparent' : c === 'tenue' ? t.muted : Array.isArray(c) ? strisce(t, c) : t.FC[c], bd: c == null ? '1.5px dashed ' + t.muted : '0' }; };
  const linea = (t, k) => { const c = k in FL ? FL[k] : (FD[k] || FD.ignoto)[1]; return typeof c === 'number' ? t.FC[c] : t.muted; };
  // Tratteggio dei vuoti e delle tendenze
  const tratteggio = c => 'repeating-linear-gradient(135deg, ' + c + ' 0 3px, transparent 3px 8px)';
  // Luna: falce disegnata dalla frazione illuminata, nel disco di raggio 10
  const lunaD = (pct, cresce) => { const k = pct / 100, rx = (10 * Math.abs(1 - 2 * k)).toFixed(2), o = cresce ? 1 : 0, s = (k < 0.5) === !!cresce ? 0 : 1; return 'M0 -10A10 10 0 0 ' + o + ' 0 10A' + rx + ' 10 0 0 ' + s + ' 0 -10Z'; };
  // Numeri: decimali col punto, migliaia con lo spazio sottile da 10 000; ore coi minuti, mai "0 h"
  const al = n => { n = Math.round(Number(n)); return n === 8 || n === 11 || (n >= 80 && n <= 89) ? 'all\u0027' : 'al '; };
  const num = n => { const s = String(n), [i, d] = s.split('.'); return Math.abs(parseInt(i, 10)) < 10000 ? s : i.replace(/\B(?=(\d{3})+(?!\d))/g, '\u202F') + (d ? '.' + d : ''); };
  const virg = (v, d) => v.toFixed(d);
  const ore = x => { if (x == null) return 'senza durata'; if (x < 0.1) return '< 6 min'; if (x < 1) return Math.round(x * 60) + ' min'; const h = Math.floor(x + 1e-9), m = Math.round((x - h) * 60); return m ? h + ' h ' + String(m).padStart(2, '0') : h + ' h'; };
  // Trasparenza: sull'esadecimale rgba(); sui token del foglio color-mix (anche l'opacita' puo' essere un token)
  const rgba = (c, o) => { if (typeof c === 'string' && c[0] === '#' && typeof o === 'number') { const n = parseInt(c.slice(1), 16); return 'rgba(' + (n >> 16) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + o + ')'; }
    return 'color-mix(in srgb, ' + c + ' calc(' + o + ' * 100%), transparent)'; };
  // Il valore di un token del foglio, per i conti (contrasto, miscele): legge il foglio per modo e accento
  let sonda = null; const giaLetti = {}; const hexDi = (v, modo, accento) => { if (typeof v !== 'string' || !v.startsWith('var(')) return v; if (typeof document === 'undefined') return '';
    const ch = (modo || 'scuro') + '|' + (accento ?? PREDEFINITO) + '|' + v; if (giaLetti[ch]) return giaLetti[ch];
    if (!sonda) { sonda = document.createElement('i'); sonda.style.display = 'none'; document.body.appendChild(sonda); }
    sonda.setAttribute('data-modo', modo || 'scuro'); sonda.setAttribute('data-accento', ACC[accento ?? PREDEFINITO] ? (accento ?? PREDEFINITO).split(' ')[0] : 'originale');
    const r = getComputedStyle(sonda).getPropertyValue(v.slice(4, -1).trim()).trim(); if (r) giaLetti[ch] = r; return r; };
  // Formato della pagina: ?formato= nell'indirizzo, poi il parametro, poi automatico (telefono sotto 700 px)
  const formatoScelto = p => ((typeof location !== 'undefined' && (location.search.match(/formato=(telefono|desktop)/) || [])[1]) || p || 'automatico');
  const telefono = (f, w) => f === 'telefono' || (f === 'automatico' && w < 700);
  window.AL = { tema, formatoScelto, telefono, ACCENTI: Object.keys(ACC), PREDEFINITO, rgba, hexDi, FD, tinta, linea, tratteggio, lunaD, num, virg, ore, al,
    LUNA: { dark: 'var(--luna-scura)', lit: 'var(--luna-chiara)', line: 'var(--luna-linea)' }, SOLE: 'var(--sole)', BIANCO: 'var(--bianco)', CORNICE_TEL: 'var(--cornice-telefono)', NERO: 'var(--nero)',
    // Il cielo disegnato (Planner, PlannerSolare, PlannerEventi): fissi, sul fondo --cielo
    CIELO_D: { testo: 'var(--cielo-testo)', stella: 'var(--cielo-stella)', orizzonte: 'var(--cielo-orizzonte)', traccia: 'var(--cielo-traccia)', segno: 'var(--cielo-segno)', disco: 'var(--cielo-disco)', discoBordo: 'var(--cielo-disco-bordo)', lunaEclisse: 'var(--cielo-luna-eclisse)', lunaBordo: 'var(--cielo-luna-bordo)', eclisse: 'var(--cielo-eclisse)', penombra: 'var(--cielo-penombra)', anelli: 'var(--cielo-anelli)', anelliChiari: 'var(--cielo-anelli-chiari)', macchia: 'var(--cielo-macchia)' },
    CORPI: { mercurio: 'var(--corpo-mercurio)', venere: 'var(--corpo-venere)', marte: 'var(--corpo-marte)', giove: 'var(--corpo-giove)', saturno: 'var(--corpo-saturno)', urano: 'var(--corpo-urano)', nettuno: 'var(--corpo-nettuno)' },
    SEGNI: ['✓', '!', '✕'], PAROLE: ['buona', 'incerta', 'non adatta'] };
})();
// Il foglio unico (astrolog.css, accanto alla cartella componenti): lo carica chi carica i token.
(() => { if (typeof document === 'undefined' || document.querySelector('link[data-al="astrolog.css"]')) return;
  const s = document.currentScript && document.currentScript.src; const u = s ? new URL('../astrolog.css', s).href : 'astrolog.css';
  const l = document.createElement('link'); l.rel = 'stylesheet'; l.href = u; l.setAttribute('data-al', 'astrolog.css'); document.head.appendChild(l); })();
// Strisce che scorrono di lato: sfumatura sul bordo che continua (destra all'inizio, sinistra alla fine, entrambe in mezzo).
(() => { if (typeof window === 'undefined' || window.__alSfuma) return; window.__alSfuma = 1;
  const G = { d: 'linear-gradient(to right,#000 calc(100% - 40px),transparent)', s: 'linear-gradient(to right,transparent,#000 40px)', e: 'linear-gradient(to right,transparent,#000 40px,#000 calc(100% - 40px),transparent)' };
  const fa = el => { const max = el.scrollWidth - el.clientWidth, x = el.scrollLeft, m = max <= 2 ? '' : x <= 2 ? G.d : x >= max - 2 ? G.s : G.e;
    if (el.style.maskImage !== m) { el.style.maskImage = m; el.style.webkitMaskImage = m; } };
  const scorre = el => { const o = getComputedStyle(el).overflowX; return o === 'auto' || o === 'scroll'; };
  let tm; const giro = () => { clearTimeout(tm); tm = setTimeout(() => document.querySelectorAll('div,span,nav').forEach(el => { if ((el.scrollWidth > el.clientWidth + 2 || el.style.maskImage) && scorre(el)) fa(el); }), 250); };
  document.addEventListener('scroll', e => { const el = e.target; if (el && el.nodeType === 1 && scorre(el)) fa(el); }, true);
  window.addEventListener('resize', giro);
  const via = () => { new MutationObserver(giro).observe(document.body, { childList: true, subtree: true }); giro(); };
  document.body ? via() : document.addEventListener('DOMContentLoaded', via);
})();
