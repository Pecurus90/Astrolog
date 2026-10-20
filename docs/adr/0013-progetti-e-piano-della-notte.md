# 0013 -- Progetti e piano della notte: il Planner fa i progetti, la serata si compone a parte

**Stato:** accettata, 4/10/2026

## Contesto

Il Planner era scritto come "Planner e Progetti", senza dire come si passa da un oggetto da
riprendere a una sequenza per la notte. L'osservatorio di Marco sara' remotizzato e fara' anche
ricerca (esopianeti, NEO): una notte puo' contenere due transiti e tre NEO in fila, e deve
andare da sola dal crepuscolo all'alba.

## Decisione

- **Il Planner fa i progetti.** Un progetto e' un oggetto DSO, la sua inquadratura su Aladin Lite
  ([ADR 0005](0005-carta-del-cielo-aladin-lite.md)), un setup (ottica, camera, ruota e filtri
  dalla pagina Attrezzatura) e un obiettivo in ore per filtro (per esempio M31, 60 h: 20 in Ha,
  40 in LRGB). Si crea una volta e vale tutto l'anno.
- **Un progetto, un setup.** Lo stesso oggetto con due telescopi fa due progetti, ognuno col suo
  avanzamento.
- **Stati del progetto:** in attesa (creato, non iniziato), in corso, finito. Stanno nella pagina
  dei progetti.
- **L'avanzamento si conta dall'archivio**, mai a mano: i frame attribuiti all'oggetto e al
  setup. E' certo perche' la sequenza la generiamo noi e scrive in `OBJECT` il nome che l'app
  riconosce.
- **La serata si compone nella pagina delle sequenze**, non dall'inquadratura. Il wizard chiede
  cosa si fa stasera: propone i progetti in corso e in attesa che stanotte sono alti, con cio' che
  conviene (finestra utile, Luna, ore che mancano per filtro: con la Luna alta, la banda
  stretta); un DSO nuovo passa dal Planner; le altre categorie si scelgono da un elenco.
- **Le categorie della serata:** DSO dei progetti, stelle variabili, esopianeti, comete, NEO,
  occultazioni asteroidali, supernove e transienti, campagne AAVSO.
- **Il piano della notte ha quattro pezzi:** l'oggetto; la sua finestra utile, calcolata per
  categoria; i blocchi in fila su una linea del tempo grafica (crepuscoli, buio, Luna), coi
  margini prima e dopo ogni blocco, i tempi di cambio (puntare, centrare, mettere a fuoco) e i
  conflitti in rosso; l'export, **un solo file N.I.N.A. per la notte intera**. Gli eventi a orario
  fisso (transiti, minimi, occultazioni) si mettono per primi, gli oggetti flessibili riempiono i
  buchi per priorita'.
- **Il piano interno non dipende dal programma di ripresa:** N.I.N.A. e' la prima traduzione, le
  altre si aggiungono senza rifare il piano.
- **Le regole di ripresa** (Luna per banda larga e stretta, altezza minima, margini) vengono da
  convenzioni pubbliche verificate sulla fonte e citate accanto al numero; la prima da verificare
  e' la *Lorentzian moon avoidance*, che usa anche il Target Scheduler di N.I.N.A.
- **Le fonti online** si chiamano a richiesta, in cache, e mai dalla spina
  ([`domini/catalogo.md`](../domini/catalogo.md)): Sesame del CDS per i DSO che il nostro catalogo
  non ha, VSX dell'AAVSO per le variabili, NASA Exoplanet Archive per gli esopianeti, JPL Horizons
  e il Minor Planet Center per comete e NEO. Le fonti di occultazioni, transienti e campagne AAVSO
  si scelgono quando si costruiscono.
- **Nell'archivio come oggetti solo DSO e comete.** Un DSO trovato online si salva, con fonte e
  citazione, in una tabella di oggetti aggiunti, non nelle tabelle del catalogo (che si rifanno da
  capo a ogni versione); da li' anche la spina lo riconosce dal cielo. Una cometa si tiene per
  sigla e si riconosce dal nome che la nostra sequenza scrive. Variabili, esopianeti, NEO,
  occultazioni e transienti producono solo sequenze.
