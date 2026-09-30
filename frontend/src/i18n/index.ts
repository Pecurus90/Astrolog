/**
 * Come un testo arriva a schermo: `t('chiave')`, mai un letterale nel componente.
 *
 * Niente dipendenza: un dizionario per lingua e una sostituzione di segnaposti sono tutto cio'
 * che serve finche' le lingue si contano sulle dita. Una libreria si fa entrare quando risolve
 * un difetto che abbiamo, non prima.
 *
 * Vincoli non ovvi:
 *
 * - **Una chiave che manca nella lingua scelta ricade sulla sorgente**, non su una stringa vuota
 *   ne' sul nome della chiave: chi legge vede l'italiano invece di un buco, e la guardia delle
 *   traduzioni e' l'unica a dover accorgersi del vuoto. Un `t()` che mostra `review.failed` a
 *   schermo e' un difetto che si scopre da un utente, non da una macchina.
 * - **I numeri scientifici non passano di qui.** `numero()` e' per conteggi, migliaia e durate;
 *   RA, Dec, magnitudine e scala sono identita' universali e restato col punto decimale in ogni
 *   lingua, come in ogni catalogo e software di acquisizione.
 */
import { en } from "./en"
import { it } from "./it"
import { LINGUA_SORGENTE, type Lingua } from "./lingue"

export const DIZIONARI: Record<Lingua, Record<string, string>> = { it, en }

export type Chiave = keyof typeof it

// La lingua di adesso. Oggi e' la sorgente e basta: la scelta dell'utente vive fra le
// preferenze del backend, e arriva quando c'e' una superficie per cambiarla.
const lingua: Lingua = LINGUA_SORGENTE

export function t(chiave: Chiave, valori?: Record<string, string | number>): string {
  const testo = singolare(chiave, valori) ?? DIZIONARI[lingua][chiave] ?? it[chiave]
  if (!valori) return testo
  return testo.replace(/\{(\w+)\}/g, (intero, nome: string) => {
    const valore = valori[nome]
    // Un segnaposto senza valore resta com'e': meglio un `{n}` visibile, che si nota e si
    // ripara, di un vuoto che sembra un testo scritto male.
    return valore === undefined ? intero : String(valore)
  })
}

/** La forma singolare, se il conto `n` e' 1 e la chiave ne ha una (`<chiave>.one`): la sceglie qui,
 *  una volta, invece che ogni pagina a mano. Il numero puo' arrivare gia' scritto per lo schermo, e 1
 *  si scrive "1" in ogni lingua che l'app ha. Il suffisso `.one` vuol dire solo questo. */
function singolare(chiave: string, valori?: Record<string, string | number>): string | undefined {
  if (valori?.n !== 1 && valori?.n !== "1") return undefined
  const una = `${chiave}.one`
  return DIZIONARI[lingua][una] ?? it[una as Chiave]
}

/** Il nome di un gruppo di frame su cui Da confermare chiede: la notte, o "senza data", e poi i
 *  pezzi che lo distinguono dagli altri gruppi, quelli che ci sono. Una casa sola per le sezioni
 *  che chiedono per gruppo, cosi' si leggono tutte allo stesso modo. */
export function nomeDelGruppo(night: string | null, parti: (string | null)[]): string {
  const prima = night === null ? t("review.group.noDate") : t("review.group.night", { notte: notte(night) })
  return [prima, ...parti.filter((p): p is string => p !== null)].join(" \u00b7 ")
}

/** Un punto del cielo come si legge accanto a un gruppo: `RA 98 Dec 4,9`, al decimo di grado. Dove
 *  puntava la montatura, o il centro di un mosaico, si riconosce a colpo d'occhio: non si misura. */
export function cielo(ra: number, dec: number): string {
  // `+ 0` perche' -0,04 al decimo e' -0, che si scriverebbe col segno
  const decimo = (gradi: number) => Math.round(gradi * 10) / 10 + 0
  // 359,99 al decimo e' 360, che e' lo stesso punto di 0
  return t("sky.point", { ra: numero(decimo(ra) % 360), dec: numero(decimo(dec)) })
}

/** Un conteggio come lo scrive la lingua di adesso (le migliaia, soprattutto). */
export function numero(n: number): string {
  return new Intl.NumberFormat(lingua).format(n)
}

/** Le coordinate di un posto, come si leggono accanto al suo nome: `46,4843 N - 12,0561 E`.
 *
 * Il verso si scrive con la lettera e non col segno meno: una latitudine negativa e' l'emisfero
 * sud, e "-33,86" chiede a chi legge di saperlo. Quattro decimali, che a queste latitudini sono
 * una decina di metri: piu' di cosi' finge una precisione che il posto non ha, e meno non
 * distingue due siti di osservazione vicini.
 *
 * Sta qui e non nella pagina del sito perche' e' formattazione di numeri, come `numero` e `ore`,
 * e la vorra' anche chi mostrera' il sito nella barra. */
