# Brief per Claude Design -- il primo avvio

Terza richiesta, dopo il design system (v4) e l'Archivio (v6). Valgono ancora
[`design-brief.md`](design-brief.md) -- token, mattoni, regole non negoziabili -- e il modo di
consegnare concordato con [`design-archivio.md`](design-archivio.md): **le schermate montate**, in
HTML vero che carica il vostro foglio, piu' `astrolog.css` intero se dovete toccarlo.

Dell'Archivio non resta niente in sospeso: correzioni fatte, foglio verificato, zero classi
inventate, contrasto dei mattoni nuovi misurato e sopra soglia.

---

## 1. Questa non e' una pagina, e va detto subito

Il primo avvio e' **la prima cosa che un utente vede**, e non e' una schermata: sono **tre passi
piu' uno**, con uno stato che avanza. Se ci consegnate un file solo ne vediamo un quarto.

| passo | cosa chiede | c'e' sempre? |
|---|---|---|
| 1 | **Come ti chiami** | si' |
| 2 | **Da dove osservi** -- il sito, e che cielo ha | si' |
| 3 | **Dove stanno i file** -- una cartella o piu' | si' |
| 4 | **Il riconoscitore** -- dove sta ASTAP | **solo a chi non ce l'ha** |

Il quarto passo compare **solo se il programma manca**, e quanti passi sono si decide
**entrando**: chi scrive il percorso a meta' strada non se lo vede sparire sotto i piedi.

Da ogni passo si puo' **saltare tutto**, e saltare non chiede conferma: e' una scelta legittima.
L'app senza primo avvio funziona lo stesso -- cataloga, ordina i nomi, conta le ore.

