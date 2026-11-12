// @vitest-environment jsdom
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  STANOTTE,
  chiamate,
  daConfermare,
  impostazioni,
  pulisci,
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
 * Gli **oggetti identificati** di *Da confermare* (tavola v82, 254-260): quelli che l'app
 * riconosce da sola. Non sono domande: stanno chiusi in fondo alla sezione Oggetti, si aprono
 * cinque alla volta e poi cinquanta, e da li' si correggono con una scheda sotto la riga; la
 * correzione parte con Applica, insieme alle altre risposte.
 */

const aPosto = (n: number) =>
  schedaOggetto({
    key: `object:m-${n}`,
    name: `M ${n}`,
    slug: `m-${n}`,
    common_name: n === 1 ? "Nebulosa del Granchio" : null,
    method: "coord_confirmed",
    confidence: "high",
    frames: 100 + n,
    integration_s: 3600,
  })
const TOTALE = 60
const TUTTI = Array.from({ length: TOTALE }, (_, i) => aPosto(i + 1))
const primi = (quanti: number) => ({ items: TUTTI.slice(0, quanti), total: TOTALE, limit: quanti, offset: 0 })

const DUBBIO = schedaOggetto({
  key: "object:ngc-7000",
  name: "NGC 7000",
  slug: "ngc-7000",
  confidence: "low",
  frames: 64,
  candidates: [{ slug: "ic-5070", name: "IC 5070", common_name: null, in_frame: true }],
})

const PAGINA = daConfermare({ to_confirm: 1, objects: [DUBBIO], settled_objects: TOTALE })

function aperta(principale: unknown = PAGINA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 103, run_started: true } },
    // prima delle rotte piu' corte: il banco sceglie la prima che l'indirizzo contiene
    "/api/v1/review/objects/settled?limit=5&offset=0": { stato: 200, corpo: primi(5) },
    "/api/v1/review/objects/settled?limit=55&offset=0": { stato: 200, corpo: primi(55) },
    "/api/v1/review": { stato: 200, corpo: principale },
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

const gesto = (sezione: HTMLElement) => within(sezione).getByRole("button", { name: `${TOTALE} oggetti identificati` })
const righe = (sezione: HTMLElement) => [...sezione.querySelectorAll<HTMLElement>("li.al-conf__riga-16")]
const nomi = (sezione: HTMLElement) => righe(sezione).map((r) => r.querySelector(".al-conf__testo-18")?.textContent)
const correzione = (sezione: HTMLElement) => sezione.querySelector<HTMLElement>("li.al-conf__corr") as HTMLElement
const piede = () => screen.getByRole("region", { name: "Le modifiche da applicare" }).querySelector(".al-conf__riga-18")?.textContent

async function aperti() {
  const sezione = await vaiASezione(/^oggetti$/i)
  fireEvent.click(gesto(sezione))
  await within(sezione).findByRole("button", { name: "Correggi: M 1" })
  return sezione
}

