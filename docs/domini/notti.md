# Le Notti -- contratto

**Quando hai ripreso**, e cosa hai fatto quella notte. L'Archivio racconta gli oggetti; questa
pagina racconta le **notti**, una per una: e' il modo in cui un astrofotografo si ricorda la vita
osservativa: *"la notte del 17 maggio, a Cima Ekar, M 51 e M 101, sei ore".* Le parole vengono da
[`glossario.md`](glossario.md); cos'e' una notte e chi la scrive sta in [`spina-scan.md`](spina-scan.md) e [`spina-group.md`](spina-group.md);
dove sta la voce nella barra, in [`navigazione.md`](navigazione.md); come si contano le ore e
perche' le copie non valgono, in [`archivio.md`](archivio.md), che ne e' la casa; il cielo di una
notte, in [`meteo.md`](meteo.md).

La pagina e' la tavola di Claude Design `handoff/design/pagine/Notti.dc.html` e `Notti stati`,
**v76** (7/11/2026): la tavola e' la specifica, aspetto e funzioni (Marco, 27/10/2026). Le
decisioni di Design che la reggono sono in `handoff/design/docs/DECISIONI.md`, v59, v60, v65.

## Cosa chiede l'utente

Le prove del backend stanno in `backend/tests/test_api_nights.py` e nei file accanto
(`test_api_nights_*.py`); quelle del frontend si chiamano col loro titolo e stanno in
`frontend/tests/notti.test.tsx`.

