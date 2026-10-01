# Il sito -- contratto

Il sito e' **il posto da cui si osserva**. Da lui dipendono la notte (che va da mezzogiorno a
mezzogiorno **nel suo fuso**), il buio, la Luna e il meteo: e' il primo dato che l'app chiede,
ed e' il primo passo utile del wizard. Lo schema sta in `backend/astrolog/schema.sql`; le
parole in [`glossario.md`](glossario.md). Le decisioni ereditate da old/ che lo riguardano
sono state assorbite qui e tolte da [`ereditato.md`](ereditato.md).

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Dico da dove osservo scrivendo il nome del posto, e l'app trova le coordinate; se non c'e' rete le scrivo a mano, e funziona uguale | `test_site_search_by_name`, `test_site_manual_coordinates` |
| Il fuso orario non me lo chiede: lo sa dalle coordinate, e lo sa anche senza rete | `test_site_timezone_offline` |
| L'altitudine si compila da sola dalle coordinate; se non ci riesce resta vuota e me lo dice, non mette zero | `test_site_elevation_or_nothing` |
| Del cielo dico quello che so: lo misuro con lo strumento, lo faccio chiedere al servizio, o scelgo il cielo dall'elenco dei nove | `test_site_sky_three_ways` |
| Vedo la classe di Bortle **e** la misura accanto, e l'app non finge che la conversione sia una legge | `test_bortle_from_sky_brightness`, `test_the_bortle_is_derived_and_never_stored` |
| Ho piu' siti: li aggiungo tutti e dico qual e' quello di casa | `test_sites_many_and_one_default` |
| Un sito che ha gia' delle notti non lo perdo per sbaglio: l'app si rifiuta e mi dice quante | `test_site_with_nights_is_not_deleted` |
| Se cambio il sito di casa, le notti che l'app aveva attribuito da sola vengono con me; quelle che ho dichiarato io restano dove le ho messe | `test_moving_home_takes_along_the_nights_the_app_assigned`, `test_a_night_that_would_collide_stays_where_it_is` |
| Il primo avvio mi chiede quattro cose -- l'ultima, la chiave Meteoblue, e' facoltativa -- e poi si toglie di mezzo; se lo salto l'app funziona lo stesso, e non me lo richiede piu' | `test_wizard_steps_and_the_stamp`; a schermo `frontend/tests/wizard.test.tsx` (le domande poste davvero, il cancelletto, e che saltare **e** completare timbrino) |
| Se il riconoscitore del cielo non ce l'ho, me lo dice **prima** di farmi aspettare una lettura che non riconoscera' niente -- e se ce l'ho non me ne parla nemmeno | `test_the_app_says_when_the_solver_is_missing`; a schermo `frontend/tests/wizard-solver.test.tsx` |
| Dico io dove sta il mio ASTAP e l'app usa quello, anche se ne troverebbe un altro per conto suo; se scrivo un percorso sbagliato me lo dice subito | `test_the_declared_path_wins_over_the_automatic_search`, `test_the_run_launches_the_path_written_in_settings`, `test_writing_the_path_turns_the_warning_off` |
| Vedo **dove** l'app prende ASTAP e da cosa l'ha dedotto, cosi' posso dire "no, non quello"; e se voglio glielo faccio cercare, e usa cio' che ha trovato solo se glielo dico | `test_the_route_says_where_the_solver_is_and_from_which_channel`, `test_looking_for_it_proposes_without_writing`, `test_looking_for_it_ignores_what_is_declared`; a schermo `frontend/tests/impostazioni-riconoscitore.test.tsx` |
| Se ad ASTAP manca il catalogo stellare me lo dice **prima**, invece di lasciarmi scoprire da una scansione che non riconosce niente; e se ASTAP non ce l'ho affatto, non mi parla anche del suo catalogo | `test_astap_without_its_catalogue_is_a_thing_that_is_missing`, `test_without_astap_nobody_complains_about_its_catalogue`, `test_the_star_databases_are_the_ones_next_to_the_program` |
| Senza un sito l'app cataloga e cerca, ma **non fa le notti**, e lo dice invece di inventarne uno | `test_no_site_no_nights_and_it_says_so` |
| Il mio nome resta scritto, se lo scrivo | `test_settings_user_name` |

## Le decisioni

