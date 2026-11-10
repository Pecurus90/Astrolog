// @vitest-environment jsdom
/**
 * La **finestra dell'oggetto** (`src/TuttoDellOggetto.tsx`, tavola v76 `Riepilogo` tipo oggetto):
 * il tocco su una carta o sul nome nell'elenco la apre sopra l'Archivio. Scrive cio' che manda
 * `GET /api/v1/objects/{key}`: la testa, le produzioni una alla volta, i setup, il catalogo, le
 * notti.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { t } from "../src/i18n"
import { type Voce, chiamate, pulisci, rispondi } from "./banco"
import {
  IGNOTO,
  M31,
  MOSAICO,
  apriArchivio,
  conArchivio,
  vaiAll,
  voceArchivio,
} from "./archivio-banco"
import { DICIASSETTE, DICIOTTO } from "./notti-banco"

afterEach(pulisci)

const FATTI = {
  key: "m-31",
  common_name: "Galassia di Andromeda",
  type_code: "GALAXY",
  constellation: "And",
  distance: { value: 2.5, unit: "million_ly" },
  extent_ly: 220000,
  distance_pc: null,
  size_arcmin: 190,
  moon: { compare: "more", moons: 6 },
}

const VICINA = { ...FATTI, distance: { value: 2400, unit: "ly" }, distance_pc: 740 }

const FUORI = {
  key: "NGC 7000",
  common_name: null,
  type_code: null,
  constellation: null,
  distance: null,
  extent_ly: null,
  distance_pc: null,
  size_arcmin: null,
  moon: null,
}

function scheda(row: unknown, extra: Record<string, unknown> = {}) {
  return {
    row,
    nights: [
      { night: DICIASSETTE, frames: 20, integration_s: 0, untimed: 20 },
      { night: DICIOTTO, frames: 100, integration_s: 36000, untimed: 0 },
    ],
    first_night: "2024-05-17",
    last_night: "2024-05-18",
    sites: ["Casa", "Cima Ekar"],
    rigs: [],
    facts: FATTI,
    ...extra,
  }
}

const stat = (key: string, median: number | null) => ({
  key,
  unit: "px",
  group: "stars_shape",
  measured: median === null ? 0 : 2,
  median,
  q1: median === null ? null : median - 0.2,
  q3: median === null ? null : median + 0.2,
  low: median === null ? null : median - 0.5,
  high: median === null ? null : median + 0.5,
  trend: null,
  verdict: null,
  silent: median === null ? "no_value" : null,
  per_filter: false,
})

const insieme = (group: string | null, fwhm: number, snr = 40) => ({
  group,
  filter: null,
  frames: 2,
  pending: 0,
  differs: [],
  measures: [stat("fwhm_arcsec", fwhm), stat("fwhm_px", fwhm / 2), stat("snr", snr)],
})

/** Le misure dell'oggetto: i gruppi sono le sue due notti. */
function misure(extra: Record<string, unknown> = {}) {
  return {
    key: "m-31",
    frames: 4,
    pending: 0,
    one_production: true,
    groups: [
      { key: "6", name: null, night_date: "2024-05-17", frames: 2, pending: 0 },
      { key: "7", name: null, night_date: "2024-05-18", frames: 2, pending: 0 },
    ],
    filters: [],
    sets: [insieme(null, 2.5), insieme("6", 2.2, 30), insieme("7", 2.8, 50)],
    series: [],
    ...extra,
  }
}

// Il banco risponde per pezzo d'indirizzo: le misure prima, o `/objects/m-31` le prenderebbe.
async function apriCon(righe: unknown[], oggetti: Record<string, Voce>, mis = misure()) {
  const percorsi = new Set(Object.keys(oggetti).map((r) => r.split("?")[0] ?? r))
  const delleMisure = Object.fromEntries(
    [...percorsi].map((p) => [`${p}/measures`, { stato: 200, corpo: mis }]),
  )
  rispondi({ ...delleMisure, ...oggetti, ...conArchivio(voceArchivio(righe)) })
  await apriArchivio()
}

const finestra = () => screen.findByRole("dialog")

