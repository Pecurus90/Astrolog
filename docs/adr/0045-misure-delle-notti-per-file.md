# 0045 -- Le misure delle notti passano per il file, fino al passo 40

**Stato:** accettata, 8/11/2026 (Marco, passo 33: "ponte per file, ora"). Anticipa una parte del
passo 40; il ponte cade quando la pipeline nuova sostituisce la vecchia (ADR 0030).

## Contesto

Le misure dei frame le scrive la pipeline nuova (`pipeline_measures`, `pipeline_sky`,
`pipeline_sqm`); notti, oggetti, filtri e pannelli li decide la spina. Fra le due non c'e' un
frame comune: la spina riconosce un frame dai pixel (`frame_hash`), la nuova da camera, istante,
dimensioni e posa (`fingerprint`). La finestra della notte (tavola v76, `MisureFrame`) vuole le
misure per notte, oggetto e filtro, coi conteggi della pagina Notti ("su 112 di 120 frame").

Prima scelta (Marco, 8/11): la nuova calcola da se' la notte di ogni frame. Ritirata dopo il
verificatore: legge l'header con regole sue (senza DATE-AVG e MJD-OBS di riserva, senza gradi
sessagesimali ne' longitudine 0-360, lo 0/0 di N.I.N.A. altrove), conta i frame senza oggetto
che la pagina non conta, e i pannelli della spina hanno gia' una regola loro: due notti diverse
per lo stesso frame.

## Decisione

- **Il ponte e' il file**: ogni posizione presente della spina prende il frame della nuova che ha
  letto il file presente alla stessa cartella e allo stesso percorso. La cartella si confronta
  come la confronta il disco (`normcase`, `normpath`): la spina la tiene come l'utente l'ha
  aggiunta, la nuova normalizzata. Un frame della nuova puo' andare a due della spina (stessa
  impronta, pixel diversi): ognuno prende le misure del suo file. Un file che la nuova ha letto e
  non misurera' mai (programma che non legge, riscritto, rotto) porta il suo perche' e non e'
  "misura in corso"; illeggibile o incompleto si riprova, e resta in attesa.
- **Notte, oggetto, filtro vengono dalla spina**, e i frame si contano come la pagina Notti:
  `night_id` non nullo e `copy_of IS NULL` (`spine/counts.py`).
- **Si scrive, non si legge calcolando**: `night_measures.py`, fuori da spina e nuova (SQL sulle
  loro tabelle, nessun import), riscrive a fine giro della nuova, a fine `group` e dopo il bias
  dichiarato di una camera (che riscrive lo SQM) il ponte
  (`night_measure_frames`), per notte, oggetto e filtro mediana, quartili di tipo 7 e andamento
  (24 mediane in ordine di ripresa, la riga sotto ogni tessera; prima 24 classi, 8/11) di ogni
  misura (`night_measures`), e per gruppo frame, in attesa e cosa cambia fra i misurati
  (camera, guadagno, posa: fondo e rumore si confrontano solo se niente) (`night_measure_groups`).
  Sul tuo archivio di prova: 0,6 s per 12 000 frame.
- **Un frame che non si misura** (programma non letto, file riscritto o rotto; un `.fz` finche'
  i compressi non si leggono) conta nei frame della notte e non compare altrove, senza un
  perche' a schermo: i programmi letti li dice il README (Marco, 8/11). Uno illeggibile ora si
  riprova: aspetta, e conta fra quelli in attesa.
- **Le tessere della tavola**: Tilt = `hfd_tilt_pct`, Curvatura = `off_axis_px` (ADR 0044);
  quartili di tipo 7 (Hyndman & Fan 1996, `units.quantile`), sui soli frame col valore.
- **I giudizi di gruppo o setup restano al passo 40** (fuoco, SNR basso, FWHM col limite del
  setup, eccentricita' rispetto al setup, `misure.md`).

## Conseguenze

- `GET /api/v1/nights/{id}/measures` legge le righe scritte e i frame uno per uno; non pagina,
  i frame di una notte non crescono con l'archivio (ADR 0011).
- Misurato sulla copia dell'archivio di Marco (8/11): 12 234 posizioni presenti, tutte col loro
  file nella nuova; 2 898 frame misurati, tutti collegati; 120 notti, 11 828 frame come la pagina.
- Al passo 40 la nuova porta notti, oggetti e pannelli: il ponte e le sue tre tabelle si tolgono
  con la vecchia.
