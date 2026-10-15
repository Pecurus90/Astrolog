// @vitest-environment jsdom
/**
 * La **Dashboard, gli stati** (`pagine/dashboard-stati*.html` del progetto Design, v37): quando
 * manca il sito, l'archivio o il meteo, in testa alla parte che manca una riga di stato con la
 * parola, la frase e un'azione sola in evidenza; il resto resta cio' che si puo' calcolare.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { pulisci, scritture } from "./banco"
import { NOTTE_ARCHIVIO, STANOTTE_CON_LUNA, cartelle, montaDashboard, notti } from "./dashboard-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

const SENZA_RISPOSTA = { at: "2026-09-25T16:00:00.000Z", status: "unreachable" }

/** L'avviso che porta quel titolo: tono, testo, azione. */
async function avviso(titolo: string) {
  const t = await screen.findByText(titolo, { selector: ".as-avviso__titolo" })
  const a = t.closest(".as-avviso") as HTMLElement
  return {
    nodo: a,
    classi: a.className,
    segno: a.querySelector(".as-avviso__segno")?.textContent ?? "",
    testo: a.querySelector(".as-avviso__testo")?.textContent ?? null,
    azione: a.querySelector(".as-avviso__azioni .as-bottone") as HTMLElement | null,
  }
}

