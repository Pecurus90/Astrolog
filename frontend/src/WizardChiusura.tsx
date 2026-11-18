import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { NOMI_ACCENTO, NOMI_MODO } from "./componenti/SceltaTema"
import type { Scelta } from "./componenti/Tema"
import { Comando, CorniceAvvio, MISURE, type Passo, segno } from "./PrimoAvvioCornice"
import { numero, t } from "./i18n"

/** What the closing tells, read from the database once the stamp is written. */
export interface Chiuso {
  nome: string | null
  scelta: Scelta
  chiave: boolean
  /** `null`: no site; `undefined`: the read failed, and the row stays silent. */
  sito: { nome: string; bortle: number | null } | null | undefined
  /** `null`: how many is unknown, and the row stays silent. */
  cartelle: number | null
  letta: boolean
}

const PUNTO = " · " // glifo-ok: punto della tavola

interface Riga {
  voce: string
  valore: string
  dato: boolean
  attenzione?: boolean
}

const AVVISO = {
  background: "var(--avviso)",
  color: "var(--avviso-testo)",
  border: "1.5px solid transparent",
}

/** "Primo avvio completato" (tavola v82 `chiusura`): only what is true, given or not given. */
export function ChiusuraAvvio({
  chiuso,
  passi,
  onApri,
}: {
  chiuso: Chiuso
  passi: readonly Passo[]
  onApri: () => void
}) {
  const formato = useFormato()
  const m = MISURE[formato]
  const { sito, cartelle } = chiuso
  const righe: Riga[] = [
    {
      voce: t("wizard.step.name"),
      valore: chiuso.nome || t("wizard.closed.noName"),
      dato: Boolean(chiuso.nome),
    },
    ...(sito === undefined
      ? []
      : [
          {
            voce: t("wizard.step.site"),
            valore: sito
              ? [sito.nome, sito.bortle && t("site.bortle", { n: sito.bortle })]
                  .filter(Boolean)
                  .join(PUNTO)
              : t("wizard.closed.noSite"),
            dato: Boolean(sito),
          },
        ]),
    {
      voce: t("wizard.step.theme"),
      valore: `${t(NOMI_MODO[chiuso.scelta.modo])}${PUNTO}${t(NOMI_ACCENTO[chiuso.scelta.accento])}`,
      dato: true,
    },
    ...(cartelle === null
      ? []
      : [
          {
            voce: t("wizard.closed.folders"),
            valore: !cartelle
              ? t("wizard.closed.noFolders")
              : [numero(cartelle), chiuso.letta && t("wizard.closed.scanStarted")]
                  .filter(Boolean)
                  .join(PUNTO),
            dato: cartelle > 0,
            attenzione: cartelle > 0 && !chiuso.letta,
          },
        ]),
    {
      voce: t("wizard.closed.seeing"),
      valore: t(chiuso.chiave ? "wizard.closed.key" : "wizard.closed.noKey"),
      dato: chiuso.chiave,
    },
  ]
  const nonPartita = cartelle !== null && cartelle > 0 && !chiuso.letta
  return (
    <CorniceAvvio
      passi={passi}
      titolo={t("wizard.closed.title")}
      perche={t("wizard.closed.why")}
      gesti={
        <>
          <span className="al-avvio__blocco-9" />
          <Comando testo={t("wizard.closed.open")} verso="pieno" onClick={onApri} />
        </>
      }
    >
      <div className="al-avvio__colonna-21">
        <ul className="al-avvio__colonna-23">
          {righe.map((r) => {
            const s = segno(r.dato ? "fatto" : "saltato", 0)
            return (
              <li
                key={r.voce}
                className="al-avvio__centro-7"
                style={{ gridTemplateColumns: m.chiusura }}
              >
                <span
                  className="al-avvio__tondo-5"
                  aria-hidden="true"
                  style={r.attenzione ? AVVISO : s.stile}
                >
                  {r.attenzione ? "!" : s.testo}
                </span>
                <span className="al-avvio__testo-21">{r.voce}</span>
                <span
                  className="al-avvio__testo-22"
                  style={{ gridColumn: m.valore, color: r.dato ? "var(--testo)" : "var(--tenue)" }}
                >
                  {r.valore}
                </span>
              </li>
            )
          })}
        </ul>
        {nonPartita && (
          <Avviso tipo="riga" formato={formato} segno="!" titolo={t("wizard.closed.notStarted")} />
        )}
      </div>
    </CorniceAvvio>
  )
}
