# La coda

Cosa resta da fare, e in che ordine. Si riscrive, non si appende: quando un punto e' fatto
sparisce, e la storia sta in git. Una voce dice **cosa non va, dove, la misura e il rimedio**, e si
ri-misura prima di aprirla. Una voce si cita con la sua frase, mai col numero. Le decisioni non
stanno qui: quelle di un dominio nel suo contratto (`domini/`), le altre in un ADR (`adr/`).

## Il piano

### Misura del metodo (fino al 19/10/2026)

ADR 0015: per ogni lavoro una riga, poi il confronto col giro vecchio (2-6 M token per lotto).
Token dai risultati di Workflow e agenti; difetti = rilievi bloccanti confermati.

| Data | Tipo | Lavoro | Token | Minuti | Difetti |
|---|---|---|---|---|---|
| 6/10/2026 | costruisci | S1, una scheda per firma | ~0,5 M agenti (workflow 0,41 + sviluppatore 0,09), sessione principale non contata | 78 workflow | 2 bloccanti dal giro (ottica persa rispondendo la camera; "a colori" con la camera della notte) + 1 mio dopo (falso avviso nel log) |
| 6/10/2026 | costruisci | S3, una scheda per gruppo di frame | ~0,68 M agenti (workflow 0,50 + due sviluppatore 0,18), sessione principale non contata | 67 workflow | 2 bloccanti dal giro (il "non e' un oggetto" di un gruppo scavalcava un cielo arrivato dopo; cambiare idea non riportava i frame legati dal gruppo) + import-linter rosso |
| 6/10/2026 | costruisci | S4, Applica scrive solo le risposte | ~0,34 M agenti (workflow, 7 agenti), sessione principale non contata | 36 workflow | 1 bloccante dall'audit (rispondere "e' giusto" a un dubbio non lo chiudeva) + 1 della guida (paragrafo sugli oggetti visti) + registro dei test tolti |
| 6/10/2026 | costruisci | S2, risposta senza nome sui frame | ~0,26 M agenti (workflow, 7 agenti), sessione principale non contata | 58 workflow | 2 bloccanti dal giro (risposta vecchia su un frame mancante; test di fondazione rosso) |
| 6/10/2026 | rifattorizza | S5, il segno lo tiene SQLite | sessione principale sola, nessun agente | ~40 | 0 dalla revisione (nessuna: la prova copre); 1 mio (import-linter vieta `db` -> `spine`, strada cambiata da trigger TEMP a schema) |
| 7/10/2026 | costruisci | Telaio v28 (ADR 0018) | ~0,86 M agenti (workflow 0,55 + due sviluppatore 0,31), sessione principale non contata | 17 workflow | 1 bloccante dall'audit (bloccata senza modo di ripartire) + 5 piccoli chiusi da me + 3 colori del foglio corretti da Design (v28) |
| 7/10/2026 | costruisci | M4, Archivio per periodo, sito, ottica, camera | ~0,35 M workflow (6 agenti), sessione principale non contata | 39 workflow | 2 bloccanti dall'audit (date non battibili da tastiera; docstring oltre 2 righe) + 1 mio dopo (valore storto nell'indirizzo = 422) |
| 7/10/2026 | costruisci | M5, backup delle risposte (ADR 0017) | ~0,49 M workflow (8 agenti), sessione principale non contata | 47 workflow | 2 bloccanti dal giro (DB ricreato prima dell'avvio non proposto; percorso di ASTAP nell'Esporta) + 5 piccoli chiusi da me |
| 7/10/2026 | costruisci | M2, la cartella ora sta qui | ~0,46 M workflow (5 agenti), sessione principale non contata | 28 workflow | 0 bloccanti; 8 piccoli parcheggiati (3 dello schermo da riparare subito) |
| 6/10/2026 | costruisci | Focale misurata dal cielo (ADR 0016) | ~0,31 M workflow (6 agenti) + esploratore 0,09, sessione principale non contata | 76 workflow | 1 bloccante dal giro (il frame rimandato aspettava il giro dopo) + 3 piccoli chiusi da me |
| 6/10/2026 | ripara | Meno frame in coda dopo filtro e unione: provato e tolto | ~0,48 M agenti (sviluppatore, due revisori) | ~60 | 3 bloccanti dai revisori (corredi diversi via gruppi di focale); trovato un difetto vero, ora in coda |
| 6/10/2026 | ripara | Risposte sul tipo: 100 in un Applica da 12,8 s a 0,29 s | sessione principale + un revisore (~0,1 M) | ~50 | 0 dal revisore (200 semi di prova a caso, 0 differenze) |
| 6/10/2026 | rifattorizza | Fase 2, lotto 6b: `api` resto, fase 2 chiusa | ~0,27 M agenti (uno sviluppatore), sessione principale non contata | 23 agente | 0 |
| 6/10/2026 | rifattorizza | Fase 2, lotto 6a: `api` Da confermare e Attrezzatura | ~0,21 M agenti (uno sviluppatore), sessione principale non contata | 16 agente | 0 |
| 6/10/2026 | rifattorizza | Fase 2, lotto 5e: `spine` Notti e Archivio, indice, Da confermare | ~0,24 M agenti (uno sviluppatore), sessione principale non contata | 23 agente | 0 |
| 6/10/2026 | rifattorizza | Fase 2, lotto 5d: `spine` oggetti e mosaici, Applica una lettura | ~0,32 M agenti (uno sviluppatore), sessione principale non contata | 38 agente | 0 |
| 6/10/2026 | rifattorizza | Fase 2, lotto 5c: `spine` attrezzatura | ~0,35 M agenti (uno sviluppatore), sessione principale non contata | 27 agente | 0 |
| 6/10/2026 | rifattorizza | Fase 2, lotto 5b: `spine` solve, identify, group | ~0,29 M agenti (uno sviluppatore), sessione principale non contata | 22 agente | 0 |
| 6/10/2026 | rifattorizza | Fase 2, lotto 5a: `spine` scansione, normalizzazione, stadi | ~0,29 M agenti (uno sviluppatore), sessione principale non contata | 25 agente | 0 |
| 6/10/2026 | rifattorizza | Fase 2, lotto 4: file sciolti e `worker` | ~0,19 M agenti (uno sviluppatore), sessione principale non contata | 15 agente | 1 mio sul resoconto (un fuso non valido cambiava esito: rimesso com'era) |
| 6/10/2026 | rifattorizza | Fase 2, lotto 3: `weather` | ~0,21 M agenti (uno sviluppatore), sessione principale non contata | 17 agente | 0 (la prova copre; confronto byte per byte delle tabelle del meteo) |
| 6/10/2026 | rifattorizza | Fase 2, lotto 2: `ephemeris` | sessione principale sola | ~35 | 0 |
| 6/10/2026 | rifattorizza | Fase 2, lotto 1: macchina dei nomi, `db`/`fits`/`catalog`/`vocab` | ~0,18 M agenti (uno sviluppatore), sessione principale non contata | ~70 | 0 (nessun revisore: la prova copre); 1 regola dei commenti presa dal commit |

### Prima delle funzioni nuove

Deciso con Marco: nessuna funzione nuova finche' non e' sistemato cio' che c'e'. La fase 1
del refactor e' fatta (sotto); poi le prime due *Tappe del prodotto*, nell'ordine di
*Semplificare e completare la spina*. La spina si
giudica dominio per dominio con una domanda sola: dice il vero, regge e risponde in tempo? I FITS
veri di ASIAIR li ha Marco; di Voyager e SGP servono frame di un altro utente (*Mancano Voyager e
SGP*).

Il Parcheggio non entra: un debito si chiude quando si tocca il codice dove sta. **Dopo cinque o
sei funzioni nuove si misura il metodo**: difetti presi dalla revisione contro difetti scappati e
trovati da Marco usando l'app; se la revisione prende poco si alleggerisce, se scappa troppo si
stringe.

### Il refactor del backend

Si lavora **package per package**, e nessuna delle due fasi cambia il comportamento. Il frontend
non entra: lo rifa' Marco col disegno nuovo (*Per il disegno nuovo*, sotto).

**Fase 1 -- pulizia e tipi.** Commenti al massimo due righe e solo il perche'; ogni funzione
annotata; il glob `ANN` di `ruff.toml` copre tutto `backend/astrolog`.
- Fatti: tutto `backend/astrolog`.
- Da chiudere strada facendo: 20 righe del backend (6 in `backend/astrolog`, 14 in
  `backend/tests`) passano i 100 caratteri dietro un
  `# noqa: CODICE - ragione` (che zittisce anche la lunghezza) o un `# pyright: ignore`: la
  ragione va sopra la riga. Dicono ancora "posa" e "luogo" dove il glossario dice "frame" e
  "sito": commenti, docstring e prove di `backend/tests`, i commenti di
  `backend/astrolog/schema.sql` e due messaggi di log
  (`spine/identify`, `spine/stage_run`). Due rimandi a
  `docs/coda.md` puntano a decisioni che ora vivono altrove: `tests/test_gear_instruments.py` va
  a `docs/domini/spina.md`, *Le schede*;
  `.pre-commit-config.yaml` (i quattro software) va a `CLAUDE.md`, "Software supportati".
  Annotare `gear_create` ha lasciato un `cast` in
  `normalize._filter_for`: il filtro che non dice niente esce prima, ma `normalize_filter` torna
  `str | None`; lo toglie un ritorno anticipato che il tipo veda. Annotare `objects` ne ha
  lasciato un secondo in `objects.stable_key`: lo slug o il nome mostrato, mai `None` perche' un
  oggetto fuori catalogo ha sempre un primario (`docs/domini/spina.md`, invariante 3), ma
  `display_name` torna `str | None`; lo toglie una riga d'oggetto tipata che dica l'invariante.
  Il `cast` di `settings._solver` resta: `SolverSource` ripete `astap.Source` come `Literal`
  apposta (`models_tonight`).

**Fase 2 -- semplificare**, sul codice gia' pulito: doppioni uniti, nomi interni in inglese, `dict`
che escono dal package -> `dataclass`, insiemi chiusi -> `StrEnum`, funzioni lunghe spezzate e i
`noqa` su `C901`/`PLR` tolti, file piccoli accorpati, e le voci di *Efficienza, misurata* e
*Doppioni* del package toccato (Marco, 6/10/2026). Si va dalla base in su: `db`, `fits`,
`catalog`, `vocab`; `ephemeris`, `weather`, i file sciolti; `spine`; `api`. Un lotto per
package: prima i nomi, poi doppioni e tipi, poi efficienza e file. **I lotti sono finiti**, `api`
compreso. Della fase 2 resta solo il debito qui sotto: cio' che cambierebbe una firma usata fuori,
una forma di risposta o un esito (quindi non e' un refactor), e le righe ancora `dict` che
aspettano chiamanti tipati. Si chiude quando si tocca il codice dove sta:
- **I nomi interni in italiano**: fatti tutti in `backend/astrolog` (`tools/nomi_italiani.txt`
  vuoto); un nome nuovo lo ferma `tools/nomi_inglesi.py` al commit. Restano in italiano, perche' arrivano nel corpo di una risposta, nel log o in nessun posto, i
  messaggi dei validatori di `models_review_apply` (il 422), delle eccezioni di `review_write*`,
  `lookalike` e `instrument_answer`, e le righe di log.
- **`identify`, dopo il terzo lotto di `spine`**: il wcs resta `dict[str, Any]` (la geometria
  legge con `.get`, e `mosaic` e i test passano dict senza i lati: *Mosaici, dichiarazioni e
  archivio* nel Parcheggio). `identify_link._name_it` ha un `cast` sul nome libero della
  decisione: una decisione senza voce di catalogo ha sempre il nome (`decide`, `_towards`), ma
  `Decision.name` e' `str | None`; lo toglie una decisione che dica col tipo "slug o nome".
  `api/settings._missing` fa `cast` a `Missing` di `GroupReason.NO_ACTIVE_SITE` e
  `solve.NO_STAR_DATABASE`, che resta: il `Literal` ripete apposta (`models_tonight`).
  `solve.NO_SOLVER` resta una stringa: il suo insieme e' `Missing`, che mescola parole di
  `group` e `solve`, e un `StrEnum` comune non ha una casa negli stadi.
- **`db/idlist.grouped` torna `dict[Any, list[Any]]`**: generico in `T` rompe `api/archive.py`, che
  passa i dict di `spine/filters_used` a un campo `list[FilterUsed]`. Si fa generico quando i
  chiamanti costruiscono righe tipate.
- **Insiemi chiusi da fare `StrEnum`**, che escono dal package (fatti tipo del frame, software e
  bande, fasi della Luna e fasce del cielo, meteo, `net.Failure`, stati del worker, motivi e
  canali di `astap`, fonti di `place`, esiti e motivi della scansione, marchio di riscrittura,
  nomi e stati degli stadi, soggetti del conto, motivi di `group`, risposte sul tipo, metodi,
  fiducie, rami e motivi di `identify`; soggetti dell'uso, campi dei corredi, risposte sul filtro,
  tipi di camera, risposte sul mosaico, tipi di entita'; tipi del bersaglio di una risposta e
  vuoti del cielo, `object_answer.TargetKind` e `objects.SkyVoid`; `nights.AnswerAt` e
  `archive.Order`). In `weather` restano stringhe i generi di
  riga (`forecast.KIND`, `history.KIND`) e le fonti per modello (`forecast.source_of`), aperte
  quanto la scelta dei modelli. Dentro l'SQL restano scritti a
  mano tipi di entita' e soggetti dell'uso (`'rig'`, `'instrument'`; `'filter'` in
  `spine/inventory.py`): li tiene il `CHECK`, che una prova lega all'enum.
- **Attrezzatura, dopo il quarto lotto di `spine`**: restano `dict` le schede di
  `gear.camera_specs` (spalmate nelle righe di `inventory` e `api/lookalike`), le righe di
  `filters_used.of` (vanno nel `list[FilterUsed]` di `api/archive` e in `nights`: vedi
  `idlist.grouped` qui sotto) e le schede di `signature_page` (le riempie `objects.subjects`,
  comune a `unnamed` e `typeless`); `rigs.rigs_with_keys` passa `sqlite3.Row`.
- **Fra i `noqa: PLR0913`**, questi restano perche' toglierli cambia una firma usata fuori:
  `replace_rows` (`db/replace_table.py`), `walk_dir` (`fits/walk.py`, i sei accumulatori in un oggetto solo),
  `create_app` (`api/app.py`, sei opzioni a parola chiave lette da `__main__`, `tools` e test),
  `scan_store.finish_run` e `upsert_position` e `normalize_rig.mount_for_frame` (chiamati dai
  test), `stages.set_status` e `stage_run.frame_safely` (chiamati da ogni stadio),
  `rigs.rig_for` (`normalize_rig`), `gear.declare_filter` (`gear_create`, `api/review_write`),
  `gear_create.filter_declared` (`api/gear_write`), `declarations.write_declaration` e
  `declare_instrument_spec` (chiamati da molti moduli), `unnamed.declare` (`api/review_write_folders`
  e i test, a parola chiave).
  `identify_link.hang` resta per un'altra ragione: togliere `counts` vuol dire contare dopo le
  scritture, e un frame che cade a meta' cambierebbe i conti della ricevuta.
  `archive_page` (`api/archive.py`) resta per un'altra ragione: i suoi otto parametri sono la
  query della rotta, e raccoglierli in una dipendenza di FastAPI e' un cambio di forma (fase 2).
- **Oggetti e mosaici, dopo il quinto lotto di `spine`**: restano `dict` le righe d'oggetto di
  `objects.by_key`, `listing`, `identities` (`o.*` largo; `display_name` e `stable_key` le leggono
  anche da `sqlite3.Row` in sei moduli di altri lotti: il `cast` di `stable_key` aspetta loro),
  `objects.counted` (va in `idlist.grouped`) e i soggetti di `objects.subjects`, scritti nei
  dizionari dei gruppi di `signature_page` e `coordinates`. I cinque `mosaic*` restano file: la
  geometria e' pura e le proposte sono un lettore, ognuno col suo contratto in `pyproject.toml`;
  `mosaic_weight` porta una soglia con la sua fonte, citata da `domini/mosaico.md`, e
  `mosaic_describe` un'altra regola (centro e nome).
- **Notti e Archivio, dopo il sesto lotto di `spine`**: restano `dict` le righe, i totali, le
  scelte e i pannelli di `nights` e `archive`, che vanno dritti nei modelli della rotta; le righe
  di `archive.page` le leggono anche `objects.stable_key` e `display_name`.
- **Doppioni piccoli dei package di base**: `catalog/load.load_catalog` riscrive a mano
  `db.transaction` (gli strati non gli lasciano importare `db`: resta).

### Tappe del prodotto

La spina onesta **su un archivio qualunque**, poi si alleggerisce, poi `measure`. Le tappe si
nominano col loro nome, per non confonderle con le fasi del refactor.

1. **La spina.** `scan`, `normalize`, `solve`, `identify` e `group` sono costruiti e misurati
   sull'archivio vero ([`domini/spina.md`](domini/spina.md)); il catalogo e' portato
   ([`domini/catalogo.md`](domini/catalogo.md)); il sito c'e' ([`domini/sito.md`](domini/sito.md));
   delle effemeridi ci sono la Luna e il buio ([`domini/effemeridi.md`](domini/effemeridi.md)).
   Finche' ASTAP non e' installato i frame non hanno oggetto, ed e' voluto. Resta da chiudere
   *Da riparare*, sotto, fino alle macchine che non guardano.
2. **Alleggerire**: i guadagni della sezione efficienza, coi numeri gia' misurati, poi i doppioni
   insieme alla fase 2 del refactor.
3. **`measure`**: contratto e posto nei contratti dei moduli, poi eccentricita', fondo cielo,
   tilt ([ADR 0007](adr/0007-metriche-con-sep.md)). Dopo la spina e l'alleggerimento apposta: su
   una catena con difetti muti misurerebbe la qualita' con dati che mentono. Planner e Progetti
   vengono dopo, quando il cuore e' a posto.
4. **Il prototipo del pacchetto desktop**, prima che costi
   ([ADR 0004](adr/0004-pacchetto-desktop-tauri.md)).
5. **Le pagine.** Esistono Casa, primo avvio, Da confermare, Archivio, Notti, Attrezzatura, Meteo e
   Impostazioni, con la guida utente; lo scheletro e' in
   [`domini/navigazione.md`](domini/navigazione.md), e una voce compare nella barra solo quando
   la sua pagina esiste. Marco le ridisegna tutte con Claude Design
   ([ADR 0012](adr/0012-il-disegno-viene-da-claude-design.md)): cosa devono saper fare sta in *Per
   il disegno nuovo*. Restano da fare le misure dei frame nelle Notti, il **modale**
   dell'oggetto (lo stesso per notte, oggetto e libreria, a pagine fatte), l'etichetta dei
   progetti nell'Archivio, e la Casa per ultima.
6. **Le effemeridi che mancano**: gli orari del Sole come numeri e le ore di buio, quando una
   schermata li chiede; **quanto sale un oggetto stanotte**, dalla cava
   (`old/backend/astrolog/ephemeris/`), col Planner.
7. **Il Planner, i progetti e il piano della notte**
   ([ADR 0013](adr/0013-progetti-e-piano-della-notte.md)): i progetti con l'inquadratura su
   Aladin Lite v3 ([ADR 0005](adr/0005-carta-del-cielo-aladin-lite.md)), la pagina delle
   sequenze col wizard della serata e la linea del tempo, l'export per N.I.N.A. Prima i DSO, poi
   esopianeti, variabili, occultazioni e campagne AAVSO, poi supernove e transienti, per ultimi
   comete e NEO. Poi la **Carta del cielo**.
8. **Il pacchetto**: immagine Docker con ASTAP dentro, multi-arch su runner arm64 nativi; su
   Windows e Mac l'app desktop con installer e updater firmati
   ([ADR 0003](adr/0003-astap-per-tutti.md), [ADR 0004](adr/0004-pacchetto-desktop-tauri.md)).
9. **Il mobile**, per ultimo, a desktop funzionante: tablet e telefono, su ogni pagina.

### Semplificare e completare la spina

Da una lettura critica del disegno (giudizi, non misure: si misurano prima di costruirli).
**S1-S4 decise da Marco: si fanno**, prima della fase 2
([ADR 0014](adr/0014-da-confermare-semplificata.md)); S5 si decide misurandola.

- **S1 -- fatta** (5/10/2026): una scheda per firma dell'header (`spine/signature.py`), che
  chiede camera, ottica e filtro, solo le parti che mancano; l'eredita' dalla notte resta
  automatica (Marco). La grafia che l'ASIAIR scrive come montatura non entra nella firma. Si perde
  anche l'unione di due camere che portava la risposta sul filtro: ogni grafia ha la sua. La
  scheda a schermo aspetta il disegno (*Per il disegno nuovo*).
- **S2 -- fatta** (6/10/2026): l'oggetto dei frame senza nome si scrive sull'impronta di ogni
  frame del gruppo (`declarations`, tipo `frame`); la risposta del gruppo e' quella che i suoi frame
  portano, cosi' vale per chi arriva dopo. `home_nights` risceglie solo il gruppo, non trasporta
  risposte. Si perde il frame arrivato dopo la risposta che il fuso nuovo porta in un gruppo senza
  frame risposti.
- **S3 -- fatta** (6/10/2026): una scheda per gruppo di frame (`ObjectCard`) al posto di Oggetti
  e Senza nome: un oggetto trovato o un gruppo senza nome, coi candidati del cielo (anche zero) e
  una risposta sola. *Non e' un oggetto* vale anche su un oggetto trovato (Marco): si scrive
  sull'impronta dei frame, `identify` lo legge prima del cielo e tiene cio' che aveva trovato in
  `frames.found_key`, che tiene la scheda. La scheda a schermo aspetta il disegno.
- **S4 -- fatta** (6/10/2026): Applica scrive solo le risposte; un oggetto si chiede solo col
  dubbio (`low`), non se il cielo lo riconosce ne' se l'header scrive una sigla del catalogo senza
  cielo (`high`, Marco). Spariti `seen` e la dichiarazione `confirmed`, e con loro l'avviso degli
  oggetti nuovi.
- **S5 -- fatta** (6/10/2026): il segno "aspetta il tipo" lo riscrivono i trigger di
  `schema.sql` (vista `frame_waits`) a ogni scrittura di un ingresso, al posto di
  `refresh_waiting` chiamato a mano in sette punti. Misurato su 20.000 pose: costo uguale
  (scansione 12,0 s contro 12,5; una risposta 74 ms contro 85). Ora lo muove anche chi scrive
  senza passare dagli aiutanti (una risposta tolta, un cielo cancellato).
- **Il telaio -- fatto** (7/10/2026, ADR 0018): tutta l'app nel telaio v28 di Claude Design.
- **Il Meteo nel disegno nuovo -- fatto** (7/10/2026, cinque commit). Prima il backend, allineato alle decisioni del Meteo
  in `docs/DECISIONI.md` del progetto di disegno (Marco, 3/10/2026), che superano parti di
  `docs/domini/meteo.md`: 7Timer esce (il seeing solo da Meteoblue, niente trasparenza a fasce);
  il semaforo lo decidono solo le nuvole, le altre misure "pesano" con parola e ora; soglie e
  giudizio ora per ora mandati dal backend; ore serene come intervallo e conto ("dalle 23 alle 04,
  4 ore"), mai minuti; vento a 250, 700 (contro il solito del sito) e 200 hPa, polvere. Ogni
  soglia del disegno si verifica su una fonte pubblica. Poi la pagina, gia'
  nel foglio v28 (`47-parametro`, `50-strato`, `63-cielo`, `64-scala`, `71-pagina-meteo`).
  Fetta 1 fatta (7/10/2026): 7Timer uscito, seeing solo Meteoblue (`seeing_arcsec`). Fetta 2
  fatta (7/10/2026): giudizio per misura (`weather/judge.py`, soglie con fonte in
  `docs/domini/meteo.md`), notti pronte in `weather_view`. Fetta 3a fatta (7/10/2026): la pagina
  nel foglio v28 -- testa, fila delle notti, scheda, pesano, carte con le barrette, tendenza, stati;
  "jet stream" e non "corrente a getto" (Marco, glossario). Fatta anche la 3b-ii (7/10/2026): il cielo delle nubi con la
  scala di destra e il lettore; le carte portate a un'ora col tocco e con le frecce. Lo stato "il
  servizio tace ma la previsione vale" e' fatto (3b-i, 7/10/2026: l'ultimo tentativo della
  previsione sta in `weather_fetches`). Resta per la veste del telefono: il cielo si stringe col
  viewBox (1080 di largo) e le scritte rimpiccioliscono, mentre il disegno ne ha uno da 358 con
  un'ora si' e una no. Da portare a Claude Design nella prossima consegna: le barre della pioggia
  nel cielo col colore del giudizio (oggi il foglio le riempie sempre di rosso); il giudizio lungo di
  una carta ("incerta dalle 21:00, niente dalle 22:00") esce dal bordo a larghezza desktop; nel
  generatore `meteo.js` la parola della prima ora sulla scala di destra non si scrive mai (il
  controllo delle sovrapposizioni parte da G+4 e la prima parola sta a G+3).
- **La ricerca nella barra -- prossima** (decisa con Marco, 7/10/2026): trova oggetti, notti,
  attrezzatura e siti dell'archivio, da ogni pagina; non le pagine dell'app, che il binario ha gia'.
  Un oggetto si trova per ogni suo nome (anche il nome proprio, "Andromeda") e si mostra sempre col
  nome di catalogo ("M 31 · Andromeda"), come vuole il glossario. I risultati stanno in un menu
  a discesa sotto il campo, divisi per tipo, poche voci per tipo, con frecce e Invio. Un risultato
  apre la pagina che gia' lo mostra: l'oggetto l'Archivio ristretto a lui, la notte le Notti su
  quella notte, un pezzo la sua scheda in Attrezzatura, un sito il sito nelle Impostazioni; nessuna
  pagina nuova. Una notte si trova per data, nelle forme comuni ("25/9", "2026-09-25", "25
  settembre", "settembre 2026"), o per l'oggetto ripreso: "M31" mette nel gruppo Notti anche le
  notti di M 31 (Marco, 7/10/2026). Oggi solo l'Archivio si apre da indirizzo (`/archivio?q=`):
  Notti, Attrezzatura e il sito nelle Impostazioni vogliono il loro parametro. Fette: (1) le pagine
  che si aprono su una voce dall'indirizzo, (2) la rotta `GET /api/v1/search`, (3) il campo nella
  barra dopo il disegno (brief dato a Marco il 7/10). Fetta 1 fatta (7/10/2026): `/notti?notte=<id>`,
  `/attrezzatura?pezzo=strumento-<id>` o `filtro-<id>`, `/impostazioni/sito?sito=<id>`. Fetta 2 fatta (7/10/2026): `GET /api/v1/search?q=`
  (`docs/domini/navigazione.md`); una voce dice chi e', non l'indirizzo, e l'oggetto apre
  l'Archivio con `?key=` (la rotta lo sa gia'). Fetta 3: il campo, che compone gli indirizzi, e
  l'Archivio che legge `?key=` e mostra a schermo che e' ristretto a un oggetto. Restano dalla
  revisione della fetta 2: le notti cercate per oggetto usano il frammento, quindi "M 1" porta anche
  le notti di M 10 e M 101, e non trovano un mosaico per il nome dato dall'utente
  (`spine/search._NIGHTS_WHERE`); mese e anno solo in cifre ("05/2024", "2024-05") non sono una data.
- **I filtri in un ordine solo, in tutta l'app -- fatta** (Marco, 7/10/2026): Notti, righe e
  tendina dell'Archivio, Attrezzatura, "uno dei miei" in Da confermare
  (`vocab/filters.DISPLAY_ORDER`, `docs/domini/notti.md`). Resta per ore la sezione Filtri di Da
  confermare: sono domande, e le piu' usate prima e' l'ordine del lavoro. `gear_usage.position`
  dei filtri si scrive ancora ma nessuno la legge piu' (`spine/gear_usage.py`): da togliere.
- **Le pagine a Claude Design, una alla volta** (Marco, 7/10/2026): Notti (fatta l'8/10, disegno arrivato il
  7/10, forma A, il registro), poi Archivio, Da confermare, Attrezzatura. Il brief di ognuna si
  scrive coi dati che l'API manda in quel momento: si rifa' la ricognizione quando tocca a lei.
  I tre dati che la pagina Notti chiedeva li manda gia' `/api/v1/nights` (7/10/2026: `untimed`
  per oggetto, `weather.arrives_on`, `reading_done_pct`). Notti montate sul foglio v29 (8/10/2026,
  forma A, il registro). Resta: il vuoto del disegno e' una frase e un'azione, il mattone `Vuoto`
  dell'app scrive ancora titolo e disegno (classi in attesa): si allinea quando il disegno passa a
  un'altra pagina che lo usa. In una notte con tempo, un filtro i cui frame non dicono la durata pesa zero nella barra
  e resta solo lo stacco minimo (lo nomina la legenda): da chiedere al disegno se basta.
- **Un colore per banda -- fatta** (Marco, 8/10/2026): foglio v30, una classe per ognuna delle 17
  bande, le doppie e multiple come strisce delle loro righe (`FiltriUsati.VARIANTE`).
- **M4 -- fatta** (7/10/2026): l'Archivio stringe per periodo (anno o date), sito, ottica e
  camera, e la riga dice solo le pose che passano (`counts.Scope`, `docs/domini/archivio.md`).

L'ordine: le prove che mancano e *L'archivio dice cose false*; poi S1-S4, prima delle
velocita' che toccano gli stessi pezzi (Applica, fuso di casa, riletture in `row_of`), che con
S1 e S2 spariscono in parte; poi la fase 2 del refactor, con le velocita' e i doppioni che
restano; poi M5, M4 (Marco, 6/10/2026: M1 e M3 non servono, M3 sta fra le *Idee*).

## Da riparare, nell'ordine

Prima cio' che rompe, poi cio' che fa dire all'archivio cose false, poi le macchine che non
guardano, poi efficienza e doppioni.

### Rompe

Niente di aperto.

### L'archivio dice cose false, e non si vede

- **Le ore restano doppie quando ne' il grezzo ne' la copia portano un nome che l'app conosce.**
  Se la copia non dice di essere calibrata e il vocabolario non riconosce nessun software nel suo
  header, due nomi diversi possono essere due programmi o due grafie dello stesso: a pari indizi i
  gemelli contano tutti e due. Colpisce chi riprende con un programma fuori dai quattro ed elabora
  con un altro. Rimedio: una domanda in Da confermare, per gruppo, **quale dei due file e'
  l'originale** (il disegno nuovo deve saperla in arrivo). Nello stesso posto tre case si
  contraddicono: `tests/synthetic.py` fa scrivere `SWCREATE` ai profili di Voyager e SGP, mentre
  `tests/test_fits_header.py` e `tests/test_normalize_rewrite.py` dichiarano `PROGRAM` e
  `SWMODIFY`; nessuna e' verificata finche' non arrivano header veri.
- **Due limiti dei file solo online.** Sul Mac elencare una cartella solo online ne scarica
  l'elenco (TN3150, Apple), mai provato su un Mac, e costa una `lstat` in piu' a FITS. Un frame gia'
  in archivio lasciato poi solo online non si riapre in scansione, ma `solve` lo leggerebbe per
  intero. Il segno di Windows non si e' visto su un file vero.
- **Da misurare su un NAS vero** quanto aspettano registrazione e conta di una cartella di rete che
  non risponde: risolvere il percorso e chiedere se risponde vengono prima del tetto della conta
  (`api/folders.py`, `PROBE_SECONDS`) e non ne hanno uno (una sonda con due attese finte da 2 s ha
  risposto in 4 s col tetto a 0,5). `GET /folders` invece le chiede tutte insieme sotto quel
  tetto.
- **Due file troncati con l'header identico diventano un frame solo**: senza pixel da leggere
  l'impronta ripiega sull'header (`fits/header_read.frame_fingerprint`). Provato su cinque
  troncati sintetici; con header veri, che differiscono almeno per `DATE-OBS`, e' improbabile ma
  nessuna prova lo esclude.
- **Il corredo di un frame dipende da quando e' stato letto**: `normalize` sostituisce la focale
  con la mediana del suo gruppo (`focal_buckets`), calcolato sui soli frame del giro, e
  `rigs.find_rig` prende il primo corredo entro la tolleranza. Tre scansioni in tempi diversi
  (CamK 1060, poi 1000, poi 1010) lasciano il frame a 1000 su un corredo suo; rifatti insieme
  finiscono tutti sul corredo a 1060. Lo stesso archivio, letto in un altro ordine, conta le ore su
  corredi diversi. Prova riprodotta il 6/10 (scratchpad `cx1`). Dalla focale misurata (ADR 0016)
  vale solo per i frame senza cielo: le misure di un treno ottico stanno nello 0,3 %, e restano a
  cavallo del 5 % solo le focali scritte a mano. Rimedio se un utente lo incontra: gruppi su tutti
  i frame della stessa camera e ottica, non su quelli del giro.

### Macchine che non guardano

- **Promesse con la prova a meta', o senza.** Delle tabelle *Cosa chiede l'utente* dei contratti,
  ogni prova nominata esiste e passa, ma alcune righe sono provate a meta' o senza prova. Le
  peggiori: **un pezzo scritto a mano e poi nominato dai file** non deve diventare un doppione con
  le ore spartite (nessuna prova; la riga di `attrezzatura.md` cita il verso opposto); **una
  correzione sulla scheda resiste a una nuova lettura** e' provata per pixel e colore della camera, non per gli altri
  campi. Piu' piccole: il catalogo ("le ore non si
  sparpagliano", "senza rete") provato di sbieco;
  in `spina.md` tre prove che esistono e la riga non cita
  (`test_scan_root_gone_midway_aborts_without_marking_missing`,
  `test_no_autostart_and_precheck_409s`, `test_scan_frames_per_second_does_not_regress`), e il
  verbo del pulsante, che `test_scan_lock_stop_and_the_button_verb` prova e nessuna riga
  promette; in `sito.md` tre righe che citano un file invece di
  una prova; le prove del catalogo col nome in italiano (`tools/test_catalogo.py`,
  `tools/test_simbad.py`). Le prove di schermo si rifanno col disegno nuovo.
- **La regola "le misure dell'header non si leggono" (`spina.md`) non ha una prova**: la guarda
  solo un commento in `fits/header_keys.py`. Rimedio: un test su `header_keys.KEYS` che rifiuti
  FWHM, HFR, SNR e STARCOUNT.
- **Una misura di tempo non ha niente che le impedisca di girare sotto carico.**
  `test_catalog_load_seconds_does_not_regress` (`backend/tests/test_perf_catalog.py`, `lento`)
  confronta un tempo col tetto di `backend/tests/perf_baseline.json`. In CI gira da solo, ma chi
  lancia la suite intera con `-n auto` lo misura con decine di processi addosso, e cade. Lo stesso
  vale per i frame al secondo di `backend/tests/test_perf_scan.py`, che cade anche da solo quando
  la macchina e' carica (sotto la soglia in 2 corse su 16, sul codice nuovo e su quello di prima).
  Rimedio: una guardia che si rifiuti di misurare quando non e' solo, o la mediana di piu' corse.
- **La guardia sull'anonimato del corpus e' cieca fuori dal suo elenco.**
  `test_no_real_site_coordinates_in_the_corpus` (`backend/tests/test_header_corpus.py`) guarda le
  chiavi di `GEO_KEYS`: con `GEOLAT`, `GEOLON` e `SITE` che portano un paese vero i test restano
  verdi; fuori anche `DATE-LOC` e i campi di testo libero. Rimedio: un criterio che non sia un
  elenco (un valore che somigli a una coordinata, un divieto sui campi liberi), e vale anche per i
  nomi di persona nei documenti.
- **Tre macchine che il frontend ha indebolito.** (a) `pytest tools` non e' autosufficiente:
  senza `frontend/node_modules` i test di `tools/tipi.py` cadono dicendo "il generatore e'
  fallito" invece di "manca npm". (b) `tools/test_chiave_due_case.py` e' cieco alla casa che
  sparisce (`if f.is_file()`): tolto `frontend/src/api/client.ts` passa. (c) La mutazione notturna
  guarda solo `backend/astrolog` (`paths_to_mutate`).
- **La purezza di `identify_decide`, `identify_score` e `identify_geometry` e' scritta e non fatta
  rispettare:** aggiungendoci `sqlite3` o `catalog.lookup`, `lint-imports` resta verde. Serve un
  contratto loro in `backend/pyproject.toml`: quello dei moduli puri vieta `astrolog.spine`, e i
  tre si importano fra loro.
- **"Idempotente" e' scritto e non e' vero, e la prova non puo' accorgersene.**
  `backend/astrolog/vocab/header_value.py` lo dichiara, ma l'indice ASCOM si toglie una volta sola:
  `'ZWO Focuser (1) (2)'` da' `'zwo focuser (1)'`, che ripassato da' `'zwo focuser'`. La prova
  (`test_header_value_is_idempotent_and_keeps_distinct_things_distinct`) usa un campione senza
  indice in coda. Rimedio: riparare la promessa (il ciclo) o toglierla; in tutti e due i casi il
  campione deve portarne uno.
- **I tipi costano al push:** `tools/test_tipi.py` lancia tre volte il generatore, e ogni
  estrazione dello schema OpenAPI costruisce un'app vera e ricarica l'intero catalogo.

### Efficienza, misurata

- **Il solver e' il 98% del tempo** sull'archivio vero a cache vuota (5.952,9 s contro 84,1 di
  scansione, 2,8 di normalizzazione, 6,3 di identificazione, 1,5 di raggruppamento; 0,543 s a
  frame). Si rimanda al pacchetto, dove si misura ASTAP su un NAS arm64 vero. Le misure che dicono
  di **non** limare altrove: `identify` rilegge il catalogo per ogni corsa ma pesa 6,3 s;
  `normalize` fa circa 19 query a frame ma dura 2,8 s; il commit per frame costa 4,3 s ed e' una
  promessa con le sue guardie. `_as_the_user_said` (`spine/identify.py`) interroga
  `declarations` una volta a frame anche a mani vuote: 2,8 µs a frame, ~31 ms sugli ~11.000
  frame veri (0,5% dei 6,3 s). Saltarla vuole una foto delle correzioni a inizio giro, e una
  correzione scritta a giro in corso non varrebbe per i frame dopo: resta.
- **La suite ricostruisce il modello del catalogo per ogni worker** (0,271 s a processo): il
  fixture e' di sessione ma per processo, senza lucchetto fra processi.
- **Chi non ha nemmeno un `IMAGETYP` paga il solver sui suoi dark.** Un file senza tipo passa dal
  cielo, e un dark con pixel caldi fitti il solver lo scambia per stelle: senza focale ne'
  puntamento arriva al tempo massimo di ASTAP, e la rinuncia non e' in cache (si ripaga a ogni DB
  ricreato).
