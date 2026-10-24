# 0013 -- Progetti e piano della notte: il Planner fa i progetti, la serata si compone a parte

**Stato:** accettata, 4/10/2026. ADR 0033: lo scarto dei frame lo sceglie l'utente (ADR 0032). ADR 0034 supera la Luna da -5° e i gradini 25/50%: di fabbrica ING 25/65% dall'orizzonte, modificabile in Impostazioni (Marco, 24/10/2026). La spec sta in `docs/domini/piano-della-notte.md` e `docs/domini/planner.md` (24/10/2026).

## Contesto

Il Planner era scritto come "Planner e Progetti", senza dire come si passa da un oggetto da
riprendere a un piano per la notte. L'osservatorio di Marco sara' remotizzato e fara' anche
ricerca (esopianeti, NEO): una notte puo' contenere due transiti e tre NEO in fila, e deve
andare da sola dal crepuscolo all'alba.

## Decisione

- **Il Planner fa i progetti.** Un progetto e' un oggetto, la sua inquadratura su Aladin Lite
  ([ADR 0005](0005-carta-del-cielo-aladin-lite.md)), un setup e un obiettivo in ore per filtro;
  vale tutto l'anno. **Un progetto, un setup** (R1, ADR 0033).
- **L'avanzamento si conta dall'archivio**, mai a mano: frame dell'oggetto e del setup. L'export
  scrive in `OBJECT` il nome che l'app riconosce.
- **La serata si compone nel Piano della notte** (Marco, 19/10/2026), pagina a se':
  `/piano-della-notte`. «Piano» resta vietato per il progetto, «sequenza» per il piano.
- **Un piano per postazione**, tre linguette per tecnica (Deep sky, Sistema solare, Ricerca), una
  per notte e postazione: non si mischiano.
- **Proposte e piano automatico con regole fisse e citate** (Target Scheduler di N.I.N.A., letto
  tutto il 19/10/2026): prima le ore fisse, poi chi scende prima, vicino al transito; nessuna
  priorita' a mano ne' punteggio. Meteo come striscia del verdetto, mai conflitto. Conflitti in
  rosso solo da regole decise.
- **Luna per oggetto con la lorentziana** di Target Scheduler, tre coppie per filtro (120°/10,
  90°/10, 60°/7); supera la distanza unica di 40°.
- **Tempi della notte in Impostazioni, vuoti**, scritti dall'utente col margine dentro: nessuna
  fonte da' tempi standard. **Automazione** della postazione solo Si'/No; la ruota dal setup.
- **Un file per notte**: N.I.N.A. per Deep sky e Ricerca; **SharpCap Pro solo per il Sistema <!-- software-ok -->
  solare** (video, `.scs`), da provare su una postazione vera. Il piano interno non dipende dal
  programma. Formati letti da file veri.
- **Ricerca**: esopianeti, variabili (VizieR), NEO (MPC, uso personale), campagne AAVSO, supernove
  TNS; niente occultazioni asteroidali, scoperta, fotometria.
- **Nell'archivio come oggetti solo DSO e comete**; un DSO trovato online va in una tabella di
  oggetti aggiunti, non nel catalogo. I frame di ricerca e del Sistema solare si tengono fuori
  dalle cartelle dell'archivio.
- **L'app non comanda l'hardware:** cupola, tetto, parcheggio e sicurezza restano a N.I.N.A.
- **Le fonti online** a richiesta, in cache, mai dalla scansione (`domini/catalogo.md`).

## Conseguenze

- L'ordine: prima i DSO (progetti, inquadratura, piano, export); poi esopianeti, variabili e
  campagne AAVSO; poi supernove e transienti; per ultimi comete e NEO.
- Curve di luce e allarmi in tempo reale restano fuori.
- `measure` resta "solo misure": nessun voto e nessuno scarto dei frame.
- La tabella degli oggetti aggiunti nasce in `backend/astrolog/schema.sql` col Planner.
