# Per Claude Design -- Piano della notte, brief completa (v30)

Da Claude Code, 20/10/2026 (prima stesura 19/10). **La v29/v29.1 ha fatto il Meteo ma non questa
brief: il Piano e' fermo alla v28.4.** Va eseguita tutta, sez. 0-13, piu' la sez. 0bis
(correzioni alla v29.1 e risposte alle vostre domande). **Questa brief sostituisce tutte le precedenti sul Piano della
notte** (`design-piano-della-notte.md`, `-v26.md`, `-v27.md`) e risponde alle vostre due domande
(«Luna e Sole a pannelli nel piano», «come sceglie il piano automatico»). E' la pagina intera,
piu' le regole che toccano tutta l'app. Decisioni in
`docs/adr/0013-progetti-e-piano-della-notte.md` (tutte le sezioni "Il disegno" e seguenti),
`docs/adr/0023-planner-e-progetti.md` (tabella delle soglie) e `docs/domini/meteo.md`. Le
parole fra «» sono proposte: Marco le approva sulla tavola. I numeri li manda l'app.

Il Planner crea i progetti; il Piano della notte decide **cosa si fa una notte** (o un giorno,
per il Sole), in che ordine, e lo esporta in un file per il programma che riprende.

## 0bis. Meteo v29.1: risposte e correzioni

**La qualita' della notte da 0 a 100 e' giusta e resta** (Marco, 20/10/2026; ADR 0020). Pesi
35/30/12/9/9/5, pioggia e nuvole dal 50% bloccano, verdetto da 70 e 40, ore utili da 60, Luna
fuori dal punteggio e sopra -5°. Il nostro `docs/domini/meteo.md` ora dice lo stesso: il vecchio
"semaforo dalle sole nuvole" e' superato ovunque.