- **Una lettura non calcola mai, e ci sono ancora letture che calcolano.** La regola ha le sue
  macchine nei contratti dei moduli (`backend/pyproject.toml`). Fuori restano: il **contatore
  della barra** chiede tutta Da confermare (`GET /review`) per mostrare un numero, a ogni pagina e
  a ogni ritorno sulla finestra (`frontend/src/main.tsx` crea il client senza `staleTime`). Dopo
  la fase 2 costa 50-114 ms su 20.000 frame sintetici (3,3 s solo sull'archivio gonfiato a 5.000
  voci per famiglia): un conto a parte scriverebbe in due case il predicato di cosa e' una domanda
  aperta, e non vale. Si rimisura col disegno nuovo, che decide quando la barra chiede. Dei lettori di
  Da confermare, la tendina dei corredi e l'elenco degli oggetti contano ancora ogni frame a ogni
  apertura. Piu' piccoli: i frame per cartella in `GET /folders`; `stages.pending_by_stage` che
  conta `measure`, stadio che non gira mai (la sua chiave esce in `GET /pipeline/status`:
  toglierla cambia la risposta). Ogni ricalcolo tolto entra in un contratto, o in una prova che
  confronta cio' che e' scritto con cio' che le regole direbbero (`tests/test_header_asks.py`).
