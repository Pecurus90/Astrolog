# Per Claude Code · porting (riordino v32, finito)

Da Claude Design, 21/10/2026. Risposta alla brief «Riordino prima del porting (brief v1)». Il riordino e' finito: il progetto e' la fonte del porting.

## Cambiato rispetto alla brief v1

- **Classi dei componenti**: anche i 25 componenti di `pagine/componenti/` sono sulle classi, con prefisso `al-c-<nome>__<ruolo>-<n>` (686 regole, in fondo alla sez. 2 del foglio). Inline restano solo i valori dai dati.
- **`--male` nel modo chiaro**: #d0503e → #bf4232 (5.2:1 su carta, 4.7 su carta-2), stessa tinta piu' scura.
- **Seeing di giorno**: stesse soglie della notte, buono fino a 2″ compreso (`soglie.esito.seeingGiorno`: `x <= 2`, come il seeing della notte).
- **Segmentato piccolo sul telefono**: 44 px, come tutti gli altri bersagli (era 38).
- **Archivio sul telefono**: «Deep sky · Sole · Sistema solare» sta su una riga intera; le voci del segmentato che riempie la riga hanno 6 px di lato sul telefono.
- **Planner, «Crea il progetto»**: campi di ore, minuti, posa, colonne e Luna allargati (64–72 px); il numero non sta piu' sotto le frecce.
- **Colori dei tipi nel Piano della notte**: la barretta (e il segno) di ogni blocco ha il colore del suo tipo, come i progetti. Token `--tipo-*` nel foglio, gemelli in `t.tipi` (`tema.js`). Il tipo resta scritto accanto.
- **Diagnostica**: resta una linguetta di Impostazioni; `/diagnostica` apre la linguetta.

## Seconda passata (24/10/2026): Selezione dei frame, Misure dei frame, MisureFrame

Lo stile che il codice calcolava e' passato nel foglio. A schermo non cambia niente: confrontate le impronte con la copia di prima (`screenshots/prima-passata2/pagine/`) su Selezione dei frame (desktop e telefono, scuro e chiaro, quattro accenti, Impostazioni, formula con errore, dopo lo spostamento, elimina senza cestino), Misure dei frame, Progetti e Riepilogo: misure e posizioni di ogni elemento uguali, colori uguali; cambiano solo i tag (`<a>` → `<button>`) e proprieta' senza effetto (cursore e allineamento del testo dentro i bottoni). Le catture finali restano valide.

- **Stati come classi**: voce scelta (`aria-selected`), bottone acceso (`aria-pressed`, `--acceso`), «Scarta» `al-sel__tondo-5--pericolo` (e `--tieni`, `--su-immagine` a schermo intero), il segno dello stato del frame `al-sel__segno--*`, barre, punti e segni del grafico `al-sel__barra--*`, `al-sel__punto--*`, `al-sel__segnetto--*`, legende; in MisureFrame tessere `--prima`/`--seconda`, barre `--accesa`/`--stimata`, cerchi `--max`. In pagina restano solo posizioni, larghezze in %, la luminosita' del frame simulato e il colore di un filtro.
- **Niente colori a mano**: `#ffffff`, `#17181c`, `#ff8a7a` e le trasparenze dell'accento sono token (`--su-immagine`, `--su-immagine-testo`, `--immagine-male`, `--accento-50`, `--accento-14`, `--accento-tessera`, piu' `--immagine-schermo`, `--immagine-velo`, `--immagine-tasto`), col contrasto accanto. Sono scritti nel foglio: `tema.js` non li genera.
- **La tabella L esce**: spaziature, raggi, titoli e griglie nel foglio sotto `[data-formato="telefono"]`; nella Selezione la Carta riceve `var(--sel-carta-pad)`, `var(--sel-esito-pad)`, `var(--sel-esito-griglia)`. MisureFrame e Misure dei frame portano ora `data-formato` sull'involucro. Nel codice resta solo quale formato e' (e la geometria dei grafici SVG).
- **Componenti**: PillolaScelta (gruppi, linguette, interruttori; `ruolo="radio"`), Pillola (giudizi, `forma="segno"`), Finestra (`larghezza="schermo"` per il frame a schermo intero), nuovi Avanzamento (comune a Progetti e Selezione: le classi `al-prog__…` della Selezione erano le stesse) e Quartili. Parametri in `docs/COMPONENTI.md`.
- **Bottoni**: `<button type="button" class="al-bottone …">` al posto di `<a href="#">` (Selezione, Misure dei frame; gli 8 di MisureFrame: «solo …», la Luna, Vista, le frecce dei grafici e del frame, la Luna nel pannello). `button.al-bottone` azzera il bottone del sistema. Restano `<a>` i link veri, le tessere, le righe e le voci delle tendine.
- **Campi e tendine**: restano sulle classi `al-campo` e `al-tendina` (le stesse di Modulo). Modulo e' un modulo intero (titolo, blocchi, Salva/Annulla), non un campo: un componente Campo si fa se serve.
- Tutte le classi `al-sel__…` usate stanno in `astrolog.css` (controllato con uno script: nessuna manca).

## Le catture finali

