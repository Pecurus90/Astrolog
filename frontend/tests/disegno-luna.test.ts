/**
 * La geometria del piede: il disco della fase e la curva della notte.
 *
 * I tracciati attesi sono quelli che il fornitore ha disegnato nella sua consegna: se i nostri
 * divergono, a schermo si vedrebbe una luna diversa da quella approvata.
 */
import { describe, expect, it } from "vitest"

import { curvaDellaNotte, tracciatoDellaLuna } from "../src/disegnoDellaLuna"

describe("il disco della fase", () => {
  it("disegna le lune che il fornitore ha disegnato, alla cifra", () => {
    // Gibbosa crescente 60%, gibbosa calante 85% e 98%, falce calante 38%: quattro tracciati
    // copiati dalla pagina consegnata. Sono il banco di prova della formula.
    expect(tracciatoDellaLuna(60, true)).toBe(
      "M 0 -10 A 10 10 0 0 1 0 10 A 2.00 10 0 0 1 0 -10 Z",
    )
    expect(tracciatoDellaLuna(85, false)).toBe(
      "M 0 -10 A 10 10 0 0 0 0 10 A 7.00 10 0 0 0 0 -10 Z",
    )
    expect(tracciatoDellaLuna(98, false)).toBe(
      "M 0 -10 A 10 10 0 0 0 0 10 A 9.60 10 0 0 0 0 -10 Z",
    )
    expect(tracciatoDellaLuna(38, false)).toBe(
      "M 0 -10 A 10 10 0 0 0 0 10 A 2.40 10 0 0 1 0 -10 Z",
    )
  })

  it("la luna nuova non ha niente di illuminato, e non e un disco vuoto", () => {
    // Zero e' una misura vera che vale zero: il cerchio spento resta, il tracciato non si
    // disegna. Un tracciato largo zero sarebbe una riga sottile in mezzo al disco.
    expect(tracciatoDellaLuna(0, true)).toBeNull()
  })

  it("la luna piena e un disco intero, e i due archi girano nello stesso verso", () => {
    // E' il caso in cui uno scambio di flag e' piu' facile e si vede meno: sabotando il codice
    // per far sparire la piena, le altre otto prove restavano verdi.
    expect(tracciatoDellaLuna(100, true)).toBe("M 0 -10 A 10 10 0 0 1 0 10 A 10.00 10 0 0 1 0 -10 Z")
  })

  it("al quarto il terminatore e dritto", () => {
    // Meta' esatta: l'ellisse ha larghezza zero, cioe' e' una riga verticale.
    expect(tracciatoDellaLuna(50, true)).toContain("A 0.00 10")
  })

  it("i due lati danno due disegni diversi", () => {
    // Da che parte sta il lembo lo decide il backend, che conosce la fase **e** l'emisfero: qui
    // si guarda solo che il lato conti davvero. La regola dell'emisfero ha la sua prova dove
    // vive, in `test_the_lit_limb_is_mirrored_south_of_the_equator`.
    expect(tracciatoDellaLuna(60, true)).not.toBe(tracciatoDellaLuna(60, false))
  })
})

const NOTTE = [
  { at: "2026-09-19T12:00:00+02:00", altitude_deg: -35.8 },
  { at: "2026-09-19T19:48:00+02:00", altitude_deg: 16.1 },
  { at: "2026-09-20T12:00:00+02:00", altitude_deg: -43.4 },
]

describe("la curva della notte", () => {
  it("l orizzonte cade dove il fornitore lo disegna", () => {
    // Col tetto a 75 gradi e il pavimento a -15, su una tela alta 40 l'orizzonte sta a 33,3:
    // e' il numero che sta nella loro pagina, e viene dalla stessa scala.
    const disegno = curvaDellaNotte(NOTTE, 75, 227, 40, new Date("2026-09-19T22:00:00+02:00"))

    expect(disegno).not.toBeNull()
    expect(disegno?.orizzonte).toBeCloseTo(33.3, 1)
  })

  it("la curva comincia a sinistra e finisce a destra, e tocca il tetto dove la luna e alta", () => {
    const disegno = curvaDellaNotte(NOTTE, 75, 227, 40, new Date("2026-09-19T22:00:00+02:00"))

    expect(disegno?.curva.startsWith("M 0.0 ")).toBe(true)
    expect(disegno?.curva).toContain("L 227.0 ")
  })

  it("la riga di adesso sta dove siamo, e sparisce quando la notte e scaduta", () => {
    // Le nove e tre quarti di sera: dentro la notte, e quindi una colonna. Il giorno dopo alle
    // sei di sera la notte e' un'altra, e una riga disegnata li' direbbe una cosa falsa.
    const dentro = curvaDellaNotte(NOTTE, 75, 227, 40, new Date("2026-09-19T21:45:00+02:00"))
    const fuori = curvaDellaNotte(NOTTE, 75, 227, 40, new Date("2026-09-20T18:00:00+02:00"))

    expect(dentro?.adesso).toBeGreaterThan(0)
    expect(dentro?.adesso).toBeLessThan(227)
    expect(fuori?.adesso).toBeNull()
  })

  it("senza abbastanza punti non si disegna niente, invece di una riga inventata", () => {
    expect(curvaDellaNotte([], 75, 227, 40, new Date())).toBeNull()
    expect(curvaDellaNotte(NOTTE.slice(0, 1), 75, 227, 40, new Date())).toBeNull()
  })

})

