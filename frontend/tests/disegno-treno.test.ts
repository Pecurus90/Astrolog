/**
 * Il treno ottico: l'esploso in vista isometrica (tavola v82, `treno` 447-548).
 *
 * I numeri attesi sono quelli che la funzione della consegna disegna sugli stessi pezzi (eseguita
 * fuori dal browser, 14/11/2026): se i nostri divergono, a schermo c'e' un treno diverso.
 */
import { describe, expect, it } from "vitest"

import {
  disegnoDelTreno,
  pezziDelTreno,
  type Pezzo,
  type Ruolo,
  type Treno,
} from "../src/disegnoDelTreno"

let id = 0
const pz = (nome: string, ruolo: Ruolo, scheda: Partial<Pezzo> = {}): Pezzo => ({
  id: ++id,
  nome,
  ruolo,
  ...scheda,
})

const RIFRATTORE: Treno = {
  ott: pz("TS 130", "optics", { apertura: 130, focale: 910 }),
  foc: pz("EAF", "focuser"),
  rid: pz("Rid 0,8x", "reducer"),
  oag: pz("OAG-L", "oag", { spessore: 16.5 }),
  dist: [pz("D10", "spacer", { spessore: 10 })],
  ruota: pz("EFW 7x36", "filter_wheel", { posizioni: 7, spessore: 20 }),
  cam: pz("ASI2600MM", "camera"),
  camG: pz("ASI120", "guide_camera"),
}
const NEWTON: Treno = {
  ott: pz("Newton 200", "optics", { schema: "newtonian", apertura: 200, focale: 800 }),
  dist: [],
  cam: pz("ASI533MC", "camera", { aColori: true }),
  gs: pz("Cercatore", "guide_scope", { apertura: 30, focale: 120 }),
  camG: pz("ASI120", "guide_camera"),
}
const SCT: Treno = {
  ott: pz("C8", "optics", { schema: "sct", apertura: 203, focale: 2032 }),
  foc: pz("EAF", "focuser"),
  dist: [],
  cam: pz("ASI2600MM", "camera"),
}

const vista = (T: Treno, w: number, tel: boolean) => {
  const d = disegnoDelTreno(T, w, tel)
  const v = d.vista
  const a = (l: (typeof d.su)[number]) =>
    `${l.pezzo.nome}@${(((l.x - v.x) / v.w) * 100).toFixed(3)}`
  return {
    viewBox: [v.x, v.y, v.w, v.h].map((n) => n.toFixed(3)).join(" "),
    maxWidth: d.larghezzaMassima,
    asse: d.asse,
    ordine: d.gruppi.map((g) => g.pezzo.nome),
    primi: d.gruppi.map((g) => `${g.tratti.length}:${g.tratti[0]!.d.slice(0, 40)}`),
    su: d.su.map(a),
    giu: d.giu.map(a),
  }
}

