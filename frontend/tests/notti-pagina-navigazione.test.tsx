// @vitest-environment jsdom
/**
 * La pagina **Notti** (`src/Notti.tsx`) montata da sola, come ci si muove: la rilettura mentre la
 * scansione va, la striscia, il calendario, i criteri, Carica altre, le righe di stato, il telefono.
 * Cosa chiede, i vuoti e la protagonista stanno in `notti-pagina.test.tsx`.
 */
import { act, fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { chiamate, pulisci } from "./banco"
import {
  DICIOTTO,
  NOVEMBRE,
  TRE,
  apri,
  apriCriteri,
  calendario,
  cartaDelMese,
  chieste,
  dove,
  giorno,
  mai,
  notte,
  opzione,
  pagina,
  rotte,
  statoTel,
  titolo,
  titoloMese,
  voci,
} from "./notti-banco"

afterEach(() => {
  vi.useRealTimers()
  pulisci()
})

describe("la rilettura mentre la scansione va", () => {
  it("mentre la lettura va, elenco e striscia si rileggono ogni 15 secondi", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    await apri(rotte(pagina([DICIOTTO], { still_reading: 4, reading_done_pct: 10 })))
    await notte()
    const elenco = chieste("limit=20").length
    const striscia = chieste("limit=7").length
    await act(() => vi.advanceTimersByTimeAsync(15100))
    await waitFor(() => expect(chieste("limit=20").length).toBeGreaterThan(elenco))
    expect(chieste("limit=7").length).toBeGreaterThan(striscia)
  })

  it("a lettura finita non si rilegge", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    await apri(rotte(pagina([DICIOTTO])))
    await notte()
    const prima = chiamate().length
    await act(() => vi.advanceTimersByTimeAsync(31000))
    expect(chiamate().length).toBe(prima)
  })
})

describe("la striscia sul desktop", () => {
  it("si chiama Le notti, e ogni notte dice giorno, mese al cambio, esito, ripresa e ore", async () => {
    await apri(rotte(TRE))
    const carta = await screen.findByRole("region", { name: "Le notti" })
    expect(carta.querySelector(".al-notti__testo-1")?.textContent).toBe("Le notti")
    const lista = within(carta).getByRole("tablist", { name: "Le notti" })
    const tab = within(lista).getAllByRole("tab")
    expect(tab.map((x) => x.querySelector(".al-c-striscia__testo-1")?.textContent)).toEqual([
      "sab 18",
      "ven 17",
      "mar 2",
    ])
    expect(tab.map((x) => x.querySelector(".al-c-striscia__testo-2")?.textContent)).toEqual([
      "maggio",
      "",
      "aprile",
    ])
    expect(tab.map((x) => x.querySelector(".al-c-striscia__testo-3")?.textContent)).toEqual([
      "3 h",
      "senza durata",
      "10 min",
    ])
    expect(tab.map((x) => x.querySelector(".al-c-striscia__testo-4")?.textContent)).toEqual([
      "Cima Ekar",
      "Casa",
      "Casa",
    ])
    expect(tab.map((x) => x.getAttribute("aria-selected"))).toEqual(["true", "false", "false"])
    expect(tab[0]?.querySelector(".al-pillola")?.className).toContain("al-pillola--buona")
    expect(tab[1]?.querySelector(".al-pillola")?.className).toContain("al-pillola--mancante")
    expect(tab[1]?.querySelector(".al-pillola")?.textContent).toContain("senza fuso")
    expect(
      within(tab[0] as HTMLElement).getByRole("img", { name: "Ripresa: 3 h 30 di banda larga" }),
    ).toBeTruthy()
    expect(within(tab[1] as HTMLElement).queryByRole("img", { name: /^Ripresa/ })).toBeNull()
  })

  it("toccarne una la sceglie", async () => {
    await apri(rotte(TRE))
    await screen.findByRole("region", { name: "Le notti" })
    fireEvent.click(screen.getAllByRole("tab")[2] as HTMLElement)
    expect(await titolo()).toBe("Martedì 2 aprile 2024")
    expect(screen.getAllByRole("tab").map((x) => x.getAttribute("aria-selected"))).toEqual([
      "false",
      "false",
      "true",
    ])
  })

  it("con piu' di sette notti in archivio dice che sono le ultime sette", async () => {
    const quante = (n: number) =>
      pagina([DICIOTTO], {
        totals: { nights: n, frames: 1, integration_s: 3600, untimed: 0, objects: 1 },
      })
    const sotto = async () =>
      (await screen.findByRole("region", { name: "Le notti" })).querySelector(".al-notti__testo-2")
        ?.textContent
    let reso = await apri(rotte(quante(8)))
    expect(await sotto()).toBe("le ultime 7 · le altre dal calendario e sotto")
    reso.unmount()
    pulisci()
    reso = await apri(rotte(quante(7)))
    expect(await sotto()).toBe("dalla più recente · le altre dal calendario e sotto")
    reso.unmount()
    pulisci()
    await apri(rotte(pagina([DICIOTTO], { totals: null })))
    expect(await sotto()).toBe("dalla più recente · le altre dal calendario e sotto")
    expect(screen.queryByRole("region", { name: "Tutto l’archivio" })).toBeNull()
  })
})

