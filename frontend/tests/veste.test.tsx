// @vitest-environment jsdom
/**
 * La veste: il telaio che tiene lo scheletro (ADR 0018), e la colonna misurata di ogni pagina.
 *
 * Qui non si prova che un colore sia bello -- quello e' il foglio, e il contrasto lo misura
 * `tools/controlli_veste.py` sui valori veri. Si prova cio' che **la pagina deve avere perche' il
 * foglio possa funzionare**, e che nessuna pagina nuova se lo dimentichi:
 *
 * - **il telaio esiste ed e' uno**: la testa e il corpo stanno nella colonna del telaio v76, e
 *   solo la testa porta i token del foglio nuovo;
 * - **il corpo e' il contenitore `telaio`** che le pagine col foglio vecchio misurano;
 * - **ogni pagina apre la sua colonna**: `.as-pagina` e' il contenitore `colonna` da cui le righe
 *   e le tabelle sanno di essere strette. Una pagina che nasce senza non si accorge di niente
 *   finche' qualcuno non stringe la finestra.
 */
import { readFileSync } from "node:fs"
import { resolve } from "node:path"

import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { PAGINE } from "../src/pagine"
import { voceArchivio } from "./archivio-banco"
import {
  SALUTE,
  STANOTTE,
  cartellaSenzaData,
  cartellaSenzaTipo,
  daConfermare,
  disegna,
  fuoriDaiMattoni,
  impostazioni,
  mosaicoProposto,
  pulisci,
  riga,
  rispondi,
  scelta,
  vai,
  vaiASezione,
} from "./banco"

afterEach(pulisci)

const PAGINA = daConfermare()

function aperta() {
  rispondi({
    ...STANOTTE,
    "/api/v1/review": { stato: 200, corpo: PAGINA },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/archive": voceArchivio([]),
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
  })
}

