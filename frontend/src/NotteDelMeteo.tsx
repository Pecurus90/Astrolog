import { Fragment, type ReactNode, useId, useState } from "react"

import { Bottone } from "./Bottone"
import { CARTE_GRANDI, CARTE_PICCOLE, CartaDelParametro, CartaDelTelefono, alPosto, parola } from "./CartaDelParametro"
import { CieloDelleNubi } from "./CieloDelleNubi"
import type { components } from "./api/schema"
import { type Chiave, giornoENumero, numero, oraDelSito, t } from "./i18n"
import { Semaforo } from "./Semaforo"

type Notte = components["schemas"]["WeatherNightOut"]
type Misura = Notte["measures"][number]
type Scala = components["schemas"]["WeatherScaleOut"]
type Seeing = components["schemas"]["WeatherSeeingOut"]
// il cielo di una notte, per forma: lo porta una notte del Meteo e una delle Notti
type Cielo = Pick<Notte, "window" | "usable_hours" | "window_hours">
type Breve = components["schemas"]["WeatherBriefOut"]

// dove non si passa col mouse (telefono, tablet) la frase d'aiuto dice di toccare
const senzaMouse = () => typeof window.matchMedia === "function" && window.matchMedia("(hover: none)").matches

/** Il nome della notte, col giorno della sera: *Notte di sabato 3*. */
export function nomeDellaNotte(n: Notte, prima: boolean): string {
  const nome = t("weather.night.name", { giorno: giornoENumero(n.night) })
  if (n.trend) return `${nome} \u00b7 ${t("weather.night.trend")}`
  return prima ? `${nome} \u00b7 ${t("weather.night.tonight")}` : nome
}

/** Una voce della fila delle notti: il giorno, il semaforo, le ore serene o quelle di buio. */
export function VoceDellaNotte({ notte: n }: { notte: Notte }) {
  return (
    <>
      <b>{giornoENumero(n.night, true)}</b>
      <Semaforo livello={n.verdict}>{verdetto(n)}</Semaforo>
      <span className="as-voce-notte__ore">{oreDellaVoce(n)}</span>
    </>
  )
}

function oreDellaVoce(n: Notte): string {
  if (n.trend) return t("weather.night.dark", { n: numero(n.window_hours ?? 0) })
  if (!n.usable_hours || !n.usable_since || !n.usable_until) return t("weather.night.noneClear")
  return t("weather.night.clear", {
    n: numero(n.usable_hours),
    da: oraDelSito(n.usable_since).slice(0, 2),
    a: oraDelSito(n.usable_until).slice(0, 2),
  })
}

/** La parola del verdetto, una sola in tutta l'app; senza notte o senza nuvole lo dice. */
function verdetto(n: Breve): string {
  if (n.window === null) return t("weather.verdict.noNight")
  return n.verdict === null ? t("weather.verdict.unknown") : t(`weather.word.${n.verdict}`)
}

/**
 * Una notte piena del **Meteo**: in testa le ore serene col semaforo e l'accordo dei modelli,
 * accanto cio' che pesa senza cambiarlo, sotto le carte delle misure nell'ordine che il backend
 * ha dato. Qui non si decide niente: giudizi, ore e ordine arrivano scritti.
 */
