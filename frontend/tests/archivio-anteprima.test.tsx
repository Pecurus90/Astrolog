// @vitest-environment jsdom
/**
 * L'**anteprima** della carta dell'Archivio (tavola v56.12-13, passo 33.2): un tondo per
 * produzione che aggiunge o cambia la foto, la foto letta con la chiave della pagina, e il perche'
 * di un rifiuto in un avviso. I posti e i loro indirizzi arrivano dall'API.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { chiamate, pulisci, rispondi } from "./banco"
import { M31, MOSAICO, apriArchivio, conArchivio, voceArchivio } from "./archivio-banco"

const CON_FOTO = {
  ...M31,
  previews: [{ url: M31.previews[0]!.url, at: "2026-11-18T10:00:00Z" }],
}

beforeEach(() => {
  vi.stubGlobal(
    "URL",
    Object.assign(URL, { createObjectURL: () => "blob:foto", revokeObjectURL: () => undefined }),
  )
})
afterEach(pulisci)

describe("l'anteprima della carta", () => {
  it("una foto accettata fa rileggere l'Archivio: la carta passa alla matita da sola", async () => {
    rispondi({
      "PUT /api/v1/archive/preview": { stato: 200, corpo: { url: M31.previews[0]!.url, at: "x" } },
      ...conArchivio(voceArchivio([M31])),
    })
    await apriArchivio()
    const tasto = await screen.findByLabelText("Aggiungi l'anteprima: M 31")
    const elenchi = () => chiamate().filter((u) => /\/api\/v1\/archive(\?|$)/.test(u)).length
    const prima = elenchi()
    fireEvent.change(tasto, {
      target: { files: [new File(["x"], "m31.jpg", { type: "image/jpeg" })] },
    })
    await waitFor(() => expect(elenchi()).toBeGreaterThan(prima))
    expect(screen.queryByText(/non risponde/)).toBeNull()
  })

  it("senza foto: il nome nel riquadro e il tondo che aggiunge", async () => {
    rispondi(conArchivio(voceArchivio([M31])))
    await apriArchivio()
    const tasto = await screen.findByLabelText("Aggiungi l'anteprima: M 31")
    expect(tasto.getAttribute("accept")).toBe("image/jpeg,image/png,image/webp")
    expect(tasto.closest("label")?.getAttribute("title")).toBe("Aggiungi l'anteprima")
    expect(document.querySelector(".al-arch__blocco-7")?.textContent).toBe("M 31")
    // il tondo sta fuori dal collegamento che apre la finestra: toccarlo non la apre
    expect(tasto.closest("a")).toBeNull()
    expect(chiamate().some((u) => u.includes("/archive/preview"))).toBe(false)
  })

  it("con la foto: letta con la chiave, il nome esce, il tondo cambia", async () => {
    rispondi({
      "GET /api/v1/archive/preview": { stato: 200, corpo: "jpeg" },
      ...conArchivio(voceArchivio([CON_FOTO])),
    })
    await apriArchivio()
    await screen.findByLabelText("Cambia l'anteprima: M 31")
    await waitFor(() =>
      expect(
        (document.querySelector(".al-arch__foto-parte") as HTMLElement).style.backgroundImage,
      ).toContain("blob:foto"),
    )
    expect(document.querySelector(".al-arch__blocco-7")).toBeNull()
  })

  it("piu' produzioni: un tondo per ognuna, col suo numero", async () => {
    const due = {
      ...M31,
      productions: [M31.productions[0], { ...M31.productions[0], optics_id: 3 }],
      previews: [
        M31.previews[0],
        { url: "/api/v1/archive/preview?key=m-31&production=3%3A2", at: null },
      ],
    }
    rispondi(conArchivio(voceArchivio([due])))
    await apriArchivio()
    expect(
      await screen.findByLabelText("Aggiungi l'anteprima: 2ª produzione di M 31"),
    ).toBeDefined()
    expect(screen.getAllByTitle(/della [12]ª produzione/)).toHaveLength(2)
  })

  it("un mosaico ha un tondo solo", async () => {
    rispondi(conArchivio(voceArchivio([MOSAICO])))
    await apriArchivio()
    expect(await screen.findByLabelText("Aggiungi l'anteprima: IC 405")).toBeDefined()
    expect(document.querySelectorAll(".al-arch__foto-tasto")).toHaveLength(1)
  })

  it("una foto rifiutata dice perche', e l'avviso si chiude", async () => {
    rispondi({
      "PUT /api/v1/archive/preview": { stato: 422, corpo: { detail: { code: "not_an_image" } } },
      ...conArchivio(voceArchivio([M31])),
    })
    await apriArchivio()
    const tasto = await screen.findByLabelText("Aggiungi l'anteprima: M 31")
    const file = new File(["x"], "m31.tif", { type: "image/tiff" })
    fireEvent.change(tasto, { target: { files: [file] } })
    expect(
      await screen.findByText("Questa immagine non si legge: usa un JPEG, un PNG o un WebP."),
    ).toBeDefined()
    fireEvent.click(screen.getByRole("button", { name: "Chiudi" }))
    await waitFor(() => expect(screen.queryByText(/non si legge/)).toBeNull())
  })

  it("troppo grande, in byte o in pixel, e' la stessa frase", async () => {
    for (const code of ["too_large", "too_many_pixels"]) {
      pulisci()
      vi.stubGlobal(
        "URL",
        Object.assign(URL, {
          createObjectURL: () => "blob:foto",
          revokeObjectURL: () => undefined,
        }),
      )
      rispondi({
        "PUT /api/v1/archive/preview": {
          stato: code === "too_large" ? 413 : 422,
          corpo: { detail: { code } },
        },
        ...conArchivio(voceArchivio([M31])),
      })
      await apriArchivio()
      const tasto = await screen.findByLabelText("Aggiungi l'anteprima: M 31")
      fireEvent.change(tasto, {
        target: { files: [new File(["x"], "m31.png", { type: "image/png" })] },
      })
      expect(
        await screen.findByText("L'immagine è troppo grande: esportala più piccola."),
      ).toBeDefined()
    }
  })
})
