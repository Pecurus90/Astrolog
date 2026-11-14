/**
 * Le misure dei frame (tavola v76, `componenti/MisureFrame.dc.html`): di una notte coi suoi
 * oggetti a gruppi, di un oggetto con le sue notti (`tipo`). Le tessere con mediane e quartili,
 * le altre misure, frame per frame, il frame scelto, i gruppi a confronto, la tabella per filtro,
 * tilt e curvatura. Il componente sceglie e scrive: i conti sono dell'API.
 */
import { type ChangeEvent, useState } from "react"

import { Pillola } from "./componenti/Pillola"
import { PillolaScelta, type OpzioneScelta } from "./componenti/PillolaScelta"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { nomeDelFiltro } from "./FiltriUsati"
import { type Chiave, numero, t } from "./i18n"
import {
  ALTRE,
  CIELO,
  DAL_SETUP,
  ESITO,
  type EsitoDelGruppo,
  type Insieme,
  type Misure,
  PILASTRO,
  type Scelta,
  TESSERE,
  type Tessera,
  type Tipo,
  diversi,
  filtriDi,
  insieme,
  latoDelPilastro,
  tintaDi,
  linea,
  nomeDelGruppo,
  nomeDi,
  quartili,
  scritto,
  statistica,
} from "./MisureDati"
import { FramePerFrame } from "./FramePerFrame"
import { AConfronto, IlFrame, PerFiltro } from "./MisureSezioni"
import { TiltCurvatura } from "./TiltCurvatura"

const RICORDA = "astrolog.misure.altra"

function letta(): string | null {
  try {
    return localStorage.getItem(RICORDA)
  } catch {
    return null
  }
}

function ricorda(v: string | null): void {
  try {
    if (v) localStorage.setItem(RICORDA, v)
    else localStorage.removeItem(RICORDA)
  } catch {
    // una finestra privata non ricorda: la scelta vale finche' la pagina e' aperta
  }
}

