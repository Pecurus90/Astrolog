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
| Le stelle sono quelle che conta Image Analysis: una stella debole, una macchia di nebulosa larga, una sorgente multipla o un nodo su una nebulosa non contano (Marco, 27/10 e 30/10/2026) <!-- software-ok --> | `test_two_peaks_in_one_structure_are_no_star`, `test_a_maximum_is_one_over_the_whole_5x5_not_only_its_structure`, `test_a_saturated_star_with_a_ragged_top_is_one_star`, `test_the_dispersion_that_counts_is_the_local_one`, `test_a_knot_on_a_nebula_is_measured_over_the_nebula`, `test_a_wide_faint_star_is_one_star_not_a_cluster_of_noise_peaks`, `test_a_star_with_no_free_sky_around_falls_back_on_the_frame_noise`, `test_the_frame_counts_the_stars_the_subframeselector_would`, `test_a_star_over_the_aperture_threshold_is_found_one_under_is_not`, `test_a_wide_faint_patch_is_not_a_star_however_much_light_it_holds`, `test_a_hot_pixel_is_not_a_star`, `test_a_dark_pixel_among_bright_ones_has_a_position`, `test_a_structure_starts_at_its_threshold_on_the_median_copy`, `test_the_position_is_the_barycentre` (`backend/tests/test_pipeline_detect.py`) <!-- software-ok --> |
| Una stella saturata conta fra le stelle ma non entra nell'HFD, anche se in una camera a colori satura un canale solo | `test_saturated_stars_are_counted_but_not_measured`, `test_a_colour_star_clipped_in_one_channel_is_saturated` |
| Il tetto di saturazione e' il fondo scala dichiarato, come PixInsight, e satura e' una stella con un pixel li' (Marco, 29/10/2026) <!-- software-ok --> | `test_the_ceiling_is_the_declared_full_scale_as_pixinsight`, `test_stars_at_the_ceiling_are_counted_saturated_and_kept_out` (`backend/tests/test_pipeline_field.py`), `test_one_sensor_pixel_at_the_ceiling_makes_a_star_saturated` (`backend/tests/test_pipeline_detect.py`) |
| Il PSF SNR e il flusso PSF sono quelli della documentazione di PixInsight, sul segnale delle stelle fittate, sature comprese come le tiene lui <!-- software-ok --> | `test_psf_snr_is_the_documented_formula`, `test_the_frame_psf_snr_takes_the_fitted_stars_signal_with_no_scale`, `test_the_signal_sums_only_the_pixels_over_the_sky`, `test_an_exact_moffat_gives_its_signal_and_its_mean_flux`, `test_chauvenet_keeps_a_normal_sample_and_drops_far_outliers`, `test_chauvenet_rejects_one_at_a_time_from_the_farthest`, `test_rejected_values_are_winsorized_to_the_nearest_kept`, `test_saturated_stars_stay_in_the_psf_flux_clipped_as_they_are`, `test_a_colour_psf_snr_takes_the_intensity_noise_not_the_written_one`, `test_under_five_stars_no_psf_snr`, `test_pipeline_psf_flux.py` (quota Moffat al decimo, fondo lasciato sotto le stelle, luce col centro al buio, stella tagliata) |
| Le statistiche dei pixel sono quelle di Image Analysis: mediana senza pedestal e per secondo, Sigma, entropia, NoiseRatio, SNR, M\* e N\* del fondo, PSF Signal Weight (Marco, 30/10/2026) <!-- software-ok --> | `test_pipeline_pixel_stats.py` (pedestal, bordi e saturi fuori, Sigma di un normale, entropia 2,047 bit, fattori di scala per lato, M\* e N\* del rumore bianco, gradiente e stelle che non li spostano), `test_sn_is_the_definition_on_small_samples`, `test_psf_signal_weight_gives_back_the_programs_own_value`, `test_the_noise_ratio_is_the_share_of_pixels_the_noise_was_read_on`, `test_the_pixel_statistics_are_written_the_pedestal_off_and_the_sky_rate_per_second` |
| Il rumore e' l'MRS di Starck e Murtagh, come lo dichiara PixInsight; nei campi densi resta quello del cielo <!-- software-ok --> | `test_pipeline_noise.py` (fattore del primo strato 0,8908 come Duchamp, trasformata che si ricompone, rumore gaussiano letto entro il 2%, campo affollato e nebulosa entro il 3%), `test_in_a_crowded_field_the_noise_is_read_off_the_stars` |
| Gradiente e banding sono quelli di Image Analysis, in unita' di rumore; il lato chiaro e' nostro e un fondo piatto non lo inventa (Marco, 30/10/2026) <!-- software-ok --> | `test_pipeline_background.py` (superficie picco-picco sul rumore, riquadri luminosi scartati, saturi e bordi vuoti fuori, rumore bianco senza banding, righe spostate di 0,3 sigma, file alterne del mosaico), `test_the_biweight_fit_drops_the_outliers_a_least_squares_follows`, `test_a_sky_on_a_plane_has_its_bright_side`, `test_the_bright_side_turns_with_the_plane`, `test_a_flat_sky_has_no_side` |
| Le scie di satelliti, aerei e meteore si contano come Image Analysis: lunghe almeno un quarto del lato corto, sottili, fino a 16; il bordo di una nebulosa no (Marco, 30/10/2026) <!-- software-ok --> | `test_pipeline_trails.py` (cielo senza scie, 4 sigma trovata in campo rado e denso, 2 sigma persa nel denso e trovata nel rado, meteora corta, tratteggio sotto il 35%, bordo e filamento di nebulosa, due incrociate, al massimo 16, stelle mascherate lungo la scia, bordo vuoto), `test_the_trails_are_written` |
| La trasparenza di una serie (stesso campo e filtro) come Image Analysis: estinzione relativa al frame piu' trasparente, estinzione da nuvole oltre la legge di Bouguer; il flusso delle stelle e' il nostro (Marco, 30/10 e 4/11/2026) <!-- software-ok --> | `test_pipeline_transparency.py` (finestre dal rango 1, 51, 101, 201..., sature sopra le altre, 40% sature fuori, frame piu' trasparente a zero, flusso al secondo, finestra dei piu' frame, suo fit di Bouguer su Abell 2151 entro 1e-6, nuvole che non inclinano la retta, sola costante sotto 0,05 di massa d'aria, sotto 5 frame niente nuvole), `test_the_upper_biweight_fit_downweights_only_the_points_above` (`test_robust.py`), `test_the_aperture_flux_holds_the_moffat_out_to_its_full_width_at_a_tenth`, `test_each_fit_knows_its_detected_star` (`test_pipeline_psf_fit.py`), `test_the_brightness_ladder_follows_the_transmission_not_the_sky_nor_much_the_seeing` (`test_pipeline_field.py`), `test_the_brightness_ladder_is_written` |
| Tilt, curvatura ed elongazione sono quelli di Image Analysis: dalle FWHM e dagli angoli di tutte le stelle fittate, muti sotto 32 fit o con stelle tonde (Marco, 30/10/2026) <!-- software-ok --> | `test_tilt_and_curvature_are_the_documented_surface`, `test_under_32_stars_no_tilt`, `test_aligned_elongations_give_their_angle_counterclockwise_and_full_coherence`, `test_crossed_elongations_have_no_coherence`, `test_round_stars_or_none_have_no_elongation`, `test_tilt_reaches_the_frame_through_measure` (`backend/tests/test_pipeline_field.py`) |
| La massa d'aria e' quella dell'oggetto a meta' posa, con l'aria che lo alza, finita all'orizzonte e nessuna sotto | `test_the_airmass_is_pickering_on_the_apparent_altitude`, `test_the_refraction_lifts_a_low_star_saemundsson`, `test_under_the_horizon_there_is_no_airmass`, `test_the_altitude_and_azimuth_agree_with_astropy` (`backend/tests/test_pipeline_airmass.py`, `test_pipeline_altitude.py`) |
| FWHM e HFD anche in secondi d'arco dalla scala risolta e allo zenit; senza soluzione niente secondi, senza sito o ora niente altezza ne' zenit | `test_a_solved_shot_gets_its_airmass_arcseconds_and_zenith_values`, `test_a_value_at_the_zenith_is_divided_by_the_airmass_to_the_three_fifths`, `test_without_a_site_there_is_no_altitude_but_the_arcseconds_stay`, `test_without_a_start_there_is_no_time_nor_altitude`, `test_the_mid_exposure_is_the_start_plus_half` (`backend/tests/test_pipeline_sky_measure.py`) |
| Di ogni posa so dove puntava e che luce aveva: azimut e angolo orario del centro, Luna e Sole a meta' posa, quanto la Luna e' lontana e illuminata, il lato del pilastro (Image Analysis par. 2.1.1; Marco, 30/10/2026) <!-- software-ok --> | `test_a_shot_gets_where_it_pointed_and_the_moon_and_sun_of_its_moment`, `test_without_a_centre_the_moon_and_sun_stay_but_not_the_distance` (`backend/tests/test_pipeline_sky_measure.py`), `test_the_altitude_and_azimuth_agree_with_astropy`, `test_the_hour_angle_is_the_apparent_sidereal_time_less_the_place_of_date` (`test_pipeline_altitude.py`), `test_ephemeris_frames.py`, `test_the_pier_side_is_east_or_west_as_written_else_unknown` (`test_pipeline_card.py`) |
| La direzione delle stelle e il lato chiaro del gradiente girati col cielo: "in AR" o "in Dec" | `test_a_pixel_direction_turns_into_its_position_angle_on_the_sky` (`test_pipeline_footprint.py`), `test_the_shape_and_the_bright_side_turn_with_the_sky`, `test_the_nearer_sky_axis_names_the_direction`, `test_a_solution_without_its_matrix_gives_arcseconds_but_no_direction`, `test_round_stars_and_a_flat_sky_have_no_direction` |
| Una soluzione arrivata dopo la misura riscrive le misure col cielo, una dimenticata le porta via | `test_an_unsolved_shot_takes_its_altitude_from_the_card_then_its_solution`, `test_a_forgotten_solution_takes_its_sky_measures_along`, `test_an_unreadable_measure_waits`, `test_a_stop_writes_nothing` |
| Una nebulosa sotto le stelle e' cielo, non stella | `test_a_nebula_under_the_stars_is_sky_the_ring_follows` |
| Una camera a colori si misura come in WBPP, dopo il debayer VNG, in pixel del sensore, anche con stelle piccole | `test_a_colour_frame_is_measured_after_vng_in_sensor_pixels`, `test_a_colour_camera_is_measured_after_its_debayer`, `test_a_colour_matrix_not_rgb_is_not_measured` |
| A colori il rumore e' quello che dice WBPP, canale per canale | `test_colour_noise_is_the_mid_of_the_cfa_channels_as_pixinsight_says_it` <!-- software-ok --> |
| A colori rumore e flusso delle stelle si stimano per canale e si combinano come Image Analysis; stelle e pixel restano sull'intensita' | `test_a_colour_frame_says_each_estimate_as_the_mid_range_of_its_channels`, `test_a_colour_frames_stars_and_pixels_stay_on_the_intensity` (`backend/tests/test_pipeline_field.py`) |
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
  WBPP: VNG a piena risoluzione dalle formule pubblicate (Chang 1999 in Chen, Stanford Psych 221;
  US 6421084; Marco 3/11: niente sorgente PCL), bordo di 2 px copiato; dal suo VNG 9-10% dei pixel,
  stelle 0,986-1,011 (125 frame). Poi l'intensita' HSI (min + max) / 2 del SubframeSelector.
  Pattern da `BAYERPAT`, una colonna in piu' con `XBAYROFF` dispari e una riga con `YBAYROFF` dispari; `ROWORDER` non si legge (come
  l'Auto del Debayer; sui 4 frame veri il verde sta dove lo dice `BAYERPAT`). Una matrice non
  R G B (CYGM): `not_supported`. La saturazione si guarda sul pixel del sensore: il debayer
  nasconde un verde saturato. Scheda muta: mono.
- **Fondo**: `sep.Background`. **Rumore** (`pipeline/noise.py`, passo 26.45): il supporto
  multirisoluzione di Starck e Murtagh (1998, PASP 110:193), lo stimatore che PixInsight dichiara <!-- software-ok -->
  (ImageWeighting par. 2.4, 3.1.2): trasformata a trous B3 sui primi 4 strati, pixel fuori dal
  supporto a 3 sigma, iterato fino a fermarsi, diviso per 0,974. Sui 205 frame del passo 26.45
  da 0,996 a 1,004 volte il suo, senza tarature; la MAD di prima arrivava a 1,24 nei campi da
  40 mila stelle (le ali entravano nel conto). Le stelle contate lo usano dal passo 26.48; i
  rilevamenti di `sep` (HFD, forma) restano sul primo passaggio (1,4826 MAD). A colori per canale
  (sotto). Mai sotto un gradino da 1 ADU, 1/sqrt(12). Costa da 1,3 a 3,2 s a frame.
- **Stime per canale** (26.56, `stars._estimates`): a colori rumore, NoiseRatio, SNR, M\*, N\*,
  PSFFlux, PSFTotalMeanFlux, PSFCount come Debayer e Image Analysis (par. 2.1, 2.1.4-2.1.5;
  ImageWeighting 3.1): piani R, G (media dei due), B del grezzo a mezza risoluzione come un mono,
  ogni stima (min + max) / 2, poi le formule; PSFCount per eccesso; sonde nel piano.
- **Stelle** (`pipeline/detect.py`, passi 25.15, 26.46, 26.48, 26.48.1): **quelle che conta Image
  Analysis** (Marco 27/10 e 30/10/2026, ADR 0042): lo StarDetector nativo PJSR ai default ridà
  le sue Stars in 203 frame su 205; regole dalla documentazione PJSR
  (`doc/pjsr/objects/StarDetector`), provate a scatola chiusa, mai sul sorgente PCL. **Struttura**
  (26.48.1, sonde sulla sua `structureMap`; la doc: non una wavelet): copia mediana 3x3 meno la sua
  gaussiana, nucleo 2^L + 1 px troncato all'1% (sigma 2^(L-1) / sqrt(2 ln 100), 5,27 px a L 5),
  pixel sopra 2,11 volte il rumore di struttura, chiusi 3x3, 8 direzioni. Su gobbe a verita' nota l'area satura
  (12 / 40 / 112 / 216 px a sigma 0,8 / 1,5 / 3 / 5) e' di questa gaussiana, sigma raddoppia per
  strato (1,3 / 2,5 / 5 / 10 px, L 3-6), la soglia segue il rumore (non cielo, piedistallo, satura,
  galassia); mappa uguale alla sua, J 0,98-0,9999 su 12 frame (I - c5 a 3 sigma: 0,57-0,86).
  **Rumore di struttura** (26.48.2, `noise.structure_noise`): strato 2 B3 della copia mediana a 3
  sigma, diviso per 0,1492 (lo stesso su rumore bianco). Vede il rumore correlato (Debayer) che MRS
  non vede: sua soglia su MRS 2,10-3,86, su questo 1,97-2,19 mono e colori, salvo Caldwell 14 e M31-33
  Poseidon 1,83-1,93 (21 frame; ~45 stimatori provati, nessuno entro il 2%; pixel caldi esclusi). Sotto 3 px
  nessuna sua stella (205 frame, `minStructureSize` spento); sotto (1 - 0,6) pi / 4 del quadrato
  circoscritto (`maxDistortion` 0,6) non e' una stella. Stella: miglior 2x2 sul residuo meno 2 b
  sopra 16,5 n ((s - b) / n, la `sensitivity`); b e n mediana e 1,4826 MAD del residuo nel
  riquadro allargato di 6 px fuori dalle strutture dilatate di 1 (la sua cornice, sonde 26.48;
  sparito il compenso 4 / 16); sotto 16 pixel liberi b = 0 e n il rumore; n mai sotto 1 ADU. Lui
  perde le stelle dove il rumore raddoppia; un nodo su nebulosa si misura sulla nebulosa (M42).
  **Una soglia sola**, la porta `brightThreshold` 3 (doc PJSR): 16,5 = 3 soglie di `sensitivity`
  (5,49 / 5,83 a `brightThreshold` 1, NGC 7380 n.3 / IC 405 n.0; LDN 1400 n.0 5779 contro 3919);
  la curtosi (`peakResponse`) salva solo stelle oltre 2x2 250. Il 16,5: meta' trovate su profili noti
  (gaussiane sigma 1-4, Moffat: 16,2-16,7); dischi e Moffat beta 4 +10% / -13% con ogni nucleo
  provato (2x2, 3x3, gaussiane 0,6-1,3). Una struttura con piu' di un pixel in cima al suo 5x5
  sul residuo intero, cielo compreso, e' una sorgente multipla e si scarta
  (`allowClusteredSources` spento, `localDetectionFilterRadius` 2; un plateau conta uno), salvo
  che un pixel del piano misurato superi 0,75 del tetto (`localMaximaDetectionLimit`; il tetto di
  ADR 0041, dove una stella si taglia: PixInsight normalizza sul fondo scala del tipo, uguale <!-- software-ok -->
  finche' `DATAMAX` manca). Sonda sulla sua mappa e il suo piano (26.48.3): sue singole tenute
  0,986 / 0,991 / 0,999 (NGC 7380 n.3, x07, IC 405 n.0; fra i soli pixel della struttura 0,957 /
  0,961 / 0,998), sue multiple tagliate tutte.
  Prefiltro e cornice sul rumore MRS (sintetico da 40 mila stelle: la MAD 19,8, il vero 10).
  Prefiltro di velocita': 2x2 sotto 8 volte quel rumore non arriva al conto locale (nessuna sua
  stella sotto, sul banco). Il 2x2: sintetici del 26.45 (1 px varia 1,48 volte, 3 px 1,64), non i
  nostri frame (Marco 28/10). **Banco dei 205** (26.48.3, massimi sul 5x5 intero): stelle / sue,
  colori A 0,994, B 0,984, mono A 0,993, B 0,997; **mono tutti in 0,95-1,05** senza compenso; fuori
  7, tutti NGC 7380 a colori (0,905-0,949): scarto noto (26.48.4 parziale, Marco 3/11). A SNR 12
  nessuna di 36 (20 semi), a SNR 14 il rumore ne porta su fino a 3. Conto locale da 0,3 s (2400
  stelle) a 2,8 s (45 mila) a frame; rumore di struttura 0,85 s a 24 MP; HFD e forma su `sep`.
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
- **Forma** (ADR 0042, passo 26.49, `pipeline/psf_fit.py`, `pipeline/shape.py`): come Image
  Analysis (par. 2.1.6; ImageWeighting 2.1-2.2.1; PJSR PSF). Ogni stella del rilevatore, fino a
  24576 dalle piu' brillanti per il flusso (maxStars di ImageCalibration, letto in PJSR; sul banco
  il suo PSFCount arriva a 23263) e, delle 8000 piu' brillanti (maxPSFFits di Image Analysis), per
  la forma: Moffat ellittica beta 4 col fondo B libero, al centro del pixel, sul
  piano col suo cielo (a colori l'intensita' VNG), Levenberg-Marquardt di scipy, 400 valutazioni.
  Regione quadrata: mezzo lato il lato maggiore del riquadro della struttura, +1 px per lato
  finche' la mediana scende almeno dell'1%, al piu' 64 (nostro). Scartato il fit col centro fuori
  dal riquadro o a meno di 1 px dal bordo (lui non da' numeri: nostri). FWHM 2 sqrt(sx sy)
  sqrt(2^(1/4) - 1), eccentricita' sqrt(1 - (sy/sx)^2); PSFResidual (eq. 24) media winsorizzata al
  10% di |v - f| sulla regione su 4 S / (pi Wx Wy), W al decimo, S il segnale della stella (sotto,
  **PSF SNR**: lo stesso `PSF.signal` di PJSR, 26.50). Per il frame biweight di Tukey (c 6 MAD, 1e-10, 20 passi) e Qn
  (le Sigma). Stella binnata sul pixel: +4% a FWHM 2,6 px, +1% a 5,2; beta 2,5 +8%, gaussiana -5%.
  - **Fit** (`fitted`) quando regge almeno meta' delle stelle provate e almeno 5; se no **stimata**
    (`estimated`) dai momenti di `sep` sulle 540 stelle sparse della griglia, che leggono le ali:
    su una Moffat beta 3 la FWHM esce 1,5 volte la vera; niente residuo. **Non misurabile**
    (`unmeasurable`) se piu' di meta' sono ciambelle
    (centro sotto l'anello di 3 rumori) o se l'eccentricita' arriva a 0,99: FWHM ed
    eccentricita' tacciono (le righe vere arrivano qui di rado: il rilevatore le scarta).
  - **Direzione** solo da eccentricita' 0,4 e se le stelle sono d'accordo: media assiale degli
    angoli (raddoppiati sul cerchio, Mardia 1972), se Rayleigh rifiuta l'uniforme al 5% (Zar,
    cap. 27; prima lunghezza 0,5, nostra); coma e tilt allungano in raggiera: la direzione tace. Si scrive sui pixel e girata col cielo (sotto,
    **Col cielo**).
  - **Colori**: sull'intensita' dopo VNG, come WBPP; VNG allarga le stelle piccole, come le
    vede Image Analysis dopo il Debayer: FWHM 3,5 px +4%, 1,8 px +28% (l'HFD +4%).
- **PSF SNR** (`pipeline/field.py`, ADR 0022 punto 5): ImageWeighting di PixInsight, eq. 7 e <!-- software-ok -->
  23-24, PSF SNR = 1,316e-7 F^2 / (4,987e6 sigma^2); F = PSFFlux, la somma dei segnali di tutte
  le stelle fittate (**Forma**), sature comprese, sigma il rumore; a colori F e sigma dalle
  **Stime per canale** (26.56; prima l'intensita', Marco 28/10/2026). Dal 26.50, come la sua
  fotometria PSF (ImageWeighting par. 2.2, eq. 7-10; `pipeline/psf_fit.py`, `field.photometry`):
  - **Segnale** di una stella: somma di v - B sui pixel con v > B, B il fondo fittato,
    nell'ellisse al decimo della Moffat fittata (semiassi sigma sqrt(10^(1/beta) - 1)) allargata
    di 1 px per semiasse. Il +1 non e' documentato: sonda su `PSF.signal` di PJSR, stella per
    stella sui suoi fit (Abell 2151 n.0 e M51 n.1, 3641 stelle): segnale e conteggio dei pixel
    1,000 in mediana, piccole e grandi uguali (al decimo 0,84 / 0,43, a 1,5 volte il decimo 0,99
    / 0,92 ma crescente col raggio); la somma dei suoi `PSF.signal` e' il suo PSFFlux (0,996).
  - **Flusso medio** (eq. 8): segnale / (pi rx ry), r al decimo senza il +1; PSFTotalMeanFlux la
    somma dopo Chauvenet robusto (Maples et al. 2018, due lati: mediana e deviazione al 68,3%, poi
    media e deviazione standard, una alla volta; fattori di correzione della Table 3, la legge per
    N > 100 anche sotto: il testo non da' la tabella) e i rifiutati winsorizzati (par. 2.2.1).
    Sui suoi stessi flussi medi 1,02 e 1,045 del suo; senza Chauvenet 3,5. PSFCount: le fit.
  - Sul banco (tabella sotto) 75 mono su 80 in 0,95-1,05; M51 0,98-1,04, cometa C/2025 A6
    0,87-0,97 (col flusso dei momenti, `psf_flux.py`, ora solo l'ordine dei fit: 0,58-0,63 e
    0,46-0,82). Fuori: Sh2-185 n.2 0,85 (fit 0,944 dei suoi), cometa n.1 e n.4 0,87, VdB 152 n.0 e
    M42 n.4 1,09. **Colori** 0,99 (26.56). Sotto 5 stelle o senza fit tace; mai fra camere.
- **Statistiche dei pixel** (passo 26.51, `pipeline/pixel_stats.py`, `pipeline/mmt.py`) come Image <!-- software-ok -->
  Analysis (ImageAnalysis par. 2.1.2, 2.1.4; ImageWeighting par. 2.3-2.5, 2.8), sul piano misurato
  (a colori l'intensita', il resto per canale), sui pixel in (min + e, max - e), 1/65535 del fondo.
  **Mediana** meno `PEDESTAL` (DN; N.I.N.A. e ASIAIR non lo scrivono); **SkyRate** = mediana /
  `EXPTIME` (lui non lo mette in tabella). **Sigma** 0,990905 sqrt(BWMV), u su 9 MAD. **Entropia**
  a passi di Sigma / 16 meno 4 bit. **NoiseRatio** la quota di pixel dell'MRS. **SNR** eq. 16, i
  lati della mediana col loro std, due volte entro 4 sigma. **M\*** mediana di R\* = {r - x | 0 <
  x < r}, **N\*** 2,054326 Sn(R\*) (sonda su `mmtBackgroundResidual`: Sn, non MAD, entro 1e-5;
  `robust.sn` esterno su 20001 statistiche d'ordine). Il fondo r a 256 px: il suo MMT usa elementi <!-- software-ok -->
  "multiway" non pubblicati; qui piramide di mediane 3x3 e medie 2x2, 8 scale, bilineare al bordo
  dispari (M\* 0,99-1,02 sul suo R\*). **PSF Signal Weight** eq. 21-22, flussi PSF e MRS.
- **Campo** come Image Analysis (par. 2.1.3, 2.1.6; ADR 0042, passo 26.52), sui pixel validi: <!-- software-ok -->
  **Gradiente** (eq. 13-14): mediane di fino a 16 x 16 riquadri da 32 px, superficie di secondo
  grado col biweight di Tukey (`robust.biweight_fit`: c 4,685, sigma dalla mediana dei residui
  assoluti, Holland e Welsch 1977), picco-picco sul rumore scritto. **Banding** (eq. 15): mediana
  di riga meno quella delle righe di pari parita' entro +-50, eccesso sul rumore. **Tilt e
  curvatura** (eq. 26-27): FWHM delle stelle della forma su a + b u + c v + d (u^2 + v^2); muti
  sotto 32 fit. **Elongazione** (eq. 28-29): antiorario (180 meno il nostro), coerenza 0-1. Il
  **lato chiaro** resta nostro: piano sulla mappa di `sep`, se spiega meta' della varianza.
  **Scie** (26.53): l'algoritmo del par. 2.1.3, i numeri non pubblicati col tag in `trails.py`;
  sigma MAD (la std semplice: 180 frame su 205, non 201). Campione segnalato: la linea o un pixel
  a cavallo (26.5, nostra lettura; solo la linea perdeva scie deboli: 120 -> 146 su 188, 1 falsa
  su 120, 2 sigma denso 2 cieli su 20; Marco 5/11/2026). Colonna calda non calibrata: scia per tutti.
- **Col cielo** (`pipeline/sky_measure.py`, stadio `sky` dopo `measure`; ADR 0022 punti 5 e 7):
  le misure dei pixel con la soluzione di `solve`, il sito e l'ora della scheda del file misurato,
  in `pipeline_sky`. Una posa senza soluzione si scrive subito e si riscrive quando la soluzione
  arriva; `solve.forget` porta via la sua riga. Nessun pixel letto: un conto erfa, uno di
  astropy per sito (Luna e Sole) e una scrittura per cartella; una fermata vale prima del conto.
  Il confronto calcola il cielo con la stessa funzione (`on_sky`, in `card_observation`).
  - **Ora**: meta' posa, inizio piu' meta' di `EXPTIME`; posa ignota, l'inizio.
  - **Altezza** del centro risolto, se no del puntamento (anche il bersaglio pianificato: in un
    mosaico sbaglia di qualche grado), dal sito della scheda e solo da quello. Geometrica con erfa
    (`pipeline/altitude.py`, ADR 0030; UT1 come UTC, sotto un centesimo di grado), poi Saemundsson
    a 1010 hPa e 10 C (Meeus 1998, eq. 16.4): 29' all'orizzonte, 1' a 45 gradi; sotto -1 niente.
  - **Osservazione** (26.54, Image Analysis par. 2.1.1): azimut da Nord verso Est e angolo orario <!-- software-ok -->
    in ore fra -12 e +12 dal conto erfa dell'altezza, posto di data; Luna e Sole dalle effemeridi
    (`ephemeris/frames.py`, una chiamata per sito), topocentrici senza rifrazione, distanza Luna-
    centro, illuminata 0-1 geocentrica come la fase; senza centro restano Luna e Sole. Lato del
    pilastro da `PIERSIDE` (ASCOM; ASIAIR non lo scrive). Il suo azimut prende il centro J2000
    nelle eq. 4-5 (sonda: rifatto a 0,0002 gradi); il nostro e' il vero (Marco, 4/11/2026).
  - **Massa d'aria**: Pickering 2002 (DIO 12(1) 20-39), X = 1 / sin(h + 244 / (165 + 47 h^1,1))
    sull'altezza apparente: 1 allo zenit, 1,99 a 30 gradi, 38,7 all'orizzonte, nessuna sotto (ADR 0022).
  - **Secondi d'arco**: FWHM e HFD per la scala risolta, pixel del file come l'HFD (anche a
    colori e in binning). Un derivato scritto accanto al suo pixel: una lettura non calcola.
  - **Allo zenit**: secondi d'arco / X^0,6 (ESO, seeing di La Silla). Legge del seeing; FWHM e HFD
    portano ottica e guida, e basso la correzione esagera: a 14 gradi (X 4,1) 6,9" torna 3,0".
  - **Girati col cielo**: forma e lato chiaro come angolo di posizione da Nord verso Est, dalla CD
    della soluzione (Calabretta e Greisen 2002: (est, nord) = CD per la direzione sui pixel come
    salvati; `ROWORDER` non entra, nessun BOTTOM-UP vero misurato); lo specchio non cambia un asse.
    "In AR" se l'asse e' piu' vicino a Est-Ovest (fra 45 e 135 esclusi), se no "in Dec". Senza CD
    niente giro; `rotation_deg` e' CROTA2, di segno opposto al nostro.
- **Poche stelle**: sotto 5 tenute, `too_few_stars`: il numero resta, l'HFD tace; la forma c'e'
  se le stelle di ogni rotondita' sono almeno 5: un frame mosso dice quanto.

**Le misure sul vero** (26/10/2026, 24 light copiati dall'archivio di Marco: ATR2600M L, R, G,
B, Ha, OIII, SII; Poseidon-C Pro; Canon 700D):

- **Stelle iniettate** sui fondi veri (Rosetta, M31, Ha, L): HFD mediano entro l'1%, P90 +7/+23%.
- **Contro i programmi di riferimento**: il riferimento e' Image Analysis di PixInsight (ADR <!-- software-ok -->
  0042; documentazione `doc/tools/ImageAnalysis`, 28/10/2026), al posto del SubframeSelector. <!-- software-ok -->
  `python tools/confronto_misure.py CARTELLA --groups GRUPPI --out FILE` misura le copie con
  measure, `astap_cli -analyse 30` e Image Analysis senza finestra, estese accese; legge le 57
  colonne per nome (indefinite a 0, Flags dice quali zeri sono veri) e stampa il nostro diviso
  il suo, o la differenza, per mono e colori e gruppo A/B. Colori prima al Debayer VNG Auto, come
  WBPP, che scrive il rumore per canale. Tempi: i nostri per stadio, i suoi con e senza estese, <!-- software-ok -->
  un frame alla volta (`--no-times` li salta). Si rilancia a ogni sottopasso; ogni sua misura si
  confronta (Marco, 27/10 e 30/10/2026). Siril no (Marco, 26/10/2026). <!-- software-ok -->

  **Primo giro contro Image Analysis** (passo 26.47, 30/10/2026, codice `a1cf1457`): le 205
  copie del 26.46, nitidi e sfocati insieme; AstroLog diviso lui, mediana [minimo-massimo];
  colori contro la sua misura sull'RGB del Debayer, come in WBPP.

  | Misura | Mono A (35) | Mono B (45) | Colori A (80) | Colori B (45) |
  |---|---|---|---|---|
  | Stelle (26.48.3) | 0,99 [0,97-1,02] | 1,00 [0,97-1,03] | 0,99 [0,95-1,03] | 0,98 [0,91-1,03] |
  | FWHM (26.49) | 1,00 [0,98-1,01] | 1,00 [0,98-1,01] | 1,00 [0,98-1,04] | 1,01 [0,99-1,04] |
  | Eccentricita' (26.49) | 1,00 [0,99-1,00] | 1,00 [0,99-1,00] | 1,00 [0,99-1,01] | 0,99 [0,97-1,00] |
  | FWHM Sigma (26.49) | 0,99 [0,86-1,08] | 1,02 [0,95-1,06] | 1,04 [0,98-1,13] | 1,04 [0,95-1,11] |
  | Eccentricita' Sigma (26.49) | 0,99 [0,95-1,00] | 1,00 [0,97-1,01] | 0,99 [0,94-1,12] | 0,99 [0,94-1,02] |
  | PSFResidual (26.50) | 0,98 [0,92-1,06] | 1,00 [0,91-1,14] | 1,07 [1,00-1,25] | 1,06 [0,99-1,24] |
  | PSFResidual Sigma (26.50) | 0,94 [0,88-1,00] | 0,97 [0,88-1,07] | 1,01 [0,88-1,23] | 0,98 [0,91-1,18] |
  | Fondo / mediana | 1,00 [0,99-1,00] | 1,00 [0,99-1,01] | 1,00 [0,99-1,01] | 1,00 [0,99-1,00] |
  | Rumore | 1,00 [1,00-1,00] | 1,00 [1,00-1,00] | 1,00 [1,00-1,00] | 1,00 [1,00-1,00] |
  | PSF SNR (26.50, colori 26.56) | 0,98 [0,85-0,99] | 1,00 [0,97-1,09] | 0,99 [0,89-1,06] | 0,99 [0,77-1,16] |
  | PSFFlux (26.50, 26.56) | 0,99 [0,92-1,00] | 1,00 [0,98-1,05] | 1,00 [0,94-1,03] | 1,00 [0,88-1,08] |
  | PSFTotalMeanFlux (26.50, 26.56) | 0,99 [0,95-1,10] | 1,03 [0,99-1,12] | 1,02 [0,88-1,09] | 1,00 [0,92-1,02] |
  | PSFCount (26.50, 26.56) | 0,98 [0,94-1,00] | 0,99 [0,96-1,02] | 0,97 [0,75-1,09] | 0,97 [0,82-1,02] |
  | Mediana, Sigma, Entropia (26.51) | 1,00 [1,00-1,00] | 1,00 [1,00-1,00] | 1,00 [1,00-1,00] | 1,00 [1,00-1,00] |
  | NoiseRatio (26.51, 26.56) | 1,00 [1,00-1,00] | 1,00 [1,00-1,00] | 1,00 [1,00-1,00] | 1,00 [1,00-1,00] |
  | SNR (26.51, 26.56) | 1,00 [0,98-1,01] | 1,00 [0,99-1,01] | 1,00 [0,99-1,00] | 1,00 [0,99-1,01] |
  | M\* (26.51, 26.56) | 1,00 [0,96-1,01] | 0,98 [0,96-1,00] | 0,99 [0,97-1,00] | 0,99 [0,98-1,00] |
  | N\* (26.51, 26.56) | 1,00 [0,97-1,00] | 0,99 [0,97-1,00] | 0,99 [0,98-1,00] | 0,99 [0,98-1,00] |
  | PSF Signal Weight (26.51, 26.56) | 0,99 [0,93-1,10] | 1,04 [0,98-1,15] | 1,03 [0,85-1,12] | 1,01 [0,84-1,10] |
  | Gradient (26.52) | 1,00 [0,98-1,02] | 1,00 [0,99-1,00] | 1,00 [0,99-1,00] | 1,00 [0,95-1,02] |
  | Row / ColumnBanding (26.52) | 1,00 / 1,00 | 1,00 / 1,00 | 0,99 / 0,99 [0,70-1,21] | 0,99 / 0,98 [0,77-1,45] |
  | FWHMTilt (26.52) | 1,03 [0,84-1,58] | 1,01 [0,90-1,22] | 1,04 [0,93-1,43] | 1,03 [0,87-1,13] |
  | FWHMCurvature (26.52) | 1,01 [0,59-1,15] | 1,01 [0,49-1,07] | 1,04 [-0,27-1,08] | 1,03 [0,17-1,08] |
  | Coerenza (differenza) / angolo (gradi) (26.52) | +0,006 / 0,19 | +0,001 / 0,14 | +0,003 / 0,32 | +0,005 / 0,32 |
  | Scie, frame col suo conteggio (26.53) | 35 / 35 | 45 / 45 | 80 / 80 | 41 / 45 |
  | Altezza | 1,00 [1,00-1,02] | 1,00 [1,00-1,01] | 1,00 [0,99-1,01] | 1,00 [0,99-1,02] |
  | Massa d'aria | 1,00 [0,99-1,00] | 1,00 [1,00-1,00] | 1,00 [0,99-1,01] | 1,00 [0,99-1,01] |

  Aperto: PSFResidual a colori (26.56, il nostro fit sulle stelle a colori). Tempi: fit del 26.49
  +1 s mono, +2,4 s colori; 26.56 +7,7-16 s colori; Sh2-185 n.2 (21964 fit) 23,9 s; il 26.51
  +2,8 s mono: il tetto di ADR 0042 al 26.57. Il 26.52: +0,86 s
  mono (mediane di riga); curvature vicine a zero danno rapporti larghi, scarto entro 0,07.
  Scie: 201 su 205 (sempre zero: 179), 22 dei 26 con scie sue; fuori la Velo, dove lui per
  strisce conta 4-11 scie sui filamenti: le sue 1-2 sono filamenti, il profilo li scarta. +0,5-0,9 s.
  Osservazione (26.54), secondi a frame (26.47, base del 26.57) e perche' degli scarti: nei passi.

**La trasparenza** (`pipeline/transparency.py`, Image Analysis par. 2.1.7; numeri nel passo 26.55): <!-- software-ok -->
per frame la scala di luminosita', mediana del log10 del flusso in finestre di 50 stelle dai ranghi
1, 51, 101, 201, ..., 6401; satura la stella col picco a 3/4 del pixel piu' alto, contata sopra le
altre; satura al 40% la finestra non c'e'. Sulla serie la finestra dei piu' frame, Delta m al
secondo meno il minimo (eq. 30), Bouguer (eq. 31) col biweight 4,685 sui soli residui positivi,
scala MAD (Holland e Welsch 1977; sola costante sotto 0,05 di massa d'aria, almeno 5 frame);
la collega il passo 40. **Il flusso e' nostro** (Marco, 4/11/2026): v - B nell'ellisse a 1 FWTM
(crescita del `PSF` di PJSR), ordine sul flusso misurato; il suo `PSF.flux` non si ritrova dai <!-- software-ok -->
pixel. Sintetici: trasparenza e cielo x4 entro 0,01 mag; M51 k 0,37, Gaia 0,40, il suo 0,10.
Aperto: una satura col fit rifiutato non prende rango.

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
in pixel, eccentricita' e direzione; il tetto e le stelle sature, il PSF SNR e il PSF Signal
Weight, le statistiche dei pixel (mediana, SkyRate, Sigma, entropia, NoiseRatio, SNR, M\*, N\*), il campo (gradiente col
lato chiaro, banding, scie, tilt, curvatura, elongazione), la scala di luminosita'; durata, ora. In `pipeline_sky`: se risolta, meta' posa, altezza,
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
