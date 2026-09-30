import type { components } from "./api/schema"
import { type Chiave, giornoDellaSettimana, notte, numero, oraDelSito, t } from "./i18n"

type Notte = components["schemas"]["WeatherNightOut"]
type Fattore = Notte["factors"][number]
type Ora = Notte["hours"][number]
type InQuota = Notte["aloft"][number]
// il cielo di una notte, per forma: lo porta una notte del Meteo e una delle Notti
type Cielo = Pick<Notte, "window" | "usable_hours" | "window_hours">
type Breve = components["schemas"]["WeatherBriefOut"]

// Le colonne della tabella, nell'ordine in cui si leggono: prima il cielo, poi l'aria.
const COLONNE: { campo: keyof Ora; titolo: Chiave }[] = [
  { campo: "cloud_total_pct", titolo: "weather.col.total" },
  { campo: "cloud_low_pct", titolo: "weather.col.low" },
  { campo: "cloud_mid_pct", titolo: "weather.col.mid" },
  { campo: "cloud_high_pct", titolo: "weather.col.high" },
  { campo: "temperature_c", titolo: "weather.col.temp" },
  { campo: "humidity_pct", titolo: "weather.col.humidity" },
  { campo: "dew_point_c", titolo: "weather.col.dew" },
  { campo: "wind_kmh", titolo: "weather.col.wind" },
  { campo: "wind_gust_kmh", titolo: "weather.col.gust" },
  { campo: "precip_mm", titolo: "weather.col.precip" },
]

/**
 * Una notte del **Meteo**: il verdetto con l'accordo dei modelli, e -- nelle prime tre -- le ore utili,
 * cosa pesa, le ore e il cielo in quota. Dalla quarta e' una tendenza, e lo dice.
 *
 * Qui non si decide niente: quali notti sono piene, l'accordo e il cielo in quota arrivano fatti.
 */
export function UnaNotte({ notte: n, piene }: { notte: Notte; piene: number }) {
  return (
    <section aria-labelledby={`notte-${n.night}`}>
      <h2 id={`notte-${n.night}`}>
        {t("weather.night", { data: notte(n.night), giorno: giornoDellaSettimana(n.night) })}
      </h2>
      {n.trend && <p>{t("weather.trend", { n: numero(piene) })}</p>}
      <Giudizio breve={n} />
      <Accordo breve={n} />
      <VentoInQuota breve={n} />
      {n.factors.length > 0 && (
        <>
          <h3>{t("weather.factors")}</h3>
          <ul>
            {n.factors.map((f) => (
              <li key={f.code}>
                <UnFattore fattore={f} />
              </li>
            ))}
          </ul>
        </>
      )}
      {!n.trend && (
        <>
          <details>
            <summary>{t("weather.hours")}</summary>
            <OraPerOra ore={n.hours} />
          </details>
          <details>
            <summary>{t("weather.aloft")}</summary>
            <CieloInQuota ore={n.aloft} />
          </details>
        </>
      )}
    </section>
  )
}

/** Su quali ore si e' giudicato, e quante di quelle sono serene: la stessa frase nel Meteo e nelle
 *  Notti, perche' e' lo stesso riassunto. */
export function Finestra({ cielo: c }: { cielo: Cielo }) {
  if (c.window == null) return <>{t("weather.window.none")}</>
  if (c.window_hours == null) return null
  if (c.usable_hours == null) return <>{t(`weather.window.${c.window}`, { su: numero(c.window_hours) })}</>
  return <>{t(`weather.usable.${c.window}`, { n: numero(c.usable_hours), su: numero(c.window_hours) })}</>
}

function UnFattore({ fattore: f }: { fattore: Fattore }) {
  const cosa = t(`weather.factor.${f.code}`, { v: numero(f.value), s: numero(f.threshold) })
  if (f.since === null || f.until === null) return <>{cosa}</>
  const quando =
    f.hours === 1
      ? t("weather.factor.at", { da: oraDelSito(f.since) })
      : t("weather.factor.span", { da: oraDelSito(f.since), a: oraDelSito(f.until), n: numero(f.hours) })
  return (
    <>
      {cosa} {quando}
    </>
  )
}

/** Un valore della tabella: il numero, o la parola che dice che il servizio non lo da'. */
function valore(v: number | null) {
  return v === null ? t("weather.unknown") : numero(v)
}

