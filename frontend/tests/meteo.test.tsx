// @vitest-environment jsdom
/**
 * La pagina **Meteo** nella tavola v82: le prossime notti del sito predefinito, una alla volta.
 *
 * La pagina non decide niente (`docs/domini/meteo.md`): verdetto, giudizi, Ore di posa, ordine
 * delle misure e scale arrivano scritti. Qui si prova che li mostra senza tradirli, che un numero
 * che manca si dice con una parola, e che il modello e il pulsante chiedono al backend invece di
 * rifare conti.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { chiamate, impostazioni, pulisci, scritture } from "./banco"
import {
  NOTTE,
  TENDENZA,
  altreMisure,
  apriMeteo,
  apriMeteoTelefono,
  carta,
  carte,
  comeVa,
  conNotti,
  meteo,
  misura,
  misure,
  nomeDi,
  scheda,
} from "./meteo-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

const DALLE_21 = { since: "2026-09-26T21:00:00+02:00", until: "2026-09-26T23:00:00+02:00", hours: 2 }
const TUTTE = ["cloud", "cloud_low", "condensation", "rain", "visibility", "wind", "seeing", "jet", "aerosol", "gust"]

/** Una notte con ogni carta piena e giudicate solo le misure date: i fattori sono quelle. */
function conFattori(codici: string[], altre: unknown[] = []) {
  const misure = TUTTE.map((c) => misura(c, codici.includes(c) ? { level: "nogo", weighs: true, ...DALLE_21 } : {}))
  return { ...NOTTE, measures: [...misure, ...altre] }
}

/** Le righe degli altri fattori, aperte e dietro «Altri N fattori». */
const righe = () => [...comeVa().querySelectorAll<HTMLElement>(".al-meteo__colonna-7, .al-meteo__colonna-8")]
const nomeRiga = (r: HTMLElement) => r.querySelector(".al-meteo__testo-7")?.textContent

const grafico = () => within(document.body).getByRole("slider", { name: /^Il cielo/ })
const lettore = () => screen.queryByRole("tooltip")
const sulGrafico = (nome: string | RegExp) => within(screen.getByRole("group", { name: "Sul grafico" })).getByRole("checkbox", { name: nome })
const barre = (c: HTMLElement) => [...c.querySelectorAll<HTMLElement>(".al-c-card-meteo__pillola-2")]
const umidita = () => grafico().querySelector('path[stroke="var(--umidita)"]')
// le parole della misura a destra, scritte dove cambiano
const parole = () => [...grafico().querySelectorAll("span")].filter((s) => /^[✓!✕] /.test(s.textContent ?? ""))
const TINTE = ["var(--prot-tenue)", "var(--buono-testo)", "var(--incerto-testo)", "var(--non-adatto-testo)"]
const segmenti = () => [...grafico().querySelectorAll("path")].filter((p) => TINTE.includes(p.getAttribute("stroke") ?? ""))