- **I frame di ricerca non hanno un trattamento speciale nella scansione:** si tengono fuori
  dalle cartelle dell'archivio. Chi li lascia dentro li paga col solver (circa 0,5 s a frame) e se
  li trova in Da confermare.
- **L'app non comanda l'hardware:** cupola, tetto, parcheggio e sicurezza restano a N.I.N.A.

### Il disegno (Marco, 19/10/2026)

- **Nome**: «Piano della notte», pagina `/piano-della-notte`. «Piano» resta vietato per il
  progetto.
- **Prima solo i DSO**, come l'ordine sotto; in piu' gli eventi a orario fisso gia' calcolati nel
  modo «Eventi» del Planner (transiti della ISS, eclissi, occultazioni lunari, ADR 0023).
- **Un piano per postazione** (una montatura, un setup): due postazioni, due piani della stessa
  notte.
- **Proposte** nell'ordine gia' deciso (ereditato.md: si chiude stanotte -> ore utili -> ore
  mancanti), coi numeri del Planner: ore visibili, distanza dalla Luna con la soglia delle
  Impostazioni, ore mancanti per filtro. Banda larga o stretta con la regola della Luna di Meteo
  e Dashboard (fase e altezza). La *Lorentzian moon avoidance* resta fuori: nessuna fonte
  primaria trovata (19/10/2026), solo descrizioni di forum.
- **Meteo**: una striscia sottile del verdetto ora per ora sotto la linea del tempo, col rimando
  a Meteo (Marco). Supera, per questa pagina, "meteo solo in Notti" di ADR 0023.
- **Tempi di cambio** (puntare, centrare, mettere a fuoco): li scrive l'utente in Impostazioni,
  nessun valore di partenza (Marco): nessuna fonte vale per tutti.
- **Conflitti in rosso**, solo regole gia' decise: blocchi sovrapposti, oggetto sotto l'altezza
  minima o l'orizzonte, banda larga con la Luna che la vieta, evento fisso spostato.
- **Export**: un file per la notte intera, per il sequencer avanzato di N.I.N.A. Il formato si
  legge da un file vero esportato da N.I.N.A. quando si costruisce: nessuno schema pubblico.

### Le categorie (Marco, 19/10/2026)

- **Due modi per notte e postazione, che non si mischiano** (Marco): fotografia (Deep sky e
  Sistema solare, comete comprese) oppure ricerca (esopianeti, NEO, variabili, mischiati fra
  loro). Una linea del tempo e un export per piano. Il disegno si fa tutto ora; la costruzione
  segue l'ordine sotto.
- **Proposte automatiche** dal sito e dall'orizzonte, in tutti e due i modi.
- **Due pulsanti** (Marco): uno completa la notte tenendo i blocchi messi a mano, uno la rifa'
  da capo. L'algoritmo: prima gli eventi a ora fissa, poi nei buchi gli oggetti liberi, prima chi
  chiude prima la sua finestra; a pari merito l'ordine gia' deciso (si chiude stanotte -> ore
  utili -> ore mancanti).
- **Due eventi di ricerca sovrapposti** (Marco): vince quello che ci sta tutto coi margini; a
  pari merito il piu' alto. L'altro resta fra le proposte.
- **Ricerca e' un elenco solo**; i tipi sono Criteri, non pagine.
- **La regola della Luna e' un'impostazione** (Marco): i due gradini della banda larga (25% e 50%
  di partenza) e l'altezza da cui la Luna conta (-5° di partenza, sotto "Le cose rimandate, decise"). Vale in tutta l'app:
  Meteo, Dashboard, Planner, Piano della notte ([`domini/meteo.md`](../domini/meteo.md)).
- **Deep sky** prende i progetti dal Planner.
- **Sistema solare**: pianeti e Luna come nel Planner, piu' le comete (Marco: si fotografano,
  non si misurano). Posizione da JPL Horizons, ricalcolata per ogni blocco.
- **Ricerca**: esopianeti, variabili, NEO, aggiunti per nome o trascinati. Transito di un
  esopianeta: blocco da 1 h prima dell'ingresso a 1 h dopo l'uscita, almeno 30 min
  (D. Conti, *A Guide to TTV Target Observing*, BAA 2022; Swarthmore Transit Finder).
