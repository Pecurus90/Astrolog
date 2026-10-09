// @vitest-environment jsdom
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

/**
 * La sezione **Oggetti** di *Da confermare*: una scheda per gruppo di frame, sempre uguale -- un
 * oggetto su cui l'app ha un dubbio, o frame che non dicono cosa e' stato ripreso. Si risponde in
 * un modo solo fra tre: una voce trovata nel campo, un nome scritto, "non e' un oggetto".
 */

const DUBBIO = {
  key: "object:ngc-7000",
  name: "NGC 7000",
  slug: "ngc-7000",
  method: "coord_review",
  confidence: "low",
  group: null,
  frames: 64,
  integration_s: 19080,
  untimed: 3,
  candidates: [
    { slug: "ngc-7000", name: "NGC 7000", common_name: "Nebulosa Nord America", in_frame: true },
    { slug: "ic-5070", name: "IC 5070", common_name: "Nebulosa Pellicano", in_frame: false },
    { slug: "ic-5068", name: "IC 5068", common_name: null, in_frame: null },
  ],
  answer: null,
}

const SENZA_NOME = {
  key: "frames:abc",
  name: null,
  slug: null,
  method: null,
  confidence: null,
  group: {
    night: "2025-08-12",
    camera: "ASI294MC",
    telescope: "RedCat 51",
    ra_deg: 83.8,
    dec_deg: -5.4,
    first_frame: "2025-08-12T23:50:00+02:00",
    last_frame: "2025-08-13T00:20:00+02:00",
  },
  frames: 18,
  integration_s: 2160,
  untimed: 0,
  candidates: [],
  answer: null,
}

const PAGINA = {
  to_confirm: 2,
  lookalikes: [],
  filters: [],
  filter_choices: [],
  gear: [],
  rig_choices: [],
  optics_choices: [],
  objects: [DUBBIO, SENZA_NOME],
  settled_objects: 218,
  typeless: [],
  unclear: [],
  mosaics: [],
}

function aperta(pagina: unknown = PAGINA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 64, run_started: true } },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

async function mandati() {
  fireEvent.click(screen.getByRole("button", { name: /applica/i }))
  let corpo: { objects: unknown[] } | undefined
  await waitFor(() => {
    corpo = scritture().find((s) => s.url.includes("/api/v1/review/apply"))?.corpo as typeof corpo
    expect(corpo).toBeDefined()
  })
  return corpo?.objects
}

const applicaSpento = () => expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
const prova = (dove: HTMLElement) =>
  [...dove.querySelectorAll("dl.as-domanda-prova > div")].map(
    (r) => `${r.querySelector("dt")?.textContent}=${r.querySelector("dd")?.textContent}`,
  )

