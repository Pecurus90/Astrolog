# Per Claude Design -- correzioni al linguaggio bento (v9) prima del porting

Da Claude Code, 17/10/2026. Ho confrontato la v9 (Dashboard, Meteo, Notti, Riepilogo, Archivio,
Sistema e i componenti) con l'app vera: glossario, API, contratti, decisioni scritte.

**Marco: estetica e comportamenti restano come sono.** Qui si correggono parole, dati, regole e
stati mancanti. Dove serve un pezzo nuovo (punti 3 e 5) si usa il linguaggio e i componenti che
ci sono gia'. Catture prima e dopo come nel riordino: uguali, salvo cio' che si dichiara.

## 1. Le parole dell'app

Il glossario dell'app e' la fonte. Ovunque: pagine, stati, componenti, `tema.js`, `dati.js`.

| oggi | si scrive | dove l'ho visto |
|---|---|---|
| ore di posa | **ore** ("posa" non si dice) | Notti, Riepilogo, DECISIONI |
| senza tempo | **senza durata** | `tema.js` `AL.ore()`, Notti |
| ? dato mancante / dato mancante | **? Non disponibile** | `CardMeteo` (stato mancante), `Pillola` (esito mancante), Dashboard senza previsione |
| senza filtro | **nessun filtro** | `tema.js` `FD.senza` |
| esito (della notte) | **verdetto**: Notte buona / incerta / non adatta | Dashboard, Meteo, Notti, Riepilogo |
| esito (di una misura) | **giudizio**: buono / incerto / non adatto | carte e barrette |
| Scansiona ora | **Scansiona** | menu Impostazioni |
| Collega la cartella | **Scegli la cartella** | Dashboard, prima volta |
| Crea il primo progetto | **Crea un progetto** | Dashboard, prima volta |
| Sole sempre su | **Il Sole non tramonta: nessuna ora di buio.** | Meteo |
| Calcolo la notte a ... / Chiedo la previsione per ... | **Caricamento...** (niente prima persona) | scheletri |
| Previsione non raggiungibile (Dashboard) | **Meteo non raggiungibile** | Dashboard |
| foto, foto in arrivo (carte dell'Archivio) | **anteprima**, **Nessuna anteprima**; quella caricata dall'utente e' la **foto finale** | Archivio |
| polvere | **polveri** | Meteo, altre misure |
| Bortle: qualita' del cielo, classe, scala di Bortle | **Bortle**; "Bortle, da 1 a 9" | ovunque |
| Localita' (ricerca del sito) | **Cerca un luogo** | sito |
| Percorso dei file (primo avvio) | **Cartelle** | primo avvio |

"Qualita'" resta: e' la parola del punteggio da 0 a 100 (punto 2), solo per quello.
Ore "4 h 18" e "< 6 min": vanno bene; mai "0 h".

## 2. La qualita': una regola sola, calcolata dall'app

Deciso con Marco il 17/10 (ADR 0020 dell'app). Tutta l'app parla la stessa lingua: Dashboard,
Meteo, Notti (anche le notti passate), calendario, prossime notti, Riepilogo.

- Ogni ora vale **da 0 a 100**: **somma** dei punti dei fattori (non piu' il peggiore). Nuvole
  30, seeing 25, Luna 15 (di giorno: Sole basso), trasparenza 10, condensa 8, vento 8, jet
  stream 4. **Pioggia e nuvole dal 50 % bloccano**: l'ora vale 0.
- **"Cosa limita"** resta: e' il fattore che ha perso piu' punti in quell'ora.
- **Luna**: si giudica da quanto schiarisce il cielo **del sito** (dal suo Bortle). Sotto
  l'orizzonte non pesa; una falce alta pesa poco; un cielo buio perde piu' di uno di citta'.
- **La notte** = media delle ore di buio; la curva e' il suo andamento.
- **Il verdetto** (buona / incerta / non adatta) viene dal punteggio della notte, con soglie che
  decide Marco. **Esce "buona da 6 ore, incerta da 3"** (`ALsoglie.oreEsito`), anche per le
  notti passate e per il giorno.
- **`soglie.js` non decide piu' niente**: punteggio ora per ora, cosa limita, tratti di "Come va
  la notte", verdetto, ore utili e giudizio di ogni misura arrivano dall'app. Nel disegno
  restano dati d'esempio; via le formule dai testi, da DECISIONI e dalla tavola Sistema.
- Barrette e giudizi delle misure con le soglie dell'app, che hanno una fonte: nuvole 25 / 50 %
  (okta WMO), vento 20 / 29 km/h (Beaufort 4 e 5), seeing 2 / 4″ (Clear Sky Chart), jet stream
  126 km/h (meteoblue, 35 m/s), condensa sotto 3 °C (FAA), aerosol 0,1 / 1 (NASA), visibilita'
  sotto 1 km (WMO), qualunque pioggia. Dove il disegno ha due gradini e l'app uno, si mostra uno.
  Umidita' e probabilita' di pioggia non hanno giudizio: solo valore.

## 3. La scansione nel menu dell'ingranaggio

Scelta di Marco: "Scansiona" sta nel menu delle Impostazioni. Ma una scansione dura anche ore, e
deve restare **visibile e fermabile da ogni pagina**:
- **mentre lavora** l'ingranaggio porta un segno (anello che gira, o punto), anche "Altro" sul
  telefono;
- nel menu: la fase, "file letti su N", "ancora circa ...", **Ferma**; finita, l'esito
  dell'ultima scansione con l'ora;
- interrotta o bloccata: la frase e **Riprendi**.

## 4. Stati che l'app ha gia' e il disegno non ha

Con i componenti che ci sono (Avviso riga o blocco, Pillola, Carta).

**Dashboard**
- Senza sito: due passi, "Scegli il sito" (primario) e la cartella. Oggi "prima volta" parte da
  sito gia' scelto.
- Prima scansione al lavoro: barra, "file letti su N, ancora circa ...", l'anno "in lettura",
  "casi da confermare: a scansione finita"; nei progetti "Finora la scansione ha trovato N
  oggetti".
- "Da riprendere": righe con **Rispondi** e "**N frame fuori dai conti**" (frame che non stanno
  in nessuna notte).
- Dettaglio della Luna (toccando la carta): eta', distanza, azimut, mese prima e dopo, legenda
  con le soglie del calendario (impostazioni dell'utente: Luna sotto il 25 %, o almeno 4 ore di
  buio senza Luna).

**Meteo**
- "Risposta non valida dal servizio"; "Aggiornamento non riuscito"; "Cambio del modello non
  riuscito"; "Nessuna previsione disponibile"; seeing parziale ("media fino alle ..."); seeing
  con dati precedenti.
- **Attribuzioni obbligatorie** in fondo: Open-Meteo, Copernicus CAMS (con l'anno e la frase
  sulla responsabilita'), Meteoblue; e "orari in ora locale del sito".
- Le carte "Nuvole basse" e "Luna": l'app oggi le giudica. Dite dove finiscono (grafico e
  riquadro va bene).

**Notti**
- **Senza durata** accanto alle ore, per notte, oggetto e filtro: frame che non dicono il tempo
  non valgono zero, si contano a parte.
- "Le copie calibrate non sono contate".
- I frame che nessuna notte raccoglie, tre righe: **da confermare / senza sito / senza data**.
- Scansione in corso con la percentuale.
- I quattro modi di non avere notti: nessuna cartella, nessun frame, senza sito, tutti fermi su
  una risposta.

**Archivio**
- **Nessun oggetto identificato** (gruppo e pannello senza oggetto).
- **ASTAP assente**: frame senza oggetto finche' il programma non c'e', col rimando alle
  Impostazioni.
- Filtri che l'app ha gia': **periodo** (anno o date), **sito**, **ottica**, **camera**,
  catalogo, solo mosaici. Una tendina compare solo se c'e' una scelta; il periodo restringe ore e
  frame della carta.
- Ordini: **nome, ore, piu' recenti** (come ora).
- Archivio vuoto con "Aggiungi cartelle".

## 5. Archivio: tre linguette e "Aggiungi oggetto" (ADR 0019)

Deciso con Marco il 17/10. Pezzi nuovi, nel linguaggio di oggi (pillole per le linguette,
finestra come il Riepilogo per il modulo):
- Linguette **Deep sky** (com'e' oggi, automatico dai FITS), **Sole**, **Sistema solare**
  (pianeti, Luna, comete, asteroidi). Comete e asteroidi in FITS arrivano da soli nella terza.
- **Aggiungi oggetto**: tipo (Sole, pianeta, Luna, cometa, asteroide, altro), poi una o piu'
  fonti: un **file SER indicato per percorso** (non si carica), il **log** del programma di
  ripresa, la **foto finale**, i **campi a mano**. Obbligatori: tipo, oggetto, data, sito; ora
  fortemente consigliata (senza, cio' che ne dipende dice "Non disponibile"); per il Sole il
  filtro (H-alfa, luce bianca, CaK) facoltativo.
- Ogni campo dice da dove viene (dal SER, dal log, dal nome del file, scritto a mano) e si
  corregge sempre a mano.
- Metriche di queste riprese (altezza, diametro, fase, meridiano centrale, coordinate di
  Carrington, meteo e attivita' solare del giorno): le calcola l'app; simulate e dette tali.

## 6. Dati: cosa esiste e cosa no

- **Metriche dei frame** (Riepilogo): le misurera' `sep`, non Astropy (ADR 0007). Avranno un
  posto: FWHM, HFD, stelle, segnale/rumore, eccentricita', fondo cielo, rumore del fondo; altezza
  e massa d'aria dall'ora del frame. Oggi nessuna e' misurata: il Riepilogo e' tutto simulato,
  e va detto nella tavola.
- **Nome comune**: il catalogo lo ha per il 3 % circa degli oggetti. Il nome di catalogo e' la
  riga principale, il comune sotto quando c'e'.
- **Distanza ed estensione in anni luce**: la distanza c'e' per una parte del catalogo; "distanza
  non nota" sara' frequente.
- **Pianeti**: oggi l'app ne calcola quattro (Saturno, Giove, Marte, Venere); gli altri e la vista
  Sistema solare arrivano con le effemeridi.
- **Progetti, anno precedente a confronto, ore per filtro dell'anno, filtri delle Notti, dati
  del Sole (NOAA), probabilita' di pioggia, confronto ora per ora fra modelli**: futuri, restano
  simulati e dichiarati.

## 7. Per il porting: il foglio (uguale al pixel)

Nell'app i componenti sono React, coi testi tradotti e i dati dall'API: il codice `.dc.html` non
si copia. Si copia il CSS. Per questo, senza cambiare niente a vista:
- **token come variabili CSS** (`--carta`, `--testo`, `--accento`, ...) per i due modi e i cinque
  accenti (`[data-modo]`, `[data-accento]`), al posto dei valori calcolati da `tema.js`;
- **una classe per ogni componente e stato** (carta, pillola, avviso, striscia, card meteo,
  barra, menu, calendario, filtri, scheletro, finestra), al posto degli stili scritti nel markup;
- **animazioni in CSS** dove si puo', con `prefers-reduced-motion`;
- **i caratteri** (Outfit nel modo scuro, Plus Jakarta Sans nel chiaro: confermate pesi usati)
  come file nel progetto, mai da una rete esterna;
- un `astrolog.css` intero, e le pagine che lo usano.

## Dopo

Aggiornate `CHANGELOG.md` (v10) e `DECISIONI.md`. Restano da disegnare nel linguaggio nuovo:
**primo avvio** (con le parole del punto 1), **Attrezzatura**, **Da confermare** come pagina,
**Impostazioni**, **Scansioni**, **Cerca** (Ctrl K, quattro gruppi: oggetti, notti, pezzi e
filtri, siti).
