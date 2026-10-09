# Brief per Claude Design -- Attrezzatura

Dopo Da confermare (v34). Vale tutto il primo brief (`design-brief.md`) e il foglio attuale (v34).
Si chiede **una cosa**: la pagina **Attrezzatura**, cioe' il posto dove l'utente vede con cosa ha
ripreso e quanto, e dove corregge o aggiunge i suoi pezzi.

Il metodo e' quello delle altre pagine: la pagina **esiste gia'** e funziona; le manca la forma.
Sotto c'e' **esattamente** cio' che fa oggi e cio' che l'API manda. Un dato o un gesto che non sta
qui non va disegnato.

Consegna come le altre: prima le proposte (`pagine/attrezzatura.html`, `attrezzatura-stati.html`),
classi `pr-`; scelta la forma, i mattoni nel foglio (v35) e le pagine senza `pr-`. Desktop 1440 e
telefono 390 per ogni parte.

I testi fra virgolette sono quelli dell'app, gia' approvati (nomi veri, tono neutro): **non vanno
riscritti**. Se un testo non regge nella forma che proponi, dillo a parte.

## 1. Cosa racconta la pagina

"Con cosa hai ripreso, e quanto." Tre famiglie di cose:

- gli **strumenti**, divisi per tipo (un telescopio, una camera, una montatura...);
- i **corredi**: un'ottica piu' una camera a una focale, cioe' la combinazione con cui si riprende;
- i **filtri**.

Per ognuno: quanti frame, quante ore, quante notti, e quali oggetti ci sono stati ripresi.

Regole che la forma deve far capire:

- **Tutto viene dai file.** L'app trova i pezzi leggendo gli header; l'utente non compila un
  inventario. Puo' aggiungere a mano cio' che i file non dicono, e allora il pezzo e' segnato
  "inserito manualmente".
- **Dove un numero non c'e', la pagina dice perche'**, e non scrive zero. "Non lo so" e "zero" sono
  due cose diverse, e qui ci sono tre "non lo so" diversi (sotto, 4.1).
- **Cio' che l'utente scrive vince sui file** e resta anche quando l'archivio viene riletto.
- **Un pezzo non si cancella.** Si corregge, si rinomina, si unisce a un altro. L'unione **non si
  annulla**.
- **Niente da quando ce l'hai**: nessuna data d'acquisto, nessuna prima notte.
- **Tutti i pezzi stanno in una pagina sola**, senza ricerca interna, senza ordinamenti, senza
  pagine: l'attrezzatura di una persona e' una manciata di cose, non mille.

Sta **dentro il telaio** (binario, barra in alto, Stanotte); il titolo "Attrezzatura" lo scrive il
telaio, la pagina non ha un titolo suo. Ci si arriva anche dalla ricerca nella barra: scegliendo
uno strumento o un filtro la pagina si apre **su quella riga** (4.5).

Ordini di grandezza, da un archivio di prova: 10-15 strumenti, 5-6 corredi, 6-8 filtri. Un gruppo
non supera le decine di righe; molti gruppi hanno una riga sola.

## 2. Cosa c'e' in pagina, dall'alto

1. **Il gesto "Aggiungi strumento"**, in cima, sempre: anche il primo giorno, anche a mani vuote.
2. **Un gruppo per tipo di strumento**, in quest'ordine fisso, ognuno col suo titolo:
   "Telescopi e obiettivi", "Camere", "Montature", "Riduttori e spianatori", "Ruote portafiltri",
   "Guide", "Camere di guida", "Focheggiatori".
3. **"Corredi"**.
4. **"Filtri"**.

**Un gruppo senza righe non si disegna**: niente titolo, niente "nessuna camera". Chi ha solo un
telescopio e una camera vede due gruppi e i corredi.

## 3. Le righe, una per una

Ogni riga ha: un nome, i dati della sua scheda (solo quelli che hanno un valore), **l'uso** (4.1),
**cosa ci e' stato ripreso** (4.2), e i suoi gesti.

### 3.1 Uno strumento

Cio' che l'API manda per uno strumento, e come si legge oggi:

| dato | forma | quando manca |
|---|---|---|
| nome | testo, sempre | -- |
| marca, modello | testo | non si scrivono |
| apertura | "apertura 103 mm" | non si scrive |
| focale | "focale 700 mm" | non si scrive |
| tipo di sensore | "monocromatica" / "a colori" | non si scrive |
| pixel | "pixel 3,76 um" | vedi sotto |
| carico | "carico 15 kg" (montatura) | non si scrive |
| peso | "peso 4,5 kg" | non si scrive |
| posizioni | "7 posizioni" / "1 posizione" (ruota) | non si scrive |
| riduzione | "riduzione 0,8x" (riduttore) | non si scrive |
| note | testo libero dell'utente | non si scrivono |
| origine | "inserito manualmente" | se viene dai file non si dice niente |

(`um` sta per micrometri, col segno vero a schermo.)