Risposte a `docs/per-claude-code-meteo-verdetto.md`:
1. **Pesi della v13: si tengono.** Sono quelli dell'ADR 0020.
2. **«Cosa limita» anche in Dashboard** (Marco): accanto alla qualita' di stanotte, la stessa
   riga del racconto («limita il seeing · qualita' fino a 62»; «nessun limite» da 85).

Approvati da Marco: i testi del racconto («Diventa buona · qualita' da 85, il primo limite e' il
seeing», «nessun limite», «limita … · qualita' fino a N») e la pillola **«banda stretta» in
giallo**, non rosso: la Luna cambia cosa si riprende, non rovina la notte.

Da correggere:
1. **Ore serene -> ore utili** dove resta la parola vecchia: stato senza buio di `Meteo.dc.html`
   («Ore serene», «ore serene col Sole…») e stato 15 di `Meteo stati.dc.html`. Le ore utili sono
   quelle di buio con qualita' da 60.
2. **`Meteo stati.dc.html` e' rotto**: contiene il documento due volte (il primo chiude con
   `</html` senza `>` e subito riparte `<html>`). Uno solo.
3. **Nuvole al 25% esatto**: in `soglie.js` il giudizio delle nuvole e' `x < 25 ? 0`, quindi
   un'ora al 25% risulta incerta. 25% = 2 okta = buona: `x <= 25`. Il punteggio gia' lo tratta
   giusto; la parola deve dire lo stesso.
4. **Impostazioni**: `planner.lun: 40°` va tolto, al suo posto le tre righe della Luna per filtro
   (sez. 9); e tutto il resto della sez. 10.

## 0. Cosa cambia rispetto alla v26.1 consegnata

- Tre **linguette per tecnica** al posto di «Fotografia» · «Ricerca» (sez. 2).
- Il **Sistema solare** si salva in Progetti ed esce con un file per SharpCap Pro (sez. 5). <!-- software-ok -->
- Il **piano automatico** ha regole scritte e mostra il perche' di ogni ora (sez. 3).
- La **Luna per bersaglio** con la formula di Target Scheduler, tre righe al posto di «40°»
  (sez. 9); la Luna smette di contare sotto **-5°** in tutta l'app.
- **Automazione della postazione** Si'/No, **ruota** dal setup, **tempi** in tre gruppi, **flat**
  (sez. 7 e 10).
- Ricerca con **campagne AAVSO** e **supernove** (sez. 6).
- Correzioni della v25 che restano valide: «Dietro l'orizzonte» usa l'orizzonte importato; testi
  scritti da voi come proposte; la riga degli eventi «Dal modo Eventi del Planner: l'ora e'
  fissa.».

Resta della v25/v26: griglia, blocchi trascinabili, bordi, tastiera, linea «adesso», conferma
dell'export, telefono verticale.

## 1. In testa

- Nome in barra: **«Piano della notte»** (`/piano-della-notte`), voce nel menu Altro.
- La notte: «Stanotte» di partenza, pillole per le notti dopo.
- La postazione: linguette, una per montatura (montatura · ottica · camera), e sotto in piccolo
  «mono · ruota 7 filtri» o «a colori · senza ruota» (dal setup in Attrezzatura). Un piano per
  postazione.
- Le **tre linguette** della sez. 2.
- Sito attivo e verdetto della notte in una riga, col rimando «Meteo ↗».

## 2. Tre linguette per tecnica

**«Deep sky» · «Sistema solare» · «Ricerca»**. Una postazione fa una linguetta per notte; due
postazioni possono farne due diverse. Cambiare linguetta con blocchi nel piano chiede: «Il piano
di stanotte si svuota: cambio?» · «Cambia» / «Annulla».

- **Deep sky**: progetti DSO dal Planner e **comete** (pose lunghe). Le comete per sigla («C/2026
  A1», «12P»), posizione da JPL Horizons ricalcolata per ogni blocco; senza rete «Serve la rete
  per la posizione della cometa.». Export per N.I.N.A.
- **Sistema solare**: **Luna, pianeti, Sole**, a video. Interruttore **«Notte · Giorno»**: Notte
  da tramonto ad alba (Luna, pianeti); Giorno da alba a tramonto (Sole), con la striscia del
  Meteo di giorno e in testa la riga fissa «Filtro solare sempre davanti all'ottica. Tetto e
  sicurezza li gestisce N.I.N.A.». Export per SharpCap. <!-- software-ok -->
- **Ricerca**: un elenco solo, Criteri a chip **«Esopianeti · NEO · Variabili · Campagne AAVSO ·
  Supernove»** (accesi di partenza). Export per N.I.N.A.

Sotto le proposte, in tutte: **«Eventi di stanotte»** (transiti della ISS, eclissi, occultazioni
lunari dal modo Eventi del Planner), ora fissa e lucchetto. Un oggetto o un evento si trascina
sulla linea del tempo, o «Aggiungi».

## 3. Proposte e piano automatico

**Proposte gia' calcolate** dal sito e dall'orizzonte importato:
- Deep sky: i progetti alti stanotte, ordinati: prima chi si chiude (ultime settimane nei mesi
  buoni), poi le ore utili, poi le ore mancanti. Ogni proposta: nome (oggetto · ottica · camera),
  «5 h visibili · 4 h utili», giudizio della Luna per banda (sez. 9), ore mancanti per filtro
  («Hα 1 h 50 · OIII 4 h»).
- Sistema solare: i progetti salvati alti stanotte (Luna, pianeti), il Sole di giorno.
- Ricerca: transiti visibili coi margini, minimi delle variabili, NEO osservabili, campagne
  AAVSO osservabili, supernove sopra la soglia.

Sopra la linea del tempo due pulsanti: **«Completa il piano»** (tiene i blocchi messi a mano e
riempie il resto) e **«Rifai il piano»** (da capo). Dopo ognuno, «Annulla» torna al piano di
prima. Non «sequenza»: e' la parola di N.I.N.A., vietata per questa pagina.

Regole fisse, nessuna impostazione, nessuna priorita' a mano, nessun punteggio. Una riga d'aiuto
sotto i pulsanti.

**Deep sky e Ricerca** — «Prima le ore fisse, poi chi scende prima, vicino al suo transito.»
1. Prima gli eventi a ora fissa.
2. Poi, fra chi passa altezza minima e massima, durata minima, crepuscolo e Luna, **chi scende
   prima**; a pari merito l'ordine delle proposte.
3. Ogni blocco si sposta il piu' vicino possibile al suo transito, se c'e' spazio.
4. Un blocco non e' mai piu' corto della durata minima (1 h).
5. Dentro il blocco i filtri vanno **a blocchi** (tutte le pose di un filtro, poi il successivo);
   l'ordine lo da' la Luna: ogni filtro nelle ore in cui la sua regola passa.
6. Le ore «non adatte» del meteo si evitano finche' c'e' altro posto; non sono un conflitto.
7. Due eventi di ricerca sovrapposti: entra quello che ci sta tutto coi margini, a pari merito
   il piu' alto; l'altro resta fra le proposte con «Si sovrappone a {oggetto}: escluso.».

**Sistema solare** — «Ogni corpo nell'ora col seeing migliore sopra la soglia, vicino al
transito.»
1. Fra le ore sopra l'altezza minima, quelle con la classe di seeing migliore (le classi di
   Meteo); a pari merito la piu' vicina al transito. Senza previsione del seeing: al transito.
