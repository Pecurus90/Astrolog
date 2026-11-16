// @vitest-environment jsdom
/**
 * I mattoni condivisi -- `Avviso`, `Bottone`, `Campo`, `Vuoto` -- e cio' che il
 * foglio si aspetta da loro.
 *
 * Perche' hanno un file proprio: un mattone lo usano tutte le pagine, e una sua regola rotta non
 * cade dove e' scritta ma **sparsa** nelle prove di chi lo usa -- quando cade. Le forme che il
 * foglio disegna e il mattone non espone sono peggio ancora: non cade niente, perche' nessuno le
 * chiede. Sono state trovate confrontando a mano il primo avvio montato dal fornitore col nostro.
 *
 * Qui si prova **cosa il mattone rende**, non come si vede: il colore lo misura
 * `tools/controlli_contrasto.py` sui valori veri, che in jsdom non esistono.
 */
import { render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { MemoryRouter } from "react-router"

import { Avviso } from "../src/Avviso"
import { Bottone } from "../src/Bottone"
import { Campo } from "../src/Campo"
import { Vuoto } from "../src/Vuoto"
import { pulisci } from "./banco"

// Si sparecchia fra una prova e l'altra: senza, i render si accumulano nello stesso documento e
// una ricerca per ruolo ne trova tre invece di uno. Qui non c'era, e finche' ogni prova ha
// cercato un testo diverso non si e' visto -- il primo mattone con nove voci uguali l'ha
// scoperto subito. Si usa `pulisci` del banco, come fa ogni altro file che rende DOM: due
// modi di sparecchiare nello stesso banco sono due comportamenti da tenere a mente.
afterEach(pulisci)

describe("Avviso", () => {
  it("nel segno un carattere solo per l'allarme e il buono; gli altri toni li dice la forma", () => {
    // Design, DECISIONI 14/10: "!" e "✓"; niente "⚠" (emoji a colori su molti sistemi),
    // "…" o "i". Attesa, neutro, ignoto e lavoro li separa il bordo che il foglio disegna.
    const attesi = { allarme: "!", buono: "✓", attesa: "", neutro: "", ignoto: "", lavoro: "" } as const
    for (const [esito, carattere] of Object.entries(attesi)) {
      const { container, unmount } = render(<Avviso esito={esito as keyof typeof attesi}>ciao</Avviso>)
      expect(container.querySelector(".as-avviso__segno")?.textContent, esito).toBe(carattere)
      unmount()
    }
  })

  it("ogni tono porta anche la sua forma, non il solo segno", () => {
    // Il segno e' una meta': l'altra e' il bordo -- tratteggiato per l'attesa, pieno e colorato
    // per gli altri -- e la porta la classe. Senza questa riga si potevano svuotare tutte e
    // quattro, o scambiarle fra loro, con la suite verde: un avviso d'attesa identico a uno
    // andato bene per chi guarda. E' lo stesso buco che `Campo` aveva sulle sue due classi.
    const forme: Record<string, string> = {
      neutro: "as-avviso",
      attesa: "as-avviso--attesa",
      buono: "as-avviso--buono",
      allarme: "as-avviso--allarme",
    }
    for (const [esito, classe] of Object.entries(forme)) {
      const { container, unmount } = render(
        <Avviso esito={esito as "neutro" | "attesa" | "buono" | "allarme"}>ciao</Avviso>,
      )
      const avviso = container.querySelector(".as-avviso")
      expect(avviso?.className, esito).toContain(classe)
      // e l'involucro non si porta dietro spazi: `class="as-avviso "` e' un letterale sporco
      expect(avviso?.className.trim(), esito).toBe(avviso?.className)
      unmount()
    }
  })

  it("il segno non lo sente chi ascolta: lo dice gia' il ruolo", () => {
    const { container } = render(<Avviso esito="allarme">rotto</Avviso>)
    expect(container.querySelector(".as-avviso__segno")?.getAttribute("aria-hidden")).toBe("true")
    expect(screen.getByRole("alert").textContent).toBe("rotto")
  })

  it("il testo puo' portare paragrafi: un paragrafo dentro un paragrafo il browser lo spezza", () => {
    const { container } = render(
      <Avviso esito="attesa">
        perche'
        <p>un passo</p>
      </Avviso>,
    )
    expect(container.querySelector("p p")).toBeNull()
    expect(screen.getByRole("status").textContent).toBe("perche'un passo")
  })

  it("puo' avere un titolo, e senza titolo non lascia un posto vuoto", () => {
    const { container, rerender } = render(<Avviso esito="buono">il testo</Avviso>)
    expect(container.querySelector(".as-avviso__titolo")).toBeNull()
    rerender(
      <Avviso esito="buono" titolo="Dentro c'e' roba da leggere">
        il testo
      </Avviso>,
    )
    expect(container.querySelector(".as-avviso__titolo")?.textContent).toBe(
      "Dentro c'e' roba da leggere",
    )
  })

  it("porta dentro di se' cio' che si puo' fare", () => {
    // I bottoni stanno **dentro** l'avviso che li motiva: staccati, chi legge "la ricerca non ha
    // risposto" deve cercare altrove cosa farci, e il legame fra il guasto e il rimedio si perde.
    const { container } = render(
      <Avviso
        esito="allarme"
        azioni={
          <Bottone piccolo onClick={() => {}}>
            Riprova
          </Bottone>
        }
      >
        la ricerca non ha risposto
      </Avviso>,
    )
    const azioni = container.querySelector(".as-avviso__azioni")
    expect(azioni).not.toBeNull()
    expect(within(azioni as HTMLElement).getByRole("button", { name: "Riprova" })).toBeDefined()
  })

  it("chi chiama puo' decidere di non interrompere, anche su un allarme", () => {
    // Serve davvero: la cartella che non si raggiunge e' un allarme, ma compare **dopo un gesto**
    // di chi sta guardando quel punto -- interromperlo per dirgli cio' che sta gia' leggendo e'
    // rumore. Senza questa riga, togliere lo scavalco non farebbe cadere niente e due schermate
    // comincerebbero a tagliare la parola a chi legge.
    const { container } = render(
      <Avviso esito="allarme" ruolo="status">
        questa cartella non si raggiunge
      </Avviso>,
    )
    expect(container.querySelector('[role="status"]')).not.toBeNull()
    expect(container.querySelector('[role="alert"]')).toBeNull()
  })

  it("un avviso che aspetta non interrompe, uno che allarma si'", () => {
    // `alert` taglia la parola a chi sta leggendo, `status` aspetta una pausa. Un esito che non e'
    // un guasto non ha diritto di interrompere.
    const { container, rerender } = render(<Avviso esito="neutro">cosa cambia senza</Avviso>)
    expect(container.querySelector('[role="status"]')).not.toBeNull()
    rerender(<Avviso esito="allarme">non ho potuto salvare</Avviso>)
    expect(container.querySelector('[role="alert"]')).not.toBeNull()
  })
})

describe("Bottone", () => {
  it("il verso errore porta la parola, non il solo bordo rosso", () => {
    // Il foglio gli mette un `!` davanti col `::before`, che in jsdom non esiste: cio' che
    // si prova qui e' che la classe ci arrivi, e che la parola dica da se' cosa e' successo.
    render(
      <Bottone verso="errore" onClick={() => {}}>
        Non salvato - riprova
      </Bottone>,
    )
    const b = screen.getByRole("button", { name: /non salvato/i })
    expect(b.className).toContain("as-bottone--errore")
  })

  it("con un indirizzo e' un collegamento, non un bottone", () => {
    // Un gesto che porta altrove **e' un indirizzo**: si apre in una scheda nuova, si copia, e il
    // tasto indietro funziona. Scritto come bottone, nessuna di quelle tre cose vale -- e le
    // classi del foglio finirebbero fuori dal loro mattone, che il cancello vieta.
    render(
      <MemoryRouter>
        <Bottone a="/impostazioni/siti" piccolo>
          Scegli il sito
        </Bottone>
      </MemoryRouter>,
    )
    expect(screen.queryByRole("button", { name: /scegli il sito/i })).toBeNull()
    const collegamento = screen.getByRole("link", { name: /scegli il sito/i })
    expect(collegamento.getAttribute("href")).toBe("/impostazioni/siti")
    // E la veste e' quella del mattone, coi suoi modificatori.
    expect(collegamento.className).toContain("as-bottone")
    expect(collegamento.className).toContain("as-bottone--piccolo")
  })
})

describe("Campo", () => {
  it("l'attesa anima il campo, e l'errore la copre", () => {
    // Due stati che non possono valere insieme: un campo o sta aspettando una risposta o ne ha
    // gia' una da dare. Senza questa prova la regola sta scritta in una docstring e basta, e il
    // giorno che qualcuno inverte il ternario un campo rotto continuerebbe a scorrere come se
    // stesse ancora lavorando.
    const { container, rerender } = render(
      <Campo id="x" etichetta="Nome" aspetta>
        <input id="x" />
      </Campo>,
    )
    expect(container.querySelector(".as-campo-modulo--attesa")).not.toBeNull()

    rerender(
      <Campo id="x" etichetta="Nome" aspetta errore="non va">
        <input id="x" />
      </Campo>,
    )

    expect(container.querySelector(".as-campo-modulo--errore")).not.toBeNull()
    expect(container.querySelector(".as-campo-modulo--attesa")).toBeNull()
  })

  it("l'errore sta sotto il campo, e chi ascolta lo sente col campo", () => {
    // Un motivo scritto in un avviso staccato lo legge chi guarda la pagina intera; chi arriva sul
    // campo col tabulatore sente solo l'etichetta. `aria-describedby` glielo lega, `aria-invalid`
    // dice che quel campo e' quello rotto.
    render(
      <Campo id="lat" etichetta="Latitudine" errore="fra -90 e 90">
        <input className="as-campo-modulo__input" id="lat" />
      </Campo>,
    )
    const campo = screen.getByLabelText("Latitudine")
    expect(campo.getAttribute("aria-invalid")).toBe("true")
    const detto = campo.getAttribute("aria-describedby")
    expect(detto).toBeTruthy()
    expect(document.getElementById(detto as string)?.textContent).toBe("fra -90 e 90")
  })

  it("l'errore si annuncia da se', non solo quando il fuoco e' sul campo", () => {
    // `aria-describedby` lo fa sentire a chi ha il fuoco **li' dentro**. Ma il motivo del
    // percorso del riconoscitore compare dopo un clic, e in quel momento il fuoco sta sul
    // bottone: senza un ruolo vivo il messaggio arrivava in silenzio. Visto misurando il DOM:
    // zero regioni vive intorno a quel testo.
    render(
      <Campo id="solver" etichetta="Dove sta" errore="Li' non c'e' ASTAP">
        <input className="as-campo-modulo__input" id="solver" />
      </Campo>,
    )
    const detto = screen.getByLabelText("Dove sta").getAttribute("aria-describedby")
    expect(document.getElementById(detto as string)?.getAttribute("role")).toBe("alert")
  })

  it("il campo rotto si VEDE, non solo si sente", () => {
    // Le due classi sono la meta' visibile dell'errore: il bordo d'allarme sull'input e il
    // `!` davanti al motivo. Senza questa riga si potevano togliere tutte e due e la suite
    // restava verde -- un campo rotto identico a uno sano, per chi guarda.
    const { container } = render(
      <Campo id="lat" etichetta="Latitudine" errore="fra -90 e 90">
        <input className="as-campo-modulo__input" id="lat" />
      </Campo>,
    )
    expect(container.querySelector(".as-campo-modulo")?.className).toContain("as-campo-modulo--errore")
    expect(container.querySelector(".as-campo-modulo__errore")?.textContent).toBe("fra -90 e 90")
  })

  it("lega il controllo anche quando e' scritto dietro una condizione", () => {
    // Un pezzo condizionale **spento** prima del controllo lascia al suo posto un `false`, e
    // `Children.map` chiama il callback anche per lui: il figlio numero zero non e' il controllo,
    // e il legame finirebbe su niente -- senza errori, senza prove rosse, e col motivo scritto
    // sotto un campo che non lo nomina.
    const conSuggerimento = false
    render(
      <Campo id="lon" etichetta="Longitudine" errore="fra -180 e 180">
        {conSuggerimento && <span>suggerimento</span>}
        <input className="as-campo-modulo__input" id="lon" />
        <p className="as-campo-modulo__aiuto">in gradi decimali</p>
      </Campo>,
    )
    const campo = screen.getByLabelText("Longitudine")
    expect(campo.getAttribute("aria-invalid")).toBe("true")
    expect(
      document.getElementById(campo.getAttribute("aria-describedby") as string)?.textContent,
    ).toBe("fra -180 e 180")
  })

  it("due campi rotti nella stessa pagina non si scambiano il motivo", () => {
    // L'id dell'errore nasce da quello del campo: fosse una costante, due campi vicini avrebbero
    // due `id` uguali e chi ascolta si sentirebbe leggere sempre il motivo del primo. Non e'
    // teorico -- una sezione di *Da confermare* ne rende tre di fila.
    render(
      <>
        <Campo id="lat" etichetta="Latitudine" errore="fra -90 e 90">
          <input className="as-campo-modulo__input" id="lat" />
        </Campo>
        <Campo id="lon" etichetta="Longitudine" errore="fra -180 e 180">
          <input className="as-campo-modulo__input" id="lon" />
        </Campo>
      </>,
    )
    const motivo = (etichetta: string) => {
      const c = screen.getByLabelText(etichetta)
      return document.getElementById(c.getAttribute("aria-describedby") as string)?.textContent
    }
    expect(motivo("Latitudine")).toBe("fra -90 e 90")
    expect(motivo("Longitudine")).toBe("fra -180 e 180")
  })

  it("lega il controllo e NIENT'ALTRO", () => {
    // La meta' negativa della regola: se gli attributi finissero su tutti i figli, l'aiuto
    // sotto il campo si prenderebbe un `aria-invalid` -- che su un paragrafo non e' nemmeno
    // ammesso -- e chi ascolta sentirebbe due cose rotte invece di una.
    const { container } = render(
      <Campo id="lat" etichetta="Latitudine" errore="fra -90 e 90">
        <input className="as-campo-modulo__input" id="lat" />
        <p className="as-campo-modulo__aiuto">in gradi decimali</p>
      </Campo>,
    )
    const aiuto = container.querySelector(".as-campo-modulo__aiuto")
    expect(aiuto?.getAttribute("aria-invalid")).toBeNull()
    expect(aiuto?.getAttribute("aria-describedby")).toBeNull()
  })

  it("il campo di testo sta nel suo pozzo, e l'aiuto resta fuori", () => {
    // Il foglio disegna il bordo e il fuoco sul pozzo, non sull'input: senza, il campo non si vede.
    const { container } = render(
      <Campo id="nome" etichetta="Nome">
        <input className="as-campo-modulo__input" id="nome" />
        <p className="as-campo-modulo__aiuto">facoltativo</p>
      </Campo>,
    )
    const pozzo = container.querySelector(".as-campo-modulo__pozzo")
    expect(pozzo?.contains(screen.getByLabelText("Nome"))).toBe(true)
    expect(pozzo?.querySelector(".as-campo-modulo__aiuto")).toBeNull()
    expect(container.querySelector(".as-campo-modulo__etichetta")?.textContent).toBe("Nome")
  })

  it("una tendina sta nel pozzo del campo, e il campo dice che e' una tendina", () => {
    // Il foglio v34 veste la tendina col pozzo del campo e la sua freccia: fuori dal pozzo resta
    // un controllo nudo, alto la meta' dei campi accanto.
    const { container } = render(
      <Campo id="tipo" etichetta="Tipo">
        <select className="as-campo-modulo__input" id="tipo" />
      </Campo>,
    )
    expect(container.querySelector(".as-campo-modulo")?.className).toBe("as-campo-modulo as-campo-modulo--tendina")
    expect(container.querySelector(".as-campo-modulo__pozzo > select")).not.toBeNull()
  })

  it("mentre aspetta, il campo lo dice anche a chi ascolta", () => {
    render(
      <Campo id="x" etichetta="Nome" aspetta>
        <input className="as-campo-modulo__input" id="x" />
      </Campo>,
    )
    expect(screen.getByLabelText("Nome").getAttribute("aria-busy")).toBe("true")
  })

  it("senza errore non dichiara niente, e l'involucro resta pulito", () => {
    const { container } = render(
      <Campo id="nome" etichetta="Nome">
        <input className="as-campo-modulo__input" id="nome" />
      </Campo>,
    )
    expect(screen.getByLabelText("Nome").getAttribute("aria-invalid")).toBeNull()
    expect(screen.getByLabelText("Nome").getAttribute("aria-describedby")).toBeNull()
    expect(container.querySelector(".as-campo-modulo")?.className).toBe("as-campo-modulo")
  })
})

describe("Vuoto", () => {
  it("il suo titolo sta un livello sotto quello che gli sta sopra", () => {
    // Il livello e' la meta' del mattone che una classe non difende: `as-vuoto__titolo` e'
    // identico su un `h2` e su un `h3`, e chi naviga per titoli non si accorge di aver saltato
    // un livello -- crede che quella sezione non ci sia. La guardia di accessibilita' morde sulle
    // pagine che monta, non sul mattone: qui si prova il tag, che e' cio' che decide.
    const { rerender } = render(<Vuoto titolo="nights.empty.noFrames" perche="nights.empty.noFrames.why" sotto={1} />)
    expect(screen.getByRole("heading", { level: 2 })).not.toBeNull()

    rerender(<Vuoto titolo="nights.empty.noFrames" perche="nights.empty.noFrames.why" />)
    expect(screen.getByRole("heading", { level: 3 })).not.toBeNull()
  })
})
