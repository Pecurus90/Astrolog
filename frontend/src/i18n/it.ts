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
  "scan.stop": "Ferma",
  "scan.resume": "Riprendi",
  "scan.progress": "{fatti} su {su}",
  "scan.label": "scansione",
  "scan.idle": "a riposo",
  "scan.working": "al lavoro",
  "scan.stopped": "Fermata",
  "scan.blocked": "bloccata",
  "scan.blocked.why": "la lettura si e' interrotta",
  "scan.blocked.see": "Vedi",
  "scan.last": "Ultima lettura {giorno} alle {ora}",
  "scan.stage.scan": "leggo i file",
  "scan.stage.normalize": "metto in ordine i nomi",
  "scan.stage.solve": "cerco il cielo",
  "scan.stage.identify": "riconosco gli oggetti",
  "scan.stage.group": "raccolgo le notti",
  "scan.lostFolder": "una cartella non si e' potuta leggere fino in fondo: riprova, o guarda se il disco risponde",
  "scan.skipped.unreachable": "{cartella}: non si riesce a leggerla adesso, l'ho saltata",
  "scan.skipped.running": "{cartella}: la sto gia' leggendo",
  "scan.failed": "non sono riuscito a leggere cosa sta facendo l'app",
  "scan.error.no_folders": "non c'e' nessuna cartella da leggere: aggiungine una",
  "scan.error.no_readable_folders": "nessuna delle cartelle indicate si riesce a leggere adesso",
  "scan.error.worker_busy": "c'e' gia' un lavoro in corso",
  "review.title": "Da confermare",
  "review.filters": "Filtri",
  "review.filters.why":
    "L'app non riconosce questi filtri: dimmi cosa sono, una volta, e vale anche per i frame che arriveranno.",
  "review.filters.mine": "E' uno dei miei filtri: {nome}",
  "review.filters.searchFor": "Cerca fra i modelli per {nome}",
  "review.filters.notListed": "Non e' in elenco: lo aggiungo io",
  "review.filters.name": "Nome",
  "review.filters.change": "Scegli un altro modello",
  "review.filters.band": "Banda",
  "review.objects.hours": "{h} h",
  "review.objects.untimed": "{n} senza tempo",
  "review.lookalikes": "Stesso pezzo?",
  "review.lookalikes.why":
    "Queste camere hanno lo stesso sensore e quasi lo stesso nome: spesso e' la stessa camera vista da due programmi. L'app non puo' saperlo -- due camere dello stesso modello sono due pezzi -- quindi lo chiede. Unite, non si possono piu' separare.",
  "review.lookalikes.looksLike": "somiglia a {nome} ({pose} frame)",
  "review.lookalikes.question": "{nome} e {altra} sono lo stesso pezzo",
  "review.lookalikes.same": "Si', uniscila a {nome}",
  "review.lookalikes.distinct": "No, sono due pezzi",
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
  "review.card.camera_type": "Colore",
  "review.card.pixel_size_um": "Pixel (um)",
  "review.card.aperture_mm": "Apertura (mm)",
  "review.card.focal_mm": "Focale nativa (mm)",
  "review.card.reducer_factor": "Fattore",
  "review.card.weight_kg": "Peso (kg)",
  "review.card.payload_kg": "Carico che regge (kg)",
  "review.card.slots": "Quanti filtri",
  "review.card.notes": "Nota",
  "review.card.mono": "mono",
  "review.card.color": "a colori",
  "review.typeless": "Frame senza tipo",
  "review.typeless.why":
    "I file di queste cartelle non dicono se sono foto del cielo o file di calibrazione, e l'app non e' riuscita a capirlo dal cielo. Finche' non lo dici tu li mette da parte: non contano nelle ore, e non te li chiede fra i Frame senza nome. Si risponde una volta per cartella, vale per tutti i suoi file senza tipo e anche per quelli che arriveranno li' dentro.",
  "review.typeless.question": "Che file sono quelli in {cartella}",
  "review.typeless.light": "Foto del cielo",
  "review.typeless.calibration": "File di calibrazione",
  "review.typeless.answerLight": "risposta: foto del cielo",
  "review.typeless.answerCalibration": "risposta: file di calibrazione",
  "sky.point": "RA {ra} Dec {dec}",
  "review.unclear": "Frame senza sito",
  "review.unclear.why":
    "Questi frame sono stati ripresi a coordinate che non cadono in nessuno dei tuoi siti: dimmi da quale, e vale anche per le notti che verranno li'.",
  "review.unclear.fromHome": "a {km} km da casa",
  "review.unclear.nights": "notti: {notti}",
  // Quando la notte non si sa ancora: nomina la domanda di questa riga.
  "review.unclear.nights.later": "le notti si sapranno quando avrai detto da dove osservavi",
  "review.unclear.question": "Da quale sito, alle coordinate {posto}",
  "review.unclear.site": "{luogo}, a {km} km",
  "review.mosaics": "Mosaici proposti",
  "review.mosaics.why":
    "Pannelli affiancati dello stesso corredo: l'app te li propone come un mosaico, ma non li unisce da sola.",
  "review.mosaics.panels": "{n} pannelli",
  "review.mosaics.panels.one": "1 pannello",
  "review.mosaics.where": "a {dove}",
  "review.mosaics.question": "{soggetti}, a {dove}: e' un mosaico?",
  "review.mosaics.yes": "e' un mosaico",
  "review.mosaics.no": "non e' un mosaico",
  "review.mosaics.name": "Di cosa e' il mosaico a {dove}",
  "review.frames": "{n} frame",
  "review.frames.one": "1 frame",
  "review.subjects": "ripreso: {oggetti}",
  "review.subjects.item": "{nome} ({pose})",
  "review.subjects.more": "e altri {n}",
  "review.subjects.more.one": "e un altro",
  "review.subjects.notFound": "{pose} in cui il cielo non ha trovato niente",
  "review.subjects.notYet": "{pose} che il cielo non ha ancora guardato o non e' riuscito a guardare",
  "review.count": "{n} cose da confermare",
  "review.count.one": "1 cosa da confermare",
  "review.apply": "Applica",
  // il piede dice cosa si sta per mandare: un Applica che non dice quanto e' un salto nel buio
  // girata cosi' si legge bene con ogni numero
  "review.inHand": "risposte in mano: {n}",
  "review.applied": "applicate {n} risposte, {pose} frame rimessi in coda",
  "review.applied.one": "applicata 1 risposta, {pose} frame rimessi in coda",
  "review.apply.failed": "le risposte non sono state applicate",
  "review.apply.unknownTarget":
    "quell'oggetto il catalogo non lo conosce: non e' stato scritto niente",
  "review.apply.notFound":
    "questa pagina e' vecchia: ricaricala e rispondi di nuovo, non e' stato scritto niente",
  "review.apply.busy": "l'archivio sta lavorando: riprova fra poco, non e' stato scritto niente",
  "review.apply.mergeRefused":
    "quei due non si possono unire: non e' stato scritto niente",
  "review.apply.nameTaken":
    "quel nome ce l'ha gia' un altro pezzo: scegline un altro, o uniscili -- non e' stato scritto niente",
  "review.models.failed": "l'elenco dei modelli non ha risposto",
  "review.loading": "sto leggendo l'archivio...",
  "review.failed": "la pagina Da confermare non ha risposto",
  "review.toConfirm": "cose da confermare",
  "health.failed": "il servizio non ha risposto",
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
  "sky.low": "1 - buio pieno",
  "sky.high": "9 - centro citta'",
  "sky.1": "cielo eccellente, buio pieno",
  "sky.1.what": "La Via Lattea proietta ombre, e il cielo stesso ha un suo debole bagliore naturale; a occhio nudo si arriva a M33 e a molti oggetti Messier.",
  "sky.2": "cielo buio vero",
  "sky.2.what": "La luce zodiacale e' gialla e fa ombra, la Via Lattea d'estate e' piena di struttura, e M33 si vede a occhio nudo senza fatica.",
  "sky.3": "cielo di campagna",
  "sky.3.what": "Qualche alone di luce basso sull'orizzonte, ma la Via Lattea d'estate e' ancora complessa e M33 si vede con la visione distolta.",
  "sky.4": "campagna piu' chiara",
  "sky.4.what": "Gli aloni delle luci si vedono in piu' direzioni; la Via Lattea e' ancora bella ma senza dettagli, e la luce zodiacale non arriva a meta' cielo.",
  "sky.5": "cielo di periferia",
  "sky.5.what": "Solo accenni di luce zodiacale nelle notti migliori; la Via Lattea sbiadisce allo zenit e sparisce verso l'orizzonte, e le luci si vedono quasi ovunque.",
  "sky.6": "periferia luminosa",
  "sky.6.what": "Niente luce zodiacale; il cielo basso e' grigio-bianco e la Via Lattea si intravede solo allo zenit. M33 solo col binocolo.",
  "sky.7": "fra periferia e citta'",
  "sky.7.what": "Tutto il cielo e' grigio chiaro, con sorgenti di luce forte in ogni direzione; la Via Lattea quasi non si vede.",
  "sky.8": "cielo di citta'",
  "sky.8.what": "Il cielo e' grigio o arancione e ci si legge; molte stelle delle costellazioni sono deboli o non si vedono affatto.",
  "sky.9": "centro citta'",
  "sky.9.what": "Le costellazioni si perdono e, a occhio nudo, a parte le Pleiadi non si vede nessun oggetto Messier: restano Luna, pianeti e gli ammassi piu' luminosi.",
  // Le lettere dei quattro versi. Passano di qui e non stanno scritte in `coordinate()` perche'
  // sono parole di una lingua: in inglese ovest e' `W`, e una lettera dentro il formattatore
  // resterebbe italiana senza che la guardia delle traduzioni se ne accorga.
  "coord.n": "N",
  "coord.s": "S",
  "coord.e": "E",
  "coord.w": "O",
}
