# Le effemeridi -- cosa fa il cielo, e cosa non promettiamo

Cosa l'utente ottiene, e la prova che lo difende.

| l'utente | la prova |
|---|---|
| Vedo che luna fa stanotte dal posto da cui osservo, senza aprire niente | `test_with_a_home_site_the_moon_is_told_with_its_night` |
| La luna e' quella del **mio** sito, non di un posto qualunque | `test_the_moon_comes_from_the_home_site_not_from_any_site` |
| Anche alle due di notte l'app mi parla della nottata in corso, non di quella dopo | `test_the_night_is_the_one_of_the_site_not_of_the_server` |
| Se non ho ancora un sito, l'app me lo dice invece di inventarsi un cielo | `test_without_a_home_site_there_is_no_moon_and_it_is_said` |
| Guardando la notte vedo **dove comincia e dove finisce il buio**, e la Luna dentro | `test_the_route_sends_the_bands_of_the_sky_already_made`, `test_the_evening_goes_down_through_the_four_thresholds_in_order` |
| Dove il Sole non tramonta il cielo e' **una fascia sola**, tutta giorno | `test_a_window_that_never_leaves_the_day_is_one_single_band` |
| Dove non sorge, vedo le fasce che quella notte ha **davvero**: alle Svalbard a gennaio il giorno non c'e', ma i crepuscoli si' | `test_a_real_polar_night_never_sees_the_day` |
| Una notte in cui il buio comincia e non finisce **conta lo stesso**, fino al bordo | `test_the_dark_that_begins_and_does_not_end_is_measured_to_the_edge` |
| Se la Luna non sorge **stanotte**, leggo che non sorge stanotte -- non un'ora finta | `test_a_moon_that_never_rises_comes_back_empty_not_invented`, `test_a_moon_that_never_rises_is_a_fact_not_an_error` |
| So **quanto sale** stanotte, e a che ora ci arriva: e' cio' che dice se mi rovina le pose | `test_the_highest_point_of_the_night_is_told_with_its_instant` |
| Anche una notte in cui non sorge mi dice quanto poco sale, invece di tacere | `test_a_moon_that_never_rises_still_has_a_highest_point` |
| Il grafico della notte comincia e finisce **con la notte**, senza perdere l'ultima mezz'ora | `test_the_curve_spans_the_whole_night_including_its_last_instant`, `test_the_route_sends_the_curve_and_the_highest_point` |
| Due notti dello stesso posto si confrontano a occhio, perche' il grafico ha sempre la stessa altezza | `test_the_ceiling_is_the_highest_the_moon_can_ever_get_from_there`, `test_the_route_sends_the_ceiling_of_the_home_site` |
| Se osservo ai tropici il grafico non nasce con un quinto di tela vuota per sempre | `test_in_the_tropics_the_moon_reaches_the_zenith_and_the_ceiling_stops_at_ninety` |
| Il tetto del grafico sta **sopra** la Luna a ogni latitudine, non quasi | `test_the_ceiling_never_falls_below_what_the_moon_really_reaches`, `test_the_declination_bound_is_not_smaller_than_the_real_moon` |
| Leggo da dove osservo e che cielo ha **nella stessa riga** della Luna, non in due giri | `test_the_route_sends_the_site_with_the_sky_it_has` |
| Se non ho mai dichiarato che cielo ho, l'app lo dice invece di indovinarlo | `test_a_site_whose_sky_was_never_declared_says_so_instead_of_guessing` |
| Se osservo dall'emisfero sud il grafico nasce dritto come al nord | `test_the_ceiling_does_not_care_which_hemisphere_you_are_in` |
| La Luna che vedo disegnata e' illuminata dalla parte da cui la vedo davvero, anche dall'altra meta' del mondo | `test_the_lit_limb_is_mirrored_south_of_the_equator` |
| Il numero che leggo e' quello della notte che sto guardando, non di dodici ore prima | `test_the_phase_is_asked_in_the_middle_of_the_night_not_at_noon` |
| La notte del cambio d'ora non mi fa sparire un orario | `test_the_window_lasts_the_real_night_not_a_fixed_day`, `test_the_grid_covers_real_hours_even_when_the_clock_jumps` |
| Se il fuso del mio sito non esiste piu', la pagina non cade | `test_a_site_whose_timezone_no_longer_exists_does_not_break_the_page` |
| Funziona senza rete, che e' esattamente dove osservo | `test_importing_the_ephemeris_disarms_the_download`, e il **recinto di rete** su tutta la suite (`tests/conftest.py`) |

