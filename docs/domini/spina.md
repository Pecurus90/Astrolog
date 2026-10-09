# La spina -- contratto

La spina e' la catena che trasforma cartelle di FITS in un archivio interrogabile: **scan
-> normalize -> solve -> identify -> group** (e `measure`, che e' nel grafo e non ha ancora un
lavoro). Non e' una linea ma un grafo: ogni
stadio lavora su cio' che per lui manca (`frame_stages`), e la ripresa e' sempre "cio' che
manca", mai "dal file N". Lo schema sta in `backend/astrolog/schema.sql`; il disegno nei
contratti di `backend/pyproject.toml`. Le decisioni ereditate da old/ che riguardano questo
dominio sono state assorbite qui e tolte da `ereditato.md` man mano.

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Indico una cartella e l'app trova tutti i FITS, anche in sottocartelle profonde, con spazi e accenti nei nomi, senza mai toccare i file | `test_scan_walk_finds_everything_and_never_touches_the_files` |
| I frame compaiono appena letti (nome dell'oggetto, data, filtro, esposizione): la scansione di migliaia di file dura minuti, non ore, anche da NAS | `test_scan_reads_header_only` |
| Se rilancio la scansione, i file gia' visti non si rileggono; un file spostato o rinominato resta lo stesso frame; una copia dello stesso file in due cartelle e' un frame con due posizioni | `test_scan_incremental`, `test_scan_duplicate_header` |
| Un file che sparisce non viene cancellato dall'archivio: e' segnato "non trovato" e torna se ricompare | `test_scan_missing_returns` |
| Dark, flat, bias e stack non entrano nell'archivio e non hanno una vista: la ricevuta li conta per motivo | `test_scan_skips_calibration`, `test_the_receipt_counts_the_skipped_by_reason` |
| Un file senza `IMAGETYP` non si perde: entra come `unknown`, e che file e' lo dice il cielo -- risolto e' una foto, senza stelle una calibrazione -- e se il cielo non sa dire me lo chiede; finche' non si sa **aspetta prima dell'oggetto**, cosi' non diventa ore ne' finisce fra i frame senza nome o senza filtro; se il cielo non l'ha riconosciuto e finisce in una cartella viva che non ha risposto -- spostato, o per una cartella tolta o rimessa -- torna ad aspettare senza ore, e le riprende da se' quando torna in una cartella che ha detto "foto del cielo"; in una cartella detta di calibrazione aspetta senza ore anche se il cielo l'aveva riconosciuto; il cielo che uno stacco gli ha tolto non conta come riconosciuto: in una cartella viva che non lo ferma torna in fila dal cielo, e senza cartella viva aspetta; un file sparito o in una cartella tolta tiene le ore che aveva | `test_scan_unknown_type_enters_and_waits_before_the_object`, `test_a_frame_that_waits_does_not_ask_for_the_filter`, `test_a_frame_moved_where_no_one_answered_waits_again_without_its_hours`, `test_a_frame_moved_into_a_folder_called_calibration_waits_without_its_hours`, `test_a_frame_the_sky_recognised_moved_into_calibration_waits_without_its_hours`, `test_a_frame_moved_back_out_of_calibration_goes_back_to_the_sky`, `test_a_frame_moved_from_calibration_into_a_photo_folder_goes_back_to_the_sky`, `test_putting_back_a_folder_sends_a_frame_that_lost_its_sky_back_to_the_sky`, `test_a_detached_frame_left_without_a_live_folder_keeps_waiting`, `test_a_frame_already_back_in_line_is_detached_all_the_same`, `test_a_frame_the_sky_recognised_keeps_its_hours_where_no_one_said_calibration`, `test_retiring_a_folder_moves_a_frame_that_is_also_elsewhere`, `test_putting_back_a_folder_that_said_photo_gives_the_hours_back`, `test_a_frame_that_goes_back_to_waiting_during_a_run_is_skipped`, `test_a_file_that_is_gone_keeps_its_hours`, `test_retiring_the_folder_keeps_the_hours`, `test_frames_without_stars_are_calibration_and_are_not_asked`, `test_a_frame_the_sky_solves_is_a_photo_and_is_not_asked`, `test_stars_without_a_solution_are_the_sky_that_cannot_say` |
| Detto che una cartella porta file di calibrazione, i file senza `IMAGETYP` che arrivano dopo non entrano affatto, e la ricevuta li conta per motivo -- tranne un file gia' in archivio: spostato li' entra e perde le ore, copiato li' entra come copia e le ore restano finche' l'originale resta dov'era, in una cartella che l'app legge | `test_scan_skips_a_folder_the_user_called_calibration`, `test_the_answer_holds_for_the_files_that_arrive_later_in_that_folder`, `test_a_frame_moved_into_a_folder_called_calibration_waits_without_its_hours`, `test_a_copy_in_a_folder_called_calibration_keeps_the_hours_of_the_original` |
| Che un file senza `IMAGETYP` aspetti e' scritto sulla posa, ed e' sempre cio' che la regola direbbe: appena entrato, dopo il cielo, dopo una posizione che cambia, dopo una risposta, dopo una cartella tolta | `test_a_new_frame_without_type_waits_from_the_start`, `test_a_frame_that_enters_a_folder_answered_light_does_not_wait`, `test_the_sky_moves_the_mark_both_ways`, `test_a_frame_whose_folder_changes_takes_the_answer_of_the_new_one`, `test_a_position_that_changes_file_moves_both_marks`, `test_an_answer_moves_the_mark_of_every_frame_of_its_folder`, `test_retiring_a_folder_moves_a_frame_that_is_also_elsewhere`, `test_a_retire_that_fails_leaves_the_folder_where_it_was` |
| Un file che sta ancora scrivendo, o che non si riesce a leggere, non rompe la scansione: si salta, si conta, si rivede la volta dopo | `test_scan_partial_file`, `test_scan_bad_header_counted` |
| Se punto una galassia grande, non mi dice il puntino accanto | `test_the_subject_is_the_one_that_contains_the_pointing`, `test_the_subject_is_not_the_nearest_one` |
| Punto un oggetto qualunque del catalogo e l'app propone quello, non un suo vicino | `test_pointing_at_a_real_target_proposes_that_target_back` |
| Mi dice cosa c'era **nell'inquadratura** e cosa era solo li' vicino | `test_each_candidate_says_whether_it_is_really_in_the_picture` |
| Su una focale lunga dentro un oggetto grande, l'app lo riconosce lo stesso | `test_a_narrow_field_still_finds_the_big_object_around_it` |
| Un nome che non e' un oggetto del cielo (una cometa, una cartella) non diventa un oggetto sbagliato | `test_what_is_not_moving_is_not_taken_for_moving`, `test_a_comet_never_takes_the_object_behind_it` |
| Quando due bersagli contendono davvero, l'app non tira a indovinare: chiede | `test_two_separate_objects_with_close_scores_are_ambiguous`, `test_no_designation_and_two_contenders_in_the_sky` |
| Non mi chiedera' di scegliere fra un oggetto e la nube che lo avvolge, ma me lo chiedera' fra due bersagli distinti che si sfiorano | `test_a_host_bigger_than_its_guest_is_not_a_rival_either`, `test_containment_far_from_the_frame_is_not_containment` |
| L'app mi dice **cosa ho fotografato**, senza che io scriva niente | `test_a_solved_frame_gets_its_object_with_the_catalog_names` |
| Se il nome che ho scritto e il cielo non concordano me lo chiede, e intanto il frame resta agganciato | `test_the_sky_disagreeing_with_the_name_hangs_the_name_and_asks` |
| Un frame non risolto finisce nel gruppo del suo nome, non in un limbo | `test_an_unsolved_frame_hangs_on_the_name` |
| I frame che l'header non nomina e di cui il cielo non dice niente non spariscono: restano marcati col loro perche' (`no_name_no_sky`), e Da confermare li chiede per gruppo | `test_a_frame_with_no_name_and_no_sky_is_skipped_not_left_pending` |
| Le mie ore su un oggetto non si sparpagliano su due voci | `test_two_frames_of_the_same_galaxy_make_one_object` |
| Quando correggo un'identificazione non torna indietro mai piu' | `test_the_user_answer_is_never_overwritten` |
| Se la cartella di rete cade a meta', l'app si ferma e lo dice: non segna "non trovato" mille file | `test_scan_root_gone_aborts` |
| Una cartella di rete che non risponde non blocca l'elenco delle cartelle: la vedo come non raggiungibile | `test_a_share_that_does_not_answer_does_not_hold_the_list`, `test_a_share_still_being_asked_is_not_asked_again`, `test_many_dead_shares_do_not_make_a_live_folder_unreachable`, `test_a_folder_that_goes_away_reads_unreachable_on_the_next_list` |
| Una cartella senza permessi non blocca le altre: la vedo elencata nella ricevuta | `test_scan_unreadable_dirs` |
| Un file che sta solo online (OneDrive, Dropbox, iCloud) non viene scaricato: si salta, la ricevuta lo conta, e entra quando lo rendo disponibile sul disco | `test_scan_does_not_download_an_online_only_file`, `test_scan_a_pose_left_online_only_is_not_missing` |
| Una sottocartella nascosta resta fuori, ma la ricevuta la nomina | `test_scan_names_the_hidden_folders_it_leaves_out` |
| La cartella del NAS la registro come `\\NAS\Foto` o come disco collegato `Z:`, e la ritrovo con la lettera o il percorso di rete che ho scelto | `test_the_folder_is_saved_in_the_form_the_user_finds_again`, `test_a_network_folder_is_accepted` |
| Aprire le cartelle di rete non apre le zone di sistema, comunque siano scritte, e su qualunque sistema: anche su Mac, dove `/etc` e `/var` sono collegamenti | `test_the_checks_look_at_where_the_path_leads`, `test_a_system_zone_that_leads_elsewhere_is_refused_too`, `test_the_forms_that_would_bypass_the_checks_are_refused`, `test_a_path_that_resolves_to_no_absolute_path_is_refused`, `test_a_folder_that_does_not_answer_is_checked_and_kept_as_written` |
| Sul NAS in Docker scelgo la cartella da un elenco, invece di indovinarne il percorso (rotte e worker; il primo avvio e le Impostazioni le usano) | `test_the_nas_folder_is_chosen_from_a_list`, `test_the_folders_to_choose_from_are_the_ones_the_walk_walks`, *nell elenco del NAS si entra, e si registra la cartella dove sei* (`frontend/tests/wizard-cartelle.test.tsx`); le Impostazioni senza prova (*Per il disegno nuovo*, in `docs/coda.md`) |
| Una cartella raggiunta da un collegamento non fa girare la scansione a vuoto, e la ricevuta la nomina | `test_a_junction_is_not_followed_and_is_named`, `test_a_link_to_a_file_is_not_named_as_a_folder`, `test_the_linked_folders_are_named_in_order`, `test_scan_names_the_linked_folders_it_does_not_follow` |
| Un file che non si riesce a leggere, per qualunque motivo, non ferma la scansione: la ricevuta lo nomina col suo motivo, e resta scritta | `test_scan_bad_header_counted`, `test_a_file_that_breaks_the_reading_is_named_and_the_scan_goes_on`, `test_a_name_the_archive_cannot_write_is_named_and_the_scan_goes_on`, `test_a_pose_that_can_no_longer_be_read_is_not_missing`, `test_scan_stop_leaves_a_coherent_prefix` |
| Se il database non risponde (disco pieno, occupato) la scansione si ferma col suo motivo, invece di contare file sani come non letti | `test_a_database_fault_stops_the_scan_and_the_receipt_says_so` |
| Un guasto uguale su mille file non riempie il log: una traccia per tipo | `test_the_same_unexpected_fault_leaves_one_trace_in_the_log` |
| L'elenco dei file non letti lo leggo a pagine, e lo tiene l'ultima scansione di ogni cartella (e, se quella non e' arrivata in fondo, l'ultima che ci e' arrivata) | `test_the_files_not_read_are_listed_a_page_at_a_time`, `test_only_the_last_scans_of_a_folder_keep_the_names` |
| La ricevuta dice quanti file ha saltato e perche', calibrazioni comprese | `test_the_receipt_counts_the_skipped_by_reason` |
| Mentre scansiona vedo un pulsante che dice cosa fa (Scansiona / Interrompi / Riprendi) e la fase in corso coi suoi numeri veri, e a fine corsa una ricevuta, che resta in Impostazioni / Scansioni (la catena intera delle fasi non ha ancora una pagina) | `test_worker_events_stages_run_in_order_one_at_a_time`, `test_scan_receipt` |
| Fermare ferma entro il file in corso, e non fa partire altro; chiudere la finestra non ferma niente | `test_worker_stop_cooperative`, `test_scan_answers_at_once_and_the_receipt_arrives_in_status` |
| Una lettura fermata prima di cominciare, o che non riesce a partire, non lascia una ricevuta aperta per sempre, che sia di una cartella o di tutte; Riprendi la rilegge lo stesso | `test_resume_reads_one_folder_stopped_before_it_began`, `test_a_start_that_breaks_unexpectedly_leaves_nothing_behind`, `test_a_stop_does_not_leave_receipts_open_forever`, `test_a_busy_worker_leaves_no_folder_locked` |
| La ricevuta di una cartella tolta dice che la cartella e' ritirata, cosi' so perche' quel percorso non si aggiorna piu' | `test_duplicate_is_409_and_retire_reactivate_keep_data` |
| Se sposto le foto (un altro disco, un'altra lettera, il NAS) la cartella resta la stessa: le risposte *che file sono* la seguono, i frame non si muovono e una scansione dopo non ne crea di nuovi; l'app riconosce da sola la cartella spostata quando guardo nel posto nuovo, e non la sposta dove non ci sono gli stessi file | `test_a_moved_folder_takes_its_answer_and_its_frames_stay`, `test_the_root_and_every_subfolder_move_and_a_neighbour_does_not`, `test_moving_to_the_same_files_keeps_everything_and_a_scan_adds_nothing`, `test_a_place_with_other_files_is_refused_and_nothing_changes`, `test_moving_onto_a_registered_folder_is_409`, `test_the_probe_recognises_an_unreachable_folder_moved_here`, `test_the_probe_recognises_a_retired_folder_and_moving_it_brings_it_back`, `test_a_copy_of_a_reachable_folder_is_not_a_move`, `test_recognising_stops_reading_headers_at_the_deadline`, `test_a_folder_that_has_not_said_whether_it_answers_is_not_skipped_as_gone`, `test_a_silent_unrelated_folder_does_not_hide_a_move`, *la sonda la riconosce, e il tasto la sposta invece di registrarne una nuova* (`frontend/tests/wizard-cartelle.test.tsx`), *Cambia percorso sposta la cartella dove stanno ora i suoi file* (`frontend/tests/impostazioni.test.tsx`) |
| Tutto quello che dico all'app sta in un file accanto al database, riscritto dopo ogni mia risposta e mai dalla scansione; se il database si perde, all'avvio me lo propone e lo rimette, e le pagine tornano come prima; l'Esporta non porta le chiavi dei servizi ne' il percorso di ASTAP; un file che non e' un backup si rifiuta; una cartella tornata senza frame si riconosce dal suo campione (ADR 0017) | `test_every_write_of_the_user_rewrites_the_file_and_a_new_database_gets_it_back`, `test_a_database_recreated_before_start_is_offered_the_file`, `test_a_database_in_use_is_not_offered_and_cannot_be_overwritten`, `test_declining_starts_from_scratch`, `test_the_stages_never_write_the_file`, `test_the_export_carries_no_service_key_and_no_solver_path`, `test_an_export_imported_elsewhere_adds_without_deleting`, `test_a_file_that_is_not_a_backup_is_refused`, `test_the_answers_keep_their_keys_and_the_folder_its_sample`, `test_a_restored_folder_without_frames_is_recognised_by_its_sample`, *su un database nuovo chiede di rimetterle, prima del primo avvio* (`frontend/tests/backup.test.tsx`) |
| Riaprendo l'app non parte nessun lavoro da solo; sul NAS la scansione gira ogni ora solo se chi lancia l'app lo chiede (`ASTROLOG_SCAN_EVERY_MIN=60`); c'e' sempre il pulsante Scansiona, nella barra in alto di ogni pagina | `test_worker_no_autostart_and_stop_when_idle_is_a_noop`, `test_scan_schedule_nas`, `test_the_nas_scan_cadence_reaches_the_app` |
| Due scansioni insieme non si pestano: la seconda riceve "gia' in corso" | `test_scan_lock_stop_and_the_button_verb` |
| Una pagina aperta mentre l'app lavora in sottofondo non cade con "database is locked", anche su Windows con l'antivirus: l'app tiene il database aperto finche' gira, e il file accanto all'archivio non resta gonfio per questo | `test_closing_a_request_is_never_the_last_close`, `test_the_wal_shrinks_back_while_a_connection_stays_open` |
| Ogni frame viene risolto sul cielo da ASTAP, prima uno per sessione, poi tutti; il FITS non viene mai modificato | `test_solve_order_one_per_group`, `test_solve_never_writes_fits`, `test_solve_field_from_the_header` |
| Un frame risolto una volta non si ri-risolve dopo un reset: la cache per hash lo ricorda | `test_solve_cache_by_hash` |
| Un frame che ASTAP non risolve e' "non risolto" con il suo perche', e l'archivio va avanti | `test_solve_failure_is_a_reason` |
| I nomi dei filtri, degli strumenti e degli oggetti scritti in mille modi diventano i miei filtri, i miei strumenti, i miei oggetti; quando l'app non sa, me lo chiede una volta per gruppo e poi si ricorda | `test_normalize_vocab_corpus`, `test_normalize_alias_learned` |
| Un filtro che l'app non riconosce (`H`, `Filter 3`) me lo chiede una volta -- e' uno dei miei, un modello in commercio, o nome e banda -- e la risposta vale per sempre; uno che riconosce non me lo chiede | `test_only_the_filters_the_app_does_not_know_are_asked`, `test_review_merges_two_filters`, `test_review_declares_a_filter_with_its_bands` |
| Lo stesso pezzo scritto in due modi (`ATR2600M` e `ATR2600M(USB2.0)`) e' un pezzo solo: me lo chiede una volta e non ci torna piu' | `test_normalize_alias_learned` |
| Un pezzo scritto in due modi lo unisco una volta, e da li' in poi l'app riconosce da sola la grafia vecchia | `test_merging_two_spellings_moves_the_poses_and_learns_the_rule` |
| Cambio idea quante volte voglio: rinomino un pezzo gia' rinominato o gia' unito, e tutte le grafie di prima continuano a portare a lui -- anche per un filtro | `test_a_second_rename_carries_the_spelling_learned_by_the_first`, `test_renaming_a_piece_carries_the_spellings_it_absorbed`, `test_renaming_a_filter_carries_the_spelling_it_absorbed` |
| Dichiaro un filtro che possiedo con la sua marca, il suo modello e le larghezze di banda, e i frame che lo usano lo prendono | `test_review_declares_a_filter_with_its_bands` |
| Alla fine della scansione vedo le domande che l'app non sa risolvere da sola, e gli oggetti: con "Applica" le risposte diventano le regole dell'archivio. L'attrezzatura non e' una domanda: la vedo e la correggo nell'Attrezzatura | `test_review_lists_what_was_found`, `test_review_only_new_things` |
| Due grafie che hanno l'aria di essere la stessa camera me le chiede -- "sono lo stesso strumento?" --; si' le unisce, no non me lo chiede piu' per quella coppia, e guardare non e' rispondere | `test_a_yes_merges_the_two_spellings`, `test_a_no_silences_the_pair_for_good_whichever_way_it_leans`, `test_seeing_the_page_does_not_answer_the_question` |
| L'oggetto me lo chiede in **una scheda per gruppo di frame** (ADR 0014, S3): i frame che l'app ha messo su un oggetto, o un gruppo di frame senza nome e senza cielo; la stessa scheda per tutti e due, coi candidati del cielo da cliccare -- anche zero -- e la stessa risposta | `test_found_objects_and_unnamed_groups_are_one_list_of_cards`, `test_an_answer_that_says_two_things_or_none_is_refused`, `test_a_card_that_is_not_there_is_refused` |
| Anche a un oggetto trovato rispondo "non e' un oggetto": i suoi frame escono dalle ore e da ogni oggetto, la scheda resta in pagina coi candidati e non conta piu', e cambio idea; vale per i frame che c'erano quando ho risposto | `test_not_an_object_on_a_found_object_takes_its_frames_out_and_the_card_stays`, `test_the_card_of_frames_put_out_keeps_the_sky_candidates` |
| "Non e' un oggetto" detto per un gruppo di frame senza nome non tocca un frame del gruppo che il cielo ha riconosciuto | `test_not_an_object_said_for_a_group_does_not_reach_a_frame_the_sky_recognised`, `test_a_sky_that_comes_after_the_group_answer_still_decides` |
| Vedo cosa l'app ha capito di ogni oggetto, e cio' su cui ha un dubbio sta in cima | `test_the_objects_section_shows_the_archive_objects_not_the_header_spellings`, `test_the_ones_to_decide_come_first` |
| Gli oggetti che l'app sa, su cui non c'e' niente da scegliere, non riempiono la pagina: stanno chiusi, si aprono a pagine, e da li' si correggono | `test_the_settled_objects_leave_the_page_and_come_in_pages` |
| Quando mi chiede quale oggetto era, mi mostra cosa c'e' a quelle coordinate e mi basta cliccare | `test_a_doubtful_object_carries_the_candidates_the_sky_found` |
| Se rispondo che quei frame sono un altro oggetto, ci vanno davvero -- e non tornano indietro | `test_answering_on_an_object_moves_its_frames_and_locks_it`, `test_a_correction_survives_a_second_run` |
| Se scrivo a mano una sigla che il catalogo conosce (`M 81`, `m81`), e' quella voce, non un oggetto fuori catalogo con lo stesso nome: le mie ore non si dividono su due voci | `test_a_designation_written_by_hand_is_the_catalog_entry` |
| E dopo che ho risposto l'app non me lo richiede piu', neanche sull'oggetto su cui era in dubbio | `test_a_correction_closes_the_question_on_a_doubtful_object` |
| Il conto delle cose da confermare scende quando **rispondo**, non quando guardo: Applica scrive solo le risposte, e non spegne una domanda che ho lasciato li' (ADR 0014, S4) | `test_only_the_filters_the_app_does_not_know_are_asked`, `test_apply_without_answers_silences_no_object`, `test_answering_a_doubt_closes_it` |
| Una pagina aperta prima di un aggiornamento, che manda un campo di ieri (`seen`), si sente dire 422 e non scrive niente | `test_an_answer_with_a_field_we_do_not_know_is_refused` |
| La mia risposta vale anche per i frame futuri con quello stesso nome, ma non quando quel nome e' un segnaposto | `test_a_learned_rule_names_a_future_frame_without_asking_again`, `test_an_answer_does_not_become_a_rule_when_the_spelling_is_a_placeholder` |
| E una regola non mi mette in archivio un frame che il cielo dice essere un'altra cosa: dove il cielo c'e', decide lui | `test_a_learned_rule_does_not_touch_a_frame_that_has_a_sky` |
| Se mi ero sbagliato, rispondo di nuovo e la seconda risposta vale | `test_a_second_answer_corrects_the_first` |
| I frame senza nome e senza cielo me li chiede per gruppo -- notte, camera, telescopio e dove puntava la montatura --, non uno per uno e non per cartella: due oggetti della stessa notte si separano col puntamento; e la domanda dice dalla prima all'ultima posa, nell'ora del posto, cosi' vedo se senza puntamento sono due; le ore sono quelle dei frame che dicono quando | `test_the_question_on_poses_without_a_name_says_their_hours`, `test_the_hours_are_those_of_the_poses_that_say_when`, `test_the_frames_with_no_name_and_no_sky_are_asked_by_group`, `test_a_question_per_group_with_what_makes_it`, `test_two_objects_of_the_same_night_are_two_questions`, `test_a_dither_stays_in_the_same_group`, `test_a_pose_without_sky_is_asked_whatever_identify_has_done_with_it`, `test_an_object_made_only_of_spaces_is_not_a_name` |
| Non me li chiede finche' il cielo puo' ancora arrivare, e nemmeno dove il cielo ha dei candidati; un cielo che non trova niente vale come nessun cielo | `test_a_pose_the_solver_has_not_looked_at_yet_is_not_asked`, `test_a_pose_whose_sky_has_candidates_is_not_asked`, `test_a_solved_pose_whose_sky_finds_nothing_is_asked_like_the_others` |
| Un file che non si trova piu' e una cartella che ho ritirato non mi chiedono niente | `test_a_file_that_is_gone_and_a_retired_folder_do_not_ask_anything` |
| L'oggetto del gruppo -- dal catalogo o scritto -- sposta i suoi frame senza nome, anche in un'altra cartella, vale anche per quelli che arriveranno e si cambia; si scrive sull'impronta di ogni frame, anche mancante, non su una chiave con la notte, e due risposte diverse nello stesso gruppo non sono una risposta; "non e' un oggetto" li chiude senza inventare un soggetto | `test_a_name_said_for_the_group_puts_its_poses_on_that_object`, `test_the_answer_hangs_on_the_poses_not_on_a_key_with_the_night`, `test_two_answers_in_one_group_are_no_answer`, `test_the_answer_reaches_a_pose_of_the_same_group_in_another_folder`, `test_a_catalog_entry_puts_the_poses_on_its_object`, `test_not_an_object_closes_the_poses_and_they_wait_for_nothing`, `test_the_rule_holds_for_the_poses_that_arrive_later`, `test_i_can_change_my_mind_and_the_poses_follow`, `test_changing_my_mind_reaches_a_missing_pose_too` |
| Dove il cielo ha dei candidati decide lui, e l'oggetto del gruppo non lo scavalca; un frame risolto ma senza niente nel cono resta nella sua domanda anche dopo | `test_the_sky_wins_over_the_group_where_it_has_candidates`, `test_a_solved_pose_whose_sky_finds_nothing_is_reached_and_stays_in_the_group`, `test_a_pose_whose_sky_finds_nothing_stays_asked_while_it_waits_to_be_redone` |
| Rispondo da Da confermare che quel gruppo e' un oggetto -- dal catalogo o scritto -- oppure che non e' un oggetto, una risposta sola; il gruppo resta in pagina con la mia risposta e la cambio, e l'oggetto che nomino non torna da confermare; finche' non rispondo il gruppo conta fra le cose da confermare | `test_answering_with_a_name_moves_the_poses_and_the_group_keeps_its_answer`, `test_an_open_group_counts_and_an_answered_one_does_not`, `test_the_object_named_by_the_answer_is_not_another_question`, `test_answering_with_a_catalog_entry`, `test_not_an_object_is_an_answer_too_and_i_can_change_my_mind`, `test_an_answer_that_says_two_things_or_none_is_refused` |
| Un oggetto che l'app sa non me lo chiede: quello che il cielo riconosce con certezza, e una sigla del catalogo scritta nel file anche senza cielo (Marco, 6/10/2026); me lo chiede solo col dubbio. La pagina non mi blocca mai: i frame sono gia' in archivio | `test_an_object_the_sky_is_sure_of_is_not_asked`, `test_a_catalog_name_without_a_sky_is_not_asked`, `test_review_only_new_things` |
| L'attrezzatura che i file non dicono -- la camera, l'ottica, il filtro -- me la chiede in **una scheda per firma dell'header** (grafia di camera e telescopio, focale entro il 5 %, sensore), non per notte ne' per cartella, e solo le parti che mancano; un `TELESCOP` che il programma dice montatura (l'ASIAIR) non entra nella firma (ADR 0014, S1) | `test_a_question_per_group_with_the_largest_first`, `test_the_signature_is_the_header_not_the_night_or_the_folder`, `test_each_value_of_the_key_makes_its_own_group_and_the_row_says_it`, `test_the_key_is_made_in_one_place_from_what_the_header_says`, `test_renaming_the_optics_does_not_move_the_key`, `test_only_the_poses_whose_header_does_not_say_the_camera_are_asked`, `test_a_part_the_files_say_is_not_asked`, `test_the_focal_is_shown_only_when_the_poses_agree`, `test_two_mount_names_of_one_asiair_are_one_card`, `test_poses_that_do_not_name_the_optics_are_asked_once_per_camera_and_focal`, `test_the_answer_is_for_that_camera_only` |
| Rispondo alla camera scegliendo un corredo che l'app conosce o scrivendo camera e focale (e l'ottica se serve), all'ottica scegliendone una mia o scrivendone il nome: i pezzi scritti a mano diventano miei, i frame vanno nel corredo che quei pezzi hanno gia', e la risposta vale anche per i frame che arriveranno con la stessa firma, **in qualunque notte** | `test_answering_with_the_pieces_makes_the_rig_and_moves_the_poses`, `test_choosing_a_rig_from_the_list_writes_its_names`, `test_the_camera_written_by_hand_becomes_a_piece_and_the_filter_question_follows`, `test_the_answer_holds_for_the_poses_that_arrive_later_in_that_group`, `test_the_answer_gives_the_optics_and_the_poses_join_the_rig_that_has_it`, `test_an_optics_written_by_name_is_born_like_from_a_header`, `test_a_pose_that_arrives_later_takes_the_answer_by_itself`, `test_the_pose_reads_the_answer_of_its_own_group`, `test_a_focal_that_drifts_finds_the_same_answer`, `test_the_answer_is_read_back_with_its_pieces`, `test_the_key_is_never_split_to_find_the_pieces` |
| Una scheda conta fra le cose da confermare finche' ogni parte che chiede non ha la sua risposta; risposta, resta in pagina; una parte che non mando tiene la risposta di prima; una risposta illeggibile vale nessuna risposta | `test_an_unanswered_group_counts_among_the_things_to_confirm`, `test_the_camera_written_by_hand_becomes_a_piece_and_the_filter_question_follows`, `test_an_answer_that_cannot_be_read_is_no_answer`, `test_a_focal_that_is_not_a_focal_leaves_the_answer_standing`, `test_an_optics_that_is_not_a_name_is_no_optics`, `test_a_filter_word_that_is_not_an_answer_is_no_filter_answer` |
| Se ho ripreso senza filtro (camera a colori) l'app non inventa un filtro, e se non riesce a saperlo me lo chiede nella scheda della firma | `test_normalize_bayer_decides_when_filter_is_none`, `test_a_question_per_camera_with_the_largest_first` |
| Al filtro rispondo a colori, nessun filtro, o uno dei miei filtri scelto da una tendina, e la risposta vale anche per i frame che verranno; "a colori" si scrive sulla scheda della camera, anche quando la camera viene dalla notte, e il colore scritto li' e' la stessa risposta | `test_answering_colour_makes_those_poses_osc_and_the_next_ones_too`, `test_the_camera_of_the_night_takes_the_answer_about_the_sensor`, `test_answering_mono_with_no_filter_puts_them_on_no_filter`, `test_answering_one_of_my_filters_puts_them_on_it`, `test_writing_colour_on_the_card_answers_too`, `test_colour_without_a_camera_is_refused`, `test_one_of_my_filters_does_not_beat_colour`, `test_a_filter_named_like_an_answer_stays_a_filter`, `test_one_of_my_filters_is_one_of_the_choices`, `test_after_the_answer_the_filter_question_reaches_those_poses` |
| La mia camera a colori non me lo chiede: se i file la dicono a colori i suoi frame senza filtro sono OSC, anche quelli di un programma che la matrice non la scrive; il frame che il filtro lo scrive resta col suo filtro | `test_a_camera_its_files_say_colour_is_not_asked_and_its_poses_are_osc`, `test_answering_no_filter_on_a_colour_camera_does_not_call_it_mono`, `test_normalize_reads_the_colour_of_the_camera_not_of_the_single_pose` |
| La mia risposta dice cosa avevo davanti e la scheda della camera dice che sensore e': cambiare il sensore non me la cancella, e tornando a mono la ritrovo | `test_the_answer_about_the_filter_survives_a_change_of_sensor`, `test_the_card_says_the_sensor_and_the_answer_stays_and_the_pixel_does_nothing` |
| Accanto a ogni gruppo su cui l'app chiede -- firma dell'attrezzatura, gruppo di frame, sito -- vedo cosa ho ripreso, anche se il file non scrive l'oggetto, e so quali frame il cielo non ha riconosciuto e quali non ha ancora guardato o non e' riuscito a guardare | `test_the_camera_question_sums_the_subjects_of_all_its_nights`, `test_a_group_says_what_the_sky_found_in_it`, `test_a_place_says_what_the_sky_found_there` |
| L'unica domanda che **non** lo mostra e' *che file sono* (per cartella): su quei frame il cielo non ha saputo dire -- un elenco vuoto sembrerebbe una risposta invece che un'attesa | `test_a_question_per_folder_about_which_files_they_are` |
| Se rinomino o unisco il filtro, la camera o l'ottica che ho risposto, la risposta li segue, e il nome vecchio non fa rinascere il pezzo; rinominare o unire una camera dei file non sposta la risposta, che sta sulla grafia del file | `test_the_answer_follows_its_filter_when_it_is_renamed_or_merged`, `test_renaming_a_piece_carries_the_answers_that_name_it`, `test_renaming_the_optics_carries_the_answer`, `test_renaming_the_camera_carries_the_answer`, `test_merging_the_optics_into_another_carries_the_answer`, `test_renaming_a_camera_carries_the_answer_on_the_group`, `test_merging_the_optics_carries_the_answer_on_the_group`, `test_renaming_a_camera_carries_its_answer`, `test_merging_two_cameras_leaves_each_signature_its_answer`, `test_merging_into_a_colour_camera_keeps_the_answer_that_arrives`, `test_merging_into_a_colour_camera_carries_the_answer_even_there`, `test_the_unfiltered_answer_follows_the_camera_when_renamed` |
| La mia risposta su una firma non decide per le altre, nemmeno se rinomino o unisco "nessun filtro" | `test_renaming_no_filter_does_not_answer_for_the_other_cameras`, `test_no_filter_is_not_merged_into_another_filter` |
| Una risposta su una firma che non c'e' piu', su una parte che la scheda non chiede, con un corredo senza camera, o una riga "nessun filtro" che non si puo' creare, si dice invece di scrivere una risposta che non sposta niente | `test_a_group_that_is_not_there_is_refused`, `test_an_answer_to_a_question_that_is_not_there_is_refused`, `test_an_answer_about_a_camera_that_is_not_there_is_refused`, `test_the_answer_of_a_group_that_is_not_there_is_not_found`, `test_a_part_the_card_does_not_ask_is_refused`, `test_an_answer_that_says_two_things_or_none_is_refused`, `test_a_rig_without_a_camera_does_not_answer_this_question`, `test_a_no_filter_name_already_taken_is_said_not_crashed`, `test_a_filter_that_is_not_there_is_refused`, `test_a_filter_goes_with_one_of_my_filters_and_only_there` |
| La notte di un frame va da mezzogiorno a mezzogiorno nel fuso del posto -- delle coordinate dell'header, o di casa -- e un frame senza data prende quella in cui il file e' stato scritto | `test_in_the_east_the_night_is_cut_at_local_noon`, `test_without_coordinates_the_home_site_gives_the_zone`, `test_without_coordinates_and_home_the_night_is_in_utc`, `test_a_pose_without_a_date_takes_the_date_of_its_file` (`backend/tests/test_local_night.py`) |
| Quando cambia il fuso di casa i frame che non dicono dove sono stati ripresi passano al fuso nuovo, partendo dall'istante con cui sono entrati -- toccare il file dopo non sposta la notte --, quelli che lo dicono no; le risposte sull'oggetto stanno sui frame e li seguono: su ogni parte di un gruppo che si divide; su due gruppi che diventano uno vale la risposta che c'era, e con due diverse la domanda torna aperta; le risposte sull'attrezzatura restano dove sono, perche' la firma non ha notte; i frame delle notti toccate si rifanno | `test_the_first_home_moves_the_nights_of_the_poses_that_do_not_say_where`, `test_a_pose_without_date_obs_takes_the_night_of_its_file_in_the_home_timezone`, `test_a_file_touched_after_it_entered_keeps_the_instant_of_its_night`, `test_moving_home_to_another_timezone_moves_them_again`, `test_choosing_another_home_moves_them_to_its_timezone`, `test_without_a_home_they_go_back_to_utc`, `test_an_object_answer_follows_its_poses_into_the_new_night`, `test_two_object_answers_that_disagree_fall_when_their_groups_become_one`, `test_the_answer_follows_its_poses_into_another_group` (`backend/tests/test_unnamed.py`), `test_a_camera_answer_stays_put_when_home_moves`, `test_the_poses_of_the_nights_that_changed_are_worked_again` (`backend/tests/test_home_nights.py`) |
| Un frame che non dice la camera prende quella degli altri frame della stessa notte, se e' una sola, anche se il frame che la dice arriva dopo, e la scheda non chiede la camera; se nella notte nessuno la dice o ne dicono piu' d'una me la chiede; due grafie che ho unito sono una camera; e la mia risposta vince sulla notte | `test_a_pose_without_camera_takes_the_one_of_its_night`, `test_in_one_scan_the_order_of_the_files_does_not_matter`, `test_two_cameras_in_the_night_leave_the_question`, `test_two_spellings_of_one_camera_are_one_camera_of_the_night`, `test_my_answer_on_the_group_wins_over_the_night`, `test_the_cards_ask_the_rig_only_of_the_nights_of_their_poses` |
| Se il frame non dice l'ottica, prende quella della notte quando la notte ne dice una sola a una focale sola, con la focale se il frame non la dice (una focale zero non e' una focale), invece di far nascere un gemello senza ottica; una focale sua diversa non prende l'ottica della notte | `test_a_silent_pose_takes_the_rig_of_its_night`, `test_a_pose_with_its_own_focal_does_not_take_the_optics_of_another`, `test_a_night_with_two_optics_gives_only_the_camera`, `test_one_optics_at_two_focals_gives_only_the_camera`, `test_a_night_of_asiair_and_other_poses_gives_only_the_camera`, `test_an_asiair_night_gives_the_rig_without_optics_of_its_poses` (`backend/tests/test_night_rig.py`) |
| La focale me la chiede con la camera, proponendo quella della mia ottica, cosi' non mi ritrovo due corredi gemelli con le ore spartite | `test_the_declared_focal_does_not_leave_two_twin_rigs`, `test_the_focal_of_the_optics_card_is_what_the_page_proposes`, `test_the_focal_of_the_optics_card_is_proposed_when_the_poses_do_not_say_it` |
| Il nome e la montatura che avevo dato al corredo senza ottica passano al corredo che nasce dalla mia risposta, anche se cambio idea, e i frame tengono la montatura; un corredo che c'era gia' tiene la sua parola; nessuna scheda mi propone la montatura come ottica | `test_the_name_and_mount_of_the_rig_without_optics_go_with_its_poses`, `test_a_rig_that_was_already_there_keeps_its_own_word`, `test_the_camera_question_does_not_offer_the_mount_as_optics`, `test_a_mixed_group_does_not_offer_the_mount_as_optics_either`, `test_the_optics_shown_is_the_name_the_user_gave_it` |
| Cambio idea rispondendo di nuovo: i frame lasciano il corredo di prima, e quelli che l'ottica la dicono restano col loro | `test_answering_again_moves_the_poses_to_the_new_rig`, `test_changing_the_answer_moves_the_poses` |
| Un frame in due cartelle o una copia riscritta e' una posa sola; una cartella ritirata o un file sparito non chiedono niente; un corredo con le sole copie resta fra le scelte | `test_a_pose_that_lives_in_two_folders_counts_once`, `test_a_rewritten_copy_is_not_another_pose_but_comes_back_in_the_queue`, `test_a_retired_folder_and_a_file_that_is_gone_do_not_ask_anything`, `test_a_rig_whose_only_poses_are_copies_stays_in_the_page` |
| La copia calibrata di un frame non raddoppia il conteggio delle ore | `test_normalize_calibrated_copy` |
| Anche se riprendo con un programma che l'app non conosce, purche' la copia dica di essere stata calibrata | `test_normalize_finds_the_copy_of_an_unsupported_capture_program` |
| E se chi elabora lascia nell'header il nome del mio programma accanto al suo, o me lo riscrive col suo | `test_normalize_calibrated_copy`, `test_normalize_the_copy_that_overwrites_the_capture_software` |
| Ma se ho tenuto **solo** il file calibrato, quelle ore restano mie | `test_normalize_a_marked_frame_without_a_twin_still_counts` |
| E se due file dicono di essere lo stesso scatto e niente dice quale sia l'originale, l'app non indovina: li conta tutti e due | `test_normalize_does_not_guess_between_two_twins_that_say_nothing`, `test_normalize_does_not_mark_a_capture_program_that_writes_only_its_own_key` |
| Le notti vanno da mezzogiorno a mezzogiorno nel fuso del mio sito; una sessione e' oggetto x notte x corredo | `test_group_night_in_site_tz`, `test_group_session_key` |
| Se l'app non e' sicura da dove ho ripreso non inventa la notte: i frame restano in attesa col loro perche' | `test_group_asks_when_the_coordinates_say_elsewhere`, `test_group_invents_no_night_without_an_answer` |
| E me lo chiede una volta per **posto**, non per notte e nemmeno per frame, proponendomi i miei siti col piu' vicino in cima | `test_the_nights_section_asks_about_the_places_that_do_not_add_up`, `test_the_places_are_proposed_with_my_sites_the_nearest_first` |
| Rispondo una volta e quei frame vanno nella loro notte -- e le notti che riprendero' li' non me lo richiedono | `test_answering_where_i_was_puts_those_poses_in_their_night`, `test_the_answer_holds_for_the_nights_that_will_come` |
| L'ora di un frame e' quella di `DATE-OBS`, in UTC come dice lo standard FITS: l'app non me la chiede e non la corregge | `test_the_date_of_the_pose_is_utc_even_when_the_local_one_disagrees` |
| Un file elaborato che si dichiara frame non entra fra i miei frame e non fa ore, ma la ricevuta lo dice | `test_a_combined_file_is_not_a_frame` |
| La scheda della mia camera ha il pixel fisico su cui concordano i file, qualunque sia l'ordine in cui arrivano e anche se riprendo binnato | `test_the_pixel_follows_the_files_not_the_first_one`, `test_files_at_bin_two_give_the_physical_pixel` |
| Il pixel e il colore che scrivo sulla scheda restano miei: nessun ricalcolo li tocca | `test_what_i_write_on_the_card_is_never_recomputed`, `test_the_card_shows_what_i_wrote_over_what_the_files_say` |
| Tutto cio' che legge un header regge sugli header di altri software, non solo sui miei | `test_header_corpus_reads_every_file` |

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

**La "sessione" del solver si calcola quando serve, e non si scrive da nessuna parte**:
oggetto, notte della posa e i due pezzi come li scrive l'header, raggruppati nella query di chi la
usa -- che e' solo il solver, per il suo "prima un frame per sessione". Era una colonna su ogni
frame: un dato salvato per un lettore solo, che invecchiava a ogni modifica. Si guarda l'oggetto
**grezzo** perche' qui si mette in fila, non si contano ore: `M31` e `M 31` in due gruppi
costano un frame risolto in piu' e nient'altro. Le sessioni vere, col fuso del sito, le fa
`group`.

**La scansione legge l'header e i 64 KB dell'impronta, mai il resto** (`astropy.io.fits`,
`output_verify='silently'`, `ignore_missing_end=True`; header primario piu' la prima pagina
con dati per i file a piu' HDU). I pixel interi li leggono solo `solve` e `measure`. Un file
modificato da meno di 30 secondi, o la cui dimensione cambia fra due letture, si salta e si
rivede. Nello stato della spina lo `state` della lettura, mentre gira, e' del worker; finita,
e' l'esito delle ricevute di **tutte** le cartelle di quel gesto, dalla peggiore: una radice
caduta nella prima cartella e' `error` anche se l'ultima e' andata bene, e resta detto quando
il worker passa a un altro lavoro. E' da quello stato che la pagina avvisa della cartella persa.

**Un file che non si legge si salta, si nomina, e la corsa va avanti** (Marco, 2026-09-11): un
file solo non tiene fuori dall'archivio quelli che vengono dopo, e l'elenco ordinato farebbe
fermare ogni scansione sullo stesso. La ricevuta porta **tutti** i file non letti, ognuno col suo
codice (`errors_detail`): `file_unreadable` (il sistema non lo apre: permessi, file sparito o
bloccato), `header_unreadable` (non e' un FITS, o l'header e' rotto), `name_not_utf8` (un nome
che l'archivio non puo' scrivere -- una condivisione Linux scritta da un sistema vecchio: si
mostra coi `?` al posto dei byte che non si leggono), `internal_error` (un guasto che nessuno
aspettava: la traccia sta nel log, una volta per tipo di guasto). Vale anche per un file solo
online, e anche le cartelle lasciate fuori si nominano coi `?` quando il nome non e' UTF-8. **Il
database che non risponde non e' un file che non si legge**: disco pieno o database occupato
fermano la corsa col loro motivo (`database_error`) invece di dire "3.000 file non letti" di file
sani, e la ricevuta si chiude lo stesso, coi file non letti fin li' -- se il database torna a
rispondere in tempo per scriverla: occupato oltre la sua attesa, la corsa resta aperta. La
fermano anche la radice caduta e lo Stop. La ricevuta nello stato porta i numeri; **l'elenco dei
file non letti si legge a pagine** (`GET /api/v1/scan-runs/{id}/errors`), perche' puo' contare
migliaia di nomi e la pagina interroga lo stato ogni pochi secondi; lo stato del worker dice solo
che ci sono. Lo tiene **l'ultima scansione di ogni cartella, e se non e' arrivata in
fondo anche l'ultima che ci e' arrivata** (Marco, 2026-09-11): quei file si riprovano a ogni
scansione arrivata in fondo, e le altre ricevute tengono i numeri (`errors_not_kept`). Cosi' il
database non cresce nemmeno se la condivisione cade a ogni giro. Di una corsa ancora aperta
l'elenco non c'e' ancora (`scan_run_open`).

**Un worker, un thread, unico scrittore.** Vive nel processo del backend (uno solo da
impacchettare su tre bersagli); esegue gli stadi in sequenza; ASTAP gira come sottoprocesso
e restituisce file nella cache, mai scritture nel DB. Stop cooperativo fra un frame e
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
(`localhost`, e sul NAS quelli dichiarati), e sul desktop la finestra porta un token per
avvio che le altre applicazioni della macchina non hanno.

**La radice si salva come l'utente la ritrova**, confinata sotto la radice dei dati quando e'
impostata (Docker): la forma risolta, salvo un disco di rete collegato a una lettera, che Python
dalla 3.8 risolverebbe nella sua condivisione (bpo-37993) -- chi ha scelto `Z:` ritrova `Z:`.
**Le cartelle di rete si accettano** (`\\server\cartella`; Marco, 2026-09-11). Aprirne una fa
autenticare Windows verso quel server con le credenziali dell'utente (n00py, *Understanding UNC
paths, SMB, and WebDAV*): il rischio resta confinato perche' il servizio ascolta sulla macchina e
chiede il token, e sul NAS in Docker quei percorsi non esistono. Non entrano le forme che
scavalcherebbero le zone di sistema -- i percorsi di dispositivo (`\\?\`, `\\.\`: codice
`path_device`), i nomi coi caratteri che Windows non ammette in un nome (`?`, `*`, il carattere
nullo: `path_invalid`, e con loro `\??\C:\Windows`), ogni forma che risolta non e' un percorso
assoluto (`path_not_absolute`), e le condivisioni amministrative (`C$`, `ADMIN$`), che si rifiutano con un codice loro
(`path_admin_share`) anche su un altro PC: da fuori non si sa se `\\nome\C$` e' questa
macchina, e la cartella si condivide con un nome normale (Marco, 2026-09-11) --; le fonti stanno
in `api/paths.py`, e i controlli guardano sempre dove il percorso porta. **Due righe per la stessa
cartella restano possibili**, e si dicono: un collegamento verso un altro disco si salva com'e'
scritto, e il suo bersaglio registrato a parte e' un'altra riga; la stessa cartella scelta una
volta come disco collegato e una volta come percorso di rete scritto a mano sono due righe; su un
disco collegato il nome corto che Windows da' alle cartelle (`Z:\ARCHIV~1`) e' un'altra riga del
nome lungo, perche' la lettera si tiene e il nome corto non coincide con quello risolto; e se
il percorso non si risolve (NAS spento, credenziali rifiutate) si controlla e si salva com'e'
scritto. Se `os.scandir(root)` fallisce
prima del walk: abort con codice, posizioni intatte. **Collegamenti a cartella e giunzioni non si
seguono** -- per Python una giunzione e' una cartella qualunque, e una verso un antenato farebbe
girare il walk a vuoto -- **e la ricevuta li nomina** (`linked_dirs`). Percorsi lunghi su Windows
in forma `\\?\`, e una cartella di rete nella sua (`\\?\UNC\server\share`, come vuole la
documentazione di Windows: col prefisso sbagliato non si apre).

**Spostare una cartella e' cambiarle percorso, non registrarne un'altra** (`spine/folder_move.py`).
Stessa riga di `folders`, `root_path` nuovo: le posizioni sono relative alla radice, i frame si
riconoscono dall'impronta, le letture stanno per `folder_id`. Seguono il percorso solo le
risposte per cartella, che lo hanno nella chiave: quelle uguali alla vecchia radice o che
cominciano con lei e una barra passano al prefisso nuovo (forma di `frame_folder.folder_key`), e
`typeless_folders` si riscrive, tutto in una transazione. **Si sposta solo dove ci sono gli stessi
file**: i primi 5 file sotto il posto nuovo, in ordine di percorso, fra quelli di cui la cartella
ha una posizione con lo stesso percorso relativo (i file di calibrazione non ne hanno), letti come
li legge la scansione; tutte le impronte uguali e' la stessa cartella, zero file o un'impronta
diversa no (`409 not_the_same_folder`). Il percorso nuovo passa la validazione di quando si
registra; gia' registrato, attivo o ritirato, e' `409 folder_exists`. Una cartella ritirata
spostata torna attiva. **La sonda riconosce lo spostamento da sola** (`moved_from`, e
`moved_check` dice perche' manca): la candidata e' una cartella ritirata o che non si
raggiunge, entro lo stesso `PROBE_SECONDS`; una ancora raggiungibile con gli stessi file e' una
copia, e non si propone. Una cartella che non ha ancora detto se risponde non e' "non si
raggiunge": se ha gli stessi file potrebbe essere l'originale, e non si propone niente
(`out_of_time`); se non li ha non conta. Anche il campione letto a meta' allo scadere e'
`out_of_time`.

**Sul NAS la cartella si sceglie da un elenco.** Dentro il container l'utente non sa quale
percorso ha la cartella che conosce come `/volume1/photo`: `GET /folders/browse` elenca le
sottocartelle visibili sotto la radice dei dati, e fuori da li' non guarda; senza radice (il
desktop) non elenca niente. **Aggiungi cartella conta per un tempo limitato**
(`PROBE_SECONDS`, con la fonte in `api/folders.py`), guardato fra una cartella e l'altra, e dice
se il conteggio e' completo (`complete`). **L'elenco delle cartelle chiede a tutte se
rispondono**, insieme e sotto lo stesso `PROBE_SECONDS`: una che non ha risposto in tempo si
legge "non si raggiunge", e una condivisione morta non tiene fermo l'elenco. Chiedono
lavoratori che restano accesi e si riusano; una cartella ancora in attesa di risposta non si
richiede, e occupa un lavoratore, non uno per ogni volta che si apre l'elenco. Un lavoratore
fermo su una cartella morta non e' libero: se non ce n'e' uno libero se ne accende un altro, cosi'
anche con molte cartelle su un NAS caduto quelle che rispondono si leggono raggiungibili.

**Cio' che il disco mette accanto ai file non e' un file.** Non si raccolgono i gemelli che
macOS scrive su chiavette e NAS (`._M42.fits`: metadati del Finder, non un FITS -- senza
questa riga un archivio passato da un Mac dice "1.200 file non letti" su 1.200 frame sani), e
non si percorrono le **cartelle nascoste**: nel cestino ci sono i frame che l'utente ha
cancellato, e percorrerlo li farebbe rientrare. Si guarda la proprieta' -- il punto davanti su
Mac e Linux, l'attributo di Windows -- e non una lista di nomi, che coprirebbe il NAS che
conosciamo e nessun altro. La radice che l'utente indica non passa da questo filtro: si
filtrano solo le sottocartelle che si incontrano. Non spariscono in silenzio: la ricevuta le
nomina (`hidden_dirs`), come le illeggibili, e i frame che contenevano diventano "non trovati".
**Le nomina dalla radice in giu'**, come i file non letti: il percorso intero e' quello della
cartella, che la ricevuta porta gia', e ripeterlo su ogni voce copre l'unica parola che le
distingue.

**Un file solo online non si apre.** OneDrive, Dropbox e iCloud lasciano sul disco un
segnaposto, e aprirlo lo scarica: chi ha l'archivio sotto *Immagini* -- dove Windows mette
OneDrive per impostazione predefinita -- se lo vedrebbe scaricare tutto alla prima scansione. Il
segno lo mette il sistema, e si legge **dall'elenco della cartella** (`fits/walk`, con le fonti
accanto): su Windows solo li' compare. Prima di macOS Sonoma iCloud non metteva il segno ma un
segnaposto nascosto `.nome.fits.icloud`, che si riconosce dal nome e vale lo stesso. Quei file si
contano nella ricevuta (`online_only`), si
rivedono a ogni scansione ed entrano quando l'utente li rende disponibili sul disco; un frame gia'
in archivio lasciato solo online non diventa "non trovato". **Senza nessun servizio**:
nessun account, nessuna rete, nessun collegamento a OneDrive, Dropbox o iCloud; l'app
guarda solo il segno o il segnaposto che il sistema scrive, una forma fissa e mai una lista di
nomi.

**Cosa entra**: `.fits` e `.fit`, tipo `light` o `unknown`; gli altri formati (`.fts`, `.fz`,
XISF) quando un utente li chiede. Dark, flat, bias, dark-flat e
`stack` (`STACKCNT`, `NCOMBINE`, `NIMAGES` quando contano **piu' di un** frame -- a 1 e' un
frame --, o *master / integration / stack / stacked* nel
tipo o nell'oggetto: anche lo stack dal vivo di un Seestar) <!-- software-ok --> si
riconoscono per essere saltati. **Il
tipo si legge da due campi, non da uno**: quando `OBJECT` e' per intero una parola di
calibrazione (`dark`, `flat`, `bias`, `darkflat`, `flatdark`, `offset`, `zero`) quella vince
su `IMAGETYP`, perche' una libreria di calibrazione puo' dichiararsi `LIGHT` -- misurato: 56
file, 28 frame distinti. Per intero e mai per pezzi: *Dark Nebula* e' un oggetto vero. **E la parola si riconosce in qualunque grafia**:
minuscole o maiuscole, con lo spazio, il trattino o l'underscore, al singolare o al plurale
-- `Dark Frame`, `DARK-FRAME`, `dark_frame`, `darkframe` e `darks` sono lo stesso dark. Il
vocabolario e' scritto una volta sola, senza separatori, in `fits/frame_type.py`: dei quattro
software supportati abbiamo l'header vero solo di N.I.N.A. e ASIAIR, e la grafia di Voyager e
SGP non deve decidere se una calibrazione entra. Calibrazioni e stack si saltano, e la ricevuta
conta i saltati **per motivo**, calibrazioni comprese (`skipped_by_reason`: `calibration`,
`stack`, `still_writing`; Marco, 2026-09-11): un NAS con l'orologio avanti, che fa saltare gli
stessi frame a ogni scansione come "ancora in scrittura", si vede. **Vale anche per chi non conta i
frame sommati ma li elenca**: un `HISTORY` che nomina i file sorgente (`SOURCE1`, `SOURCE2`,
...) dice che quel file e' una combinazione, e cinque integrazioni dell'archivio di collaudo
si dichiaravano `LIGHT` proprio cosi'. `CALSTAT` e `CALIBRAT` **non** sono spie di stack:
dicono "calibrato", non "sommato", e a chi tiene i frame calibrati accanto agli originali
farebbero sparire l'archivio intero. Fanno un altro mestiere -- il **marchio di riscrittura**,
piu' sotto -- che non fa sparire niente. Un file senza `IMAGETYP` e'
`unknown` ed entra (alcuni software non lo scrivono), e che file e' **lo dice il cielo** (Marco,
23/9/2026: *"se il cielo si risolve e' una foto, altrimenti calibrazione; si chiede solo quando il
cielo non sa dirlo"*). Va al solver come gli altri: risolto e' una foto; "poche stelle" e' una
calibrazione -- un bias, un flat, un dark con pochi pixel caldi non hanno stelle; un dark con
pixel caldi fitti o a gruppi il solver lo scambia per un campo di stelle, e quel file si chiede --;
una rinuncia per qualunque altro
motivo (nessuna soluzione, tempo scaduto, un errore) e' il cielo che non sa dire, e si chiede. Finche' non si sa **si ferma prima dell'oggetto**: il `failed` del cielo, che per un light
manda avanti dal nome, qui non manda avanti niente, e quel frame non conta nel residuo di cio' che
viene dopo il cielo (`spine/stages.py`: chi aspetta non e' lavoro da fare). Che aspetta e' scritto
sulla posa (`frames.asks_type`), e lo riscrive SQLite (i trigger della vista `frame_waits` in
`schema.sql`) a ogni scrittura di cio' da cui dipende -- il cielo, la posizione del file, la risposta
della cartella --, chiunque scriva: chi legge non rifa' la regola. Cosi' non diventa ore
e non finisce fra i **Frame senza nome**, dove la domanda e' "cosa hai ripreso" e non "che file
e'". Una foto del cielo tutta coperta dalle nuvole non ha stelle, e finisce fra le calibrazioni:
non ha dati, e non conta nelle ore. La domanda si fa per **cartella** (`spine/typeless.py`) e
conta tutti i frame senza tipo della cartella, perche' la risposta li sposta tutti, anche quelli
che il cielo aveva gia' deciso: detto "Light" quei frame ripartono, detto "Calibrazione"
restano fermi anche se il cielo li aveva risolti, e i file che arrivano dopo in
quella cartella, se l'archivio non li ha gia', non entrano nemmeno. Il software di
ripresa supportato e' N.I.N.A., ASIAIR, Voyager e SGP; il corpus (`backend/tests/header/`) ha
per ora i primi due -- Voyager e SGP mancano, e stanno in coda finche' non arriva un file
vero. Dell'ASIAIR ce ne sono **tre, di tre utenti diversi**, e non e' abbondanza: in `TELESCOP`
quel programma scrive la **montatura**, e il nome cambia da utente a utente (`EQMod Mount`
contro `ZWO AM3`), quindi un header solo farebbe sembrare una lista di nomi la risposta
giusta. Un header di un programma che non e' fra i quattro non entra nel corpus.

**`normalize` traduce, non interpreta.** Applica i vocabolari ai grezzi dell'header e scrive
`frames.software`, `filter_id`, `rig_id` e i tre pezzi che la posa nomina addosso a se'
(`filter_wheel_id`, `focuser_id`, `guide_camera_id`). Le sigle degli oggetti sono mestiere di
`identify` col catalogo: qui il nome si pulisce soltanto (spazi, parole di tavolozza), e un
suffisso di mosaico (*Pannello 2*) resta nel nome, perche' toglierlo e' interpretare.
Non dipende da nessuno stadio: gira anche prima del solver.

**I vocabolari dicono solo cio' che i quattro software scrivono**.
Nei filtri restano le grafie dei quattro; il catalogo dei modelli resta come
tendina, ma si puo' scrivere qualunque nome con la sua banda; le bande sono 16 piu' `UNKNOWN`
(`vocab/filters.json`). Il software riconosciuto e' solo quello dei quattro, e la copia calibrata
si riconosce dal marchio che il file porta, non dal nome del programma. Le chiavi dell'header sono
lo standard FITS piu' cio' che i quattro scrivono, salvo le due che dicono che il file e' stato
riscritto (`CALSTAT`, `CALIBRAT`), da una convenzione pubblica. Le misure scritte nell'header
(FWHM, SNR, stelle) non si leggono: si misurano.

**Prima l'alias, poi il vocabolario, poi la domanda.** Per ogni grezzo l'ordine e':
`header_aliases` (cio' che l'utente ha gia' risposto) -> il vocabolario -> altrimenti il
valore resta grezzo e il **gruppo** entra in Da confermare. Una risposta e' sempre una regola
riusabile, mai una correzione su un frame: si chiede per gruppo, mai per file. L'automatico
non sovrascrive mai il dichiarato, e la risposta chiama `invalidate` sugli stadi a valle.
Un'eccezione sola, dove non c'e' niente da sovrascrivere: su una camera a colori una parola che il
**vocabolario stesso** conosce come banda larga (`L`, `Lum`, `B`) resta OSC anche se una rinomina o
un filtro scritto a mano ne hanno fatto una regola -- quella regola parla delle pose mono, e sulla
matrice il filtro e' la matrice (`test_a_colour_frame_that_writes_the_app_name_stays_osc_after_a_rename`).
Una risposta su una parola che il vocabolario non conosce resta la tua
(`test_an_answer_on_a_word_the_vocabulary_does_not_know_stays_on_a_colour_camera`).

**Da confermare chiede solo i filtri che l'app non riconosce** (Marco, 25/9/2026: *"scritto e
riconosciuto si associa; scritto e sconosciuto, una domanda: che filtro e' H? per sempre"*). Uno
che il vocabolario riconosce non e' una domanda: non si elenca, non si conta, non si conferma. Una
lettera sola (`H`, `O`, `S`, `G`: lo fanno N.I.N.A. e ASIAIR) normalize non la indovina, ed e'
una domanda. Si risponde in tre modi: **e' uno dei miei**, scelto fra i filtri con la banda nota
(e' l'unione: la grafia dell'header diventa per sempre quel filtro); un **modello in commercio**
dalla tendina (che porta marca, nome ufficiale e banda); o **nome e banda** scritti -- per un duo o
tri-banda le bande che passa, e l'app ne ricava la banda canonica. Non nel wizard: al primo avvio
l'utente dovrebbe elencare cio' che possiede prima di aver visto cosa ha ripreso. `FILTER = none / no filter / open`, o un `FILTER` che non dice niente, **si chiede** (Marco,
2026-09-11): senza `BAYERPAT` una mono e una camera a colori non si distinguono. Si chiede nella
scheda della firma dell'header, insieme a camera e ottica (ADR 0014, S1; sotto, *L'attrezzatura
che i file non dicono*), e la risposta vale anche per i frame che verranno con quella firma.
**Una camera a colori non si chiede** (Marco, 23/9/2026: *"se i file dicono sensore a colori, e'
una camera a colori senza chiedere"*): i suoi frame senza filtro sono OSC. A essere a colori e' la
CAMERA e non il frame: vale cio' che l'utente ha scritto sulla scheda, poi cio' che i file hanno
votato, cosi' il programma che non scrive `BAYERPAT` non fa un frame mono in mezzo agli altri. I
file votano **prima** del giro, coi frame che la camera avra' alla fine: un frame senza matrice
sceglie il filtro sapendo gia' il colore, e quelli gia' fatti di una camera che cambia colore
rientrano nello stesso giro. Un duo-banda avvitato davanti a una camera a
colori, che il file non scrive, non lo vede nessuno: quelle ore stanno su OSC.
Alle altre camere le risposte sono tre: **a colori** (i frame sono OSC -- e come per chi scrive
`BAYERPAT` un filtro a banda larga diventa OSC, uno da avvitare resta se stesso --; si scrive sulla
scheda della camera, ed e' la stessa parola e la stessa risposta del colore scritto li'; senza una
camera, detta dal file, dalla risposta o dalla notte, non c'e' dove scriverlo e si rifiuta), **nessun filtro** (i
frame vanno sulla riga "nessun filtro"), o **uno dei tuoi filtri** (Marco, 25/9/2026), scelto fra
quelli con la banda nota: i frame vanno su quello. Queste due stanno sulla firma. La risposta tiene
il **nome** del filtro e non il suo id, che muore con la riga, percio' rinominare o unire quel filtro
se la porta dietro. Chi cambiava filtri senza che il file li scrivesse non ha una risposta: quei
frame restano senza filtro. I frame con la matrice restano OSC qualunque cosa dica la risposta. La
risposta dice cosa c'era davanti e la scheda della camera dice che sensore e': non si
contraddicono, quindi scrivere "a colori" non ritira la risposta -- la scheda smette di chiedere il
filtro, e tornando a mono la risposta e' ancora quella. Le due risposte che non sono "a colori"
scrivono anche mono sulla scheda della camera, ma **solo se non sono i file a dirla a colori**: un
"a colori" scritto prima lo riscrivono, o cambiare idea non sposterebbe niente. Rinominare o unire
una camera **non sposta** la risposta: sta sulla grafia del file, e ogni grafia ha la sua.

"Nessun filtro" e' un valore esplicito, non un vuoto: una riga sola, col nome del vocabolario
(`None`), e a tradurlo per lo schermo e' la pagina; nasce confermata, perche' l'ha chiesta la
risposta. Rinominarla non insegna una regola, e non si unisce a un altro filtro ne' un altro in lei -- una regola su
`none` risponderebbe per ogni camera -- e se non c'e' e il suo nome e' gia' di un altro filtro non
si indovina: i frame restano da rivedere.

**Strumenti e corredi si rilevano, e si confermano una volta.** Ottica e camera vengono da
`TELESCOP` e `INSTRUME` risolti **via alias**, mai per stringa: cosi' due grafie dello stesso
pezzo restano un pezzo solo. Dalla stessa porta, e con gli stessi alias, nascono i tre pezzi che
il programma scrive **sulla singola posa** -- la ruota portafiltri (`FWHEEL`), il focheggiatore
(`FOCNAME`) e la camera di guida (`GUIDECAM`) -- che pero' **non entrano nell'impronta del
corredo**: cambiare ruota non fa un secondo corredo, e le loro ore le sa la posa, non il
corredo (`domini/attrezzatura.md`). **L'app non tiene una lista di nomi di montatura** -- invecchia, e
il nome cambia da utente a utente (`EQMod Mount` e `ZWO AM3` sono tutti e due veri) -- ma sa
**quale programma ha scritto il file**, e con l'ASIAIR `TELESCOP` e' la montatura, sempre: il
pezzo nasce `mount` e il corredo di quei frame resta **senza ottica**, che l'ASIAIR non scrive
da nessuna parte (misurato su 171 header di quattro utenti, 14/9/2026). Un corredo a cui manca
un pezzo e' vero; uno con la montatura al posto dell'ottica e' falso. **Quale fosse l'ottica lo
chiede Da confermare**, nella scheda della firma: la risposta da' l'ottica a ogni frame di quella
firma che l'ottica non la nomina, anche a quelli che arriveranno. Limite dichiarato: due ottiche
diverse alla stessa focale con la stessa camera sono una domanda sola. Corredo = (ottica, camera) a una focale, con le focali entro il **+-5 %** raggruppate
prima di scrivere; il binning non cambia il corredo, un riduttore si' (cambia la focale). **La
focale e' quella misurata dal cielo** dove c'e' (ADR 0016): dopo una soluzione, pixel (`XPIXSZ`, o
quello della scheda per il binning, mai quello ricavato dal cielo) diviso la scala, al millimetro,
in `frame_wcs.focal_mm`; senza, `FOCALLEN`. Il corredo nasce dall'header prima del cielo, e il
solver rimanda a `normalize` il frame la cui misura non e' la focale del corredo, rifatto nello
stesso giro prima del `done` di `solve` (`run.queue`)
(`test_a_reducer_the_header_does_not_say_moves_the_frames_to_the_true_focal`,
`test_the_frames_the_sky_sends_back_are_redone_in_the_same_run`,
`test_a_measure_within_the_tolerance_keeps_the_rig_and_redoes_nothing`,
`test_without_a_pixel_the_header_focal_stays`, `test_a_frame_without_a_header_focal_takes_the_measured_one`).
Firme dell'header e notte restano sulla focale dell'header: chiedono cio' che i file dicono. Le
specifiche non si cercano su internet: le compila l'utente. Il legame frame -> corredo si
congela dopo il cielo: la verita' storica sta nell'header e nella focale misurata. La chiave con cui un corredo e' stato rilevato
resta separata da cio' che l'utente cambia: rinominarlo o arricchirlo non crea un doppione.
Uno strumento che l'app non conosce nasce provvisorio e **si segnala, mai si scarta**; nomi
di ripiego non entrano nel DB (niente "Corredo sconosciuto": l'assenza si dice a schermo).

**L'attrezzatura che i file non dicono** (Marco, 12/9/2026; ADR 0014, S1). Camera, ottica e
filtro si chiedono in **una scheda per firma dell'header**: grafia di `INSTRUME` e di `TELESCOP`,
focale con la regola dei corredi (+-5 %), dimensioni del sensore e pixel -- mai la notte o la
cartella (Marco, 23/9/2026: *"si lavora a frame non cartelle"*). Un `TELESCOP` che il programma
dice montatura (l'ASIAIR) **non entra** nella firma: non dice niente dell'ottica, e due nomi di
montatura della stessa camera farebbero due domande sulla stessa ottica; e nessuna scheda propone
come ottica una grafia che un file chiama montatura. La firma si compone in un posto solo
(`spine/signature.py`) dai grezzi normalizzati come un alias, quindi una rinomina di pezzi non la
tocca. La scheda chiede **solo le parti che mancano**: la camera a chi non scrive `INSTRUME` (e
la notte non la dice, sotto), l'ottica a chi non la nomina (e la notte non la dice), il filtro a
chi non lo dice su una camera non a colori. Una parte che la scheda non chiede si rifiuta
(`not_asked`), invece di scriverla e non spostare niente. La scheda conta fra le cose da
confermare finche' ogni parte chiesta non ha la sua risposta; una parte non mandata tiene quella di
prima. A video la riga dice quei valori, non un percorso ne' una notte. Un frame che vive in due
cartelle si conta una volta, e una cartella ritirata o un file sparito non chiedono niente. Alla
camera si risponde scegliendo un corredo fra quelli che l'app conosce **oppure** scrivendo camera e
focale, e l'ottica se serve: i pezzi nascono da quei nomi come da un header -- chi non ha mai
nominato la sua camera in nessun file avrebbe un elenco vuoto da cui scegliere -- e l'ottica
dichiarata **vince** su `TELESCOP`. La **focale** si chiede con la camera, proponendo quella nativa
dell'ottica: un corredo a focale ignota non e' lo stesso corredo di uno a focale nota, quindi senza
chiederla resterebbero due gemelli per sempre con le ore spartite. La risposta vale **anche per i
frame che arriveranno con la stessa firma**, da qualunque cartella e in qualunque notte: si
accetta di perdere il caso raro della stessa firma con attrezzature diverse in notti diverse, e
cambiare il fuso di casa non la sposta. I corredi fra cui si sceglie li dice l'API, e la stessa
funzione rifiuta gli altri (`review_page.rig_choices`): uno **senza camera** non risponde --
sceglierlo lascerebbe i frame dov'erano -- e uno rimasto a zero frame e' un residuo. Il nome e la
montatura dati al corredo senza ottica passano al corredo che nasce dalla risposta.
**Prima della domanda, la notte** (Marco, 23/9/2026: *"camera mancante: quella degli altri frame
della stessa notte, se e' una sola"*). Se gli header della stessa notte -- la notte della posa, da
mezzogiorno a mezzogiorno nel fuso del posto -- dicono una camera sola, contate le grafie
unite come una, il frame ha quella e la scheda non gli chiede la camera. Vale anche quando il frame che la
dice arriva dopo: chi normalizza un frame che dice la camera rilavora i frame senza camera della sua
notte, e una seconda camera nella notte glieli toglie. Se nessun header della notte dice la camera, o
ne dicono piu' d'una, la camera si chiede; e un frame senza data prende la notte in cui il file e'
stato scritto. La risposta invece e' scritta, e **vince** sulla notte: una scheda risposta resta in
pagina. La notte da' anche l'ottica e la focale, se ne dice una sola (`spine/night_rig.py`).

**La notte della posa si scrive quando la posa entra** (`scan`, `frames.local_night` e
`local_tz`, con l'istante da cui viene in `night_instant`): da mezzogiorno a mezzogiorno nel fuso
delle coordinate dell'header, o del sito di casa, o in UTC se non si sa nessuno dei due; senza `DATE-OBS` e' la notte in cui il file e' stato scritto
(Marco, 27/9/2026). La leggono le domande per notte, il solver e la domanda sui luoghi, che vengono
prima di `group` o non sanno il sito. **Quando cambia il fuso di casa** -- nasce, se ne sceglie
un'altra, si sposta, si toglie -- le pose che non hanno un fuso dalle coordinate dell'header si riscrivono nel fuso
nuovo, e il gruppo dei frame senza nome, che porta la notte, si risceglie (`spine/home_nights.py`).
Nessuna risposta porta la notte nella chiave (ADR 0014, S2): l'oggetto dei frame senza nome sta
sull'impronta di ogni frame, l'attrezzatura sulla firma, e nessuno le deve spostare. La risposta
di un gruppo e' quella che i suoi frame portano: un gruppo che si divide la porta su ogni parte; su
due gruppi che diventano uno vale quella che c'era -- una sola, o la stessa su tutti e due --,
anche per le pose che non l'avevano, e con due risposte diverse la domanda torna aperta. Si perde
un caso: un frame arrivato dopo la risposta, che il fuso nuovo porta in un gruppo senza frame
risposti, torna una domanda.

**La copia calibrata non raddoppia le ore.** Stessa data, stessa camera e stessa esposizione
di un frame gia' in archivio: e' lo stesso scatto, non un'altra ora di cielo. Fra due gemelli
vince il piu' **originale**, e un frame e' una copia solo se un gemello e' piu' originale di
lui: prima il **marchio di riscrittura** (`CALSTAT`/`CALIBRAT`, lo stato di calibrazione; o
**due programmi diversi nominati insieme**, uno in una chiave di chi ha **scritto** il file --
`PROGRAM`, `SWMODIFY`), poi il software fra i quattro di ripresa. **I due marchi non pesano
uguale**: le calibrazioni applicate dicono che sono cambiati i **pixel**, due programmi nominati
insieme dicono solo che qualcuno ha toccato l'**header** -- e l'header di un grezzo lo riscrive
anche chi non lo calibra (un solutore, un correttore di metadati). Fra un grezzo cosi' e la sua
copia calibrata vince il grezzo. Che due grafie siano due
programmi lo dice **il vocabolario dei quattro**, mai la somiglianza fra le stringhe: `SGPro 4.4`
e `Sequence Generator Pro v4.4` sono lo stesso programma. Ed e' la ragione per cui la regola sta
nella spina (`spine/rewrite.py`) e non nel lettore dell'header, che il vocabolario non puo'
consultarlo. Un nome
solo non e' un marchio: e' la grafia con cui due dei quattro si presentano, e prenderla per un
marchio marchierebbe i loro grezzi. A pari indizi si contano tutte e due:
indovinare fonderebbe due frame veri ripresi nello stesso istante, e far sparire cielo vero e'
peggio che contarlo due volte. Il marchio guarda le **chiavi**, mai il nome che ci sta dentro
(i software supportati restano quattro), e da solo non toglie niente a nessuno: senza un
gemello, un file calibrato e' semplicemente il frame -- c'e' chi tiene solo quello. Il grezzo
vince, la copia porta `frames.copy_of` e resta in archivio con le sue posizioni; chi conta le
ore filtra `copy_of IS NULL`.
Perche' due criteri e non uno: chi elabora **non cancella** sempre la chiave di chi ha
acquisito, e chi riprende con un programma fuori dai quattro non e' riconosciuto nemmeno sul
grezzo -- in tutti e due i casi il software da solo non distingue i gemelli. **Il caso che resta
scoperto**, ed e' in coda: la copia che non dice di essere calibrata e nel cui header il
vocabolario non riconosce **nessuno** dei nomi -- cioe' chi riprende con un programma fuori dai
quattro ed elabora con un altro che l'app non conosce. Li' i due gemelli si somigliano davvero,
e l'app li conta tutti e due.

**ASTAP**: `astap_cli -f <file> -o <cache>/<frame_hash> -fov <campo> -z 0 -wcs`, con
`-ra/-spd` e raggio 30 gradi se c'e' un indizio di puntamento, altrimenti cieco; mai
`-update`, mai `-extract`.

**Il campo si calcola, ed e' la leva della velocita'.** `-fov` e' l'altezza del campo
in gradi, e si ricava da `naxis2`, `pixel_size_um` e `focal_mm_raw` -- tutti gia' nell'header.
Misurato su frame veri da 26 megapixel di due corredi diversi: **0,2 s** col campo dato,
**2,3 s** con `-fov 0`, **23 s** senza nemmeno il puntamento. La leva non e' il
raggio di ricerca, e' il campo; dove l'header non dice focale o pixel si passa `0` e si
paga la differenza. Il tetto di tempo e' 60 s, piu' del doppio del caso peggiore misurato.

**Ordine: prima un frame per sessione**, poi tutti gli altri dai piu' recenti -- e un frame
il cui header non porta il puntamento **eredita l'indizio da un frame gia' risolto dello
stesso oggetto** (la regola esatta e' piu' sotto): e' cio' che lo salva dai 23 secondi. La
cache `cache/solve/<frame_hash>.ini` e `.wcs` e' immutabile: un reset la rilegge invece di
ri-risolvere.

**HFD e stelle costano una seconda passata** (`-analyse`, +0,3 s a frame) e si prendono lo
stesso: rileggere l'archivio un'altra volta costerebbe di piu'. Vanno in `frame_metrics` con
`source = 'astap'`. **Il tilt no**: servirebbe `-extract`, che scrive un CSV **accanto al
FITS dell'utente** ignorando `-o` e la cartella di lavoro (verificato) -- e su una
condivisione in sola lettura fallirebbe. Tilt, eccentricita' e fondo cielo nascono con
`measure`, dove i pixel li leggiamo noi e non si scrive niente. La rotazione e' quella
misurata (CROTA2 da `CD`), mai `OBJCTROT`: ha il segno opposto a `CROTA2`, un offset che cambia a
ogni rimontaggio della camera, e vale `0` come sentinella su meta' dei frame. **Anche il centro si
misura**: quello dell'header sbaglia di qualche minuto d'arco, e a volte di quasi mezzo grado.

**I numeri che ASTAP stampa portano la virgola decimale** (`HFD_MEDIAN=9,1`): si leggono
sapendolo, o su una macchina italiana diventano zero in silenzio.

**Un frame non risolto porta un codice**, mai una frase. Resta in archivio, le sue ore
contano, il campo non si disegna, e la pagina dice quante sono e perche'. Ma i codici sono di
due specie, e confonderle e' un vicolo cieco:

- **si riprova da sola**: `astap_missing` (il solver non c'e' ancora), `file_missing` (il
  disco e' staccato) e `no_star_database` (ASTAP c'e' ma il suo catalogo stellare no). Il frame
  resta **da fare**, non fallito. Segnarlo fallito vorrebbe dire che chi installa ASTAP il
  giorno dopo, o riattacca il disco, o scarica il catalogo, non risolverebbe mai piu' niente:
  nessuno lo rimetterebbe in coda, e il pulsante direbbe "niente da fare";
- **e' andata cosi'**: `no_stars`, `no_solution`, `timeout`, `internal_error`. Il frame e'
  `failed` col suo motivo, e si riprova solo se qualcuno lo chiede.

**E il catalogo mancante ferma la corsa**, invece di ripetersi frame per frame. Il catalogo di
ASTAP e' un **download separato**, ed e' l'errore di installazione piu' comune: senza, *ogni*
frame fallira' identico, e lanciare il solver cinquemila volte per scoprirlo e' un'ora buttata
mentre la ricevuta direbbe solo "in attesa" senza dire perche'. Si ferma alla prima e lo
dichiara: lo stadio risulta **in errore col suo motivo**, non completato -- senza, la corsa
diceva `1 / 1`, completato e zero risolti su un archivio da cinquemila frame.
Le frasi su cui si riconosce sono quelle vere di ASTAP e sono **due**, perche' i modi di avere
il catalogo a meta' sono due: `No star database found.` (non scaricato) e `Error reading star
database.` (scaricato a meta', o unzip andato male) -- lette da CLI-2025.11.19, non a memoria.
Si confrontano in minuscolo e per contenimento, perche' il testo cambia da una versione
all'altra ma la parola chiave no.

**Il binning non moltiplica il campo.** `XPIXSZ` per convenzione **include il binning**:
*FITS File Header Definitions* (Diffraction Limited, la definizione da cui la chiave e' nata)
dice "Includes binning", N.I.N.A. lo fa dalla 1.10 (17/7/2020), l'header vero dell'ASIAIR
scrive "with binning" e un header vero di Voyager "after binning" <!-- software-ok: sono le
fonti -->. Moltiplicare darebbe un campo doppio su tutto un archivio a bin 2, che e' come non
darlo. Il **pixel fisico** della camera invece e' `XPIXSZ` diviso il binning
(`units.physical_pixel_um`), e un binning che l'header non dice vale "non si sa", non 1.

**L'indizio si eredita da un frame dello stesso OGGETTO**, non della stessa sessione: lo
stesso oggetto e' lo stesso pezzo di cielo anche a un anno di distanza e con un altro corredo,
e l'indizio serve solo a restringere la ricerca. La sessione non basterebbe: i pezzi mancanti
valgono vuoto, quindi due frame senza `OBJECT`
ripresi la stessa notte con lo stesso corredo la condividono pur guardando due punti diversi
-- ereditare li' manderebbe il solver nel posto sbagliato, e non risolverebbe mentre alla
cieca ce l'avrebbe fatta.

**Il cielo si salva anche senza il suo rettangolo.** Centro e scala sono la soluzione;
rotazione e campo servono a disegnare il riquadro, e possono mancare (matrice degenere,
header che non dice quanti pixel ha il sensore). Restano vuoti, e la soluzione si salva
lo stesso: pretenderli tutti butterebbe via un cielo misurato davvero.

**Dove stanno i dati** (`platformdirs`): Windows `%LOCALAPPDATA%\AstroLog`, Mac
`~/Library/Application Support/AstroLog`, Docker `/data`. Dentro: `astrolog.db`, `cache/`,
`log/`. Il DB non va mai su una condivisione di rete; le cartelle dei FITS si'.

**Il primo avvio**: un wizard con quattro passi -- nome, sito principale, cartelle, la chiave
Meteoblue facoltativa -- saltabile
e riapribile; alla fine, se c'e' almeno una cartella, la prima scansione parte da sola (oggi, se non parte, non lo dice: [in coda](../coda.md), *Per il
disegno nuovo*, *Primo avvio*). L'attrezzatura non si dichiara qui: al buio l'utente dovrebbe elencare cio'
che possiede prima di aver visto cosa ha ripreso. Si vede e si corregge nell'Attrezzatura, dove
ogni pezzo trovato e' davanti agli occhi con quanti frame vale.

**Da confermare: solo cio' che l'app non puo' sapere** (Marco, 25/9/2026: un pezzo nuovo non e'
una domanda, si vede nell'Attrezzatura). Dell'attrezzatura restano due domande: i filtri che l'app
non riconosce, e due grafie che hanno l'aria di essere la stessa camera. Poi le *schede
dell'oggetto*, una per gruppo di frame -- un oggetto trovato, o frame senza nome e senza cielo --:
in cima quelle che chiedono una risposta; quelle che l'app sa, su cui non c'e' niente da
scegliere, stanno chiuse, e si aprono a pagine (Marco, 27/9/2026). E le domande sui **gruppi
di frame**, una per ogni cosa che l'app non puo' sapere:
il sito, e l'attrezzatura che i file non dicono. Quante sezioni siano lo dice `ReviewOut`, non questa riga: un numero scritto qui
direbbe il falso alla prossima domanda che nasce. Dentro l'ordine fisso delle sezioni, prima i
gruppi che toccano piu' frame (`api/review.py`, `api/review_page.py`; prove
`test_the_most_used_filters_come_first`, `test_a_question_per_group_with_the_largest_first`,
`test_a_question_per_camera_with_the_largest_first`; degli oggetti
`test_the_ones_to_decide_come_first` prova solo che quelli in dubbio stanno in cima; per l'ordine
per frame degli oggetti e per i siti la prova manca, vedi [`coda.md`](../coda.md) *Macchine che
non guardano*). Le decisioni si
prendono cliccando e **"Applica" le scrive in un colpo solo**: diventano dichiarazioni e
regole (`header_aliases`) valide per tutto l'archivio, non per la sola scansione. **Applica
scrive solo le risposte** (ADR 0014, S4): niente si conferma guardandolo. Non blocca: i frame
sono gia' in archivio, rispondere migliora i nomi.

**Due rotte, non venti.** `GET /review` porta tutta la pagina in una risposta: le grafie che
sembrano un pezzo solo, i filtri che l'app non riconosce e quelli fra cui si sceglie la risposta, i
corredi fra cui si sceglie, gli oggetti coi
conteggi, **i gruppi di frame su cui l'app chiede** -- ognuno con la sua chiave stabile, quanti
frame vale e la risposta gia' data, se c'e' -- e quante domande aspettano una risposta. `POST /review/apply` prende tutte le
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
dell'oggetto nuovo. **Il nome che si da' a un corredo resta una dichiarazione**, con la chiave
(ottica, camera, focale): la riga di `rigs` e' rilevata e un'unione di due grafie la cancella, il
nome invece deve tornare quando la spina ricostruisce lo stesso corredo.

**Vedere non e' rispondere** (Marco, 14/9/2026): sul suo archivio un Applica a vuoto spegneva
**58** voci, e **sette** erano domande aperte. Con S4 un Applica a vuoto non spegne niente.
I numeri di riga di quelle tabelle **non si riusano** (`AUTOINCREMENT` in `schema.sql`): i filtri
si rispondono col numero, e un numero riciclato darebbe a una riga la risposta scritta per
quella di prima.
**La scheda chiede solo i campi del suo tipo**, e li manda l'API (`cards` dell'Attrezzatura):
quali siano lo dice *Le schede* piu' sotto, scritto una volta in
`instrument_answer.CARD`. **Si unisce solo dove la spina accetta** (`mergeable_into`: stesso tipo, e
un tipo con grafie da unire): la regola e' una, `gear.mergeable`, e la leggono sia la pagina sia
l'unione vera.

**Due grafie della stessa camera sono una domanda** (Marco, 15/9/2026: `ATR2600M` e
`ATR2600M(USB2.0)` sono la stessa camera vista da due driver). Un'unione non si disfa, quindi serve
una **prova positiva** e non l'assenza di differenze: la regola larga proponeva `Canon EF (50mm)`
con `(200mm)` e `Atik 460EX (Mono)` con `(Color)`, 7 false su 28 coppie plausibili. Somigliano due
**camere** con **lo stesso nome** -- tolti maiuscole, spazi, segni e cio' che sta fra parentesi,
dove il driver scrive un'annotazione come l'indice ASCOM `(1)` --, **lo stesso pixel noto per tutte
e due** dai file o dall'utente -- quello ricavato dal cielo no, porta l'errore della focale --, e **lo stesso colore**, dove il colore che manca vale mono (una mono letta dai file non lo
porta mai, e dire "mono" su una sola grafia non deve separare le due). "Comincia come l'altro" non basta: `QHY268M` e `QHY268MC` sono due sensori.
Gli altri generi no -- ottiche, montature, ruote, focheggiatori, camere di guida: non hanno un
dato che provi niente, e si uniscono dall'Attrezzatura. Si chiede
sulla grafia con meno frame, verso quella con piu' frame (`lookalike.lookalikes`): "sono lo stesso
strumento?", perche' l'app non puo' saperlo -- due camere dello stesso modello sono due pezzi (Marco,
25/9/2026). Niente e' preselezionato, e conta fra le cose da confermare finche' non si risponde:
guardarla non e' rispondere. Si' e' l'unione; **no e' una risposta come il si'** -- senza, l'unico
modo di far tacere una domanda sbagliata, come due corpi distinti apposta con una parentesi
(`Canon EOS 6D (Ha mod)`), sarebbe accettarla. Il no si scrive sulla camera chiesta col **nome**
dell'altra (`declarations.not_same_as`), uno per ogni coppia, e vale in tutte e due le direzioni,
perche' quale grafia ha piu' frame puo' cambiare. Il nome dell'altra la segue quando si rinomina o si
unisce a una terza (`declarations.follow_not_same_as`).

**Le bande che si dichiarano sono quelle fisiche** (L, R, G, B, Ha, Hb, OIII, SII): "duo",
"tri" e "OSC" sono etichette che si RICAVANO da quelle, e nessuno le dichiara. Tre bande
danno un tri-banda solo se sono strette; tre filtri a banda larga no.

**Il lavoro che aspetta si puo' far partire**: `POST /pipeline/run` avvia cio' che e' rimasto
in coda. Senza, una risposta data mentre il worker era occupato aspetterebbe la prossima
scansione.

**Unire due grafie e' una regola, non una fusione di righe.** Quando l'utente dice che
`ATR2600M` e' lo stesso pezzo di `ATR2600M(USB2.0)`, si scrive la regola
(`header_aliases`), si toglie la riga assorbita e si rimettono in coda i frame che la
usavano: `normalize` li riaggancia al pezzo giusto. Nessun dato si perde, perche' il grezzo
dell'header non si tocca mai.

**Una regola porta a un nome, e i nomi cambiano.** Quindi rinominare un pezzo -- o unirne due e
poi rinominare quello tenuto -- porta con se' anche **le grafie che gia' arrivavano a lui**, non
solo quella di un attimo prima (`declarations.rename`). Una regola lasciata indietro punta a un
nome che non e' piu' di nessuno, e la prima posa nuova con quella grafia fa rinascere il pezzo
vecchio: senza scheda, senza risposte, con le ore spartite fra due righe.

**Gli oggetti si dichiarano in Da confermare, una scheda per gruppo di frame** (ADR 0014, S3):
i frame che `identify` ha messo su un oggetto (chiave `object:` e la chiave stabile), o un gruppo
di frame senza nome e senza cielo (chiave `frames:` e la chiave del gruppo). La scheda e' una
(`ObjectCard`), e la risposta pure: una voce del catalogo, un nome scritto, o "non e' un
oggetto". In cima le domande -- i gruppi e i dubbi (`identity_confidence = 'low'`) senza
risposta --, coi **candidati che il cielo ha trovato nel suo campo** da cliccare quando ne ha
trovati; zero candidati e' una scheda come le altre. Le schede degli oggetti che l'app sa, senza
niente da scegliere, stanno chiuse e si aprono a pagine, coi conteggi.

**"Non e' un oggetto" vale anche su un oggetto trovato** (Marco, 6/10/2026): uno scatto di prova,
una messa a fuoco. Si scrive sull'impronta di ogni frame della scheda, fissati al momento della
risposta -- un frame che arriva dopo e il cielo riconosce e' del cielo --, e `identify` lo legge
**prima** del nome e del cielo: il frame chiude `skipped` con `not_an_object`, fuori dalle ore e
da ogni oggetto. Cosa aveva trovato resta sul frame (`frames.found_key`), perche' la riga
dell'oggetto senza frame si cancella e la scheda deve restare, coi candidati del cielo, per
cambiare idea; la scheda risposta non conta. Rispondendo poi un oggetto, quei frame tornano e la
correzione li sposta; quelli senza nome ne' cielo, che solo la risposta del gruppo legava, la
correzione non li raggiunge: prendono l'oggetto sull'impronta, come risposta del loro gruppo, e
fuori tengono la chiave della scheda anche se senza risposta non troverebbero niente. Un gruppo senza nome scrive e legge la sua risposta solo sui frame senza un
cielo coi candidati: dove il cielo li ha, decide lui, anche se il frame ha ancora la chiave del
gruppo e anche se il cielo arriva dopo la risposta. Per distinguerle, la risposta su un oggetto
trovato scrive subito `frames.found_key`; quella di un gruppo no.

I frame che l'header non nomina e di
cui il cielo non dice niente si chiedono **per gruppo** (`spine/unnamed.py`): la notte, la camera,
il telescopio e **dove puntava la montatura** (Marco, 24/9/2026), mai per file e mai per cartella.
Il gruppo **si sceglie quando il frame arriva, e si scrive sul frame** -- si risceglie solo se casa
cambia fuso e con lei la notte del frame --
(`frames.unnamed_key`, Marco, 25/9/2026): il frame entra nel gruppo della sua notte, camera e
telescopio il cui puntamento dista meno del lato corto del campo inquadrato (da focale, pixel e
sensore), il piu' vicino; altrimenti ne apre uno col proprio puntamento. Si confronta con chi ha
aperto il gruppo, non con ogni frame del gruppo, o una fila di frame lo allungherebbe a catena. Non
e' una griglia fissa perche' una griglia ha dei bordi, e il dithering a cavallo di un bordo
spezzerebbe lo stesso oggetto in due domande. Il prezzo di un gruppo scritto e' che dipende
dall'ordine in cui i frame arrivano, e non si rifa' quando ne arrivano altri. Senza puntamento,
focale o pixel il campo non si sa e quei frame si separano solo per notte, camera e telescopio:
**due oggetti ripresi cosi' nella stessa notte fanno una domanda sola, e la risposta li mette tutti
e due sullo stesso oggetto** -- come due oggetti puntati a meno di un campo l'uno dall'altro. Un
mosaico a pannelli, coi frame in ordine sparso, puo' invece dividere un pannello fra due gruppi. Ogni notte e' una domanda: lo stesso oggetto ripreso tre notti se ne
chiede tre volte. `OBJECT` non c'entra: questi frame non lo scrivono. La risposta raggiunge i frame del gruppo da
qualunque cartella, compresa una copia calibrata. I candidati del cielo di una scheda li
**scrive chi identifica**, a fine giro e solo per gli oggetti in dubbio e per i frame detti "non e'
un oggetto", un frame per scheda, sotto la chiave stabile
(`spine/object_candidates.py`, Marco, 22/9/2026: una lettura non calcola mai); si riscrivono anche
dopo un catalogo nuovo e dopo una risposta "sono file di calibrazione", che stacca il cielo senza
far lavorare identify. Da confermare li legge, e un contratto le vieta il cono.

**Una risposta e' una CORREZIONE, non un lucchetto**, e questa e' la riga da cui dipende tutto
il resto: *cio' che avete trovato come `ngc-7023`, per me e' `ldn-1174`*. Il lucchetto
`identity_method = 'user'` protegge l'**oggetto**, non il frame, quindi al primo ricalcolo
`identify` rifarebbe la sua strada dal cielo e riporterebbe i frame dov'erano -- la risposta
sarebbe muta. La correzione invece sta in `declarations`, si rilegge a ogni giro e sopravvive a
un azzeramento del rilevato. **Si segue a catena** -- se l'utente si corregge, la seconda
risposta scavalca la prima. **Un ripensamento disfa cio' che rovescia** (Marco, 9/10/2026):
se la correzione nuova chiude un anello -- *M 9 e' la Cometa*, poi *la Cometa e' M 9* -- vince
l'ultima, e quella vecchia che riporterebbe indietro si toglie quando la nuova si scrive
(`test_a_second_thought_undoes_the_correction_it_reverses`,
`test_a_renamed_object_comes_back_from_its_own_card`). Chi legge la catena tiene comunque conto
di dove e' gia' passato: un anello scritto da fuori non gira all'infinito. E la risposta viaggia su una **chiave stabile** (lo slug, o il nome), mai
sul numero di riga: gli oggetti rimasti senza frame si cancellano e rinascono con numeri nuovi, e
una risposta agganciata a un numero punterebbe al nulla. Un bersaglio che il
catalogo non conosce si rifiuta **subito**, con un codice: una dichiarazione puo' spostare dei
frame, mai farli sparire, e nemmeno puntare al nulla.

**E una risposta chiude la domanda.** L'oggetto corretto vale `user`/`user` -- anche, e
soprattutto, dove il cielo era in dubbio, che sono i due rami per cui questa pagina esiste: la
correzione e' agganciata alla chiave che la pagina mostrava, quindi e' la risposta a *quella*
domanda. Vale anche quando la risposta nomina proprio l'oggetto trovato ("e' giusto"): la
correzione su se' stessa si applica una volta, e l'oggetto diventa `user`. Lasciarlo `low` voleva dire rimetterlo in cima coi suoi candidati subito dopo il clic, e
poterlo richiedere all'infinito. Per la stessa ragione la ricevuta conta una richiesta solo se la
pagina la fara' davvero: se il frame finisce su un oggetto gia' lucchettato, il suo dubbio non
arriva a schermo, e contarlo direbbe "1 da rivedere" con la pagina che ne mostra zero.

**E diventa una regola solo se la grafia non e' ambigua.** "Quando l'header dice X, e' Y" vale
per tutto l'archivio, ma si impara **solo se quella grafia punta a un oggetto solo**: un
`Snapshot` che sta su due cieli diversi non e' un nome, e' un segnaposto, e una regola su di lui
tirerebbe su un oggetto frame che guardavano tutt'altro (Marco, 2026-09-09). Le grafie si
confrontano **ripulite** dalle parole di tavolozza, la stessa forma con cui si cercano:
`Snapshot LRGB` e `Snapshot RGB` sono la stessa grafia, e valutarle grezze le farebbe sembrare
univoche tutte e due.

**La regola vale dove il cielo non c'e'; dove c'e', decide il cielo e sposta la correzione.**
Le due strade non si sovrappongono mai, ed e' il punto che e' costato due giri di revisione. Per
un filtro o uno strumento la grafia dell'header e' l'unica fonte, e li' una regola e' tutto cio'
che c'e'. Per un oggetto no: c'e' una **misura**, ed e' migliore di una stringa di testo. Dove il
cielo c'e' si decide guardando lui, e a portare la parola dell'utente e' la **correzione** --
che e' agganciata a cio' che l'app ha dedotto guardando il cielo, quindi non puo' entrare in
conflitto con lui. Dove il cielo non c'e', la regola e' la sola cosa che resta, e vale
`user`/`user`.

Le due versioni sbagliate, perche' non si rifacciano: applicata alla decisione, la regola
scavalcava il cielo e **lucchettava** -- un frame che aveva fotografato M 83 finiva su M 31 senza
nessuna domanda, cioe' il danno che la regola sull'ambiguita' doveva impedire, aggirato dal lato
lettura. Spostata sul nome, metteva il nome corretto in conflitto col cielo originale e **l'app
richiedeva su tutti i frame a cui l'utente aveva appena risposto**: 41, misurati sull'Iris.

La risposta rimette in coda i frame toccati, e l'Applica fa ripartire **`identify`**; se nello
stesso gesto si e' risposto anche su un filtro o un pezzo, parte prima la normalizzazione e poi
`identify`, perche' con la sola normalizzazione la risposta sugli oggetti resterebbe ferma.

**Un oggetto rimasto senza frame sparisce**, e la spazzata sta **all'inizio** della corsa,
subito dopo aver staccato i frame da rifare. Non e' pulizia di comodo, e il momento non e' un
dettaglio: quando una risposta sposta i frame, cio' che resta indietro comparirebbe nella pagina
come *"NGC 7023 -- 0 frame"* -- misurato sui 41 frame veri dell'Iris -- e **terrebbe in ostaggio
i suoi nomi**. A fine corsa era troppo tardi: il vecchio se li portava via col `CASCADE`, e la
grafia che l'utente aveva scritto nell'header spariva dall'archivio. All'inizio, i nomi sono
liberi proprio nella passata che li riassegna.

Vale **anche per gli oggetti `user`**: l'utente non crea oggetti, crea correzioni, e gli oggetti
li fa `identify` quando un frame ci va -- quindi uno a zero frame e' sempre un residuo. Si vede
correggendosi due volte: senza, il primo bersaglio restava li' tenendosi la sigla, e l'oggetto
giusto ripiegava sul nome comune. Non si perde niente, perche' l'oggetto e' un derivato e la
parola dell'utente vive in `declarations`.

E **le sessioni di quell'oggetto se ne vanno con lui**, senza portare via nessun frame: il
vincolo e il perche' stanno accanto a `sessions.object_id` in `schema.sql`, e `group` -- che
nella catena viene subito dopo -- rifa' la sessione. Prima non era cosi', e premere Applica su
un archivio gia' raggruppato moriva col database in faccia (misurato sugli 11.005 frame di
Marco: `FOREIGN KEY constraint failed` 0,16 s dopo l'inizio di `identify`). L'altra strada -- risparmiare
l'oggetto finche' una sessione lo punta, senza toccare lo schema -- e' stata provata e
scartata: lo lascia in piedi a zero frame coi suoi nomi in ostaggio, cioe' rimette il difetto
qui sopra, perche' dopo l'Applica i frame sono `done` e nessuna corsa lo ripassa.

**`identify` -- il nome decide, il cielo controlla.** Ha due fonti che possono contraddirsi: il
nome scritto nell'header e il cielo misurato dal solver, e nessuna delle due vince muta. Le
otto situazioni qui sotto sono l'incrocio delle due.

*Il fatto da cui parte tutto*: su cinque bersagli su sei **il candidato piu' vicino al centro e'
quello sbagliato** -- puntando M 31 il piu' vicino e' M 32, puntando M 101 e' NGC 5447, sulla
Rosetta e' Ced 76 (misurato in `old/`, `old/backend/astrolog/catalogs/propose.py:8-12`). Il
soggetto e' quasi sempre l'oggetto grande e luminoso che **contiene** il puntamento, non il
piu' vicino. Per questo i candidati si **pesano** -- contenimento, magnitudine, dimensione,
importanza del catalogo, centratura -- invece di prendere il primo della lista.

*La geometria*: la ricerca al catalogo e' un cono, perche' non esiste una query a rettangolo,
e il suo raggio **non** e' la mezza diagonale del campo: e' almeno tre gradi. Su un campo
stretto un oggetto grande ha il centro fuori dall'inquadratura e contiene il puntamento lo
stesso -- e' proprio il soggetto, e cercando solo quanto e' larga la foto non tornerebbe mai.
La mezza diagonale serve a un'altra domanda, quanto e' grande la foto, e li' e' l'unico raggio
che copre gli angoli. Poi, per ogni candidato, si dice se cade
**dentro il rettangolo vero** dell'inquadratura (centro, lati e rotazione, che `frame_wcs` ha)
o se e' solo li' vicino. Il rettangolo e' un'**informazione, non un filtro**: scartare e'
l'operazione pericolosa, e "M 31 e' nell'inquadratura, NGC 206 e' fuori" e' cio' che l'utente
vuole leggere. Dove la rotazione o i lati mancano -- lo schema dice che possono mancare a
soluzione buona -- si ricade sul cerchio, e si dice.

*Cosa NON si porta da `old/`*: il livello di fiducia a due gradini (`SLOP_GOTO_DEG`) e il
pavimento di 0,3 gradi sul metro del punteggio. Erano tarati su un mondo in cui il **94,5%**
dei frame non era risolto e le coordinate venivano dal GoTo. Qui `frames.ra_hint_deg` e'
dichiarato *indizio per il solver, non verita'*, e i casi sono due soli: cielo misurato, o
nessun cielo. Il caso di mezzo non esiste piu'.

**Le otto situazioni, e cosa fa l'app in ognuna** -- `name_only` occupa due righe perche' il
metodo cambia col nome usato, ma la situazione e' una. Nessun'altra: e' il vocabolario chiuso di
`objects.identity_method` e `identity_confidence`, gia' nello schema, e ogni riga qui sotto ha
il suo `branch` nel codice -- un nome, non una frase, perche' un test che distingue i rami
leggendo la prosa di un motivo non e' un test.

| il nome dice | il cielo dice | esito | metodo / fiducia | `branch` |
|---|---|---|---|---|
| una cometa o un asteroide | **non si consulta** | **aggancia a un oggetto fuori catalogo che porta quel nome** | `exact_name` / `high` | `moving` |
| una sigla | fra i candidati c'e' quella sigla, in cima o no | **aggancia a lei** | `coord_confirmed` / `certain` | `name_and_sky_agree` |
| una sigla | solo altre cose: quella sigla nel campo non c'e' | **Da confermare**, col nome agganciato come ipotesi e cosa c'e' invece a quelle coordinate | `coord_review` / `low` | `sky_disagrees` |
| niente, o un nome libero | una cosa sola e sicura | **aggancia** | `coord_confirmed` / `certain` | `sky_only` |
| niente, o un nome libero | piu' candidati vicini di punteggio | **Da confermare**, agganciato al migliore | `coord_review` / `low` | `sky_ambiguous` |
| una sigla | niente cielo (frame non risolto) | **aggancia dal nome** | `exact_name` / `high` | `name_only` |
| un nome storico (`NGC 224` per M 31) | niente cielo | **aggancia dal nome** | `historic_name` / `high` | `name_only` |
| un nome libero | niente cielo | **aggancia a un oggetto fuori catalogo che porta quel nome**, e va in Da confermare | `exact_name` / `low` | `free_name_only` |
| niente | niente cielo, o un cielo senza candidati | nessun oggetto: lo stadio si chiude `skipped` col codice `no_name_no_sky`, e Da confermare lo chiede **per gruppo** (notte, camera, telescopio, puntamento); se l'utente ha detto che non e' un oggetto, `skipped` col codice `not_an_object` | -- | `nothing` |

Prima di tutte le righe: un frame che l'utente ha detto **"non e' un oggetto"** -- dal suo gruppo
(solo se il cielo non ha candidati) o dalla scheda di cio' che era stato trovato -- chiude `skipped` col codice `not_an_object`, e
cio' che il nome e il cielo avrebbero deciso resta in `frames.found_key`.

Con un **oggetto del gruppo** detto dall'utente, il frame senza nome decide come se quel
nome fosse scritto -- `name_only` per una voce di catalogo, `free_name_only` per un nome scritto --
con `user` / `user`. Nel gruppo che lo chiede il frame resta per `frames.empty_cone`, che
`identify` scrive a ogni giro -- cono vuoto, cono con candidati, o nessun cielo -- e che una
rimessa in coda non azzera.

Il `certain` e' riservato a nome e cielo **concordi**: il solo nome vale `high`, mai `certain`.
Il ramo Da confermare **aggancia comunque** il suo best-guess: un frame non resta mai scollegato,
e nessuna ora si perde. La risposta dell'utente vale `user` / `user` e non si sovrascrive mai:
chi scrive controlla il lucchetto prima di toccare un oggetto.

**Un oggetto mobile si guarda per primo e sopprime il cielo.** Una cometa era li' quella notte
e non ci sara' la prossima: il cono restituirebbe l'oggetto fisso che le stava dietro, con tutto
il punteggio del caso, e lo direbbe **sicuro di se'**. Il lessico che la riconosce sta in
`vocab.moving` e sbaglia apposta per difetto: dichiarare mobile un oggetto fisso lo toglierebbe
da ogni coda e nessuno lo rivedrebbe piu'.

**La sigla dell'header scioglie l'ambiguita' ovunque stia fra i candidati**, non solo quando e'
il migliore: i candidati sono gia' cio' che si sovrappone all'inquadratura, quindi trovarla li'
vuol dire che il cielo la conferma, e quale pezzo dello stesso complesso vinca il punteggio non
e' una domanda da girare all'utente -- `M 86` davanti a `NGC 4438`, o `NGC 869` davanti a
`C 14`, che *e'* il Doppio Ammasso. Si chiede quando fra i candidati quella sigla **non c'e'**
(`sky_disagrees`), o quando un nome non c'e' e due candidati contendono (`sky_ambiguous`). E' la
definizione della spina: *"se l'header dice un nome che sta nel campo, quello vince"* (Marco,
2026-09-12). **Si guarda l'elenco intero**, non i sei che la pagina mostra: su un campo di
Orione i candidati sono venti e `NGC 1977` e' il settimo, e il tetto taglierebbe la regola.

**Un nome libero non crea mai un oggetto quando il cielo c'e'**: li' il cielo e' la misura e il
nome e' un'etichetta. Lo crea solo dove non c'e' altro (`free_name_only`), e con fiducia `low`,
perche' `Snapshot` puo' essere il nome di un oggetto quanto il segnaposto di un programma --
sono i sette frame di M 101 del collaudo. Il nome grezzo entra in `object_names` con
`origin = 'raw'`, anche quando l'oggetto viene dal cielo: e' cio' che l'utente ha scritto. Cade
in un caso solo -- quel nome e' gia' di un **altro** oggetto, e un nome appartiene a un oggetto
solo -- e allora si scrive nel log: cade, ma non in silenzio. Il contatore `name_taken` della
ricevuta conta i **nomi** non entrati, non i frame: quelli di catalogo e quello grezzo, e un
frame solo puo' valerne tre.

**Lo stadio parte anche su un frame che il solver ha rinunciato a risolvere**, mai su uno che e'
ancora in coda: `failed` e' definitivo, `pending` no, e agganciare dal nome un frame che fra un
minuto avra' il suo cielo sarebbe una risposta data in fretta. Senza questa eccezione -- che sta
in `spine/stages.py`, dichiarata per la coppia `(identify, solve)` e per quella sola -- due delle
otto situazioni non potrebbero **mai** accadere.

*E qui c'e' un'attesa voluta che va detta*: **finche' ASTAP non e' installato i frame non hanno
oggetto**. Il solver li lascia `pending` -- non `failed` -- perche' li riprovera' da solo appena
l'eseguibile arriva, e `identify` aspetta con loro. E' coerente con "il cielo arriva dopo": si
aspetta il cielo invece di agganciare un nome che poi il cielo potrebbe smentire. Il costo e'
che al **primo avvio senza ASTAP l'Archivio non ha oggetti**, e la stessa cosa vale per un
disco staccato.

*E percio' l'app deve accorgersene e dirlo prima, non dopo* (Marco, 2026-09-09): nel pacchetto
ASTAP c'e' dentro e nessuno ci pensa, ma chi installa da sorgente vedrebbe un archivio muto
senza sapere perche'. Il wizard resta di **quattro passi per tutti**, e ne aggiunge un **quinto
solo quando il solver non si trova**: dice cosa si perde senza (i frame entrano, ma restano senza
cielo e senza oggetto), lascia indicare dove sta, ed e' saltabile. E' la regola di sempre --
tutto automatico, manuale per eccezione -- e il momento giusto e' **prima della prima
scansione**. Dove sta il solver lo dice l'utente con la preferenza `astap_path`, che viene
**prima** della ricerca automatica e della variabile d'ambiente `ASTROLOG_ASTAP` (quella la
mette chi lancia l'app, non chi la usa). La ricerca ha una casa sola, `solve.solver_path`: la
leggono lo stadio che risolve e la riga di `missing` che avvisa a schermo, cosi' l'avviso non
puo' dire una cosa e la corsa farne un'altra.

**Senza catalogo caricato vale la colonna "niente cielo"**, anche su un frame risolto: il cono
non ha nessuno da restituire, quindi la decisione ricade sul nome dell'header. L'app cataloga,
cerca e conta le ore lo stesso -- ma gli oggetti che nascono cosi' sono fuori catalogo, e
quando il catalogo arriva **non si rifanno da soli**: `load_catalog` non chiama `invalidate`,
e quegli oggetti restano fuori catalogo finche' qualcosa non rimette in coda i loro frame -- una
dichiarazione in Da confermare, o una scansione che li tocca. Chiuderlo e' in coda.

**Come si chiama un oggetto** -- tre invarianti che questa casella fissa, e che chi mostra un
oggetto deve conoscere prima di fare il join:

1. Il nome **primario** e' il primo **libero fra quelli che il catalogo gli da'** (la sigla,
   poi il nome comune), non il primo della lista: `HCG 92` puo' arrivare quando "Stephan's
   Quintet" e' gia' di `NGC 7318`. Su un oggetto di catalogo il nome grezzo dell'header entra
   **sempre non-primario**: l'etichetta che l'utente ha scritto sul file si conserva, ma non e'
   come l'oggetto si chiama. Fuori catalogo e' il contrario, ed e' il punto 3.
2. Un oggetto **di catalogo** puo' quindi non avere **nessun primario**, e non e' rotto -- con
   zero righe se tutti i nomi del catalogo erano presi, o con la sola riga del nome grezzo. Il
   suo nome si legge dal catalogo per `catalog_slug`, ed e' il ripiego giusto: meglio
   `NGC 7318` che `Quintetto_2024`.
3. Un oggetto **fuori** catalogo ha sempre almeno un nome, ed e' il suo primario -- perche' chi
   aggancia cerca prima per nome, e su un nome gia' speso si attacca all'oggetto che ce l'ha
   invece di crearne un altro.

Quindi **"il nome di un oggetto" non e' una colonna, sono due passi**: il primario se c'e',
altrimenti il catalogo. La funzione che li fa e' `spine.objects.display_name`, ed e' **una
sola**: chi mostra un oggetto la chiama, e non rifa' il `JOIN` per conto suo -- rifatto a mano,
mostrerebbe una scheda vuota proprio sull'oggetto nato da una collisione, cioe' il caso piu' raro
e piu' difficile da vedere.

**Un oggetto di catalogo e' uno.** Due frame della stessa galassia non devono creare
due righe, o le ore si sparpagliano -- che e' il difetto contro cui esiste tutta questa casella.
Lo garantisce il database con un indice unico su `objects.catalog_slug` e su `object_names.name`.
L'unicita' sul nome e' **globale, non per oggetto**: due oggetti che si chiamano tutti e due
`M 31` sono il difetto stesso. Chi scrive non fa `INSERT` e prega -- cerca e poi crea, e
l'indice e' la rete sotto, non la strada.

**Cosa `identify` NON fa**: non sa che `NGC 2244` sta **dentro** la Rosetta. La relazione
pezzo/adiacenza e' misurata in `old/` e mai costruita; serve al Planner e alla Carta del cielo, non a
contare le ore, ed e' in coda. E non tocca i FITS, mai.

**Le schede: un campo si chiede solo se l'app ci fa qualcosa.** Ottica: marca, modello,
apertura, focale nativa. Camera: marca, modello, mono o colori, dimensione del pixel.
Filtro: marca, modello, tipo (la banda, dalla tendina) e la larghezza in nanometri **per
ogni banda** che lascia passare -- un Ha a 3 nm ha una riga, un duo Ha/OIII ne ha due; la
larghezza e' facoltativa. Riduttore: il fattore. Montatura: quanto regge. Ruota: quanti
filtri ci stanno. Su ogni pezzo: peso e una nota. Rapporto focale, lato del sensore in
millimetri e scala in arcosecondi per pixel **si derivano**, e non si chiedono mai: un
numero calcolabile scritto a mano e' lo stesso fatto in due case. Dimensione del pixel,
focale e "camera a colori" arrivano gia' compilate dall'header quando c'e'. Per la camera
**decidono i file, non il primo che capita**: il pixel fisico e la matrice di Bayer piu'
frequenti fra i frame che la usano, ricalcolati a ogni giro di `normalize`, e a pari file
nessuno (scelta di Marco, 2026-09-11). Cio' che l'utente scrive su quei due campi sta fra le
dichiarazioni, non nella colonna rilevata: nessun ricalcolo lo tocca, rinominare la camera se
lo porta dietro, e nell'unione di due camere vince la scheda di quella tenuta.

**`group` mette insieme le notti e le sessioni.** La notte va **da mezzogiorno a mezzogiorno
nel fuso del sito**, mai in UTC: sull'archivio di collaudo le due strade danno lo stesso
risultato (zero frame cambiano notte), quindi la regola non e' per Marco -- e' per chi riprende
dove il fuso conta, ed e' la decisione che il vecchio aveva gia' rovesciato una volta. Una
**sessione** e' oggetto x notte x corredo, coi filtri dentro: cambiare telescopio o camera a
meta' notte apre un'altra sessione. La chiave della sessione e' un indice **su un'espressione**
perche' un corredo che non si e' potuto sapere e' vuoto, e in SQLite due vuoti non contendono.

**Da dove hai ripreso si chiede, non si indovina.** Le coordinate dell'header sono un indizio:
entro **1 km** da un sito dichiarato si tace -- casa, o il piu' vicino fra gli altri -- perche'
una coordinata scritta con due decimali si sposta gia' di 1,1 km e sotto quella soglia la
differenza e' in come e' scritta, non in dove eri
(`test_a_frame_shot_at_another_declared_site_goes_there_without_asking`,
`test_between_two_declared_sites_the_nearest_wins`). Lontano da tutti, la notte **non nasce**: i suoi frame restano in attesa col codice `site_unclear`. Il motivo per cui
non si indovina e' che un GPS o una rete possono sbagliare, e una notte attribuita male e' un
dato falso che nessuno rilegge (scelta di Marco, 2026-09-09).

**La domanda si fa per COORDINATE, non per notte.** La sezione *Frame senza sito* di Da
confermare chiede *"questi frame da quale sito?"* proponendo i siti dichiarati **in ordine di
distanza da quelle coordinate**, il piu' vicino in cima. Un gruppo per posto e non per notte perche' la risposta e'
un fatto sul posto: vale per tutte le notti riprese li', **anche quelle che verranno** -- come la
regola imparata sui nomi degli oggetti. Sull'archivio di collaudo questo trasforma cinque notti
sparse in **due domande**: 391 frame a 16 km da casa e 41 a 64 km.

La risposta vive in `declarations` sulle coordinate arrotondate al chilometro, quindi sopravvive
a un azzeramento del rilevato, e porta il **nome** del sito e non il suo numero di riga: gli id
si riusano, e una risposta scritta su un id finirebbe addosso a un altro sito in silenzio. Se
quel sito sparisce o cambia nome, la risposta non aggancia piu' e l'app torna a chiedere -- che
e' la direzione sicura. La notte che ne nasce e' **`declared`** -- anche quando la risposta e'
"ero a casa", perche' cio' che conta e' che l'abbia detto l'utente -- e da li' in poi non la
sposta piu' nessuno: ne' il trasloco di casa, ne' la spazzata.

**Un gruppo a cui si e' gia' risposto resta in pagina**, con la risposta accanto: un clic
sbagliato attribuisce centinaia di frame, e rispondere di nuovo li sposta tutti. E' la stessa
lezione della seconda risposta sugli oggetti, che il primo giro di quella casella aveva
ignorato in silenzio. La proposta invece si **ricalcola alla lettura** e non si salva: uno stato salvato
invecchierebbe al primo sito nuovo. E le domande aperte **contano** in "da confermare", ma non
si chiudono con l'Applica: "ho visto la pagina" non e' una risposta a "da dove hai ripreso".

**L'ora del frame e' `DATE-OBS`, in UTC** (Marco, 23/9/2026): e' cio' che dice lo standard
(accordo IAU-FWG sulle date FITS, <https://fits.gsfc.nasa.gov/year2000.html>, 4.4: *"The
default interpretation shall use UTC"*), e l'app non la corregge con `DATE-LOC` ne' la chiede.

**Senza un sito dichiarato non nascono notti**, e l'app lo dice col codice `no_active_site`
(contratto del sito): a mani vuote non si inventa un fuso. Ogni altro motivo per cui un frame
resta fuori da una sessione ha il suo codice e si conta nella ricevuta: `site_no_timezone` (del
sito non si riconosce un fuso; in mare aperto vale quello nautico), `site_unclear`, `no_date` (un
software che non scrive `DATE-OBS` esiste; sull'archivio di collaudo non capita mai) e
`no_object`, per un frame che `identify` ha lasciato senza oggetto. Quest'ultimo arriva fin qui
**apposta**: se lo stadio non lo vedesse resterebbe `pending` per sempre, il residuo non
arriverebbe mai a zero e il pulsante Avvia partirebbe a vuoto a ogni clic.

**Si tocca solo cio' che e' in coda per questo stadio** -- a un frame rimesso in coda la
sessione vecchia si stacca all'inizio della corsa -- e rifarla non ri-chiave niente:
una notte il cui sito hai dichiarato tu non si sposta **mai** da sola, e cambiare il sito di
casa adotta le notti attribuite in automatico e nessun'altra. Unire due grafie di un pezzo in Da
confermare rimette in coda anche `group`, o le sessioni resterebbero appese al corredo sparito.

**Cosa `group` NON fa**: non salva ore ne' medie -- si contano leggendo, e un numero derivabile
non si congela in una colonna; non decide i mosaici (definiti, ma senza tabella: sono confinanti
coi Progetti); non tocca i FITS.

## Cosa NON fa

Non modifica, sposta, rinomina o cancella un FITS: togliere un frame dall'archivio dell'app,
quando si potra', sara' un'esclusione **dichiarata**, con conferma, che sopravvive alle
scansioni, e nomi e correzioni non si perdono. Non cataloga i file di calibrazione.
Non sorveglia le cartelle in continuo. Non riparte da solo all'apertura. Non vota i frame.