2. **Giove**: se la Macchia Rossa passa al meridiano centrale con Giove sopra la soglia, il blocco
   si centra su di lei.
3. **Luna a mosaico**: piu' alta possibile; i pannelli partono dal terminatore.

**Il perche' dell'ora**, riga piccola sul blocco messo dal piano: «al transito 01:15» · «seeing
buono 02:00» (al mouse: «previsione del seeing, non una misura») · «Macchia Rossa al meridiano
23:40» · «prima che scenda: sotto 30° alle 23:10» · «Hα con la Luna, RGB dopo le 01:30» · «Hα dal
crepuscolo nautico, 20:05». Un blocco spostato a mano perde la riga.

## 4. La linea del tempo

Da tramonto ad alba (Giorno: da alba a tramonto), orizzontale sul desktop.

- **Fasce del cielo**: giorno, crepuscoli civile, nautico, astronomico, buio (come Meteo).
- **Luna**: curva d'altezza sottile, fase in testa; tratteggiata dove conta (sopra -5°).
- **Meteo**: striscia sottile del verdetto ora per ora; senza previsione «Previsione non
  disponibile».
- **Blocchi**, uno per bersaglio: nome, filtri in fila coi loro tempi («Hα 2 h · OIII 1 h»),
  curva d'altezza, segno del transito («transita 01:15»). Aperto, il **conto**: «Hα 12 × 300 s =
  1 h · dither 4 × 34 s · filtro 8 s · autofocus 1 × 3 min → 1 h 05».
- **Mosaico deep sky**: il blocco elenca i pannelli nell'ordine di stanotte («pannelli 3 · 4 · 1
  · 2»): tutti ogni notte, dal piu' indietro, e il primo cambia ogni notte.
- **Meridian flip**: un blocco puo' passare il meridiano; sopra, una tacca «Flip» della sua
  durata. Con la «pausa prima del meridiano» scritta in Impostazioni, una fascia grigia attorno
  al transito dove nessun blocco cade.
- **Avvio**: raffreddamento, unpark, e i passi accesi della postazione («aspetta che sia sicuro ·
  apre il tetto · apre il coperchio»).
- **Cambio** fra due bersagli: puntamento e centratura, autofocus.
- **Chiusura**: park, chiude il tetto, riscaldamento.
- **Flat** (sez. 10): dopo la chiusura, «Flat · Hα OIII · 25 + 25»; flat di cielo nella fascia
  del crepuscolo scelta.
- **Eventi fissi** col lucchetto.
- Un pezzo senza tempo scritto non si disegna; riga: «Scrivi i tempi in Impostazioni: {elenco dei
  mancanti}.».

## 5. Sistema solare: progetto, blocco, export

**Progetto**, dal Planner («Salva come progetto»); in Progetti, al posto della barra, «ultima
volta nel piano: {data}». Campi: corpo; setup (ottica · camera, barlow o riduttore); per Luna e
Sole **mosaico** «Intero» o «Zona» (sulla carta), pannelli numerati, sovrapposizione % (20%),
ordine (Luna: dal terminatore; Sole: riga per riga); filtro dalla ruota o «Nessun filtro», Sole
«Luce bianca · Hα»; ripresa per pannello (per filtro sui pianeti): «posa» in ms e «frame», con
durata e fps calcolati («2000 frame · 5 ms · circa 40 s»), «Regione» (ROI) facoltativa.

