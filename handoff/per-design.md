# Per Claude Design -- la coda

Ogni richiesta per Design entra qui nel momento in cui nasce, mai solo in chat (Marco, 6/11/2026).
All'avvio di ogni sessione `tools/stato.py` conta le voci e dice se in `handoff/design/` c'e' una
consegna nuova.

**Come si usa.** Marco incolla a Design le voci `[data]` e dice «dato»: diventano `[data]`.
Quando la consegna nuova arriva in `handoff/design/`, Claude Code controlla ogni voce `[data]`
sulle tavole: `[fatta vN]` se c'e', di nuovo `[data]` con cio' che manca se no. Le voci fatte
escono alla consegna dopo. Il testo lungo di un brief sta nel suo file accanto (`design-v59.md`).

Consegna controllata: b173aada (v82, 11/11), in `handoff/design/` al posto della v79.

## Da dare

- [da dare] Meteo, carta Condensa e cielo della notte (passo 15, 24/11): la soglia non e' piu' 3
  gradi fissi ma una **per ora** (modello di Beysens: nuvole, vento, quota del sito). L'app oggi:
  scarto con un decimale; sotto il valore «sotto la soglia di 4,9 °C dalle 22:00» o «mai sotto
  la soglia, al più 4,9 °C»; con la condensa accesa a destra una **linea tratteggiata «Soglia di
  rugiada»** nel grafico, in legenda e nel lettore dell'ora. Senza quota del sito la nota della
  carta aggiunge «quota del sito non nota: soglia calcolata al livello del mare»: Marco vuole li'
  un **link alle Impostazioni del sito**, che la nota di CardMeteo (solo testo) non permette. Da
  disegnare: la linea della soglia (desktop e telefono) e il link nella carta.
- [da dare] Meteo, carta Campionamento (passo 14, 24/11): ogni casella di setup ha ora, dopo la
  pillola del campionamento, una **seconda pillola** «seeing buono / incerto / non adatto» (il
  seeing rispetto al limite del setup, ADR 0039; Marco: per ogni setup) e, sotto la nota «ottimo
  con seeing fra…», una seconda nota «limite del setup 0,7″»; senza apertura dell'ottica la nota
  dice «seeing: manca l'apertura dell'ottica» e la seconda pillola non c'e'. Sul telefono le due
  pillole stanno a destra una sopra l'altra (affiancate stringevano le righe del setup) e il
  limite e' una riga sotto la scala. Da ridisegnare nella
  tavola Meteo (righe 80-83 e 152), desktop e telefono, coi setup veri dei dati simulati.
- [da dare] Riquadro della scansione nel menu dell'ingranaggio (Issue #20, 18/11): (a) la catena
  delle fasi -- oggi il riquadro dice solo la fase corrente («Lettura dei file»), il backend sa
  tutte le fasi della corsa (lettura, impronta, cielo, oggetti, notti) con fatto/in corso/da fare;
  serve il disegno di come si vedono insieme, desktop e telefono. (b) La ricevuta dell'ultima corsa
  (file trovati, nuovi, invariati, doppioni, mancanti, saltati, errori, per cartella) e il caso
  «cartella ritirata» (non si segue piu'): dove sta e come si apre. (c) Lo stato «interrotta» non
  c'e' nella tavola: l'app dice la fase dove si e' fermata, poi il giorno e l'ora («Lettura dei
  file · ieri, 07:40»); confermarlo nella tavola.

- [da dare] Primo avvio, il guscio (passo 33 B, collaudo 16/11): (a) stato «lettura delle
  impostazioni» a 1440: lo Scheletro (`appSk`, riga 186) esce in due colonne strette affiancate e
  «Leggo le impostazioni…» si taglia; sul telefono e' giusto. L'app lo copia com'e'. (b) La data
  di «Backup trovato» nell'app ha il mese corto («16 nov 2026, 17:37»), come in tutta l'app; la
  tavola «12 ottobre 2026». Allineare la tavola. Dettaglio in `differenze-dalle-tavole.md`,
  «Primo avvio -- il guscio».

