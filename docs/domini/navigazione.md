# La navigazione -- contratto

Il **telaio** dell'app: il binario delle pagine, la barra in alto, Stanotte, e come tutto si piega
su un telefono. La forma viene dal disegno (Claude Design, telaio v26, `51-telaio.css`;
[ADR 0018](../adr/0018-tutto-nel-telaio-nuovo.md)); qui c'e' **dove va cosa** e perche'. I nomi
vengono da [`glossario.md`](glossario.md).

## Cosa chiede l'utente

Le prove del frontend si chiamano col loro titolo; stanno in `frontend/tests/scheletro.test.tsx`
(binario e barra), `frontend/tests/stanotte.test.tsx` (la pastiglia e il pannello) e
`frontend/tests/veste.test.tsx` (come il telaio si misura).

| richiesta | prova |
|---|---|
| Da qualunque pagina vedo dove sono e dove posso andare | *la barra in alto dice che pagina stai guardando*, *la voce della pagina aperta e' accesa, e solo lei* |
| Le voci stanno nell'ordine del disegno | *le voci del binario stanno nell ordine di pagine.tsx* |
| Una voce senza pagina mi dice che arriva, invece di sparire | *una voce senza pagina apre la pagina che dice che sta arrivando* |
| Un indirizzo che non esiste me lo dice e mi riporta alla Dashboard | *lo dice, e porta alla Dashboard* (`navigazione.test.tsx`) |
| Vedo quante cose ho da confermare senza aprire la pagina | *accanto a Da confermare c e quante cose aspettano* |
| Premo Scansiona da dove mi trovo, e la fermo anche da un'altra pagina | *il lavoro si vede e si ferma anche da un altra pagina*, *premere Scansiona chiede di leggere TUTTE le cartelle*, *il verbo del pulsante lo decide il backend, non la pagina* |
| Mentre lavora vedo cosa fa, coi numeri veri; quando finisce i conti sono di adesso | *mentre gira si legge cosa sta facendo, coi numeri veri*, *quando il lavoro finisce, il conto si rilegge* |
| Se la scansione si blocca mi dice perche' e la faccio ripartire | *bloccata, la scansione dice perche' e si fa ripartire dalla barra*, *bloccata, la scansione nel foglio dice perche' e porta dove si guarda* |
| Cio' che non si e' potuto leggere me lo dice in testa alla pagina, e *Vedi* porta dove si ripara | *le cartelle saltate si dicono, non si buttano*, *una cartella persa mentre la leggeva si dice*, *Vedi porta alle Cartelle solo quando il rifiuto e' delle cartelle* |
| La pastiglia mi dice da dove osservo e apre Stanotte; senza sito mi chiede di sceglierlo | *dice il sito, e apre Stanotte*, *senza sito chiede di sceglierlo* (`stanotte.test.tsx`) |
| In Stanotte vedo il sito, il suo cielo e la Luna, con l'ora del sito | *dice da dove osservi, che cielo hai e che luna fa*, *l ora e quella del sito, non quella del browser*, *un cielo mai dichiarato si legge, non sparisce*, *una luna che non sorge lo dice a parole*, *una luna che non tramonta lo dice a parole* |
| Fra piu' siti scelgo quello di stanotte; con uno solo non c'e' scelta | *fra piu' siti, sceglierne un altro lo scrive al backend*, *un sito solo non apre una scelta che non c e* |
| In Stanotte vedo il meteo della notte, o perche' manca | *dice il verdetto, le ore utili, l'accordo e il vento in quota, e porta al Meteo*, *senza la previsione di stanotte lo dice, e porta al Meteo che spiega perche'* |
| Cio' che apro si chiude con Esc e il fuoco torna dov'era; il foglio del telefono non lo lascia scappare | *Esc chiude Stanotte, e il fuoco torna alla pastiglia*, *Altro apre le voci che non stanno fra le schede del telefono, ed Esc lo chiude*, *il foglio Altro trattiene il fuoco: Tab non esce dietro il velo* |
| Il telaio si misura dal suo contenitore, non dalla finestra | *il contenitore misurato e' il genitore del telaio, non il telaio*, *il binario, la barra alta e il corpo stanno nel telaio* (`veste.test.tsx`) |
| Se fermo e poi riprendo, riprende davvero | `test_resume_after_a_stop_reads_the_files_that_were_left` (`backend/tests/test_api_scan_all.py`) |

## Le decisioni

