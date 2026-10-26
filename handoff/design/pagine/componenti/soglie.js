// AstroLog · cosa arriva dall'app, simulato per il disegno (ADR 0020 dell'app).
// Nell'app punteggio ora per ora, cosa limita, verdetto, ore utili e giudizio di ogni misura li calcola il motore:
// qui servono solo a far muovere i dati d'esempio. Le soglie dei giudizi sono quelle dell'app, con la loro fonte.
(function () {
  const cl = v => Math.max(0, Math.min(100, v));
  const lin = (x, a, b) => x <= a ? 100 : x >= b ? 0 : (b - x) / (b - a) * 100;
  // Punti di ogni fattore (somma 100). Trasparenza = aerosol e visibilita'.
  // Notte (v13): la Luna non entra piu' nel punteggio, decide la ripresa. Giorno del Sole: com'era (da decidere con Marco).
  const PUNTI_NOTTE = { 'le nuvole': 35, 'il seeing': 30, 'la trasparenza': 12, 'la condensa': 9, 'il vento': 9, 'il jet stream': 5 };
  const PUNTI_GIORNO = { 'le nuvole': 30, 'il seeing': 25, 'il Sole basso': 15, 'la trasparenza': 10, 'la condensa': 8, 'il vento': 8, 'il jet stream': 4 };
  // La regola della Luna (v26): un'impostazione, gruppo «Luna» delle Impostazioni, letta da tutte le pagine.
  // Banda larga buona fino a {buona} %, al limite fino a {limite} %, oltre solo banda stretta; conta solo con la Luna sopra {alt}°.
  // Partenza 25 % (regola diffusa fra chi riprende), 50 % (Marco, 7/10/2026), −5° (rete TESS, cielo costante con la Luna sotto −5°, arXiv 2105.01066; ADR 0013, Marco 19/10/2026).
  const LUNA0 = { buona: 25, limite: 50, alt: -5 };
  // ── Le impostazioni dell'app: un registro solo (v26.4). Chiave, partenza, sezione delle Impostazioni, chi la legge.
  // Nell'app sono le impostazioni salvate; qui si tengono nel browser (localStorage «astrolog-impostazioni»).
  const IMP0 = {
    'generale.nome': { v: '', sez: 'Generale', legge: ['Statistiche: intestazione'] },
    'siti.predefinito': { v: 'Cima Ekar', sez: 'Siti', legge: ['conti delle notti senza sito', 'Da confermare'] },
    'meteo.obiettivo': { v: 'Deep sky', sez: 'Meteo', legge: ['Meteo: vista di partenza (Deep sky · Sole)'] },
    'luna.buona': { v: 25, u: '%', sez: 'Luna', fonte: 'regola diffusa fra chi riprende', legge: ['soglie.ripresa: Meteo, Dashboard, Notti, Planner, Piano della notte'] },
    'luna.limite': { v: 50, u: '%', sez: 'Luna', fonte: 'nessuna convenzione: scegli tu', legge: ['soglie.ripresa: Meteo, Dashboard, Notti, Planner, Piano della notte'] },
    'luna.alt': { v: -5, u: '°', sez: 'Luna', fonte: 'rete TESS: sotto −5° il cielo non sente la Luna (arXiv 2105.01066)', legge: ['soglie.ripresa: Meteo, Dashboard, Notti, Planner, Piano della notte'] },
    'planner.alt': { v: 30, u: '°', sez: 'Planner', fonte: "massa d'aria 2", legge: ['Planner: Trova, Stanotte, periodo migliore', 'Progetti', 'Dashboard: vista Progetti', 'Piano della notte: deep sky e ricerca'] },
    'planner.dur': { v: 1, u: 'h', sez: 'Planner', fonte: 'nessuna convenzione: scegli tu', legge: ['Planner: Trova'] },
    // La Luna per oggetto (v30, al posto di «Distanza dalla Luna 40°»): distanza piena a Luna piena, la meta' dopo {giorni} (formula di Target Scheduler, ACP, Voyager)
    'luna.bersaglio': { v: { larga: [120, 10], oiii: [90, 10], stretta: [60, 7] }, sez: 'Planner', legge: ['Planner: Trova e Stanotte', 'Piano della notte: proposte, filtri nel blocco, conflitti'],
      righe: [{ k: 'larga', l: 'Luna, banda larga (L, RGB, colore)', fonte: 'ACP e Telescopius; giorni: nessuna convenzione, scegli tu' }, { k: 'oiii', l: 'Luna, OIII', fonte: 'Telescopius; giorni: nessuna convenzione, scegli tu' }, { k: 'stretta', l: 'Luna, Hα, SII, dual band', fonte: 'Target Scheduler' }] },
    'planner.crep': { v: 'astronomico', sez: 'Planner', fonte: 'banda larga: buio astronomico, fisso', legge: ['Piano della notte: dove comincia la banda stretta'] },
    'planner.altMax': { v: null, u: '°', sez: 'Planner', fonte: 'vuota = spenta', legge: ['Piano della notte: conflitto «Sopra … dalle …»'] },
    'planner.pausa': { v: null, u: 'min', sez: 'Planner', fonte: 'solo se la usi nel programma di ripresa', legge: ['Piano della notte: fascia grigia attorno al transito'] },
    'flat.n': { v: 25, sez: 'Automazione', fonte: 'sotto 20 flat la calibrazione aggiunge rumore', legge: ['Piano della notte: Flat'] },
    'flat.dark': { v: true, sez: 'Automazione', legge: ['Piano della notte: Flat'] },
    'flat.quando': { v: 'ogni notte', sez: 'Automazione', legge: ['Piano della notte: Flat'] },
    'flat.ogni': { v: 3, u: 'giorni', sez: 'Automazione', legge: ['Piano della notte: Flat'] },
    'flat.finestra': { v: [-2, -7], u: '°', sez: 'Automazione', fonte: 'nessuna convenzione: scegli tu', legge: ['Piano della notte: flat di cielo'] },
    'ricerca.aavso': { v: '', sez: 'Planner', legge: ['Piano della notte: Ricerca, campagne AAVSO'] },
    'ricerca.tns': { v: '', sez: 'Planner', legge: ['Piano della notte: Ricerca, supernove'] },
    'ricerca.sn': { v: 17, u: 'mag', sez: 'Planner', fonte: 'la lista di Rochester', legge: ['Piano della notte: Ricerca, supernove'] },
    // La stagione (v49): i mesi con almeno {stagione} % delle ore del mese migliore e almeno {mese} ore, il 15 del mese
    'planner.mese': { v: 3, u: 'h', sez: 'Planner', fonte: 'nessuna convenzione: scegli tu', legge: ['Planner: stagione', 'Progetti: mesi buoni', 'Dashboard: è stagione'] },
    'planner.stagione': { v: 67, u: '%', sez: 'Planner', fonte: 'nessuna convenzione: scegli tu (due terzi)', legge: ['Planner: stagione', 'Dashboard: è stagione'] },
    'planner.altS': { v: 30, u: '°', sez: 'Planner', fonte: "massa d'aria 2", legge: ['Planner: Sistema solare', 'Piano della notte: Sistema solare'] },
    'planner.adc': { v: 35, u: '°', sez: 'Planner', fonte: 'BAA', legge: ['Planner: Sistema solare', 'Piano della notte: Sistema solare'] },
    'planner.grs': { v: 91, u: '°', sez: 'Planner', fonte: 'Sky & Telescope, da JUPOS', legge: ['Planner: Sistema solare, Giove'] },
    'planner.grsD': { v: '1/6/2026', sez: 'Planner', fonte: 'Sky & Telescope, da JUPOS', legge: ['Planner: Sistema solare, Giove'] },
    'planner.grsV': { v: 1.75, u: '° al mese', sez: 'Planner', fonte: 'Sky & Telescope, da JUPOS', legge: ['Planner: Sistema solare, Giove'] },
    // Tempi della notte (v27): tre gruppi, uguali per tutta l'app, vuoti di partenza. es = d'esempio (misurati su un setup vero), solo nei Tweaks.
    'planner.tempi': { v: {}, sez: 'Planner', fonte: 'nessuna convenzione: scegli tu', legge: ['Piano della notte: avvio, cambi, conto del blocco, flip, chiusura, margine prima di un evento fisso'],
      righe: [
        { k: 'raff', l: 'Raffreddamento della camera', u: 'min', g: 'Avvio e chiusura', es: 10 }, { k: 'unpark', l: 'Unpark', u: 'min', g: 'Avvio e chiusura', es: 0.1 },
        { k: 'apri', l: 'Apertura del tetto', u: 'min', g: 'Avvio e chiusura', es: 1, tetto: true }, { k: 'park', l: 'Park', u: 'min', g: 'Avvio e chiusura', es: 0.5 },
        { k: 'chiudi', l: 'Chiusura del tetto', u: 'min', g: 'Avvio e chiusura', es: 1, tetto: true }, { k: 'risc', l: 'Riscaldamento della camera', u: 'min', g: 'Avvio e chiusura', es: 10 },
        { k: 'punt', l: 'Puntamento e centratura', u: 'min', g: 'Per bersaglio', es: 2 }, { k: 'af', l: 'Autofocus', u: 'min', g: 'Per bersaglio', es: 3 },
        { k: 'filtro', l: 'Cambio filtro', u: 's', g: 'Durante le pose', es: 8 }, { k: 'dither', l: 'Dither col settle', u: 's', g: 'Durante le pose', es: 34 },
        { k: 'ditherOgni', l: 'Dither ogni', u: 'pose', g: 'Durante le pose', es: 3 }, { k: 'scarico', l: 'Scaricamento della posa', u: 's', g: 'Durante le pose', es: 0.5 },
        { k: 'afOgni', l: 'Un autofocus ogni', u: 'ore, stima', g: 'Durante le pose', es: 2 }, { k: 'flip', l: 'Meridian flip', u: 'min', g: 'Durante le pose', es: 3 },
        { k: 'pannello', l: 'Spostamento fra pannelli', u: 's', g: 'Durante le pose', es: 5 },
        { k: 'flat', l: 'Flat e dark-flat per filtro', u: 'min', g: 'Durante le pose', es: 2 }] },
    // Automazione della postazione (v27): solo Sì / No. Entra nei passi di Avvio e Chiusura e nell'export.
    'automazione.a': { v: { tetto: false, sensore: false, flat: false, cielo: false }, sez: 'Automazione', legge: ['Piano della notte: passi di Avvio e Chiusura, tempi del tetto, export'] },
    'automazione.b': { v: { tetto: false, sensore: false, flat: false, cielo: false }, sez: 'Automazione', legge: ['Piano della notte: passi di Avvio e Chiusura, tempi del tetto, export'] } };
  const CHIAVE = 'astrolog-impostazioni';
  const leggi = () => { try { return JSON.parse(localStorage.getItem(CHIAVE)) || {}; } catch (e) { return {}; } };
  const imp = { schema: IMP0, chiave: CHIAVE,
    get: k => { const s = leggi(); return s[k] !== undefined && s[k] !== null && s[k] !== '' ? s[k] : IMP0[k] ? IMP0[k].v : undefined; },
    set: (k, v) => { const s = leggi(); s[k] = v; try { localStorage.setItem(CHIAVE, JSON.stringify(s)); } catch (e) {} return v; },
    partenza: k => IMP0[k] ? IMP0[k].v : undefined,
    cambiata: k => { const s = leggi(); return s[k] !== undefined && JSON.stringify(s[k]) !== JSON.stringify(IMP0[k].v); } };
  const RIP = { ...LUNA0, fase: LUNA0.limite };
  const metti = c => { RIP.buona = c.buona; RIP.limite = Math.max(c.buona, c.limite); RIP.alt = c.alt; RIP.fase = RIP.limite; return RIP; };
  const salvata = () => ({ buona: +imp.get('luna.buona'), limite: +imp.get('luna.limite'), alt: +imp.get('luna.alt') });
  metti(salvata() || LUNA0);
  // usaLuna(): la regola delle Impostazioni (le varianti di prova dei Tweaks sono uscite, v32)
  const usaLuna = () => metti(salvata() || LUNA0);
  const gradi = a => (a < 0 ? '−' + (-a) : String(a)) + '°';
  const salvaLuna = c => { imp.set('luna.buona', c.buona); imp.set('luna.limite', c.limite); imp.set('luna.alt', c.alt); return metti(c); };
  const NOMI = { larga: 'banda larga', stretta: 'solo banda stretta' };
  const ripresa = (fase, alt) => fase > RIP.limite && alt >= RIP.alt ? 'stretta' : 'larga';
  // Giudizio della fase: 0 buona, 1 al limite, 2 solo banda stretta (quando la Luna conta)
  const giudizioLuna = fase => fase <= RIP.buona ? 0 : fase <= RIP.limite ? 1 : 2;
  const sopraT = () => RIP.alt ? 'sopra ' + gradi(RIP.alt) : 'sopra l\u0027orizzonte';
  const nome = (s, fase) => s.tipo === 'larga' && fase != null && giudizioLuna(fase) === 1 ? 'banda larga al limite' : NOMI[s.tipo];
  const cap = s => s[0].toUpperCase() + s.slice(1);
  // La trasparenza e' solo l'aerosol; la visibilita' non entra nel punteggio: sotto 1 km e' nebbia e blocca (Marco, 20/10/2026)
  const ALIAS = { 'l\u0027aerosol': 'la trasparenza' };
  // Nebbia: visibilita' sotto 1 km (WMO), la stessa soglia di esito.visibilita
  const nebbia = km => km != null && km < 1;
  // Misure dei frame (ADR 0022): un giudizio per misura, mai d'insieme, mai uno scarto. Fonti accanto a ogni soglia.
  // SQM ↔ Bortle: una tabella sola, usata ovunque. E' la tabella di ASTAP (bortle() in unit_sqm.pas, da Clear Dark Sky; ADR 0022), perche' lo SQM si misura come ASTAP
  // (Claude Code, 23/10/2026: torna dopo la correzione sbagliata del 21/10). Una classe vale da SQM sopra il suo limite (strettamente: 19.50 e' Bortle 6, 21.25 e' Bortle 5): 1 da 21.99, 2 da 21.89, 3 da 21.69, 4 da 21.25,
  // 5 da 19.50, 6 da 18.94, 7 da 18.38, 8 da 17.80, 9 sotto. Il 4.5 di ASTAP (20.49–21.25) vale 5.
  const BORTLE = [[21.99, 1], [21.89, 2], [21.69, 3], [21.25, 4], [19.50, 5], [18.94, 6], [18.38, 7], [17.80, 8]];
  const qn = (a, q) => { const b = a.slice().sort((x, y) => x - y); if (!b.length) return null; const i = (b.length - 1) * q, lo = Math.floor(i); return b[lo] + (b[Math.min(lo + 1, b.length - 1)] - b[lo]) * (i - lo); };
  const G = (e, t) => ({ e, s: e === 'neutra' ? '–' : ['✓', '!', '✕'][e], t });
  const MISURE = {
    // F: il limite del corredo, due pixel per stella o la diffrazione (116/D, in mm), il maggiore
    F: (scala, apertura) => Math.max(2 * scala, apertura ? 116 / apertura : 0),
    // FWHM in ″ (consenso dei forum): sotto 2 / 2-3 / 3-4 / 4-5 / oltre; le soglie sotto F salgono a F
    fwhm: (v, F) => { if (F > 3) return null; if (v < F) return G(0, 'al limite del setup');
      return v < Math.max(2, F) ? G(0, 'eccellente') : v < 3 ? G(0, 'buono') : v < 4 ? G('neutra', 'nella media') : v < 5 ? G(1, 'scarso') : G(2, 'pessimo'); },
    nonGiudicabile: F => F > 3,
    // Campionamento in px, senza voto
    camp: px => px < 1.5 ? 'sottocampionata (grave)' : px < 2 ? 'sottocampionata' : px <= 3 ? 'ideale' : 'sovracampionata',
    // Eccentricita': 0,45 dai forum, 0,71 ESO; in mezzo solo il numero
    ecc: v => v <= 0.45 ? G(0, 'rotonde') : v > 0.71 ? G(1, 'allungate') : null,
    // Tilt (ASTAP): fino al 10 % / 10-20 % / oltre
    tilt: v => v <= 10 ? G(0, 'buono') : v <= 20 ? G(1, 'incerto') : G(2, 'non adatto'),
    // Solo sul frame, contro la sua notte (stesso oggetto e filtro), con almeno 10 frame (scelta di Marco).
    // Giudizi relativi a 2,5 MAD scalato (1,4826 × MAD; Leys et al. 2013, ADR 0022; Marco, 23/10/2026): la stessa regola delle soglie della Selezione dei frame.
    minimo: 10,
    snrBasso: (v, arr) => { if (arr.length < 10) return null; const m = qn(arr, .5), mad = 1.4826 * qn(arr.map(x => Math.abs(x - m)), .5); return v < m - 2.5 * mad ? G(1, 'SNR basso per la notte') : null; },   // 2,5 MAD scalato (Leys et al. 2013)
    fuoco: (v, arr) => { if (arr.length < 10) return null; return v > qn(arr, .1) * 1.05 ? G(1, 'fuoco peggiore') : null; },   // N.I.N.A., +5 % sulle migliori
    // Il frame contro l'oggetto: stessi oggetto e filtro, tutte le notti, almeno 10 (scelta di Marco); HFD fra notti: + 2,5 MAD, non "fuoco"
    snrBassoOgg: (v, arr) => { if (arr.length < 10) return null; const m = qn(arr, .5), mad = 1.4826 * qn(arr.map(x => Math.abs(x - m)), .5); return v < m - 2.5 * mad ? G(1, 'SNR basso per l\u0027oggetto') : null; },
    hfdAltaOgg: (v, arr) => { if (arr.length < 10) return null; const m = qn(arr, .5), mad = 1.4826 * qn(arr.map(x => Math.abs(x - m)), .5); return v > m + 2.5 * mad ? G(1, 'HFD alta per l\u0027oggetto') : null; },
    // Massa d'aria sopra 2, sotto 30° (AAVSO): solo la parola
    basso: X => X > 2 ? G(1, 'oggetto basso') : null,
    bortleDi: sqm => { const r = BORTLE.find(([x]) => sqm > x); return r ? r[1] : 9; },
    cielo: (sqm, bortleSito) => bortleSito == null ? null : MISURE.bortleDi(sqm) <= bortleSito ? G(0, 'come il Bortle del sito') : G(1, 'più chiaro del Bortle del sito') };
  // ── Dal contratto del meteo (docs/domini/meteo.md): intervalli, arrotondamenti, Luna. Il verdetto NO: resta il punteggio 0-100 (Marco, 20/10/2026).
  const conto = runs => runs.reduce((k, r) => k + r.b - r.a, 0);
  const nOre = k => k === 1 ? '1 ora' : k + ' ore';
  // "dalle 21 alle 04, 7 ore" · "dalle 21 alle 01 e dalle 03 alle 05, 6 ore"; ora(h) = l'etichetta dell'ora h
  const intervallo = (runs, ora) => runs.length ? runs.map(r => 'dalle ' + ora(r.a) + ' alle ' + ora(r.b)).join(' e ') + ', ' + nOre(conto(runs)) : '';
  // Un numero scritto resta dal lato della soglia dove sta il valore vero (judge.shown_values)
  const mostra = (x, dec, q) => { const p = Math.pow(10, dec); let r = Math.round(x * p) / p; if (q && q(r) !== q(x)) r = (r > x ? Math.floor(x * p) : Math.ceil(x * p)) / p; return r; };
  // La Luna per la banda larga: pesa solo nelle ore di buio in cui e' sopra RIP.alt. altOre[h] = altezza a meta' dell'ora h.
  // 0 buona (fino a buona %), 1 banda larga al limite (fino a limite %), 2 consigliata banda stretta. Fuori se non e' mai su col buio.
  const lunaNotte = (fase, altOre, a, b, ora) => { const su = []; for (let h = a; h <= b; h++) if (altOre[h] >= RIP.alt) su.push(h); if (!su.length) return null;
    const L = giudizioLuna(fase), h0 = su[0], h1 = su[su.length - 1] + 1, tutta = h0 === a && h1 === b + 1, libera = L === 2 ? 'banda larga' : 'senza Luna';
    const quando = tutta ? 'tutta la notte' : h0 === a ? 'fino alle ' + ora(h1) : 'dalle ' + ora(h0) + (h1 <= b ? ' alle ' + ora(h1) : '');
    const resto = tutta ? '' : h0 === a ? libera + ' dalle ' + ora(h1) : libera + ' fino alle ' + ora(h0) + (h1 <= b ? ' e dalle ' + ora(h1) : '');
    const testo = 'Luna al ' + fase + '% ' + quando + (resto && L > 0 ? ' \u00b7 ' + resto : '');
    return { L, testo, su: [h0, h1], tutta, ore: h1 - h0, pill: ['buona', 'banda larga al limite', 'banda stretta'][L], tipo: L < 2 ? 'larga' : tutta ? 'stretta' : 'mista',
      breve: L < 2 ? 'Luna al ' + fase + '%' : tutta ? 'Luna al ' + fase + '%' : resto.replace(' e dalle', ' e') }; };
  // La Luna per oggetto (v30): distanza richiesta = piena / (1 + (giorni dalla piena / meta')^2). Sotto RIP.alt la Luna non conta.
  // fase in % illuminata -> giorni dalla piena (mese sinodico 29.53)
  const giorniDaPiena = pct => Math.acos(Math.max(-1, Math.min(1, 2 * pct / 100 - 1))) * 180 / Math.PI / 360 * 29.53;
  const bandaDi = k => k === 'oiii' ? 'oiii' : ['ha', 'sii', 'dual', 'nb'].includes(k) ? 'stretta' : 'larga';
  const lunaReg = () => { const v = imp.get('luna.bersaglio') || IMP0['luna.bersaglio'].v; return v; };
  const serveLuna = (banda, pct, reg) => { const r = (reg || lunaReg())[banda]; if (!r) return 0; const d = giorniDaPiena(pct); return Math.round(r[0] / (1 + Math.pow(d / r[1], 2))); };
  // Passa il filtro k a quell'ora? sep = distanza oggetto-Luna, altL = altezza della Luna
  const lunaPassa = (k, sep, pct, altL, reg) => altL < RIP.alt || sep >= serveLuna(bandaDi(k), pct, reg);
  window.ALsoglie = { nebbia,
    giorniDaPiena, bandaDi, serveLuna, lunaPassa, lunaReg,
    imp, conto, nOre, intervallo, mostra, lunaNotte, gradi,
    misure: MISURE,
    // Giudizio di una misura: 0 buono, 1 incerto, 2 non adatto. Un gradino dove l'app ne ha uno.
    esito: {
      nuvole: x => x <= 25 ? 0 : x < 50 ? 1 : 2,         // okta WMO: 25 % = 2 okta = buona
      raffiche: x => x < 29 ? 0 : 2,                     // Beaufort 5
      vento: x => x < 20 ? 0 : x < 29 ? 1 : 2,           // Beaufort 4 e 5
      seeing: x => x <= 2 ? 0 : x < 4 ? 1 : 2,            // Clear Sky Chart
      seeingGiorno: x => x <= 2 ? 0 : x < 4 ? 1 : 2,      // come la notte (Marco, 21/10)
      jet: x => x < 126 ? 0 : 2,                         // meteoblue, 35 m/s
      condensa: x => x >= 3 ? 0 : 2,                     // FAA
      aerosol: x => x < 1 ? 0 : 2,                       // NASA: sotto 0,1 limpido, da 1 molto fosco; in mezzo nessuna parola (vedi neutro)
      visibilita: x => x >= 1 ? 0 : 2,                   // WMO
      pioggia: x => x > 0 ? 2 : 0,                       // qualunque pioggia
      umidita: () => 0, pioggiaProb: () => 0 },          // solo valore, nessun giudizio
    // Fasce senza parola: barretta neutra, nessuna pillola
    neutro: { aerosol: x => x >= 0.1 && x < 1 },
    // Quanto vale ogni fattore in quell'ora, da 0 a 100 della sua parte: pieno fino alla soglia buona, zero dalla non adatta (estremi dell'ADR).
    qualita: {
      nuvole: x => lin(x, 25, 50),
      seeing: x => lin(x, 2, 4),
      seeingGiorno: x => lin(x, 2, 4),
      jet: x => lin(x, 90, 126),
      vento: x => lin(x, 20, 29),
      condensa: x => lin(-x, -3, 0),
      aerosol: x => lin(x, 0.1, 1),
      visibilita: x => x < 1 ? 0 : 100,
      pioggiaProb: () => 100, pioggiaMm: x => x > 0 ? 0 : 100, umidita: () => 100,
      soleBasso: a => a <= 0 ? 0 : cl(a / 10 * 100) },
    // ── Il punteggio 0-100 decide il verdetto in tutte le pagine (ADR 0020; Marco, 20/10/2026: supera il contratto, che va aggiornato).
    // Ora = somma dei punti dei fattori; pioggia e nuvole dal 50 % bloccano. Cosa limita = il fattore che ha perso piu' punti.
    // parti: [[nome, valore 0-100], ...]; blocca: 'pioggia', 'nuvole' (dal 50 %) o 'nebbia' (visibilita' sotto 1 km), oppure false.
    // Risponde { v, why, senza }: senza = i fattori che mancavano (per la riga «senza seeing»).
    ora: (parti, blocca) => {
      const giorno = parti.some(([k]) => k === 'il Sole basso'), PUNTI = giorno ? PUNTI_GIORNO : PUNTI_NOTTE;
      const m = {}; parti.forEach(([k, v]) => { k = ALIAS[k] || k; if (!(k in PUNTI)) return; m[k] = Math.min(m[k] ?? 100, v); });
      // Un fattore che manca (seeing senza chiave, notti passate) cede i suoi punti agli altri in proporzione (Marco, 20/10/2026); accanto si scrive «senza …».
      const ci = Object.keys(PUNTI).filter(k => k in m), senza = Object.keys(PUNTI).filter(k => !(k in m)), tot = ci.reduce((s, k) => s + PUNTI[k], 0) || 1;
      let v = 0, why = 'le nuvole', perso = -1;
      ci.forEach(k => {
        const f = m[k] / 100; v += PUNTI[k] * f / tot * 100; const p = PUNTI[k] * (1 - f); if (p > perso) { perso = p; why = k; } });
      // Pioggia, nuvole dal 50 % e nebbia (visibilita' sotto 1 km) bloccano: l'ora vale 0 (Marco, 20/10/2026, nebbia come la pioggia)
      if (blocca) return { v: 0, why: blocca === 'pioggia' ? 'la pioggia' : blocca === 'nebbia' ? 'la nebbia' : 'le nuvole', senza };
      return { v: cl(v), why, senza };
    },
    // Ora utile: qualita' da 60 (il numero grande "Ore utili", non decide il verdetto).
    utile: 60,
    // Verdetto (ADR 0020): dal punteggio della notte, la media 0-100 delle ore di buio (di giorno, delle ore della finestra).
    // Buona da 70, incerta da 40, sotto non adatta.
    livello: v => v >= 70 ? 0 : v >= 40 ? 1 : 2,
    media: arr => { const v = arr.filter(x => x != null); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; },
    // Notti passate nel disegno: il punteggio d'esempio (met.q) o, se manca, uno simulato da ore utili e nuvole. Senza Luna.
    puntoNotte: m => m.q ?? Math.round(35 + 55 * m.u / m.b - 0.3 * (m.n ?? 20)),
    // La riga accanto al punteggio quando un fattore manca: ['il seeing'] -> «senza seeing». Le notti passate non hanno il seeing (nessuna previsione salvata).
    // Solo il seeing (la brief parla di lui; la condensa di giorno e la trasparenza sotto le nuvole mancano per regola, non per un servizio).
    senzaRiga: senza => (senza || []).includes('il seeing') ? 'senza seeing' : '',
    senzaPassate: ['il seeing'],
    // I fattori che mancano in tutte le ore date (risposte di ora()): quelli da scrivere accanto al punteggio della notte
    senzaTutte: qs => { const v = qs.filter(Boolean); return v.length ? v[0].senza.filter(k => v.every(q => q.senza.includes(k))) : []; },
    // La ripresa (v13). ripresa(fase %, altezza °) -> 'larga' | 'stretta'
    sogliaRipresa: RIP, nomiRipresa: NOMI, ripresa, usaLuna, salvaLuna, giudizioLuna, sopraT,
    // Perche' cambia la ripresa: "la Luna tramonta" / "la Luna sale sopra 10°" / "sorge la Luna"
    perche: tipo => tipo === 'larga' ? (RIP.alt ? 'la Luna scende sotto ' + gradi(RIP.alt) : 'la Luna tramonta') : (RIP.alt ? 'la Luna sale sopra ' + gradi(RIP.alt) : 'sorge la Luna'),
    // Tratti della notte: alt[i] altezza della Luna al passo i (15 minuti), passi di buio da i0 a i1 (escluso)
    tratti: (alt, fase, i0, i1) => { const out = []; for (let i = i0; i < i1; i++) { const k = ripresa(fase, alt[i]), l = out[out.length - 1]; if (l && l.tipo === k) l.b = i + 1; else out.push({ tipo: k, a: i, b: i + 1, fase }); } return out; },
    oreLarga: tr => tr.filter(s => s.tipo === 'larga').reduce((h, s) => h + (s.b - s.a) / 4, 0),
    tipoNotte: tr => tr.length === 1 ? tr[0].tipo : 'mista',
    // La riga: "Banda larga 20:45–00:45 · poi solo banda stretta", "Tutta la notte banda larga". ora(i): l'orario del passo i
    frase: (tr, ora) => tr.length === 1 ? 'Tutta la notte ' + nome(tr[0], tr[0].fase)
      : tr.length === 2 ? cap(nome(tr[0], tr[0].fase)) + ' ' + ora(tr[0].a) + '–' + ora(tr[0].b) + ' · poi ' + nome(tr[1], tr[1].fase)
      : cap(tr.map(s => nome(s, s.fase) + ' ' + ora(s.a) + '–' + ora(s.b)).join(' · ')),
    nomeTratto: nome,
    // Il segno piccolo: le ore di banda larga, o "solo banda stretta"
    breve: ore => ore > 0 ? window.AL.ore(ore) + ' di banda larga' : 'solo banda stretta',
    // Notti passate e calendario (simulato): ore di banda larga da fase e crescente, Luna a declinazione 0,
    // buio di b ore centrato all'01:15, Luna sopra l'altezza della regola per h ore prima e dopo il transito (45.85° N).
    larghePassate: (pct, cresce, b = 9) => { if (pct <= RIP.limite) return b; const e = Math.acos(1 - 2 * pct / 100) * 180 / Math.PI;
      const h = Math.acos(Math.min(1, Math.sin(RIP.alt * Math.PI / 180) / Math.cos(45.85 * Math.PI / 180))) * 180 / Math.PI / 15;
      const tr = 13.3 + (cresce ? e : 360 - e) / 15, su = tr - h, giu = tr + h, b0 = 25.25 - b / 2, b1 = 25.25 + b / 2; let sopra = 0;
      [-24, 0, 24].forEach(k => { sopra += Math.max(0, Math.min(b1, giu + k) - Math.max(b0, su + k)); });
      return Math.round(Math.max(0, b - sopra) * 6) / 6 }
  };
})();
