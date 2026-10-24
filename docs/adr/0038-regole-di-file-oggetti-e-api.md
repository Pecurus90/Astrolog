# 0038 -- Le regole di file, oggetti e API con le fonti, e l'oggetto annidato che si chiede

**Stato:** accettata, 24/10/2026 (Marco: l'oggetto annidato si chiede). Ultimi tre gruppi della
fase 2 del registro (ADR 0033). Nessun valore cambia ora, salvo dove scritto "fase 4". In vigore;
da costruire le due voci "fase 4" (oggetto annidato, ricerca del luogo a 10 s).

## Contesto

Gruppi scansione e file, oggetti e mosaici, valori tecnici dell'API. Fonti lette: FITS 4.0,
Microsoft (attributi dei file, MAX_PATH), Apple TN3150 e xnu, SQLite, RFC 9110 e 6585, NIST SP
811, POSIX `sys/stat.h`, Nielsen 1993. L'oggetto principale non ha convenzione (nessun software
sceglie un soggetto): misurato su 8.814 frame dell'archivio di Marco (cache delle soluzioni,
nessun ASTAP lanciato), riferimento il nome scritto dall'utente; validazione a oggetto escluso.

## Decisione

- **File e header**: blocco 2880, scheda 80, END, BITPIX e NAXIS fino a 999 dalla norma FITS 4.0;
  attributi dei file solo online da Microsoft e Apple; zero assoluto da NIST; interi da SQLite;
  permessi 0600 da POSIX; codici HTTP da RFC 9110 e 6585. Il resto (lotti, tetti di memoria,
  valori di default degli elenchi) e' tecnico.
- **Decisioni gia' prese, qui con la loro casa**: impronta di 64 KB e file "fresco" sotto 30 s
  (`spina.md`); campioni di 5 file (ADR 0017); stima del tempo che tace il primo minuto
  (`navigazione.md`); peso minimo del pannello 25% (`mosaico.md`); ricevute coi primi 100 percorsi
  e le 100 chiavi sconosciute piu' frequenti (Marco, quinto audit della scansione).
- **Oggetto principale**: i pesi del punteggio restano. Misura: base 59 notti su 100; la
  combinazione migliore (76) scende sotto la base a oggetto escluso: si adattava all'archivio,
  non al cielo (CLAUDE.md: l'archivio verifica, non decide).
- **Oggetto annidato** (Marco): quando il secondo candidato sta dentro il primo, o lo contiene, e
  il suo punteggio e' almeno 0,9 volte il primo, l'app chiede una volta quale e' il soggetto; la
  risposta vale per l'oggetto. Oggi sceglie in silenzio: 37 dei 41 disaccordi erano annidati.
  0,9 e' misurato (disaccordi muti da 37 a 15, falsi allarmi da 13 a 14): una domanda costa poco,
  un nome sbagliato in silenzio no. Fase 4.
- **Mosaici**: stesso pannello sotto un quarto della mezza diagonale, confermato: pannelli
  dichiarati da N.I.N.A. separati 54/54 (minimo 0,877), stesso pannello unito 12/12 (massimo
  0,016), dithering p95 0,029.
- **Attesa della rete**: la ricerca del luogo aspetta al massimo 10 s (Nielsen 1993: "about the
  limit for keeping the user's attention"); i giri in sottofondo tengono 15 s. Fase 4.

## Conseguenze

- Leggere il nome del file ASIAIR (ADR 0026) toglierebbe 12 notti dal "solo cielo".
- Una magnitudine mancante vale 0 nel punteggio e penalizza gli oggetti senza (C 14 contro NGC
  869): da rivedere con l'identificazione nella pipeline nuova.
