// AstroLog · dati simulati, in un posto solo. Oggi e' mercoledi' 30 settembre 2026.
// Notti e oggetti vengono dal vecchio sistema (spostati sul 30 settembre); corredi, produzioni, pannelli e frame sono simulati.
// Il catalogo vero sta in catalogo.js (ALcat).
window.ALdati = (function () {
  const oggi = { y: 2026, m: 9, d: 30 };
  // I corredi: nome breve (filtri delle notti, produzioni) e pezzi coi nomi del vecchio sistema
  const corredi = {
    ekar: { breve: 'Notte in quota', n: 'Askar FRA400 · ASI2600MM Pro', sito: 'Cima Ekar', righe: [['ottica', 'Askar FRA400, 72/400'], ['riduttore', 'spianatore integrato'], ['ruota', 'ZWO EFW, 7 × 36 mm'], ['camera', 'ZWO ASI2600MM Pro, −10 °C'], ['montatura', 'Sky-Watcher EQ6-R Pro'], ['focheggiatore', 'ZWO EAF'], ['guida', 'cercatore 30/120 · ASI120MM Mini'], ['programma', 'N.I.N.A.'], ['campo', '3.4° × 2.2° · 1.94″/px']] },
    casa: { breve: 'Casa leggero', n: 'RedCat 51 · ASI294MC Pro', sito: 'Casa', righe: [['ottica', 'William Optics RedCat 51, 51/250'], ['riduttore', 'spianatore integrato'], ['ruota', 'cassetto da 2″, un filtro'], ['camera', 'ZWO ASI294MC Pro, a colori, −5 °C'], ['montatura', 'Sky-Watcher HEQ5 Pro'], ['focheggiatore', 'manuale'], ['guida', 'fuori asse · ASI220MM Mini'], ['programma', 'N.I.N.A.'], ['campo', '4.4° × 3.0° · 3.82″/px']] } };
  const corredoDi = sito => sito === 'Casa' ? 'casa' : 'ekar';
  // Le notti: s sito, ore di posa, fr frame, ogg [oggetto, ore], fil [filtro, frame, ore], luna [fase, %, crescente], met (meteo: u ore utili su b di buio, n nuvole %; a arriva il; tace; fuso; sb ore serene senza buio)
  // solo: la notte esiste solo in quello stato della pagina Notti. Archivio di 212 notti.
  const notti = [
    { s: 'casa', y: 2026, m: 9, d: 29, dow: 'martedì', sito: 'Casa', ore: 4.3, fr: 129, ogg: [['NGC 7000', 3.1], ['IC 5070', 1.2]], fil: [['ha-oiii', 58, 1.9], ['quad', 71, 2.4]], luna: ['Gibbosa calante', 83, 0], met: { a: '4 ott' } },
    { s: 'ekar', y: 2026, m: 9, d: 28, dow: 'lunedì', sito: 'Cima Ekar', ore: 3.4, fr: 205, ogg: [['M 31', 2.4], ['NGC 7331', 1.0], ['M 33', 0.05]], fil: [['l', 106, 1.8], ['r', 31, 0.5], ['g', 31, 0.5], ['b', 37, 0.6]], luna: ['Gibbosa calante', 90, 0], met: { a: '3 ott' } },
    { s: 'ekar', y: 2026, m: 9, d: 27, dow: 'domenica', sito: 'Cima Ekar', ore: 4.2, fr: 126, ogg: [['IC 1396', 4.2]], fil: [['ha', 70, 2.3], ['oiii', 56, 1.9]], luna: ['Gibbosa calante', 96, 0], met: { a: '2 ott' } },
    { s: 'ekar', y: 2026, m: 9, d: 24, dow: 'giovedì', sito: 'Cima Ekar', ore: 6.6, fr: 198, ogg: [['NGC 6992', 2.8], ['NGC 6960', 1.9], ['IC 1396', 1.2]], altri: 2, fil: [['l', 30, 1.0], ['ha', 89, 3.0], ['oiii', 79, 2.6]], luna: ['Gibbosa crescente', 95, 1], met: { u: 7, b: 9, n: 8 } },
    { s: 'casa', y: 2026, m: 9, d: 22, dow: 'martedì', sito: 'Casa', ore: 1.4, fr: 28, ogg: [['NGC 7635', 1.4]], fil: [['colori', 18, 0.9], ['colori-lp', 10, 0.5]], luna: ['Gibbosa crescente', 80, 1], met: { tace: 1 } },
    { s: 'calvi', y: 2026, m: 9, d: 21, dow: 'lunedì', sito: 'Rifugio Calvi', ore: 2.2, fr: 66, ogg: [['NGC 7000', 1.8], ['M 39', 0.4]], fil: [['l', 33, 1.1], ['ha', 33, 1.1]], luna: null, met: { fuso: 1 }, solo: 'sito senza fuso' },
    { s: 'ekar', y: 2026, m: 9, d: 20, dow: 'domenica', sito: 'Cima Ekar', ore: null, fr: 120, ogg: [['M 45', null]], fil: [['l', 120, null]], luna: ['Gibbosa crescente', 64, 1], met: { u: 3, b: 9, n: 44 } },
    { s: 'ekar', y: 2026, m: 9, d: 19, dow: 'sabato', sito: 'Cima Ekar', ore: 3.1, fr: 209, st: 24, ogg: [['M 33', 2.2], ['NGC 891', 0.9]], fil: [['l', 65, 1.1], ['r', 37, 0.6], ['g', 37, 0.6], ['b', 37, 0.6], ['ignoto', 9, 0.2]], luna: ['Gibbosa crescente', 56, 1], met: { u: 8, b: 9, n: 5 } },
    { s: 'casa', y: 2026, m: 9, d: 19, dow: 'sabato', sito: 'Casa', ore: 1.6, fr: 32, ogg: [['IC 5146', 1.6]], fil: [['sii-oiii', 14, 0.7], ['tri', 8, 0.4], ['colori-uvir', 10, 0.5]], luna: ['Gibbosa crescente', 56, 1], met: { u: 6, b: 9, n: 18 } },
    { s: 'casa', y: 2026, m: 9, d: 16, dow: 'mercoledì', sito: 'Casa', ore: 2.0, fr: 40, ogg: [['IC 1396', 2.0]], fil: [['ha', 20, 1.0], ['hb', 6, 0.3], ['oiii', 14, 0.7]], luna: ['Falce crescente', 28, 1], met: { u: 2, b: 9, n: 38 } },
    { s: 'ekar', y: 2026, m: 9, d: 13, dow: 'domenica', sito: 'Cima Ekar', ore: 2.7, fr: 161, ogg: [['NGC 7293', 1.1], ['M 15', 0.8], ['NGC 253', 0.6]], altri: 1, fil: [['l', 45, 0.8], ['r', 32, 0.5], ['g', 32, 0.5], ['b', 49, 0.8], ['senza', 3, 0.05]], luna: ['Falce crescente', 8, 1], met: { u: 8, b: 9, n: 4 } },
    { s: 'lofoten', y: 2026, m: 6, d: 21, dow: 'domenica', sito: 'Lofoten', ore: 2.0, fr: 121, ogg: [['M 13', 1.4], ['M 92', 0.6]], fil: [['l', 72, 1.2], ['r', 17, 0.3], ['g', 16, 0.3], ['b', 16, 0.3]], luna: ['Primo quarto', 49, 1], met: { sb: 5, n: 12 }, solo: 'senza buio' } ];
  notti.forEach(n => { n.id = n.y + '-' + String(n.m).padStart(2, '0') + '-' + String(n.d).padStart(2, '0') + '-' + n.s; n.mk = n.y * 12 + n.m - 1; });
  // Gli oggetti dell'Archivio (15 dei 240): nome, forma (cometa, mosaico), ore, frame, produzioni, filtri, ordine dei piu' recenti
  const oggetti = [
    ['C/2026 F3', 'cometa', 1.4, 86, 1, [['colori', 86, 1.4]], 3],
    ['IC 1396', null, 7.4, 202, 2, [['l', 5, 0.17], ['ha', 106, 3.87], ['hb', 6, 0.3], ['oiii', 85, 3.07]], 1],
    ['IC 5070', null, 1.2, 36, 1, [['quad', 36, 1.2]], 9],
    ['M 13', null, 4.0, 240, 1, [['l', 120, 2.0], ['r', 40, 0.7], ['g', 40, 0.7], ['b', 40, 0.7]], 12],
    ['M 27', null, 3.2, 96, 1, [['ha-oiii', 96, 3.2]], 8],
    ['M 31', null, 17.0, 1020, 2, [['l', 480, 8.0], ['r', 180, 3.0], ['g', 180, 3.0], ['b', 180, 3.0]], 2],
    ['M 33', null, 8.0, 480, 5, [['l', 160, 2.7], ['r', 50, 0.8], ['g', 50, 0.8], ['b', 50, 0.8], ['ha', 90, 1.5], ['oiii', 40, 0.7], ['sii', 40, 0.7]], 4],
    ['M 45', null, null, 120, 1, [['l', 120, null]], 7],
    ['M 57', null, 1.0, 60, 1, [['ignoto', 60, 1.0]], 13],
    ['M 103', null, 0.8, 48, 1, [['colori-lp', 48, 0.8]], 14],
    ['NGC 6992', null, 4.7, 140, 1, [['ha', 80, 2.7], ['oiii', 60, 2.0]], 5],
    ['NGC 7000', null, 8.7, 284, 3, [['ha', 140, 4.7], ['oiii', 120, 4.0], ['ignoto', 24, null]], 6],
    ['NGC 7293', null, 2.5, 76, 1, [['ha', 37, 1.2], ['oiii', 37, 1.2], ['senza', 2, 0.1]], 10],
    ['NGC 7331', null, 4.7, 280, 1, [['l', 90, 1.5], ['r', 30, 0.5], ['g', 30, 0.5], ['b', 30, 0.5], ['ha', 40, 0.7], ['oiii', 30, 0.5], ['sii', 30, 0.5]], 11],
    ['Velo intero', 'mosaico', 28.8, 864, 1, [['ha', 480, 16.0], ['oiii', 384, 12.8]], 0] ]
    .map(([n, spec, ore, fr, prod, fil, rec]) => ({ n, spec, ore, fr, prod, fil, rec }));
  // Produzioni: l'oggetto ripreso con un corredo, una per anno
  const produzioni = o => { const pr = (anno, c, ore, fr, fil) => ({ l: String(anno), sub: corredi[c].breve + ' · ' + corredi[c].sito, sito: corredi[c].sito, anno, ore, fr, fil });
    if (o.n === 'IC 1396') return [pr(2026, 'ekar', 5.4, 162, [['l', 5, 0.17], ['ha', 86, 2.87], ['oiii', 71, 2.37]]), pr(2025, 'casa', 2.0, 40, [['ha', 20, 1.0], ['hb', 6, 0.3], ['oiii', 14, 0.7]])];
    if (o.prod < 2) return null; const W = { 2: [0.58, 0.42], 3: [0.45, 0.35, 0.2], 5: [0.3, 0.25, 0.2, 0.15, 0.1] }[o.prod] || Array(o.prod).fill(1 / o.prod);
    return W.map((w, i) => { const fil = o.fil.map(([k, fr, h]) => [k, Math.max(1, Math.round(fr * w)), h == null ? null : h * w]);
      return pr(2026 - i, i % 2 === 1 ? 'casa' : 'ekar', o.ore == null ? null : o.ore * w, fil.reduce((a, f) => a + f[1], 0), fil); }); };
  // Pannelli del mosaico
  const pannelli = o => o.spec !== 'mosaico' ? null : [['NGC 6960', 216, 7.2], ['nessun oggetto', 204, 6.8], ['NGC 6992', 228, 7.6], ['NGC 6995', 216, 7.2]]
    .map(([n, fr, h]) => ({ n, fr, ore: h, fil: [['ha', Math.round(fr * 0.556), h * 0.556], ['oiii', fr - Math.round(fr * 0.556), h * 0.444]] }));
  // Le notti di IC 1396 nel riepilogo: frame per oggetto e filtro [filtro, frame, posa in s], Luna, meteo
  const ripresa = {
    '16 set': { d: 'Mercoledì 16 settembre', sito: 'Casa', cor: 'casa', start: 3.5, luna: [28, 1], met: { u: 2, b: 9, n: 44 }, oggs: { 'IC 1396': [['ha', 20, 180], ['hb', 6, 180], ['oiii', 14, 180]] } },
    '24 set': { d: 'Giovedì 24 settembre', sito: 'Cima Ekar', cor: 'ekar', start: 3, luna: [95, 1], met: { u: 7, b: 9, n: 12 }, oggs: { 'NGC 6992': [['l', 13, 120], ['ha', 38, 120], ['oiii', 33, 120]], 'NGC 6960': [['l', 9, 120], ['ha', 25, 120], ['oiii', 23, 120]], 'IC 1396': [['l', 5, 120], ['ha', 16, 120], ['oiii', 15, 120]] } },
    '27 set': { d: 'Domenica 27 settembre', sito: 'Cima Ekar', cor: 'ekar', start: 3, luna: [96, 0], met: { a: '2 ott' }, oggs: { 'IC 1396': [['ha', 70, 120], ['oiii', 56, 120]] } } };
  // Orizzonte del sito (simulato): il file di N.I.N.A., coppie «azimut altezza» in gradi, una per riga. Una casa a est, alberi a nord-ovest.
  const orizzonteFile = { 'Cima Ekar': '0 8\n20 6\n45 5\n62 6\n70 22\n78 33\n90 35\n102 33\n110 21\n118 7\n150 4\n190 9\n205 14\n220 9\n260 5\n285 9\n298 24\n315 32\n330 27\n342 12\n360 8' };
  // Si legge come l'app: righe con due numeri, almeno due; fra due punti l'altezza va per retta
  const leggiOrizzonte = txt => { const p = String(txt || '').split(/\r?\n/).map(r => r.trim().split(/[\s,;]+/).map(Number)).filter(r => r.length >= 2 && isFinite(r[0]) && isFinite(r[1])).map(r => [((r[0] % 360) + 360) % 360, r[1]]).sort((a, b) => a[0] - b[0]);
    if (p.length < 2) return null; const q = [[p[p.length - 1][0] - 360, p[p.length - 1][1]], ...p, [p[0][0] + 360, p[0][1]]];
    const f = az => { az = ((az % 360) + 360) % 360; for (let i = 0; i < q.length - 1; i++) { const a = q[i], b = q[i + 1]; if (az >= a[0] && az <= b[0]) return b[0] === a[0] ? Math.max(a[1], b[1]) : a[1] + (b[1] - a[1]) * (az - a[0]) / (b[0] - a[0]); } return p[0][1]; };
    f.punti = p; return f; };
  const orizzonte = { 'Cima Ekar': leggiOrizzonte(orizzonteFile['Cima Ekar']) };
  return { oggi, corredi, corredoDi, notti, oggetti, produzioni, pannelli, ripresa, orizzonteFile, leggiOrizzonte, orizzonte };
})();
