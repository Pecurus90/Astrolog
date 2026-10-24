# Il Planner e i Progetti -- contratto

Il **Planner** e' dove si decide una ripresa che non esiste ancora: si cerca un oggetto, si
sceglie il setup, si inquadra, nasce un **progetto**. La pagina **Progetti** mostra i progetti e
a che punto sono, contati dall'archivio. Il Piano della notte, che compone una notte coi
progetti, ha il suo contratto: [`piano-della-notte.md`](piano-della-notte.md). Le parole stanno
in [`glossario.md`](glossario.md): setup (mai corredo), oggetto (mai bersaglio), progetto (mai
piano), Criteri (mai filtri), pannello (mai tessera), ore visibili (mai ore utili), mesi buoni
(mai stagione), Deep sky (mai cielo profondo).

Nessuna delle due pagine e' portata (24/10/2026): niente Aladin nel frontend, nessuna tabella dei
progetti in `schema.sql`. Le decisioni vengono da ADR 0005, 0006, 0013, 0023 e dalle tavole
approvate da Marco in Claude Design (Planner v23.1, Progetti, riordino v32); il disegno vince sulla
forma, questo contratto su cosa si fa e perche'. I testi fra «» sono quelli approvati; le
proposte non approvate sono dette tali.

## Cosa chiede l'utente

Le prove nascono col porting, una per riga.

| richiesta | prova |
|---|---|
| Cerco un oggetto per nome in tutto il catalogo; se non c'e', online, con la fonte accanto | -- |
| Restringo con i Criteri e vedo quanto sale stanotte, e se l'ho gia' ripreso | -- |
| Provo un setup che non ho ancora, solo per guardare | -- |
| Inquadro su un cielo fotografato vero: rotazione, mosaico, campo che entra | -- |
| Creo un progetto con ore per filtro; un doppione non nasce, mi mostra quello che c'e' | -- |
| Il progetto si aggiorna da solo dopo ogni scansione, anche sul NAS | -- |
| Simulo pianeti, Luna e Sole col mio setup, e li salvo per il Piano della notte | -- |
| Vedo gli eventi del sito: ISS su Sole e Luna, eclissi, occultazioni lunari | -- |

## Le decisioni

### Il percorso

**Trova, Scegli il setup, Inquadra, Crea, Salva, Segui** (ADR 0023). Il Planner fa i primi cinque,
Progetti l'ultimo. Un progetto = oggetto + setup + inquadratura + ore per filtro; si crea una volta
e vale tutto l'anno. **Un progetto, un setup** (R1, ADR 0033): lo stesso oggetto con due telescopi
fa due progetti, ognuno col suo avanzamento. **I progetti nascono solo nel Planner** (Marco,
24/10/2026): l'archivio non li propone; resta la produzione (`archivio.md`). Tre modi in testa,
stesso selettore: **Deep sky · Sistema solare · Eventi**; il setup scelto resta cambiando modo.

### Trova

- Per nome su **tutto il catalogo** dell'app, non solo l'archivio. Se il nome non c'e', Sesame del
  CDS, con la fonte accanto (fonti online sotto, *Oggetti aggiunti*).
- **Criteri**: di catalogo (tipo, dimensione da ... fino a, come `size` min e max di Telescopius;
  costellazione, catalogo, magnitudine, RA, Dec) e del cielo (altezza minima per una durata
  minima, Luna per filtro). Partenza dalle Impostazioni; nel Planner si cambiano per una ricerca
  senza salvarli. «Togli il criterio» / «Togli i criteri»; la parola «filtro» resta ai vetri.
- **«Gia' ripreso»** (Marco, 19/10/2026): nella riga le ore gia' in archivio («12 h in
  archivio»); Criterio «Archivio»: «Tutti» · «Mai ripresi» · «Gia' ripresi». Nessun altro
  pianificatore conosce l'archivio dell'utente. Archivio vuoto: il Criterio e' spento,
  «Nessun frame in archivio: si riempie con la scansione.» (Marco, 19/10/2026).
