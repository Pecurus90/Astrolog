import { useQuery } from "@tanstack/react-query"
import type { CSSProperties, ReactNode } from "react"
import { Link } from "react-router"

import { api } from "./api/client"
import type { components } from "./api/schema"
import { Avviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import type { Formato } from "./componenti/Tema"
import { nomeDelFiltro } from "./FiltriUsati"
import { mesiBrevi, mesiIniziali, numero, oreEMinuti, t, unDecimale } from "./i18n"
import { pallinoDi } from "./MisureDati"

type Anno = components["schemas"]["YearOut"]
type Mese = Anno["months"][number]
type Filtro = Anno["filters"][number]
type Riga = Anno["rows"][number]

// board `hatch(t.sparkOff)`: the months still to come
const TRATTEGGIO =
  "repeating-linear-gradient(135deg, var(--barretta-spenta) 0 3px, transparent 3px 8px)"
// the paused grow-in of the sheet starts with the card
const VIA: CSSProperties = { animationPlayState: "running" }
// board inline style of the phone's "Nessuna posa"
const VUOTO_TELEFONO: CSSProperties = { borderTop: "1px solid var(--linea)", paddingTop: 14 }

function useAnno() {
  return useQuery({
    queryKey: ["year"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/year")
      if (error) throw new Error("year")
      return data
    },
  })
}

/** Ore come le scrive la tavola: "128 h 40", e zero e' "0 h", non "< 6 min". */
function ore(s: number): string {
  return s === 0 ? t("dashboard.year.zero") : oreEMinuti(s)
}

/** La differenza col segno della tavola, meno tipografico o piu': "+4 h". */
function scarto(s: number): string {
  if (s === 0) return t("dashboard.year.zero")
  return `${s < 0 ? "\u2212" : "+"}${oreEMinuti(Math.abs(s))}`
}

/** L'altezza di una barra fra il 14 e l'86% della colonna; un mese senza ore non ha barra
 *  (tavola v80, stato J "zeri"). */
function altezza(s: number, quota: number): string {
  return s === 0 ? "0%" : `${14 + quota * 72}%`
}

/** Una barra del mese (tavola `months`): altezza dall'API. */
function barra(m: Mese) {
  return {
    h: m.future ? "40%" : altezza(m.integration_s, m.bar),
    gh: altezza(m.previous_s, m.previous_bar),
    bg: m.future ? TRATTEGGIO : m.current ? "var(--giorno-su)" : "var(--barra-mese)",
    ring: m.future ? "var(--barretta-spenta)" : "transparent",
  }
}

// a gradient is not a colour inside conic-gradient: the colour stripes become three slices
const A_COLORI = ["var(--filtro-r)", "var(--filtro-g)", "var(--filtro-b)"]

/** I colori del pezzo d'anello: senza filtro un grigio (nel pallino e' un filo), a colori R, G, B. */
function tinte(banda: string): string[] {
  const p = pallinoDi(banda)
  if (p.border) return ["var(--ignoto-tratteggio)"]
  return p.background === "var(--filtro-a-colori)" ? A_COLORI : [p.background]
}

/** Il pallino di una riga; "altri N filtri" e' una torta del primo colore di ognuno (tavola v81). */
function pallinoDellaRiga(r: Riga): CSSProperties {
  if (r.kind !== "others") return pallinoDi(r.passbands[0] ?? "UNKNOWN")
  const n = r.passbands.length
  const fette = r.passbands.map((b, i) => `${tinte(b)[0]} ${(i / n) * 100}% ${((i + 1) / n) * 100}%`)
  return { background: `conic-gradient(${fette.join(", ")})`, border: 0 }
}

function nomeDellaRiga(r: Riga): string {
  return r.kind === "others"
    ? t("dashboard.year.filters.others", { n: numero(r.count) })
    : nomeDelFiltro(r.name)
}

/** L'anello dei filtri (tavola `filterRing`): i pezzi dall'API, separati da un filo di carta. */
function anello(filtri: Filtro[]): string {
  const pezzi = filtri.map((f) => {
    const fine = Math.max(f.ring_from, f.ring_to - 0.6)
    const colori = tinte(f.passband)
    const passo = (fine - f.ring_from) / colori.length
    const fette = colori.map((c, i) => {
      const da = f.ring_from + i * passo
      return `${c} ${da}% ${i === colori.length - 1 ? fine : da + passo}%`
    })
    return `${fette.join(", ")}, var(--carta) ${fine}% ${f.ring_to}%`
  })
  return `conic-gradient(${pezzi.join(", ")})`
}

function Statistiche() {
  return (
    <Link
      className="al-dash__tondo-3"
      to="/statistiche"
      aria-label={t("dashboard.year.open")}
      title={t("nav.stats")}
    >
      {"\u2197"}
    </Link>
  )
}

function Mesi({ anno, telefono }: { anno: Anno; telefono: boolean }) {
  const nomi = mesiBrevi()
  const iniziali = mesiIniziali()
  const detto = t(anno.previous_known ? "dashboard.year.bars" : "dashboard.year.bars.alone", {
    anno: String(anno.year),
  })
  return (
    <>
      <div
        className={telefono ? "al-dash__griglia-19" : "al-dash__griglia-13"}
        role="img"
        aria-label={detto}
      >
        {anno.months.map((m) => {
          const b = barra(m)
          const pezzi = (
            <>
              <span
                className="al-dash__pillola-9"
                data-anim="1"
                style={{ ...VIA, height: b.h, background: b.bg, boxShadow: `inset 0 0 0 1px ${b.ring}` }}
              />
              {anno.previous_known && (
                <span
                  className={telefono ? "al-dash__strato-3" : "al-dash__strato-2"}
                  style={{ height: b.gh }}
                />
              )}
            </>
          )
          return telefono ? (
            <div key={m.month} className="al-dash__riga-45">
              {pezzi}
            </div>
          ) : (
            <div key={m.month} className="al-dash__colonna-16">
              {m.current && anno.integration_s > 0 && <span className="al-dash__strato-1">{ore(m.integration_s)}</span>}
              {pezzi}
            </div>
          )
        })}
      </div>
      {telefono ? (
        <div className="al-dash__griglia-20" aria-hidden="true">
          {nomi.map((n) => (
            <span key={n}>{n}</span>
          ))}
        </div>
      ) : (
        <div className="al-dash__griglia-10" aria-hidden="true">
          {nomi.map((n, i) => (
            <span key={n}>
              <span className="al-dash__mese-lungo">{n}</span>
              <span className="al-dash__mese-corto">{iniziali[i]}</span>
            </span>
          ))}
        </div>
      )}
    </>
  )
}

function Anello({ anno, telefono }: { anno: Anno; telefono: boolean }) {
  const primo = anno.filters[0]
  if (!primo) return null
  return (
    <span
      className={telefono ? "al-dash__tondo-15" : "al-dash__tondo-10"}
      data-anim="1"
      style={{ ...VIA, background: anello(anno.filters) }}
    >
      <span className={telefono ? "al-dash__tondo-16" : "al-dash__tondo-11"}>
        <span className={telefono ? "al-dash__testo-41" : "al-dash__testo-26"}>
          {`${numero(primo.share_pct)}%`}
        </span>
        <span className={telefono ? "al-dash__testo-17" : "al-dash__testo-13"}>
          {t("dashboard.year.filters.in", { filtro: nomeDelFiltro(primo.name) })}
        </span>
      </span>
    </span>
  )
}

function Desktop({ anno }: { anno: Anno }) {
  const a = String(anno.year)
  const prima = String(anno.year - 1)
  const media = anno.per_night_s === null ? "\u2014" : ore(anno.per_night_s)
  return (
    <>
      <Carta
        colonne={8}
        etichetta={t("dashboard.year.title", { anno: a })}
        ritardo={360}
        padding="24px 28px"
        griglia="260px minmax(0,1fr)"
        gap="32"
      >
        <div className="al-dash__colonna-15">
          <span className="al-dash__testo-1">{t("dashboard.year.title", { anno: a })}</span>
          <span className="al-dash__colonna-12">
            <span className="al-dash__testo-22">{ore(anno.integration_s)}</span>
            <span className="al-dash__testo-18">
              {t("dashboard.year.inNights", { n: numero(anno.nights) })}
            </span>
          </span>
          <div className="al-dash__griglia-12">
            <span className="al-dash__riquadro-1">
              <b className="al-dash__testo-23">{media}</b>
              <br />
              <span className="al-dash__testo-13">{t("dashboard.year.perNight")}</span>
            </span>
            <span className="al-dash__riquadro-1">
              <b className="al-dash__testo-23">{unDecimale(anno.per_month)}</b>
              <br />
              <span className="al-dash__testo-13">{t("dashboard.year.perMonth")}</span>
            </span>
          </div>
          <Statistiche />
        </div>
        <div className="al-dash__colonna-3">
          <Mesi anno={anno} telefono={false} />
          {anno.previous_known && (
            <div className="al-dash__riga-27">
              <span className="al-dash__riga-28">
                <i className="al-dash__pillola-10" />
                {a}
              </span>
              <span className="al-dash__riga-28">
                <i className="al-dash__pillola-11" />
                {prima}
              </span>
              <span className="al-dash__testo-24">
                {t("dashboard.year.vs", {
                  ore: ore(anno.integration_s),
                  prima: ore(anno.previous_same_period_s),
                  anno: prima,
                })}
                {" \u00b7 "}
                <b className="al-dash__testo-25">{scarto(anno.vs_previous_s)}</b>
              </span>
            </div>
          )}
        </div>
      </Carta>
      <Carta
        colonne={4}
        etichetta={t("dashboard.year.filters.title", { anno: a })}
        ritardo={420}
        padding="24px"
        gap="16"
        giustifica="space-between"
      >
        <span className="al-dash__testo-1">{t("dashboard.year.filters.title", { anno: a })}</span>
        {anno.filters.length > 0 ? (
          <>
            <div className="al-dash__griglia-14">
              <Anello anno={anno} telefono={false} />
              <div className="al-dash__colonna-3">
                {anno.rows.map((r) => (
                  <span key={`${r.kind}${r.name}`} className="al-dash__griglia-15">
                    <i className="al-dash__tondo-12" style={pallinoDellaRiga(r)} />
                    <span>
                      <b className="al-dash__testo-7">{nomeDellaRiga(r)}</b>{" "}
                      <span className="al-dash__testo-27">{ore(r.integration_s)}</span>
                    </span>
                    <b className="al-dash__testo-28">{`${numero(r.share_pct)}%`}</b>
                  </span>
                ))}
              </div>
            </div>
            <span className="al-dash__testo-13">
              {t("dashboard.year.filters.caption", { ore: ore(anno.integration_s) })}
            </span>
          </>
        ) : (
          <span className="al-dash__testo-18">{t("dashboard.year.none", { anno: a })}</span>
        )}
      </Carta>
    </>
  )
}

function Telefono({ anno }: { anno: Anno }) {
  const a = String(anno.year)
  const sotto = [
    t("dashboard.year.tel.nights", { n: numero(anno.nights) }),
    anno.per_night_s === null
      ? t("dashboard.year.tel.noAverage")
      : t("dashboard.year.tel.perNight", { ore: ore(anno.per_night_s) }),
    t("dashboard.year.tel.perMonth", { n: unDecimale(anno.per_month) }),
  ].join(" \u00b7 ")
  return (
    <CartaTelefono anno={a} sotto={sotto}>
      <span className="al-dash__testo-43">{ore(anno.integration_s)}</span>
      <Mesi anno={anno} telefono />
      {anno.previous_known && (
        <span className="al-dash__testo-13">
          {t("dashboard.year.tel.vs", {
            anno: String(anno.year - 1),
            scarto: scarto(anno.vs_previous_s),
          })}
        </span>
      )}
      {anno.filters.length > 0 ? (
        <div className="al-dash__griglia-21">
          <Anello anno={anno} telefono />
          <div className="al-dash__colonna-30">
            {anno.rows.map((r) => (
              <span key={`${r.kind}${r.name}`} className="al-dash__griglia-22">
                <i className="al-dash__tondo-17" style={pallinoDellaRiga(r)} />
                <b className="al-dash__testo-7">{nomeDellaRiga(r)}</b>
                <span>{`${numero(r.share_pct)}%`}</span>
              </span>
            ))}
          </div>
        </div>
      ) : (
        <span className="al-dash__testo-18" style={VUOTO_TELEFONO}>
          {t("dashboard.year.none", { anno: a })}
        </span>
      )}
    </CartaTelefono>
  )
}

/** La carta "Il 2026" del telefono: titolo, riga sotto se c'e', e Statistiche (tavola 249-250). */
function CartaTelefono({
  anno,
  sotto,
  children,
}: {
  anno: string
  sotto?: string
  children: ReactNode
}) {
  return (
    <Carta
      formato="telefono"
      etichetta={t("dashboard.year.short", { anno })}
      ritardo={360}
      padding="20px"
      gap="14"
    >
      <div className="al-dash__riga-25" style={{ alignItems: "center" }}>
        <span style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0 }}>
          <span className="al-dash__testo-29">{t("dashboard.year.short", { anno })}</span>
          {sotto && <span className="al-dash__testo-13">{sotto}</span>}
        </span>
        <Statistiche />
      </div>
      {children}
    </Carta>
  )
}

