// @vitest-environment jsdom
/**
 * La **volta** della Dashboard (tavola v37, `as-volta`): la notte dal tramonto all'alba coi colori
 * del crepuscolo, la Luna, i quattro pianeti e la coltre delle nuvole. Le altezze, la finestra e gli
 * istanti arrivano da `/tonight`; le nuvole dalle ore del meteo. Qui si disegna e basta.
 */
import { screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { pulisci } from "./banco"
import { NOTTE, STANOTTE_CON_LUNA, montaDashboard } from "./dashboard-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

/** Un istante della notte del 26 settembre a Vicenza, `minuti` dopo mezzogiorno. */
function alle(minuti: number): string {
  const tot = 12 * 60 + minuti
  const giorno = 26 + Math.floor(tot / 1440)
  const hh = String(Math.floor((tot % 1440) / 60)).padStart(2, "0")
  const mm = String(tot % 60).padStart(2, "0")
  return `2026-09-${giorno}T${hh}:${mm}:00+02:00`
}

/** Una curva ogni 15 minuti per ventiquattro ore, con l'altezza che `quota` da' a ogni minuto. */
const curva = (quota: (minuti: number) => number) =>
  Array.from({ length: 97 }, (_, i) => ({ at: alle(i * 15), altitude_deg: quota(i * 15) }))

const SORGE = 11 * 60 + 40 // 23:40
const VOLTA = {
  ...STANOTTE_CON_LUNA["/api/v1/tonight"].corpo,
  moon: { ...STANOTTE_CON_LUNA["/api/v1/tonight"].corpo.moon, track: curva((m) => (m - SORGE) / 12) },
  sky_bands: [
    { starts_at: alle(0), ends_at: alle(441), kind: "day" },
    { starts_at: alle(441), ends_at: alle(476), kind: "civil" },
    { starts_at: alle(476), ends_at: alle(528), kind: "dark" },
    { starts_at: alle(528), ends_at: alle(1051), kind: "dark" },
    { starts_at: alle(1051), ends_at: alle(1155), kind: "civil" },
    { starts_at: alle(1155), ends_at: alle(1440), kind: "day" },
  ],
  // tramonto 19:21, alba 07:15: dalle 18:30 alle 07:30
  chart: { starts_at: alle(390), ends_at: alle(1170), dark_from: alle(528), dark_until: alle(1051) },
  planets: [
    { key: "saturn", track: curva(() => 30) },
    { key: "jupiter", track: curva((m) => (m - 14 * 60) / 10) },
    { key: "mars", track: curva(() => -10) },
    { key: "venus", track: curva(() => -20) },
  ],
}

async function apriVolta(stanotte: Record<string, unknown> = {}, previsione: Record<string, unknown> = {}) {
  await montaDashboard({ altre: { "/api/v1/tonight": { stato: 200, corpo: { ...VOLTA, ...stanotte } } }, previsione })
  return screen.findByRole("img", { name: /^Stanotte dal tramonto all'alba/ })
}

describe("la volta della Dashboard", () => {
  it("dice la notte in una frase: quando comincia il buio e quando sorge la Luna", async () => {
    const tela = await apriVolta()

    expect(tela.getAttribute("aria-label")).toBe("Stanotte dal tramonto all'alba: buio dalle 20:48, Luna dalle 23:40")
    expect(tela.classList.contains("as-volta__tela--coperta")).toBe(false)
  })

  it("le ore intere dalle 19 alle 07, a meta' delle colonne", async () => {
    const tela = await apriVolta()

    const ore = [...tela.querySelectorAll(".as-volta__ora")].map((o) => o.textContent)
    expect(ore).toEqual(["19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05", "06", "07"])
  })

  it("senza progetti mostra il sistema solare, senza scelta: un pianeta mai sorto non ha curva", async () => {
    const tela = await apriVolta()

    const figura = tela.closest(".as-volta")
    expect(figura?.getAttribute("data-mostra")).toBe("sistema")
    expect(screen.queryByRole("tablist", { name: "Cosa mostra la volta" })).toBeNull()
    expect(tela.querySelector("path.as-volta__curva--saturno:not(.as-volta__curva--alone)")).toBeTruthy()
    expect(tela.querySelector("path.as-volta__curva--giove:not(.as-volta__curva--alone)")).toBeTruthy()
    expect(tela.querySelector("path.as-volta__curva--marte")).toBeNull()
    expect(tela.querySelector("path.as-volta__curva--luna")).toBeTruthy()
    const scritte = [...tela.querySelectorAll(".as-volta__scritta")].map((s) => s.textContent)
    expect(scritte).toEqual(expect.arrayContaining(["Saturno", "Giove", "Luna 62%", "Luna 23:40", "fine del buio 05:31"]))
    expect(scritte).not.toContain("Marte")
  })

  it("una curva sotto l'orizzonte non si disegna: comincia dove il pianeta sorge", async () => {
    const tela = await apriVolta()

    // Giove sorge alle 02:00, a 7,5 ore dalle 18:30 su 13: il tratto parte da li', sull'orizzonte
    const d = tela.querySelector("path.as-volta__curva--giove:not(.as-volta__curva--alone)")?.getAttribute("d") ?? ""
    const [x, y] = d.slice(1).split(/[ L]/)[0]?.split(",").map(Number) ?? []
    expect(x).toBeCloseTo((7.5 / 13) * 1300, 0)
    expect(y).toBeCloseTo(382, 0)
  })

  it("una Luna gia' alta al tramonto schiarisce il cielo dal primo istante", async () => {
    // primo quarto: sorge alle 14:00, fuori dalla volta, ed e' a 40 gradi alle 18:30
    const moon = { ...VOLTA.moon, rise: alle(120), track: curva((m) => 40 - (m - 390) / 10) }
    const tela = await apriVolta({ moon })

    const chiarore = tela.querySelector("linearGradient[id$='-luna']")
    const prima = Number(chiarore?.querySelector("stop")?.getAttribute("stop-opacity"))
    expect(prima).toBeCloseTo(0.4 * (moon.illumination_pct / 100) * Math.sin((40 * Math.PI) / 180), 3)
    expect(tela.querySelector("rect[fill$='-luna)']")?.getAttribute("x")).toBeNull()
  })

  it("la notte senza ore serene stende la coltre e lo dice", async () => {
    const tela = await apriVolta({}, { nights: [{ ...NOTTE, usable_hours: 0, verdict: "nogo", usable_since: null, usable_until: null }] })

    expect(tela.classList.contains("as-volta__tela--coperta")).toBe(true)
    expect(tela.getAttribute("aria-label")).toBe("Stanotte dal tramonto all'alba: coperto tutta la notte, buio dalle 20:48, Luna dalle 23:40")
  })

  it("sul telefono la legenda al posto dei nomi, coi quattro pianeti e la Luna", async () => {
    await montaDashboard({ altre: { "/api/v1/tonight": { stato: 200, corpo: VOLTA } }, larga: 390 })

    const legenda = await screen.findByLabelText("Le curve: tocca per evidenziarne una")
    expect(legenda.textContent).toBe("SaturnoGioveMarteVenereLuna 62%")
  })
})
