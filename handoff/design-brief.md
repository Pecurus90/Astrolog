# Brief per Claude Design -- il design system di AstroLog

Documento di **consegna**: chi lo legge non vede il nostro repository, quindi qui c'e' tutto
quello che serve. Chiede **il design system**, non le singole pagine: token, mattoni, e le regole
con cui chi scrive il codice veste dodici pagine senza chiedere un mock ogni volta.

---

## 1. Che cos'e' AstroLog

Un'app **open source** per catalogare, analizzare e pianificare sessioni di **astrofotografia**.
Punti l'app alle cartelle dove tieni i tuoi file FITS; lei legge le intestazioni di ogni frame,
riconosce sul cielo cosa hai ripreso, e ricostruisce la tua cronologia osservativa: quali oggetti,
quante ore, con che attrezzatura, da quale luogo.

Chi la usa e' un astrofotografo, non un tecnico. Puo' avere **quindici anni di archivio** e
centomila file, o **due notti**. Non c'e' nessun login: e' la sua app, sui suoi dati.

**Tre piattaforme, una sola interfaccia web**: Windows, Mac, e NAS in Docker -- e sul NAS la si usa
anche **da tablet e da telefono**. L'ordine di lavoro e' **desktop prima, mobile alla fine**: ma il
desktop si costruisce sapendo che il mobile arriva, quindi la veste deve piegarsi senza essere
ridisegnata.

---

## 2. Cosa vi chiediamo di consegnare

1. **I token**, con i nomi per **ruolo** e non per colore (`--fondo-carta`, non `--grigio-scuro`:
   il nome deve restare vero quando la veste cambia). Colori, spazi, raggi, tipografia, ombre,
   durate. Dichiarati come variabili CSS su `:root`.
2. **I mattoni**, con il loro HTML e il loro CSS: carta/sezione, riga di elenco, tabella di dati,
   bottone (primario, tenue, distruttivo), campo di testo, scelta fra poche opzioni, etichetta di
   stato, avviso, stato vuoto, barra di avanzamento, scheda a comparsa.
3. **Lo scheletro**: barra laterale a gruppi + barra in alto, e come diventano la stessa cosa in
   una colonna stretta.
