# Guida a AstroLog

AstroLog cataloga le tue sessioni di astrofotografia. Gli indichi dove tieni i FITS, lui legge
gli header, riconosce cosa hai ripreso e ricostruisce la tua cronologia osservativa.

Non c'e' nessun account e nessuna registrazione: gira sul tuo computer, e i tuoi file non li
manda a nessuno. Li **legge soltanto**: non li sposta, non li rinomina, non li tocca.

Questa guida racconta **cio' che l'app fa adesso**. Quello che ancora non fa e' detto in fondo,
apertamente, invece di essere lasciato indovinare.

## Il primo avvio

La prima volta l'app ti fa **quattro domande**, e poi si toglie di mezzo.

A sinistra vedi i passi, col loro nome e quello dove sei; a destra la domanda di quel passo, e in
fondo i comandi: *Salta*, *Indietro*, *Avanti*. Sul telefono i passi diventano una fila di segni in
alto e i comandi restano sempre in vista in fondo allo schermo.

1. **Nome utente.** Per ora l'app lo conserva soltanto. Si puo' lasciare vuoto.
2. **Sito di osservazione.** In *Cerca un luogo* scrivi un nome e scegli fra quelli che compaiono -- ognuno ti
   mostra le sue coordinate, cosi' scegli sapendo su cosa: l'app le riempie da sola, e da quelle
   ricava **il fuso orario e l'altitudine** senza chiedertele. Se preferisci, o se sei senza
   rete, **scrivi tu nome e coordinate**: la strada manuale e' sempre aperta, e non e' un
   ripiego -- e' li' fin dall'inizio, perche' i siti bui dove si osserva spesso la rete non ce
   l'hanno. Le coordinate le puoi scrivere come le scrivi di solito -- `46,4843` o `46.4843`, e
   anche `46,4843 N` -- e se una e' fuori scala te lo dice **sotto il campo**, prima che tu prema.
   Poi ti chiede il **Bortle**, da 1 a 9: non scegli un numero al buio,
   scegli guardando **cosa ci si vede** -- se la Via Lattea proietta ombre o se di notte si legge
   il giornale -- e la misura del cielo la ricava l'app da quella. Puoi **non rispondere**: il
   sito si salva lo stesso, e il cielo resta vuoto invece di prendersi un valore che non hai
   dato. Il sito si salva con **Salva sito**, in fondo insieme agli altri comandi, e poi si passa
   al passo dopo; **Avanti** va oltre senza salvare.
3. **Cartelle.** Scrivi il percorso di una cartella e premi *Verifica*: l'app conta i
   FITS che ci sono **prima** di registrarla, cosi' ti accorgi subito se hai puntato la cartella
   sbagliata. Se la cartella non si raggiunge te lo dice, e non ti lascia aggiungerla. Sul NAS
   il percorso non lo scrivi: l'app gira dentro un container e i suoi percorsi non sono i tuoi,
   quindi ti fa **sfogliare** le cartelle e ti mostra in alto dove sei arrivato.
4. **Seeing (Meteoblue).** Se hai una **chiave Meteoblue** la scrivi qui: l'app la prova
   sul tuo conto e la tiene solo se vale, e da li' il seeing arriva ora per ora per sette notti.
   Non e' obbligatoria, e la maggior parte di chi comincia non ce l'ha: senza, il seeing non c'e' e
   il resto del meteo funziona uguale. La puoi mettere anche dopo, nelle Impostazioni.

**Puoi saltare, da qualunque passo, e non ti viene chiesta nessuna conferma.** Saltare e'
una scelta legittima: l'app cataloga e cerca lo stesso. L'unica cosa che non puo' fare e' creare
le **notti**, perche' una notte e' una data *piu' un sito*, e senza un sito non sa in che fuso
comincia e finisce la tua nottata. Preferisce dirtelo piuttosto che inventarsene uno.

Al terzo passo puoi indicare **quante cartelle vuoi**: ne aggiungi una, compare nell'elenco, ne
aggiungi un'altra. Prima di registrarne una l'app la **guarda** e ti dice quanti file FITS ci sono
dentro, cosi' ti accorgi subito se hai puntato la cartella sbagliata. Dove l'app ha una radice dei
dati -- e' il caso del NAS -- le cartelle si **scelgono da un elenco** invece di scrivere il
percorso a mano: entri dentro con un clic, risali con *Cartella superiore*, e quando sei dove
vuoi premi *Seleziona cartella*. L'elenco parte dalla cartella dei dati e non esce da li'.

Se l'app non trova **ASTAP** sul tuo computer, aggiunge un **quinto passo**: ASTAP e' il
programma gratuito con cui l'app riconosce cosa hai ripreso, confrontando le tue foto col cielo.
Ti dice dove prenderlo, e se ce l'hai gia' ti lascia indicare dove sta -- il **programma**, non la
cartella dove l'hai installato. Puoi incollarlo come te lo copia Windows, virgolette comprese.
Appena scrivi il percorso l'app ti risponde se quel programma c'e'
davvero, cosi' un percorso sbagliato lo correggi subito invece di scoprirlo a lettura finita, e
quello che hai scritto si salva anche se non premi *Verifica percorso*. L'app non scarica e non installa
niente da sola. Puoi saltarlo: senza, l'app cataloga i file, mette in ordine i nomi e conta le ore,
ma non sa dirti **cosa** hai fotografato -- e quando lo installerai, i frame che aspettano verranno
riconosciuti. Se hai tutto a posto quel passo non compare nemmeno.

Quando chiudi il primo avvio, **l'app si mette a leggere da sola** le cartelle che le hai indicato:
non devi cercare nessun pulsante. Se non ne hai indicata nessuna non parte niente, e l'app funziona
lo stesso.

Dopo *Fine* l'app ti mostra **cosa hai dato**: il nome utente, il sito col suo cielo, quante
cartelle e se la scansione e' partita, e se c'e' la chiave per il seeing. Cio' che non hai dato
lo dice (*Nessun sito*, *Nessuna*, *Senza chiave*); se del sito o delle cartelle non riesce a
sapere, quella riga non la mostra. Da li' entri con *Apri AstroLog*: finche' non lo premi la
schermata resta. Se invece premi *Salta*, entri subito.

Che tu completi o che tu salti, l'app **si segna che le hai gia' viste**, e al prossimo avvio non
te le richiede.

## Come ci si muove

A sinistra c'e' il **binario**: le pagine, ognuna con la sua icona e il nome sotto. In cima la
**Dashboard**, poi Notti, Archivio, Progetti, Statistiche e Attrezzatura; dopo uno stacco le
pagine per pianificare -- Planner, Carta del cielo, Meteo -- e in fondo, staccate, *Da confermare*
e le **Impostazioni**. Accanto a *Da confermare* leggi quante cose aspettano una risposta, senza
aprirla. Alcune pagine non ci sono ancora: la loro voce c'e' gia', al suo posto, e aprendola
leggi che la pagina sta arrivando. Se apri un indirizzo che non porta a nessuna pagina -- scritto
male, o tenuto nei preferiti da una pagina che non c'e' piu' -- l'app te lo dice e ti riporta alla
Dashboard.

In alto c'e' il **nome della pagina** che stai guardando, poi la **ricerca**, la **scansione** e,
a destra, la **pastiglia di Stanotte**.

La **ricerca** trova cio' che hai nell'archivio, da qualunque pagina: oggetti, notti, attrezzatura
e siti. Premi *Cerca* (o Ctrl K; sul Mac Cmd K) e scrivi: sotto il campo si apre un elenco diviso
in quattro gruppi, con poche voci per gruppo e, quando ce ne sono altre, quante sono in tutto
("5 di 23"): per vedere le altre scrivi qualche lettera in piu'. Un oggetto lo trovi con ogni suo
nome, anche quello comune; una notte con la data, come la scrivi tu, o col nome di un oggetto che
hai ripreso quella notte. Ogni voce dice quanti frame e quante ore porta; se i file non dicono la
durata leggi "senza durata", mai zero ore. Con le frecce scegli e con Invio apri, oppure tocchi la
voce: un oggetto apre l'Archivio su di lui solo, una notte la sua notte, uno strumento la sua riga in
Attrezzatura, un sito il suo posto nelle Impostazioni. Esc chiude; sul telefono c'e' *Annulla*.
Se non trova niente te lo dice. Le pagine dell'app non si cercano qui: stanno nel binario.

La scansione dice com'e' messa: inattiva ti dice quando e' stata l'ultima (*Ultima scansione*)
e ti offre *Scansiona*; in corso ti dice cosa sta facendo, con i numeri e una
barra che avanza, e la puoi interrompere da qualunque pagina con *Interrompi*; *Interrotta* ti offre
*Riprendi*; se e' *Bloccata* ti dice perche', con *Dettagli*, e ti offre *Scansiona* per ripartire. Se qualcosa non si e' potuto leggere -- una cartella
irraggiungibile, o caduta mentre la leggeva -- lo trovi scritto in cima alla pagina, con *Dettagli*
che ti porta dove si sistema.

La pastiglia dice **da dove osservi** e, col disco, che luna fa. Premila e si apre **Stanotte**:
- il **sito**: se ne hai piu' di uno li trovi tutti e scegli quello di stanotte -- diventa il tuo
  sito predefinito, e Luna e meteo si aggiornano. Sotto c'e' che cielo ha, con il Bortle e
  la sua misura, e *Gestisci i siti*. Se non hai ancora un sito, la pastiglia dice *Seleziona
  sito* e Stanotte ti porta dove lo dichiari;
