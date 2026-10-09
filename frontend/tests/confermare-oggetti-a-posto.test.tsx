// @vitest-environment jsdom
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

/**
 * Gli **oggetti gia' a posto** di *Da confermare*: quelli che l'app riconosce da sola. Non sono
 * domande: stanno chiusi in fondo alla sezione Oggetti, si aprono a pagine, e da li' si correggono
 * con la stessa scheda di un oggetto in dubbio.
 */

const aPosto = (n: number) => ({
  key: `object:m-${n}`,
  name: `M ${n}`,
  slug: `m-${n}`,
  method: "coords",
  confidence: "high",
  group: null,
  frames: 100 + n,
  integration_s: 3600,
  untimed: 0,
  candidates: [],
  answer: null,
})
const TUTTI = Array.from({ length: 45 }, (_, i) => aPosto(i + 1))
const pagina = (offset: number) => ({ items: TUTTI.slice(offset, offset + 20), total: 45, limit: 20, offset })

const DUBBIO = {
  ...aPosto(0),
  key: "object:ngc-7000",
  name: "NGC 7000",
  slug: "ngc-7000",
  confidence: "low",
  candidates: [{ slug: "ic-5070", name: "IC 5070", common_name: null, in_frame: true }],
}

const PAGINA = {
  to_confirm: 1,
  lookalikes: [],
  filters: [],
  filter_choices: [],
  gear: [],
  rig_choices: [],
  optics_choices: [],
  objects: [DUBBIO],
  settled_objects: 45,
  typeless: [],
  unclear: [],
  mosaics: [],
}

function aperta(principale: unknown = PAGINA, prima: unknown = pagina(0)) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 101, run_started: true } },
    "/api/v1/review/objects/settled?limit=20&offset=20": { stato: 200, corpo: pagina(20) },
    "/api/v1/review/objects/settled?limit=20&offset=40": { stato: 200, corpo: pagina(40) },
    "/api/v1/review/objects/settled": { stato: 200, corpo: prima },
    "/api/v1/review": { stato: 200, corpo: principale },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

async function mandati() {
  fireEvent.click(screen.getByRole("button", { name: /applica/i }))
  let corpo: { objects: unknown[] } | undefined
  await waitFor(() => {
    corpo = scritture().find((s) => s.url.includes("/api/v1/review/apply"))?.corpo as typeof corpo
    expect(corpo).toBeDefined()
  })
  return corpo?.objects
}

const piede = (dove: HTMLElement) => dove.querySelector<HTMLElement>(".as-conferma-aposto") as HTMLElement
const nomi = (dove: HTMLElement) =>
  [...dove.querySelectorAll(".as-conferma-aposto ~ .as-domanda-riga .as-domanda-riga__nome")].map((n) => n.textContent)
const dove = (sezione: HTMLElement) => sezione.querySelector(".as-conferma-pagine__dove")?.textContent

async function aperti() {
  const sezione = await vaiASezione(/^oggetti$/i)
  fireEvent.click(within(piede(sezione)).getByRole("button", { name: "Apri" }))
  await within(sezione).findByRole("button", { name: "Correggi: M 1" })
  return sezione
}

