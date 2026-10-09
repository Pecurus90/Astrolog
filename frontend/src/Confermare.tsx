import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Bottone } from "./Bottone"
import { Fragment, useMemo, useState } from "react"

import { Avviso } from "./Avviso"
import { SezioneStessoPezzo } from "./SezioneStessoPezzo"
import { SezioneFiltri } from "./SezioneFiltri"
import { SezioneLuoghi } from "./SezioneLuoghi"
import { SezioneMosaici } from "./SezioneMosaici"
import { SezioneSenzaTipo } from "./SezioneSenzaTipo"
import { api } from "./api/client"
import { motivo } from "./api/motivo"
import type { components } from "./api/schema"
import { type Chiave, numero, t } from "./i18n"
import { type QualeSezione, SEZIONI } from "./sezioniDaConfermare"

type Schema = components["schemas"]
// Le risposte in mano, una voce per sezione, coi nomi dell'API: cosi' l'Applica le manda come
// sono, e una sezione nuova e' una riga qui e non uno stato in piu' da tenere in pari.
type Accumulo = {
  lookalikes: Record<string, Schema["LookalikeEdit"]>
  filters: Record<number, Schema["FilterEdit"]>
  typeless: Record<string, Schema["TypelessFolderEdit"]>
  unclear: Record<string, Schema["CoordinatesEdit"]>
  mosaics: Record<string, Schema["MosaicEdit"]>
}
const VUOTO: Accumulo = {
  lookalikes: {},
  filters: {},
  typeless: {},
  unclear: {},
  mosaics: {},
}

/**
 * Da confermare: le domande che l'app ha su cio' che ha letto, e le risposte.
 *
 * Tre regole che valgono per tutta la pagina (Marco, 14/9/2026):
 *
 * - **le risposte si accumulano** e partono con un solo *Applica*: una sola attesa e un solo
 *   ricalcolo, invece di uno per risposta;
 * - le **sezioni vuote si nascondono**, con in cima quante ne hanno domande: una pagina di undici
 *   titoli vuoti sembra rotta, e il giorno che hai finito vuoi vederlo;
 * - dopo *Applica* **si ricarica dicendo cosa e' cambiato**, coi numeri della ricevuta: l'elenco
 *   di prima direbbe cose non piu' vere, perche' la risposta rifa' il lavoro sulle pose toccate.
 *
 * *Applica* scrive solo le risposte: una domanda guardata e lasciata li' resta aperta (ADR 0014).
 */
export function Confermare() {
  return (
    <div className="as-pagina">
      <LaPagina />
    </div>
  )
}

