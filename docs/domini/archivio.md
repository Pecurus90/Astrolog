# L'Archivio -- contratto

**Cosa hai ripreso**, e quanto. E' la prima pagina che racconta l'archivio invece di chiedertene
conto: gli oggetti, con quanti frame, quante ore e con che filtri, in due viste -- **a carte** e
a colonne. Le parole
vengono da [`glossario.md`](glossario.md); come si legge il nome di un oggetto sta in
[`spina-identify.md`](spina-identify.md); dove sta la voce nella barra, in [`navigazione.md`](navigazione.md).

## Cosa chiede l'utente

Le prove del frontend si chiamano col loro titolo e stanno in `frontend/tests/archivio.test.tsx`
(la pagina), in `frontend/tests/archivio-criteri.test.tsx` (ricerca e criteri), e i nomi delle
costellazioni in `frontend/tests/costellazioni.test.ts`;
quelle del backend in `backend/tests/test_spine_archive.py` (cerca, ordina), in
`backend/tests/test_spine_archive_criteria.py` (i nove criteri, la testa, i frame senza oggetto),
in `backend/tests/test_spine_archive_mosaic.py` (le righe dei mosaici) e in
`backend/tests/test_api_archive.py` (cosa la rotta manda).

| richiesta | prova |
|---|---|
| Apro l'Archivio e vedo cosa ho ripreso, con i frame e le ore | `test_the_archive_lists_what_you_shot`; *dice cosa hai ripreso, con i frame e le ore* |
| Le copie calibrate che tengo accanto agli originali non mi raddoppiano le ore | `test_a_rewritten_copy_is_not_another_hour_of_sky` |
| Un frame che non dice quanto e' durato non conta come zero: me lo dice a parte | `test_a_pose_without_a_time_is_not_zero_hours`; *un frame che non dice quanto e' durato non diventa zero* |
| Se nessun frame di un oggetto dice la durata, non mi scrive "0 h" | *se nessun frame dice la durata, non scrive zero ore* |
| Vedo con che filtri ho ripreso ogni oggetto, nell'ordine dei filtri, e quante ore ciascuno | `test_the_filters_of_an_object_come_with_it_from_the_same_house`, `test_a_night_or_an_object_lists_its_filters_in_the_one_order`, `test_the_archive_dropdown_offers_the_filters_in_the_one_order` (`backend/tests/test_filter_order.py`); *dice con che filtri hai ripreso, nell'ordine dei filtri* (la barra dei filtri e' quella delle Notti) <!-- glossario-ok --> |
| Un oggetto di cui i file non dicono il filtro non mi mostra pastiglie finte | *un oggetto senza filtri riconosciuti non mostra pastiglie finte* |
| L'Archivio si apre a carte, e con un clic lo vedo a colonne per confrontare | *si apre a carte, e l'altra vista e' a un clic* |
| Se mando a qualcuno il collegamento all'elenco, gli si apre l'elenco | *quale vista stai guardando resta nell'indirizzo* |
| Sotto il nome, nell'elenco, leggo il nome comune, e un mosaico dice i suoi pannelli | *nell'elenco sotto il nome c'e' il nome comune del catalogo, e il mosaico dice i suoi pannelli* |
| So quanti oggetti ho trovato, non solo quanti ne sto vedendo | `test_the_count_is_what_you_found_not_what_you_have`, `test_the_bar_narrows_the_page_and_the_count_follows`; *dice quanti ne ha trovati, non quanti ne stai vedendo* |
| Un oggetto solo non mi viene scritto "1 oggetti" | *un oggetto solo non prende il plurale* |
| Scrivo tre lettere e trovo il mio oggetto, con qualunque sigla lo chiami | `test_you_find_an_object_by_any_name_it_is_known_by`; *cercare stringe l'elenco nel backend, non a schermo* |
| Cancello quello che avevo scritto e l'archivio torna intero | `test_searching_for_nothing_is_not_searching` |
| Dalla ricerca nella barra apro un oggetto, e vedo lui solo (`?key=`), non anche quelli che ne contengono la sigla | `test_the_key_opens_the_archive_on_that_object_alone` (`backend/tests/test_search.py`); *con ?key= chiede quell'oggetto solo, dice che e' ristretto e come tornare*, *una chiave che non trova niente lo dice, e non sembra un archivio vuoto* (`ricerca.test.tsx`) |
| Stringo per catalogo, costellazione o filtro usato, e i criteri offrono solo quello che ho | `test_you_can_narrow_down_to_one_catalogue`, `test_you_can_narrow_down_to_one_constellation`, `test_you_can_narrow_down_to_one_filter`, `test_the_choices_are_only_what_the_archive_has`; *i criteri offrono quello che hai, e quello con una voce sola non compare* |
| Scelgo piu' voci dello stesso criterio e passa chi ne ha una; criteri diversi valgono tutti | `test_two_choices_of_one_criterion_are_either`, `test_two_criteria_hold_together` |
| Ogni voce dice quante righe darebbe con le altre scelte accese, e una a zero si vede spenta | `test_each_option_counts_the_rows_with_the_other_choices`, `test_an_option_count_is_the_page_it_would_give`; *una voce a zero e' spenta e non si sceglie* |
| Stringo per tipo (galassia, nebulosa, ammasso, stella) e per produzioni (una, piu', mosaico) | `test_you_can_narrow_down_to_a_kind_of_object`, `test_you_can_narrow_down_by_how_many_productions` |
| Ordino per nome, integrazione o dai piu' recenti, e l'archivio si apre in ordine di nome | `test_the_archive_is_sorted_by_name_and_a_name_is_catalogue_then_number`, `test_by_hours_and_by_the_latest_night_are_two_different_orders`; *l'ordine lo sceglie l'utente e lo fa il backend* |
| In testa leggo tutto l'archivio: righe, mosaici, ore, frame, notti, qualunque criterio sia acceso | `test_the_totals_are_the_whole_archive_whatever_the_bar_says` |
| I frame che non hanno un oggetto stanno in una carta loro in testa, e se manca ASTAP me lo dice | `test_the_frames_without_an_object_are_counted_apart`, `test_a_missing_solver_is_said_with_the_frames_it_leaves`; *i frame senza oggetto hanno la loro carta, e senza ASTAP l'avviso porta alle Impostazioni*, *coi criteri la carta dei frame senza oggetto resta in testa, anche senza oggetti trovati* |
| Sotto il nome leggo il nome comune che il catalogo conosce | `test_a_row_carries_the_common_name_of_the_catalog` |
| Se un criterio non trova niente me lo dice, e mi lascia il modo di toglierlo | *quando un criterio non trova niente lo dice, e lascia il modo di toglierlo* |
| Mando a qualcuno il collegamento di una ricerca e gli si apre la stessa | *scegliere una voce la scrive nell'indirizzo e la chiede alla rotta*, *due voci dello stesso criterio vanno insieme, e la rotta le riceve tutte e due*, *un indirizzo scritto male non stringe* |
| Scrivere non riempie la cronologia; una scelta si', e il tasto indietro torna a quella di prima | *scrivere non riempie la cronologia, e una parola sola e' una domanda sola*, *una tendina lascia la sua traccia, e il tasto indietro torna al filtro di prima* |
| Se la rete cade dopo una scelta, la testa e i criteri restano e la posso togliere | *se la rete cade dopo un filtro, la barra resta e il filtro si puo' togliere* |
| Un tempo piccolo ma vero non mi viene scritto zero | *un tempo vero ma piccolo non diventa zero* (`frontend/tests/formati.test.ts`) |
| Per gli oggetti di catalogo vedo in che costellazione sono e che cosa sono | `test_the_catalog_says_what_kind_of_thing_it_is` |
| I criteri stanno nell'ordine della tavola, e i siti e i pezzi si leggono col nome | *i criteri offrono le voci con quante righe darebbero, nell'ordine della tavola* |
| La costellazione la leggo col nome latino ufficiale, uguale in ogni lingua | *la costellazione si legge col suo nome latino, non con la sigla*, *ogni sigla del catalogo ha il suo nome*, *il nome e' quello latino ufficiale, anche con la dieresi*, *una sigla che non conosce resta la sigla, invece di sparire* |
| Se ho molti oggetti li vedo tutti, non solo i primi | `test_the_list_is_paged_like_every_other`; *quando ce n e piu' di una pagina, si possono vedere anche gli altri* |
| Appena installata, la pagina mi dice cosa fare invece di sembrare rotta | `test_an_empty_archive_is_an_answer_not_an_error`; *a mani vuote dice cosa fare, non nessun risultato* |
| Se l'archivio non risponde me lo dice, invece di sembrare vuoto, e posso riprovare | *se l archivio non risponde lo dice, invece di sembrare vuoto, e si riprova* |
| Mentre legge, la pagina tiene il posto delle carte | *mentre legge tiene il posto delle carte, e lo dice a chi ascolta* |
| Accanto a *Mostra altri 20* leggo quanti ne vedo e quanti sono | *accanto a Mostra altri dice quanti ne stai vedendo e quanti sono* |
| Cio' che il catalogo o i file non dicono, la carta lo dice a parole | *un oggetto che il catalogo non conosce lo dice nella carta, tipo e costellazione*, *un oggetto senza filtri riconosciuti non mostra pastiglie finte*, *un tipo che la pagina non conosce non arriva a schermo come sigla: dice che non si sa* |
| Ogni riga dice con quali setup l'ho ripresa: una produzione per ottica e camera, e insieme fanno la riga | `test_an_object_shot_with_two_rigs_has_two_productions_most_time_first`, `test_the_productions_of_a_row_add_up_to_the_row`, `test_each_production_says_its_own_filters_in_the_order_of_the_row`, `test_a_rewritten_copy_is_not_a_frame_of_a_production`, `test_a_narrowed_row_tells_the_productions_of_what_was_asked`, `test_a_mosaic_has_its_productions_too_and_the_object_alone_keeps_its_own` (`backend/tests/test_spine_archive_productions.py`); `test_each_row_carries_its_productions_and_they_add_up_to_the_row` |
| Un riduttore non fa un'altra produzione; i frame senza setup lo dicono | `test_the_same_optics_and_camera_at_two_focal_lengths_are_one_production`, `test_frames_that_do_not_say_their_rig_are_a_production_that_says_so`, `test_a_rig_that_knows_only_its_camera_is_its_own_production` |
| Le produzioni di una pagina costano due domande, non una per riga | `test_all_the_productions_of_a_page_come_in_two_questions` |
| La carta ha un posto di anteprima per produzione e dice quante sono; l'elenco dice una, quante o il mosaico | *la carta ha un posto di anteprima per produzione, e dice quante sono*, *oltre tre produzioni le anteprime vanno su due righe, senza nasconderne*, *nell'elenco la colonna delle produzioni dice una, quante, o il mosaico* |
| La carta e il nome nell'elenco aprono la finestra dell'oggetto, le produzioni una alla volta | *il tocco sulla carta la apre: nome, nome comune, periodo, siti, ore e frame*, *con piu' produzioni le mostra una alla volta, e la scelta la chiede all'API*, *una produzione sola non ha linguette*, *le frecce vanno all'oggetto prima e dopo nell'ordine della pagina, Esc chiude*, *nell'elenco il nome apre la stessa finestra* (`frontend/tests/archivio-finestra.test.tsx`) |
| La finestra dice cio' che l'API scrive: notti, setup, catalogo con parsec e Lune piene | `test_its_nights_in_shooting_order_with_what_it_took_in_each`, `test_the_setups_that_took_it_with_its_frames_only`, `test_what_the_catalog_says_with_its_size_on_the_sky`, `test_a_production_with_pieces_the_frames_do_not_say` (`backend/tests/test_api_object_detail.py`); *in cielo dice tipo, costellazione, distanza e quanto e' grande accanto alla Luna piena*, *un oggetto fuori catalogo lo dice, senza inventare tipo e costellazione*, *un oggetto che non c'e' piu' lo dice* |
| Un mosaico che ho confermato e' una riga sola, col nome che gli ho dato e le ore di tutti i pannelli | `test_a_confirmed_mosaic_is_one_row_with_the_hours_of_all_its_panels`, `test_after_the_yes_the_archive_shows_the_mosaic_as_one_row` (`backend/tests/test_review_mosaic.py`) |
| Un oggetto ripreso dentro un mosaico e anche da solo ha la sua riga con le sole riprese sue, e niente si conta due volte | `test_an_object_shot_inside_and_outside_a_mosaic_keeps_its_own_poses`, `test_the_pills_of_a_row_are_the_filters_of_its_own_poses` |
| Cercando o filtrando, un mosaico compare intero se uno dei suoi pannelli risponde | `test_a_filter_of_the_bar_lets_the_mosaic_through_if_one_of_its_poses_passes`, `test_the_filter_used_is_asked_of_the_poses_of_the_row`, `test_a_mosaic_named_with_a_free_name_is_found_by_that_name` |
| Un mosaico proposto e non ancora confermato non cambia l'Archivio | `test_without_a_confirmed_mosaic_nothing_changes` |
| Un mosaico dice di esserlo e quanti pannelli ha, nelle due viste e anche a chi ascolta | `test_a_mosaic_row_says_how_many_panels_it_has`; *la carta di un mosaico dice mosaico e quanti pannelli, e si sente*, *nell'elenco la colonna delle produzioni dice una, quante, o il mosaico* |
| Ogni pannello di un mosaico, numerato, col suo oggetto, i frame e le ore, arriva con la riga e si apre nella finestra (il punto del cielo arriva dalla rotta e non si scrive: Marco, 8/10/2026) | `test_every_panel_of_a_mosaic_says_its_object_its_frames_and_its_hours`, `test_a_panel_counts_like_every_row_copies_out_and_untimed_apart`, `test_a_panel_whose_poses_found_no_object_says_so_with_nothing`, `test_the_route_gives_a_mosaic_its_panels_and_an_object_none`, `test_all_the_panels_of_a_page_come_in_two_questions` <!-- glossario-ok --> |
| Posso vedere solo i mosaici, e la voce *mosaico* c'e' solo se ne ho | `test_you_can_narrow_down_by_how_many_productions`, `test_the_choices_are_only_what_the_archive_has` |
| Stringo a uno o piu' anni, e ogni riga dice solo le ore, i frame e i filtri di quegli anni | `test_a_period_keeps_the_rows_shot_in_it_with_their_hours_in_it`, `test_two_years_are_either`, `test_the_pills_of_a_row_say_the_narrowed_hours` (`backend/tests/test_spine_archive_scope.py`) |
| Il periodo guarda la notte, non l'orologio | `test_the_period_reads_the_night_not_the_clock` |
| Stringo per sito, ottica o camera, e le condizioni valgono sulla stessa posa | `test_you_can_narrow_down_to_one_optics_or_one_camera`, `test_you_can_narrow_down_to_one_site`, `test_the_narrowings_hold_on_the_same_pose`, `test_the_filter_of_the_bar_asks_the_same_poses` |
| Per ore, con un periodo acceso, l'ordine segue le ore del periodo | `test_by_hours_reads_the_narrowed_hours` |
| Un mosaico stretto a un periodo apre i soli pannelli ripresi allora | `test_a_mosaic_says_only_the_panels_and_hours_shot_in_the_period` |
| I criteri offrono gli anni delle mie notti, i siti e i pezzi con cui ho ripreso, ognuno solo se ha almeno due voci | `test_the_choices_offer_the_years_sites_and_pieces_you_shot_with`, `test_one_site_or_one_camera_is_not_a_choice`, `test_a_chosen_option_stays_even_alone` |
| "Togli i criteri" toglie anche periodo e setup | *togli i criteri toglie anche il periodo e il setup* |
| La conta dice quante righe ho trovato | `test_the_count_says_how_many_objects_and_how_many_mosaics`; *dice quanti ne ha trovati, non quanti ne stai vedendo*, *dice quanti ne stai vedendo su quanti sono, e in che ordine* |
| In testa leggo tutto l'archivio | *in testa dice tutto l'archivio: oggetti, mosaici, ore, frame e notti* |
| Se i miei frame non sanno la notte (non ho dato un sito), non mi scrive "0 notti" | *se i frame non sanno la notte (nessun sito), la testa non scrive zero notti* |

## Le decisioni

**L'Archivio e' la vetrina del lavoro finito** (Marco, 22/9/2026). Un progetto nasce **solo nel
Planner**, e l'Archivio non lo propone (Marco, 24/10/2026): si sceglie un oggetto e ci si da' un
obiettivo -- tante ore, tanti frame, quel che sara'. Finche' e' aperto si guarda nei Progetti e nelle Notti; **quando e' concluso
passa in Archivio**, e la riga e' il **riepilogo di quel progetto**. Quindi la riga dell'Archivio
sara' un **progetto chiuso, non un oggetto**.

**Due progetti sullo stesso oggetto si distinguono dal puntamento** (Marco, 22/9/2026): se le
coordinate coincidono e' la stessa cosa -- riprese aggiunte allo stesso progetto, anche a un anno
di distanza -- e se divergono sono **due progetti diversi sullo stesso oggetto**. Non e' l'anno a
dividerli: e' dove hai puntato, e il setup (un progetto, un setup: ADR 0013, 0033 R1). E' la stessa parita' del mosaico
(`mosaico.md`), che pure ragiona su dove il setup guardava.

**Ma non e' cosi' oggi, e non e' un rinvio per pigrizia**: i progetti non esistono -- nessuna
tabella, nessuna rotta, nessuna pagina -- e stanno **dopo** l'Archivio nel piano. Applicare la
regola adesso darebbe una pagina **vuota per chiunque**. Finche' non ci sono, la riga e' un
**gruppo di frame**: un oggetto, o un mosaico confermato. Il passaggio ai progetti, nel codice, e'
**una condizione in piu'** nella domanda al database: la veste, le carte, l'elenco e le pastiglie
non si rifanno.

**Una riga e' un gruppo di frame, non un oggetto** (Marco, 22/9/2026). Un mosaico e' un insieme di
frame -- lo stesso oggetto puo' averne dentro e fuori -- quindi la riga di un mosaico porta **tutti**
i suoi frame, e quella di un oggetto **solo** quelli che nessun mosaico ha preso: nessuna ora
contata due volte, nessuna persa. La riga si legge dalla chiave scritta sul frame
(`frames.mosaic_key`, [`mosaico.md`](mosaico.md)), mai dalla geometria: una lettura non calcola.
Chi raggruppa e' solo l'Archivio: le Notti e *Da confermare* guardano l'oggetto intero.

**Un filtro della barra fa passare il gruppo se uno dei suoi frame passa**, e ogni filtro per
conto suo. I pannelli di un mosaico sono oggetti di cataloghi diversi -- i quattro di IC 405 sono
IC, LBN, LDN e Sh2 -- e filtrando i frame invece dei gruppi la riga del mosaico direbbe una parte delle ore. E la
pagina conta **righe**: venti chieste sono venti righe, non venti oggetti. A schermo la testa
dice i mosaici dentro le righe: *240 oggetti, di cui 3 mosaici* (tavola). Quanti pannelli ha un mosaico lo sa solo
la geometria, quindi lo scrive sui frame chi la fa (`frames.panel_id`), e la riga li conta. Ogni
pannello si legge allo stesso modo: i suoi frame, contati come ogni riga, il suo oggetto e il
centro che la geometria ha scritto (`panels`); il centro dice **quale** pannello, se due inquadrano
lo stesso oggetto. Tutti i pannelli della pagina arrivano in due domande, non in una per mosaico.

**Periodo, sito, ottica e camera stringono i frame, e la riga dice quelli** (Marco, 7/10/2026:
*"se e' per periodo deve mostrare il periodo"*). Catalogo, costellazione e ricerca chiedono chi e'
la riga; il filtro usato e questi quattro chiedono i suoi frame. Il filtro usato fa passare la
riga e lascia le ore di sempre, perche' le pastiglie gia' dicono le ore per filtro; questi quattro
invece **restringono** cio' che la riga conta -- ore, frame, pastiglie, pannelli -- perche' "M 31,
12 h" sotto "2025" direbbe una cosa falsa a chi quell'anno ne ha fatte 2. La condizione e' una
sola (`counts.Scope`) e si chiede allo stesso frame: "casa e ASI533" e' un frame fatto a casa con
la ASI533, non un oggetto che ha frame dell'una e dell'altra. Il periodo si legge sulla **notte**
(`nights.night_date`, nel fuso del sito), mai su `date_obs`; un anno e' dal primo gennaio al
trentuno dicembre, le due estreme comprese. Il numero dei pannelli di un mosaico resta quello del
mosaico: e' cio' che il mosaico e', non cio' che e' stato ripreso nel periodo.

**I criteri sono nove, a scelta multipla, e ogni voce dice quante righe darebbe** (tavola v56.11
e v78, `Archivio.dc.html` 139-148; superano le tendine a una voce del disegno v31). In ordine:
Periodo (gli anni delle notti), Tipo, Costellazione, Filtri, Produzioni (una, piu', mosaico),
Sito, Ottica, Camera, Catalogo. Dentro un criterio basta una voce (o), fra criteri valgono tutti
(e). La regola che fa passare una riga e' una sola (`spine/archive.where`): la conta di una voce
e' quella regola con le altre scelte accese e questa voce al posto di quelle del suo criterio,
(`spine/archive_criteria.py`): una domanda raggruppata per i criteri della riga (tipo,
costellazione, produzioni, catalogo), e una sola per i cinque dei frame (periodo, filtri, sito,
ottica, camera), che legge i frame una volta raggruppati per riga, notte, setup e filtro: ogni
loro voce cambia i frame contati, e filtro e produzioni si chiedono a quei frame, come fa la
regola. Una prova la confronta
con la pagina che la voce darebbe. Una voce a zero resta a schermo, spenta: sparire farebbe
saltare le altre sotto il dito. **Un criterio si offre solo da due voci in su**: con una sola,
sceglierla non stringe niente; una voce scelta resta in elenco anche a zero. Ottica e camera si
leggono dal setup della posa (`rigs`), come le conta l'Attrezzatura.

**Il tipo e' una famiglia, non il codice del catalogo**: galassia (anche coppie, gruppi e ammassi
di galassie), nebulosa (oscura, a emissione, a riflessione, planetaria, regione HII, resto di
supernova), ammasso (aperto, globulare, stellare), stella (anche doppia, nova, Wolf-Rayet), altro,
e "non si sa" per chi il catalogo non conosce. La tavola raggruppa per la prima parola del nome
italiano, che metterebbe gli ammassi di galassie con gli ammassi stellari; la famiglia sta in
`spine/archive.TYPE_FAMILY`. **Le produzioni** contano le coppie ottica e camera dei
frame della riga nel periodo, sito e setup scelti, come `productions.py`; un mosaico e' "mosaico".

**In testa, tutto l'archivio** (tavola, «240 oggetti, di cui 3 mosaici · 486 ore · 18 430 frame
· 212 notti»): righe, mosaici, ore, frame senza tempo, frame e notti di ogni riga, qualunque
criterio sia acceso (`totals`). La conta di cio' che hai trovato sta accanto alla ricerca. Zero
notti con dei frame vuol dire che i frame non sanno la notte (nessun sito dato): la testa non
scrive le notti, come non scrive le ore a zero ("non lo so" non e' zero).

**I frame senza oggetto hanno una carta loro, in testa** (tavola, stato «nessun oggetto
identificato»): i frame di luce che nessun oggetto e nessun mosaico hanno preso, copie escluse,
con ore, frame senza tempo e filtri (`unresolved`). Se ASTAP non c'e' la carta si chiama «Non
risolti» e sopra un avviso porta alle Impostazioni; se c'e', «Senza oggetti identificati». La
carta resta in testa anche coi criteri accesi (tavola 172), e manca solo sulla riga aperta dalla
Ricerca (`?key=`). La carta non si apre: quei frame si guardano in Da confermare.

**E costa quanto le righe che mostra, non quanto i frame che contengono.** Le ore si contano solo
per le righe della pagina, e la conta non le calcola; un filtro guarda i pannelli solo di un
mosaico. Lo misurano `backend/tests/test_spine_archive_cost.py`, in passi del motore e non in
millisecondi. Le conte delle voci leggono invece i frame, una volta per i cinque criteri dei frame
qualunque sia il numero delle voci: e' il prezzo di sapere quante righe darebbe ogni voce. Costano
poche pagine con una forma accesa (`test_the_criteria_read_the_frames_once_not_once_per_option`),
e arrivano con la sola prima pagina: «Mostra altri» non le cambia, la pagina le tiene da li'.

**Le ore si sommano nel backend, e le copie non contano.** I tre sotto-select stanno in una casa
sola (`spine/counts.py`), e li usano l'Archivio, *Da confermare* e le Notti: il nome di un oggetto
sono gia' due passi, e due query che li scrivono ognuna a modo suo sono il modo in cui due pagine
dello stesso archivio cominciano a dire nomi diversi. Ogni conteggio esclude le copie riscritte
(`copy_of`): chi elabora tiene grezzo e calibrato nella stessa cartella, e contarli tutti e due
raddoppierebbe la vita osservativa di chiunque.

**"Non lo so" non e' zero, e si mostra come in Da confermare.** Un frame senza tempo non entra
nella somma e si conta a parte (`untimed`). A schermo il tempo passa da `TempoDellePose`, lo stesso
pezzo degli oggetti e dei mosaici di Da confermare: le ore **solo se ci sono**, i frame senza tempo
accanto. Cosi' un oggetto di cui nessun frame dice la durata non mostra "0 h", e lo stesso oggetto
si legge nello stesso modo da qualunque pagina lo guardi.

**L'ordine di partenza e' il nome, perche' questo e' un inventario** (Marco, 22/9/2026: *"la
parte delle riprese con le date avviene gia' con le notti"*). I tre ordini sono **nome,
integrazione, piu' recenti** (tavola v56.11, 25/10/2026, che supera "frame"): l'ultimo legge
l'ultima notte dei frame della riga nel periodo scelto, e chi non ne ha va in fondo. Li sceglie
l'utente e li fa il **backend** -- due viste della stessa pagina ordinate in
due posti andrebbero d'accordo per caso. L'id chiude sempre, perche' senza un ultimo criterio
stabile due pagine consecutive potrebbero mostrare la stessa riga due volte.

**E "per nome" non e' l'alfabeto nudo**: li' `M 13` finirebbe dopo `M 103`, e un archivio ordinato
cosi' nessuno lo riconosce. Si legge **catalogo e poi numero**, dalla designazione principale del
catalogo; chi un catalogo non ce l'ha va in fondo, per nome -- e' l'oggetto che l'app non sa
collocare, non il primo della lista.

**Le due viste guardano le stesse righe, e quale guardi sta nell'indirizzo.** Si apre **a
carte** (Marco, 22/9/2026), il caso "guardo cosa ho"; l'elenco a colonne e' il caso
"confronto". Scambiarle non richiede niente al backend -- e' la stessa pagina raccontata in due
modi -- e il nome della vista sta in `?vista=`, o un collegamento all'elenco si riaprirebbe a
carte: chi lo manda a qualcuno manderebbe un'altra pagina.

**Mentre la risposta arriva resta a schermo cio' che c'era, e la barra lo dice.** Svuotare la
pagina a ogni ricerca smonterebbe il campo e con lui il **fuoco**, a meta' parola. Tenere cio' che
c'era pero' vuol dire che per un attimo la conta, le righe -- o lo stato vuoto -- rispondono a una
domanda vecchia. Il segno sta su **chi ha chiesto** -- il campo di ricerca, con la parola *cerco*, o la
tendina appena cambiata -- e su campo e tendine insieme quando la richiesta non parte dalla barra
(il tasto indietro, *Togli i criteri*); non sulle righe: le
righe possono essere zero, ed e' proprio li' che serve di piu'. E la barra lo **dichiara**
(`aria-busy`), perche' chi ascolta non vede il movimento. **Niente si spegne**: cambiare idea a
meta' attesa e' legittimo.

**Dalla prima risposta in poi, la barra non dipende dalla risposta.** Le ultime scelte viste
restano in mano, cosi' un errore di rete -- il backend che si riavvia mentre cerchi -- lascia a
schermo il modo di togliere il criterio. Senza, resterebbero un avviso e un criterio acceso che si
toglie solo col tasto indietro del browser. Se a cadere e' la **prima** risposta le scelte non le
abbiamo ancora viste, e li' quello scenario resta: sta nella Issue #18 ("Un errore alla primissima
risposta lascia un criterio acceso senza il modo di toglierlo"), perche' il rimedio --
una barra col campo e senza tendine -- e' un'altra decisione.

**Ogni scelta lascia la sua traccia, tranne lo scrivere -- e una scelta che non cambia niente non
lascia niente.** Una tendina, un ordine, la vista: sono gesti, e il tasto indietro deve tornare a
quello di prima invece di uscire dall'Archivio. Ricliccare la scheda che stai gia' guardando non
e' un gesto: lascerebbe una tappa identica alla precedente, e il tasto indietro non farebbe nulla.
La **ricerca** no -- una traccia per ogni tasto battuto renderebbe il tasto indietro inutile,
tre pressioni per disfare `m31` -- quindi sostituisce. E aspetta un attimo prima di partire:
una parola e' **una** domanda al backend, non una per lettera.

**La barra stringe nel backend, e cio' che stai guardando sta nell'indirizzo.** Cercare fra le
cento righe gia' scaricate troverebbe solo quelle: a chi ha seicento oggetti l'app direbbe "non
trovato" mentendo. La ricerca guarda **tutti i nomi con cui un oggetto e' conosciuto** -- i suoi e
le designazioni di catalogo -- senza spazi e senza maiuscole, perche' `m31`, `M 31` e `NGC 224`
sono la stessa galassia e nessuno scrive una sigla sempre allo stesso modo. Non usa l'indice ed e'
voluto: qui si parla di una manciata di righe, non di centomila.

**Le tendine offrono cio' che hai, non cio' che il catalogo conosce.** Le sigle e le
costellazioni del catalogo sono molte piu' di quelle che un archivio tocca -- quante, lo conta
`test_the_choices_are_only_what_the_archive_has` -- e offrirle tutte a chi ne usa due e' una
tendina che fa perdere tempo.
E' la stessa regola delle ore per genere -- per archivio, non per elenco fisso -- e una tendina
senza niente da scegliere **non compare**, invece di promettere qualcosa e non farlo.

**"Non ho trovato niente" non e' "non hai niente".** Il primo e' una risposta a cio' che hai
chiesto e tiene la barra a schermo, col modo di togliere i criteri; il secondo e' lo stato di chi
ha appena installato l'app e porta al gesto che lo riempie. Dire le stesse parole manderebbe a
cercare le cartelle chi le ha gia' indicate.

**E la conta e' quella che hai trovato**, non quella che hai: con un criterio acceso "1 240 oggetti"
sarebbe un numero che mente, ed e' anche il numero su cui la pagina decide se ce n'e' un'altra.

**La costellazione si scrive col nome latino ufficiale, uguale in ogni lingua** (Marco,
27/9/2026): *Cygnus*, *Canes Venatici*, non tradotto -- e' il nome dei cataloghi, e vale per tutti
senza una traduzione da tenere. I nomi vengono dall'elenco ufficiale dell'IAU, citato accanto alla
tabella che li porta.

**L'elenco si impagina a venti righe** (tavola, «Mostra altri 20», che supera le cento del
disegno v31): venti carte sono quattro file da cinque, e chi cerca usa la ricerca e i criteri.

## La carta e le produzioni (Marco, 8/10/2026)

Disegno v31, la carta "Di lato": a sinistra il posto dell'anteprima, a destra nome, tipo e
costellazione, ore e frame; sotto i filtri (la barra delle Notti) e, per un mosaico, i pannelli.

**Una produzione** e' lo stesso oggetto ripreso con la stessa ottica e la stessa camera (Marco,
8/10/2026), finche' non esistono i progetti; domani sara' un progetto concluso. La rotta le
manda con ogni riga (`productions`, `spine/productions.py`): ottica, camera, frame, ore, frame
senza tempo e i filtri di quei frame, da quella a cui e' andato piu' tempo. Insieme fanno la riga:
niente si conta due volte. Decisioni (8/10/2026): due setup con la stessa ottica e la stessa
camera a focali diverse (un riduttore) sono **una** produzione; i frame che non dicono il setup
sono una produzione col setup che non si sa, e meta' setup (solo la camera) e' una produzione
sua; un mosaico ha le sue produzioni come ogni riga; stringendo la barra, le produzioni sono
quelle dei frame chiesti. La carta ha un posto di anteprima **per produzione** e dice quante
sono; l'elenco lo dice solo quando sono piu' d'una.

## La finestra dell'oggetto (tavola v76, passo 33)

Toccare una carta, o il nome nell'elenco, apre la **finestra dell'oggetto** sopra la pagina
(`componenti/Riepilogo.dc.html` tipo oggetto; supera il riepilogo delle produzioni sotto la
carta): larga 1180 sul desktop, pagina intera sul telefono, ‹ › per l'oggetto prima e dopo
nell'ordine della pagina, si chiude con x, Esc o fuori. Gli stessi pezzi della finestra della
notte (`RiepilogoComune.tsx`). Tutto da `GET /api/v1/objects/{key}`: la riga dell'Archivio, le
notti in ordine di ripresa (la riga delle Notti e cio' che l'oggetto ha preso quella notte),
prima e ultima notte, siti, i setup con gli strumenti, il catalogo (tipo, costellazione,
distanza in anni luce e parsec, estensione, dimensione in primi accanto alla Luna piena, scritti
al caricamento del catalogo). Con piu' produzioni, **una alla volta**: linguette in testa, la
prima scelta; `?production=ottica:camera` restringe tutto, `none` per un pezzo che i frame non
dicono. Un **mosaico** ha le linguette dei pannelli al posto delle produzioni (Riepilogo.dc.html
116-118): «Riepilogo generale» e «Pannello N», nell'ordine di `panel_list`; `?panel=id` restringe
tutto, misure comprese (scritte anche per pannello, di tutte le produzioni), e il catalogo e'
dell'oggetto del pannello se ne ha uno solo in catalogo, se no del mosaico. Le notti di un
mosaico sono quelle dei suoi frame; l'oggetto di un suo pannello tiene solo le notti in cui e'
stato ripreso da solo. Le notti portano alla loro pagina (`/notti?notte=id`). La stessa finestra
si apre, **senza rotta d'oggetto** (Marco, 9/11/2026), anche dalla **Ricerca** e dal nome di un
oggetto in «Gli oggetti» della finestra della notte, sopra la pagina dove sei
(`FinestraDellOggetto.tsx`, tenuta dal telaio); dalla notte prende il posto della sua finestra,
perche' due finestre insieme si chiuderebbero insieme con lo stesso Esc. Le frecce ci sono spente:
l'ordine e' quello di una pagina dell'Archivio. Cambiare pagina la chiude. Cosa fa diverso
dalla tavola sta in `handoff/differenze-dalle-tavole.md`.

## Cosa NON fa

Non ha ancora l'etichetta dei **progetti**, che non esistono. I
pannelli di un mosaico stanno nella **finestra** dell'oggetto, non nella carta (tavola v76). Non
mostra **anteprime** finche' non si salvano (passo 33.2): il pozzo che le aspetta tiene gia' il
suo posto nella carta. Non mostra **l'ultima notte** (Marco, 22/9/2026): ordina per lei, ma
quando l'hai ripreso l'ultima volta si guarda nelle Notti. Non ha ancora **Sole, Sistema solare
e Aggiungi oggetto** della tavola (ADR 0019, passo 46.12): nessuna sorgente li scrive, e linguette
che portano a niente non si mostrano.
