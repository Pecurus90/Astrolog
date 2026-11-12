// @vitest-environment jsdom
/**
 * La navigazione: la barra in alto, e le pagine come **indirizzi**.
 *
 * Fin qui l'app era una pagina sola e il primo avvio un cancelletto, non un indirizzo -- per
 * questo il router non serviva. Con la seconda pagina serve, e la ragione non e' l'eleganza: un
 * indirizzo e' cio' che fa funzionare il **tasto indietro** e un collegamento che si manda a
 * qualcuno. Sul NAS l'app si apre da tablet e da telefono, dove il gesto indietro **e'** la
 * navigazione: senza, si esce dall'app.
 *
 * Il cancelletto resta **davanti** a tutto: senza il timbro non c'e' niente da navigare, e una
 * barra laterale al primo avvio inviterebbe a girare per un'app che non sa ancora da dove osservi.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { CASA, SALUTE, SPINA, STANOTTE, cartellaSenzaTipo, daConfermare, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

/** La pagina Da confermare con una domanda sola: abbastanza per aprirla davvero. */
const REVISIONE = daConfermare({
  to_confirm: 7,
  sections: [{ key: "typeless", count: 7 }],
  typeless: [cartellaSenzaTipo({ key: "D:/Astro/dark", frames: 7 })],
})

/** L'app gia' configurata: il timbro c'e', quindi si naviga. */
function configurata() {
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: REVISIONE },
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...CASA,
    ...SPINA,
  })
}

describe("la navigazione", () => {
  it("la barra c e, e la casa resta il contatore", async () => {
    configurata()
    await disegna()
    expect(await screen.findByRole("navigation", { name: "Navigazione principale" })).toBeDefined()
    // La home non cambia mestiere: dice quante cose ci sono da confermare.
    expect(await within(await screen.findByRole("main")).findByText("Da confermare, 7")).toBeDefined()
  })

  it("dalla barra si arriva a Da confermare, e l indirizzo cambia", async () => {
    // L'indirizzo e' il punto: senza, il tasto indietro del telefono esce dall'app invece di
    // tornare alla home, e un collegamento a questa pagina non si puo' mandare a nessuno.
    configurata()
    // jsdom does not scroll: the spy says which section the page brought into view
    const portate: string[] = []
    Element.prototype.scrollIntoView = function (this: Element) {
      portate.push(this.id)
    }
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: "Da confermare, 7" }))
    fireEvent.click(await screen.findByRole("link", { name: "Rispondi: Frame senza tipo" }))
    await screen.findByRole("region", { name: /frame senza tipo/i })
    expect(window.location.pathname).toBe("/da-confermare")
    expect(window.location.hash).toBe("#frame-senza-tipo")
    // Rispondi lands on its section, not at the top of the page
    await waitFor(() => expect(portate).toContain("frame-senza-tipo"))
    delete (Element.prototype as Partial<Element>).scrollIntoView
    // sulla sua pagina la pillola non c'e': non avrebbe niente da aprire
    expect(screen.queryByRole("link", { name: "Da confermare, 7" })).toBeNull()
  })

  it("senza il timbro non c e nessuna barra: il primo avvio viene prima", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    expect(screen.queryByRole("navigation", { name: "Navigazione principale" })).toBeNull()
  })
})

describe("un indirizzo che non esiste", () => {
  it("lo dice, e porta alla Dashboard", async () => {
    // un indirizzo scritto a mano, o tenuto nei preferiti da una pagina che non c'e' piu'
    window.history.pushState({}, "", "/non-esiste")
    configurata()
    await disegna()
    expect(await within(await screen.findByRole("main")).findByText(/^pagina non trovata$/i)).toBeDefined()
    fireEvent.click(screen.getByRole("link", { name: /torna alla dashboard/i }))
    expect(window.location.pathname).toBe("/")
  })
})
