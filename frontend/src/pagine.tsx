import type { ReactElement } from "react"

import { Archivio } from "./Archivio"
import { Attrezzatura } from "./Attrezzatura"
import { Confermare } from "./Confermare"
import { Home } from "./Home"
import type { IconName } from "./Icons"
import { Meteo } from "./Meteo"
import { Notti } from "./Notti"
import { Impostazioni, SEZIONI } from "./Impostazioni"
import type { Chiave } from "./i18n"

/**
 * Le pagine dell'app in un posto solo: il binario le legge da qui, e le rotte pure. Due elenchi
 * che possono divergere sono il modo in cui una voce porta a una pagina che non c'e'.
 *
 * - **L'ordine e' quello del telaio** (`docs/domini/navigazione.md`, disegno v26): si legge
 *   dall'alto come si lavora, e lo stacco divide cio' che hai da cio' che pianifichi.
 * - **Ogni voce si vede, anche senza pagina** (Marco, 7/10/2026): una voce senza `elemento` apre
 *   la pagina "in arrivo", che lo dice, invece di sparire.
 */

/** Una sezione dentro una pagina: ha il suo indirizzo, come una pagina. Senza elemento non
 *  esiste: non e' una rotta e la navigazione a sezioni non la mostra. */
export type Sezione = {
  a: string
  chiave: Chiave
  elemento?: ReactElement
}

export type Pagina = {
  a: string
  chiave: Chiave
  icona: IconName
  /** In fondo al binario, staccata dalle altre. */
  coda?: boolean
  /** Fra le cinque schede del telefono; le altre stanno nel foglio "Altro". */
  telefono?: boolean
  /** Lo stacco prima di questa voce. */
  staccata?: boolean
  /** Il nome va su due righe nel binario, al primo spazio: "Carta / del cielo". */
  dueRighe?: boolean
  /** Manca finche' la pagina non esiste: la voce apre "in arrivo". */
  elemento?: ReactElement
  /** Le sezioni che hanno un indirizzo loro. La **prima aperta** e' anche cio' che si vede
   *  aprendo l'indirizzo della pagina. */
  sezioni?: readonly Sezione[]
}

export const PAGINE: readonly Pagina[] = [
  { a: "/", chiave: "nav.home", icona: "casa", telefono: true, elemento: <Home /> },
  { a: "/notti", chiave: "nav.nights", icona: "luna", telefono: true, elemento: <Notti /> },
  { a: "/archivio", chiave: "nav.archive", icona: "griglia", telefono: true, elemento: <Archivio /> },
  { a: "/progetti", chiave: "nav.projects", icona: "bersaglio", telefono: true },
  { a: "/statistiche", chiave: "nav.stats", icona: "barre" },
  { a: "/attrezzatura", chiave: "nav.gear", icona: "tubo", elemento: <Attrezzatura /> },
  { a: "/planner", chiave: "nav.planner", icona: "calendario", staccata: true },
  { a: "/carta-del-cielo", chiave: "nav.sky", icona: "stella", dueRighe: true },
  { a: "/meteo", chiave: "nav.weather", icona: "nuvola", elemento: <Meteo /> },
  {
    a: "/da-confermare",
    chiave: "nav.review",
    icona: "domanda",
    coda: true,
    dueRighe: true,
    elemento: <Confermare />,
  },
  // Impostazioni e' una pagina con dentro le sue sezioni, ognuna col suo indirizzo
  // (`/impostazioni/cartelle`); nel binario sta una voce sola.
  {
    a: "/impostazioni",
    chiave: "nav.settings",
    icona: "cursori",
    coda: true,
    elemento: <Impostazioni />,
    sezioni: SEZIONI,
  },
]

/** Le sezioni di una pagina che esistono davvero, nell'ordine del contratto. */
export function sezioniAperte(sezioni: readonly Sezione[] | undefined): readonly Sezione[] {
  return (sezioni ?? []).filter((s) => s.elemento !== undefined)
}

/** La pagina a cui appartiene un indirizzo, **sezioni comprese**: la chiedono le rotte, il
 *  titolo in alto e la voce accesa, e scritta tre volte divergerebbe. */
export function paginaDi(indirizzo: string): Pagina | undefined {
  return PAGINE.find(
    (p) => p.a === indirizzo || sezioniAperte(p.sezioni).some((s) => s.a === indirizzo),
  )
}
