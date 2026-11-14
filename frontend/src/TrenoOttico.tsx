import { useState, type CSSProperties } from "react"

import { useLarghezza } from "./colonna"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import type { components } from "./api/schema"
import {
  disegnoDelTreno,
  type Etichetta,
  type Pezzo,
  type Ruolo,
  type Treno,
} from "./disegnoDelTreno"
import { t } from "./i18n"
import { MISURE_DETTAGLIO } from "./misureDelSetup"

type Pagina = components["schemas"]["GearList"]
type Corredo = components["schemas"]["RigOnPage"]
type Strumento = components["schemas"]["InstrumentOnPage"]

const VE = "non-scaling-stroke"

/** I pezzi che i conti leggono (`pieces`), con le voci della scheda che il disegno usa.
 *  Senza ottica non c'e' treno (tavola `trenoDi`, 333). */
export function trenoDelSetup(pagina: Pagina, setup: Corredo): Treno | null {
  const p = setup.pieces
  if (!p) return null
  const di = (id: number | null, ruolo?: Ruolo): Pezzo | undefined => {
    const s = pagina.instruments.find((x: Strumento) => x.id === id)
    if (!s) return undefined
    return {
      id: s.id,
      nome: s.name,
      ruolo: ruolo ?? (s.kind as Ruolo),
      schema: s.optical_design,
      apertura: s.aperture_mm,
      focale: s.focal_mm,
      spessore: s.thickness_mm,
      posizioni: s.slots,
      aColori: s.camera_type === "color",
    }
  }
  const ott = di(p.optics, "optics")
  if (!ott) return null
  const guida = di(p.guide)
  return {
    ott,
    foc: di(p.focuser, "focuser"),
    rid: di(p.reducer, "reducer"),
    oag: guida?.ruolo === "oag" ? guida : undefined,
    gs: guida?.ruolo === "guide_scope" ? guida : undefined,
    dist: p.spacers.map((id) => di(id, "spacer")).filter((x): x is Pezzo => x !== undefined),
    ruota: di(p.wheel, "filter_wheel"),
    cam: di(p.camera, "camera"),
    camG: di(p.guide_camera, "guide_camera"),
  }
}

/**
 * Il **treno ottico** del setup (tavola v82, 63-66): l'esploso a linee, le pillole coi nomi sopra
 * e sotto legate al pezzo da un filo; pezzo e pillola si accendono insieme e il tocco apre il pezzo
 * fra i componenti. Sul telefono, o quando i nomi di una riga non entrano, le pillole portano il
 * numero e sotto c'e' la legenda.
 */
