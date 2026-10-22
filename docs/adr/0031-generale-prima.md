# 0031 -- Generale prima: una lista standard, l'attrezzatura dell'utente, un abbinamento

**Stato:** accettata, 22/10/2026 (Marco). Vale per la pipeline nuova (ADR 0030).

## Contesto

Le regole per indovinare cosa scrive ogni utente crescevano senza fine: parole dei filtri in
quattro lingue, un catalogo di 38 modelli, eccezioni per marca e per programma. Nei 16.136 file
veri dell'archivio di prova non compare un nome straniero ne' un modello di marca. Tre revisori
indipendenti hanno chiesto di togliere quelle regole: ogni caso particolare e' codice da mantenere
e un errore che non si vede.

## Decisione

- **Si riconosce solo il certo.** Per ogni parte dell'attrezzatura (filtri, ottiche, e le altre
  quando arriva il loro mattone) c'e' una lista standard nostra, corta e con le fonti: per i filtri
  L, R, G, B, Hα, OIII, SII, Hβ, i duali, "nessun filtro".
- **L'attrezzatura dell'utente nasce dalle sue risposte**: niente dichiarazione all'avvio (Marco);
  in Attrezzatura si aggiunge o si corregge.
- **Abbinamento esatto**: il nome scritto nel file, senza maiuscole ne' spazi in piu', si confronta
  con la lista standard, l'attrezzatura dell'utente e i nomi gia' abbinati. Niente somiglianze,
  niente vocabolari per lingua, niente cataloghi di modelli.
- **Cio' che non combacia si chiede una volta** per nome scritto («"Ha 7nm" e' uno di questi, o un
  filtro nuovo?»); la risposta vale per sempre, anche per le scansioni future, e un filtro nuovo
  entra nell'attrezzatura dell'utente. Un dato non scritto (filtro sull'ASIAIR senza filtro impostato) si chiede per
  produzione.
- **Una regola nuova solo con casi veri**: niente regola per un caso che nei file non c'e'.
- I file XISF si ignorano del tutto (Marco).

## Conseguenze

- Escono le parole in altre lingue (decisione 6 della mappa) e il catalogo dei modelli di filtri.
- Al primo avvio un utente risponde a qualche domanda in piu'; in cambio niente abbinamenti
  sbagliati in silenzio, e il codice dei vocabolari si riduce a una lista.
- La domanda sul nome e la lista dei filtri in Attrezzatura: tavole da Claude Design.
- **Forme della lista** (Marco, 22/10/2026): il simbolo e le abbreviazioni d'uso, ognuna con la
  sua fonte (nomi di prodotto Chroma, Baader, Astronomik, Optolong) o decisa da Marco (H, O, S; "none",
  "no filter"); senza fonte (O3, S2, Hb, Lum) si chiede. Solo ASCII: un header FITS non ha α.
  Codice in `pipeline/filters.py`.
- **Camere** (Marco, 22/10/2026): `CAMERAID` non distingue niente, e' la porta USB (6 valori per
  una camera sola nell'archivio di prova). L'unione si propone a sensore identico e si conferma.
- **Eccezione: cartelle di servizio dei NAS** (Marco, 22/10/2026, terzo audit): cestini e
  istantanee senza punto ne' attributo (`#recycle`, `#snapshot`, `@Recycle`, `@Recently-Snapshot`,
  `lost+found`, `$Recycle.Bin`) si riconoscono per nome, ognuno con la fonte del produttore
  (`pipeline/walk.py`). Senza, su un NAS una posa cancellata resterebbe viva.
- **Filtro con nome standard e larghezza** (Marco, 22/10/2026): 'Ha' scritto nel file e' H-alfa
  subito, senza domanda; in Attrezzatura si potra' dargli dopo banda e larghezza (3 nm, 7 nm). Due
  H-alfa scritti entrambi 'Ha': il nome non li distingue, si chiede per produzione (parte 2).
