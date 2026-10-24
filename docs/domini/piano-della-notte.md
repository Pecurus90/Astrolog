# Il Piano della notte -- contratto

Il **Piano della notte** decide cosa si fa una notte (o un giorno, per il Sole), in che ordine, e
lo esporta in un file per il programma che riprende. Pagina `/piano-della-notte`, voce nel menu
Altro ([`navigazione.md`](navigazione.md)). I progetti li crea il Planner
([`planner.md`](planner.md)); qui si compongono. Le parole stanno in
[`glossario.md`](glossario.md): «piano», mai «sequenza» (e' la parola di N.I.N.A.); oggetto, mai
bersaglio; setup, mai corredo.

Non e' portata (24/10/2026): la voce manca da `pagine.tsx`. Le decisioni vengono da ADR 0013 e
dalla tavola approvata da Marco (Piano della notte v30.1 con le correzioni 0ter, riordino v32): il
disegno vince sulla forma, questo contratto su cosa si fa e perche'. I testi fra «» sono quelli
approvati, salvo dove e' detto «proposta».

## Cosa chiede l'utente

Le prove nascono col porting, una per riga.

| richiesta | prova |
|---|---|
| Vedo cosa conviene stanotte fra i miei progetti, con le ore che mancano per filtro | -- |
| Un pulsante riempie la notte con regole scritte e mi dice il perche' di ogni ora | -- |
| Vedo i conflitti in rosso solo per regole vere, e il meteo come striscia | -- |
| Esporto un file per la notte intera e lo apro nel programma di ripresa | -- |
| Con due montature faccio due piani della stessa notte | -- |
| Riprendo Luna, pianeti e Sole a video, coi pannelli calcolati dall'app | -- |
| Metto in fila transiti di esopianeti, NEO, variabili, campagne AAVSO, supernove | -- |

## Le decisioni

### Cosa e' (ADR 0013)

- **L'app non comanda l'hardware**: cupola, tetto, parcheggio e sicurezza restano al programma di
  ripresa; tutto passa dal file esportato.
- **Il piano interno non dipende dal programma**: N.I.N.A. e' la prima traduzione, le altre si
  aggiungono senza rifare il piano. **Un file per la notte intera**.
- **Un piano per postazione** (una montatura, un setup): due postazioni, due piani della stessa
  notte. La postazione **si sceglie in tendina** (Marco, v26.1), con sotto in piccolo «mono · ruota
  7 filtri» o «a colori · senza ruota» dal setup.
- In testa: «Stanotte» di partenza, pillole per le notti dopo; il sito attivo e il verdetto della
  notte in una riga, col rimando «Meteo ↗».

### Tre linguette per tecnica (Marco, 19/10/2026)

**«Deep sky» · «Sistema solare» · «Ricerca»**, una per notte e postazione: deep sky fa solo deep
sky, ricerca solo ricerca. Due postazioni possono fare due linguette diverse. Cambiare linguetta
con blocchi nel piano chiede «Il piano di stanotte si svuota: cambio?» · «Cambia» / «Annulla».

- **Deep sky**: progetti DSO dal Planner e **comete** (pose lunghe), per sigla («C/2026 A1»,
  «12P»), posizione da JPL Horizons ricalcolata per ogni blocco; senza rete «Serve la rete per la
  posizione della cometa.». Export per N.I.N.A.
- **Sistema solare**: Luna, pianeti, Sole, a video. Interruttore «Notte · Giorno»: Notte da
  tramonto ad alba, Giorno da alba a tramonto (Sole), con la striscia del Meteo di giorno e la riga
  fissa «Filtro solare sempre davanti all'ottica. Tetto e sicurezza li gestisce N.I.N.A.». Export
  per SharpCap Pro. <!-- software-ok -->
- **Ricerca**: un elenco solo, Criteri «Esopianeti · NEO · Variabili · Campagne AAVSO ·
  Supernove», accesi di partenza; i tipi sono Criteri, non pagine. Export per N.I.N.A.
- In tutte, sotto le proposte, **«Eventi di stanotte»** dal modo Eventi del Planner (ISS, eclissi,
  occultazioni lunari), ora fissa e lucchetto: «Dal modo Eventi del Planner: l'ora e' fissa.». Un
  oggetto o un evento si trascina sulla linea del tempo, o «Aggiungi».

### Le proposte

Gia' calcolate dal sito e dall'orizzonte importato, nell'ordine **si chiude stanotte -> ore di
posa -> ore mancanti** (`ereditato.md` F; Percent Complete di Target Scheduler).

- Deep sky: i progetti alti stanotte. Ogni proposta: nome («oggetto · ottica · camera»), **«4 h di
  posa»** e basta (Marco, 24/10/2026: niente ore visibili accanto; ore di posa di ADR 0034, per
  banda della Luna), il giudizio della Luna per banda, ore mancanti per filtro («Hα 1 h 50 · OIII
  4 h»). «Si chiude» = ultime settimane nei mesi buoni.
- Sistema solare: i progetti salvati alti stanotte (Luna, pianeti), il Sole di giorno.
- Ricerca: transiti visibili coi margini, minimi delle variabili, NEO osservabili, campagne AAVSO,
  supernove sopra la soglia.

### Il piano automatico (Marco, 19/10/2026)

**«Completa il piano»** tiene i blocchi messi a mano e riempie il resto; **«Rifai il piano»** da
capo; dopo ognuno «Annulla» torna a prima. Regole fisse, nessuna impostazione, nessuna priorita' a
mano, nessun punteggio. Una riga d'aiuto sotto i pulsanti.

**Deep sky e Ricerca** — «Prima le ore fisse, poi chi scende prima, vicino al suo transito.»
1. Prima gli eventi a ora fissa.
2. Fra chi passa altezza minima (30°, massa d'aria 2: Telescope Live, LCO) e massima, durata
   minima sopra soglia nel buio (Telescopius), crepuscolo e Luna: **chi scende prima** (Setting
   Soonest di Target Scheduler); a pari merito l'ordine delle proposte.
3. Ogni blocco si sposta il piu' vicino possibile al suo transito, se c'e' spazio.
4. Un blocco non scende sotto la durata minima (meno cambi: Target Switch Penalty).
5. Filtri **a blocchi**: tutte le pose di un filtro, poi il successivo; ogni filtro nelle ore in
   cui la sua regola della Luna passa: la banda larga senza Luna, la stretta con la Luna (Brecher,
   S&T nov. 2017). Nessun ordine per altezza.
6. Le ore «non adatte» del meteo si evitano finche' c'e' altro posto: non sono un conflitto
   (scelta nostra: Target Scheduler reagisce solo durante la notte).
7. Due eventi di ricerca sovrapposti: entra quello che ci sta tutto coi margini, a pari merito il
   piu' alto; l'altro resta fra le proposte con «Si sovrappone a {oggetto}: escluso.».

**Sistema solare** — «Ogni corpo nell'ora col seeing migliore sopra la soglia, vicino al transito.»
1. Fra le ore sopra l'altezza minima, la classe di seeing migliore (quelle di Meteo); a pari merito
   la piu' vicina al transito; senza previsione, al transito. Il seeing previsto non ha verifiche
   pubblicate: e' una preferenza, non un conflitto.
2. Giove: se la Macchia Rossa passa al meridiano centrale con Giove sopra soglia, il blocco si
   centra su di lei (±50 min, S&T).
3. Luna a mosaico: piu' alta possibile, pannelli dal terminatore (Omegon, Sky at Night).

**Il perche' dell'ora**, riga piccola sul blocco messo dal piano: «al transito 01:15» · «seeing
buono 02:00» (al passaggio: «previsione del seeing, non una misura») · «Macchia Rossa al meridiano
23:40» · «prima che scenda: sotto 30° alle 23:10» · «Hα con la Luna, RGB dopo le 01:30» · «Hα dal
crepuscolo nautico, 20:05». Spostato a mano, il blocco perde la riga.

Restano fuori, abitudini senza fonte: ordine dei filtri per altezza, ordine ovest-est; e dalla
documentazione di Target Scheduler: priorita' a mano, punteggi e pesi, grader, ripianificare dopo
ogni posa, Wait Plan, umidita'. Per dopo: cadenza dei filtri, bilanciamento dei pannelli, blocco a
cavallo del flip.

### La linea del tempo

Da tramonto ad alba (Giorno: da alba a tramonto), orizzontale sul desktop.

- **Fasce del cielo** come Meteo; **Luna**: curva sottile, fase in testa, tratteggiata dove conta
  (sopra l'orizzonte, ADR 0034); **Meteo**: striscia sottile del verdetto ora per ora, senza
  previsione «Previsione non disponibile»; nessun buio: «Nessun buio stanotte.».
- **Blocchi**, uno per oggetto: nome, filtri coi tempi («Hα 2 h · OIII 1 h»), curva d'altezza,
  «transita 01:15». Aperto, il **conto**: «Hα 12 × 300 s = 1 h · dither 4 × 34 s · filtro 8 s ·
  autofocus 1 × 3 min → 1 h 05».
- **Mosaico Deep sky**: tutti i pannelli ogni notte, dal piu' indietro, e il primo cambia ogni
  notte (Mosaic Completion di Target Scheduler): «pannelli 3 · 4 · 1 · 2».
- **Meridian flip**: un blocco puo' passare il meridiano e paga il flip (tacca «Flip»). Con la
  «pausa prima del meridiano» scritta in Impostazioni il piano evita la zona da transito - pausa a
  transito + minuti dopo il meridiano (formula di Target Scheduler): fascia grigia.
- **Avvio** (raffreddamento, unpark, e i passi accesi della postazione: «aspetta che sia sicuro ·
  apre il tetto · apre il coperchio»), **cambio** fra due oggetti (puntamento e centratura,
  autofocus), **chiusura** (park, chiude il tetto, riscaldamento), **flat** dopo la chiusura
  («Flat · Hα OIII · 25 + 25»; flat di cielo nella fascia del crepuscolo scelta), eventi fissi col
  lucchetto.
- Un pezzo senza tempo scritto non si disegna: «Scrivi i tempi in Impostazioni: {elenco dei
  mancanti}.».

### Sistema solare: progetto, blocco, export (Marco, 19/10/2026)

- **Progetto**, dal Planner («Salva come progetto»), senza ore da raggiungere: corpo; setup (ottica
  · camera, barlow o riduttore); per Luna e Sole mosaico «Intero» o «Zona», pannelli numerati,
  sovrapposizione (20%), ordine (Luna dal terminatore, Sole riga per riga); filtro dalla ruota o
  «Nessun filtro», Sole «Luce bianca · Hα»; ripresa per pannello (per filtro sui pianeti): posa in
  ms e frame, con durata e fps calcolati («2000 frame · 5 ms · circa 40 s»), «Regione» facoltativa.
- **Blocco**: «Luna · mosaico 12 pannelli · 18 min», pannelli come tacche; «Giove · R G B · 3 × 1
  min». Durata = pannelli × (ripresa + spostamento fra pannelli).
- **Puntare senza stelle**: l'app calcola distanza e angolo di ogni pannello dal centro del corpo;
  il programma li applica all'ora della ripresa, inseguendo il corpo. Sul disco niente plate
  solving: i buchi li copre la sovrapposizione. I frame si tengono fuori dalle cartelle
  dell'archivio.
- **Il video lo esegue SharpCap Pro, solo qui** (ADR 0029): N.I.N.A. con Lucky Imaging salva FITS <!-- software-ok -->
  e nessuna fonte conferma 30-40 fps. L'app scrive un `.scs` del Sequence Editor (corpo con
  spostamento, inseguimento, filtro, posa, frame), `SharpCap.exe /runsequence <file>` lo esegue <!-- software-ok -->
  all'avvio (docs.sharpcap.co.uk/4.1/15_AdvancedTopics.htm). Il formato si legge da un file vero <!-- software-ok -->
  al porting, **da provare su una postazione vera** prima di costruire l'export.
- «Esporta per SharpCap», «Un file di sequenza per SharpCap Pro: parte da solo all'avvio.». Avvisi: <!-- software-ok -->
  «Sul disco non c'e' plate solving: il puntamento e' quello della montatura. Se restano buchi fra
  i pannelli, alza la sovrapposizione.» · «Il video esce in SER: tienilo fuori dalle cartelle
  dell'archivio.». Non apre il tetto, non mette il filtro solare, non corregge la rotazione.
- Conflitto del Giorno: «Sole sotto 30° dalle 16:40.».

### Ricerca: i tipi e le fonti

Elenco unico, «Aggiungi oggetto» per nome, ognuno col suo segno:
- **Esopianeta** («WASP-12 b»): ora fissa; blocco da 1 h prima dell'ingresso a 1 h dopo l'uscita,
  base almeno 30 min (D. Conti, *A Guide to TTV Target Observing*, BAA 2022; Swarthmore Transit
  Finder): «transito 22:41-01:12 · base 1 h prima e dopo». Fonte NASA Exoplanet Archive.
- **Variabile** («Algol»): binaria a eclisse col minimo a ora fissa («minimo 23:58»), le altre
  blocchi brevi e flessibili. Da VizieR (B/vsx, J/AcA/54/207 Kreiner), non dall'API VSX non
  ufficiale.
- **NEO** («2026 TX»): flessibile, «posizione dal Minor Planet Center, serve la rete». NEOCP solo
  per uso personale, scaricato per l'utente, mai ripubblicato.
- **Campagna AAVSO**: Target Tool API con la chiave dell'utente; stella, filtro, cadenza («ogni 2
  min per 4 h» o «istantanea»), priorita', «ultima: 3 giorni fa», «Alert ↗».
- **Supernova**: Transient Name Server con la chiave bot dell'utente, piu' brillanti di mag 17 (la
  lista di Rochester); nome, magnitudine, galassia ospite, giorni dalla scoperta.
- Senza chiave: «Serve la chiave {AAVSO / TNS} in Impostazioni.». Vuoto: «Nessun oggetto di
  ricerca stanotte. Aggiungine uno per nome.».
- Fuori: occultazioni asteroidali (tempo GPS, nessuna API pubblica), scoperta e segnalazione,
  fotometria (AstroImageJ, software AAVSO), allarmi in tempo reale. I frame di ricerca si tengono
  fuori dalle cartelle: dentro li paga il solver e finiscono in Da confermare.

### Conflitti in rosso

Solo regole decise, sul blocco e nell'elenco sotto («{n} conflitti»):
- «Si sovrappone a {oggetto}.»;
- «Sotto 30° dalle 03:10.» / «Dietro l'orizzonte dalle 03:10.» / «Sopra 80° dalle 23:40.»;
- «Luna a 38°: in banda larga servono 45°.»;
- «Copre il transito della ISS delle 21:14.»;
- «Base prima del transito sotto 30 min.»;
- «Arrivi al transito con 5 min di margine.» (tempo libero prima di un evento fisso minore di
  puntamento + autofocus + cambio filtro);
- «Il flip cade nella pausa prima del meridiano.».
Il meteo non e' un conflitto.

### Totali ed export

«Buio 7 h 40 · pianificato 6 h 10 · avvio, cambi, chiusura e flat 1 h 05 · libero 25 min».
**«Esporta per N.I.N.A.»** (Deep sky, Ricerca), un file per il sequencer avanzato: il formato si
legge da un file vero esportato da N.I.N.A., nessuno schema pubblico. Spento col piano vuoto. Con
conflitti: «{n} conflitti: esporto lo stesso?» · «Esporta» / «Annulla»; poi «Esportato alle
18:42». Riga: «Un file per la notte intera, nel sequencer avanzato di N.I.N.A. La chiusura
d'emergenza col maltempo si imposta in N.I.N.A.».

### La Luna

- **Banda larga o stretta per la notte**: la regola della Luna di Meteo (`meteo.md`, ADR 0034): di
  fabbrica la convenzione ING, buona sotto 25%, incerta fino a 65%, contata dall'orizzonte;
  **modificabile in Impostazioni › Luna** e uguale in tutta l'app (Marco, 24/10/2026). Supera i
  gradini 25/50% e la Luna da -5° di ADR 0013. La pillola «banda stretta» e' gialla, non rossa:
  la Luna cambia cosa si riprende, non rovina la notte (Marco, 20/10/2026).
- **Luna per oggetto**: la lorentziana per filtro delle soglie del Planner
  ([`planner.md`](planner.md), *Le soglie dell'utente*); ogni filtro solo nelle ore in cui passa.

### Impostazioni › Planner e postazione

- **Soglie** del Planner ([`planner.md`](planner.md)), piu': «Pausa prima del meridiano» (minuti,
  vuota: «Solo se la usi nel programma di ripresa.»); «Altezza massima» vuota = spenta («Per
  montature altazimutali o setup che allo zenit toccano.»).
- **Tempi della notte**, uguali per tutta l'app, vuoti, fonte «nessuna convenzione: scegli tu»
  (nessuna fonte da' tempi standard; Target Scheduler non li stima). Il margine sta dentro il
  numero: «Scrivi tempi larghi: il margine sta dentro il numero.».
  - Avvio e chiusura (min): «Raffreddamento della camera» · «Unpark» · «Apertura del tetto» ·
    «Park» · «Chiusura del tetto» · «Riscaldamento della camera» (le due del tetto solo se una
    postazione ha il tetto);
  - Per oggetto (min): «Puntamento e centratura» · «Autofocus»;
  - Durante le pose: «Cambio filtro» (s) · «Dither col settle» (s) · «Dither ogni» (pose) ·
    «Scaricamento della posa» (s) · «Un autofocus ogni» (ore, stima) · «Meridian flip» (min) ·
    «Spostamento fra pannelli» (s) · «Flat e dark-flat per filtro» (min).
- **Automazione**, per postazione, Si'/No (passi di N.I.N.A.: Open/Close Dome Shutter, Park Dome,
  Wait Until Safe, Open/Close Flat Panel Cover):

| riga | Si' nel piano e nell'export |
|---|---|
| «Tetto o cupola motorizzati» | Avvio apre il tetto prima dell'unpark; Chiusura: park, poi chiude |
| «Sensore di sicurezza» | Avvio: «aspetta che sia sicuro» prima di aprire |
| «Pannello per i flat» | Avvio apre il coperchio; Chiusura lo chiude; flat a fine notte |
| «Flat di cielo» (solo senza pannello) | flat al crepuscolo, Sole fra -2° e -7° |

- **Flat** (con pannello o flat di cielo), solo i filtri usati, a fine notte dopo il park:
  «Flat per filtro» 25 di partenza, avviso sotto 20 «Sotto 20 flat la calibrazione aggiunge
  rumore.» (20: Sky at Night, forum; 30-50: High Point); «Dark-flat» Si' di partenza, stesso
  numero, non coi flat di cielo (N.I.N.A. non li fa in quel modo); «Quando»: «ogni notte»
  (partenza) · «ogni {n} giorni» · «a fine progetto» (Flats Handling di Target Scheduler);
  «Finestra dei flat di cielo» Sole da -2° a -7°, «nessuna convenzione: scegli tu», istruzione
  Sky Flat. I flat stanno solo qui: l'app non gestisce i file di calibrazione.
- **Ricerca**: «Supernove piu' brillanti di» mag 17. Le chiavi AAVSO e TNS stanno in Impostazioni ›
  Servizi, con Meteoblue ([`navigazione.md`](navigazione.md)).
- **Ruota portafiltri**: nessuna opzione, viene dal setup; con la ruota contano i cambi filtro.

### Stati

Senza sito: «Serve un sito: il piano dipende da dove sei.»; nessun progetto: «Nessun progetto
ancora.» · «Apri il Planner»; nessun progetto alto: «Nessun progetto alto piu' di {n} gradi
stanotte.»; nessun pianeta alto: «Nessun pianeta alto piu' di {n} gradi stanotte.»; piano vuoto:
«Trascina qui un progetto.»; valori fuori scala: «Un numero da {min} a {max}.», senza limiti «Un
numero.». Gli altri stati sono quelli della tavola v30.1.

### Telefono

L'**elenco** della v28.4 (Marco): niente linea verticale; proposte in un foglio dal basso, Criteri
in cima, i due pulsanti sotto; bersagli da 44 px.

### L'ordine di costruzione (ADR 0013)

Prima Deep sky (progetti, inquadratura, piano, export N.I.N.A.) e gli eventi del modo Eventi; poi
esopianeti, variabili e campagne AAVSO (coordinate fisse, conti in locale); poi supernove e
transienti; per ultimi comete e NEO, che chiedono la rete ogni notte.

## Cosa NON fa

Non comanda l'hardware. Non decide durante la notte (niente ripianificazione dopo ogni posa).
Non scarta pose ne' le vota. Non fa fotometria. Non mischia deep sky e ricerca nello stesso piano.
Non usa il «relax» della Luna vicino all'orizzonte di Target Scheduler: nessuna fonte.
