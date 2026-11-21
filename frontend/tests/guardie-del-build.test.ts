/**
 * Le guardie del build (passo 6.17.1): una pagina che rientra per nome nel primo caricamento fa
 * rosso, invece di far crescere il peso senza che nessuno lo veda.
 */
import { describe, expect, it as prova } from "vitest"

import { guardieDelBuild, type Pezzo, pesoIniziale } from "../guardieDelBuild"

const js = (byte: number, altro: Partial<Pezzo> = {}): Pezzo => ({
  type: "chunk",
  code: "x".repeat(byte),
  isEntry: false,
  imports: [],
  facadeModuleId: null,
  ...altro,
})

const BUNDLE = {
  "index.js": js(100, { isEntry: true, imports: ["librerie.js"] }),
  "librerie.js": js(300),
  "Dashboard.js": js(60, {
    facadeModuleId: "C:\\a\\src\\Dashboard.tsx",
    imports: ["comune.js", "librerie.js"],
  }),
  "comune.js": js(5),
  // a richiesta: non conta
  "Notti.js": js(30, { facadeModuleId: "/a/src/Notti.tsx", imports: ["comune.js"] }),
  "index.css": { type: "asset" as const },
}

const contesto = {
  error: (e: string | { message: string }): never => {
    throw new Error(typeof e === "string" ? e : e.message)
  },
}

describe("peso al primo caricamento", () => {
  prova("ingresso e pagina con cio' che importano per nome, ogni file una volta", () => {
    expect(pesoIniziale(BUNDLE, "/src/Dashboard.tsx")).toBe(100 + 300 + 60 + 5)
  })

  prova("una pagina che il build non ha e' un errore, non zero", () => {
    expect(() => pesoIniziale(BUNDLE, "/src/Manca.tsx")).toThrow(/Manca/)
  })

  prova("sopra il tetto fa rosso, al tetto no", () => {
    const g = guardieDelBuild({ pagina: "/src/Dashboard.tsx", tetto: 465 })
    expect(() => g.generateBundle.call(contesto, {}, BUNDLE)).not.toThrow()
    const stretta = guardieDelBuild({ pagina: "/src/Dashboard.tsx", tetto: 464 })
    expect(() => stretta.generateBundle.call(contesto, {}, BUNDLE)).toThrow(/465 byte/)
  })
})

describe("import a richiesta che non funziona", () => {
  const g = guardieDelBuild({ pagina: "/src/Dashboard.tsx", tetto: 1 })

  prova("INEFFECTIVE_DYNAMIC_IMPORT ferma il build", () => {
    const log = {
      code: "INEFFECTIVE_DYNAMIC_IMPORT",
      message: "Notti.tsx e' importato anche per nome",
    }
    expect(() => g.onLog.call(contesto, "warn", log)).toThrow(/Notti/)
  })

  prova("gli altri avvisi passano", () => {
    expect(() =>
      g.onLog.call(contesto, "warn", { code: "EMPTY_BUNDLE", message: "x" }),
    ).not.toThrow()
  })
})
