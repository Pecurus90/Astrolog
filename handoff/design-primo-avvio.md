# Brief per Claude Design -- il primo avvio

Dopo l'Archivio (v31-v32). Vale tutto il primo brief (`design-brief.md`) e il foglio attuale
(v32). Si chiede **una cosa**: il **primo avvio**, cioe' i passi che l'app mostra a chi l'ha appena
installata, prima di ogni altra pagina.

Il metodo e' quello delle Notti e dell'Archivio: la pagina **esiste gia'** e funziona; le manca la
forma. Oggi e' la pagina piu' spoglia dell'app, ed e' la prima che chiunque vede. Sotto c'e'
**esattamente** cio' che fa oggi e cio' che l'API manda. Un dato o un passo che non sta qui non va
disegnato.

Consegna come le altre: prima le proposte (`pagine/primo-avvio.html`, `primo-avvio-stati.html`),
classi `pr-`; scelta la forma, i mattoni nel foglio (v33) e le pagine senza `pr-`. Desktop 1440 e
telefono 390 per ogni passo.

## 1. Cosa racconta la pagina

Il primo avvio chiede **poche cose e poi si toglie di mezzo**. Non e' un obbligo: si puo' saltare
da ogni passo, senza conferme, e l'app funziona lo stesso. Completarlo o saltarlo e' la stessa
cosa per l'app: non lo richiede piu'.

Non e' una pagina dell'app: **non c'e' il telaio** (niente binario, niente barra in alto, niente
Stanotte). E' una colonna centrata, da sola sullo schermo.

Com'e' fatta oggi:

- **Testata**: titolo "Primo avvio", sotto "Puoi saltare: l'app cataloga e cerca lo stesso."
- **Binario dei passi**: "Passo 2 di 4" e l'elenco dei passi col nome. Ogni tappa ha tre stati:
  fatta (spunta), quella dove sei, quelle che vengono. Non sono bottoni: non si salta avanti
  toccandole.
- **Una carta per passo**: il titolo del passo, una riga che dice **perche'** l'app lo chiede, i
  controlli, e in fondo i gesti: a sinistra "Salta per ora", a destra "Indietro" (non al primo
  passo) e "Avanti" (primario); all'ultimo passo "Fatto".

I passi sono **quattro, o cinque**: il quinto compare solo a chi non ha il riconoscitore. Quanti
sono si decide entrando e non cambia piu' a meta'.

## 2. I passi, uno per uno

### Passo 1 -- "Come ti chiami"

Perche': "Serve a salutarti nella barra in alto, e a intestare le tue statistiche."

| controllo | cos'e' | note |
|---|---|---|
| Nome | campo di testo, segnaposto "Come vuoi essere chiamato" | facoltativo |

Aiuto sotto il campo: "Per ora l'app lo conserva soltanto. Si puo' lasciare vuoto."

### Passo 2 -- "Da dove osservi"

Perche': "Senza un sito le notti non nascono: serve per le fasce della notte e per l'altezza degli
oggetti. Puoi aggiungerne altri piu' avanti."

Tre blocchi, in quest'ordine:

1. **"Cerca il posto per nome"**: campo "Nome del posto" e bottone "Cerca" (spento a campo vuoto).
2. **"Oppure scrivi le coordinate"**, con la riga: "Sempre aperta, non solo quando la ricerca
   fallisce: un sito buio puo' non avere rete, ed e' proprio dove si osserva."
   - "Nome del sito" (segnaposto "es. Malga in quota")
   - "Latitudine" (segnaposto "46,4843 N") e "Longitudine" ("12,0561 E"), sulla stessa riga.
     Accettano virgola o punto, e la lettera del verso.
3. **"Che cielo hai"**: la **scala di Bortle**, nove classi da 1 a 9, ognuna col suo colore (da
   freddo a caldo) e la cifra. Agli estremi "1 - buio pieno" e "9 - centro citta'". Scelta una
   classe compare il suo nome e cosa ci si vede (classe 5: "cielo di periferia", e una frase).
   Aiuto: "Facoltativo: se non sai che cielo hai, vai avanti. La misura del cielo la ricava l'app
   dalla classe." Nessuna classe e' scelta in partenza.

In fondo al passo il bottone primario **"Usa questo sito"**, spento finche' non ci sono un nome e
due coordinate valide. Premuto, salva e porta da solo al passo dopo. "Avanti" invece va oltre
**senza salvare**: oggi i due bottoni si confondono, ed e' la cosa da risolvere in questo passo.

