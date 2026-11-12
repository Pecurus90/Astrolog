// @vitest-environment jsdom
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  STANOTTE,
  daConfermare,
  domande,
  impostazioni,
  parti,
  prove,
  pulisci,
  riga,
  rispondi,
  scelta,
  scelto,
  schedaAttrezzatura,
  scritture,
  spento,
  statoDellaDomanda,
  vaiASezione,
  voci,
} from "./banco"

afterEach(pulisci)

/**
 * La sezione **Attrezzatura da completare** di *Da confermare*: una scheda per gruppo di file che
 * scrivono le stesse intestazioni, che chiede **solo le parti che mancano** -- la camera, l'ottica,
 * il filtro. Si risponde una parte alla volta, e la parte non toccata non si manda.
 */

const SCHEDA = schedaAttrezzatura({
  key: "firma-1",
  telescope: "EQ6-R",
  width_px: 6248,
  height_px: 4176,
  pixel_um: 3.76,
  frames: 214,
  asks_camera: true,
  asks_filter: true,
  optics: "Askar FRA400",
  focal_mm: 400,
  subjects: { found: [{ name: "NGC 7000", frames: 120 }], not_found: 0, not_yet: 0 },
})

const QHY = { id: 7, name: null, optics: null, camera: "QHY268M", focal_mm: 400 }

const PAGINA = daConfermare({
  to_confirm: 1,
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
})

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

const applicaSpento = () => expect(screen.getByRole("button", { name: /applica/i }).getAttribute("aria-disabled")).toBe("true")
const sezione = () => vaiASezione(/attrezzatura da completare/i)
/** Le voci del filtro della scheda: le tre parole, e se sono spente. */
const filtri = (scheda: HTMLElement) =>
  ["A colori, nessun filtro", "Nessun filtro", "Filtro esistente"].map((v) => spento(scelta(scheda, v)))