/**
 * L'anno della Dashboard (tavola v79): "Il 2026, fino a oggi", una barra per mese col 2025
 * tratteggiato, e "Filtri del 2026" con l'anello; sul telefono in una carta sola. Tutto dall'API.
 */
export function AnnoDellaDashboard({ formato, anno }: { formato: Formato; anno: string }) {
  const lettura = useAnno()
  if (lettura.isPending) return null
  if (!lettura.data) {
    return <AnnoCheNonRisponde formato={formato} anno={anno} riprova={() => lettura.refetch()} />
  }
  return formato === "telefono" ? <Telefono anno={lettura.data} /> : <Desktop anno={lettura.data} />
}

/** Tavola v80, stato K e R: l'anno non arriva, l'avviso sta nella sua carta e il resto c'e'. */
function AnnoCheNonRisponde({
  formato,
  anno,
  riprova,
}: {
  formato: Formato
  anno: string
  riprova: () => void
}) {
  const avviso = (
    <Avviso
      tipo="riga"
      formato={formato}
      segno="!"
      titolo={t("dashboard.year.failed", { anno })}
      azione={t("dashboard.retry")}
      onAzione={riprova}
    />
  )
  if (formato !== "telefono") {
    return (
      <Carta
        colonne={12}
        etichetta={t("dashboard.year.title", { anno })}
        ritardo={360}
        padding="24px 28px"
        gap="14"
      >
        <span className="al-dash__testo-1">{t("dashboard.year.title", { anno })}</span>
        {avviso}
      </Carta>
    )
  }
  return <CartaTelefono anno={anno}>{avviso}</CartaTelefono>
}
