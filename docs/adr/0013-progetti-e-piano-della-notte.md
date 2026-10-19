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
- **Il piano della notte ha quattro pezzi:** il bersaglio; la sua finestra utile, calcolata per
  categoria; i blocchi in fila su una linea del tempo grafica (crepuscoli, buio, Luna), coi
  margini prima e dopo ogni blocco, i tempi di cambio (puntare, centrare, mettere a fuoco) e i
  conflitti in rosso; l'export, **un solo file N.I.N.A. per la notte intera**. Gli eventi a orario
  fisso (transiti, minimi, occultazioni) si mettono per primi, i bersagli flessibili riempiono i
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
- **Conflitti in rosso**, solo regole gia' decise: blocchi sovrapposti, bersaglio sotto l'altezza
  minima o l'orizzonte, banda larga con la Luna che la vieta, evento fisso spostato.
- **Export**: un file per la notte intera, per il sequencer avanzato di N.I.N.A. Il formato si
  legge da un file vero esportato da N.I.N.A. quando si costruisce: nessuno schema pubblico.

### Le categorie (Marco, 19/10/2026)

- **Tre linguette nella stessa pagina**: Deep sky, Sistema solare, Ricerca. Una linea del tempo
  e un export per la notte: le categorie si mischiano. Il disegno si fa tutto ora; la
  costruzione segue l'ordine sotto.
- **Deep sky** prende i progetti dal Planner; «Riempi la notte» li mette in fila da soli nei buchi.
- **Sistema solare**: pianeti e Luna come nel Planner, piu' le comete (Marco: si fotografano,
  non si misurano). Posizione da JPL Horizons, ricalcolata per ogni blocco.
- **Ricerca**: esopianeti, variabili, NEO, aggiunti per nome o trascinati. Transito di un
  esopianeta: blocco da 1 h prima dell'ingresso a 1 h dopo l'uscita, almeno 30 min
  (D. Conti, *A Guide to TTV Target Observing*, BAA 2022; Swarthmore Transit Finder).
- **Tempi in Impostazioni**, uno per passo, vuoti, scritti dall'utente: raffreddamento, unpark,
  puntamento e centratura, autofocus, meridian flip, park, riscaldamento. Il margine sta dentro
  il valore (Marco: "metto 15 invece di 10"). Sostituiscono il tempo di cambio unico.

## Conseguenze

- L'ordine: prima i DSO (progetti, inquadratura, piano, export); poi esopianeti, variabili,
  occultazioni e campagne AAVSO, che hanno coordinate fisse e si calcolano in locale; poi
  supernove e transienti; per ultimi comete e NEO, che chiedono la rete a ogni notte.
- Le curve di luce (fotometria) restano fuori: si fanno con AstroImageJ o col software
  dell'AAVSO. Restano fuori anche gli allarmi in tempo reale (lampi gamma, onde gravitazionali).
- `measure` resta "solo misure": nessun voto e nessuno scarto dei frame
  ([`domini/ereditato.md`](../domini/ereditato.md), *Le metriche di qualita'*).
- La tabella degli oggetti aggiunti nasce in `backend/astrolog/schema.sql` col Planner.
