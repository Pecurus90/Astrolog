// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Il riconoscitore*: dove l'app prende ASTAP, e da cosa l'ha dedotto.
 *
 * Le regole provate qui sono quelle che una lettura del codice non prende: che il **canale** si
 * legga accanto al percorso -- "trovato" da solo non si puo' smentire -- che un percorso scritto
 * e sbagliato **resti a schermo** invece di sparire, e che la ricerca automatica **proponga senza
 * scrivere**, perche' sovrascrivere di nascosto toglierebbe l'unica via d'uscita a chi quella
 * ricerca l'ha vista sbagliare.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SPINA,
  STANOTTE,
  cambia,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
} from "./banco"

afterEach(pulisci)

const TROVATO = {
  path: "C:\\Program Files\\astap\\astap_cli.exe",
  source: "declared",
  declared: "C:\\Program Files\\astap\\astap_cli.exe",
  databases: ["d80"],
}

function app(solver: unknown = TROVATO, piu: Record<string, unknown> = {}) {
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": {
      stato: 200,
      corpo: { to_confirm: 0 },
    },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...piu,
    "/api/v1/solver": { stato: 200, corpo: solver },
    ...SPINA,
  })
  return disegna()
}

/** Apre la sezione come fa chi usa l'app: dalla barra, poi dall'elenco delle sezioni. */
async function vaiAlRiconoscitore() {
  const barra = await screen.findByRole("navigation", { name: /pagine/i })
  fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
  fireEvent.click(await screen.findByRole("link", { name: /riconoscitore/i }))
}

