import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Bottone } from "./Bottone"
import { Fragment, useMemo, useState } from "react"

import { Avviso } from "./Avviso"
import { DomandaAperta, Risposta } from "./Domanda"
import { SezioneStessoPezzo } from "./SezioneStessoPezzo"
import { SezioneAttrezzatura } from "./SezioneAttrezzatura"
import { SezioneFiltri } from "./SezioneFiltri"
import { SezioneLuoghi } from "./SezioneLuoghi"
import { SezioneMosaici } from "./SezioneMosaici"
import { SezioneOggetti } from "./SezioneOggetti"
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
  gear: Record<string, Schema["GearEdit"]>
  objects: Record<string, Schema["ObjectEdit"]>
  typeless: Record<string, Schema["TypelessFolderEdit"]>
  unclear: Record<string, Schema["CoordinatesEdit"]>
  mosaics: Record<string, Schema["MosaicEdit"]>
}
const VUOTO: Accumulo = {
  lookalikes: {},
  filters: {},
  gear: {},
  objects: {},
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
  // La domanda aperta, una in tutta la pagina: `undefined` finche' non si sceglie, e allora e'
  // la prima senza risposta. E le sezioni finite che l'utente ha riaperto.
  const [scelta, setScelta] = useState<string | undefined>(undefined)
  const [riaperte, setRiaperte] = useState<readonly QualeSezione[]>([])
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
          gear: Object.values(accumulo.gear),
          typeless: Object.values(accumulo.typeless),
          unclear: Object.values(accumulo.unclear),
          mosaics: Object.values(accumulo.mosaics),
          objects: Object.values(accumulo.objects),
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
      setScelta(undefined)
      setRiaperte([])
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
  // Per ogni sezione, le sue domande come le vede la pagina: la chiave, e se ha una risposta
  // salvata. Nell'ordine dell'API, che e' quello in cui si disegnano.
  const domande: Record<QualeSezione, { chiave: string; salvata: boolean }[]> = {
    lookalikes: (dati.lookalikes ?? []).map((g) => ({ chiave: String(g.id), salvata: false })),
    filters: (dati.filters ?? []).map((f) => ({ chiave: String(f.id), salvata: false })),
    // una scheda a meta' conta finche' non ha tutte le parti che chiede
    gear: (dati.gear ?? []).map((g) => ({ chiave: g.key, salvata: g.complete })),
    objects: (dati.objects ?? []).map((o) => ({ chiave: o.key, salvata: o.answer !== null })),
    typeless: (dati.typeless ?? []).map((g) => ({ chiave: g.key, salvata: g.answer !== null })),
    unclear: (dati.unclear ?? []).map((p) => ({ chiave: p.key, salvata: p.site !== null })),
    mosaics: (dati.mosaics ?? []).map((m) => ({ chiave: m.key, salvata: m.answer !== null })),
  }
  const tutte = Object.keys(SEZIONI) as QualeSezione[]
  const inManoDi = (s: QualeSezione) => accumulo[s] as Record<string, unknown>
  const senzaRisposta = (s: QualeSezione) => domande[s].filter((d) => !d.salvata && !inManoDi(s)[d.chiave])
  // Oggetti c'e' anche senza domande: gli oggetti a posto si correggono da li'.
  const soloAPosto = domande.objects.length === 0 && dati.settled_objects > 0
  const presenti = tutte.filter((s) => domande[s].length > 0 || (s === "objects" && soloAPosto))
  const aspettano = Object.fromEntries(tutte.map((s) => [s, senzaRisposta(s).length])) as Record<QualeSezione, number>
  // Aperta e' quella scelta; finche' nessuno sceglie, la prima che aspetta una risposta.
  const prima = presenti.flatMap((s) => senzaRisposta(s).map((d) => `${s}:${d.chiave}`))[0] ?? null
  const aperta = scelta ?? prima
  // Fissata al primo disegno: se seguisse "la prima che aspetta", rispondendo salterebbe alla
  // domanda dopo e la sezione si chiuderebbe sotto le mani.
  if (scelta === undefined && prima !== null) setScelta(prima)
  // Una sezione con tutte le risposte si chiude in una riga, al suo posto. Non quella su cui si
  // sta lavorando: si chiuderebbe sotto le mani.
  const chiusa = (s: QualeSezione) =>
    domande[s].length > 0 &&
    aspettano[s] === 0 &&
    !riaperte.includes(s) &&
    !(aperta?.startsWith(`${s}:`) ?? false)
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

  // "Niente" si dice solo se il conto e' zero: lo decide l'API, non le sezioni a schermo.
  const niente = dati.to_confirm === 0 && (
    <Avviso esito="buono" pagina ruolo="status" titolo={t("review.none.title")}>
      {t("review.none.text")}
    </Avviso>
  )
  // Lo stato in cui la pagina sta quasi sempre: niente indice e niente piede, non c'e' da fare.
  if (presenti.length === 0) {
    return (
      <div className="as-conferma">
        <div className="as-conferma__colonna">
          <div className="as-conferma__testa">{conta}</div>
          {esiti}
          {niente}
        </div>
      </div>
    )
  }

  /** La riga di una sezione chiusa: il nome, quante risposte e in che stato, e come si riapre.
   *  Porta l'ancora della sezione, che da chiusa non e' montata: l'indice arriva qui. */
  const chiusaDi = (s: QualeSezione) => {
    // tutte quelle in mano, anche la correzione di un oggetto a posto, che non e' una domanda
    const mie = Object.keys(inManoDi(s)).length
    return (
      <div className="as-carta as-conferma-chiusa" id={SEZIONI[s].ancora} key={s}>
        <h2 className="as-conferma-chiusa__nome">{t(SEZIONI[s].titolo)}</h2>
        <Risposta inMano={mie > 0} salvata={mie === 0}>
          {mie > 0
            ? t("review.closed.inHand", { n: numero(mie) })
            : t("review.closed.saved", { n: numero(domande[s].length) })}
        </Risposta>
        <Bottone
          nome={`${t("review.reopen")}: ${t(SEZIONI[s].titolo)}`}
          piccolo
          verso="nudo"
          onClick={() => setRiaperte((prima) => [...prima, s])}
        >
          {t("review.reopen")}
        </Bottone>
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
                    aria-label={t("review.index.open", { n: numero(aspettano[s]) })}
                  >
                    {numero(aspettano[s])}
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
      {/* senza domande la pagina c'e' solo per gli oggetti a posto: che non c'e' da fare si dice lo stesso */}
      {presenti.every((s) => domande[s].length === 0) && niente}
      {/* **Una coda che non si e' potuta leggere non e' una coda vuota.** Senza questa riga, se
          l'elenco dei modelli cade la tendina diventa un catalogo vuoto: chi cerca il suo filtro
          non lo trova, conclude che in commercio non c'e', e lo scrive a mano per sempre. E' il
          principio portato da `old/`, ed e' la bugia piu' costosa di questa pagina. */}
      {modelli.error && <Avviso esito="allarme">{modelli.error.message}</Avviso>}

      {/* L'ordine delle sezioni e' fisso: prima i pezzi, poi come si montano insieme, poi il
          dove e il quando, poi il cielo. Una sezione che si sposta a seconda di cosa contiene non
          si ritrova. */}
      <DomandaAperta.Provider value={{ aperta, apri: setScelta }}>
      <Fragment key={giro}>
      {chiusa("lookalikes") ? chiusaDi("lookalikes") : !!dati?.lookalikes?.length && (
        <SezioneStessoPezzo
          gruppi={dati.lookalikes}
          risposte={accumulo.lookalikes}
          onRisposta={scrivi("lookalikes")}
        />
      )}
      {chiusa("filters") ? chiusaDi("filters") : !!dati?.filters?.length && (
        <SezioneFiltri
          filtri={dati.filters}
          miei={dati.filter_choices}
          modelli={modelli.data ?? []}
          risposte={accumulo.filters}
          onRisposta={scrivi("filters")}
        />
      )}
      {chiusa("gear") ? chiusaDi("gear") : !!dati?.gear?.length && (
        <SezioneAttrezzatura
          schede={dati.gear}
          corredi={dati.rig_choices}
          ottiche={dati.optics_choices}
          filtri={dati.filter_choices}
          risposte={accumulo.gear}
          onRisposta={scrivi("gear")}
        />
      )}
      {chiusa("objects") ? chiusaDi("objects") : (!!dati?.objects?.length || soloAPosto) && (
        <SezioneOggetti
          schede={dati.objects}
          aPosto={dati.settled_objects}
          risposte={accumulo.objects}
          onRisposta={scrivi("objects")}
        />
      )}
      {chiusa("typeless") ? chiusaDi("typeless") : !!dati?.typeless?.length && (
        <SezioneSenzaTipo
          gruppi={dati.typeless}
          risposte={accumulo.typeless}
          onRisposta={scrivi("typeless")}
        />
      )}
      {chiusa("unclear") ? chiusaDi("unclear") : !!dati?.unclear?.length && (
        <SezioneLuoghi posti={dati.unclear} risposte={accumulo.unclear} onRisposta={scrivi("unclear")} />
      )}
      {chiusa("mosaics") ? chiusaDi("mosaics") : !!dati?.mosaics?.length && (
        <SezioneMosaici
          mosaici={dati.mosaics}
          risposte={accumulo.mosaics}
          onRisposta={scrivi("mosaics")}
        />
      )}
      </Fragment>
      </DomandaAperta.Provider>
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
