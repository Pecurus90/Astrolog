// @vitest-environment jsdom
/**
 * Il **pannello della Luna**: cio' che in 227px non ci sta, e che si apre dalla striscia.
 *
 * Le regole provate qui sono quelle che una lettura del codice non prende: che la Luna sia **un**
 * bersaglio e non tre, che il pannello porti il numero che in barra manca -- quanto sale -- che
 * cio' che stanotte non succede resti una frase, e che il cielo dietro la curva porti **le fasce
 * che quella notte ha davvero**.
 */
process.env.TZ = "UTC"

import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { FERMO, SALUTE, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

const LUNA = {
  phase_key: "waxing_gibbous",
  illumination_pct: 60,
  rise: "2026-09-19T15:49:26.241398+02:00",
  set: "2026-09-19T23:48:58.203956+02:00",
  highest: { at: "2026-09-19T19:48:00+02:00", altitude_deg: 16.1 },
  // Una notte come arriva davvero: a passo di un quarto d'ora da mezzogiorno a mezzogiorno,
  // quindi con le ore tonde fra i campioni. Qui ce ne stanno quelle che servono all'asse.
  track: [
    { at: "2026-09-19T12:00:00+02:00", altitude_deg: -35.8 },
    { at: "2026-09-19T18:00:00+02:00", altitude_deg: 10.0 },
    { at: "2026-09-19T19:48:00+02:00", altitude_deg: 16.1 },
    { at: "2026-09-20T00:00:00+02:00", altitude_deg: 8.0 },
    { at: "2026-09-20T06:00:00+02:00", altitude_deg: -30.0 },
    { at: "2026-09-20T12:00:00+02:00", altitude_deg: -43.4 },
  ],
  ceiling_deg: 75,
  lit_side: "right",
}

/** Le fasce come le manda la rotta: attaccate, e tutte e cinque nella sera. */
const FASCE = [
  { starts_at: "2026-09-19T12:00:00+02:00", ends_at: "2026-09-19T19:00:00+02:00", kind: "day" },
  { starts_at: "2026-09-19T19:00:00+02:00", ends_at: "2026-09-19T19:30:00+02:00", kind: "civil" },
  { starts_at: "2026-09-19T19:30:00+02:00", ends_at: "2026-09-19T20:00:00+02:00", kind: "nautical" },
  { starts_at: "2026-09-19T20:00:00+02:00", ends_at: "2026-09-19T20:30:00+02:00", kind: "astronomical" },
  { starts_at: "2026-09-19T20:30:00+02:00", ends_at: "2026-09-20T05:00:00+02:00", kind: "dark" },
  { starts_at: "2026-09-20T05:00:00+02:00", ends_at: "2026-09-20T05:30:00+02:00", kind: "astronomical" },
  { starts_at: "2026-09-20T05:30:00+02:00", ends_at: "2026-09-20T06:00:00+02:00", kind: "nautical" },
  { starts_at: "2026-09-20T06:00:00+02:00", ends_at: "2026-09-20T06:30:00+02:00", kind: "civil" },
  { starts_at: "2026-09-20T06:30:00+02:00", ends_at: "2026-09-20T12:00:00+02:00", kind: "day" },
]

function app(luna: unknown = LUNA, fasce: unknown = FASCE) {
  rispondi({
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": {
      stato: 200,
      corpo: { to_confirm: 0 },
    },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/pipeline/status": { stato: 200, corpo: FERMO },
    "/api/v1/tonight": {
      stato: 200,
      corpo: {
        night: "2026-09-19",
        site: { name: "Vicenza", sky_sqm: 20.8, bortle: 4 },
        moon: luna,
        sky_bands: fasce,
      },
    },
  })
  return disegna()
}

/** La striscia, che e' il bottone che apre. */
async function striscia() {
  return screen.findByRole("button", { name: /gibbosa crescente/i })
}

