import { useInfiniteQuery, useQuery } from "@tanstack/react-query"
import { type ReactNode, useState } from "react"
import { useNavigate, useSearchParams } from "react-router"

import { Avviso, type SegnoAvviso } from "./componenti/Avviso"
import { CalendarioNotti, type GiornoNotti } from "./componenti/CalendarioNotti"
import { Carta } from "./componenti/Carta"
import { Filtri, type GruppoFiltri } from "./componenti/Filtri"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { type CartaScheletro, type PilaScheletro, Scheletro } from "./componenti/Scheletro"
import { Striscia, type NotteStriscia } from "./componenti/Striscia"
import { Pagina } from "./componenti/Pagina"
import type { Formato } from "./componenti/Tema"
import { paginaDopo } from "./Elenco"
import { VARIANTE } from "./FiltriUsati"
import { api } from "./api/client"
import { costellazione } from "./costellazioni"
import { type Chiave, maiuscola, meseEAnno, numero, t } from "./i18n"
import { AConfronto, Protagonista, TuttoLArchivio, type VoceFuori } from "./NottiCarte"
import { TuttoDellaNotte } from "./TuttoDellaNotte"
import {
  type Elenco,
  type Mese,
  type Notte,
  cielo,
  esitoDi,
  giornoBreve,
  oreDi,
  parolaDi,
  ripresa,
  sommaDelMese,
  titoloDi,
} from "./NottiDati"

// 20 alla volta (tavola v76, `Carica altre`); la striscia porta le ultime 7.
const PER_VOLTA = 20
const IN_STRISCIA = 7

// Le carte dello scheletro con le misure di quelle vere (tavola v76, `SK`, 288-291).
const SCHELETRO_DESK: (CartaScheletro | PilaScheletro)[] = [
  {
    col: "span 8",
    h: "560px",
    blocchi: [
      { riga: [{ h: "28px", w: "300px" }, t("nights.loading")], tra: true },
      { h: "64px", w: "240px" },
      { griglia: "1.4fr 1fr", gap: "12px", h: "150px", figli: [{ r: "22px" }, { r: "22px" }] },
      { flex: "1" },
    ],
  },
  {
    col: "span 4",
    pila: [
      { h: "380px", pad: "24px", blocchi: [{ h: "100%" }] },
      { flex: "1", pad: "24px", blocchi: [{ h: "100%" }] },
    ],
  },
  {
    col: "span 12",
    h: "520px",
    gap: "10px",
    blocchi: [
      { h: "24px", w: "160px", r: "12px" },
      { flex: "1", r: "18px" },
      { flex: "1", r: "18px" },
      { flex: "1", r: "18px" },
      { flex: "1", r: "18px" },
    ],
  },
]
const SCHELETRO_TEL: CartaScheletro[] = [
  { h: "390px", gap: "12px", blocchi: [t("nights.loading"), { flex: "1" }] },
  { h: "420px", blocchi: [{ h: "100%" }] },
]

// Mentre la lettura mette i frame nelle notti la pagina si rilegge: non al ritmo della scansione,
// perche' ogni pagina di notti chiede la Luna all'effemeride.
export const MENTRE_LEGGE_MS = 15000

type Criterio = Elenco["criteria"][number]
type Scelte = Partial<Record<Criterio["key"], string[]>>

const CIELO: Record<string, Chiave> = {
  go: "ui.outcome.good",
  marginal: "ui.outcome.uncertain",
  nogo: "ui.outcome.unsuitable",
  unknown: "nights.sky.silent",
}

function nomeDellaScelta(chiave: Criterio["key"], o: Criterio["options"][number]): string {
  if (chiave === "constellation") return costellazione(o.value)
  if (chiave === "sky") return CIELO[o.value] ? t(CIELO[o.value] as Chiave) : o.value
  if (chiave === "setup") return o.name ?? ([o.optics, o.camera].filter(Boolean).join(" + ") || o.value)
  if (chiave === "filter" && o.value === "__no_filter__") return t("filters.none")
  return o.name ?? o.value
}

async function chiedi(query: Record<string, unknown>): Promise<Elenco> {
  const { data, error } = await api.GET("/api/v1/nights", { params: { query } })
  if (error) throw new Error(t("nights.failed"))
  return data
}

/**
 * Le **Notti** (tavola v76, `docs/domini/notti.md`): la notte protagonista, le ultime sette, il
 * calendario del mese, i criteri, l'elenco a confronto e tutto l'archivio. Qui non si calcola:
 * esiti, ore di posa, ripresa, conteggi dei criteri e mesi arrivano dal backend.
 */