- la **Luna**: che fase e', quanto e' illuminata, a che ora sorge e tramonta. Gli orari sono
  quelli del **tuo sito**, anche se guardi l'app da un altro fuso. Se una notte la Luna non sorge
  o non tramonta, c'e' scritto: non un trattino;
- il **meteo di stanotte**: il verdetto, le ore utili, quanti modelli sono d'accordo e il vento in
  quota, col collegamento al **Meteo** per il resto. Se la previsione non c'e', te lo dice.

Su uno schermo largo Stanotte resta aperta accanto alla pagina; su uno piu' stretto si apre
sopra, e la chiudi con *chiudi*, con Esc o toccando fuori. L'app ricorda se l'avevi lasciata
aperta. Sul **telefono** le pagine principali -- Dashboard, Notti, Archivio, Progetti -- stanno in
basso, e *Altro* apre un foglio con la scansione e tutte le altre.

Le **Impostazioni** sono una pagina sola con dentro le sue sezioni --
ognuna col suo indirizzo, quindi ci torni col tasto indietro e il collegamento si manda a
qualcuno. La prima e' **Cartelle**: quelle che l'app legge, quante ne e' entrato in archivio, se
al momento si raggiungono. Da li' ne aggiungi una (scrivendo il percorso, o sfogliando se l'app
gira sul NAS) e ne rimuovi una con *Rimuovi* -- e rimuovere **non cancella niente**: l'app smette di leggerla, e i
frame gia' entrati restano con la loro storia. Te lo richiede prima, coi numeri davanti.

**Se sposti le foto** -- su un altro disco, perche' il disco ha cambiato lettera, o perche' passi
al NAS -- non rimuovere la cartella e non aggiungerla di nuovo: le risposte che hai dato in *Da
confermare* su che file sono resterebbero legate al percorso vecchio. Hai due strade. Se aggiungi
il posto nuovo, l'app guarda dentro e, se ci trova gli stessi file di una cartella che conosce e
che non raggiunge piu' (o che avevi rimosso), te lo dice -- *Cartella gia' registrata* -- e
con *Usa questo percorso* la sposta invece di aggiungerne una nuova. Oppure, su ogni cartella
dell'elenco, *Cambia percorso*: indichi dove stanno adesso i file e l'app la sposta. In tutti e
due i casi controlla prima che siano davvero gli stessi file: se non lo sono, te lo dice e non
cambia niente. Dopo lo spostamento la cartella e' la stessa di prima, con i suoi frame e le tue
risposte, e leggendola di nuovo non entra niente due volte.

La seconda e' **Siti**: da dove osservi. Ci trovi i posti che hai dichiarato, con le loro
coordinate e che cielo hanno, e uno segnato **predefinito** -- e' quello da cui l'app calcola le notti
e l'altezza degli oggetti; gli altri servono alle uscite. Di ognuno puoi modificare nome,
coordinate e cielo (*Modifica*), impostarlo come predefinito (*Imposta come predefinito*), o
rimuoverlo (*Rimuovi*). **Il cielo si corregge quando vuoi**:
cambia davvero -- un lampione nuovo, un quartiere che spegne di notte -- e prima lo sceglievi una
volta al primo avvio e restava li'. Se non sai che cielo hai, lo lasci in bianco: il sito funziona
lo stesso, quello che manca e' il confronto fra una notte e l'altra quando cambi posto.

Un sito che tiene delle notti **non si rimuove**: l'app te lo dice, e ti dice quante ne tiene.
Aggiungerne uno lo cerchi per nome, oppure ne scrivi le coordinate a mano -- e la strada a mano e'
sempre aperta, perche' dove si osserva la rete spesso non c'e'.

Subito dopo c'e' **Luna**: le due soglie delle **notti buone per la banda larga**, quelle che il
calendario della Luna nella Dashboard colora. Una notte e' buona se la Luna e' illuminata **meno
del** numero che scrivi (di fabbrica 25%), **oppure** se ha almeno tante **ore di buio senza Luna**
(di fabbrica 4). Sono una scelta, non una regola: una soglia pubblica condivisa non c'e'. Il numero
si salva quando lasci il campo, e il calendario si ricolora subito; la percentuale va da 0 a 100,
le ore da 0 a 12.

La terza e' **ASTAP**: il programma che guarda le stelle inquadrate e dice dove
punta ogni ripresa. Qui vedi se l'app lo trova, **dove**, e da cosa l'ha capito: perche' gliel'hai
detto tu, perche' l'ha detto chi ha avviato l'app (sul NAS lo fa chi lo gestisce), perche' l'ha
cercato fra i programmi di sistema, o perche' l'ha trovato dove ASTAP si installa di solito --
quattro strade, e ti dice sempre quale. Sapere **chi ha deciso** conta: se l'app ha pescato da
sola una copia vecchia rimasta in giro, li' vedi che nessuno gliel'ha detto e che quel percorso
se l'e' scelto lei. Puoi dirgli tu dove sta, o premere **Cerca ASTAP** e farlo cercare all'app:
quello che trova te lo **propone**, e lo usa solo se glielo dici. Se il percorso che hai scritto
non porta a nessun programma, l'app te lo dice subito -- non a scansione finita -- e quel percorso
resta scritto, cosi' lo correggi invece di ribatterlo.

Nella stessa sezione vedi anche **se ASTAP ha il suo catalogo stellare**, e quale. E' un download a
parte, e senza di lui ASTAP parte e non riconosce niente: la lettura si ferma alla
prima posa. Se manca, l'app te lo dice e ti da' l'indirizzo per prenderlo -- non lo scarica lei.
Il catalogo va messo **nella stessa cartella del programma** -- l'autore dice che i file devono
stare tutti insieme -- ed e'
li' che l'app lo cerca, **solo** li': se lo tieni altrove l'app ti dira' che manca, e ti conviene
spostarlo dove ASTAP se lo aspetta. La
stessa cosa te la dice il **primo avvio**, che aggiunge il suo quinto passo anche a chi ASTAP ce
l'ha ma senza catalogo: si finisce allo stesso punto -- una scansione che non riconosce niente --
e conviene saperlo prima.

La quarta e' **Servizi**: le chiavi personali dei servizi che l'app interroga. Oggi c'e' quella di
**Meteoblue**: la scrivi, premi *Verifica e salva*, e l'app la prova sul tuo conto prima di tenerla --
se il conto non la riconosce te lo dice e non la salva. Una chiave salvata non la rivedi mai
intera: l'app ti mostra come finisce, che basta a sapere se e' quella giusta. Con *Rimuovi chiave*
il seeing sparisce dal Meteo.

La quinta e' **Scansioni**: una per ogni volta che l'app ha letto le tue cartelle. Di
ognuna trovi quale cartella, quando, quanto e' durata, com'e' andata -- e i conti: quanti file ha
guardato, quanti erano nuovi, quanti erano gia' in archivio. Gli zeri non si scrivono, tranne i
**nuovi**, che sono la domanda che ti stai facendo. Se qualcosa e' **rimasto fuori** lo apri li'
dentro, con *File esclusi*: quanti file ha saltato apposta e perche' (le calibrazioni, le somme, quelli ancora in
scrittura), quali cartelle non ha guardato e perche', e i file che non e' riuscito a leggere,
ognuno col suo motivo a parole. L'elenco dei file non leggibili lo tiene **l'ultima scansione di ogni
cartella**: delle piu' vecchie restano i numeri, e l'app te lo dice invece di mostrarti un elenco
vuoto. La riga di una scansione appena finita compare **da sola**, senza ricaricare.

Nella barra compaiono **solo le pagine che esistono**: l'app cresce una pagina alla volta, e una
voce che si apre su una pagina vuota sarebbe una promessa non mantenuta. Quando una pagina nasce,
la sua voce compare al posto che ha gia'.

Ogni pagina ha il suo indirizzo, quindi il tasto indietro del browser o del telefono funziona come
ti aspetti, e puoi **ricaricare** la pagina o tenerne l'indirizzo nei preferiti: riapri, e sei
dov'eri.

## Leggere le cartelle

In alto, su ogni pagina, c'e' il pulsante **Scansiona**: lo premi e l'app legge **tutte** le
cartelle che le hai indicato -- non ti chiede quale. Mentre lavora, accanto al pulsante, ti dice
cosa sta facendo e a che punto e' (*Lettura dei file 120 su 337*), e il pulsante diventa **Interrompi**.
Se interrompi, diventa **Riprendi**, e riprende davvero: torna sulle cartelle che non aveva finito di
leggere -- i file gia' letti li salta -- e poi va avanti col resto. Il lavoro continua anche se
cambi pagina: per questo il pulsante sta in alto e non dentro una pagina.

Se una cartella non si riesce a leggere -- un disco staccato, il NAS spento -- le altre si leggono
lo stesso, e quella ti viene detta, col suo percorso. E se una cartella sparisce **mentre** l'app
la sta leggendo, te lo dice lo stesso, anche se era la prima e le altre sono andate bene, e anche
quando l'app intanto e' passata ad altro: le altre restano lette, e quella si riprova col prossimo
*Scansiona*. Quando finisce, i conti si aggiornano da soli.

## Dashboard

La pagina principale ti dice **com'e' stanotte** e cosa resta da fare.

