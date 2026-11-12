import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Fragment, type ReactNode, useEffect, useMemo, useState } from "react"
import { useLocation, useNavigate, useSearchParams } from "react-router"

import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Pagina } from "./componenti/Pagina"
import { Scheletro } from "./componenti/Scheletro"
import type { Formato } from "./componenti/Tema"
import {
  CartaDelConto,
  CasoAccanto,
  Esito,
  FormatoConf,
  Guscio,
  Indice,
  MISURE,
  Piede,
  SCHELETRO,
  SezioneChiusa,
  type StatoRisposta,
  TipiDiDomanda,
  spenta,
  statoDi,
} from "./ConfermareGuscio"
import { DomandaAperta, UnCaso } from "./Domanda"
import { SezioneStessoPezzo } from "./SezioneStessoPezzo"
import { SezioneAttrezzatura } from "./SezioneAttrezzatura"
import { SezioneFiltri } from "./SezioneFiltri"
import { SezioneLuoghi } from "./SezioneLuoghi"
import { SezioneMosaici } from "./SezioneMosaici"
import { SezioneOggetti } from "./SezioneOggetti"
import { SezioneSenzaData } from "./SezioneSenzaData"
import { SezioneSenzaTipo } from "./SezioneSenzaTipo"
import { api } from "./api/client"
import { motivo } from "./api/motivo"
import { useRevisione } from "./api/revisione"
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
  undated: Record<string, Schema["UndatedEdit"]>
  mosaics: Record<string, Schema["MosaicEdit"]>
}
const VUOTO: Accumulo = {
  lookalikes: {},
  filters: {},
  gear: {},
  objects: {},
  typeless: {},
  unclear: {},
  undated: {},
  mosaics: {},
}

// `?sezione=` coi nomi dei collegamenti delle altre pagine (tavola v82, `componentDidMount`)
const PER_NOME: Record<string, QualeSezione> = { siti: "unclear", "senza-data": "undated" }
const TUTTE = Object.keys(SEZIONI) as QualeSezione[]

/** La sezione chiesta dall'indirizzo: l'ancora nell'hash, o `?sezione=`. */
function sezioneChiesta(hash: string, chiesta: string | null): QualeSezione | null {
  const perAncora = (a: string) => TUTTE.find((s) => SEZIONI[s].ancora === a)
  if (hash) return perAncora(hash.slice(1)) ?? null
  if (!chiesta) return null
  return PER_NOME[chiesta] ?? perAncora(chiesta) ?? null
}

/**
 * Da confermare: le domande che l'app ha su cio' che ha letto, e le risposte (tavola v82).
 *
 * Tre regole che valgono per tutta la pagina (Marco, 14/9/2026):
 *
 * - **le risposte si accumulano** e partono con un solo *Applica*: una sola attesa e un solo
 *   ricalcolo, invece di uno per risposta;
 * - le **sezioni vuote si nascondono**, col conto in cima: una pagina di undici titoli vuoti
 *   sembra rotta, e il giorno che hai finito vuoi vederlo;
 * - dopo *Applica* **si ricarica dicendo cosa e' cambiato**, coi numeri della ricevuta: l'elenco
 *   di prima direbbe cose non piu' vere, perche' la risposta rifa' il lavoro sui frame toccati.
 *
 * *Applica* scrive solo le risposte: una domanda guardata e lasciata li' resta aperta (ADR 0014).
 */
export function Confermare() {
  const formato = useFormato()
  return (
    <Pagina formato={formato}>
      <FormatoConf.Provider value={formato}>
        <LaPagina formato={formato} />
      </FormatoConf.Provider>
    </Pagina>
  )
}

