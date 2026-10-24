# Registro delle regole

Generato da `tools/registro.py --scrivi`: non si scrive a mano. La casa di ogni valore
e' il codice, con la fonte accanto: C norma (ente, documentazione o codice ufficiale),
U usanza di comunita' (forum, blog, un solo operatore: reale ma debole), D metodo di
un'altra disciplina applicato ai nostri dati (statistica, fisica...), M misura nostra,
P decisione di Marco, T tecnico (non una regola).

Valori: 133; senza fonte: 82.
Fonti: C norma: 22; U usanza: 1; D metodo: 0; M misura: 2; P decisione: 7; T tecnico: 23.

## Valori e tabelle nel codice (`backend/astrolog`)

### api/app.py

| simbolo | valore | fonte |
|---|---|---|
| _WEATHER_TICK_S | `60` | T |

### api/archive.py

| simbolo | valore | fonte |
|---|---|---|
| archive_page(limit=) | `Query(100, ge=1, le=500)` | **senza fonte** |
| archive_page(q=) | `Query(None, max_length=200)` | **senza fonte** |
| archive_page(key=) | `Query(None, max_length=200)` | **senza fonte** |
| archive_page(catalog=) | `Query(None, max_length=40)` | **senza fonte** |
| archive_page(constellation=) | `Query(None, max_length=8)` | **senza fonte** |
| archive_page(filter_name=) | `Query(None, alias="filter", max_length=120)` | **senza fonte** |

### api/folders.py

| simbolo | valore | fonte |
|---|---|---|
| PROBE_SECONDS | `10` | **senza fonte** |
| list_folders(limit=) | `Query(100, ge=1, le=1000)` | **senza fonte** |
| create_folder@router.post | `router.post("/folders", response_model=FolderOut, status_code=201)` | **senza fonte** |

### api/gear_write.py

| simbolo | valore | fonte |
|---|---|---|
| add_instrument@router.post | `router.post("/gear/instruments", response_model=GearWritten, status...` | **senza fonte** |
| add_filter@router.post | `router.post("/gear/filters", response_model=GearWritten, status_cod...` | **senza fonte** |
| add_rig@router.post | `router.post("/gear/rigs", response_model=GearWritten, status_code=201)` | **senza fonte** |

### api/models_site.py

| simbolo | valore | fonte |
|---|---|---|
| SiteCreate.latitude | `Field(ge=-90, le=90)` | C geographic latitude |
| SiteCreate.longitude | `Field(ge=-180, le=180)` | C geographic longitude |
| SiteCreate.bortle | `Field(None, ge=1, le=9)` | C Bortle 2001: nine classes |
| SiteEdit.latitude | `Field(None, ge=-90, le=90)` | C geographic latitude |
| SiteEdit.longitude | `Field(None, ge=-180, le=180)` | C geographic longitude |
| SiteEdit.bortle | `Field(None, ge=1, le=9)` | C Bortle 2001: nine classes |

### api/models_tonight.py

| simbolo | valore | fonte |
|---|---|---|
| IlluminationPct | `Annotated[int, Field(ge=0, le=100)]` | T |
| MoonOut.ceiling_deg | `le=90,` | T |

### api/nights.py

| simbolo | valore | fonte |
|---|---|---|
| night_list(limit=) | `Query(100, ge=1, le=500)` | **senza fonte** |

### api/pipeline.py

| simbolo | valore | fonte |
|---|---|---|
| ETA_AFTER_S | `60` | **senza fonte** |

### api/review.py

| simbolo | valore | fonte |
|---|---|---|
| settled_objects(limit=) | `Query(50, ge=1, le=500)` | **senza fonte** |

### api/review_write.py

| simbolo | valore | fonte |
|---|---|---|
| _REFUSALS | `(gear.MergeRefusedError, 422, "merge_refused"),` | **senza fonte** |
| _REFUSALS | `(folders.NotAskedError, 422, "not_asked"),` | **senza fonte** |
| _REFUSALS | `(decl.UnknownTargetError, 422, "unknown_target"),` | **senza fonte** |
| _REFUSALS | `(rigs.NotOfKindError, 422, "not_of_kind"),` | **senza fonte** |
| _REFUSALS | `(rigs.WrongKindError, 422, "wrong_kind"),` | **senza fonte** |
| _REFUSALS | `(gear_create.SpellingTakenError, 409, "spelling_taken"),` | **senza fonte** |
| _REFUSALS | `(rigs.RigExistsError, 409, "rig_exists"),` | **senza fonte** |

