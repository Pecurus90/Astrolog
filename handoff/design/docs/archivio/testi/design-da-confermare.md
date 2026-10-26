# Brief per Claude Design -- Da confermare

Dopo il primo avvio (v33). Vale tutto il primo brief (`design-brief.md`) e il foglio attuale
(v33). Si chiede **una cosa**: la pagina **Da confermare**, cioe' il posto dove l'app fa
all'utente le domande a cui i file da soli non rispondono.

Il metodo e' quello delle Notti, dell'Archivio e del primo avvio: la pagina **esiste gia'** e
funziona; le manca la forma. Sotto c'e' **esattamente** cio' che fa oggi e cio' che l'API manda. Un
dato o una domanda che non sta qui non va disegnato.

Consegna come le altre: prima le proposte (`pagine/da-confermare.html`,
`da-confermare-stati.html`), classi `pr-`; scelta la forma, i mattoni nel foglio (v34) e le pagine
senza `pr-`. Desktop 1440 e telefono 390 per ogni sezione.

I testi fra virgolette sono quelli dell'app, gia' approvati (nomi veri, tono neutro): **non vanno
riscritti**. Se un testo non regge nella forma che proponi, dillo a parte.

## 1. Cosa racconta la pagina

L'app legge i file e decide da sola tutto cio' che puo'. Dove non puo', **chiede**: qui. Ogni
domanda riguarda un **gruppo di frame**, mai un file solo, e la risposta vale per tutto il gruppo
(e, dove e' scritto, anche per i frame che arriveranno).

Tre regole che la forma deve far capire:

- **Le risposte si accumulano, e si scrivono tutte insieme** col comando "Applica". Finche' non lo
  premi non e' cambiato niente. Applica e' una scrittura sola: se una risposta viene rifiutata non
  se ne salva nessuna.
- **Non e' obbligatorio rispondere.** Una domanda senza risposta lascia quei frame come sono: l'app
  funziona lo stesso.
- **Alcune domande, risposte, restano in pagina** per poter cambiare idea; altre spariscono. Sotto
  e' detto per ognuna.

Sta **dentro il telaio** (binario, barra in alto, Stanotte). Nel binario e' l'ultima voce, staccata
dalle altre, col nome su due righe ("Da / confermare") e una pastiglia col numero di cose da
confermare, quando e' maggiore di zero. Sul telefono non e' fra le cinque schede: sta nel foglio
"Altro", con lo stesso numero, e il numero compare anche sulla scheda "Altro". Ci si arriva anche
dalle Notti ("Apri Da confermare").

## 2. Cosa c'e' in pagina, dall'alto

1. **Il titolo** "Da confermare" lo scrive il telaio, nella barra in alto. La pagina non ne ha un
   altro.
2. **Il conto**: "12 da confermare" / "1 da confermare". E' il numero delle domande ancora senza
   risposta, lo stesso della pastiglia.
3. **L'esito dell'ultimo Applica**, quando c'e' (vedi sezione 5).
4. **Le sezioni**, una per famiglia di domande, in quest'ordine. Una sezione senza domande non
   compare affatto:
   1. Strumenti duplicati
   2. Filtri
   3. Attrezzatura da completare *(oggi il backend la manda e lo schermo non la mostra: aspetta
      questo disegno)*
   4. Oggetti *(idem)*
   5. Frame senza tipo
   6. Frame senza sito
   7. Mosaici proposti
5. **Il piede, sempre in vista**: "3 modifiche da applicare" / "1 modifica da applicare", e il
   comando "Applica" (primario; spento con zero modifiche e mentre applica).

Ogni sezione oggi e' una carta: il **nome** della sezione, **una frase** che dice perche' l'app
chiede, e l'elenco delle domande. Ogni domanda e' una riga: **di cosa si parla** (un nome), **quanti
frame** ("412 frame", "1 frame"), i dati che aiutano a rispondere, e sotto **i controlli**.

Non ci sono, e non vanno disegnati: filtri, ordinamenti, ricerca, navigazione fra sezioni, un
"rispondi a tutte". L'ordine delle domande dentro una sezione lo decide l'API.

## 3. Le sezioni, una per una

### 3.1 Strumenti duplicati

Perche': "Strumenti con nome simile e stesse caratteristiche: possono essere lo stesso strumento
rilevato da due programmi. L'unione non e' reversibile."

Compare per due **camere** col nome quasi uguale (spazi, segni, parentesi), stesso pixel, stesso
tipo di sensore.

| dato | esempio |
|---|---|
| nome dello strumento (quello con meno frame) | "ATR2600M(USB2.0)" |
| i suoi frame | "38 frame" |
| a chi somiglia, coi suoi frame | "simile a ATR2600M (412 frame)" |

Controllo: una scelta fra due, con la domanda "ATR2600M(USB2.0) e ATR2600M sono lo stesso
strumento?":
- "Si', unisci a ATR2600M"
- "No, sono distinti"

Nessuna delle due e' scelta in partenza. **Unire non si annulla**: e' l'unica risposta della pagina
che non torna indietro, e la forma deve dirlo prima di Applica. Dopo Applica la domanda
**sparisce**, con tutte e due le risposte.

Difetto di oggi, da risolvere col disegno: il nome dell'altro strumento compare tre volte nella
stessa riga (nel dato, nella domanda, nella prima scelta).

### 3.2 Filtri

Perche': "Filtri non riconosciuti. L'associazione vale anche per i frame futuri."

Compare per un nome di filtro scritto nei file che l'app non sa a che banda corrisponde (per
esempio una "H" sola).

