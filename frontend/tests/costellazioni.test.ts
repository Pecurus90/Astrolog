/**
 * Le costellazioni si scrivono col nome latino ufficiale, uguale in ogni lingua (Marco, 27/9/2026).
 * La tabella si prova contro il catalogo **vero** che l'app porta: ogni sigla che un oggetto puo'
 * avere deve avere il suo nome, o a schermo tornerebbe la sigla senza che niente cada.
 */
import { readFileSync, readdirSync } from "node:fs"
import { resolve } from "node:path"

import { describe, expect, it } from "vitest"

import { COSTELLAZIONI, costellazione } from "../src/costellazioni"

/** Le sigle che il catalogo impacchettato porta, dal file stesso. */
function sigleDelCatalogo(): string[] {
  const cartella = resolve(process.cwd(), "..", "backend", "astrolog", "catalog", "data")
  const file = readdirSync(cartella).find((f) => /^catalogo-.*\.json$/.test(f))
  if (!file) throw new Error("catalogo impacchettato non trovato")
  const dati = JSON.parse(readFileSync(resolve(cartella, file), "utf-8")) as {
    objects: { constellation?: string | null }[]
  }
  const voci = dati.objects
  return [...new Set(voci.map((v) => v.constellation).filter((c): c is string => !!c))]
}

describe("le costellazioni", () => {
  it("ogni sigla del catalogo ha il suo nome", () => {
    const sigle = sigleDelCatalogo()
    expect(sigle.length).toBeGreaterThan(80)
    expect(sigle.filter((s) => !(s in COSTELLAZIONI))).toEqual([])
  })

  it("il nome e' quello latino ufficiale, anche con la dieresi", () => {
    expect(costellazione("Cyg")).toBe("Cygnus")
    expect(costellazione("CVn")).toBe("Canes Venatici")
    expect(costellazione("Boo")).toBe("Bo\u00f6tes")
    expect(costellazione("Se1")).toBe("Serpens Caput")
    expect(costellazione("Se2")).toBe("Serpens Cauda")
  })

  it("una sigla che non conosce resta la sigla, invece di sparire", () => {
    expect(costellazione("Xyz")).toBe("Xyz")
  })
})
