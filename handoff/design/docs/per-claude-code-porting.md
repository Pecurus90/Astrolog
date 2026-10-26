# Per Claude Code · porting (v58.5, 26/10/2026)

Da Claude Design. Il disegno di AstroLog e' finito e pulito: questo progetto e' la fonte del porting. Sostituisce `docs/archivio/per-claude-code-porting-v32.md` (resta valido per tutto cio' che qui non e' detto).

## Da dove partire

1. `README.md`: dove sta cosa.
2. `docs/COMPONENTI.md`: i componenti con parametri, stati, classi e chi li usa. I due Planner nuovi (`PlannerSolare2`, `PlannerEventi2`) sono aggiornati alla v58; gli altri sono alla v32 con le seconde passate segnate.
3. `docs/DECISIONI.md`: perche' ogni cosa e' cosi'. Le sezioni v49–v58.5 sono l'ultimo giro (linguaggio bento, desktop e telefono allineati, Planner).
4. `pagine/Sistema.dc.html`: token, telaio e mattoni veri, desktop e telefono; i due Planner si aprono a richiesta, con «Desktop ↗» e «Telefono ↗».

## Il foglio

`pagine/astrolog.css`, unico per tutte le pagine (~3400 regole, 380 token). Da copiare com'e'. In testa i token (due modi × cinque accenti, col contrasto accanto), poi i componenti (`al-c-<nome>__…`), poi le pagine (`al-<pagina>__…`). I caratteri sono in `pagine/caratteri/` (`caratteri.css`).

Nuovo dalla v58.5: il vetro sul cielo dei Planner.
- Token: `--vetro`, `--vetro-bordo`, `--vetro-filtro`, `--cielo-testo-2` (11,6:1 sul vetro), `--cielo-fondo`, `--ombra-vetro`, `--ombra-finestra`, `--ombra-foglio`, `--ombra-bordo`, `--cielo-scurisci`.
- Classi: `al-bottone--vetro` (bottoni e tendine sul cielo), `al-vetro` e `al-vetro--alto` (righello, momenti dell'evento, bolla delle pagine), `al-bottone--velo` (bottone chiaro su una striscia del cielo, desktop).

Nei Planner restano inline: posizioni e misure che vengono dai dati o dal gesto (pan, rotazione, altezza del foglio), le ombre del testo sul cielo, i colori del disegno (pianeti, Luna, tracce: `AL.CIELO_D`, `AL.CORPI`).

## Le pagine

Ogni pagina e' desktop e telefono nello stesso file (formato automatico, o `?formato=telefono`). Gli indirizzi `?…` aprono uno stato o un oggetto: nel codice vero diventano le rotte o lo stato iniziale.

| pagina | componenti | indirizzo |
|---|---|---|
| `Archivio.dc.html` | Avviso, BarraFiltri, Carta, Filtri, Finestra, FinestraRiepilogo, PillolaScelta, Scheletro, Telaio | — |
| `Attrezzatura.dc.html` | Avviso, Modulo, Pillola, Scheletro, Telaio | — |
| `Cerca.dc.html` | Telaio | — |
| `Da confermare.dc.html` | Avviso, PillolaScelta, Scheletro, Telaio | — |
| `Dashboard.dc.html` | Avviso, CalendarioNotti, CardMeteo, Carta, Luna, Pillola, PillolaScelta, Ripresa, Scheletro, Telaio | — |
| `Impostazioni.dc.html` | Avviso, Carta, SceltaTema, SezioneServizi, Telaio | `?sezione=` |
| `Meteo.dc.html` | Avviso, CardMeteo, Carta, Pillola, PillolaScelta, Ripresa, Scheletro, Striscia, Telaio | — |
| `Misure dei frame.dc.html` | MisureFrame, Pillola, PillolaScelta, Quartili, Telaio | — |
| `Notti.dc.html` | Avviso, BarraFiltri, CalendarioNotti, Carta, Filtri, FinestraRiepilogo, Luna, Pillola, Ripresa, Scheletro, Striscia, Telaio | — |
| `Piano della notte.dc.html` | Carta, Finestra, Luna, Telaio | `?stato=` |
| `Planner.dc.html` | Avviso, BarraFiltri, Carta, CieloCriteri, CieloLista, CieloNotte, Finestra, Menu, PlannerEventi2, PlannerSolare2, Telaio | `?ora=` `?vista=` `?livello=` `?sel=` `?disp=` `?lista=` `?piano=` `?vola=` `?pianifica=` `?stato=` `?da=` `?n=` `?c=` `?rot=` `?mos=` `?fil=` `?fatte=` `?ob=` |
| `Primo avvio.dc.html` | Avviso, SceltaTema | — |
| `Progetti.dc.html` | Avanzamento, CalendarioNotti, Carta, Telaio | `?nuovo=` `?n=` `?solnuovo=` `?p=` `?com=` `?mos=` `?filtro=` `?c=` `?ra=` `?dec=` `?rot=` `?fil=` `?vis=` |
| `Riepilogo.dc.html` | Riepilogo | — |
| `Selezione dei frame.dc.html` | Avanzamento, Avviso, CalendarioNotti, Carta, Finestra, Pillola, PillolaScelta, Telaio | `?stato=` `?modo=` `?accento=` `?vista=` `?progetto=` `?notte=` `?errore=` `?anteprima=` |
| `Statistiche.dc.html` | Avviso, Carta, PillolaScelta, Telaio | `?stato=` |

Tavole degli stati difficili: Attrezzatura, Da confermare, Dashboard, Meteo, Notti, Primo avvio, Progetti, Riepilogo, Selezione dei frame (`pagine/* stati.dc.html`). Planner, Piano della notte, Statistiche, Impostazioni portano i loro stati nei Tweaks e in `?stato=`.

## Il Planner (v57–v58)

Tre modi con le linguette in alto: Cielo profondo · Sistema solare · Eventi (`?pianifica=solare`, `?pianifica=eventi`). La stessa forma in tutti e tre:
- **Desktop**: il cielo largo e la colonna di 424 px; sul cielo una riga sola di comandi in alto, il righello o i momenti in basso, i crediti in una riga.
- **Telefono**: il cielo a tutto schermo; in alto il modo in tendina e il corpo o l'evento (si ritirano mentre il dito muove il cielo); in basso il bordo del foglio (tocca o tira su) con la bolla delle pagine; il foglio a tre altezze (chiuso · meta' · pieno) con le linguette. «Come si inquadra» / «Come si usa» al primo avvio, una volta per modo (`localStorage`: `astrolog-planner-gesti`, `astrolog-planner-solare-gesti`, `astrolog-planner-eventi-gesti`).
- **Sequenza per SharpCap** nel Sistema solare e negli Eventi, con «Esporta per SharpCap» come nel Piano della notte (file `.scs`).
- I dati coincidono col Piano della notte: ISS sulla Luna 1/10 alle 03:41:12 (0,8 s, ripresa dalle 03:36 per 10 minuti), Macchia Rossa al meridiano 05:20, le riprese salvate di Luna, Giove, Saturno.
- `pagine/Mappa del transito.html`: la mappa dei posti (Leaflet + OpenStreetMap), aperta in un iframe da PlannerEventi2. I posti sono in `componenti/transiti.js`.

