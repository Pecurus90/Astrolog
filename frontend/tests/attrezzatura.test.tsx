// @vitest-environment jsdom
/**
 * La pagina **Attrezzatura**: con cosa hai ripreso, e quanto.
 *
 * La regola che la pagina non deve tradire e' una sola, e viene dal contratto: **si mostra solo
 * cio' che l'app possiede davvero**. Dove un numero non c'e' -- le ore di una montatura, la scala
 * di un corredo di cui non si sono ancora riconosciute le pose -- si scrive **perche'**, mai uno zero
 * (`docs/domini/attrezzatura.md`).
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  CORREDO,
  FILTRO,
  MONTATURA,
  NUMERI,
  OTTICA,
  apriAttrezzatura,
  attrezzatura,
  campo,
  carta,
  parte,
  parti,
  vedi,
} from "./attrezzatura-banco"
import { SALUTE, SPINA, STANOTTE, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"

afterEach(pulisci)

describe("l Attrezzatura", () => {
  it("elenca i pezzi che possiedi, raccolti per genere", async () => {
    attrezzatura()
    await apriAttrezzatura()

    // il setup piu' usato si apre da solo; i gruppi si scelgono dall'indice
    expect(await carta()).toBeDefined()
    const telescopi = await vedi(/telescopi/i)
    expect(within(telescopi).getByText(/TS 130 APO/)).toBeDefined()
    const montature = await vedi(/montature/i)
    expect(within(montature).getByText(/EQ6-R/)).toBeDefined()
    expect(await vedi(/filtri/i)).toBeDefined()
  })

  it("l indice mostra i setup a carte, con ore, focale e le parti da indicare", async () => {
    attrezzatura()
    await apriAttrezzatura()

    const indice = await screen.findByRole("navigation", { name: /indice dell'attrezzatura/i })
    const carta = within(indice).getByRole("link", { name: /il grande/i })
    expect(carta.textContent).toContain("10 h") // 36.000 s
    expect(carta.textContent).toContain("910 mm")
    expect(carta.textContent).toContain("8 da indicare")
    // dieci tacche, due piene: ottica e camera
    expect(carta.querySelectorAll("[data-pieno]")).toHaveLength(10)
    expect(carta.querySelectorAll('[data-pieno="true"]')).toHaveLength(2)
    // il setup aperto e' segnato nell'indice, non a colori soltanto
    expect(carta.getAttribute("aria-current")).toBe("true")
  })

  it("dopo un salvataggio che rimette dei frame in coda, la pagina lo dice e si chiude", async () => {
    attrezzatura(
      {},
      { "PUT /api/v1/gear/rigs/10/parts/mount": { stato: 200, corpo: { id: 10, requeued: 120, run_started: true } } },
    )
    await apriAttrezzatura()
    fireEvent.click(within(await parte("mount")).getByRole("button", { name: /^seleziona montatura$/i }))
    fireEvent.change(screen.getByRole("combobox", { name: /^montatura/i }), { target: { value: "2" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))

    const detto = await screen.findByText("120 frame da rielaborare")
    const riga = detto.closest("[aria-live]") as HTMLElement
    expect(riga.getAttribute("aria-live")).toBe("polite")
    fireEvent.click(within(riga).getByRole("button", { name: /^chiudi$/i }))
    expect(screen.queryByText(/frame da rielaborare/)).toBeNull()
  })

  it("un genere senza pezzi non compare affatto", async () => {
    // Otto titoli vuoti sarebbero l'elenco di cio' che **non** hai. Visto verde togliendo la
    // riga che nasconde i gruppi vuoti: senza questa prova, quella riga era un commento.
    attrezzatura({ instruments: [OTTICA] })
    await apriAttrezzatura()

    const indice = await screen.findByRole("navigation", { name: /indice dell'attrezzatura/i })
    expect(within(indice).getByRole("link", { name: /telescopi/i })).toBeDefined()
    expect(within(indice).queryByRole("link", { name: /montature/i })).toBeNull()
    expect(within(indice).queryByRole("link", { name: /focheggiatori/i })).toBeNull()
  })

  it("un pezzo e un filtro dicono le loro ore, con la barra", async () => {
    // tavola v82 `usoT` e contratto: nella riga solo le ore, la barra dall'API (`bar_pct`)
    attrezzatura()
    await apriAttrezzatura()

    expect((await carta()).textContent).toContain("10 h") // 36.000 s, gia' sommate dal backend
    const telescopi = await vedi(/telescopi/i)
    expect(telescopi.textContent).toContain("10 h")
    expect(telescopi.textContent).not.toContain("M 31")
    const barra = telescopi.querySelector<HTMLElement>('[data-an="barra"]')
    expect(barra?.style.width).toBe("100%")
    expect((await vedi(/filtri/i)).textContent).toContain("5 h")
  })

  it("una montatura che nessun setup porta apre la scelta sul setup senza montatura", async () => {
    attrezzatura({ instruments: [OTTICA, { ...MONTATURA, rig_for_mount: 10 }] })
    await apriAttrezzatura()

    const montature = await vedi(/montature/i)
    expect(montature.textContent).toContain("non associata a un setup")
    fireEvent.click(within(montature).getByRole("button", { name: /^seleziona montatura$/i }))

    // il setup aperto, la sua montatura gia' su quella da cui vengo
    expect(await carta()).toBeDefined()
    expect((screen.getByRole("combobox", { name: /^montatura/i }) as HTMLSelectElement).value).toBe("2")

    // Annulla consuma la proposta: riaperta, la parte dice cio' che il setup ha davvero
    fireEvent.click(screen.getByRole("button", { name: /^annulla$/i }))
    fireEvent.click(within(await parte("mount")).getByRole("button", { name: /^seleziona montatura$/i }))
    expect((screen.getByRole("combobox", { name: /^montatura/i }) as HTMLSelectElement).value).not.toBe("2")
  })

  it("un pezzo non ancora contato dice che si sta contando, non che i file tacciono", async () => {
    // Alla prima scansione una camera nasce a meta' giro e i suoi numeri arrivano a fine giro:
    // "i tuoi file non dicono quale hai usato" sarebbe falso, e lo dice gia' una ruota che nessun
    // file nomina.
    attrezzatura({
      instruments: [
        { ...OTTICA, frames: null, integration_s: null, untimed: null, nights: null, counted: false },
        { ...MONTATURA, id: 7, kind: "filter_wheel", name: "EFW", payload_kg: null, no_hours: "files_silent" },
      ],
    })
    await apriAttrezzatura()

    const telescopi = await vedi(/telescopi/i)
    expect(telescopi.textContent).toMatch(/conteggio in corso/)
    expect(telescopi.textContent).not.toMatch(/non indicato nei file/)
    expect((await vedi(/ruote/i)).textContent).toMatch(/non indicato nei file/)
  })

  it("il pixel ricavato dal cielo si dice ricavato, e quello dei file vince", async () => {
    // Marco, 23/9/2026: quando i file non dicono il pixel, si ricava dalla scala misurata. Si dice
    // da dove viene, perche' non e' la stessa certezza; e se i file lo dicono, si legge quello.
    const camera = { ...OTTICA, id: 5, kind: "camera", name: "ATR2600M", aperture_mm: null, focal_mm: null }
    attrezzatura({
      instruments: [
        { ...camera, pixel_from_sky_um: 3.8 },
        { ...camera, id: 6, name: "ASI2600MM", pixel_size_um: 3.76, pixel_from_sky_um: 3.8 },
      ],
    })
    await apriAttrezzatura()

    const camere = await vedi(/^camere/i)
    expect(within(camere).getByText(/ATR2600M/).closest("li")?.textContent).toMatch(
      /pixel 3,8 \u00b5m\s*\(calcolato\)/,
    )
    const detto = within(camere).getByText(/ASI2600MM/).closest("li")?.textContent
    expect(detto).toMatch(/pixel 3,76 \u00b5m/)
    expect(detto).not.toMatch(/calcolato/)
  })

  it("un setup dice quanto cielo inquadra", async () => {
    attrezzatura()
    await apriAttrezzatura()

    const sezione = await campo()
    expect(sezione.textContent).toContain("1,50° × 1,00°")
    expect(sezione.textContent).toContain("0,85 arcosecondi per pixel · ricavati dal cielo")
  })

  it("il campo si confronta con gli altri setup e con la Luna, in percento dall'API", async () => {
    const piccolo = { ...CORREDO, id: 11, name: null, title: "RedCat · ASI2600MM" }
    attrezzatura({
      rigs: [CORREDO, piccolo],
      fields: [
        { rig_id: 11, width_pct: 87, height_pct: 87.3 },
        { rig_id: 10, width_pct: 38.8, height_pct: 38.8 },
      ],
      moon_pct: 13.6,
    })
    await apriAttrezzatura()

    const confronto = within(await campo()).getByRole("img", {
      name: "Il campo di Il grande a confronto con gli altri setup e la Luna piena",
    })
    const riquadri = [...confronto.querySelectorAll<HTMLElement>(".al-attr__strato-1")]
    expect(riquadri.map((r) => [r.textContent, r.style.width])).toEqual([
      ["RedCat · ASI2600MM", "87%"],
      ["Il grande", "38.8%"],
    ])
    expect(confronto.querySelector<HTMLElement>(".al-attr__strato-3")?.style.width).toBe("13.6%")
    expect(confronto.textContent).toContain("Luna piena, per misura")
  })

  it("i dati del setup dicono ogni conto, o cosa gli manca", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, numbers: NUMERI }] })
    await apriAttrezzatura()

    const dati = await screen.findByRole("region", { name: /^dati del setup$/i })
    const riga = (k: string) => dati.querySelector(`[data-conto="${k}"]`)?.textContent ?? ""
    expect(riga("focal_ratio")).toBe("Rapporto focalef/7focale effettiva 910 mm")
    expect(riga("sampling")).toContain("0,85″/px")
    expect(riga("sampling")).toContain("ottimo con seeing fra 1,7 e 2,4″")
    // due decimali, che cadono solo se sono zero (tavola `VG`): 4,40 e non 4,4
    expect(riga("field")).toContain("4,40° × 2,99°")
    expect(riga("sensor_size")).toContain("manca la risoluzione della camera")
    expect(riga("coverage")).toContain("manca il cerchio d'immagine dell'ottica")
    expect(riga("guide_scale")).toContain("manca la guida")
    expect(riga("backfocus")).toContain("55,5 mm")
    expect(riga("backfocus")).toContain("+0,5 mm, in tolleranza")
    expect(riga("backfocus")).toContain("richiesto 55 mm dall'ottica · tolleranza ±1 mm")
    expect(riga("load")).toContain("manca la montatura")
  })

  it("l anello dei filtri e' in proporzione ai frame, coi nomi accanto", async () => {
    const filtro = (name: string, passband: string, ring_from: number, ring_to: number) => ({
      kind: "filter", id: 3, name, frames: 1, chosen: false, passband, ring_from, ring_to,
    })  // prettier-ignore
    attrezzatura({ rigs: [{ ...CORREDO, parts: [filtro("Ha", "HA", 0, 75), filtro("OIII", "OIII", 75, 100)] }] })
    await apriAttrezzatura()

    const sezione = await screen.findByRole("region", { name: /^filtri$/i })
    const anello = within(sezione).getByRole("img", { name: "Filtri, in proporzione ai frame: Ha, OIII" })
    expect(anello.style.background).toContain("conic-gradient")
    expect(anello.textContent).toBe("2filtri")
  })

  it("un setup di cui non si sa quanto inquadra non scrive una scala", async () => {
    // La riga tace e dice perche': un numero preso dalla scheda sarebbe giusto sulla carta e
    // sbagliato nel cielo, e nessuno potrebbe accorgersene. Il caso non e' solo "non ha mai
    // ripreso": visto dal vivo, un corredo con otto pose **non ancora riconosciute** non ha una
    // scala, e dirgli "dopo la prima ripresa" sarebbe falso.
    attrezzatura({
      rigs: [
        {
          ...CORREDO,
          frames: 0,
          integration_s: 0,
          nights: 0,
          objects: [],
          scale_arcsec_px: null,
          width_deg: null,
          height_deg: null,
        },
      ],
    })
    await apriAttrezzatura()

    const sezione = await campo()
    expect(sezione.textContent).toMatch(/campo non ancora disponibile/i)
    expect(sezione.textContent).not.toMatch(/arcosecondi/i)
  })

  it("scelgo la montatura di un setup dalla sua scheda", async () => {
    attrezzatura(
      {},
      { "PUT /api/v1/gear/rigs/10/parts/mount": { stato: 200, corpo: { id: 10, requeued: 120, run_started: true } } },
    )
    await apriAttrezzatura()
    fireEvent.click(within(await parte("mount")).getByRole("button", { name: /^seleziona montatura$/i }))
    // la tendina, non la regione: anche il modulo si chiama "Montatura di ..."
    fireEvent.change(screen.getByRole("combobox", { name: /^montatura/i }), { target: { value: "2" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/rigs/10/parts/mount")
    expect(scritture()[0]?.corpo).toEqual({ piece_id: 2 })
  })

  it("un setup dice tutte le parti che i suoi frame hanno usato, ognuna coi suoi frame", async () => {
    attrezzatura({
      rigs: [
        {
          ...CORREDO,
          parts: [
            { kind: "filter_wheel", id: 7, name: "ZWO EFW", frames: 100, chosen: false },
            { kind: "filter_wheel", id: 8, name: "Ruota vecchia", frames: 20, chosen: false },
            { kind: "focuser", id: 9, name: "EAF", frames: 120, chosen: false },
            { kind: "software", id: null, name: "N.I.N.A.", frames: 119, chosen: false },
            { kind: "software", id: null, name: "ASIAIR", frames: 1, chosen: false },
            { kind: "filter", id: 3, name: "Ha 3nm", frames: 60, chosen: false },
          ],
          // le tacche le scrive l'API dalle parti
          slots: CORREDO.slots.map((s) => ({
            ...s,
            filled: s.filled || ["filter_wheel", "focuser", "software"].includes(s.kind),
          })),
        },
      ],
    })
    await apriAttrezzatura()
    // tutte, nell'ordine dell'API: due ruote e due programmi restano due; i filtri stanno
    // nell'anello, non fra le parti
    expect((await parte("filter_wheel")).textContent).toBe(
      "ruota portafiltriZWO EFW ↗100 frameRuota vecchia ↗20 frameSeleziona",
    )
    expect((await parte("focuser")).textContent).toContain("EAF ↗120 frame")
    // il programma non e' un pezzo: non si apre, e lo dicono solo i file
    const programma = await parte("software")
    expect(programma.textContent).toBe("programma di ripresaN.I.N.A.119 frameASIAIR1 frame")
    expect(within(programma).queryByRole("link")).toBeNull()
    expect(within(programma).queryByRole("button")).toBeNull()
    expect((await parti()).textContent).not.toContain("Ha 3nm")
  })

  it("una parte vuota dice da indicare, e le parti che mancano si contano", async () => {
    attrezzatura()
    await apriAttrezzatura()
    expect((await parti()).querySelector("header")?.textContent).toBe("Parti○8 da indicare")
    expect((await parte("mount")).textContent).toContain("○da indicare")
  })

  it("un pezzo di una parte si apre fra i componenti, la sua riga segnata", async () => {
    attrezzatura()
    await apriAttrezzatura()
    fireEvent.click(within(await parte("optics")).getByRole("link", { name: "Apri TS 130 APO fra i componenti" }))
    const telescopi = await screen.findByRole("list", { name: /telescopi/i })
    expect(within(telescopi).getByText(/TS 130 APO/).closest("li")?.getAttribute("aria-current")).toBe("true")
  })

  it("una parte che hai scelto tu dice che e' scelta, al posto dei frame", async () => {
    attrezzatura({
      rigs: [
        {
          ...CORREDO,
          parts: [
            { kind: "mount", id: 2, name: "EQ6-R", frames: 120, chosen: false },
            { kind: "reducer", id: 30, name: "0,8x", frames: 120, chosen: true },
            { kind: "guide_scope", id: 31, name: "30 mm f/4", frames: 0, chosen: true },
          ],
        },
      ],
    })
    await apriAttrezzatura()
    expect((await parte("mount")).textContent).toContain("EQ6-R ↗120 frame")
    expect((await parte("reducer")).textContent).toContain("0,8x ↗(scelta a mano)")
    expect((await parte("guide")).textContent).toContain("30 mm f/4 ↗(scelta a mano)")
    // la montatura letta dai file dice su cosa sta il setup (tavola `mont`, 310)
    expect((await carta()).textContent).toContain("su EQ6-R")
    // ma non e' "la tua": la tendina parte vuota
    fireEvent.click(within(await parte("mount")).getByRole("button", { name: /^seleziona montatura$/i }))
    expect((screen.getByRole("combobox", { name: /^montatura/i }) as HTMLSelectElement).value).toBe("")
  })

  it("un setup dice su che montatura sta, e la voce vuota torna ai file", async () => {
    attrezzatura(
      { rigs: [{ ...CORREDO, parts: [{ kind: "mount", id: 2, name: "EQ6-R", frames: 0, chosen: true }] }] },
      { "PUT /api/v1/gear/rigs/10/parts/mount": { stato: 200, corpo: { id: 10, requeued: 120, run_started: true } } },
    )
    await apriAttrezzatura()
    expect((await carta()).textContent).toContain("su EQ6-R")
    fireEvent.click(within(await parte("mount")).getByRole("button", { name: /^seleziona montatura$/i }))
    fireEvent.change(screen.getByRole("combobox", { name: /^montatura/i }), { target: { value: "" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ piece_id: null })
  })

  it("senza montature da scegliere il modulo propone di aggiungerne una", async () => {
    attrezzatura({ instruments: [OTTICA] })
    await apriAttrezzatura()
    fireEvent.click(within(await parte("mount")).getByRole("button", { name: /^seleziona montatura$/i }))
    const modulo = screen.getByRole("group", { name: "Montatura di Il grande" })
    // niente da salvare: solo Annulla e la via per scriverne una
    expect(within(modulo).queryByRole("button", { name: /salva/i })).toBeNull()
    fireEvent.click(within(modulo).getByRole("button", { name: /aggiungine uno/i }))
    expect(((await screen.findByLabelText(/^tipo$/i)) as HTMLSelectElement).value).toBe("mount")
  })

  it("i distanziali si scelgono insieme, e partono tutti", async () => {
    const distanziale = { ...MONTATURA, id: 40, kind: "spacer", name: "M42 0,5 mm" }
    attrezzatura(
      { instruments: [OTTICA, MONTATURA, distanziale, { ...distanziale, id: 41, name: "M48 7,5 mm" }] },
      { "PUT /api/v1/gear/rigs/10/spacers": { stato: 200, corpo: { id: 10, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    fireEvent.click(within(await parte("spacer")).getByRole("button", { name: /^seleziona distanziali$/i }))
    fireEvent.click(screen.getByRole("checkbox", { name: /M42 0,5 mm/ }))
    fireEvent.click(screen.getByRole("checkbox", { name: /M48 7,5 mm/ }))
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ piece_ids: [40, 41] })
  })

  it("la guida si sceglie fra ottiche di guida e guide fuori asse, col tipo del pezzo", async () => {
    const cercatore = { ...MONTATURA, id: 50, kind: "guide_scope", name: "30 mm f/4" }
    const oag = { ...MONTATURA, id: 51, kind: "oag", name: "OAG-L" }
    const scritto = { stato: 200, corpo: { id: 10, requeued: 0, run_started: false } }
    attrezzatura(
      {
        instruments: [OTTICA, cercatore, oag],
        rigs: [{ ...CORREDO, parts: [{ kind: "guide_scope", id: 50, name: "30 mm f/4", frames: 0, chosen: true }] }],
      },
      { "PUT /api/v1/gear/rigs/10/parts/guide_scope": scritto, "PUT /api/v1/gear/rigs/10/parts/oag": scritto },
    )
    await apriAttrezzatura()
    fireEvent.click(within(await parte("guide")).getByRole("button", { name: /^seleziona guida$/i }))
    // il riduttore e la guida non li nomina nessun file: niente «vuoto: dai file»
    fireEvent.change(screen.getByRole("combobox", { name: /^guida$/i }), { target: { value: "51" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    // una scrittura: l'altra guida la toglie il backend
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture().map((s) => [s.url.split("/").pop(), s.corpo])).toEqual([["oag", { piece_id: 51 }]])
  })

  it("svuotata, la guida che avevi scelto torna ai file", async () => {
    const cercatore = { ...MONTATURA, id: 50, kind: "guide_scope", name: "30 mm f/4" }
    attrezzatura(
      {
        instruments: [OTTICA, cercatore],
        rigs: [{ ...CORREDO, parts: [{ kind: "guide_scope", id: 50, name: "30 mm f/4", frames: 0, chosen: true }] }],
      },
      { "PUT /api/v1/gear/rigs/10/parts/guide_scope": { stato: 200, corpo: { id: 10, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    fireEvent.click(within(await parte("guide")).getByRole("button", { name: /^seleziona guida$/i }))
    fireEvent.change(screen.getByRole("combobox", { name: /^guida$/i }), { target: { value: "" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/parts/guide_scope")
    expect(scritture()[0]?.corpo).toEqual({ piece_id: null })
  })

  it("senza cambiare niente Salva chiude, e non rimanda i frame a rielaborare", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, parts: [{ kind: "mount", id: 2, name: "EQ6-R", frames: 0, chosen: true }] }] })
    await apriAttrezzatura()
    fireEvent.click(within(await parte("mount")).getByRole("button", { name: /^seleziona montatura$/i }))
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(screen.queryByRole("group", { name: /^montatura di/i })).toBeNull())
    expect(scritture()).toHaveLength(0)
  })

  it("rinomina senza nome non salva, e dice perche'", async () => {
    attrezzatura({ rigs: [{ ...CORREDO, name: null, title: "TS 130 APO · ASI2600MM" }] })
    await apriAttrezzatura()
    const nome = await carta(/TS 130 APO · ASI2600MM/)
    fireEvent.click(within(nome).getByRole("button", { name: /^rinomina/i }))
    const modulo = screen.getByRole("group", { name: "Nome di TS 130 APO · ASI2600MM" })
    expect(within(modulo).getByRole("button", { name: /salva/i }).getAttribute("aria-disabled")).toBe("true")
    expect(modulo.textContent).toContain("Per salvare serve il nome.")
  })

  it("una montatura portata dalle pose ha le sue ore", async () => {
    attrezzatura({
      instruments: [OTTICA, { ...MONTATURA, frames: 120, integration_s: 36000, untimed: 0, nights: 7, no_hours: null }],
    })
    await apriAttrezzatura()
    const montature = await vedi(/montature/i)
    expect(montature.textContent).not.toMatch(/non associata a un setup/i)
    expect(montature.textContent).toMatch(/10 h/)
  })

  it("una montatura che nessuna posa porta, in un archivio dove altre ce l'hanno, non dice zero", async () => {
    attrezzatura({ instruments: [OTTICA, { ...MONTATURA, frames: 0, integration_s: 0, untimed: 0, nights: 0 }] })
    await apriAttrezzatura()
    const montature = await vedi(/montature/i)
    expect(montature.textContent).toMatch(/non associata a un setup/i)
  })

  it("un riduttore e una guida che nessun setup porta lo dicono, ognuno col suo genere", async () => {
    attrezzatura({
      instruments: [
        OTTICA,
        { ...MONTATURA, id: 8, kind: "reducer", name: "0,8x", payload_kg: null },
        { ...MONTATURA, id: 9, kind: "guide_scope", name: "30 mm f/4", payload_kg: null },
      ],
    })
    await apriAttrezzatura()
    const riduttori = await vedi(/riduttori/i)
    expect(riduttori.textContent).toMatch(/non associato a un setup/i)
    expect((await vedi(/^guide\s*\d/i, /^guide$/i)).textContent).toMatch(/non associata a un setup/i)
  })

  it("la montatura dice perche' non ha ore", async () => {
    attrezzatura()
    await apriAttrezzatura()

    const montature = await vedi(/montature/i)
    expect(montature.textContent).toMatch(/non associata a un setup/i)
    expect(montature.textContent).not.toMatch(/\b0 h\b/)
    expect(montature.textContent).toContain("20") // la scheda pero' si legge: carico 20 kg
  })

  it("a mani vuote dice cosa fare, non nessun risultato", async () => {
    attrezzatura({ instruments: [], rigs: [], filters: [] })
    await apriAttrezzatura()

    expect(await screen.findByText(/^nessuna attrezzatura$/i)).toBeDefined()
    expect(screen.getByRole("button", { name: /^aggiungi cartella$/i })).toBeDefined()
    // «Aggiungi strumento» resta sopra anche a mani vuote (tavola v82, stato Vuota)
    expect(screen.getByRole("button", { name: /^aggiungi strumento$/i })).toBeDefined()
  })

  it("se l attrezzatura non si legge lo dice, invece di sembrare vuota", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/gear": { stato: 500, corpo: { detail: "boom" } },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    await apriAttrezzatura()

    expect(await screen.findByText(/attrezzatura non disponibile/i)).toBeDefined()
    expect(screen.getByRole("button", { name: /^riprova$/i })).toBeDefined()
  })
})

describe("i gesti sull attrezzatura", () => {
  /** Apre la scheda di un pezzo dalla sua riga: e' la strada dell'utente, che vede l'errore
   *  mentre guarda il pezzo e lo corregge li'. */
  async function apriLaScheda(genere: RegExp, nomeDelPezzo: RegExp) {
    const elenco = await vedi(genere)
    const riga = within(elenco)
      .getAllByRole("listitem")
      .find((l) => nomeDelPezzo.test(l.querySelector(".al-attr__testo-26")?.textContent ?? ""))
    fireEvent.click(within(riga as HTMLElement).getByRole("button", { name: /^modifica/i }))
  }

  it("correggo la scheda di un pezzo dalla pagina in cui lo guardo", async () => {
    attrezzatura(
      {},
      {
        "PATCH /api/v1/gear/instruments/1": { stato: 200, corpo: { id: 1, requeued: 0, run_started: false } },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /TS 130 APO/)

    fireEvent.change(screen.getByLabelText(/apertura/i), { target: { value: "132" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))

    await waitFor(() => expect(scritture()).toHaveLength(1))
    const mandato = scritture()[0]
    expect(mandato?.url).toContain("/api/v1/gear/instruments/1")
    expect(mandato?.metodo).toBe("PATCH")
    // **Per intero, non a sottoinsieme**: la regola e' che un campo non toccato NON parte --
    // rimandare cio' che l'app ha letto dai file lo farebbe diventare una tua dichiarazione. Con
    // `toMatchObject` una scheda rimandata tutta intera resterebbe verde.
    expect(mandato?.corpo).toEqual({ aperture_mm: 132 })
  })

  it("la scheda chiede i campi del genere che sta guardando, e li decide il backend", async () => {
    // La portata e' della montatura, l'apertura del telescopio: la pagina non tiene un secondo
    // elenco di quali campi valgono per quale genere, lo manda l'API con ogni pezzo.
    attrezzatura()
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)

    expect(screen.getByLabelText(/carico con contrappeso/i)).toBeDefined()
    expect(screen.queryByLabelText(/apertura/i)).toBeNull()
  })

  it("cio' che scelgo in una scheda resta scelto, e parte solo quello", async () => {
    // Visto dal vivo: la scelta del colore tornava indietro appena la si mollava, perche'
    // mostrava il valore **letto dai file** invece di quello appena scelto.
    attrezzatura(
      { instruments: [{ ...OTTICA, id: 4, kind: "camera", name: "ASI2600MM", aperture_mm: null, focal_mm: null }] },
      { "PATCH /api/v1/gear/instruments/4": { stato: 200, corpo: { id: 4, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/^camere/i, /ASI2600MM/)

    const mono = within(screen.getByRole("radiogroup", { name: /tipo di sensore/i })).getByRole("radio", { name: /^mono/i })
    fireEvent.click(mono)
    expect(mono.getAttribute("aria-checked")).toBe("true")
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ camera_type: "mono" })
  })

  it("la risoluzione si scrive in un campo, larghezza per altezza, e il campo dice da dove viene", async () => {
    const camera = { ...OTTICA, id: 4, kind: "camera", name: "ASI2600MM", aperture_mm: null, focal_mm: null }
    attrezzatura(
      { instruments: [{ ...camera, pixel_size_um: 3.76, from_files: ["pixel_size_um"] }] },
      { "PATCH /api/v1/gear/instruments/4": { stato: 200, corpo: { id: 4, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/^camere/i, /ASI2600MM/)

    const pixel = screen.getByLabelText(/^pixel/i)
    expect(pixel.closest("div")?.textContent).toContain("dai file")
    fireEvent.change(pixel, { target: { value: "3,8" } })
    expect(pixel.closest("div")?.textContent).toContain("inserito")
    fireEvent.change(screen.getByLabelText(/^risoluzione/i), { target: { value: "6248 × 4176" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ pixel_size_um: 3.8, width_px: 6248, height_px: 4176 })
  })

  it("il bias si scrive per offset, uno per campo", async () => {
    const camera = { ...OTTICA, id: 4, kind: "camera", name: "ASI2600MM", aperture_mm: null, focal_mm: null }
    attrezzatura(
      {
        instruments: [
          {
            ...camera,
            biases: [
              { offset: 30, bias_adu: null, frames: 1 },
              { offset: 50, bias_adu: 500, frames: 2 },
            ],
          },
        ],
      },
      {
        "PATCH /api/v1/gear/instruments/4": { stato: 200, corpo: { id: 4, requeued: 0, run_started: false } },
        "PUT /api/v1/gear/instruments/4/biases": { stato: 200, corpo: { offset: 30, bias_adu: 480, frames: 1 } },
      },
    )
    await apriAttrezzatura()
    const camere = await vedi(/^camere/i)
    expect(camere.textContent).toContain("bias 500 ADU, offset 50")
    await apriLaScheda(/^camere/i, /ASI2600MM/)

    fireEvent.change(screen.getByLabelText("Bias (ADU), offset 30"), { target: { value: "480" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(2))
    // prima il bias: il PATCH puo' far partire il lavoro, e allora il bias aspetterebbe (409)
    expect(scritture()[0]?.url).toContain("/api/v1/gear/instruments/4/biases")
    expect(scritture()[0]?.corpo).toEqual({ offset: 30, bias_adu: 480 })
  })

  it("senza nome non si salva, e il perche' e' accanto a Salva", async () => {
    attrezzatura()
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /TS 130 APO/)
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "  " } })
    expect(screen.getByRole("button", { name: /salva/i }).getAttribute("aria-disabled")).toBe("true")
    expect(screen.getByText("Per salvare serve il nome.")).toBeDefined()
  })

  it("unisco due grafie dello stesso pezzo, solo fra quelle che l'API offre", async () => {
    const altra = { ...OTTICA, id: 5, name: "TS130APO", mergeable_into: [1] }
    attrezzatura(
      { instruments: [{ ...OTTICA, mergeable_into: [5] }, altra, MONTATURA] },
      { "PATCH /api/v1/gear/instruments/1": { stato: 200, corpo: { id: 1, requeued: 3, run_started: true } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /^TS 130 APO/)
    fireEvent.change(screen.getByLabelText(/^unisci a/i), { target: { value: "5" } })
    // scelta l'unione, la scheda si nasconde: non partirebbe, e si perderebbe in silenzio
    expect(screen.queryByLabelText(/apertura/i)).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ merge_into: 5 })
  })

  it("scelgo un'unione e torno indietro: parte cio' che vedo, non cio' che avevo scritto prima", async () => {
    // Il nome riappare col valore di prima: se la scritta tenesse "Pippo", il pezzo verrebbe
    // rinominato senza che a video si veda.
    const altra = { ...OTTICA, id: 5, name: "TS130APO", mergeable_into: [1] }
    attrezzatura(
      { instruments: [{ ...OTTICA, mergeable_into: [5] }, altra, MONTATURA] },
      { "PATCH /api/v1/gear/instruments/1": { stato: 200, corpo: { id: 1, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /^TS 130 APO/)
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "Pippo" } })
    const unione = screen.getByLabelText(/^unisci a/i)
    fireEvent.change(unione, { target: { value: "5" } })
    fireEvent.change(unione, { target: { value: "" } })
    expect(screen.getByLabelText(/^nome/i)).toHaveProperty("value", "TS 130 APO")
    fireEvent.change(screen.getByLabelText(/apertura/i), { target: { value: "132" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ aperture_mm: 132 })
  })

  it("un pezzo senza unioni possibili non offre la tendina", async () => {
    attrezzatura()
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)
    expect(screen.queryByLabelText(/^unisci a/i)).toBeNull()
  })

  it("do un nome a un setup", async () => {
    attrezzatura(
      {},
      { "PATCH /api/v1/gear/rigs/10": { stato: 200, corpo: { id: 10, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    const nome = await carta()
    fireEvent.click(within(nome).getByRole("button", { name: "Rinomina Il grande" }))
    // la casella, non la regione: anche la scheda ora si chiama "Nome di ..."
    fireEvent.change(screen.getByRole("textbox", { name: /^nome/i }), { target: { value: "Il piccolo" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/rigs/10")
    expect(scritture()[0]?.corpo).toEqual({ name: "Il piccolo" })
  })

  it("correggo la marca di un filtro fra quelle gia' scritte, o ne scrivo una nuova", async () => {
    attrezzatura(
      { brands: ["Baader"] },
      { "PATCH /api/v1/gear/filters/3": { stato: 200, corpo: { id: 3, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    const marca = screen.getByLabelText(/^marca/i)
    expect(within(marca).getByRole("option", { name: "Baader" })).toBeDefined()
    fireEvent.change(marca, { target: { value: "__altra__" } })
    fireEvent.change(screen.getByLabelText(/^nuova marca/i), { target: { value: "Antlia" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/filters/3")
    expect(scritture()[0]?.corpo).toEqual({ brand: "Antlia" })
  })

  it("le bande di un filtro si scrivono con la larghezza, e senza bande non si salva", async () => {
    attrezzatura(
      {},
      { "PATCH /api/v1/gear/filters/3": { stato: 200, corpo: { id: 3, requeued: 60, run_started: true } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    fireEvent.click(within(screen.getByRole("radiogroup", { name: /quante bande/i })).getByRole("radio", { name: "2" }))
    fireEvent.change(screen.getByLabelText("Banda 2"), { target: { value: "OIII" } })
    fireEvent.change(screen.getAllByLabelText(/larghezza/i)[1] as HTMLElement, { target: { value: "3,5" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({
      bands: [
        { band: "HA", width_nm: 3 },
        { band: "OIII", width_nm: 3.5 },
      ],
    })
    expect(await screen.findByText("60 frame da rielaborare")).toBeDefined()
  })

  it("un filtro che l'app conosce dal nome mostra la sua banda e si rinomina senza scriverla", async () => {
    // visto dal collaudatore, 14/11: senza bande scritte Salva restava spento
    attrezzatura(
      { filters: [{ ...FILTRO, passband: "L", bands: [], name: "Lum" }] },
      { "PATCH /api/v1/gear/filters/3": { stato: 200, corpo: { id: 3, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    expect(within(await vedi(/filtri/i)).getByText("L")).toBeDefined()
    await apriLaScheda(/filtri/i, /^Lum/)
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "Luminanza" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ name: "Luminanza" })
  })

  it("il nome di un altro filtro si dice con le parole dei filtri", async () => {
    attrezzatura(
      {},
      { "PATCH /api/v1/gear/filters/3": { stato: 409, corpo: { detail: { code: "name_taken" } } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "Lum" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    expect((await screen.findByRole("alert")).textContent).toContain("Nome già usato da un altro filtro.")
  })

  it("un pezzo senza frame non dice un'ora che non c'e'", async () => {
    attrezzatura({ instruments: [{ ...OTTICA, frames: 0, integration_s: 0, bar_pct: 3 }] })
    await apriAttrezzatura()
    const telescopi = await vedi(/telescopi/i)
    expect(telescopi.textContent).toContain("non indicato nei file")
    expect(telescopi.querySelector('[data-an="barra"]')).toBeNull()
  })

  it("un'eliminazione rifiutata si dice come gli altri errori del modulo", async () => {
    attrezzatura(
      {},
      { "DELETE /api/v1/gear/instruments/2": { stato: 404, corpo: { detail: { code: "not_found" } } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)
    fireEvent.click(screen.getByRole("button", { name: /^elimina$/i }))
    fireEvent.click(within(screen.getByRole("alertdialog")).getByRole("button", { name: /^elimina$/i }))
    expect((await screen.findByRole("alert")).textContent).toContain("Dati non aggiornati")
  })

  it("un pezzo usato non si elimina: Elimina spento, chi lo usa e Unisci a", async () => {
    const altra = { ...OTTICA, id: 5, name: "TS130APO" }
    attrezzatura({
      instruments: [
        { ...OTTICA, mergeable_into: [5], delete_refused: { code: "in_use", frames: 120, rigs: [10] } },
        altra,
      ],
    })
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /^TS 130 APO/)

    const elimina = screen.getByRole("button", { name: /^elimina$/i })
    expect(elimina.getAttribute("aria-disabled")).toBe("true")
    expect(
      screen.getByText("Lo usano 120 frame di Il grande: nessuna ora si perde. Uniscilo a un altro pezzo, se è lo stesso."),
    ).toBeDefined()
    fireEvent.click(elimina)
    expect(screen.queryByRole("alertdialog")).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /^unisci a$/i }))
    expect(document.activeElement).toBe(screen.getByLabelText(/^unisci a/i))
  })

  it("l'ottica di un setup senza frame dice che ne fa parte", async () => {
    attrezzatura({ instruments: [{ ...OTTICA, delete_refused: { code: "in_rig", frames: 0, rigs: [10] } }] })
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /TS 130 APO/)
    expect(
      screen.getByText("Fa parte di Il grande: un setup è fatto della sua ottica e della sua camera."),
    ).toBeDefined()
  })

  it("un pezzo senza frame si elimina dopo la conferma, che dice da quali setup esce", async () => {
    attrezzatura(
      { instruments: [OTTICA, { ...MONTATURA, in_rigs: [{ rig_id: 10, frames: 0, chosen: true }] }] },
      { "DELETE /api/v1/gear/instruments/2": { stato: 204, corpo: null } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)
    fireEvent.click(screen.getByRole("button", { name: /^elimina$/i }))

    const domanda = screen.getByRole("alertdialog", { name: "Eliminare EQ6-R? Non tiene frame." })
    expect(domanda.textContent).toContain("Esce anche da Il grande.")
    fireEvent.click(within(domanda).getByRole("button", { name: /^elimina$/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.metodo).toBe("DELETE")
    expect(scritture()[0]?.url).toContain("/api/v1/gear/instruments/2")
  })

  it("con la scansione in corso Salva ed Elimina sono spenti, e lo dicono", async () => {
    attrezzatura({}, { "/api/v1/pipeline/status": { stato: 200, corpo: { action: "stop", worker: { state: "running", stage: null, stages: [] } } } })
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)
    expect(await screen.findByText("Scansione in corso: si salva al termine.")).toBeDefined()
    expect(screen.getByRole("button", { name: /salva/i }).getAttribute("aria-disabled")).toBe("true")
    expect(screen.getByText("Scansione in corso: si elimina al termine.")).toBeDefined()
    expect(screen.getByRole("button", { name: /^elimina$/i }).getAttribute("aria-disabled")).toBe("true")
  })

  it("dico che un filtro e' lo stesso di un altro, fra quelli che l'API offre", async () => {
    attrezzatura(
      {
        filters: [
          { ...FILTRO, mergeable_into: [4] },
          { ...FILTRO, id: 4, name: "Baader Ha" },
          { ...FILTRO, id: 5, name: "H" },
        ],
      },
      { "PATCH /api/v1/gear/filters/3": { stato: 200, corpo: { id: 3, requeued: 60, run_started: true } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    const tendina = screen.getByLabelText(/^unisci a/i)
    expect(within(tendina).queryByRole("option", { name: "H" })).toBeNull()
    fireEvent.change(tendina, { target: { value: "4" } })
    expect(screen.queryByLabelText(/marca/i)).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ merge_into: 4 })
  })
})

describe("l Attrezzatura sul telefono", () => {
  it("prima l indice, poi il dettaglio a pagina intera e la via per tornare", async () => {
    attrezzatura()
    window.history.pushState({}, "", "/attrezzatura?formato=telefono")
    await disegna()

    // la prima schermata e' l'indice, senza niente di segnato e senza dettaglio
    const indice = await screen.findByRole("navigation", { name: /indice dell'attrezzatura/i })
    expect(indice.querySelectorAll('[aria-current="true"]')).toHaveLength(0)
    expect(screen.queryByRole("region", { name: /^parti$/i })).toBeNull()

    fireEvent.click(within(indice).getByRole("link", { name: /il grande/i }))
    expect(await parti()).toBeDefined()
    expect(screen.queryByRole("navigation", { name: /indice dell'attrezzatura/i })).toBeNull()

    fireEvent.click(screen.getByRole("button", { name: /attrezzatura/i }))
    expect(await screen.findByRole("navigation", { name: /indice dell'attrezzatura/i })).toBeDefined()
    expect(screen.queryByRole("region", { name: /^parti$/i })).toBeNull()
  })
})

describe("l Attrezzatura, un pezzo dall'indirizzo", () => {
  it("con ?pezzo= la riga di quel pezzo e' segnata, e nessun'altra", async () => {
    attrezzatura()
    window.history.pushState({}, "", `/attrezzatura?pezzo=strumento-${OTTICA.id}`)
    await disegna()

    const telescopi = await screen.findByRole("list", { name: /telescopi/i })
    const riga = within(telescopi).getByText(/TS 130 APO/).closest("li") as HTMLElement
    expect(riga.getAttribute("aria-current")).toBe("true")
    expect(telescopi.querySelectorAll('[aria-current="true"]')).toHaveLength(1)
    // nell'indice e' segnato il suo gruppo, e nient'altro
    const indice = screen.getByRole("navigation", { name: /indice dell'attrezzatura/i })
    const segnati = [...indice.querySelectorAll('[aria-current="true"]')].map((x) => x.textContent)
    expect(segnati).toEqual([expect.stringMatching(/^Telescopi/)])
  })

  it("un filtro si apre allo stesso modo", async () => {
    attrezzatura()
    window.history.pushState({}, "", `/attrezzatura?pezzo=filtro-${FILTRO.id}`)
    await disegna()

    const filtri = await screen.findByRole("list", { name: /filtri/i })
    expect(within(filtri).getAllByRole("listitem").some((r) => r.getAttribute("aria-current") === "true")).toBe(true)
  })
})
