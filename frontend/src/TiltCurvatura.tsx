/**
 * *Tilt e curvatura di campo* (tavola v76, `componenti/MisureFrame.dc.html` 106-120, 334-342): il
 * sensore con le HFD mediane dei quattro angoli e del centro, grande per la scelta e piccolo per
 * filtro. Mediane, tilt, curvatura e giudizio dall'API; qui il disegno.
 */
import { Pillola } from "./componenti/Pillola"
import { nomeDelFiltro } from "./FiltriUsati"
import { numero, t } from "./i18n"
import {
  ESITO,
  type Insieme,
  type Misure,
  type Scelta,
  filtriDi,
  insieme,
  scritto,
  statistica,
  tintaDi,
} from "./MisureDati"

// Angoli ai pixel (1,1) (W,1) (W,H) (1,H), come li scrive la pipeline; il sensore si disegna
// con la riga 1 in basso, come lo standard FITS. Posti sulla tavola 300 x 200 (336).
const ANGOLI = [
  { chiave: "hfd_corner_1_px", x: 70, y: 143, sopra: false },
  { chiave: "hfd_corner_2_px", x: 230, y: 143, sopra: false },
  { chiave: "hfd_corner_3_px", x: 230, y: 50, sopra: true },
  { chiave: "hfd_corner_4_px", x: 70, y: 50, sopra: true },
] as const

interface Cerchio {
  x: number
  y: number
  r: number
  max: boolean
  lx: string
  ly: string
  l: string
}

interface Sensore {
  punti: Cerchio[]
  tilt: string
  curvatura: string
  giudizio: string | null
  label: string
}

/** Il disegno del sensore di un insieme; null se le mediane degli angoli non ci sono. */
function sensore(set: Insieme | undefined, W: number, H: number, grande: boolean): Sensore | null {
  const centro = statistica(set, "hfd_centre_px")?.median
  const angoli = ANGOLI.map((a) => statistica(set, a.chiave)?.median)
  if (centro == null || angoli.some((v) => v == null)) return null
  const v = angoli as number[]
  const max = Math.max(...v)
  const sx = W / 300
  const sy = H / 200
  // il raggio cresce con la HFD sopra quella del centro (tavola 336): disegno, non giudizio
  const raggio = (x: number) =>
    Math.max(2, grande ? 9 + (x / centro - 1) * 70 : 4 + (x / centro - 1) * 34)
  const punto = (x: number, y: number, hfd: number, sopra: boolean, inMax: boolean): Cerchio => {
    const r = raggio(hfd)
    return {
      x: x * sx,
      y: y * sy,
      r,
      max: inMax,
      lx: `${((x / 300) * 100).toFixed(1)}%`,
      ly: `${(((y + (sopra ? r + 12 : -r - 11)) / 200) * 100).toFixed(1)}%`,
      l: scritto("hfd_px", hfd),
    }
  }
  const punti = ANGOLI.map((a, j) => punto(a.x, a.y, v[j] ?? 0, a.sopra, v[j] === max))
  punti.push(punto(150, 96, centro, true, false))
  const tilt = statistica(set, "hfd_tilt_pct")
  const curvatura = valoreCurvatura(set)
  return {
    punti,
    tilt: scritto("hfd_tilt_pct", tilt?.median),
    curvatura,
    giudizio: tilt?.verdict ?? null,
    label: t("sensor.label", {
      a: v.map((x) => scritto("hfd_px", x)).join(" / "),
      c: scritto("hfd_px", centro),
      t: scritto("hfd_tilt_pct", tilt?.median),
      k: curvatura,
    }),
  }
}

function valoreCurvatura(set: Insieme | undefined): string {
  const px = statistica(set, "off_axis_px")?.median
  const arc = statistica(set, "off_axis_arcsec")?.median
  const base = scritto("off_axis_px", px)
  return arc == null ? base : `${base} \u00B7 ${scritto("off_axis_arcsec", arc)}`
}