export function Notti() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const vai = useNavigate()
  const [indirizzo] = useSearchParams()
  const scritto = indirizzo.get("notte")
  const una = scritto !== null && /^[1-9][0-9]*$/.test(scritto) ? Number(scritto) : null
  const storta = scritto !== null && una === null

  const [scelte, setScelte] = useState<Scelte>({})
  const [q, setQ] = useState("")
  const [sel, setSel] = useState<number | null>(null)
  const [mese, setMese] = useState<string | null>(null)
  const [criteriAperti, setCriteriAperti] = useState(false)
  const [calAperto, setCalAperto] = useState(false)
  const [righeAperte, setRigheAperte] = useState(false)
  const [aperta, setAperta] = useState(false)

  const criteri = { ...scelte, ...(q.trim() ? { q: q.trim() } : {}) }
  const lista = useInfiniteQuery({
    queryKey: ["nights", una, criteri],
    enabled: !storta,
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      chiedi({ limit: PER_VOLTA, offset: pageParam, ...(una ? { night: una } : criteri) }),
    getNextPageParam: paginaDopo,
    placeholderData: (prima) => prima,
    refetchInterval: (qq) => (qq.state.data?.pages[0]?.still_reading ? MENTRE_LEGGE_MS : false),
  })
  const striscia = useQuery({
    queryKey: ["nights", "latest"],
    enabled: una === null && !storta,
    queryFn: () => chiedi({ limit: IN_STRISCIA }),
    // come la lista: una notte nata durante la lettura entra anche qui
    refetchInterval: (qq) => (qq.state.data?.still_reading ? MENTRE_LEGGE_MS : false),
  })
  const pagine = lista.data?.pages ?? []
  const prima = pagine[0]
  const righe = pagine.flatMap((p) => p.items)
  const ultime = striscia.data?.items ?? []
  const scelto = sel ?? una ?? ultime[0]?.id ?? righe[0]?.id
  const nota = [...ultime, ...righe].find((n) => n.id === scelto)
  const sola = useQuery({
    queryKey: ["nights", "one", scelto],
    enabled: scelto !== undefined && nota === undefined && !lista.isPending,
    queryFn: () => chiedi({ night: scelto, limit: 1 }),
    // la notte di prima resta a schermo mentre arriva la nuova: il layout non salta
    placeholderData: (prima) => prima,
  })
  const protagonista = nota ?? sola.data?.items[0]
  const solaPersa = nota === undefined && (sola.isError || (sola.isSuccess && !sola.data.items.length))
  const meseVisto = mese ?? protagonista?.night_date.slice(0, 7)
  const calendario = useQuery({
    queryKey: ["nights", "calendar", meseVisto],
    enabled: meseVisto !== undefined && una === null,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/nights/calendar", {
        params: { query: { month: meseVisto ?? "" } },
      })
      if (error) throw new Error(t("nights.failed"))
      return data
    },
  })

  // dal calendario il mese resta quello sfogliato; dalla striscia e dall'elenco segue la notte
  const scegli = (id: number, tieniMese = false) => {
    setSel(id)
    setMese(tieniMese ? (meseVisto ?? null) : null)
  }

  let corpo
  let finestra: ReactNode = null
  if (storta || (una !== null && prima && righe.length === 0)) {
    corpo = (
      <>
        <div className="al-notti__riga-1">
          <TutteLeNotti />
        </div>
        <Avviso tipo="pagina" formato={formato} segno="?" titolo={t("nights.gone")} testo={t("nights.gone.why")} azione={t("nights.gone.how")} onAzione={() => void vai("/notti")} />
      </>
    )
  } else if (lista.isPending) {
    corpo = <Scheletro formato={formato} carte={tel ? SCHELETRO_TEL : SCHELETRO_DESK} testo={t("nights.loading")} />
  } else if (!prima) {
    // solo senza nessuna pagina: un giro di rinnovo o \u00ABCarica altre\u00BB che falliscono tengono i dati
    corpo = (
      <Avviso tipo="pagina" formato={formato} segno="!" titolo={t("nights.failed")} azione={t("nights.retry")} onAzione={() => void lista.refetch()} />
    )
  } else if (prima.empty) {
    corpo = <Vuoto pagina={prima} formato={formato} vai={(a) => void vai(a)} />
  } else {
    // \u2039 \u203A nell'ordine dell'elenco; una notte fuori dalle righe caricate non ha vicine note
    const indice = righe.findIndex((n) => n.id === scelto)
    const solaNotte = una !== null
    const pista = righe
    const prev = indice >= 0 ? righe[indice + 1] : undefined
    const next = indice > 0 ? righe[indice - 1] : undefined
    const attivi = (q.trim() ? 1 : 0) + Object.values(scelte).reduce((a, v) => a + (v?.length ?? 0), 0)
    const togli = () => {
      setScelte({})
      setQ("")
    }
    const gruppi: GruppoFiltri[] = prima.criteria.map((c) => ({
      l: t(`nights.criteria.${c.key}`),
      opz: c.options.map((o) => ({
        l: nomeDellaScelta(c.key, o),
        c: numero(o.nights),
        sel: o.chosen,
        // the dot takes the band's token, the one its bar class paints with
        ...(c.key === "filter" && o.passband && VARIANTE[o.passband] ? { tinta: { fondo: `var(--filtro-${(VARIANTE[o.passband] ?? "").split("--")[1] ?? ""})` } } : {}),
        no: o.nights === 0 && !o.chosen,
        on: () => {
          const ora = new Set(scelte[c.key] ?? [])
          if (ora.has(o.value)) ora.delete(o.value)
          else ora.add(o.value)
          setScelte({ ...scelte, [c.key]: [...ora] })
        },
      })),
    }))
    const stato = righeDiStato(prima)
    const fuori = vociFuori(prima)
    const notteProt = solaPersa ? (
      <Avviso tipo="pagina" formato={formato} segno="?" colonne={8} titolo={t("nights.gone")} testo={t("nights.gone.why")} />
    ) : (
      protagonista && (
      <Protagonista
        notte={protagonista}
        formato={formato}
        sola={solaNotte}
        onPrima={prev ? () => scegli(prev.id) : undefined}
        onDopo={next ? () => scegli(next.id) : undefined}
        onApri={() => setAperta(true)}
      />
      )
    )
    finestra = aperta && protagonista && (
      <TuttoDellaNotte
        id={protagonista.id}
        formato={formato}
        onChiudi={() => setAperta(false)}
        onPrima={prev ? () => scegli(prev.id) : undefined}
        onDopo={next ? () => scegli(next.id) : undefined}
      />
    )
    const cal = calendario.data && (
      <CalendarioDelMese
        mese={calendario.data}
        scelta={scelto}
        formato={formato}
        onScegli={(id) => scegli(id, true)}
        onMese={setMese}
      />
    )
    const corpoFiltri = (
      <Filtri
        gruppi={gruppi}
        campo={t("nights.criteria.field")}
        q={q}
        onCerca={setQ}
        attivi={attivi}
        onTogli={togli}
        formato={formato}
        {...(tel
          ? {
              mostra: prima.total
                ? t("nights.criteria.show", { n: numero(prima.total) })
                : t("nights.criteria.show.none"),
              onMostra: () => setCriteriAperti(false),
              rientro: "0 16px",
            }
          : {})}
      />
    )

    corpo = tel ? (
      <>
        {solaNotte && <TutteLeNotti />}
        {!solaNotte && (
          <div className="al-notti__colonna-12">
            <div className="al-notti__riga-22">
              <a className="al-notti__riga-23" href="#" onClick={gesto(() => { setCalAperto(!calAperto); setCriteriAperti(false); setMese(null) })} aria-expanded={calAperto ? "true" : "false"} aria-label={t("nights.month.phone.label")} style={{ background: calAperto ? "var(--accento)" : "var(--carta-2)", color: calAperto ? "var(--scelta-testo)" : "var(--testo)" }}>
                <span className="al-notti__blocco-10">{meseVisto === undefined ? t("nights.month.phone.label") : calAperto ? maiuscola(meseEAnno(meseVisto)) : t("nights.month.phone", { mese: maiuscola(meseEAnno(meseVisto)) })}</span>
                <span className="al-notti__testo-20" aria-hidden="true">{calAperto ? "\u25B4" : "\u25BE"}</span>
              </a>
              <Filtri parte="bottone" attivi={attivi} aperto={criteriAperti} onApri={() => { setCriteriAperti(!criteriAperti); setCalAperto(false) }} formato="telefono" />
            </div>
            <div role="tablist" aria-label={t("nights.strip")} className="al-scelta al-scelta--segmentato al-scelta--sottili">
              {pista.map((n) => (
                <a key={n.id} href="#" role="tab" aria-selected={n.id === scelto ? "true" : "false"} aria-label={`${titoloDi(n)}, ${oreDi(n.integration_s) ?? t("nights.untimed")}, ${n.site}`} onClick={gesto(() => scegli(n.id))} className="al-scelta__voce">
                  {giornoBreve(n)}
                  <span className="al-notti__testo-21">{oreDi(n.integration_s) ?? t("nights.untimed")}</span>
                </a>
              ))}
            </div>
            <span className="al-notti__riga-24">
              <span>{attivi ? t("nights.list.chosen", { n: numero(prima.total) }) : t("nights.list.recent")}</span>
              {stato.length > 0 && (
                <a className="al-notti__riga-25" href="#" role="button" aria-expanded={righeAperte ? "true" : "false"} onClick={gesto(() => setRigheAperte(!righeAperte))}>
                  <b className="al-notti__testo-22" aria-hidden="true" style={{ color: stato.some((r) => r.s === "!") ? "var(--avviso)" : "var(--testo)" }}>{stato.some((r) => r.s === "!") ? "!" : "?"}</b>
                  {stato.length === 1 ? stato[0]?.t : t("nights.status.many", { n: stato.length })}
                  <span className="al-notti__testo-8" aria-hidden="true">{righeAperte ? "\u25B4" : "\u25BE"}</span>
                </a>
              )}
            </span>
            {righeAperte && <Righe righe={stato} formato="telefono" vai={(a) => void vai(a)} />}
            {(calAperto || criteriAperti || prima.total === 0) && (
              <Carta formato="telefono" etichetta={t("nights.month.criteria")} ritardo={0} padding="16px 0 18px" gap={12}>
                {criteriAperti && corpoFiltri}
                {prima.total === 0 && (
                  <span className="al-notti__colonna-13">
                    <b className="al-notti__testo-23">{t("nights.list.empty")}</b>
                    <span className="al-notti__testo-2">{t("nights.list.empty.phone")}</span>
                  </span>
                )}
                {calAperto && <div className="al-notti__colonna-14">{cal}</div>}
              </Carta>
            )}
          </div>
        )}
        {notteProt}
        {!solaNotte && prima.totals && <TuttoLArchivio tot={prima.totals} fuori={fuori} formato="telefono" />}
      </>
    ) : (
      <>
        {solaNotte && (
          <div className="al-notti__riga-1">
            <TutteLeNotti />
          </div>
        )}
        {!solaNotte && stato.length > 0 && (
          <div className="al-notti__griglia-1">
            <Righe righe={stato} formato="desktop" vai={(a) => void vai(a)} />
          </div>
        )}
        <div className="al-notti__griglia-2">
          {!solaNotte && (
            <Carta formato="desktop" etichetta={t("nights.strip")} colonne={12} ritardo={0} padding="22px 28px 24px" gap={14}>
              <div className="al-notti__riga-2">
                <span className="al-notti__testo-1">{t("nights.strip")}</span>
                <span className="al-notti__testo-2">{t((prima.totals?.nights ?? 0) > IN_STRISCIA ? "nights.strip.latest" : "nights.strip.recent")}</span>
              </div>
              <Striscia notti={ultime.map((n, i) => inStriscia(n, ultime[i - 1], n.id === scelto, () => scegli(n.id)))} etichetta={t("nights.strip")} formato="desktop" />
            </Carta>
          )}
          {notteProt}
          {!solaNotte && (
            <div className="al-notti__colonna-4">
              <Carta formato="desktop" etichetta={t("nights.calendar")} ritardo={60} padding="24px" gap={14}>
                {cal}
              </Carta>
            </div>
          )}
          {!solaNotte && (
            <Carta formato="desktop" etichetta={t("nights.criteria.label")} colonne={criteriAperti ? 3 : 12} ritardo={160} padding="22px 20px" gap={14}>
              <div className="al-notti__riga-12">
                <span className="al-notti__riga-13">
                  <span className="al-notti__testo-1">{t("nights.criteria")}</span>
                  <span className="al-notti__testo-2">
                    {attivi
                      ? `${t("nights.criteria.on", { n: attivi })} \u00B7 ${t("nights.month.nights", { n: numero(prima.total) })}`
                      : t("nights.criteria.none")}
                  </span>
                </span>
                <span className="al-notti__riga-14">
                  <Filtri parte="togli" attivi={attivi} onTogli={togli} formato="desktop" />
                  <a href="#" onClick={gesto(() => setCriteriAperti(!criteriAperti))} aria-expanded={criteriAperti ? "true" : "false"} className="al-bottone al-bottone--tenue al-bottone--piccolo al-bottone--blocco al-bottone--a-sinistra">
                    {t(criteriAperti ? "nights.criteria.close" : "nights.criteria.open")}
                    <span className="al-notti__testo-8" aria-hidden="true">{criteriAperti ? "\u25B4" : "\u25BE"}</span>
                  </a>
                </span>
              </div>
              {criteriAperti && corpoFiltri}
            </Carta>
          )}
          {!solaNotte && (
            <AConfronto
              notti={righe}
              mesi={prima.months}
              colonne={criteriAperti ? 9 : 12}
              sotto={attivi ? t("nights.list.chosen", { n: numero(prima.total) }) : t("nights.list.sub")}
              conta={t("nights.shown", { n: numero(righe.length), di: numero(prima.total) })}
              scelta={scelto}
              onScegli={scegli}
              altre={
                lista.hasNextPage || lista.isFetchNextPageError
                  ? {
                      testo: t(lista.isFetchingNextPage ? "nights.more.busy" : lista.isFetchNextPageError ? "nights.retry" : "nights.more"),
                      spento: lista.isFetchingNextPage,
                      occupato: lista.isFetchingNextPage,
                      errore: lista.isFetchNextPageError,
                      onAltre: () => void lista.fetchNextPage(),
                    }
                  : null
              }
            />
          )}
          {!solaNotte && prima.totals && <TuttoLArchivio tot={prima.totals} fuori={fuori} formato="desktop" />}
        </div>
      </>
    )
  }

  return (
    <div className="as-pagina">
      <Pagina formato={formato}>{corpo}</Pagina>
      {finestra}
    </div>
  )
}


