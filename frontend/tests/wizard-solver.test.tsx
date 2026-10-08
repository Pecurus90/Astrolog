// @vitest-environment jsdom
/**
 * Il quinto passo del primo avvio: **il riconoscitore**, e compare solo quando manca.
 *
 * Senza il solver l'app cataloga, mette in ordine i nomi e conta le ore, ma non sa **cosa** hai
 * ripreso. Chi installa e non ce l'ha, oggi, non lo scopre da nessuna parte: scansiona, aspetta,
 * e non riconosce niente. Il resto del primo avvio sta in `wizard.test.tsx` e le cartelle in
 * `wizard-cartelle.test.tsx`.
 *
 * test-tolto: "con tutto a posto i passi restano tre" -- rinominata: i passi per tutti ora sono quattro
 * test-tolto: "anche il quarto passo passa dai mattoni" -- rinominata: il riconoscitore ora e' il quinto
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, disegna, fuoriDaiMattoni, impostazioni, nomiDeiPassi, pulisci, quantiControlli, rispondi, scritture } from "./banco"

afterEach(pulisci)

/** Le impostazioni col loro `missing`: e' la riga che dice cosa manca all'app. */
function conManca(manca: string[]) {
  const base = impostazioni(false)
  return { ...base, missing: manca }
}

/** `extra` aggiunge o sostituisce una voce: `rispondi` prende la mappa intera, e passargli la
 *  sola PATCH lascerebbe il primo avvio senza le risposte che gli servono per comparire. */
function primoAvvio(manca: string[], extra: Parameters<typeof rispondi>[0] = {}) {
  rispondi({
    ...STANOTTE,
    "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
    "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/settings": { stato: 200, corpo: conManca(manca) },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    ...SPINA,
    ...extra,
  })
}

const avanti = () => fireEvent.click(screen.getByRole("button", { name: /avanti/i }))

/** Porta al passo del solver, che e' l'ultimo. Aspetta il montaggio: il primo avvio compare dopo
 *  la risposta delle impostazioni, e cliccare prima trova il vuoto. */
async function alPassoDelSolver() {
  await disegna()
  await screen.findByRole("button", { name: /salta/i })
  avanti()
  avanti()
  avanti()
  avanti()
}

