// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Scansioni*: le ricevute delle scansioni passate.
 *
 * Le regole provate qui sono quelle che una lettura del codice non prende: che uno **zero non sia
 * una riga** tranne dove e' la risposta, che una corsa ancora aperta **non duri zero**, che un
 * codice del backend non arrivi mai a schermo, che i file non letti si chiedano solo aprendoli, e
 * che il tasto che li apre dica a chi ascolta cosa governa.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  FERMO,
  LETTURA,
  SALUTE,
  SPINA,
  STANOTTE,
  cambia,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
} from "./banco"

afterEach(pulisci)

/** I file che una lettura non ha letto: la risposta della rotta a parte, che si chiede solo
 *  aprendo il pannello. */
const NON_LETTI = {
  stato: 200,
  corpo: {
    items: [
      { file: "sub\\rotto.fit", reason: "header_unreadable" },
      { file: "chiuso.fit", reason: "file_unreadable" },
    ],
    total: 2,
    limit: 100,
    offset: 0,
  },
}

function app(
  items: unknown[] = [LETTURA],
  total = items.length,
  nonLetti: { stato: number; corpo: unknown } = NON_LETTI,
  spina: Record<string, { stato: number; corpo: unknown }> = SPINA,
) {
  rispondi({
    ...STANOTTE,
    // prima di `/api/v1/scan-runs`, che come prefisso la prenderebbe lei
    "/api/v1/scan-runs/3/errors": nonLetti,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": {
      stato: 200,
      corpo: { to_confirm: 0 },
    },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/scan-runs": { stato: 200, corpo: { items, total, limit: 20, offset: 0 } },
    ...spina,
  })
  return disegna()
}

/** Apre la sezione come fa chi usa l'app: dalla barra, poi dall'elenco delle sezioni. */
async function vaiAlleLetture() {
  const barra = await screen.findByRole("navigation", { name: /pagine/i })
  fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
  fireEvent.click(await screen.findByRole("link", { name: /^scansioni$/i }))
}