| dato | esempio |
|---|---|
| il nome come sta scritto nei file | "H" |
| i frame | "86 frame" |

Tre modi di rispondere, **uno esclude gli altri**:

1. **E' uno dei miei.** Tendina "Filtro esistente: H", con una voce vuota e poi i filtri che
   l'app conosce gia' (per nome). Sceglierne uno unisce questo nome a quel filtro.
2. **E' un modello del catalogo.** Campo "Cerca fra i modelli per H": l'elenco compare solo
   scrivendo, cerca in marca e nome, ogni voce e' un modello ("Antlia 3nm Narrowband H-alpha Pro").
   Scelto un modello, al posto della ricerca restano il campo "Nome" (si legge, non si scrive) e
   il comando "Cambia modello", che torna alla ricerca.
3. **Non e' in elenco.** Comando "Non in elenco: nuovo filtro": compaiono il campo "Nome" e la
   tendina "Banda" (L, R, G, B, HA, HB, OIII, SII). La larghezza in nanometri non si chiede.

Dopo Applica la domanda **sparisce**: il filtro ora ha una banda.

Stati da disegnare: la ricerca che non trova niente (oggi l'elenco resta vuoto e non dice niente);
"Elenco dei modelli non disponibile" (i modelli non si sono caricati: restano i modi 1 e 3); il
modo 3 con solo il nome o solo la banda (risposta a meta': oggi conta fra le modifiche, e non
dovrebbe); il ritorno dal modo 3 agli altri due (oggi non c'e').

### 3.3 Attrezzatura da completare

**Oggi non si vede**: il backend la manda, la pagina la conta e non la mostra. Va disegnata.

Compare quando i file non dicono con che **camera**, con che **ottica** o con che **filtro** sono
stati ripresi. Una scheda per ogni gruppo di file che scrivono le stesse cose (stesso nome di
camera e di telescopio, stessa focale, stesso sensore): non per notte e non per cartella. La
risposta vale per tutti quei frame, anche futuri.

Cio' che la scheda mostra (tutto puo' mancare, tranne i frame):