- **«Entra nel campo di {setup}»** come Criterio (col mosaico: «del mosaico»), regola
  dell'ellisse (sotto, *I giudizi*). Due setup scelti: l'oggetto deve entrare in tutti e due, e la
  pillola li nomina («di {setup 1} e {setup 2}»). Senza setup e' spenta, e il perche' si legge in
  una riga sotto, non solo al passaggio (sul telefono il passaggio non c'e'): «Spento: scegli un
  setup, serve il suo campo.» (Marco, 19/10/2026, «setup» al posto di «corredo»).
- **Ordina**: Catalogo (partenza) · Dimensione · Magnitudine · Luminosita' superficiale · Ora del
  transito («transita alle 01:15»). **Mai per ore visibili**: niente classifica «i migliori
  stanotte».
- Riga del risultato: nome, tipo, dimensione, ore visibili stanotte, «sale fino a {alt}° alle
  {ora}», la Luna per la banda del filtro, il segno se c'e' gia' un progetto.

### Il setup

- I setup di Attrezzatura (nome «ottica · camera»), oppure un **setup di prova**: focale,
  apertura, riduttore o barlow (fattore), sensore dalla lista o **sensore personalizzato** (pixel
  in µm, risoluzione in px). **Solo per guardare** (Marco): fascia fissa che dice che per salvare
  un progetto il setup va aggiunto in Attrezzatura; Salva spento, col perche'.
- **Lista dei sensori nostra**: nessun elenco aperto e' riusabile (AstroBin e Telescopius <!-- software-ok -->
  proprietari, Stellarium Oculars 17 reflex). Una riga per geometria, senza marca: nome, pixel, <!-- software-ok -->
  risoluzione, URL del produttore; millimetri calcolati. **Solo sensori di camere astronomiche
  dedicate**, reflex e mirrorless fuori (Marco). Base: le righe adatte dei 36 sensori di
  `old/backend/astrolog/equipment/data/sensori.json`, ricontrollate sui produttori. Risoluzioni
  diverse fra produttori (pixel utili o totali) sotto l'1%: la stessa riga, si tiene l'utile.
- **Uso del sensore** (Marco): Deep sky, Planetario, Solare, anche piu' d'uno; viene dall'uso che
  il produttore dichiara per le sue camere (URL accanto); senza dichiarazione, «Altri». Il
  selettore raggruppa per uso; nel Sistema solare apre su Planetario (Solare col Sole).
- Accanto: campo, campionamento e rapporto focale come la scheda del setup (ADR 0021). Due setup =
  due rettangoli concentrici, stesso centro e angolo.

### La carta

- **Aladin Lite v3, versione stabile 3.8.1**, LGPL-3.0-or-later (ADR 0005); la beta 3.9.0 non
  aggiunge il supporto ai telefoni, che il README dice non finito: si prova su tablet e telefono
  prima del disegno definitivo. Scartati: Stellarium Web Engine (AGPL, nessuna release), <!-- software-ok -->
  d3-celestial (fermo dal 2022), VirtualSky (non open source). Una carta sola per Planner e Carta
  del cielo.
- **Logo di Aladin visibile** («please leave the Aladin logo and link intact») e credito «CDS
  Aladin Sky Atlas, Unistra/CNRS · {mappa}»; con NSNS anche «Northern Sky Narrowband Survey, S.
  Ziegenbalg, CC BY-NC-SA».
- **Mappe a scelta** (Marco), dal registro HiPS del CDS (MocServer, 18/10/2026):

| mappa | ID HiPS | cielo | copyright |
|---|---|---|---|
| DSS2 colore (partenza) | CDS/P/DSS2/color | 100% | STScI/NASA, CDS |
| PanSTARRS colore | CDS/P/PanSTARRS/DR1/color-i-r-g | 76% | PS1 Science Consortium |
| Hα | simg.de/P/NSNS/DR0_2/halpha8 | 65% (nord) | Ziegenbalg, CC-BY-NC-SA 4.0 |
| OIII | simg.de/P/NSNS/DR0_2/oiii8 | 65% (nord) | idem |
| SII | simg.de/P/NSNS/DR0_2/sii8 | 65% (nord) | idem |
| OIII · Hα · SII | simg.de/P/NSNS/DR0_2/ohs8 | 65% (nord) | idem |
| Hα sud | CDS/P/SHASSA/H | 100% | Swarthmore College |

