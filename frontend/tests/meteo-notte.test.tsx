// @vitest-environment jsdom
/**
 * La carta **La notte** del Meteo (`src/MeteoNotte.tsx`, tavola v82) disegnata da sola: perche'
 * una misura non va sul grafico, l'obiettivo Sole, la pillola, la chiave delle fasce e la scala
 * "Sul grafico". La pagina intera sta in `meteo.test.tsx`; qui ogni ramo, caso per caso.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { Sguardo } from "../src/Meteo"
import type { Accesa } from "../src/MeteoCielo"
import type { Meteo, Notte } from "../src/MeteoDati"
import { LaNotte, nomeDellaMisura, spenta } from "../src/MeteoNotte"
import { NOTTE, TENDENZA, banda, misura } from "./meteo-banco"

afterEach(cleanup)
afterEach(() => vi.unstubAllGlobals())

const notte = (campi: Record<string, unknown> = {}) => ({ ...NOTTE, ...campi }) as unknown as Notte
const detto = (seeing: Record<string, unknown> = {}) =>
  ({ seeing: { key: false, source: null, meteoblue: null, ...seeing } }) as unknown as Meteo
const MANCA = "Il servizio non ha mandato questa misura per la notte"
const conMisure = (...m: ReturnType<typeof misura>[]) => notte({ measures: m })

describe("spenta: perche' una misura non va sul grafico", () => {
  it("l'umidita' va sempre; una misura con ore date anche", () => {
    expect(spenta("humidity", conMisure(), detto())).toBeNull()
    expect(spenta("wind", conMisure(misura("wind", { known_hours: 2 })), detto())).toBeNull()
    expect(spenta("seeing", conMisure(misura("seeing", { known_hours: 2 })), detto())).toBeNull()
  })
  it("il seeing senza ore: senza chiave o chiave rifiutata, la chiave; non ancora chiesto, il prossimo giro", () => {
    const senza = conMisure(misura("seeing", { known_hours: 0 }))
    expect(spenta("seeing", senza, detto())).toBe("Il seeing richiede una chiave Meteoblue.")
    expect(spenta("seeing", conMisure(), detto())).toBe("Il seeing richiede una chiave Meteoblue.")
    expect(spenta("seeing", senza, detto({ key: true, meteoblue: "refused" }))).toBe(
      "Il seeing richiede una chiave Meteoblue.",
    )
    expect(spenta("seeing", senza, detto({ key: true, meteoblue: null }))).toBe(
      "Il seeing arriva da Meteoblue al prossimo giro.",
    )
    expect(spenta("seeing", senza, detto({ key: true, meteoblue: "ok" }))).toBe(MANCA)
  })
  it("sotto le nuvole seeing e aerosol non si misurano; le altre mancano e basta", () => {
    const nubi = misura("cloud", { level: "nogo" })
    const coperta = (code: string) => conMisure(nubi, misura(code, { known_hours: 0 }))
    const ok = detto({ key: true, meteoblue: "ok" })
    expect(spenta("seeing", coperta("seeing"), ok)).toBe("Sotto le nuvole non si misura")
    expect(spenta("aerosol", coperta("aerosol"), ok)).toBe("Sotto le nuvole non si misura")
    expect(spenta("aerosol", conMisure(nubi), ok)).toBe("Sotto le nuvole non si misura")
    expect(spenta("wind", coperta("wind"), ok)).toBe(MANCA)
    const incerta = conMisure(
      misura("cloud", { level: "marginal" }),
      misura("aerosol", { known_hours: 0 }),
    )
    expect(spenta("aerosol", incerta, ok)).toBe(MANCA)
    // la parola che conta e' quella delle nuvole, non di un'altra misura
    const vento = conMisure(
      misura("wind", { level: "nogo" }),
      misura("aerosol", { known_hours: 0 }),
    )
    expect(spenta("aerosol", vento, ok)).toBe(MANCA)
  })
  it("il nome di una misura", () => {
    expect(nomeDellaMisura("rain")).toBe("Pioggia")
  })
})

type Prove = {
  notte?: Notte
  detto?: Meteo
  prima?: boolean
  telefono?: boolean
  accese?: Accesa[]
  obiettivo?: "deep" | "sole"
  intera?: boolean
}

function disegnaLaNotte(p: Prove = {}) {
  const sguardo: Sguardo = {
    ora: null,
    scegliOra: vi.fn(),
    accese: p.accese ?? [],
    accendi: vi.fn(),
    fisse: {},
    fissa: vi.fn(),
    aperta: null,
    apri: vi.fn(),
  }
  const scegliObiettivo = vi.fn()
  render(
    <LaNotte
      detto={p.detto ?? detto()}
      notte={p.notte ?? notte()}
      prima={p.prima ?? true}
      formato={p.telefono ? "telefono" : "desktop"}
      sguardo={sguardo}
      obiettivo={p.obiettivo ?? "deep"}
      scegliObiettivo={scegliObiettivo}
      intera={p.intera ?? false}
    />,
  )
  return { sguardo, scegliObiettivo, carta: screen.getByRole("region", { name: "La notte" }) }
}

const testi = (c: HTMLElement, sel: string) =>
  [...c.querySelectorAll<HTMLElement>(sel)].map((e) => e.textContent)
const pillola = (c: HTMLElement) =>
  c.querySelector<HTMLElement>(".al-meteo__pillola-1, .al-meteo__pillola-3")
const grande = (c: HTMLElement) =>
  c.querySelector<HTMLElement>(".al-meteo__testo-4, .al-meteo__testo-25")

describe("La notte: l'obiettivo e il numero grande", () => {
  it("Deep sky: le Ore di posa col semaforo incerto, la Luna e il grafico", () => {
    const { carta } = disegnaLaNotte()
    expect(carta.querySelector(".al-meteo__testo-3")?.textContent).toBe(
      "Ore di posa · notte di sabato 26 · stanotte",
    )
    expect(grande(carta)?.style.fontSize).toBe("64px")
    expect(pillola(carta)?.textContent).toMatch(/^! /)
    expect(pillola(carta)?.style.background).toBe("var(--incerto-fondo)")
    expect(pillola(carta)?.style.color).toBe("var(--incerto-testo)")
    expect(carta.querySelector("svg")).not.toBeNull()
    expect(within(carta).getByRole("group", { name: "Sul grafico" })).toBeTruthy()
  })
  it("il semaforo buono e quello rosso hanno i loro colori e il loro segno", () => {
    const buona = disegnaLaNotte({ notte: notte({ verdict: "go" }) }).carta
    expect(pillola(buona)?.textContent).toMatch(/^✓ /)
    expect(pillola(buona)?.style.background).toBe("var(--buono-fondo)")
    expect(pillola(buona)?.style.color).toBe("var(--buono-testo)")
    cleanup()
    const no = disegnaLaNotte({ notte: notte({ verdict: "nogo" }) }).carta
    expect(pillola(no)?.textContent).toMatch(/^✕ /)
    expect(pillola(no)?.style.background).toBe("var(--non-adatto-fondo)")
    expect(pillola(no)?.style.color).toBe("var(--non-adatto-testo)")
  })
  it("il Sole: la parola sola, la pillola col punto di domanda, niente grafico ne' scala", () => {
    const { carta } = disegnaLaNotte({ obiettivo: "sole" })
    expect(carta.querySelector(".al-meteo__testo-3")?.textContent).toBe("Il Sole")
    expect(grande(carta)?.textContent).toBe("Non disponibile")
    expect(grande(carta)?.style.fontSize).toBe("44px")
    expect(pillola(carta)?.textContent).toBe("? Sole non disponibile")
    expect(pillola(carta)?.style.background).toBe("var(--carta-2)")
    expect(pillola(carta)?.style.color).toBe("var(--testo)")
    expect(carta.querySelector(".al-meteo__testo-5")?.textContent).toBe(
      "Il meteo del Sole arriva col Sistema solare. Fino ad allora qui non c'è un verdetto.",
    )
    expect(carta.querySelector("svg")).toBeNull()
    expect(within(carta).queryByRole("group", { name: "Sul grafico" })).toBeNull()
    expect(carta.querySelector(".al-meteo__riga-4")).toBeNull()
  })
  it("la Luna della notte sta sotto il numero solo in Deep sky", () => {
    const luna = misura("moon", {
      level: "nogo",
      value: 62,
      known_hours: 2,
      known_since: "2026-09-26T21:00:00+02:00",
      known_until: "2026-09-26T23:00:00+02:00",
    })
    const n = notte({ measures: [...NOTTE.measures, luna] })
    expect(disegnaLaNotte({ notte: n }).carta.querySelector(".al-meteo__riga-4")).not.toBeNull()
    cleanup()
    expect(
      disegnaLaNotte({ notte: n, obiettivo: "sole" }).carta.querySelector(".al-meteo__riga-4"),
    ).toBeNull()
  })
  it("l'obiettivo scelto e' acceso, l'altro si sceglie; a riga intera non c'e'", () => {
    const { carta, scegliObiettivo } = disegnaLaNotte()
    const scelta = within(carta).getByRole("tablist", { name: "Obiettivo" })
    const [deep, sole] = within(scelta).getAllByRole("tab")
    expect([deep?.textContent, sole?.textContent]).toEqual(["Deep sky", "Sole"])
    expect(deep?.getAttribute("aria-selected")).toBe("true")
    expect(sole?.getAttribute("aria-selected")).toBe("false")
    fireEvent.click(sole as HTMLElement)
    expect(scegliObiettivo).toHaveBeenCalledWith("sole")
    cleanup()
    const piccola = disegnaLaNotte({ telefono: true }).carta
    expect(within(piccola).getByRole("tablist", { name: "Obiettivo" }).className).toContain(
      "al-scelta--piccola",
    )
    cleanup()
    const intera = disegnaLaNotte({ intera: true }).carta
    expect(within(intera).queryByRole("tablist", { name: "Obiettivo" })).toBeNull()
  })
  it("sul telefono il numero e' piu' piccolo, e senza verdetto ancora di piu'", () => {
    expect(grande(disegnaLaNotte({ telefono: true }).carta)?.style.fontSize).toBe("48px")
    cleanup()
    const ignota = disegnaLaNotte({ telefono: true, notte: notte({ verdict: null }) }).carta
    expect(grande(ignota)?.style.fontSize).toBe("32px")
    expect(pillola(ignota)).toBeNull()
  })
  it("una tendenza ha il grafico ma ne' la frase del gesto ne' la scala", () => {
    const { carta } = disegnaLaNotte({ notte: TENDENZA as unknown as Notte })
    expect(carta.querySelector("svg")).not.toBeNull()
    expect(carta.querySelector(".al-meteo__testo-6")).toBeNull()
    expect(within(carta).queryByRole("group", { name: "Sul grafico" })).toBeNull()
  })
  it("la frase del gesto: il mouse sul largo, il dito sul telefono", () => {
    expect(disegnaLaNotte().carta.querySelector(".al-meteo__testo-6")?.textContent).toBe(
      "Passa sul grafico per vedere un'ora · frecce per spostarti, Esc per tornare alla notte",
    )
    cleanup()
    expect(disegnaLaNotte({ telefono: true }).carta.textContent).toContain(
      "Tocca il grafico o le barrette per vedere un'ora",
    )
  })
})

describe("La notte: la chiave delle fasce", () => {
  const chiave = (c: HTMLElement) => testi(c, ".al-meteo__riga-7")
  it("dal tramonto al buio, con le ore del buio", () => {
    expect(chiave(disegnaLaNotte().carta)).toEqual([
      "giorno · tramonto 19:20",
      "crepuscolo civile",
      "nautico",
      "astronomico",
      "buio 21:00–23:00",
    ])
  })
  it("ogni voce col suo colore di fascia", () => {
    const blocchi = [...disegnaLaNotte().carta.querySelectorAll<HTMLElement>(".al-meteo__blocco-2")]
    expect(blocchi.map((b) => b.style.background)).toEqual(
      [0, 1, 2, 3, 4].map(
        (o) =>
          `color-mix(in srgb, var(--banda-colore) calc(var(--banda-${o}) * 100%), transparent)`,
      ),
    )
    expect(blocchi[0]?.style.boxShadow).toBe("inset 0 0 0 1px var(--prot-tenue)")
  })
  it("con l'alba in fondo la dice; senza giorno in testa niente tramonto", () => {
    expect(chiave(disegnaLaNotte({ notte: TENDENZA as unknown as Notte }).carta)).toEqual([
      "giorno · tramonto 19:20",
      "buio 19:20–06:40",
      "alba 06:40",
    ])
    cleanup()
    const fasce = [
      banda("nautical", "2026-09-26T20:00:00+02:00", "2026-09-26T21:00:00+02:00"),
      banda("day", "2026-09-27T06:00:00+02:00", "2026-09-27T07:00:00+02:00"),
    ]
    expect(chiave(disegnaLaNotte({ notte: notte({ sky_bands: fasce }) }).carta)).toEqual([
      "giorno",
      "nautico",
      "alba 06:00",
    ])
  })
  it("senza fasce resta il giorno; sul telefono la chiave non c'e'", () => {
    expect(chiave(disegnaLaNotte({ notte: notte({ sky_bands: null }) }).carta)).toEqual(["giorno"])
    cleanup()
    expect(chiave(disegnaLaNotte({ telefono: true }).carta)).toEqual([])
  })
})

describe("La notte: la scala Sul grafico", () => {
  const voci = (c: HTMLElement) =>
    within(within(c).getByRole("group", { name: "Sul grafico" })).getAllByRole("checkbox")
  const conto = (c: HTMLElement) => c.querySelector(".al-meteo__testo-10")?.textContent
  it("la legenda: le nubi coi loro toni, la Trasparenza, e cio' che e' acceso", () => {
    const { carta } = disegnaLaNotte({ accese: ["humidity", "rain"] })
    const blocchi = [...carta.querySelectorAll<HTMLElement>(".al-meteo__blocco-3")]
    const mix = (p: number) => `color-mix(in srgb, var(--prot-testo) ${p}%, transparent)`
    expect(blocchi.map((b) => b.style.background)).toEqual([
      mix(28),
      mix(17),
      mix(10),
      "var(--prot-barra)",
      "var(--umidita)",
      "var(--buono-testo)",
    ])
    expect(blocchi.map((b) => b.style.boxShadow)).toEqual([
      `inset 0 0 0 1px ${mix(90)}`,
      `inset 0 0 0 1px ${mix(60)}`,
      `inset 0 0 0 1px ${mix(45)}`,
      "inset 0 0 0 1px var(--prot-barra)",
      "inset 0 0 0 1px var(--umidita)",
      "inset 0 0 0 1px var(--prot-tenue)",
    ])
    expect(testi(carta, ".al-meteo__testo-8")).toEqual(["a destra, col colore del giudizio"])
  })
  it("le voci: le misure della notte, accese col loro colore, e perche' una non si sceglie", () => {
    const { carta, sguardo } = disegnaLaNotte({ accese: ["humidity", "wind"] })
    const v = voci(carta)
    // condensa e jet la notte di prova non li ha; il seeing si', spento col suo perche'
    expect(v.map((x) => x.textContent)).toEqual([
      "umidità %",
      "pioggia",
      "vento",
      "seeing",
      "aerosol",
      "visibilità",
    ])
    const [umidita, pioggia, vento, seeing] = v
    expect(umidita?.getAttribute("title")).toBe("in %, sulla scala di sinistra")
    expect(umidita?.style.getPropertyValue("--voce-colore")).toBe("var(--umidita)")
    expect(vento?.style.getPropertyValue("--voce-colore")).toBe("var(--barretta)")
    expect(vento?.getAttribute("aria-checked")).toBe("true")
    expect(pioggia?.getAttribute("aria-checked")).toBe("false")
    expect(pioggia?.style.getPropertyValue("--voce-colore")).toBe("")
    expect(pioggia?.getAttribute("title")).toBe("una alla volta, sulla scala di destra")
    expect(pioggia?.getAttribute("aria-disabled")).toBeNull()
    expect(seeing?.getAttribute("title")).toBe("Il seeing richiede una chiave Meteoblue.")
    expect(seeing?.getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(pioggia as HTMLElement)
    expect(sguardo.accendi).toHaveBeenCalledWith("rain")
  })
  it("una misura che il servizio manda si offre, al suo posto", () => {
    const con = [...NOTTE.measures, misura("condensation"), misura("jet")]
    const { carta } = disegnaLaNotte({ notte: notte({ measures: con }) })
    expect(voci(carta).map((x) => x.textContent)).toEqual([
      "umidità %",
      "condensa",
      "pioggia",
      "vento",
      "seeing",
      "jet stream",
      "aerosol",
      "visibilità",
    ])
  })
  it("il conto delle accese: niente, una, piu' d'una", () => {
    expect(conto(disegnaLaNotte().carta)).toBe("")
    cleanup()
    expect(conto(disegnaLaNotte({ accese: ["humidity"] }).carta)).toBe("· 1 accesa")
    cleanup()
    expect(conto(disegnaLaNotte({ accese: ["humidity", "wind"] }).carta)).toBe("· 2 accese")
  })
  it("le accese che la notte non ha restano fuori dal grafico e dal conto", () => {
    const { carta } = disegnaLaNotte({ accese: ["humidity", "seeing"] })
    expect(conto(carta)).toBe("· 1 accesa")
  })
  it("sul telefono la legenda e' senza note, e la scala scorre", () => {
    const { carta } = disegnaLaNotte({ telefono: true, accese: ["rain"] })
    expect(testi(carta, ".al-meteo__testo-8")).toEqual([])
    expect(carta.querySelector(".al-meteo__blocco-13")).not.toBeNull()
    expect(carta.querySelector(".al-meteo__testo-27")?.textContent).toBe("Sul grafico · 1 accesa")
    expect(carta.querySelector(".al-scelta--scorre")).not.toBeNull()
  })
})