`screenshots/finali/`: 1248 stati (ogni pagina, ogni stato dei Tweaks, desktop e telefono, scuro e chiaro). Dalla v36.4 anche la Selezione dei frame: stati 1202–1247 (dieci stati, l'errore del NAS e le Impostazioni), file `NN-d1202.jpg` e `NN-d1225.jpg`. L'elenco degli stati, in ordine, e' `screenshots/finali/_elenco.json`; i file sono `NN-dSSSS.jpg`, dove `SSSS` e' l'indice del primo stato del gruppo e `NN` la posizione nel gruppo (stato = SSSS + NN − 1). Si rifanno con `pagine/Cattura.dc.html`, `__go(i)`.

Le catture prima e dopo del riordino sono uscite: le finali le sostituiscono.

## Il foglio

- `pagine/astrolog.css`, versione v32 (in testa al file). Si copia com'e'.
- Sez. 1 token (due modi × cinque accenti, generati da `componenti/tema.js`, col contrasto accanto; anche `--tipo-*` e `--tavola-*`); sez. 2 componenti (`al-…` e `al-c-…`); sez. 3 pagine (`al-<pagina>__<ruolo>-<n>`; ruolo: riga, colonna, griglia, testo, tondo, pillola, riquadro, strato, centro, blocco, tratto, scritta, grafico).
- Il tema si sceglie con due attributi su un antenato: `data-modo="scuro|chiaro"`, `data-accento="originale|ambra|turchese|corallo|ghiaccio"`; il telefono con `data-formato="telefono"`.
- `old/` e `pagine/foglio-v17.css` sono usciti.

## Le pagine e i componenti che usano

| pagina | componenti |
|---|---|
| Archivio | Avviso, BarraFiltri, Carta, Filtri, Finestra, FinestraRiepilogo, PillolaScelta, Scheletro, Telaio |
| Attrezzatura | Avviso, Modulo, Pillola, Scheletro, Telaio |
| Cerca | Telaio |
| Da confermare | Avviso, PillolaScelta, Scheletro, Telaio |
| Dashboard | Avviso, CalendarioNotti, CardMeteo, Carta, Luna, Pillola, PillolaScelta, Ripresa, Scheletro, Telaio |
| Impostazioni | Avviso, Carta, SceltaTema, SezioneServizi, Telaio |
| Meteo | Avviso, CardMeteo, Carta, Pillola, PillolaScelta, Ripresa, Scheletro, Striscia, Telaio |
| Misure dei frame | MisureFrame, Pillola, PillolaScelta, Quartili |
| Notti | Avviso, BarraFiltri, CalendarioNotti, Carta, Filtri, FinestraRiepilogo, Luna, Pillola, Ripresa, Scheletro, Striscia, Telaio |
| Piano della notte | Carta, Finestra, Luna, Telaio |
| Planner | Avviso, Carta, Finestra, PillolaScelta, PlannerEventi, PlannerSolare, Telaio |
| Primo avvio | Avviso, SceltaTema |
| Progetti | Avanzamento, CalendarioNotti, Carta, Telaio |
| Riepilogo | Riepilogo |
| Selezione dei frame (v36) | Avanzamento, Avviso, CalendarioNotti, Carta, Finestra, Pillola, PillolaScelta, Telaio |
| Statistiche | Avviso, Carta, PillolaScelta, Telaio |

L'elenco dei componenti, coi parametri: `docs/COMPONENTI.md`.

Senza seeing: `soglie.ora()` risponde `senza`; `soglie.senzaRiga(senza)` da' la riga «senza seeing», `soglie.senzaTutte(ore)` i fattori che mancano in tutte le ore, `soglie.senzaPassate` quelli delle notti passate. Nell'app li calcola il motore.

## Cio' che e' ancora simulato

- **Dati**: `componenti/dati.js` (notti, oggetti, produzioni, pannelli, attrezzatura, orizzonte), `componenti/dati-statistiche.js` (le notti di piu' anni per Statistiche), `componenti/catalogo.js` (catalogo ridotto). Ogni pagina con dati simulati lo dice a schermo.
- **Soglie**: `componenti/soglie.js` ha i numeri con la loro fonte (`IMP0`: valore, unita', sezione, fonte, chi la legge). I numeri sono decisioni e si portano; le funzioni sono simulazione.
- **Funzioni di soglie.js che nell'app calcola il motore**: `ora()` (punteggio dell'ora, cosa limita, fattori mancanti in `senza`, blocco per pioggia, nuvole, nebbia), `qualita.*` ed `esito.*` (punti e giudizio di ogni fattore), `media`, `conto`, `nOre`, `intervallo`, `lunaNotte`, `ripresa`, `giudizioLuna`, `misure.*` (giudizi delle misure dei frame, `bortleDi` con la tabella unica SQM ↔ Bortle), `imp` (la memoria delle Impostazioni, oggi in localStorage).
- **MisureFrame** usa anche PillolaScelta, Pillola e Quartili.
- **Componenti che oggi calcolano qualcosa** (nell'app il numero arriva fatto): MisureFrame (mediane e quartili dai frame simulati), PlannerSolare e PlannerEventi (posizioni dei corpi), Luna (fase disegnata dalla percentuale: questo resta nel componente, e' disegno).

## Da sapere

- Il caricatore `alPronto()` in ogni file, le copie di `support.js`, `pagine/Cattura.dc.html` e `strumenti/` sono del progetto di Design: non si portano.
- `AL.formatoScelto` e `AL.telefono` (in `tema.js`): la regola del formato (indirizzo, parametro, automatico sotto 700 px).
- Le decisioni del riordino: `docs/DECISIONI.md`, sezione v32.