describe("le tacche dell'ora", () => {
  // Una notte vera arriva a passo di un quarto d'ora da mezzogiorno (`ephemeris.TRACK_STEP_MIN`),
  // quindi le ore tonde sono gia' fra i campioni: qui se ne prendono tre, come in una notte vera.
  const PIENA = [
    { at: "2026-09-19T12:00:00+02:00", altitude_deg: -35.8 },
    { at: "2026-09-19T18:00:00+02:00", altitude_deg: 10.0 },
    { at: "2026-09-20T00:00:00+02:00", altitude_deg: 8.0 },
    { at: "2026-09-20T06:00:00+02:00", altitude_deg: -30.0 },
    { at: "2026-09-20T12:00:00+02:00", altitude_deg: -43.4 },
  ]

  it("segnano le ore tonde lungo la notte, non due volte lo stesso mezzogiorno", () => {
    // La notte va **da mezzogiorno a mezzogiorno**: due sole etichette agli estremi direbbero
    // "12:00" tutte e due, ogni notte, e non si capirebbe ne' quando ne' quanto dura.
    const disegno = curvaDellaNotte(PIENA, 75, 480, 180, new Date("2026-09-19T22:00:00+02:00"))

    expect(disegno?.tacche.map((t) => t.at.slice(11, 16))).toEqual([
      "12:00",
      "18:00",
      "00:00",
      "06:00",
      "12:00",
    ])
  })

  it("stanno dove sta l ora che nominano", () => {
    const disegno = curvaDellaNotte(PIENA, 75, 480, 180, new Date("2026-09-19T22:00:00+02:00"))
    const mezzanotte = disegno?.tacche.find((t) => t.at.slice(11, 16) === "00:00")

    // meta' notte, meta' tela
    expect(mezzanotte?.x).toBeCloseTo(240, 1)
    expect(disegno?.tacche[0]?.x).toBe(0)
  })

  it("una notte campionata largo non inventa ore che non ha", () => {
    // Se fra i campioni non c'e' un'ora tonda, non se ne disegna una a occhio: la tacca e' un
    // campione vero, o non c'e'.
    const disegno = curvaDellaNotte(NOTTE, 75, 480, 180, new Date("2026-09-19T22:00:00+02:00"))

    expect(disegno?.tacche.map((t) => t.at.slice(11, 16))).toEqual(["12:00", "12:00"])
  })
})

describe("le fasce dipinte", () => {
  const NOTTE_INTERA = [
    { at: "2026-09-19T12:00:00+02:00", altitude_deg: -35.8 },
    { at: "2026-09-20T12:00:00+02:00", altitude_deg: -43.4 },
  ]

  it("stanno dove sta l ora che il backend gli ha dato", () => {
    // Qui si trasformano solo in colonne, con **la stessa** scala del tempo della curva: due
    // scale diverse e il buio non starebbe piu' sotto la Luna che lo attraversa.
    const disegno = curvaDellaNotte(NOTTE_INTERA, 75, 480, 180, new Date(), [
      { starts_at: "2026-09-19T12:00:00+02:00", ends_at: "2026-09-19T18:00:00+02:00", kind: "day" },
      { starts_at: "2026-09-19T18:00:00+02:00", ends_at: "2026-09-20T12:00:00+02:00", kind: "dark" },
    ])

    expect(disegno?.fasceDipinte).toEqual([
      { x: 0, larghezza: 120, kind: "day", starts_at: "2026-09-19T12:00:00+02:00" },
      { x: 120, larghezza: 360, kind: "dark", starts_at: "2026-09-19T18:00:00+02:00" },
    ])
  })

  it("stanno con la curva anche nella notte che non dura ventiquattro ore", () => {
    // Due volte l'anno la notte dura 23 o 25 ore (`api/tonight._finestra`). Una scala che
    // assumesse le 24 fisse staccherebbe le fasce dalla curva fino a un ventiquattresimo di tela
    // -- venti pixel su 480 -- e l'ultima lascerebbe una striscia non dipinta. Qui la notte
    // comincia a mezzogiorno del 28 marzo e finisce a mezzogiorno del 29: **23 ore**.
    const primaverile = [
      { at: "2027-03-28T12:00:00+01:00", altitude_deg: -30 },
      { at: "2027-03-29T12:00:00+02:00", altitude_deg: -30 },
    ]
    const disegno = curvaDellaNotte(primaverile, 75, 480, 180, new Date(), [
      { starts_at: "2027-03-28T12:00:00+01:00", ends_at: "2027-03-29T00:00:00+02:00", kind: "day" },
      { starts_at: "2027-03-29T00:00:00+02:00", ends_at: "2027-03-29T12:00:00+02:00", kind: "dark" },
    ])

    // mezzanotte cade a 11 ore su 23, non a 12 su 24
    expect(disegno?.fasceDipinte[0]?.larghezza).toBeCloseTo((480 * 11) / 23, 6)
    // e l'ultima arriva al bordo: nessuna striscia di tela senza fascia
    const ultima = disegno!.fasceDipinte[1]!
    expect(ultima.x + ultima.larghezza).toBeCloseTo(480, 6)
  })

  it("senza fasce non si dipinge niente", () => {
    // Finche' il backend non le manda -- un sito senza fuso -- la tela resta senza fondo, e non
    // se ne inventa uno piatto che direbbe "giorno" tutta la notte.
    const disegno = curvaDellaNotte(NOTTE_INTERA, 75, 480, 180, new Date())

    expect(disegno?.fasceDipinte).toEqual([])
  })
})