describe("il calendario del mese", () => {
  it("il mese col suo nome, le ore, il conto, e le frecce accese", async () => {
    await apri(rotte(TRE))
    const cal = await calendario()
    expect(await titoloMese()).toBe("Maggio 2024")
    expect(cal.querySelector(".al-c-calendario-notti__testo-2")?.textContent).toBe(
      "2 notti · 3 h 10",
    )
    expect(cal.querySelector(".al-c-calendario-notti__testo-3")?.textContent).toBe("3 h 10")
    expect(cal.querySelector(".al-c-calendario-notti__testo-4")?.textContent).toBe("a maggio")
    expect(cal.querySelector(".al-c-calendario-notti__testo-5")?.textContent).toBe(
      "2 notti · 1 buona",
    )
    expect(
      within(cal).getByRole("link", { name: "Mese prima" }).getAttribute("aria-disabled"),
    ).toBeNull()
    expect(
      within(cal).getByRole("link", { name: "Mese dopo" }).getAttribute("aria-disabled"),
    ).toBeNull()
  })

  it("ogni giorno dice le sue notti coi segni, e quello della protagonista e' premuto", async () => {
    await apri(rotte(TRE))
    const diciotto = await giorno(/^18 maggio/)
    expect(diciotto.getAttribute("aria-label")).toBe(
      "18 maggio, 2 notti: Cima Ekar buona, Rifugio senza meteo",
    )
    expect(diciotto.querySelector(".al-c-calendario-notti__blocco-2")?.textContent).toBe("✓?")
    expect(diciotto.getAttribute("aria-pressed")).toBe("true")
    const diciassette = await giorno(/^17 maggio/)
    expect(diciassette.getAttribute("aria-label")).toBe("17 maggio, una notte: Casa senza meteo")
    expect(diciassette.getAttribute("aria-pressed")).toBe("false")
  })

  it("le frecce chiedono il mese prima e quello dopo", async () => {
    await apri(rotte(TRE))
    fireEvent.click(await screen.findByRole("link", { name: "Mese dopo" }))
    await waitFor(async () => expect(await titoloMese()).toBe("Giugno 2024"))
    expect(chiamate().some((u) => u.endsWith("calendar?month=2024-06"))).toBe(true)
    const cal = await calendario()
    expect(cal.querySelector(".al-c-calendario-notti__testo-3")?.textContent).toBe("nessuna ora")
    expect(cal.querySelector(".al-c-calendario-notti__testo-5")?.textContent).toBe("nessuna notte")
    fireEvent.click(within(cal).getByRole("link", { name: "Mese prima" }))
    fireEvent.click(await screen.findByRole("link", { name: "Mese prima" }))
    await waitFor(async () => expect(await titoloMese()).toBe("Aprile 2024"))
    expect(chiamate().some((u) => u.endsWith("calendar?month=2024-04"))).toBe(true)
  })

  it("al primo mese dell'archivio la freccia indietro e' spenta", async () => {
    await apri(rotte(TRE))
    fireEvent.click(await screen.findByRole("link", { name: "Mese prima" }))
    await waitFor(async () => expect(await titoloMese()).toBe("Aprile 2024"))
    const cal = await calendario()
    expect(
      within(cal).getByRole("link", { name: "Mese prima" }).getAttribute("aria-disabled"),
    ).toBe("true")
    expect(
      within(cal).getByRole("link", { name: "Mese dopo" }).getAttribute("aria-disabled"),
    ).toBeNull()
  })

  it("all'ultimo mese la freccia avanti e' spenta, e oggi si segna", async () => {
    await apri({
      "/api/v1/nights/calendar": { stato: 200, corpo: NOVEMBRE },
      "/api/v1/nights": { stato: 200, corpo: TRE },
    })
    const cal = await calendario()
    expect(await titoloMese()).toBe("Novembre 2026")
    expect(within(cal).getByRole("link", { name: "Mese dopo" }).getAttribute("aria-disabled")).toBe(
      "true",
    )
    expect(
      within(cal).getByRole("link", { name: "Mese prima" }).getAttribute("aria-disabled"),
    ).toBe("true")
    expect(within(cal).getByText("7 novembre, oggi")).toBeTruthy()
  })

  it("fuori dal mese di stanotte non c'e' oggi", async () => {
    await apri(rotte(TRE))
    expect((await calendario()).querySelector(".al-solo-voce")).toBeNull()
  })

  it("un mese che non arriva non mostra un calendario vuoto", async () => {
    await apri({
      "/api/v1/nights/calendar": { stato: 500, corpo: { detail: "x" } },
      "/api/v1/nights": { stato: 200, corpo: TRE },
    })
    const carta = await cartaDelMese()
    await waitFor(() => expect(chieste("calendar").length).toBeGreaterThan(0))
    expect(carta.querySelector(".al-c-calendario-notti__testo-1")).toBeNull()
  })
})

