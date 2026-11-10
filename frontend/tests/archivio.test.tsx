// @vitest-environment jsdom
/**
 * L'**Archivio** (tavola v78): cosa hai ripreso, a carte o in elenco, con la testa di tutto
 * l'archivio. Le regole vengono dal backend e la pagina deve solo **non tradirle**: le ore
 * arrivano sommate, un frame senza tempo non diventa zero, i filtri arrivano in ordine. I criteri
 * stanno in `archivio-criteri.test.tsx`, la finestra dell'oggetto in `archivio-finestra.test.tsx`,
 * il banco in `archivio-banco.tsx`.
 */
import { readFileSync, readdirSync } from "node:fs"
import { resolve } from "node:path"

import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { numero } from "../src/i18n"
import { chiamate, pulisci, rispondi } from "./banco"
import {
  IGNOTO,
  INTERO,
  M31,
  MOSAICO,
  apriArchivio,
  apriArchivioSu,
  apriDi,
  archivio,
  carte,
  conArchivio,
  vaiAll,
  voceArchivio,
} from "./archivio-banco"

afterEach(pulisci)

const testoDi = (el: Element | null | undefined) => el?.textContent ?? ""

describe("l'Archivio", () => {
  it("dice cosa hai ripreso, con i frame e le ore", async () => {
    archivio([M31])
    await apriArchivio()

    const [carta] = await carte()
    expect(within(carta as HTMLElement).getAllByText("M 31").length).toBeGreaterThan(0)
    expect(testoDi(carta)).toContain("120 frame")
    // 43.200 s = 12 h: il backend manda i secondi, lo schermo legge le ore
    expect(testoDi(carta)).toContain("12 h")
  })

  it("in testa dice tutto l'archivio: oggetti, mosaici, ore, frame e notti", async () => {
    archivio([M31], { whole: INTERO })
    await apriArchivio()

    const testa = await screen.findByRole("region", { name: "L'archivio" })
    await waitFor(() => expect(testoDi(testa)).toContain("oggetti, di cui 3 mosaici"))
    expect(testoDi(testa)).toContain("240")
    expect(testoDi(testa)).toContain(`486 h · ${numero(18430)} frame · 212 notti`)
  })

  it("se i frame non sanno la notte (nessun sito), la testa non scrive zero notti", async () => {
    archivio([M31], { whole: { ...INTERO, nights: 0 } })
    await apriArchivio()

    const testa = await screen.findByRole("region", { name: "L'archivio" })
    await waitFor(() => expect(testoDi(testa)).toContain(`${numero(18430)} frame`))
    expect(testoDi(testa)).not.toMatch(/notti|notte/)
  })

  it("un frame che non dice quanto e' durato non diventa zero", async () => {
    archivio([IGNOTO])
    await apriArchivio()

    const [carta] = await carte()
    expect(testoDi(carta)).toContain("12 senza durata")
  })

  it("se nessun frame dice la durata, non scrive zero ore", async () => {
    archivio([{ ...IGNOTO, frames: 3, untimed: 3, integration_s: 0 }])
    await apriArchivio()

    const [carta] = await carte()
    expect(testoDi(carta)).toContain("senza durata")
    expect(testoDi(carta)).not.toMatch(/\b0 h\b/)
  })

  it("si apre a carte, e l'altra vista e' a un clic", async () => {
    archivio([M31])
    await apriArchivio()

    expect((await screen.findByRole("radio", { name: /carte/i })).getAttribute("aria-checked")).toBe("true")
    await vaiAll(/elenco/i)

    expect(await screen.findByRole("region", { name: /^elenco$/i })).toBeDefined()
    expect(document.querySelector(".al-arch__centro-1")).toBeNull()
  })

  it("quale vista stai guardando resta nell'indirizzo", async () => {
    archivio([M31])
    await apriArchivio()

    await vaiAll(/elenco/i)

    await waitFor(() => expect(window.location.search).toContain("vista=elenco"))
  })

  it("cambiare vista non cancella il resto dell'indirizzo", async () => {
    archivio([M31])
    await apriArchivio()
    fireEvent.change(await screen.findByRole("combobox", { name: /^ordine$/i }), { target: { value: "hours" } })
    await waitFor(() => expect(window.location.search).toContain("sort=hours"))

    await vaiAll(/elenco/i)

    await waitFor(() => expect(window.location.search).toContain("vista=elenco"))
    expect(window.location.search).toContain("sort=hours")
  })

  it("dice con che filtri hai ripreso, nell'ordine dei filtri", async () => {
    archivio([M31])
    await apriArchivio()

    const [carta] = await carte()
    expect(within(carta as HTMLElement).getByText("Lum · Ha")).toBeDefined()
  })

  it("un oggetto senza filtri riconosciuti non mostra pastiglie finte", async () => {
    archivio([{ ...IGNOTO, untimed: 0, frames: 0, integration_s: 0 }])
    await apriArchivio()

    const [carta] = await carte()
    expect(carta?.querySelector(".al-c-barra-filtri__riga-1")).toBeNull()
    expect(within(carta as HTMLElement).getByText(/^filtri non indicati$/i)).toBeDefined()
  })

  it("un oggetto che il catalogo non conosce lo dice nella carta, tipo e costellazione", async () => {
    archivio([IGNOTO])
    await apriArchivio()

    const [carta] = await carte()
    expect(testoDi(carta)).toContain("Tipo non disponibile · Costellazione non disponibile")
  })

  it("nell'elenco sotto il nome c'e' il nome comune del catalogo, e il mosaico dice i suoi pannelli", async () => {
    archivio([M31, MOSAICO])
    await apriArchivioSu("/archivio?vista=elenco")

    const elenco = await screen.findByRole("region", { name: /^elenco$/i })
    await waitFor(() => expect(testoDi(elenco)).toContain("Andromeda Galaxy"))
    expect(testoDi(elenco)).toContain("mosaico di 4 pannelli")
  })

  it("la costellazione si legge col suo nome latino, non con la sigla", async () => {
    archivio([M31])
    await apriArchivio()

    const [carta] = await carte()
    expect(testoDi(carta)).toContain("galassia · Andromeda")
  })

  it("dice quanti ne stai vedendo su quanti sono, e in che ordine", async () => {
    archivio([M31], { total: 600 })
    await apriArchivio()

    expect(await screen.findByText("1 di 600, per nome")).toBeDefined()
  })

  it("a mani vuote dice cosa fare, non nessun risultato", async () => {
    archivio([], { whole: { ...INTERO, rows: 0, mosaics: 0, frames: 0, integration_s: 0, nights: 0 } })
    await apriArchivio()

    expect(await screen.findByText(/^archivio vuoto$/i)).toBeDefined()
    expect(screen.getByText(/^aggiungi cartelle$/i)).toBeDefined()
    expect(screen.queryByLabelText(/cerca un oggetto/i)).toBeNull()
  })

  it("ogni tipo che il catalogo usa ha la sua parola, e nessuno arriva a schermo come sigla", async () => {
    const cartella = resolve(process.cwd(), "..", "backend", "astrolog", "catalog", "data")
    const file = readdirSync(cartella).find((n) => /^catalogo-.*\.json$/.test(n))
    expect(file, `nessun catalogo in ${cartella}`).toBeDefined()
    const catalogo = JSON.parse(readFileSync(resolve(cartella, file ?? ""), "utf-8")) as {
      objects: { type_code: string }[]
    }
    const codici = [...new Set(catalogo.objects.map((o) => o.type_code))]
    expect(codici.length).toBeGreaterThan(0)

    archivio(codici.map((codice, i) => ({ ...M31, key: `k-${i}`, name: `Oggetto ${i}`, type_code: codice })))
    await apriArchivio()

    const tutte = await carte()
    expect(tutte).toHaveLength(codici.length)
    for (const [i, carta] of tutte.entries()) {
      expect(testoDi(carta), `il codice ${codici[i]} non ha una parola`).not.toContain("Tipo non disponibile")
      expect(testoDi(carta)).not.toContain(codici[i])
    }
  })

  it("un tipo che la pagina non conosce non arriva a schermo come sigla: dice che non si sa", async () => {
    archivio([{ ...M31, type_code: "CODICE_INVENTATO" }])
    await apriArchivio()

    const [carta] = await carte()
    expect(testoDi(carta)).not.toContain("CODICE_INVENTATO")
    expect(testoDi(carta)).toContain("Tipo non disponibile")
  })

  it("se l archivio non risponde lo dice, invece di sembrare vuoto, e si riprova", async () => {
    rispondi(conArchivio({ stato: 500, corpo: { detail: "boom" } }))
    await apriArchivio()

    expect(await screen.findByText(/^archivio non disponibile$/i)).toBeDefined()
    const prima = chiamate().filter((u) => u.includes("/api/v1/archive")).length
    fireEvent.click(screen.getByText(/^riprova$/i))
    await waitFor(() =>
      expect(chiamate().filter((u) => u.includes("/api/v1/archive")).length).toBeGreaterThan(prima),
    )
  })

  it("mentre legge tiene il posto delle carte, e lo dice a chi ascolta", async () => {
    let arriva: (v: unknown) => void = () => {}
    const attesa = new Promise((fatto) => (arriva = fatto))
    rispondi(conArchivio({ ...voceArchivio([M31]), attesa }))
    await apriArchivio()

    expect(await screen.findByLabelText(/caricamento/i)).toBeDefined()
    arriva(null)
    expect((await carte()).length).toBe(1)
    expect(screen.queryByLabelText(/caricamento/i)).toBeNull()
  })

  it("accanto a Mostra altri dice quanti ne stai vedendo e quanti sono", async () => {
    archivio([M31], { total: 600, limit: 1 })
    await apriArchivio()

    const altri = await screen.findByRole("link", { name: /mostra altri 20/i })
    expect(testoDi(altri.closest(".al-arch__riga-9"))).toContain("1 di 600")
  })

  it("quando ce n e piu' di una pagina, si possono vedere anche gli altri", async () => {
    archivio([M31], { total: 600, limit: 1 })
    await apriArchivio()

    fireEvent.click(await screen.findByRole("link", { name: /mostra altri/i }))

    await waitFor(() => expect(chiamate().some((u) => u.includes("/api/v1/archive") && u.includes("offset=1"))).toBe(true))
  })

  it("e quando sono tutte li', non offre di caricarne altre", async () => {
    archivio([M31, IGNOTO])
    await apriArchivio()

    await carte()
    expect(screen.queryByRole("link", { name: /mostra altri/i })).toBeNull()
  })
})

