/**
 * Il banco dell'**Archivio** (tavola v78): le righe di prova, la risposta della rotta e i gesti
 * con cui si arriva alla pagina. Lo usano la pagina (`archivio.test.tsx`), i criteri
 * (`archivio-criteri.test.tsx`) e la finestra dell'oggetto (`archivio-finestra.test.tsx`).
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { expect } from "vitest"

import { SALUTE, SPINA, STANOTTE, type Voce, disegna, impostazioni, rispondi } from "./banco"

/** Un oggetto pieno: catalogo, costellazione, tipo, nome comune e due filtri in ordine di tempo. */
export const M31 = {
  key: "m-31",
  name: "M 31",
  slug: "m-31",
  common_name: "Andromeda Galaxy",
  frames: 120,
  integration_s: 43200,
  untimed: 0,
  constellation: "And",
  type_code: "GALAXY",
  filters: [
    { name: "Lum", passband: "L", frames: 80, integration_s: 28800 },
    { name: "Ha", passband: "HA", frames: 40, integration_s: 14400 },
  ],
  productions: [
    {
      optics: "Rifrattore",
      camera: "ASI2600",
      optics_id: 1,
      camera_id: 2,
      frames: 120,
      integration_s: 43200,
      untimed: 0,
      filters: [],
    },
  ],
  panels: null,
  panel_list: [],
}

/** Cio' che il catalogo non sa dire, e frame di cui una parte non dice la durata. */
export const IGNOTO = {
  key: "NGC 7000",
  name: "NGC 7000",
  slug: null,
  common_name: null,
  frames: 40,
  integration_s: 7200,
  untimed: 12,
  constellation: null,
  type_code: null,
  filters: [],
  productions: [{ ...M31.productions[0], frames: 40, integration_s: 7200, untimed: 12 }],
  panels: null,
  panel_list: [],
}

/** Un mosaico confermato: una riga sola, col nome detto e i suoi quattro pannelli. */
export const MOSAICO = {
  ...M31,
  key: "Newton|ASI2600|800.0#80.00,34.00",
  name: "IC 405",
  slug: "ic-405",
  common_name: null,
  constellation: "Aur",
  type_code: "EMISSION_NEBULA",
  panels: 4,
  panel_list: [
    { id: 11, object: "IC 405", ra_deg: 79.07, dec_deg: 34.25, frames: 40, integration_s: 14400, untimed: 0 },
    { id: 12, object: "LBN 796, Sh2 230", ra_deg: 80.5, dec_deg: 34.9, frames: 30, integration_s: 10800, untimed: 0 },
    { id: 13, object: "LDN 1516", ra_deg: 81.2, dec_deg: 33.6, frames: 30, integration_s: 10800, untimed: 0 },
    { id: 14, object: null, ra_deg: 79.9, dec_deg: 33.1, frames: 20, integration_s: 7200, untimed: 2 },
  ],
}

const voce = (value: string, rows: number, extra: Record<string, unknown> = {}) => ({
  value,
  label: null,
  passband: null,
  rows,
  chosen: false,
  ...extra,
})

/** I criteri dell'archivio di prova: due anni, due costellazioni, due filtri. */
export const CRITERI = [
  { key: "year", options: [voce("2025", 1), voce("2024", 2)] },
  { key: "constellation", options: [voce("And", 1), voce("Cyg", 0)] },
  {
    key: "filter",
    options: [voce("Lum", 1, { passband: "L" }), voce("Ha", 2, { passband: "HA" })],
  },
  { key: "site", options: [voce("1", 1, { label: "Casa" }), voce("2", 1, { label: "Cima Ekar" })] },
]

/** Tutto l'archivio, la testa della pagina. */
export const INTERO = {
  rows: 240,
  mosaics: 3,
  frames: 18430,
  integration_s: 486 * 3600,
  untimed: 0,
  nights: 212,
}

/** Cio' che il banco risponde su ogni rotta che la pagina tocca, con la voce dell'Archivio
 *  passata da chi chiama: una risposta trattenuta, un 500. */
export function conArchivio(v: Voce) {
  return {
    ...STANOTTE,
    "/api/v1/archive": v,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  }
}

/** La voce buona: duecento, con le righe che le passi. */
export function voceArchivio(items: unknown[], extra: Record<string, unknown> = {}) {
  const total = (extra.total as number | undefined) ?? items.length
  return {
    stato: 200,
    corpo: {
      items,
      total,
      found: { objects: total, mosaics: 0 },
      limit: 20,
      offset: 0,
      whole: { ...INTERO, rows: Math.max(total, items.length) },
      criteria: CRITERI,
      unresolved: null,
      ...extra,
    },
  }
}

export function archivio(items: unknown[], extra: Record<string, unknown> = {}) {
  rispondi(conArchivio(voceArchivio(items, extra)))
}

/** Apre l'app e va sull'Archivio dalla barra: e' la strada che fa l'utente. */
export async function apriArchivio() {
  const reso = await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /archivio/i }))
  await waitFor(() => expect(window.location.pathname).toBe("/archivio"))
  return reso
}

/** L'Archivio raggiunto da un indirizzo fabbricato: un collegamento che ti sei mandato. */
export async function apriArchivioSu(indirizzo: string) {
  const reso = await apriArchivio()
  window.history.replaceState(null, "", indirizzo)
  fireEvent.popState(window)
  return reso
}

/** Passa all'altra vista come farebbe l'utente: col suo bottone a icona. */
export async function vaiAll(vista: RegExp) {
  fireEvent.click(await screen.findByRole("radio", { name: vista }))
}

/** Il comando che apre la finestra di una riga: il suo nome comincia con quello dell'oggetto. */
export async function apriDi(nome: string): Promise<HTMLElement> {
  const esatto = new RegExp(`^${nome.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")},`)
  return screen.findByRole("link", { name: esatto })
}

/** Le carte delle righe, nell'ordine della pagina: le sezioni dentro la griglia delle carte. */
export async function carte(): Promise<HTMLElement[]> {
  await screen.findAllByRole("link", { name: /apri il riepilogo$/ })
  return [...document.querySelectorAll<HTMLElement>(".al-arch__centro-1 > section")]
}
