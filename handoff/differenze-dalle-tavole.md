# Differenze fra le tavole e l'app

Cosa l'app fa diverso dalla tavola congelata, e perche' (Marco, 8/11/2026: a ogni lavoro chiuso
su una superficie, nello stesso commit; ricetta `/porta-tavola`, punto 8). Una voce per
differenza: **tavola** (file e riga in `handoff/design/pagine/`), **app**, **perche'**: una
convenzione pubblica, una decisione di Marco piu' recente, un dato che l'app non ha, o un passo
dopo. Quando la tavola si allinea o l'app la raggiunge, la voce esce.

Tavola: v79 (10/11). Le differenze delle pagine portate prima dell'8/11 sono nelle voci di
`per-design.md`; da qui in poi stanno qui.

## Telaio (passo 33, commit B, 10/11)

Fuori per ora (esiti della lista fissa):
- **Il tondo del modo e "Modo automatico".** Tavola: tondo chiaro/scuro nella testa (Telaio 33),
  "Modo automatico" nell'ingranaggio e "Passa al modo chiaro" in Altro del telefono (Menu 42, 45).
  App: niente. Perche': Marco 10/11, arrivano col passo Tema.
- **"dati simulati" in Stanotte.** Tavola: Telaio 26, 51. App: niente. Perche': i dati sono veri.
- **Il vetro accanto alla bolla.** Tavola: `vb.acc` (Telaio 60-63), spento (`CON=[]`). App: niente.
  Perche': Marco v50.
- **L'anteprima del telefono.** Tavola: telefono 390 x 844 in una finestra larga (Telaio 145).
  App: il telefono riempie la finestra. Perche': serve alla tavola, non a chi usa l'app.
- **Le strisce che scorrono non sfumano il bordo.** Tavola: `componenti/tema.js` 75-85 mette una
  sfumatura di 40 px sul bordo che continua a ogni elemento con `overflow-x: auto` (striscia delle
  notti a ogni larghezza dalla v79, e sul telefono). App: taglio netto. Perche': e' di tutte le
  strisce, non della v78 ne' della v79; va col passo che porta la prima striscia del telefono che ancora manca (piano, passo 33).
- **Gli stati dell'app (caricamento, errore).** Tavola: prop `app` del Telaio (Telaio 13, 38, 55).
  App: li disegna ogni pagina, come prima. Perche': la lista fissa li tiene nelle pagine.
- **Pieno (il Planner a tutto schermo).** Tavola: `pn` (Telaio 147). App: niente. Perche': il
  Planner non c'e' ancora.

Scelte diverse dalla tavola:
- **La scelta del sito in Stanotte.** Tavola v67: i siti coi bottoni; v70: *Cambia ↗*. App: *Cambia ↗*
  verso Impostazioni › Sito. Perche': v70 vince. Il ricordo aperto/chiuso di Stanotte esce con lei.
- **La riga della scansione in corso senza la lettura dei file.** Tavola: sempre «file letti X su Y».
  App: in una fase dopo la lettura «{fatti} su {su}» della fase. Perche': i file letti esistono
  solo nella lettura.
- **Il perche' della scansione bloccata.** Tavola: sempre «Lettura di una cartella non completata».
  App: quella frase solo se la lettura e' caduta (`scan.state` error), altrimenti «Scansione
  interrotta da un errore.». Perche': il worker va in errore anche in solve, identify, db.
- **La barra della scansione non e' un `progressbar`.** Tavola: `role=progressbar` (Menu 13). App:
  disegno nascosto ai lettori; i numeri li dice la riga sotto. Perche': ARIA non ammette un
  progressbar dentro un menu (axe, `aria-required-children`).
- **Le schede nascoste della bolla.** Tavola: chiusa, le altre schede restano nel giro del
  tabulatore. App: `aria-hidden` e fuori dal giro; la scheda Altro dice `aria-haspopup` e
  `aria-expanded`, e porta il segno della scansione (la tavola lo calcola, `navTel`, e non lo
  disegna). Perche': un bottone invisibile non si raggiunge.
- **Il logo del telefono.** Tavola: `span aria-label` (Telaio 44). App: `role="img"`. Perche': axe
  rifiuta `aria-label` su un elemento senza ruolo.
- **Il titolo della pagina sul desktop.** Tavola: nessuno. App: un titolo nascosto in testa al
  corpo, e il link «Vai al contenuto». Perche': chi usa un lettore di schermo sa dove si trova.
- **Il verdetto di Stanotte senza «buona».** Tavola: solo «✓ notte buona». App: «! notte incerta»,
  «✕ notte non adatta», coi segni delle pillole; senza previsione «Previsione non disponibile.
  Dettagli nella pagina Meteo.». Perche': la tavola mostra un caso solo.
