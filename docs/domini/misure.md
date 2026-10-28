# Le misure dei frame -- contratto

Le **misure** di un frame sono i numeri che l'app prende dai suoi pixel: quante stelle, quanto
sono larghe, il fondo del cielo, il suo rumore. Le prende lo stadio `measure` della pipeline
nuova (`backend/astrolog/pipeline/measure.py`), dopo il cielo di ASTAP, **una volta**, e le
scrive in `pipeline_measures`; con la soluzione e il sito lo stadio `sky` scrive quelle sul
cielo in `pipeline_sky`. Nessuna lettura le ricalcola. Le regole e i giudizi vengono da
ADR 0022, 0033 (D1), 0037 e 0039; questo contratto dice cosa vale oggi e cosa arriva dopo. Le
parole in [`glossario.md`](glossario.md).

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Ogni mio light viene misurato una volta, da uno dei suoi file, e la misura resta | `test_a_light_is_measured_once_and_written`, `test_only_lights_are_measured`, `test_the_plain_file_is_read_before_its_fpack_copy` (`backend/tests/test_pipeline_measure.py`) |
| L'HFD e' il diametro che contiene meta' della luce della stella, anche con le ali di una stella vera | `test_the_hfd_of_gaussian_stars_is_the_diameter_holding_half_the_flux`, `test_the_hfd_of_moffat_stars_holds_their_wings`, `test_the_truth_is_the_analytic_hfd_once_the_pixel_is_small` (`backend/tests/test_pipeline_stars.py`) |
| Fondo cielo e rumore sono quelli del cielo, non delle stelle | `test_background_and_noise_are_the_sky_and_its_spread` |
| Le stelle si contano una volta; i pixel caldi di un light non calibrato non sono stelle | `test_every_star_is_counted_once`, `test_hot_pixels_are_not_stars` |
| Le stelle sono quelle che conta il SubframeSelector: una stella debole o una macchia di nebulosa larga non conta (Marco, 27/10/2026) <!-- software-ok --> | `test_the_frame_counts_the_stars_the_subframeselector_would`, `test_a_star_over_the_aperture_threshold_is_found_one_under_is_not`, `test_a_wide_faint_patch_is_not_a_star_however_much_light_it_holds`, `test_a_hot_pixel_is_not_a_star`, `test_a_dark_pixel_among_bright_ones_has_a_position`, `test_a_structure_starts_at_its_threshold_on_the_median_copy`, `test_the_position_is_the_barycentre` (`backend/tests/test_pipeline_detect.py`) <!-- software-ok --> |
| Una stella saturata conta fra le stelle ma non entra nell'HFD, anche se in una camera a colori satura un canale solo | `test_saturated_stars_are_counted_but_not_measured`, `test_a_colour_star_clipped_in_one_channel_is_saturated` |
| Il tetto di saturazione e' dove la camera taglia davvero, anche sotto il massimo del tipo (Canon a 61208), e quante stelle ci arrivano | `test_the_ceiling_is_the_pile_at_the_top_of_the_histogram_not_the_maximum`, `test_twelve_bits_in_sixteen_clip_at_their_own_top`, `test_a_smooth_bright_patch_is_not_a_pile`, `test_stars_at_the_ceiling_are_counted_saturated_and_kept_out` (`backend/tests/test_pipeline_field.py`) |
| Il PSF SNR e' quello della documentazione di PixInsight, sature comprese come le tiene lui <!-- software-ok --> | `test_psf_snr_is_the_documented_formula`, `test_the_frame_psf_flux_is_the_stars_flux_over_their_structures`, `test_saturated_stars_stay_in_the_psf_flux_clipped_as_they_are`, `test_under_five_stars_no_psf_snr` |
| Il gradiente del fondo dice quanto e verso dove; un fondo piatto o a zero non inventa un lato | `test_a_sky_on_a_plane_gives_its_spread_over_its_median_and_its_bright_side`, `test_the_bright_side_turns_with_the_plane`, `test_a_flat_sky_has_no_gradient_and_no_side`, `test_a_sky_at_zero_or_under_has_no_gradient` |
| Tilt e curvatura dalle cinque zone, e tacciono con poche stelle in una zona | `test_tilt_is_worst_less_best_corner_over_the_median_hfd`, `test_curvature_is_corners_against_the_centre_with_its_sign`, `test_a_zone_with_too_few_stars_leaves_tilt_and_curvature_silent`, `test_tilt_reaches_the_frame_through_measure` |
| La massa d'aria e' quella dell'oggetto a meta' posa, con l'aria che lo alza, finita all'orizzonte e nessuna sotto | `test_the_airmass_is_pickering_on_the_apparent_altitude`, `test_the_refraction_lifts_a_low_star_saemundsson`, `test_under_the_horizon_there_is_no_airmass`, `test_the_altitude_agrees_with_astropy` (`backend/tests/test_pipeline_airmass.py`, `test_pipeline_altitude.py`) |
| FWHM e HFD anche in secondi d'arco dalla scala risolta e allo zenit; senza soluzione niente secondi, senza sito o ora niente altezza ne' zenit | `test_a_solved_shot_gets_its_airmass_arcseconds_and_zenith_values`, `test_a_value_at_the_zenith_is_divided_by_the_airmass_to_the_three_fifths`, `test_without_a_site_there_is_no_altitude_but_the_arcseconds_stay`, `test_without_a_start_there_is_no_time_nor_altitude`, `test_the_mid_exposure_is_the_start_plus_half` (`backend/tests/test_pipeline_sky_measure.py`) |
| La direzione delle stelle e il lato chiaro del gradiente girati col cielo: "in AR" o "in Dec" | `test_a_pixel_direction_turns_into_its_position_angle_on_the_sky` (`test_pipeline_footprint.py`), `test_the_shape_and_the_bright_side_turn_with_the_sky`, `test_the_nearer_sky_axis_names_the_direction`, `test_a_solution_without_its_matrix_gives_arcseconds_but_no_direction`, `test_round_stars_and_a_flat_sky_have_no_direction` |
| Una soluzione arrivata dopo la misura riscrive le misure col cielo, una dimenticata le porta via | `test_an_unsolved_shot_takes_its_altitude_from_the_card_then_its_solution`, `test_a_forgotten_solution_takes_its_sky_measures_along`, `test_an_unreadable_measure_waits`, `test_a_stop_writes_nothing` |
| Una nebulosa sotto le stelle e' cielo, non stella | `test_a_nebula_under_the_stars_is_sky_the_ring_follows` |
| Una camera a colori si misura come in WBPP, dopo il debayer VNG, in pixel del sensore, anche con stelle piccole | `test_a_colour_frame_is_measured_after_vng_in_sensor_pixels`, `test_a_colour_camera_is_measured_after_its_debayer`, `test_a_colour_matrix_not_rgb_is_not_measured` |
| A colori il rumore e' quello che dice WBPP, canale per canale | `test_colour_noise_is_the_mid_of_the_cfa_channels_as_pixinsight_says_it` <!-- software-ok --> |
| Il debayer e' quello di PixInsight, pixel per pixel, col pattern letto come lo legge lui | `test_vng_is_pixinsights_pixel_for_pixel`, `test_the_pattern_is_read_as_pixinsights_auto` (`backend/tests/test_pipeline_debayer.py`) <!-- software-ok --> |
| Un frame con troppo poche stelle (nuvole, frame di prova) lo dice, e il numero dell'HFD tace | `test_a_frame_without_enough_stars_says_so_and_keeps_the_count`, `test_a_cloudy_frame_keeps_its_stars_and_says_too_few`, `test_a_frame_of_one_adu_steps_has_no_stars_in_its_steps` |
| Un file che non si legge ora si riprova; uno che non e' un'immagine da misurare lo dice | `test_a_file_unreadable_now_is_tried_again`, `test_a_frame_too_small_to_measure_says_so`, `test_a_cut_file_a_missing_one_and_a_compressed_one_say_why` (`backend/tests/test_pipeline_pixels.py`) |
| Una fermata ferma la misura fra un frame e l'altro | `test_a_stop_measures_nothing_more` |
| HFD e stelle non costano una seconda passata di ASTAP | `test_a_cached_sky_launches_nothing_at_all` (`backend/tests/test_solve.py`) |

