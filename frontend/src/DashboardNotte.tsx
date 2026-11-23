import { type KeyboardEvent, type MouseEvent, type TouchEvent, useState } from "react"

import { confiniDi, FasceDelCielo, OreDeiConfini, ScalaDelCielo } from "./CieloFasce"
import { Carta } from "./componenti/Carta"
import { PillolaScelta } from "./componenti/PillolaScelta"
import { Ripresa } from "./componenti/Ripresa"
import type { Formato } from "./componenti/Tema"
import {
  type Breve,
  type NotteMeteo,
  type Stanotte,
  nomeDellaBanda,
  orePosa,
  pillolaDellaNotte,
  ripresaDiStanotte,
  sottoDellaNotte,
} from "./DashboardDati"
import { quotaSulloZenit, ZENIT_DEG } from "./disegnoDellaLuna"
import { giornoDelMese, numero, oraDelSito, oreEMinuti, t } from "./i18n"
import { buioDellaNotte, trattiDelBuio, trattiSenzaLuna } from "./Stanotte"

/**
 * The Dashboard's big card (board v79): tonight's chart, the Night view (Transparency hour by hour
 * and the Moon) or the Solar System one (the four planets and the Moon). Times and heights arrive
 * from `/tonight` and `/weather`; here they are only placed on the chart.
 */

type Vista = "notte" | "sole"
type Serie = {
  n: string
  punti: { x: number; v: number }[]
  c: string
  tratteggio?: boolean
  scrivi: (v: number) => string
}

const W = 1000
const PIANETI = ["saturn", "jupiter", "mars", "venus"] as const
const COLORE_PIANETA = {
  saturn: "var(--pianeta-0)",
  jupiter: "var(--pianeta-1)",
  mars: "var(--pianeta-2)",
  venus: "var(--pianeta-3)",
}
const LUNA = "var(--luna-linea)"
const TRATTEGGIO = "repeating-linear-gradient(135deg, var(--prot-tenue) 0 3px, transparent 3px 8px)"
const ESITI = [
  { bg: "var(--buono-fondo)", fg: "var(--buono-testo)" },
  { bg: "var(--incerto-fondo)", fg: "var(--incerto-testo)" },
  { bg: "var(--non-adatto-fondo)", fg: "var(--non-adatto-testo)" },
]
const NEUTRA = { bg: "var(--carta-2)", fg: "var(--testo)" }

type Testa = {
  label: string
  value: string
  pill: string
  tinta: { bg: string; fg: string }
  sub: string
}

const sottoOrizzonte = (a: number) =>
  a < 0 ? t("dashboard.chart.below") : `${numero(Math.round(a))}\u00b0`

/** The head of the Night view: exposure hours, or what is known without the forecast. */
function testaDellaNotte(s: Stanotte, w: Breve | null): Testa {
  if (s.night === null) {
    return {
      label: t("dashboard.head.dark"),
      value: "?",
      pill: t("dashboard.head.noZone.pill"),
      tinta: NEUTRA,
      sub: t("dashboard.head.noZone.sub"),
    }
  }
  if (s.dark_s === 0) {
    return {
      label: t("dashboard.head.dark"),
      value: t("weather.verdict.noNight"),
      pill: t("dashboard.head.polar.pill"),
      tinta: NEUTRA,
      sub: s.dark_returns
        ? t("dashboard.head.polar.subUntil", { data: giornoDelMese(s.dark_returns) })
        : t("dashboard.head.polar.sub"),
    }
  }
  if (!w || !w.verdict || w.exposure_hours == null) {
    return {
      label: t("dashboard.head.darkComputed"),
      value: s.dark_s ? oreEMinuti(s.dark_s) : "?",
      pill: t("dashboard.head.noWeather.pill"),
      tinta: NEUTRA,
      sub: [buioDellaNotte(s), t("dashboard.head.noWeather.sub")].filter(Boolean).join(" \u00b7 "),
    }
  }
  const p = pillolaDellaNotte(w.verdict)
  return {
    label: t("dashboard.head.exposure"),
    value: orePosa(w.exposure_hours),
    pill: p.testo,
    tinta: ESITI[p.esito] ?? NEUTRA,
    sub: sottoDellaNotte(s, w),
  }
}

