/**
 * La pagina dichiara la sua icona (Issue #56): senza, il browser chiede `/favicon.ico`, il
 * controllo del token risponde 401 e ogni pagina scrive un errore in console. L'icona sta fra i
 * file di Vite, che finiscono in `/assets/` (aperti senza token, `img-src 'self'`).
 */
import { existsSync, readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { describe, expect, it } from "vitest"

const radice = resolve(dirname(fileURLToPath(import.meta.url)), "..")
const pagina = readFileSync(resolve(radice, "index.html"), "utf8")

describe("l'icona della pagina", () => {
  it("c'e', ed e' un file che Vite porta in /assets", () => {
    const href = /<link[^>]*rel="icon"[^>]*href="([^"]+)"/.exec(pagina)?.[1]
    expect(href).toMatch(/^\/src\/.+\.svg$/)
    expect(existsSync(resolve(radice, `.${href ?? ""}`))).toBe(true)
  })
})