### api/scan.py

| simbolo | valore | fonte |
|---|---|---|
| scan_all@router.post | `router.post("/scan", response_model=ScanAllStarted, status_code=202)` | **senza fonte** |
| scan@router.post | `router.post("/folders/{folder_id}/scan", response_model=ScanStarted...` | **senza fonte** |
| scan_runs(limit=) | `Query(20, ge=1, le=500)` | **senza fonte** |
| scan_run_errors(limit=) | `Query(100, ge=1, le=1000)` | **senza fonte** |

### api/search.py

| simbolo | valore | fonte |
|---|---|---|
| search_archive(q=) | `Query("", max_length=200)` | **senza fonte** |
| search_archive(limit=) | `Query(5, ge=1, le=20)` | **senza fonte** |

### api/sites.py

| simbolo | valore | fonte |
|---|---|---|
| list_sites(limit=) | `Query(100, ge=1, le=1000)` | **senza fonte** |
| create_site@router.post | `router.post("/sites", response_model=SiteOut, status_code=201)` | **senza fonte** |

### api/weather.py

| simbolo | valore | fonte |
|---|---|---|
| FULL_NIGHTS | `3` | P docs/domini/meteo.md: three full nights |
| MAX_NIGHTS | `7` | P docs/domini/meteo.md |

### astap.py

| simbolo | valore | fonte |
|---|---|---|
| TIMEOUT_S | `60` | M over twice the slowest blind solve that succeeds, 23 s, docs/domini/spina.md |
| SEARCH_RADIUS_DEG | `30` | C N.I.N.A. PlateSolveSettings.cs searchRadius = 30 |
| BLIND_RADIUS_DEG | `180` | C ASTAP default radius_search1; N.I.N.A. forces 180 without coordinates |
| _POLE_DEG | `90.0` | T |
| FZ_SINCE | `(2026, 7, 17)` | C ASTAP source: RICE_1 in astap_cli from 2026.07.17 |

### clock.py

| simbolo | valore | fonte |
|---|---|---|
| _START_HOUR | `12` | P docs/domini/effemeridi.md |

### db/config.py

| simbolo | valore | fonte |
|---|---|---|
| KEYS | `25,` | C ING dark time: lit fraction under 0.25 |
| KEYS | `4,` | P docs/domini/effemeridi.md |
| RANGES | `{"moon_broadband_max_pct": (0, 100), "moon_broadband_min_dark_h": (...` | T |

### ephemeris/__init__.py

| simbolo | valore | fonte |
|---|---|---|
| RISESET_DEG | `-0.833` | C USNO RST_defs: Sun's centre at zenith distance 90.8333 |
| CIVIL_DEG | `-6.0` | C USNO https://aa.usno.navy.mil/faq/RST_defs: 6, 12, 18 degrees below the horizon |
| NAUTICAL_DEG | `-12.0` | **senza fonte** |
| ASTRO_DEG | `-18.0` | **senza fonte** |
| GRID_STEP_MIN | `3` | T |
| TRACK_STEP_MIN | `15` | T |
| CALENDAR_STEP_MIN | `5` | T |
| SYNODIC_MONTH_DAYS | `29.530588861` | C Meeus, Astronomical Algorithms, 2nd ed., ch. 49 |
| MAX_DECLINATION_DEG | `28.8` | C lunar standstill: declination up to 28.725 degrees, Wikipedia "Lunar standstill" |
| CEILING_STEP_DEG | `15` | T |

### ephemeris/moon.py

| simbolo | valore | fonte |
|---|---|---|
| _HALF_WIDTH_DEG | `6.0` | **senza fonte** |

### ephemeris/sun.py

| simbolo | valore | fonte |
|---|---|---|
| _HALF_HOUR | `dt.timedelta(minutes=30)` | T |
| _HAIR | `1e-9` | T |

### fits/header_read.py

| simbolo | valore | fonte |
|---|---|---|
| FINGERPRINT_BYTES | `65536` | **senza fonte** |
| BLOCK | `2880` | **senza fonte** |
| _CARD | `80` | **senza fonte** |
| _CLEAN_END | `b"END" + b" " * (_CARD - 3)` | **senza fonte** |
| _BYTES_PER_PIXEL | `{8: 1, 16: 2, 32: 4, 64: 8, -32: 4, -64: 8}` | **senza fonte** |

