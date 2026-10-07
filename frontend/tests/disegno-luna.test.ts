/**
 * La geometria della Luna: il disco della fase.
 *
 * I tracciati attesi sono quelli che il fornitore ha disegnato nella sua consegna: se i nostri
 * divergono, a schermo si vedrebbe una luna diversa da quella approvata.
 */
import { describe, expect, it } from "vitest"

import { tracciatoDellaLuna } from "../src/disegnoDellaLuna"

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
