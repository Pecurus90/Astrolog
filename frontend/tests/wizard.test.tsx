// @vitest-environment jsdom
/**
 * Il primo avvio: le sue domande, e poi si toglie di mezzo.
 *
 * test-tolto: "ogni campo e ogni bottone dei tre passi passa dal suo mattone" -- rinominata: i passi sono quattro
 * test-tolto: "senza il timbro l app mostra le tre domande, non il contatore" -- rinominata: le domande sono quattro
 *
 * Non e' un indirizzo, e' un **cancelletto**: se il timbro non c'e' l'app mostra il primo avvio,
 * altrimenti mostra se stessa. Il perche' e le conseguenze stanno nel contratto
 * (`docs/domini/sito.md`), che e' la loro casa; qui si prova che il codice le rispetti.
 *
 * Ogni prova qui sotto guarda una regola che, rotta, deve far diventare rosso **questo** file.
 * Il banco sta in `banco.tsx`: rifiuta le rotte che non gli sono state dichiarate, quindi
 * "questa chiamata non doveva partire" e' dimostrabile e non solo sperabile.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, cambia, chiamate, disegna, fuoriDaiMattoni, impostazioni, nomiDeiPassi, pulisci, quantiControlli, rispondi, scritture } from "./banco"

afterEach(pulisci)


/** Le rotte che l'app puo' chiedere **dopo** il timbro. Prima non deve chiederle: il primo avvio
 *  non mostra ne' il contatore ne' la salute, e a mani vuote sarebbero richieste che nessuno
 *  legge. */
const DOPO = {
  "/api/v1/review": { stato: 200, corpo: { to_confirm: 7 } },
  "/api/health": { stato: 200, corpo: SALUTE },
  ...SPINA,
}

/** Le risposte dell'API con o senza il timbro. Le rotte piu' lunghe stanno davanti: il banco
 *  sceglie la prima che l'indirizzo contiene, e `/api/v1/settings` ingoierebbe il timbro. */
function conTimbro(fatto: boolean, extra: Record<string, { stato: number; corpo: unknown }> = {}) {
  rispondi({
    ...STANOTTE,
    // Il terzo passo chiede sempre queste due: dove stanno i dati (per sapere se le cartelle si
    // scelgono o si scrivono) e quelle gia' registrate, che mostra in elenco.
    "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
    "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(fatto) },
    ...extra,
    ...(fatto ? DOPO : {}),
  })
}

/** Porta il primo avvio al passo chiesto (0 = il primo). */
function vaiAlPasso(n: number) {
  for (let i = 0; i < n; i++) fireEvent.click(screen.getByRole("button", { name: /avanti/i }))
}

