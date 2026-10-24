# 0021 -- L'attrezzatura porta i dati delle schede tecniche, e il setup ci calcola

**Stato:** accettata, 18/10/2026 (Marco). ADR 0033: i programmi verificati sono due (ADR 0029).
Non costruita: lo schema non ha OAG, distanziale, tolleranza, cerchio d'immagine, bias (`docs/piano.md`).

## Contesto

Lo schema chiedeva un campo solo se l'app ci faceva gia' un conto (commento su `instruments`):
apertura, focale, pixel, carico, fattore, posizioni, peso. Marco vuole la scheda tecnica che
pubblica il produttore, tutta modificabile: serve a riconoscere il pezzo e a fare conti che oggi
non si fanno (scala di guida, campo previsto, backfocus, carico). Una guida fuori asse (OAG) non
esisteva come pezzo.

Ricerca del 18/10/2026 sulle pagine ufficiali ZWO (ASI2600MM Pro, OAG, EFW, EAF, AM5),
SBFITSEXT 1.0, la documentazione di N.I.N.A., PHD2 e Astronomy Tools. Le cifre di Sky-Watcher,
Askar, Antlia e ASI120MM Mini sono state trovate solo su negozi.

## Decisione

### I campi, tipo per tipo

Comuni a tutti gli strumenti, come oggi: Nome, Marca, Modello, Peso (kg), Note. **F** = dai file,
**C** = calcolato; tutto il resto si scrive a mano. Ogni campo si corregge, e il valore scritto
vince su quello dei file (come oggi, strato del dichiarato).

- **Ottica**: Schema ottico (rifrattore, Newton, Schmidt-Cassegrain, Ritchey-Chrétien,
  Maksutov, obiettivo fotografico, altro; Marco, 18/10/2026), Apertura (mm), Focale nativa (mm),
  Cerchio d'immagine (mm), Backfocus richiesto (mm), Tolleranza del backfocus (mm). Rapporto
  focale C, sul setup.
