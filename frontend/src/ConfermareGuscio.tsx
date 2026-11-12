import { type CSSProperties, type ReactNode, createContext, useState } from "react"

import { gesto } from "./componenti/gesto"
import type { CartaScheletro } from "./componenti/Scheletro"
import type { Formato } from "./componenti/Tema"
import { type Chiave, numero, t } from "./i18n"
import { type QualeSezione, SEZIONI } from "./sezioniDaConfermare"

/** Come sta una risposta: senza, in mano da applicare, salvata, salvata e cambiata in mano. */
export type StatoRisposta = "dare" | "ora" | "salvata" | "cambiata"

export function statoDi(salvata: boolean, inMano: boolean): StatoRisposta {
  if (inMano) return salvata ? "cambiata" : "ora"
  return salvata ? "salvata" : "dare"
}

/** Le misure che la tavola passa con `style=`, per formato. */
export interface Misure {
  colonne: string
  stacco: string
  posizione: "sticky" | "static"
  angolo: string
  dentro: string
  grande: string
  chiusa: string
  alto: string
  esitoDentro: string
  piedeSotto: string
  piedeDentro: string
  piedeMargine: string
  piedeLargo: string
  piedeStacco: string
  piedeAlto: string
  piedeAngolo: string
  piedeVelo: string
  piedeFondo: string
  piedeNumero: string
  titolo: string
  titoloDomanda: string
  riga: string
  rigaDentro: string
  domandaDentro: string
  prove: string
  proveStacco: string
  campi: string
}

// [T] Da confermare.dc.html `L` (176-177) e `piede` (283): le misure della tavola v82
export const MISURE: Record<Formato, Misure> = {
  desktop: {
    colonne: "300px minmax(0,1fr)",
    stacco: "16px",
    posizione: "sticky",
    angolo: "28px",
    dentro: "28px",
    grande: "64px",
    chiusa: "16px 16px 16px 28px",
    alto: "40px",
    esitoDentro: "18px 18px 18px 22px",
    piedeSotto: "16px",
    piedeDentro: "14px 14px 14px 24px",
    piedeMargine: "0",
    piedeLargo: "auto",
    piedeStacco: "12px 20px",
    piedeAlto: "0",
    piedeAngolo: "28px",
    piedeVelo: "none",
    piedeFondo: "var(--carta)",
    piedeNumero: "30px",
    titolo: "24px",
    titoloDomanda: "22px",
    riga: "minmax(0,1fr) minmax(0,1.4fr) 200px 104px",
    rigaDentro: "12px 12px 12px 18px",
    domandaDentro: "24px",
    prove: "max-content minmax(0,1fr)",
    proveStacco: "6px 20px",
    campi: "repeat(auto-fit,minmax(220px,1fr))",
  },
  telefono: {
    colonne: "minmax(0,1fr)",
    stacco: "12px",
    posizione: "static",
    angolo: "24px",
    dentro: "20px",
    grande: "48px",
    chiusa: "14px 14px 14px 20px",
    alto: "44px",
    esitoDentro: "16px",
    piedeSotto: "28px",
    piedeDentro: "0 8px 0 18px",
    piedeMargine: "76px",
    piedeLargo: "calc(100% - 76px)",
    piedeStacco: "8px",
    piedeAlto: "64px",
    piedeAngolo: "32px",
    piedeVelo: "blur(18px) saturate(1.6)",
    piedeFondo: "color-mix(in srgb, var(--carta) 90%, transparent)",
    piedeNumero: "26px",
    titolo: "22px",
    titoloDomanda: "20px",
    riga: "minmax(0,1fr) auto",
    rigaDentro: "12px 12px 12px 16px",
    domandaDentro: "18px",
    prove: "minmax(0,1fr)",
    proveStacco: "0",
    campi: "minmax(0,1fr)",
  },
}

/** Il formato della pagina, per le domande e le sezioni: una casa, non un ascoltatore per riga. */
export const FormatoConf = createContext<Formato>("desktop")

