// @vitest-environment jsdom
/**
 * Il passo *Seeing* del primo avvio (tavola v82 `V.seeing`, `K`): la chiave Meteoblue si prova sul
 * conto e si tiene solo se regge; ogni esito ha la sua frase e il suo segno. La forma del passo
 * (avviso, link, un solo pieno) sta in `wizard-solver.test.tsx`; qui la chiave che parte davvero.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SPINA,
  STANOTTE,
  type Voce,
  cambia,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
} from "./banco"

afterEach(pulisci)

function conChiave(fine: string | null) {
  const base = impostazioni(false)
  return { ...base, values: { ...base.values, meteoblue_key: fine } }
}

function mappa(fine: string | null, chiave?: Voce): Record<string, Voce> {
  return {
    ...STANOTTE,
    ...(chiave ? { "PUT /api/v1/weather/meteoblue-key": chiave } : {}),
    "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
    "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/settings": { stato: 200, corpo: conChiave(fine) },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    ...SPINA,
  }
}

async function alSeeing(fine: string | null, chiave?: Voce) {
  rispondi(mappa(fine, chiave))
  await disegna()
  await screen.findByRole("button", { name: /salta/i })
  for (let i = 0; i < 4; i++) fireEvent.click(screen.getByRole("button", { name: /avanti/i }))
  await screen.findByRole("region", { name: "Seeing (Meteoblue)" })
}

/** Gli avvisi di riga del passo: «segno frase». */
const avvisi = () =>
  [...document.querySelectorAll(".al-avvio__colonna-21 [role=status]")].map(
    (s) => `${s.querySelector("[aria-hidden=true]")?.textContent} ${s.textContent?.slice(1)}`,
  )
const campo = () => screen.getByLabelText<HTMLInputElement>(/chiave meteoblue/i)
const salva = () => screen.getByRole("button", { name: /^verifica e salva$/i })
const mandate = () => scritture().filter((s) => s.url.includes("/meteoblue-key"))

