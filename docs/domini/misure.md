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
| Il tetto di saturazione e' il fondo scala dichiarato, come PixInsight, e satura e' una stella con un pixel li' (Marco, 29/10/2026) <!-- software-ok --> | `test_the_ceiling_is_the_declared_full_scale_as_pixinsight`, `test_stars_at_the_ceiling_are_counted_saturated_and_kept_out` (`backend/tests/test_pipeline_field.py`), `test_one_sensor_pixel_at_the_ceiling_makes_a_star_saturated` (`backend/tests/test_pipeline_detect.py`) |
| Il PSF SNR e' quello della documentazione di PixInsight, sature comprese come le tiene lui <!-- software-ok --> | `test_psf_snr_is_the_documented_formula`, `test_the_frame_psf_snr_takes_the_stars_flux_with_no_scale`, `test_saturated_stars_stay_in_the_psf_flux_clipped_as_they_are`, `test_a_colour_psf_snr_takes_the_intensity_noise_not_the_written_one`, `test_under_five_stars_no_psf_snr`, `test_pipeline_psf_flux.py` (quota Moffat al decimo, fondo lasciato sotto le stelle, luce col centro al buio, stella tagliata) |
| Il rumore e' l'MRS di Starck e Murtagh, come lo dichiara PixInsight; nei campi densi resta quello del cielo <!-- software-ok --> | `test_pipeline_noise.py` (fattore del primo strato 0,8908 come Duchamp, trasformata che si ricompone, rumore gaussiano letto entro il 2%, campo affollato e nebulosa entro il 3%), `test_in_a_crowded_field_the_noise_is_read_off_the_stars` |
| Il gradiente del fondo dice quanto e verso dove; un fondo piatto o a zero non inventa un lato | `test_a_sky_on_a_plane_gives_its_spread_over_its_median_and_its_bright_side`, `test_the_bright_side_turns_with_the_plane`, `test_a_flat_sky_has_no_gradient_and_no_side`, `test_a_sky_at_zero_or_under_has_no_gradient` |
| Tilt e curvatura dalle cinque zone, e tacciono con poche stelle in una zona | `test_tilt_is_worst_less_best_corner_over_the_median_hfd`, `test_curvature_is_corners_against_the_centre_with_its_sign`, `test_the_stars_a_zone_needs_follow_the_frame_s_own_hfd_spread`, `test_never_under_min_stars_a_zone`, `test_tilt_reaches_the_frame_through_measure` |
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
| La luminosita' del cielo (SQM) e' quella di ASTAP: zero point dalle stelle del catalogo, cielo dalla moda dell'istogramma | `test_the_zero_point_and_the_sky_come_back`, `test_the_sky_is_the_histogram_mode`, `test_a_mean_far_above_the_mode_wins`, `test_the_mode_leaves_out_the_frame_borders`, `test_star_flux_sums_the_star_over_its_ring`, `test_the_best_mean_drops_outliers_and_weighs_by_snr`, `test_the_sky_brightness_formula`, `test_the_brightest_stars_near_the_frame_top_are_left_out` (`backend/tests/test_pipeline_sqm.py`) |
| Il catalogo e' quello che ASTAP ha gia' installato, letto come lo legge lui | `test_the_documented_star_decodes_to_sirius`, `test_a_position_falls_in_its_area`, `test_a_field_on_the_corner_of_four_areas_shares_its_quota`, `test_the_window_keeps_the_square_around_the_centre`, `test_the_catalogue_is_the_first_gaia_bp_one_in_astaps_order`, `test_the_real_d80_reads_bright_to_faint` (`backend/tests/test_pipeline_star_catalogue.py`) |
| Lo SQM solo su mono col filtro L e su camere a colori (Marco, 28/10/2026); senza catalogo le pose aspettano | `test_a_mono_shot_counts_only_with_the_l_filter`, `test_a_colour_shot_behind_a_narrow_filter_does_not_count`, `test_your_own_l_filter_counts`, `test_without_a_catalogue_shots_wait` (`backend/tests/test_pipeline_sqm_measure.py`) |
| Il bias della camera a quell'offset si toglie al cielo (Marco, 28/10/2026); dichiarato dopo riscrive le sue pose; a colori senza bias lo SQM tace | `test_a_bias_declared_before_is_taken_off`, `test_a_bias_declared_after_rewrites_the_shots_of_that_camera_and_offset`, `test_a_colour_shot_needs_the_bias`, `test_a_bias_over_the_sky_leaves_no_brightness`, `test_a_mono_l_shot_gets_its_sky_brightness_without_bias` |
| Senza altezza (sito, ora, sotto l'orizzonte) lo SQM lo dice senza leggere i pixel; una soluzione dimenticata lo porta via | `test_a_shot_without_altitude_is_said_without_reading_it`, `test_a_forgotten_solution_takes_the_sky_brightness_with_it`, `test_a_shot_waits_for_its_sky_row` |

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
- **Fondo**: `sep.Background`. **Rumore** (`pipeline/noise.py`, passo 26.45): il supporto
  multirisoluzione di Starck e Murtagh (1998, PASP 110:193), lo stimatore che PixInsight dichiara <!-- software-ok -->
  (ImageWeighting par. 2.4, 3.1.2): trasformata a trous B3 sui primi 4 strati, pixel fuori dal
  supporto a 3 sigma, iterato fino a fermarsi, diviso per 0,974. Sui 205 frame del passo 26.45
  da 0,996 a 1,004 volte il suo, senza tarature; la MAD di prima arrivava a 1,24 nei campi da
  40 mila stelle (le ali entravano nel conto). Le stelle si cercano ancora col primo passaggio
  (1,4826 MAD), la soglia e' misurata con quello. A colori quello che dice WBPP: per piano R, G
  (media dei due), B a mezza risoluzione, come lo stima il Debayer, poi (min + max) / 2 come il
  SubframeSelector. Non si confronta con la mono. Mai sotto un gradino da 1 ADU, 1/sqrt(12).
  Costa da 1,3 a 3,2 s a frame (dal 30/10 i tap del B3 senza gli zeri: 1,4 s su 26 MP).
- **Stelle** (`pipeline/detect.py`, passo 25.15): **quelle che conta il SubframeSelector** <!-- software-ok -->
  (Marco, 27/10/2026), riscritto dalla sua documentazione pubblica (lo StarDetector della PCL:
  filtro mediano dei pixel caldi, strutture, segnale sul fondo in unita' di dispersione) e tarato
  a scatola chiusa sulle sue uscite, mai sul sorgente PCL. Struttura (passo 26.46): i pixel
  dove i primi 5 strati a trous della copia mediana 3x3 (I - c5, scale fino a 32 px:
  `structureLayers` 5 dello StarDetector, default del SubframeSelector) superano 3 volte la
  loro dispersione, la significativita' di Starck e Murtagh (come il supporto del rumore),
  uniti in 8 direzioni. Una struttura che copre meno di (1 - 0,6) pi / 4 del quadrato
  circoscritto (`maxDistortion` 0,6: un disco ne copre pi / 4) non e' una stella: scie, coppie
  unite da un ponte, nodi di nebulosa irregolari. Prima (passo 25.15) i pixel della copia
  mediana sopra 3 sigma: un nucleo di nebulosa o una chioma e la stella sopra erano una
  struttura sola. Stella: la struttura il cui miglior quadrato 2x2 sul residuo
  grezzo supera 16,85 volte il rumore di quattro pixel. Una stella per struttura: due che si
  toccano contano una. Sulle sonde a verita' nota l'errore fra 2,4 e 3 sigma cambia dell'1,5%:
  si tiene la convenzione. Sui 164 frame nitidi le stelle restano 0,99-1,03 per camera (M42
  1,13: il nucleo si spezza in nodi piccoli che lui non conta). Il quadrato 2x2: sulle stesse sonde la sua soglia varia 1,18 volte
  da FWHM 1,5 a 6, quella di 1 px 1,48 e di 3 px 1,64. **Aperto: le stelle doppie.** La
  documentazione PJSR dello StarDetector (`doc/pjsr/objects/StarDetector`) dice che con
  `allowClusteredSources` spento (default del SubframeSelector, letto dal programma, con
  `structureLayers` 5) una struttura con piu' massimi locali (filtro 5x5, sotto 0,75 del fondo
  scala) non e' una stella. Sonde del passo 26.45, 100 sistemi a frame, FWHM 3: le coppie uguali
  sotto 7 px lui non le conta (noi una), quelle a 9 px le separa sempre, anche brillanti; una
  compagna al 3% a 6 px non gli toglie la principale. Provate le regole documentate (massimi
  sul residuo o sulla copia mediana, strutture su 5 strati a trous): i conteggi si avvicinano
  (IC 405 x07 4054 contro 4053), ma sui 205 frame il PSF SNR scende da circa 0,99 a 0,78-0,94,
  perche' le stelle brillanti con una vicina al 2% a 10 px restano in una struttura con due
  massimi e si scartano; lui le separa con un criterio che non pubblica. Resta la regola di
  prima finche' una convenzione non spiega la separazione. Il 16,85 e' la soglia del SubframeSelector misurata
  su frame sintetici a verita' nota (400 stelle a SNR fissato, FWHM da 1,5 a 6 px: meta' trovate
  a 18,2 / 16,9 / 16,1 / 15,9 / 18,8, mediana 16,85), non sui nostri frame (passo 26.45, Marco
  28/10: niente costanti per far tornare i conti); prima 17,25, tarato sulle copie. Fuori dal
  conteggio la selezione per HFD e forma: resta su `sep`, sotto. 1,0 s a frame da 26 MP (0,3 prima del 26.46).
