// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Il sito*: l'elenco, la scheda che si compila, e il sito che non si
 * puo' togliere.
 *
 * Le regole provate qui sono quelle che una lettura del codice non prende: che il cielo mai
 * dichiarato **si legga** invece di sembrare uno zero, che correggere parta dai valori che il
 * sito ha davvero, che il primo sito nasca di casa e i successivi no, e che il rifiuto della
 * rotta si legga **dove si e' premuto**.
 *
 * Tre nascono da difetti veri, trovati da una revisione e da una misura, e sono quelle che si
 * romperebbero per prime: la **chiave** sulla scheda che si corregge (senza, i campi restano del
 * sito di prima e il salvataggio li scrive sull'altro); il **cielo mandato solo se scelto adesso**
 * (senza, correggere un nome ridichiara una classe derivata e cancella da dove veniva la misura);
 * e il **piede della barra riletto solo quando cambia il sito di casa**, che passa dalla rotta
 * piu' cara che l'app abbia.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SPINA,
  STANOTTE,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
} from "./banco"

afterEach(pulisci)

const CASA = {
  id: 1,
  name: "Cortina",
  latitude: 46.5405,
  longitude: 12.1357,
  bortle: 3,
  sky_sqm: 21.3,
  is_default: true,
}
const USCITA = {
  id: 2,
  name: "Passo Giau",
  latitude: 46.4843,
  longitude: 12.0533,
  bortle: null,
  sky_sqm: null,
  is_default: false,
}

function app(siti: unknown[] = [CASA, USCITA], piu: Record<string, unknown> = {}) {
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": {
      stato: 200,
      corpo: { to_confirm: 0 },
    },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...piu,
    "/api/v1/sites": { stato: 200, corpo: { items: siti, total: siti.length } },
    ...SPINA,
  })
  return disegna()
}

/** Apre la sezione come fa chi usa l'app: dalla barra, poi dall'elenco delle sezioni. */
async function vaiAlSito() {
  const barra = await screen.findByRole("navigation", { name: /pagine/i })
  fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
  // Nome esatto: col piede della barra senza sito, "Scegli il sito" porta allo stesso posto.
  fireEvent.click(await screen.findByRole("link", { name: /^il sito$/i }))
}

/** Riempie la scheda aperta. Sta qui perche' quattro prove fanno gli stessi tre gesti, e scritti
 *  quattro volte sarebbero quattro posti da correggere il giorno che nasce un campo. */
async function compila(nome: string, lat = "46,4843", lon = "12,0561") {
  fireEvent.change(await screen.findByLabelText(/nome del sito/i), { target: { value: nome } })
  fireEvent.change(screen.getByLabelText(/latitudine/i), { target: { value: lat } })
  fireEvent.change(screen.getByLabelText(/longitudine/i), { target: { value: lon } })
}

/** Quante volte il piede della barra ha riletto cio' che mostra. */
const letturaDelPiede = () => chiamate().filter((c) => c.includes("/tonight")).length