describe("una riga di Da confermare", () => {
  const CARTELLA = "D:/Astro/2024-05-17/dark"

  function conUnaDomanda() {
    rispondi({
      ...STANOTTE,
      "/api/v1/review": {
        stato: 200,
        corpo: { ...PAGINA, to_confirm: 1, typeless: [cartellaSenzaTipo({ key: CARTELLA, frames: 120, nights: ["2024-05-17"] })] },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    })
  }

  it("il nome viene per primo, in un elemento suo, aperta e chiusa", async () => {
    // Le prove trovano una domanda dal testo con cui comincia, e chi ascolta la riconosce allo
    // stesso modo: dal nome. Aperta, il nome e' il titolo e apre il nome per chi ascolta.
    conUnaDomanda()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const voce = riga(sezione, CARTELLA)
    expect(voce.textContent?.startsWith(CARTELLA)).toBe(true)
    expect(voce.querySelector("h3")?.textContent).toBe(CARTELLA)
    expect(voce.getAttribute("aria-label")?.startsWith(`${CARTELLA}, `)).toBe(true)
  })

  it("la domanda a cui hai risposto lo dice con una forma, non con un colore", async () => {
    // WCAG 2.2, 1.4.1: chi non distingue i colori deve vedere lo stesso quali domande sta per
    // mandare. Lo stato ha un segno e una parola.
    conUnaDomanda()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const voce = riga(sezione, CARTELLA)
    const stato = () => voce.querySelector(".al-conf__riga-7") as HTMLElement
    const segno = () => stato().querySelector("[aria-hidden=true]")?.textContent
    expect(segno()).toBe("\u25CB")
    expect(stato().lastChild?.textContent).toBe("senza risposta")
    fireEvent.click(scelta(voce, "Calibrazione"))
    expect(segno()).toBe("\u25CF")
    expect(stato().lastChild?.textContent).toBe("da applicare")
  })

  it("cio' che si puo' fare sta nelle parti della domanda, dopo le prove", async () => {
    // La domanda aperta dice prima di cosa si parla, poi chiede. Un controllo lasciato fuori
    // dalla sua parte finirebbe in mezzo ai dati.
    conUnaDomanda()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const voce = riga(sezione, CARTELLA)
    const parte = scelta(voce, "Calibrazione").closest(".al-conf__colonna-19")
    expect(parte).not.toBeNull()
    expect(voce.querySelector("dl.al-conf__centro-3")?.compareDocumentPosition(parte as Element)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    )
  })

  it("i campi di due sezioni hanno il loro mattone e la loro etichetta, anche dietro un clic", async () => {
    // **Si guarda dopo aver aperto.** I campi di questa pagina non esistono finche' non si
    // preme "Cambia" o non si sceglie la strada che li apre: un conto fatto sulla pagina appena
    // caricata torna zero perche' non li vede, non perche' vanno bene.
    // Il mattone del foglio v82 e' `al-campo`, con l'etichetta della parte sopra (`label[for]`).
    rispondi({
      ...STANOTTE,
      "/api/v1/review": {
        stato: 200,
        corpo: {
          ...PAGINA,
          to_confirm: 2,
          undated: [cartellaSenzaData({ key: "D:/Astro/senza-data", frames: 12 })],
          // gia' un si': il suo campo del nome e' aperto
          mosaics: [mosaicoProposto({ key: "impronta-m42", ra_deg: 83.8, dec_deg: -5.4, object: "M 42", panels: 3, frames: 90, answer: "yes", answer_name: "M 42", names: ["M 42"], proposed: "M 42" })],
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    })
    await disegna()
    vai("/da-confermare")
    await screen.findByRole("region", { name: /frame senza data/i })
    const campi = () => [...document.querySelectorAll<HTMLInputElement>(".al-conf__colonna-11 input")]
    const nudi = () =>
      campi()
        .filter((c) => !c.classList.contains("al-campo") || document.querySelector(`label[for="${c.id}"]`) === null)
        .map((c) => c.id || c.outerHTML)
    // la data si scrive dietro la sua strada
    fireEvent.click(screen.getByRole("radio", { name: /^Scrivo la data/ }))
    // che i campi ci siano davvero si guarda prima: un elenco vuoto torna anche su una pagina
    // senza campi, e questa prova diventerebbe verde per il motivo sbagliato
    expect(campi()).toHaveLength(1)
    expect(nudi()).toEqual([])
    // la sezione gia' risposta e' chiusa in una riga: si riapre, poi si apre la sua domanda
    fireEvent.click(screen.getByRole("button", { name: /^riapri: mosaici/i }))
    fireEvent.click(screen.getByRole("button", { name: /^cambia: M 42/i }))
    expect(campi()).toHaveLength(1)
    expect(nudi()).toEqual([])
  })

  it("ogni sezione e' una carta, nella colonna delle sezioni della pagina portata", async () => {
    // La pagina sta nella colonna del telaio (`app-pagina`), col guscio della tavola v82.
    conUnaDomanda()
    const sezione = await vaiASezione(/frame senza tipo/i)
    expect(sezione.className).toBe("al-conf__colonna-12")
    expect(sezione.parentElement?.className).toBe("al-conf__colonna-11")
    expect(sezione.closest(".al-conf__blocco-1")?.parentElement?.className).toBe("app-cornice app-pagina")
  })
})

describe("la veste", () => {
  it("chi guarda i mattoni vede davvero un campo scritto a mano", () => {
    // **La guardia vista rossa.** `fuoriDaiMattoni` e' cio' su cui poggiano le prove di veste del
    // primo avvio: se un giorno smettesse di vedere, quelle resterebbero verdi e nessuno se ne
    // accorgerebbe. E' gia' successo a lei: la prima versione cercava gli orfani **fra chi porta
    // gia' le classi del mattone**, quindi un `<label>` con un `<input>` nudi -- la regressione
    // esatta che deve impedire -- non aveva nessuna di quelle classi e la lasciava verde.
    document.body.innerHTML = `
      <label for="nudo">Latitudine</label><input id="nudo" />
      <button>Cerca</button>
      <div class="as-campo-modulo">
        <label class="as-campo-modulo__etichetta" for="vestito">Nome</label>
        <input class="as-campo-modulo__input" id="vestito" />
      </div>
      <button class="as-bottone" id="vestito-2">Avanti</button>
      <fieldset><input type="radio" id="scelta" /><label for="scelta">Non e' un oggetto</label></fieldset>
    `
    // i nudi e il grezzo si', il campo avvolto e il bottone vestito no, e la scelta -- che il
    // foglio non veste finche' non diventa segmentato -- nemmeno
    expect(fuoriDaiMattoni().sort()).toEqual(["Cerca", "Latitudine", "nudo"])
    document.body.innerHTML = ""
  })


  it("la testa e il corpo stanno nella colonna del telaio v76", async () => {
    aperta()
    await disegna()
    const pillole = await screen.findByRole("navigation", { name: "Navigazione principale" })
    const colonna = pillole.closest(".al-c-telaio__colonna-1")
    expect(colonna).not.toBeNull()
    expect(pillole.closest("header")?.className).toContain("al-c-telaio__riga-1")
    // la testa porta i token del foglio nuovo; il corpo no, o le pagine col foglio vecchio
    // prenderebbero il suo --inchiostro e il suo --linea
    expect(pillole.closest("[data-modo]")).not.toBeNull()
    const corpo = colonna?.querySelector(":scope > main") as HTMLElement
    expect(corpo).not.toBeNull()
    expect(corpo.closest("[data-modo]")).toBeNull()
  })

  it("il corpo e' il contenitore che le pagine col foglio vecchio misurano", async () => {
    // Il foglio vecchio si stringe con `@container telaio`: senza un contenitore con quel nome le
    // sue pagine non saprebbero di stare in un telefono.
    aperta()
    await disegna()
    expect((await screen.findByRole("main")).classList.contains("app-corpo")).toBe(true)
    const app = readFileSync(resolve(process.cwd(), "src", "stili", "app.css"), "utf-8")
    expect(app).toContain(".app-corpo {\n  container: telaio / inline-size;")
  })

  it("ogni pagina che esiste apre la sua colonna misurata", async () => {
    const esistenti = PAGINE.filter((p) => p.elemento !== undefined)
    expect(esistenti.length).toBeGreaterThan(0)
    for (const p of esistenti) {
      aperta()
      // si entra dall'indirizzo, non cliccando: e' cosi' che ci arriva anche chi apre un
      // collegamento, e la prova vale per ogni pagina futura senza sapere dove sta la sua voce
      window.history.pushState({}, "", p.a)
      await disegna()
      const corpo = await screen.findByRole("main")
      // il corpo del telaio tiene anche le righe di stato della scansione: la colonna e' la
      // pagina, figlia diretta del corpo
      // una pagina portata (le Notti) sta sotto il suo `Tema`, nella colonna del telaio
      await waitFor(() =>
        expect(
          corpo.querySelector(":scope > .as-pagina, :scope > [data-modo] > .app-pagina"),
          `${p.a} senza colonna`,
        ).not.toBeNull(),
      )
      pulisci()
    }
  })
})