- **La normalizzazione tiene in mano camera, copia e marchio di ogni frame in coda per tutto il
  giro** (`spine/normalize.py`, `_before_the_round`; `spine/copies.py`): su 5.800 frame sintetici
  il picco e' 2.653 KB contro 1.174 del giro doppio, con tempo e query piu' bassi. Pesa alla prima
  lettura di un archivio grande; si rimisura su un NAS vero prima di decidere un rimedio.
- **Il totale dell'archivio viaggia in ogni pagina dello scorrimento delle Notti**:
  `nights.archive_totals` fa una scansione piena (14,6-19 ms su 40.000 frame) a ogni "mostra
  altre", e conta solo la prima. Rimedio: i totali solo alla prima pagina. Non e' un refactor:
  le pagine dopo la prima cambiano forma (`totals` e' obbligatorio in `NightList`).
- **Rispondere a N schede dell'attrezzatura in un Applica costa N letture**: `row_of` rifa'
  `by_signature` (`spine/signature_page.py`) per ogni risposta, 44 ms a lettura su 21.000 frame
  sintetici. Leggerlo una volta non e' un refactor: una risposta cambia le altre schede (il colore
  scritto sulla camera spegne la domanda del filtro sulle schede della stessa camera; la risposta
  salvata puo' prendersi righe di una firma vicina entro la tolleranza della focale; la stessa
  firma due volte nello stesso Applica).
