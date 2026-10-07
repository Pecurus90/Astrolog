import { keepPreviousData, useInfiniteQuery } from "@tanstack/react-query"
import { useCallback, useRef } from "react"
import { Link, useSearchParams } from "react-router"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import {
  BarraDellArchivio,
  type Criteri,
  ORDINI,
  type Ordine,
  PERIODO_DATE,
  SOLO_MOSAICI,
  type ScelteDellaBarra,
} from "./BarraDellArchivio"
import { CarteDellArchivio } from "./CarteDellArchivio"
import { Altre, paginaDopo } from "./Elenco"
import { ElencoDellArchivio } from "./ElencoDellArchivio"
import { AzioniDelVuoto, Vuoto } from "./Vuoto"
import { api } from "./api/client"
import { t } from "./i18n"

// Quante righe per volta. Alto di proposito: l'Archivio e' un inventario, non un flusso da
// scorrere -- chi ha centomila frame ha comunque una manciata di oggetti, e farglieli chiedere
// venti per volta sarebbe cinque giri per vedere cio' che sta in uno.
const PER_VOLTA = 100

// Le due viste, e quella che si apre per prima (Marco, 22/9/2026: le carte). Il nome sta
// nell'indirizzo, quindi e' anche cio' che si scrive in un collegamento: un elenco condiviso deve
// riaprirsi come elenco.
const VISTE = ["carte", "elenco"] as const
type Vista = (typeof VISTE)[number]
const APERTURA: Vista = "carte"

// Gli identificativi che legano una scheda al suo pannello. Una scheda che dichiara
// `role="tab"` senza un pannello da governare e' una promessa che nessuno mantiene: chi
// ascolta sente "scheda 1 di 2" e poi non trova niente che quella scheda apra.
const SCHEDA: Record<Vista, string> = { carte: "scheda-carte", elenco: "scheda-elenco" }
const PANNELLO: Record<Vista, string> = { carte: "vista-carte", elenco: "vista-elenco" }

// Quelli che **stringono** l'elenco. L'ordine non ci sta: cambiarlo non toglie righe, e uno
// stato vuoto che dicesse "nessun oggetto con questi filtri" per un ordinamento sarebbe assurdo.
const STRINGONO = [
  "q",
  "catalog",
  "constellation",
  "filter",
  "mosaic",
  "period",
  "since",
  "until",
  "site",
  "optics",
  "camera",
] as const

// L'ordine di partenza, e quello a cui si ripiega un `sort` scritto male nell'indirizzo: un
// indirizzo storto non e' un errore da mostrare -- si guarda l'archivio per nome.
const APERTURA_ORDINE: Ordine = "name"

// Cio' con cui la pagina si apre, per i due controlli che un'apertura ce l'hanno: scriverlo
// nell'indirizzo non aggiunge niente, e lo tiene fuori da `cambia`.
const APERTURE: Record<string, string> = { vista: APERTURA, sort: APERTURA_ORDINE }

/**
 * L'Archivio: cosa hai ripreso, con quanti frame, quante ore e con che filtri.
 *
 * - **Qui non si calcola e non si filtra niente.** Righe, conta, ordine e le voci delle tendine
 *   arrivano gia' fatti dal backend. Cercare fra le cento righe gia' scaricate troverebbe solo
 *   quelle, e a chi ha seicento oggetti l'app direbbe "non trovato" mentendo.
 * - **Cio' che stai guardando sta nell'indirizzo**: la vista, la ricerca, i filtri e
 *   l'ordine. Cosi' un archivio filtrato si manda a qualcuno e il tasto indietro torna dov'eri.
 * - **A mani vuote non e' un errore**, e non e' la stessa cosa di "non ho trovato niente": la
 *   prima e' lo stato di chi ha appena installato l'app, la seconda e' una risposta.
 * - **Mentre la risposta arriva resta a schermo cio' che c'era, e la barra lo dice.** Tenerlo
 *   evita di smontare il campo -- e con lui il fuoco, a meta' parola -- ma senza un segno l'utente
 *   vedrebbe cio' che ha chiesto accanto a una risposta vecchia, e la crederebbe la sua.
 *
 * Quando i **Progetti** esisteranno, qui ci finiranno solo quelli conclusi, e la riga sara' il
 * riepilogo di un progetto invece che di un oggetto (`docs/domini/archivio.md`). Cambia **quali**
 * righe arrivano, non come si mostrano: questa pagina non si rifa'.
 */
