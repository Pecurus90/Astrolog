# Guida a AstroLog

AstroLog cataloga le tue sessioni di astrofotografia. Gli indichi dove tieni i FITS, lui legge
gli header, riconosce cosa hai ripreso e ricostruisce la tua cronologia osservativa.

Non c'e' nessun account e nessuna registrazione: gira sul tuo computer, e i tuoi file non li
manda a nessuno. Li **legge soltanto**: non li sposta, non li rinomina, non li tocca.

Questa guida racconta **cio' che l'app fa adesso**. Quello che ancora non fa e' detto in fondo,
apertamente, invece di essere lasciato indovinare.

## Il primo avvio

La prima volta l'app ti fa **quattro domande**, e poi si toglie di mezzo.

1. **Come ti chiami.** Per ora l'app lo conserva soltanto. Si puo' lasciare vuoto.
2. **Da dove osservi.** Cerchi il sito per nome e scegli fra quelli che compaiono -- ognuno ti
   mostra le sue coordinate, cosi' scegli sapendo su cosa: l'app le riempie da sola, e da quelle
   ricava **il fuso orario e l'altitudine** senza chiedertele. Se preferisci, o se sei senza
   rete, **scrivi tu nome e coordinate**: la strada manuale e' sempre aperta, e non e' un
   ripiego -- e' li' fin dall'inizio, perche' i siti bui dove si osserva spesso la rete non ce
   l'hanno. Le coordinate le puoi scrivere come le scrivi di solito -- `46,4843` o `46.4843`, e
   anche `46,4843 N` -- e se una e' fuori scala te lo dice **sotto il campo**, prima che tu prema.
   Poi ti chiede **che cielo hai**, fra le nove classi di Bortle: non scegli un numero al buio,
   scegli guardando **cosa ci si vede** -- se la Via Lattea proietta ombre o se di notte si legge
   il giornale -- e la misura del cielo la ricava l'app da quella. Puoi **non rispondere**: il
   sito si salva lo stesso, e il cielo resta vuoto invece di prendersi un valore che non hai
   dato.
3. **Dove stanno i file.** Scrivi il percorso di una cartella e premi *Guarda*: l'app conta i
   FITS che ci sono **prima** di registrarla, cosi' ti accorgi subito se hai puntato la cartella
   sbagliata. Se la cartella non si raggiunge te lo dice, e non ti lascia aggiungerla. Sul NAS
   il percorso non lo scrivi: l'app gira dentro un container e i suoi percorsi non sono i tuoi,
   quindi ti fa **sfogliare** le cartelle e ti mostra in alto dove sei arrivato.
4. **Il seeing per la planetaria.** Se hai una **chiave Meteoblue** la scrivi qui: l'app la prova
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
percorso a mano: entri dentro con un clic, risali con *Sali di una cartella*, e quando sei dove
vuoi premi *Usa questa cartella*. L'elenco parte dalla cartella dei dati e non esce da li'.

Se l'app non trova **ASTAP** sul tuo computer, aggiunge un **quinto passo**: ASTAP e' il
programma gratuito con cui l'app riconosce cosa hai ripreso, confrontando le tue foto col cielo.
Ti dice dove prenderlo, e se ce l'hai gia' ti lascia indicare dove sta -- il **programma**, non la
cartella dove l'hai installato. Puoi incollarlo come te lo copia Windows, virgolette comprese.
Appena scrivi il percorso l'app ti risponde se quel programma c'e'
davvero, cosi' un percorso sbagliato lo correggi subito invece di scoprirlo a lettura finita, e
quello che hai scritto si salva anche se non premi *Usa questo*. L'app non scarica e non installa
niente da sola. Puoi saltarlo: senza, l'app cataloga i file, mette in ordine i nomi e conta le ore,
ma non sa dirti **cosa** hai fotografato -- e quando lo installerai, i frame che aspettano verranno
riconosciuti. Se hai tutto a posto quel passo non compare nemmeno.

Quando chiudi il primo avvio, **l'app si mette a leggere da sola** le cartelle che le hai indicato:
non devi cercare nessun pulsante. Se non ne hai indicata nessuna non parte niente, e l'app funziona
lo stesso.

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
durata leggi "senza tempo", mai zero ore. Con le frecce scegli e con Invio apri, oppure tocchi la
voce: un oggetto apre l'Archivio su di lui solo, una notte la sua notte, un pezzo la sua riga in
Attrezzatura, un sito il suo posto nelle Impostazioni. Esc chiude; sul telefono c'e' *Annulla*.
Se non trova niente te lo dice. Le pagine dell'app non si cercano qui: stanno nel binario.

La scansione dice com'e' messa: a riposo ti dice quando l'app ha letto
l'ultima volta e ti offre *Scansiona*; al lavoro ti dice cosa sta facendo, con i numeri e una
barra che avanza, e la puoi fermare da qualunque pagina; fermata ti offre *Riprendi*; se si e'
bloccata ti dice perche', con *Vedi*, e ti offre *Scansiona* per ripartire. Se qualcosa non si e' potuto leggere -- una cartella
irraggiungibile, o caduta mentre la leggeva -- lo trovi scritto in cima alla pagina, con *Vedi*
che ti porta dove si sistema.

