# frontend -- perche' queste versioni, e non le ultime

Le dipendenze sono **fissate**, e due non sono le piu' recenti. Le ragioni sono misurate
(13/9/2026), non prudenziali, e vanno rilette prima di alzarle:

* **`typescript` 5.9.3 e non 7.0.2.** `typescript-eslint` dichiara di funzionare con TypeScript
  `>=4.8.4 <6.1.0`: con la 7 il linter parte su una versione non supportata, e quel genere di
  rottura si manifesta con messaggi che parlano d'altro. Si alza quando `typescript-eslint`
  allarga l'intervallo, non prima.
* **`vitest` 4.1.11 e non 5.0.0.** La 5 chiede Node `^22.12 || ^24 || >=26`; la CI installa
  **Node 20** (`.github/workflows/ci.yml`) e `CONTRIBUTING.md` dichiara Node 20. Con la 5 la
  suite girerebbe sulla macchina di chi sviluppa e cadrebbe in CI -- il difetto peggiore, perche'
  lo vede solo chi non l'ha scritto. Si alza **insieme** a Node, che e' una decisione sui tre
  bersagli (Windows, Mac, NAS in Docker), non una scelta di libreria.

Un margine da sapere: `vite`, `eslint` e `@vitejs/plugin-react` chiedono Node **20.19** o
superiore. La CI usa `node-version: "20"`, cioe' l'ultima 20.x, e oggi tiene; il giorno che
qualcuno fissa un 20 piu' vecchio, quelle tre si fermano.

## I comandi, e chi li chiama

`test` e `build` **non sono liberi**: pre-commit e la CI li lanciano per nome, e rinominarli
spegne due controlli senza che nessuno se ne accorga. eslint lo lanciano direttamente.

* `npm run dev` -- il server di sviluppo, con le chiamate `/api` girate al backend su 8765. La
  chiave di avvio arriva dalla variabile `ASTROLOG_TOKEN`, che imposta `tools/dev.py` per tutti e
  due i processi: senza, la pagina servita da Vite non porta il `<meta>` con la chiave e ogni
  chiamata prende 401. Lanciare `npm run dev` da solo, senza quel comando, e' proprio quel caso.
* `npm run build` -- prima `tsc` (i tipi, anche nei file che nessun test importa), poi il build
  vero, che finisce in `backend/astrolog/web/`: **dentro il pacchetto Python**, perche' sia il
  backend a servire la pagina anche dopo un'installazione.
