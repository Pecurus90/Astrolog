// @vitest-environment jsdom
/**
 * Il terzo passo del primo avvio: **dove stanno i file**, e cosa succede quando finisci.
 *
 * Il resto del primo avvio (le altre domande, il timbro, il salta) sta in `wizard.test.tsx`. Qui
 * c'e' quello che riguarda le cartelle: che se ne possano indicare **piu' d'una**, che dove l'app
 * ha una radice dei dati si **scelgano da un elenco** invece di scriverle, e che alla fine la
 * lettura **parta da sola** -- senza che chi ha appena installato sappia che esiste un pulsante.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, cambia, chiamate, disegna, fuoriDaiMattoni, impostazioni, pulisci, quantiControlli, rispondi, scritture } from "./banco"

afterEach(pulisci)

/** Where the NAS list says you are (tavola v82 `N.dir`, the path written whole). */
function dove() {
  return document.querySelector(".al-avvio__colonna-18 .al-avvio__testo-18")?.textContent ?? ""
}

const SONDA = {
  reachable: true,
  fits_count: 12,
  complete: true,
  root_path: "D:/Astro",
  moved_from: null,
  moved_check: "none",
}

/** Le cartelle come le manda `GET /folders`. La stessa risposta serve anche al POST -- il banco
 *  sceglie per indirizzo, non per metodo -- e chi registra guarda solo se c'e' stato un errore. */
function elenco(percorsi: string[]) {
  return {
    items: percorsi.map((root_path, i) => ({
      id: i + 1,
      root_path,
      name: null,
      frames: 0,
      reachable: true,
      created_at: "2026-09-16T00:00:00Z",
      retired_at: null,
    })),
    total: percorsi.length,
  }
}

/** L'app al primo avvio, col terzo passo pronto a rispondere. `registrate` sono le cartelle che
 *  l'API dira' di avere: e' cio' che l'elenco a schermo deve mostrare. */