### fits/walk.py

| simbolo | valore | fonte |
|---|---|---|
| FILE_ATTRIBUTE_RECALL_ON_OPEN | `0x00040000` | **senza fonte** |
| FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS | `0x00400000` | **senza fonte** |
| SF_DATALESS | `0x40000000` | **senza fonte** |
| LONG_PATH_THRESHOLD | `240` | **senza fonte** |

### net.py

| simbolo | valore | fonte |
|---|---|---|
| TIMEOUT_S | `15` | **senza fonte** |
| _REFUSALS | `frozenset({400, 401, 403, 429})` | **senza fonte** |

### pipeline/changes.py

| simbolo | valore | fonte |
|---|---|---|
| LEFT_OUT_KEPT | `100` | **senza fonte** |

### pipeline/fingerprint.py

| simbolo | valore | fonte |
|---|---|---|
| FINGERPRINT_BYTES | `65536` | **senza fonte** |
| BLOCK | `2880` | **senza fonte** |
| CARD | `80` | **senza fonte** |
| _BYTES | `{8: 1, 16: 2, 32: 4, 64: 8, -32: 4, -64: 8}` | **senza fonte** |
| _MAX_AXES | `999` | **senza fonte** |
| _MAX_BYTES | `2**62` | **senza fonte** |

### pipeline/scan.py

| simbolo | valore | fonte |
|---|---|---|
| BATCH | `100` | **senza fonte** |
| UNKNOWN_KEPT | `100` | **senza fonte** |
| UNKNOWN_TRACKED | `10_000` | **senza fonte** |

### pipeline/scanner.py

| simbolo | valore | fonte |
|---|---|---|
| MAX_HEADER_BLOCKS | `100` | **senza fonte** |

### pipeline/sky.py

| simbolo | valore | fonte |
|---|---|---|
| _J2000_PRECESSION | `erfa.bp06(2451545.0, 0.0)[1]` | C IAU 2006 precession at J2000.0 TT |

### pipeline/solve.py

| simbolo | valore | fonte |
|---|---|---|
| PASSES | `2` | **senza fonte** |

### pipeline/values.py

| simbolo | valore | fonte |
|---|---|---|
| (SQLITE_MIN, SQLITE_MAX) | `-(2**63), 2**63 - 1` | **senza fonte** |
| COLDEST_C | `-273.15` | **senza fonte** |

### pipeline/walk.py

| simbolo | valore | fonte |
|---|---|---|
| FILE_ATTRIBUTE_RECALL_ON_OPEN | `0x00040000` | **senza fonte** |
| FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS | `0x00400000` | **senza fonte** |
| SF_DATALESS | `0x40000000` | **senza fonte** |
| LONG_PATH_THRESHOLD | `240` | **senza fonte** |

### place.py

| simbolo | valore | fonte |
|---|---|---|
| _KM_PER_DEGREE | `111.2` | C IUGG mean radius R1 6371.0088 km: 2*pi*R1/360 = 111.195 |
| search(limit=) | `5` | **senza fonte** |

### spine/folder_move.py

| simbolo | valore | fonte |
|---|---|---|
| SAMPLE_FILES | `5` | **senza fonte** |

### spine/identify.py

| simbolo | valore | fonte |
|---|---|---|
| CANDIDATES_LIMIT | `6` | **senza fonte** |

### spine/identify_decide.py

| simbolo | valore | fonte |
|---|---|---|
| _RANK | `IdentityConfidence.LOW: 2,` | **senza fonte** |

### spine/identify_geometry.py

| simbolo | valore | fonte |
|---|---|---|
| MIN_SEARCH_RADIUS_DEG | `3.0` | **senza fonte** |

### spine/identify_score.py

| simbolo | valore | fonte |
|---|---|---|
| W_MAGNITUDE | `1.4` | **senza fonte** |
| W_SIZE | `0.6` | **senza fonte** |
| W_CENTERING | `1.2` | **senza fonte** |
| SEP_FLOOR_DEG | `0.05` | **senza fonte** |
| SCALE_CAP_DEG | `3.0` | **senza fonte** |
| CATALOG_PRIORITY | `"M": 1.0, "C": 0.9, "NGC": 0.7, "IC": 0.55,` | **senza fonte** |
| CATALOG_PRIORITY | `"Sh2": 0.4, "LBN": 0.3, "LDN": 0.3, "vdB": 0.3, "Ced": 0.3,` | **senza fonte** |
| CATALOG_PRIORITY | `"B": 0.3, "Abell": 0.3, "RCW": 0.3,` | **senza fonte** |
| CATALOG_PRIORITY_DEFAULT | `0.2` | **senza fonte** |
| AMBIGUOUS_SCORE_RATIO | `0.6` | **senza fonte** |
| AMBIGUOUS_SEPARATION_DEG | `0.4` | **senza fonte** |