- **Una risposta sul filtro e l'unione di due grafie di una camera rimettono in coda piu' frame del
  necessario** (`api/review_write_folders._sensor`, `api/instrument_answer.merge`): su 2.000 frame
  1.750 invece di 500 e 2.000 invece di 250 (worker 1,15 s contro 0,57; 1,18 contro 0,23).
  Provato il 6/10 e tolto: con meno frame nel giro cambiano i gruppi di focale, e tre controesempi
  danno corredi diversi. Aspetta *Il corredo di un frame dipende da quando e' stato letto*.
- **Cambiare il fuso di casa tiene il database dentro la richiesta**, e il tempo cresce coi frame
  che cambiano data (`spine/home_nights.py`): il grosso e' `unnamed.assign` frame per frame. Su un
  archivio grande senza coordinate una scrittura del worker puo' avvicinarsi al `busy_timeout`
  (`db/connect.py`). Rimedio: portare il lavoro fuori dalla richiesta. Scegliere il gruppo una
  volta per notte, camera e telescopio non e' un refactor: `assign` confronta ogni frame col
  puntamento di chi ha aperto il gruppo, frame dopo frame, e i gruppi cambierebbero.
- **I file senza tipo di una cartella detta di calibrazione si rileggono a ogni scansione**:
  saltati alla porta non hanno una posizione, e il pre-controllo incrementale non li riconosce
  (`spine/scan.py`). Rimedio: ricordare i file saltati con percorso, dimensione e data.
