# La spina -- contratto

La spina e' la catena che trasforma cartelle di FITS in un archivio interrogabile: **scan
-> normalize -> solve -> identify -> group** (e `measure`, che nel grafo della spina vecchia non
ha lavoro: e' nato nella pipeline nuova, [`misure.md`](misure.md)). Non e' una linea ma un grafo: ogni
stadio lavora su cio' che per lui manca (`frame_stages`), e la ripresa e' sempre "cio' che
manca", mai "dal file N". Lo schema sta in `backend/astrolog/schema.sql`; il disegno nei
contratti di `backend/pyproject.toml`. Le decisioni ereditate da old/ che riguardano questo
dominio sono state assorbite qui e tolte da `ereditato.md` man mano.

Ogni stadio ha il suo contratto: [`scan`](spina-scan.md), [`normalize`](spina-normalize.md),
[`solve`](spina-solve.md), [`identify`](spina-identify.md), [`group`](spina-group.md); `measure`
in [`misure.md`](misure.md). Qui cio' che vale per tutta la catena: identita', grafo, worker,
Da confermare.

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Tutto quello che dico all'app sta in un file accanto al database, riscritto dopo ogni mia risposta, e dalla scansione solo quando cambia il campione di una cartella (Marco, 25/10/2026); se il database si perde, all'avvio me lo propone e lo rimette, e le pagine tornano come prima; l'Esporta non porta le chiavi dei servizi ne' il percorso di ASTAP; un file che non e' un backup si rifiuta; una cartella tornata senza frame si riconosce dal suo campione (ADR 0017) | `test_every_write_of_the_user_rewrites_the_file_and_a_new_database_gets_it_back`, `test_a_database_recreated_before_start_is_offered_the_file`, `test_a_database_in_use_is_not_offered_and_cannot_be_overwritten`, `test_declining_starts_from_scratch`, `test_a_scan_writes_the_file_only_for_a_new_sample`, `test_the_export_carries_no_service_key_and_no_solver_path`, `test_an_export_imported_elsewhere_adds_without_deleting`, `test_a_file_that_is_not_a_backup_is_refused`, `test_the_answers_keep_their_keys_and_the_folder_its_sample`, `test_a_restored_folder_without_frames_is_recognised_by_its_sample`, *su un database nuovo chiede di rimetterle, prima del primo avvio* (`frontend/tests/backup.test.tsx`) |
| Riaprendo l'app non parte nessun lavoro da solo; sul NAS la scansione gira ogni ora solo se chi lancia l'app lo chiede (`ASTROLOG_SCAN_EVERY_MIN=60`); c'e' sempre il pulsante Scansiona, nella barra in alto di ogni pagina | `test_worker_no_autostart_and_stop_when_idle_is_a_noop`, `test_no_autostart_and_precheck_409s`, `test_scan_schedule_nas`, `test_the_nas_scan_cadence_reaches_the_app` |
| Due scansioni insieme non si pestano: la seconda riceve "gia' in corso" | `test_scan_lock_stop_and_the_button_verb` |
| Una pagina aperta mentre l'app lavora in sottofondo non cade con "database is locked", anche su Windows con l'antivirus: l'app tiene il database aperto finche' gira, e il file accanto all'archivio non resta gonfio per questo | `test_closing_a_request_is_never_the_last_close`, `test_the_wal_shrinks_back_while_a_connection_stays_open` |
| Alla fine della scansione vedo le domande che l'app non sa risolvere da sola, e gli oggetti: con "Applica" le risposte diventano le regole dell'archivio. L'attrezzatura non e' una domanda: la vedo e la correggo nell'Attrezzatura | `test_review_lists_what_was_found`, `test_review_only_new_things` |
| Il conto delle cose da confermare scende quando **rispondo**, non quando guardo: Applica scrive solo le risposte, e non spegne una domanda che ho lasciato li' (ADR 0014, S4) | `test_only_the_filters_the_app_does_not_know_are_asked`, `test_apply_without_answers_silences_no_object`, `test_answering_a_doubt_closes_it` |
| Una pagina aperta prima di un aggiornamento, che manda un campo di ieri (`seen`), si sente dire 422 e non scrive niente | `test_an_answer_with_a_field_we_do_not_know_is_refused` |

## Le decisioni

**Un'identita' sola, decisa alla scansione.** `frame_hash` = sha256 delle dimensioni e di
64 KB di pixel presi dal **centro** del blocco dati (l'offset letto dal file, anche a piu'
pagine): un accesso in piu' per file, quasi gratis, e stabile a una riscrittura
dell'header (l'elaborazione riscrive anche i pixel: la copia calibrata e' un frame
distinto, e `normalize` decide che e' una copia per data, camera ed esposizione). Il centro
perche' un frame registrato ha i bordi a zero e un sensore puo' avere l'overscan: li' due
frame diversi possono coincidere, al centro c'e' il rumore. Il pre-controllo incrementale
e' (cartella, percorso relativo, dimensione, mtime al millisecondo).

**La spina e' un grafo, e gli archi stanno nei dati.** `stages.DEPENDS` dice chi dipende da
chi (group <- normalize, identify; identify <- solve, normalize; measure <- solve) e
`invalidate(frame_ids, from_stage)` e' l'unica via per rimettere `pending` gli stadi a
valle: ogni dichiarazione dell'utente la chiama. `running` non esiste nel DB: l'"in corso"
vive nel worker, e un processo che muore non lascia righe appese.

**Il dichiarato si aggancia a chiavi che sopravvivono**: per un frame la sua impronta, per un
oggetto il nome pulito o la voce di catalogo, per una notte (sito, data). Mai a un numero
di riga: un reset ricrea il rilevato e le dichiarazioni restano vere.

**Un worker, un thread, unico scrittore.** Vive nel processo del backend (uno solo da
impacchettare su tre bersagli); esegue gli stadi in sequenza; ASTAP gira come sottoprocesso
(nella pipeline nuova piu' d'uno insieme: meta' dei core fisici, mai oltre un quarto della RAM, ADR 0033) e restituisce file nella cache, mai scritture nel DB. Stop cooperativo fra un frame e
l'altro, a transazione chiusa: "fermare ferma, non trasforma". Un solo processo `uvicorn`,
niente `workers`. Il lock per cartella si prende dopo i pre-controlli e lo rilascia il
worker a fine corsa (non a fine stadio: la normalizzazione lavora ancora su quei frame),
comunque vada.

**Commit per frame.** Un'interruzione lascia un prefisso coerente, mai un DB a meta'.

**Il progresso vive in memoria, la ricevuta nel DB** (`scan_runs`), e c'e' un canale solo:
`POST scan` risponde subito con l'id della corsa, `GET /pipeline/status` porta l'ultimo
evento, la ricevuta e il verbo del pulsante -- 1-3 s mentre gira, 60 s da fermo, zero a
scheda nascosta: e' il ritmo che la pagina dovra' tenere. Vale per il desktop, per un'altra
scheda e per il telefono allo stesso modo. La corsa (quali stadi, in che ordine) la compone
la spina, e in un posto solo: `run.queue` prende gli stadi che servono, aggiunge quelli che
devono seguirli (`identify` si porta dietro `group`: un frame che cambia oggetto cambia sessione) e li mette nell'ordine
della catena. Le rotte dicono **cosa** serve -- la scansione di una cartella, cio' che ha
residuo quando si preme Avvia, cio' che una risposta in Da confermare ha toccato -- e mai in
che ordine: quando la decidevano in tre, i tre non dicevano la stessa cosa.

**Le date nel DB sono in una forma sola**: UTC ISO 8601 con i millisecondi, qualunque cosa
scriva il software (SGP a sette decimali, ASIAIR senza millisecondi, un fuso esplicito): il
grezzo resta nell'header salvato.

**Il NAS senza login non e' senza guardia**: l'app risponde solo agli host ammessi
(`localhost`, e sul NAS quelli dichiarati), e sul desktop la finestra porta una chiave di avvio
che le altre applicazioni della macchina non hanno: obbligatoria su ogni rotta dell'API
(`X-AstroLog-Token`), non sui file della pagina, assente sul NAS; copia nel file `token` della
cartella dati, 0600 (ADR 0002, 0038). Una copia sola dell'app sugli stessi dati (lucchetto
all'avvio, ADR 0010).

**Dove stanno i dati** (`platformdirs`): Windows `%LOCALAPPDATA%\AstroLog`, Mac
`~/Library/Application Support/AstroLog`, Docker `/data`. Dentro: `astrolog.db`, `cache/`,
`log/`. Il DB non va mai su una condivisione di rete; le cartelle dei FITS si'.

**Il primo avvio** ha la sua casa in `sito.md`; alla fine, con almeno una cartella, la prima
scansione parte da sola (Issue #18). L'attrezzatura non si dichiara li': si vede nell'Attrezzatura.

**Da confermare: solo cio' che l'app non puo' sapere** (Marco, 25/9/2026: un pezzo nuovo non e'
una domanda, si vede nell'Attrezzatura). Dell'attrezzatura restano due domande: i filtri che l'app
non riconosce, e due grafie che hanno l'aria di essere la stessa camera. Poi le *schede
dell'oggetto*, una per gruppo di frame -- un oggetto trovato, o frame senza nome e senza cielo --:
in cima quelle che chiedono una risposta; quelle che l'app sa, su cui non c'e' niente da
scegliere, stanno chiuse, e si aprono a pagine (Marco, 27/9/2026). E le domande sui **gruppi
di frame**, una per ogni cosa che l'app non puo' sapere:
il sito, e l'attrezzatura che i file non dicono. Quante sezioni siano lo dice `ReviewOut`, non questa riga: un numero scritto qui
direbbe il falso alla prossima domanda che nasce. L'ordine fisso delle sezioni lo tiene la pagina:
prima gli strumenti, poi come si montano, poi il dove e il quando, poi il cielo. Senza nessun sito,
*Frame senza sito* dira' «Per rispondere serve almeno un sito: si aggiunge nelle Impostazioni.» con
«Apri le Impostazioni» (Marco, 17/10/2026; oggi manca). Dentro ogni sezione, prima i
gruppi che toccano piu' frame (`api/review.py`, `api/review_page.py`; prove
`test_the_most_used_filters_come_first`, `test_a_question_per_group_with_the_largest_first`,
`test_a_question_per_camera_with_the_largest_first`; degli oggetti
`test_the_ones_to_decide_come_first` prova solo che quelli in dubbio stanno in cima; per l'ordine
per frame degli oggetti e per i siti la prova manca, vedi la Issue #13). Le decisioni si
prendono cliccando e **"Applica" le scrive in un colpo solo**: diventano dichiarazioni e
regole (`header_aliases`) valide per tutto l'archivio, non per la sola scansione. **Applica
scrive solo le risposte** (ADR 0014, S4): niente si conferma guardandolo. Non blocca: i frame
sono gia' in archivio, rispondere migliora i nomi.

**Due rotte, non venti.** `GET /review` porta tutta la pagina in una risposta: le grafie che
sembrano un pezzo solo, i filtri che l'app non riconosce e quelli fra cui si sceglie la risposta, i
setup fra cui si sceglie, gli oggetti coi
conteggi, **i gruppi di frame su cui l'app chiede** -- ognuno con la sua chiave stabile, quanti
frame vale e la risposta gia' data, se c'e' --, quante domande aspettano una risposta, e se
l'archivio e' ancora senza frame (`empty`: non c'e' niente da chiedere, che non e' "niente da
confermare"; `test_the_page_says_when_the_archive_holds_no_frame_yet`). `POST /review/apply` prende tutte le
decisioni insieme, le scrive in una transazione sola e **fa ripartire il lavoro sui frame
toccati**: chi risponde vede i conti aggiornati in pochi secondi, non alla prossima
scansione. I frame non toccati non si rilavorano.

**Un oggetto si chiede solo col dubbio** (ADR 0014, S4): `identity_confidence = 'low'`, senza
risposta (`review_page.asks`). Non si chiede cio' che l'app sa: nome e cielo concordi (`certain`)
e una sigla del catalogo nell'header senza cielo (`high`, Marco 6/10/2026). Si chiede un nome
che il catalogo non conosce, e senza catalogo lo e' ogni nome. Un dubbio senza candidati si
risponde scrivendo il nome, quindi rispondendo a tutto il conto torna a **zero**. La risposta fa
nascere l'oggetto `user`, che non si chiede piu'. Prima Applica confermava cio' che la pagina
aveva mostrato (`seen`, una dichiarazione `confirmed`): spariti, e con loro l'avviso
dell'oggetto nuovo. **Il nome che si da' a un setup resta una dichiarazione**, con la chiave
(ottica, camera, focale): la riga di `rigs` e' rilevata e un'unione di due grafie la cancella, il
nome invece deve tornare quando la spina ricostruisce lo stesso setup.

**Vedere non e' rispondere** (Marco, 14/9/2026): sul suo archivio un Applica a vuoto spegneva
**58** voci, e **sette** erano domande aperte. Con S4 un Applica a vuoto non spegne niente.
I numeri di riga di quelle tabelle **non si riusano** (`AUTOINCREMENT` in `schema.sql`): i filtri
si rispondono col numero, e un numero riciclato darebbe a una riga la risposta scritta per
quella di prima.

**Il lavoro che aspetta si puo' far partire**: `POST /pipeline/run` avvia cio' che e' rimasto
in coda. Senza, una risposta data mentre il worker era occupato aspetterebbe la prossima
scansione.

## Cosa NON fa

Non modifica, rinomina o cancella un FITS da sola: escludere un frame, spostarlo in `scartate/`
ed eliminarlo e' un gesto dell'utente nella zona di selezione, con conferma, che sopravvive alle
scansioni (ADR 0032, 0033). Non cataloga i file di calibrazione.
Non sorveglia le cartelle in continuo. Non riparte da solo all'apertura. Non vota (ADR 0032).
Da confermare non risponde a un file solo, non annulla un'unione, non tiene la cronologia delle
risposte e non chiede quale dei due file e' l'originale.