describe("Impostazioni / Il sito", () => {
  it("ogni sito dice dove sta e che cielo ha, e quello di casa si riconosce", async () => {
    await app()
    await vaiAlSito()

    const righe = await screen.findAllByRole("listitem")
    const cortina = righe.find((r) => r.textContent?.startsWith("Cortina"))!
    // Le coordinate ci sono, formattate: senza, due siti vicini sono due nomi e basta.
    expect(cortina.textContent).toMatch(/46,5405/)
    expect(cortina.textContent).toMatch(/12,1357/)
    // La classe **e la misura**: qui la misura e' la regola, il piede della barra e' l'eccezione.
    expect(cortina.textContent).toMatch(/3/)
    expect(cortina.textContent).toMatch(/21,3/)
    expect(within(cortina).getByText(/di casa/i)).toBeTruthy()
    // E solo uno lo e': "di casa" su due righe vorrebbe dire due fusi per la stessa notte.
    expect(screen.getAllByText(/^di casa$/i)).toHaveLength(1)
  })

  it("un cielo mai dichiarato lo dice, invece di passare per uno zero", async () => {
    await app()
    await vaiAlSito()

    const righe = await screen.findAllByRole("listitem")
    const giau = righe.find((r) => r.textContent?.startsWith("Passo Giau"))!
    expect(giau.textContent).toMatch(/non dichiarato/i)
    // E non porta un numero: `bortle: null` letto come cifra diventerebbe uno 0 fuori scala.
    expect(giau.querySelector(".as-bortle-letta__classe")).toBeNull()
  })

  it("correggere parte dai valori che il sito ha, non da campi vuoti", async () => {
    await app()
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /correggi Cortina/i }))

    const nome = (await screen.findByLabelText(/nome del sito/i)) as HTMLInputElement
    expect(nome.value).toBe("Cortina")
    expect((screen.getByLabelText(/latitudine/i) as HTMLInputElement).value).toBe("46.5405")
    // E la classe che ha e' gia' quella scelta: ripartire da nessuna la cancellerebbe salvando.
    expect(screen.getByRole("radio", { checked: true }).textContent).toMatch(/3/)
  })

  it("il cielo corretto arriva alla rotta, e col verbo che non crea un sito nuovo", async () => {
    await app([CASA, USCITA], {
      "PATCH /api/v1/sites": { stato: 200, corpo: { ...CASA, bortle: 5 } },
    })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /correggi Cortina/i }))
    fireEvent.click(await screen.findByRole("radio", { name: /5/ }))
    fireEvent.click(screen.getByRole("button", { name: /^salva$/i }))

    await waitFor(() => expect(scritture().length).toBeGreaterThan(0))
    const scritta = scritture()[0]!
    expect(scritta.metodo).toBe("PATCH")
    expect(scritta.url).toMatch(/\/api\/v1\/sites\/1$/)
    expect(scritta.corpo).toMatchObject({ name: "Cortina", bortle: 5 })
  })

  it("il primo sito nasce di casa, uno in piu' no", async () => {
    await app([], { "POST /api/v1/sites": { stato: 200, corpo: CASA } })
    await vaiAlSito()

    // Senza siti la sezione dice cosa manca, invece di un elenco vuoto.
    expect(await screen.findByText(/nessun sito/i)).toBeTruthy()
    fireEvent.click(screen.getByRole("button", { name: /aggiungi un sito/i }))

    await compila("Cortina", "46,5405", "12,1357")
    fireEvent.click(screen.getByRole("button", { name: /^salva$/i }))

    await waitFor(() => expect(scritture().length).toBeGreaterThan(0))
    // Di casa **per forza**: senza uno di casa le notti non nascono.
    expect(scritture()[0]!.corpo).toMatchObject({ name: "Cortina", is_default: true })
    // E la virgola e' passata per `coordinataDa`: `Number("46,5405")` sarebbe `NaN`.
    expect(scritture()[0]!.corpo).toMatchObject({ latitude: 46.5405 })
  })

  it("cambiando sito da correggere, la scheda si rifa' sul sito nuovo", async () => {
    // I campi nascono dal sito **una volta sola**. Senza una chiave, React tiene lo stesso
    // componente e a schermo restano i valori del primo: si salverebbe Cortina su Passo Giau.
    await app()
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /correggi Cortina/i }))
    expect((await screen.findByLabelText(/nome del sito/i) as HTMLInputElement).value).toBe(
      "Cortina",
    )
    fireEvent.click(screen.getByRole("button", { name: /correggi Passo Giau/i }))
    await waitFor(() =>
      expect((screen.getByLabelText(/nome del sito/i) as HTMLInputElement).value).toBe(
        "Passo Giau",
      ),
    )
  })

  it("correggere il nome non ridichiara il cielo che si stava solo guardando", async () => {
    // La classe a schermo e' **derivata** dalla luminosita' salvata. Rimandarla indietro la
    // farebbe registrare come una risposta, spostando la misura al centro della classe e
    // cancellando da dove veniva. Si manda solo cio' che l'utente ha toccato adesso.
    await app([CASA, USCITA], { "PATCH /api/v1/sites": { stato: 200, corpo: CASA } })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /correggi Cortina/i }))
    fireEvent.change(await screen.findByLabelText(/nome del sito/i), {
      target: { value: "Cortina d'Ampezzo" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^salva$/i }))

    await waitFor(() => expect(scritture().length).toBeGreaterThan(0))
    const corpo = scritture()[0]!.corpo as Record<string, unknown>
    expect(corpo["name"]).toBe("Cortina d'Ampezzo")
    expect("bortle" in corpo).toBe(false)
  })

  it("quando aggiungere fallisce, la scheda resta aperta e lo dice", async () => {
    await app([CASA], { "POST /api/v1/sites": { stato: 500, corpo: { detail: "boom" } } })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un sito/i }))
    await compila("Giau")
    fireEvent.click(screen.getByRole("button", { name: /^salva$/i }))

    expect(await screen.findByText(/non sono riuscito a salvare il sito/i)).toBeTruthy()
    // E cio' che si era scritto e' ancora li': ricominciare da capo dopo un guasto e' la punizione
    // sbagliata per chi non ha fatto niente.
    expect((screen.getByLabelText(/nome del sito/i) as HTMLInputElement).value).toBe("Giau")
  })

  it("un sito in piu' non si prende il posto di casa", async () => {
    // L'altra meta' della regola: il **primo** nasce di casa perche' senza uno le notti non
    // nascono, ma aggiungerne un altro non deve spostare il fuso di tutte le notti gia' fatte.
    await app([CASA], { "POST /api/v1/sites": { stato: 200, corpo: USCITA } })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un sito/i }))
    await compila("Giau")
    fireEvent.click(screen.getByRole("button", { name: /^salva$/i }))

    await waitFor(() => expect(scritture().length).toBeGreaterThan(0))
    expect(scritture()[0]!.corpo).toMatchObject({ is_default: false })
  })

  it("rendere di casa scrive davvero, e se non riesce lo dice", async () => {
    // E' il gesto che decide il fuso di **tutte** le notti: ricaricare l'elenco e basta lo
    // mostrerebbe identico, e chi ha premuto crederebbe di aver cambiato posto.
    await app([CASA, USCITA], {
      "POST /api/v1/sites": { stato: 500, corpo: { detail: "boom" } },
    })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /rendi di casa Passo Giau/i }))
    await waitFor(() => expect(scritture().length).toBeGreaterThan(0))
    expect(scritture()[0]!.url).toMatch(/\/api\/v1\/sites\/2\/default$/)
    expect(await screen.findByText(/non sono riuscito a cambiare il sito di casa/i)).toBeTruthy()
  })

  it("rendere di casa riesce, e il piede della barra lo rilegge", async () => {
    // Il gemello della prova sopra: quando **riesce**, il piede deve saperlo -- e' proprio il
    // caso in cui cio' che mostra cambia, perche' mostra il sito di casa.
    await app([CASA, USCITA], { "POST /api/v1/sites": { stato: 200, corpo: USCITA } })
    await vaiAlSito()

    const prima = letturaDelPiede()
    fireEvent.click(await screen.findByRole("button", { name: /rendi di casa Passo Giau/i }))

    await waitFor(() => expect(letturaDelPiede()).toBeGreaterThan(prima))
    expect(screen.queryByText(/non sono riuscito a cambiare il sito di casa/i)).toBeNull()
  })

  it("rendere di casa non spazza via la scheda che si stava compilando", async () => {
    // I tasti dell'elenco restano premibili con una scheda aperta: chiudere cio' che qualcuno
    // stava scrivendo e' la punizione sbagliata per un gesto che con quella scheda non c'entra.
    await app([CASA, USCITA], { "POST /api/v1/sites": { stato: 200, corpo: USCITA } })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un sito/i }))
    await compila("Malga")
    fireEvent.click(screen.getByRole("button", { name: /rendi di casa Passo Giau/i }))

    await waitFor(() => expect(scritture().length).toBeGreaterThan(0))
    expect((screen.getByLabelText(/nome del sito/i) as HTMLInputElement).value).toBe("Malga")
  })

  it("togliere un sito non spazza via la scheda che si stava compilando", async () => {
    // Il gemello della prova sopra, per l'altra porta: anche *Togli* si preme dall'elenco.
    await app([CASA, USCITA], {
      "DELETE /api/v1/sites": { stato: 200, corpo: { site_id: 2, deleted: true } },
    })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un sito/i }))
    await compila("Malga")
    fireEvent.click(screen.getByRole("button", { name: /togli Passo Giau/i }))
    const dialogo = await screen.findByRole("dialog")
    fireEvent.click(within(dialogo).getByRole("button", { name: /togli il sito/i }))

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull())
    expect((screen.getByLabelText(/nome del sito/i) as HTMLInputElement).value).toBe("Malga")
  })

  it("la scheda che correggeva il sito tolto se ne va con lui", async () => {
    // L'eccezione della regola sopra: quella scheda non ha piu' un sito da correggere, e lasciarla
    // aperta vorrebbe dire un modulo che salva su qualcosa che non c'e'.
    await app([CASA, USCITA], {
      "DELETE /api/v1/sites": { stato: 200, corpo: { site_id: 2, deleted: true } },
    })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /correggi Passo Giau/i }))
    await screen.findByLabelText(/nome del sito/i)
    fireEvent.click(screen.getByRole("button", { name: /togli Passo Giau/i }))
    const dialogo = await screen.findByRole("dialog")
    fireEvent.click(within(dialogo).getByRole("button", { name: /togli il sito/i }))

    await waitFor(() => expect(screen.queryByLabelText(/nome del sito/i)).toBeNull())
  })

  it("aprendo la scheda il fuoco ci entra, e dice quale scheda e'", async () => {
    // La scheda nasce in fondo alla sezione, fuori dalla vista: senza spostare il fuoco, chi
    // naviga col tabulatore o ascolta continua a scorrere l'elenco senza sapere che e' comparsa.
    await app()
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /correggi Cortina/i }))
    await waitFor(() => {
      const dove = document.activeElement
      // Il titolo della scheda, non il corpo: `body.textContent` contiene tutta la pagina e
      // farebbe passare questa prova anche col fuoco rimasto dov'era.
      expect(dove?.tagName).toBe("H2")
      expect(dove?.className).toContain("as-carta__titolo")
      expect(dove?.textContent).toMatch(/correggi il sito/i)
    })
  })

  it("due schede aperte insieme non si rubano i campi", async () => {
    // Dall'elenco si puo' premere *Correggi* mentre *Aggiungi* e' gia' aperta: due campi con lo
    // stesso `id` darebbero il fuoco dell'etichetta a quello sbagliato, e uno dei due resterebbe
    // scollegato dal suo nome per chi ascolta.
    await app()
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un sito/i }))
    fireEvent.click(await screen.findByRole("button", { name: /correggi Cortina/i }))

    const nomi = await screen.findAllByLabelText(/nome del sito/i)
    expect(nomi).toHaveLength(2)
    expect(new Set(nomi.map((n) => n.id)).size).toBe(2)
    // E ognuna resta col suo: la scheda che corregge porta il sito, quella che aggiunge e' vuota.
    expect(nomi.map((n) => (n as HTMLInputElement).value).sort()).toEqual(["", "Cortina"])
  })

  it("senza un sito di casa la sezione lo dice, invece di lasciare l app muta", async () => {
    // La rotta che toglie **non elegge** un altro sito di casa, di proposito: e senza quello
    // `GET /tonight` non ha niente da dire, cosi' la barra torna a "non so da dove osservi"
    // mentre l'elenco qui e' pieno. E' lo stato in cui si finisce togliendo il sito di casa.
    await app([{ ...USCITA, is_default: false }])
    await vaiAlSito()

    expect(await screen.findByText(/nessun sito e' quello di casa/i)).toBeTruthy()
    // E la strada per uscirne sta li': il tasto che elegge quello giusto.
    expect(screen.getByRole("button", { name: /rendi di casa Passo Giau/i })).toBeTruthy()
  })

  it("con un sito di casa l avviso non c e", async () => {
    await app()
    await vaiAlSito()

    await screen.findAllByRole("listitem")
    expect(screen.queryByText(/nessun sito e' quello di casa/i)).toBeNull()
  })

  it("dichiarato il sito, il piede della barra lo sa senza ricaricare la pagina", async () => {
    await app([], { "POST /api/v1/sites": { stato: 200, corpo: CASA } })
    await vaiAlSito()
    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un sito/i }))
    await compila("Cortina", "46,5405", "12,1357")

    const prima = letturaDelPiede()
    fireEvent.click(screen.getByRole("button", { name: /^salva$/i }))

    // Il piede sta **fuori** da questa pagina e tiene la sua risposta per un'ora: senza buttarla
    // via, chi dichiara il sito qui continua a leggere "non so da dove osservi". Visto dal vivo.
    await waitFor(() =>
      expect(letturaDelPiede()).toBeGreaterThan(prima),
    )
  })

  it("correggere un sito d uscita non fa rileggere il piede della barra", async () => {
    // L'altra meta' della regola sopra, e **la piu' cara**: il piede mostra il sito di casa, e
    // rileggerlo rifa' le effemeridi. Correggere un sito che serve alle uscite non sposta una
    // virgola di cio' che il piede mostra.
    await app([CASA, USCITA], { "PATCH /api/v1/sites": { stato: 200, corpo: USCITA } })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /correggi Passo Giau/i }))
    await compila("Passo Giau 2")
    const prima = letturaDelPiede()
    fireEvent.click(screen.getByRole("button", { name: /^salva$/i }))

    await waitFor(() => expect(scritture().length).toBeGreaterThan(0))
    // Si aspetta che l'elenco sia stato riletto: cosi' il confronto non e' fatto troppo presto.
    await waitFor(() => expect(screen.queryByLabelText(/nome del sito/i)).toBeNull())
    expect(letturaDelPiede()).toBe(prima)
  })

  it("un sito senza notti si toglie davvero, e il dialogo si chiude", async () => {
    await app([CASA, USCITA], {
      "DELETE /api/v1/sites": { stato: 200, corpo: { site_id: 2, deleted: true } },
    })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /togli Passo Giau/i }))
    const dialogo = await screen.findByRole("dialog")
    fireEvent.click(within(dialogo).getByRole("button", { name: /togli il sito/i }))

    await waitFor(() => expect(scritture().length).toBeGreaterThan(0))
    expect(scritture()[0]!.metodo).toBe("DELETE")
    expect(scritture()[0]!.url).toMatch(/\/api\/v1\/sites\/2$/)
    // Il dialogo se ne va: restare aperto su un gesto riuscito e' chiedere due volte.
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull())
  })

  it("un sito che tiene delle notti non si toglie, e il rifiuto si legge nel dialogo", async () => {
    await app([CASA, USCITA], {
      "DELETE /api/v1/sites": {
        stato: 409,
        corpo: { detail: { code: "site_has_nights", nights: 41 } },
      },
    })
    await vaiAlSito()

    fireEvent.click(await screen.findByRole("button", { name: /togli Cortina/i }))
    const dialogo = await screen.findByRole("dialog")
    fireEvent.click(within(dialogo).getByRole("button", { name: /togli/i }))

    // Quante notte lo tengono si legge **dentro il dialogo**, dove si e' premuto: fuori sarebbe
    // una frase da cercare mentre si guarda ancora la domanda.
    await waitFor(() => expect(within(dialogo).getByText(/41/)).toBeTruthy())
    // E il sito e' ancora li': il dialogo non si chiude su un rifiuto.
    expect(screen.getByRole("dialog")).toBeTruthy()
    expect(screen.getAllByRole("listitem").some((r) => r.textContent?.startsWith("Cortina"))).toBe(
      true,
    )
  })
})

describe("Impostazioni / Il sito, dall'indirizzo", () => {
  it("con ?sito= la riga di quel sito e' segnata, e la scheda di correzione resta chiusa", async () => {
    window.history.pushState({}, "", `/impostazioni/sito?sito=${USCITA.id}`)
    await app()

    // il nome sta anche nel pannello di Stanotte: la riga e' quella della sezione
    await screen.findAllByText("Passo Giau")
    const riga = document.getElementById(`sito-${USCITA.id}`) as HTMLElement
    expect(riga.textContent).toContain("Passo Giau")
    expect(riga.getAttribute("aria-current")).toBe("true")
    expect(document.querySelectorAll('li[aria-current="true"]')).toHaveLength(1)
    expect(screen.queryByLabelText(/nome del sito/i)).toBeNull()
  })
})
