# La coda

Cosa viene dopo, nell'ordine in cui si fa. Si riscrive, non si appende: quando un punto e'
fatto, sparisce, e la storia sta in git. Una voce dice **cosa non va, dove, la misura e il
rimedio**; si ri-misura prima di aprirla, perche' e' stata scritta su uno stato che puo' essere
cambiato. Le decisioni da tenere a mente stanno in mezzo, le idee parcheggiate in fondo.

## Da riparare, nell'ordine

Prima cio' che rompe, poi cio' che fa dire all'archivio cose false, poi le macchine che non
guardano, poi efficienza e doppioni.

### 1. Rompe

Niente di aperto.

### 2. L'archivio dice cose false, e non si vede

3. **Le ore restano doppie quando ne' il grezzo ne' la copia portano un nome che l'app conosce.**
   Il marchio di riscrittura chiude gli altri casi: se la copia non dice di essere calibrata e nel
   suo header il vocabolario non riconosce nessun software, due nomi diversi possono essere due
   programmi o due grafie dello stesso, e non si indovina. Colpisce chi riprende con un programma
   fuori dai quattro ed elabora con un altro. A pari indizi i gemelli contano tutti e due, ed e' la
   regola. Si chiude con una domanda in Da confermare, per gruppo: **quale dei due file e'
   l'originale**. Nello stesso posto una contraddizione in tre case: `tests/synthetic.py` fa
   scrivere `SWCREATE` ai profili di Voyager e SGP, mentre `tests/test_fits_header.py`
   (`ALIAS_SECONDARI`) e `tests/test_normalize_rewrite.py` dichiarano `PROGRAM` e `SWMODIFY`;
   nessuna e' verificata finche' non arrivano header veri.
9. **Due limiti dei file solo online, dichiarati.** Sul Mac elencare una cartella solo online ne
    scarica l'elenco (TN3150, Apple), mai provato senza un Mac, e costa una lstat in piu' a FITS. Un
    frame gia' in archivio lasciato poi solo online non si riapre in scansione, ma `solve` lo
    leggerebbe per intero. Il segno di Windows non si e' visto su un file vero.
10. **Da misurare su un NAS vero** quanto aspettano registrazione e conta di una cartella di rete che
    non risponde -- risolvere il percorso e chiedere se risponde vengono prima del tetto della conta,
    e non ne hanno uno (una sonda con due attese finte da 2 s ha risposto in 4 s col tetto a 0,5) --
    e se il tetto basta a dare un numero su una condivisione lenta. Sulla macchina di Marco c'e' solo
    `\\localhost\D$` (11/9/2026). Anche `GET /folders` aspetta la risposta di ogni cartella, una
    per una e senza tetto (`backend/astrolog/api/folders.py`): l'elenco delle cartelle si blocca.
51. **Due file troncati con l'header identico diventano un frame solo**: dove non ci sono pixel da
    leggere l'impronta ripiega sull'header (`fits/header_read.frame_fingerprint`), e due header
    uguali danno la stessa impronta. Misurato il 28/9/2026 su cinque troncati sintetici; con header
    veri, che differiscono almeno per `DATE-OBS`, e' improbabile, ma nessuna prova lo esclude.
55. **Una cartella sola fermata prima di cominciare lascia la sua ricevuta aperta per sempre**
    (provato il 29/9/2026): la lettura di piu' cartelle butta a fine corsa le ricevute delle
    cartelle mai cominciate (`api/scan._scarta_le_mai_iniziate`), quella di una cartella sola
    (`api/scan.start_scan`) no, e `GET /scan-runs` la mostra come una lettura mai finita. La strada
    la prendono la cadenza del NAS (`api/app.py`) e la rotta `POST /folders/{folder_id}/scan`;
    nessuna pagina, che leggono tutte le cartelle insieme.
49. **`objects.by_key` puo' prendere l'oggetto sbagliato se un nome primario fuori catalogo e' uguale
    a uno slug**: cerca le due cose con un `OR`, e un header con `OBJECT = m-31` arriva intatto a
    `identify` (`clean_object_name` toglie solo spazi e parole di tavolozza). Se `identify` lo
    risolva poi sul catalogo, e quindi se il caso possa nascere, non l'ha misurato nessuno.

### 3. Macchine che non guardano

18. **Promesse con la prova a meta', o senza.** Audit del 23/9/2026 sulle tabelle *Cosa chiede
    l'utente* dei contratti: ogni prova nominata esiste e passa, ma 19 righe su 246 sono provate a
    meta' e 6 sono senza prova (dichiarate). Quelle che farebbero piu' male, nell'ordine:
    - **un pezzo scritto a mano e poi nominato dai file** non deve diventare un doppione, con le ore
      spartite su due righe: nessuna prova, la riga di `attrezzatura.md` cita il verso opposto;
    - **la scansione a cadenza sul NAS** (`ASTROLOG_SCAN_EVERY_MIN`, `backend/astrolog/__main__.py`)
      non e' letta da nessuna prova: rotta, spegnerebbe la scansione senza dirlo;
    - **il collegamento dell'Archivio**: si prova che la scelta finisce nell'indirizzo, non che
      aprendolo si veda la stessa vista con la stessa ricerca;
    - **una correzione sulla scheda resiste a una nuova lettura**: provato per pixel e colore della
      camera, non per gli altri campi;
    - **l'altitudine che manca "me lo dice"** (`sito.md`): il backend manda `site_no_elevation`, e lo
      schermo non la mostra affatto. O si mostra, o la riga del contratto si corregge;
    - poi, piu' piccoli: il catalogo ("le ore non si sparpagliano", "senza rete") provato di sbieco;
      l'ordine "dal piu' ripreso" dell'Attrezzatura con un oggetto solo nel banco; Esc sul pannello
      della Luna e il tasto indietro fra le sezioni delle Impostazioni; le due query per pagina delle
      Notti; il contatore delle risposte in mano, l'ordine delle schede e "dichiarato da te" in Da
      confermare; in `spina.md` quattro prove che esistono e la riga non cita
      (`test_scan_root_gone_midway_aborts_without_marking_missing`,
      `test_no_autostart_and_precheck_409s`, `test_scan_frames_per_second_does_not_regress`, e il
      verbo del pulsante in `test_scan_lock_stop_and_the_button_verb`); in `sito.md` tre righe che
      citano un file invece di una prova; e le prove del catalogo col nome in italiano
      (`tools/test_catalogo.py`, `tools/test_simbad.py`), sette delle quali citate in `catalogo.md`.
19. **Una misura di tempo non ha niente che le impedisca di girare sotto carico.**
    `test_catalog_load_seconds_does_not_regress` (`backend/tests/test_perf_catalog.py`, `lento`) confronta
    un tempo col tetto di `backend/tests/perf_baseline.json`. In CI gira **da solo** -- il job
    `lento` non usa `-n auto`, ri-misurato il 16/9/2026 -- ma chi lancia la suite intera in
    parallelo in locale lo misura con altri 23 processi addosso, e cade (0,77 s contro il tetto).
    Un rosso che non dice niente insegna a non fidarsi dei rossi. Si chiude dando al test una
    guardia che si rifiuti di misurare quando non e' solo, invece di dipendere da come lo si lancia.
57. **"Una parola sola e' una domanda sola" non morde** (`frontend/tests/archivio-barra.test.tsx`,
    29/9/2026): togliendo alla barra dell'Archivio l'annullamento dell'attesa fra un tasto e
    l'altro (`BarraDellArchivio.tsx`, il `clearTimeout`), o portando l'attesa a zero, il test resta
    verde, perche' nel banco le richieste intermedie non partono comunque. Va provato dove la
    richiesta di ogni tasto si vedrebbe.
20. **La guardia sull'anonimato del corpus e' cieca fuori dal suo elenco.**
    `test_no_real_site_coordinates_in_the_corpus` (`backend/tests/test_header_corpus.py`) guarda le
    chiavi di `GEO_KEYS`: aggiungendo `GEOLAT`, `GEOLON` e `SITE` con un paese vero i test restano
    verdi (14/9/2026). Fuori anche `DATE-LOC` e i campi di testo libero. Si chiude con un criterio che
    non sia un elenco (un valore che somigli a una coordinata, un divieto sui campi liberi); e vale
    anche per i documenti, dove il 14/9/2026 sono finiti tre nomi di persona.
21. **Tre macchine che il frontend ha indebolito.** (a) `pytest tools` non e' autosufficiente: senza
    `frontend/node_modules` i test di `tools/tipi.py` cadono dicendo "il generatore e' fallito"
    invece di "manca npm". (b) `tools/test_chiave_due_case.py` e' cieco alla casa che sparisce: tolto
    `frontend/src/api/client.ts` risponde `1 passed`. (c) La mutazione notturna guarda solo
    `backend/astrolog`: il frontend e `tools/` stanno fuori dal controllo piu' severo.
22. **Una promessa d'intestazione senza macchina:** `backend/astrolog/api/models_review_groups.py`
    promette che ogni gruppo porta chiave e `answer`: oggi e' vero anche per `MosaicCandidate`, ma
    nessuna prova lo controlla.
23. **Un ramo che non esiste passa tutte e due le guardie.** La tabella delle situazioni di
    `docs/domini/spina.md` e `BRANCHES` in `backend/astrolog/spine/identify_decide.py` si controllano
    a vicenda: una riga inventata in tutti e due resta verde (12/9/2026). Manca la macchina che chieda
    a ogni ramo un produttore in `decide` e un test.
24. **La purezza di `identify_decide`, `identify_score` e `identify_geometry` e' scritta e non fatta
    rispettare:** aggiungendoci `sqlite3` o `catalog.lookup`, `lint-imports` resta verde (il parser
    `catalog.designation` invece e' puro, e `identify_score` lo usa gia'). Serve un contratto loro:
    quello dei moduli puri in `backend/pyproject.toml` vieta `astrolog.spine`, e i tre si importano
    fra loro.
25. **Promesse d'intestazione senza rosso** (rotte una per una il 14/9/2026, suite verde):
    (a) `backend/astrolog/spine/rigless.py` promette la normalizzazione di
    `declarations.instrument_name`, e con uno `strip()` nudo `INSTRUME='(1)'` diventa un nome.
26. **"Idempotente" e' scritto e non e' vero, e il banco non puo' accorgersene** (22/9/2026).
    `backend/astrolog/vocab/header_value.py` lo dichiara in intestazione, ma l'indice ASCOM si toglie
    **una volta sola**: `'ZWO Focuser (1) (2)'` da' `'zwo focuser (1)'`, che ripassato da'
    `'zwo focuser'`. La prova (`test_header_value_is_idempotent_and_keeps_distinct_things_distinct`)
    misura l'idempotenza su `'ASCOM ToupTek FilterWheel'`, che un indice in coda non ce l'ha: non
    puo' fallire. Trovato dal revisore togliendo la doppia normalizzazione dai chiamanti di
    `declarations.rename`, che allinea lettore e scrittore sulla passata singola. Non si sa se un
    doppio indice esista in un header vero: si ripara la promessa (il ciclo) o la si toglie, e in
    tutti e due i casi il campione della prova deve portarne uno.
27. **Promesse del mosaico senza rosso** (14/9/2026): (a) "l'app propone e non fonde niente" e'
    provata solo sulla proposta; (d) il pannello senza rotazione e' provato solo nella geometria
    (`backend/tests/test_mosaic_geometry.py`), non nel raggruppamento.
28. **I tipi costano al push:** `tools/test_tipi.py` lancia tre volte il generatore, e ogni
    estrazione dello schema OpenAPI costruisce un'app vera e ricarica l'intero catalogo.

### 4. Efficienza, misurata

29. **Il solver e' il 98% del tempo.** Sull'archivio vero a cache vuota (12/9/2026): 5.952,9 s contro
    84,1 di scansione, 2,8 di normalizzazione, 6,3 di identificazione e 1,5 di raggruppamento; 0,543 s
    a frame. **Deciso da Marco: si rimanda al pacchetto**, dove si misura ASTAP su un NAS arm64 vero.
    Accanto, le misure che dicono di **non** limare altrove: `identify` rilegge il catalogo 736 volte
    per corsa, ma pesa 6,3 s; `normalize` fa ~19 query a frame, ma dura 2,8 s; il commit per frame
    costa 4,3 s ma e' una promessa con le sue guardie, e non si tocca; indici, memoria e thread della
    scansione sono gia' ottimali. Resta una pulizia: `_as_the_user_said`
    (`backend/astrolog/spine/identify.py`) interroga `declarations` una volta a frame anche a mani
    vuote, ~11.000 volte per sapere "niente".
31. **La suite ricostruisce il modello del catalogo per ogni worker** (24 processi x 0,271 s): il
    fixture e' di sessione ma per processo, senza lucchetto fra processi.
32. **Chi non ha nemmeno un `IMAGETYP` paga il solver sui suoi dark.** Un file senza tipo passa dal
    cielo, e un dark con pixel caldi fitti o a gruppi il solver lo scambia per stelle -- senza focale
    ne' puntamento arriva al tempo massimo di ASTAP per file, con la focale ma senza puntamento resta
    comunque una ricerca lunga --, e la rinuncia non e' in cache (si ripaga a ogni DB ricreato).
35. **Una lettura non calcola mai, e ci sono ancora letture che calcolano** (Marco, 22/9/2026).
    La regola ha la sua macchina, e copre la geometria dei mosaici, nell'Archivio e in Da
    confermare, i conti dell'Attrezzatura e i candidati degli oggetti in dubbio (i contratti *"Chi
    legge legge cio' che e' scritto"*, *"Da confermare legge le proposte scritte"*, *"L'Attrezzatura
    legge l'uso scritto"* e *"Da confermare legge i candidati scritti"* in `backend/pyproject.toml`).
    Fuori restano, dall'audit
    delle pagine del 23/9/2026 su archivi sintetici fino a 100.000 pose:
    - il **contatore della barra laterale** chiede tutta Da confermare (`frontend/src/Layout.tsx`)
      a ogni pagina e a ogni ritorno sulla finestra (`main.tsx` crea il client senza
      `staleTime`), e paga i lettori qui sotto. Merita una lettura sua;
    - dei **lettori di Da confermare**, ognuno parte dalle pose che riguardano la sua domanda
      tranne la tendina dei corredi e l'elenco degli oggetti, che contano ancora ogni posa a ogni
      apertura, dall'indice e non dalla tabella;
    - e, piu' piccoli, le pose per cartella in
      `GET /folders`, il residuo della spina che conta `measure` su ogni posa a ogni battito
      (`stages.pending_by_stage`: lo stadio non gira mai), e gli errori di una lettura letti tutti
      per tagliarne una pagina (`api/scan.py`).
    Ogni ricalcolo tolto entra in un contratto, o in una prova che confronta cio' che e' scritto con
    cio' che le regole direbbero (`tests/test_header_asks.py`).
