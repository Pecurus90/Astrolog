-- AstroLog -- lo schema, UNICA verita' del DB. Nessuna migrazione fino al
-- rilascio: `tools/reset_db.py` ricrea il file da qui e da nient'altro.
--
-- Convenzioni: tutte le tabelle STRICT; le date sono testo ISO 8601 in UTC (la
-- conversione al fuso del sito e' del backend, alla presentazione); ogni tabella dichiara
-- in testa se e' DICHIARATO (lo ha detto l'utente: sopravvive ai reset, si esporta) o
-- RILEVATO (lo ricava l'app dai FITS, dal solver o dal catalogo: si ricalcola). NULL vuol
-- dire "non so", mai zero. I nomi vengono dal glossario (docs/domini/glossario.md).
--
-- Le quattro tabelle i cui NUMERI DI RIGA viaggiano nelle risposte di Da confermare --
-- instruments, filters, rigs, objects -- hanno l'id AUTOINCREMENT, e sono le sole (lo prova
-- `backend/tests/test_db.py`): una risposta porta l'id del pezzo, e tre di loro l'Applica le
-- conferma dicendo "ho visto fin qui" col numero (`backend/astrolog/api/review_write.py`). Tutte e
-- quattro perdono righe (le unioni, la spazzata di identify, i corredi rimasti senza pose).
-- Senza, SQLite ridarebbe il numero piu' alto appena liberato alla riga nuova: una risposta da
-- una pagina aperta prima finirebbe su di lei, o la farebbe nascere gia' "vista". Il perche' per
-- esteso sta in `docs/domini/spina.md`.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================ DICHIARATO

-- Le preferenze dell'utente e i valori di fabbrica che puo' cambiare una volta
-- (nome, lingua, altezza minima, distanza dalla Luna, ore minime...). Chiavi chiuse
-- nel codice, mai libere.
CREATE TABLE config (
  key        TEXT PRIMARY KEY,
  value      TEXT,
  updated_at TEXT NOT NULL
) STRICT;

-- Un sito: da dove si osserva. Le coordinate le dichiara l'utente (quelle negli header sono
-- un indizio, mai un'assegnazione). Fuso e altitudine si RICAVANO dalle coordinate: il fuso
-- offline dai confini veri (mai dalla longitudine), l'altitudine da un servizio pubblico --
-- e se non si riesce restano vuoti, mai un valore inventato e mai 0 m.
-- Del cielo si salva la LUMINOSITA' in magnitudini per arcosecondo quadrato: e' la cosa che
-- si misura. La classe di Bortle si deriva da quella (`units.bortle_of`), non si memorizza:
-- e' una scala descrittiva senza confini ufficiali, e due tabelle in giro differiscono fino
-- a una classe. `sky_source` e `elevation_source` dicono COME lo si sa, perche' una misura
-- vale piu' di una stima -- e perche' spostando il sito si rifa' solo cio' che dalle
-- coordinate veniva: cio' che l'utente ha scritto resta sua parola.
-- L'orizzonte e' una lista di punti (azimut, altezza) in JSON, qualunque sia la strada con
-- cui e' entrato (.hrz, disegnato, libero = NULL).
CREATE TABLE sites (
  id           INTEGER PRIMARY KEY,
  name         TEXT NOT NULL,
  latitude     REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
  longitude    REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
  elevation_m  REAL,
  elevation_source TEXT CHECK (elevation_source IN ('declared', 'service')),
  timezone     TEXT,                                 -- IANA; NULL quando non si riconosce un
                                                     -- fuso (in mare aperto vale il nautico)
  sky_sqm      REAL CHECK (sky_sqm BETWEEN 10 AND 23),  -- gli stessi estremi di
                                                       -- units.SQM_MIN/SQM_MAX: questa
                                                       -- e' la guardia del database
  sky_source   TEXT CHECK (sky_source IN ('measured', 'service', 'scale')),
  horizon_json TEXT,
  is_default   INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0, 1)),
  created_at   TEXT NOT NULL,
  CHECK ((elevation_m IS NULL) = (elevation_source IS NULL)),
  CHECK ((sky_sqm IS NULL) = (sky_source IS NULL))   -- un numero senza la sua provenienza
                                                     -- non si sa quanto valga
) STRICT;
CREATE UNIQUE INDEX sites_name ON sites (name);
CREATE UNIQUE INDEX sites_one_default ON sites (is_default) WHERE is_default = 1;

-- Una cartella di FITS indicata dall'utente. Si ritira, non si cancella: i frame restano.
-- root_path e' nella forma che l'utente ritrova (api/paths.py): risolta, salvo un disco di rete
-- collegato a una lettera; puo' essere una cartella di rete.
CREATE TABLE folders (
  id         INTEGER PRIMARY KEY,
  root_path  TEXT NOT NULL UNIQUE,
  name       TEXT,
  retired_at TEXT,
  created_at TEXT NOT NULL
) STRICT;

-- Uno strumento posseduto: ottica, camera, montatura, riduttore, ruota, guida, focheggiatore.
-- `detected = 1` se lo ha creato la spina da un header (provvisorio finche' l'utente non
-- lo conferma in Da confermare); le specifiche le compila l'utente, mai internet.
-- I campi si chiedono solo se l'app ci fa qualcosa: rapporto focale, lato del sensore in
-- millimetri e scala in arcosecondi per pixel si DERIVANO e non stanno qui.
CREATE TABLE instruments (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  kind            TEXT NOT NULL CHECK (kind IN ('optics', 'camera', 'mount', 'reducer',
                                                'filter_wheel', 'guide_scope', 'guide_camera', 'focuser')),
  name            TEXT NOT NULL,                   -- come lo chiama l'utente; e' la chiave degli alias
  brand           TEXT,
  model           TEXT,
  camera_type     TEXT CHECK (camera_type IN ('mono', 'color')),
  pixel_size_um   REAL,                            -- camera: il pixel fisico piu' frequente fra i file (rilevato)
  pixel_from_sky_um REAL,                          -- camera: il pixel ricavato dalla scala misurata e dalla focale (rilevato)
  aperture_mm     REAL,                            -- ottica: con la focale da' il rapporto focale
  focal_mm        REAL,                            -- ottica: la focale nativa, senza riduttore
  reducer_factor  REAL,                            -- riduttore: 0.8 vuol dire un corredo diverso
  weight_kg       REAL,                            -- col carico della montatura dice se il corredo sta in piedi
  payload_kg      REAL,                            -- montatura: quanto regge
  slots           INTEGER,                         -- ruota portafiltri: quanti filtri ci stanno
  backfocus_mm    REAL,
  notes           TEXT,
  detected        INTEGER NOT NULL DEFAULT 0 CHECK (detected IN (0, 1)),
  created_at      TEXT NOT NULL,
  CHECK (kind = 'camera' OR camera_type IS NULL),
  CHECK (kind = 'camera' OR pixel_from_sky_um IS NULL),
  CHECK (kind = 'mount' OR payload_kg IS NULL),
  CHECK (kind = 'filter_wheel' OR slots IS NULL),
  CHECK (kind = 'reducer' OR reducer_factor IS NULL)
) STRICT;
CREATE UNIQUE INDEX instruments_kind_name ON instruments (kind, name);

