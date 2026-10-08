/**
 * I testi della pagina **Attrezzatura**: i pezzi che possiedi, e quanto ti sono serviti.
 *
 * File suo per la stessa ragione delle altre pagine: `it.ts` e' al tetto di righe, e si spezza
 * per area.
 */
export const itAttrezzatura = {
  "gear.title": "Attrezzatura",
  "gear.failed": "Attrezzatura non disponibile",
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
  "gear.rigs": "Corredi",
  "gear.filters": "Filtri",
  // La riga di un pezzo: quanto e' servito, e cosa ci hai ripreso.
  "gear.frames": "{n} frame",
  "gear.frames.one": "1 frame",
  "gear.nights": "{n} notti",
  "gear.nights.one": "1 notte",
  // Dove le ore non esistono. Non e' uno zero: e' un legame che i file non portano, e finche'
  // non sei tu a dirlo l'app non lo sa.
  "gear.noHours": "non indicato nei file",
  "gear.noHours.mount": "non associata a un corredo",
  "gear.counting": "conteggio in corso",
  // Il corredo: com'e' fatto e quanto cielo inquadra davvero.
  "gear.rig": "{ottica} + {camera}",
  "gear.rig.noOptics": "ottica non indicata",
  "gear.rig.noCamera": "camera non indicata",
  "gear.rig.mount": "su {nome}",
  "gear.focal": "{mm} mm",
  "gear.scale": "{n} arcosecondi per pixel",
  "gear.scale.one": "1 arcosecondo per pixel",
  "gear.field": "campo {larghezza}\u00b0 \u00d7 {altezza}\u00b0",
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
  "gear.write.kind.rig": "Corredo",
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
  "gear.write.mount": "Seleziona montatura",
  "gear.write.mount.title": "Montatura di {nome}",
  // la voce vuota della tendina toglie la tua parola: allora conta quella che nominano i file
  "gear.write.mount.field": "Montatura (vuoto: dai file)",
  "gear.write.mergeRefused": "Unione non possibile. Nessuna modifica salvata.",
  "gear.write.notFound": "Dati non aggiornati: ricarica la pagina. Nessuna modifica salvata.",
  "gear.write.rigExists": "Corredo gi\u00e0 presente (stessa ottica, stessa camera, focale entro il 5%).",
  "gear.write.spellingTaken": "Nome gi\u00e0 usato da un altro filtro.",
  "gear.write.wrongKind": "Ottica e camera vanno selezionate fra gli strumenti del tipo corrispondente.",
  // Il rifiuto dice cosa fare, non cosa e' andato storto: possiedi gia' quel nome, quindi il
  // pezzo che cerchi e' nell'elenco -- non ne serve un secondo.
  "gear.write.nameTaken":
    "Nome gi\u00e0 usato da uno strumento dello stesso tipo.",
  "gear.write.busy": "Scansione in corso: riprova al termine.",
  "gear.write.failed": "Salvataggio non riuscito",
}