function LaPagina() {
  const [accumulo, setAccumulo] = useState<Accumulo>(VUOTO)
  // Quante volte la pagina e' stata applicata e riletta: le sezioni si rimontano da capo, o
  // quelle che tengono un modulo in mano mostrerebbero ancora cio' che era scritto prima.
  const [giro, setGiro] = useState(0)
  // L'esito dell'ultimo Applica si chiude: non deve restare a schermo fino al prossimo.
  const [esitoChiuso, setEsitoChiuso] = useState(false)
  const cache = useQueryClient()
  /** Chi scrive nella voce di una sezione: una risposta tolta (`null`) **sparisce** -- lasciarla
   *  dentro vuota manderebbe una domanda a cui l'utente ha smesso di rispondere, e terrebbe acceso
   *  l'Applica su niente. Lo scrittore di una sezione e' **sempre lo stesso**: una sezione
   *  memorizzata non si ridisegna quando si risponde in un'altra. */
  const scrivi = useMemo(() => {
    const fatti: Partial<Record<keyof Accumulo, unknown>> = {}
    return <S extends keyof Accumulo>(sezione: S) =>
      (fatti[sezione] ??= (chiave: string | number, risposta: Accumulo[S][keyof Accumulo[S]] | null) =>
        setAccumulo((prima) => {
          const voce: Record<string | number, unknown> = { ...prima[sezione] }
          if (risposta) voce[chiave] = risposta
          else delete voce[chiave]
          return { ...prima, [sezione]: voce }
        })) as (chiave: string | number, risposta: Accumulo[S][keyof Accumulo[S]] | null) => void
  }, [])

  const pagina = useQuery({
    queryKey: ["review"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/review")
      if (error) throw new Error(t("review.failed"))
      return data
    },
  })
  const modelli = useQuery({
    queryKey: ["filter-models"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/vocab/filter-models")
      if (error) throw new Error(t("review.models.failed"))
      return data.items
    },
  })

  const applica = useMutation({
    mutationFn: async () => {
      // L'Applica porta **l'intera pagina**, non solo la sezione che hai toccato: le liste vuote
      // dicono "di queste non ho risposto", e il contratto le vuole tutte.
      const { data, error } = await api.POST("/api/v1/review/apply", {
        body: {
          lookalikes: Object.values(accumulo.lookalikes),
          filters: Object.values(accumulo.filters),
          // no gear card yet: it waits for its design (ADR 0014)
          gear: [],
          typeless: Object.values(accumulo.typeless),
          unclear: Object.values(accumulo.unclear),
          mosaics: Object.values(accumulo.mosaics),
          // no object card yet: it waits for its design (ADR 0014)
          objects: [],
        },
      })
      if (error) throw new Error(t(motivo(error, RIFIUTI, "review.apply.failed")))
      return data
    },
    onSuccess: async () => {
      // Le risposte mandate non restano in mano: la pagina si rilegge, e cio' che si vede e' cio'
      // che il database dice adesso. Si svuota **dopo** la rilettura: prima, le sezioni rimontate
      // ripartirebbero dalla pagina vecchia.
      await cache.invalidateQueries({ queryKey: ["review"] })
      setAccumulo(VUOTO)
      setGiro((g) => g + 1)
    },
  })

  if (pagina.isPending) return <InLettura />
  if (pagina.error) {
    return (
      <div className="as-conferma">
        <Avviso
          azioni={
            <Bottone verso="primario" onClick={() => void pagina.refetch()}>
              {t("action.retry")}
            </Bottone>
          }
          esito="allarme"
          pagina
        >
          {pagina.error.message}
        </Avviso>
      </div>
    )
  }

  const dati = pagina.data
  const inMano = Object.values(accumulo).reduce((quante, r) => quante + Object.keys(r).length, 0)
  // Quante domande di ogni sezione aspettano ancora: senza risposta salvata e senza una in mano.
  // Dipende da cio' che l'utente ha appena scelto, quindi si conta qui e non nell'API.
  const aspettano: Record<QualeSezione, number | null> = {
    lookalikes: quante(dati.lookalikes, (g) => !accumulo.lookalikes[g.id]),
    filters: quante(dati.filters, (f) => !accumulo.filters[f.id]),
    typeless: quante(dati.typeless, (g) => g.answer === null && !accumulo.typeless[g.key]),
    unclear: quante(dati.unclear, (p) => p.site === null && !accumulo.unclear[p.key]),
    mosaics: quante(dati.mosaics, (m) => m.answer === null && !accumulo.mosaics[m.key]),
  }
  const presenti = (Object.keys(SEZIONI) as QualeSezione[]).filter((s) => aspettano[s] !== null)
  const conta = (
    <p className="as-conferma__conta">
      <b>{numero(dati.to_confirm)}</b> {t("review.count.word", { n: dati.to_confirm })}
    </p>
  )

  // L'esito sta fuori dai due rami: l'Applica che risponde alle ultime domande svuota la pagina.
  const esiti = (
    <>
      {applica.data && !esitoChiuso && (
        <Avviso
          azioni={
            <Bottone piccolo verso="nudo" onClick={() => setEsitoChiuso(true)}>
              {t("frame.close")}
            </Bottone>
          }
          esito="buono"
          pagina
          ruolo="status"
        >
          {t("review.applied", {
            n: numero(applica.data.changed),
            pose: numero(applica.data.requeued),
          })}
        </Avviso>
      )}
      {applica.error && (
        <Avviso esito="allarme" pagina>
          {applica.error.message}
        </Avviso>
      )}
    </>
  )

  // Lo stato in cui la pagina sta quasi sempre: niente indice e niente piede, non c'e' da fare.
  if (presenti.length === 0) {
    return (
      <div className="as-conferma">
        <div className="as-conferma__colonna">
          <div className="as-conferma__testa">{conta}</div>
          {esiti}
          {/* Il conto somma anche Oggetti e Attrezzatura da completare, che qui non hanno ancora
              la loro sezione: "niente" si dice solo se il conto e' zero. */}
          {dati.to_confirm === 0 && (
            <Avviso esito="buono" pagina ruolo="status" titolo={t("review.none.title")}>
              {t("review.none.text")}
            </Avviso>
          )}
        </div>
      </div>
    )
  }

  // Unire due strumenti non si annulla: se fra le risposte in mano ce n'e' una, si dice qui.
  const unisce = Object.values(accumulo.lookalikes).some((r) => r.same)
  const ferma = applica.isPending

  return (
    <div className={ferma ? "as-conferma as-conferma--indice as-conferma--ferma" : "as-conferma as-conferma--indice"}>
      {/* Only above 900 of column: the sheet keeps the index sticky at every width, and in a
          single column it would stay over the questions and take their clicks. */}
      <nav className="as-conferma-indice as-solo-largo" aria-label={t("review.index")} inert={ferma}>
        <ol>
          {presenti.map((s) => (
            <li key={s}>
              <a href={`#${SEZIONI[s].ancora}`}>
                <span>{t(SEZIONI[s].titolo)}</span>
                {aspettano[s] === 0 ? (
                  <span className="as-conferma-indice__fatto" aria-label={t("review.index.done")}>
                    {"\u2713"}
                  </span>
                ) : (
                  <span
                    className="as-conferma-indice__n"
                    aria-label={t("review.index.open", { n: numero(aspettano[s] ?? 0) })}
                  >
                    {numero(aspettano[s] ?? 0)}
                  </span>
                )}
              </a>
            </li>
          ))}
        </ol>
      </nav>

      <div className="as-conferma__colonna" inert={ferma}>
      <div className="as-conferma__testa">
        {conta}
        <p className="as-conferma__regola">{t("review.rule")}</p>
      </div>

      {esiti}
      {/* **Una coda che non si e' potuta leggere non e' una coda vuota.** Senza questa riga, se
          l'elenco dei modelli cade la tendina diventa un catalogo vuoto: chi cerca il suo filtro
          non lo trova, conclude che in commercio non c'e', e lo scrive a mano per sempre. E' il
          principio portato da `old/`, ed e' la bugia piu' costosa di questa pagina. */}
      {modelli.error && <Avviso esito="allarme">{modelli.error.message}</Avviso>}

      {/* L'ordine delle sezioni e' fisso: prima i pezzi, poi come si montano insieme, poi il
          dove e il quando, poi il cielo. Una sezione che si sposta a seconda di cosa contiene non
          si ritrova. */}
      <Fragment key={giro}>
      {!!dati?.lookalikes?.length && (
        <SezioneStessoPezzo
          gruppi={dati.lookalikes}
          risposte={accumulo.lookalikes}
          onRisposta={scrivi("lookalikes")}
        />
      )}
      {!!dati?.filters?.length && (
        <SezioneFiltri
          filtri={dati.filters}
          miei={dati.filter_choices}
          modelli={modelli.data ?? []}
          risposte={accumulo.filters}
          onRisposta={scrivi("filters")}
        />
      )}
      {!!dati?.typeless?.length && (
        <SezioneSenzaTipo
          gruppi={dati.typeless}
          risposte={accumulo.typeless}
          onRisposta={scrivi("typeless")}
        />
      )}
      {!!dati?.unclear?.length && (
        <SezioneLuoghi posti={dati.unclear} risposte={accumulo.unclear} onRisposta={scrivi("unclear")} />
      )}
      {!!dati?.mosaics?.length && (
        <SezioneMosaici
          mosaici={dati.mosaics}
          risposte={accumulo.mosaics}
          onRisposta={scrivi("mosaics")}
        />
      )}
      </Fragment>
      </div>

      {/* Il piede resta in vista e dice **cosa si sta per mandare**: le risposte si accumulano
          scorrendo le sezioni, e un Applica che non dice quante ne porta chiede un salto nel buio.
          Il conto e' dello stato in mano all'utente, non dell'API. */}
      <div className="as-conferma-tutto" role="region" aria-label={t("review.inHand.label")}>
        <p className="as-conferma-tutto__conta" aria-live="polite">
          <b>{numero(inMano)}</b> {t("review.inHand.word", { n: inMano })}
        </p>
        {unisce && (
          <p className="as-conferma-avverte">
            <span>
              <b>{t("review.merge.warning")}</b> {t("review.merge.warning.rest")}
            </span>
          </p>
        )}
        <Bottone
          occupato={ferma}
          verso="primario"
          onClick={() => {
            setEsitoChiuso(false)
            applica.mutate()
          }}
          disabled={ferma || inMano === 0}
        >
          {ferma ? t("review.applying") : t("review.apply")}
        </Bottone>
      </div>
    </div>
  )
}

