# L'Attrezzatura -- contratto

**Con cosa hai ripreso**, e quanto. L'Archivio racconta gli oggetti, le Notti le serate; qui ci
sono i **pezzi**: telescopi, camere, montature, filtri, e i **setup** con cui li hai messi
insieme. E' il consuntivo di cosa ti e' servito davvero, non un magazzino di cose possedute. Le
parole vengono da [`glossario.md`](glossario.md) -- *strumento*, *setup*, mai "corredo" ne'
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
| In testa l'indice: i setup a carte con ore, focale, barra e le 10 parti a tacche ("{n} da indicare"), i componenti un gruppo per genere; sul telefono l'indice e' la prima schermata e il dettaglio si apre a pagina intera (tavola v82) | `test_a_rig_without_a_name_is_titled_by_its_pieces_without_the_brand`, `test_a_named_rig_is_titled_by_its_name`, `test_the_ten_slots_come_in_the_card_order_and_say_what_is_missing`, `test_a_chosen_part_fills_its_slot`; *l indice mostra i setup a carte, con ore, focale e le parti da indicare*, *prima l indice, poi il dettaglio a pagina intera e la via per tornare* |
| Scelgo un setup e vedo com'e' fatto: le parti coi loro pezzi e «Seleziona», il campo a confronto con gli altri setup e la Luna, i nove conti o cio' che manca, l'anello dei filtri, il treno ottico che apre i suoi pezzi (tavola v82) | `test_the_train_draws_the_pieces_the_numbers_read`, `test_the_fields_come_widest_first_on_the_same_frame_with_the_moon`, `test_the_filter_ring_is_in_proportion_to_the_frames`, `test_the_backfocus_says_the_train_and_who_requires_it`, `test_the_load_says_the_weight_and_the_payload_it_divides`, `test_the_guide_scale_says_which_guide_it_used`; *il campo si confronta con gli altri setup e con la Luna, in percento dall'API*, *i dati del setup dicono ogni conto, o cosa gli manca*, *l anello dei filtri e' in proporzione ai frame, coi nomi accanto*, *i distanziali si scelgono insieme, e partono tutti*, *toccare un pezzo lo apre fra i componenti* |
| Dopo un salvataggio che rimette dei frame in coda la pagina me lo dice ("{n} frame da rielaborare", Chiudi) | *dopo un salvataggio che rimette dei frame in coda, la pagina lo dice e si chiude* |
| Di ogni setup, parte e filtro vedo **solo le ore** (Marco, 11/10 e 24/10/2026); frame, notti e oggetti che la pagina vecchia mostra ancora vanno via al porting | `test_a_piece_says_how_much_you_shot_with_it`, `test_the_hours_of_a_piece_come_from_its_rigs` |
| Uno stesso pezzo montato su due setup non mi raddoppia le ore | `test_a_piece_on_two_rigs_does_not_count_its_hours_twice` |
| Un setup mi dice ottica, camera e focale, e **quanto cielo inquadra davvero** | `test_a_rig_says_the_sky_it_really_frames`, `test_the_sky_of_a_rig_is_the_middle_value_not_the_average`, `test_a_frame_that_did_not_say_its_field_does_not_drag_the_others`; *un setup dice quanto cielo inquadra* |
| Una camera i cui file non dicono il pixel me lo mostra ricavato dal cielo, e dice che e' ricavato; se i file o io lo diciamo, vince quello | `test_the_pixel_is_the_median_of_what_the_sky_measured`, `test_the_gear_page_reads_the_pixel_from_the_sky`, `test_what_the_user_writes_wins_on_the_page`, `test_a_camera_that_loses_every_solved_pose_forgets_its_pixel`, `test_calibration_answered_takes_back_the_pixel_its_sky_gave`, `test_normalize_writes_it_at_the_end_of_its_round`, `test_the_solver_writes_it_at_the_end_of_its_round`; *il pixel ricavato dal cielo si dice ricavato, e quello dei file vince* |
| La pagina si apre senza rifare i conti, anche su un archivio grande: quanto e' servito ogni pezzo lo scrive la spina quando lavora i frame, e un pezzo che scrivo io ha i suoi numeri subito | `test_the_page_reads_what_was_written_not_the_frames`, `test_every_stage_that_moves_poses_writes_the_usage_at_the_end`, `test_the_page_counts_nothing_and_the_writer_asks_per_page`, `test_a_piece_written_by_hand_says_its_hours_at_once`, `test_a_piece_not_yet_counted_says_so_and_not_that_the_files_are_silent`, `test_the_rewrite_is_all_or_nothing`, `test_a_stopped_round_writes_what_it_did`, `test_a_round_that_breaks_writes_what_it_did`, `test_a_stage_with_nothing_to_do_does_not_count_again`, `test_a_new_catalog_rewrites_the_names_it_gives`, `test_calibration_answered_takes_its_night_object_and_sky_off_the_gear`; *un pezzo non ancora contato dice che si sta contando, non che i file tacciono* |
| Un setup di cui l'app non ha ancora riconosciuto i frame non mi mostra una scala inventata | `test_a_rig_that_never_shot_says_nothing_about_the_sky`; *un setup di cui non si sa quanto inquadra non scrive una scala* |
| La montatura compare, e dove mancherebbero le ore capisco **perche'** | `test_a_mount_has_no_hours_and_the_page_says_why`, `test_a_mount_no_frame_carries_says_so_even_where_others_have_hours`; *la montatura dice perche' non ha ore*, *una montatura che nessuna posa porta, in un archivio dove altre ce l'hanno, non dice zero* |
| Un riduttore o un'ottica di guida che nessun setup porta lo dice, invece di "non indicato nei file": i file non li scrivono mai, il rimedio e' sceglierli su un setup (Marco, 12/10/2026) | `test_a_piece_only_a_rig_can_carry_says_no_rig_carries_it`; *un riduttore e una guida che nessun setup porta lo dicono, ognuno col suo genere* |
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
| Creo a mano un **filtro** o un **setup**, anche prima di averci ripreso | `test_you_can_write_a_filter_you_have_not_used_yet`, `test_you_can_write_a_rig_before_shooting_with_it`; *scrivo a mano un filtro, con la sua banda*, *scrivo a mano un setup, con ottica e camera fra i miei pezzi e la focale* |
| E sono quelli che i file porteranno, non un doppione | `test_a_filter_you_wrote_is_the_one_the_files_bring_later`, `test_a_rig_you_wrote_is_the_one_the_files_bring_later` |
| Un setup che ho scritto io resta anche senza frame; uno che l'app aveva trovato nei file e a cui una mia risposta ha tolto tutti i frame sparisce, invece di restare con zero ore | `test_a_rig_written_by_hand_stays_even_without_poses`, `test_the_answer_gives_the_optics_and_the_poses_join_the_rig_that_has_it` (`backend/tests/test_review_gear.py`) |
| Un filtro scritto col nome dei miei file prende i frame mono, e quelli a colori restano OSC | `test_a_filter_written_by_hand_takes_the_mono_frames_and_leaves_the_colour_ones_osc`, `test_a_mono_frame_that_writes_the_app_name_goes_to_the_filter_written_by_hand`, `test_a_colour_frame_stays_osc_after_a_filter_written_by_hand`, `test_a_colour_frame_that_writes_the_app_name_stays_osc_after_a_filter_written_by_hand`, `test_a_colour_frame_that_writes_the_app_name_stays_osc_after_a_rename` |
| Un filtro senza banda, un nome che ho gia' o che e' gia' la grafia di un mio filtro, o un filtro che ho gia' col nome che gli da' l'app, un setup che ho gia' o fatto di pezzi sbagliati si rifiutano e me lo dicono | `test_a_filter_needs_a_name_you_do_not_own_and_its_band`, `test_a_name_that_is_already_the_spelling_of_another_filter_is_refused`, `test_a_filter_you_already_have_under_the_app_name_is_not_written_twice`, `test_a_rig_you_have_or_not_made_of_optics_and_camera_is_refused`, `test_a_rig_you_already_have_is_refused`, `test_a_rig_is_made_of_an_optics_and_a_camera_you_own`; *un setup che ho gia' si rifiuta, e me lo dice* |
| Il setup che ho scritto non sparisce se unisco due grafie della sua ottica o della sua camera, e se quello tenuto ce l'ha gia' ne resta uno | `test_a_rig_you_wrote_survives_the_merge_of_its_camera`, `test_a_merge_into_a_rig_you_already_have_keeps_one` |
| Il nome che scrivo per uno strumento non parte se passo per filtro o setup e torno | *il nome scritto per uno strumento non parte dopo un giro su filtro o setup* |
| Do un nome a un setup, e correggo la scheda di un filtro -- marca, modello, nome -- da qui | `test_a_rig_gets_its_name_from_the_gear_page`, `test_the_card_of_a_filter_is_written_from_the_gear_page`; *do un nome a un setup*, *correggo la marca di un filtro*, *dico che un filtro e' lo stesso di un altro, fra quelli che l'API offre* |
| Dico da qui che due grafie sono lo stesso pezzo, o lo stesso filtro, e la scansione dopo non le separa piu' | `test_two_pieces_are_merged_from_the_gear_page_too`, `test_a_merged_recognised_filter_does_not_come_back`, `test_a_renamed_recognised_filter_does_not_come_back`, `test_a_colour_frame_stays_osc_after_a_rename`; *unisco due grafie dello stesso pezzo, solo fra quelle che l'API offre* |
| Un'unione che non ha senso si rifiuta e me lo dice | `test_a_merge_the_spine_refuses_is_said`, `test_a_filter_is_never_merged_into_or_from_no_filter`, `test_a_filter_is_merged_only_into_one_with_a_known_band`, `test_a_merge_into_a_filter_that_is_gone_says_the_page_is_old`, `test_a_catalog_model_that_does_not_exist_is_refused` |
| Correggo la scheda di uno strumento dalla pagina in cui lo guardo | `test_you_can_correct_a_card_without_leaving_the_page`, `test_renaming_a_piece_teaches_the_old_spelling`; *correggo la scheda di un pezzo dalla pagina in cui lo guardo* |
| E quello che dico vince su quello che dicono i file | `test_what_you_declare_about_a_camera_is_what_the_page_shows` |
| Mentre compilo, quello che scelgo resta scelto | *cio' che scelgo in una scheda resta scelto*, *cambiando genere non porto con me i campi del genere di prima* |
| E col lavoro in corso non scrivo a meta' | `test_you_cannot_write_gear_while_the_archive_is_being_read`, `test_a_busy_worker_is_not_an_error_for_whoever_answered` |
| I campi che mi chiede una scheda sono quelli del suo genere | `test_the_page_knows_which_fields_a_kind_asks_even_without_owning_one`; *la scheda chiede i campi del genere che sta guardando, e li decide il backend* |
| Se il mio programma scrive la montatura, la montatura ha le sue ore senza che io dica niente | `test_the_mount_the_files_name_is_carried_by_every_frame`, `test_a_mount_carried_by_the_frames_has_their_hours`, `test_a_frame_without_a_rig_still_takes_the_mount_its_file_names`; *una montatura portata dalle pose ha le sue ore* <!-- glossario-ok --> |
| Dove i file tacciono, scelgo la montatura dalla scheda del setup, e le sue ore compaiono | `test_a_mount_declared_on_a_rig_is_carried_by_all_its_frames`, `test_a_rig_gets_its_mount_from_its_card_and_its_frames_go_back_to_be_read`; *scelgo la montatura di un setup dalla sua scheda*, *un setup dice su che montatura sta, e la voce vuota torna ai file* |
| Quello che dico sul setup vince sui file, e se lo tolgo tornano i file; una montatura nuova che i file nominano nasce lo stesso | `test_what_you_declare_wins_over_the_mount_the_files_name`, `test_a_new_mount_the_files_name_is_born_even_on_a_rig_you_gave_one` |
| Una posa che arriva alla montatura per due strade conta una volta, e ridare la stessa montatura non rimette niente in coda | `test_a_frame_that_reaches_the_mount_two_ways_counts_once`, `test_the_same_mount_again_sends_nothing_back_to_be_read` |
| Nessuna montatura si indovina, nemmeno se ne possiedo una sola | `test_with_one_mount_only_a_rig_the_files_do_not_name_stays_without` |
| Solo una montatura che possiedo puo' essere la montatura di un setup | `test_only_a_mount_can_be_the_mount_of_a_rig`, `test_only_a_mount_you_own_can_be_the_mount_of_a_rig`; *senza montature da scegliere il setup non offre il gesto* |
| Rinominare o unire una montatura non la stacca dai setup, e se due setup diventano uno vince la montatura di quello che resta | `test_a_mount_renamed_or_merged_stays_the_mount_of_its_rigs`, `test_two_rigs_that_become_one_keep_the_mount_of_the_one_kept` |
| Dalla ricerca apro un pezzo o un filtro (`/attrezzatura?pezzo=strumento-<id>`, `filtro-<id>`): la sua riga e' segnata e in vista | *con ?pezzo= la riga di quel pezzo e' segnata, e nessun'altra*, *un filtro si apre allo stesso modo* |
| Ogni pezzo porta la scheda tecnica del produttore, tipo per tipo, e un filtro la sua (ADR 0021) | `test_the_card_asks_the_makers_sheet_kind_by_kind`, `test_a_filter_carries_its_sheet`, `test_the_closed_words_of_a_card_are_the_schemas` |
| La risoluzione della camera viene dai file, il sensore intero piu' frequente; quella che scrivo vince | `test_the_resolution_is_the_whole_sensor_most_frequent_among_the_files`, `test_the_resolution_i_write_wins_over_the_files` |
| Il setup guida con un'ottica di guida **oppure** una guida fuori asse, e porta tutti i suoi distanziali, con le ore del setup | `test_a_rig_guides_with_a_guide_scope_or_an_oag_never_both`, `test_a_rig_has_all_its_spacers_with_the_rigs_hours`, `test_spacers_follow_a_rename_and_an_empty_list_takes_them_off`, `test_only_a_spacer_is_a_spacer` |
| Il setup fa i suoi conti dalle schede, e dove manca un dato dice quale | `test_the_example_of_the_board_comes_back`, `test_each_number_names_the_first_datum_it_lacks`, `test_the_rig_says_what_it_lacks_then_its_number_once_written` e gli altri di `backend/tests/test_rig_numbers.py` |
| La pagina legge i conti scritti, non li rifa' | `test_the_page_reads_the_numbers_and_never_computes_them` |
| Il backup delle risposte porta la scheda intera | `test_the_backup_carries_the_new_fields` |

