# La navigazione -- contratto

Il **telaio** dell'app: la testa con le pagine, Altro, Stanotte, Da confermare, Cerca e
l'ingranaggio; sul telefono la testa e la bolla di vetro. La forma viene dalla tavola congelata
**Telaio v76** di Claude Design (`handoff/design/pagine/componenti/Telaio.dc.html`, con `Menu` e
`DaConfermare`), che vince sui contratti piu' vecchi (Marco, 27/10/2026); qui c'e' **dove va cosa**
e perche'. I nomi vengono da [`glossario.md`](glossario.md). Cio' che la tavola ha e l'app no sta in
`handoff/differenze-dalle-tavole.md`, sezione *Telaio*.

## Cosa chiede l'utente

Le prove del frontend si chiamano col loro titolo; stanno in `frontend/tests/scheletro.test.tsx`
(telaio e scansione), `stanotte.test.tsx`, `ricerca.test.tsx`, `veste.test.tsx` e
`navigazione.test.tsx`.

| richiesta | prova |
|---|---|
| Da qualunque pagina vedo dove sono e dove posso andare | *le pillole stanno nell'ordine di pagine.tsx, e la pagina aperta e' accesa*, *la testa dice la pagina e porta a Da confermare e a Cerca* |
| Le pagine meno usate stanno in Altro, coi loro sottotitoli | *Altro apre le quattro pagine coi loro sottotitoli, col fuoco sulla prima; le frecce girano* |
| Una voce senza pagina mi dice che arriva, invece di sparire | *una voce senza pagina apre la pagina che dice che sta arrivando* |
| Un indirizzo che non esiste me lo dice e mi riporta alla Dashboard | *lo dice, e porta alla Dashboard* (`navigazione.test.tsx`), *la Carta del cielo non e' piu' una pagina: vive nel Planner* |
| Vedo quante domande aspettano e arrivo alla sezione giusta | *la pillola dice quante domande aspettano e apre le sezioni con Rispondi*, *dalla barra si arriva a Da confermare, e l indirizzo cambia*, *quando il lavoro finisce, il conto si rilegge* |
| Scansiono dall'ingranaggio, e vedo quando e come e' andata l'ultima | *a riposo apre Scansiona con l'ultima scansione, e Tutte le impostazioni*, *l'ultima scansione senza file nuovi e con file non letti lo dice*, *premere Scansiona chiede di leggere TUTTE le cartelle* |
| Mentre lavora la vedo e la fermo da ogni pagina; interrotta la riprendo, bloccata so perche' | *in corso l'ingranaggio lo dice, e il menu porta fase, barra, file letti e Interrompi anche da un'altra pagina*, *la percentuale della barra e' quella del backend, non un conto suo*, *interrotta: il segno, l'ora, quanto ha letto e Riprendi*, *bloccata: dice perche', porta ai Dettagli e si fa ripartire*, *bloccata da una cartella persa: la colpa va alla cartella solo se la lettura e' caduta* |
| Cio' che non si e' potuto leggere me lo dice in testa alla pagina, e *Dettagli* porta dove si ripara | *le cartelle saltate si dicono, non si buttano*, *una cartella persa mentre la leggeva si dice in testa al corpo*, *Dettagli porta alle Cartelle solo quando il rifiuto e' delle cartelle* |
| La pastiglia mi dice da dove osservo e apre Stanotte; senza sito mi porta ad aggiungerlo | *dice Stanotte e il sito, e apre il pannello*, *senza sito porta ad aggiungerlo* (`stanotte.test.tsx`) |
| In Stanotte vedo il sito, la Luna con la sua frase per la banda larga e il meteo, con l'ora del sito | *dice la notte, il sito col suo cielo, la Luna e il meteo, con l'ora del sito*, *la Luna nel buio ... si dice*, *una Luna che non sorge lo dice a parole*, *un cielo mai dichiarato si legge, non sparisce*, *senza la previsione lo dice; una notte incerta e una senza ore di posa pure*, *un sito col fuso irriconoscibile si legge lo stesso, e dice cosa manca* |
| Sul telefono la bolla e' la pagina; toccata mi da' le cinque schede, Altro le altre | *la bolla chiusa mostra la pagina; toccata apre le cinque schede*, *una pagina fuori dalle cinque e' la sesta scheda*, *Altro apre le sette pagine e la scansione se c'e'; niente modo chiaro* |
| Cio' che apro si chiude con Esc o toccando fuori, e il fuoco torna dov'era | *Esc chiude il menu e riporta il fuoco su Altro; un clic fuori lo chiude*, *Esc chiude Stanotte e il fuoco torna alla pastiglia; un clic fuori la chiude* |
| Il corpo resta il contenitore delle pagine col foglio vecchio | *la testa e il corpo stanno nella colonna del telaio v76*, *il corpo e' il contenitore che le pagine col foglio vecchio misurano* (`veste.test.tsx`) |
| Se fermo e poi riprendo, riprende davvero | `test_resume_after_a_stop_reads_the_files_that_were_left` (`backend/tests/test_api_scan_all.py`) |
| Cerco un oggetto per ogni suo nome, anche quello comune, e vedo quanto ci ho ripreso | `test_an_object_is_found_by_any_of_its_names` (`backend/tests/test_search.py`, come le tre sotto) |
| Cerco una notte per data, come la scrivo, o per l'oggetto ripreso | `test_a_night_is_found_by_date_in_the_common_forms`, `test_what_is_not_one_of_your_dates_finds_no_night`, `test_a_night_is_found_by_the_object_shot_in_it` |
| Cerco un pezzo, un filtro o un sito per nome | `test_a_piece_and_a_filter_are_found_by_name_with_what_is_known_of_them`, `test_no_filter_is_not_a_filter_you_own`, `test_a_site_is_found_by_name_with_its_nights` |
| Il campo vuoto non apre niente; ogni gruppo dice quanti altri ce ne sono | `test_a_blank_search_finds_nothing_not_everything`, `test_each_group_says_how_many_beyond_the_few_it_shows` |
| Cerca sta nella testa (o con Ctrl K) e apre il campo | *chiusa e' un bottone, e toccata diventa un campo col fuoco*, *Ctrl K la apre da ogni pagina*, *aperta, il bottone Cerca lo dice; Annulla la chiude*, *sul telefono Cerca e' un tondo nella testa, e apre lo stesso campo* (`ricerca.test.tsx`, come le tre sotto) |
| Scrivo e vedo i trovati per gruppo, con frame e ore, o perche' le ore non ci sono | *mostra i quattro gruppi, ognuno con quante voci ha in tutto*, *un gruppo senza voci non si mostra*, *un campo vuoto non chiede niente alla rotta*, *niente trovato lo dice, e dice cosa si cerca qui* |
| Scelgo con le frecce e apro con Invio o col tocco; ogni voce apre la pagina che gia' la mostra | *le frecce scelgono e Invio apre*, *la voce ... apre la pagina che gia' la mostra* |
| Esc chiude la ricerca e il fuoco torna al bottone | *Esc chiude e riporta il fuoco al bottone*, *il menu aperto non ha difetti di accessibilita'* |

