# Brief per Claude Design -- Impostazioni

Quarta richiesta, dopo il design system, l'Archivio e il primo avvio. Valgono ancora
[`design-brief.md`](design-brief.md) e il modo di consegnare concordato: **le schermate montate**,
in HTML vero che carica il vostro foglio, piu' `astrolog.css` intero se dovete toccarlo.

Il primo avvio e' portato **intero** e collaudato dal vivo, scala di Bortle compresa. La
contraddizione che vi avevamo segnalato l'avete sciolta col v8: la nota qui sotto resta come
storia della domanda e della risposta.

## 0. Una contraddizione dentro `primo-avvio-v2.html` -- **risposto, e chiusa**

**Il v8 ha sciolto questa**: vale il mockup, la riga ha la sua soglia (`--soglia-riga` 420px)
staccata da quella della tabella, e nell'app le righe sono affiancate. Quello che segue resta
scritto perche' e' la domanda che vi avevamo mandato e la vostra risposta: **non ridisegnate
niente con le righe incolonnate.**

**Le righe degli elenchi del primo avvio, nel browser, non si vedono come il vostro mockup le
disegna.** Nel vostro HTML ogni cartella e' `as-riga__testa` a sinistra e `as-riga__risposte` a
destra, affiancate. Aperta in un browser contro il vostro stesso foglio, l'azione scende **sotto**
il nome, su due righe.

La causa e' nel foglio, non nel montaggio:

- `.as-carta__corpo` dichiara `container-type: inline-size; container-name: colonna`;
- `@container colonna (max-width: 720px)` porta `.as-riga` a una colonna sola;
- la carta del primo avvio e' larga `--avvio-largo`, cioe' **680px**.

Quindi **ogni** riga dentro una carta del primo avvio sta sotto la soglia per costruzione, e la
forma affiancata che il mockup mostra li' non e' raggiungibile. Non e' un caso di bordo: sono i
vostri due numeri, 680 e 720, che si contraddicono.

Noi il foglio non lo tocchiamo -- si porta alla lettera, e una vostra versione nuova
cancellerebbe le nostre modifiche -- quindi l'app oggi mostra quelle righe **incolonnate**, che e'
cio' che il foglio dice. Scegliete voi quale delle due e' la verita' e mandatecela: se vale il
mockup, la soglia o il tetto della colonna vanno cambiati; se vale il foglio, e' il mockup che va
ridisegnato con le righe incolonnate, cosi' chi lo guarda sa cosa vedra'.

**Risposto col v8: vale il mockup.** Niente di quanto sopra e' ancora da fare.

---

## 1. Perche' questa pagina, e perche' adesso

Impostazioni e' la prima pagina che vi chiediamo **i cui dati esistono gia' tutti**: le rotte
rispondono oggi, quindi appena la consegna arriva si porta e funziona. E chiude tre buchi che
l'app ha dichiarati:

- **dove sta ASTAP si puo' scrivere solo nel primo avvio.** Chi lo salta, o lo installa dopo, non
  ha nessun posto dove dirlo;
- **l'Archivio vuoto dice "indica le cartelle"**, ma le cartelle si indicano solo dal primo avvio:
  la frase diventa vera quando nasce questa pagina;
- **il cielo del proprio sito non si corregge**: si sceglie al primo avvio e poi resta li'.

## 2. La forma: una pagina, le sue sezioni

Non e' una voce di barra per ogni cosa: e' **una pagina sola con le sue sezioni**, e **ogni
sezione ha il suo indirizzo** (`/impostazioni/cartelle`) -- e' cio' che fa funzionare il tasto
indietro e il collegamento che si manda a qualcun altro. Nel foglio la navigazione a sezioni
esiste gia' (`.as-sezioni`, con `aria-current`).

Le sezioni, nell'ordine:

### a) Cartelle -- la piu' densa, ed e' da qui che partiamo
Le cartelle che l'app legge. Per ognuna: **il percorso**, quanti frame ne sono entrati in
archivio, e se al momento si raggiunge o no. Si puo' **aggiungerne una** (scrivendo il percorso
sul computer, sfogliando sul NAS -- come nel primo avvio) e **toglierne una**.