describe("il passo del riconoscitore, quando manca", () => {
  it("con tutto a posto i passi restano quattro", async () => {
    // La regola che tiene onesto il primo avvio: il quinto non e' un passo in piu' per tutti,
    // e' una rete che compare quando serve. Chi ha gia' il solver non deve nemmeno saperlo.
    primoAvvio(["no_active_site"])
    await disegna()

    await screen.findAllByRole("listitem")
    expect(nomiDeiPassi()).toEqual(["Nome utente", "Sito di osservazione", "Percorso dei file", "Seeing (Meteoblue)"])
  })

  it("se manca, il passo c e e dice cosa ci perdi", async () => {
    primoAvvio(["no_active_site", "no_solver"])
    await disegna()

    await screen.findAllByRole("listitem")
    expect(nomiDeiPassi()).toContain("ASTAP")

    avanti()
    avanti()
    avanti()
    avanti()
    expect(screen.getByText(/gli oggetti ripresi non vengono identificati/i)).toBeDefined()
    // non un allarme: manca una cosa da fare, non e' un guasto
    expect(screen.queryByRole("alert")).toBeNull()
    // E gli si dice **anche del catalogo**: chi installa ASTAP dopo aver chiuso il primo avvio
    // non ripassa piu' di qua, e cadrebbe nella trappola che questa schermata esiste per evitare.
    expect(screen.getByText(/serve anche il catalogo stellare/i)).toBeDefined()
  })

  it("scritto un percorso giusto, la conferma resta e la schermata non cambia sotto le mani", async () => {
    // Il passo si guarda mentre ci si scrive dentro: una risposta che arriva dopo e cambia
    // schermata si porta via il campo e la conferma di cio' che si e' appena scritto. Per questo
    // quale dei due casi sia lo decide chi monta il passo, **entrando**, come il loro numero.
    primoAvvio(["no_solver"], {
      "PATCH /api/v1/settings": { stato: 200, corpo: conManca([]) },
    })
    await alPassoDelSolver()

    fireEvent.change(await screen.findByLabelText(/percorso di astap/i), {
      target: { value: "D:/astap/astap_cli.exe" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica percorso$/i }))

    expect(await screen.findByText(/gli oggetti ripresi verranno identificati/i)).toBeDefined()
    // il campo e' ancora li', con dentro cio' che si e' scritto
    expect((screen.getByLabelText(/percorso di astap/i) as HTMLInputElement).value).toBe(
      "D:/astap/astap_cli.exe",
    )
    // E l'intestazione resta **quella di quando si e' entrati**: i passi e le loro ragioni si
    // congelano li', percio' continua a dire cio' che mancava allora. Cambiarla adesso vorrebbe
    // dire riscrivere la schermata sotto chi ci sta scrivendo, che e' il difetto che questa
    // prova sorveglia.
    expect(screen.getByText(/astap non \u00e8 installato/i)).toBeDefined()
    // e i passi restano quelli: toglierne uno adesso lascerebbe una schermata vuota sotto i
    // piedi di chi ci sta dentro
    expect(screen.getAllByRole("listitem")).toHaveLength(5)
  })

  it("scritto un percorso giusto ma senza catalogo, la conferma non promette troppo", async () => {
    // "L'app riconoscera' cosa hai ripreso" a chi il catalogo non ce l'ha promette il contrario
    // di quello che succedera': la scansione si ferma alla prima posa.
    primoAvvio(["no_solver"], {
      "PATCH /api/v1/settings": { stato: 200, corpo: conManca(["no_star_database"]) },
    })
    await alPassoDelSolver()

    fireEvent.change(await screen.findByLabelText(/percorso di astap/i), {
      target: { value: "D:/astap/astap_cli.exe" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica percorso$/i }))

    expect(await screen.findByText(/catalogo stellare mancante: senza/i)).toBeDefined()
    expect(screen.queryByText(/gli oggetti ripresi verranno identificati/i)).toBeNull()
  })

  it("il passo c e anche a chi ha ASTAP senza il suo catalogo", async () => {
    // Ci si arriva allo stesso identico punto -- una scansione che non riconosce niente -- e
    // chiedere il passo solo a chi non ha il programma lasciava fuori chi l'ha installato e si e'
    // fermato prima di scaricare anche quello.
    primoAvvio(["no_star_database"])
    await disegna()

    await screen.findAllByRole("listitem")
    expect(nomiDeiPassi()).toContain("ASTAP")

    avanti()
    avanti()
    avanti()
    avanti()
    // Si aspetta il **collegamento del catalogo**, che lo rende solo il corpo: la frase "manca il
    // catalogo stellare" sta anche nell'intestazione, che c'e' da subito -- aspettare quella non
    // aspetta niente, e la prova passava anche col corpo sbagliato.
    expect(await screen.findByRole("link", { name: /scarica il catalogo/i })).toBeTruthy()
    // Il percorso qui non si chiede: e' gia' giusto, e chiederlo manda a correggere cio' che
    // non e' sbagliato.
    expect(screen.queryByLabelText(/percorso di astap/i)).toBeNull()
    // E la ragione e' **la sua**: "non trovo ASTAP" a chi ce l'ha manda a cercare la cosa
    // sbagliata.
    expect(screen.queryByText(/astap non \u00e8 installato/i)).toBeNull()
    expect(screen.getByText(/^catalogo mancante$/i)).toBeTruthy()
  })

  it("il collegamento per prenderlo c e, e l app non lo scarica da sola", async () => {
    // Scaricare ed eseguire un programma senza che l'utente lo chieda e' l'unica cosa che l'app
    // non deve fare: si da' l'indirizzo, e decide lui.
    primoAvvio(["no_solver"])
    await alPassoDelSolver()

    const link = await screen.findByRole("link", { name: /scarica/i })
    expect(link.getAttribute("href")).toContain("astap")
    expect(link.getAttribute("rel")).toContain("noopener")
  })

  it("dico dove sta, e l app se lo scrive", async () => {
    primoAvvio(["no_solver"])
    await alPassoDelSolver()

    fireEvent.change(await screen.findByLabelText(/percorso di astap/i), {
      target: { value: "D:/astap/astap.exe" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica percorso$/i }))

    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.endsWith("/api/v1/settings"))
      expect(scritta?.corpo).toMatchObject({ values: { astap_path: "D:/astap/astap.exe" } })
    })
  })

  it("il percorso scritto si salva anche lasciando il campo", async () => {
    // Senza questo, chi scrive il percorso e preme Fatto senza toccare "Usa questo" ha battuto
    // a mano una riga che l'app butta via in silenzio -- e alla scansione dopo non riconosce
    // niente, senza sapere perche'.
    primoAvvio(["no_solver"])
    await alPassoDelSolver()

    const campo = await screen.findByLabelText(/percorso di astap/i)
    fireEvent.change(campo, { target: { value: "D:/astap/astap_cli.exe" } })
    fireEvent.blur(campo)

    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.endsWith("/api/v1/settings"))
      expect(scritta?.corpo).toMatchObject({ values: { astap_path: "D:/astap/astap_cli.exe" } })
    })
  })

  it("se li' non c e nessun solver, il passo lo dice", async () => {
    // La promessa dell'app e' che un percorso sbagliato non diventi un ripiego di nascosto. Ma
    // se il rifiuto non si vede, e' identico a un successo: si scrive, non cambia niente a
    // schermo, e si scopre il guaio a scansione finita.
    primoAvvio(["no_solver"])
    await alPassoDelSolver()

    fireEvent.change(await screen.findByLabelText(/percorso di astap/i), {
      target: { value: "D:/sbagliato" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica percorso$/i }))

    expect(await screen.findByText(/astap non trovato in questo percorso/i)).toBeDefined()
  })

  it("anche il passo del riconoscitore passa dai mattoni", async () => {
    // Gli altri tre li guarda `wizard.test.tsx`, e questo li' non si vede: compare solo quando il
    // riconoscitore manca, cioe' proprio nel caso che nessuna prova di veste attraversa.
    primoAvvio(["no_solver"])
    await alPassoDelSolver()
    expect(quantiControlli()).toBeGreaterThan(0)
    expect(fuoriDaiMattoni()).toEqual([])
  })

  it("si puo' saltare, e l app resta usabile", async () => {
    // Senza solver l'archivio si costruisce lo stesso: obbligare qui vorrebbe dire tenere fuori
    // chi vuole solo catalogare, o chi il solver lo installera' domani.
    primoAvvio(["no_solver"])
    await alPassoDelSolver()

    expect(screen.getByRole("button", { name: /salta/i })).toBeDefined()
    expect(screen.getByRole("button", { name: /^fine$/i })).toBeDefined()
  })
})
