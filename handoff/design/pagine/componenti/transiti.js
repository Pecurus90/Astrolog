// Transiti dei satelliti davanti al Sole e alla Luna: la striscia a terra e i posti dove metterti.
// Dati simulati: nell'app la striscia viene dall'orbita del giorno (backend), i posti da strade, orizzonte e meteo veri.
// Lo usano il Planner (Eventi) e la pagina «Mappa del transito»: stessi conti, stessi posti.
(function () {
  const SITO = { n: 'Cima Ekar', lat: 45.8486, lon: 11.5689 };
  // Paesi dell'Altopiano e dintorni (posizioni dei centri)
  const PAESI = [['Asiago', 45.8757, 11.5099], ['Gallio', 45.8893, 11.5473], ['Roana', 45.8711, 11.4699], ['Foza', 45.8967, 11.6311], ['Enego', 45.9406, 11.7056],
    ['Lusiana', 45.7856, 11.5764], ['Conco', 45.7976, 11.6082], ['Rotzo', 45.8620, 11.3980], ['Treschè Conca', 45.8530, 11.4680], ['Marostica', 45.7464, 11.6567], ['Bassano del Grappa', 45.7660, 11.7340]];
  const KX = 111.32 * Math.cos(SITO.lat * Math.PI / 180), KY = 110.57;
  const xy = (lat, lon) => [(lon - SITO.lon) * KX, (lat - SITO.lat) * KY], ll = (x, y) => [SITO.lat + y / KY, SITO.lon + x / KX];
  const hash = s => { let h = 7; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 9973; return h / 9973; };
  const BUSSOLA = ['nord', 'nord-est', 'est', 'sud-est', 'sud', 'sud-ovest', 'ovest', 'nord-ovest'];
  const verso = (dx, dy) => BUSSOLA[Math.round(((Math.atan2(dx, dy) * 180 / Math.PI + 360) % 360) / 45) % 8];
  const km = v => (v < 1 ? Math.round(v * 1000 / 10) * 10 + ' m' : v.toFixed(1).replace('.', ',') + ' km');
  // ev: { id, az (direzione della traccia a terra, gradi da nord), off (km del sito a destra della linea), strip (km), alt (altezza del corpo), met (0 sereno, 1 velato, 2 coperto, null non previsto) }
  function striscia(ev) {
    const a = ev.az * Math.PI / 180, u = [Math.sin(a), Math.cos(a)], n = [Math.cos(a), -Math.sin(a)], h = ev.strip / 2;
    const L0 = [-n[0] * ev.off, -n[1] * ev.off], L = 45;
    const pt = (s, t) => ll(L0[0] + u[0] * s + n[0] * t, L0[1] + u[1] * s + n[1] * t);
    const dist = (x, y) => (x - L0[0]) * n[0] + (y - L0[1]) * n[1];
    return { u, n, h, L0, dist, linea: [pt(-L, 0), pt(L, 0)], bordo: [pt(-L, h), pt(L, h), pt(L, -h), pt(-L, -h)],
      frecce: [-20, -8, 4, 16].map(s => ({ p: pt(s, 0), az: ev.az })) };
  }
  // Dove sei rispetto alla striscia: dentro, o di quanto e verso dove spostarti
  function stato(ev, lat, lon) {
    const S = striscia(ev), [x, y] = xy(lat, lon), d = S.dist(x, y), fuori = Math.abs(d) - S.h;
    if (fuori <= 0) return { dentro: true, d: Math.abs(d), l: 'dentro la striscia, a ' + km(Math.abs(d)) + ' dalla linea centrale' };
    const m = -Math.sign(d) * (fuori + 0.2);
    return { dentro: false, d: fuori, verso: verso(S.n[0] * m, S.n[1] * m), l: 'fuori di ' + km(fuori) + ': spostati verso ' + verso(S.n[0] * m, S.n[1] * m) };
  }
  // I posti suggeriti: dentro la striscia, entro un'ora d'auto, orizzonte libero verso il corpo, sereno all'ora; prima i siti salvati
  function posti(ev, quanti) {
    const S = striscia(ev), base = ev.met == null ? null : ev.met;
    const cand = [[SITO.n, SITO.lat, SITO.lon, true], ...PAESI.map(p => [p[0], p[1], p[2], false])].map(([n, lat, lon, salvato]) => {
      const [x, y] = xy(lat, lon), d = S.dist(x, y), dentro = Math.abs(d) <= S.h - 0.2, strada = Math.hypot(x, y) * 1.4, min = salvato ? 0 : Math.round(strada / 38 * 60 / 5) * 5 + 5;
      const hz = Math.round(4 + hash(n + 'o') * 22), oriz = hz < ev.alt - 4, k = hash(n + ev.id);
      const met = base == null ? null : base === 0 ? (k < 0.85 ? 0 : 1) : base === 1 ? (k < 0.4 ? 0 : k < 0.85 ? 1 : 2) : (k < 0.2 ? 1 : 2);
      // Il punto sulla linea centrale piu' vicino al paese: li' si va
      const t = -d, px = x + S.n[0] * t * 0.85, py = y + S.n[1] * t * 0.85, [plat, plon] = salvato && dentro ? [lat, lon] : ll(px, py);
      const dd = salvato && dentro ? Math.abs(d) : Math.abs(d) * 0.15;
      return { n: salvato ? n + ' · il tuo sito' : 'Vicino a ' + n, nb: n, salvato, lat: plat, lon: plon, dLinea: dd, min, oriz, hz, met, dentroSito: dentro,
        score: dd / S.h + min / 60 * 0.8 + (oriz ? 0 : 1.5) + (met == null ? 0 : met * 0.9) - (salvato && dentro ? 0.4 : 0) };
    }).filter(c => c.min <= 60 && (c.salvato ? c.dentroSito : true));
    return cand.sort((a, b) => a.score - b.score).slice(0, quanti || 3).map((c, i) => ({ ...c, i, linea: km(c.dLinea) + ' dalla linea', viaggio: c.min ? c.min + ' min in auto da ' + SITO.n : 'sei già qui',
      orizL: c.oriz ? 'orizzonte libero' : 'alberi fino a ' + c.hz + '°', gmaps: 'https://www.google.com/maps/dir/?api=1&destination=' + c.lat.toFixed(5) + ',' + c.lon.toFixed(5) }));
  }
  window.ALtransiti = { SITO, striscia, stato, posti, km };
})();
