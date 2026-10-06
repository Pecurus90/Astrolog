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
  `backend/astrolog/schema.sql`, il tag OpenAPI `luoghi` di `api/sites.py` e due messaggi di log
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
package: prima i nomi, poi doppioni e tipi, poi efficienza e file. Il debito gia' trovato:
- **I nomi interni in italiano** si rinominano (deciso: `CLAUDE.md`, "Nomi e commenti in
  inglese"), in `backend/astrolog`. La macchina c'e' (`tools/nomi_inglesi.py`, al commit): un
  nome italiano nuovo e' rosso, quelli vecchi stanno in `tools/nomi_italiani.txt`, che solo si
  accorcia. Non legge le stringhe: colonne SQL e segnaposto si cercano a mano. Fatti `db` e
  `fits` (e il segnaposto `{listed}` di `idlist.grouped`), poi `ephemeris` (`corpi` e' `bodies`).
  Fatti anche `weather`, `net` e gli altri file sciolti, e i primi tre lotti di `spine`
  (scansione, normalizzazione, stadi; risoluzione, identificazione, raggruppamento, frame senza
  tipo, `site_requeue`, `home_nights`). Nel quarto lotto: `corredi` (alias di
  `rigs`), `pose`, `staccate`, `modello`, `riga` (`gear`); `grafia`, `gia`, `scheda`
  (`gear_create`); `_SEMPRE`, `_CONTI`, `_USATI`, `_STRUMENTI`, `_CORREDI`, `_FILTRI`, `_OGGETTI`,
  `_OGGETTI_DEL_CORREDO`, `_OGGETTI_DEL_FILTRO`, `_OGGETTI_DEL_PEZZO`, `_CIELO`, `_COLONNE`,
  `_nuova`, `_con_le_ore`, `_riga`, `_strumenti`, `_corredi`, `_filtri`, `righe`, `elenco`,
  `conta`, `generi`, `detto`, `uso`, `cielo`, `oggetti`, `con_le_ore`, `visto`, `campo` e i
  segnaposto `{chiave}`, `{giunzione}`, `{campo}` (`gear_usage`); `trovato`, `campo`, `nomi`,
  `_pezzo_id`, `chiave`, `parti`, `ottica`, `focale`, `quando`, `rifatto`, `tolta`, `nome`, `pose`,
  `_MONTATURE`, `trovata`, `nuova` (`rigs`); `nome`,
  `votato`, `prima`, `colore`, `scelto` (`camera_specs`); `uno`, `valori`, `mezzo`
  (`camera_sky`); `soggetto` (parametro e colonna), `dove`, `solo` (`filters_used`). Nel quinto
  lotto: `dove`, `per_notte`,
  `nomi`, `nome`, `grafia`, `righe`, `ottica`, `visto`, `corredi`, `corredo`, `notte`, `viste`,
  `camere`, `ottiche`, `focali`, `intero`, `dicono` (`night_rig`); `risposta` (alias di `object_answer`, anche in
  `identify`, `mosaic`, `mosaic_proposals` e `api/review_write`), `lati`, `campo`, `chiave`,
  `vicini`, `altra`, `distanza`, `notte`, `detto`, `valore`, `nome`, `_POSES_OF_GROUP`
  (`unnamed`); `sorgente`, `righe`, `nomi`, `conti`, `gruppi`, `vuoti`, `trovati`, il parametro
  `gruppo` di `count_subject` (il dizionario del gruppo) e la colonna `gruppo` di `subjects_sql`,
  alias interno letto solo da `subjects_of` (`subjects_sql` la usano anche `mosaic_proposals` e
  `archive`, che non leggono `gruppo`) (`objects`); `prefisso`, `letto`, `valore`, `grafia`,
  `tocca`, `grezzo`, `altro_id`, `mie` (`object_answer`); `_COLONNE`, `righe`, `cielo`
  (`object_candidates`). Nel sesto lotto: `descrizione`, `proposte`, `peso` (alias di
  `mosaic_describe`, `mosaic_proposals`, `mosaic_weight`), `pose` (variabile e parametro di
  `_stays`, `_band`, `_open`), `_POSES`, `pannelli`, `vivi`, `lista`, `lasciati`, `righe`
  (`mosaic`); `_most_poses`, `voci`, `dentro`, `scelta`, `righe`, `nomi`, `versori`
  (`mosaic_describe`); `raggi`, `b_su_a`,
  `a_su_b` (`mosaic_geometry`); `soggetti`, `righe`, `valore`, `parola`, `detto`, `nomi`
  (`mosaic_proposals`); `per_mosaico`, `pannelli`, `misura`, `lavoro`, `soglia`, `peso`
  (`mosaic_weight`); `chiave`, `parti`, `ottica`, `camera`, `focale` (`declarations`); `_DOVE`,
  `_PAGINA`, `_QUANTE`, `_TOTALI`, `_OGGETTI`, `_FERME`, `_SENZA_CIELO`, `_lune`, `_meteo` e il
  suo parametro `fuso_riconosciuto`, la colonna `meteo`, `righe`, `lune`, `oggetti`, `filtri`,
  `riga`, `quando`, `certe`, `somme`, `dove`, `ordinati`, `voce`, `quanti` (`nights`); `ORDINI`
  (pubblico, letto da `test_spine_archive`), `_OGGETTI`, `_SLUG`, `_NOME`, `_DEL_SLUG`,
  `_DEL_NOME`, `_MOSAICI`, `_RIGHE`, `_ORE`, `_POSE_DELLA_RIGA`, `_PANNELLI`,
  `_OGGETTI_DELLA_RIGA`, `_CON_IL_FILTRO`, `_DAI_PANNELLI` coi segnaposto `{tabella}`,
  `{legame}`, `{colonna}`, `_DEL_CATALOGO`, `_NELLA_COSTELLAZIONE`, `_MINUSCOLE_ASCII`,
  `_PIEGATO`, `_CERCATO`, `_OGGETTI_DEI_PANNELLI` (letto da `test_spine_archive_mosaic`),
  `_cercando`, `_dove`, `_elenco`, le colonne `chiave` e `nome`, `criteri`, `scritto`, `scudato`,
  `pezzi`, `pezzo`, `valori`, `valore`, `cercato`, `suoi`, `ordine`, `dove`, `righe`, `quanti`,
  `oggetti`, `mosaici`, `elencate` (`archive`). Nel primo lotto di `api`: `cadenza`, `riga`,
  `sito` (`app`); `_servita`, `pagina_del_router`, il parametro di percorso `percorso` e il
  segnaposto `{chiave}` di `TOKEN_META` (`page`); `_scansione_interrotta`, `da_fare`
  (`pipeline`); `manca`, `percorso`, `provate`, `dove` (`settings`). Nel quarto lotto di `api`:
  `criteri`, `righe`, `quanti`, `oggetti`, `filtri`, `mosaici`, `pannelli` (`archive`); `_sito`,
  `_fascia`, `istante`, `riga`, `fascia`, `punto`, `sito`, `notte`, `mezzanotte`, `comincia`,
  `quante_ore`, `fase`, `cielo` (`tonight`); `_NOTTI`, `_ARRIVATA`, `_FONTI_DEL_CIELO`, `_CIELO`,
  `_VENTO`, `_CAMPI_DEL_CIELO`, `_in_quota`, `_notte`, `ore`, `del_cielo`, `posto`, `riassunto`,
  `fonte`, `ultimo`, `arrivate`, `scelto`, `vuoto`, `in_corso`, `del_sito`, `con_meteoblue`,
  `per_ora`, `via`, `righe`, `riga`, `sito` (`weather`); `chiave`, `esito`, `sito`
  (`weather_key`); `vuoti`, `vecchia`, `scritta`,
  `nome`, `senza_casa` (`sites`); `pezzi`, `filtri`, l'alias `strumento` (`gear`). Nel quinto
  lotto di `api`: `_pulisci`, `_scarta_le_mai_iniziate`, `prese`, `partite`, `saltate`, `coppie`,
  `iniziate`, `segui`, `orfane` (`scan`); `_scritto`, `scheda`, `bande`, `nuovo`,
  gli alias `corredi` e `strumento` (`gear_write`); `fuori`, `scheda` (`instrument_answer`);
  `domande`, `coppia`, `nomi`, l'alias `strumento` (`lookalike`). Nel sesto lotto di `api`:
  `_stadi_toccati`, `voluti`, `certi`, `incerte`, `righe_camere`, `da_chiedere`,
  `righe_senza_camera`, `righe_senza_nome`, `righe_senza_tipo`, `righe_senza_ottica`,
  `righe_mosaici`, `senza_camera`, `mosaici`, `coppie` (`review`); `righe`, `usati`, `nomi`,
  `posti`, `luoghi`, `casa`, `posto`, `vicini`, `quanto`, `confermati`, `nome`, `chiave`,
  `dubbio`, `aperti`, `certi`, l'alias `corredi` (`review_page`); `scrivendo` (letto anche da
  `gear_write`), `_rifiuto`, `rifiuto`, `_TUTTO`, `_SENZA_LIMITI`, `fino_a`, `chiave`, `scelte`,
  `rimesse`, `scritta`, `nome`, `sito`, gli alias `risposta`, `corredi`, `strumento`
  (`review_write`); `riga`, `scelte`, `scelto` (`review_write_folders`).
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
  fiducie, rami e motivi di `identify`). In `weather` restano stringhe i generi di riga
  (`forecast.KIND`, `history.KIND`) e le fonti per modello (`forecast.source_of`), aperte quanto
  la scelta dei modelli. Nell'attrezzatura i soggetti dell'uso (`instrument`, `rig`, `filter`, scritti in `gear_usage.subject` e passati come stringhe
  da `rigs` e `api/gear_write`) e i campi dei corredi (`rigs.MOUNT`, `DECLARED`,
  scritti in `declarations.field`). Nelle domande per gruppo le risposte sul filtro
  (`signature.FILTER_ANSWERS`, scritte in `declarations` e ripetute in
  `api/models_review_groups.GearFilterAnswer`), i tipi del bersaglio (`catalog`, `name`, `none`:
  `object_answer.read_target`, `unnamed.answer`, ripetuti in `api/models_review_groups`, e
  `unnamed.NONE` riscritto come `Literal["none"]` nel ritorno di `named_by_group`) e i due vuoti
  del cielo (`objects.NOT_YET`, `NOT_FOUND`). Nel sesto lotto il vocabolario di `declarations`
  (`MOSAIC_YES`/`MOSAIC_NO`, ripetuti in `api/models_review_groups.MosaicAnswer`;
  `CAMERA_MONO`/`CAMERA_COLOR`,
  ripetuti in `api/models_review.CameraType`; i tipi di entita' del `CHECK` di
  `declarations.entity_type`, passati anche come stringhe nude), i posti dove si risponde
  (`nights.REVIEW`, `SITE`, `NEVER`, ripetuti in `api/models_nights`) e gli ordini dell'archivio
  (le chiavi di `archive.ORDINI`, ripetute in `api/archive.Sort`).
