// @vitest-environment jsdom
/**
 * La larghezza misurata (`useLarghezza`, src/colonna.ts): jsdom non impagina, quindi la misura la
 * da' la prova con un `ResizeObserver` finto. Sotto la tolleranza resta la misura di prima.
 */
import { act, renderHook } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { useLarghezza } from "../src/colonna"

type Voci = { contentRect: { width: number } }[]
let dice: (v: Voci) => void = () => {}
let osservati: Element[] = []
let staccati = 0

function occhioFinto() {
  osservati = []
  staccati = 0
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(cb: (v: Voci) => void) {
        dice = cb
      }
      observe(el: Element) {
        osservati.push(el)
      }
      disconnect() {
        staccati += 1
      }
    },
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

const larghe = (...w: number[]) => w.map((width) => ({ contentRect: { width } }))

describe("useLarghezza", () => {
  it("guarda l'elemento dato e dice la sua larghezza", () => {
    occhioFinto()
    const { result } = renderHook(() => useLarghezza())
    const el = document.createElement("div")
    let stacca: (() => void) | undefined
    act(() => {
      stacca = result.current[1](el)
    })
    expect(osservati).toEqual([el])
    expect(result.current[0]).toBeUndefined()
    act(() => dice(larghe(500)))
    expect(result.current[0]).toBe(500)
    act(() => dice(larghe(501)))
    expect(result.current[0]).toBe(501)
    stacca?.()
    expect(staccati).toBe(1)
  })

  it("sotto la tolleranza resta la misura di prima, oltre cambia", () => {
    occhioFinto()
    const { result } = renderHook(() => useLarghezza(4))
    act(() => {
      result.current[1](document.createElement("div"))
    })
    act(() => dice(larghe(500)))
    expect(result.current[0]).toBe(500)
    act(() => dice(larghe(504)))
    expect(result.current[0]).toBe(500)
    act(() => dice(larghe(496)))
    expect(result.current[0]).toBe(500)
    act(() => dice(larghe(505)))
    expect(result.current[0]).toBe(505)
  })

  it("una notizia senza voci non cambia niente", () => {
    occhioFinto()
    const { result } = renderHook(() => useLarghezza())
    act(() => {
      result.current[1](document.createElement("div"))
    })
    act(() => dice(larghe(300)))
    act(() => dice([]))
    expect(result.current[0]).toBe(300)
  })

  it("senza elemento, o senza ResizeObserver, non guarda niente", () => {
    occhioFinto()
    const { result } = renderHook(() => useLarghezza())
    expect(result.current[1](null)).toBeUndefined()
    expect(osservati).toEqual([])
    vi.stubGlobal("ResizeObserver", undefined)
    expect(result.current[1](document.createElement("div"))).toBeUndefined()
    expect(result.current[0]).toBeUndefined()
  })
})
