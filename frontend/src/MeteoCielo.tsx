import { type KeyboardEvent, type MouseEvent, type TouchEvent, useState } from "react"

import { confiniDi, FasceDelCielo, OreDeiConfini, ScalaDelCielo } from "./CieloFasce"
import { ESITO } from "./DashboardDati"
import { type Chiave, numero, oraDelSito, t, unDecimale } from "./i18n"
import {
  type Codice,
  type Notte,
  type Ora,
  conUnita,
  disegnate,
  FORME,
  livelloDellOra,
  nelBuio,
  parola,
  quota,
} from "./MeteoDati"

/**
 * The sky of the night (board v82 `chart`): twilight bands to the minute, the three cloud layers,
 * the Transparency line and the measures switched on; a thread that carries every card to an hour.
 * Nothing is computed here: every number is an hour the backend wrote, placed on its scale.
 */

const W = 1000
const COLORE = ["var(--buono-testo)", "var(--incerto-testo)", "var(--non-adatto-testo)"] as const
const FONDO = ["var(--buono-fondo)", "var(--incerto-fondo)", "var(--non-adatto-fondo)"] as const
const SEGNO = ["\u2713", "!", "\u2715"] as const
const STRATI = [
  { campo: "cloud_high_pct", o: 0.1, so: 0.45, w: 1.25 },
  { campo: "cloud_mid_pct", o: 0.17, so: 0.6, w: 1.25 },
  { campo: "cloud_low_pct", o: 0.28, so: 0.9, w: 1.75 },
] as const

/** A measure on the chart: humidity in % on the left scale, one judged measure on the right. */
export type Accesa = "humidity" | Codice
export const UMIDITA = "var(--umidita)"

const y = (v: number) => 195 - (v / 100) * 185

function linea(punti: { x: number; v: number | null }[], yf: (v: number) => number): string {
  let d = ""
  let su = false
  for (const p of punti) {
    if (p.v === null) {
      su = false
      continue
    }
    d += `${su ? "L" : "M"}${p.x.toFixed(1)} ${yf(p.v).toFixed(1)} `
    su = true
  }
  return d
}

function area(punti: { x: number; v: number | null }[]): string {
  let d = ""
  let tratto: { x: number; v: number }[] = []
  const chiudi = () => {
    const a = tratto[0]
    const b = tratto[tratto.length - 1]
    if (a && b && tratto.length > 1) {
      d += `M${a.x.toFixed(1)} 195 ${tratto.map((p) => `L${p.x.toFixed(1)} ${y(p.v).toFixed(1)}`).join(" ")} L${b.x.toFixed(1)} 195 Z `
    }
    tratto = []
  }
  for (const p of punti) {
    if (p.v === null) chiudi()
    else tratto.push({ x: p.x, v: p.v })
  }
  chiudi()
  return d
}

