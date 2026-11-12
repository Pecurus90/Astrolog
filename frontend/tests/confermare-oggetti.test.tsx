// @vitest-environment jsdom
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  STANOTTE,
  cartellaSenzaTipo,
  daConfermare,
  domande,
  impostazioni,
  prove,
  pulisci,
  riga,
  rispondi,
  scelta,
  scelto,
  schedaOggetto,
  scritture,
  vaiASezione,
  voci,
} from "./banco"

afterEach(pulisci)

/**
 * La sezione **Oggetti** di *Da confermare*: una scheda per gruppo di frame, sempre uguale -- un
 * oggetto su cui l'app ha un dubbio, o frame che non dicono cosa e' stato ripreso. Si risponde in
 * un modo solo fra tre: una voce trovata nel campo, un nome scritto, "non e' un oggetto".
 */

const DUBBIO = schedaOggetto({
  key: "object:ngc-7000",
  name: "NGC 7000",
  slug: "ngc-7000",
  method: "coord_review",
  confidence: "low",
  nights: ["2025-08-12"],
  rigs: [{ optics: "RedCat 51", camera: "ASI294MC", frames: 64 }],
  frames: 64,
  integration_s: 19080,
  untimed: 3,
  candidates: [
    { slug: "ngc-7000", name: "NGC 7000", common_name: "Nebulosa Nord America", in_frame: true },
    { slug: "ic-5070", name: "IC 5070", common_name: "Nebulosa Pellicano", in_frame: false },
    { slug: "ic-5068", name: "IC 5068", common_name: null, in_frame: null },
  ],
})

const SENZA_NOME = schedaOggetto({
  key: "frames:abc",
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
})

const PAGINA = daConfermare({ to_confirm: 2, objects: [DUBBIO, SENZA_NOME], settled_objects: 218 })

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

const applicaSpento = () => expect(screen.getByRole("button", { name: /applica/i }).getAttribute("aria-disabled")).toBe("true")
const frame = (scheda: HTMLElement) => scheda.querySelector(":scope > .al-conf__colonna-17 > .al-conf__testo-7")?.textContent

