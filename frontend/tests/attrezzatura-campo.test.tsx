// @vitest-environment jsdom
/**
 * La colonna destra del **dettaglio di un setup** (`src/CampoDelSetup.tsx`, tavola v82): il Campo
 * col confronto e la Luna, i Dati del setup con le pillole, l'anello dei Filtri. Riquadri, Luna e
 * fette arrivano dall'API: qui si prova che si disegnano dove e come la tavola li mette.
 */
import { screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { anello, tinte } from "../src/anelloDeiFiltri"
import { CORREDO, NUMERI, apriAttrezzatura, attrezzatura, campo } from "./attrezzatura-banco"
import { pulisci } from "./banco"

afterEach(pulisci)

const ALTRO = { ...CORREDO, id: 11, name: null, title: "RedCat · ASI2600MM" }
const riquadri = (img: HTMLElement) => [...img.querySelectorAll<HTMLElement>(".al-attr__strato-1")]

describe("il campo del setup", () => {
  it("solo sulla cornice: il confronto e' con la Luna sola", async () => {
    attrezzatura({ fields: [{ rig_id: 10, width_pct: 87, height_pct: 58 }], moon_pct: 13.6 })
    await apriAttrezzatura()

    const img = within(await campo()).getByRole("img", {
      name: "Il campo di Il grande a confronto con la Luna piena",
    })
    expect(riquadri(img).map((r) => [r.style.width, r.style.height])).toEqual([["87%", "58%"]])
  })

  it("il riquadro del setup aperto e' segnato, gli altri no, e le etichette si alternano", async () => {
    attrezzatura({
      rigs: [CORREDO, ALTRO],
      fields: [
        { rig_id: 11, width_pct: 87, height_pct: 87.3 },
        { rig_id: 10, width_pct: 38.8, height_pct: 38.8 },
      ],
      moon_pct: 13.6,
    })
    await apriAttrezzatura()

    const [altro, mio] = riquadri(within(await campo()).getByRole("img"))
    expect(mio.style.border).toBe("2px solid var(--accento)")
    expect(mio.style.background).toBe("color-mix(in srgb, var(--accento) 16%, transparent)")
    expect(mio.style.zIndex).toBe("2")
    expect(altro.style.border).toBe("1.5px solid var(--tenue)")
    expect(altro.style.background).toBe("none") // jsdom scrive "transparent" come "none"
    expect(altro.style.zIndex).toBe("1")
    const nome = (r: HTMLElement) => r.querySelector<HTMLElement>(".al-attr__strato-2")
    expect(nome(altro)?.style).toMatchObject({ top: "4px", bottom: "auto", fontWeight: "500" })
    expect(nome(altro)?.style.color).toBe("var(--tenue)")
    expect(nome(mio)?.style).toMatchObject({ top: "auto", bottom: "4px", fontWeight: "600" })
    expect(nome(mio)?.style.color).toBe("var(--testo)")
  })

  it("un setup fuori dalla cornice, o senza Luna, non disegna il confronto", async () => {
    attrezzatura({ fields: [{ rig_id: 11, width_pct: 87, height_pct: 58 }], moon_pct: 13.6 })
    await apriAttrezzatura()
    expect(within(await campo()).queryByRole("img")).toBeNull()
    pulisci()

    attrezzatura({ fields: [{ rig_id: 10, width_pct: 87, height_pct: 58 }], moon_pct: null })
    await apriAttrezzatura()
    expect(within(await campo()).queryByRole("img")).toBeNull()
  })

  it("con la scala ma senza i lati, scrive la scala e non i gradi", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, width_deg: null }] })
    await apriAttrezzatura()
    const testo = (await campo()).textContent ?? ""
    expect(testo).toContain("0,85 arcosecondi per pixel")
    expect(testo).not.toContain("°")
    pulisci()

    attrezzatura({ rigs: [{ ...CORREDO, height_deg: null }] })
    await apriAttrezzatura()
    expect((await campo()).textContent).not.toContain("°")
  })

  it("una scala di un arcosecondo si dice al singolare", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, scale_arcsec_px: 1 }] })
    await apriAttrezzatura()
    expect((await campo()).textContent).toContain("1,00 arcosecondo per pixel")
  })
})