- **La pastiglia Stanotte larga al massimo 340 px, padding compreso.** Tavola v78: 340 piu' i 28 px
  di padding (368, `box-sizing: content-box`). App: 340 (`* { box-sizing: border-box }` del foglio
  dell'app). Perche': il brief v78 dice «al massimo 340»; 28 px di nome in meno.
- **Il menu Altro del telefono, l'ordine.** Tavola: Planner prima di Piano della notte (Menu 44), al
  contrario del desktop (46). App: come la tavola, ognuno il suo (`ALTRO_TELEFONO`).

## Cerca (passo 33, telaio commit D, 10/11)

Tavola `componenti/Cerca` v77: finestra al centro col velo sul desktop, pagina intera sul
telefono. Fuori:
- **Il gruppo Progetti, "Progetti" nell'aiuto e «Planner ↗» accanto agli oggetti.** Tavola:
  Cerca 109, 115, 138. App: niente. Perche': le pagine Progetti e Planner non ci sono ancora (i
  rimandi restano spenti finche' la pagina non esiste, `navigazione.md`).
- **Voci delle Impostazioni che Cerca non trova.** Tavola: Nome utente, Tema, Orizzonte, Meteo
  apre su, Soglie del Planner, Tempi della notte, Tetto e sicurezza (Cerca 87). App: niente.
  Perche': Nome utente e Tema stanno in Generale dal commit B delle Impostazioni e entrano in Cerca
  a pagina finita (passo 33); le altre impostazioni non esistono ancora.
- **«dati simulati» nel piede.** Tavola: Cerca 34-35. App: niente. Perche': i dati sono veri.

Scelte diverse dalla tavola:
- **Gli esempi di attrezzatura e sito nell'aiuto.** Tavola: «zwo, FRA400», «Casa». App: il pezzo
  con piu' ore e il sito predefinito di chi cerca, dalla rotta; senza, solo la parola. Perche':
  principio 1, sono l'attrezzatura e il sito di Marco.
- **Le voci delle Impostazioni portano alle sezioni dell'app.** Tavola: «Chiave Meteoblue» in
  Meteo, «Scansione» in Cartelle e scansione. App: Servizi (le chiavi stanno solo li', v68) e
  Scansioni; in piu' Servizi e Backup, che la tavola non elenca. «Percorso di ASTAP» si trova
  anche con D50 (Marco 6/11), non solo D80.
- **Un sito apre la sua sezione.** Tavola: un sito non apre niente (`href: null`, Cerca 116). App:
  Impostazioni › Siti su quel sito, come prima. Perche': la voce c'e', meglio che porti dove si legge.
- **Il telefono copre lo schermo con `position: fixed`.** Tavola: `absolute` e lo scorrimento in
  cima. App: fissa, la lista scorre dentro. Perche': stesso aspetto, senza spostare la pagina sotto.
- **La finestra chiusa col velo, Esc o Annulla riporta il fuoco al bottone Cerca; Tab gira dentro
  la finestra.** Tavola: non lo dice. Perche': finestra modale (`aria-modal`).
- **L'esempio delle notti senza anno.** Tavola: «25/9, settembre 2026». App: «25/9, settembre».
  Perche': Marco 10/11, un anno fisso invecchia; la ricerca capisce il mese senza anno.
- **Quale riga in testa quando ne valgono due.** Tavola: archivio vuoto, scansione, «Cerco…»,
  errore (un solo stato nei Tweaks). App: errore, «Cerco…», archivio vuoto, scansione. Perche'
  l'errore e l'attesa riguardano cio' che hai appena scritto; a scansione in corso, mentre scrivi,
  si legge «Cerco…».
- **Pezzi e siti col testo in qualunque punto del nome.** Tavola: il nome o una sua parola
  comincia col testo (`prende`, Cerca 94). App: come prima di questo commit, il frammento ovunque
  nel nome (con «m» anche «ASI2600MM Pro»); pagine e voci delle Impostazioni invece come la
  tavola. Perche': la regola dei pezzi e' quella dell'Archivio; cambiarla e' un altro passo.
- **Le righe sono `div role=option`.** Tavola: `a href="#"`. Perche': un'opzione di un `combobox`
  non entra nel giro del tabulatore; il fuoco resta nel campo.

## Impostazioni -- il guscio e Generale (passo 33, Impostazioni commit B, 15/11)

Tavola v82 `Impostazioni.dc.html` (desktop 14-41, telefono 216-243, logica 441-473). Fuori:
- **Le linguette Meteo, Planner, Automazione, Selezione dei frame, Diagnostica.** Tavola: `SEZ`
  (455). App: Generale, Siti, Cartelle e scansione, ASTAP, Luna, Servizi, Scansioni, Backup.
  Perche': Meteo arriva al commit D; le altre quattro fuori dalla lista fissa del 14/11.
- **Tema, «Automatico».** Tavola: scelta attiva (`SceltaTema`). App: spento (`aria-disabled`).
  Perche': Marco 15/11, arriva col passo Tema (serve l'ora del sole del sito).
- **Cartelle, ASTAP, Luna, Servizi, Scansioni, Backup col contenuto di prima.** Tavola: le
  sezioni ridisegnate. App: il contenuto vecchio a riga intera, col foglio vecchio, dentro il
  guscio nuovo. Perche': si portano ai commit D-E del passo 33 (Siti portata al commit C).
- **Modo chiaro con le parti vecchie.** Tavola: tutto chiaro. App: cornice e pagine portate
  chiare; Meteo, «in arrivo», la 404 e le sezioni vecchie qui sopra in un riquadro scuro col
  foglio vecchio (`.as-pagina`, `.app-vecchio`). Perche': Marco 15/11, finche' non sono portate.
- **Caricamento ed errore della pagina.** Tavola: li mostra il Telaio (`appSt`, 441-443). App: li
  mostra l'App (`AvvioInAttesa`, `AvvioNonRisponde` del Primo avvio) prima di montare le pagine. Perche': le impostazioni (lingua, tema)
  arrivano prima di ogni pagina.

## Impostazioni -- Siti (passo 33, Impostazioni commit C, 15/11)

Tavola v82 `Impostazioni.dc.html` (desktop 20 e 43-105, telefono 245-305, logica 475-545). Fuori:
- **L'orizzonte**: la riga della carta *Il sito* e la carta *L'orizzonte a 360°*. Perche': lista
  fissa del 14/11, arriva col Planner che lo legge. Per lo stesso motivo *Nuovo sito* dice «Il
  cielo si sceglie dopo, nel sito.» invece di «Il cielo e l'orizzonte si scelgono dopo».
- **«dalle coordinate nei frame»** (Passo Coe in `SITI0`). App: «dalla ricerca per nome» o
  «scritte a mano». Perche': nessun sito nasce dalle coordinate dei frame (`sito.md`).

Scelte diverse:
- **Una via si apre senza scrivere.** Tavola: toccare una via cambia subito «Ora» (anche a
  «nessuno»). App: «Ora» e' il cielo salvato; scrive il gesto che dice un cielo -- una classe, lo
  SQM all'uscita dal campo o con Invio, *Dalla mappa* con la chiave, *Dalle misure* quando bastano.
  Perche': aprire una via per guardarla cancellerebbe il cielo del sito. *Dalle misure* con
  misure scarse, su un sito che un cielo ce l'ha, non dice «il sito resta senza cielo».
- **Coordinate** «45,5455 N - 11,5354 E». Tavola: «45,85 N · 11,57 E». Perche': `coordinate()`
  scrive quattro decimali in tutta l'app (una decina di metri, `i18n/index.ts`).
- **Testi nuovi** (la tavola non ha il caso): altitudine «non nota · il modello del terreno non ha
  risposto»; «La mappa del servizio del cielo non ha risposto: il cielo resta com'era.»; la ricerca
  per nome che non si e' potuta fare, con l'avviso di prima («site.searchFailed»).
- **I 12 mesi** portano l'anno in ogni nome («gennaio 2026: nessuna notte»; tavola solo il primo e
  l'ultimo) e non ci sono finche' nessun frame conta (tavola: 12 tacche vuote): l'app non sa quali
  12 mesi siano.
- **Nuovo sito**: l'altitudine non e' obbligatoria (tavola: *Salva sito* spento senza); senza rete
  il sito si salva e l'altitudine resta «non nota». I risultati della ricerca col nome che il
  servizio da' (tavola: il nome lungo e un nome corto precompilato). Senza nessun sito la sezione
  apre *Nuovo sito* senza *Annulla* (la tavola non disegna il caso).
- **Le pillole** (siti, vie, classi, risultati) sono `a role="button"` con `aria-pressed`. Tavola:
  `a` con `aria-pressed`, che axe rifiuta su un link.
- **Gli errori sotto i campi e l'esito «✓»** si annunciano con `aria-live`, la conferma di Elimina e'
  un `alertdialog`. Tavola: `role="alert"` e `role="status"`. Perche': un avviso col suo ruolo passa
  da `Avviso` (`tools/controlli_veste.py`); qui il segno sta gia' nel testo.
- **Caricamento ed errore dei siti** nella sezione: `Scheletro` e `Avviso` con *Riprova* (la tavola
  li lascia al Telaio).

A Design: sul telefono le vie e le classi sono alte 36 px come nella tavola (`.al-imp__riga-18`),
sotto i 44 px (`per-design.md`).

## Impostazioni -- Cartelle e scansione, Meteo, ASTAP, Luna (passo 33, Impostazioni commit D, 15/11)

Tavola v82 `Impostazioni.dc.html` (desktop 108-189, telefono 307-398, logica 544-608). Fuori:
- **«Su questo computer / Sul NAS»** (`car.dove`). App: niente scelta; l'elenco da sfogliare c'e'
  quando l'app gira sul NAS (`data_root`). Perche': dove sono i file lo sa l'app, non si sceglie.
- **«il disco «Esterno» non risponde»** nella cartella non raggiungibile. App: «non raggiungibile ·
  1412 frame restano in archivio». Perche': il backend non conosce il nome del disco.
- **«Meteo apre su» non si salva**: Deep sky e' l'unica pagina; Sole spento come nella tavola.

Scelte diverse:
- **Il numero della cartella**: «3180 frame in archivio». Tavola: «1240 file FITS». Perche': l'elenco
  sa i frame entrati; i file FITS li conta solo *Verifica*, senza registrare.
- **Conteggio parziale**: «Conteggio interrotto a N: potrebbero essercene altri.» Tavola:
  «interrotto a 5000». Perche': il conteggio si ferma dopo 10 s, non a un numero di file.
- **Verifica percorso di ASTAP scrive il percorso** (tavola: verifica e basta). Perche': il backend
  sa se il programma c'e' solo del percorso salvato; uno sbagliato resta scritto e l'esito lo dice.
- **L'esito di ASTAP** e' un avviso a blocco col percorso e da dove l'app l'ha preso («· PATH di
  sistema»); appare anche aprendo la sezione. Tavola: avviso di riga solo dopo *Verifica*. Perche':
  «trovato» senza da dove non si puo' smentire (`sito.md`).
- **ASTROLOG_ASTAP sbagliata** (tavola: non c'e'): senza percorso scritto, l'esito dice «ASTROLOG_ASTAP
  punta a un file che non esiste: ...» invece di «ASTAP non trovato.», e *Cercalo tu* la salta.
  Perche': la variabile ferma l'analisi e la pagina diceva un motivo falso (#86, Marco 16/11).
- **Cataloghi**: tutti quelli trovati vicino ad ASTAP, con la riga solo per D05, D50, D80 (tavola:
  solo quei tre). Chi non ha ASTAP non vede la riga dei cataloghi.
- **Scansione**: mai fatta dice «Nessuna scansione finora · Scansiona legge le cartelle qui accanto.»
  (Marco 15/11); interrotta e bloccata coi testi del menu dell'ingranaggio (la tavola non le ha).
- **Luna**: le percentuali si salvano lasciando il campo o con Invio (tavola: a ogni tasto). Le
  altezze -5, 0, 5, 10 arrivano dall'API (`choices`).
- **Ruoli**: la domanda di *Togli* e' un `alertdialog`, gli errori sotto i campi `aria-live`
  (tavola: `role="alert"`), come in Siti. La classe `al-imp__cart` della tavola non c'e' nel foglio:
  la riga resta un `div` senza classe.
- **Caricamento ed errore** di cartelle e ASTAP: `Scheletro` e `Avviso` con *Riprova*.
- **Scansione mai fatta, telefono**: «...le cartelle qui sopra.» (desktop «qui accanto», Marco
  15/11). Perche': sul telefono la carta Cartelle sta sopra.
- **Ultima scansione** dice «oggi» e «ieri» solo con un sito di casa (il giorno e' quello del suo
  fuso); senza, la data.
- **Aggiungi su una cartella gia' nell'elenco**: «Cartella già registrata · {percorso} è già fra le
  cartelle qui sopra: i suoi file si leggono già.» La tavola ha il titolo per la cartella spostata.
- **Verifica percorso di ASTAP**, subito dopo: «ASTAP trovato · Gli oggetti ripresi verranno
  identificati.» (tavola); riaprendo la sezione, il percorso e da dove viene.
- **Gli avvisi vanno a capo nelle parole lunghe** (un percorso senza spazi): `overflow-wrap:
  anywhere` inline in `Avviso`, e nella riga «Il nuovo percorso di ...». A Design per il foglio.

## Impostazioni -- Servizi, Scansioni, Backup (passo 33, Impostazioni commit E, 16/11)

Tavola v82 `componenti/SezioneServizi.dc.html` (Servizi 14-23, Scansioni 25-38, Backup 49-60,
logica 76-112). Fuori:
- **«Ultimo tentativo»** dei servizi e il suo avviso «per ora le righe sono simulate». Perche':
  lista fissa del 14/11, la tavola stessa la dice simulata.
- **AAVSO e TNS**. Perche': nessuna pagina legge quelle chiavi (Piano della notte › Ricerca non
  c'e'); entrano con la loro pagina.
- **Diagnostica**. Perche': simulata nella tavola (lista fissa del 14/11).
- **«Ho trovato le tue risposte del ...: le rimetto?» dentro Backup**. App: la proposta prende lo
  schermo prima di ogni pagina (`App.tsx`, `RipristinoProposto`), quindi in Backup non si vede mai.
  Perche': la tavola stessa la segna «Al primo avvio»; si porta col Primo avvio.
- **«da 1 min 20 s» e «ferma da 2 min»** sotto il titolo di una scansione in corso o bloccata.
  App: niente durata finche' la scansione non e' chiusa. Perche': la durata e' del backend, che la
  scrive a scansione chiusa; una che corre la dice «adesso» e la barra.
- **«Dettagli» della bloccata**: porta a Scansioni, dove si e' gia'.

Scelte diverse:
- **Le chiavi non escono dal computer «e non vanno nel file esportato»**. Tavola: «non vanno nel
  backup»; la nota di Backup «non porta le chiavi dei servizi né il percorso di ASTAP». App: il
  file accanto al database le porta (ADR 0017), Esporta no. Perche': Marco 16/11 (le chiavi
  tornano da sole dopo un database rovinato). A Design.