La pastiglia dice **da dove osservi** e, col disco, che luna fa. Premila e si apre **Stanotte**:
- il **sito**: se ne hai piu' di uno li trovi tutti e scegli quello di stanotte -- diventa il tuo
  sito di casa, e Luna e meteo si aggiornano. Sotto c'e' che cielo ha, con la classe di Bortle e
  la sua misura, e *Gestisci i siti*. Se non hai ancora un sito, la pastiglia dice *Scegli il
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
gira sul NAS) e ne togli una -- e togliere **non cancella niente**: l'app smette di leggerla, e i
frame gia' entrati restano con la loro storia. Te lo richiede prima, coi numeri davanti.

**Se sposti le foto** -- su un altro disco, perche' il disco ha cambiato lettera, o perche' passi
al NAS -- non togliere la cartella e non aggiungerla di nuovo: le risposte che hai dato in *Da
confermare* su che file sono resterebbero legate al percorso vecchio. Hai due strade. Se aggiungi
il posto nuovo, l'app guarda dentro e, se ci trova gli stessi file di una cartella che conosce e
che non raggiunge piu' (o che avevi tolto), te lo dice -- *E' la cartella ... spostata qui* -- e
con *Usala da qui* la sposta invece di aggiungerne una nuova. Oppure, su ogni cartella
dell'elenco, *Cambia percorso*: indichi dove stanno adesso i file e l'app la sposta. In tutti e
due i casi controlla prima che siano davvero gli stessi file: se non lo sono, te lo dice e non
cambia niente. Dopo lo spostamento la cartella e' la stessa di prima, con i suoi frame e le tue
risposte, e leggendola di nuovo non entra niente due volte.

La seconda e' **Il sito**: da dove osservi. Ci trovi i posti che hai dichiarato, con le loro
coordinate e che cielo hanno, e uno segnato **di casa** -- e' quello da cui l'app calcola le notti
e l'altezza degli oggetti; gli altri servono alle uscite. Di ognuno puoi correggere nome,
coordinate e cielo, renderlo quello di casa, o toglierlo. **Il cielo si corregge quando vuoi**:
cambia davvero -- un lampione nuovo, un quartiere che spegne di notte -- e prima lo sceglievi una
volta al primo avvio e restava li'. Se non sai che cielo hai, lo lasci in bianco: il sito funziona
lo stesso, quello che manca e' il confronto fra una notte e l'altra quando cambi posto.

Un sito che tiene delle notti **non si toglie**: l'app te lo dice, e ti dice quante ne tiene.
Aggiungerne uno lo cerchi per nome, oppure ne scrivi le coordinate a mano -- e la strada a mano e'
sempre aperta, perche' dove si osserva la rete spesso non c'e'.

La terza e' **Il riconoscitore**: ASTAP, il programma che guarda le stelle inquadrate e dice dove
punta ogni ripresa. Qui vedi se l'app lo trova, **dove**, e da cosa l'ha capito: perche' gliel'hai
detto tu, perche' l'ha detto chi ha avviato l'app (sul NAS lo fa chi lo gestisce), perche' l'ha
cercato fra i programmi di sistema, o perche' l'ha trovato dove ASTAP si installa di solito --
quattro strade, e ti dice sempre quale. Sapere **chi ha deciso** conta: se l'app ha pescato da
sola una copia vecchia rimasta in giro, li' vedi che nessuno gliel'ha detto e che quel percorso
se l'e' scelto lei. Puoi dirgli tu dove sta, o premere **Cercalo tu** e farlo cercare all'app:
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
**Meteoblue**: la scrivi, premi *Prova e salva*, e l'app la prova sul tuo conto prima di tenerla --
se il conto non la riconosce te lo dice e non la salva. Una chiave salvata non la rivedi mai
intera: l'app ti mostra come finisce, che basta a sapere se e' quella giusta. Con *Togli la chiave*
il seeing sparisce dal Meteo.

La quinta e' **Le letture**: una per ogni volta che l'app ha letto le tue cartelle. Di
ognuna trovi quale cartella, quando, quanto e' durata, com'e' andata -- e i conti: quanti file ha
guardato, quanti erano nuovi, quanti erano gia' in archivio. Gli zeri non si scrivono, tranne i
**nuovi**, che sono la domanda che ti stai facendo. Se qualcosa e' **rimasto fuori** lo apri li'
dentro: quanti file ha saltato apposta e perche' (le calibrazioni, le somme, quelli ancora in
scrittura), quali cartelle non ha guardato e perche', e i file che non e' riuscito a leggere,
ognuno col suo motivo a parole. L'elenco dei file non letti lo tiene **l'ultima lettura di ogni
cartella**: delle piu' vecchie restano i numeri, e l'app te lo dice invece di mostrarti un elenco
vuoto. La lettura di una scansione appena finita compare **da sola**, senza ricaricare.

Nella barra compaiono **solo le pagine che esistono**: l'app cresce una pagina alla volta, e una
voce che si apre su una pagina vuota sarebbe una promessa non mantenuta. Quando una pagina nasce,
la sua voce compare al posto che ha gia'.

Ogni pagina ha il suo indirizzo, quindi il tasto indietro del browser o del telefono funziona come
ti aspetti, e puoi **ricaricare** la pagina o tenerne l'indirizzo nei preferiti: riapri, e sei
dov'eri.

## Leggere le cartelle

