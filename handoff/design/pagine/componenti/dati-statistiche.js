// AstroLog · Statistiche, dati simulati (ADR 0024). Nell'app i numeri li manda il backend; qui li inventa un generatore fisso.
// Oggi e' il 30 settembre 2026. Qualita' della notte 0-100 (ADR 0020): buona da 70. Misure dei frame allo zenit (ADR 0022).
window.ALstat = (function () {
  const OGGI = { y: 2026, m: 9, d: 30 };
  const MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];
  const M3 = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic'];
  const DOW = ['dom', 'lun', 'mar', 'mer', 'gio', 'ven', 'sab'];
  const SITI = { 'Cima Ekar': { seed: 15, buone: 1, sqm: 21.76 }, 'Casa': { seed: 23, buone: 0.8, sqm: 20.15 }, 'Passo Coe': { seed: 37, buone: 0.9, sqm: 21.35 } };
  const SETUP = {
    newton: { n: 'Newton 200/800 · ASI533MC Pro', scala: 0.97, colori: true, bias: true, tipo: [['galassie', 0.6], ['ammassi', 0.25], ['nebulose', 0.15]] },
    redcat: { n: 'RedCat 51 · ASI294MC Pro', scala: 3.82, colori: true, bias: true, tipo: [['nebulose', 0.8], ['ammassi', 0.1], ['galassie', 0.1]] },
    fra: { n: 'Askar FRA400 · ASI2600MM Pro', scala: 1.94, bias: true, tipo: [['nebulose', 0.6], ['galassie', 0.3], ['ammassi', 0.1]] },
    fra07: { n: 'Askar FRA400 · ASI2600MM Pro · riduttore 0.7×', scala: 2.77, bias: true, tipo: [['nebulose', 0.85], ['galassie', 0.15]] } };
  const ORDINE = ['newton', 'redcat', 'fra', 'fra07'];
  const POOL = { nebulose: ['IC 1396', 'NGC 7000', 'NGC 6992', 'NGC 6960', 'IC 5070', 'NGC 7635', 'IC 5146', 'M 42', 'NGC 2237', 'IC 434', 'M 16', 'NGC 6888', 'Sh2-129', 'IC 1805', 'IC 1848', 'M 8'],
    galassie: ['M 31', 'M 33', 'NGC 7331', 'NGC 891', 'M 81', 'M 82', 'M 101', 'M 51', 'NGC 4565', 'M 63', 'M 106', 'NGC 2403'], ammassi: ['M 13', 'M 92', 'M 45', 'M 15', 'M 39', 'NGC 869', 'M 3', 'M 5'] };
  const PG = [0.09, 0.08, 0.07, 0.07, 0.06, 0.08, 0.10, 0.10, 0.11, 0.14, 0.08, 0.08];   // probabilita' di una notte buona, per mese
  const ORA = [-0.72, -0.31, -0.12, -0.03, 0, 0, -0.03, -0.14, -0.46];                     // SQM dalle 21 alle 05, scarto dal mezzo della notte
  const ts = (y, m, d) => Date.UTC(y, m - 1, d);
  const doyDi = (y, m, d) => Math.round((ts(y, m, d) - ts(y, 1, 1)) / 864e5);
  const buio = doy => Math.max(3.2, 7.6 + 4.1 * Math.cos(2 * Math.PI * (doy - 355) / 365));
  const luna = t => { const jd = t / 864e5 + 2440587.5, f = (((jd - 2451550.1) / 29.530588) % 1 + 1) % 1; return (1 - Math.cos(2 * Math.PI * f)) / 2; };
  const med = a => { if (!a.length) return null; const b = a.slice().sort((x, y) => x - y), i = (b.length - 1) / 2; return (b[Math.floor(i)] + b[Math.ceil(i)]) / 2; };
  const cache = {};

  function genera(sito, var_) {
    const k = sito + '|' + var_; if (cache[k]) return cache[k];
    const S = SITI[sito] || SITI['Cima Ekar'], primo = var_ === 'primo anno', uno = var_ === 'un setup solo';
    let seed = S.seed * 7919 + (primo ? 3 : 0) + (uno ? 5 : 0); const r = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
    let seed2 = seed ^ 0x5bd1e995; const r2 = () => { seed2 = (seed2 * 1103515245 + 12345) >>> 0; return seed2 / 4294967296; };   // misure aggiunte (v31.1): non cambiano le notti
    const pick = w => { let x = r() * w.reduce((s, e) => s + e[1], 0); for (const e of w) { x -= e[1]; if (x <= 0) return e[0]; } return w[w.length - 1][0]; };
    const APP = primo ? { y: 2026, m: 1, d: 8 } : { y: 2024, m: 3, d: 12 };
    const tApp = ts(APP.y, APP.m, APP.d), t0 = primo ? tApp : ts(2021, 1, 1), tOggi = ts(OGGI.y, OGGI.m, OGGI.d), tEnd = ts(OGGI.y, 12, 31);
    const setupDi = t => { if (uno) return 'fra';
      if (sito === 'Casa') return t >= ts(2022, 6, 4) ? pick([['redcat', 0.75], [t < ts(2024, 3, 12) ? 'newton' : 'fra', 0.25]]) : 'newton';
      if (t < ts(2024, 3, 12)) return t >= ts(2022, 6, 4) ? pick([['newton', 0.8], ['redcat', 0.2]]) : 'newton';
      if (t >= ts(2026, 5, 16)) return pick([['fra', 0.45], ['fra07', 0.4], ['redcat', 0.15]]);
      return pick([['fra', 0.82], ['redcat', 0.18]]); };
    const giorni = [];
    for (let t = t0; t <= tEnd; t += 864e5) {
      const D = new Date(t), y = D.getUTCFullYear(), m = D.getUTCMonth() + 1, d = D.getUTCDate(), doy = doyDi(y, m, d);
      const g = { y, m, d, doy, dow: DOW[D.getUTCDay()], t, futuro: t > tOggi, buio: buio(doy) };
      giorni.push(g); if (g.futuro) continue;
      g.q = r() < PG[m - 1] * S.buone ? 70 + Math.floor(r() * 26) : Math.floor(70 * Math.pow(r(), 0.8));
      g.buona = g.q >= 70; g.seeingOk = t >= tApp;
      if (g.seeingOk) g.seeing = Math.round((1.6 + 1.3 * r2() + (m >= 6 && m <= 8 ? -0.15 : 0)) * 10) / 10;
      const pOut = g.buona ? (primo ? 0.62 : 0.36 + 0.055 * (y - 2021)) : g.q >= 45 ? 0.08 : 0.01;
      if (r() >= pOut) continue;
      g.out = true;
      g.ore = Math.round(g.buio * (g.buona ? 0.5 + 0.38 * r() : 0.12 + 0.3 * r()) * 12) / 12;
      const su = setupDi(t), SU = SETUP[su], tipo = pick(SU.tipo); g.setup = su;
      const pool = POOL[tipo], no = g.ore > 3.5 ? 1 + Math.floor(r() * 3) : 1; g.ogg = []; for (let i = 0; i < no; i++) { const o = pool[Math.floor(r() * pool.length)]; if (!g.ogg.includes(o)) g.ogg.push(o); }
      const fw = SU.colori ? (tipo === 'nebulose' ? [[r() < 0.7 ? 'ha-oiii' : 'colori', 1]] : [['colori', 1]])
        : tipo === 'nebulose' ? [['ha', 0.45], ['oiii', 0.35], ['sii', r() < 0.6 ? 0.2 : 0]] : tipo === 'galassie' ? [['l', 0.55], ['r', 0.15], ['g', 0.15], ['b', 0.15]] : [['l', 0.4], ['r', 0.2], ['g', 0.2], ['b', 0.2]];
      const tot = fw.reduce((s, f) => s + f[1], 0);
      g.fil = fw.filter(f => f[1] > 0).map(([f, w]) => { const h = g.ore * w / tot, exp = ['ha', 'oiii', 'sii', 'ha-oiii'].includes(f) ? 300 : 120; return [f, h, Math.max(1, Math.round(h * 3600 / exp))]; });
      g.pose = g.fil.reduce((s, f) => s + f[2], 0);
      // Misure dei frame, allo zenit. Il progresso: la guida e il fuoco migliorano negli anni, la banda si stringe.
      const p = Math.min(1, Math.max(0, (t - ts(2021, 1, 1)) / (ts(2026, 9, 30) - ts(2021, 1, 1)))), estate = m >= 6 && m <= 8 ? -0.15 : 0;
      const atm = 1.85 + 0.85 * r() + estate, err = 2.3 * (1 - p) + 0.45;
      const f = Math.sqrt(atm * atm + Math.pow(1.6 * SU.scala, 2) + err * err), sp = f * (0.05 + 0.13 * (1 - p)) * (0.7 + 0.6 * r());
      g.fwhm = { med: f, q1: f - sp, q3: f + sp * 1.2, n: g.pose };
      const h = f * 1.17 + 0.1 * (r() - 0.5), hs = sp * 1.15; g.hfd = { med: h, q1: h - hs, q3: h + hs * 1.2, n: g.pose };
      const e = 0.6 - 0.2 * p + 0.08 * (r() - 0.5), es = 0.04 + 0.06 * (1 - p); g.ecc = { med: e, q1: e - es, q3: e + es, n: g.pose };
      r2(); r2(); // stelle e fondo uscite (v31.3): il dado si tira lo stesso, cosi' gli altri numeri simulati non cambiano
      g.seeing = g.seeingOk ? Math.round((atm - 0.25 + 0.3 * (r() - 0.5)) * 10) / 10 : null;
      // Cielo: solo dai frame L, senza filtro o a colori
      const ill = luna(t); g.luna = ill;
      if (g.fil.some(x => x[0] === 'l' || x[0] === 'colori')) {
        const base = S.sqm + (m >= 6 && m <= 8 ? -0.12 : 0) + 0.18 * (r() - 0.5);
        if (ill < 0.9) g.sqmGiu = base;
        if (ill > 0.12) g.sqmSu = base - 0.4 - 1.5 * ill + 0.1 * (r() - 0.5);
        if (g.sqmGiu != null) g.ore9 = ORA.map(o => base + o + 0.08 * (r() - 0.5));
      }
    }
    const anni = [...new Set(giorni.filter(g => g.out).map(g => g.y))].sort();
    const app = { ...APP, l: APP.d + ' ' + MESI[APP.m - 1] + ' ' + APP.y };
    const senzaMassa = primo ? {} : { 2022: 37, 2023: 12 };
    return (cache[k] = { giorni, anni, app, senzaMassa, sito });
  }

  // I conti: un periodo (anno o tutto), fino a un giorno dell'anno, con un setup o tutti
  function conti(G, anno, setup, finoDoy) {
    const gg = G.giorni.filter(g => !g.futuro && (anno === 'tutto' || g.y === anno) && (finoDoy == null || g.doy <= finoDoy));
    const usa = g => g.out && (setup === 'tutti' || g.setup === setup);
    const out = gg.filter(usa), buone = gg.filter(g => g.buona);
    const ore = out.reduce((s, g) => s + g.ore, 0), buioOut = out.reduce((s, g) => s + g.buio, 0);
    return { buone: buone.length, sfruttate: buone.filter(usa).length, uscite: out.length, ore, pose: out.reduce((s, g) => s + g.pose, 0), resa: buioOut ? ore / buioOut : null, out, gg };
  }
  return { OGGI, MESI, M3, DOW, SITI: Object.keys(SITI), SETUP, ORDINE, genera, conti, med, doyDi, ts };
})();
