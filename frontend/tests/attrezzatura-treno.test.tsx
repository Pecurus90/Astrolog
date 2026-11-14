// @vitest-environment jsdom
/**
 * Il **treno ottico** nel dettaglio del setup (`src/TrenoOttico.tsx`, tavola v82 63-66): i pezzi
 * che i conti leggono (`pieces`), pezzo e pillola che si accendono insieme, il tocco che
 * apre il pezzo fra i componenti; sul telefono il numero e la legenda.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { TrenoOttico } from "../src/TrenoOttico"
import { CORREDO, NUMERI, OTTICA, apriAttrezzatura, attrezzatura } from "./attrezzatura-banco"
import { pulisci } from "./banco"

afterEach(pulisci)

const CAMERA = {
  ...OTTICA,
  id: 4,
  kind: "camera",
  name: "ASI2600MM",
  aperture_mm: null,
  focal_mm: null,
}
const DIST = { ...OTTICA, id: 5, kind: "spacer", name: "D10", thickness_mm: 10, aperture_mm: null }
const PEZZI = {
  optics: OTTICA.id, camera: CAMERA.id, reducer: null, guide: null, guide_camera: null,
  wheel: null, focuser: null, mount: null, spacers: [DIST.id],
} // prettier-ignore

function conTreno(pieces: Record<string, unknown> | null = PEZZI) {
  attrezzatura({
    instruments: [OTTICA, CAMERA, DIST],
    rigs: [{ ...CORREDO, camera_id: CAMERA.id, numbers: pieces ? NUMERI : null, pieces }],
  })
}

const treno = () => screen.findByRole("region", { name: /^treno ottico$/i })

describe("il treno ottico", () => {
  it("disegna ottica, distanziale e camera, con la nota della tavola", async () => {
    conTreno()
    await apriAttrezzatura()
    const sezione = await treno()
    expect(
      within(sezione).getByText("Schema non in scala. Seleziona uno strumento per aprirlo."),
    ).toBeTruthy()
    const disegno = within(sezione).getByRole("group", {
      name: "Treno ottico di Il grande, schema non in scala",
    })
    const pezzi = within(disegno)
      .getAllByRole("button")
      .map((b) => b.getAttribute("aria-label"))
    expect(pezzi.sort()).toEqual(["camera: ASI2600MM", "distanziale: D10", "ottica: TS 130 APO"])
    const pillole = within(sezione)
      .getAllByRole("link")
      .map((a) => a.textContent)
    expect(pillole.sort()).toEqual(["ASI2600MM", "D10", "TS 130 APO"])
  })

  it("pezzo e pillola si accendono insieme, gli altri si spengono", async () => {
    conTreno()
    await apriAttrezzatura()
    const sezione = await treno()
    const pillola = within(sezione).getByRole("link", { name: "distanziale: D10, apri" })
    fireEvent.mouseEnter(pillola)
    const pezzo = within(sezione).getByRole("button", { name: "distanziale: D10" })
    const ottica = within(sezione).getByRole("button", { name: "ottica: TS 130 APO" })
    expect(pezzo.getAttribute("stroke")).toBe("var(--accento)")
    expect(ottica.getAttribute("opacity")).toBe("0.3")
    expect(pillola.style.background).toBe("var(--scelta)")
    fireEvent.mouseLeave(pillola)
    expect(ottica.getAttribute("opacity")).toBe("1")
  })

  it("toccare un pezzo lo apre fra i componenti", async () => {
    conTreno()
    await apriAttrezzatura()
    const sezione = await treno()
    fireEvent.click(within(sezione).getByRole("button", { name: "distanziale: D10" }))
    await waitFor(() => expect(window.location.search).toContain(`pezzo=strumento-${DIST.id}`))
  })

  it("senza ottica, o prima che i conti siano scritti, il treno non c'e'", async () => {
    conTreno({ ...PEZZI, optics: null })
    await apriAttrezzatura()
    await screen.findByRole("region", { name: /^parti$/i })
    expect(screen.queryByRole("region", { name: /^treno ottico$/i })).toBeNull()
    pulisci()
    conTreno(null)
    await apriAttrezzatura()
    await screen.findByRole("region", { name: /^parti$/i })
    expect(screen.queryByRole("region", { name: /^treno ottico$/i })).toBeNull()
  })

  it("sul telefono le pillole portano il numero e sotto c'e' la legenda da 44 px", () => {
    const T = {
      ott: { id: 1, nome: "TS 130 APO", ruolo: "optics" as const, apertura: 130, focale: 910 },
      dist: [{ id: 5, nome: "D10", ruolo: "spacer" as const, spessore: 10 }],
      cam: { id: 4, nome: "ASI2600MM", ruolo: "camera" as const },
    }
    render(<TrenoOttico treno={T} nome="Il grande" formato="telefono" onVai={() => {}} />)
    const sezione = screen.getByRole("region", { name: /^treno ottico$/i })
    const voci = within(within(sezione).getByRole("list")).getAllByRole("link")
    expect(voci.map((a) => a.textContent)).toEqual(["1TS 130 APO", "2D10", "3ASI2600MM"])
    expect(voci.every((a) => a.style.minHeight === "44px")).toBe(true)
    const pillole = within(sezione)
      .getAllByRole("link", { name: /, apri$/ })
      .map((a) => a.textContent)
    expect(pillole.sort()).toEqual(["1", "2", "3"])
  })

  it("sul desktop i nomi che non entrano passano al numero, e la legenda li dice interi", () => {
    const T = {
      ott: { id: 1, nome: "TS 130 APO", ruolo: "optics" as const, apertura: 130, focale: 910 },
      foc: { id: 2, nome: "ASCOM ToupTek AAF Focuser", ruolo: "focuser" as const },
      rid: { id: 3, nome: "ASCOM Reducer Flattener 0,8x", ruolo: "reducer" as const },
      dist: [{ id: 5, nome: "ASCOM Spacer Ring 10 mm", ruolo: "spacer" as const, spessore: 10 }],
      cam: { id: 4, nome: "ASCOM ZWO ASI2600MM Pro Camera", ruolo: "camera" as const },
      camG: { id: 6, nome: "ASCOM ZWO ASI120MM Mini Guide", ruolo: "guide_camera" as const },
      oag: { id: 7, nome: "ASCOM Off-Axis Guider Large", ruolo: "oag" as const, spessore: 16.5 },
      ruota: { id: 8, nome: "ASCOM ZWO EFW 7x36 Wheel", ruolo: "filter_wheel" as const },
    }
    render(<TrenoOttico treno={T} nome="Il grande" formato="desktop" onVai={() => {}} />)
    const sezione = screen.getByRole("region", { name: /^treno ottico$/i })
    const voci = within(within(sezione).getByRole("list")).getAllByRole("link")
    expect(voci.map((a) => a.textContent)).toContain("7ASCOM ZWO ASI2600MM Pro Camera")
    const pillole = within(sezione).getAllByRole("link", { name: /, apri$/ })
    expect(pillole.every((a) => /^\d$/.test(a.textContent ?? ""))).toBe(true)
  })
})
