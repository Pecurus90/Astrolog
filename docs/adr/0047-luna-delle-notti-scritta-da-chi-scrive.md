# 0047 -- La Luna delle notti scritta da chi scrive, con la versione della formula

**Stato:** accettata, 20/11/2026 (Marco, passo 6.16: "dati derivati materializzati con la versione
della formula"). Supera l'eccezione di `docs/domini/notti.md` del 23/9/2026, "la Luna di una notte
passata si calcola, non si conserva".

## Contesto

Notti calcolava a ogni GET la fase della Luna a mezzanotte e il buio senza Luna di ogni notte della
pagina (`spine/nights.py`, `_moons` e `_shooting`): ~7 ms a notte. Sull'archivio sintetico da
10.000 frame del budget (passo 6.15), 500 notti costavano 1,6 s sul portatile, di piu' su un NAS.
L'eccezione reggeva sull'argomento che una colonna derivata sopravvive a una formula corretta: la
versione della formula nella riga toglie quel rischio.

## Decisione

- **Tabella `night_moons`, una riga per notte dell'archivio (derivata).** Porta fase e
  illuminazione a mezzanotte nel fuso del sito, buio astronomico e buio con la Luna sotto la soglia
  d'altezza della regola, e con cosa e' stata calcolata: formula, data, coordinate e fuso del sito,
  soglia. Distinta da `moon_nights`, il calendario del sito predefinito, che prende la Luna a meta'
  della finestra: due istanti diversi, due fatti.
- **`night_moons.refresh` riscrive solo le righe vecchie**: mancanti, o con un'altra formula, data,
  posizione, fuso o soglia. Senza righe vecchie costa una query.
- **Chi la chiama:** la fine di `group` (le notti appena fatte), la porta del cielo che segue
  (`sky_follows`: siti, coordinate, backup e, nuovo, la regola della Luna) dal thread di Behind,
  e l'avvio dell'app (una formula alzata riscrive tutto, una volta). Behind riceve la funzione da
  chi lo crea: la pipeline nuova non importa la spina (import-linter).
- **Notti legge e non calcola.** Resta in lettura solo il confronto con la soglia "buona" della
  regola, che non chiede il cielo, e il lato illuminato, una tabella.

## Conseguenze

- 500 notti da 1617 a 80 ms sullo stesso archivio, risposte identiche campo per campo (500 notti
  con Luna e ripresa, le tre ripresa presenti). La rotta da 500 notti entra nel budget.
- Dopo un cambio della regola o di un sito, finche' Behind non ha finito Notti mostra le righe di
  prima: secondi, mai una Luna di un'altra notte.
- Chi cambia il calcolo della Luna o del buio alza `VERSION` in `spine/night_moons.py`.
