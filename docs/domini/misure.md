# Le misure dei frame -- contratto

Le **misure** di un frame sono i numeri che l'app prende dai suoi pixel: quante stelle, quanto
sono larghe, il fondo del cielo, il suo rumore. Le prende lo stadio `measure` della pipeline
nuova (`backend/astrolog/pipeline/measure.py`), dopo il cielo di ASTAP, **una volta**, e le
scrive in `pipeline_measures`; nessuna lettura le ricalcola. Le regole e i giudizi vengono da
ADR 0022, 0033 (D1), 0037 e 0039; questo contratto dice cosa vale oggi e cosa arriva dopo. Le
parole in [`glossario.md`](glossario.md).

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Ogni mio light viene misurato una volta, da uno dei suoi file, e la misura resta | `test_a_light_is_measured_once_and_written`, `test_only_lights_are_measured`, `test_the_plain_file_is_read_before_its_fpack_copy` (`backend/tests/test_pipeline_measure.py`) |
| L'HFD e' il diametro che contiene meta' della luce della stella, anche con le ali di una stella vera | `test_the_hfd_of_gaussian_stars_is_the_diameter_holding_half_the_flux`, `test_the_hfd_of_moffat_stars_holds_their_wings`, `test_the_truth_is_the_analytic_hfd_once_the_pixel_is_small` (`backend/tests/test_pipeline_stars.py`) |
| Fondo cielo e rumore sono quelli del cielo, non delle stelle | `test_background_and_noise_are_the_sky_and_its_spread` |
| Le stelle si contano una volta; i pixel caldi di un light non calibrato non sono stelle | `test_every_star_is_counted_once`, `test_hot_pixels_are_not_stars` |
| Una stella saturata conta fra le stelle ma non entra nell'HFD, anche se in una camera a colori satura un canale solo | `test_saturated_stars_are_counted_but_not_measured`, `test_a_colour_star_clipped_in_one_channel_is_saturated` |
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
- **Stelle**: `sep.extract` a 5 sigma (Siril) sulla copia filtrata con mediana 3x3 esatta: i <!-- software-ok -->
  pixel caldi spariscono, le stelle restano. Il numero e' un **indicatore relativo**: sui 24
  frame veri e' da 1 a 19 volte quello di ASTAP `-analyse 30`, che conta solo da SNR 30.
- **Stelle tenute per l'HFD**: intere (`flag` 0), picco sotto il 90% della saturazione
  (`DATAMAX`, o il massimo del tipo di dato), b/a sopra 0,5 (Siril), lontane dal bordo e dalle <!-- software-ok -->
  vicine piu' di 3 HFD stimate dai momenti di `sep` (la FWHM arriva al passo 25.1). Al massimo
  60 per casella di una griglia 3x3, prese lungo tutta la classifica del flusso.
- **HFD**: diametro col meta' flusso dentro un'apertura di 3 HFD stimate, con `sep.sum_circle`
  su 96 raggi e interpolazione; il valore del frame e' la mediana. **Fondo locale: mediana
  dell'anello** da 1 a 1,5 aperture **sulla copia filtrata**, senza maschera dei segmenti. ADR
  0022 diceva "media dell'anello a oggetti mascherati": sul vero (Rosetta, Canon 700D) la
  maschera copriva l'anello con la nebulosa e il fondo restava zero (HFD 12,3 px contro 4,0 di
  ASTAP). La copia filtrata toglie i pixel caldi (per cui ADR 0022 scartava la mediana), la
  mediana toglie le vicine. `sep.flux_radius` non ha l'anello: non si usa.
- **Poche stelle**: sotto 5 stelle tenute, `too_few_stars`: il numero delle stelle resta,
  l'HFD tace. Sui 24 frame veri la meno ricca ne tiene 291.
- **Non e' riproducibile bit per bit**: `sep` separa le stelle che si toccano con un passo a
  caso; lo stesso frame rimisurato cambia di pochi decimi per cento (stelle 1565/1566, HFD 3,486
  contro 3,478 px, audit del 26/10/2026). I test non chiedono conteggi esatti su stelle unite.

**Le misure sul vero** (26/10/2026, 24 light copiati dall'archivio di Marco: ATR2600M L, R, G,
B, Ha, OIII, SII; Poseidon-C Pro; Canon 700D):

- **Stelle iniettate** di forma nota sui fondi veri (Rosetta, M31, Ha, L): mediana dell'HFD
  entro l'1% dalla verita', P90 da +7 a +23%.