4. **Le schermate montate** con quei mattoni (la sezione *Le due schermate da montare*: Da
   confermare e Archivio, piu' il primo avvio a mani vuote), come prova che il sistema regge.
5. **Le regole d'uso in prosa corta**: quando si usa una carta e quando una riga, quanto spazio
   fra le cose, come si comporta una tabella lunga, dove va il colore e dove non va.
6. **I grafici come forme**, **le card** e **gli altri mattoni** che le pagine gia' decise useranno
   (le sezioni *I grafici*, *Le card*, *Altri mattoni che serviranno*).

Consegnate **HTML + CSS puro** (niente framework, niente librerie di componenti), e i grafici come
**SVG statico**: chi scrive il codice porta quel CSS in React/TypeScript. Non serve che scriviate
React, e la pagina di esempio deve **aprirsi senza internet**.

---

## 3. Le pagine dell'app (dodici, in tre gruppi)

La barra laterale e' gia' decisa, gruppi e ordine compresi. In **corsivo** quelle che non esistono
ancora: il sistema deve reggerle lo stesso.

- **Casa** -- il riepilogo: quante cose aspettano una risposta, lo stato dell'archivio.
- **Guarda**: **Archivio** (gli oggetti ripresi), *Notti*, *Attrezzatura*, *Statistiche*.
- **Sistema**: **Da confermare**, *Diagnostica*.
- **Pianifica**: *Planner*, *Progetti*, *Carta del cielo*, *Meteo*.
- **Impostazioni**, staccata in fondo: una pagina con dentro sezioni (cartelle, siti, servizi).

In alto, sempre: il nome della pagina, il **pulsante che avvia la lettura dell'archivio** con lo
stato di quello che sta facendo, e -- quando esisteranno -- il luogo attivo, la lingua, il tema.

**Oggi esistono davvero quattro superfici**: la Casa, il **primo avvio** (tre domande, piu' una
quarta a chi manca il riconoscitore di cielo), **Da confermare** e l'**Archivio**. Le altre otto
arrivano dopo, e sono la
ragione per cui vogliamo un sistema e non dei mock.

---

## 4. Le due schermate da montare

### a) Da confermare -- la piu' densa, e la piu' importante

L'app non inventa: quando **non e' sicura**, chiede. Questa pagina e' fatta di sezioni, ognuna con
una domanda diversa, e sotto un elenco di casi da risolvere. Le sezioni sono **undici**, in
quest'ordine e con questi nomi a schermo: Strumenti, Filtri, Corredi, Frame senza filtro, Quale
filtro notte per notte, Frame senza camera, Frame senza tipo, Frame senza sito, Mosaici proposti, Frame senza nome, Oggetti. *Frame senza tipo* e' nata il 17/9/2026, dopo
la vostra consegna: ha la stessa forma di *Frame senza nome* (una riga per cartella, due risposte)
e non chiede nessun mattone nuovo.

Dentro una sezione, ogni riga ha: **il nome trovato nei file**, quanti frame lo portano, cosa ne
pensa l'app, e le risposte possibili. Esempi di testo vero dall'app (usateli, non inventate):

> **Strumenti**: "manca: focale, diametro" | "somiglia a TS-Optics 80/480" | "Uniscila a
> TS-Optics 80/480" | "Completa la scheda"
>
> **Oggetti**: "M 31 -- nell'inquadratura" | "NGC 206 -- solo li' accanto" | "non si sa se cadeva
> dentro" | "12,5 h" | "3 senza tempo" | "Non e' questo: lo correggo"
>
> **Filtri**: "Cerca fra i modelli per Ha" | "Non e' in elenco: lo aggiungo io" | "Banda"

Vincoli di questa pagina: le domande sono **paragrafi veri**, non etichette; le risposte date si
accumulano e si confermano **tutte insieme** con un solo pulsante in fondo; e ogni riga deve
lasciare vedere **perche'** l'app chiede.

### b) Archivio -- la pagina di lettura, fatta di righe uguali

Molte righe, quattro o cinque colonne: oggetto, quanti frame, quante ore, ultima notte. Deve
reggere **mille righe** senza diventare faticosa, e deve restare leggibile quando una cella
**non sa** (la prima delle regole non negoziabili). E' il caso opposto alla precedente: li'
prosa, qui tabella.

---

## 5. Le regole non negoziabili

1. **Le tre forme del dato.** Ogni cella puo' essere **piena**, **vuota** o **"non lo so"**, e la
   terza non e' uno zero: l'app non finge mai. "0 ore" e "non so quante ore" devono essere
   distinguibili a colpo d'occhio, e la cella muta porta **il suo perche'** accanto. Serve un
   trattamento visivo apposta.
2. **A mani vuote si regge.** Primo avvio, zero file, nessuna configurazione: l'app deve essere
   bella e comprensibile anche cosi'. Lo stato vuoto e' una schermata di prima classe, non un
   ripiego.
3. **Il colore da solo non dice niente.** Nessuno stato si distingue col **solo** colore: ci
   vogliono parola, forma o posizione. Non e' una preferenza -- WCAG 2.2, criterio 1.4.1
   *Use of Color*, **livello A**: *"Color is not used as the only visual means of conveying
   information, indicating an action, prompting a response, or distinguishing a visual
   element"*. Chi non distingue verde e rosso deve capire lo stesso se un frame e' a posto o
   aspetta.
4. **Le cifre incolonnate.** L'app e' fatta di conteggi (ore, frame, notti). Ovunque compaia un
   numero servono cifre a larghezza fissa, o le colonne non si leggono in verticale.
5. **Accessibilita' vera, verificata da una macchina.** Contrasto sufficiente, ogni elemento
   azionabile raggiungibile da tastiera e con un nome, il fuoco sempre visibile. Nei nostri
   controlli gira axe: una veste che non passa non entra.
6. **La misura e' la colonna, non la finestra.** Con la barra laterale aperta, la colonna del
   contenuto puo' essere stretta come un telefono mentre la finestra e' larga. Il punto in cui il
   layout cambia va deciso **sul contenitore** (container query), non sulla larghezza dello
   schermo.
7. **Il layout non porta logica.** La larghezza decide **come** si dispongono le cose, mai **cosa**
   c'e' dentro. Un controllo si sceglie per la natura delle voci (elenco a comparsa se vengono
   dall'archivio, segmentato solo per voci poche e fisse), non per lo schermo.
8. **Le parole sono decise e non si toccano.** L'app parla italiano (l'inglese esiste, le altre
   lingue arriveranno) e ha un glossario: *frame*, *notte*, *sito*, *corredo*, *Da confermare*.
   Le parole vietate contano quanto quelle ammesse: il file ripreso e' un **frame**, mai
   "posa", "scatto", "sub" o "esposizione"; e nessun gergo tecnico a schermo -- mai "plate
   solver", mai "pipeline".
9. **Niente dipendenze nuove.** Niente Tailwind, niente librerie di componenti, niente font da
   scaricare se una famiglia di sistema fa lo stesso lavoro: l'app gira anche su un NAS senza
   internet.

---

## 6. La direzione che ci piace (non un vincolo, un punto di partenza)

Abbiamo confrontato tre direzioni su contenuti veri:

1. **macOS/iOS con colori astro** -- superfici a livelli, angoli morbidi, traslucidita' con misura,
   gerarchia fatta di spazio, fondo notturno, accenti dal cielo (blu profondo/indaco).
2. **Sala di controllo** -- densa e tabellare, bordi netti, colore solo per lo stato, accento ambra.
3. **Diario del cielo** -- editoriale, molto scuro, titoli con personalita', contenuto in primo
   piano.

La preferenza e' la **1**, con **un po' della densita' della 2**: la 2 da sola strozza le domande
lunghe di *Da confermare*, la 3 raddoppia l'altezza delle mille righe dell'Archivio. Il tema e'
**scuro di partenza** -- si guardano foto del cielo notturno -- ma il sistema deve prevedere anche
il chiaro, perche' l'app si usa anche di giorno per pianificare.

Se pensate che una direzione diversa serva meglio queste due schermate, **ditelo con il perche'**:
la preferenza e' un punto di partenza, non un ordine.

---

## 7. Come lo useremo (e perche' certe cose contano)

Il codice e' React + TypeScript. Il CSS avra' **tre case, e nessun'altra**: il foglio dei **token**,
il foglio dei **mattoni condivisi**, e -- solo se serve -- un foglio per quella pagina, con il suo
prefisso, che non ridichiara niente. Quindi:

- i vostri token devono bastare da soli: se un mattone ha bisogno di un valore scritto a mano, quel
  valore e' un token che manca;
- i mattoni devono agganciarsi a **HTML semplice e semantico** (`nav`, `header`, `main`, `section`,
  `ul`/`li`, `button`, `table`), perche' le pagine sono gia' scritte cosi' e vestirle non deve
  chiedere di riscriverle;
- ogni mattone va consegnato con i suoi **stati**: normale, sopra cui passa il mouse, premuto,
  disabilitato, col fuoco da tastiera, in errore, in caricamento.

Se una cosa che chiediamo vi sembra sbagliata, scrivetelo: preferiamo una discussione adesso a una
veste che dobbiamo piegare dopo.

---

## 8. I grafici -- le forme, non i singoli grafici

Non chiediamo un grafico per pagina: chiediamo le **forme** come mattoni, ognuna con i suoi token
(assi, griglia, serie, evidenziazione, soglia, fasce), i suoi stati (caricamento, vuoto, "non so",
errore) e un esempio disegnato in **SVG statico**. Il codice li ricostruira' a partire da li'.

In ordine di priorita' (le prime servono subito alla Casa e alle pagine di lettura):

1. **Heatmap mese per anno** -- quante notti in ogni mese di ogni anno. Le celle hanno **tre stati**
   che si distinguono anche senza colore: *con notti* (pochi livelli, con legenda), *zero vero*
   (un mese in cui non hai osservato), *fuori dall'arco* (prima della tua prima notte o dopo oggi,
   tratteggiata). Un mese senza notti, toccato o col fuoco, **dice perche'**.
