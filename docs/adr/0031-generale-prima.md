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
