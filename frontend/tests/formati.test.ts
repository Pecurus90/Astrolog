/**
 * Come si scrivono a schermo **le ore**, **la data di una notte** e **le coordinate di un posto**:
 * i formattatori che le pagine di lettura usano su ogni riga, e che per questo non possono
 * sbagliare in silenzio.
 */
import { afterEach, describe, expect, it } from "vitest"

import {
  DIZIONARI,
  cielo,
  coordinataDa,
  coordinate,
  durata,
  giorno,
  giornoDellaSettimana,
  notte,
  orario,
  ore,
} from "../src/i18n"
import { it as testiIt } from "../src/i18n/it"

const TZ_ORIGINALE = process.env.TZ

afterEach(() => {
  process.env.TZ = TZ_ORIGINALE
})

describe("un punto del cielo", () => {
  it("si legge al decimo di grado, e l'ascensione retta non arriva mai a 360", () => {
    expect(cielo(98.04, 4.93)).toBe("RA 98 Dec 4,9")
    expect(cielo(359.99, 10)).toBe("RA 0 Dec 10")
    expect(cielo(98, -0.04)).toBe("RA 98 Dec 0")
  })
})

describe("le ore", () => {
  it("si scrivono con un decimale", () => {
    expect(ore(43200)).toBe("12")
    expect(ore(9000)).toBe("2,5")
  })

  it("un tempo vero ma piccolo non diventa zero", () => {
    // Arrotondato, un frame da un minuto sarebbe "0 h". Zero ore vuol dire "non c'e' tempo", e
    // li' il tempo c'e'.
    expect(ore(60)).toBe("< 0,1")
  })

  it("zero vero resta zero", () => {
    expect(ore(0)).toBe("0")
  })
})

describe("quanto e' durata una lettura", () => {
  it("sotto il minuto si contano i secondi", () => {
    // Una cartella piccola si legge in un lampo: "0 min" direbbe che non e' successo niente.
    expect(durata(3.5)).toBe("4 s")
    expect(durata(59)).toBe("59 s")
  })

  it("oltre il minuto i secondi restano, ma accanto ai minuti", () => {
    // I secondi non si buttano: fra "2 min" e "2 min 14 s" la seconda dice se vale la pena
    // aspettare la prossima. Il minuto tondo non si porta dietro uno "0 s" che non aggiunge niente.
    expect(durata(134)).toBe("2 min 14 s")
    expect(durata(120)).toBe("2 min")
  })

  it("oltre l'ora i secondi spariscono, che a quel punto sono rumore", () => {
    expect(durata(4320)).toBe("1 h 12 min")
    expect(durata(3600)).toBe("1 h")
  })

  it("una durata che non c'e' non e' uno zero", () => {
    // La corsa e' ancora aperta: "0 s" direbbe che e' finita in un istante.
    expect(durata(null)).toBeUndefined()
  })

  it("un tempo vero sotto il secondo non si scrive zero", () => {
    // Una cartella di quattordici file si legge in 76 millesimi: e' successo, ed e' andata bene.
    // "0 s" e' cio' che scrive una corsa mai partita.
    expect(durata(0.076)).toBe("< 1 s")
    expect(durata(0.4)).toBe("< 1 s")
    expect(durata(0)).toBe("0 s")
  })
})

describe("le coordinate di un posto", () => {
  it("dicono il verso con la lettera, non col segno meno", () => {
    // "-33,86" chiede a chi legge di sapere che il meno e' l'emisfero sud. La lettera lo dice.
    expect(coordinate(-33.8688, 151.2093)).toBe("33,8688 S - 151,2093 E")
    expect(coordinate(46.4843, -12.0561)).toBe("46,4843 N - 12,0561 O")
  })

  it("le lettere passano dal dizionario, o l'inglese legge 'O' per ovest", () => {
    // Scritte dentro il formattatore resterebbero italiane in ogni lingua -- un inglese leggerebbe
    // `12.0561 O` -- e la guardia delle traduzioni non se ne accorgerebbe, perche' quelle lettere
    // non passerebbero da `t()`. Qui si cambia la parola nel dizionario e si guarda se cambia a
    // valle: scritta a mano nel formattatore, non cambierebbe.
    const salva = DIZIONARI.it["coord.w"]!
    try {
      DIZIONARI.it["coord.w"] = "ZZ"
      expect(coordinate(1, -1)).toBe("1,0000 N - 1,0000 ZZ")
    } finally {
      DIZIONARI.it["coord.w"] = salva
    }
    expect(testiIt["coord.w"]).toBe("O")
  })

  it("quattro decimali, ne' uno di piu' ne' uno di meno", () => {
    // Piu' fingono una precisione che il posto non ha; meno non distinguono due siti vicini.
    expect(coordinate(46.5, 12)).toBe("46,5000 N - 12,0000 E")
    expect(coordinate(46.48439999, 12)).toBe("46,4844 N - 12,0000 E")
  })
})

