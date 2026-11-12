# La spina: `identify` -- contratto

Lo stadio `identify` dice quale oggetto c'e' in ogni frame, e tiene le risposte sugli oggetti.
Cio' che vale per tutta la catena sta in [`spina.md`](spina.md).

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
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
| L'oggetto me lo chiede in **una scheda per gruppo di frame** (ADR 0014, S3): i frame che l'app ha messo su un oggetto, o un gruppo di frame senza nome e senza cielo; la stessa scheda per tutti e due, coi candidati del cielo da cliccare -- anche zero -- e la stessa risposta | `test_found_objects_and_unnamed_groups_are_one_list_of_cards`, `test_an_answer_that_says_two_things_or_none_is_refused`, `test_a_card_that_is_not_there_is_refused` |
| Anche a un oggetto trovato rispondo "non e' un oggetto": i suoi frame escono dalle ore e da ogni oggetto, la scheda resta in pagina coi candidati e non conta piu', e cambio idea; vale per i frame che c'erano quando ho risposto | `test_not_an_object_on_a_found_object_takes_its_frames_out_and_the_card_stays`, `test_the_card_of_frames_put_out_keeps_the_sky_candidates` |
| "Non e' un oggetto" detto per un gruppo di frame senza nome non tocca un frame del gruppo che il cielo ha riconosciuto | `test_not_an_object_said_for_a_group_does_not_reach_a_frame_the_sky_recognised`, `test_a_sky_that_comes_after_the_group_answer_still_decides` |
| Vedo cosa l'app ha capito di ogni oggetto, e cio' su cui ha un dubbio sta in cima | `test_the_objects_section_shows_the_archive_objects_not_the_header_spellings`, `test_the_ones_to_decide_come_first` |
| Gli oggetti che l'app sa, su cui non c'e' niente da scegliere, non riempiono la pagina: stanno chiusi, si aprono a pagine, e da li' si correggono | `test_the_settled_objects_leave_the_page_and_come_in_pages` |
| Quando mi chiede quale oggetto era, mi mostra cosa c'e' a quelle coordinate e mi basta cliccare | `test_a_doubtful_object_carries_the_candidates_the_sky_found` |
| Se rispondo che quei frame sono un altro oggetto, ci vanno davvero -- e non tornano indietro | `test_answering_on_an_object_moves_its_frames_and_locks_it`, `test_a_correction_survives_a_second_run` |
| Se scrivo a mano una sigla che il catalogo conosce (`M 81`, `m81`), e' quella voce, non un oggetto fuori catalogo con lo stesso nome: le mie ore non si dividono su due voci | `test_a_designation_written_by_hand_is_the_catalog_entry` |
| E dopo che ho risposto l'app non me lo richiede piu', neanche sull'oggetto su cui era in dubbio | `test_a_correction_closes_the_question_on_a_doubtful_object` |
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

## Le decisioni

**Gli oggetti si dichiarano in Da confermare, una scheda per gruppo di frame** (ADR 0014, S3):
i frame che `identify` ha messo su un oggetto (chiave `object:` e la chiave stabile), o un gruppo
di frame senza nome e senza cielo (chiave `frames:` e la chiave del gruppo). La scheda e' una
(`ObjectCard`), e la risposta pure: una voce del catalogo, un nome scritto, o "non e' un
oggetto". In cima le domande -- i gruppi e i dubbi (`identity_confidence = 'low'`) senza
risposta --, coi **candidati che il cielo ha trovato nel suo campo** da cliccare quando ne ha
trovati; zero candidati e' una scheda come le altre. Le schede degli oggetti che l'app sa, senza
niente da scegliere, stanno chiuse e si aprono a pagine, coi conteggi: a schermo 5, poi 50 alla
volta, e si correggono a scheda sotto la riga (tavola v82).

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
senza sapere perche': lo dice il passo ASTAP del primo avvio (`sito.md`), **prima della prima
scansione**. Dove sta il solver lo dice l'utente con la preferenza `astap_path`, che viene
**prima** della ricerca automatica e della variabile d'ambiente `ASTROLOG_ASTAP` (quella la
mette chi lancia l'app, non chi la usa). La ricerca ha una casa sola, `solve.solver_path`: la
leggono lo stadio che risolve e la riga di `missing` che avvisa a schermo, cosi' l'avviso non
puo' dire una cosa e la corsa farne un'altra.

**Senza catalogo caricato vale la colonna "niente cielo"**, anche su un frame risolto: il cono
non ha nessuno da restituire, quindi la decisione ricade sul nome dell'header. L'app cataloga,
cerca e conta le ore lo stesso -- ma gli oggetti che nascono cosi' sono fuori catalogo, e
quando un catalogo nuovo arriva **tutti i frame gia' passati da `identify`** (fatti o saltati) tornano in coda
(`api/app._load_catalog`), o resterebbero fuori catalogo per sempre; lo stesso catalogo di prima
non rimette in coda niente (`test_a_new_catalog_sends_the_identified_frames_back_to_identify`).

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

**Cosa `identify` NON fa**: la relazione pezzo/adiacenza (`NGC 2244` dentro la Rosetta,
`catalogo.md`). E non tocca i FITS, mai.
