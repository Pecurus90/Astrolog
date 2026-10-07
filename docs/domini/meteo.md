# Il meteo -- contratto

**Com'e' la notte, prima e dopo.** Prima: le prossime notti ora per ora, col verdetto, le ore utili
e cio' che serve alla planetaria. Dopo: il meteo vero delle notti che hai ripreso, accanto alle
pose. Le parole vengono da [`glossario.md`](glossario.md) -- *verdetto* (`go`/`marginal`/`nogo`),
*ore utili*, *misura*, *pesa*, *giudizio*; le notti da mezzogiorno a mezzogiorno nel fuso del sito sono di
[`notti.md`](notti.md); le decisioni ereditate sul meteo, da verificare portandole, stanno in
[`ereditato.md`](ereditato.md), sezione G.

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Apro Meteo e vedo le prossime notti del mio sito, ognuna col verdetto, le ore utili e cosa lo decide | `test_each_model_writes_its_nights_from_the_current_one`, `test_the_summary_is_written_with_the_forecast`, *in testa le ore serene col semaforo, da che ora a che ora e l'accordo, con l'ora del posto*, *accanto al semaforo pesa solo cio' che il backend dice incerto o niente, con la parola e le ore* |
| Il semaforo lo fanno le nuvole; ogni altra misura con soglia dice la sua parola ora per ora e per la notte, con l'intervallo e il conto, e pesa accanto senza cambiarlo | `test_each_measure_judges_an_hour_at_the_edges_of_its_source`, `test_condensation_comes_under_three_degrees_between_air_and_dew_point`, `test_a_measure_takes_the_worst_hour_of_the_night_and_says_its_hours`, `test_the_clouds_are_the_verdict_and_never_weigh`, `test_good_and_neutral_measures_do_not_weigh`, `test_every_hour_carries_the_judgement_of_each_judged_measure`, `test_the_round_writes_the_nights_with_the_sky_sources_joined_and_judged` |
| Le misure arrivano in ordine d'importanza, con la media delle ore vere, il picco, e la parte di notte che coprono; le soglie arrivano dal backend | `test_the_order_is_clouds_then_nogo_then_marginal_then_go_earliest_first_then_neutral`, `test_the_night_value_is_the_mean_of_the_true_numbers_and_rain_is_a_total`, `test_the_peak_is_the_worst_hour_and_says_when`, `test_a_measure_known_only_in_part_of_the_night_says_which_part`, `test_every_scale_is_sent_with_its_steps`, `test_the_page_gets_the_thresholds_the_judgement_used` |
| La Luna pesa per la banda larga solo quando e' sopra l'orizzonte col buio | `test_the_moon_up_brings_its_lit_part_and_down_brings_nothing`, `test_the_moon_is_left_out_when_it_is_never_up_in_the_dark` |
| Le ore serene sono un intervallo e un conto, e la pagina sa da che ora a che ora disegnare | `test_the_usable_hours_are_said_as_an_interval_and_a_count`, `test_the_end_of_an_interval_is_the_next_hour_of_the_night_even_when_the_clocks_change`, `test_the_page_shows_from_the_last_hour_of_day_to_the_first_after_dawn` |
| Ora per ora nuvole basse, medie e alte, vento, raffiche, umidita' e punto di rugiada, da mezzogiorno a mezzogiorno | `test_a_night_carries_its_hours_from_noon_to_noon_with_the_sky_of_each`, `test_the_night_the_clocks_change_has_its_true_hours`, *un'ora che il servizio non da' si disegna a tratteggio, mai come uno zero* |
| Scelgo il modello (ECMWF, ICON, GFS, o quello che il servizio sceglie per il mio posto) e la pagina cambia senza rifare conti | `test_the_switch_reads_another_model_without_asking_again`, `test_a_model_outside_the_list_is_refused`, `test_the_time_of_the_forecast_is_of_the_site_even_when_a_model_brought_no_night`, *lo switch salva il modello scelto e rilegge*, *un modello senza notti lo dice, anche se la previsione e' arrivata* |
| Senza rete vedo l'ultima previsione con l'ora in cui e' arrivata, o che non c'e' ancora; mai numeri inventati | `test_a_silent_service_keeps_the_last_forecast_and_says_so`, `test_a_silent_service_says_why_and_the_last_forecast_stays`, *prima della prima previsione lo dice, invece di un elenco vuoto muto* |
| La previsione arriva da sola: appena ho un sito di casa, e poi ogni tre ore | `test_the_forecast_renews_itself_in_the_background`, `test_a_home_site_declared_later_gets_its_forecast_without_waiting_the_full_round` |
| Senza sito di casa la pagina mi manda a dichiararlo, e non chiede niente a nessuno | `test_without_a_home_site_the_page_says_so_and_asks_nothing`, *senza sito di casa manda a dichiararlo* |
| Un sito di casa senza fuso orario lo dice, invece di aspettare una previsione che non arrivera' | `test_a_home_site_without_a_timezone_is_said`, *un sito di casa senza fuso orario lo dice, e porta a sistemarlo* |
| Una risposta senza notti intere non cancella la previsione di prima, e una nuova non tocca gli altri siti ne' il meteo osservato | `test_an_answer_that_brings_no_whole_night_leaves_the_last_forecast_alone`, `test_a_new_forecast_leaves_other_sites_and_the_observed_weather_alone` |
| D'estate al nord, dove il buio non arriva, il verdetto guarda le ore col Sole sotto l'orizzonte e lo dice; dove il Sole non tramonta non c'e' verdetto | `test_without_dark_the_night_is_the_hours_with_the_sun_down`, `test_where_the_sun_never_sets_there_is_no_verdict` |
| Le prime tre notti hanno le ore; dalla quarta alla settima vedo solo la tendenza, detta meno affidabile | `test_three_nights_are_full_and_the_following_are_a_trend`, *dalla quarta notte mostra la tendenza, senza ore* |
| Accanto al verdetto leggo quanti modelli sono d'accordo | `test_each_night_says_how_many_models_agree`, *in testa le ore serene col semaforo, da che ora a che ora e l'accordo, con l'ora del posto* |
| Per la planetaria vedo il jet stream, l'aerosol e, con la chiave Meteoblue, il seeing; nessun dato a fasce o ogni tre ore | `test_the_sky_aloft_joins_the_wind_of_the_model_and_the_seeing_of_its_hour`, `test_without_a_key_the_sky_is_asked_only_to_cams`, *un seeing che copre solo parte della notte lo dice nella media e nel picco* |
| Una fonte del cielo che tace tiene le sue righe e non ferma le altre, e la previsione non le tocca | `test_each_source_writes_only_its_rows_and_a_silent_one_keeps_them` |
| Con la mia chiave Meteoblue, che metto nel primo avvio o nelle Impostazioni, ho il seeing Meteoblue ora per ora | `test_with_the_key_the_seeing_comes_from_meteoblue_hour_by_hour`, `test_the_seeing_is_read_hour_by_hour_in_utc_as_a_single_value`, *una chiave che vale si manda al backend, e dopo si vede solo come finisce* |
| La chiave si prova sul conto prima di salvarla, e non esce mai intera: ne' dall'API, ne' nel log | `test_a_key_the_account_refuses_is_not_kept`, `test_the_key_cannot_be_written_without_being_tried`, `test_a_good_key_is_kept_and_shown_only_by_its_last_four_characters`, `test_the_other_service_key_does_not_come_out_whole_either`, `test_a_short_key_never_comes_out_whole`, `test_the_key_never_reaches_the_log` |
| Senza chiave la pagina dice che il seeing la vuole; se Meteoblue non accetta la chiave il seeing sparisce, se tace resta quello di prima; e la pagina dice perche' | `test_without_a_key_there_is_no_seeing_and_meteoblue_is_not_mentioned`, `test_a_refused_key_leaves_the_night_without_seeing_and_says_why`, `test_a_key_the_service_refuses_drops_its_seeing_and_says_why`, `test_a_silent_service_keeps_the_seeing_it_gave_last_time`, `test_only_a_refusal_of_the_key_is_a_refusal_and_a_broken_service_is_not`, `test_the_hours_meteoblue_does_not_cover_stay_without_seeing`, *senza chiave la carta dice che serve una chiave Meteoblue, e porta alle Impostazioni*, *con la chiave appena messa e Meteoblue non ancora chiesto non chiede la chiave*, *se Meteoblue non accetta la chiave la carta lo dice* |
| Meteoblue si chiede al massimo due volte al giorno, anche dopo un riavvio; una chiave nuova si usa subito | `test_with_a_key_the_seeing_is_written_and_not_asked_again_before_its_time`, `test_meteoblue_is_asked_at_most_twice_a_day_and_the_credits_would_allow_more`, `test_a_new_key_is_asked_at_once_not_twelve_hours_later` |
| Le notti che ho ripreso hanno il loro meteo vero, arrivato da solo dopo la scansione | `test_a_night_older_than_five_days_gets_its_observed_weather`, `test_the_history_arrives_by_itself_in_the_background`, `test_the_nights_page_reads_the_weather_of_each_night_as_written`, *una notte ripresa dice com'era il cielo, e quante ore sono state serene* |
| Una notte aspetta la rianalisi finche' il suo mattino non ha cinque giorni, e lo dice; una notte senza fuso dice che non si puo' sapere | `test_a_recent_night_waits_for_the_reanalysis`, `test_the_first_night_old_enough_is_the_one_whose_morning_has_five_days`, `test_a_site_without_a_timezone_is_not_asked`, *una notte il cui meteo non e' ancora arrivato lo dice*, *una notte di un sito senza fuso dice che il meteo non si puo' sapere* |
| Lo storico non martella il servizio e non si riscrive: una chiamata per giro, al massimo un anno, una notte scritta resta com'e' | `test_one_call_per_round_covers_many_nights_of_a_site`, `test_a_call_never_asks_more_than_a_year`, `test_the_weather_of_a_night_is_written_once_and_never_again`, `test_a_silent_archive_waits_before_trying_again` |
| In Stanotte leggo il verdetto, le nuvole, le ore utili e l'accordo della notte in corso, col collegamento al Meteo | `test_tonight_tells_the_weather_of_the_night_under_way`, `test_tonight_without_a_forecast_says_nothing_of_the_weather`, *dice il verdetto, le ore utili, l'accordo e il vento in quota, e porta al Meteo* |
| Il vento in quota di una notte lo leggo accanto al solito del mio sito, non contro una soglia | `test_the_climate_of_a_site_is_a_year_of_nights_seen_in_their_own_hours`, `test_the_position_is_how_many_nights_in_ten_had_less_wind`, `test_the_forecast_says_where_each_night_falls_once_the_climate_is_there`, *il vento a 700 hPa si legge accanto al solito del sito (%s)* |
| Il solito del sito si chiede una volta l'anno, e con poche notti non si scrive | `test_the_climate_is_asked_once_a_year`, `test_the_archive_is_asked_for_the_last_year_up_to_yesterday`, `test_too_few_nights_make_no_climate`, `test_a_year_too_short_is_not_asked_again_every_quarter_of_an_hour`, `test_a_silent_archive_waits_before_trying_again_and_writes_nothing` |

