# AstroLog — cronologia

## v58 — Transiti con la mappa — 25/10/2026

- v58.6 (26/10): consegna `docs/per-claude-code-porting.md`; Sistema col vetro e i Planner su desktop e telefono; bottoni del cielo profondo sulle classi.
- v58.5 (26/10): pulizia per Claude Code. Usciti PlannerSolare, PlannerEventi, Cattura; codice spento tolto in 12 file; token e classi del vetro; COMPONENTI.md coi due Planner nuovi; due documenti chiusi in archivio.
- v58.4: il bordo del foglio anche nel cielo profondo; «Come si usa» in Sistema solare ed Eventi.

- v58.3: Sequenza per SharpCap nel Sistema solare e negli Eventi, con «Esporta per SharpCap».

- Disco · Mappa per i transiti di ISS, Tiangong e Hubble; `Mappa del transito.html` (OpenStreetMap) e `componenti/transiti.js`.
- Dove metterti: stato del sito, piano B, tre posti con «Apri in Google Maps ↗». Orologio del computer, «Aggiungi al calendario».

## v57 — Planner, Sistema solare ed Eventi — 25/10/2026

- `PlannerSolare2` e `PlannerEventi2` nella forma del cielo profondo: cielo largo e colonna di 424 px sul desktop, cielo a tutto schermo e foglio a tre altezze sul telefono.
- Dati allineati al Piano della notte (ISS 03:41:12, Macchia Rossa 05:20, riprese salvate). Lune di Giove, nuovi eventi, numeri con la virgola.
- v57.1: finestra utile, le prossime notti, frame · posa · fps calcolati; la colonna del Sistema solare scorre.
- Tolte le forme A/B degli Eventi. `?pianifica=` per le tavole.

## v55–v56 — Tutte le pagine allineate — 25/10/2026

- Pagina per pagina, desktop e telefono: Dashboard, Notti (e la finestra della notte), Archivio (anteprime per produzione), Progetti (righe come la Dashboard, azioni con «⋯»), Statistiche, Meteo, Piano della notte, Selezione dei frame (soglie solo a valore, soglia dal grafico, «cambiata qui»), Misure dei frame, Attrezzatura, Da confermare, Impostazioni, Planner.
- Regole uniche: linguette sottili, tendine, icone per la vista, anello sulla scelta, tondi ↗, un solo interruttore; tolto il codice spento.

## v54 — Desktop con le regole del telefono — 25/10/2026

- Linguette sottili, anello sulla cosa scelta, niente titoli grandi, Misure dei frame con un titolo solo. Dettagli in DECISIONI v54.

## v52–v53 — Telefono chiuso — 25/10/2026

- Planner telefono: viste a icone nella colonna di destra, legenda in un tondo, «Stanotte · Le mie riprese» in alto, comandi che si ritirano mentre si muove il cielo, «sulla carta» come interruttore; via + e −.
- Misure dei frame nel telaio; tendine del telefono tutte a pillola; un mattone per funzione (tondi 44, segni 22, pillole); frecce ▾.
- Statistiche: Stagioni, Calendario e Capacità con le tendine su una riga; Volumi, nome del setup che non esce.
- Controllo contrasto 2 modi × 5 accenti; banco `Prova tema`.

## v51 — Il telefono coerente — 25/10/2026

- Telaio del telefono: la bolla di vetro in tutte le pagine (via la barra a cinque icone; `barra="classica"` per confronto); in alto titolo della pagina e sito in tenue, tondi di vetro; niente bollino in Da confermare.
- Titoli doppi via (Selezione, Attrezzatura, Impostazioni, Meteo). Da confermare: Applica nel vetro accanto alla bolla.
- Striscia: la notte scelta con l'anello; «+ Proposte» col filo; «Parti da», «Luna · Sole» in linguette sottili.
- Esiti «✓ buona» col verde fisso (Dashboard, Meteo).
- Dashboard una riga sotto «9 ore»; Statistiche «dati simulati»; Notti ordine e avvisi su due righe; Piano della notte il modo in tendina; Archivio anteprime 3:2.

## v50 — La barra di vetro sul telefono (prova) — 25/10/2026

- `Telaio`: barra `vetro` sul telefono (bolla delle pagine e vetro con riassunto e azione), accesa con `barra="vetro"` o `?barra=vetro`; senza, tutto come prima.
- Nuova tavola `Telefono vetro`: undici pagine col vetro (1a–1k) e le scelte nelle carte (2a–2d).
- Vetro: mentre si scorre resta solo la bolla.
- Linguette sottili (2b) sul telefono in Dashboard, Meteo, Archivio, Notti, Progetti, Piano della notte, Statistiche, Planner (`al-scelta--sottili`).

## v49 — Il Planner portato — 25/10/2026

- Planner, fase di Aladin del cielo profondo: la forma di `PianoDesktop` e `PianoTelefono` coi dati veri (Aladin, `corDi`, `campoDi`, `anno`, `notte`, `candDi`, `oreDi`, `PROG`, soglie).
- Telaio: opzione `pieno` per il desktop a tutto schermo.
- Soglie: nuova `planner.stagione` (67 %); Impostazioni › Planner mostra le due soglie della stagione.

## v45 — Il Planner come progetto — 24/10/2026

- Tavole `Planner telefono` (componente `PianoTelefono`) e `Planner desktop` (componente `PianoDesktop`), approvate: cielo con setup, righello e mosaico; Stagione al centro, Stanotte come informazione, Pose con posa per filtro e priorita'; Salva con Annulla; cinque stati difficili.
- Rassegne `Telefono comandi` e `Telaio vivo` (comandi e telaio sul telefono).
- Da Trova si vola sempre prima di aprire il piano.

## v44 — Il piano a due colonne — 24/10/2026

- Planner, fase di Aladin: immagine a sinistra con rotazione e mosaico in una barra sotto, colonna a destra con Oggetto, Stanotte, Setup, Come riprendere, Periodo migliore e Salva fisso in fondo. Telefono: immagine sopra, quattro schede sotto.
- Nuovo `PianoColonna`; cancellati `PianoStrumenti` e `CieloPiano4`.

## v43 — Il piano rifatto — 24/10/2026

- Planner, fase di Aladin rifatta da zero: l'immagine occupa tutta la carta; una barra verticale «Strumenti» si apre con un clic e dà Setup, Campo, Pose, Notte, Immagine, Salva; un pannello alla volta (sul telefono un foglio con le stesse schede). Clic sull'immagine o Esc chiude il pannello.
- Nel piano spariscono le carte sotto (Stanotte, Periodo migliore: ora nello strumento Notte) e la riga dei modi: niente da scorrere.
- Nuovo componente `PianoStrumenti` al posto di `CieloPiano4` nel Planner.

## v42.2 — Proposte per il piano — 24/10/2026

- Planner: da Trova (Invio o clic) si vola verso l'oggetto, poi si apre il piano.
- Nuova tavola `Planner proposte`: 1a Plancia (griglia bento fissa) e 1b Mirino e console (vista piena, console in basso), per cielo profondo, sistema solare ed eventi, desktop e telefono. Da scegliere.

## v42.1 — La carta si chiama Planner — 24/10/2026

- `Carta del cielo v6` → `Planner`; cancellati la prima Carta del cielo e `CieloPiano`.

## v42 — Il Planner esce — 24/10/2026

- La Carta del cielo v6 prende il posto del Planner: link e menu aggiornati; cancellati Planner, Carta del cielo v2–v5, CieloPiano2 e CieloPiano3.
- v6: foglio da tirare su sul telefono, immagine di Aladin in due tempi, frecce sull'immagine, una curva sola in Aladin, «Setup virtuale» anche in Sistema solare.

## v41 — Carta del cielo v6 — 24/10/2026

- Nuova pagina `Carta del cielo v6`: il cielo per cercare (senza immagini), Aladin piatto e trascinabile per inquadrare, il piano nella scheda a destra. Nuovo `componenti/CieloPiano4`; `cupola.js`: opzione `immagini`.

## v40 — Carta del cielo v5 — 24/10/2026

- Nuova pagina `Carta del cielo v5` (da v4): cercare e inquadrare sono due momenti; nell'inquadratura i comandi del cielo spariscono e setup, rotazione e pannelli stanno sull'immagine (Tweak «Comandi»: fascia in basso o colonna a sinistra). Nuovo `componenti/CieloPiano3`.

## v39.1 — Carta del cielo v4, fase 2 — 24/10/2026

- Il cielo profondo ha tutto il Planner: provvisoria completa, secondo setup a confronto, rotazione a 1°, rettangolo trascinabile, scelta dell'immagine, ore al minuto, salvataggio nella pagina, ritorno da Progetti, ricerca online, meridiano, telefono a passi, stati nei Tweaks. B e' la disposizione predefinita.
- Nuovo `componenti/CieloPiano2`; aggiunte a `cupola.js`, `CieloNotte` (meridiano) e `CieloCriteri` (archivio vuoto).

## v39 — Carta del cielo v4, fase 1 — 24/10/2026

- Nuova pagina `Carta del cielo v4` (da v3): scelta «Cielo profondo · Sistema solare · Eventi»; Sistema solare ed Eventi coi componenti del Planner. Due disposizioni nei Tweaks (A il cielo resta, B la pagina cambia). v3 resta com'e'.

## v32.2 — Riordino, seconda passata: Selezione dei frame, Misure dei frame, MisureFrame — 24/10/2026