| richiesta | prova |
|---|---|
| Apro Notti e vedo **una notte grande**, la piu' recente: giorno, sito, ore, frame, cielo, Luna, oggetti e filtri | `test_the_page_lists_the_nights_you_shot`, `test_a_night_says_where_you_were_and_what_you_shot`; *la notte piu' recente e' la protagonista* |
| Sopra, le **ultime 7 notti** in una striscia; tocco una e diventa la protagonista | *la striscia porta le ultime sette notti, e una toccata diventa la protagonista* |
| Accanto, il **calendario del mese** della notte: un segno per notte con l'esito del cielo, le ore del mese, quante notti e quante buone; vado ai mesi prima e dopo, dal primo con notti a oggi | `test_the_month_has_a_sign_per_night_and_its_totals`, `test_the_months_go_from_the_first_night_to_today`; *il calendario va di mese in mese* |
| Sotto, **tutte le notti a confronto**, per mese, con le ore e le notti di ogni mese; 20 alla volta, e "Carica altre" | `test_the_nights_list_is_paged_like_every_other`, `test_a_month_says_its_nights_and_hours`; *quando ce n'e' piu' di una pagina, si vedono anche le altre* |
| Cerco fra le notti coi **criteri**: oggetto, anno, sito, setup, filtri, costellazione, cielo; ogni scelta mi dice quante notti restano | `test_the_criteria_count_with_the_other_choices_applied`, `test_within_a_criterion_any_across_all`, `test_an_object_is_found_by_name_and_common_name`; *i criteri dicono quante notti restano* |
| Nessuna notte coi criteri scelti: me lo dice, e tolgo i criteri | *nessuna notte con questi criteri* |
| Accanto alla data vedo anche che giorno della settimana era | *accanto alla data c'e' il giorno della settimana* |
| Accanto al sito vedo da dove viene: dalle coordinate nei frame, il sito di casa, o la mia risposta | `test_a_night_says_where_its_site_comes_from`; *il sito dice da dove viene* |
| Vedo con che filtri ho ripreso quella notte, e quanto ho dato a ciascuno | `test_a_night_says_which_filters_and_how_long_each_one_ran`, `test_a_night_or_an_object_lists_its_filters_in_the_one_order` (`backend/tests/test_filter_order.py`); *una notte dice i filtri, nell'ordine dei filtri* |
| In fondo vedo quante notti, oggetti, frame e ore ho in tutto, e quanti frame senza durata | `test_the_page_opens_with_what_the_whole_archive_holds`; *in fondo c'e' tutto l'archivio* |
| Due siti nella stessa data restano due notti, non una | `test_two_sites_on_the_same_date_stay_two_nights` |
| Le copie calibrate che tengo accanto agli originali non mi raddoppiano le ore | `test_a_rewritten_copy_is_not_another_hour_of_the_night` |
| Un frame che non dice quanto e' durato non diventa zero ore: me lo dice a parte | `test_a_pose_without_a_time_is_not_zero_hours_of_the_night`; *una notte di cui nessun frame dice la durata non scrive zero ore* |
| I frame **fuori da ogni notte** non spariscono: in fondo, per motivo, e ognuno mi porta **dove si risponde** | `test_the_page_counts_the_poses_still_waiting_for_an_answer`, `test_a_frame_without_a_date_is_answered_in_review`; *ogni voce fuori da ogni notte porta a Da confermare* |
| L'anno fino a oggi, un quadretto per giorno (nella **Dashboard**, che usa la stessa rotta) | `test_the_year_counts_its_nights_and_hours_until_today`, `test_the_averages_are_per_night_and_per_elapsed_month`, `test_one_square_per_day_with_its_level_and_the_days_still_to_come`, `test_an_empty_year_has_no_average_per_night_instead_of_zero` |
| Se l'app sta ancora leggendo l'archivio me lo dice, e quanto ha fatto | `test_the_page_says_when_the_reading_is_not_over`, `test_the_reading_says_how_far_it_has_gone`, `test_nothing_to_read_has_no_percentage` (`backend/tests/test_api_nights_page.py`); *dice che la lettura non e' finita* |
| Di ogni oggetto della notte vedo le ore con una barra, e "senza durata" invece di zero; i primi tre e quanti altri | `test_an_object_says_its_frames_without_a_duration_instead_of_zero_hours`, `test_each_object_bar_is_its_share_of_the_longest_of_the_night`, `test_a_short_object_still_shows_a_sliver`; *di ogni oggetto dice le ore con la sua barra* |
| Se non ho ancora notti capisco **quale** dei motivi e', e cosa fare | `test_the_ways_of_having_no_nights_are_different_answers`; *i modi di non avere notti dicono cose diverse* |
| La data di una notte resta quella anche se guardo l'app da un altro fuso | *resta lo stesso giorno anche guardata da un fuso a ovest* (`frontend/tests/formati.test.ts`) |
| Vedo che luna c'era quella notte, quanto era illuminata, col disco dal lato giusto | `test_a_night_says_which_moon_there_was`, `test_the_moon_of_a_night_says_which_side_is_lit`; *una notte dice che luna c'era* |
| Vedo se la Luna lasciava la banda larga: tutta la notte, in parte, o solo la banda stretta | `test_a_past_night_says_how_much_broadband_the_moon_left`; *la ripresa dice banda larga o stretta* |
| Se di una notte la Luna non si puo' sapere, la riga non mi mette un trattino | `test_a_night_whose_site_has_no_timezone_says_nothing_about_the_moon`; *una notte di cui non si sa la luna non scrive un trattino muto* |
| Vedo com'era il cielo: l'esito (buona, incerta, non adatta), le nuvole in parole e in media, le **ore di posa su quelle di buio** | `test_a_past_night_is_judged_by_its_transparency`, `test_a_past_night_says_its_exposure_hours_out_of_its_dark`, `test_a_past_night_without_aerosol_says_so`; *una notte ripresa dice com'era il cielo* |
| Di una notte di pochi giorni fa so il giorno in cui arriva il meteo; se il servizio non ha risposto, lo dice | `test_a_young_night_says_the_day_its_weather_arrives`, `test_the_day_the_weather_arrives_is_counted_in_the_site_time_zone`; *una notte giovane dice il giorno in cui arriva il meteo* |
| Una notte senza buio (estate al nord) dice le ore col Sole sotto l'orizzonte | `test_a_night_without_dark_is_judged_with_the_sun_down` |
| Dalla ricerca apro una notte precisa (`/notti?notte=<id>`), anche vecchia, e torno a tutte; una notte che non c'e' piu' lo dice | `test_a_night_is_asked_by_its_id_wherever_it_falls_in_the_list`, `test_a_night_that_does_not_exist_is_an_empty_list_not_an_error`; *con ?notte= chiede quella notte sola*; *una notte che non c'e' piu' lo dice* |
| Vedo com'erano i miei frame quella notte | nasce con le misure dei frame nelle Notti (passo 33) |
| Apro una notte e vedo tutto (↗ "Tutto della notte") | nasce con il modale, che e' lo stesso dell'oggetto e della libreria (passo 33) |

## La pagina

