/**
 * I testi della pagina **Attrezzatura**: i pezzi che possiedi, e quanto ti sono serviti.
 *
 * File suo per la stessa ragione delle altre pagine: `it.ts` e' al tetto di righe, e si spezza
 * per area.
 */
export const itAttrezzatura = {
  "gear.failed": "Attrezzatura non disponibile",
  "gear.retry": "Riprova",
  "gear.loading": "Caricamento…", // glifo-ok: ellipsis
  // Il guscio della tavola v82: indice a carte, poi il dettaglio di cio' che scegli.
  "gear.title": "Attrezzatura",
  "gear.index": "Indice dell'attrezzatura",
  "gear.components": "Componenti",
  "gear.slotsMissing": "{n} da indicare",
  "gear.rework": "{n} frame da rielaborare",
  "gear.rework.close": "Chiudi",
  // I generi, come si chiamano a schermo. Sono quelli che lo schema conosce: un genere nuovo
  // nasce li' e passa di qui, o resterebbe senza nome.
  "gear.kind.optics": "Telescopi e obiettivi",
  "gear.kind.camera": "Camere",
  "gear.kind.mount": "Montature",
  "gear.kind.reducer": "Riduttori e spianatori",
  "gear.kind.filter_wheel": "Ruote portafiltri",
  "gear.kind.guide_scope": "Guide",
  "gear.kind.guide_camera": "Camere di guida",
  "gear.kind.focuser": "Focheggiatori",
  "gear.kind.oag": "Guide fuori asse",
  "gear.kind.spacer": "Distanziali",
  "gear.part.software": "programma di ripresa",
  "gear.rigs": "Setup",
  "gear.filters": "Filtri",
  // La riga di un pezzo: quanto e' servito, e cosa ci hai ripreso.
  "gear.frames": "{n} frame",
  "gear.frames.one": "1 frame",
  "gear.nights": "{n} notti",
  "gear.nights.one": "1 notte",
  // Dove le ore non esistono. Non e' uno zero: e' un legame che i file non portano, e finche'
  // non sei tu a dirlo l'app non lo sa.
  "gear.noHours": "non indicato nei file",
  "gear.noHours.mount": "non associata a un setup",
  "gear.noHours.reducer": "non associato a un setup",
  "gear.noHours.guide_scope": "non associata a un setup",
  "gear.noHours.oag": "non associata a un setup",
  "gear.noHours.spacer": "non associato a un setup",
  "gear.counting": "conteggio in corso",
  // Il setup: com'e' fatto e quanto cielo inquadra davvero.
  "gear.rig": "{ottica} + {camera}",
  "gear.rig.noOptics": "ottica non indicata",
  "gear.rig.noCamera": "camera non indicata",
  "gear.rig.mount": "su {nome}",
  "gear.focal": "{mm} mm",
  "gear.noScale": "campo non ancora disponibile",
  // La scheda: solo le righe che hanno un valore. Un campo vuoto non si scrive.
  "gear.aperture": "apertura {mm} mm",
  "gear.focalNative": "focale {mm} mm",
  "gear.pixel": "pixel {um} \u00b5m",
  "gear.pixelFromSky": "pixel {um} \u00b5m (calcolato)",
  "gear.camera.mono": "monocromatica",
  "gear.camera.color": "a colori",
  "gear.payload": "carico {kg} kg",
  "gear.weight": "peso {kg} kg",
  "gear.slots": "{n} posizioni",
  "gear.slots.one": "1 posizione",
  "gear.reducerFactor": "riduzione {fattore}\u00d7",
  "gear.backfocus": "backfocus {mm} mm",
  "gear.band": "{banda} {nm} nm",
  "gear.band.noWidth": "{banda}",
  "gear.declared": "inserito manualmente",
  // Lo stato vuoto: non e' un guasto, e' chi ha appena installato l'app.
  "gear.empty": "Nessuna attrezzatura",
  "gear.empty.why":
    "L'attrezzatura viene rilevata dagli header dei file FITS dopo la scansione.",
  "gear.empty.how": "Aggiungi cartella",
  // I gesti: scrivere un pezzo che i file non nominano, e correggere la scheda di uno che c'e'.
  "gear.write.add": "Aggiungi strumento",
  "gear.write.add.title": "Nuovo strumento",
  "gear.write.edit": "Modifica",
  "gear.write.edit.title": "{nome}",
  "gear.write.kind": "Tipo",
  "gear.write.kind.filter": "Filtro",
  "gear.write.kind.rig": "Setup",
  "gear.write.optics": "Ottica",
  "gear.write.camera": "Camera",
  // la focale che dicono i file: col riduttore e' quella col riduttore
  "gear.write.focal": "Focale effettiva (mm)",
  "gear.write.name": "Nome",
  "gear.write.save": "Salva",
  "gear.write.cancel": "Annulla",
  "gear.write.sameAs": "Unisci a",
  "gear.write.filter.sameAs": "Unisci a",
  "gear.write.rig": "Rinomina",
  "gear.write.rig.title": "Nome di {nome}",
  "gear.write.mergeRefused": "Unione non possibile. Nessuna modifica salvata.",
  "gear.write.notFound": "Dati non aggiornati: ricarica la pagina. Nessuna modifica salvata.",
  "gear.write.rigExists": "Setup gi\u00e0 presente (stessa ottica, stessa camera, focale entro il 5%).",
  "gear.write.spellingTaken": "Nome gi\u00e0 usato da un altro filtro.",
  "gear.write.wrongKind": "Ottica e camera vanno selezionate fra gli strumenti del tipo corrispondente.",
  // Il rifiuto dice cosa fare, non cosa e' andato storto: possiedi gia' quel nome, quindi il
  // pezzo che cerchi e' nell'elenco -- non ne serve un secondo.
  "gear.write.nameTaken":
    "Nome gi\u00e0 usato da uno strumento dello stesso tipo.",
  "gear.write.busy": "Scansione in corso: riprova al termine.",
  "gear.write.failed": "Salvataggio non riuscito",
  "gear.write.needName": "Per salvare serve il nome.",
  "gear.write.rig.label": "Rinomina {nome}",
  // Il dettaglio di un setup (tavola v82, `corredoV` e `conti`).
  "gear.rig.pair": "{ottica} · {camera}", // glifo-ok: separatore della tavola
  "gear.rig.ratio": "f/{n}",
  "gear.rig.computed": "(calcolato)",
  "gear.parts": "Parti",
  "gear.part.toSay": "da indicare",
  "gear.part.byHand": "(scelta a mano)",
  "gear.part.select": "Seleziona",
  "gear.part.select.label": "Seleziona {parte}",
  "gear.part.open": "Apri {nome} fra i componenti",
  "gear.part.title": "{parte} di {nome}",
  "gear.part.field.files": "{parte} (vuoto: dai file)",
  "gear.part.addOne": "aggiungine uno",
  // Il treno ottico (tavola v82, 63-66 e `treno` 447).
  "gear.train": "Treno ottico",
  "gear.train.note": "Schema non in scala. Seleziona uno strumento per aprirlo.",
  "gear.train.label": "Treno ottico di {nome}, schema non in scala",
  "gear.train.piece": "{tipo}: {nome}",
  "gear.train.open": "{tipo}: {nome}, apri",
  "gear.slot.optics": "ottica",
  "gear.slot.camera": "camera",
  "gear.slot.reducer": "riduttore",
  "gear.slot.filter_wheel": "ruota portafiltri",
  "gear.slot.spacer": "distanziali",
  "gear.slot.mount": "montatura",
  "gear.slot.focuser": "focheggiatore",
  "gear.slot.guide": "guida",
  "gear.slot.guide_camera": "camera di guida",
  "gear.slot.software": "programma di ripresa",
  "gear.field.label": "Campo",
  "gear.field.word": "campo",
  "gear.field.sides": "{larghezza}° × {altezza}°", // glifo-ok: board glyph
  "gear.field.scaleFromSky": "arcosecondi per pixel · ricavati dal cielo", // glifo-ok: board glyph
  "gear.field.scaleFromSky.one": "arcosecondo per pixel · ricavati dal cielo", // glifo-ok: board glyph
  "gear.field.moon": "Luna piena, per misura",
  "gear.field.compare": "Il campo di {nome} a confronto con gli altri setup e la Luna piena",
  "gear.field.compare.alone": "Il campo di {nome} a confronto con la Luna piena",
  "gear.numbers": "Dati del setup",
  "gear.numbers.from": "Dalle schede tecniche degli strumenti.",
  "gear.n.focal_ratio": "Rapporto focale",
  "gear.n.focal_ratio.sub": "focale effettiva {mm} mm",
  "gear.n.sampling": "Campionamento",
  "gear.n.arcsecPx": "{n}″/px", // glifo-ok: board glyph
  "gear.n.onSky": "sul cielo {n}″/px", // glifo-ok: board glyph
  "gear.n.onSky.none": "sul cielo: non ancora misurato",
  "gear.n.seeing": "{cielo} · ottimo con seeing fra {da} e {a}″; il giudizio della notte sta in Meteo", // glifo-ok: board glyph
  "gear.n.field": "Campo previsto",
  "gear.n.field.sky": "sul cielo {larghezza}° × {altezza}°", // glifo-ok: board glyph
  "gear.n.sensor_size": "Dimensione del sensore",
  "gear.n.sensor.value": "{larghezza} × {altezza} mm", // glifo-ok: board glyph
  "gear.n.sensor.sub": "dalla risoluzione e dal pixel della camera",
  "gear.n.coverage": "Copertura",
  "gear.n.mm": "{n} mm",
  "gear.n.coverage.sub": "diagonale del sensore · cerchio d'immagine {mm} mm", // glifo-ok: board glyph
  "gear.n.coverage.yes": "copre il sensore",
  "gear.n.coverage.no": "non copre il sensore",
  "gear.n.guide_scale": "Scala di guida",
  "gear.n.guide.oag": "fuori asse, con la focale del setup",
  "gear.n.guide.scope": "con {nome}",
  "gear.n.guide.sub": "{come} · consigliata fra {da} e {a}″/px", // glifo-ok: board glyph
  "gear.n.guide.in": "nell'intervallo",
  "gear.n.guide.out": "fuori intervallo",
  "gear.n.guide_ratio": "Rapporto guida/ripresa",
  "gear.n.guide_ratio.value": "{n}×", // glifo-ok: board glyph
  "gear.n.guide_ratio.sub": "scala di guida su campionamento",
  "gear.n.backfocus": "Backfocus del treno",
  "gear.n.backfocus.reducer": "richiesto {mm} mm dal riduttore",
  "gear.n.backfocus.optics": "richiesto {mm} mm dall'ottica",
  "gear.n.backfocus.tol": "{richiesto} · tolleranza ±{mm} mm", // glifo-ok: board glyph
  "gear.n.backfocus.noTol": "{richiesto} · {scarto} · tolleranza non indicata", // glifo-ok: board glyph
  "gear.n.backfocus.exact": "esatto",
  "gear.n.backfocus.in": "{scarto}, in tolleranza",
  "gear.n.backfocus.short": "corto di {mm} mm",
  "gear.n.backfocus.long": "lungo di {mm} mm",
  "gear.n.load": "Carico",
  "gear.n.load.sub": "del carico della montatura · {kg} kg su {max}", // glifo-ok: board glyph
  "gear.n.load.in": "entro il carico",
  "gear.n.load.out": "oltre il carico",
  // Cio' che manca a un conto: il campo, poi di chi. "manca il pixel della camera".
  "gear.missing": "manca {campo} {di}",
  "gear.missing.piece": "manca {pezzo}",
  "gear.missing.f.pixel_size_um": "il pixel",
  "gear.missing.f.width_px": "la risoluzione",
  "gear.missing.f.height_px": "la risoluzione",
  "gear.missing.f.aperture_mm": "l'apertura",
  "gear.missing.f.focal_mm": "la focale",
  "gear.missing.f.image_circle_mm": "il cerchio d'immagine",
  "gear.missing.f.required_backfocus_mm": "il backfocus richiesto",
  "gear.missing.f.thickness_mm": "lo spessore",
  "gear.missing.f.weight_kg": "il peso",
  "gear.missing.f.payload_kg": "il carico",
  "gear.missing.f.other": "un dato",
  "gear.missing.of.optics": "dell'ottica",
  "gear.missing.of.camera": "della camera",
  "gear.missing.of.mount": "della montatura",
  "gear.missing.of.reducer": "del riduttore",
  "gear.missing.of.filter_wheel": "della ruota portafiltri",
  "gear.missing.of.guide_scope": "dell'ottica di guida",
  "gear.missing.of.guide_camera": "della camera di guida",
  "gear.missing.of.focuser": "del focheggiatore",
  "gear.missing.of.oag": "della guida fuori asse",
  "gear.missing.of.spacer": "del distanziale",
  "gear.missing.of.rig": "del setup",
  "gear.missing.of.guide": "della guida",
  "gear.missing.p.optics": "l'ottica",
  "gear.missing.p.camera": "la camera",
  "gear.missing.p.mount": "la montatura",
  "gear.missing.p.reducer": "il riduttore",
  "gear.missing.p.filter_wheel": "la ruota portafiltri",
  "gear.missing.p.guide_scope": "l'ottica di guida",
  "gear.missing.p.guide_camera": "la camera di guida",
  "gear.missing.p.focuser": "il focheggiatore",
  "gear.missing.p.oag": "la guida fuori asse",
  "gear.missing.p.spacer": "il distanziale",
  "gear.missing.p.rig": "il setup",
  "gear.missing.p.guide": "la guida",
  "gear.ring": "in proporzione ai frame",
  "gear.ring.n": "filtri",
  "gear.ring.n.one": "filtro",
  "gear.ring.label": "Filtri, in proporzione ai frame: {nomi}",
  // La scheda di un pezzo in una riga: le voci con un valore (tavola `specs`).
  "gear.spec.sensor": "sensore {nome}",
  "gear.spec.resolving": "potere risolutore {n}″", // glifo-ok: board glyph
  "gear.spec.circle": "cerchio d'immagine {mm} mm",
  "gear.spec.backfocusTol": "backfocus {mm} mm ± {tol}", // glifo-ok: board glyph
  "gear.spec.pixels": "{larghezza} × {altezza} px", // glifo-ok: board glyph
  "gear.spec.adc": "{n} bit",
  "gear.spec.cooled": "raffreddata",
  "gear.spec.cooledBy": "raffreddata, {c} °C sotto l'ambiente", // glifo-ok: board glyph
  "gear.spec.payloadCw": "carico {kg} kg con contrappeso",
  "gear.spec.payloadNoCw": "{kg} kg senza",
  "gear.spec.wheelSize": "filtri da {misura}",
  "gear.spec.barlow": "barlow {fattore}×", // glifo-ok: board glyph
  "gear.spec.step": "passo {um} µm", // glifo-ok: board glyph
  "gear.spec.steps": "{n} passi",
  "gear.spec.thickness": "spessore {mm} mm",
  "gear.spec.prism": "prisma {mm} mm",
  "gear.design.refractor": "rifrattore",
  "gear.design.newtonian": "Newton",
  "gear.design.sct": "Schmidt-Cassegrain",
  "gear.design.rc": "Ritchey-Chrétien", // glifo-ok: board glyph
  "gear.design.maksutov": "Maksutov",
  "gear.design.camera_lens": "obiettivo fotografico",
  "gear.design.other": "altro",
  "gear.size.1.25in": "1,25″", // glifo-ok: board glyph
  "gear.size.31mm": "31 mm",
  "gear.size.36mm": "36 mm",
  "gear.size.2in": "2″", // glifo-ok: board glyph
  "gear.size.50mm_square": "50 mm quadrato",
}
