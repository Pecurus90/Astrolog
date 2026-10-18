# Per Claude Design -- i campi dell'attrezzatura: le risposte dall'app

Da Claude Code, 18/10/2026. Controllato sull'app vera: lo schema (`instruments`, `filters`,
`filter_bands`, `rigs`), i campi che l'API accetta per tipo (`cards` in `GET /api/v1/gear`) e
gli header che la scansione legge.

**In breve: al modulo v15 non manca niente.** I campi che avete sono esattamente quelli che l'app
chiede, tipo per tipo. La regola dell'app: un campo si chiede solo se l'app ci fa qualcosa
(rapporto focale, scala, carico). Dimensioni e risoluzione del sensore, raffreddamento, diametro
e focale della guida, tipo di montatura, misura dei filtri non esistono: non disegnateli.

## 1. I campi, tipo per tipo

Comuni a tutti gli strumenti: Nome, Marca, Modello, Peso (kg), Note.

| tipo | campi propri |
|---|---|
| ottica | Apertura (mm), Focale nativa (mm) |
| camera | Tipo di sensore (mono / a colori), Pixel (µm) |
| montatura | Carico utile (kg) |
| riduttore | Fattore |
| ruota portafiltri | Numero di posizioni |
| ottica di guida, camera di guida, focheggiatore | nessuno |

- **Filtro**: Nome, Marca, Modello, le bande (una o piu', fra L, R, G, B, HA, HB, OIII, SII),
  ognuna con Larghezza (nm) facoltativa. Niente Note e niente Peso: il filtro non li ha.
- **Corredo**: Ottica, Camera, Focale effettiva (mm). Il nome si da' dopo, con Rinomina.
- **In modifica**: "Unisci a", per strumenti e filtri.
- **Programma di ripresa**: non e' un tipo e non si scrive. E' una parte del corredo che arriva
  solo dai file. Nel modulo non c'e'.

**Backfocus: togliete la riga dalla scheda del riduttore.** Il campo esiste nel database, ma
nessun modulo lo chiede e nessun header lo porta: la riga non comparirebbe mai.

## 2. Obbligatori

- Strumento: solo il Nome (il Tipo ha sempre un valore).
- Filtro: Nome e almeno una banda.
- Corredo: Ottica, Camera e Focale effettiva.
- Ogni misura, se scritta, e' maggiore di zero.

## 3. Dai file, calcolati, scritti a mano

**Dai file** ("dai file" accanto al campo):

- Camera, Tipo di sensore: dall'header `BAYERPAT`. C'e' vuol dire a colori; vince la maggioranza
  dei frame.
- Camera, Pixel: dall'header `XPIXSZ`, il valore piu' frequente.
- Corredo, Focale effettiva: dall'header `FOCALLEN`.
- Solo il nome del pezzo, senza nessun dato tecnico:
  - ottica da `TELESCOP`;
  - camera da `INSTRUME`;
  - ruota da `FWHEEL`;
  - focheggiatore da `FOCNAME`;
  - camera di guida da `GUIDECAM`;
  - filtro da `FILTER`;
  - programma da `SWCREATE` o `CREATOR`.

Montatura, riduttore e ottica di guida non arrivano mai dai file: le scrive solo l'utente.

**Calcolati**:

- Camera, Pixel quando file e utente tacciono: ricavato dalla scala misurata sul cielo e dalla
  focale ("pixel (calcolato)", solo nella scheda, senza campo).
- Corredo, Rapporto focale: Focale effettiva / Apertura dell'ottica, quando ci sono tutte e due.
- Corredo, scala e campo: misurati sul cielo.

**Il resto si scrive solo a mano**: Apertura e Focale nativa dell'ottica, Peso, Carico utile,
Fattore, Numero di posizioni, Marca, Modello, Note, le larghezze dei filtri. Un valore scritto
dall'utente vince su quello dei file.

## 4. Da dove vengono i valori delle tendine

- **Tipi** (gli otto strumenti, Filtro, Corredo): lista fissa dell'app.
- **Bande** (L, R, G, B, HA, HB, OIII, SII): lista fissa dell'app.
- **Tipo di sensore** (mono, a colori): lista fissa dell'app.
- **Marche degli strumenti**: testo libero. L'app non ha un elenco. "altra…" / "Nuova marca"
  propone le marche gia' scritte dall'utente.
- **Ottica e Camera del corredo**, e la tendina di una parte: i pezzi dell'utente di quel tipo.
- **Unisci a**: solo i pezzi con cui l'app accetta l'unione.
- **I modelli di filtro in commercio** sono un catalogo che l'app porta con se': marca, nome,
  banda. Oggi si sceglie solo in Da confermare ("Modello da catalogo"), non nel modulo di
  Attrezzatura.
