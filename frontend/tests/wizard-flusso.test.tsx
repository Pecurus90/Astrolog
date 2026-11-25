// @vitest-environment jsdom
/**
 * Il primo avvio da un passo all'altro (tavola v82 `Primo avvio`): cio' che si scrive lasciando un
 * passo, il timbro che non riesce, e la chiusura letta dal database (sito predefinito, veste, chiave,
 * cartelle e scansione). Le regole di fondo stanno in `wizard.test.tsx`.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SITO_DI_CASA,
  SPINA,
  STANOTTE,
  type Voce,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
} from "./banco"

afterEach(pulisci)

function conValori(valori: Record<string, unknown>, manca: string[] = []) {
  const base = impostazioni(false)
  return { ...base, missing: manca, values: { ...base.values, ...valori } }
}

function primoAvvio(extra: Record<string, Voce> = {}) {
  rispondi({
    ...STANOTTE,
    "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
    "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
    "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(false) },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    ...SPINA,
    ...extra,
  })
}

const avanti = () => fireEvent.click(screen.getByRole("button", { name: /avanti/i }))
const tappe = () =>
  [...document.querySelectorAll(".al-avvio__riga-1")].map((li) => li.getAttribute("aria-label"))
const righe = (carta: HTMLElement) =>
  [...carta.querySelectorAll("li.al-avvio__centro-7")].map(
    (r) =>
      `${r.querySelector(".al-avvio__testo-21")?.textContent}=${r.querySelector(".al-avvio__testo-22")?.textContent}`,
  )

async function apri() {
  await disegna()
  await screen.findByRole("button", { name: /salta/i })
}

async function finisci() {
  for (let i = 0; i < 4; i++) avanti()
  fireEvent.click(screen.getByRole("button", { name: /^fine$/i }))
  return screen.findByRole("region", { name: "Primo avvio completato" })
}

describe("il primo avvio, passo dopo passo", () => {
  it("il campo del nome dice cosa scrivere e che e' facoltativo", async () => {
    primoAvvio()
    await apri()
    const campo = screen.getByLabelText<HTMLInputElement>(/^nome$/i)
    expect(campo.getAttribute("placeholder")).toBe("Nome")
    expect(campo.getAttribute("spellcheck")).toBe("false")
    expect(screen.getByText("Facoltativo.")).toBeDefined()
  })

  it("un nome gia' salvato non si riscrive tornando indietro e avanti", async () => {
    primoAvvio()
    await apri()
    fireEvent.change(screen.getByLabelText(/^nome$/i), { target: { value: "Ada" } })
    avanti()
    await screen.findByRole("region", { name: "Sito di osservazione" })
    fireEvent.click(screen.getByRole("button", { name: /indietro/i }))
    avanti()
    await screen.findByRole("region", { name: "Sito di osservazione" })
    await new Promise((r) => setTimeout(r, 20))
    expect(scritture().filter((s) => s.metodo === "PATCH")).toHaveLength(1)
    expect(tappe()[0]).toBe("Nome utente, fatto")
  })

  it("un nome gia' nel database fa il passo fatto anche senza scriverlo", async () => {
    primoAvvio({ "/api/v1/settings": { stato: 200, corpo: conValori({ user_name: "Ada" }) } })
    await apri()
    avanti()
    await screen.findByRole("region", { name: "Sito di osservazione" })
    expect(tappe()[0]).toBe("Nome utente, fatto")
    expect(scritture().filter((s) => s.metodo === "PATCH")).toEqual([])
  })

  it("Indietro toglie l'avviso di un salvataggio non riuscito", async () => {
    primoAvvio({ "PATCH /api/v1/settings": { stato: 500, corpo: {} } })
    await apri()
    fireEvent.change(screen.getByLabelText(/^nome$/i), { target: { value: "Ada" } })
    avanti()
    expect(await screen.findByText("Salvataggio non riuscito")).toBeDefined()
    expect(tappe()[0]).toBe("Nome utente, passo attuale")
    fireEvent.change(screen.getByLabelText(/^nome$/i), { target: { value: "" } })
    avanti()
    await screen.findByRole("region", { name: "Sito di osservazione" })
    expect(screen.queryByText("Salvataggio non riuscito")).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /indietro/i }))
    expect(screen.queryByText("Salvataggio non riuscito")).toBeNull()
  })

  it("al Tema l'accento si salva subito", async () => {
    primoAvvio()
    await apri()
    avanti()
    avanti()
    await screen.findByRole("region", { name: "Tema" })
    const accenti = screen
      .getAllByRole("radio")
      .filter(
        (r) =>
          !/^(scuro|chiaro|automatico)$/i.test(r.getAttribute("aria-label") ?? r.textContent ?? ""),
      )
    fireEvent.click(accenti.at(-1)!)
    await waitFor(() =>
      expect(
        scritture().some(
          (s) =>
            s.metodo === "PATCH" &&
            "theme_accent" in ((s.corpo as { values: object }).values ?? {}),
        ),
      ).toBe(true),
    )
  })

  it("un Salta che non timbra lo dice e resta nel primo avvio; mentre timbra e' spento", async () => {
    let lascia: (v?: unknown) => void = () => {}
    primoAvvio({
      "/api/v1/settings/wizard-done": {
        stato: 500,
        corpo: {},
        attesa: new Promise((r) => (lascia = r)),
      },
    })
    await apri()
    const salta = screen.getByRole("button", { name: /salta/i })
    fireEvent.click(salta)
    await waitFor(() => expect(salta.getAttribute("aria-disabled")).toBe("true"))
    expect(screen.getByRole("button", { name: /avanti/i }).getAttribute("aria-disabled")).toBe(
      "true",
    )
    fireEvent.click(salta)
    lascia()
    expect(await screen.findByText("Salvataggio non riuscito")).toBeDefined()
    expect(chiamate().filter((u) => u.includes("/settings/wizard-done"))).toHaveLength(1)
    expect(screen.queryByText("Primo avvio completato")).toBeNull()
    expect(screen.getByRole("button", { name: /salta/i })).toBeDefined()
  })
})

describe("la chiusura legge dal database", () => {
  it("il sito predefinito e' quello segnato, non il primo dell'elenco; la veste e la chiave dal timbro", async () => {
    const altro = { ...SITO_DI_CASA, id: 2, name: "Asiago", bortle: 3, is_default: false }
    const casa = { ...SITO_DI_CASA, id: 1, name: "Vicenza", bortle: null, is_default: true }
    primoAvvio({
      "/api/v1/settings/wizard-done": {
        stato: 200,
        corpo: {
          ...impostazioni(true),
          values: { ...impostazioni(true).values, theme_mode: "chiaro", meteoblue_key: "...1234" },
        },
      },
      "/api/v1/sites": {
        stato: 200,
        corpo: { items: [altro, casa], total: 2, limit: 50, offset: 0 },
      },
    })
    await apri()
    const carta = await finisci()
    expect(righe(carta)).toEqual([
      "Nome utente=Non indicato",
      "Sito di osservazione=Vicenza",
      expect.stringMatching(/^Tema=Chiaro · /),
      "Cartelle=Nessuna",
      "Seeing=Chiave salvata",
    ])
  })

  it("senza un predefinito vale il primo sito", async () => {
    const a = { ...SITO_DI_CASA, id: 2, name: "Asiago", bortle: 3, is_default: false }
    const b = { ...SITO_DI_CASA, id: 3, name: "Bassano", bortle: 6, is_default: false }
    primoAvvio({
      "/api/v1/sites": { stato: 200, corpo: { items: [a, b], total: 2, limit: 50, offset: 0 } },
    })
    await apri()
    const carta = await finisci()
    expect(righe(carta)[1]).toBe("Sito di osservazione=Asiago · Bortle 3")
  })

  it("con delle cartelle chiede solo quante, avvia la scansione e lo dice", async () => {
    primoAvvio({
      "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 3 } },
      "POST /api/v1/scan": { stato: 202, corpo: { started: [], skipped: [] } },
    })
    await apri()
    const carta = await finisci()
    expect(righe(carta)[3]).toBe("Cartelle=3 · scansione avviata")
    expect(chiamate().some((u) => u.endsWith("/api/v1/folders?limit=1"))).toBe(true)
    expect(scritture().some((s) => s.url.endsWith("/api/v1/scan"))).toBe(true)
    expect(within(carta).queryByText(/la scansione non è partita/i)).toBeNull()
  })

  it("cartelle che non si contano: la riga tace, e nessuna scansione parte", async () => {
    primoAvvio({ "GET /api/v1/folders": { stato: 200, corpo: undefined } })
    await apri()
    const carta = await finisci()
    expect(righe(carta).map((r) => r.split("=")[0])).not.toContain("Cartelle")
    expect(scritture().some((s) => s.url.endsWith("/api/v1/scan"))).toBe(false)
  })

  it("una cartella data al passo fa la tappa fatta", async () => {
    primoAvvio({
      "GET /api/v1/folders": {
        stato: 200,
        corpo: { items: [{ id: 1, name: null, root_path: "D:/Astro", reachable: true }], total: 1 },
      },
      "POST /api/v1/scan": { stato: 202, corpo: { started: [], skipped: [] } },
    })
    await apri()
    for (let i = 0; i < 3; i++) avanti()
    await screen.findByText("D:/Astro")
    avanti()
    fireEvent.click(screen.getByRole("button", { name: /^fine$/i }))
    await screen.findByRole("region", { name: "Primo avvio completato" })
    expect(tappe()[3]).toBe("Cartelle, fatto")
  })

  it("una chiave Meteoblue gia' salvata fa il Seeing fatto", async () => {
    primoAvvio({
      "/api/v1/settings": { stato: 200, corpo: conValori({ meteoblue_key: "...1234" }) },
    })
    await apri()
    await finisci()
    expect(tappe()[4]).toBe("Seeing (Meteoblue), fatto")
  })
})

describe("le ragioni che cambiano con l'installazione", () => {
  it("su un NAS le cartelle si scelgono dall'elenco, e lo dice", async () => {
    primoAvvio({
      "GET /api/v1/folders/path-info": {
        stato: 200,
        corpo: { family: "posix", data_root: "/data" },
      },
      "/api/v1/folders/browse": { stato: 200, corpo: { path: "/data", parent: null, dirs: [] } },
    })
    await apri()
    for (let i = 0; i < 3; i++) avanti()
    await screen.findByRole("region", { name: "Cartelle" })
    expect(document.querySelector("header > .al-avvio__blocco-3")?.textContent).toBe(
      "L'app \u00e8 in un container e vede percorsi diversi da quelli del computer. Seleziona la cartella dall'elenco.",
    )
  })

  it("ASTAP senza catalogo: la ragione e la pastiglia lo dicono", async () => {
    primoAvvio({ "/api/v1/settings": { stato: 200, corpo: conValori({}, ["no_star_database"]) } })
    await apri()
    for (let i = 0; i < 5; i++) avanti()
    await screen.findByRole("region", { name: /ASTAP/ })
    expect(document.querySelector("header > .al-avvio__blocco-3")?.textContent).toBe(
      "ASTAP \u00e8 installato, ma manca il catalogo stellare. Si scarica a parte, anche dopo.",
    )
    expect(document.querySelector("h2.al-avvio__riga-4 > .al-avvio__pillola-1")?.textContent).toBe(
      "! Catalogo mancante",
    )
  })

  it("ASTAP che manca del tutto: anche senza catalogo la pastiglia dice Non trovato", async () => {
    primoAvvio({
      "/api/v1/settings": { stato: 200, corpo: conValori({}, ["no_solver", "no_star_database"]) },
    })
    await apri()
    for (let i = 0; i < 5; i++) avanti()
    await screen.findByRole("region", { name: /ASTAP/ })
    expect(document.querySelector("h2.al-avvio__riga-4 > .al-avvio__pillola-1")?.textContent).toBe(
      "! Non trovato",
    )
  })

  it("con ASTAP pronto il passo non c'e', e la pastiglia nemmeno", async () => {
    primoAvvio()
    await apri()
    for (let i = 0; i < 4; i++) avanti()
    expect(screen.getByRole("button", { name: /^fine$/i })).toBeDefined()
    expect(document.querySelector(".al-avvio__pillola-1")).toBeNull()
  })
})
