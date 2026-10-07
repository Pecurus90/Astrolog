// @vitest-environment jsdom
/**
 * L'**Archivio**: la prima pagina che racconta cosa hai ripreso, invece di chiederti conto.
 *
 * Le regole che si provano qui vengono dal backend e la pagina deve solo **non tradirle**: le ore
 * arrivano gia' sommate (il frontend le porta in ore e basta), un frame senza tempo non diventa
 * zero, i filtri arrivano gia' in ordine. Lo scheletro e la barra dell'app stanno in
 * `layout.test.tsx`; i controlli dell'Archivio in `archivio-barra.test.tsx`, e il banco che i due
 * file si dividono in `archivio-banco.tsx`.
 *
 * La pagina ha **due viste** sulle stesse righe, e si apre a carte (Marco, 22/9/2026). Le prove
 * pescano le carte per il loro ruolo (`article`) e non per `listitem`: dentro una carta c'e' la
 * lista dei filtri, e contare gli elementi di lista conterebbe anche quelli.
 *
 * L'**ultima notte** non si mostra piu' (Marco, 22/9/2026: quel posto e' dei progetti), quindi le
 * due prove che la guardavano qui non hanno piu' un oggetto. Che una data si scriva come data e
 * resti la stessa da un altro fuso ha gia' la sua casa in `frontend/tests/formati.test.ts`.
 * test-tolto: "la notte si scrive come una data, non come esce dal database"
 * test-tolto: "un oggetto che nessuna notte ha raccolto lo dice, invece di mostrare una data"
 * test-tolto: "dice quanti oggetti ci sono in tutto, non quanti ne stai vedendo" -- promette la
 * regola **rovesciata** rispetto a questa fetta (la conta e' quella che hai trovato, non quella
 * che hai): rinominata in "dice quanti ne ha trovati, non quanti ne stai vedendo".
 */
import { readFileSync, readdirSync } from "node:fs"
import { resolve } from "node:path"

import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { pulisci, rispondi } from "./banco"
import {
  IGNOTO,
  M31,
  apriArchivio,
  apriArchivioSu,
  archivio,
  conArchivio,
  vaiAll,
} from "./archivio-banco"

afterEach(pulisci)