**Il sito e' dichiarato, sempre.** Le coordinate scritte negli header sono un **indizio**, mai
un'assegnazione: alimenteranno un avviso "rivedi i siti", non creano niente. Un sito nato
da solo sarebbe un dato che nessuno ha detto, e i nomi di ripiego ("Sito sconosciuto") non
entrano nel database: l'assenza si dice a schermo.

**Il sito e' obbligatorio per le notti, non per partire.** Il wizard si salta sempre, senza
conferme: si possono registrare cartelle, scansionare, catalogare. Ma una notte e' *data-notte
+ sito*, quindi senza un sito le notti non nascono, e l'app lo dice con un motivo
(`no_active_site`) invece di indovinare un fuso. Due siti nella stessa data sono due notti.
Di `missing` (`GET /settings`) il primo avvio guarda solo il riconoscitore, programma e
catalogo: per il sito un avviso in piu' non si aggiunge, perche' il sito lo chiede gia' il
primo avvio.

**Il fuso si ricava dalle coordinate, offline, mai dalla longitudine.** I confini dei fusi
sono politici e frastagliati: un meridiano darebbe la risposta sbagliata a pochi chilometri da
casa. Si usa una libreria coi confini veri, che lavora senza rete e ha le ruote per tutte e
cinque le architetture. Dove le coordinate non cadono in nessun fuso (mare aperto) il campo
resta vuoto col suo motivo (`site_no_timezone`), e non si inventa.

**Il nome di un fuso si valida per appartenenza** all'elenco ufficiale, non provando ad
aprirlo: "Europe" e "Europe/Roma" sono sbagliati in due modi diversi e falliscono con
eccezioni diverse. Portata da old/ con la sua prova sui cinque refusi.

**L'altitudine si ricava dalle coordinate** da un servizio pubblico senza chiave (modello di
terreno europeo a 90 metri, che chiede solo di essere citato). Se la rete non c'e' o il
servizio non risponde, il campo resta **vuoto**: "non fornita", mai 0 m -- lo zero e'
un'altitudine vera, quella del mare.

**Dell'altitudine si registra la provenienza**, come della luminosita': scritta da chi c'e'
stato (`declared`) o chiesta al servizio (`service`). Serve per una cosa sola, ma decisiva:
**spostando il sito si rifa' solo cio' che dalle coordinate veniva**. Quella dichiarata resta
la parola dell'utente; quella del servizio si richiede per il posto nuovo e, se il servizio
tace, si svuota col suo motivo. Senza la provenienza, 1.000 metri rimasti attaccati a
coordinate nuove sarebbero indistinguibili da una misura, e nessuno saprebbe piu' che sono
vecchi. Vale anche il verso opposto: **un campo mandato a vuoto e' cancellato**, non
ricompilato dal servizio -- lo stesso gesto deve voler dire la stessa cosa su ogni campo.

**Del cielo si salva la LUMINOSITA'**, in magnitudini per arcosecondo quadrato, con accanto
**come la si sa**: misurata con lo strumento, chiesta al servizio, o scelta sulla scala.
La misura vince sulla stima, e la stima su una scelta a occhio. Tre strade, un numero solo:
cosi' due siti si confrontano davvero.

**La classe di Bortle si DERIVA, non si memorizza.** E' una scala descrittiva, nata per
l'occhio umano, e non ha confini ufficiali in luminosita': Bortle non ne diede mai. In giro
circolano **due famiglie** di conversioni che su uno stesso cielo differiscono fino a due
classi. L'app usa quella dei **siti di astrofotografia** (Wikipedia, AstroBackyard, Telescope
Live), non quella piu' severa del mondo degli strumenti SQM, per una ragione sola: e' il
numero con cui l'utente confrontera' il nostro, e un 21,8 chiamato "Bortle 3" quando ovunque
si legge "Bortle 1" farebbe sembrare rotta l'app. Sta in un posto solo con la sua avvertenza,
e a schermo **compare accanto alla misura** -- "Bortle 4 (20,8)" -- tranne nei due posti dove
la misura non c'e' o non ci sta: il primo avvio, dove si sceglie, e il piede della barra. Chi sceglie il cielo dalla
scala fa il percorso inverso, e ritrova la stessa classe.

