import { type PointerEvent, useState } from "react"

import type { components } from "./api/schema"
import { type Chiave, durata, numero, oraDelSito, t } from "./i18n"

type Stanotte = components["schemas"]["TonightOut"]
type Punto = components["schemas"]["SkyPointOut"]
type PuntoDellaLuna = components["schemas"]["MoonPointOut"]
type Fascia = components["schemas"]["SkyBandOut"]
type Ora = components["schemas"]["WeatherHourOut"]
type Pianeta = components["schemas"]["PlanetOut"]["key"]

const TAPPE = {
  day: "as-volta__tappa--giorno",
  civil: "as-volta__tappa--civile",
  nautical: "as-volta__tappa--nautico",
  astronomical: "as-volta__tappa--astro",
  dark: "as-volta__tappa--notte",
} as const

// Le classi di ogni astro scritte per esteso: la guardia del foglio le legge e le confronta.
const VOCE = {
  saturno: { curva: "as-volta__curva--saturno", scritta: "as-volta__scritta--saturno", tratto: "as-tratto__linea--saturno", riga: "as-volta__lettore-riga--saturno" },
  giove: { curva: "as-volta__curva--giove", scritta: "as-volta__scritta--giove", tratto: "as-tratto__linea--giove", riga: "as-volta__lettore-riga--giove" },
  marte: { curva: "as-volta__curva--marte", scritta: "as-volta__scritta--marte", tratto: "as-tratto__linea--marte", riga: "as-volta__lettore-riga--marte" },
  venere: { curva: "as-volta__curva--venere", scritta: "as-volta__scritta--venere", tratto: "as-tratto__linea--venere", riga: "as-volta__lettore-riga--venere" },
  luna: { curva: "as-volta__curva--luna", scritta: "as-volta__scritta--luna", tratto: "as-tratto__linea--luna", riga: "as-volta__lettore-riga--luna" },
} as const
type Astro = keyof typeof VOCE

/** La voce dell'astro nel foglio (`as-volta__curva--saturno`). */
const CLASSE: Record<Pianeta, Astro> = { saturn: "saturno", jupiter: "giove", mars: "marte", venus: "venere" }

// Le tele della tavola v37: il desktop e il telefono. Lo zenit sta in cima, l'orizzonte sopra la terra.
type Tela = { largo: number; alto: number; cima: number; orizzonte: number; ore: number }
const LARGA: Tela = { largo: 1300, alto: 420, cima: 10, orizzonte: 382, ore: 405 }
const STRETTA: Tela = { largo: 360, alto: 190, cima: 10, orizzonte: 160, ore: 180 }

// Il chiarore della Luna: illuminazione per seno dell'altezza (docs/per-claude-code.md della tavola);
// il colore e il massimo sono quelli della tavola.
const LUNA_COLORE = "#9aa4e8"
const LUNA_MASSIMO = 0.4

// Le stelle sono un motivo: sempre le stesse, sparse nella parte alta del cielo.
const STELLE = Array.from({ length: 24 }, (_, i) => ({
  x: ((i * 0.618034) % 1),
  y: ((i * 0.381966 + 0.13) % 1) * 0.8,
  lume: i % 3 === 0,
  grande: i % 7 === 0,
}))

type Tratto = { x: number; y: number }

/**
 * La **volta** (`as-volta`, foglio 60, tavola v37): la notte dal tramonto all'alba coi colori del
 * crepuscolo, la griglia a 30 e 60 gradi, le curve dei pianeti e della Luna, gli istanti del buio e
 * la coltre delle nuvole ora per ora. Senza progetti mostra il sistema solare, senza scelta.
 *
 * Finestra, fasce, altezze e istanti arrivano da `/tonight`; le nuvole dalle ore del meteo. Qui si
 * mettono sulla tela e basta.
 */