- NSNS e' non commerciale: mai nel pacchetto, ammessa solo scaricata in cache, col credito
  accanto alla carta (Marco, 24/10/2026; ADR 0003). Fuori Mellinger («All rights reserved»). «DSS2 Hα» non esiste. La
  copertura delle mappe del nord la da' il MOC della mappa; fuori, la carta lo dice (proposta:
  «Mappa non disponibile in questa zona del cielo») invece di restare nera.
- **Solo cache, nessun pulsante «scarica il cielo»** (ADR 0006): le tessere passano dal nostro
  server, che le tiene. Senza rete: stelle vettoriali HYG fino a mag 6.5 (ADR 0005) e una riga
  (proposta: «Cielo fotografico non disponibile senza rete»). Nessuno spinner sulla carta intera.
- Sopra la carta, nostri: rettangolo del campo (poligono coi vertici dal backend), mirino
  dell'oggetto (non un'ellisse), griglia dei pannelli, orizzonte del sito. Trascinare sposta
  l'inquadratura; centro in RA/Dec col punto («RA 10.68 Dec 41.27»). La carta occupa la maggior
  parte della pagina (Marco).

### La rotazione

- Angolo **dal Nord verso Est**, antiorario: ASCOM («angle from North... counterclockwise»), ASTAP
  («rotate east from north»), `frame_wcs.rotation_deg` (CROTA2). Est a sinistra.
- **0-180°** (Marco): girato di 180° il rettangolo copre lo stesso cielo («Solutions for CROTA2 come
  in pairs separated by 180°», Calabretta & Greisen 2002, §6.2); N.I.N.A. col rotatore pieno
  sceglie fra angolo e angolo + 180 (`CenterAndRotate.cs`). Sensore quadrato 0-90° (N.I.N.A.).
- L'avanzamento non dipende dall'angolo. L'angolo dei frame si mostra accanto a quello del
  progetto, confrontato modulo 180 (90 sui quadrati), tolleranza 1° (`rotationTolerance = 1.0`,
  `PlateSolveSettings.cs`).

### Il mosaico

Dal Framing Assistant di N.I.N.A. (`FramingAssistantVM.cs`): colonne × righe, partenza 1 × 1;
**sovrapposizione 20% di partenza** (`overlapPercentage = 0.2`), si cambia; pannelli numerati riga
per riga dall'alto a sinistra, «Pannello N»; centro di ogni pannello sulla sfera (spostamento
ruotato, poi gnomonica inversa: `ShiftGnomonic` in `Coordinates.cs`, riscritta in Python); sotto,
il campo totale. **Obiettivo per pannello**, il totale e' la somma. Il riconoscimento dei mosaici
dai frame resta senza soglia minima (`mosaico.md`).

### Stanotte e l'anno

Accanto alla carta, per l'oggetto e il sito attivo: **curva d'altezza** della notte (fasce del
cielo, altezza minima, orizzonte del sito, Luna, «adesso»), ore visibili; **periodo migliore**: 12
punti, il 15 di ogni mese, con le ore visibili, i mesi buoni segnati. **Mese buono** = il 15 l'oggetto ha almeno
**3 ore visibili**: Impostazione, nessuna convenzione (N.I.N.A. Sky Atlas «visible for» e
Telescopius lasciano scegliere), legenda «mese buono: da 3 ore, cambia in Impostazioni». Il meteo
non sta qui: rimando «Meteo di stanotte» (Marco). Senza sito: «Sito mancante» · «Aggiungi sito».

### Crea

- **Schema suggerito** dal tipo (emissione SHO, planetarie e resti HOO, il resto LRGB), cambiabile;
  su camera a colori niente SHO e HOO, schemi «Nessun filtro» e «Multibanda» (aiuto: «dual band,
  tri band, quad band»).
- **Filtri** di Attrezzatura usati o scelti per quel setup. Colore: nessun filtro, UV/IR,
  multibanda, anti-inquinamento; mono: L, R, G, B, banda singola. Regola dal numero di bande (la
  matrice di Bayer, non una convenzione). Gli altri **in «Tutti i filtri»**, chiuso, mai tolti:
  l'Hα su camera a colori e' un uso reale (Marco).
- **Ore per filtro** in ore e minuti, totale sotto; col mosaico «per pannello» e il totale. **Posa**
  per filtro facoltativa: serve solo a «mancano circa {n} frame».