- **In testa**: il sito, quante **ore di buio sereno** ci sono stanotte e il semaforo con la sua
  parola (buona, incerta, non adatta). Accanto la **Luna**: la fase, quanto e' illuminata, quando
  sorge e quando tramonta. **Toccala** e sotto si apre il suo dettaglio: quanto e' illuminata,
  quanti giorni ha, a che ora sorge e **da che parte** (a est-nord-est), fin dove **sale** stanotte
  e a che ora (*sotto l'orizzonte* se stanotte non sorge), quando tramonta, quanto e' lontana, e in che
  notte cadono la prossima **Luna nuova** e la prossima **piena**. Accanto, il **calendario** di
  questo mese e del prossimo (le frecce passano dall'uno all'altro): ogni giorno col disco della
  Luna, *nuova* e *piena* nel loro giorno, oggi contornato, e **colorate le notti buone per la
  banda larga** secondo le due soglie delle Impostazioni, sezione *Luna*. Passa sopra un giorno e
  leggi la Luna e le ore di buio senza Luna. Il calendario lo prepara l'app da sola in background
  appena c'e' un sito di casa: nei primi secondi puo' non esserci ancora. Lo stesso dopo che sposti
  il sito di casa o ne scegli un altro: quello del posto di prima sparisce subito, e il nuovo
  compare da solo entro un minuto circa (anche la prossima nuova e piena aspettano lui).
- **La volta**: la notte disegnata, da mezz'ora prima dell'ora del tramonto a mezz'ora dopo l'ora
  piu' vicina all'alba, coi colori veri del crepuscolo. Sopra l'orizzonte salgono e scendono **Saturno, Giove,
  Marte e Venere** e la **Luna**, ognuno col suo nome nel punto piu' alto; le righe a tratti dicono
  quando comincia il buio, quando sorge la Luna e quando il buio finisce. Le **nuvole** velano ogni
  ora quanto e' coperta, e se stanotte non c'e' nessuna ora serena una coltre copre tutto e le
  curve si spengono. Passa col puntatore e leggi, per quell'ora, quanto buio senza Luna resta da
  li' a fine notte (*Senza Luna ancora 1 h 50 min*; se non ne resta, la riga non c'e') e quanto e'
  alto ognuno. Sul telefono i nomi stanno nella legenda sotto: toccane uno e la sua curva si accende.
- **Il meteo della notte**: sei carte, sempre nello stesso ordine -- Nuvole, Seeing, Jet stream,
  Vento, Condensa, Aerosol -- come quelle del Meteo in piccolo: il valore della notte, cosa vuol
  dire, il giudizio con le sue ore, le barrette ora per ora e il picco. Tocca una carta e sotto si
  apre il suo grafico **dal tramonto all'alba**, sul cielo coi suoi colori; una alla volta,
  *chiudi* lo richiude. *Stanotte intera* apre il pannello di Stanotte, *Meteo* porta alla
  pagina intera.
- **Le prossime 3 notti**: il giorno, le ore serene e il semaforo; ognuna porta al Meteo. La
  terza e' gia' **tendenza**, come nel Meteo: dice le ore di buio, non quelle serene.
- **I progetti in corso** non esistono ancora: la loro sezione lo dice, e *Crea un progetto* --
  la cosa da fare adesso -- porta alla pagina Progetti, che arrivera'. Durante la **prima
  scansione** la sezione dice invece quanti oggetti la lettura ha trovato finora -- o, finche'
  non ne ha riconosciuto nessuno, che li sta ancora cercando.
- **Da riprendere**, accanto: quante domande ci sono **da confermare**, con *Rispondi*, e sotto
  quanti frame sono **fuori dai conti** -- quelli che non stanno ancora in nessuna notte e non
  aspettano una tua risposta in Da confermare (quelli li conta gia' la riga sopra): il sito da
  dichiarare, o una data che manca. Se da confermare non c'e' niente, la riga porta alle Notti, che
  dicono dove si risponde. Durante la prima scansione i frame fuori dai conti non si contano
  ancora. Poi l'ultima notte che hai ripreso -- quanto tempo, su quale oggetto (quello con piu'
  tempo, e quanti altri) e quanti frame -- che si apre nelle Notti. Se i file di quella notte non
  dicono la durata, invece del tempo leggi *frame senza durata*. Se non c'e' niente da riprendere,
  la sezione non c'e'.
- **L'anno**, in fondo: *il 2026, fino a oggi*, con quante **notti** hai ripreso, quante **ore**,
  quante ore **a notte in media** e quante **notti al mese**. Sotto, un **quadretto per giorno**
  da gennaio a dicembre, una colonna per settimana da lunedi': piu' e' chiaro, piu' ore hai ripreso
  quella notte (0 h, meno di 2, 2-4, 4-6, oltre 6); i giorni che devono ancora venire sono solo
  contornati. Passa sopra un quadretto e leggi il giorno e le ore. "Oggi" e' la notte in corso, da
  mezzogiorno a mezzogiorno. Durante la **prima scansione**, finche' ogni frame non ha la sua notte,
  accanto al titolo c'e' *in lettura* con la percentuale dei frame gia' messi nella loro notte,
  notti e ore dicono *finora* e le medie aspettano *a scansione finita*. Sul telefono l'anno non c'e': lo trovi sul desktop.

Sul **telefono** la pagina e' piu' corta: in testa stanotte e la cosa da fare adesso (oggi *Crea un
progetto*), la Luna che toccata apre il suo dettaglio, la volta piu' piccola con un'ora ogni
quattro e i nomi nella legenda sotto, poi le sei carte piccole, tre per riga, che toccate aprono
sotto il loro grafico, e le prossime 3 notti. Alle altre pagine -- le Notti, Da confermare, il Meteo -- si va dalla barra in
basso.

Quando manca qualcosa, in testa alla parte che manca una riga dice cosa e cosa fare, con un'azione
sola in evidenza; il resto della pagina resta quello che si puo' calcolare:

- **Senza un sito** la pagina mostra solo i passi per cominciare: prima *Scegli il sito*, poi
  l'archivio, che resta spento finche' il sito non c'e'.
- **Senza una cartella d'archivio** in testa c'e' *archivio vuoto* con *Scegli la cartella*;
  stanotte e il meteo ci sono gia', perche' dipendono solo dal sito, e progetti, notti e anno
  compaiono dopo la prima scansione. Sul telefono, dove l'anno non c'e', queste frasi non lo
  promettono.
- **Se il meteo non risponde** e non resta una previsione che valga, in testa leggi quanto dura il
  buio di stanotte (e' calcolo, non previsione) e *Non disponibile*; al posto delle carte e delle
  prossime notti un allarme dice da quando non arriva risposta e che l'app riprova da sola ogni 15
  minuti, con *Riprova ora*. Se a non rispondere e' l'app stessa sul meteo, la pagina lo dice in
  cima; progetti, da riprendere e l'anno vengono dall'archivio e restano al loro posto.
- **Durante la prima scansione** sotto le prossime notti una riga dice quanti file ha letto su
  quanti della cartella che sta leggendo e, dopo il primo minuto, quanto le manca al ritmo tenuto
  finora; i conti crescono man mano. Vale anche per una cartella nuova aggiunta a un archivio gia'
  letto: e' la sua prima lettura.
  In *da riprendere* i casi da confermare si contano a scansione finita, e l'ultima notte e' la
  piu' recente trovata finora.
- **Le prossime 3 notti** dicono anche il cielo in parole, col suo segno -- *Sereno*, *Nuvole sparse*,
  *Nuvoloso*, *Coperto*, dalla copertura media nel buio contata in ottavi di cielo come fanno i
  bollettini meteo (okta) -- la pioggia da che ora, e le ore di buio senza Luna, quelle buone per
  la banda larga.

Se
qualcosa non risponde, l'app **te lo dice**: non ti mostra uno zero al posto di un numero che non
ha potuto leggere.

## Archivio

**Cosa hai ripreso, e quanto.** Ogni riga e' un oggetto, o un mosaico: quanti **frame** gli hai dedicato, quante
**ore**, e con che **filtri**: una barra divisa nei colori dei filtri, larga per ognuno quanto le
sue ore, e sotto il nome di ognuno coi suoi frame e le sue ore. Leggi anche che cos'e' e in che
**costellazione** sta, col suo nome latino ufficiale, uguale in ogni lingua: nella carta su due
righe, *galassia* e sotto *Andromeda*. Cio' che l'app non sa lo dice a parole -- *Tipo non disponibile*, *Filtri non indicati* --
e i frame che non dicono la durata sono *senza durata*, mai zero ore.

Un **mosaico** che hai confermato in *Da confermare* e' **una riga sola**, col nome che gli hai
dato e i frame e le ore di tutti i suoi pannelli, e porta il segno *mosaico · 4 pannelli*: sulla
carta sotto le ore, nell'elenco nella colonna *Mosaico*. Se hai almeno un
mosaico, nella barra compare anche **Solo mosaici**, per vedere solo quelli, e accanto all'ordine leggi
quanti oggetti e quanti mosaici hai trovato (*3 oggetti e 1 mosaico*). Un oggetto che hai ripreso anche da solo, fuori
dal mosaico, ha la sua riga con quelle sole riprese: niente si conta due volte. Cercando o
filtrando, il mosaico compare se **uno** dei suoi pannelli risponde -- chi cerca il pezzo di cielo
di un pannello trova il mosaico. In fondo alla carta del mosaico c'e'
l'elenco dei pannelli, numerati, da quello a cui hai dato piu' tempo: per ognuno l'oggetto, i
frame e le ore. Un pannello
i cui frame non sono legati a nessun oggetto dice *Nessun oggetto identificato*; uno legato a un
oggetto fuori catalogo porta il nome che ha.

La pagina ha **due viste**, e si cambia col pulsante in alto a sinistra:

- **carte**, che e' come si apre: una per riga. A sinistra c'e' un riquadro per ogni
  **produzione**, cioe' per ogni coppia di ottica e camera con cui hai ripreso quell'oggetto, e
  sotto i dati leggi quante sono (*2 produzioni*). I riquadri sono vuoti: sono il posto delle
  immagini, che l'app non mostra ancora. Un riduttore non fa un'altra produzione; i frame che non
  dicono con che setup sono stati ripresi ne fanno una a parte. Se le produzioni sono piu'
  d'una, un clic sulla carta apre sotto di lei il loro riepilogo: per ognuna l'ottica e la
  camera, le ore, i frame e i filtri. Si chiude con Esc, con un altro clic sulla carta o con un
  clic fuori;
- **elenco**, a colonne allineate, per confrontare a colpo d'occhio chi ha piu' ore o piu' frame;
  accanto al nome leggi quante produzioni ha, quando sono piu' d'una.

In alto c'e' la **barra**: cerchi un oggetto scrivendo qualunque nome con cui lo conosci -- `m31`,
`M 31`, `NGC 224` sono la stessa galassia -- e stringi l'elenco per **catalogo**, **costellazione**
o **filtro usato**. Ogni criterio e' una **tendina**: una pillola che dice cosa stringe e il valore
scelto (*Catalogo tutti*, *Costellazione Andromeda*); la tocchi, scegli dall'elenco, e si applica
subito. Quando stringe qualcosa si colora e accanto compare una **×** che la toglie; oppure scegli
la prima voce dell'elenco (*Tutti i cataloghi*). *Togli i criteri*, in coda alle tendine, li toglie
tutti insieme. Le tendine ti offrono solo quello che hai davvero: se riprendi solo Messier,
non ti fanno scorrere tutti quelli che il catalogo conosce, e quella che non avrebbe niente da
offrire non compare. Se hai almeno un mosaico c'e' anche **Solo mosaici**, che si accende e si
spegne.

Sul **telefono** le tendine stanno dietro **Criteri**, che dice quanti ne hai scelti: lo tocchi e
si aprono sotto la barra, una per riga.

Puoi stringere anche **per periodo**, **sito**, **ottica** e **camera**. Il periodo e' un anno,
oppure "Intervallo di date": al posto della tendina compaiono le due date **dal** e **al**, comprese,
con la × che torna a *Tutto il periodo*. Cosi' una stagione invernale da novembre a febbraio sta in una
scelta sola. Se "al" viene prima di "dal" l'app te lo dice sotto, invece di mostrarti un elenco
vuoto senza un perche'. Il periodo guarda la **notte**, non l'orologio: una
posa delle due del primo gennaio appartiene alla notte del 31 dicembre. Con questi criteri accesi
ogni oggetto dice **solo cio' che hai chiesto**: stringendo al 2025, M 31 porta le ore, i frame e
i filtri del 2025, non quelli di sempre, e l'ordine per ore segue quelle. Lo stesso per il sito e
per il setup: "con il Newton" sono le pose fatte col Newton. Un mosaico apre i soli pannelli
ripresi li', ma il numero di pannelli resta quello del mosaico. Le tendine del sito, dell'ottica e
della camera compaiono solo se ne hai usati almeno due: con uno solo, sceglierlo non cambierebbe
niente.

A destra scegli l'**ordine** -- nome, ore o frame, anche lui una tendina -- e l'archivio si apre in
ordine di nome, perche' e' un inventario: cosa hai ripreso di recente si guarda nelle **Notti**.
Accanto all'ordine c'e' quanti ne ha **trovati**: con un criterio acceso e' quel numero, non quanti ne hai in tutto. Se la
richiesta non e' andata a buon fine dice "Conteggio non disponibile", che e' la verita': zero sarebbe l'unica
risposta che sappiamo falsa.

Mentre l'app cerca, quello che avevi sotto resta a schermo -- finche' c'e' qualcosa da mostrare:
se la ricerca di prima non aveva trovato niente, sotto la barra resta il vuoto -- e il segno
dell'attesa compare **su cio' che hai appena toccato**: nel campo, con la parola *Ricerca…*, o sulla
tendina che hai cambiato. Se la richiesta non parte dalla barra -- il bottone per togliere i
criteri sotto, il tasto indietro, un collegamento -- il segno compare sul campo e su tutte le
tendine. Cosi' non perdi il punto in cui stavi scrivendo, e sai che quello che
vedi e' ancora la risposta di prima.

Se una ricerca non trova niente l'app te lo dice, e non usa le parole dell'archivio vuoto: e'
questa ricerca che non pesca -- e trovi il bottone per togliere i criteri.

Quando apri un oggetto dalla **ricerca in alto**, l'Archivio mostra lui solo e lo dice: "Risultato
della ricerca: M 31". La barra dei criteri non c'e', perche' non c'e' niente da restringere;
restano le due viste, e *Archivio completo* ti riporta all'elenco intero. Se quell'oggetto non c'e'
piu' -- i suoi frame sono stati tolti -- l'app te lo dice, invece di mostrarti un archivio vuoto.

**Tutto quello che stai guardando finisce nell'indirizzo**: la vista, la ricerca, i filtri e
l'ordine. Se mandi il collegamento a qualcuno, gli si apre esattamente quello che vedi tu. E il
tasto indietro disfa l'**ultima scelta** -- un filtro, un ordine, la vista -- mentre quello che
hai **scritto** nella ricerca non lascia una tappa per ogni lettera, quindi il tasto indietro non
te le fa ripercorrere: disfa la scelta che avevi fatto **prima** di metterti a scrivere, e se non
ne avevi fatte ti porta fuori dall'Archivio.

Le ore sono quelle vere:

- se tieni accanto agli originali anche le **copie calibrate**, non contano due volte;
- un frame che **non dice quanto e' durato** non vale zero: non entra nelle ore, e l'app te lo
  dice a parte (*3 senza durata*), come in *Da confermare*;
- se **nessun** frame di un oggetto dice la durata, non leggi "0 h": le ore non compaiono, e
  restano solo i frame senza durata;
- un tempo piccolo ma vero non diventa zero: leggi **< 0,1 h**, qui e in *Da confermare*.

Se hai molti oggetti, in fondo trovi **Carica altri**.

Appena installata, l'Archivio e' vuoto e **te lo dice**, insieme a cosa fare per riempirlo.

## Notti

**Quando hai ripreso.** L'Archivio racconta gli oggetti; qui ci sono le **notti**, una carta
ciascuna e dalla piu' recente, in cinque colonne che si confrontano dall'alto in basso: che
**giorno** era -- con il giorno della settimana, perche' una notte ce la si ricorda come *"quel
sabato"* -- e da quale **sito**; quante **ore** e quanti **frame**; cosa hai **ripreso**, i primi
tre oggetti ognuno con una barra lunga quanto le sue ore e gli altri contati; con quali **filtri**,
in una barra divisa per ore e sotto il nome, i frame e le ore di ognuno; e **che cielo** c'era.
Sul telefono la carta si impila, senza perdere niente.
I filtri stanno sempre nello stesso ordine, in tutta l'app: L, R, G, B, Ha, OIII, SII, poi quelli
a colori, poi gli altri filtri che l'app riconosce, quelli che non riconosce e per ultimo "senza
filtro". Cosi' ogni filtro lo ritrovi sempre allo stesso posto.

Una notte e' una **data piu' un luogo**: se nella stessa sera hai ripreso da due postazioni, sono
due notti, e la riga dice da dove. Una notte con due oggetti resta **una carta sola**: le sue ore
sono le ore di quella notte, e gli oggetti stanno dentro.

In cima leggi quante notti, quanti frame e quante ore hai **in tutto** -- tutte le tue notti, non
solo quelle che stai guardando -- e cio' che spiega un elenco piu' corto del previsto:

- i frame che **aspettano una tua risposta** non stanno in nessuna notte: te li conta, e ti dice
  **dove** si risponde, che non e' sempre lo stesso posto -- in *Da confermare* per le domande su
  sito e oggetto, nelle **Impostazioni** quando manca il sito da cui osservi;
- i frame che **non dicono quando** sono stati ripresi te li conta e basta: a quelli non c'e'
  risposta che rimedi, e mandarti da qualche parte sarebbe una promessa vuota;
- se l'app **sta ancora leggendo** l'archivio, te lo dice con quanti frame mancano e una pista che
  dice quanto ha fatto: cosi' un elenco a meta' non sembra tutto quello che hai.

Se non hai ancora notti, l'app ti dice **quale** dei motivi e', perche' portano a gesti diversi:
non hai ancora frame (si parte dalla scansione), non hai detto **da dove osservi** (e allora le
notti non nasceranno mai, finche' non lo dici), i tuoi frame aspettano una risposta in *Da
confermare*, oppure l'app non ci e' ancora arrivata.

Su ogni riga c'e' anche **che luna c'era** quella notte e quanto era illuminata -- e' quello che
spiega perche' una serata e' andata come e' andata. Si calcola ogni volta, quindi non invecchia; e
se di un sito non si riconosce il fuso orario la Luna non si sa, e la riga **tace** invece di
mettere un trattino che sembra un dato.

Su ogni riga c'e' anche **com'era il cielo** quella notte, dal sito dove hai ripreso: poco,
parzialmente o molto nuvoloso -- le stesse tre classi del verdetto del Meteo -- con le nuvole nelle
ore di buio e le **ore utili**. Arriva **da solo**
dopo la scansione, senza che tu chieda niente, dall'archivio meteo di Open-Meteo. Arriva quando
il mattino di quella notte ha cinque giorni: prima, l'archivio ha solo una previsione e non ancora
la ricostruzione definitiva, e leggi **il giorno in cui arriva**. Se un archivio di anni e' appena
entrato, l'app lo chiede un pezzo per volta, per non martellare il servizio; senza rete, o se
l'archivio non risponde, aspetta e riprova, e intanto leggi che non e' ancora arrivato, senza una data che non sa. Una notte di un sito senza fuso orario
dice che il meteo non si puo' sapere.

Non ci sono ancora le **misure** dei tuoi frame di quella notte: arrivano, e finche' non ci sono
la pagina tace invece di scrivere un numero che nessuno ha misurato.

## Meteo

**Com'e' il cielo nelle prossime notti del tuo sito predefinito, e in quali ore si riprende.** In
testa leggi per quale sito e' la previsione, **quando e' arrivata** e da quanto (*2 ore fa*), e
se hai la chiave Meteoblue anche quando e' arrivato il seeing, che ha un'eta' sua. Le ore della
pagina sono quelle del sito. Accanto scegli il **modello** e c'e' *Aggiorna*.

Sotto c'e' la **fila delle sette notti**: ogni notte col suo giorno (*sab 26*), il **semaforo** --
*buona*, *incerta*, *non adatta* -- e le ore serene (*3 ore, 23-02*). Le **prime tre** sono ora per
ora; dalla quarta alla settima vedi solo la **tendenza** -- il semaforo, le ore di buio, le nuvole
e l'accordo dei modelli -- perche' cosi' avanti la previsione ora per ora vale poco, e l'app lo
dice invece di farti credere a ore precise. Tocchi una notte e sotto si apre la sua scheda, una
alla volta.

In testa alla scheda leggi **quante ore di buio sereno** avra' la notte, il semaforo, **da che ora
a che ora** (*dalle 23:00 alle 02:00, 3 ore*: se il conto e' piu' piccolo dell'intervallo, in mezzo
c'e' un'ora coperta) e **quanti modelli sono d'accordo**, che e' cio' che ti dice quanto fidarti.
Il semaforo lo decidono **solo le nuvole**, perche' sono l'unica cosa che ferma tutti i soggetti
allo stesso modo: **buona** fino a due ottavi di cielo coperto, **incerta** fino a quattro,
**non adatta** oltre -- le soglie dei bollettini meteo.

Accanto ci sono gli **altri fattori**, che non modificano il verdetto: le misure che in qualche ora della notte
diventano *incerte* o *non adatte* -- le nuvole basse, la pioggia, il vento, la condensa, il jet stream,
il seeing, l'aerosol (*molto fosco*) e la Luna (*banda larga al limite* o *consigliata banda stretta*, e solo
se e' sopra l'orizzonte col buio). Ognuna dice la sua parola e quando. La Luna dice anche quanto e'
illuminata, in che ore e' su e cosa resta nelle altre: "Luna al 55% dalle 23:00 · banda larga fino
alle 23:00". In vista ci sono i primi due, i piu' gravi; se ce ne sono altri, **Altri N fattori**
li apre sotto. Le soglie
vengono da convenzioni pubbliche: la scala Beaufort per il vento, le classi del servizio meteo
canadese per il seeing, la NASA per l'aerosol, meteoblue per il jet stream; per la Luna, la regola
diffusa del 25% per la banda larga.

Sotto c'e' **il cielo della notte**, dall'ultima ora di giorno all'alba sullo sfondo del
crepuscolo: le nuvole basse, medie e alte, ognuna dal suo zero perche' si coprono e non si sommano,
e in cima un tratto chiaro sulle ore di buio sereno. All'apertura ci sono solo le nuvole. L'umidita'
la accendi col suo interruttore, a tratteggio sulla stessa scala in percento. A destra scegli **una misura alla volta** -- pioggia, vento
con le raffiche, condensa come aria e rugiada, seeing, jet stream, aerosol -- con la sua scala, le
soglie tratteggiate e il colore del giudizio ora per ora (per la condensa, la cui soglia e' la
distanza fra aria e rugiada, si colora la fascia fra le due dove si toccano); un'ora che il servizio
non da' e' a tratteggio, mai uno zero. Sotto la linea c'e' il **valore di ogni ora** (sul telefono
di un'ora si' e una no), e accanto all'ultima ora una parola dice quale linea sono le raffiche,
quale l'aria e quale il punto di rugiada. Il seeing senza chiave c'e' fra le misure ma non si sceglie, e il
suo bottone dice perche'. La legenda sotto dice solo cio' che e' sul grafico.
Passando sul cielo, toccandolo o con le frecce, un filo indica l'ora e un riquadro dice i valori;
**tutte le carte vanno a quell'ora**.

Sotto ci sono le **carte**, ognuna sempre allo stesso posto: nuvole, nuvole basse, condensa, pioggia,
visibilita', vento, seeing, jet stream e aerosol, e in piccolo temperatura e punto di rugiada,
polvere e il vento a 700 hPa. La **visibilita'** dice la minima nel buio in chilometri: sotto 1 km
e' **nebbia** (la definizione dell'Organizzazione meteorologica mondiale), e la carta dice da che
ora; non tutti i modelli la danno, e allora la carta dice *Non disponibile*. Le sue barrette
arrivano a 20 km e si schiacciano in alto, cosi' la soglia della nebbia si legge anche in una notte
limpida. Ogni carta dice il **valore della notte** e cosa vuol dire (*media nel
buio*, *totale nel buio*, *la minima*), la parola con l'ora in cui comincia (*incerta dalle 22:00,
non adatta dalle 01:00*), il **picco** con le sue ore, e ha le barrette **ora per ora** dall'ultima ora
di giorno all'alba, col colore del giudizio di ogni ora e le soglie tratteggiate. Un'ora che il
servizio non da' e' a tratteggio, mai uno zero. Tocchi una barretta (o usi le frecce) e la carta va
a quell'ora e ci resta, col valore e la parola di quell'ora; la *x* la riporta alla notte.

La carta del **vento a 700 hPa** (circa 3.000 metri) lo legge accanto allo **storico del tuo sito**:
*superiore a 8 notti su 10 in questo sito*. Non e' un giudizio: un vento che altrove sarebbe normale da te
puo' essere raro, e viceversa. Lo storico l'app lo scarica da sola una volta l'anno; finche' non c'e'
la carta dice che il confronto non e' ancora disponibile.

Il **seeing** viene solo da **Meteoblue**, ora per ora e in arcosecondi, se hai messo la tua
chiave: senza, la sua carta ti dice che per averlo serve, gratuita, e ti porta alle Impostazioni. Se
Meteoblue non accetta la chiave la carta lo dice; se non risponde, resta il seeing che aveva dato
l'ultima volta e la pagina te lo dice. Se il seeing copre solo una parte della notte, la media lo
dice (*media fino alle 02:00*). Meteoblue si chiede al massimo due volte al giorno, perche' la
chiave gratuita ha un tetto di chiamate l'anno.

D'estate molto a nord, dove il buio astronomico non arriva, le ore serene si contano col Sole sotto
l'orizzonte e la scheda lo dice; dove il Sole non tramonta legge *Nessun buio* e, sotto,
che non c'e' nessuna ora di buio, senza carte. Se il modello non da' le nuvole di tutte le ore la
notte dice solo *Non disponibile*, senza ore serene, e sotto perche' non si puo' valutare.

Il **modello** della previsione: il predefinito e' *Automatico*, quello che il servizio sceglie per il tuo posto,
oppure l'europeo (ECMWF), il tedesco (ICON) o l'americano (GFS). Sul telefono lo scegli da un
elenco che dice cos'e' ogni voce. Cambiarlo non chiede niente a nessuno -- ogni previsione li porta
tutti insieme -- e la scelta resta. Se un modello quella volta non ha dato notti intere, la pagina
te lo dice e puoi guardarne un altro.

Sul **telefono** la pagina ha un'altra forma, con gli stessi dati. In testa c'e' il verdetto della
notte scelta: toccalo e si aprono gli *Altri fattori*; toccando una misura dell'elenco si apre la sua
carta (le raffiche aprono quella del vento), toccando fuori dall'elenco si richiude. Nella fila
delle notti le ore serene e la finestra stanno su due righe. Le misure sono carte piccole, quattro per riga,
ognuna col valore della notte e la sua parola (*non disponibile* se quella misura non arriva): toccane
una e sotto si apre la carta intera, con le ore e il picco; un'altra la sostituisce. Sul
grafico del cielo l'umidita' si accende dal menu *Scala di destra*, insieme alle altre voci.

La previsione **arriva da sola** appena hai un sito predefinito, e si rinnova ogni tre ore; con
*Aggiorna* la chiedi subito. Se il servizio non risponde -- sei senza rete, o e' giu' -- resta
quella di prima, e una riga sotto la testa dice a che ora e' stata l'ultima richiesta senza risposta e di
che ora e' la previsione che stai leggendo, con *Aggiorna* accanto per riprovare (e solo li').
Se invece della previsione di prima non resta nessuna notte valida, la pagina lo dice con un
allarme, e *Aggiorna* e' l'unica cosa da fare. Senza un sito predefinito la pagina ti chiede di
aggiungerlo. Se del tuo sito predefinito non si riconosce il fuso orario, le sue notti non si possono
dividere: la pagina te lo dice e con *Modifica sito* ti porta a sistemarlo (in mare aperto vale il fuso
nautico). I dati vengono da Open-Meteo e Copernicus, e il seeing da Meteoblue: la pagina li cita in
fondo.

