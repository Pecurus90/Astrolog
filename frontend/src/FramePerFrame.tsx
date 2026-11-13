/**
 * *Frame per frame* (tavola v76, `componenti/MisureFrame.dc.html` 35-66, 265-321): un grafico per
 * filtro, una barra per frame nell'ordine di ripresa; le misure scelte nelle tessere, la prima
 * piena e la seconda tratteggiata. Valori ed estremi dall'API; qui il disegno e le scelte.
 */
import { type MouseEvent, type PointerEvent, type TouchEvent, useState } from "react"

import { PillolaScelta } from "./componenti/PillolaScelta"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { nomeDelFiltro } from "./FiltriUsati"
import { numero, oraDelSito, t } from "./i18n"
import {
  type Disegno,
  type Geometria,
  MISURATO,
  chiaveGrafico,
  disegno,
  frameMostrato,
  geometria,
  haZenit,
  pc,
  scala,
  striscia,
  sullAsse,
} from "./FramePerFrameDati"
import {
  type FrameMisurato,
  type Misure,
  type Scelta,
  diversi,
  diversiCoiValori,
  filtriDi,
  insieme,
  nomeDelGruppo,
  nomeDi,
  scritto,
  statistica,
  pallinoDi,
  tintaDi,
} from "./MisureDati"

const ICONE = {
  barre: "M5 20V10M10 20V4M15 20v-7M20 20v-11",
  linee: "M3 18l5-6 4 4 9-10",
} as const

interface Vista {
  linee: boolean
  perValore: boolean
  zenit: boolean
  luna: boolean
}

export function FramePerFrame({
  misure,
  scelta,
  met,
  sel,
  onSel,
  formato,
}: {
  misure: Misure
  scelta: Scelta
  met: string[]
  sel: number | null
  onSel: (id: number) => void
  formato: Formato
}) {
  const tel = formato === "telefono"
  // Si accende solo il frame aperto in "Il frame" (tavola 285).
  const aperto = frameMostrato(misure, scelta, sel).f?.frame_id ?? null
  const [vista, setVista] = useState<Vista>({
    linee: false,
    perValore: false,
    zenit: false,
    luna: false,
  })
  const [gf, setGf] = useState<string[] | null>(null)
  const filtri = filtriDi(misure, scelta.gruppo)
  const nomi = filtri.map((f) => f.name)
  const scelti = (gf ?? [scelta.filtro ?? nomi[0] ?? ""]).filter((k) => nomi.includes(k))
  if (!scelti.length && nomi[0]) scelti.push(nomi[0])
  const due = met.slice(0, 2)
  const tutta = insieme(misure, scelta.gruppo, null)
  const conZenit = due.some((id) => haZenit(id, tutta))
  const zenit = vista.zenit && conZenit
  const conLuna =
    !vista.perValore && misure.series.some((f) => f.values.moon_altitude_deg !== undefined)
  const luna = vista.luna && conLuna
  const cambia = (o: Partial<Vista>) => setVista({ ...vista, ...o })
  const opzioniFiltri = filtri.map((f) => {
    const on = scelti.includes(f.name)
    return {
      l: nomeDelFiltro(f.name),
      sel: on,
      tinta: tintaDi(f.passband),
      on: () =>
        setGf(
          on
            ? scelti.length > 1
              ? scelti.filter((x) => x !== f.name)
              : scelti
            : [...scelti, f.name],
        ),
    }
  })
  const zenitNome = (id: string) => (zenit && haZenit(id, tutta) ? t("chart.at.zenith") : "")
  return (
    <section className="al-c-misure-frame__colonna-4" aria-label={t("chart.section")}>
      <div className="al-c-misure-frame__riga-9">
        <h2 className="al-c-misure-frame__blocco-4">{t("chart.title")}</h2>
        <Comandi vista={vista} cambia={cambia} conZenit={conZenit} conLuna={conLuna} />
      </div>
      <div className="al-c-misure-frame__riga-19">
        <span className="al-c-misure-frame__testo-9">{t("chart.per.filter")}</span>
        <PillolaScelta
          classe="al-c-misure-frame__scelta al-scelta--sottili"
          scorre={tel}
          opzioni={opzioniFiltri}
          etichetta={t("chart.per.filter.label")}
          formato={formato}
        />
      </div>
      {scelti.map((fk) => (
        <UnGrafico
          key={`${fk}-${vista.perValore ? "val" : "ora"}`}
          misure={misure}
          scelta={scelta}
          filtro={fk}
          scelti={scelti}
          met={due}
          vista={{ ...vista, zenit, luna }}
          g={geometria(tel, due.length > 1)}
          sel={aperto}
          onSel={onSel}
          nomeMisura={(id) => nomeDi(id) + zenitNome(id)}
        />
      ))}
      {vista.perValore && (
        <span className="al-c-misure-frame__riga-25">
          <span>{t("chart.low")}</span>
          <span>{t("chart.high", { m: nomeDi(due[0] ?? "fwhm") })}</span>
        </span>
      )}
      <Legenda misure={misure} scelta={scelta} linee={vista.linee} />
    </section>
  )
}