2. **Barre verticali nel tempo** -- ore per mese, o ore per notte. Il mese in corso si distingue
   anche per forma, non solo per colore; un mese senza dati dice perche' invece di mostrare zero.
3. **Barra impilata per filtro, con legenda** -- come sono divise le ore fra i filtri, dentro una
   card o una riga. Usa i token dei filtri, e la **sigla del filtro e' sempre scritta**.
4. **Anello per filtro** -- la stessa informazione in una scheda di dettaglio, col totale al centro.
5. **Linea nel tempo** -- l'andamento di una misura: punti con una **banda dei quartili**, una
   mediana mobile, l'asse sul **giorno dell'anno**, un anno di confronto distinto per colore **e**
   per forma del punto.
6. **Cumulato anno su anno** -- le ore accumulate, una linea per anno, ferma a oggi.
7. **Curva di altezza nella notte** -- quanto sale un oggetto sopra l'orizzonte, dal tramonto
   all'alba: le **cinque fasce del crepuscolo**, una soglia di altezza, l'orizzonte vero del sito,
   la traccia della Luna e il segno di **adesso**.
8. **Striscia della notte** -- le fasce dal tramonto all'alba con gli orari, in piccolo: sta in una
   riga di elenco.
9. **Sparkline** -- una linea o un'area senza assi, dentro una card o una riga.
10. **Nuvola di punti** -- un frame, un punto: due misure a confronto, con una tendenza per filtro.
11. **Piccoli multipli** -- la stessa forma ripetuta su una griglia con la **stessa scala**.
12. **Disco della Luna** -- la fase, col terminatore.
13. **Sagoma dell'orizzonte del sito** -- l'orizzonte vero intorno a un sito, per le Impostazioni.

