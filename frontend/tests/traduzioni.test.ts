/**
 * La guardia delle traduzioni: ogni lingua attiva dice tutto quello che dice la sorgente.
 *
 * Legge le lingue da `src/i18n/lingue.ts`, che e' il posto solo dove sono scritte: una guardia
 * che si costruisse il proprio elenco sarebbe cieca per costruzione, perche' una lingua aggiunta
 * la' non arriverebbe mai qui.
 *
 * L'ultima prova e' la macchina che dimostra se stessa: due elenchi vuoti confrontati danno
 * sempre "tutto a posto", e senza una violazione finta il verde delle prove sopra non
 * distinguerebbe "le traduzioni ci sono" da "il confronto non guarda niente".
 */
import { describe, expect, it as prova } from "vitest"

import { DIZIONARI, numero, t } from "../src/i18n"
import { it } from "../src/i18n/it"
import { LINGUE } from "../src/i18n/lingue"

/** Le chiavi che `sorgente` ha e `altra` no. */
function mancanti(sorgente: Record<string, string>, altra: Record<string, string>) {
  return Object.keys(sorgente).filter((chiave) => !(chiave in altra))
}

describe("le traduzioni", () => {
  prova.each([...LINGUE])("la lingua %s dice tutto quello che dice la sorgente", (lingua) => {
    expect(mancanti(it, DIZIONARI[lingua])).toEqual([])
  })

  prova.each([...LINGUE])("e la lingua %s non dice niente che la sorgente non dica", (lingua) => {
    // Una chiave in piu' e' una stringa che nessuno mostra: o la sorgente l'ha persa, o e'
    // l'avanzo di un testo tolto. In tutti e due i casi qualcuno deve guardarla.
    expect(mancanti(DIZIONARI[lingua], it)).toEqual([])
  })

  prova("un segnaposto senza valore resta visibile invece di sparire", () => {
    // Un buco silenzioso diventa un testo scritto male che nessuno spiega; un `{n}` a schermo
    // si nota e si ripara.
    expect(t("health.tables", {})).toContain("{n}")
  })

  prova("i conteggi si scrivono come li scrive la lingua", () => {
    expect(numero(22080)).toBe("22.080")
  })

  prova("e la guardia morde davvero quando una chiave manca", () => {
    expect(mancanti({ "a.b": "x" }, {})).toEqual(["a.b"])
  })
})