## Attrezzatura

**Con cosa hai ripreso, e quanto.** I tuoi strumenti raccolti per tipo -- telescopi, camere,
montature, e quello che ci sta intorno -- piu' i **setup** (l'ottica con la sua camera e la
focale) e i **filtri**. Di ognuno leggi quante **ore**, quanti **frame** e in quante **notti** ti
e' servito, e cosa ci hai ripreso. I numeri li conta l'app mentre legge i tuoi file, non quando
apri la pagina, cosi' la pagina si apre subito anche con un archivio grande: uno strumento appena
trovato, a meta' di una scansione, dice *conteggio in corso* finche' la scansione non finisce.

Gli strumenti li riconosce dai tuoi file: il nome e' quello che l'header scrive, e le correzioni che
fai qui restano. Uno strumento nuovo non ti viene chiesto altrove: lo trovi qui. Uno strumento che hai
scritto tu e' segnato *inserito manualmente*.

**La ruota, il focheggiatore e la camera di guida li trova da solo**, se il tuo programma li
scrive: N.I.N.A. mette nell'header il nome della ruota portafiltri e del focheggiatore, l'ASIAIR
quello della camera di guida -- e siccome li scrive **su ogni posa**, l'app sa anche quante ore
hanno fatto. Li trovi in pagina senza aver scritto niente.

