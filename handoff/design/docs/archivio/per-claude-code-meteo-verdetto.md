# Per Claude Code · il verdetto del meteo (20 ottobre 2026)

Decisione di Marco, da portare in `docs/domini/meteo.md` e nel backend: **il verdetto della notte non lo fanno solo le nuvole.** Torna il punteggio della notte (ADR 0020).

## Cosa cambia nel contratto

- Togliere: «Il semaforo lo fanno le nuvole»; «Le ore utili sono le ore di buio che il verdetto direbbe serene»; i test che lo fissano (`test_the_clouds_are_the_verdict_and_never_weigh` e simili).
- Al loro posto: ogni ora di buio vale da 0 a 100, somma dei pesi dei fattori: nuvole 35, seeing 30, trasparenza (aerosol, visibilita') 12, condensa 9, vento 9, jet stream 5. Ogni fattore e' pieno fino alla soglia buona e zero dalla non adatta. Pioggia e nuvole dal 50 % portano l'ora a zero. La Luna non entra (v13: decide cosa si riprende, non se si esce).
- Verdetto: media della qualita' nelle ore di buio; buona da 70, incerta da 40, sotto non adatta.
- Ore utili: le ore di buio con qualita' da 60, dette come intervallo e conto («dalle 21 alle 06, 9 ore»), mai in minuti.
- La pagina riceve la qualita' ora per ora e cosa limita ogni ora (il fattore che perde piu' punti): li disegna la curva e li dice il racconto della notte.

## Cosa resta del contratto, gia' nel disegno

Gli altri fattori in ordine d'importanza con «Altri N fattori», le carte in ordine fisso, medie e picchi, arrotondamenti dal lato della soglia, la Luna (25 % · 50 % · sopra −5°) con la sua riga, tre notti piene e poi tendenza, l'accordo dei modelli, il vento a 700 hPa accanto al solito del sito, gli stati di servizio e chiave.

## Domande

1. I pesi sono quelli della v13 del disegno: li tieni o li rivedi con Marco?
2. «Accanto al semaforo pesa solo cio' che e' incerto o niente»: con la qualita' resta la riga «limita il seeing» del racconto; serve anche altrove?

Pagine: `pagine/Meteo.dc.html`, `Dashboard.dc.html`, `Notti.dc.html`, `componenti/Riepilogo`; regole in `componenti/soglie.js` (`ora`, `livello`, `utile`).


## Chiuso (20 ottobre 2026, brief v30)

Claude Code: i pesi della v13 si tengono (ADR 0020); `docs/domini/meteo.md` aggiornato. «Cosa limita» anche in Dashboard; testi del racconto e pillola «banda stretta» in giallo approvati da Marco. Fatto nella v30.
