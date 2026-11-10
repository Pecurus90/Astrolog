import type { ReactElement } from "react"

import { Archivio } from "./Archivio"
import { Attrezzatura } from "./Attrezzatura"
import { Confermare } from "./Confermare"
import { Dashboard } from "./Dashboard"
import { Meteo } from "./Meteo"
import { Notti } from "./Notti"
import { Impostazioni, SEZIONI } from "./Impostazioni"
import type { Chiave } from "./i18n"

/**
 * Le pagine dell'app in un posto solo: il telaio le legge da qui, e le rotte pure. Due elenchi
 * che possono divergere sono il modo in cui una voce porta a una pagina che non c'e'.
 *
 * - **L'ordine e' quello del telaio v76** (`docs/domini/navigazione.md`): le pillole, poi il menu
 *   Altro, poi le due che hanno un posto loro (Da confermare e l'ingranaggio).
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

/** Dove sta la voce sul desktop: fra le pillole, nel menu Altro, o in un posto suo (la pillola
 *  Da confermare, l'ingranaggio). */
export type Posto = "pillole" | "altro" | "suo"

export type Pagina = {
  a: string
  chiave: Chiave
  posto: Posto
  /** Fra le schede della bolla del telefono; le altre stanno nel menu Altro. */
  telefono?: boolean
  /** La riga sotto il nome nel menu Altro del desktop. */
  sotto?: Chiave
  /** Manca finche' la pagina non esiste: la voce apre "in arrivo". */
  elemento?: ReactElement
  /** Le sezioni che hanno un indirizzo loro. La **prima aperta** e' anche cio' che si vede
   *  aprendo l'indirizzo della pagina. */
  sezioni?: readonly Sezione[]
}

export const PAGINE: readonly Pagina[] = [
  { a: "/", chiave: "nav.home", posto: "pillole", telefono: true, elemento: <Dashboard /> },
  { a: "/notti", chiave: "nav.nights", posto: "pillole", telefono: true, elemento: <Notti /> },
  { a: "/archivio", chiave: "nav.archive", posto: "pillole", telefono: true, elemento: <Archivio /> },
  { a: "/progetti", chiave: "nav.projects", posto: "pillole" },
  { a: "/statistiche", chiave: "nav.stats", posto: "pillole" },
  { a: "/meteo", chiave: "nav.weather", posto: "pillole", telefono: true, elemento: <Meteo /> },
  { a: "/piano-della-notte", chiave: "nav.plan", posto: "altro", sotto: "nav.plan.sub" },
  { a: "/planner", chiave: "nav.planner", posto: "altro", sotto: "nav.planner.sub" },
  { a: "/selezione-dei-frame", chiave: "nav.selection", posto: "altro", sotto: "nav.selection.sub" },
  {
    a: "/attrezzatura",
    chiave: "nav.gear",
    posto: "altro",
    sotto: "nav.gear.sub",
    elemento: <Attrezzatura />,
  },
  { a: "/da-confermare", chiave: "nav.review", posto: "suo", elemento: <Confermare /> },
  // Impostazioni e' una pagina con dentro le sue sezioni, ognuna col suo indirizzo
  // (`/impostazioni/cartelle`); sul desktop la apre l'ingranaggio.
  { a: "/impostazioni", chiave: "nav.settings", posto: "suo", elemento: <Impostazioni />, sezioni: SEZIONI },
]

/** Il menu Altro del telefono, nell'ordine della tavola (Menu v76, `altro telefono`): non e'
 *  quello del desktop, e Da confermare ha la sua icona nella testa. */
export const ALTRO_TELEFONO: readonly string[] = [
  "/progetti",
  "/statistiche",
  "/planner",
  "/piano-della-notte",
  "/selezione-dei-frame",
  "/attrezzatura",
  "/impostazioni",
]

/** Le pagine di un indirizzo dell'elenco, nell'ordine dato. */
export function pagineDi(indirizzi: readonly string[]): Pagina[] {
  return indirizzi.flatMap((a) => PAGINE.filter((p) => p.a === a))
}

/** Le sezioni di una pagina che esistono davvero, nell'ordine del contratto. */
export function sezioniAperte(sezioni: readonly Sezione[] | undefined): readonly Sezione[] {
  return (sezioni ?? []).filter((s) => s.elemento !== undefined)
}

/** La pagina a cui appartiene un indirizzo, **sezioni comprese**: la chiedono le rotte, il
 *  titolo del telefono e la voce accesa, e scritta tre volte divergerebbe. */
export function paginaDi(indirizzo: string): Pagina | undefined {
  return PAGINE.find(
    (p) => p.a === indirizzo || sezioniAperte(p.sezioni).some((s) => s.a === indirizzo),
  )
}