In alto, su ogni pagina, c'e' il pulsante **Scansiona**: lo premi e l'app legge **tutte** le
cartelle che le hai indicato -- non ti chiede quale. Mentre lavora, accanto al pulsante, ti dice
cosa sta facendo e a che punto e' (*leggo i file 120 su 337*), e il pulsante diventa **Ferma**.
Se fermi, diventa **Riprendi**, e riprende davvero: torna sulle cartelle che non aveva finito di
leggere -- i file gia' letti li salta -- e poi va avanti col resto. Il lavoro continua anche se
cambi pagina: per questo il pulsante sta in alto e non dentro una pagina.

Se una cartella non si riesce a leggere -- un disco staccato, il NAS spento -- le altre si leggono
lo stesso, e quella ti viene detta, col suo percorso. E se una cartella sparisce **mentre** l'app
la sta leggendo, te lo dice lo stesso, anche se era la prima e le altre sono andate bene, e anche
quando l'app intanto e' passata ad altro: le altre restano lette, e quella si riprova col prossimo
*Scansiona*. Quando finisce, i conti si aggiornano da soli.

## Dashboard

La pagina principale ti dice **quante cose ci sono da confermare**: sono le domande che l'app ha
su cio' che ha letto negli header. Sotto trovi la versione dell'app e due numeri sullo stato
interno (quante tabelle ha il database, quante voci ha il catalogo di oggetti celesti), e un tasto
per ricaricare.

Se qualcosa non risponde, l'app **te lo dice**: non ti mostra uno zero al posto di un numero che
non ha potuto leggere.

## Archivio

**Cosa hai ripreso, e quanto.** Ogni riga e' un oggetto, o un mosaico: quanti **frame** gli hai dedicato, quante
**ore**, e con che **filtri** -- ognuno con la pastiglia del suo colore e le sue ore, quando le
pose le dicono. Per gli oggetti di catalogo leggi anche la **costellazione**, col suo nome latino
ufficiale, uguale in ogni lingua, e che cosa sono (*Andromeda · galassia*).

Un **mosaico** che hai confermato in *Da confermare* e' **una riga sola**, col nome che gli hai
dato e i frame e le ore di tutti i suoi pannelli, e porta l'etichetta *mosaico 4 pannelli*: sulla
carta sopra il riquadro dell'immagine, nell'elenco nella colonna *Etichette*. Se hai almeno un
mosaico, nella barra compare anche la tendina **Mosaici**, per vedere solo quelli, e in fondo leggi
quanti oggetti e quanti mosaici hai trovato (*3 oggetti e 1 mosaico*). Un oggetto che hai ripreso anche da solo, fuori
dal mosaico, ha la sua riga con quelle sole riprese: niente si conta due volte. Cercando o
filtrando, il mosaico compare se **uno** dei suoi pannelli risponde -- chi cerca il pezzo di cielo
di un pannello trova il mosaico. Sulla carta del mosaico, **Cosa c'e' in ogni pannello** apre
l'elenco dei pannelli, da quello a cui hai dato piu' tempo: per ognuno l'oggetto, i frame, le ore
e il punto del cielo, che dice quale pannello e' se due inquadrano lo stesso oggetto. Un pannello
i cui frame non sono legati a nessun oggetto dice *nessun oggetto riconosciuto*; uno legato a un
oggetto fuori catalogo porta il nome che ha.

La pagina ha **due viste**, e si cambia col pulsante in alto a sinistra:

- **carte**, che e' come si apre: una per riga, col posto gia' pronto per l'immagine (l'app non
  la mostra ancora, e quel riquadro la aspetta);
- **elenco**, a colonne allineate, per confrontare a colpo d'occhio chi ha piu' ore o piu' frame.

In alto c'e' la **barra**: cerchi un oggetto scrivendo qualunque nome con cui lo conosci -- `m31`,
`M 31`, `NGC 224` sono la stessa galassia -- e stringi l'elenco per **catalogo**, **costellazione**
o **filtro usato**. Le tendine ti offrono solo quello che hai davvero: se riprendi solo Messier,
non ti fanno scorrere tutti quelli che il catalogo conosce, e quella che non avrebbe niente da
offrire non compare.

Puoi stringere anche **per periodo**, **sito**, **ottica** e **camera**. Il periodo e' un anno,
oppure "Scegli le date" e le due date **dal** e **al**, comprese: cosi' una stagione invernale da
novembre a febbraio sta in una scelta sola. Il periodo guarda la **notte**, non l'orologio: una
posa delle due del primo gennaio appartiene alla notte del 31 dicembre. Con questi filtri accesi
ogni oggetto dice **solo cio' che hai chiesto**: stringendo al 2025, M 31 porta le ore, i frame e
i filtri del 2025, non quelli di sempre, e l'ordine per ore segue quelle. Lo stesso per il sito e
per il corredo: "con il Newton" sono le pose fatte col Newton. Un mosaico apre i soli pannelli
ripresi li', ma il numero di pannelli resta quello del mosaico. Le tendine del sito, dell'ottica e
della camera compaiono solo se ne hai usati almeno due: con uno solo, sceglierlo non cambierebbe
niente.

Accanto scegli l'**ordine** -- nome, ore o frame -- e l'archivio si apre in ordine di nome, perche'
e' un inventario: cosa hai ripreso di recente si guarda nelle **Notti**. In fondo alla barra c'e'
quanti ne ha **trovati**: con un filtro acceso e' quel numero, non quanti ne hai in tutto. Se la
richiesta non e' andata a buon fine dice "non so quanti", che e' la verita': zero sarebbe l'unica
risposta che sappiamo falsa.