- **«la Ricerca»** tolta dall'intro di Servizi: senza AAVSO e TNS nessuna Ricerca legge le chiavi.
- **Verifica**: l'esito sotto la riga («✓ Chiave valida, salvata.», «✕ Chiave rifiutata: ...»,
  «! {servizio} non risponde ...», «! Risposta non valida ...»; per il cielo anche «! Il
  servizio del cielo ha finito le richieste di oggi ...», #104, Marco 22/11), al posto della
  riga Ultimo tentativo. «Cambia» apre il campo con *Annulla* (tavola: nessun campo dopo Cambia).
- **«4 doppioni dello stesso file»** diventa «4 duplicati»: `duplicato` e' la parola del
  glossario, «doppione» e' vietata.
- **Rimasti fuori**: i motivi dell'app (gia' in archivio, duplicati, calibrazione, immagini
  integrate, ancora in scrittura, solo online) e le cartelle lasciate fuori col percorso. «senza
  data nell'intestazione» non c'e': un frame senza data entra, e si risponde in Da confermare.
- **Non leggibili**: i motivi dell'app (file non apribile, non è un FITS o l'intestazione è
  rovinata, nome non valido, errore interno); i primi cinque, poi «Mostra tutti i N». Un elenco non
  piu' conservato lo dice, senza «Mostra tutti».
- **In corso**: «{letti} file letti su {totale}» della cartella che sta leggendo (tavola: di tutto
  il gesto, che l'app non conta prima di leggere).
- **Bloccata**: anche una scansione rimasta aperta da un AstroLog chiuso a meta' («AstroLog si è
  chiuso durante la lettura di ...»). *Riprova* solo sulla piu' recente, ed e' il gesto del menu
  dell'ingranaggio. Una cartella che non risponde quando parte Scansiona e' nella carta, bloccata
  col suo motivo; se non risponde nessuna non parte niente e non resta carta: lo dice subito
  Scansiona («Nessuna cartella raggiungibile»), come una corsa a vuoto non lascia ricevuta.
- **Il file illeggibile**: tavola «Scritto l'ultima volta» con la data; app senza quella riga (la
  data sta nel file che non si legge; l'Avviso sopra dice cosa succede). Esporta resta acceso:
  legge il database, non il file.
- **Mostra le scansioni precedenti** dopo 20 carte (la tavola ne disegna tre).
- **Le regioni** delle scansioni si chiamano col titolo e l'esito, la barra col suo esito: axe
  vuole nomi unici e una barra col nome.
- **Il file illeggibile** si nomina col percorso intero (tavola: «astrolog-risposte.json»); il file
  dell'app si chiama `risposte.json`.
- **Ripristino non riuscito** vale per Importa (Riprova rimanda lo stesso file).
- **Caricamento ed errore** di ogni sezione: `Scheletro` e `Avviso` con *Riprova*.
- **Verifica** spento col campo vuoto (tavola: acceso). Perche': una chiave vuota per la rotta
  vuol dire «togli», e per togliere c'e' *Togli*.
- **La fine della chiave** «...a3f9» con tre punti (tavola «…a3f9»): e' `config.hint`, la stessa
  in tutta l'app (anche in `GET /settings`).

## Primo avvio -- Sito, Cartelle, Seeing e ASTAP (passo 33, Primo avvio commit C, 16/11)

Tavola v82 `Primo avvio.dc.html` (`V.sito`, `V.pc`, `V.nas`, `V.seeing`, `V.astapNo`, `V.astapCat`).
Il riquadro scuro del foglio vecchio non c'e' piu'. Diverso dalla tavola:
- **Bortle da tastiera**: una fermata sola del tabulatore e le frecce che spostano la scelta senza
  uscire dalla scala. La tavola ha nove fermate e nessuna freccia. Perche': un gruppo di radio si
  attraversa cosi' (ARIA), ed era gia' la regola della scala di prima.
- **Numeri con la virgola**: segnaposto ed esempio dell'errore «46,4843 N», coordinate dei posti
  trovati scritte dall'app (`coordinate()`). Tavola «46.4843 N». Perche': virgola decimale, Marco 6/11.
- **Posto scelto dalla ricerca**: il nome del sito e' il nome intero che il servizio da'
  («Cima Ekar, Asiago, Vicenza, Veneto, 36012, Italia»), le coordinate con tutti i decimali e senza
  lettera. Tavola «Cima Ekar», «45.8486 N». Perche': l'API da' un nome solo, e tagliarlo nella
  pagina sarebbe un calcolo; il nome si corregge nel campo.
- **Trattino corto** in «1 - cielo buio», «Bortle 3 - …» e fra le coordinate dei posti trovati;
  tavola «–» e «·». Perche': testi gia' di tutta l'app (Impostazioni), cambiano insieme o niente.
- **Conteggio parziale**: «Conteggio interrotto a N: potrebbero essercene altri.», tavola «i file
  sono di più»; in Cartelle aggiunte «almeno N file FITS», tavola «oltre N». Perche': il conteggio
  si ferma anche quando una sottocartella non risponde, e allora non si sa se ce ne sono altri.
- **Cartelle aggiunte senza numero** quando l'app non l'ha contato in questa pagina (dopo un
  ricaricamento): il database conta i file solo dopo la scansione, e «0 file FITS» sarebbe falso.
- **Stesso percorso gia' registrato**: «Cartella già registrata» con «{percorso} è già fra le
  cartelle…», come nelle Impostazioni. La tavola usa quel titolo per la cartella spostata
  («Corrisponde a…», «Usa questo percorso»), che l'app ha uguale.
- **Elenco del NAS che cade sotto la cartella dei dati**: l'avviso porta «Cartella dei dati» per
  tornare su; la tavola disegna solo l'elenco che non arriva affatto, senza gesto.
- **Seleziona cartella spento** mentre arriva l'elenco della cartella appena aperta: si
  registrerebbe quella di prima.
- **Verifica o aggiunta non riuscite** (rete, app ferma): avviso «Verifica non riuscita» o
  «Cartella non aggiunta». La tavola non le disegna.
- **Chiave Meteoblue che non parte** (app ferma): riga «Invio della chiave non riuscito».
- **Link di Meteoblue**: la pagina italiana in ogni lingua, lo stesso delle Impostazioni (un
  indirizzo, una casa).
- **Percorso di ASTAP**: segnaposto del sistema (Windows «C:\Program Files\astap\astap_cli.exe»,
  tavola «/opt/astap/astap_cli»); si salva anche lasciando il campo, non solo con Verifica
  percorso. Perche': un percorso battuto a mano e perso perche' non si e' premuto il tasto.
- **Scrittura del percorso non riuscita**: avviso «Salvataggio non riuscito».
- **Escono** (non sono nella tavola): «Il percorso viene verificato subito.», «Serve anche il
  catalogo stellare…», Riprova dentro la ricerca caduta e nell'elenco del NAS, le briciole del
  percorso del NAS, il catalogo da SourceForge (ora hnsky.org come la tavola), «circa 870 MB» del D50.

## Primo avvio -- il guscio, Nome, Tema, chiusura e backup (passo 33, Primo avvio commit B, 16/11)

Tavola v82 `Primo avvio.dc.html` (markup 14-103, logica 106-318). Diverso dalla tavola:
- **Automatico** spento nel passo Tema, e lo stato «tema: automatico senza sito» non c'e'. Perche':
  Marco 15/11, piu' recente della tavola: Automatico arriva col passo Tema (`navigazione.md`).
- **«Leggo le impostazioni…» e «AstroLog non risponde, riprova»** si vedono all'apertura dell'app
  anche a chi il primo avvio l'ha gia' fatto. Perche': finche' le impostazioni non si leggono
  l'app non sa se mostrare il primo avvio o le pagine (`App.tsx`); prima diceva «Caricamento…».
- **Backup trovato**: se Ripristina o Inizia da zero non riescono, un avviso di blocco col perche'
  sotto i bottoni. La tavola non lo disegna; tacerlo lascerebbe credere fatto un ripristino che
  non c'e'. Senza la data dell'ultimo backup la riga sotto il titolo non c'e'.
- **«fatto» e «saltato» dei passi** li decide cio' che l'API ha quando si va avanti (nome salvato,
  sito salvato, cartelle registrate, chiave salvata, ASTAP pronto), non cio' che la pagina
  simula; Tema e' sempre «fatto», come nella tavola.
- **Salta** timbra il primo avvio ed entra nell'app (la tavola apre la Dashboard): stesso esito.
- **Sito dopo un ricaricamento a meta'**: nella lista di lato resta «saltato» finche' non si
  arriva alla chiusura, che lo rilegge dal database e lo segna «fatto». Perche': prima di Fine
  l'app sa solo del sito salvato in questa pagina.