**Il cielo si dichiara in due posti, e sono gli stessi due di ogni altra cosa del sito**
(Marco, 19/9/2026): al **primo avvio**, nel passo *Da dove osservi*, e nella **scheda del luogo**,
dove si torna a correggerlo. Non e' una doppia casa del dato -- il numero salvato resta uno solo,
`sky_sqm` con la sua provenienza -- sono due porte sulla stessa stanza: chi installa lo dice
subito, chi lo scopre dopo (misurandolo, o cambiando posto) non deve rifare il primo avvio per
cambiarlo. Nel primo avvio la strada offerta e' **la scala**: scegli il cielo fra i nove, e l'app
ne ricava la misura -- chiedere una magnitudine per arcosecondo quadrato a chi ha appena
installato vorrebbe dire fermarlo li'.

**Il servizio che stima il cielo vuole una chiave personale**, gratuita, chiesta con una
email all'autore. Non sta nel wizard: al primo avvio nessuno deve scrivere a uno sconosciuto
per andare avanti. Vive in Impostazioni, e quando c'e' compare il pulsante "chiedilo tu"
accanto al sito. Senza chiave l'app funziona: si misura o si sceglie.

**La ricerca del posto per nome passa da un servizio pubblico**, con l'identificazione che la
sua policy pretende e una richiesta al secondo. **La strada manuale e' sempre aperta**, non
solo quando qualcosa va storto: un sito buio puo' non avere rete, ed e' proprio dove si
osserva.

**Cio' che viene dalla rete e' sostituibile.** Le chiamate esterne si passano come argomento,
cosi' i test usano un finto locale e la suite non tocca internet: un test che chiama un
servizio vero e' un test che fallisce il giorno che il servizio cambia.

**Il primo avvio e' un timbro, non un'euristica.** "L'ho gia' visto" e' una data scritta in
Impostazioni: l'euristica "sembra vuoto" tornerebbe vera mesi dopo, dopo un azzeramento.
Completare e saltare scrivono lo stesso timbro; riaprire il wizard dalle Impostazioni non lo
riscrive.

**A schermo il primo avvio e' un cancelletto, non un indirizzo** (14/9/2026): senza il timbro
l'app mostra le sue domande, col timbro mostra se stessa -- non c'e' una pagina `/wizard` dove
si possa atterrare. Il router c'e' (nato con Da confermare), ma il primo avvio resta fuori dalle
rotte: senza il timbro l'app non monta nessuna pagina. Sta qui e non nel brief
perche' un brief si sostituisce a ogni fetta, e questa decisione deve sopravvivergli.

**Il passo del riconoscitore compare solo a chi serve, e l'app non scarica niente.** Senza ASTAP
l'archivio si costruisce lo stesso -- i file entrano, i nomi si ordinano, le ore si contano --
ma **non si sa cosa hai ripreso**, e scoprirlo a scansione finita e' mezz'ora buttata: per
questo `GET /settings` dichiara `no_solver` e il primo avvio aggiunge un passo. Chi il solver
ce l'ha non lo vede mai. Il passo da' **l'indirizzo** da cui prenderlo e il campo per dire dove
sta: scaricare o eseguire un programma senza che l'utente lo chieda e' l'unica cosa che l'app
non fa. Il percorso dichiarato **vince** sulla ricerca automatica e sulla variabile d'ambiente
(che sul NAS la mette chi gestisce la macchina, e non deve zittire chi guarda lo schermo); se
non esiste vale **niente**, mai un ripiego di nascosto, e il passo lo dice li' per li' con la
risposta della scrittura. Quanti passi sono si decide **entrando**: trovato il solver, il
quarto resta al suo posto fino alla fine, invece di sparire sotto i piedi di chi ci sta
camminando dentro.

**Fuori dal primo avvio la stessa cosa si guarda sempre, e con un dettaglio in piu': da quale dei
quattro canali arriva** -- dichiarato, variabile d'ambiente, PATH di sistema, posto noto
d'installazione. Il canale serve perche' *"trovato"* da solo **non si puo' smentire**: la ricerca
automatica sbaglia proprio quando trova qualcosa (un ASTAP vecchio rimasto nel PATH, quello di un
altro utente in un posto noto), e chi guarda deve poter dire "no, non quello". Per la stessa
ragione un percorso dichiarato e sbagliato **resta a schermo** invece di sparire: e' l'unica cosa
che si puo' correggere. E la ricerca su richiesta (*cercalo tu*) **propone e basta** -- adottarla e'
un gesto dell'utente, perche' sovrascrivere di nascosto un percorso scritto a mano toglierebbe
l'unica via d'uscita da una ricerca che sbaglia.