export function coordinate(lat: number, lon: number): string {
  const formato = new Intl.NumberFormat(lingua, {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  })
  const verso = (n: number, positivo: Chiave, negativo: Chiave) =>
    `${formato.format(Math.abs(n))} ${t(n < 0 ? negativo : positivo)}`
  return `${verso(lat, "coord.n", "coord.s")} - ${verso(lon, "coord.e", "coord.w")}`
}

// Le lettere che questo lato **accetta**, un asse per volta: la `O` dell'italiano e la `W`
// dell'inglese stanno insieme perche' chi compila non sa in che lingua gli e' stata proposta la
// casella, e rifiutare "45 W" a un italiano vorrebbe dire rifiutare cio' che ogni catalogo del
// mondo scrive cosi'.
//
// **Divise per asse, e non tutte in un mucchio**: `"45 W"` scritto nella latitudine, letto da una
// tabella sola, diventava 45 gradi **sud** -- un numero giusto su un emisfero che nessuno aveva
// chiesto, salvato senza una parola. Una lettera dell'altro asse adesso non e' un numero.
const VERSI = {
  lat: { n: 1, s: -1 },
  lon: { e: 1, o: -1, w: -1 },
} as const

/** L'asse su cui si sta leggendo: decide quali lettere hanno senso. */
export type Asse = keyof typeof VERSI

/** Una coordinata **scritta a mano**, riletta come numero: l'inverso di `coordinate`.
 *
 * Esiste perche' `Number("46,4843")` e' `NaN`, e il segnaposto che l'app propone a un italiano
 * porta la virgola: senza questa, chi copia esattamente cio' che gli viene suggerito trova il
 * tasto spento e nessun motivo. Accetta anche la lettera del verso -- `46,4843 N`, come il
 * disegno la mostra e come `coordinate` la scrive -- cosi' cio' che si legge a schermo si puo'
 * riscrivere nel campo senza tradurlo.
 *
 * **La lettera comanda sul segno**: "45 S" e' sud, e "-45 S" pure, perche' due modi di dire la
 * stessa cosa non fanno un nord. Cio' che non e' un numero resta `NaN`, compreso il campo vuoto:
 * `Number("")` fa zero, e zero-zero e' un punto nel Golfo di Guinea. */
export function coordinataDa(scritto: string, asse: Asse): number {
  const pulito = scritto.trim().replace(",", ".")
  const ultima = pulito.slice(-1).toLowerCase()
  const verso = (VERSI[asse] as Record<string, number | undefined>)[ultima]
  // Una lettera che non e' di questo asse non si ignora: `"45 W"` in latitudine non e' 45, e'
  // qualcosa che chi scrive ha in testa e noi non sappiamo leggere.
  if (verso === undefined && /[a-z]/.test(ultima)) return Number.NaN
  const cifre = (verso === undefined ? pulito : pulito.slice(0, -1)).trim()
  if (cifre === "") return Number.NaN
  const n = Number(cifre)
  return verso === undefined ? n : verso * Math.abs(n)
}

/** I secondi di posa come si leggono a schermo: **in ore**.
 *
 * Il backend manda `integration_s` e dichiara che "a schermo si legge in ore": qui si cambia
 * unita' e si formatta, che e' il mestiere di questo lato. Sta in una casa sola perche' la stessa
 * conversione la vorranno le altre sezioni, e un `/ 3600` ricopiato in tre componenti e' lo stesso
 * fatto in tre posti. Un decimale: il secondo non si legge, e "2,73 h" finge una precisione che
 * la somma di pose arrotondate non ha.
 *
 * Ma un tempo **vero** sotto quel decimale non si scrive zero: un frame da un minuto diventerebbe
 * "0 h", che a schermo vuol dire "qui non c'e' tempo". Sotto la soglia in cui l'arrotondamento lo
 * azzererebbe si scrive "< 0,1". Lo zero vero resta zero. */
export function ore(secondi: number): string {
  const formato = new Intl.NumberFormat(lingua, { maximumFractionDigits: 1 })
  // 0,05 h e' il punto sotto cui un decimale arrotonda a zero
  if (secondi > 0 && secondi / 3600 < 0.05) return `< ${formato.format(0.1)}`
  return formato.format(secondi / 3600)
}