- **Crea parte vuota** (Marco): filtri dello schema, ore a 0, posa vuota. Nessuna ora ne' posa
  suggerita: nessuna fonte.
- **Salva** porta alla scheda appena nata in Progetti. Stesso oggetto e setup: nessun doppione, si
  mostra quello (proposta: «Questo oggetto ha gia' un progetto con questo setup.» · «Apri il
  progetto»).

### I giudizi (Marco, 18-19/10/2026)

Un giudizio per riga, come le misure (ADR 0022): parola, segno e colore, mai il colore da solo.
Nessun giudizio d'insieme. Un giudizio solo dove una fonte fissa il confine o Marco lo sceglie.

- **Campionamento Deep sky**: ADR 0021, fra 1/3 e 1/2 del seeing previsto, stesse parole di
  Meteo; senza seeing solo il numero e «Giudizio col seeing previsto: serve la chiave Meteoblue.».
  Seeing = mediana delle ore visibili dell'oggetto stanotte; con nessuna ora visibile, «nessuna
  ora visibile: niente seeing per il giudizio». La FWHM dei frame sta in Progetti.
- **Campo**: «entra nel campo» / «non entra nel campo», per geometria: l'ellisse dell'oggetto (assi
  e angolo di posizione del catalogo) dentro il rettangolo ruotato del campo o del mosaico; senza
  angolo, asse maggiore contro il lato corto. Corregge la prima regola, che bocciava M 31 nel
  mosaico 2 × 1. Nessuna fascia «stretto».
- **Ore visibili stanotte** contro le ore del progetto: numeri, senza giudizio.
- **Momento migliore**: seeing previsto peggiorato con la massa d'aria, FWHM ∝ X^(3/5) (Roddier
  1981); se il seeing Meteoblue e' gia' riferito all'altezza, non si corregge due volte (da
  verificare al porting). Pillola verde «✓ migliore»; se anche l'ora migliore ha seeing cattivo lo
  dice il seeing, non la pillola.
- **Campionamento planetario**: rapporto focale critico = 2 × pixel / lunghezza d'onda (Nyquist sul
  taglio della diffrazione), lunghezza d'onda del filtro, 400 nm senza filtro o a colori (Marco).
  Sotto «sottocampionato», da li' in su «campionamento pieno»; nessun «sovracampionato» (de
  Hilster, «Optimal focal ratio part 2»: il critico e' un minimo). Stesso confine mono e colore.
  Sotto il critico, il fattore della barlow che lo raggiunge (critico / rapporto del setup).
- **Video al massimo**, solo il numero: Tmax = 3600 · P · s / (π · D) (P rotazione in ore, NASA
  Fact Sheet; s in ″/px; D in ″), un pixel di sfocatura al centro del disco (P. Tanga, lista
  Saturn-ALPO 2003, CMO n. 286). Per difetto: e' un massimo.
- **ADC**: sotto 35° «serve il correttore di dispersione atmosferica (ADC)» (M. Lewis, JBAA 131(5),
  2021); sopra nessuna parola.
- **Altezza minima di pianeti, Luna e Sole**: 30°, massa d'aria 2, come «oggetto basso» (ADR 0022).
- **Mercurio e Venere di giorno**: nel momento migliore, giorno dall'altezza del Sole, con
  «A {n}° dal Sole: non cercarlo mai a occhio o col cercatore.» (BAA, guida di Mercurio).
- **Sole**: fascia fissa del filtro solare (AAS): filtro a tutta apertura davanti all'ottica, mai
  da oculare, cercatore coperto. **Hα**: «Hα solo con un telescopio o un filtro Hα dedicato.».
- **Seeing e pianeti**: nessun giudizio; nessuna fonte lega il seeing previsto alla ripresa
  fortunata.

### I consigli (Marco, 19/10/2026)

Sotto un giudizio, una riga tenue senza pillola ne' colore: come arrivarci. Solo dove una fonte
pubblica la pratica; senza giudizio, niente consiglio. Testi approvati:

- Pianeti sottocampionati: «Per il critico: barlow {x}×. Il fattore cresce allontanando il sensore
  dalla barlow.» (M = 1 + x / f della barlow).
- Video al massimo: «Con la derotazione il tempo in tutto arriva a 3-4 volte; il singolo video
  no.» (Sky at Night).
