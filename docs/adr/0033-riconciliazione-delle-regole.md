# 0033 -- Riconciliazione delle regole: ogni regola una casa

**Stato:** accettata, 23/10/2026 (Marco: R1-R4). Nessun valore cambia: i documenti si allineano
all'ultima decisione gia' presa. Superata in parte da ADR 0040: revisione a tre agenti (L);
`tools/glossario.py` e riduzioni dei documenti al passo 26 del piano.

**Supera** in `docs/domini/spina.md`: "HFD e stelle costano una seconda passata"; "quando si potra', sara' un'esclusione"; "supportato e' N.I.N.A., ASIAIR, Voyager e SGP"; "i software supportati restano quattro"; "I vocabolari dicono solo cio' che i quattro software scrivono"; "il catalogo dei modelli resta come"; "XISF) quando un utente li chiede"
**Supera** in `docs/domini/notti.md`: "misura mentre risolve la posa"
**Supera** in `docs/domini/glossario.md`: "La da' il solver nella sua passata di analisi"
**Supera** in `docs/domini/ereditato.md`: "L'app misura, non marca e non scarta"; "nessuna soglia impostabile"; "SNR = mediana robusta di picco"; "Una soglia dell'aria ferma, non tre"; "distanza dalla Luna 40 gradi"; "Esclusi: jet stream come fattore"; "il seeing non cambia la parola del verdetto"; "Lingua e tema nella barra in alto, non in Impostazioni"
**Supera** in `docs/domini/meteo.md`: "Il semaforo lo fanno le nuvole"; "pesa solo nelle ore in cui e' sopra l'orizzonte"
**Supera** in `docs/domini/archivio.md`: "non e' il setup a dividerli"
**Supera** in `docs/domini/attrezzatura.md`: "Quanto cielo inquadra un setup si MISURA, non si calcola"; "che chiedono dati che oggi nessuno ha"; "cerca nel catalogo dei modelli"
**Supera** in `docs/domini/mosaico.md`: "nei quattro programmi supportati"
**Supera** in `docs/piano.md`: "header veri di Voyager e SGP"
**Supera** in `CLAUDE.md`: "piu' la convenzione SBIG come lettura comune"

## Contesto

Ricognizione del 23/10/2026 (tre esploratori) su circa 330 decisioni vive: ADR 0001-0032,
CLAUDE.md, piano, contratti, guida, piano di ASTAP (D1-D8, fin qui solo nel materiale di lavoro).
Dodici conflitti fra documenti (A-L): una regola in due case che dicono cose diverse. Chi legge
la casa vecchia (una sessione, una brief per Design) riporta indietro una decisione.

## Decisione

Vince l'ultima decisione presa. Il contratto si riscrive e cita l'ADR; un ADR vecchio non si
riscrive, porta in testa "superato in parte da ADR 0033".

### Decisioni di Marco (23/10/2026)

- **R1 Un progetto, un setup** (ADR 0013). Lo stesso oggetto con due setup fa due progetti; dentro
  un setup due progetti si distinguono dal puntamento (`domini/archivio.md`).
- **R2 Bortle da SQM: la tabella di ASTAP ovunque**: `bortle()` in `unit_sqm.pas`, da
  ClearDarkSky (Bortle 5 = 19,50-20,49, 6 = 18,94-19,50), come ADR 0022. Supera la tabella dei
  siti di astrofotografia di `domini/sito.md`; si applica nella fase di applicazione (codice,
  `sito.md` e guida insieme), non qui.
- **R3 Tilt**: fino al 10 % buono, 10-20 % incerto, oltre non adatto (hnsky.org/astap.htm;
  Siril mette il limite al 10 %). In ADR 0022 la riga "Nessuna fonte da' un metodo standard ne' <!-- software-ok -->
  una soglia: solo numeri" e' superata.
- **R4 Pipeline nuova: solo N.I.N.A. e ASIAIR**, un altro file si salta; nessuna lettura comune
  SBIG (ADR 0029, Conseguenze). La lettura SBIG resta solo nella pipeline vecchia, finche' c'e'.