describe("l'Archivio", () => {
  it("dice cosa hai ripreso, con i frame e le ore", async () => {
    archivio([M31])
    await apriArchivio()

    const carta = await screen.findByRole("article")
    expect(within(carta).getByText("M 31")).toBeDefined()
    expect(carta.textContent).toContain("120")
    // 43.200 s = 12 h: il backend manda i secondi, lo schermo legge le ore
    expect(carta.textContent).toContain("12")
  })

  it("un frame che non dice quanto e' durato non diventa zero", async () => {
    // E' la terza forma del dato: "non lo so" non e' "niente". Senza questa riga a schermo, chi
    // guarda le ore di un oggetto crede che siano tutte li' -- e sono di meno.
    archivio([IGNOTO])
    await apriArchivio()

    expect(await screen.findByText(/12 senza tempo/i)).toBeDefined()
  })

  it("se nessun frame dice la durata, non scrive zero ore", async () => {
    // Zero ore e "non lo so" sono due risposte diverse: dove il tempo non si sa, il numero delle
    // ore non compare, e restano solo i frame senza tempo.
    archivio([{ ...IGNOTO, frames: 3, untimed: 3, integration_s: 0 }])
    await apriArchivio()

    const carta = await screen.findByRole("article")
    expect(carta.textContent).toContain("3 senza tempo")
    expect(carta.textContent).not.toMatch(/\b0 h\b/)
  })

  it("si apre a carte, e l'altra vista e' a un clic", async () => {
    archivio([M31])
    await apriArchivio()

    expect(await screen.findByRole("tab", { name: /carte/i })).toHaveProperty(
      "ariaSelected",
      "true",
    )
    await vaiAll(/elenco/i)

    expect(await screen.findByRole("table")).toBeDefined()
    expect(screen.queryByRole("article")).toBeNull()
  })

  it("quale vista stai guardando resta nell'indirizzo", async () => {
    // Un collegamento all'elenco che si riapre a carte non e' un collegamento a quella vista:
    // chi lo manda a qualcuno manda un'altra pagina.
    archivio([M31])
    await apriArchivio()

    await vaiAll(/elenco/i)

    expect(window.location.search).toContain("vista=elenco")
  })

  it("cambiare vista non cancella il resto dell'indirizzo", async () => {
    // La barra che arriva (cerca, filtri, ordine) scrivera' i suoi li' dentro: un interruttore che
    // riscrive la query intera glieli cancellerebbe a ogni clic, e il filtro sparirebbe cambiando
    // vista senza che nessuno capisca perche'.
    archivio([M31])
    await apriArchivio()
    // un parametro **vero** della barra: quando questa prova e' nata la barra non c'era ancora e
    // ne usava uno inventato, che non avrebbe protetto niente
    fireEvent.click(await screen.findByRole("button", { name: /^ore$/i }))
    await waitFor(() => expect(window.location.search).toContain("sort=hours"))

    await vaiAll(/elenco/i)

    expect(window.location.search).toContain("sort=hours")
    expect(window.location.search).toContain("vista=elenco")
  })

  it("dice con che filtri hai ripreso, nell'ordine dei filtri", async () => {
    // L'ordine e' del backend, uno in tutta l'app (L, R, G, B, Ha, OIII, SII...): rimescolarlo qui
    // metterebbe la stessa pastiglia in due posti su due pagine.
    archivio([M31])
    await apriArchivio()

    const filtri = await screen.findByRole("list", { name: /con che filtri/i })
    const nomi = within(filtri)
      .getAllByRole("listitem")
      .map((l) => l.querySelector(".as-ore-filtro__nome")?.textContent)
    expect(nomi).toEqual(["Lum", "Ha"])
  })

  it("ogni filtro porta il colore della sua banda, nella forma che il foglio disegna", async () => {
    // Tre regole in una: la variante sta **sulla voce** (il foglio risolve i quattro slot di
    // colore sullo stesso elemento che porta la classe, non su un involucro dentro), dentro c'e'
    // la pastiglia, e il nome ha la sua classe. Le macchine della veste non possono vederlo --
    // guardano le classi **scritte**, non su quale elemento finiscono -- ed e' proprio il pezzo
    // che ha cambiato forma due volte.
    archivio([M31])
    await apriArchivio()

    const voci = within(
      await screen.findByRole("list", { name: /con che filtri/i }),
    ).getAllByRole("listitem")

    expect(voci.map((v) => v.className)).toEqual([
      "as-ore-filtro__voce as-filtro--l",
      "as-ore-filtro__voce as-filtro--ha",
    ])
    const prima = voci[0]
    expect(prima?.querySelector(".as-filtro__pastiglia")).not.toBeNull()
    expect(prima?.querySelector(".as-ore-filtro__nome")?.textContent).toBe("Lum")
  })

  it("un oggetto senza filtri riconosciuti non mostra pastiglie finte", async () => {
    archivio([IGNOTO])
    await apriArchivio()

    // si aspetta la **carta**, non il titolo: il titolo c'e' gia' mentre la pagina carica, e un
    // `queryBy` su una pagina ancora vuota non trova niente qualunque cosa faccia il codice
    await screen.findByRole("article")
    expect(screen.queryByRole("list", { name: /con che filtri/i })).toBeNull()
  })

  it("un oggetto che il catalogo non conosce non porta un soprattitolo vuoto", async () => {
    // Un paragrafo vuoto non si vede, ma il suo margine si vede: in una griglia il titolo di
    // quella carta scende rispetto a tutte le altre, e nessuno capisce perche'.
    archivio([IGNOTO])
    await apriArchivio()

    const carta = await screen.findByRole("article")
    expect(carta.querySelector(".as-soprattitolo")).toBeNull()
  })

  it("nell'elenco le celle che non sanno lo dicono con una forma, non con un vuoto", async () => {
    archivio([IGNOTO])
    await apriArchivio()
    await vaiAll(/elenco/i)

    const tabella = await screen.findByRole("table")
    expect(within(tabella).getAllByRole("row")).toHaveLength(2) // l'intestazione, piu' l'unica riga
    // tipo, costellazione e filtri: tre celle che il catalogo non sa riempire, e ognuna lo dice
    // con una **parola** E con la forma della terza forma del dato -- non col solo colore, e non
    // con `as-dato--vuoto`, che nel foglio vuol dire "una misura vera che vale zero"
    expect(within(tabella).getAllByText(/non si sa/i)).toHaveLength(3)
    expect(tabella.querySelectorAll(".as-dato--ignoto")).toHaveLength(3)
    expect(tabella.querySelector(".as-dato--vuoto")).toBeNull()
  })

  it("dice quanti ne ha trovati, non quanti ne stai vedendo", async () => {
    // Due numeri diversi: quello che la pagina scrive e' il **totale che passa il filtro**, non
    // le righe che hai in mano. Con un filtro acceso "1.240 oggetti" sarebbe un numero che mente,
    // ed e' anche quello su cui la pagina decide se c'e' un'altra pagina.
    archivio([M31], { total: 600, limit: 1 })
    await apriArchivio()

    expect(await screen.findByText(/600 oggetti/i)).toBeDefined()
    expect(await screen.findAllByRole("article")).toHaveLength(1)
  })

  it("a mani vuote dice cosa fare, non nessun risultato", async () => {
    // Chi ha appena installato l'app non ha sbagliato niente: la pagina vuota e' uno stato
    // legittimo, e deve portare al gesto che lo riempie.
    archivio([])
    await apriArchivio()

    expect(await screen.findByText(/non c'e' ancora niente/i)).toBeDefined()
    // e porta al gesto che lo riempie, invece di lasciarti fermo li'
    expect(screen.getByRole("link", { name: /scegli le cartelle/i })).toBeDefined()
    expect(screen.queryByRole("alert")).toBeNull()
  })

  it("e a mani vuote un ordine nell'indirizzo non fa comparire la barra", async () => {
    // Un collegamento fabbricato, o quello che ti sei mandato prima di svuotare la cartella:
    // l'ordine non stringe niente, quindi non c'e' niente da togliere, e una barra qui sarebbe un
    // campo che non puo' cercare niente accanto alle parole di chi ha appena installato l'app.
    archivio([])
    const reso = await apriArchivioSu("/archivio?sort=hours")

    expect(await screen.findByText(/non c'e' ancora niente/i)).toBeDefined()
    expect(screen.queryByLabelText(/cerca un oggetto/i)).toBeNull()
    reso.unmount()
  })

  it("ogni tipo che il catalogo usa ha la sua parola, e nessuno arriva a schermo come sigla", async () => {
    // I codici si leggono dal catalogo **impacchettato**, non da una lista scritta qui: se un
    // catalogo nuovo ne aggiunge uno, questa prova diventa rossa invece di lasciarlo sparire in
    // silenzio dalla pagina.
    // Da `frontend/`, dove vitest gira: sotto jsdom `import.meta.url` e' un indirizzo web, non un
    // file, e non porta al repo.
    const cartella = resolve(process.cwd(), "..", "backend", "astrolog", "catalog", "data")
    const file = readdirSync(cartella).find((n) => /^catalogo-.*\.json$/.test(n))
    expect(file, `nessun catalogo in ${cartella}`).toBeDefined()
    const catalogo = JSON.parse(readFileSync(resolve(cartella, file ?? ""), "utf-8")) as {
      objects: { type_code: string }[]
    }
    const codici = [...new Set(catalogo.objects.map((o) => o.type_code))]
    expect(codici.length).toBeGreaterThan(0)

    archivio(
      codici.map((codice, i) => ({ ...M31, key: `k-${i}`, name: `Oggetto ${i}`, type_code: codice })),
    )
    await apriArchivio()

    const carte = await screen.findAllByRole("article")
    expect(carte).toHaveLength(codici.length)
    for (const [i, carta] of carte.entries()) {
      expect(carta.textContent, `il codice ${codici[i]} non ha una parola`).toMatch(/Andromeda \u00b7 \S/)
      expect(carta.textContent).not.toContain(codici[i])
    }
  })

  it("un tipo che la pagina non conosce non si mostra affatto", async () => {
    archivio([{ ...M31, type_code: "CODICE_INVENTATO" }])
    await apriArchivio()

    const carta = await screen.findByRole("article")
    expect(carta.textContent).toContain("And")
    expect(carta.textContent).not.toContain("CODICE_INVENTATO")
    expect(carta.textContent).not.toContain("\u00b7")
  })

  it("se l archivio non risponde lo dice, invece di sembrare vuoto", async () => {
    rispondi(conArchivio({ stato: 500, corpo: { detail: "boom" } }))
    await apriArchivio()

    expect(await screen.findByRole("alert")).toBeDefined()
  })

  it("quando ce n e piu' di una pagina, si possono vedere anche gli altri", async () => {
    // Mostrare cento righe su seicento senza una strada per le altre e' un archivio che mente
    // per omissione: la pagina nasce nuda, non incompleta.
    archivio([M31], { total: 600, limit: 1 })
    await apriArchivio()

    expect(await screen.findByRole("button", { name: /mostra altri/i })).toBeDefined()
  })

  it("e quando sono tutte li', non offre di caricarne altre", async () => {
    archivio([M31, IGNOTO])
    await apriArchivio()

    await screen.findAllByRole("article")
    expect(screen.queryByRole("button", { name: /mostra altri/i })).toBeNull()
  })
})

