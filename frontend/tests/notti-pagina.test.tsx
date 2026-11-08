// @vitest-environment jsdom
/**
 * La pagina **Notti** (`src/Notti.tsx`) montata da sola, col banco al posto del backend: cosa chiede
 * e quando, mentre arriva e se non arriva, i vuoti, quale notte e' la protagonista e le sue vicine.
 * Striscia, calendario, criteri e telefono stanno in `notti-pagina-navigazione.test.tsx`.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { chiamate, pulisci } from "./banco"
import {
  DICIOTTO,
  TRE,
  apri,
  apriCriteri,
  calendario,
  chieste,
  dove,
  giorno,
  mai,
  notte,
  opzione,
  pagina,
  rotte,
  titolo,
  titoloMese,
} from "./notti-banco"

afterEach(() => {
  vi.useRealTimers()
  pulisci()
})

describe("cosa la pagina chiede", () => {
  it("l'elenco 20 alla volta, la striscia le ultime 7, il mese della protagonista; niente notte sola", async () => {
    await apri(rotte(TRE))
    await notte()
    await calendario()
    expect(chieste("/api/v1/nights?limit=20&offset=0").length).toBeGreaterThan(0)
    expect(chieste("/api/v1/nights?limit=7").length).toBeGreaterThan(0)
    expect(chieste("calendar?month=2024-05").length).toBeGreaterThan(0)
    expect(chieste("limit=1")).toEqual([])
  })

  it("senza notti non chiede ne' una notte sola ne' un mese", async () => {
    await apri(rotte(pagina([])))
    await screen.findByText("Nessuna notte con questi criteri")
    expect(chieste("limit=1")).toEqual([])
    expect(chieste("calendar")).toEqual([])
  })

  it("con ?notte= chiede solo quella: niente striscia, calendario, criteri, archivio", async () => {
    await apri(
      rotte(pagina([DICIOTTO], { waiting: [{ answer_at: "review", frames: 3 }] })),
      "/notti?notte=70",
    )
    expect(await titolo()).toBe("Sabato 18 maggio 2024")
    expect(chieste("limit=20&offset=0&night=70").length).toBeGreaterThan(0)
    expect(chieste("limit=7")).toEqual([])
    expect(chieste("calendar")).toEqual([])
    expect(screen.queryByRole("region", { name: "Le notti" })).toBeNull()
    expect(screen.queryByRole("region", { name: "Criteri delle notti" })).toBeNull()
    expect(screen.queryByRole("region", { name: "A confronto" })).toBeNull()
    expect(screen.queryByRole("region", { name: "Tutto l’archivio" })).toBeNull()
    expect(screen.queryByText("3 frame da confermare")).toBeNull()
    expect((await notte()).style.gridColumn).toBe("span 12")
  })

  it("un ?notte= storto non chiede niente e dice che la notte non c'e'", async () => {
    for (const storto of ["abc", "07", "7x", "x7", "0"]) {
      const reso = await apri(rotte(TRE), `/notti?notte=${storto}`)
      expect(await screen.findByText("Notte non trovata")).toBeTruthy()
      expect(screen.getByText("I frame sono stati rimossi o spostati.")).toBeTruthy()
      expect(chiamate()).toEqual([])
      reso.unmount()
      pulisci()
    }
  })

  it("dalla notte storta, Tutte le notti riporta all'elenco", async () => {
    await apri(rotte(TRE), "/notti?notte=abc")
    fireEvent.click(await screen.findByRole("button", { name: "Tutte le notti" }))
    expect(await titolo()).toBe("Sabato 18 maggio 2024")
  })

  it("dalla notte sola, la freccia in alto riporta a tutte le notti", async () => {
    await apri(rotte(pagina([DICIOTTO])), "/notti?notte=7")
    const torna = await screen.findByText("← Tutte le notti")
    expect(torna.getAttribute("href")).toBe("/notti")
    fireEvent.click(torna)
    expect(await screen.findByRole("region", { name: "Le notti" })).toBeTruthy()
  })

  it("una notte dall'indirizzo che non c'e' piu' lo dice", async () => {
    await apri(rotte(pagina([])), "/notti?notte=99")
    expect(await screen.findByText("Notte non trovata")).toBeTruthy()
  })
})

describe("mentre arriva, e se non arriva", () => {
  it("mentre l'elenco arriva c'e' lo scheletro, sul desktop e sul telefono", async () => {
    // le carte dello scheletro stanno dove staranno quelle vere (tavola v76, `SK`)
    const casi: [string, string[], string[]][] = [
      ["/notti", ["span 8", "span 4", "span 12"], ["560px", "", "520px"]],
      ["/notti?formato=telefono", ["auto", "auto"], ["390px", "420px"]],
    ]
    for (const [indirizzo, colonne, altezze] of casi) {
      const reso = await apri(
        { "/api/v1/nights": { stato: 200, corpo: TRE, attesa: mai } },
        indirizzo,
      )
      const scheletro = await screen.findByRole("status", { name: "Caricamento…" })
      expect(scheletro.textContent).toBe("Caricamento…")
      const carte = [...scheletro.children] as HTMLElement[]
      expect(carte.map((c) => c.style.gridColumn)).toEqual(colonne)
      expect(carte.map((c) => c.style.height)).toEqual(altezze)
      reso.unmount()
      pulisci()
    }
  })

  it("se l'elenco non arriva, Riprova lo richiede", async () => {
    await apri({ "/api/v1/nights": { stato: 500, corpo: { detail: "x" } } })
    fireEvent.click(await screen.findByRole("button", { name: "Riprova" }))
    await waitFor(() => expect(chieste("limit=20").length).toBeGreaterThan(1))
  })

  it("cambiando criterio la pagina tiene le notti di prima finche' arrivano le nuove", async () => {
    await apri(rotte(TRE, { "filter=Ha": { stato: 200, corpo: TRE, attesa: mai } }))
    await notte()
    await apriCriteri()
    fireEvent.click(opzione("Filtri", "Ha"))
    await waitFor(() => expect(chieste("filter=Ha").length).toBeGreaterThan(0))
    expect(screen.getByRole("region", { name: "La notte" })).toBeTruthy()
    expect(screen.queryByRole("status", { name: "Caricamento…" })).toBeNull()
  })
})

describe("i modi di non avere notti", () => {
  const casi: [string, string, string, string | null, string | null][] = [
    [
      "no_folders",
      "Nessuna cartella scelta",
      "Le notti nascono dai frame delle tue cartelle.",
      "Scegli la cartella",
      "/impostazioni/cartelle",
    ],
    [
      "no_frames",
      "Nessun frame nelle cartelle",
      "Le cartelle scelte non contengono frame FITS o XISF.",
      "Aggiungi cartelle",
      "/impostazioni/cartelle",
    ],
    [
      "no_site",
      "Sito mancante",
      "I frame sono stati letti, ma senza un sito non hanno una notte.",
      "Aggiungi sito",
      "/impostazioni/sito",
    ],
    [
      "waiting",
      "Tutti i frame aspettano una risposta",
      "149 frame: finché manca la risposta non entrano in nessuna notte.",
      "Apri Da confermare",
      "/da-confermare",
    ],
  ]
  for (const [motivo, titoloVuoto, perche, azione, a] of casi) {
    it(`${motivo}: dice perche' e porta dove si rimedia`, async () => {
      const waiting = [
        { answer_at: "review", frames: 37 },
        { answer_at: "site", frames: 112 },
      ]
      await apri(rotte(pagina([], { empty: motivo, waiting })))
      expect(await screen.findByText(titoloVuoto)).toBeTruthy()
      expect(screen.getByText(perche)).toBeTruthy()
      fireEvent.click(screen.getByRole("button", { name: azione as string }))
      expect(await dove()).toBe(a)
    })
  }

  it("reading: la percentuale, e niente da fare", async () => {
    await apri(rotte(pagina([], { empty: "reading", reading_done_pct: 19 })))
    expect(await screen.findByText("Scansione in corso, 19%")).toBeTruthy()
    expect(screen.queryByRole("button")).toBeNull()
  })

  it("reading senza percentuale scrive zero", async () => {
    await apri(rotte(pagina([], { empty: "reading" })))
    expect(await screen.findByText("Scansione in corso, 0%")).toBeTruthy()
  })
})

describe("la protagonista e le sue vicine", () => {
  it("toccare un giorno del calendario la sceglie, e il mese resta", async () => {
    await apri(rotte(TRE))
    fireEvent.click(await giorno(/^17 maggio/))
    expect(await titolo()).toBe("Venerdì 17 maggio 2024")
  })

  it("un giorno con piu' notti sceglie la prima", async () => {
    await apri(rotte(TRE))
    fireEvent.click(await giorno(/^17 maggio/))
    await waitFor(async () => expect(await titolo()).toBe("Venerdì 17 maggio 2024"))
    fireEvent.click(await giorno(/^18 maggio/))
    await waitFor(async () => expect(await titolo()).toBe("Sabato 18 maggio 2024"))
  })

  it("una notte non caricata arriva da sola", async () => {
    await apri(rotte(TRE))
    fireEvent.click(await giorno(/^20 maggio/))
    await waitFor(async () => expect(await titolo()).toBe("Lunedì 20 maggio 2024"))
    expect(chieste("night=99&limit=1").length).toBeGreaterThan(0)
  })

  it("mentre la notte nuova arriva resta quella di prima", async () => {
    await apri(rotte(TRE))
    fireEvent.click(await giorno(/^20 maggio/))
    await waitFor(async () => expect(await titolo()).toBe("Lunedì 20 maggio 2024"))
    fireEvent.click(await giorno(/^23 maggio/))
    await waitFor(() => expect(chieste("night=96").length).toBeGreaterThan(0))
    expect(await titolo()).toBe("Lunedì 20 maggio 2024")
  })

  it("una notte sola che non c'e', o che non risponde, lo dice al posto della protagonista", async () => {
    for (const g of [/^21 maggio/, /^22 maggio/]) {
      const reso = await apri(rotte(TRE))
      fireEvent.click(await giorno(g))
      expect(await screen.findByText("Notte non trovata")).toBeTruthy()
      expect(screen.getByText("I frame sono stati rimossi o spostati.")).toBeTruthy()
      expect(screen.queryByRole("region", { name: "La notte" })).toBeNull()
      reso.unmount()
      pulisci()
    }
  })

  it("una notte caricata non dice mai che manca", async () => {
    await apri(rotte(TRE))
    await notte()
    await calendario()
    expect(screen.queryByText("Notte non trovata")).toBeNull()
  })

  it("dalla striscia il calendario torna al mese della notte", async () => {
    await apri(rotte(TRE))
    fireEvent.click(await screen.findByRole("link", { name: "Mese prima" }))
    await waitFor(async () => expect(await titoloMese()).toBe("Aprile 2024"))
    fireEvent.click(screen.getAllByRole("tab")[1] as HTMLElement)
    await waitFor(async () => expect(await titoloMese()).toBe("Maggio 2024"))
    expect(await titolo()).toBe("Venerdì 17 maggio 2024")
  })

  it("dall'elenco il calendario torna al mese della notte", async () => {
    await apri(rotte(TRE))
    fireEvent.click(await screen.findByRole("link", { name: "Mese prima" }))
    await waitFor(async () => expect(await titoloMese()).toBe("Aprile 2024"))
    const righe = screen
      .getByRole("region", { name: "A confronto" })
      .querySelectorAll<HTMLElement>('[data-an="riga"]')
    fireEvent.click(righe[1] as HTMLElement)
    await waitFor(async () => expect(await titoloMese()).toBe("Maggio 2024"))
  })

  it("dal calendario il mese sfogliato resta, anche mentre la notte arriva", async () => {
    await apri(rotte(TRE))
    fireEvent.click(await screen.findByRole("link", { name: "Mese prima" }))
    fireEvent.click(await giorno(/^5 aprile/))
    await waitFor(() => expect(chieste("night=96").length).toBeGreaterThan(0))
    expect(await titoloMese()).toBe("Aprile 2024")
  })

  it("sul telefono le frecce vanno alla notte prima e dopo, nell'ordine dell'elenco", async () => {
    await apri(rotte(TRE), "/notti?formato=telefono")
    const freccia = async (nome: string) => within(await notte()).getByLabelText(nome)
    expect((await freccia("La notte dopo")).getAttribute("aria-disabled")).toBe("true")
    expect((await freccia("La notte prima")).getAttribute("aria-disabled")).toBeNull()
    fireEvent.click(await freccia("La notte prima"))
    await waitFor(async () => expect(await titolo()).toBe("Venerdì 17 maggio 2024"))
    expect((await freccia("La notte dopo")).getAttribute("aria-disabled")).toBeNull()
    fireEvent.click(await freccia("La notte prima"))
    await waitFor(async () => expect(await titolo()).toBe("Martedì 2 aprile 2024"))
    expect((await freccia("La notte prima")).getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(await freccia("La notte dopo"))
    await waitFor(async () => expect(await titolo()).toBe("Venerdì 17 maggio 2024"))
    fireEvent.click(await freccia("La notte dopo"))
    await waitFor(async () => expect(await titolo()).toBe("Sabato 18 maggio 2024"))
  })

  it("una notte fuori dall'elenco non ha vicine", async () => {
    await apri(rotte(TRE), "/notti?formato=telefono")
    fireEvent.click(await screen.findByRole("link", { name: "Calendario del mese" }))
    // avanti e indietro: il mese resta scritto mentre la notte sola arriva
    fireEvent.click(await screen.findByRole("link", { name: "Mese prima" }))
    await giorno(/^2 aprile/)
    fireEvent.click(await screen.findByRole("link", { name: "Mese dopo" }))
    fireEvent.click(await giorno(/^20 maggio/))
    await waitFor(async () => expect(await titolo()).toBe("Lunedì 20 maggio 2024"))
    const carta = await notte()
    expect(within(carta).getByLabelText("La notte prima").getAttribute("aria-disabled")).toBe(
      "true",
    )
    expect(within(carta).getByLabelText("La notte dopo").getAttribute("aria-disabled")).toBe("true")
  })
})
