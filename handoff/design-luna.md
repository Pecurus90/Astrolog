# Brief per Claude Design -- la Luna: la striscia in barra e il pannello

Quinta richiesta, dopo il design system, l'Archivio, il primo avvio e Impostazioni. Valgono ancora
[`design-brief.md`](design-brief.md) e il modo di consegnare concordato: **le schermate montate**,
in HTML vero che carica il vostro foglio, piu' `astrolog.css` intero se dovete toccarlo.

Il v8 e' portato e collaudato: le righe degli elenchi sono affiancate come il vostro mockup le
disegna, e la contraddizione fra `--avvio-largo` e la soglia della riga e' chiusa. Grazie.

## 1. Perche' adesso

Il backend ha imparato a dire **che luna fa stanotte**: fase, quanto e' illuminata, quando sorge e
quando tramonta, dal sito da cui si osserva. Finche' non lo sapeva, il piede della barra laterale
non poteva esistere; adesso puo'.

Nel nostro contratto di navigazione il piede e' deciso da tempo: **da dove osservi, e cosa fa il
cielo**. Prima il sito col suo cielo, sotto la Luna, e la Luna **si apre** su un pannello con gli
orari e il grafico grande. E' quel pannello che vi chiediamo.

## 2. Due superfici, e una sola ve la chiediamo davvero

**(a) La striscia in barra -- la montiamo noi.** I mattoni ci sono gia' tutti: `.as-bortle-letta`
per la classe di cielo, `.as-luna__disco` e `.as-luna__illuminata` per il disco della fase,
`.as-lato__coda` per il piede. Per il graficino avete perfino previsto la misura:
`--grafico-basso: 40px`, col commento *"sparkline dentro una card o una riga"*, e la sua forma
`.as-grafico__tela--bassa`. Lo spazio utile in barra e' **227px** (`--barra-laterale` 252, meno
12+12 di imbottitura e il filo del bordo, con `box-sizing: border-box`).

Quello che vorremmo metterci:

```
STANOTTE
Vicenza
Bortle 4 (20,8)

(disco)  Gibbosa crescente 60%
         sale a 16 gradi

|        ___                |    <- la curva dell'altezza (.as-grafico__luna)
|    ___/   \___     |      |    <- la riga di adesso (.as-grafico__adesso)
|___/___________\____|______|    <- l'orizzonte (.as-grafico__orizzonte)
 sorge 15:49 - tramonta 23:48
```

Non vi blocchiamo su questa: la costruiamo coi vostri mattoni e la vestiamo dopo. **Ma se ce la
disegnate, la usiamo** -- e se come la descriviamo contraddice una vostra regola sui grafici,
ditecelo, perche' il grafico grande del pannello deve essere **l'ingrandimento di questa
striscia**, non un disegno diverso.

Una cosa la proponiamo noi, ma **dipende dalla vostra risposta al punto 4**: a 40px di altezza la
striscia ci sembra vada **senza assi e senza etichette**. Se si disegna l'arco intero, un grado
vale 0,46 pixel e qualunque scritta e' una macchia; se invece tagliate all'orizzonte ne vale 1,3, e
allora forse una tacca ci sta. Decidete voi le due cose insieme, perche' sono la stessa cosa.
In tutti e due i casi chi usa un lettore di schermo non perde niente: la frase e gli orari sono
scritti accanto, e il disegno si nasconde.

**(b) Il pannello -- questo e' il lavoro.** Si apre dalla riga della Luna. Dentro:

- il **disco grande** con la fase scritta e la percentuale;
- **tre orari**, non due: sorge, tramonta, e **quando e' piu' alta** (con quanti gradi). Non
  chiamatelo "culmina": vedi il caso brutto in fondo al punto 6, perche' una notte su quindici
  quella parola sarebbe falsa;
- **il grafico grande**: l'altezza della Luna lungo la notte, la riga di adesso, l'orizzonte;
- sotto, **gli stessi numeri come tabella** (`.as-grafico__dati`), chiusa di suo: e' una vostra
  regola, la rispettiamo.

## 3. I dati veri

Non sono esempi inventati: sono due notti vere a Vicenza, e ogni numero qui sotto **esce dalla
rotta**. Le mandiamo tutte e due perche' sono **i due casi opposti**, e un disegno che regge l'una
e non l'altra e' un disegno a meta'.

| | notte del 19 set 2026 | notte del 27 set 2026 |
|---|---|---|
| fase | gibbosa crescente | gibbosa calante |
| illuminata | 60% | 98% |
| sorge | 15:49 | 19:03 |
| tramonta | 23:48 | 09:11 **del giorno dopo** |
| piu' alta | 19:48, a **16,1 gradi** | 02:03, a **56,1 gradi** |