- **Rilevamenti per la misura**: `sep.extract` a 5 sigma (Siril) sulla copia filtrata con <!-- software-ok -->
  mediana 3x3 esatta, senza deblending (ripartiva a caso i pixel contesi: stesso frame, tilt 10,7
  / 9,1 / 8,4%); i suoi momenti sono la scala di bordo, vicine e finestre.
- **Tetto e stelle sature** (`pipeline/stars.py`, ADR 0041): il tetto e' il fondo scala
  dichiarato, `DATAMAX` o il massimo del tipo dopo `BZERO` e `BSCALE`, come PixInsight <!-- software-ok -->
  (ImageWeighting par. 3.1.1: soglia di saturazione 1,0 del fondo scala). **Satura** una stella <!-- software-ok -->
  del conteggio con almeno un pixel del sensore al tetto (lo stesso par. 3.1.1, e ASTAP); a
  colori si guarda il mosaico. Una camera che taglia sotto il fondo scala (la Canon 700D delle
  copie a 61208) non ha sature, li' come qui (Marco, 29/10/2026). Prima (passo 25.2) il tetto
  era una pila cercata nell'istogramma con 5 soglie tarate sulle 24 copie; Chauvenet su
  conteggi di Poisson e' stato provato e non reggeva.
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
    angoli (raddoppiati sul cerchio, Mardia 1972), se Rayleigh rifiuta l'uniforme al 5% (Zar,
    cap. 27; prima lunghezza 0,5, nostra); coma e tilt allungano in raggiera: la direzione tace. Si scrive sui pixel e girata col cielo (sotto,
    **Col cielo**).
  - **Colori**: sull'intensita' dopo VNG, come WBPP; VNG allarga le stelle piccole, come le
    vede il SubframeSelector: FWHM 4 px +2%, 3 px +8%, 2 px +27% (l'HFD +4%).
- **PSF SNR** (`pipeline/field.py`, ADR 0022 punto 5): ImageWeighting di PixInsight, eq. 7 e <!-- software-ok -->
  23-24, PSF SNR = 1,316e-7 F^2 / (4,987e6 sigma^2) (fino al 30/10/2026 1,350e-7, letto male:
  il 2,6% in piu'; ora il suo PSF SNR torna esatto); F e' la somma dei flussi di tutte le
  stelle del conteggio, sature comprese (sui mono toglierle dava 0,13-0,74 volte il suo), sigma
  il rumore del piano misurato: a colori quello dell'intensita', non il rumore scritto (Marco,
  28/10/2026). Il flusso di una stella (`pipeline/psf_flux.py`, passo 26.45), come documenta
  ImageWeighting par. 2.2: i pixel veri nell'ellisse dove la PSF scende a un decimo del picco,
  meno il fondo locale. Lui l'ellisse la prende dal fit; noi dai momenti secondi della struttura
  sulla copia mediana (A, B, THETA di SExtractor, Bertin e Arnouts 1996), raggio sqrt(2 ln 10)
  come per una gaussiana, sommata con `sep.sum_ellipse`; il fondo e' la mediana di un anello di
  24 px appena fuori la struttura (BACKPHOTO_THICK di SExtractor). Nessuna costante. Strutture a
  5 strati (passo 26.46), frame nitidi (HFD sotto 5 px): mediana 0,88 mono e 0,86 colori sul gruppo
  A (sviluppo), 0,87 e 0,83 sul B (verifica); a 3 sigma della copia mediana 0,94 / 0,95 / 0,96 /
  0,91 (con la costante giusta). Cala del 6-9% (struttura e ellisse dei momenti piu' strette), ma
  nessun frame passa 1,00 e gli oggetti estesi rientrano: M42 da 0,56-3,72 a 0,77-0,97, M31 da
  1,14-1,27 a 0,88-0,94, M33 n.1 da 1,35 a 0,88 (Marco, 29/10/2026: la soglia del passo, mediane entro 0,02,
  non regge). Una Moffat beta 4 torna 1,10 / 1,04 / 0,99 della quota al decimo a FWHM 2 / 4 / 6 px.
  Struttura col centro fuori dal proprio decimo: flusso 0 (Canon 15: luce estesa, 83% del nostro F).
  Provate e scartate: PSF Moffat beta 4 per zona (0,12-0,48 volte il suo); regione dentro la
  struttura (0,88); Chauvenet dei flussi (ImageWeighting par. 2.2.1); sature tolte (0,2); tetto di
  32 px, scale piccole, diametro a meta' picco, fit sui candidati: ognuna sistema un caso e ne rompe
  un altro. Al 26.46: strutture a 3 e 4 strati; momenti adattivi (Bernstein e Jarvis 2002; Shark
  0,98 a 0,78); flusso nel decimo di una Moffat beta 4 fittata a stella, che coincide col suo fit
  (ampiezza 87.826 contro 87.816, assi 1,00) ma porta le mediane a 0,75-0,91, 35 frame fuori, e
  diverge sui nuclei. **Limite del confronto**: il suo rilevatore (StarDetector PJSR, stessi
  conteggi: 1028, 278, 741, 1200) coi suoi fit da' 0,84-1,02 del flusso PSF che scrive (colonna 21,
  formula invertita entro l'1,5%), 0,71-1,04 nel PSF SNR: il resto non e' pubblicato (non fondo,
  non modello). **Scarto aperto**: cometa C/2025 A6 0,56-0,65 su tre frame (lui fitta nucleo e
  chioma, 43% del flusso), M51 n.1 0,61 e n.3 0,58 (stelle sdoppiate dalla guida). Frame sfocati:
  NGC 7380 fino a 3,2, IC443 1,5, stelle che lui perde; si tengono le nostre (Marco, 28/10/2026).
  Sotto 5 stelle tace. Mai fra camere o oggetti.
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
  aberration" di ASTAP). Stelle per zona dalla dispersione s delle HFD del frame (MAD relativa):
  su un sensore piano lo scarto fra le quattro mediane d'angolo, d2(4) sqrt(pi/2) s / sqrt(n)
  (d2 2,059, Montgomery), sta nella prima fascia di tilt di ASTAP (0-5%, "nessuno"); mai sotto 5,
  prima 25 fisse. Solo con l'HFD, sulle stelle tonde: su un frame mosso tilt e curvatura tacciono.
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
  con la sua (Marco, 27/10/2026). Siril no (Marco, 26/10/2026). <!-- software-ok -->

  **Scarti del passo 26.46** (29/10/2026; fondo, rumore, FWHM ed eccentricita' dal passo 26.45,
  codice `d2a000e3`, che il 26.46 non tocca): 205 copie da 31 oggetti e 4
  camere (Canon 700D escluso), gruppo A di sviluppo e B di verifica divisi per oggetto
  (`groups.txt` della prova); qui i 164 frame nitidi (HFD sotto 5 px). AstroLog diviso
  SubframeSelector, 10° percentile / mediana / 90° percentile; colori contro il suo valore
  sull'intensita' (min + max) / 2 del Debayer VNG, come la passa WBPP. <!-- software-ok -->

  | Misura | ATR2600M (10) | ATR2600M USB2 (69) | Poseidon-C PRO (80) | ASI2600MC Duo (5) | Perche' lo scarto |
  |---|---|---|---|---|---|
  | Fondo | 1,00 / 1,00 / 1,00 | 1,00 / 1,00 / 1,00 | 1,00 / 1,00 / 1,00 | 1,00 / 1,00 / 1,00 | Nessuno: `sep` toglie stelle e nebulosa, la sua mediana le porta, sul cielo coincidono |
  | Rumore | 1,00 / 1,00 / 1,00 | 1,00 / 1,00 / 1,00 | 1,00 / 1,00 / 1,00 | 1,00 / 1,00 / 1,00 | Nessuno: lo stesso MRS (Starck e Murtagh 1998); a colori per piano come il Debayer |
  | FWHM | 0,77 / 0,79 / 0,86 | 0,71 / 0,86 / 0,98 | 0,69 / 0,89 / 1,03 | 0,90 / 0,96 / 0,98 | Lui valuta la Moffat al centro del pixel, noi la integriamo sul pixel (ADR 0022): le stelle piccole gli escono larghe; una sintetica da 1,0 px integrata torna 1,00, ai centri 1,29; uguali sopra 4 px |
  | Eccentricita' | 1,00 / 1,00 / 1,04 | 1,00 / 1,03 / 1,07 | 1,00 / 1,04 / 1,10 | 1,00 / 1,02 / 1,04 | Stessa definizione, sqrt(1 - (b/a)^2); sulle stelle piccole il fit integrato vede meglio l'asse corto |
  | Stelle | 0,96 / 0,99 / 1,01 | 0,97 / 0,99 / 1,02 | 0,99 / 1,01 / 1,05 | 1,01 / 1,03 / 1,04 | Soglia 16,85 dalla sonda sintetica, strutture su 5 strati a trous. Sopra 1,03 i campi densi a colori (NGC 6888 Poseidon 1,04, IC 405 1,04): lui scarta le strutture con due massimi locali (doppie), noi le contiamo una (sopra, "Aperto: le stelle doppie"); M42 1,13, i nodi del nucleo |
  | PSF SNR | 0,83 / 0,87 / 0,92 | 0,79 / 0,87 / 0,93 | 0,80 / 0,85 / 0,90 | 0,83 / 0,86 / 0,91 | Stessa formula (costante giusta dal 30/10); il flusso noi lo sommiamo nell'ellisse al decimo dei momenti della struttura, piu' stretta di quella della PSF fittata con cui somma lui (ImageWeighting par. 2.2). Il suo flusso non si rifa' meglio di 0,84-1,02 nemmeno col suo rilevatore e i suoi fit (sopra, "Limite del confronto") |

  Per oggetto (mediane, stesso verso; il rumore e' 1,00 ovunque). Il PSF SNR sta fra 0,79 e
  0,94 su ogni oggetto tranne la cometa; le stelle entro 0,97-1,03 tranne dove scritto. Gli
  oggetti estesi del passo 26.46 e i piu' lontani:

  | Oggetto | Camera | Gruppo | Frame | Stelle | PSF SNR | FWHM |
  |---|---|---|---|---|---|---|
  | C/2025 A6 Lemmon (cometa) | ATR2600M USB2 | A | 4 | 0,98 | 0,61 | 0,99 |
  | IC 405 | Poseidon-C PRO | B | 9 | 1,04 | 0,83 | 1,01 |
  | M31 | Poseidon-C PRO | B | 5 | 1,01 | 0,93 | 0,76 |
  | M42 | ATR2600M USB2 | B | 5 | 1,13 | 0,91 | 0,95 |
  | M51 | ATR2600M USB2 | B | 5 | 1,01 | 0,85 | 0,79 |
  | NGC 1333 | Poseidon-C PRO | A | 1 | 1,00 | 0,81 | 1,00 |
  | NGC 6888 | Poseidon-C PRO | A | 5 | 1,04 | 0,89 | 0,67 |
  | NGC 7380 | Poseidon-C PRO | B | 5 | 1,03 | 0,79 | 1,06 |

  Spiegati con la convenzione: fondo, rumore, FWHM (sotto 0,8 le piu' piccole), eccentricita'.
  Aperti: stelle sopra 1,03 nei campi densi (doppie); PSF SNR 0,79-0,94, cometa e M51 (sopra).
  41 frame sfocati (HFD da 5 px): stelle 1,07 / 1,36 / 3,74, PSF SNR 0,82 / 0,90 / 2,13 (Marco, 28/10/2026).

  Dal confronto del 27/10 sulle 24 copie, che il 26.45 non tocca:

  | Misura | Mono (20) | Colori (4) | Perche' lo scarto |
  |---|---|---|---|
  | HFD / FWHM SubframeSelector | 1,15 / 1,36 / 1,46 | 1,25 / 1,30 / 1,72 | Grandezze diverse: sulla Moffat HFD/FWHM e' 1,36 a beta 2,5 e 1,17 a beta 4 (dalla formula del flusso racchiuso); la gaussiana da' 1 |
  | HFD / HFD ASTAP | 0,71 / 0,83 / 0,94 | 0,78 / 0,83 / 0,89 | ASTAP sta il 6-41% sopra; ADR 0022 lo misurava +8…27% sopra la verita' (il raggio medio). Colori: ASTAP misura il mosaico grezzo |
  | Stelle / stelle ASTAP | 0,94 / 6,20 / 27,79 | 6,76 / 14,47 / 31,56 | ASTAP conta da SNR 30 sul grezzo, noi come il SubframeSelector sull'intensita' a piena risoluzione |
  | Altezza / altezza SubframeSelector | 1,00 / 1,00 / 1,01 | 1,00 / 1,00 / 1,00 | Dal puntamento della scheda, come lo stadio `sky` senza soluzione; scarto da -0,25 a +0,30 gradi sui 22 col sito. Ne' l'inizio posa ne' l'altezza geometrica lo spiegano; il perche' non e' misurato. 0,3 gradi sopra i 30 gradi sono meno dell'1% di massa d'aria |

  ASTAP non da' fondo ne' rumore. Il SubframeSelector non da' tetto, sature, gradiente, tilt,
  curvatura, secondi d'arco ne' direzione sul cielo.
- **Le misure nuove sul vero** (27/10/2026, 24 copie; dal 29/10 il tetto e' il fondo scala,
  ADR 0041, e il Canon dice 65535 e 0 sature): tetto 65535 sui 22 ATR2600M e 61208 sui
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
  4,1 s mono, da 5,6 a 7,8 s a colori. Col 26.4 (il flusso al decimo, un anello di fondo per
  stella): da 2,2 a 4,5 s mono, da 5,8 a 8,2 s a colori.

**Lo SQM** (stadio `sqm`, `pipeline/sqm.py` e `star_catalogue.py`, portati dal sorgente di ASTAP,
MPL-2.0; ADR 0022 punto 8):

- **Metodo e soglie di ASTAP**, ognuna col suo tag nel codice: stelle del catalogo nel campo
  risolto, flusso col fondo dall'anello, zero point dalla media pesata, cielo dalla moda,
  SQM = ZP - 2,5 log10((cielo - bias) / scala^2) + 0,2811 X - 0,28. Cataloghi cercati nella
  cartella di ASTAP in quest'ordine: d80, d50, d20, d05; v50 e .290 esclusi (altre bande o altro
  formato). La distorsione SIP non entra: si usa la sola CD.
- **A colori** il superpixel 2x2 col suo intento (media dei quattro); il ciclo di ASTAP scorre a
  passo 1 su un quarto del frame, quel difetto non si porta. Da riga di comando ASTAP non ha un
  riferimento a colori: `astap.exe -sqm` su un frame a colori non chiude in 120 s.
- **Bias**: per camera e offset, `pipeline_camera_bias`; se il cielo non sta sopra il bias lo SQM
  e' NULL (ASTAP azzera il bias e calcola lo stesso). N.I.N.A. e ASIAIR non scrivono `PEDESTAL`.
- **Sul vero** (28/10/2026, `python tools/confronto_sqm.py CARTELLA [--bias ADU]`, contro
  `astap.exe -r 30 -sqm`): 48 frame mono (20 del passo 25 senza bias, 28 del 18/10 con
  `--bias 400`): zero point uguale a MZEROR su tutti entro 0,0001; scarto dello SQM mediana
  0,003 mag, massimo 0,028 (m08; poi n01 0,019, 04 0,011, gli altri sotto 0,01). ASTAP scrive
  due decimali: fino a 0,005 e' arrotondamento. Un frame mono (m14) ASTAP non lo risolve. A
  colori (risolti con `astap_cli`, nessun riferimento): 29 frame Poseidon-C, ASI2600MC Duo,
  Canon 700D, zero point su 25 (da 22,2 a 27,9, da 186 a 3478 stelle), 4 senza soluzione o
  senza altezza; lo SQM aspetta il bias della camera, che non abbiamo.
- **Tempo**: da 0,4 a 1,1 s a frame mono da 26 MP, soluzione data.

**Cosa si scrive** (`pipeline_measures`): esito, stelle, stelle tenute, HFD in pixel del
sensore, fondo e rumore in ADU; la forma (fit, stimata, non misurabile) con le sue stelle, FWHM
in pixel, eccentricita' e direzione; il tetto e le stelle sature, il PSF SNR, il gradiente col
lato chiaro, tilt e curvatura; durata, ora. In `pipeline_sky`: se risolta, meta' posa, altezza,
massa d'aria, FWHM e HFD in secondi d'arco e allo zenit, direzione e lato chiaro sul cielo con
l'asse. In `pipeline_solutions` la matrice CD e il pixel di riferimento. In `pipeline_sqm`:
esito (misurato, calibrazione fallita, senza altezza, illeggibile), catalogo, zero point, stelle
di calibrazione, cielo in ADU, colori, bias tolto, SQM, durata, ora. Il fondo si confronta solo con la stessa camera,
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

## Le regole fra frame (ADR 0039)

Scritte come funzioni pure con i loro test (passo 26); le collega alla pipeline il passo 40, che
porta setup e oggetti. Nessuna misura del frame cambia: il rumore del frame e' l'MRS (sopra),
una scala su milioni di pixel, come il SubframeSelector la confronta.

- **Soglia relativa**: mediana ± 2,5 Qn (`robust.relative_bounds`), sotto 10 valori tace; tace
  anche a Qn zero (valori ripetuti), dove la soglia sarebbe la mediana stessa. Qn di
  Rousseeuw e Croux (JASA 88:1273, 1993), costante 2,21914 = 1/(√2 Φ⁻¹(5/8)) (p. 1277; il 2,2219
  dei primi lavori e' un refuso) e fattori di piccolo campione di robustbase 0.99-7 (tavola fino a
  12, poi polinomio in 1/n, simulazione di Maechler su 2^27 campioni): quelli che vanno con
  2,21914. I fattori del 1992 (n/(n+1,4), n/(n+3,8)) vanno col refuso e non si usano. Il k-esimo
  scarto si sceglie esatto senza la matrice delle coppie: 50.000 valori in 0,04 s.
- **Eccentricita' rispetto al setup** (`pipeline/setup_rules.py`): fuori solo sopra mediana +
  2,5 Qn, una coda (stelle piu' tonde non sono uno scarto); avviso "stelle allungate" se la
  mediana del setup supera 0,6 (b/a 0,8), sotto 10 frame non si dice.
- **Raffiche per setup**: FWHM² = calma² + c v⁴ (ADR 0039) su un punto per ora di meteo (la
  raffica e' oraria), fit di Theil-Sen (Sen 1968: un frame con le nuvole non lo inclina).
  Incerto dove il vento aggiunge una volta calma² (FWHM × √2, tempo doppio), niente dove la
  aggiunge tre volte (FWHM doppia), come il seeing contro il pavimento del setup. Nessuna
  estrapolazione: sotto 10 punti, senza crescita o con la soglia oltre la raffica piu' forte
  misurata resta il 25 km/h (`domini/meteo.md`); "niente" oltre i dati non si dice.

## Cosa non fa ancora, e con cosa arrivera'

- **Bias (ADU) a schermo**: col porting di Attrezzatura (fase 5) e il setup della pipeline
  (passo 40); oggi si dichiara solo da codice (`declare_bias`).
- **Le regole fra frame collegate**: al passo 40 (setup, oggetti) e 40.1 (zona di selezione,
  con "al limite" a 1 Qn). **27**: Bortle del sito, oggetto basso.
- **A schermo**: col porting delle pagine (fase 5). Le tavole di Design (`handoff/design/`,
  26/10/2026) chiedono le stesse misure; quattro scarti vanno al censimento (passo 24.1):
  eccentricita' a soglie fisse 0,45/0,71 (ADR 0039 le ha tolte), soglia relativa con la MAD
  invece di Qn, "oggetto basso" solo sotto 30 gradi (ADR 0039: 30 estesi, 45 stelle), SQM per ora
  in Statistiche.
- `.fz` compressi, cubi e immagini in estensione non si misurano.