- **Cercare il catalogo di ASTAP costa una lettura di cartella a ogni domanda** (`GET /settings`,
  `PATCH /settings`, `GET /solver`): 5,2 ms per 1.492 voci su disco locale; su una condivisione di
  rete sarebbe un'altra cosa. Rimedio: tenere la risposta per un po'. Non vale finche' ASTAP sta
  sul disco locale, come su Windows, Mac e nell'immagine Docker; si rimisura se un utente lo
  tiene su una condivisione.

### Doppioni -- lo stesso pezzo scritto piu' volte

- **Il meteo**: la condizione "il meteo di questa notte" in SQL due volte (la pagina delle Notti e
  lo storico), per cui la spina conosce la tabella del meteo senza importarla. Resta il `cast` di
  `night_date` in `forecast.refresh`: toglierlo con `clock.night_of` cambia l'esito di un fuso
  salvato non valido (oggi `bad_answer` se la risposta non ha ore), quindi va in un `/ripara`.
- **Piu' piccoli**: `CATALOG_PRIORITY` (`spine/identify_score.py`) senza sei sigle che `parse`
  produce; frasi dei contratti copiate nelle docstring (da ricontare); i siti senza una casa in
  lettura come oggetti e notti; la riga che chiede a SQLite il piano di una query, scritta a mano in 16 file di
  prova (`grep "EXPLAIN QUERY PLAN" backend/tests`), da fare aiutante in `conftest.py`; lo stadio
  tenuto fermo a meta' con una porta (`_holding` in `test_api_scan_all.py`), ricopiato in
  `test_api_scan.py` e `test_review.py`. Non sono doppioni: i tre `detach` staccano tabelle
  diverse, i tre `drop_empty_*` puliscono tre tabelle con tre regole.

## Nasce con...

Cose nominate dal metodo che non esistono, o esistono a meta', e con quale tappa arrivano. Una
riga sparisce quando la cosa c'e' tutta; se la sua tappa e' passata e la cosa non c'e', la
colonna di destra lo dice (scaduta) invece di spostarsi in silenzio su una tappa piu' comoda.

| cosa | con |
|---|---|
| `THIRD_PARTY.md` **generato** (`pip-licenses`, `license-checker`) con ogni dipendenza, la licenza e i crediti obbligatori (ESA/Gaia/DPAC, ASTAP, Aladin, HYG, OpenNGC, Stellarium, SIMBAD) | il pacchetto |
| in CI: `npm audit` e controllo licenze (`--no-audit` sulla install in `.github/workflows/ci.yml` **disattiva** il controllo, non lo fa) | il pacchetto |
| lo stack delle **metriche** scelto con la misura su arm64 in mano ([ADR 0007](adr/0007-metriche-con-sep.md)); con lui si porta `old/backend/astrolog/misura.py` coi suoi 8 test | `measure` |
| `tools/gen_changelog.py` e `release.yml` su tag `v*` (la versione vive in `astrolog/__init__.py`) | il pacchetto |
| la pagina **Diagnostica** col bottone "copia" ([ADR 0008](adr/0008-diagnostica-senza-telemetria.md)) | il pacchetto |
| `backend/tests/header/` **c'e'** (questo elenco e' l'unico: le skill vi rimandano): header veri di N.I.N.A. e ASIAIR, di piu' utenti, anonimizzati. **Mancano Voyager e SGP**: servono file veri. Ogni header nuovo entra prima della correzione che lo fa passare | appena arriva un file vero |
| nella CI: il build dell'immagine per amd64 e arm64 (runner `ubuntu-24.04-arm` nativo) | il pacchetto |
| pochi FITS **veri** con licenza compatibile e un database ASTAP piccolo (D05), per far girare in CI i test `lento` del solver (`tests/test_perf_solve.py` si salta senza `ASTROLOG_TEST_FITS`) | appena arriva un file vero |
| **la misura del solver su un NAS arm64 vero** (1-2 GB di RAM): sul portatile sta in `backend/tests/perf_baseline.json` | il pacchetto |

## Per il disegno nuovo

Le pagine si rifanno tutte con Claude Design
([ADR 0012](adr/0012-il-disegno-viene-da-claude-design.md)). Qui cio' che il disegno nuovo deve
sapere: le regole che valgono per qualunque disegno, poi cosa ogni pagina deve saper fare. Una
riga per voce.

### Regole per qualunque disegno

- **Il colore da solo non dice mai niente** (WCAG 1.4.1); un segno grafico arriva a 3:1 sul suo
  fondo (WCAG 1.4.11) e un testo vivo a 4,5:1 (1.4.3).
- **`--inchiostro-spento` non arriva alla soglia dove porta testo vivo**: nel foglio veste anche il
  conteggio di un gruppo in tabella e il segnaposto di un campo (2,75:1 e 2,47:1 contro 4,5:1);
  quando servono, la coppia entra in `tools/controlli_contrasto.py` e il colore si corregge alla
  fonte.
- **La scala di Bortle va da freddo a caldo, non da chiaro a scuro**: sul fondo scuro dell'app il
  buio non si vede (un nero puro fa 1,07:1), e sparirebbe la classe 1, il cielo migliore.
- **I numeri nostri dentro il foglio si tengono fermi con una guardia**: i pavimenti di Bortle
  nel commento di `.as-bortle` (`pavimenti_del_cielo` in `tools/controlli_foglio.py`) si'; il
  pavimento del grafico della notte (-15 gradi) e l'altezza della tela in barra (40px), ricopiati
  in `frontend/src/disegnoDellaLuna.ts` e `frontend/src/Stanotte.tsx`, no; il tetto della Luna
  (il foglio commenta 28,6 gradi, `ephemeris/__init__.py` usa 28,8 come limite superiore) no.