## Le decisioni

**Dove.** I pixel li leggiamo noi (`pipeline/pixels.py`), in sola lettura: FITS non compresso,
immagine primaria a due assi, BITPIX 8/16/32 con BZERO e BSCALE (FITS 4.0, sez. 5.3). Niente file
accanto ai FITS. Sotto 20 pixel di lato non e' un frame da misurare (`not_supported`, da
`old/misura.py`); un `.fz` aspetta (`fz_unsupported`), come in `solve` prima di ASTAP 2026.07.17.

**Quali frame.** I light presenti, uno per posa: il file semplice prima della sua copia fpack
(`pipeline/shots.py`, lo stesso ordine di `solve`). `unreadable` si riprova al giro dopo; gli
altri esiti restano. Un frame alla volta: il parallelo si misura quando servira'.

**Il metodo** (ADR 0022, punti 1, 2, 3, 7, 8, 9; ADR 0033, D1):

- **Camera a colori** (la scheda dice `BAYERPAT`; Marco, 26/10/2026, ADR 0022 punto 6) come
  WBPP: debayer VNG a piena risoluzione (`pipeline/debayer.py`, il VNGThread di PixInsight portato <!-- software-ok -->
  termine per termine, bordo di 2 pixel copiato dal vicino), poi tutto sull'intensita' HSI
  (min + max) / 2, il piano su cui misura il SubframeSelector. Pattern da `BAYERPAT`, una colonna
  in piu' con `XBAYROFF` dispari e una riga con `YBAYROFF` dispari; `ROWORDER` non si legge (come
  l'Auto del Debayer; sui 4 frame veri il verde sta dove lo dice `BAYERPAT`). Una matrice non
  R G B (CYGM): `not_supported`. La saturazione si guarda sul pixel del sensore: il debayer
  nasconde un verde saturato. Scheda muta: mono.