**Desktop, in ordine** (tavola, 18-98): le righe di stato; *Le notti*, la striscia delle ultime
7; *La notte*, la protagonista (8 colonne, 12 quando e' la sola); a destra il *Calendario delle
notti*; *Criteri*, chiusi in una riga che dice quanti sono attivi, aperti a sinistra
dell'elenco; *A confronto*, l'elenco per mese; in fondo *Tutto l'archivio*.

**Telefono** (100-156): il mese e i criteri sono due bottoni in alto che aprono la stessa carta;
le notti in linguette sottili (le ultime 7, o quelle dei criteri); le righe di stato chiuse in
una ("2 cose da vedere"); la protagonista con ‹ › per la notte prima e dopo; *Tutto l'archivio*.
L'elenco *A confronto* e "Carica altre" il telefono non li ha. L'API da' gli stessi dati ai due
formati.

## Le decisioni

**Una notte e' una data piu' un sito.** Due postazioni nella stessa data sono **due righe**, e la
riga porta il sito: accorparle vorrebbe dire sommare le ore di due cieli diversi. E' la stessa
chiave con cui la notte nasce (`sites` + `night_date` in `backend/astrolog/schema.sql`). Nel
calendario un giorno con due notti ha due segni.

**Il sito dice da dove viene** (DECISIONI v65, 5.4; Marco, 7/11/2026): «dalle coordinate nei
frame» se almeno un frame le porta, «il sito di casa, dalle Impostazioni» se nessuno le porta,
«dalla tua risposta in Da confermare» se il sito l'hai scelto tu. Lo manda l'API.

**Le ore si contano in una casa sola** (`spine/counts.py`): gli stessi numeri escono dallo
**stesso** frammento SQL dell'Archivio, allargato dall'oggetto alla notte e all'archivio intero.
La regola -- cosa entra nella somma e cosa no -- ha la sua casa in [`archivio.md`](archivio.md).

**La protagonista e' una notte sola, scelta.** In partenza la piu' recente; la sceglie la
striscia, il calendario, una riga dell'elenco, ‹ › sul telefono, o l'indirizzo `?notte=<id>`. Con
l'indirizzo la pagina mostra quella sola, a 12 colonne, con «← Tutte le notti».

**Il cielo di una notte passata e' quello del meteo storico, giudicato come il Meteo** (ADR 0034,
punteggio v4): la **Trasparenza** di ogni ora di buio, la media pesata sui minuti di buio, il
verdetto **buona da 70, incerta da 40**, non adatta sotto. Le **ore di posa** sono la somma di
Trasparenza / 100 per le ore di buio: «4,0 ore di posa su 9 di buio». Sotto, una tacca per ora di
buio, piene quante le ore di posa: una proporzione, non un orario, e la riga lo dice. Le nuvole si
dicono nelle quattro classi okta con la media accanto: «Nuvole sparse, in media 8%» (WMO 2700,
come il Meteo). Lo storico **non ha l'aerosol** (Open-Meteo archive): la Trasparenza resta quella
delle nuvole e delle ore che bloccano, e accanto alle ore di posa c'e' «senza aerosol». Una notte
senza buio astronomico si giudica sulle ore col Sole sotto l'orizzonte e lo dice: «N ore visibili
col Sole sotto l'orizzonte».

**Quando il cielo non si sa, si dice perche'.** *Meteo in arrivo*: una notte giovane dice il
giorno in cui il meteo arriva (l'archivio e' definitivo dopo 5 giorni). *Senza meteo*: e' ora,
ma il servizio non ha ancora risposto. *Non disponibile*: il sito non ha un fuso riconosciuto, e
la carta porta a «Modifica sito». Nei criteri, *senza meteo* raccoglie le tre.

**La Luna di una notte passata si calcola, non si conserva** -- ed e' l'eccezione dichiarata a
*"una lettura non calcola mai"* (Marco, 23/9/2026): e' astronomia pura, e non dipende da niente
che l'utente abbia scritto. Si chiede **in un colpo per l'intera pagina**
(`test_asking_the_phases_together_is_worth_it`, `test_the_moon_of_a_whole_page_costs_one_call`),
alla **mezzanotte della notte nel fuso del sito** (`clock.midnight_of`, il perche' in
[`effemeridi.md`](effemeridi.md)); senza fuso riconoscibile la riga **tace**. Il disco ha il lato
illuminato che manda l'app, giusto anche a sud.

**La ripresa dice cosa lasciava la Luna** (Ripresa della tavola): *banda larga* tutta la notte
se la Luna era sotto la soglia delle Impostazioni (25% di fabbrica) o sotto l'orizzonte per tutto
il buio; *solo banda stretta* se era sopra per tutto il buio; *mista* con le ore di banda larga
accanto. La soglia e' quella del calendario della Luna, una casa sola (ADR 0034).