describe("Impostazioni / Scansioni", () => {
  it("una lettura dice quale cartella, quando, quanto e com e andata", async () => {
    await app([{ ...LETTURA, found: 120, new: 5, unchanged: 115 }])
    await vaiAlleLetture()

    const riga = await within(await screen.findByRole("main")).findByRole("listitem")
    expect(riga.textContent).toContain("D:\\Astro\\2025")
    expect(riga.textContent).toMatch(/2 min 14 s/)
    expect(within(riga).getByText(/^completata$/i)).toBeTruthy()
    expect(riga.textContent).toMatch(/5 nuovi/)
    expect(riga.textContent).toMatch(/120 file esaminati/)
  })

  it("uno zero non e una riga, tranne dove e la risposta", async () => {
    // "0 nuovi" e' la risposta alla domanda che si fa chi guarda dopo una scansione; "0 doppioni"
    // e' rumore, e sette zeri di fila seppelliscono l'unico numero che conta.
    await app([{ ...LETTURA, found: 120, unchanged: 120 }])
    await vaiAlleLetture()

    const riga = await within(await screen.findByRole("main")).findByRole("listitem")
    expect(riga.textContent).toMatch(/0 nuovi/)
    expect(riga.textContent).not.toMatch(/duplicat/)
    expect(riga.textContent).not.toMatch(/esclus/)
    expect(riga.textContent).toMatch(/120 gi\u00e0 in archivio/)
  })

  it("una lettura ancora in corso non dura zero", async () => {
    // Uno "0 s" direbbe che e' finita in un istante. Sta leggendo adesso, ed e' un'altra cosa.
    await app([{ ...LETTURA, ended_at: null, duration_s: null, status: null, found: 12 }])
    await vaiAlleLetture()

    const riga = await within(await screen.findByRole("main")).findByRole("listitem")
    expect(riga.textContent).toMatch(/\bin corso\b/)
    // ai confini di parola: senza, "0 s" si trova dentro l'ora "21:00 sta..." e la prova
    // passerebbe per il motivo sbagliato
    expect(riga.textContent).not.toMatch(/\b0 s\b/)
    // e non c'e' nessun esito: non e' andata ne' bene ne' male, non e' finita
    expect(within(riga).queryByText(/^completata$/i)).toBeNull()
  })

  it("una corsa fermata da un guasto dice perche', a parole", async () => {
    await app([{ ...LETTURA, status: "aborted", reason: "root_unreachable", found: 3 }])
    await vaiAlleLetture()

    const riga = await within(await screen.findByRole("main")).findByRole("listitem")
    expect(within(riga).getByText(/^interrotta$/i)).toBeTruthy()
    expect(riga.textContent).toMatch(/cartella non raggiungibile/i)
    expect(riga.textContent).not.toMatch(/root_unreachable/)
  })

  it("una corsa fermata da te non ripete il perche'", async () => {
    // "Interrotta dall'utente" lo dice gia': aggiungere "perche' l'hai fermata tu" e' una riga che non
    // porta niente.
    await app([{ ...LETTURA, status: "stopped", reason: "stop_requested" }])
    await vaiAlleLetture()

    const riga = await within(await screen.findByRole("main")).findByRole("listitem")
    expect(within(riga).getByText(/^interrotta dall'utente$/i)).toBeTruthy()
    expect(riga.textContent).not.toMatch(/stop_requested/)
  })

  it("senza letture dice cosa fare, invece di un elenco vuoto", async () => {
    await app([], 0)
    await vaiAlleLetture()

    expect(await screen.findByText(/^nessuna scansione$/i)).toBeTruthy()
    expect(screen.getByText(/aggiungi una cartella e avvia la scansione/i)).toBeTruthy()
  })

  it("cosa e rimasto fuori si apre solo se e rimasto fuori qualcosa", async () => {
    // Una lettura pulita non ha niente da aprire: un pannello vuoto e' una promessa che l'app
    // non mantiene.
    await app([{ ...LETTURA, found: 14, new: 14 }])
    await vaiAlleLetture()
    await within(await screen.findByRole("main")).findByRole("listitem")
    expect(screen.queryByRole("button", { name: /^file esclusi$/i })).toBeNull()

    pulisci()
    const saltati = [{ reason: "calibration", count: 3 }]
    await app([{ ...LETTURA, found: 14, skipped: 3, skipped_by_reason: saltati }])
    await vaiAlleLetture()
    fireEvent.click(await screen.findByRole("button", { name: /^file esclusi$/i }))
    expect(await screen.findByText(/3 di calibrazione \(dark, flat, bias\)/i)).toBeTruthy()
  })

  it("il tasto che apre dice a chi ascolta cosa governa, e se ora e aperto", async () => {
    // Il bottone **resta** mentre il pannello e' aperto, quindi e' un interruttore: chi usa un
    // lettore di schermo deve sapere che apre qualcosa, quale, e com'e' adesso. Non lo prende la
    // guardia di accessibilita': per axe un interruttore senza stato e' al massimo "incompleto".
    const saltati = [{ reason: "calibration", count: 1 }]
    await app([{ ...LETTURA, found: 14, skipped: 1, skipped_by_reason: saltati }])
    await vaiAlleLetture()

    const tasto = await screen.findByRole("button", { name: /^file esclusi$/i })
    expect(tasto.getAttribute("aria-expanded")).toBe("false")
    const governato = tasto.getAttribute("aria-controls")
    expect(governato).toBeTruthy()
    expect(document.getElementById(governato!)).toBeNull()

    fireEvent.click(tasto)
    expect(tasto.getAttribute("aria-expanded")).toBe("true")
    // e l'id nominato e' davvero il pannello, non una promessa a vuoto
    expect(document.getElementById(governato!)).toBe(
      screen.getByRole("region", { name: /^file esclusi$/i }),
    )
  })

  it("i file non letti si chiedono al backend solo quando si guardano", async () => {
    // Possono essere migliaia, e una ricevuta su venti interessa: chiederli tutti a ogni apertura
    // della pagina sarebbe venti elenchi lunghi che nessuno ha chiesto.
    await app([{ ...LETTURA, found: 14, errors: 2 }])
    await vaiAlleLetture()
    await within(await screen.findByRole("main")).findByRole("listitem")
    expect(chiamate().filter((c) => c.includes("/errors")).length).toBe(0)

    fireEvent.click(screen.getByRole("button", { name: /^file esclusi$/i }))
    expect(await screen.findByText(/sub\\rotto\.fit/)).toBeTruthy()
    expect(screen.getByText(/un FITS o header non valido/i)).toBeTruthy()
    expect(document.body.textContent).not.toMatch(/header_unreadable/)
  })

  it("una lettura che non tiene piu l elenco lo dice, invece di un elenco vuoto", async () => {
    // Su una lettura che l'elenco non ce l'ha piu', "nessun file" sarebbe una bugia: i file non
    // letti erano due e li ha contati la riga sopra.
    await app([{ ...LETTURA, found: 14, errors: 2 }], 1, {
      stato: 410,
      corpo: { detail: { code: "errors_not_kept" } },
    })
    await vaiAlleLetture()
    fireEvent.click(await screen.findByRole("button", { name: /^file esclusi$/i }))

    expect(await screen.findByText(/conservato solo per l'ultima scansione di ogni cartella/i)).toBeTruthy()
  })

  it("una cartella lasciata fuori dice perche', a parole", async () => {
    await app([
      {
        ...LETTURA,
        found: 14,
        hidden_dirs: ["cestino"],
        linked_dirs: ["scorciatoia"],
        unreadable_dirs: ["protetta"],
      },
    ])
    await vaiAlleLetture()
    fireEvent.click(await screen.findByRole("button", { name: /^file esclusi$/i }))

    const fuori = await screen.findByRole("region", { name: /^file esclusi$/i })
    expect(fuori.textContent).toMatch(/cestino/)
    expect(fuori.textContent).toMatch(/cestino nascosta, ignorata/)
    expect(fuori.textContent).toMatch(/scorciatoia/)
    expect(fuori.textContent).toMatch(/scorciatoia collegamento simbolico, non seguito/)
    expect(fuori.textContent).toMatch(/protetta/)
    expect(fuori.textContent).toMatch(/protetta non leggibile/)
    // nessuna chiamata per i file: non ce n'erano di non letti
    expect(chiamate().filter((c) => c.includes("/errors")).length).toBe(0)
  })

  it("quando una lettura finisce, la sua ricevuta compare senza ricaricare", async () => {
    // E' la pagina che risponde a "ha funzionato?": trovarci l'elenco di prima della scansione
    // che si e' appena guardata partire sarebbe la risposta sbagliata.
    await app([LETTURA], 1, NON_LETTI, {
      "/api/v1/pipeline/status": {
        stato: 200,
        corpo: { ...FERMO, worker: { ...FERMO.worker, state: "running", stage: "scan" } },
      },
    })
    await vaiAlleLetture()
    await within(await screen.findByRole("main")).findByRole("listitem")

    cambia({
      "/api/v1/pipeline/status": {
        stato: 200,
        corpo: {
          ...FERMO,
          worker: { ...FERMO.worker, state: "completed", ended_at: "2026-09-20T21:10:00Z" },
        },
      },
      "/api/v1/scan-runs": {
        stato: 200,
        corpo: {
          items: [{ ...LETTURA, id: 4, folder_path: "D:\\Astro\\2026" }, LETTURA],
          total: 2,
          limit: 20,
          offset: 0,
        },
      },
    })

    // il battito dello stato mentre gira e' 1,5 s: si aspetta quello, non un tempo inventato
    expect(await screen.findByText(/D:\\Astro\\2026/, {}, { timeout: 5000 })).toBeTruthy()
  })

  it("si chiedono le precedenti solo se ce ne sono", async () => {
    await app([LETTURA], 1)
    await vaiAlleLetture()
    await within(await screen.findByRole("main")).findByRole("listitem")
    expect(screen.queryByRole("button", { name: /scansioni precedenti/i })).toBeNull()

    pulisci()
    await app([LETTURA], 40)
    await vaiAlleLetture()
    const altre = await screen.findByRole("button", { name: /scansioni precedenti/i })

    const prima = chiamate().filter((c) => c.includes("scan-runs")).length
    fireEvent.click(altre)
    // se ne chiedono di piu', e si chiedono **al backend**: tagliare in casa un elenco che il
    // backend pagina vorrebbe dire mostrare sempre le stesse venti
    await waitFor(() =>
      expect(chiamate().filter((c) => c.includes("limit=40")).length).toBeGreaterThan(0),
    )
    expect(chiamate().filter((c) => c.includes("scan-runs")).length).toBeGreaterThan(prima)
  })
})