describe("una coordinata riscritta a mano", () => {
  it("accetta la virgola, che e' quella che l'app stessa suggerisce", () => {
    // Il segnaposto italiano porta la virgola: con `Number` chi copiava esattamente cio' che gli
    // veniva proposto otteneva NaN, il tasto spento e nessun motivo.
    expect(coordinataDa("46,4843", "lat")).toBe(46.4843)
    expect(coordinataDa("46.4843", "lat")).toBe(46.4843)
  })

  it("accetta la lettera del verso, in tutte e due le lingue", () => {
    // Cosi' cio' che si legge a schermo si puo' riscrivere nel campo senza tradurlo.
    expect(coordinataDa("33,8688 S", "lat")).toBe(-33.8688)
    expect(coordinataDa("12,0561 O", "lon")).toBe(-12.0561)
    expect(coordinataDa("12.0561 W", "lon")).toBe(-12.0561)
    expect(coordinataDa("46,4843 N", "lat")).toBe(46.4843)
  })

  it("la lettera comanda sul segno: due modi di dire sud non fanno un nord", () => {
    expect(coordinataDa("-33,86 S", "lat")).toBe(-33.86)
  })

  it("un campo vuoto non e' una coordinata", () => {
    // `Number("")` fa zero, e zero-zero e' un punto nel Golfo di Guinea che come luogo di casa
    // deciderebbe il fuso di tutte le notti.
    expect(coordinataDa("", "lat")).toBeNaN()
    expect(coordinataDa("   ", "lat")).toBeNaN()
    expect(coordinataDa("N", "lat")).toBeNaN()
    expect(coordinataDa("quassu'", "lat")).toBeNaN()
  })

  it("la lettera dell'altro asse non e' un numero, invece di cambiare emisfero in silenzio", () => {
    // `"45 W"` battuto nella **latitudine**, letto da una tabella sola di lettere, diventava 45
    // gradi sud: un numero giusto su un emisfero che nessuno aveva chiesto, salvato senza una
    // parola. Una funzione che non sa su che asse sta non puo' accorgersene, quindi l'asse glielo
    // si dice.
    expect(coordinataDa("45 W", "lat")).toBeNaN()
    expect(coordinataDa("45 O", "lat")).toBeNaN()
    expect(coordinataDa("12 S", "lon")).toBeNaN()
    expect(coordinataDa("12 N", "lon")).toBeNaN()
  })

  it("cio' che sembra un numero e non lo e' resta NaN", () => {
    expect(coordinataDa("Infinity", "lat")).toBeNaN()
    expect(coordinataDa("45\u00B0", "lat")).toBeNaN()
    expect(coordinataDa("--45", "lat")).toBeNaN()
    expect(coordinataDa("46,4843,12", "lat")).toBeNaN()
  })

  it("rilegge cio' che il formattatore ha appena scritto", () => {
    const scritte = coordinate(-33.8688, 151.2093).split(" - ")
    expect(coordinataDa(scritte[0]!, "lat")).toBe(-33.8688)
    expect(coordinataDa(scritte[1]!, "lon")).toBe(151.2093)
  })
})

describe("la data di una notte", () => {
  // Una notte arriva `YYYY-MM-DD` gia' nel fuso del sito: e' una data, non un istante. Letta con
  // `new Date(data)` diventa mezzanotte UTC e, mostrata nel fuso del browser, scivola al giorno
  // prima per chiunque stia a ovest di Greenwich -- in Arizona, o col NAS di casa guardato dagli
  // Stati Uniti.
  it("si scrive in italiano, non come esce dal database", () => {
    const scritta = notte("2025-11-30")

    expect(scritta).not.toBe("2025-11-30")
    expect(scritta).toContain("30")
    expect(scritta).toContain("2025")
  })

  it("resta lo stesso giorno anche guardata da un fuso a ovest", () => {
    // Phoenix e' UTC-7 tutto l'anno: mezzanotte UTC del 30 e' ancora il 29 sera, li'.
    process.env.TZ = "America/Phoenix"

    expect(notte("2025-11-30")).toContain("30")
    expect(notte("2025-11-30")).not.toContain("29")
  })

  it("e il giorno della settimana e' quello, non quello del fuso di chi guarda", () => {
    // Il 30 novembre 2025 e' una domenica. Letto nel fuso del browser da Phoenix sarebbe il 29,
    // cioe' **sabato**: il nome sbagliato, accanto alla data giusta.
    process.env.TZ = "America/Phoenix"

    expect(giornoDellaSettimana("2025-11-30")).toMatch(/domenica/i)
  })
})

describe("l'ora in cui e' successa una cosa", () => {
  // Un istante che il backend scrive in UTC (`clock.now_iso`): l'orologio di chi l'ha fatta
  // diceva un'altra ora, e a schermo va quella.
  const ISTANTE = "2026-09-20T22:30:00.000Z"

  it("si legge sull'orologio di chi guarda, insieme al giorno che le sta accanto", () => {
    // Kiritimati e' UTC+14: li' quelle 22:30 di Greenwich sono le 12:30 del giorno dopo. Le due
    // cose si provano insieme perche' insieme si leggono: nella riga di una lettura, se una e'
    // locale e l'altra in UTC, una scansione di mezzanotte porta il giorno prima accanto all'ora
    // dopo -- ed e' il difetto che c'era.
    process.env.TZ = "Pacific/Kiritimati"

    expect(orario(ISTANTE)).toBe("12:30")
    expect(giorno(ISTANTE)).toContain("21")
  })
})