describe("i criteri sul desktop", () => {
  it("chiusi: dodici colonne, nessuno attivo, Apri", async () => {
    await apri(rotte(TRE))
    const carta = await screen.findByRole("region", { name: "Criteri delle notti" })
    expect(carta.style.gridColumn).toBe("span 12")
    expect(carta.querySelector(".al-notti__testo-1")?.textContent).toBe("Criteri")
    expect(carta.querySelector(".al-notti__riga-13 .al-notti__testo-2")?.textContent).toBe(
      "nessuno attivo · oggetto, anno, sito, setup, filtri, costellazione, cielo",
    )
    const apriTasto = within(carta).getByRole("link", { name: "Apri" })
    expect(apriTasto.getAttribute("aria-expanded")).toBe("false")
    expect(apriTasto.querySelector(".al-notti__testo-8")?.textContent).toBe("▾")
    expect(screen.queryByPlaceholderText("per esempio M 31 o Velo")).toBeNull()
    expect(screen.getByRole("region", { name: "A confronto" }).style.gridColumn).toBe("span 12")
  })

  it("aperti: tre colonne, Chiudi, il campo e i gruppi coi loro nomi", async () => {
    await apri(rotte(TRE))
    const carta = await apriCriteri()
    expect(carta.style.gridColumn).toBe("span 3")
    const chiudi = within(carta).getByRole("link", { name: "Chiudi" })
    expect(chiudi.getAttribute("aria-expanded")).toBe("true")
    expect(chiudi.querySelector(".al-notti__testo-8")?.textContent).toBe("▴")
    expect(screen.getByPlaceholderText("per esempio M 31 o Velo")).toBeTruthy()
    expect(screen.getByRole("region", { name: "A confronto" }).style.gridColumn).toBe("span 9")
    expect(
      within(carta)
        .getAllByRole("group")
        .map((g) => g.getAttribute("aria-label")),
    ).toEqual(expect.arrayContaining(["Anno", "Sito", "Setup", "Filtri", "Costellazione", "Cielo"]))
    fireEvent.click(chiudi)
    expect(within(carta).getByRole("link", { name: "Apri" })).toBeTruthy()
  })

  it("ogni scelta si chiama come si legge, col numero delle notti", async () => {
    await apri(rotte(TRE))
    await apriCriteri()
    expect(voci("Anno")).toEqual(["20243"])
    expect(voci("Sito")).toEqual(["Casa2", "Cima Ekar1"])
    expect(voci("Setup")).toEqual(["Il piccolo1", "RedCat 51 + ASI 26001", "ASI 5331", "s41"])
    expect(voci("Filtri")).toEqual(["Ha1", "OIII0", "Strano1", "Filtro non indicato2"])
    expect(voci("Costellazione")).toEqual(["Canes Venatici1"])
    expect(voci("Cielo")).toEqual(["buona1", "incerta1", "non adatta1", "senza meteo2", "nuovo0"])
  })

  it("il pallino del filtro prende il colore della sua banda; gli altri criteri non ne hanno", async () => {
    await apri(rotte(TRE))
    await apriCriteri()
    expect(
      opzione("Filtri", "Ha").querySelector<HTMLElement>(".al-scelta__tinta")?.style.background,
    ).toBe("var(--filtro-ha)")
    expect(
      opzione("Filtri", "OIII").querySelector<HTMLElement>(".al-scelta__tinta")?.style.background,
    ).toBe("var(--filtro-oiii)")
    expect(opzione("Filtri", "Strano").querySelector(".al-scelta__tinta")).toBeNull()
    expect(opzione("Filtri", "Filtro non indicato").querySelector(".al-scelta__tinta")).toBeNull()
    expect(opzione("Sito", "Casa").querySelector(".al-scelta__tinta")).toBeNull()
  })

  it("una scelta senza notti e' spenta, se non e' gia' scelta", async () => {
    await apri(rotte(TRE))
    await apriCriteri()
    expect(opzione("Filtri", "OIII").getAttribute("aria-disabled")).toBe("true")
    expect(opzione("Filtri", "Ha").getAttribute("aria-disabled")).toBeNull()
    expect(opzione("Cielo", "nuovo").getAttribute("aria-pressed")).toBe("true")
  })

  it("una scelta si aggiunge alla richiesta, due dello stesso gruppo si sommano, ritoccata si toglie", async () => {
    await apri(rotte(TRE))
    const carta = await apriCriteri()
    fireEvent.click(opzione("Sito", "Casa"))
    await waitFor(() =>
      expect(chiamate().some((u) => u.endsWith("nights?limit=20&offset=0&site=1"))).toBe(true),
    )
    expect(carta.querySelector(".al-notti__riga-13 .al-notti__testo-2")?.textContent).toBe(
      "1 attivo · 3 notti",
    )
    fireEvent.click(opzione("Sito", "Cima Ekar"))
    await waitFor(() =>
      expect(chiamate().some((u) => u.endsWith("nights?limit=20&offset=0&site=1&site=2"))).toBe(
        true,
      ),
    )
    expect(carta.querySelector(".al-notti__riga-13 .al-notti__testo-2")?.textContent).toBe(
      "2 attivi · 3 notti",
    )
    fireEvent.click(opzione("Anno", "2024"))
    await waitFor(() =>
      expect(chiamate().some((u) => u.endsWith("site=1&site=2&year=2024"))).toBe(true),
    )
    expect(carta.querySelector(".al-notti__riga-13 .al-notti__testo-2")?.textContent).toBe(
      "3 attivi · 3 notti",
    )
    fireEvent.click(opzione("Sito", "Casa"))
    await waitFor(() =>
      expect(chiamate().some((u) => u.endsWith("nights?limit=20&offset=0&site=2&year=2024"))).toBe(
        true,
      ),
    )
    expect(chiamate().some((u) => u.includes("Stryker"))).toBe(false)
  })

  it("coi criteri l'elenco dice quante notti restano", async () => {
    await apri(rotte(TRE))
    const confronto = await screen.findByRole("region", { name: "A confronto" })
    expect(confronto.querySelector(".al-notti__riga-15 .al-notti__testo-2")?.textContent).toBe(
      "oggetti, filtri e cielo, notte per notte",
    )
    await apriCriteri()
    fireEvent.click(opzione("Sito", "Casa"))
    await waitFor(() =>
      expect(confronto.querySelector(".al-notti__riga-15 .al-notti__testo-2")?.textContent).toBe(
        "3 notti con questi criteri",
      ),
    )
    expect(confronto.querySelector(".al-notti__testo-16")?.textContent).toBe("3 di 3")
  })

  it("la ricerca si manda senza spazi ai bordi, e solo spazi non e' un criterio", async () => {
    await apri(rotte(TRE))
    const carta = await apriCriteri()
    const campo = screen.getByPlaceholderText("per esempio M 31 o Velo")
    fireEvent.change(campo, { target: { value: "   " } })
    expect(carta.querySelector(".al-notti__riga-13 .al-notti__testo-2")?.textContent).toMatch(
      /^nessuno attivo/,
    )
    expect(chiamate().some((u) => u.includes("q="))).toBe(false)
    fireEvent.change(campo, { target: { value: " M 31 " } })
    await waitFor(() => expect(chiamate().some((u) => u.endsWith("offset=0&q=M%2031"))).toBe(true))
    expect(carta.querySelector(".al-notti__riga-13 .al-notti__testo-2")?.textContent).toBe(
      "1 attivo · 3 notti",
    )
  })

  it("Togli i criteri toglie le scelte e la ricerca", async () => {
    await apri(rotte(TRE))
    const carta = await apriCriteri()
    fireEvent.change(screen.getByPlaceholderText("per esempio M 31 o Velo"), {
      target: { value: "M 31" },
    })
    fireEvent.click(opzione("Sito", "Casa"))
    await waitFor(() =>
      expect(carta.querySelector(".al-notti__riga-13 .al-notti__testo-2")?.textContent).toMatch(
        /^2 attivi/,
      ),
    )
    fireEvent.click(within(carta).getAllByText("Togli i criteri")[0] as HTMLElement)
    await waitFor(() =>
      expect(carta.querySelector(".al-notti__riga-13 .al-notti__testo-2")?.textContent).toMatch(
        /^nessuno attivo/,
      ),
    )
    expect((screen.getByPlaceholderText("per esempio M 31 o Velo") as HTMLInputElement).value).toBe(
      "",
    )
    expect(opzione("Sito", "Casa").getAttribute("aria-pressed")).toBe("false")
  })
})

