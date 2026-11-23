// @vitest-environment jsdom
/**
 * Valori che avevano due case nel frontend (passo 12): ognuno ne ha una, e questa prova si rompe
 * se un altro file lo riscrive a mano invece di prenderlo da li'.
 */
import { readFileSync, readdirSync, statSync } from "node:fs"
import { join, relative, resolve } from "node:path"

import { describe, expect, it } from "vitest"

import { ZENIT_DEG, quotaSulloZenit } from "../src/disegnoDellaLuna"
import { TETTO } from "../src/sito"

const SRC = resolve(process.cwd(), "src")

function sorgenti(cartella: string): string[] {
  return readdirSync(cartella).flatMap((n) => {
    const p = join(cartella, n)
    if (statSync(p).isDirectory()) return n === "api" || n === "i18n" ? [] : sorgenti(p)
    return /\.tsx?$/.test(n) ? [p] : []
  })
}

/** The files whose code matches `regola`, comments left out. */
function doveSta(regola: RegExp): string[] {
  return sorgenti(SRC)
    .filter((p) =>
      readFileSync(p, "utf-8")
        .split("\n")
        .some((riga) => !/^\s*(\/\/|\*|\/\*)/.test(riga) && regola.test(riga)),
    )
    .map((p) => relative(SRC, p).replaceAll("\\", "/"))
}

describe("un valore, una casa", () => {
  it("lo zenit dei grafici della Luna sta in disegnoDellaLuna.ts", () => {
    expect(doveSta(/\/\s*90\b|[?:]\s*90\b(?!\s*,)|"90(\\u00b0|°)"/)).toEqual([])
    expect(ZENIT_DEG).toBe(90)
    expect([
      quotaSulloZenit(-3),
      quotaSulloZenit(0),
      quotaSulloZenit(45),
      quotaSulloZenit(90),
    ]).toEqual([-1, 0, 50, 100])
  })

  it("i bordi di latitudine e longitudine stanno in sito.tsx", () => {
    expect(doveSta(/(<=|>=|<|>)\s*(90|180)\b|,\s*(90|180)\)/)).toEqual([])
    expect(TETTO).toEqual({ lat: 90, lon: 180 })
  })

  it("l'anno prima della legenda arriva dall'API, lo schermo non sottrae", () => {
    expect(doveSta(/\.year\s*-\s*1\b/)).toEqual([])
  })
})