- **Fra i `noqa: PLR0913`**, questi restano perche' toglierli cambia una firma usata fuori:
  `replace_rows` (`db/replace_table.py`), `walk_dir` (`fits/walk.py`, i sei accumulatori in un oggetto solo),
  `create_app` (`api/app.py`, sei opzioni a parola chiave lette da `__main__`, `tools` e test),
  `scan_store.finish_run` e `upsert_position` e `normalize_rig.mount_for_frame` (chiamati dai
  test), `stages.set_status` e `stage_run.frame_safely` (chiamati da ogni stadio).
  `identify_link.hang` resta per un'altra ragione: togliere `counts` vuol dire contare dopo le
  scritture, e un frame che cade a meta' cambierebbe i conti della ricevuta.
  `archive_page` (`api/archive.py`) resta per un'altra ragione: i suoi otto parametri sono la
  query della rotta, e raccoglierli in una dipendenza di FastAPI e' un cambio di forma (fase 2).
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
- **M1 -- Dall'archivio ai file**: nessuna risposta di Archivio o Notti porta il percorso di un
  frame. Elenco dei file per oggetto, notte e filtro, in CSV e come lista per i programmi di
  elaborazione (PixInsight, Siril) <!-- software-ok: elaborano, non riprendono -->.
- **M2 -- "La cartella ora sta qui"**: le risposte per cartella hanno nella chiave il percorso
  intero (`spine/frame_folder.py`) e una cartella registrata non si sposta (`api/folders.py`);
  cambiare lettera al disco del NAS, o passare a Docker, le perde.
