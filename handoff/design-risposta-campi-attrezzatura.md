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

## 3. In Meteo

Nella notte, per ogni corredo, il campionamento col seeing previsto: ottimo, sottocampionato o
sovracampionato. Senza chiave Meteoblue il seeing non c'è e la riga non compare.

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