- [da dare] Impostazioni, Servizi, Scansioni e Backup (passo 33 E, 16/11): (a) le chiavi dei
  servizi stanno nel file delle risposte accanto al database e tornano dopo un database rovinato;
  solo Esporta non le porta (Marco 16/11, ADR 0017): l'intro di Servizi dice «non vanno nel file
  esportato», la nota di Backup «Il file porta le risposte e le impostazioni. Esporta non porta le
  chiavi dei servizi né il percorso di ASTAP; ...»; (b) superata il 23/11: l'app stima il seeing
  dal jet e usa la frase della tavola; (c) «doppioni dello stesso
  file» e' «duplicati» (glossario); (d) la proposta «Ho trovato le tue risposte del ...» sta nel
  Primo avvio, non dentro Backup (la tavola la segna «Al primo avvio»); (e) l'esito di Verifica sta
  sotto la riga della chiave finche' «Ultimo tentativo» non e' vero; Cambia apre il campo con
  Annulla; (f) le regioni delle scansioni hanno bisogno di nomi unici e la barra di un nome (axe).
  Allineare la tavola. Dettaglio in `differenze-dalle-tavole.md`, «Impostazioni -- Servizi,
  Scansioni, Backup».

- [da dare] Impostazioni, Cartelle e ASTAP (passo 33 D, collaudo 15/11): (a) un percorso lungo
  senza spazi nei testi di `Avviso` («Stessi file in C:\...», il percorso di ASTAP) spinge la pagina
  di lato sul telefono: serve `overflow-wrap: anywhere` sui testi di `.al-c-avviso__*` e sulla riga
  «Il nuovo percorso di ...» di `.al-imp__cart-pannello`; l'app lo mette inline finche' il foglio
  non lo ha. (b) La classe `al-imp__cart` della tavola (righe 111, 310) non c'e' nel foglio. (c) La
  pillola «5°» della Luna sul telefono e' larga 41 px, sotto i 44. Differenze in
  `differenze-dalle-tavole.md`, «Impostazioni -- Cartelle e scansione, Meteo, ASTAP, Luna».

- [da dare] Impostazioni, Siti (passo 33 C, collaudo 15/11): sul telefono le quattro vie del cielo
  e le nove classi di Bortle sono alte 36 px (`.al-imp__riga-18`, tavola 274-275): sotto i 44 px.
  L'app le porta uguali alla tavola finche' il foglio non cambia. Le differenze della sezione in
  `differenze-dalle-tavole.md`, «Impostazioni -- Siti».

- [da dare] Attrezzatura, modulo di un pezzo (passo 33 D, Marco 14/11): (a) il bias della camera
  e' uno per offset dei file: un campo per offset «Bias (ADU), offset 50», «Bias (ADU)» se
  l'offset e' uno, «Bias (ADU), senza offset» se i file non lo scrivono; nella scheda «bias 500
  ADU, offset 50». (b) Elimina spento per l'ottica o la camera di un setup senza frame, con «Fa
  parte di {setup}: un setup è fatto della sua ottica e della sua camera.» (la tavola non ha il
  caso). (c) Prima di Salva niente riga «N frame da rielaborare: cambia il cielo dei frame»: il
  numero arriva dopo, ed e' solo quello vero. Dettagli in `differenze-dalle-tavole.md`.

- [da dare] Dashboard, dettaglio della Luna (Dashboard 624, Issue #70): la parentesi «(le soglie
  stanno nelle Impostazioni, gruppo Luna)» non e' vera. I gradini 25/65 del calendario vengono
  dalla scala della Luna del Meteo, fissa; le Impostazioni (25% o 4 h senza Luna) decidono solo la
  notte buona per la banda larga, che la Dashboard non mostra. Marco 13/11: l'app scrive «(le
  soglie vengono dalla scala della Luna del Meteo)»; la tavola si allinea.
- [fatta v82] Dopo la v81 (Marco, 11/11: tutto IAU): i nomi delle stelle della Carta del cielo
  con i nomi propri IAU (WGSN: Polaris, Sirius, Arcturus), uguali in ogni lingua come le
  costellazioni latine; anche nella descrizione della scala di Bortle del Primo avvio
  «Pleiades» al posto di «le Pleiadi».