export function Archivio() {
  const [indirizzo, cambiaIndirizzo] = useSearchParams()
  const chiesta = indirizzo.get("vista")
  const vista: Vista = VISTE.includes(chiesta as Vista) ? (chiesta as Vista) : APERTURA
  const criteri: Criteri = {
    q: indirizzo.get("q") ?? "",
    catalog: indirizzo.get("catalog") ?? "",
    constellation: indirizzo.get("constellation") ?? "",
    filter: indirizzo.get("filter") ?? "",
    // un valore che non e' quello della tendina non stringe: e' un indirizzo scritto male
    mosaic: indirizzo.get("mosaic") === SOLO_MOSAICI ? SOLO_MOSAICI : "",
    period: indirizzo.get("period") ?? "",
    since: inForma(indirizzo.get("since"), DATA),
    until: inForma(indirizzo.get("until"), DATA),
    site: inForma(indirizzo.get("site"), ID),
    optics: inForma(indirizzo.get("optics"), ID),
    camera: inForma(indirizzo.get("camera"), ID),
    sort: ordineChiesto(indirizzo.get("sort")),
  }
  const stringi = STRINGONO.some((c) => criteri[c])

  // Scrivere **sostituisce**: una traccia per ogni parola battuta riempirebbe la cronologia di
  // `m`, `m3`, `m31` e il tasto indietro diventerebbe inutile. Ogni altra scelta -- una tendina,
  // un ordine, la vista -- lascia la sua traccia, o il tasto indietro non tornerebbe al filtro di
  // prima ma uscirebbe dall'Archivio.
  // E **una scelta che non cambia niente non e' un gesto**: ricliccare la scheda che stai gia'
  // guardando, o l'ordine gia' premuto, lascerebbe una tappa identica alla precedente -- tre clic,
  // tre pressioni di indietro che non fanno niente. Perche' il confronto funzioni, cio' che vale
  // **quanto l'apertura** non si scrive: `?vista=carte` dice quello che l'indirizzo nudo dice
  // gia', e senza toglierlo "torna a carte" e "sei gia' su carte" sarebbero due indirizzi diversi.
  const cambia = useCallback(
    (cambio: Record<string, string>) => {
      const netto = Object.fromEntries(
        Object.entries(cambio).map(([nome, valore]) => [
          nome,
          valore === APERTURE[nome] ? "" : valore,
        ]),
      )
      const dopo = conParametri(indirizzo, netto)
      if (dopo.toString() === indirizzo.toString()) return
      cambiaIndirizzo(dopo, { replace: Object.keys(cambio).every((c) => c === "q") })
    },
    [indirizzo, cambiaIndirizzo],
  )

  const elenco = useInfiniteQuery({
    // i criteri stanno nella chiave: sono **un'altra pagina**, non la stessa ricaricata, e senza
    // di loro la cache servirebbe le righe di prima alla ricerca dopo
    queryKey: ["archive", criteri],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) => {
      const { data, error } = await api.GET("/api/v1/archive", {
        params: {
          query: {
            limit: PER_VOLTA,
            offset: pageParam,
            sort: criteri.sort,
            ...(criteri.q && { q: criteri.q }),
            ...(criteri.catalog && { catalog: criteri.catalog }),
            ...(criteri.constellation && { constellation: criteri.constellation }),
            ...(criteri.filter && { filter: criteri.filter }),
            ...(criteri.mosaic && { mosaic: true }),
            ...notti(criteri),
            ...(criteri.site && { site: Number(criteri.site) }),
            ...(criteri.optics && { optics: Number(criteri.optics) }),
            ...(criteri.camera && { camera: Number(criteri.camera) }),
          },
        },
      })
      if (error) throw new Error(t("archive.failed"))
      return data
    },
    getNextPageParam: paginaDopo,
    // Le righe di prima restano a schermo mentre arrivano quelle nuove. Senza, ogni ricerca
    // consegnata smonta la barra -- `data` e' indefinito con una chiave nuova -- e col campo
    // sparisce **il fuoco**: scrivi `m`, il campo si smonta, e `31` finisce da nessuna parte.
    placeholderData: keepPreviousData,
  })
  const prima = elenco.data?.pages[0]
  const righe = elenco.data?.pages.flatMap((p) => p.items) ?? []
  // Le ultime scelte viste restano in mano. Le righe di prima le tiene react-query, ma **non** in
  // errore: li' `data` torna indefinito e la barra sparirebbe proprio quando serve di piu', con un
  // filtro acceso e nessun modo di toglierlo che non sia il tasto indietro.
  const viste = useRef<ScelteDellaBarra | undefined>(undefined)
  if (prima?.choices) viste.current = prima.choices
  const scelte = prima?.choices ?? viste.current

  // Chi ha appena installato l'app: una risposta **assestata** senza righe e senza niente da
  // togliere. `isSuccess` da solo e' vero anche mentre a schermo c'e' la risposta di prima, e
  // allora togliere i filtri dopo una ricerca a vuoto direbbe "non c'e' ancora niente" a chi ha
  // milleduecento oggetti, per tutto il giro di rete.
  const appenaInstallata =
    elenco.isSuccess && !elenco.isPlaceholderData && righe.length === 0 && !stringi

  // La barra c'e' quando sappiamo **cosa offrono le tendine** e c'e' **qualcosa da governare**:
  // dalla prima risposta buona in poi resta in attesa e in errore, e se ne va solo dove non c'e'
  // niente da cercare. Se a cadere e' la **prima** risposta la barra non c'e' ancora: sta in coda,
  // "Un errore alla primissima risposta dell'Archivio lascia un filtro acceso senza il modo di
  // toglierlo".
  //
  // I pannelli hanno una condizione **diversa**: senza una risposta buona non sappiamo se l'elenco
  // e' vuoto, e scrivere "non ho trovato niente" sarebbe la stessa bugia della conta a zero, detta
  // a parole. E l'interruttore sta con loro, o governerebbe il nulla.
  const barra = Boolean(scelte) && !appenaInstallata
  const pannelli = elenco.isSuccess && (righe.length > 0 || stringi)

  return (
    <div className="as-pagina">

      {elenco.isPending && <p>{t("app.loading")}</p>}
      {elenco.error && <Avviso esito="allarme">{elenco.error.message}</Avviso>}

      {/* La barra resta anche quando non c'e' niente da mostrare -- un filtro che non trova
          niente, o una richiesta andata in errore: toglierla lascerebbe senza il modo di disfare
          cio' che si e' chiesto, cioe' bloccati su una pagina vuota col tasto indietro come unica
          strada. Vale per **ogni** controllo, ordine compreso. */}
      {barra && scelte && (
        <BarraDellArchivio
          criteri={criteri}
          scelte={scelte}
          trovati={prima?.found ?? null}
          aspetta={elenco.isPlaceholderData}
          onCriteri={cambia}
        >
          {pannelli && (
            <InterruttoreDiVista vista={vista} onVista={(scelta) => cambia({ vista: scelta })} />
          )}
        </BarraDellArchivio>
      )}

      {appenaInstallata && (
        <Vuoto sotto={1} titolo="archive.empty" perche="archive.empty.why">
          <AzioniDelVuoto>
            <Link to="/impostazioni/cartelle">{t("archive.empty.how")}</Link>
          </AzioniDelVuoto>
        </Vuoto>
      )}

      {pannelli && (
        <>
          {/* Tutti e due i pannelli stanno in pagina, e quello spento porta `hidden`: e' la forma
              che il foglio si aspetta, ed e' l'unica in cui l'`aria-controls` della scheda spenta
              punta a qualcosa che esiste. E ci stanno **anche a elenco vuoto**, con dentro il
              "non ho trovato niente": cosi' l'interruttore non si smonta sotto le dita di chi ci
              ha il fuoco sopra quando l'ultima riga sparisce, e non resta mai una scheda che
              governa un pannello che non c'e'. */}
          <section
            role="tabpanel"
            id={PANNELLO.carte}
            aria-labelledby={SCHEDA.carte}
            hidden={vista !== "carte"}
          >
            {vista === "carte" &&
              (righe.length > 0 ? <CarteDellArchivio righe={righe} /> : <NonTrovato onTogli={cambia} />)}
          </section>
          <section
            role="tabpanel"
            id={PANNELLO.elenco}
            aria-labelledby={SCHEDA.elenco}
            hidden={vista !== "elenco"}
          >
            {vista === "elenco" &&
              (righe.length > 0 ? <ElencoDellArchivio righe={righe} /> : <NonTrovato onTogli={cambia} />)}
          </section>
        </>
      )}

      <Altre elenco={elenco} testo="archive.more" />
    </div>
  )
}