| dato | esempio |
|---|---|
| la camera come sta scritta nel file | "ZWO ASI2600MM Pro", o niente |
| il telescopio come sta scritto nel file | "EQ6-R" (con l'ASIAIR qui c'e' la montatura), o niente |
| il sensore | 6248 x 4176 px, pixel 3,76 um |
| i frame | "214 frame" |
| l'ottica e la focale che i frame dicono gia' | "Askar FRA400", 400 mm |
| la focale suggerita (nativa di quell'ottica), se i frame non la dicono | 400 mm |
| gli oggetti ripresi in quei frame | come nella sezione 3.6 ("Oggetti: ...") |

La scheda chiede **solo le parti che mancano**, da una a tre. Ogni parte e' una domanda a se':

- **La camera** -- si risponde scegliendo **uno dei propri corredi** (ognuno col suo nome, o con
  ottica e camera se il nome non c'e'), oppure scrivendo la camera e la focale, e l'ottica se
  serve. L'app propone l'ottica che i frame dicono e la focale nativa.
- **L'ottica** -- si sceglie **una delle proprie ottiche** (elenco di nomi) o se ne scrive il nome.
- **Il filtro** -- una scelta fra tre: "a colori, senza filtro" (possibile solo se si sa qual e' la
  camera), "nessun filtro", "uno dei miei filtri" (e allora una tendina coi filtri che l'app
  conosce).

Si puo' rispondere **una parte alla volta**: quella data resta, e la scheda conta fra le cose da
confermare finche' non ha tutte le parti che chiede. Risposta, la scheda **resta in pagina** con
cio' che si e' detto, per cambiare idea.

Stati: scheda che chiede una parte sola; due; tre; scheda a meta' (una parte data, una no); scheda
completa; il filtro scelto che non esiste piu' (la risposta c'e', il filtro no).

### 3.4 Oggetti

**Oggi non si vede**: come sopra, va disegnata.

Una scheda per gruppo di frame, **sempre con la stessa forma**, in due casi:

- **Un oggetto in dubbio**: l'app ha messo i frame su un oggetto ma non ne e' sicura (il nome del
  file e il cielo non vanno d'accordo, o il cielo esita fra oggetti vicini, o il nome non e' nel
  catalogo).
- **Frame senza nome**: i file non dicono cosa e' stato ripreso e il cielo non dice niente.

| dato | esempio |
|---|---|
| l'oggetto che l'app ha trovato (manca nei frame senza nome) | "NGC 7000" |
| i frame, le ore, e a parte i frame senza durata | "64 frame", "5,3 h", "3 senza durata" |
| cio' che il cielo ha trovato nel campo, da scegliere (anche zero voci) | "NGC 7000 - Nebulosa Nord America", "IC 5070 - Nebulosa Pellicano" |
| per ogni voce, se sta dentro l'inquadratura (si', no, non si sa) | |
| **solo nei frame senza nome**: la notte | 12 agosto 2025 |
| la camera e il telescopio come scritti nel file | "ASI2600MM", "FRA400" |
| dove puntava la montatura | RA 314,7 Dec 44,3 |
| l'ora del primo e dell'ultimo frame | "dalle 21:10 alle 03:40" |

Si risponde in **uno** di tre modi: si sceglie una voce fra quelle trovate dal cielo; si scrive il
nome; oppure "non e' un oggetto" (un frame di prova, una messa a fuoco: quei frame escono dalle
ore). Risposta, la scheda **resta in pagina** per cambiare idea.

In fondo alla sezione, un numero: **quanti sono gli oggetti gia' a posto** (per esempio 218), che
non sono domande. Si aprono a pagine e si correggono con la stessa scheda. Vanno disegnati chiusi,
e aperti. Il testo di quella riga non c'e' ancora: lo scrive Marco.

I testi delle sezioni 3.3 e 3.4 non esistono ancora nell'app (non si vedono): quelli scritti qui
sono descrizioni, non parole approvate. Proponi la forma; le parole si decidono dopo.

Stati: dubbio con piu' voci; dubbio con zero voci (resta solo scrivere, o "non e' un oggetto");
frame senza nome con tutti i dati; senza puntamento; senza ore; scheda gia' risposta nei tre modi.

### 3.5 Frame senza tipo

Perche': "Tipo di frame non indicato nei file. Finche' non viene indicato, i frame sono esclusi
dal conteggio delle ore."

Compare per una **cartella** i cui file non dicono se sono Light o calibrazione.

| dato | esempio |
|---|---|
| il percorso della cartella | "D:\Astro\M31\Sconosciuto" (puo' essere lungo) |
| i frame | "120 frame" |

Controllo: una scelta fra due, "Tipo dei frame in D:\Astro\M31\Sconosciuto": "Light" /
"Calibrazione". Non c'e' "non lo so". Risposta, la domanda **resta in pagina** con la scelta
fatta, e si cambia scegliendo l'altra.

Difetto di oggi: la risposta gia' data e' scritta come parola nuda ("Light") accanto alle due
scelte, e sembra una terza cosa.

### 3.6 Frame senza sito

Perche': "Frame ripresi a coordinate che non corrispondono a nessun sito. L'associazione vale
anche per le notti future."

Compare per frame le cui coordinate non cadono in nessun sito dichiarato, raggruppati per posto.

| dato | esempio |
|---|---|
| le coordinate del posto | "46.10,12.00" |
| i frame | "52 frame" |
| gli oggetti ripresi li': i primi tre coi loro frame, poi quanti altri | "Oggetti: M 31 (12 frame), M 33 (4 frame), NGC 7000 (3 frame) + 2" |
| a parte, se ci sono | "8 frame senza oggetti identificati"; "5 frame non risolti" |
| la distanza dal sito predefinito (manca se non c'e' un sito predefinito) | "a 38,2 km dal sito predefinito" |
| le notti | "notti: 2025-08-12, 2025-08-13", oppure "Notti non calcolabili senza sito" |

Controllo: una scelta fra i **siti dichiarati**, dal piu' vicino, "Sito per le coordinate
46.10,12.00": "Malga in quota, a 2,1 km" / "Casa, a 38,2 km". Risposta, la domanda **resta in
pagina** col sito scelto.

Stati: senza sito predefinito; con molte notti (possono essere decine); con oggetti oltre il
terzo; senza oggetti; **nessun sito dichiarato** (oggi la domanda compare senza niente da
scegliere: serve dire dove si aggiunge un sito).

### 3.7 Mosaici proposti

Perche': "Pannelli adiacenti ripresi con lo stesso corredo. Vengono uniti solo dopo conferma."

Compare quando l'app trova pannelli affiancati dello stesso soggetto: **propone**, non unisce.

| dato | esempio |
|---|---|
| gli oggetti dentro, in ordine alfabetico | "IC 1318, NGC 6910" |
| i frame e i pannelli | "240 frame", "4 pannelli" / "1 pannello" |
| le ore, e a parte i frame senza durata | "20,0 h", "3 senza durata", "< 0,1 h" |
| dove sta | "a RA 305,2 Dec 40,6" (distingue due mosaici dello stesso soggetto) |

Controllo: "IC 1318, NGC 6910, RA 305,2 Dec 40,6: mosaico?" -- "Mosaico" / "Non e' un mosaico".
Scelto "Mosaico" compare il campo "Oggetto del mosaico (RA 305,2 Dec 40,6)", gia' riempito col nome
che l'app propone, con suggerimenti fra i nomi che conosce. Risposta, la proposta **resta in
pagina**.

Difetto di oggi: la domanda mette le coordinate in fila con gli oggetti, e si legge male.

## 4. La riga che dice "ho risposto"

Oggi una domanda con una risposta **non ancora applicata** prende una barra piena a sinistra. La
stessa barra pero' dice cose diverse nelle diverse sezioni. Servono, distinte e non col solo
colore:

- **senza risposta**;
- **risposta data ora, non ancora applicata** (conta nel piede);
- **risposta gia' salvata** (solo nelle sezioni che restano in pagina: 3.3, 3.4, 3.5, 3.6, 3.7);
- **risposta salvata che sto cambiando** (di nuovo non applicata).

## 5. Applica, e gli stati della pagina

- **Mentre applica**: oggi il comando si spegne e basta, e le sezioni restano accese (una risposta
  data in quel momento si perde). Serve il segno dell'attesa sul comando e le sezioni ferme.
- **Riuscito**: "5 modifiche applicate, 320 frame da rielaborare" / "1 modifica applicata, 320
  frame da rielaborare". Oggi resta a schermo fino al prossimo Applica, senza modo di chiuderlo.
- **Non riuscito** (non si e' salvato niente): "Modifiche non applicate", oppure
  - "Oggetto non presente nel catalogo. Nessuna modifica salvata."
  - "Dati non aggiornati: ricarica la pagina. Nessuna modifica salvata."
  - "Scansione in corso: riprova al termine. Nessuna modifica salvata."
  - "Unione non possibile. Nessuna modifica salvata."
  - "Nome gia' usato da un altro strumento. Nessuna modifica salvata."
- **In lettura**: oggi una riga "Caricamento...". Serve lo scheletro.
- **Non si legge**: "Da confermare non disponibile".
- **Niente da confermare**: oggi **non esiste**. Resta il conto e il piede vuoto. Va disegnato: e'
  lo stato in cui la pagina sta quasi sempre, e deve dire che e' tutto a posto. Con risposte
  salvate che restano in pagina (3.3-3.7) il conto e' zero ma le sezioni ci sono: sono due stati
  diversi.
- **A mani vuote** (primo avvio, zero frame): niente da chiedere perche' non c'e' ancora niente.

## 6. Telefono

Oggi non c'e' niente di pensato: la colonna si stringe e basta. Da disegnare a 390:

- il piede con "N modifiche da applicare" e "Applica", sopra la barra delle schede;
- i percorsi lunghi delle cartelle (3.5) e gli elenchi lunghi di notti e oggetti (3.6);
- la scheda dell'attrezzatura con tre parti (3.3) e quella dell'oggetto con le voci del cielo (3.4);
- le scelte fra due o tre voci fisse, con bersagli da 44;
- la ricerca dei modelli di filtro col suo elenco (3.2).

## 7. Cose aperte

- **Il campo dei moduli c'e' gia'** nel foglio v33 (`.as-campo-modulo`, `.as-campo-riga`,
  `.as-campo-coppia`, `.as-modulo`), e cosi' l'avviso (`.as-avviso` coi toni buono, attesa,
  allarme, ignoto) e la carta sola. Si riusano.
- **La tendina dei moduli non ha veste**: oggi e' una `<select>` con la classe `as-scelta`, che il
  foglio non ha. Serve anche ad Attrezzatura e Impostazioni: va disegnata come mattone.
- **La scelta fra due o tre voci fisse** oggi e' un gruppo di radio nudi (il foglio non ha una
  classe per un radio). In coda c'e' l'idea di farne un segmentato: decidi tu la forma, e' la
  stessa in cinque sezioni.
- **Il bottone spento** nel foglio e' `aria-disabled`, e al lavoro `aria-busy`: vanno bene cosi'.
- **Classi che la pagina scrive oggi e il foglio non ha** (servono i mattoni): `as-carta__titolo`,
  `as-carta__domanda`, `as-carta__corpo` (`--stretto`); la riga della domanda `as-riga--risposta`,
  `as-riga__testa`, `as-riga__nome` (`--oggetto`), `as-riga__conteggio`, `as-riga__prova`,
  `as-riga__risposte`; il piede `as-conferma-tutto` (`__conta`, `__azioni`); l'elenco dei modelli
  `as-comparsa__righe`, `as-comparsa__voce`; `as-scelta`.
- **Attenzione a `.as-riga`**: nel foglio esiste gia' ed e' la riga del lavoro della Dashboard. La
  riga di una domanda e' un'altra cosa: le serve un nome suo.
- **Non esistono, e non vanno disegnati**: rispondere a un file solo; annullare un'unione di
  strumenti; un filtro "a mano" con la larghezza di banda; una cronologia delle risposte; la
  domanda "quale dei due file e' l'originale".
