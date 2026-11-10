// @vitest-environment jsdom
/**
 * La finestra del Riepilogo porta la radice della tavola v77 (`al-c-riepilogo__blocco-1` col
 * `data-formato`): le regole del telefono del foglio si appendono li'.
 */
import { cleanup, render } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { FinestraRiepilogo } from "../src/RiepilogoComune"

afterEach(cleanup)

describe("la finestra del Riepilogo", () => {
  it.each(["desktop", "telefono"] as const)(
    "sul %s il contenuto sta sotto la radice col formato",
    (f) => {
      const { container } = render(
        <FinestraRiepilogo aria="prova" formato={f} onChiudi={() => undefined}>
          <span className="dentro" />
        </FinestraRiepilogo>,
      )
      const radice = container.querySelector(`.al-c-riepilogo__blocco-1[data-formato="${f}"]`)
      expect(radice?.querySelector(".dentro")).toBeTruthy()
    },
  )
})