Per le pagine che arriveranno piu' avanti (meteo): le **aree degli strati di nuvole ora per ora**
sopra le fasce della notte, e un **istogramma orario** con evidenziazione incrociata fra piu'
misure. Sono in fondo alla lista perche' quel dominio non esiste ancora.

### Le regole dei grafici

- **Il colore da solo non dice niente** (WCAG 2.2, 1.4.1): ogni serie ha etichetta, forma o
  tratteggio, e la legenda e' scritta.
- **Mai uno zero di ripiego**: un dato che non si sa e' un vuoto dichiarato (tratteggio e
  perche'), non una barra a zero.
- **Niente calendario per giorno e niente "streak"**: la griglia e' per mese.
- **L'arco dell'archivio** va dalla prima notte a oggi, oppure all'ultima notte se viene dopo.
- **Nessun voto** a notti o a frame, e **nessuna classifica** assoluta ("i migliori stanotte").
- **Qualita' e meteo non si correlano**: nessun grafico li mette sullo stesso asse.
- **Le parole**: la larghezza delle stelle a schermo e' **HFD**, non FWHM; le durate si scrivono in
  ore e minuti.
- **Ogni grafico e' leggibile senza vederlo**: un titolo, una frase che dice cosa mostra, e il dato
  raggiungibile anche come testo o tabella. Il suggerimento che compare sopra un punto si apre
  anche da tastiera e col tocco, non solo col mouse.
- Cifre tabulari sugli assi, tema chiaro e scuro, e **colonna stretta**: come si piega un grafico
  quando la colonna e' larga come un telefono.

## 9. Le card

Le card che le pagine piazzeranno (la Casa per prima), ognuna con gli stati **caricamento, vuoto,
"non so", errore**:

- **Numero grande** -- un valore con la sua unita', una riga sotto che lo spiega, e opzionalmente
  la **variazione sull'anno prima**, detta con segno e parola e non solo col colore.
