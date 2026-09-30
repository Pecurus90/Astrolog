# Brief per Claude Design -- la pagina Notti

Terza richiesta, dopo il design system (17/9/2026) e la pagina Archivio. Il primo brief e'
[`design-brief.md`](design-brief.md) e **vale ancora tutto**: token, mattoni, regole non
negoziabili. Qui si chiede **una pagina sola**.

Il foglio consegnato sta nel repo **alla lettera** (sotto `frontend/src/stili/`): non lo
tocchiamo, e le nostre guardie automatiche ce lo impediscono (`tools/test_controlli_veste.py`). Ogni classe nuova deve
arrivare da voi, dentro il foglio intero riconsegnato.

---

## 1. Perche' questa arriva adesso, e con i dati davanti

La pagina Notti **esiste gia'**, costruita coi vostri mattoni e senza niente di inventato: si
apre, legge l'API vera e mostra le righe. Quello che le manca e' la **forma**.

Ve la mandiamo adesso perche' l'Archivio ci ha insegnato una cosa: quel disegno e' fermo da
giorni, e non perche' sia sbagliato -- **mostra dati che l'API non manda** (i filtri per oggetto,
le etichette dei progetti), e per portarlo dovremmo prima costruirli. Qui facciamo il contrario:
sotto trovate **esattamente** cio' che la pagina ha oggi e cio' che arrivera', con l'ordine. Cosi'
quello che ci riconsegnate lo portiamo il giorno stesso.

## 2. Cosa racconta la pagina

L'Archivio risponde a *"cosa ho ripreso"*. Le Notti rispondono a *"quando ho ripreso, e com'e'
andata quella sera"*: e' la pagina con cui un astrofotografo ripercorre la propria vita
osservativa, scorrendo indietro nel tempo.

**Una notte e' una riga**, anche quando dentro ci sono tre oggetti: le ore sono le ore di quella
notte, e gli oggetti stanno dentro la riga. Una notte e' **una data piu' un luogo**: due
postazioni nella stessa sera sono due righe, e la riga lo deve far capire a colpo d'occhio.

La vista che ci serve e' **l'elenco**, ed e' quella di partenza. Le **carte**, se nel vostro
sistema hanno senso anche qui, sono un di piu' -- non la vista principale.

## 3. I dati veri della pagina

Ogni riga porta questo, e nient'altro (`backend/astrolog/api/models_nights.py`):

| dato | esempio | quando non sa |
|---|---|---|
| data | `18 mag 2024` | mai |
| giorno della settimana | `sabato` -- accanto alla data, perche' una notte ce la si ricorda cosi' | mai |
| sito | `Cima Ekar` | mai (senza sito la notte non nasce) |
| frame | `84` | mai |
| ore | `6,2 h` | la notte puo' avere **frame che non dicono quanto sono durati**: si contano a parte, e non valgono zero |
| oggetti | `M 51`, `M 101` -- da uno a molti, gia' ordinati **dal piu' ripreso** | mai (senza oggetto la notte non nasce) |
| filtri | `Ha 3,1 h`, `OIII 1,4 h` -- gia' ordinati **per tempo dato**, col tempo di ciascuno | la notte puo' non avere **nessun filtro dichiarato**; e un filtro puo' avere frame senza durata, e allora ha solo il nome |
| la Luna | `Gibbosa calante, 68%` -- il nome della fase (una delle otto) e quanto era illuminata | **nulla** quando del sito non si riconosce il fuso orario: li' la riga tace, e non va messo un trattino |

In cima alla pagina, tre cose che non sono righe:

| cosa | esempio | quando c'e' |
|---|---|---|
| i totali dell'archivio | `312 notti`, `9.480 frame`, `740 h` | sempre |
| i frame fuori da ogni notte, **per dove si risponde** | *"12 frame aspettano una tua risposta"* + collegamento a *Da confermare*; *"5 frame aspettano di sapere da dove osservavi"* + collegamento alle Impostazioni; *"3 frame non dicono quando sono stati ripresi"*, **senza** collegamento | da zero a tre righe insieme |
| la lettura non finita | *"Sto ancora leggendo l'archivio: 431 frame devono ancora trovare la loro notte"* | solo mentre la spina lavora |

L'elenco arriva a pezzi da 100 col totale dichiarato: la pagina sa sempre quante righe sta
mostrando e quante ce ne sono.

## 4. Cosa arrivera', e va previsto senza disegnarlo pieno

Queste cose **non hanno ancora una forma** -- o non esistono affatto, e allora la pagina tace
invece di scrivere un numero che nessuno ha misurato. Arrivano in quest'ordine, e sulla riga serve
che il posto ci sia:

1. **Il disco della Luna.** La fase e la percentuale **ci sono gia'** (tabella qui sopra) e oggi
   sono due parole in fondo alla riga; nel progetto di prima stavano **a lato**, come un disco
   disegnato, ed e' li' che si leggono a colpo d'occhio. Il foglio ha gia' la falce nel piede
   della barra: se la riutilizzate, ditecelo.
2. **Le misure dei frame** -- quanto erano gonfie le stelle, quante ne ha contate il
   riconoscitore. Uno o due numeri, non una tabella.
3. **Il meteo** -- nuvole, temperatura, vento.
4. **Il dettaglio di una notte**, che si apre: oggetto per oggetto, coi grafici e le statistiche.
   Arriva **per ultimo** ed e' lo stesso pannello dell'oggetto e della libreria, quindi **non
   disegnatelo qui**: serve solo che la riga possa diventare apribile senza essere rifatta.