Non si chiedono, e non vanno disegnati: il **fuso** (l'app lo ricava dalle coordinate),
l'**altitudine**, la misura del cielo in magnitudini.

### Passo 3 -- "Dove stanno i file"

Ha **due forme**, e l'utente ne vede una sola, secondo dove gira l'app.

**Sul computer** -- perche': "Scrivi il percorso di una cartella: la leggo tutta, sottocartelle
comprese. Puoi indicarne piu' di una."
- campo "Percorso della cartella" e bottone "Guarda".

**Sul NAS (Docker)** -- perche': "L'app gira dentro un container: il percorso che vede lei non e'
quello che vedi tu, e non si puo' indovinare. Sfoglia le cartelle e dimmi quale usare."
- "Scegli una cartella"; il percorso a briciole, l'ultimo pezzo in evidenza;
- "Usa questa cartella" e, se c'e', "Sali di una cartella";
- l'elenco delle sottocartelle, che scorre, ognuna con "Apri". Vuoto: "qui dentro non ci sono
  altre cartelle".

Dopo "Guarda" (o "Usa questa cartella") l'app **dice cosa ha trovato** (vedi gli stati) e offre
il bottone primario "Aggiungi la cartella".

Sotto, solo se ce n'e' almeno una: **"Le cartelle che hai indicato"**, col conteggio, e una riga
per cartella (percorso, numero di frame). Se ne possono aggiungere quante si vuole.

### Passo 4 -- "Il seeing per la planetaria"

Perche': "Se hai una chiave Meteoblue, il seeing arriva ora per ora e per sette notti. Non e'
obbligatoria: senza, il seeing non c'e' e il resto del meteo funziona uguale. Puoi saltare e
metterla dopo nelle Impostazioni."

- riga di stato: "Nessuna chiave: il seeing non c'e'." oppure "Chiave salvata, che finisce con
  ab12." e il collegamento "Come si chiede una chiave gratuita";
- campo "Chiave Meteoblue" e bottone primario "Prova e salva" (spento a campo vuoto);
- con una chiave salvata, "Togli la chiave".

### Passo 5 -- "Il riconoscitore" (solo a chi manca)

Il riconoscitore e' ASTAP, un programma esterno che riconosce il cielo dalle stelle. L'app **non
scarica e non installa niente**: dice dove si prende. Il passo ha **due forme**; accanto al titolo
una pastiglia dice quale: "non trovato" o "senza catalogo".

**ASTAP non c'e'** -- perche': "Sul computer non trovo ASTAP, il programma che riconosce il cielo
dalle stelle inquadrate. Non e' un guasto: e' una cosa da fare, e si puo' fare anche dopo."
- "Cosa cambia senza": "Senza, l'app cataloga i tuoi file, mette in ordine i nomi e conta le ore,
  ma non sapra' dirti cosa hai ripreso. Puoi installarlo anche piu' avanti."
- "Dove si prende": collegamento "Scarica ASTAP dal sito dell'autore", e "L'app non scarica e non
  installa niente: l'indirizzo e' scritto qui perche' tu possa andarci, quando vuoi."
- "Se ce l'hai gia'": campo "Se ce l'hai gia', dove sta" (segnaposto
  `C:\Program Files\astap\astap_cli.exe`) e bottone primario "Usa questo". Aiuto: "Il percorso va
  fino al programma, non alla cartella che lo contiene."

**ASTAP c'e', manca il catalogo stellare** -- perche': "ASTAP c'e', ma gli manca il catalogo
stellare: senza, non riconosce niente. Non e' un guasto: e' un download a parte, e si puo' fare
anche dopo."
- avviso "Manca il catalogo stellare", collegamento "Scarica il catalogo stellare", e "Se non sai
  quale, prendi il D80: e' il piu' completo, circa 1,25 GB. Va messo nella stessa cartella del
  programma." Qui il percorso **non** si chiede.

## 3. Gli stati

**Comuni a ogni passo**
- **Non ho potuto salvare**: "le impostazioni non hanno risposto". Si resta sul passo.
- **Mentre salva**: il bottone che ha chiesto. Oggi non c'e' nessun segno: va disegnato.

**Passo 2, il sito**
- Coordinata sbagliata, sotto il suo campo: "non e' una coordinata: scrivi un numero, con o senza
  la lettera del verso", oppure "deve stare fra -90 e 90" (-180 e 180 per la longitudine).
- Coordinate scritte e nome mancante: "serve un nome per ritrovare questo posto".
- **Ricerca in corso**: oggi non si vede niente. Va disegnato.
- **Piu' posti trovati**: un elenco; ogni riga il nome, le coordinate e "Scegli". Quello scelto
  e' segnato e dice "scelto". Scegliere riempie nome e coordinate, che restano modificabili.
  ("Verona" esiste in due posti: le coordinate sulla riga servono a distinguerli.)
- **Niente trovato**: "nessun sito trovato: puo' essere il nome, o la rete. Scrivi tu le
  coordinate."
- **La ricerca non ha risposto**: con "Riprova" e "Scrivi le coordinate a mano".
- Sito non salvato: "Non ho potuto salvare il sito".

**Passo 3, le cartelle**
- **Dentro c'e' roba da leggere**: "1.240 file FITS".
- **Il numero e' un minimo, non un totale**: "Ne ho contati 5.000 e ho smesso di contare: ce ne
  sono almeno tanti."
- **Questa cartella non si raggiunge**: "Finche' la cartella non risponde non c'e' niente da
  registrare. Correggi il percorso, o collega il disco e riprova." Niente bottone "Aggiungi".
- **E' una cartella che conosco** (gia' registrata altrove, spostata): il bottone diventa "Usala
  da qui".
