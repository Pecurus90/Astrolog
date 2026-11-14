import { useState } from "react"

import { CampoDelModulo, TendinaDelModulo, TestoDelModulo } from "./componenti/Modulo"
import { PillolaScelta } from "./componenti/PillolaScelta"
import type { Formato } from "./componenti/Tema"
import { ALTRA, ModuloDellaRiga } from "./ModuloDellaRiga"
import { pallinoDi } from "./MisureDati"
import { rifiutoDetto, useScrittura } from "./ModuloDelGesto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, numeroNelCampo, t } from "./i18n"
import { misuraConVirgola, testo } from "./scritto"

type Pagina = components["schemas"]["GearList"]
type Filtro = components["schemas"]["FilterOnPage"]
type Scritta = components["schemas"]["FilterCorrection"]
type Banda = components["schemas"]["BandIn"]["band"]

// [T] Attrezzatura.dc.html `BANDE`, `MISURE` (428-429)
const BANDE: Banda[] = ["L", "R", "G", "B", "HA", "HB", "OIII", "SII"]
const MISURE = ["1.25in", "31mm", "36mm", "2in", "50mm_square"] as const
const SI_NO: { v: string; l: Chiave }[] = [
  { v: "si", l: "gear.form.yes" },
  { v: "no", l: "gear.form.no" },
]

interface Bozza {
  name: string
  brand: string
  newBrand: string
  model: string
  bande: [string, string][]
  filter_size: string
  mounted: string
  fast_optics: string
  thickness_mm: string
}

const siNo = (v: boolean | null) => (v === null ? "" : v ? "si" : "no")
const daSiNo = (s: string) => (s === "si" ? true : s === "no" ? false : undefined)
// a filter's taken name is said as a filter's (board ERR, name taken by a filter)
const codiceDi = (e: unknown) => (e as { detail?: { code?: string } } | null)?.detail?.code

function iniziale(f: Filtro): Bozza {
  return {
    name: f.name,
    brand: f.brand ?? "",
    newBrand: "",
    model: f.model ?? "",
    bande: f.bands.length
      ? f.bands.map((x) => [x.band, x.width_nm === null ? "" : numeroNelCampo(x.width_nm)])
      : // a band the name gives, not yet written: the form starts on it, sent only if changed
        [[BANDE.includes(f.passband as Banda) ? (f.passband as string) : "", ""]],
    filter_size: f.filter_size ?? "",
    mounted: siNo(f.mounted),
    fast_optics: siNo(f.fast_optics),
    thickness_mm: f.thickness_mm === null ? "" : numeroNelCampo(f.thickness_mm),
  }
}

/** The bands written, a band without its name left out (board `bandeV`). */
function bande(b: Bozza): { band: Banda; width_nm: number | null }[] {
  return b.bande.flatMap(([band, nm]) =>
    BANDE.includes(band as Banda)
      ? [{ band: band as Banda, width_nm: misuraConVirgola(nm) ?? null }]
      : [],
  )
}

/** Only what changed leaves, as for a piece. */
function scritta(prima: Bozza, b: Bozza): Scritta {
  const out: Scritta = {}
  if (b.name !== prima.name && b.name.trim()) out.name = b.name.trim()
  const marca = b.brand === ALTRA ? testo(b.newBrand) : b.brand || undefined
  if (marca && marca !== prima.brand) out.brand = marca
  const modello = testo(b.model)?.trim()
  if (modello && modello !== prima.model) out.model = modello
  if (JSON.stringify(b.bande) !== JSON.stringify(prima.bande)) out.bands = bande(b)
  if (b.filter_size !== prima.filter_size && b.filter_size) {
    out.filter_size = b.filter_size as NonNullable<Scritta["filter_size"]>
  }
  if (b.mounted !== prima.mounted) out.mounted = daSiNo(b.mounted) ?? null
  if (b.fast_optics !== prima.fast_optics) out.fast_optics = daSiNo(b.fast_optics) ?? null
  const spessore = misuraConVirgola(b.thickness_mm)
  if (b.thickness_mm !== prima.thickness_mm && spessore !== undefined) out.thickness_mm = spessore
  return out
}

/**
 * Il **modulo di un filtro** (tavola v82 `modulo`, k `mod` su un filtro): il disco del suo colore,
 * nome e modello, le bande con la larghezza, misura, montato, per ottiche veloci, spessore;
 * "Unisci a" ed Elimina come per un pezzo.
 */
