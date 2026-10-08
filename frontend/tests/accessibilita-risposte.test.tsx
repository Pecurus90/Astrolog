// @vitest-environment jsdom
/**
 * La guardia di accessibilita' del **primo avvio e delle Impostazioni**: axe sulle pagine dove si
 * risponde a delle domande, non su quelle che si guardano.
 *
 * Sta in un file suo per il tetto di righe, e il taglio e' quello del mestiere: qui i campi, i
 * gruppi di scelte, i dialoghi e le schede -- il markup dove un'etichetta orfana fa piu' danno --
 * mentre in `accessibilita.test.tsx` restano le pagine che si leggono. La macchina che dimostra
 * se stessa (una violazione vera, vista rossa) vive li', una volta per tutte.
 *
 * Gli otto casi arrivano da li', **spostati e non riscritti** -- stesso titolo, stesso corpo:
 * test-tolto: "e nemmeno il primo avvio, che e la prima cosa che si vede"
 * test-tolto: "e nemmeno il passo del sito, dove c e il gruppo di scelte scritto a mano"
 * test-tolto: "e nemmeno il passo del riconoscitore, che non tutti vedono"
 * test-tolto: "e nemmeno Impostazioni, col suo dialogo aperto"
 * test-tolto: "e nemmeno Il sito, con la scheda aperta e la scala del cielo dentro"
 * test-tolto: "e nemmeno Il riconoscitore, con la proposta della ricerca aperta"
 * test-tolto: "e nemmeno Le letture, con una ricevuta per ogni esito"
 * test-tolto: "e nemmeno Il riconoscitore con ASTAP ma senza il suo catalogo"
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  LETTURA,
  SALUTE,
  SPINA,
  STANOTTE,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  violazioni,
} from "./banco"

afterEach(pulisci)

describe("l accessibilita di dove si risponde", () => {
  it("e nemmeno il primo avvio, che e la prima cosa che si vede", async () => {
    // Il primo avvio e' la **prima** superficie di chi installa l'app: se e' quella a non
    // essere accessibile, il resto non lo vede nessuno.
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 7 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    const { container } = await disegna()
    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno il passo del sito, dove c e il gruppo di scelte scritto a mano", async () => {
    // Il passo *Da dove osservi* porta l'unico `radiogroup` dell'app scritto da noi -- nove
    // bottoni con `role="radio"`, `aria-checked` e il tabindex mobile. E' il costrutto ARIA piu'
    // facile da sbagliare che abbiamo, e axe non ci era mai arrivato: le due prove di qui
    // guardano il passo 0 e il passo 3, e questo sta in mezzo.
    rispondi({
      ...STANOTTE,
      "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
      "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    const { container } = await disegna()
    await screen.findByRole("button", { name: /salta/i })
    fireEvent.click(screen.getByRole("button", { name: /avanti/i }))
    await screen.findByRole("radiogroup")

    expect(await violazioni(container)).toEqual([])

    // e anche col cielo scelto, che fa comparire l'avviso col suo titolo
    fireEvent.click(screen.getByRole("radio", { name: /^Bortle 5 -/ }))
    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno il passo del riconoscitore, che non tutti vedono", async () => {
    // Il passo del riconoscitore compare solo a chi manca il solver: e' la superficie che meno occhi
    // guardano, quindi quella che si rompe senza che nessuno lo dica.
    rispondi({
      ...STANOTTE,
      "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
      "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
      "/api/v1/settings": {
        stato: 200,
        corpo: { ...impostazioni(false), missing: ["no_solver"] },
      },
      // `/api/v1/solver` **non** si dichiara: il passo del riconoscitore non la chiede, e dichiararla qui
      // spegnerebbe proprio la guardia del banco che se ne accorgerebbe se tornasse a chiederla.
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    const { container } = await disegna()
    await screen.findByRole("button", { name: /salta/i })
    for (let i = 0; i < 4; i++) fireEvent.click(screen.getByRole("button", { name: /avanti/i }))
    await screen.findByLabelText(/percorso di astap/i)

    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno Impostazioni, col suo dialogo aperto", async () => {
    // Due superfici in una: la pagina a sezioni, e il dialogo che chiede conferma -- che e' il
    // pezzo dove l'accessibilita' si rompe piu' facilmente (un dialogo senza nome, o che non si
    // dichiara modale, axe lo prende).
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
      "/api/v1/folders": {
        stato: 200,
        corpo: {
          items: [
            {
              id: 1,
              name: "2025",
              root_path: "D:/Astro/2025",
              created_at: "2026-09-16T10:00:00Z",
              reachable: true,
              frames: 3180,
              reactivated: false,
            },
            {
              id: 2,
              name: "nas",
              root_path: "//NAS/foto",
              created_at: "2026-09-16T10:00:00Z",
              reachable: false,
              frames: 1412,
              reactivated: false,
            },
          ],
          total: 2,
          limit: 50,
          offset: 0,
        },
      },
      ...SPINA,
    })
    const { container } = await disegna()
    const barra = await screen.findByRole("navigation", { name: /pagine/i })
    fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
    await screen.findByRole("heading", { level: 2, name: /^cartelle$/i })
    expect(await violazioni(container)).toEqual([])

    fireEvent.click((await screen.findAllByRole("button", { name: /^rimuovi$/i }))[0]!)
    await screen.findByRole("dialog")
    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno Siti, con la scheda aperta e la scala del cielo dentro", async () => {
    // La scala e' un `radiogroup` scritto a mano, con una fermata sola per il tabulatore: e' il
    // pezzo che axe prende se un `role` resta spaiato o se un nome manca.
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/sites": {
        stato: 200,
        corpo: {
          items: [
            // Uno col cielo dichiarato e uno senza: la fascia "ignota" e' un ramo suo.
            {
              id: 1,
              name: "Cortina",
              latitude: 46.5405,
              longitude: 12.1357,
              bortle: 3,
              sky_sqm: 21.3,
              is_default: true,
            },
            {
              id: 2,
              name: "Passo Giau",
              latitude: 46.4843,
              longitude: 12.0533,
              bortle: null,
              sky_sqm: null,
              is_default: false,
            },
          ],
          total: 2,
        },
      },
      ...SPINA,
    })
    const { container } = await disegna()
    const barra = await screen.findByRole("navigation", { name: /pagine/i })
    fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
    fireEvent.click(await screen.findByRole("link", { name: /^siti$/i }))
    await screen.findByText(/^siti di osservazione$/i)
    expect(await violazioni(container)).toEqual([])

    fireEvent.click(await screen.findByRole("button", { name: /^modifica Cortina$/i }))
    await screen.findByRole("radiogroup")
    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno ASTAP, con la proposta della ricerca aperta", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "POST /api/v1/solver": {
        stato: 200,
        corpo: { path: "/usr/bin/astap_cli", source: "path", declared: null, databases: [] },
      },
      "/api/v1/solver": {
        stato: 200,
        corpo: { path: null, source: null, declared: null, databases: [] },
      },
      ...SPINA,
    })
    const { container } = await disegna()
    const barra = await screen.findByRole("navigation", { name: /pagine/i })
    fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
    fireEvent.click(await screen.findByRole("link", { name: /^astap$/i }))
    await screen.findByText(/^astap non trovato\./i)
    expect(await violazioni(container)).toEqual([])

    // La proposta porta dentro di se' cosa farci: e' un avviso con un'azione, ed e' la forma
    // dove un nome che manca non si vede a schermo.
    fireEvent.click(screen.getByRole("button", { name: /^cerca astap$/i }))
    await screen.findByText(/^astap trovato$/i)
    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno Scansioni, con una ricevuta per ogni esito", async () => {
    // Tre righe con tre esiti diversi: lo stato e' colore **piu'** parola, e una riga senza la
    // parola sarebbe leggibile solo da chi distingue il verde dal rosso.
    const base = {
      ...LETTURA,
      found: 120,
      new: 5,
      unchanged: 115,
      skipped: 2,
      errors: 1,
      hidden_dirs: ["cestino"],
      skipped_by_reason: [{ reason: "calibration", count: 2 }],
    }
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      // prima di `/api/v1/scan-runs`, che come prefisso la prenderebbe lei
      "/api/v1/scan-runs/3/errors": {
        stato: 200,
        corpo: {
          items: [{ file: "sub/rotto.fit", reason: "header_unreadable" }],
          total: 1,
          limit: 100,
          offset: 0,
        },
      },
      "/api/v1/scan-runs": {
        stato: 200,
        corpo: {
          items: [
            { ...base, id: 3, status: "ok" },
            { ...base, id: 2, status: "aborted", reason: "root_unreachable" },
            { ...base, id: 1, status: null, ended_at: null, duration_s: null },
          ],
          total: 3,
          limit: 20,
          offset: 0,
        },
      },
      ...SPINA,
    })
    const { container } = await disegna()
    const barra = await screen.findByRole("navigation", { name: /pagine/i })
    fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
    fireEvent.click(await screen.findByRole("link", { name: /^scansioni$/i }))
    await screen.findAllByRole("listitem")
    // e col pannello aperto: e' il bottone che dichiara cosa governa, e una regione in piu' dentro
    // una riga -- due cose che axe guarda e che chiuso non ci sono
    fireEvent.click((await screen.findAllByRole("button", { name: /^file esclusi$/i }))[0]!)
    await screen.findByText(/un FITS o header non valido/i)
    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno ASTAP, trovato ma senza il suo catalogo", async () => {
    // Un ramo diverso dal precedente: qui c'e' un avviso d'attesa con dentro un collegamento che
    // porta fuori, che e' la forma dove un `target="_blank"` senza avvertimento axe lo prende.
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/solver": {
        stato: 200,
        corpo: { path: "/usr/bin/astap_cli", source: "path", declared: null, databases: [] },
      },
      ...SPINA,
    })
    const { container } = await disegna()
    const barra = await screen.findByRole("navigation", { name: /pagine/i })
    fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
    fireEvent.click(await screen.findByRole("link", { name: /^astap$/i }))
    await screen.findByText(/^catalogo stellare mancante$/i)
    expect(await violazioni(container)).toEqual([])
  })

})