- **Il fuoco va dove serve**: un bottone che apre un campo ("Non e' questo: lo correggo", "Non e'
  in elenco", "Dagli un nome") ci porta il fuoco; **il dialogo non trattiene il fuoco** oggi
  (`frontend/src/Dialogo.tsx`: col tabulatore si esce sulla pagina dietro), e va chiuso con un
  anello provato col tabulatore.
- **Comportamenti che il CSS non fa e il codice si'**: Esc che chiude suggerimento e dialogo; le
  frecce dentro la ricerca (`aria-activedescendant`) e fra le schede (`tabindex` che segue la
  attiva); `aria-expanded` e `aria-selected` che si ribaltano; il suggerimento che si apre col
  dito (su iOS toccare un `button` non da' il fuoco); l'avviso breve che sparisce da solo, mai
  quello d'allarme; il `viewBox` dei grafici calcolato dalla larghezza della colonna.
- **Una scelta fra voci poche e fisse e' un segmentato, fra voci dell'archivio un elenco a
  comparsa** (skill `componente-che-formatta`); un mattone solo per i due ruoli ARIA del
  segmentato (scegliere un pannello, riordinare un elenco).
- **Un punto di riferimento contiene cio' che dice**: il piede con sito, cielo e Luna non sta
  dentro il `<nav>` delle pagine, e un elenco di voci si annuncia come elenco.
- **Testi**: nessun letterale fuori da `t()`, oggi senza guardia (ne' `frontend/eslint.config.js`
  ne' `tools/` la controllano); il singolare lo sceglie `t()` solo per il segnaposto
  `n`, quindi ogni conto si chiama `n` (oggi non lo fanno `nights.totals`, `weather.window.*`,
  `review.applied`, `review.lookalikes.looksLike`); le parole vietate del glossario hanno bisogno
  di una macchina, che leghi ogni parola vietata alla sua voce ("sessione" e' vietata per
  `night` e giusta per `session`); i dizionari si caricano a richiesta quando l'utente puo'
  scegliere la lingua (oggi l'inglese viaggia nel bundle di tutti, il 6,5% del pacchetto); una
  guardia i18n per pagina.
- **Un numero scritto in un campo e' all'italiana**: oggi coordinate e focale proposta arrivano
  col punto (`frontend/src/sito.tsx`; la focale proposta e' `focal_suggested` della scheda
  dell'attrezzatura), e chi scrive col punto deve
  ritrovare cio' che ha scritto.
- **Nomi in inglese** per file, componenti e funzioni del frontend nuovo, come nel backend.
- **Il formato del frontend in pre-commit**, con una configurazione che dica lo stile del
  progetto: `frontend/` non ne ha, e Prettier di serie riscrive i file con regole diverse.
- **Prove**: una richiesta per tasto si prova dove la richiesta si vede (oggi
  `frontend/tests/archivio-barra.test.tsx` resta verde senza l'attesa fra un tasto e l'altro); il
  guscio finto, la via per una sezione di Impostazioni e **la pagina piena vive in un file di
  prova solo** (`frontend/tests/accessibilita.test.tsx`) vanno nel banco; `jscpd` guarda anche
  `frontend/tests`; una prova che aspetta col tetto di fabbrica di un secondo cade sotto
  copertura (*se li' non c e nessun solver, il passo lo dice*, `frontend/tests/wizard-solver.test.tsx`:
  se ricapita, si alza l'attesa); la scelta della cartella dall'elenco del NAS nelle Impostazioni
  (`ImpostazioniCartelle.tsx`) non ha prova, il primo avvio si'; il campo del percorso di ASTAP (`frontend/src/riconoscitore.tsx`) mette in cache
  cio' che la scrittura ha restituito e torna riprovabile se la scrittura cade, e nessuna prova
  se ne accorge.
- **Righe dei contratti provate a meta' sullo schermo**: il collegamento dell'Archivio (si prova
  che la scelta va nell'indirizzo, non che aprendolo si veda la stessa vista con la stessa ricerca,
  `archivio.md`); Esc sul pannello della Luna; il tasto indietro fra le sezioni delle Impostazioni
  (`navigazione.md`); in Da confermare il contatore delle risposte, l'ordine delle schede e
  "dichiarato da te". Il disegno nuovo le prova davvero.
- **Dopo una scrittura si usa la risposta**: si scrive nella cache invece di rileggere (siti e
  cartelle), e cio' che il server decide (il sito di casa, `is_default`) si legge dalla risposta,
  non si indovina contando prima.
- **Gli elenchi di valori chiusi arrivano dall'OpenAPI**: le bande dei filtri, oggi enumerate a
  mano in `frontend/src/SezioneFiltri.tsx`, con `backend/astrolog/api/vocab.py`.

### Cosa devono saper fare le pagine

- **Casa**, per ultima: una riga di stato (cose da confermare, l'ultima lettura), l'ultima notte
  (data, quanti giorni fa, sito, ore, frame, corredo, oggetti coi filtri) e tutto l'archivio
  (notti, sessioni, oggetti, ore con la media a notte; notti e ore per mese, ore per filtro); sopra,
  quando nascono, barra della notte, *Stanotte, in cielo*, meteo, prossime tre notti e pianeti.
  Niente calendario a giorni ne' streak; un mese senza notti dice perche'; l'arco arriva a oggi o
  all'ultima notte, quale viene dopo. Fuori la FWHM media (senza `measure`) e la miniatura.
- **Primo avvio**: riapribile dalle Impostazioni (`docs/domini/sito.md` lo promette); dice se la
  prima lettura non e' partita. Oggi `Wizard.tsx` tace in tre modi: un errore HTTP di
  `GET /folders` finisce in `data?.total ?? 0` e la lettura salta come se non ci fossero
  cartelle; l'`error` di `POST /scan` non si legge; il `catch` vuoto prende solo le richieste
  che non arrivano. Il rimedio guarda `error` su tutte e due le chiamate, non solo il `catch`.
- **Il nome dell'utente**, che il primo avvio chiede e salva, compare da qualche parte.
- **La lettura**: la catena intera delle fasi e la ricevuta dell'ultima corsa (`GET
  /pipeline/status` porta ogni stadio in `worker.stages`, `Scansiona.tsx` ne mostra uno); una
  frase per una corsa fermata da `no_star_database`; una lettura di una cartella ritirata dice che
  la cartella non si segue piu' (il campo c'e': `folder_retired` di `GET /scan-runs`).
- **Impostazioni**: tema chiaro e densita' (il foglio conosce `data-tema` e `data-densita`); un
  indice, o l'ultima sezione aperta, invece di atterrare su *Cartelle* e pagarne le chiamate.
- **Archivio**: **un errore alla primissima risposta dell'Archivio lascia un filtro acceso senza
  il modo di toglierlo** (`?q=zzz` col backend che si riavvia: la barra non c'e' finche' non
  arriva una risposta buona); la tabella stretta riconosce le celle di filtri ed etichette da
  qualcosa che non si traduce (oggi `td[data-etichetta="filtri"]` non aggancia mai); la modalita'
  "schermo" (la tabella che scorre e la barra delle pagine sempre raggiungibile) e' una fetta
  del guscio, non di una pagina; una chiave i18n per parola, una mappa sola delle viste, il tipo
  `Riga` esportato una volta.
- **Lo scheletro di pagina** (titolo, attesa, avviso d'errore) e i mattoni scritti a mano in piu'
  posti diventano mattoni: la tendina di scelta (cinque posti, voce vuota opzionale), il dato che
  non si sa (`as-dato--ignoto` in tre file, uno solo col segno).
- **Telaio**: il contatore di Da confermare con una lettura sua (*Una lettura non calcola mai*,
  sopra); la ricerca nella barra, con la sua rotta (Marco, 7/10/2026).
- **Stanotte**: senza previsione non rilegge ogni 5 minuti per sempre (`rileggiOgni`); il piede
  sa la scadenza vera al mezzogiorno del sito (*Il piede richiede il cielo a tempo, non a
  scadenza*, nel Parcheggio); sopra gli 84 gradi di latitudine, se il buio tocca tutti e due i
  bordi, dice "tutta la notte" invece di "dalle 12:00 alle 12:00".
- **Sito**: l'altitudine che manca si dice (il backend manda `site_no_elevation`, lo schermo non
  la mostra); la ricerca che cerca mentre si scrive mette un ritardo nella pagina, perche' la
  rotta ne serve una al secondo.
- **Da confermare, la scheda dell'attrezzatura** (S1, Marco: aspetta il disegno). Il backend la
  manda gia' (`gear` in `/api/v1/review`, `gear` in Applica); oggi non si vede, e il conto la
  conta. Una scheda per firma: cio' che i file dicono (camera e telescopio come scritti, focale,
  sensore, pixel), cosa ci hai ripreso, e solo le parti chieste (`asks_camera`, `asks_optics`,
  `asks_filter`): la camera da un corredo (`rig_choices`) o scritta con la focale (proposta
  `focal_suggested`), l'ottica fra le tue (`optics_choices`, proposta `optics`) o scritta, il
  filtro fra *a colori*, *nessun filtro*, *uno dei miei* (`filter_choices`). Si risponde una
  parte alla volta; `complete` dice quando non conta piu'; un rifiuto `not_asked` dice una parte
  che la scheda non chiede.
- **Da confermare, la scheda dell'oggetto** (S3, aspetta il disegno). Il backend la manda gia'
  (`objects` in `/api/v1/review`, pagine in `/review/objects/settled`, `objects` in Applica);
  oggi non si vede, e il conto la conta. Una scheda per gruppo di frame: un oggetto trovato
  (`name`, `confidence`, `candidates` da cliccare) o frame senza nome e senza cielo (`group`:
  notte, camera, telescopio, puntamento, dalla prima all'ultima posa nell'ora del posto). Ore e
  frame su ogni scheda (`integration_s`, `untimed`). Risposta: un candidato (`slug`), un nome
  scritto, o *non e' un oggetto*; `answer` dice quella data, e una scheda risposta resta in pagina.
  Erano le sezioni Oggetti e Senza nome, tolte dallo schermo con S3.
- **Da confermare**: le sezioni si spengono finche' l'Applica non torna (oggi una risposta data
  nell'attesa si perde); la barra a sinistra di una riga dice una cosa sola (oggi *Quale filtro
  notte per notte* segna il salvato, le altre il da mandare); la tendina
  dei corredi della scheda dell'attrezzatura si apre solo premendo; la scelta fra due o tre voci fisse
  e' un segmentato.
- **Attrezzatura**: un filtro scritto a mano cerca nel catalogo dei modelli, cosi' si possono
  scrivere anche le bande delle camere a colori.
- **Mobile**: le frasi di posto ("qui accanto") si rileggono con la veste stretta.
- **Errori**: se `/api/v1/settings` non risponde arriva una frase giusta anche senza corpo (il
  502 del proxy) e quando il fetch fallisce.

## Parcheggio

### Debito che aspetta il suo momento

- **Il backup delle risposte, quattro limiti** (ADR 0017, `spine/backup.py`): il campione di una
  cartella entra nel file solo alla prima risposta dopo la sua scansione (la scansione non lo
  riscrive), quindi un database perso prima di ogni altra risposta torna con la cartella senza
  campione; i "pezzi e filtri scritti da te" contano anche i filtri nati dai file (`filters` non
  dice chi l'ha fatto); i numeri della frase non concordano al singolare ("1 siti"); il nome
  `risposte.json` sta anche in `frontend/src/Backup.tsx`.
- **La cartella spostata, tre limiti** (M2, `spine/folder_move.py`, `api/folders._moved_here`):
  una condivisione bloccata consuma da sola `PROBE_SECONDS` nella raggiungibilita' e la sonda
  risponde `out_of_time` anche per le altre (serve un tempo a parte: meccanismo nuovo); il
  campione sono i primi 5 file che la cartella vecchia conosce, quindi un solo file in comune
  basta a proporre lo spostamento (il clic resta dell'utente); con due cartelle registrate una
  dentro l'altra, `UPDATE OR REPLACE` sulle dichiarazioni puo' sovrascrivere la risposta
  dell'altra.
- **Mosaici, dichiarazioni e archivio, dopo la fase 1**: le pose e i
  pannelli di `mosaic` e `mosaic_geometry` restano `dict[str, Any]`, non `db/row.Row`, perche'
  `identify_geometry.frame_shape`/`frame_radius_deg` leggono con `.get` (un `sqlite3.Row` non ce
  l'ha, e i test passano dict senza i lati): passare a `[]` cambia comportamento, quindi aspetta.
  `mosaic_geometry` non e' uno stadio: quando il mosaico lo diventera', entra nel contratto di
  indipendenza in `backend/pyproject.toml`. La docstring di
  `nights.still_reading` dice "`measure`, which nobody runs yet": invecchia quando uno stadio lo
  lancera'.
- **Domande per gruppo e oggetti, dopo la fase 1**: `row_of` e' la stessa riga
  (`next(iter(by_...(conn, only=key)), None)`) in `signature_page` e `typeless`, e l'ordine "il
  piu' numeroso in cima" (`-frames`, `key`) e' riscritto in `signature_page`, `unnamed` e
  `frame_folder.counted`; "un grezzo senza bianchi o `None`" e' `unnamed._written` e di nuovo a
  mano in `signature_page._card`: nessuna casa comune fra i tre senza un modulo nuovo. Regola
  detta piu' volte: "i frame gia' risposti tornano in coda, cosi' un
  ripensamento vale" nei `requeue` di `signature`, `unfiltered` e `unnamed`.
- **La base di `api`, dopo la fase 1.** Senza test: i 409 di `POST /pipeline/run`
  (`no_folders`, `no_readable_folders`, `worker_busy`) e il suo 200 "niente da avviare" a corsa
  in giro; `POST /pipeline/stop` a worker fermo; `GET /pipeline/status` con una scansione fermata
  prima della prima cartella; `create_app` con un catalogo che solleva al caricamento. Un solo
  `except` in `app._load_catalog` copre il catalogo e le due tabelle derivate
  (`gear_usage.write`, `object_candidates.write`): se cadono queste, il log dice che il catalogo
  non si e' caricato, ed e' falso, e le tabelle restano vecchie fino al catalogo dopo. Riprendi
  butta il `ScanAllStarted` di `start_scan_all`, quindi le cartelle saltate in parte non si
  dicono. `GET /settings` e
  `GET /solver` cercano il solver sul disco a ogni lettura (~7,9 ms contro ~1,5): una lettura che
  calcola. Doppioni: i tre verbi del bottone scritti a mano due volte in
  `frontend/src/Scansiona.tsx` invece del tipo generato; regole dette due volte (il perche' delle
  ricevute in `pipeline.scan_progress` e `_reading_cut_short`; i perche' di `solver_found` e
  `solver_where` ripetuti dalle docstring delle rotte del solver, che sono l'OpenAPI).
- **Il testo di `no_readable_folders`, in una fetta che tocca lo schermo.** Il 409 di
  `POST /pipeline/run` e `POST /scan` scatta anche quando tutte le cartelle sono gia' in
  scansione (`scan_running`), ma `frontend/src/i18n/it.ts` e `en.ts` (riga 47) dicono solo che non
  si riescono a leggere: un doppio clic su Scansiona mostra "non si riesce a leggere". Il testo
  deve dire anche il caso della scansione gia' in corso.
- **La lista delle cartelle sotto un tetto unico** (`api/folders._reachable`): una condivisione
  che non risponde lascia indietro il suo thread a ogni `GET /folders`, e finche' resta morta i
  thread si sommano; quando il tempo scade la cartella diventa `reachable: false` senza una riga
  nel log, quindi non si distingue un'attesa scaduta da un errore vero.
- **Le ricevute di lettura, dopo la riparazione.** Una lettura conta come cominciata appena il
  suo stadio parte (`on_folder`), prima che `connect()` e `folder_root` riescano: se cadono li',
  il worker lo scrive nel log ma la ricevuta resta aperta, per una cartella come per tutte.
  `test_a_start_that_breaks_unexpectedly_leaves_nothing_behind` parte da un'app vuota, quindi
  non distingue "rimette la corsa di prima" da "azzera" (lo prova solo il ramo
  `WorkerBusyError`); il caso `stop_from_check=2` di
  `test_resume_reads_one_folder_stopped_before_it_began` conta su quante volte il worker chiede
  lo Stop prima di consegnare lo stadio. `start_scan` pulisce un avvio fallito a mano e
  `start_scan_all` con `_forget_start`, in ordine opposto (lucchetto poi ricevuta, ricevuta poi
  lucchetto): unirli cambia cosa vede una richiesta che arriva in mezzo. A
  fine suite un worker puo' ancora lanciare l'ASTAP vero della macchina e stampare "can't create
  new thread at interpreter shutdown": dipende dai tempi, visto una volta e poi in nessuna di
  quattro corse ripetute.
- **Le rotte di scrittura, dopo la fase 1.** Codici d'errore scritti nel contratto e mai provati
  da un test (i test guardano solo lo stato HTTP, o non arrivano al caso): 409 `root_unreachable`
  di browse, 409 `folder_exists` col suo `folder_id`, 404 `folder_not_found` (`api/folders.py`);
  409 `folder_retired`, 404 `scan_run_not_found` (`api/scan.py`); e la prima registrazione di una
  cartella che risponde `reactivated: false`. Regole dette due o tre volte: "le stesse funzioni di
  Da confermare" in `gear_write` (modulo, due
  rotte: il loro testo e' l'OpenAPI) e in `docs/domini/attrezzatura.md`; "`frames` viene dal
  database" in `folders` e in `FolderOut.frames`.
- **Le rotte di lettura, dopo la fase 1.** `create_site` e `edit_site` (`api/sites.py`)
  prendono `sqlite3.IntegrityError` su tutta la transazione, non solo sull'`INSERT`/`UPDATE` del
  nome: un vincolo violato in `_make_default`, nei `requeue` o in `home_nights.follow_home`
  risponde 409 `site_name_taken`, che e' falso, e l'errore vero non va nel log (il contratto ora
  dice "409 se il nome e' gia' di un altro sito"). Le docstring delle rotte hanno preso la prosa
  della docstring di modulo, e ripetono nell'OpenAPI cio' che i modelli dicono gia': cosa perde
  una notte di tendenza (`weather` e `WeatherNightOut`), il piede con posto e classe (`tonight`
  e `SiteSkyOut`), `still_reading` (`nights` e `models_nights`).
- **I modelli di revisione e attrezzatura, dopo la fase 1: le regole ripetute ora stanno
  nell'OpenAPI.** I commenti diventati descrizioni portano in `schema.d.ts` regole scritte molte
  volte: "un gruppo gia' risposto resta in pagina per cambiare idea" (otto modelli di
  `models_review_groups`), "si risponde con la chiave stabile, mai col numero di riga" (in quasi
  ogni `key` di `models_review*`), "`null` finche' non e' contato" in tre modelli di `models_gear`, le
  descrizioni di `key`, `night`, `integration_s` e `untimed` uguali fra gruppi, "Checked here so
  the OpenAPI declares it" in due validatori. Rimedio: la regola nella docstring del modulo o
  del modello padre, e i campi che rimandano.
- **I modelli delle pagine, dopo la fase 1**: `Night.frames` e `ArchiveObject.frames` hanno la
  stessa descrizione parola per parola nell'OpenAPI, e quelle di `untimed` sono quasi uguali (il
  significato ha casa nel glossario).
- **Le rotte di lettura di `api`, dopo la fase 2**: `api/weather._seeing` scrive a mano
  `"meteoblue"` accanto a `fetches.Source`: il campo e' un `Literal` che ripete
  apposta, e un membro dell'enum non lo soddisfa per il tipo (servirebbe un `cast`).
- **Frame senza tipo, dopo la fase 2**: "risolto e' una foto, senza stelle una calibrazione" e'
  detta in `typeless` e nella descrizione OpenAPI di `api/models_review_groups` (toglierla di li'
  cambia lo schema).
- **Attrezzatura, dopo la fase 1**: `filters_used.of` e `idlist` accettano anche chiavi di
  testo (i mosaici dell'Archivio) in una tabella `id INTEGER`, che le tiene per affinita' di SQLite.
- **Stadi, dopo la fase 1**: per un alias di tipo `worker/worker.py` importa `spine.stage_run`
  (da solo, 16 moduli invece di 3; nell'app intera costo zero; toglierlo vuole un import sotto
  `TYPE_CHECKING`, che il repo non usa ancora).
- **I file sciolti, dopo la fase 2**: `astap.analyse` inghiotte timeout e `OSError` e torna
  `(None, None)` senza scrivere nel log, mentre `solve` lo scrive (HFD e stelle vuoti senza
  traccia in Diagnostica: aggiungere la riga cambia il log, quindi non e' un refactor); `astap.solve`
  e `place.sky_of` tengono il `noqa: PLR0913` perche' la firma e' usata fuori (`spine/solve`,
  `api/sites`); il log d'accesso scrive la query intera, quindi
  una chiave messa a mano in un indirizzo (`/?token=...`) finirebbe in `log/astrolog.log`, ma l'app
  non la mette mai in un indirizzo (ADR 0002: arriva nella pagina e viaggia in un header).
- **`tools/guardia_test.py` non vede due forme di test del frontend**: `it.each([...])(...)` e i
  titoli che vanno a capo dopo `it(` (`frontend/tests/confermare-soggetti.test.tsx`,
  `frontend/tests/meteo.test.tsx`), quindi toglierli passa inosservato.
- **Dopo il rilascio, cio' che si ricava dal vocabolario va riscritto quando il vocabolario
  cambia.** Oggi il database si ricrea; dopo il rilascio restera' scritto col vocabolario di
  prima: i tre giudizi sul grezzo (`spine/header_asks.py`), il software normalizzato, ogni valore
  che `normalize` ricava da un nome. Serve un modo per rifarli prima che una versione cambi il
  vocabolario, o la pagina leggerebbe il giudizio vecchio mentre chi rimette in coda rigiudica col
  nuovo (`signature.frames_of`); oggi coincidono, e
  `tests/test_header_asks.py` lo prova.
- **L'app non si accorge di girare su un database di uno schema vecchio**: la scansione si rompe
  con `no such column`. Lo schema non si migra, ma l'avvio deve dirlo confrontando `schema.sql`
  con `PRAGMA table_info` (`db/connect.py`).
- **Un corredo scritto a mano con la focale sbagliata non si corregge e non si cancella**: la sua
  impronta e' la sua identita', e un'unione lo fa risorgere dalla dichiarazione
  (`restore_declared` in `spine/rigs.py`). Resta con zero ore accanto a quello giusto. Rimedio: il
  gesto che toglie un corredo tuo senza frame, riga e dichiarazione insieme.
- **Cancellare un pezzo dell'attrezzatura non si puo', e la domanda non e' banale**: un pezzo che
  tiene dei frame non si toglie senza decidere che fine fanno le sue ore (sparire, restare
  orfane, tornare in coda). Il progetto di prima rispondeva 409 dicendo chi lo tiene e quanti frame
  (`old/backend/astrolog/api/instruments.py`). Prima serve la scelta di prodotto.
- **`backfocus_mm` esiste e non si puo' scrivere**: sta nello schema e nei modelli
  (`api/models_gear.py`), ma nessuna scheda lo chiede (`api/instrument_answer.CARD`), nessuna
  grafia d'header lo riempie, e mandarlo e' un 422. Da decidere a quali generi chiederlo (non alla
  montatura).
- **Riportare la riga "nessun filtro" a filtro vero non riconta l'uso** (`is_none` da 1 a 0 in
  `spine/gear.declare_filter`): nessuno stadio riparte. Oggi ci arriva solo chi chiama l'API a
  mano; rimedio: far ripartire i suoi frame o riscrivere l'uso.
- **Un `catalog_id` si scrive insieme a bande che lo contraddicono** (`gear.declare_filter`): le
  bande vincono sul modello. Nessuna pagina manda le due cose insieme.
- **Un campo della scheda di uno strumento non si svuota**: `InstrumentCorrection` scarta i campi
  nulli (`exclude_none` in `api/instrument_answer.py`). Costa un modo di dire "vuoto" distinto da
  "non toccato"; la guida lo dichiara.
- **Due corredi possono avere lo stesso nome** (`rigs.declare_rig` lo accetta): serve un rifiuto
  come `name_taken` per strumenti e filtri.
- **Due corredi con gli stessi pannelli danno due mosaici con la stessa etichetta**: la risposta
  dell'API non porta un nome del corredo leggibile.
- **Accanto a un gruppo di frame senza nome, cosa il cielo ha trovato negli altri frame della
  stessa notte e dello stesso puntamento**: servirebbe un campo `subjects` sul gruppo.
- **Tre elenchi ordinano nomi scritti dall'utente sui byte**: SQLite ordina `TEXT` sui byte (`vdB`
  dopo `WR`, le minuscole dopo le maiuscole). L'Archivio usa `COLLATE NOCASE`; restano
  `spine/inventory.py` (pezzi e filtri) e `api/sites.py` (siti). Rimedio: `COLLATE NOCASE` e una
  prova che mescoli le casse, e la regola scritta dove vale, cioe' per tutto il repo.
- **Un percorso dichiarato si controlla che sia un file, non che sia ASTAP**: `astap.where_exe`
  accetta qualunque file, e chi sbaglia si sente dire "trovato" e poi "gli manca il catalogo
  stellare". Rimedio: dirlo quando la corsa fallisce, dove ASTAP ha gia' parlato.
- **Le camere i cui file non dicono il binning restano senza pixel**: pixel fisico e ricavato
  vogliono il binning (`units.physical_pixel_um`, `units.pixel_um_from_scale`). Nell'archivio
  sintetico sono i profili di Voyager e SGP (`tests/synthetic.py`), non verificati; per SGP il
  lettore si aspetta gia' `CCDXBIN` (`fits/header_keys.py`). Si guarda con *Mancano Voyager e SGP*.
- **Il pixel ricavato dal cielo potrebbe dare al solver il campo dei frame che non dicono il
  pixel** (`instruments.pixel_from_sky_um`): oggi il campo viene solo da `XPIXSZ`
  (`spine/solve.py`, `_scale_of`). Da misurare su frame veri: un pixel sbagliato manda il solver
  fuori strada.
- **L'ottica che i file non dicono: due ottiche alla stessa focale con la stessa camera sono
  una domanda sola** (`spine/signature.py`): i file non dicono altro. Si chiude con un'altra chiave, se un
  header vero ne mostrera' una.
- **La scheda dell'attrezzatura riabbina le risposte alle firme con la tolleranza della focale**
  (`signature.answer_for`, `units.same_focal`) a ogni lettura e a ogni giro di `normalize`. Rimedio: scrivere sul frame da quale
  risposta ha preso l'ottica.
- **Spostare un sito non ritaglia le sue notti dichiarate**: col fuso cambiato le notti nate da una
  risposta restano tagliate col fuso vecchio, e rifarle lascerebbe vuota per sempre quella di
  prima (`spine/group_store.drop_empty_nights` non la tocca). Rimedio: lo spostamento di data
  porta la notte con se'.
- **Rinominare un sito perde la risposta sulle sue coordinate**: la dichiarazione porta il nome.
  Rimedio: la rinomina impara la grafia vecchia, come per strumenti e filtri.
- **Un mosaico non si divide quando perde il pannello che lo legava** (`spine/mosaic.py`,
  `_sweep`). Della stessa famiglia: unendo due grafie di una camera, se il mosaico con la
  risposta e' quello della grafia assorbita, quello della tenuta resta una domanda sovrapposta; se
  la camera si dice per una parte dei pannelli, un frame nuovo nel punto di un pannello rimasto sul
  vecchio ne apre un altro accanto; un pannello che non conta (`spine/mosaic_weight.py`) lega lo
  stesso i mosaici che tocca quando nasce.
- **Una cartella detta "di calibrazione" che resta senza frame non si puo' piu' contraddire**: la
  domanda si compone dai frame entrati (`spine/typeless.py`), e la risposta resta scritta senza un
  posto dove ritirarla. Strada rara, ma la sezione promette che una risposta si cambia sempre.
- **Fra `identify` e `group` l'archivio ha zero sessioni**: nessuna rotta legge `sessions` fuori
  da `group_store`. Il giorno che nasce una pagina Sessioni, o si legge dalla ricevuta o le due
  spazzate vanno in una transazione.
- **Quando il catalogo arriva tardi, gli oggetti nati senza non si rifanno**: `load_catalog` non
  chiama `invalidate`. Tocca il primo avvio di tutti.
- **Un frame il cui file non c'e' piu', o che uno stadio ha segnato `failed`, resta nel residuo
  per sempre**: il pulsante Avvia parte a vuoto. La ricevuta distingue (`waiting`), il conteggio
  degli stadi no. Si chiude con la Diagnostica.
- **Una qualita' chiesta e non arrivata non si richiede piu'**: se la passata di analisi di ASTAP
  non risponde, il frame e' `done` senza `frame_metrics`. Si chiude con `measure`.
- **`frame_metrics` ha una provenienza sola per riga, e due produttori** (`astap` oggi, `sep` con
  `measure`): si decide quando nasce `measure`.
- **Su una primaria che ripete `NAXIS`, la strada veloce e astropy dicono due blocchi dati
  diversi**: astropy tiene la prima `NAXIS`, `header_read._primary_data_block` l'ultima (un file a
  piu' pagine la cui primaria ha perso l'END, o una primaria con due `NAXIS`). L'impronta usa la
  strada veloce ed e' stabile, ma l'oracolo di `tests/test_data_block_header_read.py` su quei
  file direbbe rosso. Si decide quale e' giusta prima di toccarla: cambiarla cambia le impronte.
- **La stessa chiave due volte nello stesso header: la prima o l'ultima?** Chi rilegge l'header
  salvato come dizionario tiene l'ultima, astropy la prima: `normalize` e la guardia del corpus
  possono rispondere diverso. Da decidere una volta per tutte le chiavi.
- **Meteoblue, tre cose da decidere**: un 429 (crediti finiti con una chiave buona) conta come
  rifiuto, toglie il seeing e dice "controlla la chiave"; ogni salvataggio di una chiave valida
  azzera il freno delle dodici ore e spende subito una chiamata, dentro la richiesta; nel primo
  avvio una chiave scritta e non provata si perde premendo Avanti, senza dirlo.
- **Il seeing non e' ancora un fattore mostrato**, come deve essere (`docs/domini/ereditato.md`,
  sezione G): la scala dipende dal corredo con cui si esce, e il Meteo non lo sa. Si decide quando
  il Planner sapra' con cosa esci.
- **La previsione del vecchio sito di casa resta nella tabella**: `weather.forecast.refresh`
  riscrive solo il sito nuovo. Nessuno la legge; si toglie quando il meteo guardera' piu' siti, o
  con una pulizia al cambio di casa.
- **Lo storico che non arriva non si vede**: se l'archivio rifiuta sempre la richiesta di un sito,
  le sue notti restano "non ancora arrivato" per sempre, e l'esito sta solo nel log e in
  `weather_fetches`; una notte che fa fallire la richiesta ferma anche le successive.
- **Il piede richiede il cielo a tempo, non a scadenza.** `GET /tonight` costa cento volte una
  lettura, e i suoi numeri scadono al mezzogiorno del sito: `frontend/src/Stanotte.tsx` si difende
  con un'ora di `staleTime`. Per l'ora esatta serve il fuso del posto, che la rotta non manda: si
  chiude quando il piede avra' comunque bisogno di sapere che ora e' li'.
- **Il totale in cima alle Notti costa 2,5 volte la forma che sostituisce**: i tre numeri passano
  dalla casa comune (`spine/counts.py`) con tre sotto-select, dove una passata con `COUNT(*)
  FILTER` bastava (18,2 ms contro 45,4 su 200.000 frame). Se un archivio vero lo mostra lento, si
  da' a `counts` anche la forma aggregata, non la si ricopia.
- **`tools/dev.py` con `ASTROLOG_PORT` avvia un frontend che non raggiunge il backend**: il proxy
  di `frontend/vite.config.ts` punta sempre a 8765.
- **Sul NAS senza `ASTROLOG_HOSTS` ogni chiamata dalla LAN e' un 400 senza indizio**: l'avvio
  (`backend/astrolog/__main__.py`) non avvisa e non c'e' un compose. Rimedio: il compose del
  pacchetto la dichiara, e l'avvio avvisa se manca.

### Aspettando un file vero

- **Il marchio di riscrittura si vede scattare su header veri, ma solo su file che non entrano**
  (9 stack su 14.148 header): la prova su un frame riscritto gira su FITS sintetici, e manca una
  coppia grezzo+calibrato vera.
- **`CREATOR` puo' portare una persona invece di un programma**, e allora il marchio finirebbe su
  un grezzo. Non si toglie: e' la chiave dell'ASIAIR. Mai visto su 14.148 file.
- **Le voci di calibrazione senza un header per provarle** (`flat bias`, `sky flat`, `dome flat`,
  `twilight flat`) entrano quando un header vero le scrive.
- **La spia dei file sommati non si vede su un FITS compresso** (`HISTORY` su un'estensione).
- **Un indizio ereditato sbagliato brucia il frame**: un `OBJECT` uguale su tutto rende sorelle
  frame di cieli diversi, e quello che eredita finisce `no_solution`. Il ritentativo alla cieca e'
  escluso; si riapre con un archivio che ha quel difetto.

### Misure che dicono di non toccare (ancora)

- **Le ore non sprecano**: ore degli oggetti 2,84 ms e dei mosaici 2,79 su un archivio sintetico
  della taglia di quello vero, una sola interrogazione per pagina. Un mosaico non conta due volte
  i frame di un oggetto su due pannelli (misurato, senza un test che lo difenda).
- **`mergeable_into` cresce al quadrato col numero dei pezzi**: 2,4 MB di risposta con 1.007
  pezzi; sotto i 100 non si sente. Rimedio, se serve: le grafie una volta per tipo.
- **Sospetto sul bytecode, non chiuso**: rossi aritmeticamente impossibili
  (`overlaps_frame(0.9, 120.0, 0.694)` che torna `False`) sono spariti con
  `PYTHONDONTWRITEBYTECODE=1` e non si sono ripetuti col bytecode acceso. La suite del push
  (`python -B`) e il job `instabilita` non lo scrivono, la mutazione notturna si'. Se un rosso
  impossibile ricompare, si guarda qui.
- **Due domande di Da confermare leggono righe che poi scartano** (la scheda dell'attrezzatura,
  i siti): su 100.000 frame sintetici la pagina intera sta a circa 0,22 s, e toglierle vale
  qualche decina di millesimi.
- **Tagliare in SQL la pagina dei file non letti non paga** (`GET /scan-runs/{id}/errors`): su
  20.000 file `json_each` con `LIMIT` costa 3,3 ms alla prima pagina e 5,8 all'ultima, contro
  3,2 di leggerli tutti e tagliarli in Python.
- **La cartella viva come `EXISTS` non paga**: nelle domande sull'attrezzatura e sul nome
  `frame_folder.JOIN` e un `EXISTS` costano lo stesso.

### Idee

- **Altri formati di file**: entrano solo `.fits` e `.fit` (`domini/spina.md`); poi `.fts` e
  `.fz`, poi XISF, che N.I.N.A. sa salvare. Quando un utente salva in un altro formato.
- **La previsione accanto al meteo vero**, per misurare quanto ci azzeccava su quel sito: oggi la
  previsione di una notte passata si butta.
- **Dividere i frame di una notte dal fondo cielo, invece che a mano**: il fondo separa bande
  larghe e strette di ordini di grandezza. Si cercano gli scalini, non le soglie; si misura prima,
  usando come campione i frame che il filtro lo scrivono; e prima si decide la provenienza di
  `frame_metrics`. La divisione a mano resta il pavimento.
- **Il cielo dentro l'app senza chiave**: il dato di luminosita' a 30 arcosecondi e' 2,9 GB;
  ridotto, la casella diventa di 9 km. Si riapre se qualcuno pubblica un dato piu' compatto.
- **Il dubbio vive sull'oggetto, non sul frame**: un frame sbagliato dentro un oggetto
  lucchettato non fa arrivare nessuna domanda. E' voluto; si riapre con una vista per questo
  genere di segnalazione.
- **Il generatore del catalogo resta in `old/`**: il dato e' portato, ma per rifarlo servono lo
  script e 13 MB di sorgenti. Finche' non si porta, `old/` non si cancella.
- **La relazione pezzo/adiacenza fra oggetti** (`NGC 2244` dentro la Rosetta, `M 110` accanto a
  `M 31`): in `old/` e' misurata, mai costruita. Serve al Planner e alla Carta del cielo.
- **Il corredo simulato del Planner** ("e se avessi") e' l'unico caso in cui il campo si deriva
  invece di misurarsi.
