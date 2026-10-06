# Il mosaico -- contratto

Un mosaico e' **un soggetto ripreso a pannelli affiancati**: piu' inquadrature diverse che, messe
insieme, sono una foto sola. L'app identifica i pannelli come oggetti **slegati** -- ognuno inquadra
una parte diversa del complesso -- ma la proposta li raccoglie e **ne somma le ore**: e' il secondo
tipo di immagine che un archivio contiene, accanto al soggetto ripreso in un'inquadratura sola.

La definizione, decisa con Marco e che non si riapre: **rettangoli risolti che si toccano o si
sovrappongono in parte, attorno allo stesso soggetto o regione, anche in notti diverse, con lo
stesso corredo**. Corredi diversi = due progetti. L'app lo propone, l'utente conferma una volta.
Le parole stanno in [`glossario.md`](glossario.md):
**mosaico** (`mosaic`) e **pannello** (`panel`), che non si dice *tessera* ne' *riquadro*.

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| I frame che ho ripreso a pannelli li vedo come **un** soggetto, e le sue ore sono la somma dei pannelli | `test_a_mosaic_sums_the_hours_of_its_panels`, `test_panels_identified_as_different_objects_are_one_mosaic` |
| L'app me lo **propone**, dicendo quali pannelli ha trovato, e non decide mai da sola | `test_the_app_proposes_a_mosaic_and_never_merges_by_itself`, `test_before_an_answer_no_frame_is_merged` |
| Rispondo **una volta sola** e vale per sempre, come per i filtri e gli oggetti | `test_confirming_a_mosaic_is_an_answer_that_lasts`, `test_the_answer_holds_when_the_mosaic_grows` |
| Se dico di no, l'app non me lo richiede | `test_a_refused_mosaic_is_not_asked_again`, `test_an_unanswered_mosaic_counts_among_the_things_to_confirm` |
| I pannelli ripresi in **notti diverse** stanno nello stesso mosaico | `test_panels_from_different_nights_are_the_same_mosaic` |
| Due riprese **dello stesso campo** non diventano un mosaico: sono la stessa foto rifatta | `test_one_framing_shot_many_times_is_not_a_mosaic` |
| Pochi frame spostati -- un giro al meridiano non ricentrato -- non fanno un pannello: un pannello conta solo con almeno il 25% del tempo del piu' lungo, e le pose se il tempo non si sa; i frame che non contano restano col loro oggetto | `test_two_stray_poses_beside_a_panel_are_not_a_mosaic`, `test_a_panel_shot_less_than_the_others_still_counts`, `test_the_share_is_measured_on_the_time_of_the_poses`, `test_without_the_time_the_share_is_measured_on_the_poses`, `test_without_the_time_few_poses_still_do_not_count`, `test_a_pose_that_leaves_for_another_rig_reweighs_the_mosaic`, `test_poses_that_turn_out_to_be_calibration_reweigh_the_mosaic`, `test_a_confirmed_mosaic_does_not_take_poses_that_do_not_count`, `test_the_centre_of_the_mosaic_does_not_lean_towards_a_panel_that_does_not_count`, `test_without_the_catalog_the_name_comes_from_the_panels_that_count`, `test_a_confirmed_mosaic_whose_other_panel_stops_counting_is_not_one_anymore` (`backend/tests/test_mosaic_weight.py`) |
| Un frame di cui non si sa quanto e' grande il campo non fa mosaici | `test_poses_without_the_size_of_their_field_make_no_mosaic` |
| Con un **altro corredo** e' un altro progetto, non un altro pannello | `test_another_rig_is_another_production` |
| Se di un frame non si sa come era orientato, l'app lo considera lo stesso invece di buttarlo via | `test_without_the_rotation_it_answers_on_the_circle_instead_of_giving_up` (`backend/tests/test_mosaic_geometry.py`), `test_panels_without_the_rotation_still_make_a_mosaic` |
| Posso sciogliere un mosaico che ho confermato, e i pannelli tornano soggetti a se' | `test_dissolving_a_confirmed_mosaic_frees_its_panels` |
| Quando dico di si' dico anche **di cosa** e' il mosaico, e il campo arriva gia' compilato con l'oggetto del catalogo al suo centro | `test_the_question_asks_what_the_mosaic_is_of_and_the_answer_names_it`, `test_the_proposal_is_the_catalog_object_at_the_centre` |
| Le pose che ho ripreso dentro il mosaico stanno nel mosaico; quelle dello stesso oggetto riprese da sole no | `test_an_object_inside_and_outside_a_mosaic_keeps_its_own_poses`, `test_the_answer_is_written_on_the_poses_of_the_mosaic_only` |
| Un pannello ripreso dopo entra nel mosaico da solo, anche se la corsa si ferma a meta' | `test_poses_that_arrive_later_join_the_mosaic_when_the_spine_groups_them`, `test_a_group_run_stopped_halfway_still_writes_the_mosaic` |
| Rinominare la camera, unirla a un'altra, o dire con che camera ho ripreso, non mi fa perdere la risposta | `test_renaming_the_camera_keeps_the_mosaic`, `test_merging_the_camera_into_another_keeps_the_mosaic`, `test_saying_the_camera_of_the_poses_keeps_the_mosaic` |
| Una volta scritto, il mosaico non si ricalcola: un frame nuovo si confronta solo coi pannelli del suo corredo nella sua fascia di cielo | `test_placing_again_does_not_redo_the_geometry`, `test_a_new_pose_is_compared_only_with_nearby_panels` |

