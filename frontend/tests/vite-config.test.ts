/**
 * In sviluppo Vite gira le chiamate `/api` al backend: deve trovarlo sulla porta dove
 * `tools/dev.py` l'ha acceso, anche quando `ASTROLOG_PORT` non e' quella di sempre.
 */
import { afterEach, describe, expect, it, vi } from "vitest"

afterEach(() => {
  vi.unstubAllEnvs()
  vi.resetModules()
})

async function destinazione(): Promise<unknown> {
  const config = (await import("../vite.config")).default as {
    server?: { proxy?: Record<string, unknown> }
  }
  return config.server?.proxy?.["/api"]
}

describe("il proxy dello sviluppo", () => {
  it("segue ASTROLOG_PORT", async () => {
    vi.stubEnv("ASTROLOG_PORT", "9123")
    expect(await destinazione()).toBe("http://127.0.0.1:9123")
  })

  it("senza ASTROLOG_PORT resta sulla porta del backend", async () => {
    vi.stubEnv("ASTROLOG_PORT", "")
    expect(await destinazione()).toBe("http://127.0.0.1:8765")
  })
})
