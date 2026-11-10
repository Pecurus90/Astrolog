// @vitest-environment jsdom
/**
 * The v58 bricks (`src/componenti/`), before any page mounts them (step 32): classes of the new
 * sheet for every variant, words from t(), sign and word together, roles, and the window's keys.
 *
 * Colour is not tested here: jsdom has no cascade. That every `al-*` written exists in the sheet
 * is `tools/controlli_veste.py`'s job.
 */
import { readFileSync } from "node:fs"
import { resolve } from "node:path"

import { fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { Avviso } from "../src/componenti/Avviso"
import { Carta } from "../src/componenti/Carta"
import { Finestra } from "../src/componenti/Finestra"
import { Pillola } from "../src/componenti/Pillola"
import { PillolaScelta } from "../src/componenti/PillolaScelta"
import { Scheletro } from "../src/componenti/Scheletro"
import { Tema } from "../src/componenti/Tema"
import { t } from "../src/i18n"
import { pulisci } from "./banco"

afterEach(pulisci)

describe("Tema", () => {
  it("starts dark and amber, and wraps without a box", () => {
    const { container } = render(<Tema>x</Tema>)
    const involucro = container.firstElementChild as HTMLElement
    expect(involucro.dataset["modo"]).toBe("scuro")
    expect(involucro.dataset["accento"]).toBe("ambra")
    expect(involucro.style.display).toBe("contents")
  })

  it("hands its mode and accent to the bricks inside", () => {
    const { container } = render(
      <Tema modo="chiaro" accento="ghiaccio">
        <Pillola esito={0} />
      </Tema>,
    )
    const blocco = container.querySelector(".al-c-pillola__blocco-1") as HTMLElement
    expect(blocco.dataset["modo"]).toBe("chiaro")
    expect(blocco.dataset["accento"]).toBe("ghiaccio")
  })
})

describe("Avviso", () => {
  const forme = [
    ["pagina", "desktop", "al-c-avviso__griglia-1", "al-c-avviso__tondo-1"],
    ["pagina", "telefono", "al-c-avviso__colonna-2", "al-c-avviso__tondo-2"],
    ["blocco", "desktop", "al-c-avviso__griglia-2", "al-c-avviso__tondo-3"],
    ["blocco", "telefono", "al-c-avviso__colonna-3", "al-c-avviso__tondo-4"],
    ["riga", "desktop", "al-c-avviso__riga-3", "al-c-avviso__tondo-5"],
    ["riga", "telefono", "al-c-avviso__colonna-4", "al-c-avviso__tondo-6"],
  ] as const

  it.each(forme)(
    "%s on %s wears its own classes and says status",
    (tipo, formato, involucro, tondo) => {
      render(<Avviso tipo={tipo} formato={formato} titolo="Meteo non raggiungibile" />)
      const avviso = screen.getByRole("status")
      expect(avviso.className).toBe(involucro)
      expect(avviso.querySelector(`.${tondo}`)?.textContent).toBe("!")
      expect(avviso.textContent).toContain("Meteo non raggiungibile")
    },
  )

  it("the sign is hidden from who listens, and never comes alone", () => {
    render(<Avviso segno={"✓"} titolo="Fatto" />)
    const segno = screen.getByRole("status").querySelector('[aria-hidden="true"]')
    expect(segno?.textContent).toBe("✓")
    expect(screen.getByRole("status").textContent).toContain("Fatto")
  })

  it("each sign takes its colours from the sheet's tokens", () => {
    const segni = [
      ["!", "var(--avviso)"],
      ["?", "var(--carta)"],
      ["✓", "var(--buono-fondo)"],
    ] as const
    for (const [segno, fondo] of segni) {
      const { unmount } = render(<Avviso segno={segno} titolo="x" />)
      const tondo = screen.getByRole("status").querySelector<HTMLElement>('[aria-hidden="true"]')
      expect(tondo?.style.background, segno).toBe(fondo)
      unmount()
    }
  })

  it("the action is a button of the sheet, and it calls back", () => {
    const azione = vi.fn()
    render(<Avviso titolo="x" testo="dettaglio" azione="Riprova ora" onAzione={azione} />)
    const bottone = screen.getByRole("button", { name: "Riprova ora" })
    expect(bottone.className).toBe("al-bottone al-bottone--contorno")
    fireEvent.click(bottone)
    expect(azione).toHaveBeenCalledOnce()
    expect(screen.getByText("dettaglio").className).toBe("al-c-avviso__testo-2")
  })
})

describe("Pillola", () => {
  it.each([
    [0, "al-pillola--buona", "✓", "ui.outcome.good"],
    [1, "al-pillola--incerta", "!", "ui.outcome.uncertain"],
    [2, "al-pillola--non-adatta", "✕", "ui.outcome.unsuitable"],
    ["mancante", "al-pillola--mancante", "?", "ui.outcome.missing"],
  ] as const)("outcome %s: class, sign and word together", (esito, classe, segno, parola) => {
    const { container } = render(<Pillola esito={esito} />)
    const pillola = container.querySelector(".al-pillola") as HTMLElement
    expect(pillola.classList).toContain(classe)
    expect(pillola.textContent).toBe(`${segno} ${t(parola)}`)
  })

  it("the words of the outcomes match their names too", () => {
    const { container } = render(<Pillola esito="non adatta" />)
    expect(container.querySelector(".al-pillola")?.classList).toContain("al-pillola--non-adatta")
  })

  it("a neutral pill shows only the text it is given", () => {
    const { container } = render(
      <Pillola esito="neutra" testo="12 frame" fondo="carta" dimensione="micro" />,
    )
    const pillola = container.querySelector(".al-pillola") as HTMLElement
    expect(pillola.className).toBe(
      "al-pillola al-pillola--neutra al-pillola--micro al-pillola--su-carta",
    )
    expect(pillola.textContent).toBe("12 frame")
  })

  it("the sign shape is the round alone, hidden from who listens", () => {
    const { container } = render(<Pillola forma="segno" esito={1} fondo="carta2" />)
    const segno = container.querySelector(".al-segno") as HTMLElement
    expect(segno.className).toBe("al-segno al-segno--avviso al-segno--carta-2")
    expect(segno.getAttribute("aria-hidden")).toBe("true")
    expect(segno.textContent).toBe("!")
  })
})

describe("Carta", () => {
  it("a section with its name, on the card or protagonist ground", () => {
    render(
      <Carta etichetta="Stanotte" tono="protagonista" colonne={6}>
        dentro
      </Carta>,
    )
    const carta = screen.getByRole("region", { name: "Stanotte" })
    expect(carta.className).toBe("al-c-carta__blocco-1")
    expect(carta.style.background).toBe("var(--prot-fondo)")
    expect(carta.style.gridColumn).toBe("span 6")
    // v78: the sheet puts a card under 1000 px on the whole row
    expect(carta.dataset.col).toBe("6")
    expect(carta.style.display).toBe("flex")
  })

  it("on the phone the columns are not the card's to choose", () => {
    render(
      <Carta etichetta="x" formato="telefono" colonne={6} griglia="1fr 1fr">
        dentro
      </Carta>,
    )
    const carta = screen.getByRole("region", { name: "x" })
    expect(carta.style.gridColumn).toBe("")
    expect(carta.dataset.col).toBeUndefined()
    expect(carta.style.display).toBe("grid")
    expect(carta.style.background).toBe("var(--carta)")
  })
})

describe("Scheletro", () => {
  it("says loading to who listens, with the word of the dictionary", () => {
    render(<Scheletro carte={[{ col: "span 6", blocchi: [{ h: "36px", w: "60%" }, "Notti"] }]} />)
    const scheletro = screen.getByRole("status", { name: t("ui.loading") })
    expect(scheletro.className).toBe("al-c-scheletro__blocco-2")
    expect(scheletro.querySelectorAll(".al-c-scheletro__blocco-4")).toHaveLength(1)
    expect(scheletro.querySelector(".al-c-scheletro__blocco-3")).not.toBeNull()
    expect(scheletro.querySelector(".al-c-scheletro__testo-1")?.textContent).toBe("Notti")
  })

  it("a pile of cards sits in one column", () => {
    render(
      <Scheletro carte={[{ pila: [{ h: "120px" }, { h: "80px", blocchi: [{ w: "40%" }] }] }]} />,
    )
    const scheletro = screen.getByRole("status")
    expect(scheletro.querySelectorAll(".al-c-scheletro__colonna-2")).toHaveLength(2)
  })

  it("a row of blocks inside a card becomes a group", () => {
    render(
      <Scheletro
        carte={[{ blocchi: [{ riga: [{ w: "20%" }, { colonna: [{ h: "8px" }, { h: "8px" }] }] }] }]}
      />,
    )
    const gruppo = screen
      .getByRole("status")
      .querySelector(".al-c-scheletro__blocco-5") as HTMLElement
    expect(gruppo.style.display).toBe("flex")
    expect(gruppo.querySelectorAll(".al-c-scheletro__blocco-3")).toHaveLength(3)
  })
})

describe("PillolaScelta", () => {
  const opzioni = [
    { l: "Notti", sel: true },
    { l: "Archivio", no: true },
  ]

  it("pills are pressed, in a named group", () => {
    const scelta = vi.fn()
    render(
      <PillolaScelta
        opzioni={[
          { l: "Notti", sel: true },
          { l: "Archivio", on: scelta },
        ]}
      />,
    )
    const gruppo = screen.getByRole("group", { name: t("ui.choice") })
    expect(gruppo.className).toBe("al-scelta al-scelta--pillole")
    expect(screen.getByText("Notti").closest("a")?.getAttribute("aria-pressed")).toBe("true")
    fireEvent.click(screen.getByText("Archivio"))
    expect(scelta).toHaveBeenCalledOnce()
  })

  it("a switched-off option does not answer", () => {
    const scelta = vi.fn()
    render(
      <PillolaScelta
        opzioni={[
          { l: "Notti", sel: true },
          { l: "Archivio", no: true, on: scelta },
        ]}
      />,
    )
    fireEvent.click(screen.getByText("Archivio"))
    expect(scelta).not.toHaveBeenCalled()
    expect(screen.getByText("Archivio").closest("a")?.getAttribute("aria-disabled")).toBe("true")
  })

  it("radio role: a radiogroup with checked voices", () => {
    render(<PillolaScelta opzioni={opzioni} ruolo="radio" forma="segmentato" etichetta="Vista" />)
    expect(screen.getByRole("radiogroup", { name: "Vista" }).className).toBe(
      "al-scelta al-scelta--segmentato",
    )
    expect(screen.getByRole("radio", { name: "Notti" }).getAttribute("aria-checked")).toBe("true")
  })

  it("segmented without radio is a tab list", () => {
    render(<PillolaScelta opzioni={opzioni} forma="linguette" misura="piccola" />)
    expect(screen.getByRole("tablist").className).toBe(
      "al-scelta al-scelta--linguette al-scelta--piccola",
    )
    expect(screen.getByRole("tab", { name: "Notti" }).getAttribute("aria-selected")).toBe("true")
  })

  it("ticks are checkboxes with the colour of their measure", () => {
    render(
      <PillolaScelta
        opzioni={[{ l: "FWHM", sel: true, colore: "var(--filtro-1)" }]}
        forma="spunta"
      />,
    )
    const voce = screen.getByRole("checkbox", { name: "FWHM" })
    expect(voce.style.getPropertyValue("--voce-colore")).toBe("var(--filtro-1)")
    expect(voce.querySelector(".al-scelta__pallino")).not.toBeNull()
  })

  it("answers carry a round and an optional line below", () => {
    render(
      <PillolaScelta
        opzioni={[{ l: "Si", sub: "per tutti i frame", sel: true }]}
        forma="risposta"
        fondo="carta2"
      />,
    )
    const voce = screen.getByRole("radio", { name: /Si/ })
    expect(voce.className).toBe("al-scelta__voce al-scelta__voce--con-riga")
    expect(screen.getByRole("radiogroup").className).toBe(
      "al-scelta al-scelta--risposta al-scelta--fondo-carta-2",
    )
    expect(screen.getByText("per tutti i frame").className).toBe("al-scelta__riga")
  })

  it("the switch is a real button with role switch", () => {
    render(
      <PillolaScelta
        opzioni={[{ l: "Notifiche", titolo: "Notifiche accese", sel: true }]}
        forma="interruttore"
      />,
    )
    const interruttore = screen.getByRole("switch", { name: "Notifiche accese" })
    expect(interruttore.tagName).toBe("BUTTON")
    expect(interruttore.className).toBe("al-interruttore")
    expect(interruttore.getAttribute("aria-checked")).toBe("true")
  })

  it("on the phone the wrapper says so to the sheet", () => {
    const { container } = render(<PillolaScelta opzioni={opzioni} formato="telefono" />)
    expect((container.firstElementChild as HTMLElement).dataset["formato"]).toBe("telefono")
  })
})

describe("Finestra", () => {
  function aperta(onChiudi = vi.fn()) {
    const fuori = document.createElement("button")
    document.body.appendChild(fuori)
    fuori.focus()
    const resa = render(
      <Finestra titolo="Aggiungi oggetto" onChiudi={onChiudi}>
        <div className="al-finestra__gesti">
          <button type="button">Annulla</button>
          <button type="button">Aggiungi</button>
        </div>
      </Finestra>,
    )
    return { fuori, onChiudi, ...resa }
  }

  it("is a modal dialog named by its title, and takes the focus", () => {
    aperta()
    const finestra = screen.getByRole("dialog", { name: "Aggiungi oggetto" })
    expect(finestra.getAttribute("aria-modal")).toBe("true")
    expect(finestra.className).toBe("al-finestra__pannello")
    expect(document.activeElement).toBe(finestra)
  })

  it("Esc closes, and so do the x and a click on the veil", () => {
    const { onChiudi, container } = aperta()
    fireEvent.keyDown(document, { key: "Escape" })
    fireEvent.click(screen.getByRole("link", { name: t("ui.close") }))
    fireEvent.click(container.querySelector(".al-finestra") as HTMLElement)
    expect(onChiudi).toHaveBeenCalledTimes(3)
    expect(screen.getByRole("link", { name: t("ui.close") }).textContent).toBe(t("ui.close.sign"))
  })

  it("a click inside the panel does not close", () => {
    const { onChiudi } = aperta()
    fireEvent.click(screen.getByRole("dialog"))
    expect(onChiudi).not.toHaveBeenCalled()
  })

  it("Tab turns inside, and the focus goes back on closing", () => {
    const { fuori, unmount } = aperta()
    const ultimo = screen.getByRole("button", { name: "Aggiungi" })
    ultimo.focus()
    fireEvent.keyDown(ultimo, { key: "Tab" })
    expect(document.activeElement).toBe(screen.getByRole("link", { name: t("ui.close") }))
    fireEvent.keyDown(document.activeElement as HTMLElement, { key: "Tab", shiftKey: true })
    expect(document.activeElement).toBe(ultimo)
    unmount()
    expect(document.activeElement).toBe(fuori)
    fuori.remove()
  })

  it("narrow, on card ground, inside the page, with its sign", () => {
    const { container } = render(
      <Finestra
        titolo="x"
        segno="!"
        larghezza="stretta"
        fondo="carta"
        posizione="dentro"
        formato="telefono"
        onChiudi={vi.fn()}
      >
        corpo
      </Finestra>,
    )
    expect(container.querySelector(".al-finestra")?.className).toBe(
      "al-finestra al-finestra--dentro",
    )
    expect(screen.getByRole("dialog").className).toBe(
      "al-finestra__pannello al-finestra__pannello--stretta al-finestra__pannello--carta",
    )
    expect(container.querySelector(".al-finestra__segno")?.textContent).toBe("!")
    expect((container.firstElementChild as HTMLElement).dataset["formato"]).toBe("telefono")
  })

  it("without a head keeps the title as the dialog's name only", () => {
    render(
      <Finestra titolo="Frame" testa={false} larghezza="schermo" onChiudi={vi.fn()}>
        corpo
      </Finestra>,
    )
    expect(screen.getByRole("dialog", { name: "Frame" }).className).toBe(
      "al-finestra__pannello al-finestra__pannello--schermo",
    )
    expect(screen.queryByRole("link", { name: t("ui.close") })).toBeNull()
  })
})

describe("the two sheets", () => {
  const radice = process.cwd()

  it("the new sheet is the delivery's, with its classes", () => {
    const foglio = readFileSync(
      resolve(radice, "src", "stili", "consegna", "astrolog.css"),
      "utf-8",
    )
    expect(foglio).toContain('@import url("caratteri.css");')
    expect(foglio).toContain(".al-pillola--buona")
  })

  it("main imports the new sheet first, so the old one's :root wins for the as- pages", () => {
    const main = readFileSync(resolve(radice, "src", "main.tsx"), "utf-8")
    const nuovo = main.indexOf('import "./stili/consegna/astrolog.css"')
    const vecchio = main.indexOf('import "./stili/astrolog.css"')
    expect(nuovo).toBeGreaterThan(-1)
    expect(vecchio).toBeGreaterThan(nuovo)
    const primoFoglio = main.match(/import "(\.\/stili\/[^"]+)"/)?.[1]
    expect(primoFoglio).toBe("./stili/consegna/astrolog.css")
  })

  it("app.css resets the frame's links without beating any al- class, and loads last", () => {
    // the board's head rule `a{color:inherit}` weighs one element: `:where` keeps it there
    const app = readFileSync(resolve(radice, "src", "stili", "app.css"), "utf-8")
    expect(app).toContain(":where(.app-telaio) a {\n  color: inherit;\n  text-decoration: none;\n}")
    const main = readFileSync(resolve(radice, "src", "main.tsx"), "utf-8")
    const fogli = [...main.matchAll(/import "(\.\/stili\/[^"]+)"/g)].map((m) => m[1])
    expect(fogli.at(-1)).toBe("./stili/app.css")
  })
})
