// @vitest-environment jsdom
/**
 * La pagina **Notti** della tavola v76 (`docs/domini/notti.md`): la notte protagonista, la
 * striscia delle ultime sette, il calendario, i criteri, l'elenco a confronto, tutto l'archivio.
 * La pagina non calcola: esiti, ore di posa, ripresa e conteggi arrivano dal backend.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, chiamate, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

const CIELO = {
  state: "ok",
  arrives_on: null,
  verdict: "go",
  cloud_total_pct: 8,
  usable_hours: 7,
  window: "dark",
  window_hours: 9,
  transparency: 88,
  exposure_hours: 7.9,
  dark_hours: 9,
  without_aerosol: true,
  sky_word: "scattered",
}

const DICIOTTO = {
  id: 7,
  night_date: "2024-05-18",
  site: "Cima Ekar",
  site_source: "detected",
  site_from: "frames",
  shooting: { kind: "mixed", broadband_hours: 3.5, dark_hours: 7.5 },
  frames: 3,
  integration_s: 10800,
  untimed: 0,
  objects: [
    { key: "m-51", name: "M 51", frames: 2, integration_s: 7200, untimed: 0, bar_pct: 100 },
    { key: "m-101", name: "M 101", frames: 1, integration_s: 3600, untimed: 0, bar_pct: 50 },
  ],
  filters: [
    { name: "Ha", passband: "HA", frames: 2, integration_s: 7200 },
    { name: "OIII", passband: "OIII", frames: 1, integration_s: 3600 },
  ],
  moon: { phase_key: "waxing_gibbous", illumination_pct: 69, lit_side: "right" },
  weather: CIELO,
}

const DICIASSETTE = {
  id: 6,
  night_date: "2024-05-17",
  site: "Casa",
  site_source: "detected",
  site_from: "home",
  shooting: null,
  frames: 1,
  integration_s: 600,
  untimed: 0,
  objects: [{ key: "m-31", name: "M 31", frames: 1, integration_s: 600, untimed: 0, bar_pct: 100 }],
  filters: [],
  moon: null,
  weather: { ...CIELO, state: "unknown", verdict: null, exposure_hours: null, sky_word: null },
}

const APRILE = { ...DICIASSETTE, id: 3, night_date: "2024-04-02", site_from: "answer" }

const CRITERI = [
  { key: "year", options: [{ value: "2024", nights: 3, chosen: false }] },
  { key: "site", options: [{ value: "1", name: "Casa", nights: 2, chosen: false }, { value: "2", name: "Cima Ekar", nights: 1, chosen: false }] },
  { key: "setup", options: [] },
  { key: "filter", options: [{ value: "Ha", passband: "HA", nights: 1, chosen: false }, { value: "OIII", passband: "OIII", nights: 0, chosen: false }] },
  { key: "constellation", options: [{ value: "CVn", nights: 1, chosen: false }] },
  { key: "sky", options: [{ value: "go", nights: 1, chosen: false }, { value: "unknown", nights: 2, chosen: false }] },
]

const MAGGIO = {
  month: "2024-05",
  days: [
    { day: 17, verdict: null, nights: [{ id: 6, site: "Casa", verdict: null }] },
    { day: 18, verdict: "go", nights: [{ id: 7, site: "Cima Ekar", verdict: "go" }] },
  ],
  nights: 2,
  good: 1,
  integration_s: 11400,
  untimed: 0,
  first_month: "2024-04",
  last_month: "2026-11",
  tonight: "2026-11-07",
}

function pagina(items: unknown[], extra: Record<string, unknown> = {}) {
  return {
    items,
    total: items.length,
    limit: 20,
    offset: 0,
    criteria: CRITERI,
    months: [
      { month: "2024-05", nights: 2, integration_s: 11400, untimed: 0 },
      { month: "2024-04", nights: 1, integration_s: 600, untimed: 0 },
    ],
    empty: null,
    totals: { nights: items.length, frames: 4, integration_s: 11400, untimed: 0, objects: 3 },
    waiting: [],
    waiting_frames: 0,
    still_reading: 0,
    reading_done_pct: null,
    ...extra,
  }
}

function notti(corpo: unknown, mese: unknown = MAGGIO) {
  rispondi({
    ...STANOTTE,
    "/api/v1/nights/calendar": { stato: 200, corpo: mese },
    "/api/v1/nights": { stato: 200, corpo },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  })
}

async function apriNotti() {
  const reso = await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /notti/i }))
  return reso
}

const protagonista = async () => screen.findByRole("region", { name: "La notte" })

describe("le Notti", () => {
  it("la notte piu' recente e' la protagonista", async () => {
    notti(pagina([DICIOTTO, DICIASSETTE, APRILE]))
    await apriNotti()
    const carta = await protagonista()
    expect(within(carta).getByText("Sabato 18 maggio 2024")).toBeTruthy()
    expect(within(carta).getByText("3 h")).toBeTruthy()
    expect(within(carta).getByText("3 frame")).toBeTruthy()
  })

  it("accanto alla data c'e' il giorno della settimana", async () => {
    notti(pagina([DICIOTTO]))
    await apriNotti()
    expect(within(await protagonista()).getByText(/^Sabato/)).toBeTruthy()
  })

  it("il sito dice da dove viene", async () => {
    notti(pagina([DICIOTTO, DICIASSETTE, APRILE]))
    await apriNotti()
    expect(within(await protagonista()).getByText(/dalle coordinate nei frame/)).toBeTruthy()
    fireEvent.click(screen.getByRole("button", { name: /2 aprile 2024/i }))
    expect(await within(await protagonista()).findByText(/dalla tua risposta in Da confermare/)).toBeTruthy()
  })

  it("la striscia porta le ultime sette notti, e una toccata diventa la protagonista", async () => {
    notti(pagina([DICIOTTO, DICIASSETTE, APRILE]))
    await apriNotti()
    const linguette = await screen.findAllByRole("tab")
    expect(linguette).toHaveLength(3)
    fireEvent.click(linguette[1] as HTMLElement)
    expect(await within(await protagonista()).findByText("Venerd\u00EC 17 maggio 2024")).toBeTruthy()
    expect(chiamate().some((u) => u.includes("limit=7"))).toBe(true)
  })

  it("una notte ripresa dice com'era il cielo", async () => {
    notti(pagina([DICIOTTO]))
    await apriNotti()
    const carta = await protagonista()
    expect(within(carta).getByText("Nuvole sparse, in media 8%")).toBeTruthy()
    expect(within(carta).getByText("7.9 ore di posa su 9 di buio \u00B7 senza aerosol")).toBeTruthy()
    expect(within(carta).getByText(/una tacca per ora di buio/)).toBeTruthy()
  })

  it("una notte di un sito senza fuso dice che il meteo non si puo' sapere, e porta al sito", async () => {
    notti(pagina([DICIASSETTE]))
    await apriNotti()
    const carta = await protagonista()
    expect(within(carta).getByText("Fuso orario del sito non riconosciuto.")).toBeTruthy()
    expect(within(carta).getByRole("link", { name: "Modifica sito" }).getAttribute("href")).toBe("/impostazioni/sito")
  })

  it("una notte giovane dice il giorno in cui arriva il meteo", async () => {
    const giovane = { ...DICIOTTO, weather: { ...CIELO, state: "waiting", verdict: null, exposure_hours: null, arrives_on: "2024-05-24" } }
    notti(pagina([giovane]))
    await apriNotti()
    expect(within(await protagonista()).getByText(/Il meteo arriva il 24 mag/)).toBeTruthy()
  })

  it("una notte dice che luna c'era, e la ripresa dice banda larga o stretta", async () => {
    notti(pagina([DICIOTTO]))
    await apriNotti()
    const carta = await protagonista()
    expect(within(carta).getByText("illuminata al 69%")).toBeTruthy()
    expect(within(carta).getByText("Gibbosa crescente")).toBeTruthy()
    expect(within(carta).getByText("3 h 30 di banda larga")).toBeTruthy()
  })

  it("una notte di cui non si sa la luna non scrive un trattino muto", async () => {
    notti(pagina([DICIASSETTE]))
    await apriNotti()
    expect(within(await protagonista()).queryByText(/illuminata/)).toBeNull()
    expect(within(await protagonista()).queryByText("\u2014")).toBeNull()
  })

  it("di ogni oggetto dice le ore con la sua barra", async () => {
    notti(pagina([DICIOTTO]))
    await apriNotti()
    const carta = await protagonista()
    expect(within(carta).getByText("M 51")).toBeTruthy()
    expect(within(carta).getAllByText("2 h").length).toBeGreaterThan(0)
    const barre = carta.querySelectorAll<HTMLElement>(".al-notti__pillola-2")
    expect([...barre].map((b) => b.style.width)).toEqual(["100%", "50%"])
  })

  it("una notte dice i filtri, nell'ordine dei filtri", async () => {
    notti(pagina([DICIOTTO]))
    await apriNotti()
    const carta = await protagonista()
    const testo = carta.textContent ?? ""
    expect(testo.indexOf("Ha")).toBeGreaterThan(-1)
    expect(testo.indexOf("Ha")).toBeLessThan(testo.indexOf("OIII"))
  })

  it("una notte di cui nessun frame dice la durata non scrive zero ore", async () => {
    const senza = { ...DICIOTTO, integration_s: 0, untimed: 3, objects: [{ ...DICIOTTO.objects[0], integration_s: 0, untimed: 2, bar_pct: 0 }] }
    notti(pagina([senza]))
    await apriNotti()
    const carta = await protagonista()
    expect(within(carta).getByText("Nei file non c\u2019\u00E8 il tempo: le ore non si contano.")).toBeTruthy()
    expect(within(carta).queryByText(/^0 h/)).toBeNull()
  })

  it("il calendario va di mese in mese", async () => {
    notti(pagina([DICIOTTO, DICIASSETTE, APRILE]))
    await apriNotti()
    await screen.findByRole("region", { name: "Calendario delle notti" })
    fireEvent.click(await screen.findByRole("link", { name: /mese prima/i }))
    expect(chiamate().some((u) => u.includes("month=2024-04"))).toBe(true)
  })

  it("i criteri dicono quante notti restano", async () => {
    notti(pagina([DICIOTTO, DICIASSETTE, APRILE]))
    await apriNotti()
    fireEvent.click(await screen.findByRole("link", { name: /^Apri/ }))
    const ha = (await screen.findByText("Ha", { selector: ".al-scelta__voce *, .al-scelta__voce" })).closest("a") as HTMLElement
    expect(ha.textContent).toContain("1")
    fireEvent.click(ha)
    expect(chiamate().some((u) => u.includes("filter=Ha"))).toBe(true)
  })

  it("nessuna notte con questi criteri", async () => {
    notti(pagina([]))
    await apriNotti()
    expect(await screen.findByText("Nessuna notte con questi criteri")).toBeTruthy()
  })

  it("quando ce n'e' piu' di una pagina, si vedono anche le altre", async () => {
    notti(pagina([DICIOTTO], { total: 30 }))
    await apriNotti()
    expect(await screen.findByText("1 di 30")).toBeTruthy()
    fireEvent.click(screen.getByText("Carica altre"))
    expect(chiamate().some((u) => u.includes("offset=1"))).toBe(true)
  })

  it("in fondo c'e' tutto l'archivio", async () => {
    notti(pagina([DICIOTTO]))
    await apriNotti()
    const carta = await screen.findByRole("region", { name: "Tutto l\u2019archivio" })
    expect(within(carta).getByText("3 oggetti \u00B7 4 frame \u00B7 3.2 ore")).toBeTruthy()
    expect(within(carta).getByText("Le copie calibrate non sono contate.")).toBeTruthy()
  })

  it("ogni voce fuori da ogni notte porta dove si risponde", async () => {
    notti(pagina([DICIOTTO], { waiting: [{ answer_at: "review", frames: 37 }, { answer_at: "site", frames: 112 }, { answer_at: "date", frames: 9 }] }))
    await apriNotti()
    const carta = await screen.findByRole("region", { name: "Tutto l\u2019archivio" })
    expect(within(carta).getByRole("link", { name: /37 da confermare/ }).getAttribute("href")).toBe("/da-confermare")
    expect(within(carta).getByRole("link", { name: /112 senza sito/ }).getAttribute("href")).toBe("/impostazioni/sito")
    // la sezione dei frame senza data nasce col porting di Da confermare: fino ad allora si conta
    expect(within(carta).queryByRole("link", { name: /senza data/ })).toBeNull()
    expect(within(carta).getByText("senza data")).toBeTruthy()
    expect(screen.getByText("37 frame da confermare")).toBeTruthy()
  })

  it("un'ora sola in archivio non diventa \"1 ore\"", async () => {
    notti(pagina([DICIOTTO], { totals: { nights: 1, frames: 1, integration_s: 3510, untimed: 0, objects: 1 } }))
    await apriNotti()
    const carta = await screen.findByRole("region", { name: "Tutto l\u2019archivio" })
    expect(within(carta).getByText(/1 ora$/)).toBeTruthy()
  })

  it("se le altre notti non arrivano lo dice sotto l'elenco, e la pagina resta", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/nights/calendar": { stato: 200, corpo: MAGGIO },
      "/api/v1/nights?limit=20&offset=1": { stato: 500, corpo: {} },
      "/api/v1/nights": { stato: 200, corpo: pagina([DICIOTTO], { total: 30 }) },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    await apriNotti()
    fireEvent.click(await screen.findByText("Carica altre"))
    expect(await screen.findByText(/Le altre notti non sono arrivate/)).toBeTruthy()
    expect(screen.getByRole("region", { name: "La notte" })).toBeTruthy()
  })

  it("sul telefono ogni notte si chiama col giorno, le ore e il sito", async () => {
    notti(pagina([DICIOTTO, DICIASSETTE]))
    window.history.pushState({}, "", "/notti?formato=telefono")
    await disegna()
    expect(await screen.findByRole("tab", { name: "Sabato 18 maggio 2024, 3 h, Cima Ekar" })).toBeTruthy()
  })

  it("dice che la lettura non e' finita", async () => {
    notti(pagina([DICIOTTO], { still_reading: 40, reading_done_pct: 19 }))
    await apriNotti()
    expect(await screen.findByText("Scansione in corso, 19%: le notti si aggiungono da sole")).toBeTruthy()
  })

  it("i modi di non avere notti dicono cose diverse", async () => {
    const casi: [string, string, string | null][] = [
      ["no_folders", "Nessuna cartella scelta", "Scegli la cartella"],
      ["no_frames", "Nessun frame nelle cartelle", "Aggiungi cartelle"],
      ["no_site", "Sito mancante", "Aggiungi sito"],
      ["reading", "Scansione in corso, 19%", null],
      ["waiting", "Tutti i frame aspettano una risposta", "Apri Da confermare"],
    ]
    for (const [motivo, titolo, azione] of casi) {
      notti(pagina([], { empty: motivo, reading_done_pct: 19, waiting: [{ answer_at: "review", frames: 86 }] }))
      const reso = await apriNotti()
      expect(await screen.findByText(titolo)).toBeTruthy()
      if (azione) expect(screen.getByText(azione)).toBeTruthy()
      reso.unmount()
      pulisci()
    }
  })

  it("se le notti non si leggono lo dice, con Riprova", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/nights": { stato: 500, corpo: {} },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    await apriNotti()
    expect(await screen.findByText("Notti non disponibili")).toBeTruthy()
    expect(screen.getByText("Riprova")).toBeTruthy()
  })
})

describe("le Notti, una notte dall'indirizzo", () => {
  it("con ?notte= chiede quella notte sola e porta a tutte le altre", async () => {
    notti(pagina([DICIOTTO]))
    window.history.pushState({}, "", "/notti?notte=7")
    await disegna()
    expect(await screen.findByText("\u2190 Tutte le notti")).toBeTruthy()
    expect(chiamate().some((u) => u.includes("night=7"))).toBe(true)
    expect(screen.queryByRole("tab")).toBeNull()
  })

  it("una notte che non c'e' piu' lo dice, invece di dire che l'archivio e' vuoto", async () => {
    notti(pagina([]))
    window.history.pushState({}, "", "/notti?notte=99")
    await disegna()
    expect(await screen.findByText("Notte non trovata")).toBeTruthy()
  })
})
