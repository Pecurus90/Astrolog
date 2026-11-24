import { Carta } from "./componenti/Carta"
import { PillolaScelta } from "./componenti/PillolaScelta"
import { Ripresa } from "./componenti/Ripresa"
import type { Formato } from "./componenti/Tema"
import { type Chiave, numero, oraDelSito, t } from "./i18n"
import type { Sguardo } from "./Meteo"
import { type Accesa, MeteoCielo, oreSotto, UMIDITA } from "./MeteoCielo"
import { type Codice, type Meteo, type Notte, buioDellaNotte, protagonista } from "./MeteoDati"

export type Obiettivo = "deep" | "sole"

const PILLOLA = {
  0: ["var(--buono-fondo)", "var(--buono-testo)"],
  1: ["var(--incerto-fondo)", "var(--incerto-testo)"],
  2: ["var(--non-adatto-fondo)", "var(--non-adatto-testo)"],
} as const
const SEGNO = { 0: "\u2713", 1: "!", 2: "\u2715" } as const
// the cloud layers' swatch: the protagonist's ink at the chart's opacity
const strato = (pct: number) => `color-mix(in srgb, var(--prot-testo) ${pct}%, transparent)`

/** The measures the scale switches on, in the board's order (`SC`). */
const SCALA: { a: Accesa; l: Chiave }[] = [
  { a: "humidity", l: "meteo.scale.humidity" },
  { a: "condensation", l: "weather.right.condensation" },
  { a: "rain", l: "weather.right.rain" },
  { a: "wind", l: "weather.right.wind" },
  { a: "seeing", l: "weather.right.seeing" },
  { a: "jet", l: "weather.right.jet" },
  { a: "aerosol", l: "weather.right.aerosol" },
  { a: "visibility", l: "weather.right.visibility" },
]

/** Why a measure cannot go on the chart, or `null`: the reasons the board gives. */
export function spenta(a: Accesa, n: Notte, detto: Meteo): string | null {
  if (a === "humidity") return null
  const m = n.measures.find((x) => x.code === a)
  if (a === "seeing" && (!m || m.known_hours === 0)) {
    if (!detto.seeing.key || detto.seeing.meteoblue === "refused")
      return t("weather.card.seeing.none")
    if (detto.seeing.meteoblue === null) return t("meteo.scale.seeing.soon")
  }
  if (!m || m.known_hours === 0) {
    const nuvole = n.measures.find((x) => x.code === "cloud")?.level === "nogo"
    return nuvole && (a === "seeing" || a === "aerosol")
      ? t("meteo.scale.clouds")
      : t("meteo.scale.missing")
  }
  return null
}

