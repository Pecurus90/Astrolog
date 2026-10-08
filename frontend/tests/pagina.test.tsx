// @vitest-environment jsdom
/**
 * La prima pagina, provata davvero nel DOM.
 *
 * Il DOM si accende **qui, per file**, e non nella configurazione: `token.test.ts` dice apposta
 * che la sua funzione si prova senza, perche' provarla con un DOM intero proverebbe il DOM.
 *
 * La regola tenuta: il componente **formatta e basta**. Il numero a schermo e' quello che l'API
 * ha mandato, non un conto rifatto qui -- ed e' cio' che rende la veste finale un cambio d'abito
 * invece di una riscrittura. Il banco sta in `banco.tsx`, che lo divide con l'accessibilita'.
 */
import { screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

describe("la prima pagina", () => {
  it("mostra il numero che l API ha mandato, non un conto suo", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 7 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    await disegna()
    expect(await within(await screen.findByRole("main")).findByText("7")).toBeDefined()
  })

  it("un errore non si inghiotte: lo dice invece di mostrare zero", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 500, corpo: { detail: { code: "rotto" } } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    await disegna()
    const avviso = await screen.findByRole("alert")
    expect(avviso.textContent).toContain("Da confermare non disponibile")
    // E soprattutto: nessun conteggio a schermo. Uno zero su un archivio che non ha risposto e'
    // una bugia tranquillizzante, ed e' il difetto che la riga dell'errore in `App.tsx` evita.
    // minuscolo: e' l'unita' accanto al numero, non il nome della pagina nel binario
    expect(document.body.textContent).not.toContain("da confermare")
  })
})
