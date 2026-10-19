# Per Claude Design -- Planner, Eventi e Macchia Rossa (e tre ritocchi a Trova)

Da Claude Code, 19/10/2026. Marco vuole il disegno del Planner completo: entrano Macchia Rossa,
meridiano di Marte e un terzo modo «Eventi». Decisione in `docs/adr/0023-planner-e-progetti.md`,
sezione "Eventi e Macchia Rossa". Le parole fra «» sono proposte: Marco le approva sulla tavola.
I numeri li manda l'app; qui servono forma, posto e stati.

## Trova v22: tre ritocchi

Controllata nel codice: le quattro aggiunte ci sono, una funzione sola per l'ellisse, ora del
transito giusta, telefono a posto. Restano:

1. **Il perche' della pillola spenta si vede**, non solo al passaggio (`title`): sul telefono non
   c'e' il passaggio. Una riga sotto, come gli `altri` di Crea.
2. **«Entra nel campo di {corredo}» col nome del corredo**, non solo dell'ottica (oggi «di Askar
   103APO»): il campo dipende anche dalla camera.
3. **Due corredi scelti**: l'oggetto deve entrare in tutti e due, e la pillola li nomina («di
   {corredo 1} e {corredo 2}»). Oggi conta solo il primo e non lo dice.

Testi nuovi da far approvare a Marco: «Nessun frame in archivio: si riempie con la scansione.»,
«Spento: scegli un corredo, serve il suo campo.»

## Sistema solare: Giove e Marte

1. **Macchia Rossa**, solo con Giove. Sotto i numeri: «Macchia Rossa al meridiano: 23:42 · 09:38»
   (i passaggi della notte scelta). Sulla curva d'altezza ogni passaggio e' una fascia di 50 minuti
   prima e dopo (Sky & Telescope: ben visibile in quella finestra), con l'ora al centro. Toccando
   la fascia l'ora va li'.
   - Riga piccola: «Macchia Rossa a 91° (Sistema II) il 1/6/2026, deriva 1.75° al mese: cambia in
     Impostazioni.» E' la settima riga della sezione «Planner» delle Impostazioni: longitudine,
     data, deriva.
   - Il disco di Giove si disegna girato al meridiano centrale dell'ora scelta (mappa OPAL
     cilindrica gia' in uso), con la Macchia dove sta. Spostando l'ora, il disco gira.
   - Stato: Giove sotto l'orizzonte in tutti i passaggi della notte: «Nessun passaggio con Giove
     sopra {altezza minima}°.»
2. **Marte**: «Meridiano centrale 215°» sotto i numeri, e il disco girato a quel meridiano, che
   gira con l'ora. Mappa pubblica di Marte (NASA/USGS): la licenza si controlla sulla sua pagina,
   credito visibile come le altre.

## Terzo modo «Eventi»

Accanto a «Cielo profondo» e «Sistema solare», stesso selettore. Gli eventi del sito attivo,
in una lista per data, dal piu' vicino. Filtro a pillole: «Tutti» · «ISS» · «Eclissi» ·
«Occultazioni». Il corredo resta: serve al campo sulla carta.

Una riga per evento, aperta mostra la carta. Tre tipi:

1. **Transito della ISS sul Sole o sulla Luna.**
   - Riga: data, ora al secondo («14:32:07»), «sul Sole» / «sulla Luna», durata («1.3 s»).
   - Aperta: carta del disco (Sole del giorno o Luna con fase, come nel Sistema solare) col campo
     del corredo e la traccia della ISS che lo attraversa, in scala (la ISS circa 50″, il disco
     circa 1800-1900″). Numeri: diametro apparente della ISS, distanza, larghezza della striscia
     («6 km»), altezza del Sole o della Luna.
   - Giudizio geometrico, senza soglia: «✓ sei nella striscia» / «! fuori di 12 km dalla linea
     centrale». Uno schema semplice: la striscia, la sua linea centrale, il punto del sito. Niente
     mappa geografica (servirebbero tessere di terzi).
   - Riga piccola: «Orbita del 19/10: la previsione si rifa' a ogni orbita nuova.» Lontano nel
     tempo l'ora si sposta.
   - Sul Sole: l'avvertenza del filtro, la stessa del Sistema solare.
2. **Eclissi di Sole o di Luna** visibili dal sito.
   - Riga: data, tipo («parziale di Sole», «totale di Luna»), grandezza dal sito.
   - Aperta: i contatti con l'ora e l'altezza (Sole: primo, massimo, ultimo; totale o anulare anche
     secondo e terzo. Luna: penombra, ombra, totalita'), il disco al massimo col campo del
     corredo. Credito visibile: «Eclipse Predictions by Fred Espenak, NASA's GSFC».
   - Un contatto sotto l'orizzonte: «sotto l'orizzonte» al posto dell'ora; con altezza sotto la
     minima, il giudizio «basso» come nel Sistema solare.
3. **Occultazione lunare di un pianeta.**
   - Riga: data, pianeta, «sparisce alle 21:14 · ricompare alle 22:31».
   - Aperta: la Luna con fase e il pianeta in scala, il punto del lembo dove sparisce e ricompare
     (lembo chiaro o scuro, scritto), altezza della Luna.

Stati nei Tweaks:
- nessun evento nel periodo: «Nessun evento visibile da {sito} nei prossimi {n} giorni.»;
- orbita della ISS non scaricata (rete): le altre righe restano, la ISS dice «Orbita della ISS
  non scaricata: riprova.»;
- senza sito: «Serve un sito: gli eventi dipendono da dove sei.»

Periodo della lista: tendina, partenza da decidere col backend (il numero lo dico io con la
fonte); disegnate «{n} giorni».

## Telefono

Il terzo modo nelle pillole dei modi. Eventi in lista a tutta larghezza; la riga aperta sale nel
foglio dal basso come gli oggetti. Giove e Marte come sul desktop, la fascia della Macchia sulla
curva tocca bene (44 px).

CHANGELOG e DECISIONI come al solito.