/** The night's card (board v82 `La notte`): the objective, the big number, the sky and its scale. */
export function LaNotte({
  detto,
  notte: n,
  prima,
  formato,
  sguardo: g,
  obiettivo,
  scegliObiettivo,
  intera,
}: {
  detto: Meteo
  notte: Notte
  prima: boolean
  formato: Formato
  sguardo: Sguardo
  obiettivo: Obiettivo
  scegliObiettivo: (o: Obiettivo) => void
  /** The Sun never sets: the card takes the whole row. */
  intera: boolean
}) {
  const tel = formato === "telefono"
  const sole = obiettivo === "sole"
  const p = sole
    ? {
        top: t("meteo.sun.name"),
        valore: t("weather.verdict.unknown"),
        pillola: { esito: "mancante" as const, testo: t("meteo.sun.pill") },
        ripresa: null,
        sotto: t("meteo.sun.text"),
        grande: false,
        grafico: false,
      }
    : protagonista(n, prima)
  const pill =
    p.pillola && typeof p.pillola.esito === "number"
      ? {
          bg: PILLOLA[p.pillola.esito as 0 | 1 | 2][0],
          fg: PILLOLA[p.pillola.esito as 0 | 1 | 2][1],
          testo: `${SEGNO[p.pillola.esito as 0 | 1 | 2]} ${p.pillola.testo}`,
        }
      : p.pillola
        ? { bg: "var(--carta-2)", fg: "var(--testo)", testo: `? ${p.pillola.testo}` }
        : null
  const fs = p.grande ? (tel ? "48px" : "64px") : tel ? "32px" : "44px"
  const obiettivi = (
    <PillolaScelta
      forma="segmentato"
      classe="al-scelta--sottili"
      fondo="protagonista"
      allinea="flex-start"
      etichetta={t("meteo.objective")}
      formato={formato}
      {...(tel ? { misura: "piccola" as const } : {})}
      opzioni={(["deep", "sole"] as const).map((o) => ({
        l: t(`meteo.objective.${o}`),
        sel: o === obiettivo,
        on: () => scegliObiettivo(o),
      }))}
    />
  )
  const senzaMouse =
    tel || (typeof window.matchMedia === "function" && window.matchMedia("(hover: none)").matches)
  const interattivo = !n.trend && !sole && p.grafico
  const accese = g.accese.filter((a) => spenta(a, n, detto) === null)
  const grafico = !sole && p.grafico && (
    <div className={tel ? "al-meteo__colonna-16" : "al-meteo__colonna-3"}>
      {interattivo && (
        <span className="al-meteo__testo-6">
          {t(senzaMouse ? "meteo.chart.hint.touch" : "meteo.chart.hint")}
        </span>
      )}
      <MeteoCielo
        notte={n}
        accese={accese}
        ora={g.ora}
        scegliOra={g.scegliOra}
        telefono={tel}
        aria={t("meteo.chart.aria", { valore: p.valore, top: p.top })}
      />
      <div className={tel ? "al-meteo__riga-26" : "al-meteo__riga-5"}>
        {oreSotto(n, tel).map((h, k) => (
          <span key={`${h}${k}`}>{h}</span>
        ))}
      </div>
      {!tel && <ChiaveDelleFasce notte={n} />}
    </div>
  )
  const scala = !sole && interattivo && (
    <Scala detto={detto} notte={n} formato={formato} sguardo={g} accese={accese} />
  )
  const numeroGrande = (
    <div className={tel ? "al-meteo__colonna-11" : "al-meteo__colonna-2"}>
      <span className={tel ? "al-meteo__testo-24" : "al-meteo__testo-3"}>{p.top}</span>
      <span className={tel ? "al-meteo__riga-24" : "al-meteo__riga-3"}>
        <span className={tel ? "al-meteo__testo-25" : "al-meteo__testo-4"} style={{ fontSize: fs }}>
          {p.valore}
        </span>
        {pill && (
          <span
            className={tel ? "al-meteo__pillola-3" : "al-meteo__pillola-1"}
            style={{ background: pill.bg, color: pill.fg }}
          >
            {pill.testo}
          </span>
        )}
      </span>
      {p.ripresa && !sole && (
        <span className={tel ? "al-meteo__riga-25" : "al-meteo__riga-4"}>
          <Ripresa
            tipo={p.ripresa.tipo}
            testo={p.ripresa.testo}
            forma="riga"
            fondo="protagonista"
            formato={formato}
          />
        </span>
      )}
      <span className={tel ? "al-meteo__testo-26" : "al-meteo__testo-5"}>{p.sotto}</span>
    </div>
  )
  return (
    <Carta
      formato={formato}
      etichetta={t("meteo.night.card")}
      tono="protagonista"
      {...(tel ? {} : { colonne: intera ? 12 : 8 })}
      ritardo={60}
      padding={tel ? "20px 16px" : "28px"}
      gap={tel ? "14" : "18"}
    >
      {!intera && obiettivi}
      {numeroGrande}
      {grafico}
      {scala}
    </Carta>
  )
}

/** The bands' key under the chart: "giorno \u00b7 tramonto 19:11", civil, nautical, astronomical,
 *  "buio 20:48\u201305:48", "alba 07:25" (board v82 `bandKey`). */
function ChiaveDelleFasce({ notte: n }: { notte: Notte }) {
  const fasce = n.sky_bands ?? []
  const tramonto = fasce[0]?.kind === "day" ? fasce[0].ends_at : null
  const ultima = fasce[fasce.length - 1]
  const alba = ultima?.kind === "day" ? ultima.starts_at : null
  const tipi = new Set(fasce.map((f) => f.kind))
  const buio = buioDellaNotte({ ...n, window: "dark" })
  const voci: { n: string; o: number }[] = [
    {
      n: tramonto
        ? t("dashboard.band.day.sunset", { ora: oraDelSito(tramonto) })
        : t("dashboard.band.day"),
      o: 0,
    },
    ...(tipi.has("civil") ? [{ n: t("dashboard.band.civil"), o: 1 }] : []),
    ...(tipi.has("nautical") ? [{ n: t("dashboard.band.nautical"), o: 2 }] : []),
    ...(tipi.has("astronomical") ? [{ n: t("dashboard.band.astronomical"), o: 3 }] : []),
    ...(tipi.has("dark")
      ? [{ n: buio ? t("meteo.band.dark", { buio }) : t("dashboard.band.dark"), o: 4 }]
      : []),
    ...(alba ? [{ n: t("dashboard.band.sunrise", { ora: oraDelSito(alba) }), o: 0 }] : []),
  ]
  return (
    <div className="al-meteo__riga-6">
      {voci.map((v) => (
        <span key={v.n} className="al-meteo__riga-7">
          <i
            className="al-meteo__blocco-2"
            style={{
              background: `color-mix(in srgb, var(--banda-colore) calc(var(--banda-${v.o}) * 100%), transparent)`,
              boxShadow: "inset 0 0 0 1px var(--prot-tenue)",
            }}
          />
          {v.n}
        </span>
      ))}
    </div>
  )
}

