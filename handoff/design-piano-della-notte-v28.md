# Per Claude Design -- Piano della notte v28: piano automatico e Luna per bersaglio

Da Claude Code, 19/10/2026. **Brief unica dopo la v27**: risponde alla vostra «come sceglie il
piano automatico» e porta le decisioni prese con Marco dopo il confronto con Target Scheduler di
N.I.N.A. Decisioni in `docs/adr/0013-progetti-e-piano-della-notte.md` ("Come sceglie il piano
automatico", "Dalla documentazione di Target Scheduler") e `docs/adr/0023-planner-e-progetti.md`
(tabella delle soglie). Le parole fra «» sono proposte: Marco le approva sulla tavola. Della v27
resta tutto cio' che qui non cambia.

## 1. Nomi dei pulsanti

**«Completa il piano» / «Rifai il piano»**, uguali di notte e di giorno. Non «sequenza»: nel
glossario e' la parola di N.I.N.A. e per questa pagina e' vietata.

## 2. Come sceglie: regole fisse, nessuna impostazione

Una regola per mondo, scritta in una riga d'aiuto sotto i pulsanti. Niente priorita' a mano,
niente punteggi.

### Deep sky e Ricerca

Riga d'aiuto: **«Prima le ore fisse, poi chi scende prima, vicino al suo transito.»**

1. Prima gli eventi a ora fissa.
2. Poi, fra chi passa altezza minima e massima, durata minima, crepuscolo e Luna (sez. 3),
   **chi scende prima**; a pari merito l'ordine delle proposte.
3. Ogni blocco si sposta **il piu' vicino possibile al suo transito**, se c'e' spazio: un oggetto
   che sale aspetta, uno che scende va subito.
4. Un blocco non e' mai piu' corto della durata minima (Impostazioni, 1 h): meno cambi.
5. Dentro il blocco **ogni filtro va nelle ore in cui la sua regola della Luna passa**: la banda
   larga senza Luna o con la Luna lontana, la stretta con la Luna (oggi la larga si spegne
   soltanto: ora si sposta).
6. Le ore «non adatte» del meteo si evitano finche' c'e' altro posto; non diventano un conflitto.

### Sistema solare

Riga d'aiuto: **«Ogni corpo nell'ora col seeing migliore sopra la soglia, vicino al transito.»**

1. Fra le ore sopra l'altezza minima, quelle con la **classe di seeing migliore** (le classi di
   Meteo: buono, incerto); a pari merito la piu' vicina al transito.
2. Senza previsione del seeing (nessuna chiave Meteoblue, o oltre la previsione): **al transito**.
3. **Giove**: se la Macchia Rossa passa al meridiano centrale mentre Giove e' sopra la soglia, il
   blocco si centra su di lei; vince sul seeing.
4. **Luna a mosaico**: piu' alta possibile; i pannelli partono dal terminatore.
5. **Sole** (Giorno): come i pianeti.
6. Meteo: come sopra.

### Il perche' dell'ora, sul blocco

Sul blocco messo dal piano automatico, una riga piccola col motivo:
- «al transito 01:15»;
- «seeing buono 02:00» (al passaggio del mouse: «previsione del seeing, non una misura»);
- «Macchia Rossa al meridiano 23:40»;
- «prima che scenda: sotto 30° alle 23:10»;
- «Hα con la Luna, RGB dopo le 01:30»;
- «Hα dal crepuscolo nautico, 20:05».
Un blocco spostato a mano perde la riga.

## 3. La Luna per bersaglio (Impostazioni › Planner)

**Via «Distanza dalla Luna 40°».** Al suo posto la regola che usano Target Scheduler, ACP e
Voyager: la distanza richiesta dipende dalla fase. A Luna piena serve la distanza piena; dopo un
certo numero di giorni ne basta la meta'. Tre righe, ognuna con due numeri:

| riga | partenza | fonte |
|---|---|---|
| «Luna, banda larga (L, RGB, colore)» | «120° a Luna piena · meta' a 10 giorni» | «ACP e Telescopius; giorni scelti da Marco» |
| «Luna, OIII» | «90° a Luna piena · meta' a 10 giorni» | «Telescopius; giorni scelti da Marco» |
| «Luna, Hα, SII, dual band» | «60° a Luna piena · meta' a 7 giorni» | «Target Scheduler» |

Accanto, **una curva piccola** con le tre linee: la distanza richiesta lungo il mese lunare, col
segno di stanotte («stanotte servono 45° · 32° · 18°»). Riga d'aiuto: «Piu' la Luna e' piena, piu'
il bersaglio deve stare lontano. Con la Luna sotto l'orizzonte non conta.».

La Luna conta solo sopra l'altezza della riga «La Luna conta sopra» (sezione «Luna», v26):
nessun'altra attenuazione.

La regola per fase della sezione «Luna» (25% · 50%) **resta** per il verdetto della notte in Meteo
e Dashboard. Nel Planner e nel Piano il giudizio sul bersaglio usa queste tre righe.

**Dove si vede**:
- Planner e proposte: la pillola diventa «Luna a 74° · servono 45°», col giudizio della banda del
  filtro; con filtri di bande diverse, un giudizio per banda («larga no · Hα si'»).
- Piano: ogni filtro sta solo nelle ore in cui la sua regola passa. Conflitto: «Luna a 38°: in
  banda larga servono 45°.».

## 4. Crepuscolo e altezza massima (Impostazioni › Planner)

- **«Crepuscolo ammesso»**: banda larga «buio astronomico» (fisso); banda stretta a scelta «buio
  astronomico» (partenza) o «crepuscolo nautico». Col nautico scelto, i blocchi a banda stretta
  possono cominciare nella fascia nautica (la fascia resta disegnata).
- **«Altezza massima»**: vuota = spenta. Riga: «Per montature altazimutali o setup che allo zenit
  toccano.». Conflitto: «Sopra 80° dalle 23:40.».

## 5. Tweaks

- un piano Deep sky dopo «Completa il piano»: un oggetto che scende (subito), uno che sale
  (aspetta il transito), un blocco con Hα con la Luna e RGB dopo il tramonto della Luna;
- un piano Sistema solare: Giove centrato sulla Macchia Rossa, Saturno sul seeing migliore, Luna
  a mosaico al punto piu' alto;
- senza chiave Meteoblue: tutti al transito, riga «al transito»;
- Luna al primo quarto e Luna piena: la curva delle Impostazioni e i giudizi che cambiano;
- banda stretta col crepuscolo nautico acceso;
- altezza massima scritta, col conflitto.

## Fuori

- Attenuazione della Luna vicino all'orizzonte («relax» di Target Scheduler): no.
- Priorita' a mano dei progetti, punteggi, scarto automatico delle pose: no.
- Flat, ordine dei filtri (LRGB a giro o in fila), bilanciamento dei pannelli: dopo.

CHANGELOG e DECISIONI come al solito.