Se invece il tuo programma quei nomi non li scrive, la ruota che ti sei aggiunto a mano **non
dice zero ore**: dice che quelle ore l'app non le sa. Uno zero sarebbe una misura, e sarebbe falsa.

**Quello che i file non nominano lo scrivi tu.** Una guida, un riduttore, una montatura, o un
altro strumento che il tuo programma non nomina: *Aggiungi strumento*, in cima alla pagina, li fa esistere -- anche il primo giorno, prima di aver letto una sola cartella.
Scegli il tipo, dai un nome, e compila quello che sai: i campi che ti chiede cambiano col tipo
(la portata la chiede a una montatura, l'apertura a un telescopio). Se quel nome lo possiedi gia'
te lo dice, invece di farti un doppione: lo strumento che cerchi e' gia' nell'elenco.

**E ogni scheda si corregge da qui**, col bottone *Modifica* accanto allo strumento: la scheda si apre
dentro la sua riga. Cambiare il nome non perde niente -- l'app impara che il nome vecchio degli
header e' quello nuovo, cosi' la scansione dopo non ricrea lo strumento com'era. E cio' che scrivi
vince sui file: resta anche quando l'archivio viene riletto. Se due righe sono lo stesso strumento
scritto in due modi, nella scheda scegli *Unisci a*: la tendina offre solo quelli dello
stesso tipo. Lo stesso vale per i filtri, con *Modifica* accanto al filtro (nome, marca, modello,
o *Unisci a*), e un setup lo chiami come vuoi con *Rinomina*.

Se i file di una camera non dicono quanto e' grande il pixel, l'app lo **ricava dal cielo**: dalla
scala che ha misurato sulle foto risolte e dalla focale del setup. Serve che i file dicano almeno
il binning: senza, la scala misurata non dice quanti pixel erano uniti, e l'app non tira a indovinare. Lo leggi con scritto
*(calcolato)*, perche' non e' la stessa certezza -- un riduttore che il file non dice lo sposta --; se
il pixel lo scrivi tu nella scheda, vale il tuo.

Di un setup leggi anche **quanto cielo inquadra davvero**: la scala in arcosecondi per pixel e
il rettangolo in gradi, **misurati** sulle pose che l'app ha risolto -- non calcolati da focale e
pixel. Cosi' un riduttore e' gia' dentro il numero, invece di essere una correzione da fare a
mente. Se di un setup l'app non ha ancora riconosciuto nessuna posa -- perche' non hai ancora
ripreso, o perche' ASTAP non ci e' ancora arrivato -- la scala non c'e', e te lo dice.

Di ogni setup leggi anche **tutte le parti che i suoi frame dicono di aver usato**: la
montatura, la ruota portafiltri, il focheggiatore, la camera di guida, il programma di ripresa, i
filtri. Accanto a ognuna, quanti frame. Se negli anni hai cambiato ruota, o sei passato da un
programma a un altro, le trovi tutte, dalla piu' usata. Una parte che i file non scrivono non
compare, a meno che tu non l'abbia scelta: allora accanto al nome leggi *tua scelta* al posto dei
frame. Oggi dalla pagina si sceglie la montatura (qui sotto); riduttore, ottica di guida e le
altre parti si potranno scegliere allo stesso modo con la pagina nuova. Un riduttore o un'ottica
di guida che nessun setup porta lo dice nella sua riga (*non associato a un setup*), come la
montatura: i file non li scrivono mai, quindi le loro ore arrivano solo da un setup.

**La montatura ha le sue ore.** Se il tuo programma di ripresa la scrive nei file, l'app la lega
da sola a ogni posa: fra i programmi che l'app conosce, oggi lo fa l'ASIAIR. Se no, apri un setup, premi *Seleziona montatura* e
scegli fra quelle che possiedi (una montatura che non trovi la scrivi con *Aggiungi strumento*):
da li' la montatura conta le ore, le notti e cosa ci hai ripreso con quel setup, e la riga del
setup dice su quale sta. Quello che scegli tu vale anche dove i file dicono altro; lasciando la
scelta vuota tornano i file. Finche' nessun setup la porta, la riga della montatura te lo dice
invece di scrivere zero.

**Anche un filtro o un setup li puoi scrivere tu**, dallo stesso *Aggiungi strumento*, prima di
averci ripreso. Un **filtro** vuole il nome e la **banda** che lascia passare -- e' cio' che l'app
guarda per capire cosa hai ripreso -- e se vuoi marca e modello. Un **setup** vuole l'ottica e la
camera, scelte fra i tuoi strumenti, e la **focale** vera, col riduttore se lo usi. La focale dei tuoi
file l'app la **misura dal cielo** quando riconosce una foto e conosce il pixel della camera:
anche se il tuo programma scrive la focale del telescopio senza il riduttore, dopo il
riconoscimento le pose passano al setup della focale vera. Dove il cielo non c'e' (dark, flat,
foto non riconosciute) vale la focale che scrive il programma. Il giorno che i tuoi file li
portano, sono gli stessi: un filtro scritto col
nome che il tuo programma mette nei file (`L`, per esempio) prende le pose che lo dicono -- quelle
di una camera a colori restano *OSC* -- e un setup con la stessa ottica, la stessa camera e una
focale entro il 5% e' quello. Per la stessa ragione, se quel filtro ce l'hai gia' (le tue pose `L`
stanno gia' su *Lum*) o se hai gia' un setup uguale, te lo dice invece di fartene un secondo: il
filtro si rinomina con *Modifica*. Con l'ASIAIR i file non dicono l'ottica: le sue pose vanno in un
setup senza ottica, finche' non dici quale era in *Da confermare* (*Attrezzatura da
completare*).