- **Tempi in Impostazioni**, uno per passo, vuoti, scritti dall'utente: raffreddamento, unpark,
  puntamento e centratura, autofocus, meridian flip, park, riscaldamento. Il margine sta dentro
  il valore (Marco: "metto 15 invece di 10"). Sostituiscono il tempo di cambio unico.

### Il Sistema solare nel piano (Marco, 19/10/2026)

- **Luna, Sole e pianeti si salvano in Progetti**, senza ore da raggiungere: corpo, setup,
  mosaico (intero o zona) per Luna e Sole, sovrapposizione, ordine, filtro (Sole: luce bianca o
  Hα), posa e frame per pannello o per filtro.
- **Si riprendono a video** (Marco). L'app calcola per ogni pannello distanza e angolo dal
  centro del corpo; il programma li applica all'ora della ripresa. Candidati: N.I.N.A. con
  Orbitals (punta e insegue, github.com/ghilios/NINA.Joko.Plugin.Orbitals) e Lucky Imaging
  (raffica FITS); oppure SharpCap Pro (vedi sotto). **Da provare su una postazione vera** prima <!-- software-ok -->
  di costruire l'export.
- **Sul disco niente plate solving**: il puntamento e' quello della montatura; ai buchi
  risponde la sovrapposizione (20% di partenza, ADR 0023).
- **Il Sole di giorno**: nella stessa pagina, linea del tempo da alba a tramonto (interruttore
  Notte · Giorno della linguetta Sistema solare, sotto). Tetto, filtro solare e sicurezza restano
  a N.I.N.A.
- I frame di questi blocchi si tengono fuori dalle cartelle dell'archivio, come la ricerca.
- Un tempo in piu' fra i tempi della notte: lo spostamento fra due pannelli.
- **Il video lo esegue SharpCap Pro, solo per il Sistema solare** (Marco, 19/10/2026): <!-- software-ok -->
  N.I.N.A. con Lucky Imaging salva FITS e nessuna fonte conferma 30-40 fps (una sola: 3 fps a
  sensore intero, AstronoMolly 2024). L'app scrive un file `.scs` del Sequence Editor (vai al
  corpo con spostamento, inseguimento, filtro, posa, frame); `SharpCap.exe /runsequence <file>` <!-- software-ok -->
  lo esegue all'avvio (docs.sharpcap.co.uk/4.1/15_AdvancedTopics.htm). Il mosaico lo calcola <!-- software-ok -->
  l'app: il pianificatore di SharpCap vuole un allineamento a mano. Il formato `.scs` si legge da <!-- software-ok -->
  un file vero quando si costruisce. Deep sky e Ricerca restano a N.I.N.A.

### Le linguette e la postazione (Marco, 19/10/2026)

- **Tre linguette per tecnica**, al posto di Fotografia / Ricerca / Giorno: **Deep sky** (DSO e
  comete, pose lunghe), **Sistema solare** (Luna, pianeti, Sole: video; il Sole con
  l'interruttore Notte · Giorno), **Ricerca** (esopianeti, NEO, variabili). Una linguetta per
  notte e postazione, come "deep sky fa solo deep sky, ricerca fa solo ricerca".
- **Automazione della postazione, solo Si'/No** (Marco): tetto o cupola motorizzati, sensore di
  sicurezza, pannello per i flat. L'export scrive o no i passi di N.I.N.A. (Open/Close Dome
  Shutter, Park Dome, Wait Until Safe, Open/Close Flat Panel Cover;
  nighttime-imaging.eu/docs/master/site/sequencer/advanced/instructions/). Flat: sotto, "Le
  cose rimandate, decise". La chiusura d'emergenza («Close on unsafe»)
  e' un'opzione di N.I.N.A., non del file.
- **La ruota portafiltri si legge dal setup** (Attrezzatura): con la ruota contano i cambi filtro,
  senza no. Una OSC con ruota la mette nel setup.