### spine/mosaic_geometry.py

| simbolo | valore | fonte |
|---|---|---|
| SAME_POINTING_FRACTION | `0.25` | **senza fonte** |

### spine/mosaic_weight.py

| simbolo | valore | fonte |
|---|---|---|
| MIN_SHARE | `0.25` | **senza fonte** |

### spine/nights.py

| simbolo | valore | fonte |
|---|---|---|
| _SLIVER_PCT | `2` | T |

### spine/rewrite.py

| simbolo | valore | fonte |
|---|---|---|
| MARK_WEIGHT | `{None: 0, RewriteMark.REWRITTEN: 1, RewriteMark.CALIBRATED: 2}` | **senza fonte** |

### spine/scan.py

| simbolo | valore | fonte |
|---|---|---|
| DEFAULT_MIN_AGE_S | `30` | **senza fonte** |
| MTIME_TOLERANCE_S | `0.001` | **senza fonte** |

### spine/search.py

| simbolo | valore | fonte |
|---|---|---|
| _ANY_YEAR | `2000` | **senza fonte** |

### spine/year.py

| simbolo | valore | fonte |
|---|---|---|
| _EDGES_H | `((2, "under2"), (4, "2to4"), (6, "4to6"))` | T |

### startup.py

| simbolo | valore | fonte |
|---|---|---|
| OWNER_ONLY | `0o600` | **senza fonte** |

### units.py

| simbolo | valore | fonte |
|---|---|---|
| F32_SIGNIFICANT_DIGITS | `7` | T |
| ARCSEC_PER_RAD_PER_1000 | `206.265` | C 648000/pi |
| FOCAL_TOLERANCE | `0.05` | P ADR 0016 |
| NATURAL_SKY_CD_M2 | `174e-6` | **senza fonte** |
| CD_M2_PER_MAG0 | `1.08e5` | **senza fonte** |
| BORTLE_FLOORS | `BORTLE_FLOORS = ((1, 21.76), (2, 21.60), (3, 21.30), (4, 20.80), (5...` | **senza fonte** |
| BORTLE_FLOORS | `(7, 18.00), (8, 17.00))` | **senza fonte** |
| (BORTLE_TOP, BORTLE_BOTTOM) | `22.00, 16.00` | **senza fonte** |
| (SQM_MIN, SQM_MAX) | `10.0, 23.0` | **senza fonte** |

### weather/climate.py

| simbolo | valore | fonte |
|---|---|---|
| YEAR_DAYS | `365` | T |
| MIN_NIGHTS | `120` | P docs/domini/meteo.md: a third of a year |

### weather/forecast.py

| simbolo | valore | fonte |
|---|---|---|
| REFRESH_EVERY_S | `3 * 3600` | T |
| RETRY_S | `15 * 60` | T |

### weather/history.py

| simbolo | valore | fonte |
|---|---|---|
| DELAY_DAYS | `5` | C Open-Meteo: ERA5 joins five days later, final only then |
| MAX_DAYS | `366` | T |

### weather/judge.py

