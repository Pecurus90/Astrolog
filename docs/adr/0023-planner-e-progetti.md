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
telefoni non e' finito (README): si prova su tablet e telefono prima del disegno definitivo. La
beta 3.9.0 (1/6/2026) non lo aggiunge (CHANGELOG del repository): si resta sulla 3.8.1.

**Mappe a scelta** (Marco), dal registro HiPS del CDS (MocServer, 18/10/2026), solo cache e
nessuno scaricamento (0006):

| mappa | ID HiPS | cielo | pixel | copyright |
|---|---|---|---|---|
| DSS2 colore (partenza) | CDS/P/DSS2/color | 100 % | ordine 9 | STScI/NASA, CDS |
| PanSTARRS colore | CDS/P/PanSTARRS/DR1/color-i-r-g | 76 % | 1.6" | PS1 Science Consortium |
| Hα | simg.de/P/NSNS/DR0_2/halpha8 | 65 % (nord) | 6.4" | Ziegenbalg, CC-BY-NC-SA 4.0 |
| OIII | simg.de/P/NSNS/DR0_2/oiii8 | 65 % (nord) | 6.4" | idem |
| SII | simg.de/P/NSNS/DR0_2/sii8 | 65 % (nord) | 6.4" | idem |
| OIII · Hα · SII | simg.de/P/NSNS/DR0_2/ohs8 | 65 % (nord) | 6.4" | idem |
| Hα sud | CDS/P/SHASSA/H | 100 % | 26" | Swarthmore College |

- NSNS (Northern Sky Narrowband Survey) e' non commerciale: va bene per un'app gratuita; chi
  vendesse l'app dovrebbe toglierla. Il credito va accanto alla carta.
- Fuori: Mellinger ("All rights reserved", la cache sarebbe una copia). "DSS2 Hα" non esiste:
  il DSS2 ha rosso, blu e vicino infrarosso.

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
  (µm), risoluzione (px), URL del produttore; millimetri calcolati. **Solo sensori montati in
  camere astronomiche dedicate**, deep sky e planetario (ZWO, ToupTek, Player One, QHY...); reflex
  e mirrorless fuori (Marco). Base: le righe adatte dei 36 sensori di
  `old/backend/astrolog/equipment/data/sensori.json`, ricontrollate sulle pagine dei produttori.
  Dove i produttori danno risoluzioni diverse (pixel utili o totali) vale la regola dell'1 % del
  vecchio progetto: sotto, la stessa riga.
- **Sensore personalizzato** nel corredo di prova (Marco): pixel (µm) e risoluzione (px), per chi
  ha un sensore fuori lista.

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

- **Nessun progetto**: niente ore da accumulare. Effemeridi in Dashboard (ADR 0019).
- **Simulazione, senza salvataggio** (Marco): Mercurio, Venere, Marte, Giove, Saturno, Urano,
  Nettuno, Luna e Sole, col corredo vero o di prova (barlow e riduttore compresi).
  - Diametro apparente = 2 · atan(raggio / distanza) nella data scelta; distanza da astropy
    (`get_body`), raggi dal NASA Planetary Fact Sheet; partenza stanotte, accanto la prossima
    opposizione. I numeri si leggono dalla fonte quando si scrive il codice.
  - Disegno: disco nel rettangolo del sensore, fase per Mercurio, Venere e Luna, anelli inclinati
    per Saturno (raggio dal NASA Saturnian Rings Fact Sheet, inclinazione da Meeus, Astronomical
    Algorithms, cap. 45). Diametro in pixel accanto.
  - Luna e Sole: anche il mosaico, come per il cielo profondo.
  - **Campionamento planetario**: rapporto focale critico = 2 × pixel / lunghezza d'onda (Nyquist
    sulla frequenza di taglio della diffrazione; vlaiv su Stargazers Lounge, astropix.com). La
    lunghezza d'onda e' quella del filtro scelto; senza filtro o a colori, 400 nm (Marco). Si
    mostra il rapporto del corredo accanto a quello critico. Le regole 5-7 × pixel dei forum non
    entrano: non hanno fonte.
  - Il Sole porta l'avvertenza del filtro solare.
- Transiti della Grande Macchia Rossa e meridiano centrale: idea per dopo, non decisa.

## Conseguenze

- Nuove tabelle: progetti, pannelli con inquadratura, obiettivi per filtro, oggetti aggiunti
  (ADR 0013). Lo schema si ricrea.
- Dipendenza frontend nuova: `aladin-lite` 3.8.1.
- ADR 0006 perde il pulsante "scarica il cielo": solo cache.
- File nuovo dei sensori, con test che lo confronta coi frame veri.
- `docs/domini/mosaico.md`: la frase "nessuno documenta un valore predefinito" era falsa per
  N.I.N.A.; il riconoscimento dei mosaici dai frame resta senza soglia minima.
- Brief per Design: `handoff/design-planner-progetti.md`.