export function Volta({ stanotte: s, nubi, coperta, telefono }: {
  stanotte: Stanotte
  /** Le ore del meteo della notte, per la coltre; vuote se il meteo non c'e'. */
  nubi: Ora[]
  /** Nessuna ora di buio sereno: la coltre copre tutto e le curve si spengono. */
  coperta: boolean
  telefono: boolean
}) {
  const [evidenzia, setEvidenzia] = useState<string | null>(null)
  const [lettore, setLettore] = useState<number | null>(null)
  const volta = s.chart
  const luna = s.moon
  if (!volta || !luna) return null
  const tela = telefono ? STRETTA : LARGA
  const { largo, alto, cima, orizzonte } = tela
  const da = Date.parse(volta.starts_at)
  const durata = Date.parse(volta.ends_at) - da
  const x = (iso: string) => ((Date.parse(iso) - da) / durata) * largo
  const y = (gradi: number) => orizzonte - (Math.max(0, gradi) / 90) * (orizzonte - cima)
  const dentro = (iso: string) => x(iso) >= 0 && x(iso) <= largo
  const id = `volta-${s.night}-${telefono ? "t" : "d"}`

  const sorge = luna.rise && dentro(luna.rise) ? luna.rise : null
  const astri = [
    ...s.planets.map((p) => ({ chiave: CLASSE[p.key], nome: t(`dashboard.chart.planet.${p.key}` as Chiave), punti: p.track })),
    { chiave: "luna" as Astro, nome: t("dashboard.chart.moon", { pct: numero(luna.illumination_pct) }), punti: luna.track },
  ]
  const curve = astri.map((a) => ({ ...a, tratti: sopra(a.punti, x, y, largo) }))
  // sul telefono un'ora ogni quattro dalla prima ora piena (tredici su 360 si toccano): ore che
  // seguono il tramonto, non fisse, cosi' il bordo sinistro ha sempre un'ora
  const ore = luna.track.filter((p) => p.at.slice(14, 16) === "00" && dentro(p.at)).filter((_, i) => !telefono || i % 4 === 0)
  const frase = [
    coperta ? t("dashboard.chart.covered") : null,
    volta.dark_from ? t("dashboard.chart.dark", { ora: oraDelSito(volta.dark_from) }) : null,
    sorge ? t("dashboard.chart.moonFrom", { ora: oraDelSito(sorge) }) : null,
  ].filter(Boolean).join(", ")

  const leggi = (ev: PointerEvent<HTMLDivElement>) => {
    const q = ev.currentTarget.getBoundingClientRect()
    setLettore(Math.min(1, Math.max(0, (ev.clientX - q.left) / q.width)))
  }
  const istante = lettore === null ? null : vicino(luna.track, da + lettore * durata)

  return (
    <figure className="as-volta" data-mostra="sistema" data-evidenzia={evidenzia ?? undefined}>
      <div className="as-volta__posto" onPointerMove={leggi} onPointerDown={leggi}
        onPointerLeave={(ev) => { if (ev.pointerType === "mouse") setLettore(null) }}>
        <svg className={coperta ? "as-volta__tela as-volta__tela--coperta" : "as-volta__tela"} viewBox={`0 0 ${largo} ${alto}`}
          preserveAspectRatio="none" role="img" aria-label={frase ? `${t("dashboard.chart.label")}: ${frase}` : t("dashboard.chart.label")}>
          <defs>
            <linearGradient id={`${id}-cielo`} x1="0" x2="1" y1="0" y2="0">
              {tappe(s.sky_bands, x, largo).map((p, i) => <stop key={i} offset={`${p.dove}%`} className={`${TAPPE[p.kind]}`} />)}
            </linearGradient>
            <linearGradient id={`${id}-alone`} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0" className="as-volta__alone-0" />
              <stop offset="1" className="as-volta__alone-1" />
            </linearGradient>
            {/* Su tutta la tela: sotto l'orizzonte il seno e' zero, e una Luna gia' alta al tramonto schiarisce da subito. */}
            <linearGradient id={`${id}-luna`} x1="0" x2="1" y1="0" y2="0">
              {luna.track.filter((p) => dentro(p.at)).map((p) => (
                <stop key={p.at} offset={`${(x(p.at) / largo) * 100}%`} stopColor={LUNA_COLORE}
                  stopOpacity={LUNA_MASSIMO * (luna.illumination_pct / 100) * Math.max(0, Math.sin((p.altitude_deg * Math.PI) / 180))} />
              ))}
            </linearGradient>
            <radialGradient id={`${id}-nube`}>
              <stop offset="0" className="as-volta__coltre-0" />
              <stop offset="1" className="as-volta__coltre-1" />
            </radialGradient>
            <filter id={`${id}-bagliore`} x="-5%" y="-30%" width="110%" height="160%">
              <feGaussianBlur stdDeviation="3" />
            </filter>
          </defs>
          <rect width={largo} height={alto} fill={`url(#${id}-cielo)`} />
          <rect width={largo} height={alto} fill={`url(#${id}-alone)`} />
          <rect width={largo} height={alto} fill={`url(#${id}-luna)`} />
          {STELLE.map((st, i) => (
            <circle key={i} className={st.lume ? "as-volta__stella as-volta__stella--lume" : "as-volta__stella"}
              cx={st.x * largo} cy={cima + st.y * (orizzonte - cima)} r={st.grande ? 1.3 : 0.7} />
          ))}
          <Coltre nubi={nubi} x={x} largo={largo} orizzonte={orizzonte} coperta={coperta} id={id} />
          {[30, 60].map((g) => (
            <g key={g}>
              <line className="as-volta__griglia" x1={0} x2={largo} y1={y(g)} y2={y(g)} />
              <text className="as-volta__gradi" x={6} y={y(g) - 5}>{`${g}\u00b0`}</text>
            </g>
          ))}
          <g className="as-volta__gruppo--sistema">
            {curve.filter((c) => c.chiave !== "luna").map((c) => <Curva key={c.chiave} curva={c} id={id} alone={!coperta} nome={!telefono} />)}
          </g>
          <g>
            {curve.filter((c) => c.chiave === "luna").map((c) => <Curva key={c.chiave} curva={c} id={id} alone={false} nome={!telefono} />)}
          </g>
          <rect className="as-volta__terra" y={orizzonte} width={largo} height={alto - orizzonte} />
          <line className="as-volta__orizzonte" x1={0} x2={largo} y1={orizzonte} y2={orizzonte} />
          {ore.map((o) => (
            <text key={o.at} className="as-volta__ora" x={x(o.at)} y={tela.ore} textAnchor={ancora(x(o.at), largo)}>{oraDelSito(o.at).slice(0, 2)}</text>
          ))}
          {volta.dark_from && dentro(volta.dark_from) && <Istante x={x(volta.dark_from)} tela={tela} />}
          {sorge && <Istante x={x(sorge)} tela={tela} scritta={telefono ? null : t("dashboard.chart.moonAt", { ora: oraDelSito(sorge) })} />}
          {volta.dark_until && dentro(volta.dark_until) && (
            <Istante x={x(volta.dark_until)} tela={tela} scritta={telefono ? null : t("dashboard.chart.darkEnd", { ora: oraDelSito(volta.dark_until) })} />
          )}
        </svg>
        {istante && lettore !== null && (
          <Lettore istante={istante} astri={astri} dove={lettore} />
        )}
      </div>
      {telefono && (
        <div className="as-legenda" aria-label={t("dashboard.chart.legend")}>
          <div className="as-legenda__gruppo as-legenda__gruppo--sistema">
            {curve.filter((c) => c.chiave !== "luna").map((c) => (
              <button key={c.chiave} className="as-legenda__voce" type="button" aria-pressed={evidenzia === c.chiave}
                onClick={() => setEvidenzia(evidenzia === c.chiave ? null : c.chiave)}>
                <Campione chiave={c.chiave} />
                {c.nome}
              </button>
            ))}
          </div>
          <span className="as-legenda__luna"><Campione chiave="luna" />{curve[curve.length - 1]?.nome}</span>
        </div>
      )}
    </figure>
  )
}

