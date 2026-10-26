# Riordino v32 · seconda passata (24/10/2026) — Selezione dei frame, Misure dei frame, MisureFrame

Brief di Marco: gli stati che il codice calcola passano dal tema allo stile in pagina → varianti di classe nel foglio; niente colori a mano; la tabella L esce; componenti comuni; <button> veri; catture uguali.

## Come si controlla
- Copia di prima: `screenshots/prima-passata2/pagine/` (24/10, prima di toccare).
- show_html `strumenti/Confronto.html#base=prima-passata2&sinc=1&chiavi=X`, poi multi_screenshot: definire `__L` (chiavi), `__cmp(k)` (hash nei due iframe A/B), `__chk()` (riassunto(a,b) delle `__fp(null)`; `=` uguale), `__go()`; 7 s fra un passo e l'altro.

## Fatto
- Tavola degli stati: «le soglie del corredo» → «le soglie del setup».
- Tutte le classi al-sel__ / al-sel2__ / al-misure__ / al-c-misure-frame__ usate stanno in astrolog.css (controllo con script).
- Foglio §1: --accento-50 / --accento-14 / --accento-tessera in ogni blocco modo × accento (rgba letterali, contrasto accanto); fissi --su-immagine-testo, --immagine-schermo, --immagine-velo, --immagine-tasto, --immagine-male.
- Foglio §2: button.al-bottone (azzera il bottone del sistema), .al-bottone--acceso; pillole aria-checked; .al-interruttore; .al-pillola--avviso/--spenta; .al-segno--buona/--non-adatta/--carta-2; .al-finestra--schermo; Avanzamento (al-c-avanzamento__*, telefono e --piccola); al-c-quartili.
- Foglio §3 Selezione: L nel foglio (variabili --sel-carta-pad, --sel-esito-pad, --sel-esito-griglia + blocco telefono), stati: colonna-7/riga-28 aria-selected, tondo-3 aria-checked, tondo-5--pericolo/--tieni/--su-immagine con aria-pressed, al-sel__segno--*, barre/punti/segnetti/linee/legenda per stato, sb/--acceso, riga-26--spenta, riga-30--errore, centro-4--angoli, filtri.
- Componenti: PillolaScelta (ruolo="radio", forma linguette e interruttore, href, classe; sel accetta 'true'); Pillola (forma="segno", esiti avviso e spenta, classe); Finestra (larghezza="schermo", testa="no"); nuovi Avanzamento e Quartili.
- Pagina Selezione: template e logica rifatti (L = {desk, tel}; niente colori del tema nel codice).

## Fatto anche
- Confronto delle impronte: Selezione (12 stati fra formati, modi, accenti e Tweaks), Progetti (3), Misure dei frame (3), Riepilogo (2): nessuna misura ne' colore cambiato.
- Progetti su Avanzamento; Misure dei frame e MisureFrame sulle classi (L fuori, 8 bottoni, PillolaScelta, Pillola, Quartili).
- COMPONENTI.md, per-claude-code-porting.md, CHANGELOG (v32.2), DECISIONI (v32, seconda passata).

## Da fare
- Niente. `screenshots/prima-passata2/` si puo' togliere quando Marco ha guardato.