- **Fondo**: `sep.Background`. **Rumore**: 1,4826 x MAD del frame meno il fondo, a piena
  risoluzione (Rousseeuw e Croux 1993; `units.sigma_from_mad`). A colori quello che dice WBPP:
  per piano R, G (media dei due), B a mezza risoluzione, come lo stima il Debayer, poi (min +
  max) / 2 come il SubframeSelector; le stelle si cercano col rumore dell'intensita'. Non si
  confronta con la mono. Mai sotto un
  gradino da 1 ADU, 1/sqrt(12): un cielo quantizzato ha MAD 0 e ogni gradino diventava stella.
- **Stelle** (`pipeline/detect.py`, passo 25.15): **quelle che conta il SubframeSelector** <!-- software-ok -->
  (Marco, 27/10/2026), riscritto dalla sua documentazione pubblica (lo StarDetector della PCL:
  filtro mediano dei pixel caldi, strutture, segnale sul fondo in unita' di dispersione) e tarato
  a scatola chiusa sulle sue uscite, mai sul sorgente PCL. Struttura: i pixel della copia
  mediana 3x3 sopra 2,4 sigma, uniti in 8 direzioni; la sua mappa delle strutture
  (`StarDetectionPreview`) sui 24 frame parte da 2,3-2,5. Stella: la struttura il cui miglior
  quadrato 2x2 sul residuo grezzo supera 17,25 volte il rumore di quattro pixel. Una stella per
  struttura: due che si toccano contano una. Tarato sulle 12 copie pari contro il conteggio del
  SubframeSelector, provato sulle 12 dispari: mediana 1,00, da 0,98 a 1,12; stella per stella,
  contro i segni della sua anteprima, F1 0,93. Il picco sulla copia mediana seguiva la FWHM del
  frame (correlazione 0,90: le stelle piccole perdevano il picco nella mediana), 1 px e 3 px pure
  (-0,80 e 0,78); il quadrato 2x2 no (-0,25). Prima (`sep.extract` a 5 sigma) era da 0,36 a 1,34
  volte il suo. Fuori dal conteggio la selezione per HFD e forma: resta su `sep`, sotto. Il
  numero sale, nella mediana circa il doppio di prima. 0,3 s a frame da 26 MP.
- **Rilevamenti per la misura**: `sep.extract` a 5 sigma (Siril) sulla copia filtrata con <!-- software-ok -->
  mediana 3x3 esatta: i pixel caldi spariscono, le stelle restano; i suoi momenti sono la scala
  di bordo, vicine e finestre.
- **Tetto e stelle sature** (`pipeline/ceiling.py`, passo 25.2; ADR 0022 punto 7): un sensore
  tagliato ammucchia i pixel piu' chiari su un valore solo. Il tetto e' il valore piu' basso
  della pila piu' alta fra i pixel sopra il 99,9° percentile: almeno 4 pixel su quel valore e
  almeno 10 volte la mediana dei conteggi degli 8 valori presenti appena sotto (cosi' regge 8 bit
  e 12 bit in 16); valori entro lo 0,1% sono una pila. Nessuna pila: `DATAMAX`, o il massimo del
  tipo di dato. Sulle 24 copie: ATR2600M a 65535 (da 64 a 4050 pixel, vicini da 1 a 4), Canon
  700D a 61208/61212 con pochi pixel isolati sopra fino a 65532: il massimo avrebbe sbagliato.
  Una nebulosa liscia ha molti pixel per valore anche nei vicini: non e' una pila. **Satura** una
  stella del conteggio con almeno 2 pixel del sensore al tetto (uno e' un pixel caldo dentro la
  stella); a colori si guarda il mosaico. Il debayer taglia invece al fondo scala dichiarato,
  come quello di PixInsight. Fuori: un light diviso per il flat o col dark sottratto non ha pila, <!-- software-ok -->
  il tetto resta quello dichiarato e le sature si perdono. Il tetto e' per frame: un frame Canon
  senza stelle tagliate dice 65535.
- **Stelle tenute**: intere (`flag` 0), picco sotto il 90% del tetto, lontane dal bordo e dalle vicine piu' di 3 FWHM stimate dai momenti
  di `sep`. Per l'HFD anche b/a sopra 0,5 (Siril); la forma le prende tutte, se no un frame <!-- software-ok -->
  mosso non ne ha (Marco, 27/10). SubframeSelector fa lo stesso fino a b/a 0,3-0,4: oltre, il suo <!-- software-ok -->
  `maxDistortion` 0,6 scarta le stelle e tace; noi diciamo 0,95-0,98 (misurato, 14 frame
  sintetici da b/a 1 a 0,2). Al massimo 60 per casella di una griglia 3x3, prese lungo tutta la classifica
  del flusso. La stima dai momenti sta circa 1,6 volte sopra la FWHM vera: e' una scala per
  bordo, vicine e finestre, non una misura.
- **HFD**: diametro col meta' flusso dentro un'apertura di 3 FWHM stimate, con `sep.sum_circle`
  su 96 raggi e interpolazione; il valore del frame e' la mediana. **Fondo locale: mediana
  dell'anello** da 1 a 1,5 aperture **sulla copia filtrata**, senza maschera dei segmenti. ADR
  0022 diceva "media dell'anello a oggetti mascherati": sul vero (Rosetta, Canon 700D) la
  maschera copriva l'anello con la nebulosa e il fondo restava zero (HFD 12,3 px contro 4,0 di
  ASTAP). La copia filtrata toglie i pixel caldi (per cui ADR 0022 scartava la mediana), la
  mediana toglie le vicine. `sep.flux_radius` non ha l'anello: non si usa.
