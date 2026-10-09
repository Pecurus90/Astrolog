/**
 * I testi italiani: la **sorgente**. Le chiavi sono in inglese perche' sono nomi nel codice.
 *
 * Vincolo non ovvio: `review.toConfirm` e' un frammento che segue un numero, non una frase
 * intera, perche' a schermo il numero e' in grassetto e il testo no. Regge in italiano e in
 * inglese, dove il numero sta davanti in tutti e due; una lingua che lo volesse altrove avrebbe
 * bisogno di una frase sola con il numero dentro, e questa chiave andrebbe rifatta.
 */
import { itArchivio } from "./it-archivio"
import { itAttrezzatura } from "./it-attrezzatura"
import { itGuscio } from "./it-guscio"
import { itImpostazioni } from "./it-impostazioni"
import { itLetture } from "./it-letture"
import { itMeteo } from "./it-meteo"
import { itNotti } from "./it-notti"
import { itSito } from "./it-sito"
import { itSolver } from "./it-solver"
import { itStanotte } from "./it-stanotte"
import { itWizard } from "./it-wizard"

export const it = {
  ...itWizard,
  ...itStanotte,
  ...itImpostazioni,
  ...itLetture,
  ...itNotti,
  ...itMeteo,
  ...itAttrezzatura,
  ...itArchivio,
  ...itGuscio,
  ...itSito,
  ...itSolver,
  "scan.start": "Scansiona",
  "scan.stop": "Interrompi",
  "scan.resume": "Riprendi",
  "scan.progress": "{fatti} su {su}",
  "scan.label": "scansione",
  "scan.idle": "Inattiva",
  "scan.working": "In corso",
  "scan.stopped": "Interrotta",
  "scan.blocked": "Bloccata",
  "scan.blocked.why": "Scansione interrotta da un errore",
  "scan.blocked.see": "Dettagli",
  "scan.last": "Ultima scansione: {giorno}, {ora}",
  "scan.stage.scan": "Lettura dei file",
  "scan.stage.normalize": "Normalizzazione dei nomi",
  "scan.stage.solve": "Plate solving",
  "scan.stage.identify": "Identificazione degli oggetti",
  "scan.stage.group": "Raggruppamento in notti",
  "scan.lostFolder": "Lettura di una cartella non completata. Controlla il disco e riprova.",
  "scan.skipped.unreachable": "{cartella}: non raggiungibile, ignorata",
  "scan.skipped.running": "{cartella}: scansione gi\u00e0 in corso",
  "scan.failed": "Stato della scansione non disponibile",
  "scan.error.no_folders": "Nessuna cartella da leggere. Aggiungi una cartella.",
  "scan.error.no_readable_folders": "Nessuna cartella raggiungibile",
  "scan.error.worker_busy": "Operazione gi\u00e0 in corso",
  "review.title": "Da confermare",
  "review.filters": "Filtri",
  "review.filters.why":
    "Filtri non riconosciuti. L'associazione vale anche per i frame futuri.",
  "review.filters.mine": "Filtro esistente: {nome}",
  "review.filters.searchFor": "Cerca fra i modelli per {nome}",
  "review.filters.notListed": "Non in elenco: nuovo filtro",
  "review.filters.name": "Nome",
  "review.filters.change": "Cambia modello",
  "review.filters.band": "Banda",
  "review.objects.hours": "{h} h",
  "review.objects.untimed": "{n} senza durata",
  "review.lookalikes": "Strumenti duplicati",
  "review.lookalikes.why":
    "Strumenti con nome simile e stesse caratteristiche: possono essere lo stesso strumento rilevato da due programmi. L'unione non \u00e8 reversibile.",
  "review.lookalikes.looksLike": "simile a {nome} ({pose} frame)",
  "review.lookalikes.question": "{nome} e {altra} sono lo stesso strumento?",
  "review.lookalikes.same": "S\u00ec, unisci a {nome}",
  "review.lookalikes.distinct": "No, sono distinti",
  "review.kind.optics": "ottica",
  "review.kind.camera": "camera",
  "review.kind.mount": "montatura",
  "review.kind.reducer": "riduttore",
  "review.kind.filter_wheel": "ruota portafiltri",
  "review.kind.guide_scope": "ottica di guida",
  "review.kind.guide_camera": "camera di guida",
  "review.kind.focuser": "focheggiatore",
  "review.card.brand": "Marca",
  "review.card.model": "Modello",
  "review.card.camera_type": "Tipo di sensore",
  "review.card.pixel_size_um": "Pixel (um)",
  "review.card.aperture_mm": "Apertura (mm)",
  "review.card.focal_mm": "Focale nativa (mm)",
  "review.card.reducer_factor": "Fattore",
  "review.card.weight_kg": "Peso (kg)",
  "review.card.payload_kg": "Carico utile (kg)",
  "review.card.slots": "Numero di posizioni",
  "review.card.notes": "Note",
  "review.card.mono": "mono",
  "review.card.color": "a colori",
  "review.typeless": "Frame senza tipo",
  "review.typeless.why":
    "Tipo di frame non indicato nei file. Finch\u00e9 non viene indicato, i frame sono esclusi dal conteggio delle ore.",
  "review.typeless.question": "Tipo dei frame in {cartella}",
  "review.typeless.light": "Light",
  "review.typeless.calibration": "Calibrazione",
  "review.typeless.answerLight": "Light",
  "review.typeless.answerCalibration": "Calibrazione",
  "sky.point": "RA {ra} Dec {dec}",
  "review.unclear": "Frame senza sito",
  "review.unclear.why":
    "Frame ripresi a coordinate che non corrispondono a nessun sito. L'associazione vale anche per le notti future.",
  "review.unclear.fromHome": "a {km} km dal sito predefinito",
  "review.unclear.nights": "notti: {notti}",
  // Quando la notte non si sa ancora: nomina la domanda di questa riga.
  "review.unclear.nights.later": "Notti non calcolabili senza sito",
  "review.unclear.question": "Sito per le coordinate {posto}",
  "review.unclear.site": "{luogo}, a {km} km",
  "review.mosaics": "Mosaici proposti",
  "review.mosaics.why":
    "Pannelli adiacenti ripresi con lo stesso corredo. Vengono uniti solo dopo conferma.",
  "review.mosaics.panels": "{n} pannelli",
  "review.mosaics.panels.one": "1 pannello",
  "review.mosaics.where": "a {dove}",
  "review.mosaics.question": "{soggetti}, {dove}: mosaico?",
  "review.mosaics.yes": "Mosaico",
  "review.mosaics.no": "Non \u00e8 un mosaico",
  "review.mosaics.name": "Oggetto del mosaico ({dove})",
  "review.frames": "{n} frame",
  "review.frames.one": "1 frame",
  "review.subjects": "Oggetti: {oggetti}",
  "review.subjects.item": "{nome} ({pose})",
  "review.subjects.more": "+ {n}",
  "review.subjects.more.one": "+ 1",
  "review.subjects.notFound": "{pose} senza oggetti identificati",
  "review.subjects.notYet": "{pose} non risolti",
  "review.count": "{n} da confermare",
  "review.count.one": "1 da confermare",
  "review.apply": "Applica",
  // il piede dice cosa si sta per mandare: un Applica che non dice quanto e' un salto nel buio
  // girata cosi' si legge bene con ogni numero
  "review.inHand": "{n} modifiche da applicare",
  "review.inHand.one": "1 modifica da applicare",
  "review.applied": "{n} modifiche applicate, {pose} frame da rielaborare",
  "review.applied.one": "1 modifica applicata, {pose} frame da rielaborare",
  "review.apply.failed": "Modifiche non applicate",
  "review.apply.unknownTarget":
    "Oggetto non presente nel catalogo. Nessuna modifica salvata.",
  "review.apply.notFound":
    "Dati non aggiornati: ricarica la pagina. Nessuna modifica salvata.",
  "review.apply.busy": "Scansione in corso: riprova al termine. Nessuna modifica salvata.",
  "review.apply.mergeRefused":
    "Unione non possibile. Nessuna modifica salvata.",
  "review.apply.nameTaken":
    "Nome gi\u00e0 usato da un altro strumento. Nessuna modifica salvata.",
  "review.models.failed": "Elenco dei modelli non disponibile",
  "review.loading": "Caricamento\u2026",
  "review.failed": "Da confermare non disponibile",
  "review.toConfirm": "da confermare",
  "health.failed": "Il servizio non ha risposto",
  "health.version": "versione {v}",
  "health.tables": "{n} tabelle nel database",
  "health.tables.one": "1 tabella nel database",
  "health.catalogEntries": "{n} voci di catalogo",
  "health.catalogEntries.one": "1 voce di catalogo",
  "action.reload": "Ricarica",
  "action.retry": "Riprova",
  "settings.failed": "Il servizio non ha risposto.",
  // **Che cielo hai**, le nove classi di Bortle. I nomi e le descrizioni vengono dalla colonna
  // *Title* della voce *Bortle scale* di Wikipedia, letta nel sorgente grezzo
  // (https://en.wikipedia.org/w/index.php?title=Bortle_scale&action=raw), che e' una delle tre
  // fonti con cui `backend/astrolog/units.py` dichiara di allinearsi -- quella dei siti di
  // astrofotografia, cioe' il numero con cui l'utente confrontera' il nostro. Non si scrivono a
  // memoria: la scala e' gia' entrata sbagliata di due classi una volta, scritta a mente.
  //
  // **La 4 e la 7 si somigliano nel nome e non vanno scambiate**: li' la fonte dice *brighter
  // rural* e *suburban/urban transition*. Il montaggio del fornitore, sulla 4, scrive "cielo di
  // periferia rurale", che e' il nome della 7 tradotto: e' un testo di prova loro, non una fonte.
  // Se la domanda torna, si rilegge quell'URL, non questa riga.
  //
  // La luce zodiacale **a colori** e' l'indizio della 2, non della 1: sulla 1 l'indizio vero sono
  // le ombre della Via Lattea, che le altre classi non hanno.
  // Ogni riga dice **cosa ci si vede**, non quanto e' buio: e' l'unica cosa su cui chi ha appena
  // installato puo' davvero rispondere.
  "sky.scale": "Classe di Bortle, da 1 a 9",
  "sky.label": "Qualit\u00e0 del cielo (scala di Bortle)",
  "sky.chosen": "Bortle {n} - {cielo}",
  "sky.optional": "Facoltativo.",
  "sky.low": "1 - cielo buio",
  "sky.high": "9 - centro citt\u00e0",
  "sky.1": "cielo eccellente, buio pieno",
  "sky.1.what": "La Via Lattea proietta ombre, e il cielo stesso ha un suo debole bagliore naturale; a occhio nudo si arriva a M33 e a molti oggetti Messier.",
  "sky.2": "cielo buio vero",
  "sky.2.what": "La luce zodiacale \u00e8 gialla e fa ombra, la Via Lattea d'estate \u00e8 piena di struttura, e M33 si vede a occhio nudo senza fatica.",
  "sky.3": "cielo di campagna",
  "sky.3.what": "Qualche alone di luce basso sull'orizzonte, ma la Via Lattea d'estate \u00e8 ancora complessa e M33 si vede con la visione distolta.",
  "sky.4": "campagna pi\u00f9 chiara",
  "sky.4.what": "Gli aloni delle luci si vedono in pi\u00f9 direzioni; la Via Lattea \u00e8 ancora bella ma senza dettagli, e la luce zodiacale non arriva a met\u00e0 cielo.",
  "sky.5": "cielo di periferia",
  "sky.5.what": "Solo accenni di luce zodiacale nelle notti migliori; la Via Lattea sbiadisce allo zenit e sparisce verso l'orizzonte, e le luci si vedono quasi ovunque.",
  "sky.6": "periferia luminosa",
  "sky.6.what": "Niente luce zodiacale; il cielo basso \u00e8 grigio-bianco e la Via Lattea si intravede solo allo zenit. M33 solo col binocolo.",
  "sky.7": "fra periferia e citt\u00e0",
  "sky.7.what": "Tutto il cielo \u00e8 grigio chiaro, con sorgenti di luce forte in ogni direzione; la Via Lattea quasi non si vede.",
  "sky.8": "cielo di citt\u00e0",
  "sky.8.what": "Il cielo \u00e8 grigio o arancione e ci si legge; molte stelle delle costellazioni sono deboli o non si vedono affatto.",
  "sky.9": "centro citt\u00e0",
  "sky.9.what": "Le costellazioni si perdono e, a occhio nudo, a parte le Pleiadi non si vede nessun oggetto Messier: restano Luna, pianeti e gli ammassi pi\u00f9 luminosi.",
  // Le lettere dei quattro versi. Passano di qui e non stanno scritte in `coordinate()` perche'
  // sono parole di una lingua: in inglese ovest e' `W`, e una lettera dentro il formattatore
  // resterebbe italiana senza che la guardia delle traduzioni se ne accorga.
  "coord.n": "N",
  "coord.s": "S",
  "coord.e": "E",
  "coord.w": "O",
}
