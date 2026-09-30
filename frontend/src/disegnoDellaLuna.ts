/**
 * La geometria della Luna: il disco della fase e la curva della notte, per **tutte e due** le
 * tele che le disegnano -- la striscia in barra e il pannello.
 *
 * Non e' derivazione di dati -- quella sta nel backend -- e' **disegno**: numeri che diventano
 * un tracciato SVG. Sta in un file suo perche' e' la parte che si puo' provare senza montare
 * niente.
 */

import type { components } from "./api/schema"

/** Il raggio del disco nel suo `viewBox`, che e' `-12 -12 24 24` come nel foglio. */
const RAGGIO = 10

/** Sotto l'orizzonte il grafico mostra questo tanto di terreno, e non di piu': basta a vedere
 *  dove la Luna entra ed esce, e non sprofonda il resto. Viene dal disegno. */
export const PAVIMENTO_DEG = -15

/**
 * Il tracciato della parte illuminata, o `null` quando non c'e' niente da illuminare.
 *
 * Due archi: il bordo del disco, e il **terminatore**, che e' una mezza ellisse la cui larghezza
 * viene dalla frazione illuminata -- piatta al quarto, larga come il disco alla piena.
 *
 * **Da che parte sta il lembo illuminato lo dice il backend** (`lit_side`), che conosce la fase
 * **e** l'emisfero: una crescente e' illuminata a destra da noi e a sinistra in Australia.
 */
export function tracciatoDellaLuna(illuminazionePct: number, aDestra: boolean): string | null {
  if (illuminazionePct <= 0) return null
  const frazione = illuminazionePct / 100
  const bordo = aDestra ? 1 : 0
  // Il terminatore curva dalla parte del lembo quando e' gibbosa, dall'altra quando e' falce.
  const terminatore = frazione > 0.5 ? bordo : 1 - bordo
  const larghezza = (RAGGIO * Math.abs(1 - 2 * frazione)).toFixed(2)
  return (
    `M 0 ${-RAGGIO} A ${RAGGIO} ${RAGGIO} 0 0 ${bordo} 0 ${RAGGIO}` +
    ` A ${larghezza} ${RAGGIO} 0 0 ${terminatore} 0 ${-RAGGIO} Z`
  )
}

/** Un punto della notte come lo manda la rotta. */
export type Punto = { at: string; altitude_deg: number }

/** Un pezzo di notte in cui il cielo e' sempre la stessa cosa, come lo manda la rotta. La forma
 *  viene dallo schema, cosi' una fascia nuova nel backend non compila finche' non ha la sua
 *  tinta. */
export type Fascia = components["schemas"]["SkyBandOut"]

/** Ogni quante ore si segna una tacca sull'asse del tempo. Sei ne fanno cinque su una notte
 *  intera -- mezzogiorno, sera, mezzanotte, mattino, mezzogiorno -- che bastano a leggere la curva
 *  contro l'orologio senza affollare 480px. */
const TACCA_OGNI_ORE = 6

/** Il disegno della notte dentro una tela larga `larghezza` e alta `altezza`.
 *
 * `curva` e' l'altezza della Luna, `orizzonte` la riga dello zero, `adesso` la colonna di
 * adesso -- o `null` se cade fuori dalla notte, che succede solo quando i numeri sono scaduti.
 *
 * `tacche` sono le ore da scrivere sotto la tela. Si **prendono dai campioni**, non si calcolano:
 * la curva arriva a passo di un quarto d'ora da mezzogiorno, quindi le ore tonde ci sono gia', e
 * un'ora costruita qui sarebbe aritmetica da orologio da parete -- la notte del cambio d'ora dura
 * 23 o 25 ore, e un passo fisso ci inciamperebbe. Se fra i campioni un'ora tonda non c'e', non si
 * disegna: una tacca e' un istante vero, o non e'.
 */
export function curvaDellaNotte(
  track: Punto[],
  tettoDeg: number,
  larghezza: number,
  altezza: number,
  quando: Date,
  fasce: readonly Fascia[] = [],
): {
  curva: string
  orizzonte: number
  adesso: number | null
  tacche: { x: number; at: string }[]
  fasceDipinte: { x: number; larghezza: number; kind: Fascia["kind"]; starts_at: string }[]
} | null {
  const primo = track[0]
  const ultimo = track[track.length - 1]
  if (!primo || !ultimo || track.length < 2) return null
  const inizio = Date.parse(primo.at)
  const fine = Date.parse(ultimo.at)
  const alto = tettoDeg - PAVIMENTO_DEG
  const y = (gradi: number) => altezza * (1 - (gradi - PAVIMENTO_DEG) / alto)
  const x = (istante: number) => (larghezza * (istante - inizio)) / (fine - inizio)

  const curva = track
    .map((p, i) => `${i === 0 ? "M" : "L"} ${x(Date.parse(p.at)).toFixed(1)} ${y(p.altitude_deg).toFixed(1)}`)
    .join(" ")
  const adessoMs = quando.getTime()
  // Un campione e' una tacca se segna un'ora tonda del **fuso del sito**, che sta gia' scritta
  // nell'ISO che arriva, e se quell'ora e' un multiplo del passo. Qui esce l'**istante**: come si
  // scrive un'ora lo sa `i18n.oraDelSito`, e questo file fa geometria.
  const tacche = track
    .filter((p) => p.at.slice(14, 16) === "00" && Number(p.at.slice(11, 13)) % TACCA_OGNI_ORE === 0)
    .map((p) => ({ x: x(Date.parse(p.at)), at: p.at }))
  // Le fasce passano per la **stessa** scala del tempo della curva: due scale diverse e il buio
  // non starebbe piu' sotto la Luna che lo attraversa.
  const fasceDipinte = fasce.map((f) => {
    const da = x(Date.parse(f.starts_at))
    // `starts_at` viaggia con la fascia dipinta: e' la sua identita'. Due fasce possono avere la
    // stessa `x` -- una lunga zero, se un attraversamento cade esatto su un campione -- e con due
    // chiavi uguali React non le distingue: aggiornandone una puo' toccare l'altra.
    return { x: da, larghezza: x(Date.parse(f.ends_at)) - da, kind: f.kind, starts_at: f.starts_at }
  })
  return {
    curva,
    orizzonte: y(0),
    adesso: adessoMs >= inizio && adessoMs <= fine ? x(adessoMs) : null,
    tacche,
    fasceDipinte,
  }
}