## Le decisioni

**Si propone sulla geometria, non su una percentuale.** Due frame sono pannelli quando i loro
rettangoli si sovrappongono o si toccano **e nessuno contiene l'altro**. Il contenimento e' il
discriminante: due inquadrature diverse si sfiorano, mentre la stessa ripresa rifatta -- e il
dithering -- si contengono a vicenda. **Non esiste una sovrapposizione minima**, ed e' una scelta
con una fonte: nei quattro programmi supportati la sovrapposizione e' un parametro che **sceglie
l'utente** e nessuno ne documenta un valore predefinito -- N.I.N.A. (`Horizontal Panels`,
`Vertical Panels` e l'overlap, <https://nighttime-imaging.eu/docs/master/site/advanced/framingassistant/>),
ASIAIR (numero di pannelli e percentuale di sovrapposizione regolabili), SGP (la percentuale sta
nella procedura guidata, che ricorda l'ultima usata). I valori che circolano fra chi fotografa
vanno dal 10% al 30%: una soglia fissa non sarebbe una convenzione, sarebbe **un'ipotesi**, e
taglierebbe fuori chi riprende piu' stretto o senza margine (Marco, 12/9/2026). La conseguenza
e' voluta: due riprese lunghe dello stesso soggetto ricentrate fra due notti oltre la soglia della stessa
inquadratura (`SAME_POINTING_FRACTION`) arrivano come **proposta**, che si rifiuta una volta;
alzarla unirebbe in silenzio i pannelli di chi riprende con molta sovrapposizione.

**Il nome rafforza, non decide.** Un header che dice `Panel 2` e' un indizio forte -- N.I.N.A.
aggiunge quel suffisso al nome del target -- e `normalize` lo conserva apposta invece di pulirlo
(vedi [`spina.md`](spina.md)). Ma non basta da solo: *"Pane 1"* non e' un pannello, e un mosaico
ripreso senza rinominare i target non direbbe niente. La geometria e' il criterio, il nome e' il
rinforzo.

**Si raggruppa per corredo e regione, non per soggetto** (Marco, 12/9/2026). Ogni pannello
inquadra una parte diversa del complesso, quindi l'app li identifica come oggetti **diversi**: sui
quattro pannelli veri di IC 405 ne escono **quattro** (`ic-405`, `lbn-796`, `ldn-1516`,
`sh2-230`), rimisurati il 14/9/2026 sui 337 frame dell'archivio intero -- erano tre il 12/9 su
95 frame, e il numero cresce col catalogo: e' un esempio, non una soglia. Raggruppando per
soggetto il mosaico si spezza -- misurato il 12/9, 1 mosaico di 2 pannelli invece di 1 di 4. E' la meta'
che questo contratto diceva gia' e che l'implementazione aveva lasciato cadere: *"attorno allo
stesso soggetto **o regione**"*.

**Si scrive una volta, e non si ricalcola** (Marco, 23/9/2026: *"ok questi pannelli sono IC405,
scritto nel database... se e' scritto che cazzo deve ricalcolare"*). Quando un frame arriva a
`group` entra nel suo **pannello** -- l'inquadratura della posa che l'ha aperto -- o ne apre uno, e
un pannello nuovo entra nel **mosaico** dei pannelli che tocca (`spine/mosaic.py`). Tutto si
scrive e resta: un frame si confronta solo coi pannelli del suo corredo che potrebbero toccarlo,
mai con l'archivio, e un frame gia' piazzato non si confronta piu'. Un pannello che lega dei
mosaici entra nel piu' vecchio con una risposta -- o nel piu' vecchio, se nessuno ne ha -- e
quello si prende gli altri senza risposta: due mosaici con una risposta non si fondono mai.

**La chiave del mosaico non porta la camera.** E' l'impronta di uno dei suoi frame, scelta quando
nasce e poi ferma, e mai la chiave di un altro mosaico vivo: cosi' due corredi non si ritrovano
nello stesso (`test_a_mosaic_never_mixes_two_rigs`). Rinominare la camera, unirla a un'altra o
dire con che camera erano i frame non la toccano.
Un frame che cambia corredo resta nel suo pannello se il mosaico ha una risposta -- e il pannello
prende il corredo nuovo quando tutti i suoi frame ce l'hanno; se non ce l'ha,
si ripiazza fra i pannelli del corredo nuovo, e cosi' entra nel mosaico che quel corredo ha gia'
li' (`test_merging_two_spellings_of_a_camera_joins_the_confirmed_mosaic`,
`test_a_pose_told_its_camera_later_joins_the_confirmed_mosaic`). Un frame che perde il cielo esce
dal pannello e dal mosaico, e un pannello rimasto vuoto si toglie
(`test_a_pose_that_loses_its_sky_leaves_the_mosaic`,
`test_an_emptied_panel_does_not_link_its_neighbours`); un mosaico rimasto con un pannello solo
non e' piu' un mosaico, e le sue pose tornano ai loro oggetti
(`test_a_confirmed_mosaic_left_with_one_panel_is_not_a_mosaic`).

**L'app propone, l'utente conferma, e non si fonde niente.** I pannelli restano oggetti distinti:
il mosaico li **raccoglie**, non li fa diventare uno. E' la decisione portata da `old/`
(vedi [`ereditato.md`](ereditato.md)) e regge su un fatto: la differenza fra un mosaico e un
doppione e' **di intenzione, non geometrica**, quindi la geometria puo' proporre ma non concludere.
La risposta e' una dichiarazione dell'utente e non si sovrascrive mai, come ogni altra risposta di
Da confermare.

**Si chiede in Da confermare** (Marco, 12/9/2026), dove l'app gia' chiede tutto cio' su cui ha un
dubbio e dove si risponde una volta per tutto l'archivio. Non nasce un posto nuovo: nasce una
sezione, con lo stesso giro delle altre -- si propone, si risponde, la risposta resta se si cambia
idea. La sezione legge i mosaici scritti e non rifa' la geometria
(`test_the_page_reads_the_proposals_without_redoing_the_geometry`).

**Il si' dice di cosa e' il mosaico** (Marco, 22/9/2026). Una domanda sola: *si', e' un mosaico,
ed e' IC 405*. Il campo arriva compilato con la voce del catalogo in cui cade il centro del
mosaico (Marco, 23/9/2026) -- senza catalogo, col soggetto che ha piu' frame -- e si cambia
scrivendo; una sigla che il catalogo conosce va sulla sua voce, come per i frame senza nome. E' una
proposta: il nome lo conferma l'utente.

**La risposta e' una dichiarazione, e si scrive sui frame.** Il si' o il no sta fra le
dichiarazioni con la chiave del mosaico, cosi' sopravvive come le altre risposte. Ogni frame di un
mosaico confermato porta la chiave (`frames.mosaic_key`), che l'Archivio legge: la scrivono chi
risponde e `group` per i frame che arrivano dopo. Sta sul **frame** e non sull'oggetto, perche' lo
stesso oggetto puo' avere frame dentro un mosaico e altri fuori. **Nessun frame torna in coda**:
la chiave la scrive la risposta stessa, e nessun altro dato dipende da lei.

**Non si fonde niente, e l'Archivio li mostra come una cosa sola.** Le due decisioni stanno
insieme: nei dati i pannelli restano oggetti distinti -- chi cerca `LBN 796` lo trova -- ed e'
l'Archivio che raccoglie i frame con la stessa chiave in una riga, col nome detto dall'utente
(`archivio.md`). `identify` non si tocca. **Un mosaico confermato ha le stesse funzioni di un
oggetto**: dove l'app mostra un oggetto, il mosaico si mostra e si usa allo stesso modo.

**Un pannello conta solo se regge una parte del lavoro** (Marco, 27/9/2026): almeno il 25% del
tempo del pannello piu' lungo del suo mosaico, contando le pose se il tempo non si sa. La pratica
condivisa e' lo stesso tempo su ogni pannello, e al 25% il rumore del pannello e' il doppio; il
perche' e le fonti stanno in `backend/astrolog/spine/mosaic_weight.py`. Lo scrive chi piazza o
stacca le pose, sui mosaici che toccano (`mosaic.settle`, `panels.counts_in_mosaic`), e la proposta,
il suo centro e il suo nome, la chiave sulle pose e i conti guardano solo i pannelli che contano. La
sovrapposizione resta libera.

**Senza le misure del campo non c'e' pannello.** I lati del rettangolo si ricavano da quanti pixel
ha il sensore e dalla scala **misurata** dal solver: mancano solo se l'header non dice
`NAXIS1`/`NAXIS2`, e allora quel frame non entra nei mosaici. Puo' mancare la **rotazione**,
che arriva dal solver e cade quando la matrice e' degenere: li' si sa quanto e' grande il campo ma
non come e' orientato, e si usa il cerchio circoscritto, la stessa ricaduta che il codice usa gia'
per dire se un oggetto e' nell'inquadratura. Sbagliare per eccesso qui costa una proposta rifiutata
con un clic; escludere il frame costa un pannello perso in silenzio.

**Cosa il mosaico NON fa**: non unisce oggetti (quello e' il collasso di identita' di un doppione,
un'altra cosa); non tocca i FITS; non decide da solo; non cambia le sessioni, che restano *oggetto
x notte x corredo*.
