import { useQuery } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { Link } from "react-router"

import { Avviso } from "./Avviso"
import { AggiungiUnPezzo } from "./GestiDelPezzo"
import { UnCorredo, UnFiltro, UnPezzo } from "./RigheDellAttrezzatura"
import { AzioniDelVuoto, Vuoto } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"

type Pezzo = components["schemas"]["InstrumentOnPage"]
type Pagina = components["schemas"]["GearList"]

// Come si chiama ogni genere **al plurale**: qui si intitola un gruppo, non un pezzo (quello lo
// fa `GENERE`). **Un `Record` e non un elenco**: i generi li decide lo schema, e il tipo generato
// dall'OpenAPI li porta tutti -- cosi' il giorno che ne nasce uno questo file non compila, invece
// di far sparire quei pezzi dalla pagina in silenzio.
const TITOLO: Record<Pezzo["kind"], Chiave> = {
  optics: "gear.kind.optics",
  camera: "gear.kind.camera",
  mount: "gear.kind.mount",
  reducer: "gear.kind.reducer",
  filter_wheel: "gear.kind.filter_wheel",
  guide_scope: "gear.kind.guide_scope",
  guide_camera: "gear.kind.guide_camera",
  focuser: "gear.kind.focuser",
}

// L'ordine in cui si guardano: prima cio' che fa la foto, poi cio' che la tiene ferma, poi il
// contorno. Chi non e' nominato qui non sparisce -- va in fondo.
const ORDINE: readonly Pezzo["kind"][] = [
  "optics",
  "camera",
  "mount",
  "reducer",
  "filter_wheel",
  "guide_scope",
  "guide_camera",
  "focuser",
]

function generiDi(pezzi: Pezzo[]): Pezzo["kind"][] {
  const dentro = [...new Set(pezzi.map((p) => p.kind))]
  const posto = (k: Pezzo["kind"]) => (ORDINE.indexOf(k) + 1 || ORDINE.length + 1) - 1
  return dentro.sort((a, b) => posto(a) - posto(b))
}

/**
 * L'**Attrezzatura**: con cosa hai ripreso, e quanto -- e i gesti per correggerla.
 *
 * - **Un genere senza pezzi non si mostra affatto**: otto titoli vuoti sarebbero un elenco di
 *   cose che non hai. E un genere **nuovo** non puo' sparire: i titoli stanno in un `Record` sul
 *   tipo generato dall'API, quindi se lo schema ne aggiunge uno questo file smette di compilare.
 * - **Scrivere un pezzo sta in cima**, fuori dai gruppi: a mani vuote non c'e' nessun gruppo, ed
 *   e' proprio li' che serve.
 * - **Niente paginazione**: l'attrezzatura di chiunque sta in una schermata.
 */
export function Attrezzatura() {
  const elenco = useQuery({
    queryKey: ["gear"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/gear")
      if (error) throw new Error(t("gear.failed"))
      return data
    },
  })
  const pagina = elenco.data
  const vuota =
    pagina &&
    pagina.instruments.length === 0 &&
    pagina.rigs.length === 0 &&
    pagina.filters.length === 0

  return (
    <div className="as-pagina">

      {elenco.isPending && <p>{t("app.loading")}</p>}
      {elenco.error && <Avviso esito="allarme">{elenco.error.message}</Avviso>}

      {pagina && <AggiungiUnPezzo schede={pagina.cards} pezzi={pagina.instruments} />}

      {vuota && (
        <Vuoto sotto={1} titolo="gear.empty" perche="gear.empty.why">
          <AzioniDelVuoto>
            <Link to="/impostazioni">{t("gear.empty.how")}</Link>
          </AzioniDelVuoto>
        </Vuoto>
      )}

      {pagina && <Posseduto pagina={pagina} />}
    </div>
  )
}

function Posseduto({ pagina }: { pagina: Pagina }) {
  return (
    <>
      {generiDi(pagina.instruments).map((genere) => (
        <Gruppo
          key={genere}
          titolo={TITOLO[genere]}
          quanti={pagina.instruments.filter((p) => p.kind === genere).length}
        >
          {pagina.instruments
            .filter((p) => p.kind === genere)
            .map((p) => (
              <li key={p.id}>
                <UnPezzo pezzo={p} campi={pagina.cards[genere] ?? []} tutti={pagina.instruments} />
              </li>
            ))}
        </Gruppo>
      ))}
      <Gruppo titolo="gear.rigs" quanti={pagina.rigs.length}>
        {pagina.rigs.map((r) => (
          <li key={r.id}>
            <UnCorredo corredo={r} montature={pagina.instruments.filter((p) => p.kind === "mount")} />
          </li>
        ))}
      </Gruppo>
      <Gruppo titolo="gear.filters" quanti={pagina.filters.length}>
        {pagina.filters.map((f) => (
          <li key={f.id}>
            <UnFiltro filtro={f} tutti={pagina.filters} />
          </li>
        ))}
      </Gruppo>
    </>
  )
}

/** Un gruppo di pezzi col suo titolo. **Vuoto non si disegna**: un titolo senza righe sarebbe
 *  l'elenco di cio' che non possiedi. */
function Gruppo({
  titolo,
  quanti,
  children,
}: {
  titolo: Chiave
  quanti: number
  children: ReactNode
}) {
  if (quanti === 0) return null
  return (
    <>
      <h2>{t(titolo)}</h2>
      <ul aria-label={t(titolo)}>{children}</ul>
    </>
  )
}