**Il binario, nell'ordine del disegno** (Marco in Claude Design, v15-v26): Dashboard, Notti,
Archivio, Progetti, Statistiche, Attrezzatura; uno stacco; Planner, Carta del cielo, Meteo. In
fondo, staccate, Da confermare e Impostazioni. Niente gruppi con titolo: lo stacco basta a
dividere cio' che hai da cio' che pianifichi. Ogni voce e' un'icona con la parola sotto; i nomi
lunghi vanno a capo dove dice il glossario ("Carta / del cielo", "Da / confermare"). La prima
pagina si chiama **Dashboard** (glossario del disegno).

**Ogni voce si vede, anche senza la sua pagina** (Marco, 7/10/2026): apre una pagina che dice
che sta arrivando. Supera "una voce nasce con la sua pagina": il binario e' gia' quello finale, e
chi lo impara non lo reimpara. I **rimandi dentro le pagine** invece restano: un *Apri la notte*
non si mostra finche' la pagina che aprirebbe non esiste.

**Impostazioni e' una pagina con dentro le sue sezioni** (Marco, 16/9/2026): Cartelle, Il sito,
Il riconoscitore, Le letture, Backup, e le altre quando nascono. Ogni sezione ha il suo indirizzo
(`/impostazioni/cartelle`): il tasto indietro funziona e il collegamento si manda.

**La barra in alto dice il titolo della pagina, la scansione e la pastiglia di Stanotte.** La
pagina non ripete il suo titolo (disegno v18).
- **La scansione** ha quattro stati: a riposo ("Ultima lettura ... ", *Scansiona*), al lavoro
  (fase, pista, numeri, *Ferma*), fermata (*Riprendi*), bloccata (il motivo, *Vedi* e il verbo per ripartire). Il verbo lo
  decide il backend. Sta nel telaio perche' **il lavoro sopravvive alla pagina**: cambiando
  schermata deve restare fermabile. *Riprendi* dopo uno Stop torna a leggere le cartelle rimaste.
- **Cio' che la scansione non ha potuto fare** -- un rifiuto, una cartella caduta mentre la
  leggeva, le cartelle saltate -- e' una **riga di stato in testa al corpo**, con *Vedi* che porta
  dove si ripara (Marco, 7/10/2026). Tacerlo farebbe sembrare completa una scansione che non lo e'.
- **La ricerca** ("Cerca oggetto, notte, sito") entra quando cerca davvero, con la sua rotta
  (Marco, 7/10/2026): un campo che non cerca e' una promessa che l'app non mantiene.

**La pastiglia dice il sito e apre Stanotte** (disegno v25). Senza sito dice "Scegli il sito".
**Stanotte** e' un pannello: da 1440 px prende una colonna sua, sotto si apre sopra il contenuto
col velo, sul telefono sale dal basso. Dentro, tre blocchi: il **sito** (i siti da scegliere,
se sono piu' di uno; la classe del cielo letta con la sua misura; *Gestisci i siti*), la **Luna**
(fase, quanto e' illuminata, quando sorge e tramonta), il **meteo** della notte (verdetto,
accordo, vento in quota, e il rimando al Meteo). Stanno insieme perche' dipendono tutti dal sito
acceso. Scegliere un sito cambia il sito di casa: si rileggono stanotte, il meteo e l'elenco.
L'app ricorda in questo browser se l'avevi lasciato aperto.

**Cio' che si apre si chiude come tutto il resto**: Esc chiude (prima il foglio Altro, poi
Stanotte), toccare il velo chiude, e il fuoco torna a chi l'aveva aperto.

**Sul telefono** il binario scende in basso con cinque schede -- Dashboard, Notti, Archivio,
Progetti, Altro -- e "Altro" e' un foglio che sale con la scansione e le altre pagine; Da
confermare porta il suo conteggio anche sulla scheda Altro. La barra in alto va su due righe, e la
seconda si ritira scorrendo in giu'. **Le misure si leggono dal contenitore**
(`.as-telaio-misura`), non dalla finestra: soglie 1440, 1180, 900 del foglio.

## Cosa NON fa

Non decide come le pagine sono fatte dentro: ogni pagina ha il suo contratto. Non calcola niente:
cio' che il telaio mostra -- quante cose da confermare, la fase del lavoro, il sito, la Luna --
arriva pronto dall'API. Non ha ancora la lingua e il tema al volo, ne' il tuo nome: il disegno
non li ha messi in barra, e tornano con Impostazioni.
