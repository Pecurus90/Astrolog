import { useState } from "react"

import { CalcolatoDelModulo, CampoDelModulo, TestoDelModulo } from "./componenti/Modulo"
import { PillolaScelta } from "./componenti/PillolaScelta"
import type { Formato } from "./componenti/Tema"
import { ALTRA, ModuloDellaRiga } from "./ModuloDellaRiga"
import { rifiutoDetto, useScrittura } from "./ModuloDelGesto"
import type { CampoScheda } from "./SchedaDelPezzo"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, alPiu, numero, numeroNelCampo, t } from "./i18n"
import { misuraConVirgola, testo } from "./scritto"

type Pagina = components["schemas"]["GearList"]
type Pezzo = components["schemas"]["InstrumentOnPage"]
type Scritta = components["schemas"]["InstrumentCorrection"]
type Bozza = Record<string, string>

// [T] Attrezzatura.dc.html `SCHEMI`, `MISURE` (427-428): the pills, in the board's order
const SCHEMI = ["refractor", "newtonian", "sct", "rc", "maksutov", "camera_lens", "other"] as const
const MISURE = ["1.25in", "31mm", "36mm", "2in", "50mm_square"] as const
const PILLOLE: Partial<Record<CampoScheda, { v: string; l: Chiave }[]>> = {
  optical_design: SCHEMI.map((v) => ({ v, l: `gear.design.${v}` as const })),
  camera_type: [
    { v: "mono", l: "gear.form.mono" },
    { v: "color", l: "gear.form.color" },
  ],
  cooled: [
    { v: "si", l: "gear.form.yes" },
    { v: "no", l: "gear.form.no" },
  ],
  filter_size: MISURE.map((v) => ({ v, l: `gear.size.${v}` as const })),
}
const LARGHI: CampoScheda[] = ["optical_design", "camera_type", "filter_size"]
const INTERI: CampoScheda[] = ["adc_bits", "slots", "total_steps"]
const TESTI: CampoScheda[] = ["brand", "model", "notes", "sensor"]
// the first block's fields; the API sends them in every kind's card
const CHI: CampoScheda[] = ["brand", "model", "notes"]

function etichetta(kind: Pezzo["kind"], campo: CampoScheda): string {
  if (campo === "width_px") return t("gear.f.resolution")
  if (campo === "focal_mm" && kind === "guide_scope") return t("gear.f.focal_mm.guide")
  if (campo === "filter_size" && kind === "filter_wheel") return t("gear.f.filter_size.wheel")
  if (campo === "thickness_mm" && (kind === "camera" || kind === "guide_camera")) {
    return t("gear.f.thickness_mm.camera")
  }
  return t(`gear.f.${campo}` as Chiave)
}

/** What the card holds now, as the fields write it: the comma, yes/no, "W x H". */
function iniziale(p: Pezzo): Bozza {
  const b: Bozza = { name: p.name }
  for (const c of Object.keys(p) as (keyof Pezzo)[]) {
    const v = p[c]
    if (typeof v === "number") b[c] = numeroNelCampo(v)
    else if (typeof v === "string") b[c] = v
    else if (typeof v === "boolean" && c === "cooled") b[c] = v ? "si" : "no"
  }
  b.width_px = p.width_px && p.height_px ? `${p.width_px} × ${p.height_px}` : "" // glifo-ok: board glyph
  for (const x of p.biases)
    b[`bias:${x.offset}`] = x.bias_adu === null ? "" : numeroNelCampo(x.bias_adu)
  return b
}

/** A changed field as the API takes it; undefined: nothing to send (empty, or not a number). */
function valore(campo: CampoScheda, s: string): unknown {
  if (TESTI.includes(campo)) return testo(s)
  if (campo === "cooled") return s === "si" ? true : s === "no" ? false : undefined
  if (PILLOLE[campo]) return s || undefined
  return misuraConVirgola(s, INTERI.includes(campo))
}

