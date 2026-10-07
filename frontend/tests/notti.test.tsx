// @vitest-environment jsdom
/**
 * La pagina **Notti**: le serate passate, una riga ciascuna.
 *
 * Le regole vengono dal backend e la pagina deve **non tradirle**: una notte e' una riga anche
 * con due oggetti dentro, le ore arrivano gia' sommate, e cio' che non sta in nessuna notte si
 * dice invece di sparire. I tre modi di non avere notti sono tre risposte diverse
 * (`docs/domini/notti.md`).
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, chiamate, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

const DICIOTTO = {
  id: 7,
  night_date: "2024-05-18",
  site: "Cima Ekar",
  site_source: "declared",
  frames: 3,
  integration_s: 10800,
  untimed: 0,
  objects: [
    { key: "m-51", name: "M 51", frames: 2, integration_s: 7200 },
    { key: "m-101", name: "M 101", frames: 1, integration_s: 3600 },
  ],
  filters: [
    { name: "Ha", frames: 2, integration_s: 7200 },
    { name: "OIII", frames: 1, integration_s: 3600 },
  ],
  moon: { phase_key: "waxing_gibbous", illumination_pct: 69 },
  weather: {
    state: "ok",
    verdict: "go",
    cloud_total_pct: 8,
    usable_hours: 7,
    window: "dark",
    window_hours: 8,
  },
}

const DICIASSETTE = {
  id: 6,
  night_date: "2024-05-17",
  site: "Casa",
  site_source: "detected",
  frames: 1,
  integration_s: 600,
  untimed: 0,
  objects: [{ key: "m-31", name: "M 31", frames: 1, integration_s: 600 }],
  filters: [],
  moon: null,
  weather: { state: "waiting" },
}

const NIENTE_ORE = {
  ...DICIASSETTE,
  id: 5,
  night_date: "2024-05-16",
  frames: 4,
  integration_s: 0,
  untimed: 4,
  // un filtro le cui pose non dicono la durata: ha ripreso, e non si sa per quanto
  filters: [
    { name: "Lum", frames: 2, integration_s: 0 },
    { name: "OIII", frames: 2, integration_s: 0 },
  ],
}

function notti(items: unknown[], extra: Record<string, unknown> = {}) {
  rispondi({
    ...STANOTTE,
    "/api/v1/nights": {
      stato: 200,
      corpo: {
        items,
        total: items.length,
        limit: 100,
        offset: 0,
        totals: { nights: items.length, frames: 4, integration_s: 11400, untimed: 0 },
        waiting: [],
        still_reading: 0,
        ...extra,
      },
    },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  })
}

/** Apre l'app e va sulle Notti **dalla barra**: e' la strada dell'utente, e prova anche che la
 *  voce sia accesa -- una pagina raggiungibile solo scrivendo l'indirizzo non esiste. */
async function apriNotti() {
  const reso = await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /notti/i }))
  await screen.findByRole("heading", { name: /notti/i })
  return reso
}

const elenco = () => screen.findByRole("list", { name: /notti/i })

