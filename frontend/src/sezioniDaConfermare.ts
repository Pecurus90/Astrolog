import type { Chiave } from "./i18n"

/**
 * Le sezioni di *Da confermare*, nell'ordine della pagina: come si chiamano e a che ancora
 * rispondono. Le leggono l'indice e la sezione stessa, cosi' il nome e l'ancora hanno una casa.
 */
export const SEZIONI = {
  lookalikes: { ancora: "strumenti-duplicati", titolo: "review.lookalikes" },
  filters: { ancora: "filtri", titolo: "review.filters" },
  objects: { ancora: "oggetti", titolo: "review.objects" },
  typeless: { ancora: "frame-senza-tipo", titolo: "review.typeless" },
  unclear: { ancora: "frame-senza-sito", titolo: "review.unclear" },
  mosaics: { ancora: "mosaici-proposti", titolo: "review.mosaics" },
} as const satisfies Record<string, { ancora: string; titolo: Chiave }>

export type QualeSezione = keyof typeof SEZIONI