function TutteLeNotti() {
  const vai = useNavigate()
  return (
    <a href="/notti" onClick={gesto(() => void vai("/notti"))} className="al-bottone al-bottone--tenue al-bottone--rovescio al-bottone--blocco al-bottone--a-sinistra">
      {t("nights.all")}
    </a>
  )
}

function inStriscia(n: Notte, prima: Notte | undefined, scelta: boolean, on: () => void): NotteStriscia {
  const c = cielo(n)
  const nuovoMese = !prima || prima.night_date.slice(0, 7) !== n.night_date.slice(0, 7)
  const nomeMese = nuovoMese ? (meseEAnno(n.night_date.slice(0, 7)).split(" ")[0] ?? "") : ""
  const r = ripresa(n)
  return {
    day: giornoBreve(n),
    tag: nomeMese,
    tagS: nomeMese,
    sel: scelta,
    esito: c.esito === -1 ? "mancante" : c.esito,
    pillT: c.striscia,
    ...(r ? { rip: r } : {}),
    hours: oreDi(n.integration_s) ?? t("nights.untimed"),
    range: n.site,
    on,
  }
}

function CalendarioDelMese({
  mese,
  scelta,
  formato,
  onScegli,
  onMese,
}: {
  mese: Mese
  scelta: number | undefined
  formato: Formato
  onScegli: (id: number) => void
  onMese: (m: string) => void
}) {
  const [anno, numMese] = mese.month.split("-").map(Number) as [number, number]
  const nome = meseEAnno(mese.month).split(" ")[0] ?? ""
  const giorni: GiornoNotti[] = mese.days.map((g) => {
    const prima = g.nights[0]
    return {
      d: g.day,
      esiti: g.nights.map((n) => esitoDi(n.verdict)),
      esito: esitoDi(g.verdict),
      sel: g.nights.some((n) => n.id === scelta),
      ...(prima ? { on: () => onScegli(prima.id) } : {}),
      aria: t("nights.day.label", { giorno: `${g.day} ${nome}`, quante: t("nights.day.nights", { n: g.nights.length }), notti: g.nights.map((n) => `${n.site} ${parolaDi(esitoDi(n.verdict))}`).join(", ") }),
    }
  })
  const sposta = (passi: number) => {
    const d = new Date(Date.UTC(anno, numMese - 1 + passi, 1))
    onMese(d.toISOString().slice(0, 7))
  }
  const conta = mese.nights
    ? `${t("nights.month.nights", { n: numero(mese.nights) })} \u00B7 ${t("nights.month.good", { n: numero(mese.good) })}`
    : t("nights.month.none")
  return (
    <CalendarioNotti
      anno={anno}
      mese={numMese - 1}
      giorni={giorni}
      {...(mese.tonight.startsWith(mese.month) ? { oggi: Number(mese.tonight.slice(8, 10)) } : {})}
      sub={sommaDelMese(mese.nights, mese.integration_s)}
      {...(formato === "desktop"
        ? {
            numero: oreDi(mese.integration_s) ?? t("nights.month.noHours"),
            numeroL: t("nights.month.at", { mese: nome }),
            conta,
          }
        : {})}
      onPrima={() => sposta(-1)}
      onDopo={() => sposta(1)}
      primaNo={!mese.first_month || mese.month <= mese.first_month}
      dopoNo={mese.month >= mese.last_month}
      formato={formato}
    />
  )
}

