# Per Claude Design -- il primo avvio nel linguaggio bento, col tema

Da Claude Code, 17/10/2026. Il primo avvio e' la prima pagina che chiunque vede: oggi e' ancora
nel foglio vecchio (v33, `old/pagine/primo-avvio.html` e `primo-avvio-stati.html`). Si rifa' nel
linguaggio della v11, con i componenti e `astrolog.css`. In piu' **un passo nuovo: il tema**
(Marco, 17/10/2026).

Sotto c'e' esattamente cio' che l'app fa oggi, coi testi veri. Un passo o un dato che non sta qui
non va disegnato. I testi si possono migliorare nel tono del glossario: dite cosa cambiate, si
approvano con Marco prima del codice.

## 1. Cosa resta com'e'

- **Niente telaio**: niente barra in alto, niente menu. Sul desktop i passi stanno di lato
  (titolo "Primo avvio", sotto "Tutti i passi sono facoltativi.", poi l'elenco dei passi) e a
  destra la carta del passo. Sul telefono i passi in fila sopra, i gesti in una barra in fondo.
- **Elenco dei passi**: "Passo 2 di 5" e i nomi. Ogni tappa: fatta, quella dove sei, quelle dopo.
  Non sono bottoni: non si salta avanti toccandole. Non e' una barra di avanzamento.
- **Carta del passo**: titolo, una riga che dice perche' l'app lo chiede, i controlli, i gesti.
  Gesti: "Salta" a sinistra (lontano dal resto), "Indietro" (non al primo passo), "Avanti";
  all'ultimo "Fine". **Un solo primario a schermo**: se il passo ha un comando suo (Salva sito,
  Aggiungi cartella, Verifica e salva, Verifica percorso), quello e' pieno e "Avanti" scende a
  tenue.
- **Si salta sempre, da ogni passo, senza conferma.** "Salta" chiude il primo avvio ed entra
  nell'app; "Fine" passa dalla chiusura (punto 4).
- **Quanti passi sono si decide entrando** e non cambia a meta'.

## 2. I passi

Ordine: **Nome utente, Sito di osservazione, Tema, Cartelle, Seeing (Meteoblue)**, e **ASTAP**
solo a chi manca. Il tema sta dopo il sito perche' "Automatico" ha bisogno del sito.

### Nome utente
Perche': "Usato per intestare le statistiche." Campo "Nome", segnaposto "Nome", aiuto
"Facoltativo.".

### Sito di osservazione
Perche': "Serve a calcolare le notti e l'altezza degli oggetti. Altri siti si aggiungono dalle
Impostazioni."
1. **Cerca per nome**: campo "Cerca un luogo", bottone "Cerca". Risultati: "Risultati della
   ricerca", una riga per posto con nome e coordinate e "Seleziona"; quello scelto dice
   "Selezionato". Scegliere riempie nome e coordinate, che restano modificabili.