## Decisioni

**Un servizio per ogni compito** (Marco, 25/9/2026, dopo la verifica sulle pagine dei servizi):

| compito | fonte | perche' |
|---|---|---|
| previsione, fino a 16 giorni | Open-Meteo, piu' modelli dalla stessa chiamata | gratis, senza chiave, nuvole su tre strati, CC BY 4.0 |
| seeing e jet stream | vento a 700, 250 e 200 hPa da Open-Meteo; seeing Meteoblue `seeing-1h` con la chiave dell'utente | il vento gratis per chiunque; il seeing ora per ora c'e' solo da Meteoblue |
| limpidezza: aerosol e polveri | Open-Meteo Air Quality (dati CAMS) | gratis e mondiale |
| storico di una notte passata | Open-Meteo Archive (ERA5), definitivo dopo 5 giorni | gratis dal 1940 |
| il vento in quota solito del sito | Open-Meteo Historical Forecast, un anno a 700 hPa | l'archivio ERA5 a 700 hPa non risponde, questo si' |

- **Windy non entra**: la prova gratuita da' dati volutamente alterati, il piano utile costa 990
  euro l'anno, le condizioni vietano di salvare i dati e il modello ECMWF non c'e'.
- **Meteoblue non e' la base**: il gratuito regge meno di due chiamate al giorno con le nuvole ora
  per ora e scade dopo un anno. Il seeing Meteoblue si chiede al massimo due volte al giorno --
  il tetto dei crediti ne reggerebbe di piu' (`backend/astrolog/weather/meteoblue.py`) -- e
  l'ultimo tentativo si scrive (`weather_fetches`) cosi' un riavvio non rispende crediti. Le ore che
  Meteoblue non copre restano vuote. Se Meteoblue rifiuta la chiave, il suo seeing si toglie; se
  tace, resta quello di prima. In tutti e due i casi la pagina dice perche'.
