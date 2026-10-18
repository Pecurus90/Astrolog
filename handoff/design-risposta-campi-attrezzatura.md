# Per Claude Design -- i campi dell'attrezzatura: la lista nuova

Da Claude Code, 18/10/2026. Marco ha deciso di allargare i campi: ogni pezzo porta la scheda
tecnica del produttore, tutta modificabile, e il corredo ci calcola sopra. La decisione e' in
`docs/adr/0021-dati-completi-dell-attrezzatura.md`. Oggi l'app ha solo i campi del vostro v15:
quelli nuovi arrivano col porting.

Le etichette dei campi nuovi sono **proposte**: Marco le approva sulla vostra tavola. Quelle che
esistono gia' restano parola per parola (Nome, Marca, Modello, Peso (kg), Note, Apertura (mm),
Focale nativa (mm), Tipo di sensore, Pixel (µm), Carico utile (kg), Fattore, Numero di
posizioni, Larghezza (nm), Focale effettiva (mm)).

## 1. I campi, tipo per tipo

Comuni a tutti gli strumenti: Nome (obbligatorio), Marca, Modello, Peso (kg), Note. Tutti gli altri
campi sono facoltativi. Accanto al campo: **dai file**, **calcolato** o **inserito**, come nel v15.

- **ottica**: Apertura (mm), Focale nativa (mm), Cerchio d'immagine (mm), Backfocus richiesto (mm).
  Calcolato: potere risolutore (").
- **camera**:
  - Sensore (il nome, es. IMX571)
  - Risoluzione (px), larghezza × altezza: dai file
  - Pixel (µm): dai file
  - Dimensione del sensore (mm): calcolata
  - Tipo di sensore (mono / a colori): dai file
  - Bit dell'ADC
  - Raffreddata (sì / no) e, se sì, Raffreddamento (°C sotto l'ambiente)
  - Spessore fino al sensore (mm)
- **camera di guida**: come la camera, senza raffreddamento. Dai file arriva solo il nome.
- **ottica di guida**: Apertura (mm), Focale (mm).
- **guida fuori asse (OAG)**, tipo nuovo: Spessore (mm), Prisma (mm). Niente focale: guida con
  quella del corredo.
- **montatura**: Carico con contrappeso (kg), Carico senza contrappeso (kg). Il Peso e' quello
  della testa.
- **riduttore** (anche barlow: fattore sopra 1): Fattore, Backfocus richiesto (mm), Cerchio
  d'immagine (mm).
- **ruota portafiltri**: Numero di posizioni, Misura dei filtri (1,25″ / 31 mm / 36 mm / 2″ /
  50 mm quadrato), Spessore (mm).
- **focheggiatore**: Passo (µm), Passi totali.
- **distanziale**, tipo nuovo: Spessore (mm).
- **Filtro**: Nome e almeno una banda (obbligatori), Marca, Modello, le bande con Larghezza (nm),
  Misura (come la ruota), Spessore (mm), Montato (sì / no), Per ottiche veloci (sì / no).
- **Corredo**: Ottica, Camera, Focale effettiva (mm), obbligatori come oggi.

Il programma di ripresa resta una parte del corredo che arriva solo dai file: nessun modulo.

## 2. Il corredo: parti e conti

Parti nuove, scelte come le altre: la **guida** (ottica di guida **oppure** OAG, più la camera di
guida) e i **distanziali** (anche più d'uno).

Una sezione di conti nella scheda del corredo. Ogni conto compare solo coi suoi dati; se ne manca
uno, la riga dice quale (es. "manca il pixel della camera di guida"):

- Rapporto focale (calcolato)
- Scala prevista ("/px), accanto a quella misurata sul cielo
- Campo previsto (° × °), accanto a quello misurato
- Copertura: diagonale del sensore contro cerchio d'immagine (ci sta / non ci sta)
- Scala di guida ("/px), con **avviso fuori da 0,5-4 "/px**
- Rapporto guida/ripresa (es. "3,2×"), **senza giudizio**
- Campionamento: "ottimo con seeing fra {a} e {b}""
- Backfocus del treno: somma degli spessori contro il richiesto, con la differenza in mm (senza
  giudizio)
- Carico: "{p} % del carico della montatura", **avviso solo sopra il 100 %**

### Le regole, per i numeri d'esempio e per `soglie.js`

- Rapporto focale = focale effettiva / apertura.
- Scala prevista = 206,265 × pixel (µm) / focale effettiva (mm).
- Dimensione del sensore (mm) = pixel × risoluzione / 1000.
- Campo previsto, per lato = 2·atan(lato del sensore / (2 × focale effettiva)).
- Copertura: diagonale del sensore ≤ cerchio d'immagine del riduttore, o dell'ottica senza
  riduttore.
- Scala di guida = 206,265 × pixel di guida / focale di guida. Con l'OAG la focale di guida è la
  focale effettiva del corredo. Avviso fuori da 0,5-4 "/px (Bruce Waddington, PHD2).
- Rapporto guida/ripresa = scala di guida / scala prevista.
- Campionamento sul corredo: "ottimo con seeing fra {2 × scala} e {3 × scala}"" (Nyquist,
  Astronomy Tools).
- Backfocus = spessore di OAG + ruota + distanziali + camera, contro il richiesto del riduttore (o
  dell'ottica senza riduttore). Differenza in mm.
- Carico = somma dei pesi di ottica, camera, riduttore, ruota, focheggiatore, guida, camera di
  guida, distanziali / carico più alto della montatura × 100.
- Potere risolutore dell'ottica = 116 / apertura (mm) (Dawes, Astronomy Tools).

### Esempio: "Notte in quota" (Askar FRA400 + ZWO ASI2600MM Pro)

Askar FRA400 72 mm, 400 mm. ASI2600MM Pro: 3,76 µm, 6248 × 4176 px. Guida: tubo da 120 mm,
camera di guida 3,75 µm.

- rapporto focale f/5,6
- scala 1,94 "/px
- sensore 23,5 × 15,7 mm
- campo 3,36° × 2,25°
- potere risolutore 1,61"
- campionamento: ottimo con seeing fra 3,9 e 5,8"
- scala di guida 6,45 "/px, fuori da 0,5-4: **avviso**
- rapporto guida/ripresa 3,3×
- con OAG al posto del tubo: scala di guida 1,93 "/px, rapporto 1,0×, niente avviso

## 3. In Meteo

Nella notte, per ogni corredo, il campionamento col seeing previsto:
- **sottocampionato** se la scala supera metà del seeing;
- **sovracampionato** se la scala è sotto un terzo del seeing;
- **ottimo** in mezzo.

Esempio: "Notte in quota" (1,94 "/px) con seeing previsto 2,5" dà sottocampionato; con seeing
4,5" dà ottimo.

Il seeing è quello che Meteo mostra già per la notte: la media delle ore che hanno un numero. Senza chiave
Meteoblue il seeing non c'è e la riga non compare.

## 4. Dai file

Solo: i nomi dei pezzi, il pixel, il tipo di sensore, la risoluzione della camera e la focale
effettiva del corredo. Tutto il resto si scrive a mano. Il valore scritto vince su quello dei file.

## 5. Le tendine

- Liste fisse dell'app: i tipi, le bande, il tipo di sensore, le misure dei filtri.
- Marche: testo libero. "altra…" / "Nuova marca" propone quelle già scritte dall'utente.
- Parti del corredo: i pezzi dell'utente di quel tipo.

## 6. Cosa vi chiedo

1. Il modulo con i blocchi per tipo e "{n} di {m} scritti", anche coi campi in più.
2. La sezione dei conti del corredo, con i tre stati: valore, avviso, "manca …".
3. La riga del campionamento in Meteo.

CHANGELOG e DECISIONI come al solito.
