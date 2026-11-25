import { useState } from "react"

import { GRUPPI } from "./AttrezzaturaIndice"
import type { Formato } from "./componenti/Tema"
import { ICONE } from "./iconeDeiPezzi"
import { Modulo } from "./componenti/Modulo"
import { NuovoFiltro } from "./ModuloDelFiltro"
import { type Bozza, NuovoPezzo } from "./ModuloDelPezzo"
import { NuovoSetup } from "./NuovoSetup"
import { statoDi, useStato } from "./Scansiona"
import { GENERE } from "./SchedaDelPezzo"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"

type Pagina = components["schemas"]["GearList"]
type Genere = components["schemas"]["InstrumentOnPage"]["kind"]
// oltre agli strumenti, cio' che si scrive a mano dallo stesso gesto: un filtro e un setup
type DaScrivere = Genere | "filter" | "rig"

// [T] Attrezzatura.dc.html `TIPI` (425): the tiles' order; the icons are the groups' (`ICT`)
const TIPI: { kind: DaScrivere; l: Chiave }[] = [
  ...(["optics", "camera", "mount", "reducer", "filter_wheel", "guide_scope", "oag", "guide_camera", "focuser", "spacer"] as const).map(
    (kind) => ({ kind, l: GENERE[kind] }),
  ),
  { kind: "filter", l: "gear.write.kind.filter" },
  { kind: "rig", l: "gear.write.kind.rig" },
]
const icona = (kind: DaScrivere) =>
  ICONE[kind === "rig" ? "setup" : (GRUPPI.find((g) => g.kind === kind)?.icona ?? "setup")]

/**
 * Il gesto *Aggiungi strumento* (tavola v82 `modulo`, k `nuovo`): prima il tipo a tasselli, poi
 * "Tipo: ... Cambia" col modulo del tipo -- uno strumento, un filtro (`NuovoFiltro`) o un setup
 * (`NuovoSetup`).
 *
 * - **Il tipo si sceglie dentro il gesto**, non fuori: un tipo senza strumenti non compare
 *   nell'elenco, quindi un *aggiungi* per gruppo non farebbe mai nascere la prima guida.
 * - **Quali campi chiedere non si decide qui**: li manda l'API per tipo (`cards`), ed e' la
 *   stessa tabella su cui *Da confermare* costruisce le sue domande.
 */
export function AggiungiUnPezzo({
  pagina,
  formato,
  onChiudi: chiudi,
  primo,
}: {
  pagina: Pagina
  formato: Formato
  /** The page opens it from its bar ("Aggiungi strumento") and closes it. */
  onChiudi: () => void
  /** The kind it opens on: a rig's empty part asks for one of its own ("aggiungine uno"). */
  primo?: Genere
}) {
  const [tipo, setTipo] = useState<DaScrivere | null>(primo ?? null)
  const [bozza, setBozza] = useState<Bozza>({ name: "" })
  const scansione = statoDi(useStato().data) === "in corso"
  /** **Cambiando tipo si tiene solo cio' che il tipo nuovo chiede.** I campi che si smontano
   *  resterebbero nella bozza e partirebbero lo stesso -- una montatura nata con l'apertura di un
   *  telescopio, perche' su quei due campi lo schema non ha nessun CHECK che la fermi. Quelli
   *  **comuni** invece restano: sono ancora in pagina con cio' che ci hai scritto. */
  const scegli = (nuovo: DaScrivere) => {
    setTipo(nuovo)
    // filtro e setup hanno un modulo loro: il nome dello strumento non deve restare in mano,
    // invisibile, a partire con Salva al ritorno
    if (nuovo === "filter" || nuovo === "rig") return setBozza({ name: "" })
    const chiesti = new Set<string>(["name", "newBrand", ...(pagina.cards[nuovo] ?? [])])
    setBozza((b) => Object.fromEntries(Object.entries(b).filter(([c]) => chiesti.has(c))))
  }

  if (tipo === null) {
    return (
      <Modulo
        titolo={t("gear.write.add.title")}
        formato={formato}
        tipi={TIPI.map((x) => ({ l: t(x.l), icona: icona(x.kind), on: () => scegli(x.kind) }))}
        salva={{ onSalva: () => {}, occupato: false, spento: true }}
        onAnnulla={chiudi}
      />
    )
  }
  const detto = {
    l: t(TIPI.find((x) => x.kind === tipo)?.l ?? "gear.write.kind"),
    icona: icona(tipo),
    onCambia: () => setTipo(null),
  }
  if (tipo === "filter") {
    return <NuovoFiltro pagina={pagina} formato={formato} scansione={scansione} tipo={detto} onChiudi={chiudi} />
  }
  if (tipo === "rig") {
    return <NuovoSetup pezzi={pagina.instruments} formato={formato} scansione={scansione} tipo={detto} onChiudi={chiudi} />
  }
  return (
    <NuovoPezzo
      kind={tipo}
      pagina={pagina}
      formato={formato}
      scansione={scansione}
      tipo={detto}
      bozza={bozza}
      onBozza={setBozza}
      onChiudi={chiudi}
    />
  )
}
