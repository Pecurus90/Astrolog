# La spina: `normalize` -- contratto

Lo stadio `normalize` traduce i grezzi dell'header in pezzi, filtri e setup, e riconosce le copie.
Cio' che vale per tutta la catena sta in [`spina.md`](spina.md).

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| I nomi dei filtri, degli strumenti e degli oggetti scritti in mille modi diventano i miei filtri, i miei strumenti, i miei oggetti; quando l'app non sa, me lo chiede una volta per gruppo e poi si ricorda | `test_normalize_vocab_corpus`, `test_normalize_alias_learned` |
| Un filtro che l'app non riconosce (`H`, `Filter 3`) me lo chiede una volta -- e' uno dei miei, un modello in commercio (solo pipeline vecchia, ADR 0031), o nome e banda -- e la risposta vale per sempre; uno che riconosce non me lo chiede | `test_only_the_filters_the_app_does_not_know_are_asked`, `test_review_merges_two_filters`, `test_review_declares_a_filter_with_its_bands` |
| Lo stesso pezzo scritto in due modi (`ATR2600M` e `ATR2600M(USB2.0)`) e' un pezzo solo: me lo chiede una volta e non ci torna piu' | `test_normalize_alias_learned` |
| Un pezzo scritto in due modi lo unisco una volta, e da li' in poi l'app riconosce da sola la grafia vecchia | `test_merging_two_spellings_moves_the_poses_and_learns_the_rule` |
| Cambio idea quante volte voglio: rinomino un pezzo gia' rinominato o gia' unito, e tutte le grafie di prima continuano a portare a lui -- anche per un filtro | `test_a_second_rename_carries_the_spelling_learned_by_the_first`, `test_renaming_a_piece_carries_the_spellings_it_absorbed`, `test_renaming_a_filter_carries_the_spelling_it_absorbed` |
| Dichiaro un filtro che possiedo con la sua marca, il suo modello e le larghezze di banda, e i frame che lo usano lo prendono | `test_review_declares_a_filter_with_its_bands` |
| Due grafie che hanno l'aria di essere la stessa camera me le chiede -- "sono lo stesso strumento?" --; si' le unisce, no non me lo chiede piu' per quella coppia, e guardare non e' rispondere | `test_a_yes_merges_the_two_spellings`, `test_a_no_silences_the_pair_for_good_whichever_way_it_leans`, `test_seeing_the_page_does_not_answer_the_question` |
| L'attrezzatura che i file non dicono -- la camera, l'ottica, il filtro -- me la chiede in **una scheda per firma dell'header** (grafia di camera e telescopio, focale entro il 5 %, sensore), non per notte ne' per cartella, e solo le parti che mancano; un `TELESCOP` che il programma dice montatura (l'ASIAIR) non entra nella firma (ADR 0014, S1) | `test_a_question_per_group_with_the_largest_first`, `test_the_signature_is_the_header_not_the_night_or_the_folder`, `test_each_value_of_the_key_makes_its_own_group_and_the_row_says_it`, `test_the_key_is_made_in_one_place_from_what_the_header_says`, `test_renaming_the_optics_does_not_move_the_key`, `test_only_the_poses_whose_header_does_not_say_the_camera_are_asked`, `test_a_part_the_files_say_is_not_asked`, `test_the_focal_is_shown_only_when_the_poses_agree`, `test_two_mount_names_of_one_asiair_are_one_card`, `test_poses_that_do_not_name_the_optics_are_asked_once_per_camera_and_focal`, `test_the_answer_is_for_that_camera_only` |
| Rispondo alla camera scegliendo un setup che l'app conosce o scrivendo camera e focale (e l'ottica se serve), all'ottica scegliendone una mia o scrivendone il nome: i pezzi scritti a mano diventano miei, i frame vanno nel setup che quei pezzi hanno gia', e la risposta vale anche per i frame che arriveranno con la stessa firma, **in qualunque notte** | `test_answering_with_the_pieces_makes_the_rig_and_moves_the_poses`, `test_choosing_a_rig_from_the_list_writes_its_names`, `test_the_camera_written_by_hand_becomes_a_piece_and_the_filter_question_follows`, `test_the_answer_holds_for_the_poses_that_arrive_later_in_that_group`, `test_the_answer_gives_the_optics_and_the_poses_join_the_rig_that_has_it`, `test_an_optics_written_by_name_is_born_like_from_a_header`, `test_a_pose_that_arrives_later_takes_the_answer_by_itself`, `test_the_pose_reads_the_answer_of_its_own_group`, `test_a_focal_that_drifts_finds_the_same_answer`, `test_the_answer_is_read_back_with_its_pieces`, `test_the_key_is_never_split_to_find_the_pieces` |
| Una scheda conta fra le cose da confermare finche' ogni parte che chiede non ha la sua risposta; risposta, resta in pagina; una parte che non mando tiene la risposta di prima; una risposta illeggibile vale nessuna risposta | `test_an_unanswered_group_counts_among_the_things_to_confirm`, `test_the_camera_written_by_hand_becomes_a_piece_and_the_filter_question_follows`, `test_an_answer_that_cannot_be_read_is_no_answer`, `test_a_focal_that_is_not_a_focal_leaves_the_answer_standing`, `test_an_optics_that_is_not_a_name_is_no_optics`, `test_a_filter_word_that_is_not_an_answer_is_no_filter_answer` |
| Se ho ripreso senza filtro (camera a colori) l'app non inventa un filtro, e se non riesce a saperlo me lo chiede nella scheda della firma | `test_normalize_bayer_decides_when_filter_is_none`, `test_a_question_per_camera_with_the_largest_first` |
| Al filtro rispondo a colori, nessun filtro, o uno dei miei filtri scelto da una tendina, e la risposta vale anche per i frame che verranno; "a colori" si scrive sulla scheda della camera, anche quando la camera viene dalla notte, e il colore scritto li' e' la stessa risposta | `test_answering_colour_makes_those_poses_osc_and_the_next_ones_too`, `test_the_camera_of_the_night_takes_the_answer_about_the_sensor`, `test_answering_mono_with_no_filter_puts_them_on_no_filter`, `test_answering_one_of_my_filters_puts_them_on_it`, `test_writing_colour_on_the_card_answers_too`, `test_colour_without_a_camera_is_refused`, `test_one_of_my_filters_does_not_beat_colour`, `test_a_filter_named_like_an_answer_stays_a_filter`, `test_one_of_my_filters_is_one_of_the_choices`, `test_after_the_answer_the_filter_question_reaches_those_poses` |
| La mia camera a colori non me lo chiede: se i file la dicono a colori i suoi frame senza filtro sono OSC, anche quelli di un programma che la matrice non la scrive; il frame che il filtro lo scrive resta col suo filtro | `test_a_camera_its_files_say_colour_is_not_asked_and_its_poses_are_osc`, `test_answering_no_filter_on_a_colour_camera_does_not_call_it_mono`, `test_normalize_reads_the_colour_of_the_camera_not_of_the_single_pose` |
| La mia risposta dice cosa avevo davanti e la scheda della camera dice che sensore e': cambiare il sensore non me la cancella, e tornando a mono la ritrovo | `test_the_answer_about_the_filter_survives_a_change_of_sensor`, `test_the_card_says_the_sensor_and_the_answer_stays_and_the_pixel_does_nothing` |
| Accanto a ogni gruppo su cui l'app chiede -- firma dell'attrezzatura, gruppo di frame, sito -- vedo cosa ho ripreso, anche se il file non scrive l'oggetto, e so quali frame il cielo non ha riconosciuto e quali non ha ancora guardato o non e' riuscito a guardare | `test_the_camera_question_sums_the_subjects_of_all_its_nights`, `test_a_group_says_what_the_sky_found_in_it`, `test_a_place_says_what_the_sky_found_there` |
| L'unica domanda che **non** lo mostra e' *che file sono* (per cartella): su quei frame il cielo non ha saputo dire -- un elenco vuoto sembrerebbe una risposta invece che un'attesa | `test_a_question_per_folder_about_which_files_they_are` |
| Se rinomino o unisco il filtro, la camera o l'ottica che ho risposto, la risposta li segue, e il nome vecchio non fa rinascere il pezzo; rinominare o unire una camera dei file non sposta la risposta, che sta sulla grafia del file | `test_the_answer_follows_its_filter_when_it_is_renamed_or_merged`, `test_renaming_a_piece_carries_the_answers_that_name_it`, `test_renaming_the_optics_carries_the_answer`, `test_renaming_the_camera_carries_the_answer`, `test_merging_the_optics_into_another_carries_the_answer`, `test_renaming_a_camera_carries_the_answer_on_the_group`, `test_merging_the_optics_carries_the_answer_on_the_group`, `test_renaming_a_camera_carries_its_answer`, `test_merging_two_cameras_leaves_each_signature_its_answer`, `test_merging_into_a_colour_camera_keeps_the_answer_that_arrives`, `test_merging_into_a_colour_camera_carries_the_answer_even_there`, `test_the_unfiltered_answer_follows_the_camera_when_renamed` |
| La mia risposta su una firma non decide per le altre, nemmeno se rinomino o unisco "nessun filtro" | `test_renaming_no_filter_does_not_answer_for_the_other_cameras`, `test_no_filter_is_not_merged_into_another_filter` |
| Una risposta su una firma che non c'e' piu', su una parte che la scheda non chiede, con un setup senza camera, o una riga "nessun filtro" che non si puo' creare, si dice invece di scrivere una risposta che non sposta niente | `test_a_group_that_is_not_there_is_refused`, `test_an_answer_to_a_question_that_is_not_there_is_refused`, `test_an_answer_about_a_camera_that_is_not_there_is_refused`, `test_the_answer_of_a_group_that_is_not_there_is_not_found`, `test_a_part_the_card_does_not_ask_is_refused`, `test_an_answer_that_says_two_things_or_none_is_refused`, `test_a_rig_without_a_camera_does_not_answer_this_question`, `test_a_no_filter_name_already_taken_is_said_not_crashed`, `test_a_filter_that_is_not_there_is_refused`, `test_a_filter_goes_with_one_of_my_filters_and_only_there` |
| Un frame che non dice la camera prende quella degli altri frame della stessa notte, se e' una sola, anche se il frame che la dice arriva dopo, e la scheda non chiede la camera; se nella notte nessuno la dice o ne dicono piu' d'una me la chiede; due grafie che ho unito sono una camera; e la mia risposta vince sulla notte | `test_a_pose_without_camera_takes_the_one_of_its_night`, `test_in_one_scan_the_order_of_the_files_does_not_matter`, `test_two_cameras_in_the_night_leave_the_question`, `test_two_spellings_of_one_camera_are_one_camera_of_the_night`, `test_my_answer_on_the_group_wins_over_the_night`, `test_the_cards_ask_the_rig_only_of_the_nights_of_their_poses` |
| Se il frame non dice l'ottica, prende quella della notte quando la notte ne dice una sola a una focale sola, con la focale se il frame non la dice (una focale zero non e' una focale), invece di far nascere un gemello senza ottica; una focale sua diversa non prende l'ottica della notte | `test_a_silent_pose_takes_the_rig_of_its_night`, `test_a_pose_with_its_own_focal_does_not_take_the_optics_of_another`, `test_a_night_with_two_optics_gives_only_the_camera`, `test_one_optics_at_two_focals_gives_only_the_camera`, `test_a_night_of_asiair_and_other_poses_gives_only_the_camera`, `test_an_asiair_night_gives_the_rig_without_optics_of_its_poses` (`backend/tests/test_night_rig.py`) |
| La focale me la chiede con la camera, proponendo quella della mia ottica, cosi' non mi ritrovo due setup gemelli con le ore spartite | `test_the_declared_focal_does_not_leave_two_twin_rigs`, `test_the_focal_of_the_optics_card_is_what_the_page_proposes`, `test_the_focal_of_the_optics_card_is_proposed_when_the_poses_do_not_say_it` |
| Il nome e la montatura che avevo dato al setup senza ottica passano al setup che nasce dalla mia risposta, anche se cambio idea, e i frame tengono la montatura; un setup che c'era gia' tiene la sua parola; nessuna scheda mi propone la montatura come ottica | `test_the_name_and_mount_of_the_rig_without_optics_go_with_its_poses`, `test_a_rig_that_was_already_there_keeps_its_own_word`, `test_the_camera_question_does_not_offer_the_mount_as_optics`, `test_a_mixed_group_does_not_offer_the_mount_as_optics_either`, `test_the_optics_shown_is_the_name_the_user_gave_it` |
| Cambio idea rispondendo di nuovo: i frame lasciano il setup di prima, e quelli che l'ottica la dicono restano col loro | `test_answering_again_moves_the_poses_to_the_new_rig`, `test_changing_the_answer_moves_the_poses` |
| Un frame in due cartelle o una copia riscritta e' una posa sola; una cartella ritirata o un file sparito non chiedono niente; un setup con le sole copie resta fra le scelte | `test_a_pose_that_lives_in_two_folders_counts_once`, `test_a_rewritten_copy_is_not_another_pose_but_comes_back_in_the_queue`, `test_a_retired_folder_and_a_file_that_is_gone_do_not_ask_anything`, `test_a_rig_whose_only_poses_are_copies_stays_in_the_page` |
| La copia calibrata di un frame non raddoppia il conteggio delle ore | `test_normalize_calibrated_copy` |
| Anche se riprendo con un programma che l'app non conosce, purche' la copia dica di essere stata calibrata | `test_normalize_finds_the_copy_of_an_unsupported_capture_program` |
| E se chi elabora lascia nell'header il nome del mio programma accanto al suo, o me lo riscrive col suo | `test_normalize_calibrated_copy`, `test_normalize_the_copy_that_overwrites_the_capture_software` |
| Ma se ho tenuto **solo** il file calibrato, quelle ore restano mie | `test_normalize_a_marked_frame_without_a_twin_still_counts` |
| E se due file dicono di essere lo stesso scatto e niente dice quale sia l'originale, l'app non indovina: li conta tutti e due | `test_normalize_does_not_guess_between_two_twins_that_say_nothing`, `test_normalize_does_not_mark_a_capture_program_that_writes_only_its_own_key` |
| La scheda della mia camera ha il pixel fisico su cui concordano i file, qualunque sia l'ordine in cui arrivano e anche se riprendo binnato | `test_the_pixel_follows_the_files_not_the_first_one`, `test_files_at_bin_two_give_the_physical_pixel` |
| Il pixel e il colore che scrivo sulla scheda restano miei: nessun ricalcolo li tocca | `test_what_i_write_on_the_card_is_never_recomputed`, `test_the_card_shows_what_i_wrote_over_what_the_files_say` |

