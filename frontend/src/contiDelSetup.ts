import type { components } from "./api/schema"
import type { Esito } from "./componenti/Pillola"
import { type Chiave, alPiu, decimali, numero, t } from "./i18n"

type Corredo = components["schemas"]["RigOnPage"]
type Conti = components["schemas"]["RigNumbers"]
type Manca = NonNullable<Conti["sampling"]["missing"]>

/** One row of "Dati del setup": the value with its line, the verdict pill, or what is missing. */
export interface Conto {
  chiave: keyof Conti
  l: string
  v: string
  sub: string
  esito: Esito | null
  pillola: string
  manca: string
}

// the fields a number can lack, with their article; any other one is "un dato"
const CAMPI_DETTI = new Set([
  "pixel_size_um",
  "width_px",
  "height_px",
  "aperture_mm",
  "focal_mm",
  "image_circle_mm",
  "required_backfocus_mm",
  "thickness_mm",
  "weight_kg",
  "payload_kg",
])

/** "manca il pixel della camera", "manca la montatura": il campo, poi di chi (tavola `conti`). */
export function mancanza(m: Manca): string {
  if (m.field === null) return t("gear.missing.piece", { pezzo: t(`gear.missing.p.${m.kind}`) })
  const campo = CAMPI_DETTI.has(m.field) ? m.field : "other"
  return t("gear.missing", {
    campo: t(`gear.missing.f.${campo}` as Chiave),
    di: t(`gear.missing.of.${m.kind}`),
  })
}

const PX = (n: number) => t("gear.n.arcsecPx", { n: decimali(n, 2) })
const GRADI = (w: number, h: number) =>
  t("gear.field.sides", { larghezza: alPiu(w, 2), altezza: alPiu(h, 2) })
const SCARTO = (mm: number) => `${mm > 0 ? "+" : "−"}${alPiu(Math.abs(mm), 1)} mm` // glifo-ok: minus sign

type Riga = Omit<Conto, "chiave" | "l" | "manca">
const riga = (v: string, sub: string, esito: Esito | null = null, pillola = ""): Riga => ({
  v, sub, esito, pillola,
}) // prettier-ignore

function campionamento(c: Conti["sampling"], r: Corredo): Riga {
  const cielo =
    r.scale_arcsec_px === null
      ? t("gear.n.onSky.none")
      : t("gear.n.onSky", { n: decimali(r.scale_arcsec_px, 2) })
  const da = decimali(c.seeing_from ?? 0, 1)
  const a = decimali(c.seeing_to ?? 0, 1)
  return riga(PX(c.value ?? 0), t("gear.n.seeing", { cielo, da, a }))
}

function campo(c: Conti["field"], r: Corredo): Riga {
  const cielo =
    r.width_deg === null || r.height_deg === null
      ? t("gear.n.onSky.none")
      : t("gear.n.field.sky", { larghezza: alPiu(r.width_deg, 2), altezza: alPiu(r.height_deg, 2) })
  return riga(GRADI(c.width ?? 0, c.height ?? 0), cielo)
}

function copertura(c: Conti["coverage"]): Riga {
  const sub = t("gear.n.coverage.sub", { mm: alPiu(c.circle_mm ?? 0, 1) })
  const v = t("gear.n.mm", { n: alPiu(c.diagonal_mm ?? 0, 1) })
  return c.covers
    ? riga(v, sub, 0, t("gear.n.coverage.yes"))
    : riga(v, sub, 2, t("gear.n.coverage.no"))
}

function guida(c: Conti["guide_scale"]): Riga {
  const come =
    c.guide === "oag"
      ? t("gear.n.guide.oag")
      : t("gear.n.guide.scope", { nome: c.guide_name ?? "" })
  const sub = t("gear.n.guide.sub", {
    come,
    da: alPiu(c.range_from ?? 0, 1),
    a: alPiu(c.range_to ?? 0, 1),
  })
  return c.in_range
    ? riga(PX(c.value ?? 0), sub, 0, t("gear.n.guide.in"))
    : riga(PX(c.value ?? 0), sub, 1, t("gear.n.guide.out"))
}

