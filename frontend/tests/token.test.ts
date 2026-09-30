import { describe, expect, it } from "vitest"

import { tokenFromPage } from "../src/api/token"

/** Una pagina finta: solo cio' che `tokenFromPage` guarda davvero. Senza finto browser -- la
 *  funzione e' pura, e provarla con un DOM intero proverebbe il DOM. */
function pagina(contenuto: string | null) {
  return {
    querySelector: () =>
      contenuto === null ? null : ({ getAttribute: () => contenuto } as unknown as Element),
  } as Pick<Document, "querySelector">
}

describe("la chiave di avvio nella pagina", () => {
  it("la legge dal meta che il backend ha messo dentro", () => {
    expect(tokenFromPage(pagina("gettone-di-prova"))).toBe("gettone-di-prova")
  })

  it("senza meta non inventa niente: sul NAS la chiave non serve", () => {
    // `null` e non stringa vuota: chi chiama deve poter decidere di NON mandare
    // l'intestazione, invece di mandarne una vuota che il backend rifiuterebbe.
    expect(tokenFromPage(pagina(null))).toBeNull()
  })

  it("un meta vuoto vale come nessuna chiave", () => {
    // E' il caso del NAS servito da un backend senza chiave: il segnaposto c'e' ma non porta
    // niente. Darlo per buono vorrebbe dire mandare un'intestazione vuota a ogni richiesta.
    expect(tokenFromPage(pagina(""))).toBeNull()
  })
})
