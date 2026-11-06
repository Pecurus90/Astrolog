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
| Anche in mare aperto il sito ha un fuso, quello nautico, e le notti nascono in quel fuso | `test_an_empty_field_says_why_it_is_empty`, `test_on_the_open_sea_the_night_follows_the_nautical_zone` |
| L'altitudine si compila da sola dalle coordinate; se non ci riesce resta vuota e me lo dice, non mette zero | `test_site_elevation_or_nothing` |
| Del cielo dico quello che so: lo misuro con lo strumento, lo faccio chiedere al servizio, o scelgo il cielo dall'elenco dei nove | `test_site_sky_three_ways` |
| Vedo la classe di Bortle **e** la misura accanto, e l'app non finge che la conversione sia una legge | `test_bortle_from_sky_brightness`, `test_the_bortle_is_derived_and_never_stored` |
| Le mie foto misurano il cielo del sito: l'app mi propone il Bortle che dicono, lo adotto o lo lascio, e se lo lascio non me lo ripropone finche' la classe non cambia; se le notti non bastano mi dice quante ne ha e in quanti mesi | `test_the_good_frames_give_the_site_its_sky`, `test_a_year_of_nights_gives_back_the_level_under_the_season`, `test_too_few_data_say_how_many_nights_in_how_many_months`, `test_use_writes_the_measure_with_its_nights`, `test_dismissed_it_comes_back_only_when_the_class_changes`, `test_a_site_without_a_sky_is_proposed_one` |
| Ho piu' siti: li aggiungo tutti e dico qual e' quello di casa | `test_sites_many_and_one_default` |
| Un sito che ha gia' delle notti non lo perdo per sbaglio: l'app si rifiuta e mi dice quante | `test_site_with_nights_is_not_deleted` |
| Se cambio il sito di casa, le notti che l'app aveva attribuito da sola vengono con me; quelle che ho dichiarato io restano dove le ho messe | `test_moving_home_takes_along_the_nights_the_app_assigned`, `test_a_night_that_would_collide_stays_where_it_is` |
| Il primo avvio mi chiede Nome, Sito, Tema, Cartelle e Seeing (Meteoblue), tutti facoltativi, e poi si toglie di mezzo; un passo saltato resta segnato «saltato», e la chiusura dice se la scansione non e' partita; se lo salto l'app funziona lo stesso, e non me lo richiede piu' (Tema dal 24/10/2026, Marco: Tema e «saltato» da costruire) | `test_wizard_steps_and_the_stamp`; a schermo *col timbro l app mostra se stessa e non richiede niente*, *ogni campo e ogni bottone dei quattro passi passa dal suo mattone*, *saltare TIMBRA: domani l app non rifa le stesse domande*, *si completa, e completare timbra come saltare*, *e dopo il timbro il primo avvio si toglie davvero di mezzo* |
| Se il riconoscitore del cielo non ce l'ho, me lo dice **prima** di farmi aspettare una lettura che non riconoscera' niente -- e se ce l'ho non me ne parla nemmeno | `test_the_app_says_when_the_solver_is_missing`; a schermo *se manca, il passo c e e dice cosa ci perdi*, *con tutto a posto i passi restano quattro* |
| Dico io dove sta il mio ASTAP e l'app usa quello, anche se ne troverebbe un altro per conto suo; se scrivo un percorso sbagliato me lo dice subito | `test_the_declared_path_wins_over_the_automatic_search`, `test_the_run_launches_the_path_written_in_settings`, `test_writing_the_path_turns_the_warning_off` |
| Vedo **dove** l'app prende ASTAP e da cosa l'ha dedotto, cosi' posso dire "no, non quello"; e se voglio glielo faccio cercare, e usa cio' che ha trovato solo se glielo dico | `test_the_route_says_where_the_solver_is_and_from_which_channel`, `test_looking_for_it_proposes_without_writing`, `test_looking_for_it_ignores_what_is_declared`; a schermo *dice dove sta, e da cosa l app l ha dedotto*, *Cerca ASTAP propone, e non scrive niente finche' non si adotta* |
| Se ad ASTAP manca il catalogo stellare me lo dice **prima**, invece di lasciarmi scoprire da una scansione che non riconosce niente; e se ASTAP non ce l'ho affatto, non mi parla anche del suo catalogo | `test_astap_without_its_catalogue_is_a_thing_that_is_missing`, `test_without_astap_nobody_complains_about_its_catalogue`, `test_the_star_databases_are_the_ones_next_to_the_program` |
| Senza un sito l'app cataloga e cerca, ma **non fa le notti**, e lo dice invece di inventarne uno | `test_no_site_no_nights_and_it_says_so` |
| Il mio nome resta scritto, se lo scrivo | `test_settings_user_name` |
| Dalla ricerca apro un sito (`/impostazioni/sito?sito=<id>`): la sua riga e' segnata e in vista, e correggerlo resta un gesto | *con ?sito= la riga di quel sito e' segnata, e la scheda di correzione resta chiusa* |

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
cinque le architetture. In mare aperto vale il **fuso nautico** che la libreria da' (`Etc/GMT+9`
e simili, fasce di 15 gradi): e' una convenzione vera, e la notte da mezzogiorno a mezzogiorno
ci funziona. Il campo resta vuoto col suo motivo (`site_no_timezone`) solo dove un fuso non si
riconosce, e non si inventa.

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
cosi' due siti si confrontano davvero (la quarta, il Bortle misurato sui frame e adottato, in
fondo). Un numero e' credibile da 7 a 23 (Unihedron, SQM-LU:
"about 7 (brightest) to 23 (darkest)"); la luminanza del servizio diventa magnitudini con
Garstang, V = 12,603 - 2,5 log10 L, cosi' i 174 ucd/m2 del cielo naturale di Falchi tornano 22,00
(ADR 0035).