48. **La normalizzazione tiene in mano camera, copia e marchio di ogni posa in coda per tutto il
    giro** (`spine/normalize.py`, `_before_the_round`; `spine/copies.py`): e' il prezzo del giro
    unico. Misurato il 28/9/2026 su 5.800 pose sintetiche alla prima corsa: picco 2.653 KB contro
    1.174 del giro doppio, con tempo e istruzioni SQL piu' bassi. Pesa solo alla prima lettura di
    un archivio grande; va rimisurato su un NAS vero prima di decidere se vale un rimedio.
52. **Una risposta sul tipo riscrive il segno dell'attesa di ogni posa senza tipo**
    (`typeless.declare`), dove basterebbero quelle della cartella: costa in proporzione alle pose
    senza tipo dell'archivio, una volta per cartella risposta. Le pose della cartella
    `declare` non le ha: le trova `apply_answer`, subito dopo.

### 5. Doppioni -- lo stesso pezzo scritto piu' volte

46. **Piu' piccoli**: `CATALOG_PRIORITY` senza sei sigle che `parse` produce; il numero "110 voci,
    42 nomi comuni" scritto in piu' case del codice; frasi dei contratti copiate nelle docstring (da
    ricontare prima di aprire); i siti senza una casa in lettura come oggetti e notti; e
    `identify_store.object_by_name` e `name_owner`, che fanno quasi la stessa query. Non sono
    doppioni, misurato il 28/9/2026: i tre `detach` staccano tabelle diverse e
    `typeless_answer.detach` li compone, i tre `drop_empty_*` puliscono tre tabelle con tre regole.
    E la riga che chiede a SQLite il piano di una query, scritta a mano in dieci file di prova (`grep
    "EXPLAIN QUERY PLAN" backend/tests`): un aiutante in `backend/tests/conftest.py`. Lo stesso
    per lo stadio tenuto fermo a meta' con una porta: aiutante `_holding` in
    `backend/tests/test_api_scan_all.py`, ricopiato per intero in `test_api_scan.py` e
    `test_review.py`.

## Il piano

Deciso a video con Marco il 10/9/2026: la spina onesta **su un archivio qualunque**, poi si
alleggerisce, poi `measure`. Le fasi 0 (la macchina: rimandi e mutazione), 1 (cio' che rompe) e 2
(cio' che mente senza che si veda: copia calibrata, ora locale, specifiche della camera, cloud, reti,
frame che spariscono, filtro e camera che mancano) sono fatte, salvo le voci ancora aperte nelle
prime due sezioni di *Da riparare*. Restano:

- **Fase 3 -- alleggerire.** Coi numeri gia' misurati: i doppioni e i guadagni della sezione efficienza. Le voci si nominano con la loro frase, mai col numero.
- **L'ordine da qui** (Marco, 27/9/2026, scelto a video): prima i difetti piccoli e visibili, poi
  l'Archivio (le pagine che ci sono si chiudono), poi le prime due sezioni di *Da riparare* per
  temi, una fetta per tema, poi la fase 3 e la fase 4. Planner e Progetti vengono dopo, quando il
  cuore e' a posto.
- **La grafica si rifa'** (Marco, 29/9/2026): ridisegna tutte le pagine con Claude Design. Finche'
  il disegno nuovo non arriva si lavorano in ordine le voci di *Da riparare* che non toccano lo
  schermo -- quelle che fanno dire all'archivio cose false, poi le macchine, l'efficienza e i
  doppioni del backend --, e restano ferme la sezione *La veste, cose che restano da fare* del
  Parcheggio, i doppioni dell'interfaccia e tre voci che toccano lo schermo: *Le ore restano doppie
  quando ne' il grezzo ne' la copia portano un nome che l'app conosce* (la sua domanda in Da
  confermare, che Design deve sapere in arrivo), l'altitudine del sito che manca (in *Promesse con
  la prova a meta', o senza*) e *Aperto un campo col suo bottone, il fuoco non ci va*.
- **Fase 4 -- `measure`.** Contratto e posto nei contratti dei moduli, poi il codice: eccentricita', fondo cielo,
  tilt. Per ultima apposta: su una catena con difetti muti misurerebbe la qualita' con dati che
  mentono.

## Adesso

1. **La spina.** Schema e contratto sono fatti (i contratti dei moduli in
   `backend/pyproject.toml`, `backend/astrolog/schema.sql`, [`domini/spina.md`](domini/spina.md)).
   **`scan`, `normalize`, `solve`, `identify` e `group` sono costruiti e misurati sull'archivio
   vero**; il worker e' un thread nel processo del backend, e ASTAP gira come sottoprocesso. Il
   **catalogo** e' portato e caricato ([`domini/catalogo.md`](domini/catalogo.md)), e `identify`
   propone giusti il 97,1% dei 577 bersagli col nome comune (i 17 mancati non sono errori veri) e 53
   frame su 53 di sei fotografi diversi. Finche' ASTAP non e' installato i frame non hanno oggetto, ed
   e' voluto: si aspetta il cielo. Il **sito** c'e' ([`domini/sito.md`](domini/sito.md)), e delle
   **effemeridi** ci sono la Luna e il buio ([`domini/effemeridi.md`](domini/effemeridi.md)): fase,
   quanto e' illuminata, sorgere e tramontare, e le cinque fasce del cielo, con la loro rotta.
   Restano `measure` e, delle effemeridi, la visibilita' di un oggetto -- che si porta quando nasce
   la schermata che la chiede.
2. **Il prototipo del pacchetto desktop, prima che costi**: Tauri 2 + un sidecar Python vuoto + ASTAP,
   firmato e **notarizzato su macOS**. Se passa, e' la strada; se no, Electron (+80 MB).
3. **Le pagine desktop**, in TypeScript, una alla volta. Ne esistono
   quattro: la **prima pagina** col contatore, il **primo avvio**, **Da confermare** con
   tutte le sue sezioni, e l'**Archivio** ([`domini/archivio.md`](domini/archivio.md)). Con loro
   ci sono la guardia di accessibilita', la traduzione inglese con la sua guardia, il pavimento di
   copertura e la [guida utente](guida-utente.md). **Da adesso una pagina nuova nasce vestita**:
   i mattoni ci sono (punto 4), e costruirla nuda vorrebbe dire rivestirla dopo. Le quattro che
   c'erano prima si vestono nelle due fette che restano. **Lo scheletro che le tiene insieme e' deciso**
   -- i tre gruppi, cosa vive in alto, come si piega su un telefono -- e sta in
   [`domini/navigazione.md`](domini/navigazione.md); una voce compare nella barra **solo quando la
   sua pagina esiste**. Nell'ordine, cio' che resta:
   - **Notti** c'e' ([`domini/notti.md`](domini/notti.md)): l'elenco delle notti, con dentro
     oggetti e filtri, e in cima cio' che spiega un elenco corto -- i frame fermi, col gesto che
     li sblocca, e la lettura non finita. **La Luna c'e'**, calcolata a ogni apertura e non
     conservata. **Il meteo c'e'** (`docs/domini/meteo.md`). Restano le **misure dei frame**
     (la casella che misura) -- e il **modale**, che e' lo stesso dell'oggetto e della libreria e
     si fa alla fine, quando ci saranno i dati da metterci (Marco, 20/9/2026: prima tutte le
     pagine);
   - **Attrezzatura** c'e' in lettura ([`domini/attrezzatura.md`](domini/attrezzatura.md)): i
     pezzi per genere coi loro numeri, i corredi con quanto cielo inquadrano **misurato**, i
     filtri con le loro bande. Degli **strumenti** ci
     sono anche i gesti: scriverne uno a mano e correggerne la scheda da li' invece che da *Da
     confermare*. **Ruota, focheggiatore e camera di guida li legge la scansione** (`FWHEEL`,
     `FOCNAME`, `GUIDECAM`), con le ore: a mano restano da scrivere la **guida** e il
     **riduttore**, che nessuno dei due programmi di cui abbiamo un header vero nomina. **La montatura ha le sue ore**, dai file o dalla scheda
     del corredo, e **filtri e corredi si scrivono anche a mano**. L'Attrezzatura e' chiusa;
   - nell'**Archivio** le ore per filtro ci sono, e la costellazione si legge col nome latino
     ufficiale, e la carta di un mosaico apre i suoi **pannelli** (nell'elenco no: una riga di
     tabella che si allunga rompe le colonne, e il posto giusto e' il modale dell'oggetto, che
     Design disegnera'). Manca l'**etichetta dei progetti**, che aspetta i Progetti.
4. **La veste, in due fasi** (Marco, 16/9/2026, che ha portato il consiglio di un terzo e ha
   chiesto tre direzioni da guardare prima di decidere). Misurato mentre si apriva la voce: 25
   file `.tsx`, **nessun foglio di stile**, 106 elementi grezzi ricorrenti -- il rischio di
   dover riscrivere il DOM pagina per pagina non e' ipotetico. Quindi: **i token subito** --
   colori, spazi, raggi, tipografia come variabili in una casa sola -- e i **mattoni**
   (`Card`, `DataTable`, `StatusBadge`...) quando **due pagine vere** li chiedono, mai a
   tavolino: un mattone inventato prima dei dati e' una gabbia da cui la terza pagina deve
   uscire. **Niente modalita' a luce rossa** (Marco, 16/9/2026:
   non la vuole). Resta invece la regola che ne era la conseguenza, con una ragione sua: **il
   colore da solo non dice mai niente** -- WCAG 2.2, criterio 1.4.1 *Use of Color*, livello A --
   perche' chi non distingue verde e rosso deve capire lo stesso se un frame e' a posto o
   aspetta. **Il giro con Claude Design**: la sua consegna si verifica punto per punto (completezza
   contro il brief, contrasto **misurato** coi token e non dichiarato) e le correzioni tornano **alla
   fonte**, non si fanno da noi, perche' il porto e' alla lettera e una versione successiva
   cancellerebbe le nostre.
   **Dove siamo**: il foglio della consegna e' nel repo alla lettera, ed e' **uno**
   (`frontend/src/stili/astrolog.css`, v8): la consegna stessa ha unito i due di prima. Sono
   vestiti il guscio, la **Casa**, **Da confermare** con le sue dodici sezioni e il **primo
   avvio**, e con quest'ultimo i dodici `<p role="alert">` sparsi sono diventati `Avviso`. I
   mattoni nostri sono `Sezione`, `Riga` (con dentro `Dettaglio` e `Prova`), `Campo`, `Bottone`
   e `Avviso` -- e le prove che li difendono stanno in `tools/test_controlli_*.py`: il contrasto
   **misurato** sui valori veri, una classe
   che il foglio non ha, una classe scritta fuori dal suo mattone, un avviso senza il suo mattone,
   il foglio della consegna che nessuno ha toccato, e i due confronti sui numeri che il foglio
   porta dentro di se' (`tools/controlli_foglio.py`).
   Il **primo avvio** e' portato **intero**, collaudato dal vivo su tutte e quattro le schermate,
   e da questa fetta chiede anche **che cielo hai**: le nove classi di Bortle sono un mattone
   (`frontend/src/ScalaDelCielo.tsx`), che nasce qui perche' la stessa scala serve alla scheda del
   luogo e alla barra -- il foglio la disegna gia' in due forme. L'**Archivio** e' vestito nelle sue
   due viste, coi filtri di ogni oggetto, e la sua **barra** cerca, stringe e ordina davvero;
   un mosaico confermato e' una riga sola con la sua etichetta, e resta quella dei progetti, quando
   esisteranno. Dopo, `/design-sync` carica i componenti veri in
   Claude Design, e da li' in poi Design disegna le pagine nuove coi nostri mattoni invece che
   con dei disegni.
5. **Le effemeridi**: la **Luna c'e'** e **il buio anche** ([`domini/effemeridi.md`](domini/effemeridi.md)),
   coi loro moduli puri, il loro posto nei contratti dei moduli e la rotta `GET /tonight` -- le cinque fasce del
   cielo arrivano gia' divise e la tela della notte le disegna dietro la curva. Del Sole resta
   fuori cio' che nessuna schermata chiede ancora: **gli orari come numeri** (tramonto, fine del
   crepuscolo) e le **ore di buio**, che arrivano con le Notti. Resta **quanto sale un oggetto
   stanotte**, che si porta dalla cava (`old/backend/astrolog/ephemeris/`) col Planner.
6. **Il Planner e i Progetti**, poi la **Carta del cielo**, tutte e due su Aladin Lite v3.
7. **Il pacchetto**: immagine Docker con ASTAP dentro, multi-arch su runner arm64 nativi; su Windows e
   Mac un'app vera con Tauri 2 e il backend come sidecar (PyInstaller), installer firmati, updater
   firmato.
8. **Il mobile**, per ultimo, a desktop funzionante: tablet e telefono, su ogni pagina.

## Nasce con...

File e macchine nominati dal metodo che **non esistono, o esistono a meta'**, e con quale punto
arrivano. Una riga sparisce quando la cosa c'e' tutta; quando l'innesco e' gia' passato lo dice la
colonna di destra, invece di spostarsi in silenzio su un innesco piu' comodo.