/** "Non ho trovato niente": una **risposta** a cio' che hai chiesto, non lo stato di chi ha
 *  appena installato l'app -- quello ha parole sue e porta alle cartelle. Sta dentro il pannello
 *  della vista e non accanto, cosi' i pannelli ci sono sempre e l'interruttore non si smonta. */
function NonTrovato({ onTogli }: { onTogli: (cambio: Record<string, string>) => void }) {
  return (
    <Vuoto sotto={1} titolo="archive.nothing" perche="archive.nothing.why">
      <AzioniDelVuoto>
        <Bottone onClick={() => onTogli(NIENTE)}>{t("archive.nothing.clear")}</Bottone>
      </AzioniDelVuoto>
    </Vuoto>
  )
}

// Le forme che la rotta accetta. Un valore storto nell'indirizzo, come un ordine inventato, non
// stringe: alla rotta sarebbe un 422, e alla prima risposta la pagina resterebbe senza barra.
const DATA = /^\d{4}-\d{2}-\d{2}$/
const ID = /^\d+$/

function inForma(scritto: string | null, forma: RegExp) {
  return scritto !== null && forma.test(scritto) ? scritto : ""
}

/** Le notti del periodo, le due estreme comprese: un anno va dal primo gennaio al trentuno
 *  dicembre, le date scelte a mano valgono solo sotto `PERIODO_DATE`. Un anno storto
 *  nell'indirizzo non stringe: e' un indirizzo scritto male. */
