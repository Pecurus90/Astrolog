/**
 * Le parole del **dettaglio del setup** (`src/vociDellaScheda.ts`, `src/contiDelSetup.ts`): ogni
 * campo del pezzo e ogni conto del setup diventa la frase esatta della tavola v82, e un campo
 * assente non scrive niente.
 */
import { describe, expect, it } from "vitest"

import type { components } from "../src/api/schema"
import { contiDelSetup, mancanza } from "../src/contiDelSetup"
import { inBreve, vociDellaScheda } from "../src/vociDellaScheda"
import { CORREDO, NUMERI, OTTICA } from "./attrezzatura-banco"

type Pezzo = components["schemas"]["InstrumentOnPage"]
type Corredo = components["schemas"]["RigOnPage"]
type Conti = components["schemas"]["RigNumbers"]

const pezzo = (campi: Record<string, unknown> = {}) =>
  ({ ...OTTICA, aperture_mm: null, focal_mm: null, ...campi }) as unknown as Pezzo
const voci = (campi: Record<string, unknown> = {}) => vociDellaScheda(pezzo(campi))
const testi = (campi: Record<string, unknown> = {}) => voci(campi).map((x) => x.v)

describe("la scheda di un pezzo", () => {
  it("un pezzo senza campi non scrive niente", () => {
    expect(voci()).toEqual([])
  })

  it("ogni campo dichiarato con le sue parole, non calcolato", () => {
    expect(
      voci({
        optical_design: "refractor",
        sensor: "IMX571",
        aperture_mm: 130,
        focal_mm: 910,
        image_circle_mm: 44.5,
        width_px: 600,
        height_px: 400,
        camera_type: "mono",
        pixel_size_um: 3.76,
        adc_bits: 16,
        payload_kg: 20,
        payload_no_cw_kg: 12.5,
        slots: 7,
        step_um: 4.25,
        total_steps: 900,
        thickness_mm: 16.5,
        prism_mm: 8,
        weight_kg: 5.75,
      }),
    ).toEqual(
      [
        "rifrattore",
        "sensore IMX571",
        "apertura 130 mm",
        "focale 910 mm",
        "cerchio d'immagine 44,50 mm",
        "600 × 400 px",
        "monocromatica",
        "pixel 3,76 µm",
        "16 bit",
        "carico 20 kg con contrappeso",
        "12,50 kg senza",
        "7 posizioni",
        "passo 4,25 µm",
        "900 passi",
        "spessore 16,50 mm",
        "prisma 8 mm",
        "peso 5,75 kg",
      ].map((v) => ({ v, calc: false })),
    )
  })

  it("lo zero e' un valore, non un campo vuoto", () => {
    expect(testi({ aperture_mm: 0, weight_kg: 0, slots: 0 })).toEqual([
      "apertura 0 mm",
      "0 posizioni",
      "peso 0 kg",
    ])
  })

  it("le voci ricavate dall'API sono calcolate", () => {
    expect(
      voci({
        numbers: { dawes: { value: 0.89 }, sensor_size: { width: 23.5, height: 15.7 } },
        pixel_from_sky_um: 3.8,
      }),
    ).toEqual([
      { v: "potere risolutore 0,89″", calc: true },
      { v: "pixel 3,80 µm", calc: true },
      { v: "23,5 × 15,7 mm", calc: true },
    ])
  })

  it("il pixel dichiarato vince su quello dal cielo", () => {
    expect(voci({ pixel_size_um: 3.76, pixel_from_sky_um: 3.8 })).toEqual([
      { v: "pixel 3,76 µm", calc: false },
    ])
  })

  it("una dimensione sola, del sensore o in pixel, non si scrive", () => {
    expect(testi({ width_px: 600 })).toEqual([])
    expect(testi({ height_px: 400 })).toEqual([])
    expect(testi({ numbers: { sensor_size: { width: 23.5, height: null } } })).toEqual([])
    expect(testi({ numbers: { sensor_size: { width: null, height: 15.7 } } })).toEqual([])
  })

  it("il backfocus con e senza tolleranza", () => {
    expect(testi({ required_backfocus_mm: 55 })).toEqual(["backfocus 55 mm"])
    expect(testi({ required_backfocus_mm: 55, backfocus_tolerance_mm: 0.5 })).toEqual([
      "backfocus 55 mm ± 0,50",
    ])
  })

  it("la camera a colori e quella raffreddata", () => {
    expect(testi({ camera_type: "color" })).toEqual(["a colori"])
    expect(testi({ cooled: true })).toEqual(["raffreddata"])
    expect(testi({ cooled: true, cooling_c: 35 })).toEqual(["raffreddata, 35 °C sotto l'ambiente"])
    expect(testi({ cooled: false, cooling_c: 35 })).toEqual([])
  })

  it("la misura dei filtri, sola o della ruota", () => {
    expect(testi({ filter_size: "2in" })).toEqual(["2″"])
    expect(testi({ kind: "filter_wheel", filter_size: "36mm" })).toEqual(["filtri da 36 mm"])
  })

  it("il fattore: sopra 1 e' una barlow, fino a 1 un riduttore", () => {
    expect(testi({ reducer_factor: 2 })).toEqual(["barlow 2×"])
    expect(testi({ reducer_factor: 1 })).toEqual(["riduzione 1×"])
    expect(testi({ reducer_factor: 0.8 })).toEqual(["riduzione 0,80×"])
  })

  it("in breve: le prime tre voci, mai il peso", () => {
    const p = { aperture_mm: 130, focal_mm: 910, weight_kg: 5.75 }
    expect(inBreve(pezzo(p))).toBe("apertura 130 mm · focale 910 mm")
    const tante = { ...p, sensor: "IMX571", adc_bits: 16, slots: 7 }
    expect(inBreve(pezzo(tante))).toBe("sensore IMX571 · apertura 130 mm · focale 910 mm")
    expect(inBreve(pezzo())).toBe("")
  })
})