describe("le altre notti dell'elenco", () => {
  it("con tutte caricate non c'e' Carica altre", async () => {
    await apri(rotte(TRE))
    await screen.findByRole("region", { name: "A confronto" })
    expect(screen.queryByText("Carica altre")).toBeNull()
  })

  it("mentre arrivano il bottone dice che carica, e se non arrivano dice Riprova", async () => {
    await apri(
      rotte(pagina([DICIOTTO], { total: 30 }), {
        "offset=1": { stato: 200, corpo: TRE, attesa: mai },
      }),
    )
    fireEvent.click(await screen.findByText("Carica altre"))
    const occupato = await screen.findByText("Carico altre…")
    expect(occupato.getAttribute("aria-busy")).toBe("true")
    expect(occupato.getAttribute("aria-disabled")).toBe("true")
  })

  it("se le altre non arrivano il bottone dice Riprova", async () => {
    await apri(
      rotte(pagina([DICIOTTO], { total: 30 }), {
        "offset=1": { stato: 500, corpo: { detail: "x" } },
      }),
    )
    fireEvent.click(await screen.findByText("Carica altre"))
    const riprova = await screen.findByText("Riprova")
    expect(riprova.getAttribute("aria-busy")).toBe("false")
    expect(screen.getByText(/Le altre notti non sono arrivate/)).toBeTruthy()
  })
})

