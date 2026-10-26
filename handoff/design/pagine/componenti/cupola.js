// AstroLog · Carta del cielo: il motore della cupola (three.js, dal CDN).
// Disegna il cielo vero di dati-cielo.js e lo muove: ora, viste, trascinamento, volo verso un oggetto, immagine di Aladin all'arrivo.
// I conti di posizione sono qui perche' servono al disegno (bassa precisione); giudizi e ore arrivano dalla pagina.
(function () {
  if (window.ALcupola) return;
  const URL3 = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.min.js';
  const D = Math.PI / 180;
  const norm = a => ((a % 360) + 360) % 360;
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const sstep = (a, b, x) => { const k = clamp((x - a) / (b - a), 0, 1); return k * k * (3 - 2 * k); };
  const ease = k => k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
  const dAng = (a, b) => ((((b - a) % 360) + 540) % 360) - 180;

  // ---------- Posizioni ----------
  const jd = t => t / 86400000 + 2440587.5;
  const lst = (t, lon) => norm(280.46061837 + 360.98564736629 * (jd(t) - 2451545) + lon);
  const EPS = 23.4393 * D;
  const ecl2eq = (lam, bet) => { const x = Math.cos(bet) * Math.cos(lam), y = Math.cos(bet) * Math.sin(lam), z = Math.sin(bet);
    const ye = y * Math.cos(EPS) - z * Math.sin(EPS), ze = y * Math.sin(EPS) + z * Math.cos(EPS); return [norm(Math.atan2(ye, x) / D), Math.asin(clamp(ze, -1, 1)) / D]; };
  const sole = t => { const n = jd(t) - 2451545, L = 280.46 + 0.9856474 * n, g = (357.528 + 0.9856003 * n) * D;
    const lam = (L + 1.915 * Math.sin(g) + 0.02 * Math.sin(2 * g)) * D; return { lam, eq: ecl2eq(lam, 0) }; };
  const luna = t => { const n = jd(t) - 2451545, Lp = 218.316 + 13.176396 * n, Mp = (134.963 + 13.064993 * n) * D, F = (93.272 + 13.22935 * n) * D, Dm = (297.85 + 12.190749 * n) * D, M = (357.529 + 0.98560028 * n) * D;
    const lam = (Lp + 6.289 * Math.sin(Mp) - 1.274 * Math.sin(Mp - 2 * Dm) + 0.658 * Math.sin(2 * Dm) - 0.186 * Math.sin(M) - 0.059 * Math.sin(2 * Mp - 2 * Dm) - 0.057 * Math.sin(Mp - 2 * Dm + M) + 0.053 * Math.sin(Mp + 2 * Dm) + 0.046 * Math.sin(2 * Dm - M)) * D;
    const bet = (5.128 * Math.sin(F) + 0.281 * Math.sin(Mp + F) - 0.278 * Math.sin(F - Mp) - 0.173 * Math.sin(F - 2 * Dm)) * D;
    const s = sole(t), el = Math.acos(clamp(Math.cos(bet) * Math.cos(lam - s.lam), -1, 1));
    return { eq: ecl2eq(lam, bet), k: (1 - Math.cos(el)) / 2, cresce: norm((lam - s.lam) / D) < 180 }; };
  // Elementi orbitali J2000 e variazione per secolo (JPL, Standish): a, e, I, L, perielio, nodo
  const EL = { terra: [1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0, 0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0],
    mercurio: [0.38709927, 0.20563593, 7.00497902, 252.2503235, 77.45779628, 48.33076593, 0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081],
    venere: [0.72333566, 0.00677672, 3.39467605, 181.9790995, 131.60246718, 76.67984255, 0.0000039, -0.00004107, -0.0007889, 58517.81538729, 0.00268329, -0.27769418],
    marte: [1.52371034, 0.0933941, 1.84969142, -4.55343205, -23.94362959, 49.55953891, 0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343],
    giove: [5.202887, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909, -0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106],
    saturno: [9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448, -0.0012506, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794],
    urano: [19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.9542763, 74.01692503, -0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589],
    nettuno: [30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574, 0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664] };
  const kep = (e, T) => { const a = e[0] + e[6] * T, ec = e[1] + e[7] * T, I = (e[2] + e[8] * T) * D, L = e[3] + e[9] * T, w = e[4] + e[10] * T, Om = e[5] + e[11] * T;
    const M = norm(L - w) * D, om = (w - Om) * D, O = Om * D; let E = M + ec * Math.sin(M); for (let i = 0; i < 7; i++) E -= (E - ec * Math.sin(E) - M) / (1 - ec * Math.cos(E));
    const xp = a * (Math.cos(E) - ec), yp = a * Math.sqrt(1 - ec * ec) * Math.sin(E), co = Math.cos(om), so = Math.sin(om), cO = Math.cos(O), sO = Math.sin(O), cI = Math.cos(I), sI = Math.sin(I);
    return [(co * cO - so * sO * cI) * xp + (-so * cO - co * sO * cI) * yp, (co * sO + so * cO * cI) * xp + (-so * sO + co * cO * cI) * yp, so * sI * xp + co * sI * yp]; };
  const pianeta = (k, t) => { const T = (jd(t) - 2451545) / 36525, p = kep(EL[k], T), e = kep(EL.terra, T), x = p[0] - e[0], y = p[1] - e[1], z = p[2] - e[2];
    const ye = y * Math.cos(EPS) - z * Math.sin(EPS), ze = y * Math.sin(EPS) + z * Math.cos(EPS); return [norm(Math.atan2(ye, x) / D), Math.atan2(ze, Math.hypot(x, ye)) / D]; };
  const altaz = (ra, dec, t, lat, lon) => { const H = (lst(t, lon) - ra) * D, d = dec * D, f = lat * D;
    const alt = Math.asin(clamp(Math.sin(f) * Math.sin(d) + Math.cos(f) * Math.cos(d) * Math.cos(H), -1, 1));
    const az = Math.atan2(-Math.cos(d) * Math.sin(H), Math.cos(f) * Math.sin(d) - Math.sin(f) * Math.cos(d) * Math.cos(H)); return [alt / D, norm(az / D)]; };
  const vec = (ra, dec) => { const a = ra * D, d = dec * D, c = Math.cos(d); return [c * Math.cos(a), c * Math.sin(a), Math.sin(d)]; };
  const vAltAz = (az, alt, r) => { const a = az * D, h = alt * D; return [r * Math.cos(h) * Math.sin(a), r * Math.sin(h), -r * Math.cos(h) * Math.cos(a)]; };
  const matAltAz = (t, lat, lon) => { const th = lst(t, lon) * D, f = lat * D, ct = Math.cos(th), st = Math.sin(th), cf = Math.cos(f), sf = Math.sin(f);
    return [-st, ct, 0, cf * ct, cf * st, sf, sf * ct, sf * st, -cf]; };
  const PIANETI = [['mercurio', 'Mercurio'], ['venere', 'Venere'], ['marte', 'Marte'], ['giove', 'Giove'], ['saturno', 'Saturno'], ['urano', 'Urano'], ['nettuno', 'Nettuno']];
  const corpi = t => { const l = luna(t), s = sole(t);
    return [{ id: 'Luna', nome: 'Luna', tipo: 'luna', ra: l.eq[0], dec: l.eq[1], k: l.k, cresce: l.cresce }, { id: 'Sole', nome: 'Sole', tipo: 'sole', ra: s.eq[0], dec: s.eq[1] },
      ...PIANETI.map(([k, n]) => { const p = pianeta(k, t); return { id: 'pianeta:' + k, k, nome: n, tipo: 'pianeta', ra: p[0], dec: p[1] }; })]; };

  // ---------- Il catalogo ----------
  // Colori con un significato: fissi, sul fondo --cielo (da portare nel foglio come --dso-* e --calore-*)
  const CLASSI = ['galassia', 'nebulosa', 'nebulosa planetaria', 'resto di supernova', 'ammasso aperto', 'ammasso globulare'];
  const CLASSI_P = ['galassie', 'nebulose', 'planetarie', 'resti di supernova', 'ammassi aperti', 'ammassi globulari'];
  const COLORI = ['#ffbe85', '#ff8aa0', '#62dccb', '#c39cff', '#94bcff', '#ffe07a'];
  const CALORE = [[0, [58, 36, 128]], [0.3, [140, 47, 132]], [0.58, [226, 82, 74]], [0.8, [255, 169, 74]], [1, [255, 241, 194]]];
  const calore = k => { k = clamp(k, 0, 1); let i = 1; while (i < CALORE.length - 1 && CALORE[i][0] < k) i++; const [a, ca] = CALORE[i - 1], [b, cb] = CALORE[i], f = (k - a) / (b - a || 1); return ca.map((v, j) => Math.round(lerp(v, cb[j], f))); };
  const caloreCss = k => 'rgb(' + calore(k).join(',') + ')';
  const NOMI = { 'M 1': 'Nebulosa Granchio', 'M 6': 'Ammasso Farfalla', 'M 7': 'Ammasso di Tolomeo', 'M 8': 'Nebulosa Laguna', 'M 11': 'Ammasso Anatra Selvatica', 'M 13': 'Ammasso di Ercole',
    'M 16': 'Nebulosa Aquila', 'M 17': 'Nebulosa Omega', 'M 20': 'Nebulosa Trifida', 'M 24': 'Nube del Sagittario', 'M 27': 'Nebulosa Manubrio', 'M 31': 'Galassia di Andromeda', 'M 33': 'Galassia del Triangolo',
    'M 42': 'Grande Nebulosa di Orione', 'M 43': 'Nebulosa di De Mairan', 'M 44': 'Presepe', 'M 45': 'Pleiadi', 'M 51': 'Galassia Vortice', 'M 57': 'Nebulosa Anello', 'M 63': 'Galassia Girasole',
    'M 64': 'Galassia Occhio Nero', 'M 65': 'Tripletto del Leone', 'M 66': 'Tripletto del Leone', 'M 76': 'Piccolo Manubrio', 'M 81': 'Galassia di Bode', 'M 82': 'Galassia Sigaro', 'M 83': 'Girandola australe',
    'M 97': 'Nebulosa Civetta', 'M 101': 'Galassia Girandola', 'M 104': 'Galassia Sombrero', 'NGC 281': 'Nebulosa Pacman', 'IC 1805': 'Nebulosa Cuore', 'IC 1848': 'Nebulosa Anima', 'IC 434': 'Testa di Cavallo',
    'NGC 2024': 'Nebulosa Fiamma', 'IC 405': 'Stella Fiammeggiante', 'IC 410': 'Nebulosa Girini', 'NGC 1499': 'Nebulosa California', 'NGC 6888': 'Nebulosa Crescente', 'NGC 6946': 'Galassia Fuochi d\u0027artificio',
    'NGC 2264': 'Albero di Natale', 'NGC 7023': 'Nebulosa Iris', 'NGC 6543': 'Occhio di Gatto', 'NGC 1977': 'Uomo che corre', 'NGC 2359': 'Elmo di Thor', 'NGC 3628': 'Galassia Hamburger', 'NGC 4631': 'Galassia Balena',
    'IC 443': 'Nebulosa Medusa', 'NGC 7380': 'Nebulosa Mago', 'IC 63': 'Fantasma di Cassiopea', 'NGC 869': 'Doppio Ammasso', 'NGC 884': 'Doppio Ammasso', 'NGC 2237': 'Nebulosa Rosetta', 'NGC 2174': 'Testa di Scimmia',
    'NGC 4565': 'Galassia Ago', 'IC 2118': 'Testa di Strega', 'NGC 3372': 'Nebulosa della Carena', 'NGC 5128': 'Centaurus A', 'NGC 2392': 'Nebulosa Eschimese', 'NGC 4038': 'Galassie Antenne', 'IC 342': 'Galassia Nascosta',
    'NGC 6334': 'Zampa di Gatto', 'NGC 6357': 'Nebulosa Aragosta', 'IC 4604': 'Rho Ophiuchi', 'NGC 7662': 'Palla di Neve Blu', 'IC 1318': 'Nebulosa di Sadr', 'NGC 6960': 'Velo occidentale', 'NGC 6992': 'Velo orientale',
    'Velo intero': 'Nebulosa Velo', 'NGC 6995': 'Velo orientale, parte sud', 'NGC 7635': 'Nebulosa Bolla', 'IC 5146': 'Nebulosa Bozzolo', 'NGC 7293': 'Nebulosa Elica', 'NGC 253': 'Galassia dello Scultore', 'NGC 7000': 'Nebulosa Nord America', 'IC 5070': 'Nebulosa Pellicano', 'IC 1396': 'Proboscide d\u0027Elefante' };
  const piega = s => String(s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/['\u2019]/g, ' ');
  const chiave = s => piega(s).replace(/\s+/g, '').replace(/^messier/, 'm');
  let CAT = null;
  const i16 = s => { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return new Int16Array(u.buffer); };
  function catalogo() {
    if (CAT) return CAT; const C = window.ALcielo; if (!C) return null;
    const cat = window.ALcat || {}, ARCH = new Set((window.ALdati ? window.ALdati.oggetti : []).map(o => o.n));
    const S = i16(C.stelle), O = i16(C.oggetti);
    const dso = C.sigle.split('|').map((s, i) => { const [id, alt] = s.split('/'), k = i * 5, mag = O[k + 3] / 10, size = O[k + 4] / 10, ac = cat[id], nome = (ac && ac[0]) || NOMI[id] || '', m = /^M \d+$/.test(id);
      return { id, alt: alt || '', ra: O[k] / 90, dec: O[k + 1] / 300, cls: O[k + 2], mag: mag > 99 ? null : mag, size, nome, tipo: (ac && ac[1]) || CLASSI[O[k + 2]], cost: ac ? ac[2] : '',
        pri: ARCH.has(id) ? 1 : (nome || m) ? 0.9 : mag < 9 ? 0.7 : (mag < 10.5 || size > 20) ? 0.5 : mag < 12 ? 0.3 : 0.1, arch: ARCH.has(id), i, k: chiave(id), k2: alt ? chiave(alt) : '', kn: piega(nome) }; });
    const perId = new Map(dso.map(o => [o.id, o]));
    const cost = C.costellazioni.map(([id, nome, ra, dec, rank]) => ({ id: 'cost:' + id, sigla: id, nome, ra, dec, rank, tipo: 'costellazione', kn: piega(nome) }));
    const stelle = C.nomiStelle.map(([ra, dec, mag, nome]) => ({ id: 'stella:' + nome, nome, ra, dec, mag, tipo: 'stella', kn: piega(nome) }));
    CAT = { S, nS: C.nStelle, dso, perId, cost, stelle, linee: C.linee };
    return CAT;
  }
  function aggiungi(lista) { const c = catalogo(); if (!c) return; for (const x of lista) { if (c.perId.has(x.id)) continue;
    const o = { id: x.id, alt: '', ra: x.ra, dec: x.dec, cls: x.cls, mag: x.mag == null ? null : x.mag, size: x.size || 10, nome: x.nome || '', tipo: x.tipo || CLASSI[x.cls], cost: x.cost || '', pri: 0.9, arch: false, i: c.dso.length, k: chiave(x.id), k2: '', kn: piega(x.nome || '') };
    c.dso.push(o); c.perId.set(o.id, o); } }
  // Ricerca: sigla esatta, poi inizio di sigla, poi nome comune; anche pianeti, Luna, costellazioni, stelle
  function cerca(q, n) {
    const c = catalogo(); if (!c) return []; const k = chiave(q), p = piega(q).trim(); if (!k) return [];
    const out = [];
    for (const o of c.dso) { let s = 0;
      if (o.k === k || o.k2 === k) s = 100; else if (o.k.startsWith(k) && /\d$/.test(k) === false) s = 70 - o.k.length; else if (o.k.startsWith(k)) s = 60 - (o.k.length - k.length) * 4;
      if (!s && o.kn && p.length > 2) { if (o.kn.startsWith(p)) s = 75; else if (o.kn.includes(' ' + p)) s = 65; else if (o.kn.includes(p)) s = 50; }
      if (s > 0) out.push([s + o.pri * 10, o]); }
    const altri = [...PIANETI.map(([kk, nome]) => ({ id: 'pianeta:' + kk, nome, tipo: 'pianeta', kn: piega(nome) })), { id: 'Luna', nome: 'Luna', tipo: 'luna', kn: 'luna' }, ...c.cost, ...c.stelle];
    for (const o of altri) { if (o.kn === p) out.push([105, o]); else if (p.length > 1 && o.kn.startsWith(p)) out.push([78, o]); else if (p.length > 3 && o.kn.includes(p)) out.push([52, o]); }
    out.sort((a, b) => b[0] - a[0]); const vis = new Set(), r = [];
    for (const [, o] of out) { if (vis.has(o.id)) continue; vis.add(o.id); r.push(o); if (r.length >= (n || 8)) break; }
    return r;
  }
  // Un oggetto dal suo nome nel motore, con la posizione all'ora t (pianeti e Luna si muovono)
  function oggetto(id, t) {
    const c = catalogo(); if (!c || !id) return null;
    if (c.perId.has(id)) return c.perId.get(id);
    if (id === 'Luna' || id === 'Sole' || id.startsWith('pianeta:')) return corpi(t).find(o => o.id === id) || null;
    if (id.startsWith('cost:')) return c.cost.find(o => o.id === id) || null;
    if (id.startsWith('stella:')) return c.stelle.find(o => o.id === id) || null;
    return null;
  }
  const cielo = { altaz, sole, luna, pianeta, lst, corpi, vec, CLASSI, CLASSI_P, COLORI, calore, caloreCss };

  // ---------- Il motore ----------
  async function crea(opz) {
    const THREE = await (window.__alTre || (window.__alTre = import(URL3)));
    const C = catalogo();
    const sito = opz.sito, profilo = opz.orizzonte || (() => 0);
    const ascolta = new Set(); const emetti = e => ascolta.forEach(f => { try { f(e); } catch (x) { console.error(x); } });
    const hex = v => (window.AL && AL.hexDi ? AL.hexDi(v) : '') || '#0b0b0e';
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(dpr); renderer.setClearColor(0x000000, 0);
    const tela = renderer.domElement; tela.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;touch-action:none';
    const lab = document.createElement('div'); lab.style.cssText = 'position:absolute;inset:0;pointer-events:none;overflow:hidden;color:var(--cielo-testo);font-family:var(--carattere);-webkit-font-smoothing:antialiased';
    const scena = new THREE.Scene(), camera = new THREE.PerspectiveCamera(42, 1, 0.002, 60);
    const cieloG = new THREE.Group(); cieloG.matrixAutoUpdate = false; scena.add(cieloG);
    const locale = new THREE.Group(); locale.matrixAutoUpdate = false; scena.add(locale);
    const U = { uUp: { value: new THREE.Vector3(0, 1, 0) }, uClip: { value: 1 } };
    const CLIP = `uniform vec3 uUp; uniform float uClip; float clipA(vec3 wp){ float a = dot(normalize(wp), uUp); return mix(1.0, smoothstep(-0.003, 0.012, a), uClip); }`;
    const add = THREE.AdditiveBlending;

    // Stelle
    const nS = C.nS, pS = new Float32Array(nS * 3), mS = new Float32Array(nS), cS = new Float32Array(nS * 3);
    const bvCol = bv => { bv = clamp(bv, -0.4, 2); const t = (bv + 0.4) / 2.4; return t < 0.3 ? [lerp(0.66, 0.92, t / 0.3), lerp(0.76, 0.95, t / 0.3), 1] : t < 0.55 ? [lerp(0.92, 1, (t - 0.3) / 0.25), lerp(0.95, 0.96, (t - 0.3) / 0.25), lerp(1, 0.86, (t - 0.3) / 0.25)] : [1, lerp(0.96, 0.72, (t - 0.55) / 0.45), lerp(0.86, 0.5, (t - 0.55) / 0.45)]; };
    for (let i = 0; i < nS; i++) { const v = vec(C.S[i * 4] / 90, C.S[i * 4 + 1] / 300); pS.set(v, i * 3); mS[i] = C.S[i * 4 + 2] / 100; cS.set(bvCol(C.S[i * 4 + 3] / 1000), i * 3); }
    const gS = new THREE.BufferGeometry(); gS.setAttribute('position', new THREE.BufferAttribute(pS, 3)); gS.setAttribute('aMag', new THREE.BufferAttribute(mS, 1)); gS.setAttribute('aCol', new THREE.BufferAttribute(cS, 3));
    const matS = new THREE.ShaderMaterial({ uniforms: { ...U, uLim: { value: 5.6 }, uPx: { value: dpr }, uBoost: { value: 1 }, uOp: { value: 1 } }, transparent: true, depthWrite: false, blending: add,
      vertexShader: `${CLIP} attribute float aMag; attribute vec3 aCol; uniform float uLim, uPx, uBoost; varying vec3 vCol; varying float vA;
        void main(){ vec4 wp = modelMatrix*vec4(position,1.0); vA = clipA(wp.xyz) * smoothstep(uLim+0.35, uLim-0.6, aMag) * clamp(0.5 + 0.18*(uLim-aMag), 0.0, 1.0);
          gl_PointSize = clamp(1.5*pow(10.0, 0.13*(uLim-aMag))*uBoost, 1.3, 12.0) * uPx; vCol = aCol; gl_Position = projectionMatrix*viewMatrix*wp; }`,
      fragmentShader: `uniform float uOp; varying vec3 vCol; varying float vA; void main(){ vec2 c = gl_PointCoord-0.5; float r = length(c)*2.0; if(r>1.0) discard; float k = exp(-r*r*6.5); gl_FragColor = vec4(mix(vCol, vec3(1.0), k*0.45), k*vA*uOp); }` });
    const stelle = new THREE.Points(gS, matS); stelle.renderOrder = 6; stelle.frustumCulled = false; cieloG.add(stelle);

    // Oggetti del cielo profondo
    const nO = C.dso.length, pO = new Float32Array(nO * 3), aO = new Float32Array(nO * 3), cO = new Float32Array(nO * 3);
    const rgb = h => { const n = parseInt(h.slice(1), 16); return [(n >> 16) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255]; };
    const CR = COLORI.map(rgb);
    C.dso.forEach((o, i) => { pO.set(vec(o.ra, o.dec), i * 3); aO.set([o.size, o.pri, o.arch ? 1 : 0], i * 3); cO.set(CR[o.cls] || CR[0], i * 3); });
    const gO = new THREE.BufferGeometry(); gO.setAttribute('position', new THREE.BufferAttribute(pO, 3)); gO.setAttribute('aDat', new THREE.BufferAttribute(aO, 3)); gO.setAttribute('aCol', new THREE.BufferAttribute(cO, 3));
    const matO = new THREE.ShaderMaterial({ uniforms: { ...U, uPpr: { value: 800 }, uPri: { value: 0.7 }, uPx: { value: dpr }, uDim: { value: 0 }, uOp: { value: 1 } }, transparent: true, depthWrite: false, blending: add,
      vertexShader: `${CLIP} attribute vec3 aDat; attribute vec3 aCol; uniform float uPpr, uPri, uPx, uDim; varying vec3 vCol; varying float vA, vRing;
        void main(){ vec4 wp = modelMatrix*vec4(position,1.0); vec4 mv = viewMatrix*wp; float px = aDat.x/60.0*0.0174533*uPpr/max(0.05, length(mv.xyz)); float vis = smoothstep(uPri-0.08, uPri, aDat.y);
          vA = clipA(wp.xyz) * vis * mix(1.0, mix(0.22, 1.0, aDat.z), uDim); vRing = smoothstep(7.0, 22.0, px);
          gl_PointSize = clamp(px*1.15, 5.0, 240.0) * uPx; vCol = mix(aCol, vec3(0.85,0.86,0.92), uDim*(1.0-aDat.z)); gl_Position = projectionMatrix*mv; }`,
      fragmentShader: `uniform float uOp; varying vec3 vCol; varying float vA, vRing; void main(){ vec2 c = gl_PointCoord-0.5; float r = length(c)*2.0; if(r>1.0) discard;
        float pt = exp(-r*r*5.0); float ring = smoothstep(0.8, 0.9, r)*smoothstep(1.0, 0.93, r); float fill = (1.0-r)*0.16; gl_FragColor = vec4(vCol, mix(pt, ring*0.85+fill, vRing)*vA*uOp*0.95); }` });
    const oggetti = new THREE.Points(gO, matO); oggetti.renderOrder = 5; oggetti.frustumCulled = false; cieloG.add(oggetti);

    // Sfera su misura: u = ra/360, v = (dec+90)/180 (per Via Lattea e mappa di calore)
    const sfera = (r, nx, ny) => { const p = [], uv = [], ix = []; for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++) { const ra = i / nx * 360, dec = -90 + j / ny * 180, v = vec(ra, dec); p.push(v[0] * r, v[1] * r, v[2] * r); uv.push(i / nx, j / ny); }
      for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) { const a = j * (nx + 1) + i, b = a + 1, c = a + nx + 1, d = c + 1; ix.push(a, b, d, a, d, c); }
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(ix); return g; };
    const gSf = sfera(1, 144, 72);
    const texVL = new THREE.TextureLoader().load(opz.viaLattea, () => segna());
    const matVL = new THREE.ShaderMaterial({ uniforms: { ...U, uTex: { value: texVL }, uOp: { value: 0.3 } }, transparent: true, depthWrite: false, blending: add, side: THREE.DoubleSide,
      vertexShader: `${CLIP} varying vec2 vUv; varying float vA; void main(){ vec4 wp = modelMatrix*vec4(position,1.0); vA = clipA(wp.xyz); vUv = uv; gl_Position = projectionMatrix*viewMatrix*wp; }`,
      fragmentShader: `uniform sampler2D uTex; uniform float uOp; varying vec2 vUv; varying float vA; void main(){ float m = pow(texture2D(uTex, vUv).r, 1.05);
        vec3 c = mix(vec3(0.5,0.58,0.86), vec3(0.98,0.88,0.74), smoothstep(0.3, 0.95, m)); gl_FragColor = vec4(c, m*uOp*vA); }` });
    const vl = new THREE.Mesh(gSf, matVL); vl.renderOrder = 1; vl.frustumCulled = false; cieloG.add(vl);
    const tCal = document.createElement('canvas'); tCal.width = 720; tCal.height = 360; const texCal = new THREE.CanvasTexture(tCal);
    const matCal = new THREE.ShaderMaterial({ uniforms: { ...U, uTex: { value: texCal }, uOp: { value: 0 } }, transparent: true, depthWrite: false, side: THREE.DoubleSide,
      vertexShader: `${CLIP} varying vec2 vUv; varying float vA; void main(){ vec4 wp = modelMatrix*vec4(position,1.0); vA = clipA(wp.xyz); vUv = uv; gl_Position = projectionMatrix*viewMatrix*wp; }`,
      fragmentShader: `uniform sampler2D uTex; uniform float uOp; varying vec2 vUv; varying float vA; void main(){ vec4 t = texture2D(uTex, vUv); gl_FragColor = vec4(t.rgb, t.a*uOp*vA); }` });
    const cal = new THREE.Mesh(sfera(0.996, 144, 72), matCal); cal.renderOrder = 2; cal.frustumCulled = false; cieloG.add(cal);

    // Linee: costellazioni, eclittica, griglie, orizzonte
    const lineMat = (col, op, dash, clip) => new THREE.ShaderMaterial({ uniforms: { uUp: U.uUp, uClip: clip === false ? { value: 0 } : U.uClip, uCol: { value: new THREE.Color(col) }, uOp: { value: op }, uDash: { value: dash || 0 } }, transparent: true, depthWrite: false,
      vertexShader: `${CLIP} attribute float aD; varying float vA, vD; void main(){ vec4 wp = modelMatrix*vec4(position,1.0); vA = clipA(wp.xyz); vD = aD; gl_Position = projectionMatrix*viewMatrix*wp; }`,
      fragmentShader: `uniform vec3 uCol; uniform float uOp, uDash; varying float vA, vD; void main(){ if(uDash > 0.0 && fract(vD*uDash) > 0.55) discard; gl_FragColor = vec4(uCol, uOp*vA); }` });
    const segmenti = (polilinee, mat, ord) => { const p = [], d = []; for (const pl of polilinee) { let acc = 0; for (let i = 0; i < pl.length - 1; i++) { const a = pl[i], b = pl[i + 1]; p.push(...a, ...b); const l = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]); d.push(acc, acc + l); acc += l; } }
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); g.setAttribute('aD', new THREE.Float32BufferAttribute(d, 1)); const m = new THREE.LineSegments(g, mat); m.renderOrder = ord || 3; m.frustumCulled = false; return m; };
    const fitta = (a, b, n) => { const out = []; for (let i = 0; i <= n; i++) { const k = i / n, v = [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)], l = Math.hypot(...v); out.push(v.map(x => x / l)); } return out; };
    const linCost = []; for (const f of C.linee) for (const ln of f) { const pts = []; for (let i = 0; i < ln.length; i += 2) pts.push(vec(ln[i], ln[i + 1])); const pl = []; for (let i = 0; i < pts.length - 1; i++) { const s = fitta(pts[i], pts[i + 1], 6); if (i) s.shift(); pl.push(...s); } linCost.push(pl); }
    const costL = segmenti(linCost, lineMat('#8d97c4', 0.42)); cieloG.add(costL);
    const eclP = []; for (let l = 0; l <= 360; l += 2) { const r = ecl2eq(l * D, 0); eclP.push(vec(r[0], r[1])); }
    const eclL = segmenti([eclP], lineMat('#e8b36a', 0.6, 22)); cieloG.add(eclL);
    const eqG = []; for (const dec of [-60, -30, 0, 30, 60]) { const pl = []; for (let ra = 0; ra <= 360; ra += 3) pl.push(vec(ra, dec)); eqG.push(pl); } for (let ra = 0; ra < 360; ra += 30) { const pl = []; for (let dec = -88; dec <= 88; dec += 4) pl.push(vec(ra, dec)); eqG.push(pl); }
    const matEqG = lineMat('#6d7bb0', 0.0); const eqGL = segmenti(eqG, matEqG); cieloG.add(eqGL);
    const azG = []; for (const alt of [30, 60]) { const pl = []; for (let az = 0; az <= 360; az += 3) pl.push(vAltAz(az, alt, 1)); azG.push(pl); } for (let az = 0; az < 360; az += 30) { const pl = []; for (let alt = 0; alt <= 84; alt += 4) pl.push(vAltAz(az, alt, 1)); azG.push(pl); }
    const matAzG = lineMat('#7f8cc0', 0.0, 0, false); const azGL = segmenti(azG, matAzG); locale.add(azGL);
    const orzP = []; for (let az = 0; az <= 360; az += 2) orzP.push(vAltAz(az, 0, 1));
    const matOrz = lineMat('#b9bfd6', 0.6, 0, false); const orzL = segmenti([orzP], matOrz, 4); locale.add(orzL);

    // Suolo, orizzonte del sito, guscio della cupola
    const scuro = new THREE.Color(hex('var(--cielo-orizzonte)'));
    const matSuolo = new THREE.ShaderMaterial({ uniforms: { uOp: { value: 1 }, uC: { value: scuro } }, transparent: true,
      vertexShader: `varying vec2 vP; void main(){ vP = position.xy; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
      fragmentShader: `uniform float uOp; uniform vec3 uC; varying vec2 vP; void main(){ float r = length(vP); float g = smoothstep(0.55, 1.0, r)*0.07; float ring = (smoothstep(0.012,0.0,abs(r-0.866)) + smoothstep(0.012,0.0,abs(r-0.5)))*0.05;
        gl_FragColor = vec4(uC + vec3(0.30,0.34,0.5)*(g+ring), uOp*0.94); }` });
    const gDisco = new THREE.CircleGeometry(1, 160); gDisco.rotateX(-Math.PI / 2);
    const suolo = new THREE.Mesh(gDisco, matSuolo); suolo.renderOrder = 0; locale.add(suolo);
    const matConca = new THREE.MeshBasicMaterial({ color: scuro, transparent: true, opacity: 0, side: THREE.BackSide, depthWrite: true });
    const conca = new THREE.Mesh(new THREE.SphereGeometry(0.992, 96, 24, 0, Math.PI * 2, Math.PI / 2 + 0.002, Math.PI / 2), matConca); conca.renderOrder = 0; locale.add(conca);
    const mP = [], mI = []; let ni = 0; for (let az = 0; az <= 360; az += 1.5) { const h = Math.max(0, profilo(az)); mP.push(...vAltAz(az, -0.3, 0.994), ...vAltAz(az, h, 0.994)); if (az > 0) mI.push(ni - 2, ni - 1, ni + 1, ni - 2, ni + 1, ni); ni += 2; }
    const gMuro = new THREE.BufferGeometry(); gMuro.setAttribute('position', new THREE.Float32BufferAttribute(mP, 3)); gMuro.setIndex(mI);
    const matMuro = new THREE.MeshBasicMaterial({ color: scuro, transparent: true, opacity: 0.96, side: THREE.DoubleSide });
    const muro = new THREE.Mesh(gMuro, matMuro); muro.renderOrder = 8; locale.add(muro);
    const bordoP = []; for (let az = 0; az <= 360; az += 1.5) bordoP.push(vAltAz(az, Math.max(0, profilo(az)), 0.993));
    const matBordo = lineMat('#a6a6b0', 0.5, 0, false); const bordo = segmenti([bordoP], matBordo, 9); locale.add(bordo);
    const matGuscio = new THREE.ShaderMaterial({ uniforms: { ...U, uOp: { value: 0.5 }, uCol: { value: new THREE.Color('#7d8fe0') } }, transparent: true, depthWrite: false, blending: add, side: THREE.FrontSide,
      vertexShader: `${CLIP} varying vec3 vN, vV; varying float vA; void main(){ vec4 wp = modelMatrix*vec4(position,1.0); vN = normalize(mat3(modelMatrix)*normal); vV = normalize(cameraPosition-wp.xyz); vA = clipA(wp.xyz); gl_Position = projectionMatrix*viewMatrix*wp; }`,
      fragmentShader: `uniform float uOp; uniform vec3 uCol; varying vec3 vN, vV; varying float vA; void main(){ float f = pow(1.0-abs(dot(normalize(vN), normalize(vV))), 3.0); gl_FragColor = vec4(uCol, f*uOp*vA); }` });
    const guscio = new THREE.Mesh(new THREE.SphereGeometry(1.004, 96, 48), matGuscio); guscio.renderOrder = 7; scena.add(guscio);

    // Immagini di Aladin (hips2fits, proiezione TAN: un piano tangente alla sfera la mostra senza deformarla)
    const imm = new Map(); const carica = new THREE.TextureLoader(); carica.setCrossOrigin('anonymous');
    const matImm = tex => new THREE.ShaderMaterial({ uniforms: { uTex: { value: tex }, uOp: { value: 0 } }, transparent: true, depthWrite: false, side: THREE.DoubleSide,
      vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
      fragmentShader: `uniform sampler2D uTex; uniform float uOp; varying vec2 vUv; void main(){ vec2 d = abs(vUv-0.5); float e = smoothstep(0.5, 0.36, max(d.x, d.y)); vec4 t = texture2D(uTex, vUv); gl_FragColor = vec4(t.rgb, uOp*e); }` });
    function immagine(o, Fmin) {
      if (!opz.rete || S.noImm || !o || o.ra == null) return null;
      const F = clamp(Math.max((o.size || 3) / 60 * 2.3, Fmin || 0), 0.3, 10), old = imm.get(o.id);
      if (old && old.stato === 'carica') { if (F > old.F * 1.15) old.voglio = F; return old; }
      if (old && old.F >= F * 0.85) return old;
      if (old && old.mesh) { cieloG.remove(old.mesh); old.mesh.geometry.dispose(); old.mesh.material.dispose(); }
      const h = F / 2 * D, c = vec(o.ra, o.dec), a = o.ra * D, d = o.dec * D;
      const n = [-Math.sin(d) * Math.cos(a), -Math.sin(d) * Math.sin(a), Math.cos(d)], e = [-Math.sin(a), Math.cos(a), 0], r = 0.995;
      const P = (x, y) => [0, 1, 2].map(i => (c[i] + x * h * e[i] + y * h * n[i]) * r);
      const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute([...P(1, 1), ...P(-1, 1), ...P(1, -1), ...P(-1, -1)], 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute([0, 1, 1, 1, 0, 0, 1, 0], 2)); g.setIndex([0, 2, 1, 1, 2, 3]);
      const voce = { id: o.id, F, stato: 'carica', mesh: null, op: 0 }; imm.set(o.id, voce);
      const url = 'https://alasky.cds.unistra.fr/hips-image-services/hips2fits?hips=' + encodeURIComponent(S.hips || 'CDS/P/DSS2/color') + '&width=1024&height=1024&fov=' + F.toFixed(4) + '&projection=TAN&coordsys=icrs&ra=' + o.ra.toFixed(5) + '&dec=' + o.dec.toFixed(5) + '&format=jpg';
      carica.load(url, tex => { if (imm.get(o.id) !== voce) { tex.dispose(); return; } tex.minFilter = THREE.LinearFilter; tex.generateMipmaps = false; const m = new THREE.Mesh(g, matImm(tex)); m.renderOrder = 6.5; m.frustumCulled = false; cieloG.add(m); voce.mesh = m; voce.stato = 'pronta'; segna(); emetti({ tipo: 'immagine', id: o.id, stato: 'pronta' }); if (voce.voglio) immagine(o, voce.voglio); },
        undefined, () => { if (imm.get(o.id) !== voce) return; voce.stato = 'errore'; emetti({ tipo: 'immagine', id: o.id, stato: 'errore' }); });
      emetti({ tipo: 'immagine', id: o.id, stato: 'carica' }); return voce;
    }

    // ---------- Stato ----------
    const S = { t: opz.t || Date.now(), vista: opz.vista || 'cupola', livello: opz.livello || 'stanotte', mostra: { cost: true, vl: true, ecl: true, griglia: false, nomi: true, corpi: true, ...(opz.mostra || {}) }, sel: null, riprese: [], ripreseK: '' };
    S.segni = []; S.campo = null; S.filoT0 = 0; S.sposta = 0;
    const campoF = c => { const wt = c.w * (c.cols - (c.cols - 1) * c.ov), ht = c.h * (c.rows - (c.rows - 1) * c.ov); return Math.hypot(wt, ht) * 1.2; };
    const cam = { A: 196, T: 26, Dd: 3.75, lAz: 160, lAlt: 32, fov: 75, b: 0, s: 0, cl: 1 };
    let pronto = false, M = matAltAz(S.t, sito.lat, sito.lon), corpiOra = corpi(S.t), sporco = true, W = 1, H = 1, host = null, anim = [], vel = { x: 0, y: 0 }, ultimoImm = '';
    const qAA = new THREE.Quaternion(), qEQ = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().set(1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1)), qF = new THREE.Quaternion(), qL = new THREE.Quaternion(), m4 = new THREE.Matrix4();
    const vistaDi = () => cam.b > 0.5 ? (cam.s > 0.5 ? 'sfera' : 'dentro') : (cam.s > 0.5 ? 'sfera' : 'cupola');
    function aggiornaQuadro() {
      M = matAltAz(S.t, sito.lat, sito.lon);
      qAA.setFromRotationMatrix(m4.set(M[0], M[1], M[2], 0, M[3], M[4], M[5], 0, M[6], M[7], M[8], 0, 0, 0, 0, 1));
      qF.copy(qAA).slerp(qEQ, cam.s); cieloG.matrix.makeRotationFromQuaternion(qF); cieloG.matrixWorldNeedsUpdate = true;
      qL.copy(qF).multiply(qAA.clone().invert()); locale.matrix.makeRotationFromQuaternion(qL); locale.matrixWorldNeedsUpdate = true;
      U.uUp.value.set(0, 1, 0).applyQuaternion(qL); U.uClip.value = cam.cl;
    }
    const mondo = q => { const e = cieloG.matrix.elements; return [e[0] * q[0] + e[4] * q[1] + e[8] * q[2], e[1] * q[0] + e[5] * q[1] + e[9] * q[2], e[2] * q[0] + e[6] * q[1] + e[10] * q[2]]; };
    const mondoL = q => { const e = locale.matrix.elements; return [e[0] * q[0] + e[4] * q[1] + e[8] * q[2], e[1] * q[0] + e[5] * q[1] + e[9] * q[2], e[2] * q[0] + e[6] * q[1] + e[10] * q[2]]; };
    const dir = (az, alt) => vAltAz(az, alt, 1);
    const azAlt = w => [norm(Math.atan2(w[0], -w[2]) / D), Math.asin(clamp(w[1], -1, 1)) / D];
    function piazza() {
      const k = cam.b, cy = lerp(-0.02, 0, cam.s), dO = dir(cam.A, cam.T), Dd = cam.Dd * Math.max(1, 3.4 / Math.max(0.3, W / H) / 3.75), pO = [dO[0] * Dd, cy + dO[1] * Dd, dO[2] * Dd], dI = dir(cam.lAz, cam.lAlt);
      camera.position.set(lerp(pO[0], 0, k), lerp(pO[1], 0, k), lerp(pO[2], 0, k));
      camera.up.set(0, 1, 0); camera.lookAt(lerp(0, dI[0], k), lerp(cy, dI[1], k), lerp(0, dI[2], k));
      camera.fov = Math.exp(lerp(Math.log(40), Math.log(cam.fov), k)); camera.aspect = W / H; if (S.sposta) camera.setViewOffset(W, H, S.sposta, 0, W, H); else camera.clearViewOffset(); camera.updateProjectionMatrix(); camera.updateMatrixWorld();
    }
    function uniformi() {
      const k = cam.b, f = camera.fov, ppr = (H / 2) / Math.tan(f / 2 * D), zoom = Math.log2(90 / Math.max(f, 0.3));
      matS.uniforms.uLim.value = lerp(5.5, clamp(5.7 + 0.75 * zoom, 5.7, 7.0), k); matS.uniforms.uBoost.value = lerp(1, clamp(1 + 0.18 * zoom, 1, 1.7), k);
      matO.uniforms.uPpr.value = ppr; matO.uniforms.uPri.value = k < 0.5 ? 0.69 : f > 60 ? 0.69 : f > 30 ? 0.5 : f > 12 ? 0.3 : 0.05;
      const rip = S.livello === 'riprese'; matO.uniforms.uDim.value = rip ? 1 : 0;
      matVL.uniforms.uOp.value = S.mostra.vl ? (rip ? 0.26 : 0.52) : 0; matCal.uniforms.uOp.value = rip ? 0.82 : 0;
      costL.material.uniforms.uOp.value = S.mostra.cost ? (rip ? 0.24 : 0.42) : 0; eclL.material.uniforms.uOp.value = S.mostra.ecl ? 0.6 : 0;
      matAzG.uniforms.uOp.value = S.mostra.griglia ? 0.22 * (1 - cam.s) : 0; matEqG.uniforms.uOp.value = S.mostra.griglia ? 0.2 * cam.s : 0;
      matOrz.uniforms.uOp.value = lerp(0.6, 0.75, cam.s); matSuolo.uniforms.uOp.value = cam.cl * (1 - cam.s) * lerp(0.62, 1, k); suolo.visible = cam.cl * (1 - cam.s) > 0.02; matSuolo.depthWrite = cam.cl > 0.5;
      matConca.opacity = cam.cl * k; conca.visible = matConca.opacity > 0.02; matMuro.opacity = lerp(0.34, 0.96, k) * cam.cl * (1 - cam.s); muro.visible = matMuro.opacity > 0.02; matMuro.depthWrite = k > 0.5; matBordo.uniforms.uOp.value = 0.5 * cam.cl * (1 - cam.s);
      matGuscio.uniforms.uOp.value = 0.55 * (1 - k);
    }

    // ---------- Mappa di calore delle riprese ----------
    function dipingiCalore() {
      const x = tCal.getContext('2d'), w = tCal.width, h = tCal.height, img = x.createImageData(w, h), acc = new Float32Array(w * h);
      const ogg = S.riprese.map(r => { const o = C.perId.get(r.id); return o && r.ore ? { v: vec(o.ra, o.dec), ore: r.ore, sg: Math.max(4.5, Math.min(9, (o.size || 10) / 60 * 1.2 + 4)) * D } : null; }).filter(Boolean);
      let mx = 0; const vx = new Float32Array(w * h * 3);
      for (let j = 0; j < h; j++) { const dec = 90 - (j + 0.5) / h * 180; for (let i = 0; i < w; i++) { const v = vec((i + 0.5) / w * 360, dec); vx.set(v, (j * w + i) * 3); } }
      for (const o of ogg) { const cmin = Math.cos(o.sg * 3.2), s2 = 2 * o.sg * o.sg; for (let p = 0; p < w * h; p++) { const c = vx[p * 3] * o.v[0] + vx[p * 3 + 1] * o.v[1] + vx[p * 3 + 2] * o.v[2]; if (c < cmin) continue; const a = Math.acos(Math.min(1, c)); acc[p] += o.ore * Math.exp(-a * a / s2); } }
      for (let p = 0; p < w * h; p++) mx = Math.max(mx, acc[p]);
      for (let p = 0; p < w * h; p++) { const k = mx ? Math.pow(acc[p] / mx, 0.62) : 0, c = calore(k); img.data.set([c[0], c[1], c[2], Math.round(255 * sstep(0.04, 0.5, k) * lerp(0.55, 1, k))], p * 4); }
      x.putImageData(img, 0, 0); texCal.needsUpdate = true; segna();
    }

    // ---------- Etichette ----------
    const pool = new Map(); let usate = new Set();
    const OMBRA = 'text-shadow:0 0 6px #000,0 0 2px #000,0 1px 2px #000;';
    function eti(key, html, x, y, op, clic, z) {
      let e = pool.get(key); if (!e) { e = document.createElement('div'); e.style.cssText = 'position:absolute;left:0;top:0;white-space:nowrap;will-change:transform;line-height:1.2;' + OMBRA; lab.appendChild(e); pool.set(key, e); e._h = ''; }
      if (e._h !== html) { e.innerHTML = html; e._h = html; }
      if (clic) { e.style.pointerEvents = 'auto'; e.style.cursor = 'pointer'; e.onclick = clic; } else { e.style.pointerEvents = 'none'; e.onclick = null; }
      e.style.transform = 'translate(' + Math.round(x) + 'px,' + Math.round(y) + 'px)'; e.style.opacity = op; e.style.zIndex = z || 1; e.style.display = 'block'; usate.add(key); return e;
    }
    const vp = new THREE.Vector3(), vc = new THREE.Vector3();
    const proietta = w => { vp.set(w[0], w[1], w[2]); vc.copy(vp).applyMatrix4(camera.matrixWorldInverse); if (vc.z > -0.001) return null; vp.project(camera); const x = (vp.x + 1) / 2 * W, y = (1 - vp.y) / 2 * H; if (x < -60 || x > W + 60 || y < -40 || y > H + 40) return null;
      const lato = cam.b < 0.5 ? (w[0] * camera.position.x + w[1] * camera.position.y + w[2] * camera.position.z > 0 ? 1 : 0.5) : 1; return { x, y, lato }; };
    const distCam = w => Math.max(0.05, Math.hypot(w[0] - camera.position.x, w[1] - camera.position.y, w[2] - camera.position.z));
    const sopra = w => cam.cl < 0.5 || (w[0] * U.uUp.value.x + w[1] * U.uUp.value.y + w[2] * U.uUp.value.z) > 0.004;
    const selClic = id => ev => { ev.stopPropagation(); emetti({ tipo: 'sel', id }); };
    const lunaSvg = (k, cresce, px) => { const p = window.AL ? AL.lunaD(Math.round(k * 100), cresce) : ''; return '<svg width="' + px + '" height="' + px + '" viewBox="-11 -11 22 22" style="display:block"><circle r="10" fill="var(--luna-scura)"/><path d="' + p + '" fill="var(--luna-chiara)"/></svg>'; };
    function etichette() {
      usate = new Set(); const posti = [], libero = (x, y, w, h) => { for (const r of posti) if (x < r[0] + r[2] && x + w > r[0] && y < r[1] + r[3] && y + h > r[1]) return false; posti.push([x, y, w, h]); return true; };
      const f = camera.fov, k = cam.b, nomi = S.mostra.nomi, rip = S.livello === 'riprese', dentro = k > 0.5, ppr = (H / 2) / Math.tan(f / 2 * D);
      // Selezione
      const so = S.sel ? oggetto(S.sel, S.t) : null;
      if (so && so.ra != null && !(S.campo && S.campo.id === S.sel)) { const w = mondo(vec(so.ra, so.dec)), p = proietta(w); if (p && sopra(w)) { const r = clamp((so.size || 0) / 60 * D * ppr / distCam(w) * 0.62, 18, 160);
        eti('sel', '<div style="position:relative;width:' + 2 * r + 'px;height:' + 2 * r + 'px;margin:' + (-r) + 'px 0 0 ' + (-r) + 'px;border-radius:50%;box-shadow:0 0 0 1.5px var(--cielo-accento),0 0 18px color-mix(in srgb, var(--cielo-accento) 45%, transparent)"><i style="position:absolute;left:50%;top:-9px;width:1.5px;height:7px;background:var(--cielo-accento)"></i><i style="position:absolute;left:50%;bottom:-9px;width:1.5px;height:7px;background:var(--cielo-accento)"></i><i style="position:absolute;top:50%;left:-9px;height:1.5px;width:7px;background:var(--cielo-accento)"></i><i style="position:absolute;top:50%;right:-9px;height:1.5px;width:7px;background:var(--cielo-accento)"></i></div>', p.x, p.y, 1, null, 5);
        posti.push([p.x - r, p.y - r, 2 * r, 2 * r]); } }
      // Il filo dell'altezza: dallo zenit all'orizzonte passando per l'oggetto scelto; nel volo si disegna partendo dall'oggetto
      if (so && so.ra != null && so.tipo !== 'costellazione' && so.tipo !== 'sole') {
        const [alt0, az0] = altaz(so.ra, so.dec, S.t, sito.lat, sito.lon), kf = S.filoT0 ? clamp((performance.now() - S.filoT0) / 1400, 0, 1) : 1, ef = 1 - Math.pow(1 - kf, 3);
        const da = alt0 + (90 - alt0) * ef, a = Math.max(cam.cl > 0.5 ? 0 : -90, alt0 - (alt0 + (cam.cl > 0.5 ? 0 : 90)) * ef);
        let d = '', su = false; for (let h = da; h >= a - 0.01; h -= 1.5) { const w = mondoL(vAltAz(az0, h, 1)), p = proietta(w); if (!p || !sopra(w)) { su = false; continue; } d += (su ? 'L' : 'M') + p.x.toFixed(1) + ' ' + p.y.toFixed(1); su = true; }
        { const w = mondoL(vAltAz(az0, a, 1)), p = proietta(w); if (p && su) d += 'L' + p.x.toFixed(1) + ' ' + p.y.toFixed(1); }
        if (d) eti('filo', '<svg width="' + Math.round(W) + '" height="' + Math.round(H) + '" style="position:absolute;left:0;top:0;overflow:visible;display:block"><path d="' + d + '" fill="none" stroke="var(--cielo-accento)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity=".18"></path><path d="' + d + '" fill="none" stroke="var(--cielo-accento)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" opacity=".95"></path></svg>', 0, 0, 1, null, 0);
        if (kf < 1) sporco = true; }
      // L'inquadratura: i rettangoli del sensore (uno o il mosaico), ruotati dal Nord verso Est
      S.campoBox = null; if (S.campo) { const c0 = S.campo, o = oggetto(c0.id, S.t);
        if (o && o.ra != null) { const c1 = vec(o.ra, o.dec), ra = o.ra * D, de = o.dec * D, n = [-Math.sin(de) * Math.cos(ra), -Math.sin(de) * Math.sin(ra), Math.cos(de)], e = [-Math.sin(ra), Math.cos(ra), 0], th = (c0.rot || 0) * D;
          const ox = Math.tan((c0.dx || 0) * D), oy = Math.tan((c0.dy || 0) * D), c = (q => { const l = Math.hypot(q[0], q[1], q[2]); return q.map(x => x / l); })([0, 1, 2].map(i => c1[i] + ox * e[i] + oy * n[i]));
          { const nz = q => { const l = Math.hypot(q[0], q[1], q[2]); return q.map(x => x / l); }, p0 = proietta(mondo(c)), pE = proietta(mondo(nz([0, 1, 2].map(i => c[i] + 0.002 * e[i])))), pN = proietta(mondo(nz([0, 1, 2].map(i => c[i] + 0.002 * n[i])))); S.campoJ = p0 && pE && pN ? { ex: (pE.x - p0.x) / 0.002, ey: (pE.y - p0.y) / 0.002, nx: (pN.x - p0.x) / 0.002, ny: (pN.y - p0.y) / 0.002 } : null; }
          const v = [0, 1, 2].map(i => Math.cos(th) * n[i] + Math.sin(th) * e[i]), u = [0, 1, 2].map(i => Math.cos(th) * e[i] - Math.sin(th) * n[i]);
          const Wr = 2 * Math.tan(c0.w * D / 2), Hr = 2 * Math.tan(c0.h * D / 2), P = (X, Y) => { const q = [0, 1, 2].map(i => c[i] + X * u[i] + Y * v[i]), l = Math.hypot(q[0], q[1], q[2]); return mondo(q.map(x => x / l)); };
          let svg = '', top = null;
          for (let i = 0; i < c0.cols; i++) for (let j = 0; j < c0.rows; j++) { const cx = (i - (c0.cols - 1) / 2) * Wr * (1 - c0.ov), cy = ((c0.rows - 1) / 2 - j) * Hr * (1 - c0.ov), pts = [];
            const ang = [[-1, 1], [1, 1], [1, -1], [-1, -1]]; let ok = true;
            for (let k2 = 0; k2 < 4 && ok; k2++) { const [x0, y0] = ang[k2], [x1, y1] = ang[(k2 + 1) % 4]; for (let t = 0; t < 6; t++) { const f2 = t / 6, w = P(cx + lerp(x0, x1, f2) * Wr / 2, cy + lerp(y0, y1, f2) * Hr / 2), p = proietta(w); if (!p || !sopra(w)) { ok = false; break; } pts.push(p); } }
            if (!ok) continue; svg += '<polygon points="' + pts.map(p => p.x.toFixed(1) + ',' + p.y.toFixed(1)).join(' ') + '" fill="color-mix(in srgb, var(--cielo-accento) 9%, transparent)" stroke="var(--cielo-accento)" stroke-width="1.6" stroke-linejoin="round"></polygon>';
            for (const p of pts) { if (!top || p.y < top.y) top = p; const b = S.campoBox || (S.campoBox = [p.x, p.y, p.x, p.y]); b[0] = Math.min(b[0], p.x); b[1] = Math.min(b[1], p.y); b[2] = Math.max(b[2], p.x); b[3] = Math.max(b[3], p.y); } }
          if (c0.c2 && svg) { const W2 = 2 * Math.tan(c0.c2.w * D / 2), H2 = 2 * Math.tan(c0.c2.h * D / 2), ang = [[-1, 1], [1, 1], [1, -1], [-1, -1]], pts = []; let ok = true;
            for (let k2 = 0; k2 < 4 && ok; k2++) { const [x0, y0] = ang[k2], [x1, y1] = ang[(k2 + 1) % 4]; for (let t = 0; t < 6; t++) { const f2 = t / 6, w = P(lerp(x0, x1, f2) * W2 / 2, lerp(y0, y1, f2) * H2 / 2), p = proietta(w); if (!p || !sopra(w)) { ok = false; break; } pts.push(p); } }
            if (ok) svg += '<polygon points="' + pts.map(p => p.x.toFixed(1) + ',' + p.y.toFixed(1)).join(' ') + '" fill="none" stroke="var(--cielo-testo)" stroke-width="1.4" stroke-dasharray="6 5" stroke-linejoin="round"></polygon>'; }
          // il lato alto del sensore: un trattino fuori dal bordo
          { const w0 = P(0, (c0.rows / 2 - (c0.rows - 1) * c0.ov / 2) * Hr), w1 = P(0, (c0.rows / 2 - (c0.rows - 1) * c0.ov / 2) * Hr * 1.12), p0 = proietta(w0), p1 = proietta(w1); if (svg && p0 && p1) svg += '<line x1="' + p0.x.toFixed(1) + '" y1="' + p0.y.toFixed(1) + '" x2="' + p1.x.toFixed(1) + '" y2="' + p1.y.toFixed(1) + '" stroke="var(--cielo-accento)" stroke-width="2" stroke-linecap="round"></line>'; }
          if (svg) { eti('campo', '<svg width="' + Math.round(W) + '" height="' + Math.round(H) + '" style="position:absolute;left:0;top:0;overflow:visible;display:block">' + svg + '</svg>', 0, 0, 1, null, 3);
            if (top && c0.nome) { eti('campoT', '<span style="display:block;transform:translate(-50%,-26px);font-size:11px;font-weight:600;padding:3px 9px;border-radius:999px;background:var(--cielo-accento);color:var(--cielo-accento-testo);text-shadow:none">' + c0.nome + '</span>', top.x, top.y, 1, null, 4); posti.push([top.x - 80, top.y - 28, 160, 22]); } } } }
      // I segni numerati della lista: il numero e la sigla, come nella lista sotto
      for (const sg of S.segni) { const o = oggetto(sg.id, S.t); if (!o || o.ra == null) continue; const w = mondo(vec(o.ra, o.dec)), p = proietta(w); if (!p || !sopra(w)) continue; const tw = String(sg.l || '').length * 7 + 30;
        eti('n:' + sg.id, '<span style="display:flex;align-items:center;gap:6px;transform:translate(-10px,-10px)"><b style="display:grid;place-items:center;min-width:20px;height:20px;padding:0 5px;box-sizing:border-box;border-radius:999px;background:var(--cielo-accento);color:var(--cielo-accento-testo);font-size:11px;font-weight:700;text-shadow:none;box-shadow:0 0 0 2px rgba(0,0,0,.5)">' + sg.n + '</b>' + (sg.l && libero(p.x + 12, p.y - 9, tw - 22, 18) ? '<span style="font-size:12px;font-weight:600">' + sg.l + '</span>' : '') + '</span>', p.x, p.y, p.lato, selClic(sg.id), 4);
        posti.push([p.x - 10, p.y - 10, 20, 20]); }
      // Riprese: anelli col numero di ore
      if (rip) { const mx = Math.max(1, ...S.riprese.map(r => r.ore || 0)), anelli = []; for (const r of S.riprese) { const o = C.perId.get(r.id); if (!o) continue; const w = mondo(vec(o.ra, o.dec)), p = proietta(w); if (!p || !sopra(w)) continue;
        const kk = (r.ore || 0) / mx, d = Math.round(16 + 16 * Math.sqrt(kk)), col = caloreCss(0.35 + 0.65 * kk), ore = r.ore == null ? '?' : (window.AL ? AL.ore(r.ore) : r.ore + ' h');
        eti('rip:' + o.id, '<span style="display:block;width:' + d + 'px;height:' + d + 'px;margin:' + (-d / 2) + 'px 0 0 ' + (-d / 2) + 'px;border-radius:50%;box-shadow:inset 0 0 0 2px ' + col + ',0 0 14px ' + col + '"></span>', p.x, p.y, p.lato, selClic(o.id), 4);
        anelli.push([kk, o, p, d, col, ore]); }
        anelli.sort((x, y) => y[0] - x[0]); for (const [, o, p, d, col, ore] of anelli) { const tw = (o.id.length + ore.length) * 7 + 24;
          if (libero(p.x - tw / 2, p.y + d / 2 + 2, tw, 20)) eti('ripT:' + o.id, '<span style="display:block;transform:translate(-50%,' + (d / 2 + 3) + 'px);font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px;background:rgba(12,12,16,.72)">' + o.id + ' <span style="color:' + col + '">' + ore + '</span></span>', p.x, p.y, p.lato, selClic(o.id), 4); }
        for (const [, , p, d] of anelli) posti.push([p.x - d / 2, p.y - d / 2, d, d]); }
      // Corpi del Sistema solare
      if (S.mostra.corpi) for (const c of corpiOra) { const w = mondo(vec(c.ra, c.dec)), p = proietta(w); if (!p || !sopra(w)) continue;
        const html = c.tipo === 'luna' ? '<span style="display:flex;align-items:center;gap:6px;transform:translate(-11px,-11px)">' + lunaSvg(c.k, c.cresce, 22) + '<span style="font-size:12px;font-weight:500">Luna ' + Math.round(c.k * 100) + '%</span></span>'
          : c.tipo === 'sole' ? '<span style="display:flex;align-items:center;gap:6px;transform:translate(-10px,-10px)"><i style="width:20px;height:20px;border-radius:50%;background:var(--sole);box-shadow:0 0 22px var(--sole)"></i><span style="font-size:12px;font-weight:500">Sole</span></span>'
          : '<span style="display:flex;align-items:center;gap:6px;transform:translate(-4px,-4px)"><i style="width:8px;height:8px;border-radius:50%;background:var(--corpo-' + c.k + ');box-shadow:0 0 8px var(--corpo-' + c.k + ')"></i><span style="font-size:12px">' + c.nome + '</span></span>';
        if (libero(p.x - 12, p.y - 12, 90, 22)) eti('c:' + c.id, html, p.x, p.y, p.lato, selClic(c.id), 3); }
      // Punti cardinali e "tu"
      const CARD = [['N', 0], ['NE', 45], ['E', 90], ['SE', 135], ['S', 180], ['SO', 225], ['O', 270], ['NO', 315]];
      for (const [n, az] of CARD) { const w = mondoL(vAltAz(az, dentro ? 1.2 : -1.5, dentro ? 1 : 1.07)), p = proietta(w); if (!p) continue; const big = n.length === 1;
        eti('card:' + n, '<span style="display:block;transform:translate(-50%,-50%);font-size:' + (big ? 15 : 11) + 'px;font-weight:' + (big ? 600 : 500) + ';color:' + (big ? 'var(--cielo-testo)' : 'var(--cielo-tenue)') + '">' + n + '</span>', p.x, p.y, (big ? 1 : 0.85) * (1 - cam.s * 0.5), null, 2); }
      if (k < 0.4 && cam.s < 0.5) { const p = proietta([0, 0, 0]); if (p) eti('tu', '<span style="display:flex;flex-direction:column;align-items:center;gap:4px;transform:translate(-50%,-5px)"><i style="width:10px;height:10px;border-radius:50%;background:var(--cielo-testo);box-shadow:0 0 0 4px rgba(244,244,246,.18)"></i><span style="font-size:11px;font-weight:600;letter-spacing:.06em">' + (sito.nome || '').toUpperCase() + '</span></span>', p.x, p.y, 1 - k * 2, null, 2); }
      // Costellazioni
      if (S.mostra.cost) for (const c of C.cost) { if (!dentro && c.rank > 1) continue; const w = mondo(vec(c.ra, c.dec)), p = proietta(w); if (!p || !sopra(w)) continue; const tw = c.nome.length * 7.4 + 8;
        if (libero(p.x - tw / 2, p.y - 7, tw, 14)) eti('k:' + c.sigla, '<span style="display:block;transform:translate(-50%,-50%);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--cielo-tenue)">' + c.nome + '</span>', p.x, p.y, 0.9 * p.lato, null, 1); }
      // Eclittica
      if (S.mostra.ecl) for (const l of [60, 150, 240, 330]) { const r = ecl2eq(l * D, 0), w = mondo(vec(r[0], r[1])), p = proietta(w); if (!p || !sopra(w)) continue; if (libero(p.x, p.y - 14, 66, 13)) eti('e:' + l, '<span style="display:block;transform:translate(4px,-14px);font-size:10px;letter-spacing:.12em;color:#e8b36a">ECLITTICA</span>', p.x, p.y, 0.85 * p.lato, null, 1); }
      // Oggetti e stelle coi nomi
      if (nomi) {
        const soglia = !dentro ? 0.89 : f > 60 ? 0.89 : f > 30 ? 0.69 : f > 12 ? 0.5 : 0.3, conNome = dentro && f < 70, maxO = !dentro ? 26 : f > 60 ? 70 : 140;
        const cand = []; for (const o of C.dso) { if (o.pri < soglia || (rip && o.arch) || (!dentro && !o.nome && !o.arch)) continue; const w = mondo(vec(o.ra, o.dec)), p = proietta(w); if (!p || !sopra(w)) continue; cand.push([o.pri + (o.mag != null ? -o.mag * 0.004 : -0.06), o, p]); }
        cand.sort((a, b) => b[0] - a[0]);
        for (const [, o, p] of cand.slice(0, maxO)) { const sub = conNome && o.nome ? o.nome : '', tw = o.id.length * 7 + (sub ? sub.length * 6.2 + 6 : 0) + 6;
          if (!libero(p.x + 6, p.y - 16, tw, 15)) continue;
          eti('o:' + o.id, '<span style="display:block;transform:translate(7px,-16px);font-size:12px;font-weight:500">' + o.id + (sub ? '<span style="font-weight:400;color:var(--cielo-tenue)"> ' + sub + '</span>' : '') + '</span>', p.x, p.y, p.lato, selClic(o.id), 2); }
        for (const s of C.stelle) { if (!dentro && s.mag > 1.4) continue; const w = mondo(vec(s.ra, s.dec)), p = proietta(w); if (!p || !sopra(w)) continue; const tw = s.nome.length * 6.4 + 6;
          if (libero(p.x + 5, p.y + 2, tw, 13)) eti('s:' + s.nome, '<span style="display:block;transform:translate(6px,3px);font-size:11px;color:var(--cielo-tenue)">' + s.nome + '</span>', p.x, p.y, 0.95 * p.lato, null, 1); }
      }
      pool.forEach((e, key) => { if (!usate.has(key) && e.style.display !== 'none') e.style.display = 'none'; });
    }

    // ---------- Immagini quando si e' vicini ----------
    function vicino() {
      if (cam.b < 0.9 || !opz.rete) { imm.forEach(v => { if (v.mesh) v.mesh.material.uniforms.uOp.value = 0; }); return; }
      const f = camera.fov, cd = new THREE.Vector3(); camera.getWorldDirection(cd);
      const ang = o => { const w = mondo(vec(o.ra, o.dec)); return Math.acos(clamp(w[0] * cd.x + w[1] * cd.y + w[2] * cd.z, -1, 1)) / D; };
      if (f < 14) { let best = null, bd = 1e9; const so = S.sel && C.perId.get(S.sel); if (so && ang(so) < f / 2) best = so;
        if (!best) for (const o of C.dso) { if (o.pri < 0.5 || o.size < 1.5) continue; const a = ang(o); if (a < f / 3 && a < bd) { bd = a; best = o; } }
        if (best) immagine(best); }
      let vis = '';
      imm.forEach(v => { if (!v.mesh) return; const o = C.perId.get(v.id), a = ang(o), op = sstep(v.F * 3.4, v.F * 1.4, f) * sstep(f * 0.9, f * 0.4, a); v.mesh.material.uniforms.uOp.value = op; if (op > 0.08) vis = v.id; });
      if (vis !== ultimoImm) { ultimoImm = vis; emetti({ tipo: 'aladin', id: vis || null }); }
    }

    // ---------- Disegno ----------
    // Il giro di disegno: requestAnimationFrame; con la pagina nascosta (catture) un timer, cosi' il cielo si disegna lo stesso
    let raf = 0, tPrec = 0, via = false, ultimoD = 0;
    const prossimo = () => { if (via) return; raf = document.visibilityState === 'hidden' ? -setTimeout(() => giro(performance.now()), 40) : requestAnimationFrame(giro); };
    function giro(ts) {
      prossimo();
       tPrec = ts;
      if (anim.length) { const now = performance.now(), fini = []; anim = anim.filter(a => { const k = clamp((now - a.t0) / a.dur, 0, 1), e = a.ease ? a.ease(k) : ease(k);
        for (const key in a.to) { const from = a.from[key], to = a.to[key]; cam[key] = key === 'fov' || key === 'Dd' ? Math.exp(lerp(Math.log(from), Math.log(to), e)) : lerp(from, to, e); }
        if (k >= 1) { if (a.fine) fini.push(a.fine); return false; } return true; }); fini.forEach(f => f()); sporco = true; }
      if (Math.abs(vel.x) + Math.abs(vel.y) > 0.01 && !giu) { muovi(vel.x, vel.y); vel.x *= 0.9; vel.y *= 0.9; sporco = true; }
      if (imgFoto && !nascosta() && sporco) viaFoto();
      if (!sporco || !host) return; sporco = false; ultimoD = ts;
      disegna();
    }
    const animaVerso = (to, dur, fine, ez) => { const from = {}; for (const k in to) { from[k] = cam[k]; if (k === 'A' || k === 'lAz') to[k] = from[k] + dAng(from[k], to[k]); }
      const rid = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches; anim.push({ from, to, t0: performance.now(), dur: rid ? 1 : dur, fine, ease: ez }); segna(); };

    // Quando il cielo e' fermo il disegno 3D si copia in un'immagine sopra la tela: chi cattura la pagina (tavole, catture) la vede; al primo gesto esce
    let imgFoto = null, vivi = 0;
    const foto = () => { if (!host) return; const q = Math.min(1, 1400 / tela.width), w = Math.round(tela.width * q), h = Math.round(tela.height * q);
      const k = document.createElement('canvas'); k.width = w; k.height = h; const g = k.getContext('2d'), fondo = hex('var(--cielo)') || '#05060a', rg = g.createRadialGradient(w / 2, h * 0.56, 0, w / 2, h * 0.56, Math.max(w, h) * 0.62);
      rg.addColorStop(0, '#0d1226'); rg.addColorStop(1, fondo); g.fillStyle = rg; g.fillRect(0, 0, w, h); g.drawImage(tela, 0, 0, w, h);
      const im = new Image(); im.alt = ''; im.setAttribute('aria-hidden', 'true'); im.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none'; im.src = k.toDataURL('image/jpeg', 0.88);
      if (imgFoto) imgFoto.replaceWith(im); else tela.after(im); imgFoto = im; vivi = 0; };
    const viaFoto = () => { if (imgFoto) { imgFoto.remove(); imgFoto = null; } };
    // Tornati visibili: la copia esce dopo una ventina di disegni dal vivo (le catture rendono visibile la pagina solo un attimo)
    document.addEventListener('visibilitychange', () => { vivi = 0; if (nascosta()) segna(); });

    // Disegno subito: con la pagina nascosta i timer rallentano, quindi il disegno non aspetta il giro e i movimenti arrivano alla fine
    const nascosta = () => document.visibilityState === 'hidden';
    function disegna() { if (!host) return; aggiornaQuadro(); piazza(); uniformi(); vicino(); renderer.render(scena, camera); etichette(); if (nascosta()) foto(); const v = vistaDi(); if (v !== S._v) { S._v = v; emetti({ tipo: 'vista', vista: v }); } }
    function segna() { sporco = true; if (!nascosta() || !pronto) return; let n = 0; while (anim.length && n++ < 8) { const a = anim.shift(); for (const k in a.to) cam[k] = a.to[k]; a.fine && a.fine(); } sporco = false; disegna(); }

    // ---------- Gesti ----------
    function muovi(dx, dy) {
      if (cam.b < 0.5) { cam.A = norm(cam.A - dx * 0.28); cam.T = clamp(cam.T + dy * 0.22, 3, 88); }
      else { const g = camera.fov / H; cam.lAz = norm(cam.lAz - dx * g * 1.1); cam.lAlt = clamp(cam.lAlt + dy * g, cam.cl > 0.5 ? -8 : -89, 89); }
      segna();
    }
    function entra() { cam.lAz = norm(cam.A + 180); cam.lAlt = clamp(cam.T * 0.45 + 12, 8, 60); cam.fov = 80; animaVerso({ b: 1 }, 1100); }
    function esci() { cam.A = norm(cam.lAz + 180); cam.T = clamp(cam.lAlt * 0.6 + 22, 14, 60); cam.Dd = 3.75; animaVerso({ b: 0 }, 1100); }
    function zoom(fat) {
      if (anim.length) return;
      if (cam.b < 0.5) { const n = cam.Dd * fat; if (n < 1.7 && fat < 1) { entra(); return; } cam.Dd = clamp(n, 1.7, 6); }
      else { const n = cam.fov * fat; if (n > 100 && fat > 1) { esci(); return; } cam.fov = clamp(n, 0.25, 100); }
      segna();
    }
    let giu = null, pt = new Map(), mosso = 0, pinza = 0, ultimo = [null, 0];
    const su = e => { if (S.trasc) { S.trasc = null; emetti({ tipo: 'campo', dx: S.campo ? S.campo.dx || 0 : 0, dy: S.campo ? S.campo.dy || 0 : 0 }); return; } pt.delete(e.pointerId); if (pt.size < 2) pinza = 0; if (pt.size) return; tela.style.cursor = 'grab';
      if (giu && mosso < 5) { const r = tela.getBoundingClientRect(), id = scegli(e.clientX - r.left, e.clientY - r.top), ora = performance.now(); emetti({ tipo: 'sel', id }); if (id && id === ultimo[0] && ora - ultimo[1] < 380) api.vola(id); ultimo = [id, ora]; }
      giu = null; };
    const dentroCampo = e => { const b = S.campoBox, r = tela.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top; return !!(S.campo && S.campo.trascina && b && S.campoJ && x > b[0] - 6 && x < b[2] + 6 && y > b[1] - 6 && y < b[3] + 6); };
    tela.addEventListener('pointermove', e => { if (!pt.size) tela.style.cursor = dentroCampo(e) ? 'move' : 'grab'; });
    tela.addEventListener('pointerdown', e => { if (dentroCampo(e)) { tela.setPointerCapture(e.pointerId); S.trasc = { x: e.clientX, y: e.clientY, dx: S.campo.dx || 0, dy: S.campo.dy || 0, J: S.campoJ }; return; } viaFoto(); tela.setPointerCapture(e.pointerId); pt.set(e.pointerId, [e.clientX, e.clientY]); giu = [e.clientX, e.clientY]; mosso = 0; vel.x = vel.y = 0; tela.style.cursor = 'grabbing'; });
    tela.addEventListener('pointermove', e => { if (S.trasc) { const T = S.trasc, J = T.J, X = e.clientX - T.x, Y = e.clientY - T.y, det = J.ex * J.ny - J.nx * J.ey; if (Math.abs(det) < 1e-6) return; const a = (X * J.ny - J.nx * Y) / det, b = (J.ex * Y - X * J.ey) / det; S.campo = { ...S.campo, dx: +(T.dx + a / D).toFixed(4), dy: +(T.dy + b / D).toFixed(4) }; S.campoK = JSON.stringify(S.campo); segna(); return; } if (!pt.has(e.pointerId)) return; const pr = pt.get(e.pointerId); pt.set(e.pointerId, [e.clientX, e.clientY]);
      if (pt.size === 2) { const [a, b] = [...pt.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]); if (pinza) zoom(pinza / d); pinza = d; mosso = 99; return; }
      const dx = e.clientX - pr[0], dy = e.clientY - pr[1]; mosso += Math.abs(dx) + Math.abs(dy); if (mosso < 4) return; muovi(dx, dy); vel.x = dx; vel.y = dy; });
    tela.addEventListener('pointerup', su); tela.addEventListener('pointercancel', su);
    tela.addEventListener('wheel', e => { e.preventDefault(); viaFoto(); zoom(Math.pow(1.0015, e.deltaY * (e.deltaMode ? 30 : 1))); }, { passive: false });
    tela.addEventListener('dblclick', e => e.preventDefault());
    tela.style.cursor = 'grab';
    function scegli(x, y) {
      let best = null, bd = 16; const f = camera.fov, soglia = matO.uniforms.uPri.value, ppr = (H / 2) / Math.tan(f / 2 * D);
      const prova = (id, ra, dec, r0) => { const w = mondo(vec(ra, dec)), p = proietta(w); if (!p || !sopra(w)) return; const d = Math.hypot(p.x - x, p.y - y) - (r0 || 0); if (d < bd) { bd = d; best = id; } };
      if (S.mostra.corpi) for (const c of corpiOra) prova(c.id, c.ra, c.dec, 4);
      for (const o of C.dso) { if (o.pri < soglia - 0.05) continue; { const w = mondo(vec(o.ra, o.dec)); prova(o.id, o.ra, o.dec, Math.min(60, o.size / 60 * D * ppr / distCam(w) * 0.5)); } }
      return best;
    }

    // ---------- API ----------
    const misura = () => { W = Math.max(1, host.clientWidth); H = Math.max(1, host.clientHeight); renderer.setSize(W, H, false); segna(); };
    const ro = new ResizeObserver(() => { if (host) misura(); });
    const api = {
      monta(el) { if (host === el) return; if (host) ro.unobserve(host); host = el; if (!el) return; el.appendChild(tela); el.appendChild(lab); ro.observe(el); misura(); },
      set(p) {
        if (p.t != null && p.t !== S.t) { S.t = p.t; corpiOra = corpi(S.t); }
        if (p.livello && p.livello !== S.livello) { const prima = S.livello; S.livello = p.livello; if (prima && cam.b < 0.5 && cam.s < 0.5) animaVerso({ T: p.livello === 'riprese' ? 58 : 26 }, 900); } if (p.mostra) S.mostra = { ...S.mostra, ...p.mostra }; if ('sel' in p) S.sel = p.sel; if (p.rete != null) opz.rete = p.rete;
        if (p.riprese) { const k = JSON.stringify(p.riprese); if (k !== S.ripreseK) { S.ripreseK = k; S.riprese = p.riprese; dipingiCalore(); } }
        if (p.vista && p.vista !== vistaDi() && !anim.length) api.vista(p.vista);
        if (p.segni) S.segni = p.segni;
        if ('immagini' in p && S.noImm !== !p.immagini) { S.noImm = !p.immagini; if (S.noImm) { for (const vv of imm.values()) if (vv.mesh) { cieloG.remove(vv.mesh); vv.mesh.geometry.dispose(); vv.mesh.material.dispose(); } imm.clear(); } }
        if (p.hips && p.hips !== (S.hips || 'CDS/P/DSS2/color')) { S.hips = p.hips; for (const vv of imm.values()) if (vv.mesh) { cieloG.remove(vv.mesh); vv.mesh.geometry.dispose(); vv.mesh.material.dispose(); } imm.clear(); const idI = S.campo ? S.campo.id : S.sel, oI = idI && oggetto(idI, S.t); if (oI && oI.size != null) immagine(oI, S.campo ? campoF(S.campo) : 0); }
        if ('campo' in p) { const k = JSON.stringify(p.campo); if (k !== S.campoK) { S.campoK = k; S.campo = p.campo; if (p.campo) { const o = oggetto(p.campo.id, S.t); if (o && o.size != null) immagine(o, campoF(p.campo)); } } }
        if (p.sposta != null) S.sposta = p.sposta;
        segna();
      },
      vista(v) {
        anim = []; const eq = v === 'sfera' ? 1 : 0;
        if (v === 'dentro') { if (cam.b < 0.5) { cam.lAz = norm(cam.A + 180); cam.lAlt = 30; cam.fov = 80; } animaVerso({ b: 1, s: 0, cl: 1 }, 1300); }
        else { if (cam.b > 0.5) { cam.A = norm(cam.lAz + 180); cam.T = v === 'sfera' ? 18 : 30; } animaVerso({ b: 0, s: eq, cl: 1 - eq, Dd: v === 'sfera' ? 3.9 : 3.75, T: v === 'sfera' ? 16 : clamp(cam.T, 20, 40) }, 1300); }
      },
      // Il volo: la cupola gira finche' l'oggetto e' dall'altra parte, poi si entra e si stringe il campo
      vola(id, Fv) {
        const o = oggetto(id, S.t); if (!o || o.ra == null) return { ok: false }; S.filoT0 = performance.now();
        aggiornaQuadro(); const w = mondo(vec(o.ra, o.dec)), [az, alt] = azAlt(w), eq = cam.s > 0.5;
        if (!eq && alt < 0) return { ok: false, sotto: true };
        const F = Fv ? clamp(Fv, 0.3, 90) : o.tipo === 'costellazione' ? 42 : o.tipo === 'luna' ? 3 : o.tipo === 'sole' ? 4 : o.tipo === 'pianeta' ? 1.6 : o.tipo === 'stella' ? 6 : clamp((o.size || 3) / 60 * 2.6, 0.45, 9);
        anim = []; vel.x = vel.y = 0; if (o.size != null && o.tipo !== 'costellazione') immagine(o, S.campo && S.campo.id === id ? campoF(S.campo) : 0);
        const lAlt = clamp(alt, eq ? -89 : -2, 89);
        if (cam.b < 0.5) { animaVerso({ A: norm(az + 180), T: clamp(alt * 0.55 + 16, 10, 62), Dd: 2.4 }, 1100, () => { cam.lAz = az; cam.lAlt = lAlt; cam.fov = 70; animaVerso({ b: 1, fov: F }, 2300, null, k => 1 - Math.pow(1 - k, 3)); }); return { ok: true, dur: 3400 }; }
        else { const mid = Math.max(cam.fov, Math.min(70, Math.abs(dAng(cam.lAz, az)) + 30)); animaVerso({ lAz: az, lAlt, fov: mid }, 900, () => animaVerso({ fov: F }, 1700, null, k => 1 - Math.pow(1 - k, 3))); }
        return { ok: true, dur: 2600 };
      },
      zoom: fat => zoom(fat),
      on(f) { ascolta.add(f); return () => ascolta.delete(f); },
      distruggi() { via = true; raf > 0 ? cancelAnimationFrame(raf) : clearTimeout(-raf); ro.disconnect(); renderer.dispose(); tela.remove(); lab.remove(); ascolta.clear(); }
    };
    { const { vista, ...resto } = opz; api.set({ ...resto, t: S.t }); }
    if (S.livello === 'riprese') cam.T = 58;
    if (S.vista !== 'cupola') { const v = S.vista; if (v === 'dentro') { cam.b = 1; cam.lAz = 160; cam.lAlt = 30; cam.fov = 80; } if (v === 'sfera') { cam.s = 1; cam.cl = 0; cam.Dd = 3.9; cam.T = 16; } }
    api._stato = () => ({ cam: { ...cam }, W, H, host: !!host, sporco, anim: anim.length, calOp: matCal.uniforms.uOp.value, cal: (() => { const d = tCal.getContext('2d').getImageData(0, 0, tCal.width, tCal.height).data; let m = 0, n = 0; for (let i = 3; i < d.length; i += 4) { if (d[i] > 20) n++; m = Math.max(m, d[i]); } return [m, n]; })(), rip: S.riprese.length, imm: [...imm.values()].map(v => [v.id, v.stato, v.F, v.mesh ? +v.mesh.material.uniforms.uOp.value.toFixed(2) : null]), fov: camera.fov });
    window.__alMotore = api; pronto = true; segna();
    prossimo();
    return api;
  }
  window.ALcupola = { crea, catalogo, cerca, oggetto, aggiungi, cielo };
})();