- **Tempi uguali per tutta l'app** (Marco: 10 min nel deep sky non contano), vuoti, scritti
  dall'utente: avvio e chiusura (raffreddamento, unpark, apertura e chiusura del tetto, park,
  riscaldamento), per oggetto (puntamento e centratura, autofocus), durante le pose (cambio
  filtro, dither col settle e ogni quante pose, scaricamento della posa, un autofocus ogni X ore
  come stima, flip, spostamento fra pannelli). Nessuna fonte da' tempi standard (Target
  Scheduler non li stima); i tempi misurati sui log di Marco (agosto-ottobre 2026) sono solo
  esempi. La ricerca la protegge il suo margine prima dell'evento, piu' un conflitto quando il
  tempo libero prima di un evento fisso e' meno dei cambi.

### Come sceglie il piano automatico (Marco, 19/10/2026)

Pulsanti «Completa il piano» / «Rifai il piano» («sequenza» e' di N.I.N.A., vietata per il
piano). Regole fisse, nessuna impostazione per sceglierle.

- **Deep sky e Ricerca**: prima le ore fisse; poi, fra chi passa i filtri (altezza minima 30°,
  massa d'aria 2: Telescope Live, LCO; almeno la durata minima sopra soglia nel buio, come
  Telescopius; distanza dalla Luna), chi scende prima (Setting Soonest di Target Scheduler); a
  pari merito l'ordine delle proposte (chi si chiude, ore utili, ore mancanti: Percent Complete).
  Ogni blocco poi si sposta il piu' vicino possibile al suo transito, se c'e' spazio. Un blocco
  non scende sotto la durata minima (meno cambi: Target Switch Penalty). Dentro il blocco la
  banda larga nelle ore senza Luna, la stretta con la Luna (Brecher, S&T nov. 2017).
- **Sistema solare**: ogni corpo nelle ore sopra l'altezza minima con la classe di seeing
  migliore (le classi di Meteo), a pari merito la piu' vicina al transito; senza previsione, al
  transito. La previsione del seeing non ha verifiche pubblicate: e' una preferenza, non un
  conflitto. Giove: se la Macchia Rossa passa al meridiano centrale con Giove sopra soglia, il
  blocco si centra su di lei (visibile ±50 min, S&T). Luna a mosaico: piu' alta possibile, dal
  terminatore (Omegon, Sky at Night). L'altezza minima dei pianeti resta un'impostazione: le fonti
  la legano a diametro e filtro (Pellier, citato), nessun numero unico.
- **Meteo**: le ore «non adatte» si evitano finche' c'e' altro posto (Marco). Nessuno scheduler
  documentato lo fa in anticipo (Target Scheduler reagisce durante la notte): scelta nostra.
- Restano fuori, abitudini senza fonte: ordine dei filtri per altezza, distanza dalla Luna per
  singolo filtro, ordine ovest-est come regola a se'.

### Dalla documentazione di Target Scheduler (Marco, 19/10/2026)

Letta tutta (tcpalmer.github.io/nina-scheduler) e confrontata. Si prende:
- **Luna per oggetto con la lorentziana**, tre coppie: separazione richiesta = D / (1 +
  (giorni dalla Luna piena / W)^2), cioe' D a Luna piena e D/2 a W giorni. Codice:
  `GetMoonAvoidanceLorentzianSeparation` in `AstrometryUtils.cs` del repo
  tcpalmer/nina.plugin.targetscheduler (ciclo 29.53059 giorni). Partenze (Marco):
  - banda larga (L, RGB, colore) **120°/10**: 120 a Luna piena da ACP, forum e Telescopius; W
    tagliato da 14 perche' 120/14 chiede 57° anche a Luna nuova (un oggetto a 45° non passa
    mai); 10 ricavato dai numeri attribuiti a Telescopius (README di astro-recommender);
  - **OIII 90°/10**: piu' sensibile alla Luna (forum), 90 attribuito a Telescopius;
  - **Hα, SII, dual band 60°/7**: default nel codice di Target Scheduler e nella sua doc.
  Conta solo con la Luna sopra l'altezza scelta in Impostazioni (-5° di partenza): niente
  "relax" di Target Scheduler (`MoonAvoidanceExpert.cs`), la sua scala non ha fonte (Marco).
  Supera "La *Lorentzian moon avoidance* resta fuori" qui sopra e la distanza unica di 40°; la
  regola di fase 25/50% resta per il verdetto della notte in Meteo e Dashboard.
