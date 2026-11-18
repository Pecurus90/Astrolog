// @vitest-environment jsdom
/**
 * Impostazioni, le sezioni Cartelle e scansione, Meteo, ASTAP e Luna (tavola v82): l'impronta del
 * markup su desktop e telefono ferma classi e misure della consegna, che un'asserzione puntuale non
 * dice. Un ritocco voluto della tavola riscrive l'impronta attesa.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  FERMO,
  SALUTE,
  SPINA,
  chiamate,
  STANOTTE,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  vai,
  type Voce,
} from "./banco"
import { impronta } from "./impronta"

afterEach(pulisci)

const CARTELLE = {
  items: [
    {
      id: 1,
      name: "2025",
      root_path: "D:\\Astro\\2025",
      created_at: "2026-09-16T10:00:00Z",
      reachable: true,
      frames: 3180,
      reactivated: false,
    },
    {
      id: 2,
      name: "astro",
      root_path: "\\\\NAS\\foto\\astro",
      created_at: "2026-09-16T10:00:00Z",
      reachable: false,
      frames: 1,
      reactivated: false,
    },
  ],
  total: 2,
  limit: 50,
  offset: 0,
}
const SOLVER = {
  path: "C:\\Program Files\\astap\\astap_cli.exe",
  source: "declared",
  declared: "C:\\Program Files\\astap\\astap_cli.exe",
  databases: ["d50"],
}
const stato = (corpo: object) => ({
  "/api/v1/pipeline/status": { stato: 200, corpo: { ...FERMO, ...corpo } },
})
const IN_CORSO = stato({
  action: "stop",
  worker: { ...FERMO.worker, state: "running", stage: "scan" },
})
const INTERROTTA = stato({ action: "resume" })
const BLOCCATA = stato({ worker: { ...FERMO.worker, state: "error" } })
const entrambe = async (titolo: string) => {
  await screen.findByText(/3180 frame in archivio$/)
  await screen.findByText(titolo)
}

async function sezione(
  chiave: string,
  carta: string,
  telefono: boolean,
  piu: Record<string, Voce> = {},
  cartelle: unknown = CARTELLE,
  solver: unknown = SOLVER,
) {
  rispondi({
    ...STANOTTE,
    ...SPINA,
    ...piu,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "/api/v1/folders": { stato: 200, corpo: cartelle },
    "/api/v1/solver": { stato: 200, corpo: solver },
  })
  await disegna()
  vai(`/impostazioni/${chiave}${telefono ? "?formato=telefono" : ""}`)
  const regione = await screen.findByRole("region", { name: carta })
  return regione.parentElement as HTMLElement
}

async function impronte(
  chiave: string,
  carta: string,
  attesa: () => Promise<unknown>,
  piu: Record<string, Voce> = {},
  cartelle: unknown = CARTELLE,
  solver: unknown = SOLVER,
) {
  const visti: string[] = []
  for (const telefono of [false, true]) {
    const dove = await sezione(chiave, carta, telefono, piu, cartelle, solver)
    await attesa()
    visti.push(impronta(dove.outerHTML))
    pulisci()
  }
  return visti
}

describe("Impostazioni, le impronte della consegna", () => {
  it("Cartelle e scansione: piene, vuote, e a scansione in corso", async () => {
    const piene = await impronte("cartelle", "Scansione", () =>
      entrambe("Nessuna scansione finora"),
    )
    const vuote = await impronte(
      "cartelle",
      "Scansione",
      () => screen.findByText("Nessuna scansione finora"),
      {},
      { ...CARTELLE, items: [], total: 0 },
    )
    const corre = await impronte(
      "cartelle",
      "Scansione",
      () => entrambe("Scansione in corso"),
      IN_CORSO,
    )
    const ferma = await impronte(
      "cartelle",
      "Scansione",
      () => entrambe("! Scansione interrotta"),
      INTERROTTA,
    )
    const rotta = await impronte(
      "cartelle",
      "Scansione",
      () => entrambe("! Scansione bloccata"),
      BLOCCATA,
    )
    expect([...piene, ...vuote, ...corre, ...ferma, ...rotta]).toEqual([
      "16736923",
      "98802005",
      "17d59a5b",
      "2568ef67",
      "62160445",
      "4b7a0b0f",
      "b9868b86",
      "4a794b52",
      "743736ed",
      "f58a820f",
    ])
  })

  it("Cartelle: Togli e Sposta aperti nella riga", async () => {
    const visti: string[] = []
    for (const telefono of [false, true]) {
      const dove = await sezione("cartelle", "Scansione", telefono)
      const riga = (await within(dove).findByText(/3180 frame in archivio$/)).closest(
        "li, [role=listitem], div",
      ) as HTMLElement
      fireEvent.click(within(dove).getAllByText("Togli")[0] as HTMLElement)
      visti.push(impronta(dove.outerHTML))
      fireEvent.click(within(dove).getAllByText("Sposta")[0] as HTMLElement)
      visti.push(impronta(dove.outerHTML))
      expect(riga).toBeTruthy()
      pulisci()
    }
    expect(visti).toEqual(["8ef25ced", "1532d010", "d0303647", "7d559c4c"])
  })

  it("togliere una cartella rilegge anche il conto di Da confermare (Issue #20)", async () => {
    // il vuoto di Da confermare dipende dalle cartelle: senza, restava quello di prima 5 minuti
    const dove = await sezione("cartelle", "Scansione", false, {
      "DELETE /api/v1/folders": { stato: 200, corpo: { deleted: true } },
    })
    await within(dove).findByText(/3180 frame in archivio$/)
    const domande = () => chiamate().filter((u) => u.endsWith("/api/v1/review")).length
    const prima = domande()
    fireEvent.click(within(dove).getAllByText("Togli")[0] as HTMLElement)
    fireEvent.click(within(dove).getByRole("button", { name: "Togli la cartella" }))
    await waitFor(() => expect(domande()).toBeGreaterThan(prima))
  })

  it("Meteo", async () => {
    expect(await impronte("meteo", "Previsione", () => Promise.resolve())).toEqual([
      "8750305a",
      "19bcc529",
    ])
  })

  it("ASTAP trovato e assente", async () => {
    const trovato = await impronte("astap", "ASTAP", () =>
      screen.findByText(/astap_cli\.exe · percorso inserito manualmente$/),
    )
    const assente = await impronte("astap", "ASTAP", () => Promise.resolve(), {}, CARTELLE, {
      path: null,
      source: null,
      declared: null,
      databases: [],
    })
    expect([...trovato, ...assente]).toEqual(["2fc2da56", "41e2be2e", "d2e5cc60", "240a627e"])
  })

  it("Luna", async () => {
    expect(
      await impronte("luna", "Luna", () =>
        screen.findByLabelText("Banda larga buona fino a, in percento"),
      ),
    ).toEqual(["493c6419", "dd04a167"])
  })
})