describe("l'Archivio, filtri e costellazioni", () => {
  it("ogni filtro dice le sue ore, nelle carte e nell'elenco", async () => {
    archivio([M31])
    await apriArchivio()

    const filtri = await screen.findByRole("list", { name: /filtri/i })
    // 28.800 s = 8 h al Lum, 14.400 s = 4 h all'Ha: arrivano gia' sommate dal backend
    expect(filtri.textContent).toMatch(/Lum\s*8 h/)
    expect(filtri.textContent).toMatch(/Ha\s*4 h/)

    await vaiAll(/elenco/i)
    const riga = (await screen.findByText("M 31")).closest("tr") as HTMLElement
    expect(riga.textContent).toMatch(/Lum\s*8 h/)
    expect(riga.textContent).toMatch(/Ha\s*4 h/)
  })

  it("un filtro le cui pose non dicono la durata non scrive ore", async () => {
    // "0 h" direbbe che con quel filtro non hai ripreso niente: ha ripreso, e non si sa per quanto.
    archivio([{ ...M31, filters: [{ name: "Lum", passband: "L", frames: 80, integration_s: 0 }] }])
    await apriArchivio()

    const filtri = await screen.findByRole("list", { name: /filtri/i })
    expect(filtri.textContent).toBe("Lum")
    // e niente casella delle ore vuota, che il foglio disegnerebbe comunque
    expect(filtri.querySelector(".as-ore-filtro__ore")).toBeNull()
  })

  it("la costellazione si legge col suo nome latino, non con la sigla", async () => {
    archivio([M31])
    await apriArchivio()

    const carta = await screen.findByRole("article")
    expect(carta.textContent).toContain("Andromeda")
    expect(carta.textContent).not.toMatch(/\bAnd\b/)

    await vaiAll(/elenco/i)
    const riga = (await screen.findByText("M 31")).closest("tr") as HTMLElement
    expect(riga.textContent).toContain("Andromeda")
    expect(riga.textContent).not.toMatch(/\bAnd\b/)
  })
})

