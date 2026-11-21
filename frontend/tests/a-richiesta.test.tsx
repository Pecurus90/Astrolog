// @vitest-environment jsdom
/**
 * Il frontend si scarica a richiesta: al primo caricamento arriva il telaio, una pagina quando la
 * si apre, una lingua quando la si sceglie. Prima era un pacchetto solo da 1 061 kB, e la
 * Dashboard ne usava il 36-40%.
 */
import { describe, expect, it as prova } from "vitest"

import { DIZIONARI, caricaLingua, t, usaLingua } from "../src/i18n"
import { en } from "../src/i18n/en"
import { PAGINE } from "../src/pagine"

const PIGRO = Symbol.for("react.lazy")

describe("a richiesta", () => {
  prova("ogni pagina si scarica quando la si apre", () => {
    const pagine = PAGINE.filter((p) => p.elemento !== undefined)
    expect(pagine.length).toBeGreaterThan(0)
    for (const p of pagine) {
      // Impostazioni resta nel telaio: le sue sezioni le legge la ricerca. Si scaricano le sezioni.
      if (p.sezioni) continue
      const tipo = p.elemento?.type as { $$typeof?: symbol }
      expect(tipo.$$typeof, p.a).toBe(PIGRO)
    }
  })

  prova("e anche le sezioni delle Impostazioni che il telaio non usa", () => {
    const sezioni = PAGINE.flatMap((p) => p.sezioni ?? []).filter((s) => s.elemento !== undefined)
    const pigre = sezioni.filter(
      (s) => (s.elemento?.type as { $$typeof?: symbol }).$$typeof === PIGRO,
    )
    expect(pigre.length).toBeGreaterThan(0)
  })

  prova("nei test una pagina e' gia' arrivata prima del primo test", () => {
    // React 19 trattiene 300 ms ogni pagina che compare dopo l'attesa: la suite triplicava
    const pagine = PAGINE.filter((p) => p.elemento !== undefined && !p.sezioni)
    for (const p of pagine) {
      const tipo = p.elemento?.type as unknown as { _payload: { _status: number } }
      expect(tipo._payload._status, p.a).toBe(1)
    }
  })

  prova("l'inglese non c'e' finche' non si sceglie", async () => {
    expect(DIZIONARI.en).toBeUndefined()
    // Prima che arrivi, un testo resta nella sorgente invece di sparire.
    usaLingua("en")
    expect(t("nav.nights")).not.toBe(en["nav.nights"])
    expect(await caricaLingua("en")).toBe("en")
    usaLingua("en")
    expect(t("nav.nights")).toBe(en["nav.nights"])
    usaLingua("it")
  })

  prova("una lingua che l'app non ha resta la sorgente", async () => {
    expect(await caricaLingua("xx")).toBe("it")
  })
})
