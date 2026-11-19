// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *ASTAP* (tavola v82): da dove viene, il percorso con Verifica percorso e
 * Cercalo tu, i cataloghi trovati.
 *
 * Le regole provate qui sono quelle che una lettura del codice non prende: che il **canale** si
 * legga accanto al percorso -- "trovato" da solo non si puo' smentire -- che un percorso scritto e
 * sbagliato **resti a schermo**, e che la ricerca **proponga senza scrivere**.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SPINA,
  STANOTTE,
  apriImpostazioni,
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
  databases: ["d50"],
}
const ASSENTE = { path: null, source: null, declared: null, databases: [] }

function mappa(solver: unknown, piu: Record<string, unknown> = {}) {
  return {
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...piu,
    "/api/v1/solver": { stato: 200, corpo: solver },
    ...SPINA,
  }
}

async function vaiAdASTAP(solver: unknown = TROVATO, piu: Record<string, unknown> = {}) {
  rispondi(mappa(solver, piu) as never)
  await disegna()
  await apriImpostazioni()
  fireEvent.click(await screen.findByRole("tab", { name: /^astap$/i }))
  return screen.findByRole("region", { name: "ASTAP" })
}

const campo = (c: HTMLElement) => within(c).getByLabelText(/percorso di astap/i) as HTMLInputElement