- **«Ultimo backup: 16 nov 2026, 17:37.»** col mese corto; la tavola «12 ottobre 2026, 22:14».
  Perche': la data viene da `giorno()`, lo stesso formato di tutta l'app.
- **Lettura delle impostazioni a 1440**: lo Scheletro esce in due colonne strette col testo
  tagliato, come nella tavola. A Design (`handoff/per-design.md`).

## Notti -- la pagina fra 700 e 1000 px e il sito lungo (v78, 10/11)


## Notti -- Tutto della notte (passo 33, commit B, 8/11)

- **Tilt, soglie del giudizio.** Tavola: incerto fino a 20% compreso (`soglie.js` 106). App:
  incerto da 10 a sotto 20, non adatto da 20. Perche': manuale di ASTAP, "equal or more than 20%
  ... tilt problem" (`pipeline/inspection.py`).
- **Il tilt giudicato sulla mediana.** Tavola: la soglia del frame sulla mediana calcolata dalla
  pagina. App: lo stesso giudizio, scritto dal backend (`night_measures.verdict`). A schermo uguale.
- **Eccentricita', l'asse.** Tavola: «in AR» o «in Dec» solo da 0,40 in su (MisureFrame 242,
  355). App: l'asse quando il frame ne ha uno (stelle non tonde e risolte). Perche': ADR 0039 ha
  tolto le soglie fisse dell'eccentricita'.