// [T] Da confermare.dc.html `SK` (299-300): lo scheletro con le carte della pagina
export const SCHELETRO: Record<Formato, CartaScheletro[]> = {
  desktop: [
    {
      col: "1",
      h: "190px",
      blocchi: [{ h: "64px", w: "120px" }, { h: "14px" }, { h: "14px", w: "70%" }],
    },
    {
      col: "2",
      h: "72px",
      blocchi: [{ riga: [{ h: "22px", w: "240px" }, t("review.loading")], tra: true }],
    },
    {
      col: "1",
      h: "380px",
      blocchi: [
        { h: "14px", w: "80px" },
        { h: "44px", r: "16px" },
        { h: "44px", r: "16px" },
        { h: "44px", r: "16px" },
        { h: "44px", r: "16px" },
      ],
    },
    {
      col: "2",
      h: "420px",
      blocchi: [
        { h: "26px", w: "200px" },
        { h: "56px", r: "18px" },
        { flex: "1", r: "22px" },
      ],
    },
  ],
  telefono: [
    {
      h: "120px",
      blocchi: [
        { riga: [{ h: "48px", w: "90px" }, t("review.loading")], tra: true },
        { h: "14px" },
      ],
    },
    {
      h: "320px",
      blocchi: [
        { h: "14px", w: "120px" },
        { h: "72px", r: "18px" },
        { h: "72px", r: "18px" },
        { h: "72px", r: "18px" },
      ],
    },
  ],
}

/** Lo stato di una parte di una domanda: come una risposta, o ancora da indicare. */
export type StatoParte = StatoRisposta | "indicare"

// [T] Da confermare.dc.html `PL` (178-180): segno e colori di ogni stato, mai il colore da solo
const PILLOLE: Record<StatoParte, { segno: string; fondo: string; testo: string; anello: string }> =
  {
    indicare: { segno: "○", fondo: "transparent", testo: "var(--testo)", anello: "var(--tenue)" }, // glifo-ok: segno della tavola
    dare: { segno: "○", fondo: "transparent", testo: "var(--testo)", anello: "var(--tenue)" }, // glifo-ok: segno della tavola
    ora: {
      segno: "\u25cf",
      fondo: "var(--scelta)",
      testo: "var(--scelta-testo)",
      anello: "transparent",
    }, // glifo-ok: segno della tavola
    salvata: {
      segno: "✓", // glifo-ok: segno della tavola
      fondo: "var(--buono-fondo)",
      testo: "var(--buono-testo)",
      anello: "transparent",
    },
    cambiata: { segno: "◐", fondo: "transparent", testo: "var(--testo)", anello: "var(--accento)" }, // glifo-ok: segno della tavola
  }

const TIPI: Record<StatoRisposta, Chiave> = {
  dare: "review.type.open",
  ora: "review.type.inHand",
  salvata: "review.type.saved",
  cambiata: "review.type.changed",
}

/** Cio' che non si tocca mentre Applica lavora (tavola `fz`). */
export const spenta = (ferma: boolean): CSSProperties => ({
  opacity: ferma ? 0.45 : 1,
  pointerEvents: ferma ? "none" : "auto",
})

// [T] Da confermare.dc.html `PL` (178-180): la parola di ogni stato
const PAROLE: Record<StatoParte, Chiave> = {
  dare: "review.state.open",
  ora: "review.state.inHand",
  salvata: "review.state.saved",
  cambiata: "review.state.changed",
  indicare: "review.gear.toGive",
}

/** La pillola con la parola del suo stato. */
export const PillolaDi = ({ stato }: { stato: StatoParte }) => (
  <Pillola stato={stato}>{t(PAROLE[stato])}</Pillola>
)

export function Pillola({ stato, children }: { stato: StatoParte; children: ReactNode }) {
  const p = PILLOLE[stato]
  return (
    <span
      className="al-conf__riga-7"
      style={{ background: p.fondo, color: p.testo, boxShadow: `inset 0 0 0 1.5px ${p.anello}` }}
    >
      <span aria-hidden="true">{p.segno}</span>
      {children}
    </span>
  )
}

/** Il guscio: a sinistra il conto e l'indice (se ci sono), a destra il resto. */
export function Guscio({
  m,
  sinistra,
  children,
}: {
  m: Misure
  sinistra?: ReactNode
  children: ReactNode
}) {
  return (
    <div className="al-conf__blocco-1">
      <div
        className="al-conf__centro-1"
        style={{ gridTemplateColumns: sinistra ? m.colonne : "minmax(0,1fr)", gap: m.stacco }}
      >
        {sinistra && (
          <div className="al-conf__colonna-1" style={{ position: m.posizione, gap: m.stacco }}>
            {sinistra}
          </div>
        )}
        <div className="al-conf__colonna-6" style={{ gap: m.stacco }}>
          {children}
        </div>
      </div>
    </div>
  )
}

