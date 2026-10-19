# 0023 -- Planner e Progetti: inquadratura, mosaico, setup di prova, filtri, modifiche

**Stato:** accettata, 18/10/2026 (Marco).

## Contesto

L'ADR 0013 dice cos'e' un progetto; le decisioni portate dal vecchio progetto stanno in
`docs/domini/ereditato.md` (A, F). Marco ha descritto il flusso del Planner il 18/10/2026; restavano
aperti rotazione, mosaico, sensori di prova, filtri per camera e modifica di un progetto iniziato.
Ricerca del 18/10/2026 sul codice di N.I.N.A. (MPL-2.0, branch develop), ASCOM, ASTAP, Calabretta
& Greisen 2002, CDS e pagine dei produttori di camere. Proposta per esteso:
`handoff/planner-proposta.md`.

## Decisione

### Il percorso

Trova, Scegli il setup, Inquadra, Crea (filtri e ore), Salva, Segui. La pagina si chiama
**Progetti** (glossario: progetto, non piano).

### La carta

Resta Aladin Lite v3 (ADR 0005, 0006), versione stabile 3.8.1, licenza LGPL-3.0-or-later
(github.com/cds-astro/aladin-lite). Scartati: Stellarium Web Engine (AGPL-3.0, nessuna release), <!-- software-ok -->
d3-celestial (solo vettoriale, fermo dal 2022), VirtualSky (non open source). Il logo di Aladin
resta visibile ("please leave the Aladin logo and link intact", README); credito "CDS Aladin Sky
Atlas, Unistra/CNRS" con il nome del HiPS (cds.unistra.fr/aladin-org/licences_aladin.html). Il
rettangolo ruotato si disegna come poligono coi vertici calcolati dal backend. Il supporto ai
telefoni non e' finito (README): si prova su tablet e telefono prima del disegno definitivo. La
beta 3.9.0 (1/6/2026) non lo aggiunge (CHANGELOG del repository): si resta sulla 3.8.1.

**Mappe a scelta** (Marco), dal registro HiPS del CDS (MocServer, 18/10/2026), solo cache e
nessuno scaricamento (0006):

| mappa | ID HiPS | cielo | pixel | copyright |
|---|---|---|---|---|
| DSS2 colore (partenza) | CDS/P/DSS2/color | 100 % | ordine 9 | STScI/NASA, CDS |
| PanSTARRS colore | CDS/P/PanSTARRS/DR1/color-i-r-g | 76 % | 1.6" | PS1 Science Consortium |
| Hα | simg.de/P/NSNS/DR0_2/halpha8 | 65 % (nord) | 6.4" | Ziegenbalg, CC-BY-NC-SA 4.0 |
| OIII | simg.de/P/NSNS/DR0_2/oiii8 | 65 % (nord) | 6.4" | idem |
| SII | simg.de/P/NSNS/DR0_2/sii8 | 65 % (nord) | 6.4" | idem |
| OIII · Hα · SII | simg.de/P/NSNS/DR0_2/ohs8 | 65 % (nord) | 6.4" | idem |
| Hα sud | CDS/P/SHASSA/H | 100 % | 26" | Swarthmore College |

- NSNS (Northern Sky Narrowband Survey) e' non commerciale: va bene per un'app gratuita; chi
  vendesse l'app dovrebbe toglierla. Il credito va accanto alla carta.
- Fuori: Mellinger ("All rights reserved", la cache sarebbe una copia). "DSS2 Hα" non esiste:
  il DSS2 ha rosso, blu e vicino infrarosso.

### La rotazione

- Angolo dal Nord verso Est, antiorario: ASCOM ("angle from North... counterclockwise",
  ascom-standards.org/newdocs/rotator-faq.html), ASTAP ("rotate east from north", hnsky.org/astap.htm),
  `frame_wcs.rotation_deg` (CROTA2).