function Comandi({
  vista,
  cambia,
  conZenit,
  conLuna,
}: {
  vista: Vista
  cambia: (o: Partial<Vista>) => void
  conZenit: boolean
  conLuna: boolean
}) {
  const tendina = {
    flex: "none",
    minHeight: 44,
    boxSizing: "border-box",
    fontFamily: "var(--carattere)",
  } as const
  return (
    <div
      role="group"
      aria-label={t("chart.view.group")}
      style={{
        display: "flex",
        gap: 8,
        alignItems: "center",
        flexWrap: "wrap",
        marginLeft: "auto",
      }}
    >
      <div
        role="radiogroup"
        aria-label={t("chart.view")}
        style={{
          flex: "none",
          display: "flex",
          gap: 2,
          padding: 2,
          borderRadius: 999,
          background: "var(--carta-2)",
        }}
      >
        {(["barre", "linee"] as const).map((k) => {
          const on = vista.linee === (k === "linee")
          return (
            <button
              key={k}
              type="button"
              role="radio"
              aria-checked={on ? "true" : "false"}
              aria-label={t(`chart.view.${k}`)}
              title={t(`chart.view.${k}`)}
              onClick={() => cambia({ linee: k === "linee" })}
              style={{
                width: 44,
                height: 44,
                padding: 0,
                border: 0,
                borderRadius: "50%",
                cursor: "pointer",
                display: "grid",
                placeItems: "center",
                background: "transparent",
                color: on ? "var(--testo)" : "var(--tenue)",
                boxShadow: on ? "inset 0 0 0 2px var(--accento)" : "none",
              }}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d={ICONE[k]} />
              </svg>
            </button>
          )
        })}
      </div>
      <select
        key={vista.perValore ? "val" : "ora"}
        defaultValue={vista.perValore ? "val" : "ora"}
        onChange={(e) => cambia({ perValore: e.target.value === "val" })}
        aria-label={t("chart.order")}
        className="al-tendina al-tendina--tondo"
        style={tendina}
      >
        <option value="ora">{t("chart.order.time")}</option>
        <option value="val">{t("chart.order.value")}</option>
      </select>
      {conZenit && (
        <select
          key={vista.zenit ? "z" : "m"}
          defaultValue={vista.zenit ? "z" : "m"}
          onChange={(e) => cambia({ zenit: e.target.value === "z" })}
          aria-label={t("chart.value")}
          className="al-tendina al-tendina--tondo"
          style={tendina}
        >
          <option value="m">{t("chart.value.measured")}</option>
          <option value="z">{t("chart.value.zenith")}</option>
        </select>
      )}
      {conLuna && (
        <PillolaScelta
          forma="interruttore"
          opzioni={[
            {
              l: t("chart.moon"),
              sel: vista.luna,
              titolo: t(vista.luna ? "chart.moon.off" : "chart.moon.on"),
              on: () => cambia({ luna: !vista.luna }),
            },
          ]}
        />
      )}
    </div>
  )
}

