import { useInfiniteQuery } from "@tanstack/react-query"
import type { CSSProperties } from "react"
import { useSearchParams } from "react-router"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Altre, paginaDopo } from "./Elenco"
import { BarraDeiFiltri } from "./FiltriUsati"
import { Finestra } from "./NotteDelMeteo"
import { Semaforo } from "./Semaforo"
import { Disco } from "./Stanotte"
import { AzioniDelVuoto, Vuoto } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, giornoDellaSettimana, notte, numero, ore, t } from "./i18n"

type Notte = components["schemas"]["Night"]
type Elenco = components["schemas"]["NightList"]

// Quante righe per volta, come l'Archivio: si guarda indietro nel tempo, e chiederne venti per
// volta sarebbe cinque giri per vedere un anno.
const PER_VOLTA = 100

// Mentre la lettura mette i frame nelle notti la pagina si rilegge, o la pista resterebbe ferma: non
// al ritmo della scansione, perche' ogni pagina di notti chiede la Luna all'effemeride.
const MENTRE_LEGGE_MS = 15000

// Quanti oggetti per notte si mostrano: gli altri si contano ("e 2 altri"). Il backend li manda
// gia' dal piu' ripreso.
const OGGETTI_IN_VISTA = 3

// Dove si va a rispondere, deciso dal backend (`spine/nights`): qui c'e' solo **come si dice** e
// dove porta. `never` non ha un'azione: quei frame non hanno una risposta da dare. Il primario va
// al sito, il primo nell'ordine del disegno (sito, archivio, meteo, progetto, casi).
type Dove = Elenco["waiting"][number]["answer_at"]

const RIGA: Record<Dove, { titolo: Chiave; testo: Chiave; dove?: string; vai?: Chiave; primario?: boolean }> = {
  review: { titolo: "nights.waiting.review", testo: "nights.waiting.review.why", dove: "/da-confermare", vai: "nights.waiting.where" },
  site: { titolo: "nights.waiting.site", testo: "nights.waiting.site.why", dove: "/impostazioni/sito", vai: "nights.waiting.site.how", primario: true },
  never: { titolo: "nights.waiting.never", testo: "nights.waiting.never.why" },
}

/**
 * Le **Notti**: quando hai ripreso, da dove, e cosa hai fatto quella sera. Il disegno e' il v29,
 * forma A, il registro: una carta per notte in cinque colonne che si confrontano dall'alto in basso.
 *
 * - **Qui non si calcola niente.** Ore, frame, oggetti, filtri, la barra di ogni oggetto, la Luna e
 *   il meteo arrivano gia' fatti dal backend, che sa quali frame escludere (le copie riscritte non
 *   sono un'altra ora di cielo) e in che ordine mettere i filtri.
 * - **Una notte e' una carta**, anche con due oggetti dentro: spaccarla spezzerebbe le sue ore, e
 *   due carte con la stessa data sembrerebbero un doppione. La vista per oggetto e' l'Archivio.
 * - **Un elenco corto ha due spiegazioni**, e stanno in testa, una riga per motivo: i frame che
 *   aspettano una risposta -- raggruppati dal backend per **dove** si risponde -- e la lettura che
 *   non e' finita. Senza, chi apre la pagina a meta' corsa crede di avere tre notti.
 * - **Non avere notti ha quattro motivi**, e sono quattro risposte diverse: nessun frame, nessun
 *   sito di casa, frame fermi su una domanda, o l'app che non ci e' ancora arrivata.
 * - **Una notte sola si apre dall'indirizzo** (`/notti?notte=<id>`, la usa la ricerca): niente
 *   totali ne' righe di stato, quella notte e il ritorno a tutte.
 */