describe("il Meteo, la notte", () => {
  it("in testa le Ore di posa col semaforo, le bande e l'accordo, e nella fila da che ora a che ora", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    const testo = (await scheda()).textContent ?? ""
    expect(testo).toContain("Ore di posa · notte di sabato 26 · stanotte")
    expect(testo).toContain("3,0 ore")
    expect(testo).toContain("! incerta")
    expect(testo).toContain("tutte in banda larga · 3 modelli d'accordo su 4")
    expect(screen.getAllByRole("tab")[0]?.textContent).toContain("23–02")
  })

  it("gli altri fattori sono le misure giudicate nell'ordine del backend, con la parola e le ore, e in fondo le carte senza numero", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    expect(comeVa().textContent).toContain("9 fattori, i più gravi prima")
    fireEvent.click(within(comeVa()).getByRole("button", { name: "Altri 7 fattori" }))
    expect(righe().map(nomeRiga)).toEqual([
      "Nuvole basse", "Vento", "Raffiche", "Pioggia", "Aerosol", "Visibilità", "Condensa", "Seeing", "Jet stream",
    ])
    const vento = righe()[1] as HTMLElement
    expect(vento.textContent).toContain("non adatta")
    expect(vento.textContent).toContain("dalle 21:00 alle 23:00, 2 ore · 20 km/h media nel buio")
    expect(righe()[7]?.textContent).toContain("serve una chiave")
  })

  it.each([
    [5, "Altri 3 fattori"],
    [3, "Altro fattore"],
  ])("di %i fattori ne mostra due, gli altri dietro «%s» che li apre senza cambiare testo", async (quanti, testo) => {
    conNotti(conFattori(["wind", "rain", "aerosol", "cloud_low", "gust"].slice(0, quanti)))
    await apriMeteo()
    await scheda()

    expect(righe()).toHaveLength(2)
    const altri = within(comeVa()).getByRole("button", { name: testo })
    expect(altri.getAttribute("aria-expanded")).toBe("false")
    fireEvent.click(altri)
    expect(righe()).toHaveLength(quanti)
    expect(altri.getAttribute("aria-expanded")).toBe("true")
    expect(within(comeVa()).getByRole("button", { name: testo })).toBe(altri)
  })

  it("con due fattori soli non c'e' niente da aprire", async () => {
    conNotti(conFattori(["wind", "rain"]))
    await apriMeteo()
    await scheda()

    expect(righe()).toHaveLength(2)
    expect(within(comeVa()).queryByRole("button", { name: /^Altr/ })).toBeNull()
  })

  it("la frase sopra il grafico dice il gesto che c'e': passare col mouse, toccare col dito", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    expect((await scheda()).textContent).toContain("Passa sul grafico per vedere un'ora · frecce per spostarti, Esc per tornare alla notte")
  })

  it("dove non c'e' un mouse la frase dice di toccare il grafico o le barrette", async () => {
    vi.stubGlobal("matchMedia", (q: string) => ({ matches: q === "(hover: none)" }))
    conNotti(NOTTE)
    await apriMeteo()
    expect((await scheda()).textContent).toContain("Tocca il grafico o le barrette per vedere un'ora")
  })

  it("se non pesa niente lo dice", async () => {
    conNotti(conFattori([]))
    await apriMeteo()
    await scheda()

    expect(comeVa().textContent).toContain("Nessun altro fattore.")
  })

  it.each([
    ["nogo", false, true, "consigliata banda stretta", "al 55% dalle 23:00 · banda larga fino alle 23:00"],
    ["marginal", false, true, "banda larga al limite", "al 55% dalle 23:00 · senza Luna fino alle 23:00"],
    ["nogo", true, true, "consigliata banda stretta", "al 55% tutta la notte"],
    ["nogo", true, false, "consigliata banda stretta", "al 55% fino alle 02:00 · banda larga dalle 02:00"],
    ["marginal", true, false, "banda larga al limite", "al 55% fino alle 02:00 · senza Luna dalle 02:00"],
    ["nogo", false, false, "consigliata banda stretta", "al 55% dalle 23:00 alle 02:00 · banda larga prima e dopo"],
  ])("la Luna %s (dall'inizio %s, fino in fondo %s) consiglia la banda e dice le ore senza Luna", async (level, daSubito, finoInFondo, parola, frase) => {
    const luna = misura("moon", {
      level, weighs: true, value: 55, known_from_start: daSubito, known_to_end: finoInFondo,
      known_since: "2026-09-26T23:00:00+02:00", known_until: "2026-09-27T02:00:00+02:00",
    })
    conNotti(conFattori([], [luna]))
    await apriMeteo()
    await scheda()

    expect(righe()).toHaveLength(1)
    const riga = righe()[0] as HTMLElement
    expect(nomeRiga(riga)).toBe("Luna")
    expect(riga.textContent).toContain(parola)
    expect(riga.querySelector(".al-meteo__testo-2")?.textContent).toBe(frase)
  })

  it("la fila dice il giorno, il semaforo e le Ore di posa di ogni notte, e ne apre una alla volta", async () => {
    conNotti(NOTTE, TENDENZA)
    await apriMeteo()

    const voci = await screen.findAllByRole("tab")
    expect(voci[0]?.textContent).toContain("sab 26")
    expect(voci[0]?.textContent).toContain("incerta")
    expect(voci[0]?.textContent).toContain("3,0 ore23–02")
    expect(voci[0]?.getAttribute("aria-selected")).toBe("true")
    expect(voci[1]?.textContent).toContain("8 ore di buio")
    expect(screen.getAllByRole("region", { name: "La notte" })).toHaveLength(1)
  })

  it("dalla quarta notte mostra la tendenza, senza ore serene ne' carte, e lo dice", async () => {
    conNotti(NOTTE, TENDENZA)
    await apriMeteo()

    fireEvent.click((await screen.findAllByRole("tab"))[1] as HTMLElement)
    const tendenza = await scheda()
    expect(tendenza.textContent).toMatch(/Buio · notte di \S+ 29 · tendenza/)
    expect(tendenza.textContent).toContain("8 ore")
    expect(tendenza.textContent).toContain("Nuvole sparse nel buio, 40%")
    expect(tendenza.textContent).toContain("2 modelli d'accordo su 4")
    expect(tendenza.textContent).toContain("Dalla quarta notte la previsione è una tendenza")
    expect(comeVa().textContent).toContain("Per le notti di tendenza non ci sono le misure ora per ora")
    expect(screen.queryByRole("region", { name: "Le misure" })).toBeNull()
  })

  it("dove il buio non arriva conta le ore col Sole sotto l'orizzonte, e dove il Sole non tramonta non da' un verdetto finto", async () => {
    conNotti({ ...NOTTE, window: "sun_down" })
    await apriMeteo()
    expect((await scheda()).textContent).toContain("Ore di posa col Sole sotto l'orizzonte · notte di sabato 26")
    pulisci()

    conNotti({ ...NOTTE, window: "nautical" })
    await apriMeteo()
    expect((await scheda()).textContent).toContain("Ore di posa nel buio nautico · notte di sabato 26")
    pulisci()

    conNotti({ ...NOTTE, verdict: null, usable_hours: null, usable_since: null, usable_until: null, window: null, window_hours: 0 })
    await apriMeteo()
    const polo = await scheda()
    expect(polo.querySelector(".al-meteo__testo-4")?.textContent).toBe("Nessun buio")
    expect(polo.textContent).toContain("Il Sole non tramonta: nessuna ora di buio.")
    expect(polo.querySelector(".al-meteo__pillola-1")).toBeNull()
    expect(screen.queryByRole("region", { name: "Le misure" })).toBeNull()
  })

  it("senza le nuvole di tutte le ore il verdetto non si sa, e non si inventa", async () => {
    conNotti({ ...NOTTE, verdict: null })
    await apriMeteo()

    const notte = await scheda()
    expect(notte.querySelector(".al-meteo__testo-4")?.textContent).toBe("Non disponibile")
    expect(notte.querySelector(".al-meteo__pillola-1")).toBeNull()
  })
})

