/**
 * Il singolare dei conti lo sceglie `t()`, in una casa sola: se il numero `n` e' 1 e la chiave ha
 * la sua forma `.one`, usa quella.
 */
import { describe, expect, it } from "vitest"

import { numero, t } from "../src/i18n"

describe("il singolare dei conti", () => {
  it("con 1 si legge al singolare, con 2 al plurale", () => {
    expect(t("gear.nights", { n: 1 })).toBe("1 notte")
    expect(t("gear.nights", { n: 2 })).toBe("2 notti")
  })

  it("vale anche col numero gia' scritto per lo schermo", () => {
    expect(t("review.count", { n: numero(1) })).toBe("1 cosa da confermare")
    expect(t("review.count", { n: numero(1000) })).toBe(`${numero(1000)} cose da confermare`)
  })

  it("una chiave senza forma singolare resta com'e'", () => {
    // `n` qui non e' un conto: la regola non deve prenderle
    expect(t("site.bortle", { n: 1 })).toBe("Bortle 1")
    expect(t("wizard.passo", { n: 1, tot: 3 })).toBe("Passo 1 di 3")
  })

  it("le frasi con un conto solo si leggono al singolare", () => {
    expect(t("review.applied", { n: 1, pose: 3 })).toBe("applicata 1 risposta, 3 frame rimessi in coda")
    expect(t("weather.usable.dark", { n: 1, su: 8 })).toBe("1 ora utile su 8 di buio.")
    expect(t("settings.readings.duplicates", { n: 1 })).toBe("1 doppione")
    expect(t("nights.waiting.review", { n: 1 })).toMatch(/^1 frame aspetta una tua risposta/)
  })
})