export function Notti() {
  const [indirizzo] = useSearchParams()
  const scritto = indirizzo.get("notte")
  // solo un id intero positivo si chiede: un indirizzo storto e' una notte che non c'e'
  const una = scritto !== null && /^[1-9][0-9]*$/.test(scritto) ? Number(scritto) : null
  const storta = scritto !== null && una === null
  const elenco = useInfiniteQuery({
    queryKey: ["nights", una],
    enabled: !storta,
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      const { data, error } = await api.GET("/api/v1/nights", {
        params: { query: { limit: PER_VOLTA, offset: pageParam, ...(una ? { night: una } : {}) } },
      })
      if (error) throw new Error(t("nights.failed"))
      return data
    },
    getNextPageParam: paginaDopo,
    refetchInterval: (q) => (q.state.data?.pages.at(-1)?.still_reading ? MENTRE_LEGGE_MS : false),
  })
  const pagine = elenco.data?.pages ?? []
  const righe = pagine.flatMap((p) => p.items)
  const ultima = pagine.at(-1)

  return (
    <div className="as-pagina">
      <div className="as-registro">
        {elenco.isPending && !storta && <InLettura />}
        {elenco.error && (
          <Avviso
            esito="allarme"
            pagina
            azioni={
              <Bottone verso="primario" onClick={() => void elenco.refetch()}>
                {t("nights.retry")}
              </Bottone>
            }
          >
            {elenco.error.message}
          </Avviso>
        )}

        {scritto !== null && (
          <Bottone verso="nudo" a="/notti">
            {t("nights.all")}
          </Bottone>
        )}
        {(storta || (una !== null && ultima && righe.length === 0)) && <Sparita />}

        {scritto === null && ultima && <Testa pagina={ultima} />}
        {scritto === null && ultima && righe.length === 0 && <Niente pagina={ultima} />}

        {righe.length > 0 && (
          <div className="as-registro__elenco" role="list" aria-label={t("nights.title")}>
            {scritto === null && <Capi />}
            {righe.map((riga) => (
              <UnaNotte key={riga.id} notte={riga} />
            ))}
          </div>
        )}

        {ultima && elenco.hasNextPage && (
          <div className="as-registro__carico">
            <span>{t("nights.shown", { n: numero(righe.length), di: numero(ultima.total) })}</span>
            <Altre elenco={elenco} testo="nights.more" />
          </div>
        )}
      </div>
    </div>
  )
}

/** Mentre la pagina chiede le notti: i totali e le prime tre carte tengono il loro posto, cosi'
 *  niente salta quando arrivano. */
function InLettura() {
  return (
    <>
      <div className="as-registro__testa">
        <p className="as-soprattitolo">{t("nights.totals.title")}</p>
        <span className="as-scheletro as-registro__scheletro-cifre" />
      </div>
      <div className="as-registro__elenco" aria-busy="true" aria-label={t("nights.loading")}>
        <span className="as-scheletro as-registro__scheletro" />
        <span className="as-scheletro as-registro__scheletro" />
        <span className="as-scheletro as-registro__scheletro" />
      </div>
    </>
  )
}

/** La notte dell'indirizzo che non c'e' piu': i suoi frame sono stati tolti o spostati. */
function Sparita() {
  return (
    <Vuoto sotto={1} titolo="nights.gone" perche="nights.gone.why">
      <AzioniDelVuoto>
        <Bottone a="/notti">{t("nights.all.short")}</Bottone>
      </AzioniDelVuoto>
    </Vuoto>
  )
}

/** Cosa tiene l'archivio intero, e una riga per ogni cosa che spiega un elenco piu' corto. */
function Testa({ pagina }: { pagina: Elenco }) {
  const tot = pagina.totals
  return (
    <>
      <header className="as-registro__testa">
        <p className="as-soprattitolo">{t("nights.totals.title")}</p>
        <div className="as-registro__totali">
          <p className="as-registro__totale">
            <b>{numero(tot.nights)}</b>
            {t("nights.totals.nights")}
          </p>
          <p className="as-registro__totale">
            <b>{numero(tot.frames)}</b>
            {t("nights.totals.frames")}
          </p>
          {tot.integration_s > 0 && (
            <p className="as-registro__totale">
              <b>{ore(tot.integration_s)}</b>
              {t("nights.totals.hours", { n: ore(tot.integration_s) })}
            </p>
          )}
          {tot.untimed > 0 && (
            <p className="as-registro__totale">
              <b>{numero(tot.untimed)}</b>
              {t("nights.totals.untimed")}
            </p>
          )}
        </div>
        <p className="as-registro__nota">{t("nights.totals.copies")}</p>
      </header>
      {(pagina.waiting.length > 0 || pagina.still_reading > 0) && (
        <div className="as-registro__stati">
          {pagina.waiting.map((gruppo) => (
            <Ferme key={gruppo.answer_at} gruppo={gruppo} />
          ))}
          {pagina.still_reading > 0 && <Lettura pagina={pagina} />}
        </div>
      )}
    </>
  )
}