describe("il Meteo, le carte", () => {
  it("stanno sempre allo stesso posto, prima le grandi e poi le piccole, qualunque ordine mandi il backend", async () => {
    conNotti({ ...NOTTE, measures: [...NOTTE.measures].reverse() })
    await apriMeteo()
    await scheda()

    expect(carte().map(nomeDi)).toEqual(["Nuvole", "Nuvole basse", "Pioggia", "Visibilità", "Vento", "Seeing", "Aerosol"])
    const altre = [...altreMisure().querySelectorAll(".al-meteo__testo-16")].map((e) => e.textContent)
    expect(altre).toEqual(["Temperatura e punto di rugiada", "Polveri", "Vento a 700 hPa"])
  })

  it("una carta dice il valore, cosa vuol dire, la parola della notte con le sue ore e il picco", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    const vento = carta(/^Vento$/)
    expect(vento.querySelector(".al-c-card-meteo__testo-2")?.textContent).toBe("20")
    expect(vento.textContent).toContain("media nel buio · a 10 m")
    expect(vento.textContent).toContain("non adatta dalle 21:00 alle 23:00, 2 ore")
    expect(vento.textContent).toContain("raffiche fino a 35 km/h tra le 22:00 e le 23:00")
  })

  it("un'ora che il servizio non da' si disegna a tratteggio, mai come uno zero", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    const tratteggiate = barre(carta(/^Vento$/)).filter((b) => b.style.background.startsWith("repeating-linear-gradient"))
    expect(tratteggiate).toHaveLength(1)
    expect(tratteggiate[0]?.style.height).toBe("100%")
  })

  it("le barre prendono il colore del giudizio di ogni ora, e le ore non disegnate restano fuori", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    // l'ora di mezzogiorno non e' fra quelle da disegnare; quella delle 19 e' fuori dal buio
    expect(barre(carta(/^Nuvole$/)).map((b) => b.style.background)).toEqual([
      "var(--barretta-spenta)", "var(--buono-testo)", "var(--buono-testo)",
    ])
  })

  it("la pioggia che non c'e' lo dice, invece di un picco a zero", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    expect(carta(/^Pioggia$/).textContent).toContain("nessuna ora con pioggia")
  })

  it("senza nessuna ora data, pioggia e condensa non dicono che non ce n'e'", async () => {
    const muta = { level: null, value: null, peak: null, known_hours: 0 }
    conNotti({
      ...NOTTE,
      measures: [...NOTTE.measures.filter((m) => m.code !== "rain"), misura("rain", muta), misura("condensation", muta)],
    })
    await apriMeteo()
    await scheda()

    expect(carta(/^Pioggia$/).textContent).not.toContain("nessuna ora con pioggia")
    expect(carta(/^Condensa$/).textContent).not.toContain("mai sotto")
  })

  it("una linea si spezza dove il servizio non da' il valore, invece di unire i due lati", async () => {
    conNotti({ ...NOTTE, hours: NOTTE.hours.map((o, i) => ({ ...o, humidity_pct: i === 2 ? null : 60 })) })
    await apriMeteo()
    await scheda()

    fireEvent.click(sulGrafico("umidità %"))
    expect(umidita()?.getAttribute("d")?.match(/M/g)).toHaveLength(2)
  })

  it("la visibilit\u00e0 dice la minima nel buio in km e che non c'e' nebbia", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    const visibilita = carta(/^Visibilit/)
    expect(visibilita.textContent).toContain("12km")
    expect(visibilita.textContent).toContain("minima nel buio")
    expect(visibilita.textContent).toContain("buona tutta la notte")
    expect(visibilita.textContent).toContain("nessuna ora di nebbia")
  })

  it("con la nebbia la carta dice da che ora, e sotto 10 km il valore porta un decimale", async () => {
    const nebbia = misura("visibility", {
      level: "nogo", weighs: true, value: 0.8, peak: 0.8, axis_max: 12, hours: 1,
      since: "2026-09-26T22:00:00+02:00", until: "2026-09-26T23:00:00+02:00",
      spans: [{ level: "nogo", since: "2026-09-26T22:00:00+02:00", until: "2026-09-26T23:00:00+02:00", hours: 1 }],
    })
    conNotti({ ...NOTTE, measures: [...NOTTE.measures.filter((m) => m.code !== "visibility").map((m) => ({ ...m, weighs: false })), nebbia] })
    await apriMeteo()
    await scheda()

    const visibilita = carta(/^Visibilit/)
    expect(visibilita.textContent).toContain("0,8km")
    expect(visibilita.textContent).toContain("non adatta dalle 22:00")
    expect(visibilita.textContent).toContain("nebbia dalle 22:00")
    fireEvent.click(within(comeVa()).getByRole("button", { name: /^Altri/ }))
    expect(righe().find((r) => nomeRiga(r) === "Visibilità")?.textContent).toContain("dalle 22:00 alle 23:00, 1 ora")
  })

  it("la condensa incerta dice da che ora l'aria scende sotto la soglia di quell'ora: la parola la decide il backend", async () => {
    const umida = misura("condensation", {
      level: "marginal", weighs: true, value: 2, peak: 2, hours: 1,
      since: "2026-09-26T22:00:00+02:00", until: "2026-09-26T23:00:00+02:00",
      spans: [{ level: "marginal", since: "2026-09-26T22:00:00+02:00", until: "2026-09-26T23:00:00+02:00", hours: 1 }],
    })
    conNotti({
      ...NOTTE,
      hours: NOTTE.hours.map((o) => ({ ...o, dew_threshold_c: o.at === "2026-09-26T22:00:00+02:00" ? 4.9 : 3.2 })),
      measures: [...NOTTE.measures.filter((m) => m.code !== "condensation"), umida],
    })
    await apriMeteo()
    await scheda()

    expect(carta(/^Condensa/).textContent).toContain("sotto la soglia di 4,9 \u00b0C dalle 22:00")
  })

  it("scelta la condensa a destra, la soglia di ogni ora e' una linea tratteggiata con la sua voce in legenda", async () => {
    const secca = misura("condensation", { level: "go", value: 6, peak: 6, known_hours: 3 })
    conNotti({
      ...NOTTE,
      hours: NOTTE.hours.map((o) => ({ ...o, dew_spread_c: 6, dew_threshold_c: 4.9 })),
      measures: [...NOTTE.measures.filter((m) => m.code !== "condensation"), secca],
    })
    await apriMeteo()
    await scheda()
    const soglia = () => grafico().querySelectorAll("path[stroke-dasharray='5 4']")
    expect(soglia()).toHaveLength(0)
    fireEvent.click(sulGrafico(/^condensa/i))

    await waitFor(() => expect(soglia()).toHaveLength(1))
    expect(screen.getAllByText("Soglia di rugiada").length).toBeGreaterThan(0)
  })

  it("la carta della visibilit\u00e0 cresce con la radice: 41 km non escono dalla carta e 5 km stanno a meta' dell'altezza utile", async () => {
    const limpida = misura("visibility", { level: "go", value: 41, peak: 41, axis_max: 20, axis_curve: "sqrt" })
    conNotti({
      ...NOTTE,
      hours: NOTTE.hours.map((o, i) => ({ ...o, visibility_km: i === 2 ? 5 : 41 })),
      measures: [...NOTTE.measures.filter((m) => m.code !== "visibility"), limpida],
    })
    await apriMeteo()
    await scheda()

    // a bar is 25% at zero and 100% at the top: sqrt(5/20) is half of the 75 above the floor
    expect(barre(carta(/^Visibilit/)).map((b) => parseFloat(b.style.height))).toEqual([100, 62.5, 100])
  })

  it("la visibilit\u00e0 si sceglie sulla scala di destra del cielo", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    expect(sulGrafico("visibilità").getAttribute("title")).toBe("una alla volta, sulla scala di destra")
  })

  it("le carte doppie non ci sono pi\u00f9: n\u00e9 l'umidit\u00e0 n\u00e9 il vento a 200 hPa", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    const nomi = [...carte().map(nomeDi), altreMisure().textContent ?? ""].join(" ")
    expect(nomi).not.toMatch(/umidit/i)
    expect(nomi).not.toContain("200 hPa")
  })

  it("la temperatura dice la minima e la rugiada accanto", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    expect(altreMisure().textContent).toContain("minima nel buio \u00b7 punto di rugiada 4 \u00b0C")
  })

  it.each([
    [8, "meno vento in 8 notti su 10 dell'ultimo anno, in questo sito"],
    [0, "fra i pi\u00f9 deboli dell'anno in questo sito"],
    [1, "meno vento in 1 notte su 10 dell'ultimo anno, in questo sito"],
    [10, "fra i pi\u00f9 forti dell'anno in questo sito"],
    [null, "confronto con lo storico non ancora disponibile"],
  ])("il vento a 700 hPa si legge accanto al solito del sito (%s)", async (decimi, frase) => {
    conNotti({ ...NOTTE, wind_700hpa_tenths: decimi })
    await apriMeteo()
    await scheda()

    expect(altreMisure().textContent).toContain(frase)
  })
})