- **M3 -- Formati**: entrano solo `.fits` e `.fit` (`domini/spina.md`); poi `.fts` e `.fz`, poi
  XISF, che N.I.N.A. sa salvare.
- **M4 -- Filtri dell'Archivio** per periodo, camera o corredo, sito (`api/archive.py`).
- **M5 -- Il backup delle risposte** (*Le dichiarazioni dell'utente non si esportano*, nel
  Parcheggio) va agganciato all'impronta del frame e alla grafia dell'header, non alla notte o al
  percorso: piu' facile dopo S2.

L'ordine: le prove che mancano e *L'archivio dice cose false*; poi S1-S4, prima delle
velocita' che toccano gli stessi pezzi (Applica, fuso di casa, riletture in `row_of`), che con
S1 e S2 spariscono in parte; poi la fase 2 del refactor, con le velocita' e i doppioni che
restano; poi M1, M2, M4, M3; M5 dopo S2.

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

### Macchine che non guardano

- **Promesse con la prova a meta', o senza.** Delle tabelle *Cosa chiede l'utente* dei contratti,
  ogni prova nominata esiste e passa, ma alcune righe sono provate a meta' o senza prova. Le
  peggiori: **un pezzo scritto a mano e poi nominato dai file** non deve diventare un doppione con
  le ore spartite (nessuna prova; la riga di `attrezzatura.md` cita il verso opposto); **la
  scansione a cadenza sul NAS** (`ASTROLOG_SCAN_EVERY_MIN`, `backend/astrolog/__main__.py`) non la
  legge nessuna prova, e rotta spegnerebbe la scansione in silenzio; **una correzione sulla scheda
  resiste a una nuova lettura** e' provata per pixel e colore della camera, non per gli altri
  campi; **l'ordine "dal piu' ripreso" dell'Attrezzatura** (`spine/gear_usage.py`) si prova con un
  oggetto solo (`test_a_piece_says_what_you_shot_with_it`, citata da `attrezzatura.md`): con due
  oggetti di ore diverse l'ordine non e' controllato. Piu' piccole: i totali delle Notti in una
  query sola, promessi in `notti.md`, che nessuna prova conta; il catalogo ("le ore non si
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
- **L'ordine "piu' frame prima" dei siti in Da confermare (`spina.md`) non ha una prova.**
  `api/review_page.py` (`unclear_coordinates`) ordina per frame, ma `test_review_nights.py` sceglie
  il sito per numero di frame e non guarda mai la posizione: tolto l'ordine, la suite resta verde.
  Rimedio: un test che chieda `[n["frames"] for n in notti(review(client))] == [2, 1]`.
- **L'ordine "piu' frame prima" degli oggetti in Da confermare (`spina.md`) non ha una prova.**
  `api/review_page.py` ordina per (in dubbio, frame, nome), ma `test_the_ones_to_decide_come_first`
  guarda solo che i dubbi stiano in cima: tolto `-o.frames`, la suite resta verde. Rimedio: un test
  con due oggetti dello stesso livello e frame diversi, ordinati per frame decrescenti.
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
- **Una promessa d'intestazione senza macchina:** `backend/astrolog/api/models_review_groups.py`
  promette che ogni gruppo porta chiave e `answer`; oggi e' vero anche per `MosaicCandidate`, ma
  nessuna prova lo controlla.
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
- **Promesse del mosaico senza rosso**: "l'app propone e non fonde niente" e' provata solo sulla
  proposta; il pannello senza rotazione e' provato solo nella geometria
  (`backend/tests/test_mosaic_geometry.py`), non nel raggruppamento.
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
  della barra** chiede tutta Da confermare (`GET /review`, che costruisce tutte le sezioni: 3,3 s
  su un archivio gonfiato a 5.000 voci per famiglia) per mostrare un numero, a ogni pagina e a
  ogni ritorno sulla finestra (`frontend/src/main.tsx` crea il client senza `staleTime`); un conto
  leggero non deve scrivere in due case il predicato di cosa e' una domanda aperta. Dei lettori di
  Da confermare, la tendina dei corredi e l'elenco degli oggetti contano ancora ogni frame a ogni
  apertura. Piu' piccoli: i frame per cartella in `GET /folders`; `stages.pending_by_stage` che
  conta `measure`, stadio che non gira mai (la sua chiave esce in `GET /pipeline/status`:
  toglierla cambia la risposta); gli errori di una lettura letti tutti per tagliarne
  una pagina (`api/scan.py`). Ogni ricalcolo tolto entra in un contratto, o in una prova che
  confronta cio' che e' scritto con cio' che le regole direbbero (`tests/test_header_asks.py`).
- **La normalizzazione tiene in mano camera, copia e marchio di ogni frame in coda per tutto il
  giro** (`spine/normalize.py`, `_before_the_round`; `spine/copies.py`): su 5.800 frame sintetici
  il picco e' 2.653 KB contro 1.174 del giro doppio, con tempo e query piu' bassi. Pesa alla prima
  lettura di un archivio grande; si rimisura su un NAS vero prima di decidere un rimedio.
- **Una risposta sul tipo riscrive il segno dell'attesa di ogni frame senza tipo**
  (il trigger di `declarations` in `schema.sql` riscrive tutto l'archivio), dove basterebbero quelle
  della cartella, che `declare` non ha: le trova `apply_answer`, subito dopo.
- **Alle notti manca un indice.** La query della pagina valuta i tre conteggi su tutte le notti e
  ordina in una tabella temporanea prima del `LIMIT`: su 1.000 notti e 40.000 frame 12,81 ms, che
  con `CREATE INDEX nights_date ON nights(night_date DESC, id DESC)` diventano 1,05, anche a
  pagina 10.
- **Il totale dell'archivio viaggia in ogni pagina dello scorrimento delle Notti**:
  `nights.archive_totals` fa una scansione piena (14,6-19 ms su 40.000 frame) a ogni "mostra
  altre", e conta solo la prima. Rimedio: i totali solo alla prima pagina.
- **Rispondere a N gruppi in un Applica costa N letture dell'archivio.** Ogni risposta ritrova il
  suo gruppo rifacendo il lettore da capo dentro la transazione (`row_of` rifa' `by_signature` in
  `spine/signature_page.py`, `by_group` in `spine/unnamed.py`, o `by_folder` in `spine/typeless.py`), e poi `requeue`
  rilegge il gruppo, calcolando anche i soggetti per buttarli. Su ~21.000 frame sintetici: cartelle
  senza nome 124 ms con una risposta, 9,6 s con cento. Rimedio: leggere ogni lettore una volta per
  Applica.
- **Una risposta sul filtro rimette in coda tutti i frame senza matrice della sua camera, anche
  quelli che il filtro lo scrivono** (`_OF_CAMERA` in `spine/unfiltered.py`, chiamato da
  `api/review_write_folders._sensor`): 6.558 per 10 su un caso costruito, misurato quando la
  risposta era per camera.
- **Unire due grafie di una camera rifa' tutti i frame della camera che resta**
  (`apply_answers` in `api/review_write.py`): 6.990 in coda per 432 cambiati, 6,0 s contro ~0,6.
  Rimedio: rimettere in coda la tenuta solo se la risposta le cambia qualcosa.
- **Cambiare il fuso di casa tiene il database dentro la richiesta**, e il tempo cresce coi frame
  che cambiano data (`spine/home_nights.py`): il grosso e' `unnamed.assign` frame per frame. Su un
  archivio grande senza coordinate una scrittura del worker puo' avvicinarsi al `busy_timeout`
  (`db/connect.py`). Rimedio: portare il lavoro fuori dalla richiesta. Scegliere il gruppo una
  volta per notte, camera e telescopio non e' un refactor: `assign` confronta ogni frame col
  puntamento di chi ha aperto il gruppo, frame dopo frame, e i gruppi cambierebbero.
- **I file senza tipo di una cartella detta di calibrazione si rileggono a ogni scansione**:
  saltati alla porta non hanno una posizione, e il pre-controllo incrementale non li riconosce
  (`spine/scan.py`). Rimedio: ricordare i file saltati con percorso, dimensione e data.
- **Il backend non comprime niente**: `StaticFiles` e' montato nudo (`api/page.py`) e nessun
  middleware comprime. Il foglio di stile viaggia per 57,9 kB invece di 10,4, e la previsione ora
  per ora e' la risposta piu' pesante; conta sul NAS guardato dal telefono. Rimedio: una riga di
  `GZipMiddleware`, per tutte le risposte.
- **Cercare il catalogo di ASTAP costa una lettura di cartella a ogni domanda** (`GET /settings`,
  `PATCH /settings`, `GET /solver`): 5,2 ms per 1.492 voci su disco locale; su una condivisione di
  rete sarebbe un'altra cosa. Rimedio: tenere la risposta per un po' (una cache: meccanismo
  nuovo, fuori dal refactor).

### Doppioni -- lo stesso pezzo scritto piu' volte

- **`rigs._pezzo_id` e' `gear.instrument_id` scritta due volte.** Vive in `rigs` perche' `gear`
  importa `rigs`: va in un modulo che tutti e due possono importare.
- **I soggetti di un mosaico si leggono in due posti** (`_most_poses` in
  `spine/mosaic_describe.py`, `_SUBJECTS` in `spine/mosaic_proposals.py`): la stessa giunzione
  frame-pannelli, una per il piu' frequente e una per l'insieme.
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
- **I pavimenti di Bortle 4 e 5 nella fonte del foglio vanno portati a quelli della norma**
  (`units.BORTLE_FLOORS`, voce *Bortle scale* di Wikipedia): `4 = 20,80 · 5 = 19,25` al posto di
  `20,40` e `19,10`. Il commento di `.as-bortle` in `frontend/src/stili/astrolog.css` e' gia'
  corretto qui, con l'impronta di `tools/controlli_veste.py`, per eccezione all'ADR 0012 decisa da
  Marco: la correzione va chiesta a Claude Design, perche' la prossima consegna non la riporti
  indietro.
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
- **Barra**: il nome del sito nel piede porta alla sua scheda (`domini/navigazione.md`); su
  telefono si decide cosa apre il pulsante "Sezioni", o si corregge il contratto; il contatore di
  Da confermare con una lettura sua (*Una lettura non calcola mai*, sopra).
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

- **Mosaici, dichiarazioni e archivio, dopo la fase 1**: `archive._PANNELLI` e' assegnato due
  volte (il pezzo di `WHERE` sui pannelli di una riga, poi la query dei pannelli in fondo al
  file): il primo vale solo perche' `_OGGETTI_DELLA_RIGA` lo legge prima che il secondo lo
  copra; due nomi. `declarations.learn` (`target_key`) e `confirm` (`key`) accettano
  `str | None` perche' `object_answer.declare_object` e `unnamed.declare` passano `slug or name`
  da `resolved`, che torna due opzionali; un `None` cadrebbe sul `NOT NULL`: lo toglie un
  bersaglio risolto tipato `str`. `declarations.values_of` torna `list[Any]` (righe che `rigs`
  spacchetta in coppie con `dict()`): coppie tipate quando la riga avra' una forma. Le pose e i
  pannelli di `mosaic` e `mosaic_geometry` restano `dict[str, Any]`, non `db/row.Row`, perche'
  `identify_geometry.frame_shape`/`frame_radius_deg` leggono con `.get` (un `sqlite3.Row` non ce
  l'ha, e i test passano dict senza i lati): passare a `[]` cambia comportamento, quindi aspetta.
  `mosaic_geometry` non e' uno stadio: quando il mosaico lo diventera', entra nel contratto di
  indipendenza in `backend/pyproject.toml`. Due righe di `archive.py` passano i 100 caratteri con
  la ragione del `noqa` dopo il codice. La docstring di
  `nights.still_reading` dice "`measure`, which nobody runs yet": invecchia quando uno stadio lo
  lancera'. Regole dette due volte: "righe e conta usano una condizione sola" (docstring di
  `archive` e di `_dove`); `COLLATE NOCASE` (`archive.ORDINI` e `choices`); "sta qui perche' la
  leggono piu' stadi" e "una chiave che sopravvive, mai l'id di riga" (docstring di
  `declarations`, poi `FOLDER_TYPE` e `declare_coordinates`).
- **Domande per gruppo e oggetti, dopo la fase 1**: `row_of` e' la stessa riga
  (`next(iter(by_...(conn, only=key)), None)`) in `signature_page`, `unnamed` e `typeless`,
  e l'ordine "il piu' numeroso in cima" (`-frames`, `key`) e' riscritto in `signature_page`,
  `unnamed` e `frame_folder.counted`; "un grezzo senza bianchi o `None`" e'
  `unnamed._written` e di nuovo a mano in `signature_page._card`. Due regole senza test: in
  `unnamed.assign` un frame senza puntamento non entra in un gruppo della stessa notte aperto con
  un puntamento (tolta la condizione, la suite resta verde e due bersagli prendono una risposta
  sola); `signature_page.row_of` non ricostruisce la pagina intera per ogni risposta (costo al
  quadrato delle schede), e nessun test di costo lo tiene. Regole dette piu' volte: "i frame gia'
  risposti tornano in coda, cosi' un ripensamento vale" nei `requeue` di `signature`, `unfiltered`
  e `unnamed`; gli invarianti
  del nome in `objects.NAME_COLUMNS` e `display_name` ripetono `docs/domini/spina.md` senza
  rimandarci.
- **La base di `api`, dopo la fase 1.** Senza test: i 409 di `POST /pipeline/run`
  (`no_folders`, `no_readable_folders`, `worker_busy`) e il suo 200 "niente da avviare" a corsa
  in giro; `POST /pipeline/stop` a worker fermo; `GET /pipeline/status` con una scansione fermata
  prima della prima cartella; `create_app` con un catalogo che solleva al caricamento. Un solo
  `except` in `app._load_catalog` copre il catalogo e le due tabelle derivate
  (`gear_usage.write`, `object_candidates.write`): se cadono queste, il log dice che il catalogo
  non si e' caricato, ed e' falso, e le tabelle restano vecchie fino al catalogo dopo. Riprendi
  butta il `ScanAllStarted` di `start_scan_all`, quindi le cartelle saltate in parte non si
  dicono. `GET /settings` non ha docstring (contratto OpenAPI vuoto); `GET /settings` e
  `GET /solver` cercano il solver sul disco a ogni lettura (~7,9 ms contro ~1,5): una lettura che
  calcola. I tag OpenAPI dei router sono in italiano (fase 2). Doppioni: `[Stage(n, f) for ...]`
  in `pipeline.run` e `work.after`; i tre verbi del bottone scritti a mano due volte in
  `frontend/src/Scansiona.tsx` invece del tipo generato; regole dette due volte ("riprendere
  rilegge le cartelle", il perche' delle ricevute, "una regola, non un elenco" in `app._is_open`
  e `page.is_page`, "la rotta di ripiego si registra per ultima", i perche' di `solver_found` e
  `solver_where` ripetuti dalle rotte del solver, i commenti italiani su
  `PipelineStatus.pending` e `.action`).
- **Il testo di `no_readable_folders`, in una fetta che tocca lo schermo.** Il 409 di
  `POST /pipeline/run` e `POST /scan` scatta anche quando tutte le cartelle sono gia' in
  scansione (`scan_running`), ma `frontend/src/i18n/it.ts` e `en.ts` (riga 47) dicono solo che non
  si riescono a leggere: un doppio clic su Scansiona mostra "non si riesce a leggere". Il testo
  deve dire anche il caso della scansione gia' in corso.
- **`objects.by_key` cerca slug e nome primario con un `OR`**: un nome fuori catalogo scritto
  come uno slug (`OBJECT = m-31`) e un oggetto di catalogo con quello slug danno due righe, e
  vince la prima che SQLite trova. Misurato: col piano di query di oggi vince lo slug anche
  inserendo prima l'oggetto fuori catalogo, quindi il caso non nasce; un `ORDER BY` che metta lo
  slug davanti lo renderebbe una regola invece di un piano.
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
  lo Stop prima di consegnare lo stadio. `start_scan` e `start_scan_all` puliscono un avvio
  fallito con due forme diverse (un `except` con `isinstance`, due `except` con `_pulisci`). A
  fine suite un worker puo' ancora lanciare l'ASTAP vero della macchina e stampare "can't create
  new thread at interpreter shutdown": dipende dai tempi, visto una volta e poi in nessuna di
  quattro corse ripetute.
- **La revisione in `api`, dopo la fase 1.** Il contratto di `POST /review/apply` promette
  "tutte le risposte o nessuna" e 409 `none_filter_exists`, e nessun test lo prova: nessun corpo
  misto con una risposta valida e una rifiutata, nessun filtro "nessun filtro" doppio passando da
  Applica. Regole dette piu' volte: "una risposta a cio' che non esiste
  piu' e' una pagina vecchia: 404" in `review_write_folders` e nel contratto; quali filtri sono una domanda, due volte in `review.py`; il "ripensamento che
  sposta" in `review_write._answer_where` e in `coordinates.frames_at`; l'ordine per distanza
  vera in `review_page` e in `place.by_distance`.
- **Le rotte di scrittura, dopo la fase 1.** Codici d'errore scritti nel contratto e mai provati
  da un test (i test guardano solo lo stato HTTP, o non arrivano al caso): 409 `root_unreachable`
  di browse, 409 `folder_exists` col suo `folder_id`, 404 `folder_not_found` (`api/folders.py`);
  409 `folder_retired`, 404 `scan_run_not_found` (`api/scan.py`); 409 `none_filter_exists`, 422
  `not_a_mount` (`api/gear_write.py`); e la prima registrazione di una cartella che risponde
  `reactivated: false`. Regole dette due o tre volte: "prima l'avvio, poi le ricevute" (`api/scan.py`); il
  criterio delle camere simili e "il no si scrive col nome dell'altra" in `lookalike` (modulo,
  `lookalikes`, `answer_all`, `_bare_name`, un commento) e in `docs/domini/spina.md`; "le stesse
  funzioni di Da confermare" in `gear_write` (modulo, due rotte) e in
  `docs/domini/attrezzatura.md`; "`frames` viene dal database" in `folders` e in
  `FolderOut.frames`.
- **Le rotte di lettura, dopo la fase 1.** `create_site` e `edit_site` (`api/sites.py`)
  prendono `sqlite3.IntegrityError` su tutta la transazione, non solo sull'`INSERT`/`UPDATE` del
  nome: un vincolo violato in `_make_default`, nei `requeue` o in `home_nights.follow_home`
  risponde 409 `site_name_taken`, che e' falso, e l'errore vero non va nel log (il contratto ora
  dice "409 se il nome e' gia' di un altro sito"). Le docstring delle rotte hanno preso la prosa
  della docstring di modulo, e ripetono nell'OpenAPI cio' che i modelli dicono gia': cosa perde
  una notte di tendenza (`weather` e `WeatherNightOut`), il piede con posto e classe (`tonight`
  e `SiteSkyOut`), `still_reading` (`nights` e `models_nights`). In `api/weather.py` la ragione
  del `noqa: S608` di `_CIELO` e' scritta due volte in due righe.
- **I modelli di revisione e attrezzatura, dopo la fase 1: le regole ripetute ora stanno
  nell'OpenAPI.** I commenti diventati descrizioni portano in `schema.d.ts` regole scritte molte
  volte: "un gruppo gia' risposto resta in pagina per cambiare idea" (otto modelli di
  `models_review_groups`), "si risponde con la chiave stabile, mai col numero di riga" (in quasi
  ogni `key` di `models_review*`), "`null` finche' non e' contato" in tre modelli di `models_gear`, le
  descrizioni di `key`, `night`, `integration_s` e `untimed` uguali fra gruppi, "Checked here so
  the OpenAPI declares it" in due validatori. Rimedio: la regola nella docstring del modulo o
  del modello padre, e i campi che rimandano. Senza test: `OpticslessAnswer.optics` che rifiuta
  una risposta vuota o di soli spazi (il 422 di `pattern`).
- **I modelli delle pagine, dopo la fase 1**: `Night.frames` e `ArchiveObject.frames` hanno la
  stessa descrizione parola per parola nell'OpenAPI, e quelle di `untimed` sono quasi uguali (il
  significato ha casa nel glossario); il limite `Field(ge=0, le=100)` della Luna e' scritto in
  `MoonOut` e di nuovo in `MoonThatNight`, che dice di condividerlo ma condivide solo `PhaseKey`.
