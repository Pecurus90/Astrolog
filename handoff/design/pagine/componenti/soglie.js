// AstroLog · cosa arriva dall'app, simulato per il disegno (ADR 0020 dell'app).
// Nell'app trasparenza ora per ora, verdetto, ore di posa e giudizio di ogni misura li calcola il motore:
// qui servono solo a far muovere i dati d'esempio. Le soglie dei giudizi sono quelle dell'app, con la loro fonte.
(function () {
  const cl = v => Math.max(0, Math.min(100, v));
  const lin = (x, a, b) => x <= a ? 100 : x >= b ? 0 : (b - x) / (b - a) * 100;
  // La regola della Luna (v26): un'impostazione, gruppo «Luna» delle Impostazioni, letta da tutte le pagine.
  // Banda larga buona fino a {buona} %, al limite fino a {limite} %, oltre solo banda stretta; conta solo con la Luna sopra {alt}°.
  // Partenza 25% (regola di ING: buio sotto 0,25), 65% (regola di ING: grigio fino a 0,65) e 0°, la Luna conta dall'orizzonte, quando sorge (ADR 0034). −5° (rete TESS, arXiv 2105.01066) resta una scelta.
  const LUNA0 = { buona: 25, limite: 65, alt: 0 };
  // ── Le impostazioni dell'app: un registro solo (v26.4). Chiave, partenza, sezione delle Impostazioni, chi la legge.
  // Nell'app sono le impostazioni salvate; qui si tengono nel browser (localStorage «astrolog-impostazioni»).
  const IMP0 = {
    'generale.nome': { v: '', sez: 'Generale', legge: ['Statistiche: intestazione'] },
    'siti.predefinito': { v: 'Cima Ekar', sez: 'Siti', legge: ['conti delle notti senza sito', 'Da confermare'] },
    'meteo.obiettivo': { v: 'Deep sky', sez: 'Meteo', legge: ['Meteo: vista di partenza (Deep sky · Sole)'] },
    'luna.buona': { v: 25, u: '%', sez: 'Luna', fonte: 'regola di ING: buio sotto 0,25', legge: ['soglie.ripresa: Meteo, Dashboard, Notti, Planner, Piano della notte'] },
    'luna.limite': { v: 65, u: '%', sez: 'Luna', fonte: 'regola di ING: grigio fino a 0,65', legge: ['soglie.ripresa: Meteo, Dashboard, Notti, Planner, Piano della notte'] },
    'luna.alt': { v: 0, u: '°', sez: 'Luna', fonte: 'dall\u0027orizzonte, quando sorge', legge: ['soglie.ripresa: Meteo, Dashboard, Notti, Planner, Piano della notte'] },
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
    // I mesi buoni (v49; «stagione» fino alla v71): i mesi con almeno {stagione} % delle ore del mese migliore e almeno {mese} ore, il 15 del mese
    'planner.mese': { v: 3, u: 'h', sez: 'Planner', fonte: 'nessuna convenzione: scegli tu', legge: ['Planner: mesi buoni', 'Progetti: mesi buoni', 'Dashboard: mesi buoni'] },
    'planner.stagione': { v: 67, u: '%', sez: 'Planner', fonte: 'nessuna convenzione: scegli tu (due terzi)', legge: ['Planner: mesi buoni', 'Dashboard: mesi buoni'] },
    // Crea (v71, brief 8.7): le ore di un progetto nuovo, divise fra i filtri dello schema, e la posa di partenza per banda
    'planner.oreNuovo': { v: 10, u: 'h', sez: 'Planner', fonte: 'nessuna convenzione: scegli tu', legge: ['Planner: Pose di un progetto nuovo'] },
    'planner.posaL': { v: 120, u: 's', sez: 'Planner', fonte: 'nessuna convenzione: dipende da cielo e camera', legge: ['Planner: Pose, banda larga'] },
    'planner.posaS': { v: 300, u: 's', sez: 'Planner', fonte: 'nessuna convenzione: dipende da cielo e camera', legge: ['Planner: Pose, banda stretta'] },
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
        { k: 'punt', l: 'Puntamento e centratura', u: 'min', g: 'Per oggetto', es: 2 }, { k: 'af', l: 'Autofocus', u: 'min', g: 'Per oggetto', es: 3 },
        { k: 'filtro', l: 'Cambio filtro', u: 's', g: 'Durante i frame', es: 8 }, { k: 'dither', l: 'Dither col settle', u: 's', g: 'Durante i frame', es: 34 },
        { k: 'ditherOgni', l: 'Dither ogni', u: 'pose', g: 'Durante i frame', es: 3 }, { k: 'scarico', l: 'Scaricamento della posa', u: 's', g: 'Durante i frame', es: 0.5 },
        { k: 'afOgni', l: 'Un autofocus ogni', u: 'ore, stima', g: 'Durante i frame', es: 2 }, { k: 'flip', l: 'Meridian flip', u: 'min', g: 'Durante i frame', es: 3 },
        { k: 'pannello', l: 'Spostamento fra pannelli', u: 's', g: 'Durante i frame', es: 5 },
        { k: 'flat', l: 'Flat e dark-flat per filtro', u: 'min', g: 'Durante i frame', es: 2 }] },
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
    // Tilt (ASTAP): fino al 10% / 10-20% / oltre
    tilt: v => v <= 10 ? G(0, 'buono') : v <= 20 ? G(1, 'incerto') : G(2, 'non adatto'),
    // Solo sul frame, contro la sua notte (stesso oggetto e filtro), con almeno 10 frame (scelta di Marco).
    // Giudizi relativi a 2,5 Qn (ADR 0039, Marco 24/10/2026; a schermo «rispetto al gruppo»): la stessa regola delle soglie della Selezione dei frame. Nel disegno la dispersione si simula col MAD scalato.
    minimo: 10,
    snrBasso: (v, arr) => { if (arr.length < 10) return null; const m = qn(arr, .5), mad = 1.4826 * qn(arr.map(x => Math.abs(x - m)), .5); return v < m - 2.5 * mad ? G(1, 'SNR basso per la notte') : null; },   // 2,5 Qn (ADR 0039), simulato col MAD scalato
    fuoco: (v, arr) => { if (arr.length < 10) return null; return v > qn(arr, .1) * 1.05 ? G(1, 'fuoco peggiore') : null; },   // N.I.N.A., +5% sulle migliori
    // Il frame contro l'oggetto: stessi oggetto e filtro, tutte le notti, almeno 10 (scelta di Marco); HFD fra notti: + 2,5 Qn, non "fuoco"
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
  // Selezione dei frame (v63, brief 2.9): le partenze per setup e filtro si salvano SOLO in Impostazioni › Selezione dei frame.
  // La pagina Selezione le legge e le cambia solo per il gruppo che guardi (oggetto, setup, filtro, tempo di posa, guadagno), senza salvarle qui.
  const SEL0 = { fw: { on: true, op: '>', tipo: 'rel', v: 2.5 }, ecc: { on: false, op: '>', tipo: 'rel', v: 2.5 }, stelle: { on: true, op: '<', tipo: 'rel', v: 2.5 }, snr: { on: true, op: '<', tipo: 'rel', v: 2.5 },
    bg: { on: false, op: '>', tipo: 'rel', v: 2.5 }, alt: { on: false, op: '<', tipo: 'abs', v: 30 }, psw: { on: false, op: '<', tipo: 'rel', v: 2.5 }, scie: { on: false, op: '>', tipo: 'abs', v: 0 },
    skyr: { on: false, op: '>', tipo: 'rel', v: 2.5 }, lalt: { on: false, op: '>', tipo: 'abs', v: 0 }, ldist: { on: false, op: '<', tipo: 'abs', v: 30 }, lill: { on: false, op: '>', tipo: 'abs', v: 65 }, fx: { on: false, testo: 'FWHM / SNR > 0,012' } };
  // Fonti pubbliche accanto a ogni partenza (v75): i 2,5 rispetto al gruppo sono la regola di Rousseeuw & Croux 1993 (lo stimatore Qn); nell'app ADR 0039.
  const RC = 'Rousseeuw & Croux 1993';
  const SELM = [['fw', 'FWHM', '″', RC], ['ecc', 'Eccentricità', '', 'solo le più allungate: le allunga il setup · ' + RC], ['stelle', 'Stelle', '', RC], ['snr', 'SNR', '', RC],
    ['bg', 'Fondo cielo', 'ADU', 'spenta: cambia con la Luna · ' + RC], ['alt', 'Altezza', '°', "massa d'aria 2 (AAVSO), come il Planner"], ['psw', 'Peso del segnale', '', 'il peso con cui si integra · ' + RC],
    ['scie', 'Scie', '', "ogni scia trovata dall'app (da 0 a 16 per frame)"], ['skyr', 'Fondo al secondo', 'ADU/s', 'si confronta fra tempi di posa diversi · ' + RC],
    ['lalt', 'Altezza della Luna', '°', 'dall\u0027orizzonte, quando sorge: come la regola della Luna'], ['ldist', 'Distanza dalla Luna', '°', 'nessuna convenzione: scegli tu'], ['lill', 'Luna illuminata', '%', 'regola di ING: grigio fino a 0,65']];
  const SELSET = [{ k: 'fra', n: 'Askar FRA400 + ZWO ASI2600MM Pro', b: 'FRA400 + 2600MM', filtri: ['l', 'ha'] }, { k: 'a103', n: 'Askar 103 + ZWO ATR2600M', b: 'Askar 103 + ATR2600M', filtri: ['l'] }];
  const selK = (sk, fk) => 'selezione.' + sk + '.' + fk;
  const SELEZ = { partenza: SEL0, misure: SELM, setup: SELSET,
    get: (sk, fk) => { const o = imp.get(selK(sk, fk)) || {}, fx = imp.get(selK(sk, 'fx')) || {}, r = {}; Object.keys(SEL0).forEach(k => { r[k] = { ...SEL0[k], ...(k === 'fx' ? fx : (o[k] || {})) }; }); return r; },
    set: (sk, fk, k, v) => { if (k === 'fx') return imp.set(selK(sk, 'fx'), { ...(imp.get(selK(sk, 'fx')) || {}), ...v }); const o = { ...(imp.get(selK(sk, fk)) || {}) }; o[k] = { ...(o[k] || {}), ...v }; return imp.set(selK(sk, fk), o); },
    cambiate: sk => { const S = SELSET.find(x => x.k === sk); return (S ? S.filtri : []).some(f => imp.get(selK(sk, f))) || !!imp.get(selK(sk, 'fx')); },
    rimetti: sk => { const S = SELSET.find(x => x.k === sk); (S ? S.filtri : []).forEach(f => imp.set(selK(sk, f), null)); imp.set(selK(sk, 'fx'), null); } };
  window.ALsoglie = { nebbia, selezione: SELEZ,
    giorniDaPiena, bandaDi, serveLuna, lunaPassa, lunaReg,
    imp, conto, nOre, intervallo, mostra, lunaNotte, gradi,
    misure: MISURE,
    // Giudizio di una misura: 0 buono, 1 incerto, 2 non adatto. Un gradino dove l'app ne ha uno.
    esito: {
      nuvole: x => x <= 25 ? 0 : x < 50 ? 1 : 2,         // okta WMO: 25% = 2 okta = buona
      raffiche: x => x < 25 ? 0 : 2,                     // 25 km/h (ADR 0034)
      vento: x => x < 20 ? 0 : x < 29 ? 1 : 2,           // Beaufort 4 e 5
      seeing: x => x <= 2 ? 0 : x < 4 ? 1 : 2,            // Clear Sky Chart
      jet: x => x < 126 ? 0 : 2,                         // meteoblue, 35 m/s
      condensa: x => x >= 3 ? 0 : 1,                     // FAA; mai «non adatta» (ADR 0034, in arrivo il modello di Beysens)
      aerosol: x => x < 1 ? 0 : 2,                       // NASA: sotto 0,1 limpido, da 1 molto fosco; in mezzo nessuna parola (vedi neutro)
      visibilita: x => x >= 1 ? 0 : 2,                   // WMO
      pioggia: x => x > 0 ? 2 : 0,                       // qualunque pioggia
      umidita: () => 0, pioggiaProb: () => 0 },          // solo valore, nessun giudizio
    // Fasce senza parola: barretta neutra, nessuna pillola
    neutro: { aerosol: x => x >= 0.1 && x < 1 },
    // ── Notte: la Trasparenza oraria 0-100 decide il verdetto (ADR 0034): 0 nelle ore che bloccano (pioggia, nuvole dal 50%, nebbia), altrimenti l'aerosol tolte le nuvole.
    // Il seeing e' fuori. Senza aerosol si conta solo con le nuvole e accanto si scrive «senza aerosol». Risponde { v, senza }.
    notte: (blocca, nuvole, aerosol) => ({ v: ALsoglie.trasparenzaOra(blocca, nuvole, aerosol), senza: aerosol == null ? ['l\u0027aerosol'] : [] }),
    // Ore di posa (ADR 0034, Marco 24/10/2026; al posto delle ore utili, «qualita' da 60», uscite): somma di (trasparenza / 100) × ore di buio,
    // divisa per banda della Luna. passi: [{ tr 0-100, banda 'larga'|'stretta', h ore del passo }]. Non decide il verdetto.
    // Nell'app la trasparenza dell'ora la da' il motore; nel disegno: 0 nelle ore che bloccano (pioggia, nuvole dal 50%, nebbia), altrimenti l'aerosol tolte le nuvole.
    trasparenzaOra: (blocca, nuvole, aerosol) => blocca ? 0 : cl((aerosol == null ? 100 : lin(aerosol, 0.1, 1)) * (1 - (nuvole || 0) / 100)),
    posa: passi => passi.reduce((p, x) => { const v = x.tr / 100 * (x.h ?? 1); p.tot += v; p[x.banda === 'stretta' ? 'stretta' : 'larga'] += v; return p; }, { tot: 0, larga: 0, stretta: 0 }),
    posaN: x => (Math.round(x * 10) / 10).toFixed(1).replace('.', ','),
    // Cielo in quattro classi okta (Marco 24/10, glossario): la parola viene dall'app, il numero accanto. okta = copertura / 12,5 arrotondata:
    // 0 Sereno · 1-4 Nuvole sparse · 5-7 Nuvoloso · 8 Coperto.
    cielo: pct => { const o = Math.round(pct / 12.5); return o === 0 ? 'Sereno' : o <= 4 ? 'Nuvole sparse' : o <= 7 ? 'Nuvoloso' : 'Coperto'; },
    // «Nuvoloso · 62%»
    cieloT: pct => ALsoglie.cielo(pct) + ' \u00b7 ' + Math.round(pct) + '%',
    // Seeing senza chiave (ADR 0034, Marco 6/11): un gradino solo dal jet stream, meteoblue: da 126 km/h (35 m/s) «scarso · stima dal vento in quota»; sotto, nessuna parola (solo l'invito alla chiave).
    seeingStima: jet => jet == null || isNaN(jet) || jet < 126 ? null : 'scarso',
    // Numeri all'italiana (Marco, 6/11): virgola decimale. dec cifre dopo la virgola.
    num: (x, dec) => x == null || isNaN(x) ? '' : AL.virg(x, dec),   // la regola sta in tema.js (AL.virg)
    // «4,6 ore» · «Nessuna ora»
    posaOre: p => p.tot < 0.05 ? 'Nessuna ora' : ALsoglie.posaN(p.tot) + ' ore',
    // La Luna divide la notte: ci sono ore di posa in banda larga e in sola banda stretta
    divisa: p => p.larga >= 0.05 && p.stretta >= 0.05,
    // «3,1 in banda larga, 1,5 solo banda stretta» (vuota se la Luna non divide)
    posaBande: p => ALsoglie.divisa(p) ? ALsoglie.posaN(p.larga) + ' in banda larga, ' + ALsoglie.posaN(p.stretta) + ' solo banda stretta' : p.tot >= 0.05 && p.stretta >= 0.05 ? 'solo banda stretta' : '',
    // «4,6 ore di posa: 3,1 in banda larga, 1,5 solo banda stretta»
    posaTesto: p => p.tot < 0.05 ? 'nessuna ora di posa' : ALsoglie.posaN(p.tot) + ' ore di posa' + (ALsoglie.posaBande(p) ? (ALsoglie.divisa(p) ? ': ' : ', ') + ALsoglie.posaBande(p) : ''),
    // Verdetto: dalla Trasparenza della notte, media pesata sulle ore di buio (di giorno, il punteggio delle ore della finestra).
    // Buona da 70, incerta da 40, sotto non adatta.
    livello: v => v >= 70 ? 0 : v >= 40 ? 1 : 2,
    media: arr => { const v = arr.filter(x => x != null); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null; },
    // Notti passate nel disegno: il punteggio d'esempio (met.q) o, se manca, uno simulato da ore visibili e nuvole. Senza Luna.
    puntoNotte: m => m.q ?? Math.round(35 + 55 * m.u / m.b - 0.3 * (m.n ?? 20)),
    // La riga accanto alla Trasparenza quando manca l'aerosol: «senza aerosol» (ADR 0034). Il seeing non entra, quindi non manca mai.
    senzaRiga: senza => (senza || []).includes('l\u0027aerosol') ? 'senza aerosol' : '',
    senzaPassate: [],
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
    larghePassate: (pct, cresce, b = 9) => pct <= RIP.limite ? b : ALsoglie.senzaLuna(pct, cresce, b),
    // Ore di buio con la Luna sotto l'altezza della regola (qualunque fase), simulate come sopra
    senzaLuna: (pct, cresce, b = 9) => { const e = Math.acos(1 - 2 * pct / 100) * 180 / Math.PI;
      const h = Math.acos(Math.min(1, Math.sin(RIP.alt * Math.PI / 180) / Math.cos(45.85 * Math.PI / 180))) * 180 / Math.PI / 15;
      const tr = 13.3 + (cresce ? e : 360 - e) / 15, su = tr - h, giu = tr + h, b0 = 25.25 - b / 2, b1 = 25.25 + b / 2; let sopra = 0;
      [-24, 0, 24].forEach(k => { sopra += Math.max(0, Math.min(b1, giu + k) - Math.max(b0, su + k)); });
      return Math.round(Math.max(0, b - sopra) * 6) / 6 }
  };
})();