/** Only what changed leaves: sending back what the files said would make it yours. */
function scritta(campi: CampoScheda[], prima: Bozza, b: Bozza): Scritta {
  const out: Record<string, unknown> = {}
  const nome = b.name?.trim() ?? ""
  if (b.name !== prima.name && nome) out.name = nome
  for (const c of campi) {
    if (c === "height_px" || b[c] === prima[c]) continue
    if (c === "width_px") {
      const m = /^\s*(\d+)\s*[x×]\s*(\d+)\s*$/i.exec(b[c] ?? "") // glifo-ok: board glyph
      if (m) Object.assign(out, { width_px: Number(m[1]), height_px: Number(m[2]) })
    } else if (c === "brand") {
      const marca = b.brand === ALTRA ? testo(b.newBrand ?? "") : b.brand || undefined
      if (marca) out.brand = marca
    } else {
      const v = valore(c, b[c] ?? "")
      if (v !== undefined) out[c] = v
    }
  }
  return out as Scritta
}

/**
 * Il **modulo di un pezzo** (tavola v82 `modulo`, k `mod`): nome e modello, dati tecnici coi campi
 * che l'API chiede per il suo tipo, "dai file" o "inserito" accanto, i valori calcolati dal backend
 * (si aggiornano dopo Salva), il bias per offset, "Unisci a" ed Elimina.
 */