- **Luminosita' del cielo senza valore.** Tavola: «nessun frame L o a colori in questa notte» o
  «serve il bias della camera» (235). App: le stesse frasi (Issue #75, 14/11); nella finestra
  dell'oggetto «nessun frame L o a colori», senza «in questa notte»; «non c'e' per questi frame»
  quando i frame misurati dicono motivi diversi o qualcuno e' ancora da misurare.
- **SQM col Bortle.** Tavola: «come / piu' chiaro del Bortle del sito» (242, 262, 358). App: lo
  stesso, classi di ASTAP (Issue #71, 14/11); nella finestra dell'oggetto niente giudizio ne'
  «senza Bortle del sito», perche' le sue notti possono avere siti diversi.
- **Nomi delle misure.** Tavola: in italiano («Fondo cielo», «Massa d'aria», «Gradiente del
  fondo», «Peso del segnale · PSF Signal Weight»). App: il nome tecnico inglese dei programmi,
  uguale in ogni lingua («Background», «Airmass», «Gradient», «PSF Signal Weight»). Perche':
  Marco 9/11, nessun riferimento italiano (la documentazione italiana di Siril le lascia in <!-- software-ok -->
  inglese); contratto `misure.md`.
- **Altre misure.** Tavola: tutte le colonne (passo 32.1, Marco 6/11). App: anche stelle usate,
  scie, tetto, angoli della forma, PSF SNR, altezza, calibrazione dello SQM. Restano fuori il bias
  (della camera, non del frame), la scala di luminosita' (serve la trasparenza di serie, passo
  40) e zenit, angoli, centro, tilt e curvatura dalla FWHM, curvatura in ″ (gia' in Frame per frame,
  Il frame e Tilt e curvatura).
- **Trasparenza, Nuvole.** Tavola: fra le Altre misure. App: assenti. Perche': nella tavola le
  stima la serie dei frame (`serie: 1`, 208), come la trasparenza del passo 40; entrano insieme li'
  (Marco 14/11, Issue #74). Il CLOUDCVR del file e' un'altra misura: N.I.N.A. lo scrive solo con un
  sensore di nuvole collegato.
- **Lato del pilastro.** Tavola: «a ovest N di M frame, prima del meridiano» (248), tessera che
  entra nei grafici. App: «a ovest N di M frame»; la tessera non si sceglie per i grafici ne' per A
  confronto. Perche': e' il `PIERSIDE` dell'header, un fatto e non una misura; ovest non vuol dire
  prima del meridiano per ogni montatura (ASCOM `SideOfPier`).
- **SNR dei pixel.** Tavola: fra le Altre misure, accanto alla tessera SNR. App: e' la tessera SNR
  (`snr`, ImageAnalysis eq. 16), non ripetuta fra le Altre misure. Perche': l'SNR della tessera
  della tavola non ha una misura sua (Issue #73).
- **Setup, titolo.** Tavola: «Setup» o «Due setup». App: anche «Tre setup»... «Nove setup», poi
  «10 setup». Perche': la tavola non dice il caso; in lettere fino a nove, Marco 9/11.
- **Setup, link a Progetti e «simulato».** Tavola: ↗ Progetti accanto all'oggetto, «simulato»
  accanto al titolo. App: assenti. Perche': Progetti non e' ancora portata; niente e' simulato.
- **Frame scelto all'apertura.** Tavola: il sesto misurato (368). App: il primo misurato.
  Perche': il sesto e' una scelta della dimostrazione.

## Notti -- Tutto della notte, Frame per frame e Tilt e curvatura (passo 33, commit C, 8/11)

- **Ordine «per ora».** Tavola: gli oggetti uno dopo l'altro (MisureFrame 275, `u.g - w.g`). App:
  l'ordine di ripresa, un separatore a ogni cambio di oggetto. Perche': la didascalia della tavola
  dice «nell'ordine di ripresa»; con oggetti alternati nella notte i due ordini divergono.
- **Seleziona i frame ↗.** Tavola: il tondo accanto a «Frame per frame» (36). App: assente.
  Perche': Selezione dei frame non e' ancora portata.
- **Nota della luminosita' del cielo nel grafico.** Tavola: «c'e' solo con L, nessun filtro e a
  colori» o «serve il bias della camera» (310). App: le stesse frasi (Issue #75, 14/11); «non c'e'
  per questi frame» con motivi diversi o frame ancora da misurare.
- **Tilt e curvatura del sensore.** Tavola: ricalcolati dalle mediane di angoli e centro (339).
  App: la mediana del tilt dei frame (ASTAP, col giudizio) e quella dell'aberrazione fuori asse,
  in px e in ″. Perche': una lettura non calcola; sono le stesse misure delle tessere (ADR 0044).
- **Verso del sensore.** Tavola: non lo dice. App: la riga 1 del file in basso, come lo standard
  FITS; gli angoli sono ai pixel (1,1) (W,1) (W,H) (1,H).
- **«Stelle troppo piccole per una camera a colori».** Tavola: tilt e curvatura tacciono sotto 1,2
  superpixel (233, 358). App: assente; senza tilt la tessera dice «non c'e' per questi frame».
  Perche': la pipeline non ha questa regola (ADR 0044 dice solo le nove aree).
- **Nome dell'oggetto sotto il grafico, telefono.** Tavola: toglie la prima parola («1396» per IC
  1396, 282). App: il nome intero. Perche': tagliare un nome che non conosciamo puo' lasciarne
  solo un numero ambiguo (principio 1); quello che non ci sta salta, come sul desktop.
- **Bottoni degli oggetti sotto la finestra dei frame.** Tavola: uno per gruppo anche se il gruppo
  e' uno (302). App: solo con piu' di un oggetto. Perche': un bottone solo porta dove si e' gia'.

## Archivio -- La pagina (passo 33, tavola v78, 10/11)

- **Deep sky, Sole, Sistema solare e «+ Aggiungi oggetto».** Tavola: linguette in testa e la
  finestra Aggiungi oggetto (Archivio.dc.html 32, 86-94). App: assenti, la pagina e' il deep sky.
  Perche': nessuna sorgente scrive oggetti a mano, SER o log (ADR 0019, passo 46.12); linguette
  che portano a niente non si mostrano.
- **Anteprime da caricare.** Tavola: un tondo per produzione che aggiunge o cambia la foto (60),
  `accept="image/*"`, foto tenuta per la sessione. App (18/11, passo 33.2): lo stesso tondo, la
  foto salvata; `accept` solo JPEG, PNG e WebP (cio' che il backend legge: un HEIC o un TIFF
  scelto darebbe solo un rifiuto). Un rifiuto la tavola non lo disegna: l'app lo dice in un avviso
  riga dentro la carta, sotto i filtri, coi testi di Marco; finche' resta aperto la riga di carte
  si allunga (vista da Marco il 18/11: va bene). La carta dei frame senza oggetto non ha il tondo.
- **Tipo.** Tavola: la prima parola del tipo (139), quindi «ammasso di galassie» sta con gli
  ammassi. App: le famiglie galassia, nebulosa, ammasso, stella, altro, non si sa (archivio.md).
- **Catalogo.** Tavola: Messier, NGC, IC, Sharpless, altro (128). App: le sigle che il catalogo
  scrive (M, NGC, Sh2, LBN...). Perche': «altro» nasconderebbe quale catalogo; il nome e' un dato.
- **Campo di ricerca.** Tavola: «Cerca: M 31, Velo, Andromeda…» (39). App: «Cerca: M 31, NGC
  7000…». Perche': la ricerca guarda sigle e nomi dell'oggetto, non i nomi comuni (in inglese nel
  catalogo): «Velo» non troverebbe niente. A Design.
- **Nome comune.** Tavola: in italiano (catalogo.js). App: come lo scrive il catalogo, in inglese
  («Andromeda Galaxy»), come gia' la finestra dell'oggetto.
- **Carta dei frame senza oggetto.** Tavola: sotto il nome «un gruppo e 2 pannelli senza oggetti
  identificati» (172, simulato). App: su quella riga «restano qui finché ASTAP non c'è» o «frame
  senza oggetti identificati», le parole che la tavola mette accanto al nome (l'API non conta
  gruppi e pannelli); ore, frame e filtri sono quelli veri. La carta non si apre: quei frame si
  guardano in Da confermare.
- **Costellazioni.** Tavola: in italiano (Cefeo, Cigno, catalogo.js). App: il nome latino IAU
  (Cepheus, Cygnus), uguale in ogni lingua. Perche': decisione di Marco del 27/9, confermata il
  10/11. A Design.
- **Frame senza durata in una riga con ore.** Tavola: «senza durata» solo senza ore (167). App:
  «120 frame · 12 senza durata» (archivio.md, «non lo so» non e' zero).
- **Accanto alla ricerca e a «Mostra altri».** Tavola: «15 di 240» fisso (156, 229). App: le righe
  a schermo su quelle trovate; «Mostra altri N» dice le righe che restano, fino a 20.
- **Aperto dalla Ricerca (`?key=`).** Tavola: non c'e'. App: al posto della riga di ricerca
  «← Archivio completo» e «Risultato della ricerca: M 31» (contratto, ricerca.test.tsx).
- **La rete cade dopo una scelta.** Tavola: non c'e'. App: testa e criteri restano, sotto un avviso
  «Archivio non disponibile · Riprova» (archivio.md).
- **Elenco, la carta dei frame senza oggetto.** Riga senza comando e senza ↗: non apre niente.
- **Testa, frame che non sanno la notte.** Tavola: sempre «· 212 notti» (simulato). App: senza
  nessuna notte nota (frame letti senza un sito) le notti non si scrivono, come le ore a zero
  (archivio.md, «non lo so» non e' zero).
- **Carta dei frame senza oggetto, aperto dalla Ricerca (`?key=`).** Tavola: lo stato non c'e'.
  App: la carta manca, la pagina e' l'oggetto cercato; coi criteri resta in testa come in tavola.

## Archivio -- La finestra dell'oggetto (passo 33, commit B, 9/11)

- **Misure dei frame (commit C, 9/11).** Portate: MisureFrame tipo oggetto, gruppi le notti
  (*Mercoledì 16 settembre*, Riepilogo 121), «Le notti a confronto» con l'esito della notte accanto, tessere FWHM e SNR, le
  mediane in testa (Riepilogo 58, 165; MisureFrame 211, 326, 333). Differenze:
  - **Riga del seeing** «seeing previsto … · FWHM allo zenit …» (MisureFrame 332). App: assente.
    Perche': serve la previsione Meteoblue tenuta per le notti passate; arriva in un passo suo.
  - **Tessera della luminosita' del cielo** senza frame L o a colori (229): come nelle Notti, resta.
  - **FWHM in testa con piu' produzioni insieme** (un mosaico). Tavola: la FWHM sempre, l'SNR no
    (165). App: anche la FWHM solo in secondi d'arco; senza scala «—». Perche': i pixel di due
    camere non si confrontano (ADR 0022), come l'SNR.
  - **«misura in corso»** e lo stato «misure in calcolo»: gli stessi della notte, dall'API
    (`pending`), non simulati.
- **Mosaico, l'ordine dei pannelli.** Tavola: Pannello 1..N nell'ordine dei dati (116). App:
  l'ordine della carta, dal pannello con piu' ore; un pannello con piu' oggetti li dice tutti
  («LBN 796, Sh2 230»). Perche': lo stesso pannello porta lo stesso numero nella carta e nella
  finestra.
- **Mosaico con piu' produzioni.** Tavola: non lo mostra. App: solo le linguette dei pannelli, ogni
  pannello di tutte le produzioni (`?panel` con `?production` e' un 422). Perche': le misure di un
  pannello sono scritte solo cosi'; due righe di linguette non stanno nella testa.
- **In cielo, le righe sotto tipo e costellazione.** Tavola: «idrogeno ionizzato da stelle
  giovani», «alta d'estate e d'autunno» (156). App: vuote. Perche': testi simulati, il catalogo
  non li ha.
- **Setup, «simulato».** Tavola: 35. App: assente, come nelle Notti (sopra).
- **Le notti, riga senza Luna.** Tavola: sempre la Luna (121, simulata). App: la cella vuota quando
  la notte non sa la sua Luna; il cielo e' la frase corta delle Notti.
- **Pagina intera con «← Archivio».** Tavola: `contenitore="pagina"` (Riepilogo.dc.html). App:
  solo la finestra; sul telefono la finestra e' gia' a pagina intera.
- **Dalla notte.** Tavola: gli oggetti della notte non aprono niente (Riepilogo.dc.html 53). App:
  il nome apre la finestra dell'oggetto al posto di quella della notte. Perche': lista fissa di
  Marco, 9/11 (si apre da Archivio, Gli oggetti delle Notti, Ricerca).
- **↗ Progetti.** Assente: Progetti non e' ancora portata.
- **Una Luna piena e mezza.** Tavola: «più di 1 Lune piene» da 1,5 a 2 Lune (132). App: «più di
  una Luna piena». Lo stesso giorno da due siti: tavola non lo dice; app «il 18 maggio 2024 · 2
  notti».

## Dashboard -- La pagina (passo 33, commit C, 11/11)

Fuori per ora (esiti della lista fissa):
- **Progetti in corso, vista Progetti, «Prima scansione finita».** Tavola: carta dei progetti, la
  vista del grafico e la domanda dei progetti finiti (Dashboard.dc.html 21-24, 85-98). App:
  assenti; le prossime 3 notti prendono la riga intera, come la tavola senza progetti (297).
  Perche': i progetti non esistono ancora (passi 44, 44.1).
- **Il Sole.** Tavola: la scelta Luna/Sole e la carta del Sole con Kp (55-72). App: la scelta ha
  solo «Luna», come lo stato «Sole non disponibile» della tavola (570). Perche': passi 46.10-46.12.

Diverse dalla tavola:
- **Le sei carte del meteo restano le stesse anche a notte coperta.** Tavola: con la notte
  coperta Pioggia e Visibilità prendono il posto di Seeing e Aerosol (360-365). App: sempre
  Nuvole, Seeing, Jet stream, Vento, Condensa, Aerosol; Seeing e Aerosol senza ore dicono «non si
  misura» (stato della CardMeteo). Perche': nessun dato dice quando una notte e' «coperta» per
  cambiare le carte; sei carte al loro posto (Marco, 12/10). A Design.
- **«La prossima notte buona».** Tavola: a notte coperta la testa dice «coperto dalle 17, pioggia
  fino alle 04 · la prossima notte buona e' venerdi' 2, con 8,4 ore di posa» (427). App (18/11,
  passo 33.4): la stessa frase in testa alla riga di sempre, prima di buio, trasparenza, modelli e
  vento, solo a notte non adatta; senza le ore se quella notte e' di tendenza; niente se nessuna
  delle sette notti e' buona. In testa perche' la riga e' una sola e si taglia alla larghezza:
  in fondo non si vedeva. La causa in testa («coperto dalle 17») resta fuori: la riga dice gia'
  l'accordo dei modelli e le carte la causa. Sul telefono la riga mostra solo il primo pezzo, che
  a notte non adatta e' questa frase.
- **La Luna sopra le curvette delle prossime notti.** Tavola: «Luna 00:10» (523). App: «5 h di
  buio senza Luna · Luna sorge 00:10», o «tramonta», «tutta la notte», «non sorge»; la linea
  tratteggiata come la tavola, ogni 15 minuti. Perche': l'ora sola non dice se sorge o tramonta, e le
  ore senza Luna contano per la banda larga (Marco, 13/11, #65).
- **La Ripresa delle prossime notti.** Tavola: dalla Luna ora per ora (509). App: dalle ore di
  posa divise per banda («3,1 in banda larga, 1,5 stretta»), che il backend scrive per notte.
- **Prossime notti senza previsione.** Tavola: le tre notti restano, con le ore di buio e la
  Ripresa dalla Luna (526). App: le tre notti restano col buio dal calendario della Luna, senza la
  Ripresa (13/11, #66). Perche': la Ripresa dell'app viene dalle ore di posa della previsione.
- **Da riprendere.** Tavola: le domande una per una («Due siti lo stesso giorno», «Filtro
  sconosciuto», 588). App: «Da confermare, N» con Rispondi e i frame fuori dai conti. Perche':
  l'elenco tipizzato delle domande arriva col passo 33.4.
- **Prima scansione.** Tavola: «in lettura: il 2024» (583). App: la cartella, file letti su quanti
  e quanto manca, senza l'anno. Perche': l'anno in lettura e' una scelta di prodotto (data del
  file o della ripresa), Issue #69.
- **Il dettaglio della Luna.** Tavola: «(le soglie stanno nelle Impostazioni, gruppo Luna)» (596).
  App: «(le soglie vengono dalla scala della Luna del Meteo)». Perche': i gradini 25/65 sono della
  scala del Meteo, fissa; le Impostazioni decidono solo la notte buona, che la Dashboard non
  mostra (Marco, 13/11, Issue #70). A Design.
- **Carta del meteo «Non disponibile».** Tavola: «Non tutti i modelli danno la visibilità.» App:
  «La previsione non la dà per stanotte.» per ogni misura senza ore (Marco, 11/11, Issue #59).
  Perche': la riga della tavola vale solo per la visibilità. A Design.
- **Seeing stimato dal jet con la chiave buona.** Tavola v59: la stima «scarso» solo accanto a
  «serve una chiave» o «chiave non valida». App (23/11): anche con la chiave buona, se Meteoblue
  non da' il numero (ultima notte oltre i suoi 7 giorni) la carta dice «scarso · stima dal vento
  in quota», senza frase sulla chiave; Meteo uguale, avviso d'attesa senza bottone. Perche': il
  backend stima ogni volta che il numero manca (ADR 0034). A Design.
- **Seeing stimato negli Altri fattori.** Tavola Meteo v82: la stima sta negli Altri fattori, in
  fondo, con la pillola «scarso · stima dal vento in quota» (Meteo.dc.html 413, 451-452). App
  (23/11): la stima non pesa, quindi non c'e' negli Altri fattori (c'e' gia' il jet, con le stesse
  ore); la dice la carta Seeing. Perche': la pagina di oggi mostra solo «non adatta», senza la
  pillola della stima; torna con /porta-tavola della pagina Meteo v82.
- **Il punto della Trasparenza sul cursore.** Tavola: punto e riquadro leggono lo stesso valore
  per passo (Dashboard.dc.html 454-456). App: il punto sta sulla linea disegnata fra i centri
  delle ore, il riquadro dice il valore dell'ora intera; fuori dalle :30 i due differiscono (a
  mezzanotte 55 contro 50). Perche': la previsione e' oraria e il cursore va a 15 minuti; un
  valore interpolato nel riquadro sarebbe un testo nuovo, da decidere (21/11).

## Dashboard -- Il 2026 e Filtri del 2026 (passo 33, commit D, 11/11)

Le differenze del commit D le ha disegnate la v80-v82 (4,6 con la virgola, «Filtro non
indicato», filtro a colori in tre fette, taglio a sei righe, stati I J K e P Q R H2 P0); portate
il 12/11. Restano diverse dalla tavola:
- **Notti al mese senza notti.** Tavola, stato J: «0» (Dashboard.dc.html 544). App: «0,0».
  Perche': lo stesso decimale fisso di «2,0» e «4,6» (tavola v76, `posaN`); un numero solo che
  cambia forma per lo zero e' un caso in piu'. Non a Design: differenza di una cifra.
- **Il quadretto per giorno** (tavola v37) esce: la v79 non lo disegna.

## Da confermare -- Il backend (passo 33, commit A e B, 12/11)

- **Montatura** (tavola v82, `Da confermare.dc.html` 220-222; DECISIONI 3.8): fuori. Tavola:
  «EQ6-R è la tua montatura? Sì, è la montatura · La montatura è un'altra». App: la sezione non
  c'e'. Perche': nessun header vero mostra lo stesso nome come telescopio e come montatura (in
  `tests/header/` l'ASIAIR scrive la montatura, N.I.N.A. l'ottica), e la tavola non dice cosa fa
  «La montatura è un'altra»; Marco, 12/11: «non saprei cosa fare qua». Entra quando un file vero
  porta il caso (Issue #24).
- **Progetti finiti** (tavola 232-245): fuori fino ai Progetti (passo 44.1).
- **«Nessun filtro» c'era già**: tavola, esito di Applica; prima l'app rifiutava con un 409.
  Ora i frame passano alla riga che c'e' (contratto `docs/domini/spina.md`).

## Da confermare -- Il guscio (passo 33, commit D1, 12/11)

- **Rifiuto di Applica.** Tavola: esito `role="status"` (35). App: `role="alert"`. Perche': un
  rifiuto annulla tutte le risposte, si annuncia subito.
- **Guasto di lettura ed elenco dei modelli che non risponde.** Prima: `alert`. App: `status`.
  Perche': passano dall'`Avviso` comune, che e' sempre `status`.
- **Stati vuoti** (caricamento, errore, zero frame, niente da confermare). Tavola: griglia a due
  colonne, colonna sinistra nascosta (`L.cols` resta `300px` tranne che in caricamento, 293). App:
  una colonna. Perche': l'avviso finirebbe nella cella da 300 px.
- **«La rielaborazione è in coda».** Tavola: con ogni frame da rifare (289). App: solo con frame da
  rifare e lavoro non partito. Perche': l'API manda `run_started` falso anche senza niente in coda,
  e con lavoro partito la coda non c'e'.
- **Pagina ferma durante Applica.** Tavola: opacita' .45 e niente clic su indice e sezioni (`fz`,
  181). App: in piu' `inert`, anche sui tipi del telefono. Perche': cosi' anche la tastiera non
  tocca risposte che andrebbero perse.
- **Rifiuto `model_contradicts_bands`.** Tavola: «Il filtro scelto per «O3» ha la banda Hα, i frame
  dicono OIII...» (358). App: «Il modello scelto non ha le bande indicate. Scegli un altro modello o
  un filtro nuovo. Nessuna modifica salvata.» Perche' (rivisto 14/11, Issue #78): la pagina non
  puo' ricevere quel rifiuto, manda un modello o le bande, mai insieme (`SezioneFiltri.tsx`
  `manda`); e i filtri chiesti hanno banda sconosciuta (`review.py`, `Passband.UNKNOWN`), quindi
  nessun frame "dice OIII". Il caso della tavola non esiste nell'app; la frase resta per un client
  dell'API.

## Da confermare -- Le domande (passo 33, commit D2, 12/11)

Righe, domande, prove e parti sulle classi `al-conf__` (`Da confermare.dc.html` 46-78). Restano
diverse dalla tavola:
- **Strumenti duplicati, il titolo.** Tavola: il nome che resta («ZWO ASI2600MM Pro», 318). App: la
  grafia che se ne va, «Si', unisci a» quella che resta. Perche': la domanda e' su quella grafia;
  i frame della riga sono i suoi.
- **Filtri, la ricerca nel catalogo.** Tavola: il campo parte scritto («antlia oiii», `cerca0`,
  320). App: vuoto. Perche': nella tavola e' simulato; l'app non indovina la marca.
- **Attrezzatura, l'Ottica accanto ad «Altra camera».** Tavola: sempre (203), anche con la parte
  Ottica sotto. App: solo se la scheda non chiede l'ottica a parte. Perche': due campi per la
  stessa ottica, e non si saprebbe quale vale.
- **Attrezzatura, setup e ottica insieme.** Tavola: non lo dice. App: il setup parte per pezzi
  scritti (camera, focale, ottica), un Applica solo (Issue #20); un setup senza focale parte da
  solo, con la sua ottica.
- **Attrezzatura, scheda a meta'.** Tavola: «senza risposta» finche' tutte le parti non hanno una
  risposta (`stat`, 380). App: «da applicare» appena una parte e' in mano. Perche': e' lo stesso
  conto di tacche, indice e piede.
- **Oggetti, «Perche' l'app dubita».** Tavola: «metodo: nome nei file e plate solving», «fiducia
  media: il centro del campo cade fra...» (322). App: «metodo: plate solving», «nome nei file» o
  «nome storico nei file», e «fiducia bassa» o «alta» (Marco, 12/11). Perche': l'API non ha
  «media», e la frase dopo i due punti e' simulata. A Design.
- **Oggetti, «Altri frame».** Tavola: non c'e'. App: sotto «Oggetti nel campo», i frame senza
  oggetti identificati o non risolti, in Attrezzatura e Frame senza sito. Perche': «non lo so» non
  e' zero.
- **Oggetti identificati sul telefono.** Tavola: il caso solo, senza elenco (276). App: uguale;
  l'elenco c'e' solo se Oggetti non ha casi.
- **Oggetti identificati, l'ordine.** Tavola: per nome (IC 1396, M 31, M 33, 351). App: l'ordine
  dell'API, piu' frame prima (`review_page.py`). Perche': chi corregge cerca prima gli oggetti
  con piu' ore; l'ordine e' del backend, la pagina non riordina.
- **Oggetti identificati, «Vale per il frame».** Tavola: «Vale per tutti i 186 frame» (259). App:
  con un frame solo «Vale per il frame.».
- **Mosaici, l'aiuto del nome.** Tavola: «Nome proposto dall'app: l'oggetto con piu' frame nel
  campo» (228). App: «Nome proposto dall'app: Sadr.». Perche': il backend propone l'oggetto di
  catalogo al centro, o se non c'e' quello con piu' frame; il nome lo dice senza sbagliare il
  perche'.
- **Frame senza data, sito non dichiarato.** Tavola: «sul sito di Casa» (224). App: senza sito
  «La notte comincia la sera di quel giorno.». Senza notti dello stesso setup «Scelgo una notte»
  e' spenta.

## Attrezzatura -- Il backend (passo 33, commit A, 12/11)

- **Luna piena del campo.** Tavola: 0,52° (`Attrezzatura.dc.html` 328). App: 0,527°
  (`moon_deg`). Perche': il diametro apparente medio della NASA, 1896″ (NSSDC Moon Fact Sheet);
  a schermo la Luna e' piu' larga di un pixel su 100.
- **«{n} frame da rielaborare» dopo sensore, risoluzione, focale o fattore.** Tavola (192,
  DECISIONI v66 10.3): dopo ognuna di queste modifiche. App: solo quando uno stadio rilegge
  davvero dei frame (colore e pixel della camera, banda del filtro, unione, parte scelta).
  Perche': nessuno stadio legge gli altri campi scritti da te.
- **Elimina l'ottica o la camera di un setup senza frame.** Tavola: non lo prevede (la sua ottica
  di un setup ha sempre frame). App: rifiutato (409 `in_rig`), il setup e' fatto di loro. Il testo
  a schermo arriva col commit D.

## Attrezzatura -- Il guscio (passo 33, commit B, 13/11)

Barra con «Aggiungi strumento», indice a carte (Setup e Componenti), riga dei frame da
rielaborare, Scheletro, Avviso, vuota, telefono indice e dettaglio con «← Attrezzatura», sulle
classi `al-attr__` (`Attrezzatura.dc.html` 19-49). Restano diverse dalla tavola:
- **Titolo di un setup senza nome.** Tavola: ottica e camera senza una marca di una lista fissa
  (ZWO, Askar, ...) e solo la prima parola, «RedCat · ASI2600MM» (`corto`, 444). App: il modello
  del pezzo se scritto, se no il nome senza la marca scritta sul pezzo, se no il nome intero,
  «FRA400 · ASI2600MM Pro» (`title` dall'API). Perche': una lista di marche vale per l'archivio di
  chi l'ha scritta (principio 1), e la prima parola fa uguali due ottiche diverse («EdgeHD 8» e
  «EdgeHD 11»). Il pezzo che manca resta «?» come nella tavola, «? · EOS 700D».
- **Il dettaglio sotto l'indice.** Tavola: carta del setup, Parti, Campo, Dati del setup, Filtri,
  Treno ottico; il gruppo a righe con Modifica (51-117). App: le righe di prima (`UnCorredo`,
  `UnPezzo`, `UnFiltro`) del setup o del gruppo scelto. Perche': arrivano coi commit C e D.
- **Il modulo di «Aggiungi strumento».** Tavola: il Modulo in testa con i tipi a icone (32). App:
  il modulo di prima. Perche': arriva col commit D. Fatto al passo 33, Sistema A (17/11): sotto.
- **Il titolo grande «Attrezzatura».** Tavola: un h1 che il foglio nasconde (`al-attr__testo-1`).
  App: nessun h1 nella pagina. Perche': lo porta gia' il telaio per chi legge con la voce; a
  schermo non cambia niente.
- **Riga dei frame da rielaborare.** Tavola: `role="status"` (26). App: `aria-live="polite"`, si
  annuncia uguale. Perche': `status` a mano e' solo dell'`Avviso` comune, che non ha il segno ↻.

## Attrezzatura -- Il dettaglio del setup (passo 33, commit C1, 13/11)

Carta col nome e Rinomina, Parti con Seleziona, Campo col confronto e la Luna, Dati del setup,
anello dei Filtri, sulle classi `al-attr__` (`Attrezzatura.dc.html` 51-97) e sul Modulo comune.
Restano diverse dalla tavola:
- **Una parte scelta a mano e quelle dei file.** Tavola: la scelta sola, «(scelta a mano)»
  (`parte`, 305). App: la scelta e anche i pezzi che i file nominano, ognuno coi suoi frame.
  Perche': fuori dalla montatura la scelta vale solo dove il file non nomina niente, e i frame che
  nominano un altro pezzo restano suoi.
- **Programma di ripresa senza «Seleziona».** Tavola: Seleziona con N.I.N.A. e ASIAIR (320, 563).
  App: nessun bottone. Perche': il programma lo dicono solo i file e l'API non ha una scelta del
  programma; e' fuori.
- **Salva senza cambiare niente.** Tavola: scrive la stessa scelta. App: chiude il modulo senza
  scrivere. Perche': ogni scelta rimanda i frame del setup a rielaborare.
- **Cio' che manca a un conto.** Tavola: «manca il campionamento» nel rapporto guida/ripresa (353).
  App: il primo dato che manca, «manca il pixel della camera». Le frasi si compongono dal campo e
  dal pezzo che l'API nomina (`missing`), anche per casi che la tavola non scrive («manca la focale
  del setup»).
- **Dati del setup di un setup appena nato.** Tavola: sempre. App: la sezione non c'e' finche' i
  conti non sono scritti (`numbers` nullo, fine del giro).
- **Etichette del confronto dei campi.** Tavola: `corto` (444), il nome o le due parole senza una
  marca di una lista fissa (ZWO, Askar...), solo la prima parola («103APO · ASI2600MM»). App: il
  `title` dell'API, il nome o il modello del pezzo, altrimenti il nome senza la marca scritta sul
  pezzo, intero. Perche': niente lista di marche (principio 1). Un pezzo senza marca ne' modello
  porta il nome intero («Askar 103Apo · ATR2600M»), che col foglio (`strato-2`, nowrap) esce da un
  riquadro piccolo e copre la Luna: come stare in un riquadro stretto e' chiesto a Design.
- **Numeri delle schede col punto.** Tavola: «pixel 3.76 µm», «backfocus 55 mm ± 1» (`vir`, 550).
  App: la virgola, «pixel 3,76 µm». Errore della tavola (virgola decimale, Marco 6/11): a Design.
- **Intervallo della scala di guida.** Tavola: «consigliata fra 0,5 e 4″/px» scritto nel testo
  (352). App: uguale a schermo, ma i due numeri arrivano dall'API (`range_from`, `range_to`), che
  ha la soglia con la sua fonte.

## Attrezzatura -- Il treno ottico (passo 33, commit C2, 14/11)

L'esploso dopo la carta del setup (`Attrezzatura.dc.html` 63-66, `treno` 447-548), con le
pillole sopra e sotto, i fili, la legenda numerata sul telefono; la geometria e' quella della
tavola, provata alla cifra su un rifrattore, un Newton e uno Schmidt-Cassegrain
(`tests/disegno-treno.test.ts`). Restano diverse dalla tavola:
- **Quali pezzi.** Tavola: `trenoDi` (332) prende il primo nome di ogni parte. App: i pezzi che i
  conti leggono, la parte scelta se no la piu' usata, dall'API (`pieces`). Perche': una regola
  sola fra Dati del setup e treno, e la pagina non sceglie.
- **Treno di un setup appena nato.** Tavola: sempre, con l'ottica. App: non c'e' finche' i conti
  non sono scritti (`pieces` nullo, fine del giro), come i Dati del setup.
- **Schema ottico non disegnato.** Tavola: cinque schemi, quello non scritto e' rifrattore. App:
  uguale; anche un obiettivo fotografico e «altro» si disegnano rifrattore. A Design.
- **Il treno che si disegna.** Tavola: `alDraw` in 0,9 s (helmet della pagina). App: l'animazione
  c'e' ma il foglio non ha `@keyframes alDraw`: il treno compare intero. A Design.
- **Una pillola senza pezzo.** Tavola: `vaiComp` torna nullo se il nome non e' fra i componenti e
  la pillola non apre niente. App: ogni pezzo del treno e' fra gli strumenti (lo dice l'API per
  id), la pillola apre sempre.
- **Nomi che non entrano.** Tavola: le pillole coi nomi si spingono di lato; con nomi lunghi
  (driver ASCOM, «ASCOM ToupTek AAF») la prima esce a sinistra dal riquadro. App (Marco, 14/11):
  se i nomi di una riga non entrano, quel treno passa alle pillole col numero e alla legenda a
  due colonne, come il telefono; chi rinomina corto torna ai nomi. A Design.

## Attrezzatura -- Il gruppo e il modulo di un pezzo (passo 33, commit D, 14/11)

Il gruppo di un tipo (`grp`, 102-117) e il modulo di modifica (`modulo` k `mod`, 223-301, con
`componenti/Modulo`): righe con la scheda intera, ore e barra dall'API, Modifica nella riga, nome e
modello e dati tecnici, Unisci a, Elimina con la conferma. Restano diverse dalla tavola:
- **«N frame da rielaborare» prima di salvare.** Tavola (v66 10.3, `righe` 273): la riga
  «cambia il cielo dei frame» appena cambi sensore, pixel, risoluzione, focale, fattore o tipo.
  App: il numero arriva dopo Salva (`requeued`), e solo per cio' che uno stadio rilegge davvero
  (contratto attrezzatura.md): prima non si sa, e per sensore, risoluzione, focale e fattore
  sarebbe falso. Resta la riga dell'unione, «N frame da rielaborare: passano a X», che e' vera.
- **I calcolati nel modulo.** Tavola: rapporto focale, potere risolutore e sensore in mm cambiano
  mentre scrivi. App: li scrive il backend (`numbers`), si aggiornano dopo Salva; senza dati
  «servono apertura e focale». Perche': il frontend non calcola.
- **Il bias.** Tavola: un campo «Bias (ADU)». App (Marco, 14/11): uno per offset dei file,
  «Bias (ADU), offset 50»; con un offset solo resta «Bias (ADU)»; senza offset scritto «Bias
  (ADU), senza offset». Nella scheda «bias 500 ADU, offset 50». A Design.
- **Elimina dell'ottica o della camera di un setup senza frame.** Tavola: non c'e' il caso
  (`usato` guarda solo i frame). App (Marco, 14/11): spento con «Fa parte di {setup}: un setup è
  fatto della sua ottica e della sua camera.», il rifiuto `in_rig` del backend. A Design.
- **«dai file».** Tavola: anche sul Nome di una camera rilevata (`comp.da`). App: solo sui campi
  che i file dicono (`from_files`, il sensore della camera), come il contratto; il Nome non ha
  pillola, gli altri campi scritti «inserito».
- **Gli oggetti nella riga.** Prima del porting la riga diceva frame, notti e oggetti. App come la
  tavola: solo le ore con la barra.
- **«inserito manualmente» sui filtri.** Tavola: anche su un filtro scritto a mano (`man`). App:
  l'API non dice se un filtro e' nato dai file, la pillola sta solo sui pezzi. A Design se serve.
- **Scegliere o togliere un'unione** rimette il modulo com'era: una modifica nascosta dai campi
  che spariscono partirebbe senza vedersi. La tavola tiene i valori scritti.
- **I numeri della scheda** si scrivono come sono (`vir`: «pixel 3,8 µm», «riduzione 0,8×»);
  fino al commit C1 l'app li scriveva a due decimali («3,80»). Corretto qui.
- **Un filtro senza bande scritte** (riconosciuto dal nome, `Lum`): la riga mostra la banda che
  il nome da' (`passband`) senza larghezza, e il modulo parte da quella; parte solo se la cambi.
  La tavola non ha filtri senza bande.
- **Un pezzo senza frame** (scritto a mano, o un setup appena nato) dice «non indicato nei file»,
  come la tavola per un pezzo scritto a mano, invece di «< 6 min» con la barra al 3%. Una
  montatura scelta su un setup senza frame non dice piu' «non associata a un setup».
- **Il rifiuto di Elimina al gesto** (un pezzo non ancora contato) sta fra gli errori del modulo,
  col «!», come la tavola (`delErr`).
- **L'ordine dei campi della camera** e' quello della tavola (`TEC`: sensore, risoluzione, pixel,
  tipo, bit): l'API lo manda cosi' (`instrument_answer.CARD`).

## Sistema -- Token, telaio e mattoni (passo 33, 17/11)

`Sistema.dc.html` non e' una pagina dell'app: e' il catalogo dei token, del telaio e dei mattoni.
Il foglio e' gia' identico alla consegna, il telaio gia' portato, i mattoni stanno in
`frontend/src/componenti` con le classi `al-c-*`. Si porta come i componenti contro il catalogo.
- **Commit A, il Modulo coi tipi a tasselli** (`componenti/Modulo` 18-19): «Aggiungi strumento»
  dell'Attrezzatura sceglie il tipo a tasselli con l'icona, poi «Tipo: ... Cambia». Restano
  diversi: i calcolati del pezzo nuovo (rapporto focale, potere risolutore, sensore in mm) non ci
  sono, perche' li scrive il backend e un pezzo nuovo non ha ancora numeri; la bozza resta con
  «Cambia» solo fra i tipi di strumento (nome, marca, campi in comune), filtro e setup ripartono
  vuoti, come prima del porting. Il disco del filtro nuovo prende il colore delle bande dalla
  tabella `band_passbands` di `GET /gear`, la stessa regola della scrittura (`discoK` della
  tavola). «Quante bande» parte con «1» scelto (tavola: nessuna pillola scelta, ma una banda gia'
  in vista): la pillola dice quello che il modulo mostra. Fra i tasselli e Salva l'app non ha i
  18 px di un contenitore dei blocchi vuoto che la tavola disegna (`blocchi: []`): a Design.
- **Commit B, i mattoni comuni dove il telaio ridisegnava**: le righe di cio' che la scansione
  non ha potuto fare (un rifiuto, una cartella persa, le cartelle saltate) passano all'Avviso
  della consegna, tipo riga, col «!» e «Dettagli» come bottone; prima classi `as-avviso` e un
  link. Tutte annunciate come stato (`role="status"`, come l'Avviso della consegna): prima il
  rifiuto dopo un gesto interrompeva chi legge (`alert`). Il disco della Luna di Stanotte, rimasto
  senza utenti, esce.
- **Fuori, con la pagina Meteo** (dopo il passo 13): CardMeteo «telefono compatta», `anello` e la
  carta che si apre (`aperto`); il Meteo di oggi usa ancora i suoi mattoni vecchi.
- **Fuori, coi Planner** (passo 45): il vetro sul cielo, `PlannerSolare2`, `PlannerEventi2`.
- **SceltaTema senza sito**: Automatico resta spento finche' non arriva il passo Tema (Marco 15/11).

## Stanotte e Dashboard -- Il buio da mezzogiorno a mezzogiorno (passo 7, 19/11)

- **Un caso che le tavole non disegnano**: sopra gli 84 gradi il buio puo' coprire la notte intera.
  Dove la tavola scrive le ore del buio («buio 20:48-05:48»), l'app dice «buio tutta la notte»
  (Marco 19/11), e la legenda del grafico «Buio tutta la notte»; prima «12:00-12:00» (Issue #18).

## Notti e Dashboard -- Il buio nautico (passo 7, ADR 0035, 19/11)

- **Un terzo gradino che le tavole non disegnano**: senza buio astronomico la tavola ha un testo
  solo, «{sb} ore visibili col Sole sotto l'orizzonte», corto «{sb} ore visibili, senza buio»
  (Notti.dc.html riga 211). L'app ne ha due: col buio nautico (Sole sotto -12) «{n} ore visibili
  col buio nautico», corto «{n} ore visibili, buio nautico»; senza nemmeno quello il testo della
  tavola (Marco 19/11: tre gradini, testo nello stesso stampo).
- **Dashboard, le ore serene**: accanto a «di buio sereno» e «serene col Sole sotto l'orizzonte»
  l'app dice «di buio nautico sereno», e senza ore «Nessuna ora di buio nautico sereno».

## Tutte le pagine -- Il file della pagina che non arriva (passo 6.17.1, 21/11)

- **Uno stato che le tavole non disegnano**: una pagina si scarica quando la si apre (passo 6.17);
  se il suo file non arriva due volte nel minuto, al posto della pagina c'e' l'`Avviso` di pagina
  della v58 con segno «!», «Questa pagina non si è caricata», «Può succedere se la rete si è
  interrotta o l'app è stata aggiornata.» e «Riprova», che ricarica l'app (testo di Marco 21/11).
  Il telaio resta. Prima: pagina bianca.
- **La finestra dell'oggetto** (dalla ricerca e dagli oggetti di *Le notti*): se il suo file non
  arriva, gli stessi testi stanno in una `Finestra` della v58, stretta, col segno «!», la x e
  «Riprova», sopra la pagina; si chiude con la x, Esc o fuori. Prima: non succedeva nulla.
- **Il primo avvio** (il file del Wizard): senza telaio, lo stesso `Avviso` sta nella colonna del
  primo avvio, come «non risponde» (`appErr`, Primo avvio.dc.html). Prima: pagina bianca.

## Meteo -- La pagina (passo 13, tavola v82, 23/11)

- **Il racconto della notte** (Meteo.dc.html 61-66, 462-499): fuori fino al passo 13.1 (eventi
  della notte dal backend, testi di Marco). Al suo posto i due fatti che la tavola mostra senza
  racconto (riga 511): il buio con le sue ore e la Trasparenza della notte.
- **Il campionamento dei setup** (righe 80-83, 440): fuori fino al passo 14 (seeing rispetto al
  pavimento del setup, ADR 0039); la tavola usa scale inventate.
- **Il Sole** (riga 187): «Sole non disponibile» come la tavola; «Meteo apre su» non si salva
  (gia' scritto sotto Impostazioni). I sette giorni del Sole al passo 46.11.
- **Il grafico a ore, non a quarti d'ora** (righe 337-338, 538): la tavola interpola le ore a 57
  punti; l'app disegna le ore che il backend scrive e il filo si sposta di un'ora (una lettura non
  calcola). Le fasce del crepuscolo invece sono al minuto, scritte con la previsione (`sky_bands`).
- **Il buio nautico** (riga 516, Oslo): dove manca il buio astronomico l'app conta il buio
  nautico (ADR 0035, 19/11, piu' recente della tavola) e lo dice: «Ore di posa nel buio nautico»,
  nei fatti «Buio nautico 22:10-03:20 · mai buio astronomico» (Marco 23/11). Senza nemmeno quello,
  il testo della tavola «col Sole sotto l'orizzonte», nei fatti «mai buio nautico» (testo nuovo).
- **«decide il verdetto»** (righe 53-54, 119): blocco che la tavola non riempie mai (`verdict:
  null`, riga 448): non portato; il verdetto sta nel numero grande.
- **«Non disponibile» di una misura**: vale il testo della pagina (riga 416, «Il servizio non ha
  mandato questa misura per la notte: torna col prossimo aggiornamento.») su quello del componente
  (CardMeteo.dc.html 63, «Non tutti i modelli danno la visibilità.»).
- **La Luna negli altri fattori**: «Luna» e accanto «al 55% dalle 23:00 · banda larga fino alle
  23:00», senza ripetere «Luna»; sotto il numero grande la frase intera della tavola.
- **Le ore nel dettaglio del telefono** (riga 142, scritte a mano 18 21 01 05 07): cinque ore a
  passo uguale fra le ore disegnate della notte.
- **La frase Copernicus** in inglese come la tavola (riga 86); prima l'app la traduceva.
- **Errore dell'app**: «AstroLog non risponde, riprova» con Riprova nella pagina, non nel telaio.
- **Ore e picchi con i minuti** (righe 375, 384): la tavola scrive «picco 40% alle 05» e «dalle 04
  alle 06»; l'app «picco 54% tra le 19:00 e le 20:00» e «dalle 19:00 alle 21:00», come la carta
  della Dashboard (CardMeteo v79, «picco 40% tra le 05 e le 06») e il resto dell'app (l'ora del
  posto sempre con i minuti): una forma sola per Meteo e Dashboard.
- **Condensa e temperatura: la minima, non la media** (righe 383, 386): il backend scrive il
  valore piu' freddo della notte (contratto meteo, «il freddo al suo minimo»), perche' la condensa
  si decide sull'ora peggiore; la riga sotto lo dice («minimo di temperatura meno punto di
  rugiada», «minima nel buio»).
- **La barretta delle ore fuori dal buio nella notte scelta** della striscia: grigia come le altre
  (`--carta-2`), non `rgba(inchiostro,.25)`; minuzia del componente Striscia, a Design se conta.
