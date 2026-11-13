// @vitest-environment jsdom
/**
 * La **carta del setup** in testa al dettaglio (`src/DettaglioSetup.tsx`, tavola v82): nome e
 * coppia, ore o conteggio, le pastiglie di focale rapporto e montatura, ottica e camera con le
 * prime voci della loro scheda, e Rinomina.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  CORREDO,
  NUMERI,
  OTTICA,
  apriAttrezzatura,
  attrezzatura,
  carta,
  parte,
} from "./attrezzatura-banco"
import { pulisci, scritture } from "./banco"

afterEach(pulisci)

const montatura = (id: number, name: string, chosen: boolean) => ({
  kind: "mount",
  id,
  name,
  frames: 3,
  chosen,
})
const pastiglie = (c: HTMLElement) =>
  [...c.querySelectorAll(".al-attr__riga-18")].map((x) => x.textContent)
const chi = (c: HTMLElement) =>
  [...c.querySelectorAll(".al-attr__colonna-9")].map((x) => x.textContent)

describe("la carta del setup", () => {
  it("un nome tuo con la coppia sotto, le ore, focale rapporto e montatura", async () => {
    attrezzatura({
      rigs: [
        {
          ...CORREDO,
          numbers: NUMERI,
          parts: [montatura(2, "AM5", false), montatura(3, "EQ6-R", true)],
        },
      ],
    })
    await apriAttrezzatura()

    const c = await carta()
    expect(within(c).getByRole("heading", { level: 2 }).textContent).toBe("Il grande")
    expect(c.querySelector(".al-attr__testo-9")?.textContent).toBe("TS 130 APO · ASI2600MM")
    expect(c.querySelector(".al-attr__testo-10")?.textContent).toBe("10 h")
    // la montatura che hai scelto, non quella con piu' frame
    expect(pastiglie(c)).toEqual(["910 mm", "f/7(calcolato)", "su EQ6-R"])
  })

  it("senza montatura scelta, quella che i file nominano per prima", async () => {
    attrezzatura({
      rigs: [{ ...CORREDO, parts: [montatura(2, "AM5", false), montatura(3, "EQ6-R", false)] }],
    })
    await apriAttrezzatura()
    expect(pastiglie(await carta())).toEqual(["910 mm", "su AM5"])
  })

  it("una scelta che non e' una montatura non conta come montatura", async () => {
    const riduttore = { kind: "reducer", id: 4, name: "Riduttore 0,8", frames: 3, chosen: true }
    attrezzatura({ rigs: [{ ...CORREDO, parts: [riduttore, montatura(2, "AM5", false)] }] })
    await apriAttrezzatura()
    expect(pastiglie(await carta())).toEqual(["910 mm", "su AM5"])
  })

  it("senza focale, rapporto ne' montatura, nessuna pastiglia", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, focal_mm: null }] })
    await apriAttrezzatura()
    expect(pastiglie(await carta())).toEqual([])
  })

  it("senza nome tuo il titolo e' la coppia, e non si ripete sotto", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, name: null }] })
    await apriAttrezzatura()
    const c = await carta(/TS 130 APO · ASI2600MM/)
    expect(c.querySelector(".al-attr__testo-9")).toBeNull()
  })

  it("non ancora contato, o senza ore, dice che conta", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, counted: false }] })
    await apriAttrezzatura()
    expect((await carta()).querySelector(".al-attr__riga-16")?.textContent).toBe(
      "conteggio in corso",
    )
    pulisci()

    attrezzatura({ rigs: [{ ...CORREDO, integration_s: null }] })
    await apriAttrezzatura()
    const c = await carta()
    expect(c.querySelector(".al-attr__testo-10")).toBeNull()
    expect(c.textContent).toContain("conteggio in corso")
  })

  it("ottica e camera col loro tipo, e le prime voci della scheda del pezzo trovato", async () => {
    attrezzatura({
      instruments: [
        OTTICA,
        { ...OTTICA, id: 9, kind: "camera", name: "ASI2600MM", aperture_mm: null, focal_mm: null },
      ],
    })
    await apriAttrezzatura()
    // la camera del setup e' camera_id null: nessun pezzo, nessuna voce
    expect(chi(await carta())).toEqual([
      "otticaTS 130 APOapertura 130 mm · focale 910 mm",
      "cameraASI2600MM",
    ])
  })

  it("una camera trovata ha le sue voci; una senza voci non ne scrive", async () => {
    const camera = {
      ...OTTICA,
      id: 9,
      kind: "camera",
      name: "ASI2600MM",
      aperture_mm: null,
      focal_mm: null,
    }
    attrezzatura({
      instruments: [
        { ...OTTICA, aperture_mm: null, focal_mm: null },
        { ...camera, pixel_size_um: 3.76 },
      ],
      rigs: [{ ...CORREDO, camera_id: 9 }],
    })
    await apriAttrezzatura()
    const c = await carta()
    expect(chi(c)).toEqual(["otticaTS 130 APO", "cameraASI2600MMpixel 3,76 µm"])
    expect(c.querySelectorAll(".al-attr__testo-14")).toHaveLength(1)
  })

  it("ottica e camera non indicate", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, optics: null, camera: null, optics_id: null }] })
    await apriAttrezzatura()
    expect(chi(await carta())).toEqual(["otticaottica non indicata", "cameracamera non indicata"])
  })

  it("Rinomina apre e chiude il modulo, e dice se e' aperto", async () => {
    attrezzatura()
    await apriAttrezzatura()
    const bottone = within(await carta()).getByRole("button", { name: "Rinomina Il grande" })
    expect(bottone.textContent).toBe("Rinomina")
    expect(bottone.getAttribute("aria-expanded")).toBe("false")
    fireEvent.click(bottone)
    expect(bottone.getAttribute("aria-expanded")).toBe("true")
    const casella = screen.getByRole("textbox", { name: /^nome/i })
    expect(casella).toHaveProperty("value", "Il grande")
    expect(casella.getAttribute("spellcheck")).toBe("false")
    fireEvent.click(bottone)
    expect(screen.queryByRole("textbox", { name: /^nome/i })).toBeNull()
  })

  it("aperto Rinomina, le parti restano chiuse; aperta una parte, Rinomina si chiude", async () => {
    attrezzatura()
    await apriAttrezzatura()
    fireEvent.click(within(await carta()).getByRole("button", { name: "Rinomina Il grande" }))
    expect(screen.queryByRole("group", { name: /^montatura di/i })).toBeNull()
    fireEvent.click(
      within(await parte("mount")).getByRole("button", { name: /^seleziona montatura$/i }),
    )
    expect(screen.queryByRole("textbox", { name: /^nome/i })).toBeNull()
    expect(screen.getByRole("group", { name: /^montatura di/i })).toBeTruthy()
  })

  it("il nome si salva senza spazi ai lati; solo spazi non salva", async () => {
    attrezzatura(
      {},
      {
        "PATCH /api/v1/gear/rigs/10": {
          stato: 200,
          corpo: { id: 10, requeued: 0, run_started: false },
        },
      },
    )
    await apriAttrezzatura()
    fireEvent.click(within(await carta()).getByRole("button", { name: "Rinomina Il grande" }))
    const casella = screen.getByRole("textbox", { name: /^nome/i })
    fireEvent.change(casella, { target: { value: "   " } })
    expect(screen.getByRole("button", { name: /salva/i }).getAttribute("aria-disabled")).toBe(
      "true",
    )
    expect(screen.getByText("Per salvare serve il nome.")).toBeTruthy()
    fireEvent.change(casella, { target: { value: "  Il piccolo  " } })
    expect(screen.queryByText("Per salvare serve il nome.")).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ name: "Il piccolo" })
    await waitFor(() => expect(screen.queryByRole("textbox", { name: /^nome/i })).toBeNull())
  })

  it("un rifiuto lascia il modulo aperto e lo dice", async () => {
    attrezzatura(
      {},
      { "PATCH /api/v1/gear/rigs/10": { stato: 409, corpo: { detail: { code: "name_taken" } } } },
    )
    await apriAttrezzatura()
    fireEvent.click(within(await carta()).getByRole("button", { name: "Rinomina Il grande" }))
    fireEvent.change(screen.getByRole("textbox", { name: /^nome/i }), {
      target: { value: "Altro" },
    })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    expect(await screen.findByRole("alert")).toBeTruthy()
    expect(screen.getByRole("textbox", { name: /^nome/i })).toBeTruthy()
  })
})
