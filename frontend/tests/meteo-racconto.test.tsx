// @vitest-environment jsdom
/**
 * Il **racconto della notte** del Meteo (passo 13.1, tavola v82 Meteo.dc.html:460-499): sotto
 * gli altri fattori, dal tramonto all'alba, un evento per riga; sul telefono i momenti che
 * contano, la notte intera a un tocco. Gli eventi li scrive il backend; qui si dicono.
 */
import { fireEvent, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { pulisci } from "./banco"
import { NOTTE, apriMeteo, apriMeteoTelefono, comeVa, conNotti, scheda } from "./meteo-banco"

afterEach(pulisci)

const ev = (at: string, kind: string, group: string, resto: Record<string, unknown> = {}) => ({
  at: `2026-09-26T${at}+02:00`,
  kind,
  group,
  key_moment: ["sky", "verdict", "moon", "shooting"].includes(group),
  level: null,
  value: null,
  bound: null,
  until: null,
  body: null,
  ...resto,
})

const EVENTI = [
  ev("19:20", "sunset", "sun"),
  ev("21:00", "dark_start", "sky", { until: "2026-09-27T05:40+02:00" }),
  ev("21:00", "verdict", "verdict", { level: "go", value: 92.4 }),
  ev("22:00", "verdict", "verdict", { level: "marginal", value: 48 }),
  ev("22:00", "clouds_over", "measure", { value: 40, bound: 25 }),
  ev("22:00", "gust_peak", "measure", { value: 34.6 }),
  ev("22:00", "condensation", "measure", { value: 2.6, bound: 2.7 }),
  ev("22:12", "moon_rise", "moon", { value: 83 }),
  ev("22:30", "moon_above", "shooting", { level: "nogo", value: 0 }),
  ev("22:45", "planet_top", "planet", { value: 44, body: "jupiter" }),
]

const CON_RACCONTO = { ...NOTTE, events: EVENTI }

const righe = (dove: HTMLElement) =>
  within(within(dove).getByRole("list"))
    .getAllByRole("listitem")
    .map((r) => r.getAttribute("aria-label"))

describe("il racconto della notte", () => {
  it("dice ogni evento con l'ora, il nome e la riga sotto, in ordine, con le parole della tavola", async () => {
    conNotti(CON_RACCONTO)
    await apriMeteo()
    await scheda()
    const carta = await comeVa()

    expect(carta.textContent).toContain(
      "10 eventi, in ordine d'ora · toccane uno per portarci il grafico",
    )
    expect(righe(carta)).toEqual([
      "19:20, Tramonto",
      "21:00, Inizia il buio, buio astronomico fino alle 05:40",
      "21:00, Diventa buona, trasparenza da 92",
      "22:00, Diventa incerta, trasparenza fino a 48",
      "22:00, Nuvole oltre il 25%, al 40%",
      "22:00, Raffiche fino a 35 km/h, vento a 10 m",
      "22:00, Condensa sotto 2,7 °C, temperatura meno punto di rugiada 2,6 °C",
      "22:12, Sorge la Luna, illuminata all'83%",
      "22:30, La Luna sale sopra 0°, da qui banda stretta consigliata",
      "22:45, Giove culmina, a 44°",
    ])
  })

  it("col racconto i riquadri del buio e della Trasparenza si fanno da parte, senza restano", async () => {
    conNotti(CON_RACCONTO)
    await apriMeteo()
    await scheda()
    expect((await comeVa()).textContent).not.toContain("Trasparenza della notte")
  })

  it("il tondo del verdetto porta il segno dell'esito, gli altri sono punti", async () => {
    conNotti(CON_RACCONTO)
    await apriMeteo()
    await scheda()
    const tondi = [...(await comeVa()).querySelectorAll(".al-meteo__tondo-1")].map(
      (t) => t.textContent,
    )
    expect(tondi).toEqual(["", "", "✓", "!", "", "", "", "", "", ""])
  })

  it("toccare un evento porta il filo del grafico alla sua ora", async () => {
    conNotti(CON_RACCONTO)
    await apriMeteo()
    await scheda()
    const carta = await comeVa()
    const riga = within(carta).getByRole("listitem", { name: /Diventa incerta/ })
    fireEvent.click(riga)
    expect(riga.style.background).toBe("var(--carta-2)")
    // alla stessa ora ci sono altri eventi: si accende solo quello toccato
    expect(within(carta).getByRole("listitem", { name: /Nuvole oltre/ }).style.background).not.toBe(
      "var(--carta-2)",
    )
  })

  it("sul telefono parte dai momenti che contano, e un tocco apre la notte intera", async () => {
    conNotti(CON_RACCONTO)
    await apriMeteoTelefono()
    await scheda()
    const carta = await comeVa()

    expect(carta.textContent).toContain("I momenti che contano · 5 di 10")
    expect(righe(carta)).toHaveLength(5)
    const bottone = within(carta).getByRole("button", { name: /Tutta la notte, ora per ora · 10/ })
    expect(bottone.getAttribute("aria-expanded")).toBe("false")
    fireEvent.click(bottone)
    expect(righe(carta)).toHaveLength(10)
    expect(
      within(carta)
        .getByRole("button", { name: /Solo i momenti che contano/ })
        .getAttribute("aria-expanded"),
    ).toBe("true")
  })
})