Mentre l'app cerca, quello che avevi sotto resta a schermo -- finche' c'e' qualcosa da mostrare:
se la ricerca di prima non aveva trovato niente, sotto la barra resta il vuoto -- e il campo di
ricerca e le tendine si animano: cosi' non perdi il punto in cui stavi scrivendo, e sai che quello
che vedi e' ancora la risposta di prima.

Se una ricerca non trova niente l'app te lo dice, e non usa le parole dell'archivio vuoto: e'
questa ricerca che non pesca -- e trovi il bottone per togliere i filtri.

Quando apri un oggetto dalla **ricerca in alto**, l'Archivio mostra lui solo e lo dice: "Solo
M 31, aperto dalla ricerca". La barra dei filtri non c'e', perche' non c'e' niente da restringere;
restano le due viste, e *Tutto l'archivio* ti riporta all'elenco intero. Se quell'oggetto non c'e'
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
  dice a parte (*3 senza tempo*), come in *Da confermare*;
- se **nessun** frame di un oggetto dice la durata, non leggi "0 h": le ore non compaiono, e
  restano solo i frame senza tempo;
- un tempo piccolo ma vero non diventa zero: leggi **< 0,1 h**, qui e in *Da confermare*.

Se hai molti oggetti, in fondo trovi **Mostra altri**.

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

**Com'e' il cielo nelle prossime notti del tuo sito di casa, e in quali ore si riprende.** In
testa leggi per quale sito e' la previsione, **quando e' arrivata** e da quanto (*2 ore fa*), e
se hai la chiave Meteoblue anche quando e' arrivato il seeing, che ha un'eta' sua. Le ore della
pagina sono quelle del sito. Accanto scegli il **modello** e c'e' *Aggiorna*.

Sotto c'e' la **fila delle sette notti**: ogni notte col suo giorno (*sab 26*), il **semaforo** --
*buona*, *incerta*, *niente* -- e le ore serene (*3 ore, 23-02*). Le **prime tre** sono ora per
ora; dalla quarta alla settima vedi solo la **tendenza** -- il semaforo, le ore di buio, le nuvole
e l'accordo dei modelli -- perche' cosi' avanti la previsione ora per ora vale poco, e l'app lo
dice invece di farti credere a ore precise. Tocchi una notte e sotto si apre la sua scheda, una
alla volta.

In testa alla scheda leggi **quante ore di buio sereno** avra' la notte, il semaforo, **da che ora
a che ora** (*dalle 23:00 alle 02:00, 3 ore*: se il conto e' piu' piccolo dell'intervallo, in mezzo
c'e' un'ora coperta) e **quanti modelli sono d'accordo**, che e' cio' che ti dice quanto fidarti.
Il semaforo lo decidono **solo le nuvole**, perche' sono l'unica cosa che ferma tutti i soggetti
allo stesso modo: **buona** fino a due ottavi di cielo coperto, **incerta** fino a quattro,
**niente** oltre -- le soglie dei bollettini meteo.

Accanto c'e' cio' che **pesa**, senza cambiare il semaforo: le misure che in qualche ora della notte
diventano *incerte* o *niente* -- le nuvole basse, la pioggia, il vento, la condensa, il jet stream,
il seeing, l'aerosol (*molto fosco*) e la Luna (*al limite* o *solo banda stretta* per chi riprende in
banda larga, e solo se e' sopra l'orizzonte col buio). Ognuna dice la sua parola e quando. Le soglie
vengono da convenzioni pubbliche: la scala Beaufort per il vento, le classi del servizio meteo
canadese per il seeing, la NASA per l'aerosol, meteoblue per il jet stream; per la Luna, la regola
diffusa del 25% per la banda larga.

Sotto c'e' **il cielo della notte**, dall'ultima ora di giorno all'alba sullo sfondo del
crepuscolo: le nubi basse, medie e alte, ognuna dal suo zero perche' si coprono e non si sommano,
l'umidita' a tratteggio sulla stessa scala in percento (la spegni col suo interruttore), e in cima un
tratto chiaro sulle ore di buio sereno. A destra scegli **una misura alla volta** -- pioggia, vento
con le raffiche, condensa come aria e rugiada, seeing, jet stream, aerosol -- con la sua scala, le
soglie tratteggiate e il colore del giudizio ora per ora (per la condensa, la cui soglia e' la
distanza fra aria e rugiada, si colora la fascia fra le due dove si toccano); un'ora che il servizio
non da' e' a tratteggio, mai uno zero. Si apre da sola su quella che pesa di piu'.
Passando sul cielo, o con le frecce, un filo indica l'ora e un riquadro dice i valori; **tutte le
carte vanno a quell'ora**.

Sotto ci sono le **carte**, prima quelle che pesano di piu': nuvole, nuvole basse, poi pioggia,
vento, condensa, seeing, jet stream e aerosol, e in piccolo temperatura e rugiada, umidita', polvere
e il vento a 700 e 200 hPa. Ogni carta dice il **valore della notte** e cosa vuol dire (*media nel
buio*, *in tutto nel buio*, *la minima*), la parola con l'ora in cui comincia (*incerta dalle 22:00,
niente dalle 01:00*), il **picco** con le sue ore, e ha le barrette **ora per ora** dall'ultima ora
di giorno all'alba, col colore del giudizio di ogni ora e le soglie tratteggiate. Un'ora che il
servizio non da' e' a tratteggio, mai uno zero. Tocchi una barretta (o usi le frecce) e la carta va
a quell'ora e ci resta, col valore e la parola di quell'ora; *x notte* la riporta alla notte.