**La classe di Bortle si DERIVA, non si memorizza.** E' una scala descrittiva, nata per
l'occhio umano, e non ha confini ufficiali in luminosita': Bortle non ne diede mai. In giro
circolano **due famiglie** di conversioni che su uno stesso cielo differiscono fino a due
classi. L'app usa **una sola tabella, quella di ASTAP** (`bortle()` in `unit_sqm.pas`, da
ClearDarkSky; Marco, 23/10/2026; ADR 0033 R2, 0035), perche' lo SQM dei frame si misura col metodo
di ASTAP: una classe vale da sopra il suo pavimento, 1 = 21,99 · 2 = 21,89 · 3 = 21,69 · 4 = 21,25
· 5 = 19,50 · 6 = 18,94 · 7 = 18,38 · 8 = 17,80 · 9 sotto; la 4,5 di ASTAP (sopra 20,49) si
legge 5, perche' il nostro numero non sia mai piu' generoso della fonte. La classe 1 si rappresenta
con 22,00, il cielo naturale (Falchi 2016). Il codice usa ancora la tabella vecchia finche' il
foglio di Design non porta i pavimenti nuovi (Issue #28). Sta in un posto solo con la sua avvertenza,
e a schermo **compare accanto alla misura** -- "Bortle 4 (21.4)" -- tranne nei due posti dove
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
Completare e saltare scrivono lo stesso timbro. **Il primo avvio non si riapre** (Marco,
21/10/2026): ognuna delle sue cose -- nome, sito, tema, cartelle, chiave, ASTAP -- si cambia nelle
Impostazioni; il nome non c'e' ancora (Issue #19). **Completare passa dalla chiusura** (Marco, 9/10/2026): timbrato, l'app mostra cosa e'
stato dato, letto dal database e non dalla memoria della pagina -- nome, sito, cartelle e se la
scansione e' partita, chiave del seeing -- e si entra
con "Apri AstroLog"; saltare entra subito. Una riga di cui la lettura e' fallita (sito, cartelle)
si tace: "Nessuna" a chi le ha date sarebbe falso. La chiusura resta finche' non si preme il
comando, anche se le impostazioni si rileggono col timbro gia' scritto: lo ricorda `App.tsx`.

**A schermo il primo avvio e' un cancelletto, non un indirizzo** (14/9/2026): senza il timbro
l'app mostra le sue domande, col timbro mostra se stessa -- non c'e' una pagina `/wizard` dove
si possa atterrare. Il router c'e' (nato con Da confermare), ma il primo avvio resta fuori dalle
rotte: senza il timbro l'app non monta nessuna pagina. Sta qui e non nel brief
perche' un brief si sostituisce a ogni fetta, e questa decisione deve sopravvivergli.

**Il passo del riconoscitore compare solo a chi serve, e l'app non scarica programmi.** Senza ASTAP
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
quando sono entrati, e le risposte sui frame senza nome che la portano nella chiave (`spine/home_nights.py`,
il contratto in `domini/spina-scan.md`). Un cambio dei siti rimette in coda i frame fermi perche' il posto non si sapeva, ma solo quelli che quel cambio puo'
sbloccare: entro 1 km da un sito nuovo, spostato o diventato casa; con una risposta che nomina un
sito rinominato; fermi perche' casa non c'era. **Rinominare non richiede:** le risposte che nominano
il sito seguono il nome nuovo, perche' e' un'altra parola e non un altro posto (Marco, 25/10/2026;
`test_renaming_a_site_keeps_the_answers_that_name_it`); a richiedere e' solo lo spostamento. Ancora:
fermi perche' casa non c'era, quando nasce; e sempre quelli fermi per un sito
senza fuso, che sono pochi e che uno spostamento o una cancellazione possono sbloccare anche senza
coordinate. Gli altri tornerebbero uguali. Spostare un sito rifa' anche le notti che l'app gli aveva
dato
(`test_declaring_a_site_puts_the_waiting_frames_back_in_the_queue`,
`test_a_change_that_cannot_help_puts_nothing_back_in_the_queue`,
`test_renaming_a_site_to_the_name_an_answer_says_puts_those_frames_back`,
`test_moving_a_site_puts_its_nights_back_in_the_queue`). Una notte che sul nuovo sito esisterebbe gia' (stessa data) **resta dov'e'**:
il database non ne ammette due uguali, e far fallire il trasloco per un'attribuzione dubbia
sarebbe peggio -- i frame non si perdono comunque.

**Il Bortle del sito dalle misure** (Marco, 18/10/2026; ADR 0022, 0039; `pipeline/site_sky.py`,
tabella `site_sky_measures`). L'app **propone**, l'utente sceglie; mai un cambio da sola.
- **Frame che contano**: quelli con lo SQM dai pixel (mono col filtro L, a colori: `SQM_SHOTS`,
  quindi un filtro risposto dopo cambia l'insieme) **e col bias della camera** (senza, lo scarto
  arriva a 0,18 mag, e una classe e' larga 0,5-1 mag); Sole sotto -18° e Luna sotto -5° ("Sun
  below -18° and Moon below -5°", Bara et al. 2021, arXiv 2104.10616); cielo inquadrato sopra 30°,
  contro il bagliore delle citta' che lo SQM non corregge. Nessuna fonte da' un'altezza minima (le
  misure pubbliche sono allo zenit): 30° e' la massa d'aria 2, l'"esteso" dell'oggetto basso di
  ADR 0039, perche' il fondo cielo e' esteso.
- **Di quale sito**: quello a cui va la sua notte, con la stessa regola (`site_of.site_at`, sotto
  tutte e due le pipeline: Marco, 5/11/2026, "voglio sia pulito"): casa entro 1 km, poi la
  risposta dell'utente per quelle coordinate, poi il sito piu' vicino entro 1 km; le coordinate
  sono quelle della scheda che ha dato Sole e Luna. Fuori da tutti: non conta, e nessun sito nasce.
  Un sito senza fuso non ha notti, quindi non ha misura.
- **Numero**: una mediana per notte (da mezzogiorno a mezzogiorno nel fuso del sito).
- **Minimo** (ADR 0039): notti in almeno 4 mesi dei 12 di calendario che finiscono con l'**ultima
  notte misurata** (Marco, 5/11/2026: un archivio vecchio scansionato oggi propone lo stesso; la
  risposta porta prima e ultima notte), nessun buco oltre 3 mesi, contato in giro sui 12: il
  fit e' periodico, e dicembre tocca gennaio.
- **Livello annuo**: il cielo ha stagioni (Posch et al. 2018: 0,5-1,5 mag fra estate e inverno, ma
  medie mensili e nessun fit). Il modello e' quello di Shah et al. 2025 (arXiv 2507.11343, App. F,
  "m(t) = m0 + A sin[2π(t − t0)] + mt") **senza il termine lineare**: 12 mesi non misurano una
  tendenza (Posch: "only measurable after more than two years"). Minimi quadrati di livello e
  onda annua sulle mediane delle notti, poi la **mediana delle notti tolta l'onda**: una notte
  nuvolosa sopra la citta' non sposta il livello.