/** I frame di un filtro nella scelta: in ordine di ripresa, o misurati dal valore piu' basso. */
function framesDi(
  misure: Misure,
  scelta: Scelta,
  filtro: string,
  chiave: string,
  perValore: boolean,
) {
  const fr = misure.series.filter(
    (f) => f.filter === filtro && (scelta.gruppo === null || f.group === scelta.gruppo),
  )
  if (!perValore) return fr
  return fr
    .filter((f) => MISURATO.has(f.state) && f.values[chiave] !== undefined)
    .sort((a, b) => (a.values[chiave] ?? 0) - (b.values[chiave] ?? 0))
}

function UnGrafico({
  misure,
  scelta,
  filtro,
  scelti,
  met,
  vista,
  g,
  sel,
  onSel,
  nomeMisura,
}: {
  misure: Misure
  scelta: Scelta
  filtro: string
  scelti: string[]
  met: string[]
  vista: Vista
  g: Geometria
  sel: number | null
  onSel: (id: number) => void
  nomeMisura: (id: string) => string
}) {
  const [inizio, setInizio] = useState(0)
  const [sopra, setSopra] = useState<number | null>(null)
  const set = insieme(misure, scelta.gruppo, filtro)
  const insiemi = scelti.map((k) => insieme(misure, scelta.gruppo, k))
  const chiavi = met.map((id) => chiaveGrafico(id, set, vista.zenit))
  const scale = chiavi.map((k) => scala(insiemi, k))
  const frames = framesDi(misure, scelta, filtro, chiavi[0] ?? "", vista.perValore)
  const d = disegno({
    frames,
    chiavi,
    scale: scale.map((s) => s ?? [0, 1]),
    g,
    inizio,
    linee: vista.linee,
    luna: vista.luna,
    acceso: sopra ?? sel,
  })
  const passband = misure.filters.find((f) => f.name === filtro)?.passband
  const prendi = (x: number, larghezza: number) => {
    const i = Math.floor(((x / larghezza) * g.W - g.x0) / d.slot)
    const f = d.vis[Math.max(0, Math.min(d.vis.length - 1, i))]
    if (f && f.frame_id !== sopra) setSopra(f.frame_id)
    return f
  }
  const muovi = (e: MouseEvent<HTMLDivElement> | TouchEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    const x = "touches" in e ? (e.touches[0]?.clientX ?? 0) : e.clientX
    prendi(x - r.left, r.width)
  }
  const tocca = (e: MouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect()
    const f = prendi(e.clientX - r.left, r.width)
    if (f) onSel(f.frame_id)
  }
  const mediane = met.map((id, j) => ({
    n: nomeDi(id),
    v: scritto(chiavi[j] ?? "", statistica(set, chiavi[j] ?? "")?.median),
  }))
  return (
    <div className="al-c-misure-frame__colonna-6">
      <div className="al-c-misure-frame__riga-20">
        <span className="al-c-misure-frame__riga-21">
          <span
            className="al-c-misure-frame__tondo-1"
            aria-hidden="true"
            style={pallinoDi(passband)}
          />
          {nomeDelFiltro(filtro)}
        </span>
        {nota(set, chiavi) && (
          <span className="al-c-misure-frame__testo-2">{nota(set, chiavi)}</span>
        )}
        {met.map((id, j) => (
          <span key={id} className="al-c-misure-frame__riga-22">
            <i
              className={
                vista.linee
                  ? j
                    ? "al-c-misure-frame__pillola-1 al-c-misure-frame__pillola-1--linea-2"
                    : "al-c-misure-frame__pillola-1 al-c-misure-frame__pillola-1--linea-1"
                  : j
                    ? "al-c-misure-frame__pillola-1 al-c-misure-frame__pillola-1--barra-2"
                    : "al-c-misure-frame__pillola-1 al-c-misure-frame__pillola-1--barra-1"
              }
              aria-hidden="true"
            />
            {nomeMisura(id)}
          </span>
        ))}
        {vista.luna && (
          <span className="al-c-misure-frame__riga-22">
            <i
              className="al-c-misure-frame__pillola-1 al-c-misure-frame__pillola-1--luna"
              aria-hidden="true"
            />
            {t("chart.moon.key")}
          </span>
        )}
        <span className="al-c-misure-frame__blocco-5" />
        <span className="al-c-misure-frame__testo-10">
          {mediane.map((m) => (
            <span key={m.n} className="al-c-misure-frame__testo-11">
              {m.n} {m.v}
            </span>
          ))}{" "}
          {t("chart.medians")}
        </span>
      </div>
      <div
        className="al-c-misure-frame__blocco-6"
        onMouseMove={muovi}
        onMouseLeave={() => setSopra(null)}
        onTouchStart={muovi}
        onTouchMove={muovi}
        onClick={tocca}
      >
        <Svg
          d={d}
          g={g}
          linee={vista.linee}
          label={t("chart.label", {
            f: nomeDelFiltro(filtro),
            m: met.map(nomeDi).join(t("chart.and")),
            n: numero(frames.length),
          })}
        />
        {chiavi.map((k, j) => {
          const s = scale[j]
          if (!s) return null
          return [0.1, 0.5, 0.9].map((q) => {
            const v = s[0] + (s[1] - s[0]) * q
            const y = g.bot - ((v - s[0]) / (s[1] - s[0] || 1)) * (g.bot - g.top)
            return (
              <span
                key={`${k}-${q}`}
                className="al-c-misure-frame__strato-1"
                aria-hidden="true"
                style={{
                  left: pc(j ? g.x1 + 6 : g.x0 - 6, g.W),
                  top: pc(y, g.H),
                  transform: j ? "translate(0,-50%)" : "translate(-100%,-50%)",
                }}
              >
                {sullAsse(k, v)}
              </span>
            )
          })
        })}
        <Riquadro
          misure={misure}
          d={d}
          g={g}
          frames={frames}
          id={sopra}
          filtro={filtro}
          met={met}
          chiavi={chiavi}
          nomeMisura={nomeMisura}
          luna={vista.luna}
        />
      </div>
      {!vista.perValore && <Oggetti misure={misure} d={d} g={g} />}
      {d.finestra && (
        <Finestra
          frames={frames}
          d={d}
          g={g}
          chiave={chiavi[0] ?? ""}
          scala={scale[0] ?? [0, 1]}
          vai={setInizio}
          misure={misure}
          perOra={!vista.perValore}
        />
      )}
    </div>
  )
}