La carta del **vento a 700 hPa** (circa 3.000 metri) lo legge accanto al **solito del tuo sito**:
*piu' forte di 8 notti su 10, qui*. Non e' un giudizio: un vento che altrove sarebbe normale da te
puo' essere raro, e viceversa. Il solito l'app lo scarica da sola una volta l'anno; finche' non c'e'
la carta dice che il confronto arriva.

Il **seeing** viene solo da **Meteoblue**, ora per ora e in arcosecondi, se hai messo la tua
chiave: senza, la sua carta ti dice che per averlo serve, gratuita, e ti porta alle Impostazioni. Se
Meteoblue non accetta la chiave la carta lo dice; se non risponde, resta il seeing che aveva dato
l'ultima volta e la pagina te lo dice. Se il seeing copre solo una parte della notte, la media lo
dice (*media fino alle 02:00*). Meteoblue si chiede al massimo due volte al giorno, perche' la
chiave gratuita ha un tetto di chiamate l'anno.

D'estate molto a nord, dove il buio pieno non arriva, le ore serene si contano col Sole sotto
l'orizzonte e la scheda lo dice; dove il Sole non tramonta legge *Sole sempre su*, senza carte. Se il modello non
da' le nuvole di tutte le ore il semaforo dice *non si sa*.

Il **modello** della previsione: di fabbrica quello che il servizio sceglie per il tuo posto,
oppure l'europeo (ECMWF), il tedesco (ICON) o l'americano (GFS). Sul telefono lo scegli da un
elenco che dice cos'e' ogni voce. Cambiarlo non chiede niente a nessuno -- ogni previsione li porta
tutti insieme -- e la scelta resta. Se un modello quella volta non ha dato notti intere, la pagina
te lo dice e puoi guardarne un altro.

La previsione **arriva da sola** appena hai un sito di casa, e si rinnova ogni tre ore; con
*Aggiorna* la chiedi subito. Se il servizio non risponde -- sei senza rete, o e' giu' -- resta
quella di prima, e una riga in testa dice a che ora e' stata l'ultima richiesta senza risposta e di
che ora e' la previsione che stai leggendo, con *Aggiorna* accanto per riprovare. Se del tuo sito di casa non si riconosce il fuso orario, le sue notti non si possono
dividere: la pagina te lo dice e ti porta a sistemare il sito (in mare aperto vale il fuso
nautico). I dati vengono da Open-Meteo e Copernicus, e il seeing da Meteoblue: la pagina li cita in
fondo.

## Attrezzatura

**Con cosa hai ripreso, e quanto.** I tuoi pezzi raccolti per genere -- telescopi, camere,
montature, e quello che ci sta intorno -- piu' i **corredi** (l'ottica con la sua camera e la
focale) e i **filtri**. Di ognuno leggi quante **ore**, quanti **frame** e in quante **notti** ti
e' servito, e cosa ci hai ripreso. I numeri li conta l'app mentre legge i tuoi file, non quando
apri la pagina, cosi' la pagina si apre subito anche con un archivio grande: un pezzo appena
trovato, a meta' di una lettura, dice *si sta contando* finche' la lettura non finisce.

I pezzi li riconosce dai tuoi file: il nome e' quello che l'header scrive, e le correzioni che
fai qui restano. Un pezzo nuovo non ti viene chiesto altrove: lo trovi qui. Un pezzo che hai
dichiarato tu e' segnato come tale.

**La ruota, il focheggiatore e la camera di guida li trova da solo**, se il tuo programma li
scrive: N.I.N.A. mette nell'header il nome della ruota portafiltri e del focheggiatore, l'ASIAIR
quello della camera di guida -- e siccome li scrive **su ogni posa**, l'app sa anche quante ore
hanno fatto. Li trovi in pagina senza aver scritto niente.

Se invece il tuo programma quei nomi non li scrive, la ruota che ti sei aggiunto a mano **non
dice zero ore**: dice che quelle ore l'app non le sa. Uno zero sarebbe una misura, e sarebbe falsa.

