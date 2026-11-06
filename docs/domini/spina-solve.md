# La spina: `solve` -- contratto

Lo stadio `solve` risolve ogni frame sul cielo con ASTAP.
Cio' che vale per tutta la catena sta in [`spina.md`](spina.md).

## Cosa chiede l'utente

| richiesta | prova |
|---|---|
| Ogni frame viene risolto sul cielo da ASTAP, prima uno per sessione, poi tutti; il FITS non viene mai modificato | `test_solve_order_one_per_group`, `test_solve_never_writes_fits`, `test_solve_field_from_the_header` |
| Un frame risolto una volta non si ri-risolve dopo un reset: la cache per hash lo ricorda | `test_solve_cache_by_hash` |
| Un frame che ASTAP non risolve e' "non risolto" con il suo perche', e l'archivio va avanti | `test_solve_failure_is_a_reason` |

## Le decisioni

**La "sessione" del solver si calcola quando serve, e non si scrive da nessuna parte**:
oggetto, notte della posa e i due pezzi come li scrive l'header, raggruppati nella query di chi la
usa -- che e' solo il solver, per il suo "prima un frame per sessione". Era una colonna su ogni
frame: un dato salvato per un lettore solo, che invecchiava a ogni modifica. Si guarda l'oggetto
**grezzo** perche' qui si mette in fila, non si contano ore: `M31` e `M 31` in due gruppi
costano un frame risolto in piu' e nient'altro. Le sessioni vere, col fuso del sito, le fa
`group`.

**ASTAP**: `astap_cli -f <file> -o <cache>/<frame_hash> -fov <campo> -z 0`, `-ra/-spd` e raggio
30 gradi con un indizio, altrimenti cieco; mai `-update` ne' `-extract`. Pipeline nuova, solo dopo nessuna soluzione: `-z 1`, `-fov 0`, poi cieca col campo (failover di N.I.N.A.); senza tipo un tentativo; timeout ferma (dopo un no: `no_solution`). Dal WCS (`pipeline/footprint.py`, Paper II): scala sqrt|det CD|, specchiato se det<0 con righe dall'alto (N.I.N.A., ASIAIR; misurato su copie specchiate; ROWORDER con 'BOT' rovescia, letto come ASTAP lo legge per il Bayer), skew, campo, 4 angoli TAN. Nome fuori dalla code page
ANSI: 8.3 o copia; cartella di lavoro illeggibile: `path_unsupported`, ferma; `.fz` con `astap_cli` < 2026.07.17 (la GUI dal 16): `fz_unsupported`.

**Il campo si calcola, ed e' la leva della velocita'.** `-fov` e' l'altezza del campo
in gradi, e si ricava da `naxis2`, `pixel_size_um` e `focal_mm_raw` -- tutti gia' nell'header.
Misurato su frame veri da 26 megapixel di due setup diversi: **0,2 s** col campo dato,
**2,3 s** con `-fov 0`, **23 s** senza nemmeno il puntamento. La leva non e' il
raggio di ricerca, e' il campo; dove l'header non dice focale o pixel si passa `0` e si
paga la differenza. Tetto di tempo 60 s finche' non c'e' il limite di previsione (ADR 0036, 0039).

**Ordine: prima un frame per sessione**, poi tutti gli altri dai piu' recenti -- e un frame
il cui header non porta il puntamento **eredita l'indizio da un frame gia' risolto dello
stesso oggetto** (la regola esatta e' piu' sotto): e' cio' che lo salva dai 23 secondi. La
cache `cache/solve/<frame_hash>.ini` e `.wcs` e' immutabile: un reset la rilegge invece di
ri-risolvere.

**HFD e stelle le misura `measure`** dai pixel, nella pipeline nuova (ADR 0022, 0033;
[`misure.md`](misure.md)): la passata `-analyse` (+0,3 s a frame) e `frame_metrics` sono uscite
anche dalla vecchia, che non le leggeva. **Il tilt no**: servirebbe `-extract`, che scrive un CSV **accanto al
FITS dell'utente** ignorando `-o` e la cartella di lavoro (verificato) -- e su una
condivisione in sola lettura fallirebbe. Tilt, eccentricita' e fondo cielo nascono con
`measure`, dove i pixel li leggiamo noi e non si scrive niente. La rotazione e' quella
misurata (CROTA2 da `CD`), mai `OBJCTROT`: ha il segno opposto a `CROTA2`, un offset che cambia a
ogni rimontaggio della camera, e vale `0` come sentinella su meta' dei frame. **Anche il centro si
misura**: quello dell'header sbaglia di qualche minuto d'arco, e a volte di quasi mezzo grado.