function LaPagina({ formato }: { formato: Formato }) {
  const tel = formato === "telefono"
  const m = MISURE[formato]
  const vaiA = useNavigate()
  // Rispondi of the frame lands on its section: the router does not follow a hash
  const { hash } = useLocation()
  const [indirizzo] = useSearchParams()
  const chiesta = sezioneChiesta(hash, indirizzo.get("sezione"))
  // Sul telefono: il tipo scelto (`null` = l'elenco dei tipi), il caso, e cio' che si apre fuori dal caso.
  const [tipo, setTipo] = useState<QualeSezione | null>(chiesta)
  const [caso, setCaso] = useState(0)
  const [fuoriCaso, setFuoriCaso] = useState<string | undefined>(undefined)
  const [accumulo, setAccumulo] = useState<Accumulo>(VUOTO)
  // Quante volte la pagina e' stata applicata e riletta: le sezioni si rimontano da capo, o
  // quelle che tengono un modulo in mano mostrerebbero ancora cio' che era scritto prima.
  const [giro, setGiro] = useState(0)
  // La domanda aperta, una in tutta la pagina: `undefined` finche' non si sceglie, e allora e'
  // la prima senza risposta. E le sezioni finite che l'utente ha riaperto.
  const [scelta, setScelta] = useState<string | undefined>(undefined)
  const [riaperte, setRiaperte] = useState<readonly QualeSezione[]>(chiesta ? [chiesta] : [])
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
      (fatti[sezione] ??= (
        chiave: string | number,
        risposta: Accumulo[S][keyof Accumulo[S]] | null,
      ) =>
        setAccumulo((prima) => {
          const voce: Record<string | number, unknown> = { ...prima[sezione] }
          if (risposta) voce[chiave] = risposta
          else delete voce[chiave]
          return { ...prima, [sezione]: voce }
        })) as (chiave: string | number, risposta: Accumulo[S][keyof Accumulo[S]] | null) => void
  }, [])

  const pagina = useRevisione()
  const pronta = pagina.isSuccess
  const meta = hash ? hash.slice(1) : chiesta ? SEZIONI[chiesta].ancora : null
  useEffect(() => {
    if (pronta && meta) document.getElementById(meta)?.scrollIntoView?.({ block: "start" })
  }, [pronta, meta])
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
          undated: Object.values(accumulo.undated),
          mosaics: Object.values(accumulo.mosaics),
          objects: Object.values(accumulo.objects),
        },
      })
      if (error) {
        // il titolo dice gia' "non applicate": un rifiuto senza nome non aggiunge testo
        const perche = motivo(error, RIFIUTI, "review.apply.failed")
        throw new Error(perche === "review.apply.failed" ? "" : t(perche))
      }
      return data
    },
    onSuccess: async () => {
      // Le risposte mandate non restano in mano: la pagina si rilegge, e cio' che si vede e' cio'
      // che il database dice adesso. Si svuota **dopo** la rilettura: prima, le sezioni rimontate
      // ripartirebbero dalla pagina vecchia.
      await cache.invalidateQueries({ queryKey: ["review"] })
      setAccumulo(VUOTO)
      setScelta(undefined)
      setFuoriCaso(undefined)
      setRiaperte([])
      setGiro((g) => g + 1)
    },
  })

  if (pagina.isPending) {
    return (
      <Guscio m={m}>
        <Scheletro
          carte={SCHELETRO[formato]}
          griglia={tel ? "minmax(0,1fr)" : MISURE.desktop.colonne}
          gap={m.stacco}
          testo={t("review.loading")}
          formato={formato}
        />
      </Guscio>
    )
  }
  if (pagina.error) {
    return (
      <Guscio m={m}>
        <Avviso
          tipo="pagina"
          formato={formato}
          segno="!"
          titolo={t("review.failed")}
          azione={t("action.retry")}
          onAzione={() => void pagina.refetch()}
        />
      </Guscio>
    )
  }

  const dati = pagina.data
  const inMano = Object.values(accumulo).reduce((quante, r) => quante + Object.keys(r).length, 0)
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
    undated: (dati.undated ?? []).map((g) => ({ chiave: g.key, salvata: g.answer !== null })),
    mosaics: (dati.mosaics ?? []).map((x) => ({ chiave: x.key, salvata: x.answer !== null })),
  }
  const inManoDi = (s: QualeSezione) => accumulo[s] as Record<string, unknown>
  const senzaRisposta = (s: QualeSezione) =>
    domande[s].filter((d) => !d.salvata && !inManoDi(s)[d.chiave])
  // Oggetti c'e' anche senza domande: gli oggetti a posto si correggono da li'.
  const soloAPosto = domande.objects.length === 0 && dati.settled_objects > 0
  const presenti = TUTTE.filter((s) => domande[s].length > 0 || (s === "objects" && soloAPosto))
  // Quante domande di ogni sezione aspettano ancora: senza risposta salvata e senza una in mano.
  // Dipende da cio' che l'utente ha appena scelto, quindi si conta qui e non nell'API.
  const aspettano = Object.fromEntries(TUTTE.map((s) => [s, senzaRisposta(s).length])) as Record<
    QualeSezione,
    number
  >
  // Il conto vivo: cio' che aspetta qui, piu' le sezioni che la pagina non disegna ancora (dall'API).
  const nonDisegnate = (dati.sections ?? [])
    .filter((x) => domande[x.key].length === 0)
    .reduce((a, x) => a + x.count, 0)
  const conto = TUTTE.reduce((a, s) => a + aspettano[s], 0) + nonDisegnate
  const primaDi = (s: QualeSezione) => {
    const d = senzaRisposta(s)[0] ?? domande[s][0]
    return d ? `${s}:${d.chiave}` : null
  }
  // Aperta e' quella scelta; finche' nessuno sceglie, la prima che aspetta (o quella dell'indirizzo).
  const prima = presenti.flatMap((s) => senzaRisposta(s).map((d) => `${s}:${d.chiave}`))[0] ?? null
  const partenza =
    (giro === 0 && chiesta && presenti.includes(chiesta) ? primaDi(chiesta) : null) ?? prima
  const aperta = scelta ?? partenza
  // Fissata al primo disegno: se seguisse "la prima che aspetta", rispondendo salterebbe alla
  // domanda dopo e la sezione si chiuderebbe sotto le mani.
  if (scelta === undefined && partenza !== null) setScelta(partenza)
  // Una sezione con tutte le risposte si chiude in una riga, al suo posto. Non quella su cui si
  // sta lavorando: si chiuderebbe sotto le mani.
  const chiusa = (s: QualeSezione) =>
    domande[s].length > 0 &&
    aspettano[s] === 0 &&
    !riaperte.includes(s) &&
    !(aperta?.startsWith(`${s}:`) ?? false)
  const statoDelle = (s: QualeSezione): StatoRisposta[] =>
    domande[s].map((d) => statoDi(d.salvata, Boolean(inManoDi(s)[d.chiave])))

  // L'esito sta fuori dai rami: l'Applica che risponde alle ultime domande svuota la pagina.
  const fatto = applica.data
  const esiti = (
    <>
      {fatto && !esitoChiuso && (
        <Esito
          segno={"✓" /* glifo-ok: segno della tavola */}
          m={m}
          titolo={
            fatto.requeued > 0
              ? t("review.applied", { n: numero(fatto.changed), frame: numero(fatto.requeued) })
              : t("review.applied.only", { n: numero(fatto.changed) })
          }
          testo={[
            fatto.none_filter_existed ? t("review.applied.noneFilter") : "",
            // senza frame da rifare il lavoro non parte, e non c'e' niente in coda
            fatto.requeued > 0 && !fatto.run_started ? t("review.applied.queued") : "",
          ]
            .filter(Boolean)
            .join(" ")}
          onChiudi={() => setEsitoChiuso(true)}
        />
      )}
      {applica.error && (
        <Esito segno="!" m={m} titolo={t("review.apply.failed")} testo={applica.error.message} />
      )}
    </>
  )

  // "Niente" si dice solo se il conto dell'API e' zero, non per le sezioni a schermo.
  const niente = dati.to_confirm === 0 && (
    <Avviso
      tipo="pagina"
      formato={formato}
      segno={"✓" /* glifo-ok: segno della tavola */}
      titolo={t("review.none.title")}
      testo={t("review.none.text")}
    />
  )
  // Primo avvio: non c'e' niente da chiedere perche' non c'e' ancora niente. Senza conto e senza piede.
  // Solo senza domande: risposte ripristinate su un archivio nuovo ne portano anche a zero frame.
  if (dati.empty && presenti.length === 0) {
    return (
      <Guscio m={m}>
        <Avviso
          tipo="pagina"
          formato={formato}
          segno="?"
          titolo={t("review.empty.title")}
          testo={t("review.empty.text")}
          azione={t("review.empty.how")}
          onAzione={() => void vaiA("/impostazioni/cartelle")}
        />
      </Guscio>
    )
  }
  // Lo stato in cui la pagina sta quasi sempre: niente conto, indice e piede, non c'e' da fare.
  if (presenti.length === 0 && dati.to_confirm === 0) {
    return (
      <Guscio m={m}>
        {esiti}
        {niente}
      </Guscio>
    )
  }

  // Unire due strumenti non si annulla: se fra le risposte in mano ce n'e' una, si dice qui.
  const unisce = Object.values(accumulo.lookalikes).some((r) => r.same)
  const ferma = applica.isPending

  // Le sezioni, scritte una volta: la pagina larga le mette in fila, il telefono una alla volta.
  const sezioni: Record<QualeSezione, ReactNode> = {
    lookalikes: (
      <SezioneStessoPezzo
        gruppi={dati.lookalikes}
        risposte={accumulo.lookalikes}
        onRisposta={scrivi("lookalikes")}
      />
    ),
    filters: (
      <SezioneFiltri
        filtri={dati.filters}
        miei={dati.filter_choices}
        modelli={modelli.data ?? []}
        // **Una coda che non si e' potuta leggere non e' una coda vuota**: la domanda lo dice
        senzaModelli={modelli.isError}
        risposte={accumulo.filters}
        onRisposta={scrivi("filters")}
      />
    ),
    gear: (
      <SezioneAttrezzatura
        schede={dati.gear}
        corredi={dati.rig_choices}
        ottiche={dati.optics_choices}
        filtri={dati.filter_choices}
        risposte={accumulo.gear}
        onRisposta={scrivi("gear")}
      />
    ),
    objects: (
      <SezioneOggetti
        schede={dati.objects}
        aPosto={dati.settled_objects}
        risposte={accumulo.objects}
        onRisposta={scrivi("objects")}
      />
    ),
    typeless: (
      <SezioneSenzaTipo
        gruppi={dati.typeless}
        risposte={accumulo.typeless}
        onRisposta={scrivi("typeless")}
      />
    ),
    unclear: (
      <SezioneLuoghi
        posti={dati.unclear}
        risposte={accumulo.unclear}
        onRisposta={scrivi("unclear")}
      />
    ),
    undated: (
      <SezioneSenzaData
        gruppi={dati.undated}
        risposte={accumulo.undated}
        onRisposta={scrivi("undated")}
      />
    ),
    mosaics: (
      <SezioneMosaici
        mosaici={dati.mosaics}
        risposte={accumulo.mosaics}
        onRisposta={scrivi("mosaics")}
      />
    ),
  }
  // Il piede resta in vista e dice **cosa si sta per mandare**: il conto e' dello stato in mano.
  const piede = presenti.length > 0 && (
    <Piede
      inMano={inMano}
      unisce={unisce}
      ferma={ferma}
      formato={formato}
      onApplica={() => {
        setEsitoChiuso(false)
        applica.mutate()
      }}
    />
  )
  const avvisi = (
    <>
      {esiti}
      {/* senza domande la pagina c'e' solo per gli oggetti a posto: che non c'e' da fare si dice lo stesso */}
      {presenti.every((s) => domande[s].length === 0) && niente}
    </>
  )
  const tacche = presenti.flatMap(statoDelle)
  const vado = (s: QualeSezione | null, k = 0) => {
    setTipo(s)
    setCaso(k)
    setFuoriCaso(undefined)
  }
  // Dopo un Applica il tipo scelto puo' non esserci piu': si torna ai tipi.
  const qui = tel && tipo !== null && presenti.includes(tipo) ? tipo : null
  const cartaConto = (
    <CartaDelConto conto={conto} tacche={tacche} regola={conto > 0 && qui === null} m={m} />
  )

  if (tel) {
    if (qui === null) {
      // Quante risposte di un tipo stanno in ognuno dei quattro stati, nell'ordine in cui si leggono.
      const stati = (s: QualeSezione) => {
        // in mano anche cio' che non e' una domanda: la correzione di un oggetto a posto
        const fuori = Object.keys(inManoDi(s)).filter(
          (c) => !domande[s].some((d) => d.chiave === c),
        ).length
        const tutti = statoDelle(s)
        return (["dare", "ora", "salvata", "cambiata"] as const)
          .map((stato) => ({
            stato,
            n: tutti.filter((x) => x === stato).length + (stato === "ora" ? fuori : 0),
          }))
          .filter((v) => v.n > 0)
      }
      return (
        <Guscio m={m} sinistra={cartaConto}>
          {avvisi}
          {presenti.length > 0 && (
            <TipiDiDomanda
              voci={presenti.map((s) => ({ sezione: s, stati: stati(s) }))}
              ferma={ferma}
              m={m}
              // un tipo si apre sulla prima domanda che aspetta (tavola `vaiSez`, 167-169)
              onTipo={(s) => {
                const d = senzaRisposta(s)[0]
                vado(s, d ? domande[s].indexOf(d) : 0)
              }}
            />
          )}
          {piede}
        </Guscio>
      )
    }
    const casi = domande[qui]
    const k = Math.min(caso, Math.max(0, casi.length - 1))
    const idCaso = casi[k] ? `${qui}:${casi[k].chiave}` : null
    return (
      <Guscio m={m} sinistra={cartaConto}>
        {avvisi}
        {/* [T] Da confermare.dc.html 42: dove si e', sopra la colonna delle sezioni */}
        <div className="al-conf__riga-8">
          <a
            href="#"
            role="button"
            onClick={gesto(() => vado(null))}
            className="al-bottone al-bottone--testo al-bottone--a-filo"
          >
            {t("review.phone.all")}
          </a>
          {casi.length > 0 && (
            <span className="al-conf__blocco-6">
              {t("review.phone.case", { k: numero(k + 1), n: numero(casi.length) })}
            </span>
          )}
        </div>
        <div
          className="al-conf__colonna-11"
          aria-disabled={ferma ? "true" : undefined}
          inert={ferma}
          style={{ gap: m.stacco, ...spenta(ferma) }}
        >
          {/* Aperto e' il caso; gli oggetti identificati, senza casi, si aprono fuori dal caso. */}
          <DomandaAperta.Provider value={{ aperta: fuoriCaso ?? idCaso, apri: setFuoriCaso }}>
            <UnCaso.Provider value={k}>
              <Fragment key={`${giro}:${qui}:${k}`}>{sezioni[qui]}</Fragment>
            </UnCaso.Provider>
          </DomandaAperta.Provider>
        </div>
        {/* [T] Da confermare.dc.html 85: come si va avanti, sotto la colonna */}
        {casi.length > 0 && <CasoAccanto k={k} n={casi.length} onVai={(j) => vado(qui, j)} />}
        {piede}
      </Guscio>
    )
  }

  /** Dall'indice: apre la sezione (anche se chiusa) sulla prima che aspetta, e ci scorre. */
  const vaiSez = (s: QualeSezione) => {
    const id = primaDi(s)
    if (id) setScelta(id)
    setRiaperte((prima) => (prima.includes(s) ? prima : [...prima, s]))
    window.setTimeout(
      () =>
        document
          .getElementById(SEZIONI[s].ancora)
          ?.scrollIntoView?.({ block: "start", behavior: "smooth" }),
      60,
    )
  }
  const sinistra = (
    <>
      {cartaConto}
      {presenti.length > 0 && (
        <Indice
          voci={presenti.map((s) => ({
            sezione: s,
            aspettano: aspettano[s],
            corrente: aperta?.startsWith(`${s}:`) ?? false,
          }))}
          ferma={ferma}
          m={m}
          onVai={vaiSez}
        />
      )}
    </>
  )
  return (
    <Guscio m={m} sinistra={sinistra}>
      {avvisi}
      {/* L'ordine delle sezioni e' fisso: prima i pezzi, poi come si montano insieme, poi il
          dove e il quando, poi il cielo. Una sezione che si sposta non si ritrova. */}
      <div
        className="al-conf__colonna-11"
        aria-disabled={ferma ? "true" : undefined}
        inert={ferma}
        style={{ gap: m.stacco, ...spenta(ferma) }}
      >
        <DomandaAperta.Provider value={{ aperta, apri: setScelta }}>
          <Fragment key={giro}>
            {presenti.map((s) =>
              chiusa(s) ? (
                <SezioneChiusa
                  key={s}
                  sezione={s}
                  // tutte quelle in mano, anche la correzione di un oggetto a posto
                  inMano={Object.keys(inManoDi(s)).length}
                  salvate={domande[s].length}
                  m={m}
                  onRiapri={() => setRiaperte((prima) => [...prima, s])}
                />
              ) : (
                <Fragment key={s}>{sezioni[s]}</Fragment>
              ),
            )}
          </Fragment>
        </DomandaAperta.Provider>
      </div>
      {piede}
    </Guscio>
  )
}

/** I rifiuti che l'*Applica* puo' ricevere, detti per nome.
 *
 * Non e' una cortesia: `POST /review/apply` e' **una transazione sola**, quindi uno qualunque di
 * questi annulla anche le risposte buone. Un "non ha funzionato" generico lascerebbe l'utente
 * senza sapere ne' cosa e' stato scritto ne' cosa riparare -- e le riparazioni sono diverse:
 * si cambia bersaglio, si ricarica la pagina, si aspetta. */
const RIFIUTI: Record<string, Chiave> = {
  unknown_target: "review.apply.unknownTarget",
  not_found: "review.apply.notFound",
  worker_busy: "review.apply.busy",
  name_taken: "review.apply.nameTaken",
  merge_refused: "review.apply.mergeRefused",
  model_contradicts_bands: "review.apply.contradictsBands",
}