## Le decisioni

**`normalize` traduce, non interpreta.** Applica i vocabolari ai grezzi dell'header e scrive
`frames.software`, `filter_id`, `rig_id` e i tre pezzi che la posa nomina addosso a se'
(`filter_wheel_id`, `focuser_id`, `guide_camera_id`). Le sigle degli oggetti sono mestiere di
`identify` col catalogo: qui il nome si pulisce soltanto (spazi, parole di tavolozza), e un
suffisso di mosaico (*Pannello 2*) resta nel nome, perche' toglierlo e' interpretare.
Non dipende da nessuno stadio: gira anche prima del solver.

**I vocabolari dicono solo cio' che scrivono i programmi verificati** (ADR 0029). I filtri:
lista standard, abbinamento esatto, cio' che non combacia si chiede (ADR 0031, 0033); nella
pipeline vecchia restano le bande di `vocab/filters.json` (16 piu' `UNKNOWN`). Il software
riconosciuto e' solo quello verificato, e la copia calibrata
si riconosce dal marchio che il file porta, non dal nome del programma. Le chiavi dell'header sono
lo standard FITS piu' cio' che i verificati scrivono, salvo le due che dicono che il file e' stato
riscritto (`CALSTAT`, `CALIBRAT`), da una convenzione pubblica. Le misure scritte nell'header
(FWHM, SNR, stelle) non si leggono: si misurano (`test_the_measurements_a_header_writes_are_not_read`).

**Prima l'alias, poi il vocabolario, poi la domanda.** Per ogni grezzo l'ordine e':
`header_aliases` (cio' che l'utente ha gia' risposto) -> il vocabolario -> altrimenti il
valore resta grezzo e il **gruppo** entra in Da confermare. Una risposta e' sempre una regola
riusabile, mai una correzione su un frame: si chiede per gruppo, mai per file. L'automatico
non sovrascrive mai il dichiarato, e la risposta chiama `invalidate` sugli stadi a valle.
Un'eccezione sola, dove non c'e' niente da sovrascrivere: su una camera a colori una parola che il
**vocabolario stesso** conosce come banda larga (`L`, `Lum`, `B`) resta OSC anche se una rinomina o
un filtro scritto a mano ne hanno fatto una regola -- quella regola parla dei frame mono, e sulla
matrice il filtro e' la matrice (`test_a_colour_frame_that_writes_the_app_name_stays_osc_after_a_rename`).
Una risposta su una parola che il vocabolario non conosce resta la tua
(`test_an_answer_on_a_word_the_vocabulary_does_not_know_stays_on_a_colour_camera`).

**Da confermare chiede solo i filtri che l'app non riconosce** (Marco, 25/9/2026: *"scritto e
riconosciuto si associa; scritto e sconosciuto, una domanda: che filtro e' H? per sempre"*). Uno
che il vocabolario riconosce non e' una domanda: non si elenca, non si conta, non si conferma. Le
lettere sole della ruota (`L`, `R`, `G`, `B`, e `H`, `O`, `S` per decisione di Marco, ADR 0031:
lo fanno N.I.N.A. e ASIAIR) sono nella lista, la stessa della pipeline (un test le tiene uguali);
una lettera fuori dalla lista (`N`) normalize non la indovina, ed e' una domanda. Si risponde in tre modi: **e' uno dei miei**, scelto fra i filtri con la banda nota
(e' l'unione: la grafia dell'header diventa per sempre quel filtro); un **modello in commercio**
dalla tendina (solo pipeline vecchia: muore col porting, ADR 0031); o **nome e banda** scritti -- per un duo o
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

**Strumenti e setup si rilevano, e si confermano una volta.** Ottica e camera vengono da
`TELESCOP` e `INSTRUME` risolti **via alias**, mai per stringa: cosi' due grafie dello stesso
pezzo restano un pezzo solo. Dalla stessa porta, e con gli stessi alias, nascono i tre pezzi che
il programma scrive **sulla singola posa** -- la ruota portafiltri (`FWHEEL`), il focheggiatore
(`FOCNAME`) e la camera di guida (`GUIDECAM`) -- che pero' **non entrano nell'impronta del
setup**: cambiare ruota non fa un secondo setup, e le loro ore le sa la posa, non il
setup (`domini/attrezzatura.md`). **L'app non tiene una lista di nomi di montatura** -- invecchia, e
il nome cambia da utente a utente (`EQMod Mount` e `ZWO AM3` sono tutti e due veri) -- ma sa
**quale programma ha scritto il file**, e con l'ASIAIR `TELESCOP` e' la montatura, sempre: il
pezzo nasce `mount` e il setup di quei frame resta **senza ottica**, che l'ASIAIR non scrive
da nessuna parte (misurato su 171 header di quattro utenti, 14/9/2026). Un setup a cui manca
un pezzo e' vero; uno con la montatura al posto dell'ottica e' falso. **Quale fosse l'ottica lo
chiede Da confermare**, nella scheda della firma: la risposta da' l'ottica a ogni frame di quella
firma che non la nomina, anche ai prossimi (Issue #23). Setup = (ottica, camera) a una focale:
focali entro il **+-5 %** raggruppate per camera su tutto l'archivio, un setup per gruppo, e un
frame fuori posto torna nel giro (ogni ordine, stessi setup); il binning no, un riduttore si'. **La
focale e' quella misurata dal cielo** dove c'e' (ADR 0016): dopo una soluzione, pixel (`XPIXSZ`, o
quello della scheda per il binning, mai quello ricavato dal cielo) diviso la scala, al millimetro,
in `frame_wcs.focal_mm`; senza, `FOCALLEN`. Il setup nasce dall'header prima del cielo, e il
solver rimanda a `normalize` il frame la cui misura non e' la focale del setup, rifatto nello
stesso giro prima del `done` di `solve` (`run.queue`)
(`test_a_reducer_the_header_does_not_say_moves_the_frames_to_the_true_focal`,
`test_the_frames_the_sky_sends_back_are_redone_in_the_same_run`,
`test_a_measure_within_the_tolerance_keeps_the_rig_and_redoes_nothing`,
`test_without_a_pixel_the_header_focal_stays`, `test_a_frame_without_a_header_focal_takes_the_measured_one`).
Firme dell'header e notte restano sulla focale dell'header: chiedono cio' che i file dicono. Le
specifiche non si cercano su internet: le compila l'utente. Il legame frame -> setup si
congela dopo il cielo: la verita' storica sta nell'header e nella focale misurata. La chiave con cui un setup e' stato rilevato
resta separata da cio' che l'utente cambia: rinominarlo o arricchirlo non crea un doppione.
Uno strumento che l'app non conosce nasce provvisorio e **si segnala, mai si scarta**; nomi
di ripiego non entrano nel DB (niente "Setup sconosciuto": l'assenza si dice a schermo).

**L'attrezzatura che i file non dicono** (Marco, 12/9/2026; ADR 0014, S1). Camera, ottica e
filtro si chiedono in **una scheda per firma dell'header**: grafia di `INSTRUME` e di `TELESCOP`,
focale con la regola dei setup (+-5 %), dimensioni del sensore e pixel -- mai la notte o la
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
camera si risponde scegliendo un setup fra quelli che l'app conosce **oppure** scrivendo camera e
focale, e l'ottica se serve: i pezzi nascono da quei nomi come da un header -- chi non ha mai
nominato la sua camera in nessun file avrebbe un elenco vuoto da cui scegliere -- e l'ottica
dichiarata **vince** su `TELESCOP`. La **focale** si chiede con la camera, proponendo quella nativa
dell'ottica: un setup a focale ignota non e' lo stesso setup di uno a focale nota, quindi senza
chiederla resterebbero due gemelli per sempre con le ore spartite. La risposta vale **anche per i
frame che arriveranno con la stessa firma**, da qualunque cartella e in qualunque notte: si
accetta di perdere il caso raro della stessa firma con attrezzature diverse in notti diverse, e
cambiare il fuso di casa non la sposta. I setup fra cui si sceglie li dice l'API, e la stessa
funzione rifiuta gli altri (`review_page.rig_choices`): uno **senza camera** non risponde --
sceglierlo lascerebbe i frame dov'erano -- e uno rimasto a zero frame e' un residuo. Il nome e la
montatura dati al setup senza ottica passano al setup che nasce dalla risposta.
**Prima della domanda, la notte** (Marco, 23/9/2026: *"camera mancante: quella degli altri frame
della stessa notte, se e' una sola"*). Se gli header della stessa notte -- la notte della posa, da
mezzogiorno a mezzogiorno nel fuso del posto -- dicono una camera sola, contate le grafie
unite come una, il frame ha quella e la scheda non gli chiede la camera. Vale anche quando il frame che la
dice arriva dopo: chi normalizza un frame che dice la camera rilavora i frame senza camera della sua
notte, e una seconda camera nella notte glieli toglie. Se nessun header della notte dice la camera, o
ne dicono piu' d'una, la camera si chiede; e un frame senza data prende la notte in cui il file e'
stato scritto. La risposta invece e' scritta, e **vince** sulla notte: una scheda risposta resta in
pagina. La notte da' anche l'ottica e la focale, se ne dice una sola (`spine/night_rig.py`).

**La copia calibrata non raddoppia le ore.** Stessa data, stessa camera e stessa esposizione
di un frame gia' in archivio: e' lo stesso scatto, non un'altra ora di cielo. Fra due gemelli
vince il piu' **originale**, e un frame e' una copia solo se un gemello e' piu' originale di
lui: prima il **marchio di riscrittura** (`CALSTAT`/`CALIBRAT`, lo stato di calibrazione; o
**due programmi diversi nominati insieme**, uno in una chiave di chi ha **scritto** il file --
`PROGRAM`, `SWMODIFY`), poi il software di ripresa riconosciuto. **I due marchi non pesano
uguale**: le calibrazioni applicate dicono che sono cambiati i **pixel**, due programmi nominati
insieme dicono solo che qualcuno ha toccato l'**header** -- e l'header di un grezzo lo riscrive
anche chi non lo calibra (un solutore, un correttore di metadati). Fra un grezzo cosi' e la sua
copia calibrata vince il grezzo. Che due grafie siano due
programmi lo dice **il vocabolario dei programmi**, mai la somiglianza fra le stringhe: `SGPro 4.4`
e `Sequence Generator Pro v4.4` sono lo stesso programma. Ed e' la ragione per cui la regola sta
nella spina (`spine/rewrite.py`) e non nel lettore dell'header, che il vocabolario non puo'
consultarlo. Un nome
solo non e' un marchio: e' la grafia con cui due programmi si presentano, e prenderla per un
marchio marchierebbe i loro grezzi. A pari indizi si contano tutte e due:
indovinare fonderebbe due frame veri ripresi nello stesso istante, e far sparire cielo vero e'
peggio che contarlo due volte. Il marchio guarda le **chiavi**, mai il nome che ci sta dentro
(i programmi verificati restano due, ADR 0029), e da solo non toglie niente a nessuno: senza un
gemello, un file calibrato e' semplicemente il frame -- c'e' chi tiene solo quello. Il grezzo
vince, la copia porta `frames.copy_of` e resta in archivio con le sue posizioni; chi conta le
ore filtra `copy_of IS NULL`.
Perche' due criteri e non uno: chi elabora **non cancella** sempre la chiave di chi ha
acquisito, e chi riprende con un programma non verificato non e' riconosciuto nemmeno sul
grezzo -- in tutti e due i casi il software da solo non distingue i gemelli. **Il caso che resta
scoperto** (Issue #23): la copia che non dice di essere calibrata e nel cui header il
vocabolario non riconosce **nessuno** dei nomi -- cioe' chi riprende con un programma non
verificato ed elabora con un altro che l'app non conosce. Li' i due gemelli si somigliano davvero,
e l'app li conta tutti e due.

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

**Le schede**: oggi i campi di `instrument_answer.CARD` (un filtro ha la larghezza **per banda**,
facoltativa); la scheda tecnica completa e i conti sono di ADR 0021 (Marco, 18/10/2026), al
porting (`attrezzatura.md`). I conti si derivano e non si chiedono mai. Pixel, focale e "camera a
colori" arrivano dall'header quando c'e'. Per la camera
**decidono i file, non il primo che capita**: il pixel fisico e la matrice di Bayer piu'
frequenti fra i frame che la usano, ricalcolati a ogni giro di `normalize`, e a pari file
nessuno (scelta di Marco, 2026-09-11). Cio' che l'utente scrive su quei due campi sta fra le
dichiarazioni, non nella colonna rilevata: nessun ricalcolo lo tocca, rinominare la camera se
lo porta dietro, e nell'unione di due camere vince la scheda di quella tenuta.