- **Camera**:
  - Sensore (il nome, es. IMX571);
  - Risoluzione (px, larghezza × altezza): F, la piu' frequente fra i frame, moltiplicata per il
    binning (`NAXIS1/2`, `XBINNING`), cioe' il sensore intero;
  - Pixel (µm): F, nativo, come oggi (`XPIXSZ`);
  - Dimensione del sensore (mm): C, pixel × risoluzione / 1000;
  - Tipo di sensore: F, come oggi (`BAYERPAT`);
  - Bit dell'ADC (`BITPIX` dice il formato del file, non l'ADC: si scrive a mano);
  - Raffreddata (si'/no) e Raffreddamento (ΔT, °C);
  - Spessore fino al sensore (mm); Bias (ADU), per la luminosita' del cielo (ADR 0022; Marco, 18/10).
- **Camera di guida**: come la camera, senza raffreddamento. I frame di guida non entrano
  nell'archivio: dai file arriva solo il nome (`GUIDECAM`).
- **Ottica di guida** (il tubo guida): Apertura (mm), Focale (mm). PHD2 chiede la focale
  (openphdguiding.org/man/Basic_use.htm).
- **Guida fuori asse (OAG)**, tipo nuovo: Spessore (mm), Prisma (mm). Non ha focale: guida con
  quella del setup (PHD2, stessa pagina).
- **Montatura**: Carico con contrappeso (kg), Carico senza contrappeso (kg). Il Peso e' quello
  della testa.
- **Riduttore** (anche barlow: fattore sopra 1): Fattore, Backfocus richiesto (mm), Tolleranza
  del backfocus (mm), Cerchio d'immagine (mm). Sostituisce la colonna `backfocus_mm` scritta e mai chiesta.
- **Ruota portafiltri**: Numero di posizioni, Misura dei filtri (1,25″, 31 mm, 36 mm, 2″,
  50 mm quadrato), Spessore (mm).
- **Focheggiatore**: Passo (µm), Passi totali.
- **Distanziale**, tipo nuovo: Spessore (mm). Serve solo al backfocus.
- **Filtro**: come oggi le bande con Larghezza (nm); in piu' Misura (le stesse della ruota),
  Spessore (mm), Montato (si'/no), Per ottiche veloci (si'/no).
- Fuori, per scelta di Marco: full well, rumore di lettura, gamma dinamica.

### Il setup

Parti nuove: la guida (ottica di guida **oppure** OAG, piu' la camera di guida) e i distanziali,
anche piu' d'uno. Si scelgono come le altre parti; i file non le dicono.

I conti, ognuno solo quando ci sono tutti i suoi dati; se ne manca uno, il setup dice quale:

- **Rapporto focale** = focale effettiva / apertura dell'ottica.
- **Campionamento** ("/px; nome scelto da Marco per la scala prevista) = 206,265 × pixel /
  focale effettiva (Astronomy Tools; ADR 0016), accanto a quello misurato sul cielo.
- **Campo previsto** = 2·atan(lato del sensore / (2 · focale effettiva)), per lato.
- **Copertura**: la diagonale del sensore contro il cerchio d'immagine del riduttore, o
  dell'ottica senza riduttore. E' un confronto, non una soglia.
- **Scala di guida** = 206,265 × pixel di guida / focale di guida; la focale e' quella dell'ottica
  di guida, o la focale effettiva del setup con l'OAG. **Avviso fuori da 0,5-4 "/px**: "The
  preferred range is roughly between 0.5 arc-sec/px and 4 arc-sec/px" (Bruce Waddington,
  sviluppatore di PHD2, groups.google.com/g/open-phd-guiding/c/TSP4CRpZP6E, 2022).
- **Rapporto guida/ripresa** = scala di guida / scala prevista, **senza giudizio** (Marco): nessuna
  convenzione lo fissa. Le regole trovate vanno da 3× a 20× (forum PHD2, ZWO 1:5 sulle focali,
  staff Diffraction Limited); Waddington stesso dice di ragionare sulla scala.
- **Campionamento**: la scala giusta sta fra 1/3 e 1/2 del seeing (Nyquist, Astronomy Tools:
  "a resolution between 0.67” and 2” per pixel is the sweet spot" con seeing 2-4",
  astronomy.tools/calculators/ccd_suitability). Sul setup, rovesciata: "ottimo con seeing fra
  {2s} e {3s}"", con s la scala. **In Meteo**, per la notte e per ogni setup, col seeing previsto
  (Marco): sottocampionato sopra 1/2, sovracampionato sotto 1/3. Senza chiave Meteoblue il seeing
  non c'e' (`docs/domini/meteo.md`), e il giudizio in Meteo tace.
- **Potere risolutore dell'ottica** ("): Dawes 116 / apertura in mm (Astronomy Tools,
  astronomy.tools/calculators/telescope_capabilities), sulla scheda dell'ottica.
- **Backfocus del treno**: spessori di OAG, ruota, distanziali e camera, contro il backfocus
  richiesto del riduttore (o dell'ottica senza). Si mostra la differenza in mm. Il giudizio ("in
  tolleranza", "corto di", "lungo di") c'e' solo se la scheda porta la tolleranza del produttore:
  nessuna convenzione unica la fissa, dipende dall'ottica (Marco, 18/10/2026). Lo spessore del filtro non si conta (lo spostamento del fuoco non e'
  verificato).
- **Carico**: peso di ottica, camera, riduttore, ruota, focheggiatore, guida, camera di guida e
  distanziali, contro il carico piu' alto dichiarato della montatura. **Solo la percentuale**,
  avviso solo sopra il 100 % (Marco): nessun produttore pubblica un margine, i negozi e i forum
  dicono dal 50 al 75 %.
- **Le parole a schermo** (Marco, 18/10/2026, sulla tavola v16): accanto all'avviso anche la
  parola buona, sugli stessi confini: "entro il carico" / "oltre il carico" (100 %),
  "nell'intervallo" / "fuori intervallo" (0,5-4 "/px), "copre il sensore" / "non copre il
  sensore". Nessuna soglia nuova.

### Dai file

Solo cio' che sta gia' negli header letti: nomi dei pezzi, pixel, tipo di sensore, risoluzione,
focale effettiva. `APTDIA` (SBFITSEXT) entra solo se un header vero di un programma verificato
lo porta (`backend/tests/header/`): N.I.N.A. non lo scrive.

## Conseguenze

- Il modulo di un pezzo si allunga: blocchi per tipo, campi tutti facoltativi salvo il nome. Lo
  schema cambia (`instruments`, `filters`, `rig_parts`) e si ricrea, come ogni volta.
- Il backup delle risposte (ADR 0017) porta i campi nuovi.
- La scheda del setup guadagna una sezione di conti; ognuno dice cosa gli manca.
- Meteo guadagna il giudizio del campionamento per setup (contratto `docs/domini/meteo.md`).
- Fuori, per ora: la misura minima del filtro (Astronomy Tools non mostra la formula) e la
  distanza della polvere (serve un'immagine).
- Due soglie restano solo numeri senza giudizio: rapporto di guida e margine del carico. Se un
  giorno una fonte vera le fissa, si aggiungono.
