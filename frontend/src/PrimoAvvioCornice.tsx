import type { CSSProperties, ReactNode } from "react"
import { useId } from "react"

import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Scheletro } from "./componenti/Scheletro"
import { type Formato, Tema } from "./componenti/Tema"
import { numero, t } from "./i18n"

/** The board's `L`, per format: what `Primo avvio` passes with `style=`. */
interface Misure {
  largo: string
  dentro: string
  colonne: string
  stacco: string
  posizione: "sticky" | "static"
  staccoLato: string
  titolo: string
  angolo: string
  dentroCarta: string
  titoloPasso: string
  conti: string
  chiusura: string
  valore: string
}

// [T] Primo avvio.dc.html `L` (282-283): the measures of tavola v82
export const MISURE: Record<Formato, Misure> = {
  desktop: {
    largo: "1160px",
    dentro: "64px 40px 80px",
    colonne: "300px minmax(0,1fr)",
    stacco: "56px",
    posizione: "sticky",
    staccoLato: "28px",
    titolo: "34px",
    angolo: "28px",
    dentroCarta: "32px",
    titoloPasso: "28px",
    conti: "repeat(4,minmax(0,1fr))",
    chiusura: "26px 200px minmax(0,1fr)",
    valore: "auto",
  },
  telefono: {
    largo: "none",
    dentro: "20px 16px 28px",
    colonne: "minmax(0,1fr)",
    stacco: "18px",
    posizione: "static",
    staccoLato: "16px",
    titolo: "24px",
    angolo: "24px",
    dentroCarta: "20px",
    titoloPasso: "24px",
    conti: "repeat(2,minmax(0,1fr))",
    chiusura: "26px minmax(0,1fr)",
    valore: "2",
  },
}

/** How a step stands: given, skipped, the one on screen, still to come. */
export type Tappa = "fatto" | "saltato" | "ora" | "dopo"

/** A round sign of the board (`sg`): word or number inside, and never the colour alone. */
export function segno(m: Tappa, n: number): { testo: string; stile: CSSProperties } {
  if (m === "fatto")
    return {
      testo: "✓", // glifo-ok: segno della tavola
      stile: {
        background: "var(--buono-fondo)",
        color: "var(--buono-testo)",
        border: "1.5px solid transparent",
      },
    }
  if (m === "saltato")
    return {
      testo: "–", // glifo-ok: segno della tavola
      stile: {
        background: "transparent",
        color: "var(--tenue)",
        border: "1.5px dashed var(--tenue)",
      },
    }
  if (m === "ora")
    return {
      testo: String(n),
      stile: {
        background: "var(--accento)",
        color: "var(--scelta-testo)",
        border: "1.5px solid transparent",
      },
    }
  return {
    testo: String(n),
    stile: { background: "transparent", color: "var(--tenue)", border: "1.5px solid var(--linea)" },
  }
}

const VERSO = {
  pieno: "al-bottone--pieno",
  tenue: "al-bottone--tenue",
  rovescio: "al-bottone--tenue al-bottone--rovescio",
  contorno: "al-bottone--contorno",
} as const

/** A command of the board (`B`): a `<a role="button">`, its spinner and word while it works. */
export function Comando({
  testo,
  verso,
  spento = false,
  occupato,
  onClick,
}: {
  testo: string
  verso: keyof typeof VERSO
  spento?: boolean
  /** The word while it works ("Ripristino..."); set, the command is busy. */
  occupato?: string | undefined
  onClick: () => void
}) {
  return (
    <a
      href="#"
      role="button"
      aria-disabled={spento ? "true" : undefined}
      aria-busy={occupato ? "true" : undefined}
      onClick={gesto(() => {
        if (!spento && !occupato) onClick()
      })}
      className={`al-bottone ${VERSO[verso]} al-avvio__blocco-4`}
    >
      {occupato && <span className="al-avvio__tondo-3" aria-hidden="true" />}
      {occupato ?? testo}
    </a>
  )
}

/** One step in the side list: its name, how it stands, and its number. */
export interface Passo {
  nome: string
  tappa: Tappa
}

const PAROLA: Record<
  Tappa,
  "wizard.mark.done" | "wizard.mark.skipped" | "wizard.mark.here" | "wizard.mark.later"
> = {
  fatto: "wizard.mark.done",
  saltato: "wizard.mark.skipped",
  ora: "wizard.mark.here",
  dopo: "wizard.mark.later",
}

