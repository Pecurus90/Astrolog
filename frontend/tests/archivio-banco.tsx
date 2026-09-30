/**
 * Il banco dell'**Archivio**: le righe di prova e i due gesti con cui si arriva alla pagina.
 *
 * Sta qui e non in uno dei due file di prova perche' li usano tutti e due -- la pagina
 * (`archivio.test.tsx`) e la barra (`archivio-barra.test.tsx`), spezzati quando il primo ha
 * superato il tetto di righe. Due copie di un banco non sono due prove: sono una prova e una
 * copia che un giorno racconta un archivio diverso.
 */
import { fireEvent, screen } from "@testing-library/react"

import { SALUTE, SPINA, STANOTTE, type Voce, disegna, impostazioni, rispondi } from "./banco"

/** Un oggetto pieno: catalogo, costellazione, tipo, e due filtri in ordine di tempo. */
export const M31 = {
  key: "m-31",
  name: "M 31",
  slug: "m-31",
  frames: 120,
  integration_s: 43200,
  untimed: 0,
  constellation: "And",
  type_code: "GALAXY",
  filters: [
    { name: "Lum", passband: "L", frames: 80, integration_s: 28800 },
    { name: "Ha", passband: "HA", frames: 40, integration_s: 14400 },
  ],
  panels: null,
  panel_list: [],
}

/** Cio' che il catalogo non sa dire, e pose di cui una parte non dice la durata: e' la riga di
 *  chiunque abbia un archivio a meta' corsa, non un caso di laboratorio. */
export const IGNOTO = {
  key: "NGC 7000",
  name: "NGC 7000",
  slug: null,
  frames: 40,
  integration_s: 7200,
  untimed: 12,
  constellation: null,
  type_code: null,
  filters: [],
  panels: null,
  panel_list: [],
}

/** Un mosaico confermato: una riga sola, col nome detto e i suoi quattro pannelli. */
export const MOSAICO = {
  ...M31,
  key: "Newton|ASI2600|800.0#80.00,34.00",
  name: "IC 405",
  slug: "ic-405",
  constellation: "Aur",
  type_code: "EMISSION_NEBULA",
  panels: 4,
  panel_list: [
    { object: "IC 405", ra_deg: 79.07, dec_deg: 34.25, frames: 40, integration_s: 14400, untimed: 0 },
    { object: "LBN 796, Sh2 230", ra_deg: 80.5, dec_deg: 34.9, frames: 30, integration_s: 10800, untimed: 0 },
    { object: "LDN 1516", ra_deg: 81.2, dec_deg: 33.6, frames: 30, integration_s: 10800, untimed: 0 },
    { object: null, ra_deg: 79.9, dec_deg: 33.1, frames: 20, integration_s: 7200, untimed: 2 },
  ],
}

/** Cosa offrono le tendine. Di fabbrica quelle dell'archivio di prova: una pagina senza
 *  scelte e' lo stato di chi ha appena installato l'app, non il caso normale. */
export const SCELTE = {
  catalogs: ["M", "NGC"],
  constellations: ["And", "Cyg"],
  filters: ["Lum", "Ha"],
  mosaics: false,
}

/** Cio' che il banco risponde su ogni rotta che la pagina tocca, con **la voce dell'Archivio
 *  passata da chi chiama**: i casi che contano davvero -- una risposta trattenuta, un 500 -- non
 *  cambiano il corpo ma la voce, e senza questo la mappa si riscriveva a mano a ogni prova. */
export function conArchivio(voce: Voce) {
  return {
    ...STANOTTE,
    "/api/v1/archive": voce,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  }
}

/** La voce buona: duecento, con le righe che le passi. Quante ne ha trovate, di fabbrica, sono
 *  tutte oggetti: chi prova i mosaici lo dice in `found`. */
export function voceArchivio(items: unknown[], extra: Record<string, unknown> = {}) {
  const total = (extra.total as number | undefined) ?? items.length
  const found = { objects: total, mosaics: 0 }
  return {
    stato: 200,
    corpo: { items, total, found, limit: 100, offset: 0, choices: SCELTE, ...extra },
  }
}

export function archivio(items: unknown[], extra: Record<string, unknown> = {}) {
  rispondi(conArchivio(voceArchivio(items, extra)))
}

/** Apre l'app e va sull'Archivio dalla barra: e' la strada che fa l'utente, e prova anche che la
 *  voce sia accesa -- una pagina raggiungibile solo scrivendo l'indirizzo non esiste. */
export async function apriArchivio() {
  const reso = await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /archivio/i }))
  await screen.findByRole("heading", { name: /archivio/i })
  return reso
}

/** L'Archivio raggiunto da un **indirizzo fabbricato**: un collegamento che ti sei mandato, o una
 *  riga scritta a mano. Si passa dalla barra e poi si cambia indirizzo, invece di partire di la',
 *  perche' e' quello che fa il browser -- e perche' cosi' si prova anche che i criteri arrivino
 *  dall'indirizzo e non dallo stato lasciato dal gesto di prima. */
export async function apriArchivioSu(indirizzo: string) {
  const reso = await apriArchivio()
  window.history.replaceState(null, "", indirizzo)
  fireEvent.popState(window)
  return reso
}

/** Passa all'altra vista come farebbe l'utente: cliccando la sua scheda. */
export async function vaiAll(vista: RegExp) {
  fireEvent.click(await screen.findByRole("tab", { name: vista }))
}

/** La barra che contiene il campo di ricerca: e' il posto dove vivono `aria-busy` e i segni
 *  dell'attesa, e pescarla dal campo e' l'unico modo stabile -- la barra non ha un ruolo suo. */
export async function laBarra() {
  return (await screen.findByLabelText(/cerca un oggetto/i)).closest(".as-barra")
}