export function SchedaDellaNotte({ notte: n, prima, scale, seeing, telefono }: {
  notte: Notte; prima: boolean; scale: Scala[]; seeing: Seeing
  /** Sul telefono il verdetto sta in testa alla pagina e le misure sono carte piccole: quale e' aperta lo sa la pagina. */
  telefono?: { aperta: Misura["code"] | null; apri: (c: Misura["code"] | null) => void } | undefined
}) {
  const ore = n.hours.filter((o) => o.shown)
  // l'ora che il filo sul cielo indica: porta tutte le carte a quell'ora
  const [ora, setOra] = useState<number | null>(null)
  const qui = ora === null ? undefined : ore[ora]
  const carta = (m: Misura) => (
    <CartaDelParametro key={m.code} misura={m} notte={n} ore={ore} scala={scale.find((s) => s.code === m.code)} seeing={seeing}
      oraDelCielo={ora} />
  )
  return (
    <>
      {!telefono && (
        <div className="as-meteo__capo-notte">
          <CapoDellaNotte notte={n} prima={prima} />
          {n.window !== null && <Pesano notte={n} />}
        </div>
      )}
      {/* senza buio nessuna ora e' giudicata: le carte direbbero "non fornito" a dati che ci sono */}
      {n.window !== null && (
        <>
          <div className="as-meteo__parte">
            <div className="as-meteo__capo">
              <p className="as-soprattitolo">{t("weather.sky.title")}</p>
              <span>{t(senzaMouse() ? "weather.sky.hint.touch" : "weather.sky.hint")}</span>
            </div>
            <CieloDelleNubi notte={n} ore={ore} scale={scale} seeing={seeing} ora={ora} scegli={setOra} telefono={telefono !== undefined} />
          </div>
          <div className="as-meteo__parte">
            <div className="as-meteo__capo">
              <p className="as-soprattitolo">{qui ? t("weather.cards.at", { ora: oraDelSito(qui.at) }) : t("weather.cards")}</p>
            </div>
            {telefono ? (
              <div className="as-tel-carte">
                {[...alPosto(n.measures, CARTE_GRANDI), ...alPosto(n.measures, CARTE_PICCOLE)].map((m) => {
                  const aperta = telefono.aperta === m.code
                  const id = `tel-${n.night}-${m.code}`
                  return (
                    <Fragment key={m.code}>
                      <CartaDelTelefono misura={m} notte={n} ore={ore} scala={scale.find((s) => s.code === m.code)} aperta={aperta} governa={id}
                        apri={() => telefono.apri(aperta ? null : m.code)} />
                      <div className="as-tel-dettaglio" id={id} hidden={!aperta}>{aperta && carta(m)}</div>
                    </Fragment>
                  )
                })}
              </div>
            ) : (
              <>
                <div className="as-parametri">{alPosto(n.measures, CARTE_GRANDI).map(carta)}</div>
                <div className="as-parametri as-parametri--piccole">{alPosto(n.measures, CARTE_PICCOLE).map(carta)}</div>
              </>
            )}
          </div>
        </>
      )}
    </>
  )
}

/** Il nome della notte, le ore serene col semaforo e da che ora a che ora. `segno` sta accanto al
 *  semaforo: sul telefono dice che il verdetto si tocca. */
export function CapoDellaNotte({ notte: n, prima, segno }: { notte: Notte; prima: boolean; segno?: ReactNode }) {
  const finestra = n.window ?? "dark"
  const ore = n.usable_hours ?? 0
  return (
    <div className="as-meteo__notte">
      <h2 className="as-meteo__notte-nome">{nomeDellaNotte(n, prima)}</h2>
      <div className="as-meteo__verdetto">
        {n.window === null ? (
          <span className="as-meteo__parola">{verdetto(n)}</span>
        ) : (
          <>
            <p className="as-meteo__grande">
              {ore > 0 ? (
                <>
                  <b>{t("weather.clear.hours", { n: numero(ore) })}</b> {t(`weather.clear.${finestra}`, { n: numero(ore) })}
                </>
              ) : (
                <>
                  <b>{t("weather.clear.none")}</b> {t(`weather.clear.none.${finestra}`)}
                </>
              )}
            </p>
            {n.verdict === null ? <span className="as-meteo__parola">{verdetto(n)}</span> : <Semaforo livello={n.verdict} grande>{verdetto(n)}</Semaforo>}
            {segno}
          </>
        )}
      </div>
      <p className="as-meteo__quando">
        {n.usable_hours && n.usable_since && n.usable_until ? (
          <>
            <b>{t("weather.clear.when", { n: numero(n.usable_hours), da: oraDelSito(n.usable_since), a: oraDelSito(n.usable_until) })}</b>
            {" \u00b7 "}
          </>
        ) : null}
        {n.verdict !== null && t("weather.clear.agreement", { n: numero(n.agreement[n.verdict]), su: numero(n.agreement.total) })}
      </p>
    </div>
  )
}

const IN_VISTA = 2

/** Cio' che pesa: le misure che il backend dice incerte o niente, con la loro parola e le ore.
 *  La Luna dice quanto e' illuminata, in che ore e' su e cosa resta nelle altre. */