const TACCHE: Record<StatoRisposta, CSSProperties> = {
  dare: { background: "transparent", border: "1.5px solid var(--tenue)" },
  ora: { background: "var(--accento)", border: "0" },
  salvata: { background: "var(--buono-testo)", border: "0" },
  cambiata: { background: "var(--accento)", border: "0" },
}

/** Il conto vivo, una tacca per domanda, e la regola finche' qualcosa aspetta. */
export function CartaDelConto({
  conto,
  tacche,
  regola,
  m,
}: {
  conto: number
  tacche: readonly StatoRisposta[]
  regola: boolean
  m: Misure
}) {
  const conRisposta = tacche.filter((x) => x !== "dare").length
  return (
    <section
      className="al-conf__colonna-2"
      aria-label={t("review.count.label")}
      style={{ borderRadius: m.angolo, padding: m.dentro }}
    >
      <span className="al-conf__riga-1">
        <span className="al-conf__testo-1" style={{ fontSize: m.grande }}>
          {numero(conto)}
        </span>
        <span className="al-conf__testo-2">{t("review.count.word")}</span>
      </span>
      {tacche.length > 0 && (
        <span
          className="al-conf__riga-2"
          role="img"
          aria-label={t("review.ticks", { k: numero(conRisposta), n: numero(tacche.length) })}
        >
          {tacche.map((x, i) => (
            <span key={i} className="al-conf__blocco-2" style={TACCHE[x]} />
          ))}
        </span>
      )}
      {regola && <p className="al-conf__testo-3">{t("review.rule")}</p>}
    </section>
  )
}

export interface VoceIndice {
  sezione: QualeSezione
  aspettano: number
  corrente: boolean
}

/** L'indice delle sezioni: quante aspettano, e la corrente. Spento mentre Applica lavora. */
export function Indice({
  voci,
  ferma,
  m,
  onVai,
}: {
  voci: readonly VoceIndice[]
  ferma: boolean
  m: Misure
  onVai: (s: QualeSezione) => void
}) {
  return (
    <nav
      className="al-conf__colonna-3"
      aria-labelledby="conf-indice"
      aria-disabled={ferma ? "true" : undefined}
      inert={ferma}
      style={{ borderRadius: m.angolo, ...spenta(ferma) }}
    >
      <span className="al-conf__blocco-3" id="conf-indice">
        {t("review.index")}
      </span>
      <ol className="al-conf__colonna-4">
        {voci.map((v) => (
          <li key={v.sezione}>
            <a
              className="al-conf__riga-3"
              href={`#${SEZIONI[v.sezione].ancora}`}
              onClick={gesto(() => onVai(v.sezione))}
              aria-current={v.corrente ? "true" : undefined}
              style={{ background: v.corrente ? "var(--carta-2)" : "transparent" }}
            >
              <span className="al-conf__colonna-5">
                <span className="al-conf__testo-4" style={{ fontWeight: v.corrente ? 600 : 400 }}>
                  {t(SEZIONI[v.sezione].titolo)}
                </span>
                <span className="al-conf__testo-5">
                  {v.aspettano
                    ? t("review.index.open", { n: numero(v.aspettano) })
                    : t("review.index.done")}
                </span>
              </span>
              <span
                className="al-conf__tondo-1"
                aria-hidden="true"
                style={
                  v.aspettano
                    ? {
                        background: "transparent",
                        color: "var(--testo)",
                        border: "1.5px solid var(--tenue)",
                      }
                    : {
                        background: "var(--buono-fondo)",
                        color: "var(--buono-testo)",
                        border: "1.5px solid transparent",
                      }
                }
              >
                {v.aspettano ? numero(v.aspettano) : "✓" /* glifo-ok: segno della tavola */}
              </span>
            </a>
          </li>
        ))}
      </ol>
    </nav>
  )
}

