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

  it("sul telefono sotto non c'e' niente da promettere: la frase non c'e'", async () => {
    await montaDashboard({ altre: cartelle(0), larga: 390 })

    await avviso("archivio vuoto")
    expect(await screen.findByRole("region", { name: /stanotte a Casa/i })).toBeTruthy()
    expect(screen.queryByRole("region", { name: "progetti, notti, l'anno" })).toBeNull()
  })
})

describe("la Dashboard del telefono senza sito", () => {
  it("non promette l'anno, che sul telefono non c'e'", async () => {
    await montaDashboard({ previsione: { site: null, nights: [], fetched_at: null }, altre: cartelle(0), larga: 390 })

    const sito = await avviso("sito di ripresa")
    const inizio = sito.nodo.closest(".as-dashboard__inizio") as HTMLElement
    expect(inizio.querySelector(".as-dashboard__dopo")?.textContent).toBe(
      "Stanotte, il meteo e i progetti compaiono qui quando il sito e l'archivio ci sono.",
    )
  })
})

/** La prima scansione al lavoro: 1240 file letti su 8310, ne mancano circa 20 minuti. */
function prima(campi: Record<string, unknown> = {}) {
  const evento = { current: 1240, total: 8310, file: "D:/Astro/a.fits", run_id: 1, folder_id: 1, found: 1240, new: 1240, unchanged: 0, duplicates: 0, missing: 0, skipped: 0, errors: 0, online_only: 0 }
  return {
    "/api/v1/pipeline/status": {
      stato: 200,
      corpo: {
        worker: { state: "running", stage: "scan", started_at: "2026-09-25T15:00:00Z", ended_at: null, stages: [] },
        scan: { state: "running", folder_id: 1, run_id: 1, last_event: evento, receipt: null, remaining_s: 1200, first: true, ...campi },
        pending: {},
        action: "stop",
      },
    },
  }
}

describe("la Dashboard durante la prima scansione", () => {
  it("in testa la riga del lavoro: quanti file su quanti, quanto manca, e la pista", async () => {
    await montaDashboard({ altre: prima() })

    const a = await avviso("prima scansione")
    expect(a.classi).toBe("as-avviso as-avviso--lavoro as-avviso--pagina")
    expect(a.testo).toBe(
      "1240 file letti su 8310, ancora circa 20 min. I conteggi qui sotto crescono man mano; medie e casi da confermare arrivano a scansione finita. Non serve fare niente.",
    )
    const pista = within(a.nodo).getByRole("progressbar", { name: "Lettura dell'archivio" })
    expect(pista.getAttribute("aria-valuenow")).toBe("15")
  })

  it("nel primo minuto il tempo che manca tace", async () => {
    await montaDashboard({ altre: prima({ remaining_s: null }) })

    expect((await avviso("prima scansione")).testo).toMatch(/^1240 file letti su 8310\. I conteggi/)
  })

  it("da riprendere dice che i casi si contano alla fine, e l'ultima notte e' quella trovata finora", async () => {
    await montaDashboard({ altre: prima() })

    const lavoro = await screen.findByRole("region", { name: "da riprendere" })
    expect(await within(lavoro).findByText("si contano a scansione finita")).toBeTruthy()
    expect(within(lavoro).queryByRole("link", { name: "Rispondi" })).toBeNull()
    expect((await within(lavoro).findByRole("link", { name: /Sabato 19 settembre/ })).textContent).toContain("la notte pi\u00f9 recente trovata finora")
  })

  it("il vuoto dei progetti dice quanti oggetti la lettura ha trovato finora, senza Crea un progetto", async () => {
    const conOggetti = notti([NOTTE_ARCHIVIO])["/api/v1/nights"]
    await montaDashboard({
      altre: { ...prima(), "/api/v1/nights": { ...conOggetti, corpo: { ...conOggetti.corpo, totals: { ...conOggetti.corpo.totals, objects: 9 } } } },
    })

    const progetti = await screen.findByRole("region", { name: "progetti in corso" })
    expect((await within(progetti).findByText(/^Nessun progetto ancora\./)).textContent).toBe(
      "Nessun progetto ancora. Finora la lettura ha trovato 9 oggetti; un progetto si crea da Progetti anche adesso.",
    )
    expect(within(progetti).queryByRole("link", { name: "Crea un progetto" })).toBeNull()
  })

  it("finche' nessun oggetto e' riconosciuto, il vuoto dei progetti dice che la lettura li sta cercando", async () => {
    await montaDashboard({ altre: prima() })

    const progetti = await screen.findByRole("region", { name: "progetti in corso" })
    expect((await within(progetti).findByText(/^Nessun progetto ancora\./)).textContent).toBe(
      "Nessun progetto ancora. La lettura sta ancora cercando gli oggetti; un progetto si crea da Progetti anche adesso.",
    )
  })

  it("finita la lettura dei file, la frase resta finche' ogni frame non ha la sua notte", async () => {
    const conOggetti = notti([NOTTE_ARCHIVIO])["/api/v1/nights"]
    await montaDashboard({
      altre: {
        ...prima({ state: "completed", last_event: null }),
        "/api/v1/nights": { ...conOggetti, corpo: { ...conOggetti.corpo, still_reading: 90, reading_done_pct: 15, totals: { ...conOggetti.corpo.totals, objects: 1 } } },
      },
    })

    const progetti = await screen.findByRole("region", { name: "progetti in corso" })
    expect((await within(progetti).findByText(/^Nessun progetto ancora\./)).textContent).toContain("ha trovato 1 oggetto;")
  })

  it("i frame fuori dai conti tacciono finche' la prima scansione non finisce", async () => {
    await montaDashboard({ altre: { ...prima(), ...notti([NOTTE_ARCHIVIO], 214) } })

    const lavoro = await screen.findByRole("region", { name: "da riprendere" })
    await within(lavoro).findByText("si contano a scansione finita")
    expect(lavoro.textContent).not.toContain("fuori dai conti")
  })

  it("una scansione che non e' la prima non cambia la pagina", async () => {
    await montaDashboard({ altre: prima({ first: false }) })

    await screen.findByRole("region", { name: "da riprendere" })
    expect(screen.queryByText("prima scansione")).toBeNull()
    expect(await screen.findByText("32 da confermare")).toBeTruthy()
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