| simbolo | valore | fonte |
|---|---|---|
| SCALES | `Scale(Measure.CLOUD, _field("cloud_total_pct"), _EIGHTHS, axis_top=...` | T |
| SCALES | `Scale(Measure.CLOUD_LOW, _field("cloud_low_pct"), _EIGHTHS, axis_to...` | T |
| SCALES | `axis_top=1.5,` | T |
| SCALES | `[Step(NOGO, 29.0, strict=False)],` | C RMetS Beaufort 5, a mean-wind scale |
| SCALES | `axis_top=45.0,` | T |
| SCALES | `[Step(NOGO, 29.0, strict=False), Step(MARGINAL, 20.0, strict=False)],` | C RMetS Beaufort 5 and 4 |
| SCALES | `axis_top=45.0,` | T |
| SCALES | `[Step(NOGO, 3.0, strict=True)],` | U imagers' usage, AstroBin above |
| SCALES | `axis_top=10.0,` | T |
| SCALES | `[Step(NOGO, 126.0, strict=False)],` | C meteoblue, 35 m/s |
| SCALES | `axis_top=160.0,` | T |
| SCALES | `[Step(NOGO, 4.0, strict=True), Step(MARGINAL, 2.0, strict=True)],` | C CMC class I: >4"; U Astronomy Tools: OK 2-4" |
| SCALES | `axis_top=5.0,` | T |
| SCALES | `[Step(NOGO, 1.0, strict=False), Step(None, 0.1, strict=False)],` | C NASA |
| SCALES | `digits=2,` | T |
| SCALES | `axis_top=0.2,` | T |
| SCALES | `[Step(NOGO, 50.0, strict=True), Step(MARGINAL, 25.0, strict=True)],` | C ING dark time under 25 %; P docs/domini/meteo.md: 50 % |
| SCALES | `axis_top=100.0,` | T |
| SCALES | `axis_top=20.0,` | T |
| NEUTRAL | `Scale(Measure.CLOUD_MID, _field("cloud_mid_pct"), [], axis_top=100.0),` | T |
| NEUTRAL | `Scale(Measure.CLOUD_HIGH, _field("cloud_high_pct"), [], axis_top=10...` | T |
| _RANK | `{NOGO: 0, MARGINAL: 1, None: 2, GO: 3}` | T |

### weather/meteoblue.py

| simbolo | valore | fonte |
|---|---|---|
| FREE_YEAR_CREDITS | `10_000_000` | C meteoblue free API: "10 million credits", "for one year" |
| CREDITS_PER_CALL | `8_000` | M cost of one call, as the account's usage page reports it |
| MIN_GAP_H | `max(12, math.ceil(24 * 365 / CALLS_PER_YEAR))` | T |

### weather/openmeteo.py

| simbolo | valore | fonte |
|---|---|---|
| FORECAST_DAYS | `8` | T |

### weather/verdict.py

| simbolo | valore | fonte |
|---|---|---|
| CLOUD_GO_MAX_PCT | `25.0` | C WMO/ICAO code D-8: FEW 1-2 oktas, SCT 3-4 |
| CLOUD_MARGINAL_MAX_PCT | `50.0` | C WMO/ICAO code D-8: SCT up to 4 oktas |

## Decisioni (ADR)

