# L'Archivio -- contratto

**Cosa hai ripreso**, e quanto. E' la prima pagina che racconta l'archivio invece di chiedertene
conto: gli oggetti, con quanti frame, quante ore e con che filtri, in due viste -- **a carte** e
a colonne. Le parole
vengono da [`glossario.md`](glossario.md); come si legge il nome di un oggetto sta in
[`spina.md`](spina.md); dove sta la voce nella barra, in [`navigazione.md`](navigazione.md).

## Cosa chiede l'utente

Le prove del frontend si chiamano col loro titolo e stanno in `frontend/tests/archivio.test.tsx`
(la pagina), in `frontend/tests/archivio-barra.test.tsx` (i controlli) e in
`frontend/tests/archivio-mosaici.test.tsx` (i mosaici), e i nomi delle costellazioni in
`frontend/tests/costellazioni.test.ts`;
quelle del backend in `backend/tests/test_spine_archive.py` (la barra: cerca, filtra, ordina,
le tendine), in `backend/tests/test_spine_archive_mosaic.py` (le righe dei mosaici) e in
`backend/tests/test_api_archive.py` (cosa la rotta manda).

| richiesta | prova |
|---|---|
| Apro l'Archivio e vedo cosa ho ripreso, con i frame e le ore | `test_the_archive_lists_what_you_shot`; *dice cosa hai ripreso, con i frame e le ore* |
| Le copie calibrate che tengo accanto agli originali non mi raddoppiano le ore | `test_a_rewritten_copy_is_not_another_hour_of_sky` |
| Un frame che non dice quanto e' durato non conta come zero: me lo dice a parte | `test_a_pose_without_a_time_is_not_zero_hours`; *un frame che non dice quanto e' durato non diventa zero* |
| Se nessun frame di un oggetto dice la durata, non mi scrive "0 h" | *se nessun frame dice la durata, non scrive zero ore* |
| Vedo con che filtri ho ripreso ogni oggetto, dal piu' usato, e quante ore ciascuno | `test_the_filters_of_an_object_come_with_it_from_the_same_house`; *dice con che filtri hai ripreso, dal piu' usato*, *ogni filtro dice le sue ore, nelle carte e nell'elenco*, *un filtro le cui pose non dicono la durata non scrive ore* |
| Un oggetto di cui i file non dicono il filtro non mi mostra pastiglie finte | *un oggetto senza filtri riconosciuti non mostra pastiglie finte* |
| L'Archivio si apre a carte, e con un clic lo vedo a colonne per confrontare | *si apre a carte, e l'altra vista e' a un clic* |
| Se mando a qualcuno il collegamento all'elenco, gli si apre l'elenco | *quale vista stai guardando resta nell'indirizzo* |
| Nell'elenco, una cella che il catalogo non sa riempire lo dice con un segno invece di restare vuota | *nell'elenco le celle che non sanno lo dicono con una forma, non con un vuoto* |
| So quanti oggetti ho trovato, non solo quanti ne sto vedendo | `test_the_count_is_what_you_found_not_what_you_have`, `test_the_bar_narrows_the_page_and_the_count_follows`; *dice quanti ne ha trovati, non quanti ne stai vedendo* |
| Un oggetto solo non mi viene scritto "1 oggetti" | *un oggetto solo non prende il plurale* |
| Scrivo tre lettere e trovo il mio oggetto, con qualunque sigla lo chiami | `test_you_find_an_object_by_any_name_it_is_known_by`; *cercare stringe l'elenco nel backend, non a schermo* |
| Cancello quello che avevo scritto e l'archivio torna intero | `test_searching_for_nothing_is_not_searching` |
| Stringo per catalogo, costellazione o filtro usato, e le tendine offrono solo quello che ho | `test_you_can_narrow_down_to_one_catalogue`, `test_you_can_narrow_down_to_one_constellation`, `test_you_can_narrow_down_to_one_filter`, `test_the_choices_are_only_what_the_archive_has`; *le tendine offrono quello che hai, e quella vuota non compare* |
| Ordino per nome, ore o frame, e l'archivio si apre in ordine di nome | `test_the_archive_is_sorted_by_name_and_a_name_is_catalogue_then_number`, `test_by_hours_and_by_frames_are_two_different_orders`; *l'ordine lo sceglie l'utente e lo fa il backend* |
| Se un filtro non trova niente me lo dice, e mi lascia il modo di toglierlo | *quando un filtro non trova niente lo dice, e lascia il modo di toglierlo* |
| Mando a qualcuno il collegamento di una ricerca e gli si apre la stessa | *scegliere un catalogo lo scrive nell'indirizzo, senza toccare la vista* |
| Un tempo piccolo ma vero non mi viene scritto zero | *un tempo vero ma piccolo non diventa zero* (`frontend/tests/formati.test.ts`) |
| Per gli oggetti di catalogo vedo in che costellazione sono e che cosa sono | `test_the_catalog_says_what_kind_of_thing_it_is` |
| Nella tendina le costellazioni stanno in ordine di nome | *la tendina delle costellazioni legge i nomi in ordine alfabetico, e sceglie la sigla* |
| La costellazione la leggo col nome latino ufficiale, uguale in ogni lingua | *la costellazione si legge col suo nome latino, non con la sigla*, *ogni sigla del catalogo ha il suo nome*, *il nome e' quello latino ufficiale, anche con la dieresi*, *una sigla che non conosce resta la sigla, invece di sparire* |
| Se ho molti oggetti li vedo tutti, non solo i primi | `test_the_list_is_paged_like_every_other`; *quando ce n e piu' di una pagina, si possono vedere anche gli altri* |
| Appena installata, la pagina mi dice cosa fare invece di sembrare rotta | `test_an_empty_archive_is_an_answer_not_an_error`; *a mani vuote dice cosa fare, non nessun risultato* |
| Se l'archivio non risponde me lo dice, invece di sembrare vuoto | *se l archivio non risponde lo dice, invece di sembrare vuoto* |
| Un mosaico che ho confermato e' una riga sola, col nome che gli ho dato e le ore di tutti i pannelli | `test_a_confirmed_mosaic_is_one_row_with_the_hours_of_all_its_panels`, `test_after_the_yes_the_archive_shows_the_mosaic_as_one_row` (`backend/tests/test_review_mosaic.py`) |
| Un oggetto ripreso dentro un mosaico e anche da solo ha la sua riga con le sole riprese sue, e niente si conta due volte | `test_an_object_shot_inside_and_outside_a_mosaic_keeps_its_own_poses`, `test_the_pills_of_a_row_are_the_filters_of_its_own_poses` |
| Cercando o filtrando, un mosaico compare intero se uno dei suoi pannelli risponde | `test_a_filter_of_the_bar_lets_the_mosaic_through_if_one_of_its_poses_passes`, `test_the_filter_used_is_asked_of_the_poses_of_the_row`, `test_a_mosaic_named_with_a_free_name_is_found_by_that_name` |
| Un mosaico proposto e non ancora confermato non cambia l'Archivio | `test_without_a_confirmed_mosaic_nothing_changes` |
| Un mosaico dice di esserlo e quanti pannelli ha, nelle due viste e anche a chi ascolta | `test_a_mosaic_row_says_how_many_panels_it_has`; *la carta di un mosaico dice mosaico e quanti pannelli, e si sente*, *anche nell'elenco la riga del mosaico porta la sua etichetta* (`frontend/tests/archivio-mosaici.test.tsx`) |
| La carta di un mosaico si apre e dice ogni pannello: il suo oggetto, i frame, le ore e dove sta nel cielo | `test_every_panel_of_a_mosaic_says_its_object_its_frames_and_its_hours`, `test_a_panel_counts_like_every_row_copies_out_and_untimed_apart`, `test_a_panel_whose_poses_found_no_object_says_so_with_nothing`, `test_the_route_gives_a_mosaic_its_panels_and_an_object_none`, `test_all_the_panels_of_a_page_come_in_two_questions`; *la carta del mosaico si apre e dice ogni pannello, con oggetto, frame, ore e dove sta*, *un pannello di cui il cielo non ha legato l'oggetto lo dice, e le pose senza tempo a parte*, *un oggetto non ha pannelli da aprire* (`frontend/tests/archivio-mosaici.test.tsx`) |
| Posso vedere solo i mosaici, e la tendina c'e' solo se ne ho | `test_you_can_narrow_down_to_the_mosaics`, `test_the_mosaic_choice_is_offered_only_to_who_has_a_mosaic`; *la tendina dei mosaici compare solo a chi ne ha, e stringe nel backend*, *chi non ha mosaici non vede la tendina* |
| La conta dice quanti oggetti e quanti mosaici ho trovato | `test_the_count_says_how_many_objects_and_how_many_mosaics`; *la conta dice quanti oggetti e quanti mosaici* |