describe("Da confermare -- gli oggetti", () => {
  it("la sezione c'e', nell'indice e in pagina, dopo i filtri e prima dei frame senza tipo", async () => {
    aperta({ ...PAGINA, typeless: [cartellaSenzaTipo({ key: "D:/Astro/dark", frames: 12 })] })
    const sezione = await vaiASezione(/^oggetti$/i)
    expect(sezione.querySelector("header .al-conf__testo-10")?.textContent).toBe("2 domande")
    const indice = within(screen.getByRole("navigation", { name: "Sezioni" })).getAllByRole("listitem")
    // il nome, quante senza risposta, e il tondo col numero
    expect(indice.map((v) => v.textContent)).toEqual(["Oggetti2 senza risposta2", "Frame senza tipo1 senza risposta1"])
  })

  it("un oggetto in dubbio dice perche' l'app dubita, e per ogni voce se e' nell'inquadratura", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "NGC 7000")
    expect(scheda.querySelector("h3")?.textContent).toBe("NGC 7000")
    expect(frame(scheda)).toBe("64 frame \u00b7 5 h 18 \u00b7 3 senza durata")
    // un dubbio non ha ne' puntamento ne' arco: quelli sono dei frame senza nome
    expect(prove(scheda)).toEqual([
      "Perch\u00e9 l'app dubita=metodo: plate solving | fiducia bassa",
      "Notte=12 ago 2025",
      "Ottica e camera=RedCat 51 \u00b7 ASI294MC",
    ])
    expect(voci(scheda)).toEqual([
      "NGC 7000 \u00b7 Nebulosa Nord America / nell'inquadratura",
      "IC 5070 \u00b7 Nebulosa Pellicano / fuori dall'inquadratura",
      "IC 5068 / posizione non nota",
      "Altro nome",
      "Non \u00e8 un oggetto / frame di prova o di messa a fuoco: esclusi dalle ore",
    ])
  })

  it("scelta una voce del campo, la risposta porta la sua sigla", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "NGC 7000")
    fireEvent.click(scelta(scheda, /IC 5070/))
    expect(await mandati()).toEqual([{ key: "object:ngc-7000", slug: "ic-5070", not_an_object: false }])
  })

  it("il nome si scrive, e un nome vuoto non e' una risposta", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "NGC 7000")
    fireEvent.click(scelta(scheda, "Altro nome"))
    applicaSpento()
    const campo = within(scheda).getByLabelText("Nome dell'oggetto")
    fireEvent.change(campo, { target: { value: "   " } })
    applicaSpento()
    fireEvent.change(campo, { target: { value: " Sh2-117 " } })
    expect(await mandati()).toEqual([{ key: "object:ngc-7000", name: "Sh2-117", not_an_object: false }])
  })

  it("non e' un oggetto e' una risposta, e porta solo quella", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "NGC 7000")
    fireEvent.click(scelta(scheda, /^Non \u00e8 un oggetto/))
    expect(await mandati()).toEqual([{ key: "object:ngc-7000", not_an_object: true }])
  })

  it("i frame senza nome si chiamano cosi', e la notte, gli strumenti, il puntamento e l'arco stanno nelle prove", async () => {
    aperta()
    const scheda = riga(await vaiASezione(/^oggetti$/i), "Frame senza nome")
    // chi ascolta distingue due gruppi senza nome dalla notte e dalla camera
    expect(scheda.getAttribute("aria-label")).toBe("Frame senza nome, 12 ago 2025, ASI294MC, senza risposta")
    expect(frame(scheda)).toBe("18 frame \u00b7 36 min")
    expect(prove(scheda)).toEqual([
      "Oggetti nel campo=Nessun oggetto trovato: il plate solving non riconosce il campo",
      "Notte=12 ago 2025",
      "Camera e telescopio=ASI294MC \u00b7 RedCat 51",
      "Puntamento=RA 83,8 Dec \u22125,4",
      "Primo e ultimo frame=23:50–00:20",
    ])
    // senza voci dal campo restano due modi
    expect(voci(scheda)).toEqual(["Altro nome", "Non \u00e8 un oggetto / frame di prova o di messa a fuoco: esclusi dalle ore"])
  })

  it("frame senza nome che non dicono la notte, il puntamento o le ore lo dicono", async () => {
    aperta({
      ...PAGINA,
      objects: [
        {
          ...SENZA_NOME,
          searched: false,
          group: { night: null, camera: null, telescope: null, ra_deg: null, dec_deg: null, first_frame: null, last_frame: null },
        },
      ],
    })
    const scheda = riga(await vaiASezione(/^oggetti$/i), "Frame senza nome")
    expect(prove(scheda)).toEqual([
      "Oggetti nel campo=Non ancora cercato: il plate solving non \u00e8 ancora passato su questi frame",
      "Notte=Non indicata",
      "Camera e telescopio=Non indicati",
      "Puntamento=Non indicato",
      "Primo e ultimo frame=Non indicati",
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
    expect(domande(sezione).map((c) => c.querySelector(".al-conf__blocco-9")?.textContent)).toEqual(["IC 5070", "Non \u00e8 un oggetto"])
    const scheda = riga(sezione, "NGC 7000")
    expect(scelto(scelta(scheda, /IC 5070/))).toBe(true)
    fireEvent.click(scelta(scheda, /^NGC 7000/))
    expect(screen.getByRole("button", { name: /applica/i }).getAttribute("aria-disabled")).toBeNull()
    fireEvent.click(scelta(scheda, /IC 5070/))
    applicaSpento()
  })

  it("un nome scritto che il catalogo conosce torna come nome scritto, e riscriverlo non manda niente", async () => {
    // senza voci nel campo la sigla salvata non e' fra le scelte: e' stata scritta in 'Altro nome'
    aperta({ ...PAGINA, objects: [{ ...SENZA_NOME, answer: { kind: "catalog", value: "m-31", name: "M 31" } }] })
    const scheda = riga(await vaiASezione(/^oggetti$/i), "Frame senza nome")
    expect(scelto(scelta(scheda, "Altro nome"))).toBe(true)
    const campo = within(scheda).getByLabelText("Nome dell'oggetto")
    expect(campo).toHaveProperty("value", "M 31")
    fireEvent.change(campo, { target: { value: "M 3" } })
    expect(screen.getByRole("button", { name: /applica/i }).getAttribute("aria-disabled")).toBeNull()
    fireEvent.change(campo, { target: { value: "M 31" } })
    applicaSpento()
  })

  it("in fondo dice quanti oggetti sono gia' identificati, chiusi", async () => {
    aperta()
    const sezione = await vaiASezione(/^oggetti$/i)
    const gesto = within(sezione).getByRole("button", { name: "218 oggetti identificati" })
    expect(gesto.getAttribute("aria-expanded")).toBe("false")
  })
})