describe("Da confermare -- gli oggetti", () => {
  it("la sezione c'e', nell'indice e in pagina, dopo i filtri e prima dei frame senza tipo", async () => {
    aperta({ ...PAGINA, typeless: [{ key: "D:/Astro/dark", frames: 12, answer: null }] })
    const sezione = await vaiASezione(/^oggetti$/i)
    expect(sezione.querySelector(".as-conferma-sezione__quante")?.textContent).toBe("2 domande")
    const indice = within(screen.getByRole("navigation", { name: "Sezioni" })).getAllByRole("listitem")
    expect(indice.map((v) => v.textContent)).toEqual(["Oggetti2", "Frame senza tipo1"])
  })

  it("un oggetto in dubbio mostra cosa c'e' nel campo, e per ogni voce se e' nell'inquadratura", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "NGC 7000")
    expect(scheda.querySelector(".as-domanda__nome .as-nome-oggetto")?.textContent).toBe("NGC 7000")
    expect(scheda.querySelector(".as-domanda__frame")?.textContent).toBe("64 frame \u00b7 5,3 h \u00b7 3 senza durata")
    // un dubbio non ha ne' puntamento ne' ore: quelli sono dei frame senza nome
    expect(prova(scheda)).toEqual([])
    const voci = within(scheda).getAllByRole("radio").map((r) => r.closest("label")?.textContent)
    expect(voci).toEqual([
      "NGC 7000 - Nebulosa Nord Americanell'inquadratura",
      "IC 5070 - Nebulosa Pellicanofuori dall'inquadratura",
      "IC 5068posizione non nota",
      "Altro nome",
      "Non \u00e8 un oggettoframe di prova o di messa a fuoco: esclusi dalle ore",
    ])
    expect(scheda.querySelector(".as-scelta-fissa__sub")?.textContent).toBe("nell'inquadratura")
    expect(within(scheda).getAllByRole("radio").some((r) => (r as HTMLInputElement).checked)).toBe(false)
  })

  it("scelta una voce del campo, la risposta porta la sua sigla", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "NGC 7000")
    fireEvent.click(within(scheda).getByRole("radio", { name: /IC 5070/ }))
    expect(await mandati()).toEqual([{ key: "object:ngc-7000", slug: "ic-5070", not_an_object: false }])
  })

  it("il nome si scrive, e un nome vuoto non e' una risposta", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "NGC 7000")
    fireEvent.click(within(scheda).getByRole("radio", { name: "Altro nome" }))
    applicaSpento()
    const campo = within(scheda).getByLabelText("Nome dell'oggetto")
    expect(campo.closest(".as-scelta-fissa__dopo")).not.toBeNull()
    fireEvent.change(campo, { target: { value: "   " } })
    applicaSpento()
    fireEvent.change(campo, { target: { value: " Sh2-117 " } })
    expect(await mandati()).toEqual([{ key: "object:ngc-7000", name: "Sh2-117", not_an_object: false }])
  })

  it("non e' un oggetto e' una risposta, e porta solo quella", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "NGC 7000")
    fireEvent.click(within(scheda).getByRole("radio", { name: /^Non \u00e8 un oggetto/ }))
    expect(await mandati()).toEqual([{ key: "object:ngc-7000", not_an_object: true }])
  })

  it("i frame senza nome si chiamano con la loro notte, e dicono camera, puntamento e ore", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "12 ago 2025")
    expect(scheda.querySelector(".as-domanda__frame")?.textContent).toBe("18 frame \u00b7 0,6 h")
    expect(prova(scheda)).toEqual([
      "Camera e telescopio=ASI294MC \u00b7 RedCat 51",
      "Puntamento=RA 83,8 Dec -5,4",
      "Primo e ultimo frame=23:50 - 00:20",
      "Oggetti nel campo=Nessuno",
    ])
    // senza voci dal campo restano due modi
    expect(within(scheda).getAllByRole("radio").map((r) => r.closest("label")?.querySelector(".as-scelta-fissa__nome")?.textContent)).toEqual([
      "Altro nome",
      "Non \u00e8 un oggetto",
    ])
  })

  it("frame senza nome che non dicono la notte, il puntamento o le ore lo dicono", async () => {
    aperta({
      ...PAGINA,
      objects: [
        { ...SENZA_NOME, group: { night: null, camera: null, telescope: null, ra_deg: null, dec_deg: null, first_frame: null, last_frame: null } },
      ],
    })
    const scheda = riga(await vaiASezione(/^oggetti$/i), "Frame senza nome")
    expect(prova(scheda)).toEqual([
      "Notte=Non indicata",
      "Camera e telescopio=Non indicati",
      "Puntamento=Non indicato",
      "Primo e ultimo frame=Non indicati",
      "Oggetti nel campo=Nessuno",
    ])
  })

  it("una risposta salvata si legge, e ridarla uguale non manda niente", async () => {
    aperta({
      ...PAGINA,
      objects: [
        { ...DUBBIO, answer: { kind: "catalog", value: "ic-5070", name: "IC 5070" } },
        { ...SENZA_NOME, answer: { kind: "none", value: null, name: null } },
      ],
    })
    const sezione = await vaiASezione(/^oggetti$/i)
    const chiuse = [...sezione.querySelectorAll(".as-domanda-riga")]
    expect(chiuse.map((c) => c.querySelector(".as-domanda-riga__breve")?.textContent)).toEqual(["IC 5070", "Non \u00e8 un oggetto"])
    const scheda = riga(sezione, "NGC 7000")
    expect(within(scheda).getByRole("radio", { name: /IC 5070/ })).toHaveProperty("checked", true)
    fireEvent.click(within(scheda).getByRole("radio", { name: /^NGC 7000/ }))
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", false)
    fireEvent.click(within(scheda).getByRole("radio", { name: /IC 5070/ }))
    applicaSpento()
  })

  it("un nome scritto che il catalogo conosce torna come nome scritto, e riscriverlo non manda niente", async () => {
    // senza voci nel campo la sigla salvata non e' fra le scelte: e' stata scritta in 'Altro nome'
    aperta({ ...PAGINA, objects: [{ ...SENZA_NOME, answer: { kind: "catalog", value: "m-31", name: "M 31" } }] })
    const scheda = riga(await vaiASezione(/^oggetti$/i), "12 ago 2025")
    expect(within(scheda).getByRole("radio", { name: "Altro nome" })).toHaveProperty("checked", true)
    const campo = within(scheda).getByLabelText("Nome dell'oggetto")
    expect(campo).toHaveProperty("value", "M 31")
    fireEvent.change(campo, { target: { value: "M 3" } })
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", false)
    fireEvent.change(campo, { target: { value: "M 31" } })
    applicaSpento()
  })

  it("in fondo dice quanti oggetti sono gia' riconosciuti", async () => {
    aperta()
    const sezione = await vaiASezione(/^oggetti$/i)
    expect(sezione.querySelector(".as-conferma-aposto p")?.textContent).toBe("218 oggetti riconosciuti")
    expect(sezione.querySelector(".as-conferma-aposto b")?.textContent).toBe("218")
  })
})