describe("Da confermare -- gli oggetti identificati", () => {
  it("chiusi sono un numero e un gesto, e non chiedono niente all'API", async () => {
    aperta()
    const sezione = await vaiASezione(/^oggetti$/i)
    expect(gesto(sezione).getAttribute("aria-expanded")).toBe("false")
    expect(righe(sezione)).toEqual([])
    expect(chiamate().some((u) => u.includes("/objects/settled"))).toBe(false)
  })

  it("aperti sono cinque righe senza stato, col gesto Correggi, e poi altri 50", async () => {
    aperta()
    const sezione = await aperti()
    expect(gesto(sezione).getAttribute("aria-expanded")).toBe("true")
    expect(chiamate().filter((u) => u.includes("/objects/settled"))).toEqual([
      expect.stringContaining("/api/v1/review/objects/settled?limit=5&offset=0"),
    ])
    expect(nomi(sezione)).toEqual(["M 1", "M 2", "M 3", "M 4", "M 5"])
    // non e' una domanda: niente stato, e il gesto dice di quale riga
    const prima = righe(sezione)[0] as HTMLElement
    expect(prima.querySelector(".al-conf__riga-7")).toBeNull()
    expect(prima.querySelector(".al-conf__testo-10")?.textContent).toBe("Nebulosa del Granchio · 101 frame")
    expect(within(prima).getByRole("button").textContent).toBe("Correggi")

    fireEvent.click(within(sezione).getByRole("button", { name: "Mostra altri 50 di 55" }))
    await within(sezione).findByRole("button", { name: "Correggi: M 55" })
    expect(chiamate().some((u) => u.includes("/api/v1/review/objects/settled?limit=55&offset=0"))).toBe(true)
    expect(righe(sezione)).toHaveLength(55)
    expect(within(sezione).getByRole("button", { name: "Mostra altri 5 di 5" })).toBeDefined()
  })

  it("il gesto li richiude, e aprirli chiude la domanda aperta: una cosa aperta alla volta", async () => {
    aperta()
    const sezione = await vaiASezione(/^oggetti$/i)
    expect(sezione.querySelector("article.al-conf__colonna-16")).not.toBeNull()
    fireEvent.click(gesto(sezione))
    await within(sezione).findByRole("button", { name: "Correggi: M 1" })
    expect(sezione.querySelector("article.al-conf__colonna-16")).toBeNull()
    // nessuna domanda aperta: il perche' della sezione non si legge (tavola, `aperta: null`)
    expect(sezione.querySelector("p.al-conf__blocco-8")).toBeNull()
    fireEvent.click(gesto(sezione))
    expect(righe(sezione)).toEqual([])
    expect(gesto(sezione).getAttribute("aria-expanded")).toBe("false")
  })

  it("con tutte le domande risposte, aprirli non chiude la sezione: l'elenco si vede al primo clic", async () => {
    aperta()
    const sezione = await vaiASezione(/^oggetti$/i)
    fireEvent.click(scelta(sezione, "IC 5070"))
    fireEvent.click(gesto(screen.getByRole("region", { name: /^oggetti$/i })))
    const dopo = screen.getByRole("region", { name: /^oggetti$/i })
    expect(await within(dopo).findByRole("button", { name: "Correggi: M 1" })).toBeDefined()
  })

  it("Correggi apre sotto la riga la scheda, col nome di adesso gia' scelto", async () => {
    aperta()
    const sezione = await aperti()
    fireEvent.click(within(sezione).getByRole("button", { name: "Correggi: M 3" }))
    const scheda = correzione(sezione)
    // sotto la sua riga, non in fondo
    expect(scheda.previousElementSibling).toBe(righe(sezione)[2])
    expect(within(sezione).getByRole("button", { name: "Chiudi: M 3" })).toBeDefined()
    expect(within(scheda).getByRole("radiogroup").getAttribute("aria-label")).toBe("Che oggetto è M 3?")
    expect(voci(scheda)).toEqual([
      "[x] Resta M 3 / come l'ha riconosciuto l'app",
      "Altro nome",
      "Non è un oggetto / frame di prova o di messa a fuoco: esclusi dalle ore",
    ])
    expect(scheda.textContent).toMatch(/Vale per tutti i 103 frame\. Si salva con Applica, con le altre risposte\./)
    // aperta senza toccare niente non e' una modifica
    expect(screen.getByRole("button", { name: /applica/i }).getAttribute("aria-disabled")).toBe("true")
  })

  it("Non e' un oggetto va nell'Applica, con le altre risposte", async () => {
    aperta()
    const sezione = await aperti()
    fireEvent.click(within(sezione).getByRole("button", { name: "Correggi: M 3" }))
    fireEvent.click(scelta(correzione(sezione), /^Non è un oggetto/))
    expect(scelto(scelta(correzione(sezione), /^Non è un oggetto/))).toBe(true)
    expect(piede()).toBe("1modifica da applicare")
    expect(await mandati()).toEqual([{ key: "object:m-3", not_an_object: true }])
  })

  it("un altro nome si scrive; vuoto, o tornati a Resta, non c'e' niente da mandare", async () => {
    aperta()
    const sezione = await aperti()
    fireEvent.click(within(sezione).getByRole("button", { name: "Correggi: M 3" }))
    fireEvent.click(scelta(correzione(sezione), "Altro nome"))
    const campo = within(correzione(sezione)).getByLabelText("Nome dell'oggetto")
    expect(piede()).toBe("0modifiche da applicare")
    fireEvent.change(campo, { target: { value: "  " } })
    expect(piede()).toBe("0modifiche da applicare")
    fireEvent.change(campo, { target: { value: " NGC 5272 " } })
    expect(piede()).toBe("1modifica da applicare")
    fireEvent.click(scelta(correzione(sezione), /^Resta M 3/))
    expect(piede()).toBe("0modifiche da applicare")
    fireEvent.click(scelta(correzione(sezione), "Altro nome"))
    // il nome scritto e' della riga: torna com'era
    expect(within(correzione(sezione)).getByLabelText("Nome dell'oggetto")).toHaveProperty("value", " NGC 5272 ")
    expect(await mandati()).toEqual([{ key: "object:m-3", name: "NGC 5272", not_an_object: false }])
  })

  it("il nome di adesso riscritto in Altro nome non e' una correzione", async () => {
    aperta()
    const sezione = await aperti()
    fireEvent.click(within(sezione).getByRole("button", { name: "Correggi: M 3" }))
    fireEvent.click(scelta(correzione(sezione), "Altro nome"))
    fireEvent.change(within(correzione(sezione)).getByLabelText("Nome dell'oggetto"), { target: { value: " M 3 " } })
    expect(piede()).toBe("0modifiche da applicare")
  })

  it("senza domande aperte la sezione c'e' lo stesso: gli oggetti identificati si correggono da li'", async () => {
    aperta({ ...PAGINA, to_confirm: 0, objects: [] })
    const sezione = await vaiASezione(/^oggetti$/i)
    expect(gesto(sezione)).toBeDefined()
    // che non c'e' niente da fare si dice lo stesso
    expect(screen.getByText("Niente da confermare")).toBeDefined()
  })
})
