// @vitest-environment jsdom
/**
 * La sezione **oggetti** di Da confermare: quella che sblocca le pose.
 *
 * Il contratto (`docs/domini/spina.md`) dice tre cose, e sono le tre che si provano qui:
 *
 * - in cima chi ha un dubbio, **coi candidati che il cielo ha trovato nel suo campo**, da
 *   cliccare; sotto quelli nuovi, e chiusi i gia' visti. L'ordine lo decide il backend;
 * - una risposta e' una **correzione**, e viaggia su una **chiave stabile** -- mai sul numero di
 *   riga: gli id si riusano, e una risposta partita prima di una corsa finirebbe addosso a un
 *   altro oggetto;
 * - **un bersaglio solo**: lo slug di un candidato cliccato **oppure** un nome scritto, mai tutti
 *   e due -- e' la stessa domanda, e accettarli insieme vorrebbe dire scegliere noi quale vince.
 *
 * E una quarta, che con i soli filtri non si poteva provare: `POST /review/apply` e' **una
 * transazione sola**, quindi uno slug che il catalogo non conosce annulla anche le risposte
 * buone. La pagina lo dice per nome e non butta via cio' che hai scritto.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, cambia, chiamate, disegna, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

/** Tre oggetti, nell'ordine che manda l'API: due con un dubbio (uno col cielo, uno senza) e uno
 *  gia' a posto. `NGC 7023` porta i tre casi di `in_frame`: dentro, accanto, e non si sa. */
const PAGINA = {
  seen: { instruments: 0, rigs: 0, objects: 0 },
  to_confirm: 2,
  filters: [],
  instruments: [],
  rigs: [],
  objects: [
    {
      id: 3,
      key: "ngc-7023",
      name: "NGC 7023",
      slug: "ngc-7023",
      method: "coord_review",
      confidence: "low",
      frames: 60,
      integration_s: 9720,
      untimed: 0,
      confirmed: false,
      candidates: [
        {
          slug: "ngc-7023",
          name: "NGC 7023",
          common_name: "Nebulosa Iris",
          in_frame: true,
        },
        { slug: "ldn-1174", name: "LDN 1174", common_name: null, in_frame: false },
        { slug: "sh2-136", name: "Sh2-136", common_name: null, in_frame: null },
      ],
    },
    {
      id: 5,
      key: "Nebulosa di casa",
      name: "Nebulosa di casa",
      slug: null,
      method: null,
      confidence: "low",
      frames: 12,
      integration_s: 0,
      untimed: 12,
      confirmed: false,
      candidates: [],
    },
    {
      id: 8,
      key: "m-31",
      name: "M 31",
      slug: "m-31",
      method: "exact_name",
      confidence: "certain",
      frames: 200,
      integration_s: 36000,
      untimed: 3,
      confirmed: true,
      candidates: [],
    },
  ],
  mosaics: [],
  unclear: [],
  unfiltered: [],
  filter_choices: [],
  rigless: [],
  unnamed: [],
  settled_objects: 0,
}

const RICEVUTA = { stato: 200, corpo: { changed: 1, confirmed: 0, requeued: 60, run_started: true } }

/** Cosa risponde il banco. Sta a parte da `aperta` perche' serve anche a **cambiare** le
 *  risposte senza rimontare la pagina, che e' l'unico modo di provare un secondo Applica. */
function mappa(pagina: unknown, apply: { stato: number; corpo: unknown }) {
  return {
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": apply,
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  }
}

const RIFIUTO = { stato: 422, corpo: { detail: { code: "unknown_target" } } }

function aperta(pagina: unknown = PAGINA, apply: { stato: number; corpo: unknown } = RICEVUTA) {
  rispondi(mappa(pagina, apply))
}

const vaiAgliOggetti = () => vaiASezione(/oggetti/i)

/** Le righe degli **oggetti**, non i candidati annidati dentro: si guardano i figli dell'elenco
 *  di primo livello, perche' `getAllByRole("listitem")` porta su anche le voci dei candidati. */
function righe(sezione: HTMLElement) {
  const elenco = within(sezione).getAllByRole("list")[0]
  return Array.from(elenco?.children ?? [])
}

/** Sceglie un candidato sulla riga di un oggetto e manda la pagina. */
function rispondiCliccando(sezione: HTMLElement, oggetto: string, candidato: RegExp) {
  fireEvent.click(within(riga(sezione, oggetto)).getByRole("button", { name: candidato }))
  fireEvent.click(screen.getByRole("button", { name: /applica/i }))
}