- **7Timer esce** (Marco, 3/10/2026): dava seeing e trasparenza a fasce e ogni tre ore. In tutta
  l'app nessun dato a fasce e nessun dato ogni tre ore: senza chiave Meteoblue il seeing non c'e', e
  la pagina dice che per averlo serve la chiave, gratuita. La limpidezza la dice l'aerosol.
- **Il seeing non lo stimiamo noi**: una formula pubblicata "vento in quota -> seeing in secondi
  d'arco" non esiste, e le app che la mostrano usano soglie senza fonte. Il vento in quota si
  mostra com'e'.
- **Piu' modelli con uno switch**: di fabbrica il modello che Open-Meteo sceglie per il posto
  (`best_match`). Il riassunto -- verdetto, misure, ore utili -- si scrive per ogni modello quando
  arriva la previsione, e lo switch legge soltanto.
- **Il semaforo lo decidono solo le nuvole** (DECISIONI del disegno, 3/10/2026): la copertura
  media nel buio in okta (WMO 2700, classi dei METAR): **si fa** fino a 2 okta (FEW), **incerta**
  fino a 4 (SCT), **no** da BKN in su, contando in ottavi (2/8 = 25%, 4/8 = 50%). Le **ore utili**
  sono le ore di buio che il verdetto direbbe serene, cosi' non si contraddicono, dette come
  intervallo e conto ("dalle 23 alle 04, 4 ore"), mai in minuti: i dati sono orari.