describe("il passo Seeing del primo avvio", () => {
  it("una chiave valida parte senza spazi, il campo si vuota e le impostazioni si rileggono", async () => {
    await alSeeing(null, { stato: 200, corpo: { status: "ok", hint: "...1234" } })
    fireEvent.change(campo(), { target: { value: "  abcd1234  " } })
    const prima = chiamate().filter((u) => u.endsWith("/api/v1/settings")).length
    cambia(mappa("...1234", { stato: 200, corpo: { status: "ok", hint: "...1234" } }))
    fireEvent.click(salva())

    await waitFor(() => expect(avvisi()).toContain("✓ Chiave valida: seeing attivo."))
    expect(mandate()).toEqual([
      {
        url: expect.stringContaining("/api/v1/weather/meteoblue-key"),
        metodo: "PUT",
        corpo: { key: "abcd1234" },
      },
    ])
    expect(campo().value).toBe("")
    await waitFor(() =>
      expect(chiamate().filter((u) => u.endsWith("/api/v1/settings")).length).toBeGreaterThan(
        prima,
      ),
    )
    // rilette, dicono la fine della chiave salvata e offrono di toglierla
    await waitFor(() => expect(avvisi()[0]).toBe("✓ Chiave salvata (termina con ...1234)."))
    expect(screen.getByRole("button", { name: /^rimuovi chiave$/i })).toBeDefined()
  })

  it("crediti finiti: la chiave si salva, la frase lo dice e il campo si vuota", async () => {
    await alSeeing(null, { stato: 200, corpo: { status: "limited", hint: "...1234" } })
    fireEvent.change(campo(), { target: { value: "abcd1234" } })
    fireEvent.click(salva())
    await waitFor(() =>
      expect(avvisi()).toContain(
        "! Meteoblue non risponde per ora: crediti o richieste esauriti. La chiave è buona, riprovo più tardi.",
      ),
    )
    expect(campo().value).toBe("")
  })

  it.each([
    ["refused", "! Chiave non riconosciuta da Meteoblue: non salvata."],
    ["unreachable", "! Meteoblue non risponde: chiave non verificata e non salvata."],
    ["bad_answer", "! Risposta non valida da Meteoblue: chiave non salvata."],
  ])(
    "una chiave %s non si salva: la frase col segno, e il campo resta scritto",
    async (esito, frase) => {
      await alSeeing(null, { stato: 200, corpo: { status: esito, hint: null } })
      fireEvent.change(campo(), { target: { value: "sbagliata" } })
      fireEvent.click(salva())
      await waitFor(() =>
        expect(avvisi()).toEqual(["? Nessuna chiave: seeing non disponibile.", frase]),
      )
      expect(campo().value).toBe("sbagliata")
      expect(screen.queryByRole("button", { name: /^rimuovi chiave$/i })).toBeNull()
    },
  )

  it("un invio che non riesce lo dice, e non finge un esito", async () => {
    await alSeeing(null, { stato: 500, corpo: { detail: { code: "rotto" } } })
    fireEvent.change(campo(), { target: { value: "k" } })
    fireEvent.click(salva())
    await waitFor(() =>
      expect(avvisi()).toEqual([
        "? Nessuna chiave: seeing non disponibile.",
        "! Invio della chiave non riuscito",
      ]),
    )
    expect(campo().value).toBe("k")
  })

  it("Fine con la chiave scritta la verifica e la salva, poi va avanti", async () => {
    await alSeeing(null, { stato: 200, corpo: { status: "ok", hint: "...0001" } })
    fireEvent.change(campo(), { target: { value: " k0001 " } })
    fireEvent.click(screen.getByRole("button", { name: /^fine$/i }))
    await waitFor(() => expect(mandate().map((s) => s.corpo)).toEqual([{ key: "k0001" }]))
    await waitFor(() => expect(scritture().some((s) => s.url.includes("/wizard-done"))).toBe(true))
    // la chiusura conta il passo fatto: la chiave salvata adesso, non quella letta prima
    await waitFor(() =>
      expect(
        [...document.querySelectorAll(".al-avvio__riga-1")].map((li) =>
          li.getAttribute("aria-label"),
        ),
      ).toContain("Seeing (Meteoblue), fatto"),
    )
  })

  it("due Fine mentre la chiave si verifica: una verifica e una chiusura", async () => {
    let lascia: (v: unknown) => void = () => {}
    await alSeeing(null, {
      stato: 200,
      corpo: { status: "ok", hint: "...0001" },
      attesa: new Promise((r) => (lascia = r)),
    })
    fireEvent.change(campo(), { target: { value: "k0001" } })
    const fine = screen.getByRole("button", { name: /^fine$/i })
    fireEvent.click(fine)
    fireEvent.click(fine)
    lascia(undefined)
    await waitFor(() => expect(scritture().some((s) => s.url.includes("/wizard-done"))).toBe(true))
    await new Promise((r) => setTimeout(r, 50))
    expect(mandate()).toHaveLength(1)
    expect(scritture().filter((s) => s.url.includes("/wizard-done"))).toHaveLength(1)
  })

  it("Fine con una chiave rifiutata resta sul passo e dice perche'", async () => {
    await alSeeing(null, { stato: 200, corpo: { status: "refused", hint: null } })
    fireEvent.change(campo(), { target: { value: "sbagliata" } })
    fireEvent.click(screen.getByRole("button", { name: /^fine$/i }))
    await waitFor(() =>
      expect(avvisi()).toContain("! Chiave non riconosciuta da Meteoblue: non salvata."),
    )
    await new Promise((r) => setTimeout(r, 20))
    expect(scritture().some((s) => s.url.includes("/wizard-done"))).toBe(false)
    expect(screen.getByRole("region", { name: "Seeing (Meteoblue)" })).toBeDefined()
  })

  it("Invio nel campo manda la chiave come il comando", async () => {
    await alSeeing(null, { stato: 200, corpo: { status: "ok", hint: "...0001" } })
    fireEvent.change(campo(), { target: { value: "k0001" } })
    fireEvent.submit(campo().closest("form")!)
    await waitFor(() => expect(mandate().map((s) => s.corpo)).toEqual([{ key: "k0001" }]))
  })

  it("solo spazi nel campo: niente parte, ne' dal comando ne' da Invio", async () => {
    await alSeeing(null, { stato: 200, corpo: { status: "ok", hint: null } })
    fireEvent.change(campo(), { target: { value: "   " } })
    expect(salva().getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(salva())
    fireEvent.submit(campo().closest("form")!)
    await new Promise((r) => setTimeout(r, 20))
    expect(mandate()).toEqual([])
  })

  it("mentre la chiave si prova il comando lo dice e non riparte", async () => {
    await alSeeing(null, {
      stato: 200,
      corpo: { status: "ok", hint: null },
      attesa: new Promise(() => {}),
    })
    fireEvent.change(campo(), { target: { value: "k" } })
    fireEvent.click(salva())
    const occupato = await screen.findByRole("button", { name: "Verifica…" })
    expect(occupato.getAttribute("aria-busy")).toBe("true")
    fireEvent.submit(campo().closest("form")!)
    fireEvent.click(occupato)
    await new Promise((r) => setTimeout(r, 20))
    expect(mandate()).toHaveLength(1)
  })

  it("con la chiave salvata il pieno torna a Fine, e Rimuovi la toglie con l'esito suo", async () => {
    await alSeeing("...1234", { stato: 200, corpo: { status: "removed", hint: null } })
    expect(avvisi()).toEqual(["✓ Chiave salvata (termina con ...1234)."])
    // tavola `cmd`: chiave salvata e campo vuoto, il passo non chiede piu' niente
    expect(salva().className).toContain("al-bottone--tenue")
    expect(screen.getByRole("button", { name: /^fine$/i }).className).toContain("al-bottone--pieno")
    fireEvent.change(campo(), { target: { value: "nuova" } })
    expect(salva().className).toContain("al-bottone--pieno")
    fireEvent.change(campo(), { target: { value: "" } })

    fireEvent.click(screen.getByRole("button", { name: /^rimuovi chiave$/i }))
    await waitFor(() => expect(avvisi()).toContain("? Chiave rimossa: seeing non disponibile."))
    expect(mandate().map((s) => s.corpo)).toEqual([{ key: "" }])
  })
})