function Disegno({ s, W, H, grande }: { s: Sensore; W: number; H: number; grande: boolean }) {
  const cerchi = s.punti.map((c, i) => (
    <circle
      key={i}
      className={
        c.max
          ? "al-c-misure-frame__cerchio al-c-misure-frame__cerchio--max"
          : "al-c-misure-frame__cerchio"
      }
      cx={c.x.toFixed(1)}
      cy={c.y.toFixed(1)}
      r={c.r.toFixed(1)}
      fill="none"
    />
  ))
  if (!grande)
    return (
      <svg
        className="al-c-misure-frame__grafico-3"
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        aria-hidden="true"
      >
        <rect
          className="al-c-misure-frame__tratto-7"
          x="6"
          y="5"
          width="138"
          height="90"
          rx="4"
          strokeWidth="1"
        />
        {cerchi}
      </svg>
    )
  return (
    <div className="al-c-misure-frame__blocco-11">
      <svg
        className="al-c-misure-frame__grafico-3"
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        role="img"
        aria-label={s.label}
      >
        <rect
          className="al-c-misure-frame__tratto-7"
          x="20"
          y="10"
          width="260"
          height="173"
          rx="6"
          strokeWidth="1.5"
        />
        {cerchi}
      </svg>
      {s.punti.map((c, i) => (
        <span
          key={i}
          className={
            c.max
              ? "al-c-misure-frame__strato-4 al-c-misure-frame__strato-4--max"
              : "al-c-misure-frame__strato-4"
          }
          aria-hidden="true"
          style={{ left: c.lx, top: c.ly }}
        >
          {c.l}
        </span>
      ))}
    </div>
  )
}

function Giudizio({ g }: { g: string | null }) {
  if (!g) return null
  return (
    <Pillola
      esito={ESITO[g] ?? 0}
      testo={t(`measures.tilt.${g as "go"}`)}
      dimensione="micro"
      fondo="carta"
    />
  )
}

export function TiltCurvatura({ misure, scelta }: { misure: Misure; scelta: Scelta }) {
  const set = insieme(misure, scelta.oggetto, scelta.filtro)
  const grande = sensore(set, 300, 200, true)
  const misurati = statistica(set, "hfd_px")?.measured ?? 0
  const piccoli = filtriDi(misure, scelta.oggetto)
    .map((f) => ({ f, s: sensore(insieme(misure, scelta.oggetto, f.name), 150, 100, false) }))
    .filter((x) => x.s !== null)
  return (
    <section className="al-c-misure-frame__colonna-4" aria-label={t("sensor.title")}>
      <h2 className="al-c-misure-frame__testo-1">{t("sensor.title")}</h2>
      <div className="al-c-misure-frame__centro-4">
        {grande ? (
          <div className="al-c-misure-frame__colonna-16">
            <span className="al-c-misure-frame__testo-9">
              {`${scelta.filtro ? nomeDelFiltro(scelta.filtro) : t("sensor.all")} \u00B7 ${t("measures.of", { m: numero(misurati), n: numero(set?.frames ?? 0) })}`}
            </span>
            <Disegno s={grande} W={300} H={200} grande />
            <div className="al-c-misure-frame__griglia-1">
              <div className="al-c-misure-frame__colonna-17">
                <span className="al-c-misure-frame__testo-9">{t("sensor.tilt")}</span>
                <span className="al-c-misure-frame__testo-19">{grande.tilt}</span>
                <span className="al-c-misure-frame__riga-37">
                  <Giudizio g={grande.giudizio} />
                </span>
              </div>
              <div className="al-c-misure-frame__colonna-17">
                <span className="al-c-misure-frame__testo-9">{t("sensor.curvature")}</span>
                <span className="al-c-misure-frame__testo-19">{grande.curvatura}</span>
              </div>
            </div>
          </div>
        ) : (
          <span className="al-c-misure-frame__testo-9">{t("measures.none")}</span>
        )}
        <div className="al-c-misure-frame__colonna-18">
          <span className="al-c-misure-frame__testo-9">{t("perfilter.title")}</span>
          <div className="al-c-misure-frame__centro-1 al-c-misure-frame__centro-1--filtri">
            {piccoli.map(({ f, s }) =>
              s ? (
                <div key={f.name} className="al-c-misure-frame__colonna-19">
                  <span className="al-c-misure-frame__riga-38">
                    <span
                      className="al-c-misure-frame__tondo-1"
                      aria-hidden="true"
                      style={{ background: tintaDi(f.passband).fondo }}
                    />
                    {nomeDelFiltro(f.name)}
                  </span>
                  <Disegno s={s} W={150} H={100} grande={false} />
                  <span className="al-c-misure-frame__testo-20">
                    {t("sensor.small", { t: s.tilt, k: s.curvatura })}
                  </span>
                  <span className="al-c-misure-frame__riga-37">
                    <Giudizio g={s.giudizio} />
                  </span>
                </div>
              ) : null,
            )}
          </div>
          <span className="al-c-misure-frame__testo-7">{t("sensor.how")}</span>
        </div>
      </div>
    </section>
  )
}