## Le decisioni

**Si mostra solo cio' che l'app possiede davvero.** Ogni numero di questa pagina viene dai tuoi
file o da una tua risposta; niente si prende da internet (lo dice gia' lo schema); i conti del
setup partono solo da dati che hai, e lo dicono (ADR 0021, 0033). Dove un numero non c'e', la pagina **dice perche'** invece di scrivere uno zero: uno zero
e' un dato, e qui sarebbe falso.

**Le ore si contano in una casa sola** (`spine/counts.py`): lo stesso frammento dell'Archivio e
delle Notti, allargato al pezzo, al setup e al filtro invece che ricopiato. Le copie riscritte non
contano, e un frame senza durata non e' zero.

**Un pezzo puo' nascere in due modi, e resta uno solo** (scelta di Marco, 21/9/2026). L'app lo
riconosce dai file, oppure lo crei tu -- **qualunque genere**, compreso un setup che non ha
ancora ripreso. Quando poi i file portano quella stessa cosa, non ne nasce un secondo: un setup
e' la sua **impronta** (ottica, camera, focale) e un pezzo e' il suo nome dentro il suo genere,
quindi cio' che crei a mano e' esattamente cio' che l'app riconoscera'. Senza questa regola, il
giorno della prima ripresa ti ritroveresti l'elenco doppio.

**E cio' che dici tu non lo sovrascrive nessuno.** Le schede, i nomi e la montatura legata a un
setup vivono nello strato del dichiarato: la spina riempie cio' che i file dicono, la tua parola
resta.

**Quanto cielo inquadra un setup si misura**, e la scala prevista dalla scheda sta accanto (ADR 0021, 0033). La
scala in arcosecondi per pixel e il campo inquadrato escono dai frame che il riconoscitore ha
gia' risolto (`frame_wcs`), presi come **mediana** -- non media: un frame risolto storto, che su
un campo povero di stelle capita, sposterebbe la media e lascia ferma la mediana -- e' cio' che quel setup ha inquadrato
davvero, riduttore compreso e con la camera montata come la monti tu. Il conto teorico -- focale
e pixel -- direbbe un altro numero su ogni setup con un riduttore, e sarebbe giusto sulla carta
e sbagliato nel cielo. Un setup di cui il riconoscitore non ha ancora risolto nessun frame
non ha una scala, e lo dice -- e non e' lo stesso di "non ha mai ripreso": i frame possono
esserci ed essere ancora in coda.

**Quanto e' servito ogni pezzo lo scrive chi lavora i frame** (Marco, 22/9/2026: una lettura
non calcola mai). Ore, frame, notti, oggetti e cielo di ogni pezzo, setup e filtro si contano
tutti insieme a fine giro di ogni stadio che cambia i frame -- setup e filtro, cielo, oggetto,
notte -- **solo se quello stadio ha lavorato qualche frame**, perche' contare un archivio grande costa;
nella risposta "sono file di calibrazione", che stacca notte, oggetto e cielo senza che nessuno
stadio lavori quei frame; e di nuovo all'avvio se arriva un catalogo nuovo, che da' i nomi degli
oggetti
(`spine/gear_usage.py`, tabella `gear_usage`). Un pezzo scritto a mano scrive la sua riga e basta,
senza ricontare l'archivio dentro la richiesta. La pagina li legge e
basta (`spine/inventory.py`), e un contratto in `backend/pyproject.toml` le vieta di contare. Si
riscrive intera in un colpo solo: chi apre la pagina a meta' vede i numeri di prima, mai una tabella
vuota. Fra un gesto che sposta frame -- un'unione -- e la fine del giro che parte subito dopo, la
pagina mostra i numeri di prima; un pezzo nato a meta' giro -- alla prima scansione, per minuti --
dice **conteggio in corso**, che non e' "non indicato nei file".

