# La navigazione -- contratto

Lo **scheletro** dell'app: dove stanno le pagine, cosa vive nella barra in alto e in fondo a
quella laterale, e come tutto
questo si piega su un telefono. Non e' grafica -- quella la porta il design system, che veste lo
scheletro e poi le pagine una per una -- e' **dove va cosa**, deciso una volta perche' ogni pagina
nuova non lo rimetta in discussione (Marco, 16/9/2026). I nomi vengono da [`glossario.md`](glossario.md);
l'ordine in cui le pagine nascono sta in [`../coda.md`](../coda.md).

## Cosa chiede l'utente

Le prove del frontend si chiamano col loro titolo, che e' l'unica identita' che hanno; stanno in
`frontend/tests/scheletro.test.tsx`.

| richiesta | prova |
|---|---|
| Da qualunque pagina vedo dove sono e dove posso andare | *la barra in alto dice che pagina stai guardando* |
| Le voci sono raccolte per quello che ci faccio, non per come e' fatta l'app | *i gruppi stanno nell ordine del contratto* |
| Una voce che clicco mi porta sempre da qualche parte: non esistono voci che non fanno niente | *una pagina che non esiste ancora non e nella barra*, *una sezione non ancora nata non si mostra*, *nell elenco ci sono le sezioni che esistono, e solo quelle* |
| Una sezione ha il suo indirizzo: il tasto indietro funziona e il collegamento si manda | *un sotto-indirizzo e una pagina vera, non un buco* |
| Vedo quante cose ho da confermare senza aprire la pagina | *accanto a Da confermare c e quante cose aspettano* |
| Vedo da dove sto osservando e che cielo ho, senza aprire niente | *dice da dove osservi, che cielo hai e che luna fa* |
| Se non ho mai dichiarato che cielo ho, lo leggo lo stesso invece di non vedere niente | *un cielo mai dichiarato si legge, non sparisce* |
| Vedo che luna fa stanotte senza aprire niente | *l ora e quella del sito, non quella del browser*, *una luna che non tramonta lo dice a parole* |
| Vedo **dove comincia e dove finisce il buio**, senza aprire niente | *il cielo sta dietro la curva, con la fascia che ogni pezzo di notte ha davvero* |
| Se voglio gli orari della Luna e il suo grafico li apro da li' | *la Luna e un bersaglio solo, e apre il pannello*, *il pannello porta il numero che in barra non ci sta* |
| Cio' che apro si chiude come si chiude tutto, e mi ritrovo dov'ero | *chiudendo, il fuoco torna alla striscia da cui si era aperto* |
| Su telefono la barra si toglie di mezzo e torna quando la chiamo, con le stesse voci | nasce col mobile |
| Premo Scansiona da dove mi trovo, e vedo che sta lavorando anche se cambio pagina | *il lavoro si vede e si ferma anche da un altra pagina* |
| Quando il lavoro finisce, i conti che guardo sono di adesso | *quando il lavoro finisce, il conto si rilegge* |
| Se una cartella non si e' potuta leggere, me lo dice invece di far finta di niente -- sia quando era gia' irraggiungibile, sia quando cade mentre la legge | *le cartelle saltate si dicono, non si buttano*, *una cartella persa mentre la leggeva si dice* |
| Se fermo e poi riprendo, riprende davvero: i file che non aveva letto li legge | `test_resume_after_a_stop_reads_the_files_that_were_left` (`backend/tests/test_api_scan_all.py`) |

## Le decisioni

**Tre gruppi, per quello che ci fai** (Marco, 16/9/2026): **GUARDA** cio' che hai, **SISTEMA**
l'archivio, **PIANIFICA** cio' che farai. *Casa* sta sopra i gruppi, da sola, ed e' il crocevia;
*Impostazioni* sta in fondo, staccata, perche' e' l'unica voce che non e' un pezzo del lavoro.
L'ordine dentro ogni gruppo **e' parte del contratto**: si legge dall'alto come si lavora.

| gruppo | voci, in ordine |
|---|---|
| -- | Casa |
| **GUARDA** | Archivio · Notti · Attrezzatura · Statistiche |
| **SISTEMA** | Da confermare · Diagnostica |
| **PIANIFICA** | Planner · Progetti · Carta del cielo · Meteo |
| -- | Impostazioni |

**Impostazioni e' una pagina con dentro le sue sezioni** (Marco, 16/9/2026), non una voce per ogni
cosa configurabile: **Cartelle**, *Il sito*, *Il riconoscitore*, *Le letture*, *Backup* -- e poi
*Il tuo nome*, *Servizi*, *Soglie*, e domani *Meteo*. Le cartelle stanno li' e non in barra
perche' indicarle e' un gesto che si fa una volta ogni tanto, non ogni giorno -- e una voce in
meno nella barra vale piu' di un clic risparmiato.
**Ogni sezione ha il suo indirizzo** (`/impostazioni/cartelle`): e' cio' che fa funzionare il tasto
indietro e un collegamento che si manda a qualcuno, ed e' la stessa regola delle pagine.

**Ma cio' che l'app non trova deve portare dove si ripara**: il messaggio *"non c'e' nessuna
cartella da leggere"* apre la sezione Cartelle. Senza, dopo il primo avvio non esiste nessuna
strada per aggiungerne una seconda -- e non e' un difetto che si vede provando l'app con
l'archivio gia' pieno.

**Una voce nasce con la sua pagina, mai prima.** Lo scheletro e' deciso **qui**, tutto intero, ma
la barra mostra solo le voci che portano da qualche parte: una voce che apre una pagina vuota e'
una promessa che l'app non mantiene, e chi la clicca la clicca una volta sola. La lista vive in un
posto solo, con accanto la fetta che la fa nascere, cosi' l'ordine e' gia' deciso quando arriva il
suo turno e nessuno lo ridiscute.