| cosa | con |
|---|---|
| `THIRD_PARTY.md` **generato** (`pip-licenses`, `license-checker`) con ogni dipendenza, la licenza e i crediti obbligatori (ESA/Gaia/DPAC, ASTAP, Aladin, HYG, OpenNGC, Stellarium, SIMBAD) | il pacchetto |
| in pre-commit: il formato del frontend in controllo. Prima serve la **configurazione**: `frontend/` non ne ha, e il 15/9/2026 `npx prettier --write` ha riscritto cinque file con le regole di serie (punti e virgola, 80 colonne), diverse dallo stile del progetto | **scaduta**: l'innesco e' passato il 13/9/2026 |
| in CI: `npm audit` e controllo licenze (le falle di Python e le ruote per le cinque architetture le controlla gia'; `--no-audit` sulla install in `.github/workflows/ci.yml` **disattiva** il controllo, non lo fa) | il pacchetto |
| lo stack delle **metriche** scelto con la misura su arm64 in mano: prima HFD/stelle/SNR da ASTAP, poi `sep`; con lui si porta `old/backend/astrolog/misura.py` coi suoi 8 test | `measure` |
| `tools/gen_changelog.py` e `release.yml` su tag `v*` (la versione vive gia' in `astrolog/__init__.py`) | il pacchetto |
| la pagina **Diagnostica** col bottone "copia" e il log ruotato accanto al DB | il pacchetto |
| esporta / reimporta le **dichiarazioni** dell'utente | **scaduta**: l'innesco (la seconda pagina) e' passato il 14/9/2026 |
| **la catena intera delle fasi e la ricevuta dell'ultima corsa**: `GET /pipeline/status` porta l'avanzamento di ogni stadio in `worker.stages`, ma `frontend/src/Scansiona.tsx` ne mostra solo la **fase corrente** coi suoi numeri, piu' le cartelle saltate o perse | la sezione Cartelle delle Impostazioni |
| `backend/tests/header/` **c'e'** (questo elenco e' l'unico: le skill vi rimandano): header veri di N.I.N.A. e ASIAIR, dell'archivio di Marco e di altri utenti, anonimizzati. **Mancano Voyager e SGP**: servono file veri. Ogni header nuovo entra prima della correzione che lo fa passare | appena arriva un file vero |
| nella CI: il build dell'immagine per amd64 e arm64 (runner `ubuntu-24.04-arm` nativo) | il pacchetto |
| pochi FITS **veri** con licenza compatibile e un database ASTAP piccolo (D05), per far girare in CI i test `lento` del solver (`tests/test_perf_solve.py` si salta finche' non gli si dice `ASTROLOG_TEST_FITS`) | appena arriva un file vero |
| **la misura del solver su un NAS arm64 vero** (1-2 GB di RAM): sul portatile la misura sta in `backend/tests/perf_baseline.json`, li' non si sa | il pacchetto |
| del frontend due macchine: la **guardia i18n per pagina** (oggi `frontend/tests/traduzioni.test.ts` confronta i dizionari interi) e quella che **vieta un letterale fuori da `t()`**, che oggi e' una regola senza guardia (un rilevatore a regex sul JSX litiga, e la ragione sta in `frontend/eslint.config.js`) | **scaduta**: l'innesco (la seconda pagina) e' passato il 14/9/2026 |
| **i dizionari si caricano a richiesta**: `frontend/src/i18n/index.ts` importa anche l'inglese, che viaggia nel bundle di ogni utente. Misurato il 20/9/2026 ricostruendo il bundle col dizionario inglese svuotato: **28.836 byte, 7.030 gzippati, il 6,5% del pacchetto** -- sei volte una fetta intera | quando l'utente puo' scegliere la lingua |
| **accendere il tema chiaro e la densita'**: il foglio li conosce gia' (`data-tema`, `data-densita` sull'elemento `html`) e reggono -- provati dal vivo -- ma non c'e' nessun posto dove chiederli | le Impostazioni |
| **riaprire il primo avvio dalle Impostazioni** (`docs/domini/sito.md` lo promette): la pagina c'e' e le sue sezioni pure, manca la voce che lo riapre | la sezione che lo ospitera' |
| **il nome dell'utente a schermo**: il primo avvio lo chiede e lo salva, ma nessuna pagina lo legge | la prima pagina che lo mostra |
| **il codice `no_star_database` di una corsa fermata** non ha ancora una frase a schermo: la sezione *Il riconoscitore* e il primo avvio dicono ora che il catalogo manca **prima** di far scansionare, ma chi sta guardando una corsa fermarsi legge ancora il codice e basta. La sezione *Le letture* non lo copre: li' ci sono le ricevute della **lettura delle cartelle**, e il catalogo manca allo stadio che risolve | la superficie che mostrera' la ricevuta degli altri stadi |

## Deciso, e da tenere a mente

Le definizioni della spina (notte, sessione, soggetto, cosa entra, identita' del frame, frame non
risolto) stanno nel [contratto](domini/spina.md), il mosaico nel [suo](domini/mosaico.md): qui
restano le decisioni che non hanno ancora un contratto.

- **La Casa si fa per ultima**, quando le pagine che riassume esistono e i suoi rimandi portano
  davvero da qualche parte (Marco, 16/9/2026). Fino ad allora resta com'e'. Quando si fara' avra'
  **cio' che i dati sanno rispondere**: una riga di stato (quante cose da confermare, com'e' andata
  l'ultima scansione), **l'ultima notte** (data, quanti giorni fa, sito, ore, pose, corredo, e gli
  oggetti coi loro filtri) e **tutto l'archivio** (notti dalla prima, sessioni, oggetti, ore totali
  con la media a notte; notti per mese, ore per mese, ore per filtro). Sopra questi due blocchi
  scenderanno, quando nasceranno i loro domini, la **barra della notte** (tramonto, buio, Luna,
  verdetto), ***Stanotte, in cielo*** con le curve di altezza e *Da riprendere*, le **carte del
  meteo**, le **prossime tre notti** e i **pianeti**: e' l'ordine che aveva il vecchio -- prima cosa
  puoi fare stanotte, poi com'e' andata. Tre regole del vecchio valgono e si portano: **niente
  "activity" a calendario e niente streak** (la griglia e' per mese, non per giorno), **un mese
  senza notti dice perche'** e non mostra uno zero, e **l'arco dell'archivio arriva a oggi oppure
  all'ultima notte, quale viene dopo**. Fuori restano, dichiarate: la **FWHM media** (la tabella
  c'e', ma `measure` non ha ancora lo stack) e la miniatura dell'immagine, che nel vecchio era un
  segnaposto.

- **I formati in v1** sono `.fits` e `.fit`; gli altri (`.fts`, `.fz`, XISF) quando un utente li
  chiede.
- **Cancellare**: mai un file sul disco. Dall'archivio dell'app si', con conferma; e' un'esclusione
  **dichiarata** ("non voglio questo") che sopravvive alle scansioni. Nomi e correzioni non si perdono.
- **Un utente, piu' siti, piu' corredi.** Due persone sullo stesso NAS = due istanze, due cartelle dati.
- **Meteo**: le fonti per compito, quando si scarica (lo storico da solo dopo la scansione, Marco
  25/9/2026) e dove si scrive stanno nel suo contratto, `docs/domini/meteo.md`.
- **Arricchimento online, a richiesta e in cache, mai nella spina**: SIMBAD TAP (una richiesta al
  secondo al massimo), Wikidata (CC0) per nomi e descrizioni nelle lingue, Commons per l'immagine con
  la riga di credito. `urllib` + JSON, niente `astroquery`. **Uno User-Agent con un contatto**
  (l'indirizzo del repo): senza, Wikimedia dal 2026 concede 10 richieste al minuto. Dove tace, "non
  arricchito" e' un campo. **Non offline-first**: la spina non tocca la rete in nessun punto, ma
  arricchimento e meteo sono benvenuti dove non sono il cuore.
- **Il motore della carta del cielo e' Aladin Lite v3, uno per Planner e Carta del cielo**: LGPL dal 2026-03,
  zero dipendenze, mantenuto dal CDS, tessere dal **proxy nostro con cache su disco**, N impronte e
  rotazioni native; rettangolo del campo, griglia del mosaico e orizzonte del sito li disegniamo noi.
  Sopra il fondo, uno **strato di stelle vettoriali nostro** (HYG, ~9.000 stelle a mag 6,5, CC BY-SA)
  e la Via Lattea: offline e a mani vuote il cielo non e' mai nero. `celestia_atlas` e' il ripiego.
- **Il cielo fotografico (DSS2) non sta mai nel pacchetto** (ODbL + copyright STScI): le tessere
  arrivano dal proxy e restano in cache; un bottone **"scarica il cielo per usarlo senza rete"**
  prende gli ordini fino al 5 (~1,1 GB, 13"/px), a scelta.
- **Un archivio in cloud si tratta senza servizi** (Marco, 11/9/2026): nessun account, nessuna rete,
  nessun collegamento a OneDrive, Dropbox o iCloud. L'app guarda solo il segno che il sistema mette su
  un file solo online: non lo apre, lo conta nella ricevuta e lo rivede alla scansione dopo. Sui Mac
  precedenti a Sonoma vale il segnaposto `.nome.fits.icloud`: una forma fissa scritta dal sistema, non
  una lista di nomi.
- **ASTAP e' impacchettato per tutti**, non opzionale: cosi' non c'e' da indovinare quale database
  serve a chi. **E quando non c'e', l'app lo dice prima della prima scansione** (Marco, 9/9/2026): il
  primo avvio resta di quattro passi per chiunque e ne aggiunge un **quinto solo se il solver non si
  trova** -- cosa si perde senza, il campo per dire dove sta, saltabile: **questa meta' e' fatta**,
  con la preferenza `astap_path` che vince sulla ricerca automatica e sulla variabile d'ambiente.
  Resta da fare l'**impacchettamento**, che vive con il pacchetto. Licenza: MPL 2.0
  il programma, Gaia DR3 i database (credito *ESA/Gaia/DPAC* obbligatorio). **Non** si spediscono
  `deep_sky.csv` e `hyperleda.csv` (non commerciali, e non servono).
- **Senza un sito di casa le notti non nascono** (il contratto in `docs/domini/sito.md`); il
  sito si dichiara nel primo avvio. `GET /api/v1/settings` lo dice in `missing`; di quel campo il
  primo avvio guarda solo `no_solver` (per il passo del riconoscitore), e **per il sito un avviso non si
  aggiunge** (Marco, 14/9/2026: il sito lo chiede il primo avvio). La sezione Frame senza sito
  di Da confermare e' un'altra domanda: elenca le coordinate che non tornano con un sito dichiarato.
- **Cio' che l'ASIAIR scrive in `TELESCOP` e' una montatura, e nasce come montatura** (Marco,
  14/9/2026). Il criterio e' il **software**, mai una lista di nomi (`vocab.software.telescope_is_mount`).
  Quei frame restano con un corredo **senza ottica** -- vero, invece che falso -- finche' non dici
  quale ottica era: la chiede *Frame senza ottica*, una volta per camera e focale. Su un database
  gia' normalizzato la riga vecchia resta fra le ottiche, perche' gli strumenti non si cancellano
  da soli (un pezzo e' roba dell'utente, un corredo e' un derivato): si ricrea, non si migra.
- **`OBJCTROT` non serve a orientare il campo**: segno opposto a `CROTA2`, offset che cambia a ogni
  rimontaggio della camera, e vale `0` come sentinella su meta' dei frame. La rotazione si **misura**
  col solver, sempre. E **il centro dell'header sbaglia** di 4' in mediana, fino a 26': anche il
  centro si misura.
- **La rete di casa e' fidata, nessun login in v1.** Sul NAS l'app ascolta solo in rete locale, mai su
  Internet, e la guida lo dice chiaro. Un login vero, se servira', arriva dopo senza rifare nulla.
- **Sul desktop il backend ascolta solo su `127.0.0.1`, con un token per avvio** che la finestra
  dell'app conosce e le altre applicazioni della macchina no.
- **L'app si apre e basta** (Marco, 13/9/2026): e' il **backend a servire la pagina**, e le consegna
  la chiave di avvio mentre gliela manda -- la chiave non finisce in un link, in una cronologia o in un
  messaggio. In sviluppo la pagina la serve Vite: la chiave la decide `tools/dev.py` e la passa ai due
  processi con `ASTROLOG_TOKEN`. La chiave resta obbligatoria su ogni rotta (`X-AstroLog-Token`).
- **Prima scansione: tutto subito, il cielo arriva dopo -- un frame per sessione prima.** I frame
  compaiono appena letti (notti, oggetti dal nome, corredi); il solver lavora in sottofondo e risolve
  prima un frame per sessione, poi tutti gli altri dai piu' recenti. Dove non e' ancora arrivato la
  pagina lo dice.
- **Il database stellare si scarica al primo avvio**, da solo, con checksum, nella cartella dati:
  nessun installer da un GB, nessun aggiornamento che lo riscarica, e l'utente non sceglie niente. E' l'unico scaricamento che l'app fa senza
  una richiesta esplicita, ed e' dichiarato a schermo.
- **Su Windows e Mac l'app e' un'app vera**: Tauri 2, backend Python come sidecar, firma e updater. Il
  prototipo decide fra Tauri ed Electron sulla notarizzazione. Cio' che la ricognizione del 4/9/2026 ha
  fissato: il bundler di Tauri 2 **firma da solo i sidecar**; l'issue aperta e' la #11992 ("signature
  of the binary is invalid" con `externalBin`), si diagnostica con `xcrun notarytool log`; il sidecar
  PyInstaller va **onedir, mai onefile**; gli entitlements stanno in un `entitlements.plist` a parte e
  valgono anche per il sidecar (`allow-jit`, `allow-unsigned-executable-memory`,
  `disable-library-validation`). **Serve l'Apple Developer Program (99 USD/anno)**: senza, da macOS
  Sequoia l'utente passa da Impostazioni > Privacy > "Apri comunque"; l'alternativa senza account e'
  Homebrew cask. **Windows**: senza firma SmartScreen blocca, EV non lo salta piu' dal 2024, Azure
  Artifact Signing accetta individui solo in USA e Canada; per un progetto open source **SignPath
  Foundation firma gratis** (licenza OSI, build riproducibile dalla CI) -- e' la strada.
- **ASTAP su ARM64**: la build ufficiale aarch64 esiste (deb, tar, CLI); i tempi pubblici sono di
  Raspberry Pi 4 (2-15 s a frame); nessuna misura su un NAS. D50 = 867 MB, D05 = 101 MB, G05 = 102 MB,
  da SourceForge `star_databases/`.
- **Le metriche dei frame con `sep` + numpy/scipy**, non `photutils`, che non ha la ruota per Linux
  arm64. Si riapre quando photutils la pubblica, se la misura dice che vale.
- **Le dichiarazioni dell'utente sopravvivono a tutto.** Cio' che l'utente ha *detto* -- nomi,
  correzioni, piani, siti -- e' distinto nello schema da cio' che l'app *deriva* dai FITS, si esporta in
  un file leggibile e rientra su un DB nuovo. Il derivato si ricalcola; il dichiarato non si perde mai.
- **Una pagina Diagnostica, con un bottone "copia"**: versione, sistema, percorsi, cosa il solver non
  ha risolto e perche', gli ultimi errori del log, senza dati personali. **Nessuna telemetria, per
  costruzione**: le segnalazioni le fa l'utente, a mano, con la diagnostica.
- **Tutto automatico, manuale per eccezione.** L'app deduce e propone; l'unico gesto manuale
  necessario e' **dare un nome all'oggetto che non riconosce**. Impostazioni minime. Nessun
  "accetta/scarta" dei frame in v1. **v1 = app completa**: si rilascia una cosa finita.
- **Si chiede per gruppo, mai per file, e solo cio' che cambia qualcosa, dicendo cosa si
  guadagna**: e' la regola di *Da confermare*. Dentro l'ordine fisso delle sezioni, prima cio' che
  tocca piu' frame (`backend/astrolog/api/review.py`, `review_page.py`). Una risposta e' una dichiarazione nell'archivio dell'app, **mai nel FITS**: vince sul
  dedotto, sopravvive ai reset, si esporta. Si chiede all'utente solo cio' che ne' l'header, ne' la
  misura, ne' l'arricchimento online sanno dare.
- **Niente badge di provenienza** a schermo: il dato si mostra e basta.
- **Stesso soggetto, anni o corredi diversi = un oggetto e N progetti.** Il mosaico ha **parita'
  piena di funzioni** con l'oggetto. La pagina delle sessioni si chiama *Notti*.
- **Anteprime**: la card mostra la foto finale dell'utente, e in mancanza il suo frame migliore. Mai
  immagini di terzi.
- **Qualita' e meteo non si correlano**: sono misure di cose diverse.
- **Controlli**: un elenco a comparsa quando le voci vengono dall'archivio; un segmentato solo per voci
  poche e fisse.
- **Il glossario e' una casa** ([`domini/glossario.md`](domini/glossario.md)), e l'ha scelto Marco
  parola per parola (5/9/2026).
  Il 15/9/2026 Marco l'ha riconfermato contro lo schermo, che diceva "pose" e "luogo": vale il
  glossario, a schermo e nei documenti. Un nome nuovo che non sta li' e' un rosso.
- **L'API e' versionata** (`/api/v1`): un cambiamento che rompe un client e' un `v2`. Ogni rotta che
  restituisce un elenco che cresce con l'archivio **pagina**: un archivio puo' avere cinquantamila
  frame in una cartella. Non paginano, e lo dicono nelle loro docstring, gli elenchi che non
  crescono con l'archivio: l'attrezzatura (`/gear`, sta in una schermata), il vocabolario dei filtri
  (`/vocab/filter-models`, viene col programma), le sottocartelle di una sola cartella
  (`/folders/browse`) e i luoghi di una ricerca (`/places`, col tetto di `place.search`). E
  Da confermare (`/review`), che manda cio' che e' da guardare: cresce con cio' che e' nuovo, non
  con l'archivio, perche' gli oggetti gia' visti stanno fuori e si leggono a pagine
  (`/review/objects/settled`, Marco, 27/9/2026).
- **Le decisioni di prodotto del vecchio sono state rilette tutte** (206, il 5/9/2026) e stanno in
  [`domini/ereditato.md`](domini/ereditato.md). **I bivi chiusi da Marco il 5/9/2026**: vince sempre il
  dichiarato e l'header si conserva; `FILTER = none` -> `BAYERPAT` decide, altrimenti *Da confermare*;
  nessun voto ai frame; il seeing non cambia la parola del verdetto; altezza minima / distanza dalla
  Luna / ore minime = **valori di fabbrica in Impostazioni** con la fonte accanto; la scansione
  sempre col pulsante e nessuna sorveglianza continua (che non parta da sola all'apertura l'ha deciso
  il `/progetto scanner` lo stesso giorno: vale il contratto), con **una sola eccezione**: sul NAS
  chi lancia l'app puo' chiedere una scansione a intervalli (`ASTROLOG_SCAN_EVERY_MIN`,
  `docs/domini/spina.md`), e senza quella richiesta non parte niente; export = **un file del dichiarato**, reimportabile; il progetto e' di soggetto
  e corredo, **non del sito**; il catalogo si aggiorna **con la versione dell'app**; orizzonte = una
  lista di punti (azimut, altezza), da `.hrz` o disegnato o libero; fondere tiene l'obiettivo piu'
  alto, eliminare toglie l'intenzione, "sospeso" e' "fermo" e non e' una colonna.
- **Dal `/progetto scanner` (5/9/2026)**: primo avvio a tre passi (nome, sito, cartelle), piu' un
  quarto solo per chi non ha il riconoscitore del cielo (16/9/2026, `docs/domini/sito.md`), saltabile
  e riapribile, poi la prima scansione parte da sola; l'attrezzatura non si dichiara al buio nel primo
  avvio ma in Da confermare (7/9/2026); **i file di calibrazione si saltano in toto**, e la ricevuta li
  conta per motivo (11/9/2026); **prima i dati per catalogare, le misure dopo**; la pagina della
  scansione come nel vecchio (un pulsante a tre verbi, catena di fasi coi numeri veri, ricevuta);
  worker = **un thread**; un file **senza `IMAGETYP` entra** come `unknown` e va in Da confermare
  (ASI Studio e SharpCap non lo scrivono <!-- software-ok: sono la ragione del ramo -->)
  -- oggi la domanda non c'e', ed e' fra le cose da riparare; DB via `platformdirs`.
- **Il software di ripresa supportato e' N.I.N.A., ASIAIR, Voyager e SGP** (Marco, 6/9/2026): il
  corpus di header e le regole di lettura si provano su questi quattro; gli altri non entrano nel corpus:
  (TheSkyX, MaxIm, ASI Studio, SharpCap, APT, Ekos, Seestar...) <!-- software-ok: questa e' la decisione -->
  Un header di un software
  qualunque entra comunque: quello che non si sa va in Da confermare.
- **I vocabolari rivisti voce per voce con Marco** (6/9/2026): nei filtri restano solo le grafie che i
  quattro software scrivono; il **catalogo dei modelli resta** come tendina, ma **si puo' scrivere
  qualunque nome con la sua banda**; le bande sono 16 piu' UNKNOWN (senza IR, UV, NB, NII; con Hβ); il
  software riconosciuto e' **solo** i quattro, e la copia calibrata si riconosce dal **marchio** che il
  file porta, non dal nome del programma; le **sigle degli oggetti le sa il catalogo**, non una lista a
  mano; le **chiavi dell'header** sono lo standard FITS piu' cio' che i quattro scrivono, salvo le due
  che dicono che il file e' stato riscritto (`CALSTAT`, `CALIBRAT`), da una convenzione pubblica; le
  misure scritte nell'header (FWHM, SNR, stelle) **non si leggono: si misurano**.
- **La pagina *Da confermare* e' il cuore delle dichiarazioni** (Marco, 7/9/2026): non elenca solo
  cio' che l'app non sa, ma **tutto cio' che la scansione ha trovato** -- attrezzatura con la sua
  scheda, oggetti coi dubbi in cima -- e le domande sui gruppi di frame. Si risponde e **"Applica"
  scrive tutto in un colpo**: le risposte diventano dichiarazioni e **regole riusabili**. Confermare e'
  una dichiarazione; la pagina non blocca mai, i frame sono gia' in archivio.
- **I campi di una scheda si chiedono solo se l'app ci fa qualcosa** (7/9/2026). Ottica: apertura e
  focale nativa. Camera: mono/colori e pixel. Filtro: marca, modello, banda e larghezza in nanometri
  per ogni banda, facoltativa. Riduttore: il fattore. Montatura: quanto regge. Ruota: quanti filtri. Su
  ogni pezzo peso e nota. **Non si chiedono mai** rapporto focale, lato del sensore in mm e scala in
  arcosecondi per pixel: si derivano.
- **Copie calibrate dei light**: stessa `DATE-OBS` + stessa camera + stessa esposizione = gemelli; e'
  copia chi ha un gemello piu' originale (prima il marchio `calibrated`/`rewritten`, poi il software
  fra i quattro; a pari indizi contano tutti e due), e il grezzo vince. Sull'archivio di Marco (7/9/2026)
  zero coppie: i 391 frame riscritti stanno dove il grezzo non c'e' piu', e contano come ore vere.

## Parcheggio

- **Dopo il rilascio, cio' che si ricava dal vocabolario va riscritto quando il vocabolario
  cambia.** Oggi il database si ricrea da zero (`CLAUDE.md`, terzo principio), e un vocabolario nuovo non lascia niente
  di vecchio. Dopo il rilascio restera' scritto col vocabolario di prima: i tre giudizi sul grezzo
  (`spine/header_asks.py`), il software normalizzato, e ogni valore che `normalize` ricava da un
  nome. Serve un modo per rifarli -- rimettere in coda la normalizzazione e riscrivere i giudizi --
  prima che una versione nuova cambi il vocabolario. Senza, la pagina leggerebbe il giudizio vecchio
  mentre chi rimette in coda dopo una risposta rigiudica col nuovo (`rigless.frames_of`,
  `rig_optics.requeue`): oggi coincidono, e `tests/test_header_asks.py` lo prova.
- **Il singolare lo sceglie `t()` solo per il conto che si chiama `n`**: dove il numero sta in un
  altro segnaposto con 1 si legge ancora storto -- le notti in tutto (`{notti}`, `nights.totals`) e
  le ore della finestra (`{su}`, `weather.window.*`) in tutte e due le lingue, e in inglese anche i
  frame rimessi in coda (`{pose}`, `review.applied`, `review.lookalikes.looksLike`). Si chiude chiamando `n` il conto di quelle
  chiavi, o spezzandole in due frasi.
- **Un filtro scritto a mano ha una banda sola, e fra quelle che si scelgono non ci sono le bande
  delle camere a colori** (anti-inquinamento, UV/IR-cut): chi riprende a colori non puo' ancora
  scriverne uno cosi' dall'Attrezzatura. Da Da confermare invece si': dal catalogo dei modelli.
  Si chiude portando la ricerca nel catalogo anche nel filtro scritto a mano.
- **Un corredo scritto a mano con la focale sbagliata non si corregge e non si cancella**: la sua
  impronta e' la sua identita', e un'unione lo fa anche risorgere dalla dichiarazione
  (`restore_declared` in `backend/astrolog/spine/rigs.py`). Oggi resta con zero ore accanto a
  quello giusto che la scansione fa nascere. Si chiude con il gesto che toglie un corredo tuo senza
  pose, che cancella riga e dichiarazione insieme.
- **Stanotte senza previsione si rilegge ogni 5 minuti finche' la previsione non c'e'**
  (`rileggiOgni` in `frontend/src/Stanotte.tsx`): senza rete per giorni, o col modello scelto che il
  servizio non manda, resta cosi' a finestra aperta, e ogni lettura di `GET /tonight` campiona una
  notte di cielo. Si chiude con la scadenza vera (la voce *Il piede richiede il cielo a
  tempo, non a scadenza*) o con un segnale di quando la previsione e' stata tentata.

- **Riportare la riga "nessun filtro" a filtro vero non riconta l'uso** (`is_none` da 1 a 0 in
  `gear.declare_filter`, `backend/astrolog/spine/gear.py`): nessuno stadio riparte, e l'Attrezzatura
  dice "si sta contando" per quel filtro fino alla corsa dopo. Oggi ci arriva solo chi chiama l'API
  a mano (la pagina non manda `is_none`); si chiude facendo ripartire le sue pose o riscrivendo l'uso.

- **Le camere i cui file non dicono il binning restano senza pixel, dai file e dal cielo.** Il pixel
  fisico e quello ricavato vogliono tutti e due il binning (`units.physical_pixel_um`,
  `units.pixel_um_from_scale`), e "un binning ignoto non vale 1". Nell'archivio sintetico sono i
  profili di Voyager e SGP (`backend/tests/synthetic.py`), che pero' non sono verificati su header
  veri -- e per SGP il lettore si aspetta gia' `CCDXBIN` (`backend/astrolog/fits/header_keys.py`).
  Da guardare quando arrivano gli header veri, con la voce "Mancano Voyager e SGP": se quei programmi
  davvero non lo scrivono, si decide con Marco cosa fare.

- **Il pixel ricavato dal cielo potrebbe dare al solver il campo delle pose che non dicono il
  pixel** (`instruments.pixel_from_sky_um`): oggi il solver prende il campo solo da `XPIXSZ`
  (`spine/solve.py`, `_scale_of`), e senza cerca alla cieca. Da misurare su pose vere prima di
  farlo: il campo e' la leva della velocita', ma un pixel sbagliato lo manda fuori strada.

- **Un errore alla primissima risposta dell'Archivio lascia un filtro acceso senza il modo di
  toglierlo.** La barra compare dalla prima risposta buona in poi, perche' le sue tendine offrono
  cio' che l'archivio ha e prima di quella risposta non si sa. Chi apre un collegamento gia'
  filtrato (`?q=zzz`) mentre il backend si sta riavviando vede titolo e avviso, e per uscirne ha
  solo il tasto indietro. Dal secondo giro in poi le ultime scelte viste restano in mano e il caso
  non si presenta. Il rimedio -- una barra col campo e senza tendine finche' non si sa cosa
  offrono -- e' una decisione di prodotto, non una riparazione.

- **Il metodo dice "inglese nei nomi", e per i nomi che vivono dentro una funzione il codice non
  lo fa.** Contate il 22/9/2026 le coppie (file, nome) distinte fra argomenti di funzione e nomi
  assegnati in `backend/astrolog`, con un giro sull'albero sintattico: **78 italiane su 2.398**,
  cioe' il 3,3%, ed e' vecchia quanto il progetto (`dove`, `righe`, `soggetto`, `istante`,
  `notte`, `riga`). Cio' che **esce** da un modulo -- funzioni esposte, costanti lette da fuori,
  parole chiave di un argomento -- e' invece in inglese, e il 22/9/2026 i due casi che non lo
  erano sono stati rinominati (`rigs_joined`, `KEY_KINDS`). Le due strade sono **rinominare anche
  i 78**, in una passata sola e con una macchina che poi lo impedisca, oppure **scrivere nel
  metodo** che la regola vale per cio' che esce da un modulo e non per i nomi interni -- che e'
  quello che il codice fa gia' senza dirlo. **Decisa da Marco il 30/9/2026 (`CLAUDE.md`, "Nomi e
  commenti in inglese"): si rinominano**, package per package nella fase 2 del refactor.

- **Gli strumenti che la posa nomina costano query per posa, senza cache.**
  `spine/normalize_rig.instruments_on_frame` risolve tre generi uno per uno -- grafia imparata
  piu' ricerca del pezzo -- e non ha il raggruppamento che `rig_for_frame` ha nei suoi
  `buckets`. Su un header muto non costa niente; su ogni posa di N.I.N.A. sono fino a sei
  query in piu' (rilievo del revisore, 22/9/2026, non ancora cronometrato). Si chiude come le
  focali: si risolvono i nomi **una volta per passata**, non una per posa.

- **Cancellare un pezzo dell'attrezzatura non si puo', e la domanda non e' banale.** Un pezzo che
  tiene delle pose non si toglie senza decidere che fine fanno le sue ore: sparire con lui,
  restare orfane, o tornare in coda. Il progetto di prima rispondeva con un 409 che diceva **chi**
  lo tiene e quante pose (`old/backend/astrolog/api/instruments.py`), ed e' una risposta che
  regge. Prima serve la scelta di prodotto, non il codice.

- **`backfocus_mm` esiste e non si puo' scrivere.** Sta nello schema e in `INSTRUMENT_FIELDS`, e
  la pagina Attrezzatura lo mostra quando c'e', ma **nessuna scheda lo chiede**
  (`api/instrument_answer.CARD`) e nessuna grafia d'header lo riempie -- e da quando la guardia sui campi
  di un genere sta nel backend (`instrument_answer.of_the_kind`), mandarlo e' un 422. Quindi oggi quella
  riga non si accende in nessun modo. Da decidere a quali generi chiederlo -- non alla montatura --
  e allora si accende da sola.

- **Alle notti manca un indice, e si sente.** La query della pagina valuta i tre conteggi su
  **tutte** le notti e poi ordina in una tabella temporanea, prima del `LIMIT`: su 1.000 notti e
  40.000 pose sono **12,81 ms**, che con `CREATE INDEX nights_date ON nights(night_date DESC, id
  DESC)` diventano **1,05** -- dodici volte, e restano tali anche a pagina 10 (misura
  dell'auditor, 21/9/2026). Cresce col numero di notti dell'archivio, non con la pagina. E'
  preesistente alla Luna, ed e' il costo piu' grosso trovato in quel giro.

- **Il totale dell'archivio viaggia in ogni pagina dello scorrimento, e si guarda solo l'ultima.**
  `archive_totals` fa una scansione piena (14,6-19 ms su 40.000 pose) a ogni "mostra altre",
  mentre a schermo conta solo la pagina piu' recente. Sommato al fatto che il client rinfresca
  **tutte** le pagine caricate quando si torna sulla scheda (`main.tsx` crea il client senza
  `staleTime`), cinque pagine aperte costano cinque volte tutto. Si chiude mandando i totali solo
  alla prima pagina, o dando al client una politica.

- **`Time([...])` costruito un istante per volta.** Nelle effemeridi si compone l'elenco degli
  istanti creando un `Time` scalare per ognuno e poi rifondendoli: **2,39 ms** contro 0,16 per
  cento istanti in `moon.phases`, e **6,5 su 74,3** per una griglia da 280 punti in
  `corpi.altezze`. La guardia sul fuso si puo' tenere lo stesso. Due case, e si tocca in una sola
  volta (misura dell'auditor, 21/9/2026).

- **Il totale in cima alle Notti costa 2,5 volte la forma che sostituisce.** I tre numeri
  dell'archivio intero passano dalla casa comune (`spine/counts.py`), che sono **tre sotto-select**
  dove una passata sola con `COUNT(*) FILTER` bastava: misurato su 200.000 frame in una notte,
  18,2 ms contro 45,4 (misura dell'auditor, 20/9/2026). Sono +27 ms a ogni apertura della pagina,
  e si pagano per non avere due modi di contare le stesse ore -- ma il giorno che un archivio vero
  lo mostri lento, la strada e' dare a `counts` anche la forma aggregata, non ricopiarla.

- **Quattro righe di guscio finto in ogni prova di pagina.** `"/api/v1/settings"`,
  `"/api/v1/review"`, `"/api/health"` e `SPINA` si ripetono **31 volte** in `frontend/tests`
  (misura del 20/9/2026): `banco.tsx` espone i pezzi ma non la combinazione, e ogni pagina nuova
  ne aggiunge due. Si chiude con un `GUSCIO` nel banco.

- **Le parole vietate del glossario non hanno una macchina, e si rompono.** La pagina Notti e'
  nata scrivendo *pose* dove il glossario dice **frame** (che elenca "posa" fra le parole da non
  usare): quattro testi a schermo, e nessuna guardia se n'e' accorta -- l'ha vista il
  `traduttore`, portando la pagina in inglese, dove le due parole diventano la stessa. Una
  macchina non e' banale: la colonna delle vietate non dice **per quale voce** una parola e'
  vietata, e "sessione" vietata per `night` e' il termine giusto per `session`. Servirebbe legare
  ogni parola vietata alla sua voce, e allora il controllo sui testi dell'app diventa un grep.

- **Sopra gli 84 gradi di latitudine la frase del buio dice "dalle 12:00 alle 12:00".** Quando il
  Sole non arriva mai alla soglia astronomica la finestra e' **tutta** buio, e il nome del grafico
  (`tonight.dark`) legge i due estremi -- che sono lo stesso mezzogiorno. E' la stessa forma del
  difetto riparato in `5012abda` sulle etichette dell'asse. **Nessun posto abitato lo vede**:
  misurato a Longyearbyen, Alert, Pituffik, Utqiagvik e Dikson il buio sta sempre **dentro** la
  finestra, e serve gia' l'85 parallelo. Si chiude con una riga -- se il buio tocca tutti e due i
  bordi, "tutta la notte" -- il giorno che qualcuno ci osservi davvero.

- **I nomi degli otto conti di una scansione stanno in tre case, due ricopiate a mano.** La casa
  e' `COUNTS` (`backend/astrolog/spine/scan.py`); `finish_run` (`backend/astrolog/spine/scan_store.py`)
  li riscrive due volte -- come colonne SQL e come chiavi del dizionario -- mentre la lista delle
  **liste** della ricevuta, due righe sopra nello stesso file, e' derivata da `RECEIPT_LISTS`.
  Sedici righe ricopiate, e nessuna guardia le lega: un nono conto aggiunto a `COUNTS` e al modello
  resterebbe **zero per sempre** con la suite verde -- `backend/tests/test_models_match_constants.py`
  verifica solo che i nomi siano campi del modello, non che `finish_run` li scriva. Il rimedio e'
  gia' scritto due righe sopra. Misurato il 20/9/2026 da un audit.

- **"Come si arriva a una sezione di Impostazioni" e' scritto nove volte nelle prove.** Il banco
  espone gia' `vaiASezione` per *Da confermare*, con la docstring che dice proprio questa regola;
  le quattro prove delle sezioni hanno ognuna il suo aiutante privato, identico salvo la regex, e
  `frontend/tests/accessibilita.test.tsx` fa gli stessi due passi cinque volte in linea. Misurato
  il 20/9/2026: nove case, ~20 righe, il clic sulla voce *Impostazioni* ripetuto dieci volte.

- **Una lettura di una cartella che non segui piu' non lo dice.** Togliere una cartella e' un
  **ritiro** (`folders.retired_at`), quindi il percorso c'e' sempre e la riga si legge -- ma a
  schermo niente distingue la lettura di una cartella viva da quella di una ritirata, e chi non
  ricorda di averla tolta legge un percorso che non viene piu' aggiornato. Costa un campo in piu'
  sulla ricevuta (`f.retired_at IS NOT NULL`) e una frase.
- **Perche' la scala di Bortle non va dal rosso al nero.** Proposta il 19/9/2026 e scartata su
  una misura, non su un'opinione: il fondo dell'app e' `#0a0b10`, e **il buio non si vede sul
  buio**. Un nero puro su quel fondo fa **1,07:1**, un bordeaux 1,96:1, un blu notte 1,13:1 --
  contro i 3:1 che WCAG 1.4.11 chiede a un segno grafico. Sarebbe sparita proprio la fascia 1,
  cioe' il cielo migliore. La rampa consegnata dice la stessa cosa in un modo che sopravvive al
  tema scuro: non chiaro/scuro ma **freddo/caldo**, dal ciano del cielo pulito al rosa delle
  luci, e sul fondo dell'app sta fra 4,3:1 e 10,9:1 nei due temi (3,81:1 il pavimento su **ogni**
  fondo, che una prova misura). Se la domanda torna, la risposta e' questa.

- **La prima lettura che non parte non lo dice a nessuno.** Alla fine del primo avvio l'app chiede
  `POST /api/v1/scan`, e se quella risponde no -- un lavoro gia' in corso, le cartelle diventate
  irraggiungibili -- l'utente esce comunque (ed e' giusto: il timbro comanda) ma **convinto che
  l'app stia leggendo**, che e' quello che gli promette la guida. La strada c'e' gia', il pulsante
  in barra, ma nessuno gliela indica. Si chiude quando la Casa avra' la sua riga di stato, o con un
  avviso alla prima apertura.
- **Sfogliare le cartelle si ferma alla radice dei dati.** Dal primo avvio si scende dentro le
  sottocartelle e si registra quella dove si e' arrivati, ma **solo dentro `data_root`**: chi ha il
  NAS montato con le foto fuori da li' non le vede, e sul desktop l'elenco non esiste proprio (la
  rotta risponde 409 `no_data_root`, per scelta: elencare le cartelle della macchina a chi lo chiede
  e' un'altra cosa). Sul desktop il percorso si scrive, ed e' un limite dichiarato, non un difetto.

- **La barra chiede l'intera pagina di Da confermare per mostrare un numero.** Il conto accanto
  alla voce viene da `GET /api/v1/review`, che costruisce **tutte** le sezioni: 2,84 ms quando
  erano undici (oggi sono dodici)
  sull'archivio sintetico, ma **3.286 ms** su uno gonfiato a 5.000 voci per famiglia (misurato il
  16/9/2026). Oggi non si paga due volte -- la Casa e la barra condividono la stessa query -- ma su
  una pagina che di Da confermare non sa niente e' una lettura intera per un numero. Si chiude con
  un conto leggero il giorno che la lentezza si vede: farlo adesso vorrebbe dire scrivere in due
  case il predicato di cosa conta come domanda aperta, che e' il difetto peggiore dei due.

### La veste, cose che restano da fare

- **Sotto i 720px la tabella non allarga le celle dei filtri e delle etichette**: il foglio le
  riconosce da `td[data-etichetta="filtri"]` e `"etichette"`, minuscolo e in italiano, mentre la
  pagina ci scrive il nome della colonna tradotto e con la maiuscola (`Filtri`, `Etichette`;
  `Filters`, `Labels` in inglese) -- che e' quello che il foglio stesso mostra davanti alla cella.
  Il selettore non aggancia mai. E' del foglio, quindi torna a Design: la cella va riconosciuta da
  qualcosa che non si traduce.
- **Il foglio nuovo e' consegnato e non portato, e chiude sette correzioni nostre.** Arrivato
  con la pagina della Luna, e rifatto dopo i nostri rilievi. Misurato contro quello che abbiamo:
  **non toglie nessuna classe** (461 contro 404), e le tre guardie che giudicano il **contenuto**
  passano, contrasto **misurato** compreso (`sotto_soglia`, `soglia_della_riga`,
  `pavimenti_del_cielo`); `fogli_cambiati` va rossa, ed e' il suo mestiere. L'elenco delle guardie
  lo tiene `controlli_veste.tutti()`, non questa riga.
  Cosa cambia di cio' che c'era: i due token `--grafico-soglia` e `--grafico-adesso` cambiano
  colore; le cinque fasce del crepuscolo cambiano valore nei due temi (nello scuro la notte piena
  non e' piu' dipinta, nel chiaro resta un velo); `.as-grafico__luna` e `.as-grafico__soglia`
  **perdono il tratteggio**; `.as-lato__coda` prende la sua colonna dal foglio invece che da uno
  stile nel montaggio, perche' sul telefono la striscia la ribalta in riga; e `.as-dialogo-fondale`
  e' una **riparazione** -- con `place-items: center` la colonna si dimensionava sul dialogo invece
  che sulla finestra, quindi `max-width: 100%` non tagliava mai e a 360px il pannello sbordava. E'
  un difetto che abbiamo **gia' oggi**, e non si vede solo perche' nessuna pagina apre ancora un
  dialogo.
  Hanno chiuso, alla fonte: la parola *"culmina"*, il rimando a una pagina che non esiste, la
  formula del tetto rotta ai tropici, il commento della legenda che parlava di un tratteggio tolto,
  le due classi nate morte, la riga di versione che diceva v8, e la frase *"nessuna regola dell'v8
  e' cambiata"* che era falsa. Il doppione della scala di Bortle e' sciolto: **tre forme, una per
  posto**, e nel piede della barra vale `.as-bortle-scala` -- che adesso ha anche il caso "classe
  non dichiarata" che le mancava.
  **Resta una divergenza, piccola e sul confine**: il loro commento calcola il tetto con 28,6 gradi
  di declinazione massima, che e' la somma delle due inclinazioni **medie**; la Luna al lunistizio
  maggiore arriva a 28,72, e `backend/astrolog/ephemeris/__init__.py` usa 28,8 perche' quel numero deve
  essere un limite superiore o il tetto taglia la curva. Il conto lo fa il backend e glielo
  mandiamo gia' fatto, quindi il loro resta documentazione -- ma e' una seconda casa dello stesso
  fatto, e quando il foglio entra va detto alla fonte o tenuto fermo da una guardia, come i
  pavimenti di Bortle.
  Piccolezze loro, da segnalare col prossimo giro: l'intestazione del blocco di Bortle nomina
  ancora due forme nel titolo e dice *"tre regole, e valgono per tutte e due"* mentre le forme sono
  tre.

- **Quattro doppioni piccoli dell'Archivio, trovati dall'audit del 22/9/2026 e lasciati li'.**
  Nessuno cambia un numero; tutti costano una riscrittura in piu' il giorno che qualcosa cambia.
  (a) **Due chiavi i18n per la stessa parola**: `archive.measure.frames`/`.time` (la carta) e
  `archive.column.frames`/`.time` (la tabella) dicono "frame" e "tempo" a meno della maiuscola, che
  il foglio non impone -- otto stringhe per due fatti, e la guardia delle traduzioni prova la
  parita' fra lingue, non fra due chiavi della stessa lingua. (b) **Quattro mappe parallele per due
  viste** in `frontend/src/Archivio.tsx` (`VISTE`, `SCHEDA`, `PANNELLO`, piu' il ternario dei
  testi): una vista in piu' sono quattro posti, e il ternario sbaglierebbe **in silenzio**. La casa
  unica e' una mappa sola di oggetti. (c) `type Riga = components["schemas"]["ArchiveObject"]`
  scritto in tre file: basta esportarlo da `RigaDellArchivio`. (d) Lo **scheletro di pagina**
  (titolo, "sto caricando", l'avviso d'errore) e' identico in `Archivio`, `Notti` e `Attrezzatura`:
  66 token, cioe' sotto la soglia di `jscpd` (60 token ma con `threshold` 0.001, e a
  30 ne uscirebbero 24). Vuole un mattone della superficie, non una soglia piu' bassa.

- **Tre elenchi ordinano nomi scritti dall'utente sui byte, e sembrano rotti a chi li scrive.**
  SQLite ordina `TEXT` confrontando i byte: `vdB` finisce **dopo** `WR`, e ogni nome battuto in
  minuscolo dopo tutti quelli in maiuscolo. L'Archivio lo ha chiuso il 22/9/2026 mettendo
  `COLLATE NOCASE` su ognuno dei suoi ordinamenti che legge un nome; restano fuori
  `backend/astrolog/spine/inventory.py` (i **pezzi**, `ORDER BY i.kind, i.name`, e i **filtri**,
  `ORDER BY ... x.name`) e `backend/astrolog/api/sites.py` (i **siti**, `ORDER BY s.is_default
  DESC, s.name`). Sono tutti e tre nomi che l'utente batte o che vengono dall'header, cioe' il
  caso in cui capita di sicuro. Si chiude con `COLLATE NOCASE` accanto a ognuno e una prova che
  mescoli le casse; e la regola, che oggi vive accanto agli ordinamenti di `spine/archive.py`
  come se fosse dell'Archivio, va detta dove vale -- e' del repo.

- **La tendina di scelta e' scritta a mano in cinque posti**, oltre a `frontend/src/TendinaDiScelta.tsx`
  che ne raccoglie una parte (le voci che vengono dall'archivio). `Campo` piu'
  `<select class="as-scelta">`, di solito con una prima voce vuota (`frontend/src/GestiDelPezzo.tsx`
  non ce l'ha: scegliere il genere di un pezzo e' obbligatorio -- quindi nel mattone la voce vuota
  sara' **opzionale**): `frontend/src/GestiDelPezzo.tsx`, `frontend/src/SchedaDelPezzo.tsx`,
  `frontend/src/SezioneFiltri.tsx`, `frontend/src/SezioneSenzaCamera.tsx` e
  `frontend/src/BarraDellArchivio.tsx`, che una `Tendina` ce l'ha ma **privata**. E' la storia di
  `as-riga__conteggio` e di `as-bottone`: un mattone `Tendina` (etichetta, voce vuota, voci, stato
  d'attesa) e la sua riga in `controlli_veste.MATTONI`, e le case diventano una. Da fare quando si
  tocca una di quelle pagine per altro, non di slancio.

- **Il segmentato e' scritto in due posti, con due ARIA diverse.** `as-segmentato` piu'
  `as-segmentato__voce` vivono in `frontend/src/Archivio.tsx` (l'interruttore fra carte ed elenco,
  `tablist`/`tab`) e in `frontend/src/BarraDellArchivio.tsx` (i tre ordini, `group`/`button`
  con `aria-pressed`). Due ARIA diverse sono giuste -- una sceglie quale pannello vedi, l'altra
  riordina lo stesso elenco -- quindi un mattone solo dovrebbe prendere quale ruolo vestire, ed e'
  un mattone con un interruttore dentro. Alla terza occorrenza si decide; due non bastano.

- **La terza forma del dato esce in due modi, e alla terza occorrenza vuole un mattone.**
  `as-dato--ignoto` e' scritta a mano in tre file (`frontend/src/ElencoDellArchivio.tsx`,
  `frontend/src/ScalaDelCielo.tsx`, `frontend/src/ImpostazioniLetture.tsx`) e **solo l'ultima
  arrivata porta `as-dato__segno`**, cioe' il tratteggio che il foglio le da'. Quindi la stessa
  cosa -- "non si sa" -- oggi si legge in due forme diverse nella stessa app. E' la storia di
  `as-riga__conteggio` e di `as-bottone`: un mattone `DatoIgnoto` (segno, parola, e il perche'
  accanto quando c'e') e la sua riga in `controlli_veste.MATTONI`, e le tre case diventano una.

- **La modalita' "schermo" e' disegnata e non montata, e non si puo' montare da una pagina sola.**
  Il foglio la prevede per le **pagine a risultati**: alte quanto la finestra, con la tabella che
  scorre dentro e la barra delle pagine sempre raggiungibile. Il foglio la fa con tre pezzi che
  vanno insieme: `.as-guscio--schermo` sul guscio, `.as-pagina--schermo` sulla pagina e un
  `[role="tabpanel"]` in mezzo -- e lo dichiara in chiaro (`frontend/src/stili/astrolog.css`, nel
  blocco `AREA DI UNA VISTA -- .as-vista-guscio`). Il primo sta nel **Layout**, che sa gia' su che pagina e'
  (`paginaDi`) e potrebbe metterlo solo dove serve: il rinvio non e' per quello. E' che
  `.as-guscio--schermo .as-principale` prende `overflow: auto`, cioe' **cambia come scorre**
  l'app, e una cosa del guscio si collauda su tutte le superfici, non su una. L'Archivio oggi e' montato **senza**: la
  pagina scorre intera, come le altre, invece di far scorrere la sola tabella. Mezzo meccanismo e'
  peggio di nessuno, quindi non si e' preso il solo `.as-pagina--schermo`. Si chiude con una fetta
  del Layout, e allora tornano anche `.as-vista-guscio` sulle due viste.

- **Due indicazioni di posto da rileggere quando arriva il mobile.** Lo stato vuoto delle letture
  dice *"Indica almeno una cartella qui accanto, poi premi Scansiona in alto"*
  (`frontend/src/i18n/it-letture.ts`): sul telefono l'elenco delle sezioni non sta **accanto**, e
  la frase va rifatta insieme alla veste stretta.

- **Sul telefono resta da decidere cosa apre il pulsante "Sezioni", ed e' una decisione nostra.**
  `docs/domini/navigazione.md` dice che *"su telefono la barra si ritira dietro un pulsante, e le
  voci restano tutte"*. Il foglio fa un'altra cosa: sotto `--soglia-guscio` (900px) `.as-lato`
  diventa una striscia orizzontale che scorre, con tutte le voci in fila. Per la **Luna** la
  questione e' chiusa, e bene: il blocco STANOTTE si **collassa alla sua forma minima** -- disco,
  parola, percentuale -- un bersaglio solo alto quanto le voci accanto, che apre lo stesso pannello,
  e il pannello si stringe fino a 360px. Niente classe nuova nel markup.
  Ma `.as-alto__menu` ("Sezioni") compare in quel blocco e **il foglio non dice cosa apre**: con le
  voci gia' tutte visibili nella striscia, quel pulsante non ha un lavoro. O la striscia nasconde
  le voci dietro di lui -- ed e' il contratto -- o il pulsante sparisce e il contratto va corretto.
  E' un bivio di prodotto, e vale la pena portarlo a Marco quando nasce la fetta del mobile, non
  prima: oggi non c'e' niente da collaudare.

- **I nostri confini della scala di Bortle e la fonte che citiamo si sono scostati su due classi.**
  Misurato dall'audit del 19/9/2026 scaricando la fonte (`en.wikipedia.org`, voce *Bortle scale*):
  sette pavimenti su nove coincidono con `backend/astrolog/units.py`, la **4** no (nostro 20,40
  contro 20,80) e la **5** nemmeno (19,10 contro 19,25). La ragione e' che la fonte oggi ha una
  classe **4,5** che non esiste nella nostra tabella, e i nostri numeri vengono da tre fonti, non
  da una. Effetto vero e misurabile: un cielo a 20,5 si legge da noi come la 4 ("la Via Lattea e'
  ancora bella"), e sulla fonte come la 4,5 ("la Via Lattea si vede appena a 10-15 gradi
  sull'orizzonte") -- cioe' il testo che mostriamo e' piu' generoso del numero. Si chiude
  scegliendo: o si allineano i due pavimenti alla fonte citata, o `units.py` dichiara **quale**
  delle tre fonti vince quando si scostano. Non e' un rosso: e' una decisione rimandata, e finche'
  dura la nostra tabella e' l'autorita'.

- **Il nostro elenco dei pavimenti di Bortle vive anche in un commento del foglio consegnato.**
  Il fornitore ce l'ha scritto dentro (v8, commento di `.as-bortle`) perche' gli serve a disegnare
  mockup con la coppia classe/misura giusta -- e gliel'avevamo mandato noi. Il foglio si porta
  **alla lettera** e non lo possiamo correggere: il giorno che quei numeri cambiano, quel commento
  dice il falso. Da questa fetta se ne accorge una macchina -- `pavimenti_del_cielo` in
  `tools/controlli_foglio.py` -- e la correzione va chiesta alla fonte insieme alla consegna dopo.

- **Nel piede della barra il nome del sito non e' cliccabile**, mentre
  [`domini/navigazione.md`](domini/navigazione.md) dice *"Il sito diventa cliccabile quando c'e' la
  sua scheda"* -- e la scheda adesso c'e'. La strada non manca: senza sito il piede porta gia' il
  tasto *Scegli il sito*, e con un sito si passa dalle Impostazioni. Manca la **veste**: il foglio
  non da' nessun mattone per un collegamento dentro `.as-bortle-scala__dice`, e inventarlo qui
  vorrebbe dire mettere una veste nostra accanto alla loro. Va chiesto alla fonte col prossimo
  giro, insieme alle altre due correzioni in sospeso.

- **Un percorso dichiarato si controlla che sia *un file*, non che sia ASTAP.**
  `astap.where_exe` accetta qualunque file esistente (`Path(scritto).is_file()`), quindi chi sbaglia
  percorso e indovina un file qualunque si sente dire "trovato" e poi "gli manca il catalogo
  stellare" -- due frasi che accusano la cosa sbagliata. Si chiude solo lanciandolo (`astap -h`),
  che e' un effetto fuori dal processo e non sta dentro una lettura: la strada vera e' dirlo
  **quando la corsa fallisce**, dove ASTAP ha gia' parlato.

- **Cercare il catalogo costa una lettura di cartella a ogni domanda.** `GET /settings`,
  `PATCH /settings` e `GET /solver` elencano ora la cartella di ASTAP: misurato sull'installazione
  vera di qui, **5,2 ms per 1492 voci** a cache calda, su disco locale. Trascurabile li'; da
  guardare il giorno che qualcuno tiene ASTAP su una condivisione di rete, dove un `iterdir` costa
  tutt'altro. Si chiude tenendo la risposta per un po', non cambiando dove si guarda.

- **Tre regole del campo del percorso non hanno una guardia, e sono portate dal primo avvio.**
  In `frontend/src/riconoscitore.tsx`: le impostazioni in cache sono **quelle** che la scrittura ha
  appena restituito; una scrittura caduta torna riprovabile (`onError`); il bottone avvolto perche'
  in una colonna flex si stirerebbe. Misurate da un audit sabotandole: la suite intera resta verde
  su tutte e tre. Le prime due erano gia' senza guardia in `WizardSolver` e sono **spostate**, non
  nate qui; la terza e' veste, e nessuna macchina la prende. Si chiudono con una prova che guardi
  la cache dopo una scrittura e una che faccia cadere la scrittura e la rifaccia.

- **Una prova del primo avvio e' caduta una volta sola, e non si e' piu' ripetuta.** *"se li' non
  c'e' nessun solver, il passo lo dice"* (`frontend/tests/wizard-solver.test.tsx`) e' andata rossa
  **una volta**, in un giro dei controlli con la copertura accesa, non trovando il testo dell'errore;
  poi tre giri con copertura e due senza sono tornati verdi, e da sola nove volte su nove. Aspetta
  la scrittura con il tetto di attesa di fabbrica (un secondo), e la copertura rallenta tutto: il
  sospetto e' li'. Scritto invece che dimenticato perche' **un test che cade a caso e' peggio di
  uno che manca**: rassicura. Se ricapita, il posto da guardare e' quanto aspetta.

- **Chi nasce di casa lo decide il client contando, il server contando un'altra volta.** La
  sezione *Il sito* manda `is_default` guardando quanti siti ha in mano (`ImpostazioniSito.tsx`,
  `primo`), mentre `backend/astrolog/api/sites.py` lo decide con un `COUNT(*)` dentro la
  transazione. Da un dispositivo solo coincidono sempre; da due -- il NAS aperto sul portatile e
  sul tablet, che il metodo dichiara -- il server puo' eleggere di casa un sito che il client
  credeva in piu', e il piede della barra non se ne accorge. Si chiude leggendo `is_default`
  **dalla risposta** della POST invece di indovinarlo prima.

- **Dopo una scrittura l'app rilegge cio' che la risposta le ha gia' dato.** Le scritture che
  **modificano** un sito tornano il sito aggiornato (la cancellazione torna solo l'id), e la pagina
  lo butta per rifare `GET /api/v1/sites`: misurato su un giro completo, **4 riletture** da 2,0 ms
  l'una, cioe' quattro andate e ritorni in piu' su un elenco che era gia' in mano. Poco tempo, ma
  su un tablet sul NAS sono quattro attese. Si chiude scrivendo la risposta nella cache invece di
  invalidarla -- e sulla cancellazione togliendo la riga, che e' l'altro gesto -- e vale per le
  cartelle quanto per i siti, quindi si fa una volta per tutte e due, non qui.

- **Entrando in Impostazioni dal menu si paga la sezione sbagliata.** Si atterra su *Cartelle*,
  che chiede `GET /api/v1/folders` e `GET /api/v1/folders/path-info` e li butta appena si sceglie
  un'altra sezione: **2 chiamate sprecate a ogni visita** (misurate: 7 chiamate arrivando dal
  menu contro 5 andando all'indirizzo diretto). Si chiude quando la pagina ricordera' l'ultima
  sezione aperta, o quando `/impostazioni` avra' un indice invece di una sezione di partenza --
  che e' una domanda di prodotto, non una riparazione.

- **Un campo riempito da un numero dell'API lo scrive col punto**, mentre il segnaposto accanto e
  tutto il resto dell'app usano la virgola (`46,4843 N`): succede alle coordinate di un sito, sia
  correggendolo sia prendendole dalla ricerca (`frontend/src/sito.tsx`, `prendiDa`), e alla focale
  proposta in *Da confermare* (`frontend/src/SezioneSenzaCamera.tsx`). Non e' un difetto --
  `coordinataDa` rilegge tutte e due le grafie, e il giro completo e' stato provato dal vivo -- ma
  e' l'unica forma in cui l'app scrive un numero non all'italiana. Si chiude formattando il valore
  all'ingresso, e allora va provato che chi scrive col punto ritrovi cio' che ha scritto.

- **Le prove del frontend hanno 24 doppioni** (5,86%, 280 righe: `frontend/tests/`), e jscpd
  **non li guarda** -- jscpd gira solo su `backend/astrolog` e `frontend/src`. Il piu' grosso e' un
  blocco da 32 righe fra `confermare-cielo-tempo` e `confermare-gruppi-attrezzatura`. Non e' nato
  adesso: e' li' da prima della veste, e nessuno l'aveva misurato.

- **La pagina piena vive in un file di prova solo.** `frontend/tests/accessibilita.test.tsx` ha la
  fixture con **tutte e dodici** le sezioni riempite, ed e' l'unica: chi ha bisogno di una pagina
  vera -- la prova che ogni campo abbia il suo involucro, in `veste.test.tsx`, ne guarda due sezioni
  su sette -- o la ricopia o si accontenta. Sta nel banco (`tests/banco.tsx`), non in un file che se
  la tiene.

- **La barra a sinistra di una riga risposta significa due cose diverse nella stessa pagina.** In
  dieci sezioni segna la risposta **in mano** -- cio' che stai per mandare -- in *Quale filtro notte
  per notte* e *Frame senza nome* la risposta **gia' salvata**. La ragione e' che a quelle due la
  pagina non passa l'accumulatore: tengono i loro campi da se'. Si chiude passandoglielo, cioe'
  cambiando la firma di due sezioni. Chi guarda la pagina, intanto, vede la stessa barra dire due
  cose.

- **Il gruppo di scelte e' ancora radio dentro un `fieldset`, e a schermo si vede.** Il design lo
  disegna **segmentato** (`.as-segmentato`, bottoni con `aria-pressed`) e la regola e' gia' scritta
  nella skill `componente-che-formatta`: *elenco a comparsa se le voci vengono dall'archivio,
  segmentato solo per voci poche e fisse*. Le nostre sono poche e fisse (due o tre: foto del cielo
  / calibrazione, ora locale / UTC, si' / no), quindi la forma giusta e' quella. Non e' veste ma
  **cambio di controllo**: `frontend/src/Scelte.tsx` passa da `input[type=radio]` a bottoni, e una
  ventina di asserzioni che cercano `getAllByRole("radio")` o `getByLabelText` vanno riscritte --
  piu' la domanda vera, se per una scelta singola sia meglio un gruppo di radio (che i lettori di
  schermo annunciano come "1 di 3") o dei bottoni premuti. Fetta sua, piccola e mirata.

- **Il backend non comprime niente, e adesso si sente.** `StaticFiles` e' montato nudo
  (`backend/astrolog/api/page.py`) e nessun middleware comprime: il foglio viaggia per **57,9 kB
  veri** invece dei 10,4 che farebbe in gzip. Misurato il 18/9/2026 in Chrome a 50 kB/s con 400 ms
  di latenza: **+1,15 s sul primo carico** (8,11 -> 9,26 s), e dal secondo e' gratis (etag e nome
  con impronta). Il primo disegno invece **migliora**, perche' il fondo arriva prima del bundle
  (8,10 -> 3,11 s). Si chiude con una riga di `GZipMiddleware`, e vale per tutte le risposte, non
  solo per il CSS.
- **Di quel foglio oggi si usa il 14%**: 8.236 byte su 57.829, misurati con la copertura CSS di
  Chrome su Casa, Archivio e Da confermare. Il resto sono mattoni per pagine che non esistono
  ancora (tabelle, form, dialoghi). Non e' uno spreco da correggere: e' la consegna portata
  intera, e il numero sale a ogni pagina nuova. Si guarda se un giorno il peso pesa davvero.

- **Sei comportamenti che il CSS non fa, e che scriviamo noi** (li dichiara la consegna stessa, e
  nessuno serve alle pagine di oggi): **Esc** che chiude suggerimento e dialogo; le **frecce** che
  muovono la scelta dentro la ricerca (con `aria-activedescendant`) e fra le schede (col `tabindex`
  che segue quella attiva); il **fuoco** che resta dentro il dialogo finche' e' aperto e torna al
  bottone che l'ha aperto; `aria-expanded` che si **ribalta** sul pannello del perche' e sulla
  scheda di dettaglio, e `aria-selected` fra le schede; l'apertura del suggerimento **col dito**
  (su Safari per iOS e iPadOS toccare un `button` non gli da' il fuoco, quindi `:focus-within` non
  scatta: il codice aggiunge `.as-suggerimento--aperto`, che il foglio gia' conosce); l'avviso
  breve che **sparisce da solo**, ma non quello d'allarme; il `viewBox` dei grafici **calcolato
  dalla larghezza della colonna**, perche' la scala del disegno resti 1. Ognuno nasce con il
  mattone che lo chiede.
- **`--inchiostro-spento` non arriva alla soglia dove porta testo vivo.** Nasce per il disabilitato
  -- che WCAG 1.4.3 esenta -- ma nel foglio veste anche il conteggio di un gruppo in tabella
  (`.as-tabella__gruppo-conta`) e il suggerimento dentro un campo (`::placeholder`), che testo vivo
  lo sono: misurati **2,75:1** su `--fondo-carta` nel tema scuro e **2,47:1** su `--fondo-incavo`
  nel chiaro, contro 4,5:1. Oggi non si vede perche' l'app non ha ne' tabelle ne' campi vestiti:
  quando arrivano, la coppia entra in `tools/controlli_veste.py` e **il colore si corregge alla
  fonte**, perche' il foglio si porta alla lettera.
- **La barra ha perso l'annuncio "elenco di N voci"**: per stare nella forma dei mattoni le voci
  sono link dentro `.as-gruppo` e non `<ul>`/`<li>` (`frontend/src/Layout.tsx`). Il legame fra il
  nome del gruppo e le sue voci c'e' ancora (`role="group"`), la posizione nell'elenco no. Se pesa,
  si chiede alla fonte una classe che tolga i pallini senza separare le voci.

### Da confermare, cose piccole

- **Il fuso di un sito in mare aperto non resta vuoto.** `docs/domini/sito.md` dice che dove le
  coordinate non cadono in nessun fuso il campo resta vuoto col suo motivo (`site_no_timezone`), ma
  la libreria dei fusi da' un fuso `Etc/GMT...` anche all'oceano (`place.timezone_of(0, -140)` torna
  `Etc/GMT+9`), e quel nome passa la validazione. Da decidere se un fuso `Etc/` vale come fuso del
  posto, o come nessun fuso: la casa comune e' `place.timezone_of`, da cui passano sia il fuso di un
  sito sia quello di un frame (`place.timezone_of_frame`). La stessa affermazione sta
  anche nella guida, sulla pagina del meteo ("coordinate in mare aperto").
- **Due oggetti senza nome nella stessa notte possono prendere la stessa risposta** (limite
  dichiarato, Marco, 27/9/2026). Senza `RA`/`DEC`, focale o pixel il campo non si sa e i frame
  fanno un gruppo solo per notte, camera e telescopio; e due oggetti a meno di un campo l'uno
  dall'altro (M 81 e M 82 con un campo di un grado) cadono nello stesso gruppo. Una soglia di
  pausa non ha una fonte, e la cartella e' esclusa: la domanda dice dalla prima all'ultima posa,
  e chi risponde vede se sono due. Vicino c'e' il caso opposto: un mosaico a pannelli senza nome,
  coi frame che arrivano in ordine sparso, puo' dividere un pannello fra due gruppi.

- **Frame senza ottica: due ottiche alla stessa focale con la stessa camera sono una domanda
  sola.** La risposta sta sulla camera a quella focale (`spine/rig_optics.py`), e i file non dicono
  altro che le distingua. Si chiude con un'altra chiave che il file porta, se un header vero ne
  mostrera' una.
- **Frame senza ottica: la pagina riabbina le risposte ai corredi con la tolleranza della focale.**
  `rig_optics.by_rig` confronta la focale di ogni risposta con quella dei corredi (`units.same_focal`)
  a ogni lettura: e' un confronto, non una geometria, ma e' un calcolo in lettura. Si toglie
  scrivendo sulla posa da quale risposta ha preso l'ottica.

- **Spostare un sito non ritaglia le sue notti dichiarate.** Se il fuso cambia -- un segno di
  longitudine corretto -- le notti nate da una risposta restano tagliate col fuso vecchio. Rifarle
  lascerebbe vuota per sempre la notte dichiarata di prima, che la spazzata non tocca
  (`backend/astrolog/spine/group_store.py`, `drop_empty_nights`): la strada e' che lo spostamento
  di data porti la notte con se'.

- **Un mosaico non si divide quando perde il pannello che lo legava.** Se il pannello in mezzo a
  una striscia perde tutte le sue pose, i due lati restano nello stesso mosaico anche se non si
  toccano piu' (`backend/astrolog/spine/mosaic.py`, `_sweep`). E unendo due grafie di una camera,
  se il mosaico con la risposta e' quello della grafia assorbita, il mosaico della grafia tenuta
  resta una domanda sovrapposta: solo le pose rimesse in coda si ripiazzano. Stessa famiglia: se
  la camera si dice per una parte sola dei pannelli di un mosaico confermato, una posa nuova del
  corredo nuovo nel punto di un pannello rimasto sul vecchio ne apre un altro accanto. E un
  pannello che non conta (meno del 25% del lavoro, `spine/mosaic_weight.py`) lega lo stesso i
  mosaici che tocca quando nasce: il suo peso si sa solo dopo, e i mosaici non si dividono.
- **I soggetti di un mosaico si leggono in due posti** (`_most_poses` in
  `backend/astrolog/spine/mosaic.py`, `_SUBJECTS` in `backend/astrolog/spine/mosaic_proposals.py`):
  la stessa giunzione pose-pannelli, una per il piu' frequente e una per l'insieme.
- **Una cartella detta "di calibrazione" che resta senza frame non si puo' piu' contraddire.** La
  domanda *che file sono* si compone dai frame entrati (`backend/astrolog/spine/typeless.py`):
  cancellato il rilevato con la dichiarazione viva, le scansioni dopo saltano quei file per
  "calibration" e il gruppo non compare piu' a video, quindi la risposta resta scritta e non ha piu'
  un posto dove ritirarla. Strada rara -- `tools/reset_db.py` porta via anche le dichiarazioni --
  ma la sezione promette che una risposta si possa cambiare sempre.
- **Aperto un campo col suo bottone, il fuoco non ci va.** "Non e' questo: lo correggo", "Non e'
  in elenco" e, nell'Attrezzatura, "Dagli un nome" spariscono al clic e il fuoco resta sul niente: chi
  usa la tastiera non sa dove e' finito. Vale per tutte le sezioni: si ripara in una volta, con la prova.
- **Una risposta data mentre l'Applica e' in corso si perde**: dopo l'Applica le sezioni ripartono da
  capo (`frontend/src/Confermare.tsx`, `giro`) e cio' che si scrive nell'attesa (~445 ms sulla copia
  vera) sparisce. Il rimedio e' spegnere le sezioni finche' l'Applica non torna.
- **Una risposta sul filtro di una camera rimette in coda tutti i suoi frame senza matrice, anche
  quelli che il filtro lo scrivono** (`_OF_CAMERA` in `backend/astrolog/spine/unfiltered.py`): 6.558
  per 10 su un caso costruito, 0 sull'archivio vero.
- **Unire due grafie di una camera rifa' tutti i frame della camera che resta** (`apply_answers` in
  `backend/astrolog/api/review_write.py`): 6.990 in coda per 432 cambiati, 6,0 s contro ~0,6. Il
  rimedio e' rimettere in coda la tenuta solo se la risposta passata le cambia qualcosa.
- **Due corredi possono avere lo stesso nome** (`rigs.declare_rig` lo accetta): serve un rifiuto per
  nome, come `name_taken` per strumenti e filtri.
- **Due corredi con gli stessi pannelli danno due mosaici con la stessa etichetta**: la sezione
  Mosaici proposti non nomina il corredo (`frontend/src/SezioneMosaici.tsx`). Serve un nome del
  corredo leggibile nella risposta dell'API.
- **Un `catalog_id` si scrive insieme a bande che lo contraddicono** (`gear.declare_filter` in
  `backend/astrolog/spine/gear.py`): le bande vincono sul modello. Nessuna pagina manda le due cose
  insieme.
- **Un campo della scheda di uno strumento non si svuota dalla pagina**: la risposta
  (`InstrumentCorrection`) scarta i campi nulli (`exclude_none` in
  `backend/astrolog/api/instrument_answer.py`). Costa un modo di dire "vuoto" distinto da "non
  toccato"; la guida lo dichiara.
- **Accanto a un gruppo di frame senza nome, cosa il cielo ha trovato negli altri frame della
  stessa notte e dello stesso puntamento**: i frame senza nome non hanno un cielo che dica
  qualcosa, ma i loro vicini spesso si'. Servirebbe un campo `subjects` sul gruppo.
- **La sezione Frame senza camera cresce come gruppi per corredi**: ogni gruppo aperto ripete la
  tendina dei corredi. Si rifa' se un utente arriva li': aprire la tendina solo premendo.
- **L'elenco delle bande nel frontend e' tipizzato ma enumerato a mano**
  (`frontend/src/SezioneFiltri.tsx`): una banda inventata non compila, una mancante si'. Si chiude
  quando l'OpenAPI la manda come dato (`backend/astrolog/api/vocab.py`).

### Macchine ed efficienza, parcheggiate

- **Cambiare il fuso di casa tiene il database dentro la richiesta, e il tempo cresce con le pose
  che cambiano data** (`spine/home_nights.py`, audit del 29/9/2026). Il grosso e' `unnamed.assign`
  chiamata posa per posa. Su un archivio molto grande senza coordinate la scrittura del worker che
  arriva nel frattempo puo' avvicinarsi al tempo che aspetta prima di arrendersi
  (`db/connect.py`, `busy_timeout`). Si toglie scegliendo il gruppo una volta per notte, camera e
  telescopio per le pose senza puntamento, o portando il lavoro fuori dalla richiesta.
- **Su una primaria che ripete `NAXIS`, la strada veloce e astropy dicono due blocchi dati
  diversi** (revisione e audit del 28/9/2026): astropy tiene la prima `NAXIS`,
  `header_read._primary_data_block` l'ultima. Succede su un file a piu' pagine la cui primaria ha
  perso l'END -- astropy fonde le pagine in una senza pixel -- e su una primaria scritta con due
  `NAXIS`. L'impronta prova la strada veloce per prima da quando c'e', quindi e' stabile, e la
  prova delle impronte tiene tutti e due i casi; ma l'oracolo di
  `tests/test_data_block_header_read.py` su quei file direbbe rosso, e il suo banco non li
  contiene. Si decide quale dei due e' giusto prima di toccarlo: cambiare strada cambia le
  impronte di quei file.
- **`rigs._pezzo_id` e' `gear.instrument_id` scritta due volte** (trovata dall'audit del
  27/9/2026, corpo per corpo). Vive in `rigs` perche' `gear` importa `rigs`: si unifica spostandola
  in un modulo che tutti e due possono importare.
- **I file senza tipo di una cartella detta di calibrazione si rileggono a ogni scansione.** Saltati
  alla porta, non hanno una posizione, quindi il pre-controllo incrementale non li riconosce: ogni
  giro riapre l'header e legge l'impronta (`spine/scan.py`), che serve a far entrare un frame
  spostato li'. Misurato su un disco locale in cache (audit del 29/9/2026); su un NAS a freddo no.
  Si toglie ricordando i file saltati con percorso, dimensione e data, cosi' che il pre-controllo li
  riconosca.
- **Per una posa senza camera la notte si chiede due volte** in `normalize`: una per la chiave del
  gruppo (`rigless.key_of_frame`) e una per il corredo della notte (`night_rig.rig_of_night`).

- **Meteoblue, tre cose da decidere** (audit del 26/9/2026): un 429 -- crediti finiti con una
  chiave buona -- conta come rifiuto, toglie il seeing e dice "controlla la chiave"; ogni
  salvataggio di una chiave valida azzera il freno delle dodici ore e spende subito una chiamata,
  e il salvataggio fa il giro del meteo dentro la richiesta; nel primo avvio una chiave scritta e
  non provata si perde premendo Avanti, senza dirlo.

- **Il seeing non e' ancora un fattore mostrato**, come Marco ha confermato che debba essere
  (`docs/domini/ereditato.md`, sezione G). Il progetto di prima lo faceva con una
  soglia dal campionamento del corredo (`old/backend/astrolog/weather/verdict.py`); qui si mostra
  soltanto, perche' la scala dipende dal corredo con cui si uscira', e il
  Meteo non lo sa. Si decide quando il Planner sapra' con cosa esci.

- **La previsione del vecchio sito di casa resta nella tabella**: quando il sito di casa cambia,
  `weather.forecast.refresh` riscrive solo le righe del sito nuovo, e quelle del vecchio restano:
  una previsione intera per ogni sito che e' stato di casa. Nessuno le legge; si tolgono quando
  il meteo guardera' piu' siti, o con una pulizia al cambio di casa.
- **Le risposte dell'API non sono compresse**: la previsione ora per ora e' la piu' pesante, e
  compressa ne peserebbe una frazione. Conta sul NAS guardato dal telefono, e vale per tutte le
  rotte: si decide con la fetta del mobile.

- **La Luna e' stata verificata contro l'USNO, e nel repo non c'e' piu' traccia.** Il confronto
  c'e' stato -- tre posti, due date future, scarto sotto il mezzo minuto -- e viveva in una frase
  di `docs/domini/navigazione.md`, che il piede della barra ha riscritto: adesso non vive **da
  nessuna parte**. Nessun dato di riferimento, nessuna prova, niente che una macchina possa
  rifare. E' l'affermazione su cui poggia la fiducia in tutti gli orari che mostriamo, ed e'
  l'unica che nessuno puo' smentire -- e questa voce e' quanto ne resta. Si chiude con una prova
  `lento` che tiene accanto una manciata di orari dell'almanacco e li confronta.

- **Il piede richiede il cielo a tempo, non a scadenza.** `GET /tonight` costa cento volte una
  lettura, e i suoi numeri scadono al **mezzogiorno del sito**: la rotta manda `night` apposta
  perche' chi la mostra lo sappia. `frontend/src/Stanotte.tsx` si difende con un'ora di
  `staleTime`, che e' una pezza buona ma non la cosa giusta -- per l'ora esatta serve il **fuso
  del posto**, che la rotta oggi non manda. Si chiude quando il piede avra' comunque bisogno di
  sapere che ora e' li' (la riga di *adesso* nel grafico), non prima.

- **Due numeri del foglio vivono anche da noi, senza una guardia che li tenga insieme.** Il
  pavimento del grafico (-15 gradi) e l'altezza della tela in barra (40px) stanno nel foglio --
  nel commento del blocco della Luna e in `--grafico-basso` -- e ricopiati in
  `frontend/src/disegnoDellaLuna.ts` e `frontend/src/Stanotte.tsx`, perche' li' servono come
  numeri e non come stile. E' la stessa forma dei pavimenti di Bortle, che una guardia gia' la
  tiene (`controlli_foglio.pavimenti_del_cielo`): qui non e' nata. Finche' non c'e', il giorno
  che il foglio cambia uno dei due il disegno resta indietro in silenzio.

- **Il dialogo non trattiene il fuoco.** `frontend/src/Dialogo.tsx` fa entrare il fuoco quando si
  apre e lo restituisce a chi l'ha aperto quando si chiude, e tutte e due hanno la loro prova; ma
  col tabulatore si esce dal dialogo e si cammina sulla pagina dietro, che `aria-modal` dichiara
  intoccabile. Chi vede non se ne accorge -- il fondale copre -- chi naviga da tastiera si'. Si
  chiude con un anello sul primo e sull'ultimo elemento raggiungibile, e si prova col tabulatore.

- **Il piede vive dentro il `<nav>` della barra, e non e' navigazione.** Chi salta al punto di
  riferimento *"Le pagine"* ci trova anche sito, cielo e Luna: sei paragrafi senza un titolo che
  li raccolga, quindi senza modo di saltarli ne' di raggiungerli. **Non e' una violazione WCAG** e
  axe non ha una regola che lo veda (misurato: sul piede pieno torna a vuoto). Il foglio pero'
  vuole `.as-lato__coda` figlio di `.as-lato`, e `.as-lato` **e'** il `<nav>`: tirarlo fuori vuol
  dire rimaneggiare lo scheletro. Si guarda nella fetta della veste, dove lo scheletro si tocca
  comunque.

- **Il tetto di lunghezza delle righe non tiene.** Righe oltre i 100 caratteri che portano un
  `# noqa: CODICE - ragione`, che zittisce anche la lunghezza, o un `# pyright: ignore`. Si chiude
  scrivendo la ragione sopra la riga.
- **Rispondere a N gruppi in un Applica costa N letture dell'archivio.** Ogni risposta ritrova il
  suo gruppo rifacendo il lettore da capo, dentro la transazione: `row_of` rifa' `by_group`
  (`backend/astrolog/spine/rigless.py`, `spine/unnamed.py`) o `by_folder` (`spine/typeless.py`),
  filtrando in Python, e poi `requeue` rilegge il gruppo. Misurato il
  15/9/2026:
  - su un archivio **sintetico** di ~21.000 frame: cartelle senza nome 124 ms con una, 994 con dieci,
    9,6 s con cento; 163 ms per cartella senza camera. Sull'archivio vero la lettura costa 17 ms, e a
    otto volte l'archivio venti risposte sulle cartelle prendono 12,1 s;
  - da quando i gruppi portano cosa hai ripreso, la rilettura calcola anche i soggetti e li butta:
    +13% per cartella.
  Il rimedio e' leggere ogni lettore una volta per Applica.

### Misure che dicono di non toccare (ancora)

- **Le ore non sprecano** (audit del 14/9/2026, archivio sintetico della taglia di quello vero): le
  ore degli oggetti costano 2,84 ms e quelle dei mosaici 2,79, circa l'1% di una lettura della
  pagina, con una sola interrogazione per tutta la pagina. E un mosaico non conta due volte i frame
  di un oggetto che sta su due pannelli (1.288.440 s dai mosaici, 1.288.440 dagli oggetti): misurato,
  ma senza un test che lo difenda.
- **`mergeable_into` cresce al quadrato col numero dei pezzi**: 2,4 MB di risposta con 1.007 pezzi.
  Sotto i 100 non si sente; si rifa' mandando le grafie una volta per tipo invece che per pezzo.
- **Sospetto sul bytecode, non chiuso.** Un audit del 14/9/2026 ha visto rossi aritmeticamente
  impossibili (`overlaps_frame(0.9, 120.0, 0.694)` che torna `False`) che sparivano con
  `PYTHONDONTWRITEBYTECODE=1`; rifatto il 23/9/2026 col bytecode acceso, 13 corse su 13 verdi. La
  suite del push (`python -B`) e il job `instabilita` della CI non lo scrivono, la mutazione notturna
  si'. Se un rosso impossibile ricompare, e' qui che si guarda.
- **Tre domande di Da confermare leggono righe che poi scartano, e non vale toglierle** (audit del
  28/9/2026, archivio sintetico da 100.000 pose, pagina intera a circa 0,22 s): senza camera legge
  i gruppi di notti che hanno gia' il loro corredo e ne chiede la risposta uno per uno; senza
  ottica legge le pose di corredi che l'ottica ce l'hanno gia'; i luoghi portano in Python una riga
  per posa invece che per notte, posto e oggetto. Toglierle vale qualche decina di millesimi in
  tutto. Si guarda di nuovo se una di quelle domande torna lenta.
- **La cartella viva come `EXISTS` non paga** (28/9/2026, archivio sintetico da 100.000 pose):
  nelle domande su camera, ottica e nome, `frame_folder.JOIN` e un `EXISTS` sulle posizioni vive
  danno le stesse righe e costano lo stesso, dentro il rumore della misura. Si guarda di nuovo se
  una di quelle domande torna lenta.

### Il resto

- **Fase 2 del refactor, `identify`: cosa il pilota ha lasciato.**
  - La rotazione dello scarto negli assi del sensore e' scritta due volte: dentro `in_frame`
    (`spine/identify_geometry.py`) e come `_in_axes` (`spine/mosaic_geometry.py`). Va in
    `identify_geometry` e la chiamano tutti e due.
  - Il letterale del lucchetto dell'utente (`method`/`confidence` `user`, `review` falso) e' scritto
    due volte in `spine/identify.py`: una costante.
  - Decisioni, candidati, voci del catalogo e wcs viaggiano come `dict[str, Any]`: un `TypedDict` o
    una `dataclass` per forma, cosi' i tipi controllano le chiavi.
  - I nomi interni in italiano (`con_cielo`, `lucchettato`, `fra_i_candidati`...): si rinominano, vedi
    la voce *Il metodo dice "inglese nei nomi"*.

- **La previsione accanto al meteo vero**, per misurare quanto ci azzeccava su quel sito: lo
  storico scrive solo l'osservato, e la previsione di una notte passata si butta.
- **Il meteo, tre doppioni piccoli** (audit del 26/9/2026): le colonne di una riga di
  `weather_nights` sono scritte in tre case (`forecast.write_rows`, l'INSERT dello storico, le righe
  di `sky` e `forecast`); la condizione "il meteo di questa notte" e' in SQL due volte (la pagina
  delle Notti e lo storico), per cui la spina conosce la tabella del meteo anche se non la importa;
  e tre ricette di indirizzi Open-Meteo quasi uguali (`openmeteo.forecast_url`, `cams.url`,
  `history._url`).
- **Lo storico che non arriva non si vede**: se l'archivio rifiuta sempre la richiesta di un sito,
  le sue notti restano "non ancora arrivato" per sempre e l'esito sta solo nel log e in
  `weather_fetches`; e una notte che fa fallire la richiesta ferma anche le successive dello stesso
  sito, perche' si riparte sempre dalla prima mancante.

- **Il frontend nomina in italiano file, componenti e funzioni**, sorgente e prove (`Confermare.tsx`,
  le `Sezione*.tsx`, `scritto.ts`, `pezziDelCorredo`, il banco in `frontend/tests/banco.tsx`), contro
  l'inglese del metodo. Si chiude con un rinomino unico di `frontend/src` e `frontend/tests`.
- **Commenti, docstring e prove dicono ancora "posa" e "luogo"**, contro il glossario
  (`backend/astrolog/spine/unnamed.py`, `frontend/src/SezioneSenzaNome.tsx`...). Schermo e documenti scritti a mano dicono "frame"; il
  codice si allinea in un giro unico, insieme al rinomino del frontend, non a pezzi.
- **Se `/api/v1/settings` non risponde, a schermo puo' non arrivare la frase giusta**:
  `frontend/src/App.tsx` e `frontend/src/Wizard.tsx` controllano solo `if (error)`, e un errore senza
  corpo (il 502 del proxy) arriva come `error` vuoto; un fetch che fallisce mostra il messaggio del
  browser.
- **`tools/dev.py` con `ASTROLOG_PORT` avvia un frontend che non raggiunge il backend**: il proxy di
  `frontend/vite.config.ts` punta sempre a 8765.
- **L'app non si accorge di girare su un database di uno schema vecchio**: successo il 13/9/2026, la
  scansione ha letto 11.678 file e si e' rotta con `no such column`. Lo schema non si migra, ma l'app
  deve dirlo all'avvio, confrontando `schema.sql` con `PRAGMA table_info` in `db/connect.py`.
- **Il marchio di riscrittura si vede scattare su header veri, ma solo su file che non entrano**: su
  14.148 header scatta su 9 stack. La prova su un frame riscritto gira su FITS sintetici: se un utente
  manda una coppia grezzo+calibrato, e' quella la prova che manca.
- **Dividere i frame di una notte dal fondo cielo, invece che a mano** (idea di Marco, 12/9/2026): il
  fondo separa bande larghe e strette di ordini di grandezza, e l'app potrebbe proporre la divisione.
  Tre vincoli: si cercano gli scalini, non le soglie; si misura prima, usando come campione i frame che
  il filtro lo scrivono; e prima di scrivere due volte il fondo si decide insieme a *`frame_metrics` ha
  una provenienza sola per riga*. La divisione a mano resta il pavimento.
- **La stessa chiave due volte nello stesso header: la prima o l'ultima?** Chi rilegge l'header salvato
  come dizionario tiene l'ultima, astropy la prima: `normalize` e la guardia del corpus possono
  rispondere diverso. Da decidere una volta per tutte le chiavi: o si legge la prima come astropy, o
  il corpus prova il salvato come la produzione.
- **`CREATOR` puo' portare una persona invece di un programma**, e allora il marchio finirebbe su un
  grezzo. Non si toglie: e' la chiave dell'ASIAIR. Mai visto su 14.148 file.
- **Fra `identify` e `group` l'archivio ha zero sessioni** (125 -> 0 -> 125): nessuna rotta legge
  `sessions` fuori da `group_store`. Il giorno che nasce una pagina Sessioni, o si legge dalla ricevuta
  o le due spazzate vanno in una transazione.
- **Le voci di calibrazione senza un header per provarle** (`flat bias`, `sky flat`, `dome flat`,
  `twilight flat`) entrano quando un header vero le scrive.
- **Il cielo dentro l'app senza chiave**: il dato di luminosita' a 30 arcosecondi e' 2,9 GB; ridotto, la
  casella diventa di 9 km. Si riapre se qualcuno pubblica un dato piu' compatto.
- **Un indizio ereditato sbagliato brucia il frame**: un `OBJECT` uguale su tutto rende sorelle frame di
  cieli diversi, e quello che eredita finisce `no_solution`. Il ritentativo alla cieca l'ha escluso Marco;
  si riapre con un archivio che ha quel difetto.
- **Un frame il cui file non c'e' piu', o che uno stadio ha segnato `failed`, resta nel residuo per
  sempre**: il pulsante Avvia parte a vuoto. La ricevuta distingue (`waiting`), il conteggio degli stadi
  no. Si chiude con la Diagnostica.
- **Rinominare un sito perde la risposta sulle sue coordinate**: la dichiarazione porta il nome. Si
  chiude quando la rinomina di un sito imparera' la grafia vecchia, come per strumenti e filtri.
- **La spia dei file sommati non si vede su un FITS compresso** (`HISTORY` su un'estensione): si chiude
  quando arriva un file vero cosi'.
- **Quando il catalogo arriva tardi, gli oggetti nati senza non si rifanno**: `load_catalog` non
  chiama `invalidate`. Tocca il primo avvio di tutti: si guarda con calma.
- **Il dubbio vive sull'oggetto, non sul frame**: un frame sbagliato dentro un oggetto lucchettato non
  fa arrivare nessuna domanda. E' voluto; si riapre con una vista per questo genere di segnalazione.
- **Il generatore del catalogo resta in `old/`**: il dato e' portato, ma per rifarlo servono lo script
  e 13 MB di sorgenti. Finche' non si porta, `old/` non si cancella.
- **La relazione pezzo/adiacenza fra oggetti** (`NGC 2244` dentro la Rosetta, `M 110` accanto a `M 31`):
  in `old/` e' misurata (314 relazioni), mai costruita. Serve al Planner e alla Carta del cielo, non alle ore.
- **Una qualita' chiesta e non arrivata non si richiede piu'**: se la passata di analisi di ASTAP non
  risponde, il frame e' `done` senza `frame_metrics`. Si chiude con `measure`.
- **`frame_metrics` ha una provenienza sola per riga, e due produttori** (`astap` oggi, `sep` con
  `measure`): si decide quando nasce `measure`.
- **La ricerca del sito aspetta il suo turno sul percorso della richiesta** (una al secondo): quando
  nascera' il campo che cerca mentre si scrive, davanti ci va un ritardo nella pagina.
- **Sul NAS senza `ASTROLOG_HOSTS` ogni chiamata dalla LAN e' un 400 senza indizio**: il compose la
  dichiara, e l'avvio lo dice se manca.
- Il corredo simulato del Planner ("e se avessi") e' l'unico caso in cui il campo si **deriva** invece
  di misurarsi.
