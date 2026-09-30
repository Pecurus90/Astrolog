import { useState } from "react"

import { Bottone } from "./Bottone"
import { Campo } from "./Campo"
import { Modulo, NomeDelPezzo, con, useScrittura } from "./ModuloDelGesto"
import { NuovoCorredo, NuovoFiltro } from "./NuovoFiltroOCorredo"
import { CampoDellaScheda, GENERE } from "./SchedaDelPezzo"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"

type Pezzo = components["schemas"]["InstrumentOnPage"]
type Schede = components["schemas"]["GearList"]["cards"]
type Scritta = components["schemas"]["InstrumentCorrection"]
type Genere = Pezzo["kind"]
// oltre agli strumenti, cio' che si scrive a mano dallo stesso gesto: un filtro e un corredo
type DaScrivere = Genere | "filter" | "rig"
const ALTRI: Record<"filter" | "rig", Chiave> = {
  filter: "gear.write.kind.filter",
  rig: "gear.write.kind.rig",
}

/**
 * Il gesto *Aggiungi un pezzo*: uno strumento che i file non nominano, e -- dallo stesso gesto -- un
 * filtro o un corredo (`NuovoFiltroOCorredo`). I mattoni del modulo stanno in `ModuloDelGesto`.
 *
 * - **Il genere si sceglie dentro il gesto**, non fuori: un genere senza pezzi non compare
 *   nell'elenco, quindi un *aggiungi* per gruppo non farebbe mai nascere la prima guida.
 * - **Quali campi chiedere non si decide qui**: li manda l'API per genere (`cards`), ed e' la
 *   stessa tabella su cui *Da confermare* costruisce le sue domande.
 */

/** Scrivere un pezzo che i tuoi file non nominano: una guida, un riduttore, una montatura. Sta in
 *  cima alla pagina e non accanto a un pezzo, perche' **a mani vuote** non c'e' nessun pezzo
 *  accanto a cui metterlo -- ed e' proprio chi non ha ancora scansionato ad averne piu' bisogno. */
export function AggiungiUnPezzo({ schede, pezzi }: { schede: Schede; pezzi: Pezzo[] }) {
  const [aperto, setAperto] = useState(false)
  const [genere, setGenere] = useState<DaScrivere>("optics")
  const [nome, setNome] = useState("")
  const [scritta, setScritta] = useState<Scritta>({})
  const chiudi = () => {
    setAperto(false)
    setScritta({})
    setNome("")
  }
  /** **Cambiando genere si tiene solo cio' che il genere nuovo chiede.** I campi che si
   *  smontano resterebbero nella scritta e partirebbero lo stesso -- una montatura nata con
   *  l'apertura di un telescopio, perche' su quei due campi lo schema non ha nessun CHECK che la
   *  fermi. Quelli **comuni** invece restano: sono ancora in pagina con cio' che ci hai scritto,
   *  e buttarli via vorrebbe dire una casella che dice una cosa e un'app che ne manda un'altra. */
  const cambiaGenere = (nuovo: DaScrivere) => {
    setGenere(nuovo)
    // filtro e corredo hanno un modulo loro, e tornando il nome dello strumento rinasce vuoto:
    // quello scritto prima non deve restare in mano, invisibile, a partire con Salva
    if (nuovo === "filter" || nuovo === "rig") setNome("")
    const chiesti = new Set<string>(nuovo === "filter" || nuovo === "rig" ? [] : (schede[nuovo] ?? []))
    setScritta(
      (s) => Object.fromEntries(Object.entries(s).filter(([c]) => chiesti.has(c))) as Scritta,
    )
  }
  const scrivi = useScrittura(async () => {
    if (genere === "filter" || genere === "rig") throw new Error(`${genere} ha il suo modulo`)
    const { error } = await api.POST("/api/v1/gear/instruments", {
      body: { ...scritta, kind: genere, name: nome },
    })
    if (error) throw error
  }, chiudi)
  const scelta = (
    <Campo id="aggiungi-kind" etichetta={t("gear.write.kind")}>
      <select
        className="as-scelta"
        id="aggiungi-kind"
        value={genere}
        onChange={(e) => cambiaGenere(e.target.value as DaScrivere)}
      >
        {Object.entries({ ...GENERE, ...ALTRI }).map(([valore, parola]) => (
          <option key={valore} value={valore}>
            {t(parola)}
          </option>
        ))}
      </select>
    </Campo>
  )

  if (!aperto) {
    return (
      <div className="as-pagina__azioni">
        <Bottone onClick={() => setAperto(true)}>{t("gear.write.add")}</Bottone>
      </div>
    )
  }
  if (genere === "filter") return <NuovoFiltro scelta={scelta} onChiudi={chiudi} />
  if (genere === "rig") return <NuovoCorredo scelta={scelta} pezzi={pezzi} onChiudi={chiudi} />
  return (
    <Modulo
      base="aggiungi"
      titolo={t("gear.write.add.title")}
      onManda={() => scrivi.mutate()}
      onAnnulla={chiudi}
      salvando={scrivi.isPending}
      valido={nome.trim() !== ""}
      errore={scrivi.error}
    >
      {scelta}
      <NomeDelPezzo id="aggiungi-name" onNome={(n) => setNome(n ?? "")} />
      {(schede[genere] ?? []).map((campo) => (
        <CampoDellaScheda
          key={campo}
          id={`aggiungi-${campo}`}
          campo={campo}
          valore={scritta[campo]}
          onValore={(v) => setScritta((s) => con(s, campo, v))}
        />
      ))}
    </Modulo>
  )
}