-- Un filtro posseduto: marca, modello, tipo (la banda, dominio chiuso in vocab) e le
-- larghezze. Si sceglie dalla tendina dei modelli in commercio (che porta marca, nome e
-- banda) o si scrive un nome qualunque dichiarando la banda: `catalog_id` ricorda la voce.
-- `is_none` = "nessun filtro" esplicito (camera mono senza vetro davanti): una riga sola.
CREATE TABLE filters (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL,                        -- come lo chiama l'utente; e' la chiave degli alias
  brand      TEXT,
  model      TEXT,
  catalog_id TEXT,                                 -- id del modello di catalogo, NULL se nome libero
  passband   TEXT NOT NULL,                        -- la banda canonica: dal vocabolario, dal modello o dalle bande
  is_none    INTEGER NOT NULL DEFAULT 0 CHECK (is_none IN (0, 1)),
  color      TEXT,
  created_at TEXT NOT NULL
) STRICT;
CREATE UNIQUE INDEX filters_name ON filters (name);
CREATE UNIQUE INDEX filters_one_none ON filters (is_none) WHERE is_none = 1;

-- Le bande che un filtro lascia passare, una riga ciascuna, con la larghezza dichiarata:
-- un Ha a 3 nm ha una riga, un duo Ha/OIII ne ha due (7 e 5 nm). La larghezza e'
-- facoltativa (un anti inquinamento luminoso non la dichiara). Da queste righe si ricava
-- la banda canonica di `filters.passband`: un fatto, una casa.
CREATE TABLE filter_bands (
  filter_id INTEGER NOT NULL REFERENCES filters (id) ON DELETE CASCADE,
  band      TEXT NOT NULL,                         -- una banda del dominio chiuso (vocab)
  width_nm  REAL,
  PRIMARY KEY (filter_id, band)
) STRICT;

-- Le regole riusabili imparate in Da confermare: "quando l'header dice X, e' Y".
-- Una per (tipo, valore dell'header normalizzato); la spina le applica prima di chiedere.
-- Il bersaglio e' una chiave che sopravvive ai reset del rilevato: il nome del filtro o
-- dello strumento dichiarato, il nome pulito (o lo slug di catalogo) dell'oggetto.
CREATE TABLE header_aliases (
  id           INTEGER PRIMARY KEY,
  -- I generi che hanno grafie da imparare sono quelli che **crea la spina** leggendo un
  -- header: oltre ai primi, i tre che la posa nomina addosso a se' (ruota, focheggiatore,
  -- camera di guida). Senza, rinominare la propria ruota la fa rinascere alla notte dopo.
  kind         TEXT NOT NULL CHECK (kind IN ('filter', 'optics', 'camera', 'mount',
                                            'object', 'filter_wheel', 'focuser',
                                            'guide_camera')),
  header_value TEXT NOT NULL,                      -- normalizzato (vocab.normalize_header_value)
  target_key   TEXT NOT NULL,
  created_at   TEXT NOT NULL,
  UNIQUE (kind, header_value)
) STRICT;

-- Lo strato del dichiarato: un valore che l'utente ha impostato su un'entita', e che vince
-- sul rilevato. In lettura "presenza della riga vince"; il rilevato resta nella sua colonna.
-- `entity_key` e' una chiave che sopravvive ai reset del rilevato, mai un numero di riga:
-- per un oggetto il nome pulito o lo slug di catalogo, per
-- una notte "sito:<id>|<data>", per una sessione "notte|oggetto|corredo", e per delle
-- COORDINATE quelle che l'header portava, arrotondate al chilometro ("45.60,11.67") -- li' il
-- campo `site` dice il NOME del sito a cui appartengono le pose riprese di li'. Sono la chiave
-- giusta perche' la risposta e' un fatto sul posto e non su una notte: vale anche per le notti
-- che verranno.
-- Per l'ATTREZZATURA che i file non dicono (`signature`) la chiave e' la firma dell'header: grafia
-- di camera e telescopio, focale, sensore (ADR 0014, S1); il campo `gear` tiene in JSON i NOMI di
-- camera e ottica, la focale e cosa c'era davanti (`no_filter`, o `filter` col nome del filtro).
-- Vale anche per le pose che arriveranno con la stessa firma, in qualunque notte.
-- Per le pose che non dicono l'OGGETTO e di cui il cielo non dice niente (`frame`) la chiave e'
-- l'impronta della posa, non il gruppo, che porta la notte (ADR 0014, S2): la risposta del gruppo
-- si scrive su ognuna, e il campo `object` vale "catalog:<slug>", "name:<nome>" oppure "none",
-- cioe' non e' un oggetto (Marco, 15/9/2026).
-- Per un mosaico (`mosaic`) la chiave e' quella del mosaico -- l'impronta di una delle sue pose,
-- scelta quando nasce e poi ferma, che non dipende dalla camera -- e il campo e' `answer`: il valore e'
-- "no", oppure DI COSA e' il mosaico, "catalog:<slug>" o "name:<nome>", che e' il si' (Marco,
-- 22/9/2026). Si scrive una volta, e nessuno la ricalcola (Marco, 23/9/2026).
CREATE TABLE declarations (
  entity_type TEXT NOT NULL CHECK (entity_type IN ('object', 'rig', 'instrument', 'night', 'session', 'coordinates', 'folder', 'frame', 'mosaic', 'signature')),
  entity_key  TEXT NOT NULL,
  field       TEXT NOT NULL,
  value       ANY,
  created_at  TEXT NOT NULL,
  -- the single frame carries only the answer on its object (ADR 0014, S2)
  CHECK (entity_type <> 'frame' OR field = 'object'),
  PRIMARY KEY (entity_type, entity_key, field)
) STRICT;