describe("il pannello della Luna", () => {
  it("la Luna e un bersaglio solo, e apre il pannello", async () => {
    // Disco, grafico e orari sarebbero tre soste di tabulatore per una cosa sola. E il bottone
    // dice che apre una finestra, invece di lasciarlo indovinare.
    await app()
    const apre = await striscia()
    expect(apre.getAttribute("aria-haspopup")).toBe("dialog")
    expect(within(apre).queryAllByRole("button")).toHaveLength(0)
    expect(screen.queryByRole("dialog")).toBeNull()

    fireEvent.click(apre)
    expect(await screen.findByRole("dialog")).toBeTruthy()
  })

  it("il pannello porta il numero che in barra non ci sta", async () => {
    // **Quanto** sale decide la notte: una piena che resta bassa disturba meno di una mezza che
    // passa allo zenit. In 227px c'e' solo la gobba, qui c'e' il numero.
    await app()
    fireEvent.click(await striscia())

    const pannello = await screen.findByRole("dialog")
    // "sale fino a", non "culmina": il massimo della notte non e' sempre una culminazione vera,
    // ed e' una parola decisa in `docs/domini/glossario.md`
    expect(within(pannello).getByText(/sale fino a/i)).toBeTruthy()
    expect(pannello.textContent).not.toMatch(/culmina/i)
    expect(pannello.textContent).toMatch(/16,1 gradi/)
    expect(pannello.textContent).toMatch(/alle 19:48/)
  })

  it("i tre orari ci sono, e quello che non succede resta una frase", async () => {
    // Mai un trattino e mai un'ora finta: una Luna che non sorge e' un fatto, non un buco.
    await app({ ...LUNA, rise: null })
    fireEvent.click(await striscia())

    const pannello = await screen.findByRole("dialog")
    expect(within(pannello).getByText(/^non sorge$/i)).toBeTruthy()
    expect(pannello.textContent).toMatch(/tramonta/i)
    expect(pannello.textContent).toMatch(/23:48/)
  })

  it("il cielo sta dietro la curva, con la fascia che ogni pezzo di notte ha davvero", async () => {
    // Le fasce arrivano gia' divise dalla rotta: la tela le dipinge e basta. Stanno **dietro**,
    // perche' sono il fondo su cui passa la Luna -- disegnate dopo, coprirebbero la curva.
    await app()
    fireEvent.click(await striscia())

    const pannello = await screen.findByRole("dialog")
    const tela = pannello.querySelector(".as-grafico__tela--alta")!
    const dipinte = [...tela.querySelectorAll("rect[class*='as-fascia']")].map((r) => r.getAttribute("class"))
    // la sera scende per le cinque fasce e la mattina risale: nove pezzi, come una notte vera
    expect(dipinte).toEqual([
      "as-fascia--giorno",
      "as-fascia--civile",
      "as-fascia--nautico",
      "as-fascia--astronomico",
      "as-fascia--notte",
      "as-fascia--astronomico",
      "as-fascia--nautico",
      "as-fascia--civile",
      "as-fascia--giorno",
    ])
    // dietro la curva: nel documento vengono prima
    const primaFascia = tela.querySelector("rect[class*='as-fascia']")!
    const curva = tela.querySelector(".as-grafico__luna")!
    expect(primaFascia.compareDocumentPosition(curva) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it("i due istanti che chiudono il buio sono segnati, che la fascia non si vede", async () => {
    // Nel tema di casa `--fascia-notte` e' **trasparente**: la fascia che tutto questo esiste per
    // mostrare non dipinge niente, e senza i due segni la finestra che conta si leggerebbe solo
    // dal bordo della fascia accanto. Il foglio li chiama "istanti operativi" e gli da' l'accento.
    await app()
    fireEvent.click(await striscia())

    const tela = (await screen.findByRole("dialog")).querySelector(".as-grafico__tela--alta")!
    const accenti = [...tela.querySelectorAll(".as-grafico__istante")].map((l) => l.getAttribute("x1"))
    expect(accenti).toHaveLength(2)
    // e dove va l'accento non va anche il capello, **da tutte e due le parti**: due segni
    // sovrapposti fanno una tinta che il foglio non ha disegnato, perche' l'accento e'
    // semitrasparente. Il banco ha il buio **in mezzo** apposta: con il buio per ultimo il bordo
    // destro non esisterebbe e meta' della regola non verrebbe mai eseguita.
    const capelli = [...tela.querySelectorAll(".as-grafico__confine")].map((l) => l.getAttribute("x1"))
    expect(capelli).toHaveLength(6)
    for (const accento of accenti) {
      expect(capelli).not.toContain(accento)
    }
  })

  it("chi non vede la tela legge il buio, che e il dato che le fasce mostrano", async () => {
    // Senza questa frase le fasce sarebbero **solo un colore**: il nome della figura diceva quanto
    // sale la Luna e nient'altro.
    await app()
    fireEvent.click(await striscia())

    const tela = (await screen.findByRole("dialog")).querySelector(".as-grafico__tela--alta")!
    expect(tela.getAttribute("aria-label")).toMatch(/il buio va dalle 20:30 alle 05:00/i)
  })

  it("una notte senza fasce non se ne inventa una piatta", async () => {
    // Un sito senza fuso non ha una notte da dividere, e la rotta manda l'elenco vuoto: la tela
    // resta senza fondo invece di dipingere "giorno" per ventiquattro ore.
    await app(LUNA, [])
    fireEvent.click(await striscia())

    const pannello = await screen.findByRole("dialog")
    expect(pannello.querySelectorAll("[class*='as-fascia']")).toHaveLength(5) // solo la legenda
    expect(pannello.querySelectorAll(".as-grafico__tela--alta [class*='as-fascia']")).toHaveLength(0)
  })

  it("la legenda e scritta, che un colore da solo non dice niente", async () => {
    await app()
    fireEvent.click(await striscia())

    const pannello = await screen.findByRole("dialog")
    expect(within(pannello).getByText(/la luna/i)).toBeTruthy()
    expect(within(pannello).getByText(/^adesso$/i)).toBeTruthy()
    expect(within(pannello).getByText(/sotto l'orizzonte/i)).toBeTruthy()
    // la quarta voce, quella delle fasce: i cinque rettangoli sono `aria-hidden`, quindi senza la
    // sua parola la rampa sarebbe **solo colore** -- che e' proprio cio' che la legenda impedisce
    expect(within(pannello).getByText(/dal giorno al buio/i)).toBeTruthy()
  })

  it("la tela grande ha il suo asse, e quella in barra no", async () => {
    // Sotto la tela del pannello ci sono le **ore tonde**, non due volte lo stesso mezzogiorno; in
    // barra non c'e' nessuna scritta, che a quell'altezza coprirebbe la curva invece di spiegarla.
    await app()
    const apre = await striscia()
    const inBarra = document.querySelector(".as-grafico__tela--bassa")
    expect(inBarra).not.toBeNull()
    expect(inBarra?.querySelectorAll("text")).toHaveLength(0)

    fireEvent.click(apre)
    const pannello = await screen.findByRole("dialog")
    const ore = [...pannello.querySelectorAll(".as-grafico__tela--alta text")].map(
      (e) => e.textContent,
    )
    expect(ore).toContain("00:00")
    expect(ore.filter((o) => o === "12:00")).toHaveLength(2)
    // e si scrivono **sopra la fascia**: cadono dentro il terreno, dove l'inchiostro debole fa
    // 4,30:1. Il contrasto dei due colori lo misura `tools/controlli_contrasto.py`; che le ore li
    // usino davvero lo tiene ferma questa riga, e nient'altro -- axe il testo dentro un SVG non
    // lo guarda.
    const tacche = [...pannello.querySelectorAll(".as-grafico__tela--alta text")].filter((e) =>
      /^[0-9][0-9]:[0-9][0-9]$/.test(e.textContent ?? ""),
    )
    expect(tacche).toHaveLength(5)
    expect(
      tacche.every((e) => e.classList.contains("as-grafico__etichetta--sopra-fascia")),
    ).toBe(true)
  })

  it("il pannello e' largo, che una tela intera nella misura normale si rimpicciolisce", async () => {
    // E' l'unica ragione per cui il dialogo ha una misura larga: senza, la tela da 480 si scala e
    // le etichette si rimpiccioliscono con lei -- cioe' non sono piu' quelle che il design ha
    // misurato.
    await app()
    fireEvent.click(await striscia())

    const pannello = await screen.findByRole("dialog")
    expect(pannello.className).toContain("as-dialogo--largo")
  })

  it("chiudendo, il fuoco torna alla striscia da cui si era aperto", async () => {
    // Senza, chi si muove a tastiera riparte dall'inizio della pagina ogni volta che guarda la
    // Luna.
    await app()
    const apre = await striscia()
    // come chi ci arriva a tastiera: il bersaglio e' gia' sotto il fuoco quando si preme
    apre.focus()
    fireEvent.click(apre)
    await screen.findByRole("dialog")

    fireEvent.click(screen.getByRole("button", { name: /chiudi/i }))
    expect(screen.queryByRole("dialog")).toBeNull()
    expect(document.activeElement).toBe(apre)
  })
})
