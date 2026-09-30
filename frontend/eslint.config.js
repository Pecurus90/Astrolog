// Il linter del frontend, e SOLO cio' che serve.
//
// PERCHE' ESISTE, e perche' e' minimo. Tre macchine guardano il frontend e nessuna copre le
// altre: `vitest` prova la logica ma esegue solo cio' che un test importa; `tsc` (dentro
// `npm run build`) prende i tipi e gli identificatori inventati anche nei file che nessun test
// tocca; il linter prende cio' che resta -- gli avanzi dei refactor e le regole degli hook di
// React, che un compilatore non puo' conoscere.
//
// REGOLA DI QUESTO FILE: solo regole che prendono DIFETTI, mai stile. Niente preset "consigliati".
// Non e' minimalismo per gusto: un linter che litiga con lo stile scritto a mano viene messo a
// tacere entro un mese, e un controllo disattivato e' peggio di un controllo che non c'e' --
// perche' la sua riga nel cancello continua a promettere qualcosa.
//
// `no-undef` NON c'e', ed e' voluto: in TypeScript quel difetto lo prende il compilatore, e
// tenerlo qui vorrebbe dire la stessa regola in due case che possono divergere.

import globals from "globals"
import reactHooks from "eslint-plugin-react-hooks"
import tseslint from "typescript-eslint"

export default tseslint.config(
  // Fuori: cio' che nessuno ha scritto a mano. `schema.d.ts` lo genera l'OpenAPI, `coverage/` lo
  // riscrive ogni giro del cancello -- e git lo ignora gia', ma il linter ha il suo elenco: dirlo
  // a una macchina sola vuol dire tre avvisi a ogni giro su codice di nessuno, e un linter che
  // stampa rumore e' un linter che si smette di leggere.
  { ignores: ["node_modules/**", "coverage/**", "src/api/schema.d.ts"] },
  {
    files: ["src/**/*.{ts,tsx}"],
    extends: [tseslint.configs.base],
    languageOptions: { globals: { ...globals.browser } },
    plugins: { "react-hooks": reactHooks },
    rules: {
      // Import e variabili morti: gli avanzi dei refactor. `args: "none"` perche' un parametro
      // non usato e' spesso la firma di un contratto (un gestore, una callback di libreria):
      // segnalarlo non trova difetti, trova rumore.
      "@typescript-eslint/no-unused-vars": ["error", { args: "none", ignoreRestSiblings: true }],
      // Le regole degli hook: un hook chiamato dentro una condizione rompe React in modi che
      // non somigliano alla causa. Nessun compilatore lo vede.
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      // Same file ceiling as Python (docs/adr/0001-metodo-standard.md).
      "max-lines": ["error", { max: 1000 }],
    },
  },
  {
    // `tsx` compreso: la prova di un componente e' un `.tsx`, e senza questa forma cadrebbe
    // fuori da tutti e due i blocchi -- cioe' senza nessuna regola, in silenzio.
    files: ["tests/**/*.{ts,tsx}", "vite.config.ts", "eslint.config.js"],
    extends: [tseslint.configs.base],
    languageOptions: { globals: { ...globals.node } },
    rules: {
      "@typescript-eslint/no-unused-vars": ["error", { args: "none" }],
      "max-lines": ["error", { max: 1000 }],
    },
  },
)