## Le decisioni

**L'Archivio e' la vetrina del lavoro finito** (Marco, 22/9/2026). Un progetto nasce nei
**Progetti**, insieme al Planner: si sceglie un oggetto e ci si da' un obiettivo -- tante ore,
tanti frame, quel che sara'. Finche' e' aperto si guarda li' e nelle Notti; **quando e' concluso
passa in Archivio**, e la riga e' il **riepilogo di quel progetto**. Quindi la riga dell'Archivio
sara' un **progetto chiuso, non un oggetto**.

**Due progetti sullo stesso oggetto si distinguono dal puntamento** (Marco, 22/9/2026): se le
coordinate coincidono e' la stessa cosa -- riprese aggiunte allo stesso progetto, anche a un anno
di distanza -- e se divergono sono **due progetti diversi sullo stesso oggetto**. Non e' l'anno e
non e' il corredo a dividerli: e' dove hai puntato. E' la stessa parita' del mosaico
(`mosaico.md`), che pure ragiona su dove il corredo guardava.

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
pagina conta **righe**: cento chieste sono cento righe, non cento oggetti. A schermo pero' la conta
non chiama "oggetto" un mosaico: *3 oggetti e 1 mosaico*. Quanti pannelli ha un mosaico lo sa solo
la geometria, quindi lo scrive sui frame chi la fa (`frames.panel_id`), e la riga li conta. Ogni
pannello si legge allo stesso modo: i suoi frame, contati come ogni riga, il suo oggetto e il
centro che la geometria ha scritto (`panels`); il centro dice **quale** pannello, se due inquadrano
lo stesso oggetto. Tutti i pannelli della pagina arrivano in due domande, non in una per mosaico.