describe("il primo avvio", () => {
  it("senza il timbro l app mostra le sue domande, non il contatore", async () => {
    conTimbro(false)
    await disegna()
    expect(await screen.findByRole("button", { name: /salta/i })).toBeDefined()
    expect(screen.queryByText(/^da confermare$/)).toBeNull()
  })

  it("col timbro l app mostra se stessa e non richiede niente", async () => {
    conTimbro(true)
    await disegna()
    expect(await within(await screen.findByRole("main")).findByText("7")).toBeDefined()
    expect(screen.queryByRole("button", { name: /salta/i })).toBeNull()
    // E soprattutto: il timbro e' stato **letto**. Senza questa riga il test sarebbe verde anche
    // se l'app ignorasse del tutto `wizard_done` -- infatti lo era, prima che il primo avvio
    // esistesse, perche' i due rami mostrano tutti e due il contatore.
    expect(chiamate().some((u) => u.includes("/api/v1/settings"))).toBe(true)
  })

  it("se le impostazioni non rispondono non si tira a indovinare", async () => {
    // Le due scelte sbagliate sono simmetriche: mostrare l'app direbbe "tutto configurato"
    // senza saperlo, mostrare il primo avvio rifarebbe domande gia' risposte. Si dice che non
    // si sa, e basta.
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 500, corpo: { detail: { code: "rotto" } } },
      ...DOPO,
    })
    await disegna()
    const avviso = await screen.findByRole("alert")
    expect(avviso.textContent).toContain("Il servizio non ha risposto")
    expect(screen.queryByText(/^da confermare$/)).toBeNull()
    expect(screen.queryByRole("button", { name: /salta/i })).toBeNull()
  })

  it("si salta da OGNI passo, non solo dal primo", async () => {
    conTimbro(false)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    for (let passo = 1; passo <= 2; passo++) {
      vaiAlPasso(1)
      expect(screen.queryByRole("button", { name: /salta/i })).not.toBeNull()
    }
  })

  it("saltare TIMBRA: domani l app non rifa le stesse domande", async () => {
    // La meta' che si dimentica. "Si salta sempre" senza il timbro non e' saltare, e' rimandare
    // a ogni avvio: il contratto dice che completare e saltare scrivono **lo stesso** timbro.
    conTimbro(false)
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: /salta/i }))
    await waitFor(() =>
      expect(chiamate().some((u) => u.includes("/settings/wizard-done"))).toBe(true),
    )
  })

  it("e dopo il timbro il primo avvio si toglie davvero di mezzo", async () => {
    // L'altra meta' della stessa promessa: scrivere il timbro e restare fermi nel wizard
    // sarebbe la stessa prigione, con una riga in piu' nel database.
    conTimbro(false)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    cambia({
      "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
      "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      ...DOPO,
    })
    fireEvent.click(screen.getByRole("button", { name: /salta/i }))
    // Prima si aspetta l'app -- la barra c'e' solo dopo il timbro -- e poi si guarda dentro il
    // contenuto: cercando subito, il `main` trovato e' ancora quello del primo avvio.
    await screen.findByRole("navigation")
    expect(await within(screen.getByRole("main")).findByText("7")).toBeDefined()
  })

  it("il primo passo chiede il nome, e quello che scrivo viene salvato", async () => {
    conTimbro(false)
    await disegna()
    fireEvent.change(await screen.findByLabelText(/^nome$/i), {
      target: { value: "Marco" },
    })
    vaiAlPasso(1)
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/settings"))
      expect(scritta?.corpo).toEqual({ values: { user_name: "Marco" } })
    })
  })

  it("il terzo passo guarda la cartella prima di registrarla, e dice quanti file", async () => {
    conTimbro(false, {
      "/api/v1/folders/probe": {
        stato: 200,
        corpo: { root_path: "D:/Astro", reachable: true, fits_count: 10957, complete: true },
      },
      "/api/v1/folders": { stato: 201, corpo: { id: 1, name: null, root_path: "D:/Astro" } },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(2)
    fireEvent.change(screen.getByLabelText(/percorso della cartella/i), {
      target: { value: "D:/Astro" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica$/i }))
    // Il numero si vede **prima** di registrare: e' cosi' che si capisce di aver puntato la
    // cartella giusta invece di scoprirlo a scansione finita.
    expect(await screen.findByText(/10\.957 file FITS/)).toBeDefined()
    fireEvent.click(screen.getByRole("button", { name: /aggiungi cartella/i }))
    await waitFor(() => {
      const scritta = scritture().find(
        (s) => s.url.includes("/api/v1/folders") && !s.url.includes("probe"),
      )
      expect(scritta?.corpo).toMatchObject({ root_path: "D:/Astro" })
    })
  })

  it("una conta fermata dal tempo si dice come minimo, non come totale", async () => {
    // Il "non lo so" che il backend produce DAVVERO non e' `fits_count` nullo -- quello arriva
    // solo con la cartella irraggiungibile (`backend/astrolog/api/folders.py`) -- ma
    // `complete: false`: la conta si e' fermata al suo tetto di tempo, quindi il numero e' un
    // **minimo**. Mostrarlo come totale su un archivio lento e' la stessa bugia tranquillizzante
    // dello zero, spostata di un campo.
    conTimbro(false, {
      "/api/v1/folders/probe": {
        stato: 200,
        corpo: { root_path: "D:/Astro", reachable: true, fits_count: 10957, complete: false },
      },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(2)
    fireEvent.change(screen.getByLabelText(/percorso della cartella/i), {
      target: { value: "D:/Astro" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica$/i }))
    expect(await screen.findByText(/conteggio interrotto a/i)).toBeDefined()
    expect(screen.getByText(/957/)).toBeDefined()
  })

  it("una cartella che non si registra non fa timbrare il primo avvio", async () => {
    // Timbrare dopo una scrittura fallita e' la trappola peggiore di tutte: l'utente esce dal
    // primo avvio senza niente di fatto, e non puo' rientrarci -- le Impostazioni non esistono.
    conTimbro(false, {
      "/api/v1/folders/probe": {
        stato: 200,
        corpo: { root_path: "D:/Astro", reachable: true, fits_count: 12, complete: true },
      },
      "/api/v1/folders": { stato: 500, corpo: { detail: { code: "rotto" } } },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(2)
    fireEvent.change(screen.getByLabelText(/percorso della cartella/i), {
      target: { value: "D:/Astro" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica$/i }))
    fireEvent.click(await screen.findByRole("button", { name: /aggiungi cartella/i }))
    expect(await screen.findByRole("alert")).toBeDefined()
    expect(chiamate().some((u) => u.includes("/settings/wizard-done"))).toBe(false)
  })

  it("una cartella irraggiungibile non si puo nemmeno aggiungere", async () => {
    // Dirlo e poi offrire lo stesso il tasto per registrarla sarebbe un invito a sbagliare.
    conTimbro(false, {
      "/api/v1/folders/probe": {
        stato: 200,
        corpo: { root_path: "Z:/via", reachable: false, fits_count: null, complete: null },
      },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(2)
    fireEvent.change(screen.getByLabelText(/percorso della cartella/i), {
      target: { value: "Z:/via" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica$/i }))
    expect(await screen.findByText(/cartella non raggiungibile/i)).toBeDefined()
    expect(screen.queryByRole("button", { name: /aggiungi cartella/i })).toBeNull()
  })

  it("una sonda che non riesce a guardare lo dice", async () => {
    // Raggiungibile davvero: un percorso relativo prende 422 `path_not_absolute`. Senza questa
    // riga il clic su "Guarda" non produrrebbe nulla e sembrerebbe un tasto rotto.
    conTimbro(false, {
      "/api/v1/folders/probe": { stato: 422, corpo: { detail: [{ msg: "path_not_absolute" }] } },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(2)
    fireEvent.change(screen.getByLabelText(/percorso della cartella/i), {
      target: { value: "casa" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica$/i }))
    expect(await screen.findByRole("alert")).toBeDefined()
  })

  it("se le impostazioni non accettano il nome, non si va avanti fingendo", async () => {
    // La rotta si legge e si scrive: deve rispondere BENE in lettura (o il primo avvio non
    // comparirebbe) e MALE in scrittura. Per questo il banco distingue il metodo.
    conTimbro(false, {
      "PATCH /api/v1/settings": { stato: 500, corpo: { detail: { code: "rotto" } } },
    })
    await disegna()
    fireEvent.change(await screen.findByLabelText(/^nome$/i), { target: { value: "Marco" } })
    fireEvent.click(screen.getByRole("button", { name: /avanti/i }))
    expect(await screen.findByRole("alert")).toBeDefined()
    expect(screen.getByLabelText(/^nome$/i)).toBeDefined()
  })

  it("il binario dice davvero come si chiamano i passi, e quale sono", async () => {
    // La meta' positiva della promessa: che non ci sia una percentuale lo prova gia' un'altra
    // riga, ma se i nomi sparissero o il segno del passo corrente non si spostasse, il binario
    // non direbbe piu' niente e nessuna prova cadrebbe.
    conTimbro(false)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    expect(nomiDeiPassi()).toEqual(["Nome utente", "Sito di osservazione", "Percorso dei file", "Seeing (Meteoblue)"])
    const corrente = () =>
      screen.getAllByRole("listitem").findIndex((li) => li.getAttribute("aria-current") === "step")
    expect(corrente()).toBe(0)
    vaiAlPasso(1)
    expect(corrente()).toBe(1)
  })

  it("una tappa dice a che punto e', e non col solo colore", async () => {
    // Le tre forme del binario sono la promessa di questa veste, e nessuna prova le guardava:
    // il segno e' `aria-hidden`, quindi chi ascolta ha solo la parola -- e chi non distingue i
    // colori ha solo la forma. Se domani sparisse una delle due, la suite resterebbe verde.
    conTimbro(false)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    const tappe = () => [...document.querySelectorAll(".as-passi__tappa")]

    // al primo passo: nessuna fatta, la prima e' quella di adesso e lo dice a parole
    expect(tappe().map((t) => t.className.includes("as-passi__tappa--fatto"))).toEqual([
      false,
      false,
      false,
      false,
    ])
    expect(tappe()[0]?.textContent).toContain("sei qui")
    expect(tappe()[1]?.textContent).not.toContain("sei qui")
    // e quelle che vengono non dicono niente: dirlo sarebbe rumore su cio' che non e' successo
    expect(tappe()[2]?.textContent?.trim()).toBe("3Percorso dei file")

    vaiAlPasso(1)
    // la prima ora e' fatta, e lo dice in tutti e tre i modi: il segno, la forma, la parola.
    // Il segno **per intero**, non "contiene": lasciando il numero al posto della spunta la
    // tappa fatta direbbe "1" e senza questa riga la suite non se ne accorgerebbe.
    expect(tappe()[0]?.textContent?.trim()).toBe("\u2713Nome utente - fatto")
    expect(tappe()[0]?.className).toContain("as-passi__tappa--fatto")
    expect(tappe()[1]?.textContent).toContain("sei qui")
  })

  it("il movimento d'apertura non riparte tornando indietro", async () => {
    // Un ingresso si vede **una volta**: se la classe si togliesse e si rimettesse al variare del
    // passo, premere Indietro la farebbe ripartire -- e la promessa scritta nel foglio ("passare
    // dal passo 2 al 3 non porta .as-entra") sarebbe falsa proprio dove si torna indietro.
    conTimbro(false)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    const entrano = () => document.querySelectorAll(".as-entra").length
    const quanti = entrano()
    expect(quanti).toBeGreaterThan(0)
    vaiAlPasso(1)
    expect(entrano()).toBe(quanti)
    fireEvent.click(screen.getByRole("button", { name: /indietro/i }))
    expect(entrano()).toBe(quanti)
  })

  it("Indietro riporta al passo di prima", async () => {
    conTimbro(false)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    expect(screen.getByLabelText(/localit\u00e0/i)).toBeDefined()
    fireEvent.click(screen.getByRole("button", { name: /indietro/i }))
    expect(screen.getByLabelText(/^nome$/i)).toBeDefined()
  })

  it("la riga sulle notti sta dove e vera, non su ogni passo", async () => {
    // Visto a schermo collaudando il 14/9/2026: al terzo passo il luogo e' appena stato
    // dichiarato, e ripetere li' "senza un luogo le notti non nascono" dice il falso proprio a
    // chi ha appena fatto la cosa giusta. Una frase vale dove e' vera.
    conTimbro(false)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(1)
    expect(screen.getByText(/calcolare le notti/i)).toBeDefined()
    vaiAlPasso(1)
    expect(screen.queryByText(/calcolare le notti/i)).toBeNull()
  })

  it("ogni passo dice a che punto sei e perche' l app chiede", async () => {
    // Due cose che il disegno mette in cima e che senza prova si possono togliere senza che
    // niente cada: il conto dei passi (chi entra deve sapere quanto manca) e la riga che spiega
    // **perche'** l'app chiede quella cosa.
    //
    // Si guardano **tutti e quattro** i passi, non i primi due: la riga del terzo era sbagliata e
    // nessuno se n'era accorto, perche' la prova si fermava prima di arrivarci. E si guarda che
    // stia **nell'intestazione della carta**, non solo che sia a schermo da qualche parte:
    // spostata nel corpo, la pagina direbbe la domanda prima della ragione -- che e' il contrario
    // di cio' che il disegno fa -- e una prova sulla sola presenza resterebbe verde.
    conTimbro(false, {
      "/api/v1/settings": {
        stato: 200,
        corpo: { ...impostazioni(false), missing: ["no_active_site", "no_solver"] },
      },
    })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })

    const perche = () =>
      document.querySelector(".as-carta__intestazione .as-carta__domanda")?.textContent ?? ""
    const attesi = [
      /intestare le statistiche/i,
      /calcolare le notti/i,
      /indica una cartella/i,
      /chiave API Meteoblue/i,
      /ASTAP non \u00e8 installato/i,
    ]
    for (const [i, atteso] of attesi.entries()) {
      expect(screen.getByText(new RegExp(`passo ${i + 1} di 5`, "i"))).toBeDefined()
      expect(perche()).toMatch(atteso)
      if (i < attesi.length - 1) vaiAlPasso(1)
    }
  })

  it("ogni campo e ogni bottone dei quattro passi passa dal suo mattone", async () => {
    // I mattoni esistono perche' la stessa classe non finisca scritta a mano in dodici file, e la
    // sola macchina che lo impedisce guarda le classi **dei mattoni** (`tools/controlli_veste.py`):
    // un campo o un bottone che i mattoni non li usa affatto non e' una classe fuori casa, e li'
    // non si vede. Qui si guarda l'altra meta': cio' che a schermo e' rimasto grezzo.
    // Si attraversano i quattro passi perche' i campi di questa pagina non esistono tutti insieme --
    // sei dei sette compaiono uno passo per volta, e un conto fatto sul primo torna zero perche'
    // non li vede.
    conTimbro(false)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    for (const passo of [0, 1, 2, 3]) {
      // che ci sia qualcosa da guardare si afferma **prima**. Il conto e' sempre almeno due --
      // il piede porta *Salta* e *Avanti* su ogni schermata -- quindi qui la soglia e' piu' alta:
      // ogni passo ha un controllo **suo**, e senza di quello si sta guardando un'altra pagina.
      expect(quantiControlli(), `al passo ${passo}`).toBeGreaterThan(3)
      expect(fuoriDaiMattoni(), `al passo ${passo}`).toEqual([])
      if (passo < 3) vaiAlPasso(1)
    }
  })

  it("si completa, e completare timbra come saltare", async () => {
    conTimbro(false)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    vaiAlPasso(3)
    // All'ultimo passo "Avanti" non ha piu' senso: al suo posto c'e' la fine.
    expect(screen.queryByRole("button", { name: /avanti/i })).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /^fine$/i }))
    await waitFor(() =>
      expect(chiamate().some((u) => u.includes("/settings/wizard-done"))).toBe(true),
    )
  })
})