**Il programma non basta: senza il suo catalogo stellare ASTAP parte e non riconosce niente.** E'
un download a parte -- dai 101 MB del D05 a 1,25 GB del D80 -- e porta esattamente
dove porta l'assenza del programma -- una scansione che torna a mani vuote. Per questo sta fra le
cose che **mancano** (`no_star_database`) accanto al sito e al solver, e per questo il passo del
riconoscitore nel primo avvio compare **anche** a chi ASTAP ce l'ha e il catalogo no: li' pero' il percorso non
si chiede, perche' e' gia' giusto. Dove cercarlo lo dice l'autore -- *"they can be placed anywhere
as long as all files are in the same directory"* (hnsky.org/astap.htm) -- cioe' **accanto
all'eseguibile e solo li'**, sciogliendo prima un eventuale collegamento -- il catalogo sta dove
il programma sta davvero, non dove punta la scorciatoia che l'ha trovato. Si
riconosce dal nome (`d80_0101.1476`) e non dall'estensione, che cambia col formato.

**Guardare anche nelle cartelle d'installazione note sembra piu' generoso e invece mente**: su una
macchina che ha ASTAP installato, un eseguibile indicato altrove risulterebbe col catalogo di un
altro programma -- e l'app direbbe "tutto a posto" proprio nel caso che questa domanda esiste per
prendere (visto dal vivo). Il prezzo si dichiara: chi tiene il catalogo in un terzo posto si sente
dire che manca. Un "ti manca" di troppo si corregge guardando; un "ce l'hai" falso si scopre a
lettura finita.

Si **guarda**, non si chiede: interrogare ASTAP vorrebbe dire lanciarlo, e questa risposta la da'
una lettura. E a chi il programma non ce l'ha il catalogo non si nomina affatto: due allarmi per un
problema solo mandano a cercare due cose.

**Un sito con notti non si cancella** (409, con quante notti lo tengono). Cambiare il sito
predefinito **porta con se' i frame senza coordinate che l'app aveva dato alla casa vecchia**: le
loro notti si rifanno, e quelli con le coordinate della casa vecchia ci tornano, perche' le
coordinate dicono dove eri. Le notti dichiarate, e quelle che l'app ha dato a un altro sito, nessuno
le tocca
(`test_moving_home_leaves_the_nights_of_the_other_sites_alone`). Ogni cambio del fuso di casa --
anche la prima casa, e anche casa tolta -- riscrive la notte che i frame senza coordinate portano da
quando sono entrati, e le risposte per gruppo che la portano nella chiave (`spine/home_nights.py`,
il contratto in `domini/spina.md`). Un cambio dei siti rimette in coda i frame fermi perche' il posto non si sapeva, ma solo quelli che quel cambio puo'
sbloccare: entro 1 km da un sito nuovo, spostato o diventato casa; con una risposta che nomina un
sito rinominato; fermi perche' casa non c'era, quando nasce; e sempre quelli fermi per un sito
senza fuso, che sono pochi e che uno spostamento o una cancellazione possono sbloccare anche senza
coordinate. Gli altri tornerebbero uguali. Spostare un sito rifa' anche le notti che l'app gli aveva
dato
(`test_declaring_a_site_puts_the_waiting_frames_back_in_the_queue`,
`test_a_change_that_cannot_help_puts_nothing_back_in_the_queue`,
`test_renaming_a_site_to_the_name_an_answer_says_puts_those_frames_back`,
`test_moving_a_site_puts_its_nights_back_in_the_queue`). Una notte che sul nuovo sito esisterebbe gia' (stessa data) **resta dov'e'**:
il database non ne ammette due uguali, e far fallire il trasloco per un'attribuzione dubbia
sarebbe peggio -- i frame non si perdono comunque.

## Cosa NON fa

Non crea siti da solo. Non inventa un'altitudine, un fuso o un cielo. Non mostra un Bortle
senza la misura accanto. Non chiede la chiave del servizio per far partire l'app. Non scarica, non installa e non
lancia programmi di sua iniziativa: dice dove si prendono. L'orizzonte
non e' di questa casella: nasce col Planner, che e' l'unico che lo legge.