## 5. I casi che la realta' produce

Nel file montato ci vogliono tutti, non solo la riga bella:

- una notte con **un solo oggetto** e un filtro solo;
- una notte con **quattro o piu' oggetti** e tre filtri (e' quella che decide come si taglia);
- una notte **senza filtro dichiarato** (chi riprende a colori non li ha);
- una notte i cui frame **non dicono la durata**: niente ore, e i frame senza tempo a parte;
- una notte **senza la Luna** (il sito non ha un fuso riconoscibile): la riga deve reggersi
  quando quel pezzo manca, senza lasciare un buco ne' un trattino;
- **due notti con la stessa data e due siti diversi**, una sotto l'altra;
- un **nome di sito lungo** e un nome di oggetto lungo, che rischiano di traboccare;
- il cappello con **tutte e tre** le righe dei frame fermi piu' quella della lettura in corso;
- i **quattro modi di non avere notti**, che sono quattro stati vuoti diversi: non hai frame; non
  hai detto da dove osservi (e allora le notti non nasceranno **mai**); i tuoi frame aspettano una
  risposta; l'app non ci e' ancora arrivata.

## 6. I mattoni da cui passare

Disegnate **con questi**, non accanto a questi (li trovate in `frontend/src/`):

| nostro | avvolge |
|---|---|
| `Riga` (con `Dettaglio`) | `.as-riga` e i suoi pezzi -- oggi la riga di una notte e' questo |
| `Vuoto` (con `NotaDelVuoto`, `AzioniDelVuoto`) | `.as-vuoto` -- i quattro stati vuoti |
| `Avviso` | `.as-avviso` -- la riga della lettura in corso |
| `Bottone` | `.as-bottone` -- *Mostra altre* |
| `TempoDellePose` | le ore, **solo se ci sono**, coi frame senza tempo accanto |

Se per montare la pagina vi servono classi che il foglio non ha -- per esempio una **barra
proporzionale dei filtri** (i numeri ce li abbiamo gia', in ordine e in secondi) o il modo di
mostrare molti oggetti dentro una riga stretta -- aggiungetele **al foglio** e riconsegnatecelo
intero. Un frammento da incollare ci costringerebbe a scrivere dentro il foglio, che e'
esattamente cio' che non facciamo.

## 7. Cosa NON vi chiediamo

- **Ricerca, faccette e ordinamenti**: sono funzioni non ancora costruite, e nasceranno insieme a
  quelle dell'Archivio. Se la vostra forma prevede gia' dove andrebbero, meglio; non disegnatele.
- **Il dettaglio della notte** (vedi sopra).
- **Anteprime delle immagini**: nessun frame ha ancora una miniatura.
- Correzioni ai token: se ne trovate una da fare, ditecela e la fate **voi** alla fonte.

## 8. Come consegnare

1. **`notti.html`** -- la pagina montata, statica, con dati d'esempio dentro, che carica il
   vostro foglio com'e'. Non un'immagine: il markup vero, che trasformiamo in componenti senza
   ridisegnare niente.
2. **il foglio intero e aggiornato**, solo se avete dovuto aggiungere qualcosa. Lo portiamo alla
   lettera e ne ricalcoliamo l'impronta.

---

## 9. La consegna v11, letta -- quattro correzioni

Ricevuta il 21/9/2026: `notti.html` piu' il foglio a v11. Il confronto col nostro (v10) dice
**56 righe cambiate**: le tre classi `.as-notte__oggetti` / `__oggetto` / `__altri` e il
`min-width: 0` sulle carte dentro la griglia. Nessun token nuovo, niente tolto. La pagina e'
montata coi mattoni di `archivio.html` e su questo non abbiamo rilievi.

1. **`.as-bottone--forte` non esiste.** Nel foglio che ci avete consegnato compare **zero
   volte**; le varianti sono otto e la forte si chiama `--primario`, come nel vostro
   `archivio-vuoto.html`. La usano i tre bottoni degli stati vuoti di `notti.html`.
2. **La Luna c'e', e va montata.** La nota di consegna dice che quel dato oggi non esiste: lo
   manda l'API dal 21/9 ed e' scritto nella tabella del punto 3 qui sopra, nome della fase piu'
   percentuale. Montatela dove dite voi -- `.as-luna__disco` in una colonna fra Sito e Oggetti,
   in testa al corpo nella carta -- e serve anche il caso chiesto al punto 5: **una notte senza
   Luna**, che la riga deve reggere senza buco e senza trattino.
3. **Due scostamenti dall'Archivio**, dove invece volevamo l'identita': nella vista a carte le
   pastiglie dei filtri hanno `--spazio-3` (l'Archivio usa `--spazio-2`) e le pagine sotto le
   carte hanno perso `.as-pagine--nuda`, che li' l'Archivio porta. In piu' i quattro vuoti non
   hanno `.as-entra`, che l'Archivio vuoto usa sui suoi.
4. **In partenza si apre l'elenco**, non le carte (Marco, 21/9/2026). L'interruttore resta
   quello, e le carte restano a un clic: cambia solo quale delle due `section` nasce `hidden`.

Le ore per filtro restano fuori, come avete fatto: la riga che vogliamo e' data, sito, oggetti,
ore, frame, e i filtri ci stanno come pastiglie. `.as-ore-filtro` non serve qui.