**Il meteo invece si conserva, perche' non si sa derivare**: lo dice un servizio, si chiede una
volta sola e si tiene accanto alla notte. **Il seeing non si recupera**: lo dicono i tuoi frame
(l'HFD), non un modello; la notte passata non ha una parola del seeing.

**I criteri sono le faccette del backend.** Oggetto (nome e nome comune, senza spazi ne'
maiuscole, come la Ricerca), anno, sito, setup, filtri, costellazione, cielo (buona, incerta, non
adatta, senza meteo). Dentro un criterio basta una scelta, fra criteri valgono tutte. Ogni
scelta porta il **numero di notti che darebbe** con le altre scelte applicate: chi la tocca sa
gia' cosa trova, e una scelta a zero e' spenta. I valori sono i tuoi (siti, setup, filtri):
nessun nome e' una regola. L'ordine: anni dal piu' recente, filtri nell'ordine dei filtri, cielo
dal migliore, il resto in ordine alfabetico.

**L'elenco, per mese.** *A confronto* raggruppa le notti per mese, dalla piu' recente, e ogni
mese dice le sue notti e le sue ore (dei criteri scelti, non solo delle righe caricate). Colonne:
giorno, sito e oggetti, integrazione, filtri, cielo, Luna. **20 alla volta** e «Carica altre»; il
conto «20 di 212». La riga scelta ha l'anello, non solo il colore.

**I filtri stanno nell'ordine dei filtri**, uno in tutta l'app (Marco, 7/10/2026):
L, R, G, B, Ha, OIII, SII, poi a colori, poi le altre bande riconosciute, gli sconosciuti per
nome, "senza filtro" ultimo (`vocab/filters.DISPLAY_ORDER`). **Un colore per banda** (Marco,
8/10/2026), sempre col nome accanto.

**In fondo, cosa c'e' in tutto** (DECISIONI v65, 5.4): notti, oggetti, frame, ore e frame senza
durata dell'archivio intero, e «Le copie calibrate non sono contate.»

**Fuori da ogni notte, tre voci con la loro risposta** (DECISIONI v65, 5.2; Marco, 6/11/2026):
*da confermare* («aspettano una risposta») porta a Da confermare; *senza sito* («scegli il sito:
entrano nelle notti») dove si sceglie il sito (Impostazioni › Sito: sono i frame senza nessun sito
o col fuso che non si riconosce; quelli lontani da ogni sito sono gia' fra *da confermare*); *senza
data* («scrivi la data o la notte della cartella») a Da confermare, sezione dei frame senza data.
Una voce a zero non c'e'. Le
stesse tre sono le righe di stato in cima, con l'azione. Supera "un frame senza data non ha
risposta" (contratto del 9/2026): la data la scrivi tu. La sezione dei frame senza data nasce col
porting di Da confermare; fino ad allora la voce si conta e non porta da nessuna parte, perche'
una promessa vuota manda l'utente dove non si risponde.

**E se la lettura non e' finita, lo dice**: «Scansione in corso, 19%: le notti si aggiungono da
sole», una riga sopra le notti che ci sono gia'.

**Non avere notti ha cinque motivi, e cinque risposte** (tavola, 279-286): *Nessuna cartella
scelta* (Scegli la cartella); *Nessun frame nelle cartelle* (Aggiungi cartelle); *Sito mancante*
(Aggiungi sito: una notte e' una data piu' un luogo, e senza sito non nasce mai); *Scansione in
corso* (nessuna azione: e' solo da aspettare); *Tutti i frame aspettano una risposta* (Apri Da
confermare). Il sito che c'e' ma senza fuso riconoscibile ricade in *Sito mancante*: il gesto e'
lo stesso. Poi *Notti non disponibili* (AstroLog non risponde: Riprova) e *Notte non trovata*
(un indirizzo vecchio: Tutte le notti).

**A mani vuote e su tre bersagli.** I numeri arrivano dall'API gia' fatti -- ore sommate, date
nel fuso del sito, esiti, conteggi dei criteri -- e il layout non porta logica.

## Cosa non fa ancora, e con cosa arrivera'

- **Le misure dei frame** nella notte: col pezzo che le porta nelle Notti (passo 33; stati e
  testi in [`misure.md`](misure.md), *I testi a schermo*).
- **"Tutto della notte"** (↗, il Riepilogo in finestra): col modale, lo stesso per notte,
  oggetto e libreria (passo 33). Fino ad allora il ↗ non c'e'.
- Restano fuori per scelta: **anteprime**, **note scritte a mano** e il **voto** della notte --
  una notte si giudica dalle sue ore, dal suo cielo e dalle sue misure, non da una stella su
  cinque.