## Cosa e' simulato (nel codice vero lo fa l'app)

- **Dati**: `componenti/dati.js` (notti, progetti, archivio), `dati-cielo.js` e `catalogo.js` (oggetti), `dati-statistiche.js` (sei anni), `transiti.js` (posti per la ISS).
- **Calcoli**: `soglie.js` (`ALsoglie`: verdetto e punteggio della notte, giudizi, impostazioni in `ALsoglie.imp` con la loro fonte). Le funzioni sono il contratto: i numeri arrivano dall'app, il componente li mostra.
- **Cielo**: `cupola.js` e `moto.js` (la cupola, i moti); effemeridi di Sole, Luna e pianeti approssimate; seeing e meteo inventati; lune di Giove e Macchia Rossa con fase simulata.
- **Eventi**: transiti della ISS, eclissi, occultazioni e congiunzioni sono scritti a mano (nell'app: orbita del giorno, canoni di Espenak).
- **Immagini**: Sole, Luna e pianeti nella tavola tengono il posto (SDO, LROC via Aladin, o un disco disegnato). Nell'app sono immagini vere in alta risoluzione.
- **Esportazioni**: «Esporta per SharpCap», «Aggiungi al calendario» (.ics), «Copia» della Diagnostica: a schermo dicono «fatto», il file non si scrive.
- **Adesso**: mercoledi' 30 settembre 2026 a Cima Ekar. L'ora simulata non e' una sola: 21:40 nel cielo profondo, 20:05 nel Sistema solare e negli Eventi. Nel codice vero e' l'ora del computer.

## Cosa non serve portare

- I tre `support.js` (radice, `pagine/`, `componenti/`): sono dell'ambiente di Design.
- Il caricatore `alPronto()` e i `?…` dei Tweaks: servono alla tavola.
- `tema.js`: rimanda ai `var(--…)` del foglio per i colori a schermo; tiene i valori solo per i disegni SVG e canvas (Luna, cupola, grafici). Nel codice vero i colori vengono dal foglio.
- `docs/archivio/`: brief e note chiusi.

## Domande aperte

- Le proposte non ancora decise sono in DECISIONI v58, «Prossimi».
- Tre avvisi del motore di Design (valori vuoti nelle `<option>` di Archivio e Selezione dei frame) compaiono solo durante il caricamento: a schermo le voci ci sono. Nel porting non esistono.
