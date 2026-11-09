/**
 * Le misure dei frame di una notte (tavola v76, `componenti/MisureFrame.dc.html`, tipo
 * `notte`): le tessere con mediane e quartili, le altre misure, frame per frame, il frame
 * scelto, gli oggetti a confronto, la tabella per filtro, tilt e curvatura. Il componente
 * sceglie e scrive: i conti sono dell'API.
 */
import { type ChangeEvent, useState } from "react"

import { Pillola } from "./componenti/Pillola"
import { PillolaScelta, type OpzioneScelta } from "./componenti/PillolaScelta"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { nomeDelFiltro } from "./FiltriUsati"
import { numero, t } from "./i18n"
import {
  ALTRE,
  DAL_SETUP,
  ESITO,
  type Insieme,
  type Misure,
  type Scelta,
  TESSERE,
  type Tessera,
  diversi,
  filtriDi,
  insieme,
  tintaDi,
  linea,
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

export function MisureDellaNotte({ misure, formato }: { misure: Misure; formato: Formato }) {
  const tel = formato === "telefono"
  const [scelta, setScelta] = useState<Scelta>({ oggetto: null, filtro: null })
  const [altra, setAltra] = useState<string | null>(letta)
  const [met, setMet] = useState<string[]>(() => ["fwhm", "eccentricity"])
  const [cmp, setCmp] = useState<string | null>(null)
  const [sel, setSel] = useState<number | null>(null)

  const set = insieme(misure, scelta.oggetto, scelta.filtro)
  const tutti = insieme(misure, scelta.oggetto, null)
  const filtri = filtriDi(misure, scelta.oggetto)
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
      c: numero(insieme(misure, scelta.oggetto, f.name)?.frames ?? 0),
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
    if (v) {
      ora.push(v)
      if (ora.length > 2) ora.shift()
    }
    ricorda(v)
    setAltra(v)
    setMet(ora.length ? ora : ["fwhm"])
  }
  const isolato = scelta.oggetto
    ? (misure.objects.find((o) => o.key === scelta.oggetto)?.name ?? scelta.oggetto)
    : null
  const tessere = [
    ...TESSERE,
    ...(altra ? [{ id: altra, nome: "measures.other" as const, chiave: altra }] : []),
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
                onClick={() => setScelta({ ...scelta, oggetto: null })}
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
                altra={x.id === altra}
                perFiltro={statistica(set, x.chiave)?.per_filter === true}
                posto={met.indexOf(x.id)}
                onTocca={() => tocca(x.id)}
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
                        {v.pi ? `${t(v.nome)} \u00B7 ${v.pi}` : t(v.nome)}
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
        <IlFrame misure={misure} scelta={scelta} sel={sel} onSel={setSel} />
        <AConfronto
          misure={misure}
          scelta={scelta}
          misura={cmp !== null && met.includes(cmp) ? cmp : (met[0] ?? "fwhm")}
          scelte={met}
          onMisura={setCmp}
          onOggetto={(o) => {
            setScelta({ ...scelta, oggetto: o })
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

function UnaTessera({
  tessera: x,
  set,
  altra,
  perFiltro,
  posto,
  onTocca,
}: {
  tessera: Tessera
  set: Insieme | undefined
  altra: boolean
  perFiltro: boolean
  posto: number
  onTocca: () => void
}) {
  const { v: v0, chiave } = valore(x, set)
  const s = statistica(set, chiave)
  let v = v0
  let sub = sotto(x, set, chiave)
  // tessera vuota: il perche' dall'API (tavola: "non c'e' per questi frame")
  if (!sub && s?.median == null && s?.silent)
    sub = t(s.silent === "measuring" ? "measures.pending" : "measures.none")
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
        <span className="al-c-misure-frame__blocco-2">{altra ? nomeDi(x.id) : t(x.nome)}</span>
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
