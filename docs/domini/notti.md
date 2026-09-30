# Le Notti -- contratto

**Quando hai ripreso**, e cosa hai fatto quella notte. L'Archivio racconta gli oggetti; questa
pagina racconta le **notti**, una per una: e' il modo in cui un astrofotografo si ricorda la vita
osservativa: *"la notte del 17 maggio, a Cima Ekar, M 51 e M 101, sei ore".* Le parole vengono da
[`glossario.md`](glossario.md); cos'e' una notte e chi la scrive sta in [`spina.md`](spina.md);
dove sta la voce nella barra, in [`navigazione.md`](navigazione.md); come si contano le ore e
perche' le copie non valgono, in [`archivio.md`](archivio.md), che ne e' la casa.

## Cosa chiede l'utente

Le prove del backend stanno in `backend/tests/test_api_nights.py`; quelle del frontend si chiamano
col loro titolo e stanno in `frontend/tests/notti.test.tsx`.

| richiesta | prova |
|---|---|
| Apro Notti e vedo le notti che ho ripreso, dalla piu' recente | `test_the_page_lists_the_nights_you_shot`; *elenca le notti, dalla piu' recente* |
| Ogni notte mi dice che giorno era, da dove, cosa ho ripreso, quante ore e quanti frame | `test_a_night_says_where_you_were_and_what_you_shot`; *una notte porta il giorno, il sito, gli oggetti, le ore e i frame* |
| Accanto alla data vedo anche che giorno della settimana era | *accanto alla data c'e' il giorno della settimana* |
| Vedo con che filtri ho ripreso quella notte, e quanto ho dato a ciascuno | `test_a_night_says_which_filters_and_how_long_each_one_ran`; *una notte dice i filtri, dal piu' usato* |
| In cima vedo quante notti, quante ore e quanti frame ho in tutto | `test_the_page_opens_with_what_the_whole_archive_holds`; *in cima ci sono le notti, le ore e i frame di tutto l'archivio* |
| Due siti nella stessa data restano due notti, non una | `test_two_sites_on_the_same_date_stay_two_nights` |
| Le copie calibrate che tengo accanto agli originali non mi raddoppiano le ore | `test_a_rewritten_copy_is_not_another_hour_of_the_night` |
| Un frame che non dice quanto e' durato non diventa zero ore: me lo dice a parte | `test_a_pose_without_a_time_is_not_zero_hours_of_the_night`; *una notte di cui nessun frame dice la durata non scrive zero ore* |
| I frame che aspettano una mia risposta non spariscono: me li conta in cima, e mi porta **dove si risponde** | `test_the_page_counts_the_poses_still_waiting_for_an_answer`; *dice quanti frame aspettano una risposta, e porta a Da confermare*; *chi deve dichiarare il sito non viene mandato a Da confermare* |
| Un frame a cui non posso rispondere niente non mi manda da nessuna parte | `test_a_frame_with_no_answer_to_give_does_not_send_you_anywhere`; *un frame senza risposta possibile non porta da nessuna parte* |
| Se l'app sta ancora leggendo l'archivio me lo dice, invece di lasciarmi credere che sia tutto qui | `test_the_page_says_when_the_reading_is_not_over`; *dice che la lettura non e' finita* |
| Se non ho ancora notti capisco **quale** dei motivi e', e cosa fare | `test_the_ways_of_having_no_nights_are_different_answers`; *i quattro modi di non avere notti dicono quattro cose diverse* |
| Se ho molte notti le vedo tutte, non solo le prime | `test_the_nights_list_is_paged_like_every_other`; *quando ce n e' piu' di una pagina, si vedono anche le altre* |
| La data di una notte resta quella anche se guardo l'app da un altro fuso | *resta lo stesso giorno anche guardata da un fuso a ovest* (`frontend/tests/formati.test.ts`) |
| Vedo che luna c'era quella notte, e quanto era illuminata | `test_a_night_says_which_moon_there_was`; *una notte dice che luna c'era, con quanto era illuminata* |
| Se di una notte la Luna non si puo' sapere, la riga non mi mette un trattino | `test_a_night_whose_site_has_no_timezone_says_nothing_about_the_moon`; *una notte di cui non si sa la luna non scrive un trattino muto* |
| Vedo che tempo faceva: nuvole, temperatura, vento (la casa e' [`meteo.md`](meteo.md)) | `test_the_nights_page_reads_the_weather_of_each_night_as_written`; *una notte ripresa dice com'era il cielo, e quante ore sono state serene* |
| Vedo com'erano i miei frame quella notte: stelle piu' o meno gonfie, quante ne ha trovate | nasce con la casella che misura le pose |
| Apro una notte e vedo tutto -- oggetto per oggetto, i grafici, le misure, il corredo | nasce con il modale, che e' lo stesso dell'oggetto e della libreria |

## Le decisioni

**Una notte e' una data piu' un sito.** Due postazioni nella stessa data sono **due righe**, e la
riga porta il sito: accorparle vorrebbe dire sommare le ore di due cieli diversi. E' la stessa
chiave con cui la notte nasce (`sites` + `night_date` in `backend/astrolog/schema.sql`).

**Le ore si contano in una casa sola** (`spine/counts.py`): i tre numeri escono dallo **stesso**
frammento SQL dell'Archivio, allargato dall'oggetto alla notte e all'archivio intero invece che
ricopiato. La regola -- cosa entra nella somma e cosa no -- ha la sua casa in
[`archivio.md`](archivio.md) e non si riscrive qui.

**Tutte le notti, a pagine larghe.** Non e' un flusso da scorrere: e' la tua vita osservativa, e
si guarda indietro. L'elenco esce dal backend gia' ordinato -- **dalla piu' recente** -- e si
allunga come quello dell'Archivio, senza filtri ne' ordinamenti a scelta: quelli arrivano quando la
pagina avra' i suoi controlli, ed e' la stessa riga scritta li'.

**Una riga dice cosa e con cosa**, che e' il modo in cui una notte si riconosce: gli **oggetti**
(i primi, e quanti altri) e i **filtri**, ognuno con le sue ore. I filtri stanno **in ordine di
tempo dato**, non alfabetico: e' quello che dice com'e' andata la notte, e il giorno che la veste
ne fa una barra proporzionale i numeri sono gia' quelli giusti.

**Il sito si vede anche nell'elenco.** Nel progetto di prima la vista a colonne lo toglieva
apposta -- li' una notte era **una data**, e il sito era una curiosita'. Qui una notte e' data
**piu'** sito: toglierlo metterebbe due righe identiche una sotto l'altra senza modo di
distinguerle.

**In cima, cosa c'e' in tutto.** Notti, frame e ore dell'archivio intero -- il tempo con lo stesso
pezzo che lo scrive nelle righe, o la stessa somma si leggerebbe in due modi: e' la risposta alla
domanda che si fa aprendo la pagina (*"quanto ho ripreso in vita mia?"*), e non costa una query in
piu' per riga -- e' una sola, sull'archivio.

**Le ore che non stanno in nessuna notte si dicono, e si dice dove si risponde.** Un frame fermo
non entra in nessuna notte, e se la pagina tace quelle ore sembrano non essere mai esistite:
quindi in cima c'e' **quanti sono**. Ma i cinque motivi per cui un frame resta fuori portano a
**tre gesti diversi**, e il conto si fa per gesto: una domanda di *Da confermare*, il **sito** da
dichiarare (e li' *Da confermare* non ha niente da mostrare), o **niente** -- un frame che non dice
quando e' stato ripreso non ha risposta che lo rimedi, e mandarlo da qualche parte sarebbe una
promessa vuota. Il raggruppamento lo fa il backend, perche' e' un conto, non una forma.

**E se la lettura non e' finita, lo dice.** Le notti nascono dopo che l'app ha riconosciuto cosa
c'era in ogni posa: chi apre Notti a meta' corsa vedrebbe tre notti e crederebbe di averne tre.
La riga in cima dice che sta ancora lavorando, con quante pose mancano.

**Non avere notti ha quattro motivi, e sono quattro risposte diverse.** *Non hai ancora frame* (e
allora si parte dalla scansione); *non hai detto dov'e' casa* (e allora le notti non nasceranno
**mai**, finche' non lo dici: una notte e' una data piu' un luogo); *i tuoi frame aspettano una
risposta* (ci sono, e si sbloccano da *Da confermare*); *l'app non ci e' ancora arrivata* (e allora
e' solo questione di aspettare). Uno stato vuoto che li confonde manda l'utente a sistemare la cosa
sbagliata. Il secondo copre anche il caso in cui **il sito c'e' ma il suo fuso non si riconosce**:
la frase parla di "da dove osservavi" e il gesto e' lo stesso -- si apre la scheda del sito -- e
distinguerli vorrebbe dire una quinta frase per un caso che nasce solo da coordinate storte.

**Le misure sono quelle che l'app ha preso davvero.** Oggi sono **HFD e stelle**, che il
riconoscitore misura mentre risolve la posa; FWHM, SNR, eccentricita' e fondo cielo sono colonne
che aspettano la casella che le misura, e una pagina non scrive un numero che nessuno ha misurato.
Dove la scala del cielo e' nota, l'HFD si legge in **arcosecondi**, o due notti con due telescopi
non si potrebbero confrontare.

**La Luna di una notte passata si calcola, non si conserva** -- ed e' l'eccezione dichiarata a
*"una lettura non calcola mai"* (Marco, 23/9/2026): e' astronomia pura, e non dipende da niente
che l'utente abbia scritto. Le effemeridi rispondono su un
istante qualunque, quindi la fase di una notte di due anni fa esce dallo stesso posto da cui esce
quella di stanotte, e non diventa una colonna del database: un numero che si sa derivare non si
congela, o il giorno che la formula si corregge l'archivio resta pieno di numeri vecchi. Si chiede
**in un colpo per l'intera pagina** -- quanto costa una chiamata per riga lo misura
`test_asking_the_phases_together_is_worth_it`, e che sia una sola lo tiene
`test_the_moon_of_a_whole_page_costs_one_call`.

**E si chiede alla mezzanotte della notte, nel fuso del sito** -- lo stesso istante che chiede la
barra di stanotte, da una casa sola (`clock.midnight_of`, e il perche' sta in
[`effemeridi.md`](effemeridi.md)). La mezzanotte di una notte cade il **giorno dopo** quello che le
da' il nome, e senza un fuso riconoscibile non esiste: li' la riga **tace**, invece di prendersi
Greenwich e descrivere il cielo di un altro posto.

**Il meteo invece si conserva, perche' non si sa derivare.** Che tempo facesse il 17 maggio non lo
calcola nessuna formula: lo dice un servizio, si chiede **una volta sola** e si tiene accanto alla
notte. E' una casella sua, con la sua rete e il suo "se non c'e' rete l'app funziona lo stesso".

**E il seeing non si recupera.** Quanto fosse buona l'aria quella notte lo dicono le **tue pose**,
non un modello su griglia: se il numero non e' stato misurato allora, oggi non esiste piu'. La
cosa piu' vicina e' l'HFD delle pose, che l'app misura gia'; il numero che i servizi meteo
chiamano "seeing" e' una previsione, e dove comparisse andrebbe scritto che viene da un modello.

**A mani vuote e su tre bersagli.** I numeri arrivano dall'API gia' fatti -- ore sommate, date gia'
nel fuso del sito -- e il layout non porta logica: la stessa pagina reggera' il telefono senza
essere riscritta, ed e' la regola con cui nasce ogni superficie.

## Cosa non fa ancora, e con cosa arrivera'

La pagina e' il **riepilogo delle notti passate**, e ci arriva per pezzi: l'elenco e la Luna ci
sono, e il meteo di ogni notte anche; restano le misure dei frame. Ogni riga *nasce con* qui sopra dice quale pezzo la
porta; finche' non c'e', la pagina **tace invece di ripiegare** su un numero inventato.

**Il modale di una notte arriva per ultimo, con gli altri due.** Aprire una notte, aprire un
oggetto e aprire una voce della libreria mostrano in fondo le stesse cose -- i grafici, le misure,
le statistiche -- quindi e' **un** modale, e si fa quando ci sono i dati che deve mostrare
(scelta di Marco, 20/9/2026: prima tutte le pagine, i modali alla fine). Qui intanto ogni notte
esce con la sua **chiave stabile**, cosi' il giorno che il modale nasce ha gia' come chiamarla.

Restano fuori per scelta, non per mancanza: **anteprime**, **note scritte a mano** e il **voto**
della notte -- nel progetto di prima erano stati provati e scartati, e la ragione vale ancora: una
notte si giudica dalle sue ore e dalle sue misure, non da una stella su cinque. E niente
**ricerca, faccette o ordinamenti a scelta**: come l'Archivio, arrivano quando la pagina avra' i
suoi controlli, tutti insieme e non uno per volta.