- Gli stati che passavano colori del tema nello stile della pagina sono varianti di classe nel foglio (aria-selected, aria-checked, aria-pressed, aria-expanded o una classe `--…`); in pagina restano posizioni, larghezze in %, la luminosita' del frame simulato, il colore di un filtro.
- Token nuovi: `--accento-50`, `--accento-14`, `--accento-tessera` (per modo × accento), `--su-immagine-testo`, `--immagine-schermo`, `--immagine-velo`, `--immagine-tasto`, `--immagine-male`; col contrasto accanto.
- La tabella L esce dalle tre pagine: tutto nel foglio sotto `[data-formato="telefono"]`.
- PillolaScelta: `ruolo="radio"`, forme linguette e interruttore, `classe`, `href`. Pillola: `forma="segno"`, esiti avviso e spenta, `classe`. Finestra: `larghezza="schermo"`, `testa="no"`. Nuovi: Avanzamento (anche in Progetti), Quartili.
- Bottoni: `<button class="al-bottone">`; gli 8 di MisureFrame prendono al-bottone. `button.al-bottone` nel foglio.
- Tavola degli stati della Selezione: «le soglie del corredo» → «le soglie del setup».
- A schermo uguale: impronte confrontate con `screenshots/prima-passata2/` (misure, posizioni, colori). Docs: COMPONENTI.md, per-claude-code-porting.md.

## v36.4 — Misure dei frame, tre correzioni di Claude Code — 23/10/2026

- Catture finali della Selezione dei frame: 46 stati (1202–1247) in `screenshots/finali/`, elenco aggiornato, la pagina aggiunta a `pagine/Cattura.dc.html`.

- Ultimi ritocchi (stesso giorno): `bortleDi` con `sqm > x` (19.50 e' Bortle 6, 21.25 e' Bortle 5). FWHM d'esempio sopra 2 px nella scala del loro setup: Misure dei frame (Archivio FRA400 4,0 · 4,3 · 4,7″, Askar 103 2,9 · 3,2 · 3,6″, RedCat 7,8 · 8,3 · 9,0″; stati «FWHM 2.1 px · HFD 2.9 px», «FWHM 4.2″ · 2.2 px», «FWHM 4.1″ · 2.1 px»), il generatore di MisureFrame (seeing moltiplicato per max(1, 2,15 × scala / 2,5)). Selezione dei frame: HFD = FWHM × 1,36 come in MisureFrame, HFD d'esempio alzata (FRA400 L 5,6″ ⇒ FWHM circa 4,1″, 2,1 px; Askar 103 L 4,1″ ⇒ FWHM 3,0″, 2,2 px).

- `componenti/soglie.js`: `snrBasso`, `snrBassoOgg`, `hfdAltaOgg` a mediana ± 2,5 × 1,4826 × MAD (Leys et al. 2013, ADR 0022; Marco), come le soglie della Selezione dei frame; via il richiamo al SubframeSelector. Il minimo di 10 frame e' «scelta di Marco», non di N.I.N.A.
- SQM ↔ Bortle torna la tabella di ASTAP (`bortle()` in unit_sqm.pas, da Clear Dark Sky): 1 da 21.99, 2 da 21.89, 3 da 21.69, 4 da 21.25, 5 da 19.50, 6 da 18.94, 7 da 18.38, 8 da 17.80, 9 sotto; il 4.5 di ASTAP vale 5. Annulla la correzione del 21/10. I nomi delle classi del Primo avvio non leggono gli SQM: restano.

## v36.3 — Selezione dei frame, ritocchi di Claude Code — 23/10/2026

