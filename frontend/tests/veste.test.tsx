// @vitest-environment jsdom
/**
 * La veste: il guscio che tiene lo scheletro, e la colonna misurata di ogni pagina.
 *
 * Qui non si prova che un colore sia bello -- quello e' il foglio, e il contrasto lo misura
 * `tools/controlli_veste.py` sui valori veri. Si prova cio' che **la pagina deve avere perche' il
 * foglio possa funzionare**, e che nessuna pagina nuova se lo dimentichi:
 *
 * - **il guscio esiste ed e' uno**: la barra, la testata e il contenuto stanno nella stessa
 *   griglia. Finche' erano tre fratelli sciolti non c'era nessun nodo su cui appenderla;
 * - **il contenitore misurato sta SOPRA il guscio**: un elemento non si stila dalla propria
 *   container query, quindi `.as-guscio-misura` deve essere il genitore e non il guscio stesso --
 *   sbagliarlo non rompe niente a schermo, la colonna stretta semplicemente non arriva mai;
 * - **ogni pagina apre la sua colonna**: `.as-pagina` e' il contenitore `colonna` da cui le righe
 *   e le tabelle sanno di essere strette. Una pagina che nasce senza non si accorge di niente
 *   finche' qualcuno non stringe la finestra.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { APERTE, GRUPPI, TITOLI } from "../src/pagine"
import { SALUTE, STANOTTE, disegna, fuoriDaiMattoni, impostazioni, pulisci, riga, rispondi, vaiASezione } from "./banco"

afterEach(pulisci)

const PAGINA = {
  seen: { objects: 0 },
  to_confirm: 0,
  lookalikes: [],
  filters: [],
  objects: [],
  mosaics: [],
  unclear: [],
  filter_choices: [],
  gear: [],
  rig_choices: [],
  typeless: [],
}

function aperta() {
  rispondi({
    ...STANOTTE,
    "/api/v1/review": { stato: 200, corpo: PAGINA },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/archive": { stato: 200, corpo: { items: [], total: 0 } },
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
        corpo: {
          ...PAGINA,
          to_confirm: 1,
          typeless: [{ key: CARTELLA, frames: 120, answer: null }],
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    })
  }

  it("il nome viene per primo, e staccato da cio' che lo segue", async () => {
    // Le prove trovano una riga dal testo con cui comincia, e chi ascolta la riconosce allo
    // stesso modo. Lo **spazio** e' la meta' che non si vede: col solo `gap` della griglia il
    // testo della riga sarebbe "D:/Astro/...dark120 frame", e a schermo sembrerebbe a posto.
    conUnaDomanda()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const voce = riga(sezione, CARTELLA)
    expect(voce.textContent?.startsWith(CARTELLA)).toBe(true)
    expect(voce.textContent).toContain(`${CARTELLA} `)
  })

  it("la riga a cui hai risposto lo dice con una forma, non con un colore", async () => {
    // WCAG 2.2, 1.4.1: chi non distingue i colori deve vedere lo stesso quali righe sta per
    // mandare. La barra piena a sinistra e' quella forma.
    conUnaDomanda()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const voce = riga(sezione, CARTELLA)
    const corpo = voce.querySelector(".as-riga")
    expect(corpo?.className).toBe("as-riga")
    fireEvent.click(within(voce).getByLabelText(/file di calibrazione/i))
    expect(voce.querySelector(".as-riga")?.className).toContain("as-riga--risposta")
  })

  it("cio' che si puo' fare sta nella colonna delle risposte", async () => {
    // `.as-riga` e' una griglia a due colonne: una risposta lasciata fuori finirebbe in mezzo
    // alla prosa, e in colonna stretta non scenderebbe sotto la domanda.
    conUnaDomanda()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const voce = riga(sezione, CARTELLA)
    const scelta = within(voce).getByLabelText(/file di calibrazione/i)
    expect(scelta.closest(".as-riga__risposte")).not.toBeNull()
  })

  it("i campi di due sezioni hanno il loro involucro, anche dietro un clic", async () => {
    // **Si guarda dopo aver aperto.** Meta' dei campi di questa pagina non esiste finche' non si
    // preme "Cambia" o "Completa la scheda": un conto fatto sulla pagina appena caricata torna
    // zero perche' non li vede, non perche' vanno bene -- ed e' cosi' che uno di questi campi e'
    // passato per due giri di revisione.
    // **Due sezioni, non tutte**: una pagina piena esiste gia' in `accessibilita.test.tsx`, e
    // ricopiarne qui la fixture sarebbe il doppione che questa fetta e' nata per togliere. Il
    // giorno che quella fixture vive nel banco, questa prova le passa davanti tutte (`docs/coda.md`).
    // Senza `.as-campo` (griglia) l'etichetta e il controllo diventano due elementi affiancati
    // dentro `.as-riga__risposte`, che e' un flex allineato a destra: lo stesso campo si dispone
    // in due modi nella stessa pagina.
    rispondi({
      ...STANOTTE,
      "/api/v1/review": {
        stato: 200,
        corpo: {
          ...PAGINA,
          to_confirm: 2,
          typeless: [{ key: "D:/Astro/2024-05-17/dark", frames: 12, answer: null }],
          // already a yes: its name field is open (the unnamed section left with ADR 0014 S3)
          mosaics: [
            { key: "impronta-m42", ra_deg: 83.8, dec_deg: -5.4, object: "M 42", panels: 3, frames: 90, integration_s: 10800, untimed: 0, answer: "yes", answer_name: "M 42", names: ["M 42"], proposed: "M 42" },
          ],
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    await screen.findByRole("region", { name: /mosaici/i })
    // si apre tutto cio' che si apre, e solo dopo si guarda
    const apre = /cambia|completa|dagli un nome/i
    for (const b of screen.queryAllByRole("button", { name: apre })) {
      fireEvent.click(b)
    }
    // che i campi ci siano davvero si guarda prima: `fuoriDaiMattoni` torna vuoto anche su una
    // pagina senza campi, e questa prova diventerebbe verde per il motivo sbagliato
    expect(
      document.querySelectorAll(".as-campo__etichetta, .as-campo__input, .as-scelta").length,
    ).toBeGreaterThan(0)
    expect(fuoriDaiMattoni()).toEqual([])
  })

  it("ogni sezione e' una carta, e il suo elenco sta nel corpo della carta", async () => {
    // Il corpo di una carta e' un contenitore **misurato**: le regole di colonna stretta delle
    // righe si misurano su di lui. Saltarlo non si vede finche' qualcuno non stringe la finestra,
    // e allora la soglia scatta sul numero sbagliato -- e' il foglio stesso ad avvisarne.
    conUnaDomanda()
    const sezione = await vaiASezione(/frame senza tipo/i)
    expect(sezione.className).toContain("as-carta")
    const elenco = sezione.querySelector("ul.as-elenco")
    expect(elenco?.parentElement?.className).toContain("as-carta__corpo")
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
      <div class="as-campo">
        <label class="as-campo__etichetta" for="vestito">Nome</label>
        <input class="as-campo__input" id="vestito" />
      </div>
      <button class="as-bottone" id="vestito-2">Avanti</button>
      <fieldset><input type="radio" id="scelta" /><label for="scelta">Non e' un oggetto</label></fieldset>
    `
    // i nudi e il grezzo si', il campo avvolto e il bottone vestito no, e la scelta -- che il
    // foglio non veste finche' non diventa segmentato -- nemmeno
    expect(fuoriDaiMattoni().sort()).toEqual(["Cerca", "Latitudine", "nudo"])
    document.body.innerHTML = ""
  })


  it("la barra, la testata e la pagina stanno nella stessa griglia", async () => {
    aperta()
    await disegna()
    const barra = await screen.findByRole("navigation")
    const guscio = barra.closest(".as-guscio")
    expect(guscio).not.toBeNull()
    expect(guscio?.querySelector("header.as-alto")).not.toBeNull()
    expect(guscio?.querySelector(".as-principale")).not.toBeNull()
  })

  it("il contenitore misurato e' il genitore del guscio, non il guscio", async () => {
    aperta()
    await disegna()
    const guscio = (await screen.findByRole("navigation")).closest(".as-guscio")
    expect(guscio?.classList.contains("as-guscio-misura")).toBe(false)
    expect(guscio?.parentElement?.classList.contains("as-guscio-misura")).toBe(true)
  })

  it("ogni gruppo della barra porta con se' il suo nome", async () => {
    // La barra ha perso `<ul>`/`<li>` per stare nella forma dei mattoni: questo e' cio' che tiene
    // in piedi la meta' che avevo promesso -- il nome del gruppo resta legato alle sue voci. Senza
    // la prova, toglierlo per sbaglio non farebbe cadere niente: axe non ha una regola per un
    // gruppo senza nome, e nessun'altra prova guarda qui.
    aperta()
    await disegna()
    const barra = await screen.findByRole("navigation")
    const guarda = within(barra).getByRole("group", { name: /guarda/i })
    expect(within(guarda).getByRole("link", { name: /archivio/i })).toBeDefined()
    // e i gruppi senza titolo non fingono di essere gruppi: un `group` senza nome non raccoglie
    // niente, aggiunge solo un livello. Quanti sono si conta dalle pagine che esistono, non a
    // mano: scritto come numero, cadrebbe il giorno che nasce una pagina, per la ragione sbagliata
    const conNome = GRUPPI.filter((g) => TITOLI[g] && APERTE.some((p) => p.gruppo === g))
    expect(within(barra).getAllByRole("group")).toHaveLength(conNome.length)
    expect(within(barra).getByRole("link", { name: /casa/i })).toBeDefined()
  })

  it("ogni pagina che esiste apre la sua colonna misurata", async () => {
    for (const p of APERTE) {
      aperta()
      // si entra dall'indirizzo, non cliccando: e' cosi' che ci arriva anche chi apre un
      // collegamento, e la prova vale per ogni pagina futura senza sapere dove sta la sua voce
      window.history.pushState({}, "", p.a)
      await disegna()
      await waitFor(() => expect(document.querySelector("main")).not.toBeNull())
      const dentro = document.querySelector("main")
      expect(dentro?.classList.contains("as-pagina"), `${p.a} senza colonna`).toBe(true)
      pulisci()
    }
  })
})