Togliere una cartella **non cancella niente**: i frame gia' letti restano in archivio. Va detto
nella schermata, perche' nessuno lo indovina e la paura di perdere il lavoro blocca il gesto.

Sotto, **le ricevute delle letture**: quando l'app ha letto, quanto ci ha messo, quanti file ha
trovato, e **quali non ha potuto leggere**, col motivo. E' la parte che oggi non ha casa.

### b) Il sito
Il luogo da cui osservi: nome, coordinate, e **che cielo ha** -- la scala di Bortle che avete
disegnato per il primo avvio, qui in versione "si corregge" invece che "si sceglie la prima
volta". Si possono avere **piu' siti**, e uno e' quello di casa.

### c) Il riconoscitore (ASTAP)
Dove sta il programma, e se l'app lo trova. E' la stessa sostanza del quarto passo del primo
avvio, ma qui ci si torna: non e' un passo, e' uno stato che si guarda e si cambia.

### d) Lingua e tema -- **no**
Non stanno qui: vivono nella barra in alto, si cambiano al volo e non sono configurazione. E' una
decisione gia' presa da noi, la scriviamo perche' non le disegniate per simmetria.

## 3. I dati veri

| dato | esempio | quando non sa |
|---|---|---|
| percorso della cartella | `D:\Astro\2024`, `/volume1/foto` | mai |
| frame entrati in archivio | `3.180` | mai (zero e' zero, e si scrive) |
| si raggiunge? | si' / no | mai |
| quando e' stata aggiunta | `16 set 2026` | mai |
| ricevuta di una lettura | quando, quanto e' durata, quanti file | -- |
| file non letti | il percorso e **il motivo** | -- |
| sito | nome, latitudine, longitudine, classe di cielo | il cielo puo' non essere stato dichiarato: **terza forma del dato**, non uno zero |
| ASTAP | il percorso, e se c'e' | il percorso puo' essere vuoto |

**Cosa NON abbiamo, e quindi non disegnate**: quanti file ci sono **su disco** in una cartella
(diverso dai frame in archivio), la data dell'ultima lettura **per cartella**, il numero di
sottocartelle. Se vi servono per il disegno, ditecelo e valutiamo se allargare l'API -- ma non
dateli per scontati.

## 4. I casi brutti, che sono meta' del lavoro

- **nessuna cartella**: e' lo stato di chi ha saltato il primo avvio, e questa pagina e' dove lo
  ripara;
- **una cartella non si raggiunge**: il disco staccato, il NAS spento. Le altre funzionano lo
  stesso, e questa lo dice col suo motivo;
- **una lettura e' andata a meta'**: qualche file non si e' potuto leggere, e si vede quali;
- **nessun sito**: l'app cataloga lo stesso ma non fa le notti, e la pagina lo spiega;
- **ASTAP non c'e'**: non e' un guasto, e' una cosa da fare -- niente allarme.

## 5. Le regole non negoziabili (le vostre stesse)

- **Il colore da solo non dice mai niente** -- WCAG 2.2, 1.4.1.
- **Una cosa che non si sa si legge lo stesso**, e dice *cosa* non sa.
- **Niente promesse che l'app non mantiene**: nessun interruttore che non fa niente.
- **Un gesto che cancella chiede conferma**, e dice cosa succede davvero (togliere una cartella
  non butta via i frame).
- **Tre bersagli**: Windows, Mac, NAS in Docker -- e questa pagina sul NAS si apre da tablet.

## 6. Un'ultima cosa, che ci servirebbe

Nel primo avvio abbiamo trovato **cinque forme che il vostro foglio sa gia' fare** e che noi non
usavamo: l'avviso col titolo, l'avviso che porta i bottoni dentro di se', l'avviso neutro, il
bottone col verso errore, il campo col suo errore sotto. Adesso i nostri componenti le sanno
tutte e cinque, e sono gia' a schermo. Se in questa pagina ne servono altre, **usatele pure**:
e' meglio scoprirlo ora che dopo.