describe("Da confermare -- gli oggetti", () => {
  it("l ordine e quello dell API, e la pagina non lo tocca", async () => {
    // In cima chi ha un dubbio, poi per numero di pose: lo decide `review_page.py` con la sua
    // `sort`. Riordinare qui sarebbe lo stesso fatto deciso in due case.
    aperta()
    const sezione = await vaiAgliOggetti()
    const elenco = righe(sezione)
    expect(elenco[0]?.textContent?.startsWith("NGC 7023")).toBe(true)
    expect(elenco[1]?.textContent?.startsWith("Nebulosa di casa")).toBe(true)
    expect(elenco[2]?.textContent?.startsWith("M 31")).toBe(true)
  })

  it("chi ha un dubbio porta i candidati da cliccare, chi e a posto no", async () => {
    // I candidati costano un cono, e il backend li scrive solo per chi ha una domanda. Su un oggetto certo non c'e' niente da scegliere, c'e' solo da correggere.
    aperta()
    const sezione = await vaiAgliOggetti()
    const suIris = riga(sezione, "NGC 7023")
    expect(within(suIris).getByRole("button", { name: /LDN 1174/ })).toBeDefined()
    expect(within(riga(sezione, "M 31")).queryByRole("button", { name: /LDN 1174/ })).toBeNull()
  })

  it("un candidato dice se era nell inquadratura o solo li accanto", async () => {
    // E' la domanda a cui serve rispondere per scegliere: il piu' vicino al centro non e' sempre
    // il soggetto, e "c'era davvero dentro" e' cio' che lo distingue da un vicino di campo.
    aperta()
    const sezione = await vaiAgliOggetti()
    const suIris = riga(sezione, "NGC 7023")
    expect(within(suIris).getByRole("button", { name: /Nebulosa Iris/ }).textContent).toMatch(
      /nell'inquadratura/i,
    )
    expect(within(suIris).getByRole("button", { name: /LDN 1174/ }).textContent).toMatch(
      /solo li' accanto/i,
    )
  })

  it("e quando il cielo non porta i lati lo dice, invece di tacere", async () => {
    // `in_frame: null` non e' un no: e' "non si sa", perche' senza i lati e la rotazione il campo
    // si e' approssimato a un cerchio. Mostrarlo come "solo li' accanto" sarebbe una bugia, e
    // nasconderlo lascerebbe scegliere senza sapere.
    aperta()
    const sezione = await vaiAgliOggetti()
    const suIris = riga(sezione, "NGC 7023")
    expect(within(suIris).getByRole("button", { name: /Sh2-136/ }).textContent).toMatch(
      /non si sa/i,
    )
  })

  it("cliccando un candidato la risposta porta la chiave stabile, mai l id di riga", async () => {
    // Gli oggetti rimasti senza pose si cancellano, SQLite riusa gli id, e una risposta partita
    // prima di una corsa finirebbe addosso a un altro oggetto.
    aperta()
    const sezione = await vaiAgliOggetti()
    rispondiCliccando(sezione, "NGC 7023", /LDN 1174/)
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/review/apply"))
      expect(scritta?.corpo).toMatchObject({ objects: [{ key: "ngc-7023", slug: "ldn-1174" }] })
      const corpo = scritta?.corpo as { objects: Record<string, unknown>[] }
      expect(corpo.objects[0]?.id).toBeUndefined()
      // **Un bersaglio solo**, anche in questo verso: `toMatchObject` da solo passerebbe con un
      // `name` di troppo accanto allo slug, e il backend risponderebbe 422 annullando tutto.
      expect(corpo.objects[0]?.name).toBeUndefined()
    })
  })

  it("il campo a mano non e un vicolo cieco: dai candidati si torna indietro", async () => {
    // Aperto il campo, i candidati spariscono: senza una via di ritorno un clic sbagliato si
    // correggeva solo ricaricando la pagina. E' **la stessa lezione gia' pagata sui filtri**
    // (`SezioneFiltri.tsx`: "una scelta non e' un vicolo cieco finche' non si preme Applica"),
    // che nel ramo nuovo non era stata riportata.
    aperta()
    const sezione = await vaiAgliOggetti()
    const suIris = riga(sezione, "NGC 7023")
    fireEvent.click(within(suIris).getByRole("button", { name: /lo correggo/i }))
    expect(within(suIris).queryByRole("button", { name: /Nebulosa Iris/ })).toBeNull()
    fireEvent.click(within(suIris).getByRole("button", { name: /scegli un altro oggetto/i }))
    expect(within(suIris).getByRole("button", { name: /Nebulosa Iris/ })).toBeDefined()
  })

  it("un nome svuotato TOGLIE la risposta, invece di mandarne una vuota", async () => {
    // `ObjectEdit` pretende almeno un carattere: una stringa vuota tornerebbe 422 e -- essendo
    // l'Applica una transazione sola -- annullerebbe anche le risposte buone, con un messaggio
    // generico perche' un errore di validazione non porta un `code`. Finora la regola stava
    // **solo in un commento**.
    aperta()
    const sezione = await vaiAgliOggetti()
    const suCasa = riga(sezione, "Nebulosa di casa")
    fireEvent.click(within(suCasa).getByRole("button", { name: /lo correggo/i }))
    const campo = within(suCasa).getByLabelText(/nome per Nebulosa di casa/i)
    fireEvent.change(campo, { target: { value: "vdB 141" } })
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", false)
    fireEvent.change(campo, { target: { value: "" } })
    // Niente piu' in mano: l'Applica si spegne, quindi la risposta vuota non puo' nemmeno partire.
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
  })

  it("si corregge anche un oggetto su cui l app non ha dubbi", async () => {
    // "Cio' che avete trovato come `ngc-7023`, per me e' `ldn-1174`": una risposta e' una
    // **correzione**, non un lucchetto, e vale anche dove il cielo era sicuro. Senza questa
    // prova, chiudere il campo dietro "solo chi non ha candidati" restava verde.
    aperta()
    const sezione = await vaiAgliOggetti()
    const suM31 = riga(sezione, "M 31")
    fireEvent.click(within(suM31).getByRole("button", { name: /lo correggo/i }))
    fireEvent.change(within(suM31).getByLabelText(/nome per M 31/i), {
      target: { value: "NGC 224" },
    })
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/review/apply"))
      const corpo = scritta?.corpo as { objects: Record<string, unknown>[] } | undefined
      expect(corpo?.objects[0]).toMatchObject({ key: "m-31", name: "NGC 224" })
    })
  })

  it("il campo dice DI CHI e il nome che stai scrivendo", async () => {
    // Due righe aperte insieme danno due campi: se si chiamano tutti e due "Nome dell'oggetto"
    // non si distinguono, ne' per chi legge con uno schermo ne' per chi ci scrive dentro. E' la
    // ragione gia' scritta sui filtri, e vale qui identica.
    aperta()
    const sezione = await vaiAgliOggetti()
    fireEvent.click(
      within(riga(sezione, "Nebulosa di casa")).getByRole("button", { name: /lo correggo/i }),
    )
    fireEvent.click(within(riga(sezione, "M 31")).getByRole("button", { name: /lo correggo/i }))
    expect(screen.getByLabelText(/nome per Nebulosa di casa/i)).toBeDefined()
    expect(screen.getByLabelText(/nome per M 31/i)).toBeDefined()
  })

  it("dopo un rifiuto la ricevuta di prima non resta a schermo", async () => {
    // Il caso vero: un Applica riuscito, poi un secondo rifiutato. Se la ricevuta di prima
    // restasse, la pagina direbbe insieme "fatto" e "non e' stato scritto niente" -- e quella
    // di prima e' la piu' visibile delle due.
    aperta()
    const sezione = await vaiAgliOggetti()
    rispondiCliccando(sezione, "NGC 7023", /LDN 1174/)
    await screen.findByRole("status")
    cambia(mappa(PAGINA, RIFIUTO))
    // dopo un Applica riuscito le sezioni ripartono dalla pagina riletta: quella di prima non c'e' piu'
    rispondiCliccando(screen.getByRole("region", { name: /oggetti/i }), "NGC 7023", /LDN 1174/)
    await screen.findByRole("alert")
    expect(screen.queryByRole("status")).toBeNull()
  })

  it("chi non ha nessuna posa col cielo si risponde scrivendo", async () => {
    // Nessun candidato non e' un guasto: e' una posa senza cielo misurato. Senza la strada
    // scritta, quell'oggetto non avrebbe modo di essere corretto.
    aperta()
    const sezione = await vaiAgliOggetti()
    const suCasa = riga(sezione, "Nebulosa di casa")
    fireEvent.click(within(suCasa).getByRole("button", { name: /lo correggo/i }))
    fireEvent.change(within(suCasa).getByLabelText(/nome per Nebulosa di casa/i), {
      target: { value: "vdB 141" },
    })
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/review/apply"))
      const corpo = scritta?.corpo as { objects: Record<string, unknown>[] } | undefined
      expect(corpo?.objects[0]).toMatchObject({ key: "Nebulosa di casa", name: "vdB 141" })
      // **Un bersaglio solo**: il nome scritto esclude lo slug, o il backend risponde 422.
      expect(corpo?.objects[0]?.slug).toBeUndefined()
    })
  })

  it("l elenco porta le pose, le ore, e le pose senza tempo contate a parte", async () => {
    // Il backend manda i secondi e dichiara che a schermo si leggono in ore: qui si cambia unita'
    // e si formatta, non si deriva niente. Le pose che non dicono il tempo **non valgono zero**:
    // sommarle come tali direbbe un'integrazione piu' corta di quella vera.
    aperta()
    const sezione = await vaiAgliOggetti()
    expect(riga(sezione, "NGC 7023").textContent).toContain("60 frame")
    expect(riga(sezione, "NGC 7023").textContent).toContain("2,7 h")
    const suM31 = riga(sezione, "M 31")
    expect(suM31.textContent).toContain("10 h")
    expect(suM31.textContent).toContain("3 senza tempo")
  })

  it("chi non ha un tempo non scrive zero ore", async () => {
    // "0 h" sarebbe un dato: quelle dodici pose un tempo ce l'hanno, e' l'header che non lo dice.
    aperta()
    const sezione = await vaiAgliOggetti()
    const suCasa = riga(sezione, "Nebulosa di casa")
    expect(suCasa.textContent).toContain("12 senza tempo")
    expect(suCasa.textContent).not.toMatch(/0 h/)
  })

  it("una risposta rifiutata si dice per nome, e non butta via cio che hai scritto", async () => {
    // `POST /review/apply` e' **una transazione sola**: un bersaglio che il catalogo non conosce
    // fa ROLLBACK di tutto, anche dei filtri risposti bene. Un "non ha funzionato" generico
    // lascerebbe l'utente a non sapere ne' cosa e' stato scritto ne' cosa riparare -- e svuotare
    // l'accumulatore gli farebbe perdere risposte che il database non ha mai visto.
    aperta(PAGINA, { stato: 422, corpo: { detail: { code: "unknown_target" } } })
    const sezione = await vaiAgliOggetti()
    rispondiCliccando(sezione, "NGC 7023", /LDN 1174/)
    const avviso = await screen.findByRole("alert")
    expect(avviso.textContent).toMatch(/catalogo non lo conosce/i)
    expect(screen.queryByRole("status")).toBeNull()
    expect(
      within(riga(sezione, "NGC 7023")).getByRole("button", { name: /scegli un altro oggetto/i }),
    ).toBeDefined()
  })

  it("un clic sbagliato si corregge: si torna a scegliere", async () => {
    // Una scelta non e' un vicolo cieco finche' non si preme Applica. Stessa lezione dei filtri,
    // dove scelto un modello non si poteva piu' cambiare idea senza ricaricare.
    aperta()
    const sezione = await vaiAgliOggetti()
    const suIris = riga(sezione, "NGC 7023")
    fireEvent.click(within(suIris).getByRole("button", { name: /LDN 1174/ }))
    // La riga **dice** cosa hai risposto: collaudando dal vivo il bersaglio scelto si leggeva
    // attaccato ai conteggi ("60 pose 1 h IC 1133"), e sembrava un altro numero.
    expect(suIris.textContent).toMatch(/risposta: LDN 1174/)
    fireEvent.click(within(suIris).getByRole("button", { name: /scegli un altro oggetto/i }))
    expect(within(suIris).getByRole("button", { name: /Nebulosa Iris/ })).toBeDefined()
  })

  it("un oggetto senza nome si presenta con la sua chiave, non con un buco", async () => {
    // `ObjectOut.name` puo' essere nullo -- l'oggetto il cui header non porta `OBJECT` e che il
    // catalogo non ha ancora nominato. Senza questo ramo la riga comincerebbe con un vuoto e
    // l'etichetta del campo direbbe "Nome per ", cioe' per chi? Era l'unico ramo del file che
    // nessuna prova attraversava (misurato dall'auditor, 14/9/2026).
    aperta({
      ...PAGINA,
      objects: [
        {
          id: 11,
          key: "ldn-1174",
          name: null,
          slug: "ldn-1174",
          method: "coord_review",
          confidence: "low",
          frames: 8,
          integration_s: 3600,
          untimed: 0,
          confirmed: false,
          candidates: [],
        },
      ],
    })
    const sezione = await vaiAgliOggetti()
    const senzaNome = riga(sezione, "ldn-1174")
    fireEvent.click(within(senzaNome).getByRole("button", { name: /lo correggo/i }))
    expect(within(senzaNome).getByLabelText(/nome per ldn-1174/i)).toBeDefined()
  })

  it("un rifiuto che non porta un codice si dice lo stesso, invece di tacere", async () => {
    // Un errore di **forma** della richiesta arriva da FastAPI con `detail` lista, non oggetto:
    // niente `code` da tradurre. Senza la ricaduta sul messaggio generico la pagina resterebbe
    // muta proprio quando non si sa cosa sia andato storto.
    aperta(PAGINA, { stato: 422, corpo: { detail: [{ loc: ["body"], msg: "campo mancante" }] } })
    const sezione = await vaiAgliOggetti()
    rispondiCliccando(sezione, "NGC 7023", /LDN 1174/)
    const avviso = await screen.findByRole("alert")
    expect(avviso.textContent).toMatch(/non sono state applicate/i)
  })

  it("gli oggetti gia' visti stanno chiusi, e si aprono a pagine", async () => {
    // Non sono domande, e crescono con l'archivio (Marco, 27/9/2026): la pagina ne dice
    // quanti sono, e li chiede solo quando qualcuno li apre. Da li' si correggono come gli altri.
    const [dubbio, , certo] = PAGINA.objects
    const certi = { items: [certo], total: 3, limit: 50, offset: 0 }
    rispondi({
      "/api/v1/review/objects/settled": { stato: 200, corpo: certi },
      ...mappa({ ...PAGINA, objects: [dubbio], settled_objects: 3 }, RICEVUTA),
    })
    const sezione = await vaiAgliOggetti()
    expect(righe(sezione)).toHaveLength(1)
    expect(chiamate().some((u) => u.includes("/settled"))).toBe(false)

    fireEvent.click(within(sezione).getByRole("button", { name: /gia' visti \(3\)/i }))
    await waitFor(() => expect(righe(sezione)).toHaveLength(2))
    expect(righe(sezione)[1]?.textContent?.startsWith("M 31")).toBe(true)
    expect(within(sezione).queryByRole("button", { name: /gia' visti/i })).toBeNull()
    // il totale dice che ce ne sono altri: il bottone per chiederli c'e'
    expect(within(sezione).getByRole("button", { name: /mostrane altri/i })).toBeDefined()
    fireEvent.click(within(riga(sezione, "M 31")).getByRole("button", { name: /correggo/i }))
    expect(within(sezione).getByLabelText(/nome per m 31/i)).toBeDefined()
  })

  it("dopo l'Applica la riga torna chiusa, e non mostra cio' che la cache ricordava", async () => {
    // La sezione si rimonta dopo l'Applica, e una query spenta tiene i dati di prima senza
    // rileggerli: mostrarli vorrebbe dire righe vecchie accanto al bottone che le apre.
    const [dubbio, , certo] = PAGINA.objects
    rispondi({
      "/api/v1/review/objects/settled": {
        stato: 200,
        corpo: { items: [certo], total: 1, limit: 50, offset: 0 },
      },
      ...mappa({ ...PAGINA, objects: [dubbio], settled_objects: 1 }, RICEVUTA),
    })
    const sezione = await vaiAgliOggetti()
    fireEvent.click(within(sezione).getByRole("button", { name: /gia' visti \(1\)/i }))
    await waitFor(() => expect(righe(sezione)).toHaveLength(2))
    rispondiCliccando(sezione, "NGC 7023", /LDN 1174/)
    const dopo = await screen.findByRole("button", { name: /gia' visti \(1\)/i })
    expect(righe(dopo.closest("section") as HTMLElement)).toHaveLength(1)
  })

  it("la sezione c'e' anche quando restano solo gli oggetti gia' visti", async () => {
    aperta({ ...PAGINA, objects: [], settled_objects: 2, to_confirm: 0 })
    const sezione = await vaiAgliOggetti()
    expect(within(sezione).getByRole("button", { name: /gia' visti \(2\)/i })).toBeDefined()
  })

  it("una sezione senza domande non si vede", async () => {
    aperta({ ...PAGINA, objects: [], settled_objects: 0, to_confirm: 0 })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    await screen.findByRole("heading", { name: /da confermare/i })
    expect(screen.queryByRole("region", { name: /oggetti/i })).toBeNull()
  })
})