describe("il Meteo, il seeing", () => {
  const titolo = () => carta(/^Seeing$/).querySelector(".al-c-card-meteo__testo-4")?.textContent
  const sotto = () => carta(/^Seeing$/).querySelector(".al-c-card-meteo__testo-5")?.textContent ?? null
  const stimata = {
    ...NOTTE,
    measures: NOTTE.measures.map((m) => (m.code === "seeing" ? misura("seeing", { level: "nogo", known_hours: 0, estimated_from: "jet" }) : m)),
  }

  it("senza chiave la carta dice che serve una chiave Meteoblue, e porta alle Impostazioni", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    expect(titolo()).toBe("Il seeing richiede una chiave Meteoblue.")
    const porta = within(carta(/^Seeing$/)).getByRole("link", { name: /apri le impostazioni/i })
    expect(porta.getAttribute("href")).toBe("/impostazioni/servizi")
  })

  it("senza il numero, un jet forte fa dire alla carta seeing scarso, come stima, e la chiave resta", async () => {
    conNotti(stimata)
    await apriMeteo()
    await scheda()

    expect(titolo()).toBe("Seeing scarso · stima dal vento in quota")
    expect(sotto()).toBe("Con una chiave Meteoblue, il numero in secondi d'arco.")
    expect(carta(/^Seeing$/).textContent).toContain("scarso · stima dal vento in quota")
    expect(within(carta(/^Seeing$/)).getByRole("link", { name: /apri le impostazioni/i })).toBeTruthy()
  })

  it("con la chiave buona ma senza il numero, la stima dal jet resta e non chiede una chiave", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [stimata], seeing: { key: true, source: "meteoblue", meteoblue: "ok" } })
    await apriMeteo()
    await scheda()

    expect(titolo()).toBe("Seeing scarso · stima dal vento in quota")
    expect(sotto()).toBeNull()
    expect(within(carta(/^Seeing$/)).queryByRole("link")).toBeNull()
  })

  it("se Meteoblue non accetta la chiave la carta lo dice con un allarme", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: null, meteoblue: "refused" } })
    await apriMeteo()
    await scheda()

    expect(titolo()).toBe("Chiave Meteoblue non valida o scaduta.")
    expect(carta(/^Seeing$/).querySelector(".al-c-card-meteo__tondo-4")?.textContent).toBe("!")
  })

  it("una misura che il modello non da' ha la carta dell'ignoto, senza numeri ne' grafico", async () => {
    const senza = { ...NOTTE, measures: NOTTE.measures.map((m) => (m.code === "visibility" ? { ...m, level: null, value: null, peak: null, known_hours: 0 } : m)) }
    conNotti(senza)
    await apriMeteo()
    await scheda()

    const visibilita = carta(/^Visibilit/)
    expect(visibilita.querySelector(".al-c-card-meteo__testo-4")?.textContent).toBe("Non disponibile")
    expect(visibilita.querySelector(".al-c-card-meteo__testo-2")).toBeNull()
    // al posto del grafico un tratteggio fermo: nessuna barretta dice un'ora
    expect(barre(visibilita).every((b) => b.style.background.startsWith("repeating-linear-gradient"))).toBe(true)
    expect(barre(visibilita).some((b) => b.parentElement?.hasAttribute("title"))).toBe(false)
  })

  it("con la chiave appena messa e Meteoblue non ancora chiesto non chiede la chiave", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: null, meteoblue: null } })
    await apriMeteo()
    await scheda()

    expect(screen.queryByText(/richiede una chiave (API )?Meteoblue/i)).toBeNull()
  })

  it("Meteoblue che tace la prima volta non promette un seeing di prima che non c'e'", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: null, meteoblue: "unreachable" } })
    await apriMeteo()
    await scheda()

    expect(screen.queryByText(/dati precedenti/)).toBeNull()
  })

  it("Meteoblue che tace lascia il seeing di prima, e lo dice", async () => {
    const vista = { ...NOTTE, measures: NOTTE.measures.map((m) => (m.code === "seeing" ? misura("seeing", { level: "go", value: 1.2, axis_max: 5 }) : m)) }
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [vista], seeing: { key: true, source: "meteoblue", meteoblue: "unreachable" } })
    await apriMeteo()

    expect(await screen.findByText(/aggiornamento del seeing non riuscito: dati precedenti/)).toBeDefined()
  })

  it("un seeing che copre solo parte della notte lo dice nella media e nel picco", async () => {
    const seeing = misura("seeing", {
      level: "go", value: 1.2, axis_max: 5, peak: 1.5, peak_at: "2026-09-26T22:00:00+02:00",
      peak_until: "2026-09-26T23:00:00+02:00", known_hours: 2, known_until: "2026-09-27T02:00:00+02:00",
    })
    conNotti({ ...NOTTE, measures: [...NOTTE.measures.filter((m) => m.code !== "seeing"), seeing] })
    await apriMeteo()
    await scheda()

    const testo = carta(/^Seeing$/).textContent
    expect(testo).toContain("media fino alle 02:00 · Meteoblue")
    expect(testo).toContain("dalle 02:00 non disponibile")
    // il segno dei secondi d'arco sta accanto al numero, come un'unita'
    expect(carta(/^Seeing$/).querySelector(".al-c-card-meteo__riga-2 .al-c-card-meteo__testo-3")?.textContent).toBe("″")
  })
})