/** Le tappe del cielo come stop del gradiente: una all'inizio di ogni fascia, e la fine del buio. */
function tappe(fasce: Fascia[], x: (iso: string) => number, largo: number) {
  const dove = (iso: string) => Math.min(100, Math.max(0, (x(iso) / largo) * 100))
  return fasce.flatMap((f) => [
    { dove: dove(f.starts_at), kind: f.kind },
    ...(f.kind === "dark" ? [{ dove: dove(f.ends_at), kind: f.kind }] : []),
  ])
}

/** I tratti di una curva sopra l'orizzonte, dentro la tela; ai bordi si taglia sull'orizzonte. */
function sopra(punti: Punto[], x: (iso: string) => number, y: (g: number) => number, largo: number): Tratto[][] {
  const tratti: Tratto[][] = []
  let corrente: Tratto[] = []
  punti.forEach((p, i) => {
    const prima = punti[i - 1]
    if (prima && (prima.altitude_deg < 0) !== (p.altitude_deg < 0)) {
      // dove la curva passa l'orizzonte, fra i due campioni
      const f = prima.altitude_deg / (prima.altitude_deg - p.altitude_deg)
      const bordo = { x: x(prima.at) + (x(p.at) - x(prima.at)) * f, y: y(0) }
      if (p.altitude_deg < 0) {
        corrente.push(bordo)
        tratti.push(corrente)
        corrente = []
      } else {
        corrente = [bordo]
      }
    }
    if (p.altitude_deg >= 0) corrente.push({ x: x(p.at), y: y(p.altitude_deg) })
  })
  if (corrente.length) tratti.push(corrente)
  return tratti
    .map((tr) => tr.filter((q) => q.x >= -largo * 0.02 && q.x <= largo * 1.02))
    .filter((tr) => tr.length > 1)
}

function Curva({ curva: c, id, alone, nome }: {
  curva: { chiave: Astro; nome: string; tratti: Tratto[][] }; id: string; alone: boolean; nome: boolean
}) {
  if (c.tratti.length === 0) return null
  const d = c.tratti.map((tr) => `M${tr.map((q) => `${q.x.toFixed(1)},${q.y.toFixed(1)}`).join(" L")}`).join(" ")
  const alto = c.tratti.flat().reduce((a, b) => (b.y < a.y ? b : a))
  return (
    <>
      {alone && <path className={`as-volta__curva ${VOCE[c.chiave].curva} as-volta__curva--alone`} d={d} filter={`url(#${id}-bagliore)`} />}
      <path className={`as-volta__curva ${VOCE[c.chiave].curva}`} d={d} />
      {nome && (
        <text className={`as-volta__scritta ${VOCE[c.chiave].scritta}`} x={Math.min(1260, Math.max(40, alto.x))} y={alto.y - 12} textAnchor="middle">
          {c.nome}
        </text>
      )}
    </>
  )
}