/** Quante voci di una sezione aspettano ancora; `null` se la sezione non c'e'. */
function quante<V>(voci: V[] | undefined, aspetta: (v: V) => boolean): number | null {
  return voci?.length ? voci.filter(aspetta).length : null
}

/** Mentre legge: lo scheletro tiene il posto dell'indice, del conto e delle sezioni. */
function InLettura() {
  return (
    <div className="as-conferma as-conferma--indice" aria-busy="true" aria-label={t("review.loading")}>
      <div className="as-conferma-indice as-solo-largo" aria-hidden="true">
        {[1, 2, 3, 4, 5].map((n) => (
          <span key={n} className="as-scheletro as-conferma__sk-voce" />
        ))}
      </div>
      <div className="as-conferma__colonna" aria-hidden="true">
        <span className="as-scheletro as-conferma__sk-conto" />
        <span className="as-scheletro as-conferma__sk-frase" />
        <span className="as-scheletro as-conferma__sk-chiusa" />
        <span className="as-scheletro as-conferma__sk-carta" />
        <span className="as-scheletro as-conferma__sk-chiusa" />
      </div>
    </div>
  )
}

/** I rifiuti che l'*Applica* puo' ricevere, detti per nome.
 *
 * Non e' una cortesia: `POST /review/apply` e' **una transazione sola**, quindi uno qualunque di
 * questi annulla anche le risposte buone. Un "non ha funzionato" generico lascerebbe l'utente
 * senza sapere ne' cosa e' stato scritto ne' cosa riparare -- e le tre riparazioni sono diverse:
 * si cambia bersaglio, si ricarica la pagina, si aspetta. */
const RIFIUTI: Record<string, Chiave> = {
  unknown_target: "review.apply.unknownTarget",
  not_found: "review.apply.notFound",
  worker_busy: "review.apply.busy",
  name_taken: "review.apply.nameTaken",
  merge_refused: "review.apply.mergeRefused",
}
