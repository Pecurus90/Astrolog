// @vitest-environment jsdom
/**
 * Impostazioni, *Il cielo del sito* (tavola v82, 65-90): la fonte del cielo di ora, le quattro vie
 * e cio' che ognuna scrive, lo SQM a mano col suo intervallo, la proposta delle misure con Usa e
 * Lascia, i dodici mesi. Si prova che una via scrive solo col gesto che dice un cielo.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import type { components } from "../src/api/schema"
import {
  SALUTE,
  SITO_DI_CASA,
  SPINA,
  STANOTTE,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
  vai,
  type Voce,
} from "./banco"
import { impronta } from "./impronta"

afterEach(pulisci)

type Sito = components["schemas"]["SiteOut"]
type Misurato = Sito["measured"]

const CASA: Sito = { ...SITO_DI_CASA, name: "Cima Ekar" }

const MESI = Array.from({ length: 12 }, (_, i) => ({
  year: i < 2 ? 2025 : 2026,
  month: ((10 + i) % 12) + 1,
  measured: i % 3 !== 2,
}))

const BASTANO: Misurato = {
  status: "enough",
  nights: 38,
  months: 10,
  sqm: 21.4,
  bortle: 4,
  first_night: "2025-11-02",
  last_night: "2026-10-28",
  propose: false,
  month_marks: MESI,
}

const POCHE: Misurato = {
  ...BASTANO,
  status: "too_few",
  nights: 3,
  months: 2,
  sqm: null,
  bortle: null,
  month_marks: MESI.slice(0, 2),
}

async function apri(
  sito: Sito,
  piu: Record<string, Voce> = {},
  chiave: string | null = null,
  indirizzo = "/impostazioni/siti",
) {
  const valori = impostazioni(true)
  rispondi({
    ...STANOTTE,
    ...piu,
    "/api/v1/settings": {
      stato: 200,
      corpo: { ...valori, values: { ...valori.values, sky_service_key: chiave } },
    },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/sites": {
      stato: 200,
      corpo: { items: [sito], total: 1, limit: 100, offset: 0, sqm_range: { min: 7, max: 23 } },
    },
    ...SPINA,
  })
  const { container } = await disegna()
  vai(indirizzo)
  const carta = await screen.findByRole("region", { name: "Il cielo del sito" })
  return { carta, container }
}

const via = (carta: HTMLElement, nome: string) =>
  within(within(carta).getByRole("group", { name: "Da dove viene il cielo" })).getByText(nome)
const premuta = (el: HTMLElement) => el.getAttribute("aria-pressed")
const scritte = (metodo: string, coda: string) =>
  scritture().filter((s) => s.metodo === metodo && s.url.endsWith(coda))
const attendi = () => new Promise((r) => setTimeout(r, 30))

describe("Impostazioni / Il cielo del sito", () => {
  it("il cielo di ora dice da dove viene, per ogni fonte", async () => {
    const casi: [Partial<Sito>, string, string][] = [
      [
        { sky_source: "frames", sky_sqm: 21.374, sky_nights: 14, bortle: 4 },
        "Bortle 4 – campagna più chiara",
        "dalle misure dei frame: SQM 21,37, 14 notti",
      ],
      [
        { sky_source: "frames", sky_sqm: 21.5, sky_nights: null, bortle: 4 },
        "Bortle 4 – campagna più chiara",
        "dalle misure dei frame: SQM 21,5, 0 notti",
      ],
      [
        { sky_source: "service", sky_sqm: 19.6, bortle: 5 },
        "Bortle 5 – cielo di periferia",
        "SQM 19,6 dalla mappa del servizio del cielo",
      ],
      [
        { sky_source: "scale", sky_sqm: 18, bortle: 7 },
        "Bortle 7 – fra periferia e città",
        "scritto a mano",
      ],
      [
        { sky_source: null, sky_sqm: 20, bortle: 5 },
        "Bortle 5 – cielo di periferia",
        "scritto a mano",
      ],
      [{ sky_source: null, sky_sqm: null, bortle: null }, "nessuno", "lasciato vuoto"],
      [{ sky_source: "scale", sky_sqm: 20, bortle: null }, "nessuno", "lasciato vuoto"],
    ]
    for (const [cambio, valore, fonte] of casi) {
      const { carta } = await apri({ ...CASA, ...cambio })
      const riga = within(carta).getByText("Ora").parentElement as HTMLElement
      expect(within(riga).getByText(valore)).toBeTruthy()
      expect(within(riga).getByText(fonte)).toBeTruthy()
      pulisci()
    }
  })

  it("la via accesa e' quella della fonte; Lascia vuoto c'e' solo con una via aperta", async () => {
    const { carta } = await apri({ ...CASA, sky_source: null, sky_sqm: null, bortle: null })
    for (const k of ["Dalle misure", "Bortle a mano", "SQM a mano", "Dalla mappa"])
      expect(premuta(via(carta, k))).toBe("false")
    expect(within(carta).queryByText("Lascia vuoto")).toBeNull()
    expect(
      within(carta).getByText(
        "Nessun cielo: dove serve, i conti lo dicono. Si sceglie una delle quattro vie.",
      ),
    ).toBeTruthy()
    pulisci()
    const { carta: due } = await apri(CASA)
    expect(premuta(via(due, "SQM a mano"))).toBe("true")
    expect(premuta(via(due, "Bortle a mano"))).toBe("false")
    expect(within(due).getByText("Lascia vuoto")).toBeTruthy()
  })

  it("Lascia vuoto toglie lo SQM e spegne la via", async () => {
    const { carta } = await apri(CASA, { "PATCH /api/v1/sites/1": { stato: 200, corpo: CASA } })
    fireEvent.click(within(carta).getByText("Lascia vuoto"))
    await waitFor(() =>
      expect(scritte("PATCH", "/api/v1/sites/1").map((s) => s.corpo)).toEqual([{ sky_sqm: null }]),
    )
    expect(premuta(via(carta, "SQM a mano"))).toBe("false")
    expect(within(carta).queryByText("Lascia vuoto")).toBeNull()
    expect(within(carta).getByText(/^Nessun cielo: dove serve/)).toBeTruthy()
  })

  it("Dalle misure scrive solo se le misure bastano e il cielo non viene gia' da li'", async () => {
    const usa = { "POST /api/v1/sites/1/sky/use": { stato: 200, corpo: CASA } }
    const { carta } = await apri({ ...CASA, measured: BASTANO }, usa)
    fireEvent.click(via(carta, "Dalle misure"))
    await waitFor(() => expect(scritte("POST", "/sky/use")).toHaveLength(1))
    expect(
      within(carta).getByText("Segue le misure: quando la classe misurata cambia, lo dice."),
    ).toBeTruthy()
    pulisci()

    const { carta: gia } = await apri(
      { ...CASA, measured: BASTANO, sky_source: "frames", sky_nights: 38 },
      usa,
    )
    fireEvent.click(via(gia, "Bortle a mano"))
    fireEvent.click(via(gia, "Dalle misure"))
    await attendi()
    expect(scritture()).toEqual([])
    pulisci()

    const { carta: poche } = await apri({ ...CASA, measured: POCHE }, usa)
    fireEvent.click(via(poche, "Dalle misure"))
    await attendi()
    expect(scritture()).toEqual([])
    // il sito ha un cielo: «resta senza cielo» non sarebbe vero
    expect(within(poche).queryByText(/^Finché le misure non bastano/)).toBeNull()
    pulisci()

    const { carta: vuoto } = await apri(
      { ...CASA, measured: POCHE, sky_source: null, sky_sqm: null, bortle: null },
      usa,
    )
    fireEvent.click(via(vuoto, "Dalle misure"))
    expect(
      within(vuoto).getByText("Finché le misure non bastano il sito resta senza cielo."),
    ).toBeTruthy()
  })

  it("Dalla mappa con la chiave chiede il cielo al servizio, e se tace lo dice", async () => {
    const { carta } = await apri(
      CASA,
      { "POST /api/v1/sites/1/sky/service": { stato: 503, corpo: { detail: "giu'" } } },
      "k",
    )
    fireEvent.click(via(carta, "Dalla mappa"))
    expect(within(carta).getByText(/^La mappa della luce artificiale dice il cielo/)).toBeTruthy()
    expect(within(carta).queryByText("Apri Servizi")).toBeNull()
    expect(
      await within(carta).findByText(
        "✕ La mappa del servizio del cielo non ha risposto: il cielo resta com'era.",
      ),
    ).toBeTruthy()
    expect(scritte("POST", "/sky/service")).toHaveLength(1)
    // un'altra via toglie l'avviso
    fireEvent.click(via(carta, "Bortle a mano"))
    expect(within(carta).queryByText(/non ha risposto/)).toBeNull()
    pulisci()

    const { carta: bene } = await apri(
      CASA,
      { "POST /api/v1/sites/1/sky/service": { stato: 200, corpo: CASA } },
      "k",
    )
    fireEvent.click(via(bene, "Dalla mappa"))
    await waitFor(() => expect(scritte("POST", "/sky/service")).toHaveLength(1))
    await attendi()
    expect(within(bene).queryByText(/non ha risposto/)).toBeNull()
    pulisci()

    const { carta: gia } = await apri({ ...CASA, sky_source: "service" }, {}, "k")
    fireEvent.click(via(gia, "Bortle a mano"))
    fireEvent.click(via(gia, "Dalla mappa"))
    await attendi()
    expect(scritture()).toEqual([])
  })

  it("Apri Servizi porta alla sezione Servizi", async () => {
    const { carta } = await apri(CASA)
    fireEvent.click(via(carta, "Dalla mappa"))
    fireEvent.click(within(carta).getByText("Apri Servizi"))
    await waitFor(() => expect(window.location.pathname).toBe("/impostazioni/servizi"))
  })

  it("Bortle a mano accende la classe del sito solo se viene dalla scala", async () => {
    const { carta } = await apri({ ...CASA, sky_source: "scale", bortle: 6 })
    const classi = within(carta).getByRole("group", { name: "Classe di Bortle" })
    expect(
      within(classi)
        .getAllByRole("button")
        .map((b) => `${b.textContent}${premuta(b) === "true" ? "*" : ""}`),
    ).toEqual(["1", "2", "3", "4", "5", "6*", "7", "8", "9"])
    pulisci()
    const { carta: misurato } = await apri({ ...CASA, sky_source: "measured", bortle: 6 })
    fireEvent.click(via(misurato, "Bortle a mano"))
    expect(within(misurato).getByText("Da 1, cielo buio, a 9, centro città.")).toBeTruthy()
    const tutte = within(
      within(misurato).getByRole("group", { name: "Classe di Bortle" }),
    ).getAllByRole("button")
    expect(tutte.filter((b) => premuta(b) === "true")).toEqual([])
  })

  it("SQM a mano: solo cifre, nell'intervallo dell'API, scritto lasciando il campo o con Invio", async () => {
    const { carta } = await apri(CASA, { "PATCH /api/v1/sites/1": { stato: 200, corpo: CASA } })
    expect(within(carta).getByText(/^Da un misuratore SQM/)).toBeTruthy()
    const campo = within(carta).getByRole("textbox", { name: /^SQM del sito/ }) as HTMLInputElement
    expect(campo.value).toBe("20,8")
    expect(campo.getAttribute("placeholder")).toBe("21,4")
    // lo stesso numero non si riscrive
    fireEvent.blur(campo)
    fireEvent.keyDown(campo, { key: "Enter" })
    await attendi()
    expect(scritture()).toEqual([])

    fireEvent.change(campo, { target: { value: "a25,0x9" } })
    expect(campo.value).toBe("25,09")
    expect(campo.getAttribute("aria-invalid")).toBe("true")
    expect(within(carta).getByText("✕ Un numero da 7 a 23.")).toBeTruthy()
    fireEvent.blur(campo)
    await attendi()
    expect(scritture()).toEqual([])

    fireEvent.change(campo, { target: { value: "6.9" } })
    expect(campo.getAttribute("aria-invalid")).toBe("true")
    fireEvent.change(campo, { target: { value: "7" } })
    expect(campo.getAttribute("aria-invalid")).toBe("false")
    fireEvent.change(campo, { target: { value: "23" } })
    expect(campo.getAttribute("aria-invalid")).toBe("false")

    fireEvent.change(campo, { target: { value: "21,45" } })
    expect(campo.getAttribute("aria-invalid")).toBe("false")
    expect(within(carta).queryByText(/Un numero da/)).toBeNull()
    fireEvent.keyDown(campo, { key: "a" })
    await attendi()
    expect(scritture()).toEqual([])
    fireEvent.keyDown(campo, { key: "Enter" })
    await waitFor(() =>
      expect(scritte("PATCH", "/api/v1/sites/1").map((s) => s.corpo)).toEqual([{ sky_sqm: 21.45 }]),
    )

    fireEvent.change(campo, { target: { value: "" } })
    expect(campo.getAttribute("aria-invalid")).toBe("false")
    fireEvent.blur(campo)
    await attendi()
    expect(scritte("PATCH", "/api/v1/sites/1")).toHaveLength(1)
  })

  it("SQM a mano parte vuoto se il cielo non e' stato misurato a mano", async () => {
    const { carta } = await apri(
      { ...CASA, sky_source: "service", sky_sqm: 19.6 },
      { "PATCH /api/v1/sites/1": { stato: 200, corpo: CASA } },
    )
    fireEvent.click(via(carta, "SQM a mano"))
    const campo = within(carta).getByRole("textbox", { name: /^SQM del sito/ }) as HTMLInputElement
    expect(campo.value).toBe("")
    fireEvent.change(campo, { target: { value: "19,6" } })
    fireEvent.blur(campo)
    await waitFor(() =>
      expect(scritte("PATCH", "/api/v1/sites/1").map((s) => s.corpo)).toEqual([{ sky_sqm: 19.6 }]),
    )
  })

  it("la proposta senza cielo: Lascia vuoto dice che resta senza", async () => {
    const sito: Sito = {
      ...CASA,
      sky_source: null,
      sky_sqm: null,
      bortle: null,
      measured: { ...BASTANO, propose: true },
    }
    const { carta } = await apri(sito, {
      "POST /api/v1/sites/1/sky/dismiss": { stato: 200, corpo: sito },
    })
    expect(
      within(carta).getByText(
        "Le misure di Cima Ekar dicono Bortle 4 – campagna più chiara (SQM 21,4, 38 notti in 10 mesi). Il sito non ha un cielo.",
      ),
    ).toBeTruthy()
    const pannello = within(carta).getByText("Usa Bortle 4").parentElement as HTMLElement
    fireEvent.click(within(pannello).getByText("Lascia vuoto"))
    expect(
      await within(carta).findByText(
        "✓ Il sito resta senza cielo; si propone di nuovo solo se la classe misurata cambia.",
      ),
    ).toBeTruthy()
    expect(scritte("POST", "/sky/dismiss")).toHaveLength(1)
    // l'esito sparisce aprendo una via
    fireEvent.click(via(carta, "Bortle a mano"))
    expect(within(carta).queryByText(/^✓/)).toBeNull()
  })

  it("la proposta con un cielo: Lascia lo tiene; una scrittura fallita non dice niente", async () => {
    const sito: Sito = { ...CASA, measured: { ...BASTANO, propose: true } }
    const { carta } = await apri(sito, {
      "POST /api/v1/sites/1/sky/dismiss": { stato: 200, corpo: sito },
      "POST /api/v1/sites/1/sky/use": { stato: 500, corpo: { detail: "no" } },
    })
    fireEvent.click(within(carta).getByText("Usa Bortle 4"))
    await waitFor(() => expect(scritte("POST", "/sky/use")).toHaveLength(1))
    await attendi()
    expect(within(carta).queryByText(/^✓/)).toBeNull()
    expect(premuta(via(carta, "Dalle misure"))).toBe("false")
    fireEvent.click(within(carta).getByText("Lascia Bortle 5"))
    expect(
      await within(carta).findByText(
        "✓ Resta Bortle 5; si propone di nuovo solo se la classe misurata cambia.",
      ),
    ).toBeTruthy()
  })

  it("Lascia fallito non dice niente; senza proposta niente pannello", async () => {
    const sito: Sito = { ...CASA, measured: { ...BASTANO, propose: true } }
    const { carta } = await apri(sito, {
      "POST /api/v1/sites/1/sky/dismiss": { stato: 500, corpo: { detail: "no" } },
    })
    fireEvent.click(within(carta).getByText("Lascia Bortle 5"))
    await waitFor(() => expect(scritte("POST", "/sky/dismiss")).toHaveLength(1))
    await attendi()
    expect(within(carta).queryByText(/^✓/)).toBeNull()
    pulisci()
    for (const m of [
      BASTANO,
      { ...BASTANO, propose: true, bortle: null },
      { ...BASTANO, propose: true, sqm: null },
    ]) {
      const { carta: senza } = await apri({ ...CASA, measured: m })
      expect(within(senza).queryByText(/^Usa Bortle/)).toBeNull()
      pulisci()
    }
  })

  it("i mesi: nessuna notte, poche, abbastanza", async () => {
    const casi: [Misurato, string][] = [
      [SITO_DI_CASA.measured, "Nessuna notte misurata: le misure arrivano con le notti."],
      [
        { ...POCHE, nights: 1, month_marks: [{ year: 2026, month: 3, measured: true }] },
        "Servono notti in almeno 4 mesi, senza buchi di oltre 3: finora 1 notte in 1 mese.",
      ],
      [POCHE, "Servono notti in almeno 4 mesi, senza buchi di oltre 3: finora 3 notti in 2 mesi."],
      [
        { ...BASTANO, sqm: null },
        "Servono notti in almeno 4 mesi, senza buchi di oltre 3: finora 38 notti in 8 mesi.",
      ],
      [
        { ...BASTANO, bortle: null },
        "Servono notti in almeno 4 mesi, senza buchi di oltre 3: finora 38 notti in 8 mesi.",
      ],
      [BASTANO, "Misurato su 38 notti in 8 mesi: SQM 21,4, Bortle 4 – campagna più chiara."],
    ]
    for (const [m, testo] of casi) {
      const { carta } = await apri({ ...CASA, measured: m })
      expect(within(carta).getByText(testo)).toBeTruthy()
      expect(within(carta).getByText(/^Contano i frame con lo SQM/)).toBeTruthy()
      expect(within(carta).queryAllByRole("img")).toHaveLength(m.month_marks.length ? 1 : 0)
      pulisci()
    }
    const { carta } = await apri({ ...CASA, measured: BASTANO })
    const mesi = within(carta).getByRole("img", { name: "8 mesi misurati sugli ultimi 12" })
    expect(
      [...mesi.children]
        .map((c) => `${c.textContent}${c.className.endsWith("--fatto") ? "+" : "-"}`)
        .join(" "),
    ).toBe("N+ D+ G- F+ M+ A- M+ G+ L- A+ S+ O-")
  })

  it("resta come nella consegna, su desktop e telefono", async () => {
    // impronta del markup della carta: classi, anelli e misure per formato della tavola v82
    const sito: Sito = {
      ...CASA,
      sky_source: "scale",
      bortle: 5,
      measured: { ...BASTANO, propose: true },
    }
    const visti: string[] = []
    for (const indirizzo of ["/impostazioni/siti", "/impostazioni/siti?formato=telefono"]) {
      const { carta } = await apri(sito, {}, null, indirizzo)
      visti.push(impronta(carta.outerHTML))
      fireEvent.click(via(carta, "SQM a mano"))
      fireEvent.change(within(carta).getByRole("textbox", { name: /^SQM del sito/ }), {
        target: { value: "30" },
      })
      visti.push(impronta(carta.outerHTML))
      fireEvent.click(via(carta, "Dalla mappa"))
      visti.push(impronta(carta.outerHTML))
      pulisci()
    }
    expect(visti).toEqual(["e13dd68c", "65f1fd9d", "78eba1d5", "b42427fe", "8b8a0e43", "c2e9b793"])
  })
})
