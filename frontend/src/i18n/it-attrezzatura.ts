/**
 * I testi della pagina **Attrezzatura**: i pezzi che possiedi, e quanto ti sono serviti.
 *
 * File suo per la stessa ragione delle altre pagine: `it.ts` e' al tetto di righe, e si spezza
 * per area.
 */
export const itAttrezzatura = {
  "gear.title": "Attrezzatura",
  "gear.failed": "non sono riuscito a leggere l'attrezzatura",
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
  "gear.noHours": "i tuoi file non dicono quale hai usato per ogni ripresa",
  "gear.noHours.mount": "nessun corredo la porta ancora: sceglila nella scheda dei corredi con cui la usi",
  "gear.counting": "si sta contando: i numeri arrivano a fine lettura",
  // Il corredo: com'e' fatto e quanto cielo inquadra davvero.
  "gear.rig": "{ottica} + {camera}",
  "gear.rig.noOptics": "ottica non dichiarata",
  "gear.rig.noCamera": "camera non dichiarata",
  "gear.rig.mount": "sulla {nome}",
  "gear.focal": "{mm} mm",
  "gear.scale": "{n} arcosecondi per pixel",
  "gear.scale.one": "1 arcosecondo per pixel",
  "gear.field": "inquadra {larghezza} x {altezza} gradi",
  "gear.noScale": "quanto inquadra si sapra' quando l'app avra' riconosciuto qualche suo frame",
  // La scheda: solo le righe che hanno un valore. Un campo vuoto non si scrive.
  "gear.aperture": "apertura {mm} mm",
  "gear.focalNative": "focale {mm} mm",
  "gear.pixel": "pixel {um} micron",
  "gear.pixelFromSky": "pixel {um} micron, ricavato dal cielo",
  "gear.camera.mono": "monocromatica",
  "gear.camera.color": "a colori",
  "gear.payload": "regge {kg} kg",
  "gear.weight": "pesa {kg} kg",
  "gear.slots": "{n} posti",
  "gear.slots.one": "1 posto",
  "gear.reducerFactor": "riduce a {fattore}x",
  "gear.backfocus": "backfocus {mm} mm",
  "gear.band": "{banda} {nm} nm",
  "gear.band.noWidth": "{banda}",
  "gear.declared": "dichiarato da te",
  // Lo stato vuoto: non e' un guasto, e' chi ha appena installato l'app.
  "gear.empty": "Non so ancora con cosa riprendi",
  "gear.empty.why":
    "I tuoi strumenti, i filtri e i corredi si riconoscono dagli header dei FITS: appena una cartella e' stata letta, compaiono qui con le ore che hanno fatto.",
  "gear.empty.how": "Aggiungi una cartella",
  // I gesti: scrivere un pezzo che i file non nominano, e correggere la scheda di uno che c'e'.
  "gear.write.add": "Aggiungi un pezzo",
  "gear.write.add.title": "Un pezzo che l'app non ha trovato nei file",
  "gear.write.edit": "Correggi",
  "gear.write.edit.title": "La scheda di {nome}",
  "gear.write.kind": "Genere",
  "gear.write.kind.filter": "Filtro",
  "gear.write.kind.rig": "Corredo",
  "gear.write.optics": "Ottica",
  "gear.write.camera": "Camera",
  // la focale che dicono i file: col riduttore e' quella col riduttore
  "gear.write.focal": "Focale in mm (col riduttore, se lo usi)",
  "gear.write.name": "Nome",
  "gear.write.save": "Salva",
  "gear.write.cancel": "Annulla",
  "gear.write.sameAs": "E' lo stesso pezzo di",
  "gear.write.filter.sameAs": "E' lo stesso filtro di",
  "gear.write.rig": "Dagli un nome",
  "gear.write.rig.title": "Il nome di {nome}",
  "gear.write.mount": "Scegli la montatura",
  "gear.write.mount.title": "La montatura di {nome}",
  // la voce vuota della tendina toglie la tua parola: allora conta quella che nominano i file
  "gear.write.mount.field": "Montatura (vuota: quella che dicono i file)",
  "gear.write.mergeRefused": "Questi due non si possono unire: non e' stato scritto niente.",
  "gear.write.notFound": "Questa pagina e' vecchia: ricaricala, non e' stato scritto niente.",
  "gear.write.rigExists": "Questo corredo ce l'hai gia': stessa ottica, stessa camera, focale entro il 5%.",
  "gear.write.spellingTaken": "Questo filtro ce l'hai gia': le pose che lo scrivono stanno su un tuo filtro. Se vuoi chiamarlo cosi', rinomina quello.",
  "gear.write.wrongKind": "L'ottica e la camera vanno scelte fra i tuoi pezzi di quel genere.",
  // Il rifiuto dice cosa fare, non cosa e' andato storto: possiedi gia' quel nome, quindi il
  // pezzo che cerchi e' nell'elenco -- non ne serve un secondo.
  "gear.write.nameTaken":
    "Lo possiedi gia': un pezzo con questo nome c'e' gia' fra quelli del suo genere, e lo trovi qui sotto.",
  "gear.write.busy": "Sto leggendo l'archivio: riprova fra poco, per non scrivere a meta'.",
  "gear.write.failed": "non sono riuscito a scrivere questo pezzo",
}
