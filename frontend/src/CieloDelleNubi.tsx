import { type KeyboardEvent, type PointerEvent, useRef, useState } from "react"

import { oraDalTasto, parola } from "./CartaDelParametro"
import type { components } from "./api/schema"
import { type Chiave, numero, oraDelSito, t } from "./i18n"

type Notte = components["schemas"]["WeatherNightOut"]
type Misura = components["schemas"]["WeatherMeasureOut"]
type Ora = components["schemas"]["WeatherHourOut"]
type Scala = components["schemas"]["WeatherScaleOut"]
type Seeing = components["schemas"]["WeatherSeeingOut"]
type Livello = NonNullable<Misura["level"]>
type Destra = "rain" | "wind" | "condensation" | "seeing" | "jet" | "aerosol"
type Campo = "precip_mm" | "wind_kmh" | "temperature_c" | "seeing_arcsec" | "wind_250hpa_kmh" | "aerosol_optical_depth"

/** Le metriche della scala di destra, una alla volta (DECISIONI del disegno, v27). */
export const A_DESTRA: readonly Destra[] = ["rain", "wind", "condensation", "seeing", "jet", "aerosol"]

// Il campo che ogni metrica disegna, la sua unita' e la misura che da' la scala: la condensa si
// disegna come aria e rugiada, sulla scala della temperatura.
const DISEGNO: Record<Destra, { campo: Campo; unita: Chiave | null; scala: Misura["code"] }> = {
  rain: { campo: "precip_mm", unita: "weather.unit.mm", scala: "rain" },
  wind: { campo: "wind_kmh", unita: "weather.unit.kmh", scala: "wind" },
  condensation: { campo: "temperature_c", unita: "weather.unit.celsius", scala: "temperature" },
  seeing: { campo: "seeing_arcsec", unita: "weather.unit.arcsec", scala: "seeing" },
  jet: { campo: "wind_250hpa_kmh", unita: "weather.unit.kmh", scala: "jet" },
  // lo spessore ottico non ha unita': in testa alla scala va il suo nome
  aerosol: { campo: "aerosol_optical_depth", unita: null, scala: "aerosol" },
}

const TAPPE = {
  day: "as-volta__tappa--giorno",
  civil: "as-volta__tappa--civile",
  nautical: "as-volta__tappa--nautico",
  astronomical: "as-volta__tappa--astro",
  dark: "as-volta__tappa--notte",
} as const
const TINTE = {
  go: "as-scala__tinta--buona",
  marginal: "as-scala__tinta--incerta",
  nogo: "as-scala__tinta--niente",
  neutro: "as-scala__tinta--neutro",
} as const
const PAROLE = { go: "as-scala__parola--buona", marginal: "as-scala__parola--incerta", nogo: "as-scala__parola--niente" } as const
const RIGHE = { go: "as-cielo__riga--buona", marginal: "as-cielo__riga--incerta", nogo: "as-cielo__riga--niente", sotto: "as-cielo__riga--sotto" } as const

// La tela: larga quanto il disegno del desktop; sul telefono si stringe col viewBox.
const LARGO = 1080
const ALTO = 300
const SINISTRA = 44
const DESTRA = 48
const CIMA = 30
const FONDO = ALTO - 26

/** Una metrica di destra che non si sceglie (il seeing senza chiave) e perche'. */
function bloccata(d: Destra, seeing: Seeing): Chiave | null {
  if (d !== "seeing") return null
  if (!seeing.key) return "weather.right.seeing.noKey"
  return seeing.meteoblue === "refused" ? "weather.right.seeing.refused" : null
}

/** Cosa dice una metrica nella notte, accanto al suo nome nell'elenco: le sue parole e le ore. */
function detto(m: Misura | undefined, finestra: number): string {
  if (!m || m.known_hours === 0) return t("weather.card.unknown")
  const manca = m.known_until && m.known_hours < finestra ? ` \u00b7 ${t("weather.card.missingSince", { da: oraDelSito(m.known_until) })}` : ""
  if (m.level === null) return `${t("weather.right.noWord")}${manca}`
  if (m.spans.length === 0) return `${t("weather.card.allNight", { parola: parola(m.code, m.level) })}${manca}`
  return `${m.spans.map((s) => t("weather.card.since", { parola: parola(m.code, s.level), da: oraDelSito(s.since) })).join(", ")}${manca}`
}

