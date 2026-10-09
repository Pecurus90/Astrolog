// @vitest-environment jsdom
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

/**
 * La sezione **Attrezzatura da completare** di *Da confermare*: una scheda per gruppo di file che
 * scrivono le stesse intestazioni, che chiede **solo le parti che mancano** -- la camera, l'ottica,
 * il filtro. Si risponde una parte alla volta, e la parte non toccata non si manda.
 */

const SCHEDA = {
  key: "firma-1",
  camera: null,
  telescope: "EQ6-R",
  width_px: 6248,
  height_px: 4176,
  pixel_um: 3.76,
  frames: 214,
  asks_camera: true,
  asks_optics: false,
  asks_filter: true,
  optics: "Askar FRA400",
  focal_mm: 400,
  focal_suggested: null,
  answer: null,
  complete: false,
  subjects: { found: [{ name: "NGC 7000", frames: 120 }], not_found: 0, not_yet: 0 },
}

const PAGINA = {
  to_confirm: 1,
  lookalikes: [],
  filters: [],
  filter_choices: [
    { id: 1, name: "Ha 7 nm", passband: "HA" },
    { id: 3, name: "L", passband: "L" },
  ],
  gear: [SCHEDA],
  rig_choices: [
    { id: 5, name: "Notte in quota", optics: "Askar FRA400", camera: "ZWO ASI2600MM Pro", focal_mm: 400 },
    { id: 6, name: null, optics: "Askar FRA400", camera: "ZWO ASI294MC Pro", focal_mm: 400 },
  ],
  optics_choices: ["Askar FRA400", "RedCat 51"],
  objects: [],
  settled_objects: 0,
  typeless: [],
  unclear: [],
  mosaics: [],
}

function aperta(pagina: unknown = PAGINA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 214, run_started: true } },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

async function mandate() {
  fireEvent.click(screen.getByRole("button", { name: /applica/i }))
  let corpo: { gear: unknown[] } | undefined
  await waitFor(() => {
    corpo = scritture().find((s) => s.url.includes("/api/v1/review/apply"))?.corpo as typeof corpo
    expect(corpo).toBeDefined()
  })
  return corpo?.gear
}

const applicaSpento = () => expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
const prova = (dove: HTMLElement) =>
  [...dove.querySelectorAll("dl.as-domanda-prova > div")].map(
    (r) => `${r.querySelector("dt")?.textContent}=${r.querySelector("dd")?.textContent}`,
  )
const parti = (dove: HTMLElement) =>
  [...dove.querySelectorAll(".as-domanda-parti > .as-domanda-parte")].map(
    (p) => `${p.querySelector(".as-soprattitolo")?.textContent}: ${p.querySelector(".as-risposta")?.textContent}`,
  )
const sezione = () => vaiASezione(/attrezzatura da completare/i)

