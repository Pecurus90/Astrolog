# Il meteo -- contratto

**Com'e' la notte, prima e dopo.** Prima: le prossime notti ora per ora, col verdetto, le ore utili
e cio' che serve alla planetaria. Dopo: il meteo vero delle notti che hai ripreso, accanto alle
pose. Le parole vengono da [`glossario.md`](glossario.md) -- *verdetto* (`go`/`marginal`/`nogo`),
*ore utili*, *fattore*; le notti da mezzogiorno a mezzogiorno nel fuso del sito sono di
[`notti.md`](notti.md); le decisioni ereditate sul meteo, da verificare portandole, stanno in
[`ereditato.md`](ereditato.md), sezione G.

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Apro Meteo e vedo le prossime notti del mio sito, ognuna col verdetto, le ore utili e cosa lo decide | `test_each_model_writes_its_nights_from_the_current_one`, `test_the_summary_is_written_with_the_forecast`, *una notte dice il verdetto, le nuvole, le ore utili e cosa pesa, con l'ora del posto* |
| Ora per ora nuvole basse, medie e alte, vento, raffiche, umidita' e punto di rugiada, da mezzogiorno a mezzogiorno | `test_a_night_carries_its_hours_from_noon_to_noon_with_the_sky_of_each`, `test_the_night_the_clocks_change_has_its_true_hours`, *ora per ora, un numero che il modello non da' si dice, non si scrive zero* |
| Scelgo il modello (ECMWF, ICON, GFS, o quello che il servizio sceglie per il mio posto) e la pagina cambia senza rifare conti | `test_the_switch_reads_another_model_without_asking_again`, `test_a_model_outside_the_list_is_refused`, `test_the_time_of_the_forecast_is_of_the_site_even_when_a_model_brought_no_night`, *lo switch salva il modello scelto e rilegge*, *un modello senza notti lo dice, anche se la previsione e' arrivata* |
| Senza rete vedo l'ultima previsione con l'ora in cui e' arrivata, o che non c'e' ancora; mai numeri inventati | `test_a_silent_service_keeps_the_last_forecast_and_says_so`, `test_a_silent_service_says_why_and_the_last_forecast_stays`, *prima della prima previsione lo dice, invece di un elenco vuoto muto* |
| La previsione arriva da sola: appena ho un sito di casa, e poi ogni tre ore | `test_the_forecast_renews_itself_in_the_background`, `test_a_home_site_declared_later_gets_its_forecast_without_waiting_the_full_round` |
| Senza sito di casa la pagina mi manda a dichiararlo, e non chiede niente a nessuno | `test_without_a_home_site_the_page_says_so_and_asks_nothing`, *senza sito di casa manda a dichiararlo* |
| Un sito di casa senza fuso orario lo dice, invece di aspettare una previsione che non arrivera' | `test_a_home_site_without_a_timezone_is_said`, *un sito di casa senza fuso orario lo dice, invece di aspettare una previsione* |
| Una risposta senza notti intere non cancella la previsione di prima, e una nuova non tocca gli altri siti ne' il meteo osservato | `test_an_answer_that_brings_no_whole_night_leaves_the_last_forecast_alone`, `test_a_new_forecast_leaves_other_sites_and_the_observed_weather_alone` |
| D'estate al nord, dove il buio non arriva, il verdetto guarda le ore col Sole sotto l'orizzonte e lo dice; dove il Sole non tramonta non c'e' verdetto | `test_without_dark_the_night_is_the_hours_with_the_sun_down`, `test_where_the_sun_never_sets_there_is_no_verdict` |
| Le prime tre notti hanno le ore; dalla quarta alla settima vedo solo la tendenza, detta meno affidabile | `test_three_nights_are_full_and_the_following_are_a_trend`, *dalla quarta notte mostra la tendenza, senza ore* |
| Accanto al verdetto leggo quanti modelli sono d'accordo | `test_each_night_says_how_many_models_agree`, *accanto al verdetto dice quanti modelli sono d'accordo*, *un modello solo si dice al singolare* |
| Per la planetaria vedo il jet stream, il seeing e la trasparenza dei servizi, e l'aerosol | `test_the_sky_aloft_joins_the_wind_of_the_model_and_the_seeing_of_its_hour`, `test_the_seeing_bands_become_the_ranges_the_service_documents`, `test_a_source_every_three_hours_still_gives_the_night_that_is_under_way`, *il cielo in quota scrive le fasce del seeing come le da' il servizio* |
| Una fonte del cielo che tace tiene le sue righe e non ferma le altre, e la previsione non le tocca | `test_each_source_writes_only_its_rows_and_a_silent_one_keeps_them` |
| Con la mia chiave Meteoblue, che metto nel primo avvio o nelle Impostazioni, ho il seeing Meteoblue ora per ora | `test_with_the_key_the_seeing_comes_from_meteoblue_hour_by_hour`, `test_the_seeing_is_read_hour_by_hour_in_utc_as_a_single_value`, *una chiave che vale si manda al backend, e dopo si vede solo come finisce* |
| La chiave si prova sul conto prima di salvarla, e non esce mai intera: ne' dall'API, ne' nel log | `test_a_key_the_account_refuses_is_not_kept`, `test_the_key_cannot_be_written_without_being_tried`, `test_a_good_key_is_kept_and_shown_only_by_its_last_four_characters`, `test_the_other_service_key_does_not_come_out_whole_either`, `test_a_short_key_never_comes_out_whole`, `test_the_key_never_reaches_the_log` |
| Se Meteoblue rifiuta la chiave il seeing torna a 7Timer, se tace resta quello di prima; e la pagina dice perche' | `test_a_refused_key_falls_back_to_7timer_and_says_why`, `test_a_key_the_service_refuses_drops_its_seeing_and_says_why`, `test_a_silent_service_keeps_the_seeing_it_gave_last_time`, `test_only_a_refusal_of_the_key_is_a_refusal_and_a_broken_service_is_not`, *se Meteoblue rifiuta la chiave dice perche' il seeing viene da 7Timer* |
| Meteoblue si chiede al massimo due volte al giorno, anche dopo un riavvio; una chiave nuova si usa subito | `test_with_a_key_the_seeing_is_written_and_not_asked_again_before_its_time`, `test_meteoblue_is_asked_at_most_twice_a_day_and_the_credits_would_allow_more`, `test_a_new_key_is_asked_at_once_not_twelve_hours_later` |
| Le notti che ho ripreso hanno il loro meteo vero, arrivato da solo dopo la scansione | `test_a_night_older_than_five_days_gets_its_observed_weather`, `test_the_history_arrives_by_itself_in_the_background`, `test_the_nights_page_reads_the_weather_of_each_night_as_written`, *una notte ripresa dice com'era il cielo, e quante ore sono state serene* |
| Una notte aspetta la rianalisi finche' il suo mattino non ha cinque giorni, e lo dice; una notte senza fuso dice che non si puo' sapere | `test_a_recent_night_waits_for_the_reanalysis`, `test_the_first_night_old_enough_is_the_one_whose_morning_has_five_days`, `test_a_site_without_a_timezone_is_not_asked`, *una notte il cui meteo non e' ancora arrivato lo dice*, *una notte di un sito senza fuso dice che il meteo non si puo' sapere* |
| Lo storico non martella il servizio e non si riscrive: una chiamata per giro, al massimo un anno, una notte scritta resta com'e' | `test_one_call_per_round_covers_many_nights_of_a_site`, `test_a_call_never_asks_more_than_a_year`, `test_the_weather_of_a_night_is_written_once_and_never_again`, `test_a_silent_archive_waits_before_trying_again` |
| In Stanotte leggo il verdetto, le nuvole, le ore utili e l'accordo della notte in corso, col collegamento al Meteo | `test_tonight_tells_the_weather_of_the_night_under_way`, `test_tonight_without_a_forecast_says_nothing_of_the_weather`, *dice il verdetto, le ore utili, l'accordo e il vento in quota, e porta al Meteo* |
| Il vento in quota di una notte lo leggo accanto al solito del mio sito, non contro una soglia | `test_the_climate_of_a_site_is_a_year_of_nights_seen_in_their_own_hours`, `test_the_position_is_how_many_nights_in_ten_had_less_wind`, `test_the_forecast_says_where_each_night_falls_once_the_climate_is_there`, *senza la storia del sito dice il vento e che il confronto arriva, senza inventarlo* |
| Il solito del sito si chiede una volta l'anno, e con poche notti non si scrive | `test_the_climate_is_asked_once_a_year`, `test_the_archive_is_asked_for_the_last_year_up_to_yesterday`, `test_too_few_nights_make_no_climate`, `test_a_year_too_short_is_not_asked_again_every_quarter_of_an_hour`, `test_a_silent_archive_waits_before_trying_again_and_writes_nothing` |