describe("Impostazioni / Il riconoscitore", () => {
  it("dice dove sta, e da cosa l app l ha dedotto", async () => {
    await app()
    await vaiAlRiconoscitore()

    expect(await screen.findByText(/astap_cli\.exe/)).toBeTruthy()
    // Il canale accanto al percorso: senza, "trovato" non si puo' smentire.
    expect(screen.getByText(/gliel'hai detto tu/i)).toBeTruthy()
  })

  it("ogni canale ha la sua frase, e nessuno resta un codice a schermo", async () => {
    // Quattro rami, e il codice del backend non deve arrivare a schermo in nessuno.
    for (const [source, frase] of [
      ["env", /chi ha avviato l'app/i],
      ["path", /programmi di sistema/i],
      ["known_place", /dove si installa di solito/i],
    ] as const) {
      pulisci()
      await app({ ...TROVATO, source })
      await vaiAlRiconoscitore()
      expect(await screen.findByText(frase), source).toBeTruthy()
      expect(screen.queryByText(source)).toBeNull()
    }
  })

  it("non trovandolo dice cosa si perde, senza chiamarlo guasto", async () => {
    await app({ path: null, source: null, declared: null, databases: [] })
    await vaiAlRiconoscitore()

    expect(await screen.findByText(/non trovo astap/i)).toBeTruthy()
    // Non e' un allarme: manca un programma, non si e' rotto niente.
    expect(screen.getByText(/cosa cambia senza/i)).toBeTruthy()
    expect(screen.getByText(/non sapra' dirti cosa hai ripreso/i)).toBeTruthy()
  })

  it("dice quale catalogo stellare c e", async () => {
    await app()
    await vaiAlRiconoscitore()

    expect(await screen.findByText(/catalogo stellare: d80/i)).toBeTruthy()
    expect(screen.queryByText(/manca il catalogo stellare/i)).toBeNull()
  })

  it("ASTAP senza catalogo lo dice, e porta dove si prende", async () => {
    // E' l'errore di installazione piu' comune: il programma c'e' e non riconosce niente, e
    // finora si scopriva da una scansione tornata a mani vuote.
    await app({ ...TROVATO, databases: [] })
    await vaiAlRiconoscitore()

    expect(await screen.findByText(/manca il catalogo stellare/i)).toBeTruthy()
    expect(screen.getByText(/si ferma alla prima posa/i)).toBeTruthy()
    const dove = screen.getByRole("link", { name: /scarica il catalogo/i })
    expect(dove.getAttribute("href")).toContain("star_databases")
    expect(dove.getAttribute("rel")).toContain("noopener")
    // Non e' un allarme: manca un download, non si e' rotto niente.
    expect(screen.queryByRole("alert")).toBeNull()
  })

  it("chi non ha ASTAP non si sente dire anche che gli manca il catalogo", async () => {
    // Due allarmi per un problema solo mandano a cercare due cose: il catalogo e' di ASTAP, e
    // chi non ha il programma ha una cosa sola da fare.
    await app({ path: null, source: null, declared: null, databases: [] })
    await vaiAlRiconoscitore()

    expect(await screen.findByText(/non trovo astap/i)).toBeTruthy()
    expect(screen.queryByText(/catalogo stellare/i)).toBeNull()
  })

  it("un percorso scritto e sbagliato resta a schermo", async () => {
    // E' l'unica cosa che si puo' correggere: nasconderlo lascerebbe "non trovato" senza perche'.
    await app({ path: null, source: null, declared: "D:\\sbagliato\\astap.exe" })
    await vaiAlRiconoscitore()

    expect(await screen.findByText(/non porta a nessun programma/i)).toBeTruthy()
    expect(screen.getByText("D:\\sbagliato\\astap.exe")).toBeTruthy()
    // e il campo parte da li', cosi' si corregge invece di riscriverlo da capo
    expect((screen.getByLabelText(/dove sta/i) as HTMLInputElement).value).toBe(
      "D:\\sbagliato\\astap.exe",
    )
  })

  it("cercalo tu propone, e non scrive niente finche' non si adotta", async () => {
    await app(
      { path: null, source: null, declared: "D:\\sbagliato\\astap.exe" },
      { "POST /api/v1/solver": { stato: 200, corpo: { ...TROVATO, source: "path" } } },
    )
    await vaiAlRiconoscitore()

    fireEvent.click(await screen.findByRole("button", { name: /cercalo tu/i }))
    expect(await screen.findByText(/ne ho trovato uno/i)).toBeTruthy()
    // La ricerca ha guardato, e **non ha scritto**: nessuna PATCH sulle impostazioni.
    expect(scritture().some((s) => s.url.includes("/settings"))).toBe(false)
  })

  it("adottando la proposta, quella diventa la preferenza", async () => {
    await app(
      { path: null, source: null, declared: null, databases: [] },
      {
        "POST /api/v1/solver": { stato: 200, corpo: { ...TROVATO, source: "path" } },
        "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      },
    )
    await vaiAlRiconoscitore()

    fireEvent.click(await screen.findByRole("button", { name: /cercalo tu/i }))
    fireEvent.click(await screen.findByRole("button", { name: /usa quello che hai trovato/i }))

    await waitFor(() => expect(scritture().some((s) => s.metodo === "PATCH")).toBe(true))
    const scritta = scritture().find((s) => s.metodo === "PATCH")!
    expect(scritta.corpo).toMatchObject({ values: { astap_path: TROVATO.path } })
    // E la proposta se ne va: adottata, non e' piu' una proposta -- restando, lo stesso percorso
    // sarebbe a schermo due volte, una delle quali come domanda.
    await waitFor(() => expect(screen.queryByText(/ne ho trovato uno/i)).toBeNull())
    expect((screen.getByLabelText(/dove sta/i) as HTMLInputElement).value).toBe(TROVATO.path)
  })

  it("scritto il percorso, la riga di stato lo sa senza ricaricare", async () => {
    // La risposta della scrittura non porta il canale, quindi dove sta il solver si **richiede**.
    // Senza, dopo aver adottato la proposta la riga continua a dire "Non trovo ASTAP" mentre il
    // campo sotto mostra il percorso giusto: due verita' sulla stessa cosa, a due centimetri.
    await app(
      { path: null, source: null, declared: null, databases: [] },
      {
        "POST /api/v1/solver": { stato: 200, corpo: { ...TROVATO, source: "path" } },
        "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      },
    )
    await vaiAlRiconoscitore()
    expect(await screen.findByText(/non trovo astap/i)).toBeTruthy()

    // dopo la scrittura il backend dice un'altra cosa, e la sezione deve andare a risentirlo
    cambia({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "POST /api/v1/solver": { stato: 200, corpo: { ...TROVATO, source: "path" } },
      "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/solver": { stato: 200, corpo: TROVATO },
      ...SPINA,
    })
    fireEvent.click(screen.getByRole("button", { name: /cercalo tu/i }))
    fireEvent.click(await screen.findByRole("button", { name: /usa quello che hai trovato/i }))

    expect(await screen.findByText(/gliel'hai detto tu/i)).toBeTruthy()
    expect(screen.queryByText(/non trovo astap/i)).toBeNull()
  })

  it("lo stesso percorso si scrive una volta sola, da qualunque parte arrivi", async () => {
    // Premere il tasto **toglie il fuoco dal campo**: senza memoria di cosa si e' gia' mandato,
    // l'uscita dal campo e il clic mandano la stessa preferenza due volte. Non e' un doppione
    // innocuo -- sono due scritture sul database per un gesto solo.
    await app(
      { path: null, source: null, declared: null, databases: [] },
      { "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) } },
    )
    await vaiAlRiconoscitore()

    const campo = await screen.findByLabelText(/dove sta/i)
    fireEvent.change(campo, { target: { value: "D:/astap/astap_cli.exe" } })
    fireEvent.blur(campo)
    fireEvent.click(screen.getByRole("button", { name: /^usa questo$/i }))

    await waitFor(() => expect(scritture().some((s) => s.metodo === "PATCH")).toBe(true))
    expect(scritture().filter((s) => s.metodo === "PATCH")).toHaveLength(1)
  })

  it("cambiando il percorso, l esito di quello di prima se ne va", async () => {
    // Un "non c'e'" attaccato a un percorso che nel frattempo e' cambiato accusa la cosa
    // sbagliata: chi sta correggendo legge un errore su cio' che ha appena riscritto.
    await app(
      { path: null, source: null, declared: null, databases: [] },
      { "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true, ["no_solver"]) } },
    )
    await vaiAlRiconoscitore()

    const campo = await screen.findByLabelText(/dove sta/i)
    fireEvent.change(campo, { target: { value: "D:/sbagliato" } })
    fireEvent.click(screen.getByRole("button", { name: /^usa questo$/i }))
    expect(await screen.findByText(/li' non c'e' astap/i)).toBeTruthy()

    fireEvent.change(campo, { target: { value: "D:/un-altro" } })
    expect(screen.queryByText(/li' non c'e' astap/i)).toBeNull()
  })

  it("una ricerca a vuoto lo dice, invece di non rispondere", async () => {
    await app(
      { path: null, source: null, declared: null, databases: [] },
      { "POST /api/v1/solver": { stato: 200, corpo: { path: null, source: null, declared: null, databases: [] } } },
    )
    await vaiAlRiconoscitore()

    fireEvent.click(await screen.findByRole("button", { name: /cercalo tu/i }))
    expect(await screen.findByText(/non c'e'/i)).toBeTruthy()
  })

  it("l app non scarica niente da sola, e lo dice", async () => {
    // L'unica riga di questa schermata che non si negozia.
    await app()
    await vaiAlRiconoscitore()

    const dove = await screen.findByRole("link", { name: /scarica astap/i })
    expect(dove.getAttribute("href")).toContain("hnsky.org")
    // e un collegamento che porta fuori si apre altrove, senza dare a quella pagina la nostra
    expect(dove.getAttribute("rel")).toContain("noopener")
    expect(screen.getByText(/non scarica e non installa niente/i)).toBeTruthy()
  })
})