La prima e' la notte buona: la Luna se ne va prima di mezzanotte e resta bassa. La seconda e' la
notte rovinata: sorge quando fa buio, sale alta e non se ne va piu'. **Chi guarda la barra sta
facendo esattamente questa domanda** -- *stanotte mi rovina le pose?* -- e la risposta dev'essere
leggibile senza aprire niente.

### 3.1 Cosa la rotta manda

Tutto cio' che vi serve **c'e' gia'**: fase e quanto e' illuminata, sorgere e tramontare, il punto
piu' alto della notte (quando, e a quanti gradi) e la curva dell'altezza.

La curva arriva come **97 punti** per una notte intera, uno ogni quindici minuti, ognuno un
istante e un'altezza in gradi. L'altezza e' **negativa sotto l'orizzonte** e non e' tagliata a
zero: e' quello che vi permette di disegnare dove la Luna entra ed esce, invece di una curva che
si appoggia al bordo. Il primo e l'ultimo punto sono i due estremi della notte.

Il quindici e' una decisione nostra: dentro campioniamo ogni tre minuti, ma mandarne 481 sarebbe
cinque volte tanti per una differenza che a schermo non si vede. Cosi' la risposta pesa 5,5 KB. Se
per il grafico grande vi serve piu' fitto, ditelo -- e' un numero, si cambia.

La notte dura ventiquattro ore da mezzogiorno a mezzogiorno nel fuso del sito -- tranne le due
notti all'anno del cambio d'ora, che ne durano 23 e 25: il numero di punti cambia, il disegno no.

## 4. La domanda vera, e ha un numero dentro

**Che intervallo di altezza si disegna?** La curva vera della notte del 19 va da **-71,4 gradi** a
**+16,1**. Disegnandola tutta, la parte che interessa -- quella sopra l'orizzonte -- e' una scheggia
in cima: **l'82% dell'altezza del grafico sta sottoterra**.

Tre strade, e la scelta e' vostra:

- si taglia all'orizzonte e sotto si mostra solo un dito di terreno (diciamo fino a -10 o -15
  gradi), cosi' si vede **quando** entra ed esce;
- la scala si adatta alla notte, dal minimo al massimo veri;
- la scala e' fissa da -20 a +90, uguale tutte le notti, cosi' due notti si confrontano a occhio.

Hanno conseguenze diverse e le sapete meglio di noi: la prima e' leggibile, la terza e'
confrontabile. Ci interessa che la **striscia da 40px e il grafico grande usino la stessa**, o
l'ingrandimento sarebbe un altro disegno.

## 5. Il disco della fase -- cosa facciamo noi

Il tracciato della parte illuminata lo **calcoliamo**: e' un semicerchio piu' un arco la cui
larghezza viene dalla percentuale. Voi disegnate il contenitore (misura, bordo, come sta accanto
al testo), noi ci mettiamo dentro la forma giusta.

Due cose che gestiamo noi e che vi diciamo solo perche' non ve ne preoccupiate:

- **da quale lato e' illuminata dipende dall'emisfero.** Una crescente e' illuminata a destra da
  noi e a sinistra in Australia. Nei mockup disegnatela pure all'italiana;
- **la riga di adesso si muove da sola**, ricalcolata in casa ogni minuto senza chiedere niente al
  server.

## 6. I casi brutti, che sono meta' del lavoro