describe("le righe di stato", () => {
  const ATTESE = {
    waiting: [
      { answer_at: "review", frames: 37 },
      { answer_at: "date", frames: 9 },
      { answer_at: "site", frames: 112 },
    ],
    still_reading: 4,
    reading_done_pct: null,
  }

  it("sul desktop una riga per motivo: sito, risposte, data, lettura, coi loro segni", async () => {
    await apri(rotte(pagina([DICIOTTO], ATTESE)))
    await notte()
    const righe = [...document.querySelectorAll(".al-notti__griglia-1 .al-c-avviso__riga-3")]
    expect(righe.map((r) => r.querySelector(".al-c-avviso__blocco-2")?.textContent)).toEqual([
      "112 frame senza sito",
      "37 frame da confermare",
      "9 frame senza data, fuori da ogni notte: la data la scrivi tu",
      "Scansione in corso, 0%: le notti si aggiungono da sole",
    ])
    expect(righe.map((r) => r.querySelector(".al-c-avviso__tondo-5")?.textContent)).toEqual([
      "!",
      "!",
      "?",
      "?",
    ])
    expect(righe.map((r) => r.querySelector("button")?.textContent ?? null)).toEqual([
      "Apri le Impostazioni",
      "Apri Da confermare",
      null,
      null,
    ])
  })

  it("il bottone di una riga porta dove si risponde", async () => {
    await apri(rotte(pagina([DICIOTTO], ATTESE)))
    fireEvent.click(await screen.findByRole("button", { name: "Apri le Impostazioni" }))
    expect(await dove()).toBe("/impostazioni/sito")
  })

  it("le risposte portano a Da confermare", async () => {
    await apri(rotte(pagina([DICIOTTO], ATTESE)))
    fireEvent.click(await screen.findByRole("button", { name: "Apri Da confermare" }))
    expect(await dove()).toBe("/da-confermare")
  })

  it("senza niente in attesa non ci sono righe", async () => {
    await apri(rotte(pagina([DICIOTTO])))
    await notte()
    expect(document.querySelector(".al-notti__griglia-1")).toBeNull()
  })

  it("le voci fuori da ogni notte contano solo i loro frame", async () => {
    await apri(rotte(pagina([DICIOTTO], ATTESE)))
    const carta = await screen.findByRole("region", { name: "Tutto l’archivio" })
    expect(
      within(carta)
        .getByRole("link", { name: /37 da confermare/ })
        .getAttribute("href"),
    ).toBe("/da-confermare")
    expect(
      within(carta)
        .getByRole("link", { name: /112 senza sito/ })
        .getAttribute("href"),
    ).toBe("/impostazioni/sito")
    expect(within(carta).getByText("9")).toBeTruthy()
  })
})