describe("la Dashboard senza sito", () => {
  it("per cominciare, due passi in fila: il sito aperto col primario, l'archivio dopo", async () => {
    await montaDashboard({ previsione: { site: null, nights: [], fetched_at: null }, altre: cartelle(0) })

    const sito = await avviso("sito di ripresa")
    expect(sito.classi).toBe("as-avviso as-avviso--ora as-avviso--pagina")
    expect(sito.segno).toBe("1")
    expect(sito.azione?.textContent).toBe("Scegli il sito")
    expect(sito.azione?.className).toContain("as-bottone--primario")
    expect(sito.azione?.getAttribute("href")).toBe("/impostazioni/sito")
    const archivio = await avviso("archivio")
    expect(archivio.classi).toBe("as-avviso as-avviso--dopo as-avviso--pagina")
    expect(archivio.segno).toBe("2")
    expect(archivio.azione).toBeNull()
    const inizio = sito.nodo.closest(".as-dashboard__inizio") as HTMLElement
    expect(inizio.querySelector(".as-dashboard__inizio-titolo")?.textContent).toBe("Prima il sito, poi l'archivio")
    expect(inizio.querySelector(".as-dashboard__dopo")?.textContent).toMatch(/^Stanotte, il meteo, i progetti e l'anno compaiono qui/)
    expect(screen.queryByRole("region", { name: "da riprendere" })).toBeNull()
  })

  it("con l'archivio gia' scelto il passo resta uno: il sito", async () => {
    await montaDashboard({ previsione: { site: null, nights: [], fetched_at: null } })

    await avviso("sito di ripresa")
    expect(screen.queryByText("archivio", { selector: ".as-avviso__titolo" })).toBeNull()
  })
})

describe("la Dashboard con l'archivio vuoto", () => {
  it("in testa la riga dell'archivio con Scegli la cartella; stanotte c'e' tutta; sotto una frase sola", async () => {
    await montaDashboard({ altre: cartelle(0) })

    const a = await avviso("archivio vuoto")
    expect(a.classi).toBe("as-avviso as-avviso--attesa as-avviso--pagina")
    expect(a.testo).toMatch(/^Scegli la cartella dove tieni i frame\./)
    expect(a.azione?.textContent).toBe("Scegli la cartella")
    expect(a.azione?.className).toContain("as-bottone--primario")
    expect(a.azione?.getAttribute("href")).toBe("/impostazioni/cartelle")
    expect(await screen.findByRole("region", { name: /stanotte a Casa/i })).toBeTruthy()
    const seguito = screen.getByRole("region", { name: "progetti, notti, l'anno" })
    expect(seguito.textContent).toContain("Compaiono qui dopo la prima scansione.")
    expect(screen.queryByRole("region", { name: "progetti in corso" })).toBeNull()
    expect(screen.queryByRole("region", { name: "da riprendere" })).toBeNull()
  })
})

describe("la Dashboard con le cartelle tolte", () => {
  it("un archivio che ha ancora i suoi frame non e' vuoto, anche senza cartelle attive", async () => {
    const conFrame = notti([NOTTE_ARCHIVIO])["/api/v1/nights"]
    await montaDashboard({
      altre: { ...cartelle(0), "/api/v1/nights": { ...conFrame, corpo: { ...conFrame.corpo, totals: { nights: 1, frames: 180, integration_s: 15120, untimed: 0 } } } },
    })

    expect(await screen.findByRole("region", { name: "da riprendere" })).toBeTruthy()
    expect(screen.queryByText("archivio vuoto")).toBeNull()
  })
})

describe("la Dashboard col meteo che non risponde", () => {
  it("in testa il buio calcolato e Non disponibile; al posto di carte e serate l'allarme con Riprova ora", async () => {
    await montaDashboard({ previsione: { last_request: SENZA_RISPOSTA, nights: [] } })

    const stanotte = await screen.findByRole("region", { name: /stanotte a Casa/i })
    expect(stanotte.querySelector(".as-dashboard__grande")?.textContent).toBe("8 h 43 min di buio")
    expect(stanotte.querySelector(".as-semaforo--grande")?.className).toContain("as-semaforo--ignoto")
    const a = await avviso("meteo non raggiungibile")
    expect(a.classi).toBe("as-avviso as-avviso--allarme as-avviso--pagina")
    expect(a.testo).toMatch(/^Nessuna risposta dal .+: la notte e le prossime 3 non si possono dire\. Riprovo da solo ogni 15 minuti\.$/)
    expect(a.azione?.className).toContain("as-bottone--primario")
    expect(stanotte.querySelector(".as-parametro, .as-tel-carta")).toBeNull()
    expect(screen.queryByRole("region", { name: "meteo delle prossime 3 notti" })).toBeNull()
  })

  it("dove stanotte il buio astronomico non arriva lo dice con la parola, non con zero", async () => {
    const luna = STANOTTE_CON_LUNA["/api/v1/tonight"]
    await montaDashboard({
      previsione: { last_request: SENZA_RISPOSTA, nights: [] },
      altre: { "/api/v1/tonight": { ...luna, corpo: { ...luna.corpo, dark_s: 0 } } },
    })

    const stanotte = await screen.findByRole("region", { name: /stanotte a Casa/i })
    expect(await within(stanotte).findByText("Nessuna notte astronomica")).toBeTruthy()
    expect(stanotte.querySelector(".as-dashboard__grande")).toBeNull()
  })

  it("Riprova ora chiede la previsione subito", async () => {
    await montaDashboard({
      previsione: { last_request: SENZA_RISPOSTA, nights: [] },
      altre: { "POST /api/v1/weather/refresh": { stato: 200, corpo: { status: "unreachable" } } },
    })

    const a = await avviso("meteo non raggiungibile")
    fireEvent.click(a.azione as HTMLElement)
    await waitFor(() => expect(scritture().map((s) => s.url)).toContainEqual(expect.stringContaining("/api/v1/weather/refresh")))
  })

  it("con l'archivio vuoto il primario resta all'archivio, e Riprova ora scende a tenue", async () => {
    await montaDashboard({ previsione: { last_request: SENZA_RISPOSTA, nights: [] }, altre: cartelle(0) })

    expect((await avviso("archivio vuoto")).azione?.className).toContain("as-bottone--primario")
    expect((await avviso("meteo non raggiungibile")).azione?.className).toContain("as-bottone--tenue")
  })

  it("una previsione che vale ancora non e' un meteo che non risponde", async () => {
    await montaDashboard({ previsione: { last_request: SENZA_RISPOSTA } })

    const stanotte = await screen.findByRole("region", { name: /stanotte a Casa/i })
    expect(within(stanotte).queryByText("meteo non raggiungibile")).toBeNull()
    expect(stanotte.querySelectorAll(".as-parametro--piccolo")).toHaveLength(6)
  })
})
