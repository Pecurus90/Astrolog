// @vitest-environment jsdom
/**
 * La carta **Campionamento** del Meteo (passo 14, tavola v82 Meteo.dc.html:80-83 e 152): una
 * casella per setup con la scala, il campionamento col seeing previsto e, decisione di Marco del
 * 24/11/2026, il seeing rispetto al limite del setup. I giudizi li scrive il backend; qui si dicono.
 */
import { screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { pulisci } from "./banco"
import { NOTTE, apriMeteo, apriMeteoTelefono, conNotti, misura, scheda } from "./meteo-banco"

afterEach(pulisci)

const setup = (resto: Record<string, unknown> = {}) => ({
  rig_id: 1,
  name: "Notte in quota",
  optics: "FRA400",
  camera: "ASI2600MM",
  scale_arcsec_px: 1.94,
  seeing_from: 3.88,
  seeing_to: 5.82,
  sampling: "ideal",
  floor_arcsec: 2.1,
  floor_missing: null,
  seeing_level: "marginal",
  ...resto,
})

const C8 = setup({
  rig_id: 2,
  name: null,
  optics: "C8",
  camera: "ASI533MC",
  scale_arcsec_px: 0.5,
  seeing_from: 1,
  seeing_to: 1.5,
  sampling: "over",
  floor_arcsec: null,
  floor_missing: { kind: "optics", field: "aperture_mm" },
  seeing_level: null,
})

const conSeeing = (setups: unknown[]) => ({
  ...NOTTE,
  measures: NOTTE.measures.map((m) =>
    m.code === "seeing" ? misura("seeing", { value: 4.2, peak: 4.6, known_hours: 3 }) : m,
  ),
  setups,
})

const campionamento = () => screen.getByRole("region", { name: "Campionamento" })

describe("la carta Campionamento", () => {
  it("dice il seeing previsto e per ogni setup scala, campionamento, seeing e limite", async () => {
    conNotti(conSeeing([setup(), C8]))
    await apriMeteo()
    await scheda()
    const carta = campionamento()
    expect(carta.textContent).toContain("dei setup, col seeing previsto di 4,2″")
    const quota = within(carta).getByText("Notte in quota").parentElement as HTMLElement
    expect(quota.textContent).toContain("1,94″/px")
    expect(quota.textContent).toContain("✓ ottimo")
    expect(quota.textContent).toContain("! seeing incerto")
    expect(quota.textContent).toContain("ottimo con seeing fra 3,9 e 5,8″")
    expect(quota.textContent).toContain("limite del setup 2,1″")
  })

  it("un setup senza nome si chiama ottica e camera, e senza apertura dice cosa manca", async () => {
    conNotti(conSeeing([C8]))
    await apriMeteo()
    await scheda()
    const casella = within(campionamento()).getByText("C8 · ASI533MC").parentElement as HTMLElement
    expect(casella.textContent).toContain("! sovracampionato")
    expect(casella.textContent).toContain("seeing: manca l'apertura dell'ottica")
    expect(casella.textContent).not.toContain("seeing incerto")
  })

  it("senza setup giudicati la carta non c'e'", async () => {
    conNotti(conSeeing([]))
    await apriMeteo()
    await scheda()
    expect(screen.queryByRole("region", { name: "Campionamento" })).toBeNull()
  })

  it("sul telefono sta in fondo alle altre misure", async () => {
    conNotti(conSeeing([setup({ seeing_level: "nogo" })]))
    await apriMeteoTelefono()
    await scheda()
    const fondo = screen.getByText("col seeing previsto di 4,2″").parentElement as HTMLElement
    expect(fondo.textContent).toContain("1,94″/px · ottimo con seeing fra 3,9 e 5,8″")
    expect(fondo.textContent).toContain("✕ seeing non adatto")
  })
})
