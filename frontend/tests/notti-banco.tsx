/**
 * Il banco delle **Notti**: le notti di prova, le rotte e la pagina montata da sola.
 *
 * Sta qui perche' lo usano due file (`notti-pagina.test.tsx`, `notti-pagina-navigazione.test.tsx`):
 * due copie delle stesse notti un giorno raccontano due archivi.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import { MemoryRouter, Route, Routes, useLocation } from "react-router"
import { vi } from "vitest"

import { chiamate, rispondi, type Voce } from "./banco"

export const CIELO = {
  state: "ok",
  arrives_on: null,
  verdict: "go",
  cloud_total_pct: 8,
  usable_hours: 7,
  window: "dark",
  window_hours: 9,
  transparency: 88,
  exposure_hours: 7.9,
  dark_hours: 9,
  without_aerosol: true,
  sky_word: "scattered",
}

export const DICIOTTO = {
  id: 7,
  night_date: "2024-05-18",
  site: "Cima Ekar",
  site_source: "detected",
  site_from: "frames",
  shooting: { kind: "mixed", broadband_hours: 3.5, dark_hours: 7.5 },
  frames: 3,
  integration_s: 10800,
  untimed: 0,
  objects: [
    { key: "m-51", name: "M 51", frames: 2, integration_s: 7200, untimed: 0, bar_pct: 100 },
  ],
  filters: [{ name: "Ha", passband: "HA", frames: 2, integration_s: 7200 }],
  moon: { phase_key: "waxing_gibbous", illumination_pct: 69, lit_side: "right" },
  weather: CIELO,
}

export const DICIASSETTE = {
  ...DICIOTTO,
  id: 6,
  night_date: "2024-05-17",
  site: "Casa",
  site_from: "home",
  shooting: null,
  frames: 1,
  integration_s: 0,
  untimed: 1,
  moon: null,
  weather: { ...CIELO, state: "unknown", verdict: null, exposure_hours: null, sky_word: null },
}

export const APRILE = {
  ...DICIASSETTE,
  id: 3,
  night_date: "2024-04-02",
  integration_s: 600,
  untimed: 0,
  site_from: "answer",
}

// Una notte che la pagina non ha caricato: arriva sola, dal calendario.
export const VENTI = { ...DICIOTTO, id: 99, night_date: "2024-05-20", site: "Asiago" }

export const CRITERI = [
  { key: "year", options: [{ value: "2024", nights: 3, chosen: false }] },
  {
    key: "site",
    options: [
      { value: "1", name: "Casa", nights: 2, chosen: false, passband: "HA" },
      { value: "2", name: "Cima Ekar", nights: 1, chosen: false },
    ],
  },
  {
    key: "setup",
    options: [
      { value: "s1", name: "Il piccolo", nights: 1, chosen: false },
      {
        value: "s2",
        name: null,
        optics: "RedCat 51",
        camera: "ASI 2600",
        nights: 1,
        chosen: false,
      },
      { value: "s3", name: null, optics: null, camera: "ASI 533", nights: 1, chosen: false },
      { value: "s4", name: null, optics: null, camera: null, nights: 1, chosen: false },
    ],
  },
  {
    key: "filter",
    options: [
      { value: "Ha", passband: "HA", nights: 1, chosen: false },
      { value: "OIII", passband: "OIII", nights: 0, chosen: false },
      { value: "Strano", passband: "MISTERO", nights: 1, chosen: false },
      { value: "__no_filter__", nights: 2, chosen: false },
    ],
  },
  { key: "constellation", options: [{ value: "CVn", nights: 1, chosen: false }] },
  {
    key: "sky",
    options: [
      { value: "go", nights: 1, chosen: false },
      { value: "marginal", nights: 1, chosen: false },
      { value: "nogo", nights: 1, chosen: false },
      { value: "unknown", nights: 2, chosen: false },
      { value: "nuovo", nights: 0, chosen: true },
    ],
  },
]

export const MAGGIO = {
  month: "2024-05",
  days: [
    { day: 17, verdict: null, nights: [{ id: 6, site: "Casa", verdict: null }] },
    {
      day: 18,
      verdict: "go",
      nights: [
        { id: 7, site: "Cima Ekar", verdict: "go" },
        { id: 8, site: "Rifugio", verdict: null },
      ],
    },
    { day: 20, verdict: "go", nights: [{ id: 99, site: "Asiago", verdict: "go" }] },
    { day: 21, verdict: null, nights: [{ id: 98, site: "Via", verdict: null }] },
    { day: 22, verdict: null, nights: [{ id: 97, site: "Rotta", verdict: null }] },
    { day: 23, verdict: null, nights: [{ id: 96, site: "Lenta", verdict: null }] },
  ],
  nights: 2,
  good: 1,
  integration_s: 11400,
  untimed: 0,
  first_month: "2024-04",
  last_month: "2026-11",
  tonight: "2026-11-07",
}

export const APRILE_MESE = {
  ...MAGGIO,
  month: "2024-04",
  days: [
    { day: 2, verdict: null, nights: [{ id: 3, site: "Casa", verdict: null }] },
    { day: 5, verdict: null, nights: [{ id: 96, site: "Lenta", verdict: null }] },
  ],
  nights: 1,
  good: 0,
  integration_s: 0,
}

export const GIUGNO = {
  ...MAGGIO,
  month: "2024-06",
  days: [],
  nights: 0,
  good: 0,
  integration_s: 0,
}

export const NOVEMBRE = { ...GIUGNO, month: "2026-11", first_month: null, last_month: "2026-11" }

export function pagina(items: unknown[], extra: Record<string, unknown> = {}) {
  return {
    items,
    total: items.length,
    limit: 20,
    offset: 0,
    criteria: CRITERI,
    months: [
      { month: "2024-05", nights: 2, integration_s: 11400, untimed: 0 },
      { month: "2024-04", nights: 1, integration_s: 600, untimed: 0 },
    ],
    empty: null,
    totals: { nights: items.length, frames: 4, integration_s: 11400, untimed: 0, objects: 3 },
    waiting: [],
    waiting_frames: 0,
    still_reading: 0,
    reading_done_pct: null,
    ...extra,
  }
}

export const TRE = pagina([DICIOTTO, DICIASSETTE, APRILE])

export const mai = new Promise<unknown>(() => undefined)

/** Le rotte delle Notti: le voci date vincono, poi le notti sole e i mesi del calendario. */
export function rotte(corpo: unknown, prima: Record<string, Voce> = {}): Record<string, Voce> {
  return {
    ...prima,
    "night=99&limit=1": { stato: 200, corpo: pagina([VENTI]) },
    "night=98&limit=1": { stato: 200, corpo: pagina([]) },
    "night=97&limit=1": { stato: 500, corpo: { detail: "x" } },
    "night=96&limit=1": { stato: 200, corpo: pagina([]), attesa: mai },
    "month=2024-04": { stato: 200, corpo: APRILE_MESE },
    "month=2024-06": { stato: 200, corpo: GIUGNO },
    "/api/v1/nights/calendar": { stato: 200, corpo: MAGGIO },
    "/api/v1/nights": { stato: 200, corpo },
  }
}

