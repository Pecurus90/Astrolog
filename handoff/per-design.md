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

- [da dare] Foglio vecchio, commento di `.as-bortle-letta` (`foglio/48-bortle.css`, Issue #28 e
  #71): cita ancora i pavimenti di Wikipedia (1 = 21,76 ... 8 = 17,00); le tavole usano ASTAP dal
  23/10 (`soglie.js`), il foglio no. Va riscritto coi pavimenti di ASTAP e l'esempio «Bortle 4
  (21,4)»: testo intero in `handoff/design-bortle-astap.md`. Finche' non arriva, l'app non passa
  alla tabella di ASTAP e lo SQM delle Notti resta senza classe (Marco 14/11: si da' a Design).
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