describe("sul telefono", () => {
  const TEL = "/notti?formato=telefono"

  it("il mese e i criteri sono chiusi; la striscia dice giorno e ore di ogni notte", async () => {
    await apri(rotte(TRE), TEL)
    const mese = await screen.findByRole("link", { name: "Calendario del mese" })
    expect(mese.getAttribute("aria-expanded")).toBe("false")
    expect(mese.style.background).toBe("var(--carta-2)")
    expect(mese.style.color).toBe("var(--testo)")
    expect(mese.querySelector(".al-notti__blocco-10")?.textContent).toBe("Mese · Maggio 2024")
    expect(mese.querySelector(".al-notti__testo-20")?.textContent).toBe("▾")
    expect(screen.queryByRole("region", { name: "Mese e criteri" })).toBeNull()
    const lista = screen.getByRole("tablist", { name: "Le notti" })
    const tab = within(lista).getAllByRole("tab")
    expect(tab.map((x) => x.getAttribute("aria-label"))).toEqual([
      "Sabato 18 maggio 2024, 3 h, Cima Ekar",
      "Venerdì 17 maggio 2024, senza durata, Casa",
      "Martedì 2 aprile 2024, 10 min, Casa",
    ])
    expect(tab.map((x) => x.querySelector(".al-notti__testo-21")?.textContent)).toEqual([
      "3 h",
      "senza durata",
      "10 min",
    ])
    expect(tab.map((x) => x.getAttribute("aria-selected"))).toEqual(["true", "false", "false"])
    expect(tab[0]?.textContent?.startsWith("sab 18")).toBe(true)
    expect(screen.queryByText("← Tutte le notti")).toBeNull()
    expect(document.querySelector(".al-notti__riga-24 > span")?.textContent).toBe(
      "dalla più recente",
    )
  })

  it("una linguetta toccata diventa la protagonista", async () => {
    await apri(rotte(TRE), TEL)
    await notte()
    fireEvent.click(screen.getAllByRole("tab")[1] as HTMLElement)
    await waitFor(async () => expect(await titolo()).toBe("Venerdì 17 maggio 2024"))
    expect(screen.getAllByRole("tab").map((x) => x.getAttribute("aria-selected"))).toEqual([
      "false",
      "true",
      "false",
    ])
  })

  it("il bottone del mese apre il calendario e chiude i criteri; richiuso, il mese torna alla notte", async () => {
    await apri(rotte(TRE), TEL)
    fireEvent.click(await screen.findByRole("link", { name: "Criteri" }))
    expect(await screen.findByPlaceholderText("per esempio M 31 o Velo")).toBeTruthy()
    const mese = screen.getByRole("link", { name: "Calendario del mese" })
    fireEvent.click(mese)
    expect(screen.queryByPlaceholderText("per esempio M 31 o Velo")).toBeNull()
    expect(mese.getAttribute("aria-expanded")).toBe("true")
    expect(mese.style.background).toBe("var(--accento)")
    expect(mese.style.color).toBe("var(--scelta-testo)")
    expect(mese.querySelector(".al-notti__testo-20")?.textContent).toBe("▴")
    const carta = screen.getByRole("region", { name: "Mese e criteri" })
    expect(
      carta.querySelector(".al-notti__colonna-14 .al-c-calendario-notti__testo-1")?.textContent,
    ).toBe("Maggio 2024")
    expect(carta.querySelector(".al-c-calendario-notti__testo-3")).toBeNull()
    expect(mese.querySelector(".al-notti__blocco-10")?.textContent).toBe("Maggio 2024")
    fireEvent.click(within(carta).getByRole("link", { name: "Mese prima" }))
    await waitFor(() =>
      expect(mese.querySelector(".al-notti__blocco-10")?.textContent).toBe("Aprile 2024"),
    )
    fireEvent.click(mese)
    expect(mese.getAttribute("aria-expanded")).toBe("false")
    expect(mese.querySelector(".al-notti__blocco-10")?.textContent).toBe("Mese · Maggio 2024")
    expect(screen.queryByRole("region", { name: "Mese e criteri" })).toBeNull()
  })

  it("i criteri si aprono nella carta, chiudono il mese, e Mostra li richiude", async () => {
    await apri(rotte(TRE), TEL)
    const mese = await screen.findByRole("link", { name: "Calendario del mese" })
    fireEvent.click(mese)
    const criteri = screen.getByRole("link", { name: "Criteri" })
    fireEvent.click(criteri)
    expect(criteri.getAttribute("aria-expanded")).toBe("true")
    expect(mese.getAttribute("aria-expanded")).toBe("false")
    const carta = screen.getByRole("region", { name: "Mese e criteri" })
    expect(carta.querySelector(".al-notti__colonna-14")).toBeNull()
    expect(carta.querySelector(".al-notti__colonna-13")).toBeNull()
    expect(carta.querySelector<HTMLElement>(".al-c-filtri__colonna-1")?.style.padding).toBe(
      "0px 16px",
    )
    fireEvent.click(within(carta).getByText("Mostra 3 notti"))
    expect(screen.queryByRole("region", { name: "Mese e criteri" })).toBeNull()
    expect(criteri.getAttribute("aria-expanded")).toBe("false")
    fireEvent.click(criteri)
    fireEvent.click(criteri)
    expect(screen.queryByRole("region", { name: "Mese e criteri" })).toBeNull()
  })

  it("coi criteri la riga sotto la striscia conta le notti", async () => {
    await apri(rotte(TRE), TEL)
    fireEvent.click(await screen.findByRole("link", { name: "Criteri" }))
    fireEvent.click(opzione("Sito", "Casa"))
    await waitFor(() =>
      expect(document.querySelector(".al-notti__riga-24 > span")?.textContent).toBe(
        "3 notti con questi criteri",
      ),
    )
  })

  it("senza notti coi criteri lo dice nella carta, e Mostra dice nessuna notte", async () => {
    // la striscia non ha criteri: la protagonista resta la sua prima notte
    await apri(rotte(pagina([]), { "limit=7": { stato: 200, corpo: TRE } }), TEL)
    const carta = await screen.findByRole("region", { name: "Mese e criteri" })
    expect(carta.querySelector(".al-notti__colonna-13 .al-notti__testo-23")?.textContent).toBe(
      "Nessuna notte con questi criteri",
    )
    expect(carta.querySelector(".al-notti__colonna-13 .al-notti__testo-2")?.textContent).toBe(
      "Togline uno, o tutti.",
    )
    fireEvent.click(screen.getByRole("link", { name: "Criteri" }))
    expect(
      within(screen.getByRole("region", { name: "Mese e criteri" })).getByText("Nessuna notte"),
    ).toBeTruthy()
  })

  it("una riga di stato sola si legge intera; aperta, porta dove si risponde", async () => {
    await apri(rotte(pagina([DICIOTTO], { waiting: [{ answer_at: "review", frames: 37 }] })), TEL)
    const tasto = await statoTel()
    expect(tasto.textContent).toBe("!37 frame da confermare▾")
    expect(tasto.getAttribute("role")).toBe("button")
    expect(tasto.getAttribute("aria-expanded")).toBe("false")
    const segno = tasto.querySelector<HTMLElement>(".al-notti__testo-22")
    expect(segno?.textContent).toBe("!")
    expect(segno?.style.color).toBe("var(--avviso)")
    expect(tasto.querySelector(".al-notti__testo-8")?.textContent).toBe("▾")
    expect(screen.queryByRole("button", { name: "Apri Da confermare" })).toBeNull()
    fireEvent.click(tasto)
    expect(tasto.getAttribute("aria-expanded")).toBe("true")
    expect(tasto.querySelector(".al-notti__testo-8")?.textContent).toBe("▴")
    fireEvent.click(screen.getByRole("button", { name: "Apri Da confermare" }))
    expect(await dove()).toBe("/da-confermare")
  })

  it("piu' righe di stato si contano; senza punti esclamativi il segno e' una domanda", async () => {
    await apri(
      rotte(
        pagina([DICIOTTO], {
          waiting: [{ answer_at: "date", frames: 9 }],
          still_reading: 2,
          reading_done_pct: 40,
        }),
      ),
      TEL,
    )
    const tasto = await statoTel()
    expect(tasto.textContent).toContain("2 cose da vedere")
    const segno = tasto.querySelector<HTMLElement>(".al-notti__testo-22")
    expect(segno?.textContent).toBe("?")
    expect(segno?.style.color).toBe("var(--testo)")
    fireEvent.click(tasto)
    expect(screen.getByText("Scansione in corso, 40%: le notti si aggiungono da sole")).toBeTruthy()
    fireEvent.click(tasto)
    expect(screen.queryByText("Scansione in corso, 40%: le notti si aggiungono da sole")).toBeNull()
  })

  it("un punto esclamativo fra le righe le fa tutte avviso", async () => {
    await apri(
      rotte(
        pagina([DICIOTTO], {
          waiting: [
            { answer_at: "date", frames: 9 },
            { answer_at: "site", frames: 3 },
          ],
        }),
      ),
      TEL,
    )
    const tasto = await statoTel()
    expect(tasto.textContent).toContain("2 cose da vedere")
    expect(tasto.querySelector(".al-notti__testo-22")?.textContent).toBe("!")
    expect(tasto.querySelector<HTMLElement>(".al-notti__testo-22")?.style.color).toBe(
      "var(--avviso)",
    )
  })

  it("senza righe di stato non c'e' il bottone", async () => {
    await apri(rotte(TRE), TEL)
    await notte()
    expect(document.querySelector(".al-notti__riga-25")).toBeNull()
  })

  it("in fondo c'e' tutto l'archivio, se il backend lo manda", async () => {
    await apri(rotte(TRE), TEL)
    expect(await screen.findByRole("region", { name: "Tutto l’archivio" })).toBeTruthy()
  })

  it("senza i totali non c'e' l'archivio", async () => {
    await apri(rotte(pagina([DICIOTTO], { totals: null })), TEL)
    await notte()
    expect(screen.queryByRole("region", { name: "Tutto l’archivio" })).toBeNull()
  })

  it("una notte dall'indirizzo porta a tutte le notti, senza archivio ne' mese", async () => {
    await apri(rotte(pagina([DICIOTTO])), "/notti?formato=telefono&notte=7")
    expect(await screen.findByText("← Tutte le notti")).toBeTruthy()
    await notte()
    expect(screen.queryByRole("link", { name: "Calendario del mese" })).toBeNull()
    expect(screen.queryByRole("region", { name: "Tutto l’archivio" })).toBeNull()
  })

  it("un giorno del calendario fuori dalle notti caricate tiene il mese mentre la notte arriva", async () => {
    await apri(rotte(TRE), TEL)
    const mese = await screen.findByRole("link", { name: "Calendario del mese" })
    fireEvent.click(mese)
    fireEvent.click(await giorno(/^23 maggio/))
    await waitFor(() => expect(chieste("night=96&limit=1").length).toBe(1))
    expect(mese.querySelector(".al-notti__blocco-10")?.textContent).toBe("Maggio 2024")
  })

  it("senza protagonista ne' mese il bottone dice solo Calendario del mese", async () => {
    await apri(
      rotte(pagina([]), { "limit=7": { stato: 200, corpo: pagina([]), attesa: mai } }),
      TEL,
    )
    const mese = await screen.findByRole("link", { name: "Calendario del mese" })
    expect(mese.querySelector(".al-notti__blocco-10")?.textContent).toBe("Calendario del mese")
  })
})