- [fatta v82] Dopo la v80 (Marco, 11/11: si' a tutte e due): (a) i circa 150 attributi SVG col
  segnaposto nelle altre tavole (Archivio, Menu, Planner, Statistiche e le altre): stessa cura
  di Cerca e Telaio, l'icona nasce gia' col suo disegno; nessuna tavola, aperta da sola, da'
  errori in console. (b) I nomi comuni scritti a mano in italiano (Progetti, Cerca, Primo avvio,
  Da confermare, Selezione, Planner, `cupola.js`, `dati-cielo.js`) si leggono da `catalogo.js`:
  costellazioni latine IAU, nomi comuni in inglese, come l'app. (c) La proposta dei filtri oltre
  cinque (prime quattro per ore, «altri N filtri» con la somma, poi «Filtro non indicato», ogni
  filtro con la sua fetta nell'anello) va bene: disegnarne lo stato, desktop e telefono, nella
  tavola «Dashboard stati».
- [fatta v82] Errori delle tavole v79 (collaudo 11/11): il `sc-if` attorno ai `<path d="{{ … }}">`
  non basta, il browser legge il segnaposto prima del runtime. `componenti/Cerca.dc.html` da'
  `<path> attribute d` con `{{ a.d }}` e `{{ g.d }}`; `componenti/Telaio.dc.html` ancora i quattro
  `{{ m.altroChev }}`, `{{ m.modeIcon }}`, `{{ vb.az.d }}`, `{{ b.d }}`. Solo tavola: l'app non li ha.
- [fatta v82] Archivio, porting v78 (10/11): (a) il campo dice «Cerca: M 31, Velo, Andromeda…», ma
  la ricerca trova sigle e nomi dell'oggetto, non i nomi comuni: l'app scrive «Cerca: M 31, NGC
  7000…»; (b) le costellazioni nell'app sono latine IAU (Cepheus, Cygnus), decisione di Marco
  confermata il 10/11: catalogo.js le ha in italiano; (c) i nomi comuni arrivano dal catalogo in
  inglese («Andromeda Galaxy»); (d) Sole, Sistema solare e Aggiungi oggetto restano fuori finche'
  non c'e' una sorgente (ADR 0019). Allineare la tavola.
- [da dare] Da confermare, porting delle domande (12/11): (a) «Perche' l'app dubita» dice due
  righe, «metodo: plate solving» (o «nome nei file», «nome storico nei file») e «fiducia bassa» o
  «alta» (Marco, 12/11): la fiducia «media» e la frase dopo i due punti non esistono; (b)
  l'aiuto del mosaico dice il nome proposto («Nome proposto dall'app: Sadr. Si cambia.»): il
  backend propone l'oggetto di catalogo al centro, non sempre quello con piu' frame; (c) il campo
  Ottica accanto ad «Altra camera» c'e' solo se la scheda non chiede l'ottica a parte; (d) Frame
  senza data senza sito dichiarato: «La notte comincia la sera di quel giorno.»; (e) gli oggetti
  identificati vengono nell'ordine dell'API, piu' frame prima; (f) errore della tavola, uguale
  nell'app: nella risposta scelta (`al-scelta--risposta`, `aria-checked`) il tondo e la riga
  sotto quasi spariscono, bordo `rgb(31,20,6)` su fondo `rgb(24,24,28)` (si vede in «Resta M 31»).
  Allineare la tavola. Dettaglio in `differenze-dalle-tavole.md`.
- [da dare] Attrezzatura, porting del dettaglio del setup (13/11): (a) le schede scrivono i numeri
  col punto («pixel 3.76 µm», `vir`): la virgola, come il resto; (b) una parte scelta a mano sta
  accanto ai pezzi che i file nominano, ognuno coi suoi frame (fuori dalla montatura la scelta vale
  solo dove il file tace); (c) il programma di ripresa non ha «Seleziona»: lo dicono solo i file;
  (d) cio' che manca a un conto e' il primo dato che manca («manca il pixel della camera» anche
  nel rapporto guida/ripresa); (e) nel confronto dei campi l'etichetta e' il `title` dell'API
  (nome, modello o nome senza la marca scritta sul pezzo, senza lista di marche): un nome lungo
  («Askar 103Apo · ATR2600M») esce dal riquadro piccolo e copre la Luna. Disegnare l'etichetta
  lunga su un campo stretto. Allineare la tavola. Dettaglio in `differenze-dalle-tavole.md`.
- [da dare] Attrezzatura, porting del treno ottico (14/11): (a) `@keyframes alDraw` (il treno che
  si disegna in 0,9 s) vive solo nell'helmet delle tavole, non in `astrolog.css`: portarlo nel
  foglio coi movimenti nominati (riga 542 e seguenti), col movimento ridotto; (b) nell'app il
  disegno legge lo schema ottico della scheda: un obiettivo fotografico o «altro» si disegna
  rifrattore come uno schema non scritto; se serve un disegno suo, disegnarlo; (c) nomi lunghi
  (driver ASCOM): la tavola spinge la prima pillola fuori dal riquadro a sinistra; l'app (Marco,
  14/11) passa ai numeri con la legenda del telefono anche sul desktop. Disegnare lo stato.