/** The legend of what is on the chart, and the ticks that switch measures on (board `legend`,
 *  `scaleP`). */
function Scala({
  detto,
  notte: n,
  formato,
  sguardo: g,
  accese,
}: {
  detto: Meteo
  notte: Notte
  formato: Formato
  sguardo: Sguardo
  accese: Accesa[]
}) {
  const tel = formato === "telefono"
  const legenda = [
    { n: t("meteo.chart.low"), c: strato(28), b: strato(90), note: "" },
    { n: t("meteo.chart.mid"), c: strato(17), b: strato(60), note: "" },
    { n: t("meteo.chart.high"), c: strato(10), b: strato(45), note: "" },
    { n: t("meteo.chart.transparency"), c: "var(--prot-barra)", b: "var(--prot-barra)", note: "" },
    ...accese.map((a) =>
      a === "humidity"
        ? { n: t("meteo.scale.humidity"), c: UMIDITA, b: UMIDITA, note: "" }
        : {
            n: t(`weather.measure.${a}` as Chiave),
            c: "var(--buono-testo)",
            b: "var(--prot-tenue)",
            note: t("meteo.legend.right"),
          },
    ),
    // the condensation's dashed line: the hour's threshold (Beysens)
    ...(accese.includes("condensation")
      ? [{ n: t("meteo.chart.dewThreshold"), c: "transparent", b: "var(--prot-tenue)", note: "" }]
      : []),
  ]
  // a measure the service never sent this night is not offered (board `X.na`)
  const opzioni = SCALA.filter((s) => spenta(s.a, n, detto) !== t("meteo.scale.missing")).map(
    (s) => {
      const perche = spenta(s.a, n, detto)
      const sel = accese.includes(s.a)
      return {
        l: t(s.l),
        sel,
        no: perche !== null,
        titolo: perche ?? t(s.a === "humidity" ? "meteo.scale.left" : "meteo.scale.right"),
        ...(sel ? { colore: s.a === "humidity" ? UMIDITA : "var(--barretta)" } : {}),
        on: () => g.accendi(s.a),
      }
    },
  )
  const conto = accese.length
    ? t(accese.length === 1 ? "meteo.scale.on.one" : "meteo.scale.on", { n: numero(accese.length) })
    : ""
  return (
    <div className={tel ? "al-meteo__colonna-17" : "al-meteo__colonna-4"}>
      <div className={tel ? "al-meteo__riga-27" : "al-meteo__riga-8"}>
        {legenda.map((l) => (
          <span key={l.n} className={tel ? "al-meteo__riga-28" : "al-meteo__riga-9"}>
            <i
              className={tel ? "al-meteo__blocco-13" : "al-meteo__blocco-3"}
              style={{ background: l.c, boxShadow: `inset 0 0 0 1px ${l.b}` }}
            />
            <b className="al-meteo__testo-7">{l.n}</b>
            {!tel && l.note && <span className="al-meteo__testo-8">{l.note}</span>}
          </span>
        ))}
      </div>
      {tel ? (
        <>
          <span className="al-meteo__testo-27">
            {t("meteo.scale.title")} <span className="al-meteo__testo-10">{conto}</span>
          </span>
          <span className="al-meteo__riga-29">
            <PillolaScelta
              forma="spunta"
              fondo="protagonista"
              scorre
              etichetta={t("meteo.scale.title")}
              formato={formato}
              opzioni={opzioni}
            />
          </span>
        </>
      ) : (
        <div className="al-meteo__riga-10">
          <span className="al-meteo__testo-9">
            {t("meteo.scale.title")} <span className="al-meteo__testo-10">{conto}</span>
          </span>
          <PillolaScelta
            forma="spunta"
            fondo="protagonista"
            etichetta={t("meteo.scale.title")}
            formato={formato}
            opzioni={opzioni}
          />
        </div>
      )}
    </div>
  )
}

export const nomeDellaMisura = (c: Codice): string => t(`weather.measure.${c}` as Chiave)