**Il pixel di una camera si ricava dal cielo quando i file non lo dicono** (Marco, 23/9/2026). La
stessa misura letta all'incontrario: per ogni posa risolta, scala per focale del setup diviso il
binning, e la camera prende la **mediana**, al centesimo di micron (`camera_sky.write`). Una posa
che non dice il binning non vota: un binning ignoto non vale 1. Lo scrive
chi cambia cio' da cui dipende -- `normalize` e il solver a fine giro, la risposta "sono file di
calibrazione" che stacca il cielo -- e la pagina lo legge e basta. Si
mostra solo dove i file e l'utente tacciono, e dice che e' ricavato: un riduttore che la focale
dell'header non conta lo sposta. Per la stessa ragione non basta a proporre un'unione fra due
grafie, che vuole il pixel noto (`docs/domini/spina-normalize.md`).

**Un pezzo arriva ai suoi frame per due strade** (22/9/2026). Ottica e camera passano dal
**setup**: la posa conosce quello, non i suoi pezzi. Ruota portafiltri, focheggiatore e camera di
guida no -- quelli il programma li scrive **sulla singola posa** (`FWHEEL` e `FOCNAME` di N.I.N.A.,
`GUIDECAM` dell'ASIAIR), quindi la posa li porta addosso e le loro ore si sanno. Il legame sta in
una casa sola (`spine/counts.py`), e ore, notti e oggetti di una riga vengono tutti di li': tre
definizioni della stessa riga racconterebbero tre archivi diversi.

**E le ore che l'app non puo' sapere restano nulle, per archivio e non per genere.** Un genere che
la posa nomina entra nel conto **solo se almeno una posa dell'archivio lo nomina**: chi riprende
con un programma che la ruota non la scrive, e se la e' scritta a mano, non ha fatto zero ore --
ha ore che l'app non sa, e la riga lo dice. E' lo stesso pezzo che racconta due cose a due utenti,
e a deciderlo e' cio' che i loro file dicono.

**Il setup dice tutte le sue parti** (Marco, 11/10/2026): oltre a ottica e camera, cio' che i
suoi frame dicono di aver usato -- montatura, ruota, focheggiatore, camera di guida, programma di
ripresa, filtri -- ognuna con quanti frame, copie riscritte escluse. Piu' pezzi dello stesso
genere si elencano tutti, dal piu' usato: nasconderne uno direbbe che non e' mai stato usato. Le
scrive la spina in `rig_parts`, insieme ai conteggi; il nome e' quello del pezzo adesso, non di
quando si e' contato (`test_a_rig_says_every_part_its_frames_used`,
`test_a_rig_used_with_two_of_a_kind_lists_both_most_used_first`,
`test_a_part_renamed_reads_with_its_new_name`). Il programma di ripresa non e' un pezzo: si legge
e basta.