**Blocco**: «Luna · mosaico 12 pannelli · 18 min», pannelli come tacche; «Giove · R G B · 3 × 1
min». Si apre con la carta piccola del mosaico. Durata = pannelli × (ripresa + spostamento).

**Puntare senza stelle**: l'app calcola distanza e angolo di ogni pannello dal centro del corpo;
SharpCap li applica all'ora della ripresa, inseguendo alla velocita' del corpo. <!-- software-ok -->

**Export**: **«Esporta per SharpCap»**, riga: «Un file di sequenza per SharpCap Pro: parte da solo <!-- software-ok -->
all'avvio.». Avvisi: «Sul disco non c'e' plate solving: il puntamento e' quello della montatura.
Se restano buchi fra i pannelli, alza la sovrapposizione.» · «Il video esce in SER: tienilo fuori
dalle cartelle dell'archivio.». Non apre il tetto, non mette il filtro solare, non corregge la
rotazione della camera (entro 10°).

Conflitto del Giorno: «Sole sotto 30° dalle 16:40.».

## 6. Ricerca: i tipi

Elenco unico, «Aggiungi oggetto» per nome, ognuno col suo segno:
- **Esopianeta** («WASP-12 b»): ora fissa; blocco in tre parti (base prima, transito, base dopo):
  «transito 22:41-01:12 · base 1 h prima e dopo».
- **Variabile** («Algol»): binaria a eclisse col minimo a ora fissa («minimo 23:58»); le altre
  blocchi brevi e flessibili.
- **NEO** («2026 TX»): flessibile, «posizione dal Minor Planet Center, serve la rete».
- **Campagna AAVSO** (nuova): dal Target Tool, con la chiave AAVSO dell'utente. Riga: stella,
  filtro richiesto, cadenza («ogni 2 min per 4 h» o «istantanea»), priorita', ultima misura
  («ultima: 3 giorni fa»), «Alert ↗». Blocco a serie temporale o istantanea.
- **Supernova** (nuova): dal Transient Name Server, con la chiave dell'utente; solo quelle piu'
  brillanti della soglia (mag 17 di partenza). Riga: nome, magnitudine, galassia ospite, giorni
  dalla scoperta. Blocco flessibile.
Senza chiave: la riga del tipo dice «Serve la chiave {AAVSO / TNS} in Impostazioni.».

Stato vuoto: «Nessun oggetto di ricerca stanotte. Aggiungine uno per nome.».

## 7. Conflitti in rosso

Sul blocco e nell'elenco sotto («{n} conflitti»):
- «Si sovrappone a {bersaglio}.»;
- «Sotto 30° dalle 03:10.» / «Dietro l'orizzonte dalle 03:10.» (orizzonte importato) / «Sopra
  80° dalle 23:40.» (altezza massima);
- «Luna a 38°: in banda larga servono 45°.»;
- «Copre il transito della ISS delle 21:14.»;
- «Base prima del transito sotto 30 min.»;
- «Arrivi al transito con 5 min di margine.» (tempo libero prima di un evento fisso minore di
  puntamento + autofocus + cambio filtro);
- «Il flip cade nella pausa prima del meridiano.».
Il meteo non e' un conflitto.

## 8. Totali ed export

Totali: «Buio 7 h 40 · pianificato 6 h 10 · avvio, cambi, chiusura e flat 1 h 05 · libero 25
min».

**«Esporta per N.I.N.A.»** (Deep sky, Ricerca) o **«Esporta per SharpCap»** (Sistema solare): un <!-- software-ok -->
file per la notte intera. Spento col piano vuoto. Con conflitti: «{n} conflitti: esporto lo
stesso?» · «Esporta» / «Annulla»; poi «Esportato alle 18:42». Riga N.I.N.A.: «Un file per la
notte intera, nel sequencer avanzato di N.I.N.A. La chiusura d'emergenza col maltempo si imposta
in N.I.N.A.».

## 9. La Luna