- [da dare] Attrezzatura, «Aggiungi strumento» coi tasselli (17/11): (a) coi tasselli in vista la
  tavola disegna anche il contenitore dei blocchi vuoto (`blocchi: []` e' vero per `sc-if`), 18 px
  in piu' prima di Salva; l'app non lo disegna; (b) nel filtro nuovo «Quante bande» non ha
  nessuna pillola scelta mentre una banda e' gia' in vista: l'app sceglie «1». Allineare la tavola.
## Date, da controllare alla consegna

- [fatta v82] Dashboard, Il 2026 e Filtri del 2026 (porting 11/11): (a) «4.6» col punto e' un
  errore: «4,6»; (b) i frame senza filtro sono l'ultima riga «Filtro non indicato» col pallino a
  filo tratteggiato e un pezzo grigio dell'anello: disegnarli; (c) l'app elenca tutti i filtri
  dell'anno: dire se e dove tagliare; (d) senza notti nell'anno prima ne' tratteggio ne'
  confronto; (e) anno senza ore: zeri, media «—», «Nessuna posa nel 2026, per ora.» al posto
  dell'anello (Marco); (f) l'anno che non risponde: Avviso riga; (g) un filtro a colori
  nell'anello e' tre fette R, G, B (la strisciata del foglio nel conic-gradient lo cancella);
  (h) a 700 px le etichette dei mesi si accavallano («marapr»), anche in tavola; (i) a 860 e
  1280 lo scarto «−2 h 20» va a capo a meta'. Disegnare (d), (e), (f) negli stati. Dettaglio in
  `differenze-dalle-tavole.md`.

## Fatte

Le sette voci del 10/11 (brief archiviato in `handoff/design/docs/archivio/brief-porting-v78.md`)
sono fatte nella v79, portate nell'app l'11/11: fonte del sito fuori dalla pillola, striscia da
176 px, Impostazioni/Primo avvio/Sistema misurate (Sistema non e' una pagina dell'app), calendario
delle Notti sulla riga intera, sito lungo in Tutto della notte e Cerca, icona della scheda
(`frontend/src/icona.svg`, `icona-16.svg`, Issue #56). Gli errori delle tavole restano: in «Da dare».

Le tre voci date il 10/11 sono fatte nella v78, controllate nell'app e sulle tavole il 10/11 (a
700, 760, 860, 960, 1000, 1100, 1280, 1440 e 390 nessuno scorrimento di lato, nemmeno con la barra
vera): pagine fra 700 e 1000 px, sito dal nome lungo, errori della tavola v77 (lo schermo alto 0
di `Riepilogo stati` non ricontrollato: pagina non ancora portata). I resti sono in «Da dare».

Le 14 voci date il 10/11 sono fatte nella v77 (brief archiviato in
`handoff/design/docs/archivio/brief-porting-v76.md`).

- Resta per il porting, non per Design: le etichette degli assi di Statistiche 446 e 449 usano
  `toFixed(1)` col punto; nell'app i numeri li formatta il frontend con la virgola.
- Risposta a Design (v68): le quattro vie del cielo del sito sono quelle dell'app (Dalle misure =
  `frames`, Bortle a mano = `scale`, SQM a mano = `measured`, Dalla mappa = `service`; `sito.md`
  74-76); il servizio e' quello della mappa della luce artificiale.