export function ModuloDelFiltro({
  filtro: f,
  pagina,
  formato,
  scansione,
  onChiudi,
}: {
  filtro: Filtro
  pagina: Pagina
  formato: Formato
  scansione: boolean
  onChiudi: () => void
}) {
  const [prima] = useState(() => iniziale(f))
  const [b, setB] = useState<Bozza>(prima)
  const [unione, setUnione] = useState("")
  const unibili = pagina.filters.filter((o) => f.mergeable_into.includes(o.id))
  const verso = unibili.find((o) => String(o.id) === unione)
  const base = `filtro-${f.id}`
  const scrivi = useScrittura(async () => {
    const { data, error } = await api.PATCH("/api/v1/gear/filters/{filter_id}", {
      params: { path: { filter_id: f.id } },
      body: verso ? { merge_into: verso.id } : scritta(prima, b),
    })
    if (error) throw error
    return data
  }, onChiudi)
  const metti = (o: Partial<Bozza>) => setB((x) => ({ ...x, ...o }))
  const metteBanda = (i: number, j: 0 | 1, v: string) =>
    setB((x) => {
      const nuove = x.bande.map((y, k) => {
        const z: [string, string] = [...y]
        if (k === i) z[j] = v
        return z
      })
      return { ...x, bande: nuove }
    })
  const quante = (n: number) =>
    setB((x) => ({ ...x, bande: Array.from({ length: n }, (_, i) => x.bande[i] ?? ["", ""]) }))

  const scritte = bande(b).length
  const marca = b.brand === ALTRA ? b.newBrand : b.brand
  const inserito = (v: string) => (v ? t("gear.form.declared") : undefined)
  const pillole = (chiave: keyof Bozza, voci: { v: string; l: string }[], lab: string) => (
    <PillolaScelta
      forma="risposta"
      fondo="vuoto"
      etichetta={lab}
      formato={formato}
      opzioni={voci.map((s) => ({
        l: s.l,
        sel: b[chiave] === s.v,
        on: () => metti({ [chiave]: s.v }),
      }))}
    />
  )
  const siNoVoci = SI_NO.map((s) => ({ v: s.v, l: t(s.l) }))
  const tec = [b.filter_size, b.mounted, b.fast_optics, b.thickness_mm].filter(Boolean).length

  return (
    <ModuloDellaRiga
      base={base}
      titolo={f.name}
      disco={pallinoDi(f.passband ?? undefined)}
      formato={formato}
      pagina={pagina}
      scansione={scansione}
      nome={b.name}
      onNome={(v) => metti({ name: v })}
      marca={b.brand}
      nuovaMarca={b.newBrand}
      origineMarca={inserito(b.brand)}
      onMarca={(v) => metti({ brand: v })}
      onNuovaMarca={(v) => metti({ newBrand: v })}
      chi={{ scritti: [b.name, marca, b.model].filter((x) => x.trim()).length, di: 3 }}
      tecnici={{ scritti: scritte + tec, di: b.bande.length + 4 }}
      manca={scritte === 0 ? t("gear.write.needBand") : ""}
      unibili={unibili}
      etichettaUnione={t("gear.write.filter.sameAs")}
      unione={unione}
      onUnione={(v) => {
        // choosing or dropping the merge starts over: a hidden edit would leave unseen
        setUnione(v)
        setB(prima)
      }}
      frame={f.frames}
      scrittura={{ onSalva: () => scrivi.mutate(), occupato: scrivi.isPending }}
      rifiuto={
        codiceDi(scrivi.error) === "name_taken"
          ? t("gear.write.spellingTaken")
          : rifiutoDetto(scrivi.error)
      }
      elimina={{
        rifiuto: f.delete_refused,
        inSetup: f.in_rigs,
        manda: () =>
          api.DELETE("/api/v1/gear/filters/{filter_id}", { params: { path: { filter_id: f.id } } }),
      }}
      onChiudi={onChiudi}
      campiChi={
        <CampoDelModulo
          id={`${base}-model`}
          etichetta={t("gear.f.model")}
          origine={inserito(b.model)}
        >
          <TestoDelModulo
            id={`${base}-model`}
            valore={b.model}
            onValore={(v) => metti({ model: v })}
          />
        </CampoDelModulo>
      }
      campiTecnici={
        <>
          <CampoDelModulo id={`${base}-nb`} etichetta={t("gear.f.bands")} largo>
            <PillolaScelta
              forma="risposta"
              fondo="vuoto"
              etichetta={t("gear.f.bands")}
              formato={formato}
              opzioni={[1, 2, 3, 4].map((n) => ({
                l: String(n),
                sel: b.bande.length === n,
                on: () => quante(n),
              }))}
            />
          </CampoDelModulo>
          {b.bande.flatMap(([band, nm], i) => [
            <CampoDelModulo
              key={`b${i}`}
              id={`${base}-b${i}`}
              etichetta={
                b.bande.length > 1 ? t("gear.f.bandN", { n: String(i + 1) }) : t("gear.f.band")
              }
            >
              <TendinaDelModulo
                id={`${base}-b${i}`}
                valore={band}
                voci={[{ valore: "", l: "--" }, ...BANDE.map((x) => ({ valore: x, l: x }))]}
                onValore={(v) => metteBanda(i, 0, v)}
              />
            </CampoDelModulo>,
            <CampoDelModulo key={`nm${i}`} id={`${base}-nm${i}`} etichetta={t("gear.f.width_nm")}>
              <TestoDelModulo
                id={`${base}-nm${i}`}
                valore={nm}
                onValore={(v) => metteBanda(i, 1, v)}
              />
            </CampoDelModulo>,
          ])}
          <CampoDelModulo
            id={`${base}-size`}
            etichetta={t("gear.f.filter_size")}
            largo
            origine={inserito(b.filter_size)}
          >
            {pillole(
              "filter_size",
              MISURE.map((v) => ({ v, l: t(`gear.size.${v}`) })),
              t("gear.f.filter_size"),
            )}
          </CampoDelModulo>
          <CampoDelModulo
            id={`${base}-mounted`}
            etichetta={t("gear.f.mounted")}
            origine={inserito(b.mounted)}
          >
            {pillole("mounted", siNoVoci, t("gear.f.mounted"))}
          </CampoDelModulo>
          <CampoDelModulo
            id={`${base}-fast`}
            etichetta={t("gear.f.fast_optics")}
            origine={inserito(b.fast_optics)}
          >
            {pillole("fast_optics", siNoVoci, t("gear.f.fast_optics"))}
          </CampoDelModulo>
          <CampoDelModulo
            id={`${base}-thickness`}
            etichetta={t("gear.f.thickness_mm")}
            origine={inserito(b.thickness_mm)}
          >
            <TestoDelModulo
              id={`${base}-thickness`}
              valore={b.thickness_mm}
              onValore={(v) => metti({ thickness_mm: v })}
            />
          </CampoDelModulo>
        </>
      }
    />
  )
}