describe("il Meteo, la testa", () => {
  const testa = () => screen.getByRole("region", { name: "Le prossime notti" })

  it("la testa dice quando e' arrivata la previsione e che le ore sono del sito", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    // il giorno col mese per esteso e senza anno, come nel vocabolario (docs/domini/meteo.md)
    expect(testa().textContent).toMatch(/Previsione Open-Meteo del \d+ [a-z]+, \d\d:\d\d/)
    expect(testa().textContent).toContain("ora locale del sito")
  })

  it("lo switch salva il modello scelto e rilegge, anche Stanotte", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] }, {
      "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    })
    await apriMeteo()

    fireEvent.click(await screen.findByRole("button", { name: "Modello: Automatico" }))
    fireEvent.click(screen.getByRole("menuitemradio", { name: /^ICON/ }))
    await waitFor(() =>
      expect(scritture()).toContainEqual({
        url: expect.stringContaining("/api/v1/settings"),
        metodo: "PATCH",
        corpo: { values: { weather_model: "icon_seamless" } },
      }),
    )
    await waitFor(() => expect(chiamate().filter((u) => u.includes("/api/v1/tonight")).length).toBeGreaterThan(1))
  })

  it("sul telefono il modello si sceglie da un elenco che dice cos'e' ogni voce", async () => {
    conNotti(NOTTE)
    await apriMeteoTelefono()

    const apri = await screen.findByRole("button", { name: /^modello/i })
    fireEvent.click(apri)
    expect(apri.getAttribute("aria-expanded")).toBe("true")
    expect(screen.getByRole("menuitemradio", { name: /ECMWF/ }).textContent).toContain("centro europeo")
  })

  it("se l'ultima richiesta non ha avuto risposta lo dice, con l'ora della previsione che resta", async () => {
    meteo({
      fetched_at: "2026-09-25T06:00:00.000Z",
      last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" },
      nights: [NOTTE],
    })
    await apriMeteo()

    const riga = await screen.findByText(/^Aggiornamento delle \S+ non riuscito\. Previsione delle/)
    expect(within(riga.closest("[role=status]") as HTMLElement).getByRole("button").textContent).toBe("Aggiorna")
  })

  it("anche senza nessuna previsione, una richiesta senza risposta lo dice", async () => {
    meteo({ last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" } })
    await apriMeteo()

    expect(await screen.findByText(/^Aggiornamento delle \S+ non riuscito\. Nessuna previsione disponibile/)).toBeDefined()
  })

  it("dopo Aggiorna senza risposta la pagina rilegge e la riga compare", async () => {
    meteo({ fetched_at: "2026-09-25T06:00:00.000Z", last_request: { at: "2026-09-25T06:00:00.000Z", status: "ok" }, nights: [NOTTE] }, {
      "POST /api/v1/weather/refresh": { stato: 200, corpo: { status: "unreachable" } },
    })
    await apriMeteo()
    await scheda()
    expect(screen.queryByText(/^Aggiornamento delle \S+ non riuscito/)).toBeNull()

    meteo({ fetched_at: "2026-09-25T06:00:00.000Z", last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" }, nights: [NOTTE] }, {
      "POST /api/v1/weather/refresh": { stato: 200, corpo: { status: "unreachable" } },
    })
    fireEvent.click(screen.getByRole("button", { name: "Aggiorna la previsione" }))
    expect(await screen.findByText(/^Aggiornamento delle \S+ non riuscito\. Previsione delle/)).toBeDefined()
  })

  it("se l'ultima richiesta e' andata bene non dice niente", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", last_request: { at: "2026-09-25T15:00:00.000Z", status: "ok" }, nights: [NOTTE] })
    await apriMeteo()
    await scheda()

    expect(screen.queryByText(/^Aggiornamento delle \S+ non riuscito/)).toBeNull()
  })

  it("dopo il pulsante anche Stanotte rilegge la notte in corso", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] }, {
      "POST /api/v1/weather/refresh": { stato: 200, corpo: { status: "ok" } },
    })
    await apriMeteo()
    await waitFor(() => expect(chiamate().filter((u) => u.includes("/api/v1/tonight"))).toHaveLength(1))

    fireEvent.click(await screen.findByRole("button", { name: "Aggiorna la previsione" }))
    await waitFor(() => expect(chiamate().filter((u) => u.includes("/api/v1/tonight"))).toHaveLength(2))
  })
})