**Sezione «Luna» delle Impostazioni (tutta l'app)**, tre righe:
| riga | partenza | fonte |
|---|---|---|
| «Banda larga buona fino a» | 25% | «regola diffusa fra chi riprende» |
| «Banda larga al limite fino a» | 50% | «nessuna convenzione: scegli tu» |
| «La Luna conta sopra» | -5° | «8 milioni di misure della rete TESS» |
Riga d'aiuto: «Sotto un cielo buio la Luna disturba prima: abbassa le percentuali.». La seconda
percentuale non sta sotto la prima («Deve essere almeno {prima}%.»). Queste righe danno il
verdetto della notte in **Meteo** e **Dashboard** (riga della Luna, «banda larga al limite»,
«consigliata banda stretta», carta della Luna, ore utili).

**Luna per bersaglio (Impostazioni › Planner)**, al posto di «Distanza dalla Luna 40°». La
distanza richiesta dipende dalla fase: piena a Luna piena, la meta' dopo N giorni (formula di
Target Scheduler, ACP, Voyager):
| riga | partenza | fonte |
|---|---|---|
| «Luna, banda larga (L, RGB, colore)» | «120° a Luna piena · meta' a 10 giorni» | «ACP e Telescopius; giorni scelti da Marco» |
| «Luna, OIII» | «90° a Luna piena · meta' a 10 giorni» | «Telescopius; giorni scelti da Marco» |
| «Luna, Hα, SII, dual band» | «60° a Luna piena · meta' a 7 giorni» | «Target Scheduler» |
Accanto, una curva piccola con le tre linee lungo il mese lunare e il segno di stanotte
(«stanotte servono 45° · 32° · 18°»). Riga: «Piu' la Luna e' piena, piu' il bersaglio deve stare
lontano. Sotto -5° la Luna non conta.».

**Dove si vede**: Planner e proposte, pillola «Luna a 74° · servono 45°» per la banda del filtro
(due bande: «larga no · Hα si'»); Piano, ogni filtro solo nelle ore in cui passa; conflitto della
sez. 7.

Nei Tweaks: Luna al primo quarto e piena; un'impostazione diversa della sezione «Luna» (10%, 25%,
sopra 10°) e Meteo, Dashboard, Planner, Piano che cambiano.

## 10. Impostazioni › Planner e postazione

**Soglie** (gia' in v24, invariate salvo dove detto): altezza minima deep sky 30°, durata minima
1 h, mese buono, altezza minima pianeti/Luna/Sole 30°, ADC sotto 35°, Macchia Rossa. Nuove:
- le tre righe della Luna per bersaglio (sez. 9);
- **«Crepuscolo ammesso»**: banda larga «buio astronomico» (fisso); banda stretta «buio
  astronomico» (partenza) o «crepuscolo nautico»;
- **«Altezza massima»**: vuota = spenta («Per montature altazimutali o setup che allo zenit
  toccano.»);
- **«Pausa prima del meridiano»**, minuti, vuota («Solo se in N.I.N.A. la usi.»).

**Tempi della notte**, uguali per tutta l'app, vuoti, fonte «nessuna convenzione: scegli tu»:
- Avvio e chiusura (min): «Raffreddamento della camera» · «Unpark» · «Apertura del tetto» ·
  «Park» · «Chiusura del tetto» · «Riscaldamento della camera» (le due del tetto solo se una
  postazione ha il tetto);
- Per bersaglio (min): «Puntamento e centratura» · «Autofocus»;
- Durante le pose: «Cambio filtro» (s) · «Dither col settle» (s) · «Dither ogni» (pose) ·
  «Scaricamento della posa» (s) · «Un autofocus ogni» (ore, stima) · «Meridian flip» (min) ·
  «Spostamento fra pannelli» (s) · «Flat e dark-flat per filtro» (min).
Riga: «Scrivi tempi larghi: il margine sta dentro il numero.». Nei Tweaks d'esempio (misurati su
un setup vero, mai di partenza): 10, 0.1, 1, 0.5, 1, 10 · 2, 3 · 8, 34, 3, 0.5, 2, 3, 5, 2.

