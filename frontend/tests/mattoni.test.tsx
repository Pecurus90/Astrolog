// @vitest-environment jsdom
/**
 * I mattoni condivisi -- `Avviso`, `Bottone`, `Campo`, `ScalaDelCielo`, `Vuoto` -- e cio' che il
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
import { fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { MemoryRouter } from "react-router"

import { Avviso } from "../src/Avviso"
import { Bottone } from "../src/Bottone"
import { Campo } from "../src/Campo"
import { CLASSI, ScalaDelCielo, cosaSiVede } from "../src/ScalaDelCielo"
import { Vuoto } from "../src/Vuoto"
import { pulisci } from "./banco"

// Si sparecchia fra una prova e l'altra: senza, i render si accumulano nello stesso documento e
// una ricerca per ruolo ne trova tre invece di uno. Qui non c'era, e finche' ogni prova ha
// cercato un testo diverso non si e' visto -- il primo mattone con nove voci uguali l'ha
// scoperto subito. Si usa `pulisci` del banco, come fa ogni altro file che rende DOM: due
// modi di sparecchiare nello stesso banco sono due comportamenti da tenere a mente.
afterEach(pulisci)

describe("Avviso", () => {
  it("ha quattro toni, e ognuno porta il suo segno", () => {
    // WCAG 2.2, 1.4.1: se il tono lo dicesse il solo colore, chi non distingue verde e rosso
    // leggerebbe quattro avvisi identici. Il segno e' la forma che li separa.
    const segni = new Set<string>()
    for (const esito of ["neutro", "attesa", "buono", "allarme"] as const) {
      const { container, unmount } = render(<Avviso esito={esito}>ciao</Avviso>)
      const segno = container.querySelector(".as-avviso__segno")
      expect(segno?.textContent, esito).toBeTruthy()
      segni.add(segno?.textContent ?? "")
      unmount()
    }
    expect(segni.size, "due toni con lo stesso segno non si distinguono").toBe(4)
  })

  it("ogni tono porta anche la sua forma, non il solo segno", () => {
    // Il segno e' una meta': l'altra e' il bordo -- tratteggiato per l'attesa, pieno e colorato
    // per gli altri -- e la porta la classe. Senza questa riga si potevano svuotare tutte e
    // quattro, o scambiarle fra loro, con la suite verde: un avviso d'attesa identico a uno
    // andato bene per chi guarda. E' lo stesso buco che `Campo` aveva sulle sue due classi.
    const forme: Record<string, string> = {
      neutro: "as-avviso",
      attesa: "as-avviso--attesa",
      // il v26 ha tolto il tono buono: lo distingue il segno, la spunta (prova qui sopra)
      buono: "as-avviso",
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
    // Il foglio gli mette un triangolo davanti col `::before`, che in jsdom non esiste: cio' che
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
        <Bottone a="/impostazioni/sito" piccolo>
          Scegli il sito
        </Bottone>
      </MemoryRouter>,
    )
    expect(screen.queryByRole("button", { name: /scegli il sito/i })).toBeNull()
    const collegamento = screen.getByRole("link", { name: /scegli il sito/i })
    expect(collegamento.getAttribute("href")).toBe("/impostazioni/sito")
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
    expect(container.querySelector(".as-campo--caricamento")).not.toBeNull()

    rerender(
      <Campo id="x" etichetta="Nome" aspetta errore="non va">
        <input id="x" />
      </Campo>,
    )

    expect(container.querySelector(".as-campo--errore")).not.toBeNull()
    expect(container.querySelector(".as-campo--caricamento")).toBeNull()
  })

  it("l'errore sta sotto il campo, e chi ascolta lo sente col campo", () => {
    // Un motivo scritto in un avviso staccato lo legge chi guarda la pagina intera; chi arriva sul
    // campo col tabulatore sente solo l'etichetta. `aria-describedby` glielo lega, `aria-invalid`
    // dice che quel campo e' quello rotto.
    render(
      <Campo id="lat" etichetta="Latitudine" errore="fra -90 e 90">
        <input className="as-campo__input" id="lat" />
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
        <input className="as-campo__input" id="solver" />
      </Campo>,
    )
    const detto = screen.getByLabelText("Dove sta").getAttribute("aria-describedby")
    expect(document.getElementById(detto as string)?.getAttribute("role")).toBe("alert")
  })

  it("il campo rotto si VEDE, non solo si sente", () => {
    // Le due classi sono la meta' visibile dell'errore: il bordo d'allarme sull'input e il
    // triangolo davanti al motivo. Senza questa riga si potevano togliere tutte e due e la suite
    // restava verde -- un campo rotto identico a uno sano, per chi guarda.
    const { container } = render(
      <Campo id="lat" etichetta="Latitudine" errore="fra -90 e 90">
        <input className="as-campo__input" id="lat" />
      </Campo>,
    )
    expect(container.querySelector(".as-campo-modulo")?.className).toContain("as-campo--errore")
    expect(container.querySelector(".as-campo__errore")?.textContent).toBe("fra -90 e 90")
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
        <input className="as-campo__input" id="lon" />
        <p className="as-campo__aiuto">in gradi decimali</p>
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
          <input className="as-campo__input" id="lat" />
        </Campo>
        <Campo id="lon" etichetta="Longitudine" errore="fra -180 e 180">
          <input className="as-campo__input" id="lon" />
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
        <input className="as-campo__input" id="lat" />
        <p className="as-campo__aiuto">in gradi decimali</p>
      </Campo>,
    )
    const aiuto = container.querySelector(".as-campo__aiuto")
    expect(aiuto?.getAttribute("aria-invalid")).toBeNull()
    expect(aiuto?.getAttribute("aria-describedby")).toBeNull()
  })

  it("senza errore non dichiara niente, e l'involucro resta pulito", () => {
    const { container } = render(
      <Campo id="nome" etichetta="Nome">
        <input className="as-campo__input" id="nome" />
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

describe("ScalaDelCielo", () => {
  const scala = () => screen.getByRole("radiogroup")
  const voci = () => within(scala()).getAllByRole("radio")

  it("ha nove classi, e ognuna porta la sua cifra scritta", () => {
    // Il colore non dice mai da solo che classe e' (WCAG 2.2, 1.4.1): la fascia e' decorazione,
    // e chi non distingue il ciano dal rosa deve leggere il numero.
    render(<ScalaDelCielo onScegli={() => {}} />)

    expect(voci()).toHaveLength(9)
    expect(voci().map((v) => v.textContent?.trim())).toEqual([
      "1",
      "2",
      "3",
      "4",
      "5",
      "6",
      "7",
      "8",
      "9",
    ])
  })

  it("ogni classe si chiama col suo cielo, e sono nove cieli diversi", () => {
    // Nove bottoni che si chiamano "1".."9" non dicono niente a chi ascolta: il nome porta
    // dentro che cielo e' quello, che e' l'unica cosa su cui si puo' scegliere.
    //
    // E si guardano **tutte e nove**, legate una per una alla loro parola: e' cosi' che questa
    // scala e' gia' entrata sbagliata una volta, con due classi scambiate fra loro. Provandone
    // due, scambiare la 4 con la 5 -- nome e descrizione, in tutte e due le lingue -- lasciava
    // la suite verde.
    const PAROLA: Record<number, RegExp> = {
      1: /buio pieno/i,
      2: /buio vero/i,
      3: /campagna/i,
      4: /chiara/i,
      5: /periferia/i,
      6: /luminosa/i,
      7: /fra periferia e citt/i,
      8: /di citt/i,
      9: /centro citt/i,
    }
    render(<ScalaDelCielo onScegli={() => {}} />)

    const nomi = voci().map((v) => v.getAttribute("aria-label") ?? "")
    for (const [i, nome] of nomi.entries()) {
      expect(nome).toMatch(new RegExp(`^Bortle ${i + 1} - `))
      expect(nome).toMatch(PAROLA[i + 1]!)
    }
    // e sono nove nomi diversi, non lo stesso ripetuto
    expect(new Set(nomi).size).toBe(9)
  })

  it("e ogni classe dice cosa ci si vede, con un segno che le altre non hanno", () => {
    // La descrizione e' la riga su cui si sceglie davvero. Due classi che danno lo stesso
    // indizio non si possono distinguere: la 1 e la 2 lo facevano tutte e due sulla luce
    // zodiacale, e chi sceglieva leggeva due volte la stessa cosa.
    const dette = CLASSI.map((c) => cosaSiVede(c))

    expect(new Set(dette).size).toBe(9)
    expect(dette[0]).toMatch(/ombre/i)
    expect(dette[1]).toMatch(/zodiacale/i)
    expect(dette[0]).not.toMatch(/zodiacale/i)
  })

  it("anche senza scelta il tabulatore trova UNA voce, o il gruppo e' irraggiungibile", () => {
    // E' lo stato in cui la scala **nasce** nel primo avvio. Senza una fermata, da tastiera non
    // ci si entra affatto: nessun `tabindex="0"`, e nove voci che il tabulatore salta. La prova
    // con `scelta` non lo vedrebbe, perche' li' la fermata e' quella scelta.
    render(<ScalaDelCielo onScegli={() => {}} />)

    const fermate = voci().filter((v) => v.getAttribute("tabindex") === "0")
    expect(fermate).toHaveLength(1)
    expect(fermate[0]?.textContent?.trim()).toBe("1")
    // e restare raggiungibili non vuol dire essere scelti
    expect(fermate[0]?.getAttribute("aria-checked")).toBe("false")
  })

  it("ogni fascia porta la classe che il foglio le da', non una tinta scritta qui", () => {
    // La rampa dal ciano al rosa **e' del foglio**, una classe per fascia
    // (`as-bortle__voce--1` ... `--9`). Scrivere il colore in linea sarebbe una seconda verita'
    // sullo stesso colore, e nessuna macchina la vedrebbe: una classe che **esiste** non e' una
    // classe inventata, quindi la guardia del cancello tace. Qui si guarda che la classe ci sia.
    render(<ScalaDelCielo onScegli={() => {}} />)

    const tinte = voci().map((v, i) => v.classList.contains(`as-bortle__voce--${i + 1}`))
    expect(tinte).toEqual(CLASSI.map(() => true))
    // e il colore non e' scritto sull'elemento: se ci fosse, verrebbe da noi e non dal foglio
    expect(voci().every((v) => v.getAttribute("style") === null)).toBe(true)
  })

  it("il tabulatore trova UNA voce sola, e le frecce spostano la scelta", () => {
    // E' un gruppo di scelte, non nove fermate del tabulatore: senza il tabindex mobile chi
    // arriva da tastiera deve premere nove volte per attraversarlo.
    const scelte: number[] = []
    render(<ScalaDelCielo scelta={4} onScegli={(n) => scelte.push(n)} />)

    expect(voci().filter((v) => v.getAttribute("tabindex") === "0")).toHaveLength(1)
    expect(voci()[3]?.getAttribute("tabindex")).toBe("0")

    fireEvent.keyDown(voci()[3]!, { key: "ArrowRight" })
    fireEvent.keyDown(voci()[3]!, { key: "ArrowLeft" })
    expect(scelte).toEqual([5, 3])
  })

  it("le frecce non escono dalla scala, da nessuno dei due estremi", () => {
    // Nove classi sono nove, e una scala che gira su se' stessa farebbe saltare dal centro
    // citta' al buio pieno con un tasto solo.
    //
    // E l'estremo basso e' il piu' pericoloso dei due: senza la guardia, ArrowLeft sulla 1
    // prende la classe di posto -1, che non esiste, e **cancella in silenzio la scelta gia'
    // fatta** -- il cielo sparisce dal sito che si sta per salvare, senza un messaggio.
    const scelte: (number | undefined)[] = []
    const { unmount } = render(<ScalaDelCielo scelta={9} onScegli={(n) => scelte.push(n)} />)
    fireEvent.keyDown(voci()[8]!, { key: "ArrowRight" })
    expect(scelte).toEqual([])
    unmount()

    render(<ScalaDelCielo scelta={1} onScegli={(n) => scelte.push(n)} />)
    fireEvent.keyDown(voci()[0]!, { key: "ArrowLeft" })
    expect(scelte).toEqual([])
  })

  it("dice quale ha scelto, e una sola", () => {
    render(<ScalaDelCielo scelta={4} onScegli={() => {}} />)

    expect(voci().filter((v) => v.getAttribute("aria-checked") === "true")).toHaveLength(1)
    expect(voci()[3]?.getAttribute("aria-checked")).toBe("true")
  })

  it("senza scelta nessuna classe e' scelta: un cielo non dichiarato non e' il migliore", () => {
    // Partire dalla 1 vorrebbe dire dichiarare un cielo eccellente a chi non ha risposto, e
    // quello e' il numero che poi finisce nel database.
    render(<ScalaDelCielo onScegli={() => {}} />)

    expect(voci().filter((v) => v.getAttribute("aria-checked") === "true")).toHaveLength(0)
  })

  it("i due estremi si leggono a parole, non solo dai colori", () => {
    // Chi non vede la rampa deve sapere da che parte si va: e' scritto sotto la scala.
    render(<ScalaDelCielo onScegli={() => {}} />)

    const estremi = document.querySelector(".as-bortle__estremi")?.textContent ?? ""
    expect(estremi).toMatch(/buio/i)
    expect(estremi).toMatch(/citt/i)
  })
})