/** Quanto e' durata una cosa, come si legge: `4 s`, `2 min 14 s`, `1 h 12 min`.
 *
 * Non e' `ore()`, che serve alle **ore di integrazione** e scrive un decimale: una lettura dura
 * secondi, e "0 h" direbbe che non e' successo niente.
 *
 * **L'unita' piu' piccola cade quando quella grande e' abbastanza grande**: sotto il minuto i
 * secondi sono tutto; sopra il minuto dicono ancora se vale la pena aspettare la prossima; sopra
 * l'ora sono rumore. E un resto **zero non si scrive**: "2 min 0 s" non aggiunge niente a "2 min".
 *
 * Un tempo **vero** sotto il secondo non si scrive zero, come in `ore()`: una cartella piccola si
 * legge in decimi, e "0 s" e' cio' che scriverebbe una corsa mai partita. Lo zero vero resta zero.
 *
 * `undefined` per una durata che non c'e' -- una corsa ancora aperta -- cosi' chi chiama mostra il
 * suo "sta leggendo" invece di uno zero che direbbe "finita in un istante". */
export function durata(secondi: number | null): string | undefined {
  if (secondi === null) return undefined
  if (secondi > 0 && secondi < 0.5) return `< ${numero(1)} s`
  const tondi = Math.round(secondi)
  if (tondi < 60) return `${numero(tondi)} s`
  const min = Math.floor(tondi / 60)
  if (min < 60) {
    const resto = tondi % 60
    return resto === 0 ? `${numero(min)} min` : `${numero(min)} min ${numero(resto)} s`
  }
  const restoMin = min % 60
  return restoMin === 0
    ? `${numero(Math.floor(min / 60))} h`
    : `${numero(Math.floor(min / 60))} h ${numero(restoMin)} min`
}

/** L'ora di un istante **nel fuso del sito**, come `15:49`.
 *
 * Si legge dalla stringa, non da `Date`: l'ISO che arriva porta gia' l'ora del posto e il suo
 * scarto, e passare da `Date` la rimostrerebbe nel fuso del browser -- cioe' sbagliata per
 * chiunque guardi l'archivio da fuori casa. E' la stessa ragione per cui `notte()` legge in UTC. */
export function oraDelSito(istante: string): string {
  return istante.slice(11, 16)
}

/** L'ora di un **istante**, nel fuso di chi guarda: `00:30`.
 *
 * Non e' `oraDelSito()`, e la differenza si vede a schermo: quella **taglia** la stringa perche'
 * l'ISO delle effemeridi porta gia' l'ora del posto col suo scarto, mentre un istante scritto dal
 * backend (`clock.now_iso`) e' in UTC -- tagliato, mostrerebbe l'ora di Greenwich a chiunque non
 * ci abiti. Va **in coppia con `giorno()`**, che legge nello stesso fuso: uno locale e l'altro in
 * UTC fanno una riga che nomina due momenti diversi. */
export function orario(istante: string): string {
  return new Intl.DateTimeFormat(lingua, { hour: "2-digit", minute: "2-digit" }).format(
    new Date(istante),
  )
}

/** Il giorno di un **istante**, nel fuso di chi guarda.
 *
 * Non e' `notte()`: quella formatta una **data** gia' data, e la legge in UTC apposta. Qui arriva
 * un istante UTC -- quando una cosa e' stata fatta -- e il giorno giusto e' quello dell'orologio
 * di chi l'ha fatta: una cartella aggiunta all'una di notte, letta in UTC, si racconterebbe col
 * giorno prima. */
export function giorno(istante: string): string {
  return new Intl.DateTimeFormat(lingua, { day: "numeric", month: "short", year: "numeric" }).format(
    new Date(istante),
  )
}

/** La data di una notte, come si legge a schermo.
 *
 * Arriva `YYYY-MM-DD` gia' nel fuso del sito: e' una **data**, non un istante. Letta con
 * `new Date(data)` diventa mezzanotte UTC, e mostrata nel fuso del browser scivola al giorno prima
 * per chiunque stia a ovest di Greenwich -- in Arizona, o sul NAS di casa guardato dagli Stati
 * Uniti. Quindi si legge **e si scrive in UTC**: il giorno esce identico a quello del database. */
export function notte(data: string): string {
  return new Intl.DateTimeFormat(lingua, {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(mezzanotteUtc(data))
}

/** Una data `YYYY-MM-DD` come istante: mezzanotte **UTC**, che e' il solo modo di rileggerla
 *  senza farla scivolare di un giorno. Chi la mostra tiene `timeZone: "UTC"` anche nel formato,
 *  o la riporterebbe nel fuso del browser dall'altra parte. */
function mezzanotteUtc(data: string): Date {
  return new Date(`${data}T00:00:00Z`)
}

/** Che giorno della settimana era quella notte: *sabato*, *venerdi'*. In UTC come `notte`, o a
 *  ovest di Greenwich uscirebbe il nome del giorno prima. */
export function giornoDellaSettimana(data: string): string {
  return new Intl.DateTimeFormat(lingua, { weekday: "long", timeZone: "UTC" }).format(
    mezzanotteUtc(data),
  )
}