## Le decisioni

**Offline, sempre.** Importare `astrolog.ephemeris` disinnesca il download di `astropy` e usa il
suo modello incorporato del sistema solare. Le due righe che lo fanno **lavorano insieme**,
misurato su una macchina senza rete: col solo "non scaricare" astropy solleva lo stesso, perche'
i dati impacchettati risultano troppo vecchi -- serve anche dire che vanno bene cosi'. L'app gira
su un NAS in una casa senza rete e su un portatile in montagna, e li' un'effemeride che scarica
non e' lenta, e' rotta. Il prezzo e' una precisione di arcosecondi che per dire quanta luce fa
stanotte non si vede, e astropy lo dichiara con un avviso che le prove lasciano passare
nominandolo.

**La fase e' geocentrica, il sorgere e' topocentrico.** Quanto e' illuminata la Luna si vede
uguale da tutta la Terra: calcolarla dal sito la farebbe ballare di pochissimo e senza motivo, e
due persone che guardano la stessa luna leggerebbero due numeri diversi. L'ora in cui sorge invece
dipende da dove sei, ed e' tutto il punto.

**Otto fasi, e non sono fette uguali.** I quattro nomi "esatti" -- nuova, primo quarto, piena,
ultimo quarto -- coprono **dodici gradi** ciascuno, sei per lato del centro; i quattro nomi
intermedi si prendono quel che resta, **settantotto** a testa. "Luna piena" e' una parola, non un
istante: chiamarla piena solo all'istante esatto vorrebbe dire non dirlo mai. La semi-ampiezza e'
scritta in un posto solo (`ephemeris/moon.py`), e da li' si ricava anche quanta luce puo' avere
ogni fase -- e' cosi' che la prova verifica che il nome e la luce non si contraddicano, senza
fidarsi di una data ricordata.

**La fase si chiede alla mezzanotte di quella notte**, non all'inizio della finestra. La Luna
cambia circa il sei per cento al giorno: chiesta a mezzogiorno, chi guarda la barra alle undici di
sera leggerebbe il numero di dodici ore prima -- misurato, 48% contro 54% sulla stessa notte. E
vicino al bordo di una banda sarebbe anche il **nome** a scattare un giorno prima.

L'istante lo compone `clock.midnight_of`, ed e' **una casa sola**: lo chiedono la barra di stanotte
e la pagina delle Notti, che raccontano la stessa notte e non possono chiederla a due momenti
diversi. Non e' il mezzo esatto della finestra, che nella notte del cambio d'ora cadrebbe alle
23:30 o alle 00:30: e' la mezzanotte, che si spiega in una parola e non dipende da quanto dura la
notte.

**La finestra si misura fra i due mezzogiorni veri**, non a ventiquattro ore fisse: la notte del
cambio d'ora ne dura 23 o 25, e contarne 24 vorrebbe dire guardare un'ora della notte dopo o
perdere l'ultima di questa. Sommare le ore a un istante che porta il fuso, invece che in UTC,
sbagliava quattro orari su ottanta in vent'anni a Vicenza -- fino a un'ora, e fino a quasi nove
allargando la finestra.

**La notte e' quella dell'app**, da mezzogiorno a mezzogiorno nel fuso del sito
(`astrolog.clock.night_date`). La rotta manda **anche la notte** a cui si riferisce: chi mostra
quei numeri deve sapere quando sono scaduti, e una risposta senza data costringerebbe a
richiederla di continuo.

**Gli orari sono quelli della notte, non di sempre.** `rise` e `set` sono i primi
attraversamenti dentro la finestra della notte, e `null` vuol dire **"non in questa notte"**: la
Luna torna ogni giorno circa cinquanta minuti piu' tardi, quindi un paio di notti al mese uno dei
due cade fuori anche a latitudini normali (misurato a Vicenza: due su trenta). Sopra il circolo
polare e' il caso ovvio, ma non e' l'unico, e chi li mostra scrive "non tramonta stanotte".
I due istanti sono **indipendenti**: per meta' mese il tramonto viene prima del sorgere (misurato:
tredici notti su trenta), ed e' giusto -- e' la Luna di ieri che cala prima che sorga quella di
stanotte.