## Da confermare

Qui rispondi alle domande dell'app. Ogni domanda e' una **scheda**, sempre nello stesso ordine, e
quelle senza niente da chiedere non si vedono. Dentro ogni scheda, una riga per cosa: il nome e i
conteggi, e in alcune schede anche **l'indizio che viene dai tuoi file** da cui la domanda nasce,
cosi' puoi controllare invece di fidarti.

**Le risposte si accumulano**: rispondi a quello che sai, in qualunque scheda, e premi **Applica**
una volta sola. In fondo alla pagina una barra ti segue e ti dice **quante modifiche ci sono da
applicare** prima di premere; una riga a cui hai risposto lo dice con un segno e una parola, cosi' vedi
cosa stai per mandare anche se non distingui i colori. La pagina si rilegge e ti dice quante
modifiche ha applicato e quanti frame sono da rielaborare. Ogni risposta vale anche per i frame che
arriveranno, e **si cambia**: un gruppo a cui hai risposto resta in pagina con la sua risposta.

**Una domanda sola e' aperta alla volta**: le altre sono righe chiuse, che dicono di cosa si
parla, la risposta in breve (o fra cosa si sceglie) e il suo stato -- *senza risposta*, *da
applicare*, *salvata*, *cambiata, da applicare* (con cos'era prima). Apri una riga con *Rispondi*
o *Cambia*; quella di prima si chiude. Le scelte fra poche voci sono pillole. Una scheda con
tutte le risposte si chiude in una riga, al suo posto, e si riapre con *Riapri*; la spiegazione
di una scheda si legge solo in quella su cui stai lavorando.

Nella domanda aperta, sotto il nome, una tabellina raccoglie **i dati che aiutano a rispondere**:
a sinistra la parola (*Oggetti*, *Altri frame*, *Distanza*, *Notti*, *Durata*, *Posizione*, *Simile
a*), a destra il dato. In un mosaico i pannelli stanno accanto ai frame. Le notti sono raggruppate per mese, e le coordinate di un posto sono scritte come si
leggono (*46,1000 N - 12,0000 E*).

In cima leggi **quante domande aspettano**. A sinistra c'e' l'**indice** delle schede: accanto a
ognuna quante domande sono ancora senza risposta, o una spunta quando le hai risposte tutte; un
clic ti porta alla scheda. Sul telefono, e in una finestra stretta, la pagina ha un'altra forma: prima vedi l'elenco dei
**tipi di domanda** (*Filtri*, *Oggetti*...), ognuno con quante risposte ha e in che stato; toccandone
uno vedi **un caso alla volta**, con in alto *Tutti i tipi* e *caso 1 di 2*, e in fondo *Caso
prima* e *Caso dopo* (ai due capi, *Tipo prima* e *Tipo dopo*). Le risposte sono le stesse, e
*Applica* resta in fondo. Se fra le modifiche c'e'
un'**unione di strumenti**, la barra in fondo te lo dice prima di *Applica*: e' l'unica risposta
che non si annulla. Mentre l'app applica, la pagina si ferma; l'esito si chiude con *Chiudi*.
Quando non c'e' niente da chiedere la pagina dice *Niente da confermare*; se l'ultimo *Applica*
ha risposto a tutto, sopra resta il suo esito finche' non lo chiudi. Se in archivio non c'e'
ancora nessun frame la pagina lo dice e ti porta ad *Aggiungi cartelle*: le domande arrivano
quando l'app ha letto i file.

Il conto scende quando **rispondi**, non quando guardi: *Applica* scrive solo le risposte che hai
dato. Le cose su cui l'app ti sta chiedendo qualcosa -- un filtro che non riconosce, due camere che
sembrano la stessa, un oggetto su cui ha un dubbio, un gruppo di frame senza risposta -- restano
contate finche' non rispondi. Il tuo equipaggiamento qui non c'e': uno strumento nuovo, trovato nei
file o scritto da te, lo vedi e lo completi nell'*Attrezzatura*.

Accanto ai gruppi di frame ci sono gli **oggetti**: quelli che l'app ha riconosciuto in
quei frame, con quanti frame ciascuno (i primi tre, e un *+ N* per gli altri), per rispondere senza dover
ricordare -- anche se il file non scrive l'oggetto, come succede con molte reflex. A parte dice i
frame *senza oggetti identificati* e quelli *non risolti*, perche' non sono la stessa cosa.

- **Strumenti duplicati.** Quando due camere hanno lo stesso nome a parte spazi, segni o un'aggiunta fra
  parentesi (per esempio `ATR2600M` e `ATR2600M(USB2.0)`), e lo stesso pixel e lo stesso colore,
  spesso sono la stessa camera vista da due programmi -- ma possono anche essere due camere dello
  stesso modello, e questo l'app non puo' saperlo. Te lo chiede sulla camera con meno frame: *Si',
  unisci a* la unisce a quella con piu' frame, *No, sono distinti* e la domanda non torna piu' per
  quelle due. Niente e'
  scelto prima di te, perche' un'unione non si disfa. Per gli altri strumenti non te lo chiede, perche'
  non ha un dato per esserne sicura: l'unione la scegli dall'*Attrezzatura*.
- **Filtri.** Qui arrivano solo i filtri che l'app non riconosce, come una `H` sola: dici cos'e',
  una volta, e vale anche per i frame che arriveranno. Scegli come rispondere fra tre modi, uno
  alla volta: *Filtro esistente* (lo scegli fra quelli che l'app conosce), *Modello da catalogo*
  (scrivi la marca o il nome, e scegli dall'elenco che compare; se non trova niente te lo dice) o
  *Nuovo filtro* (un nome con la sua banda). Cambiare modo toglie la risposta data con quello di
  prima. I filtri che
  l'app riconosce non te li chiede. A differenza delle altre domande, un filtro a cui hai risposto
  esce dalla pagina. Nell'Attrezzatura, con *Modifica* accanto al filtro, ne cambi nome, marca e
  modello, o lo unisci a un altro; la banda, per ora, no.
- **Attrezzatura da completare.** Quando i file non dicono con che camera, con che ottica o con
  che filtro hai ripreso, l'app te lo chiede in **una scheda sola** per ogni gruppo di file che
  scrivono le stesse cose: lo stesso nome di camera e di telescopio, la stessa focale (a meno del
  5%) e lo stesso sensore. Non per notte e non per cartella: la tua risposta vale per tutti quei
  frame, anche per quelli che arriveranno, in qualunque notte e da qualunque cartella. La scheda
  ti chiede solo cio' che manca.
  - *La camera.* Se un frame non la dice, prende quella degli altri frame della stessa notte, se
    dicono tutti la stessa, e non te la chiede; e se non dice l'ottica, prende quella della notte
    quando la notte ne dice una sola a una focale sola. Te la chiede quando nessun frame di quella
    notte dice la camera, o quando ne dicono piu' d'una. Scegli uno dei tuoi setup, oppure
    scrivi la camera e la focale, e l'ottica se serve: l'app ti propone l'ottica che i frame
    dicono e la focale nativa. La tua risposta vale anche se poi la notte direbbe un'altra camera.
    Se la scheda chiede anche l'ottica e il setup scelto non ne ha una, o non la scrivi, dopo
    *Applica* la scheda te la chiede da sola, sotto la camera.
  - *L'ottica.* Con l'ASIAIR il file scrive la montatura al posto dell'ottica, e altri programmi
    il telescopio non lo scrivono: scegli una delle tue ottiche o ne scrivi il nome, e se non ce
    l'hai nasce in Attrezzatura. I frame vanno nel setup che quell'ottica ha gia' con quella
    camera. Il nome della montatura non conta: due montature con la stessa camera alla stessa
    focale sono una scheda sola. Due ottiche diverse usate alla stessa focale con la stessa camera
    ti arrivano come una domanda sola.
  - *Il filtro.* Scegli cosa c'era davanti: *a colori, nessun filtro* (si scrive sulla scheda della
    camera, quindi prima serve sapere qual e' la camera: se la togli, la scelta non parte), *nessun filtro* o *filtro esistente*,
    che scegli da una tendina fra i filtri che l'app conosce. Se cambiavi filtri senza che il file
    li scrivesse non c'e' una risposta giusta: quei frame restano senza filtro. Una camera che i
    suoi file dicono a colori non te lo chiede: i suoi frame senza filtro vanno su OSC da soli.

  La scheda conta fra le cose da confermare finche' non hai risposto a tutte le parti che chiede;
  puoi rispondere una parte alla volta, e quella gia' data resta. Se rinomini o unisci la camera,
  l'ottica o il filtro che hai scritto, la risposta li segue; se rinomini o unisci una camera dei
  tuoi file, la risposta resta sul nome che i file scrivono. Se cambi casa o il suo fuso, le
  risposte sull'attrezzatura restano dove sono.

  La scheda aperta mostra a sinistra cio' che i file scrivono (camera, telescopio, sensore, ottica
  e focale, gli oggetti ripresi) e a destra una parte per ogni cosa che manca, ognuna col suo
  stato: *senza risposta*, *da applicare*, *salvata*. Chiusa, la riga dice in breve cosa hai gia'
  dato e cosa resta da indicare.
- **Frame senza tipo.** Alcuni programmi non scrivono nel file se e' un Light o un file
  di calibrazione. Lo capisce l'app guardando il cielo: se riesce a riconoscere dove punta e' un
  Light, se non trova stelle e' una calibrazione (bias, flat e dark con pochi pixel caldi non ne hanno; e
  nemmeno un Light tutto coperto dalle nuvole, che cosi' non conta nelle ore). Un dark con molti
  pixel caldi puo' sembrarle un cielo: quello te lo chiede. Te lo chiede in tutti gli altri
  casi: quando vede delle stelle ma non riconosce il cielo, quando non ci riesce in tempo, o quando
  il file non si lascia leggere. Per quelle cartelle lo dici tu, una volta: *Light* li manda
  avanti come gli altri, *Calibrazione* li lascia da parte
  -- e da li' in poi l'app salta anche i file senza tipo che arriveranno in quella cartella e che
  l'archivio non ha ancora, contandoli fra i saltati della scansione. La tua risposta vale per
  tutti i file senza tipo della cartella, anche per quelli che l'app aveva gia' capito. Finche' non rispondi quei frame non contano nelle
  ore e non te li chiede fra i Frame senza nome ne' per il filtro: prima si sa **che
  file sono**, poi cosa inquadrano. La risposta e' della cartella, e vale anche per i file che ci
  sposti: in una cartella a cui non hai ancora risposto torna ad aspettare un file che il cielo non
  ha riconosciuto, in una cartella che hai detto di calibrazione qualunque file senza tipo, anche
  uno che il cielo aveva riconosciuto. In tutti e due i casi le sue ore escono dall'archivio, e
  tornano quando di quella cartella dici *Light*, o quando lo rimetti in una
  cartella che lo lascia andare. Se invece ce lo copi, e
  l'originale resta dov'era in una cartella che l'app legge, conta la cartella dell'originale e le
  ore restano. Un file che
  sparisce, o una cartella che togli, tiene invece le sue ore come ogni altro frame. L'elenco delle
  cartelle e i loro numeri si aggiornano quando l'app finisce di leggerle o di guardare il cielo:
  mentre lavora possono essere indietro di un passo, e se la fermi a meta' lettura restano indietro
  finche' non riparte. La tua risposta invece si vede subito.
- **Frame senza sito.** Dei frame ripresi a coordinate che non cadono in nessuno dei tuoi siti dici
  **da quale sito** vengono: te li propone dal piu' vicino, ma non ne sceglie uno. Accanto vedi le
  **notti** di quei frame, per ricordarti dov'eri: il fuso e' quello delle coordinate -- quando
  avrai risposto sara' quello del sito che scegli, e per una posa vicino a mezzogiorno le due date
  possono non coincidere.
- **Mosaici proposti.** Dei pannelli affiancati che l'app ti propone come mosaico dici *Mosaico* o
  *Non e' un mosaico*: un no resta, e non te lo ripropone. Con *Mosaico* dici anche l'**oggetto del
  mosaico**: il campo
  arriva gia' compilato con l'oggetto del catalogo che sta al centro del mosaico, e se non e'
  quello scrivi il nome giusto. I pannelli che riprenderai dopo entrano nel mosaico da soli, e
  rinominare la camera o dire con che camera hai ripreso non cambia niente: la risposta resta.
  Un gruppo di frame conta come pannello solo se ha almeno un quarto del tempo del pannello piu'
  lungo (le pose, se i file non dicono la durata): i pochi frame spostati di un giro al meridiano
  non ti fanno proporre un mosaico, e restano col loro oggetto. Un frame di cui non si sa quanto e'
  grande il campo non entra nei mosaici.
- **Che oggetto e'.** L'oggetto te lo chiede in **una scheda per gruppo di frame**, sempre uguale:
  i frame che l'app ha messo su un oggetto di cui non e' sicura, oppure un gruppo di frame che non
  dicono cosa hai ripreso e di cui il cielo non dice niente. Non ti chiede un oggetto che il cielo
  riconosce, ne' una sigla del catalogo scritta nel file (`M 31`) anche se il cielo non c'e': quelli
  li conta fra gli oggetti gia' riconosciuti, che correggi dal fondo della sezione. Ti chiede un nome
  che il catalogo non conosce, e quello su cui nome e cielo non vanno d'accordo, o il cielo esita
  fra piu' oggetti vicini. A ogni scheda rispondi allo stesso modo: scegli una
  voce fra quelle che il cielo ha trovato -- quando ne ha trovate --, scrivi il nome, oppure spunta
  *non e' un oggetto*, per un frame di prova o una messa a fuoco. *Non e' un oggetto* vale anche
  per un oggetto che l'app ha riconosciuto: quei frame escono dalle ore, e la scheda resta, con
  quello che il cielo aveva trovato, per cambiare idea. Vale per i frame che c'erano quando hai
  risposto: se ne riprendi altri dello stesso oggetto, l'app li riconosce come prima. L'app non ti
  avvisa piu' di un oggetto nuovo che sa riconoscere da sola: lo trovi nell'Archivio.

  Nella scheda ogni voce trovata nel campo dice se sta *nell'inquadratura*, *fuori
  dall'inquadratura* o se la *posizione non e' nota*; *Altro nome* apre il campo dove lo scrivi.
  In fondo alla sezione leggi quanti oggetti l'app riconosce da sola (*218 oggetti
  riconosciuti*). Con *Apri* li vedi venti alla volta, e ti sposti con *Precedenti* e
  *Successivi*; *Chiudi* li toglie di nuovo. Non sono domande, quindi non hanno uno stato: accanto
  a ognuno c'e' *Correggi*, che apre la stessa scheda con il nome di adesso gia' scelto. Un oggetto
  che non e' in un catalogo (una cometa, un nome che hai scritto tu) si apre su *Altro nome*, col
  suo nome gia' nel campo. Da li'
  scrivi un altro nome o spunti *non e' un oggetto*; la correzione parte con *Applica*, insieme
  alle altre risposte. La sezione c'e' anche quando non ha domande, proprio per questo.

  *I frame senza nome.* I frame che non dicono cosa hai ripreso, e di cui il cielo non dice niente
  -- non ci ha trovato oggetti, o non e' riuscito a guardarli -- si chiedono per gruppo: la notte,
  la camera, il telescopio e **dove puntava la montatura**, non la cartella. I frame che puntano a
  meno di un campo inquadrato dal primo del gruppo sono lo stesso oggetto, cosi' il dithering non
  conta; per saperlo servono il puntamento, la focale e i pixel del file. Due oggetti ripresi nella
  stessa notte sono quindi due domande, tranne quando stanno a meno di un campo l'uno dall'altro
  (M 81 e M 82 con un campo largo) o quando il file non dice dove puntavi: li' restano una domanda
  sola, e rispondendo metti tutti quei frame sullo stesso oggetto. Per accorgertene, la domanda
  dice l'ora del primo e dell'ultimo frame (*dalle 21:10 alle 03:40*), nell'ora del posto; contano
  solo i frame che dicono quando sono stati ripresi, e un gruppo dove nessuno lo dice non mostra
  ore. Ogni notte
  e' una domanda a parte. Scrivi l'oggetto oppure spunta *non e' un oggetto*, per un frame di prova o una
  messa a fuoco: la risposta vale anche per i frame che arriveranno nello stesso gruppo. La
  risposta resta scritta sui frame: se cambi casa o il suo fuso e un frame passa a un'altra notte,
  la porta con se'; se in un gruppo finiscono frame con due risposte diverse, la domanda torna
  aperta. Dove invece il cielo ha trovato qualcosa decide lui -- anche *non e' un oggetto* detto
  per il gruppo non tocca un frame che il cielo ha riconosciuto, nemmeno se lo riconosce dopo la
  tua risposta --, e un frame che il nome lo
  scrive tiene il suo.

  *Gli oggetti trovati.* In cima ci sono quelli su cui l'app ha un dubbio, ognuno con cio' che il
  cielo ha trovato nel campo di quel frame da cliccare, quando ha trovato qualcosa; se nessuno e'
  quello giusto, o se non c'e' niente da cliccare, il nome lo scrivi tu. Un dubbio resta aperto
  finche' non rispondi. Gli oggetti che l'app riconosce da sola stanno gia' chiusi, e li apri a
  pagine quando ti serve correggerne uno. Su ogni scheda trovi quanti frame sono e quante ore, e a parte
  i frame il cui header non dice il tempo.

Quando scrivi a mano un oggetto una **sigla** che il
catalogo conosce, come *M 81* o *m81*, diventa quella voce del catalogo; un altro nome resta com'e'.

## Cosa non fa ancora

- **Sul NAS la scansione puo' partire da sola a intervalli**, se chi avvia l'app imposta
  `ASTROLOG_SCAN_EVERY_MIN`. Per il resto partono da soli solo i giri del meteo -- la previsione,
  lo storico delle notti riprese e il solito del sito: la scansione si chiede col pulsante.
- **ASTAP va installato a parte**, col suo catalogo: l'app ti dice se li trova e ti lascia
  indicare dove sta il programma -- al primo avvio e in Impostazioni -- ma non scarica ne' installa
  niente per te. In futuro viaggera' dentro l'app.
- Nelle **Notti** mancano ancora le misure dei
  tuoi frame, e **una notte non si apre**: il suo dettaglio, come quello di un
  oggetto, arrivera' tutto insieme; le Notti non si filtrano e non si riordinano. Nell'Archivio
  i pannelli di un mosaico si aprono dalla sua carta, non dall'elenco.
- **Il tuo nome si dichiara solo al primo avvio**: le cartelle, il sito e ASTAP ora si
  rivedono dalle Impostazioni, il nome no.
- **Le cartelle si sfogliano da un elenco solo sul NAS**, dove l'app ha una radice dei dati; sul
  computer il percorso si scrive.
- **Un campo della scheda non si svuota**: si corregge scrivendo un altro valore, ma un valore
  scritto non si toglie dalla pagina.
- **La veste nuova e' solo sul telaio**: il binario, la barra in alto e Stanotte sono quelli
  disegnati, col carattere nuovo. Le pagine dentro -- Archivio, Notti, Da confermare,
  Attrezzatura, Impostazioni -- funzionano come prima ma sono **spoglie** finche' non arriva il
  loro disegno; il Meteo e la Dashboard l'hanno gia'. Il tema chiaro c'e' nel foglio e **non si puo'
  ancora accendere**.
- **Nella Dashboard**, nella volta le curve dei progetti arrivano coi
  progetti.
- **Gli avvisi dicono com'e' andata anche senza il colore**: ogni messaggio dell'app porta un
  tondo con la sua forma -- con una spunta se e' andata bene, un punto esclamativo se c'e' un
  problema, tratteggiato se aspetta -- perche' chi non distingue il verde dal rosso deve capire lo
  stesso. E nel primo avvio tre risposte che prima
  comparivano in silenzio -- la cartella che non si raggiunge, quanti file ha trovato, se
  ASTAP c'e' -- ora vengono **lette ad alta voce** da un lettore di schermo.

## Dove stanno i tuoi dati

Tutto in un file solo, fuori dalla cartella del programma:

- **Windows**: `%LOCALAPPDATA%\AstroLog`
- **Mac**: `~/Library/Application Support/AstroLog`
- **Docker / NAS**: `/data`

Li' dentro ci sono il database, la cache e i log. I tuoi FITS restano dove sono.

Accanto al database c'e' anche **`risposte.json`, il backup di tutto quello che hai detto
all'app**: le preferenze, i siti, le cartelle, gli strumenti e i filtri che hai scritto tu, i nomi che
le hai insegnato e ogni risposta di *Da confermare*. Si riscrive da solo dopo ogni tua risposta.
Le foto non ci sono, e nemmeno cio' che l'app ricava leggendole: frame, setup, notti si rifanno
rileggendo le cartelle.

- **Se il database si perde** (reinstallazione, database ricreato, passaggio al NAS con la stessa
  cartella dati), all'avvio l'app ti dice *"Backup trovato"*, ti mostra quando e' stato
  scritto e cosa contiene (conferme, siti, cartelle, strumenti e filtri) e ti chiede se
  ripristinare i dati (*Ripristina*); poi rilegge le cartelle e ritrovi tutto come prima. Se preferisci
  *Inizia da zero*, il file si riscrive alla tua prima risposta.
- **Per portarle su un altro computer**: *Impostazioni > Backup > Esporta backup*, e
  sull'altro computer *Importa backup*. Il file esportato **non contiene le chiavi dei
  servizi** (Meteoblue), che riscrivi a mano, ne' dove sta ASTAP: sull'altro computer l'app lo
  cerca da sola. L'importazione aggiunge e aggiorna, non cancella niente. Se sull'altro computer le foto stanno in un altro posto, aggiungi la cartella nel posto
  nuovo: l'app la riconosce dai file e le risposte la seguono.