- **Le altre misure pesano accanto, senza cambiarlo.** Ogni misura con soglia ha la sua parola
  ora per ora (buona, incerta, niente) e per la notte quella dell'ora peggiore, con l'intervallo e
  il conto delle ore che la portano. Le soglie stanno in `backend/astrolog/weather/judge.py`, con
  la fonte accanto al numero (verificate il 7/10/2026), e la rotta le manda alla pagina (`scales`):
  - nuvole basse come il totale (okta); pioggia: qualunque e' niente; raffiche: niente da Beaufort 5
    (29 km/h); vento medio: incerta da Beaufort 4 (20 km/h), niente da 5;
  - condensa: niente sotto i 3 gradi fra aria e rugiada (regola FAA dei 5 gradi Fahrenheit);
  - jet stream (250 hPa): niente da 126 km/h, i 35 m/s che meteoblue dice "seeing
    cattivo"; nessuna fonte per un gradino incerto, quindi non c'e';
  - seeing: buona fino a 2", incerta fino a 4", niente oltre (classi del Canadian Meteorological
    Centre, quelle di Clear Sky Chart);
  - aerosol: sotto 0,1 *limpido*, da 1 *molto fosco* (NASA Earth Observatory); in mezzo nessuna
    parola, che per la notte e' peggio di *limpido* (un'ora limpida non fa limpida la notte);
  - Luna, per la banda larga: buona fino al 25% illuminata (la regola diffusa fra chi riprende),
    *al limite* fino al 50%, oltre *solo banda stretta* (il 50 e' di Marco, 7/10/2026); pesa solo
    nelle ore in cui e' sopra l'orizzonte (-0,833 gradi, convenzione del Nautical Almanac).
  Neutri, senza parola: nuvole medie e alte, umidita', temperatura, punto di rugiada, vento a 700
  hPa (si confronta col solito del sito), vento a 200 hPa, polveri.
- **L'ordine d'importanza** lo scrive il backend: le nuvole, poi le misure giudicate da "niente" a
  "buona", a pari parola quella che comincia prima, poi i neutri. Il valore della notte e' la media
  delle ore che hanno un numero (la pioggia, il totale); il picco e' l'ora peggiore; se una misura
  copre solo parte della notte lo dice, cosi' una media parziale non passa per intera.
- **Tre notti piene, poi tendenza fino alla settima** (Marco, 26/9/2026): le ore e le misure delle
  prime tre notti, dalla quarta il verdetto, le nuvole, le ore di buio e l'accordo, detti meno
  affidabili. Nessuna fonte trovata
  dice un giorno preciso in cui la previsione ora per ora smette di valere: e' una scelta di
  prodotto, non una soglia.
- **Il vento in quota non ha giudizio: si confronta col solito del sito.** Il progetto di prima
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
fonte, con la serie ora per ora come arriva (lo storico col suo riassunto). Le notti della
previsione pronte per la pagina stanno in `weather_view`, derivata: la riscrive il giro del meteo
(`weather/view.py`) dopo previsione e cielo, unendo per ogni modello aerosol, seeing e Luna, coi
giudizi e l'accordo gia' fatti. Una lettura non calcola mai. Non sta
nella tabella delle notti, che spazza le notti senza pose -- e la notte di domani non ne ha ancora.
Si tiene cio' che l'app usa, mai la risposta intera del servizio.

**A mani vuote.** Il meteo funziona appena c'e' un sito di casa, senza chiavi. Il primo avvio ha un
passo facoltativo per la chiave Meteoblue, saltabile; la stessa chiave si cambia nelle Impostazioni,
non si mostra mai intera e si prova sul conto prima di salvarla. Sotto i dati, le attribuzioni che i
servizi chiedono: "Weather data by Open-Meteo.com", e per CAMS la frase della licenza
Copernicus con l'anno dei dati; meteoblue quando il seeing viene da li'.

**La pagina nel disegno** (ADR 0018; DECISIONI del disegno, forma C): una notte alla volta, la fila
delle sette notti, la scheda con le ore serene, cio' che pesa e le carte delle misure. I grafici
disegnano solo cio' che il backend manda: le ore da disegnare (`shown`), la scala di ogni carta
(`axis_*`) e il giudizio di ogni ora (`levels`).
