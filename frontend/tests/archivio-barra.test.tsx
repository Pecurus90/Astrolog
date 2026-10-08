// @vitest-environment jsdom
/**
 * La **barra dell'Archivio**: cerca, le tendine, l'ordine, e cosa si vede mentre la risposta
 * arriva.
 *
 * File suo perche' `archivio.test.tsx` ha superato il tetto di righe: li' stanno le regole della
 * **pagina** (cosa mostra una riga, le due viste, gli stati vuoti), qui quelle dei **controlli**.
 * Il banco -- le righe di prova e i due gesti per arrivare alla pagina -- e' in
 * `archivio-banco.tsx`, uno solo per tutti e due: due copie di un banco sono una prova e una
 * copia che un giorno racconta un archivio diverso.
 *
 * La regola che tiene insieme quasi tutto: **qui non si filtra niente**. Ogni controllo scrive
 * nell'indirizzo e il backend risponde -- cercare fra le cento righe gia' scaricate troverebbe
 * solo quelle, e a chi ha seicento oggetti l'app direbbe "non trovato" mentendo.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { BarraDellArchivio } from "../src/BarraDellArchivio"
import { cambia, chiamate, disegna, fuoriDaiMattoni, pulisci, quantiControlli } from "./banco"
import {
  M31,
  SCELTE,
  apriArchivio,
  apriArchivioSu,
  archivio,
  conArchivio,
  laBarra,
  laTendina,
  scegli,
  vaiAll,
  voceArchivio,
  vociDi,
} from "./archivio-banco"

afterEach(pulisci)

/** La conta come si legge: i numeri stanno in un `<b>`, quindi il testo e' su piu' nodi. */
const laConta = () => document.querySelector(".as-archivio__conta")?.textContent

/** Il bottone "Rimuovi filtri" del vuoto: quando un filtro non trova niente ce n'e' anche uno nella
 *  barra, e questo e' quello che sta dove l'utente guarda. */
const togliDalVuoto = () =>
  within(screen.getByRole("tabpanel")).getByRole("button", { name: /^rimuovi filtri$/i })