export function MisureDeiFrame({
  misure,
  formato,
  tipo = "notte",
  esiti,
}: {
  misure: Misure
  formato: Formato
  tipo?: Tipo
  /** L'esito di ogni gruppo accanto alla sua riga in *A confronto*: le notti dell'oggetto. */
  esiti?: ReadonlyMap<string, EsitoDelGruppo>
}) {
  const tel = formato === "telefono"
  const [scelta, setScelta] = useState<Scelta>({ gruppo: null, filtro: null })
  const [altra, setAltra] = useState<string | null>(letta)
  // le due tessere di partenza (tavola, MisureFrame 211)
  const [met, setMet] = useState<string[]>(() =>
    tipo === "oggetto" ? ["fwhm", "snr"] : ["fwhm", "eccentricity"],
  )
  const [cmp, setCmp] = useState<string | null>(null)
  const [sel, setSel] = useState<number | null>(null)

  const set = insieme(misure, scelta.gruppo, scelta.filtro)
  const tutti = insieme(misure, scelta.gruppo, null)
  const filtri = filtriDi(misure, scelta.gruppo)
  const misurati = statistica(set, "hfd_px")?.measured ?? 0
  const scegliFiltro = (f: string | null) => {
    setScelta({ ...scelta, filtro: f })
    setSel(null)
  }
  const opzioni: OpzioneScelta[] = [
    {
      l: t("measures.all"),
      c: numero(tutti?.frames ?? 0),
      sel: scelta.filtro === null,
      on: () => scegliFiltro(null),
    },
    ...filtri.map((f) => ({
      l: nomeDelFiltro(f.name),
      c: numero(insieme(misure, scelta.gruppo, f.name)?.frames ?? 0),
      sel: scelta.filtro === f.name,
      tinta: tintaDi(f.passband),
      on: () => scegliFiltro(f.name),
    })),
  ]
  const tocca = (id: string) => {
    const j = met.indexOf(id)
    const ora = met.slice()
    if (j >= 0) {
      if (ora.length > 1) ora.splice(j, 1)
    } else {
      ora.push(id)
      if (ora.length > 2) ora.shift()
    }
    setMet(ora)
  }
  const sceltaAltra = (e: ChangeEvent<HTMLSelectElement>) => {
    const v = e.target.value || null
    const ora = met.filter((k) => k !== altra)
    if (v && v !== PILASTRO) {
      ora.push(v)
      if (ora.length > 2) ora.shift()
    }
    ricorda(v)
    setAltra(v)
    setMet(ora.length ? ora : ["fwhm"])
  }
  const solo = misure.groups.find((o) => o.key === scelta.gruppo)
  const isolato = solo ? nomeDelGruppo(solo) : null
  const tessere = [
    ...TESSERE,
    ...(altra ? [{ id: altra, nome: nomeDi(altra), chiave: altra }] : []),
  ]

  return (
    <div className="al-c-misure-frame__blocco-1" data-formato={formato}>
      <div className="al-c-misure-frame__colonna-1">
        <section className="al-c-misure-frame__colonna-2" aria-label={t("measures.title")}>
          <div className="al-c-misure-frame__riga-1" style={{ alignItems: "center" }}>
            <h2 className="al-c-misure-frame__testo-1">{t("measures.title")}</h2>
          </div>
          <div className="al-c-misure-frame__riga-2">
            <PillolaScelta
              ruolo="radio"
              classe="al-c-misure-frame__scelta al-scelta--sottili"
              scorre={tel}
              opzioni={opzioni}
              etichetta={t("measures.filter")}
              formato={formato}
            />
            <span className="al-c-misure-frame__testo-4">
              {t("measures.of", { m: numero(misurati), n: numero(set?.frames ?? 0) })}
            </span>
            {(set?.pending ?? misure.pending) > 0 && (
              <span className="al-c-misure-frame__riga-5">
                <span className="al-c-misure-frame__tondo-2" aria-hidden="true" />
                {t("measures.pending")}
              </span>
            )}
            {isolato && (
              <button
                type="button"
                className="al-bottone al-c-misure-frame__riga-6"
                onClick={() => setScelta({ ...scelta, gruppo: null })}
              >
                {t("measures.only", { n: isolato })}
              </button>
            )}
          </div>
          <div className="al-c-misure-frame__centro-1 al-c-misure-frame__centro-1--tessere">
            {tessere.map((x) => (
              <UnaTessera
                key={x.id}
                tessera={x}
                set={set}
                perFiltro={statistica(set, x.chiave)?.per_filter === true}
                posto={met.indexOf(x.id)}
                tipo={tipo}
                onTocca={() => x.id !== PILASTRO && tocca(x.id)}
              />
            ))}
            <div className="al-c-misure-frame__altre">
              <span className="al-c-misure-frame__riga-7">{t("measures.other")}</span>
              <select
                key={altra ?? ""}
                defaultValue={altra ?? ""}
                onChange={sceltaAltra}
                aria-label={t("measures.other")}
                className="al-tendina al-tendina--tondo al-c-misure-frame__altre-tendina"
              >
                <option value="">{t(altra ? "measures.other.none" : "measures.other.pick")}</option>
                {ALTRE.map((g) => (
                  <optgroup key={g.gruppo} label={t(g.gruppo)}>
                    {g.voci.map((v) => (
                      <option key={v.chiave} value={v.chiave}>
                        {v.nome}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
          </div>
          <span className="al-c-misure-frame__testo-7">{t("measures.how")}</span>
        </section>
        <FramePerFrame
          misure={misure}
          scelta={scelta}
          met={met}
          sel={sel}
          onSel={setSel}
          formato={formato}
        />
        <IlFrame misure={misure} scelta={scelta} sel={sel} onSel={setSel} tipo={tipo} />
        <AConfronto
          misure={misure}
          scelta={scelta}
          misura={cmp !== null && met.includes(cmp) ? cmp : (met[0] ?? "fwhm")}
          scelte={met}
          onMisura={setCmp}
          tipo={tipo}
          esiti={esiti}
          onOggetto={(o) => {
            setScelta({ ...scelta, gruppo: o })
            setSel(null)
          }}
        />
        <PerFiltro misure={misure} scelta={scelta} altra={altra} onFiltro={scegliFiltro} />
        <TiltCurvatura misure={misure} scelta={scelta} />
      </div>
    </div>
  )
}

/** Il valore di una tessera: FWHM e HFD in secondi d'arco e pixel, senza scala solo in pixel. */
function valore(x: Tessera, set: Insieme | undefined): { v: string; chiave: string } {
  const s = statistica(set, x.chiave)
  if (x.px) {
    const px = statistica(set, x.px)
    if (s?.median == null) return { v: scritto(x.px, px?.median), chiave: x.px }
    return {
      v: `${scritto(x.chiave, s.median)} \u00B7 ${scritto(x.px, px?.median)}`,
      chiave: x.chiave,
    }
  }
  if (x.id === "curvature") {
    const arc = statistica(set, "off_axis_arcsec")?.median
    return {
      v:
        arc == null
          ? scritto(x.chiave, s?.median)
          : `${scritto(x.chiave, s?.median)} \u00B7 ${scritto("off_axis_arcsec", arc)}`,
      chiave: x.chiave,
    }
  }
  return { v: scritto(x.chiave, s?.median), chiave: x.chiave }
}

function sotto(x: Tessera, set: Insieme | undefined, chiave: string): string {
  const s = statistica(set, chiave)
  const q = quartili(chiave, s)
  if (x.id === "fwhm") {
    const zenit = statistica(set, "fwhm_zenith_arcsec")?.median
    if (zenit != null) return t("measures.zenith", { v: scritto("fwhm_zenith_arcsec", zenit) })
  }
  if (x.id === "stars") {
    const sature = statistica(set, "saturated")?.median
    if (sature != null && q)
      return `${t("measures.saturated", { n: numero(Math.round(sature)) })} \u00B7 ${q}`
  }
  if (x.id === "sqm" && s?.median != null) return t("measures.sqm.unit")
  return q
}

type Tace = NonNullable<NonNullable<ReturnType<typeof statistica>>["silent"]>

// la tavola dice "in questa notte": nella finestra dell'oggetto la frase resta senza il luogo
const TACE: Record<Tace, Record<Tipo, Chiave>> = {
  measuring: { notte: "measures.pending", oggetto: "measures.pending" },
  no_value: { notte: "measures.none", oggetto: "measures.none" },
  sqm_not_this_filter: { notte: "measures.sqm.notThisFilter", oggetto: "measures.sqm.noLOrColour" },
  needs_camera_bias: { notte: "measures.sqm.needsBias", oggetto: "measures.sqm.needsBias" },
}

function UnaTessera({
  tessera: x,
  set,
  perFiltro,
  posto,
  tipo,
  onTocca,
}: {
  tessera: Tessera
  set: Insieme | undefined
  perFiltro: boolean
  posto: number
  tipo: Tipo
  onTocca: () => void
}) {
  const { v: v0, chiave } = valore(x, set)
  const s = statistica(set, chiave)
  const lato = x.id === PILASTRO ? latoDelPilastro(set) : null
  let v = lato?.v ?? v0
  let sub = lato?.sub ?? sotto(x, set, chiave)
  // tessera vuota: il perche' dall'API (tavola MisureFrame 236)
  if (!sub && s?.median == null && s?.silent) sub = t(TACE[s.silent][tipo])
  if (perFiltro) {
    v = t("measures.per.filter")
    sub = t("measures.per.filter.why")
  } else if (DAL_SETUP.has(x.chiave) && set?.differs.length) {
    v = t("measures.not.comparable")
    sub = t("measures.not.comparable.why", { r: diversi(set.differs) })
  }
  const fwhmPx = statistica(set, "fwhm_px")?.verdict
  const tag = x.id === "fwhm" && fwhmPx ? t(`measures.sampling.${fwhmPx as "ideal"}`) : ""
  const tilt = x.id === "tilt" ? s?.verdict : null
  const cielo = x.id === "sqm" && s?.sky_verdict ? CIELO[s.sky_verdict] : undefined
  const d = perFiltro ? "" : linea(s?.trend)
  const scelta =
    posto === 0
      ? "al-c-misure-frame__colonna-3--prima"
      : posto === 1
        ? "al-c-misure-frame__colonna-3--seconda"
        : ""
  return (
    <a
      className={`al-c-misure-frame__colonna-3 ${scelta}`}
      href="#"
      role="button"
      aria-pressed={posto >= 0 ? "true" : "false"}
      onClick={gesto(onTocca)}
    >
      <span className="al-c-misure-frame__riga-7">
        <span className="al-c-misure-frame__blocco-2">{nomeDi(x.id)}</span>
      </span>
      <span className="al-c-misure-frame__testo-5">{v}</span>
      {sub && <span className="al-c-misure-frame__testo-6">{sub}</span>}
      {tilt && (
        <span className="al-c-misure-frame__riga-8">
          <Pillola
            esito={ESITO[tilt] ?? 0}
            testo={t(`measures.tilt.${tilt as "go"}`)}
            dimensione="micro"
            fondo="carta"
          />
        </span>
      )}
      {cielo && (
        <span className="al-c-misure-frame__riga-8">
          <Pillola esito={cielo.esito} testo={t(cielo.chiave)} dimensione="micro" fondo="carta" />
        </span>
      )}
      {tag && <span className="al-c-misure-frame__blocco-3">{tag}</span>}
      {d && (
        <svg
          className="al-c-misure-frame__grafico-1"
          aria-hidden="true"
          width="100%"
          height="20"
          viewBox="0 0 100 30"
          preserveAspectRatio="none"
        >
          <path
            className={`al-c-misure-frame__spark ${posto === 0 ? "al-c-misure-frame__spark--prima" : ""}`}
            d={d}
            fill="none"
            strokeWidth="1.5"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      )}
    </a>
  )
}