2. **Coordinate**, con "Inseribili anche senza connessione.": "Nome del sito" (segnaposto "es.
   Malga in quota"), "Latitudine" ("46,4843 N"), "Longitudine" ("12,0561 E"). Virgola o punto, e
   la lettera del verso.
3. **Bortle** ("Bortle, da 1 a 9"): nove classi, agli estremi "1 - cielo buio" e "9 - centro
   citta'". Scelta una classe: "Bortle 5 - cielo di periferia" e la sua frase. Nessuna scelta in
   partenza ("Nessuna classe selezionata."), aiuto "Facoltativo.".

Primario "Salva sito", spento finche' mancano nome e coordinate valide; salvato, va da solo al
passo dopo. Non si chiedono fuso, altitudine, misura del cielo.

### Tema (nuovo)
Le due scelte della v11: **modo** (Chiaro, Scuro, Automatico: scuro dal tramonto all'alba del
sito) e **accento** (originale, ambra · blu notte, turchese · petrolio, corallo · terracotta,
ghiaccio · indaco). Predefiniti: scuro, ambra · blu notte.
- **Si vede subito**: toccata una scelta, tutto il primo avvio prende quel tema. Niente bottone
  "Salva": vale cio' che e' scelto quando si va avanti.
- Ogni accento si riconosce senza leggerne il nome (un campione dei suoi colori nel modo scelto).
- **Automatico senza sito** (sito saltato): spento, con una riga che dice che serve un sito.
- Una riga di perche' corta, e che si cambia dalle Impostazioni.
- Disegnatelo come **componente**: lo stesso selettore va nelle Impostazioni (DECISIONI: "il
  selettore completo sta in Impostazioni; nella barra solo il modo").

### Cartelle
Due forme, l'utente ne vede una sola.
- **Sul computer** -- perche': "Indica una cartella: vengono lette anche le sottocartelle. Se ne
  possono aggiungere piu' di una." Campo "Percorso della cartella", bottone "Verifica".
- **Sul NAS** -- perche': "L'app e' in un container e vede percorsi diversi da quelli del
  computer. Seleziona la cartella dall'elenco." "Scegli una cartella", "Cartella corrente:" col
  percorso, "Seleziona cartella", "Cartella superiore", "Cartella dei dati"; l'elenco delle
  sottocartelle che scorre, ognuna con "Apri"; vuoto: "Nessuna sottocartella".

Dopo la verifica, l'esito: "File trovati" ("1.240 file FITS"); "Conteggio parziale" ("Conteggio
interrotto a 5.000: i file sono di piu'."); "Cartella non raggiungibile" ("Controlla il percorso o
collega il disco, poi riprova.", niente Aggiungi); "Cartella gia' registrata" con "Usa questo
percorso". Primario "Aggiungi cartella". Sotto, "Cartelle aggiunte", una riga per cartella.
NAS senza elenco: "Elenco delle cartelle non disponibile", "Inserisci il percorso." e il campo a
mano con "Percorso interno al container, non quello del computer."

### Seeing (Meteoblue)
Perche': "Con una chiave API Meteoblue il seeing e' disponibile ora per ora, per sette notti.
Senza chiave il resto del meteo funziona. Si puo' aggiungere dalle Impostazioni."
Stato ("Nessuna chiave: seeing non disponibile." o "Chiave salvata (termina con ab12)."), "Come
ottenere una chiave gratuita", campo "Chiave Meteoblue", primario "Verifica e salva", "Rimuovi
chiave". Esiti: "Chiave valida: seeing attivo.", "Chiave rimossa: seeing non disponibile.",
"Chiave non riconosciuta da Meteoblue: non salvata.", "Meteoblue non risponde: chiave non
verificata e non salvata.", "Risposta non valida da Meteoblue: chiave non salvata.".

### ASTAP (solo a chi manca)
Pastiglia accanto al titolo: "Non trovato" o "Catalogo mancante". L'app non scarica e non
installa niente.
- **Non trovato** -- perche': "ASTAP non e' installato. E' il programma che identifica il campo
  inquadrato dalle stelle (plate solving). Si puo' installare anche dopo." Gruppi: "Senza ASTAP"
  ("I file vengono catalogati e le ore contate, ma gli oggetti ripresi non vengono
  identificati."), "Download" ("Scarica ASTAP dal sito dell'autore", "L'app non scarica ne'
  installa ASTAP."), "Gia' installato" (campo "Percorso di ASTAP", segnaposto
  `C:\Program Files\astap\astap_cli.exe`, aiuto "Percorso del programma (astap_cli), non della
  cartella.", primario "Verifica percorso").
- **Catalogo mancante**: avviso "Catalogo stellare mancante", "Scarica il catalogo stellare" e
  quale prendere. Qui il percorso non si chiede.
- Esiti: "ASTAP trovato" ("Gli oggetti ripresi verranno identificati."); trovato ma senza
  catalogo (non e' il caso buono: va distinto); "ASTAP non trovato in questo percorso. Il
  percorso deve terminare con il programma (astap_cli)."

## 3. Stati

- **Comuni**: "Salvataggio non riuscito" nel passo che l'ha provocato, e ci si resta; il bottone
  al lavoro mentre salva o verifica.
- **Sito**: ricerca in corso; "Nessun risultato. Controlla il nome o la connessione, oppure
  inserisci le coordinate."; "Ricerca non riuscita" ("Il servizio non ha risposto.") con
  "Inserisci le coordinate"; sotto il campo "Coordinata non valida. Esempio: 46,4843 N",
  "Valore fra -90 e 90" (180 per la longitudine), "Nome obbligatorio"; "Sito non salvato".
- **Backup trovato**, prima di tutto (stessa colonna senza telaio): "Backup trovato", "Ultimo
  backup: ..." e i conti (conferme, siti, cartelle, strumenti e filtri), "Ripristinare i dati
  salvati? Le cartelle verranno rilette.", "Ripristina" e "Inizia da zero".

## 4. La chiusura

Dopo "Fine": "Primo avvio completato" e cio' che e' vero, una riga per voce: Nome utente (o "Non
indicato"), Sito di osservazione ("Cima Ekar · Bortle 4" o "Nessun sito"), **Tema** (nuovo:
"Scuro · ambra · blu notte"), Cartelle ("3 · scansione avviata" o "Nessuna"), Seeing ("Chiave
salvata" o "Senza chiave"). Una riga che non si e' potuta leggere si tace. Bottone "Apri AstroLog".
Con almeno una cartella la scansione parte da sola.

## 5. Tre difetti di oggi, da risolvere nel disegno

- **Un passo saltato risulta "fatto"**: l'elenco segna fatta ogni tappa gia' passata, anche con
  Avanti senza salvare. Serve un terzo segno, **saltato**, distinto da fatto.
- **La scansione che non parte non si dice**: oggi la chiusura tace e basta. Serve lo stato
  "Cartelle: 3" con una riga che dice che la scansione non e' partita e che si avvia da Scansiona,
  nel menu dell'ingranaggio (proponete la frase).
- **Telefono**: campi a 16 px almeno (sotto, iOS ingrandisce la pagina al tocco); bersagli da 44;
  latitudine e longitudine, la scala di Bortle a nove voci, il percorso lungo del NAS e i cinque
  accenti a 390 px.

## 6. Consegna

Pagina `pagine/Primo avvio.dc.html` (Tweaks: passo, stato, formato, modo, accento) e la tavola
degli stati, desktop 1440 e telefono 390, coi componenti e le classi di `astrolog.css` (le classi
nuove li', come le altre). Il selettore del tema come componente, anche in Sistema. Poi CHANGELOG
v12, DECISIONI, e via `old/pagine/primo-avvio*.html` e `old/docs/proposte/primo-avvio.js`.
