# Per Claude Code · porting (v76, 7/11/2026)

Da Claude Design. Versione finale dopo il brief del 6/11 (v60–v73): sostituisce in `handoff/design/` la consegna v58.6. La tavola e' la specifica, aspetto e funzioni (regola del 27/10); controlla ogni pagina con la lista di /porta-tavola prima di portarla. Sostituisce `docs/archivio/per-claude-code-porting-v32.md` (resta valido per tutto cio' che qui non e' detto).

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

Tavole degli stati difficili: Attrezzatura, Da confermare, Dashboard, Impostazioni, Meteo, Notti, Primo avvio, Progetti, Riepilogo, Selezione dei frame (`pagine/* stati.dc.html`). Planner, Piano della notte, Statistiche portano i loro stati nei Tweaks e in `?stato=`. Da confermare apre una sezione con `?sezione=` (`siti`, `senza-data`).

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

## v59 (27/10): i ritocchi dopo l'inventario

Fatti nella tavola, che resta la specifica (DECISIONI v59): Luna 25 / 65 / 0°; Ore di posa al posto delle ore utili (`soglie.posa…`, nel Planner «visibili»); Attrezzatura «Elimina» (Modulo `m.elimina`); «Progetti finiti» in Da confermare, chiesta una volta dalla Dashboard. Classi nuove nel foglio: `al-c-modulo__elimina…`, `al-c-modulo__conferma…`, `al-conf__fin…`. Chiusi poi in v60 (Meteo del Sole: «Sole non disponibile») e v72 (progetto senza obiettivo).

## v60–v73 (6–7/11): il brief prima del porting

Il brief intero e' in `docs/archivio/brief-porting-v59.md`; ogni punto ha la sua sezione in DECISIONI, con le parole a schermo. In breve, cosa cambia per il porting:

