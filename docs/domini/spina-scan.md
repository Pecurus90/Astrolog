# La spina: `scan` -- contratto

Lo stadio `scan` legge le cartelle e gli header, e fa entrare i frame.
Cio' che vale per tutta la catena sta in [`spina.md`](spina.md).

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
| Se la cartella di rete cade a meta', l'app si ferma e lo dice: non segna "non trovato" mille file | `test_scan_root_gone_aborts`, `test_scan_root_gone_midway_aborts_without_marking_missing` |
| Una cartella di rete che non risponde non blocca l'elenco delle cartelle: la vedo come non raggiungibile | `test_a_share_that_does_not_answer_does_not_hold_the_list`, `test_a_share_still_being_asked_is_not_asked_again`, `test_many_dead_shares_do_not_make_a_live_folder_unreachable`, `test_a_folder_that_goes_away_reads_unreachable_on_the_next_list` |
| Una cartella senza permessi non blocca le altre: la vedo elencata nella ricevuta | `test_scan_unreadable_dirs` |
| Un file che sta solo online (OneDrive, Dropbox, iCloud) non viene scaricato: si salta, la ricevuta lo conta, e entra quando lo rendo disponibile sul disco | `test_scan_does_not_download_an_online_only_file`, `test_scan_a_pose_left_online_only_is_not_missing` |
| Una sottocartella nascosta resta fuori, ma la ricevuta la nomina | `test_scan_names_the_hidden_folders_it_leaves_out` |
| La cartella del NAS la registro come `\\NAS\Foto` o come disco collegato `Z:`, e la ritrovo con la lettera o il percorso di rete che ho scelto | `test_the_folder_is_saved_in_the_form_the_user_finds_again`, `test_a_network_folder_is_accepted` |
| Aprire le cartelle di rete non apre le zone di sistema, comunque siano scritte, e su qualunque sistema: anche su Mac, dove `/etc` e `/var` sono collegamenti | `test_the_checks_look_at_where_the_path_leads`, `test_a_system_zone_that_leads_elsewhere_is_refused_too`, `test_the_forms_that_would_bypass_the_checks_are_refused`, `test_a_path_that_resolves_to_no_absolute_path_is_refused`, `test_a_folder_that_does_not_answer_is_checked_and_kept_as_written` |
| Sul NAS in Docker scelgo la cartella da un elenco, invece di indovinarne il percorso (rotte e worker; il primo avvio e le Impostazioni le usano) | `test_the_nas_folder_is_chosen_from_a_list`, `test_the_folders_to_choose_from_are_the_ones_the_walk_walks`, *nell elenco del NAS si entra, e si registra la cartella dove sei* (`frontend/tests/wizard-cartelle.test.tsx`); le Impostazioni senza prova (Issue #13) |
| Una cartella raggiunta da un collegamento non fa girare la scansione a vuoto, e la ricevuta la nomina | `test_a_junction_is_not_followed_and_is_named`, `test_a_link_to_a_file_is_not_named_as_a_folder`, `test_the_linked_folders_are_named_in_order`, `test_scan_names_the_linked_folders_it_does_not_follow` |
| Un file che non si riesce a leggere, per qualunque motivo, non ferma la scansione: la ricevuta lo nomina col suo motivo, e resta scritta | `test_scan_bad_header_counted`, `test_a_file_that_breaks_the_reading_is_named_and_the_scan_goes_on`, `test_a_name_the_archive_cannot_write_is_named_and_the_scan_goes_on`, `test_a_pose_that_can_no_longer_be_read_is_not_missing`, `test_scan_stop_leaves_a_coherent_prefix` |
| Se il database non risponde (disco pieno, occupato) la scansione si ferma col suo motivo, invece di contare file sani come non letti | `test_a_database_fault_stops_the_scan_and_the_receipt_says_so` |
| Un guasto uguale su mille file non riempie il log: una traccia per tipo | `test_the_same_unexpected_fault_leaves_one_trace_in_the_log` |
| L'elenco dei file non letti lo leggo a pagine, e lo tiene l'ultima scansione di ogni cartella (e, se quella non e' arrivata in fondo, l'ultima che ci e' arrivata) | `test_the_files_not_read_are_listed_a_page_at_a_time`, `test_only_the_last_scans_of_a_folder_keep_the_names` |
| La ricevuta dice quanti file ha saltato e perche', calibrazioni comprese | `test_the_receipt_counts_the_skipped_by_reason` |
| Mentre scansiona vedo un pulsante che dice cosa fa (Scansiona / Interrompi / Riprendi) e la fase in corso coi suoi numeri veri, e a fine corsa una ricevuta, che resta in Impostazioni / Scansioni (la catena intera delle fasi non ha ancora una pagina) | `test_worker_events_stages_run_in_order_one_at_a_time`, `test_scan_receipt`, `test_scan_lock_stop_and_the_button_verb` |
| Fermare ferma entro il file in corso, e non fa partire altro; chiudere la finestra non ferma niente | `test_worker_stop_cooperative`, `test_scan_answers_at_once_and_the_receipt_arrives_in_status` |
| Una lettura fermata prima di cominciare, o che non riesce a partire, non lascia una ricevuta aperta per sempre, che sia di una cartella o di tutte; Riprendi la rilegge lo stesso | `test_resume_reads_one_folder_stopped_before_it_began`, `test_a_start_that_breaks_unexpectedly_leaves_nothing_behind`, `test_a_stop_does_not_leave_receipts_open_forever`, `test_a_busy_worker_leaves_no_folder_locked` |
| La ricevuta di una cartella tolta dice che la cartella e' ritirata, cosi' so perche' quel percorso non si aggiorna piu' | `test_duplicate_is_409_and_retire_reactivate_keep_data` |
| Se sposto le foto (un altro disco, un'altra lettera, il NAS) la cartella resta la stessa: le risposte *che file sono* la seguono, i frame non si muovono e una scansione dopo non ne crea di nuovi; l'app riconosce da sola la cartella spostata quando guardo nel posto nuovo, e non la sposta dove non ci sono gli stessi file | `test_a_moved_folder_takes_its_answer_and_its_frames_stay`, `test_the_root_and_every_subfolder_move_and_a_neighbour_does_not`, `test_moving_to_the_same_files_keeps_everything_and_a_scan_adds_nothing`, `test_a_place_with_other_files_is_refused_and_nothing_changes`, `test_moving_onto_a_registered_folder_is_409`, `test_the_probe_recognises_an_unreachable_folder_moved_here`, `test_the_probe_recognises_a_retired_folder_and_moving_it_brings_it_back`, `test_a_copy_of_a_reachable_folder_is_not_a_move`, `test_recognising_stops_reading_headers_at_the_deadline`, `test_a_folder_that_has_not_said_whether_it_answers_is_not_skipped_as_gone`, `test_a_silent_unrelated_folder_does_not_hide_a_move`, *la sonda la riconosce, e il tasto la sposta invece di registrarne una nuova* (`frontend/tests/wizard-cartelle.test.tsx`), *Cambia percorso sposta la cartella dove stanno ora i suoi file* (`frontend/tests/impostazioni.test.tsx`) |
| La notte di un frame va da mezzogiorno a mezzogiorno nel fuso del posto -- delle coordinate dell'header, o di casa -- e un frame senza data prende quella in cui il file e' stato scritto | `test_in_the_east_the_night_is_cut_at_local_noon`, `test_without_coordinates_the_home_site_gives_the_zone`, `test_without_coordinates_and_home_the_night_is_in_utc`, `test_a_pose_without_a_date_takes_the_date_of_its_file` (`backend/tests/test_local_night.py`) |
| Quando cambia il fuso di casa i frame che non dicono dove sono stati ripresi passano al fuso nuovo, partendo dall'istante con cui sono entrati -- toccare il file dopo non sposta la notte --, quelli che lo dicono no; le risposte sull'oggetto stanno sui frame e li seguono: su ogni parte di un gruppo che si divide; su due gruppi che diventano uno vale la risposta che c'era, e con due diverse la domanda torna aperta; le risposte sull'attrezzatura restano dove sono, perche' la firma non ha notte; i frame delle notti toccate si rifanno | `test_the_first_home_moves_the_nights_of_the_poses_that_do_not_say_where`, `test_a_pose_without_date_obs_takes_the_night_of_its_file_in_the_home_timezone`, `test_a_file_touched_after_it_entered_keeps_the_instant_of_its_night`, `test_moving_home_to_another_timezone_moves_them_again`, `test_choosing_another_home_moves_them_to_its_timezone`, `test_without_a_home_they_go_back_to_utc`, `test_an_object_answer_follows_its_poses_into_the_new_night`, `test_two_object_answers_that_disagree_fall_when_their_groups_become_one`, `test_the_answer_follows_its_poses_into_another_group` (`backend/tests/test_unnamed.py`), `test_a_camera_answer_stays_put_when_home_moves`, `test_the_poses_of_the_nights_that_changed_are_worked_again` (`backend/tests/test_home_nights.py`) |
| Un file elaborato che si dichiara frame non entra fra i miei frame e non fa ore, ma la ricevuta lo dice | `test_a_combined_file_is_not_a_frame` |
| Tutto cio' che legge un header regge sugli header di altri software, non solo sui miei | `test_header_corpus_reads_every_file` |

## Le decisioni

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
l'elenco non c'e' ancora (`scan_run_open`). La ricevuta porta i primi 100 percorsi e le 100
chiavi sconosciute piu' frequenti (ADR 0038).

**La radice si salva come l'utente la ritrova**, confinata sotto la radice dei dati quando e'
impostata (Docker): la forma risolta, salvo un disco di rete collegato a una lettera, che Python
dalla 3.8 risolverebbe nella sua condivisione (bpo-37993) -- chi ha scelto `Z:` ritrova `Z:`.
**Le cartelle di rete si accettano** (`\\server\cartella`; Marco, 2026-09-11). Aprirne una fa
autenticare Windows verso quel server con le credenziali dell'utente (n00py, *Understanding UNC
paths, SMB, and WebDAV*): il rischio resta confinato perche' il servizio ascolta sulla macchina e
chiede la chiave di avvio, e sul NAS in Docker quei percorsi non esistono. Non entrano le forme che
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

**Cosa entra**: `.fits` e `.fit`, tipo `light` o `unknown`; la pipeline nuova anche `.fts` e `.fz`
(`pipeline/walk.py`), XISF mai (ADR 0031, 0033). Dark, flat, bias, dark-flat e
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
vocabolario e' scritto una volta sola, senza separatori, in `fits/frame_type.py`: i programmi
verificati sono N.I.N.A. e ASIAIR (ADR 0029), e la grafia di un programma senza un suo file
vero non deve decidere se una calibrazione entra. Calibrazioni e stack si saltano, e la ricevuta
conta i saltati **per motivo**, calibrazioni comprese (`skipped_by_reason`: `calibration`,
`stack`, `still_writing`; Marco, 2026-09-11): un NAS con l'orologio avanti, che fa saltare gli
stessi frame a ogni scansione come "ancora in scrittura", si vede. **Vale anche per chi non conta i
frame sommati ma li elenca**: un `HISTORY` che nomina i file sorgente (`SOURCE1`, `SOURCE2`,
...) dice che quel file e' una combinazione, e cinque integrazioni dell'archivio di collaudo
si dichiaravano `LIGHT` proprio cosi'. `CALSTAT` e `CALIBRAT` **non** sono spie di stack:
dicono "calibrato", non "sommato", e a chi tiene i frame calibrati accanto agli originali
farebbero sparire l'archivio intero. Fanno un altro mestiere -- il **marchio di riscrittura**,
in [`spina-normalize.md`](spina-normalize.md) -- che non fa sparire niente. Un file senza `IMAGETYP` e'
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
quella cartella, se l'archivio non li ha gia', non entrano nemmeno. I programmi di
ripresa verificati sono N.I.N.A. e ASIAIR (ADR 0029); il corpus (`backend/tests/header/`) ha i
loro header; un altro programma entra solo con un suo file vero e una decisione di Marco (Issue
#23). Dell'ASIAIR ce ne sono **tre, di tre utenti diversi**, e non e' abbondanza: in `TELESCOP`
quel programma scrive la **montatura**, e il nome cambia da utente a utente (`EQMod Mount`
contro `ZWO AM3`), quindi un header solo farebbe sembrare una lista di nomi la risposta
giusta. Un header di un programma non verificato non entra nel corpus.

**La notte della posa si scrive quando la posa entra** (`scan`, `frames.local_night` e
`local_tz`, con l'istante da cui viene in `night_instant`): da mezzogiorno a mezzogiorno nel fuso
delle coordinate dell'header, o del sito di casa, o in UTC se non si sa nessuno dei due; senza `DATE-OBS` e' la notte in cui il file e' stato scritto
(Marco, 27/9/2026). La leggono le domande per notte, il solver e la domanda sui luoghi, che vengono
prima di `group` o non sanno il sito. **Quando cambia il fuso di casa** -- nasce, se ne sceglie
un'altra, si sposta, si toglie -- i frame che non hanno un fuso dalle coordinate dell'header si riscrivono nel fuso
nuovo, e il gruppo dei frame senza nome, che porta la notte, si risceglie (`spine/home_nights.py`).
Nessuna risposta porta la notte nella chiave (ADR 0014, S2): l'oggetto dei frame senza nome sta
sull'impronta di ogni frame, l'attrezzatura sulla firma, e nessuno le deve spostare. La risposta
di un gruppo e' quella che i suoi frame portano: un gruppo che si divide la porta su ogni parte; su
due gruppi che diventano uno vale quella che c'era -- una sola, o la stessa su tutti e due --,
anche per i frame che non l'avevano, e con due risposte diverse la domanda torna aperta. Si perde
un caso: un frame arrivato dopo la risposta, che il fuso nuovo porta in un gruppo senza frame
risposti, torna una domanda.