/** La nota accanto al filtro: la luminosita' del cielo, fondo e rumore non confrontabili. */
function nota(set: ReturnType<typeof insieme>, chiavi: string[]): string {
  const parti: string[] = []
  if (chiavi.includes("sqm"))
    parti.push(t(statistica(set, "sqm")?.median == null ? "measures.none" : "chart.sqm.direction"))
  const fondo = chiavi.some((k) => k === "background_adu" || k === "noise_adu")
  if (fondo && set?.differs.length) {
    const solo = set.differs.every((x) => x === "exposure")
    const coi = diversiCoiValori(set.differs, set.differs_values)
    parti.push(
      coi
        ? t(solo ? "chart.not.comparable.values.rate" : "chart.not.comparable.values", { r: coi })
        : t(solo ? "chart.not.comparable.rate" : "chart.not.comparable", {
            r: diversi(set.differs),
          }),
    )
  }
  return parti.join(" \u00B7 ")
}

function Svg({ d, g, linee, label }: { d: Disegno; g: Geometria; linee: boolean; label: string }) {
  return (
    <svg
      className="al-c-misure-frame__grafico-2"
      viewBox={`0 0 ${g.W} ${g.H}`}
      width="100%"
      role="img"
      aria-label={label}
    >
      <line
        className="al-c-misure-frame__tratto-1"
        x1={g.x0}
        x2={g.x1}
        y1={g.bot}
        y2={g.bot}
        strokeWidth="1"
      />
      {d.sep.map((x) => (
        <line
          key={x}
          className="al-c-misure-frame__tratto-2"
          x1={x}
          x2={x}
          y1="0"
          y2={g.bot}
          strokeWidth="1"
          strokeDasharray="3 4"
        />
      ))}
      {d.B.filter((r) => !r.sol).map((r) => (
        <rect
          key={`t${r.x}`}
          className="al-c-misure-frame__tratto-2"
          x={r.x}
          y={r.y}
          width={r.w}
          height={r.h}
          rx={r.r}
          fill="none"
          strokeOpacity=".55"
          strokeWidth="1"
          strokeDasharray="1.5 3.5"
        />
      ))}
      {d.A.map((r) => (
        <rect
          key={`a${r.x}`}
          className={
            r.stimata
              ? "al-c-misure-frame__barra al-c-misure-frame__barra--stimata"
              : r.accesa
                ? "al-c-misure-frame__barra al-c-misure-frame__barra--accesa"
                : "al-c-misure-frame__barra"
          }
          x={r.x}
          y={r.y}
          width={r.w}
          height={r.h}
          rx={r.r}
          strokeWidth="1.25"
        />
      ))}
      {d.B.map((r) => (
        <g key={`b${r.x}`}>
          <path
            className="al-c-misure-frame__tratto-3"
            d={r.d}
            strokeWidth="3.5"
            strokeLinecap="round"
          />
          <path
            className="al-c-misure-frame__tratto-4"
            d={r.d}
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </g>
      ))}
      {linee && (
        <>
          <path
            className="al-c-misure-frame__tratto-5"
            d={d.dA}
            fill="none"
            strokeOpacity=".18"
            strokeWidth="7"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          <path
            className="al-c-misure-frame__tratto-5"
            d={d.dA}
            fill="none"
            strokeWidth="1.75"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          <path
            className="al-c-misure-frame__tratto-4"
            d={d.dB}
            fill="none"
            strokeWidth="1.25"
            strokeDasharray="3 5"
            strokeLinecap="round"
          />
        </>
      )}
      {d.dL && (
        <path
          className="al-c-misure-frame__tratto-2"
          d={d.dL}
          fill="none"
          strokeWidth="2"
          strokeDasharray="1 4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
      {d.segni.map((p, i) => (
        <path key={i} className="al-c-misure-frame__tratto-2" d={p} strokeWidth="1.5" fill="none" />
      ))}
      {d.hx !== null && (
        <>
          <line
            className="al-c-misure-frame__tratto-4"
            x1={d.hx}
            x2={d.hx}
            y1="0"
            y2={g.bot}
            strokeWidth="1"
            strokeOpacity=".35"
          />
          {linee && d.hy !== null && (
            <circle
              className="al-c-misure-frame__tratto-6"
              cx={d.hx}
              cy={d.hy}
              r="5"
              strokeWidth="2"
            />
          )}
        </>
      )}
    </svg>
  )
}

function Riquadro({
  misure,
  d,
  g,
  frames,
  id,
  filtro,
  met,
  chiavi,
  nomeMisura,
  luna,
}: {
  misure: Misure
  d: Disegno
  g: Geometria
  frames: FrameMisurato[]
  id: number | null
  filtro: string
  met: string[]
  chiavi: string[]
  nomeMisura: (id: string) => string
  luna: boolean
}) {
  const i = d.vis.findIndex((f) => f.frame_id === id)
  const f = d.vis[i]
  if (!f) return null
  const gruppo = misure.groups.find((o) => o.key === f.group)
  const nome = gruppo ? nomeDelGruppo(gruppo) : null
  const righe: { n: string; v: string }[] = MISURATO.has(f.state)
    ? met.map((m, j) => ({
        n: nomeMisura(m),
        v: scritto(chiavi[j] ?? "", f.values[chiavi[j] ?? ""]),
      }))
    : [{ n: t(f.state === "too_few_stars" ? "shot.few" : "measures.pending"), v: "" }]
  if (MISURATO.has(f.state) && f.values.airmass !== undefined && !chiavi.includes("airmass"))
    righe.push({ n: nomeDi("airmass"), v: scritto("airmass", f.values.airmass) })
  const lu = f.values.moon_altitude_deg
  if (MISURATO.has(f.state) && luna && lu !== undefined)
    righe.push({
      n: nomeDi("moon_altitude_deg"),
      v: lu < 0 ? t("chart.moon.below") : scritto("moon_altitude_deg", lu),
    })
  const x = g.x0 + d.slot * (i + 0.5)
  return (
    <div
      role="tooltip"
      className="al-riquadro al-c-misure-frame__blocco-7"
      style={{
        left: pc(x, g.W),
        transform: i > d.vis.length * 0.6 ? "translateX(calc(-100% - 12px))" : "translateX(12px)",
      }}
    >
      <b className="al-riquadro__titolo">
        {t("shot.title", {
          i: numero(frames.indexOf(f) + 1),
          n: numero(frames.length),
          f: nomeDelFiltro(filtro),
        })}
      </b>
      <span className="al-riquadro__sotto">
        {[nome, f.start ? oraDelSito(f.start) : null].filter(Boolean).join(" \u00B7 ")}
      </span>
      {righe.map((r) => (
        <span key={r.n} style={{ display: "contents" }}>
          <span>{r.n}</span>
          <b className="al-riquadro__valore">{r.v}</b>
        </span>
      ))}
    </div>
  )
}

/** I nomi degli oggetti sotto l'asse, dove ne comincia uno; uno che non ci sta salta. */
function Oggetti({ misure, d, g }: { misure: Misure; d: Disegno; g: Geometria }) {
  const nomi = new Map(misure.groups.map((o) => [o.key, nomeDelGruppo(o)]))
  const gl: { x: number; l: string }[] = []
  d.vis.forEach((f, i) => {
    if (i && d.vis[i - 1]?.group === f.group) return
    const x = g.x0 + d.slot * i
    const l = (f.group && nomi.get(f.group)) ?? ""
    const prima = gl.at(-1)
    if (l && (!prima || x - prima.x > prima.l.length * 6.2 + 8)) gl.push({ x, l })
  })
  const ml = pc(g.x0, g.W)
  return (
    <div
      className="al-c-misure-frame__blocco-8"
      style={{ marginLeft: ml, marginRight: pc(g.W - g.x1, g.W) }}
    >
      {gl.map((o) => (
        <span
          key={`${o.x}`}
          className="al-c-misure-frame__strato-2"
          style={{ left: `calc(${pc(o.x, g.W)} - ${ml})` }}
        >
          {o.l}
        </span>
      ))}
    </div>
  )
}

function Finestra({
  frames,
  d,
  g,
  chiave,
  scala: s,
  vai,
  misure,
  perOra,
}: {
  frames: FrameMisurato[]
  d: Disegno
  g: Geometria
  chiave: string
  scala: [number, number]
  vai: (i: number) => void
  misure: Misure
  perOra: boolean
}) {
  const n = frames.length
  const quanti = d.vis.length
  const testo = t("chart.window", {
    a: numero(d.inizio + 1),
    b: numero(d.inizio + quanti),
    n: numero(n),
  })
  const trascina = (e: PointerEvent<HTMLDivElement>) => {
    if (e.type !== "pointerdown" && !(e.buttons & 1)) return
    const r = e.currentTarget.getBoundingClientRect()
    vai(Math.round(((e.clientX - r.left) / r.width) * n - quanti / 2))
  }
  const oggetti = perOra ? [...new Set(frames.map((f) => f.group))] : []
  const nomi = new Map(misure.groups.map((o) => [o.key, nomeDelGruppo(o)]))
  const margini = { marginLeft: pc(g.x0, g.W), marginRight: pc(g.W - g.x1, g.W) }
  return (
    <>
      <div className="al-c-misure-frame__riga-23" style={margini}>
        <button
          type="button"
          className="al-bottone al-c-misure-frame__tondo-5"
          aria-label={t("shot.prev")}
          onClick={gesto(() => vai(d.inizio - Math.floor(quanti / 2)))}
        >
          {"\u2039"}
        </button>
        <div
          className="al-c-misure-frame__riquadro-1"
          onPointerDown={trascina}
          onPointerMove={trascina}
          role="slider"
          aria-label={t("chart.window.label")}
          aria-valuetext={testo}
          aria-valuenow={d.inizio + 1}
          aria-valuemin={1}
          aria-valuemax={n}
        >
          <svg
            className="al-c-misure-frame__grafico-3"
            viewBox="0 0 100 24"
            preserveAspectRatio="none"
            width="100%"
            height="100%"
            aria-hidden="true"
          >
            <path
              className="al-c-misure-frame__tratto-2"
              d={striscia(frames, chiave, s)}
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
            />
          </svg>
          <span
            className="al-c-misure-frame__strato-3"
            style={{ left: pc(d.inizio, n), width: pc(quanti, n) }}
          />
        </div>
        <button
          type="button"
          className="al-bottone al-c-misure-frame__tondo-5"
          aria-label={t("shot.next")}
          onClick={gesto(() => vai(d.inizio + Math.floor(quanti / 2)))}
        >
          {"\u203A"}
        </button>
      </div>
      <div className="al-c-misure-frame__riga-24" style={{ marginLeft: margini.marginLeft }}>
        <span className="al-c-misure-frame__testo-12">{testo}</span>
        {oggetti.length > 1 &&
          oggetti.map((k) => (
            <button
              key={k ?? ""}
              type="button"
              className="al-bottone al-bottone--tenue al-bottone--piccolo"
              onClick={gesto(() => vai(frames.findIndex((f) => f.group === k)))}
            >
              {(k && nomi.get(k)) ?? t("archive.panel.noObject")}
            </button>
          ))}
      </div>
    </>
  )
}

/** Sotto i grafici: come si leggono, e i segni che ci sono (tavola 312-313). */
function Legenda({ misure, scelta, linee }: { misure: Misure; scelta: Scelta; linee: boolean }) {
  const vis = misure.series.filter((f) => scelta.gruppo === null || f.group === scelta.gruppo)
  const segni = [
    vis.some((f) => f.state === "estimated") && {
      n: t("chart.estimated"),
      d: linee ? "M9 5m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0" : "M6 1h6v8h-6z",
      accento: true,
    },
    vis.some((f) => f.state === "too_few_stars") && {
      n: t("shot.few"),
      d: "M6 2l6 6m0 -6l-6 6",
      accento: false,
    },
    vis.some((f) => f.state === "pending") && {
      n: t("measures.pending"),
      d: "M7 5a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
      accento: false,
    },
  ].filter((x) => x !== false)
  return (
    <div className="al-c-misure-frame__riga-26">
      <span>{t("chart.caption")}</span>
      {segni.map((s) => (
        <span key={s.n} className="al-c-misure-frame__riga-27">
          <svg aria-hidden="true" width="18" height="10" viewBox="0 0 18 10">
            <path
              className={
                s.accento
                  ? "al-c-misure-frame__chiave--accento"
                  : "al-c-misure-frame__chiave--tenue"
              }
              d={s.d}
              fill="none"
              strokeWidth="1.5"
            />
          </svg>
          {s.n}
        </span>
      ))}
    </div>
  )
}