interface RigaDiStato {
  s: SegnoAvviso
  t: string
  a?: { testo: string; dove: string }
}

/** Le righe in cima, una per motivo: il sito, le risposte, la data, la lettura. */
function righeDiStato(p: Elenco): RigaDiStato[] {
  const quanti = (dove: string) => p.waiting.find((w) => w.answer_at === dove)?.frames ?? 0
  const righe: RigaDiStato[] = []
  if (quanti("site")) righe.push({ s: "!", t: t("nights.waiting.site", { n: numero(quanti("site")) }), a: { testo: t("nights.waiting.site.how"), dove: "/impostazioni/sito" } })
  if (quanti("review")) righe.push({ s: "!", t: t("nights.waiting.review", { n: numero(quanti("review")) }), a: { testo: t("nights.waiting.review.how"), dove: "/da-confermare" } })
  if (quanti("date")) righe.push({ s: "?", t: t("nights.waiting.date", { n: numero(quanti("date")) }) })
  if (p.still_reading) righe.push({ s: "?", t: t("nights.reading", { pct: p.reading_done_pct ?? 0 }) })
  return righe
}

function vociFuori(p: Elenco): VoceFuori[] {
  const quanti = (dove: string) => p.waiting.find((w) => w.answer_at === dove)?.frames ?? 0
  const voci: VoceFuori[] = [
    { chiave: "review", n: quanti("review"), a: "/da-confermare" },
    { chiave: "site", n: quanti("site"), a: "/impostazioni/sito" },
    // la sezione dei frame senza data nasce col porting di Da confermare
    { chiave: "date", n: quanti("date"), a: null },
  ]
  return voci.filter((v) => v.n > 0)
}