Quali dati ha un tipo: tutti hanno marca, modello, peso, note. In piu': l'ottica apertura e focale;
la camera tipo di sensore e pixel; la montatura il carico; il riduttore il fattore; la ruota le
posizioni. Guida, camera di guida e focheggiatore non hanno altro.

**Il pixel calcolato.** Se ne' i file ne' l'utente dicono il pixel di una camera, l'app lo ricava
dal cielo e lo scrive "pixel 3,76 um (calcolato)". Va distinto a colpo d'occhio dal pixel
dichiarato: e' una misura, non un dato di targa.

**Gesto: "Modifica".** Apre la scheda **dentro la riga**, col nome dello strumento come titolo.
Campi: "Nome", poi quelli del tipo ("Marca", "Modello", "Apertura (mm)", "Focale nativa (mm)",
"Tipo di sensore" con "mono" / "a colori", "Pixel (um)", "Fattore", "Carico utile (kg)", "Numero di
posizioni", "Peso (kg)", "Note"), poi la tendina **"Unisci a"**, poi "Salva" e "Annulla".

- "Unisci a" c'e' **solo se** esiste almeno un altro strumento dello stesso tipo a cui l'app
  accetta di unirlo. Scelto un bersaglio, **gli altri campi spariscono**: unire non e' correggere.
- **L'unione non si annulla**, e oggi la scheda non lo dice prima di "Salva". Va disegnato un
  avviso, come in Da confermare ("Include un'unione di strumenti: non e' reversibile.").
- Un campo **non si svuota**: si corregge scrivendo un altro valore.
- "Salva" e' spento finche' la scheda non e' valida, e mentre salva.

### 3.2 Un corredo

| dato | forma | quando manca |
|---|---|---|
| nome | il nome dato dall'utente | allora il nome e' "{ottica} + {camera}" |
| ottica e camera | "Askar 103Apo + ASI2600MM Pro" | "ottica non indicata", "camera non indicata" |
| focale | "700 mm" | non si scrive |
| montatura | "su ZWO AM5" | non si scrive |
| scala | "1,11 arcosecondi per pixel" | vedi sotto |
| campo | "campo 1,93 x 1,29", ogni numero col segno di grado e fra i due il segno per | vedi sotto |

Se il corredo ha un nome dato dall'utente, sotto il nome resta scritto "{ottica} + {camera}".

**Scala e campo si misurano**, sulle pose che il riconoscitore ha risolto: non si calcolano da
focale e pixel. Se nessuna posa e' ancora risolta la riga dice "campo non ancora disponibile". Non
vuol dire "mai ripreso": vuol dire che la misura non c'e' ancora.

**Gesti: due.**

- **"Rinomina"**: apre nella riga "Nome di {nome}", un solo campo "Nome".
- **"Seleziona montatura"**: c'e' **solo se** l'utente possiede almeno una montatura. Apre
  "Montatura di {nome}" con una tendina "Montatura (vuoto: dai file)" fra le sue montature. La
  scelta vuota vuol dire "torna a cio' che dicono i file". "Salva" e' spento finche' la scelta non
  cambia.

Un corredo **non si unisce e non si cancella**.

### 3.3 Un filtro

| dato | forma | quando manca |
|---|---|---|
| nome | testo, sempre | -- |
| marca, modello | testo | non si scrivono |
| bande | una riga per banda: "HA 3 nm" | senza larghezza: solo "HA"; senza bande dichiarate: niente |

Un filtro puo' avere **piu' bande** (un doppia banda: "HA 7 nm" e "OIII 7 nm"). Le bande possibili:
L, R, G, B, HA, HB, OIII, SII.

**Gesto: "Modifica".** Come lo strumento: "Nome", "Marca", "Modello", "Unisci a" (stesse regole:
solo se c'e' a chi unirlo, e non si annulla). **La banda non si corregge** da qui.

## 4. Cio' che vale per tutte le righe

### 4.1 L'uso, e i tre modi di non saperlo

Quando i numeri ci sono: "214 frame", le ore ("35,6 h"), le notti ("12 notti" / "1 notte"). Se
alcune pose non dicono la durata, accanto alle ore: "3 senza durata". Le notti si scrivono solo se
sono piu' di zero.

Quando non ci sono, **una frase al posto dei numeri**, mai uno zero:

- **"conteggio in corso"**: lo strumento e' appena nato, a meta' scansione, e l'app non l'ha ancora
  contato. Passa da solo.
- **"non indicato nei file"**: il programma di ripresa non scrive quel tipo di strumento su ogni
  posa (una ruota aggiunta a mano, un focheggiatore), quindi le sue ore non si possono sapere.
- **"non associata a un corredo"**: una montatura che nessun corredo porta.

Le tre frasi hanno peso diverso: la prima e' un'attesa, le altre due sono fatti stabili, e la terza
ha un rimedio nella stessa pagina ("Seleziona montatura" su un corredo).

### 4.2 Cosa ci e' stato ripreso

Un elenco di **oggetti**, dal piu' ripreso: per ognuno il nome, i frame e le ore. Oggi e' una fila
di nomi separati da virgole. Puo' essere lungo (decine di oggetti per una camera usata anni) o
vuoto. Un oggetto puo' non avere nome.

### 4.3 Aggiungere

"Aggiungi strumento" apre un modulo "Nuovo strumento". Prima si sceglie il **"Tipo"**: gli otto
tipi di strumento (al singolare: "ottica", "camera", "montatura", "riduttore", "ruota portafiltri",
"ottica di guida", "camera di guida", "focheggiatore"), piu' **"Filtro"** e **"Corredo"**. Il modulo
cambia col tipo:

- **strumento**: "Nome" e i campi di quel tipo (3.1);
- **filtro**: "Nome", "Banda" (obbligatoria), "Marca", "Modello";
- **corredo**: "Ottica" e "Camera" (due tendine fra gli strumenti dell'utente), "Focale effettiva
  (mm)".

Poi "Salva" e "Annulla". Le tendine hanno una voce vuota, scritta "--".

### 4.4 I rifiuti

Un salvataggio puo' essere rifiutato. La frase compare **dentro il modulo**, e non si salva niente:

- "Nome gia' usato da uno strumento dello stesso tipo."
- "Nome gia' usato da un altro filtro."
- "Corredo gia' presente (stessa ottica, stessa camera, focale entro il 5%)."
- "Ottica e camera vanno selezionate fra gli strumenti del tipo corrispondente."
- "Unione non possibile. Nessuna modifica salvata."
- "Dati non aggiornati: ricarica la pagina. Nessuna modifica salvata."
- "Scansione in corso: riprova al termine."
- "Salvataggio non riuscito."

**Mentre l'app legge i file non si scrive niente**: ogni salvataggio torna "Scansione in corso:
riprova al termine." Una scansione puo' durare a lungo. Oggi lo si scopre solo premendo "Salva":
si puo' proporre di dirlo prima.

### 4.5 La riga su cui si arriva

Dalla ricerca nella barra si arriva su **uno strumento o un filtro preciso**: la pagina scorre fino
a quella riga e la segna. Il segno oggi non ha una veste. I corredi non hanno ancora un indirizzo.

### 4.6 Dopo un salvataggio

Il modulo si chiude e la pagina si rilegge. Alcune modifiche rimettono al lavoro l'app (cambiare
una camera da mono a colori fa rielaborare i suoi frame senza filtro): oggi la pagina **non dice
niente**, ne' "salvato" ne' "N frame da rielaborare". In Da confermare c'e' un esito che si chiude
("1 modifica applicata, 38 frame da rielaborare"): qui manca, e va proposto.

## 5. Gli stati della pagina

- **In lettura**: oggi la parola "Caricamento...". Serve lo scheletro.
- **Non si legge**: "Attrezzatura non disponibile". Oggi senza modo di riprovare.
- **A mani vuote** (nessuno strumento, nessun corredo, nessun filtro): "Nessuna attrezzatura",
  "L'attrezzatura viene rilevata dagli header dei file FITS dopo la scansione.", e il collegamento
  "Aggiungi cartella". **"Aggiungi strumento" resta in cima anche qui.**
- **Piena.**
- **Un modulo aperto** (aggiunta in cima; modifica dentro una riga), valido e non valido, mentre
  salva, rifiutato.
- **Durante una scansione** (4.4).

Oggi si possono aprire piu' moduli insieme, uno per riga. Da confermare ha scelto "una cosa aperta
alla volta": dire se vale anche qui.

## 6. Telefono

Stessi dati, stessi gesti. Le righe portano molto (nome, scheda, uso, oggetti, uno o due gesti): su
390 serve una forma che non tagli niente. I moduli si aprono nel flusso della pagina.

## 7. Cose aperte

- **La riga non ha un nome nel foglio.** La pagina scrive `.as-riga` con `__testa`, `__nome`,
  `__conteggio`, `__perche`, `__risposte`, che nel foglio e' un'altra cosa (la riga del lavoro
  della Dashboard). Serve un mattone suo. Idem il pannello che si apre nella riga (`.as-apertura`,
  in attesa dal v34) e la riga dei gesti in cima (`.as-pagina__azioni`).
- **I testi che non esistono**: l'avviso dell'unione nella scheda, l'esito di un salvataggio, lo
  stato "scansione in corso" detto prima di salvare, il segno della riga su cui si arriva per chi
  ascolta. Il testo lo scrive Marco: lasciare il posto.
- **Cio' che la pagina non fa, per scelta**: cancellare un pezzo, correggere la banda di un filtro,
  correggere la focale di un corredo, svuotare un campo, il valore in denaro, la manutenzione, la
  posizione di un filtro nella ruota, il peso del corredo contro il carico della montatura. Non
  vanno disegnati.
- **Un dato che c'e' e non si puo' scrivere**: il backfocus. L'app lo mostrerebbe ("backfocus 55
  mm") ma oggi nessuno lo riempie: non va disegnato come campo.
