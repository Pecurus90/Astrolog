import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router"

import { api } from "./api/client"
import type { components } from "./api/schema"
import { MENTRE_LEGGE_MS } from "./Notti"
import { durata, giornoDelMese, mesiBrevi, numero, t } from "./i18n"

type Anno = components["schemas"]["YearOut"]
type Giorno = Anno["days"][number]

const CELLA: Record<Giorno["level"], string> = {
  future: "as-heat__cella--fuori",
  none: "as-heat__cella--zero",
  under2: "as-heat__cella--l1",
  "2to4": "as-heat__cella--l2",
  "4to6": "as-heat__cella--l3",
  over6: "as-heat__cella--l4",
}
const LEGENDA = [
  ["none", "dashboard.year.legend.none"],
  ["under2", "dashboard.year.legend.under2"],
  ["2to4", "dashboard.year.legend.2to4"],
  ["4to6", "dashboard.year.legend.4to6"],
  ["over6", "dashboard.year.legend.over6"],
] as const

/** Durante la prima scansione si rilegge da sola, come Notti; a fine corsa la rilegge la barra. */
function useAnno(leggendo: boolean) {
  return useQuery({
    queryKey: ["year"],
    refetchInterval: leggendo ? MENTRE_LEGGE_MS : false,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/year")
      if (error) throw new Error(t("dashboard.year.failed"))
      return data
    },
  })
}

/**
 * L'**anno** (`as-dashboard__anno`, tavola v37): notti, ore, la media a notte e al mese, e un
 * quadretto per giorno colorato per ore riprese, sette righe da lunedi'. Sul telefono non c'e'
 * (la tavola del telefono non lo porta). Durante la prima scansione notti e ore sono *finora* e le medie aspettano.
 */
export function AnnoDellaDashboard({ lettura }: {
  /** La percentuale della prima scansione, o `null` quando non c'e'. */
  lettura: number | null
}) {
  const finora = lettura !== null
  const anno = useAnno(finora).data
  if (!anno) return null
  const titolo = t("dashboard.year.title", { anno: String(anno.year) })
  const nome = { anno: String(anno.year), n: numero(anno.nights), giorno: giornoDelMese(anno.until) }
  const cella = (g: Giorno) => (
    <span key={g.date} className={`as-heat__cella ${CELLA[g.level]}`}
      title={g.level === "future" ? undefined : `${giornoDelMese(g.date)}: ${durata(g.integration_s) ?? ""}`} />
  )
  const vuote = (n: number, chiave: string) => Array.from({ length: n }, (_, i) => <span key={`${chiave}-${i}`} className="as-heat__cella as-heat__cella--vuoto" />)
  const media = (valore: string | null) => (finora || valore === null ? (
    <dd>
      <span className="as-dato--vuoto">{"\u2014"}</span>
      {finora && <span className="as-parziale as-parziale--a-lettura-finita">{t("dashboard.year.later")}</span>}
    </dd>
  ) : <dd>{valore}</dd>)
  const conto = (valore: string) => (
    <dd>
      {valore}
      {finora && <span className="as-parziale as-parziale--finora">{t("dashboard.year.sofar")}</span>}
    </dd>
  )
  const mesi = mesiBrevi()
  return (
    <section className="as-dashboard__anno" aria-labelledby="dash-anno">
      <div className="as-dashboard__capo">
        <p className="as-soprattitolo" id="dash-anno">{titolo}</p>
        {finora ? (
          <span className="as-parziale as-parziale--finora">{t("dashboard.year.reading", { pct: numero(lettura) })}</span>
        ) : (
          <Link to="/statistiche">{t("nav.stats")}</Link>
        )}
      </div>
      <dl className="as-dashboard__medie">
        <div><dt>{t("dashboard.year.nights")}</dt>{conto(numero(anno.nights))}</div>
        <div><dt>{t("dashboard.year.hours")}</dt>{conto(durata(anno.integration_s) ?? "")}</div>
        <div><dt>{t("dashboard.year.perNight")}</dt>{media(anno.per_night_s === null ? null : durata(anno.per_night_s) ?? null)}</div>
        <div><dt>{t("dashboard.year.perMonth")}</dt>{media(anno.nights ? t("dashboard.year.perMonth.value", { n: numero(anno.per_month) }) : null)}</div>
      </dl>
      <div className="as-heat">
        <div>
          <div className="as-heat__intestazione" aria-hidden="true">{mesi.map((m) => <span key={m}>{m}</span>)}</div>
          <div className="as-heat__anno" role="img" aria-label={t("dashboard.year.img", nome)}>
            {vuote(anno.lead_blank, "prima")}
            {anno.days.map(cella)}
          </div>
        </div>
        <p className="as-heat__legenda">
          {LEGENDA.map(([livello, chiave]) => (
            <span key={livello}><i className={`as-heat__campione ${CELLA[livello]}`} />{t(chiave)}</span>
          ))}
        </p>
      </div>
    </section>
  )
}