describe("la finestra dell'oggetto", () => {
  it("il tocco sulla carta la apre: nome, nome comune, periodo, siti, ore e frame", async () => {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const f = await finestra()
    expect(f.getAttribute("aria-label")).toBe("Riepilogo: M 31")
    expect(await within(f).findByText("Galassia di Andromeda")).toBeDefined()
    expect(within(f).getByText("dal 17 al 18 maggio 2024 · 2 notti, 2 siti")).toBeDefined()
    const siti = [...f.querySelectorAll(".al-c-riepilogo__pillola-1")].map((p) => p.textContent)
    expect(siti).toEqual(["Casa", "Cima Ekar"])
    expect(within(f).getByText("12 h")).toBeDefined()
    expect(within(f).getByText("120 frame")).toBeDefined()
  })

  it("in cielo dice tipo, costellazione, distanza e quanto e' grande accanto alla Luna piena", async () => {
    await apriCon([M31], {
      "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31, { facts: VICINA }) },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const cielo = await within(await finestra()).findByRole("region", { name: "In cielo" })
    expect(cielo.textContent).toMatch(/Andromeda/)
    expect(within(cielo).getByText("Galassia")).toBeDefined()
    expect(within(cielo).getByText("2400 anni luce")).toBeDefined()
    expect(within(cielo).getByText("circa 740 parsec")).toBeDefined()
    expect(within(cielo).getByText("190′ in cielo, più di 6 Lune piene")).toBeDefined()
  })

  it("due siti la stessa notte: una data, due notti; poco piu' di una Luna al singolare", async () => {
    const stessa = { ...DICIOTTO, id: 8, site: "Casa" }
    await apriCon([M31], {
      "/api/v1/objects/m-31": {
        stato: 200,
        corpo: scheda(M31, {
          nights: [
            { night: DICIOTTO, frames: 50, integration_s: 18000, untimed: 0 },
            { night: stessa, frames: 70, integration_s: 25200, untimed: 0 },
          ],
          first_night: "2024-05-18",
          last_night: "2024-05-18",
          facts: { ...VICINA, size_arcmin: 50, moon: { compare: "more", moons: 1 } },
        }),
      },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const f = await finestra()
    expect(await within(f).findByText("il 18 maggio 2024 · 2 notti, 2 siti")).toBeDefined()
    expect(within(f).getByText("50′ in cielo, più di una Luna piena")).toBeDefined()
  })

  it("un oggetto fuori catalogo lo dice, senza inventare tipo e costellazione", async () => {
    await apriCon([IGNOTO], {
      "/api/v1/objects/NGC%207000": {
        stato: 200,
        corpo: scheda(IGNOTO, { facts: FUORI }),
      },
    })
    fireEvent.click(
      within(await screen.findByRole("article")).getByRole("link", { name: "NGC 7000" }),
    )

    const f = await finestra()
    expect(await within(f).findByText("fuori catalogo")).toBeDefined()
    expect(within(f).getByText("Tipo non disponibile")).toBeDefined()
    expect(within(f).getByText("Costellazione non disponibile")).toBeDefined()
    expect(within(f).getByText("Filtri non indicati")).toBeDefined()
  })

  it("le notti portano alla loro pagina, con le ore dell'oggetto e il cielo della notte", async () => {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const notti = await within(await finestra()).findByRole("region", { name: "Le notti" })
    const sabato = within(notti).getByRole("link", {
      name: "Apri la notte di Sabato 18 maggio 2024",
    })
    expect(sabato.getAttribute("href")).toBe("/notti?notte=7")
    expect(sabato.textContent).toMatch(/10 h/)
    expect(sabato.textContent).toMatch(/100 frame/)
    expect(sabato.textContent).toMatch(/69%/)
    // solo il disco e la percentuale: il nome della fase non ci sta nella colonna (tavola 64)
    expect(sabato.querySelector(".al-c-luna__colonna-1")).toBeNull()
    const venerdi = within(notti).getByRole("link", { name: /Venerdì 17 maggio 2024/ })
    expect(venerdi.textContent).toMatch(/senza durata/)
  })

  it("con piu' produzioni le mostra una alla volta, e la scelta la chiede all'API", async () => {
    const due = {
      ...M31,
      productions: [
        { ...M31.productions[0], optics_id: 2, camera_id: 1 },
        { ...M31.productions[0], optics: null, optics_id: null, camera: "ASI533", camera_id: 5 },
      ],
    }
    await apriCon([due], {
      "/api/v1/objects/m-31?production=none": {
        stato: 200,
        corpo: scheda(due, { sites: ["Casa"] }),
      },
      "/api/v1/objects/m-31": { stato: 200, corpo: scheda(due) },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const f = await finestra()
    const schede = await within(f).findAllByRole("tab")
    expect(schede.map((s) => s.getAttribute("aria-selected"))).toEqual(["true", "false"])
    expect(chiamate().some((u) => u.includes("production=2%3A1"))).toBe(true)
    expect(schede[1]?.textContent).toMatch(/ottica non indicata.*ASI533/)

    fireEvent.click(schede[1] as HTMLElement)
    expect(chiamate().some((u) => u.includes("production=none%3A5"))).toBe(true)
  })

  it("un mosaico ha le linguette dei pannelli, e il pannello scelto lo chiede all'API", async () => {
    const chiave = encodeURIComponent(MOSAICO.key)
    const pannello = { ...MOSAICO, frames: 20, panel_list: [MOSAICO.panel_list[3]] }
    await apriCon([MOSAICO], {
      [`/api/v1/objects/${chiave}?panel=14`]: {
        stato: 200,
        corpo: scheda(pannello, { facts: FUORI }),
      },
      // l'API restringe panel_list al solo pannello chiesto
      [`/api/v1/objects/${chiave}?panel=12`]: {
        stato: 200,
        corpo: scheda({ ...MOSAICO, panel_list: [MOSAICO.panel_list[1]] }),
      },
      [`/api/v1/objects/${chiave}`]: { stato: 200, corpo: scheda(MOSAICO) },
    })
    fireEvent.click(
      within(await screen.findByRole("article")).getByRole("link", { name: "IC 405" }),
    )

    const f = await finestra()
    const gruppo = await within(f).findByRole("tablist", { name: "mosaico" })
    const schede = within(gruppo).getAllByRole("tab")
    expect(schede.map((s) => s.textContent)).toEqual([
      "Riepilogo generale4 pannelli",
      "Pannello 1IC 405",
      "Pannello 2LBN 796, Sh2 230",
      "Pannello 3LDN 1516",
      "Pannello 4nessun oggetto",
    ])
    expect(schede[0]?.getAttribute("aria-selected")).toBe("true")
    expect(chiamate().some((u) => u.includes("panel="))).toBe(false)

    fireEvent.click(schede[4] as HTMLElement)
    expect(await within(f).findByText("pannello 4, senza oggetti in catalogo")).toBeDefined()
    expect(chiamate().some((u) => u.includes("objects/") && u.includes("measures?panel=14"))).toBe(
      true,
    )
    // le linguette restano tutte: vengono dal mosaico intero, non dal pannello
    expect(within(f).getAllByRole("tab")).toHaveLength(5)

    fireEvent.click(within(f).getAllByRole("tab")[2] as HTMLElement)
    expect(await within(f).findByText("pannello 2: LBN 796, Sh2 230")).toBeDefined()
  })

  it("una produzione sola non ha linguette", async () => {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))
    const f = await finestra()
    await within(f).findByText("Galassia di Andromeda")
    expect(within(f).queryByRole("tab")).toBeNull()
  })

  it("un oggetto che non c'e' piu' lo dice", async () => {
    await apriCon([M31], {
      "/api/v1/objects/m-31": { stato: 404, corpo: { detail: "object_not_found" } },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))
    expect(await within(await finestra()).findByText("Oggetto non trovato")).toBeDefined()
  })

  it("le frecce vanno all'oggetto prima e dopo nell'ordine della pagina, Esc chiude", async () => {
    await apriCon([M31, IGNOTO], {
      "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) },
      "/api/v1/objects/NGC%207000": { stato: 200, corpo: scheda(IGNOTO, { facts: FUORI }) },
    })
    const [prima] = await screen.findAllByRole("article")
    fireEvent.click(within(prima as HTMLElement).getByRole("link", { name: "M 31" }))

    let f = await finestra()
    expect(
      within(f).getByRole("link", { name: "L’oggetto prima" }).getAttribute("aria-disabled"),
    ).toBe("true")
    fireEvent.click(within(f).getByRole("link", { name: "L’oggetto dopo" }))
    f = await finestra()
    expect(f.getAttribute("aria-label")).toBe("Riepilogo: NGC 7000")

    fireEvent.keyDown(f, { key: "Escape" })
    expect(screen.queryByRole("dialog")).toBeNull()
  })

  it("nell'elenco il nome apre la stessa finestra", async () => {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } })
    await vaiAll(/elenco/i)
    fireEvent.click(await screen.findByRole("link", { name: "M 31" }))
    expect((await finestra()).getAttribute("aria-label")).toBe("Riepilogo: M 31")
  })
})

describe("le misure dell'oggetto", () => {
  it("il frame scelto dice la sua notte, e l'SNR si confronta anche nell'oggetto", async () => {
    const frame = {
      frame_id: 1,
      start: "2024-05-17T23:00:00+02:00",
      group: "6",
      filter: "__no_filter__",
      state: "measured",
      tilt_level: null,
      sampling: null,
      angle_axis: null,
      values: { fwhm_px: 1.2, hfd_px: 1.6, stars: 900, snr: 33 },
    }
    await apriCon(
      [M31],
      { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } },
      misure({ series: [frame] }),
    )
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const f = await finestra()
    const scelto = await within(f).findByRole("region", { name: "Il frame" })
    expect(scelto.textContent).toMatch(/Venerdì 17 maggio/)
    expect(within(scelto).getByText("si confronta nella notte e nell'oggetto")).toBeDefined()
  })

  it("i gruppi sono le notti, con l'esito accanto; FWHM e SNR in testa", async () => {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const f = await finestra()
    const confronto = await within(f).findByRole("region", { name: "Le notti a confronto" })
    const righe = within(confronto).getAllByRole("link")
    expect(righe.map((r) => r.querySelector(".al-c-misure-frame__testo-15")?.textContent)).toEqual([
      "Venerdì 17 maggio",
      "Sabato 18 maggio",
    ])
    expect(righe[0]?.querySelector(".al-pillola")).not.toBeNull()
    expect(within(f).getByText("2,5″")).toBeDefined()
    expect(within(f).getByText("SNR mediano")).toBeDefined()
  })

  it("con piu' produzioni insieme ne' SNR ne' pixel in testa (ADR 0022)", async () => {
    const senzaScala = {
      ...misure({ one_production: false }),
      sets: [
        {
          ...insieme(null, 2.5),
          measures: [stat("fwhm_arcsec", null), stat("fwhm_px", 1.3), stat("snr", 40)],
        },
      ],
    }
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } }, senzaScala)
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const f = await finestra()
    const etichetta = await within(f).findByText("FWHM mediana")
    const testa = etichetta.closest("section") as HTMLElement
    expect(within(testa).queryByText("SNR mediano")).toBeNull()
    expect(within(testa).queryByText("1,3 px")).toBeNull()
  })
})

