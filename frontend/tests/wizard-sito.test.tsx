// @vitest-environment jsdom
/**
 * Il **secondo passo** del primo avvio: da dove osservi. E' quello che fa nascere le notti.
 *
 * Sta in un file suo come le cartelle e il riconoscitore: il guscio del primo avvio -- il timbro,
 * il binario, il piede -- resta in `wizard.test.tsx`. Qui c'e' quello che riguarda il posto: che
 * la strada manuale sia **sempre** aperta, che una coordinata scritta come l'app la suggerisce
 * venga letta, e che cio' che non va si dica **sul campo** invece che dopo aver premuto.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { STANOTTE, chiamate, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"

afterEach(pulisci)

/** Le risposte dell'API **prima** del timbro: qui il primo avvio c'e' sempre, ed e' il punto.
 *  Il ramo "col timbro" non esiste apposta -- portato qui accanto al guscio sarebbe una copia
 *  che diverge senza che nessuno la percorra, e diverge gia'. Le rotte piu' lunghe stanno
 *  davanti: il banco sceglie la prima che l'indirizzo contiene. */
function senzaTimbro(extra: Record<string, { stato: number; corpo: unknown }> = {}) {
  rispondi({
    ...STANOTTE,
    "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
    "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
    ...extra,
  })
}

/** Porta il primo avvio al passo chiesto (0 = il primo). */
function vaiAlPasso(n: number) {
  for (let i = 0; i < n; i++) fireEvent.click(screen.getByRole("button", { name: /avanti/i }))
}