- **Crepuscolo ammesso per banda** (larga, stretta): buio astronomico di partenza; la stretta
  puo' cominciare dal nautico, cioe' col Sole sotto -6° (Target Scheduler: Nighttime,
  Astronomical, Nautical, Civil).
- **Altezza massima**, spenta di partenza.
- Non si prende: priorita' a mano (Marco: bastano le regole), punteggi e pesi, grader e throttle,
  ripianificare dopo ogni posa, Wait Plan, umidita', sincronizzazione: servono a chi decide
  durante la notte. Per dopo: flat per sessione, cadenza dei filtri, bilanciamento dei pannelli,
  blocco a cavallo del flip.

### Le cose rimandate, decise (Marco, 19/10/2026)

- **La Luna conta sopra -5°** (partenza, in tutta l'app; prima l'orizzonte): rete di fotometri
  TESS, cielo costante con la Luna sotto -5° a ogni fase (arXiv 2105.01066, §III.2.2); Schaaf per
  la Luna piena (arXiv 2507.11343). Niente "relax" di Target Scheduler: -15/+5 e la scala non
  hanno fonte, e Krisciunas & Schaefer 1991 da' alla Luna a 5° dal 38 all'83% del peso a 40°.
- **Filtri a blocchi** (Marco): tutte le pose di un filtro, poi il successivo; l'ordine dei
  blocchi lo da' la regola della Luna per banda. Nessun ordine per altezza.
- **Mosaico deep sky**: tutti i pannelli ogni notte, partendo dal piu' indietro, e il primo
  cambia ogni notte (forum; Mosaic Completion di Target Scheduler).
- **Meridian flip**: un blocco puo' passare il meridiano e paga il tempo del flip. Con «pausa
  prima del meridiano» scritta in Impostazioni (come in N.I.N.A.) il piano evita la zona da
  transito - pausa a transito + minuti dopo il meridiano (formula di Target Scheduler).
- **Flat** (solo col pannello, o di cielo se scelti): a fine notte, dopo il park, ogni notte,
  solo i filtri usati; 25 per filtro di partenza, avviso sotto 20 (20: Sky at Night, forum;
  30-50: High Point); dark-flat accesi di partenza (Marco), stesso numero; ogni notte di partenza,
  oppure ogni N giorni o a fine progetto (Flats Handling di Target Scheduler). **Flat di cielo**
  facoltativi per chi non ha il pannello: Sole fra -2° e -7° (Marco; numeri da una richiesta su
  N.I.N.A. e da un diario d'osservatorio, nessuna convenzione), istruzione Sky Flat, senza
  dark-flat (N.I.N.A. non li fa in quel modo).
- **Ricerca**: entrano le **campagne AAVSO** (Target Tool API, chiave dell'utente: filtro,
  cadenza, priorita', visibilita') e le **supernove brillanti da seguire** (Transient Name
  Server, chiave bot dell'utente; soglia di partenza mag 17, quella della lista di Rochester).
  Niente scoperta ne' segnalazione. **Occultazioni asteroidali: no** (tempo GPS, video, nessuna
  API pubblica delle previsioni).
- **Fonti**: variabili da VizieR (B/vsx, J/AcA/54/207 Kreiner), non dall'API VSX non ufficiale;
  NEOCP del Minor Planet Center solo per uso personale, scaricato per l'utente e mai ripubblicato.

## Conseguenze

- L'ordine: prima i DSO (progetti, inquadratura, piano, export); poi esopianeti, variabili,
  occultazioni e campagne AAVSO, che hanno coordinate fisse e si calcolano in locale; poi
  supernove e transienti; per ultimi comete e NEO, che chiedono la rete a ogni notte.
- Le curve di luce (fotometria) restano fuori: si fanno con AstroImageJ o col software
  dell'AAVSO. Restano fuori anche gli allarmi in tempo reale (lampi gamma, onde gravitazionali).
- `measure` resta "solo misure": nessun voto e nessuno scarto dei frame
  ([`domini/ereditato.md`](../domini/ereditato.md), *Le metriche di qualita'*).
- La tabella degli oggetti aggiunti nasce in `backend/astrolog/schema.sql` col Planner.