function primoAvvio(
  // `attesa` trattiene una risposta: serve a guardare cosa mostra l'app **mentre** aspetta
  extra: Record<string, { stato: number; corpo: unknown; attesa?: Promise<unknown> }> = {},
  registrate: string[] = ["D:/Astro/2024"],
) {
  // `extra` davanti a tutto: il banco sceglie la **prima rotta che l'indirizzo contiene**, quindi
  // `/api/v1/folders` ingoierebbe `/api/v1/folders/browse` se venisse prima.
  rispondi({
    ...STANOTTE,
    ...extra,
    "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
    "/api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "/api/v1/folders/probe": { stato: 200, corpo: SONDA },
    "/api/v1/folders": { stato: 200, corpo: elenco(registrate) },
    "/api/v1/scan": { stato: 202, corpo: { started: [], skipped: [] } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    ...SPINA,
  })
}

async function alTerzoPasso() {
  await disegna()
  await screen.findByRole("button", { name: /salta/i })
  // nome, sito, tema: le cartelle sono il quarto passo (tavola v82)
  for (let i = 0; i < 3; i++) fireEvent.click(screen.getByRole("button", { name: /avanti/i }))
}

async function indica(percorso: string) {
  fireEvent.change(screen.getByLabelText(/percorso della cartella/i), {
    target: { value: percorso },
  })
  fireEvent.click(screen.getByRole("button", { name: /^verifica$/i }))
  fireEvent.click(await screen.findByRole("button", { name: /aggiungi/i }))
  // Si aspetta che la registrazione sia **partita**: il clic la mette in volo, e chi legge le
  // scritture subito dopo ne conta una in meno -- un rosso che sembra del codice ed e' del test.
  await waitFor(() =>
    expect(
      scritture().some(
        (s) => s.url.endsWith("/api/v1/folders") && (s.corpo as { root_path: string }).root_path === percorso,
      ),
    ).toBe(true),
  )
}

describe("le cartelle del primo avvio", () => {
  it("ne posso indicare piu' di una, e restano tutte", async () => {
    // Prima ne accettava **una**: aggiungerla timbrava, e il primo avvio si chiudeva in faccia.
    // Chi tiene le foto in due dischi -- il caso di chiunque abbia un NAS e un portatile --
    // doveva ricordarsi di aggiungere la seconda da un posto che non esiste ancora.
    primoAvvio()
    await alTerzoPasso()

    await indica("D:/Astro/2024")
    await indica("E:/Vecchie")

    const aggiunte = scritture().filter((s) => s.url.endsWith("/api/v1/folders"))
    // il messaggio porta con se' TUTTE le scritture: se ne manca una, la causa arriva col rosso
    expect(aggiunte.map((s) => (s.corpo as { root_path: string }).root_path)).toEqual([
      "D:/Astro/2024",
      "E:/Vecchie",
    ])
    // e il primo avvio e' ancora li': non si e' chiuso alla prima
    expect(screen.getByRole("button", { name: /avanti/i })).toBeDefined()
  })

  it("cio' che la verifica trova sta in un esito, col comando che aggiunge dentro", async () => {
    // Il comando pieno del passo e' quello che registra: sta nell'esito che lo motiva, e Avanti
    // gli cede il posto, cosi' il pieno resta uno solo.
    primoAvvio({}, [])
    await alTerzoPasso()
    const campo = screen.getByLabelText(/percorso della cartella/i)
    expect(campo.closest(".al-avvio__riga-6")?.textContent).toBe("Verifica")
    const avanti = () => screen.getByRole("button", { name: /^avanti$/i })
    // tavola `cmd`: without folders the step's command is the full one, Avanti tenue
    expect(avanti().className).toContain("al-bottone--tenue")
    expect(screen.getByRole("button", { name: /^verifica$/i }).className).toContain("al-bottone--pieno")

    fireEvent.change(campo, { target: { value: "D:/Astro" } })
    fireEvent.click(screen.getByRole("button", { name: /^verifica$/i }))
    const aggiungi = await screen.findByRole("button", { name: /aggiungi cartella/i })
    const esito = aggiungi.closest("[role=status]") as HTMLElement
    expect(within(esito).getByText("File trovati")).toBeDefined()
    expect(within(esito).getByText("12 file FITS · D:/Astro")).toBeDefined()
    // the check steps down to tenue: the full command is the one in the outcome
    expect(screen.getByRole("button", { name: /^verifica$/i }).className).toContain("al-bottone--tenue")
    expect(avanti().className).toContain("al-bottone--tenue")
  })

  it("le cartelle aggiunte sono un elenco del foglio: percorso e frame di ognuna", async () => {
    primoAvvio({}, ["D:/Astro/2024", "E:/Vecchie"])
    await alTerzoPasso()
    const voci = await waitFor(() => {
      const trovate = [...document.querySelectorAll(".al-avvio__colonna-13 > .al-avvio__riga-14")]
      expect(trovate).toHaveLength(2)
      return trovate
    })
    expect(voci[0]?.querySelector(".al-avvio__tondo-4")?.textContent).toBe("✓")
    expect(voci[0]?.querySelector(".al-avvio__testo-19")?.textContent).toBe("D:/Astro/2024")
    // never read yet: no count is made up from the database's zero
    expect(voci[0]?.querySelector(".al-avvio__testo-9")).toBeNull()
    expect(
      voci[0]?.closest(".al-avvio__colonna-15")?.querySelector(".al-avvio__testo-13")?.textContent,
    ).toBe("Cartelle aggiunte")
    // folders added, nothing waiting: Avanti is the full command again
    expect(screen.getByRole("button", { name: /^avanti$/i }).className).toContain("al-bottone--pieno")
  })

  it("le cartelle indicate si vedono in elenco", async () => {
    // Senza l'elenco non sai cosa hai gia' dato: si finisce per aggiungere due volte la stessa
    // cartella (e la seconda volta l'app risponde "c'e' gia'", che sembra un errore tuo).
    //
    // Si parte da un elenco **vuoto** e si guarda che compaia dopo: partendo da uno che la
    // contiene gia', il testo sarebbe a schermo dal montaggio e la prova resterebbe verde anche
    // se l'aggiunta non facesse niente.
    primoAvvio({}, [])
    await alTerzoPasso()
    expect(screen.queryByText("E:/Nuova")).toBeNull()

    cambia({
      "GET /api/v1/folders": { stato: 200, corpo: elenco(["E:/Nuova"]) },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
      "/api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
      // la sonda PRIMA della registrazione: fra due voci col metodo vince quella dichiarata
      // per prima, e `POST /api/v1/folders` contiene anche `/api/v1/folders/probe`
      "POST /api/v1/folders/probe": { stato: 200, corpo: SONDA },
      "POST /api/v1/folders": { stato: 201, corpo: { id: 1, root_path: "E:/Nuova" } },
      ...SPINA,
    })
    await indica("E:/Nuova")

    expect(await screen.findByText("E:/Nuova")).toBeDefined()
  })

  it("mentre l elenco arriva, Seleziona cartella non punta a quella di prima", async () => {
    // Il difetto piu' insidioso di tutta la fetta, e si vede **solo** se la risposta tarda: appena
    // clicchi un nome la richiesta parte, e per un istante l'app non ha ancora l'elenco nuovo.
    // Ripiegando su cio' che aveva in mano, in quell'istante lo schermo diceva `/data` e "Usa
    // questa cartella" **registrava `/data`** mentre tu credevi di aver scelto `/data/Notti`. Su
    // un NAS lento e' un secondo intero, e nessuno se ne accorgerebbe.
    let arriva = () => {}
    const tarda = new Promise<void>((r) => {
      arriva = r
    })
    primoAvvio({
      "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "posix", data_root: "/data" } },
      "GET /api/v1/folders/browse?path=%2Fdata%2FNotti": {
        stato: 200,
        corpo: { path: "/data/Notti", parent: "/data", folders: [] },
        attesa: tarda,
      },
      "GET /api/v1/folders/browse": {
        stato: 200,
        corpo: { path: "/data", parent: null, folders: [{ name: "Notti", path: "/data/Notti" }] },
      },
      "POST /api/v1/folders/probe": {
        stato: 200,
        corpo: { reachable: true, fits_count: 7, complete: true, root_path: "/data/Notti" },
      },
    })
    await alTerzoPasso()

    // la cartella e' una **riga** col suo bottone: si aspetta il nome (i `listitem` ci sono gia',
    // sono le tappe del binario) e si apre da li'
    const voce = (await screen.findByText("Notti")).closest("li")
    fireEvent.click(within(voce as HTMLElement).getByRole("button", { name: /apri/i }))
    // qui l'elenco nuovo NON e' ancora arrivato, ed e' il momento che conta
    expect(dove()).toBe("/data/Notti")
    // e finche' non arriva non si registra niente: sondare una cartella mentre se ne carica
    // un'altra non ha senso in nessun caso
    expect(
      screen.getByRole("button", { name: /^seleziona cartella$/i }).getAttribute("aria-disabled"),
    ).toBe("true")

    arriva()
    expect(await screen.findByRole("button", { name: /cartella superiore/i })).toBeDefined()
  })

  it("nell elenco del NAS si entra, e si registra la cartella dove sei", async () => {
    // Prima cliccare un nome lo **sondava** invece di aprirlo: si vedeva un livello solo, e la
    // radice dei dati -- dove le foto stanno spesso -- non si poteva indicare affatto. Chi ha il
    // NAS montato con le foto in `/data/Notti/2024` non riusciva a dire niente.
    //
    // La prova va fino in fondo -- si entra, si guarda dove si e' finiti, si registra -- perche'
    // e' l'unica forma che si accorge del difetto vero: col ripiego sulla radice, "Usa questa
    // cartella" registrava `/data` mentre a schermo si era appena entrati in `/data/Notti`.
    primoAvvio({
      "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "posix", data_root: "/data" } },
      "GET /api/v1/folders/browse?path=%2Fdata%2FNotti": {
        stato: 200,
        corpo: { path: "/data/Notti", parent: "/data", folders: [] },
      },
      "GET /api/v1/folders/browse": {
        stato: 200,
        corpo: { path: "/data", parent: null, folders: [{ name: "Notti", path: "/data/Notti" }] },
      },
      "POST /api/v1/folders/probe": {
        stato: 200,
        corpo: { reachable: true, fits_count: 7, complete: true, root_path: "/data/Notti" },
      },
    })
    await alTerzoPasso()

    // la cartella e' una **riga** col suo bottone: si aspetta il nome (i `listitem` ci sono gia',
    // sono le tappe del binario) e si apre da li'
    const voce = (await screen.findByText("Notti")).closest("li")
    fireEvent.click(within(voce as HTMLElement).getByRole("button", { name: /apri/i }))

    // dove sei lo dice lo schermo, e da li' in poi e' quella la cartella in gioco
    await waitFor(() => expect(dove()).toBe("/data/Notti"))
    // una cartella senza altre dentro lo dice: non e' un guasto, quella dove sei si usa lo stesso
    expect(await screen.findByText(/nessuna sottocartella/i)).toBeDefined()
    // e adesso si puo' risalire: il tasto esiste solo quando si e' scesi
    expect(screen.getByRole("button", { name: /cartella superiore/i })).toBeDefined()

    fireEvent.click(screen.getByRole("button", { name: /^seleziona cartella$/i }))
    fireEvent.click(await screen.findByRole("button", { name: /aggiungi/i }))

    await waitFor(() =>
      expect(
        scritture().some(
          (s) =>
            s.url.endsWith("/api/v1/folders") &&
            (s.corpo as { root_path: string }).root_path === "/data/Notti",
        ),
      ).toBe(true),
    )
  })

  it("anche il ramo del NAS passa dai mattoni", async () => {
    // L'altra prova dei mattoni (`wizard.test.tsx`) attraversa il terzo passo col percorso da
    // scrivere: `data_root` nullo, cioe' il desktop. Sul NAS quel passo e' un'altra schermata --
    // l'elenco da sfogliare, *Usa questa cartella*, *Sali*, l'esito della sonda -- e li' i
    // bottoni sono cinque su nove di tutto il primo avvio: senza questa prova la meta' piu'
    // popolata non la guarda nessuno.
    primoAvvio({
      "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "posix", data_root: "/data" } },
      "GET /api/v1/folders/browse": {
        stato: 200,
        corpo: { path: "/data", parent: null, folders: [{ name: "Notti", path: "/data/Notti" }] },
      },
      "POST /api/v1/folders/probe": { stato: 200, corpo: SONDA },
    })
    await alTerzoPasso()
    await screen.findByText("Notti")

    // la schermata dell'elenco
    expect(quantiControlli()).toBeGreaterThan(3)
    expect(fuoriDaiMattoni()).toEqual([])

    // e quella dopo la sonda, che porta l'esito e il tasto che registra
    fireEvent.click(screen.getByRole("button", { name: /^seleziona cartella$/i }))
    await screen.findByRole("button", { name: /aggiungi/i })
    expect(fuoriDaiMattoni()).toEqual([])
  })

  it("se l elenco del NAS non arriva, si puo' scrivere il percorso", async () => {
    // Un elenco che non si carica non puo' lasciare senza strade: li' la scrittura a mano non
    // esiste, e l'utente resterebbe davanti a un titolo e al vuoto.
    primoAvvio({
      "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "posix", data_root: "/data" } },
      "GET /api/v1/folders/browse": { stato: 409, corpo: { detail: { code: "root_unreachable" } } },
    })
    await alTerzoPasso()

    expect(await screen.findByText("Elenco delle cartelle non disponibile")).toBeDefined()
    expect(await screen.findByLabelText(/percorso della cartella/i)).toBeDefined()
    expect(screen.getByText("Percorso interno al container, non quello del computer.")).toBeDefined()
  })

  it("alla fine la lettura parte da sola", async () => {
    // E' la promessa di questa fetta: chi installa non deve sapere che esiste un pulsante.
    primoAvvio()
    await alTerzoPasso()
    await indica("D:/Astro/2024")

    fireEvent.click(screen.getByRole("button", { name: /avanti/i }))
    fireEvent.click(screen.getByRole("button", { name: /^fine$/i }))

    await waitFor(() =>
      expect(scritture().some((s) => s.url.endsWith("/api/v1/scan"))).toBe(true),
    )
  })

  it("se la lettura non parte, il primo avvio finisce lo stesso", async () => {
    // Il timbro e' gia' scritto: tenere l'utente dentro il primo avvio perche' una chiamata in
    // piu' e' andata storta vorrebbe dire chiuderlo in una stanza di cui ha gia' la chiave. La
    // scansione, semmai, si chiede col pulsante in barra.
    // Le cartelle ci sono -- quindi la scansione si chiede davvero -- ed e' **lei** a rifiutare.
    primoAvvio()
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    cambia({
      "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "GET /api/v1/folders": { stato: 200, corpo: elenco(["D:/Astro/2024"]) },
      "POST /api/v1/scan": { stato: 409, corpo: { detail: { code: "worker_busy" } } },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    fireEvent.click(screen.getByRole("button", { name: /salta/i }))

    expect(await screen.findByRole("navigation")).toBeDefined()
    expect(scritture().some((s) => s.url.endsWith("/api/v1/scan"))).toBe(true)
  })

  it("chi salta senza indicare niente non fa partire niente", async () => {
    // Saltare resta possibile sempre e senza conferme. Chiedere al backend di leggere quando non
    // c'e' nessuna cartella vorrebbe dire aprire il primo avvio con un errore in faccia.
    primoAvvio({}, [])
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    cambia({
      "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/folders": { stato: 200, corpo: elenco([]) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    fireEvent.click(screen.getByRole("button", { name: /salta/i }))

    await screen.findByRole("navigation")
    expect(scritture().some((s) => s.url.endsWith("/api/v1/scan"))).toBe(false)
  })

  it("dove c e una radice dei dati le cartelle si scelgono, non si scrivono", async () => {
    // Sul NAS in Docker l'utente non sa che percorso abbia la sua cartella **dentro** il
    // container: scriverlo a mano e' indovinare. La rotta che le elenca esiste da sempre e
    // nessuno la chiamava.
    primoAvvio({
      "GET /api/v1/folders/path-info": {
        stato: 200,
        corpo: { family: "posix", data_root: "/data" },
      },
      "GET /api/v1/folders/browse": {
        stato: 200,
        corpo: {
          path: "/data",
          parent: null,
          folders: [
            { name: "M31", path: "/data/M31" },
            { name: "Notti", path: "/data/Notti" },
          ],
        },
      },
    })
    await alTerzoPasso()

    const elenco = await screen.findByRole("list", { name: /sottocartelle/i })
    expect(await within(elenco).findByText("M31")).toBeDefined()
    expect(chiamate().some((u) => u.includes("/api/v1/folders/browse"))).toBe(true)
    // l'altra meta' del titolo: li' il percorso NON si scrive
    expect(screen.queryByLabelText(/percorso della cartella/i)).toBeNull()
    // la forma del foglio: l'elenco scorre nel suo pozzo, una riga per cartella
    expect(elenco.className).toBe("al-avvio__colonna-20")
    expect(
      elenco.closest(".al-avvio__colonna-18")?.querySelector(".al-avvio__testo-17")?.textContent,
    ).toBe("Scegli una cartella")
    const voce = within(elenco).getByText("M31").closest("li") as HTMLElement
    expect(voce.className).toBe("al-avvio__riga-13")
    expect(within(elenco).getByText("M31").className).toBe("al-avvio__blocco-7")
    const apri = within(voce).getByRole("button", { name: /apri m31/i })
    expect(apri.className).toContain("al-bottone--tenue")
    expect(voce.children).toHaveLength(2)
    // at the data root there is no going higher
    expect(
      screen.getByRole("button", { name: /cartella superiore/i }).getAttribute("aria-disabled"),
    ).toBe("true")
    expect(
      screen.getByRole("button", { name: /cartella dei dati/i }).getAttribute("aria-disabled"),
    ).toBe("true")
  })

  it("una cartella senza sottocartelle lo dice nel pozzo dell'elenco", async () => {
    primoAvvio({
      "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "posix", data_root: "/data" } },
      "GET /api/v1/folders/browse": { stato: 200, corpo: { path: "/data", parent: null, folders: [] } },
    })
    await alTerzoPasso()
    const niente = await screen.findByText("Nessuna sottocartella")
    expect(niente.className).toBe("al-avvio__blocco-8")
  })

  it("sul NAS la carta spiega che si sfoglia, non che si scrive", async () => {
    // La riga in cima alla carta dice **perche'** l'app chiede: sul NAS mandava a "scrivere il
    // percorso di una cartella" sopra una schermata che il percorso non lo fa scrivere affatto.
    primoAvvio({
      "GET /api/v1/folders/path-info": {
        stato: 200,
        corpo: { family: "posix", data_root: "/data" },
      },
      "GET /api/v1/folders/browse": {
        stato: 200,
        corpo: { path: "/data", parent: null, folders: [] },
      },
    })
    await alTerzoPasso()

    expect(await screen.findByText(/l'app \u00e8 in un container/i)).toBeDefined()
    expect(screen.queryByText(/indica una cartella/i)).toBeNull()
  })

  it("sul computer la carta spiega che si scrive, non che si sfoglia", async () => {
    // L'altra meta': senza radice dei dati la riga giusta e' l'altra, e una sola delle due e'
    // vera per chi la legge.
    primoAvvio()
    await alTerzoPasso()

    expect(screen.getByText(/indica una cartella/i)).toBeDefined()
    expect(screen.queryByText(/l'app \u00e8 in un container/i)).toBeNull()
  })
})

describe("una cartella spostata", () => {
  it("la sonda la riconosce, e il tasto la sposta invece di registrarne una nuova", async () => {
    // Registrata di nuovo, ogni frame avrebbe due posti e le risposte date resterebbero sul
    // percorso vecchio.
    primoAvvio({
      "POST /api/v1/folders/7/move": { stato: 200, corpo: {} },
      "POST /api/v1/folders/probe": {
        stato: 200,
        corpo: {
          ...SONDA,
          root_path: "E:/Astro",
          moved_from: { id: 7, root_path: "D:/Astro" },
          moved_check: "found",
        },
      },
    })
    await alTerzoPasso()
    fireEvent.change(screen.getByLabelText(/percorso della cartella/i), {
      target: { value: "E:/Astro" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica$/i }))

    expect(await screen.findByText(/corrisponde a D:\/Astro: stessi file/i)).toBeDefined()
    expect(screen.queryByRole("button", { name: /aggiungi/i })).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /^usa questo percorso$/i }))

    await waitFor(() =>
      expect(
        scritture().some(
          (s) =>
            s.url.endsWith("/api/v1/folders/7/move") &&
            (s.corpo as { root_path: string }).root_path === "E:/Astro",
        ),
      ).toBe(true),
    )
    expect(scritture().some((s) => s.url.endsWith("/api/v1/folders"))).toBe(false)
    // Come dopo Aggiungi: il percorso usato non resta nel campo a farsi riusare per sbaglio.
    expect((screen.getByLabelText(/percorso della cartella/i) as HTMLInputElement).value).toBe(
      "",
    )
  })
})

describe("il percorso per chi ascolta", () => {
  it("quando l elenco non arriva, cosa farci sta dentro l avviso", async () => {
    // Il disegno dice: il guasto che riguarda la pagina porta **dentro di se'** i gesti che lo
    // risolvono. Staccati, sarebbero da cercare -- e su questo passo `Sali` sparisce insieme
    // all'elenco, quindi chi e' sceso di tre livelli resterebbe senza modo di tornare.
    primoAvvio({
      "GET /api/v1/folders/path-info": {
        stato: 200,
        corpo: { family: "posix", data_root: "/data" },
      },
      "GET /api/v1/folders/browse": { stato: 500, corpo: { detail: { code: "rotto" } } },
    })
    await alTerzoPasso()

    // tavola v82 `C.nasNo`: the notice says what to do, and the path field is that road
    const dentro = (await screen.findByText("Elenco delle cartelle non disponibile")).closest(
      "[role=status]",
    ) as HTMLElement
    expect(within(dentro).getByText("Inserisci il percorso.")).toBeDefined()
    expect(screen.getByLabelText(/percorso della cartella/i)).toBeDefined()
    // at the root there is nowhere to go back to
    expect(within(dentro).queryByRole("button")).toBeNull()
  })

  it("sceso di tre livelli, l elenco che cade lascia la strada per tornare", async () => {
    // `Sali` sparisce insieme alla risposta, quindi il ritorno alla radice sta **dentro**
    // l'avviso: senza, chi e' sceso resterebbe fermo dov'e' senza modo di risalire.
    primoAvvio({
      "GET /api/v1/folders/path-info": {
        stato: 200,
        corpo: { family: "posix", data_root: "/data" },
      },
      "GET /api/v1/folders/browse?path=%2Fdata%2FNotti": {
        stato: 500,
        corpo: { detail: { code: "rotto" } },
      },
      "GET /api/v1/folders/browse": {
        stato: 200,
        corpo: { path: "/data", parent: null, folders: [{ name: "Notti", path: "/data/Notti" }] },
      },
    })
    await alTerzoPasso()
    fireEvent.click(await screen.findByRole("button", { name: /apri notti/i }))

    const dentro = (await screen.findByText("Elenco delle cartelle non disponibile")).closest(
      "[role=status]",
    ) as HTMLElement
    fireEvent.click(within(dentro).getByRole("button", { name: /^cartella dei dati$/i }))

    await waitFor(() => expect(dove()).toBe("/data"))
  })
})