**I numeri che ASTAP stampa portano la virgola decimale** (`HFD_MEDIAN=9,1`): si leggono
sapendolo, o su una macchina italiana diventano zero in silenzio.

**Un frame non risolto porta un codice**, mai una frase. Resta in archivio, le sue ore
contano, il campo non si disegna, e la pagina dice quante sono e perche'. Ma i codici sono di
due specie, e confonderle e' un vicolo cieco:

- **si riprova da sola**: `astap_missing` (il solver non c'e' ancora), `file_missing` (il
  disco e' staccato) e `no_star_database` (ASTAP c'e' ma il suo catalogo stellare no). Il frame
  resta **da fare**, non fallito. Segnarlo fallito vorrebbe dire che chi installa ASTAP il
  giorno dopo, o riattacca il disco, o scarica il catalogo, non risolverebbe mai piu' niente:
  nessuno lo rimetterebbe in coda, e il pulsante direbbe "niente da fare";
- **e' andata cosi'**: `no_stars`, `no_solution`, `timeout`, `internal_error`, `unreadable` (ASTAP
  non apre il file). `failed`, si riprova se qualcuno lo chiede. Pipeline nuova: ogni esito scritto, con versione di ASTAP, catalogo e durata; `timeout`, `crashed`, `unreadable` una volta alla passata dopo, poi fermi finche' cambia ASTAP o il catalogo installato; `fz_unsupported` finche' cambia ASTAP.

**E il catalogo mancante ferma la corsa**, invece di ripetersi frame per frame. Il catalogo di
ASTAP e' un **download separato**, ed e' l'errore di installazione piu' comune: senza, *ogni*
frame fallira' identico, e lanciare il solver cinquemila volte per scoprirlo e' un'ora buttata
mentre la ricevuta direbbe solo "in attesa" senza dire perche'. Si ferma alla prima e lo
dichiara: lo stadio risulta **in errore col suo motivo**, non completato -- senza, la corsa
diceva `1 / 1`, completato e zero risolti su un archivio da cinquemila frame.
Le frasi su cui si riconosce sono quelle vere di ASTAP e sono **due**, perche' i modi di avere
il catalogo a meta' sono due: `No star database found.` (non scaricato) e `Error reading star
database.` (scaricato a meta', o unzip andato male) -- lette da CLI-2025.11.19, non a memoria.
Si confrontano in minuscolo e per contenimento, perche' il testo cambia da una versione
all'altra ma la parola chiave no.

**Il binning non moltiplica il campo.** `XPIXSZ` per convenzione **include il binning**:
*FITS File Header Definitions* (Diffraction Limited, la definizione da cui la chiave e' nata)
dice "Includes binning", N.I.N.A. lo fa dalla 1.10 (17/7/2020), l'header vero dell'ASIAIR
scrive "with binning" e un header vero di Voyager "after binning" <!-- software-ok: sono le
fonti -->. Moltiplicare darebbe un campo doppio su tutto un archivio a bin 2, che e' come non
darlo. Il **pixel fisico** della camera invece e' `XPIXSZ` diviso il binning
(`units.physical_pixel_um`), e un binning che l'header non dice vale "non si sa", non 1.

**L'indizio si eredita da un frame dello stesso OGGETTO**, non della stessa sessione: lo
stesso oggetto e' lo stesso pezzo di cielo anche a un anno di distanza e con un altro setup,
e l'indizio serve solo a restringere la ricerca. La sessione non basterebbe: i pezzi mancanti
valgono vuoto, quindi due frame senza `OBJECT`
ripresi la stessa notte con lo stesso setup la condividono pur guardando due punti diversi
-- ereditare li' manderebbe il solver nel posto sbagliato, e non risolverebbe mentre alla
cieca ce l'avrebbe fatta.

**Il cielo si salva anche senza il suo rettangolo.** Centro e scala sono la soluzione;
rotazione e campo servono a disegnare il riquadro, e possono mancare (matrice degenere,
header che non dice quanti pixel ha il sensore). Restano vuoti, e la soluzione si salva
lo stesso: pretenderli tutti butterebbe via un cielo misurato davvero.