/** Il piede: quante modifiche partono, l'avviso dell'unione, Applica. */
export function Piede({
  inMano,
  unisce,
  ferma,
  formato,
  onApplica,
}: {
  inMano: number
  unisce: boolean
  ferma: boolean
  formato: Formato
  onApplica: () => void
}) {
  const [avvisoAperto, setAvvisoAperto] = useState(false)
  const m = MISURE[formato]
  const tel = formato === "telefono"
  const spento = ferma || inMano === 0
  const testoUnione = tel && unisce && avvisoAperto
  const unione = (
    <>
      <b className="al-conf__testo-15">{t("review.merge.warning")}</b>{" "}
      {t("review.merge.warning.rest")}
    </>
  )
  return (
    <div
      className="al-conf__riga-17"
      role="region"
      aria-label={t("review.inHand.label")}
      style={{
        bottom: m.piedeSotto,
        background: m.piedeFondo,
        borderRadius: m.piedeAngolo,
        padding: m.piedeDentro,
        flexWrap: tel && !testoUnione ? "nowrap" : "wrap",
        marginLeft: m.piedeMargine,
        width: m.piedeLargo,
        gap: m.piedeStacco,
        minHeight: m.piedeAlto,
        boxSizing: "border-box",
        backdropFilter: m.piedeVelo,
        WebkitBackdropFilter: m.piedeVelo,
      }}
    >
      <p className="al-conf__riga-18" aria-live="polite">
        <span className="al-conf__testo-19" style={{ fontSize: m.piedeNumero }}>
          {numero(inMano)}
        </span>
        <span className="al-conf__testo-20">
          {tel ? t("review.state.inHand") : t("review.inHand.word", { n: inMano })}
        </span>
      </p>
      {tel && unisce && (
        <a
          className="al-conf__tondo-3"
          href="#"
          role="button"
          aria-expanded={avvisoAperto ? "true" : "false"}
          aria-label={`${t("review.merge.warning")} ${t("review.merge.show")}`}
          onClick={gesto(() => setAvvisoAperto(!avvisoAperto))}
        >
          <span className="al-conf__tondo-4" aria-hidden="true">
            !
          </span>
        </a>
      )}
      {!tel && unisce && (
        <span className="al-conf__riga-19">
          <span className="al-conf__tondo-5" aria-hidden="true">
            !
          </span>
          <span>{unione}</span>
        </span>
      )}
      <span className="al-conf__blocco-17" />
      <a
        className="al-conf__riga-20"
        href="#"
        role="button"
        aria-disabled={spento ? "true" : undefined}
        aria-busy={ferma ? "true" : undefined}
        onClick={gesto(() => {
          if (!spento) onApplica()
        })}
        style={{
          background: "var(--scelta)",
          color: "var(--scelta-testo)",
          opacity: inMano === 0 && !ferma ? 0.45 : 1,
          cursor: ferma ? "progress" : spento ? "not-allowed" : "pointer",
        }}
      >
        {ferma && <span className="al-conf__tondo-6" aria-hidden="true" />}
        {ferma ? t("review.applying") : t("review.apply")}
      </a>
      {testoUnione && <p className="al-conf__blocco-18">{unione}</p>}
    </div>
  )
}

/** L'esito dell'Applica: fatto (si chiude) o rifiutato col motivo. */
export function Esito({
  segno,
  titolo,
  testo,
  m,
  onChiudi,
}: {
  segno: "✓" | "!" // glifo-ok: segni della tavola
  titolo: string
  testo: string
  m: Misure
  onChiudi?: () => void
}) {
  const tinta =
    segno === "!"
      ? { background: "var(--avviso)", color: "var(--avviso-testo)" }
      : { background: "var(--buono-fondo)", color: "var(--buono-testo)" }
  return (
    // un rifiuto annulla tutte le risposte: si annuncia subito, non quando capita
    <div
      className="al-conf__riga-4"
      role={segno === "!" ? "alert" : "status"}
      style={{ borderRadius: m.angolo, padding: m.esitoDentro }}
    >
      <span className="al-conf__tondo-2" aria-hidden="true" style={tinta}>
        {segno}
      </span>
      <span className="al-conf__colonna-7">
        <b className="al-conf__testo-6">{titolo}</b>
        {testo && <span className="al-conf__testo-7">{testo}</span>}
      </span>
      {onChiudi && (
        <a
          href="#"
          role="button"
          onClick={gesto(onChiudi)}
          className="al-bottone al-bottone--contorno"
        >
          {t("frame.close")}
        </a>
      )}
    </div>
  )
}

