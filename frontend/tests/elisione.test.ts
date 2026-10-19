/**
 * L'articolo davanti a una percentuale si elide dove il numero si legge con vocale: otto, undici,
 * ottanta (glossario, `illumination_pct`).
 */
import { describe, expect, it } from "vitest"

import { t } from "../src/i18n"

describe("l'articolo davanti a una percentuale", () => {
  it.each([
    [8, "illuminata all'8%"],
    [11, "illuminata all'11%"],
    [83, "illuminata all'83%"],
    [50, "illuminata al 50%"],
    [100, "illuminata al 100%"],
  ])("con %i si scrive come si legge", (pct, atteso) => {
    expect(t("tonight.illuminated", { pct })).toBe(atteso)
  })

  it("vale per ogni articolo, anche nel mezzo della frase", () => {
    expect(t("dashboard.moon.legend", { pct: 8, ore: 4 })).toContain("Luna sotto l'8%")
    expect(t("dashboard.moon.day", { giorno: "8 settembre", pct: 85, durata: "1 h" })).toBe(
      "8 settembre: Luna all'85%, 1 h di buio senza Luna",
    )
  })

  it("110 si legge centodieci, e l'articolo resta intero", () => {
    expect(t("tonight.illuminated", { pct: 110 })).toBe("illuminata al 110%")
  })
})
