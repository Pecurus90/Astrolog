import { pallinoDi } from "./MisureDati"

/** A slice of a filter ring as the API sends it: where it starts and ends, in percent. */
export interface Fetta {
  ring_from: number
  ring_to: number
  passband: string
}

// a gradient is not a colour inside conic-gradient: the colour stripes become three slices
const A_COLORI = ["var(--filtro-r)", "var(--filtro-g)", "var(--filtro-b)"]

/** I colori del pezzo d'anello: senza filtro un grigio (nel pallino e' un filo), a colori R, G, B. */
export function tinte(banda: string): string[] {
  const p = pallinoDi(banda)
  if (p.border) return ["var(--ignoto-tratteggio)"]
  return p.background === "var(--filtro-a-colori)" ? A_COLORI : [p.background]
}

/** L'anello dei filtri (Dashboard `filterRing`, Attrezzatura `anello`): i pezzi dall'API,
 *  separati da un filo di carta largo `filo` percento. */
export function anello(fette: readonly Fetta[], filo: number): string {
  const pezzi = fette.map((f) => {
    const fine = Math.max(f.ring_from, f.ring_to - filo)
    const colori = tinte(f.passband)
    const passo = (fine - f.ring_from) / colori.length
    const strisce = colori.map((c, i) => {
      const da = f.ring_from + i * passo
      return `${c} ${da}% ${i === colori.length - 1 ? fine : da + passo}%`
    })
    return `${strisce.join(", ")}, var(--carta) ${fine}% ${f.ring_to}%`
  })
  return `conic-gradient(${pezzi.join(", ")})`
}
