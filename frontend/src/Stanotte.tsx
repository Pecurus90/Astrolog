import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router"

import { api } from "./api/client"
import { Avviso } from "./componenti/Avviso"
import type { components } from "./api/schema"
import { tracciatoDellaLuna } from "./disegnoDellaLuna"
import { type Chiave, giornoEMese, numero, oraDelSito, t, unDecimale } from "./i18n"

/**
 * Stanotte (Telaio v76, pastiglia v70): la pastiglia dice il sito e apre il pannello col sito, la
 * Luna e il meteo della notte. I numeri arrivano fatti da `GET /api/v1/tonight`
 * (`docs/domini/effemeridi.md`): la scala della Luna (`moon_in_dark.level`), i tratti senza Luna,
 * le ore di posa.
 *
 * - **Qui non si calcola niente**: si sceglie la frase, mai un numero.
 * - **Ogni vuoto e' una frase, mai un trattino.**
 */

export function useStanotte() {
  return useQuery({
    queryKey: ["tonight"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/tonight")
      if (error) throw new Error(t("tonight.failed"))
      return data
    },
    // Questa rotta campiona una notte di cielo e costa cento volte una lettura: la Luna cambia una
    // volta al giorno e il meteo ogni tre ore, e chi li cambia a mano la butta via. Finche' la prima
    // previsione non arriva la si richiede piu' spesso.
    staleTime: 60 * 60 * 1000,
    refetchInterval: (q) => rileggiOgni(q.state.data),
  })
}

type LunaDetta = components["schemas"]["MoonOut"]
type Notte = components["schemas"]["TonightOut"]

/** Il disco della Luna: il cerchio spento e la parte illuminata. Lo usano le Notti e la Dashboard. */
export function Disco({
  luna,
  className = "",
}: {
  luna: Pick<LunaDetta, "illumination_pct" | "lit_side">
  className?: string
}) {
  const illuminata = tracciatoDellaLuna(luna.illumination_pct, luna.lit_side === "right")
  return (
    <svg
      className={`as-luna__faccia ${className}`.trim()}
      viewBox="-12 -12 24 24"
      aria-hidden="true"
    >
      <circle className="as-luna__disco" cx="0" cy="0" r="10" />
      {illuminata && <path className="as-luna__illuminata" d={illuminata} />}
    </svg>
  )
}

/** Cio' che la pastiglia dice: il sito (la freccia la disegna il telaio), o "Aggiungi sito"; vuoto
 *  finche' non si sa. */
export type PastigliaDetta = {
  sito: string | null
  etichetta: string
  aria: string
  senzaSito: boolean
}

/** La pastiglia dalla risposta di stanotte: senza sito porta ad aggiungerlo, finche' non si sa
 *  (o se non si legge) apre il pannello che lo dice. */
export function usePastiglia(): PastigliaDetta {
  const stanotte = useStanotte()
  const sito = stanotte.data?.site?.name ?? null
  if (sito)
    return {
      sito,
      etichetta: sito,
      aria: t("frame.tonight.aria", { sito }),
      senzaSito: false,
    }
  if (stanotte.data)
    return {
      sito: null,
      etichetta: t("frame.tonight.add"),
      aria: t("frame.tonight.nosite"),
      senzaSito: true,
    }
  return { sito: null, etichetta: "", aria: t("frame.tonight"), senzaSito: false }
}

/** I tre segni del verdetto, come le pillole degli esiti (`Pillola`): il colore non e' mai solo. */
const VERDETTI: Record<"go" | "marginal" | "nogo", { segno: string; esito: Chiave }> = {
  go: { segno: "\u{2713}", esito: "ui.outcome.good" },
  marginal: { segno: "!", esito: "ui.outcome.uncertain" },
  nogo: { segno: "\u{2715}", esito: "ui.outcome.unsuitable" },
}

/** Quando la Luna sta nel buio, nelle parole della risposta di Marco (10/11): dopo, fino, dalle-alle,
 *  tutta la notte. */
function quandoNelBuio(nelBuio: components["schemas"]["MoonInDarkOut"]): string {
  if (nelBuio.from_start && nelBuio.to_end) return t("frame.moon.all")
  if (nelBuio.to_end) return t("frame.moon.after", { da: oraDelSito(nelBuio.since) })
  if (nelBuio.from_start) return t("frame.moon.until", { a: oraDelSito(nelBuio.until) })
  return t("frame.moon.between", { da: oraDelSito(nelBuio.since), a: oraDelSito(nelBuio.until) })
}

/** La frase della Luna per la banda larga, dal gradino che il backend ha gia' deciso. */
export function fraseDellaLuna(notte: Notte): string {
  const nelBuio = notte.moon_in_dark ?? null
  if (nelBuio === null) return t("frame.moon.none")
  if (nelBuio.level === "go") return t("frame.moon.go")
  return t(nelBuio.level === "nogo" ? "frame.moon.nogo" : "frame.moon.marginal", {
    quando: quandoNelBuio(nelBuio),
  })
}