describe("la finestra dell'oggetto, quando i dati sono pochi", () => {
  async function apriM31(corpo: unknown, mis?: unknown) {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo } }, mis as never)
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))
    return finestra()
  }

  it("una notte sola in un sito: la sua data, senza i siti", async () => {
    const f = await apriM31(
      scheda(M31, {
        nights: [{ night: DICIOTTO, frames: 100, integration_s: 36000, untimed: 0 }],
        first_night: "2024-05-18",
        last_night: "2024-05-18",
        sites: ["Cima Ekar"],
      }),
    )
    expect(
      await within(f).findByText(t("object.period.one", { data: "18 maggio 2024" })),
    ).toBeDefined()
  })

  it("senza notti nessun periodo", async () => {
    const f = await apriM31(scheda(M31, { nights: [], first_night: null, last_night: null }))
    const testa = await within(f).findByRole("region", { name: t("window.summary") })
    expect(testa.querySelector(".al-c-riepilogo__testo-4")?.textContent).toBe("")
  })

  it("pose senza durata: le ore e quanti frame non le dicono; senza ore, solo i frame", async () => {
    const parte = { ...M31, untimed: 12 }
    const f = await apriM31(scheda(parte))
    expect(
      await within(f).findByText(t("object.untimed", { frame: "120 frame", n: "12" })),
    ).toBeDefined()
    pulisci()
    const nessuna = { ...M31, integration_s: 0, untimed: 120 }
    const g = await apriM31(scheda(nessuna))
    const testa = await within(g).findByRole("region", { name: t("window.summary") })
    expect(within(testa).getByText("120 frame")).toBeDefined()
    expect(within(testa).getByText(t("window.untimed"))).toBeDefined()
  })

  it("nel catalogo senza tipo ne' costellazione: le lineette; poco piu' piccolo della Luna", async () => {
    const facts = {
      ...FATTI,
      common_name: null,
      type_code: null,
      constellation: null,
      size_arcmin: 7.25,
      moon: { compare: "less", moons: null },
    }
    const f = await apriM31(scheda(M31, { facts }))
    const cielo = await within(f).findByRole("region", { name: t("object.sky") })
    expect(within(cielo).getAllByText("—")).toHaveLength(2)
    expect(
      within(cielo).getByText(t("object.size", { n: "7,3", luna: t("object.moon.less") })),
    ).toBeDefined()
    // nel catalogo e senza nome comune: niente "fuori catalogo"
    expect(within(f).queryByText(t("object.outside"))).toBeNull()
  })

  it("grande come la Luna piena, in primi interi; senza Luna nessun confronto", async () => {
    const come = { ...FATTI, size_arcmin: 31.4, moon: { compare: "like", moons: 1 } }
    const f = await apriM31(scheda(M31, { facts: come }))
    const cielo = await within(f).findByRole("region", { name: t("object.sky") })
    expect(
      within(cielo).getByText(t("object.size", { n: "31", luna: t("object.moon.like") })),
    ).toBeDefined()
    pulisci()
    const senza = { ...FATTI, moon: null, distance_pc: null }
    const g = await apriM31(scheda(M31, { facts: senza }))
    const altro = await within(g).findByRole("region", { name: t("object.sky") })
    expect(altro.textContent).not.toContain("in cielo,")
    expect(altro.textContent).not.toContain("parsec")
  })

  it("le misure che non arrivano lo dicono, col bottone per riprovare", async () => {
    await apriCon([M31], {
      "/api/v1/objects/m-31/measures": { stato: 500, corpo: { detail: "boom" } },
      "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))
    const f = await finestra()
    expect(await within(f).findByText(t("window.failed"))).toBeDefined()
    expect(within(f).getByRole("button", { name: t("window.retry") })).toBeDefined()
  })

  it("quando l'oggetto non c'e' piu', la x chiude lo stesso (v77)", async () => {
    await apriCon([M31], {
      "/api/v1/objects/m-31": { stato: 404, corpo: { detail: "gone" } },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))
    const f = await finestra()
    await within(f).findByText(t("object.gone"))
    fireEvent.click(within(f).getByRole("link", { name: t("ui.close") }))
    expect(screen.queryByRole("dialog")).toBeNull()
  })

  it("una produzione senza ore e senza camera lo dice nella sua linguetta", async () => {
    const due = {
      ...M31,
      productions: [
        { ...M31.productions[0], optics_id: 2, camera_id: 1 },
        {
          ...M31.productions[0],
          camera: null,
          camera_id: null,
          optics_id: 3,
          integration_s: 0,
          frames: 7,
        },
      ],
    }
    await apriCon([due], {
      "/api/v1/objects/m-31?production=2%3A1": { stato: 200, corpo: scheda(due) },
      "/api/v1/objects/m-31": { stato: 200, corpo: scheda(due) },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))
    const schede = await within(await finestra()).findAllByRole("tab")
    // v77: optics and camera in the title, the hours (here the frames) below
    expect(schede[1]?.textContent).toBe(
      `${t("object.production.title", { ottica: "Rifrattore", camera: t("gear.rig.noCamera") })}7 frame`,
    )
    expect(
      within(await finestra()).getByRole("tablist", { name: t("object.productions") }),
    ).toBeDefined()
  })

  it("le notti dell'oggetto col suo nome", async () => {
    const f = await apriM31(scheda(M31))
    const notti = await within(f).findByRole("region", { name: t("object.nights") })
    expect(within(notti).getByText(t("object.nights.sub", { nome: "M 31" }))).toBeDefined()
  })
})