export function Altrove() {
  const dove = useLocation()
  return <p data-testid="altrove">{dove.pathname}</p>
}

/** La pagina montata a un indirizzo, coi moduli azzerati: il client nasce col fetch del banco. */
export async function apri(mappa: Record<string, Voce>, indirizzo = "/notti") {
  rispondi(mappa)
  vi.resetModules()
  const { Notti } = await import("../src/Notti")
  const { FinestraDellOggetto } = await import("../src/FinestraDellOggetto")
  const dati = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={dati}>
      <MemoryRouter initialEntries={[indirizzo]}>
        {/* the shell holds the object window: the Nights open it from their objects */}
        <FinestraDellOggetto>
          <Routes>
            <Route path="/notti" element={<Notti />} />
            <Route path="*" element={<Altrove />} />
          </Routes>
        </FinestraDellOggetto>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

export const chieste = (parte: string) => chiamate().filter((u) => u.includes(parte))
export const notte = () => screen.findByRole("region", { name: "La notte" })
export const titolo = async () => (await notte()).querySelector("b")?.textContent
export const dove = async () => (await screen.findByTestId("altrove")).textContent
export const cartaDelMese = () => screen.findByRole("region", { name: "Calendario delle notti" })
// la carta c'e' subito, il mese quando arriva
export const calendario = () =>
  waitFor(() => {
    const carta = screen.getByRole("region", { name: "Calendario delle notti" })
    if (!carta.querySelector(".al-c-calendario-notti__testo-1"))
      throw new Error("il mese non e' arrivato")
    return carta
  })
export const titoloMese = async () =>
  (await calendario()).querySelector(".al-c-calendario-notti__testo-1")?.textContent
export const giorno = (n: RegExp) => screen.findByRole("button", { name: n })
export const statoTel = () =>
  waitFor(() => {
    const a = document.querySelector<HTMLElement>(".al-notti__riga-25")
    if (!a) throw new Error("manca il bottone dello stato")
    return a
  })

export async function apriCriteri() {
  const carta = await screen.findByRole("region", { name: "Criteri delle notti" })
  fireEvent.click(within(carta).getByRole("link", { name: "Apri" }))
  return carta
}

export const opzione = (gruppo: string, nome: string) => {
  const g = screen.getAllByRole("group", { name: gruppo })[0] as HTMLElement
  const voce = [...g.querySelectorAll<HTMLElement>(".al-scelta__voce")].find((v) =>
    v.textContent?.startsWith(nome),
  )
  if (!voce) throw new Error(`manca ${nome} in ${gruppo}`)
  return voce
}

export const voci = (gruppo: string) =>
  [
    ...(screen.getAllByRole("group", { name: gruppo })[0] as HTMLElement).querySelectorAll(
      ".al-scelta__voce",
    ),
  ].map((v) => v.textContent)