function Tappe({ passi, formato }: { passi: readonly Passo[]; formato: Formato }) {
  const corrente = passi.findIndex((p) => p.tappa === "ora")
  const quanti =
    corrente >= 0 ? t("wizard.passo", { n: numero(corrente + 1), tot: numero(passi.length) }) : ""
  const etichetta = (p: Passo) => `${p.nome}, ${t(PAROLA[p.tappa])}`
  if (formato === "telefono")
    return (
      <div className="al-avvio__colonna-7">
        <ol className="al-avvio__riga-2" aria-label={t("wizard.steps")}>
          {passi.map((p, j) => {
            const s = segno(p.tappa, j + 1)
            return (
              <li
                key={p.nome}
                className="al-avvio__riga-3"
                aria-current={p.tappa === "ora" ? "step" : undefined}
                aria-label={etichetta(p)}
                style={{ flex: j ? "1" : "none" }}
              >
                {j > 0 && <span className="al-avvio__riquadro-1" aria-hidden="true" />}
                <span className="al-avvio__tondo-2" aria-hidden="true" style={s.stile}>
                  {s.testo}
                </span>
              </li>
            )
          })}
        </ol>
        {quanti && (
          <span className="al-avvio__testo-5">
            <b className="al-avvio__testo-6">{quanti}</b>
            <span className="al-avvio__testo-7">
              {` · ${passi[corrente]!.nome}` /* glifo-ok: punto della tavola */}
            </span>
          </span>
        )}
      </div>
    )
  return (
    <div className="al-avvio__colonna-4">
      {quanti && <span className="al-avvio__blocco-2">{quanti}</span>}
      <ol className="al-avvio__colonna-5" aria-label={t("wizard.steps")}>
        {passi.map((p, j) => {
          const s = segno(p.tappa, j + 1)
          const ora = p.tappa === "ora"
          return (
            <li
              key={p.nome}
              className="al-avvio__riga-1"
              aria-current={ora ? "step" : undefined}
              aria-label={etichetta(p)}
              style={{ background: ora ? "var(--carta)" : "transparent" }}
            >
              <span className="al-avvio__tondo-1" aria-hidden="true" style={s.stile}>
                {s.testo}
              </span>
              <span className="al-avvio__colonna-6">
                <span
                  className="al-avvio__testo-3"
                  style={{
                    fontWeight: ora ? 600 : 400,
                    color: p.tappa === "dopo" ? "var(--tenue)" : "var(--testo)",
                  }}
                >
                  {p.nome}
                </span>
                {(p.tappa === "fatto" || p.tappa === "saltato") && (
                  <span className="al-avvio__testo-4">{t(PAROLA[p.tappa])}</span>
                )}
              </span>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

/** The page of the first run: dark sheet of the saved theme, no frame around it. */
function Fondo({ children }: { children: ReactNode }) {
  return (
    <Tema>
      <div className="al-avvio__blocco-1">
        <div className="al-avvio__colonna-1" data-screen-label={t("wizard.title")}>
          {children}
        </div>
      </div>
    </Tema>
  )
}

/** Settings still unread (`appCar`): the board's skeleton, inside the first run's page. */
export function AvvioInAttesa() {
  const formato = useFormato()
  const m = MISURE[formato]
  return (
    <Fondo>
      <div
        style={{
          maxWidth: m.largo,
          width: "100%",
          margin: "0 auto",
          padding: m.dentro,
          boxSizing: "border-box",
        }}
      >
        <Scheletro
          formato={formato}
          testo={t("wizard.loading")}
          // [T] Primo avvio.dc.html `appSk` (186)
          carte={[
            { h: "120px", blocchi: [{ h: "32px", w: "50%" }, t("wizard.loading")] },
            { h: "280px", blocchi: [{ h: "28px", w: "40%" }, { flex: "1" }] },
          ]}
        />
      </div>
    </Fondo>
  )
}

/** Settings that do not answer (`appErr`): nothing is guessed, and the retry is there. */
export function AvvioNonRisponde({ onRiprova }: { onRiprova: () => void }) {
  return (
    <AvvisoDiAvvio
      titolo={t("wizard.unreachable")}
      testo={t("wizard.unreachable.text")}
      azione={t("wizard.retry")}
      onAzione={onRiprova}
    />
  )
}

/** A page notice in the first start's frame (`appErr`): its margins, not the edges of the window. */
export function AvvisoDiAvvio({
  titolo,
  testo,
  azione,
  onAzione,
}: {
  titolo: string
  testo: string
  azione: string
  onAzione: () => void
}) {
  const formato = useFormato()
  const m = MISURE[formato]
  return (
    <Fondo>
      <div
        style={{
          maxWidth: m.largo,
          width: "100%",
          margin: "0 auto",
          padding: m.dentro,
          boxSizing: "border-box",
        }}
      >
        <Avviso
          tipo="pagina"
          formato={formato}
          segno="!"
          titolo={titolo}
          testo={testo}
          azione={azione}
          onAzione={onAzione}
        />
      </div>
    </Fondo>
  )
}

/**
 * The first run's frame (tavola v82 `Primo avvio`): title and steps on the side, the step in a
 * card with its name and reason, the gestures at the card's foot or, on the phone, in a bar.
 */
export function CorniceAvvio({
  passi,
  titolo,
  pastiglia,
  perche,
  gesti,
  children,
}: {
  /** The side list; none for the backup's question, which comes before the steps. */
  passi?: readonly Passo[]
  titolo: string
  pastiglia?: { testo: string; buono: boolean } | undefined
  perche?: string | undefined
  gesti?: ReactNode
  children: ReactNode
}) {
  const formato = useFormato()
  const tel = formato === "telefono"
  const m = MISURE[formato]
  const idTitolo = useId()
  return (
    <Fondo>
      <main
        className="al-avvio__centro-1"
        data-formato={formato}
        style={{
          maxWidth: m.largo,
          padding: m.dentro,
          gridTemplateColumns: m.colonne,
          gap: m.stacco,
        }}
      >
        <div className="al-avvio__colonna-2" style={{ position: m.posizione, gap: m.staccoLato }}>
          <div className="al-avvio__colonna-3">
            <h1 className="al-avvio__testo-1" style={{ fontSize: m.titolo }}>
              {t("wizard.title")}
            </h1>
            <p className="al-avvio__testo-2">{t("wizard.reassure")}</p>
          </div>
          {passi && <Tappe passi={passi} formato={formato} />}
        </div>

        <section
          className="al-avvio__colonna-8"
          aria-labelledby={idTitolo}
          style={{ borderRadius: m.angolo, padding: m.dentroCarta }}
        >
          <header className="al-avvio__colonna-4">
            <h2 className="al-avvio__riga-4" id={idTitolo} style={{ fontSize: m.titoloPasso }}>
              <span>{titolo}</span>
              {pastiglia && (
                <span
                  className="al-avvio__pillola-1"
                  style={
                    pastiglia.buono
                      ? { background: "var(--buono-fondo)", color: "var(--buono-testo)" }
                      : { background: "var(--incerto-fondo)", color: "var(--incerto-testo)" }
                  }
                >
                  {pastiglia.testo}
                </span>
              )}
            </h2>
            {perche && <p className="al-avvio__blocco-3">{perche}</p>}
          </header>
          {children}
          {gesti && !tel && <div className="al-avvio__riga-16">{gesti}</div>}
        </section>
      </main>
      {gesti && tel && <div className="al-avvio__riga-18">{gesti}</div>}
    </Fondo>
  )
}

/** A field of the board (`F`): label, input, the reason under it once there is one. */
export function CampoAvvio({
  id,
  etichetta,
  valore,
  onScrivi,
  onLascia,
  segnaposto = "",
  errore,
  dopo,
  aiuto,
}: {
  id: string
  etichetta: string
  valore: string
  onScrivi: (v: string) => void
  onLascia?: () => void
  segnaposto?: string
  errore?: string | undefined
  /** The command on the same row (Cerca, Verifica). */
  dopo?: ReactNode
  aiuto?: string | undefined
}) {
  return (
    <div className="al-avvio__colonna-10">
      <label className="al-avvio__testo-11" htmlFor={id}>
        {etichetta}
      </label>
      <div className="al-avvio__riga-6">
        <input
          id={id}
          className="al-campo al-avvio__blocco-6"
          value={valore}
          onChange={(e) => onScrivi(e.target.value)}
          onBlur={onLascia}
          placeholder={segnaposto}
          aria-invalid={errore ? "true" : "false"}
          aria-describedby={`${id}-e`}
          autoComplete="off"
          spellCheck={false}
        />
        {dopo}
      </div>
      {errore && (
        <span className="al-avvio__riga-7" id={`${id}-e`} style={{ color: "var(--male)" }}>
          <b aria-hidden="true">!</b>
          {errore}
        </span>
      )}
      {aiuto !== undefined && <span className="al-avvio__testo-12">{aiuto}</span>}
    </div>
  )
}
