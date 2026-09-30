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
  vaiAll,
  voceArchivio,
} from "./archivio-banco"

afterEach(pulisci)

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
    archivio([M31], { choices: { catalogs: ["M"], constellations: [], filters: ["Lum"] } })
    await apriArchivio()

    expect(await screen.findByLabelText(/catalogo/i)).toBeDefined()
    expect(screen.queryByLabelText(/costellazione/i)).toBeNull()
  })

  it("la tendina delle costellazioni legge i nomi in ordine alfabetico, e sceglie la sigla", async () => {
    // Le sigle arrivano in ordine di sigla: "CVn" dopo "Cep" metterebbe Cepheus prima di Canes
    // Venatici. A schermo si leggono i nomi, e si cercano per nome.
    archivio([M31], { choices: { catalogs: ["M"], constellations: ["And", "Cep", "CVn", "Cyg"], filters: [] } })
    await apriArchivio()

    const tendina = (await screen.findByLabelText(/costellazione/i)) as HTMLSelectElement
    const voci = [...tendina.options].slice(1)
    expect(voci.map((o) => o.textContent)).toEqual(["Andromeda", "Canes Venatici", "Cepheus", "Cygnus"])
    expect(voci.map((o) => o.value)).toEqual(["And", "CVn", "Cep", "Cyg"])
  })

  it("scegliere un catalogo lo scrive nell'indirizzo, senza toccare la vista", async () => {
    archivio([M31])
    await apriArchivio()
    await vaiAll(/elenco/i)

    fireEvent.change(await screen.findByLabelText(/catalogo/i), { target: { value: "NGC" } })

    await waitFor(() => expect(window.location.search).toContain("catalog=NGC"))
    expect(window.location.search).toContain("vista=elenco")
  })

  it("l'ordine lo sceglie l'utente e lo fa il backend", async () => {
    archivio([M31])
    await apriArchivio()

    // Gli ordini sono tre. Il tipo che viene dall'OpenAPI impedisce di **scriverne uno storto**,
    // non di **dimenticarne uno**: togliere una riga dall'elenco compila, e l'utente perde un
    // ordine senza che niente cada. Lato backend la coppia rotta-spina ce l'ha gia' un test suo.
    const gruppo = await screen.findByRole("group", { name: /ordina/i })
    expect(within(gruppo).getAllByRole("button")).toHaveLength(3)

    fireEvent.click(await screen.findByRole("button", { name: /^ore$/i }))

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

    fireEvent.change(await screen.findByLabelText(/catalogo/i), { target: { value: "M" } })
    await waitFor(() => expect(window.location.search).toContain("catalog=M"))
    fireEvent.change(await screen.findByLabelText(/catalogo/i), { target: { value: "NGC" } })
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
    expect(await screen.findByRole("button", { name: /^nome$/i })).toHaveProperty(
      "ariaPressed",
      "true",
    )
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
    fireEvent.change(await screen.findByLabelText(/catalogo/i), { target: { value: "M" } })

    await waitFor(() => expect(barra).toHaveProperty("ariaBusy", "true"))
    // e il segno si **vede**: sono i due modificatori che nel foglio animano davvero, e stanno
    // sui controlli della barra perche' li' ci sono sempre -- anche quando le righe sono zero,
    // che e' proprio il caso in cui un segno sulle righe non esisterebbe
    // tutti e due, non "almeno uno": un `or` qui lascerebbe togliere il segno da meta' della
    // barra senza che niente cada -- provato, ed e' successo
    expect(barra?.querySelector(".as-campo--caricamento")).not.toBeNull()
    expect(barra?.querySelectorAll(".as-scelta--caricamento")).toHaveLength(3)
    // e **niente si spegne**: cambiare idea a meta' attesa e' legittimo, e su rete lenta l'attesa
    // dura. Spegnere i controlli e' la scorciatoia che ogni barra prende, ed e' anche la ragione
    // per cui `as-segmentato--caricamento` e' stato rifiutato: senza questa riga si potevano
    // aggiungere tre `disabled` e la suite restava verde.
    expect(barra?.querySelectorAll("[disabled], [aria-disabled='true']")).toHaveLength(0)

    liberala()
    await waitFor(() => expect(barra).toHaveProperty("ariaBusy", "false"))
    expect(barra?.querySelector(".as-campo--caricamento")).toBeNull()
    expect(barra?.querySelector(".as-scelta--caricamento")).toBeNull()
  })

  it("e lo dice anche quando le righe sono zero", async () => {
    // Il caso in cui un segno **sulle righe** non esisterebbe: un filtro che non trova niente, e
    // poi se ne cambia un altro. Per tutta l'attesa a schermo resta lo stato vuoto di **prima**,
    // che e' la risposta a una domanda vecchia, e senza segno lo si legge come la nuova.
    archivio([])
    const reso = await apriArchivioSu("/archivio?q=zzz")
    await screen.findByText(/nessun oggetto con questi filtri/i)

    let liberala = () => {}
    cambia(conArchivio({
        stato: 200,
        corpo: { items: [], total: 0, limit: 100, offset: 0, choices: SCELTE },
        attesa: new Promise<unknown>((r) => (liberala = () => r(null))),
      }))
    fireEvent.change(await screen.findByLabelText(/catalogo/i), { target: { value: "M" } })

    const barra = await laBarra()
    await waitFor(() =>
      expect(barra?.querySelector(".as-campo--caricamento")).not.toBeNull(),
    )
    expect(barra?.querySelectorAll(".as-scelta--caricamento")).toHaveLength(3)

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

    fireEvent.change(await screen.findByLabelText(/catalogo/i), { target: { value: "M" } })

    expect(await screen.findByText(/nessun oggetto con questi filtri/i)).toBeDefined()
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

    fireEvent.change(await screen.findByLabelText(/catalogo/i), { target: { value: "M" } })

    expect(await screen.findByRole("alert")).toBeDefined()
    expect(screen.getByLabelText(/catalogo/i)).toBeDefined()
    expect(screen.getByLabelText(/cerca un oggetto/i)).toBeDefined()
    // e la conta **dice che non sa**: zero sarebbe l'unica risposta che sappiamo falsa, e
    // toglierla farebbe saltare i bottoni dell'ordine sotto le dita
    expect(screen.getByText(/non so quanti/i)).toBeDefined()
    expect(screen.queryByText(/oggetti?$/i)).toBeNull()
    // e **non** dice "non ho trovato niente": non lo sappiamo, la richiesta e' fallita
    expect(screen.queryByText(/nessun oggetto con questi filtri/i)).toBeNull()
  })

  it("e resta anche se a cadere e' un cambio d'ordine", async () => {
    // L'ordine non stringe l'elenco, ma chiede una pagina nuova come gli altri: la prima volta
    // che ho riparato questo difetto avevo coperto i quattro controlli che stringono e lasciato
    // fuori il quinto, e la barra spariva lo stesso -- senza nemmeno il modo di rimettere
    // l'ordine di prima.
    archivio([M31])
    await apriArchivio()
    cambia(conArchivio({ stato: 500, corpo: { detail: "boom" } }))

    fireEvent.click(await screen.findByRole("button", { name: /^ore$/i }))

    expect(await screen.findByRole("alert")).toBeDefined()
    expect(screen.getByRole("button", { name: /^nome$/i })).toBeDefined()
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

    expect(await screen.findByText(/nessun oggetto con questi filtri/i)).toBeDefined()
    expect(screen.queryByText(/non c'e' ancora niente/i)).toBeNull()
    expect(screen.getByLabelText(/cerca un oggetto/i)).toBeDefined()

    fireEvent.click(screen.getByRole("button", { name: /togli i filtri/i }))

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

    expect(await screen.findByText(/^1 oggetto$/)).toBeDefined()
  })

  it("togliere i filtri non fa dire all'app che l'archivio e' vuoto", async () => {
    // La strada: cerchi, non trovi niente, premi "togli i filtri". La risposta senza criteri non
    // e' in cache, quindi per tutto il giro di rete restano a schermo **zero righe vecchie** e
    // nessun criterio -- che assomigliano a un primo avvio e non lo sono. Chi ha milleduecento
    // oggetti si vedrebbe dire di non averne nessuno, e perderebbe la barra col fuoco dentro.
    // Si **atterra** sulla pagina filtrata, non ci si passa: e' cio' che fa un collegamento che ti
    // sei mandato, o un ricarica. La differenza conta -- passandoci, l'elenco senza criteri
    // resterebbe in cache e tornerebbe subito, che e' il caso facile.
    archivio([])
    window.history.replaceState(null, "", "/archivio?q=zzz")
    const reso = await disegna()
    await screen.findByText(/nessun oggetto con questi filtri/i)

    // e l'archivio, senza quel filtro, e' **pieno**
    let liberala = () => {}
    cambia(
      conArchivio({
        stato: 200,
        corpo: { items: [M31], total: 1, limit: 100, offset: 0, choices: SCELTE },
        attesa: new Promise<unknown>((r) => (liberala = () => r(null))),
      }),
    )
    fireEvent.click(screen.getByRole("button", { name: /togli i filtri/i }))

    await waitFor(() => expect(window.location.search).not.toContain("q="))
    expect(screen.queryByText(/non c'e' ancora niente/i)).toBeNull()
    expect(screen.getByLabelText(/cerca un oggetto/i)).toBeDefined()
    // E cosa si vede, non solo cosa non si vede: sotto la barra resta il vuoto -- le righe di
    // prima erano zero -- quindi il segno d'attesa sulla barra e' **l'unica** cosa che dice che
    // sta succedendo qualcosa. La guida lo racconta cosi'.
    expect(await laBarra()).toHaveProperty("ariaBusy", "true")
    expect(screen.queryByText(/nessun oggetto con questi filtri/i)).toBeNull()

    liberala()
    reso.unmount()
  })

  it("ricliccare la scelta gia' accesa non lascia una tappa morta", async () => {
    // Tre clic sulla scheda che stai gia' guardando sarebbero tre tappe identiche, e tre pressioni
    // del tasto indietro che non fanno niente -- la promessa "il tasto indietro disfa l'ultima
    // scelta" rotta nel modo piu' banale. Vale per tutti e due i segmentati.
    archivio([M31])
    await apriArchivio()
    await screen.findByLabelText(/catalogo/i)
    const prima = window.history.length

    fireEvent.click(screen.getByRole("tab", { name: /carte/i }))
    fireEvent.click(screen.getByRole("button", { name: /^nome$/i }))

    expect(window.history.length).toBe(prima)
    // e quella **diversa** la tappa la lascia: la potatura non deve spegnere il gesto vero
    await vaiAll(/elenco/i)
    await waitFor(() => expect(window.history.length).toBe(prima + 1))
  })

  it("i controlli della barra sono mattoni, non classi scritte a mano", async () => {
    // La barra porta quattro controlli veri -- un campo, tre tendine -- piu' tre bottoni: e' la
    // superficie piu' fitta di controlli fuori dal primo avvio, e finora questa guardia
    // sull'Archivio non era mai girata. Un `as-campo__etichetta` appeso a un `<label>` scritto a
    // mano si vede identico e si comporta diverso il giorno che il foglio cambia.
    archivio([M31])
    await apriArchivio()
    await screen.findByLabelText(/catalogo/i)

    expect(quantiControlli()).toBeGreaterThan(3)
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
})