describe("l'Archivio, produzioni, mosaici e frame senza oggetto", () => {
  const PIU = {
    ...M31,
    productions: [M31.productions[0], { ...M31.productions[0], optics: "Newton", optics_id: 3 }],
  }

  it("la carta ha un posto di anteprima per produzione, e dice quante sono", async () => {
    archivio([PIU])
    await apriArchivio()

    const [carta] = await carte()
    expect(carta?.querySelectorAll(".al-arch__foto-parte")).toHaveLength(2)
    expect(testoDi(carta?.querySelector(".al-arch__strato-2"))).toBe("2 produzioni")
  })

  it("oltre tre produzioni le anteprime vanno su due righe, senza nasconderne", async () => {
    const cinque = { ...M31, productions: Array.from({ length: 5 }, () => M31.productions[0]) }
    archivio([cinque])
    await apriArchivio()

    const [carta] = await carte()
    const griglia = carta?.querySelector<HTMLElement>(".al-arch__foto-griglia")
    expect(griglia?.querySelectorAll(".al-arch__foto-parte")).toHaveLength(5)
    expect(griglia?.style.gridTemplateColumns).toBe("repeat(3,minmax(0,1fr))")
  })

  it("la carta di un mosaico dice mosaico e quanti pannelli, e si sente", async () => {
    archivio([MOSAICO])
    await apriArchivio()

    const [carta] = await carte()
    expect(testoDi(carta?.querySelector(".al-arch__strato-2"))).toBe("mosaico · 4 pannelli")
    expect((await apriDi("IC 405")).getAttribute("aria-label")).toContain("mosaico di 4 pannelli")
  })

  it("nell'elenco la colonna delle produzioni dice una, quante, o il mosaico", async () => {
    archivio([M31, PIU, MOSAICO])
    await apriArchivioSu("/archivio?vista=elenco")

    await screen.findByRole("region", { name: /^elenco$/i })
    await waitFor(() => expect(document.querySelectorAll(".al-arch__testo-9")).toHaveLength(3))
    const colonna = [...document.querySelectorAll(".al-arch__testo-9")].map((c) => c.textContent)
    expect(colonna).toEqual(["una", "2 produzioni", "mosaico · 4"])
  })

  it("i frame senza oggetto hanno la loro carta, e senza ASTAP l'avviso porta alle Impostazioni", async () => {
    const fuori = { frames: 1204, integration_s: 51480, untimed: 0, filters: [], solver_missing: true }
    archivio([M31], { unresolved: fuori })
    await apriArchivio()

    const tutte = await carte()
    expect(testoDi(tutte[0])).toContain("Non risolti")
    expect(testoDi(tutte[0])).toContain(`${numero(1204)} frame`)
    const avviso = `ASTAP non è installato: ${numero(1204)} frame restano non risolti`
    expect(await screen.findByText((testo) => testo.startsWith(avviso))).toBeDefined()
    fireEvent.click(screen.getByText(/^apri le impostazioni$/i))
    await waitFor(() => expect(window.location.pathname).toBe("/impostazioni/riconoscitore"))
  })

  it("coi criteri la carta dei frame senza oggetto resta in testa, anche senza oggetti trovati", async () => {
    const fuori = { frames: 3, integration_s: 0, untimed: 3, filters: [], solver_missing: false }
    archivio([M31], { unresolved: fuori })
    await apriArchivioSu("/archivio?type=galaxy")

    const tutte = await carte()
    expect(testoDi(tutte[0])).toContain("Senza oggetti identificati")
    expect(testoDi(tutte[1])).toContain("M 31")

    pulisci()
    archivio([], { unresolved: fuori, whole: INTERO })
    await apriArchivioSu("/archivio?type=galaxy")
    expect(await screen.findByText(/^nessun oggetto con questi criteri$/i)).toBeDefined()
    expect(testoDi(document.querySelector(".al-arch__centro-1 > section"))).toContain("Senza oggetti identificati")
  })

  it("con ASTAP la carta dice senza oggetti identificati, e non c'e' l'avviso", async () => {
    const fuori = { frames: 3, integration_s: 0, untimed: 3, filters: [], solver_missing: false }
    archivio([M31], { unresolved: fuori })
    await apriArchivio()

    const tutte = await carte()
    expect(testoDi(tutte[0])).toContain("Senza oggetti identificati")
    expect(screen.queryByText(/ASTAP non è installato/)).toBeNull()
  })
})