**Il punto piu' alto c'e' sempre, e non e' sempre una culminazione.** E' il massimo **dentro la
finestra della notte**: quasi sempre coincide con la culminazione vera, ma se la Luna sta ancora
salendo quando la notte finisce cade sul bordo -- e quello, per chi osserva, e' comunque il numero
giusto, perche' la domanda e' *quanto sale stanotte*, non *quanto salirebbe domani*. Non e' un
caso di laboratorio, ed e' la ragione per cui a schermo si dice *"sale fino a"* e non *"culmina"*:
misurato a Vicenza su **due anni interi** (2026 e 2027), il massimo cade su un estremo della
finestra **48 notti su 730**, cioe' una su quindici. E su **tutti e due** gli estremi -- 22 volte
sul primo campione, quando la Luna sta gia' scendendo a mezzogiorno, e 26 sull'ultimo, quando sta
ancora salendo quando la notte finisce. Il numero si misura su un anno intero e non su un mese:
fra gennaio e febbraio 2027 sono 5 notti su 60, che sarebbe una su dodici -- un grumo, non la
frequenza. E si manda
**anche quando non ci sono orari**: una Luna che non sorge sale lo stesso, sotto l'orizzonte, e
quanto poco sale e' esattamente cio' che si vuole sapere.

**Il sito viaggia con la notte, e col suo cielo.** La rotta manda il nome del posto **e** la sua
classe di Bortle con la misura da cui nasce, perche' il piede della barra le scrive in una riga
sola: *"da dove osservi, e cosa fa il cielo"*. Chiederle a due rotte vorrebbe dire due giri di rete
per una frase, e un momento in cui la pagina e' a meta'. La classe **non e' una colonna**: la
conversione vive in `astrolog.units` e qui si riusa, perche' due conti uguali in due posti un
giorno diranno cose diverse -- e sullo stesso cielo le due famiglie di conversione differiscono
fino a due classi. I due campi possono mancare **insieme**: senza la misura non c'e' classe, ed e'
lo stato di chi ha saltato quella domanda, non un guasto.

**Da che parte e' illuminata lo dice il backend.** Cresce a destra e cala a sinistra, ma
**dall'emisfero sud si vede al contrario**: la Luna sta dalla parte opposta del cielo e la si
guarda capovolta. Dipende dalla fase **e** da dove sei, cioe' da due cose che solo qui stanno
insieme: farlo dedurre a chi disegna vorrebbe dire un conto nel layout, e meta' del mondo con
ogni fase specchiata -- un difetto che da queste latitudini non si vede mai.

**Il tetto e' del sito, non della notte.** Il bordo alto del grafico e' **quanto in alto la Luna
puo' arrivare da quella latitudine**, mai di piu', salito al multiplo di quindici gradi. Dipende
solo da dove sei, ed e' tutto il punto: una scala che si adattasse alla notte farebbe diventare
due notti diverse la stessa gobba, e la sola domanda che si sta facendo -- *quanto e' alta* --
sparirebbe dal disegno. Una scala fissa uguale per tutti invece spreca: da Vicenza la Luna non
passa mai i 73 gradi (misurati 72,9), quindi contro un tetto fisso a 90 resterebbero vuoti per
sempre diciassette gradi su centocinque, **un sesto della tela**. Il prezzo del tetto
del sito e' che due posti a latitudini diverse non si confrontano a occhio, e si paga volentieri:
chi osserva confronta stanotte con domani notte, non Vicenza con Palermo.

**E si ferma a novanta.** La declinazione massima della Luna si scrive come somma dei due numeri
pubblicati -- l'inclinazione dell'asse terrestre piu' quella dell'orbita lunare -- e sotto quella
latitudine la Luna passa **allo zenit**: li' il tetto e' novanta e basta. La forma senza quel
limite, che e' quella arrivata dal disegno, alle Canarie da' 90,5 e a Singapore 117 -- un tetto di
120 contro i 90 che servono, cioe' poco piu' di un quinto di tela vuota per sempre. Il numero lo
manda il backend gia' salito alla tacca: farlo salire a schermo sarebbe un conto dentro il layout.