| ADR | titolo | stato | supera in |
|---|---|---|---|
| 0001 | Il metodo passa a strumenti standard | accettata, 30/9/2026 |  |
| 0002 | Nessun login: la rete di casa e' fidata, e ogni avvio ha la sua chiave | accettata, 13/9/2026 |  |
| 0003 | ASTAP e' impacchettato per tutti, e il suo database si scarica al primo avvio | accettata, 9/9/2026; il catalogo che si scarica e' il D50 (ADR 0036, 24/10/2026). |  |
| 0004 | Su Windows e Mac l'app e' un'app vera: Tauri 2 col backend come sidecar | accettata, 4/9/2026; la scelta fra Tauri ed Electron la chiude il prototipo |  |
| 0005 | Il motore della carta del cielo e' Aladin Lite v3 | accettata |  |
| 0006 | Il cielo fotografico (DSS2) non sta mai nel pacchetto | accettata |  |
| 0007 | Le metriche dei frame con `sep` e numpy/scipy, non `photutils` | accettata |  |
| 0008 | Una pagina Diagnostica, nessuna telemetria | accettata |  |
| 0009 | Tutto automatico, manuale per eccezione; v1 e' un'app completa | accettata |  |
| 0010 | Un utente per istanza, con piu' siti e piu' setup | accettata |  |
| 0011 | L'API e' versionata, e pagina ogni elenco che cresce con l'archivio | accettata |  |
| 0012 | Il disegno delle pagine viene da Claude Design e si porta alla lettera | accettata, 29/9/2026 |  |
| 0013 | Progetti e piano della notte: il Planner fa i progetti, la serata si compone a parte | accettata, 4/10/2026. ADR 0033: lo scarto dei frame lo sceglie l'utente (ADR 0032). |  |
| 0014 | Da confermare semplificata: meno famiglie di domande, chiavi che non si spostano | accettata, 5/10/2026 |  |
| 0015 | Una ricetta per tipo di lavoro, una revisione sola | accettata, 5/10/2026. Sostituisce il giro di revisione di ADR 0001. |  |
| 0016 | La focale di un frame si misura dal cielo, l'header e' il ripiego | accettata, 6/10/2026 (Marco). |  |
| 0017 | Il backup delle risposte: un file accanto al database, riscritto a ogni risposta | accettata, 7/10/2026 (Marco). |  |
| 0018 | Si passa tutto al telaio e al foglio v26, senza convivenza | accettata, 7/10/2026 |  |
| 0019 | Sole e Sistema solare entrano in Archivio a mano, il deep sky resta automatico | accettata, 17/10/2026 (Marco). Nessun codice ancora. Ordine dei pezzi: disegno della linguetta e di "Aggiungi oggetto"; comete, |  |
| 0020 | La qualita' della notte e' un punteggio da 0 a 100, coi pesi decisi con Marco | accettata, 17/10/2026 (Marco); superata in parte da ADR 0034 (24/10/2026: pesi, ora | domini/meteo.md |
| 0021 | L'attrezzatura porta i dati delle schede tecniche, e il setup ci calcola | accettata, 18/10/2026 (Marco). ADR 0033: i programmi verificati sono due (ADR 0029). |  |
| 0022 | Le misure dei frame: tutte, attestate, nel database, senza voto | accettata, 18/10/2026 (Marco). Superata in parte da ADR 0033 e 0037 (SNR, zone, tilt). |  |
| 0023 | Planner e Progetti: inquadratura, mosaico, setup di prova, filtri, modifiche | accettata, 18/10/2026 (Marco). ADR 0033: nel piano della notte il meteo e' una striscia (ADR 0013). |  |
| 0024 | Statistiche: i confronti nel tempo | accettata, 20/10/2026 (Marco). Riprende il contratto vecchio |  |
| 0025 | Uno studio per ruoli: la pagina si collauda contro la tavola prima di Marco | accettata, 20/10/2026 (Marco, dal check di salute). Allarga ADR 0015: ricette, un giro |  |
| 0026 | La pipeline usa cio' che ha gia': nome del file, posizione nell'header, effemeridi, notte | accettata, 20/10/2026 (Marco, dal check di salute). Nessun codice ancora: ordine in |  |
| 0027 | Ogni cosa una casa e un tetto: piano, idee, Issue; niente coda | accettata, 20/10/2026 (Marco). Proposta completa e fonti: |  |
| 0028 | Le ricette, gli audit e GitHub | accettata, 20/10/2026 (Marco). Proposta completa e fonti: |  |
| 0029 | Due programmi verificati e una convenzione: N.I.N.A., ASIAIR, SBIG | accettata, 22/10/2026 (Marco). Supera "Software supportati: quattro" di CLAUDE.md. |  |
| 0030 | Il metodo della pipeline: un passo alla volta, provato sul vero | accettata, 22/10/2026 (Marco). Vale per la pipeline rifatta da zero (`docs/piano.md`). |  |
| 0031 | Generale prima: una lista standard, l'attrezzatura dell'utente, un abbinamento | accettata, 22/10/2026 (Marco). Vale per la pipeline nuova (ADR 0030). |  |
| 0032 | La zona di selezione dei frame | accettata, 23/10/2026 (Marco); soglie e file rivisti lo stesso giorno sulla tavola di |  |
| 0033 | Riconciliazione delle regole: ogni regola una casa | accettata, 23/10/2026 (Marco: R1-R4). Nessun valore cambia: i documenti si allineano | domini/spina.md, domini/notti.md, domini/glossario.md, domini/ereditato.md, domini/meteo.md, domini/archivio.md, domini/attrezzatura.md, domini/mosaico.md, piano.md, CLAUDE.md |
| 0034 | Le regole del meteo con le fonti verificate, e il punteggio della notte v4 | accettata, 24/10/2026 (Marco: raffiche, condensa, Luna, nomi, soglie dal suo archivio). | domini/meteo.md |
| 0035 | Le regole del cielo con le fonti verificate | accettata, 24/10/2026. Soglie tecniche scelte dalla sessione sulle convenzioni |  |
| 0036 | Le regole di ASTAP con le fonti verificate, e il catalogo stellare D50 | accettata, 24/10/2026. Raccoglie le decisioni del piano di ASTAP (D2-D8) che stavano |  |
| 0037 | Le regole delle misure dei frame con le fonti verificate | accettata, 24/10/2026. Soglie tecniche scelte dalla sessione sulle convenzioni |  |