function Pesano({ notte: n }: { notte: Notte }) {
  const pesano = n.measures.filter((m) => m.weighs)
  // in vista i primi due, i piu' gravi: arrivano gia' in ordine
  const resto = pesano.slice(IN_VISTA)
  const [aperto, setAperto] = useState(false)
  const id = useId()
  const voce = (m: Misura) => (
    <li key={m.code}>
      {m.level && <Semaforo livello={m.level}>{parola(m.code, m.level)}</Semaforo>}
      <span>
        <b>{t(`weather.measure.${m.code}` as Chiave)}</b> {quando(m)}
      </span>
    </li>
  )
  return (
    <div className="as-pesano">
      <p>{t("weather.weighs")}</p>
      {pesano.length === 0 ? <p>{t("weather.weighs.none")}</p> : <ul>{pesano.slice(0, IN_VISTA).map(voce)}</ul>}
      {resto.length > 0 && (
        <>
          <Bottone verso="nudo" piccolo aggiunta="as-pesano__altri" governa={id} aperto={aperto} onClick={() => setAperto(!aperto)}>
            <span>{t("weather.weighs.more", { n: numero(resto.length) })}</span>
          </Bottone>
          <ul className="as-pesano__resto" id={id} hidden={!aperto}>{resto.map(voce)}</ul>
        </>
      )}
    </div>
  )
}

/** La Luna dice le ore in cui e' su (non quelle della parola) e cosa resta nelle ore senza. */
function quandoLaLuna(m: Misura): string {
  if (!m.known_since || !m.known_until || (m.level !== "nogo" && m.level !== "marginal")) return ""
  const valori = { pct: numero(m.value ?? 0), da: oraDelSito(m.known_since), a: oraDelSito(m.known_until) }
  if (m.known_from_start && m.known_to_end) return t("weather.weighs.moon.all", valori)
  const forma = m.known_to_end ? "rises" : m.known_from_start ? "sets" : "middle"
  return t(`weather.weighs.moon.${forma}.${m.level}`, valori)
}

/** Le ore in cui una misura pesa, come le dice la riga degli altri fattori. */
export function quando(m: Misura): string {
  if (m.code === "moon") return quandoLaLuna(m)
  if (!m.since || !m.until) return ""
  if (m.code === "visibility") return t("weather.weighs.fog", { da: oraDelSito(m.since), a: oraDelSito(m.until), n: numero(m.hours) })
  return t("weather.weighs.span", { da: oraDelSito(m.since), a: oraDelSito(m.until), n: numero(m.hours) })
}

/** Una notte dalla quarta in poi: le ore di buio, il semaforo, le nuvole e l'accordo, e la nota
 *  che dice perche' non c'e' altro. */
export function TendenzaDellaNotte({ notte: n }: { notte: Notte }) {
  return (
    <>
      <CapoDellaTendenza notte={n} />
      <NotaDellaTendenza />
    </>
  )
}

/** Perche' una notte in tendenza non ha altro. */
export function NotaDellaTendenza() {
  return <p className="as-meteo__tendenza-nota">{t("weather.trend.note")}</p>
}

/** La testa di una notte in tendenza: sul telefono sta in testa alla pagina, da sola. */
export function CapoDellaTendenza({ notte: n }: { notte: Notte }) {
  return (
      <div className="as-meteo__notte">
        <h2 className="as-meteo__notte-nome">{nomeDellaNotte(n, false)}</h2>
        <div className="as-meteo__verdetto">
          <p className="as-meteo__grande">
            <b>{t("weather.clear.hours", { n: numero(n.window_hours ?? 0) })}</b> {t("weather.clear.trend")}
          </p>
          <Semaforo livello={n.verdict} grande>{verdetto(n)}</Semaforo>
        </div>
        <p className="as-meteo__quando">
          {n.cloud_total_pct !== null && t("weather.clear.trendWhen", { pct: numero(n.cloud_total_pct) })}
          {n.verdict !== null && ` \u00b7 ${t("weather.clear.agreement", { n: numero(n.agreement[n.verdict]), su: numero(n.agreement.total) })}`}
        </p>
      </div>
  )
}

/** Su quali ore si e' giudicato, e quante di quelle sono serene: la stessa frase in Stanotte e
 *  nelle Notti, perche' e' lo stesso riassunto. */
export function Finestra({ cielo: c }: { cielo: Cielo }) {
  if (c.window == null) return <>{t("weather.window.none")}</>
  if (c.window_hours == null) return null
  if (c.usable_hours == null) return <>{t(`weather.window.${c.window}`, { su: numero(c.window_hours) })}</>
  return <>{t(`weather.usable.${c.window}`, { n: numero(c.usable_hours), su: numero(c.window_hours) })}</>
}

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
