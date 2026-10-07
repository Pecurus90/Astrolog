import { useInfiniteQuery } from "@tanstack/react-query"
import { Link } from "react-router"

import { Avviso } from "./Avviso"
import { Finestra } from "./NotteDelMeteo"
import { Altre, paginaDopo } from "./Elenco"
import { Dettaglio, Riga } from "./Riga"
import { TempoDellePose } from "./TempoDellePose"
import { AzioniDelVuoto, Vuoto } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, giornoDellaSettimana, notte, numero, t } from "./i18n"

type Notte = components["schemas"]["Night"]
type Elenco = components["schemas"]["NightList"]

// Quante righe per volta, come l'Archivio: si guarda indietro nel tempo, e chiederne venti per
// volta sarebbe cinque giri per vedere un anno.
const PER_VOLTA = 100

// Dove si va a rispondere, deciso dal backend (`spine/nights`): qui c'e' solo **come si dice** e
// dove porta il collegamento. `never` non ne ha uno: quelle pose non hanno una risposta da dare,
// e un collegamento porterebbe davanti a un elenco dove non compaiono.
type Dove = Elenco["waiting"][number]["answer_at"]

const GESTO: Record<Dove, { frase: Chiave; dove?: string; vai?: Chiave }> = {
  review: { frase: "nights.waiting.review", dove: "/da-confermare", vai: "nights.waiting.where" },
  site: { frase: "nights.waiting.site", dove: "/impostazioni", vai: "nights.empty.noSite.how" },
  never: { frase: "nights.waiting.never" },
}

// Il gruppo che, quando non c'e' nessuna notte, dice che non ne nascera' **mai** una finche'
// l'utente non dichiara da dove osserva.
const SITO = "site"

/**
 * Le **Notti**: quando hai ripreso, da dove, e cosa hai fatto quella sera.
 *
 * - **Qui non si calcola niente.** Ore, pose, oggetti e filtri arrivano gia' fatti dal backend,
 *   che sa quali pose escludere (le copie riscritte non sono un'altra ora di cielo) e in che
 *   ordine mettere i filtri.
 * - **Una notte e' una riga**, anche con due oggetti dentro: spaccarla spezzerebbe le sue ore, e
 *   due righe con la stessa data sembrerebbero un doppione. La vista per oggetto e' l'Archivio.
 * - **Un elenco corto ha due spiegazioni**, e stanno in cima: i frame che aspettano una risposta
 *   -- raggruppati dal backend per **dove** si risponde, che non e' sempre *Da confermare* -- e la
 *   lettura che non e' finita. Senza, chi apre la pagina a meta' corsa crede di avere tre notti.
 * - **Non avere notti ha quattro motivi**, e sono quattro risposte diverse: nessun frame, nessun
 *   sito di casa, frame fermi su una domanda, o l'app che non ci e' ancora arrivata. Confonderli
 *   manda l'utente a sistemare la cosa sbagliata.
 */
export function Notti() {
  const elenco = useInfiniteQuery({
    queryKey: ["nights"],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      const { data, error } = await api.GET("/api/v1/nights", {
        params: { query: { limit: PER_VOLTA, offset: pageParam } },
      })
      if (error) throw new Error(t("nights.failed"))
      return data
    },
    getNextPageParam: paginaDopo,
  })
  const pagine = elenco.data?.pages ?? []
  const righe = pagine.flatMap((p) => p.items)
  const ultima = pagine.at(-1)

  return (
    <div className="as-pagina">

      {elenco.isPending && <p>{t("app.loading")}</p>}
      {elenco.error && <Avviso esito="allarme">{elenco.error.message}</Avviso>}

      {ultima && <Cappello pagina={ultima} />}

      {ultima && righe.length === 0 && <Niente pagina={ultima} />}

      {righe.length > 0 && (
        <ul aria-label={t("nights.title")}>
          {righe.map((riga) => (
            <li key={riga.id}>
              <UnaNotte notte={riga} />
            </li>
          ))}
        </ul>
      )}

      <Altre elenco={elenco} testo="nights.more" />
    </div>
  )
}

/** Cosa tiene l'archivio intero, e le cose che spiegano un elenco piu' corto del previsto. */
function Cappello({ pagina }: { pagina: Elenco }) {
  return (
    <>
      <p>
        {t("nights.totals", { notti: numero(pagina.totals.nights) })}{" "}
        {t("nights.totals.frames", { n: numero(pagina.totals.frames) })}{" "}
        <TempoDellePose secondi={pagina.totals.integration_s} senzaTempo={pagina.totals.untimed} />
      </p>
      {pagina.still_reading > 0 && (
        <Avviso esito="attesa">{t("nights.reading", { n: numero(pagina.still_reading) })}</Avviso>
      )}
      {pagina.waiting.map((gruppo) => (
        <Ferme key={gruppo.answer_at} gruppo={gruppo} />
      ))}
    </>
  )
}

