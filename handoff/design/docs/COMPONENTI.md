# AstroLog · I componenti (v32)

L'elenco per il porting, senza doppioni. Ogni componente e' un file `pagine/componenti/<Nome>.dc.html`; le classi stanno in `pagine/astrolog.css` (sez. 2). I parametri `modo` (scuro, chiaro) e `accento` (originale, ambra · blu notte, turchese · petrolio, corallo · terracotta, ghiaccio · indaco) li hanno tutti e non li ripeto.

Regola per tutti: **il componente non calcola**. Verdetti, punteggi, ore, giudizi, misure arrivano dall'app; il componente li mostra. Le funzioni di `soglie.js` che i componenti chiamano oggi sono la simulazione di cio' che nel codice vero calcola il motore (vedi `per-claude-code-porting.md`).

## Avviso

Un avviso: di pagina, a blocco o a riga, col segno («!» non riuscito, «?» dato che manca) e il gesto.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| tipo | string | pagina, blocco, riga | "blocco" |
| formato | string | desktop, telefono | "desktop" |
| segno | string | !, ?, ✓ | "!" |
| titolo | string |  | "Meteo non raggiungibile" |
| testo | string |  | "Open-Meteo non risponde dalle 14:05. Riprovo da solo ogni 15 minuti." |
| azione | string |  | "Riprova ora" |
| colonne | number |  |  |
| rientro | number |  |  |
| onAzione | () => void |  |  |

Classi: `al-bottone`, `al-c-avviso__…`.

Lo usano: Archivio, Attrezzatura, Da confermare, Dashboard, Foglio, Impostazioni, Meteo, Notti, Planner, Primo avvio, Sistema, Statistiche, PlannerEventi2, SezioneServizi.

## Avanzamento

L'avanzamento di un progetto: l'anello delle ore fatte sull'obiettivo e una barra per filtro. Due blocchi fratelli (l'involucro non fa scatola): la pagina li mette nella sua griglia. Seconda passata (24/10): prima erano le classi `al-prog__…`, uguali in Progetti e Selezione dei frame.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| percento | number | 0–100 | 62 |
| anello | string | il fondo dell'anello, se la pagina lo vuole diverso (Progetti: colore per gruppo) | conic-gradient(--anello, --traccia) dal percento |
| testo | string | la cifra nell'anello | «62%», «✓» da 100 |
| fatte | string |  | "12 h 30" |
| obiettivo | string |  | "20 h" |
| aria | string |  | «fatte di obiettivo» |
| titolo | string |  | "Per filtro" |
| filtri | { l, c, w, fatte, ob }[] | c il colore del filtro, w la larghezza in % | |
| nota | string | riga sotto le barre |  |
| misura | string | "", piccola | "" (grande sul desktop, media sul telefono) |
| colonna | string | grid-column del blocco delle barre |  |
| formato | string | desktop, telefono | "desktop" |

Classi: `al-c-avanzamento__…`, `al-c-avanzamento--piccola`.

Lo usano: Progetti, Selezione dei frame.

## BarraFiltri

La barra delle ore per filtro (strisce colorate, filtro non indicato tratteggiato).

| parametro | tipo | valori | partenza |
|---|---|---|---|
| filtri | Array<[string, number, number\|null]> |  |  |
| altezza | number \| string | 12, 8 | "12" |
| righe | boolean |  | true |
| anima | boolean |  | false |
| formato | string | desktop, telefono | "desktop" |