## Decisioni

**Un servizio per ogni compito** (Marco, 25/9/2026, dopo la verifica sulle pagine dei servizi):

| compito | fonte | perche' |
|---|---|---|
| previsione, fino a 16 giorni | Open-Meteo, piu' modelli dalla stessa chiamata | gratis, senza chiave, nuvole su tre strati, CC BY 4.0 |
| seeing e jet stream | vento a 700, 250 e 200 hPa da Open-Meteo; seeing e trasparenza da 7Timer ASTRO; seeing Meteoblue `seeing-1h` con la chiave dell'utente | i primi due gratis per chiunque; Meteoblue e' il piu' curato ma vuole la chiave |
| trasparenza, fumo, aerosol | Open-Meteo Air Quality (dati CAMS) | gratis e mondiale |
| storico di una notte passata | Open-Meteo Archive (ERA5), definitivo dopo 5 giorni | gratis dal 1940 |
| il vento in quota solito del sito | Open-Meteo Historical Forecast, un anno a 700 hPa | l'archivio ERA5 a 700 hPa non risponde, questo si' |

- **Windy non entra**: la prova gratuita da' dati volutamente alterati, il piano utile costa 990
  euro l'anno, le condizioni vietano di salvare i dati e il modello ECMWF non c'e'.
- **Meteoblue non e' la base**: il gratuito regge meno di due chiamate al giorno con le nuvole ora
  per ora e scade dopo un anno. Il seeing Meteoblue si chiede al massimo due volte al giorno --
  il tetto dei crediti ne reggerebbe di piu' (`backend/astrolog/weather/meteoblue.py`) -- e
  l'ultimo tentativo si scrive (`weather_fetches`) cosi' un riavvio non rispende crediti. Una notte
  che ha il seeing di Meteoblue lo prende tutto da li': le ore che non copre restano vuote, invece
  di mescolarsi con le fasce di 7Timer. Se Meteoblue rifiuta la chiave, il suo seeing
  si toglie e torna quello di 7Timer; se tace, resta quello di prima. In tutti e due i casi la
  pagina dice perche'.