- **Intervallo 0-180°** (Marco): un rettangolo girato di 180° copre lo stesso cielo; "Solutions
  for CROTA2 come in pairs separated by 180°" (Calabretta & Greisen 2002, §6.2). N.I.N.A. con
  rotatore pieno sceglie da solo fra angolo e angolo + 180 (`CenterAndRotate.cs`). Sensore quadrato:
  0-90° (N.I.N.A., escursione "90 Degrees, useful primarily for square sensors").
- L'avanzamento non dipende dall'angolo. L'angolo dei frame si mostra accanto a quello del piano,
  confrontato modulo 180 (modulo 90 sui quadrati), tolleranza 1° (`rotationTolerance = 1.0`,
  `PlateSolveSettings.cs` di N.I.N.A.).

### Il mosaico

Dal Framing Assistant di N.I.N.A. (`FramingAssistantVM.cs`):
- colonne × righe, partenza 1 × 1;
- sovrapposizione in %, **partenza 20 %** (`overlapPercentage = 0.2`); si cambia;
- pannelli numerati riga per riga dall'angolo in alto a sinistra, «Pannello N»;
- centro di ogni pannello sulla sfera: spostamento ruotato poi proiezione gnomonica inversa
  (`Coordinates.cs`, `ShiftGnomonic`), riscritta in Python;
- obiettivo per pannello; il totale e' la somma (ereditato.md A).

### Il setup

- Setup veri di Attrezzatura, oppure **setup di prova**: focale, apertura, riduttore o barlow,
  sensore dalla lista. **Solo per guardare** (Marco): un progetto nasce solo su un setup vero.
- **Lista dei sensori nostra**: nessun elenco aperto e' riusabile (AstroBin e Telescopius <!-- software-ok -->
  proprietari, Stellarium Oculars 17 reflex). Una riga per geometria, senza marca: nome, pixel <!-- software-ok -->
  (µm), risoluzione (px), URL del produttore; millimetri calcolati. **Solo sensori montati in
  camere astronomiche dedicate**, deep sky e planetario (ZWO, ToupTek, Player One, QHY...); reflex
  e mirrorless fuori (Marco). Base: le righe adatte dei 36 sensori di
  `old/backend/astrolog/equipment/data/sensori.json`, ricontrollate sulle pagine dei produttori.
  Dove i produttori danno risoluzioni diverse (pixel utili o totali) vale la regola dell'1 % del
  vecchio progetto: sotto, la stessa riga.
- **Uso del sensore** (Marco): deep sky, planetario, solare, anche piu' d'uno per riga. Viene
  dall'uso che il produttore dichiara per le camere con quel sensore (es. ZWO presenta l'ASI174MM
  e l'ASI432MM per il solare, zwoastro.com), con l'URL accanto; senza dichiarazione, nessuna
  etichetta. Il selettore raggruppa per uso.
- **Sensore personalizzato** nel setup di prova (Marco): pixel (µm) e risoluzione (px), per chi
  ha un sensore fuori lista.

### I filtri

- I filtri proposti sono quelli di Attrezzatura usati o scelti per quel setup.
- Camera a colori: nessun filtro, UV/IR, multibanda, anti-inquinamento. Camera mono: L, R, G, B
  e banda singola. Regola dal numero di bande del filtro; non e' una convenzione pubblicata ma il
  funzionamento della matrice di Bayer.
- Gli altri filtri **nascosti in «Tutti i filtri»**, non tolti (Marco): l'Hα su camera a colori e'
  un uso reale.
- Ore per filtro in ore e minuti; esposizione del frame facoltativa (serve solo a «mancano circa N
  frame»). Schema suggerito dal tipo come in ereditato.md F.

### La pagina Progetti

- Nome: oggetto + ottica + camera, come la produzione.
- Gruppi in corso / in attesa / fermi / finiti; finito proposto dall'app, confermato
  dall'utente; eliminare non tocca i frame (ereditato.md A). La stagione e' fatta dei mesi buoni
  (sotto, "I giudizi"; a schermo «mesi buoni», mai «stagione», Marco 19/10/2026): in corso = mese
  buono adesso; in attesa = fuori dai mesi buoni, circumpolare mai; fermo = mesi buoni passati
  tutti senza frame (ereditato.md, "fermo da una stagione").