/** Il verdetto della notte con le ore di posa, o la frase che dice che la previsione non c'e'. */
function verdettoDelMeteo(notte: Notte): string {
  const meteo = notte.weather ?? null
  if (meteo?.verdict == null) return t("tonight.weather.none")
  const { segno, esito } = VERDETTI[meteo.verdict]
  const verdetto = t("frame.tonight.verdict", { segno, esito: t(esito) })
  const ore = meteo.exposure_hours ?? null
  if (ore === null) return verdetto
  return ore === 0
    ? t("frame.tonight.exposure.none", { verdetto })
    : t("frame.tonight.exposure", { verdetto, ore: unDecimale(ore) })
}

/** Il buio della notte e i suoi tratti senza Luna: "buio 20:48-05:48, senza Luna 20:48-23:40". */
export function buioDellaNotte(notte: Notte): string {
  const da = notte.chart?.dark_from ?? null
  const a = notte.chart?.dark_until ?? null
  const parti: string[] = []
  if (da && a) parti.push(t("frame.tonight.dark", { da: oraDelSito(da), a: oraDelSito(a) }))
  const tratti = (notte.moonless_dark ?? []).map((s) =>
    t("frame.tonight.stretch", { da: oraDelSito(s.starts_at), a: oraDelSito(s.ends_at) }),
  )
  if (tratti.length > 0) parti.push(t("frame.tonight.moonless", { tratti: tratti.join(", ") }))
  return parti.join(" \u{00b7} ")
}

type Riga = { l: string; v: string; s: string; a: { l: string; a: string } | null }

/** Le tre righe del pannello: sito, Luna, meteo (Telaio v76, `sn.righe`). */
function righeDi(notte: Notte, sito: components["schemas"]["SiteSkyOut"]): Riga[] {
  const cielo = sito.bortle === null ? t("tonight.sky.none") : t("tonight.sky", { n: sito.bortle })
  const luna = notte.moon
  return [
    {
      l: t("frame.tonight.row.site"),
      v: sito.name,
      s: t("frame.tonight.default", { cielo }),
      a: { l: t("frame.tonight.change"), a: "/impostazioni/sito" },
    },
    {
      l: t("frame.tonight.row.moon"),
      v:
        luna === null
          ? t("tonight.notimezone")
          : luna.rise === null
            ? t("frame.tonight.moon.norise", { pct: numero(luna.illumination_pct) })
            : t("frame.tonight.moon", {
                pct: numero(luna.illumination_pct),
                ora: oraDelSito(luna.rise),
              }),
      s: luna === null ? "" : fraseDellaLuna(notte),
      a: null,
    },
    {
      l: t("frame.tonight.row.weather"),
      v: verdettoDelMeteo(notte),
      s: buioDellaNotte(notte),
      a: { l: t("frame.tonight.weather"), a: "/meteo" },
    },
  ]
}

/** Il pannello di Stanotte (Telaio v76, `al-c-telaio__notte`): sotto la pastiglia sul desktop,
 *  sotto la testa sul telefono. */
export function PannelloStanotte({ telefono }: { telefono: boolean }) {
  const stanotte = useStanotte()
  const notte = stanotte.data
  const sito = notte?.site ?? null
  const titolo = notte?.night
    ? t("frame.tonight.title", { giorno: giornoEMese(notte.night) })
    : t("frame.tonight")
  return (
    <div
      className={telefono ? "al-c-telaio__notte al-c-telaio__notte--tel" : "al-c-telaio__notte"}
      role="dialog"
      aria-label={t("frame.tonight")}
      data-menu="1"
    >
      <span className="al-c-telaio__notte-testa">
        <b className="al-c-telaio__notte-tit">{titolo}</b>
      </span>
      {stanotte.isPending && <span className="al-c-telaio__notte-s">{t("tonight.loading")}</span>}
      {stanotte.isError && <Avviso tipo="riga" titolo={t("tonight.failed")} />}
      {notte &&
        sito &&
        righeDi(notte, sito).map((r) => (
          <div className="al-c-telaio__notte-riga" key={r.l}>
            <span className="al-c-telaio__notte-l">{r.l}</span>
            <span className="al-c-telaio__notte-v">
              <b>{r.v}</b>
              <span className="al-c-telaio__notte-s">{r.s}</span>
            </span>
            {r.a && (
              <Link to={r.a.a} className="al-bottone al-bottone--testo al-bottone--piccolo">
                {r.a.l}
              </Link>
            )}
          </div>
        ))}
      <span className="al-c-telaio__notte-gesti">
        <Link to="/meteo" className="al-bottone al-bottone--pieno al-bottone--piccolo">
          {t("frame.tonight.open.weather")}
        </Link>
        <Link
          to="/piano-della-notte"
          className="al-bottone al-bottone--contorno al-bottone--piccolo"
        >
          {t("frame.tonight.open.plan")}
        </Link>
      </span>
    </div>
  )
}

/** Ogni quanto rileggere Stanotte: spesso solo mentre c'e' una notte da dividere e la sua previsione
 *  non e' ancora arrivata; senza fuso non arrivera' mai, e con la previsione basta la scadenza. */
export function rileggiOgni(detto: { moon: unknown; weather?: unknown } | undefined) {
  return detto?.moon && !detto.weather ? 5 * 60 * 1000 : false
}
