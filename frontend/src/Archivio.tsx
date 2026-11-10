import { keepPreviousData, useInfiniteQuery } from "@tanstack/react-query"
import { type ReactNode, useCallback, useEffect, useRef, useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router"

import {
  CRITERI,
  type ChiaveCriterio,
  type Criterio,
  type Elenco,
  ORDINI,
  PUNTO,
  type Ordine,
  mostra,
  nomeCriterio,
  nomeVoce,
  parolaOrdine,
  sintesi,
  testa,
} from "./ArchivioDati"
import { CarteArchivio, ElencoArchivio } from "./ArchivioRighe"
import { Avviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import { Filtri, type GruppoFiltri } from "./componenti/Filtri"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Pagina } from "./componenti/Pagina"
import { type CartaScheletro, Scheletro } from "./componenti/Scheletro"
import { paginaDopo } from "./Elenco"
import { tintaDi } from "./MisureDati"
import { TuttoDellOggetto } from "./TuttoDellOggetto"
import { api } from "./api/client"
import { numero, t } from "./i18n"

// Venti alla volta (tavola, "Mostra altri 20").
const PER_VOLTA = 20

const VISTE = ["carte", "elenco"] as const
type Vista = (typeof VISTE)[number]
// Le icone delle due viste (tavola, `visT`).
const ICONA: Record<Vista, string> = {
  carte: "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z",
  elenco: "M4 6h16M4 12h16M4 18h16",
}

// Lo scheletro della tavola (`SK`): la testa, poi le carte.
const scheletro = (tel: boolean): CartaScheletro[] => [
  { col: "1 / -1", h: "150px", pad: "24px", gap: "14px", blocchi: [t("archive.loading"), { flex: "1", w: "40%" }] },
  ...Array.from({ length: tel ? 4 : 10 }, () => ({ h: tel ? "300px" : "320px", pad: "12px", blocchi: [{ h: "100%", r: "20px" }] })),
]

// La ricerca parte quando chi scrive si ferma: una parola e' una domanda, non una per lettera.
const ATTESA_MS = 250
// Le forme che la rotta accetta; un valore storto nell'indirizzo non stringe.
const CHIAVE = /^.{1,200}$/s
const ID = /^\d+$/
const PER_ID: ReadonlySet<ChiaveCriterio> = new Set(["site", "optics", "camera"])

type Scelte = Record<ChiaveCriterio, string[]>

function scelteDa(indirizzo: URLSearchParams): Scelte {
  return Object.fromEntries(
    CRITERI.map((k) => [k, indirizzo.getAll(k).filter((v) => (PER_ID.has(k) ? ID.test(v) : v !== ""))]),
  ) as Scelte
}

async function chiedi(query: Record<string, unknown>): Promise<Elenco> {
  const { data, error } = await api.GET("/api/v1/archive", { params: { query } })
  if (error) throw new Error(t("archive.failed"))
  return data
}

/**
 * L'**Archivio** (tavola v78, `docs/domini/archivio.md`): cosa hai ripreso, a carte o in elenco,
 * con la testa di tutto l'archivio, la ricerca e i nove criteri. Qui non si calcola: righe,
 * conte di ogni voce, ordine, totali e frame senza oggetto arrivano dal backend. Cio' che stai
 * guardando sta nell'indirizzo: un archivio ristretto si manda a qualcuno, e il tasto indietro
 * torna alla scelta di prima.
 */
export function Archivio() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const vai = useNavigate()
  const [indirizzo, cambiaIndirizzo] = useSearchParams()
  const [aperta, setAperta] = useState<string | null>(null)
  const [criteriAperti, setCriteriAperti] = useState(false)

  const vista: Vista = indirizzo.get("vista") === "elenco" ? "elenco" : "carte"
  const scritto = indirizzo.get("sort")
  const ordine: Ordine = ORDINI.includes(scritto as Ordine) ? (scritto as Ordine) : "name"
  const q = indirizzo.get("q") ?? ""
  const chiaveScritta = indirizzo.get("key")
  const chiave = chiaveScritta !== null && CHIAVE.test(chiaveScritta) ? chiaveScritta : ""
  const scelte = scelteDa(indirizzo)
  const attivi = (q.trim() ? 1 : 0) + CRITERI.reduce((a, k) => a + scelte[k].length, 0)

  // Una scelta lascia la sua traccia; scrivere sostituisce, o il tasto indietro disfarebbe lettere.
  const cambia = useCallback(
    (fai: (p: URLSearchParams) => void, sostituisci = false) => {
      const dopo = new URLSearchParams(indirizzo)
      fai(dopo)
      if (dopo.toString() !== indirizzo.toString()) cambiaIndirizzo(dopo, { replace: sostituisci })
    },
    [indirizzo, cambiaIndirizzo],
  )
  const [scrive, setScrive] = useState(q)
  const ultimo = useRef(q)
  useEffect(() => {
    if (q !== ultimo.current) setScrive(q)
    ultimo.current = q
  }, [q])
  useEffect(() => {
    if (scrive === q) return
    const via = setTimeout(() => cambia((p) => (scrive.trim() ? p.set("q", scrive) : p.delete("q")), true), ATTESA_MS)
    return () => clearTimeout(via)
  }, [scrive, q, cambia])

  const query = {
    sort: ordine,
    ...(chiave ? { key: chiave } : q.trim() ? { q: q.trim() } : {}),
    ...Object.fromEntries(CRITERI.filter((k) => scelte[k].length).map((k) => [k, scelte[k]])),
  }
  const elenco = useInfiniteQuery({
    queryKey: ["archive", query],
    initialPageParam: 0,
    queryFn: ({ pageParam }) => chiedi({ limit: PER_VOLTA, offset: pageParam, ...query }),
    getNextPageParam: paginaDopo,
    // le righe di prima restano mentre arrivano le nuove: il campo non si smonta a meta' parola
    placeholderData: keepPreviousData,
  })
  // Dalla prima risposta in poi la testa e i criteri restano in mano: se la rete cade dopo una
  // scelta, il modo di toglierla resta a schermo (archivio.md).
  const visto = useRef<Elenco | undefined>(undefined)
  if (elenco.data?.pages[0]) visto.current = elenco.data.pages[0]
  const prima = elenco.data?.pages[0] ?? visto.current
  const caduto = elenco.isError && prima !== undefined
  const righe = elenco.data?.pages.flatMap((p) => p.items) ?? []

  const qui = aperta === null ? -1 : righe.findIndex((r) => r.key === aperta)
  const vicina = (d: number) => {
    const r = qui < 0 ? undefined : righe[qui + d]
    return r ? () => setAperta(r.key) : undefined
  }
  const finestra = aperta !== null && (
    <TuttoDellOggetto
      key={aperta}
      chiave={aperta}
      nome={righe[qui]?.name ?? aperta}
      formato={formato}
      onChiudi={() => setAperta(null)}
      onPrima={vicina(-1)}
      onDopo={vicina(1)}
    />
  )

  let corpo: ReactNode
  if (elenco.isPending && !prima) {
    corpo = <Scheletro formato={formato} carte={scheletro(tel)} testo={t("archive.loading")} griglia={tel ? "repeat(2,minmax(0,1fr))" : "repeat(5,minmax(0,1fr))"} gap={tel ? "10px" : "16px"} />
  } else if (!prima) {
    corpo = <Avviso tipo="pagina" formato={formato} segno="!" titolo={t("archive.failed")} azione={t("archive.retry")} onAzione={() => void elenco.refetch()} />
  } else if (prima.whole.rows === 0 && !prima.unresolved) {
    corpo = <Avviso tipo="pagina" formato={formato} segno="?" titolo={t("archive.empty")} testo={t("archive.empty.why")} azione={t("archive.empty.how")} onAzione={() => void vai("/impostazioni/cartelle")} />
  } else {
    const togli = () => {
      setScrive("")
      cambia((p) => {
        for (const k of [...CRITERI, "q"]) p.delete(k)
      })
    }
    const gruppi: GruppoFiltri[] = prima.criteria.map((c: Criterio) => ({
      l: nomeCriterio(c.key),
      opz: c.options.map((o) => ({
        l: nomeVoce(c.key, o),
        c: numero(o.rows),
        sel: o.chosen,
        no: o.rows === 0 && !o.chosen,
        ...(c.key === "filter" ? { tinta: tintaDi(o.passband ?? undefined) } : {}),
        on: () =>
          cambia((p) => {
            const ora = p.getAll(c.key)
            p.delete(c.key)
            const dopo = ora.includes(o.value) ? ora.filter((v) => v !== o.value) : [...ora, o.value]
            for (const v of dopo) p.append(c.key, v)
          }),
      })),
    }))
    const intero = testa(prima.whole)
    // la carta dei frame senza oggetto sta in testa anche coi criteri (tavola 172), non sulla riga
    // aperta dalla Ricerca; l'avviso di nessun oggetto guarda le righe sole
    const fuori = prima.unresolved && !chiave ? prima.unresolved : null
    const nessuno = righe.length === 0
    const ordineVista = (
      <OrdineEVista
        ordine={ordine}
        vista={vista}
        onOrdine={(o) => cambia((p) => (o === "name" ? p.delete("sort") : p.set("sort", o)))}
        onVista={(v) => cambia((p) => (v === "carte" ? p.delete("vista") : p.set("vista", v)))}
      />
    )
    corpo = (
      <div className="al-arch__colonna-1 al-arch__pagina">
        <Carta formato={formato} etichetta={t("archive.head")} colonne={12} ritardo={0} padding={tel ? "20px" : "28px"} gap={16}>
          {tel ? (
            <div className="al-arch__colonna-2">
              <span className="al-arch__blocco-4">
                <b className="al-arch__testo-1">{intero.n} {intero.parola}</b>{PUNTO}{intero.sotto}
              </span>
              <div className="al-arch__riga-fine">{ordineVista}</div>
            </div>
          ) : (
            <div className="al-arch__colonna-3">
              <div className="al-arch__riga-3">
                <span className="al-arch__riga-4">
                  <span className="al-arch__testo-2">{intero.n}</span>
                  <span className="al-arch__colonna-4">
                    <span className="al-arch__testo-3">{intero.parola}</span>
                    <span className="al-arch__testo-4">{intero.sotto}</span>
                  </span>
                </span>
                <span className="al-arch__riga-5">{ordineVista}</span>
              </div>
            </div>
          )}
          {chiave ? (
            // sulle righe di prima direbbe ristretto a un oggetto non chiesto: si aspetta la risposta
            !elenco.isPlaceholderData && (
              <div className="al-arch__riga-6">
                <Link to="/archivio" className="al-bottone al-bottone--tenue al-bottone--rovescio">
                  {t("archive.all")}
                </Link>
                <span className="al-arch__testo-5">{t("archive.only", { nome: righe[0]?.name ?? chiave })}</span>
              </div>
            )
          ) : (
            <div className="al-arch__riga-6">
              <input value={scrive} onChange={(e) => setScrive(e.target.value)} aria-label={t("archive.search")} placeholder={t("archive.search.placeholder")} className="al-campo al-campo--tondo al-campo--piccolo al-arch__blocco-5" aria-busy={elenco.isPlaceholderData ? "true" : "false"} />
              <Filtri parte="bottone" attivi={attivi} aperto={criteriAperti} onApri={() => setCriteriAperti(!criteriAperti)} altezza={tel ? "44px" : "40px"} formato={formato} />
              {!tel && <Filtri parte="togli" attivi={attivi} onTogli={togli} altezza="40px" formato="desktop" />}
              <span className="al-arch__testo-5" aria-live="polite">{sintesi(prima, righe.length, attivi, ordine)}</span>
            </div>
          )}
          {criteriAperti && !chiave && (
            <Filtri gruppi={gruppi} colonne={5} attivi={attivi} onTogli={togli} mostra={mostra(prima.total)} onMostra={() => setCriteriAperti(false)} formato={formato} />
          )}
        </Carta>

        {prima.unresolved?.solver_missing && (
          <Avviso tipo="riga" formato={formato} segno="!" titolo={t("archive.solver.missing", { n: numero(prima.unresolved.frames) })} azione={t("archive.solver.open")} onAzione={() => void vai("/impostazioni/riconoscitore")} />
        )}

        {caduto && (
          <Avviso tipo="riga" formato={formato} segno="!" titolo={t("archive.failed")} azione={t("archive.retry")} onAzione={() => void elenco.refetch()} />
        )}

        {nessuno && !caduto && (
          <div className="al-arch__blocco-6">
            <Avviso tipo="blocco" formato={formato} segno="?" titolo={chiave ? t("archive.gone") : t("archive.nothing")} testo={chiave ? t("archive.gone.why") : t("archive.nothing.why")} />
          </div>
        )}

        {(!nessuno || fuori) &&
          (vista === "carte" ? (
            <CarteArchivio righe={righe} fuori={fuori} formato={formato} onApri={setAperta} />
          ) : (
            <ElencoArchivio righe={righe} fuori={fuori} formato={formato} onApri={setAperta} />
          ))}

        {elenco.hasNextPage && (
          <div className="al-arch__riga-9">
            <a href="#" onClick={gesto(() => void elenco.fetchNextPage())} className="al-bottone al-bottone--tenue al-bottone--rovescio al-bottone--blocco al-bottone--a-sinistra" aria-busy={elenco.isFetchingNextPage ? "true" : "false"}>
              {t("archive.more", { n: numero(Math.min(PER_VOLTA, prima.total - righe.length)) })}
            </a>
            <span className="al-arch__testo-4">{t("archive.loaded", { n: numero(righe.length), tot: numero(prima.total) })}</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <>
      {finestra}
      <Pagina formato={formato}>{corpo}</Pagina>
    </>
  )
}

/** Ordine in tendina e vista a due icone (tavola v56.11, 29 e 35), desktop e telefono. */
function OrdineEVista({
  ordine,
  vista,
  onOrdine,
  onVista,
}: {
  ordine: Ordine
  vista: Vista
  onOrdine: (o: Ordine) => void
  onVista: (v: Vista) => void
}) {
  return (
    <div role="group" aria-label={t("archive.order.view")} className="al-arch__ordine-vista">
      <select value={ordine} onChange={(e) => onOrdine(e.target.value as Ordine)} aria-label={t("archive.order")} className="al-tendina al-tendina--tondo al-arch__ordine">
        {ORDINI.map((o) => (
          <option key={o} value={o}>
            {parolaOrdine(o)}
          </option>
        ))}
      </select>
      <div role="radiogroup" aria-label={t("archive.view")} className="al-arch__viste">
        {VISTE.map((v) => {
          const parola = t(v === "carte" ? "archive.view.cards" : "archive.view.list")
          return (
            <button key={v} type="button" role="radio" aria-checked={vista === v} aria-label={parola} title={parola} onClick={() => onVista(v)} className="al-arch__vista">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d={ICONA[v]} />
              </svg>
              <span className="al-arch__vista-parola" aria-hidden="true">
                {parola}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

