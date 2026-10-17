# Per Claude Design -- revisione del linguaggio bento prima del porting

Da Claude Code, 17/10/2026. Ho letto `docs/DECISIONI.md` e confrontato Dashboard, Meteo, Notti,
Riepilogo e Archivio con l'app vera: glossario, API, contratti, decisioni scritte. Il disegno
regge: forma, stati e dati simulati dichiarati vanno bene. Sotto c'e' solo cio' che va corretto
prima che io lo porti nell'app. **Non si cambia la forma**, salvo dove e' detto.

Ordine: prima i punti 1-3 (toccano tutte le pagine), poi 4-6.

## 1. Una lingua sola: le parole dell'app

Il glossario dell'app e' la fonte. Sostituire ovunque, pagine, stati e componenti:

| nel disegno | si scrive |
|---|---|
| ore di posa | **ore** ("posa" non si dice) |
| senza tempo | **senza durata** |
| dato mancante | **Non disponibile** |
| esito (della notte) | **verdetto**: "Notte buona", "Notte incerta", "Notte non adatta" |
| esito (di una misura, nelle carte e barrette) | **giudizio**: buono / incerto / non adatto |
| Scansiona ora | **Scansiona** |
| Collega la cartella | **Scegli la cartella** |
| Crea il primo progetto | **Crea un progetto** |
| Sole sempre su | **Il Sole non tramonta: nessuna ora di buio.** |
| Calcolo la notte a ... / Chiedo la previsione per ... | **Caricamento...** (niente prima persona) |
| Previsione non raggiungibile (Dashboard) | **Meteo non raggiungibile** |
| foto (sulla carta dell'Archivio), foto in arrivo | **anteprima** / **Nessuna anteprima**; la foto caricata dall'utente e' la **foto finale** |
| polvere | **polveri** |
| Bortle: "qualita' del cielo", "classe", "scala di Bortle" | **Bortle**, "Bortle, da 1 a 9" |
| Localita' (ricerca del sito) | **Cerca un luogo** |
| Percorso dei file (passo del primo avvio) | **Cartelle** |

Le ore: "4 h 18" e "< 6 min" vanno bene; mai "0 h".
"Qualita'" e' la parola nuova del punteggio da 0 a 100 (punto 2): solo quella.

## 2. La qualita' della notte: una regola sola, calcolata dall'app

Deciso con Marco il 17/10 (ADR 0020 dell'app). **Tutta l'app parla la stessa lingua**: Dashboard,
Meteo, Notti (anche le notti passate), calendario, prossime notti, riepilogo.

- Ogni ora vale **da 0 a 100**: somma dei punti dei fattori. Nuvole 30, seeing 25, Luna 15 (di
  giorno: Sole basso), trasparenza 10, condensa 8, vento 8, jet stream 4. **Pioggia e nuvole
  "non adatta" bloccano**: l'ora vale 0.
- La **Luna** si giudica da quanto schiarisce il cielo **del sito** (dal suo Bortle): sotto
  l'orizzonte non pesa; una falce alta pesa poco; un cielo buio perde piu' di uno di citta'.
- **La notte** = media delle ore di buio; la curva e' il suo andamento.
- **Il verdetto della notte** (buona / incerta / non adatta) viene dal punteggio, con soglie che
  Marco decide. **Escono "buona da 6 ore, incerta da 3"** e ogni altra regola sulle ore: anche
  una notte passata si giudica cosi'.
- **`soglie.js` non decide piu' niente.** Punteggio ora per ora, cosa limita, i tratti di "Come
  va la notte", il verdetto, le ore utili e il giudizio di ogni misura arrivano gia' fatti
  dall'app. Nel disegno restano come dati d'esempio; togliete le formule (`100 - 1,5 x %`, ecc.)
  dai testi e dalla tavola Sistema.
- Le soglie delle barrette sono quelle dell'app, con fonte: nuvole 25 / 50 % (okta WMO), vento
  Beaufort 4 e 5 (20 / 29 km/h), seeing 2 / 4″ (Clear Sky Chart), jet stream 35 m/s (126 km/h),
  condensa sotto 3 °C (FAA), aerosol 0,1 / 1 (NASA), visibilita' sotto 1 km (WMO), qualunque
  pioggia. Dove il disegno ha due gradini e l'app uno, si mostra uno.

## 3. La scansione nel menu delle Impostazioni

Scelta di Marco: la scansione sta nel menu che si apre dall'ingranaggio. Ma una scansione lunga
deve restare **visibile e fermabile da ogni pagina**:
- **mentre lavora**, l'ingranaggio porta un segno (anello che gira o punto), anche sul telefono
  nel menu Altro;
- nel menu: la fase, "file letti su N", "ancora circa ...", **Ferma**; finita, l'esito
  dell'ultima scansione con l'ora;
- interrotta o bloccata: la frase e **Riprendi**.

## 4. Stati che l'app ha gia' e il disegno ha perso

**Dashboard**
- Senza sito: due passi, "Scegli il sito" (primario) e la cartella (lo stato "prima volta" parte
  da sito gia' scelto).
- Prima scansione al lavoro: barra, "file letti su N, ancora circa ...", l'anno "in lettura",
  "casi da confermare: a scansione finita", e nei progetti "Finora la scansione ha trovato N
  oggetti".
- "Da riprendere": le righe con **Rispondi** e "**N frame fuori dai conti**" (frame che non
  stanno in nessuna notte).
- Dettaglio della Luna: eta', distanza, azimut, mese prima e dopo, la legenda con le soglie del
  calendario (impostazioni dell'utente: Luna sotto il 25 %, o almeno 4 ore di buio senza Luna).

**Meteo**
- Risposta non valida del servizio; "Aggiornamento non riuscito"; "Cambio del modello non
  riuscito"; "Nessuna previsione disponibile"; seeing parziale ("media fino alle ..."); seeing
  con dati precedenti.
- **Attribuzioni obbligatorie** in fondo: Open-Meteo, Copernicus CAMS (con l'anno e la frase
  sulla responsabilita'), Meteoblue. E "orari in ora locale del sito".
- Le carte "Nuvole basse" e "Luna" fra le misure giudicate: o restano, o si dice dove finiscono.

**Notti**
- **Senza durata** accanto alle ore, per notte, oggetto e filtro (frame che non dicono il tempo:
  non valgono zero, si contano a parte).
- "Le copie calibrate non sono contate".
- I frame che nessuna notte raccoglie, tre righe: **da confermare / senza sito / senza data**.
- Scansione in corso con la percentuale.
- I quattro modi di non avere notti (nessuna cartella, nessun frame, senza sito, tutti fermi).

**Archivio**
- **Oggetto non identificato** e pannello senza oggetto ("Nessun oggetto identificato").
- **ASTAP assente**: frame senza oggetto finche' il programma non c'e', con il rimando alle
  Impostazioni.
- Filtri dell'Archivio che l'app ha: **periodo** (anno o date), **sito**, **ottica**, **camera**,
  catalogo, "solo mosaici"; una tendina compare solo se c'e' una scelta. Il periodo restringe ore
  e frame della riga.
- Ordini: **nome, ore, piu' recenti** (come il disegno).
- Archivio vuoto con "Aggiungi cartelle".

## 5. Archivio: tre linguette e "Aggiungi oggetto" (ADR 0019)

Deciso con Marco il 17/10:
- Tre linguette: **Deep sky** (com'e' oggi, tutto automatico dai FITS), **Sole**, **Sistema
  solare** (pianeti, Luna, comete, asteroidi). Comete e asteroidi ripresi in FITS arrivano da
  soli nella terza.
- Fuori dal deep sky si entra con **Aggiungi oggetto**: tipo (Sole, pianeta, Luna, cometa,
  asteroide, altro), poi una o piu' fonti: un **file SER indicato per percorso** (non si
  carica), il **log** del programma di ripresa, la **foto finale**, i **campi a mano**.
  Obbligatori: tipo, oggetto, data, sito; ora fortemente consigliata (senza, cio' che ne dipende
  dice "Non disponibile"); per il Sole il filtro (H-alfa, luce bianca, CaK) facoltativo.
- Ogni campo dice da dove viene (dal SER, dal log, dal nome del file, scritto a mano) e a mano
  si corregge sempre.
- Le metriche di queste riprese (altezza, diametro, fase, meridiano centrale, coordinate di
  Carrington per il Sole, meteo e attivita' solare del giorno) le calcola l'app: simulate e
  dette tali.

## 6. Dati: cosa esiste e cosa no

- **Metriche dei frame** (riepilogo): le misura `sep`, non Astropy. Quelle che avranno un
  posto: FWHM, HFD, stelle, segnale/rumore, eccentricita', fondo cielo, rumore del fondo. Altezza
  e massa d'aria si calcolano dall'ora del frame. Oggi nessuna e' ancora misurata: tutto il
  riepilogo e' simulato, e va detto.
- **Nome comune** degli oggetti: il catalogo lo ha solo per il 3 % circa. Non puo' essere la
  riga principale di una carta; il nome e' quello di catalogo, il comune sotto quando c'e'.
- **Distanza ed estensione in anni luce**: la distanza c'e' per una parte del catalogo, da
  contare; lo stato "distanza non nota" sara' frequente.
- **Pianeti**: oggi l'app ne calcola quattro (Saturno, Giove, Marte, Venere); gli altri e la
  vista Sistema solare arrivano con le effemeridi.
- **Progetti, anno precedente a confronto, ore per filtro dell'anno, filtri delle Notti, dati
  del Sole (NOAA), probabilita' di pioggia, confronto ora per ora fra modelli**: futuri, restano
  simulati e dichiarati.

## Dopo

Quando il punto 1-6 e' fatto, aggiornate `CHANGELOG.md` e `DECISIONI.md`. Restano da disegnare,
nel linguaggio nuovo: **primo avvio** (con le parole del punto 1), **Attrezzatura**, **Da
confermare** come pagina, **Impostazioni**, **Scansioni**, **Cerca** (Ctrl K, quattro gruppi:
oggetti, notti, pezzi e filtri, siti).