/** The head of the Solar System view: the highest planet tonight and the others' rise or set. */
function testaDelSole(s: Stanotte): Testa | null {
  // the backend chose it (`highest_planet`): here it is only found by its key
  const alto = s.planets.find((p) => p.key === s.highest_planet)
  const h = alto?.highest
  if (!alto || !h) return null
  const altri = s.planets
    .filter((p) => p !== alto)
    .map((p) => quandoDelPianeta(p))
    .filter(Boolean)
  return {
    label: t("dashboard.head.solar"),
    value: t(`dashboard.chart.planet.${alto.key}`),
    pill: t("dashboard.head.solar.pill", {
      gradi: numero(Math.round(h.altitude_deg)),
      ora: oraDelSito(h.at),
    }),
    tinta: { bg: "var(--scelta)", fg: "var(--scelta-testo)" },
    sub: altri.join(" \u00b7 "),
  }
}

/** "Giove sorge alle 22:10" in the head, "sorge 22:10" in the legend. */
function quandoDelPianeta(p: Stanotte["planets"][number], conNome = true): string {
  const nome = t(`dashboard.chart.planet.${p.key}`)
  const k = conNome ? "" : ".short"
  if (p.rise) return t(`dashboard.planet.rises${k}`, { nome, ora: oraDelSito(p.rise) })
  if (p.set) return t(`dashboard.planet.sets${k}`, { nome, ora: oraDelSito(p.set) })
  if (!p.highest) return ""
  return t(`dashboard.planet.top${k}`, { nome, gradi: numero(Math.round(p.highest.altitude_deg)) })
}

/** The legend's dark: "20:48-05:48, senza Luna 20:48-23:40". */
function notaDelBuio(s: Stanotte): string {
  const buio = trattiDelBuio(s)
  const senza = trattiSenzaLuna(s)
  const parti = buio ? [buio] : []
  if (senza) parti.push(t("frame.tonight.moonless", { tratti: senza }))
  return parti.join(" \u00b7 ")
}

/** "sorge 09:49" or "sorge domani 09:49": after the night's date it is tomorrow. */
export function quandoDellEvento(s: Stanotte, k: "rise" | "set" | "at", istante: string): string {
  const domani = s.night !== null && istante.slice(0, 10) > s.night
  return t(`dashboard.moon.${k}${domani ? ".tomorrow" : ""}`, { ora: oraDelSito(istante) })
}

/** "sorge 23:40, tramonta domani 15:17" in time order, or the Moon that does not rise or set. */
export function quandoDellaLuna(s: Stanotte): string {
  const l = s.moon
  if (!l) return ""
  if (!l.rise && !l.set)
    return l.highest.altitude_deg < 0 ? t("dashboard.moon.never") : t("dashboard.moon.always")
  const eventi = [
    ...(l.rise ? [{ k: "rise" as const, at: l.rise }] : []),
    ...(l.set ? [{ k: "set" as const, at: l.set }] : []),
  ].sort((a, b) => Date.parse(a.at) - Date.parse(b.at))
  const detti = eventi.map((e) => quandoDellEvento(s, e.k, e.at))
  if (!l.rise) detti.push(t("dashboard.moon.noRiseTonight"))
  if (!l.set) detti.push(t("dashboard.moon.noSetTonight"))
  return detti.join(" \u00b7 ")
}