- **Quando**: lo riscrive chi cambia cio' da cui viene. Dentro la pipeline nella stessa
  transazione: la fine di un giro, un bias dichiarato, un filtro risposto. Fuori, dove la vecchia
  non puo' chiamare la nuova (ADR 0030, una porta sola): ogni scrittura dei siti, la risposta "queste
  coordinate sono quel sito", il ripristino e l'import del backup **chiedono** il ricalcolo al thread
  della pipeline (`Behind.refresh_sky`), che lo fa subito dopo, anche dopo uno Stop. Per un istante
  la pagina puo' leggere la misura di prima; la lettura legge e basta. Si propone quando la classe misurata e' diversa da quella del sito, **anche quando il
  sito il cielo non ce l'ha** (Marco, 5/11/2026: e' il caso in cui serve di piu'); dopo «Lascia»
  (`site_sky_dismissed`, va nel backup col sito) di nuovo solo se la classe misurata cambia.
- **«Usa»** scrive la misura nel sito con la provenienza `frames` e le sue notti (`sky_nights`):
  una quarta strada accanto alle tre, perche' sotto il Bortle si legge «misurato su {n} notti» e
  non «scritto a mano». Spostare il sito la svuota, come quella del servizio: era di quel posto, e
  il posto nuovo propone la sua. Correggerla a mano la riporta a `measured` o `scale`.