Classi: `al-c-barra-filtri__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Archivio, Notti, Sistema.

## CalendarioNotti

Il calendario del mese con le notti buone e quelle di ripresa.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| tipo | string | notti, luna | "notti" |
| anno | number |  | 2026 |
| mese | number | 0–11 | 8 |
| giorni | Array&lt;{d:number,esiti?:number[],segno?:string,stella?:boolean,sel?:boolean,on?:Function,aria?:string}&gt; |  |  |
| buone | number[] |  |  |
| titolo | string |  | "" |
| sub | string |  | "" |
| numero | string |  | "" |
| numeroL | string |  | "" |
| conta | string |  | "" |
| nuova | string |  | "" |
| piena | string |  | "" |
| onPrima | () =&gt; void |  |  |
| onDopo | () =&gt; void |  |  |
| primaNo | boolean |  |  |
| dopoNo | boolean |  |  |
| formato | string | desktop, telefono | "desktop" |
| buoneL | string |  | "" |

Classi: `al-c-calendario-notti__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Dashboard, Notti, Progetti, Selezione dei frame (tipo luna: notti con frame accese con la stella, piu' notti insieme), Sistema.

## CardMeteo

La carta di una notte nel Meteo: verdetto, ore utili, Luna.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| formato | string | desktop, telefono, telefono compatta | "desktop" |
| stato | string | normale, mancante, non si misura, chiave, chiave non valida, non disponibile | "normale" |
| nome | string |  | "Nuvole" |
| valore | string |  | "16" |
| unita | string |  | "%" |
| nota | string |  | "media nel buio · picco 40% tra le 05 e le 06" |
| esito | 0 \| 1 \| 2 \| string | buona, incerta, non adatta, mancante | "buona" |
| giudizio | string |  | "buona" |
| limita | string |  | "" |
| anello | string |  | "" |
| link | string |  | "" |
| etichetta | string |  | "" |
| aggiornamento | string |  | "" |
| picco | string |  |  |
| celle | {h,bg,op?,on?,title?}[] |  |  |
| aperto | boolean |  |  |
| onClick | () => void |  |  |
| onLeave | () => void |  |  |

Stati: normale, mancante, non si misura, chiave, chiave non valida, non disponibile.

Classi: `al-bottone`, `al-c-card-meteo__…`.

Lo usano: Dashboard, Meteo, Sistema.

## Carta

La carta bento: fondo, angoli, colonne della griglia, entrata quando arriva sullo schermo.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| formato | string | desktop, telefono | "desktop" |
| tono | string | carta, protagonista | "carta" |
| colonne | number | 1–12 | 12 |
| padding | string |  | "" |
| gap | number | 0–40 | 18 |
| griglia | string |  | "" |
| anello | string |  | "" |
| ritardo | number | 0–600 | 0 |
| etichetta | string |  | "" |
| allinea | string |  |  |
| giustifica | string |  |  |
| flex | string |  |  |
| children | ReactNode |  |  |

Classi: `al-c-carta__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Archivio, Dashboard, Impostazioni, Meteo, Notti, Piano della notte, Planner, Progetti, Sistema, Statistiche, Riepilogo.

## Cerca

La ricerca (Ctrl K): oggetti, notti, attrezzatura, siti, pagine.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| testo | string |  | "m31" |
| stato | string | normale, scansione in corso, archivio vuoto | "normale" |
| formato | string | desktop, telefono | "desktop" |
| statico | boolean |  | true |
| onChiudi | () => void |  |  |

Stati: normale, scansione in corso, archivio vuoto.

Classi: `al-bottone`, `al-c-cerca__…`.

Lo usano: Telaio.

## DaConfermare

Il riquadro «Da confermare» del menu in alto: l'ultima notte e le domande aperte.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| statico | boolean |  | true |
| sezioni | [string, string, number][] |  |  |

Classi: `al-c-da-confermare__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Sistema, Telaio.

## Filtri

I criteri dell'Archivio: bottone, «Togli», pannello coi gruppi.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| parte | string | corpo, bottone, togli | "corpo" |
| gruppi | Array<{l:string,opz:any[]}> |  |  |
| colonne | number | 1–6 | 1 |
| campo | string |  | "per esempio M 31 o Velo" |
| q | string |  |  |
| onCerca | (q: string) => void |  |  |
| attivi | number | 0–9 | 0 |
| aperto | boolean |  | false |
| freccia | boolean |  |  |
| onApri | () => void |  |  |
| onTogli | () => void |  |  |
| mostra | string |  | "Mostra 6 notti" |
| onMostra | () => void |  |  |
| altezza | string |  |  |
| rientro | string |  |  |
| formato | string | desktop, telefono | "desktop" |

Classi: `al-campo`, `al-bottone`, `al-c-filtri__…`.

Lo usano: Archivio, Notti, Sistema.

## Finestra

Finestra sopra la pagina: titolo, ×, corpo, gesti; Esc, fuoco dentro; foglio dal basso sul telefono.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| titolo | string |  | "Aggiungi oggetto" |
| segno | string | , !, ? | "" |
| sottotitolo | string |  | "" |
| larghezza | 'stretta' \| 'media' \| 'larga' | stretta, media, larga | "media" |
| fondo | 'telaio' \| 'carta' | telaio, carta | "telaio" |
| posizione | 'fissa' \| 'dentro' | fissa, dentro | "fissa" |
| formato | string | desktop, telefono | "desktop" |
| onChiudi | () => void |  |  |
| children | ReactNode |  |  |

Classi: `al-finestra`, `al-c-finestra__…`.

Lo usano: Archivio, Piano della notte, Planner.


Seconda passata (24/10): `larghezza="schermo"` (il frame a schermo intero della Selezione: sul nero `--immagine-schermo`, senza velo ne' angoli, `al-finestra--schermo`) e `testa="no"` (niente titolo ne' ×: la testa la porta la pagina; il titolo resta come aria-label).

## FinestraRiepilogo

Il Riepilogo in una finestra larga (desktop) o a pagina intera (telefono), con prima/dopo.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| tipo | string | oggetto, notte | "oggetto" |
| notte | object |  |  |
| oggetto | object |  |  |
| posizione | string | fissa, dentro | "dentro" |
| aria | string |  |  |
| onChiudi | () => void |  |  |
| onPrima | () => void |  |  |
| onDopo | () => void |  |  |
| primaNo | boolean |  |  |
| dopoNo | boolean |  |  |
| formato | string | desktop, telefono | "desktop" |

Classi: `al-c-finestra-riepilogo__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Archivio, Notti.

## Luna

La Luna: fase disegnata, percentuale, sorge/tramonta.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| percento | number | 0–100 | 62 |
| crescente | boolean |  | false |
| misura | number \| string | 20, 22, 30, 34, 60, 76 | "30" |
| piena | boolean |  | false |
| titolo | string |  | "" |
| testo | string |  | "" |
| formato | string | desktop, telefono | "desktop" |

Classi: `al-c-luna__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Dashboard, Notti, Piano della notte, Sistema, Riepilogo.

## Menu

I menu della barra: «Altro», «Impostazioni» (con la scansione), quello del telefono.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| tipo | string | altro, impostazioni, altro telefono | "altro" |
| scansione | string | ferma, in corso, interrotta, bloccata | "ferma" |
| statico | boolean |  | true |
| sito | string |  | "Cima Ekar" |
| onModo | (modo: string) => void |  |  |

Classi: `al-c-menu__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Voci di «Altro» (v36): Planner, Piano della notte, Carta del cielo, Selezione dei frame, Attrezzatura; sul telefono anche Progetti e Statistiche.

Lo usano: Foglio, Sistema, Telaio.

## MisureFrame

Le misure dei frame: FWHM, HFD, SNR, eccentricità, fondo, SQM; quartili, frame per frame, riquadro.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| tipo | 'oggetto' \| 'notte' | oggetto, notte | "oggetto" |
| onMediane | (k: { fw: string, snr: string }) => void |  |  |
| selezione | string |  | "" (indirizzo di «Seleziona i frame ↗» accanto a «Frame per frame»; vuoto: niente bottone) |
| gruppi | { n: string, filtri: [string, number][], seeing?: boolean, es?: 0\|1\|2, esT?: string }[] |  |  |
| scala | number |  | 1.94 |
| stato | string | normale, misura in corso, senza scala del cielo, senza sito | "normale" |
| formato | string | automatico, desktop, telefono | "automatico" |

Stati: normale, misura in corso, senza scala del cielo, senza sito.

Classi: `al-riquadro`, `al-bottone`, `al-quartili`, `al-c-misure-frame__…`.

Lo usano: Foglio, Misure dei frame, Sistema, Riepilogo (che passa `selezione` solo per la notte).

## Modulo

Un modulo: campi, tendine, tipi a tasselli, errore sotto, unità a destra.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| m | object |  |  |
| t | object |  |  |

Classi: `al-bottone`, `al-campo`, `al-tendina`, `al-c-modulo__…`.

Lo usano: Attrezzatura, Sistema.

## Pillola

L'esito con colore, segno e parola (buona ✓, incerta !, non adatta ✕, mancante ?, neutra).

| parametro | tipo | valori | partenza |
|---|---|---|---|
| acapo | boolean |  | false |
| esito | 0 \| 1 \| 2 \| string | buona, incerta, non adatta, mancante, neutra | "buona" |
| testo | string |  | "buona" |
| segno | string |  | "" |
| dimensione | string | media, piccola, minima, micro | "media" |
| fondo | string | carta2, carta | "carta2" |
| allinea | string |  |  |

Classi: `al-pillola`, `al-c-pillola__…`.

Lo usano: Attrezzatura, Dashboard, Foglio, Meteo, Misure dei frame, Notti, Sistema, CardMeteo, MisureFrame, Riepilogo, SezioneServizi, Striscia.


Seconda passata (24/10):

| parametro | tipo | valori | partenza |
|---|---|---|---|
| forma | string | pillola, segno | "pillola" |
| esito | | anche avviso (al limite: fondo dell'avviso), spenta (la soglia non c'e': senza fondo, tenue) | |
| classe | string | classe di posto in piu' (misure del posto, es. `al-sel__pillola-1`) |  |

`forma="segno"`: il tondo da solo (`al-segno al-segno--<esito>`, `al-segno--carta-2` con fondo carta2), aria-hidden; e' il segno «?» delle pagine. Lo usano anche: Selezione dei frame (giudizi delle misure, «! modifiche da applicare», segni di «Come funzionano»), Misure dei frame (segni «?» e «!»), MisureFrame (la nota del frame).

## PillolaScelta

Le scelte: pillole, segmentato, spunta, risposta.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| opzioni | Array<{l:string,sub?:string,sel?:boolean,on?:Function,c?:string,no?:boolean,tinta?:string,linea?:string,titolo?:string}> |  |  |
| forma | string | pillole, segmentato, spunta, risposta | "pillole" |
| misura | string | normale, piccola | "normale" |
| fondo | string | carta, carta2, vuoto, protagonista | "carta" |
| scorre | boolean |  | false |
| allinea | string |  |  |
| etichetta | string |  | "Scelta" |
| formato | string | desktop, telefono | "desktop" |

Classi: `al-scelta`, `al-c-pillola-scelta__…`.

Lo usano: Archivio, Da confermare, Dashboard, Meteo, Planner, Sistema, Statistiche, Filtri, Modulo.


Seconda passata (24/10):

| parametro | tipo | valori | partenza |
|---|---|---|---|
| forma | string | anche linguette (le sezioni: `al-scelta--linguette`), interruttore (`al-interruttore`: una opzione, l il nome, titolo l'aria-label, sel acceso) | |
| ruolo | string | "", radio | "" |
| classe | string | classe di posto in piu' |  |
| opzioni[].href | string | linguette che portano a un'altra pagina (niente preventDefault) |  |

`ruolo="radio"`: radiogroup e voci `role="radio"` con aria-checked (segmentato e pillole; senza, il segmentato e' tablist/tab con aria-selected e le pillole aria-pressed). `sel` accetta true o 'true'. L'interruttore e' un `<button role="switch">`: binario 36 × 22, pomello 16, acceso col colore dell'accento.

Lo usano anche: Selezione dei frame (11 gruppi, filtri, linguette di Impostazioni, 8 interruttori), Misure dei frame (produzione), MisureFrame (filtri, grafici per filtro, Vista, Ordine, Valore, Misura).

## PlannerEventi2

Gli eventi del Planner (v57–v58): transiti della ISS su Sole e Luna, eclissi, occultazioni, congiunzioni, ombre delle lune di Giove. Sul cielo il disco nel campo del setup o la Mappa dei posti; nella colonna (foglio sul telefono) Evento, Dettagli, Sequenza per SharpCap.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| formato | string | desktop, telefono | "desktop" |
| modi | Array | le linguette Cielo profondo · Sistema solare · Eventi |  |
| corredo | object | il setup scelto (focale, pixel, sensore) |  |
| corSel | object | i setup per «Setup ▾» |  |
| preset | object | stato iniziale (tipo, periodo, sel, nessuno, issErr) |  |
| sito | boolean |  | true |
| modo, accento | string |  |  |

Stati: lista vuota, senza sito, senza rete (ISS), evento passato, fuori dalla striscia, meteo non ancora previsto.
Classi: `al-bottone` (--vetro, --pieno, --contorno, --tenue, --icona, --riga, --scelta), `al-tendina`, `al-tocco`, `al-vetro`; token `--vetro`, `--cielo-testo-2`, `--ombra-*`.
Simulato: gli eventi (nell'app li calcola il backend: ISS dall'orbita del giorno, eclissi dai canoni di Espenak), i posti della mappa (`transiti.js`), l'esportazione (.scs).
Lo usano: Planner, Sistema.

## PlannerSolare2

Il Planner del Sistema solare (v57–v58): il disco nel campo del sensore, righello della rotazione, mosaico per Luna e Sole, lune di Giove; nella colonna (foglio sul telefono) Quando (il momento migliore, la curva, le prossime notti), Ripresa (diametro, scala, rapporto focale, Barlow scrivibile, filtro, la ripresa salvata), Sequenza per SharpCap.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| formato | string | desktop, telefono | "desktop" |
| modi | Array | le linguette |  |
| corredo | object | il setup (con `cam` mono/colore e `fil`, i filtri della ruota) |  |
| corSel | object | i setup per «Setup ▾» |  |
| provaBtn | object | apre e chiude il setup virtuale |  |
| pv, onPv | object, Function | i campi del setup virtuale |  |
| sensori | Array | il catalogo dei sensori |  |
| preset | object | corpo iniziale |  |
| rete | boolean | senza rete: le immagini non arrivano | true |
| modo, accento | string |  |  |

Stati: non sale da qui, il Sole (di giorno), seeing non adatto, senza seeing, setup virtuale, mosaico acceso, sequenza piu' lunga della finestra.
La sequenza: con la camera mono solo i filtri R G B L della ruota del setup, piu' IR e CH4; Luna 12 pannelli dal terminatore (area 1920 × 1080), Giove e Saturno dalla ripresa salvata.
Classi: come PlannerEventi2, piu' `al-campo`, `al-interruttore`, `al-scelta`.
Simulato: effemeridi, seeing, la Macchia Rossa e le lune di Giove, l'esportazione (.scs). Le immagini di Sole, Luna e pianeti nella tavola tengono il posto: nell'app sono vere, in alta risoluzione.
Lo usano: Planner, Sistema.

## Quartili

La misura di molti frame su una riga: traccia, banda dal primo al terzo quartile, segno della mediana, soglia tratteggiata se c'e'. Seconda passata (24/10): prima markup ripetuto con le classi `al-quartili`.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| q1 | string | % | "25%" |
| qw | string | % | "30%" |
| m | string | % | "42%" |
| soglia | string | %, vuoto senza soglia | "" |
| misura | string | normale, piccola | "normale" |

Classi: `al-quartili`, `al-quartili--piccolo`, `al-c-quartili__blocco-1`.

Lo usano: Misure dei frame, MisureFrame.

## Riepilogo

Il riepilogo di un oggetto o di una notte: produzioni, misure, attrezzatura.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| tipo | string | oggetto, notte | "oggetto" |
| stato | string | normale, caricamento, misure in calcolo, senza durata | "normale" |
| formato | string | automatico, desktop, telefono | "automatico" |

Stati: normale, caricamento, misure in calcolo, senza durata.

Classi: `al-bottone`, `al-c-riepilogo__…`.

Lo usano: Riepilogo stati, Riepilogo, FinestraRiepilogo.

## Ripresa

Segno e parole della ripresa con la Luna (banda larga o stretta).

| parametro | tipo | valori | partenza |
|---|---|---|---|
| tipo | 'larga' \| 'stretta' \| 'mista' | larga, stretta, mista | "mista" |
| testo | string |  | "Banda larga 20:45–00:45 · poi solo banda stretta" |
| forma | 'riga' \| 'segno' | riga, segno | "riga" |
| fondo | string | carta, protagonista | "carta" |
| colore | string |  |  |
| tenue | string |  |  |
| formato | string | desktop, telefono | "desktop" |

Classi: `al-c-ripresa__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Dashboard, Meteo, Notti, Sistema, Striscia.

## SceltaTema

Scelta del modo e dell'accento, col campione.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| sito | string |  | "Cima Ekar" |
| ora | string | scuro, chiaro | "scuro" |
| piede | string |  | "" |
| formato | string | desktop, telefono | "desktop" |
| onModo | (modo: string) => void |  |  |
| onAccento | (accento: string) => void |  |  |

Classi: `al-c-scelta-tema__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Foglio, Impostazioni, Primo avvio, Sistema.

## Scheletro

Lo scheletro del caricamento, carta per carta.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| carte | Array<{col?:string,h?:string,pad?:string,gap?:string,griglia?:string,blocchi:any[]}> |  |  |
| griglia | string |  |  |
| gap | string |  |  |
| testo | string |  | "Caricamento" |
| formato | string | desktop, telefono | "desktop" |

Classi: `al-c-scheletro__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Archivio, Attrezzatura, Da confermare, Dashboard, Meteo, Notti, Sistema, Riepilogo.

## SezioneServizi

Le quattro sezioni nuove di Impostazioni: Servizi, Scansioni, Diagnostica, Backup.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| sezione | 'servizi' \| 'scansioni' \| 'diagnostica' \| 'backup' | servizi, scansioni, diagnostica, backup | "servizi" |
| stato | string | normale, senza chiave, attiva, rifiutata, non raggiungibile, nessuna scansione, in corso, una bloccata, molti file non leggibili, ASTAP assente, errori, mai scritto, ripristino al primo avvio | "normale" |
| formato | string | desktop, telefono | "desktop" |

Stati: normale, senza chiave, attiva, rifiutata, non raggiungibile, nessuna scansione, in corso, una bloccata, molti file non leggibili, ASTAP assente, errori, mai scritto, ripristino al primo avvio.

Classi: `al-imp-sezione`, `al-imp-intro`, `al-imp-carta`, `al-imp-testa`, `al-imp-titoli`, `al-imp-titolo`, `al-imp-sotto`, `al-bottone`, `al-imp-riga`, `al-imp-etichetta`, `al-imp-valore`, `al-imp-chiave`, `al-campo`, `al-imp-nota`, `al-imp-barra`, `al-imp-percorso`, `al-imp-file`, `al-imp-gesti`, `al-c-sezione-servizi__…`.

Lo usano: Impostazioni.

## Striscia

La striscia delle notti (scorre di lato, una accesa).

| parametro | tipo | valori | partenza |
|---|---|---|---|
| formato | string | desktop, telefono | "desktop" |
| etichetta | string |  | "le sette notti" |
| notti | {day,tag,tagS,tend,sel,esito,pillT,rip?:{tipo,testo},hours,range,cells,on}[] |  |  |
| rientro | number |  |  |

Classi: `al-c-striscia__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Meteo, Notti, Sistema.

## Telaio

La cornice della pagina: barra in alto (desktop) o in basso (telefono), menu, Cerca, modo.

| parametro | tipo | valori | partenza |
|---|---|---|---|
| scansione | string | ferma, in corso, interrotta, bloccata | "ferma" |
| formato | string | desktop, telefono | "desktop" |
| pagina | string | Dashboard, Notti, Archivio, Progetti, Statistiche, Meteo | "Dashboard" |
| menu | string | nessuno, altro, impostazioni, da confermare, cerca | "nessuno" |
| sito | string \| null |  | "Cima Ekar" |
| daConfermare | boolean |  | true |
| domande | number | 0–200 | 4 |
| cornice | boolean |  | true |
| altezza | string |  |  |
| etichetta | string |  |  |
| onModo | (modo: string) => void |  |  |
| children | ReactNode |  |  |

Classi: `al-c-telaio__…` (sez. 2 di astrolog.css; inline restano solo i valori dai dati).

Lo usano: Archivio, Attrezzatura, Cerca, Da confermare, Dashboard, Impostazioni, Meteo, Notti, Piano della notte, Planner, Progetti, Sistema, Statistiche, Riepilogo.

## I token

Seconda passata (24/10), aggiunti nel foglio: `--accento-50`, `--accento-14`, `--accento-tessera` (le trasparenze dell'accento, in ogni blocco modo × accento, col contrasto accanto), `--su-immagine-testo`, `--immagine-schermo`, `--immagine-velo`, `--immagine-tasto`, `--immagine-male` (il frame simulato e lo schermo intero).

In `astrolog.css`, sez. 1, per i due modi e i cinque accenti (i colori col significato non cambiano con l'accento):

`--cielo`, `--luna-scura`, `--luna-chiara`, `--luna-linea`, `--cielo-testo`, `--cielo-tenue`, `--cielo-credito`, `--cielo-ombra`, `--cielo-velo`, `--cielo-bottone`, `--cielo-bottone-testo`, `--su-immagine`, `--punto-chiaro`, `--aladin-testo`, `--aladin-segno`, `--cielo-stella`, `--cielo-orizzonte`, `--cielo-traccia`, `--cielo-segno`, `--cielo-disco`, `--cielo-disco-bordo`, `--cielo-luna-eclisse`, `--cielo-luna-bordo`, `--cielo-eclisse`, `--cielo-penombra`, `--cielo-anelli`, `--cielo-anelli-chiari`, `--cielo-macchia`, `--corpo-mercurio`, `--corpo-venere`, `--corpo-marte`, `--corpo-giove`, `--corpo-saturno`, `--corpo-urano`, `--corpo-nettuno`, `--sole`, `--sole-esterno`, `--sole-medio`, `--sole-interno`, `--sole-raggio`, `--sole-macchia`, `--sole-numero`, `--bianco`, `--cornice-telefono`, `--nero`, `--raggio-carta`, `--raggio-carta-tel`, `--raggio-interno`, `--raggio-pillola`, `--durata-entrata`, `--curva-entrata`, `--durata-breve`, `--foto-fondo`, `--umidita`, `--strumento-1`, `--strumento-2`, `--strumento-3`, `--strumento-4`, `--inchiostro`, `--carattere`, `--pagina`, `--telaio`, `--carta`, `--carta-2`, `--linea`, `--testo`, `--tenue`, `--nav-su`, `--nav-su-testo`, `--prot-fondo`, `--prot-testo`, `--prot-tenue`, `--prot-traccia`, `--prot-barra`, `--riquadro-fondo`, `--riquadro-testo`, `--barretta-spenta`, `--barretta`, `--traccia`, `--avviso`, `--avviso-testo`, `--male`, `--da-confermare-fondo`, `--da-confermare-testo`, `--accento`, `--scelta`, `--scelta-testo`, `--giorno-su`, `--giorno-su-testo`, `--anello`, `--barra-mese`, `--macchia`, `--buono-fondo`, `--buono-testo`, `--incerto-fondo`, `--incerto-testo`, `--non-adatto-fondo`, `--non-adatto-testo`, `--setup-1`, `--setup-2`, `--setup-3`, `--setup-4`, `--setup-5`, `--pianeta-0`, `--pianeta-1`, `--pianeta-2`, `--pianeta-3`, `--pianeta-4`, `--pianeta-5`, `--pianeta-6`, `--filtro-0`, `--filtro-1`, `--filtro-2`, `--filtro-3`, `--filtro-4`, `--filtro-5`, `--filtro-6`, `--filtro-7`, `--filtro-8`, `--filtro-9`, `--banda-colore`, `--banda-0`, `--banda-1`, `--banda-2`, `--banda-3`, `--banda-4`.

Tipi della Ricerca e degli eventi (v32, barretta dei blocchi nel Piano della notte): `--tipo-exo`, `--tipo-ecl`, `--tipo-var` (anche AAVSO), `--tipo-neo`, `--tipo-sn`, `--tipo-cometa`, `--tipo-evento`; in tema.js `t.tipi`. Non cambiano con l'accento.
