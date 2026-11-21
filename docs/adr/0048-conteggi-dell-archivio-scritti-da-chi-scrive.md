# 0048 -- Conteggi sull'intero archivio scritti da chi scrive, con un segno di freschezza

**Stato:** accettata, 21/11/2026 (passo 6.19; regola di Marco del 22/9/2026, "una lettura non
calcola", e del 20/11/2026, "dati derivati materializzati"). Estende ADR 0047 a due conteggi che
oggi si rifanno a ogni GET.

## Contesto

Scansione del 20/11 (passo 6.10), archivio sintetico del budget (passo 6.15), misurato di nuovo il
21/11 sul portatile, migliore di cinque, da 1.000 a 10.000 frame:

- le voci dei nove criteri dell'Archivio (`spine/archive_criteria.offered`): da 2,3 a 25 ms, perche'
  ogni apertura della pagina rileggeva tutti i frame per contare anni, siti, ottiche, camere,
  filtri e produzioni;
- gli offset delle camere in Attrezzatura (`spine/inventory._OFFSETS`): da 0,5 a 9 ms, frame, ponte,
  file e schede uniti a ogni lettura;
- Cerca, le notti di un oggetto (`spine/search._BY_OBJECT`): 11-17 ms per domanda a 10.000 frame,
  due domande per ricerca, perche' cercava il nome a ogni frame invece che a ogni oggetto.

## Decisione

- **`archive_options` (derivata):** le voci dei nove criteri con nient'altro scelto e le righe che
  darebbero. La riscrive `archive_criteria.write` a fine giro di group e identify, dopo una
  risposta su un mosaico (nessun giro la segue), dopo il caricamento del catalogo e all'avvio
  (cosi' un codice nuovo riconta una volta, senza versione da alzare). Etichette e ordine restano
  in lettura dalle tabelle piccole: una rinomina si legge subito.
- **`derived_fresh`, il segno:** chi scrive la tabella lascia la riga; un trigger su ogni suo
  ingresso (frame, oggetti, risposte sui mosaici, notti, setup, filtri; il catalogo con la sua
  versione, scritta una volta a caricamento: un trigger su ognuna delle 22.080 voci portava il
  caricamento da 0,23 a 0,99 s) la toglie. Senza
  la riga la pagina conta dai frame come prima. Conta e segno in una transazione `BEGIN IMMEDIATE`:
  uno scrittore che committa fra le letture e il segno aspetta, e non lascia fresca una conta
  vecchia. Diverso da `gear_usage`, che si fida dei giri:
  qui una scrittura senza giro (un mosaico, un test, uno scrittore dimenticato domani) non lascia
  a schermo un numero falso, al piu' una pagina lenta fino al giro dopo.
- **Un criterio con altre scelte accese si conta in lettura**, come prima: le combinazioni sono
  troppe per scriverle, e chi sceglie ha gia' ristretto le righe.
- **`camera_offsets` (derivata):** la riscrive `night_measures.rebuild` insieme al ponte da cui
  viene, nella stessa transazione; nessun segno, perche' il ponte stesso si fida degli stessi giri.
- **Cerca** non scrive niente: la domanda prende prima gli oggetti col nome (pochi), poi i loro
  frame sull'indice `frames_object`. Stesse notti, stesso ordine.

## Conseguenze

- Sull'archivio da 10.000 frame: Archivio da 68 a 38 ms, Cerca `M` da 41 a 20 ms, `2024` da 53 a
  5 ms, Attrezzatura piatta; risposte identiche byte per byte a 1.000 e 10.000 frame.
- L'Archivio non e' ancora piatto: produzioni e filtri delle righe della pagina, la pagina stessa,
  i totali e i frame senza oggetto leggono i frame (17, 8, 5 e 5 ms a 10.000). Passo 6.19.1.
- Chi aggiunge un ingresso alle voci dell'Archivio (una tabella nuova nella regola) aggiunge i suoi
  trigger in `schema.sql`, o le voci restano fresche su dati vecchi.