/** Un gruppo di frame che nessuna notte ha raccolto: quanti sono, e dove si risponde. */
function Ferme({ gruppo }: { gruppo: Elenco["waiting"][number] }) {
  const riga = RIGA[gruppo.answer_at]
  return (
    <Avviso
      esito={riga.dove ? "attesa" : "neutro"}
      titolo={t(riga.titolo, { n: numero(gruppo.frames) })}
      azioni={
        riga.dove &&
        riga.vai && (
          <Bottone verso={riga.primario ? "primario" : "tenue"} a={riga.dove}>
            {t(riga.vai)}
          </Bottone>
        )
      }
    >
      {t(riga.testo)}
    </Avviso>
  )
}

/** La lettura al lavoro: quanti frame devono ancora trovare la loro notte, e quanto ha fatto. */
function Lettura({ pagina }: { pagina: Elenco }) {
  const fatto = pagina.reading_done_pct
  return (
    <Avviso
      esito="lavoro"
      titolo={t("nights.reading", { n: numero(pagina.still_reading) })}
      sotto={
        fatto != null && (
          <div className="as-avanza">
            <div className="as-avanza__pista">
              <div className="as-avanza__riempi" style={{ width: `${fatto}%` }} />
            </div>
          </div>
        )
      }
    >
      {t("nights.reading.why")}
    </Avviso>
  )
}

/** I quattro modi di non avere notti, in ordine di cosa fare: dichiarare il sito (senza, non ne
 *  nascera' mai una), rispondere alle domande, aspettare la lettura, o cominciare a leggere. */
function Niente({ pagina }: { pagina: Elenco }) {
  const senzaCasa = pagina.waiting.some((v) => v.answer_at === "site")
  const ferme = pagina.waiting.length > 0
  const quale: { titolo: Chiave; perche: Chiave; dove?: string; gesto?: Chiave } = senzaCasa
    ? {
        titolo: "nights.empty.noSite",
        perche: "nights.empty.noSite.why",
        dove: "/impostazioni/sito",
        gesto: "nights.empty.noSite.how",
      }
    : ferme
      ? {
          titolo: "nights.empty.waiting",
          perche: "nights.empty.waiting.why",
          dove: "/da-confermare",
          gesto: "nights.waiting.where",
        }
      : pagina.still_reading > 0
        ? { titolo: "nights.empty.notYet", perche: "nights.empty.notYet.why" }
        : {
            titolo: "nights.empty.noFrames",
            perche: "nights.empty.noFrames.why",
            dove: "/impostazioni",
            gesto: "nights.empty.noFrames.how",
          }
  return (
    <Vuoto sotto={1} titolo={quale.titolo} perche={quale.perche}>
      {quale.dove && quale.gesto && (
        <AzioniDelVuoto>
          <Bottone verso="primario" a={quale.dove}>
            {t(quale.gesto)}
          </Bottone>
        </AzioniDelVuoto>
      )}
    </Vuoto>
  )
}

/** Le intestazioni delle cinque colonne, una volta sola in cima: sotto 1180 il foglio le nasconde. */
function Capi() {
  return (
    <div className="as-notte as-notte--capi" aria-hidden="true">
      <span className="as-soprattitolo">{t("nights.col.when")}</span>
      <span className="as-soprattitolo">{t("nights.col.done")}</span>
      <span className="as-soprattitolo">{t("nights.col.objects")}</span>
      <span className="as-soprattitolo">{t("nights.col.filters")}</span>
      <span className="as-soprattitolo">{t("nights.col.sky")}</span>
    </div>
  )
}

/** Una notte: quando e dove, quanto, cosa, con che filtri, che cielo. */
function UnaNotte({ notte: riga }: { notte: Notte }) {
  const data = notte(riga.night_date)
  const giorno = giornoDellaSettimana(riga.night_date)
  return (
    <div
      className="as-carta as-notte"
      role="listitem"
      aria-label={t("nights.card", { data, giorno, sito: riga.site })}
    >
      <div className="as-notte__quando">
        <h2 className="as-notte__data">
          {data} <span className="as-notte__giorno">{t("nights.weekday", { giorno })}</span>
        </h2>
        <p className="as-notte__sito">
          <svg className="as-notte__segno" viewBox="0 0 20 20" aria-hidden="true">
            <use href="#i-m-sito" />
          </svg>
          {riga.site}
        </p>
      </div>
      <div className="as-notte__fatto">
        <Fatto notte={riga} />
      </div>
      <div className="as-notte__oggetti">
        <Oggetti oggetti={riga.objects} />
      </div>
      <div className="as-notte__filtri">
        <BarraDeiFiltri filtri={riga.filters} perFrame={riga.integration_s === 0} />
      </div>
      <div className="as-notte__cielo">
        {riga.moon && (
          <p className="as-luna__fase as-notte__luna">
            <Disco luna={riga.moon} className="as-luna__faccia--giorno" />
            <span className="as-luna__dice">
              <span className="as-luna__nome">{t(`moon.${riga.moon.phase_key}`)}</span>
              <span className="as-luna__quanto">{t("tonight.illuminated", { pct: riga.moon.illumination_pct })}</span>
            </span>
          </p>
        )}
        <Cielo meteo={riga.weather} />
      </div>
    </div>
  )
}

