/**
 * Le guardie del build sul JS a richiesta (passo 6.17.1): una pagina importata per nome da
 * un'altra rientra nel primo caricamento senza dirlo, e il peso torna su a poco a poco.
 *
 * - **INEFFECTIVE_DYNAMIC_IMPORT fa rosso**: Rolldown lo dice quando un modulo chiesto a
 *   richiesta e' importato anche per nome, quindi resta dove sta. Un avviso si perde, un errore no.
 * - **Un tetto sul JS al primo caricamento di una pagina**: l'ingresso, la pagina e cio' che
 *   importano per nome; cio' che arriva a richiesta non conta.
 */

/** A chunk as the bundle gives it: only the fields the weight reads. */
export interface Pezzo {
  type: "chunk"
  code: string
  isEntry: boolean
  imports: readonly string[]
  facadeModuleId: string | null
}

type Bundle = Record<string, Pezzo | { type: "asset" }>

const pezzo = (bundle: Bundle, nome: string): Pezzo | undefined => {
  const p = bundle[nome]
  return p?.type === "chunk" ? p : undefined
}

/** Bytes of JS fetched before `pagina` (a source path's tail, `/src/Dashboard.tsx`) draws:
 *  entry and page, with what they import by name, each file once. */
export function pesoIniziale(bundle: Bundle, pagina: string): number {
  const nomi = Object.keys(bundle)
  const radici = nomi.filter((n) => {
    const p = pezzo(bundle, n)
    return (
      p !== undefined &&
      (p.isEntry || (p.facadeModuleId ?? "").replaceAll("\\", "/").endsWith(pagina))
    )
  })
  if (!radici.some((n) => !pezzo(bundle, n)?.isEntry))
    throw new Error(`nessun file del build per ${pagina}: la guardia non misura nulla`)
  const visti = new Set<string>()
  const coda = [...radici]
  let byte = 0
  for (let n = coda.pop(); n !== undefined; n = coda.pop()) {
    const p = pezzo(bundle, n)
    if (visti.has(n) || p === undefined) continue
    visti.add(n)
    byte += Buffer.byteLength(p.code)
    coda.push(...p.imports)
  }
  return byte
}

/** The plugin's two hooks, with the context they use: Rolldown's `this.error` stops the build. */
interface Contesto {
  error: (e: string | { code?: string; message: string }) => never
}

export function guardieDelBuild({ pagina, tetto }: { pagina: string; tetto: number }) {
  return {
    name: "astrolog-guardie-del-build",
    apply: "build" as const,
    onLog(this: Contesto, _livello: string, log: { code?: string; message: string }) {
      if (log.code === "INEFFECTIVE_DYNAMIC_IMPORT") this.error(log)
    },
    generateBundle(this: Contesto, _opzioni: unknown, bundle: Bundle) {
      const byte = pesoIniziale(bundle, pagina)
      if (byte > tetto)
        this.error(
          `${pagina}: ${byte} byte di JS al primo caricamento, sopra il tetto di ${tetto} ` +
            "(frontend/vite.config.ts): cosa e' entrato per nome invece che a richiesta?",
        )
    },
  }
}