describe("i dati del setup", () => {
  it("valore, pillola e riga sotto solo se ci sono; cio' che manca col punto di domanda", async () => {
    const conti = {
      ...NUMERI,
      coverage: { diagonal_mm: 28.3, circle_mm: 44, covers: false, missing: null },
    }
    attrezzatura({ rigs: [{ ...CORREDO, numbers: conti }] })
    await apriAttrezzatura()

    const dati = await screen.findByRole("region", { name: /^dati del setup$/i })
    expect(dati.textContent).toContain("Dalle schede tecniche degli strumenti.")
    const riga = (k: string) => dati.querySelector<HTMLElement>(`[data-conto="${k}"]`)
    const copertura = riga("coverage")
    expect(copertura?.querySelector(".al-attr__testo-21")?.textContent).toBe("28,3 mm")
    expect(copertura?.textContent).toContain("non copre il sensore")
    expect(copertura?.querySelector(".al-attr__testo-22")?.textContent).toBe(
      "diagonale del sensore · cerchio d'immagine 44 mm",
    )
    expect(copertura?.querySelector(".al-attr__riga-27")).toBeNull()
    const manca = riga("load")
    expect(manca?.querySelector(".al-attr__testo-21")).toBeNull()
    expect(manca?.querySelector(".al-attr__testo-22")).toBeNull()
    expect(manca?.querySelector(".al-attr__riga-27")?.textContent).toBe("?manca la montatura")
    // il rapporto focale non ha pillola: solo valore e riga sotto
    expect(riga("focal_ratio")?.children).toHaveLength(2)
  })

  it("un setup senza conti non ha la sezione", async () => {
    attrezzatura()
    await apriAttrezzatura()
    await campo()
    expect(screen.queryByRole("region", { name: /^dati del setup$/i })).toBeNull()
  })
})

const parte = (kind: string, name: string, passband: string | null, da: number | null, a: number | null) => ({
  kind, id: 3, name, frames: 1, chosen: false, passband, ring_from: da, ring_to: a,
}) // prettier-ignore

describe("l'anello dei filtri", () => {
  it("solo i filtri con fetta e banda; un filtro solo al singolare", async () => {
    attrezzatura({
      rigs: [
        {
          ...CORREDO,
          parts: [
            parte("filter", "Ha", "HA", 0, 100),
            parte("filter", "Senza banda", null, 0, 100),
            parte("filter", "Senza inizio", "OIII", null, 100),
            parte("filter", "Senza fine", "OIII", 0, null),
            parte("reducer", "Riduttore", "HA", 0, 100),
          ],
        },
      ],
    })
    await apriAttrezzatura()

    const sezione = await screen.findByRole("region", { name: /^filtri$/i })
    expect(sezione.textContent).toContain("in proporzione ai frame")
    expect([...sezione.querySelectorAll("li")].map((li) => li.textContent)).toEqual(["Ha"])
    const img = within(sezione).getByRole("img", { name: "Filtri, in proporzione ai frame: Ha" })
    expect(img.textContent).toBe("1filtro")
    expect(img.style.width).toBe("140px")
  })

  it("senza fette non c'e' la sezione", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, parts: [parte("filter", "Ha", null, 0, 100)] }] })
    await apriAttrezzatura()
    await campo()
    expect(screen.queryByRole("region", { name: /^filtri$/i })).toBeNull()
  })

  it("ogni fetta col suo colore e il filo di carta prima della successiva", () => {
    const [ha] = tinte("HA")
    const [oiii] = tinte("OIII")
    expect(
      anello(
        [
          { ring_from: 0, ring_to: 75, passband: "HA" },
          { ring_from: 75, ring_to: 100, passband: "OIII" },
        ],
        0.8,
      ),
    ).toBe(
      `conic-gradient(${ha} 0% 74.2%, var(--carta) 74.2% 75%, ${oiii} 75% 99.2%, var(--carta) 99.2% 100%)`,
    )
  })

  it("il filtro a colori in tre strisce, e una fetta piu' stretta del filo non va all'indietro", () => {
    expect(tinte("OSC")).toEqual(["var(--filtro-r)", "var(--filtro-g)", "var(--filtro-b)"])
    expect(anello([{ ring_from: 0, ring_to: 30.8, passband: "OSC" }], 0.8)).toBe(
      "conic-gradient(var(--filtro-r) 0% 10%, var(--filtro-g) 10% 20%, var(--filtro-b) 20% 30%," +
        " var(--carta) 30% 30.8%)",
    )
    const [ha] = tinte("HA")
    expect(anello([{ ring_from: 50, ring_to: 50.5, passband: "HA" }], 0.8)).toBe(
      `conic-gradient(${ha} 50% 50%, var(--carta) 50% 50.5%)`,
    )
  })
})