/** Una fascia come la da' il servizio: da-a, sotto, sopra, o niente; e un valore solo quando i
 *  due estremi coincidono (il seeing di Meteoblue). */
function fascia(da: number | null, a: number | null) {
  if (da !== null && da === a) return numero(da)
  if (da !== null && a !== null) return t("weather.range", { da: numero(da), a: numero(a) })
  if (a !== null) return t("weather.range.below", { a: numero(a) })
  if (da !== null) return t("weather.range.above", { da: numero(da) })
  return t("weather.unknown")
}

function OraPerOra({ ore }: { ore: Ora[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th scope="col">{t("weather.col.at")}</th>
          <th scope="col">{t("weather.col.sky")}</th>
          {COLONNE.map((c) => (
            <th key={c.campo} scope="col">
              {t(c.titolo)}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {ore.map((o) => (
          <tr key={o.at}>
            <th scope="row">{oraDelSito(o.at)}</th>
            <td>{t(`weather.sky.${o.sky}`)}</td>
            {COLONNE.map((c) => {
              const v = o[c.campo]
              return <td key={c.campo}>{valore(typeof v === "number" ? v : null)}</td>
            })}
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function CieloInQuota({ ore }: { ore: InQuota[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th scope="col">{t("weather.col.at")}</th>
          <th scope="col">{t("weather.col.wind700")}</th>
          <th scope="col">{t("weather.col.wind250")}</th>
          <th scope="col">{t("weather.col.wind200")}</th>
          <th scope="col">{t("weather.col.seeing")}</th>
          <th scope="col">{t("weather.col.transparency")}</th>
          <th scope="col">{t("weather.col.aerosol")}</th>
          <th scope="col">{t("weather.col.dust")}</th>
        </tr>
      </thead>
      <tbody>
        {ore.map((o) => (
          <tr key={o.at}>
            <th scope="row">{oraDelSito(o.at)}</th>
            <td>{valore(o.wind_700hpa_kmh)}</td>
            <td>{valore(o.wind_250hpa_kmh)}</td>
            <td>{valore(o.wind_200hpa_kmh)}</td>
            <td>{fascia(o.seeing_from, o.seeing_to)}</td>
            <td>{fascia(o.transparency_from, o.transparency_to)}</td>
            <td>{valore(o.aerosol_optical_depth)}</td>
            <td>{valore(o.dust_ugm3)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

/** Il riassunto di una notte che dice anche Stanotte: una notte del Meteo lo porta tutto. */
export type { Breve }

/** Il verdetto, le nuvole in media e le ore utili: la prima riga di una notte. */
export function Giudizio({ breve: b }: { breve: Breve }) {
  return (
    <p>
      {t(b.verdict === null ? "weather.verdict.none" : `weather.verdict.${b.verdict}`)}{" "}
      {b.cloud_total_pct !== null && t("weather.cloud", { pct: numero(b.cloud_total_pct) })}{" "}
      <Finestra cielo={b} />
    </p>
  )
}

/** Quanti modelli dicono la stessa cosa del verdetto: e' cio' che dice quanto fidarsi. */
export function Accordo({ breve: b }: { breve: Breve }) {
  if (b.verdict === null) return null
  const quanti = b.agreement[b.verdict]
  return (
    <p>
      {t(`weather.agreement.${b.verdict}`, {
        n: numero(quanti),
        su: numero(b.agreement.total),
      })}
    </p>
  )
}

// "piu' forte di 0 notti su 10" e "di 10 notti su 10" non si dicono: agli estremi le loro frasi
const FORMA_DEI_DECIMI: Record<number, ".zero" | ".one" | ".ten"> = { 0: ".zero", 1: ".one", 10: ".ten" }

/** Il vento in quota della notte, accanto al suo solito: quante notti su dieci dell'ultimo anno, da
 *  quel sito, ne avevano meno. Senza la storia del sito lo si dice, non si inventa. */
export function VentoInQuota({ breve: b }: { breve: Breve }) {
  if (b.wind_700hpa_kmh === null) return null
  const v = numero(b.wind_700hpa_kmh)
  return (
    <p>
      {b.wind_700hpa_tenths === null
        ? t("weather.wind700.nobase", { v })
        : t(`weather.wind700${FORMA_DEI_DECIMI[b.wind_700hpa_tenths] ?? ""}`, {
            v,
            n: numero(b.wind_700hpa_tenths),
          })}
    </p>
  )
}
