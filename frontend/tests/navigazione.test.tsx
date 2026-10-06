// @vitest-environment jsdom
/**
 * La navigazione: la barra laterale, e le pagine come **indirizzi**.
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
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

/** L'app gia' configurata: il timbro c'e', quindi si naviga. */
function configurata() {
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 7 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  })
}

describe("la navigazione", () => {
  it("la barra c e, e la casa resta il contatore", async () => {
    configurata()
    await disegna()
    expect(await screen.findByRole("navigation")).toBeDefined()
    // La home non cambia mestiere: dice quante cose ci sono da confermare.
    expect(await within(await screen.findByRole("main")).findByText("7")).toBeDefined()
  })

  it("dalla barra si arriva a Da confermare, e l indirizzo cambia", async () => {
    // L'indirizzo e' il punto: senza, il tasto indietro del telefono esce dall'app invece di
    // tornare alla home, e un collegamento a questa pagina non si puo' mandare a nessuno.
    configurata()
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    expect(await screen.findByRole("heading", { name: /da confermare/i })).toBeDefined()
    expect(window.location.pathname).not.toBe("/")
  })

  it("senza il timbro non c e nessuna barra: il primo avvio viene prima", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    expect(screen.queryByRole("navigation")).toBeNull()
  })
})

describe("un indirizzo che non esiste", () => {
  it("lo dice, e porta a Casa", async () => {
    // un indirizzo scritto a mano, o tenuto nei preferiti da una pagina che non c'e' piu'
    window.history.pushState({}, "", "/non-esiste")
    configurata()
    await disegna()
    expect(await screen.findByRole("heading", { name: /questa pagina non c'e'/i })).toBeDefined()
    fireEvent.click(screen.getByRole("link", { name: /torna a casa/i }))
    expect(window.location.pathname).toBe("/")
  })
})