- **Numero grande con mini-grafico** -- lo stesso, con una sparkline o una barra per filtro.
- **Elenco breve** -- per esempio l'ultima notte: tre o quattro numeri (ore, frame, HFD, corredo)
  e gli oggetti con le pastiglie dei filtri.
- **Card di un oggetto** -- nome, filtri, ore, frame. L'**anteprima e' prevista ma oggi non c'e'**:
  quando arrivera' sara' la foto finale dell'utente o il suo frame migliore, mai un'immagine di
  terzi. La card deve reggere **senza immagine** e accoglierla dopo senza essere ridisegnata.
- **Card di una notte** -- data, sito, Luna, oggetti con le pastiglie, HFD.
- **Riga con barra di avanzamento** -- quanto manca a un obiettivo, per filtro (per i Progetti).

## 10. Altri mattoni che serviranno

Pezzi che le pagine gia' decise useranno, e che conviene avere studiati adesso invece che
inventati pagina per pagina:

- **Barra di un elenco**: ricerca, un elenco a comparsa, un segmentato e l'ordinamento per colonna
  -- l'Archivio ne ha bisogno per primo. Il controllo si sceglie per la natura delle voci, non per
  lo schermo: elenco a comparsa se vengono dall'archivio, segmentato solo per voci poche e fisse.
- **Campo di ricerca con suggerimenti**: la ricerca di un sito per nome, di un modello di filtro.
- **Schede (tab)** dentro una pagina, e la **navigazione a sezioni** delle Impostazioni, dove ogni
  sezione ha il suo indirizzo.
- **Scheda di dettaglio** di un oggetto o di una notte: un pannello che si apre sopra la pagina o
  accanto, con la sua testata e le sue sezioni.
- **Testata di dettaglio**, col percorso (*Archivio > M 31*).
- **Selettore di periodo**: un anno, un intervallo.
- **Suggerimento (tooltip)** accessibile da tastiera e col tocco.
- **Avviso breve** che compare e sparisce (per esempio "applicate 12 risposte").
- **Dialogo di conferma** per un'azione che non si annulla (per esempio eliminare un sito): dice
  cosa si perde, e il pulsante che conferma dice il verbo, non "OK".
- **Scheletri di caricamento** per card, righe e grafici, della stessa misura del contenuto vero:
  quando i dati arrivano il layout non salta.

Chiediamo tutto questo in un giro solo, ma **consegnate pure a blocchi**: prima le correzioni della
consegna precedente, poi grafici e card nell'ordine di priorita' qui sopra, poi gli altri mattoni.
Un blocco completo vale piu' di tutto a meta'.

---

## 11. Verifica finale (17/9/2026): niente da correggere

La v4 e' **accettata**. Abbiamo verificato ogni giro sui vostri file, non sul riepilogo, e misurato
quello che si misura: contrasto del testo e delle forme con la formula WCAG, spessori e scale dei
grafici, bersagli della heatmap, altezze dei pannelli.

Cosa c'e', in breve: i token per ruolo nei due temi, i mattoni con tutti i loro stati, lo scheletro,
le tre schermate montate (Da confermare con le undici sezioni, Archivio, primo avvio), le regole
d'uso, tredici forme di grafico coi quattro stati, sei card, e gli altri mattoni del blocco 3
(suggerimento, barra di un elenco, ricerca con suggerimenti, schede, sezioni, testata col percorso,
scheda di dettaglio, selettore di periodo, avviso breve, dialogo di conferma, scheletri).

Le ultime due cose sono chiuse: il `README.md` elenca ora **tutto** cio' che vuole codice (tasti,
fuoco, stato annunciato, tocco, tempo, misure) e dice che col dito il suggerimento oggi si apre solo
dove la guida lo tiene aperto; e l'aria sopra la heatmap e' ricontata -- 84px a larghezza piena,
120px in colonna stretta -- col conto scritto accanto ai token.

Quello che resta e' nostro: portare il foglio nel repository **alla lettera**, e
scrivere le sei cose che il CSS non fa. Se torneremo da voi sara' per una pagina nuova, non per
queste.

Grazie: e' una consegna che si porta senza doverla piegare.