**E costa quanto le righe che mostra, non quanto le pose che contengono.** Le ore si contano solo
per le righe della pagina, e la conta non le calcola; un filtro guarda i pannelli solo di un
mosaico. Lo misurano `backend/tests/test_spine_archive_cost.py`, in passi del motore e non in
millisecondi.

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
parte delle riprese con le date avviene gia' con le notti"*). Prima si apriva dalla ripresa piu'
recente: quella domanda ha la sua pagina, e qui serviva a un'altra. I tre ordini sono **nome, ore,
frame**, li sceglie l'utente e li fa il **backend** -- due viste della stessa pagina ordinate in
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
domanda vecchia. Il segno sta sul **campo di ricerca** e sulle **tendine**, non sulle righe: le
righe possono essere zero, ed e' proprio li' che serve di piu'. E la barra lo **dichiara**
(`aria-busy`), perche' chi ascolta non vede il movimento. **Niente si spegne**: cambiare idea a
meta' attesa e' legittimo.

**Dalla prima risposta in poi, la barra non dipende dalla risposta.** Le ultime scelte viste
restano in mano, cosi' un errore di rete -- il backend che si riavvia mentre filtri -- lascia a
schermo il modo di togliere il filtro. Senza, resterebbero un avviso e un filtro acceso che si
toglie solo col tasto indietro del browser. Se a cadere e' la **prima** risposta le scelte non le
abbiamo ancora viste, e li' quello scenario resta: sta in `coda.md` ("Un errore alla primissima
risposta dell'Archivio lascia un filtro acceso senza il modo di toglierlo"), perche' il rimedio --
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
chiesto e tiene la barra a schermo, col modo di togliere i filtri; il secondo e' lo stato di chi
ha appena installato l'app e porta al gesto che lo riempie. Dire le stesse parole manderebbe a
cercare le cartelle chi le ha gia' indicate.

**E la conta e' quella che hai trovato**, non quella che hai: con un filtro acceso "1.240 oggetti"
sarebbe un numero che mente, ed e' anche il numero su cui la pagina decide se ce n'e' un'altra.

**La costellazione si scrive col nome latino ufficiale, uguale in ogni lingua** (Marco,
27/9/2026): *Cygnus*, *Canes Venatici*, non tradotto -- e' il nome dei cataloghi, e vale per tutti
senza una traduzione da tenere. I nomi vengono dall'elenco ufficiale dell'IAU, citato accanto alla
tabella che li porta.

**L'elenco si impagina come gli altri, ma largo** (cento righe per volta). E' un inventario, non
un flusso da scorrere: chi ha centomila frame ha comunque una manciata di oggetti.

## Cosa NON fa

Non ha ancora l'etichetta dei **progetti**, che non esistono, ne' la **scheda** di un oggetto. I
pannelli di un mosaico si aprono dalla sua **carta**, non dall'elenco. Non mostra **anteprime**: sono decise (la foto finale dell'utente, o
il suo frame migliore) ma non esistono ancora, e il pozzo che le aspetta tiene gia' il suo posto
nella carta. Non mostra piu' **l'ultima notte** (Marco, 22/9/2026): quel posto e' dei progetti, e
quando l'hai ripreso l'ultima volta si guarda nelle Notti.
