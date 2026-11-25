// @vitest-environment jsdom
/**
 * Il **treno ottico** nel dettaglio del setup (`src/TrenoOttico.tsx`, tavola v82 63-66): gli strumenti
 * che i conti leggono (`pieces`), strumento e pillola che si accendono insieme, il tocco che
 * apre lo strumento fra i componenti; sul telefono il numero e la legenda.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { TrenoOttico, trenoDelSetup } from "../src/TrenoOttico"
import { SETUP, NUMERI, OTTICA, apriAttrezzatura, attrezzatura } from "./attrezzatura-banco"
import { pulisci } from "./banco"
import { impronta } from "./impronta"

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
    rigs: [{ ...SETUP, camera_id: CAMERA.id, numbers: pieces ? NUMERI : null, pieces }],
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

  it("strumento e pillola si accendono insieme, gli altri si spengono", async () => {
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

  it("toccare uno strumento lo apre fra i componenti", async () => {
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

  it("dagli strumenti del setup: la guida fuori asse o il cercatore al suo posto, la camera a colori", () => {
    const s = (id: number, kind: string, extra: Record<string, unknown> = {}) => ({
      ...OTTICA, id, kind, name: `p${id}`, aperture_mm: null, focal_mm: null, ...extra,
    }) // prettier-ignore
    const pagina = {
      instruments: [
        s(1, "telescope", { optical_design: "sct", aperture_mm: 203, focal_mm: 2032 }),
        s(2, "focuser"),
        s(3, "reducer"),
        s(4, "oag", { thickness_mm: 16.5 }),
        s(5, "spacer", { thickness_mm: 10 }),
        s(6, "filter_wheel", { slots: 7 }),
        s(7, "camera", { camera_type: "color" }),
        s(8, "camera", { camera_type: "mono" }),
        s(9, "guide_scope", { aperture_mm: 30, focal_mm: 120 }),
      ],
    } as unknown as Parameters<typeof trenoDelSetup>[0]
    const setup = (guide: number | null, camera: number) =>
      ({ pieces: { ...PEZZI, optics: 1, focuser: 2, reducer: 3, guide, wheel: 6, camera,
        guide_camera: 8, spacers: [5, 99] } }) as unknown as Parameters<typeof trenoDelSetup>[1] // prettier-ignore
    const conOag = trenoDelSetup(pagina, setup(4, 7))!
    expect(conOag).toEqual({
      ott: { id: 1, nome: "p1", ruolo: "optics", schema: "sct", apertura: 203, focale: 2032,
        spessore: OTTICA.thickness_mm, posizioni: OTTICA.slots, aColori: false }, // prettier-ignore
      foc: expect.objectContaining({ id: 2, ruolo: "focuser" }),
      rid: expect.objectContaining({ id: 3, ruolo: "reducer" }),
      oag: expect.objectContaining({ id: 4, ruolo: "oag", spessore: 16.5 }),
      gs: undefined,
      dist: [expect.objectContaining({ id: 5, ruolo: "spacer", spessore: 10 })],
      ruota: expect.objectContaining({ id: 6, ruolo: "filter_wheel", posizioni: 7 }),
      cam: expect.objectContaining({ id: 7, ruolo: "camera", aColori: true }),
      camG: expect.objectContaining({ id: 8, ruolo: "guide_camera", aColori: false }),
    })
    const conCercatore = trenoDelSetup(pagina, setup(9, 8))!
    expect(conCercatore.oag).toBeUndefined()
    expect(conCercatore.gs).toEqual(expect.objectContaining({ id: 9, ruolo: "guide_scope" }))
    expect(conCercatore.cam?.aColori).toBe(false)
  })

  it("ogni tratto, filo e pillola resta quello visto a schermo, spento e acceso", () => {
    // gli strumenti singoli li dicono i test sopra, l'impronta del markup ferma il resto
    const T = {
      ott: { id: 1, nome: "TS 130 APO", ruolo: "optics" as const, apertura: 130, focale: 910 },
      foc: { id: 2, nome: "EAF", ruolo: "focuser" as const },
      oag: { id: 7, nome: "OAG-L", ruolo: "oag" as const, spessore: 16.5 },
      dist: [{ id: 5, nome: "D10", ruolo: "spacer" as const, spessore: 10 }],
      cam: { id: 4, nome: "ASI2600MM", ruolo: "camera" as const },
      camG: { id: 6, nome: "ASI120", ruolo: "guide_camera" as const },
    }
    const visti: string[] = []
    const vai: number[] = []
    for (const formato of ["desktop", "telefono"] as const) {
      const { container, unmount } = render(
        <TrenoOttico treno={T} nome="Il grande" formato={formato} onVai={(id) => vai.push(id)} />,
      )
      visti.push(impronta(container.innerHTML))
      const pezzo = screen.getByRole("button", { name: "distanziale: D10" })
      fireEvent.focus(pezzo)
      visti.push(impronta(container.innerHTML))
      fireEvent.keyDown(pezzo, { key: "Enter" })
      fireEvent.keyDown(pezzo, { key: " " })
      fireEvent.keyDown(pezzo, { key: "a" })
      fireEvent.blur(pezzo)
      expect(impronta(container.innerHTML)).toBe(visti[visti.length - 2])
      unmount()
    }
    expect(vai).toEqual([5, 5, 5, 5])
    expect(visti).toEqual(["31fad9b6", "9044e6c1", "de5c82ae", "956efc45"])
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