/** La coltre: ogni ora del meteo vela la sua colonna quanto e' coperta; la notte coperta tutta. */
function Coltre({ nubi, x, largo, orizzonte, coperta, id }: {
  nubi: Ora[]; x: (iso: string) => number; largo: number; orizzonte: number; coperta: boolean; id: string
}) {
  const ora = 3600 * 1000
  const colonne = nubi.flatMap((o) => {
    const inizio = x(o.at)
    const fine = x(new Date(Date.parse(o.at) + ora).toISOString())
    if (o.cloud_total_pct === null || fine <= 0 || inizio >= largo) return []
    return [{ at: o.at, inizio, fine, quanto: o.cloud_total_pct / 100 }]
  })
  return (
    <>
      {coperta && <rect className="as-volta__coltre" width={largo} height={orizzonte} />}
      {colonne.map((c, i) => c.quanto > 0 && (
        <ellipse key={c.at} cx={(c.inizio + c.fine) / 2} cy={orizzonte * (0.2 + 0.12 * (i % 4))}
          rx={(c.fine - c.inizio) * 1.9} ry={orizzonte * 0.18} fill={`url(#${id}-nube)`} opacity={c.quanto} />
      ))}
    </>
  )
}

function Istante({ x, tela, scritta = null }: { x: number; tela: Tela; scritta?: string | null }) {
  return (
    <>
      <line className="as-volta__istante" x1={x} x2={x} y1={tela.cima} y2={tela.orizzonte} />
      {scritta && <text className="as-volta__scritta as-volta__scritta--istante" x={x + 6} y={tela.orizzonte - 8}>{scritta}</text>}
    </>
  )
}

function Campione({ chiave }: { chiave: Astro }) {
  return (
    <svg className="as-tratto" viewBox="0 0 28 8" aria-hidden="true">
      <path className={`as-tratto__linea ${VOCE[chiave].tratto}`} d="M1 4 H27" />
    </svg>
  )
}

/** Un'ora sul bordo della tela (la finestra intera, al polo) si appoggia dentro invece di tagliarsi. */
function ancora(x: number, largo: number): "start" | "middle" | "end" {
  return x < 1 ? "start" : x > largo - 1 ? "end" : "middle"
}

/** Il campione della curva piu' vicino a un istante. */
function vicino<P extends Punto>(punti: P[], ms: number): P | null {
  return punti.reduce<P | null>((a, p) => (!a || Math.abs(Date.parse(p.at) - ms) < Math.abs(Date.parse(a.at) - ms) ? p : a), null)
}

/** Sotto il puntatore: l'ora, il buio senza Luna che resta (se ne resta), l'altezza di ogni astro
 *  dal piu' alto; chi e' sotto l'orizzonte in fondo. */
function Lettore({ istante: { at: istante, moonless_dark_left_s: resta }, astri, dove }: {
  istante: PuntoDellaLuna; astri: { chiave: Astro; nome: string; punti: Punto[] }[]; dove: number
}) {
  const righe = astri
    .map((a) => ({ ...a, gradi: a.punti.find((p) => p.at === istante)?.altitude_deg ?? null }))
    .filter((a) => a.gradi !== null)
    .sort((a, b) => (b.gradi ?? 0) - (a.gradi ?? 0))
  return (
    <>
      <div className="as-volta__lettore-filo" style={{ left: `${dove * 100}%` }} />
      <div className="as-volta__lettore" style={dove > 0.5 ? { right: `${(1 - dove) * 100 + 1}%` } : { left: `${dove * 100 + 1}%` }}>
        <span className="as-volta__lettore-ora">{oraDelSito(istante)}</span>
        {resta > 0 && <span className="as-volta__lettore-buio">{t("dashboard.chart.moonlessLeft")} <b>{durata(resta)}</b></span>}
        {righe.map((r) => (
          <span key={r.chiave} className={(r.gradi ?? 0) < 0 ? "as-volta__lettore-riga as-volta__lettore-riga--sotto" : `as-volta__lettore-riga ${VOCE[r.chiave].riga}`}>
            <i />
            <span>{r.nome}</span>
            <b>{(r.gradi ?? 0) < 0 ? t("dashboard.chart.reader.below") : `${numero(Math.round(r.gradi ?? 0))}\u00b0`}</b>
          </span>
        ))}
      </div>
    </>
  )
}