- Pianeti, sempre: «Pose sotto 30 ms, almeno 30 fotogrammi al secondo; area di ripresa stretta
  attorno al disco.» (documentazione di SharpCap). <!-- software-ok -->
- Pianeti bassi o seeing da 2″: «Un filtro IR-pass soffre meno il seeing.» (produttori: fonte
  debole, solo consiglio).
- Deep sky sovracampionato: «Bin 2 × 2 (anche in elaborazione) o un riduttore: con bin 2 × 2,
  {s}″/px.» (ZWO, astronomy.tools).
- Deep sky sottocampionato: «Dithering e drizzle, con molti frame; oppure pixel fino a {p} µm con
  questa focale.» (Fruchter e Hook 1998), {p} = seeing / 2 · focale / 206.265.
- Fuori: regole 3.5 / 5 / 7 × pixel dei forum; gain, istogramma, filtri UV e metano, etalon.

### Il modo Sistema solare

- Mercurio, Venere, Marte, Giove, Saturno, Urano, Nettuno, Luna e Sole, col setup vero o di prova.
  In testa il corpo, data e ora (partenza adesso, o stanotte se e' giorno), il sito. Al centro il
  corpo col rettangolo del sensore nelle coordinate del corpo, ruotabile 0-180°.
- **Si salvano in Progetti, senza ore da raggiungere** (Marco, 19/10/2026): «Salva come progetto»,
  campi in [`piano-della-notte.md`](piano-della-notte.md) (*Sistema solare*). AstroLog non guida
  montatura ne' camera, e i video (SER, AVI) non entrano nell'archivio.
- **Immagini**, ognuna col suo credito visibile: Luna HiPS `CDS/P/Moon/LROC-WAC-100m` (pubblico
  dominio, LROC/ASU), zoomabile, nome IAU del cratere al clic (planetary-features del CDS); Sole
  l'immagine del giorno da Helioviewer, SDO HMI luce bianca o GONG Hα, con «Courtesy of NASA/SDO <!-- software-ok -->
  and the AIA, EVE, and HMI science teams» o il ringraziamento NSO; senza rete un disco grigio in
  scala; pianeti una foto per corpo in scala, Hubble OPAL (CC BY 4.0) e NASA, licenza controllata
  sulla pagina, «Foto per la scala: l'aspetto della notte cambia.».
- Diametro apparente = 2 · atan(raggio / distanza) alla data (raggi NASA Planetary Fact Sheet);
  accanto la prossima opposizione (Mercurio e Venere: massima elongazione).
- **Calcoli nostri, senza librerie nuove**: fase, terminatore, colongitudine, librazione e asse
  della Luna (Meeus cap. 53), P, B0, L0 del Sole (cap. 29), anelli di Saturno (cap. 45); test
  contro JPL Horizons (quantita' 10, 13, 14, 15, 17).
- **Mosaico di Luna e Sole**: pannelli fissati sul corpo (come Moon Panorama Maker), «Intero» o
  «Zona»; sulla Luna solo la parte illuminata, e la stima dei pannelli usa lo stesso conto.
  Sovrapposizione 20% di partenza (nessuno standard). Ordine: prima il terminatore («Il
  terminatore cambia in circa 30 minuti: riprendilo per primo.», Omegon). Rotazione della camera
  entro 10° o restano buchi.
- **Una domanda, un giudizio**: «entra intero» si dice sotto «Campo», non sotto il diametro.
- Numeri: diametro in ″ e in px, scala, campo, rapporto del setup e critico del filtro, per Luna e
  Sole «km per pixel» e numero di pannelli.

### Eventi e Macchia Rossa (Marco, 19/10/2026)

Si disegnano ora, si costruiscono dopo il resto del Planner.

- **Macchia Rossa**, con Giove: i passaggi al meridiano centrale nella notte (Sistema II, Meeus
  cap. 43; Project Pluto, circa un minuto), ognuno con una fascia di ±50 minuti sulla curva (Sky &
  Telescope). Longitudine come Impostazione con data e deriva: **91° al 1/6/2026, 1.75° al mese**
  (Sky & Telescope, da JUPOS). Disco di Giove girato al meridiano dell'ora scelta. Nessun
  passaggio alto: «Nessun passaggio con Giove sopra {altezza minima}°.».
- **Meridiano centrale di Marte** (Meeus cap. 42): numero e disco girato; mappa pubblica, licenza
  controllata.
- **Modo Eventi**, per il sito attivo, in lista per data dal piu' vicino; Criteri a pillole «Tutti
  · ISS · Eclissi · Occultazioni»; periodo in tendina, partenza da scegliere col backend:
  - **transiti della ISS su Sole e Luna**: ora al secondo, durata, diametro della ISS, larghezza
    della striscia, distanza dalla linea centrale; giudizio geometrico «sei nella striscia» /
    «fuori di {d} km». Orbita CelesTrak, calcolo SGP4: **dipendenza nuova, si chiede a Marco** al
    porting. Riga sempre: «Orbita del {data}: la previsione si rifa' a ogni orbita nuova.»;
  - **eclissi di Sole e di Luna** dal sito: contatti, grandezza («Grandezza»; «dal sito» solo col
    Sole), altezza, «al massimo, {ora}»; credito «Eclipse Predictions by Fred Espenak, NASA's GSFC»;
  - **occultazioni lunari dei pianeti**: sparizione e ricomparsa, lembo chiaro o scuro.
  - Fuori le occultazioni asteroidali (IOTA: dati loro). Altezza giudicata con l'altezza minima di
    pianeti, Luna e Sole; sul Sole l'avvertenza del filtro.
- Stati (proposte): «Nessun evento visibile da {sito} nei prossimi {n} giorni.»; «Orbita della ISS
  non scaricata: riprova.»; «Serve un sito: gli eventi dipendono da dove sei.».

### Le soglie dell'utente (Marco, 19/10/2026)

Ogni soglia che dipende da dove e come si riprende sta in **Impostazioni › Planner**, col valore
di partenza e la fonte accanto; dove il Planner la usa, una riga dice «da Impostazioni».

| Soglia | Partenza | Fonte |
|---|---|---|
| Altezza minima, Deep sky | 30° | massa d'aria 2 (AAVSO, IRAF) |
| Durata minima sopra l'altezza | 1 h | nessuna convenzione: scegli tu |
| Luna, banda larga (L, RGB, colore) | 120° a Luna piena, meta' a 10 giorni | ACP, Telescopius; W scelto (sotto) |
| Luna, OIII | 90° a Luna piena, meta' a 10 giorni | attribuito a Telescopius |
| Luna, Hα, SII, dual band | 60° a Luna piena, meta' a 7 giorni | Target Scheduler |
| Crepuscolo ammesso | larga: buio astronomico; stretta: buio astronomico o «crepuscolo nautico · Sole sotto -6°» | Target Scheduler |
| Altezza massima | spenta | Target Scheduler |
| Mese buono | 3 h visibili il 15 del mese | nessuna convenzione: scegli tu |
| Altezza minima di pianeti, Luna e Sole | 30° | massa d'aria 2 |
| ADC sotto | 35° | BAA, Lewis 2021 |
| Macchia Rossa | 91° (Sistema II) al 1/6/2026, 1.75° al mese | Sky & Telescope, JUPOS |

- **Luna per oggetto**, lorentziana di Target Scheduler: separazione = D / (1 + (giorni dalla piena
  / W)²), D a Luna piena e D/2 a W giorni (`GetMoonAvoidanceLorentzianSeparation`,
  `AstrometryUtils.cs`, ciclo 29.53059 giorni). W = 10 della banda larga ricavato dai numeri
  attribuiti a Telescopius (W = 14 chiederebbe 57° anche a Luna nuova). Conta con la Luna sopra
  l'orizzonte (ADR 0034); niente «relax» di Target Scheduler. Supera la distanza unica di 40°.
  Curva piccola lungo il mese col segno di stanotte; «Piu' la Luna e' piena, piu' l'oggetto deve
  stare lontano.». Pillola «Luna a 74° · servono 45°» per la banda del filtro.
- Restano fisse le regole fisiche: rapporto critico, campionamento, video al massimo, campo.

### L'orizzonte del sito (Marco, 19/10/2026)

Si importa in Impostazioni, uno per sito (`sites.horizon_json`). Formato di N.I.N.A.: testo,
coppie azimut altezza, riga `#` d'intestazione, almeno due coppie, i vuoti interpolati. Disegno a
360° (N in alto, E a destra) con la sagoma e l'altezza minima tratteggiata. Caricato, vale ovunque
conta l'altezza: ore visibili, momento migliore, mese buono, carta, Sistema solare, Eventi, Piano
della notte; il minimo per direzione e' il piu' alto fra orizzonte e altezza minima. Meteo no: la
Luna dietro un albero illumina lo stesso. Proposte: «Nessun orizzonte: conta solo l'altezza
minima.», «Il file non si legge: servono almeno due righe azimut altezza.», «con l'orizzonte di
{sito}».

### La pagina Progetti

- Nome: «oggetto · ottica · camera», come la produzione.
- **Gruppi** dai mesi buoni: «In corso» = mese buono adesso; «In attesa» = fuori, «torna buono a
  {mese}», un circumpolare mai; «Fermi» = mesi buoni passati tutti senza frame; «Finiti» =
  confermati dall'utente. Finito lo propone l'app a ore raggiunte («Obiettivo raggiunto. Segnarlo
  come finito?»), lo conferma l'utente; alzare l'obiettivo lo riapre.
- **Scheda**: miniatura (foto finale se c'e', altrimenti l'inquadratura), anello di avanzamento
  (ore fatte / obiettivo, lo stesso della Dashboard), barre per filtro, griglia dei pannelli col
  loro avanzamento, ultima notte, prossima notte buona, «fermo da {tempo}», mediane delle misure
  coi giudizi di ADR 0022. Ore a zero: «0 h di 8 h». Sistema solare: al posto della barra «ultima
  volta nel piano: {data}».
- **Azioni**: «Apri nel Planner», «Segna come finito» / «Riapri», «Elimina» («Il progetto sparisce.
  I frame restano nell'archivio.»).
- **Modifiche** (Marco): ore, filtri e pose sempre libere. Inquadratura, griglia o setup su un
  progetto iniziato: «{durata} gia' riprese non conterebbero piu'.» · «Salva lo stesso» /
  «Annulla», contato sui frame veri. Supera «griglia congelata» (`ereditato.md` A).
- **«Apri nel Planner»** riapre inquadratura, griglia, setup e ore com'erano: e' la via per
  rifare l'inquadratura e per dare l'obiettivo a un progetto gia' cominciato.
- Frame senza pannello: «{n} frame senza pannello: non risolti.». Vuoto: «Nessun progetto ancora.»
  · «Apri il Planner». Nessun pulsante «aggiorna».
- Dashboard: la carta «Progetti in corso» resta; il ↗ apre Progetti, una riga apre la sua scheda.

### L'avanzamento

Lo scrive la scansione (anche quella automatica sul NAS), non la lettura. Un frame conta se ha
stesso oggetto, stesso setup e centro risolto dentro il campo del progetto o del pannello; senza
soluzione conta per nome, senza pannello. Dashboard e Progetti leggono lo stesso numero. Il nome
che il nostro export scrive in `OBJECT` e' quello che l'app riconosce.

### Oggetti aggiunti e fonti online

- **Nell'archivio come oggetti solo DSO e comete** (ADR 0013). Un DSO trovato online si salva, con
  fonte e citazione, in una tabella di **oggetti aggiunti**, non nel catalogo (che si rifa' a ogni
  versione); da li' la scansione lo riconosce. Una cometa si tiene per sigla.
- Fonti a richiesta, in cache, mai dalla scansione (`catalogo.md`): Sesame del CDS per i DSO, JPL
  Horizons e Minor Planet Center per comete e NEO; le altre in `piano-della-notte.md`.

## Cosa NON fa

Non comanda montatura, camera o tetto. Non fa classifiche ne' punteggi d'insieme. Non scarica il
cielo per l'uso senza rete. Non salva un progetto su un setup di prova. Non propone progetti
dall'archivio. Non giudica dove nessuna fonte fissa un confine: mostra il numero. Fuori, idee per
dopo: macchie solari, esposizioni previste col S/N (`ereditato.md` F, parcheggio).

Al porting nascono: le tabelle progetti, pannelli con inquadratura, obiettivi per filtro, oggetti
aggiunti (`schema.sql`); la dipendenza `aladin-lite` 3.8.1; il file dei sensori, con un test che
lo confronta coi frame veri; le chiavi delle soglie in `db/config.py`.
