# 0023 -- Planner e Progetti: inquadratura, mosaico, corredo di prova, filtri, modifiche

**Stato:** accettata, 18/10/2026 (Marco).

## Contesto

L'ADR 0013 dice cos'e' un progetto; le decisioni portate dal vecchio progetto stanno in
`docs/domini/ereditato.md` (A, F). Marco ha descritto il flusso del Planner il 18/10/2026; restavano
aperti rotazione, mosaico, sensori di prova, filtri per camera e modifica di un progetto iniziato.
Ricerca del 18/10/2026 sul codice di N.I.N.A. (MPL-2.0, branch develop), ASCOM, ASTAP, Calabretta
& Greisen 2002, CDS e pagine dei produttori di camere. Proposta per esteso:
`handoff/planner-proposta.md`.

## Decisione

### Il percorso

Trova, Scegli il corredo, Inquadra, Crea (filtri e ore), Salva, Segui. La pagina si chiama
**Progetti** (glossario: progetto, non piano).

### La carta

Resta Aladin Lite v3 (ADR 0005, 0006), versione stabile 3.8.1, licenza LGPL-3.0-or-later
(github.com/cds-astro/aladin-lite). Scartati: Stellarium Web Engine (AGPL-3.0, nessuna release), <!-- software-ok -->
d3-celestial (solo vettoriale, fermo dal 2022), VirtualSky (non open source). Il logo di Aladin
resta visibile ("please leave the Aladin logo and link intact", README); credito "CDS Aladin Sky
Atlas, Unistra/CNRS" con il nome del HiPS (cds.unistra.fr/aladin-org/licences_aladin.html). Il
rettangolo ruotato si disegna come poligono coi vertici calcolati dal backend. Il supporto ai
telefoni non e' finito (README): si prova su tablet e telefono prima del disegno definitivo.

### La rotazione

- Angolo dal Nord verso Est, antiorario: ASCOM ("angle from North... counterclockwise",
  ascom-standards.org/newdocs/rotator-faq.html), ASTAP ("rotate east from north", hnsky.org/astap.htm),
  `frame_wcs.rotation_deg` (CROTA2).
- **Intervallo 0-180°** (Marco): un rettangolo girato di 180° copre lo stesso cielo; "Solutions
  for CROTA2 come in pairs separated by 180°" (Calabretta & Greisen 2002, §6.2). N.I.N.A. con
  rotatore pieno sceglie da solo fra angolo e angolo + 180 (`CenterAndRotate.cs`). Sensore quadrato:
  0-90° (N.I.N.A., escursione "90 Degrees, useful primarily for square sensors").
- L'avanzamento non dipende dall'angolo. L'angolo dei frame si mostra accanto a quello del piano,
  confrontato modulo 180 (modulo 90 sui quadrati), tolleranza 1° (`rotationTolerance = 1.0`,
  `PlateSolveSettings.cs` di N.I.N.A.).

### Il mosaico

Dal Framing Assistant di N.I.N.A. (`FramingAssistantVM.cs`):
- colonne × righe, partenza 1 × 1;
- sovrapposizione in %, **partenza 20 %** (`overlapPercentage = 0.2`); si cambia;
- pannelli numerati riga per riga dall'angolo in alto a sinistra, «Pannello N»;
- centro di ogni pannello sulla sfera: spostamento ruotato poi proiezione gnomonica inversa
  (`Coordinates.cs`, `ShiftGnomonic`), riscritta in Python;
- obiettivo per pannello; il totale e' la somma (ereditato.md A).

### Il corredo

- Corredi veri di Attrezzatura, oppure **corredo di prova**: focale, apertura, riduttore o barlow,
  sensore dalla lista. **Solo per guardare** (Marco): un progetto nasce solo su un corredo vero.
- **Lista dei sensori nostra**: nessun elenco aperto e' riusabile (AstroBin e Telescopius <!-- software-ok -->
  proprietari, Stellarium Oculars 17 reflex). Una riga per geometria, senza marca: nome, pixel <!-- software-ok -->
  (µm), risoluzione (px), URL del produttore; millimetri calcolati. Base: i 36 sensori di
  `old/backend/astrolog/equipment/data/sensori.json`, ricontrollati sulle pagine dei produttori.
  Dove i produttori danno risoluzioni diverse (pixel utili o totali) vale la regola dell'1 % del
  vecchio progetto: sotto, la stessa riga.

### I filtri

- I filtri proposti sono quelli di Attrezzatura usati o scelti per quel corredo.
- Camera a colori: nessun filtro, UV/IR, multibanda, anti-inquinamento. Camera mono: L, R, G, B
  e banda singola. Regola dal numero di bande del filtro; non e' una convenzione pubblicata ma il
  funzionamento della matrice di Bayer.
- Gli altri filtri **nascosti in «Tutti i filtri»**, non tolti (Marco): l'Hα su camera a colori e'
  un uso reale.
- Ore per filtro in ore e minuti; esposizione del frame facoltativa (serve solo a «mancano circa N
  frame»). Schema suggerito dal tipo come in ereditato.md F.

### La pagina Progetti

- Nome: oggetto + ottica + camera, come la produzione.
- Gruppi in corso / in attesa / fermi / finiti; finito proposto dall'app, confermato
  dall'utente; eliminare non tocca i frame (ereditato.md A).
- **Modifiche** (Marco): ore, filtri ed esposizioni sempre libere. Inquadratura, griglia o corredo
  su un progetto iniziato si cambiano **con un avviso numerico**: «{durata} gia' riprese non
  conterebbero piu'», contato sui frame veri. Supera "griglia congelata a progetto iniziato"
  (ereditato.md A).
- «Apri nel Planner» riapre il progetto con inquadratura, griglia, corredo e ore com'erano: e' la
  via per rifare l'inquadratura e per dare l'obiettivo a un progetto gia' cominciato.

### L'avanzamento

Lo scrive la scansione (anche quella automatica sul NAS), non la lettura. Un frame conta se ha
stesso oggetto, stesso corredo e centro risolto dentro il campo del progetto o del pannello. Senza
risoluzione conta per nome, senza pannello. Dashboard e Progetti leggono lo stesso numero.

### Planetario e solare

Nessun piano e nessuna inquadratura: niente da inquadrare ne' ore da accumulare. Effemeridi in
Dashboard (ADR 0019). Transiti della Grande Macchia Rossa e meridiano centrale: idea per dopo,
non decisa.

## Conseguenze

- Nuove tabelle: progetti, pannelli con inquadratura, obiettivi per filtro, oggetti aggiunti
  (ADR 0013). Lo schema si ricrea.
- Dipendenza frontend nuova: `aladin-lite` 3.8.1.
- File nuovo dei sensori, con test che lo confronta coi frame veri.
- `docs/domini/mosaico.md`: la frase "nessuno documenta un valore predefinito" era falsa per
  N.I.N.A.; il riconoscimento dei mosaici dai frame resta senza soglia minima.
- Brief per Design: `handoff/design-planner-progetti.md`.
