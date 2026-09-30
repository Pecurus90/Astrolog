import type { ReactElement } from "react"

import { Archivio } from "./Archivio"
import { Attrezzatura } from "./Attrezzatura"
import { Confermare } from "./Confermare"
import { Home } from "./Home"
import { Meteo } from "./Meteo"
import { Notti } from "./Notti"
import { Impostazioni, SEZIONI } from "./Impostazioni"
import type { Chiave } from "./i18n"

/**
 * Le pagine dell'app in un posto solo: la barra le legge da qui, e le rotte pure. Due elenchi
 * che possono divergere sono il modo in cui una voce di menu porta a una pagina che non c'e'.
 *
 * - **Lo scheletro e' deciso tutto** (`docs/domini/navigazione.md`): i tre gruppi e il loro
 *   ordine stanno qui anche per le pagine che non esistono ancora, cosi' quando nascono nessuno
 *   ridiscute dove vanno.
 * - **Ma si mostra solo cio' che porta da qualche parte**: una voce senza `elemento` e' una
 *   pagina non ancora nata, e non compare ne' nella barra ne' fra le rotte. Una voce che apre
 *   una pagina vuota e' una promessa che l'app non mantiene.
 * - **L'ordine dei gruppi e delle voci dentro ogni gruppo e' contratto**, non gusto: si legge
 *   dall'alto come si lavora.
 */

/** I gruppi nell'ordine in cui si leggono. `cima` e `fondo` non hanno titolo: sono le voci
 *  che stanno da sole -- Casa sopra tutto, Impostazioni staccata in fondo. */
export const GRUPPI = ["cima", "guarda", "sistema", "pianifica", "fondo"] as const
export type Gruppo = (typeof GRUPPI)[number]

/** I gruppi che a schermo portano un titolo, col titolo: gli altri due (`cima`, `fondo`) sono
 *  contenitori di posizione e non si scrivono da nessuna parte. La mappa sta qui e non nel
 *  layout, cosi' un gruppo nuovo nasce con la sua parola o non compila. */
export const TITOLI: Partial<Record<Gruppo, Chiave>> = {
  guarda: "nav.group.guarda",
  sistema: "nav.group.sistema",
  pianifica: "nav.group.pianifica",
}

/** Una sezione dentro una pagina: ha il suo indirizzo, come una pagina.
 *
 * Vale la stessa regola delle voci di barra -- **senza elemento non esiste**, quindi non e' una
 * rotta e la navigazione a sezioni non la mostra. Una sezione che si apre su niente e' una
 * promessa che l'app non mantiene, esattamente come una voce di menu. */
export type Sezione = {
  a: string
  chiave: Chiave
  elemento?: ReactElement
}

export type Pagina = {
  a: string
  chiave: Chiave
  gruppo: Gruppo
  /** Manca finche' la pagina non esiste: e' cio' che tiene la voce fuori dalla barra. */
  elemento?: ReactElement
  /** Le sezioni che hanno un indirizzo loro. La **prima aperta** e' anche cio' che si vede
   *  aprendo l'indirizzo della pagina. */
  sezioni?: readonly Sezione[]
}

export const PAGINE: readonly Pagina[] = [
  { a: "/", chiave: "nav.home", gruppo: "cima", elemento: <Home /> },
  { a: "/archivio", chiave: "nav.archive", gruppo: "guarda", elemento: <Archivio /> },
  { a: "/notti", chiave: "nav.nights", gruppo: "guarda", elemento: <Notti /> },
  { a: "/attrezzatura", chiave: "nav.gear", gruppo: "guarda", elemento: <Attrezzatura /> },
  { a: "/statistiche", chiave: "nav.stats", gruppo: "guarda" },
  { a: "/da-confermare", chiave: "nav.review", gruppo: "sistema", elemento: <Confermare /> },
  { a: "/diagnostica", chiave: "nav.diagnostics", gruppo: "sistema" },
  { a: "/planner", chiave: "nav.planner", gruppo: "pianifica" },
  { a: "/progetti", chiave: "nav.projects", gruppo: "pianifica" },
  { a: "/carta-del-cielo", chiave: "nav.sky", gruppo: "pianifica" },
  { a: "/meteo", chiave: "nav.weather", gruppo: "pianifica", elemento: <Meteo /> },
  // Impostazioni e' una pagina con dentro le sue sezioni -- Cartelle, i siti, il nome, i servizi,
  // le soglie -- ognuna col suo indirizzo (`/impostazioni/cartelle`). Nella barra sta una voce
  // sola: quelle cose si toccano una volta ogni tanto, e una voce in meno vale piu' di un clic.
  {
    a: "/impostazioni",
    chiave: "nav.settings",
    gruppo: "fondo",
    elemento: <Impostazioni />,
    sezioni: SEZIONI,
  },
]

/** Quelle che esistono davvero: la barra mostra queste, e le rotte sono queste. */
export const APERTE = PAGINE.filter((p) => p.elemento !== undefined)

/** Le sezioni di una pagina che esistono davvero, nell'ordine del contratto. */
export function sezioniAperte(sezioni: readonly Sezione[] | undefined): readonly Sezione[] {
  return (sezioni ?? []).filter((s) => s.elemento !== undefined)
}

/** La pagina a cui appartiene un indirizzo, **sezioni comprese**.
 *
 * Sta qui e non nel layout perche' la stessa domanda la fanno in tre: le rotte, il titolo in alto
 * e la voce accesa nella barra. Scritta tre volte, un sotto-indirizzo accenderebbe la rotta e
 * lascerebbe la barra a dire "Pagina sconosciuta" -- che e' proprio cio' che succedeva prima. */
export function paginaDi(indirizzo: string): Pagina | undefined {
  return APERTE.find(
    (p) => p.a === indirizzo || sezioniAperte(p.sezioni).some((s) => s.a === indirizzo),
  )
}