export function TrenoOttico({
  treno,
  nome,
  formato,
  onVai,
}: {
  treno: Treno
  nome: string
  formato: Formato
  onVai: (pezzo: number) => void
}) {
  const m = MISURE_DETTAGLIO[formato]
  const telefono = formato === "telefono"
  const [acceso, setAcceso] = useState<number | null>(null)
  // the labels are pushed apart in real pixels
  const [larga, misura] = useLarghezza(4)
  const d = disegnoDelTreno(treno, larga || undefined, telefono)
  const v = d.vista
  const tipo = (p: Pezzo) => t(`review.kind.${p.ruolo}`)
  const luce = (id: number) => ({
    onMouseEnter: () => setAcceso(id),
    onMouseLeave: () => setAcceso(null),
    onFocus: () => setAcceso(id),
    onBlur: () => setAcceso(null),
  })
  const spento = (id: number) => acceso !== null && acceso !== id
  const pillola = (l: Etichetta, su: boolean) => {
    const on = acceso === l.pezzo.id
    const stile: CSSProperties = {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      gap: 6,
      boxSizing: "border-box",
      whiteSpace: "nowrap",
      width: "max-content",
      borderRadius: 999,
      background: on ? "var(--scelta)" : "var(--carta)",
      color: on ? "var(--scelta-testo)" : "var(--testo)",
      fontSize: 12,
      fontWeight: 600,
      transition: "background .15s",
      position: "absolute",
      left: `${((l.x - v.x) / v.w) * 100}%`,
      [su ? "bottom" : "top"]: 0,
      transform: "translateX(-50%)",
      height: 28,
      minWidth: d.coiNumeri ? 28 : 0,
      padding: d.coiNumeri ? 0 : "0 11px",
    }
    return (
      <a
        key={`l${l.pezzo.id}`}
        href="#"
        onClick={gesto(() => onVai(l.pezzo.id))}
        {...luce(l.pezzo.id)}
        aria-label={t("gear.train.open", { tipo: tipo(l.pezzo), nome: l.pezzo.nome })}
        style={stile}
      >
        {d.coiNumeri ? String(l.numero) : l.pezzo.nome}
      </a>
    )
  }
  const riga = (arr: Etichetta[], su: boolean) => (
    <div style={{ position: "relative", height: 30 }}>{arr.map((l) => pillola(l, su))}</div>
  )
  return (
    <section
      className="al-attr__colonna-10"
      aria-labelledby="dt-treno"
      style={{ borderRadius: m.angolo, padding: m.dentro }}
    >
      <div className="al-attr__riga-19">
        <h3 className="al-attr__testo-2" id="dt-treno">
          {t("gear.train")}
        </h3>
        <span className="al-attr__testo-12">{t("gear.train.note")}</span>
      </div>
      <div className="al-attr__riquadro-1" style={{ padding: telefono ? "10px 6px" : "18px 16px" }}>
        <div ref={misura} style={{ maxWidth: d.larghezzaMassima, margin: "0 auto" }}>
          {riga(d.su, true)}
          <svg
            viewBox={`${v.x} ${v.y} ${v.w} ${v.h}`}
            width="100%"
            role="group"
            aria-label={t("gear.train.label", { nome })}
            style={{ display: "block" }}
          >
            <path
              d={d.asse}
              fill="none"
              stroke="var(--tenue)"
              strokeOpacity={0.6}
              strokeDasharray="10 4 2 4"
              vectorEffect={VE}
              pointerEvents="none"
            />
            {[...d.su, ...d.giu].map((l) => {
              const on = acceso === l.pezzo.id
              return (
                <g
                  key={`f${l.pezzo.id}`}
                  pointerEvents="none"
                  stroke={on ? "var(--accento)" : "var(--tenue)"}
                  strokeOpacity={spento(l.pezzo.id) ? 0.3 : 0.8}
                >
                  <path d={l.filo} fill="none" vectorEffect={VE} strokeWidth={on ? 1.6 : 1} />
                  <path
                    d={`M${l.punto[0] - 3} ${l.punto[1]}a3 3 0 1 0 6 0a3 3 0 1 0 -6 0`}
                    fill={on ? "var(--accento)" : "var(--tenue)"}
                    stroke="none"
                  />
                </g>
              )
            })}
            {d.gruppi.map((g) => {
              const id = g.pezzo.id
              const on = acceso === id
              return (
                <g
                  key={`g${id}`}
                  role="button"
                  tabIndex={0}
                  aria-label={t("gear.train.piece", { tipo: tipo(g.pezzo), nome: g.pezzo.nome })}
                  onClick={() => onVai(id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault()
                      onVai(id)
                    }
                  }}
                  {...luce(id)}
                  stroke={on ? "var(--accento)" : "var(--testo)"}
                  strokeWidth={on ? 2 : 1.1}
                  opacity={spento(id) ? 0.3 : 1}
                  style={{ cursor: "pointer", transition: "opacity .15s", outline: "none" }}
                >
                  {g.tratti.map((x, k) => (
                    <path
                      key={k}
                      d={x.d}
                      fill={x.pieno ? "var(--carta-2)" : "none"}
                      strokeOpacity={x.opacita}
                      vectorEffect={VE}
                      strokeLinejoin="round"
                      strokeLinecap="round"
                      pathLength={1}
                      strokeDasharray={1}
                      style={{ animation: "alDraw .9s cubic-bezier(.3,.6,.2,1) both" }}
                    />
                  ))}
                </g>
              )
            })}
          </svg>
          {riga(d.giu, false)}
        </div>
        {d.coiNumeri && <Legenda voci={d.legenda} acceso={acceso} onVai={onVai} />}
      </div>
    </section>
  )
}

function Legenda({
  voci,
  acceso,
  onVai,
}: {
  voci: Etichetta[]
  acceso: number | null
  onVai: (pezzo: number) => void
}) {
  return (
    <ul
      style={{
        listStyle: "none",
        margin: "12px 0 0",
        padding: 0,
        display: "grid",
        gridTemplateColumns: "repeat(2,minmax(0,1fr))",
        gap: 6,
      }}
    >
      {voci.map((l) => {
        const on = acceso === l.pezzo.id
        return (
          <li key={l.pezzo.id} style={{ display: "flex", minWidth: 0 }}>
            <a
              href="#"
              onClick={gesto(() => onVai(l.pezzo.id))}
              style={{
                flex: 1,
                minWidth: 0,
                display: "flex",
                alignItems: "center",
                gap: 8,
                minHeight: 44,
                boxSizing: "border-box",
                padding: "0 12px 0 8px",
                borderRadius: 16,
                background: on ? "var(--scelta)" : "var(--carta)",
                color: on ? "var(--scelta-testo)" : "var(--testo)",
                fontSize: 13,
              }}
            >
              <span
                style={{
                  width: 22,
                  height: 22,
                  flex: "none",
                  borderRadius: "50%",
                  boxShadow: "inset 0 0 0 1.5px currentColor",
                  display: "grid",
                  placeItems: "center",
                  fontSize: 11,
                  fontWeight: 700,
                }}
              >
                {String(l.numero)}
              </span>
              <span
                style={{
                  minWidth: 0,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {l.pezzo.nome}
              </span>
            </a>
          </li>
        )
      })}
    </ul>
  )
}