- Errori: "non si e' potuto guardare li'", "la cartella non si e' registrata".
- **Solo NAS, l'elenco non arriva**: "Non riesco a leggere l'elenco", con "Riprova"; sotto compare
  il campo del percorso a mano, e "E' il percorso come lo vede il container, non come lo vedi tu
  dal computer."

**Passo 4, la chiave**
- "La chiave vale: il seeing ora viene da Meteoblue."
- "Chiave tolta: il seeing non c'e' piu'."
- "Meteoblue non riconosce questa chiave: non l'ho salvata."
- "Meteoblue non risponde: non ho potuto provare la chiave, e non l'ho salvata."
- Mentre prova: il segno dell'attesa sul campo.

**Passo 5, il riconoscitore**
- Percorso sbagliato, sotto il campo: "Li' non c'e' ASTAP. Controlla il percorso: deve finire col
  programma (si chiama astap_cli), non con la cartella dove l'hai installato."
- **Trovato**: "Trovato. L'app riconoscera' cosa hai ripreso."
- **Trovato, ma senza catalogo**: "Trovato. Gli manca ancora il catalogo stellare: finche' non
  c'e', non riconosce niente." Oggi e' verde come il caso buono: non lo e', va distinto.

**Prima di tutto: le risposte ritrovate.** Se l'app trova un salvataggio di prima, al posto del
primo avvio mostra una schermata sola: "Ho trovato le tue risposte", quando sono state salvate,
quante sono ("412 risposte, 2 siti, 3 cartelle, 5 pezzi e filtri scritti da te"), e due bottoni:
"Rimettile" e "Ricomincia da capo". Va disegnata insieme: e' la stessa colonna senza telaio.

**Mentre l'app si apre**: "un momento...".

## 4. Come si esce

- "Salta per ora" (da ogni passo) e "Fatto" (all'ultimo) fanno la stessa cosa: chiudono il primo
  avvio e aprono l'app.
- Se c'e' almeno una cartella, **la lettura parte da sola**.
- **Non c'e' una schermata di chiusura.** Oggi si passa di colpo all'app. Se ne serve una, dice
  solo cio' che e' vero: cosa hai dato e che la lettura e' partita (o che non c'erano cartelle).

## 5. Telefono

Oggi non c'e' niente di pensato: la colonna si stringe e basta. Da disegnare a 390:
- i gesti in fondo alla carta ("Salta per ora", "Indietro", "Avanti") con bersagli da 44;
- latitudine e longitudine, che oggi stanno affiancate;
- la **scala di Bortle a nove voci** in 390 px;
- l'elenco delle cartelle da sfogliare, col percorso a briciole che puo' essere lungo;
- il binario dei passi con cinque tappe.

## 6. Cose aperte

- **Non esistono, e non vanno disegnati**: la scelta del software di acquisizione (l'app lo legge
  dai file), il fuso, l'altitudine, la lingua, il tema. Il bottone "Cercalo tu" del riconoscitore
  c'e' nelle Impostazioni e non qui.
- **Il primo avvio non si riapre**: una volta chiuso, quelle cose si cambiano nelle Impostazioni.
  Non disegnare un "rifai il primo avvio".
- **Nomi gia' usati dall'app** (per non ripetere `.as-campo` e `.as-elenco`): il campo dei moduli
  nell'app e' `as-campo-modulo` con `as-campo__etichetta`, `__input`, `__aiuto`, `__errore`,
  `--errore`, `--caricamento`; la lista e' `as-elenco`. Puoi rinominarli: dimmi i nomi nuovi.
- **Classi che il primo avvio scrive oggi e il foglio non ha** (servono i mattoni):
  `as-colonna`, `as-testata` (`__titolo`, `__sotto`), `as-entra` (`--alone`), `as-pagina__azioni`;
  `as-passi` (`__tappa`, `__tappa--fatto`, `__segno`, `__nome`);
  `as-carta__corpo` (`--colonna`, `--stretto`), `as-carta--alta`, `as-carta__titolo`,
  `as-carta__domanda`, `as-carta__azioni`, `as-carta__piede`;
  il campo dei moduli (sopra) e `as-scelta`;
  `as-stato--attesa`, `as-stato--buono`, `as-stato--conteggio`;
  `as-percorso` (`__qui`, `__separa`);
  `as-bortle` (`__scala`, `__voce`, `__voce--1`...`--9`, `__fascia`, `__estremi`);
  `as-cerca__niente`.
- **Misure che mancano nel foglio**: la larghezza della colonna, l'altezza dell'elenco delle
  cartelle, la larghezza di un campo di coordinata.
- **Il campo dei moduli serve anche a Impostazioni e Da confermare**: disegnalo come mattone, non
  come pezzo di questa pagina.