describe("la barra dell'Archivio", () => {
  it("cercare stringe l'elenco nel backend, non a schermo", async () => {
    // Cercare fra le cento righe gia' scaricate troverebbe solo quelle: a chi ha seicento oggetti
    // l'app direbbe "non trovato" mentendo. Quindi cio' che si scrive deve **arrivare alla rotta**.
    archivio([M31])
    await apriArchivio()

    fireEvent.change(await screen.findByLabelText(/cerca un oggetto/i), {
      target: { value: "m31" },
    })

    await waitFor(() => expect(window.location.search).toContain("q=m31"))
    await waitFor(() =>
      expect(chiamate().some((u) => u.includes("/archive") && u.includes("q=m31"))).toBe(true),
    )
  })

  it("le tendine offrono quello che hai, e quella vuota non compare", async () => {
    // Una tendina con la sola voce "tutti" e' un controllo che promette di fare qualcosa e non fa
    // niente: chi non ha ancora nessun filtro riconosciuto non deve vederla.
    archivio([M31], { choices: { ...SCELTE, catalogs: ["M"], constellations: [], filters: ["Lum"] } })
    await apriArchivio()

    expect(await screen.findByRole("button", { name: /catalogo/i })).toBeDefined()
    expect(screen.queryByRole("button", { name: /costellazione/i })).toBeNull()
  })

  it("la tendina delle costellazioni legge i nomi in ordine alfabetico, e sceglie la sigla", async () => {
    // Le sigle arrivano in ordine di sigla: "CVn" dopo "Cep" metterebbe Cepheus prima di Canes
    // Venatici. A schermo si leggono i nomi, e si cercano per nome.
    archivio([M31], { choices: { ...SCELTE, catalogs: ["M"], constellations: ["And", "Cep", "CVn", "Cyg"], filters: [] } })
    await apriArchivio()

    const nomi = ["Andromeda", "Canes Venatici", "Cepheus", "Cygnus"]
    expect((await vociDi(/costellazione/i)).slice(1)).toEqual(nomi)
    fireEvent.click(screen.getByRole("button", { name: /costellazione/i })) // la richiude

    // cio' che va nell'indirizzo e' la sigla, voce per voce
    const sigle = ["And", "CVn", "Cep", "Cyg"]
    for (const [i, nome] of nomi.entries()) {
      await scegli(/costellazione/i, nome)
      await waitFor(() => expect(window.location.search).toContain(`constellation=${sigle[i]}`))
    }
  })

  it("scegliere un catalogo lo scrive nell'indirizzo, senza toccare la vista", async () => {
    archivio([M31])
    await apriArchivio()
    await vaiAll(/elenco/i)

    await scegli(/catalogo/i, "NGC")

    await waitFor(() => expect(window.location.search).toContain("catalog=NGC"))
    expect(window.location.search).toContain("vista=elenco")
  })

  it("l'ordine lo sceglie l'utente e lo fa il backend", async () => {
    archivio([M31])
    await apriArchivio()

    // Gli ordini sono tre. Il tipo che viene dall'OpenAPI impedisce di **scriverne uno storto**,
    // non di **dimenticarne uno**: togliere una riga dall'elenco compila, e l'utente perde un
    // ordine senza che niente cada. Lato backend la coppia rotta-spina ce l'ha gia' un test suo.
    expect(await vociDi(/ordina/i)).toEqual(["Nome", "Ore", "Frame"])

    fireEvent.click(screen.getByRole("menuitemradio", { name: "Ore" }))

    await waitFor(() =>
      expect(chiamate().some((u) => u.includes("/archive") && u.includes("sort=hours"))).toBe(true),
    )
  })

  it("la barra resta a schermo mentre la ricerca arriva", async () => {
    // Con una chiave nuova la query riparte da zero: senza tenere le righe di prima, la barra si
    // smonta a **ogni** parola consegnata, e col campo se ne va il fuoco -- scrivi `m`, aspetti, e
    // `31` finisce da nessuna parte. E' il difetto piu' fastidioso che una barra possa avere.
    archivio([M31])
    await apriArchivio()
    const campo = await screen.findByLabelText(/cerca un oggetto/i)
    fireEvent.change(campo, { target: { value: "m31" } })

    await waitFor(() => expect(window.location.search).toContain("q=m31"))

    // lo stesso nodo di prima, non uno rimontato: se fosse stato smontato, il fuoco sarebbe perso
    expect(screen.getByLabelText(/cerca un oggetto/i)).toBe(campo)
    // e **le righe di prima sono ancora li'**: e' questo che tiene `keepPreviousData`, non la
    // barra -- quella la tengono le ultime scelte viste. Senza, per tutta l'attesa la pagina
    // sarebbe vuota sotto il campo.
    expect(screen.getAllByRole("article").length).toBeGreaterThan(0)
  })

  it("una tendina lascia la sua traccia, e il tasto indietro torna al filtro di prima", async () => {
    // Scrivere sostituisce -- una traccia per ogni tasto riempirebbe la cronologia di `m`, `m3`,
    // `m31` -- ma una scelta e' un gesto: senza la sua traccia, il tasto indietro non torna al
    // filtro di prima, esce dall'Archivio.
    archivio([M31])
    await apriArchivio()

    await scegli(/catalogo/i, "M")
    await waitFor(() => expect(window.location.search).toContain("catalog=M"))
    await scegli(/catalogo/i, "NGC")
    await waitFor(() => expect(window.location.search).toContain("catalog=NGC"))

    window.history.back()

    await waitFor(() => expect(window.location.search).toContain("catalog=M"))
  })

  it("e la vista lascia la sua traccia come gli altri controlli", async () => {
    // Prima di questa fetta l'interruttore sostituiva la tappa. Adesso segue la regola sola --
    // ogni scelta lascia la sua traccia, tranne lo scrivere -- e senza questa prova il ritorno
    // al comportamento di prima non farebbe rumore.
    archivio([M31])
    await apriArchivio()

    await vaiAll(/elenco/i)
    await waitFor(() => expect(window.location.search).toContain("vista=elenco"))
    window.history.back()

    // **e si resta nell'Archivio**: senza la traccia, il tasto indietro salta la vista e torna da
    // dove si era arrivati -- l'indirizzo non avrebbe piu' `vista=elenco` lo stesso, e senza
    // questa riga il sabotaggio passava
    await waitFor(() => expect(window.location.search).not.toContain("vista=elenco"))
    expect(window.location.pathname).toBe("/archivio")
  })

  it("scrivere non riempie la cronologia, e una parola sola e' una domanda sola", async () => {
    // Due regole che stavano scritte in intestazione e non le teneva niente. Una traccia per ogni
    // tasto renderebbe il tasto indietro inutile (tre pressioni per disfare `m31`), e tre domande
    // al backend per una parola sono due giri buttati.
    archivio([M31])
    await apriArchivio()
    const prima = window.history.length
    const campo = await screen.findByLabelText(/cerca un oggetto/i)

    fireEvent.change(campo, { target: { value: "m" } })
    fireEvent.change(campo, { target: { value: "m3" } })
    fireEvent.change(campo, { target: { value: "m31" } })

    await waitFor(() => expect(window.location.search).toContain("q=m31"))
    expect(window.history.length).toBe(prima)
    // la domanda parte un giro dopo l'indirizzo: si aspetta lei, non solo lui
    await waitFor(() =>
      expect(chiamate().filter((u) => u.includes("/archive") && u.includes("q="))).toHaveLength(1),
    )
  })

  it("un ordine che non esiste non rompe la pagina", async () => {
    // Un indirizzo scritto male non e' un errore da mostrare: se diventasse un 422, la pagina
    // resterebbe con un avviso e **senza barra**, cioe' senza il modo di uscirne.
    archivio([M31])
    const reso = await apriArchivioSu("/archivio?sort=pippo")

    expect(await screen.findByRole("article")).toBeDefined()
    // la tendina dice l'ordine con cui la pagina si e' aperta, e la sua voce e' quella accesa
    const ordina = await screen.findByRole("button", { name: /ordina/i })
    expect(ordina.querySelector("b")?.textContent).toBe("Nome")
    fireEvent.click(ordina)
    const accese = (await screen.findAllByRole("menuitemradio")).filter(
      (v) => v.getAttribute("aria-checked") === "true",
    )
    expect(accese.map((v) => v.textContent)).toEqual(["Nome"])
    reso.unmount()
  })

  it("mentre la risposta arriva, la barra dice che sta aspettando", async () => {
    // Tenere le righe di prima a schermo salva il fuoco, ma senza un segno l'utente vedrebbe cio'
    // che ha appena scritto accanto alla conta e alle righe di **prima**, e le prenderebbe per la
    // risposta. Lo si dichiara, non solo lo si dipinge: chi ascolta non vede il movimento.
    archivio([M31])
    await apriArchivio()
    const barra = await laBarra()
    expect(barra).toHaveProperty("ariaBusy", "false")

    let liberala = () => {}
    cambia(conArchivio({
        stato: 200,
        corpo: { items: [], total: 0, limit: 100, offset: 0, choices: SCELTE },
        attesa: new Promise<unknown>((r) => (liberala = () => r(null))),
      }))
    await scegli(/catalogo/i, "M")

    await waitFor(() => expect(barra).toHaveProperty("ariaBusy", "true"))
    // e il segno si **vede**, su chi ha chiesto e **solo** li': sta su un controllo della barra
    // perche' quello c'e' sempre -- anche quando le righe sono zero, che e' proprio il caso in cui
    // un segno sulle righe non esisterebbe. Uno solo, non "almeno uno": un segno su ogni tendina
    // non direbbe piu' quale scelta sta aspettando.
    const catalogo = await laTendina(/catalogo/i)
    expect(catalogo.querySelector(".as-attesa")).not.toBeNull()
    expect(barra?.querySelectorAll(".as-attesa")).toHaveLength(1)
    expect([...(barra?.querySelectorAll("[aria-busy='true']") ?? [])]).toEqual([catalogo])
    // le righe di prima restano
    expect(screen.getAllByRole("article").length).toBeGreaterThan(0)
    // e **niente si spegne**: cambiare idea a meta' attesa e' legittimo, e su rete lenta l'attesa
    // dura. Spegnere i controlli e' la scorciatoia che ogni barra prende: senza questa riga si
    // potevano aggiungere tre `disabled` e la suite restava verde.
    expect(barra?.querySelectorAll("[disabled], [aria-disabled='true']")).toHaveLength(0)

    liberala()
    await waitFor(() => expect(barra).toHaveProperty("ariaBusy", "false"))
    expect(barra?.querySelector(".as-attesa")).toBeNull()
    expect(barra?.querySelector("[aria-busy='true']")).toBeNull()
  })

  it("e lo dice anche quando le righe sono zero", async () => {
    // Il caso in cui un segno **sulle righe** non esisterebbe: un filtro che non trova niente, e
    // poi se ne cambia un altro. Per tutta l'attesa a schermo resta lo stato vuoto di **prima**,
    // che e' la risposta a una domanda vecchia, e senza segno lo si legge come la nuova.
    archivio([])
    const reso = await apriArchivioSu("/archivio?q=zzz")
    await screen.findByText(/^nessun risultato$/i)

    let liberala = () => {}
    cambia(conArchivio({
        stato: 200,
        corpo: { items: [], total: 0, limit: 100, offset: 0, choices: SCELTE },
        attesa: new Promise<unknown>((r) => (liberala = () => r(null))),
      }))
    await scegli(/catalogo/i, "M")

    const barra = await laBarra()
    await waitFor(() => expect(barra).toHaveProperty("ariaBusy", "true"))
    const catalogo = await laTendina(/catalogo/i)
    expect(catalogo.querySelector(".as-attesa")).not.toBeNull()
    expect(barra?.querySelectorAll(".as-attesa")).toHaveLength(1)
    expect([...(barra?.querySelectorAll("[aria-busy='true']") ?? [])]).toEqual([catalogo])

    liberala()
    reso.unmount()
  })

  it("l'interruttore di vista non si smonta quando l'ultima riga sparisce", async () => {
    // Niente si spegne durante l'attesa, quindi si puo' cambiare vista mentre una ricerca e' in
    // volo: se la risposta torna vuota e l'interruttore sparisse, il fuoco di chi ci stava sopra
    // finirebbe sul corpo della pagina. I due pannelli ci sono anche a elenco vuoto, col "non ho
    // trovato niente" dentro, e l'interruttore resta.
    archivio([M31])
    await apriArchivio()
    cambia(conArchivio(voceArchivio([])))

    await scegli(/catalogo/i, "M")

    expect(await screen.findByText(/^nessun risultato$/i)).toBeDefined()
    const schede = screen.getAllByRole("tab")
    expect(schede).toHaveLength(2)
    for (const scheda of schede) {
      const governa = scheda.getAttribute("aria-controls")
      expect(governa && document.getElementById(governa)).not.toBeNull()
    }
  })

  it("se la rete cade dopo un filtro, la barra resta e il filtro si puo' togliere", async () => {
    // E' il backend che si riavvia mentre stai filtrando, non un caso di scuola. Senza le ultime
    // scelte in mano la barra sparirebbe -- niente righe, niente `choices` -- e resterebbero un
    // avviso e un filtro acceso che non si puo' piu' togliere se non col tasto indietro.
    archivio([M31])
    await apriArchivio()
    cambia(conArchivio({ stato: 500, corpo: { detail: "boom" } }))

    await scegli(/catalogo/i, "M")

    expect(await screen.findByRole("alert")).toBeDefined()
    expect(await laTendina(/catalogo/i)).toBeDefined()
    // e il filtro si toglie da li': la x accanto alla tendina c'e'
    expect(screen.getByRole("button", { name: /rimuovi catalogo: M/i })).toBeDefined()
    expect(screen.getByLabelText(/cerca un oggetto/i)).toBeDefined()
    // e la conta **dice che non sa**, e nient'altro: zero sarebbe l'unica risposta che sappiamo
    // falsa, e toglierla farebbe saltare l'ordine sotto le dita
    expect(laConta()).toBe("Conteggio non disponibile")
    // e **non** dice "non ho trovato niente": non lo sappiamo, la richiesta e' fallita
    expect(screen.queryByText(/^nessun risultato$/i)).toBeNull()
  })

  it("e resta anche se a cadere e' un cambio d'ordine", async () => {
    // L'ordine non stringe l'elenco, ma chiede una pagina nuova come gli altri: la prima volta
    // che ho riparato questo difetto avevo coperto i quattro controlli che stringono e lasciato
    // fuori il quinto, e la barra spariva lo stesso -- senza nemmeno il modo di rimettere
    // l'ordine di prima.
    archivio([M31])
    await apriArchivio()
    cambia(conArchivio({ stato: 500, corpo: { detail: "boom" } }))

    await scegli(/ordina/i, "Ore")

    expect(await screen.findByRole("alert")).toBeDefined()
    expect(screen.getByRole("button", { name: /ordina/i })).toBeDefined()
  })

  it("quando un filtro non trova niente lo dice, e lascia il modo di toglierlo", async () => {
    // Togliere la barra qui lascerebbe senza il modo di togliere il filtro: bloccati su una
    // pagina vuota, con l'unica strada il tasto indietro. E non sono le parole di chi ha appena
    // installato l'app: li' l'archivio e' vuoto davvero.
    // **Due** criteri accesi, non uno: il bottone deve toglierli tutti, e con uno solo un bottone
    // che ne dimentica uno passerebbe. La vista invece resta dov'era -- toglie i filtri, non
    // rimette la pagina a nuovo.
    archivio([])
    const reso = await apriArchivioSu("/archivio?q=zzz&catalog=M&vista=elenco")

    expect(await screen.findByText(/^nessun risultato$/i)).toBeDefined()
    expect(screen.queryByText(/^archivio vuoto$/i)).toBeNull()
    expect(screen.getByLabelText(/cerca un oggetto/i)).toBeDefined()

    fireEvent.click(togliDalVuoto())

    await waitFor(() => expect(window.location.search).not.toContain("q="))
    expect(window.location.search).not.toContain("catalog=")
    expect(window.location.search).toContain("vista=elenco")
    reso.unmount()
  })

  it("un oggetto solo non prende il plurale", async () => {
    // Stringere un elenco finisce spesso su una riga sola: e' la prima cosa che si legge dopo
    // aver cercato, e leggerla sgrammaticata e' il difetto piu' visibile della barra.
    archivio([M31], { total: 1 })
    await apriArchivio()

    await waitFor(() => expect(laConta()).toBe("1 oggetto"))
  })

  it("togliere i filtri non fa dire all'app che l'archivio e' vuoto", async () => {
    // La strada: cerchi, non trovi niente, premi "Rimuovi filtri". La risposta senza criteri non
    // e' in cache, quindi per tutto il giro di rete restano a schermo **zero righe vecchie** e
    // nessun criterio -- che assomigliano a un primo avvio e non lo sono. Chi ha milleduecento
    // oggetti si vedrebbe dire di non averne nessuno, e perderebbe la barra col fuoco dentro.
    // Si **atterra** sulla pagina filtrata, non ci si passa: e' cio' che fa un collegamento che ti
    // sei mandato, o un ricarica. La differenza conta -- passandoci, l'elenco senza criteri
    // resterebbe in cache e tornerebbe subito, che e' il caso facile.
    archivio([])
    window.history.replaceState(null, "", "/archivio?q=zzz")
    const reso = await disegna()
    await screen.findByText(/^nessun risultato$/i)

    // e l'archivio, senza quel filtro, e' **pieno**
    let liberala = () => {}
    cambia(
      conArchivio({
        stato: 200,
        corpo: { items: [M31], total: 1, limit: 100, offset: 0, choices: SCELTE },
        attesa: new Promise<unknown>((r) => (liberala = () => r(null))),
      }),
    )
    fireEvent.click(togliDalVuoto())

    await waitFor(() => expect(window.location.search).not.toContain("q="))
    expect(screen.queryByText(/^archivio vuoto$/i)).toBeNull()
    expect(screen.getByLabelText(/cerca un oggetto/i)).toBeDefined()
    // E cosa si vede, non solo cosa non si vede: sotto la barra resta il vuoto -- le righe di
    // prima erano zero -- quindi il segno d'attesa sulla barra e' **l'unica** cosa che dice che
    // sta succedendo qualcosa. La guida lo racconta cosi'.
    const barra = await laBarra()
    expect(barra).toHaveProperty("ariaBusy", "true")
    // nessun controllo della barra ha chiesto: il segno **visibile** c'e' lo stesso
    await waitFor(() => expect(barra?.querySelector(".as-attesa")).not.toBeNull())
    expect(screen.queryByText(/^nessun risultato$/i)).toBeNull()

    liberala()
    reso.unmount()
  })

  it("ricliccare la scelta gia' accesa non lascia una tappa morta", async () => {
    // Tre clic sulla scheda che stai gia' guardando sarebbero tre tappe identiche, e tre pressioni
    // del tasto indietro che non fanno niente -- la promessa "il tasto indietro disfa l'ultima
    // scelta" rotta nel modo piu' banale. Vale per la vista e per l'ordine.
    archivio([M31])
    await apriArchivio()
    await screen.findByRole("button", { name: /catalogo/i })
    const prima = window.history.length

    fireEvent.click(screen.getByRole("tab", { name: /carte/i }))
    await scegli(/ordina/i, "Nome")

    expect(window.history.length).toBe(prima)
    // e quella **diversa** la tappa la lascia: la potatura non deve spegnere il gesto vero
    await vaiAll(/elenco/i)
    await waitFor(() => expect(window.history.length).toBe(prima + 1))
  })

  it("i controlli della barra sono mattoni, non classi scritte a mano", async () => {
    // La barra porta un campo, le tendine e l'ordine: e' la superficie piu' fitta di controlli
    // fuori dal primo avvio. Una classe del foglio appesa a un controllo scritto a mano si vede
    // identica e si comporta diversa il giorno che il foglio cambia.
    archivio([M31])
    await apriArchivio()
    await screen.findByRole("button", { name: /catalogo/i })

    expect(quantiControlli()).toBeGreaterThan(3)
    expect(fuoriDaiMattoni()).toEqual([])

    // e con una tendina scelta e il periodo a giorni: la x e le due date sono controlli in piu'
    const prima = quantiControlli()
    window.history.replaceState(null, "", "/archivio?catalog=M&period=date&since=2026-08-01")
    fireEvent.popState(window)
    await screen.findByRole("button", { name: /rimuovi catalogo: M/i })
    await screen.findByLabelText(/^dal$/i)

    expect(quantiControlli()).toBeGreaterThan(prima)
    expect(fuoriDaiMattoni()).toEqual([])
  })

  it("un tasto battuto mentre la consegna torna indietro non sparisce", async () => {
    // La consegna cambia l'indirizzo e l'indirizzo rientra nel campo: fra i due momenti ci sta un
    // tasto, e riallineare il campo a **ogni** giro lo cancellerebbe -- niente errore, niente
    // rosso, e chi scrive non capisce perche' manca una cifra. Qui la barra si guida da sola,
    // perche' e' l'unico modo di fermare il ritorno dell'indirizzo **dopo** il tasto e non prima.
    const criteri = {
      q: "",
      catalog: "",
      constellation: "",
      filter: "",
      mosaic: "",
      period: "",
      since: "",
      until: "",
      site: "",
      optics: "",
      camera: "",
      sort: "name" as const,
    }
    const consegne: string[] = []
    const barra = (q: string) => (
      <BarraDellArchivio
        criteri={{ ...criteri, q }}
        scelte={SCELTE}
        trovati={{ objects: 1, mosaics: 0 }}
        aspetta={false}
        onCriteri={(cambio) => consegne.push(cambio.q as string)}
        onTogli={() => {}}
      />
    )
    const { rerender } = render(barra(""))
    const campo = screen.getByLabelText(/cerca un oggetto/i) as HTMLInputElement
    fireEvent.change(campo, { target: { value: "m31" } })
    await waitFor(() => expect(consegne).toEqual(["m31"]))

    fireEvent.change(campo, { target: { value: "m314" } })
    rerender(barra("m31")) // l'indirizzo arriva **dopo** il tasto: e' la corsa vera

    expect(campo.value).toBe("m314")
    await waitFor(() => expect(consegne).toEqual(["m31", "m314"]))
  })

  it("Filtri apre e chiude le tendine, e dice quanti filtri sono scelti", async () => {
    // Sul telefono le tendine stanno dietro questo bottone: chi ascolta deve sentire se sono
    // aperte, e chi guarda deve sapere che un filtro stringe anche a tendine chiuse.
    archivio([M31])
    await apriArchivio()
    const barra = await laBarra()
    const filtri = screen.getByRole("button", { name: /^filtri/i })
    expect(filtri.getAttribute("aria-expanded")).toBe("false")
    expect(barra?.hasAttribute("data-aperta")).toBe(false)
    expect(filtri.querySelector("b")).toBeNull()

    fireEvent.click(filtri)
    expect(barra?.hasAttribute("data-aperta")).toBe(true)
    expect(filtri.getAttribute("aria-expanded")).toBe("true")

    fireEvent.click(filtri)
    expect(barra?.hasAttribute("data-aperta")).toBe(false)
    expect(filtri.getAttribute("aria-expanded")).toBe("false")

    window.history.replaceState(null, "", "/archivio?catalog=M&constellation=And")
    fireEvent.popState(window)
    await waitFor(() => expect(filtri.querySelector("b")?.textContent).toBe("2"))
  })

  it("una tendina che stringe lo mostra, e la prima voce la toglie", async () => {
    archivio([M31])
    await apriArchivio()

    await scegli(/catalogo/i, "M")
    // la pillola si ripesca a ogni sguardo: con la x accanto cambia posto nel documento, e un nodo
    // tenuto in mano da prima direbbe lo stato di allora
    await waitFor(async () =>
      expect((await laTendina(/catalogo/i)).classList.contains("as-tendina--scelta")).toBe(true),
    )
    expect((await laTendina(/catalogo/i)).querySelector("b")?.textContent).toBe("M")

    await scegli(/catalogo/i, /tutti i cataloghi/i)
    await waitFor(() => expect(window.location.search).not.toContain("catalog="))
    await waitFor(async () =>
      expect((await laTendina(/catalogo/i)).classList.contains("as-tendina--scelta")).toBe(false),
    )
  })

  it("la x accanto a una tendina scelta la toglie", async () => {
    // L'altra strada, senza aprire l'elenco: un bottone suo, col nome di cio' che toglie.
    archivio([M31])
    const reso = await apriArchivioSu("/archivio?catalog=M")

    fireEvent.click(await screen.findByRole("button", { name: /rimuovi catalogo: M/i }))

    await waitFor(() => expect(window.location.search).not.toContain("catalog="))
    await waitFor(() => expect(screen.queryByRole("button", { name: /rimuovi catalogo: M/i })).toBeNull())
    expect((await laTendina(/catalogo/i)).classList.contains("as-tendina--scelta")).toBe(false)
    reso.unmount()
  })

  it("Esc chiude la tendina aperta e riporta il fuoco al suo bottone", async () => {
    archivio([M31])
    await apriArchivio()
    const catalogo = await screen.findByRole("button", { name: /catalogo/i })

    fireEvent.click(catalogo)
    const voce = await screen.findByRole("menuitemradio", { name: /tutti i cataloghi/i })
    expect(document.activeElement).toBe(voce)
    fireEvent.keyDown(voce, { key: "Escape" })

    expect(screen.queryByRole("menu")).toBeNull()
    expect(document.activeElement).toBe(catalogo)
  })

  it("scelta una voce, il fuoco torna alla sua tendina, anche se ora ha la x accanto", async () => {
    // La pillola scelta cambia posto (entra nella coppia con la x): il fuoco deve ritrovarla, o chi
    // usa la tastiera ricomincia dall'inizio della pagina.
    archivio([M31])
    await apriArchivio()

    await scegli(/catalogo/i, "M")
    await waitFor(() => expect(window.location.search).toContain("catalog=M"))
    const scelta = await laTendina(/catalogo/i)
    expect(scelta.className).toContain("as-tendina--scelta")
    await waitFor(() => expect(document.activeElement).toBe(scelta))
  })

  it("Rimuovi filtri nella barra li toglie tutti", async () => {
    // Con le righe a schermo il vuoto non c'e': questo e' il bottone in fondo alle tendine.
    archivio([M31])
    const reso = await apriArchivioSu("/archivio?catalog=M&constellation=And")
    const barra = (await laBarra()) as HTMLElement

    fireEvent.click(await within(barra).findByRole("button", { name: /^rimuovi filtri$/i }))

    await waitFor(() => expect(window.location.search).not.toContain("catalog="))
    expect(window.location.search).not.toContain("constellation=")
    reso.unmount()
  })
})