describe("il Meteo, quando manca qualcosa", () => {
  it("senza sito predefinito manda a dichiararlo", async () => {
    meteo({ site: null })
    await apriMeteo()

    expect(await screen.findByText(/sito predefinito mancante/i)).toBeDefined()
    fireEvent.click(screen.getByRole("button", { name: /^aggiungi sito$/i }))
    await waitFor(() => expect(window.location.pathname).toBe("/impostazioni/siti"))
  })

  it("prima della prima previsione lo dice, invece di un elenco vuoto muto", async () => {
    meteo({})
    await apriMeteo()

    expect(await screen.findByText(/^nessuna previsione disponibile\.$/i)).toBeDefined()
    // nessuna fonte ha ancora scritto niente: nessuna si cita
    expect(screen.queryByRole("link", { name: "Weather data by Open-Meteo.com" })).toBeNull()
    expect(screen.queryByRole("tablist", { name: /notti/i })).toBeNull()
  })

  it("un modello senza notti lo dice, anche se la previsione e' arrivata", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [] })
    await apriMeteo()

    expect(await screen.findByText(/nessuna notte disponibile per questo modello/i)).toBeDefined()
  })

  it("un sito predefinito senza fuso orario lo dice, e porta a sistemarlo", async () => {
    meteo({ missing: "no_timezone" })
    await apriMeteo()

    expect(await screen.findByText(/fuso orario del sito non riconosciuto/i)).toBeDefined()
    expect(screen.getByRole("button", { name: /^modifica sito$/i })).toBeDefined()
    expect(screen.queryByText(/nessuna previsione disponibile/i)).toBeNull()
  })
})

describe("il Meteo, le fonti citate", () => {
  it("cita Open-Meteo e i dati Copernicus con l'anno; 7Timer non c'e' piu'", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    expect(await screen.findByRole("link", { name: "Weather data by Open-Meteo.com" })).toBeDefined()
    expect(screen.getByText(/Copernicus Atmosphere Monitoring Service information 2026/)).toBeDefined()
    expect(screen.queryByText(/7Timer/)).toBeNull()
  })

  it("cita solo le fonti del cielo che hanno scritto qualcosa, e nessuna che non conosce", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], sources: [{ source: "altra", fetched_at: "2026-09-25T15:00:00.000Z" }] })
    await apriMeteo()

    await screen.findByRole("link", { name: "Weather data by Open-Meteo.com" })
    expect(screen.queryByText(/Copernicus/)).toBeNull()
    expect(screen.queryByRole("link", { name: /meteoblue/i })).toBeNull()
  })

  it("cita Meteoblue quando il seeing viene da li'", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], sources: [{ source: "meteoblue", fetched_at: "2026-09-25T15:00:00.000Z" }] })
    await apriMeteo()

    expect(await screen.findByRole("link", { name: /meteoblue/i })).toBeDefined()
  })
})