- **Parole** (Marco): «Le misure di {sito} dicono Bortle {b} (SQM {sqm}, {n} notti). Nel sito
  c'e' Bortle {b0}.» · «Usa Bortle {b}» · «Lascia Bortle {b0}»; sito senza cielo (Marco,
  5/11/2026): la prima frase sola, e «Usa Bortle {b}» · «Lascia vuoto». Sotto il Bortle del sito:
  «misurato su {n} notti» / «scritto a mano». Dati scarsi: «Servono notti in almeno 4 mesi, senza
  buchi di oltre 3: finora {n} notti in {m} mesi.» (Marco, 24/10/2026). L'API manda codici e
  numeri (`measured` in `SiteOut`); le frasi entrano con la pagina (fase 5).
- **Oggi tace per tutti**: un bias si dichiara solo da codice finche' il setup della pipeline non
  arriva a schermo (passo 40, `domini/misure.md`), quindi nessun frame conta ancora.
- Il giudizio di un frame «come / piu' chiaro del Bortle del sito» resta: una classe e' larga, e
  un frame che esce dal basso ha Luna, foschia o luci.

## Cosa NON fa

Non crea siti da solo. Non inventa un'altitudine, un fuso o un cielo. Non mostra un Bortle
senza la misura accanto. Non chiede la chiave del servizio per far partire l'app. Non scarica, non installa e non
lancia programmi di sua iniziativa: dice dove si prendono. L'orizzonte
non e' di questa casella: si importa in Impostazioni, uno per sito (`planner.md`, *L'orizzonte del sito*).