## Le decisioni

**Le pagine, in un posto solo** (`frontend/src/pagine.tsx`): sul desktop sei **pillole** --
Dashboard, Notti, Archivio, Progetti, Statistiche, Meteo -- e **Altro** con Piano della notte,
Planner, Selezione dei frame e Attrezzatura, ognuna col suo sottotitolo. Da confermare ha la sua
pillola, Impostazioni l'ingranaggio. La **Carta del cielo non e' una pagina**: vive nel Planner
(Marco, 10/11/2026). La prima pagina si chiama **Dashboard** (glossario del disegno).

**Ogni voce si vede, anche senza la sua pagina** (Marco, 7/10/2026): apre una pagina che dice che
sta arrivando (Progetti, Statistiche, Piano della notte, Planner, Selezione dei frame). I
**rimandi dentro le pagine** invece restano spenti finche' la pagina che aprirebbero non esiste.

**Impostazioni e' una pagina con dentro le sue sezioni** (Marco, 16/9/2026). Oggi in codice:
Cartelle, Sito, Luna, ASTAP, Servizi, Scansioni, Backup (`Impostazioni.tsx`); col porting Planner
(soglie, tempi della notte, automazione per postazione) e Diagnostica (ADR 0008). Ogni sezione ha
il suo indirizzo, in parole che l'utente legge (`/impostazioni/cartelle`); il tasto indietro
funziona e il collegamento si manda. **Tutto cio' che il primo avvio chiede sta anche in
Impostazioni** (Marco, 21/10/2026). **Servizi** tiene le chiavi in un posto solo. **Luna**: la
regola della Luna di tutta l'app, ING 25/65% dall'orizzonte, modificabile (`meteo.md`).