const corredo = (campi: Record<string, unknown> = {}) =>
  ({ ...CORREDO, ...campi }) as unknown as Corredo
const conti = (campi: Record<string, unknown> = {}) => ({ ...NUMERI, ...campi }) as unknown as Conti
const conto = (chiave: keyof Conti, campi: Record<string, unknown>, r = corredo()) =>
  contiDelSetup(r, conti({ [chiave]: { missing: null, ...campi } })).find(
    (c) => c.chiave === chiave,
  )

describe("i dati del setup", () => {
  it("nove righe nell'ordine della tavola, coi nomi e cio' che manca", () => {
    expect(contiDelSetup(corredo(), conti())).toEqual([
      {
        chiave: "focal_ratio",
        l: "Rapporto focale",
        v: "f/7",
        sub: "focale effettiva 910 mm",
        esito: null,
        pillola: "",
        manca: "",
      },
      {
        chiave: "sampling",
        l: "Campionamento",
        v: "0,85″/px",
        sub: "sul cielo 0,85″/px · ottimo con seeing fra 1,7 e 2,4″; il giudizio della notte sta in Meteo",
        esito: null,
        pillola: "",
        manca: "",
      },
      {
        chiave: "field",
        l: "Campo previsto",
        v: expect.stringContaining("4,4"),
        sub: "sul cielo 1,50° × 1°",
        esito: null,
        pillola: "",
        manca: "",
      },
      {
        chiave: "sensor_size",
        l: "Dimensione del sensore",
        v: "",
        sub: "",
        esito: null,
        pillola: "",
        manca: "manca la risoluzione della camera",
      },
      {
        chiave: "coverage",
        l: "Copertura",
        v: "",
        sub: "",
        esito: null,
        pillola: "",
        manca: "manca il cerchio d'immagine dell'ottica",
      },
      {
        chiave: "guide_scale",
        l: "Scala di guida",
        v: "",
        sub: "",
        esito: null,
        pillola: "",
        manca: "manca la guida",
      },
      {
        chiave: "guide_ratio",
        l: "Rapporto guida/ripresa",
        v: "",
        sub: "",
        esito: null,
        pillola: "",
        manca: "manca la guida",
      },
      {
        chiave: "backfocus",
        l: "Backfocus del treno",
        v: "55,5 mm",
        sub: "richiesto 55 mm dall'ottica · tolleranza ±1 mm",
        esito: 0,
        pillola: "+0,5 mm, in tolleranza",
        manca: "",
      },
      {
        chiave: "load",
        l: "Carico",
        v: "",
        sub: "",
        esito: null,
        pillola: "",
        manca: "manca la montatura",
      },
    ])
  })

  it("il cielo non ancora misurato", () => {
    const r = corredo({ scale_arcsec_px: null, width_deg: null, height_deg: 1 })
    expect(conto("sampling", NUMERI.sampling, r)?.sub).toMatch(/^sul cielo: non ancora misurato ·/)
    expect(conto("field", NUMERI.field, r)?.sub).toBe("sul cielo: non ancora misurato")
    const alto = corredo({ width_deg: 1.5, height_deg: null })
    expect(conto("field", NUMERI.field, alto)?.sub).toBe("sul cielo: non ancora misurato")
  })

  it("il sensore in mm", () => {
    expect(conto("sensor_size", { width: 23.5, height: 15.7 })).toMatchObject({
      v: "23,5 × 15,7 mm",
      sub: "dalla risoluzione e dal pixel della camera",
      manca: "",
    })
  })

  it("la copertura: copre o no, col suo esito", () => {
    const c = { diagonal_mm: 28.3, circle_mm: 44 }
    expect(conto("coverage", { ...c, covers: true })).toMatchObject({
      v: "28,3 mm",
      sub: "diagonale del sensore · cerchio d'immagine 44 mm",
      esito: 0,
      pillola: "copre il sensore",
    })
    expect(conto("coverage", { ...c, covers: false })).toMatchObject({
      esito: 2,
      pillola: "non copre il sensore",
    })
  })

  it("la scala di guida: fuori asse o con l'ottica di guida, dentro o fuori", () => {
    const g = { value: 2.5, range_from: 1, range_to: 3, guide_name: "Mini" }
    expect(conto("guide_scale", { ...g, guide: "oag", in_range: true })).toMatchObject({
      v: "2,50″/px",
      sub: "fuori asse, con la focale del setup · consigliata fra 1 e 3″/px",
      esito: 0,
      pillola: "nell'intervallo",
    })
    expect(conto("guide_scale", { ...g, guide: "scope", in_range: false })).toMatchObject({
      v: "2,50″/px",
      sub: "con Mini · consigliata fra 1 e 3″/px",
      esito: 1,
      pillola: "fuori intervallo",
    })
  })

  it("il rapporto guida/ripresa", () => {
    expect(conto("guide_ratio", { value: 2.94 })).toMatchObject({
      v: "2,9×",
      sub: "scala di guida su campionamento",
    })
  })

  it("il backfocus: ogni giudizio, e senza tolleranza", () => {
    const b = { train_mm: 54, required_mm: 55, required_by: "reducer", tolerance_mm: 1 }
    const corto = conto("backfocus", { ...b, difference_mm: -1, verdict: "short" })
    expect(corto).toMatchObject({
      v: "54 mm",
      sub: "richiesto 55 mm dal riduttore · tolleranza ±1 mm",
      esito: 1,
      pillola: "corto di 1 mm",
    })
    expect(conto("backfocus", { ...b, difference_mm: 2, verdict: "long" })).toMatchObject({
      esito: 1,
      pillola: "lungo di 2 mm",
    })
    expect(conto("backfocus", { ...b, difference_mm: 0, verdict: "exact" })).toMatchObject({
      esito: 0,
      pillola: "esatto",
    })
    const libero = { ...b, difference_mm: -1, tolerance_mm: null, verdict: null }
    expect(conto("backfocus", libero)).toMatchObject({
      sub: "richiesto 55 mm dal riduttore · −1 mm · tolleranza non indicata",
      esito: null,
      pillola: "",
    })
    const senzaTolleranza = { ...b, difference_mm: -1, tolerance_mm: null, verdict: "short" }
    expect(conto("backfocus", senzaTolleranza)).toMatchObject({ esito: null, pillola: "" })
    const senzaGiudizio = { ...b, difference_mm: 1.5, verdict: null }
    expect(conto("backfocus", senzaGiudizio)?.sub).toBe(
      "richiesto 55 mm dal riduttore · +1,5 mm · tolleranza non indicata",
    )
  })

  it("il carico: entro o oltre, in percento arrotondato", () => {
    const c = { weight_kg: 12.5, payload_kg: 20 }
    expect(conto("load", { ...c, percent: 62.6, within: true })).toMatchObject({
      v: "63%",
      sub: "del carico della montatura · 12,5 kg su 20",
      esito: 0,
      pillola: "entro il carico",
    })
    expect(conto("load", { ...c, percent: 120, within: false })).toMatchObject({
      esito: 2,
      pillola: "oltre il carico",
    })
  })
})

describe("cio' che manca", () => {
  it("il pezzo intero, il campo detto, o un dato", () => {
    expect(mancanza({ kind: "mount", field: null })).toBe("manca la montatura")
    expect(mancanza({ kind: "mount", field: "payload_kg" })).toBe("manca il carico della montatura")
    expect(mancanza({ kind: "optics", field: "focal_mm" })).toBe("manca la focale dell'ottica")
    expect(mancanza({ kind: "camera", field: "pixel_size_um" })).toBe("manca il pixel della camera")
    expect(mancanza({ kind: "camera", field: "height_px" })).toBe(
      "manca la risoluzione della camera",
    )
    expect(mancanza({ kind: "optics", field: "aperture_mm" })).toBe("manca l'apertura dell'ottica")
    expect(mancanza({ kind: "optics", field: "required_backfocus_mm" })).toBe(
      "manca il backfocus richiesto dell'ottica",
    )
    expect(mancanza({ kind: "spacer", field: "thickness_mm" })).toBe(
      "manca lo spessore del distanziale",
    )
    expect(mancanza({ kind: "optics", field: "weight_kg" })).toBe("manca il peso dell'ottica")
    expect(mancanza({ kind: "camera", field: "adc_bits" })).toBe("manca un dato della camera")
  })
})