function Righe({ righe, formato, vai }: { righe: RigaDiStato[]; formato: Formato; vai: (a: string) => void }) {
  return (
    <>
      {righe.map((r) => (
        <Avviso key={r.t} tipo="riga" formato={formato} segno={r.s} titolo={r.t} {...(r.a ? { azione: r.a.testo, onAzione: () => vai(r.a?.dove ?? "/") } : {})} />
      ))}
    </>
  )
}

const VUOTI: Record<NonNullable<Elenco["empty"]>, { titolo: Chiave; testo: Chiave; azione?: Chiave; dove?: string }> = {
  no_folders: { titolo: "nights.empty.noFolders", testo: "nights.empty.noFolders.why", azione: "nights.empty.noFolders.how", dove: "/impostazioni/cartelle" },
  no_frames: { titolo: "nights.empty.noFrames", testo: "nights.empty.noFrames.why", azione: "nights.empty.noFrames.how", dove: "/impostazioni/cartelle" },
  no_site: { titolo: "nights.empty.noSite", testo: "nights.empty.noSite.why", azione: "nights.empty.noSite.how", dove: "/impostazioni/sito" },
  reading: { titolo: "nights.empty.reading", testo: "nights.empty.reading.why" },
  waiting: { titolo: "nights.empty.waiting", testo: "nights.empty.waiting.why", azione: "nights.empty.waiting.how", dove: "/da-confermare" },
}

function Vuoto({ pagina, formato, vai }: { pagina: Elenco; formato: Formato; vai: (a: string) => void }) {
  const v = VUOTI[pagina.empty ?? "no_frames"]
  const ferme = pagina.waiting.reduce((a, w) => a + w.frames, 0)
  return (
    <Avviso
      tipo="pagina"
      formato={formato}
      segno="?"
      titolo={t(v.titolo, { pct: pagina.reading_done_pct ?? 0 })}
      testo={t(v.testo, { n: numero(ferme) })}
      {...(v.azione && v.dove ? { azione: t(v.azione), onAzione: () => vai(v.dove ?? "/") } : {})}
    />
  )
}