**Quello che i file non nominano lo scrivi tu.** Una guida, un riduttore, una montatura, o un
pezzo che il tuo programma non nomina: *Aggiungi un pezzo*, in cima alla pagina, li fa esistere -- anche il primo giorno, prima di aver letto una sola cartella.
Scegli il genere, dai un nome, e compila quello che sai: i campi che ti chiede cambiano col genere
(la portata la chiede a una montatura, l'apertura a un telescopio). Se quel nome lo possiedi gia'
te lo dice, invece di farti un doppione: il pezzo che cerchi e' gia' nell'elenco.

**E ogni scheda si corregge da qui**, col bottone *Correggi* accanto al pezzo: la scheda si apre
dentro la sua riga. Cambiare il nome non perde niente -- l'app impara che il nome vecchio degli
header e' quello nuovo, cosi' la scansione dopo non ricrea il pezzo com'era. E cio' che scrivi
vince sui file: resta anche quando l'archivio viene riletto. Se due righe sono lo stesso pezzo
scritto in due modi, nella scheda scegli *E' lo stesso pezzo di*: la tendina offre solo quelli dello
stesso genere. Lo stesso vale per i filtri, con *Correggi* accanto al filtro (nome, marca, modello,
o *E' lo stesso filtro di*), e un corredo lo chiami come vuoi con *Dagli un nome*.

Se i file di una camera non dicono quanto e' grande il pixel, l'app lo **ricava dal cielo**: dalla
scala che ha misurato sulle foto risolte e dalla focale del corredo. Serve che i file dicano almeno
il binning: senza, la scala misurata non dice quanti pixel erano uniti, e l'app non tira a indovinare. Lo leggi con scritto *ricavato
dal cielo*, perche' non e' la stessa certezza -- un riduttore che il file non dice lo sposta --; se
il pixel lo scrivi tu nella scheda, vale il tuo.

Di un corredo leggi anche **quanto cielo inquadra davvero**: la scala in arcosecondi per pixel e
il rettangolo in gradi, **misurati** sulle pose che l'app ha risolto -- non calcolati da focale e
pixel. Cosi' un riduttore e' gia' dentro il numero, invece di essere una correzione da fare a
mente. Se di un corredo l'app non ha ancora riconosciuto nessuna posa -- perche' non hai ancora
ripreso, o perche' il riconoscitore non ci e' ancora arrivato -- la scala non c'e', e te lo dice.

**La montatura ha le sue ore.** Se il tuo programma di ripresa la scrive nei file, l'app la lega
da sola a ogni posa: fra i programmi che l'app conosce, oggi lo fa l'ASIAIR. Se no, apri un corredo, premi *Scegli la montatura* e
scegli fra quelle che possiedi (una montatura che non trovi la scrivi con *Aggiungi un pezzo*):
da li' la montatura conta le ore, le notti e cosa ci hai ripreso con quel corredo, e la riga del
corredo dice su quale sta. Quello che scegli tu vale anche dove i file dicono altro; lasciando la
scelta vuota tornano i file. Finche' nessun corredo la porta, la riga della montatura te lo dice
invece di scrivere zero.

**Anche un filtro o un corredo li puoi scrivere tu**, dallo stesso *Aggiungi un pezzo*, prima di
averci ripreso. Un **filtro** vuole il nome e la **banda** che lascia passare -- e' cio' che l'app
guarda per capire cosa hai ripreso -- e se vuoi marca e modello. Un **corredo** vuole l'ottica e la
camera, scelte fra i tuoi pezzi, e la **focale** vera, col riduttore se lo usi. La focale dei tuoi
file l'app la **misura dal cielo** quando riconosce una foto e conosce il pixel della camera:
anche se il tuo programma scrive la focale del telescopio senza il riduttore, dopo il
riconoscimento le pose passano al corredo della focale vera. Dove il cielo non c'e' (dark, flat,
foto non riconosciute) vale la focale che scrive il programma. Il giorno che i tuoi file li
portano, sono gli stessi: un filtro scritto col
nome che il tuo programma mette nei file (`L`, per esempio) prende le pose che lo dicono -- quelle
di una camera a colori restano *OSC* -- e un corredo con la stessa ottica, la stessa camera e una
focale entro il 5% e' quello. Per la stessa ragione, se quel filtro ce l'hai gia' (le tue pose `L`
stanno gia' su *Lum*) o se hai gia' un corredo uguale, te lo dice invece di fartene un secondo: il
filtro si rinomina con *Correggi*. Con l'ASIAIR i file non dicono l'ottica: le sue pose vanno in un
corredo senza ottica, finche' non dici quale era in *Da confermare* (*Attrezzatura da
completare*).

## Da confermare

Qui rispondi alle domande dell'app. Ogni domanda e' una **scheda**, sempre nello stesso ordine, e
quelle senza niente da chiedere non si vedono. Dentro ogni scheda, una riga per cosa: il nome e i
conteggi, e in alcune schede anche **l'indizio che viene dai tuoi file** da cui la domanda nasce,
cosi' puoi controllare invece di fidarti.

**Le risposte si accumulano**: rispondi a quello che sai, in qualunque scheda, e premi **Applica**
una volta sola. In fondo alla pagina una barra ti segue e ti dice **quante risposte hai in mano**
prima di premere; una riga a cui hai risposto si segna con una barra piena a sinistra, cosi' vedi
cosa stai per mandare anche se non distingui i colori. La pagina si rilegge e ti dice quante
risposte ha applicato e quanti frame ha rimesso in lavorazione. Ogni risposta vale anche per i frame che
arriveranno, e **si cambia**: un gruppo a cui hai risposto resta in pagina con la sua risposta.

Il conto scende quando **rispondi**, non quando guardi: *Applica* scrive solo le risposte che hai
dato. Le cose su cui l'app ti sta chiedendo qualcosa -- un filtro che non riconosce, due camere che
sembrano la stessa, un oggetto su cui ha un dubbio, un gruppo di frame senza risposta -- restano
contate finche' non rispondi. Il tuo equipaggiamento qui non c'e': un pezzo nuovo, trovato nei
file o scritto da te, lo vedi e lo completi nell'*Attrezzatura*.

Accanto ai gruppi di frame c'e' **cosa hai ripreso**: gli oggetti che l'app ha riconosciuto in
quei frame, con quanti frame ciascuno (i primi tre, e quanti altri), per rispondere senza dover
ricordare -- anche se il file non scrive l'oggetto, come succede con molte reflex. A parte dice i
frame in cui il cielo non ha trovato niente e quelli che non ha ancora guardato o non e' riuscito
a guardare, perche' non sono la stessa cosa.

- **Stesso pezzo?** Quando due camere hanno lo stesso nome a parte spazi, segni o un'aggiunta fra
  parentesi (per esempio `ATR2600M` e `ATR2600M(USB2.0)`), e lo stesso pixel e lo stesso colore,
  spesso sono la stessa camera vista da due programmi -- ma possono anche essere due camere dello
  stesso modello, e questo l'app non puo' saperlo. Te lo chiede sulla camera con meno frame: *si'*
  la unisce a quella con piu' frame, *no* e la domanda non torna piu' per quelle due. Niente e'
  scelto prima di te, perche' un'unione non si disfa. Per gli altri pezzi non te lo chiede, perche'
  non ha un dato per esserne sicura: l'unione la scegli dall'*Attrezzatura*.
- **Filtri.** Qui arrivano solo i filtri che l'app non riconosce, come una `H` sola: dici cos'e',
  una volta, e vale anche per i frame che arriveranno. E' *uno dei miei filtri* (lo scegli fra
  quelli che l'app conosce), un modello in commercio, o un nome con la sua banda. I filtri che
  l'app riconosce non te li chiede. A differenza delle altre domande, un filtro a cui hai risposto
  esce dalla pagina. Nell'Attrezzatura, con *Correggi* accanto al filtro, ne cambi nome, marca e
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
    notte dice la camera, o quando ne dicono piu' d'una. Scegli uno dei tuoi corredi, oppure
    scrivi la camera e la focale, e l'ottica se serve: l'app ti propone l'ottica che i frame
    dicono e la focale nativa. La tua risposta vale anche se poi la notte direbbe un'altra camera.
  - *L'ottica.* Con l'ASIAIR il file scrive la montatura al posto dell'ottica, e altri programmi
    il telescopio non lo scrivono: scegli una delle tue ottiche o ne scrivi il nome, e se non ce
    l'hai nasce in Attrezzatura. I frame vanno nel corredo che quell'ottica ha gia' con quella
    camera. Il nome della montatura non conta: due montature con la stessa camera alla stessa
    focale sono una scheda sola. Due ottiche diverse usate alla stessa focale con la stessa camera
    ti arrivano come una domanda sola.
  - *Il filtro.* Scegli cosa c'era davanti: *a colori, senza filtro* (si scrive sulla scheda della
    camera, quindi prima serve sapere qual e' la camera), *nessun filtro* o *uno dei miei filtri*,
    che scegli da una tendina fra i filtri che l'app conosce. Se cambiavi filtri senza che il file
    li scrivesse non c'e' una risposta giusta: quei frame restano senza filtro. Una camera che i
    suoi file dicono a colori non te lo chiede: i suoi frame senza filtro vanno su OSC da soli.

  La scheda conta fra le cose da confermare finche' non hai risposto a tutte le parti che chiede;
  puoi rispondere una parte alla volta, e quella gia' data resta. Se rinomini o unisci la camera,
  l'ottica o il filtro che hai scritto, la risposta li segue; se rinomini o unisci una camera dei
  tuoi file, la risposta resta sul nome che i file scrivono. Se cambi casa o il suo fuso, le
  risposte sull'attrezzatura restano dove sono.

  **In questa versione la scheda non si vede ancora**: arriva col disegno nuovo della pagina. Fino
  ad allora il numero di *Da confermare* la conta, e quei frame restano senza le parti che mancano.
- **Frame senza tipo.** Alcuni programmi non scrivono nel file se e' una foto del cielo o un file
  di calibrazione. Lo capisce l'app guardando il cielo: se riesce a riconoscere dove punta e' una
  foto, se non trova stelle e' una calibrazione (bias, flat e dark con pochi pixel caldi non ne hanno; e
  nemmeno una foto tutta coperta dalle nuvole, che cosi' non conta nelle ore). Un dark con molti
  pixel caldi puo' sembrarle un cielo: quello te lo chiede. Te lo chiede in tutti gli altri
  casi: quando vede delle stelle ma non riconosce il cielo, quando non ci riesce in tempo, o quando
  il file non si lascia leggere. Per quelle cartelle lo dici tu, una volta: *e' una
  foto del cielo* li manda avanti come gli altri, *sono file di calibrazione* li lascia da parte
  -- e da li' in poi l'app salta anche i file senza tipo che arriveranno in quella cartella e che
  l'archivio non ha ancora, contandoli fra i saltati della scansione. La tua risposta vale per
  tutti i file senza tipo della cartella, anche per quelli che l'app aveva gia' capito. Finche' non rispondi quei frame non contano nelle
  ore e non te li chiede fra i Frame senza nome ne' per il filtro: prima si sa **che
  file sono**, poi cosa inquadrano. La risposta e' della cartella, e vale anche per i file che ci
  sposti: in una cartella a cui non hai ancora risposto torna ad aspettare un file che il cielo non
  ha riconosciuto, in una cartella che hai detto di calibrazione qualunque file senza tipo, anche
  uno che il cielo aveva riconosciuto. In tutti e due i casi le sue ore escono dall'archivio, e
  tornano quando di quella cartella dici *e' una foto del cielo*, o quando lo rimetti in una
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
- **Mosaici proposti.** Dei pannelli affiancati che l'app ti propone come mosaico dici se lo sono o
  no: un no resta, e non te lo ripropone. Col si' dici anche **di cosa** e' il mosaico: il campo
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
  li trovi fra gli oggetti gia' a posto, aperti a pagine, e li correggi da li'. Ti chiede un nome
  che il catalogo non conosce, e quello su cui nome e cielo non vanno d'accordo, o il cielo esita
  fra piu' oggetti vicini. A ogni scheda rispondi allo stesso modo: scegli una
  voce fra quelle che il cielo ha trovato -- quando ne ha trovate --, scrivi il nome, oppure spunta
  *non e' un oggetto*, per un frame di prova o una messa a fuoco. *Non e' un oggetto* vale anche
  per un oggetto che l'app ha riconosciuto: quei frame escono dalle ore, e la scheda resta, con
  quello che il cielo aveva trovato, per cambiare idea. Vale per i frame che c'erano quando hai
  risposto: se ne riprendi altri dello stesso oggetto, l'app li riconosce come prima. L'app non ti
  avvisa piu' di un oggetto nuovo che sa riconoscere da sola: lo trovi nell'Archivio.

  **In questa versione la scheda non si vede ancora**: arriva col disegno nuovo della pagina. Fino
  ad allora il numero di *Da confermare* la conta.

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
- **Il Meteo non ha ancora grafici**: arrivano col design.
- **ASTAP va installato a parte**, col suo catalogo: l'app ti dice se li trova e ti lascia
  indicare dove sta il programma -- al primo avvio e in Impostazioni -- ma non scarica ne' installa
  niente per te. In futuro viaggera' dentro l'app.
- Nelle **Notti** mancano ancora le misure dei
  tuoi frame, e **una notte non si apre**: il suo dettaglio, come quello di un
  oggetto, arrivera' tutto insieme; le Notti non si filtrano e non si riordinano. Nell'Archivio
  i pannelli di un mosaico si aprono dalla sua carta, non dall'elenco.
- **Il tuo nome si dichiara solo al primo avvio**: le cartelle, il sito e il riconoscitore ora si
  rivedono dalle Impostazioni, il nome no.
- **Le cartelle si sfogliano da un elenco solo sul NAS**, dove l'app ha una radice dei dati; sul
  computer il percorso si scrive.
- **Un campo della scheda non si svuota**: si corregge scrivendo un altro valore, ma un valore
  scritto non si toglie dalla pagina.
- **La veste nuova e' solo sul telaio**: il binario, la barra in alto e Stanotte sono quelli
  disegnati, col carattere nuovo. Le pagine dentro -- Dashboard, Archivio, Notti, Da confermare,
  Attrezzatura, Impostazioni -- funzionano come prima ma sono **spoglie** finche' non arriva il
  loro disegno; il Meteo e' la prima a riceverlo. Il tema chiaro c'e' nel foglio e **non si puo'
  ancora accendere**.
- **Gli avvisi dicono com'e' andata anche senza il colore**: ogni messaggio dell'app porta un
  segno -- una spunta se e' andata bene, un triangolo se c'e' un problema -- perche' chi non
  distingue il verde dal rosso deve capire lo stesso. E nel primo avvio tre risposte che prima
  comparivano in silenzio -- la cartella che non si raggiunge, quanti file ha trovato, se il
  riconoscitore c'e' -- ora vengono **lette ad alta voce** da un lettore di schermo.

## Dove stanno i tuoi dati

Tutto in un file solo, fuori dalla cartella del programma:

- **Windows**: `%LOCALAPPDATA%\AstroLog`
- **Mac**: `~/Library/Application Support/AstroLog`
- **Docker / NAS**: `/data`

Li' dentro ci sono il database, la cache e i log. I tuoi FITS restano dove sono.

Accanto al database c'e' anche **`risposte.json`, il backup di tutto quello che hai detto
all'app**: le preferenze, i siti, le cartelle, i pezzi e i filtri che hai scritto tu, i nomi che
le hai insegnato e ogni risposta di *Da confermare*. Si riscrive da solo dopo ogni tua risposta.
Le foto non ci sono, e nemmeno cio' che l'app ricava leggendole: frame, corredi, notti si rifanno
rileggendo le cartelle.

- **Se il database si perde** (reinstallazione, database ricreato, passaggio al NAS con la stessa
  cartella dati), all'avvio l'app ti dice *"Ho trovato le tue risposte"* e ti chiede se
  rimetterle; poi rilegge le cartelle e ritrovi tutto come prima. Se preferisci ricominciare da
  capo, il file si riscrive alla tua prima risposta.
- **Per portarle su un altro computer**: *Impostazioni > Backup > Esporta le risposte*, e
  sull'altro computer *Importa le risposte*. Il file esportato **non contiene le chiavi dei
  servizi** (Meteoblue), che riscrivi a mano, ne' dove sta ASTAP: sull'altro computer l'app lo
  cerca da sola. L'importazione aggiunge e aggiorna, non cancella niente. Se sull'altro computer le foto stanno in un altro posto, aggiungi la cartella nel posto
  nuovo: l'app la riconosce dai file e le risposte la seguono.