**La curva si manda a quindici minuti, il conto si fa a tre.** Sono due mestieri: il passo fitto
serve a trovare gli attraversamenti, quello largo a disegnare. Una notte sono 97 punti invece di
481 -- misurata, la risposta pesa 5,5 KB -- per una differenza che a schermo non si vede. Il passo
della curva
**deve restare un multiplo** di quello del conto, o "ogni quindici minuti" diventa un
arrotondamento e i punti si spostano di poco -- cioe' nel modo che non si nota. E il primo e
l'ultimo punto sono i due estremi della notte: con una finestra che non e' un multiplo del passo,
prendere un campione ogni tot scavalca l'ultimo e il grafico chiude prima della fine.

**Un corpo, un campionamento.** Della Luna, sorgere, tramontare, punto piu' alto e curva escono
dalla **stessa** griglia e dalla stessa unica chiamata ad astropy -- chiederla due volte sarebbe
pagarla due volte per gli stessi numeri. Il Sole e' un corpo diverso e ha il suo: sono due, non
uno ripetuto. E' l'unica cosa cara che c'e' qui (misurato il 20/9/2026: 140 ms la Luna, 53 il
Sole, contro i 2 ms di una rotta che legge e basta -- e il Sole costa meno perche' non passa da
`get_body`, che per lui vale 87 ms in piu' e due centesimi di secondo d'arco: la ragione sta in
`ephemeris/corpi.py`).

**Il conto si fa in UTC, la risposta torna nel fuso del sito.** Sommare ore a un istante con un
fuso vero fa aritmetica da orologio da parete, e la notte del cambio d'ora "ventiquattro ore"
diventano ventitre: la griglia tornava indietro, inventava un attraversamento, e il tramonto
usciva sbagliato di otto ore con un orario che quella notte non era mai esistito.

**Un istante senza fuso si rifiuta.** `astropy` lo leggerebbe come UTC in silenzio, e su un sito
in Arizona la notte risulterebbe sbagliata di mezza giornata. E' la stessa regola con cui
l'archivio legge le date degli header, applicata al cielo.

**Le fasce arrivano gia' divise.** La rotta manda segmenti attaccati che coprono la notte, non
gli otto attraversamenti da ricomporre a schermo. Con quelli, chi disegna dovrebbe ragionare su
**quali mancano** -- e alle alte latitudini ne mancano tre, quattro o tutti -- cioe' fare una
derivazione, che sta qui. Una lista di segmenti copre da se' anche il caso polare, dove la
finestra e' una fascia sola. Chi la mostra la dipinge e basta.

## Cosa NON promettiamo

- **I pianeti e la visibilita' di un oggetto** non ci sono. Il codice esiste in `old/`, e si
  porta quando nasce la schermata che lo chiede -- non prima: cio' che si porta senza una
  superficie che lo mostri e' codice che nessuno guida. **Del Sole c'e' quello che serve a dire
  dov'e' il buio** -- le cinque fasce del cielo -- e non un minuto di piu': niente sorgere e
  tramontare del Sole come orari a se', niente ore di buio come numero. Arrivano con le Notti, che
  e' la schermata che li chiede.
- **Niente meteo.** Non e' un'effemeride e non e' nostro: dipende da un servizio, e quel dominio
  non esiste ancora.
- **Nessuna previsione di quanto sara' buono il cielo.** L'app dice cosa fa la Luna; se la notte
  valga la pena lo decide chi osserva.

## Dove vive

`backend/astrolog/ephemeris/` -- puro: non tocca il database, la spina, le rotte ne' la rete, e un
contratto di import-linter lo fa rispettare. La rotta e' `GET /api/v1/tonight`, in
`backend/astrolog/api/tonight.py`, che e' l'unico posto dove le effemeridi incontrano un sito.

Chi mostrera' questi numeri e' il **piede della barra**, gia' deciso e disegnato in
[`navigazione.md`](navigazione.md): il sito attivo col suo cielo, e sotto la Luna.