/** Le ore in grande, o "senza tempo" a parole quando nessun frame dice la durata; sotto i frame. */
function Fatto({ notte: riga }: { notte: Notte }) {
  return (
    <>
      {riga.integration_s > 0 ? (
        <p className="as-notte__ore">{t("nights.hours", { h: ore(riga.integration_s) })}</p>
      ) : (
        <p className="as-notte__ore as-notte__ore--parole">{t("nights.untimed", { n: numero(riga.untimed) })}</p>
      )}
      <p className="as-notte__frame">{t("nights.frames", { n: numero(riga.frames) })}</p>
      {riga.integration_s > 0 && riga.untimed > 0 && (
        <p className="as-notte__frame as-notte__frame--senza">{t("nights.untimed", { n: numero(riga.untimed) })}</p>
      )}
    </>
  )
}

/** I primi oggetti, ognuno con la barra delle sue ore in quella notte; gli altri contati. */
function Oggetti({ oggetti }: { oggetti: Notte["objects"] }) {
  const altri = oggetti.length - OGGETTI_IN_VISTA
  return (
    <>
      <ul className="as-notte__lista">
        {oggetti.slice(0, OGGETTI_IN_VISTA).map((o) => (
          <li key={o.key} className="as-notte__oggetto">
            <span className="as-notte__nome">{o.name ?? o.key}</span>
            <span className="as-notte__barra-ore" style={{ "--quanto": `${o.bar_pct}%` } as CSSProperties} />
            <span className="as-notte__cifra">
              {o.integration_s > 0 ? t("nights.hours", { h: ore(o.integration_s) }) : t("nights.object.untimed")}
            </span>
          </li>
        ))}
      </ul>
      {altri > 0 && <p className="as-notte__altri">{t("nights.objects.more", { n: numero(altri) })}</p>}
    </>
  )
}

/** Il cielo vero di quella notte, come lo storico l'ha scritto, o perche' non c'e' ancora. Qui
 *  non si decide niente: lo stato, la data e i numeri arrivano fatti. */
function Cielo({ meteo }: { meteo: Notte["weather"] }) {
  if (meteo.state === "waiting") {
    return meteo.arrives_on ? (
      <>
        <p className="as-notte__attesa">{t("nights.weather.arrives", { data: notte(meteo.arrives_on) })}</p>
        <p className="as-notte__utili">{t("nights.weather.arrives.why")}</p>
      </>
    ) : (
      <>
        <p className="as-notte__attesa">{t("nights.weather.waiting")}</p>
        <p className="as-notte__utili">{t("nights.weather.waiting.why")}</p>
      </>
    )
  }
  if (meteo.state === "unknown") {
    return (
      <>
        <p className="as-notte__meteo">
          <Semaforo livello={null}>{t("nights.weather.unknown")}</Semaforo>
        </p>
        <p className="as-notte__utili">{t("nights.weather.unknown.why")}</p>
      </>
    )
  }
  if (meteo.verdict == null || meteo.cloud_total_pct == null) return <p className="as-notte__utili">{t("nights.weather.none")}</p>
  return (
    <>
      <p className="as-notte__meteo">
        <Semaforo livello={meteo.verdict}>{t(`weather.word.${meteo.verdict}`)}</Semaforo>
        <span className="as-notte__nuvole">{t(`nights.weather.${meteo.verdict}`, { pct: numero(meteo.cloud_total_pct) })}</span>
      </p>
      <p className="as-notte__utili">
        <Finestra cielo={meteo} />
      </p>
    </>
  )
}