describe("Da confermare -- l'attrezzatura da completare", () => {
  it("la scheda dice cosa scrivono i file, e chiede solo le parti che mancano", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    expect(prove(scheda)).toEqual([
      "Camera nel file=Non indicata",
      "Telescopio nel file=EQ6-R",
      "Sensore=6248 × 4176 px · 3,76 µm",
      "Ottica nei frame=Askar FRA400 · 400 mm",
      "Oggetti nel campo=NGC 7000 (120 frame)",
    ])
    // la camera e il filtro mancano, l'ottica no: due parti, ognuna col suo capo e il suo stato
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: da indicare", "Filtro per EQ6-R: da indicare"])
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
    expect(riga(dove, "6248 × 4176 px · 3,76 µm")).toBeDefined()
    expect(riga(dove, "Attrezzatura senza nome")).toBeDefined()
  })

  it("la camera si da' scegliendo un setup, e la risposta porta solo quello", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    const camera = within(scheda).getByRole("radiogroup", { name: "Camera per EQ6-R" })
    expect(voci(camera)).toEqual([
      "Notte in quota / Askar FRA400 · ZWO ASI2600MM Pro",
      "Askar FRA400 · ZWO ASI294MC Pro",
      "Altra camera",
    ])
    fireEvent.click(scelta(camera, "Notte in quota"))
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: da applicare", "Filtro per EQ6-R: da indicare"])
    expect(await mandate()).toEqual([{ key: "firma-1", rig_id: 5 }])
  })

  it("la camera scritta a mano vuole la sua focale, e porta l'ottica che i frame dicono", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    fireEvent.click(scelta(scheda, "Altra camera"))
    // i campi arrivano con cio' che i frame dicono gia'; l'ottica si scrive qui, perche' la
    // scheda non la chiede a parte
    expect(within(scheda).getByLabelText("Focale (mm)")).toHaveProperty("value", "400")
    expect(within(scheda).getByLabelText("Ottica")).toHaveProperty("value", "Askar FRA400")
    applicaSpento()
    fireEvent.change(within(scheda).getByLabelText("Camera"), { target: { value: " QHY268M " } })
    fireEvent.change(within(scheda).getByLabelText("Focale (mm)"), { target: { value: "" } })
    // una camera senza focale non e' una risposta: il backend la rifiuterebbe
    applicaSpento()
    fireEvent.change(within(scheda).getByLabelText("Focale (mm)"), { target: { value: "382,5" } })
    expect(await mandate()).toEqual([{ key: "firma-1", camera: "QHY268M", focal_mm: 382.5, optics: "Askar FRA400" }])
  })

  it("il filtro si sceglie solo a camera data, e uno dei propri si sceglie fra le pillole", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    // tutte e tre spente finche' la camera non si sa, e la nota lo dice
    expect(filtri(scheda)).toEqual([true, true, true])
    expect(within(scheda).getByText("Selezionabile dopo aver indicato la camera.")).toBeDefined()
    fireEvent.click(scelta(scheda, "Filtro esistente"))
    expect(scelto(scelta(scheda, "Filtro esistente"))).toBe(false)

    fireEvent.click(scelta(scheda, "Notte in quota"))
    expect(filtri(scheda)).toEqual([false, false, false])
    expect(within(scheda).queryByText("Selezionabile dopo aver indicato la camera.")).toBeNull()
    fireEvent.click(scelta(scheda, "Filtro esistente"))
    // senza dire quale non e' una risposta
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: da applicare", "Filtro per EQ6-R: da indicare"])
    const miei = within(scheda).getByRole("radiogroup", { name: "Filtro esistente" })
    expect(voci(miei)).toEqual(["Ha 7 nm", "L"])
    fireEvent.click(scelta(miei, "Ha 7 nm"))
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: da applicare", "Filtro per EQ6-R: da applicare"])
    expect(await mandate()).toEqual([{ key: "firma-1", rig_id: 5, filter: "filter", filter_id: 1 }])
  })

  it("a colori non parte se la camera torna a mancare: il backend rifiuterebbe tutto l'Applica", async () => {
    aperta()
    const scheda = riga(await sezione(), "EQ6-R")
    fireEvent.click(scelta(scheda, "Notte in quota"))
    fireEvent.click(scelta(scheda, "A colori, nessun filtro"))
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: da applicare", "Filtro per EQ6-R: da applicare"])
    // "Altra camera" col nome vuoto non e' una camera: il filtro a colori non ha dove scriversi
    fireEvent.click(scelta(scheda, "Altra camera"))
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: da indicare", "Filtro per EQ6-R: da indicare"])
    applicaSpento()
    fireEvent.click(scelta(scheda, "Notte in quota"))
    expect(await mandate()).toEqual([{ key: "firma-1", rig_id: 5, filter: "color" }])
  })

  it("l'ottica si chiede anche quando manca la camera, e allora non sta accanto ad Altra camera", async () => {
    const senzaOttica = { ...SCHEDA, asks_optics: true, asks_filter: false, optics: null }
    aperta({
      ...PAGINA,
      rig_choices: [...PAGINA.rig_choices, QHY],
      gear: [
        { ...senzaOttica, answer: { camera: "QHY268M", optics: null, focal_mm: 400, filter: null, filter_id: null } },
        { ...senzaOttica, key: "firma-2", telescope: "AM5" },
      ],
    })
    const dove = await sezione()
    const nuova = riga(dove, "AM5")
    expect(parti(nuova)).toEqual(["Camera per AM5: da indicare", "Ottica per AM5: da indicare"])
    fireEvent.click(scelta(nuova, "Altra camera"))
    // due campi per la stessa cosa no: l'ottica si dice nella sua parte
    expect(within(nuova).queryByLabelText("Ottica")).toBeNull()
    expect(within(nuova).queryByText("Facoltativa.")).toBeNull()

    const scheda = riga(dove, "EQ6-R")
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: salvata", "Ottica per EQ6-R: da indicare"])
    fireEvent.click(scelta(scheda, "RedCat 51"))
    expect(await mandate()).toEqual([{ key: "firma-1", optics: "RedCat 51" }])
  })

  it("un setup dell'elenco e un'ottica nello stesso Applica partono per pezzi scritti", async () => {
    // Un setup dell'elenco insieme a un'ottica il backend lo rifiuta (Issue #20): parte la camera
    // del setup con la sua focale, e l'ottica scelta.
    aperta({ ...PAGINA, gear: [{ ...SCHEDA, asks_optics: true, asks_filter: false, optics: null }] })
    const scheda = riga(await sezione(), "EQ6-R")
    fireEvent.click(scelta(scheda, "Notte in quota"))
    fireEvent.click(scelta(scheda, "RedCat 51"))
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: da applicare", "Ottica per EQ6-R: da applicare"])
    expect(await mandate()).toEqual([{ key: "firma-1", camera: "ZWO ASI2600MM Pro", focal_mm: 400, optics: "RedCat 51" }])
  })

  it("un setup senza focale non porta l'ottica scelta accanto: la parte Ottica lo dice", async () => {
    const senzaFocale = PAGINA.rig_choices.map((c) => ({ ...c, focal_mm: null }))
    aperta({ ...PAGINA, rig_choices: senzaFocale, gear: [{ ...SCHEDA, asks_optics: true, asks_filter: false, optics: null }] })
    const scheda = riga(await sezione(), "EQ6-R")
    fireEvent.click(scelta(scheda, "Notte in quota"))
    fireEvent.click(scelta(scheda, "RedCat 51"))
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: da applicare", "Ottica per EQ6-R: da indicare"])
    expect(await mandate()).toEqual([{ key: "firma-1", rig_id: senzaFocale[0]?.id }])
  })

  it("la camera rimessa com'era salvata non e' un cambio: l'ottica scelta accanto parte", async () => {
    aperta({
      ...PAGINA,
      rig_choices: [...PAGINA.rig_choices, QHY],
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
    fireEvent.click(scelta(scheda, "Notte in quota"))
    fireEvent.click(scelta(scheda, "QHY268M"))
    fireEvent.click(scelta(scheda, "RedCat 51"))
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: salvata", "Ottica per EQ6-R: da applicare"])
    expect(await mandate()).toEqual([{ key: "firma-1", optics: "RedCat 51" }])
  })

  it("due setup con gli stessi pezzi e focale diversa non si confondono", async () => {
    aperta({
      ...PAGINA,
      rig_choices: [...PAGINA.rig_choices, { id: 8, name: "Col riduttore", optics: "Askar FRA400", camera: "ZWO ASI2600MM Pro", focal_mm: 280 }],
      gear: [{ ...SCHEDA, answer: { camera: "ZWO ASI2600MM Pro", optics: "Askar FRA400", focal_mm: 280, filter: null, filter_id: null } }],
    })
    const scheda = riga(await sezione(), "EQ6-R")
    expect(scelto(scelta(scheda, "Col riduttore"))).toBe(true)
    // l'altro corredo e' un cambio vero, e parte
    fireEvent.click(scelta(scheda, "Notte in quota"))
    expect(await mandate()).toEqual([{ key: "firma-1", rig_id: 5 }])
  })

  it("quando manca solo l'ottica, si sceglie fra le proprie o se ne scrive il nome", async () => {
    aperta({
      ...PAGINA,
      gear: [{ ...SCHEDA, camera: "ZWO ASI2600MM Pro", asks_camera: false, asks_optics: true, asks_filter: false, optics: null, focal_mm: null }],
    })
    const scheda = riga(await sezione(), "ZWO ASI2600MM Pro")
    expect(parti(scheda)).toEqual(["Ottica per ZWO ASI2600MM Pro: da indicare"])
    const ottica = within(scheda).getByRole("radiogroup", { name: "Ottica per ZWO ASI2600MM Pro" })
    expect(voci(ottica)).toEqual(["Askar FRA400", "RedCat 51", "Altra ottica"])
    fireEvent.click(scelta(ottica, "Altra ottica"))
    applicaSpento()
    fireEvent.change(within(scheda).getByLabelText("Nome dell'ottica"), { target: { value: "Newton 200/800" } })
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
    const chiusa = domande(dove).find((r) => r.tagName !== "ARTICLE" && r.textContent?.startsWith("EQ6-R")) as HTMLElement
    expect(chiusa.querySelector(".al-conf__blocco-9")?.textContent).toBe(
      "Camera per EQ6-R: ZWO ASI2600MM Pro · Filtro per EQ6-R: da indicare",
    )
    expect(statoDellaDomanda(chiusa)).toBe("senza risposta")
    const scheda = riga(dove, "EQ6-R")
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: salvata", "Filtro per EQ6-R: da indicare"])
    expect(scelto(scelta(scheda, "Notte in quota"))).toBe(true)
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
    expect(parti(scheda)).toEqual(["Camera per EQ6-R: salvata", "Filtro per EQ6-R: salvata"])
    expect(scelto(scelta(scheda, "Filtro esistente"))).toBe(true)
    expect(scelto(scelta(scheda, "Ha 7 nm"))).toBe(true)
    applicaSpento()
  })
})