function backfocus(c: Conti["backfocus"]): Riga {
  const mm = alPiu(c.required_mm ?? 0, 1)
  const richiesto = t(
    c.required_by === "reducer" ? "gear.n.backfocus.reducer" : "gear.n.backfocus.optics",
    { mm },
  )
  const v = t("gear.n.mm", { n: alPiu(c.train_mm ?? 0, 1) })
  const d = c.difference_mm ?? 0
  if (c.tolerance_mm === null || c.verdict === null) {
    return riga(v, t("gear.n.backfocus.noTol", { richiesto, scarto: SCARTO(d) }))
  }
  const sub = t("gear.n.backfocus.tol", { richiesto, mm: alPiu(c.tolerance_mm, 1) })
  const quanto = alPiu(Math.abs(d), 1)
  const giudizio: Record<NonNullable<Conti["backfocus"]["verdict"]>, [Esito, string]> = {
    exact: [0, t("gear.n.backfocus.exact")],
    in_tolerance: [0, t("gear.n.backfocus.in", { scarto: SCARTO(d) })],
    short: [1, t("gear.n.backfocus.short", { mm: quanto })],
    long: [1, t("gear.n.backfocus.long", { mm: quanto })],
  }
  const [esito, parola] = giudizio[c.verdict]
  return riga(v, sub, esito, parola)
}

function carico(c: Conti["load"]): Riga {
  const sub = t("gear.n.load.sub", {
    kg: alPiu(c.weight_kg ?? 0, 1),
    max: alPiu(c.payload_kg ?? 0, 1),
  })
  const v = `${numero(Math.round(c.percent ?? 0))}%`
  return c.within ? riga(v, sub, 0, t("gear.n.load.in")) : riga(v, sub, 2, t("gear.n.load.out"))
}

/** Le righe di "Dati del setup", nell'ordine della tavola: ognuna col suo valore, o con cio'
 *  che le manca. I numeri arrivano gia' fatti (`numbers`); qui si scrivono. */
export function contiDelSetup(r: Corredo, conti: Conti): Conto[] {
  const scrivi: { [K in keyof Conti]: (c: Conti[K]) => Riga } = {
    focal_ratio: (c) =>
      riga(
        t("gear.rig.ratio", { n: alPiu(c.value ?? 0, 1) }),
        t("gear.n.focal_ratio.sub", { mm: numero(r.focal_mm ?? 0) }),
      ),
    sampling: (c) => campionamento(c, r),
    field: (c) => campo(c, r),
    sensor_size: (c) =>
      riga(
        t("gear.n.sensor.value", {
          larghezza: alPiu(c.width ?? 0, 1),
          altezza: alPiu(c.height ?? 0, 1),
        }),
        t("gear.n.sensor.sub"),
      ),
    coverage: copertura,
    guide_scale: guida,
    guide_ratio: (c) =>
      riga(
        t("gear.n.guide_ratio.value", { n: alPiu(c.value ?? 0, 1) }),
        t("gear.n.guide_ratio.sub"),
      ),
    backfocus,
    load: carico,
  }
  const ordine: (keyof Conti)[] = [
    "focal_ratio", "sampling", "field", "sensor_size", "coverage", "guide_scale", "guide_ratio",
    "backfocus", "load",
  ] // prettier-ignore
  return ordine.map((chiave) => {
    const c = conti[chiave]
    const l = t(`gear.n.${chiave}`)
    if (c.missing)
      return { chiave, l, v: "", sub: "", esito: null, pillola: "", manca: mancanza(c.missing) }
    const scritto = (scrivi[chiave] as (x: typeof c) => Riga)(c)
    return { chiave, l, manca: "", ...scritto }
  })
}