describe("il posto da cui osservi", () => {
  it("il secondo passo cerca il posto per nome e ne fa il luogo di casa", async () => {
    senzaTimbro({
      "/api/v1/places": {
        stato: 200,
        corpo: { items: [{ name: "Verona", latitude: 45.44, longitude: 10.99 }] },
      },
      "/api/v1/sites": { stato: 201, corpo: { id: 1, name: "Verona" } },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/localit\u00e0/i), {
      target: { value: "Verona" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^cerca$/i }))
    // il posto trovato ora e' una **riga** -- nome, coordinate, e il bottone che lo sceglie --
    // quindi si cerca il bottone dentro la riga che porta quel nome, non un bottone che si
    // chiama come il posto
    // si aspetta **il posto**, non la lista: i `listitem` ci sono gia' -- sono le tappe del
    // binario -- quindi aspettarli tornerebbe subito, prima che la ricerca abbia risposto
    const trovato = (await screen.findByText("Verona")).closest("li")
    fireEvent.click(within(trovato as HTMLElement).getByRole("button", { name: /seleziona/i }))
    fireEvent.click(screen.getByRole("button", { name: /salva sito/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/sites"))
      // `is_default` vero: e' il luogo di casa che decide il fuso delle notti, e al primo avvio
      // un luogo che non e' di nessuno non farebbe nascere niente.
      expect(scritta?.corpo).toMatchObject({
        name: "Verona",
        latitude: 45.44,
        longitude: 10.99,
        is_default: true,
      })
    })
  })
  it("cio che l API non distingue, lo schermo non lo inventa", async () => {
    // **Decisione del backend, gia' presa e gia' provata**
    // (`backend/tests/test_sites.py`, `test_searching_without_network_gives_an_empty_list_not_an_error`):
    // senza rete `GET /places` risponde **200 con elenco vuoto**, mai un errore, perche' un
    // servizio muto non deve diventare un guasto in faccia a chi sta creando un luogo.
    //
    // Quindi "non ho trovato" e "non ho potuto cercare" arrivano qui **identici**, e una frase
    // "senza rete" sarebbe irraggiungibile: un testo che nessun utente vedra' mai, che pero'
    // farebbe sembrare coperta una regola che non lo e'. Si dice l'unica cosa vera per tutti e
    // due i casi, e la strada manuale resta aperta -- che e' cio' che serve davvero a chi
    // osserva da un posto buio.
    senzaTimbro({ "/api/v1/places": { stato: 200, corpo: { items: [] } } })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/localit\u00e0/i), {
      target: { value: "Zzz" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^cerca$/i }))
    expect(await screen.findByText(/nessun risultato/i)).toBeDefined()
    expect(screen.queryByText(/senza rete/i)).toBeNull()
    expect(screen.getByLabelText(/latitudine/i)).toBeDefined()
    expect(screen.getByLabelText(/longitudine/i)).toBeDefined()
  })
  it("un luogo che non si salva non fa finta di essersi salvato", async () => {
    // Il difetto peggiore trovato su questa fetta: la scrittura falliva e il passo avanzava lo
    // stesso. Chi osserva si ritrova senza luogo di casa -- e senza luogo le notti non nascono,
    // che era l'unica cosa che questa fetta doveva ottenere.
    senzaTimbro({
      "/api/v1/places": {
        stato: 200,
        corpo: { items: [{ name: "Verona", latitude: 45.44, longitude: 10.99 }] },
      },
      "/api/v1/sites": { stato: 500, corpo: { detail: { code: "rotto" } } },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/localit\u00e0/i), {
      target: { value: "Verona" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^cerca$/i }))
    // il posto trovato ora e' una **riga** -- nome, coordinate, e il bottone che lo sceglie --
    // quindi si cerca il bottone dentro la riga che porta quel nome, non un bottone che si
    // chiama come il posto
    // si aspetta **il posto**, non la lista: i `listitem` ci sono gia' -- sono le tappe del
    // binario -- quindi aspettarli tornerebbe subito, prima che la ricerca abbia risposto
    const trovato = (await screen.findByText("Verona")).closest("li")
    fireEvent.click(within(trovato as HTMLElement).getByRole("button", { name: /seleziona/i }))
    fireEvent.click(screen.getByRole("button", { name: /salva sito/i }))
    expect(await screen.findByRole("alert")).toBeDefined()
    // E soprattutto: si resta qui, dove il problema si puo' ancora risolvere.
    expect(screen.getByLabelText(/localit\u00e0/i)).toBeDefined()
  })
  it("chi non ha rete deve poter dare un nome al suo luogo", async () => {
    // Il difetto piu' grave della fetta: il nome veniva preso dalla casella di RICERCA, quindi
    // chi prende la strada manuale -- coordinate a mano, senza cercare, che e' esattamente il
    // caso per cui quella strada esiste -- mandava nome vuoto. Il modello pretende almeno un
    // carattere (`backend/astrolog/api/models_site.py`), quindi 422, e a schermo solo "il luogo
    // non si e' salvato". Chi osserva da un posto senza rete non poteva creare il suo luogo.
    senzaTimbro({ "/api/v1/sites": { stato: 201, corpo: { id: 1, name: "Casa" } } })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/nome del sito/i), { target: { value: "Casa" } })
    // **Con la virgola e con la lettera**, che e' come il segnaposto le propone a un italiano:
    // scritte col punto, anche `Number` le leggerebbe, e la riparazione del parser resterebbe
    // senza prova -- il tasto si accenderebbe e nel corpo finirebbe `null`.
    fireEvent.change(screen.getByLabelText(/latitudine/i), { target: { value: "45,8 N" } })
    fireEvent.change(screen.getByLabelText(/longitudine/i), { target: { value: "11,5 E" } })
    fireEvent.click(screen.getByRole("button", { name: /salva sito/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/sites"))
      expect(scritta?.corpo).toMatchObject({ name: "Casa", latitude: 45.8, longitude: 11.5 })
    })
  })
  it("una ricerca caduta porta dentro di se' cosa farci", async () => {
    // Il disegno dice: il guasto che riguarda la pagina porta **dentro l'avviso** i gesti che lo
    // risolvono -- riprovare, o passare alla strada che non dipende dalla rete. Staccati,
    // sarebbero due cose da cercare proprio mentre qualcosa non ha funzionato.
    senzaTimbro({ "/api/v1/places": { stato: 500, corpo: { detail: { code: "rotto" } } } })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/localit\u00e0/i), { target: { value: "Verona" } })
    fireEvent.click(screen.getByRole("button", { name: /^cerca$/i }))

    const dentro = (await screen.findByRole("alert")).closest(".as-avviso") as HTMLElement
    expect(within(dentro).getByRole("button", { name: /riprova/i })).toBeDefined()

    // e *Scrivi a mano* porta **dove si comincia**, cioe' al nome: portando alla latitudine si
    // saltava il campo che il tasto pretende, e riempite le coordinate il tasto restava spento
    // senza dire perche' -- lo stesso difetto della virgola, con un altro ingresso
    fireEvent.click(within(dentro).getByRole("button", { name: /inserisci le coordinate/i }))
    expect(document.activeElement?.id).toBe("wizard-name")
  })

  it("un nome che manca lo dice, invece di spegnere il tasto in silenzio", async () => {
    // Finche' non si e' scritto niente il campo non e' sbagliato, e' solo vuoto. Ma appena si
    // comincia a compilare, un tasto spento senza ragione e' il difetto che questa schermata ha
    // gia' pagato una volta.
    senzaTimbro()
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    const nome = screen.getByLabelText(/nome del sito/i)
    expect(nome.getAttribute("aria-invalid")).toBeNull()

    fireEvent.change(screen.getByLabelText(/latitudine/i), { target: { value: "45,44" } })
    fireEvent.change(screen.getByLabelText(/longitudine/i), { target: { value: "12,05" } })

    expect(nome.getAttribute("aria-invalid")).toBe("true")
    expect(
      document.getElementById(nome.getAttribute("aria-describedby") as string)?.textContent,
    ).toContain("Nome obbligatorio")
    expect(screen.getByRole("button", { name: /salva sito/i }).hasAttribute("disabled")).toBe(
      true,
    )
  })

  it("il cielo scelto entra nel sito, e dice cosa ci si vede", async () => {
    // La classe non si salva: il backend ne ricava la luminosita'. Ma se non parte nel corpo,
    // il cielo resta non dichiarato e nessuno se ne accorge -- il sito si salva lo stesso.
    senzaTimbro({ "/api/v1/sites": { stato: 201, corpo: { id: 1, name: "Malga" } } })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/nome del sito/i), { target: { value: "Malga" } })
    fireEvent.change(screen.getByLabelText(/latitudine/i), { target: { value: "46,4843 N" } })
    fireEvent.change(screen.getByLabelText(/longitudine/i), { target: { value: "12,0561 E" } })

    fireEvent.click(screen.getByRole("radio", { name: /^Bortle 3 -/ }))
    // e la scelta si legge: la riga dice cosa ci si vede, non solo il numero
    expect(screen.getByText(/Via Lattea/i)).toBeDefined()

    fireEvent.click(screen.getByRole("button", { name: /salva sito/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/sites"))
      expect(scritta?.corpo).toMatchObject({ name: "Malga", bortle: 3 })
    })
  })

  it("chi non risponde sul cielo salva un sito senza cielo, non il migliore", async () => {
    // Una classe di partenza dichiarerebbe un cielo eccellente a chi non ha risposto, e quel
    // numero diventerebbe la luminosita' salvata del suo sito.
    senzaTimbro({ "/api/v1/sites": { stato: 201, corpo: { id: 1, name: "Malga" } } })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/nome del sito/i), { target: { value: "Malga" } })
    fireEvent.change(screen.getByLabelText(/latitudine/i), { target: { value: "46,4843 N" } })
    fireEvent.change(screen.getByLabelText(/longitudine/i), { target: { value: "12,0561 E" } })
    fireEvent.click(screen.getByRole("button", { name: /salva sito/i }))

    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/sites"))
      expect(scritta?.corpo).toBeDefined()
      expect(Object.keys(scritta?.corpo as object)).not.toContain("bortle")
    })
  })

  it("in elenco ogni bottone si chiama col suo posto, non tutti Seleziona", async () => {
    // Venti righe fanno venti bottoni che si chiamano uguale: chi naviga per bottoni o comanda a
    // voce ("clicca Verona") non ne distingue nessuno.
    senzaTimbro({
      "/api/v1/places": {
        stato: 200,
        corpo: {
          items: [
            { name: "Verona", latitude: 45.44, longitude: 10.99 },
            { name: "Vicenza", latitude: 45.55, longitude: 11.55 },
          ],
        },
      },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/localit\u00e0/i), { target: { value: "V" } })
    fireEvent.click(screen.getByRole("button", { name: /^cerca$/i }))

    expect(await screen.findByRole("button", { name: /seleziona verona/i })).toBeDefined()
    expect(screen.getByRole("button", { name: /seleziona vicenza/i })).toBeDefined()
  })

  it("una ricerca che va storta non si traveste da nessun risultato", async () => {
    // "Elenco vuoto = non lo so" vale per una risposta **riuscita**. Un 422 o un 500 sono un
    // guasto, e dirgli "nessun posto con questo nome" manda l'utente a correggere un nome che
    // era giusto.
    senzaTimbro({
      "/api/v1/places": { stato: 422, corpo: { detail: [{ msg: "q troppo corta" }] } },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/localit\u00e0/i), { target: { value: "x" } })
    fireEvent.click(screen.getByRole("button", { name: /^cerca$/i }))
    expect(await screen.findByRole("alert")).toBeDefined()
    expect(screen.queryByText(/nessun risultato/i)).toBeNull()
  })
  it("senza coordinate non nasce nessun luogo", async () => {
    // `Number("")` fa **zero**, e zero-zero e' un punto nel Golfo di Guinea: un luogo di casa
    // li' deciderebbe il fuso di tutte le notti. Un campo vuoto non e' una coordinata.
    senzaTimbro({ "/api/v1/sites": { stato: 201, corpo: { id: 1, name: "x" } } })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    // Il tasto si vede spento: e' la meta' che l'utente puo' constatare, e senza questa riga
    // toglierlo lascerebbe la suite verde.
    expect(screen.getByRole("button", { name: /salva sito/i })).toHaveProperty(
      "disabled",
      true,
    )
    fireEvent.click(screen.getByRole("button", { name: /salva sito/i }))
    await waitFor(() => expect(chiamate().length).toBeGreaterThan(0))
    expect(scritture().some((s) => s.url.includes("/api/v1/sites"))).toBe(false)
  })
  it("una coordinata fuori scala lo dice sul campo, prima di mandarla", async () => {
    // Il motivo sta **sotto il campo** e legato a lui: in un avviso staccato chi arriva col
    // tabulatore non lo sente, e un 422 dal server arriverebbe dopo aver premuto.
    senzaTimbro()
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    const lat = screen.getByLabelText(/latitudine/i)
    fireEvent.change(lat, { target: { value: "120" } })
    expect(lat.getAttribute("aria-invalid")).toBe("true")
    const motivo = document.getElementById(lat.getAttribute("aria-describedby") as string)
    // il testo intero, non solo il numero: `toContain("90")` restava verde anche su un tetto
    // scritto a mano al posto di quello dell'asse
    expect(motivo?.textContent).toBe("Valore fra -90 e 90")

    // e la longitudine ha **il suo** tetto, che e' il doppio: senza questa riga, portarlo a 90
    // avrebbe reso irricevibile Sydney (151 gradi est) senza che niente cadesse
    const lon = screen.getByLabelText(/longitudine/i)
    fireEvent.change(lon, { target: { value: "151,2" } })
    expect(lon.getAttribute("aria-invalid")).toBeNull()
    fireEvent.change(lon, { target: { value: "181" } })
    expect(
      document.getElementById(lon.getAttribute("aria-describedby") as string)?.textContent,
    ).toBe("Valore fra -180 e 180")

    // e il tasto che salva resta spento finche' un campo dice che c'e' qualcosa che non va:
    // acceso, manderebbe una scrittura che il backend rifiuta col motivo scritto a due
    // centimetri. Si guarda **una guardia per volta**: con tutte e due le coordinate storte il
    // tasto resta spento comunque, e togliere quella della longitudine lascerebbe la prova verde.
    fireEvent.change(screen.getByLabelText(/nome del sito/i), { target: { value: "Malga" } })
    fireEvent.change(lat, { target: { value: "45,44" } })
    expect(screen.getByRole("button", { name: /salva sito/i }).hasAttribute("disabled")).toBe(
      true,
    )
    // e ora l'altra meta': la latitudine buona, la longitudine storta
    fireEvent.change(lon, { target: { value: "12,05" } })
    fireEvent.change(lat, { target: { value: "120" } })
    expect(screen.getByRole("button", { name: /salva sito/i }).hasAttribute("disabled")).toBe(
      true,
    )

    // e una coordinata buona non lascia il campo segnato -- scritta **con la virgola**, che e'
    // quella che il segnaposto italiano propone: con `Number` era NaN, il campo tornava pulito
    // per la ragione sbagliata e il tetto poteva essere qualunque senza che niente cadesse
    fireEvent.change(lat, { target: { value: "45,44" } })
    expect(screen.getByLabelText(/latitudine/i).getAttribute("aria-invalid")).toBeNull()
    expect(screen.getByRole("button", { name: /salva sito/i }).hasAttribute("disabled")).toBe(
      false,
    )
  })
  it("una coordinata che non e' un numero dice perche', invece di tacere", async () => {
    // La stessa regola del fuori scala, sull'altra meta': chi scrive qualcosa che non e' una
    // coordinata -- una parola, o la lettera dell'altro emisfero -- trovava il tasto spento e
    // **nessuna ragione a schermo**. E' esattamente il difetto che la virgola aveva gia' fatto
    // pagare a questa schermata.
    senzaTimbro()
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    const lat = screen.getByLabelText(/latitudine/i)

    fireEvent.change(lat, { target: { value: "quassu'" } })
    expect(lat.getAttribute("aria-invalid")).toBe("true")
    expect(
      document.getElementById(lat.getAttribute("aria-describedby") as string)?.textContent,
    ).toContain("Coordinata non valida")

    // e "45 W" nella latitudine non e' 45 gradi sud: e' qualcosa che non sappiamo leggere
    fireEvent.change(lat, { target: { value: "45 W" } })
    expect(lat.getAttribute("aria-invalid")).toBe("true")
  })
  it("due posti con lo stesso nome non si accendono insieme", async () => {
    // Una ricerca per "Verona" torna quella italiana e quella dello stato di New York. Col solo
    // nome, sceglierne una accendeva "scelto" su tutte e due, e chi guarda non sa piu' quale
    // punto sta per salvare.
    senzaTimbro({
      "/api/v1/places": {
        stato: 200,
        corpo: {
          items: [
            { name: "Verona", latitude: 45.44, longitude: 10.99 },
            { name: "Verona", latitude: 42.98, longitude: -75.58 },
          ],
        },
      },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    fireEvent.change(screen.getByLabelText(/localit\u00e0/i), { target: { value: "Verona" } })
    fireEvent.click(screen.getByRole("button", { name: /^cerca$/i }))

    const righe = await screen.findAllByText("Verona")
    fireEvent.click(
      within(righe[0]!.closest("li") as HTMLElement).getByRole("button", { name: /seleziona/i }),
    )

    expect(screen.getAllByText(/^selezionato$/i)).toHaveLength(1)
    // e quella salvata e' la prima, non la seconda
    expect(screen.getByLabelText(/latitudine/i).getAttribute("value")).toBe("45.44")
  })
})