**Automazione**, per postazione, Si'/No:
| riga | Si' nel piano e nell'export |
|---|---|
| «Tetto o cupola motorizzati» | Avvio apre il tetto prima dell'unpark; Chiusura: park, poi chiude |
| «Sensore di sicurezza» | Avvio: «aspetta che sia sicuro» prima di aprire |
| «Pannello per i flat» | Avvio apre il coperchio; Chiusura lo chiude; flat a fine notte |
| «Flat di cielo» (solo senza pannello) | flat al crepuscolo, Sole fra -2° e -7° |

**Flat** (si vede con pannello o flat di cielo):
- «Flat per filtro»: 25 (avviso sotto 20: «Sotto 20 il master flat e' rumoroso.»);
- «Dark-flat»: Si' di partenza, stesso numero (non con i flat di cielo);
- «Quando»: «ogni notte» (partenza) · «ogni {n} giorni» · «a fine progetto»; sempre solo i filtri
  usati;
- «Finestra dei flat di cielo»: Sole da -2° a -7°, fonte «nessuna convenzione: scelta di Marco».

**Ricerca**: «Chiave AAVSO», «Chiave TNS», «Supernove piu' brillanti di» (mag 17, fonte «la lista
di Rochester»).

**Ruota portafiltri**: nessuna opzione; viene dal setup.

## 11. Stati (Tweaks)

- senza sito: «Serve un sito: il piano dipende da dove sei.»;
- nessun progetto: «Nessun progetto ancora.» · «Apri il Planner»;
- nessun progetto alto: «Nessun progetto sopra 30° stanotte.»;
- Ricerca vuota coi Criteri scelti; chiave mancante per AAVSO o TNS;
- notte senza buio: «Nessun buio» e le fasce che ci sono;
- piano vuoto: «Trascina qui un progetto.»;
- tempi non scritti;
- piano con conflitti; piano esportato;
- Deep sky dopo «Completa il piano»: un oggetto che scende, uno che sale, un blocco Hα con la
  Luna poi RGB, un mosaico coi pannelli a rotazione, un blocco che passa il meridiano;
- Sistema solare Notte: Giove sulla Macchia Rossa, Saturno sul seeing, Luna a mosaico; Giorno:
  Sole luce bianca e Hα; senza chiave Meteoblue, tutti «al transito»;
- Ricerca: esopianeta a inizio sera, NEO a mezzanotte e mezza, campagna AAVSO a serie, supernova;
- postazione col tetto, sensore e pannello (Avvio, Chiusura, Flat completi) e una senza (flat di
  cielo); setup mono con ruota e a colori senza;
- banda stretta col crepuscolo nautico; altezza massima col conflitto; pausa prima del meridiano
  con la fascia grigia.

## 12. Telefono

Linea del tempo verticale (le ore scendono). In testa linguette e interruttore Notte · Giorno;
proposte in un foglio dal basso, Criteri in cima; i due pulsanti sotto la linea. Avvio, cambi,
chiusura e flat come fasce. Blocchi da toccare (il mosaico si apre con la carta dei pannelli);
bersagli da 44 px.

## 13. Foglio di stile

In `old/astrolog.css` (il foglio che il codice copia, oggi v38) i numeri dei commenti col punto:
- r.493 `--campo-coordinata`: «46,4843 N» -> «46.4843 N»;
- r.1578 blocco BORTLE: «Bortle 4 (20,8)» -> «Bortle 4 (20.8)»;
- r.1580 stessa nota: «21,76 · 21,60 · 21,30 · 20,80 · 19,25 · 18,50 …» -> col punto.

Nel Piano: «Completa la sequenza» e «Rifai la sequenza» (5 volte) diventano **«Completa il
piano»** e **«Rifai il piano»** (sez. 3).

## Fuori

- Occultazioni asteroidali (tempo GPS, video, nessuna API pubblica).
- Scoperta e segnalazione di supernove; fotometria e invio dati AAVSO (si fanno con altri
  strumenti).
- Attenuazione della Luna vicino all'orizzonte (il «relax» di Target Scheduler): basta -5°.
- Priorita' a mano, punteggi dei bersagli, scarto automatico delle pose. (La qualita' della notte
  0-100 del Meteo resta: e' un'altra cosa, sez. 0bis.)
- Ordine dei filtri per altezza.
- Nessun comando diretto all'hardware: tutto passa dal file esportato.

CHANGELOG e DECISIONI come al solito.
