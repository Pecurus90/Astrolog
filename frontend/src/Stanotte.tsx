import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { Ref, RefObject } from "react"
import { Link } from "react-router"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Icon } from "./Icons"
import { CieloLetto } from "./ScalaDelCielo"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { tracciatoDellaLuna } from "./disegnoDellaLuna"
import { oraDelSito, t } from "./i18n"
import { Accordo, type Breve, Giudizio, VentoInQuota } from "./NotteDelMeteo"

/**
 * Stanotte (disegno v25-v26): la pastiglia in alto dice il sito e la Luna, e apre il pannello col
 * sito da scegliere, la Luna e il meteo della notte. I numeri arrivano fatti da
 * `GET /api/v1/tonight` (`docs/domini/effemeridi.md`); i siti da `GET /api/v1/sites`.
 *
 * - **Qui non si calcola niente**: ne' la classe di Bortle, ne' da che parte e' illuminata la
 *   Luna. Solo il disegno, che sta in `disegnoDellaLuna.ts`.
 * - **Ogni vuoto e' una frase, mai un trattino.**
 */

function useStanotte() {
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

/** Il disco della Luna: il cerchio spento e la parte illuminata. Lo usano anche le Notti, con la
 *  Luna di quella sera. */
export function Disco({
  luna,
  className = "",
}: {
  luna: Pick<LunaDetta, "illumination_pct" | "lit_side">
  className?: string
}) {
  const illuminata = tracciatoDellaLuna(luna.illumination_pct, luna.lit_side === "right")
  return (
    <svg className={`as-luna__faccia ${className}`.trim()} viewBox="-12 -12 24 24" aria-hidden="true">
      <circle className="as-luna__disco" cx="0" cy="0" r="10" />
      {illuminata && <path className="as-luna__illuminata" d={illuminata} />}
    </svg>
  )
}

/** La pastiglia della barra: il sito e la Luna, e apre Stanotte. Senza sito chiede di sceglierlo. */
export function Pastiglia({
  aperta,
  onApri,
  ref,
}: {
  aperta: boolean
  onApri: () => void
  ref: Ref<HTMLButtonElement>
}) {
  const detto = useStanotte().data
  const sito = detto?.site?.name ?? null
  return (
    <button
      className="as-telaio__pastiglia"
      type="button"
      aria-expanded={aperta}
      aria-controls="stanotte"
      aria-label={sito ? t("tonight.at", { sito }) : t("tonight.nosite.how")}
      onClick={onApri}
      ref={ref}
    >
      <Icon name="m-sito" className="as-telaio__pastiglia-segno" />
      <b>{sito ?? t("tonight.nosite.how")}</b>
      {detto?.moon && <Disco luna={detto.moon} className="as-telaio__pastiglia-luna" />}
    </button>
  )
}

/** Il pannello di Stanotte: sito, Luna, meteo. */
export function Stanotte({
  titolo,
  aperta,
  onChiudi,
}: {
  titolo: RefObject<HTMLHeadingElement | null>
  aperta: boolean
  onChiudi: () => void
}) {
  const stanotte = useStanotte()
  const detto = stanotte.data
  return (
    <aside
      className="as-telaio__stanotte as-stanotte"
      id="stanotte"
      aria-labelledby="stanotte-titolo"
      hidden={!aperta}
    >
      <div className="as-stanotte__testa">
        <h2 className="as-stanotte__titolo" id="stanotte-titolo" tabIndex={-1} ref={titolo}>
          {t("tonight.title")}
        </h2>
        <Bottone verso="nudo" piccolo onClick={onChiudi}>
          {t("frame.close.word")}
        </Bottone>
      </div>
      {stanotte.isPending && <p>{t("tonight.loading")}</p>}
      {stanotte.isError && <Avviso esito="allarme">{t("tonight.failed")}</Avviso>}
      {detto && (
        <>
          <Sito sito={detto.site} />
          {detto.site && (
            <div className="as-stanotte__blocco">
              <span className="as-stanotte__etichetta">{t("tonight.moon")}</span>
              {detto.moon === null ? <span>{t("tonight.notimezone")}</span> : <Luna luna={detto.moon} />}
            </div>
          )}
          {detto.site && detto.moon !== null && (
            <div className="as-stanotte__blocco">
              <span className="as-stanotte__etichetta">{t("tonight.weather")}</span>
              <MeteoDiStanotte meteo={detto.weather ?? null} />
            </div>
          )}
        </>
      )}
    </aside>
  )
}

type SitoDiStanotte = components["schemas"]["SiteSkyOut"]

/** Il blocco del sito: i siti da scegliere, la classe del cielo e il rimando ai siti. */
function Sito({ sito }: { sito: SitoDiStanotte | null }) {
  const cache = useQueryClient()
  const siti = useQuery({
    queryKey: ["sites"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/sites")
      if (error) throw new Error(t("tonight.sites.unread"))
      return data
    },
  })
  const scegli = useMutation({
    mutationFn: async (id: number) => {
      const { error } = await api.POST("/api/v1/sites/{site_id}/default", {
        params: { path: { site_id: id } },
      })
      if (error) throw new Error(t("tonight.sites.failed"))
    },
    // Il sito di casa cambia stanotte, il meteo e l'elenco: si rileggono, non si indovinano.
    onSettled: () => {
      for (const chiave of ["tonight", "sites", "weather"]) {
        void cache.invalidateQueries({ queryKey: [chiave] })
      }
    },
  })
  const elenco = siti.data?.items ?? []
  return (
    <div className="as-stanotte__blocco">
      <span className="as-stanotte__etichetta" id="stanotte-sito">
        {t("tonight.site")}
      </span>
      {sito === null && <span>{t("tonight.nosite")}</span>}
      {elenco.length > 1 && (
        <div className="as-menu__voci" role="radiogroup" aria-labelledby="stanotte-sito">
          {elenco.map((s) => (
            <button
              className="as-menu__voce"
              type="button"
              role="radio"
              aria-checked={s.is_default}
              key={s.id}
              disabled={scegli.isPending}
              onClick={() => !s.is_default && scegli.mutate(s.id)}
            >
              <span className="as-menu__nome">{s.name}</span>
              <span className="as-menu__dove">
                {s.bortle === null ? t("tonight.sky.none") : t("tonight.sky", { n: s.bortle })}
              </span>
            </button>
          ))}
        </div>
      )}
      {scegli.error && <Avviso esito="allarme">{scegli.error.message}</Avviso>}
      {sito && <CieloLetto bortle={sito.bortle} sqm={sito.sky_sqm} />}
      <Link className="as-stanotte__rimando" to="/impostazioni/sito">
        {sito === null ? t("tonight.nosite.how") : t("tonight.sites.manage")}
      </Link>
    </div>
  )
}

/** La Luna: fase, quanto e' illuminata, quando sorge e quando tramonta. */
function Luna({ luna }: { luna: LunaDetta }) {
  return (
    <>
      <span className="as-luna__fase">
        <Disco luna={luna} />
        <span className="as-luna__dice">
          <span className="as-luna__nome">{t(`moon.${luna.phase_key}`)}</span>
          <span className="as-luna__quanto">{t("tonight.illuminated", { pct: luna.illumination_pct })}</span>
        </span>
      </span>
      <Orario quando={luna.rise} verbo="tonight.rise" mai="tonight.rise.never" />
      <Orario quando={luna.set} verbo="tonight.set" mai="tonight.set.never" />
    </>
  )
}

/** Un orario della notte, o la frase che dice che stanotte non succede. */
function Orario({
  quando,
  verbo,
  mai,
}: {
  quando: string | null
  verbo: "tonight.rise" | "tonight.set"
  mai: "tonight.rise.never" | "tonight.set.never"
}) {
  if (quando === null) return <span>{t(mai)}</span>
  return (
    <span>
      {t(verbo)} <b>{oraDelSito(quando)}</b>
    </span>
  )
}

/** Il meteo della notte in corso: il verdetto, le ore utili, l'accordo e il vento in quota, e il
 *  collegamento al Meteo per il resto. */
function MeteoDiStanotte({ meteo }: { meteo: Breve | null }) {
  return (
    <>
      {meteo === null ? (
        <span>{t("tonight.weather.none")}</span>
      ) : (
        <>
          <Giudizio breve={meteo} />
          <Accordo breve={meteo} />
          <VentoInQuota breve={meteo} />
        </>
      )}
      <Link className="as-stanotte__rimando" to="/meteo">
        {t("tonight.weather.open")}
      </Link>
    </>
  )
}

/** Ogni quanto rileggere Stanotte: spesso solo mentre c'e' una notte da dividere e la sua previsione
 *  non e' ancora arrivata; senza fuso non arrivera' mai, e con la previsione basta la scadenza. */
export function rileggiOgni(detto: { moon: unknown; weather?: unknown } | undefined) {
  return detto?.moon && !detto.weather ? 5 * 60 * 1000 : false
}