- Eccentricità accesa parte da > 0,6 (scelta di Marco). «In scartate». Il motivo delle soglie dalla mediana dice il valore calcolato («FWHM > mediana + 2,5 MAD (3.42″)»). Il cambio di tipo di una riga accende «! modifiche da applicare».
- Ogni soglia sceglie «dalla mediana · valore» (l'utente).
- Consegna `docs/per-claude-code-selezione-frame.md` v36.3: testi allineati (gruppo con posa e guadagno, altezza dall'app, velocità, mosaico 3 × 3, refusi).

## v36.2 — Selezione dei frame, le correzioni di Claude Code — 23/10/2026

- Partenze delle soglie uguali per ogni setup (2,5 MAD scalato, Leys et al. 2013; eccentricità e fondo e altezza spenti); FWHM dalla mediana o a valore, con «sotto il limite del setup: scarterebbe tutto»; «al limite» solo dalla mediana, entro 1 MAD; FWHM simulata ≥ 2 px.
- Gruppo con posa e guadagno; M 31 L in due pose nel simulato; pillole «filtro · posa»; «Per filtro e posa» nel progetto.
- «Setup» al posto di «corredo»; «scartate» nella radice dell'archivio; Elimina col cestino e senza (NAS), due stati nuovi nelle Tweaks e nella tavola.
- Velocità di Riproduci (0,1–2 s), angoli e bordi 3 × 3, la riga del MAD in «Come funzionano». Classi `al-sel2__…` per i pochi stili nuovi.
- Consegna `docs/per-claude-code-selezione-frame.md` aggiornata (v36.2).

## v36.1 — Selezione dei frame promossa — 23/10/2026

- La pagina rifatta in sette giri con l'utente e promossa a pagina fissa (vedi DECISIONI v36, dai giri in giu'): Un progetto in corso · Delle notti (via l'archivio, via il setup); striscia «Da scartare»; riquadro del frame con l'immagine simulata, lo stretch, Intero · Centro · Angoli, schermo intero, ✕ ▶ ✓; grafico «Frame per frame» come il riepilogo (barre o linee, per ora o per valore, seconda misura, un filtro alla volta, finestra oltre circa 190 frame); soglie per corredo e filtro (FWHM, Eccentricità, Stelle, Altezza col valore; SNR, Fondo dalla mediana in MAD; formula) che valgono dopo Applica. Telefono solo per guardare. Usciti riepilogo, tabella dei frame, «proposto» e «Applica le proposte», espressioni a parole.
- Classi: lo style= della pagina in `al-sel__…` (172 regole in fondo a `pagine/astrolog.css`, con `strumenti/a-classi.js`); inline restano i valori dai dati.
- Tavola degli stati `pagine/Selezione dei frame stati.dc.html`: dieci stati desktop (esempio, appena aperto, misura in corso, notte da misurare, nessun progetto in corso, modifiche da applicare, formula con errore, dopo lo spostamento, NAS in sola lettura, Impostazioni) e tre del telefono. Tweaks «stato» coi quattro nuovi.
- Ingressi: voce in «Altro» (Menu), «Seleziona i frame ↗» nella scheda dei progetti in corso (Progetti) e nel riepilogo della notte (MisureFrame, parametro `selezione`). La pagina legge `?progetto=`, `?notte=`, `?modo=`, `?accento=`.
- Contrasto controllato in scuro e chiaro coi cinque accenti. Per Claude Code: `docs/per-claude-code-selezione-frame.md`.

## v36 — Selezione dei frame — 23/10/2026

- Pagina nuova `pagine/Selezione dei frame.dc.html` (brief di Claude Code del 23/10, ADR 0032): scelta del gruppo (un gruppo, una notte, un setup), riepilogo (frame tenuti, integrazione, stati), grafico nel tempo notte per notte e distribuzione collegati alla tabella, tabella ordinabile divisa per notte, «In scartati», finestre di spostamento e di cancellazione, barra della selezione. Telefono: la tabella diventa una lista.
- Nella stessa pagina la vista `Impostazioni › Selezione dei frame` (`?vista=regole` o Tweaks «vista»): soglie per misura, espressioni con l'anteprima, «Come funzionano».
- Tweaks e indirizzo: `?stato=` (esempio, appena aperto, misura in corso, dopo lo spostamento), `?errore=` (cartella in sola lettura (NAS), disco staccato, file aperto da un altro programma), `?anteprima=no` (telefono senza cornice, per le catture).
- Catture di lavoro in `screenshots/selezione/`.

## v35 — Carta del cielo v3: il planner completo sotto la carta — 22/10/2026

- `pagine/Carta del cielo v3.dc.html` (da v2, disposizione A; v2 resta per il confronto). Sotto la carta: Stanotte (curva dell'oggetto scelto), Periodo migliore (12 mesi), Il piano. La lista non sta piu' sotto: si apre sulla carta, sotto la ricerca, dalle liste pronte o da «Lista» nella striscia; sul telefono e' una carta che si chiude.
- Criteri completi come nel Planner: cielo, direzione, tipo, catalogo (Messier, NGC, IC, Sh2, altri), archivio (tutti, mai ripresi, gia' ripresi), entra nel campo del piano, altri criteri (magnitudine, luminosita' superficiale, dimensione, Dec, RA, costellazione), ordine (ore utili, altezza, catalogo, dimensione, magnitudine, luminosita' superficiale, ora del piu' alto). «Mostra la lista» dai criteri.
- Scheda dell'oggetto: tolto «Planner ↗» (restano Pianifica, Vola fin li', Archivio ↗).
- Il piano: posa del frame per filtro, con il numero di frame.
- Ritocco: il piano prima di Stanotte e Periodo migliore, sempre visibile; scegliere un oggetto lo mette nel piano e mostra l'inquadratura; il volo arriva inquadrato; Pianifica scorre al piano.
- Mattone nuovo `componenti/CieloNotte` (Stanotte + Periodo migliore); `CieloCriteri` coi criteri nuovi; `CieloLista` senza schede quando `liste` e' vuoto.

## v34 — Carta del cielo come Planner, due disposizioni — 22/10/2026

- `pagine/Carta del cielo v2.dc.html`: la carta con la ricerca coi criteri, tre liste (Migliori di stanotte, Progetti in corso, Le mie riprese) coi numeri sulla carta, e il piano dell'oggetto (attrezzatura o provvisoria, inquadratura e mosaico, filtri e ore, Salva come progetto). Due disposizioni nei Tweaks o con `?disp=b`: A sotto la carta, B pannello sulla carta. Telefono uguale per tutte e due. Tolte le carte «Alti alle …» e «Luna e pianeti».
- Mattoni nuovi: `componenti/CieloLista`, `CieloPiano`, `CieloCriteri` (servono in tre posti: carta A, pannello B, telefono).
- Motore (`cupola.js`): filo dell'altezza dell'oggetto scelto (dallo zenit all'orizzonte, si disegna nel volo), rettangoli del sensore e del mosaico ruotati, segni numerati della lista, `aggiungi()` per gli oggetti fuori catalogo (Sh2-155), volo con campo voluto, spostamento del centro per il pannello B, immagine di Aladin larga quanto il campo da inquadrare.
- Foglio: `--cielo-accento` e `--cielo-accento-testo` (l'accento sopra il cielo, uguale nei due modi). Carta del cielo e v2: viste, letture, livelli accesi, «Adesso», cursore della barra, selezione e segni nel colore dell'accento.
- Carta del cielo: livello «Pianeti, Luna e Sole»; Via Lattea più forte (0,52, nelle riprese 0,26).
- Indirizzo in più: `?disp=`, `?lista=`, `?piano=`.

## v33 — Carta del cielo, prima versione — 22/10/2026

- Nuova pagina `pagine/Carta del cielo.dc.html` (voce «Carta del cielo» di Altro, ora col link): il cielo in 3D da Cima Ekar, tre viste (Dentro, Cupola, Sfera), due letture (Stanotte, Le mie riprese), barra del cielo per l'ora, ricerca col volo verso l'oggetto e immagine di Aladin all'arrivo, scheda dell'oggetto, due carte sotto (Alti alle … / Luna e pianeti; Dove ho ripreso di più / Per costellazione). Desktop e telefono.
- `componenti/cupola.js`: il motore (three.js 0.160 dal CDN). `componenti/dati-cielo.js` (15 544 stelle fino alla magnitudine 7, 13 889 oggetti NGC/IC/Messier, linee e nomi italiani delle costellazioni, 65 stelle coi nomi) e `componenti/via-lattea.png`, generati una volta da d3-celestial.
- Indirizzo per tavole e catture: `?vista=`, `?livello=`, `?sel=`, `?ora=`, `?vola=1`.

## v32 — Riordino (chiuso) — 20–21/10/2026

- Catture finali in `screenshots/finali/` (1202 stati, desktop e telefono, scuro e chiaro, stesso `_elenco.json`). Uscite `screenshots/prima-riordino/` e `dopo-riordino/`.
- Colori dei tipi nel Piano della notte (`--tipo-*`, `t.tipi`).
- `docs/per-claude-code-porting.md`: riordino finito, cosa e' cambiato rispetto alla brief v1, dove stanno le catture.
- Controllo finale del codice morto: nessuna classe e nessun token del foglio inutilizzati; tolto `AL.strisce` dall'esportazione di `tema.js` (resta interno a `tinta`).

- Risposte di Marco: seeing di giorno come la notte; campi del Planner allargati; `--male` chiaro #bf4232; segmentato piccolo a 44 sul telefono; Archivio sul telefono su una riga. Componenti sulle classi (686 regole `al-c-…`, sez. 2); confronto con la copia ferma: nessuna differenza.
- Catture dopo il riordino (`screenshots/dopo-riordino/`, 1202 stati) e confronto completo con quelle di prima; elenco delle differenze in DECISIONI v32. Segmentato: barra di scorrimento nascosta (sul telefono compariva in Archivio e Notti). Uscita `screenshots/tappe/`.
- Pagine sulle classi: lo `style=` di 15 pagine e di Sistema nel foglio, sez. 3 (`al-<pagina>__…`, 2 200 regole circa); inline solo i valori dai dati. Strumento `strumenti/a-classi.js`.
- «Senza seeing» accanto al punteggio: Meteo (senza chiave, chiave non valida o appena messa, parziale), Dashboard (stato nuovo «seeing senza chiave»), Notti (notti passate), Statistiche (notti prima dell'app). `soglie.senzaRiga`, `senzaTutte`, `senzaPassate`.
- Foglio rifatto sulle classi v32; Sistema sulle classi; tavole degli stati e Telefono coi token `--tavola-*`.
- Usciti: `pagine/foglio-v17.css`, `old/` (95 file).
- Catture prima del riordino (`screenshots/prima-riordino/`, 1202 stati) e copia ferma delle pagine; `strumenti/Confronto.html` confronta prima e dopo elemento per elemento.
- `pagine/astrolog.css` v32: token dei due modi e dei cinque accenti generati da `tema.js`, col contrasto; nuovi token per cielo, Luna, Sole, corpi, setup a confronto, strumenti, raggi, durate. Nessun colore esadecimale nelle pagine e nei componenti.
- Unificati, con le classi nel foglio: Bottone (150 bottoni), Scelta (PillolaScelta, segmentato, linguette: 23 gruppi a mano), Campo e tendina (90 campi e Modulo), Riquadro (tutti i grafici), Quartili, Pillola, Segno, Pannello.
- Nuovi: Finestra (Aggiungi oggetto, Prima di salvare, il foglio del Piano sul telefono), SezioneServizi (Impostazioni: Servizi, Scansioni, Diagnostica, Backup).
- Formato della pagina in un posto solo (`AL.formatoScelto`, `AL.telefono`).
- Correzioni della brief, sez. 6: nebbia, trasparenza, fattori mancanti, «culmina» da 30°, Produzioni, flat, il nome di Marco fuori, oggetto, frame, V50, N.I.N.A., crepuscolo, scansione interrotta e bloccata, Archivio senza oggetti identificati e non risolti, Da confermare, Piano, MisureFrame, Riepilogo (SNR per produzione), Notti stati, Dashboard stati, tavola Telefono.
- Una tabella sola SQM ↔ Bortle (quella dell'app).
- Usciti: Meteo v4, docs/proposte, catture di lavoro vecchie, `verdetto`, `okta`, `oreSerene`, le varianti di prova della Luna, `archivio` di dati.js, stelle/fondo/tipo per notte, `pesaT`. I `per-claude-code-*.md` risposti in `docs/archivio/`.
- Documenti: `docs/COMPONENTI.md`, `docs/per-claude-code-porting.md`.

## v31.8 — Statistiche, controlli e consegna — 20/10/2026

- Contrasto della griglia delle stagioni corretto nel modo chiaro. Controlli dei sei stati, desktop e telefono.
- Nota per Claude Code: `docs/per-claude-code-statistiche.md`.

## v31.7 — Statistiche, risposte di Claude Code — 20/10/2026

- Capacità: «Confronta: Anni · Setup», due setup sovrapposti in ″.
- Per setup e griglia: ″ in evidenza, testi corretti. Bortle col riquadro della «i».

## v31.6 — Statistiche, setup a confronto — 20/10/2026

- Per setup: FWHM in px in evidenza, ″ e scala accanto, riga su cosa si confronta.

## v31.5 — Parole — 20/10/2026

- «filtri stretti» → «filtri a banda stretta» in Statistiche e Misure dei frame.

## v31.4 — Statistiche, riquadri corti — 20/10/2026

- Un riquadro unico in tutta la pagina: titolo e righe etichetta · valore, al passaggio o al tocco.

## v31.3 — Statistiche, ritocchi — 20/10/2026

- Stagioni: fuori Stelle e Fondo cielo; interruttore Griglia · Linee.
- Celle dell'anno: segno del trend (su, giù, piatto) col delta, verde o rosso.
- Animazioni d'ingresso dei grafici, quando la carta entra nello schermo.

## v31.2 — Statistiche, il setup dalla tendina — 20/10/2026

- Mesi x anni: niente più «setup con più ore»; la griglia segue la tendina Setup, «Tutti» = tutti insieme, con la riga sotto.

## v31.1 — Correzioni alle Statistiche — 20/10/2026

- Mesi x anni: selettore in «Cielo · Frame · Volumi», misure nuove (qualità, HFD, eccentricità, stelle, fondo cielo), mediana del mese, setup con più ore dove conta.
- Bortle del sito con la regola dell'ADR 0022 (12 mesi, 6 mesi diversi, frame col bias) e il testo dei dati scarsi. «Scansiona ora» → «Scansiona».

## v31 — Statistiche — 20/10/2026

- Pagina nuova `Statistiche` dalla brief v1 di Claude Code: testa con anni, confronto, sito e setup; l'anno in un colpo; calendario delle notti; volumi e cumulato; capacità (FWHM, HFD, eccentricità); stagioni mesi × anni; per filtro; per setup; cielo del sito. Desktop e telefono, sei stati nel Tweak.
- `componenti/dati-statistiche.js`: sei anni simulati, tre siti, quattro setup.
- Telaio, menu Altro, Cerca e Dashboard aprono Statistiche.

## v30.1 — Correzioni alla v30 — 20/10/2026

- Piano: banda stretta dal crepuscolo nautico = Sole sotto −6°; via la linea verticale del telefono (e il Tweak); testi «Nessun buio stanotte.», «sale fino a …», «Nessun pianeta alto più di … gradi stanotte.». Impostazioni: errori «Un numero da … a ….» / «Un numero.».

## v30 — Piano della notte completo — 20/10/2026

- Piano della notte: «Completa il piano» · «Rifai il piano» con regole scritte e il perché dell'ora sul blocco; filtri ordinati dalla Luna per bersaglio; crepuscolo nautico per la banda stretta, altezza massima, pausa prima del meridiano, flat (pannello o cielo), mosaico deep sky, campagne AAVSO e supernove; nuovi stati e Tweaks.
- `soglie.js`: Luna per bersaglio (`serveLuna`, `lunaPassa`), chiavi `luna.bersaglio`, `planner.crep`, `planner.altMax`, `planner.pausa`, `flat.*`, `ricerca.*`; via `planner.lun`; nuvole al 25% buone.
- Impostazioni: Luna per bersaglio con la curva, La notte del piano, Ricerca, Flat in Automazione. Planner: distanza dalla Luna dalla formula.
- Dashboard: «limita … · qualità fino a …». Meteo: «ore utili» nello stato senza buio. Meteo stati: un documento solo. `old/astrolog.css`: numeri col punto.

## v29.1 — Il verdetto torna dal punteggio — 20/10/2026

- Decisione di Marco, supera il contratto: qualità 0-100 coi pesi, verdetto da 70 / 40, ore utili da 60, curva della qualità e racconto con cosa limita. Meteo, Dashboard, Notti, Riepilogo. Resta il resto della v29. Documento per Claude Code: `per-claude-code-meteo-verdetto.md`.

## v29 — Il contratto del meteo — 20/10/2026

- Verdetto solo dalle nuvole in okta, ore utili = ore di buio serene («dalle 21 alle 04, 7 ore»), Luna 25 % · 50 % · sopra −5° in tutta l'app. `soglie.js`: `verdetto`, `oreSerene`, `intervallo`, `mostra`, `lunaNotte`.
- Meteo: «Pesa accanto», due fattori e «Altri N fattori», carte in ordine fisso con nuvole basse, medie e picchi calcolati, grafico con le sole nubi, tratto sereno, umidità e una misura a destra col giudizio, carta fermata su un'ora con ×. Stato «seeing, chiave appena messa». Copia di prima: `Meteo v4`.
- Dashboard, Notti, Riepilogo, Impostazioni (Luna −5°) allineati. Tavola Meteo stati aggiornata.
- Ritocchi: torna il racconto della notte (verdetto dalle nuvole), via «Pesa accanto» e il tratto sereno, curva delle nuvole totali come in Dashboard.

## v28.4 — Piano della notte sul telefono, a elenco — 19/10/2026

- Striscia orizzontale della notte e piano in righe in ordine d'ora; la linea verticale resta nel Tweak «telefono». Tavola `Piano della notte telefono`.

## v28.3 — Ritocchi del telefono — 19/10/2026

- Dashboard: una notte sola, le altre si aprono. Meteo: carte della stessa altezza, «Come va la notte» coi momenti che contano. Riepilogo: menu «Vista» nei grafici dei frame, formato dall'indirizzo. Planner: «Setup di prova» piccolo.

## v28.2 — Il telefono più leggero — 19/10/2026

- Pulsanti piccoli e ritorni a testo: Dashboard (ore in cima, viste in fondo), Meteo (modello e ↻ nel titolo), Progetti (scheda affiancata, scelta), Piano della notte, Impostazioni (indice delle sezioni), Notti. Cerca con progetti, impostazioni e le pagine nuove. Tavola Telefono con tredici pagine.

## v28.1 — Planner e Notti sul telefono, stati di Progetti — 19/10/2026

- Planner: pista dei tre modi + «⋯» del setup in testa sul telefono. Notti: Mese + Criteri, pista delle notti, righe di stato nel conto. Ritocchi da controllo in Progetti (Modifica) e Piano della notte (setup nell'accento). Tavola `Progetti stati` (cinque stati) e documento per Claude Code su Progetti.

## v28 — La testa del telefono — 19/10/2026

- Tre tipi di testa (pista, cerca, fila che scorre) con le stesse misure. Fatti Archivio, Progetti, Impostazioni.

## v27.8 — Progetti completi — 19/10/2026

- Progetti: Modifica e Rinquadra (con le ore), calendario per tutti, cerca e ordine. Planner Sistema solare: Salva come progetto.

## v27.3 — Progetti rivisti — 19/10/2026

- Anelli nel colore del gruppo e ✓ oltre il 100%; righe corte; gruppi pieghevoli; 28 finiti dalla prima scansione; gruppo Sistema solare con la sua scheda; legame col Piano della notte; notti riprese; misure a tessere. Link fra le pagine (menu, barra del telefono, Dashboard, Notti).

## v27 — Piano della notte: linguette, Sistema solare, postazione, tempi — 19/10/2026

- Piano della notte: Deep sky (con le comete) · Sistema solare (Notte · Giorno, mosaici, export SharpCap) · Ricerca; conto del blocco; Avvio e Chiusura coi passi; ruota dal setup; conflitto del margine prima di un evento fisso; quattro stati nuovi e due Tweaks.
- Impostazioni: tempi in tre gruppi nella linguetta Planner, linguetta Automazione per postazione. Registro: `planner.tempi`, `automazione.*`.

## v26.4 — Impostazioni collegate — 19/10/2026

- Registro delle impostazioni in `soglie.js`; Planner, Sistema solare, Piano della notte, Dashboard, Progetti e Meteo leggono le soglie dalle Impostazioni. Documento per Claude Code.

## v26.3 — Impostazioni complete — 19/10/2026

- Otto linguette: Generale, Siti, Cartelle e scansione, Meteo, ASTAP, Luna, Planner, Piano della notte; soglie del Planner modificabili con partenza e fonte.

## v26.2 — Impostazioni a linguette — 19/10/2026

- Sito e orizzonte · Luna · Planner · Piano della notte, una alla volta; tempi della notte in carta propria; telefono con linguette che scorrono.

## v26.1 — Piano della notte, ritocchi — 19/10/2026

- Setup in tendina, modo piccolo accanto; Completa e Rifai nella riga del titolo; fase della Luna sulla corsia; blocchi stretti col nome solo; legenda corta; cambio d'esempio 10 min.

## v26 — Piano della notte completo, la Luna in tutta l'app — 19/10/2026

- Piano della notte: modi Fotografia (Deep sky · Sistema solare, comete) e Ricerca (esopianeti, NEO, variabili, Criteri), Completa / Rifai con Annulla, avvio, cambi, flip e chiusura dai sette tempi della notte, orizzonte del sito, conflitti nuovi, dodici stati nei Tweaks, telefono.
- La regola della Luna diventa un'impostazione (25% · 50% · sopra l'orizzonte): Impostazioni col gruppo «Luna» e i «Tempi della notte»; `soglie.js` la legge per Meteo, Dashboard, Planner e Piano della notte, ognuna col Tweak «luna».

## v25 — Piano della notte — 19/10/2026

- Pagina nuova `Piano della notte`: proposte e eventi a sinistra, linea del tempo con fasce, Luna, ripresa, meteo, blocchi trascinabili, cambi e conflitti; totali ed export per N.I.N.A. con conferma; sette stati nei Tweaks; telefono con linea verticale e fogli dal basso. Voce nel menu Altro; riga «Tempo di cambio fra due bersagli» nelle Impostazioni.

## v24.4.1 — Frasi, ultimi ritocchi — 19/10/2026

- Numeri SI: decimali e coordinate col punto, migliaia con lo spazio sottile da 10 000. Setup «ottica · camera» in Misure dei frame, grandezza dell'eclisse di Luna senza sito, chiave Meteoblue senza «API» e «gratuita», «integrazione» minuscola nelle colonne, «Seeing: meteoblue» nei crediti.

## v24.4 — Le frasi — 19/10/2026

- Tutte le frasi a schermo corrette: «Deep sky», «Criteri» in Archivio e Notti, «40%», «all'83%», apostrofo dritto, Hα, «ottica · camera», numeri col punto, «Integrazione», «nuvole», «punto di rugiada», «foglio», «Interrompi», credito Copernicus intero, un segnaposto per la ricerca. Pagine: quasi tutte, più dieci componenti e tema.js.

## v24.3 — Il vocabolario — 19/10/2026

- «setup» al posto di «corredo», «posa» al posto di «esposizione», «Integrazione» nei titoli, «criteri» nella ricerca del Planner, «pannelli» nel mosaico di Luna e Sole, «Nessun filtro», «ADC». Pagine: Attrezzatura, Da confermare, Meteo, Misure dei frame, Notti, Planner, Progetti, Impostazioni, le tavole stati e cinque componenti.

## v24.2 — Quattro ritocchi — 19/10/2026

- «Prossima notte» in Progetti, «nessuna ora visibile», «ore visibili» nella vista Progetti del grafico della Dashboard, «nessuna convenzione: scegli tu» dove manca la fonte in Impostazioni.

## v24.1 — Correzioni e parole — 19/10/2026

- Salva di Crea porta alla scheda nuova in Progetti; nome dell'elenco con ottica e camera; sezione «Planner» in Impostazioni con le sette soglie e la fonte; «ore visibili» nel Planner e in Progetti; «mesi buoni» al posto di «stagione».

## v24 — Orizzonte, Progetti, collegamenti — 19/10/2026

- Impostazioni: riga Orizzonte (file di N.I.N.A.) e disegno a 360° con tre stati. Planner: sagoma sulla carta, soglia che segue l'orizzonte in Stanotte, Trova e Sistema solare. Pagina Progetti nuova (gruppi, scheda, azioni, cinque stati, telefono). Dashboard: ↗ e righe aprono Progetti.

## v23.2 — Planner, testi approvati — 19/10/2026

- Testi di Trova, giudizi, sicurezza, consigli ed Eventi approvati da Marco. Planner chiuso nel disegno.

## v23.1 — Eventi, due ritocchi — 19/10/2026

- Riga dell'orbita della ISS sempre intera; periodo della lista segnato come provvisorio; testi approvati da Marco.

## v23 — Eventi, Macchia Rossa e Marte — 19/10/2026

- Terzo modo Eventi (ISS su Sole e Luna, eclissi, occultazioni; lista e carta, foglio sul telefono; sette stati). Giove: passaggi della Macchia Rossa con fasce sulla curva e disco girato; Marte: meridiano centrale e mappa Viking girata. Trova: perché delle pillole spente in vista, campo di tutti e due i corredi col nome intero.

## v22 — Trova, quattro aggiunte — 19/10/2026

- Già ripreso (ore in archivio e pillola Archivio), dimensione da … fino a, pillola Entra nel campo, Ordina (mai per ore utili); stati archivio vuoto e nessun oggetto nel campo; telefono con pillole che scorrono e Ordina in un foglio.

## v21.4.1 — Planner, ultimi ritocchi — 19/10/2026

- Un seeing solo nel momento migliore (peggiorato dalla massa d'aria); video al massimo senza tetto; riga Hα solo col Sole; tolta `chip`.

## v21.4 — Planner, correzioni di Claude Code — 19/10/2026

- Soglie da Impostazioni (30° per tutti i corpi); consigli sotto i giudizi; momento migliore verde col seeing giudicato; entra nel campo con l'ellisse ruotata; Crea parte vuota; mese buono da 3 ore; stato senza chiave Meteoblue; schemi per camere a colori; tessere stimate = mosaico; video al massimo per difetto; Mercurio e Venere di giorno; tolte Macchia Rossa, Faccia di Marte e attività del Sole; RA / Dec e numeri col punto; pulizia delle forme A e C.

## v21.3 — Planner completo — 18/10/2026

- Telefono: foglio trascinabile, pallino su Salva, «Migliore →», rotazione sulla carta col mosaico nel Sistema solare, Luce bianca · Hα sulla carta, dissolvenza fra i passi.

## v21.2 — Planner sul telefono, forma 1b — 18/10/2026

- Tre forme a confronto; scelta e promossa la 1b: carta grande e foglio che sale, nei due modi. Tolte A, C e la loro tavola.

## v21.1 — Planner sul telefono, rifinito — 18/10/2026

- Corredo sotto la carta; due pillole per i modi; Trova dentro lo schermo; Crea ↓; mappe in un foglio dal basso; rotazione sulla carta; schermo intero e pizzico; − e + in Crea; corpi come icone.

## v21 — Planner sul telefono — 18/10/2026

- Planner (cielo profondo e Sistema solare) in una colonna sul telefono; Trova a schermo intero; luminosità superficiale nella ricerca. Tablet rimandato all'ultima release.

## v20.10 — Trova rifinita — 18/10/2026

- Ripresa in barre sotto la curva di Stanotte; curva piccola con scala; nessun risultato; costellazioni a tendina; luminosità superficiale (riga e filtro); carta del cielo alta quanto la colonna destra.

## v20.9 — Trova centrata — 18/10/2026

- Planner: Trova in una finestra centrata con pillole di filtro, Direzione a 8 settori, curva piccola della notte per riga, tastiera. Sistema solare: entra / non entra nel campo.

## v20.8 — Planner, Crea compatta e Trova rivista — 18/10/2026

- Cielo profondo: Stanotte a destra, Periodo migliore e Crea affiancati; righe più basse; riepilogo dei frame sotto il totale. Criteri del cielo in una riga; corredo di prova a puntini sulla carta; barra di Salva dopo la prima scelta. Sistema solare sempre in scala vera.

## v20.7 — Planner, Trova a scomparsa — 18/10/2026

- Cielo profondo: Trova in un pannello da sinistra, carta più larga, Il corredo e Periodo migliore a destra, Stanotte a tutta larghezza. Corredo di prova come pulsante nei due modi.

## v20.6 — Planner, rifiniture — 18/10/2026

- Sistema solare dalla Luna; numeri sotto la carta nei due modi; pianeti ingranditi alla partenza; ora migliore sulla curva; barra di Salva fissa nel cielo profondo.

## v20.5 — Planner, giudizi — 18/10/2026

- Giudizi per riga: campionamento pieno / sottocampionato (Sistema solare); ottimo / sotto / sovracampionato, entra / non entra nel campo (cielo profondo). Video al massimo con la formula ALPO. Rimando al Meteo.

## v20.4 — Planner, meno ripetizioni — 18/10/2026

- Cielo profondo e Sistema solare: ogni dato in un posto solo. Sistema solare: video al massimo, Macchia Rossa, faccia di Marte, correttore di dispersione.

## v20.3 — Planner, animazioni — 18/10/2026

- Puntatore sulla curva di Stanotte; le dieci animazioni proposte, nei due modi.

## v20.2 — Planner, correzioni — 18/10/2026

- Sistema solare: curva d'altezza esplorabile col puntatore, clic per portare l'ora lì.
- Corredi e filtro in tendina; «Filtri di ricerca»; cornice nell'accento sull'oggetto scelto; barlow da 1×; «Il momento migliore» col seeing nel Sistema solare; carta del corpo più compatta.

## v20.1 — Planner, Sistema solare — 18/10/2026

- Il selettore del Planner cambia modo. `componenti/PlannerSolare`: nove corpi, data e ora, il corpo in scala col sensore che gira; Luna LROC con fase, terminatore, nomi al clic, mosaico (intera o una zona) con l'ordine dal terminatore; Sole in luce bianca o Hα con la fascia fissa; pianeti con fase e anelli; i numeri (diametro, scala, campo, critico, tessere) e la prossima opposizione o elongazione. Sette stati nei Tweaks.

## v20 — Planner, cielo profondo — 18/10/2026

- `pagine/Planner.dc.html`, desktop: Trova coi criteri del cielo e di catalogo e la ricerca online; corredi a spunta (fino a due) e corredo di prova coi sensori per uso; la carta col cielo fotografico vero (sette mappe), campo che gira, mosaico numerato, mirino, orizzonte, rosa N/E, crediti; Stanotte e Periodo migliore; Crea con schema, filtri adatti, ore e minuti, frame mancanti, Salva coi suoi stati. Dieci stati nei Tweaks.
- Da fare: telefono e tablet del Planner, la pagina Progetti, il cerchio dei progetti nella Dashboard.

## v18.1 — il telefono in anteprima — 18/10/2026

- Cerca approvata; via `old/pagine/ricerca.html`. I piani entreranno come gruppo quando ci saranno.
- Il Bortle del sito dalle misure: proposta, sito misurato o scritto a mano, dati scarsi; nella tavola delle misure.
- v18.2 · Correzioni dopo il controllo di Claude Code: luminosità del cielo nel componente (bias, Bortle anche a colori, avvertenze), una ventina di testi allineati all'app, Attrezzatura (Riduttore, Guida, backfocus, Luna piena per misura), tolto il non deciso, corredi di prova coerenti in dati.js.
- Giudizi relativi: SNR basso e HFD alta per l'oggetto accanto a quelli della notte; mediana del corredo sotto la HFD; "oggetto basso" sopra massa d'aria 2; il limite del corredo spiegato accanto a "non giudicabile".
- Misure dei frame: tolta la sezione della curva del cielo; SQM si confronta nei grafici frame per frame; la Luna è un interruttore che aggiunge la sua linea.
- Luminosità del cielo come ASTAP: solo L, senza filtro e a colori; via il V50 (Primo avvio e tavola); "serve il bias della camera" per le camere a colori; curva della notte con la Luna nelle Notti. Misure della produzione con giudizi.
- Giudizi delle misure sempre in pillola (tabella per filtro, tilt del sensore). Riepilogo: riga delle notti senza sovrapposizioni, freccia sola.
- Misure dei frame: giudizi per misura (FWHM col limite del corredo, eccentricità, tilt, cielo; SNR basso e fuoco peggiore solo sul frame), FWHM e HFD in ″ e px, campionamento a parte, PSF SNR, tilt come ASTAP; niente backfocus. Soglie in `soglie.js`. Tweak "corredo" nella pagina delle misure.
- v19 · Cerca: finestra al centro (Ctrl K) sul desktop, pagina intera sul telefono; cinque gruppi, date nei due versi, stati vuoto, niente, scansione in corso, archivio vuoto. Componente `componenti/Cerca`, montato dal Telaio.
- Telefono: piede di Da confermare a una riga e fondo pieno; testa dell'Archivio alleggerita (vista e ordine in Filtri); tre numeri in fila nel Riepilogo; righe di stato delle Notti raccolte; provenienza del Meteo in una riga; sfumatura sulle strisce che scorrono; voce attiva della barra in basso nell'accento.
- Telaio: col formato telefono in una finestra larga, il telefono in anteprima (390 × 844, cornice, scorrimento dentro). Tavole e Cattura invariate.
- `pagine/Telefono.dc.html`: tutte le pagine nei telefoni, nel formato automatico.
- Misure dei frame: tolta la logica della riga vecchia.
- Primo avvio: formato "automatico" predefinito (telefono sotto 700 px).

## v18 — riordino — 18/10/2026

- Definitive: il Riepilogo v2 diventa `componenti/Riepilogo` (anche nelle finestre di Notti e Archivio), l'Attrezzatura v2 diventa `pagine/Attrezzatura.dc.html`.
- Escono `Riepilogo v2`, `RiepilogoV2`, `Attrezzatura v2` (spostate) e `componenti/MisureOggetto`; la tavola delle misure usa MisureFrame.
- Riepilogo: tolti i grafici e le metriche vecchie e il loro stato.
- `astrolog.css`: classi di Da confermare, Attrezzatura, Modulo e misure dei frame; nel Foglio la carta delle misure e MisureFrame vero.
- Sistema: "Le misure dei frame" col componente vero al posto di "Grafico delle metriche". Cattura: Riepilogo della notte sul telefono, Riepilogo chiaro, tavola delle misure.
- Sistema: il telefono con la scansione in corso e il menu "Altro" alto 700 (il menu usciva dalla cornice); "Si riprova da solo ogni 15 minuti." (era in prima persona); MisureFrame vero a richiesta, per catturare la tavola. "Per filtro": "sottocampionata" centrata sotto il valore.
- "Per filtro": sotto la FWHM solo "sottocampionata" (lo zenit si guarda nel grafico); righe e colonne tornano com'erano, la riga sotto il valore a 12 px.
- MisureFrame sul telefono: barre strette senza tratteggio, nomi brevi delle notti, righe di "A confronto" a due piani.

## v17.1 — Riepilogo v2 — 18/10/2026

- `componenti/MisureFrame`: misure in tessere, tabella per filtro, grafici frame per frame (per ora, per massa d'aria, per valore; allo zenit col seeing previsto), notti o oggetti a confronto, tilt e curvatura per filtro, il frame scelto.
- `pagine/Riepilogo v2.dc.html` con `componenti/RiepilogoV2`: le carte delle metriche e "Per filtro" lasciano il posto a MisureFrame.
- La direzione dell'allungamento solo da 0,40; "sottocampionata" sotto 2 px.
- Tratteggio della seconda misura piu' leggero; `docs/per-claude-code-misure-giudizi.md` (backfocus dai frame, giudizi sulle misure).
- Frame per frame rifatto: un grafico per filtro, una barra per frame, due misure (piena e tratteggiata, come l'anno della Dashboard), vista barre / linee, riquadro al passaggio, finestra sui frame quando sono tanti.
- (superato) Grafici a linee (mediana di 9 frame) coi punti tenui, scelta "linee / punti"; misure scelte nell'accento; il frame subito sotto i grafici; corretto l'errore al clic su un filtro.

## v17 — le misure dei frame — 18/10/2026

- `pagine/Misure dei frame.dc.html`: la tavola delle misure (ADR 0022). Notti: la riga di un oggetto con le mediane per filtro ("su 112 di 120 frame"), il grafico della FWHM frame per frame con l'altezza dell'oggetto (misurata / allo zenit), il frame scelto con tutte le misure e il rettangolo del sensore per tilt e curvatura. Archivio: per produzione mediana e quartili di FWHM, eccentricità e SNR. Luminosità del cielo con la banda, "senza bias", "manca il catalogo V50". Il catalogo V50 nel passo di ASTAP. Gli stati. Tweaks: stato (sei), formato, modo, accento.
- Primo avvio: nel passo di ASTAP la riga sul catalogo V50.
- `componenti/MisureOggetto`: la riga di un oggetto con le misure (oggetti, filtri, corredo, scala, stato). Nel riepilogo della notte la carta "Le misure per oggetto"; la tavola usa il componente.

## v16.1 — Attrezzatura v2, risposte di Claude Code — 18/10/2026

- Testi approvati da Marco; numeri scientifici col punto; Schema ottico con obiettivo fotografico e altro; Tolleranza del backfocus (ottica, riduttore) e Bias (camera); backfocus senza tolleranza: solo la differenza.
- Meteo: scale del campionamento col punto.
- DECISIONI: brief delle misure dei frame, per la prossima conversazione.

## v16 — dati completi dell'attrezzatura — 18/10/2026

- Attrezzatura v2, layout a due colonne, treno ottico isometrico in esploso con etichette, componenti a pillole; domande per Claude Code in `docs/per-claude-code-attrezzatura-v2.md`.

- Attrezzatura v2: campi nuovi per tipo, tipi guida fuori asse e distanziale, parti guida e distanziali, carta dei Conti coi tre stati (valore, avviso, manca).
- `componenti/Modulo`: tendine con la stessa forma dei campi di testo.
- Meteo: carta del campionamento dei corredi col seeing della notte, pillole degli esiti.
- Attrezzatura v2: "I numeri del corredo" dentro la carta del corredo, con pillole d'esito (copertura, scala di guida, backfocus ±1 mm, carico); campionamento in ″/px; il treno ottico disegnato e interattivo; campo Schema ottico.

## v15.2 — Attrezzatura a carte — 18/10/2026

- `pagine/Attrezzatura v2.dc.html`: corredi e componenti a carte in testa, ottica e camera nella carta del corredo, campo coi nomi e la Luna piena, parti a tessere, filtri ad anello, pezzi dei gruppi a carte. Logica e dati invariati.

## v15.1 — riordino — 17/10/2026

- `componenti/PillolaScelta`: forma "risposta" (pallino, riga sotto facoltativa, 44 px), fondi `carta2` e `vuoto`. La usano Da confermare e il Modulo al posto delle loro copie.
- Da confermare e Attrezzatura: scheletro col componente Scheletro; moto.js nella testa; codice morto tolto.
- Sistema: la carta del Modulo. Cattura: Attrezzatura e Da confermare.

## v15 — Attrezzatura, forma nuova — 17/10/2026

- `pagine/Attrezzatura.dc.html`: indice a sinistra (corredi con le parti da indicare, gruppi dei componenti), dettaglio a destra; sul telefono indice e dettaglio a pagina intera. Interattiva: scelta di una parte, Rinomina, Modifica, Aggiungi strumento, Unisci a, Salva che salva davvero. Tweaks: stato (sette), vista, modulo aperto (dieci), errore (otto), telefono, formato, tema.
- `componenti/Modulo`: il modulo di creazione e modifica, solo disegno.
- `pagine/Attrezzatura stati.dc.html`: la tavola, 23 telefoni e 8 desktop.
- Testi e dati di Claude Code (risposta del 17/10). Da confermare: corredi col "+".
- Escono da `old/`: `pagine/attrezzatura.html`, `attrezzatura-stati.html`, `attrezzatura-moduli.html`, `docs/proposte/attrezzatura.js`, `attrezzatura.css`. Esce `docs/per-claude-code-attrezzatura.md` (risposto).
- Attrezzatura: barre delle ore e tacche delle parti nell'accento, segni dei tipi, campo dei corredi a confronto, animazioni (barre, numero, righe).
- Da confermare: tacche delle domande nel conto; animazioni (domanda che si apre, conto e piede che contano, esito).

## v12.1 — primo avvio, i testi dell'app — 17/10/2026

Da Claude Code. Estetica e comportamenti restano; cambiano solo testi.

- Bortle: nomi e descrizioni delle nove classi sono quelli dell'app, dalla voce "Bortle scale" di Wikipedia (la stessa fonte del numero). Non si riscrivono.
- ASTAP senza catalogo: perché del passo, avviso "Catalogo stellare mancante" col catalogo consigliato (D80, circa 1,25 GB, nella cartella di ASTAP) ed esito della verifica coi testi dell'app.
- Cartella già registrata: "Corrisponde a \\nas\astro\2026: stessi file. I dati associati vengono mantenuti."
- I testi nuovi del primo avvio (tema, chiusura, "saltato") sono approvati da Marco.

## v14 — Da confermare — 17/10/2026

- `pagine/Da confermare.dc.html`: Da confermare nel linguaggio bento, forma B, desktop e telefono. Tweaks: stato (nove), domanda aperta (diciannove casi), motivo del rifiuto, vista del telefono, formato, tema. Interattiva: scelte, campi, ricerca dei modelli, Rispondi / Cambia / Riapri, Applica che applica davvero (strumenti e filtri escono), indice che porta alla sezione, `#sezione` nell'indirizzo.
- `pagine/Da confermare stati.dc.html`: la tavola, 31 telefoni e 9 desktop.
- Testi dell'app, controllati da Claude Code (risposta del 17/10). Il conto sono le domande, non le notti.
- `componenti/DaConfermare`: il pannello elenca le sezioni con domande aperte e il loro conto, Rispondi apre la pagina sulla sezione. Niente notte d'esempio.
- `componenti/Telaio`: `domande` al posto di `notti` (4 d'esempio); sul telefono "4 da confermare" per chi legge con la voce.
- Escono da `old/`: `pagine/da-confermare.html`, `da-confermare-stati.html`, `docs/proposte/da-confermare.js`, `docs/archivio/brief-da-confermare.md`, `contenuti-da-confermare.md`. Esce `docs/per-claude-code-da-confermare.md` (risposto).

## v13.1 — un ritocco alla v13 — 17/10/2026

Da Claude Code. Estetica e comportamenti restano.

- Meteo, il racconto della notte: i pianeti "culminano" dai 10° (prima 15°, senza fonte). E' la stessa altezza minima della Luna: un solo numero per "alto abbastanza da contare" (Marco).
- `soglie.js`: tolti in `qualita` il commento rimasto della Luna e il commento "Quanto vale ogni fattore" doppio.
- DECISIONI: il racconto della notte sostituisce le fasce orarie e i riquadri Buio e Luna nelle notti con le ore; Marco lo tiene in Meteo.

## v13 — la Luna decide la ripresa, non il punteggio — 17/10/2026

Regola nuova di Marco (da Claude Code). Estetica e comportamenti restano.

- `componenti/soglie.js`: di notte la Luna esce dai punti; pesi 35 nuvole / 30 seeing / 12 trasparenza / 9 condensa / 9 vento / 5 jet stream. "Cosa limita" non può più essere la Luna. Esce `qualita.luna`. Nuove `ripresa(fase, altezza)` (stretta da 25 % e 10°), `tratti`, `oreLarga`, `tipoNotte`, `frase`, `breve`, `larghePassate` (notti passate e calendario, simulato). `puntoNotte` senza Luna (non la usava già).
- Il giorno del Sole non cambia: pesi di prima, con "Sole basso" 15. Come giudicarlo senza Sole basso si decide con Marco quando si costruisce.
- Componente nuovo `componenti/Ripresa`: riga (sotto il verdetto) e segno (con le ore di banda larga). In Sistema; classi `al-ripresa…` e `al-fascia-ripresa…` in `astrolog.css`.
- Dashboard: sotto il verdetto "Banda larga 20:48–01:00 · poi solo banda stretta"; nel riquadro della Luna le ore di ciascun tipo; sotto l'asse del grafico la fascia della ripresa (tratteggiata = solo banda stretta); nel riquadro del puntatore la ripresa di quell'ora; prossime 3 notti col segno accanto al verdetto. Calendario: notti buone = almeno 4 ore di banda larga.
- Meteo: la stessa riga nella carta della notte; "Come va la notte" ha la riga del cambio ("01:00 · la Luna sale sopra 10°: solo banda stretta"); la Luna esce da "inoltre" e resta nel riquadro in fondo; sette notti col segno.
- Notti: nella carta della notte, nella striscia e in "A confronto", sotto il cielo, le ore di banda larga.
- Striscia: campo `rip` facoltativo.
- Meteo, "Come va la notte" diventa il racconto della notte: una linea del tempo, dal tramonto all'alba, con un evento per riga. Ci sono tramonto e alba, inizio e fine del buio, quando sorge e tramonta la Luna, i cambi di ripresa, il verdetto solo quando cambia (col segno), le nuvole oltre o sotto il 25 e il 50 %, la pioggia che comincia o finisce, la condensa sotto 3 °C, le raffiche, il seeing migliore, i pianeti che sorgono, tramontano o culminano (dai 15° in su). Sul desktop la carta resta alta quanto il grafico: si vedono quelli che ci stanno, gli altri scorrono dentro la carta, con una sfumatura in fondo. Toccando un evento il puntatore del grafico va a quell'ora. Le fasce orarie e i due riquadri (Buio, Luna) escono per le notti con le ore; restano per le notti di tendenza e per il giorno del Sole.

Effetto sui dati d'esempio:
- Nessun verdetto cambia: stanotte buona, giovedì 1 non adatta, venerdì 2 buona; le notti di tendenza hanno il verdetto scritto; le notti passate non usavano la Luna.
- Ore utili: in Meteo stanotte da 6 (21–03) a 9 (21–06); venerdì 2 da 8 (21–05) a 9 (21–06), anche nella Dashboard. Dashboard stanotte resta 9.
- Ripresa: stanotte banda larga 20:48–01:00 (4 h 15), poi solo banda stretta; giovedì 1 5 ore, venerdì 2 6 ore, sabato 3 7 ore, domenica 4 7 h 45 di banda larga; lunedì 5 e martedì 6 (Luna sotto il 25 %) tutta la notte banda larga.
- Calendario: settembre dall'1 al 18 e il 30 (prima dal 4 al 14); ottobre dall'1 al 17 e dal 29 al 31 (prima dal 3 al 13). Il 30 settembre entra: 4 h 15 di banda larga, prima 2 h 52 di buio senza Luna.
- Notti passate: le ore di banda larga vanno da 1 h (27 settembre, Luna al 96 %) a tutta la notte (13 settembre, Luna all'8 %); il 16 settembre, falce al 28 %, 7 h 10.

## v12 — il primo avvio, col tema — 17/10/2026

- `pagine/Primo avvio.dc.html`: il primo avvio nel linguaggio bento, senza telaio. Desktop: passi di lato, carta del passo a destra, gesti in fondo alla carta. Telefono: passi in fila sopra, gesti in una barra fissa in fondo. Tweaks: passo, stato, ASTAP (non trovato, catalogo mancante, installato), formato, modo, accento.
- Passi: Nome utente, Sito di osservazione, Tema (nuovo), Cartelle (computer o NAS), Seeing (Meteoblue), ASTAP solo a chi manca (5 o 6 passi, deciso entrando). Prima di tutto, se c'è, Backup trovato. Dopo "Fine", Primo avvio completato.
- Risolti i tre difetti: tappa saltata col suo segno ("–" tratteggiato, parola "saltato") distinta da fatta (✓); chiusura con "Cartelle: 3" e la riga "La scansione non è partita: si avvia da Scansiona, nel menu dell'ingranaggio."; telefono con campi a 16 px, bersagli da 44, coordinate in due colonne, Bortle 5 + 4, percorso del NAS che va a capo, accenti in colonna.
- `componenti/SceltaTema`: modo e accento col campione dei colori nel modo scelto; Automatico spento senza sito. In Sistema e nel Foglio.
- `componenti/Avviso`: segno "✓" per gli esiti riusciti.
- `pagine/astrolog.css`: classi del primo avvio (al-primo, al-tappe / al-tappa, al-passo-carta, al-gesti, al-modulo, al-bortle-scegli, al-voce, al-sfoglia, al-chiusura, al-segno--fatto, al-attesa) e della scelta del tema (al-tema…); il campione prende i colori da data-modo e data-accento suoi.
- `pagine/Primo avvio stati.dc.html`: la tavola, 46 telefoni e 10 desktop. `Cattura.dc.html`: #pa|formato|passo|stato|astap|modo|accento.
- Contrasto delle coppie nuove nei 2 modi × 5 accenti: testo minimo 5,14:1 (tenue su carta2), errore 6,57:1.
- Escono da `old/`: `pagine/primo-avvio.html`, `primo-avvio-stati.html`, `docs/proposte/primo-avvio.js`.

## v11 — ultimi ritocchi prima del porting — 17/10/2026

- Verdetto dal punteggio della notte (media delle ore di buio; di giorno della finestra): buona da 70, incerta da 40 (ADR 0020). Ore utili da 60, solo come numero. Esce `oreEsito`.
- Gradini: jet stream da 126 km/h e condensa sotto 3 °C passano a "non adatto"; aerosol tra 0,1 e 1 senza parola (barretta neutra).
- Curve della qualità con gli estremi dell'ADR (pieno alla soglia buona, zero alla non adatta).
- Voluto, sui dati d'esempio: stanotte 9 ore utili (prima 8), "notte buona"; la condensa di stanotte "non adatto"; nelle Notti il 19 settembre a Casa passa da buona a incerta; in Meteo il limite di stanotte alle 23 è il jet stream.
- Luna: nel riquadro del grafico (Meteo, Dashboard) anche "illuminata al N %"; nella qualità la Luna usa la fase della notte e il Bortle del sito (prima una fase fissa).
- Parole: Notti e Riepilogo "Caricamento…"; "Le notti non si possono leggere"; frase del cielo a 25 / 50 %.
- DECISIONI: le sezioni vecchie usano le parole della v10; le regole cambiate rimandano a v10 o v11.

## v10 — correzioni prima del porting — 17/10/2026

- Parole dal glossario dell'app in pagine, componenti, tema.js e dati.js (ore, senza durata, Non disponibile, nessun filtro, verdetto e giudizio, Caricamento…, niente prima persona).
- Qualità: somma dei punti dei fattori (ADR 0020), cosa limita = il fattore che perde di più; soglie dei giudizi dall'app. `soglie.js` simula l'app. Voluto: stanotte 8 ore utili (prima 6), nuvole e condensa "incerto", Visibilità al posto di Umidità nella notte coperta.
- Scansione nel menu dell'ingranaggio: segno sull'ingranaggio e su "Altro", Ferma e Riprendi (Telaio, Menu, Sistema).
- Stati nuovi: Dashboard (senza sito, prima scansione, da riprendere, dettaglio della Luna), Meteo (risposta non valida, cambio del modello non riuscito, seeing parziale; ora locale in fondo), Notti (nessuna cartella, fuori da ogni notte, senza durata nei totali), Archivio (senza oggetto, ASTAP assente, filtri nuovi). Tavole degli stati aggiornate.
- Archivio: linguette Deep sky / Sole / Sistema solare e la finestra "Aggiungi oggetto".
- Riepilogo: HFD, fondo cielo, rumore del fondo; tutto dichiarato simulato; distanza non nota.
- `pagine/astrolog.css`, `pagine/caratteri.css` e i caratteri nel progetto; `pagine/Foglio.dc.html` per il confronto. Le pagine non caricano più caratteri da Google.
- Sistema: la carta "Scansione"; il telaio desktop d'esempio mostra la scansione in corso.
- Catture in `screenshots/v10/`.

## v9 — il riordino — 17/10/2026

- Componenti nuovi: PillolaScelta, Filtri, BarraFiltri, Luna, CalendarioNotti, Scheletro, FinestraRiepilogo; Riepilogo spostato in `pagine/componenti/` (la pagina `Riepilogo.dc.html` lo monta).
- `componenti/dati.js`: tutti i dati simulati (notti, oggetti, produzioni, pannelli, corredi, oggi 30 settembre). `tema.js`: filtri (AL.FD, AL.tinta, AL.linea), Luna (AL.lunaD), tratteggio, ore e numeri all'italiana.
- Le sei pagine e le tavole usano i componenti; Sistema mostra quelli veri (in piu' la carta Luna).
- Unificati: strisce dei filtri nel riepilogo, calendario della Dashboard (CalendarioNotti, stelline dalle notti vere), "Togli tutti", misure di pillole e segmentati, tratteggio 3/8, angoli degli scheletri, bordo della Luna.
- PillolaScelta ha la forma "spunta": le misure sul grafico di Meteo (desktop e telefono) e in Sistema.
- Corretto: nella Dashboard, con "Sole", il calendario della Luna restava in vista.
- Catture prima e dopo in `screenshots/v9/`; controlli: testo minimo 5,14:1, forme 3,32:1, 44 px sul telefono, console pulita.

## v8 — Archivio — 17/10/2026

- Approvato: produzioni al posto dei corredi, una produzione alla volta nel riepilogo, mosaico coi pannelli, carte cinque per riga, scelte nell'accento, animazioni (`componenti/moto.js`).
- Escono da `old/`: `pagine/archivio.html`, `archivio-produzioni.html`, `archivio-stati.html`, `archivio-telefono.html`, `docs/proposte/archivio.js`, `archivio-carte.css`.

- `pagine/Archivio.dc.html`: carte ed elenco, ricerca, filtri, ordine; il riepilogo dell'oggetto in finestra. Riepilogo: funziona con qualsiasi oggetto (parametro `oggetto`). Catalogo: cinque oggetti in più. Telaio: la voce Archivio apre la pagina.

## v7 — il riepilogo — 17/10/2026

- `pagine/Riepilogo.dc.html`: il riepilogo di un oggetto finito (IC 1396, tre notti, due corredi) o di una notte. Testa con periodo, ore e filtri col pallino; in cielo (tipo, costellazione, distanza, estensione); le metriche dei frame (FWHM, eccentricità, stelle, fondo, rumore, segnale/rumore, altezza) in grafici uno sotto l'altro, per ora o dal migliore al peggiore, filtri a confronto, puntatore comune; per filtro; corredo compatto; le notti con Luna ed esito. Tweaks: tipo, stato, formato, modo, accento.
- In Notti "Tutto della notte ↗" apre il riepilogo: finestra sul desktop, pagina intera sul telefono, con la notte prima e dopo. Esce la prima bozza.
- `componenti/catalogo.js`: il catalogo degli oggetti, dati veri. Telaio: parametro `solo`.
- Approvato: in testa FWHM, segnale/rumore ed esito; miniature delle metriche; fascia degli oggetti; "Per filtro" isola il filtro; telefono con righe che scorrono.
- `pagine/Riepilogo stati.dc.html`: otto telefoni e quattro desktop. Sistema: il mattone "Grafico delle metriche".

## v6 — Notti — 17/10/2026

- `pagine/Notti.dc.html`: Notti nel linguaggio bento, desktop e telefono, coi componenti (Telaio, Carta, Pillola, Avviso, Striscia). Desktop: striscia delle ultime 7 notti, la notte scelta (ore di posa, cielo, Luna, oggetti, filtri), calendario col numero del mese, filtri accanto all'elenco "A confronto" (20 alla volta), totali dell'archivio. Telefono: righe di stato in testa, striscia delle notti con "Mese" e "Filtri", la notte, i totali. Quindici stati (Tweaks: Stato, Formato, dettaglio, modo, accento).
- `pagine/Notti stati.dc.html`: la tavola, sedici telefoni e quattro desktop; gli schermi si accendono entrando nella vista.
- Filtri delle notti: oggetto, anno, sito, corredo, filtri, costellazione, cielo; ogni pillola col conto.
- "Tutto della notte" in bozza, da rifare.
- Striscia: la casella scelta entra da sola nella vista; oltre 8 caselle sul desktop scorre; parametro `intestazione`. Meteo invariata.
- Telaio: la voce Notti apre la pagina.
- Sistema: calendario delle notti (col numero del mese), barra dei filtri della notte, filtri delle notti, riga della notte.
- Date allineate al 30 settembre 2026 come Dashboard e Meteo; il 27 settembre è quello della Dashboard.
- Controlli: testo minimo 5,14:1 e forme 3,32:1 nei due modi coi cinque accenti; bersagli da 44 sul telefono; console pulita.
- Escono da `old/`: `pagine/notti.html`, `notti-stati.html`, `notti-telefono-nastro.html`, `notti-telefono-stati.html`, `docs/proposte/notti.js`, `notti-nastro.css`.

## v5 — i componenti veri — 17/10/2026

- `pagine/componenti/`: Telaio, Menu, DaConfermare, Carta, CardMeteo, Pillola, Avviso, Striscia, ognuno coi suoi parametri e Tweaks (modo, accento, formato, stato).
- `componenti/tema.js` e `componenti/soglie.js`: token e soglie in un file solo, letti da Dashboard, Meteo, Sistema e dai componenti.
- Dashboard e Meteo passano ai componenti. Catture prima e dopo in `screenshots/prima/` e `screenshots/dopo/`, desktop e telefono: uguali al pixel, salvo il numero che pulsa e tre cose volute: due barrette della Dashboard con le soglie decise (nuvole 45%, seeing 2″) e la barra di Meteo allineata a quella della Dashboard (segno da 34, ingranaggio, pannello di Da confermare).
- `pagine/Sistema.dc.html`: telaio, menu, Da confermare, carta, pillole (quattro misure), card meteo (desktop, telefono e i quattro stati), avviso (blocco e riga), striscia nuova: sono i componenti veri. Contrasto su quindici coppie.
- Controlli: 300 coppie nei due modi coi cinque accenti, testo minimo 5,05:1. Bersagli da 44 sul telefono, console pulita anche nelle tavole degli stati.
- Modo chiaro: il segno "!" su ambra scuro #956600 col "!" bianco (prima giallo #d39a2b, 2,2:1 sul fondo).

## v4 — Meteo — 17/10/2026

- `pagine/Meteo.dc.html`: Meteo nel linguaggio bento, desktop e telefono. Le sette notti, la notte col cielo (nubi a tre strati, umidità, una misura sulla scala di destra), cosa pesa, otto misure che seguono il puntatore e vanno sul grafico, altre misure, fonti. Sedici stati come parametro (Tweaks: Stato, Formato, modo, accento).
- `pagine/Meteo stati.dc.html`: la tavola, sedici telefoni e quattro desktop.
- Grafico: pillola Deep sky / Sole (tutta la pagina passa al giorno), fino a quattro misure insieme con colori propri, umidità e probabilità di pioggia sulla scala in %, le altre solo forma col valore al puntatore. Testa con le fonti (Open-Meteo, Meteoblue). Tweak `obiettivo`. Qualità della notte o del giorno sempre sul grafico; animazioni del grafico; barrette delle carte che portano la pagina a quell'ora; variante a fasce (tweak `grafico`). Ore utili ed esito dalla qualità; "Come va la notte" al posto di "Cosa pesa"; misure in ibrido (umidità e pioggia linee sul cielo, le altre fasce, senza limite, accese da sole quelle che limitano).
- Allineati Dashboard e Sistema: soglie della condensa, Sabato 3 come tendenza, "Ore utili stanotte", ↗ verso Meteo, barrette nei colori degli esiti.
- Tavola degli stati: in più Sole, quattro misure accese, modo chiaro (telefono) e Sole (desktop).
- Escono da `old/`: `pagine/meteo.html`, `meteo-stati.html`, `meteo-telefono.html`, `docs/consegna-meteo-dashboard.md`.

## v3 — token, telaio e mattoni — 17/10/2026

- `pagine/Sistema.dc.html`: la tavola ricavata dalla Dashboard. Token nei due modi e nei cinque accenti con il contrasto calcolato, colori fissi, caratteri, misure, telaio (barra desktop, barre del telefono, menu Altro, Impostazioni, Da confermare), mattoni: carta, esiti, pillole di scelta, bottoni e ↗, card meteo, riga con anello, anello e barre dell'anno, avviso e passi, scheletro, giorni del calendario, legenda e grafici, riquadro dei valori, scheda della notte. Tweaks: modo, accento.
- Filtri: tutti quelli del vecchio sistema, anche a più bande e sconosciuto; nuove tinte anche nella Dashboard. Pianeti: aggiunti Mercurio, Urano, Nettuno.

## v2 — la Dashboard completa — 17/10/2026

- `pagine/Dashboard.dc.html`: quattro stati (prima volta, caricamento, senza previsione, notte coperta) e il formato telefono, nella stessa pagina (Tweaks: Stato, Formato). Accento predefinito ambra · blu notte.
- `pagine/Dashboard stati.dc.html`: la tavola, cinque telefoni e quattro desktop.
- Sole ridisegnato; Luna · Sole come pillola piccola a destra.
- Animazioni: curve che si disegnano al cambio vista, carte in entrata, puntatore morbido, anelli e barre che si riempiono.
- Accessibilita': grafico della notte da tastiera e lettore di schermo; contrasto misurato sulle 10 combinazioni, nulla sotto soglia.

La cronologia del vecchio sistema (fino alla v38) sta in `old/docs/CHANGELOG.md`.

## v1 del linguaggio nuovo — si riparte dalla Dashboard — 17/10/2026

- `pagine/Dashboard.dc.html`: la dashboard bento definitiva (ex variante 2c),
  ripulita dalle varianti. Modo e accento sono parametri della pagina
  (Tweaks); il modo si cambia anche dalla barra.
- Escono: le dashboard vecchie (desktop, telefono, Atlante, stati), le
  varianti bento 2a e 2b, la copia con barra laterale, le catture di lavoro.
- In `old/`: `astrolog.css`, `foglio/`, le pagine vecchie, mattoni, tavole,
  token, proposte, documenti di consegna, decisioni e cronologia fino alla v38.