export function MeteoCielo({
  notte: n,
  accese,
  ora,
  scegliOra,
  telefono,
  aria,
}: {
  notte: Notte
  accese: Accesa[]
  /** The hour the thread is on, as an index of the drawn hours; `null`: the night. */
  ora: number | null
  scegliOra: (i: number | null) => void
  telefono: boolean
  aria: string
}) {
  const [fuoco, setFuoco] = useState(false)
  const ore = disegnate(n)
  const t0 = Date.parse(n.shown_from ?? ore[0]?.at ?? "")
  const t1 = Date.parse(n.shown_until ?? ore[ore.length - 1]?.at ?? "")
  const x = (iso: string) => Math.min(W, Math.max(0, ((Date.parse(iso) - t0) / (t1 - t0 || 1)) * W))
  const punti = (f: (o: Ora) => number | null) => ore.map((o) => ({ x: x(o.at), v: f(o) }))
  const interattivo = !n.trend && ore.length > 0
  const PADL = telefono ? 28 : 36
  const PADR = telefono ? 8 : 12
  const CH = telefono ? 180 : 250

  const fasce = n.sky_bands ?? []
  const confini = confiniDi(fasce, x)
  const etichette = telefono ? confini.filter((c) => c.forte) : confini

  // the first hour without the clouds: hatched from there, and said
  const manca = n.trend ? -1 : ore.findIndex((o) => o.cloud_low_pct === null)
  const destra = accese.find((a): a is Codice => a !== "humidity")
  const forma = destra ? FORME[destra] : undefined
  const misura = destra ? n.measures.find((m) => m.code === destra) : undefined
  const yd = (v: number) => 185 - Math.max(0, Math.min(1, quota(misura, v))) * 160
  const umidita = accese.includes("humidity")
  const qui = ora === null ? undefined : ore[ora]
  const sinistra = qui ? x(qui.at) / 10 : 0

  const muovi = (ev: MouseEvent<HTMLDivElement> | TouchEvent<HTMLDivElement>) => {
    const r = ev.currentTarget.getBoundingClientRect()
    const cx = "touches" in ev ? (ev.touches[0]?.clientX ?? 0) : ev.clientX
    const fr = ((cx - r.left) / r.width) * W
    let migliore = 0
    ore.forEach((o, i) => {
      if (Math.abs(x(o.at) - fr) < Math.abs(x(ore[migliore]?.at ?? o.at) - fr)) migliore = i
    })
    if (migliore !== ora) scegliOra(migliore)
  }
  const tasto = (ev: KeyboardEvent<HTMLDivElement>) => {
    const ultima = ore.length - 1
    let i = ora ?? 0
    if (ev.key === "ArrowRight" || ev.key === "ArrowUp") i += 1
    else if (ev.key === "ArrowLeft" || ev.key === "ArrowDown") i -= 1
    else if (ev.key === "Home") i = 0
    else if (ev.key === "End") i = ultima
    else if (ev.key === "Escape") {
      scegliOra(null)
      return
    } else return
    ev.preventDefault()
    scegliOra(Math.max(0, Math.min(ultima, i)))
  }

  // the tooltip's rows: the Transparency, the three layers, the measures on, the hour's exposure
  const righe: { n: string; c: string; v: string }[] = []
  if (qui) {
    const pct = (v: number | null) =>
      v === null ? t("weather.card.unknown") : `${numero(Math.round(v))}%`
    righe.push({
      n: t("meteo.chart.transparency"),
      c: "var(--prot-barra)",
      v:
        qui.transparency == null ? t("weather.card.unknown") : numero(Math.round(qui.transparency)),
    })
    righe.push({ n: t("meteo.chart.low"), c: "var(--prot-testo)", v: pct(qui.cloud_low_pct) })
    righe.push({ n: t("meteo.chart.mid"), c: "var(--prot-tenue)", v: pct(qui.cloud_mid_pct) })
    righe.push({ n: t("meteo.chart.high"), c: "var(--prot-tenue)", v: pct(qui.cloud_high_pct) })
    if (umidita) righe.push({ n: t("meteo.chart.humidity"), c: UMIDITA, v: pct(qui.humidity_pct) })
    if (destra && forma) {
      const v = qui[forma.campo]
      const lv = livelloDellOra(qui, destra)
      righe.push({
        n: t(`weather.measure.${destra}` as Chiave),
        c: "var(--prot-testo)",
        v:
          v === null
            ? t("weather.card.unknown")
            : `${conUnita(destra, v)}${lv ? ` \u00b7 ${parola(destra, lv)}` : ""}`,
      })
      if (destra === "condensation") {
        righe.push({
          n: t("meteo.chart.dewThreshold"),
          c: "var(--prot-tenue)",
          v: conUnita(destra, qui.dew_threshold_c ?? null),
        })
      }
    }
    righe.push({
      n: t("meteo.chart.sky"),
      c: "var(--prot-barra)",
      v:
        qui.exposure_hours != null
          ? t("meteo.chart.exposure", { n: unDecimale(qui.exposure_hours) })
          : nelBuio(qui, n)
            ? t("weather.card.unknown")
            : t("meteo.chart.outside"),
    })
  }
  const valori = righe.map((r) => `${r.n} ${r.v}`).join(", ")
  const oraQui = qui ? oraDelSito(qui.at) : ""

  // the right measure's word where it changes inside the window
  const parole: { x: number; v: number; lv: NonNullable<ReturnType<typeof livelloDellOra>> }[] = []
  if (destra && forma) {
    let prima: string | null = null
    for (const o of ore) {
      const v = o[forma.campo]
      const lv = livelloDellOra(o, destra)
      if (v === null || !nelBuio(o, n) || !lv) {
        prima = null
        continue
      }
      if (lv !== prima) parole.push({ x: x(o.at), v, lv })
      prima = lv
    }
  }
  const segmenti: { d: string; c: string; dentro: boolean }[] = []
  if (destra && forma) {
    ore.slice(0, -1).forEach((o, i) => {
      const b = ore[i + 1]
      const va = o[forma.campo]
      const vb = b?.[forma.campo] ?? null
      if (!b || va === null || vb === null) return
      const lv = livelloDellOra(o, destra)
      const dentro = nelBuio(o, n)
      segmenti.push({
        d: `M${x(o.at).toFixed(1)} ${yd(va).toFixed(1)} L${x(b.at).toFixed(1)} ${yd(vb).toFixed(1)}`,
        c: dentro && lv ? COLORE[ESITO[lv]] : "var(--prot-tenue)",
        dentro,
      })
    })
  }
  const media = n.cloud_total_pct ?? 0
  const buio = fasce.filter((b) => b.kind === "dark")
  const primoBuio = buio[0]
  const ultimoBuio = buio[buio.length - 1]

  return (
    <div style={{ position: "relative", paddingTop: 34 }}>
      <OreDeiConfini confini={etichette} sinistra={PADL} destra={PADR} />
      <div style={{ position: "relative", height: CH }}>
        <ScalaDelCielo etichette={["100%", "50%", "0"]} />
        <div
          onMouseMove={interattivo ? muovi : undefined}
          onMouseLeave={interattivo && !telefono ? () => scegliOra(null) : undefined}
          onTouchStart={interattivo ? muovi : undefined}
          onTouchMove={interattivo ? muovi : undefined}
          onKeyDown={interattivo ? tasto : undefined}
          onFocus={() => setFuoco(true)}
          onBlur={() => setFuoco(false)}
          tabIndex={interattivo ? 0 : -1}
          role={interattivo ? "slider" : "img"}
          aria-label={aria}
          aria-valuemin={interattivo ? 0 : undefined}
          aria-valuemax={interattivo ? ore.length - 1 : undefined}
          aria-valuenow={interattivo ? (ora ?? 0) : undefined}
          aria-valuetext={
            interattivo && qui ? t("meteo.chart.at", { ora: oraQui, valori }) : undefined
          }
          style={{
            position: "absolute",
            left: PADL,
            right: PADR,
            top: 0,
            bottom: 0,
            cursor: interattivo ? "crosshair" : "default",
            touchAction: "pan-y",
            outline: fuoco && interattivo ? "2px solid var(--prot-testo)" : "none",
            outlineOffset: 6,
            borderRadius: 8,
          }}
        >
          <svg
            viewBox="0 0 1000 200"
            preserveAspectRatio="none"
            aria-hidden="true"
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              overflow: "visible",
            }}
          >
            <defs>
              <pattern
                id={`meteo-manca-${n.night}`}
                width={6}
                height={6}
                patternUnits="userSpaceOnUse"
                patternTransform="rotate(45)"
              >
                <line
                  x1={0}
                  y1={0}
                  x2={0}
                  y2={6}
                  stroke="var(--prot-tenue)"
                  strokeOpacity={0.5}
                  strokeWidth={1.5}
                />
              </pattern>
            </defs>
            <FasceDelCielo fasce={fasce} confini={confini} x={x} />
            {!n.trend &&
              STRATI.map((s) => {
                const p = punti((o) => o[s.campo])
                return (
                  <g key={s.campo}>
                    <path d={area(p)} fill="var(--prot-testo)" fillOpacity={s.o} />
                    <path
                      d={linea(p, y)}
                      fill="none"
                      stroke="var(--prot-testo)"
                      strokeOpacity={s.so}
                      strokeWidth={s.w}
                      vectorEffect="non-scaling-stroke"
                      strokeLinejoin="round"
                    />
                  </g>
                )
              })}
            {manca >= 0 && ore[manca] && (
              <rect
                x={x(ore[manca]?.at ?? "")}
                y={0}
                width={W - x(ore[manca]?.at ?? "")}
                height={195}
                fill={`url(#meteo-manca-${n.night})`}
              />
            )}
            {!n.trend && (
              <>
                <path
                  d={linea(
                    punti((o) => o.transparency ?? null),
                    y,
                  )}
                  fill="none"
                  stroke="var(--prot-barra)"
                  strokeWidth={6}
                  strokeOpacity={0.14}
                  vectorEffect="non-scaling-stroke"
                  strokeLinecap="round"
                />
                <path
                  d={linea(
                    punti((o) => o.transparency ?? null),
                    y,
                  )}
                  fill="none"
                  stroke="var(--prot-barra)"
                  strokeWidth={1.75}
                  vectorEffect="non-scaling-stroke"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </>
            )}
            {umidita && (
              <path
                d={linea(
                  punti((o) => o.humidity_pct),
                  y,
                )}
                fill="none"
                stroke={UMIDITA}
                strokeWidth={1.75}
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
              />
            )}
            {destra === "condensation" && (
              <path
                d={linea(
                  punti((o) => o.dew_threshold_c ?? null),
                  yd,
                )}
                fill="none"
                stroke="var(--prot-tenue)"
                strokeWidth={1.5}
                strokeDasharray="5 4"
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
              />
            )}
            {segmenti.map((s, k) => (
              <path
                key={k}
                d={s.d}
                fill="none"
                stroke={s.c}
                strokeOpacity={s.dentro ? 1 : 0.45}
                strokeWidth={s.dentro ? 2.5 : 1.25}
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
              />
            ))}
            {n.trend && primoBuio && ultimoBuio && (
              <line
                x1={x(primoBuio.starts_at)}
                x2={x(ultimoBuio.ends_at)}
                y1={y(media)}
                y2={y(media)}
                stroke="var(--prot-testo)"
                strokeWidth={1.75}
                strokeDasharray="6 5"
                vectorEffect="non-scaling-stroke"
              />
            )}
          </svg>
          {manca >= 0 && ore[manca] && (
            <span
              style={{
                position: "absolute",
                left: `${x(ore[manca]?.at ?? "") / 10 + 1}%`,
                top: 8,
                fontSize: 11,
                color: "var(--prot-testo)",
                background: "var(--prot-fondo)",
                borderRadius: 8,
                padding: "2px 6px",
              }}
            >
              {t("meteo.chart.missing", { ora: oraDelSito(ore[manca]?.at ?? "") })}
            </span>
          )}
          {n.trend && n.sky_word && (
            <span
              style={{
                position: "absolute",
                left: "21%",
                top: `calc(${y(media) / 2}% - 24px)`,
                fontSize: 12,
                color: "var(--prot-testo)",
              }}
            >
              {t("meteo.chart.trend", {
                cielo: t(`weather.sky.word.${n.sky_word}`),
                pct: numero(Math.round(media)),
              })}
            </span>
          )}
          {parole.map((p) => (
            <span
              key={`w${p.x}`}
              style={{
                position: "absolute",
                left: `${p.x / 10}%`,
                top: `${yd(p.v) / 2}%`,
                transform: "translate(-10%,-140%)",
                background: FONDO[ESITO[p.lv]],
                color: COLORE[ESITO[p.lv]],
                borderRadius: 999,
                padding: "1px 7px",
                fontSize: 11,
                fontWeight: 600,
                whiteSpace: "nowrap",
                pointerEvents: "none",
                boxShadow: "0 0 0 2px var(--prot-fondo)",
              }}
            >
              {SEGNO[ESITO[p.lv]]} {destra ? parola(destra, p.lv) : ""}
            </span>
          ))}
          {destra &&
            misura &&
            misura.axis_max !== null &&
            misura.axis_min !== null &&
            [
              [misura.axis_max, 12.5],
              [misura.axis_min, 92.5],
            ].map(([v, top]) => (
              <span
                key={`ax${top}`}
                style={{
                  position: "absolute",
                  right: 0,
                  top: `${top}%`,
                  transform: "translate(calc(100% + 4px),-50%)",
                  fontSize: 11,
                  color: "var(--prot-tenue)",
                  whiteSpace: "nowrap",
                  pointerEvents: "none",
                }}
              >
                {conUnita(destra, v ?? 0)}
              </span>
            ))}
          {interattivo && qui && (
            <>
              <span
                style={{
                  position: "absolute",
                  left: `${sinistra}%`,
                  top: 0,
                  bottom: 0,
                  borderLeft: "1.5px dashed var(--prot-tenue)",
                  pointerEvents: "none",
                }}
              />
              {qui.transparency != null && (
                <span
                  style={{
                    position: "absolute",
                    left: `${sinistra}%`,
                    top: `${y(qui.transparency) / 2}%`,
                    width: 11,
                    height: 11,
                    marginLeft: -5.5,
                    marginTop: -5.5,
                    borderRadius: "50%",
                    background: "var(--punto-chiaro)",
                    boxShadow: "0 0 0 2px var(--prot-barra)",
                    pointerEvents: "none",
                  }}
                />
              )}
              <div
                className="al-riquadro al-riquadro--lista"
                role="tooltip"
                style={{
                  position: "absolute",
                  top: telefono ? -10 : 4,
                  left: telefono ? 0 : `${sinistra}%`,
                  transform: telefono
                    ? "translateY(-100%)"
                    : sinistra > 60
                      ? "translateX(calc(-100% - 14px))"
                      : "translateX(14px)",
                  zIndex: 3,
                }}
              >
                <b style={{ fontWeight: 600, fontSize: 13 }}>
                  {t("meteo.card.at", { ora: oraQui })}
                </b>
                {righe.map((r) => (
                  <span key={r.n} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <i style={{ width: 8, height: 8, borderRadius: "50%", background: r.c }} />
                    <span style={{ flex: 1 }}>{r.n}</span>
                    <b style={{ fontWeight: 600, marginLeft: 12 }}>{r.v}</b>
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

/** The hours under the chart: every two hours, every four on the phone. */
export function oreSotto(n: Notte, telefono: boolean): string[] {
  const passo = telefono ? 4 : 2
  return disegnate(n)
    .map((o) => oraDelSito(o.at))
    .filter((o) => o.endsWith(":00") && Number(o.slice(0, 2)) % passo === 0)
    .map((o) => o.slice(0, 2))
}