/** Un gruppo di pose che nessuna notte ha raccolto: quante sono, e dove si risponde. */
function Ferme({ gruppo }: { gruppo: Elenco["waiting"][number] }) {
  const gesto = GESTO[gruppo.answer_at]
  return (
    <p>
      {t(gesto.frase, { n: numero(gruppo.frames) })}{" "}
      {gesto.dove && gesto.vai && <Link to={gesto.dove}>{t(gesto.vai)}</Link>}
    </p>
  )
}

/** I quattro modi di non avere notti, in ordine di cosa fare: dichiarare il sito (senza, non ne
 *  nascera' mai una), rispondere alle domande, aspettare la lettura, o cominciare a leggere. */
function Niente({ pagina }: { pagina: Elenco }) {
  const senzaCasa = pagina.waiting.some((v) => v.answer_at === SITO)
  const ferme = pagina.waiting.length > 0
  const quale: { titolo: Chiave; perche: Chiave; dove?: string; gesto?: Chiave } = senzaCasa
    ? {
        titolo: "nights.empty.noSite",
        perche: "nights.empty.noSite.why",
        dove: "/impostazioni",
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
          <Link to={quale.dove}>{t(quale.gesto)}</Link>
        </AzioniDelVuoto>
      )}
    </Vuoto>
  )
}

/** Un filtro col tempo che gli e' stato dato. Il tempo passa da `TempoDellePose`, che e' la casa
 *  della regola "le ore **solo se ci sono**": un filtro le cui pose non dicono la durata ha
 *  ripreso, e non si sa per quanto -- "0 h" direbbe che non ha ripreso niente. */
function UnFiltro({ filtro }: { filtro: Notte["filters"][number] }) {
  return (
    <>
      {filtro.name}
      {/* Lo spazio solo se il tempo si vede: quando il mattone non scrive niente, il nome
          resterebbe attaccato alla virgola che separa dal filtro dopo ("Lum , OIII 2 h"). */}
      {filtro.integration_s > 0 && " "}
      <TempoDellePose secondi={filtro.integration_s} senzaTempo={0} />
    </>
  )
}

/** Una notte: che giorno era, da dove, cosa hai ripreso e con che filtri. */
function UnaNotte({ notte: riga }: { notte: Notte }) {
  return (
    <Riga
      nome={t("nights.when", {
        data: notte(riga.night_date),
        giorno: giornoDellaSettimana(riga.night_date),
      })}
      dettagli={
        <>
          <Dettaglio>{t("nights.at", { sito: riga.site })}</Dettaglio>{" "}
          <Dettaglio>{t("nights.frames", { n: numero(riga.frames) })}</Dettaglio>{" "}
          <Dettaglio>
            <TempoDellePose secondi={riga.integration_s} senzaTempo={riga.untimed} />
          </Dettaglio>{" "}
          <Dettaglio>{riga.objects.map((o) => o.name ?? o.key).join(", ")}</Dettaglio>{" "}
          {riga.moon && (
            <Dettaglio>
              {t("nights.moon", {
                fase: t(`moon.${riga.moon.phase_key}`),
                pct: numero(riga.moon.illumination_pct),
              })}
            </Dettaglio>
          )}{" "}
          <Dettaglio>
            <CieloDiQuellaNotte meteo={riga.weather} />
          </Dettaglio>{" "}
          <Dettaglio>
            {riga.filters.length === 0
              ? t("nights.noFilter")
              : riga.filters.map((f, i) => (
                  <span key={f.name}>
                    {i > 0 && ", "}
                    <UnFiltro filtro={f} />
                  </span>
                ))}
          </Dettaglio>
        </>
      }
    />
  )
}

/** Il cielo vero di quella notte, come lo storico l'ha scritto: le nuvole nel buio e le ore
 *  serene; oppure perche' non c'e' ancora, o non ci sara'. Qui non si decide niente: lo stato e i
 *  numeri arrivano fatti. */
function CieloDiQuellaNotte({ meteo }: { meteo: Notte["weather"] }) {
  if (meteo.state === "waiting") return <>{t("nights.weather.waiting")}</>
  if (meteo.state === "unknown") return <>{t("nights.weather.unknown")}</>
  if (meteo.verdict == null || meteo.cloud_total_pct == null) return <>{t("nights.weather.none")}</>
  return (
    <>
      {t(`nights.weather.${meteo.verdict}`, { pct: numero(meteo.cloud_total_pct) })}{" "}
      <Finestra cielo={meteo} />
    </>
  )
}