export function ModuloDelPezzo({
  pezzo: p,
  pagina,
  formato,
  scansione,
  onChiudi,
}: {
  pezzo: Pezzo
  pagina: Pagina
  formato: Formato
  scansione: boolean
  onChiudi: () => void
}) {
  const [prima] = useState(() => iniziale(p))
  const [b, setB] = useState<Bozza>(prima)
  const [unione, setUnione] = useState("")
  const metti = (c: string, v: string) => setB((x) => ({ ...x, [c]: v }))
  const campi = (pagina.cards[p.kind] ?? []) as CampoScheda[]
  const tecnici = campi.filter(
    (c) => !CHI.includes(c) && c !== "height_px" && (c !== "cooling_c" || b.cooled === "si"),
  )
  const unibili = pagina.instruments.filter((o) => p.mergeable_into.includes(o.id))
  const base = `pezzo-${p.id}`
  const scrivi = useScrittura(async () => {
    if (unione) {
      const { data, error } = await api.PATCH("/api/v1/gear/instruments/{instrument_id}", {
        params: { path: { instrument_id: p.id } },
        body: { merge_into: Number(unione) },
      })
      if (error) throw error
      return data
    }
    // the biases first: the card's PATCH may start the worker, and a bias then waits (409)
    for (const x of p.biases) {
      const k = `bias:${x.offset}`
      const adu = b[k] === prima[k] ? undefined : misuraConVirgola(b[k] ?? "")
      if (adu === undefined) continue
      const put = await api.PUT("/api/v1/gear/instruments/{camera_id}/biases", {
        params: { path: { camera_id: p.id } },
        body: { offset: x.offset, bias_adu: adu },
      })
      if (put.error) throw put.error
    }
    const { data, error } = await api.PATCH("/api/v1/gear/instruments/{instrument_id}", {
      params: { path: { instrument_id: p.id } },
      body: scritta(campi, prima, b),
    })
    if (error) throw error
    return data
  }, onChiudi)

  const origine = (c: string) =>
    !b[c]
      ? undefined
      : p.from_files.includes(c) && b[c] === prima[c]
        ? t("gear.form.fromFiles")
        : t("gear.form.declared")
  const campo = (c: CampoScheda) => {
    const id = `${base}-${c}`
    const scelte = PILLOLE[c]
    return (
      <CampoDelModulo
        key={c}
        id={id}
        etichetta={etichetta(p.kind, c)}
        largo={LARGHI.includes(c)}
        origine={origine(c)}
      >
        {scelte ? (
          <PillolaScelta
            forma="risposta"
            fondo="vuoto"
            etichetta={etichetta(p.kind, c)}
            formato={formato}
            opzioni={scelte.map((s) => ({ l: t(s.l), sel: b[c] === s.v, on: () => metti(c, s.v) }))}
          />
        ) : (
          <TestoDelModulo id={id} valore={b[c] ?? ""} onValore={(v) => metti(c, v)} />
        )}
      </CampoDelModulo>
    )
  }
  const n = p.numbers
  const dopo = (c: CampoScheda) => {
    if (c === "focal_mm" && p.kind === "optics") {
      const rf = n.focal_ratio?.value
      const dw = n.dawes?.value
      return [
        <CalcolatoDelModulo
          key="rf"
          id={`${base}-rf`}
          etichetta={t("gear.calc.ratio")}
          valore={rf == null ? null : t("gear.rig.ratio", { n: alPiu(rf, 1) })}
          manca={t("gear.calc.needRatio")}
        />,
        <CalcolatoDelModulo
          key="pr"
          id={`${base}-pr`}
          etichetta={t("gear.calc.resolving")}
          valore={dw == null ? null : t("gear.calc.arcsec", { n: alPiu(dw, 2) })}
          manca={t("gear.calc.needAperture")}
        />,
      ]
    }
    if (c === "pixel_size_um") {
      const s = n.sensor_size
      const v =
        s?.width != null && s.height != null
          ? t("gear.n.sensor.value", { larghezza: alPiu(s.width, 1), altezza: alPiu(s.height, 1) })
          : null
      return [
        <CalcolatoDelModulo
          key="ds"
          id={`${base}-ds`}
          etichetta={t("gear.calc.sensor")}
          valore={v}
          manca={t("gear.calc.needSensor")}
        />,
      ]
    }
    if (c === "adc_bits") {
      return p.biases.map((x) => {
        const k = `bias:${x.offset}`
        const lab =
          p.biases.length === 1
            ? t("gear.f.bias")
            : x.offset === null
              ? t("gear.f.biasNoOffset")
              : t("gear.f.biasAt", { n: numero(x.offset) })
        return (
          <CampoDelModulo
            key={k}
            id={`${base}-${k}`}
            etichetta={lab}
            origine={b[k] ? t("gear.form.declared") : undefined}
          >
            <TestoDelModulo id={`${base}-${k}`} valore={b[k] ?? ""} onValore={(v) => metti(k, v)} />
          </CampoDelModulo>
        )
      })
    }
    return []
  }

  const marca = b.brand === ALTRA ? b.newBrand : b.brand
  const bias = p.biases.map((x) => `bias:${x.offset}`)
  return (
    <ModuloDellaRiga
      base={base}
      titolo={p.name}
      formato={formato}
      pagina={pagina}
      scansione={scansione}
      nome={b.name ?? ""}
      onNome={(v) => metti("name", v)}
      marca={b.brand ?? ""}
      nuovaMarca={b.newBrand ?? ""}
      origineMarca={origine("brand")}
      onMarca={(v) => metti("brand", v)}
      onNuovaMarca={(v) => metti("newBrand", v)}
      chi={{ scritti: [b.name, marca, b.model, b.notes].filter((x) => x?.trim()).length, di: 4 }}
      tecnici={{
        scritti: [...tecnici, ...bias].filter((c) => b[c]?.trim()).length,
        di: tecnici.length + bias.length,
      }}
      manca=""
      unibili={unibili}
      etichettaUnione={t("gear.write.sameAs")}
      unione={unione}
      onUnione={(v) => {
        // choosing or dropping the merge starts over: a hidden edit would leave unseen
        setUnione(v)
        setB(prima)
      }}
      frame={p.frames}
      scrittura={{ onSalva: () => scrivi.mutate(), occupato: scrivi.isPending }}
      rifiuto={rifiutoDetto(scrivi.error)}
      elimina={{
        rifiuto: p.delete_refused,
        inSetup: p.in_rigs,
        manda: () =>
          api.DELETE("/api/v1/gear/instruments/{instrument_id}", {
            params: { path: { instrument_id: p.id } },
          }),
      }}
      onChiudi={onChiudi}
      campiChi={
        <>
          {campo("model")}
          <CampoDelModulo
            id={`${base}-notes`}
            etichetta={t("gear.f.notes")}
            largo
            origine={origine("notes")}
          >
            <TestoDelModulo
              id={`${base}-notes`}
              valore={b.notes ?? ""}
              onValore={(v) => metti("notes", v)}
            />
          </CampoDelModulo>
        </>
      }
      campiTecnici={tecnici.flatMap((c) => [campo(c), ...dopo(c)])}
    />
  )
}