### Decisioni del piano di ASTAP (Marco, 23/10/2026), qui per avere una casa

- **D1 Stelle da `measure`**: la passata `-analyse` esce (letture del file da 3 a 2); `measure`
  conta le stelle sul frame intero senza pixel caldi (copia filtrata 3×3). Anche la HFD.
- **D7 ASTAP in parallelo**: meta' dei core fisici, mai oltre un quarto della RAM (circa 160 MB a
  processo, misurati su 26 MP). Lo scrittore del database resta uno.

### I conflitti

| | vince | dove sta ora |
|---|---|---|
| A stelle, HFD | D1 | `spina.md`, `notti.md`, `glossario.md`; ADR 0007 e 0022 marcati |
| B scarto dei frame | ADR 0032: lo sceglie l'utente, reversibile | `ereditato.md`, `spina.md` (*Cosa NON fa*); ADR 0009 e 0013 marcati |
| C programmi | ADR 0029 e R4 | CLAUDE.md, `spina.md`, `mosaico.md`, `piano.md`; ADR 0019, 0021, 0026, 0029 marcati |
| D filtri | ADR 0031: lista standard, abbinamento esatto | `spina.md`, `attrezzatura.md` |
| E formati | ADR 0031 (XISF mai); `.fts`, `.fz` nella pipeline nuova | `spina.md`; ADR 0026 marcato |
| F meteo | ADR 0020 (punteggio, Luna da -5°); Luna per banda di ADR 0023 | `meteo.md`, `ereditato.md` |
| G Bortle | R2 | ADR 0022; `sito.md` nella fase di applicazione |
| H progetti | R1 | `archivio.md` |
| I attrezzatura | ADR 0021: conti del setup, scala prevista accanto alla misurata, carico | `attrezzatura.md` |
| J "posa" | `glossario.md`: posa = tempo, frame = file | resta da fare, sotto |
| K tilt | R3 | ADR 0022 marcato |

**L, minori:**

- Meteo nel piano della notte: una striscia (ADR 0013); nel Planner solo in Notti (ADR 0023,
  marcato).
- Impostazioni: nascono dove una soglia non ha una convenzione unica (ADR 0013, 0020, 0023,
  0032); "impostazioni minime" di ADR 0009 e' superata (marcato).
- Revisione: un giro (ADR 0015); per un passo del cuore della pipeline quel giro ha tre agenti
  (ADR 0030). Nessun conflitto. (superata: vedi 0040)
- SNR: la PSF SNR di ADR 0022; FWHM: fasce e limite del setup di ADR 0022 (Nyquist). In
  `ereditato.md`.
- Lingua e tema: tornano con Impostazioni (`navigazione.md`); `ereditato.md` allineato.
- Un worker, uno scrittore (`spina.md`), con ASTAP in parallelo (D7) nella pipeline nuova.
- `moon_broadband_min_dark_h` (4 h): casa `effemeridi.md` e le Impostazioni, nessun conflitto;
  `glossario.md` non dice "40 gradi".
- `spina.md` sui tentativi di ASTAP descrive le due pipeline finche' convivono: voluto.

## Conseguenze

- `tools/test_adr_superati.py` tiene fuori dai contratti le frasi superate qui sopra.
- Restano aperti: il database stellare di ASTAP (ADR 0003 non lo nomina, chiuso da ADR 0036; D05 nei test, D80 e V50
  in ADR 0022), da decidere col pacchetto; "posa" usata per frame in `spina.md`, ADR 0016 e 0030,
  che `tools/glossario.py` (ADR 0025) trovera'; il vocabolario della pipeline vecchia porta
  ancora Voyager e SGP finche' esce (ADR 0029).
- La guida segue il codice: `guida-utente.md` (scarto, filtri, meteo) cambia quando si
  costruiscono ADR 0020, 0031 e 0032; `sito.md` e la guida con R2.
- ADR sopra 100 righe e `spina.md` sopra 400: si riducono al passo 26 del piano (ADR 0040).