- **Modifiche** (Marco): ore, filtri ed esposizioni sempre libere. Inquadratura, griglia o setup
  su un progetto iniziato si cambiano **con un avviso numerico**: «{durata} gia' riprese non
  conterebbero piu'», contato sui frame veri. Supera "griglia congelata a progetto iniziato"
  (ereditato.md A).
- «Apri nel Planner» riapre il progetto con inquadratura, griglia, setup e ore com'erano: e' la
  via per rifare l'inquadratura e per dare l'obiettivo a un progetto gia' cominciato.

### L'avanzamento

Lo scrive la scansione (anche quella automatica sul NAS), non la lettura. Un frame conta se ha
stesso oggetto, stesso setup e centro risolto dentro il campo del progetto o del pannello. Senza
risoluzione conta per nome, senza pannello. Dashboard e Progetti leggono lo stesso numero.

### Planetario e solare

- **Nessun progetto**: niente ore da accumulare. Effemeridi in Dashboard (ADR 0019).
- **Simulazione, senza salvataggio** (Marco): Mercurio, Venere, Marte, Giove, Saturno, Urano,
  Nettuno, Luna e Sole, col setup vero o di prova (barlow e riduttore compresi). Nel Planner e'
  un secondo modo, «Sistema solare», accanto a «Deep sky»: cambia la carta, il setup resta.
  - **AstroLog simula, non segue**: i video planetari (SER, AVI) non entrano nell'archivio, che
    legge FITS; e non guida montatura ne' camera (ADR 0013). La ripresa di un mosaico lunare o
    solare la guidano programmi come SharpCap o Moon Panorama Maker (GPL-3.0, fermo dal 2019). <!-- software-ok -->
    ~~Nessun file esportato~~ **Superato (Marco, 19/10/2026)**: Luna, Sole e pianeti si salvano
    in Progetti (senza ore da raggiungere) ed entrano nel Piano della notte, ADR 0013 "Il Sistema
    solare nel piano". Lo spostamento dal centro del corpo, applicato all'ora della ripresa
    (Orbitals in N.I.N.A., o SharpCap Pro), toglie l'ostacolo delle RA/Dec che invecchiano <!-- software-ok -->
    (13,2°/giorno, cseligman.com/text/sky/moonmotion.htm); il programma del video e' da scegliere.
  - **Immagini**, ognuna col suo credito visibile:
    - Luna: HiPS `CDS/P/Moon/LROC-WAC-100m` in Aladin (100 m/px, pubblico dominio, LROC/ASU,
      astrogeology.usgs.gov), zoomabile; al clic il nome IAU del cratere (servizio
      planetary-features del CDS, Gazetteer USGS). A 0.2"/px un pixel e' circa 370 m sulla Luna:
      la mappa e' piu' fine del telescopio.
    - Sole: **l'immagine del giorno** (Marco) da Helioviewer, SDO HMI in luce bianca o GONG Hα a <!-- software-ok -->
      scelta; SDO "not copyrighted unless explicitly noted", credito "Courtesy of NASA/SDO and the
      AIA, EVE, and HMI science teams"; GONG col ringraziamento NSO. Rete e cache.
    - Pianeti: una foto per corpo, in scala. Giove, Saturno, Urano, Nettuno dalle mappe Hubble
      OPAL (CC BY 4.0, archive.stsci.edu/hlsp/opal); gli altri da NASA ("generally are not subject
      to copyright", nasa.gov/multimedia/guidelines). Licenza di ogni immagine controllata sulla
      sua pagina. Serve alla scala, non all'aspetto di quella notte.
  - Diametro apparente = 2 · atan(raggio / distanza) nella data scelta; partenza stanotte, accanto
    la prossima opposizione (Mercurio e Venere: massima elongazione). Raggi dal NASA Planetary
    Fact Sheet.
  - **Calcoli nostri, senza librerie nuove**: fase, terminatore, colongitudine, librazione e angolo
    dell'asse della Luna (Meeus, Astronomical Algorithms, cap. 53), P, B0, L0 del Sole (cap. 29),
    anelli di Saturno (cap. 45); i test confrontano con JPL Horizons (quantita' 10, 13, 14, 15, 17).
  - Disegno: rettangolo del sensore nelle coordinate del corpo, non in RA/Dec; fase disegnata
    sopra Mercurio, Venere e Luna; anelli di Saturno inclinati (raggio dal NASA Saturnian Rings Fact
    Sheet). Diametro in pixel accanto.
  - **Mosaico di Luna e Sole**: pannelli fissati sul corpo, come Moon Panorama Maker <!-- software-ok -->
    (`tile_constructor.py`); sulla Luna solo la parte illuminata. Sovrapposizione di partenza 20 %
    come nel cielo profondo (MPM usa 5-21 % secondo la camera; nessuno standard). Mostra quante <!-- software-ok -->
    pannelli e l'ordine: prima il terminatore, che cambia in circa 30 minuti (Omegon, rivista di un
    negozio). Rotazione della camera da tenere entro 10°, o restano buchi (forum SharpCap). <!-- software-ok -->
  - **Campionamento planetario**: rapporto focale critico = 2 × pixel / lunghezza d'onda (Nyquist
    sulla frequenza di taglio della diffrazione; vlaiv su Stargazers Lounge, astropix.com). La
    lunghezza d'onda e' quella del filtro scelto; senza filtro o a colori, 400 nm (Marco). Si
    mostra il rapporto del setup accanto a quello critico. Le regole 5-7 × pixel dei forum non
    entrano: non hanno fonte.
  - Il Sole porta l'avvertenza del filtro solare: filtro sempre davanti all'ottica, mai filtri da
    oculare, cercatore coperto (AAS, eclipse.aas.org/eye-safety/optics-filters).