-- ============================================================ RILEVATO

-- Un corredo: ottica + camera a una focale. Le focali che stanno entro il +-5 % sono la
-- stessa focale: il raggruppamento lo fa la spina prima di scrivere, e qui si conserva il
-- rappresentante del gruppo -- percio' l'impronta e' su uguaglianza esatta.
-- Il NOME che l'utente da' a un corredo non sta qui: sta fra le dichiarazioni, con la
-- chiave (ottica, camera, focale). Questa riga la fa la spina dalle pose, o l'utente
-- (`detected` = 0), e un'unione di due grafie la cancella; il nome invece deve tornare da solo
-- quando la spina ricostruisce il corredo, e quello scritto dall'utente dalla sua dichiarazione.
CREATE TABLE rigs (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  optics_id  INTEGER REFERENCES instruments (id),
  camera_id  INTEGER REFERENCES instruments (id),
  focal_mm   REAL,
  detected   INTEGER NOT NULL DEFAULT 0 CHECK (detected IN (0, 1)),
  created_at TEXT NOT NULL
) STRICT;
CREATE UNIQUE INDEX rigs_fingerprint
  ON rigs (COALESCE(optics_id, -1), COALESCE(camera_id, -1), COALESCE(focal_mm, -1));

-- Un frame: un file light (o un file che non dice cosa e': `unknown`, e finisce in Da
-- completare). L'identita' e' UNA, decisa alla scansione: `frame_hash` = sha256 delle
-- dimensioni e di 64 KB di pixel dal centro, stabile a una riscrittura dell'header. Due copie
-- dello stesso file sono un frame con due posizioni; niente fusioni, mai. I file di
-- calibrazione non entrano.
CREATE TABLE frames (
  id             INTEGER PRIMARY KEY,
  frame_hash     TEXT NOT NULL UNIQUE,
  image_type     TEXT NOT NULL CHECK (image_type IN ('light', 'unknown')),
  date_obs       TEXT,                             -- UTC ISO, dall'header: cio' che il file dice
  -- La notte della posa, da mezzogiorno a mezzogiorno nel fuso del posto (`local_tz`, NULL e'
  -- UTC): la scrive `scan` quando la posa entra, e si rifa' solo se il fuso non viene dalle
  -- coordinate dell'header e casa cambia fuso (`spine/home_nights.py`). Senza `DATE-OBS` e' la
  -- notte in cui il file e' stato scritto (Marco, 27/9/2026). Chi raggruppa per notte legge questa.
  local_night    TEXT,                             -- scan
  local_tz       TEXT,                             -- scan
  -- L'istante da cui viene la notte: `DATE-OBS`, o senza l'ora del file quando la posa e' entrata.
  -- Chi riscrive la notte quando casa cambia fuso parte da qui, perche' l'ora del file cambia
  -- ogni volta che lo si tocca (`positions.mtime`).
  night_instant  TEXT,                             -- scan
  exposure_s     REAL,
  gain           REAL,
  "offset"       REAL,
  ccd_temp_c     REAL,
  naxis1         INTEGER,
  naxis2         INTEGER,
  binning        INTEGER,
  pixel_size_um  REAL,
  bayer_pattern  TEXT,
  focal_mm_raw   REAL,
  filter_raw     TEXT,                             -- com'era scritto nell'header
  object_raw     TEXT,
  telescope_raw  TEXT,
  instrument_raw TEXT,
  -- Gli altri pezzi che l'header nomina, com'erano scritti. A differenza della montatura,
  -- questi i file li legano alla SINGOLA posa: N.I.N.A. scrive FWHEEL e FOCNAME, l'ASIAIR
  -- GUIDECAM. Il grezzo resta perche' `normalize` lo ririsolva dopo una rinomina, come fa
  -- con `telescope_raw`. Nessuno di questi entra nell'impronta del corredo: cambiare ruota
  -- non fa un secondo corredo.
  filter_wheel_raw TEXT,
  focuser_raw      TEXT,
  guide_camera_raw TEXT,
  software       TEXT,                             -- normalizzato (vocab)
  software_raw   TEXT,
  -- Tre giudizi sul grezzo, scritti dalla scansione (`spine/header_asks.py`): il file non dice la
  -- camera, non dice il filtro, nomina l'ottica. Dipendono solo da cio' che il file dice e dal
  -- vocabolario, che oggi cambia solo col codice: nessuno li riscrive (dopo il rilascio si', vedi
  -- il Parcheggio di `docs/coda.md`). Da confermare li filtra invece di rileggere l'archivio. Il
  -- ripiego e' il giudizio di un header che non dice niente, come il ripiego vuoto delle colonne
  -- grezze.
  asks_camera    INTEGER NOT NULL DEFAULT 1 CHECK (asks_camera IN (0, 1)),
  asks_filter    INTEGER NOT NULL DEFAULT 1 CHECK (asks_filter IN (0, 1)),
  names_optics   INTEGER NOT NULL DEFAULT 0 CHECK (names_optics IN (0, 1)),
  -- La posa aspetta una risposta sul tipo di file (DERIVATO dalla regola in `spine/stages.py`):
  -- chi cambia un suo ingresso -- il cielo, la posizione, la risposta della cartella -- lo
  -- riscrive subito, e chi legge legge questo.
  asks_type      INTEGER NOT NULL DEFAULT 0 CHECK (asks_type IN (0, 1)),
  -- Il file dichiara di essere stato lavorato dopo la camera: le calibrazioni applicate
  -- (`calibrated`), o due programmi diversi nominati insieme (`rewritten`). I due sono in
  -- ORDINE -- `calibrated` pesa di piu': dice che sono cambiati i pixel, non solo l'header.
  -- Non dice CHI, e da solo non toglie niente a nessuno: decide quale di due gemelli e'
  -- l'originale. Lo ricava `normalize` dall'header, perche' distinguere due programmi vuole
  -- il vocabolario.
  rewrite_mark   TEXT CHECK (rewrite_mark IN ('calibrated', 'rewritten')),   -- normalize
  ra_hint_deg    REAL,                             -- dall'header: indizio per il solver, non verita'
  dec_hint_deg   REAL,
  site_lat       REAL,                             -- dall'header: indizio per "rivedi i siti"
  site_lon       REAL,
  site_elev_m    REAL,
  header_json    TEXT NOT NULL,                    -- l'header intero, lista di coppie
  filter_id      INTEGER REFERENCES filters (id),  -- normalize
  object_id      INTEGER REFERENCES objects (id),  -- identify
  -- Il cielo misurato di questa posa non ha nessun candidato nel campo (1), ne ha (0), o non si sa
  -- (NULL: nessun cielo, o `identify` non e' ancora passato). Lo scrive `identify` e resta anche quando la posa torna in coda: la domanda
  -- sulle pose senza nome lo legge, e con lo stato dello stadio -- che una rimessa in coda azzera
  -- -- una cartella di pose cosi' sparirebbe dalla pagina a ogni Applica.
  empty_cone     INTEGER CHECK (empty_cone IN (0, 1)),                        -- identify
  -- Il gruppo della posa senza nome e senza cielo (`spine/unnamed.py`): scelto quando la posa
  -- arriva, e riscelto solo se casa cambia fuso e con lei la notte (`spine/home_nights.py`). La
  -- chiave porta la notte, la camera, il telescopio e il puntamento di chi ha aperto il gruppo, con
  -- cui si confronta chi arriva dopo.
  unnamed_key    TEXT,                                                        -- identify
  -- Cosa `identify` aveva trovato (slug o nome) per una posa che l'utente ha detto "non e' un
  -- oggetto": la chiave della sua scheda in Da confermare, che cosi' resta e si cambia. NULL
  -- altrimenti; una rimessa in coda non lo azzera. La risposta lo scrive subito: distingue il "non
  -- e' un oggetto" di una scheda da quello di un gruppo, che il cielo coi candidati scavalca.
  found_key      TEXT,                                                        -- identify, risposta
  rig_id        INTEGER REFERENCES rigs (id),     -- normalize
  filter_wheel_id  INTEGER REFERENCES instruments (id),   -- normalize
  focuser_id       INTEGER REFERENCES instruments (id),   -- normalize
  guide_camera_id  INTEGER REFERENCES instruments (id),   -- normalize
  -- La montatura: quella che hai dato al corredo, o dove taci quella che il file nomina
  -- (`spine/normalize_rig.py`). Non ha un grezzo suo: con l'ASIAIR sta in `telescope_raw`.
  mount_id         INTEGER REFERENCES instruments (id),   -- normalize
  -- La copia calibrata dello stesso scatto (l'elaborazione la riscrive nella cartella di
  -- acquisizione): resta in archivio con le sue posizioni, ma non e' un'altra ora di cielo.
  -- Chi conta le ore filtra `copy_of IS NULL`. Lo decide `normalize`; il grezzo vince.
  copy_of        INTEGER REFERENCES frames (id),   -- normalize
  -- La posa sopravvive alla sua notte e alla sua sessione: quelle sono derivate e si
  -- rifanno, lei no. `SET NULL` e non `CASCADE`, o cancellare una sessione porterebbe via
  -- delle pose.
  night_id       INTEGER REFERENCES nights (id) ON DELETE SET NULL,      -- group
  session_id     INTEGER REFERENCES sessions (id) ON DELETE SET NULL,    -- group
  -- L'inquadratura della posa (`panels`): la scrive `group` una volta, e non si rifa'.
  panel_id       INTEGER REFERENCES panels (id) ON DELETE SET NULL,      -- group
  -- Il mosaico CONFERMATO di cui la posa fa parte, o NULL: la chiave del mosaico, scritta da chi
  -- risponde e da `group` per le pose che arrivano dopo. Sta sulla posa e non sull'oggetto: lo
  -- stesso oggetto puo' avere pose dentro un mosaico e altre fuori.
  mosaic_key     TEXT,                                -- group, Da confermare
  created_at     TEXT NOT NULL
) STRICT;
CREATE INDEX frames_mosaic ON frames (mosaic_key) WHERE mosaic_key IS NOT NULL;
-- Le pose di un pannello, con cio' che serve a contarle e a dirne l'oggetto: i mosaici di Da
-- confermare e chi pesa i pannelli le leggono dall'indice, senza la tabella. Il prezzo lo paga chi
-- riscrive una di queste colonne su una posa gia' in un pannello, che aggiorna anche l'indice.
CREATE INDEX frames_panel ON frames (panel_id, copy_of, object_id, exposure_s)
  WHERE panel_id IS NOT NULL;
CREATE INDEX frames_unnamed ON frames (unnamed_key) WHERE unnamed_key IS NOT NULL;
-- Chi arriva cerca i gruppi della sua notte: senza, ogni posa rileggerebbe tutte le altre.
CREATE INDEX frames_unnamed_night ON frames (json_extract(unnamed_key, '$[0]'))
  WHERE unnamed_key IS NOT NULL;
CREATE INDEX frames_found ON frames (found_key) WHERE found_key IS NOT NULL;
-- Le pose di un oggetto, con cio' che serve a contarle: l'elenco degli oggetti di Da confermare le
-- conta tutte a ogni apertura, e dall'indice non legge la tabella.
CREATE INDEX frames_object ON frames (object_id, copy_of, exposure_s);
-- Le pose di un corredo, con cio' che serve a contarle: le conta la tendina dei corredi a ogni
-- apertura e a ogni Applica con una risposta sulla camera, e l'uso dell'Attrezzatura a fine giro.
-- Sulla sola colonna, chi conta le ore leggerebbe comunque la riga di ogni posa.
CREATE INDEX frames_rig ON frames (rig_id, copy_of, exposure_s, night_id);
CREATE INDEX frames_session ON frames (session_id);
CREATE INDEX frames_night ON frames (night_id);
-- Cio' che le pose di una notte locale dicono del corredo (`spine/night_rig.py`): lo chiedono la
-- domanda sulla camera e la normalizzazione, e dall'indice non leggono la tabella.
CREATE INDEX frames_local_night
  ON frames (local_night, instrument_raw, telescope_raw, software_raw, focal_mm_raw);
CREATE INDEX frames_date ON frames (date_obs);
-- Le pose di un filtro: le conta Da confermare, e la tendina dell'Archivio ci cerca la prima buona
-- (senza, anche un filtro con molte pose e nessuna buona scorrerebbe l'archivio), e l'uso
-- dell'Attrezzatura le conta dall'indice come per i corredi.
CREATE INDEX frames_filter ON frames (filter_id, copy_of, exposure_s, night_id);
-- Le pose su cui Da confermare chiede qualcosa, per i giudizi sul grezzo: la pagina legge solo
-- quelle, e un archivio i cui header dicono camera, filtro e ottica non ne ha nessuna.
CREATE INDEX frames_asks_camera ON frames (asks_camera) WHERE asks_camera = 1;
CREATE INDEX frames_asks_filter ON frames (asks_filter) WHERE asks_filter = 1;
CREATE INDEX frames_no_optics ON frames (names_optics) WHERE names_optics = 0;
-- I frame che non dicono che file sono: li rileggono tutti chi riscrive il segno dell'attesa quando
-- cambia una cartella o una risposta, e chi scrive le cartelle della domanda a fine stadio.
CREATE INDEX frames_image_type ON frames (image_type);
-- Chi aspetta una risposta sul tipo: il residuo della spina li toglie dal totale, e la pagina della
-- scansione lo chiede ogni secondo e mezzo mentre la corsa gira.
CREATE INDEX frames_asks_type ON frames (asks_type) WHERE asks_type = 1;

-- Dove sta un frame su disco: N posizioni per frame (stesso file in due cartelle).
-- `filesize` e `mtime` sono il pre-controllo della scansione incrementale.
CREATE TABLE positions (
  id         INTEGER PRIMARY KEY,
  frame_id   INTEGER NOT NULL REFERENCES frames (id) ON DELETE CASCADE,
  folder_id  INTEGER NOT NULL REFERENCES folders (id),
  rel_path   TEXT NOT NULL,
  filesize   INTEGER NOT NULL,
  mtime      REAL NOT NULL,
  status     TEXT NOT NULL DEFAULT 'present' CHECK (status IN ('present', 'missing')),
  seen_at    TEXT NOT NULL,
  UNIQUE (folder_id, rel_path)
) STRICT;
CREATE INDEX positions_frame ON positions (frame_id);

-- Lo stato di ogni frame in ogni stadio: la spina e' un grafo, non una linea, e gli archi
-- (chi dipende da chi) stanno in `spine/stages.py`. Ogni stadio lavora su cio' che per lui
-- e' `pending`; la ripresa e' "cio' che manca", mai "dal file N". Non esiste `running`:
-- l'"in corso" vive nel worker, e un processo che muore non lascia righe appese.
-- `reason` e' un codice chiuso (mai una frase) quando lo stato e' failed o skipped.
CREATE TABLE frame_stages (
  frame_id   INTEGER NOT NULL REFERENCES frames (id) ON DELETE CASCADE,
  stage      TEXT NOT NULL CHECK (stage IN ('solve', 'normalize', 'identify', 'group', 'measure')),
  status     TEXT NOT NULL CHECK (status IN ('pending', 'done', 'failed', 'skipped')),
  reason     TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (frame_id, stage)
) STRICT;
CREATE INDEX frame_stages_pending ON frame_stages (stage, status);

-- I mosaici: pannelli dello stesso corredo che si toccano senza contenersi (`docs/domini/
-- mosaico.md`). Li scrive `group` quando una posa apre un pannello, e nessuno li ricalcola.
-- `key` e' l'impronta di una delle sue pose, scelta quando nasce e poi ferma: la chiave della
-- risposta, che non cambia quando cambia la camera. Il centro e il nome proposto -- la voce del catalogo al
-- centro -- si riscrivono quando il mosaico cresce.
CREATE TABLE mosaics (
  id       INTEGER PRIMARY KEY,
  key      TEXT NOT NULL UNIQUE,
  ra_deg   REAL NOT NULL,
  dec_deg  REAL NOT NULL,
  proposed TEXT NOT NULL
) STRICT;

-- Le inquadrature: il cielo della posa che le ha aperte, e il mosaico di cui fanno parte.
-- `radius_deg` e' la mezza diagonale del campo, e con la declinazione restringe a una fascia i
-- pannelli con cui una posa nuova si confronta. `rig_id` NULL e' il corredo che non si sa.
CREATE TABLE panels (
  id           INTEGER PRIMARY KEY,
  rig_id       INTEGER,
  ra_deg       REAL NOT NULL,
  dec_deg      REAL NOT NULL,
  width_deg    REAL,
  height_deg   REAL,
  rotation_deg REAL,
  radius_deg   REAL NOT NULL,
  mosaic_id    INTEGER REFERENCES mosaics (id) ON DELETE SET NULL,
  -- Se il pannello regge una parte del lavoro del suo mosaico (`spine/mosaic_weight.py`): lo
  -- scrive chi piazza o stacca le pose (`mosaic.settle`), e chi legge guarda solo questo.
  counts_in_mosaic INTEGER NOT NULL DEFAULT 1 CHECK (counts_in_mosaic IN (0, 1))
) STRICT;
CREATE INDEX panels_rig_dec ON panels (rig_id, dec_deg);
CREATE INDEX panels_mosaic ON panels (mosaic_id) WHERE mosaic_id IS NOT NULL;

-- Il cielo del frame, misurato dal solver. Quello dell'header e' un indizio (`ra_hint_deg`),
-- non un cielo. La cache immutabile del solve sta fuori dal DB (cache/solve/<frame_hash>.*):
-- un reset rilegge da li' senza ri-risolvere.
CREATE TABLE frame_wcs (
  frame_id        INTEGER PRIMARY KEY REFERENCES frames (id) ON DELETE CASCADE,
  ra_deg          REAL NOT NULL,                   -- il cielo: senza questi tre non c'e'
  dec_deg         REAL NOT NULL,                   -- soluzione, e la riga non si scrive
  scale_arcsec_px REAL NOT NULL,
  -- Il rettangolo, invece, puo' mancare a soluzione buona: la rotazione se la matrice e'
  -- degenere, il campo se l'header non dice quanti pixel ha il sensore. Il centro e la scala
  -- restano, e valgono: pretenderli tutti butterebbe via un cielo che si e' misurato davvero.
  rotation_deg    REAL,                            -- convenzione CROTA2
  width_deg       REAL,
  height_deg      REAL,
  solved_at       TEXT NOT NULL
) STRICT;

-- Le misure per frame. Prima quelle che il solver da' nella stessa passata (HFD, stelle,
-- SNR), poi eccentricita' e fondo cielo (casella misura). NULL = non misurata.
CREATE TABLE frame_metrics (
  frame_id       INTEGER PRIMARY KEY REFERENCES frames (id) ON DELETE CASCADE,
  hfd_px         REAL,
  fwhm_px        REAL,
  stars          INTEGER,
  snr            REAL,
  eccentricity   REAL,
  sky_background REAL,
  sky_noise      REAL,
  source         TEXT NOT NULL CHECK (source IN ('astap', 'sep')),  -- mai l'header: si misura
  measured_at    TEXT NOT NULL
) STRICT;

-- Un oggetto dell'archivio: cio' che e' stato fotografato. Il nome vive in object_names.
-- Una voce di catalogo e' UN oggetto solo: due pose della stessa galassia che ne creassero due
-- sparpaglierebbero le ore, che e' il difetto contro cui esiste tutto identify. Lo garantisce
-- l'indice unico qui sotto; `catalog_slug` NULL (l'oggetto fuori catalogo) si ripete, perche'
-- in SQLite i NULL non contendono un indice unico.
CREATE TABLE objects (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  catalog_slug        TEXT,                        -- la voce di catalogo agganciata, se c'e'
  identity_method     TEXT CHECK (identity_method IN ('coord_confirmed', 'coord_review',
                                                      'exact_name', 'historic_name', 'user')),
  identity_confidence TEXT CHECK (identity_confidence IN ('certain', 'high', 'low', 'user')),
  identified_at       TEXT,
  created_at          TEXT NOT NULL
) STRICT;
CREATE UNIQUE INDEX objects_catalog_slug ON objects (catalog_slug);