describe("Impostazioni / ASTAP", () => {
  it("dice dove sta, e da cosa l app l ha dedotto", async () => {
    const carta = await vaiAdASTAP()

    expect(within(carta).getByText("installato a parte, da hnsky.org")).toBeTruthy()
    // il percorso e la sua origine sono due cose: fra loro c'e' un separatore
    expect(within(carta).getByText(/astap_cli\.exe · percorso inserito manualmente$/)).toBeTruthy()
    expect(campo(carta).value).toBe(TROVATO.path)
  })

  it("ogni canale ha la sua frase, e nessuno resta un codice a schermo", async () => {
    for (const [source, frase] of [
      ["env", /variabile ASTROLOG_ASTAP/i],
      ["path", /PATH di sistema/i],
      ["known_place", /cartella di installazione predefinita/i],
    ] as const) {
      pulisci()
      const carta = await vaiAdASTAP({ ...TROVATO, source, declared: null })
      expect(within(carta).getByText(frase), source).toBeTruthy()
      expect(within(carta).queryByText(source)).toBeNull()
    }
  })

  it("non trovandolo dice cosa si perde, e non parla di cataloghi", async () => {
    const carta = await vaiAdASTAP(ASSENTE)

    expect(within(carta).getByText("ASTAP non trovato.")).toBeTruthy()
    expect(within(carta).getByText(/gli oggetti ripresi non vengono identificati/i)).toBeTruthy()
    expect(within(carta).queryByText(/catalogo/i)).toBeNull()
  })

  it("ogni catalogo trovato su una riga, D50 consigliato", async () => {
    const carta = await vaiAdASTAP({ ...TROVATO, databases: ["d05", "d50", "d80"] })

    expect(within(carta).getByText("Catalogo D50")).toBeTruthy()
    expect(within(carta).getByText("consigliato: va bene per quasi tutti i campi")).toBeTruthy()
    expect(within(carta).getByText("per i campi molto stretti")).toBeTruthy()
    expect(within(carta).getAllByText("\u2713 trovato")).toHaveLength(3)
  })

  it("ASTAP senza catalogo lo dice", async () => {
    const carta = await vaiAdASTAP({ ...TROVATO, databases: [] })

    expect(within(carta).getByText("? nessun catalogo")).toBeTruthy()
    expect(within(carta).getByText(/senza catalogo gli oggetti non vengono identificati/i)).toBeTruthy()
    const dove = within(carta).getByRole("link", { name: /sul sito di hnsky\.org/i })
    expect(dove.getAttribute("href")).toContain("hnsky.org")
    expect(dove.getAttribute("rel")).toContain("noopener")
  })

  it("un percorso scritto e sbagliato resta a schermo", async () => {
    const carta = await vaiAdASTAP({ ...ASSENTE, declared: "D:\\sbagliato\\astap.exe" })

    expect(within(carta).getByText("ASTAP non trovato in questo percorso.")).toBeTruthy()
    expect(campo(carta).value).toBe("D:\\sbagliato\\astap.exe")
  })

  it("una ASTROLOG_ASTAP sbagliata e' nominata, non spacciata per ASTAP assente (#86)", async () => {
    const carta = await vaiAdASTAP({ ...ASSENTE, wrong_env: "/opt/astap/astap_cli" })

    expect(
      within(carta).getByText("ASTROLOG_ASTAP punta a un file che non esiste: /opt/astap/astap_cli"),
    ).toBeTruthy()
    expect(within(carta).getByText(/cercalo tu la salta/i)).toBeTruthy()
    expect(within(carta).queryByText("ASTAP non trovato.")).toBeNull()
  })

  it("Cercalo tu propone, e non scrive niente finche' non si sceglie", async () => {
    const carta = await vaiAdASTAP(ASSENTE, {
      "POST /api/v1/solver": { stato: 200, corpo: { ...TROVATO, source: "path" } },
      "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    })

    fireEvent.click(within(carta).getByRole("button", { name: "Cercalo tu" }))
    expect(await within(carta).findByText(`Trovato in ${TROVATO.path}`)).toBeTruthy()
    expect(within(carta).getByText("Il percorso non cambia finché non lo scegli.")).toBeTruthy()
    expect(scritture().some((s) => s.url.includes("/settings"))).toBe(false)

    fireEvent.click(within(carta).getByRole("button", { name: "Usa questo percorso" }))
    await waitFor(() =>
      expect(scritture().find((s) => s.metodo === "PATCH")?.corpo).toMatchObject({
        values: { astap_path: TROVATO.path },
      }),
    )
    await waitFor(() => expect(within(carta).queryByRole("button", { name: "Usa questo percorso" })).toBeNull())
    expect(campo(carta).value).toBe(TROVATO.path)
  })

  it("una ricerca a vuoto lo dice, invece di non rispondere", async () => {
    const carta = await vaiAdASTAP(ASSENTE, { "POST /api/v1/solver": { stato: 200, corpo: ASSENTE } })

    fireEvent.click(within(carta).getByRole("button", { name: "Cercalo tu" }))
    expect(await within(carta).findByText(/astap non trovato nel PATH/i)).toBeTruthy()
  })

  it("Verifica percorso scrive una volta sola, e dice com e andata", async () => {
    // premere il tasto toglie il fuoco dal campo: senza memoria partirebbero due scritture
    const carta = await vaiAdASTAP(ASSENTE, {
      "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true, ["no_solver"]) },
    })

    fireEvent.change(campo(carta), { target: { value: "D:/sbagliato" } })
    fireEvent.blur(campo(carta))
    fireEvent.click(within(carta).getByRole("button", { name: "Verifica percorso" }))

    expect(await within(carta).findByText("ASTAP non trovato in questo percorso.")).toBeTruthy()
    expect(scritture().filter((s) => s.metodo === "PATCH")).toHaveLength(1)
    // cambiando il percorso l'esito di quello di prima se ne va
    fireEvent.change(campo(carta), { target: { value: "D:/un-altro" } })
    expect(within(carta).queryByText("ASTAP non trovato in questo percorso.")).toBeNull()
  })

  it("scritto il percorso giusto, la carta lo sa senza ricaricare", async () => {
    const carta = await vaiAdASTAP(ASSENTE, {
      "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    })
    cambia(mappa(TROVATO, { "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) } }) as never)

    fireEvent.change(campo(carta), { target: { value: TROVATO.path } })
    fireEvent.click(within(carta).getByRole("button", { name: "Verifica percorso" }))

    expect(await within(carta).findByText("Gli oggetti ripresi verranno identificati.")).toBeTruthy()
    expect(await within(carta).findByText("Catalogo D50")).toBeTruthy()
  })

  it("sul NAS il percorso si legge e non si cambia: lo decide chi gestisce il NAS (#95)", async () => {
    const nas = { ...TROVATO, path: "/opt/astap/astap_cli", source: "env", declared: null, set_by_admin: true }
    const carta = await vaiAdASTAP(nas)

    expect(within(carta).getByText("impostato da chi gestisce il NAS")).toBeTruthy()
    expect(
      within(carta).getByText("Qui non si cambia: lo decide la variabile ASTROLOG_ASTAP del container."),
    ).toBeTruthy()
    expect(within(carta).getByText("/opt/astap/astap_cli")).toBeTruthy()
    expect(within(carta).getByText(/· variabile ASTROLOG_ASTAP$/)).toBeTruthy()
    expect(within(carta).queryByLabelText(/percorso di astap/i)).toBeNull()
    expect(within(carta).queryByRole("button", { name: "Verifica percorso" })).toBeNull()
    expect(within(carta).queryByRole("button", { name: "Cercalo tu" })).toBeNull()
    expect(within(carta).queryByText("installato a parte, da hnsky.org")).toBeNull()
    expect(within(carta).getByText("Catalogo D50")).toBeTruthy()
  })
})
