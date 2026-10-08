# L'Attrezzatura -- contratto

**Con cosa hai ripreso**, e quanto. L'Archivio racconta gli oggetti, le Notti le serate; qui ci
sono i **pezzi**: telescopi, camere, montature, filtri, e i **corredi** con cui li hai messi
insieme. E' il consuntivo di cosa ti e' servito davvero, non un magazzino di cose possedute. Le
parole vengono da [`glossario.md`](glossario.md) -- *strumento*, *corredo*, mai "setup" ne'
"equipaggiamento"; come le ore si contano e perche' le copie non valgono sta in
[`archivio.md`](archivio.md), che ne e' la casa; dove sta la voce nella barra, in
[`navigazione.md`](navigazione.md).

## Cosa chiede l'utente

Le prove del backend stanno in `backend/tests/test_api_gear.py` (cio' che la pagina mostra) e in
`backend/tests/test_api_gear_write.py` (i gesti); quelle del frontend si chiamano col loro titolo
e stanno in `frontend/tests/attrezzatura.test.tsx` e, per il gesto *Aggiungi strumento*, in
`frontend/tests/attrezzatura-aggiungi.test.tsx`.

| richiesta | prova |
|---|---|
| Apro Attrezzatura e vedo i pezzi che possiedo, raccolti per genere | `test_the_page_lists_the_gear_you_own`; *elenca i pezzi che possiedi, raccolti per genere* |
| Di ogni pezzo vedo quante ore e quanti frame ci ho fatto, e in quante notti | `test_a_piece_says_how_much_you_shot_with_it`, `test_the_hours_of_a_piece_come_from_its_rigs` |
| Uno stesso pezzo montato su due corredi non mi raddoppia le ore | `test_a_piece_on_two_rigs_does_not_count_its_hours_twice` |
| E vedo cosa ci ho ripreso, dal piu' ripreso | `test_a_piece_says_what_you_shot_with_it`, `test_what_a_piece_shot_comes_most_shot_first`; *un pezzo dice cosa ci hai ripreso* |
| Un corredo mi dice ottica, camera e focale, e **quanto cielo inquadra davvero** | `test_a_rig_says_the_sky_it_really_frames`, `test_the_sky_of_a_rig_is_the_middle_value_not_the_average`, `test_a_frame_that_did_not_say_its_field_does_not_drag_the_others`; *un corredo dice quanto cielo inquadra* |
| Una camera i cui file non dicono il pixel me lo mostra ricavato dal cielo, e dice che e' ricavato; se i file o io lo diciamo, vince quello | `test_the_pixel_is_the_median_of_what_the_sky_measured`, `test_the_gear_page_reads_the_pixel_from_the_sky`, `test_what_the_user_writes_wins_on_the_page`, `test_a_camera_that_loses_every_solved_pose_forgets_its_pixel`, `test_calibration_answered_takes_back_the_pixel_its_sky_gave`, `test_normalize_writes_it_at_the_end_of_its_round`, `test_the_solver_writes_it_at_the_end_of_its_round`; *il pixel ricavato dal cielo si dice ricavato, e quello dei file vince* |
| La pagina si apre senza rifare i conti, anche su un archivio grande: quanto e' servito ogni pezzo lo scrive la spina quando lavora le pose, e un pezzo che scrivo io ha i suoi numeri subito | `test_the_page_reads_what_was_written_not_the_frames`, `test_every_stage_that_moves_poses_writes_the_usage_at_the_end`, `test_the_page_counts_nothing_and_the_writer_asks_per_page`, `test_a_piece_written_by_hand_says_its_hours_at_once`, `test_a_piece_not_yet_counted_says_so_and_not_that_the_files_are_silent`, `test_the_rewrite_is_all_or_nothing`, `test_a_stopped_round_writes_what_it_did`, `test_a_round_that_breaks_writes_what_it_did`, `test_a_stage_with_nothing_to_do_does_not_count_again`, `test_a_new_catalog_rewrites_the_names_it_gives`, `test_calibration_answered_takes_its_night_object_and_sky_off_the_gear`; *un pezzo non ancora contato dice che si sta contando, non che i file tacciono* |
| Un corredo di cui l'app non ha ancora riconosciuto le pose non mi mostra una scala inventata | `test_a_rig_that_never_shot_says_nothing_about_the_sky`; *un corredo di cui non si sa quanto inquadra non scrive una scala* |
| La montatura compare, e dove mancherebbero le ore capisco **perche'** | `test_a_mount_has_no_hours_and_the_page_says_why`, `test_a_mount_no_frame_carries_says_so_even_where_others_have_hours`; *la montatura dice perche' non ha ore*, *una montatura che nessuna posa porta, in un archivio dove altre ce l'hanno, non dice zero* |
| Un filtro mi dice che banda lascia passare, e quanto e' larga | `test_a_filter_says_which_band_it_passes` |
| Fra i miei filtri non trovo "nessun filtro", che non e' una cosa che possiedo | `test_no_filter_at_all_is_not_a_filter_you_own` |
| I miei filtri stanno nell'ordine dei filtri, lo stesso di tutta l'app | `test_the_gear_page_lists_your_filters_in_the_one_order` (`backend/tests/test_filter_order.py`) |
| Le copie calibrate che tengo accanto agli originali non mi raddoppiano le ore | `test_a_rewritten_copy_is_not_another_hour_of_gear` |
| Un frame che non dice quanto e' durato non diventa zero ore | `test_a_frame_without_a_time_is_not_zero_hours_of_gear` |
| Se ancora non ho niente, capisco cosa fare invece di trovare una pagina rotta | `test_an_empty_gear_page_is_an_answer_not_an_error`; *a mani vuote dice cosa fare, non nessun risultato* |
| La ruota, il focheggiatore e la camera di guida che il mio programma scrive li trovo gia' li', **con le loro ore** | `test_the_pieces_a_frame_names_come_from_the_header_too`, `test_every_frame_says_which_of_them_it_used`, `test_a_piece_the_files_name_on_every_frame_has_its_hours` |
| Creo a mano un pezzo che i file non nominano: una guida, un riduttore, una montatura | `test_you_can_add_a_piece_the_files_never_named`, `test_a_piece_is_born_with_its_card`; *aggiungo un pezzo che nessun file nomina, scegliendone il genere* |
| E quello che scrivo io non fa un doppione il giorno che i file lo nominano | `test_a_piece_you_wrote_is_the_one_the_files_bring_later`, `test_a_name_you_already_own_is_a_refusal_not_a_second_piece`, `test_the_same_name_in_another_kind_is_another_piece` |
| Un pezzo nuovo, trovato nei file o scritto da me, non e' una domanda: lo vedo qui | `test_a_piece_you_wrote_yourself_is_not_a_question`, `test_review_only_new_things` |
| Creo a mano un **filtro** o un **corredo**, anche prima di averci ripreso | `test_you_can_write_a_filter_you_have_not_used_yet`, `test_you_can_write_a_rig_before_shooting_with_it`; *scrivo a mano un filtro, con la sua banda*, *scrivo a mano un corredo, con ottica e camera fra i miei pezzi e la focale* |
| E sono quelli che i file porteranno, non un doppione | `test_a_filter_you_wrote_is_the_one_the_files_bring_later`, `test_a_rig_you_wrote_is_the_one_the_files_bring_later` |
| Un corredo che ho scritto io resta anche senza frame; uno che l'app aveva trovato nei file e a cui una mia risposta ha tolto tutti i frame sparisce, invece di restare con zero ore | `test_a_rig_written_by_hand_stays_even_without_poses`, `test_the_answer_gives_the_optics_and_the_poses_join_the_rig_that_has_it` (`backend/tests/test_review_gear.py`) |
| Un filtro scritto col nome dei miei file prende le pose mono, e quelle a colori restano OSC | `test_a_filter_written_by_hand_takes_the_mono_frames_and_leaves_the_colour_ones_osc`, `test_a_mono_frame_that_writes_the_app_name_goes_to_the_filter_written_by_hand`, `test_a_colour_frame_stays_osc_after_a_filter_written_by_hand`, `test_a_colour_frame_that_writes_the_app_name_stays_osc_after_a_filter_written_by_hand`, `test_a_colour_frame_that_writes_the_app_name_stays_osc_after_a_rename` |
| Un filtro senza banda, un nome che ho gia' o che e' gia' la grafia di un mio filtro, o un filtro che ho gia' col nome che gli da' l'app, un corredo che ho gia' o fatto di pezzi sbagliati si rifiutano e me lo dicono | `test_a_filter_needs_a_name_you_do_not_own_and_its_band`, `test_a_name_that_is_already_the_spelling_of_another_filter_is_refused`, `test_a_filter_you_already_have_under_the_app_name_is_not_written_twice`, `test_a_rig_you_have_or_not_made_of_optics_and_camera_is_refused`, `test_a_rig_you_already_have_is_refused`, `test_a_rig_is_made_of_an_optics_and_a_camera_you_own`; *un corredo che ho gia' si rifiuta, e me lo dice* |
| Il corredo che ho scritto non sparisce se unisco due grafie della sua ottica o della sua camera, e se quello tenuto ce l'ha gia' ne resta uno | `test_a_rig_you_wrote_survives_the_merge_of_its_camera`, `test_a_merge_into_a_rig_you_already_have_keeps_one` |
| Il nome che scrivo per uno strumento non parte se passo per filtro o corredo e torno | *il nome scritto per uno strumento non parte dopo un giro su filtro o corredo* |
| Do un nome a un corredo, e correggo la scheda di un filtro -- marca, modello, nome -- da qui | `test_a_rig_gets_its_name_from_the_gear_page`, `test_the_card_of_a_filter_is_written_from_the_gear_page`; *do un nome a un corredo*, *correggo la marca di un filtro*, *dico che un filtro e' lo stesso di un altro, fra quelli che l'API offre* |
| Dico da qui che due grafie sono lo stesso pezzo, o lo stesso filtro, e la scansione dopo non le separa piu' | `test_two_pieces_are_merged_from_the_gear_page_too`, `test_a_merged_recognised_filter_does_not_come_back`, `test_a_renamed_recognised_filter_does_not_come_back`, `test_a_colour_frame_stays_osc_after_a_rename`; *unisco due grafie dello stesso pezzo, solo fra quelle che l'API offre* |
| Un'unione che non ha senso si rifiuta e me lo dice | `test_a_merge_the_spine_refuses_is_said`, `test_a_filter_is_never_merged_into_or_from_no_filter`, `test_a_filter_is_merged_only_into_one_with_a_known_band`, `test_a_merge_into_a_filter_that_is_gone_says_the_page_is_old`, `test_a_catalog_model_that_does_not_exist_is_refused` |
| Correggo la scheda di uno strumento dalla pagina in cui lo guardo | `test_you_can_correct_a_card_without_leaving_the_page`, `test_renaming_a_piece_teaches_the_old_spelling`; *correggo la scheda di un pezzo dalla pagina in cui lo guardo* |
| E quello che dico vince su quello che dicono i file | `test_what_you_declare_about_a_camera_is_what_the_page_shows` |
| Mentre compilo, quello che scelgo resta scelto | *cio' che scelgo in una scheda resta scelto*, *cambiando genere non porto con me i campi del genere di prima* |
| E col lavoro in corso non scrivo a meta' | `test_you_cannot_write_gear_while_the_archive_is_being_read`, `test_a_busy_worker_is_not_an_error_for_whoever_answered` |
| I campi che mi chiede una scheda sono quelli del suo genere | `test_the_page_knows_which_fields_a_kind_asks_even_without_owning_one`; *la scheda chiede i campi del genere che sta guardando, e li decide il backend* |
| Se il mio programma scrive la montatura, la montatura ha le sue ore senza che io dica niente | `test_the_mount_the_files_name_is_carried_by_every_frame`, `test_a_mount_carried_by_the_frames_has_their_hours`, `test_a_frame_without_a_rig_still_takes_the_mount_its_file_names`; *una montatura portata dalle pose ha le sue ore* |
| Dove i file tacciono, scelgo la montatura dalla scheda del corredo, e le sue ore compaiono | `test_a_mount_declared_on_a_rig_is_carried_by_all_its_frames`, `test_a_rig_gets_its_mount_from_its_card_and_its_frames_go_back_to_be_read`; *scelgo la montatura di un corredo dalla sua scheda*, *un corredo dice su che montatura sta, e la voce vuota torna ai file* |
| Quello che dico sul corredo vince sui file, e se lo tolgo tornano i file; una montatura nuova che i file nominano nasce lo stesso | `test_what_you_declare_wins_over_the_mount_the_files_name`, `test_a_new_mount_the_files_name_is_born_even_on_a_rig_you_gave_one` |
| Una posa che arriva alla montatura per due strade conta una volta, e ridare la stessa montatura non rimette niente in coda | `test_a_frame_that_reaches_the_mount_two_ways_counts_once`, `test_the_same_mount_again_sends_nothing_back_to_be_read` |
| Nessuna montatura si indovina, nemmeno se ne possiedo una sola | `test_with_one_mount_only_a_rig_the_files_do_not_name_stays_without` |
| Solo una montatura che possiedo puo' essere la montatura di un corredo | `test_only_a_mount_can_be_the_mount_of_a_rig`, `test_only_a_mount_you_own_can_be_the_mount_of_a_rig`; *senza montature da scegliere il corredo non offre il gesto* |
| Rinominare o unire una montatura non la stacca dai corredi, e se due corredi diventano uno vince la montatura di quello che resta | `test_a_mount_renamed_or_merged_stays_the_mount_of_its_rigs`, `test_two_rigs_that_become_one_keep_the_mount_of_the_one_kept` |
| Dalla ricerca apro un pezzo o un filtro (`/attrezzatura?pezzo=strumento-<id>`, `filtro-<id>`): la sua riga e' segnata e in vista | *con ?pezzo= la riga di quel pezzo e' segnata, e nessun'altra*, *un filtro si apre allo stesso modo* |

## Le decisioni

**Si mostra solo cio' che l'app possiede davvero.** Ogni numero di questa pagina viene dai tuoi
file o da una tua risposta; niente si prende da internet (lo dice gia' lo schema), niente si
stima. Dove un numero non c'e', la pagina **dice perche'** invece di scrivere uno zero: uno zero
e' un dato, e qui sarebbe falso.

**Le ore si contano in una casa sola** (`spine/counts.py`): lo stesso frammento dell'Archivio e
delle Notti, allargato al pezzo, al corredo e al filtro invece che ricopiato. Le copie riscritte non
contano, e un frame senza durata non e' zero.

**Un pezzo puo' nascere in due modi, e resta uno solo** (scelta di Marco, 21/9/2026). L'app lo
riconosce dai file, oppure lo crei tu -- **qualunque genere**, compreso un corredo che non ha
ancora ripreso. Quando poi i file portano quella stessa cosa, non ne nasce un secondo: un corredo
e' la sua **impronta** (ottica, camera, focale) e un pezzo e' il suo nome dentro il suo genere,
quindi cio' che crei a mano e' esattamente cio' che l'app riconoscera'. Senza questa regola, il
giorno della prima ripresa ti ritroveresti l'elenco doppio.

**E cio' che dici tu non lo sovrascrive nessuno.** Le schede, i nomi e la montatura legata a un
corredo vivono nello strato del dichiarato: la spina riempie cio' che i file dicono, la tua parola
resta.

**Quanto cielo inquadra un corredo si MISURA, non si calcola** (scelta di Marco, 21/9/2026). La
scala in arcosecondi per pixel e il campo inquadrato escono dalle pose che il riconoscitore ha
gia' risolto (`frame_wcs`), prese come **mediana** -- non media: una posa risolta storta, che su
un campo povero di stelle capita, sposterebbe la media e lascia ferma la mediana -- e' cio' che quel corredo ha inquadrato
davvero, riduttore compreso e con la camera montata come la monti tu. Il conto teorico -- focale
e pixel -- direbbe un altro numero su ogni corredo con un riduttore, e sarebbe giusto sulla carta
e sbagliato nel cielo. Un corredo di cui il riconoscitore non ha ancora risolto nessuna posa
non ha una scala, e lo dice -- e non e' lo stesso di "non ha mai ripreso": le pose possono
esserci ed essere ancora in coda.

**Quanto e' servito ogni pezzo lo scrive chi lavora le pose** (Marco, 22/9/2026: una lettura
non calcola mai). Ore, frame, notti, oggetti e cielo di ogni pezzo, corredo e filtro si contano
tutti insieme a fine giro di ogni stadio che cambia le pose -- corredo e filtro, cielo, oggetto,
notte -- **solo se quello stadio ha lavorato qualche posa**, perche' contare un archivio grande costa;
nella risposta "sono file di calibrazione", che stacca notte, oggetto e cielo senza che nessuno
stadio lavori quei frame; e di nuovo all'avvio se arriva un catalogo nuovo, che da' i nomi degli
oggetti
(`spine/gear_usage.py`, tabella `gear_usage`). Un pezzo scritto a mano scrive la sua riga e basta,
senza ricontare l'archivio dentro la richiesta. La pagina li legge e
basta (`spine/inventory.py`), e un contratto in `backend/pyproject.toml` le vieta di contare. Si
riscrive intera in un colpo solo: chi apre la pagina a meta' vede i numeri di prima, mai una tabella
vuota. Fra un gesto che sposta pose -- un'unione -- e la fine del giro che parte subito dopo, la
pagina mostra i numeri di prima; un pezzo nato a meta' giro -- alla prima scansione, per minuti --
dice **conteggio in corso**, che non e' "non indicato nei file".

**Il pixel di una camera si ricava dal cielo quando i file non lo dicono** (Marco, 23/9/2026). La
stessa misura letta all'incontrario: per ogni posa risolta, scala per focale del corredo diviso il
binning, e la camera prende la **mediana**, al centesimo di micron (`camera_sky.write`). Una posa
che non dice il binning non vota: un binning ignoto non vale 1. Lo scrive
chi cambia cio' da cui dipende -- `normalize` e il solver a fine giro, la risposta "sono file di
calibrazione" che stacca il cielo -- e la pagina lo legge e basta. Si
mostra solo dove i file e l'utente tacciono, e dice che e' ricavato: un riduttore che la focale
dell'header non conta lo sposta. Per la stessa ragione non basta a proporre un'unione fra due
grafie, che vuole il pixel noto (`docs/domini/spina.md`).

**Un pezzo arriva alle sue pose per due strade** (22/9/2026). Ottica e camera passano dal
**corredo**: la posa conosce quello, non i suoi pezzi. Ruota portafiltri, focheggiatore e camera di
guida no -- quelli il programma li scrive **sulla singola posa** (`FWHEEL` e `FOCNAME` di N.I.N.A.,
`GUIDECAM` dell'ASIAIR), quindi la posa li porta addosso e le loro ore si sanno. Il legame sta in
una casa sola (`spine/counts.py`), e ore, notti e oggetti di una riga vengono tutti di li': tre
definizioni della stessa riga racconterebbero tre archivi diversi.

**E le ore che l'app non puo' sapere restano nulle, per archivio e non per genere.** Un genere che
la posa nomina entra nel conto **solo se almeno una posa dell'archivio lo nomina**: chi riprende
con un programma che la ruota non la scrive, e se la e' scritta a mano, non ha fatto zero ore --
ha ore che l'app non sa, e la riga lo dice. E' lo stesso pezzo che racconta due cose a due utenti,
e a deciderlo e' cio' che i loro file dicono.

**E non entrano nell'impronta di un corredo.** Un corredo e' ottica + camera + focale: infilarci
la ruota farebbe nascere un secondo corredo a chi ne cambia una, e l'archivio di prima si
spezzerebbe in due senza che nessuno abbia cambiato telescopio.

**Posizione, temperatura e angolo non sono pezzi.** `FOCUSPOS`, `FOCTEMP` e `ROTATOR` stanno
negli stessi header e **oggi non si leggono affatto**: sono misure di una posa, non la scheda di
uno strumento, e il posto dove andranno nascera' con le metriche dei frame.

**La montatura arriva alle pose per due strade, e la tua parola vince** (Marco, 26/9/2026). Dove
il programma la scrive -- l'ASIAIR, in `TELESCOP`, e lo dice il software, mai una lista di nomi --
la posa la porta addosso come la ruota, e le ore si sanno senza chiedere niente. Dove i file
tacciono, la scegli dalla **scheda del corredo**, fra le montature che possiedi: vale per tutte le
sue pose, anche su quelle che il file nomina, e togliendola tornano i file. Sta fra le
dichiarazioni col **nome** della montatura, cosi' una rinomina o un'unione la portano con se', e
una montatura sola per corredo, per costruzione della chiave. Nessuna montatura si indovina: se ne
possiedi una sola, non si da' per scontata. Una montatura che nessuna posa porta dice che nessun
corredo la porta ancora, invece di scrivere zero.

**Niente "da quando ce l'hai"** (Marco, 21/9/2026): non si chiede una data d'acquisto e non si
mostra la prima notte. Contano le ore, cosa ci hai ripreso e com'e' fatto il pezzo.

**Tutti i pezzi insieme, senza sceglierne uno.** Si guarda l'attrezzatura per confrontarla: un
selettore costringerebbe a ricordare cosa aveva l'altro. E' la stessa forma delle pagine sorelle,
e i pezzi di un archivio vero sono una manciata, non mille.

**Un pezzo nuovo non e' una domanda** (Marco, 25/9/2026): che l'abbiano trovato i file o l'abbia
scritto tu, si vede qui, e Da confermare non si riaccende per lui. Da confermare chiede
dell'attrezzatura solo cio' che l'app non puo' sapere -- che filtro e' uno che non riconosce, e se due
grafie che sembrano la stessa camera sono lo stesso pezzo -- e alcune sue risposte scrivono anche qui:
"nessun filtro" scrive mono sulla scheda della camera, "a colori" scrive colore, e la camera scritta
nella scheda della firma diventa un pezzo.

**L'unione passa dalla stessa mano di *Da confermare***: `api/instrument_answer.py`, non una
seconda strada. Due strade vorrebbero dire due verita' sullo stesso pezzo -- le pose rimesse in
coda solo per chi passa dal posto giusto. Ma scrivere un pezzo **non e' un Applica**: non conferma
le domande aperte della pagina delle domande.

**Cio' che scrivi vince sui file, e si vede.** Colore e pixel di una camera vivono fra le
dichiarazioni, non nella colonna che la spina ricalcola a ogni corsa: la pagina legge le une sopra
l'altra, o dopo una correzione continuerebbe a mostrare cio' che dicono i file.

## Cosa non fa ancora, e con cosa arrivera'

**Un filtro e un corredo scritti a mano** (Marco, 21/9/2026) nascono dallo stesso *Aggiungi un
pezzo*: il filtro col nome e la banda, il corredo con ottica, camera e focale obbligatoria -- senza,
i file che la dicono farebbero un secondo corredo. Se il vocabolario darebbe al filtro un altro nome
(`L` diventa `Lum`), il filtro lo impara come una rinomina: la regola si legge dopo il colore, e le
pose mono di chi scrive `L` vengono a lui mentre quelle a colori restano OSC. Se quel nome e' gia'
un tuo filtro, si rifiuta: le pose ci stanno gia', e si rinomina quello. Il corredo sta anche fra le dichiarazioni, perche'
un'unione della sua ottica o della sua camera cancella i corredi e `normalize` rifa' solo quelli con
delle pose. Filtri e corredi si correggono da qui (Marco, 25/9/2026): il nome di
un corredo, la scheda di un filtro, e l'unione di due grafie, di un pezzo o di un filtro -- la
destinazione di un filtro e' uno con la banda nota, la stessa regola della tendina di *Da
confermare*. Un filtro rinominato o unito non rinasce: la regola imparata vale anche sul nome che il
vocabolario da' alla grafia dell'header (`L` diventa `Lum`), e vale dopo il colore, quindi su una
camera a colori `L` resta OSC.

**Cancellare un pezzo non si fa**, e non per dimenticanza: un pezzo che tiene delle pose non si
toglie senza decidere che fine fanno le sue ore. Sta in [`coda.md`](../coda.md).

Restano fuori per scelta: il **valore** dei pezzi e il **registro di manutenzione** (provati e
scartati nel progetto di prima, e la ragione vale ancora: questa pagina dice come hai ripreso,
non quanto hai speso); lo **slot** di un filtro nella ruota e il **peso del corredo contro la
portata della montatura**, che chiedono dati che oggi nessuno ha; e il **colore del corredo**, che
e' gia' deciso ([`ereditato.md`](ereditato.md)) e nascera' quando servira' a un grafico, non
prima.