- Transiti della Grande Macchia Rossa e meridiano centrale: decisi (sotto, "Eventi e Macchia
  Rossa").

### I giudizi (Marco, 18/10/2026)

Marco chiede un giudizio per riga, come le misure (ADR 0022): parola, segno e colore. Nessun
giudizio d'insieme. Supera la riga "nessuna pillola" della brief del sistema solare. Un giudizio
solo dove una fonte fissa il confine o Marco lo sceglie; il resto resta un numero.

- **Campionamento planetario**: sotto il rapporto focale critico «sottocampionato», da li' in su
  «campionamento pieno». Nessun «sovracampionato»: il critico e' un minimo, e nessuna fonte fissa
  un tetto (N. de Hilster, "Optimal focal ratio part 2", dehilster.info: "the factor 3.7 will
  lead to oversampling"; le regole 5-7 × pixel sono dei forum). Stesso confine per mono e colore:
  "the optimal focal ratio does not have to be adjusted to the type of camera, provided that
  stacking is applied" (de Hilster, che ritira il ×2 della parte 1).
- **Video al massimo**, solo il numero (Marco): Tmax = 3600 · P · s / (π · D), P periodo di
  rotazione in ore (NASA Planetary Fact Sheet), s scala in "/px, D diametro apparente in ".
  Sfocatura di un pixel al centro del disco: formula di P. Tanga, "Tmax [sec] = 1150xPxM/D"
  (lista Saturn-ALPO, 2003, ripresa in CMO n. 286, kwasan.kyoto-u.ac.jp/~cmo/cmomn2/286EGf.htm).
  Nessun campo per la durata voluta. Arrotondato per difetto: e' un massimo.
- **Altezza dei pianeti** all'ora scelta: sotto 35° «serve il correttore di dispersione». "An
  essential piece of equipment for high resolution imaging of planets when they fall below about
  35° altitude" (M. Lewis, J. Br. Astron. Assoc. 131(5), 2021, britastro.org/?p=613619).
- **Altezza minima di pianeti, Luna e Sole**: 30°, massa d'aria 2, la stessa di «oggetto basso»
  (ADR 0022, AAVSO e IRAF) (Marco, 19/10/2026). ALPO e BAA non fissano un minimo planetario.
- **Mercurio e Venere di giorno**: inclusi nel momento migliore, con la riga fissa della distanza
  dal Sole (Marco). Il minimo sicuro BAA (tan θ = D / L, "Guide to observing Mercury" v2.6, § 2.2)
  chiede la lunghezza del paraluce, che non c'e': nessun giudizio, solo l'avvertenza ("NEVER USE
  BINOCULARS TO LOOK FOR MERCURY IN DAYTIME", stessa guida).
- **Momento migliore**: seeing previsto peggiorato con la massa d'aria, FWHM ∝ X^(3/5) (Roddier
  1981, turbolenza di Kolmogorov). Se il seeing Meteoblue e' gia' riferito all'altezza, non si
  corregge due volte: da verificare quando si costruisce.
- **Barlow per il critico**: sotto il critico, accanto, il fattore che lo raggiunge (critico /
  rapporto del setup). Aritmetica sul confine gia' deciso, nessuna soglia nuova.
- **Hα**: col filtro Hα una riga fissa sul telescopio o filtro dedicato (etalon e filtro di blocco,
  Meade/Coronado; AAS per il filtro davanti all'ottica). Parole da Marco sulla tavola.
- **Seeing e pianeti**: nessun giudizio. Nessuna fonte lega il seeing previsto alla ripresa
  fortunata; le classi CMC (cleardarksky.com) descrivono l'immagine, non dicono se vale la pena.
- **Campionamento del cielo profondo**: quello di ADR 0021 (1/3-1/2 del seeing previsto), stesse
  parole di Meteo; senza seeing tace. Seeing = mediana delle ore visibili dell'oggetto stanotte. La
  FWHM in pixel (ADR 0022) resta sui frame, in Progetti.
- **Campo**: «entra nel campo» / «non entra nel campo» (Marco), per geometria: l'ellisse
  dell'oggetto (assi e angolo di posizione del catalogo) dentro il rettangolo ruotato del campo, o
  del mosaico. Senza angolo di posizione, asse maggiore contro il lato corto. Corregge la prima
  regola (sempre il lato corto), che bocciava M 31 nel mosaico 2 × 1 che la contiene. Nessuna
  fascia «stretto»: nessuna convenzione, i calcolatori di campo calcolano il campo e basta.
- **Ore visibili stanotte** contro le ore del progetto: numeri, senza giudizio.
- **Mese buono** nel periodo migliore: ✓ se il 15 del mese l'oggetto ha almeno 3 ore visibili.
  Impostazione dell'utente, partenza 3 ore (Marco, 19/10/2026). Nessuna convenzione: N.I.N.A.
  (Sky Atlas, «visible for») e Telescopius lasciano scegliere; stessa strada del calendario delle
  notti buone (`docs/coda.md`).
- **Crea parte vuota** (Marco): filtri dello schema in lista, ore a 0, esposizione vuota. Nessuna
  ora ne' esposizione suggerita: nessuna fonte.
- **Fuori**: macchie solari, idea per dopo. Macchia Rossa e meridiano di Marte: sotto, "Eventi e
  Macchia Rossa".

### Trova, in piu' (Marco, 19/10/2026)

Confronto con Telescopius, N.I.N.A. Sky Atlas, Deep-Sky Planner, SkySafari (ricerca del 19/10).

- **«Gia' ripreso»**: nella riga le ore gia' nell'archivio per quell'oggetto; filtro «mai
  ripresi» / «gia' ripresi». Nessun pianificatore conosce l'archivio dell'utente.
- **Dimensione da … fino a**, come Telescopius (`size` min e max).
- **«Entra nel campo»** come filtro: solo gli oggetti che stanno nel campo del setup scelto, o
  del mosaico, con la regola dell'ellisse (sotto). Nessuna soglia nuova.
- **Ordinamento**: nome (ordine del catalogo, partenza), dimensione, magnitudine, luminosita'
  superficiale, ora del transito. Mai per ore visibili: niente classifica «i migliori stanotte».
- Fuori: l'esportazione verso i programmi di ripresa va con la pagina delle sequenze (ADR 0013).

### I consigli (Marco, 19/10/2026)

Sotto un giudizio, una riga che dice come arrivarci: un input, non una guida. Solo dove una fonte
pubblica la pratica; i numeri escono dai conti gia' decisi, nessuna soglia nuova.

- **Pianeti sottocampionati**: «per il critico: barlow {x}×» (critico / rapporto del setup), e
  «il fattore cresce allontanando il sensore dalla barlow» (M = 1 + x / f della barlow, ottica).
- **Video al massimo**: «Con la derotazione il tempo in tutto arriva a 3-4 volte; il singolo video
  no.» Sky at Night: "extend your imaging time by a factor of three or four", "doesn't lift the
  restriction on the length of each video" (skyatnightmagazine.com, WinJUPOS). <!-- software-ok -->
- **Ripresa planetaria**: «Pose sotto 30 ms, almeno 30 fotogrammi al secondo; area di ripresa
  stretta attorno al disco.» Doc SharpCap: "exposures of less than 30ms have a chance to 'freeze' <!-- software-ok -->
  the seeing", "A smaller Capture Area helps achieve higher frames per second"
  (docs.sharpcap.co.uk, howtos/jupiter). <!-- software-ok -->
- **Basso o seeing incerto** (sotto la soglia del correttore, o seeing da 2″): «Un filtro IR-pass
  soffre meno il seeing.» Produttori (ZWO 850 nm, Astronomik 742): fonte debole, solo consiglio.
- **Cielo profondo sovracampionato**: «Bin 2 × 2 (anche in elaborazione) o un riduttore: con bin
  2 × 2 {s}″/px.» ZWO: "We don't really recommend you use BIN during DSO imaging unless your
  image is oversampled" (zwoastro.com, 2022); astronomy.tools.
- **Cielo profondo sottocampionato**: «Dithering e drizzle, con molti frame; oppure pixel fino a
  {p} µm con questa focale.» Siril: "If your image is significantly undersampled, you may be able <!-- software-ok -->
  to achieve an improvement in resolution using Drizzle" (siril.readthedocs.io); Fruchter e Hook <!-- software-ok -->
  1998. {p} = seeing / 2 · focale / 206.265.
- **Fuori**: regole 3.5 / 5 / 7 × pixel col seeing (Lodriguss, forum): restano fuori, il critico
  Nyquist decide. Gain, istogramma, filtri UV e metano, etalon: consigli di nicchia o del
  programma di ripresa, non del Planner.

### Le soglie dell'utente (Marco, 19/10/2026)

Ogni soglia del Planner che dipende da dove e come si riprende sta in **Impostazioni**, col valore
di partenza e la sua fonte accanto; nel Planner si cambia per una ricerca senza salvarla.

| Soglia | Partenza | Da dove |
|---|---|---|
| Altezza minima, cielo profondo | 30° | massa d'aria 2 (AAVSO, IRAF) |
| Durata minima sopra l'altezza | 1 h | Marco |
| Distanza dalla Luna | 40° | Marco |
| Mese buono | 3 h visibili il 15 del mese | Marco |
| Altezza minima di pianeti, Luna e Sole | 30° | massa d'aria 2 (AAVSO, IRAF) |
| ADC (correttore di dispersione atmosferica) sotto | 35° | BAA, Lewis 2021 |
| Macchia Rossa: longitudine, data, deriva | 91° (Sistema II) al 1/6/2026, 1.75° al mese | Sky & Telescope, da JUPOS |

Restano fisse le regole fisiche, che non dipendono dal sito: rapporto focale critico (Nyquist),
campionamento fra 1/3 e 1/2 del seeing, video al massimo (un pixel), campo che entra.
- **Meteo della notte**: solo in Notti, col rimando «Meteo di stanotte» (Marco).

### Eventi e Macchia Rossa (Marco, 19/10/2026)

Marco: "fare anche macchia rossa e transiti, in modo da avere tutto il disegno fatto". Supera la
riga "idee per dopo" dei giudizi. Si disegna ora; si costruisce dopo il resto del Planner.

- **Macchia Rossa**, nella carta di Giove: le ore in cui passa al meridiano centrale nella notte.
  Meridiano centrale nel Sistema II (Meeus, Astronomical Algorithms, cap. 43; Project Pluto,
  grs_form.htm: "accurate to about a degree", circa un minuto). La longitudine della Macchia
  deriva: e' un'impostazione con data e deriva, partenza 91° al 1/6/2026 e 1.75° al mese (Sky &
  Telescope, calcolatore dei transiti, dall'andamento JUPOS). Ben visibile 50 minuti prima e dopo
  il passaggio (Sky & Telescope). Il disco di Giove si disegna girato al meridiano dell'ora scelta.
- **Meridiano centrale di Marte** (Meeus cap. 42): il numero e il disco girato a quel meridiano.
  Mappa pubblica di Marte, licenza da controllare sulla sua pagina come le altre.
- **Terzo modo «Eventi»**, accanto a «Deep sky» e «Sistema solare», per il sito attivo:
  - **transiti della ISS su Sole e Luna**: ora al secondo, durata, diametro apparente della ISS,
    larghezza della striscia, distanza dalla linea centrale. Giudizio geometrico, nessuna soglia:
    «sei nella striscia» / «fuori di {d} km». Orbita da CelesTrak, calcolo SGP4 (come
    transit-finder.com e issinfo.net): dipendenza nuova, si chiede a Marco quando si costruisce.
    La previsione si rifa' a ogni orbita nuova; lontano nel tempo e' approssimata (transit-finder);
  - **eclissi di Sole e di Luna** visibili dal sito: contatti, grandezza, altezza. Elementi di
    Bessel di F. Espenak (NASA GSFC), col credito "Eclipse Predictions by Fred Espenak, NASA's
    GSFC";
  - **occultazioni lunari dei pianeti**: sparizione e ricomparsa, lembo chiaro o scuro, coi conti
    della Luna che gia' ci sono. Le occultazioni di asteroidi (IOTA) restano fuori: campagne con
    dati loro (ADR 0013, tappe).
- Altezza di Sole e Luna negli eventi giudicata con «Altezza minima di pianeti, Luna e Sole»; sul
  Sole l'avvertenza del filtro, come nel Sistema solare.

### L'orizzonte del sito (Marco, 19/10/2026)

- Si importa in Impostazioni, uno per sito. Formato di N.I.N.A.: testo, coppie azimut altezza, <!-- software-ok -->
  riga `#` d'intestazione, almeno due coppie, i vuoti interpolati (nighttime-imaging.eu, Options
  > General). Il file importato si mostra in un disegno a 360°.
- Caricato, vale in tutta l'app dove conta l'altezza di un oggetto: ore visibili, momento migliore,
  mese buono, carta del cielo, Sistema solare, Eventi. Il minimo in ogni direzione e' il piu' alto
  fra l'orizzonte e l'altezza minima delle Impostazioni.
- Non caricato: tutto come prima, solo l'altezza minima.
- Il cielo del Meteo non cambia: la Luna dietro un albero illumina lo stesso.

## Conseguenze

- Nuove tabelle: progetti, pannelli con inquadratura, obiettivi per filtro, oggetti aggiunti
  (ADR 0013). Lo schema si ricrea.
- Dipendenza frontend nuova: `aladin-lite` 3.8.1.
- ADR 0006 perde il pulsante "scarica il cielo": solo cache.
- File nuovo dei sensori, con test che lo confronta coi frame veri.
- `docs/domini/mosaico.md`: la frase "nessuno documenta un valore predefinito" era falsa per
  N.I.N.A.; il riconoscimento dei mosaici dai frame resta senza soglia minima.
- Brief per Design: `handoff/design-planner-progetti.md` (cielo profondo e Progetti) e
  `handoff/design-planner-sistema-solare.md`.
