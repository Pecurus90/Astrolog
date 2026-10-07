# Brief per Claude Design -- la pagina Archivio, in due viste

Seconda richiesta, dopo il design system consegnato il 17/9/2026. Il primo brief e'
[`design-brief.md`](design-brief.md) e **vale ancora tutto**: token, mattoni, regole non
negoziabili. Qui si chiede **una pagina sola**, e le poche classi che le mancano.

Il foglio consegnato e' nel repo **alla lettera** (sotto `frontend/src/stili/`): non lo
tocchiamo, e cinque guardie automatiche ce lo impediscono.
Per questo ogni aggiunta deve arrivare da voi.

---

## 0. Se avete gia' letto questo file: cosa c'e' di nuovo

Questa e' la stessa richiesta di prima, **con la vostra consegna montata dentro**. Le sezioni da 1
a 7 non sono cambiate: servono a chi legge per la prima volta. Le due nuove stanno in fondo, e
sono quelle da leggere.

- **[§8 -- La consegna, portata](#8-la-consegna-portata----tre-correzioni)**: tre cose trovate
  montando `archivio.html` sulla pagina vera. Una sola vi chiede di decidere (le file di pastiglie
  come stili in riga, quando il foglio ha gia' `.as-ore-filtro`); una e' un limite nostro, non
  vostro (i due nomi nel titolo della carta: l'app ne risolve uno); la terza vi da' ragione.
- **[§9 -- La barra, portata](#9-la-barra-portata----quattro-cose-da-guardare)**: quattro cose,
  tre sullo **stato d'attesa** e una sul **campo di ricerca**. Le prime tre sono la stessa storia
  -- i modificatori `--caricamento` che avete dato o spengono cio' che non dovrebbero o non
  dipingono niente -- e la quarta e' un conflitto fra due `max-width` nel foglio, dove vince
  quello che il vostro commento dice di non volere.

**Cosa ci serve indietro**: il foglio `astrolog.css` aggiornato, **intero**, com'e' scritto nella
sezione 2. Noi lo portiamo alla lettera e non lo tocchiamo, quindi una correzione fatta da noi
sparirebbe alla vostra consegna dopo.

---

## 1. Cosa e' cambiato dal primo brief

Il primo brief descriveva l'Archivio come **una tabella e basta** (sezione 4b: *"molte righe,
quattro o cinque colonne... li' prosa, qui tabella"*). Quella descrizione **e' superata**: il
proprietario del prodotto la vuole in **due viste**, con un interruttore, e gli stessi dati in
tutte e due.

Il resto del foglio ha retto benissimo la prova: abbiamo gia' vestito con i vostri mattoni il
guscio, la Casa e *Da confermare* (dodici sezioni), e non abbiamo dovuto inventare niente.

## 2. Cosa vi chiediamo

**La pagina Archivio montata**: un file HTML statico, con dati d'esempio dentro, che usa **le
classi del vostro foglio** -- quello che gia' abbiamo -- e lo carica com'e'. Non un'immagine,
non un mockup da guardare: il markup vero, che noi trasformiamo in componenti React senza
ridisegnare niente. Se per montarla vi servono classi che nel foglio non ci sono, le
**aggiungete al foglio** e ce lo riconsegnate intero (vedi in fondo a questa sezione).

La pagina ha **due viste** che si scambiano con un interruttore:

- **Vista elenco** -- il caso "confronto": chi ha piu' ore, cosa non riprendo da un anno.
  Colonne allineate, deve reggere **mille righe** senza stancare. I mattoni ci sono gia'
  (`.as-tabella` e la sua trasformazione in elenco sotto i 720px): se bastano, ditecelo e non
  aggiungete niente.
- **Vista carte** -- il caso "guardo cosa ho": una carta per oggetto, con **il posto per
  l'anteprima dell'immagine**. Il pozzo esiste gia' nel vostro foglio (`.as-carta__anteprima`,
  col commento *"l'anteprima non c'e' ancora: il pozzo la aspetta e tiene il suo posto"*), e
  ora la pagina che lo usa e' nata. **Quello che manca e' la griglia** che dispone le carte:
  il foglio non ha nessuna classe che faccia colonne (nessun `repeat(auto-fill, ...)` in
  tutto il foglio, l'abbiamo cercato). E' l'unica lacuna che questa pagina scopre.
- **L'interruttore fra le due**, se `.as-segmentato` non e' la forma giusta per un cambio di
  vista (li' i bottoni dichiarano `aria-pressed`; qui potrebbe volerci un'icona, o una coppia
  con etichetta).
- **Lo stato vuoto** e **il carico progressivo**: `.as-vuoto` c'e', `.as-carta__piede` c'e';
  manca -- se serve -- la forma del *"stai vedendo 100 di 1.240, mostra altri"*.

**Come consegnare**, due file:

1. **`archivio.html`** -- la pagina montata, statica, con dati d'esempio. Dentro ci vogliono
   **tutti i casi che la realta' produce**, non solo la riga bella: un oggetto senza ultima
   notte, uno senza costellazione ne' tipo, uno con frame che non dicono la loro durata, un
   nome lungo che rischia di traboccare, e le due viste (mostratele tutte e due, anche se per
   vederle servono due file). Piu' l'archivio **vuoto**, che e' lo stato di chi ha appena
   installato l'app.
2. **il foglio intero e aggiornato**, non un frammento da incollare. Lo portiamo alla
   lettera e ne ricalcoliamo l'impronta; un pezzo staccato ci costringerebbe a scrivere dentro
   il foglio, che e' esattamente cio' che non facciamo. Se non avete dovuto aggiungere niente,
   ditelo e non riconsegnatelo.

## 3. I dati veri della pagina

Ogni oggetto porta questo, e nient'altro (`backend/astrolog/api/models_archive.py`).
**Aggiornata il 22/9/2026**, quando la pagina e' stata montata: e' sparita l'**ultima notte**
(Marco: quel posto e' dei progetti) e sono arrivati i **filtri**. Nient'altro e' cambiato.

| dato | esempio | quando non sa |
|---|---|---|
| nome | `M31`, `NGC 7000`, o un nome dato dall'utente | mai |
| frame | `412` | mai |
| ore | `18,5 h` -- somma dei tempi di posa | l'oggetto puo' avere **frame che non dicono quanto sono durati**: si mostrano a parte, non valgono zero |
| filtri | `Lum`, `R`, `G`, `B` -- nell'ordine dei filtri, uno in tutta l'app (L, R, G, B, Ha, OIII, SII, poi a colori, poi gli altri), ognuno con la sua **banda canonica**, che e' cio' che gli da' il colore | vuoto: i file non dicevano il filtro. Niente pastiglie, non una pastiglia grigia |
| costellazione | `And` (sigla IAU a tre lettere, che la pagina scrive col nome latino ufficiale: *Andromeda*) | nulla se l'oggetto non e' di catalogo: si dichiara, non si mette un trattino muto |
| tipo | galassia, nebulosa oscura, ammasso globulare... | come sopra |
| anteprima | **non esiste ancora**: nessun frame ha una miniatura | sempre, per ora: il posto va tenuto, non riempito |

La lista arriva a pezzi da 100 con il totale dichiarato: la pagina sa sempre quanti ne sta
mostrando e quanti ce ne sono.

## 4. I mattoni che abbiamo gia' costruito sui vostri

Questi componenti avvolgono le vostre classi, e da qui in poi ogni pagina passa da loro.
Disegnate **con questi**, non accanto a questi:

| nostro | avvolge | dove |
|---|---|---|
| `Sezione` | `.as-carta` + intestazione + `.as-elenco` | `frontend/src/Sezione.tsx` |
| `Riga` (con `Dettaglio` e `Prova`) | `.as-riga` e i suoi pezzi | `frontend/src/Riga.tsx` |
| `Campo` | `.as-campo` + etichetta | `frontend/src/Campo.tsx` |
| `Bottone` | `.as-bottone` e i suoi tre versi | `frontend/src/Bottone.tsx` |
| `Avviso` | `.as-avviso`, col segno non cromatico dentro | `frontend/src/Avviso.tsx` |

## 5. Le regole non negoziabili (le stesse del primo brief)

- **Il colore da solo non dice mai niente** -- WCAG 2.2, 1.4.1. Ogni stato ha anche una forma.
- **Una cella che non sa si legge lo stesso**, e dice *cosa* non sa. Niente trattini muti.
- **Mille righe senza fatica**, e il primo carico conta: il foglio viaggia gia' per 57,9 kB.
- **Niente modalita' a luce rossa** (decisa e scartata).
- **Tre bersagli**: Windows, Mac, e NAS in Docker -- quest'ultimo si usa anche da tablet e da
  telefono. Il desktop viene prima, ma la forma mobile non deve essere una riscrittura.

## 6. Due lacune che un'altra pagina ha scoperto

Non sono dell'Archivio, ma sono del foglio, e le correggete voi perche' il foglio lo portiamo
alla lettera. Le abbiamo trovate vestendo il **primo avvio**, che e' un modulo: piu' campi uno
sotto l'altro e un bottone in fondo.

- **Il foglio non sa impilare.** Dentro `.as-carta__corpo` i figli non hanno spaziatura fra loro:
  due campi di fila si toccano, e il bottone sotto l'ultimo campo gli sta addosso. Oggi rimediamo
  dando a ogni gruppo il **suo** `.as-carta__corpo`, che il padding ce l'ha -- ma dentro un gruppo
  non c'e' niente. Serve il modo che intendete voi: una utility di pila, un `gap` sul corpo, o
  quello che nel vostro sistema e' giusto.
- **Il binario dei passi non ha un mattone, e il vostro stato non lo raggiunge.** Un primo avvio
  ha delle tappe, e quella dove sei si deve vedere. L'abbiamo montato con `.as-sezioni` (la
  navigazione delle Impostazioni), ma il fondo e la barra li agganciate a
  `[aria-current="true"]`, e per un passo il valore corretto e' `step` -- e' cio' che un lettore
  di schermo annuncia come "passo corrente". Un selettore d'attributo confronta per intero,
  quindi da noi **quella regola non scatta**: la tappa corrente si distingue solo per inchiostro
  e peso, con una classe presa da un altro blocco (`.as-percorso__qui`), che e' proprio cio' che
  il vostro sistema evita. Due strade, scegliete voi: il mattone dei passi, oppure lo stato che
  aggancia `[aria-current]` qualunque sia il suo valore.

## 7. Cosa NON vi chiediamo

- Il resto delle pagine: arrivano una per volta, quando esistono.
- Filtri, ordinamenti e scheda dell'oggetto: sono funzioni non ancora costruite. Se la vostra
  tabella prevede gia' dove va una colonna ordinabile, meglio; non disegnatele.
- Correzioni ai token: se ne trovate una da fare, ditecela e la fate **voi** alla fonte.

## 8. La consegna, portata -- tre correzioni

Montato il 22/9/2026 sulla pagina vera, con dati veri. La griglia, le carte, la tabella,
l'interruttore e il pozzo dell'anteprima hanno retto senza una riga di stile scritta da noi: su
questo non abbiamo rilievi.

1. **Nel vostro `archivio.html` le file di pastiglie sono stili in riga, e il mattone c'era.**
   Sia nelle carte sia nella cella *Filtri* della tabella usate `.as-filtro` dentro un
   `style="display:flex;gap:var(--spazio-2);flex-wrap:wrap"`, mentre il foglio porta gia'
   `.as-ore-filtro` -- una fila di filtri che va a capo -- e la descrive per intero: la variante
   sui `__voce`, la pastiglia di `.as-filtro__pastiglia` dentro, il nome in `__nome`. **Abbiamo
   montato quella**, e lasciato le ore fuori perche' la carta non le mostra. Uno stile in riga
   nella consegna ci obbligherebbe a scrivere stile fuori dal foglio, che e' la cosa che non
   facciamo: se per voi le due viste devono avere la **pillola** incorniciata (`.as-filtro`) e non
   la voce nuda, allora manca il contenitore, e ce lo aggiungete voi al foglio.
2. **Il titolo della carta chiede due nomi, e ne abbiamo uno.** Voi mostrate la sigla (`M31`) e
   sotto il nome comune (*Galassia di Andromeda*): sono due dati distinti, e l'app oggi ne risolve
   **uno solo** per oggetto. Abbiamo montato quello, e `.as-carta__domanda` resta inutilizzata qui.
   Non e' una correzione al vostro disegno -- e' giusto -- ma sappiatelo: finche' l'API non manda
   il secondo nome, quella riga non c'e'.
3. **Niente colonna "ultima notte", ed e' una conferma.** Nel vostro elenco non c'era e noi
   volevamo rimettercela; **Marco ha deciso che non ci va** (22/9/2026): quel posto e' dei
   progetti. Avevate ragione voi.

**Cosa NON abbiamo montato**, e non e' una dimenticanza: la **barra** (cerca, catalogo,
costellazione, filtro usato, ordina) e le **etichette** (progetti, mosaico). Chiedono all'API dati
e risposte che oggi non esistono, e un campo di ricerca che non cerca e' peggio di nessun campo.
Arrivano con le due fette che seguono, sul vostro disegno com'e'.

## 9. La barra, portata -- quattro cose da guardare

Montata il 22/9/2026 con dati veri. La barra, le tendine, l'interruttore e la conta hanno retto
coi mattoni che ci sono; il **campo di ricerca** no (punto 4). Quattro cose da segnalare: tre sullo **stato d'attesa**, una sul campo di ricerca.

1. **`.as-segmentato--caricamento` spegne il mouse e non la tastiera.** Mette `pointer-events:
   none` sulle voci: chi clicca non ottiene niente e nessuno glielo dice, chi arriva col
   tabulatore preme Invio e il comando parte. Un controllo morto per meta' delle mani e' peggio
   di uno vivo, quindi **non l'abbiamo usato**. Se l'intenzione era disabilitare, serve che lo
   stato lo dica davvero (`disabled`/`aria-disabled`), non solo il puntatore.
2. **I due modificatori delle righe non servono a dire "sto aspettando".** Ci abbiamo provato e
   li abbiamo tolti: `.as-carta--caricamento` mette `visibility: hidden` su `.as-carta__titolo` e
   `.as-carta__domanda`, cioe' durante l'attesa le carte **perdono il nome dell'oggetto**;
   `.as-tabella--caricamento` ha due sole regole, tutte e due `background: none` sull'hover, quindi
   **non dipinge niente**. (Lo scheletro vero sembra essere `.as-tabella__riga--scheletro`, che
   pero' e' un'altra cosa: una riga finta, non una riga vera che aspetta.) Il segno sta ora sul
   **campo** e sulle **tendine** (`.as-campo--caricamento`, `.as-scelta--caricamento`), che animano
   e non spengono niente -- e soprattutto ci sono anche quando le righe sono **zero**, che e' il
   caso in cui serve di piu'.
3. **Alla conta manca lo stato d'attesa.** `.as-barra__conta` non ha nessun modificatore, ed e'
   l'elemento che mente di piu' mentre si aspetta: "1.240 oggetti" accanto a `m31` scritto nel
   campo e' un numero, non una sfumatura.
4. **`.as-cerca` e `.as-barra__cerca` si contendono la larghezza, e vince quella sbagliata.**
   Tutte e due portano un `max-width` con la stessa specificita', quindi conta l'ordine nel
   foglio: `.as-barra__cerca` dice 340px -- col vostro commento accanto, *"oltre questa misura un
   campo di ricerca sembra un campo di testo lungo, e la barra perde il suo ritmo"* -- e
   `.as-cerca`, piu' in basso, la sovrascrive con `--misura-campo` (420px). In piu' `.as-cerca` il
   foglio lo dichiara per il campo **con i suggerimenti** (`combobox` piu' `listbox`), e qui non
   ce ne sono. Nel vostro `archivio.html` il campo le porta tutte e due: noi abbiamo tenuto solo
   `.as-barra__cerca`, cosi' il tetto che avete scelto vale. Se `.as-cerca` serviva anche senza
   suggerimenti, va sciolto il conflitto fra i due `max-width`.

**Cosa non abbiamo montato del vostro disegno**, e perche': la vostra barra delle pagine numerate
(`.as-pagine`) resta fuori -- l'app impagina con *Mostra altri*, cento righe per volta, ed e' una
decisione presa (`docs/domini/archivio.md`). Se le pagine numerate sono importanti per voi,
ditelo e ne parliamo, ma non e' una dimenticanza.