**Due fogli per tutto il passo 33** (Marco, 7/11/2026): il nuovo (`al-`, consegna v76) e il
vecchio (`as-`) finche' l'ultima pagina non e' portata. `main.tsx` importa prima il nuovo e poi il
vecchio, cosi' sul `:root` vincono i token del vecchio. Il telaio porta i token nuovi **solo dove
li usa** (la testa, i menu, Stanotte, la bolla, sotto `Tema`): il corpo resta fuori, perche' le
pagine col foglio vecchio sotto `data-modo` prenderebbero il suo `--inchiostro` e il suo `--linea`.
Il corpo (`.app-corpo`) e' il contenitore `telaio` che il foglio vecchio misura, e sul telefono
rimette i suoi bersagli da 44 px. Una pagina portata sta sotto `componenti/Pagina` (il suo `Tema`
e il formato) e mette le carte direttamente nella colonna del telaio.

**La testa del desktop** (Telaio v76): il logo, le pillole e Altro; a destra la pastiglia di
Stanotte, Da confermare, Cerca e l'ingranaggio. La pagina non ripete il suo titolo a schermo; per
chi usa un lettore di schermo il corpo porta un titolo nascosto.
- **Da confermare** dice il conto col battito della tavola e apre un pannello: il numero, e le
  sezioni con domande ("1 domanda", "N domande"), ognuna con *Rispondi* che apre la pagina su
  quella sezione (`/da-confermare#ancora`). Conti e sezioni arrivano da `GET /review`
  (`to_confirm`, `sections`). Sulla pagina Da confermare la pillola non c'e'.
- **La scansione** sta nell'ingranaggio, perche' **il lavoro sopravvive alla pagina**. Sul tondo
  un segno: l'anello che gira mentre lavora, "!" ambra interrotta o bloccata, e il nome lo dice
  ("Impostazioni · scansione in corso"). A riposo il menu ha *Scansiona* con l'ultima scansione
  ("ultima scansione {giorno}, {ora} · 214 file nuovi, nessun problema"; con file non letti
  "· 3 file non letti"; "nessun file nuovo"; Marco, 10/11/2026) e *Tutte le impostazioni*. Accesa,
  al posto di Scansiona c'e' il riquadro: titolo, fase, barra (la percentuale `pct` del backend),
  "file letti X su Y · ancora circa 1 h 20", e il gesto (*Interrompi*, *Riprendi*, *Riprova*);
  bloccata, anche *Dettagli* verso le letture, e il perche': la cartella solo se la lettura e'
  caduta, altrimenti "interrotta da un errore". Il verbo che si manda lo decide il backend
  (`action`). *Riprendi* dopo uno Stop torna a leggere le cartelle rimaste.
- **Cio' che la scansione non ha potuto fare** -- un rifiuto, una cartella caduta mentre la
  leggeva, le cartelle saltate -- e' una **riga di stato in testa al corpo**, con *Dettagli* che
  porta dove si ripara (Marco, 7/10/2026).