describe("Da confermare -- gli oggetti gia' a posto", () => {
  it("chiusi sono un numero e un gesto, e non disegnano righe", async () => {
    aperta()
    const sezione = await vaiASezione(/^oggetti$/i)
    expect(piede(sezione).querySelector("p")?.textContent).toBe("45 oggetti riconosciuti")
    expect(piede(sezione).classList.contains("as-conferma-aposto--aperto")).toBe(false)
    expect(nomi(sezione)).toEqual([])
    expect(sezione.querySelector(".as-conferma-pagine")).toBeNull()
  })

  it("aperti sono righe senza stato, col gesto Correggi, venti per pagina", async () => {
    aperta()
    const sezione = await aperti()
    expect(piede(sezione).classList.contains("as-conferma-aposto--aperto")).toBe(true)
    expect(nomi(sezione)).toEqual(TUTTI.slice(0, 20).map((o) => o.name))
    const prima = sezione.querySelector<HTMLElement>(".as-conferma-aposto ~ .as-domanda-riga") as HTMLElement
    // non e' una domanda: niente stato, e il gesto dice di quale riga
    expect(prima.querySelector(".as-risposta")).toBeNull()
    expect(prima.querySelector(".as-domanda-riga__breve")?.textContent).toBe("")
    expect(within(prima).getByRole("button").getAttribute("aria-label")).toBe("Correggi: M 1")
    expect(dove(sezione)).toBe("1\u201320 di 45")
  })

  it("le pagine vanno avanti e indietro, e si fermano ai due capi", async () => {
    aperta()
    const sezione = await aperti()
    const prec = within(sezione).getByRole("button", { name: "Precedenti" })
    const succ = within(sezione).getByRole("button", { name: "Successivi" })
    expect(prec).toHaveProperty("disabled", true)
    fireEvent.click(succ)
    await within(sezione).findByRole("button", { name: "Correggi: M 21" })
    expect(dove(sezione)).toBe("21\u201340 di 45")
    fireEvent.click(succ)
    await within(sezione).findByRole("button", { name: "Correggi: M 45" })
    expect(dove(sezione)).toBe("41\u201345 di 45")
    expect(nomi(sezione)).toHaveLength(5)
    expect(succ).toHaveProperty("disabled", true)
    fireEvent.click(prec)
    await within(sezione).findByRole("button", { name: "Correggi: M 21" })
  })

  it("Chiudi li toglie di nuovo", async () => {
    aperta()
    const sezione = await aperti()
    fireEvent.click(within(piede(sezione)).getByRole("button", { name: "Chiudi" }))
    expect(nomi(sezione)).toEqual([])
    expect(within(piede(sezione)).getByRole("button", { name: "Apri" })).toBeDefined()
  })

  it("Correggi apre la scheda dell'oggetto col nome di adesso gia' scelto", async () => {
    aperta()
    const sezione = await aperti()
    const scheda = riga(sezione, "M 3")
    expect(within(scheda).getAllByRole("radio").map((r) => r.closest("label")?.textContent?.replace(/frame di.*/, ""))).toEqual([
      "M 3",
      "Altro nome",
      "Non \u00e8 un oggetto",
    ])
    expect(within(scheda).getByRole("radio", { name: "M 3" })).toHaveProperty("checked", true)
    // aperta senza toccare niente non e' una modifica
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
    // una cosa aperta alla volta: la domanda di sopra si e' chiusa
    expect(sezione.querySelectorAll("article.as-domanda")).toHaveLength(1)
  })

  it("una correzione parte con le altre risposte, e la riga dice che e' da applicare", async () => {
    aperta()
    const sezione = await aperti()
    const scheda = riga(sezione, "M 3")
    fireEvent.click(within(scheda).getByRole("radio", { name: "Altro nome" }))
    fireEvent.change(within(scheda).getByLabelText("Nome dell'oggetto"), { target: { value: "NGC 5272" } })
    expect(scheda.querySelector(".as-risposta")?.textContent).toBe("da applicare")
    // rimesso il nome di adesso, non c'e' piu' niente da mandare
    fireEvent.click(within(scheda).getByRole("radio", { name: "M 3" }))
    expect(scheda.querySelector(".as-risposta")).toBeNull()
    fireEvent.click(within(scheda).getByRole("radio", { name: /^Non \u00e8 un oggetto/ }))
    expect(await mandati()).toEqual([{ key: "object:m-3", not_an_object: true }])
  })

  it("un oggetto a posto senza sigla (una cometa, un nome scritto) si apre col suo nome nel campo", async () => {
    const cometa = { ...aPosto(1), key: "object:C/2023 A3", name: "C/2023 A3", slug: null }
    aperta(PAGINA, { items: [aPosto(1), cometa], total: 2, limit: 20, offset: 0 })
    const sezione = await aperti()
    const scheda = riga(sezione, "C/2023 A3")
    expect(within(scheda).getByRole("radio", { name: "Altro nome" })).toHaveProperty("checked", true)
    const campo = within(scheda).getByLabelText("Nome dell'oggetto")
    expect(campo).toHaveProperty("value", "C/2023 A3")
    // cambiato e rimesso il nome di adesso, non c'e' niente da mandare
    fireEvent.change(campo, { target: { value: "C/2023 A3 Tsuchinshan" } })
    expect(scheda.querySelector(".as-risposta")?.textContent).toBe("da applicare")
    fireEvent.change(campo, { target: { value: "C/2023 A3" } })
    expect(scheda.querySelector(".as-risposta")).toBeNull()
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
  })

  it("senza domande aperte la sezione c'e' lo stesso: gli oggetti a posto si correggono da li'", async () => {
    aperta({ ...PAGINA, to_confirm: 0, objects: [] })
    const sezione = await vaiASezione(/^oggetti$/i)
    expect(within(piede(sezione)).getByRole("button", { name: "Apri" })).toBeDefined()
    // che non c'e' niente da fare si dice lo stesso
    expect(screen.getByText("Niente da confermare")).toBeDefined()
  })
})