**Cosa ci serve**: le **quattro schermate montate** (quattro file, o uno con quattro sezioni:
fate come vi torna, purche' si vedano tutte), piu' i casi brutti elencati sotto.

## 2. Le schermate, una per una

### Passo 1 -- Come ti chiami
Un campo solo, e si puo' lasciare vuoto. Sotto, una riga che lo dice: *"Per ora l'app lo conserva
soltanto"*. Serve per salutarti nella barra, niente altro.

### Passo 2 -- Da dove osservi
Il passo piu' pieno, e **tre cose in uno**:
1. **cerca il posto per nome** (un campo + un bottone, e i risultati sotto, da scegliere);
2. **oppure scrivi le coordinate a mano**: nome del sito, latitudine, longitudine. Non e' un
   ripiego per quando la ricerca fallisce -- **e' sempre aperta**, perche' un sito buio spesso non
   ha rete, ed e' proprio dove si osserva;
3. **che cielo hai**: si sceglie sulla **scala di Bortle, da 1 a 9** (novita' di questo giro). Non
   chiediamo una magnitudine a chi ha appena installato: sceglie il cielo, e l'app ne ricava la
   misura. Nel resto dell'app la classe si mostra **sempre con la misura accanto** -- "Bortle 4
   (20,8)" -- ma **qui** si sceglie e basta.

Il cielo e' **facoltativo**: chi non lo sa va avanti.

### Passo 3 -- Dove stanno i file
Questo passo ha **due facce diverse**, e dipende da dove gira l'app:
- **sul computer** (Windows, Mac): il percorso **si scrive**, e un bottone *Guarda* dice cosa c'e'
  dentro prima di registrarla;
- **sul NAS, dentro un container**: il percorso non si puo' indovinare, quindi le cartelle **si
  sfogliano**: dove sei, l'elenco di cio' che c'e' dentro, *Sali*, e *Usa questa cartella*.

Servono **tutte e due**. Poi, in tutti e due i casi: cosa ha visto la sonda, il bottone che
registra, e **l'elenco delle cartelle gia' indicate** -- perche' se ne possono dare **piu' di una**,
e chi tiene le foto su due dischi deve poterlo fare qui.

### Passo 4 -- Il riconoscitore (solo a chi manca)
Non e' un guasto, e' una cosa da fare: **niente allarme**. Dice cosa ci perdi senza (l'app non
sapra' dirti *cosa* hai ripreso), da' **l'indirizzo** da cui prenderlo, e offre un campo per dire
dove sta se ce l'hai gia'. **L'app non scarica e non installa niente**: e' l'unica riga di questo
passo che non si negozia.

### Il piede, su ogni passo
*Indietro* (dal secondo in poi), *Avanti* (o *Fatto* sull'ultimo), e *Salta per ora*, che c'e'
sempre. Tre azioni, e una sola e' quella che proponete.

## 3. I casi brutti -- mostrateli, non descriveteli

Sono la meta' del lavoro, e sulla schermata bella non si vedono:

- **il sito non si trova**: la ricerca torna vuota. Attenzione: *"non l'ho trovato"* e *"non ho
  potuto cercare"* per noi **sono la stessa cosa** (senza rete l'API risponde elenco vuoto), ma un
  **guasto vero** e' un'altra cosa e non si traveste da "nessun posto";
- **la cartella non si raggiunge**: e allora non si puo' nemmeno aggiungere;
- **il conteggio e' un minimo, non un totale**: quando la conta si ferma al suo tetto di tempo,
  l'app dice *"almeno 6.500 file"*. Mostrarlo come totale sarebbe una bugia tranquillizzante;
- **l'elenco del NAS non arriva**: si dice, e si torna a poter **scrivere il percorso a mano** --
  scomodo, ma meglio che restare senza strade;
- **il percorso del riconoscitore e' sbagliato**: il passo lo dice **li' per li'**, invece di
  lasciar scoprire il guaio a scansione finita;
- **una scrittura fallisce**: si resta sul passo, dove il problema si puo' ancora risolvere.

## 4. Cosa avete gia', e cosa manca

**Non serve inventare niente**: il primo avvio l'abbiamo gia' vestito coi vostri mattoni, e regge.
Campo, bottone (tre versi), avviso col suo segno, carta col corpo e il piede, elenco, ricerca.
La **colonna dentro la carta** (`.as-carta__corpo--colonna`) risolve la lacuna che vi avevamo
segnalato: due campi di fila non si toccano piu'.

**Quello che manca ancora e' il binario dei passi.** Ve l'avevamo scritto col brief dell'Archivio
e resta aperto: non c'e' un mattone che dica *"sei al secondo di tre, e si chiamano cosi'"*. Noi
intanto l'abbiamo montato con `.as-sezioni` (la navigazione delle Impostazioni), ma lo stato lo
agganciate a `[aria-current="true"]` e per un passo il valore corretto e' `step` -- quindi da noi
quella regola **non scatta**, e la tappa di adesso si distingue solo per inchiostro e peso. E'
questo il pezzo che vi chiediamo di disegnare davvero.

## 5. Un'animazione all'apertura -- proponetela voi

**La vogliamo, e questo e' il posto giusto per permettersela**: il primo avvio si vede **una volta
sola nella vita dell'installazione**, quindi un momento di benvenuto non diventa mai la cosa che
rivedi trecento volte. Come sia, lo proponete voi -- e' il vostro mestiere, non il nostro.

Tre paletti, e sono tecnici:

- **Usa i token delle durate** (`--durata-breve`, `--durata-media`, `--curva`). Cosi' cade da sola
  sotto la regola che avete gia' scritto: chi ha chiesto al sistema *riduci il movimento* vede le
  durate azzerate a 1ms, e l'animazione semplicemente non c'e'. **Senza i token quella regola non
  la raggiunge**, e chi soffre di vertigini si prende l'animazione in faccia.
- **Non ritarda l'uso**: il primo campo si deve poter scrivere subito, anche mentre il movimento
  finisce. Un benvenuto che blocca per un secondo e' un secondo tolto a chi ha fretta.
- **Solo all'apertura, non a ogni passo.** Passare dal passo 2 al 3 non e' un ingresso: se ogni
  passo entra con un movimento, alla terza volta e' un intralcio.

Se vi viene bene anche un piccolo movimento **sul primo passo dell'Archivio vuoto** (l'altra
schermata che si vede la prima volta), mostratecelo: ma non e' richiesto.

## 6. Le regole non negoziabili (le vostre stesse)

- **Il colore da solo non dice mai niente** -- WCAG 2.2, 1.4.1. Vale per il passo dove sei, per
  l'esito della sonda, per il riconoscitore trovato o no.
- **Niente promesse che l'app non mantiene**: nessun passo finto, nessun "presto".
- **Un numero che e' un minimo si dice minimo.**
- **Tre bersagli**: Windows, Mac, NAS in Docker. Il primo avvio sul NAS si fa **da tablet**, spesso
  in piedi davanti al telescopio: se una schermata regge male a 800px, e' quella del passo 3.

## 7. Cosa NON vi chiediamo

- Il salvataggio, la validazione, i messaggi d'errore veri: li scriviamo noi.
- Il quarto passo per chi ha gia' ASTAP: non esiste, non disegnatelo.
- Il meteo, la luna, il Planner: non sono di questa schermata.