- **nessun sito**: chi ha saltato il primo avvio non ha detto da dove osserva. Il blocco non
  sparisce: **dice cosa manca**, ed e' lo stato di chiunque apra l'app la prima volta. Ma
  disegnatelo **senza collegamento**: il posto dove si ripara e' Impostazioni, *I tuoi siti* --
  che voi avete gia' disegnato e noi non abbiamo ancora montato. La nostra regola vieta i rimandi
  a pagine che non esistono (e' la stessa che ci diamo a fondo pagina), quindi il collegamento lo
  accendiamo noi il giorno che la pagina c'e';
- **la Luna non sorge, o non tramonta, in questa notte.** Non e' solo il circolo polare: la Luna
  torna ogni giorno cinquanta minuti piu' tardi, e un paio di notti al mese uno dei due
  attraversamenti cade fuori dalla finestra (misurato a Vicenza: due notti su trenta). Li' si
  scrive **"non tramonta stanotte"**, mai un trattino e mai un'ora finta;
- **il tramonto prima del sorgere**: per meta' mese e' cosi' (misurato: tredici notti su trenta),
  ed e' giusto -- e' la Luna di ieri che cala prima che sorga quella di stanotte. Un disegno che
  dia per scontato l'ordine sorge-poi-tramonta si rompe meta' del mese;
- **luna nuova**: il disco e' tutto spento e la percentuale e' 0. Non e' un dato mancante, e non
  deve sembrarlo;
- **il pannello aperto a mezzogiorno**: la notte cambia, i numeri scadono e l'app li richiede;
- **il punto piu' alto che cade sul bordo della notte.** La Luna torna ogni giorno cinquanta
  minuti piu' tardi, quindi ogni tanto dentro la finestra della notte **non culmina affatto**: o
  sta ancora salendo quando la notte finisce, o stava gia' scendendo quando e' cominciata. In tutti
  e due i casi il massimo e' un estremo, cioe' **mezzogiorno** -- di domani nel primo caso, di oggi
  nel secondo. Misurato a Vicenza su due anni interi: **48 notti su 730**, una su quindici. Per
  questo l'orario si chiama *"quando e' piu' alta"* e non *"culmina"* -- e per questo l'etichetta
  deve reggere un orario che cade in pieno giorno senza sembrare un guasto.

## 7. Cosa NON disegnare

- **Le fasce del crepuscolo.** Il vostro foglio le ha tutte e cinque (`.as-fascia--giorno`,
  `--civile`, `--nautico`, `--astronomico`, `--notte`) e sarebbero perfette dietro questa curva.
  **Ma il Sole non ce l'abbiamo ancora**: sta nel vecchio progetto e arrivera' con la sua fetta.
  Disegnarle adesso vorrebbe dire consegnare un pannello che non possiamo montare. Lasciate lo
  spazio perche' ci entrino dopo, dietro alla curva, senza toccarla.
- **Il meteo**, per la stessa ragione: non e' un'effemeride, dipende da un servizio, e quel
  dominio non esiste.
- **Quanto sara' buona la notte.** L'app dice cosa fa la Luna; se la notte valga la pena lo decide
  chi osserva. Niente voti, niente semafori, niente "condizioni: discrete".
- **La riga del buio nel piede.** Stessa storia del Sole: due righe vere sono meglio di tre con
  una finta.

## 8. Dove si apre, e quanto e' grande

Il pannello si apre dalla barra laterale, che e' larga 252px e sta a sinistra: il pannello **non
ci sta dentro**, deve aprirsi sopra la pagina. Nel vostro foglio esistono gia' le forme per
farlo -- scegliete voi quale e' la giusta, e diteci perche'.

Il pannello si apre comunque a larghezza di telefono: il mobile lo costruiremo dopo, ma nasce
sapendo dove si piega.

**E qui c'e' una domanda per voi, perche' il vostro foglio e il nostro contratto non dicono la
stessa cosa.** Non e' un rilievo sul disegno: e' che dobbiamo sapere quale delle due vale prima di
disegnare dove vive la Luna su un telefono.

Il nostro contratto di navigazione dice: *"su telefono la barra si ritira dietro un pulsante, e le
voci restano tutte"*.

Il foglio v8 fa un'altra cosa. Sotto `--soglia-guscio` (900px):

- `.as-lato` diventa `flex-direction: row` con `overflow-x: auto` -- cioe' **una striscia
  orizzontale che scorre**, con tutte le voci in fila e nessun pulsante di mezzo;
- `.as-lato__coda { margin: 0 }` porta **il piede dentro quella riga**, in coda alle voci;
- e insieme compare `.as-alto__menu { display: inline-flex }`, un pulsante menu che nel foglio
  **non apre niente**: non c'e' nessuna regola per un pannello, un cassetto o uno stato aperto.

Per noi cambia tutto proprio qui: il blocco STANOTTE che vi abbiamo disegnato al punto 2 e' alto
quattro righe piu' un grafico, e **in una riga orizzontale che scorre non ci sta**. Se vale il
foglio, la Luna su telefono deve andare da qualche altra parte, e quel posto va disegnato.

Quindi: **quale delle due e' la verita'?** Se vale il contratto, serve la forma aperta della barra
(il cassetto) che il foglio non ha ancora, e il pulsante menu trova cosa aprire. Se vale il foglio,
diteci dove mettiamo il blocco STANOTTE sotto i 900px -- e allora il pulsante menu, che oggi non
apre niente, e' un pezzo da togliere o da riempire.

## 9. Le regole non negoziabili (le vostre stesse)

- **Il colore da solo non dice mai niente** -- WCAG 2.2, 1.4.1. La curva della Luna e' gia'
  tratteggiata nel vostro foglio, e la legenda e' scritta.
- **Una cosa che non si sa si legge lo stesso**, e dice *cosa* non sa.
- **Ogni grafico ha il suo dato come tabella**, raggiungibile da tastiera.
- **Niente promesse che l'app non mantiene**: nessun rimando a una pagina che non esiste.
- **Tre bersagli**: Windows, Mac, NAS in Docker -- e sul NAS si apre da tablet.