- **Contro i programmi di riferimento**: `python tools/confronto_misure.py CARTELLA` misura le
  copie con measure, con `astap_cli -analyse 30` e col SubframeSelector di PixInsight senza <!-- software-ok -->
  finestra, e stampa il nostro diviso il loro (minimo / mediana / massimo), mono e colori a
  parte; i colori li passa prima al Debayer VNG di PixInsight col pattern Auto, come WBPP. Si <!-- software-ok -->
  rilancia a ogni sottopasso di measure. Siril no (Marco, 26/10/2026). Sui 24 frame (colori <!-- software-ok -->
  dopo VNG, passo 24.06):

  | Misura | Mono (20) | Colori (4) | Perche' lo scarto |
  |---|---|---|---|
  | Fondo / mediana SubframeSelector | 0,99 / 1,00 / 1,00 | 0,99 / 1,00 / 1,00 | La mediana dell'immagine porta le stelle e la nebulosa, `sep` le toglie |
  | Rumore / rumore SubframeSelector | 1,00 / 1,02 / 1,05 | 1,01 / 1,04 / 1,06 | MAD contro wavelet MRS, stessa cosa. Colori: come il Debayer, per piano R, G (media dei due), B a mezza risoluzione, poi (min + max) / 2 come il SubframeSelector; sull'intensita' sarebbe 0,88-0,96 |
  | HFD / FWHM SubframeSelector | 1,15 / 1,36 / 1,46 | 1,25 / 1,30 / 1,72 | Grandezze diverse: sulla Moffat HFD/FWHM e' 1,36 a beta 2,5 e 1,17 a beta 4 (dalla formula del flusso racchiuso); la gaussiana da' 1 |
  | HFD / HFD ASTAP | 0,71 / 0,83 / 0,94 | 0,78 / 0,83 / 0,89 | ASTAP sta il 6-41% sopra; ADR 0022 lo misurava +8…27% sopra la verita' (il raggio medio). Colori: ASTAP misura il mosaico grezzo. Col superpixel il Canon (frame 15) dava 6,94 px contro 3,97, ora 3,20 |
  | Stelle / stelle ASTAP | 1,06 / 2,96 / 18,97 | 5,52 / 9,98 / 37,75 | ASTAP conta da SNR 30 sul grezzo, noi da 5 sigma sull'intensita' a piena risoluzione |
  | Stelle / stelle SubframeSelector | 0,36 / 0,47 / 1,12 | 0,64 / 0,77 / 1,34 | Il SubframeSelector rileva sui livelli delle wavelet e arriva piu' in basso; un indicatore relativo, non un conteggio |

  La FWHM confrontata a quella del SubframeSelector arriva col passo 25.1; ASTAP non da' fondo
  ne' rumore.
- **Tempo**: da 1,2 a 4,0 s a frame da 26 MP mono; a colori da 4,2 s (18 MP) a 7,0 s (26 MP),
  di cui il debayer 3,6-5 s; un processo, su copia locale. Senza il tetto di 60 per casella un
  campo denso arrivava a 7,9 s.

**Cosa si scrive** (`pipeline_measures`): esito, stelle, stelle tenute, HFD in pixel del
sensore, fondo e rumore in ADU, durata, ora. Il fondo si confronta solo con la stessa camera,
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

- **25.1**: FWHM, eccentricita', direzione dell'allungamento (fit di Moffat, scipy) sulle stelle
  gia' scelte, a colori sull'intensita' dopo VNG; "forma stimata" e "forma non misurabile".
- **25.2**: SNR (PSF SNR), gradiente, tilt e curvatura dalle cinque zone, stelle sature col
  tetto dall'istogramma, massa d'aria e valori allo zenit, i secondi d'arco.
- **25.3**: SQM col metodo di ASTAP portato, il lettore del catalogo D80, il bias della camera.
- **26-27**: soglie relative (Qn), eccentricita' rispetto al setup, Bortle del sito, oggetto basso.
- **A schermo**: col porting delle pagine (fase 5). Le tavole di Design (`handoff/design/`,
  26/10/2026) chiedono le stesse misure; quattro scarti vanno al censimento (passo 24.1):
  eccentricita' a soglie fisse 0,45/0,71 (ADR 0039 le ha tolte), soglia relativa con la MAD
  invece di Qn, "oggetto basso" solo sotto 30 gradi (ADR 0039: 30 estesi, 45 stelle), SQM per ora
  in Statistiche.
- `.fz` compressi, cubi e immagini in estensione non si misurano.