- **Forma** (ADR 0022 punto 4, `pipeline/shape.py`): per stella una Moffat ellittica
  A (1 + (x'/ax)^2 + (y'/ay)^2)^-beta, beta libero fra 1,01 e 100, integrata sul pixel (5x5
  campioni a stima sotto 3 px, 3x3 sotto 6, uno sopra), col fondo fisso alla mediana dell'anello
  sulla copia filtrata (libero si mangiava le ali: FWHM +4%), su un cerchio di 2 FWHM stimate,
  pixel caldi fuori dal nucleo tolti. Levenberg-Marquardt di scipy (MINPACK) con lo jacobiano
  scritto, al piu' 400 valutazioni. Per stella FWHM = 2 sqrt(ax ay) sqrt(2^(1/beta) - 1), la
  media geometrica dei due assi; eccentricita' sqrt(1 - (b/a)^2); asse lungo da +x (colonne)
  verso +y (righe), da 0 a 180 gradi. Per il frame la mediana delle stelle.
  - **Fit** (`fitted`) quando regge almeno meta' delle stelle e almeno 5; se no **stimata**
    (`estimated`) dai momenti di `sep`, che leggono le ali: su una Moffat beta 3 la FWHM esce
    1,5 volte la vera. **Non misurabile** (`unmeasurable`) se piu' di meta' sono ciambelle
    (centro sotto l'anello di 3 rumori) o se l'eccentricita' arriva a 0,99; FWHM ed
    eccentricita' tacciono. Le righe vere arrivano qui di rado: `sep` le spezza in pezzi vicini
    e il frame dice troppo poche stelle.
  - **Direzione** solo da eccentricita' 0,4 e se le stelle sono d'accordo: media assiale degli
    angoli (gli angoli raddoppiati sul cerchio, Mardia 1972), lunghezza almeno 0,5; coma e tilt
    allungano in raggiera e la direzione tace. Si scrive sui pixel e girata col cielo (sotto,
    **Col cielo**).
  - **Colori**: sull'intensita' dopo VNG, come WBPP; VNG allarga le stelle piccole, come le
    vede il SubframeSelector: FWHM 4 px +2%, 3 px +8%, 2 px +27% (l'HFD +4%).
- **PSF SNR** (`pipeline/field.py`, ADR 0022 punto 5): ImageWeighting di PixInsight, eq. 7 e <!-- software-ok -->
  18-19, PSF SNR = 1,350e-7 F^2 / (4,987e6 sigma^2); F e' la somma dei flussi di tutte le
  stelle del conteggio, sature comprese (il SubframeSelector le tiene: il suo limite e' il fondo
  scala), sigma il rumore scritto. PixInsight integra ogni stella nella regione al decimo del <!-- software-ok -->
  massimo del suo fit; noi sommiamo il residuo sulla struttura della stella (`detect.py`), per una
  costante tarata a scatola chiusa (sotto). Una PSF sola per il frame, nel cerchio al decimo del
  massimo, dava da 0,06 a 0,42 volte il suo PSF SNR sui mono: le stelle chiare e sature, larghe,
  portano gran parte del flusso, e il loro fit e' largo. Sotto 5 stelle tace. Mai fra camere o
  oggetti.
- **Gradiente** (ADR 0022 punto 7): la mappa del fondo di `sep` ai centri delle sue maglie da
  64 pixel, (max - min) / mediana in %. Il **lato chiaro**: la pendenza del piano dei minimi
  quadrati, da +x verso +y, 0-360 gradi, solo quando il piano spiega almeno meta' della varianza
  della mappa (la vignettatura ha un'ampiezza e nessun lato). Convenzione nostra: nessun programma
  da' un numero solo. Il fondo dei light non calibrati porta l'offset della camera: solo stessa
  camera; un fondo a zero o sotto non ha percentuale.
- **Tilt e curvatura** (ADR 0037): HFD mediana nelle quattro caselle d'angolo e in quella
  centrale della griglia 3x3 (le zone 1A, 3A, 1C, 3C e 2B di ASTAP). Tilt = 100 (angolo peggiore
  - migliore) / HFD mediana del frame (hnsky.org/astap.htm). Curvatura = 100 (mediana dei quattro
  angoli - centro) / HFD mediana, col segno: positiva se gli angoli sono peggiori (l'"off-axis
  aberration" di ASTAP, sulle zone). Almeno 25 stelle per zona, se no tacciono: peggiore meno
  migliore di quattro mediane non e' mai sotto zero, e a 5 stelle per zona un sensore piano
  leggeva il 15%. Solo con l'HFD (`measured`), sulle sue stelle tonde (b/a sopra 0,5): su un
  frame mosso le zone restano povere e tilt e curvatura tacciono.
- **Col cielo** (`pipeline/sky_measure.py`, stadio `sky` dopo `measure`; ADR 0022 punti 5 e 7):
  le misure dei pixel con la soluzione di `solve`, il sito e l'ora della scheda del file misurato,
  in `pipeline_sky`. Una posa senza soluzione si scrive subito e si riscrive quando la soluzione
  arriva; `solve.forget` porta via la sua riga. Nessun pixel letto: un conto erfa e una
  scrittura per cartella; una fermata vale prima del conto. Il confronto calcola l'altezza con
  la stessa funzione (`apparent_altitudes`).
  - **Ora**: meta' posa, inizio piu' meta' di `EXPTIME`; posa ignota, l'inizio.
  - **Altezza** del centro risolto, se no del puntamento della scheda (anche il bersaglio
    pianificato: per la massa d'aria basta il grado; in un mosaico sbaglia di qualche grado), dal
    sito scritto nella scheda e solo da quello: il sito di default non si indovina per un
    viaggio. Geometrica con erfa (`pipeline/altitude.py`; astropy no, ADR 0030; UT1 come UTC,
    sotto un centesimo di grado), poi la rifrazione di Saemundsson a 1010 hPa e 10 C (Meeus
    1998, eq. 16.4): 29' all'orizzonte, 1' a 45 gradi; sotto -1 grado niente. La quota del sito
    non c'e' nella scheda.
  - **Massa d'aria**: Pickering 2002 (DIO 12(1) 20-39), X = 1 / sin(h + 244 / (165 + 47 h^1,1))
    sull'altezza apparente: 1 allo zenit, 1,99 a 30 gradi, 38,7 all'orizzonte, nessuna sotto.
    La stessa che usera' lo SQM (ADR 0022). Solo il numero, nessun giudizio (ADR 0022).
  - **Secondi d'arco**: FWHM e HFD per la scala risolta, pixel del file come l'HFD (anche a
    colori e in binning). Un derivato scritto accanto al suo pixel: una lettura non calcola.
  - **Allo zenit**: secondi d'arco / X^0,6 (ESO, seeing di La Silla: seeing allo zenit = misurato
    / airmass^0,6). La legge e' del seeing; FWHM e HFD portano anche ottica e guida, e basso
    sull'orizzonte la correzione esagera: il frame 23 a 14 gradi (X 4,1) da 6,9" torna 3,0".
  - **Girati col cielo**: la direzione della forma e il lato chiaro come angolo di posizione, da
    Nord verso Est, dalla matrice CD della soluzione (Calabretta e Greisen 2002: (est, nord) = CD
    per la direzione sui pixel del file come salvati, come measure li legge; `ROWORDER` non
    entra, ma nessun file BOTTOM-UP vero e' misurato). Lo specchio non cambia un asse. "In AR"
    se l'asse sta piu' vicino a Est-Ovest (angolo di posizione fra 45 e 135, estremi esclusi),
    se no "in Dec".
    Senza CD (ASTAP non l'ha scritta intera) niente giro; la `rotation_deg` della soluzione e'
    l'angolo CROTA2, di segno opposto al nostro.
- **Poche stelle**: sotto 5 stelle tenute, `too_few_stars`: il numero delle stelle resta,
  l'HFD tace. La forma c'e' anche li', se le stelle di ogni rotondita' sono almeno 5: un frame
  mosso dice quanto. Sui 24 frame veri la meno ricca ne tiene 291.
- **Non e' riproducibile bit per bit**: `sep` separa le stelle che si toccano con un passo a
  caso; lo stesso frame rimisurato cambia di pochi decimi per cento (stelle 1565/1566, HFD 3,486
  contro 3,478 px, audit del 26/10/2026). I test non chiedono conteggi esatti su stelle unite.

**Le misure sul vero** (26/10/2026, 24 light copiati dall'archivio di Marco: ATR2600M L, R, G,
B, Ha, OIII, SII; Poseidon-C Pro; Canon 700D):

- **Stelle iniettate** di forma nota sui fondi veri (Rosetta, M31, Ha, L): mediana dell'HFD
  entro l'1% dalla verita', P90 da +7 a +23%. Forma (27/10/2026, 150 Moffat ellittiche beta 3,
  b/a 0,7, picco 100 rumori, su tutti i 24): FWHM da +0,2 a +0,7%, eccentricita' 0,710-0,716
  contro 0,714. Sui 4 a colori iniettate dopo VNG: provano il fit sul fondo vero, non VNG
  (quello lo misura la riga dei colori sotto, su stelle sintetiche).
- **Contro i programmi di riferimento**: `python tools/confronto_misure.py CARTELLA` misura le
  copie con measure, con `astap_cli -analyse 30` e col SubframeSelector di PixInsight senza <!-- software-ok -->
  finestra, e stampa il nostro diviso il loro (minimo / mediana / massimo), mono e colori a
  parte; i colori li passa prima al Debayer VNG di PixInsight col pattern Auto, come WBPP. Si <!-- software-ok -->
  rilancia a ogni sottopasso di measure, e ogni misura che il SubframeSelector da' si confronta
  con la sua (Marco, 27/10/2026). Siril no (Marco, 26/10/2026). Sui 24 frame (colori <!-- software-ok -->
  dopo VNG, passo 24.06):

  | Misura | Mono (20) | Colori (4) | Perche' lo scarto |
  |---|---|---|---|
  | Fondo / mediana SubframeSelector | 0,99 / 1,00 / 1,00 | 0,99 / 1,00 / 1,00 | La mediana dell'immagine porta le stelle e la nebulosa, `sep` le toglie |
  | Rumore / rumore SubframeSelector | 1,00 / 1,02 / 1,05 | 1,01 / 1,04 / 1,06 | MAD contro wavelet MRS, stessa cosa. Colori: come il Debayer, per piano R, G (media dei due), B a mezza risoluzione, poi (min + max) / 2 come il SubframeSelector; sull'intensita' sarebbe 0,88-0,96 |
  | HFD / FWHM SubframeSelector | 1,15 / 1,36 / 1,46 | 1,25 / 1,30 / 1,72 | Grandezze diverse: sulla Moffat HFD/FWHM e' 1,36 a beta 2,5 e 1,17 a beta 4 (dalla formula del flusso racchiuso); la gaussiana da' 1 |
  | FWHM / FWHM SubframeSelector | 0,68 / 0,83 / 1,00 | 0,68 / 0,83 / 1,00 | Il SubframeSelector valuta la Moffat al centro del pixel, noi la integriamo (ADR 0022): le stelle piccole gli escono larghe. Ai centri la nostra da' 1,36 contro 1,39 (frame 05), 4,39 contro 4,33 (frame 23); una stella sintetica da 1,0 px integrata torna 1,00, ai centri 1,29. Uguali sopra 4 px. Tenuta l'integrata (27/10/2026) |
  | Eccentricita' / SubframeSelector | 0,93 / 1,02 / 1,10 | 0,99 / 1,05 / 1,07 | Stessa definizione, sqrt(1 - (b/a)^2); a colori VNG allunga di poco le stelle piccole |
  | HFD / HFD ASTAP | 0,71 / 0,83 / 0,94 | 0,78 / 0,83 / 0,89 | ASTAP sta il 6-41% sopra; ADR 0022 lo misurava +8…27% sopra la verita' (il raggio medio). Colori: ASTAP misura il mosaico grezzo. Col superpixel il Canon (frame 15) dava 6,94 px contro 3,97, ora 3,20 |
  | Stelle / stelle ASTAP | 0,94 / 6,20 / 27,79 | 6,76 / 14,47 / 31,56 | ASTAP conta da SNR 30 sul grezzo, noi come il SubframeSelector sull'intensita' a piena risoluzione |
  | Stelle / stelle SubframeSelector | 0,98 / 1,00 / 1,10 | 0,99 / 1,00 / 1,12 | Tarato sul suo conteggio (12 copie pari, prova sulle 12 dispari). Sopra 1,05 due frame: 15 (Canon 700D, 1,12) e 21 (NGC 6888, campo denso a FWHM 1,34, 1,10); il perche' non e' misurato |
  | PSF SNR / PSF SNR SubframeSelector | 0,92 / 1,01 / 1,59 | 19,1 / 22,9 / 2443 | Costante del flusso tarata sulle 10 mono pari (mediana 1,12 a costante 1), prova sulle 10 dispari: mediana 1,01. Sopra 1,3 il frame 23 (FWHM 4,3 px, 265 stelle, 1,59) e il 12 (1,24): stelle larghe, la struttura raccoglie piu' della regione al decimo del massimo. **A colori lo scarto e' aperto**: 19-29 volte il suo, il Canon 15 2443 (il SubframeSelector da' 0,0005); il perche' non e' misurato, non si tara via. Nella colonna 28 della sua tabella; c3 F^2 / (c4 sigma^2) delle colonne 21 e 12 la ridà entro il 3% |

  | Altezza / altezza SubframeSelector | 1,00 / 1,00 / 1,01 | 1,00 / 1,00 / 1,00 | Dal puntamento della scheda, come lo stadio `sky` senza soluzione; scarto da -0,25 a +0,30 gradi sui 22 col sito (i 2 Canon non l'hanno, lui scrive 0). Ne' l'inizio posa ne' l'altezza geometrica lo spiegano (da -0,15 a +0,24 all'inizio); il perche' non e' misurato. 0,3 gradi sopra i 30 gradi sono meno dell'1% di massa d'aria. Colonna 20 della sua tabella |

  ASTAP non da' fondo ne' rumore. Le misure del 25.2 non spostano le altre righe (stesse cifre
  di prima). Il SubframeSelector non da' tetto, sature, gradiente, tilt, curvatura, secondi
  d'arco ne' direzione sul cielo.
- **Le misure nuove sul vero** (27/10/2026, 24 copie): tetto 65535 sui 22 ATR2600M e 61208 sui
  due Canon; sature da 6 a 454 per frame. Gradiente da 2,6 a 45,3% (il 23, nebulosa), il lato
  chiaro solo su 5 frame: sugli altri il piano non spiega la mappa. Tilt da 0,8 a 77% (il Canon
  18, obiettivo), curvatura da -6,9 a +20%; il 23 tace (265 stelle, sotto 25 per zona). Il tilt
  alto e' vero: diviso a caso in due meta' delle stelle, le zone tornano entro 0,1 px (frame 00,
  05, 07: l'angolo in alto a sinistra peggiore; il 20, piano, 0,8%).
- **Col cielo sul vero** (28/10/2026, pipeline intera sulle 24 copie con ASTAP, 124 s compreso
  il solve): 23 risolte, il Canon 15 no (secondi d'arco muti, niente sito). Altezza da 13,9 a
  86,3 gradi, massa d'aria da 1,00 a 4,11; scala 1,38"/px sugli ATR2600M e Poseidon, 1,58 sul
  Canon 18 (senza sito: secondi si', zenit no). HFD da 2,58" a 6,89", allo zenit da 2,41" a
  3,95". Direzione su 17 frame: 14 "in AR", 3 "in Dec"; lato chiaro su 5 frame.
- **Tempo** (27/10/2026, con la forma): da 1,9 a 4,1 s a frame da 26 MP mono; a colori da 6,1 a
  8,8 s, di cui il debayer 3,6-5 s; la forma da 0,6 a 1,6 s, su 291-540 stelle. Un processo, su
  copia locale. Senza il tetto di 60 per casella un campo denso arrivava a 7,9 s. Il conteggio
  come il SubframeSelector aggiunge 0,3 s (passo 25.15). <!-- software-ok --> Col 25.2: da 2,0 a
  4,1 s mono, da 5,6 a 7,8 s a colori.

**Cosa si scrive** (`pipeline_measures`): esito, stelle, stelle tenute, HFD in pixel del
sensore, fondo e rumore in ADU; la forma (fit, stimata, non misurabile) con le sue stelle, FWHM
in pixel, eccentricita' e direzione; il tetto e le stelle sature, il PSF SNR, il gradiente col
lato chiaro, tilt e curvatura; durata, ora. In `pipeline_sky`: se risolta, meta' posa, altezza,
massa d'aria, FWHM e HFD in secondi d'arco e allo zenit, direzione e lato chiaro sul cielo con
l'asse. In `pipeline_solutions` la matrice CD. Il fondo si confronta solo con la stessa camera,
guadagno e posa (ADR 0022). Le misure scritte negli header da altri programmi non si leggono.

**La pipeline vecchia** non lancia piu' `-analyse` (D1, +0,3 s a frame) e non ha piu'
`frame_metrics`: nessuno la leggeva, e un `-analyse` che non rispondeva si richiedeva a ogni giro.

## I testi a schermo

Approvati (Marco, 18/10/2026; da `notti.md`): "misura in corso" (non ancora misurato); "troppo
poche stelle" (non misurabile, il numero tace); forma stimata, quando il fit non riesce, detta
sulla riga; senza scala del cielo FWHM e HFD in px e niente zenit; senza sito o coordinate
dell'oggetto niente zenit; le mediane solo sui frame misurati, con quanti ("su 112 di 120
frame"). FWHM e HFD sempre in due unita', secondi d'arco e pixel. Per notte e filtro la mediana
di ogni misura, e un grafico della FWHM frame per frame con l'altezza dell'oggetto sullo stesso
asse del tempo. La curva dello SQM lungo la notte porta l'altezza della Luna sullo stesso asse,
con "il valore cambia anche con la direzione del cielo" accanto, e "nessun frame L o a colori in
questa notte" quando manca; una camera a colori senza bias non ha SQM e dice "serve il bias
della camera", col rimando a "Bias (ADU)" in Attrezzatura. Parole del campionamento ancora da
approvare sulla tavola: "sottocampionata (grave)", "sottocampionata", "ideale",
"sovracampionata". Dove si vedono: Notti, Archivio, Statistiche, Selezione dei frame; la scheda
dell'oggetto no.

## Cosa non fa ancora, e con cosa arrivera'

- **25.3**: SQM col metodo di ASTAP portato, il lettore del catalogo D80, il bias della camera.
- **26-27**: soglie relative (Qn), eccentricita' rispetto al setup, Bortle del sito, oggetto basso.
- **A schermo**: col porting delle pagine (fase 5). Le tavole di Design (`handoff/design/`,
  26/10/2026) chiedono le stesse misure; quattro scarti vanno al censimento (passo 24.1):
  eccentricita' a soglie fisse 0,45/0,71 (ADR 0039 le ha tolte), soglia relativa con la MAD
  invece di Qn, "oggetto basso" solo sotto 30 gradi (ADR 0039: 30 estesi, 45 stelle), SQM per ora
  in Statistiche.
- `.fz` compressi, cubi e immagini in estensione non si misurano.