describe("il Meteo, il cielo", () => {
  const laNotte = () => screen.getByRole("region", { name: "La notte" })
  const legenda = () => [...laNotte().querySelectorAll(".al-meteo__testo-7")].map((e) => e.textContent)

  it("all'apertura disegna solo le nubi, ognuna dal suo zero; l'umidita' si accende", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    const strati = [...grafico().querySelectorAll("svg g")]
    expect(strati).toHaveLength(3)
    // ogni area parte e torna sul fondo del grafico (y 195)
    for (const g of strati) expect(g.querySelector("path")?.getAttribute("d")).toMatch(/^M[\d.]+ 195 .* 195 Z $/)
    const accendi = sulGrafico("umidità %")
    expect(accendi.getAttribute("aria-checked")).toBe("false")
    expect(umidita()).toBeNull()
    fireEvent.click(accendi)
    expect(sulGrafico("umidità %").getAttribute("aria-checked")).toBe("true")
    expect(umidita()).not.toBeNull()
  })

  it("la legenda e il lettore dicono solo cio' che e' sul grafico", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    expect(legenda()).toEqual(["Nuvole basse", "medie", "alte", "Trasparenza"])
    fireEvent.keyDown(grafico(), { key: "Home" })
    expect(lettore()?.textContent).not.toContain("Umidità")
    fireEvent.click(sulGrafico("umidità %"))
    fireEvent.click(sulGrafico("pioggia"))
    expect(legenda()).toEqual(["Nuvole basse", "medie", "alte", "Trasparenza", "umidità %", "Pioggia"])
    expect(laNotte().textContent).toContain("Pioggiaa destra, col colore del giudizio")
    fireEvent.keyDown(grafico(), { key: "Home" })
    expect(lettore()?.textContent).toContain("Umidità")
    expect(lettore()?.textContent).toContain("Pioggia")
  })

  it("a destra una metrica si sceglie, con la sua parola dove cambia; un'altra la sostituisce", async () => {
    const ventoso = NOTTE.hours.map((o, i) => (i >= 2 ? { ...o, wind_kmh: 30, levels: { ...o.levels, wind: "nogo" } } : o))
    conNotti({ ...NOTTE, hours: ventoso })
    await apriMeteo()
    await scheda()

    expect(sulGrafico("vento").getAttribute("aria-checked")).toBe("false")
    fireEvent.click(sulGrafico("vento"))
    expect(sulGrafico("vento").getAttribute("aria-checked")).toBe("true")
    expect(parole().map((p) => p.textContent)).toEqual(["✕ non adatta"])
    fireEvent.click(sulGrafico("pioggia"))
    expect(sulGrafico("pioggia").getAttribute("aria-checked")).toBe("true")
    expect(sulGrafico("vento").getAttribute("aria-checked")).toBe("false")
    expect(parole().map((p) => p.textContent)).toEqual(["✓ buona"])
  })

  it("la parola della prima ora si scrive anche lei, all'inizio della scala", async () => {
    const ventoso = NOTTE.hours.map((o) => ({ ...o, sky: "dark", wind_kmh: 30, levels: { ...o.levels, wind: "nogo" } }))
    conNotti({ ...NOTTE, hours: ventoso })
    await apriMeteo()
    await scheda()

    fireEvent.click(sulGrafico("vento"))
    expect(parole()).toHaveLength(1)
    expect(parole()[0]?.style.left).toBe("0%")
  })

  it("il seeing senza chiave c'e' fra le metriche ma non si sceglie, e dice perche'", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    const seeing = sulGrafico("seeing")
    expect(seeing.getAttribute("aria-disabled")).toBe("true")
    expect(seeing.getAttribute("title")).toBe("Il seeing richiede una chiave Meteoblue.")
  })

  it("un'ora che il servizio non da' sulla scala di destra lascia un vuoto nella linea, e il lettore dice \"Non disponibile\"", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    // il vento delle 22 manca nella notte di prova: nessun tratto lo attraversa
    fireEvent.click(sulGrafico("vento"))
    expect(segmenti()).toHaveLength(0)
    fireEvent.keyDown(grafico(), { key: "ArrowRight" })
    expect(lettore()?.textContent).toContain("VentoNon disponibile")
  })

  it("la pioggia a destra e' una linea col colore del giudizio di ogni ora, tenue fuori dal buio", async () => {
    const piovosa = NOTTE.hours.map((o, i) => (i === 2 ? { ...o, precip_mm: 0.5, levels: { ...o.levels, rain: "marginal" } } : o))
    conNotti({ ...NOTTE, hours: piovosa })
    await apriMeteo()
    await scheda()

    fireEvent.click(sulGrafico("pioggia"))
    expect(segmenti().map((s) => s.getAttribute("stroke"))).toEqual(["var(--prot-tenue)", "var(--incerto-testo)"])
  })

  it("la condensa a destra va sul suo asse: accanto i due capi della sua scala", async () => {
    conNotti({ ...NOTTE, measures: [...NOTTE.measures, misura("condensation", { level: "go", value: 8, axis_min: -5, axis_max: 15 })] })
    await apriMeteo()
    await scheda()

    fireEvent.click(sulGrafico("condensa"))
    const capi = [...grafico().querySelectorAll<HTMLElement>("span")].filter((s) => s.style.right === "0px")
    expect(capi.map((s) => s.textContent?.replace(/\s/g, " "))).toEqual([expect.stringMatching(/^15,0 ?°C$/), expect.stringMatching(/^[-−]5,0 ?°C$/)])
  })

  it("cambiando notte le carte tornano alla notte, e le misure sul grafico restano accese", async () => {
    conNotti(NOTTE, { ...NOTTE, night: "2026-09-27" })
    await apriMeteo()
    await scheda()

    const ore = within(carta(/^Vento$/)).getByRole("group")
    fireEvent.keyDown(ore, { key: "ArrowRight" })
    fireEvent.keyDown(ore, { key: "ArrowRight" })
    fireEvent.click(sulGrafico("vento"))
    expect(carta(/^Vento$/).textContent).toContain("solo questa carta")
    fireEvent.click((await screen.findAllByRole("tab"))[1] as HTMLElement)
    expect(carta(/^Vento$/).textContent).toContain("media nel buio · a 10 m")
    expect(within(carta(/^Vento$/)).queryByRole("link", { name: "Torna alla notte" })).toBeNull()
    expect(sulGrafico("vento").getAttribute("aria-checked")).toBe("true")
  })

  it("il grafico disegna la Trasparenza di ogni ora, e il lettore la dice", async () => {
    conNotti({ ...NOTTE, hours: NOTTE.hours.map((o, i) => ({ ...o, transparency: 50 + i * 10 })) })
    await apriMeteo()
    await scheda()

    expect(grafico().querySelectorAll('path[stroke="var(--prot-barra)"]')).toHaveLength(2)
    fireEvent.keyDown(grafico(), { key: "Home" })
    expect(lettore()?.textContent).toContain("Trasparenza60")
    expect(comeVa().textContent).toContain("Trasparenza della notte64/100")
  })

  it("con le frecce il filo va a un'ora, il lettore la dice e tutte le carte la seguono; Esc torna alla notte", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    fireEvent.keyDown(grafico(), { key: "ArrowRight" })
    expect(grafico().getAttribute("aria-valuetext")).toContain("alle 22:00")
    expect(lettore()?.textContent).toContain("Nuvole basse")
    expect(misure().textContent).toContain("alle 22:00 · fuori dal grafico tornano alla notte")
    expect(carta(/^Nuvole$/).textContent).toContain("alle 22:00")
    fireEvent.keyDown(grafico(), { key: "Escape" })
    expect(lettore()).toBeNull()
    expect(carta(/^Nuvole$/).textContent).toContain("media nel buio")
  })
})