/**
 * Il cielo della notte (`as-cielo`, foglio 63 e 64): dall'ultima ora di giorno all'alba le nubi
 * basse, medie e alte ognuna dal suo zero, l'umidita' sulla stessa scala in %, e a destra una
 * metrica alla volta col colore del suo giudizio ora per ora. Il filo dell'ora porta tutte le carte
 * a quell'ora (`scegli`). Tutti i numeri e i giudizi arrivano scritti: qui si disegna e basta.
 */
export function CieloDelleNubi({
  notte: n,
  ore,
  scale,
  seeing,
  ora,
  scegli,
}: {
  notte: Notte
  ore: Ora[]
  scale: Scala[]
  seeing: Seeing
  ora: number | null
  scegli: (i: number | null) => void
}) {
  // la metrica che pesa di piu' si apre da sola: le misure arrivano gia' in ordine d'importanza
  const ordine = n.measures.flatMap((m) => (A_DESTRA as readonly string[]).includes(m.code) ? [m.code as Destra] : [])
  const prima = n.measures.find((m) => m.weighs && (A_DESTRA as readonly string[]).includes(m.code))?.code as Destra | undefined
  const [destra, setDestra] = useState<Destra | null>(prima ?? null)
  const [umidita, setUmidita] = useState(true)
  const [menu, setMenu] = useState(false)
  const tela = useRef<HTMLDivElement>(null)
  const passo = (LARGO - SINISTRA - DESTRA) / (ore.length || 1)
  const x = (i: number) => SINISTRA + (i + 0.5) * passo
  const y = (v: number) => FONDO - (v / 100) * (FONDO - CIMA)
  const misura = (c: Misura["code"]) => n.measures.find((m) => m.code === c)

  const oraDa = (ev: PointerEvent<HTMLDivElement>) => {
    const q = ev.currentTarget.getBoundingClientRect()
    const i = Math.floor((((ev.clientX - q.left) / q.width) * LARGO - SINISTRA) / passo)
    return i < 0 || i >= ore.length ? null : i
  }
  const tasto = (ev: KeyboardEvent<HTMLDivElement>) => {
    const nuova = oraDalTasto(ev.key, ora, ore.length - 1)
    if (nuova === undefined) return
    ev.preventDefault()
    scegli(nuova)
  }
  const qui = ora === null ? undefined : ore[ora]
  const nomeDestra = destra ? t(`weather.right.${destra}` as Chiave) : t("weather.right.none")

  return (
    <div className="as-cielo">
      <div className="as-strati" role="group" aria-label={t("weather.right.label")}>
        <span className="as-strati__eti as-meteo__solo-largo">{t("weather.sky.left")}</span>
        <button className="as-strato" type="button" aria-pressed={umidita} onClick={() => setUmidita(!umidita)}>
          <i aria-hidden="true" />
          {t("weather.sky.humidity")}
        </button>
        <div className="as-menu as-menu--telefono">
          <button className="as-menu__apri" type="button" aria-expanded={menu} onClick={() => setMenu(!menu)}>
            <span>{t("weather.right.menu")}</span>
            <b>{nomeDestra}</b>
            <i aria-hidden="true">{"\u25be"}</i>
          </button>
          <ul className="as-menu__voci as-menu__voci--elenco" role="menu" hidden={!menu}>
            <li>
              <button className="as-menu__voce" type="button" role="menuitemradio" aria-checked={destra === null}
                onClick={() => { setDestra(null); setMenu(false) }}>
                <span className="as-menu__nome">{t("weather.right.none")}</span>
                <span className="as-menu__dove">{t("weather.right.noneWhat")}</span>
              </button>
            </li>
            {ordine.map((d) => {
              const perche = bloccata(d, seeing)
              return (
                <li key={d}>
                  <button className="as-menu__voce" type="button" role="menuitemradio" aria-checked={destra === d}
                    aria-disabled={perche !== null} onClick={() => { if (perche === null) { setDestra(d); setMenu(false) } }}>
                    <span className="as-menu__nome">{t(`weather.right.${d}` as Chiave)}</span>
                    <span className="as-menu__dove">{perche ? t(perche) : detto(misura(d), n.window_hours ?? 0)}</span>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
        <span className="as-strati__eti as-meteo__solo-largo">{t("weather.sky.right")}</span>
        {ordine.map((d) => {
          const perche = bloccata(d, seeing)
          return (
            <button key={d} className="as-strato as-meteo__solo-largo" type="button" aria-pressed={destra === d}
              aria-disabled={perche !== null} title={perche ? t(perche) : undefined}
              onClick={() => { if (perche === null) setDestra(destra === d ? null : d) }}>
              <i aria-hidden="true" />
              {t(`weather.right.${d}` as Chiave)}
            </button>
          )
        })}
      </div>
      <div ref={tela} className="as-cielo__tela" tabIndex={0} role="slider" aria-label={t("weather.sky.label")}
        aria-valuemin={0} aria-valuemax={ore.length - 1} aria-valuenow={ora ?? undefined}
        aria-valuetext={qui ? t("weather.sky.at", {
          ora: oraDelSito(qui.at),
          b: valore(qui.cloud_low_pct), m: valore(qui.cloud_mid_pct), a: valore(qui.cloud_high_pct), u: valore(qui.humidity_pct),
        }) : t("weather.sky.night")}
        onPointerMove={(ev) => scegli(oraDa(ev))} onPointerDown={(ev) => scegli(oraDa(ev))}
        // col dito il filo resta dove si e' alzato: solo il mouse che esce torna alla notte
        onPointerLeave={(ev) => { if (ev.pointerType === "mouse") scegli(null) }} onKeyDown={tasto} onBlur={() => scegli(null)}>
        <svg viewBox={`0 0 ${LARGO} ${ALTO}`} role="img" aria-label={t("weather.sky.img")} data-dx-acceso={destra ? "" : undefined}>
          <defs>
            <pattern id={`cielo-${n.night}-tr`} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="6" className="as-scala__tratteggio" />
            </pattern>
            <linearGradient id={`cielo-${n.night}-c`} x1="0" x2="1">
              {ore.map((o, i) => (
                <stop key={o.at} offset={`${((i + 0.5) / ore.length) * 100}%`} className={`${TAPPE[o.sky]}`} />
              ))}
            </linearGradient>
          </defs>
          <rect width={LARGO} height={ALTO} fill={`url(#cielo-${n.night}-c)`} />
          {[0, 50, 100].map((v) => (
            <g key={v}>
              <line className="as-volta__griglia" x1={SINISTRA} x2={LARGO - DESTRA} y1={y(v)} y2={y(v)} />
              <text className="as-volta__gradi" x={SINISTRA - 6} y={y(v) + 4} textAnchor="end">{`${v}%`}</text>
            </g>
          ))}
          <Strato ore={ore} campo="cloud_high_pct" classe="as-cielo__alte" filo="as-cielo__alte-filo" x={x} y={y} />
          <Strato ore={ore} campo="cloud_mid_pct" classe="as-cielo__medie" filo="as-cielo__medie-filo" x={x} y={y} />
          <Strato ore={ore} campo="cloud_low_pct" classe="as-cielo__basse" filo="as-cielo__basse-filo" x={x} y={y} />
          {umidita && (
            <polyline className="as-cielo__umidita"
              points={ore.flatMap((o, i) => (o.humidity_pct === null ? [] : [`${x(i)},${y(o.humidity_pct)}`])).join(" ")} />
          )}
          {/* la soglia della condensa vale sullo scarto aria-rugiada, non sull'asse della temperatura */}
          {destra && (
            <ScalaDiDestra destra={destra} ore={ore} misura={misura(DISEGNO[destra].scala)}
              scala={DISEGNO[destra].scala === destra ? scale.find((s) => s.code === destra) : undefined}
              x={x} passo={passo} id={`cielo-${n.night}-tr`} />
          )}
          <text className="as-scala__unita" x={SINISTRA - 6} y={CIMA - 10} textAnchor="end">%</text>
          <line className="as-volta__orizzonte" x1={SINISTRA} x2={LARGO} y1={FONDO} y2={FONDO} />
          <rect className="as-volta__terra" x={0} y={FONDO + 0.5} width={LARGO} height={ALTO - FONDO} />
          <Sereno notte={n} ore={ore} passo={passo} />
          {ore.map((o, i) => (
            <text key={o.at} className="as-volta__ora" x={x(i)} y={ALTO - 8} textAnchor="middle">{oraDelSito(o.at).slice(0, 2)}</text>
          ))}
        </svg>
        {qui && ora !== null && (
          <>
            <div className="as-volta__lettore-filo" style={{ left: `${(x(ora) / LARGO) * 100}%` }} />
            <Lettore ora={qui} destra={destra} nomeDestra={nomeDestra} sinistra={ora > ore.length / 2} x={(x(ora) / LARGO) * 100} />
          </>
        )}
      </div>
      <p className="as-cielo__legenda">
        <span><i className="as-cielo__campione--basse" />{t("weather.sky.legend.low")}</span>
        <span><i className="as-cielo__campione--medie" />{t("weather.sky.legend.mid")}</span>
        <span><i className="as-cielo__campione--alte" />{t("weather.sky.legend.high")}</span>
        <span><i className="as-cielo__campione--umidita" />{t("weather.sky.humidity")}</span>
        <span>{t("weather.sky.legend.right")}</span>
        {ore.length > 0 && (
          <span>{t("weather.sky.legend.span", { da: oraDelSito(ore[0]?.at ?? ""), a: oraDelSito(ore[ore.length - 1]?.at ?? "") })}</span>
        )}
      </p>
    </div>
  )
}

function valore(v: number | null): string {
  return v === null ? t("weather.card.unknown") : numero(v)
}

/** Uno strato di nubi dal suo zero, mai sommato agli altri: si coprono. */
function Strato({ ore, campo, classe, filo, x, y }: {
  ore: Ora[]; campo: "cloud_low_pct" | "cloud_mid_pct" | "cloud_high_pct"; classe: string; filo: string
  x: (i: number) => number; y: (v: number) => number
}) {
  const punti = ore.flatMap((o, i) => (o[campo] === null ? [] : [`${x(i)},${y(o[campo] as number)}`]))
  if (punti.length === 0) return null
  return (
    <>
      <path className={`${classe}`} d={`M${x(0)},${FONDO} L${punti.join(" L")} L${x(ore.length - 1)},${FONDO} Z`} />
      <polyline className={`${filo}`} points={punti.join(" ")} />
    </>
  )
}

/** Il tratto sereno sull'orizzonte: le ore che il backend dice serene, a pezzi, e quante sono. */
function Sereno({ notte: n, ore, passo }: { notte: Notte; ore: Ora[]; passo: number }) {
  const pezzi: [number, number][] = []
  ore.forEach((o, i) => {
    if (!o.clear) return
    const ultimo = pezzi[pezzi.length - 1]
    if (ultimo && ultimo[1] === i - 1) ultimo[1] = i
    else pezzi.push([i, i])
  })
  const fine = pezzi.length ? SINISTRA + ((pezzi[pezzi.length - 1]?.[1] ?? 0) + 1) * passo - 2 : SINISTRA
  return (
    <>
      {pezzi.map(([a, b]) => (
        <line key={a} className="as-cielo__sereno" x1={SINISTRA + a * passo + 2} x2={SINISTRA + (b + 1) * passo - 2} y1={13} y2={13} />
      ))}
      <text className="as-volta__scritta" x={pezzi.length ? fine + 6 : SINISTRA} y={17}>
        {n.usable_hours ? t("weather.sky.clear", { n: numero(n.usable_hours) }) : t("weather.sky.noClear")}
      </text>
    </>
  )
}

/** La metrica scelta sulla scala di destra: le tacche delle soglie, il tratto col colore del
 *  giudizio di ogni ora (spezzato dove il giudizio cambia), la parola dove cambia, il tratteggio
 *  dove il servizio tace. La condensa e' aria e rugiada; il vento porta le raffiche. */
function ScalaDiDestra({ destra, ore, misura: m, scala, x, passo, id }: {
  destra: Destra; ore: Ora[]; misura: Misura | undefined; scala: Scala | undefined
  x: (i: number) => number; passo: number; id: string
}) {
  const { campo, unita } = DISEGNO[destra]
  const basso = m?.axis_min ?? 0
  const alto = m?.axis_max ?? 1
  const y = (v: number) => FONDO - ((v - basso) / (alto - basso || 1)) * (FONDO - CIMA)
  const livello = (o: Ora) => o.levels[destra]
  const tacche = [basso, ...(scala?.steps ?? []).map((s) => s.bound).filter((b) => b > basso && b < alto), alto]
  const soglie = new Set((scala?.steps ?? []).map((s) => s.bound))
  return (
    <g>
      {tacche.map((v) => (
        <g key={v}>
          {soglie.has(v) && <line className="as-scala__soglia" x1={SINISTRA} x2={LARGO - DESTRA} y1={y(v)} y2={y(v)} />}
          <text className={soglie.has(v) ? "as-scala__eti as-scala__eti--soglia" : "as-scala__eti"} x={LARGO - DESTRA + 6} y={y(v) + 4}>{numero(v)}</text>
        </g>
      ))}
      <text className="as-scala__unita" x={LARGO - 4} y={CIMA - 10} textAnchor="end">{t(unita ?? "weather.right.aerosol")}</text>
      {destra === "rain" ? (
        <Tratti ore={ore} valore={(o) => o.precip_mm} livello={livello} x={x} y={y} passo={passo} id={id} classe="" barre />
      ) : (
        <>
          {destra === "condensation" &&
            ore.map((o, i) =>
              o.levels.condensation === "nogo" && o.temperature_c !== null && o.dew_point_c !== null ? (
                <rect key={`c-${o.at}`} className="as-scala__tocca" x={SINISTRA + i * passo} y={y(o.temperature_c)}
                  width={passo + 0.3} height={Math.max(2, y(o.dew_point_c) - y(o.temperature_c))} />
              ) : null,
            )}
          {destra === "condensation" && (
            <polyline className="as-scala__rugiada" points={ore.flatMap((o, i) => (o.dew_point_c === null ? [] : [`${x(i)},${y(o.dew_point_c)}`])).join(" ")} />
          )}
          {destra === "wind" && (
            <Tratti ore={ore} valore={(o) => o.wind_gust_kmh} livello={(o) => (o.levels.gust === "nogo" ? "nogo" : null)} x={x} y={y} passo={passo} id={id} classe=" as-scala__tratto--raffiche" />
          )}
          <Tratti ore={ore} valore={(o) => o[campo]} livello={livello} x={x} y={y} passo={passo} id={id} classe="" />
        </>
      )}
      <Parole ore={ore} destra={destra} valore={(o) => (destra === "rain" ? null : o[campo])} y={y} passo={passo} />
    </g>
  )
}

/** Il tratto a pezzi: un pezzo per ogni corsa di ore con la stessa parola, unito a mezz'ora con
 *  quello prima (o a barre, per la pioggia); le ore senza valore sono un tratteggio con "non fornito". */
function Tratti({ ore, valore, livello, x, y, passo, id, classe, barre = false }: {
  ore: Ora[]; valore: (o: Ora) => number | null; livello: (o: Ora) => Livello | null
  x: (i: number) => number; y: (v: number) => number; passo: number; id: string; classe: string; barre?: boolean
}) {
  const pezzi: { da: number; a: number; vuoto: boolean; l: Livello | null }[] = []
  ore.forEach((o, i) => {
    const vuoto = valore(o) === null
    const l = vuoto ? null : livello(o)
    const ultimo = pezzi[pezzi.length - 1]
    if (ultimo && ultimo.vuoto === vuoto && ultimo.l === l) ultimo.a = i
    else pezzi.push({ da: i, a: i, vuoto, l })
  })
  return (
    <>
      {pezzi.map((p) => {
        if (p.vuoto) {
          return (
            <g key={p.da}>
              <rect x={SINISTRA + p.da * passo} y={CIMA} width={(p.a - p.da + 1) * passo} height={FONDO - CIMA} fill={`url(#${id})`} />
              <text className="as-scala__eti" x={SINISTRA + p.da * passo + 6} y={CIMA + 14}>{t("weather.card.unknown")}</text>
            </g>
          )
        }
        const tinta = TINTE[p.l ?? "neutro"]
        if (barre) {
          return ore.slice(p.da, p.a + 1).map((o, k) => {
            const v = valore(o) as number
            return v > 0 ? <rect key={o.at} className={`as-scala__barra ${tinta}`} x={x(p.da + k) - passo * 0.28} y={y(v)} width={passo * 0.56} height={FONDO - y(v)} rx={2} /> : null
          })
        }
        const prima = ore[p.da - 1]
        const dopo = ore[p.a + 1]
        const punti: string[] = []
        const v0 = prima ? valore(prima) : null
        if (v0 !== null) punti.push(`${x(p.da) - passo / 2},${(y(valore(ore[p.da] as Ora) as number) + y(v0)) / 2}`)
        for (let k = p.da; k <= p.a; k++) punti.push(`${x(k)},${y(valore(ore[k] as Ora) as number)}`)
        const v1 = dopo ? valore(dopo) : null
        if (v1 !== null) punti.push(`${x(p.a) + passo / 2},${(y(valore(ore[p.a] as Ora) as number) + y(v1)) / 2}`)
        return <polyline key={p.da} className={`as-scala__tratto ${tinta}${classe}`} points={punti.join(" ")} />
      })}
    </>
  )
}

/** La parola del giudizio dove cambia ("niente dalle 22"), senza sovrapporsi alla precedente. */
function Parole({ ore, destra, valore, y, passo }: {
  ore: Ora[]; destra: Destra; valore: (o: Ora) => number | null; y: (v: number) => number; passo: number
}) {
  const scritte: { i: number; l: Livello; testo: string; x0: number }[] = []
  let fine = SINISTRA
  ore.forEach((o, i) => {
    const l = o.levels[destra]
    if (l === null || (i > 0 && ore[i - 1]?.levels[destra] === l)) return
    const testo = i === 0 ? parola(destra, l) : t("weather.card.since", { parola: parola(destra, l), da: oraDelSito(o.at).slice(0, 2) })
    const largo = testo.length * 6.3
    const x0 = Math.min(SINISTRA + i * passo + 3, LARGO - DESTRA - 3 - largo)
    if (x0 < fine) return
    fine = x0 + largo + 10
    scritte.push({ i, l, testo, x0 })
  })
  return (
    <>
      {scritte.map((s) => {
        const v = valore(ore[s.i] as Ora)
        return (
          <text key={s.i} className={`as-scala__parola ${PAROLE[s.l]}`} x={s.x0} y={v === null ? CIMA + 14 : Math.max(CIMA + 12, y(v) - 9)}>{s.testo}</text>
        )
      })}
    </>
  )
}

/** Il lettore sotto il filo: l'ora, i tre strati e l'umidita', e la metrica di destra con la sua
 *  parola. */
function Lettore({ ora: o, destra, nomeDestra, sinistra, x }: { ora: Ora; destra: Destra | null; nomeDestra: string; sinistra: boolean; x: number }) {
  const righe: [string, string, string][] = [
    ["as-cielo__riga--basse", t("weather.sky.legend.lowFull"), `${valore(o.cloud_low_pct)}%`],
    ["as-cielo__riga--medie", t("weather.sky.legend.midFull"), `${valore(o.cloud_mid_pct)}%`],
    ["as-cielo__riga--alte", t("weather.sky.legend.highFull"), `${valore(o.cloud_high_pct)}%`],
    ["as-cielo__riga--umidita", t("weather.sky.humidity"), `${valore(o.humidity_pct)}%`],
  ]
  if (destra) {
    const l = o.levels[destra]
    const v = o[DISEGNO[destra].campo]
    const detto = v === null ? t("weather.card.unknown") : `${numero(v)}${DISEGNO[destra].unita ? ` ${t(DISEGNO[destra].unita as Chiave)}` : ""}${l ? `, ${parola(destra, l)}` : ""}`
    righe.push([RIGHE[l ?? "sotto"], nomeDestra, detto])
  }
  return (
    <div className="as-volta__lettore" style={sinistra ? { right: `calc(${100 - x}% + 14px)` } : { left: `calc(${x}% + 14px)` }}>
      <div className="as-volta__lettore-ora">{oraDelSito(o.at)}</div>
      {righe.map(([classe, nome, v]) => (
        <div key={nome} className={`as-volta__lettore-riga ${classe}`}>
          <i />
          <span>{nome}</span>
          <b>{v}</b>
        </div>
      ))}
    </div>
  )
}