export function DashboardNotte({
  stanotte: s,
  notte,
  formato,
}: {
  stanotte: Stanotte
  notte: NotteMeteo | undefined
  formato: Formato
}) {
  const tel = formato === "telefono"
  const [vista, setVista] = useState<Vista>("notte")
  const [sopra, setSopra] = useState<number | null>(null)
  const [fuoco, setFuoco] = useState(false)
  const chart = s.chart
  const w = s.weather ?? null
  const sole = testaDelSole(s)
  const v: Vista = vista === "sole" && sole ? "sole" : "notte"
  const testa = v === "sole" && sole ? sole : testaDellaNotte(s, w)
  const rip = v === "notte" ? ripresaDiStanotte(s) : null
  const t0 = chart ? Date.parse(chart.starts_at) : 0
  const t1 = chart ? Date.parse(chart.ends_at) : 1
  const x = (iso: string) => Math.min(W, Math.max(0, ((Date.parse(iso) - t0) / (t1 - t0)) * W))
  const dentro = (iso: string) => {
    const ms = Date.parse(iso)
    return ms >= t0 && ms <= t1
  }
  const passi = (s.moon?.track ?? []).filter((p) => dentro(p.at))
  const vmax = v === "notte" ? 100 : ZENIT_DEG
  const ore = (notte?.hours ?? []).filter((o) => o.transparency != null && dentro(o.at))
  const luna: Serie = {
    n: t("dashboard.chart.moon.name"),
    punti: passi.map((p) => ({
      x: x(p.at),
      v: v === "notte" ? quotaSulloZenit(p.altitude_deg) : p.altitude_deg < 0 ? -1 : p.altitude_deg,
    })),
    c: LUNA,
    tratteggio: true,
    scrivi: (i) => {
      const p = passi[i]
      if (!p) return ""
      const ms = Date.parse(p.at)
      const tratto = (s.shooting ?? []).find(
        (x) => Date.parse(x.starts_at) <= ms && ms < Date.parse(x.ends_at),
      )
      return (
        sottoOrizzonte(p.altitude_deg) +
        (p.altitude_deg >= 0 && s.moon
          ? t("dashboard.chart.moon.lit", { pct: numero(s.moon.illumination_pct) })
          : "") +
        (tratto ? ` \u00b7 ${nomeDellaBanda(tratto.band)}` : "")
      )
    },
  }
  const serie: Serie[] =
    v === "notte"
      ? [
          ...(ore.length
            ? [
                {
                  n: t("dashboard.chart.transparency"),
                  punti: ore.map((o) => ({
                    x: x(o.at) + (3600000 / (t1 - t0)) * W * 0.5,
                    v: o.transparency ?? 0,
                  })),
                  c: "var(--prot-barra)",
                  scrivi: (i: number) => {
                    const at = passi[i]?.at
                    const o = at
                      ? ore.find(
                          (h) =>
                            Date.parse(h.at) <= Date.parse(at) &&
                            Date.parse(at) < Date.parse(h.at) + 3600000,
                        )
                      : undefined
                    return o?.transparency != null
                      ? numero(Math.round(o.transparency))
                      : t("dashboard.chart.unknown")
                  },
                },
              ]
            : []),
          luna,
        ]
      : [
          ...PIANETI.flatMap((k) => {
            const p = s.planets.find((q) => q.key === k)
            if (!p) return []
            const punti = p.track.filter((q) => dentro(q.at))
            return [
              {
                n: t(`dashboard.chart.planet.${k}`),
                punti: punti.map((q) => ({ x: x(q.at), v: q.altitude_deg })),
                c: COLORE_PIANETA[k],
                scrivi: (i: number) => {
                  const at = passi[i]?.at
                  const q = at ? punti.find((r) => Date.parse(r.at) === Date.parse(at)) : undefined
                  return q ? sottoOrizzonte(q.altitude_deg) : t("dashboard.chart.unknown")
                },
              },
            ]
          }),
          luna,
        ]
  const y = (val: number) => 195 - (val / vmax) * 185
  const linea = (punti: Serie["punti"]) => {
    let d = ""
    let su = false
    for (const p of punti) {
      if (p.v < 0) {
        su = false
        continue
      }
      d += `${su ? "L" : "M"}${p.x.toFixed(1)} ${y(p.v).toFixed(1)} `
      su = true
    }
    return d
  }
  // dove la linea disegnata passa all'ascissa `xx`: fuori dai suoi tratti, null
  const sullaLinea = (punti: Serie["punti"], xx: number) => {
    const k = punti.findIndex((p) => p.x >= xx)
    const b = punti[k]
    const a = punti[k - 1]
    if (b && b.x === xx) return b.v < 0 ? null : b.v
    if (!a || !b || a.v < 0 || b.v < 0) return null
    return a.v + ((b.v - a.v) * (xx - a.x)) / (b.x - a.x)
  }
  const prima = serie[0]
  const area =
    prima && v === "notte" && ore.length
      ? `M${prima.punti[0]?.x ?? 0} 195 ${prima.punti.map((p) => `L${p.x.toFixed(1)} ${y(p.v).toFixed(1)}`).join(" ")} L${prima.punti[prima.punti.length - 1]?.x ?? 0} 195 Z`
      : ""

  const fasce = s.sky_bands.filter(
    (b) => Date.parse(b.ends_at) > t0 && Date.parse(b.starts_at) < t1,
  )
  const confini = confiniDi(fasce, x)
  const mostrati = tel
    ? confini.filter((_, k) => k === 0 || k === confini.length - 1 || confini[k]?.forte)
    : confini
  const N = passi.length
  const idx =
    sopra ??
    Math.max(
      0,
      passi.findIndex((p) => chart?.dark_from && Date.parse(p.at) >= Date.parse(chart.dark_from)),
    )
  const qui = passi[idx]
  const sinistra = qui ? x(qui.at) / 10 : 0
  const PADL = tel ? 28 : 36
  const CH = tel ? 180 : 220
  const muovi = (ev: MouseEvent<HTMLDivElement> | TouchEvent<HTMLDivElement>) => {
    const r = ev.currentTarget.getBoundingClientRect()
    const cx = "touches" in ev ? (ev.touches[0]?.clientX ?? 0) : ev.clientX
    const fr = (cx - r.left) / r.width
    let migliore = 0
    passi.forEach((p, i) => {
      if (Math.abs(x(p.at) / W - fr) < Math.abs(x(passi[migliore]?.at ?? p.at) / W - fr))
        migliore = i
    })
    if (migliore !== sopra) setSopra(migliore)
  }
  const tasto = (ev: KeyboardEvent<HTMLDivElement>) => {
    const passo = ev.shiftKey ? 4 : 1
    let i = sopra ?? idx
    if (ev.key === "ArrowRight" || ev.key === "ArrowUp") i += passo
    else if (ev.key === "ArrowLeft" || ev.key === "ArrowDown") i -= passo
    else if (ev.key === "Home") i = 0
    else if (ev.key === "End") i = N - 1
    else return
    ev.preventDefault()
    setSopra(Math.max(0, Math.min(N - 1, i)))
  }
  const ora = qui ? oraDelSito(qui.at) : ""
  const valori = serie.map((sr) => `${sr.n} ${sr.scrivi(idx)}`).join(", ")
  const viste = [
    {
      l: t("dashboard.view.night"),
      sel: v === "notte",
      on: () => {
        setVista("notte")
        setSopra(null)
      },
    },
    ...(sole
      ? [
          {
            l: t("dashboard.view.solar"),
            sel: v === "sole",
            on: () => {
              setVista("sole")
              setSopra(null)
            },
          },
        ]
      : []),
  ]
  const legenda =
    v === "notte"
      ? [
          {
            n: t("dashboard.legend.transparency"),
            c: "var(--prot-barra)",
            note: ore.length ? "" : t("dashboard.legend.needsForecast"),
          },
          { n: t("dashboard.chart.moon.name"), c: LUNA, note: quandoDellaLuna(s) },
          { n: t("dashboard.legend.dark"), c: "var(--prot-tenue)", note: notaDelBuio(s) },
        ]
      : [
          ...PIANETI.flatMap((k) => {
            const p = s.planets.find((q) => q.key === k)
            return p
              ? [
                  {
                    n: t(`dashboard.chart.planet.${k}`),
                    c: COLORE_PIANETA[k],
                    note: quandoDelPianeta(p, false),
                  },
                ]
              : []
          }),
          { n: t("dashboard.chart.moon.name"), c: LUNA, note: quandoDellaLuna(s) },
        ]
  const tramonto = fasce[0]?.kind === "day" ? fasce[0].ends_at : null
  const alba =
    fasce[fasce.length - 1]?.kind === "day" ? (fasce[fasce.length - 1]?.starts_at ?? null) : null
  const buio = trattiDelBuio(s)
  const chiave: { n: string; o: number }[] = [
    {
      n: tramonto
        ? t("dashboard.band.day.sunset", { ora: oraDelSito(tramonto) })
        : t("dashboard.band.day"),
      o: 0,
    },
    { n: t("dashboard.band.civil"), o: 1 },
    { n: t("dashboard.band.nautical"), o: 2 },
    { n: t("dashboard.band.astronomical"), o: 3 },
    {
      n: buio ? t("frame.tonight.dark", { tratti: buio }) : t("dashboard.band.dark"),
      o: 4,
    },
    ...(alba ? [{ n: t("dashboard.band.sunrise", { ora: oraDelSito(alba) }), o: 0 }] : []),
  ]
  // every two whole hours, read in the site's zone from the curve's steps
  const tacchi = passi
    .filter((p) => {
      const o = oraDelSito(p.at)
      return o.endsWith(":00") && Number(o.slice(0, 2)) % 2 === 0
    })
    .map((p) => ({ h: oraDelSito(p.at).slice(0, 2), x: x(p.at) / 10 }))

  const grafico = chart && (
    <div style={{ position: "relative", paddingTop: 34 }}>
      <OreDeiConfini confini={mostrati} sinistra={PADL} />
      <div style={{ position: "relative", height: CH }}>
        <ScalaDelCielo
          etichette={
            v === "notte"
              ? ["100", "50", "0"]
              : [ZENIT_DEG, ZENIT_DEG / 2, 0].map((g) => `${g}\u00b0`)
          }
        />
        <div
          onMouseMove={muovi}
          onTouchStart={muovi}
          onTouchMove={muovi}
          onKeyDown={tasto}
          onFocus={() => setFuoco(true)}
          onBlur={() => setFuoco(false)}
          tabIndex={0}
          role="slider"
          aria-label={t("dashboard.chart.aria", {
            label: testa.label,
            value: testa.value,
            sub: testa.sub,
          })}
          aria-valuemin={0}
          aria-valuemax={Math.max(0, N - 1)}
          aria-valuenow={idx}
          aria-valuetext={t("dashboard.chart.at", { ora, valori })}
          style={{
            position: "absolute",
            left: PADL,
            right: 0,
            top: 0,
            bottom: 0,
            cursor: "crosshair",
            touchAction: "pan-y",
            outline: fuoco ? "2px solid var(--prot-testo)" : "none",
            outlineOffset: 6,
            borderRadius: 8,
          }}
        >
          <svg
            viewBox="0 0 1000 200"
            preserveAspectRatio="none"
            style={{
              position: "absolute",
              inset: 0,
              width: "100%",
              height: "100%",
              overflow: "visible",
            }}
            aria-hidden="true"
          >
            <defs>
              <linearGradient id="dash-area" x1={0} y1={0} x2={0} y2={1}>
                <stop offset="0%" stopColor="var(--prot-barra)" stopOpacity={0.32} />
                <stop offset="100%" stopColor="var(--prot-barra)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <FasceDelCielo fasce={fasce} confini={confini} x={x} />
            {area && <path d={area} fill="url(#dash-area)" />}
            {serie.map((sr, k) => (
              <path
                key={`g${sr.n}`}
                d={linea(sr.punti)}
                fill="none"
                stroke={sr.c}
                strokeWidth={k === 0 ? 6 : 4}
                strokeOpacity={0.14}
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ))}
            {serie.map((sr, k) => (
              <path
                key={`l${sr.n}`}
                d={linea(sr.punti)}
                fill="none"
                stroke={sr.c}
                strokeWidth={k === 0 ? 1.75 : 1.25}
                strokeDasharray={sr.tratteggio ? "4 4" : undefined}
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            ))}
          </svg>
          <span
            style={{
              position: "absolute",
              left: `${sinistra}%`,
              top: 0,
              bottom: 0,
              borderLeft: "1.5px dashed var(--prot-tenue)",
              pointerEvents: "none",
              transition: "left .16s ease-out",
            }}
          />
          {serie.map((sr, k) => {
            const val = qui ? sullaLinea(sr.punti, x(qui.at)) : null
            return val == null ? null : (
              <span
                key={`p${sr.n}`}
                style={{
                  position: "absolute",
                  left: `${sinistra}%`,
                  top: `${y(val) / 2}%`,
                  width: 0,
                  height: 0,
                  pointerEvents: "none",
                  zIndex: k === 0 ? 2 : 1,
                  transition: "left .16s ease-out, top .16s ease-out",
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    left: -11,
                    top: -11,
                    width: 22,
                    height: 22,
                    borderRadius: "50%",
                    background: sr.c,
                    opacity: 0.22,
                  }}
                />
                <span
                  style={{
                    position: "absolute",
                    left: -5.5,
                    top: -5.5,
                    width: 11,
                    height: 11,
                    borderRadius: "50%",
                    background: "var(--punto-chiaro)",
                    boxShadow: `0 0 0 2px ${sr.c}, 0 0 10px ${sr.c}`,
                  }}
                />
              </span>
            )
          })}
          {qui && (!tel || sopra !== null) && (
            <div
              className="al-riquadro al-riquadro--lista"
              role="tooltip"
              style={{
                position: "absolute",
                top: tel ? -38 : 4,
                left: tel ? 0 : `${sinistra}%`,
                transform: tel
                  ? "translateY(-100%)"
                  : sinistra > 60
                    ? "translateX(calc(-100% - 14px))"
                    : "translateX(14px)",
                zIndex: 3,
              }}
            >
              <b style={{ fontWeight: 600, fontSize: 13 }}>
                {t("dashboard.chart.atTime", { ora })}
              </b>
              {serie.map((sr) => (
                <span key={sr.n} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <i style={{ width: 8, height: 8, borderRadius: "50%", background: sr.c }} />
                  <span style={{ flex: 1 }}>{sr.n}</span>
                  <b style={{ fontWeight: 600, marginLeft: 12 }}>{sr.scrivi(idx)}</b>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
      {v === "notte" && (s.shooting ?? []).length > 0 && (
        <div
          aria-hidden="true"
          style={{ position: "relative", height: 20, margin: `8px 0 0 ${PADL}px` }}
        >
          {(s.shooting ?? []).map((tr, k) => {
            const a = x(tr.starts_at) / 10
            const b = x(tr.ends_at) / 10
            const larga = tr.band === "broadband"
            return (
              <span
                key={tr.starts_at}
                style={{
                  position: "absolute",
                  left: `calc(${a}% + ${k ? 2 : 0}px)`,
                  width: `calc(${b - a}% - ${k ? 2 : 0}px)`,
                  top: 0,
                  bottom: 0,
                  borderRadius: 6,
                  background: larga ? "var(--prot-traccia)" : TRATTEGGIO,
                  boxShadow: "inset 0 0 0 1px var(--prot-tenue)",
                  display: "flex",
                  alignItems: "center",
                  padding: "0 8px",
                  overflow: "hidden",
                  fontSize: 11,
                  fontWeight: 600,
                  color: "var(--prot-testo)",
                  whiteSpace: "nowrap",
                }}
              >
                <span
                  style={{
                    background: larga ? "transparent" : "var(--prot-fondo)",
                    borderRadius: 4,
                    padding: larga ? 0 : "0 4px",
                  }}
                >
                  {b - a > (tel ? 26 : 14)
                    ? nomeDellaBanda(tr.band)
                    : t(larga ? "dashboard.band.broad.short" : "dashboard.band.narrow.short")}
                </span>
              </span>
            )
          })}
        </div>
      )}
    </div>
  )

  // the hours under the chart, each at its own place
  const asse = (
    <div className={tel ? "al-dash__riga-32" : "al-dash__riga-5"} aria-hidden="true">
      <span style={{ position: "relative", display: "block", flex: 1, height: 16 }}>
        {tacchi.map((h) => (
          <span
            key={h.x}
            style={{ position: "absolute", left: `${h.x}%`, transform: "translateX(-50%)" }}
          >
            {h.h}
          </span>
        ))}
      </span>
    </div>
  )
  const numeroGrande = <span style={{ display: "inline-block" }}>{testa.value}</span>
  const pillola = (
    <span
      className={tel ? "al-dash__pillola-12" : "al-dash__pillola-2"}
      style={{ background: testa.tinta.bg, color: testa.tinta.fg }}
    >
      {testa.pill}
    </span>
  )
  const scelta = (
    <PillolaScelta
      forma="segmentato"
      classe="al-scelta--sottili"
      fondo="protagonista"
      opzioni={viste}
      etichetta={t("dashboard.view.label")}
      formato={formato}
      {...(tel ? { misura: "piccola" as const } : {})}
    />
  )
  if (tel) {
    return (
      <Carta
        formato="telefono"
        etichetta={t("dashboard.tonight.label")}
        tono="protagonista"
        ritardo={0}
        padding="20px 16px"
        gap="14"
      >
        {scelta}
        <div className="al-dash__colonna-18">
          <span className="al-dash__testo-30">{testa.label}</span>
          <span className="al-dash__riga-30">
            <span className="al-dash__testo-31">{numeroGrande}</span>
            {pillola}
          </span>
          {rip && (
            <span className="al-dash__riga-31">
              <Ripresa
                tipo={rip.tipo}
                testo={rip.testo}
                forma="riga"
                fondo="protagonista"
                formato="telefono"
              />
            </span>
          )}
          <span className="al-dash__testo-32">{testa.sub.split(" \u00b7 ")[0]}</span>
        </div>
        {grafico}
        {asse}
        <div className="al-dash__riga-24">
          {legenda.map((l) => (
            <span key={l.n} className="al-dash__riga-33">
              <i className="al-dash__tondo-13" style={{ background: l.c }} />
              <b className="al-dash__testo-7">{l.n}</b>
              <span className="al-dash__testo-8">{l.note}</span>
            </span>
          ))}
        </div>
      </Carta>
    )
  }
  return (
    <Carta tono="protagonista" colonne={7} ritardo={0}>
      <div className="al-dash__riga-2">{scelta}</div>
      <div className="al-dash__colonna-2">
        <span className="al-dash__testo-5">{testa.label}</span>
        <span className="al-dash__riga-3">
          <span className="al-dash__testo-6">{numeroGrande}</span>
          {pillola}
        </span>
        {rip && (
          <span className="al-dash__riga-4">
            <Ripresa tipo={rip.tipo} testo={rip.testo} forma="riga" fondo="protagonista" />
          </span>
        )}
        <span className="al-dash__blocco-2" title={testa.sub}>
          {testa.sub}
        </span>
      </div>
      <div className="al-dash__colonna-3">
        {grafico}
        {asse}
        {v === "notte" && (
          <div className="al-dash__riga-6">
            {chiave.map((k) => (
              <span key={k.n} className="al-dash__riga-7">
                <i
                  className="al-dash__blocco-3"
                  style={{
                    background: `color-mix(in srgb, var(--banda-colore) calc(var(--banda-${k.o}) * 100%), transparent)`,
                  }}
                />
                {k.n}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="al-dash__riga-8">
        {legenda.map((l) => (
          <span key={l.n} className="al-dash__riga-9">
            <i className="al-dash__tondo-2" style={{ background: l.c }} />
            <b className="al-dash__testo-7">{l.n}</b>
            <span className="al-dash__testo-8">{l.note}</span>
          </span>
        ))}
      </div>
    </Carta>
  )
}