- **Cerca** apre il campo della ricerca (`Ricerca.tsx`), anche con Ctrl K (Cmd K sul Mac). La
  rotta c'e' (`GET /api/v1/search`): quattro gruppi, pochi per gruppo col totale. Gli oggetti col
  frammento dell'Archivio, le notti per data nelle forme comuni o per l'oggetto ripreso, pezzi e
  siti per nome. Una voce dice **chi e'** (chiave, id, genere), non l'indirizzo: le pagine stanno
  nel frontend. Un oggetto apre la sua **finestra** sopra la pagina dove sei (`archivio.md`). Il
  campo chiede dopo 250 ms dall'ultima lettera, mostra solo le voci del testo che c'e' scritto, e
  il fuoco resta nel campo (le frecce spostano `aria-activedescendant`; `combobox` sull'input,
  ARIA 1.2). La Cerca della v76 -- un dialogo al centro, coi gruppi delle pagine e delle
  impostazioni -- e' il passo dopo; fino ad allora il campo si apre sotto la testa, a destra, sopra
  la pagina: non allarga la testa.

**Stanotte** (pastiglia v70): la pastiglia dice "Stanotte" e il sito; senza sito "Aggiungi sito"
porta alle Impostazioni. Il pannello: "Stanotte · {giorno della notte}", tre righe -- il **sito**
(Bortle, "il sito predefinito", *Cambia ↗* verso i siti), la **Luna** (quanto e' illuminata e
quando sorge, e sotto la frase per la banda larga), il **meteo** (il verdetto col suo segno e le
ore di posa; sotto il buio e i tratti senza Luna) -- e i gesti *Apri il Meteo ↗* e *Piano della
notte ↗*. La frase della Luna viene dal gradino che il backend ha deciso (`moon_in_dark.level`,
ING 25/65) e da quando sta nel buio (Marco, 10/11/2026): "dopo le {da}", "fino alle {a}", "dalle
{da} alle {a}", "tutta la notte", seguito da "la banda larga è al limite" o, oltre, "consigliata
banda stretta"; sotto la soglia "la Luna non disturba la banda larga"; senza Luna nel buio "col
buio la Luna non c'è". Il sito si cambia nelle Impostazioni: la scelta coi bottoni dentro
Stanotte e' uscita (v70 vince).

**Sul telefono** la testa porta il logo, il titolo della pagina col sito (tocca e apre Stanotte
sotto la testa), Da confermare col conto e Cerca. In basso la **bolla di vetro**: chiusa e' la
pagina; toccata si allarga su Dashboard, Notti, Archivio, Meteo e Altro, e una pagina fuori dalle
cinque e' la sesta; mentre si scorre si richiude. Altro apre Progetti, Statistiche, Planner,
Piano della notte, Selezione dei frame, Attrezzatura e Impostazioni, con la scansione in testa
quando c'e'; il segno della scansione sta anche sulla scheda Altro. Telefono o desktop lo decide
`useFormato()`: `?formato=` prima, poi la finestra sotto i 700 px. I bersagli sono da 44 px.

**Cio' che si apre si chiude come tutto il resto**: un menu alla volta; Esc chiude e riporta il
fuoco a chi l'aveva aperto, toccare fuori chiude, le frecce girano fra le voci di un menu, e un
menu appena aperto porta il fuoco alla sua prima voce. Cambiare pagina chiude tutto.

**Il tema** (Marco, 17/10/2026): modo Chiaro, Scuro, Automatico e cinque accenti, nel primo avvio
e in Impostazioni. Il tondo del modo nella testa e "Modo automatico" nell'ingranaggio arrivano col
passo Tema, quando tutte le pagine sono nel foglio nuovo (Marco, 10/11/2026).

**La Dashboard** (Marco, 15-16/10/2026): il tempo che manca alla scansione si stima dal ritmo
finora della cartella in lettura, si dice "circa" e tace nel primo minuto; "prima scansione"
vuol dire che il gesto legge almeno una cartella mai letta fino in fondo.

## Cosa NON fa

Non decide come le pagine sono fatte dentro: ogni pagina ha il suo contratto. Non calcola niente:
cio' che il telaio mostra -- il conto e le sezioni da confermare, la fase e la percentuale del
lavoro, l'ultima scansione, il sito, la Luna e il suo gradino, il buio -- arriva pronto dall'API.
Non ha ancora il tondo del modo, la Cerca in dialogo, la lingua al volo ne' il tuo nome.