describe("il treno ottico disegnato come nella tavola", () => {
  it("un rifrattore col riduttore, la guida fuori asse, un distanziale e la ruota", () => {
    expect(vista(RIFRATTORE, 700, false)).toEqual({
      viewBox: "-81.983 -579.989 951.192 700.837",
      maxWidth: 543,
      asse: "M-28.3 16.3L857.2 -494.9",
      ordine: ["ASI2600MM", "EFW 7x36", "D10", "OAG-L", "Rid 0,8x", "ASI120", "EAF", "TS 130"],
      primi: [
        "12:M743.4 -464.3L743.6 -468.1L744.1 -471.7L",
        "3:M643.7 -479.4L644.1 -487.6L645.3 -495.2L",
        "2:M659.2 -405.1L659.4 -407.8L659.8 -410.3L",
        "5:M642.4 -459.7L642.5 -460.4L642.7 -461.1L",
        "5:M572.6 -360.0L572.8 -363.2L573.3 -366.2L",
        "2:M635.4 -518.5L635.5 -519.7L635.9 -520.8L",
        "3:M494.8 -337.9L494.8 -370.6L525.9 -352.6L",
        "24:M165.5 -33.5L165.5 -41.7L188.2 -28.6L188",
      ],
      su: ["EAF@46.250", "Rid 0,8x@57.600", "ASI120@70.643", "D10@80.864", "ASI2600MM@92.779"],
      giu: ["TS 130@36.861", "OAG-L@77.312", "EFW 7x36@89.791"],
    })
  })

  it("sul telefono le pillole portano il numero, piu' strette, e il disegno e' alto 300", () => {
    const tel = vista(RIFRATTORE, 330, true)
    expect(tel.maxWidth).toBe(407)
    expect(tel.su).toEqual([
      "EAF@51.818",
      "Rid 0,8x@62.727",
      "ASI120@73.636",
      "D10@84.545",
      "ASI2600MM@95.455",
    ])
    expect(tel.giu).toEqual(["TS 130@36.861", "OAG-L@77.312", "EFW 7x36@88.221"])
  })

  it("un Newton porta il treno in verticale sul focheggiatore, la guida sopra il tubo", () => {
    expect(vista(NEWTON, 700, false)).toEqual({
      viewBox: "-102.489 -447.790 725.411 595.108",
      maxWidth: 488,
      asse: "M-28.3 16.3L562.9 -325.0",
      ordine: ["Newton 200", "ASI120", "Cercatore", "ASI533MC"],
      primi: [
        "21:M66.8 52.1L66.8 43.9L89.4 57.0L89.4 65.2",
        "2:M314.2 -328.4L314.3 -330.0L314.6 -331.5L",
        "13:M221.5 -225.0L221.5 -249.5L230.0 -244.6L",
        "2:M44.3 -290.6L44.5 -293.1L45.2 -295.6L46.",
      ],
      su: ["Cercatore@49.552", "Newton 200@65.416", "ASI120@79.587"],
      giu: ["ASI533MC@25.607"],
    })
  })

  it("uno Schmidt-Cassegrain ha la cella posteriore e nessun paraluce", () => {
    expect(vista(SCT, 700, false)).toEqual({
      viewBox: "-104.964 -371.473 602.233 521.986",
      maxWidth: 461,
      asse: "M-28.3 16.3L485.3 -280.2",
      ordine: ["ASI2600MM", "EAF", "C8"],
      primi: [
        "12:M371.4 -249.6L371.6 -253.4L372.2 -256.9L",
        "3:M288.7 -273.2L288.7 -305.9L319.8 -287.9L",
        "21:M33.9 73.9L33.9 65.8L56.5 78.8L56.5 87.0",
      ],
      su: ["EAF@70.771", "ASI2600MM@84.978"],
      giu: ["C8@43.863"],
    })
  })

  it("i nomi che entrano restano nomi; quelli lunghi dei driver passano ai numeri (Marco, 14/11)", () => {
    expect(disegnoDelTreno(RIFRATTORE, 700, false).coiNumeri).toBe(false)
    const lunghi: Treno = {
      ...RIFRATTORE,
      foc: pz("ASCOM ToupTek AAF Focuser", "focuser"),
      rid: pz("ASCOM Reducer Flattener 0,8x", "reducer"),
      camG: pz("ASCOM ZWO ASI120MM Mini Guide", "guide_camera"),
      dist: [pz("ASCOM Spacer Ring 10 mm", "spacer", { spessore: 10 })],
      cam: pz("ASCOM ZWO ASI2600MM Pro Camera", "camera"),
    }
    const d = disegnoDelTreno(lunghi, 700, false)
    expect(d.coiNumeri).toBe(true)
    for (const l of [...d.su, ...d.giu])
      expect(l.x - l.larghezza / 2).toBeGreaterThanOrEqual(d.vista.x)
  })

  it("i numeri della legenda seguono il treno dall'ottica alla camera di guida", () => {
    expect(pezziDelTreno(RIFRATTORE).map((p) => p.nome)).toEqual([
      "TS 130",
      "EAF",
      "Rid 0,8x",
      "OAG-L",
      "D10",
      "EFW 7x36",
      "ASI2600MM",
      "ASI120",
    ])
    expect(disegnoDelTreno(RIFRATTORE, 330, true).legenda.map((l) => l.numero)).toEqual([
      1, 2, 3, 4, 5, 6, 7, 8,
    ])
  })
})