CREATE TABLE object_names (
  id         INTEGER PRIMARY KEY,
  object_id  INTEGER NOT NULL REFERENCES objects (id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  origin     TEXT NOT NULL CHECK (origin IN ('raw', 'catalog', 'user')),
  is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
  UNIQUE (object_id, name)
) STRICT;
CREATE UNIQUE INDEX object_names_one_primary ON object_names (object_id) WHERE is_primary = 1;
-- Un nome, un oggetto: l'unicita' e' GLOBALE, non per oggetto. Due oggetti che si chiamano
-- tutti e due `M 31` sono il difetto stesso. Chi scrive cerca prima e poi crea: l'indice e' la
-- rete sotto, non la strada -- e serve davvero, perche' un nome puo' essere gia' di un altro:
-- nel catalogo 110 voci si spartiscono 42 nomi comuni (`HCG 92` e `NGC 7318` sono due dei
-- cinque "Stephan's Quintet").
CREATE UNIQUE INDEX object_names_name ON object_names (name);

-- Il meteo di una notte, per sito (RILEVATO: lo portano i servizi meteo, `astrolog.weather`,
-- contratto in `docs/domini/meteo.md`). Una riga per tipo -- la previsione o lo storico -- e per
-- fonte: un modello di Open-Meteo, Meteoblue, 7Timer, CAMS. Non sta su `nights`, che spazza le
-- notti senza pose: la notte di domani non ne ha ancora. La serie ora per ora e il riassunto
-- (verdetto, fattori, ore utili) si scrivono quando arrivano, e chi legge non calcola; il
-- riassunto e' NULL per una fonte che da sola non fa un verdetto (il seeing).
-- L'ultimo tentativo di una fonte meteo che non deve ripetersi troppo spesso (Meteoblue per i
-- crediti, lo storico per non martellare l'archivio dopo un rifiuto): quando e
-- com'e' andata. Serve a non rispendere crediti a ogni riavvio, e a dire perche' il seeing non
-- viene da li'.
CREATE TABLE weather_fetches (
  site_id      INTEGER NOT NULL REFERENCES sites (id) ON DELETE CASCADE,
  source       TEXT NOT NULL,
  attempted_at TEXT NOT NULL,
  status       TEXT NOT NULL CHECK (status IN ('ok', 'refused', 'unreachable', 'bad_answer')),
  PRIMARY KEY (site_id, source)
) STRICT;

-- Il vento in quota tipico di un sito: i 101 percentili del vento a 700 hPa medio nelle ore di
-- ogni notte dell'ultimo anno, quante notti li hanno fatti e le coordinate del posto che hanno
-- misurato (`weather/climate.py`). Una riga per sito, rifatta una volta l'anno o se il sito si sposta.
CREATE TABLE weather_climate (
  site_id          INTEGER PRIMARY KEY REFERENCES sites (id) ON DELETE CASCADE,
  latitude         REAL NOT NULL,
  longitude        REAL NOT NULL,
  computed_at      TEXT NOT NULL,
  nights           INTEGER NOT NULL,
  percentiles_json TEXT NOT NULL
) STRICT;

CREATE TABLE weather_nights (
  site_id      INTEGER NOT NULL REFERENCES sites (id) ON DELETE CASCADE,
  night_date   TEXT NOT NULL,                      -- YYYY-MM-DD nel fuso del sito, come `nights`
  kind         TEXT NOT NULL CHECK (kind IN ('forecast', 'observed')),
  source       TEXT NOT NULL,                      -- il modello o il servizio
  fetched_at   TEXT NOT NULL,
  hourly_json  TEXT NOT NULL,                      -- da mezzogiorno a mezzogiorno, ora per ora
  summary_json TEXT,
  PRIMARY KEY (site_id, night_date, kind, source)
) STRICT;

-- Una notte: da mezzogiorno a mezzogiorno nel fuso del sito. Due siti, stessa data: due notti.
-- Porta i dati irripetibili (meteo, Luna, ore di buio) nelle caselle che li aggiungono.
CREATE TABLE nights (
  id          INTEGER PRIMARY KEY,
  site_id     INTEGER NOT NULL REFERENCES sites (id),
  night_date  TEXT NOT NULL,                       -- YYYY-MM-DD nel fuso del sito
  site_source TEXT NOT NULL DEFAULT 'detected' CHECK (site_source IN ('detected', 'declared')),
  created_at  TEXT NOT NULL,
  UNIQUE (site_id, night_date)
) STRICT;

-- Una sessione: oggetto x notte x corredo.
CREATE TABLE sessions (
  id        INTEGER PRIMARY KEY,
  night_id  INTEGER NOT NULL REFERENCES nights (id) ON DELETE CASCADE,
  -- L'oggetto se ne va (la spazzata di `identify` toglie quelli rimasti a zero pose) e la
  -- sessione va con lui, per la stessa ragione del corredo qui sotto. Non porta via una posa
  -- a nessuno: un oggetto arriva a zero pose solo perche' `identify` gliele ha appena
  -- staccate tutte, e `group` -- che gira dopo, sempre, perche' `invalidate` li rimette in
  -- coda insieme -- stacca comunque notte e sessione da quelle stesse pose in apertura di
  -- corsa. Senza, premere Applica su un archivio gia' raggruppato moriva col database in
  -- faccia. Il perche' per l'utente sta nel contratto della spina.
  object_id INTEGER NOT NULL REFERENCES objects (id) ON DELETE CASCADE,
  -- Il corredo se ne va (due grafie unite in Da confermare) e la sessione va con lui: e'
  -- un derivato, e `group` la rifa' al giro dopo. Senza, l'unione falliva col database in
  -- faccia -- misurato, `FOREIGN KEY constraint failed`.
  rig_id    INTEGER REFERENCES rigs (id) ON DELETE CASCADE  -- vuoto: non si e' saputo
) STRICT;

-- La chiave della sessione. E' un indice su un'espressione e non un `UNIQUE` di colonne perche'
-- in SQLite due NULL non contendono: con `rig_id` vuoto -- una posa il cui corredo non si sa --
-- la stessa notte e lo stesso oggetto avrebbero potuto aprire due sessioni identiche.
CREATE UNIQUE INDEX sessions_key ON sessions (night_id, object_id, COALESCE(rig_id, -1));

-- La ricevuta di ogni scansione: cosa ha trovato, cosa e' cambiato, come e' finita.
-- E' l'unico stato persistito della scansione: il progresso vive in memoria nel worker.
-- Una corsa aperta ha `ended_at` e `status` NULL: un processo che muore non lascia un
-- "in corso" scritto da nessuna parte.
CREATE TABLE scan_runs (
  id         INTEGER PRIMARY KEY,
  folder_id  INTEGER NOT NULL REFERENCES folders (id),
  started_at TEXT NOT NULL,
  ended_at   TEXT,
  status     TEXT CHECK (status IN ('ok', 'stopped', 'aborted', 'error')),
  reason     TEXT,                                 -- codice chiuso, se aborted/error
  found      INTEGER NOT NULL DEFAULT 0,           -- file FITS incontrati, solo online compresi
  new        INTEGER NOT NULL DEFAULT 0,           -- frame mai visti prima
  unchanged  INTEGER NOT NULL DEFAULT 0,           -- pre-controllo size+mtime
  duplicates INTEGER NOT NULL DEFAULT 0,           -- stessa impronta in un'altra posizione
  missing    INTEGER NOT NULL DEFAULT 0,           -- posizioni non piu' trovate
  skipped    INTEGER NOT NULL DEFAULT 0,           -- calibrazione, stack, ancora in scrittura
  errors     INTEGER NOT NULL DEFAULT 0,
  online_only INTEGER NOT NULL DEFAULT 0,          -- FITS solo online: non aperti, si rivedono
  unreadable_dirs_json TEXT,                       -- cartelle senza permesso, elencate
  hidden_dirs_json     TEXT,                       -- sottocartelle nascoste lasciate fuori, elencate
  linked_dirs_json     TEXT,                       -- raggiunte da un collegamento o una giunzione
  errors_detail_json   TEXT,                       -- i file non letti, ognuno col suo codice
  skipped_by_reason_json TEXT                      -- quanti file saltati, per motivo
) STRICT;

-- Quanto e' servito ogni pezzo, corredo e filtro (DERIVATO: si riscrive intero a fine giro di
-- ogni stadio che cambia le pose, `spine/gear_usage.py`, e la pagina Attrezzatura lo legge e
-- basta). `subject_id` e' l'id della riga di `instruments`, `rigs` o `filters`: niente chiave
-- esterna, perche' punta a tre tabelle, e chi legge parte da quelle -- una riga orfana non si
-- vede. NULL nei quattro conteggi vuol dire "l'app non puo' saperlo", non zero; una riga che
-- manca vuol dire "non ancora contato" (un pezzo nato a meta' giro), che e' un'altra cosa.
CREATE TABLE gear_usage (
  subject         TEXT NOT NULL CHECK (subject IN ('instrument', 'rig', 'filter')),
  subject_id      INTEGER NOT NULL,
  frames          INTEGER,
  integration_s   REAL,
  untimed         INTEGER,
  nights          INTEGER,
  scale_arcsec_px REAL,                            -- solo i corredi: la mediana del cielo misurato
  width_deg       REAL,
  height_deg      REAL,
  objects_json    TEXT NOT NULL DEFAULT '[]',      -- cosa ci hai ripreso, dal piu' ripreso
  position        INTEGER NOT NULL,                -- l'ordine della pagina: prima il piu' usato
  PRIMARY KEY (subject, subject_id)
) STRICT;

-- I candidati del cielo per la scheda di un oggetto in dubbio, o di pose dette "non e' un oggetto"
-- (DERIVATO: li scrive `spine/object_candidates.py`, che dice quando; Da confermare li legge).
-- `object_key` e' la chiave stabile della scheda, perche' la riga dell'oggetto puo' non esserci
-- piu'. `rank` e' l'ordine, dal piu' probabile; `in_frame` NULL quando il cielo non porta lati o
-- rotazione.
CREATE TABLE object_candidates (
  object_key  TEXT NOT NULL,
  rank        INTEGER NOT NULL,
  slug        TEXT NOT NULL,
  name        TEXT NOT NULL,
  common_name TEXT,
  in_frame    INTEGER CHECK (in_frame IN (0, 1)),
  PRIMARY KEY (object_key, rank)
) STRICT;

-- Le cartelle della domanda sul tipo di file, coi frame senza tipo che contano (DERIVATO: le scrive
-- `spine/typeless_folders.py`, che dice quando; Da confermare le legge). La risposta non sta qui:
-- e' una dichiarazione, e si legge dalla sua casa. `position` e' l'ordine della pagina.
CREATE TABLE typeless_folders (
  key      TEXT PRIMARY KEY,
  root     TEXT NOT NULL,
  sub      TEXT NOT NULL,
  frames   INTEGER NOT NULL,
  position INTEGER NOT NULL
) STRICT;

-- ============================================================ IL CATALOGO
-- Derivato al 100%: si ricarica dal file impacchettato (`catalog/data/catalogo-*.json`) e
-- non si modifica mai da qui. Sta nel database e non solo nel file perche' `identify` deve
-- poter chiedere "cosa c'e' in questo pezzo di cielo" con una query, non leggendo 22.080
-- voci a ogni frame.

-- Una voce di catalogo: un oggetto reale con almeno una designazione e un cielo.
-- L'identita' e' lo `slug`, non un numero di riga: gli id si rinumererebbero a ogni
-- ricostruzione del catalogo, lo slug no. I campi sono i 19 decisi in
-- `docs/domini/catalogo.md`; NULL vuol dire "non si sa", e per molti oggetti e' la verita'
-- (una nebulosa oscura non ha magnitudine, una stella non ha dimensione).
CREATE TABLE catalog_entries (
  slug               TEXT PRIMARY KEY,
  name               TEXT NOT NULL,             -- la sigla principale, come si scrive
  common_name        TEXT,                      -- il nome che l'utente legge, in inglese
  ra_deg             REAL NOT NULL CHECK (ra_deg BETWEEN 0 AND 360),
  dec_deg            REAL NOT NULL CHECK (dec_deg BETWEEN -90 AND 90),
  -- Il versore: le stesse coordinate in cartesiane sulla sfera unitaria. Serve alla ricerca
  -- per cono: un cerchio sul cielo diventa un riquadro su x, y, z -- che un indice sa fare --
  -- e il wraparound dell'ascensione retta a 0/360 sparisce, invece di essere un caso da
  -- ricordarsi. La distanza vera si controlla dopo, sul prodotto scalare.
  x                  REAL NOT NULL,
  y                  REAL NOT NULL,
  z                  REAL NOT NULL,
  constellation      TEXT NOT NULL,             -- codice IAU a tre lettere
  type_code          TEXT NOT NULL,             -- i 21 codici nostri (GALAXY, DARK_NEBULA...)
  kinds_json         TEXT,                      -- le famiglie d'uso, per i filtri
  size_major_arcmin  REAL,
  size_minor_arcmin  REAL,
  position_angle_deg REAL,                      -- dove manca, si disegna un cerchio
  magnitude          REAL,
  magnitude_band     TEXT CHECK (magnitude_band IN ('V', 'B')),
  surface_brightness REAL,
  distance_ly        REAL,
  opacity            REAL,                      -- solo le nebulose oscure: la loro "luminosita'"
  src_json           TEXT,                      -- da dove viene ogni valore
  CHECK ((magnitude IS NULL) = (magnitude_band IS NULL))
) STRICT;
-- La ricerca per cono: si filtra il riquadro sui tre assi, poi si misura davvero.
CREATE INDEX catalog_entries_x ON catalog_entries (x);

-- Le designazioni di una voce: `M 31` e `NGC 224` sono la stessa cosa, e la prima e' la
-- principale. E' qui che un nome scritto nell'header trova il suo oggetto, ed e' il motivo
-- per cui le ore non si sparpagliano fra le sigle.
CREATE TABLE catalog_names (
  catalog     TEXT NOT NULL,                    -- `M`, `NGC`, `Abell`...
  designation TEXT NOT NULL,                    -- `31`, `224`, `1136`...
  -- La chiave con cui si cerca: `NGC|224`, scritta al caricamento. Normalizzare le colonne
  -- dentro la query (UPPER, REPLACE) costringerebbe a leggere tutte le 24.266 righe a ogni
  -- ricerca, e `identify` ne fara' una per posa.
  key         TEXT NOT NULL,
  slug        TEXT NOT NULL REFERENCES catalog_entries (slug) ON DELETE CASCADE,
  is_primary  INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
  PRIMARY KEY (catalog, designation)
) STRICT;
CREATE INDEX catalog_names_slug ON catalog_names (slug);
-- UNIQUE e non un indice qualunque: due sigle che si riducono alla stessa chiave renderebbero
-- ambigua la ricerca, e chi carica le ha gia' tolte. Qui lo si fa dire alla macchina.
CREATE UNIQUE INDEX catalog_names_key ON catalog_names (key);
CREATE UNIQUE INDEX catalog_names_one_primary ON catalog_names (slug) WHERE is_primary = 1;

-- Quale catalogo e' caricato adesso. Una riga sola: serve a sapere se il file impacchettato
-- e' cambiato (aggiornamento dell'app) e le tabelle vanno rifatte.
CREATE TABLE catalog_version (
  id        INTEGER PRIMARY KEY CHECK (id = 1),
  version   TEXT NOT NULL,
  entries   INTEGER NOT NULL,
  loaded_at TEXT NOT NULL
) STRICT;