- **Il seeing e la trasparenza di 7Timer restano a fasce**: senza chiave, per le prime notti e non
  ogni ora, in otto fasce (https://www.7timer.info/doc.php?lang=en); la pagina scrive l'intervallo, e un
  numero in mezzo sarebbe una misura che nessuno ha fatto. L'aerosol si mostra com'e', senza una scala che non
  abbiamo trovato su una fonte.
- **Il seeing non lo stimiamo noi**: una formula pubblicata "vento in quota -> seeing in secondi
  d'arco" non esiste, e le app che la mostrano usano soglie senza fonte. Il vento in quota si
  mostra com'e'.
- **Piu' modelli con uno switch**: di fabbrica il modello che Open-Meteo sceglie per il posto
  (`best_match`). Il riassunto -- verdetto, fattori, ore utili -- si scrive per ogni modello quando
  arriva la previsione, e lo switch legge soltanto.
- **Le soglie del verdetto vengono da convenzioni pubbliche**, verificate sulla fonte e citate
  accanto al numero in `backend/astrolog/weather/verdict.py`; le prove ne tengono i confini
  (`test_the_verdict_follows_the_okta_classes_of_the_total_cloud` e le sue vicine):
  - la copertura media nel buio in okta (WMO 2700, classi dei METAR): **si fa** fino a 2 okta
    (FEW), **incerta** fino a 4 (SCT), **no** da BKN in su, contando in ottavi (2/8 = 25%, 4/8 = 50%);
  - le **ore utili** sono le ore di buio che il verdetto direbbe serene, cosi' non si contraddicono;
  - i **fattori**, dal piu' grave: pioggia (qualunque, nel buio), nuvole basse oltre 2 okta, nuvole
    oltre 2 okta, raffiche da Beaufort 5 (29 km/h), condensa sotto i 3 gradi fra aria e rugiada
    (regola FAA dei 5 gradi Fahrenheit). Ognuno dice quando morde e quante ore, perche' una
    finestra a tratti non sembri piena.
- **Tre notti piene, poi tendenza fino alla settima** (Marco, 26/9/2026): le ore e i fattori delle
  prime tre notti, dalla quarta il verdetto, le nuvole, le ore di buio e l'accordo, detti meno
  affidabili. Nessuna fonte trovata
  dice un giorno preciso in cui la previsione ora per ora smette di valere: e' una scelta di
  prodotto, non una soglia.
- **Il vento in quota non e' un fattore: si confronta col solito del sito.** Il progetto di prima
  lo faceva pesare oltre il 60esimo percentile, un numero scelto sul suo archivio: nessuna
  convenzione pubblica dice quando il vento a 700 hPa rovina una notte. La notte dice quante notti
  su dieci dell'ultimo anno, **da quel sito**, avevano meno vento nelle ore su cui si giudica la notte; la distribuzione si
  chiede una volta l'anno (`weather_climate`) e sotto un terzo dell'anno di notti non si scrive, e il confronto tace.
- **Quanti modelli sono d'accordo** si dice accanto al verdetto (Marco, 26/9/2026): e' cio' che fa
  capire quanto fidarsi di una notte senza cambiare modello a mano.
- **Nessun voto unico della notte, e la Luna resta fuori dal verdetto**: per la planetaria e la
  Luna il plenilunio non e' un difetto. Il totale delle nuvole e' quello del modello, mai
  ricalcolato dagli strati.

**Quando si scarica.** La previsione appena c'e' un sito di casa (o cambia), poi ogni tre ore in
sottofondo, e a richiesta col pulsante. Lo
storico **da solo, dopo la scansione, in sottofondo** (Marco, 25/9/2026). Fuori dalla lettura dei file comunque: il pacchetto
`astrolog.weather` sta accanto alla spina e i due non si conoscono, e una scansione senza rete va
avanti uguale.

**Dove si scrive.** Una tabella sua, `weather_nights`, per sito, notte, tipo (previsione o storico) e
fonte, con la serie ora per ora e il riassunto gia' calcolato: una lettura non calcola mai. Non sta
nella tabella delle notti, che spazza le notti senza pose -- e la notte di domani non ne ha ancora.
Si tiene cio' che l'app usa, mai la risposta intera del servizio.

**A mani vuote.** Il meteo funziona appena c'e' un sito di casa, senza chiavi. Il primo avvio ha un
passo facoltativo per la chiave Meteoblue, saltabile; la stessa chiave si cambia nelle Impostazioni,
non si mostra mai intera e si prova sul conto prima di salvarla. Sotto i dati, le attribuzioni che i
servizi chiedono: "Weather data by Open-Meteo.com", 7Timer, e per CAMS la frase della licenza
Copernicus con l'anno dei dati; meteoblue quando il seeing viene da li'.

**Niente grafica** (Marco, 25/9/2026): la pagina nasce semplice, coi dati veri in righe e tabelle; i
grafici e la veste arrivano dopo, col design.