**E vale per ogni rimando, non solo per le voci** (Marco, 16/9/2026): un *Apri la notte* o un
*Vedi le statistiche* dentro una pagina **non si mostra** finche' la pagina che aprirebbe non
esiste. Niente rimandi spenti col "presto": e' una promessa a schermo, e su un rilascio pubblico
la legge chiunque.

**In alto vive cio' che vale su ogni pagina**, e niente altro:
- **Scansiona**, col verbo che decide il backend (*Avvia* / *Ferma* / *Riprendi*), e accanto la
  fase coi numeri veri mentre gira. Sta li' e non solo dentro una pagina perche' **il lavoro
  sopravvive alla pagina**: cambiando schermata deve restare fermabile, o resta un lavoro che
  nessuno puo' piu' fermare (e' la ragione per cui il vecchio lo aveva messo li', e vale ancora).
  E **un verbo non promette cio' che non fa**: *Riprendi* dopo uno Stop torna a leggere le
  cartelle rimaste, non solo il lavoro a valle -- un file mai letto non lascia niente in coda,
  quindi senza quella riga l'app diceva "fatto" con l'archivio a un quarto (misurato il
  16/9/2026: 7 frame su 9 fuori).
- **Un avviso quando qualcosa non va**, che compare **solo** se c'e' qualcosa di rotto -- il solver
  non installato, una cartella irraggiungibile, il catalogo assente -- e porta alla Diagnostica.
- **Lingua e tema**, che si cambiano al volo e non sono configurazione (decisione ereditata:
  *"lingua e tema nella barra in alto, non in Impostazioni"*, [`ereditato.md`](ereditato.md)).
- **Il tuo nome**, se lo hai scritto: senza, non compare niente -- nessun ripiego, nessun "Utente".

**In fondo alla barra vive STANOTTE: da dove osservi, e cosa fa il cielo** (Marco, 19/9/2026).
Prima il **sito attivo** con la sua classe di cielo, letta come rampa di nove bande: la posizione
dice quanto e' buono, che una cifra su nove da sola non dice. **La misura in magnitudini qui non
compare** -- e' una delle due eccezioni dichiarate nel foglio, insieme al primo avvio: in 227px
la classe e' un promemoria di dov'e' puntata l'app, e la coppia intera si legge dove si corregge.
Il sito diventa cliccabile quando c'e' la sua scheda; **sotto di
lui la Luna** -- che fase e', quanto e' illuminata, e la curva di come sale e scende stanotte --
che si apre su un pannello con gli orari e il grafico grande. **Quanto sale, in gradi, sta nel
pannello e non in barra**: in 227px il numero toglie posto alla curva, che quella cosa la mostra
gia' (decisione del disegno, dichiarata nel foglio). Stanno insieme perche' sono **la stessa cosa detta in due righe**: la
Luna, il buio e il meteo dipendono dal sito acceso, e separarli costringerebbe a guardare in due
posti per capire una frase sola. In alto resta cio' che riguarda **il lavoro e te** -- la
scansione, il tuo nome, la lingua e il tema, l'avviso quando qualcosa e' rotto.

**Il piede c'e', e il pannello di cui sopra e' costruito:** tutta la Luna
e' **un** bersaglio che lo apre, e dentro la stessa curva si vede grande, con le sue scritte. I
numeri arrivano gia' fatti da `GET /tonight` ([`effemeridi.md`](effemeridi.md)), **il buio
compreso**: dietro la curva ci sono le cinque fasce del cielo, quindi dove comincia e dove finisce
si **vede** invece di essere scritto. Una riga che lo scriva a parole non c'e' ancora, e nascera'
con le Notti -- prima di allora starebbe in 227px a dire con le parole cio' che il disegno dice
gia'.

**Niente ricerca finta.** Il vecchio aveva un campo che non cercava niente. Un posto vuoto in barra
e' una promessa che l'app non mantiene: la ricerca entra quando cerca davvero, e allora e' una
funzione con un suo progetto, non un ornamento.

**Su telefono la barra si ritira dietro un pulsante, e le voci restano tutte.** Nessuna
destinazione si perde e nessuna cambia posto: *mobile = desktop nel contenuto*. Accanto al pulsante
compare il **nome della pagina**, che sul desktop non serve (la voce accesa lo dice gia') e li'
invece e' l'unica cosa che dice dove sei. Il pannello si chiude da solo quando scegli, e si chiude
con Esc o toccando fuori.

**La soglia si misura sulla COLONNA, non sulla finestra.** Con la barra aperta la colonna del
contenuto puo' essere larga come un telefono mentre la finestra e' un desktop: chi guarda la
finestra sbaglia proprio nel caso che conta. E' la stessa regola gia' scritta in
[`ereditato.md`](ereditato.md).

**Il mobile si disegna ora e si costruisce col mobile.** L'ordine e' desktop prima, mobile quando
il desktop funziona; ma il desktop nasce sapendo dove si piega -- i dati escono dall'API gia' fatti
e il layout non porta logica -- cosi' la seconda forma e' una veste e non una riscrittura. Il
pannello a scomparsa **non si costruisce prima**: una superficie che nessuno puo' aprire e
collaudare non e' fatta, e resterebbe verde senza che nessuno l'abbia mai vista.

## Cosa NON fa

Non decide come le pagine sono fatte dentro: ogni pagina ha il suo contratto. Non porta dati --
l'unica eccezione dichiarata e' cio' che la barra **mostra** (quante cose da confermare, la fase
del lavoro, il sito attivo), che arriva gia' pronto dall'API e non si calcola qui. Non ha una
pagina "menu": la barra e' la navigazione, e su telefono e' lo stesso pannello.
