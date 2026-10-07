/**
 * La **pastiglia di un filtro** e il vocabolario che le da' il colore.
 *
 * Una mappa scritta a mano che traduce un dominio chiuso e' la cosa che invecchia in silenzio: il
 * giorno che il vocabolario impara una banda nuova, la pastiglia prenderebbe il colore di "non si
 * sa" e nessuno se ne accorgerebbe -- il colore sbagliato non rompe niente. Quindi la copertura si
 * legge dal **vocabolario vero**, come la prova dei tipi di oggetto legge il catalogo vero.
 */
import { readFileSync } from "node:fs"
import { resolve } from "node:path"

import { describe, expect, it } from "vitest"

import { VARIANTE } from "../src/FiltriUsati"

/** Le bande che il backend puo' scrivere in `passband`, dal file che le elenca. Da `frontend/`,
 *  dove vitest gira: sotto jsdom `import.meta.url` e' un indirizzo web e non porta al repo. */
function bandeDelVocabolario(): string[] {
  const file = resolve(process.cwd(), "..", "backend", "astrolog", "vocab", "filters.json")
  const dati = JSON.parse(readFileSync(file, "utf-8")) as { passbands: string[] }
  return dati.passbands
}

/** Le varianti che il **foglio** disegna davvero. Il foglio e' la consegna di Design e si porta
 *  alla lettera: una classe che li' non c'e' non si applica, e la pastiglia resta del grigio di
 *  "non si sa" senza che niente cada. */
function variantiDelFoglio(): Set<string> {
  const file = resolve(process.cwd(), "src", "stili", "astrolog.css")
  const testo = readFileSync(file, "utf-8")
  return new Set([...testo.matchAll(/\.(as-filtro--[a-z0-9-]+)/g)].map((m) => m[1] as string))
}

/** Le classi che il codice scrive e il foglio v27 non ha ancora, dichiarate una per una in
 *  `tools/classi_in_attesa.txt` (ADR 0018): le pastiglie tornano col disegno dell'Archivio. */
function classiInAttesa(): Set<string> {
  const file = resolve(process.cwd(), "..", "tools", "classi_in_attesa.txt")
  const righe = readFileSync(file, "utf-8").split("\n")
  return new Set(righe.map((r) => r.trim()).filter((r) => r && !r.startsWith("#")))
}

describe("la pastiglia di un filtro", () => {
  it("conosce ogni banda che il vocabolario produce", () => {
    const bande = bandeDelVocabolario()
    expect(bande.length).toBeGreaterThan(0)

    const senza = bande.filter((b) => !(b in VARIANTE))

    expect(senza, `bande senza un colore: ${senza.join(", ")}`).toEqual([])
  })

  it("non conosce bande che il vocabolario non produce", () => {
    // L'altro verso: una voce rimasta dopo che il vocabolario l'ha tolta e' codice morto che
    // sembra vivo, e il prossimo che legge la mappa crede che quella banda esista ancora.
    const bande = new Set(bandeDelVocabolario())

    expect(Object.keys(VARIANTE).filter((b) => !bande.has(b))).toEqual([])
  })

  it("ogni colore che promette esiste nel foglio", () => {
    // L'altra meta', e la piu' insidiosa: una classe **inventata** non rompe niente -- non si
    // applica, e la pastiglia resta grigia. Senza questa riga la prova misurava solo che una banda
    // avesse *una* chiave, non che quella chiave dipingesse qualcosa.
    // Una classe assente dal foglio passa solo se e' dichiarata in attesa del disegno.
    const nelFoglio = variantiDelFoglio()
    const inAttesa = classiInAttesa()
    expect(nelFoglio.size + inAttesa.size).toBeGreaterThan(0)

    const inventate = [...new Set(Object.values(VARIANTE))].filter(
      (c) => !nelFoglio.has(c) && !inAttesa.has(c),
    )

    expect(inventate, `classi che il foglio non ha: ${inventate.join(", ")}`).toEqual([])
  })

  it("ogni banda ha il SUO colore, non quello di una vicina", () => {
    // Il foglio ne disegna una per banda, coi suoi colori. Accorpare due bande -- le tre `OSC*`,
    // le due `DUO_*` -- vuol dire dare a un filtro il colore di un altro, e chi riprende in banda
    // stretta con un duo-band si ritroverebbe due pastiglie identiche per due filtri diversi.
    const colori = Object.values(VARIANTE)

    expect(new Set(colori).size).toBe(colori.length)
  })
})