- **Le rotte di lettura di `api`, dopo la fase 1**: `api/weather._seeing` e il ciclo di `weather`
  scrivono a mano `"meteoblue"` e `"7timer"` accanto a `fetches.Source`; `MeteoblueKeyOut` e
  `MeteoblueKeyIn` stanno in `api/weather_key.py` e non in `models_weather`. Regole dette due
  volte: "l'ordine lo decide il backend" nei moduli `api/archive` e `api/nights`; il Bortle che
  passa da `units.bortle_of` in `api/tonight._sito` e `api/sites._out`.
- **Da confermare, dopo la fase 1**: il 409 `none_filter_exists` di `POST /review/apply` e'
  scritto nel contratto ma nessun test lo prova.
- **L'attrezzatura, dopo la fase 1**: le docstring di `rigs.find_rig` e `rigs.RigExistsError`
  scrivono a mano il 5 % di `units.FOCAL_TOLERANCE`; "la scheda dell'utente vince su file e cielo"
  e' detta in `camera_sky`, `camera_specs` e `gear.camera_specs`, ma vive solo in
  `gear.camera_specs`.
- **Frame senza tipo, dopo la fase 2**: "risolto e' una foto, senza stelle una calibrazione" e'
  detta in `typeless` e nella descrizione OpenAPI di `api/models_review_groups` (toglierla di li'
  cambia lo schema).
- **Attrezzatura, dopo la fase 1**: `rigs.declared_mount` riscrive la query di `rigs._rig`
  (`RIG_ROWS` per id) invece di chiamarla; `filters_used.of` e `idlist` accettano anche chiavi di
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
- **Le dichiarazioni dell'utente non si esportano ne' si reimportano**: nomi, correzioni e
  risposte vivono solo nel database, e ricrearlo le perde (`tools/reset_db.py` le porta via).
  Rimedio: un file solo del dichiarato, reimportabile; doveva nascere con la seconda pagina, che
  c'e'.
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
- **La cartella viva come `EXISTS` non paga**: nelle domande sull'attrezzatura e sul nome
  `frame_folder.JOIN` e un `EXISTS` costano lo stesso.

### Idee

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
