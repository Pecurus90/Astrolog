# AstroLog — le decisioni prese

Le decisioni del vecchio sistema (fino alla v38) stanno in
`old/docs/DECISIONI.md`. Qui solo quelle del linguaggio nuovo.

> Dalla v10 le parole sono quelle del glossario dell'app anche nelle sezioni vecchie; dove una regola e' cambiata, la sezione rimanda a v10 o v11. Una versione sola.

## Da fare dopo v49

1. Marco guarda il porting (desktop e telefono) e lo approva.
2. Si cancellano `PianoColonna` e le tavole di prova (`Planner proposte`, `Telefono comandi`, `Telaio vivo`); `Planner telefono` e `Planner desktop` restano finche' Marco non approva.
3. Sistema solare ed Eventi nella stessa forma; il modo si sceglie nella pagina «Cielo».
4. Carta «È stagione» nella Dashboard (progetti salvati, per priorita').
5. Poi si cancellano le tavole di prova: `Planner proposte`, `Telefono comandi`, `Telaio vivo` (restano `Planner telefono` e `Planner desktop` come riferimento finche' il porting non e' fatto).

## v57 — Planner, Sistema solare ed Eventi nella forma del cielo profondo (25/10/2026, Marco: «vai»)

Brief in `docs/archivio/brief-planner-solare-eventi.md` (i cinque punti scelti da Claude, approvati da Marco). Componenti `PlannerSolare2` e `PlannerEventi2`, riscritti; il Planner passa solo i dati.

- **Desktop**: in alto le linguette Cielo profondo · Sistema solare · Eventi, poi il cielo largo e la colonna di 424 px, a tutta pagina come la fase di Aladin. Sul cielo una sola riga di comandi: la pillola del corpo (o dell'evento) con l'altezza adesso, «Setup ▾», a destra Luce bianca · Hα (Sole), − +, Adatta. In basso il righello della rotazione e la tessera Mosaico (Luna e Sole), come nel cielo profondo.
- **Sistema solare, colonna**: Quando (il momento migliore, numero protagonista, col seeing; la curva d'altezza; data, −1 g −1 h +1 h +1 g, Adesso; la prossima opposizione o elongazione), Ripresa (diametro, scala, campo, rapporto focale, video al massimo, Barlow −/+, filtro, la ripresa salvata), in fondo Salva o «Apri in Progetti ↗». Il Setup virtuale si apre in testa a Ripresa.
- **Eventi, colonna**: il conto alla rovescia protagonista («fra 7 h 36 min»), l'ora al secondo e la durata, la striscia (✓ dentro / ! fuori di n km), Parti alle, altezza, meteo all'ora; poi Dettagli; in fondo «Aggiungi al piano» o «Nel piano di stanotte ↗». L'elenco degli eventi si apre dalla pillola sul cielo, con Tipo ▾ e Periodo ▾; i passati in fondo, spenti. Sul cielo in basso i momenti dell'evento (parti, entra, esce…).
- **Telefono**: cielo a tutto schermo; in alto il modo in tendina («Sistema solare ▾», «Eventi ▾») e il corpo o l'evento, sotto Setup e lo zoom; righello e Mosaico, bolla delle pagine e barra col momento migliore (o il conto alla rovescia) e l'azione; foglio a tre altezze con le linguette Quando · Ripresa o Evento · Dettagli. Mentre il dito tocca il cielo i comandi si ritirano.
- **Dati come il Piano della notte**: ISS sulla Luna giovedì 1 ottobre alle 03:41:12, 0,8 s, ripresa dalle 03:36 per 10 minuti; Macchia Rossa al meridiano 05:20; riprese salvate di Luna (R, 4000 frame · 5 ms · 50 fps, 12 pannelli), Giove (R G B, 3000 · 8 ms · 50 fps, 640 × 480 px), Saturno (R G B, 3000 · 12 ms · 50 fps, 800 × 600 px).
- **Nuovo**: lune di Giove sul disegno (posizioni simulate); eventi «Ombra di Io su Giove», «Luna e Giove a 2,1°», un transito della ISS fuori dalla striscia, uno passato. Numeri con la virgola.
- **Sistema solare, completato sul brief** (v57.1): la finestra utile nella frase sotto l'ora migliore («Finestra utile 03:20 – 07:35, 4 h 15 min sopra 30°»); il seeing ora per ora resta nelle barre della curva; Le prossime notti, cinque caselle (ora migliore, altezza, seeing dove c'e' la previsione di 3 giorni) con ‹ › per il giorno; frame · posa · fps calcolati per i corpi senza ripresa salvata («Ripresa consigliata · calcolata»). Porta l'ora lì accanto al numero, −1 h +1 h Adesso accanto alla data. Sul desktop Quando e Ripresa scorrono insieme; Salva resta in fondo.
- **Immagini dei corpi** (Marco): nell'app Sole, Luna e pianeti saranno immagini vere in alta risoluzione. I dischi disegnati e le immagini di rete della tavola (SDO, GONG, LROC, Viking) tengono solo il posto; restano la scala, la fase, la rotazione e il campo del setup sopra l'immagine.
- Superate le forme A/B di v43–v44 (tolti il Tweak `eventi` e `?eventi=riga`). Per le tavole: `?pianifica=solare` o `?pianifica=eventi`.
- Controlli: 1440 × 900, 1280 × 800, 390 × 844; bersagli del telefono tutti da 44; contrasto della colonna nei due modi coi cinque accenti.

## v58 — Transiti dei satelliti con la mappa (25/10/2026, Marco: «vai»)

Marco toglie dal «cosa non c'e'» la mappa a terra. Brief in `docs/archivio/brief-planner-solare-eventi.md`.

- **Satelliti**: ISS, Tiangong, Hubble, davanti al Sole e alla Luna. Il tipo si chiama «Transiti dei satelliti».
- **Disco · Mappa**: per i transiti, sul cielo, a destra della riga dei comandi. La mappa e' OpenStreetMap (Leaflet), pagina a parte `Mappa del transito.html` dentro il cielo: la striscia, la linea centrale tratteggiata con le frecce del passaggio, il sito, i posti numerati. Niente vista satellite: OpenStreetMap e basta. Google Maps dentro l'app no (chiave a pagamento): lo apre il bottone.
- **Dove metterti**, in testa a Dettagli: lo stato del sito («Cima Ekar: dentro la striscia, a 800 m dalla linea centrale» o «fuori di 900 m: spostati verso nord-ovest»), il piano B se al sito e' velato e altrove sereno, tre posti. Ogni posto: distanza dalla linea, minuti d'auto dal sito, orizzonte verso il corpo, meteo all'ora. Il posto scelto ha «Apri in Google Maps ↗» e «Sulla mappa». Scelta legata nei due versi: tocchi il numero sulla mappa e si sceglie la riga, e viceversa.
- **Come si scelgono i posti**: prima il sito salvato se e' dentro; poi dentro la striscia, entro un'ora d'auto, orizzonte libero, sereno. Conti in `componenti/transiti.js`, uguali per Planner e mappa. Posti e tempi simulati, dichiarati («posti simulati»).
- **Telefono**: mappa a tutto schermo, «Dove sono» mostra la posizione (simulata) e lo stato sul posto.
- **Con gli eventi**: «Orologio del computer: 0,3 s avanti» (simulato) per i transiti; «Aggiungi al calendario» (file .ics) per ogni evento futuro, al posto delle notifiche.
- **Crediti e colonna** (Marco, v58.1): i crediti delle immagini in una riga sola, piccola, sotto i momenti dell'evento o sotto il righello, centrata; sul telefono sopra la barra. La colonna degli Eventi scorre tutta insieme come quella del Sistema solare; l'azione resta in fondo.
- **Telefono, il bordo del foglio** (Marco, v58.2): la barra in basso non e' piu' una carta di vetro: e' il bordo del foglio che spunta dal fondo, a tutta larghezza, con la maniglia in alto, il numero e l'azione; la bolla delle pagine ci sta sopra a sinistra. Si tocca o si tira su (meta' foglio, o tutto se si tira tanto).
- **Barlow scrivibile** (Marco, v58.2): fra − e + il fattore si scrive (da 0,5 a 5, con la virgola); sopra, «Barlow o riduttore · Barlow / riduttore / nessuna».
- **Sequenza per SharpCap** (Marco, v58.3): nel Sistema solare una carta «Sequenza» dopo Ripresa (sul telefono la terza linguetta): la riga del tempo coi video in fila, colorati per filtro, centrata sull'ora migliore e dentro la finestra; filtri a pillole (R G B L IR CH4 con la camera mono; Colore e IR a colori; Luna e Sole i loro), «Un video» in secondi scrivibile con − +, al massimo il limite di rotazione; Cicli − +; cambio filtro 15 s e spostamento fra pannelli 10 s da Impostazioni › Planner; frame, area e GB su disco. Luna, Giove e Saturno partono dalla ripresa salvata (80 s, 60 s, 60 s; area 640 × 480 e 800 × 600). Negli Eventi la stessa carta per transiti, eclissi, occultazioni e lune di Giove: i video attorno ai momenti (ISS: dalle 03:36 per 10 minuti, come il Piano della notte), il segno dell'ora dell'evento sulla riga. «Esporta per SharpCap» come nel Piano della notte: «✓ Esportata alle 20:05», e le stesse avvertenze col «!». Esportazione simulata.
- **Numeri della sequenza** (v58.3, dal controllo): la Luna parte dai 12 pannelli dal terminatore della ripresa salvata, ogni pannello in un'area 1920 × 1080 px (a 50 fps il sensore intero non ci sta): circa 100 GB. Senza mosaico, l'area attorno al disco. La ISS e' un buffer circolare di 10 minuti che salva 20 s attorno al transito, area stretta sulla traccia: circa 1,6 GB.
- **Controllo d'insieme** (v58.3): i bottoni delle caselle (le prossime notti, i posti, i sensori) passano alle classi dell'app (al-bottone--riga, --tenue --icona).
- **Telefono, i tre modi uguali** (Marco: «ok», v58.4): anche il cielo profondo passa al bordo del foglio (via la barra di vetro e la linguetta «⌃ Piano»); la bolla delle pagine sopra, il Salva tondo in accento, spento in carta-2. Sistema solare ed Eventi hanno al primo avvio «Come si usa», come «Come si inquadra» del cielo profondo, ognuno con la sua chiave (si chiude con «Ho capito» e non torna).
- **Pulizia per Claude Code** (Marco, v58.5, 26/10/2026; regole del brief v1 sez. 3 e v56.19):
  - Usciti: `componenti/PlannerSolare` e `componenti/PlannerEventi` (superati da PlannerSolare2 e PlannerEventi2; Sistema mostra i nuovi), `pagine/Cattura.dc.html` (serviva alle catture del riordino, che non ci sono piu').
  - In archivio: `brief-planner-solare-eventi.md`, `per-claude-code-selezione-frame.md` (chiusi).
  - Codice spento tolto (dichiarazioni mai lette): Archivio, Attrezzatura, Dashboard, Meteo, Notti, Planner, Selezione dei frame, Statistiche, MisureFrame, PlannerSolare2 (la vecchia scheda del setup, `curvaT`, `fattore`), Striscia, cupola.js. Props mai lette: `sito` in Menu e PlannerSolare2, `corOpz`.
  - Token nuovi nel foglio: `--vetro`, `--vetro-bordo`, `--vetro-filtro`, `--cielo-testo-2`, `--cielo-fondo`, `--ombra-vetro`, `--ombra-finestra`, `--ombra-foglio`, `--ombra-bordo`, `--cielo-scurisci`; classi `al-vetro`, `al-vetro--alto`. `al-bottone--vetro` li usa. Nei due Planner nuovi e nel Planner restano a mano solo le ombre del testo sul cielo e i colori del disegno (dati).
  - Resta: un `support.js` per cartella (radice, `pagine/`, `componenti/`): lo scrive l'ambiente di Design e ogni pagina lo cerca accanto a se'; nel porting non serve. Resta per Claude Code: i bottoni del cielo profondo con lo stile nella pagina (v54.2).
- **Consegna a Claude Code** (Marco, v58.6, 26/10/2026): `docs/per-claude-code-porting.md` (foglio, pagine coi componenti e gli indirizzi, il Planner, cosa e' simulato, cosa non si porta). Sistema: il «Vetro sul cielo» e le forme del telefono dei Planner, con «Desktop ↗» e «Telefono ↗» per i due Planner. Il cielo profondo: le tendine sul vetro passano a `al-bottone--vetro`, i bottoni chiari delle strisce a `al-bottone--velo` (nel foglio). Superata la nota v54.2 sui bottoni del cielo con lo stile nella pagina.
- **Prossimi, dalle proposte del 25/10** (Marco: «mi piacciono tutte»): seeing del sito imparato dalle riprese; sequenza per SharpCap (filtri e minuti entro la rotazione); Luna, le formazioni sul terminatore; Sole, regioni attive e protuberanze; Giove, lune ombre ed eclissi; il confronto con le tue riprese migliori; la stagione; quanto regolare l'ADC; le eclissi con le pose per fase; «dopo l'evento», il video collegato dall'Archivio.

## v56.43 — Fine fase (25/10/2026, Marco: «ci siamo»)

Tutte le pagine fatte col giro di allineamento, desktop e telefono. Prossima fase, in una conversazione nuova: il Planner del Sistema solare e degli Eventi; brief in `docs/archivio/brief-planner-solare-eventi.md`.

## v56.39 — Planner, primo giro (25/10/2026, Marco: «passiamo al Planner»)

Inventario: 118 bottoni e link, quasi tutti gia' coi mattoni comuni (al-bottone --scelta, --cielo, --vetro, --tenue, --icona); solo 2 con lo stile scritto. 12 gruppi di scelte con lo stile scritto nella pagina.
Fatto:
- Tutte le scelte del Planner (viste, Stanotte · Le mie riprese, setup da confrontare, riduttore, camera, sovrapposizione, schema dei filtri, priorita') con l'anello, non piene: sul cielo l'anello dell'accento del cielo.
- Desktop, «Cielo profondo · Sistema solare · Eventi» in linguette sottili (come il telefono).
- «← Cielo» non e' piu' pieno nell'accento: bottone di vetro (e' un ritorno, non l'azione principale).
- La carta Stanotte sul cielo (desktop) parte chiusa: una pillola di vetro «Stanotte · dov'e' adesso 77° N ▾» in alto a destra, sotto Immagine e Adatta; si apre a 300 px e si richiude da «Stanotte ▴». Cosi' non copre il campo, la maniglia ne' la riga del centro (v56.40).
- La pillola del nome (IC 1396 · nome comune · altezza) non sborda piu' sull'«Immagine ▾»: si stringe col nome comune che finisce in «…»; causa vera: la colonna di sinistra (← Cielo, nome, Setup) e quella di destra (Immagine, Adatta, Stanotte) erano due riquadri assoluti che si ignoravano. Ora sono una sola riga flessibile in alto: a sinistra si stringe solo il nome comune (l'id «IC 1396» resta intero), a destra Immagine · Adatta su una riga sola; la pillola «Stanotte ▾» (corta) sta accanto a «Setup ▾». Al massimo due righe di comandi a 1280 e 1440, cosi' la maniglia del campo resta libera (v56.42).

## v56.38 — Impostazioni (25/10/2026, Marco: «prossima pagina»)

- Le sezioni (Generale · Siti · … · Backup) e tutte le scelte della pagina (Modo, Dove sono i file, Meteo apre su, le scelte delle righe) in linguette sottili.
- I siti (Cima Ekar · Casa) e le altre pillole della pagina: la scelta con l'anello nell'accento, non piena.
- Desktop: niente titolo grande «Impostazioni» (resta per la voce); resta il sottotitolo della sezione.
- Gia' a posto: sul telefono l'indice delle sezioni con ↗; i colori d'accento con l'anello sulla scelta.

## v56.37 — Da confermare (25/10/2026, Marco: «stesso lavoro»)

- Le risposte (Filtro esistente · Modello da catalogo · Nuovo filtro, e le altre «risposta») scelte con l'anello nell'accento, non piene; vale in tutta l'app.
- Telefono, i tipi di domanda: «›» in fondo diventa il piccolo tondo ↗.
- Gia' a posto: «N da applicare · Applica» nel vetro accanto alla bolla; esiti coi colori fissi (senza risposta, da applicare, salvate); niente bollino nella sua pagina.

## v56.36 — Attrezzatura chiusa (25/10/2026, Marco)

- Gia' in linea (anello sul setup, niente titoli doppi). I gruppi dei componenti restano pillole con l'icona sul desktop e righe dell'indice sul telefono: sono un indice con i simboli dei pezzi, solo di questa pagina; eccezione voluta.
- Fatte: Dashboard, Notti, Archivio, Progetti, Statistiche, Meteo, Piano della notte, Selezione dei frame, Misure dei frame, Attrezzatura. Restano: Da confermare, Impostazioni, Planner.

## v56.33 — Misure dei frame (25/10/2026)

- Il componente MisureFrame era gia' a posto (v56.4–v56.9). Nella pagina: le produzioni dell'Archivio («Produzione») in linguette sottili.
- La misura scelta (prima) ha solo l'anello nell'accento, il fondo resta carta-2 (Marco: niente fondo giallo); la seconda resta tratteggiata.
- In fondo restano le righe degli stati con «Mostra sopra»: sono la tavola degli stati della pagina, non l'app.

## v56.32 — Selezione chiusa (25/10/2026, Marco)

- «Soglie dei setup ↗» diventa il tondo ↗ (title e aria-label «Soglie dei setup»), come gli altri collegamenti.
- Fatte: Dashboard, Notti, Archivio, Progetti, Statistiche, Meteo, Piano della notte, Selezione dei frame. Restano: Misure dei frame, Attrezzatura, Da confermare, Impostazioni, Planner.

## v56.31 — Selezione: le soglie solo a valore (25/10/2026, Marco: «piu' semplice possibile»)

- Ogni soglia e' «misura · > · numero · unita'». Via «dalla mediana · valore», «mediana +» e «MAD», e le descrizioni accanto (mediana, minimo–massimo, «vale 4,29″»).
- Le soglie di partenza scritte come mediana + MAD si mostrano col numero che danno in quel gruppo; quando si cambia il numero diventano «valore».
- Anche i testi (riassunto delle soglie, la riga della soglia sul grafico, il perche' di un frame) dicono solo il valore.

## v56.30 — Selezione: cosa e' cambiato qui (25/10/2026, Marco: «ok»)

- Le soglie partono da Impostazioni › Soglie dei setup; qui si sovrascrivono. «Applica» resta un gesto esplicito: sposta i file.
- Ogni riga cambiata rispetto a Impostazioni mostra «✎ cambiata qui · Ripristina» (Ripristina rimette il valore di Impostazioni, da applicare).
- Il bottone dice quante: «Applica · 1 soglia cambiata».

## v56.29 — Selezione: un riquadro alla volta (25/10/2026, Marco)

- Sulla barra cliccata il riquadro coi valori (file, notte, ora, misura) non compare: resta solo la pillola «Usa …», cosi' si legge il valore sotto. Passando sulle altre barre il riquadro torna.

## v56.28 — Selezione: vista e ordine sulla riga dei filtri (25/10/2026, Marco)

- Le icone barre · linee e «Per ora ▾» scendono a destra sulla riga dei filtri, subito sopra il grafico; la riga delle misure (FWHM · HFD · …) resta da sola.
- Confermato lo stile v56.27 per i fuori soglia (tratteggio rosso spento e ✕ sotto).

## v56.27 — Grafico: chi resta e chi si scarta (25/10/2026, Marco)

- Con la soglia, le barre dei frame che restano sono accese (testo al 58%); quelle da scartare si spengono: solo il filo rosso tratteggiato, quasi trasparente, e la ✕ sotto la barra (il segno, non solo il colore). Non rosse piene: il rosso pieno su meta' grafico urla, l'occhio deve andare a cio' che resta.
- Il frame scelto resta nell'accento.

## v56.26 — Soglia dal grafico (25/10/2026, Marco)

- Selezione, Frame per frame: toccata una barra, sopra la barra compare la pillola «Usa FWHM > 4,29″» (Marco: sopra la barra, piu' intuitivo; il setup e il filtro nel title e nell'aria-label). Vicino ai bordi la pillola si sposta verso l'interno. Un tocco compila la soglia di quella misura per quel setup e filtro: «valore», col numero del frame, accesa. Poi diventa «✓ FWHM > 4,29″ in uso».
- Non si compila da sola al tocco della barra: toccare le barre serve anche a guardare i frame, e ogni tocco cambierebbe i frame da scartare.
- Il verso (> o <) resta quello della soglia (FWHM, eccentricita' e fondo: >; stelle e SNR: <).

## v56.25 — Selezione dei frame (25/10/2026, Marco: «stesso lavoro»)

Come Misure dei frame, desktop e telefono:
- Vista a due icone (barre, linee); ordine in tendina «Per ora ▾»; Setup in tendina, nella tabella e in «Scarta i frame con…».
- In linguette sottili: Quali frame (Da scartare o al limite · Tutti), la misura (FWHM · HFD · …), i filtri (col pallino del colore), lo Stretch, il filtro delle soglie.
- Telefono, «Per filtro e posa»: filtro e ore sulla prima riga, «110 di 120 frame tenuti» sotto (prima andava a capo parola per parola).
- Restano: «Tipo di soglia» (dalla mediana · valore) dentro le righe delle soglie, piccolo; i tondi ✕ ✓ e il play del blink; «Soglie dei setup ↗».
- Superata la nota v54 «restano pillole piene barre · linee, per ora · per valore».

## v56.24 — Piano della notte chiuso (25/10/2026, Marco)

Fatte: Dashboard, Notti, Archivio, Progetti, Statistiche, Meteo, Piano della notte. Restano: Selezione dei frame, Misure dei frame, Attrezzatura, Da confermare, Impostazioni, Planner.

## v56.23 — Piano della notte, ritocchi (25/10/2026, Marco: «si»)

- Foglio «⋯» del telefono (Setup): la postazione scelta ha l'anello nell'accento e la ✓, non il fondo pieno.
- Righe del piano: «›» in fondo diventa il piccolo tondo ↗ (apre il dettaglio del blocco).
- Sul telefono le righe (avvio, cambi, chiusura, nome e sottotitolo dei blocchi) vanno a capo invece di tagliarsi.

## v56.22 — Piano della notte (25/10/2026, Marco: «stesso lavoro»)

- La postazione («AM5 · FRA400 · 4 bianchi ▾») non e' piu' una pillola piena nell'accento: e' una tendina come le altre (fondo carta-2, filo). Il pieno resta alle azioni (Completa il piano, Esporta per N.I.N.A.).
- «Meteo ↗» (desktop e telefono) diventa il tondo ↗, come gli altri collegamenti.
- Categoria (Deep sky · comete…) e Notte · giorno del Sistema solare in linguette sottili, anche nel foglio delle proposte sul telefono.
- Gia' a posto: le notti in linguette sottili, il modo in tendina sul telefono e in linguette sul desktop, «+ Proposte» col filo, ‹ ›, − +, la riga del tempo.

## v56.21 — Meteo (25/10/2026, Marco: «stesso lavoro»)

- Desktop come il telefono: il modello e' il menu «Automatico ▾» (ogni modello con la sua riga di spiegazione) e «Aggiorna» e' il tondo ↻. Prima: «modello» + quattro linguette + bottone «Aggiorna».
- Tolti i dati delle vecchie linguette del modello (`modelsP`).
- Gia' a posto: la striscia delle notti con l'anello; Deep sky · Sole e Obiettivo in linguette sottili; esiti coi colori fissi; «Altri 8 fattori ▾» e «Tutta la notte, ora per ora ▾» come «Tutti gli strumenti ▾»; le carte delle misure.

## v56.20 — Statistiche chiuso (25/10/2026, Marco)

Fatte: Dashboard, Notti, Archivio, Progetti, Statistiche. Restano: Meteo, Piano della notte, Selezione dei frame, Misure dei frame, Attrezzatura, Da confermare, Impostazioni, Planner.

## v56.19 — Niente codice spento (25/10/2026, Marco: «devi toglierle te, Claude Code non deve poter sbagliare»)

Tolto dal codice tutto cio' che non si vede piu':
- Archivio: il foglio «Vista e ordine» del telefono e il suo stato.
- Progetti: il foglio «Ordine nei gruppi» del telefono e il suo stato.
- Statistiche: le vecchie pillole del Calendario e della Capacita', i comandi desktop delle Stagioni (`ctrlDesk`), gli anni in pillole del telefono (`anniOn`, `telAnni`), la condizione sempre vera `ctrlTel`.
- MisureFrame: la prop `compatta` e il pannello «Vista ▾» del telefono (`VM`).
Le note «da togliere nel porting» qui sotto sono superate.

## v56.18 — Statistiche (25/10/2026, Marco: «stesso lavoro»)

- Desktop come il telefono: Calendario «2026 ▾» quando si guarda Tutto; Capacità «Misura ▾ · con gli anni ▾» su una riga (prima due file di pillole piene).
- Gia' a posto: in alto gli anni in linguette sottili sul desktop e «2026 ▾» sul telefono; Confronta, Sito, Setup in tendina; Stagioni con tendine e icone; esiti coi colori fissi; «dati simulati».
- Restano nel codice, spenti: le vecchie pillole del Calendario e della Capacità e i comandi desktop delle Stagioni (`sta.ctrlDesk`); da togliere nel porting.

## v56.17 — Progetti chiuso (25/10/2026, Marco: «possiamo considerarlo finito»)

Fatte finora con lo stesso giro: Dashboard, Notti (con la finestra della notte), Archivio (con la finestra dell'oggetto), Progetti. Restano: Statistiche, Meteo, Piano della notte, Selezione dei frame, Misure dei frame, Attrezzatura, Da confermare, Impostazioni, Planner.

## v56.16 — Progetti: le righe come nella Dashboard (25/10/2026, Marco: «uguale alla Dashboard»)

- Ogni riga dell'elenco: il cerchio della percentuale, poi il nome, il setup in tenue sotto, la barra dei filtri (la stessa di «Progetti in corso» nella Dashboard: un pezzo per filtro, lungo quanto le ore fatte sull'obiettivo totale), lo stato. A destra le ore fatte e l'obiettivo. Niente piu' testo tagliato a meta' («Askar FRA400 · A…»).
- Il dettaglio usa gia' il componente comune Avanzamento (lo stesso di Selezione dei frame): resta.

## v56.14 — Progetti (25/10/2026, Marco: «stesso lavoro»)

- Ordine in tendina «Per data ▾ / Per ore che mancano / Per nome», desktop e telefono. Sul telefono sta accanto a Cerca, al posto del «⋯» (il suo foglio non si apre piu').
- Modifica: il setup in tendina «Setup ▾», non piu' una fila di pillole.
- Gia' a posto: gruppi In corso · In attesa · Fermi · Finiti in linguette sottili; anello sul progetto scelto; esiti coi colori fissi.
- Le azioni del progetto (v56.15, Marco: «vai»), desktop e telefono: una azione piena («Reframing ↗», scelta di Marco al posto di «Rinquadra nel Planner», per il Sistema solare «Apri nel Planner ↗»); i collegamenti come tondi ↗ (Seleziona i frame, Aggiungi al piano); il resto nel tondo «⋯» con un menu: Modifica, Segna come finito o Riapri, Elimina in rosso e in fondo. Sul telefono il menu si apre verso l'alto.

## v56.12 — Archivio: l'anteprima si aggiunge (25/10/2026, Marco)

- Un tondo piccolo (44 px) con la fotocamera, in basso a destra del riquadro, apre la scelta di un'immagine; con l'immagine diventa la matita «Cambia». Via la scritta «Nessuna anteprima» (Marco: la pillola col testo ingombrava).
- Un'anteprima per produzione (v56.13): il riquadro si divide in tante parti quante sono le produzioni, ognuna col suo tondo; fino a 3 su una riga, oltre su due righe (5 produzioni: 3 + 2). Il mosaico ha un'anteprima sola.
- Il nome grande nel riquadro resta finche' manca l'immagine.
- Simulato: l'immagine resta per la sessione; nel porting va salvata con l'oggetto.

## v56.11 — Archivio (25/10/2026, Marco: «stesse cose controllate finora»)

- Ordine in tendina «Per nome ▾» e vista a due icone (tessere, elenco, 44 px, anello sulla scelta), desktop e telefono. Sul telefono stanno sotto il conteggio; via il «⋯» e il suo foglio «Vista e ordine» (pillole piene).
- La finestra di un oggetto sul telefono, nell'anteprima larga, ora sta dentro il telefono 390 × 844 (prima riempiva tutta la finestra). Vale anche per Notti: e' lo stesso componente FinestraRiepilogo.
- Gia' a posto: linguette sottili Deep sky · Sole · Sistema solare; Criteri ▾; tondo + sul telefono; finestra dell'oggetto con gli stessi pezzi della notte (Setup con icone, misure con linguette e Luna).
- Da togliere nel porting: il foglio «Vista e ordine» resta nel codice ma non si apre piu'.

## v56.10 — Controllo Notti e finestra (25/10/2026)

- Desktop e telefono guardati, pagina e finestra della notte. Unico difetto: le due icone della vista (barre · linee) erano da 40 px; ora 44, anche nelle Stagioni.
- La tabella «Per filtro» sul telefono scorre di lato: voluto.
- Tutto il resto usa i pezzi comuni: tondi ↗ ‹ › ×, linguette sottili, tendine a pillola, anello sulla notte scelta, esiti coi colori fissi.

## v56.7 — Finestra della notte, ritocchi (25/10/2026, Marco)

- Riepilogo e Setup in alto hanno la stessa altezza.
- Ogni pezzo del Setup ha la sua icona tonda, la stessa di Attrezzatura (ottica, riduttore, ruota, camera, montatura, focheggiatore, guida, programma, campo).
- Misure dei frame: «Un grafico per filtro» in linguette sottili (se ne possono accendere piu' d'una); la Luna nei grafici e' l'interruttore comune (lo stesso delle soglie in Selezione: binario e nome «Luna»), v56.35; superata la versione con icona e Off/On. Le linguette valgono anche sul telefono (v56.8). Anche i filtri (tutti · L · R · G · B · Hα…) sono linguette sottili, col pallino del colore del filtro e il numero dei frame (v56.9).

## v56.6 — La finestra della notte piu' corta (25/10/2026, Marco: «ok»)

- Le misure dei frame nella finestra della notte restano intere, coi grafici frame per frame (Marco: per guardare e confrontare la notte senza uscire). Scegliere e scartare i frame si fa in Selezione dei frame, col tondo ↗ accanto a «Frame per frame». La prop `compatta` di MisureFrame resta disponibile ma non e' usata.
- Gli oggetti: ogni riga ha il tondo ↗ verso Progetti.
- «In cielo dal catalogo» c'era gia' solo nella finestra di un oggetto: resta.

## v56.5 — La finestra della notte: il setup in alto (25/10/2026, Marco)

- La carta Setup sale accanto al Riepilogo, a destra (Riepilogo 8 colonne, Setup 4); sul telefono subito sotto il Riepilogo. Prima stava in fondo, dopo le misure.

## v56.4 — Le misure dei frame come le Stagioni (25/10/2026, Marco)

Componente MisureFrame (Misure dei frame, la finestra della notte), desktop e telefono:
- Frame per frame: una riga sola: la vista a due icone (barre, linee), «Per ora ▾», «Misurata ▾» (quando c'e' lo zenit), il tondo della Luna. Via le pillole segmentate e, sul telefono, il pannello «Vista ▾».
- «Seleziona i frame ↗» (bottone a contorno) diventa il tondo ↗.
- A confronto: «Misura ▾» in tendina al posto della fila di pillole.
- Restano pillole i filtri (Tutti · L · R · G · B · Hα…): hanno i colori dei filtri e si cambiano guardando.

## v56.3 — La finestra della notte (Riepilogo) (25/10/2026, Marco)

- Le scelte in testa (produzioni, pannelli del mosaico) sono linguette sottili con la sottolineatura nell'accento, non pillole piene.
- Setup: «Apri in Attrezzatura ↗» (bottone a testo in fondo) diventa il tondo ↗ accanto al titolo «Setup»; «Tutti gli strumenti ▾» e' il bottone a testo comune con la freccia.
- ‹ › e × da 44 anche sul desktop (erano 40).
- Restano pillole, perche' sono stati e non comandi: il sito, l'esito del cielo, gli esiti delle notti.

## v56 — Notti con le regole della Dashboard (25/10/2026, Marco)

- La notte scelta nella striscia in alto ha l'anello nell'accento anche sul desktop (mancava: l'anello c'era solo sulle caselle del telefono). Vale per tutte le pagine con la striscia (Notti, Meteo, Piano della notte).
- «Tutto della notte ↗» (bottone pieno in fondo alla carta) diventa il tondo ↗ in alto a destra della carta, desktop e telefono: apre un dettaglio.
- Telefono: «← Tutte le notti» e' il bottone comune, come sul desktop.
- Tutto l'archivio, «fuori da ogni notte»: ogni riga (da confermare, senza sito, senza data) porta in Da confermare col tondo ↗; una riga a zero non compare, e se sono tutte a zero sparisce il blocco.
- Criteri (i filtri della ricerca) e A confronto (l'elenco delle notti) erano gia' a posto: restano.
- Corretto: sul telefono «Tutto della notte» si apriva a tutta finestra, come sul desktop; ora la finestra sta dentro il telefono.

## v55.6 — Dashboard, desktop e telefono allineati (25/10/2026)

Confronto delle informazioni e dei comandi tra i due formati. Allineato sul telefono:
- Luna: il tondo ↗ per il dettaglio (c'era il dettaglio ma non il modo di aprirlo).
- Sole: il tondo ↗ verso il Meteo; «112 macchie» come numero a destra (come il 62% della Luna); sotto, tramonto e alba come sul desktop.
- Notte scelta nel calendario: anche × per chiudere.
- Il 2026: il tondo ↗ verso Statistiche e «4,6 al mese».
- «migliore 08:30–10:30» con la stessa parola del desktop.
Diverso di proposito: sul telefono il sottotitolo della carta protagonista e' una riga sola; i titoli «La Luna stanotte» e «Il Sole oggi» li fanno le linguette. Tutti i comandi sono i mattoni comuni (linguette sottili, tondi ↗ e ×, bottoni); nessun colore scritto nella pagina.

## v55.5 — Dashboard telefono (25/10/2026, Marco)

- «Notte · Progetti · Sistema solare» in cima alla carta protagonista (prima in fondo): si capisce subito cosa si guarda.
- Il calendario della Luna sul telefono e' sempre aperto (via il bottone «Calendario · settembre ▾»): Luna e Sole occupano ora lo stesso spazio.
- Il Sole sul telefono ha quello che ha il desktop: le pillole dell'attività, le regioni attive sotto il grafico, «Effetti sulla notte» col Kp e l'aurora.

## v55.4 — Dashboard, un comando per funzione (25/10/2026, Marco: «si vai»)

Regola per tutte le pagine: linguette sottili per scegliere cosa guardare; tondo ↗ per andare in un'altra pagina o aprire un dettaglio; tondo × per chiudere; bottone comune col nome solo per un'azione vera (pieno se e' la principale, a contorno o a testo se secondaria); pillole solo per stati ed esiti, mai cliccabili.
Dashboard:
- Primi passi: «Scegli il sito», «Scegli la cartella», «Crea un progetto» sono il bottone comune (pieno il primo passo, a contorno il secondo), non piu' pillole disegnate nella pagina.
- Da riprendere: «Rispondi» bottone pieno piccolo; «Vedi in Notti» diventa il tondo ↗.
- Telefono: «Le altre 2 notti ▾» e' il bottone a testo; «Calendario · settembre ▾» il bottone tenue a tutta riga, come i «mostra» delle altre pagine.
- Avvisi (componente Avviso, tutte le pagine): l'azione a contorno, non piena: l'avviso non e' l'azione principale della pagina.

## v55.3 — Dashboard, le frecce (25/10/2026, Marco)

- Progetti in corso: «Per ore · Meglio stanotte» in linguette sottili (desktop e telefono).
- Il giorno scelto nel calendario: «Apri in Notti →» diventa il tondo ↗ accanto a «★ mercoledì 16 settembre · 2 h» (a sinistra di × sul desktop); il riquadro e' piu' basso.
- Ogni carta che porta a un'altra pagina ha lo stesso tondo ↗ in alto a destra, senza nome (il nome nel title e nell'aria-label): Meteo della notte (prima «Prossime notti» + «Meteo ↗», due bottoni per la stessa pagina), Statistiche (prima «Statistiche ↗» a testo), Progetti, Luna, Sole.

## v55.2 — Planner desktop come il telefono (25/10/2026, Marco)

- Dentro · Cupola · Sfera: tre icone tonde (occhio, cupola, globo), come sul telefono; il nome e la spiegazione nel title.
- «Stanotte · Le mie riprese»: la stessa pillola del telefono, la scelta nell'accento del cielo.

## v55.1 — Planner nei mattoni (25/10/2026, Marco: «anche il Planner, telefono e desktop»)

I 58 bottoni del Planner con lo stile scritto nella pagina ora usano i mattoni del foglio; nella pagina resta solo cio' che cambia (colore della scelta, posizione, ombra dinamica):
- `al-bottone--scelta` (22): le scelte dentro un gruppo (filtri, viste, setup, pose); 36 px sul desktop, 44 sul telefono.
- `al-bottone--icona` + `--tenue` (8): i «Chiudi»; ora tutti 44 (prima 32–36 sul desktop).
- `al-bottone--vetro` (7, nuovo): vetro scuro sul cielo (Setup, Adatta, Torna al cielo, Rotazione).
- `al-bottone--cielo` (+ `--icona`, `--tessera` per il Mosaico, `--copia`): i comandi chiari sul cielo.
- `al-bottone--riga` (6, nuovo): le righe degli elenchi (risultati, setup, componenti).
- `al-tocco` (7, nuovo): bersagli senza aspetto (maniglie, linguette del foglio, interruttore «sulla carta»).

## v55 — Desktop: un mattone per funzione (25/10/2026, Marco: «fai il check come per il telefono»)

Inventario dei comandi del desktop in tredici pagine. I pulsanti usano gia' tutti `al-bottone` (con le sue varianti), salvo il Planner. I tondi, i segni e le pillole delle pagine invece avevano misure loro:
- Tondi che si toccano (⋯, ‹ ›, ×, ↗, frame prima e dopo): da 28 a 48 px → 44, fondo carta-2, come `al-bottone--icona`. Nelle barre strette della Selezione (viste, schermo intero) 36, come `al-bottone--icona` piccolo.
- Segni degli stati: da 16 a 26 px → 22, come `al-segno`.
- Pillole piccole (esiti, etichette): undici varianti → una (4 × 10, 12 px), come `al-pillola`; la pillola dell'esito accanto al numero protagonista: una misura (5 × 12, 13 px); le pillole che sono azioni: 44 px come `al-bottone`.
- Numeri di posizione in Dashboard: una misura (40 px). Icone nelle righe di Attrezzatura: 44 come le altre righe.
- Tendine: pillole da 44 (v54.1). Linguette sottili, anello, titoli: v54.
Restano come sono, perche' sono un'altra cosa: i protagonisti (gli anelli di avanzamento, l'esito grande in Da confermare, i tondi degli stati vuoti), i puntini dei colori, il «Scarta» grande del visore della Selezione.
Resta per Claude Code: i 58 bottoni del Planner sul cielo con lo stile nella pagina.

## v54.1 — Statistiche sul desktop come sul telefono (25/10/2026, Marco)

- Stagioni: una riga sola anche sul desktop: «Misura ▾» (raggruppata Cielo · Frame · Volumi), «Anno ▾» solo nella vista a linee (la griglia mostra tutti gli anni), la vista a due icone (griglia, linee). Via le tre file di pillole.
- Tutte le tendine sono pillole da 44 anche sul desktop (stessa regola del telefono, testo 14 px): la riga in alto «Confronta con · Sito · Setup» e i setup della Capacità non sono piu' piccole.

## v54 — Desktop con le regole del telefono (25/10/2026, Marco: «vai»)

I quattro punti di v52, fatti:
1. Linguette sottili anche sul desktop (stesse regole del foglio, testo 14 px): Dashboard (Notte · Progetti · Sistema solare, Luna · Sole), Statistiche (gli anni, Cielo · Frame · Volumi), Meteo (Deep sky · Sole, il modello), Archivio (Carte · Elenco), Piano della notte (le notti, Deep sky · Sistema solare · Ricerca).
2. La cosa scelta con l'anello nell'accento, non il fondo pieno: la notte nella striscia (Notti, Meteo, Piano della notte), il setup e il gruppo dei componenti in Attrezzatura.
3. Niente titolo grande nella pagina (resta per la lettura vocale): Statistiche, Selezione dei frame, Attrezzatura, Misure dei frame, Piano della notte, Progetti. Meteo: la carta si chiama «Le prossime notti» come sul telefono.
4. Misure dei frame: un titolo solo, «Le misure dei frame» nella carta.
Restano pillole piene le scelte che si cambiano guardando (Selezione: barre · linee, per ora · per valore; Misure: i filtri) e l'azione principale.

## v53.2 — Solo l'essenziale (25/10/2026, Marco: «ottimizza tutti i file»)

- Cancellate: le tavole `Telefono vetro`, `Prova tema`, `Foglio` (v32, superato da `Sistema`), `Piano della notte telefono` (proposta superata), `Planner telefono`, `Planner desktop` e i loro componenti `PianoTelefono`, `PianoDesktop`; le cartelle `screenshots/` (643 catture di lavoro), `scraps/`, `strumenti/` (gli attrezzi del riordino v32), `uploads/` (riferimenti visivi e video di partenza).
- Spostati in `docs/archivio/`: i brief e le note del riordino v32 e del porting del Planner, chiusi; in `docs/archivio/testi/` i testi di partenza di Attrezzatura, Da confermare e Meteo.
- `Cattura`: tolte le voci delle pagine cancellate.
- README e CLAUDE.md aggiornati.
- Un solo sistema per desktop e telefono: `Sistema` mostrera' ogni mattone nei due formati (dopo il desktop).

## v53.1 — Pulizia (25/10/2026, Marco: «ok»)

Sul telefono resta una versione sola di tutto:
- Uscita la barra a cinque icone (e `barra="classica"`): la bolla di vetro e' l'unica barra del telefono.
- Uscita dall'Archivio la riga del telefono che non si vedeva.
- Cancellate le tavole di prova `Planner proposte`, `Telefono comandi`, `Telaio vivo`, la vecchia tavola `Telefono` (sostituita da `Telefono vetro`) e i componenti `ProposteNotte`, `PianoColonna`.
- Restano finche' serve: `Prova tema` (fino a fine desktop); `Planner telefono` e `Planner desktop`, le tavole di riferimento del Planner.

## v53 — Telefono chiuso (25/10/2026)

Controlli finali prima del desktop:
- Contrasto calcolato su tutti i temi (2 modi × 5 accenti): testo e tenue su carta e carta-2, testo delle pillole piene, esiti, anello e accento sul fondo. Tutto sopra soglia (4,5:1 il testo, 3:1 l'anello).
- Catture in modo chiaro e scuro con accenti diversi, anche sotto la prima schermata (Dashboard, Notti, Statistiche, Meteo, Piano della notte, Impostazioni, Attrezzatura, Da confermare).
- Corretti: Statistiche › Volumi, il nome del setup sul grafico usciva a sinistra della carta (ora nome corto e lato giusto); Stagioni, nella tendina le misure lunghe col nome corto («Notti buone», «Qualità»).
- Banco di prova: `pagine/Prova tema.dc.html?p=Notti&modo=chiaro&accento=...` mostra una pagina del telefono con modo e accento a scelta.
- Restano per Claude Code: i bottoni del Planner sul cielo con lo stile nella pagina.
Il telefono e' chiuso. Prossimo: il desktop con le regole v52 (linguette sottili, anello, titoli, Misure).

## v52.3 — Le tendine dove servono (25/10/2026, Marco: «ok»)

Regola: tendina per cio' che si sceglie e si lascia (misura, anno, ordine); icone per la vista; pillole e linguette per cio' che si cambia guardando.
Fatto sul telefono:
- Statistiche: Calendario «2026 ▾» quando si guarda «Tutto»; Capacità «Misura ▾ · con gli anni ▾» su una riga (prima due file di pillole); le tendine dei setup restano.
Controllato e lasciato com'e' (il giro di prima sovrastimava):
- Selezione dei frame: sul telefono c'e' gia' solo «Quali frame»; Vista, Ordine e Misura sono solo desktop.
- Progetti: gia' linguette sottili + «⋯» per l'ordine; il Setup sta nel foglio di modifica.
- Meteo: «modello» e' solo nella testata del desktop.
- Archivio: sul telefono vista e ordine stanno gia' nel «⋯»; Tipo e Fonti sono spunte del modulo «Aggiungi»: restano. (La riga per il telefono preparata nella pagina non si vede: resta spenta.)

## v52.2 — Statistiche, Stagioni sul telefono: una riga di comandi (25/10/2026, Marco: «confusionario»)

Prima: quattro file di pillole (Griglia · Linee, Cielo · Frame · Volumi, la misura, gli anni). Ora una riga sola:
- «Misura ▾»: una tendina con le otto misure raggruppate sotto Cielo, Frame e Volumi (il gruppo non e' piu' una scelta a parte).
- «2026 ▾»: l'anno.
- La vista: due icone (griglia, linee), la scelta con l'anello.
Desktop invariato.

## v52.1 — Telefono: un mattone per funzione (25/10/2026, Marco: «la versione mobile la consideriamo finita»)

Inventario dei comandi del telefono in tredici pagine (classi del foglio e classi locali). Le classi delle pagine restano; sul telefono prendono le misure dei mattoni comuni (blocco «v52» in fondo al foglio):
- Tondi che si toccano (⋯, ‹ ›, − +, ×, ↗): dieci varianti da 28 a 44 px → 44 px, fondo carta-2, come `al-bottone--icona`.
- Segni degli stati (✓ ! ? ✕ ○): sedici varianti da 16 a 26 px → 22 px, come `al-segno`.
- Pillole piccole (esiti, etichette): undici varianti → padding 4 × 10, 12 px, come `al-pillola`.
- Pillola dell'esito accanto al numero protagonista: una misura (5 × 12, 13 px) in Dashboard e Meteo.
- Pillole che sono azioni (Dashboard, Impostazioni): misure di `al-bottone`, 44 px.
- Freccia delle tendine e dei «mostra»: una sola, ▾ / ▴ (via ▼ ▲).
- Tendine: una regola (pillola, filo, freccia disegnata). Scelte di vista: linguette sottili. Scelta dentro una striscia: anello.
- Resta fuori: il Planner (58 bottoni con lo stile scritto nella pagina, sul cielo): stessi valori, ma non ancora mattoni; da fare col porting a Claude Code.
- Prossimo passo: le stesse regole sul desktop.

## v52 — Giro profondo (25/10/2026)

Fatto:
- Planner, telefono (Marco): Dentro · Cupola · Sfera diventano tre icone tonde da 44 (occhio, cupola, globo; il nome nel title e nell'aria-label). La legenda non sta piu' sotto il cielo (si tagliava): si apre da un tondo «legenda» accanto alle viste, in un vetro scuro sul cielo, col credito delle stelle.
- Planner, telefono (Marco, giro 4): «12 sulla carta · Migliori di stanotte · Nascondi» diventa un interruttore piccolo (pillola di vetro 28 px col binario e il numero; bersaglio 44); il nome della lista nell'aria-label.
- Planner, telefono (Marco, giro 3): mentre il dito muove il cielo, «Stanotte · Le mie riprese», la legenda e «12 sulla carta · Nascondi» si ritirano (dopo 0,12 s di dito fermo sul cielo); tornano 1,2 s dopo che il dito si alza. Un tocco breve non li nasconde. Lo stesso vale per la colonna di destra (lente, viste, Cosa mostrare). Sul telefono + e − escono: la colonna copriva «Adesso»; lo zoom e' con due dita.
- Planner, telefono (Marco, giro 2): Dentro · Cupola · Sfera in colonna sotto la lente, a destra (lente, viste, Cosa mostrare, +, −); in alto a sinistra «Stanotte · Le mie riprese» e il tondo della legenda. Superato il giro 1: «Stanotte · Le mie riprese» saliva sul cielo, sotto le viste, come pillola di vetro (prima stava sotto la carta, poco visibile e sotto la bolla).
- Misure dei frame era l'unica pagina senza telaio: ora sta nel telaio di sempre (sul telefono «Misure»; il titolo grande esce).
- Tutte le tendine del telefono sono pillole (fondo, filo, freccia disegnata) con una regola sola nel foglio.

Da decidere (desktop, trovato nel giro):
1. Le linguette sottili (2b) ci sono solo sul telefono: sul desktop le stesse scelte sono ancora pillole piene (Notte · Progetti · Sistema solare, Deep sky · Sole, gli anni, le sezioni delle Impostazioni).
2. Il colore pieno per la cosa scelta resta sul desktop: il setup in Attrezzatura, la notte nelle Notti e nel Meteo.
3. I titoli: Progetti, Statistiche, Meteo, Piano della notte, Selezione, Attrezzatura, Impostazioni, Misure hanno un titolo grande; Dashboard, Notti, Archivio, Da confermare no. Proposta: nessun titolo grande sul desktop (la pagina e' gia' accesa nella barra), al suo posto la riga del sottotitolo.
4. Misure dei frame: «Il riepilogo della notte · le misure dei frame» e poi «Le misure dei frame» nella carta: un titolo di troppo.

## v51 — Il telefono coerente: il piano (25/10/2026, Marco: «mi piace, inizia»)

Giro pagina per pagina sul telefono (prima schermata di ognuna). Generali prima, poi per pagina.

Generali:
1. Un titolo solo: quello della barra in alto. Via i titoli grandi doppi (Selezione dei frame, Attrezzatura, Impostazioni, Meteo «Meteo a Cima Ekar»).
2. Spazio in fondo per la bolla: il contenuto non ci finisce sotto.
3. Le barre d'azione della pagina vanno nel vetro accanto alla bolla, come Salva nel Planner: Da confermare («5 da applicare · Applica»), Notti («Tutto della notte»). E' l'unico caso in cui il vetro torna.
4. Il colore pieno solo all'azione principale; le scelte con l'anello o la sottolineatura («Un progetto in corso», il giorno del Meteo, «+ Proposte»).
5. Gli esiti hanno colori fissi, non l'accento (controllare «✓ notte buona»).
6. Nella pagina Da confermare il bollino in alto non c'e'.

Per pagina:
- Dashboard: sotto «9 ore» una riga sola, il resto nel dettaglio; «Luna · Sole» in linguette sottili.
- Notti: «dalla più recente» e «2 cose da vedere» separati; frecce ‹ › da 44.
- Archivio: senza anteprima, riga compatta al posto della tessera vuota.
- Meteo: il giorno scelto con l'anello.
- Statistiche: sotto le tendine solo «dati simulati».
- Piano della notte: linguette solo per le notti; il modo in una tendina «Deep sky ▾».
- Selezione dei frame: «Parti da» in linguette sottili.
- Da fare dopo: il resto delle pagine sotto la prima schermata, e il Planner.

Fatto (25/10):
- 1 titoli doppi via (Selezione, Attrezzatura, Impostazioni; Meteo: la carta si chiama «Le prossime notti»).
- 2 spazio in fondo 116 px.
- 3 la bolla di vetro e' la barra del telefono in tutte le pagine (`barra="classica"` solo per confronto); Da confermare: «N da applicare · Applica» e' il vetro accanto alla bolla. Nelle Notti «Tutto della notte» sta dentro la carta: resta li'.
- 4 Striscia sul telefono: la notte scelta con l'anello nell'accento; «+ Proposte» col filo; «Parti da» in linguette sottili.
- 5 Dashboard e Meteo: «✓ buona» col verde degli esiti, non l'accento.
- 6 Da confermare: niente bollino nella sua pagina (anche sul desktop).
- Dashboard: sotto «9 ore» una riga sola sul telefono; «Luna · Sole» sottili. Statistiche: sotto le tendine «dati simulati». Notti: ordine e avvisi su due righe, l'avviso e' una pillola da 44 (le frecce erano gia' da 44). Piano della notte: il modo in tendina «Deep sky ▾». Archivio: anteprime 3:2 invece che quadrate.

## v50 — La barra di vetro sul telefono (25/10/2026, prova, da approvare)

Marco: il telefono del Planner (barra di vetro, bolla, foglio) e' l'esperienza migliore; si riporta nelle altre pagine, una cosa alla volta.

- `Telaio`, formato telefono: nuova barra `vetro` (prop `barra="vetro"`, o `?barra=vetro`). Al posto della barra con le cinque icone: la bolla di vetro con la pagina in cui sei (toccata si apre in Dashboard, Notti, Archivio, Meteo, Altro) e accanto il vetro con la cosa piu' importante della pagina e un'azione sola. La barra in alto resta.
- Contenuto del vetro, per ora nel telaio (dati simulati): Dashboard «9 ore ✓ notte buona» → Piano della notte; Notti «212 notti» · Cerca; Archivio «240 oggetti» · Cerca; Meteo «Stanotte ✓ notte buona» → Piano della notte; Progetti → Planner. Le pagine lo potranno passare con `vetro`.
- Tavola `pagine/Telefono vetro.dc.html`: 1a–1k le undici pagine del telefono vere col vetro (Progetti «5 in corso», Statistiche, Piano della notte, Selezione dei frame, Attrezzatura «5 setup», Da confermare, Impostazioni); le pagine fuori dalle cinque hanno la loro icona nella bolla e accendono Altro.
- Marco: le righe di pillole (Notte · Progetti · Sistema solare, Deep sky · Sole, i modi del Planner) occupano troppo. Proposte 2a oggi, 2b linguette sottili in testa alla carta, 2c il titolo e' la scelta («Notte ▾»), 2d si scorre di lato coi segni. **Scelta (Marco, 25/10): 2b**, portata sul telefono: classe `al-scelta--sottili` nel foglio (parola sottolineata, 44 px, nessun fondo; solo sotto `[data-formato="telefono"]`). Dove: Dashboard (Notte · Progetti · Sistema solare), Meteo (Deep sky · Sole), Archivio (Deep sky · Sole · Sistema solare, le due righe), Notti (la pista), Progetti (i gruppi), Piano della notte (le notti, la tecnica, notte o giorno), Statistiche (Vista, Anno), Planner (Cielo profondo · Sistema solare · Eventi, Stanotte · Le mie riprese). Restano pillole: le scelte brevi dentro un'impostazione (SHO/HOO, priorita', stretch) e i comandi sul cielo (Dentro · Cupola · Sfera).
- Statistiche, telefono: gli anni non sono piu' una riga da scorrere ma una tendina («2026 ▾») accanto a Confronta, sito e setup; la riga va a capo (crescono ogni anno).
- **Giro 3 (Marco, d'accordo su tutto)**: telaio del telefono rifatto.
  - In alto vetro come in basso: il titolo della pagina (17 px) con sotto il sito in tenue («Cima Ekar ▾», tutto un bersaglio da 44); Da confermare e Cerca tondi di vetro. Via la pillola piena del sito. In Progetti sul telefono il titolo grande esce (doppio).
  - **Giro 4 (Marco)**: via il vetro accanto alla bolla in tutte le pagine (anche Dashboard, Meteo, Progetti); resta solo la bolla del menu. Gli avvisi come «è stagione» andranno nelle notifiche dell'app.
  - La bolla e' di vetro con l'icona nell'accento, come nel Planner.
  - Il vetro accanto alla bolla c'e' solo dove aggiunge qualcosa che la pagina non ha: Dashboard «IC 1396 ✓ è stagione» (il prossimo progetto → Progetti), Meteo «Il piano · 3 oggetti» (→ Piano della notte), Progetti «Nuovo progetto» (→ Planner). Nelle altre pagine resta solo la bolla.
  - Statistiche, telefono: l'anno da solo sulla prima riga; Confronta, sito e setup su una seconda riga che scorre di lato (mai a capo).
  - Bolla piu' leggibile sulle foto: vetro al 90 % e icona a tratto 2,1.
  - Statistiche, telefono: le tendine della testa (anno, Confronta, sito, setup) sono pillole come «Cerca un progetto»: fondo carta, filo, freccia disegnata.
- Planner, telefono (Marco: «non e' chiaro come si fa il piano»): sopra il vetro una linguetta «︿ Piano» che tira su il foglio (bersaglio 120 × 44).
- Tavola: aggiunti 1l Planner · Cielo (col vetro) e 1m Planner · Il piano.
- Marco: mentre si scorre il vetro sparisce e resta solo la bolla; quando ci si ferma ricompare (dopo 0,45 s).
- Da decidere: il foglio dal basso per pagina; la barra in alto; cosa va sul vetro in Archivio, Progetti, Statistiche, Impostazioni.

## v49 — Il Planner portato (25/10/2026)

La fase di Aladin del cielo profondo in `pagine/Planner.dc.html` prende la forma di `PianoDesktop` e `PianoTelefono`, coi dati veri.

- Desktop: telaio di sempre con l'opzione nuova `pieno` (pagina a tutto schermo, barra in alto uguale). Cielo largo con Aladin vero, Stanotte di vetro sul cielo, colonna di 424 px: Stagione, Pose, Salva in fondo. Righello, Mosaico, maniglia, riga del centro con «Copia», tastiera.
- Telefono: cielo a tutto schermo, righello che si riduce a pillola, bolla del Planner e barra di vetro col riassunto e Salva, foglio a tre altezze (Stanotte · Stagione · Pose), aiuto dei gesti al primo avvio.
- Stagione dai dati (`stagioneDi`): i mesi con almeno il 67 % delle ore del mese migliore e almeno 3 h, il 15 del mese. Le due soglie in Impostazioni › Planner (`planner.stagione`, `planner.mese`). «è stagione», «in attesa · da …» o «non sale da qui» dalla data simulata (30 settembre 2026).
- Sette stati controllati a 1440 × 900 (progetto in corso, fuori stagione, non sale da qui, senza rete, setup virtuale, sito mancante, Aladin che non risponde), ognuno con parola e segno.

## v48 — Planner sul desktop (24/10/2026, approvato da Marco insieme al telefono v47)

Tavola `pagine/Planner desktop.dc.html` (componente `PianoDesktop`), con le stesse regole del telefono.

- A sinistra il cielo (756 px): «← Cupola», nome con altezza adesso, sotto la tendina «Setup ▾» (corredi e Setup virtuale); in alto a destra immagine e «Adatta»; in basso il righello «da nord verso est» e «Mosaico» (colonne e righe −/+, il cielo si adatta). Maniglia sul campo, etichetta sotto.
- A destra due colonne a vista insieme: Stanotte (piccola) e Stagione (la principale); Pose (schema, posa scritta per filtro, ore −/+, «+ Aggiungi un filtro», totale e notti, priorita'). In fondo, su tutta la larghezza, il riassunto e Salva (Aggiorna, Salva lo stesso, Non si salva); dopo Salva «Salvato in Progetti · Annulla».
- Stessi cinque stati del telefono. Sul desktop resta il telaio di sempre (Dashboard … Meteo, Altro, sito, Da confermare, Cerca, modo, Impostazioni), non la barra del telefono (Marco).
- **Giro 2 (Marco)**: il cielo si allarga fino alla colonna (972 px); Stanotte va sul cielo, in una carta di vetro in alto a destra; la colonna (424 px) ha Stagione sopra Pose, e Salva in fondo.
- La prima pagina del Planner (Cupola, Sfera, Dentro e la ricerca) si chiama «Cielo»: il ritorno e' «← Cielo», qualunque vista si usasse (proposta a Marco, al posto di «hub Planning»).
- **Giro 3**: sotto l'etichetta del campo la riga del centro (RA, Dec, rotazione) con «Copia» per NINA o ASIAIR e «Rimetti al centro» se il cielo e' spostato; nella tendina del setup «Confronta col campo di» (tratteggiato); tastiera: frecce, [ ], + −, A. «Adatta» usa lo spazio sotto la carta Stanotte; col mosaico aperto Stanotte si nasconde.

## v47.1 — A cosa serve il Planner (24/10/2026, Marco)

- Il Planner crea progetti, non piani per stanotte: si inquadra un oggetto (anche visto su AstroBin) e si salva, che lo si riprenda stanotte o fra sei mesi. Quando e' stagione, la Dashboard lo ricorda. Il centro e' la stagione; stanotte resta in fondo, come informazione (dov'e' adesso).
- **Giro 2 (Marco)**: tolte le Note; la Priorità (alta, media, bassa) resta, in fondo a Pose. Ordine: Stanotte · Stagione · Pose.
- **Giro 3 (Marco)**: niente pose preimpostate: ogni filtro ha la sua posa, scritta a mano (anche 58 s), accanto alle ore −/+; i frame si contano da li'. «+ Aggiungi un filtro» elenca quelli della camera che mancano; a 30 minuti il − diventa × e toglie il filtro. LRGB parte coi suoi quattro: L, R, G, B.
- **Stati (24/10)**: progetto in corso (barra «In corso · 9 h 10 di 12 h» sotto la stagione, «Aggiorna», «già fatte» nelle pose); fuori stagione («in attesa · da novembre», si salva, la Dashboard lo ricorda); non sale mai («non sale da qui», mesi vuoti, «Salva lo stesso» per un altro sito); senza rete (campo sul fondo scuro); setup virtuale (Salva spento). Regola proposta per la stagione: i mesi con almeno due terzi delle ore del mese migliore e almeno 3 h.
- Telefono: linguette Stagione · Pose · Note · Stanotte (superato dal giro 2). Stagione: periodo migliore, 12 mesi, altezza massima, una notte del mese migliore, notti senza Luna, quanto resta. Pose con la posa di ogni frame (120/180/300/600 s) e le notti del mese migliore. Note: perche' lo voglio, riferimento (AstroBin), priorita'. Barra: «Set – nov · e' stagione». Salva subito, poi «Salvato in Progetti · Annulla». Righello «dal nord», si riduce a pillola dopo qualche secondo; «Adatta» al posto di + e −; aiuto dei gesti al primo avvio.

## v47 — Planner sul telefono (24/10/2026, approvato da Marco)

Tavola `pagine/Planner telefono.dc.html` (tre telefoni veri, componente `PianoTelefono`), dopo le rassegne `Telefono comandi` e `Telaio vivo`.

- Cielo a tutto schermo; il dito sposta il cielo sotto il campo, maniglia sul campo per ruotare, + e − per lo zoom. In alto solo indietro, nome con altezza, immagine.
- In basso, nella metà del pollice: righello di vetro per la rotazione col valore e il bottone «Mosaico»; sotto la barra di vetro del telaio raccolta (F1): bolla del Planner (riapre le pagine) e barra del piano con ore utili, setup, mosaico, pose e Salva.
- Toccando la barra il piano sale a metà (il campo resta visibile sopra); la maniglia lo porta a tutto schermo. In testa ore utili e Salva; linguette sottolineate Notte · Setup · Campo · Pose · Anno che saltano alla sezione; dentro si scorre. Tocco sul cielo: si torna a inquadrare.
- Setup come carte coi loro campi e «entra / esce»; Setup virtuale dentro Setup.
- **Giro 2 (Marco)**: rotazione col righello come la Fotocamera di iOS. «Mosaico» apre un riquadro con la griglia 6 × 4 da toccare e la sovrapposizione; il cielo si rimpicciolisce da solo perche' tutti i pannelli stiano in vista. Sotto il nome dell'oggetto la tendina «Setup ▾» coi quattro corredi e «+ Setup virtuale (temporaneo)»: focale, riduttore o Barlow, sensore, camera; il campo cambia mentre scrivi; con il virtuale Salva e' spento («non si salva»).
- **Giro 3 (Marco)**: nel piano tolti Setup e Campo (erano doppi: stanno sul cielo); linguette Notte · Pose · Anno. Il mosaico si sceglie con Colonne −/+ e Righe −/+, niente griglia. Pillole solo per scelte brevi (SHO/HOO/LRGB, 0° 45° 90° 135°, sovrapposizione). Bersagli da 44.

## v46 — Il piano: immagine a sinistra, colonna a destra (24/10/2026, Marco: «vai»)

Riferimenti: Telescopius (anteprima del campo col proprio setup) e NINA (maniglia sull'angolo del campo per ruotare). Supera barra degli strumenti, pannelli e barra «il piano in breve» della v45.

- **Desktop**: a sinistra l'immagine di Aladin col campo; maniglia per ruotare, etichetta sotto il campo, in alto «← Cupola» e la scelta dell'immagine, zoom; in basso una barra sottile con Rotazione −/+, Mosaico ↔ ↕ −/+, Sovrapposizione (col mosaico), «Rimetti al centro».
- **Colonna a destra (396 px)**, carte in quest'ordine: Oggetto (tipo, nome, dati, altezza e pillola, progetto in corso), Stanotte (ore utili, curva con finestra, meridiano, Luna), Setup (tendina, campo, entra o no, Setup virtuale dentro la carta, Confronta), Come riprendere (SHO/HOO/LRGB, filtri con posa e ore −/+, totale e notti), Periodo migliore (12 mesi). In fondo, sempre a vista, la carta Salva con il riepilogo di una riga. Su schermi bassi scorre solo la colonna.
- **Telefono**: immagine in alto (54 %) con la sola Rotazione −/+; sotto quattro schede (Stanotte · Setup · Riprese · Oggetto) e Salva fisso. Il mosaico sta nella scheda Setup.
- Componente `PianoColonna`; cancellati `PianoStrumenti` e `CieloPiano4`.

## v45 — Il piano in Aladin rifatto da zero (24/10/2026, Marco)

Marco: la ricerca (Cupola, Sfera, Dentro) resta com'e'; il piano si rifa' da zero, prima l'usabilita' e il telefono, niente da scorrere, niente tasti grandi sopra l'immagine.

- Da Trova (Invio o clic) si vola sempre verso l'oggetto, poi si apre il piano.
- L'immagine di Aladin occupa tutta la carta. Sopra restano solo «← indietro», il nome con altezza e pillola, lo zoom e il credito.
- **Strumenti**: una barra verticale (a sinistra sul desktop, in basso a destra sul telefono) che si apre con un clic: Setup, Campo, Pose, Notte, Immagine, Salva. Un pannello alla volta; clic sull'immagine, × o Esc lo chiudono. Sul telefono il pannello e' un foglio con le sei schede in testa.
- Stanotte e Periodo migliore stanno nello strumento Notte; nel piano non c'e' niente sotto la carta.
- **Il piano in breve** (giro 2): in basso una barra con Setup, Campo (✓/!), Rotazione, Mosaico, Pose, Stanotte e «Salva il progetto»; ogni voce apre il suo strumento. Sul telefono quattro voci accanto al bottone degli strumenti.
- Rotazione: maniglia sul campo da trascinare in tondo, e quadrante nello strumento Campo (−/+ e 0°, 45°, 90°, 135°). Mosaico: griglia 6 × 6 da toccare. Setup: carte coi corredi, ognuna col suo campo e se l'oggetto entra. Salva: riepilogo del piano prima del bottone.
- Col pannello aperto l'immagine si sposta (a destra sul desktop, in su sul telefono) perche' il campo resti in vista.
- **Giro 3 (Marco: «e' tutto nascosto»)**: i comandi che servono sempre sono a vista. Barra in basso: Setup (tendina), Campo, Rotazione −/+, Mosaico ↔ e ↕ −/+, Pose, Salva. In alto a destra la carta Stanotte (curva, ore utili, finestra, piu' alto, Luna). Barra degli strumenti aperta di base; sul telefono sei icone sempre a vista e la barra in basso su due righe (Rotazione −/+, Campo, Setup, Pose, Salva).
- Supera v40–v42 per la fase di Aladin (scheda a destra, foglio a tre altezze, barretta di rotazione sull'immagine). Le tavole `Planner proposte` (1a, 1b, 2a) restano come archivio delle idee.

## v44 — Eventi nel linguaggio della carta (24/10/2026, da scegliere: A o B); Sistema solare: solo A

- **Sistema solare**: tolta la B (e il Tweak). Sotto i 1240 px la scheda passa da 362 a 300 px. Pianeti: se il campo e' piu' di 12 volte il disco, si parte zoomati sul pianeta e la riga dice «Il campo è N volte Giove: lo vedi intero con −».
- Nuovo `componenti/PlannerEventi2` (calcoli di `PlannerEventi`, template nuovo).
- **A · immersiva**: l'evento scelto nella carta scura alta (Sole o Luna col campo del setup e la traccia), titolo e ora in alto a sinistra; la scheda a destra con Eventi, tipo (Tutti · ISS · Eclissi · Occultazioni), periodo, l'elenco (scorre, 300 px) e sotto l'evento: avviso del Sole, «sei nella striscia» con lo schema, contatti, numeri, campo del setup.
- **B · riga del tempo**: una carta in alto con tipo, periodo e la riga del tempo (un punto per evento, etichette su tre file; oltre, solo il punto); sotto l'evento nella carta scura (8) e i dettagli (4).
- **Telefono** uguale per A e B: l'elenco; toccando un evento sopra compaiono la carta scura (× per chiudere) e i dettagli.
- Tweak `eventi` del Planner (o `?eventi=riga`).

## v43 — Sistema solare nel linguaggio della carta (24/10/2026, scelta di Marco: A · immersiva)

Marco: due varianti per pagina; forma e ordine li decide Claude. Si parte dal Sistema solare (Eventi dopo la scelta).

- Nuovo `componenti/PlannerSolare2`: stessi calcoli di `PlannerSolare` (disco, fase, mosaico, seeing, momento migliore, rapporto focale critico, salvataggio), template nuovo con inline. La scena ora misura anche l'altezza (prima fissa a 460).
- **A · immersiva**: la carta scura alta come il cielo profondo in Aladin; in alto a sinistra i corpi a pillole e la data (−1 g −1 h +1 h +1 g · Adesso); in basso la barretta rotazione · mosaico · cosa coprire · sovrapposizione; a destra la scheda: corpo, avviso del Sole, momento migliore grande, numeri a due colonne, setup (elenco + «+ Crea un setup virtuale»), evento e Salva. Sotto la curva della notte.
- **B · bento**: una carta coi corpi (segmentato) e la data; il disco in una carta scura (8 colonne) col nome sopra e la barretta sotto; a destra il momento migliore (protagonista) e i numeri; sotto la curva (8) e setup + salva (4).
- **Telefono** uguale per A e B: disco in alto col corpo in un elenco, zoom in basso a destra, rotazione in fondo; poi data e momento, numeri e mosaico, setup, curva, salva.
- Tweak `solare` del Planner (o `?solare=bento`). Nel telefono «Stanotte · Le mie riprese» e la legenda si vedono solo nel cielo profondo.

## v42.1 — Si chiama Planner (24/10/2026, Marco)

- `Carta del cielo v6.dc.html` diventa `Planner.dc.html`; nel telaio e nel menu la pagina si chiama «Planner». Cancellati la prima `Carta del cielo.dc.html` e `CieloPiano`. I link (Progetti, Piano della notte, Cerca, Menu) vanno a `Planner.dc.html`.
- Prossimo: Sistema solare ed Eventi nel linguaggio della carta (brief sotto, da approvare).

### Brief · Sistema solare (bozza)
- A cosa serve: inquadrare Luna, Sole e pianeti col proprio setup e scegliere quando (data, ora, seeing).
- Dati: posizione, diametro, fase e illuminazione, altezza lungo la notte, seeing simulato, campo e scala del setup, rapporto focale critico per filtro, mosaico per Luna e Sole.
- Stati difficili: Sole (avviso del filtro sempre visibile), corpo sotto l'orizzonte, pianeta troppo piccolo (sottocampionato), mosaico che non chiude, senza rete (niente mappa del Sole o della Luna), setup virtuale.
- La cosa piu' importante: il disco nel campo, grande, col momento migliore accanto.
- Cosa NON c'e': cielo profondo, liste di oggetti, ore da raggiungere.

### Brief · Eventi (bozza)
- A cosa serve: sapere quando e dove guardare per ISS davanti a Sole o Luna, eclissi, occultazioni.
- Dati: elenco dei prossimi eventi (periodo, tipo), per l'evento scelto ora, durata, striscia e distanza dal sito, campo del setup, contatti dell'eclisse.
- Stati difficili: fuori dalla striscia, evento sotto l'orizzonte, evento sul Sole (filtro), nessun evento nel periodo, senza sito.
- La cosa piu' importante: l'ora esatta e «sei nella striscia / fuori di N km».
- Cosa NON c'e': mappa geografica, previsioni calcolate dall'app (vengono dal servizio, simulate).

## v42 — La Carta del cielo v6 prende il posto del Planner (24/10/2026, Marco: «ok vai»)

- **Telefono in Aladin**: il piano e' un foglio da tirare su: basso (30%, nome, altezza, rotazione), meta' (52%), alto (88%); si tocca o si trascina la maniglia.
- **Immagine piu' svelta**: prima una piccola (un quarto), subito; poi quella buona. La piccola non prende mai il posto della buona.
- **Una curva sola**: in Aladin sotto la carta resta solo «Periodo migliore» (la curva della notte e' nella scheda). `CieloNotte` impara `notteOn`.
- **Tastiera su Aladin**: frecce per spostare il centro (Maiuscolo per passi lunghi), + e − per lo zoom.
- **Simulato** scritto sopra «Salva il progetto».
- **Nomi**: «Setup virtuale» anche in Sistema solare («+ Crea un setup virtuale», «virtuale», «Ottica virtuale»). Eventi: «linea centrale» sotto la linea, non piu' sopra il nome del sito.
- **Via il Planner**: cancellati `Planner`, Carta del cielo v2–v5, `CieloPiano2` e `CieloPiano3`. I link a `Planner.dc.html` (Progetti, Piano della notte, Cerca) vanno a `Carta del cielo v6.dc.html`, che legge gli stessi parametri di «Rinquadra». Menu: via la voce «Planner»; «Carta del cielo» apre la v6 («cosa riprendere e come: cielo profondo, Sistema solare, eventi»).
- Resta `Carta del cielo.dc.html` (la prima) con `CieloPiano`: da cancellare quando Marco lo dice.
- Da fare: Sistema solare ed Eventi nel linguaggio della v6 (oggi sono i componenti del Planner, coi nomi gia' allineati); la traccia dell'ISS sulla cupola.

## v41 — Carta del cielo v6: il cielo per cercare, Aladin per pianificare (24/10/2026, da provare)

Marco: nella cupola (e in Dentro, Sfera) niente immagini di Aladin; scelto l'oggetto la pagina cambia davvero: solo Aladin, da trascinare per migliorare l'inquadratura; «Indietro» solo in Aladin e torna dove si era; a destra la scheda dell'oggetto si allunga e diventa il piano (setup, confronto, filtri, ore, Salva). Claude: rotazione e pannelli sull'immagine, in una barretta in basso a sinistra; la legenda dei tipi in basso.

- **Il cielo**: mai immagini di Aladin, niente rettangolo del campo, niente «Immagine». La scheda piccola: «Pianifica» apre Aladin, «Vola fin lì» vola nella cupola e basta. Ricerca, lista e liste pronte aprono Aladin.
- **Aladin** (piano tangente, nord in alto, est a sinistra): il rettangolo resta al centro, il cielo si trascina sotto (rotella o + − per lo zoom). L'immagine (hips2fits) si chiede a carta ferma, 1,5 volte la vista; finche' non arriva resta quella di prima. In alto «← Cupola» (o Sfera, Dentro) e «Immagine»; in alto a destra centro RA/Dec, campo visto, credito. Senza rete: il rettangolo e la frase «niente immagine».
- **Barretta** in basso a sinistra: rotazione (± 1° e cursore), pannelli ↔ ↕, sovrapposizione col mosaico, «entra», «rimetti al centro».
- **Scheda a destra** (362 px, scorre dentro): oggetto, altezza adesso con la pillola, curva della notte; poi `CieloPiano4`: attrezzatura (confronto, provvisoria), filtri e ore, riepilogo, Salva.
- **Sotto la carta** restano Stanotte e Periodo migliore; il piano lungo non c'e' piu'.
- **Telefono**: Aladin sopra, il piano in un foglio fisso in basso (42%) con la barretta in testa.
- Il motore della cupola impara `immagini: false`.
- **Correzioni (24/10)**: un solo bottone, «Pianifica»: vola verso l'oggetto nella cupola (1,5 s) e poi apre Aladin; «Vola fin lì» resta solo per cio' che non si pianifica qui (pianeti, stelle). La legenda dei tipi sale sopra «12 sulla carta» quando c'e'. In Aladin la carta si allunga fin quasi a tutto lo schermo (desktop 100vh − 110, telefono 100svh − 120) cosi' piano e immagine si vedono interi.
- **Correzioni 2 (24/10)**: Aladin si apre solo a volo finito (il motore dice quanto dura: 3,4 s dalla cupola, 2,6 s da dentro) e compare in dissolvenza. Nel piano il setup e' un elenco a discesa (i quattro corredi e «Setup virtuale…», che prende il posto di «Provvisoria» e apre i suoi campi in un riquadro: focale, apertura, Barlow, sensore, camera); anche «A confronto» e' un elenco; sotto il setup il campo in piccolo, poi una riga e i filtri.
- **Correzioni 3 (24/10)**: sotto l'elenco del setup «+ Crea un setup virtuale» (e «← Torna a …» quando e' acceso); il setup virtuale non e' piu' una voce dell'elenco. Toccare Sole, Luna o un pianeta sulla carta (o sceglierli dalla ricerca) porta a Sistema solare col corpo gia' scelto. In Stanotte il link «Meteo di stanotte ↗», come nel Planner.

## v40 — Carta del cielo v5: cercare e inquadrare (24/10/2026, da provare: due posizioni dei comandi)

Marco: finche' si cerca, tutti i comandi del cielo; quando si vola o si inquadra, spariscono e restano l'immagine, la scelta della mappa, rotazione, pannelli e setup sopra l'immagine; a destra la scheda dell'oggetto con la curva e «Pianifica»; sotto, filtri e ore. Stanotte e Periodo migliore restano sotto.

- **Due momenti**: «Vola fin lì», «Inquadra sulla carta», una riga della lista o della ricerca su un oggetto del cielo profondo aprono l'inquadratura. Spariscono: Cielo profondo · Sistema solare · Eventi sopra il cielo (restano sopra la carta), viste, livelli, «Cosa mostrare», ricerca e criteri, legenda, lista coi numeri (anche sulla carta), barra della notte. Restano: zoom, scheda, «Immagine».
- **Uscita**: «← Torna al cielo» (telefono «← Cielo») ed Esc; si torna alla vista di prima del volo, oggetto e inquadratura restano.
- **Comandi sopra l'immagine** (Tweak «Comandi»): **fascia in basso** (larga fino alla scheda) o **colonna a sinistra** (300 px). Setup a pillole (Provvisoria compresa; i suoi numeri restano nel piano), rotazione ± 1° e cursore, pannelli in larghezza e in altezza, sovrapposizione col mosaico, campo ed «entra», centro spostato, il setup a confronto.
- **Il piano sotto**: una riga «FRA400 · 3,36° × 2,25° · rotazione 0°» con «Inquadra sulla carta ↑», poi solo filtri, ore e salvataggio (con la provvisoria anche i suoi dati).
- **Telefono**: «← Cielo» e il nome in alto, «Immagine» sotto; in basso un pannello (al massimo meta' carta) con setup che scorre, rotazione, pannelli e «Pianifica: filtri e ore ↓»; la scheda e i livelli sotto la carta spariscono finche' si inquadra.
- Il credito di Aladin passa sotto i bottoni in alto (la fascia occupa il basso).
- Componente `CieloPiano3` (v4 resta su `CieloPiano2`).

## v39 — Carta del cielo v4: il Planner dentro la carta (24/10/2026, prima fase, due disposizioni da scegliere)

Marco: v3 «stupenda» (Dentro, Cupola, Sfera, Le mie riprese); il Planner entra tutto nella Carta del cielo, poi il Planner si cancella.

### Brief
- A cosa serve: pianificare tutto da una pagina sola: cielo profondo, sistema solare, eventi.
- Dati: quelli di v3 piu' quelli del Planner (corredi, sensori, PlannerSolare, PlannerEventi), simulati.
- Stati difficili: senza sito, senza rete, mappa non disponibile, archivio vuoto, «entra nel campo» senza risultati, progetto doppione, ritorno da Progetti.
- La cosa piu' importante: scegliere cosa pianificare senza perdere il cielo.
- Cosa NON c'e': prossime 30 notti, confronto fra candidati, «Aggiungi a Piano della notte» (Marco non li ha scelti).

### Da portare dal Planner (scelti da Marco, tutti)
Sistema solare, Eventi, secondo setup a confronto, scelta della mappa (DSS, Hα, NSNS), provvisoria completa (apertura, Barlow, sensore cercato e personalizzato), inquadratura trascinabile e rotazione a 1°, ricerca online, salvataggio dentro la pagina (riepilogo, doppione, «Prima di salvare»), ritorno da Progetti, ore al minuto, stati difficili, telefono a passi. Nuovo: passaggio al meridiano nella curva di Stanotte.

### Fase 1 (questa): la scelta in alto
- «Cielo profondo · Sistema solare · Eventi» in alto (scelta di Marco). Sistema solare ed Eventi sono i componenti del Planner, cosi' come sono, coi corredi del Planner.
- Due disposizioni (Tweaks «Disposizione»): **A · il cielo resta**: la scelta e' il primo gruppo sopra il cielo; la carta resta e con Sistema solare vola alla Luna (il corpo di partenza); sotto, il componente al posto del piano. **B · la pagina cambia**: la scelta sta sopra la carta, sulla pagina; con Sistema solare ed Eventi il cielo sparisce e resta solo il componente.
- Telefono: la scelta a tre sopra il cielo (44 px); con Sistema solare la tiene il componente (ce l'ha gia').
- Tweak «Pianifica» per aprire la pagina su uno dei tre.
### Fase 2 (24/10): il resto del Planner nel cielo profondo
- **Attrezzatura**: provvisoria con apertura, Barlow o riduttore (moltiplica la focale), rapporto f/, sensore dal catalogo o «Personalizzato…» (pixel, larghezza, altezza). Accanto al campo il rapporto f/ anche per i corredi.
- **A confronto**: un secondo corredo, tratteggiato sulla carta (stesso centro e rotazione, un pannello), col suo campo e «entra / entra se lo ruoti / esce». Spento con la provvisoria.
- **Inquadratura**: rotazione a 1° (± e cursore 0–359°); il rettangolo si trascina sulla carta (cursore «sposta» sopra il rettangolo), «Centro spostato: 65′ a est · 48′ a nord · Rimetti al centro». Cambiando oggetto il centro torna sull'oggetto.
- **Immagine**: «Immagine» sopra il cielo quando c'e' un oggetto del cielo profondo: DSS2, PanSTARRS, Hα, OIII, SII, OIII · Hα · SII, Hα sud (le stesse del Planner). Se la mappa non copre l'oggetto resta DSS2 e il credito lo dice.
- **Ore al minuto**: ore e minuti si scrivono; ± resta a mezz'ora.
- **Salvare qui**: «Si salva: …» come riepilogo, poi «Salva il progetto» → «✓ salvato · Nuovo progetto … · Apri in Progetti ↗». Stesso oggetto e stesso corredo di un progetto: «Questo oggetto ha già un progetto con questo setup» con «Apri il progetto» e «Aggiungi queste ore».
- **Ritorno da Progetti** (`?da=progetto&n=…&c=…&rot=…&mos=…&fil=…&fatte=…&ob=…`, come il Planner): riga «Aperto da Progetti», «Aggiorna il progetto»; se cambiano rotazione, attrezzatura o centro, la finestra «Prima di salvare» (Annulla · Salva lo stesso).
- **Ricerca online**: senza risultati nel catalogo, la risposta di Sesame (simulata: Sh2-129); «Vola fin lì» la aggiunge alla carta e al piano.
- **Meridiano**: nella curva di Stanotte una riga punteggiata nell'accento all'ora del passaggio, in legenda «meridiano, 01:20: la montatura gira» e la riga «Passa al meridiano».
- **Telefono a passi**: nel piano «Attrezzatura · Inquadratura · Filtri e ore», uno alla volta.
- **Stati** (Tweak «Stato»): progetto iniziato, progetto doppione, due setup, provvisoria, mappa non disponibile, ricerca online, senza rete, senza sito, archivio vuoto, «entra nel campo» senza risultati.
- Componenti: `CieloPiano2` (v3 resta su `CieloPiano`); `cupola.js` impara centro spostato, secondo rettangolo, trascinamento e mappa (in aggiunta: v3 non cambia).
- Da fare: «Immagine» sul telefono; la traccia dell'ISS sulla cupola.

- **Scelta (24/10, Marco): B.** La cupola e il volo servono al cielo profondo; pianeti ed eventi si pianificano meglio con la loro vista intera. Resta una pagina sola con la scelta in alto, non tre pagine. Da riprendere piu' avanti: la traccia dell'ISS sulla cupola, l'unico punto dove il cielo aiuta gli eventi. A resta nei Tweaks finche' la fase 2 non la toglie.

## v36 — Selezione dei frame (23/10/2026, approvata e promossa a pagina fissa dall'utente; i giri sotto, dal piu' recente, superano il brief e la «Forma» iniziale)

Brief di Claude Code (ADR 0032; misure e giudizi da ADR 0022). Le etichette sono proposte: Marco le approva sulla tavola.

### Brief
- A cosa serve: scegliere quali frame entrano nello stacking, con le misure gia' fatte, raggruppate per gruppo (oggetto + setup + filtro), notte o setup.
- Dati: le misure di ADR 0022 per frame; i giudizi gia' decisi; le regole delle Impostazioni. Archivio simulato: M 31 · FRA400 + 2600MM · L (3 notti, 120 × 300 s, l'esempio della brief), M 31 Hα, NGC 7000 Hα, M 33 · Askar 103 + ATR2600M · L.
- Stati difficili: frame proposti da piu' regole, scelta a mano contro la regola, non misurati, in «scartati», errori dei file (NAS in sola lettura, disco staccato, file aperto), cancellazione.
- La cosa piu' importante: il riepilogo «110 di 120 frame tenuti · 9 h 10 di 10 h» e la proposta che resta una proposta.
- Cosa NON c'e': anteprima dell'immagine del frame (blink), cancellazione fuori da «scartati», regole che spostano da sole.

### Forma
- **Gruppo**: «Parti da» Un gruppo · Una notte · Un setup, poi le pillole col numero di frame. In una notte le sezioni sono gli oggetti; altrove le notti.
- **v36.4, ultimi ritocchi** (23/10, Claude Code): una classe di Bortle vale da sopra il suo limite (`sqm > x`). Le FWHM d'esempio stanno sopra 2 px nella scala del setup («non giudicabile su questo setup» lo decide F, non il numero). HFD = FWHM × 1,36 in tutte le pagine (una stella ha HFD ≥ FWHM); nella Selezione si alza la HFD d'esempio, non il rapporto.
- **v36.4, Misure dei frame** (23/10, Claude Code; Marco): i giudizi relativi del riepilogo (SNR basso per la notte e per l'oggetto, HFD alta per l'oggetto) a 2,5 MAD scalato, la stessa regola delle soglie; il minimo di 10 frame e' una scelta di Marco. SQM ↔ Bortle con la tabella di ASTAP (1 da 21.99 … 8 da 17.80), che supera la tabella di Wikipedia del 21/10.
- **v36.3, ritocchi di Claude Code** (23/10): eccentricità accesa parte a valore > 0,6 (scelta di Marco; nessuna soglia ufficiale, forum 0,5–0,6); «In scartate»; il motivo di una soglia dalla mediana dice il valore («FWHM > mediana + 2,5 MAD (3.42″)»); il cambio di tipo e' una modifica da applicare.
- **Ogni soglia sceglie** (23/10, l'utente): FWHM, eccentricità, stelle, SNR, fondo cielo e altezza hanno tutte «dalla mediana · valore» nella riga; le partenze restano quelle della v36.2 (2,5 MAD per FWHM, stelle, SNR, fondo; valore per eccentricità 0,55 e altezza 30°). Passando a «valore» parte da mediana ± 2,5 MAD del gruppo.
- **v36.2, le correzioni di Claude Code** (23/10, controllate contro ADR 0022 e 0032, glossario e fonti; Marco ha deciso i punti di prodotto; superano le partenze, «al limite» e lo spostamento dei giri sotto): partenze uguali per ogni setup, FWHM > mediana + 2,5 MAD, stelle e SNR < mediana − 2,5 MAD accese, eccentricità, fondo (2,5 MAD) e altezza (30°) spenti; MAD scalato 1,4826; FWHM anche a valore, con «sotto il limite del setup (F″): scarterebbe tutto». Al limite solo dalla mediana, entro 1 MAD. Gruppo = oggetto + setup + filtro + posa + guadagno: pillole «filtro · posa» quando servono. «Setup», non «corredo» (glossario). «scartate» nella radice dell'archivio con lo stesso percorso (WBPP scende nelle sottocartelle). Elimina nel cestino; senza cestino (NAS, Docker) «Elimina per sempre», «non si recuperano» solo li'. Riproduci con la velocità (0,1 · 0,3 · 0,5 · 1 · 2 s, partenza 0,5). Angoli e bordi 3 × 3.
- **Nel Telaio** (23/10): «Selezione dei frame» è una voce di «Altro» (computer: fra Carta del cielo e Attrezzatura, «prima dello stacking: togli i frame inutili»; telefono: nel menu Altro). La pagina passa al Telaio il suo nome, non piu' «Archivio». Gli ingressi restano anche da Progetti (scheda) e Notti (riepilogo).
- **Il telefono guarda, il computer decide** (23/10, l'utente): sul telefono la riga in testa dice «Qui guardi i frame e cosa segnano le soglie. Scartare, tenere e spostare si fa dal computer.»; niente ✕ ✓, Sposta, Annulla, Riporta indietro, Elimina, campo «Perché?», barra della selezione e «Soglie dei corredi ↗». Restano la scelta, il resoconto, i frame da rivedere uno alla volta (‹ › e dito, ▶, ingrandimento, schermo intero) e le soglie in sola lettura.
- **Ingresso da Notti** (23/10): nel riepilogo della notte, accanto a «Frame per frame», «Seleziona i frame ↗» (parametro `selezione` di `componenti/MisureFrame`, solo per la notte; nel simulato apre il 12 ottobre). Selezione dei frame legge anche ?modo= e ?accento=. **Contrasto**: testi controllati in scuro e chiaro coi cinque accenti, nessuno sotto 4,5:1 (3:1 i titoli); restano fuori dal controllo l'immagine simulata e i disegni dei grafici.
- **Settimo giro** (23/10): nel riquadro del frame Intero · Centro · Angoli sono icone in alto a destra sull'immagine, piu' «Schermo intero» (frecce, S, T, Esc per tornare); sotto l'immagine tre tasti tondi ✕ scarta · ▶ riproduci · ✓ tieni (non pollici: ✓ ✕ sono i segni degli stati). Al passaggio sul grafico il riquadro dice ✓ dentro / ! al limite / ✕ fuori con la soglia. **Tanti frame**: oltre circa 190 per filtro il grafico mostra una finestra con ‹ › e la striscia da toccare, e la finestra segue il frame del riquadro. **Telefono**: niente grafico; «Da rivedere» con Da scartare o al limite · Tutti, un frame alla volta (scorri col dito, ✕ ✓), le soglie applicate in sola lettura («si cambiano dal computer»). **Ingressi**: «Seleziona i frame ↗» nella scheda dei progetti in corso (Progetti); la pagina legge ?progetto= e ?notte=AAAA-MM-GG.
- **Sesto giro, dopo l'audit** (23/10, l'utente: «tutte cose sensate», niente RMS di guida: e' un dato di ripresa che l'app non ha): le soglie valgono per **corredo e filtro** (la formula per corredo); valori di partenza delle stelle per filtro (FRA400 L 900, Hα 400; Askar 103 L 700). Tutte le righe si scrivono in bozza e valgono solo dopo **Applica**; finche' no, «! modifiche da applicare» e il conteggio dice cosa scarterebbero. Il confronto si sceglie da un menu proprio (> maggiore di, ≥ da, < minore di, ≤ fino a). Sotto ogni riga «mediana · minimo–massimo» del gruppo, per le relative «vale …»; sotto 10 frame «la soglia non vale». Nuova soglia **Altezza** (spenta, sotto 30°); la fascia oraria si fa trascinando sul grafico. «Da scartare» dice il dettaglio per filtro e quanti sono a mano; «restano» dice quanti sono da misurare. Il riquadro del frame: Intero · Centro ingrandito · Angoli, e per lo scarto a mano il campo «Perché?». Un clic porta il frame nel riquadro; selezionare e' solo trascinare. In Impostazioni corredo e filtro.
- **Quinto giro, piu' compatta** (23/10, l'utente): «Da scartare» sale sopra il grafico come striscia bassa (numero, ore e MB, «restano per lo stacking», Annulla, Sposta). Le soglie vanno sotto il grafico, a destra del riquadro del frame, una riga alta 48: interruttore e nome · tendina del confronto · valore · unita' · quanti ne scarta. Niente piu' scelta valore/mediana: FWHM, eccentricità e stelle col valore (stelle FRA400 sotto 500, Askar 103 sotto 400), SNR e fondo dalla mediana in MAD. La formula ha la tendina «Aggiungi…» con misure e segni e vale solo dopo **Applica**; finche' non e' applicata lo dice col segno !. Stesse righe in Impostazioni.
- **Quarto giro, prima dello stacking** (23/10, l'utente; supera i giri precedenti dove diversi): la pagina serve a togliere i frame inutili prima di PixInsight, poi finisce. **Parti da** Un progetto in corso · Delle notti; l'archivio esce (e' gia' pulito). **Le soglie** in una carta sopra il grafico, come l'approvazione di SubframeSelector: FWHM, Eccentricità, Stelle, SNR, Fondo cielo, una riga ciascuna (interruttore, > ≥ < ≤, valore assoluto o MAD dalla mediana, quanti ne scarta), piu' la Formula (misure, _mediana _mad _min _max del gruppo, + − × ÷, parentesi, confronti, «e» «o»; vera = scarta). Per corredo, le stesse in Impostazioni › Selezione dei frame; partenza: FWHM ed eccentricità assolute (FRA400 3,1″, Askar 103 2,5″, 0,55), stelle e SNR mediana − 2 MAD, fondo spento. **Stati**: tenuto · da scartare (soglie o a mano) · tenuto a mano · in «scartati»; niente piu' «proposto» e «Applica». **Il riquadro del frame** a sinistra del grafico: immagine simulata con «Stretch uguale per tutti» (come il Blink) o «Per frame», ‹ › e Riproduci, le cinque misure col giudizio, Tieni / Scarta. Clic sul grafico porta il frame nel riquadro; Maiusc o trascinare selezionano; tastiera frecce, S, T. **Da scartare** (carta protagonista): numero, ore, «restano per lo stacking», Sposta in «scartati»; eliminare solo dalla carta «In scartati», con la conferma. La barra in basso solo con una selezione.
- **Terzo giro** (23/10, l'utente; supera il secondo giro per la carta della scelta e i grafici): via il riepilogo e la tabella dei frame. **La scelta**: a sinistra Parti da, la tendina con la ricerca e il calendario; a destra il resoconto: nome, corredo, una riga per filtro (frame tenuti di tutti, ore tenute di tutte). Per il progetto in piu' l'anello e le barre per filtro di Progetti, con le stesse classi; si aggiornano escludendo. «Una produzione» ora sceglie l'oggetto; il filtro si sceglie al grafico. **Il grafico** come «Frame per frame» del riepilogo: una barra per frame, Barre · Linee, Per ora · Per valore, la seconda misura a trattini con la scala a destra, un filtro alla volta. Stati: tenuto pieno, proposto contorno giallo, escluso contorno rosso a trattini, «scartati» spento; sotto l'asse il segno (● a mano, △ proposto, ✕ escluso, – scartati). Al passaggio la barra si accende nell'accento con la linea; il riquadro dice file, notte, ora, stato, il giudizio del frame e tutte le misure col valore, la soglia e ✓ dentro / ! al limite / ✕ fuori. Al limite: dalla parte buona, entro 1 MAD dalla soglia relativa o il 5 % da quella assoluta. Clic seleziona, trascinare prende un tratto, frecce e Invio da tastiera. **Barra in basso**: la selezione (Escludi · Tieni · Torna alla regola) e sempre Applica le proposte, Sposta in «scartati», Annulla.
- **La scelta, secondo giro** (23/10, l'utente; supera «Gruppo» qui sopra): «Parti da» Una produzione · Un progetto · Delle notti; il setup esce (lo stesso oggetto ad altezze e Lune diverse non si confronta). «Gruppo» si chiama produzione, come nell'Archivio. Produzione e progetto si scelgono da una tendina con la ricerca (gli oggetti dell'archivio dalla A alla Z; i progetti in corso), poi pillole: corredo · filtro per la produzione, Tutti i filtri · L · Hα per il progetto. A destra il calendario delle notti (come la Dashboard): accese con la stella le notti con frame della scelta, si tocca per sceglierne una o piu'; nessuna = tutte, «Tutte le notti» per tornare; in «Delle notti» almeno una, in partenza l'ultima. Il progresso del progetto conta sempre tutto il progetto. Apertura: l'ultima produzione ripresa (M 31 L).
- **I grafici, due misure** (23/10, Claude, chiesto dall'utente): la misura dal segmentato, «Confronta con» una seconda (tendina, nessuna in partenza) disegnata a tratti con la sua scala a destra e nel riquadro; «Punti · Linea» unisce i punti notte per notte. Mai piu' di due misure.
- **Un progetto** (23/10, l'utente): quarta voce di «Parti da». Pillole dei progetti in corso (simulati: M 31 L 14 h e Hα 8 h, NGC 7000 Hα 6 h, M 33 L 5 h; nel codice vero da Progetti e dalle produzioni dell'Archivio). Sotto, per filtro: percentuale dell'obiettivo coi soli frame tenuti, ore tenute di obiettivo, barra nell'accento con a tratteggio la parte tolta, «senza N frame tolti · prima X · Y %». Si aggiorna a ogni esclusione. Tabella per notte, come il gruppo.
- **Riepilogo** (carta protagonista): numero protagonista i frame tenuti, sotto l'integrazione e il peso su disco; barra degli stati con la legenda a segni (✓ tenuti · N a mano, ! proposti, ✕ esclusi a mano, ✕ esclusi dalle regole, → in «scartati», ? non misurati); a destra «Sposta in «scartati» · N», «Applica le proposte · N», «↶ Annulla l'ultima scelta» (ultime 30 scelte). Le righe a zero non si mostrano, tranne i tenuti.
- **Grafici**: una misura alla volta (segmentato). A sinistra il tempo, notte per notte, un punto per frame: tenuto pieno, tenuto a mano con l'anello, proposto anello giallo, escluso ✕ rosso, in «scartati» piccolo grigio, non misurato quadratino in fondo; selezionato anello nell'accento. Soglia della regola accesa tratteggiata con l'etichetta. A destra la distribuzione con la stessa scala: istogramma, scatola dei quartili, mediana, soglia; sotto mediana, quartili, MAD. Trascinare seleziona un'area (sul tempo un rettangolo, sulla distribuzione una fascia di valori); clic su un punto lo seleziona, Maiusc aggiunge; la selezione e' la stessa della tabella. Soglie solo partendo da un gruppo (con notte o setup cambiano per oggetto e filtro, e lo si dice).
- **Tabella**: ordinata in partenza per stato (le decisioni in alto), poi per ora; ogni intestazione ordina. Divisa per notte (o «Tutti insieme»), 10 frame per notte con «Mostra gli altri N» (la pagina resta leggera da catturare). Colonne: stato col segno e la regola, ora, posa, filtro, FWHM e HFD (″ e px), stelle, eccentricita' (direzione da 0,4), SNR, fondo cielo, gradiente, massa d'aria, luminosita' (solo L); giudizi in una pillola sola «! fuoco peggiore · SNR basso per la notte · …»; gesto per riga: Escludi / Tieni / Riammetti / Torna alla regola / Riporta indietro.
- **Selezione**: barra in basso, fissa nello scorrimento: «N selezionati · Escludi · Tieni · Torna alla regola · Riporta indietro · ×». Maiusc+clic seleziona un tratto della tabella.
- **Sposta in «scartati»**: finestra con le cartelle (da → \\scartati), frame e MB per cartella. Se ci sono proposte non applicate lo dice e offre «Sposta solo i N esclusi» o «Sposta tutti» (le proposte diventano esclusioni col nome della regola). Dopo: avviso ✓ con «Riporta indietro».
- **Errori**: l'avviso dice quanti ha fatto e quanti no e perche' («Spostati 3 di 10 frame · 7 non spostati. La cartella \\NAS\astro\2026-10-12\M 31\L sul NAS e' in sola lettura. Dai il permesso di scrittura, poi riprova.»), con «Riprova i 7». Uguale per Riporta indietro e Cancella.
- **In «scartati»**: carta con le cartelle, «Riporta indietro» per cartella e per tutti, «Cancella da «scartati»…» (bottone rosso). Finestra col segno !: «Cancellare N frame per sempre?», frame e GB, «e' per sempre: i file escono dal disco e non si recuperano».
- **Impostazioni › Selezione dei frame**: linguetta nuova fra Automazione e Servizi. Soglie per misura (interruttore con la parola, nome, «relativa al gruppo · tutti i gruppi · in M 31 L vale 3.68″», «propone 9 di 120 in …», Cambia: misura, relativa/assoluta, verso, quanti MAD o valore, vale per tutti i gruppi o un setup, Togli). Partenza: SNR sotto mediana − 2 MAD e HFD oltre mediana + 2 MAD accese, FWHM sopra 4.0″ spenta (esempio di assoluta). Espressioni: «Tieni i frame con» · «Escludi i frame con», campo, nomi delle misure e segni da toccare, «Si legge: …» o l'errore (misura sconosciuta, manca il segno, manca il numero, manca «e»/«o»), «Escluderebbe N frame su M nel gruppo …». Anteprima su un gruppo a scelta. «Come funzionano»: quattro righe.

### Regole del simulato (nel codice vero le calcola l'app)
- Stato di un frame: in «scartati» > escluso a mano > tenuto a mano > escluso dalle regole (applicato, col nome) > non misurato > proposto > tenuto. «Riammetti» su un frame che una regola prende lo segna «tenuto a mano».
- Soglie relative sul gruppo (oggetto + setup + filtro, tutte le notti, solo frame misurati, almeno 10). Un'espressione non tocca i frame a cui manca una misura che usa (per esempio la luminosita' con Hα).
- Esempio: HFD oltre mediana + 2 MAD propone 9 frame (8 del 12/10 con le nuvole, 1 del 5/10 col fuoco); tenuti a mano 2, esclusi a mano 3 (scia di satellite) → 110 di 120, 9 h 10 di 10 h; Sposta: 10 frame, 520 MB, 3 cartelle.

### Domande
- L'espressione dell'esempio («FWHM < 3.5 e Eccentricita' < 0.6 e Stelle > 300») descrive i frame buoni: l'ho fatta «Tieni i frame con», con l'alternativa «Escludi i frame con». Va bene cosi'?
- Da dove si entra: dall'Archivio (oggetto) e dalle Notti con un link, o una voce in «Altro»? Per ora la barra accende Archivio.
- Le proposte non applicate si spostano solo dopo la conferma nella finestra («Sposta tutti»). O «Sposta» deve prendere solo gli esclusi?

## v35 — Carta del cielo v3: il planner completo (22/10/2026, da provare)

**Ritocco (stesso giorno)**: sotto la carta prima **Il piano**, poi Stanotte e Periodo migliore. Il piano c'e' sempre, anche senza oggetto («Nessun oggetto»: attrezzatura, inquadratura e filtri restano pronti, Salva spento col perche'). Scegliere un oggetto del cielo profondo (tocco sulla carta, ricerca, lista, Vola fin li') lo mette nel piano e accende l'inquadratura: il rettangolo si vede finche' l'oggetto e' scelto, sparisce quando si guarda il cielo senza scelta. Il volo arriva con un campo che contiene tutto il rettangolo (1,9 volte il lato lungo). «Pianifica» nella scheda porta giu' al piano.

Marco sceglie la disposizione A di v2 (si tiene) e chiede di provare: niente lista sotto la carta, al suo posto tutto il planner dell'oggetto; via «Planner ↗» dalla scheda; tutti i criteri del Planner.

- **Sotto la carta**: «Stanotte · oggetto» (8 colonne): numero protagonista le ore utili; curva dalle 18 alle 07:30 con il buio astronomico in chiaro, l'orizzonte del sito lungo il cammino dell'oggetto, la Luna tratteggiata, i 30° tratteggiati, il tratto nell'accento dove l'oggetto e' utile, la riga dell'ora della barra; sotto finestra utile, piu' alto col buio, Luna, buio. «Periodo migliore» (4 colonne): ore utili il 15 di ogni mese, ✓ e accento dai 3 h (Impostazioni › Planner), settembre contornato, «Da agosto a gennaio». Poi «Il piano» a tutta larghezza. Senza oggetto: una carta che spiega e le tre liste pronte.
- **La lista sulla carta**: sotto la ricerca, larga 440, si chiude con ×; si riapre con «Lista» nella striscia dei numeri. Scegliere una riga la chiude, apre il piano e vola.
- **Criteri**: come nel Planner. Gli altri criteri stanno chiusi sotto «Altri criteri · N». «Entra nel campo» usa il campo del piano (mosaico compreso). Candidati: tutti gli oggetti con magnitudine fino a 11,5 o grandi almeno 8′ o con un nome (circa mille stanotte coi criteri di partenza); a parita' di ore vengono prima quelli col nome e i piu' luminosi.
- Semplificazioni da sapere: luminosita' superficiale dalla sola dimensione maggiore; la costellazione di un oggetto senza scheda e' quella col centro piu' vicino; «ora del piu' alto» al posto del transito (dentro il buio).

## v34 — Carta del cielo come Planner (22/10/2026, due disposizioni da scegliere)

Richiesta di Marco: la carta resta fissa e la ricerca in alto resta dov'e'; mancano i criteri di ricerca e la progettazione (ore, filtri, attrezzatura, campo, anche con un'attrezzatura provvisoria). Via «Alti alle …» e «Luna e pianeti»: stanno gia' in Dashboard. Il Planner di oggi resta in parallelo.

### Dal video di ATLAS (fotogrammi ogni 0,4 s, 9–26 s)
- Cercato M 31, la cupola gira e una linea viola chiaro collega l'oggetto e resta mentre l'ora cambia; dentro la cupola e' una retta che passa per l'oggetto.
- In Frame: il rettangolo del sensore ruotato (PA 0° → 284° → 308° → 324°), cerchi attorno, «Clipped»/«Fits», singolo o mosaico. L'immagine sotto, nei fotogrammi, quasi non si vede (registrazione scura).
- Da noi: il **filo dell'altezza** (il cerchio verticale dallo zenit all'orizzonte che passa per l'oggetto: dice dove guardare e quanto e' alto), nel colore dell'accento, che nel volo si disegna partendo dall'oggetto; il **rettangolo del sensore** ruotato dal Nord verso Est, col trattino sul lato alto, e l'etichetta «FRA400 · 3,36° × 2,25°»; sotto, l'immagine di Aladin larga quanto il campo. Niente cerchi concentrici.

### Forma
- **Criteri** accanto alla ricerca (bottone «Criteri», acceso nel colore dell'accento quando sono cambiati): altezza minima (Impostazioni › Planner, 30°), durata minima (1 h), distanza dalla Luna (40°, la Luna a meta' notte), direzione col buio, tipo, ordine (ore utili, altezza, nome). Valgono solo per «Migliori di stanotte»; la ricerca per nome li ignora.
- **Liste pronte** quando si apre la ricerca vuota, piccole: Migliori di stanotte, Progetti in corso, Le mie riprese, col numero. Default: Migliori di stanotte; con «Le mie riprese» acceso, Le mie riprese.
- **Numeri sulla carta**: le prime 12 righe della lista hanno lo stesso numero sulla carta e in lista (pallino nell'accento; il nome accanto solo se c'e' posto). In basso a sinistra la striscia «12 sulla carta · Migliori di stanotte · Nascondi».
- **Il piano**: si apre con «Pianifica» nella scheda o toccando una riga. Numero protagonista: le ore in tutto, con «circa N notti come stanotte» (ore utili sopra l'altezza minima col buio). Attrezzatura: i quattro corredi del Planner o «Provvisoria» (focale, sensore, mono o a colori; non si salva). Campo e scala. Inquadratura: rotazione a passi di 5°, pannelli in larghezza e altezza (1–6), sovrapposizione 10/15/20%, «✓ entra nel campo» / «! entra se lo ruoti» / «! esce dal campo» con il mosaico consigliato. Filtri: schema suggerito per tipo (SHO nebulose, HOO planetarie e resti, LRGB il resto; a colori Multibanda o Nessun filtro), solo i filtri del corredo, ± mezz'ora, «+ filtro» per gli altri. Con un progetto in corso le ore partono da quelle che mancano. «Salva come progetto ↗» porta a Progetti (spento con la provvisoria e senza ore, col perche').
- **Due disposizioni** (Tweaks «Disposizione» o `?disp=b`): **A** sotto la carta, lista (5 colonne) e piano (7) affiancati; **B** pannello di 400 px sulla carta, a schede «Lista · Piano», il centro della cupola si sposta a sinistra e la scheda dell'oggetto si mette accanto al pannello. Telefono: carta, poi lista e piano uno sotto l'altro, i criteri dentro la lista.
- **Accento del tema sopra il cielo**: `--cielo-accento` e' l'accento del modo scuro anche nel modo chiaro (il cielo resta scuro). Lo prendono: vista e lettura scelte, livelli accesi, «Adesso», cursore della barra, cerchio della selezione, filo, rettangoli del sensore, numeri della lista. Ambra #e9a23b, originale #b9a6ff, turchese #5ad1c8, corallo #ff9a7a, ghiaccio #9cc9ff, col testo scuro sopra (8–10:1).

### Da sapere
- Sh2-155 non e' in NGC/IC/Messier: entra con `ALcupola.aggiungi` (coordinate a mano), cosi' il progetto si trova e si inquadra.
- La distanza dalla Luna e' semplificata (un angolo fisso); nell'app vale la regola per oggetto di v30 (`luna.bersaglio`).
- Ore utili a passi di 15 minuti col buio astronomico; molti oggetti alti tutta la notte fanno 9 h pari: a parita' decide l'altezza massima.

## v33 — Carta del cielo (22/10/2026, prima versione, da approvare)

Richiesta di Marco: «una sfera 3D di tutto il cielo», sul modello della vista Dome di ATLAS (app di M102 Astro, vista nel video del 22/10); per ora una pagina a parte, il Planner resta com'e'. Si riprende l'idea della cupola e della barra dell'ora fatta col cielo; grafica e parole sono nostre.

### Brief
- A cosa serve: vedere il cielo di stanotte da Cima Ekar in 3D, trovare un oggetto e arrivarci; vedere dove si sono concentrate le riprese.
- Dati: stelle, oggetti, costellazioni e Via Lattea veri (d3-celestial); Sole, Luna e pianeti calcolati per l'ora; orizzonte del sito da `dati.js`; ore di posa dall'Archivio simulato (14 dei 240 oggetti, dichiarato a schermo).
- Stati difficili: oggetto sotto l'orizzonte (avviso con «Vai alle hh:mm» o «Cercalo sulla sfera»); oggetto che non sale stanotte; Aladin che non risponde o senza rete; cometa senza posizione; frame senza durata (Pleiadi).
- La cosa piu' importante: la cupola e il volo verso l'oggetto.
- Cosa NON c'e': inquadratura col sensore e invio a N.I.N.A., vista Universo (distanze), punteggio del Planner sugli oggetti.

### Forma
- Il cielo occupa la carta grande (fondo `--cielo`, scuro anche nel modo chiaro, come nel Planner). Sopra: vista (Dentro · Cupola · Sfera) e lettura (Stanotte · Le mie riprese) in alto a sinistra con la legenda sotto, «Trova un oggetto» in alto a destra, livelli a sinistra (Costellazioni, Via Lattea, Eclittica, Griglia, Nomi: pallino pieno = acceso), + e − a destra, barra del cielo in fondo.
- **Cupola**: la semisfera vista da fuori, il suolo scuro, l'orizzonte del sito come bordo, i punti cardinali (N, E, S, O) e «CIMA EKAR» al centro. **Sfera**: tutto il cielo col polo in alto, l'orizzonte diventa un cerchio. **Dentro**: dal centro, come al telescopio. Rotella o pizzico: da fuori ci si avvicina e si entra; da dentro si stringe il campo, allargando troppo si esce.
- **Il volo**: la cupola gira finche' l'oggetto e' dall'altra parte, poi si entra e il campo si stringe sulla misura dell'oggetto; all'arrivo l'immagine DSS2 a colori di Aladin (hips2fits, TAN) si posa sul cielo nel punto giusto, coi bordi sfumati. Credito «Aladin · DSS2 a colori, CDS». Anche avvicinandosi a mano: sotto i 14° di campo l'oggetto al centro prende la sua immagine.
- **Le mie riprese**: mappa di calore sulla sfera (ore di posa, scala fissa dal viola al giallo chiaro, numeri agli estremi), un anello per oggetto con le ore; la cupola si guarda dall'alto. Gli altri oggetti restano grigi.
- **Barra del cielo**: la notte dalle 18 alle 07:30 col colore del cielo calcolato dall'altezza del Sole (giorno, tramonto, crepuscoli, buio con le stelline), righe a tramonto, inizio e fine del buio, alba, la Luna sopra l'orizzonte come trattino chiaro in basso. Si trascina, frecce ±5 min, PagSu/PagGiu ±1 h; −1 h, +1 h, ▶ (la notte scorre), «Adesso» (simulato: 21:40).
- **Scheda**: tipo e costellazione, sigla, nome, magnitudine e misura; il numero protagonista e' l'altezza adesso con la pillola (✓ alto sopra i 30° di Impostazioni › Planner, ! basso, ✕ sotto, ✕ coperto dall'orizzonte del sito); curva dell'altezza della notte col buio in chiaro e i 30° tratteggiati; «Più alto stanotte», «Sopra i 30° col buio»; «Vola fin lì», «Archivio ↗», «Planner ↗». In Le mie riprese sopra c'e' il riquadro delle ore con BarraFiltri.
- Telefono: vista in alto, a destra Trova, livelli, + e −; la lettura sotto la carta; la scheda e' un foglio dal basso.

### Colori nuovi (fissi, sul fondo --cielo; oggi in `cupola.js`, da portare nel foglio)
- Tipi degli oggetti: galassie #ffbe85, nebulose #ff8aa0, planetarie #62dccb, resti di supernova #c39cff, ammassi aperti #94bcff, ammassi globulari #ffe07a (`--dso-*`). Sempre con la parola nella legenda e nella scheda.
- Calore: #3a2480 → #8c2f84 → #e2524a → #ffa94a → #fff1c2 (`--calore-*`).
- Cielo della barra, per altezza del Sole: 8° #7fa8d6, 2° #d9b27a, −1° #e07a4a, −4° #a8496d, −8° #3b3a7a, −12° #1c2050, −15.5° #0d102e, −18.5° #06070d (`--volta-*`).
- Linee: costellazioni #8d97c4, eclittica #e8b36a tratteggiata, griglia #6d7bb0 / #7f8cc0, guscio della cupola #7d8fe0.

### Da sapere
- La pagina e' stile inline (come si disegna); il passaggio alle classi `al-cielo__…` si fa con `strumenti/a-classi.js` quando la pagina e' approvata.
- Le catture del DOM non leggono il disegno WebGL: con la pagina nascosta il motore copia il cielo in un'immagine sopra la tela (al primo gesto esce). `window.__alMotore` per le prove.
- Posizioni a bassa precisione (Sole, Luna a pochi primi, pianeti dagli elementi di JPL): bastano per disegnare; nell'app li calcola il motore. La Luna della pagina (79%) e' quella vera del 30/09/2026, non quella simulata della Dashboard (62%).
- Domande: la Carta del cielo prende il posto di Aladin nel Planner, o resta a parte? Servono nella scheda i progetti e le notti dell'oggetto?

## v32 — Riordino prima del porting (20–21/10/2026, chiuso)

### Seconda passata (24/10/2026): la parte che il codice calcola
- Uno stato si scrive nel foglio, guidato dall'attributo ARIA che c'e' gia' (aria-selected, aria-checked, aria-pressed, aria-expanded) o da una classe `--<stato>` (`--acceso`, `--pericolo`, `--accesa`, `--spenta`…). La pagina passa solo dati: posizioni, larghezze in %, il colore di un filtro.
- Le trasparenze dell'accento sono token per modo × accento (rgba letterali, non color-mix: stesso valore calcolato di prima).
- Le misure per formato stanno nel foglio sotto `[data-formato="telefono"]`; dove il valore va a un componente che lo vuole come parametro (Carta) passa una variabile del foglio.
- Il componente fa la forma; il posto lo fa la pagina con `classe` (Pillola, PillolaScelta).
- Avanzamento e' un componente comune: le classi `al-prog__…` della Selezione erano le stesse dei Progetti.
- Campi e tendine restano sulle classi `al-campo` / `al-tendina`: Modulo e' un modulo intero, non un campo.
- Il controllo: impronte uguali a `screenshots/prima-passata2/` per misure, posizioni e colori; differenze ammesse solo nei tag (<a> → <button>) e in proprieta' senza effetto.

Brief di Claude Code «Riordino prima del porting (brief v1)». Non si ridisegna niente: aspetto e comportamenti restano identici, salvo le correzioni della sez. 6 della brief.

### Metodo di controllo
- Prima di toccare le pagine: `screenshots/prima-riordino/` (1202 catture: ogni stato dei Tweaks × desktop/telefono × scuro/chiaro) e una copia ferma di `pagine/` in `screenshots/prima-riordino/pagine/`.
- `strumenti/Confronto.html` apre lo stesso stato nella copia ferma e nella pagina di oggi e confronta l'impronta di ogni elemento (posizione, misure, 50 proprieta' di stile calcolate, testo, tracciati SVG). Uguale = uguale al pixel. Le catture servono all'occhio; il confronto vale anche sotto la parte catturata e con i cinque accenti.

### Token (fatto)
- `pagine/astrolog.css` v32: in testa i token, generati da `componenti/tema.js` (stessa fonte delle pagine), con il contrasto misurato accanto. Nomi di prima (`--carta`, `--tenue`…); nuovi: `--cielo`, `--luna-scura`, `--luna-chiara`, `--luna-linea`, `--sole`, `--setup-1…5` (i colori dei setup a confronto, il primo e' l'accento), `--prot-barra`, `--banda-colore`, `--banda-0…4`, raggi e durate.
- Il foglio lo carica `tema.js` (chi carica i token carica il foglio): nessun percorso da ripetere nelle pagine.
- Ogni componente e ogni pagina mette `data-modo` e `data-accento` su un involucro `display:contents`, dagli stessi valori dei suoi token (`t.modo`, `t.acc`): ogni componente resta corretto anche da solo e nelle tavole che mostrano i due modi insieme.
- Nelle pagine i colori del tema passano da `{{ t.carta }}` a `var(--carta)` (2 500 sostituzioni circa, 33 file). Restano da fare: i colori che il codice calcola (pillole, barre), gli attributi SVG `fill`/`stroke` (Statistiche, MisureFrame, Impostazioni), i colori esadecimali scritti nelle pagine.
- Colori scritti a mano tolti da pagine e componenti: tutti passano da `tema.js` (una fonte) e hanno il token gemello nel foglio: cielo disegnato (`--cielo-*`), corpi del Sistema solare (`--corpo-*`), Sole disegnato (`--sole-*`), marchio di Aladin (`--aladin-*`), fondo delle anteprime (`--foto-fondo`), umidita' (`--umidita`), i quattro strumenti della Capacita' (`--strumento-1…4`), il contrario del testo (`--inchiostro`), bordo del telefono (`--cornice-telefono`).
- Il foglio v17 resta in `pagine/foglio-v17.css` solo per la tavola Foglio, finche' non e' rifatta; poi esce.

### Formato e caricatore
- Il calcolo del formato (indirizzo `?formato=`, poi il parametro, poi automatico sotto 700 px) e' in un posto solo: `AL.formatoScelto(p)` e `AL.telefono(f, w)` in `tema.js`, usati da tutte le pagine e da MisureFrame e Riepilogo. Le tabelle `L` restano nelle pagine: sono le misure di quella pagina.
- Il caricatore `alPronto()` resta in ogni file: nel progetto di Design ogni file deve potersi aprire da solo e niente lo precede, quindi non puo' importarne un altro prima di aver caricato. Non si porta: nell'app i moduli si importano.

### Bottone (scelta di Marco, 20/10/2026: unificare)
- Una classe `al-bottone`: pillola 44 (36 `--piccolo`), testo 14 (13), peso 500 (600 nel pieno), spazio di lato 18 (14 piccolo e testo). Varianti: `--pieno`, `--contorno`, `--tenue` (+ `--rovescio` sopra carta-2), `--testo`, `--pericolo`, `--cielo`, `--cielo-pieno`; modificatori `--icona`, `--blocco`, `--a-sinistra`, `--a-filo`, `--sottolineato`. Disattivato con `aria-disabled`, in corso con `aria-busy`.
- Sul telefono ogni bottone e' alto almeno 44: lo dice il foglio (`[data-formato="telefono"]`, messo dal Telaio), non piu' le tabelle `L` delle pagine.
- La barra in alto, i suoi menu e Cerca restano come sono (brief, sez. 6): i loro bottoni non sono `al-bottone`.
- Fatti finora: 150 bottoni (i fissi di tutte le pagine e i gesti del Primo avvio). Restano quelli con i colori calcolati nel codice (scelte accese/spente): passano a `PillolaScelta` o al segmentato.
- Cosa cambia a schermo, misurato col confronto (stato predefinito): altezze da 37–40 a 44 o da 28–34 a 36, larghezze di 2–14 px per il nuovo spazio di lato. Archivio «+ Aggiungi oggetto», «Mostra altri 20»; Cerca «Planner ↗»; Da confermare «Cambia», «Rispondi»; Dashboard «Prossime notti», «Meteo ↗», «Statistiche ↗»; Meteo «Aggiorna», «Altri 8 fattori»; Misure dei frame «Usa Bortle 5», «Lascia Bortle 4», «Mostra sopra»; Notti «Apri Da confermare», «Apri», «Carica altre»; Piano della notte «blocchi», «Aggiungi», «Rifai il piano»; Planner «Mappa», «Centra sull'oggetto», le pillole Hα, OIII, SII (da 28 a 36), i bottoni rotondi del telefono; Progetti «Mostra tutti», «Apri il piano»; Primo avvio i gesti (spazio di lato da 20 a 18).

### Scelte: segmentato e linguette (unificati)
- `PillolaScelta` ora usa le classi `al-scelta` del foglio (aspetto identico, controllato: 40 confronti su 40 uguali).
- Il segmentato e' una forma sola: `al-scelta--segmentato` (fondo carta-2, una voce accesa nel colore della scelta). Con `--riempie` le voci si dividono la riga.
- Le linguette sono una cosa diversa dal segmentato e restano una forma a parte (decisione presa una volta): `al-scelta--linguette`, voci a contorno, una accesa piena nel colore della scelta. Sono le sezioni di Impostazioni e i gruppi a contorno di Piano della notte e Progetti.
- 23 gruppi fatti a mano portati sulle classi (Archivio, Impostazioni, Notti, Piano della notte, Planner, Progetti). Cosa cambia a schermo: le voci da 38 a 32 sul desktop (44 sul telefono), il peso della voce accesa da 600 a 500, nel Piano e in Progetti la voce accesa a contorno passa dal colore del testo a quello della scelta.
- Restano a parte, perche' sono forme diverse e si fanno con le loro pagine: le linguette sopra il cielo (Planner, PlannerSolare), le griglie a 5 e 3 colonne del telefono, la scelta del Bortle del Primo avvio, i tipi del Modulo, le produzioni del Riepilogo, SceltaTema, la Striscia, i filtri di MisureFrame.

### Finestra e Pannello
- Nuovo componente `Finestra` (`componenti/Finestra.dc.html`): titolo (con sottotitolo e, se serve, il segno «!»), ×, corpo, gesti in fondo (`al-finestra__gesti`). Esc e clic fuori chiudono; il fuoco entra nella finestra, resta dentro col Tab e torna dov'era alla chiusura. Sul telefono e' un foglio che sale dal basso, con la maniglia. Larghezze: stretta 440, media 780, larga 1180.
- La usano: Archivio «Aggiungi oggetto», Planner «Prima di salvare», il foglio del telefono del Piano della notte («Cosa si fa stanotte» e il blocco). FinestraRiepilogo resta il suo involucro (ha le frecce prima/dopo e il suo movimento).
- Cambia a schermo: in «Prima di salvare» il segno va accanto al titolo e compare la ×; nel foglio del Piano «Fatto» diventa ×; sul telefono «Aggiungi oggetto» diventa un foglio dal basso invece di una pagina intera.
- «Trova un oggetto» del Planner resta com'e': e' una ricerca con la sua tastiera, della stessa famiglia di Cerca (che la brief chiede di lasciare), non una finestra di gesti.
- Le scelte che si aprono sopra la carta senza velo (Setup del Planner e del Piano, Ordine di Progetti, Vista e ordine dell'Archivio) sono una cosa diversa: classe `al-pannello` (aspetto identico).

### Campo e tendina (unificati)
- Classi `al-campo` e `al-tendina` (foglio, sez. 2): 44 (36 `--piccolo` sul desktop, sempre 44 sul telefono), angoli 12, fondo carta-2 con l'anello della linea, testo 15 (16 sul telefono). Varianti `--rovescio`, `--vuoto`, `--tondo` (ricerche), `--numero`. Errore con `aria-invalid`. La tendina tiene la freccia del sistema; Modulo la sua freccia disegnata (`--freccia` + `al-tendina__freccia`).
- 90 campi e tendine fatti a mano portati sulle classi (Archivio, Da confermare, Impostazioni, Piano della notte, Planner, Primo avvio, Progetti, Statistiche, Filtri, PlannerEventi, PlannerSolare) e Modulo.
- Cambia a schermo: angoli da 10–14 a 12; i campi senza anello ora l'hanno; altezze a 44 o 36; nel Primo avvio e in Modulo il bordo diventa anello (stessa misura).
- Restano a parte: i cursori (`type="range"`), il campo dentro la ricerca di Cerca e di «Trova un oggetto».

### Riquadro, Quartili, Pillola, Segno
- Riquadro al passaggio: classi `al-riquadro` (titolo, righe etichetta · valore; `--lista` per le righe col pallino, `--etichetta` per l'etichetta piccola sopra un cursore). Lo usano tutti i grafici: Statistiche (9), MisureFrame, Dashboard, Meteo, Planner (2), PlannerSolare. Cambia a schermo: angoli 16 → 12, spazio fra le righe 5 → 4 in Dashboard, Meteo, Planner.
- Quartili: classi `al-quartili` (traccia, banda, mediana, soglia; `--piccolo`), in Misure dei frame e MisureFrame. Aspetto identico. In Statistiche i quartili sono le barre verticali del grafico a punti: forma del grafico, restano li'. Baffi e valore al passaggio non ci sono oggi in nessuna copia: non li ho aggiunti (nessun disegno nuovo).
- Pillola: il componente usa le classi `al-pillola` (`--buona`, `--incerta`, `--non-adatta`, `--mancante`, `--neutra`; misure). Le pillole dei giudizi fatte a mano in PlannerEventi ora usano le stesse classi (angoli e misure come le altre).
- Segno tondo da solo: `al-segno` (`--mancante` ?, `--avviso` !), in Misure dei frame.

### Correzioni della sez. 6 (fatte)
- Nebbia: `soglie.ora()` blocca con 'nebbia' (visibilita' sotto 1 km, `ALsoglie.nebbia`), come la pioggia; la visibilita' esce dalla trasparenza (`ALIAS` solo per l'aerosol). Dashboard e Meteo passano la nebbia.
- Fattore che manca: `ora()` divide i punti fra i fattori presenti e risponde anche `senza` (l'elenco di quelli mancanti). Da fare nelle pagine: la riga «senza seeing» negli stati «seeing senza chiave», «seeing parziale» e nelle notti passate (Notti, Statistiche).
- Seeing di 2.0″: buona fino a 2″ compreso (`x <= 2`). `seeingGiorno` resta `x < 2`: la brief parla solo del seeing della notte; domanda: vale anche per il Sole?
- Pianeti nel racconto della notte (Meteo): «culmina» da `planner.altS` (30°).
- Archivio: gruppo «Ripresa» → «Produzioni»; «Senza oggetti identificati»; con ASTAP assente «Non risolti» («1204 frame restano non risolti…»); «Aggiungi oggetto»: «buona · seeing …».
- Flat: «Sotto 20 flat la calibrazione aggiunge rumore.» (Impostazioni e la fonte in soglie.js).
- Il nome di Marco non compare piu': «nessuna convenzione: scegli tu» (Impostazioni, soglie.js; «giorni: nessuna convenzione, scegli tu» per i giorni della Luna).
- «bersaglio» → «oggetto» a schermo e nei commenti (la chiave `luna.bersaglio` resta: e' un nome di codice, non si vede).
- «pose» come conto → «frame» in Statistiche (cella, riga del riquadro, «… frame · N oggetti», «{n} frame senza massa d'aria esclusi.») e nelle unita' dei tempi di Impostazioni («secondi, frame, ore»).
- V50 fuori (Impostazioni, Cerca: «catalogo D80»). «Solo se la usi nel programma di ripresa.» Crepuscolo: «crepuscolo nautico · Sole sotto −6°».
- Scansione: «Interrotta a mano: …»; bloccata col motivo, «Riprova» e «Dettagli» (porta a Impostazioni › Scansioni).
- Da confermare: «… dopo la scansione.», «oggetti identificati».
- Piano della notte: «Nessun progetto alto più di {n} gradi stanotte.»
- MisureFrame: fuori la frase sulla FWHM di ASTAP. Riepilogo stati: «le misurerà sep: FWHM, HFD, segnale/rumore…».
- Riepilogo: «SNR mediano» solo quando l'oggetto ha una produzione sola; con piu' produzioni resta la FWHM.
- Notti stati (Lofoten): «ore utili».
- Dashboard stati: un documento solo. Tavola Telefono: aggiunte Statistiche e Misure dei frame.
- «corredo» nei Tweaks e nei commenti → «setup» (Attrezzatura, Misure dei frame: il parametro si chiama `setup`).
- Meteo: `pesaT` tolto (sez. 3).

### SQM e Bortle (sez. 5, fatto)
- Una tabella sola in `soglie.js` (`BORTLE`), quella dell'app e dei nomi del Primo avvio (voce «Bortle scale» di Wikipedia): limiti inferiori 1 = 21.76, 2 = 21.60, 3 = 21.30, 4 = 20.80, 5 = 19.25, 6 = 18.50, 7 = 18.00, 8 = 17.00, 9 sotto. Fuori quella di ASTAP / Clear Dark Sky. `bortleDi` ora arriva a 9.

### Pulizia (sez. 3, fatto)
- Usciti: `Meteo v4.dc.html`, `docs/proposte/` (11 file), le catture di lavoro vecchie in `screenshots/` (restano `prima-riordino/` e `tappe/`, che serve finche' il riordino non e' finito); i `per-claude-code-*.md` (11) spostati in `docs/archivio/`.
- `soglie.js`: fuori `verdetto`, `okta`, `oreSerene`, l'esportazione `lunaPartenza` e le varianti di prova della Luna nei Tweaks («25% · 50% · orizzonte», «10% · 25% · sopra 10°»; `usaLuna` legge solo le Impostazioni). `intervallo` resta: lo usano Dashboard e Meteo («dalle 21 alle 04, 7 ore»).
- `dati.js`: fuori `archivio`. `dati-statistiche.js`: fuori stelle, fondo e tipo per notte (il dado dei numeri simulati si tira lo stesso, cosi' gli altri numeri non cambiano); in Statistiche fuori il calcolo di `tipo` e `tb`.
- Restano, come chiede la brief: `PUNTI_GIORNO` col Sole basso, `puntoNotte`, `larghePassate`.
- `support.js`: restano le copie in `pagine/` e `componenti/` (ogni file .dc.html si apre da solo e carica `./support.js` accanto a se'; e' il motore del progetto di Design, non si porta); quella in radice la tiene il progetto di Design.
- `old/`: resta finche' il foglio al- non copre tutte le pagine (passo dopo).

### Impostazioni: quattro sezioni nuove (sez. 4, da approvare sulla tavola)
- Servizi, Scansioni, Diagnostica, Backup: nuove linguette, desktop e telefono, in un componente solo `componenti/SezioneServizi.dc.html` (parametro `sezione`), usato da Impostazioni nei due formati. Classi `al-imp-*` nel foglio, sez. 3.
- Tweak «stato» (gruppo «Sezioni nuove»): Servizi senza chiave / rifiutata / non raggiungibile (vale per Meteoblue; AAVSO attiva, TNS senza chiave); Scansioni nessuna / in corso / una bloccata / molti file non leggibili; Diagnostica ASTAP assente / errori; Backup mai scritto / ripristino al primo avvio.
- Le parole sono proposte (brief: Marco le approva sulla tavola): le righe d'introduzione, «Dove si prende ↗», «Ultimo tentativo», «Cambia», «Togli», «Verifica», «Rimasti fuori», «Non leggibili», «Interrompi», «Riprova», «Dettagli», «Copia» / «Copiato ✓», «Rimettile» / «Non ora», «Esporta» / «Importa», e quelle fisse della brief («L'app non manda niente da sola: copi tu e incolli dove vuoi.», «Ho trovato le tue risposte del {data}: le rimetto?»).
- Il menu dell'ingranaggio porta gia' a Impostazioni; «Dettagli» della scansione bloccata porta a Impostazioni › Scansioni (`?sezione=scansioni`).
- Domanda: la Diagnostica e' qui una linguetta di Impostazioni; l'ADR 0008 la mette in `/diagnostica`. Basta un indirizzo che apre la linguetta?

### Pagine sulle classi (fatto)
- Lo `style=` delle 15 pagine e della tavola Sistema e' passato nel foglio, sez. 3: un blocco per pagina, classi `al-<pagina>__<ruolo>-<n>` (codici: dash, meteo, notti, misure, arch, attr, conf, avvio, imp, cerca, plan, prog, piano, stat, sis). Inline restano solo le dichiarazioni con `{{ }}` (valori dai dati). Uno strumento solo, `strumenti/a-classi.js`, fa il passaggio: stesse dichiarazioni, stesso ordine; dove l'elemento aveva gia' una classe del foglio (bottone, campo…) la regola e' composta (`.al-campo.al-imp__blocco-4`) per vincere come prima vinceva lo stile scritto. `style-hover` e simili diventano `:hover`.
- I nomi sono meccanici (ruolo dal tipo di regola + numero), non di significato: si portano cosi' e si rinominano nel codice se serve. Domanda: li volete con nomi di significato prima del porting?
- Controllo: base ferma `screenshots/tappe/classi/` (le pagine un attimo prima). Dashboard 44/44, Meteo 92/92, Notti e Misure dei frame 100/100, Archivio e parte di Attrezzatura senza differenze; le altre otto pagine nei quattro stati base (desktop e telefono, scuro e chiaro) 32/32 uguali. Le differenze viste al primo giro erano pagine non ancora caricate: ripetute, uguali. Il confronto completo e' quello del passo «dopo».
- Meteo, lista degli eventi: lo stile scritto aveva una sfumatura in fondo (`mask-image`) che non si vedeva (il motore delle pagine non la applicava). Nel foglio l'avrebbe applicata: l'ho tolta per restare uguali. Domanda: la sfumatura la vogliamo?

### Senza seeing (fatto)
- `soglie.senzaRiga` scrive «senza seeing» solo per il seeing (la condensa di giorno e la trasparenza sotto le nuvole mancano per regola, non per un servizio).
- Meteo: «seeing senza chiave», «chiave non valida», «chiave appena messa»: «· senza seeing» in fondo alla riga sotto le ore utili e nel riquadro al passaggio («98 · nessun limite · senza seeing»). «Seeing parziale»: il seeing manca dalle 02 (come nella carta del seeing) anche nel punteggio; la riga compare nel riquadro delle ore senza seeing, non sotto le ore utili. Domanda: per il parziale serve una riga sotto le ore utili (per esempio «senza seeing dalle 02»)?
- Dashboard: nuovo stato nei Tweaks «seeing senza chiave» (non c'era): la carta del seeing resta con «?», «serve una chiave Meteoblue», «non disponibile», barrette spente; il punteggio si conta senza; «· senza seeing» dopo «qualità media».
- Notti: ogni notte passata con meteo ha «· senza seeing» dopo le ore utili (carta della notte, striscia, calendario).
- Statistiche: nel calendario, il riquadro della notte dice «qualità N · senza seeing» per le notti prima dell'app (come la nota «Notti prima del …: qualità senza seeing.»).
- Domanda: Notti e Statistiche non dicono la stessa cosa. Statistiche (gia' approvata) dice che dopo l'arrivo dell'app il seeing c'e' (la previsione salvata); la brief dice «notti passate» senza distinguere, e cosi' l'ho fatto in Notti. Vale la regola di Statistiche anche in Notti?

### Tavole (fatto)
- Foglio rifatto sulle classi vere v32 (bottone, pillola, scelta, campo e tendina, riquadro, quartili, segno, pannello, finestra, e una fila col formato telefono), accanto Pillola e PillolaScelta veri. Classi `al-foglio__*` nel foglio. `foglio-v17.css` uscito.
- Sistema: stessi pezzi, colori del tema da `{{ t.… }}` a `var(--…)` e stile nelle classi `al-sis__*`; confronto 2/2 uguale.
- Tavole degli stati e Telefono: i grigi della tavola sono token fissi `--tavola-*` (foglio, sez. 1, col contrasto; gemelli in `AL.TAVOLA`); ogni tavola carica il foglio. `old/` uscita (95 file): nessuna pagina la apriva.

### Catture «dopo» e confronto completo (21/10/2026)
- `screenshots/dopo-riordino/`: 1202 catture, stesso `_elenco.json`. Nome `NN-dIIII.jpg`: stato numero IIII+NN−1 dell'elenco (`01-d0959.jpg` = 959). Le impronte stanno in `localStorage` (`al-riordino-dopo`, `al-confronto`) del progetto.
- Confronto con `prima-riordino/pagine/`, elemento per elemento senza le posizioni (uno spostamento conta solo dalla sua causa): 948 stati uguali al pixel su 1202 con le pagine al loro posto; 40 non confrontabili (sotto); gli altri diversi per le voci qui sotto. `Confronto.html#sinc=1&riassunto=1` (un passo per chiamata, `__s()`), ricarica a ogni cambio di pagina.
- `screenshots/tappe/` uscita (261 file).

Differenze attese (gia' decise, da guardare sulle catture):
- Bottoni 44/36, spazio di lato 18/14, peso 500 (tutte le pagine; Primo avvio i gesti 20 → 18).
- Scelte: segmentato e linguette (voci 32 sul desktop, 44 sul telefono, accesa a 500); campi e tendine (angoli 12, anello, 36/44, testo 13 sul desktop e 16 sul telefono: anche le voci delle tendine di Statistiche e Planner).
- Riquadro al passaggio (Dashboard, Meteo, Planner: interlinea e spazi).
- Sez. 6: «oggetti identificati» (Da confermare), la frase di ASTAP fuori da MisureFrame (Misure dei frame, Riepilogo), «senza seeing» (Meteo, Notti, Dashboard, Statistiche), «Apri in Attrezzatura ↗» nel Riepilogo come bottone.
- Impostazioni: le quattro linguette nuove (desktop e telefono).
- Foglio rifatto (1453 → 163 elementi); Sistema: i pezzi veri al posto dei disegnati.

Corretto in questo giro:
- Segmentato sul telefono: con le voci a 44 e 14 di lato, in Archivio («Deep sky · Sole · Sistema solare») e nella striscia delle notti (Notti) le voci non stanno piu' nella riga e compariva la barra di scorrimento (nel modo scuro una fascia chiara sotto). `al-scelta--segmentato` ora la nasconde (`scrollbar-width: none`), come le altre strisce del foglio; si scorre col dito.

Da approvare:
- Archivio e Notti sul telefono: anche senza barra, «Sistema solare» e le ultime notti escono dalla riga e si scorrono (prima le voci avevano 6 di lato e ci stavano). Va bene cosi', o sul telefono le voci del segmentato tornano a 6 di lato?
- Il collegamento della barra in alto (e i bottoni a testo) ha ora `gap: 6px`: a schermo non cambia niente (non e' una fila), lo segnalo solo perche' il confronto lo vede.

Non confrontabili (40): gli stati coi Tweak della Luna di prima («25% · 50% · orizzonte», «10% · 25% · sopra 10°»: Impostazioni, Meteo, Piano della notte, Planner), che sono usciti con la pulizia, e due fasi della Luna del Piano («primo quarto, 50%», «piena, 100%»): il «%» rompe l'indirizzo di Cattura, la pagina resta vuota anche nella copia di prima. Le due fasi vanno guardate a mano.

Da ricontrollare: in Primo avvio parte delle differenze sono il confronto preso a meta' del cambio di modo (scuro da una parte, chiaro dall'altra); le vere sono i gesti a 18 di lato.

### Colori dei tipi nel Piano della notte (21/10/2026, Marco)
- La barretta a sinistra (e il segno) di ogni blocco ha il colore del suo tipo, come i progetti: Sole col colore del filtro (luce bianca, Hα), pianeti col loro, Luna il grigio, e per la Ricerca toni nuovi, fuori dai filtri: esopianeta lime, binaria a eclisse rosa, variabile e AAVSO sabbia, NEO ruggine, supernova giallo chiaro, cometa ghiaccio, eventi a ora fissa (ISS) grigio. `t.tipi` in tema.js, `--tipo-*` nel foglio. Il tipo resta scritto: il colore non e' mai da solo.

### Componenti sulle classi (21/10/2026)
- I 25 componenti di `pagine/componenti/` sono sulle classi: 686 regole `al-c-<nome>__<ruolo>-<n>` in fondo alla sez. 2 di `astrolog.css` (stesso strumento delle pagine, `strumenti/a-classi.js`). Inline restano solo i valori dai dati.
- Confronto con la copia ferma di prima (`screenshots/dopo-riordino/pagine/`): tutti i 1202 stati uguali, salvo quelli che lo strumento non apre (stati col «%», Piano della notte telefono, che carica i telefoni solo quando si vedono).
- Catture finali (21/10/2026): `screenshots/finali/`, 1202 stati; prima e dopo del riordino uscite (anche la copia ferma `dopo-riordino/pagine/`).

### Risposte di Marco (21/10/2026)
- Seeing di giorno: stesse soglie della notte, buono fino a 2″ compreso (`seeingGiorno` ora `x <= 2`).
- Diagnostica: resta la linguetta di Impostazioni; `/diagnostica` apre la linguetta.
- Planner: campi di ore, minuti, posa, colonne e Luna allargati (64–72 px), il numero non sta piu' sotto le frecce.
- `--male` chiaro: #d0503e → #bf4232 (5.2:1 su carta, 4.7 su carta-2), stessa tinta piu' scura.
- Classi: si fa come chiede il porting.
- Notti sul telefono: la striscia si scorre, va bene. Archivio sul telefono: «Deep sky · Sole · Sistema solare» deve stare intera; le voci del segmentato che riempie la riga tornano a 6 di lato sul telefono.
- Segmentato piccolo sul telefono: 44 px come tutti gli altri bersagli (Marco: uniformare).

### Domande (gia' fatte)
- Seeing del giorno (Sole): `seeingGiorno` resta `x < 2`; la notte ora e' «buona fino a 2″ compreso». Vale anche di giorno?
- Diagnostica: e' una linguetta di Impostazioni; l'ADR 0008 la mette in `/diagnostica`. Basta un indirizzo che apre la linguetta?
- Planner, «Crea il progetto»: i campi di ore, minuti e posa sono larghi 44–52 px e le frecce del sistema coprono il numero (era gia' cosi'). Li allargo o tolgo le frecce?
- Segmentato piccolo sul telefono: 38 px, sotto i 44 del bersaglio. L'ho lasciato com'era; lo porto a 44?
- `--male` nel modo chiaro (#d0503e) sta a 4.3:1 sulla carta bianca, sotto 4.5. Dove e' testo piccolo serve un tono piu' scuro? Non l'ho cambiato (nessun colore nuovo senza decisione).
- Il sistema delle Design Component preferisce lo stile scritto sull'elemento (la pagina si disegna mentre arriva); il foglio unico lo chiede il porting. Le classi entrano comunque; l'unico costo e' che nel progetto di Design le pagine aspettano il foglio prima di colorarsi.

## Si riparte da zero (17 ottobre 2026)

- La dashboard "bento" (variante densa, ex 2c) e' la base definitiva:
  `pagine/Dashboard.dc.html`. Le varianti 2a, 2b, crema e giallo e la copia
  con barra laterale escono.
- Il vecchio sistema va in `old/` in sola lettura; si cancella pagina per
  pagina man mano che si rifa'.
- Tutte le pagine si rifanno nel linguaggio nuovo prima di passare a Claude
  Code, che riparte dal design nuovo.

## Navigazione

- Barra in alto (la laterale e' stata provata e scartata: toglie spazio al
  grafico della notte). In vista: Dashboard, Notti, Archivio, Progetti,
  Statistiche, Meteo; "Altro" e' un menu con Planner, Carta del cielo,
  Attrezzatura.
- A destra: sito, "Da confermare" (pillola che pulsa finche' restano frame,
  con menu dell'ultima notte), Cerca (Ctrl K, apre anche le pagine), modo
  chiaro/scuro, Impostazioni (con Scansiona ora e Modo automatico).
- I menu si chiudono cliccando fuori o con Esc; le voci si scorrono con le frecce.

## Temi

- Due scelte separate: modo (chiaro, scuro, poi automatico: scuro dal tramonto
  all'alba) e accento: originale (lavanda / verde bosco), ambra · blu notte,
  turchese · petrolio, corallo · terracotta, ghiaccio · indaco.
- Accento predefinito: ambra · blu notte (17 ottobre 2026).
- Il selettore completo sta in Impostazioni; nella barra solo il modo.
- I colori con un significato non cambiano col tema; se un accento li ricorda,
  si sposta l'accento.
- Luna: un solo grigio ovunque, `#8a8474` (sopra 3:1 sul bianco e sul nero,
  vale come forma); disco crema `#ece6d6` su antracite `#2e3038`.
- Toni per il contrasto: pianeti sul chiaro #8a6a14 · #9a5420 · #b0321c ·
  #6f6440; curve dei progetti sul chiaro #8a5e0a · #2a62a6 · #6e44a3 · #b04432;
  ambra scuro #e9a23b; corallo scuro #ff9a7a; terracotta chiaro #8f3a22.
- Filtri: tutti quelli del vecchio sistema, con le sue tinte (gia' provate a
  3:1 e distinte fra loro): L, R, G, B, Ha, Hb, OIII, SII, a colori LP, a
  colori UV/IR; a piu' bande (a colori, Ha + OIII, SII + OIII, tribanda,
  quadribanda) a strisce oblique da 3 px; sconosciuto vuoto e tratteggiato.
  Sostituiscono le tinte provvisorie della Dashboard (17 ottobre 2026).
- Pianeti e filtri nei colori di convenzione. Aggiunti Mercurio, Urano e
  Nettuno (17 ottobre 2026): scuro #b8b0a4 · #7fd3d6 · #7f9cff, chiaro
  #6b6660 · #1d7a80 · #3450b0, tutti sopra 5:1.

## Dashboard

- **Grafico della notte**, tre viste: Notte (qualita' + Luna), Progetti
  (altezze, linea a 30°, ore utili in tratto spesso), Sistema solare. Il numero
  grande segue la vista. Fasce del crepuscolo a gradini con gli orari ai
  confini; linee sottili (1,75 la principale, 1,25 le altre); marcatore a punto
  bianco con anello e alone.
- **Qualita' della notte**: il punteggio ora per ora calcolato dall'app (vedi
  "v10 · La qualità"). Il riquadro dice cosa limita; la card meteo
  corrispondente si accende. Il dettaglio sta in Meteo.
- **Luna · Sole** nella stessa carta, senza cambio d'altezza. Luna: disco,
  pillole, calendario con notti buone, stelline di ripresa (scheda della notte
  → Notti), Luna nuova e piena. Sole: regioni attive, finestra di ripresa di
  domani con seeing di giorno, Kp a tre giorni, aurora.
- **Meteo**: sei card con valore, mini-grafico, nota e giudizio.
- **Progetti**: righe con anello piccolo e barra dei filtri a segmenti;
  ordine "Per ore" / "Meglio stanotte".
- **Prossime 3 notti**: mini-curva con la stessa grammatica del grafico grande.
- **Il 2026** contro il 2025 tratteggiato; **Filtri del 2026** ad anello.

## Gli stati della Dashboard (17 ottobre 2026, approvati)

Brief. **A cosa serve**: che la Dashboard dica qualcosa di utile anche quando
mancano dati, mai un buco e mai un numero finto. **Dati**: gli stessi, con
quello che c'e' davvero. **Stati difficili**: archivio vuoto, caricamento,
previsione assente, notte coperta. **La cosa piu' importante**: si capisce
cosa manca e cosa fare, con un'azione sola in evidenza. **Cosa non c'e'**:
illustrazioni per il vuoto, pagine diverse dalla Dashboard.

Sono un parametro della pagina (`stato`); la tavola e' `pagine/Dashboard stati.dc.html`.
- **Prima volta** (sito scelto, archivio vuoto): notte, Luna, meteo e prossime
  notti ci sono gia'. Via la pillola "Da confermare", la vista Progetti, le
  stelline. Al posto di progetti, anno e filtri: "Per cominciare" con due passi
  (1 Scegli la cartella, primario; 2 Crea un progetto, spento) e l'anno
  vuoto a barre tratteggiate.
- **Caricamento**: scheletro con le misure delle carte vere, barra vera,
  "Caricamento…".
- **Meteo non raggiungibile**: in testa il buio calcolato ("9 ore",
  "? senza meteo"); il grafico tiene crepuscolo e Luna, la qualita' sparisce.
  Il meteo diventa una riga "Meteo non raggiungibile" con "Riprova ora" e
  sei caselle "? Non disponibile"; le prossime notti danno il buio senza Luna.
- **Notte coperta**: la pagina resta quella. "Nessuna ora · ✕ notte coperta",
  la frase dice la prossima notte buona. Le card meteo mettono la causa
  (nuvole, pioggia, umidita', condensa, vento, jet stream): seeing e aerosol
  sotto le nubi non si misurano.

## La Dashboard sul telefono (17 ottobre 2026, approvata)

Stessa pagina, formato "telefono" (automatico sotto 700 px). Tavola: `pagine/Dashboard stati.dc.html`, riga in alto.
- In alto: segno, sito, "Da confermare" come icona con il numero, Cerca. In basso la
  barra fissa: Dashboard, Notti, Archivio, Meteo, Altro (menu con Progetti,
  Statistiche, Planner, Carta del cielo, Attrezzatura, modo, Impostazioni).
- Ordine: stanotte, Luna · Sole, meteo (striscia scorrevole), progetti a righe,
  prossime notti, anno con i filtri. Il calendario si apre toccandolo.
- Il grafico si usa col dito; il riquadro dei valori compare solo toccando e sta
  sopra il grafico, per non coprire il numero. Sulle fasce restano quattro orari:
  tramonto, buio, fine del buio, alba.
- Bersagli da 44 px.

## Accessibilita' (17 ottobre 2026)

- Il grafico della notte e' un cursore: si raggiunge col tasto Tab, frecce per
  15 minuti, Maiuscolo + frecce per un'ora, Inizio e Fine. Il lettore di schermo
  legge la frase della vista (etichetta, numero, frase sotto) e il valore all'ora
  scelta. Sul telefono si trascina col dito.
- Contrasto misurato sulle 10 combinazioni (2 modi × 5 accenti): 230 coppie,
  nessuna sotto soglia (4,5:1 il testo, 3:1 le forme).
- Movimento ridotto: col sistema che lo chiede si fermano pulsazioni, scheletro
  e transizioni.

## Animazioni (17 ottobre 2026)

- **Notti, Archivio e riepilogo** (17 ottobre, seconda parte), in
  \`componenti/moto.js\` (\`ALmoto\`, Web Animations API, niente stato): cambio di
  notte, numero che sale e barre di oggetti e filtri che si riempiono (0,6 s);
  casella della striscia che cambia colore in 0,2 s; righe di "A confronto"
  in fila (40 ms) quando cambiano i filtri. Archivio: carte in entrata come
  nella Dashboard, conto che scorre, carte che si riassestano (0,3 s).
  Riepilogo: si apre salendo (finestra 0,25 s, telefono dal basso 0,32 s), si
  chiude al contrario piu' in fretta; con ‹ › il contenuto scivola dalla parte
  della freccia; le curve si disegnano in 0,8 s a ogni cambio di metrica,
  filtro, ordine, produzione; miniature una volta; puntatore con ritardo
  morbido di circa 0,16 s.

Poche e con uno scopo; nulla su pillole, menu e calendario. Spente col movimento ridotto.
- Cambio vista del grafico: le curve si disegnano in 0,8 s, area e alone sfumano, il numero grande sale e sfuma.
- Arrivo della pagina: le carte entrano in fila (60 ms l'una), solo quando entrano nello schermo.
- Puntatore: linea, marcatori e riquadro seguono con 0,16 s di ritardo morbido.
- Anelli dei progetti e dei filtri si riempiono, barre dell'anno crescono, una volta sola.

## Token, telaio e mattoni (17 ottobre 2026)

- Per ora c'e' una tavola di riferimento, `pagine/Sistema.dc.html`: token (2 modi ×
  5 accenti, con il contrasto misurato), colori con un significato, caratteri,
  misure, telaio desktop e telefono coi menu, dodici mattoni con la regola d'uso.
- (superato, vedi sotto) Le pagine copiavano markup e funzione `tema()` dalla tavola.
- Nomi italiani dei token: pagina, telaio, carta, carta2, linea, testo, tenue,
  attivo, su attivo, accento, su accento, barre anno, binario, spento, riquadro,
  avviso, male, da confermare, esito buono / incerto / no.

## Meteo (17 ottobre 2026)

Brief. **A cosa serve**: decidere se e quando uscire nelle prossime sette notti,
e capire perche'; e' il dettaglio a cui rimanda la Dashboard. **Dati**: sette
notti (tre ora per ora, quattro di tendenza) con esito e ore di buio sereno; il
cielo dal tramonto all'alba; otto misure con esito e tre senza; cosa pesa;
modello, eta' della previsione, fonti. **Stati difficili**: quelli sotto.
**La cosa piu' importante**: l'esito della notte scelta, con le ore e cosa la
limita. **Cosa non c'e'**: Luna e Sole in dettaglio (Dashboard), progetti,
mappe e radar.

Pagina `pagine/Meteo.dc.html` (Tweaks: Stato, Formato, modo, accento); tavola
`pagine/Meteo stati.dc.html`, sedici telefoni e quattro desktop.
- **Le notti**: carta in testa col titolo, l'eta' della previsione (anche del
  seeing), il modello (Automatico, ECMWF, ICON, GFS: pillole sul desktop, menu
  sul telefono) e Aggiorna. Sotto sette caselle: le tre ora per ora piene, con le
  barrette delle nuvole; le quattro di tendenza tratteggiate. Quella scelta e'
  piena del colore del testo. Sul telefono scorrono di lato.
- **La notte** (carta protagonista, 8 colonne): ore di buio sereno, esito,
  orario e accordo dei modelli. Il cielo: nubi basse, medie e alte sovrapposte,
  ognuna dal suo zero (piu' scure le basse), umidita' tratteggiata sulla stessa
  scala in %, fasce del crepuscolo come nella Dashboard. A destra una misura alla
  volta (all'apertura nessuna): il tratto prende il colore e lo spessore
  dell'esito, e la parola compare dove cambia. Notti di tendenza: le fasce e una
  linea alla media delle nuvole, "senza dettaglio orario".
- **Cosa pesa**: superato, vedi "Come va la notte / il giorno" piu' sotto.
- **Le misure**: otto carte (mattone card meteo) in ordine di peso: nuvole,
  poi chi pesa di piu' e da prima. Valore della notte, barrette, nota, picco,
  esito con l'ora. Passando sul cielo tutte vanno a quell'ora; uscendo tornano
  alla notte. Cliccata, una carta va sulla scala di destra. Nuvole basse non ha
  piu' una carta sua: sta nel grafico e nel riquadro dei valori.
- **Altre misure**, senza esito: temperatura e rugiada, polveri, vento a 700 hPa.
- **Telefono**: stesso ordine; carte a due colonne che si aprono sotto la loro
  riga, una alla volta, con "Metti sul grafico". Bersagli da 44.
- Le soglie delle barrette sono quelle dell'app (vedi "v10 · La qualità"),
  uguali nella Dashboard.

Il grafico, seconda versione (17 ottobre 2026):
- **Deep sky / Sole**, pillola in testa alla carta della notte (predefinito nel
  parametro `obiettivo`, poi dalle Impostazioni). Cambia tutta la pagina: in Sole
  le caselle sono i sette giorni (da domani; tre ora per ora, quattro di
  tendenza), il grafico va dalle 06 alle 20 con l'altezza del Sole, l'esito sono
  le ore di Sole sereno sopra 15°, misure e "cosa pesa" contano le ore dalle 08
  alle 18; niente condensa; in "cosa pesa" il Sole al posto della Luna, in fondo
  le ore di Sole e il seeing migliore. Le finestre restano di 14 ore: con 12 si
  perderebbe il crepuscolo.
- **Piu' misure insieme**, fino a quattro, scelte con pillole a spunta. L'umidita'
  non c'e' piu' all'apertura: e' una voce come le altre. Umidita' e pioggia (in
  probabilita') stanno sulla scala in % di sinistra; le altre non hanno scala:
  si confronta la forma, i valori si leggono col puntatore.
- Ogni misura ha un colore suo (curve dei progetti, mai l'accento, mai il blu
  dell'umidita' quando c'e'); l'esito si legge dallo spessore (1,75 / 3 / 4,25) e
  da un segno ! o ✕ nel punto dove peggiora. Fuori dalla finestra il tratto e'
  sottile e tenue.
- Luna (nella notte) e Sole (nel giorno) tratteggiati, altezza sulla scala in %.
- **Ore utili e verdetto vengono dalla qualità**: ore della finestra con
  qualita' da 60 in su; il verdetto dall'app (vedi "v10 · La qualità"). Il
  "seeing migliore" e' l'ora utile col seeing piu' basso. Il numero grande dice
  "ore utili", come la Dashboard.
- **Come va la notte / il giorno** prende il posto di "Cosa pesa": la storia ora
  per ora (tratti con lo stesso esito e la stessa causa: "03:00–05:00 · incerta ·
  limita la condensa"); toccato un tratto, la sua misura va sul grafico. Sotto,
  "inoltre": Luna o Sole. Le nuvole restano la prima carta delle misure.
- La qualita' e' solo linea con alone, senza area, per non impastarsi con le nubi.
- Nel grafico del giorno le fasce scure sono il crepuscolo, il giorno e' pulito.
- **Le misure sul grafico, scelta finale (ibrido)**: umidita' % e pioggia % come
  linee sul cielo, con la scala vera; tutte le altre come fasce sotto il cielo,
  una riga ora per ora col colore e il segno dell'esito, nell'ordine delle carte.
  Le fasce usano i colori fissi degli esiti (verde, giallo, rosso), non
  l'accento: con l'ambra "buona" e "incerta" si confondevano.
  Nessun limite di numero. All'apertura si accendono da sole le misure che
  abbassano la qualita' nella finestra; scelta una volta, la scelta resta
  cambiando notte. Le linee solo-forma e la variante "linee" escono, con la
  tavola di confronto. Il parametro `misure` resta per le tavole.
- **Qualità**, sempre in vista (notte o giorno), nell'accento con alone, come nella
  Dashboard; il riquadro dice il valore e cosa limita. In legenda dopo nubi e
  Luna/Sole. La regola e' quella dell'app (vedi "v10 · La qualità").
- **Animazioni del grafico** (come in DECISIONI · Animazioni): al cambio di
  notte, giorno o obiettivo le nubi sfumano in fila, la qualita' e le misure a
  linea piena si disegnano in 0,8 s, Luna/Sole e le linee tratteggiate sfumano,
  i segni ! ✕ compaiono da sinistra; aggiunta una misura si disegna solo quella.
  Il numero grande sale e sfuma, il riquadro compare in 0,15 s, le fasce
  entrano ora per ora. Niente clipPath ne' transform sull'SVG, perche' la pagina
  deve lasciarsi catturare.
- Sul cursore delle carte: passando sulle barrette tutta la pagina va a
  quell'ora; sul telefono si tocca una barretta nella carta aperta.
- Le scale si dicono: "umidità %" e "pioggia %" nelle pillole e in legenda, linee
  piene; le misure senza scala sono tratteggiate.
- (superato dall'ibrido, sotto) variante linee / fasce.

Gli stati (parametro `stato`), coi testi del vecchio sistema:
- Pagina sostituita da un avviso (segno + titolo + una azione): senza sito
  (Aggiungi sito), fuso orario mancante (Modifica sito), prima previsione non
  arrivata (si aggiorna ogni tre ore; Aggiorna in testa), servizio che tace con
  le notti passate (Aggiorna), modello senza notti (si sceglie un altro modello:
  scelto un altro, la pagina torna).
- Servizio che tace con la previsione ancora buona: pagina intera, riga di
  stato sotto il titolo, Aggiorna tenue.
- Seeing senza chiave o con la chiave rifiutata: la carta chiede la chiave
  (Apri le Impostazioni), la voce della scala e' spenta e dice perche'.
  Meteoblue muto: resta l'ultimo seeing, la testa ne dice l'eta'.
- Visibilita' non disponibile: carta "Non disponibile", esce dalla scala.
- Poca storia: il vento a 700 hPa resta, senza confronto.
- Notte coperta (giovedi' 1): seeing e aerosol "Sotto le nubi non si misura".
- Sole sempre su: la parola sola, senza esito ne' grafico. Senza buio: le ore
  serene col Sole sotto l'orizzonte, fasce che non arrivano al buio; le misure
  qui non si mostrano (da fare con "col Sole sotto l'orizzonte").
- Nuvole incomplete: "Non disponibile", la parola sola; il grafico tratteggia
  le ore che mancano.
- Caricamento: scheletro con le misure vere, "Caricamento…".
- Segni degli avvisi: "!" su avviso quando qualcosa non e' riuscito, "?" su
  carta2 quando un dato manca.

Fonti: la previsione e' di Open-Meteo, il seeing di Meteoblue; la testa di Meteo
le nomina entrambe con la loro eta'. Corretto anche l'avviso della Dashboard
("Open-Meteo non risponde").
Allineato con la Dashboard (17 ottobre 2026): condensa 4 / 3 °C anche nelle
sue barrette; "Sabato 3" nelle prossime notti e' tendenza ("9 ore di buio");
il numero grande dice "Ore utili stanotte"; le ↗ delle card meteo e "Meteo ↗"
portano a Meteo (alla carta della misura quando ci saranno gli indirizzi).
Barrette di carte e caselle, in Meteo, Dashboard e Sistema, nel buio coi colori
fissi degli esiti, mai l'accento.

## I componenti veri (17 ottobre 2026)

- Stanno in `pagine/componenti/`, uno per file, e si importano con
  `<dc-import name="componenti/Nome">`: **Telaio** (barra desktop, barre del
  telefono, modo; la pagina va dentro), **Menu** (Altro, Impostazioni, Altro
  del telefono), **DaConfermare** (il pannello), **Carta** (carta e
  protagonista, colonne, entrata), **CardMeteo** (desktop, telefono, telefono
  compatta; stati: Non disponibile, non si misura, chiave, chiave non valida,
  non disponibile), **Pillola** (esito: quattro misure, mancante, neutra),
  **Avviso** (pagina, blocco, riga; segno ! o ?), **Striscia** (notti o giorni).
- Ognuno prende `modo` e `accento` e calcola i colori da solo; i Tweaks hanno
  formato, stato e i testi d'esempio. Il menu aperto e il modo li tiene il
  Telaio; la pagina gli passa `on-modo` per sapere del cambio.
- I token stanno in `componenti/tema.js` (`AL.tema(modo, accento)`), le soglie
  in `componenti/soglie.js` (`ALsoglie`: esito delle barrette, qualita', ore
  utili). Li leggono tutte le pagine e tutti i componenti: un colore o una
  soglia si cambia li', una volta.
- Le soglie delle barrette sono quelle dell'app (vedi "v10 · La qualità").
- La barra e' quella della Dashboard anche in Meteo: segno da 34, Impostazioni
  con l'ingranaggio, contorno al fuoco, frecce nei menu, pannello di Da
  confermare.
- Regola tecnica: il contenitore di ogni componente non occupa posto
  (`display: contents`), cosi' carte e pillole stanno nella griglia come prima.
  Le carte fanno da sole l'entrata quando entrano nello schermo.
- Restano copie nella tavola, non componenti: bottoni, riga con anello, anello
  e barre dell'anno, passi, legenda, riquadro dei valori, scheda della notte.
  Diventano componenti quando una seconda pagina li usa. (Pillole di scelta,
  scheletro e calendario sono diventati componenti col riordino.)
- Controlli (17 ottobre 2026): 300 coppie nei 2 modi × 5 accenti, testo minimo
  5,05:1. Sul telefono nessun bersaglio sotto 44 px in Dashboard e Meteo.
- Segno "!" nel modo chiaro (17 ottobre 2026): `avviso` passa da #d39a2b a
  #956600, il "!" diventa bianco. Il disco ora fa 4,5:1 su carta2 (prima 2,2:1),
  il "!" 5:1. Vale anche per le barre del Kp. Il modo scuro non cambia.

## Notti (17 ottobre 2026, approvata)

Brief. **A cosa serve**: ritrovare una notte passata e vedere com'e' andata.
**Dati**: quelli del vecchio sistema (oggi e' mercoledi' 7 ottobre 2026, nove
notti delle 212). **Stati difficili**: sotto. **La cosa piu' importante**: le
ore della notte e il verdetto del cielo, confrontabili fra le notti.
**Cosa non c'e'**: filtri, ordinamenti, anteprime, note, voto, il meteo ora per
ora (sta in Meteo).

Pagina `pagine/Notti.dc.html` (Tweaks: Stato, Formato, modo, accento); tavola
`pagine/Notti stati.dc.html`, sedici telefoni e quattro desktop (gli schermi
si accendono entrando nella vista, se no la tavola non si lascia catturare).
- **Desktop**: in testa la notte scelta (protagonista, 8 colonne): data e sito,
  le ore come numero grande, frame; cielo (esito, frase, ore utili su
  ore di buio a barrette nei colori dell'esito) e Luna (disco, fase, %);
  oggetti con la barra delle ore nell'accento; filtri con la barra a pezzi e una
  riga per filtro; "I N frame in Archivio ↗". Frecce per la notte prima e dopo.
  A destra il calendario del mese e "tutto l'archivio" (212 notti, frame e ore,
  le righe di stato). Sotto l'elenco, a mesi, dalla piu' recente: sei colonne
  (giorno, sito e oggetti, ore, filtri, cielo, Luna); "Mostra altre 100".
- **Telefono**: calendario, la notte scelta, le notti del mese (tre colonne),
  l'archivio con le righe di stato in fondo. Toccata una riga, la pagina sale
  alla notte. Bersagli da 44.
- **Calendario**: il giorno con una notte prende fondo e segno dell'esito (✓ ! ✕,
  ? senza meteo); due notti, due segni; scelta piena del testo, oggi a
  contorno; nel mese di oggi la griglia finisce a oggi.
- **Verdetto di una notte passata**: dal punteggio della notte, come stanotte
  (vedi "v11 · Il verdetto").
- Ore coi minuti ("4 h 18", "< 6 min"), mai "0 h": "senza durata".
- Stati (parametro `stato`): caricamento, errore, nessun frame, senza sito,
  prima lettura, frame fermi su una risposta (avviso al posto della pagina);
  tutte le righe di stato; una notte sola (dall'indirizzo, niente calendario
  ne' elenco); notte che non c'e' piu'; sito senza fuso (la Luna tace, "Modifica
  sito"); meteo che non arriva; senza durata; due siti lo stesso giorno; senza
  buio.
- **Secondo giro (17 ottobre)**: le righe di stato vanno in testa (desktop in
  due colonne, telefono sotto la barra); i totali dell'archivio scendono in una
  carta bassa sotto l'elenco; a destra della notte resta solo il calendario.
  Telefono: scelta la **B** (17 ottobre). In testa la striscia delle notti
  (componente Striscia), "Calendario" apre il mese sotto; poi la notte e i
  totali, niente elenco. La A (settimana + elenco del mese) esce.
- **Terzo giro (17 ottobre)**: la striscia anche sul desktop, in testa su tutta
  la larghezza (oltre 8 notti scorre di lato, caselle da 164); sotto la notte e
  il calendario; l'elenco resta in fondo come "A confronto" (oggetti, filtri e
  cielo in colonna). Il mese compare sulla prima casella di ogni mese.
  Componente Striscia: la casella scelta entra da sola nella vista; parametro
  `intestazione` per togliere "ora per ora / tendenza". Meteo non cambia.
- **Date allineate**: oggi e' mercoledi' 30 settembre 2026 anche in Notti. Le
  notti del vecchio sistema sono spostate prima del 30; il 27 settembre e'
  quello della Dashboard (Cima Ekar, IC 1396, 4 h 12, 126 frame), col meteo in
  arrivo il 2 ottobre perche' ha meno di 5 giorni. Fasi della Luna ricalcolate
  a mano sulle date nuove (Luna piena il 26).
- **Quarto giro (17 ottobre, desktop)**: la striscia ha le ultime 7 notti e non
  scorre; le altre si trovano col calendario e sotto. Via le frecce ‹ › dalla
  carta della notte (sul telefono restano). Il calendario ha un numero suo: le
  ore del mese, poi notti e notti buone; legenda in fondo.
- **Filtri delle notti** (chiesti dall'utente; superano "niente filtri" del
  vecchio sistema): carta di 3 colonne accanto all'elenco "A confronto" (9).
  Oggetto (testo, anche nome comune), anno, sito, corredo, filtri (con la
  tinta), costellazione, cielo. Pillole a scelta multipla: nello stesso gruppo
  basta una, fra gruppi valgono tutte. Ogni pillola dice quante notti trova
  con gli altri filtri; a zero si spegne. "Togli tutti". Valgono solo per
  l'elenco, non per striscia e calendario. Sul telefono: bottone "Filtri" accanto
  a "Mese" nella carta delle notti (col numero dei filtri attivi); si aprono
  sotto, stessi gruppi, pillole da 44, "Mostra N notti" chiude; li' i filtri
  restringono la striscia, che sul telefono fa da elenco.
- **"Mostra altre 20"** al posto di 100: 20 notti alla volta nell'elenco.
- **Quinto giro (17 ottobre, desktop)**: toccare di nuovo la notte scelta
  (striscia, calendario, elenco) apre il riepilogo. Cielo e Luna in una riga
  sola nella carta della notte. I filtri partono chiusi in una riga ("nessuno
  attivo" o "2 attivi · 6 notti") e l'elenco prende tutta la larghezza;
  aperti tornano 3 + 9.
- **Date allineate**:
- **Il riepilogo al posto di "Tutto della notte"** (17 ottobre): il bottone
  "Tutto della notte ↗" apre `Riepilogo.dc.html` con la notte scelta. Desktop:
  finestra larga 1180 sopra la pagina, ‹ › per la notte prima e dopo, × ed
  Esc, clic fuori. Telefono: pagina intera, ‹ › e × da 44. La prima bozza esce.
  Da fare con Claude Code: l'indirizzo (?notte=…) perche' "indietro" la chiuda.
- (superato) **Tutto della notte: da rifare** (17 ottobre, l'utente: "così non va"). Resta
  nella pagina com'e', si riprende piu' avanti con un brief suo. Prima bozza:
- (bozza) **Tutto della notte** (chiesto dall'utente; supera "niente modale della
  notte" del vecchio sistema): "Tutto della notte ↗" nella carta della notte.
  Desktop: finestra sopra la pagina, larga 1120, si chiude con ×, Esc o
  cliccando fuori. Telefono: pagina intera, × da 44. Dentro: testa (ore, frame,
  oggetti, orario, esito); qualità dei frame (FWHM media e migliore, in pixel
  con la scala del corredo; stelle per frame; eccentricità; segnale/rumore;
  FWHM ora per ora), tutte simulate e dette tali, senza esito finché non ci
  sono soglie; la ripresa ora per ora dalle 18 alle 06, una riga per oggetto
  nelle tinte dei filtri (orari simulati; senza durata lo dice); gli oggetti dal
  catalogo (nome comune, tipo, costellazione, distanza, magnitudine,
  dimensioni, ore) con "In Archivio ↗"; corredo (telescopio, camera,
  montatura, guida, filtri, campo e scala, simulati); condizioni (cielo, ore,
  Luna, buio del sito, temperatura). Parametro `dettaglio` per le tavole.
  Servira' anche ad Archivio: li' diventa componente.
- Nella tavola Sistema: calendario delle notti, barra dei filtri della notte,
  riga della notte (copie; componenti se servono a un'altra pagina).
- Dati simulati: le notti vengono dal vecchio sistema, spostate sul 30
  settembre (vedi "Date allineate").

## Riepilogo (17 ottobre 2026, approvato)

Brief. **A cosa serve**: vedere com'e' venuta una ripresa e quanto valgono i
frame; lo stesso pezzo per una notte (da Notti) e per un oggetto finito (da
Archivio). **Dati**: oggetto e data (o periodo), quattro dati scientifici
(tipo, costellazione, distanza, estensione in anni luce), metriche dei frame
(FWHM, eccentricita', stelle, mediana del fondo, segnale/rumore), corredo.
**Stati difficili**: misure in calcolo, frame senza ora, piu' corredi, filtri
con pochi frame, distanza non nota. **La cosa piu' importante**: i grafici
delle metriche. **Cosa non c'e'**: anteprime, modifica del corredo, previsione.

Pagina `pagine/Riepilogo.dc.html` (Tweaks: tipo oggetto/notte, stato, formato,
modo, accento). La forma (pagina, finestra, pannello) si decide dopo,
guardandola: ora e' una pagina con "← Archivio" / "← Notti".
- **Testa**: oggetto (IC 1396 · Proboscide d'Elefante), periodo "dal 16 al 27
  settembre 2026 · 3 notti, 2 siti", ore come numero, frame e filtri.
  Per la notte: data, sito, orario, cielo; poi "Gli oggetti" con i dati di
  catalogo di ognuno.
- **In cielo** (oggetto): tipo, costellazione, distanza (anche in parsec),
  estensione in anni luce calcolata da distanza e dimensione (con le Lune
  piene per misura). Dati veri dal catalogo.
- **Le metriche dei frame** (protagonista): metrica (una, o due: la seconda a
  tratteggio con la sua scala a destra), ordine "Per ora" (le notti in fila,
  separate) o "Dal migliore al peggiore" (curva ordinata sulla prima metrica,
  la seconda segue lo stesso ordine), filtri a pillole con la tinta, oggetto
  (solo nella notte). Numero grande: la mediana, con migliore, peggiore e
  frame. Puntatore come in Meteo: linea, punti, riquadro coi valori.
- **Per filtro**: mediane di ogni metrica, frame e ore; "pochi frame" sotto 10.
- **Corredo** in sola lettura coi nomi dei pezzi del vecchio sistema (ottica,
  riduttore, ruota, camera, montatura, focheggiatore, guida, programma,
  campo); due corredi quando l'oggetto ne ha usati due; "Apri in Attrezzatura
  ↗". Attrezzatura si rifa' dopo con gli stessi nomi.
- **Le notti** (oggetto): una riga per notte con ore, frame, FWHM, "La notte ↗".
- Dati simulati: frame, metriche, orari, corredi. Il riepilogo della prima
  bozza dentro Notti resta finche' questo non e' approvato.
- **Secondo giro (17 ottobre)**: nella testa i filtri come pillole col pallino
  della tinta e il numero dei frame. Le notti dell'oggetto hanno anche la Luna
  (disco e %) e l'esito del meteo (pillola e ore utili, o "meteo in arrivo").
  Il riepilogo della notte non ha meteo ne' elenco delle notti (stanno in
  Notti). **Due metriche insieme**: un filtro alla volta (pillole a scelta
  singola, Ha di partenza) e le due metriche in due colori delle curve dei
  progetti, entrambe piene, scala a sinistra e a destra; esce il tratteggio.
- **La forma** (17 ottobre, scelta con l'utente): finestra sul desktop, pagina
  intera sul telefono; parametro `contenitore` (pagina, finestra) con
  `on-chiudi`, `on-prima`, `on-dopo`. Il Telaio ha `solo` per mostrare solo
  il contenuto. Dalla notte di Notti il riepilogo ricava frame e oggetti da
  ore e filtri della notte (simulati); il catalogo vero sta in
  `componenti/catalogo.js` (`ALcat`), 18 oggetti.
- **Quarto giro (17 ottobre)**: in testa FWHM mediana, segnale/rumore e (nella
  notte) l'esito del cielo accanto alle ore. Le metriche sono sette miniature
  (nome, mediana, mini-curva dell'andamento): toccata, una metrica entra nei
  grafici sotto (fino a tre); escono le pillole delle metriche. Nella notte,
  sopra il grafico per ora, una fascia dice quale oggetto si riprendeva.
  "Per filtro": toccata una riga, nei grafici resta solo quel filtro; di
  nuovo, tornano tutti. Telefono: miniature e pillole su righe che scorrono.
- Metriche nel vecchio sistema: solo "FWHM media" (Dashboard, "da
  riprendere"). Il resto e' da decidere con l'utente.
- **Terzo giro (17 ottobre)**: niente frame scartati (in archivio arrivano
  solo frame gia' scelti con PixInsight). Metriche: FWHM, eccentricita',
  stelle, fondo (mediana), rumore, segnale/rumore, altezza (con la massa
  d'aria nel riquadro); peso, guida e temperatura escono. Le misurera'
  sep (ADR 0007), con HFD, fondo cielo e rumore del fondo (vedi v10). **Grafico**: piu'
  metriche (fino a tre) vanno una sotto l'altra, ognuna con la sua scala, lo
  stesso asse del tempo e lo stesso puntatore; i filtri restano tutti
  confrontabili nelle loro tinte. Per ora: linea sottile per ogni frame,
  spessa per l'andamento (mediana mobile di 9). Le notti sotto il grafico
  aprono il riepilogo della notte. Corredo: uno solo resta aperto; due si
  chiudono a ottica, camera, montatura e campo, con "Tutti i pezzi". Nelle
  notti esce la FWHM.

## Le scelte nell'accento (17 ottobre 2026)

- Pillole e segmentati scelti (viste, ordini, filtri, metriche, produzioni,
  modelli di Meteo, "Per ore" della Dashboard) prendono l'accento del tema
  (`hPill` / `hPillFg`), come le viste del grafico della Dashboard. Prima
  nel modo scuro erano bianchi. Poi, su richiesta, anche i bottoni d'azione
  (pagine e Avviso), la casella scelta della Striscia e il giorno scelto del
  calendario delle Notti, in tutte le pagine e nella tavola Sistema. Resta su
  "attivo" solo la barra in alto (voce della pagina e sito). Contrasto sulle
  10 combinazioni: testo e tenue sull'accento, minimo 5,25:1.

## Archivio (17 ottobre 2026, approvato)

Brief. **A cosa serve**: ritrovare un oggetto fotografato e aprirne il
riepilogo. **Dati**: foto (quando c'e'), nome e nome comune, tipo e
costellazione, ore, frame, filtri, corredi; in testa i totali e la ricerca.
**Stati difficili**: piu' corredi, mosaico, fuori catalogo (cometa), senza
tempo o senza filtro, nessuna foto, nomi lunghi, archivio vuoto, caricamento,
nessun risultato. **La cosa piu' importante**: riconoscere l'oggetto dalla foto
e dalle ore, e aprirlo. **Cosa non c'e'**: modifica dei dati, elaborazione,
frame singoli, previsione.

Pagina `pagine/Archivio.dc.html` (Tweaks: stato, vista, dettaglio, formato,
modo, accento). Dati: i 15 oggetti del vecchio sistema; IC 1396 allineato al
riepilogo (7 h 24, 202 frame, 2 corredi).
- **Testa**: 240 oggetti come numero, ore, frame, notti; Carte / Elenco;
  Per nome / Per ore / Piu' recenti; campo di ricerca (anche nome comune e
  costellazione); "Filtri" chiusi di partenza (tipo, costellazione, filtri,
  ripresa: un corredo, piu' corredi, mosaico), stesse pillole col conto delle
  Notti.
- **Carte**: quattro per riga sul desktop (foto 3:2), due sul telefono (foto
  quadrata). Il posto della foto ha il nome e "Nessuna anteprima"; "2 corredi" o
  "mosaico · 4 pannelli" sulla foto. Sotto: nome, tipo e costellazione, ore
  come numero, frame, barra dei filtri.
- **Elenco**: oggetto, tipo e costellazione, ore, filtri, corredi, ↗.
- **Piu' corredi**: niente menu di scelta; si apre il riepilogo dell'oggetto,
  che li mostra tutti (supera il menu delle produzioni del vecchio sistema).
- Tocco su carta o riga: il Riepilogo dell'oggetto in finestra (desktop) o a
  pagina intera (telefono), con ‹ › per l'oggetto prima e dopo nell'ordine
  della pagina. Il riepilogo ricava notti e corredi dai totali (simulati).
- **Secondo giro (17 ottobre)**: conta la **produzione** (l'oggetto ripreso con
  un corredo, o un pannello), non il corredo: "2 produzioni", "mosaico · 4
  pannelli"; filtro "Ripresa": una produzione, piu' produzioni, mosaico. Nel
  riepilogo una produzione alla volta: pillole "produzioni" in testa (2026 ·
  Rifrattore 80/480 · Cima Ekar, 2025 · Newton 200/800 · Casa), ognuna con la
  sua storia intera; per il mosaico "Riepilogo generale" e Pannello 1–4.
  Produzioni simulate, una per anno. Carte del desktop cinque per riga, piu'
  piccole. (Supera "piu' corredi: si apre il riepilogo che li mostra tutti".)

## Il riordino (17 ottobre 2026, v9)

Brief nella voce 0 di "Da fare" (fatto). Ogni pezzo e ogni dato in un posto solo.
- **Componenti nuovi** in `pagine/componenti/`: **PillolaScelta** (segmentato o
  pillole; conto, pallino della tinta, linea della curva, spenta), **Filtri**
  (corpo coi gruppi, bottone "Filtri" col numero, "Togli tutti"), **BarraFiltri**
  (12 o 8, righe per filtro), **Luna** (disco e falce; con fase e percentuale),
  **CalendarioNotti** (tipo notti o luna), **Scheletro** (la pagina passa le
  carte con le misure vere), **FinestraRiepilogo** (velo, finestra 1180 o pagina
  intera, Esc, clic fuori, animazioni di apertura, chiusura e scivolamento),
  **Riepilogo** (spostato da `pagine/`; `pagine/Riepilogo.dc.html` resta come
  pagina che lo monta).
- **Dati simulati** in `componenti/dati.js` (`ALdati`): oggi (30 settembre
  2026), notti, totali dell'archivio, oggetti, produzioni, pannelli del mosaico,
  corredi coi pezzi, le notti di ripresa di IC 1396. Il catalogo vero resta in
  `catalogo.js`; Notti non ha piu' una copia sua del catalogo.
- **tema.js** ha anche: `AL.FD` (filtri: nome e tinta), `AL.tinta` (fondo e
  bordo, strisce), `AL.linea` (colore della curva di un filtro), `AL.lunaD`,
  `AL.tratteggio`, `AL.ore`, `AL.num`, `AL.virg`.
- Tutti i file caricano tema, soglie, catalogo e dati nello stesso modo.
- **Unificazioni scelte con l'utente** ("unificare tutto"):
  - a colori e filtri a piu' bande: a strisce anche nel riepilogo (pallini della
    testa e righe "Per filtro"). Le curve hanno un colore solo: la prima banda,
    quadribanda in Hβ.
  - Il calendario della Dashboard e' CalendarioNotti `tipo="luna"`: frecce ai
    lati del titolo, caselle da 42 (46 sul telefono), segno sotto il numero, ★
    in alto a destra, legenda a quadretti, niente giorni degli altri mesi. Il
    giorno scelto resta nel colore del testo (li' l'accento vuol dire notte buona).
  - Le stelline del calendario sono le notti vere dell'archivio (13, 16, 19, 20,
    22, 24, 27, 28, 29 settembre); la scheda dice sito, oggetti e frame (via la
    FWHM, che il dato della notte non ha).
  - "Togli tutti": sottolineato in testa sul desktop, pillola col bordo in fondo
    sul telefono (anche in Archivio, che sul telefono ha ora "Mostra N oggetti").
  - Pillole dei filtri: alte 32 sul desktop (44 sul telefono), padding 12,
    pallino tondo da 10, fondo carta2; nel riepilogo le pillole spente non hanno
    piu' il contorno.
  - Segmentati (viste, ordini, modello, obiettivo, Luna/Sole, Carte/Elenco):
    binario da 4, voci alte 32 (44 sul telefono), padding 14, 13 px; Luna/Sole
    sul desktop resta piccolo (24).
  - Le misure sul grafico di Meteo sono PillolaScelta `forma="spunta"` (dopo
    il riordino, su consiglio): anello e pallino nel colore della misura, mai
    l'accento; ruolo di casella a spunta. Alte 32 (prima circa 30), 44 sul telefono.
  - Tratteggio unico 3/8 px (prima 2/5 in Meteo, Striscia, card meteo e Kp).
  - Scheletri: angoli delle carte 28, 24 sul telefono (il riepilogo aveva 28
    anche sul telefono).
  - Bordo della Luna nel grigio della Luna anche nella Dashboard (prima la linea).
  - Bottone "Filtri" di Notti sul telefono con la freccia, come in Archivio.
  - Correzione: i giorni del calendario ereditano la visibilita' (con "Sole"
    il calendario della Luna restava sopra le informazioni del Sole).
  - Calendario sul telefono: spazio fra le caselle 3 px, perche' nella carta
    della Luna le caselle arrivino a 44 di larghezza.
- Effetto non cercato: in Archivio a 1440 × 0,6 le pillole dell'ordine andavano
  a capo sotto la riga; ora no.
- Catture prima e dopo in `screenshots/v9/` (desktop a 1440 ridotto a 0,6 e
  telefono a 390, da `pagine/Cattura.dc.html`). Uguali al pixel dove non c'e'
  un'unificazione; altrove cambiano solo le cose sopra, o spostamenti di 1–8 px
  sotto un segmentato o un calendario che ha cambiato altezza.
- Controlli: 260 coppie nei due modi coi cinque accenti, testo minimo 5,14:1,
  forme 3,32:1; nessun bersaglio sotto 44 sul telefono (Dashboard col
  calendario aperto, Meteo, Notti coi filtri e il mese, Archivio coi filtri,
  riepilogo); console pulita nelle pagine e nelle quattro tavole.

## Da fare, in ordine

0. (fatto, vedi "Il riordino") **Riordino**. Brief: **a cosa serve**: le sei
   pagine (Dashboard, Meteo, Notti, Riepilogo, Archivio, Sistema) parlano la
   stessa lingua e sono pronte per Claude Code. **Cosa tocca**: componenti
   nuovi dai pezzi ripetuti (CalendarioNotti, Filtri, PillolaScelta, Luna,
   BarraFiltri, Scheletro, Finestra del riepilogo, Riepilogo stesso); nomi,
   testi, misure, angoli; dati simulati in un file solo (\`componenti/dati.js\`:
   notti, oggetti, produzioni, corredi, oggi = 30 settembre); \`tema.js\`
   (FD dei filtri e lunaD in un posto). **Difficile**: non cambiare nulla a
   vista (catture prima e dopo, uguali al pixel salvo cio' che si dichiara);
   pagine che restano leggere da catturare. **La cosa piu' importante**:
   ogni pezzo e ogni dato in un posto solo. **Cosa non c'e'**: pagine nuove,
   ritocchi di disegno (si annotano e si chiedono). In fondo: \`old/\` senza
   Notti e Archivio (fatto: Archivio approvato e tolto il 17 ottobre; resta
   `ricerca.html`, che va con Cerca), Sistema coi componenti veri, controlli
   (contrasto, 44 px, console), CHANGELOG v9.

1. Il riepilogo diventa componente quando lo usa Archivio (con i filtri delle
   notti e il catalogo). Tavola: `pagine/Riepilogo stati.dc.html`.
2. Le altre pagine, una per conversazione, coi componenti. Da confermare fatta
   (v14), Attrezzatura fatta (v15, forma nuova). Poi Cerca.
3. Si aggiungono alla tavola quando servono: pannello di Cerca (con la
   ricerca), tabella, campi dei moduli e tendina (con Archivio e Attrezzatura).

## v15 · Attrezzatura (17 ottobre 2026)

Brief. **A cosa serve**: vedere com'e' fatto un corredo, completarne i pezzi, aggiungere strumenti. **Dati**: corredi (nome, ottica + camera, focale, rapporto focale calcolato, montatura, scala e campo, ore, parti coi frame, filtri in proporzione); componenti per tipo con la scheda e le ore. **Stati difficili**: parti da indicare, conteggio in corso, campo non disponibile, moduli con errori, scansione in corso, vuota, non si legge. **La cosa piu' importante**: il corredo scelto, cosa ha e cosa gli manca. **Cosa non c'e'**: oggetti, notti, frame totali; il campo disegnato e la catena della luce.

- **Forma nuova, da zero** (l'utente, 17/10): supera le schede grafiche dell'11 ottobre e la nota "si tiene la seconda forma". Comandano i corredi. Niente della forma vecchia: niente catena, campo disegnato, tessere.
- **Desktop**: indice a sinistra (320, fisso scorrendo): "Corredi" (nome, riga sotto, ore, "{n} da indicare" col segno ○) e "Componenti" (i gruppi nell'ordine dell'app, col numero). La voce scelta nell'accento. A destra il dettaglio.
- **Il corredo**: carta del nome (ore come numero protagonista, focale, "f/… (calcolato)", "su …", Rinomina); carta del campo ("campo", gradi come numero, arcosecondi per pixel; senza frame risolti "campo non ancora disponibile"); "Parti" con una riga per parte, nell'ordine ottica, camera, riduttore, ruota, montatura, focheggiatore, ottica di guida, camera di guida, programma: nome coi frame, "(scelta a mano)", o "○ da indicare" a contorno; "Seleziona" su tutte tranne ottica e camera, apre sotto la riga la tendina "{Parte} (vuoto: dai file)" con "--", o "aggiungine uno" se non si possiede nessun pezzo di quel tipo. Il nome di un pezzo porta ↗ al suo gruppo. "filtri" in proporzione, senza cifre.
- **Un gruppo**: una riga per pezzo (nome, marca · modello, "inserito manualmente"; la scheda con le parole dell'app; le ore o i tre modi di non saperle; Modifica). Il modulo si apre sotto la riga, col bordo nell'accento.
- **Telefono**: l'indice e' la prima schermata; toccata una voce, il dettaglio a pagina intera con "← Attrezzatura". "Aggiungi strumento" sempre in testa.
- **Moduli**: componente nuovo `componenti/Modulo` (solo disegno, i valori li tiene la pagina): tipo a tasselli poi "Tipo: … Cambia", blocchi "chi è" / "dati tecnici" con "{n} di {m} scritti" (sul telefono uno aperto alla volta, Salva attaccato in fondo), "dai file" / "inserito" / "calcolato", Unisci a, errori sopra Salva / Annulla. Campi per tipo come dall'app; esce la tipologia.
- **Testi nuovi, da approvare con Marco**: "{n} da indicare" (conto delle parti), "Parti" (titolo della carta), "Seleziona" sulle righe (l'app ha "Seleziona montatura"), "Per salvare serve almeno una banda.", "Per salvare servono ottica, camera e focale effettiva.", "servono apertura e focale" (rapporto non calcolabile), "Larghezza (nm)" nelle bande del filtro, "Pixel (µm)" (l'app scrive "um"), "Apri {nome} fra i componenti" (per chi legge con la voce).
- **Dati**: "Notte in quota" e' Askar FRA400 + ZWO ASI2600MM Pro, "Casa leggero" RedCat 51 + ZWO ASI294MC Pro, anche in Da confermare (col "+"). In piu' la camera ATR2600M (412 frame), la stessa che Da confermare propone di unire.
- Tavola: `pagine/Attrezzatura stati.dc.html`.
- **L'accento** (17/10, l'utente: "mancano gli accenti"): barra delle ore nell'accento sotto ogni corredo dell'indice (rispetto al piu' usato) e sotto le ore di ogni pezzo (rispetto al piu' usato del gruppo); nove tacche delle parti accanto a "Parti" (piene = indicata, a contorno = da indicare); "Seleziona" pieno sulle parti da indicare.
- **Ritocchi scelti da Claude** (l'utente: "decidi tu"): segni dei tipi nell'indice dei componenti e su ogni riga di Parti (il programma ha il suo); nella carta del campo il campo di tutti i corredi a confronto, centrati, quello scelto nell'accento ("a confronto, il campo dei corredi", parola da approvare). Animazioni da `componenti/moto.js`: barre delle ore che si riempiono una volta; al cambio di corredo o gruppo il numero sale e sfuma e le righe entrano in fila. Ferme col movimento ridotto.

## Dati simulati da sostituire

Meteo: tutte le misure ora per ora delle sette notti e dei sette giorni, la
probabilita' di pioggia, i tre modelli (cambiano
solo l'etichetta), le fasce delle notti dopo stanotte (uguali a stanotte), Capo
Nord e Oslo. Dashboard: ore per filtro, mesi del 2025, notti di ripresa del calendario (vera solo
quella del 27, che pero' nel calendario cade di domenica), curve e Luna delle
prossime notti, posizioni dei pianeti (approssimate), dati del Sole (macchie,
regioni, brillamenti, Kp, seeing di giorno: dal centro meteo spaziale NOAA).

## v10 · correzioni prima del porting (17 ottobre 2026)

Dalla revisione di Claude Code contro l'app (glossario, API, contratti). Estetica e
comportamenti restano; cambiano parole, dati, regole e stati mancanti.

### Le parole
- Il glossario dell'app e' la fonte: ore (mai "posa"), senza durata, ? Non
  disponibile, nessun filtro, verdetto della notte (Notte buona / incerta / non
  adatta), giudizio di una misura (buono / incerto / non adatto), Scansiona, Scegli
  la cartella, Crea un progetto, Meteo non raggiungibile, Caricamento… (niente
  prima persona), anteprima / Nessuna anteprima (la foto finale e' quella
  caricata dall'utente), polveri, Bortle ("Bortle, da 1 a 9"), Cerca un luogo,
  Cartelle. "Qualità" solo per il punteggio da 0 a 100. Mai "0 h".

### La qualità (ADR 0020 dell'app)
- La calcola l'app, una regola sola per Dashboard, Meteo, Notti (anche passate),
  calendario, prossime notti, Riepilogo. Ogni ora vale da 0 a 100: somma dei punti
  dei fattori (nuvole 30, seeing 25, Luna 15 o di giorno Sole basso, trasparenza
  10, condensa 8, vento 8, jet stream 4). Pioggia e nuvole dal 50 % bloccano: l'ora
  vale 0. "Cosa limita" e' il fattore che ha perso piu' punti. La Luna pesa per
  quanto schiarisce il cielo del sito (dal Bortle); sotto l'orizzonte non pesa.
  (Superato dalla v13: di notte la Luna non pesa piu'; vedi "v13 · La ripresa".)
- La notte e' la media delle ore di buio; il verdetto dal punteggio (vedi
  "v11 · Il verdetto").
- `soglie.js` non decide piu' niente: simula cio' che arriva dall'app perche' i
  dati d'esempio si muovano. Nessuna formula nei testi.
- Giudizi delle misure con le soglie dell'app e la loro fonte: nuvole 25 / 50 %
  (okta WMO), vento 20 / 29 km/h (Beaufort 4 e 5), seeing 2 / 4″ (Clear Sky Chart),
  jet stream 126 km/h (meteoblue), condensa sotto 3 °C (FAA), aerosol 0,1 / 1
  (NASA), visibilita' sotto 1 km (WMO), qualunque pioggia. Dove l'app ha un gradino
  solo: superato dalla v11 (il gradino unico e' "non adatto").
- Effetto sui dati d'esempio: stanotte le ore utili passano da 6 a 8 (la condensa
  pesa 8 punti, non piu' il minimo); le nuvole di stanotte (picco 40 %) diventano
  "incerto dalle 04:00"; la condensa "incerto". Nella notte coperta la carta
  Umidita' lascia il posto a Visibilita' (l'umidita' non ha giudizio).

### La scansione
- "Scansiona" sta nel menu dell'ingranaggio. Mentre lavora l'ingranaggio porta un
  anello che gira (sul telefono anche "Altro"); interrotta o bloccata un "!" ambra.
  Nel menu: fase, file letti su N, tempo che resta, Ferma; finita, l'esito
  dell'ultima scansione con l'ora; interrotta o bloccata, la frase e Riprendi.
  Parametro `scansione` di Telaio e Menu.

### Stati nuovi
- Dashboard: senza sito (due passi: Scegli il sito, poi la cartella; niente notte
  ne' meteo), prima scansione (barra, file letti, anno in lettura, casi da
  confermare a scansione finita; "Finora la scansione ha trovato N oggetti"), da
  riprendere (righe con Rispondi e i frame fuori dai conti), dettaglio della Luna
  (↗ sulla carta: eta', distanza, azimut, legenda del calendario dalle
  Impostazioni; il mese prima e dopo con le frecce).
- Meteo: risposta non valida, cambio del modello non riuscito, seeing parziale
  ("media fino alle 02:00"); nessuna previsione, aggiornamento non riuscito e
  seeing con dati precedenti c'erano gia'. In fondo "Orari in ora locale del sito"
  con le attribuzioni. Nuvole basse e Luna: solo grafico e riquadro, senza giudizio.
- Notti: nessuna cartella (con nessun frame, senza sito, tutti fermi su una
  risposta: i quattro modi di non avere notti); "senza durata" nei totali; "Le
  copie calibrate non sono contate"; fuori da ogni notte tre righe (da confermare,
  senza sito, senza data); scansione in corso con la percentuale.
- Archivio: nessun oggetto identificato (la carta "Senza oggetto"), ASTAP assente
  (riga con il rimando alle Impostazioni), archivio vuoto con "Aggiungi cartelle".
  Filtri in piu': periodo, sito, ottica, camera, catalogo (mosaici in "Ripresa");
  una tendina compare solo se c'e' una scelta; il periodo restringe ore e frame.

### Archivio: linguette e Aggiungi oggetto (ADR 0019)
- Linguette Deep sky (dai FITS, com'era), Sole, Sistema solare (pianeti, Luna,
  comete, asteroidi; le comete in FITS ci arrivano da sole).
- Aggiungi oggetto in una finestra: tipo, poi una o piu' fonti (file SER per
  percorso, log del programma di ripresa, foto finale, a mano). Obbligatori tipo,
  oggetto, data, sito; ora fortemente consigliata (senza, cio' che ne dipende dice
  "Non disponibile"); per il Sole il filtro facoltativo. Ogni campo dice da dove
  viene e si corregge a mano. Le metriche (altezza, diametro, fase, meridiano
  centrale, Carrington, meteo e attivita' solare) le calcola l'app: simulate.

### Dati
- Riepilogo tutto simulato: le metriche le misurera' sep (FWHM, HFD, stelle,
  segnale/rumore, eccentricita', fondo cielo, rumore del fondo; altezza e massa
  d'aria dall'ora del frame). Nome di catalogo sopra, comune sotto solo se c'e'
  (3 % circa). "distanza non nota" frequente. Pianeti calcolati: quattro.

### Il foglio per il porting
- `pagine/astrolog.css`: token come variabili CSS per `[data-modo]` ×
  `[data-accento]` (originale, ambra, turchese, corallo, ghiaccio), generati da
  tema.js; una classe per componente e stato; animazioni in CSS con
  prefers-reduced-motion. `pagine/caratteri.css` e `pagine/caratteri/`: Outfit e
  Plus Jakarta Sans variabili (pesi usati 300–700), nel progetto. Le pagine .dc.html
  restano con gli stili scritti nel markup e caricano i caratteri dal progetto;
  `pagine/Foglio.dc.html` usa solo le classi, accanto ai componenti veri.

## v11 · ultimi ritocchi prima del porting (17 ottobre 2026)

### Il verdetto (ADR 0020, deciso da Marco)
- Il verdetto viene dal punteggio della notte, la media 0-100 delle ore di buio:
  buona da 70, incerta da 40, sotto non adatta. Vale per stanotte, le prossime
  notti, le notti passate (Notti, calendario, Riepilogo) e il giorno del Sole
  (media delle ore della finestra di giorno).
- Ora utile: qualita' da 60. Il numero grande "Ore utili" resta, ma non decide il
  verdetto.
- Nel disegno: `ALsoglie.livello` (70 / 40) sulla media; per le notti passate il
  punteggio d'esempio (`met.q`) o uno simulato da ore utili e nuvole
  (`ALsoglie.puntoNotte`). `oreEsito` esce.

### I gradini dei giudizi
- Dove l'app ha un gradino solo, e' "non adatto": jet stream da 126 km/h,
  condensa sotto 3 °C, visibilita' sotto 1 km, qualunque pioggia.
- Aerosol: sotto 0,1 buono; da 0,1 a 1 nessuna parola (barretta neutra, nessuna
  pillola: `ALsoglie.neutro`); da 1 non adatto.
- Curve della qualita' (simulate) con gli estremi dell'ADR: piene fino alla soglia
  buona, zero dalla non adatta (nuvole 25 / 50 %, seeing 2 / 4″, vento 20 / 29
  km/h, condensa 3 / 0 °C, aerosol 0,1 / 1, jet stream 90 / 126 km/h).
- Frase del cielo nelle Notti: poco / parzialmente / molto nuvoloso a 25 / 50 %.
- Luna nella qualita': superato dalla v13 (la Luna non entra piu' nel punteggio). Nel riquadro del grafico, accanto all'altezza, "illuminata al N %" resta.


## v12 · Il primo avvio (17 ottobre 2026)

Brief. **A cosa serve**: la prima pagina che chiunque vede; prepara l'app in pochi passi, tutti facoltativi. **Dati**: nome, sito (ricerca, coordinate, Bortle), tema, cartelle (computer o NAS), chiave Meteoblue, ASTAP; prima, un eventuale backup; dopo, la chiusura. **Stati difficili**: passo saltato, ricerca muta, coordinate sbagliate, cartella non raggiungibile o gia' registrata, NAS senza elenco, chiave rifiutata, ASTAP senza catalogo, scansione che non parte, salvataggio non riuscito. **La cosa piu' importante**: si capisce cosa chiede ogni passo e perche', e che si puo' saltare. **Cosa non c'e'**: telaio e menu; fuso, altitudine, misura del cielo; download o installazione di ASTAP.

Pagina `pagine/Primo avvio.dc.html` (Tweaks: passo, stato, ASTAP, formato, modo, accento); tavola `pagine/Primo avvio stati.dc.html`.
- **Forma**: niente telaio. Desktop: a sinistra "Primo avvio", "Tutti i passi sono facoltativi.", "Passo N di M" e l'elenco; a destra la carta del passo (titolo, perche', controlli, gesti). Telefono: segni dei passi in fila con "Passo N di M · nome", la carta, i gesti in una barra fissa in fondo.
- **Tappe**: fatta (✓ nei colori dell'esito buono, "fatto"), saltata ("–" su anello tratteggiato, "saltato"), quella dove sei (numero sull'accento, riga su carta), quelle dopo (numero su anello). Non sono bottoni. Un passo e' fatto se lascia un dato salvato (nome scritto, sito salvato, almeno una cartella, chiave salvata, ASTAP trovato; il tema sempre); con Avanti senza dato e' saltato.
- **Gesti**: "Salta" a sinistra (chiude il primo avvio ed entra nell'app, senza conferma), "Indietro" (non al primo passo), "Avanti" o "Fine". Un solo primario: se il passo ha un comando suo (Salva sito, Verifica / Aggiungi cartella / Usa questo percorso / Seleziona cartella, Verifica e salva, Verifica percorso) quello e' pieno e Avanti e' tenue; quando il comando non serve piu' (cartelle aggiunte e campo vuoto, chiave salvata, ASTAP trovato, catalogo mancante) Avanti torna primario. Il bottone al lavoro gira e dice "Ricerca…", "Verifica…", "Salvataggio…", "Ripristino…".
- **Tema**: dopo il sito. Componente `componenti/SceltaTema` (modo, accento, sito, formato, on-modo, on-accento), lo stesso per le Impostazioni. Modo a segmentato; accenti come voci con un campione (telaio, carta, anello e bottone "Avanti" nei colori dell'accento nel modo scelto; con Automatico, il modo in vigore). Toccata una scelta, tutto il primo avvio cambia; niente Salva. Automatico senza sito spento, con la riga del perche'. Desktop: accenti in fila; telefono: in colonna, voci da 60.
- **Sito**: la ricerca riempie nome e coordinate, che restano modificabili; errori sotto il campo dopo l'uscita dal campo; Bortle a nove voci (5 + 4 sul telefono) con la classe letta sotto. Salvato, va da solo al passo dopo.
- **Cartelle sul NAS**: elenco delle sottocartelle con "Apri", percorso corrente che va a capo; il bottone "Seleziona cartella" verifica la cartella corrente.
- **Esiti**: componente Avviso, blocco o riga; segno "✓" (nuovo) per i riusciti, "!" per i non riusciti, "?" per cio' che manca. "Cartella gia' registrata" ha "!".
- **Chiusura**: una riga per voce (Nome utente, Sito di osservazione, Tema, Cartelle, Seeing) con ✓ o "–"; "Cartelle: 3" con "!" e la riga della scansione che non e' partita. "Apri AstroLog".
- **Testi nuovi o cambiati, da approvare con Marco**: perche' del Tema "Come si vede l'app. Si cambia quando si vuole dalle Impostazioni."; Automatico "Scuro dal tramonto all'alba di Cima Ekar, chiaro di giorno." e, senza sito, "Automatico ha bisogno di un sito di osservazione: tramonto e alba si calcolano da lì."; "Salvataggio non riuscito" / "Sito non salvato" con "Le impostazioni non hanno risposto. Riprova."; "Ricerca non riuscita: il servizio non ha risposto." in una riga; "File trovati" con "1.240 file FITS · percorso"; "Cartella gia' registrata" con "È la stessa cartella registrata come \\nas\astro\2026."; ASTAP trovato senza catalogo: "ASTAP trovato, catalogo mancante" e "Senza il catalogo stellare gli oggetti ripresi non vengono identificati. Scarica il catalogo, poi verifica di nuovo."; Catalogo mancante: perche' "ASTAP identifica il campo inquadrato dalle stelle (plate solving), ma gli serve un catalogo stellare. Si può aggiungere anche dopo.", avviso "ASTAP è installato, ma senza catalogo non identifica gli oggetti ripresi.", "Quale prendere: D50 va bene per quasi tutti i campi; D05, più leggero, basta per campi più larghi di 0,6°." (da verificare con la documentazione di ASTAP); scansione: "La scansione non è partita: si avvia da Scansiona, nel menu dell'ingranaggio."; chiusura "Tutto si cambia dalle Impostazioni."; Bortle col trattino lungo ("Bortle 3 – campagna").
- **Dati simulati**: risultati della ricerca (Cima Ekar, Pennar), conti dei file, cartelle del NAS, chiave che termina con ab12, data e conti del backup; nella chiusura Cima Ekar e' Bortle 3, come nel resto delle pagine.
- **Foglio**: le classi nuove in `astrolog.css`; nel Foglio le tappe (desktop e telefono), il campo con l'errore, il Bortle, i gesti e la scelta del tema accanto al componente vero.


## v13 · La ripresa: la Luna decide cosa si riprende (17 ottobre 2026, deciso da Marco)

Da Claude Code: una notte con la Luna al 63 % risultava migliore di una al 43 % a parita' del resto. Il difetto era nella regola (ADR 0020 dell'app): la Luna pesava 15 punti su 100. Estetica e comportamenti restano; cambiano la regola e cio' che si dice.

### La regola
- Due risposte separate. **Il meteo dice se si esce**: punteggio 0-100 e verdetto come prima (buona da 70, incerta da 40; pioggia e nuvole dal 50 % bloccano). La Luna non entra nel punteggio: nuvole 35, seeing 30, trasparenza 12, condensa 9, vento 9, jet stream 5. "Cosa limita" non e' mai la Luna.
- **La Luna dice cosa si riprende**: ogni ora di buio e' banda larga o solo banda stretta. Solo banda stretta quando la Luna e' illuminata dal 25 % e alta da 10°; sotto l'una o l'altra soglia, banda larga. Le due soglie stanno nelle Impostazioni.
- Il giorno del Sole non cambia per ora (pesi di prima, con Sole basso 15). Come si giudica senza "Sole basso" si decide con Marco quando si costruisce.
- Calendario della Luna: notte buona = almeno 4 ore di banda larga, con le stesse soglie. La regola delle 4 ore resta.
- Notti passate: il punteggio d'esempio non tiene conto della Luna (`puntoNotte` non la usava).

### Dove si vede
- Il verdetto resta la cosa piu' grande; la ripresa e' la seconda riga. Componente `componenti/Ripresa`: forma "riga" (tratti con le ore) e "segno" (le ore di banda larga). Segno pieno largo = banda larga; segno stretto dentro il contorno = solo banda stretta; tutti e due = la notte cambia. Colore del testo, mai l'accento: forma e parola dicono il tipo.
- Dashboard: riga sotto il verdetto (solo nella vista Notte, anche senza previsione: la Luna si calcola); nel riquadro della Luna due caselle con le ore di ciascun tipo e gli orari; sotto l'asse del grafico la fascia della ripresa (piena = banda larga, tratteggiata = solo banda stretta); nel riquadro del puntatore la ripresa di quell'ora; prossime 3 notti col segno accanto al verdetto (la Luna ha transito, declinazione e fase di Meteo).
- Meteo: la riga nella carta della notte, anche per le notti di tendenza; in "Come va la notte" una riga all'ora del cambio, in ordine con le ore del verdetto; la Luna esce da "inoltre" e resta nel riquadro in fondo; sette notti col segno.
- Notti: carta della notte, striscia e "A confronto", sotto il cielo, le ore di banda larga. Senza Luna nei dati, senza fuso o senza buio: niente segno.

### Parole (da approvare con Marco)
- banda larga, solo banda stretta, "Tutta la notte banda larga", "Tutta la notte solo banda stretta", "Banda larga 20:48–01:00 · poi solo banda stretta", "N ore di banda larga".
- In piu' delle proposte: "la Luna scende sotto 10°" al posto di "la Luna tramonta" (con la soglia a 10° la banda larga comincia prima del tramonto); "la Luna sale sopra 10°" resta.
- Nella legenda del calendario: "Notti buone nel calendario: almeno 4 ore di banda larga, cioè con la Luna sotto il 25 % o sotto 10° (le soglie stanno nelle Impostazioni)."
- Gruppo "Ripresa" nei filtri delle Notti: non fatto, da decidere con Marco.

### Simulato
- `soglie.js`: `ripresa`, `tratti` (passi da 15 minuti), `frase`, `breve`, `oreLarga`, `tipoNotte`; `larghePassate` per notti passate e calendario (Luna a declinazione 0, sopra 10° per 5 ore prima e dopo il transito, buio centrato all'01:15). Nell'app li calcola il motore.

### Come va la notte: il racconto (deciso da Marco)
- Una linea del tempo dal tramonto all'alba, in ordine d'ora al minuto: ora, punto, fatto e una riga sotto. Solo il fatto, niente consigli.
- Eventi: tramonto, inizio e fine del buio, alba; la Luna che sorge e tramonta; il cambio di ripresa; il verdetto quando cambia (punto nel colore dell'esito col segno e la parola: "Ore buone", "Ore incerte", "Ore non adatte"); nuvole oltre o sotto il 25 e il 50 %; pioggia che comincia o finisce; condensa sotto 3 °C; raffiche; seeing migliore; pianeti che sorgono, tramontano o culminano (dai 10° in su: la stessa altezza minima della Luna, un solo numero per "alto abbastanza da contare"; v13.1, Marco).
- Il racconto sostituisce, nelle notti con le ore, le fasce orarie del verdetto e i riquadri Buio e Luna: il verdetto e' un evento quando cambia (v13.1, Marco).
- Desktop: la carta non allunga la riga e il grafico non cresce. Si vedono gli eventi che ci stanno, gli altri scorrono dentro la carta, con una sfumatura in fondo. Telefono: tutti, righe da 44.
- Toccando un evento il puntatore del grafico va a quell'ora (anche le carte delle misure).
- Il transito dei progetti al meridiano non c'e' (tolto da Marco).
- Simulato: pianeti con le posizioni della Dashboard; tramonto e alba fissi.


## v14 · Da confermare (17 ottobre 2026)

Brief. **A cosa serve**: rispondere alle domande che la scansione non risolve da sola; le risposte si scrivono tutte insieme con Applica. **Dati**: sette sezioni (l'API manda sette liste), per domanda i frame, le prove dei file e le scelte. **Difficile**: Applica in corso, applicato, sei rifiuti, niente da confermare (anche con risposte salvate), zero frame; le domande a piu' parti. **La cosa piu' importante**: quante restano e quale si sta facendo, una sola aperta. **Cosa non c'e'**: consigli, risposte obbligatorie, navigazione oltre l'indice.

- Testi e dati controllati da Claude Code contro l'app (API `GET /api/v1/review`, dizionario): si usano parola per parola. La vecchia tavola e' superata.
- **Il conto sono le domande senza risposta** (`to_confirm`), non notti ne' frame. Pillola in barra "{n} da confermare"; il pannello elenca le sezioni con domande aperte, ognuna col suo conto e Rispondi, che apre la pagina su quella sezione (`Da confermare.dc.html#filtri`). "N frame fuori dai conti" resta in Dashboard e Notti. Telaio: parametro `domande` (prima `notti`).
- **Forma B, pelle bento**. Desktop: a sinistra il conto (numero protagonista, la regola di Applica sotto) e l'indice "Sezioni" con "{n} senza risposta" o "tutte con risposta" (cifra in un anello, o la spunta). A destra le sezioni: con tutte le risposte si chiudono in una riga al loro posto ("{n} risposte da applicare" / "{n} risposte salvate", Riapri). Una domanda aperta in tutta la pagina, con il bordo nell'accento; le altre sono righe (nome, frame, risposta in breve, stato, Rispondi o Cambia). Il perche' solo nella sezione su cui si lavora.
- Telefono: il conto, poi "Tipi di domanda" coi conti per stato; un tipo apre un caso alla volta ("← Tutti i tipi", "caso {k} di {n}", "Caso prima" / "Caso dopo"). Nel caso la regola di Applica non si ripete.
- **Le scelte sono pillole da 44 col pallino** (pieno se scelta) nell'accento; con una riga sotto ("nell'inquadratura", "ottica · camera") diventano blocchi a angoli di 18.
- **Quattro stati della risposta**, segno e parola: ○ senza risposta, ● da applicare (accento), ✓ salvata (verde), ◐ cambiata, da applicare (anello accento) con "era …". Le parti dell'attrezzatura: "da indicare", "da applicare", "salvata".
- **Il piede** e' una barra di vetro fissa in fondo: "{n} modifiche da applicare", l'avviso "Include un'unione di strumenti: non è reversibile.", Applica (spento a zero). In corso: "Applicazione in corso…", indice e sezioni spenti. Esito e rifiuti sopra le sezioni; l'esito si chiude, il conto non cambia; strumenti e filtri applicati escono dalla coda.
- Stati della pagina: caricamento (scheletro e "Caricamento…"), "Da confermare non disponibile" · Riprova, "Niente da confermare" · "Nessuna domanda aperta." (niente pillola in barra), zero frame ("Nessun frame in archivio." · Aggiungi cartelle).
- **Nessun sito dichiarato**: buco dell'app, disegnato con la frase di Marco e "Apri le Impostazioni".
- Gli oggetti gia' a posto: una riga "{n} oggetti riconosciuti" che si apre in coda alla sezione (chiude la domanda aperta); ogni voce ha Correggi.
- Da confermare con Claude Code: la riga che apre gli oggetti riconosciuti non ha una parola sua (qui e' la riga stessa, con la freccia); le voci della prova di Strumenti duplicati ("Altri frame") sono d'esempio.
- Tavola: `pagine/Da confermare stati.dc.html` (telefono: pagina, Applica, domande; desktop: nove stati). Escono da `old/` le pagine, la proposta e i due documenti d'archivio di Da confermare.

## v15.1 · Riordino dopo Attrezzatura (17 ottobre 2026)

Controllo di doppioni, codice morto e componenti non usati nelle due pagine nuove (Da confermare, Attrezzatura). Niente cambia a vista, salvo dove si dice.
- **PillolaScelta forma "risposta"**: la pillola da 44 col pallino di Da confermare (con la riga sotto diventa blocco a angoli di 18), prima copiata in Da confermare (due volte) e nel Modulo. Ora la usano tutti e due. Parametro `fondo` con `carta2` e `vuoto` (il Modulo la mette trasparente).
- **Scheletro**: Da confermare e Attrezzatura usano il componente con le misure vere, come le altre pagine (prima blocchi pulsanti scritti a mano). In Da confermare lo scheletro prende tutta la larghezza, indice compreso.
- **moto.js** caricato nella testa della pagina come in Notti e Archivio (prima ogni pagina lo caricava da se').
- **Modulo** in Sistema, con un esempio (ottica nuova, rapporto focale calcolato). Esce il segno nella testa del Modulo, mai usato.
- Codice morto: in Da confermare `testa` aveva un "|| true", il vecchio scheletro della colonna di sinistra, `skT` e `indSk`.
- **Cattura**: `#att_d`, `#att_t`, `#att_car`, `#dc_d`, `#dc_t`, `#dc_car`.
- Restano copie, non componenti (una pagina sola o forme diverse): la riga d'esito sopra le sezioni di Da confermare e la riga dei frame da rielaborare di Attrezzatura (simili: diventano un componente se una terza pagina ne ha bisogno); il segno "!" piccolo nel piede di Da confermare e negli errori del Modulo (Avviso "riga" ha un'altra misura).
- Da fare per il porting: le classi di Da confermare, Attrezzatura e Modulo in `astrolog.css` e nel Foglio.
- **Accento e animazioni** (17/10, con Attrezzatura): nel conto una tacca per domanda (a contorno senza risposta, accento da applicare, verde salvata), nello stesso ordine dell'indice. Da `componenti/moto.js`: la domanda che si apre sale e sfuma (0,3 s); conto e piede contano quando cambiano; l'esito di Applica entra dall'alto. Fermi col movimento ridotto.

## v15.2 · Attrezzatura a carte (18 ottobre 2026, scelta dall'utente)

L'utente: "troppo elenco rispetto alle altre pagine". Pagina `pagine/Attrezzatura v2.dc.html`; stessi dati, stati, moduli e Tweaks della v15. Supera l'indice a sinistra della v15 e il "niente tessere" (valeva per la forma dell'11 ottobre).
- **In testa** i corredi come carte bento (cinque per riga sul desktop, due sul telefono): nome su due righe al massimo, ottica e camera sotto, ore come numero, focale, barra delle ore, nove tacche delle parti, "{n} da indicare". La scelta nell'accento. Sotto i componenti a tessere: segno del tipo in un disco, nome del gruppo, numero dei pezzi.
- **Carta del corredo**: ore e misure a sinistra; a destra ottica e camera in grande, col segno e la scheda (senza peso).
- **Campo**: i campi dei corredi a confronto, ciascuno col suo nome breve (nome dato, o ottica + camera senza marca), quello scelto nell'accento; al centro la Luna piena (0,52°) nel grigio della Luna. Si vede anche con un corredo solo. Esce la didascalia.
- **Parti** a tessere, 4 colonne (2 sul telefono): ottica e camera larghe il doppio in prima riga, nomi piu' grandi; programma di ripresa largo il doppio in fondo. Da indicare: contorno e segno tratteggiati, "Seleziona" pieno. Le tacche escono da qui (restano sulla carta in testa).
- **Filtri** ad anello nei colori dei filtri, come nella Dashboard, col numero al centro.
- **Gruppi**: un pezzo per carta (segno o disco del filtro, nome, scheda a pillole, ore in grande con la barra, Modifica); il modulo si apre su tutta la riga.
- (fatto, v18) Sostituisce `Attrezzatura.dc.html`.
- **Carte in testa, secondo giro** (18/10, l'utente): il titolo e' il nome dato o ottica + camera senza marca; sotto un elenco puntato, ottica e camera una per riga.
- **Tendine del Modulo** come gli altri campi (18/10, l'utente): stesso bordo, angoli e altezza dei campi di testo, freccia disegnata a destra al posto di quella del sistema. Vale per tutte le pagine che usano il Modulo.
- **Campi dei moduli da rivedere** con Claude Code (l'utente: "mancano alcune cose"): domande in `docs/per-claude-code-attrezzatura-campi.md`.

## v16 · I dati completi dell'attrezzatura (18 ottobre 2026, da Claude Code, ADR 0021)

Ogni pezzo porta la scheda tecnica del produttore, tutta modificabile; il corredo ci calcola sopra. Le etichette nuove sono proposte, da approvare con Marco; quelle esistenti restano parola per parola. Pagina `pagine/Attrezzatura v2.dc.html`, Meteo in `pagine/Meteo.dc.html`.
- **Tipi nuovi**: guida fuori asse (Spessore, Prisma) e distanziale (Spessore), con segno e gruppo loro ("Guide fuori asse", "Distanziali"). Tasselli del tipo su 6 colonne (2 sul telefono).
- **Campi per tipo** (blocco "dati tecnici", Peso in tutti): ottica Apertura, Focale nativa, Cerchio d'immagine, Backfocus richiesto, calcolati Rapporto focale e Potere risolutore; camera Sensore, Risoluzione (px) larghezza × altezza in un campo solo, Pixel, Tipo di sensore, Bit dell'ADC, Raffreddata sì/no e, solo col sì, Raffreddamento (°C sotto l'ambiente), Spessore fino al sensore, calcolata Dimensione del sensore; camera di guida come la camera senza raffreddamento; ottica di guida Apertura, Focale; montatura Carico con e senza contrappeso; riduttore Fattore, Backfocus richiesto, Cerchio d'immagine (barlow: fattore sopra 1); ruota Numero di posizioni, Misura dei filtri, Spessore; focheggiatore Passo, Passi totali. Filtro: bande, poi Misura, Montato, Per ottiche veloci, Spessore. Sì/no e misure come pillole; "{n} di {m} scritti" conta anche i campi nuovi.
- **Dai file** solo nomi, pixel, tipo di sensore, risoluzione e focale effettiva; il valore scritto vince.
- **Parti del corredo**: dieci. Nuove la guida (ottica di guida oppure OAG, una tendina sola) e i distanziali (pillole a scelta multipla). Tessere su 4 colonne: ottica e camera doppie in prima riga.
- **Conti** (carta a tutta larghezza sotto le parti), regole di Claude Code: rapporto focale, scala prevista (con la misurata), campo previsto 2·atan(lato / 2f) (col misurato), copertura (diagonale contro cerchio del riduttore o dell'ottica), scala di guida (OAG con la focale del corredo; avviso fuori da 0,5–4″/px), rapporto guida/ripresa, campionamento "ottimo con seeing fra 2× e 3× la scala", backfocus del treno (OAG + ruota + distanziali + camera, differenza senza giudizio), carico (somma dei pesi sul carico piu' alto, avviso sopra 100 %). Tre stati: valore su carta2; avviso col segno "!"; "manca …" a contorno col segno "?", che nomina il primo dato mancante.
- Verifica sull'esempio di Claude Code ("Notte in quota"): f/5,6 · 1,94″/px · 3,36° × 2,25° · 1,61″ · 3,9–5,8″ · guida 6,45″/px con avviso · 3,3×. La camera di guida d'esempio passa a 3,75 µm.
- **Meteo**: carta "Campionamento" dopo "Altre misure" (sul telefono in fondo alla carta delle altre misure), una casella per corredo con la scala: ✓ ottimo, ↓ sottocampionato (scala oltre meta' del seeing), ↑ sovracampionato (sotto un terzo). Seeing della notte come gia' mostrato; senza chiave Meteoblue, col seeing sotto le nubi, nelle notti di tendenza e di giorno la carta non c'e'. Scale dei corredi copiate dall'Attrezzatura (simulate).
- Tweaks nuovi di Attrezzatura: camera con tutti i campi, guida fuori asse, distanziale, distanziali del corredo.
- Dati simulati: tutte le schede tecniche dei pezzi.
- **Secondo giro (18/10, l'utente)**: i conti salgono dentro la carta del corredo come "I numeri del corredo", nove mini carte 3 × 3 (2 colonne sul telefono). Esce la carta "Conti" in fondo. Campo e filtri stanno a destra uno sopra l'altro; le parti vanno a tutta larghezza su 6 colonne. Pillole d'esito (componente Pillola) dove l'app ha una regola: copertura ✓ ci sta / ✕ non ci sta; scala di guida ✓ nei limiti / ! fuori dai limiti (0,5–4″/px); carico ✓ entro il carico / ✕ oltre il carico. Le pillole "buone" sono nuove (Claude Code dava solo l'avviso): da confermare con Marco. Rapporto focale, scale, campo, rapporto guida/ripresa e backfocus restano senza giudizio, come da brief; il campionamento rimanda a Meteo per il giudizio della notte.
- **Meteo**: le pillole del campionamento sono quelle degli esiti: ✓ ottimo (buona), ! sottocampionato e ! sovracampionato (incerta).
- **Correzioni (18/10, l'utente)**: il campionamento e' la scala in ″/px (focale e pixel), non l'intervallo di seeing. "Scala prevista" diventa "Campionamento" (col valore sul cielo e "ottimo con seeing fra {2×} e {3×}″" sotto); al suo posto, fra i nove, "Dimensione del sensore". In Meteo la scala e' il numero di ogni casella.
- **Backfocus con giudizio**: il richiesto viene dal campo "Backfocus richiesto (mm)" del riduttore, o dell'ottica senza riduttore; tolleranza ±1 mm (l'utente: ±0,5 o ±1, da scegliere con Marco; `TOLL_BF`). Pillole: ✓ "pari" / "+0,5 mm, in tolleranza"; ! "corto di 17,5 mm" / "lungo di …". Supera il "senza giudizio" della brief di Claude Code: da dirgli.
- **Il treno ottico** (18/10, l'utente; supera "niente catena della luce" della v15): sotto "I numeri del corredo", nella carta del corredo, il corredo disegnato senza montatura, in vista di tre quarti e nelle misure vere dei pezzi (mm). Si disegnano solo i pezzi indicati: ottica secondo lo schema ottico (rifrattore con paraluce e vetro; Newton col treno in verticale sul fuocheggiatore; Schmidt-Cassegrain e Maksutov con la cella posteriore; Ritchey-Chrétien con la crociera), anelli e coda di rondine, riduttore, guida fuori asse con la camera di guida sul prisma, distanziali, ruota portafiltri decentrata, camera con le alette, motore del focheggiatore, tubo guida sopra l'ottica con la sua camera. Passando su un pezzo si accende nell'accento e gli altri si spengono; toccato, apre il pezzo fra i componenti. Sotto, i pezzi in pillole con lo stesso comportamento (servono anche a chi usa la tastiera o legge con la voce). Le mini carte dei numeri si stringono (numero 20 px).
- Campo nuovo dell'ottica: **Schema ottico** (rifrattore, Newton, Schmidt-Cassegrain, Ritchey-Chrétien, Maksutov), da approvare con Marco e chiedere a Claude Code. Colori dei pezzi nel disegno: simulati, per marca; da decidere se l'app li sa.
- **Il treno ottico, seconda resa** (18/10, l'utente: "troppo giocoso"): disegno tecnico a linee, senza riempimenti ne' colori, linee nascoste coperte dal fondo; linea dell'asse ottico tratto-punto. Il pezzo sotto il puntatore si accende nell'accento, gli altri si spengono. Escono i colori per marca. Ordine del treno confermato: riduttore, guida fuori asse, distanziali, ruota, camera.
- **Il treno ottico, terza resa** (18/10, l'utente): vista isometrica vera (asse ottico a 30°, visto dall'alto e di lato) e in esploso, 30 mm fra un pezzo e l'altro lungo l'asse; a linee, linee nascoste coperte dal fondo. Escono le pillole sotto il disegno: passando su un pezzo (o col fuoco della tastiera) compare un riquadro col tipo, il nome e "tocca per aprire". Sul telefono il tocco apre il pezzo.
- **Il layout del corredo, quarto giro** (18/10, l'utente: "rivedere il layout"): due colonne. Larga (8): carta del corredo (nome, ore, misure, ottica e camera), il treno ottico in una carta sua, le parti a tessere su 4 colonne. Stretta (4): campo, "I numeri del corredo" come elenco a righe (nome e valore sulla stessa riga, pillola e nota sotto, "manca …" in tenue), filtri. Sul telefono una colonna: corredo, treno, parti, campo, numeri, filtri.
- **Etichette del treno**: pillole fisse coi nomi, sopra e sotto il disegno, legate al pezzo da un filo con un punto; focheggiatore e guida sopra, gli altri alternati; spinte di lato perche' non si tocchino. Pillola o pezzo: si accendono insieme, il tocco apre il pezzo. Esce il riquadro al passaggio. Sul telefono le pillole hanno il numero e sotto c'e' la legenda numerata a due colonne (44 px).
- **Componenti in testa**: pillole compatte (segno, nome, numero) al posto delle tessere.
- Il disegno del treno al massimo alto 400 px (300 sul telefono), centrato; le etichette seguono la sua larghezza.
- Ritocchi (18/10, l'utente): nella carta dei filtri l'elenco a sinistra e l'anello a destra (170 px), cosi' la colonna destra finisce con le parti. La guida fuori asse si disegna tonda, col prisma tondo. Il disegno del treno: approvato.
- **Chiusura di Attrezzatura v2** (18/10): nel campo le etichette dei corredi alternate in alto e in basso (non si sovrappongono piu'); il treno si disegna in 0,9 s quando cambia il corredo (fermo col movimento ridotto). Domande per Claude Code in `docs/per-claude-code-attrezzatura-v2.md`.

## v16.1 · Attrezzatura v2, risposte di Claude Code (18 ottobre 2026, testi approvati da Marco; ADR 0021)

- **Difetti corretti**: "Distanziali" senza "(vuoto: dai file)" (nessun file li indica). Treno: "Schema non in scala. Seleziona uno strumento per aprirlo." (tubo, camera e diametri sono stimati). **Numeri scientifici col punto** (regola dell'app): campionamento, scala di guida, potere risolutore, seeing del campionamento ("1.94″/px", "1.61″"); millimetri, chili e percentuali con la virgola.
- **Testi**: "Dati del corredo" · "Dalle schede tecniche degli strumenti." · "Treno ottico" · "copre il sensore" / "non copre il sensore" · "nell'intervallo" / "fuori intervallo" · "esatto". "Pezzo" non si usa a schermo: la parola e' "strumento".
- **Schema ottico** entra nell'app, con "obiettivo fotografico" e "altro" (si disegnano come il rifrattore).
- **Backfocus**: niente tolleranza fissa. Campo nuovo "Tolleranza del backfocus (mm)" in ottica e riduttore (vale quella del riduttore, se c'e'). Con la tolleranza: pillola "esatto", "+0,5 mm, in tolleranza", "corto di …", "lungo di …". Senza: solo la differenza, senza pillola, e "tolleranza non indicata".
- **Camera**: campo "Bias (ADU)", facoltativo (servira' alla luminosita' del cielo).
- **Meteo**: le scale dei corredi arrivano dall'app; nel disegno restano simulate.
- L'ordine del treno vale solo per il disegno; l'app non lo conosce e i conti non ne dipendono.

## v17 · Le misure dei frame (18 ottobre 2026, ADR 0022)

Tavola `pagine/Misure dei frame.dc.html` (Tweaks: stato, formato, modo, accento); i pezzi entrano in Notti e Archivio quando sono approvati. Brief sotto.
- **Notti, la riga di un oggetto**: testa (oggetto, corredo e scala, ore, frame), pillole dei filtri col pallino della tinta e il numero dei frame, "su N di M frame". Mediane della notte in nove tessere (FWHM e HFD con lo zenit, stelle e sature, eccentricita' con "✓ rotonde" e la direzione, SNR, fondo col rumore, gradiente col lato, tilt · curvatura, luminosita' del cielo). Grafico: un punto per frame nella tinta del filtro, altezza tratteggiata sulla scala di destra in gradi, stesso asse del tempo; segmentato "misurata / allo zenit". Segni: punto vuoto = forma stimata, × in basso = troppo poche stelle, cerchietto in basso = misura in corso. Toccato un punto (o con ‹ ›), il frame scelto sotto: titolo "Frame 6 di 120 · L", ora, altezza e massa d'aria, FWHM come numero grande, le altre in tessere.
- **Tilt e curvatura**: rettangolo del sensore con un cerchio per angolo e al centro, grande quanto la HFD, il valore in px; l'angolo con la HFD piu' alta nell'accento. Sotto tilt e curvatura come numeri. Conti del disegno (da confermare con Claude Code): tilt = (angolo massimo − angolo minimo) / centro; curvatura = (media degli angoli − centro) / centro; danno 17 % e 11 % sull'esempio.
- **Archivio**: per produzione, pillole come nel riepilogo; tre carte (FWHM, eccentricita', SNR) con la mediana come numero, la scatola dei quartili nell'accento e il segno della mediana, "quartili 3.3″ – 4.0″"; nell'eccentricita' la linea tratteggiata a 0,45 e "✓ rotonde" se la mediana ci sta. Produzione senza scala: FWHM in px, "Senza scala del cielo: in px, non si confronta fra corredi."
- **Luminosita' del cielo**: tessere per filtro; scala da 17 a 22 con "più alto il numero, più buio il cielo". "senza bias" come etichetta a contorno, "manca il catalogo V50" col segno "?". Con Hα, OIII e SII nessuna riga.
- **ASTAP**: la riga nel passo del Primo avvio (catalogo mancante) e nelle Impostazioni, dove i cataloghi D80 e V50 hanno ✓ trovato / ? non trovato.
- **Stati**: "misura in corso" (pallino che pulsa; le mediane valgono sui frame gia' misurati), "troppo poche stelle" (segno "?", nessun numero), forma stimata (segno "!", etichetta "stimata" su FWHM ed eccentricita', niente pillola "rotonde"), senza scala del cielo (px, niente zenit, niente luminosita' del cielo), senza sito (niente zenit, altezza ne' massa d'aria). Ogni carta degli stati porta la riga in alto in quello stato.
- **Testi nuovi, da approvare con Marco**: "Mediane della notte", "FWHM e altezza dell'oggetto", "misurata / allo zenit", "Frame 6 di 120", "massa d'aria 1,74", "± 21 di rumore", "Forma stimata: il fit non è riuscito.", "stimata", "Senza scala del cielo: FWHM e HFD in px, niente zenit.", "Senza sito: niente zenit.", "Il catalogo V50 serve a misurare la luminosità del cielo nei frame R, G e B.", "Catalogo D80 / V50 · trovato / non trovato", "quartili", "Rotonde fino a 0,45.", "È una stima." (con "senza bias").
- **Da chiedere a Claude Code**: la luminosita' del cielo senza scala del cielo (qui non c'e'); se "rotonde" vale anche con la forma stimata (qui no); il lato del gradiente nelle mediane (qui il piu' frequente); le formule di tilt e curvatura.
- **Numeri**: scientifici col punto (3.7″, SQM 19.2, 1.94″/px), eccentricita', massa d'aria e percentuali con la virgola come nel brief; stelle all'italiana (1.240).
- **Dati simulati**: tutti i frame (M 31 da Cima Ekar, transito alle 02:00; L 120 frame dalle 20:30, R G B 20 ciascuno), le tre produzioni, le luminosita'. Il frame 6 di L e' l'esempio del brief.
- **Nel riepilogo della notte** (18/10, l'utente): la riga di un oggetto diventa il componente `componenti/MisureOggetto` e va nel riepilogo della notte (la finestra di Notti) come carta "Le misure per oggetto", dopo "Gli oggetti": pillole degli oggetti della notte con le ore, poi testa, filtri della notte, mediane, grafico e frame scelto, a una colonna. La tavola usa lo stesso componente. Filtri, frame, corredo e scala vengono dalla notte (Casa: Casa leggero, 3.82″/px, simulata). Con filtri a banda stretta (Ha, Hβ, OIII, SII e i filtri a piu' bande stretti) la luminosita' del cielo non c'e'; con R, G, B si scrive la banda; con L, senza filtro e a colori e' "SQM". L'asse del tempo copre i frame dell'oggetto (almeno 4 ore). "Le metriche dei frame" resta sotto, com'era.
- **Archivio**: superato dal Riepilogo v2, sotto.

### v17.1 · Riepilogo v2: le misure dei frame (18/10, proposta di Claude accettata dall'utente)
Componente `componenti/MisureFrame`, uguale nel riepilogo della notte e dell'oggetto; cambia solo cosa si confronta (gli oggetti della notte, le notti dell'oggetto). Sostituisce "Le metriche dei frame", "Le misure per oggetto" e "Per filtro". Pagina `pagine/Riepilogo v2.dc.html` con `componenti/RiepilogoV2`; il riepilogo di prima resta finche' questo non e' approvato.
- **Le misure**: dodici tessere (FWHM, HFD, stelle e sature, eccentricita', SNR, fondo, rumore del fondo, gradiente, tilt, curvatura, luminosita' del cielo, massa d'aria): mediana, quartili, mini-curva. Toccate entrano nei grafici, fino a tre, ognuna nel suo colore (anello e pallino). Fondo, rumore e luminosita' con piu' filtri dicono "per filtro" / "per banda": si confrontano solo nella tabella. Filtri a pillole con "tutti"; "su N di M frame".
- **Per filtro**: tabella, una riga per filtro (frame, FWHM con sotto solo "sottocampionata", senza lo zenit: si guarda nel grafico, 18/10 l'utente; HFD, eccentricita', SNR, fondo col rumore, tilt, curvatura, luminosita'); toccata una riga resta quel filtro.
- **Frame per frame**: grafici uno sotto l'altro, stesso asse; ordine "per ora" (nella notte gli oggetti in fascia; nell'oggetto le notti in fila, separate), "per massa d'aria", "per valore" (dal piu' basso al piu' alto; sostituisce "dal migliore al peggiore": niente giudizio); "misurata / allo zenit". Con allo zenit e per ora, sulla FWHM il seeing previsto tratteggiato.
- **A confronto** (le notti / gli oggetti): una riga per gruppo con la scatola dei quartili della misura scelta, tutte sulla stessa scala, mediana, verdetto della notte; nell'oggetto "seeing previsto 2.2″ · FWHM allo zenit 2.1″" o "seeing non disponibile per questa notte". Toccata una riga, resta solo quella ("solo … ×" in testa).
- **Tilt e curvatura**: il rettangolo del sensore con le mediane, accanto uno piccolo per filtro.
- **Il frame**: quello toccato, con tutte le misure.
- **Risposte di Claude Code (18/10)**: il seeing previsto c'e' per le notti da quando l'app ha la chiave Meteoblue (ultima previsione prima della notte, tabella weather_nights); prima non c'e' e non si recupera (lo storico non lo porta); se Meteoblue rifiuta la chiave, si cancella tutto il seeing salvato. La riga deve saper tacere. Le misure valgono per ogni filtro, banda stretta compresa; gli angoli del sensore su ogni frame. La direzione dell'allungamento si mostra solo con eccentricita' da 0,40. Sotto 2 px di FWHM la FWHM porta "sottocampionata" (frequente in banda stretta).
- **Testi nuovi, da approvare**: "Frame per frame", "per ora / per massa d'aria / per valore", "dal valore più basso", "Le notti a confronto", "Gli oggetti a confronto", "seeing previsto", "per filtro", "per banda", "si confronta per filtro", "solo {nome} ×", "stessa scala per tutte le righe".
- Simulato: seeing previsto, frame, verdetti; nella notte del 16 settembre il seeing non c'e'.
- **Approvato dall'utente (18/10)**: "Frame per frame" a barre e linee, un grafico per filtro, "per valore" sulla prima misura. Tratteggio della seconda misura piu' leggero; in cima alla barra tratteggiata un trattino nel colore del testo, sopra la barra piena con un bordo del colore della carta, cosi' si legge anche quando la seconda misura sta sotto la prima. Chieste a Claude Code (`docs/per-claude-code-misure-giudizi.md`): il backfocus dai frame (verso l'interno o l'esterno, accanto al tilt) e i giudizi sulle misure (FWHM contro seeing e corredo, SNR, tilt, curvatura, gradiente, luminosita'), che superano il "nessun voto" dell'ADR 0022: decide Marco.
- **Terzo giro (18/10, l'utente: "devo analizzare frame per frame")**: "Frame per frame" e' un grafico per filtro (pillole a scelta multipla "Un grafico per filtro"), uno sotto l'altro con le stesse scale. Una barra per frame nell'ordine di ripresa (asse a numero di frame, niente buchi), separatori tratteggiati col nome della notte o dell'oggetto. Due misure al massimo, scelte dalle tessere: la prima a barre piene nel colore delle barre dell'anno della Dashboard (monthBar, il frame scelto nell'accento), la seconda a barre tratteggiate, con la sua scala a destra; come il 2026 contro il 2025 della Dashboard. Le barre partono dal minimo dell'asse. Vista "barre / linee": in linee la prima e' la linea dell'accento con alone (come la qualita'), la seconda tratteggiata nel colore del testo. Colori dei filtri solo nella pillola del grafico. Riquadro al passaggio: frame N di M, notte e ora, le due misure, la massa d'aria; il tocco apre il frame. Oltre ~180 frame (90 sul telefono) sotto il grafico la striscia di tutti i frame con la finestra da trascinare, ‹ › e le pillole delle notti. Ordine "per ora" o "per valore". Escono "per massa d'aria" (si confronta con la massa d'aria come seconda misura), la mediana mobile, i punti e il seeing previsto nel grafico (resta in "A confronto").
- **Secondo giro (18/10, l'utente: "coi puntini è difficile capire l'andamento")**: grafici a "linee" di partenza: per ogni filtro (e notte) la mediana mobile di 9 frame in tratto spesso, i frame come punti tenui sotto; "punti" resta come scelta. Le misure scelte nell'accento (anello, fondo tenue, mini-curva), al posto dei colori delle curve, che nei grafici non comparivano. Ordine nuovo: misure, grafici, il frame, a confronto, per filtro, tilt e curvatura. Corretto: un filtro senza frame in una notte (Hβ) dava errore.
- **Da fare**: il Riepilogo con queste misure (oggi: FWHM, eccentricita', stelle, fondo, rumore, SNR, altezza); i pezzi dentro Notti e Archivio.

### Brief (ADR 0022, Claude Code 18/10, testi approvati da Marco)
 **A cosa serve**: vedere com'e' venuta ogni ripresa con le misure dell'app, senza voti ne' scarti. **Dati**: per frame FWHM e FWHM allo zenit (″, col punto), HFD e allo zenit, stelle e sature, eccentricita' ("rotonde" fino a 0,45) con la direzione "in AR" / "in Dec", SNR, fondo in ADU col rumore (si confronta solo con stessa camera, guadagno, posa), gradiente (% e lato), tilt e curvatura (% dalle HFD di quattro angoli e centro, su un rettangolo del sensore), luminosita' del cielo ("SQM 19.2" con L, senza filtro e a colori; "R: 20.8 mag/arcsec²" con R, G, B; mai con Hα, OIII, SII; "senza bias" quando manca il bias della camera; R, G, B chiedono il catalogo V50 di ASTAP: "manca il catalogo V50"). Zenit = valore / massa d'aria^0,6. **Dove**: Notti (per oggetto e filtro le mediane; grafico della FWHM frame per frame con l'altezza dell'oggetto sullo stesso asse del tempo), Archivio (per produzione: mediana e quartili di FWHM, eccentricita', SNR), la riga sul V50 nel passo di ASTAP (Primo avvio e Impostazioni). Il Riepilogo ha gia' metriche simulate: va allineato. **Stati**: "misura in corso", "troppo poche stelle", forma stimata, senza scala del cielo (FWHM e HFD in px, niente zenit), senza sito o coordinate (niente zenit), mediane "su 112 di 120 frame". **Esempio**: Notte in quota, M 31 in L a 35°: FWHM 3.7″ (zenit 2.7″), HFD 5.0″ (3.6″), 1240 stelle, 18 sature, eccentricita' 0,42 rotonde in AR, SNR 34, fondo 812 ADU ± 21, gradiente 6 % piu' chiaro verso est, angoli 2.5 / 2.7 / 2.9 / 2.6 px e centro 2.4 px: tilt 17 %, curvatura 11 %, SQM 19.2. **Cosa non c'e'**: voto, frame buoni o cattivi, la scheda dell'oggetto, Statistiche (brief a parte).

## Ritocchi del telefono (18 ottobre 2026)
- Da confermare: il piede su telefono è una riga sola a fondo pieno («5 da applicare · Applica»); l’avviso dell’unione di strumenti è un «!» che si apre sotto. Niente più vetro: il testo sotto non si legge attraverso.
- Archivio: su telefono in testa restano linguette, numero, Cerca e Filtri; Carte/Elenco e l’ordine stanno dentro Filtri. Sole e Sistema solare, senza filtri, li tengono in testa.
- Riepilogo: su telefono ore, FWHM e SNR in fila alla stessa altezza; esito del cielo e filtri sotto.
- Notti: su telefono più righe di stato diventano una («N cose da vedere») che si apre.
- Meteo: su telefono la provenienza è una riga («Open-Meteo 2 ore fa · Meteoblue 14 ore fa»); toccandola si legge per intero.
- Strisce che scorrono di lato: sfumatura sul bordo dove continua, ovunque (tema.js).
- Barra in basso: la voce della pagina ha l’icona in una pillola nell’accento.

## v19 · Cerca (18 ottobre 2026)

Brief. **A cosa serve**: da ogni pagina trovare un oggetto, una notte, un pezzo di attrezzatura, un sito o una pagina, e aprirlo. **Dati**: per gruppo (oggetti, notti, attrezzatura, siti, pagine) al massimo 5 voci e quante in tutto («5 di 8»); oggetto con nome comune, frame e ore (mosaico coi pannelli); notte con sito, frame e ore e il perché («con M 31»); attrezzatura col genere, frame e ore o perché mancano; sito con le notti. **Stati difficili**: campo vuoto, niente, molti, senza tempo, non ancora contato, scansione in corso, archivio vuoto. **La cosa più importante**: dalla prima lettera alla cosa giusta col minimo di gesti. **Cosa non c'è**: i filtri dell'Archivio, la ricerca nelle note, la cronologia.

Scelte di Claude (l'utente: "decidi tu"):
- **Desktop**: finestra al centro sopra la pagina, larga 640, velo dietro; si apre da "Cerca" nella barra o con Ctrl K. In fondo "↑ ↓ scegli · Invio apre · Esc chiude". La voce scelta ha il fondo e il segno del gruppo nell'accento, e "Invio".
- **Telefono**: pagina intera sopra la barra, campo in alto con "Annulla", righe da 56; nessuna voce scelta di partenza.
- **Le pagine** stanno fra i risultati, ultimo gruppo.
- **Campo vuoto**: solo cosa si cerca, con un esempio per gruppo. Niente cronologia.
- **Come trova**: inizio del nome o di una sua parola, senza spazi né accenti («m31» = M 31, «ngc 7» = NGC 7000…); i nomi di catalogo (NGC 224, Caldwell 20) solo se si scrive una cifra. Date: «5/6» nei due versi, «2026-09-25», «25 settembre», «settembre 2026», «settembre». Un oggetto trovato porta le sue notti.
- **Testi nuovi, da approvare con Marco**: «Si cercano», «Niente per «…».», «Qui si cercano oggetti, notti, attrezzatura, siti e pagine.», «Scansione in corso, 19 %: quello che non è ancora stato letto non si trova.», «L’archivio è vuoto: oggetti, notti, attrezzatura e siti arrivano con la prima scansione. Intanto si trovano le pagine.»
- **Dati simulati**: l'indice degli oggetti, dell'attrezzatura e dei siti, e alcune notti vecchie; le altre notti vengono da `componenti/dati.js`.
- Componente `componenti/Cerca` (testo, stato, formato, statico, on-chiudi), montato dal Telaio (menu "cerca", prop cerca e cercaStato). Pagina `pagine/Cerca.dc.html` (Tweaks: ricerca, stato, formato, modo, accento); in Cattura `#ce|formato|ricerca|stato|modo`; nella tavola dei telefoni.
- `old/pagine/ricerca.html` si cancella quando la pagina è approvata; con lei `old/` resta senza pagine.
- **Moto** (18/10): la finestra entra dall'alto e un filo più piccola, il velo si scurisce (desktop); sul telefono la pagina sale di poco e sfuma. A ogni lettera le righe entrano in fila (25 ms l'una, al massimo 10). All'uscita il contrario, più breve. Fermo col movimento ridotto.
- **Tema**: tutto da `AL.tema`; l'accento solo sulla voce scelta (segno del gruppo pieno). Velo più scuro nel modo scuro (60 %) che nel chiaro (35 %).

## Misure dei frame · giudizi (18 ottobre 2026, risposta di Claude Code, decisioni di Marco)

- **Backfocus: no.** Da un frame solo il verso non è affidabile; restano tilt e curvatura, niente frecce per angolo.
- **Un giudizio per misura**, per frame, notte e produzione (mediana); mai un giudizio d'insieme, mai uno scarto. Soglie e fonti in `componenti/soglie.js` (`ALsoglie.misure`).
- **Pillole**: buono ✓ verde, incerto ! ambra, non adatto ✕ rosso; "nella media" è una pillola neutra (–). FWHM: eccellente, buono e "al limite del corredo" ✓; nella media –; scarso !; pessimo ✕. Eccentricità: rotonde ✓, allungate ! (oltre 0,71), in mezzo solo il numero. Tilt: buono / incerto / non adatto. Cielo: "come il Bortle del sito" ✓, "più chiaro del Bortle del sito" ! (solo L e senza filtro; senza Bortle del sito tace).
- **F del corredo** = il maggiore fra 2 × scala e 116/apertura; FWHM sotto F "al limite del corredo"; F oltre 3″ "non giudicabile su questo corredo", scritto sotto il valore. Con Notte in quota (1.94″/px) e Casa leggero la FWHM non si giudica mai: nella pagina delle misure il Tweak "corredo" prova Askar 103 + ATR2600M (1.385″/px).
- **Solo sul frame, contro la sua notte** (stesso oggetto e filtro, almeno 10 frame): "SNR basso per la notte" (sotto mediana − 2 MAD) sotto SNR, "fuoco peggiore" (HFD oltre +5 % sulle migliori) sotto HFD. Sotto 10 frame tacciono e lo dicono.
- **FWHM e HFD in due unità**: "2.9″ · 2.1 px". Campionamento a parte, senza voto, nell'etichetta a contorno: sottocampionata (grave) / sottocampionata / ideale / sovracampionata.
- **SNR** è la PSF SNR (centinaia): numero all'italiana, "si confronta nella notte".
- **Tilt come ASTAP**: (angolo peggiore − migliore) / HFD mediana. Tilt e curvatura tacciono sulle camere a colori con stelle sotto 1,2 superpixel: "stelle troppo piccole per una camera a colori".
- La riga sotto le mediane dice una volta che la FWHM è quella vera (circa il 14 % sotto PixInsight sulle stelle piccole).
- Nel frame la FWHM non mostra più lo zenit (l'utente: lo si guarda nel grafico).
- **Testi da approvare con Marco sulla tavola**: le parole dei giudizi, "non giudicabile su questo corredo", "fuoco: servono 10 frame della notte", "si giudica con 10 frame della notte", "si confronta nella notte", "stelle troppo piccole per una camera a colori", "senza Bortle del sito".
- Senza giudizio: curvatura, gradiente, stelle, sature, fondo, rumore, massa d'aria, direzione.
- **I giudizi sempre in pillola** (l'utente, 18/10): anche nella tabella "Per filtro" (FWHM, eccentricità, tilt, cielo) e sotto il tilt del rettangolo del sensore, grande e per filtro. Il campionamento resta etichetta a contorno; "non giudicabile su questo corredo" resta testo (non è un giudizio).
- **Riepilogo · Le notti**: la colonna della data non scende sotto 150 px (prima nella finestra a 8 colonne la data finiva sotto le ore); "La notte ↗" diventa la sola freccia, col nome per chi legge con la voce.
- **Luminosità del cielo, aggiornata** (Claude Code, 18/10): identica ad ASTAP. Solo L, senza filtro e camere a colori; R, G, B e filtri stretti mai. **Il V50 esce**: tolti "manca il catalogo V50", la riga nel passo di ASTAP (Primo avvio) e la sezione della tavola. Mono senza bias: il numero con "senza bias"; a colori senza bias: niente SQM, "serve il bias della camera" e il rimando "Bias (ADU) in Attrezzatura ↗".
- **Curva della notte nelle Notti** (componente MisureFrame, tipo notte): "Luminosità del cielo nella notte", un punto per frame nell'accento, l'altezza della Luna tratteggiata sullo stesso tempo (0°–90°). Senza frame L o a colori: "nessun frame L o a colori in questa notte". Sotto: "Il valore cambia anche con la direzione del cielo." Nella simulazione la Luna sorge alle 00:30 e abbassa l'SQM.
- **Archivio · misure della produzione**: FWHM in due unità con giudizio e campionamento, eccentricità con pillola, SNR come PSF SNR; aggiunta la produzione Askar 103 + ATR2600M per vedere i giudizi della FWHM.
- **La curva della notte esce come sezione a parte** (l'utente, 18/10): la luminosità del cielo è una misura come le altre fra i riquadri, e si confronta nei grafici "Frame per frame" (es. FWHM contro SQM, gradiente o rumore contro SQM). **La Luna è un interruttore** (l'utente: non una misura), un bottone tondo con la falce (pieno nell'accento quando è acceso), accanto a "misurata / allo zenit": nei grafici in ordine di tempo una linea a puntini grigia, da 0° a 90°, in legenda e nel suggerimento ("altezza della Luna"). Con "per valore" l'interruttore non c'è. Nei grafici dei filtri senza SQM: "la luminosità del cielo c'è solo con L, senza filtro e a colori".
- **Tabella "Per filtro" più stretta** (l'utente: la luminosità usciva a destra): la colonna "Frame" entra sotto il nome del filtro ("60 di 60 frame"), colonne da 64 px (FWHM e luminosità da 84), le celle vanno a capo; le pillole della tabella vanno a capo anch'esse (Pillola, prop nuova `acapo`).

## Misure dei frame · giudizi relativi (18 ottobre 2026, risposta di Claude Code, decisioni di Marco)

- **Il frame contro l'oggetto** (solo nel riepilogo dell'oggetto): stessi oggetto e filtro, tutte le notti, almeno 10 frame. "SNR basso per l'oggetto" (mediana − 2 MAD, SubframeSelector) e "HFD alta per l'oggetto" (mediana + 2 MAD; non "fuoco": fra notti la HFD cambia col seeing). Accanto ai giudizi della notte, due pillole distinte, mai unite. Sotto 10: "meno di 10 frame dell'oggetto in questo filtro".
- **HFD contro l'archivio: solo il numero**, sotto la mediana: "mediana del corredo: 2.6 px" (stesso corredo e filtro, tutti gli oggetti; simulata).
- **SNR fra oggetti diversi: no.**
- **Massa d'aria**: nel frame un riquadro suo con l'altezza; "oggetto basso" (!) sopra 2, cioè sotto 30° (AAVSO). Tace senza sito.
- **"Non giudicabile su questo corredo"**, nella mediana: "Limite del corredo 3.9″: due pixel da 1.94″." (o "la diffrazione dell'apertura" quando vince quella). Nel frame solo la prima frase.
- Regole in `soglie.js`: `snrBassoOgg`, `hfdAltaOgg`, `basso`.

## Correzioni dopo il controllo della v18.1 (18 ottobre 2026, Claude Code)

- **Luminosità del cielo nel componente** (MisureFrame, in Notti e Archivio): con la camera a colori senza bias niente SQM, "serve il bias della camera" e "Bias (ADU) in Attrezzatura ↗" (nel frame); con la mono senza bias il numero con l'etichetta "senza bias" (tolto "È una stima."). Il giudizio contro il Bortle vale anche per le camere a colori. Nuovo stato "senza bias" (prop `bias`, Tweak nella pagina delle misure).
- **Avvertenze**: nel riquadro della notte senza frame adatti "nessun frame L o a colori in questa notte"; nei grafici con la luminosità scelta, accanto al filtro, "il valore cambia anche con la direzione del cielo".
- **Testi allineati all'app**: "stessa esposizione" (non "posa"); SNR "solo dentro la stessa notte e lo stesso oggetto, mai fra camere"; "Tipo non disponibile", "Costellazione non disponibile"; "Tutti gli strumenti" / "Meno strumenti"; filtro ignoto "Filtro non indicato"; Cerca "senza durata"; secondi d'arco col punto (1.6″, 46.2″, RA 305.2 Dec 40.6, 1.94″/px); Archivio vuoto "Archivio vuoto" / "Aggiungi le cartelle dei file e avvia la scansione."; Luna "sale fino a 68° alle 07:30"; Dashboard senza "tu" ("Qui compaiono…", "Il sito di ripresa: …"); legenda del calendario col testo dell'app; Notti: "37 frame da confermare · Apri Da confermare", "112 frame senza sito", "Sito mancante" / "I frame sono stati letti, ma senza un sito non possono essere assegnati a una notte." · "Aggiungi sito", "Le notti compaiono man mano che i frame vengono letti.", "Non disponibile" / "Fuso orario del sito non riconosciuto.", "Notti non disponibili", "Notte non trovata" / "I frame sono stati rimossi o spostati.", "Carica altre", "Le notti vengono create dai frame delle cartelle aggiunte."; Menu "Lettura dei file", "Lettura di una cartella non completata. Controlla il disco e riprova."; Primo avvio "Ricerca non riuscita" / "Il servizio non ha risposto.".
- **Attrezzatura**: "Riduttore" e "Guida" senza "(vuoto: dai file)"; backfocus senza tolleranza: solo la differenza ("+0,0 mm"), niente "esatto"; sotto la Luna del campo "Luna piena, per misura".
- **Tolto il non deciso**: nel giorno del Sole il riquadro "Seeing migliore · col Sole sopra 15°"; "oggetto finito" diventa "oggetto"; le produzioni senza l'anno davanti (l'anno va nella riga sotto); "la Luna tramonta" al posto di "scende sotto 10°".
- **Dati coerenti** (`dati.js`): "Notte in quota" = Askar FRA400 · ASI2600MM Pro, 1.94″/px; "Casa leggero" = RedCat 51 · ASI294MC Pro, 3.82″/px.
- **Approvati da Marco**: "fuoco: servono 10 frame della notte", "si giudica con 10 frame della notte", "stelle troppo piccole per una camera a colori", "senza Bortle del sito", "come il Bortle del sito / più chiaro del Bortle del sito", "SQM 19.2". Il limite del corredo per diffrazione: "diffrazione dell'apertura da {D} mm."
- `soglie.js`: la tabella SQM ↔ Bortle ha i numeri di ASTAP (ClearDarkSky), corretto il commento.
- Da controllare da Claude Code alla prossima: le tavole "stati" e Telefono.dc.html.

## Il Bortle del sito dalle misure (18 ottobre 2026, Claude Code, decisioni di Marco)

- L'app propone, l'utente sceglie; non lo cambia mai da sola. Frame con lo SQM e col bias; Sole sotto −18°, Luna sotto −5°, oggetto sopra 30°; notti in almeno 6 mesi diversi negli ultimi 12 (scelta di Marco); mediana per notte, poi delle notti. Ricalcolo a ogni scansione; dopo «Lascia» si propone di nuovo solo se la classe misurata cambia.
- Parole: «Le misure di Cima Ekar dicono Bortle 5 (SQM 19.6, 34 notti). Nel sito c'è Bortle 4.» · «Usa Bortle 5» · «Lascia Bortle 4»; sotto il Bortle del sito «misurato su 34 notti» o «scritto a mano»; dati scarsi «Servono notti in 6 mesi diversi: finora 4 notti in 2 mesi.» Il giudizio «come / più chiaro del Bortle del sito» resta.
- **Dove (proposta di Claude Design, approvata dall'utente il 18/10)**: nelle Impostazioni del sito (numero, provenienza, SQM e notti; con dati scarsi sei tacche dei mesi, piene quelle che contano) e la proposta come riga d'avviso nella Dashboard, che sparisce con «Usa» o «Lascia». In Statistiche la curva dello SQM del sito nei mesi, col suo brief. Per ora i tre pezzi stanno nella tavola `Misure dei frame.dc.html` ("Il Bortle del sito dalle misure"); entrano nelle pagine quando si disegnano Impostazioni e la riga della Dashboard.
- Testo nuovo da approvare: «Resta Bortle 4; si propone di nuovo solo se la classe misurata cambia.» (dopo «Lascia»), «SQM 19.6 · mediana di 34 notti in 9 mesi».
- **Cerca approvata** (l'utente, 18/10). Tolto `old/pagine/ricerca.html`. Da fare quando arrivano i piani: un gruppo "piani" fra i risultati; un oggetto si trova come oggetto e porta con sé le sue notti, le sue produzioni dell'Archivio e i suoi piani.
- Tolto anche `old/pagine/telaio.html` (il Telaio nuovo lo sostituisce): `old/` non ha più pagine; restano docs, foglio, astrolog.css e indice come archivio.

## Planner, cielo profondo (18 ottobre 2026, brief di Claude Code, ADR 0023)

Brief. **A cosa serve**: trovare un oggetto, provarlo col corredo, inquadrarlo e crearne il progetto. **Dati**: catalogo dell'app (e Sesame/CDS se manca), corredi di Attrezzatura o di prova, il cielo fotografico, altezza e Luna stanotte, ore utili mese per mese, filtri adatti alla camera. **Stati difficili**: corredo di prova, due corredi, mosaico, progetto doppione, progetto già iniziato, nome trovato solo online, senza rete, mappa che non copre la zona, senza sito. **La cosa più importante**: la carta, col campo vero sopra il cielo vero. **Cosa non c'è**: punteggi d'insieme e classifiche «i migliori stanotte», il modo Sistema solare (solo il selettore), le sequenze e il piano della notte.

Pagina `pagine/Planner.dc.html` (Tweaks: stato, modo, accento). Solo desktop; telefono e tablet dopo.
- **Disposizione**: Trova a sinistra (3 colonne, alta quanto carta e riga sotto); la carta a destra (9); sotto Stanotte (5) e Periodo migliore (4); in fondo Crea, con le ore a sinistra e totale e Salva a destra. In testa «Planner» e il selettore «Cielo profondo · Sistema solare» (il secondo spento, «Arriva con una brief sua»).
- **Trova**: un campo; i criteri del cielo sempre in vista come frase con tre numeri («sopra 30° per almeno 1 h · Luna ad almeno 40°»), «Valori dalle Impostazioni.» o «Cambiati solo per questa ricerca» con Ripristina; i criteri di catalogo in un riquadro chiuso col conto. Ordine del catalogo, mai per ore. Riga: nome e nome comune, ore utili stanotte, tipo e dimensione, «sale fino a 85° alle 01:15», Luna, «◉ progetto». Nome che non c'è: risultato online con la fonte in pillola e «Inquadra».
- **Corredo**: pillole a spunta in testa alla carta, al massimo due (il terzo toglie il più vecchio); il pallino ha il colore del rettangolo (accento il primo, bianco tratteggiato il secondo). «Corredo di prova» apre un riquadro sopra la carta con la fascia fissa, focale, apertura, riduttore o barlow, sensore (lista con ricerca per Deep sky, Planetario, Solare, Altri; IMX585 sta in due gruppi) o «Sensore personalizzato»; «mono / colore» se il sensore li ha entrambi.
- **La carta**: alta 520, fondo fotografico (proposta: per la tavola un'immagine sola chiesta a hips2fits del CDS, ridisegnata solo a carta ferma; nell'app Aladin Lite v3). Sopra, disegnati da noi: rettangolo (o mosaico) nell'accento del modo scuro in entrambi i modi, perché sta sempre su un fondo nero; mirino a quattro tacche con bordo scuro; orizzonte del sito tratteggiato con la parte sotto velata, solo quando cade nella carta; rosa N/E. Sulla carta: «Mappa» con le sette mappe e la copertura accanto, «Centra sull'oggetto», − e +, centro «RA 10.69 Dec 41.27», logo Aladin e crediti (riga NSNS con le mappe a banda stretta). Fuori copertura e senza rete: stelle disegnate e un riquadro al centro («Mappa non disponibile in questa zona del cielo» con «Passa a DSS2 colore»; «Cielo fotografico non disponibile senza rete»). Nessuno spinner: finché la mappa nuova non arriva resta la vecchia, spostata.
- **Sotto la carta**: Rotazione (cursore e numero, «dal Nord verso Est», 0–90° coi sensori quadrati); Mosaico (interruttore con «acceso / spento», colonne, righe, sovrapposizione, «2 pannelli · campo totale 3,46° × 1,29°»); poi i conti come la scheda del corredo: campo, mosaico, campionamento, rapporto focale; col secondo corredo anche il suo campo.
- **Stanotte**: ore utili come numero, la frase (buio, «sale fino a», Luna), curva con le fasce del crepuscolo della Dashboard, orizzonte del sito come area tenue, linea dell'altezza minima, Luna tratteggiata, tratto spesso = ore utili, «adesso 20:05». **Periodo migliore**: barre del 15 di ogni mese con le ore; mesi buoni nell'accento con ✓; il numero è il periodo («settembre – dicembre»). Proposta da approvare: mese buono = almeno il 60 % del mese migliore e non meno della durata minima.
- **Crea**: nome oggetto + ottica + camera; schema suggerito dal tipo in pillole; righe per filtro (ore e minuti, esposizione facoltativa, «mancano circa {n} frame», ×); «Aggiungi» coi filtri adatti, «Tutti i filtri» chiuso con il perché («per camere a colori», «non in questo corredo»). Totale grande; col mosaico «Totale per pannello» e «mosaico di 2 pannelli: 24 h in tutto». Salva spento col perché sotto; doppione al posto di Salva con «Apri il progetto»; progetto iniziato: riga «Aperto da Progetti» in testa e, se cambiano inquadratura, griglia o corredo, la finestra «{durata} già riprese non conterebbero più.» · «Salva lo stesso» / «Annulla».
- Parole nuove da approvare: «Corredo · fino a due insieme», «Centra sull'oggetto», «Cambiati solo per questa ricerca: le Impostazioni restano come sono.», «Non è nel catalogo dell'app. Trovato online:», «Inquadra», «Torna a Progetti», «Spento: il corredo di prova serve solo per guardare…», «Il progetto compare in Progetti e si aggiorna dopo ogni scansione.», il testo sotto la finestra del progetto iniziato.
- Dati simulati: sito Cima Ekar, 30 settembre, adesso 20:05, Luna come nella Dashboard, profilo dell'orizzonte inventato. Coordinate e dimensioni degli oggetti vere.

## Planner, modo «Sistema solare» (18 ottobre 2026, brief di Claude Code, ADR 0023)

Brief. **A cosa serve**: vedere come il corredo inquadra un pianeta, la Luna o il Sole, e per Luna e Sole il mosaico. **Dati**: corpo, data e ora, sito; il corredo del cielo profondo con barlow o riduttore; diametro, scala, campo, rapporto focale e critico, tessere; la prossima opposizione o massima elongazione. **Stati difficili**: corpo sotto l'orizzonte, senza rete, Sole (avvertenza), mosaico su una zona. **La cosa più importante**: il corpo in scala col rettangolo del sensore sopra. **Cosa non c'è**: progetti, salvataggio, file esportati, pillole buono/cattivo.

Nella stessa pagina `pagine/Planner.dc.html` (il selettore in testa cambia modo); il modo sta in `componenti/PlannerSolare.dc.html`, che riceve dal Planner corredo, corredo di prova e sensori. Tweaks: sette stati «sistema solare · …».
- **In alto**, una carta: i nove corpi in un segmentato, −1 g / −1 h / +1 h / +1 g, la data e l'ora («adesso» quando lo è), «Adesso», il sito. Sotto una riga sul cielo: «Alle 20:05 la Luna è sotto l'orizzonte: sorge alle 23:50.» (proposta: la partenza resta «adesso» anche quando il corpo non c'è, e la riga lo dice).
- **Al centro** (8 colonne), il corpo in scala su fondo nero col rettangolo del sensore (nell'accento del modo scuro), rotazione 0–180° come nel cielo profondo, rosa N/E, Centra, − +. Trascinando si sposta il corpo; le tessere restano attaccate al corpo.
- **Luna**: la mappa LROC WAC 100 m in proiezione ortografica (nella tavola un'immagine sola da hips2fits del CDS, `CDS/P/Moon/LROC-WAC-100m`; nell'app Aladin), girata con l'asse della notte, la parte in ombra scurita e il terminatore come linea. Al clic il nome ufficiale in pillola (ventiquattro crateri e mari nella tavola). Mosaico: interruttore, sovrapposizione, «Luna intera» (solo le tessere sulla parte illuminata) o «Una zona» (si trascina un rettangolo). Tessere numerate nell'ordine consigliato: 1 è quella sul terminatore, più piena delle altre. Righe fisse con un segno: le tessere fissate sulla Luna, la rotazione entro 10° (col mosaico), il terminatore per primo.
- **Sole**: «Luce bianca» (SDO) o «Hα» (GONG) in pillole; fascia rossa fissa sopra la carta, senza chiudi. Senza rete o senza immagine: disco grigio in scala e la frase in pillola sulla carta.
- **Pianeti**: disco disegnato in scala come segnaposto della foto (OPAL arriverà), fase per Mercurio e Venere, anelli di Saturno con l'inclinazione della data; al posto del mosaico «Niente mosaico: un pianeta sta sempre nel campo.»; riga «Foto per la scala: l'aspetto della notte cambia.».
- **A destra**: Il corredo (pillole, campi del corredo di prova con la lista dei sensori che apre su Planetario, su Solare col Sole; «Barlow o riduttore» sempre; filtro in pillole per il critico), I numeri (diametro e px, scala con km per pixel per Luna e Sole, campo, «f/15 · critico f/14.5» con «senza filtro (400 nm)», tessere), e la carta dell'evento con «Porta la data lì».
- Crediti sulla carta come da brief; con la Luna anche logo Aladin e «CDS Aladin Sky Atlas, Unistra/CNRS».
- Numeri: scala sotto 1″/px con tre cifre (0.663″/px), sopra con due; rapporto focale intero senza decimali («f/15»), il critico con un decimale. I conti tornano con gli esempi della brief (C9.25 + barlow 1,5× + 2.9 µm: 0.17″/px, f/15, critico f/14.5 e f/8.8 con Hα; C11 + 9.0 µm: 0.663″/px, 17.8′ × 12.2′). Con la Luna del 30 settembre a 371.402 km i km per pixel sono 1.19 (la brief dice 1.24 alla distanza media).
- Parole nuove da approvare: «Centra», «Porta la data lì», «Disco intero», «Niente mosaico: un pianeta sta sempre nel campo.», «La tessera 1 è quella sul terminatore.», «Trascina sulla Luna per disegnare la zona.», «Mappa della Luna non disponibile senza rete», «Immagine del Sole di oggi non arrivata», «sul sensore: entra intero / non entra intero».
- Dati simulati: orbite circolari per diametri e fasi (allineate alle opposizioni della brief; Nettuno 28/9/2027 e la congiunzione di Mercurio inventate), transiti, asse e librazione della Luna, profilo dell'orizzonte. L'indirizzo dell'immagine Hα di GONG nella tavola è da sostituire con quello vero.

## Planner, correzioni dell'utente (18 ottobre 2026)

- **Corredi da elenco**, non più pillole: nel cielo profondo due tendine in testa alla carta, «Corredo» (tratto pieno nell'accento) e «Secondo, a confronto» (tratto bianco tratteggiato, «Nessuno» in testa); nel Sistema solare una tendina sola, e il filtro per il critico anche lui in tendina. La testa della carta sta su una riga.
- **«Filtri di ricerca»** al posto di «Criteri di catalogo» (scelta dell'utente: supera la regola della brief che teneva «filtri» per i filtri ottici). «Criteri del cielo» resta.
- Oggetto scelto nella lista: cornice nell'accento.
- Sistema solare: **barlow o riduttore parte da 1×** a ogni apertura (la tavola di Giove resta a 1,5× per l'esempio della brief).
- Sistema solare: **Il momento migliore**, prima carta della colonna, nel tono protagonista: l'ora col seeing migliore peggiorato dalla massa d'aria nelle prossime 24 ore (Sole sopra 15° di giorno; pianeti e Luna sopra 20° fuori dalla luce del giorno), pillola «seeing 1.6″», la frase («Stanotte alle 07:20, a 56° sull'orizzonte…»), 24 barre orarie (più alte = seeing migliore, tratteggio = non adatta, l'ora migliore nell'accento) e «Porta l'ora lì». Oltre i tre giorni di previsione conta solo l'altezza e la carta lo dice. Seeing simulato, come in Dashboard.
- Carta del corpo più bassa (460); «Niente mosaico» diventa una riga sotto, accanto a «Foto per la scala».
- Da chiedere a Claude Code: le sigle che restano (l'utente le farà rivedere lì).

- **Curva d'altezza nel Sistema solare** (18 ottobre 2026, richiesta dell'utente), sotto Rotazione e Mosaico: pianeti e Luna dalle 18 alle 08, Sole dalle 05 alle 19. Fasce del crepuscolo dal Sole, linea dell'altezza minima (20°, Sole 15°), tratto spesso dove il corpo è adatto, linea «adesso». Col puntatore linea tratteggiata, punto con alone e riquadro (ora, altezza, seeing, «non adatta»), come Dashboard e Meteo; clic: «porta l'ora lì». Il Sole in #f2a93b (il suo colore fisso), gli altri nell'accento.

## Planner, animazioni e puntatore (18 ottobre 2026, approvate dall'utente)

- **Stanotte (cielo profondo)**: la curva ha il puntatore come in Dashboard e nel Sistema solare (linea tratteggiata, punto con alone, riquadro con ora, altezza dell'oggetto, Luna, orizzonte del sito e «✓ ore utili» o il perché no). Senza puntatore il riquadro sta su «adesso». Niente clic: nel cielo profondo non c'è un'ora da scegliere.
- **Animazioni** (tutte quelle proposte; spente col movimento ridotto). Un tween comune nelle due logiche (`tw`, uscita morbida), senza clipPath ne' transform sull'SVG intero:
  - la carta scivola sul nuovo oggetto (centro e scala, 0,65 s); trascinando niente ritardo; l'immagine nuova si chiede a carta ferma;
  - il campo cresce o si stringe alla misura nuova al cambio di corredo o mosaico (0,45 s); la rotazione segue con 0,18 s;
  - pannelli del mosaico e tessere di Luna e Sole compaiono in fila (40 ms l'uno), le tessere nell'ordine di ripresa;
  - il terminatore e la fase scorrono al cambio di data o ora (0,5 s);
  - le curve d'altezza si disegnano in 0,8 s al cambio di oggetto, corpo o giorno;
  - le barre del periodo migliore crescono una volta;
  - ore utili, totale del progetto, campo, campionamento, diametro e scala salgono al valore nuovo;
  - le righe dei risultati rientrano in fila quando cambiano ricerca o filtri;
  - «Progetto salvato» sale e sfuma al posto del pulsante.
- Sistema solare: tolta la riga sul cielo sotto corpo e data («Alle 16:05 la Luna è sotto l'orizzonte…»): lo dice già la curva d'altezza (utente, 18/10).
- **Planner, cielo profondo** (utente, 18/10): tolta la riga sotto il nome dell'oggetto nella carta (tipo, dimensione, costellazione, magnitudine, coordinate): tipo e dimensione stanno nella riga di Trova, il centro sulla carta. In Stanotte la ripresa delle ore utili dell'oggetto, con le regole della Dashboard (v13): la riga del mattone Ripresa sotto la frase («Banda larga 21:15–23:45 · poi solo banda stretta») e la fascia sotto la curva, piena = banda larga, tratteggiata = solo banda stretta, solo dove l'oggetto è utile.
- **Planner, cielo profondo: ogni dato una volta** (utente, 18/10). Via da Stanotte la frase (buio, «sale fino a», Luna: stanno nella riga di Trova, nella legenda e nella curva), il sito e il nome in testa, «nel buio sopra 30°» sotto il numero (resta nella legenda), la fascia banda larga/stretta (resta la riga Ripresa, con gli orari). Via da Periodo migliore la frase «fino a … in ottobre» (lo dicono le barre). Sulla carta il nome del corredo sul rettangolo solo con due corredi; via «Mosaico 2 × 1» sul rettangolo e il totale accanto all'interruttore (resta la tessera Mosaico). Tessera Campo: sotto la risoluzione in px invece del nome del corredo. Crea: via «3 filtri · corredo» sotto il totale.
- **Planner, cielo profondo: ogni dato una volta sola** (utente, 18/10). Altezza massima, ora e Luna stanno nella riga di Trova (confronto fra oggetti) e nel riquadro della curva; niente frase sotto le ore di Stanotte. Buio solo nella legenda. Stanotte ha in testa la data (sito in barra, oggetto nel titolo della carta). Il campo totale del mosaico solo nei numeri sotto la carta. Legenda del periodo migliore senza l'altezza minima (sta nei criteri del cielo).
- **Sistema solare: ogni dato una volta sola** (utente, 18/10). Data solo in testa (non sulla curva); «adesso» solo sulla linea; corredo solo nella tendina (sotto Campo solo barlow o riduttore); anelli di Saturno solo nella riga sotto la carta; Il momento migliore senza le 24 barre (le ore stanno nella curva) e la frase senza ripetere l'ora.
- **Sistema solare: tre aggiunte** (approvate; superate in parte dalla v21.4). Nei numeri «Video al massimo» per Giove, Saturno e Marte: Tmax = 3600 · periodo · scala / (π · diametro), sfocatura di 1 pixel (Tanga, ALPO); Giove della brief 43 s. Riga «A {alt}° i colori si separano: serve il correttore di dispersione.» per pianeti e Luna sotto 35° (BAA). «Macchia Rossa al meridiano» e «Faccia di Marte» tolti nella v21.4 (idee per dopo nell'ADR).
- **Video al massimo** (utente, 18/10; superato dai giudizi): la tolleranza e' 1 pixel, non Dawes; il numero si arrotonda per difetto (v21.4).

## Planner, i giudizi (18 ottobre 2026, risposta di Claude Code, ADR 0023 «I giudizi»)

Un giudizio per riga, solo dove una fonte fissa il confine; pillola sotto il numero col colore delle misure, la parola e il segno (✓ / !). Nessun giudizio d'insieme. Supera «Nessuna pillola» della brief del Sistema solare.
- **Sistema solare**: Rapporto focale «✓ campionamento pieno» da critico in su, «! sottocampionato» sotto (niente sovracampionato). Video al massimo: Tmax = 3600 · periodo · scala / (π · diametro) (Tanga, ALPO), solo il numero; Giove della brief 43 s. Correttore di dispersione sotto 35° (BAA), riga com'era. Seeing: nessun giudizio.
- **Cielo profondo**: Campionamento «✓ ottimo / ! sottocampionato / ! sovracampionato» come Meteo, fra 1/3 e 1/2 del seeing previsto (2,4″ simulato; tace senza seeing). Campo e Mosaico «entra / non entra nel campo» (asse maggiore contro il lato corto; col mosaico il mosaico intero). Ore utili stanotte accanto al totale di Crea, senza giudizio.
- **Meteo**: solo in Notti; in testa a Stanotte il rimando «Meteo di stanotte ↗».

## Planner, rifiniture (18 ottobre 2026, approvate dall'utente)

- **Sistema solare parte dalla Luna**: si vede con qualsiasi corredo.
- **I numeri nello stesso posto nei due modi**: riquadri sotto la carta (sotto Rotazione e Mosaico), col giudizio in pillola e la riga piccola. Nel Sistema solare non c'è più la carta «I numeri» a destra.
- **Pianeti ingranditi alla partenza**: se il lato corto del campo è più di 12 volte il pianeta, la carta parte sul pianeta (8 diametri) e sulla carta compare «Il campo è 40 volte Giove: lo vedi intero con −»; la scritta sparisce quando il campo si vede intero.
- **Ora migliore sulla curva**: linea tratteggiata nell'accento (nel colore del Sole per il Sole) con l'etichetta «migliore 07:20», voce in legenda. La carta Il momento migliore resta col numero grande, il seeing e «Porta l'ora lì»; la frase c'è solo quando non c'è un momento.
- **Barra di Salva** (cielo profondo): finché la carta Crea non si vede, in basso una barra fissa col nome del progetto, il totale e «Salva il progetto» (spento col suo perché nel suggerimento; «Apri il progetto» col doppione; «✓ In Progetti» dopo il salvataggio). Sparisce quando Crea è sullo schermo, così il totale non compare due volte.
- Da fare: le foto dei pianeti (Hubble OPAL e NASA) vanno chieste a Claude Code coi crediti; tablet e telefono.
- **Sistema solare, Il corredo espanso** (utente, 18/10): sotto la tendina la scheda del corredo (ottica; focale, e con barlow la focale risultante; apertura col potere risolutivo; camera mono o a colori; sensore in px, µm e mm) e il rimando «Attrezzatura ↗». Niente rapporto focale, scala e campo: stanno nei numeri sotto la carta. Col corredo di prova restano i campi da compilare più focale, camera e sensore.

## Planner, nuova disposizione del cielo profondo (18 ottobre 2026, proposta dell'utente)

- **Trova si apre da sinistra**: la carta del cielo prende 8 colonne; in testa alla carta «Trova un oggetto» (pillola piena) apre un pannello di 410 px che scorre da sinistra sopra la pagina velata, con ×; scelto l'oggetto il pannello si chiude e la pagina torna piena. Contenuto del pannello invariato.
- **Il corredo a destra, come nel Sistema solare**: tendine «Corredo» e «Secondo, a confronto», sotto il pulsante «Corredo di prova» (non più una voce della tendina: è un extra). Col corredo di prova le tendine spariscono, il pulsante diventa «← Torna a {corredo}» e sotto si aprono la fascia e i campi. Poi la scheda del corredo (ottica, focale, apertura, camera, sensore); «Attrezzatura ↗» in testa. Sotto, nella stessa colonna, Periodo migliore.
- Stanotte a tutta larghezza, poi Crea. La barra di Salva si nasconde col pannello Trova aperto.
- Periodo migliore nella colonna stretta: sopra le barre solo il numero di ore (′ per i minuti), il ✓ del mese buono dentro la barra.
- Sistema solare: anche lì «Corredo di prova» è un pulsante sotto la tendina, con «← Torna a …».
- **Cielo profondo, una riga in meno** (utente, 18/10): a destra della carta Il corredo e sotto Stanotte (curva, ripresa, legenda); sotto la carta, affiancati, Periodo migliore (4 colonne) e Crea il progetto (8). Nella tabella delle ore l'esposizione è facoltativa senza dirlo in colonna e «circa {n} frame» sta sotto il campo.
- **Sistema solare, niente ingrandimento automatico** (utente, 18/10): annullato l'ingrandimento sui pianeti alla partenza e la scritta «Il campo è … volte»; si parte sempre col campo intero in scala vera. La Luna resta il corpo di partenza.
- Stanotte nella colonna stretta: il riquadro della curva compare solo col puntatore (fermo su «adesso» copriva mezza curva); linea e punto restano su «adesso».
- **Crea più bassa e riepilogo** (utente, 18/10): righe dei filtri a 4 px e campi a 30 px; barre del periodo migliore alte 112 px fisse. Sotto il totale il riepilogo di ciò che si crea, una riga per filtro: «L 6 h · 180 × 120 s» (col mosaico anche «in tutto»); i frame stanno solo qui, non più nella tabella. Esposizioni proposte e cambiabili: 300 s per banda stretta e multibanda, 120 s per il resto (proposta da approvare).
- **Trova rivista** (18/10): Criteri del cielo in una riga («Criteri del cielo · sopra 30° per 1 h · Luna a 40°», «Cambia» la apre, con Ripristina accanto alla nota); campo di ricerca e filtri non si schiacciano quando si aprono; «ore utili stanotte» una volta sola in testa alla lista, non su ogni riga.
- **Corredo di prova anche sulla carta**: rettangolo a puntini con l'etichetta «Corredo di prova · solo per guardare».
- **Barra di Salva solo dopo una scelta** (oggetto, corredo, rotazione, mosaico, trascinamento), non all'arrivo nella pagina.

## Trova centrata e direzione (18 ottobre 2026, proposta dell'utente)

- **Trova è una finestra centrata** (800 px, dall'alto), aperta da «Trova un oggetto»; il cursore è già nel campo. Sotto il campo una riga di pillole: criteri del cielo («sopra 30° · 1 h · Luna 40°»), Direzione, Tipo, Catalogo, Altri filtri; piena = cambiata, ognuna apre il suo riquadro sotto, la lista resta in vista. «Togli i filtri» quando ce n'è almeno uno.
- **Direzione** (idea dell'utente, come i siti di pianificazione): rosa di 8 settori (N, NE, E, SE, S, SO, O, NO), più d'uno insieme. Le ore utili contano solo quando l'oggetto è in quei settori sopra l'altezza minima; il conto lo dice («ore contate solo verso N, NE»). Stato nei Tweaks «ricerca per direzione» (N e NE, 2 h).
- **Riga del risultato**: nome, nome comune, «◉ progetto»; tipo e dimensione; una curva piccola della notte (18–08, buio velato, altezza minima a puntini, tratto spesso = ore utili, linea su adesso; col puntatore ora, altezza e direzione); ore utili come numero. Tolti «sale fino a …» e «Luna 77°»: resta «· Luna a 25°» solo se è più vicina del criterio.
- In testa «PROGETTI IN CORSO», poi «CATALOGO»; con un nome scritto, una lista sola. Ordine del catalogo.
- Tastiera: ↑ ↓, Invio inquadra, Esc chiude (scritto in fondo alla finestra).
- **Sistema solare, Campo**: «✓ entra nel campo» / «! non entra nel campo» (diametro contro il lato corto); per Luna e Sole senza mosaico anche «→ mosaico di {n} tessere», con lo stesso conto del mosaico (v21.4). C11 + 9.0 µm sulla Luna del 30/9 (371.402 km, 32.2′): disco intero 3 × 4 = 12 tessere; la parte illuminata (62 %) ne prende 6, ed e' il numero mostrato. Il 6 della brief valeva per il disco intero a distanza media (31.1′).
- **Stanotte, ripresa come in Dashboard** (utente, 18/10): tolta la riga «Banda larga 21:15–… · poi solo banda stretta»; tornano le barre orizzontali sotto la curva (piena = banda larga, tratteggiata = solo banda stretta), con le due voci in legenda.
- Trova (18/10): riga scelta con lo sfondo nell'accento tenue; curva piccola alta 44 px con 0° e altezza minima segnati; «Nessun oggetto con questi filtri» col perché e «Togli i filtri»; Costellazione a tendina con le 88 costellazioni in italiano (in Altri filtri, con AR fino a). La carta del cielo prende l'altezza che avanza accanto alla colonna destra (almeno 520 px).
- **Luminosità superficiale** (utente, 18/10): nella riga del risultato «· 22,4 mag/″²» e in Altri filtri «Luminosità superficiale fino a (mag/″²)». Media sull'ellisse: m + 2,5 log10(π/4 · a · b · 3600), a e b in primi. Oggetti senza magnitudine esclusi quando il filtro è attivo. Per Claude Code: i valori del catalogo dell'app vanno calcolati o presi dalla fonte del catalogo.

## Planner sul telefono (18 ottobre 2026; il tablet resta per l'ultima release)

Stessa pagina, `formato` nei Tweaks (automatico sotto 700 px; per provarlo anche `?formato=telefono`). Telaio del telefono con la barra in basso. Una colonna, nell'ordine: Planner e i due modi a tutta larghezza; oggetto e «Trova un oggetto» a tutta larghezza; la carta alta 380 (trascinabile col dito, «Centra» diventa ◎); Rotazione e Mosaico uno sotto l'altro; i numeri a due per riga, coi giudizi che vanno a capo; Il corredo; Stanotte; Periodo migliore; Crea (tabella delle ore più stretta, riepilogo sotto). Barra di Salva a tutta larghezza. Trova a schermo intero, curva piccola da 112 px, niente scorciatoie da tastiera. Sistema solare: corpi in una riga che scorre, carta alta 380, colonna destra sotto. Il riquadro delle curve compare al tocco come in Dashboard.
- Telefono: tutti i bersagli a 44 px (pulsanti della carta, passi della data, Adesso, campi numerici, ×, interruttore del mosaico, cursore della rotazione, «Attrezzatura ↗», «Meteo di stanotte ↗»).
- **Telefono, giro 2** (utente, 18/10): Il corredo subito sotto la carta (dentro la sua carta, su fondo secondario), poi il resto, nei due modi; i due modi del Planner come due pillole separate a metà larghezza, con un segno (✦ cielo profondo, ☉ sistema solare); Trova dentro lo schermo del telefono anche nell'anteprima (il telaio del telefono fa da riferimento per ciò che è fisso: vale per tutte le pagine); nei risultati il progetto è solo «◉». Sistema solare: data e «Adesso» su una riga, i quattro passi sotto a tutta larghezza; il sito resta solo in barra. Sulla carta del cielo niente parola «Mappa» (resta il nome della mappa).
- **Telefono, giro 3** (approvato dall'utente, 18/10): barra in basso «Crea ↓» che porta alle ore (Salva sta in Crea); sulla carta l'icona delle mappe apre un foglio dal basso e la rotazione è un cursore sottile in fondo alla carta («↻ 35°»), il riquadro Rotazione sotto resta solo sul desktop; ⤢ apre la carta a schermo intero (⤡ per uscire), pizzico per lo zoom; in Crea una riga per filtro con − e + a mezz'ora e l'esposizione accanto, senza testata; Sistema solare: i nove corpi come icone tonde coi simboli (☿ ♀ ♂ ♃ ♄ ⛢ ♆ ☾ ☉) nei colori fissi dei pianeti, 5 + 4.
- **Telefono, prima parte rifatta** (utente, 18/10: «slegata dalle altre pagine»): niente titolo «Planner» né pillole grandi; come le altre pagine del telefono si parte da una carta. In testa alla carta il selettore piccolo dei modi (PillolaScelta segmentato, come le viste della Dashboard), sotto una riga di ricerca su fondo secondario con l'oggetto («M 31 Galassia di Andromeda») e la lente: toccandola si apre Trova. Sistema solare: stesso selettore, poi «Corpo» a tendina (Luna per prima), la data; via le icone dei corpi e il nome grande ripetuto sulla carta del corpo. Crea sul telefono: una riga per filtro (sigla · − 2 h + · esposizione), − diventa × a mezz'ora per togliere il filtro.

## Planner sul telefono: tre forme a confronto (18 ottobre 2026)

L'utente: sul telefono il Planner è una pagina attiva, non da leggere; troppo scorrere per arrivare al piano. Tavola `pagine/Planner telefono, varianti.dc.html` (1a, 1b, 1c), costruita sul Planner vero (prop `variante` A/B/C, solo telefono e cielo profondo; il Sistema solare seguirà la forma scelta):
- **1a Carta fissa e passi**: selettore dei modi, una riga di chip che riassume e porta al passo (oggetto, ottica, giudizio del campo, del campionamento, ore stanotte, ore di progetto), carta da 220, poi un foglio coi passi Oggetto · Corredo · Inquadra · Ore · Salva e «Avanti».
- **1b Carta grande e foglio che sale**: carta a tutta altezza; foglio con tre altezze (maniglia): chiuso mostra modi, oggetto e chip; aperto i passi.
- **1c Il piano in una carta**: cinque righe (Oggetto, Corredo, Inquadratura, Stanotte, Ore) col loro giudizio; toccando una riga la scelta si apre in un foglio dal basso con «Fatto»; sotto la carta da 300 e Salva.
- **Scelta: 1b** (utente, 18/10): carta grande e foglio che sale; diventa il telefono del Planner (`variante` vuota = B; A e C restano solo nella tavola). Foglio chiuso (206 px) più piccolo: selettore dei modi compatto (40 px, due voci), riga dell'oggetto (44 px, lente), tre caselle Corredo · Campo · Stanotte che portano al passo; via i chip lunghi («12 h di progetto»). Aperto: passi in un segmentato (Oggetto · Corredo · Inquadra · Ore · Salva).
- **Sistema solare sul telefono nella stessa forma**: carta del corpo a tutta altezza; foglio chiuso con modi, «Corpo» a tendina, la fascia del Sole quando serve, caselle Corredo · Campo (entra / non entra / n tessere) · Migliore (ora); passi Corpo · Corredo · Inquadra · Quando (Corpo: fase, immagine del Sole, opposizione; Corredo: scheda e numeri; Inquadra: rotazione, mosaico e righe; Quando: data, momento migliore, curva). Niente Salva.
- **1b promossa** (utente, 18/10): è il Planner del telefono, nei due modi. Tolte dal Planner le forme A e C e la prop `variante`; cancellata la tavola `Planner telefono, varianti`.
- Telefono, Sole (utente, 18/10): «Luce bianca · Hα» sta sulla carta, in alto a sinistra, sempre a portata (non più nel passo Corpo).
- Rifiniture finali del telefono (18/10): i due modi senza segni (☉ non si vedeva in tutti i caratteri); cambio di passo nel foglio con una dissolvenza breve (220 ms, spenta col movimento ridotto). Controllati modo chiaro e accenti corallo e turchese su desktop e telefono: la carta del cielo resta scura in tutti i temi (è il cielo), i giudizi tengono i colori fissi.
- Ultime rifiniture del telefono (18/10): la maniglia del foglio si trascina (su e giù di un'altezza, due se il gesto è lungo; il tocco cambia altezza come prima); nel passo Salva un pallino nell'accento quando il piano è pronto da salvare; nel Sistema solare la casella «Migliore →» porta subito all'ora migliore e apre Quando. Rotazione del Sistema solare sulla carta solo col Mosaico acceso (è lì che conta, entro 10°): «↻ 0°» in fondo alla carta, come nel cielo profondo; senza mosaico resta nel passo Inquadra.
- **Mosaico sulla carta, telefono** (utente, 18/10): «▦ Mosaico» sulla carta lo accende; acceso diventa una riga sopra la rotazione con ▦ ✕ (spegne), colonne − n + e righe − n + (cielo profondo), oppure «Luna intera | Una zona» e il numero di tessere (Luna e Sole; la zona si disegna trascinando sulla carta). La sovrapposizione resta nel passo Inquadra. RA/Dec sale sopra la riga quando il mosaico è acceso.
- Telefono, cielo profondo (utente, 18/10): il centro della vista sta a metà dello spazio libero fra i comandi in alto e quelli in basso (più su col mosaico acceso), così il centro del campo non finisce sotto i pulsanti. Nel passo Inquadra resta solo «Sovrapposizione dei pannelli» col campo totale; colonne e righe si cambiano sulla carta.
- Telefono, Sistema solare (utente, 18/10): come nel cielo profondo, il centro della vista sta nello spazio libero fra i comandi (più su col mosaico); rosa N/E in alto a destra sotto i pulsanti (a sinistra copriva il nome del corredo); passo Inquadra: rotazione (senza mosaico) o «Sovrapposizione delle tessere» (col mosaico), più le righe.
- Cielo profondo (utente, 18/10): il nome del corredo sta sempre sopra il rettangolo del campo, allineato al bordo («Askar 103APO · ASI2600MM Pro»; col mosaico «2 × 1 · …»), non solo con due corredi.
- **I due Planner del telefono allineati** (utente, 18/10). Stessa carta: in alto a sinistra la mappa (cielo) o Luce bianca · Hα (Sole), in alto a destra ◎ − +, rosa N/E sotto; in basso, sempre, la barra «↻ °» della rotazione e sopra «▦ Mosaico» o la riga del mosaico; tolto ⤢ (la carta è già grande). Stesso foglio chiuso: selettore dei modi, la riga di ciò che si guarda (oggetto con la lente, corpo a tendina), tre caselle Corredo · Campo · Stanotte/Migliore. Stessi passi nello stesso ordine: Corredo · Inquadra · Stanotte · Ore · Salva (cielo) e Corredo · Inquadra · Quando (Sistema solare; fase e opposizione stanno in Quando). Colori del tema su ciò che è scelto: modi, passi, Luce bianca · Hα e Luna intera · Una zona nell'accento (pieno + testo sull'accento).
- Telefono, passo Stanotte (utente, 18/10): sotto la curva tornano le barre del Periodo migliore (12 mesi, ✓ nei mesi buoni, alte 84 px) col periodo accanto al titolo, al posto della sola riga di testo.


## v21.4 · Planner, correzioni di Claude Code (19 ottobre 2026, ADR 0023 «I giudizi»)

Revisione v21.3 di Claude Code; le parole fra «» sono proposte, da approvare con Marco. Supera, dove dice, le voci sopra.

### Le soglie stanno in Impostazioni (Marco)
- Sezione «Planner» nelle Impostazioni, sei righe col valore di partenza e la fonte: altezza minima cielo profondo 30° (massa d'aria 2); durata minima 1 h; distanza dalla Luna 40°; mese buono 3 h utili il 15 del mese; altezza minima di pianeti, Luna e Sole 30° (massa d'aria 2); correttore di dispersione sotto 35° (BAA). Nel Planner si cambiano per una ricerca, senza salvarle.
- Dove il Planner usa una soglia, la riga piccola dice «da Impostazioni» (legende delle curve, riga del correttore, legenda del periodo migliore). Fisse perché fisica: rapporto critico, campionamento, video al massimo, campo che entra.
- Sistema solare: via 20° e 15°; 30° per tutti i corpi. Supera «Sole sopra 15°, pianeti e Luna sopra 20°».

### Il momento migliore
- Pillola verde «✓ migliore» (non più gialla); accanto il seeing col giudizio di Meteo (sotto 2″ buono, 2-4″ incerto, oltre non adatto). Se l'ora migliore ha seeing cattivo lo dice il seeing.
- Mercurio e Venere anche di giorno (Marco); il giorno viene dall'altezza del Sole, non dalle ore fisse. Col Sole sopra l'orizzonte: «A {n}° dal Sole: non cercarlo mai a occhio o col cercatore.» (proposta; BAA, guida di Mercurio).

### I consigli (Marco)
Sotto un giudizio una riga tenue, senza pillola e senza colore; senza giudizio niente consiglio. I numeri li manda l'app.
- Pianeti, «! sottocampionato»: «Per il critico: barlow {x}×. Il fattore cresce allontanando il sensore dalla barlow.» ({x} = critico / rapporto del corredo, una cifra decimale).
- Video al massimo: «Con la derotazione il tempo in tutto arriva a 3-4 volte; il singolo video no.»
- Pianeti, sempre sotto i numeri: «Pose sotto 30 ms, almeno 30 fotogrammi al secondo; area di ripresa stretta attorno al disco.»
- Pianeti sotto 35° o seeing da 2″: «Un filtro IR-pass soffre meno il seeing.»
- Cielo profondo, «! sovracampionato»: «Bin 2 × 2 (anche in elaborazione) o un riduttore: con bin 2 × 2, {s}″/px.»; «! sottocampionato»: «Dithering e drizzle, con molti frame; oppure pixel fino a {p} µm con questa focale.»

### Cielo profondo
- **Entra nel campo, geometrico**: entra se l'ellisse dell'oggetto (asse maggiore, asse minore, angolo di posizione del catalogo) sta tutta nel rettangolo ruotato del campo o del mosaico, contando anche dove sta l'oggetto nel campo. Senza angolo di posizione, asse maggiore contro il lato corto. Il giudizio cambia girando la rotazione. Rotazione = direzione del lato corto dal Nord verso Est: M 31 (angolo 35°) sta nel mosaico 2 × 1 (3.46° × 1.29°) a 125°, e la tavola parte da lì (prima 35°, che lo metteva di traverso). Angoli nella tavola: M 31 35°, M 33 23°, NGC 891 22°, NGC 7331 171°, NGC 253 52°.
- **Crea parte vuota** (Marco): i filtri dello schema in lista, ore a 0, esposizione vuota. Tolte le ore suggerite e le esposizioni 300 / 120 s (nessuna fonte). Riepilogo dei frame solo per i filtri con l'esposizione. Supera «Crea più bassa e riepilogo» per le esposizioni proposte.
- **Camera a colori**: schemi «Senza filtro» e «Multibanda» (niente SHO e HOO: servono filtri a banda singola).
- **Mese buono**: ✓ con almeno 3 ore utili il 15 del mese (Marco). Legenda: «mese buono: da 3 ore, cambia in Impostazioni». Via il 60 % del mese migliore.
- **Senza seeing**: stato nei Tweaks «nessuna chiave Meteoblue». Il campionamento mostra solo il numero e «Giudizio col seeing previsto: serve la chiave Meteoblue.» (proposta). Il seeing del giudizio è la mediana delle ore utili dell'oggetto (simulato).
- PanSTARRS: `CDS/P/PanSTARRS/DR1/color-i-r-g` (ADR 0023).
- Finestra del progetto iniziato: solo «{durata} già riprese non conterebbero più.».
- Telefono, foglio chiuso: nella casella Corredo, sotto il nome, il giudizio del campionamento («✓ ottimo» / «! sottocampionato»).
- RA / Dec ovunque (anche in Altri filtri, prima «AR»). Numeri col punto anche in campo, mosaico, rapporto focale, luminosità superficiale (regola v16.1).
- Pulizia: tolto dalla pagina il codice delle forme A e C del telefono e i pezzi del telefono che la forma B non usa.
- Nota per la tavola: la copertura NSNS «Dec > −16» è una semplificazione; nell'app la dà il MOC della mappa.

### Sistema solare
- Una domanda, un giudizio: via la riga sotto «Diametro apparente»; resta il giudizio del Campo (lato corto).
- Tessere stimate = tessere del mosaico: stesso conto (Luna: solo la parte illuminata), col bordo esatto del disco; sovrapposizione vuota 20 % in tutti e due.
- Video al massimo per difetto: «2 min 30 s», mai arrotondato in su.
- Tolti «attività moderata · 112 macchie», «Macchia Rossa al meridiano», «Faccia di Marte» (non decisi; idee per dopo nell'ADR).
- Col filtro Hα, riga fissa «Hα solo con un telescopio o un filtro Hα dedicato.» (proposta).
- Periodi di rotazione dalla NASA Planetary Fact Sheet: Giove 9.925 h, Saturno 10.656 h, Marte 24.623 h.
- Telefono: pulsante del sensore nel corredo di prova a 44 px (anche i campi del corredo di prova nel cielo profondo).

## v21.4.1 · Planner, ultimi ritocchi (19 ottobre 2026, Claude Code)

- Il momento migliore: un seeing solo. Pillola e numero mostrano il seeing peggiorato dalla massa d'aria, quello che ha scelto l'ora, giudicato come in Meteo.
- Video al massimo senza tetto: via «oltre 10 min» (nessuna fonte); sempre il numero vero, per difetto («14 min»).
- «Hα solo con un telescopio o un filtro Hα dedicato.» solo col Sole: è un avviso di sicurezza solare.
- Pulizia: tolta la funzione `chip` del telefono (non la usava nessuno).
- Parola nuova da approvare con Marco: «nessuna ora utile: niente seeing per il giudizio».

## v22 · Trova, quattro aggiunte (19 ottobre 2026, Claude Code, scelte di Marco; ADR 0023 «Trova, in più»)

Dal confronto con gli altri pianificatori. Le parole fra «» sono proposte, da approvare con Marco.
- **Già ripreso**: nella riga del risultato «12 h in archivio» quando l'archivio ha frame dell'oggetto. Pillola «Archivio» con «Tutti» · «Mai ripresi» · «Già ripresi» (piena quando non è «Tutti»). Archivio vuoto: pillola spenta «Archivio vuoto» (col perché al passaggio). Ore in archivio simulate.
- **Dimensione da … fino a (′)** in Altri filtri.
- **Entra nel campo**: pillola a interruttore «Entra nel campo di {ottica}» (col mosaico «del mosaico», col corredo di prova «del corredo di prova»): solo gli oggetti che ci stanno, regola dell'ellisse ruotata, oggetto al centro, rotazione della carta. Senza campo la pillola è spenta: «Spento: scegli un corredo, serve il suo campo.». Senza risultati: «Nessun oggetto entra in questo campo» · «Togli il filtro».
- **Ordina**, in testa alla lista accanto al conto: Catalogo (partenza) · Dimensione · Magnitudine · Luminosità superficiale · Ora del transito. Mai per ore utili. Con «Ora del transito» la riga dice «transita alle 01:15» (ordine dalla sera).
- Tweaks: «archivio vuoto», «entra nel campo, nessuno» (nebulose a emissione da 100′ con l'Askar 103APO).
- Telefono: le pillole stanno in una riga che scorre; «Ordina: {scelta} ▾» apre un foglio dal basso (righe da 48 px).
- «Togli i filtri» toglie anche Archivio ed Entra nel campo.

## v23 · Eventi, Macchia Rossa e Marte (19 ottobre 2026, Claude Code, decisioni di Marco; ADR 0023 «Eventi e Macchia Rossa»)

Le parole fra «» sono proposte, da approvare con Marco. Numeri ed eventi li manda l'app: nella tavola sono simulati.

### Trova, tre ritocchi
- Il perché di una pillola spenta sta in una riga sotto le pillole (anche sul telefono), non solo al passaggio.
- «Entra nel campo di {corredo}» col nome intero del corredo (il campo dipende anche dalla camera).
- Due corredi: l'oggetto deve entrare in tutti e due; la pillola li nomina («di {corredo 1} e di {corredo 2}»).
- Da approvare: «Nessun frame in archivio: si riempie con la scansione.», «Spento: scegli un corredo, serve il suo campo.».

### Sistema solare: Giove e Marte
- **Macchia Rossa** (solo Giove), sotto i numeri: «Macchia Rossa al meridiano: 19:33 · 05:29» (i passaggi nelle ore della curva). Sulla curva ogni passaggio è una fascia di 50 minuti prima e dopo (Sky & Telescope), con l'ora in basso; il tocco porta l'ora lì (almeno 44 px). Voce in legenda.
- Riga piccola: «Macchia Rossa a 91° (Sistema II) il 1/6/2026, deriva 1.75° al mese: cambia in Impostazioni.»: settima riga della sezione «Planner» delle Impostazioni (longitudine, data, deriva).
- Senza passaggi con Giove alto: «Nessun passaggio con Giove sopra 30°.». Tweaks: «sistema solare · Giove, nessun passaggio» (3 ottobre, 02:59 a 15°).
- Il disco di Giove gira col meridiano centrale (Sistema II) dell'ora scelta e porta la Macchia dove sta. Nella tavola il disco è disegnato dall'app (bande e Macchia): la mappa OPAL non è ancora in pagina, il credito lo dice.
- **Marte**: «Meridiano centrale 215°» sotto i numeri; il disco è la mappa Viking MDIM 2.1 (NASA/USGS, pubblico dominio, da Wikimedia Commons), cilindrica, spostata al meridiano centrale, che gira con l'ora. Credito sulla carta. Nella tavola lo spostamento è lineare (niente proiezione ortografica vera): nell'app la proiezione la fa la mappa. Tweaks: «sistema solare · Marte».
- Passaggi della Macchia e meridiani simulati (riferimento: passaggio il 1/10 alle 05:29).

### Terzo modo «Eventi»
Componente `componenti/PlannerEventi`, stesso selettore dei modi (Cielo profondo · Sistema solare · Eventi). Eventi del sito attivo per data, dal più vicino; filtro «Tutti · ISS · Eclissi · Occultazioni»; periodo a tendina «{n} giorni» (30 · 90 · 365 · 1100 nella tavola; la partenza la decide il backend). Il corredo resta e serve al campo sulla carta («Campo di …»).
- **Desktop**: lista a sinistra (5 colonne), l'evento scelto a destra (7). **Telefono**: lista a tutta larghezza; la riga toccata sale in un foglio dal basso con ×.
- **ISS sul Sole o sulla Luna**: riga con data, ora al secondo, «sul Sole» / «sulla Luna», durata. Aperta: disco (Sole del giorno o Luna con fase) col campo del corredo e la traccia della ISS in scala (ISS circa 50″); numeri: diametro della ISS, distanza, larghezza della striscia, altezza del Sole o della Luna. Giudizio geometrico: «✓ sei nella striscia» / «! fuori di {n} km dalla linea centrale», con lo schema (striscia, linea centrale, punto del sito; niente mappa geografica). Riga: «Orbita del 30/9: la previsione si rifà a ogni orbita nuova.» (più «Lontano nel tempo l'ora si sposta.»). Sul Sole l'avvertenza del filtro.
- **Eclissi**: riga con data, tipo, grandezza; aperta: i contatti con ora e altezza («sotto l'orizzonte» al posto dell'ora; «! basso» sotto 30°), il disco al massimo col campo. «Eclipse Predictions by Fred Espenak, NASA's GSFC». Nella tavola: parziale di Sole 2/8/2027 (0.81) e totale di Luna 31/12/2028 (1.25), contatti simulati.
- **Occultazione lunare di un pianeta**: riga con data, pianeta, «sparisce alle 21:14 · ricompare alle 22:31»; aperta: Luna con fase e pianeta in scala, i due punti del lembo (scuro, chiaro) scritti, altezza della Luna.
- Stati nei Tweaks: «eventi», «eventi · ISS fuori dalla striscia», «eventi · occultazione», «eventi · eclissi di Luna», «eventi · nessun evento» («Nessun evento visibile da {sito} nei prossimi {n} giorni.»), «eventi · orbita ISS non scaricata» (le altre righe restano; «Orbita della ISS non scaricata: riprova.» con Riprova), «eventi · senza sito» («Serve un sito: gli eventi dipendono da dove sei.»).
- Parole nuove da approvare: «Campo di», «Da {sito} passa accanto al disco», «Nessun evento di questo tipo da {sito} nei prossimi {n} giorni.», «Eventi simulati per la tavola · ore del sito», «ombra della Terra», «al massimo, {ora}».

## v23.1 · Eventi, due ritocchi (19 ottobre 2026, Claude Code)

- La riga dell'orbita della ISS si mostra sempre, intera, per ogni transito: «Orbita del {data}: la previsione si rifà a ogni orbita nuova. Lontano nel tempo l'ora si sposta.» (via la soglia dei 2 giorni, senza fonte).
- Periodo della lista (30 · 90 · 365 · 1100 giorni): numeri provvisori, lo decide il backend; nella tavola la nota «provvisorio: lo decide il backend» accanto alla tendina.
- **Approvati da Marco** (19/10/2026): «transiti della ISS, eclissi e occultazioni visibili dal sito», «Macchia Rossa al meridiano: nessun passaggio in queste ore», «Viking MDIM 2.1: NASA/USGS, pubblico dominio», «visibili da {sito}, dal più vicino», «serve un sito», «Sito mancante» · «Aggiungi sito», «Nessun evento di questo tipo da {sito} nei prossimi {n} giorni.», «Riprova», «Campo di», «Da {sito} passa accanto al disco», «ombra della Terra».
- Per il porting, non da rifare nella tavola: Giove nell'app è la mappa OPAL girata (qui disco piatto); la mappa di Marte si prende da USGS e si proietta sulla sfera (qui Wikimedia Commons, spostata in piano).

## v23.2 · Planner, testi approvati (19 ottobre 2026, Marco; Claude Code)

Il Planner è chiuso nel disegno. Approvati da Marco, restano così:
- **Trova**: «Nessun frame in archivio: si riempie con la scansione.», «Spento: scegli un corredo, serve il suo campo.»
- **Giudizi**: «Giudizio col seeing previsto: serve la chiave Meteoblue.», «nessuna ora utile: niente seeing per il giudizio»
- **Sicurezza**: «A {n}° dal Sole: non cercarlo mai a occhio o col cercatore.», «Hα solo con un telescopio o un filtro Hα dedicato.»
- **Consigli**: «Per il critico: barlow {x}×. Il fattore cresce allontanando il sensore dalla barlow.», «Con la derotazione il tempo in tutto arriva a 3-4 volte; il singolo video no.», «Pose sotto 30 ms, almeno 30 fotogrammi al secondo; area di ripresa stretta attorno al disco.», «Un filtro IR-pass soffre meno il seeing.», «Bin 2 × 2 (anche in elaborazione) o un riduttore: con bin 2 × 2, {s}″/px.», «Dithering e drizzle, con molti frame; oppure pixel fino a {p} µm con questa focale.»
- **Eventi**: «al massimo, {ora}» sotto il disco dell'eclisse.
- «Eventi simulati per la tavola · ore del sito» resta solo nella tavola: nell'app non c'è.


## v24 · L'orizzonte del sito, la pagina Progetti, i collegamenti della Dashboard (19 ottobre 2026, brief di Claude Code, ADR 0023)

### L'orizzonte del sito
Brief. **A cosa serve**: contare le altezze col cielo vero del sito, case e alberi compresi. **Dati**: il file di N.I.N.A. (coppie «azimut altezza» in gradi, una per riga), uno per sito; l'altezza minima delle Impostazioni (30°). **Stati difficili**: nessun orizzonte, file non leggibile. **La cosa piu' importante**: dove la sagoma supera l'altezza minima conta la sagoma. **Cosa non c'e'**: Meteo (cielo e Luna non dipendono dagli ostacoli).
- **Impostazioni**: pagina nuova `pagine/Impostazioni.dc.html`, per ora solo il sito (pillole Cima Ekar · Casa). Riga «Orizzonte»: «Importa file»; col file «Sostituisci» · «Togli». Riga piccola sotto: «File dell'orizzonte di N.I.N.A.: azimut e altezza in gradi, una coppia per riga.» Il file si legge davvero (Importa apre la scelta del file).
- **Il disegno a 360°**: cerchio visto dall'alto, N in alto, E a destra; bordo = 0°, centro = zenit. Sagoma piena, linea tratteggiata dei 30°, e tratto spesso dove la sagoma supera la linea. Al passaggio (o con le frecce, Maiuscolo 15°): «Est 90°: ostacolo fino a 35°»; sotto i 30° si aggiunge «· conta l'altezza minima» (proposta). Telefono: disegno a tutta larghezza, pillole da 44.
- **Stati** (Tweaks `orizzonte`): importato, nessuno («Nessun orizzonte: conta solo l'altezza minima.»), non leggibile («Il file non si legge: servono almeno due righe azimut altezza.», in ambra col «!»).
- **Planner** (Tweaks `orizzonte`: caricato / nessuno): sulla carta la sagoma al posto della linea piatta (verde, piena; tratteggiata senza file), il cielo coperto velato. Curva di Stanotte, curve piccole di Trova e curva del Sistema solare: la soglia segue l'orizzonte nella direzione dell'oggetto a quell'ora (il piu' alto fra 30° e l'ostacolo); le ore non utili sono tratteggiate. Ore utili, momento migliore, mese buono, Trova contano con la stessa soglia; «utili stanotte · con l'orizzonte di Cima Ekar». Eventi: stessa soglia, nessun disegno nuovo (nell'app).
- Un orizzonte solo per tutta l'app: `ALdati.orizzonte` e `ALdati.leggiOrizzonte` in `componenti/dati.js` (fra due punti l'altezza va per retta). Profilo di Cima Ekar simulato: casa a est fino a 35°, alberi a nord-ovest fino a 32°.

### La pagina Progetti
Brief. **A cosa serve**: seguire ogni progetto fino all'obiettivo. **Dati**: oggetto + ottica + camera, ore fatte e obiettivo per filtro e per pannello, inquadratura, notti, mediane delle misure (ADR 0022). **Stati difficili**: vuoto, obiettivo raggiunto, appena creato, frame senza pannello, eliminazione. **La cosa piu' importante**: l'anello delle ore. **Cosa non c'e'**: planetario e solare, punteggi d'insieme, classifiche, pulsante «aggiorna» (si aggiorna da solo dopo ogni scansione).
- Pagina `pagine/Progetti.dc.html` (Tweaks: stato normale / obiettivo raggiunto / appena creato / elimina / vuoto; formato; tema). Desktop: elenco a sinistra coi quattro gruppi, scheda a destra. Telefono: gruppi come pillole in testa, una colonna; la scheda a pagina intera con «← Progetti».
- **Gruppi**: «In corso» (nella loro stagione), «In attesa» (fuori stagione, «torna a {mese}»; un circumpolare non e' mai in attesa), «Fermi» («fermo da {tempo}», una stagione intera senza frame), «Finiti» (confermati dall'utente). Le note dei gruppi sono proposte.
- **Scheda**: segno e parola del gruppo; nome, nome comune, corredo; miniatura dell'inquadratura (CDS hips2fits, DSS2 colore; rettangolo nell'accento, ruotato; col mosaico la griglia); anello grande con la percentuale e «{fatte} di {obiettivo}»; barre per filtro nelle tinte dei filtri; col mosaico una carta coi pannelli e «{n} frame senza pannello: non risolti.»; «Le notti» (ultima, prossima notte utile «con l'orizzonte di {sito}», o torna / fermo / finito); «Le misure» (FWHM, eccentricita', luminosita' del cielo, con i giudizi di `ALsoglie.misure`; «non giudicabile su questo corredo» dove il limite supera 3″).
- **Azioni**: «Apri nel Planner ↗», «Segna come finito» / «Riapri», «Elimina» → «Il progetto sparisce. I frame restano nell'archivio.» · «Elimina» / «Annulla». Ore raggiunte: «Obiettivo raggiunto. Segnarlo come finito?» · «Segna come finito» (lo propone l'app, lo conferma l'utente).
- Il dialogo «{durata} già riprese non conterebbero più.» resta nel Planner (stato «progetto iniziato»); «Torna a Progetti» porta alla scheda.
- Vuoto: «Nessun progetto ancora.» · «Apri il Planner». Appena creato (il Salva di Crea porta qui): la scheda nuova aperta, la riga con l'anello nell'accento, «Le misure arrivano con i primi frame.» (proposta).
- Indirizzo: `Progetti.dc.html?p={id}` apre la scheda.

### Dashboard
- La carta «Progetti in corso» resta com'e'. Il ↗ apre Progetti; ogni riga apre Progetti sulla sua scheda. Anelli e ore sono gli stessi numeri della scheda. «Progetti» nella barra in alto porta alla pagina.

### Simulato
- Profilo dell'orizzonte; progetti In attesa, Fermi e Finiti; notti, mediane delle misure, Bortle dei siti (Cima Ekar 4, Casa 6).


## v24.1 · Correzioni e parole (19 ottobre 2026, Claude Code, decisioni di Marco)

- **Il Salva di Crea porta alla scheda**: «Apri in Progetti» e «✓ In Progetti» vanno a `Progetti.dc.html?p={id}&nuovo=1` con oggetto, corredo, inquadratura, filtri e ore visibili nell'indirizzo; Progetti apre la scheda appena nata (come lo stato «appena creato»). Da un progetto iniziato si torna alla sua scheda; «Apri il progetto» del doppione va alla scheda che c'e' gia'.
- **Nome nell'elenco di Progetti**: oggetto + ottica + camera, come la scheda.
- **Impostazioni, sezione «Planner»**: sette righe con partenza e fonte (ADR 0023): altezza minima del cielo profondo 30° (massa d'aria 2); durata minima sopra l'altezza 1 h; distanza dalla Luna 40°; mese buono 3 ore visibili il 15 del mese; altezza minima di pianeti, Luna e Sole 30° (massa d'aria 2); correttore di dispersione sotto 35° (BAA); Macchia Rossa 91° (Sistema II) al 1/6/2026, deriva 1.75° al mese (Sky & Telescope, da JUPOS). Esce la riga «per tutti i corpi · massa d'aria 2». Il disegno a 360° mostra la linea del cielo profondo («altezza minima, cielo profondo: 30°»); nel Sistema solare conta la quinta.
- **«ore visibili»** (glossario, Marco) in tutto il Planner e in Progetti: ore di buio con l'oggetto sopra l'altezza minima e l'orizzonte. «ore utili» resta del Meteo e della Dashboard (buio con cielo sereno).
- **«mesi buoni»**, non «stagione» (le stagioni saranno delle Statistiche). Gruppi: «nei loro mesi buoni» · «fuori dai mesi buoni» · «mesi buoni passati senza frame» · «segnati come finiti». «Torna buono a {mese}»; «mesi buoni {mesi veri} passati senza frame»; «Nessun progetto nei suoi mesi buoni.»; «Nessun progetto fuori dai mesi buoni.».
- **Testi approvati da Marco**: tutti gli altri testi nuovi della v24.
- **Per il porting**: in Progetti «con l'orizzonte di {sito}» esce solo se il sito ha il file (nella tavola: Cima Ekar si', Casa no). «almeno 3 ore visibili»: il 3 viene dalle Impostazioni.


## v24.2 · Quattro ritocchi (19 ottobre 2026, Claude Code, decisioni di Marco)

- Progetti: «Prossima notte utile» -> «Prossima notte» (etichetta della scheda e riga dell'elenco); la riga sotto dice gia' «{n} h visibili». Senza ore: «nessuna ora visibile».
- Dashboard: la carta dei progetti resta «ore utili» (conta anche il cielo sereno, glossario); nella vista Progetti del grafico, che e' la curva d'altezza, «sopra 30° · tratto spesso = ore visibili».
- Impostazioni, sezione «Planner»: dove non c'e' fonte (durata minima, distanza dalla Luna, mese buono) «nessuna convenzione: scegli tu».
- Testi approvati da Marco: «valori di partenza, con la fonte», «altezza minima, cielo profondo: 30°». «Profilo d'esempio: dati simulati.» resta solo nella tavola: non va nell'app.


## v24.3 · Il vocabolario, in tutte le pagine (19 ottobre 2026, Claude Code, decisioni di Marco)

Controllo sull'uso dei forum italiani (Coelum, astronomia.com, astrofili.org): il pubblico e' esperto, si parla come lui. Glossario dell'app: docs/domini/glossario.md.
- **«setup»**, non «corredo» (ottica + camera, + riduttore). Invariabile: il setup, i setup, due setup, setup di prova. Anche nei nomi degli stati dei Tweaks («setup di prova», «due setup»).
- **«posa»**, non «esposizione», per il tempo di un frame: colonna «Posa» in Crea, «Posa del frame in secondi», «Ore, filtri e pose cambiano senza perdere niente.», «la stessa posa» in Misure. «Pose sotto 30 ms» resta. Il file resta «frame».
- **«Integrazione»** nei titoli, il numero resta in ore: in Crea la colonna «Integrazione» (e «Integrazione per pannello») e il passo «Integrazione» del foglio sul telefono.
- **Planner, criteri di ricerca**: «Altri criteri», «Togli i criteri», «Togli il criterio» (entra nel campo), «Nessun oggetto con questi criteri», «Prova a togliere un criterio…». In Crea «Togli il filtro» resta: li' e' il vetro.
- **Mosaico di Luna e Sole**: «pannelli», non «tessere» («Sovrapposizione dei pannelli», «→ mosaico di n pannelli», «I pannelli sono fissati sulla Luna…», «Il pannello 1 è quello sul terminatore.»), come nel cielo profondo.
- **Schema di Crea per le camere a colori**: «Nessun filtro» al posto di «Senza filtro». «Multibanda» resta; scelto, la riga d'aiuto aggiunge «dual band, tri band, quad band».
- **ADC**: alla prima occorrenza «correttore di dispersione atmosferica (ADC)» (Sistema solare), poi «ADC». Impostazioni: «ADC sotto: 35°» (BAA).
- **Restano in inglese**: seeing, dithering, drizzle, bin, barlow, plate solving, light, flat, dark, bias, frame, FWHM, HFD, SQM, tilt, backfocus.
- Nel codice gli identificatori restano (`corredo`, `corredi`, `tessere`): cambiano solo le parole a schermo.
- **Pagine toccate**: Attrezzatura, Attrezzatura stati, Da confermare, Meteo, Meteo stati, Dashboard stati, Misure dei frame, Notti, Planner, Progetti, Impostazioni, Riepilogo stati; componenti MisureFrame, PlannerSolare, PlannerEventi, Riepilogo, soglie.js.

## v24.4 · Le frasi, in tutte le pagine (19 ottobre 2026, Claude Code, scelte di Marco)

Controllo di tutte le frasi a schermo (italiano, senso per un esperto, glossario). Il tono resta.
- **«Deep sky» ovunque** (modi del Planner, Impostazioni «altezza minima, deep sky»), mai «Cielo profondo».
- **«Criteri»** anche in Archivio e Notti: pulsante e carta delle scelte di ricerca, «Togli i criteri», «con questi criteri». «Filtri» resta solo il gruppo dei vetri.
- **Percentuali attaccate**: «40%», ovunque.
- **«illuminata all'83%»**: articolo calcolato (`AL.al` in tema.js: «all'» davanti a 8, 11, 80-89). Luna, pianeti interni, elongazioni, Eventi, Notti, Meteo.
- **Un apostrofo solo, il dritto** (').
- **Hα**, una grafia sola (non H-alfa, Ha, H-alpha); i nomi dei prodotti restano come li scrive il produttore. «quad band», «tri band».
- **Nome del setup «ottica · camera»**. Numeri col punto (regola v16.1) anche in altitudine (1366 m), eccentricita', seeing, aerosol, distanziali, riduttore, eta' della Luna.
- **Parole**: «Integrazione» (colonne di Archivio e Notti, riepilogo, «Per integrazione», «dalla più lunga»); «mosaico di n pannelli»; «nessun filtro»; «Bit del convertitore» (ADC e' il correttore); «torna buono a»; «foglio», mai «piano»; «Interrompi» la scansione; «siti, tema, cartelle, servizi»; «punto di rugiada»; «nuvole», mai «nubi»; «✕ non adatta» come verdetto; «nessuna ora utile»; «Diventa buona / incerta / non adatta»; «Nessun buio»; «Il seeing richiede una chiave Meteoblue.»; «3 modelli d'accordo su 4»; «domani 15:17»; «fino a 13 km/h»; «Inizia»; «Grandezza» per l'eclisse di Luna; «0 h di 8 h».
- **Credito Copernicus** tutto nella forma della licenza (inglese).
- **Ricerca**: un segnaposto solo, «Cerca oggetto, notte, attrezzatura, sito o pagina».
- **Resta** la carta del Sole in Dashboard e Archivio (ADR 0019).
- **Pagine toccate**: Archivio, Attrezzatura, Attrezzatura stati, Da confermare, Dashboard, Foglio, Impostazioni, Meteo, Misure dei frame, Notti, Planner, Primo avvio, Progetti, Sistema; componenti CardMeteo, Cerca, Filtri, Luna, Menu, MisureFrame, PlannerEventi, PlannerSolare, Riepilogo, Telaio, tema.js (e l'apostrofo in tutte le tavole stati).

## v24.4.1 · Frasi, ultimi ritocchi (19 ottobre 2026, Claude Code, regola SI di Marco)

- **Decimali col punto, sempre**: `AL.virg` non mette piu' la virgola (resta il nome); via i replace('.', ',') di Attrezzatura, Meteo e Sistema; valori d'esempio col punto (eccentricita', massa d'aria, f/5.6, 7.5 mm, 1.25″, 3.76 µm, 44.1 km, 1.2 milioni di anni luce, seeing, aerosol, pioggia, visibilita').
- **Coordinate col punto**: «45.8486 N · 11.5689 E» (Primo avvio, Da confermare), anche negli esempi dei campi.
- **Migliaia**: spazio sottile (U+202F) da 10 000 in su («18 430 frame», «396 200 km»); sotto niente separatore («1204 frame», «1366 m»). Mai il punto. `AL.num` lo fa da solo.
- **Setup «ottica · camera»** anche in Misure dei frame (Askar 103 · ZWO ATR2600M, Newton 200/800 · ZWO ASI533MC Pro).
- **Eclisse di Luna**: «grandezza 1.25» nell'elenco e «Grandezza» nel dettaglio; col Sole «da {sito}» e «Grandezza dal sito».
- **Primo avvio**: «Con una chiave Meteoblue…», «Come ottenere una chiave ↗».
- **Intestazioni di colonna** in minuscolo come le vicine: «integrazione» in Archivio e Notti.
- **Crediti**: «Seeing: meteoblue», minuscolo come chiede il servizio; altrove «Meteoblue».
- **Pagine toccate**: Archivio, Attrezzatura, Da confermare, Dashboard, Foglio, Meteo, Misure dei frame, Notti, Primo avvio, Sistema; componenti Menu, PlannerEventi, dati.js, tema.js.

## v25 · Piano della notte (19 ottobre 2026, brief di Claude Code, ADR 0013 «Il disegno» e 0023)

Brief. **A cosa serve**: decidere cosa si fa una notte, in che ordine, ed esportarlo per N.I.N.A. **Dati**: progetti della postazione alti stanotte, eventi del modo Eventi, fasce del cielo, Luna e ripresa, verdetto del meteo ora per ora, tempo di cambio dalle Impostazioni. **Stati difficili**: conflitti, notte senza buio, senza previsione, senza sito, nessun progetto. **La cosa piu' importante**: la linea del tempo coi blocchi e i conflitti. **Cosa non c'e'**: variabili, esopianeti, NEO, comete, supernove; comandi all'hardware (cupola, tetto, sicurezza restano a N.I.N.A.); punteggi.

Pagina `pagine/Piano della notte.dc.html` (Tweaks: Stato, Formato, Tempo di cambio, Postazioni, modo, accento; anche `?stato=` e `?formato=`).
- **Dove sta**: nel menu Altro, subito dopo il Planner («cosa si fa stanotte, in che ordine»). Il brief dice «in barra accanto a Planner e Progetti», ma il Planner sta in Altro: da confermare con Marco.
- **Testa**: notti in pillole (Stanotte e le sei dopo, come Meteo), postazioni in linguette (montatura · ottica · camera, col numero dei blocchi), sito e verdetto in una riga con «Meteo ↗». Con una postazione sola il nome e' scritto, senza linguette.
- **Cosa si fa stanotte** (4 colonne): progetti della postazione con almeno 1 h sopra 30° nel buio; prima chi si chiude, poi le ore utili, poi le ore mancanti. Riga: nome · ottica · camera, «ore visibili · ore utili», Luna col giudizio della soglia (✓ da 40°, ! sotto), «◷ ultime settimane nei mesi buoni», «mancano» per filtro. Con la banda larga e la Luna che la vieta: filtri a banda larga tenui e «dalle 00:45 solo banda stretta». «nel piano · 20:48–22:33» quando c'e' gia'. Si trascina sulla linea o «Aggiungi» (primo spazio libero sopra 30°, al massimo 2 h).
- **Eventi di stanotte** sotto, col lucchetto; si aggiungono all'ora fissa.
- **La linea del tempo** (8 colonne), da tramonto ad alba: fasce del cielo a gradini sotto tutte le corsie; corsia Luna (curva tratteggiata, fase in testa, sotto la striscia della ripresa: piena banda larga, tratteggiata solo banda stretta); corsia Meteo (striscia coi colori e i segni del verdetto; senza previsione «Previsione non disponibile» tratteggiata); corsia Piano coi blocchi; corsia Eventi con le pillole col lucchetto (nel piano una barretta all'ora fissa). «adesso» tratteggiato.
- **Blocchi**: carta col bordo nel colore del progetto, nome e durata, filtri in fila («Hα 2 h 30 · SII 2 h»), barra dei filtri nelle loro tinte, curva d'altezza dell'oggetto e «transita 22:10» tratteggiato. Si sposta col blocco, si allunga coi bordi (a 5 minuti, filtri in proporzione), si aggancia al cambio del vicino; coi tasti ← → di 5 minuti, Maiuscolo 15, Canc toglie. Scelto, sotto la linea: orario, filtri con − e + da 15 minuti, «Togli dal piano».
- **Tempo di cambio**: fascia tratteggiata prima di ogni blocco dopo il primo. Senza valore: niente fascia e «Scrivi il tempo dei cambi in Impostazioni.» con «Impostazioni ↗».
- **Conflitti**: bordo rosso, ✕ e la frase sul blocco (nei blocchi stretti solo ✕), elenco sotto la linea che porta al blocco. La sovrapposizione si scrive sul blocco che comincia dopo. Il meteo non e' un conflitto.
- **Regola della Luna**: quella decisa in v13 (dal 25% e sopra 10°, soglie delle Impostazioni), non «oltre il 50% e sopra l'orizzonte» del brief. Frase: «Banda larga con la Luna al 62% sopra 10°.» Da confermare con Marco.
- **Totali ed export** (carta sotto la linea): numero grande delle ore pianificate; «Buio 9 h · pianificato 7 h 35 · cambi 30 min · libero 55 min» (i cambi sono una voce in piu' del brief: senza, buio meno pianificato non torna). «Esporta per N.I.N.A.» con la riga sotto; con conflitti chiede «{n} conflitti: esporto lo stesso?» · Esporta / Annulla; poi «✓ Esportato alle 20:05». Piano vuoto: pulsante spento.
- **Stati**: senza sito («Serve un sito: il piano dipende da dove sei.» · Scegli il sito); nessun progetto («Nessun progetto ancora.» · Apri il Planner, al posto delle proposte); nessun progetto alto; senza buio (sito di prova a 51° N il 21 giugno: fasce fino all'astronomico, «◐ nessun buio», «Nessun buio stanotte: nessuna ora utile.»); piano vuoto («Trascina qui un progetto.»); con conflitti (quattro, uno per tipo); esportato («Esportato alle 18:42»).
- **Telefono**: linea verticale (le ore scendono, 0.9 px al minuto), colonne Luna, Meteo, Piano; «Aggiungi un progetto» apre le proposte e gli eventi in un foglio dal basso; un blocco toccato apre il suo foglio (↑ 15 min prima, ↓ 15 min dopo, filtri − +, Togli dal piano). Bersagli da 44 px. Piano vuoto: «Tocca «Aggiungi un progetto» per cominciare.»
- **Impostazioni**, sezione Planner: «Tempo di cambio fra due bersagli», vuota, «nessuna convenzione: scegli tu».
- **Testi da approvare**: «mancano», «nel piano · …», «adesso 20:05», «Togli dal piano», le frasi dei Tweaks senza buio e del telefono, «Ora fissa, 03:41:12: non si sposta.», l'aiuto sotto il blocco scelto.
- **Dati simulati**: progetti, transiti e Luna di stanotte come la Dashboard; ore mancanti da Progetti; postazioni (ZWO AM5 · Askar FRA400, Sky-Watcher EQ6-R Pro · Askar 103APO), Luna delle notti dopo, verdetti ora per ora, transito della ISS sulla Luna alle 03:41:12 (non e' nella lista del Planner), sito di prova a 51° N.

## v26 · Piano della notte completo, e la Luna in tutta l'app (19 ottobre 2026, brief di Claude Code, ADR 0013 «Il disegno» e «Le categorie», domini/meteo.md)

Supera la v25 dove dice; il resto della v25 resta. Le parole fra «» sono proposte, da approvare con Marco.

Brief. **A cosa serve**: decidere cosa si fa una notte su ogni postazione, in un modo solo, ed esportarlo per N.I.N.A. **Dati**: progetti, pianeti, Luna e comete (Fotografia); esopianeti, NEO e variabili (Ricerca); eventi del modo Eventi; fasce, Luna con la regola delle Impostazioni, meteo ora per ora; sette tempi della notte; orizzonte del sito. **Stati difficili**: due transiti sovrapposti, tempi non scritti, senza rete, Ricerca senza oggetti, conflitti. **La cosa piu' importante**: la linea del tempo che si riempie da sola e si corregge a mano. **Cosa non c'e'**: occultazioni asteroidali, supernove, campagne AAVSO, comandi all'hardware, scelte durante la notte, Lorentzian moon avoidance.

- **Modo per postazione e per notte**: «Fotografia» · «Ricerca» in testa, sotto le postazioni; la linguetta della postazione dice «Ricerca» quando lo e'. Cambiare modo con blocchi chiede «Il piano di stanotte si svuota: cambio modo?» · Cambia / Annulla.
- **Fotografia**: linguette «Deep sky» · «Sistema solare» in testa alle proposte; i blocchi stanno nella stessa traccia col segno piccolo della categoria (disegnato, non emoji). Sistema solare: pianeti e Luna con almeno 30 min sopra 30° nel buio, «sopra 30° {da}–{a} · massimo {n}° alle {ora}», «! ADC sotto 35°» quando una parte della finestra e' sotto, Macchia Rossa per Giove; «Aggiungi una cometa» per sigla (riga con magnitudine, altezza, Luna; «posizione ricalcolata per ogni blocco»); senza rete il pulsante e' spento con «Serve la rete per la posizione della cometa.».
- **Ricerca**: un elenco solo, Criteri a chip «Esopianeti · NEO · Variabili» (✓ e accento quando accesi, tutti accesi di partenza), «Aggiungi oggetto» per nome (dati simulati). Esopianeta: blocco a ora fissa col lucchetto, transito in una fascia dentro il blocco, le basi si allungano dai bordi (partenza 1 h). Algol: minimo a ora fissa col segno «minimo 02:46». Altre variabili e NEO: blocchi flessibili (30 e 45 min). Una proposta a ora fissa sovrapposta al piano dice «✕ Si sovrappone a {oggetto}: escluso.».
- **Completa / Rifai** sopra la linea, «↶ Annulla» dopo ognuno (torna al piano di prima; un ritocco a mano lo toglie). Riga sotto: «Prima le ore fisse, poi chi scende prima.». Regola: prima le ore fisse (a pari merito chi ci sta tutto coi margini, poi il piu' alto a meta' blocco); poi nei buchi, fra chi e' sopra la soglia in quel momento, chi chiude prima la sua finestra; a pari merito l'ordine delle proposte. Il blocco dura le ore mancanti, fin dove l'oggetto scende o fino al blocco dopo (minimo 30 min). Scelta di Claude: in Fotografia riempie con le proposte della linguetta aperta (Deep sky o Sistema solare), gli eventi restano a mano. Da confermare con Marco.
- **Tempi della notte** al posto del tempo di cambio: «Avvio» (raffreddamento + unpark) prima del primo blocco, «Cambio» (puntamento e centratura + autofocus) prima di ogni blocco dopo il primo, «Flip» tacca della sua durata al transito al meridiano dentro il blocco, «Chiusura» (park + riscaldamento) dopo l'ultimo. Stesso tratteggio, nome e minuti al passaggio del mouse. Un pezzo senza valori non si disegna; sotto: «Scrivi i tempi in Impostazioni: {mancanti}.» con «Impostazioni ↗». Nei totali «avvio, cambi e chiusura {n} min» (il flip sta dentro il blocco).
- **Dietro l'orizzonte**: con l'orizzonte importato conta la sagoma all'azimut dell'oggetto, senza conta 0°. Prima si controlla l'orizzonte, poi i 30°. Vale per proposte, Completa e conflitti.
- **Curva della Luna**: sottile e tenue dove non conta, tratteggiata e piu' spessa dove conta (Luna sopra l'altezza della regola e fase oltre «buona»). Striscia: piena banda larga, a contorno banda larga al limite, tratteggiata solo banda stretta.
- **Conflitti in piu'**: «Dietro l'orizzonte dalle …», «Base prima del transito sotto 30 min.» / «Base dopo …», «Banda larga con la Luna al 62% sopra l'orizzonte.» (o «sopra 10°»).
- **Stati (Tweaks)**: normale, dopo Completa la notte (EQ6-R: NGC 6992 che scende, poi Sh2-155 alto tutta la notte), piano Ricerca (Qatar-1 b in prima serata, 2026 TX alle 00:33, Algol e SS Cygni dopo; HAT-P-37 b escluso), con conflitti, piano vuoto, esportato, tempi non scritti, nessun progetto, nessun progetto alto, Ricerca senza oggetti, senza buio, senza sito. Altri Tweaks: rete, tempi (d'esempio · dalle Impostazioni), Luna, orizzonte, postazioni.
- **Telefono**: modo in testa; «Proposte ed eventi» (o «Oggetti di ricerca ed eventi») apre il foglio con linguette o Criteri in cima; Completa e Rifai sotto la linea, Annulla accanto alla riga d'aiuto; avvio, cambi e chiusura come fasce nella linea.
- **Dati simulati**: transiti, minimi, NEO e comete inventati (coordinate degli oggetti vere quando esistono), Macchia Rossa, tempi d'esempio 15, 1, 5, 5, 6, 1, 10.

### La Luna, in tutta l'app (decisione di Marco)

- **Impostazioni**, gruppo nuovo «Luna» prima di «Planner»: «Banda larga buona fino a» 25% (regola diffusa fra chi riprende), «Banda larga al limite fino a» 50% (nessuna convenzione: scegli tu), «La Luna conta sopra» l'orizzonte · 5° · 10° · 15° in pillole (Nautical Almanac: Luna sorta). Riga: «Sotto un cielo buio la Luna disturba prima: abbassa le percentuali.». La seconda sotto la prima: bordo rosso e «✕ Deve essere almeno {prima}%.», non si salva. Accanto alla riga d'aiuto la regola in uso. Si salva sul computer e la leggono tutte le pagine.
- **La regola** (`soglie.js`): solo banda stretta con la fase oltre «al limite» e la Luna sopra l'altezza; fra «buona» e «al limite» resta banda larga e si scrive «banda larga al limite». Supera la v13 (25% e 10°). Con le partenze cambiano i dati d'esempio: stanotte (62%) la banda stretta parte quando la Luna sorge (23:40), non sopra 10°; le notti al 34–50% tornano banda larga «al limite».
- **Dove si legge**: Meteo (riga della ripresa, racconto della notte con «sorge la Luna» o «la Luna sale sopra {n}°»), Dashboard (carta della Luna, fascia, calendario e legenda coi numeri scelti), Planner (Stanotte), Piano della notte (proposte, curva, conflitto). Tweak «luna» in Dashboard, Meteo, Planner, Piano della notte e Impostazioni: «dalle Impostazioni», «25% · 50% · orizzonte», «10% · 25% · sopra 10°».
- **Parole**: la design usa ancora «solo banda stretta»; il brief cita «consigliata banda stretta». Da decidere con Marco.
- **Impostazioni, sezione Planner**: via «Tempo di cambio fra due bersagli»; gruppo «Tempi della notte», sette righe in minuti, vuote, fonte «nessuna convenzione: scegli tu», riga «Scrivi tempi larghi: il margine sta dentro il numero.». Tweak «tempi»: vuoti · d'esempio. La «Distanza dalla Luna» (40°) resta nel Planner.

### v26.1 · Ritocchi dell'utente (19 ottobre 2026)

- **Setup in tendina**: una pillola nell'accento («AM5 · FRA400 ▾», col modo e i blocchi), il menu elenca i setup per intero con modo e blocchi; si chiude toccando fuori. Supera le linguette della v25 (con tanti setup erano troppe).
- **Fotografia · Ricerca** piu' piccolo, accanto alla tendina; sito, verdetto e «Meteo ↗» a destra. La testa ha due righe.
- **Completa · Rifai · Annulla** nella riga del titolo della linea del tempo, a destra; la fase della Luna accanto all'etichetta della corsia (sorgere al passaggio del mouse). Deep sky · Sistema solare restano nelle proposte.
- **Cambio d'esempio 10 min** (puntamento e centratura 5, autofocus 5), flip 6: valori d'esempio 15, 1, 5, 5, 6, 1, 10. Di partenza restano vuoti.
- **Blocchi stretti** (sotto il 9 % della notte): segno e nome tagliato, senza durata e filtri; nome, ore e filtri al passaggio del mouse.
- **Legenda** senza tramonto, nautico, astronomico e alba (le fasce li mostrano): buio, Luna, ripresa, tempi della notte.
- «Notte buona» resta: e' il verdetto di Meteo e Dashboard.
- **Aperto (Marco)**: Luna e Sole a mosaico richiamati da un piano salvato, il Sole di giorno su una postazione remota, e se i pianeti restano nel Piano della notte. Domande in `docs/per-claude-code-piano-luna-sole.md`; il disegno non cambia fino alla risposta.

## v26.2 · Impostazioni a linguette (19 ottobre 2026, richiesta dell'utente, scelte di Claude)

- Quattro linguette sotto il titolo, una sezione alla volta: «Sito e orizzonte» (coi siti in pillole, solo qui), «Luna», «Planner» (le soglie), «Piano della notte» (i tempi della notte, carta propria, prima stavano dentro Planner). Accanto al titolo la riga della sezione. Sul telefono le linguette scorrono, 44 px. Tweak «sezione» e `?sezione=sito|luna|planner|piano`.
- Cartelle e scansione, Meteo (chiave Meteoblue), ASTAP, Tema e nome entreranno come linguette quando Claude Code manda campi e testi: nessuna linguetta vuota.

## v26.3 · Impostazioni complete (19 ottobre 2026, richiesta dell'utente, scelte di Claude)

Supera la v26.2. Tutte le impostazioni dell'app in una pagina, otto linguette (una alla volta; sul telefono scorrono, 44 px): **Generale** · **Siti** · **Cartelle e scansione** · **Meteo** · **ASTAP** · **Luna** · **Planner** · **Piano della notte**. Tweak «sezione» e `?sezione=generale|siti|cartelle|meteo|astap|luna|planner|piano`.
- **Generale**: Nome utente (campo, Salva, «Usato per intestare le statistiche.»); Tema col componente SceltaTema del Primo avvio (modo e accento cambiano la pagina).
- **Siti**: pillole dei siti in testa; Coordinate, **Bortle** (classe e «scritto a mano»; la proposta dalle misure arriva come da v18.1), **Predefinito** («Usa come predefinito», riga «Il sito dei conti quando una notte non ne ha uno.», proposta), Orizzonte e il disegno a 360° come prima.
- **Cartelle e scansione**: elenco con Togli; «Aggiungi una cartella» con Su questo computer · Sul NAS, Verifica e gli esiti del Primo avvio; carta Scansione con ultima scansione, Scansiona / Interrompi.
- **Meteo**: chiave Meteoblue coi testi e gli esiti del Primo avvio (Verifica e salva, Rimuovi chiave, «Chiedi una chiave a Meteoblue ↗», proposta); «Meteo apre su» Deep sky · Sole (il predefinito di Meteo, v4); fonti.
- **ASTAP**: percorso con Verifica percorso e i suoi esiti; cataloghi D80 e V50 con ✓ trovato / ? non trovato (v17). Tweak «astap».
- **Luna** e **Piano della notte**: come v26.
- **Planner**: le soglie si scrivono (prima solo lette), come i tempi della notte: campo, unita', «partenza … · fonte», «· cambiato», errore sotto («Scrivi un numero.», «Da … a …», data «1/6/2026»). La Macchia Rossa in tre righe (longitudine, data, deriva). «Rimetti i valori di partenza» quando qualcosa e' cambiato. Si salvano sul computer; il Planner nella tavola usa ancora i valori fissi.
- Testi nuovi da approvare: «Usato per intestare le statistiche.» (dal Primo avvio), «Predefinito», «Il sito dei conti quando una notte non ne ha uno.», «Meteo apre su», «Fonti: Open-Meteo per il meteo, Meteoblue per il seeing.», «ASTAP e i cataloghi, sul sito di hnsky.org ↗», le righe dei cataloghi, «Il Planner, Progetti e il Piano della notte leggono questi valori.».
- Fuori, per ora: aggiungere un sito nuovo (il modulo del Primo avvio, da portare qui), backup.

## v26.4 · Le impostazioni collegate (19 ottobre 2026, richiesta dell'utente)

- Un registro solo in `soglie.js` (`ALsoglie.imp`): ogni chiave con partenza, unita', sezione, fonte e chi la legge. Le Impostazioni lo scrivono, le pagine lo leggono: Planner, PlannerSolare, Piano della notte, Dashboard (vista Progetti), Progetti (mese buono), Meteo (vista di partenza e ripresa). La regola della Luna passa dal registro (prima aveva una chiave sua).
- Elenco, collegamenti e cio' che resta fisso: `docs/per-claude-code-impostazioni.md`.
- Supera «si salvano sul computer; il Planner nella tavola usa ancora i valori fissi» della v26.3.

## v27 · Piano della notte: tre linguette, Sistema solare, postazione, tempi (19 ottobre 2026, brief di Claude Code, ADR 0013 «Il Sistema solare nel piano», «Le linguette e la postazione», ADR 0023)

Supera la v26 dove dice. Le parole fra «» sono proposte, da approvare con Marco.
- **Tre linguette** al posto di Fotografia · Ricerca: «Deep sky» · «Sistema solare» · «Ricerca», per postazione e per notte. Con blocchi: «Il piano di stanotte si svuota: cambio?» · Cambia / Annulla. Nella tendina del setup la linguetta di ogni postazione.
- **Deep sky**: progetti e comete (per sigla, «posizione ricalcolata per ogni blocco», pillola «Cometa»). Export per N.I.N.A.
- **Sistema solare**: progetti salvati (Luna a mosaico 12 pannelli dal terminatore, Giove e Saturno R G B con regione), a video. Interruttore **Notte · Giorno**: di giorno la linea va da 06:30 a 20:00 (Sole dalle 07:25 alle 19:11), striscia del meteo di giorno, riga fissa in ambra «Filtro solare sempre davanti all'ottica. Tetto e sicurezza li gestisce N.I.N.A.», titolo «Il giorno», due progetti del Sole (luce bianca intero 12 pannelli, Hα zona 4 pannelli). Conflitto «Sole sotto 30° dalle …». Il piano del giorno e' un piano a parte della stessa postazione.
- **Blocco del Sistema solare**: durata = pannelli × (ripresa + spostamento), per filtro sui pianeti, piu' i cambi filtro con la ruota; non si allunga dai bordi, si sposta. Nome, «mosaico 12 pannelli» o «R G B · 3 × 1 min», pannelli come tacche in fila (filtri nelle loro tinte). Aperto: il conto («12 pannelli × (4000 frame · 5 ms · circa 80 s + spostamento 5 s) → 17 min») e la carta piccola del mosaico coi numeri nell'ordine, con tipo, sovrapposizione, ordine e filtro. Blocchi corti larghi almeno 30 px, nome al passaggio del mouse.
- **Export Sistema solare**: «Esporta per SharpCap», riga «Un file di sequenza per SharpCap Pro: parte da solo all'avvio.» e i due avvisi col «!» (plate solving sul disco, video in SER).
- **Postazione**: accanto alle linguette il setup in piccolo («mono · ruota 7 filtri» / «a colori · senza ruota»): senza ruota il conto non ha cambi filtro e il tempo «Cambio filtro» non si chiede.
- **Avvio e Chiusura** elencano i passi accesi, sotto la legenda e al passaggio del mouse: «Avvio 20:37 · raffreddamento · aspetta che sia sicuro · apre il tetto · unpark», «Chiusura 05:16 · park · chiude il tetto · riscaldamento». Il tetto e il sensore vengono dall'automazione della postazione.
- **Il conto del blocco deep sky** (aperto): «Hα 12 × 300 s = 1 h · dither 4 × 34 s · scaricamento 12 × 0.5 s · filtro 8 s · autofocus 1 × 3 min → 1 h 05». Pose di 300 s in banda stretta, 120 s in LRGB (simulate: nell'app dal progetto). Il blocco dura il conto; allungando dai bordi cambia l'integrazione. Completa e Rifai tengono conto del conto e non mettono la banda larga dove la Luna la vieta. Una parte senza tempo scritto manca e la riga dei tempi mancanti la nomina (solo i tempi che servono a quella postazione e linguetta).
- **Conflitto nuovo**: prima di un evento fisso (ISS, transito, minimo), se fra la fine del blocco e l'evento c'e' meno di puntamento + autofocus + cambio filtro: «Arrivi al transito con {n} min di margine.» sul blocco prima.
- **Impostazioni**: linguetta «Piano della notte» tolta; i tempi stanno in «Planner», in tre gruppi (Avvio e chiusura, Per bersaglio, Durante le pose), uguali per tutta l'app, vuoti, fonte «nessuna convenzione: scegli tu»; i due del tetto solo se una postazione ha il tetto. Linguetta nuova «Automazione»: una carta per postazione, tre righe Sì / No (tetto o cupola, sensore di sicurezza, pannello per i flat) con l'effetto sotto; riga «La chiusura d'emergenza col maltempo si imposta in N.I.N.A.». Registro: `planner.tempi` (quindici chiavi, d'esempio 10, 0.1, 1, 0.5, 1, 10 · 2, 3 · 8, 34, 3, 0.5, 2, 3, 5), `automazione.a`, `automazione.b`.
- **Tweaks**: stati in piu' «Sistema solare · notte», «Sistema solare · giorno», «esportato per SharpCap», «margine prima di un transito»; «automazione» (EQ6-R senza, AM5 con tetto e sensore · nessuna · dalle Impostazioni), «setup» (mono con ruota · a colori senza ruota).
- **Telefono**: linguette in testa, Notte · Giorno accanto, passi di avvio e chiusura sotto la linea, il blocco del mosaico apre il foglio con conto e carta.
- **Da fare dopo questa tavola**: nel Planner, modo Sistema solare, «Salva come progetto» coi campi del brief; in Progetti, per i progetti del Sistema solare «ultima volta nel piano: {data}» al posto della barra.
- **v27.1** (utente): tolto il conto scritto dal blocco deep sky aperto. Il calcolo resta (la durata del blocco e' quella del conto); il conto del Sistema solare resta.
- **v27.2** (utente): i pulsanti diventano «Completa la sequenza» · «Rifai la sequenza», uguali di notte e di giorno (proposta). Aperto: come sceglie il piano automatico (punto piu' alto o seeing migliore per i pianeti e il Sole; per il deep sky chi chiude prima, il transito o l'integrazione). Domande in `docs/per-claude-code-piano-strategia.md`.

## v27.3 · Progetti rivisti (19 ottobre 2026, con l'utente)

- **Anelli**: nel colore del gruppo (in corso accento, in attesa tenue, fermi ambra, finiti verde), sempre con il gruppo scritto in testa. Oltre il 100%: ✓ nell'anello e a destra «+ 10 min» (le ore in piu'), nella scheda «di 10 h · + 10 min».
- **Riga sotto il nome** corta: «nel piano stanotte · 22:45–03:15» o «prossima: ven 2 · 3 h visibili».
- **Bortle di Cima Ekar 3**, come in Impostazioni › Siti.
- **Gruppi pieghevoli** (desktop): In corso sempre aperto; In attesa, Fermi, Finiti e Sistema solare mostrano i primi 3 e «Mostra tutti · {n}» / «Mostra meno». Sul telefono restano le pillole per gruppo.
- **La prima scansione crea i finiti** (utente): un progetto finito per ogni oggetto gia' ripreso, obiettivo = ore fatte. Riga «dalla prima scansione · {mese anno}», scheda «Finito · dalla prima scansione, …», «obiettivo = ore fatte». Nella tavola 28 oggetti simulati (nomi e coordinate veri).
- **Sistema solare in Progetti** (brief v27): gruppo proprio, niente barra: segno del corpo nell'anello, durata nel piano a destra, «nel piano stanotte, 03:00» o «ultima volta nel piano: {data}». Scheda: Corpo, Setup, Mosaico, Filtro, Ripresa (con regione), Durata nel piano; azioni Apri nel Planner ↗ · Aggiungi al piano ↗ · Elimina; Le notti: Nel piano, Ultima volta nel piano.
- **Col Piano della notte**: in Le notti la riga «Stanotte · nel piano · 22:45–03:15» con «Apri il piano ↗», o «non nel piano» con «Aggiungi al piano ↗» (anche fra le azioni).
- **Notti riprese**: sotto Le notti l'elenco (data, ore, segno e parola della ripresa: banda larga / banda larga, poi solo banda stretta / solo banda stretta). Dati simulati.
- **Le misure a tutta larghezza**, a tessere (3 colonne, 2 sul telefono), come nel riepilogo dell'Archivio: FWHM, HFD, Eccentricità, Stelle, SNR, Altezza, Fondo cielo, Rumore del fondo, Luminosita' del cielo; giudizio dove c'e' una soglia. Valori oltre le tre mediane simulati.
- Da fare: nel Planner, Sistema solare, «Salva come progetto».
- **v27.4** (utente): Le misure tornano tre (FWHM, eccentricita', luminosita' del cielo), mediane di tutti i filtri («tutti i filtri · mediane di {n} frame»), con «Tutte le misure, per filtro e per notte, nell'Archivio ↗»: qui solo per dire se il progetto va bene. Le notti riprese sono un calendario di un mese (componente CalendarioNotti, prop nuova `buoneL`): giorni ripresi accesi, legenda «notte ripresa per questo progetto», frecce fra i mesi con notti, riga sopra «{n} notti in {m} mesi · tocca un giorno acceso»; il giorno toccato apre la riga (data, ore, ripresa) con «Apri in Notti ↗». Luminosita' d'esempio dei progetti di Cima Ekar portata a Bortle 3.
- **v27.5** (utente): nella scheda due azioni distinte. «Modifica» (qui): nome, setup in pillole, obiettivo per filtro con − e + di 30 min; le ore fatte restano; Salva / Annulla. «Rinquadra nel Planner ↗» (prima «Apri nel Planner ↗»): apre il Planner col progetto com'e' (oggetto, setup, rotazione, mosaico, ore fatte e obiettivo) nello stato «progetto iniziato», per ruotare e spostare; il Salva torna alla scheda. Il Planner legge `?da=progetto&p&n&c&cn&rot&mos&fatte&ob`. Ricerca e ordine nell'elenco: da fare.
- **v27.6** (utente): «Rinquadra» porta anche le ore per filtro del progetto (`&fil=ha:480,oiii:420,sii:300`): il Crea del Planner le ha gia' scritte, al Salva non si riscrivono.
- **v27.7** (utente): il calendario delle notti c'e' per tutti i progetti (in corso, in attesa, fermi, finiti, anche dalla prima scansione); parte dal mese dell'ultima notte. Notti d'esempio simulate dalle ore fatte. Il Sistema solare resta senza calendario (nel piano, non notti di ripresa).
- **v27.8** (utente): **Planner, Sistema solare**: in fondo la carta «Salva come progetto» (corpo, setup, mosaico, filtro; riga «In Progetti, senza ore da raggiungere. Frame, posa e regione si scrivono nella scheda; il Piano della notte lo richiama nella linguetta Sistema solare.»). Per Luna, Giove, Saturno e Sole che hanno gia' il progetto: «Apri in Progetti ↗». Gli altri creano il progetto in Progetti (`?solnuovo=1`), con «da scrivere: frame e posa». Testa del modo: «come il setup inquadra il corpo · si salva come progetto, in fondo» (era «non si salva»). **Progetti**: campo «Cerca un progetto» (nome e nome comune; con la ricerca i gruppi si aprono) e «Ordine» Data · Ore che mancano · Nome dentro i gruppi; «Nessun progetto col nome «…».». Telefono: cerca a 16 px, ordine che scorre.

## v27.9 · Archivio sul telefono, testa compatta (19 ottobre 2026, utente)

- Una riga sola: Deep sky · Sole · Sistema solare in una pista (13 px, 38 px dentro la pista), «⋯» e «+» tondi da 44 px. Sotto, in piccolo, il conto («240 oggetti, di cui 3 mosaici · 486 ore · …»). Il numero grande e la pillola «+ Aggiungi oggetto» restano solo sul desktop.
- Il foglio «⋯» (Vista e ordine) sale dal basso: Carte · Elenco in tutte e tre le parti, l'ordine (Per nome · Per integrazione · Più recenti) nel Deep sky. Supera «Carte/Elenco e l'ordine stanno dentro Filtri» del 18/10. Cerca e Criteri restano in vista nel Deep sky.
- Il foglio «⋯» si apre dentro lo schermo come il menu Altro (sopra la barra in basso, carta col bordo e l'ombra, colori del tema), non piu' a tutta finestra.
- Pista delle parti e scelte del foglio «⋯» nell'accento, come le pillole del desktop («Le scelte nell'accento», 17/10).

## v28 · La testa del telefono, tre tipi (19 ottobre 2026, proposta di Claude, approvata dall'utente)

Stesse misure in tutte le pagine: pista `card2` arrotondata, voci alte 38 px dentro 44 px toccabili, 13 px, la scelta nell'accento; conto in piccolo; al massimo due righe prima del contenuto.
- **A · Pista + ⋯ + «+»**: da 2 a 4 parti della pagina in una pista; «⋯» apre vista e ordine in un foglio dentro lo schermo (bordo, ombra, «Fatto»); «+» tondo per l'azione principale.
- **B · Cerca + Criteri**: campo e pulsante sulla stessa riga; criteri o ordine in un foglio.
- **C · Fila che scorre**: pista che scorre di lato quando le voci sono piu' di 4.
- Fatto: **Archivio** (A, B nel Deep sky), **Progetti** (B: cerca + «⋯» con «Ordine nei gruppi»; C: i cinque gruppi col numero), **Impostazioni** (C: le otto linguette).
- Fatti anche **Piano della notte**, **Planner** e **Notti** (v28.1). Dashboard, Da confermare, Attrezzatura restano.
- Tutte le pagine leggono `?formato=telefono` (o `desktop`) dall'indirizzo, prima del Tweak: i link al telefono si aprono gia' nel formato giusto.
- **Piano della notte, telefono (v28)**: C le notti in pista che scorre; A Deep sky · Sistema solare · Ricerca + «⋯» (Setup: le postazioni con linguetta e blocchi, il setup in piccolo, Notte · Giorno nel Sistema solare); sotto, in piccolo, «AM5 · FRA400 · Cima Ekar · ✓ notte buona · Meteo ↗». Il titolo grande sul telefono esce. Il desktop resta com'era.
- **Meteo sul telefono**: resta com'e' (utente, 19/10): la testa e' gia' compatta. Restano Planner e Notti.

## v28.1 · Planner e Notti sul telefono, controllo, stati di Progetti (19 ottobre 2026, utente)

- **Planner, telefono (A)**: in testa a tutti e tre i modi la pista Deep sky · Sistema solare · Eventi (38 px dentro 44, scelta nell'accento) e «⋯» tondo da 44; sotto, in piccolo, il setup e «· Cima Ekar · dati simulati» (nel Deep sky anche «a confronto {ottica}»). Il «⋯» apre il foglio «Setup» dentro lo schermo (bordo, ombra, «Fatto»): i setup con focale e camera, scelta nell'accento; nel Deep sky «A confronto, tratteggiato sulla carta» (Nessuno o un altro setup); «Setup di prova» (apre il passo Setup coi campi della prova) e «Attrezzatura ↗». Trova resta la riga grande dell'oggetto nel foglio della carta. Tolti i commutatori di modo dentro i fogli (Planner, PlannerSolare, PlannerEventi) e le tendine del setup del telefono (passo Setup del Deep sky, PlannerSolare); «Campo di» negli Eventi resta (e' il confronto del singolo evento). Il desktop non cambia.
- **Notti, telefono (B + C)**: prima riga Mese + Criteri (Mese largo, «Mese · Settembre 2026 ▼»; aperto e' nell'accento, «Settembre 2026 ▲», e sotto si apre il calendario); seconda riga la pista delle notti che scorre («mar 29 4 h 18», scelta nell'accento). Sotto, in piccolo, «dalla più recente» (o «{n} notti con questi criteri») e le righe di stato: «· ! 2 cose da vedere ▼» (con una sola riga, il suo testo), che apre le righe sotto. La carta «Le notti» con la striscia a carte esce dal telefono: i dati della notte stanno nella carta della notte sotto. Calendario, Criteri e «Nessuna notte con questi criteri» in una carta che c'e' solo quando servono.
- **Controllo del telefono**: Progetti, in Modifica le righe dell'obiettivo per filtro andavano su tre righe («6 h / 10 / fatte»): ora nome e «6 h 10 fatte» uno sotto l'altro. La percentuale della scheda al 100% esatto mostra ✓ come l'elenco. Piano della notte: nel foglio «⋯» il setup scelto e' nell'accento (prima card2), come la v27.9.
- **Da decidere (proposte, non fatte)**: Progetti sul telefono tiene il titolo grande e il conto su due righe sopra Cerca e la pista (quattro righe prima dell'elenco); proposta: via il titolo, conto in piccolo sotto la pista come Archivio. Archivio sul telefono: il segnaposto «Cerca: M 31, Velo, Andromeda…» si taglia; proposta «Cerca: M 31, Velo…» solo sul telefono. Piano della notte sul telefono: la linea tratteggiata del transito (21:30) passa sopra le righe del blocco; proposta: le righe del blocco su un fondo pieno.
- **Tavola degli stati di Progetti**: `pagine/Progetti stati.dc.html`, telefono e desktop: Sistema solare (Luna), finito dalla prima scansione (M 27), in Modifica (IC 1396), calendario su piu' mesi (IC 1396 sul primo mese), oltre il 100% (NGC 6960, «+ 10 min»). Progetti legge tre props nuove: `progetto` (id), `modifica`, `calendario` (ultimo mese · primo mese).
- **Per Claude Code**: `docs/per-claude-code-progetti.md` (notti per progetto col tipo di ripresa, finiti dalla prima scansione, misure, «ultima volta nel piano», piano di stanotte, parametri di Rinquadra, Modifica, testi da approvare con Marco).
- In sospeso le risposte su `per-claude-code-piano-strategia.md` e `per-claude-code-piano-luna-sole.md`.

## v28.2 · Il telefono più leggero (19 ottobre 2026, resoconto di Claude, approvato dall'utente: «vai»)

Regola: a tutta larghezza solo l'azione che chiude un percorso (Applica, Salva il progetto, Crea); le altre sono pillole larghe quanto il testo, affiancate; i ritorni («← Progetti», «← Tutte le notti», «← Impostazioni») sono testo con la freccia; Elimina e' testo rosso. Restano come sono Notti (testa), Planner, Archivio, Attrezzatura, Da confermare, Riepilogo, Primo avvio.
- **PillolaScelta**: `misura="piccola"` vale anche sul telefono: 38 px dentro la traccia, 44 in tutto (prima il telefono la ignorava, 52 px).
- **Dashboard, telefono**: la carta parte da «Ore utili stanotte» col verdetto; Notte · Progetti · Sistema solare in una pista piccola in fondo alla carta, sotto la legenda. Luna · Sole piccola. Il desktop non cambia.
- **Meteo, telefono**: modello e aggiorna nella riga del titolo: pillola del modello («Automatico ▾», 34 px dentro 44, il menu si apre sotto a destra) e «↻» tondo (34 dentro 44, «Aggiorna la previsione»). Titolo 20 px su una riga. Deep sky · Sole piccola.
- **Progetti, scheda sul telefono**: Tweak «scheda» (e `?scheda=`): «colonna» (com'era), «affiancata» (A, partenza: miniatura in alto, anello da 104 px a sinistra e barre per filtro a destra nella stessa riga, tre misure in una riga), «carosello» (B: come A, poi Mosaico, Le notti e Le misure in carte che scorrono di lato, 86% della larghezza, riga «Le notti · Le misure · scorri di lato»). Azioni in fila di pillole, Elimina testo rosso, «← Progetti» testo. Tavola: `Progetti stati`, riga in alto «La scheda sul telefono · da scegliere». **Scelta dell'utente (19/10): A, «affiancata».** «colonna» e «carosello» restano nel Tweak per confronto; Claude Code porta solo la A.
- **Piano della notte, telefono**: via la barra piena «Proposte ed eventi»: pillola «+ Proposte 3» (o «+ Oggetti» in Ricerca) nella riga del titolo «La notte»; la Luna passa nella riga sotto. «Completa la sequenza» pillola piena, «Rifai» e «↶ Annulla» testo accanto; sotto la riga d'aiuto.
- **Impostazioni, telefono**: si apre sull'indice delle nove sezioni (nome, una riga sotto, ↗; Generale «Marco · modo scuro», Siti «Cima Ekar · Bortle 3 · predefinito», le altre la loro descrizione). Toccata una riga: «← Impostazioni», titolo e riga della sezione; via le linguette che scorrono. Con `?sezione=` o il Tweak si apre la sezione. Nome utente: «Salva» e' una pillola dentro il campo, solo quando il nome e' cambiato. Gli altri «Salva» delle sezioni restano come sono (da rivedere uno per uno). Il desktop non cambia.
- **Cerca**: gruppi nuovi «progetti» (nome, nome comune, gruppo e ore; apre la scheda `Progetti.dc.html?p=`) e «impostazioni» (quindici voci: nome utente, tema, coordinate, Bortle, sito predefinito, orizzonte, cartelle, scansione, chiave Meteoblue, Meteo apre su, ASTAP, regola della Luna, soglie, tempi della notte, tetto e sicurezza; aprono `Impostazioni.dc.html?sezione=`). Le pagine Progetti, Planner, Piano della notte e Impostazioni si aprono. Ogni oggetto ha accanto «Planner ↗» (la riga apre l'Archivio). Esempi in testa: «Progetti · IC 1396, Luna», «Impostazioni · Bortle, Meteoblue». Dati simulati.
- **Tavola Telefono**: tredici pagine, gia' col formato telefono nell'indirizzo; esce Misure dei frame (e' la tavola del componente, gia' nel Riepilogo dalla v17.1), che resta come tavola di riferimento.
- **Per Claude Code, alla fine**: l'indice delle Impostazioni vuole il valore principale di ogni sezione (oggi solo Generale e Siti); Cerca vuole l'indice dei progetti e delle voci delle Impostazioni.

## v28.3 · Ritocchi del telefono dopo il giro dell'utente (19 ottobre 2026)

Giudizio dell'utente: Notti, Archivio, Progetti (affiancata), Attrezzatura, Da confermare, Impostazioni, Primo avvio, Cerca vanno bene come sono; Piano della notte sul telefono va ridisegnato (proposta sotto, non fatto).
- **Dashboard, telefono**: «Le prossime 3 notti» mostra solo la prima; sotto «Le altre 2 notti ▼» (aperto: «Mostra meno ▲»). Il titolo resta «Le prossime 3 notti».
- **Meteo, telefono**: le carte delle notti in alto hanno la stessa altezza in Deep sky e in Sole: nel Sole la riga della ripresa c'e' ma non si vede (prop `riserva` di Striscia). «Come va la notte» parte dai momenti che contano (buio, cambi del verdetto, Luna, cambio di ripresa: «I momenti che contano · 9 di 15»); sotto «Tutta la notte, ora per ora · 15 ▼» apre il racconto intero (tramonto, alba, pianeti, misure), «Solo i momenti che contano ▲» lo richiude. Il desktop non cambia.
- **Riepilogo, telefono** (componente MisureFrame): in «Frame per frame» vista (barre · linee), ordine (per ora · per valore), valore (misurata · allo zenit) e l'altezza della Luna stanno nel menu «Vista ▼», che si apre sotto il titolo; fuori restano i filtri («Un grafico per filtro»). «← Archivio» / «← Notti» testo. La pagina Riepilogo legge `?formato=` (prima no: nella tavola Telefono si vedeva il desktop).
- **Planner**: «Setup di prova» pillola piccola (32 px dentro 44, 12 px), anche nel Sistema solare e nel foglio «⋯». Vale anche sul desktop.

## v28.4 · Piano della notte sul telefono, a elenco (19 ottobre 2026, proposta di Claude, «ok» dell'utente)

- **Tweak «telefono»** (e `?vista=`): «elenco» (partenza) · «linea» (la linea verticale di prima). Il desktop non cambia.
- **Striscia della notte**: sotto «La notte», orizzontale, alta 48 px: fasce del cielo, curva della Luna (tratteggiata dove conta), blocchi pieni nel loro colore, avvio, cambi e chiusura a tratteggio, ISS come tacca, linea dell'ora di adesso; ore ogni due sopra.
- **Il piano in righe**, in ordine d'ora: per ogni blocco inizio e fine, la barretta del colore, segno, nome, filtri (o «ora fissa · …»), durata e «›»; il conflitto in rosso sotto. Fra i blocchi le righe piccole di avvio, cambi e chiusura col loro testo. Toccata una riga si apre il foglio del blocco di sempre (↑ 15 min prima · ↓ 15 min dopo, filtri con − e +, Togli dal piano). Piano vuoto: riga tratteggiata «Nessun blocco. Tocca «+ Proposte» o «Completa la sequenza».».
- Nell'elenco l'elenco dei passi di avvio e chiusura sotto la legenda esce (stanno nelle righe).
- Tavola: `pagine/Piano della notte telefono.dc.html` (linea di oggi, elenco normale, con conflitti, Ricerca, Sistema solare di giorno, piano vuoto).
- **Approvato dall'utente** (19/10): «il piano della notte così va molto meglio». Elenco di partenza.

## v28.5 · Attrezzatura, il setup aperto nell'accento: provato e tolto (19 ottobre 2026)

- Provato il fondo dell'accento sulla carta del setup aperto; l'utente: «troppo, era meglio prima». Torna com'era (carta normale). Nessun altro colore del tema in Attrezzatura per ora.

## v29 · Il contratto del meteo (20 ottobre 2026, decisioni di Marco; contratto dell'app `docs/domini/meteo.md`)

Il contratto dell'app e' la verita'. Supera, dove dice, v10 «La qualita'», v11 «Il verdetto», v13 «La regola» e il racconto della notte in Meteo. La copia di prima resta in `pagine/Meteo v4.dc.html` (legge il soglie.js nuovo: nuvole fino al 25 % comprese, Luna da −5°).

- **Il semaforo lo fanno solo le nuvole**: copertura media nel buio in okta (WMO 2700): buona fino a 2/8 (25 %), incerta fino a 4/8 (50 %), non adatta da BKN in su. Il punteggio 0-100 non decide piu' niente, in nessuna pagina. `ALsoglie.verdetto`.
- **Ore utili = ore di buio serene** (nuvole fino al 25 %), dette come intervallo e conto, mai minuti: «dalle 21 alle 04, 7 ore». `ALsoglie.oreSerene`, `intervallo`. Stanotte in Meteo e Dashboard: 7 ore (prima 6 e 9); venerdì 2: 9 ore.
- **Le altre misure pesano accanto, senza cambiarlo**. Ogni misura con soglia ha la parola ora per ora e per la notte quella dell'ora peggiore, con intervallo e conto («✕ non adatto dalle 01 alle 06, 5 ore»). Accanto al semaforo «Pesa accanto:» solo cio' che e' incerto o non adatto.
- **Gli altri fattori**: in ordine del backend (da non adatto a buono, a pari parola chi comincia prima); se ne vedono due, gli altri dietro «Altri N fattori» (il testo non cambia aprendo). Raffiche come fattore a se' (non adatte da 29 km/h).
- **Le carte sempre allo stesso posto**: nuvole, nuvole basse, condensa, pioggia, visibilita', vento, seeing, jet stream, aerosol; poi temperatura e punto di rugiada, polveri, vento a 700 hPa. Valore della notte = media delle ore con un numero (pioggia: totale), picco = ora peggiore con l'ora; misura parziale lo dice. Interi; pioggia, seeing, visibilita' un decimale, aerosol due; il numero resta dal lato della soglia del valore vero (`ALsoglie.mostra`).
- **Il grafico**: all'apertura solo le nubi (tre strati) e il tratto sereno con le sue ore; l'umidita' si accende a sinistra in %, a destra una misura alla volta col colore del giudizio e la parola dove cambia (un'altra la sostituisce). Visibilita' da 0 a 20 km con la radice. Niente curva della qualita', niente Luna sul grafico di Meteo. La legenda e il riquadro dicono solo cio' che e' disegnato, piu' «ora serena / non serena». Senza mouse la frase sopra il grafico dice di toccare.
- **Il filo dell'ora** porta tutte le carte a quell'ora; una barretta (clic o frecce) ferma una carta sola, × la riporta alla notte (`CardMeteo`: `fissa`, `onTorna`, `onTasto`).
- **La Luna** (vale in tutta l'app, Impostazioni › Luna): buona fino al 25 %, banda larga al limite fino al 50 %, oltre consigliata banda stretta; pesa solo col buio e sopra −5° (rete TESS, arXiv 2105.01066, ADR 0013, Marco 19/10). La riga: «Luna al 62% dalle 23 · banda larga fino alle 23»; fra 25 e 50 % «senza Luna»; su tutta la notte solo il dato; mai su col buio, fuori. `ALsoglie.lunaNotte`. Pillola «banda stretta» in giallo, non rosso: non e' un difetto della notte.
- **Stato nuovo**: «seeing, chiave appena messa» (Meteoblue non ancora chiesto: la carta non chiede la chiave). «Seeing: meteoblue» nei crediti solo quando il seeing viene da li'.
- **Fuori dal contratto, lasciati come sono**: la vista Sole di Meteo (ora anch'essa col verdetto dalle nuvole), il Campionamento. Da decidere con Marco.
- **Dashboard**: vista Notte con le nuvole al posto della qualita'; ore utili, accordo e vento a 700 hPa accanto al solito del sito; prossime notti con le nuvole e la riga della Luna nuova.
- **Notti e Riepilogo**: verdetto dalle nuvole medie del meteo vero, «N ore serene su B di buio».
- **Piano della notte**: solo la Luna da −5° (da soglie.js); il resto con la brief `design-piano-della-notte-completo.md`.
- **Ritocchi dell'utente (20/10)**: il racconto della notte torna in Meteo com'era a vista, sotto gli altri fattori, col verdetto dalle nuvole («Diventa buona · nuvole al 10%, 1 okta su 8») e la Luna sopra/sotto −5°; senza riquadri sotto. Via «Pesa accanto» (sta negli altri fattori) e il tratto sereno; al suo posto l'andamento della notte come in Dashboard: la curva delle nuvole totali, con legenda, riquadro e punto sul filo.

## v29.1 · Il verdetto torna dal punteggio (20 ottobre 2026, Marco: supera il contratto)

Marco: il giudizio della notte coi pesi di tutti i fattori, da 100 a 0, dà una panoramica migliore delle sole nuvole. Supera in v29 «Il semaforo lo fanno solo le nuvole» e «Ore utili = ore di buio serene». Il contratto dell'app va aggiornato: `docs/per-claude-code-meteo-verdetto.md`.

- **Torna com'era (v11, v13)**: qualita' ora per ora 0-100, somma dei pesi (nuvole 35, seeing 30, trasparenza 12, condensa 9, vento 9, jet stream 5; la Luna fuori), pioggia e nuvole dal 50 % bloccano; verdetto dalla media nel buio, buona da 70, incerta da 40; ore utili = ore con qualita' da 60. Curva della qualita' sul grafico di Meteo e della Dashboard; nel racconto «Diventa buona · qualita' da 85, il primo limite e' il seeing»; riquadro «Qualita' della notte 87/100». Nuvole buone sotto il 25 %, incerte sotto il 50 % (com'erano). Notti e Riepilogo dal punteggio.
- **Resta del contratto**: ore come intervallo e conto («dalle 21 alle 06, 9 ore»), la Luna (25 · 50 % · sopra −5°) con la sua riga, gli altri fattori con «Altri N fattori», le carte in ordine fisso con medie, picchi e arrotondamenti dal lato della soglia, una misura a destra col giudizio, la carta fermata su un'ora, lo stato «chiave appena messa», i crediti di meteoblue.
- Dati d'esempio: stanotte 9 ore (21–06), buona, come prima della v29.


## v30 · Piano della notte, brief completa (20 ottobre 2026, brief di Claude Code, ADR 0013, 0020, 0023, domini/meteo.md)

Supera le v25-v28.4 dove dice. Le parole fra «» sono proposte, da approvare con Marco.

### 0bis · Meteo v29.1, correzioni
- La qualita' 0-100 resta (Marco, 20/10; pesi della v13 = ADR 0020). Il bridge `per-claude-code-meteo-verdetto.md` e' chiuso: il contratto dell'app dice lo stesso.
- **Dashboard**: accanto alla qualita' di stanotte la riga del racconto: «limita {fattore} · qualita' fino a {n}», «nessun limite» da 85.
- **Ore serene -> ore utili** nello stato senza buio di Meteo e nella tavola Meteo stati (stato 15). Tavola Meteo stati: un documento solo.
- **Nuvole al 25% esatto = buona** (`soglie.js`: `x <= 25`).
- **Impostazioni › Planner**: via «Distanza dalla Luna 40°»; carte nuove «Luna per bersaglio», «La notte del piano», «Ricerca» (sez. 9-10). Automazione: riga «Flat di cielo» (solo senza pannello) e gruppo «Flat». Tempi: «Flat e dark-flat per filtro» (min).

### La Luna per bersaglio
- Distanza richiesta = piena / (1 + (giorni dalla Luna piena / meta')^2): banda larga 120° · 10 giorni, OIII 90° · 10, Hα SII dual band 60° · 7. Sotto −5° la Luna non conta. `ALsoglie.serveLuna`, `lunaPassa`, `bandaDi`, chiave `luna.bersaglio`.
- Giorni dalla piena dalla fase illuminata (mese di 29.53 giorni). Stanotte (62%): servono 87° · 65° · 34°.
- Impostazioni: tre righe (gradi a Luna piena, meta' a giorni), la curva lungo il mese col segno di stanotte, la riga d'aiuto.
- Piano: pillola «Luna a 74° · servono 87°» o, con piu' bande, «Luna a 74° · larga no · OIII sì · Hα sì»; conflitto «Luna a 52°: in banda larga servono 87°.» (supera «Banda larga con la Luna al …»). Planner (Trova): la distanza di partenza e' quella della banda stretta di stanotte (la piu' bassa).

### Piano della notte
- **Pulsanti** «Completa il piano» · «Rifai il piano» (supera «… la sequenza»). Riga d'aiuto per linguetta: «Prima le ore fisse, poi chi scende prima, vicino al suo transito.» · «Ogni corpo nell'ora col seeing migliore sopra la soglia, vicino al transito.».
- **Regole del piano automatico** (nessuna impostazione): ore fisse; poi chi scende prima; ogni blocco spostato verso il transito se c'e' spazio; deep sky mai sotto la durata minima (Impostazioni, 1 h); i filtri a blocchi, ognuno solo nelle ore in cui la sua Luna passa, ordinati dalla Luna; le ore «non adatte» del meteo solo se non c'e' altro posto. Sistema solare: seeing migliore (classi di Meteo, simulato), a pari merito vicino al transito; Giove sulla Macchia Rossa; Luna piu' alta possibile; senza chiave Meteoblue al transito.
- **Il perche' dell'ora** sotto i filtri del blocco messo dal piano (e nell'elenco del telefono): «al transito 20:55», «prima che scenda: sotto 30° alle 05:11», «seeing buono 02:00» (al mouse «previsione del seeing, non una misura»), «Macchia Rossa al meridiano 05:20», «più alta possibile: 59° alle 05:36», «LRGB prima della Luna, Hα dalle …» / «Hα con la Luna, LRGB dopo le …», «Hα dal crepuscolo nautico, 20:15». Spostato, allungato o ritoccato a mano lo perde.
- **Crepuscolo nautico** per la banda stretta: dalla fine del nautico (Sole sotto −12°). Da confermare con Marco: «crepuscolo nautico» puo' voler dire anche dentro il nautico (Sole sotto −6°).
- **Altezza massima**: proposte e piano la rispettano; conflitto «Sopra 80° dalle …». **Pausa prima del meridiano**: fascia grigia prima del transito dentro il blocco; conflitto «Il flip cade nella pausa prima del meridiano.» se un bordo del blocco cade fra pausa e flip.
- **Flat**: col pannello dopo la chiusura («Flat · Hα OIII · 25 + 25 · dark-flat 25 + 25»); senza pannello, coi flat di cielo, al crepuscolo della sera (Sole fra −2° e −7°). Solo i filtri usati. Totali: «avvio, cambi, chiusura e flat».
- **Mosaico deep sky** (M 31, 4 pannelli): nel blocco «pannelli 3 · 4 · 1 · 2», nelle proposte «tutti ogni notte, dal più indietro».
- **Ricerca**: Criteri «Esopianeti · NEO · Variabili · Campagne AAVSO · Supernove». Campagna AAVSO (CH Cygni: filtro V, ogni 2 min per 2 h, priorita' alta, ultima 3 giorni fa, «Alert ↗»); supernova (SN 2026qd, mag 15.8 in NGC 7331, 12 giorni; sopra la soglia di Impostazioni). Senza chiave: «Serve la chiave {AAVSO / TNS} in Impostazioni.».
- **Export N.I.N.A.**: riga con «La chiusura d'emergenza col maltempo si imposta in N.I.N.A.».
- **Tweaks nuovi**: stati «dopo Completa il piano», «banda stretta col crepuscolo nautico», «altezza massima col conflitto», «pausa prima del meridiano», «Sistema solare · senza chiave Meteoblue», «Ricerca · chiavi mancanti», «postazione senza automazione»; «crepuscolo», «altezza massima», «pausa», «seeing», «chiavi», «Luna stanotte» (62% · primo quarto · piena); automazione di partenza «AM5 con tetto, sensore e pannello · EQ6-R con flat di cielo». Lo stato si legge anche da `?stato=`.
- **Restano scelte dell'utente** (non cambiate dalla brief): setup in tendina (v26.1) al posto delle linguette per montatura; telefono a elenco (v28.4, approvato), la linea verticale resta nel Tweak «telefono».
- **Dati simulati**: NGC 6960 nuovo progetto (AM5), M 31 con Hα e mosaico, seeing ora per ora, CH Cygni e SN 2026qd, Macchia Rossa alle 05:20. Con le ore mancanti di IC 1396 (5 h 40) stanotte M 31 non entra nel piano automatico: lo stato «pausa prima del meridiano» lo mostra a mano, al meridiano col flip.
- **Foglio di stile** (`old/astrolog.css`): numeri dei commenti col punto (coordinate, Bortle, scala SQM).

### v30.1 · Correzioni di Claude Code (20 ottobre 2026)
- **Crepuscolo nautico = dentro il nautico**: la banda stretta puo' cominciare dalla fine del civile, Sole sotto −6° (come Target Scheduler, ADR 0013). Supera la lettura «Sole sotto −12°» della v30.
- **Scelte di Marco**: postazione in tendina (v26.1) e telefono a elenco (v28.4). Escono la linguetta per montatura (sez. 1) e la linea verticale (sez. 12); tolto il Tweak «telefono».
- **Testi sul lessico dell'app**: «Nessun buio stanotte.» (senza «nessuna ora utile»); «sale fino a 59° alle 05:36» (al posto di «più alta possibile», che resta solo nella regola); «Nessun pianeta alto più di 30 gradi stanotte.»; errori dei campi «Un numero da {min} a {max}.», senza limiti «Un numero.». Gli altri testi della v30 sono approvati.


## v31 · Statistiche (20 ottobre 2026, brief di Claude Code v1, ADR 0024, 0020, 0022)

Pagina nuova: `pagine/Statistiche.dc.html` (desktop e telefono, `?formato=`, `?stato=`). Dati simulati in `componenti/dati-statistiche.js` (`ALstat`: sei anni a Cima Ekar, Casa, Passo Coe; oggi 30 settembre 2026). Le parole fra «» del brief restano proposte da approvare con Marco.

- **Testa**: titolo «Statistiche»; anni in pista (l'ultimo acceso) e «Tutto»; «Confronta con» (l'anno prima, «nessuno»), «Sito» (di partenza Cima Ekar, casa), «Setup» («Tutti» o uno). Sul telefono la pista, poi le tre tendine in fila che scorre, senza titolo grande (v28).
- **L'anno in un colpo** (carta protagonista): «20 su 27 notti buone», sotto «l'anno scorso 15 su 21»; quattro celle (notti uscite, ore integrate, pose, resa del buio) con «+4 · l'anno scorso 23», niente colore sul delta. Con l'anno in corso il confronto si ferma allo stesso giorno: riga «Confronto fino al 30 settembre, come il 2026.». Riga del seeing solo quando l'anno o il confronto toccano notti prima dell'app (12 marzo 2024).
- **Calendario**: settimane in colonna da lunedi', quattro gradini dell'accento per le ore (sotto 2, 2-4, 4-6, da 6), contorno pieno per la notte buona persa, futuro a filo. Il valore si legge nella riga sotto la griglia (al passaggio o al tocco), non in un riquadro: il calendario scorre e un riquadro verrebbe tagliato. In «Tutto» il calendario ha la sua pista degli anni. Sul telefono scorre dentro la carta e parte dalla fine.
- **Volumi**: barre per notte (in «Tutto» per mese) e cumulato sul giorno dell'anno, l'anno di confronto tratteggiato; il punto di oggi e la frase «al 30 set: 107 h · l'anno scorso 87 h» sopra il grafico. Il cambio di setup e' la prima notte di un setup nuovo: tratteggio verticale col nome.
- **Capacita'**: FWHM · HFD · eccentricita' (pista). Un punto per notte × setup; colore e forma per setup (cerchio, rombo, quadrato, triangolo; tinte fisse, non dell'accento), punto pieno l'anno, vuoto il confronto; barretta dal primo al terzo quartile (sotto 4 pose niente barretta); mediana mobile su 7 notti per setup, spezzata oltre 26 giorni. Legenda con la mediana dell'anno in ″ e px. Fra setup diversi non si mescola niente.
- **Stagioni**: anni × mesi con riga «media» e le quattro stagioni sotto; cinque gradini dell'accento, testo scelto per contrasto. FWHM con «Tutti» = il setup con piu' ore (la riga lo dice). Casella vuota «–» col perche' nella riga sotto («nessuna uscita», «seeing non archiviato prima del 12 marzo 2024», «deve ancora venire»). Sul telefono: pista degli anni e 12 righe con la media.
- **Per filtro**: barre impilate in HTML (servono le strisce dei filtri a piu' bande), il filtro con piu' ore in basso, totale sopra; tabellina filtro · ore · pose · notti.
- **Per setup**: una riga per setup in ordine di ore: ore, pose, oggetti, notti, FWHM mediana allo zenit (″ e px), «soprattutto nebulose, 81 % delle ore» con la barretta dei tipi.
- **Cielo del sito**: numero grande SQM mediano (Luna sotto −5°); SQM per mese con Luna sotto −5° (accento) e Luna su (grigio della Luna, tratteggio); curva per ora dalle 21 alle 05; «Bortle 3 · misurato su 84 notti».
- **Stati (Tweak `stato`)**: pieno; primo anno (2026 solo, niente confronto); zero frame (avviso con «Scansiona ora»); misure dei frame non ancora calcolate (Capacita' e Cielo con l'avviso, FWHM e SQM vuoti nelle Stagioni); sito senza meteo storico («Meteo storico in arrivo», niente contorni delle notti perse, «– · 6»); un setup solo (esce Per setup, Per filtro a tutta larghezza).
- **Numeri col punto** (v24.4.1): «alla 0.6 (ESO)», «21.77», «3.8″». Percentuali con lo spazio come nel brief («57 %»).
- **Link**: Statistiche si apre dalla barra, dal menu Altro del telefono, da Cerca e da «Statistiche ↗» della Dashboard.
- **Da chiedere a Claude Code**: il seeing mediano delle Stagioni e' delle notti uscite (qui) o di tutte le notti col meteo; se il confronto dell'anno in corso si ferma allo stesso giorno (qui si') o prende l'anno intero; cosa fa il calendario in «Tutto» (qui un anno alla volta).

### v31.1 · Correzioni alla prima consegna (20 ottobre 2026, brief v1.1 di Claude Code; Marco)

- **Approvati da Marco**: gradini del calendario a 2, 4 e 6 ore; FWHM del setup con piu' ore; il cielo diviso in SQM e Seeing; i testi nuovi della v31, con «Scansiona ora» -> «Scansiona», come nel resto dell'app.
- **Mesi x anni, piu' misure**: il selettore e' in due righe, sopra il gruppo «Cielo · Frame · Volumi», sotto le misure del gruppo. Cielo (dal meteo): Notti buone e uscite, Qualita' della notte (0-100), Seeing. Frame: FWHM, HFD (allo zenit, ″ nella casella, ″ e px nella riga del valore), Eccentricita', Stelle (per posa), Fondo cielo (ADU), SQM. Volumi: Ore integrate. In ogni casella la mediana del mese. Qualita' e seeing contano tutte le notti, le misure dei frame le notti uscite. FWHM, HFD, stelle e fondo dipendono dal setup: con «Tutti» si mostra il setup con piu' ore negli ultimi 12 mesi (sull'archivio intero vinceva il Newton, fermo dal 2024, e gli anni recenti restavano vuoti) e la riga sotto il titolo lo dice; negli anni senza quel setup la casella dice «nessuna uscita con {setup}». L'eccentricita' prende tutti i setup. Il colore va sempre dal peggio al meglio (piu' scuro = meglio; FWHM, HFD, eccentricita', fondo e seeing a rovescio).
- **Bortle del sito (ADR 0022)**: ultimi 12 mesi, solo frame col bias, Sole sotto −18°, Luna sotto −5°, oggetto sopra 30°; una mediana per notte, poi la mediana delle notti; serve che le notti cadano in almeno 6 mesi diversi. Se no: «Servono notti in 6 mesi diversi: finora {n} notti in {m} mesi.». La regola e' scritta in piccolo sotto.
- **Dati simulati**: stelle, fondo e il seeing delle notti senza uscita vengono da un secondo generatore, per non cambiare le notti della v31.

### v31.2 · Il setup lo sceglie l'utente (20 ottobre 2026, brief v1.2, scelta di Marco)

- Supera in v31.1 «con «Tutti» si mostra il setup con piu' ore negli ultimi 12 mesi»: la griglia mesi x anni segue la tendina «Setup» in testa. Un setup: solo le sue notti. «Tutti»: tutti i setup insieme, mediana su tutte le notti uscite, anche per FWHM, HFD, stelle e fondo. I px della FWHM e dell'HFD sono la mediana dei px notte per notte, ognuno con la scala del suo setup.
- Sotto la griglia, con «Tutti» e piu' di un setup, per FWHM, HFD, stelle e fondo: «Tutti i setup insieme: FWHM, stelle e fondo cambiano da un setup all'altro.» (testo da approvare).
- Approvati da Marco: «nessuna uscita con {setup}» (ora solo con un setup scelto) e la riga della regola del Bortle.

### v31.3 · Ritocchi di Marco sulla tavola (20 ottobre 2026)

- **Stagioni, Frame**: escono «Stelle» e «Fondo cielo»: dipendono troppo dall'oggetto ripreso. Restano FWHM, HFD, Eccentricità, SQM. La riga sotto diventa «Tutti i setup insieme: FWHM e HFD cambiano da un setup all'altro.» (da approvare).
- **Stagioni, Griglia · Linee**: un interruttore accanto ai gruppi. In Linee: una linea per anno sui 12 mesi; l'anno scelto (pista degli anni, di partenza quello in testa) in accento con i punti e il nome in fondo, la media tratteggiata, gli altri anni in grigio sottile. Al passaggio o al tocco su un mese (Marco): un riquadro corto col nome del mese e l'elenco anno · valore, dal più recente, l'anno scelto in grassetto, in fondo la media; niente frasi. Un tratteggio verticale segna il mese. Con «Notti buone e uscite» la linea porta le notti uscite. La legenda dei gradini esce, le stagioni restano.
- **L'anno in un colpo, celle** (corretto con Marco): niente linea dell'andamento, pesava. Sotto il numero solo il segno del trend (spezzata con la punta in su, in giù, o piatta) col delta «+4» / «−3» / «uguale» in verde o rosso (colori degli esiti, non dell'accento), e «l'anno scorso 23» in grigio. Il colore non è mai da solo: c'è il segno e il più o il meno. Senza confronto niente delta.
- **Animazioni**: le linee si disegnano da sinistra, le barre crescono dal basso, i quadretti del calendario e le caselle delle stagioni compaiono in sequenza; ogni carta parte quando entra nello schermo. Con «riduci movimento» niente animazioni.

### v31.4 · Un riquadro solo, corto, in tutta la pagina (20 ottobre 2026, Marco)

- Ogni valore al passaggio o al tocco si legge nello stesso riquadro scuro: in grassetto il titolo (giorno, mese, ora), sotto righe corte etichetta · valore, niente frasi. Vale per calendario, volumi, capacità, cielo (mese con Luna sotto e Luna su insieme), curva per ora, griglia e stagioni, linee, per filtro (tutta la barra: un filtro per riga e il totale).
- Calendario, griglia delle stagioni e filtri: il riquadro si aggancia alla casella; vicino al bordo alto della carta va sotto. Se il calendario scorre, il riquadro si chiude. Le righe sotto i grafici restano solo come indicazione («Passa sopra un giorno per vederne le ore.»).
- Casella senza dato: titolo e il perché in una riga («Ottobre 2021» · «nessuna uscita»).

### v31.5 · «filtri a banda stretta», mai «filtri stretti» (20 ottobre 2026, Marco)

- I filtri sono a banda larga o a banda stretta: a schermo sempre «filtri a banda stretta». Corretto in Statistiche (Cielo del sito) e in Misure dei frame (Luminosità del cielo). Il resto dell'app diceva già «banda stretta».

### v31.6 · Per setup: la FWHM in px davanti (20 ottobre 2026, Marco)

- In «Per setup» la FWHM si legge prima in px (numero in evidenza), poi in ″ con la scala del setup («2.4″ · 1.94″/px»). In fondo alla carta: «FWHM mediana allo zenit. In px si confronta fra setup diversi; in ″ no, dipende dalla scala.» (da approvare). Senza misure: «non ancora calcolata».
- Il confronto setup contro setup nel tempo (due setup sovrapposti in Capacità) resta fuori: da chiedere a Claude Code se l'app ha i dati.
- Ancora aperte per Claude Code: il calendario in «Tutto» (qui un anno alla volta), il seeing della griglia (qui tutte le notti), il confronto dell'anno in corso (qui fino allo stesso giorno).

### v31.7 · Risposte di Claude Code alla v31.6 (20 ottobre 2026, brief v1.3)

- **Confronta setup** (Marco): in Capacità «Confronta: Anni · Setup». Con Setup due tendine (di partenza i due setup con più ore nel periodo), stesso anno sovrapposto sul giorno dell'anno (in «Tutto» sul tempo), punto pieno il primo e vuoto il secondo, con le loro barrette e linee. In ″: la FWHM in ″ è il cielo più l'ottica e si confronta fra setup; i px restano nel riquadro al passaggio. La tendina Setup in testa qui non conta. Esce con un setup solo o senza misure.
- **Corretta al rovescio la v31.6**: in «Per setup» in evidenza la FWHM in ″, accanto px e scala. Riga: «FWHM mediana allo zenit. In ″ si confronta fra setup diversi; in px dipende dalla scala.» Griglia: «Tutti i setup insieme: in px FWHM e HFD cambiano da un setup all'altro.»
- **Bortle**: sotto il numero solo «Bortle 3 · misurato su {n} notti» (come Impostazioni); la regola nel riquadro della «i», al passaggio o al tocco. Corretto anche un difetto: una riga vecchia scavalcava la regola dell'ADR 0022 e il testo dei dati scarsi.
- **Confermati** (Marco): calendario in «Tutto» un anno alla volta; seeing della griglia su tutte le notti col meteo (il cielo del sito), misure dei frame sulle notti uscite; confronto allo stesso giorno con l'anno in corso, anno intero con «Tutto» o un anno finito.
- **Dati**: l'elenco della v31.6 è il contratto della rotta; per ora dati di prova.
- **Per setup** (Marco, v31.7.1): esce la riga «soprattutto nebulose, 81 % delle ore» con la barretta dei tipi. Restano ore, pose, oggetti, notti e FWHM.

### v31.8 · Controlli finali e consegna (20 ottobre 2026)

- Contrasto: il gradino 4 della griglia delle stagioni in chiaro (ambra, turchese, ghiaccio) era 4.3–4.4:1. Ora il testo della casella e' il migliore fra testo del tema, nero e bianco: minimo 4.78:1 in tutti i dieci temi. Tutto il resto passa.
- Sei stati × desktop e telefono: nessuna carta fuori colonna, nessun errore. Telefono: piste 38 px dentro 44 (v28); quadretti del calendario da 14 px accettati (tocco col riquadro, carta che scorre).
- Nota di consegna: `docs/per-claude-code-statistiche.md`.