describe("Da confermare -- l'attrezzatura da completare", () => {
  it("la scheda dice cosa scrivono i file, e chiede solo le parti che mancano", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    expect(prova(scheda)).toEqual([
      "Camera nel file=Non indicata",
      "Telescopio nel file=EQ6-R",
      "Sensore=6248 \u00d7 4176 px \u00b7 3,76 \u00b5m",
      "Ottica nei frame=Askar FRA400 \u00b7 400 mm",
      "Oggetti=NGC 7000 (120 frame)",
    ])
    // la camera e il filtro mancano, l'ottica no: due parti, ognuna col suo stato
    expect(parti(scheda)).toEqual(["Camera: senza risposta", "Filtro: senza risposta"])
  })

  it("senza camera e senza telescopio il titolo viene dal sensore, o da una parola fissa", async () => {
    aperta({
      ...PAGINA,
      gear: [
        { ...SCHEDA, telescope: null },
        { ...SCHEDA, key: "firma-2", telescope: null, width_px: null, height_px: null, pixel_um: null },
      ],
    })
    const dove = await sezione()
    expect(riga(dove, "6248 \u00d7 4176 px \u00b7 3,76 \u00b5m")).toBeDefined()
    expect(riga(dove, "Attrezzatura senza nome")).toBeDefined()
  })

  it("la camera si da' scegliendo un corredo, e la risposta porta solo quello", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    const camera = within(scheda).getByRole("group", { name: "Camera per EQ6-R" })
    expect(within(camera).getAllByRole("radio").map((r) => r.closest("label")?.textContent)).toEqual([
      "Notte in quotaAskar FRA400 \u00b7 ZWO ASI2600MM Pro",
      "Askar FRA400 \u00b7 ZWO ASI294MC Pro",
      "Altra camera",
    ])
    fireEvent.click(within(camera).getByRole("radio", { name: /Notte in quota/ }))
    expect(parti(scheda)).toEqual(["Camera: da applicare", "Filtro: senza risposta"])
    expect(await mandate()).toEqual([{ key: "firma-1", rig_id: 5 }])
  })

  it("la camera scritta a mano vuole la sua focale, e porta l'ottica che i frame dicono", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    fireEvent.click(within(scheda).getByRole("radio", { name: "Altra camera" }))
    // i campi arrivano con cio' che i frame dicono gia'
    expect(within(scheda).getByLabelText("Focale (mm)")).toHaveProperty("value", "400")
    expect(within(scheda).getByLabelText(/^Ottica/)).toHaveProperty("value", "Askar FRA400")
    applicaSpento()
    fireEvent.change(within(scheda).getByLabelText("Camera"), { target: { value: " QHY268M " } })
    fireEvent.change(within(scheda).getByLabelText("Focale (mm)"), { target: { value: "" } })
    // una camera senza focale non e' una risposta: il backend la rifiuterebbe
    applicaSpento()
    fireEvent.change(within(scheda).getByLabelText("Focale (mm)"), { target: { value: "382,5" } })
    expect(await mandate()).toEqual([{ key: "firma-1", camera: "QHY268M", focal_mm: 382.5, optics: "Askar FRA400" }])
  })

  it("il filtro: a colori si sceglie solo a camera data, e uno dei propri vuole dire quale", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    const filtro = within(scheda).getByRole("group", { name: "Filtro per EQ6-R" })
    const colori = within(filtro).getByRole("radio", { name: /^A colori, senza filtro/ })
    expect(colori).toHaveProperty("disabled", true)
    expect(within(filtro).getByText("Selezionabile dopo aver indicato la camera.")).toBeDefined()

    fireEvent.click(within(filtro).getByRole("radio", { name: "Filtro esistente" }))
    // senza dire quale non e' una risposta
    applicaSpento()
    fireEvent.change(within(filtro).getByLabelText("Filtro"), { target: { value: "1" } })
    expect(parti(scheda)).toEqual(["Camera: senza risposta", "Filtro: da applicare"])

    fireEvent.click(within(scheda).getByRole("radio", { name: /Notte in quota/ }))
    expect(within(filtro).getByRole("radio", { name: /^A colori, senza filtro/ })).toHaveProperty("disabled", false)
    expect(await mandate()).toEqual([{ key: "firma-1", rig_id: 5, filter: "filter", filter_id: 1 }])
  })

  it("a colori non parte se la camera torna a mancare: il backend rifiuterebbe tutto l'Applica", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    fireEvent.click(within(scheda).getByRole("radio", { name: /Notte in quota/ }))
    fireEvent.click(within(scheda).getByRole("radio", { name: /^A colori, senza filtro/ }))
    expect(parti(scheda)).toEqual(["Camera: da applicare", "Filtro: da applicare"])
    // "Altra camera" col nome vuoto non e' una camera: il filtro a colori non ha dove scriversi
    fireEvent.click(within(scheda).getByRole("radio", { name: "Altra camera" }))
    expect(parti(scheda)).toEqual(["Camera: senza risposta", "Filtro: senza risposta"])
    applicaSpento()
    fireEvent.click(within(scheda).getByRole("radio", { name: /Notte in quota/ }))
    expect(await mandate()).toEqual([{ key: "firma-1", rig_id: 5, filter: "color" }])
  })

  it("camera data e ottica ancora da dare: la scheda chiede l'ottica da sola", async () => {
    const senzaOttica = { ...SCHEDA, asks_optics: true, asks_filter: false, optics: null }
    aperta({
      ...PAGINA,
      rig_choices: [...PAGINA.rig_choices, { id: 7, name: null, optics: null, camera: "QHY268M", focal_mm: 400 }],
      gear: [
        { ...senzaOttica, answer: { camera: "QHY268M", optics: null, focal_mm: 400, filter: null, filter_id: null } },
        { ...senzaOttica, key: "firma-2", telescope: "AM5" },
      ],
    })
    const dove = await sezione()
    // finche' la camera manca l'ottica la porta lei, e li' non e' facoltativa
    const nuova = riga(dove, "AM5")
    expect(parti(nuova)).toEqual(["Camera: senza risposta"])
    fireEvent.click(within(nuova).getByRole("radio", { name: "Altra camera" }))
    expect(within(nuova).queryByText("Facoltativa.")).toBeNull()

    const scheda = riga(dove, "EQ6-R")
    expect(parti(scheda)).toEqual(["Camera: salvata", "Ottica: senza risposta"])
    fireEvent.click(within(scheda).getByRole("radio", { name: "RedCat 51" }))
    expect(await mandate()).toEqual([{ key: "firma-1", optics: "RedCat 51" }])
  })

  it("la camera rimessa com'era salvata non e' un cambio: l'ottica scelta accanto parte", async () => {
    aperta({
      ...PAGINA,
      rig_choices: [...PAGINA.rig_choices, { id: 7, name: null, optics: null, camera: "QHY268M", focal_mm: 400 }],
      gear: [
        {
          ...SCHEDA,
          asks_optics: true,
          asks_filter: false,
          optics: null,
          answer: { camera: "QHY268M", optics: null, focal_mm: 400, filter: null, filter_id: null },
        },
      ],
    })
    const scheda = riga(await sezione(), "EQ6-R")
    fireEvent.click(within(scheda).getByRole("radio", { name: /Notte in quota/ }))
    fireEvent.click(within(scheda).getByRole("radio", { name: "QHY268M" }))
    fireEvent.click(within(scheda).getByRole("radio", { name: "RedCat 51" }))
    expect(parti(scheda)).toEqual(["Camera: salvata", "Ottica: da applicare"])
    expect(await mandate()).toEqual([{ key: "firma-1", optics: "RedCat 51" }])
  })

  it("due corredi con gli stessi pezzi e focale diversa non si confondono", async () => {
    aperta({
      ...PAGINA,
      rig_choices: [...PAGINA.rig_choices, { id: 8, name: "Col riduttore", optics: "Askar FRA400", camera: "ZWO ASI2600MM Pro", focal_mm: 280 }],
      gear: [{ ...SCHEDA, answer: { camera: "ZWO ASI2600MM Pro", optics: "Askar FRA400", focal_mm: 280, filter: null, filter_id: null } }],
    })
    const scheda = riga(await sezione(), "EQ6-R")
    expect(within(scheda).getByRole("radio", { name: /Col riduttore/ })).toHaveProperty("checked", true)
    // l'altro corredo e' un cambio vero, e parte
    fireEvent.click(within(scheda).getByRole("radio", { name: /Notte in quota/ }))
    expect(await mandate()).toEqual([{ key: "firma-1", rig_id: 5 }])
  })

  it("quando manca solo l'ottica, si sceglie fra le proprie o se ne scrive il nome", async () => {
    aperta({
      ...PAGINA,
      gear: [{ ...SCHEDA, camera: "ZWO ASI2600MM Pro", asks_camera: false, asks_optics: true, asks_filter: false, optics: null, focal_mm: null }],
    })
    const scheda = riga(await sezione(), "ZWO ASI2600MM Pro")
    expect(parti(scheda)).toEqual(["Ottica: senza risposta"])
    const ottica = within(scheda).getByRole("group", { name: "Ottica per ZWO ASI2600MM Pro" })
    expect(within(ottica).getAllByRole("radio").map((r) => r.closest("label")?.textContent)).toEqual([
      "Askar FRA400",
      "RedCat 51",
      "Altra ottica",
    ])
    fireEvent.click(within(ottica).getByRole("radio", { name: "Altra ottica" }))
    applicaSpento()
    fireEvent.change(within(ottica).getByLabelText("Nome dell'ottica"), { target: { value: "Newton 200/800" } })
    expect(await mandate()).toEqual([{ key: "firma-1", optics: "Newton 200/800" }])
  })

  it("una scheda a meta' dice cosa c'e' e cosa manca, e resta fra le cose da confermare", async () => {
    aperta({
      ...PAGINA,
      gear: [
        { ...SCHEDA, answer: { camera: "ZWO ASI2600MM Pro", optics: "Askar FRA400", focal_mm: 400, filter: null, filter_id: null } },
        { ...SCHEDA, key: "firma-2", telescope: "AM5", asks_filter: false },
      ],
    })
    const dove = await sezione()
    // aperta l'altra scheda, questa si legge chiusa: una parte salvata, una da dare
    riga(dove, "AM5")
    const chiusa = [...dove.querySelectorAll<HTMLElement>(".as-domanda-riga")].find((r) => r.textContent?.startsWith("EQ6-R"))
    expect(chiusa?.querySelector(".as-domanda-riga__breve")?.textContent).toBe("Camera: ZWO ASI2600MM Pro \u00b7 Filtro: da indicare")
    expect(chiusa?.querySelector(".as-risposta")?.textContent).toBe("senza risposta")
    const scheda = riga(dove, "EQ6-R")
    expect(parti(scheda)).toEqual(["Camera: salvata", "Filtro: senza risposta"])
    expect(within(scheda).getByRole("radio", { name: /Notte in quota/ })).toHaveProperty("checked", true)
  })

  it("una scheda completa resta in pagina, salvata, per cambiare idea", async () => {
    aperta({
      ...PAGINA,
      to_confirm: 0,
      gear: [
        { ...SCHEDA, complete: true, answer: { camera: "ZWO ASI2600MM Pro", optics: "Askar FRA400", focal_mm: 400, filter: "filter", filter_id: 1 } },
      ],
    })
    const scheda = riga(await sezione(), "EQ6-R")
    expect(parti(scheda)).toEqual(["Camera: salvata", "Filtro: salvata"])
    expect(within(scheda).getByRole("radio", { name: "Filtro esistente" })).toHaveProperty("checked", true)
    expect(within(scheda).getByLabelText("Filtro")).toHaveProperty("value", "1")
    applicaSpento()
  })
})