describe("le Notti", () => {
  it("elenca le notti, dalla piu' recente", async () => {
    notti([DICIOTTO, DICIASSETTE])
    await apriNotti()

    const righe = within(await elenco()).getAllByRole("listitem")
    expect(righe).toHaveLength(2)
    expect(righe[0]?.textContent).toContain("18")
    expect(righe[1]?.textContent).toContain("17")
  })

  it("una notte porta il giorno, il sito, gli oggetti, le ore e i frame", async () => {
    notti([DICIOTTO])
    await apriNotti()

    const riga = within(await elenco()).getByRole("listitem")
    expect(riga.textContent).toContain("Cima Ekar")
    expect(riga.textContent).toContain("M 51")
    expect(riga.textContent).toContain("M 101")
    expect(riga.textContent).toContain("3 frame")
    expect(riga.textContent).toContain("3 h") // 10.800 s, gia' sommati dal backend
  })

  it("una notte dice che luna c'era, con quanto era illuminata", async () => {
    // E' la prima cosa che si ricorda di una nottata, e cambia cosa si e' potuto riprendere.
    notti([DICIOTTO])
    await apriNotti()

    const riga = within(await elenco()).getByRole("listitem")
    expect(riga.textContent).toContain("Gibbosa crescente")
    expect(riga.textContent).toContain("69")
  })

  it("una notte di cui non si sa la luna non scrive un trattino muto", async () => {
    // Senza il fuso del sito non c'e' una mezzanotte, quindi non c'e' una Luna: la riga tace,
    // e non mette un segno che sembra un dato.
    notti([DICIASSETTE])
    await apriNotti()

    const riga = within(await elenco()).getByRole("listitem")
    expect(riga.textContent).not.toMatch(/luna|%/i)
  })

  it("accanto alla data c'e' il giorno della settimana", async () => {
    // "Quel sabato" e' il modo in cui ci si ricorda una serata: la data da sola non lo dice.
    notti([DICIOTTO])
    await apriNotti()

    expect((await elenco()).textContent).toMatch(/sabato/i)
  })

  it("una notte con due oggetti resta una riga sola", async () => {
    // Spaccarla in due righe spezzerebbe le ore fra le righe, e due righe con la stessa data
    // sembrerebbero un doppione. La vista per oggetto esiste gia' ed e' l'Archivio.
    notti([DICIOTTO])
    await apriNotti()

    expect(within(await elenco()).getAllByRole("listitem")).toHaveLength(1)
  })

  it("una notte dice i filtri, dal piu' usato", async () => {
    notti([DICIOTTO])
    await apriNotti()

    const riga = within(await elenco()).getByRole("listitem")
    const testo = riga.textContent ?? ""
    expect(testo).toContain("Ha")
    expect(testo).toContain("OIII")
    expect(testo.indexOf("Ha")).toBeLessThan(testo.indexOf("OIII"))
  })

  it("una notte di cui nessun frame dice la durata non scrive zero ore", async () => {
    // "Non lo so" e "zero ore" sono due risposte diverse, ed e' la stessa regola dell'Archivio.
    notti([NIENTE_ORE])
    await apriNotti()

    const testo = (await elenco()).textContent ?? ""
    expect(testo).toContain("4 senza tempo")
    expect(testo).not.toMatch(/\b0 h\b/)
    // e i filtri senza ore restano leggibili: senza questa riga uscirebbe "Lum , OIII"
    expect(testo).toContain("Lum, OIII")
  })

  it("in cima ci sono le notti, le ore e i frame di tutto l'archivio", async () => {
    notti([DICIOTTO], { totals: { nights: 42, frames: 900, integration_s: 360000, untimed: 3 } })
    await apriNotti()

    expect(await screen.findByText(/42 notti in archivio/i)).toBeDefined()
    const cappello = screen.getByText(/900 frame in tutto/i)
    expect(cappello.textContent).toContain("100") // 360.000 s = 100 h, gia' sommate dal backend
    expect(cappello.textContent).toContain("3 senza tempo")
  })

  it("dice quanti frame aspettano una risposta, e porta a Da confermare", async () => {
    notti([DICIOTTO], { waiting: [{ answer_at: "review", frames: 12 }] })
    await apriNotti()

    expect(await screen.findByText(/12 frame aspettano una tua risposta/i)).toBeDefined()
    // dentro la pagina: `link` da solo pesca anche la voce della barra, che c'e' sempre
    const dentro = within(screen.getByRole("main"))
    expect(dentro.getByRole("link", { name: /da confermare/i })).toBeDefined()
  })

  it("chi deve dichiarare il sito non viene mandato a Da confermare", async () => {
    // E' il difetto per cui il gruppo esiste: a quei frame *Da confermare* non ha niente da
    // mostrare, e la risposta sta nelle Impostazioni.
    notti([DICIOTTO], { waiting: [{ answer_at: "site", frames: 5 }] })
    await apriNotti()

    expect(await screen.findByText(/5 frame aspettano di sapere da dove osservavi/i)).toBeDefined()
    const dentro = within(screen.getByRole("main"))
    expect(dentro.queryByRole("link", { name: /da confermare/i })).toBeNull()
    expect(dentro.getByRole("link", { name: /dichiara il tuo sito/i })).toBeDefined()
  })

  it("un frame senza risposta possibile non porta da nessuna parte", async () => {
    // Un frame che non dice quando e' stato ripreso non ha niente da rispondere: un collegamento
    // lo manderebbe davanti a un elenco dove quel frame non compare.
    notti([DICIOTTO], { waiting: [{ answer_at: "never", frames: 4 }] })
    await apriNotti()

    expect(await screen.findByText(/4 frame non dicono quando sono stati ripresi/i)).toBeDefined()
    const dentro = within(screen.getByRole("main"))
    expect(dentro.queryByRole("link", { name: /da confermare/i })).toBeNull()
  })

  it("dice che la lettura non e' finita", async () => {
    // Senza questa riga, chi apre la pagina a meta' corsa vede tre notti e crede di averne tre.
    notti([DICIOTTO], { still_reading: 431 })
    await apriNotti()

    expect(await screen.findByText(/sto ancora leggendo/i)).toBeDefined()
    expect(screen.getByText(/431/)).toBeDefined()
  })

  it("i quattro modi di non avere notti dicono quattro cose diverse", async () => {
    const senzaNotti = { totals: { nights: 0, frames: 0, integration_s: 0, untimed: 0 } }
    notti([], senzaNotti)
    await apriNotti()
    expect(await screen.findByText(/nessuna notte, per ora/i)).toBeDefined()

    pulisci()
    notti([], { ...senzaNotti, waiting: [{ answer_at: "site", frames: 8 }] })
    await apriNotti()
    expect(await screen.findByText(/non so da dove osservavi/i)).toBeDefined()

    pulisci()
    notti([], { ...senzaNotti, waiting: [{ answer_at: "review", frames: 8 }] })
    await apriNotti()
    expect(await screen.findByText(/l'app ti sta aspettando/i)).toBeDefined()

    pulisci()
    notti([], { ...senzaNotti, still_reading: 90 })
    await apriNotti()
    expect(await screen.findByText(/le notti stanno arrivando/i)).toBeDefined()
  })

  it("quando ce n e' piu' di una pagina, si vedono anche le altre", async () => {
    notti([DICIOTTO], { total: 2 })
    await apriNotti()

    expect(await screen.findByRole("button", { name: /mostra altre/i })).toBeDefined()
  })

  it("se le notti non si leggono lo dice, invece di sembrare un archivio vuoto", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/nights": { stato: 500, corpo: { detail: "boom" } },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    await apriNotti()

    expect(await screen.findByText(/non sono riuscito a leggere le notti/i)).toBeDefined()
  })
})

describe("le Notti, il cielo di quella notte", () => {
  it("una notte ripresa dice com'era il cielo, e quante ore sono state serene", async () => {
    notti([DICIOTTO])
    await apriNotti()

    const riga = within(await elenco()).getByRole("listitem")
    expect(riga.textContent).toContain("poco nuvoloso (nuvole al 8%)")
    expect(riga.textContent).toContain("7 ore utili su 8 di buio")
  })

  it("una notte il cui meteo non e' ancora arrivato lo dice", async () => {
    notti([DICIASSETTE])
    await apriNotti()

    const riga = within(await elenco()).getByRole("listitem")
    expect(riga.textContent).toContain("il meteo di quella notte non e' ancora arrivato")
  })

  it("una notte che l'archivio non racconta lo dice, invece di un cielo inventato", async () => {
    notti([{ ...DICIASSETTE, weather: { state: "ok", verdict: null, cloud_total_pct: null, usable_hours: null, window: null, window_hours: null } }])
    await apriNotti()

    const riga = within(await elenco()).getByRole("listitem")
    expect(riga.textContent).toContain("non dice com'era il cielo")
  })

  it("una notte di un sito senza fuso dice che il meteo non si puo' sapere", async () => {
    notti([{ ...DICIASSETTE, weather: { state: "unknown" } }])
    await apriNotti()

    const riga = within(await elenco()).getByRole("listitem")
    expect(riga.textContent).toContain("non si puo' sapere")
  })
})

describe("le Notti, una notte dall'indirizzo", () => {
  it("con ?notte= chiede quella notte sola e porta a tutte le altre", async () => {
    notti([DICIOTTO], { total: 1 })
    window.history.pushState({}, "", `/notti?notte=${DICIOTTO.id}`)
    await disegna()

    const righe = within(await elenco()).getAllByRole("listitem")
    expect(righe).toHaveLength(1)
    expect(chiamate().some((u) => u.includes("/api/v1/nights") && u.includes(`night=${DICIOTTO.id}`))).toBe(true)
    expect(screen.getByRole("link", { name: "Tutte le notti" }).getAttribute("href")).toBe("/notti")
  })

  it.each(["-3", "1.5", "abc"])("un indirizzo storto (?notte=%s) dice che la notte non c'e', senza chiederla", async (scritto) => {
    notti([DICIOTTO])
    window.history.pushState({}, "", `/notti?notte=${scritto}`)
    await disegna()

    expect(await screen.findByText(/questa notte non c'e' piu'/i)).toBeDefined()
    expect(chiamate().some((u) => u.includes("night="))).toBe(false)
    // niente da aspettare: la pagina non resta "in lettura"
    expect(screen.queryByText(/un momento/i)).toBeNull()
  })

  it("una notte che non c'e' piu' lo dice, invece di dire che l'archivio e' vuoto", async () => {
    notti([], { total: 0 })
    window.history.pushState({}, "", "/notti?notte=999")
    await disegna()

    expect(await screen.findByText(/questa notte non c'e' piu'/i)).toBeDefined()
  })
})