describe("il Meteo, una carta a un'ora", () => {
  it("le frecce sulle barrette portano la carta a un'ora e ce la lasciano; \u00d7 la riporta alla notte", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    const vento = carta(/^Vento$/)
    const ore = within(vento).getByRole("group", { name: /^Vento ora per ora/ })
    fireEvent.keyDown(ore, { key: "ArrowRight" })
    fireEvent.keyDown(ore, { key: "ArrowRight" })
    expect(vento.textContent).toContain("alle 23:00 · solo questa carta")
    expect(barre(vento).filter((b) => b.style.opacity === "0.35")).toHaveLength(2)
    // le altre carte restano sulla notte
    expect(carta(/^Nuvole$/).textContent).toContain("media nel buio")
    fireEvent.click(within(vento).getByRole("link", { name: "Torna alla notte" }))
    expect(vento.textContent).toContain("media nel buio · a 10 m")
    expect(within(vento).queryByRole("link", { name: "Torna alla notte" })).toBeNull()
  })

  it("a un'ora la carta dice il valore e la parola di quell'ora", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    const vento = carta(/^Vento$/)
    fireEvent.keyDown(within(vento).getByRole("group"), { key: "ArrowLeft" })
    expect(vento.querySelector(".al-c-card-meteo__testo-2")?.textContent).toBe("5")
    expect(vento.textContent).toContain("buona alle 19:00")
  })
})

describe("il Meteo, rifiniture del cielo e delle carte", () => {
  it("l'aerosol non ha unita': il lettore dice il numero e basta", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    fireEvent.click(sulGrafico("aerosol"))
    fireEvent.keyDown(grafico(), { key: "Home" })
    const riga = [...(lettore()?.children ?? [])].find((r) => r.textContent?.startsWith("Aerosol"))
    expect(riga?.textContent).toBe("Aerosol0,12")
  })

  it("col dito il filo resta dove l'hai lasciato, finche' non tocchi altrove", async () => {
    conNotti(NOTTE)
    await apriMeteoTelefono()
    await scheda()

    fireEvent.keyDown(grafico(), { key: "Home" })
    fireEvent.mouseLeave(grafico())
    expect(lettore()).not.toBeNull()
  })

  it("la barretta di un'ora senza valore dice \"Non disponibile\" senza l'unita' accanto", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    expect(barre(carta(/^Vento$/))[1]?.parentElement?.getAttribute("title")).toBe("22:00 · Non disponibile")
  })
})

describe("il Meteo, la striscia e la Luna", () => {
  it("la striscia dice quali notti sono ora per ora e quali tendenza", async () => {
    conNotti(NOTTE, TENDENZA)
    await apriMeteo()
    await scheda()

    const fila = screen.getByRole("tablist", { name: "le sette notti" })
    expect(fila.textContent).toContain("ora per ora")
    expect(fila.textContent).toContain("tendenza, meno affidabile")
  })

  it("una notte di tendenza dice la sua Luna, nella striscia e negli altri fattori", async () => {
    const luna = misura("moon", {
      level: "marginal", value: 40, known_from_start: false, known_to_end: true,
      known_since: "2026-09-30T03:00:00+02:00", known_until: "2026-09-30T06:00:00+02:00",
    })
    conNotti(NOTTE, { ...TENDENZA, measures: [luna] })
    await apriMeteo()

    const tende = (await screen.findAllByRole("tab"))[1] as HTMLElement
    expect(tende.textContent).toContain("Luna al 40%")
    fireEvent.click(tende)
    await waitFor(() => expect(comeVa().textContent).toContain("banda larga al limite"))
    // board :511: the trend keeps the dark fact; its transparency is not a forecast hour
    const fatti = comeVa().querySelectorAll(".al-meteo__colonna-10")
    expect([...fatti].map((f) => f.firstElementChild?.textContent)).toEqual(["Buio"])
  })
})