**Una parte si puo' scegliere sul setup** (Marco, 11/10/2026): `PUT
/gear/rigs/{id}/parts/{kind}`, un gesto solo per montatura, ruota, focheggiatore, camera di guida,
riduttore, ottica di guida (`counts.CARRIED`); `piece_id` nullo toglie la scelta. La scelta sta
fra le dichiarazioni del setup col nome del pezzo, quindi segue rinomina e unione, e i frame del
setup tornano a `normalize`. Due regole, in `rigs.OVER_THE_FILE`: la **montatura** scelta vale
su tutti i frame, anche dove il file ne nomina un'altra (26/9/2026); per **gli altri generi** la
scelta riempie solo il silenzio del file -- cio' che i file nominano si rinomina, non si
sostituisce. Riduttore e ottica di guida nessun programma li scrive (`counts.CHOSEN_ONLY`): stanno
sulla posa (`reducer_id`, `guide_scope_id`) solo per scelta, e da li' prendono ore e parti come
gli altri. Ogni parte dice `chosen`, scritto dalla spina in `rig_parts` (la lettura non lo
ricava); una scelta che nessuna posa porta ancora si legge subito, con zero frame, perche' la
rotta riscrive le parti (`gear_usage.write_parts`) (`test_a_part_you_choose_reads_as_chosen_at_once`,
`test_a_wheel_you_choose_fills_only_the_frames_whose_file_is_silent`,
`test_a_part_the_files_never_name_is_carried_once_you_choose_it`). Ottica, camera e focale non si
scelgono: fanno il setup.

**E non entrano nell'impronta di un setup.** Un setup e' ottica + camera + focale: infilarci
la ruota farebbe nascere un secondo setup a chi ne cambia una, e l'archivio di prima si
spezzerebbe in due senza che nessuno abbia cambiato telescopio.

**Posizione, temperatura e angolo non sono pezzi.** `FOCUSPOS`, `FOCTEMP` e `ROTATOR` stanno
negli stessi header e **oggi non si leggono affatto**: sono misure di una posa, non la scheda di
uno strumento, e il posto dove andranno nascera' con le metriche dei frame.

**La montatura arriva ai frame per due strade, e la tua parola vince** (Marco, 26/9/2026). Dove
il programma la scrive -- l'ASIAIR, in `TELESCOP`, e lo dice il software, mai una lista di nomi (Marco, 24/10/2026) --
la posa la porta addosso come la ruota, e le ore si sanno senza chiedere niente. Dove i file
tacciono, la scegli dalla **scheda del setup**, fra le montature che possiedi: vale per tutti i
suoi frame, anche su quelli che il file nomina, e togliendola tornano i file. Sta fra le
dichiarazioni col **nome** della montatura, cosi' una rinomina o un'unione la portano con se', e
una montatura sola per setup, per costruzione della chiave. Nessuna montatura si indovina: se ne
possiedi una sola, non si da' per scontata. Una montatura che nessuna posa porta dice che nessun
setup la porta ancora, invece di scrivere zero.

**Niente "da quando ce l'hai"** (Marco, 21/9/2026): non si chiede una data d'acquisto e non si
mostra la prima notte. Contano le ore e com'e' fatto il pezzo.

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
seconda strada. Due strade vorrebbero dire due verita' sullo stesso pezzo -- i frame rimessi in
coda solo per chi passa dal posto giusto. Ma scrivere un pezzo **non e' un Applica**: non conferma
le domande aperte della pagina delle domande.

**Cio' che scrivi vince sui file, e si vede.** Colore e pixel di una camera vivono fra le
dichiarazioni, non nella colonna che la spina ricalcola a ogni corsa: la pagina legge le une sopra
l'altra, o dopo una correzione continuerebbe a mostrare cio' che dicono i file.

## Cosa non fa ancora, e con cosa arrivera'

**La pagina della tavola v82** (congelata 11/11/2026; supera la v15 del 17/10, indice a sinistra
e "niente campo disegnato ne' tessere"): in testa l'indice a carte, *Setup* (ore, focale, barra,
le 10 parti a tacche) e *Componenti* (un gruppo per genere), sotto il dettaglio di cio' che scegli;
il titolo della pagina e' quello della cornice (la tavola lo nasconde col foglio). Un gruppo senza righe non compare. **Il guscio c'e'** (commit B,
13/11): barra, indice, frame da rielaborare, stati, telefono. Il titolo di una carta senza nome
e le 10 parti (`slots`, `slots_missing`) arrivano dall'API (`spine/rig_card.py`): il titolo e'
il nome dato, se no ottica e camera col modello, o il nome senza la marca scritta sul pezzo, e
«?» al posto del pezzo che manca (come la tavola); la
guida e' una tacca, ottica o fuori asse. **Il dettaglio di un setup c'e'** (commit C1, 13/11):
la carta col nome, «Rinomina», le ore, focale, rapporto e montatura, ottica e camera con le prime
tre voci della scheda (mai il peso); le Parti, ognuna coi pezzi che i file nominano («N frame») o
che hai scelto («(scelta a mano)»), e «Seleziona» col modulo nella riga (il programma di ripresa
lo dicono solo i file: non si seleziona; Salva senza cambiare chiude e non scrive); il Campo
misurato col confronto fra i setup e la Luna, in percento dall'API (`fields`, `moon_pct`: la
cornice e' il campo piu' largo piu' il 15%, mai sotto 0,9°, alta due terzi; li scrive
`gear_usage.write_fields`); i Dati del setup, i nove conti con le parole della tavola o cio' che
manca («manca il pixel della camera»), dove `numbers` porta anche il treno e chi chiede il
backfocus, peso e carico, la guida usata e l'intervallo della scala di guida; l'anello dei Filtri
in proporzione ai frame (`ring_from`, `ring_to`, `passband` sulle parti `filter`). **Il treno
ottico c'e'** (commit C2, 14/11): disegna i pezzi che i conti leggono, la parte scelta se no la
piu' usata, la guida una sola (`pieces`, scritti con i conti da `gear_numbers`); senza ottica o
prima che i conti siano scritti non c'e'. L'esploso e' disegno, non dato: la geometria della
tavola sta in `disegnoDelTreno.ts`, e uno schema ottico non scritto si disegna rifrattore. Se i
nomi di una riga non entrano, le pillole passano al numero con la legenda (Marco, 14/11). Il
gruppo e il modulo di un pezzo arrivano col commit D, che fino ad allora mostra le righe di
prima. Le barre arrivano dall'API
(`bar_pct`: ore sul piu' usato del gruppo, mai sotto 3), scritte con l'uso
(`gear_usage.write_bars`); la Luna piena del campo disegnato e' `moon_deg`, il diametro apparente
medio della NASA (1896″, 0,527°; la tavola scrive 0,52). La scala del campo dice "arcosecondi per
pixel · ricavati dal cielo" (DECISIONI v66 10.2): e' la mediana dei frame risolti. Accanto a un
campo del modulo "dai file" vale solo per i campi che i file dicono (`from_files`: il sensore di
una camera), ogni altro campo scritto e' "inserito". Un filtro
scritto a mano si abbina alla lista standard, senza catalogo dei modelli (ADR 0031, 0033); le
bande si scrivono, anche quelle delle camere a colori.

**La scheda tecnica e i conti del setup** (Marco, 18/10/2026): campi per tipo, formule, soglie e
parole dei conti stanno in [ADR 0021](../adr/0021-dati-completi-dell-attrezzatura.md), che ne e'
la casa; ogni conto compare solo coi suoi dati, e se ne manca uno lo dice ("manca il pixel della
camera di guida"). L'ordine del treno ottico e' solo disegno: i conti non ne dipendono. **Il
backend c'e'** (passo 32): i campi in `instrument_answer.CARD`, i conti in `spine/rig_numbers.py`,
scritti da `spine/gear_numbers.py` dopo ogni scrittura di schede o parti e a fine giro, e letti
dalla pagina in `numbers`; ognuno arriva intero o con `missing` (tipo di pezzo e campo, il primo
che manca). La focale effettiva e' quella del setup, senza ripieghi; la parte che un conto legge
e' quella scelta, altrimenti la piu' usata; la guida e' una, ottica o fuori asse, e sceglierne una
toglie l'altra. I distanziali stanno fra le dichiarazioni del setup, uno per campo
(`spacer:<nome>`), e le loro ore sono quelle dei setup che li portano (`rig_spacers`); se due
setup diventano uno, vincono i distanziali di quello che resta, come la montatura
(`test_two_rigs_that_become_one_keep_the_spacers_of_the_one_kept`). Il bias della camera per lo
SQM (ADR 0022) e' uno per camera e offset, come i file li scrivono: `GET /api/v1/gear/camera-biases`
li elenca tutti, dichiarati o no, coi frame di luce che li portano; `PUT` lo dichiara (404
`camera_not_found` se nessun frame li scrive) e riscrive lo SQM di quei frame; viaggia nel
backup (`camera_biases`) e, ripristinato o importato, riscrive lo SQM come dichiararlo
(`test_an_imported_bias_rewrites_the_sky_brightness_as_declaring_it_does`). La pagina
di oggi non chiede ancora i campi nuovi: arrivano col porting della tavola, insieme alle loro
etichette. "(vuoto:
dai file)" solo sulle parti che i file possono dire (non i distanziali). Il programma di ripresa
e' una parte del setup coi suoi frame, senza ore e senza modulo. Le marche sono testo libero:
"altra…" propone quelle gia' scritte.

**Testi approvati** (Marco, 11/10, 17/10 e 18/10/2026; parola per parola, *setup* al posto di
"corredo", decimali con la virgola come in [`glossario.md`](glossario.md), Marco 6/11/2026):

- uso: solo le ore (sopra); i frame restano accanto alle parti del setup, i filtri del setup in
  proporzione, senza cifre;
- parti: "{parte}: {nome}" coi frame se dai file, "{parte}: {nome} (scelta a mano)", "da
  indicare" se i file tacciono, "{n} da indicare", "Parti", "Seleziona" su ogni parte; il gesto
  di scelta vale per tutte le parti; "aggiungine uno" apre *Aggiungi strumento* col tipo gia'
  scelto; rapporto focale "(calcolato)";
- dettaglio del setup: "Dati del setup", "Dalle schede tecniche degli strumenti.", "Treno
  ottico", "Schema non in scala. Seleziona uno strumento per aprirlo.", "Campionamento", "Schema
  ottico", "Guide fuori asse", "Distanziali", "Apri {nome} fra i componenti"; sotto la Luna del
  campo disegnato "Luna piena, per misura";
- backfocus con la tolleranza: "esatto", "+0.5 mm, in tolleranza", "corto di …", "lungo di …";
  senza tolleranza solo la differenza ("+0.5 mm"), senza pillola;
- modulo: "Tipo: … Cambia", i blocchi "chi è" e "dati tecnici" con "{n} di {m} scritti",
  "altra…" / "Nuova marca", "calcolato" / "dai file" / "inserito" accanto al campo, "Quante
  bande", "Larghezza (nm)", "Pixel (µm)", "servono apertura e focale"; campi nuovi "Schema
  ottico", "Tolleranza del backfocus (mm)" (ottica e riduttore), "Bias (ADU)" (camera);
- rifiuti prima di salvare: "Per salvare serve il nome.", "Per salvare serve almeno una banda.",
  "Per salvare servono ottica, camera e focale effettiva."; unione: "L'unione non è reversibile.";
  "{n} frame da rielaborare", anche dopo il salvataggio, che altrimenti chiude il modulo senza
  messaggio; il numero e' `requeued`: i frame che uno stadio rilegge davvero (mono / a colori di
  una camera, la banda di un filtro, un'unione, una parte scelta, il pixel di una camera, che
  rimanda al solve i frame senza `XPIXSZ`: misurano la focale col pixel della scheda). La tavola
  (v66 10.3) lo vuole anche per sensore, risoluzione, focale e fattore: nessuno stadio legge quei
  campi scritti da te (la risoluzione dei frame viene dai loro header), e un numero che non
  rielabora niente sarebbe falso;
- scansione in corso: Salva spento con "Scansione in corso: si salva al termine." (non
  "potrai"); oggi c'e' solo il rifiuto dopo ("riprova al termine");
- non si legge: "Attrezzatura non disponibile" e "Riprova".

Le etichette proposte il 18/10 per i campi nuovi (Raffreddamento, Risoluzione, Prisma, Passo,
Passi totali, Montato, Per ottiche veloci) valgono come la tavola v82 le scrive.

**Un filtro e un setup scritti a mano** (Marco, 21/9/2026) nascono dallo stesso *Aggiungi un
pezzo*: il filtro col nome e la banda, il setup con ottica, camera e focale obbligatoria -- senza,
i file che la dicono farebbero un secondo setup. Se il vocabolario darebbe al filtro un altro nome
(`L` diventa `Lum`), il filtro lo impara come una rinomina: la regola si legge dopo il colore, e i
frame mono di chi scrive `L` vengono a lui mentre quelli a colori restano OSC. Se quel nome e' gia'
un tuo filtro, si rifiuta: i frame ci stanno gia', e si rinomina quello. Il setup sta anche fra le dichiarazioni, perche'
un'unione della sua ottica o della sua camera cancella i setup e `normalize` rifa' solo quelli con
dei frame. Filtri e setup si correggono da qui (Marco, 25/9/2026): il nome di
un setup, la scheda di un filtro, e l'unione di due grafie, di un pezzo o di un filtro -- la
destinazione di un filtro e' uno con la banda nota, la stessa regola della tendina di *Da
confermare*. Un filtro rinominato o unito non rinasce: la regola imparata vale anche sul nome che il
vocabolario da' alla grafia dell'header (`L` diventa `Lum`), e vale dopo il colore, quindi su una
camera a colori `L` resta OSC.

**Cancellare un pezzo** (Marco, 21/10/2026): si cancella solo un pezzo senza frame. Uno che ne
tiene si rifiuta, e l'app dice chi lo usa e quanti frame: nessuna ora si perde.
`DELETE /api/v1/gear/instruments/{id}` e `/gear/filters/{id}` (`spine/gear_delete.py`): 204; 409
`in_use` coi `frames` e i `rigs` di quei frame; 409 `in_rig` per l'ottica o la camera di un setup
senza frame, che e' fatto di loro; 409 `worker_busy`; 404. Con lui vanno la sua scheda e le sue
scelte nei setup: rinato col nome, riparte vuoto. Prima del gesto la pagina legge da ogni pezzo e
filtro `in_rigs` (setup, frame, scelto), per "Esce anche da {setup}.", e `delete_refused`, lo
stesso rifiuto del DELETE dai frame contati: Elimina spento con "Lo usano {n} frame di {setup}:
nessuna ora si perde. Uniscilo a un altro pezzo, se è lo stesso." (`in_use`) o "Fa parte di
{setup}: un setup è fatto della sua ottica e della sua camera." (`in_rig`, Marco 14/11/2026; la
tavola non ha il caso). Un pezzo non ancora contato lo rifiuta il DELETE, con le stesse parole.

**Il gruppo di un tipo** (commit D, 14/11/2026): righe con la scheda intera, le ore con la barra,
"inserito manualmente" sui pezzi dichiarati. Una montatura che nessun setup porta ha "Seleziona
montatura", che apre la scelta sul setup `rig_for_mount` (il piu' usato ancora senza montatura).
Il filtro porta `passband`, che da' il colore del disco. Sull'ottica `numbers.focal_ratio` e' il
rapporto focale nativo (focale su apertura), accanto a Dawes. Il bias di una camera e' uno per
offset (Marco 14/11/2026: un campo per offset, "Bias (ADU), offset {n}", uno solo senza offset
diversi): `biases` elenca gli offset che i suoi file scrivono, passando dal ponte dei frame (ADR
0045), e `PUT /gear/instruments/{id}/biases` lo scrive su ogni grafia dell'header di quella camera
(404 `offset_not_found`, 409 `worker_busy`). La tendina "Marca" del modulo propone `brands`, le
marche gia' scritte su pezzi e filtri, una per nome senza badare alle maiuscole.

Restano fuori per scelta: il **valore** dei pezzi e il **registro di manutenzione** (provati e
scartati nel progetto di prima, e la ragione vale ancora: questa pagina dice come hai ripreso,
non quanto hai speso); lo **slot** di un filtro nella ruota, che chiede un dato che oggi nessuno
ha (il carico del setup invece entra, ADR 0021, 0033); e il **colore del setup**, che
e' gia' deciso ([`ereditato.md`](ereditato.md)) e nascera' quando servira' a un grafico, non
prima.