- **Regole comuni (v60)**: Trasparenza al posto della Qualita' (`soglie.notte`), cielo in quattro classi okta (`soglie.cielo`), ore di posa, «rispetto al gruppo» al posto del MAD, virgola decimale con una casa sola (`AL.virg` in `tema.js`), colore mai da solo, bersagli da 44. **Telaio** con la prop `app` (normale · caricamento · errore): le pagine passano solo lo stato.
- **Dashboard e Meteo (v61)**: meteo tre per riga sul telefono, calendario della Luna a tre gradini (CalendarioNotti `gradini`), seeing senza chiave da 126 km/h, Sole non disponibile (prop `sole`), otto stati nuovi.
- **Misure dei frame (v62)**: «Altre misure» a gruppi, trasparenza e nuvole con una serie, tilt in px, gradiente in unita' di rumore, frame non confrontabili.
- **Selezione dei frame (v63)**: le partenze si salvano solo in Impostazioni › Selezione dei frame (`ALsoglie.selezione`); sei criteri nuovi; gruppo con guadagno.
- **Archivio, Riepilogo, Notti (v64–v65)**: stili fissi nel foglio; Luna col lato illuminato (`Luna.lato`); Carica altre in corso e non riuscito.
- **Da confermare e Attrezzatura (v66–v67)**: filtri a piu' bande, Correggi, Montatura, Frame senza data; frame da rielaborare per ogni modifica che cambia il cielo.
- **Impostazioni e Primo avvio (v68)**: siti completi, carta «Il cielo del sito» con le quattro vie, ASTAP con D50, chiavi solo in Servizi, Lingua, Cartelle, Backup, Automazione per postazione.
- **Statistiche (v69)**: Bortle misurato (4 mesi), grafici da tastiera.
- **Telaio e Sistema (v70)**: pastiglia Stanotte (`menu="stanotte"`); la Carta del cielo vive solo nel Planner.
- **Planner (v71)**: OpenNGC e stelle fino a mag 6,5 nel pacchetto dell'app (la tavola tiene un catalogo ridotto); immagini dal proxy dell'app, Sole da Helioviewer; un progetto per setup; mosaici 20 %; ore e pose di partenza in Impostazioni (`planner.oreNuovo`, `planner.posaL`, `planner.posaS`); Luna per filtro nei criteri; campionamento col seeing; «mesi buoni». PlannerEventi2: `preset.mappa` (spento finche' i servizi delle mappe non sono scelti: restano striscia, sito e Google Maps) e `preset.orbita` («orbita in caricamento»).
- **Progetti (v72)**: Reinquadra; doppione con un altro setup, Prima di salvare con «{durata} già riprese non conterebbero più» (la conta l'app), errore di salvataggio, Elimina non riuscito; prima scansione «Tutti finiti · Scelgo io · Decido dopo»; progetto senza obiettivo con «Scrivi l'obiettivo».
- **Piano della notte (v73)**: proposte «4 h di posa».

**Restano disegnati, arrivano dopo**: esportazioni N.I.N.A. e SharpCap, ricerche online (JPL, MPC, VizieR, AAVSO, TNS), eventi dall'orbita vera, la mappa del transito, la carta Sole del Meteo, Diagnostica e «Ultimo tentativo» dei servizi.

**Stato**: v60–v73 da approvare da Marco sulla tavola, parole comprese.

## v76 (7/11): le 11 voci del secondo controllo

1. **Selezione dei frame, Gradiente**: «Gradiente del fondo» in unità di rumore, come le Misure (grad / 100 × fondo / rumore; rumore simulato √fondo × 1,6). Criteri e formula («Gradiente del fondo · in unità di rumore»).
2. **Virgola**: Statistiche (assi SQM, eccentricità, ore con passo 2,5, legenda), Progetti (eccentricità, SQM), Piano della notte (mag), Attrezzatura «1,25″». Planner «22 080 oggetti» con lo spazio sottile.
3. **Dashboard**: la pillola della Luna prende altezza e ora dal massimo della curva della stessa carta.
4. **Meteo**: raffiche derivate = vento × 1,5 (prima 1,8): con la notte d'esempio restano sotto 25 km/h accanto al Vento «buona».
5. **Dalla mappa senza chiave**: si può scegliere (come Impostazioni); SezioneServizi ora dice «si può scegliere ma non dà un cielo finché non la aggiungi».
6. **Attrezzatura, Unisci a**: nel modulo «{n} frame da rielaborare: passano a {nome}»; al salvataggio parte l'avviso dei frame da rielaborare.
7. **Curvatura**: «HFD oltre il 75% verso gli angoli meno HFD al centro».
8. **ASTAP**: un solo percorso d'esempio, `/opt/astap/astap_cli` (placeholder e predefinito, Primo avvio, Impostazioni, SezioneServizi).
9. **Cartella d'esempio**: `Condivisa/Astro` al posto di nas/astro.
10. **Cerca**: tolta «Carta del cielo».
11. **Foglio**: `alPulse` e `alHalo` in `astrolog.css`.

## v75 (7/11): le 15 voci del controllo della v73

Da `handoff/per-design.md`, sezione «Da dare». Una riga per voce, nell'ordine della coda:

1. **skPulse nel foglio**: `astrolog.css` definisce ora tutti i movimenti che nomina (`skPulse`, `alSpin`, `alFill` con `@property --p`, `alGrow`, `alGrowX`, `alFade`, `alPop`, `alWipe`), accanto ad `alIn`. Gli helmet delle tavole li ripetono ancora, ma non servono piu'.
2. **Curvatura** (MisureFrame): l'aberrazione fuori asse di ASTAP, HFD verso gli angoli meno HFD del centro, in px col segno e in ″ con la scala («+0,29 px · +0,6″»; senza scala solo px). Nessun giudizio. In tessera, nella tabella per filtro, nel sensore e nel frame (tessera «Curvatura» a parte; «Tilt» resta in % col giudizio 10 / 20 %).
3. **Gradiente**: tolta la % del fondo (tessera e frame); restano «× rumore» e il lato chiaro.
4. **FWHMTilt e FWHMCurvature**: tessera «Tilt · curvatura dalla FWHM», due numeri puri, «numeri puri: fra gli angoli · angoli e centro».
5. **Fonti della Selezione** (`soglie.js`, `SELM`): «Rousseeuw & Croux 1993» per ogni 2,5 rispetto al gruppo; altezza «massa d'aria 2 (AAVSO)»; Luna sorta «dall'orizzonte, quando sorge»; Luna illuminata «regola di ING: grigio fino a 0,65». Nessun ADR a schermo.
6. **Parole**: «ore visibili» in Notti; «ore di posa col Sole alto» in Meteo stati; «verdetto» in Meteo; Statistiche «notti di ripresa», «nessuna ripresa», «non hai ripreso» al posto di uscite e uscito; tutte le percentuali a schermo attaccate («96%»), anche in `soglie.cieloT`, Planner, Telaio, Selezione, Statistiche, PlannerEventi2 e PlannerSolare2.
7. **Virgola in Statistiche**: ogni `toFixed` a schermo passa da `AL.virg`.
8. **Luna**: 25% «regola di ING: buio sotto 0,25»; 0° «dall'orizzonte, quando sorge» (Impostazioni e `soglie.imp`).
9. **SQM a mano**: da 7 a 23, «Un numero da 7 a 23.».
10. **Dalla mappa**: «… quando bastano, propongono di correggerlo.»
11. **Servizio del cielo**: «Servizio del cielo · lightpollutionmap.info», World Atlas della luce artificiale, chiave gratuita chiesta con una email all'autore, 500 richieste al giorno; «Dove si prende ↗» apre https://www.lightpollutionmap.info/.
12. **Piano della notte, Ricerca senza chiavi**: «Serve la chiave AAVSO in Impostazioni › Servizi.» (e TNS), rimando «Impostazioni › Servizi ↗» a `Impostazioni.dc.html?sezione=servizi`.
13. **Archivio**: lo stato «errore dell'app» c'era gia' (Tweak «stato» o `?stato=errore dell'app`): lo disegna il Telaio con la prop `app="errore"`, «AstroLog non risponde, riprova» e Riprova, come nelle altre pagine. Stili fissi nel foglio: la radice ha `data-formato` e le misure del formato sono classi (`al-arch__pagina`, `__carta-testo`, `__elenco-righe`, `__solo-desk`, `__elenco-ore`, `__campo-riga`, `__testo-13--forte`). Restano inline solo i dati: colonne delle anteprime per produzione e l'immagine caricata.
14. **Bortle misurato**: il buco fra i mesi si conta in giro sui 12 (Statistiche, Impostazioni `regolaOk`); con poche misure «Servono notti in almeno 4 mesi, senza buchi di oltre 3: finora {n} notti in {m} mesi.» (anche in Misure dei frame e in Impostazioni).
15. **NAS**: Selezione «La cartella … è in sola lettura», «Erano su un disco senza cestino», «… sono su un disco senza cestino»; Primo avvio, percorso d'esempio `/opt/astap/astap_cli`.
16. **Dati d'esempio**: Dashboard raffiche 22 km/h con «buona»; Luna «sale fino a 64° alle 05:30», dentro il buio.

**Risposta v68 chiusa**: le quattro vie del cielo sono quelle dell'app; il servizio e' lightpollutionmap.info.

## Domande aperte

- Le proposte non ancora decise sono in DECISIONI v58, «Prossimi».
- Tre avvisi del motore di Design (valori vuoti nelle `<option>` di Archivio e Selezione dei frame) compaiono solo durante il caricamento: a schermo le voci ci sono. Nel porting non esistono.