/** Una sezione con tutte le risposte, chiusa in una riga: porta l'ancora, l'indice arriva qui. */
export function SezioneChiusa({
  sezione,
  inMano,
  salvate,
  m,
  onRiapri,
}: {
  sezione: QualeSezione
  inMano: number
  salvate: number
  m: Misure
  onRiapri: () => void
}) {
  const nome = t(SEZIONI[sezione].titolo)
  return (
    <div
      className="al-conf__riga-9"
      id={SEZIONI[sezione].ancora}
      style={{ borderRadius: m.angolo, padding: m.chiusa }}
    >
      <h2 className="al-conf__blocco-7">{nome}</h2>
      <Pillola stato={inMano > 0 ? "ora" : "salvata"}>
        {inMano > 0
          ? t("review.closed.inHand", { n: numero(inMano) })
          : t("review.closed.saved", { n: numero(salvate) })}
      </Pillola>
      <a
        className="al-conf__riga-10"
        href="#"
        role="button"
        aria-label={`${t("review.reopen")}: ${nome}`}
        onClick={gesto(onRiapri)}
        style={{
          minHeight: m.alto,
          background: "transparent",
          color: "var(--testo)",
          boxShadow: "inset 0 0 0 1.5px var(--linea)",
        }}
      >
        {t("review.reopen")}
      </a>
    </div>
  )
}

export interface VoceTipo {
  sezione: QualeSezione
  stati: readonly { stato: StatoRisposta; n: number }[]
}

/** Il telefono, prima di un caso: i tipi di domanda coi loro stati. */
export function TipiDiDomanda({
  voci,
  ferma,
  m,
  onTipo,
}: {
  voci: readonly VoceTipo[]
  ferma: boolean
  m: Misure
  onTipo: (s: QualeSezione) => void
}) {
  return (
    <section
      className="al-conf__colonna-8"
      aria-labelledby="conf-tipi"
      aria-disabled={ferma ? "true" : undefined}
      inert={ferma}
      style={{ borderRadius: m.angolo, ...spenta(ferma) }}
    >
      <span className="al-conf__blocco-4" id="conf-tipi">
        {t("review.types")}
      </span>
      <ul className="al-conf__colonna-9">
        {voci.map((v) => (
          <li key={v.sezione}>
            <a className="al-conf__colonna-10" href="#" onClick={gesto(() => onTipo(v.sezione))}>
              <span className="al-conf__riga-5">
                <span className="al-conf__blocco-5">{t(SEZIONI[v.sezione].titolo)}</span>
                <span aria-hidden="true" style={FRECCIA}>
                  {"↗" /* glifo-ok: segno della tavola */}
                </span>
              </span>
              <span className="al-conf__riga-6">
                {v.stati.map((x) => (
                  <Pillola key={x.stato} stato={x.stato}>
                    {t(TIPI[x.stato], { n: numero(x.n) })}
                  </Pillola>
                ))}
              </span>
            </a>
          </li>
        ))}
      </ul>
    </section>
  )
}

// [T] Da confermare.dc.html:39 il tondo della freccia, scritto in linea dalla tavola
const FRECCIA: CSSProperties = {
  flex: "none",
  width: "32px",
  height: "32px",
  borderRadius: "50%",
  display: "grid",
  placeItems: "center",
  background: "var(--carta-2)",
  color: "var(--testo)",
  fontSize: "14px",
}

/** Caso prima e Caso dopo, sempre tutti e due: ai bordi spenti. */
export function CasoAccanto({ k, n, onVai }: { k: number; n: number; onVai: (j: number) => void }) {
  const gestoVerso = (j: number, chiave: Chiave) => {
    const fuori = j < 0 || j >= n
    return (
      <a
        href="#"
        role="button"
        aria-disabled={fuori ? "true" : undefined}
        onClick={gesto(() => {
          if (!fuori) onVai(j)
        })}
        className="al-bottone al-bottone--tenue al-bottone--rovescio al-bottone--blocco"
        style={{ opacity: fuori ? 0.4 : 1 }}
      >
        {t(chiave)}
      </a>
    )
  }
  return (
    <div className="al-conf__griglia-1">
      {gestoVerso(k - 1, "review.phone.before")}
      {gestoVerso(k + 1, "review.phone.after")}
    </div>
  )
}