function notti({ period, since, until }: Criteri) {
  if (/^\d{4}$/.test(period)) return { since: `${period}-01-01`, until: `${period}-12-31` }
  if (period !== PERIODO_DATE) return {}
  return { ...(since && { since }), ...(until && { until }) }
}

/** L'ordine chiesto dall'indirizzo, se e' uno dei tre. Un valore inventato non e' un errore da
 *  mostrare -- un `?sort=pippo` che diventasse un 422 lascerebbe la pagina con un avviso e **senza
 *  barra**, cioe' senza il modo di uscirne: e' un indirizzo scritto male, e la pagina si apre come
 *  si apre sempre. L'elenco di quali esistono lo tiene la barra, che e' dove si scelgono. */
function ordineChiesto(scritto: string | null): Ordine {
  return ORDINI.some((o) => o.chiave === scritto) ? (scritto as Ordine) : APERTURA_ORDINE
}

/** Togliere tutto cio' che stringe, lasciando la vista e l'ordine dove sono: chi si e' perso in
 *  un filtro vuole tornare all'archivio intero, non alla pagina di partenza. **Si deriva**
 *  dall'elenco: scritto a mano sarebbe un secondo posto dove dire quali criteri stringono, e un
 *  quinto aggiunto solo di la' darebbe un bottone "togli i filtri" che non li toglie tutti. */
const NIENTE = Object.fromEntries(STRINGONO.map((c) => [c, ""] as const))

/** L'indirizzo coi parametri cambiati e **tutto il resto com'era**: i controlli della barra sono
 *  cinque piu' la vista, e ognuno che riscrivesse la query intera cancellerebbe gli altri. Un
 *  valore vuoto non resta come parametro vuoto: sparisce, o l'indirizzo si riempirebbe di
 *  `catalog=` che non vogliono dire niente. */
function conParametri(indirizzo: URLSearchParams, cambio: Record<string, string>) {
  const dopo = new URLSearchParams(indirizzo)
  for (const [nome, valore] of Object.entries(cambio)) {
    if (valore) dopo.set(nome, valore)
    else dopo.delete(nome)
  }
  return dopo
}

/** L'interruttore fra le due viste. Sono **schede** (`tab`), non interruttori a due stati: ognuna
 *  governa un pannello, e chi ascolta deve sentire quale delle due sta guardando. */
function InterruttoreDiVista({
  vista,
  onVista,
}: {
  vista: Vista
  onVista: (scelta: Vista) => void
}) {
  return (
    <div className="as-segmentato" role="tablist" aria-label={t("archive.view")}>
      {VISTE.map((voce) => (
        <button
          key={voce}
          type="button"
          className="as-segmentato__voce"
          role="tab"
          id={SCHEDA[voce]}
          aria-controls={PANNELLO[voce]}
          aria-selected={vista === voce}
          onClick={() => onVista(voce)}
        >
          {t(voce === "carte" ? "archive.view.cards" : "archive.view.list")}
        </button>
      ))}
    </div>
  )
}
