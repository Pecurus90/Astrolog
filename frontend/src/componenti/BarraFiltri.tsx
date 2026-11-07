import { VARIANTE } from "../FiltriUsati"
import { numero, oreEMinuti, t } from "../i18n"
import { type Formato, useTema } from "./Tema"

/** One filter of the night, as the app sends it. */
export interface PezzoFiltro {
  /** The canonical passband (`FilterUsed.passband`): it gives the colour, never the name. */
  banda: string
  /** The filter's name, as the user wrote it. */
  nome: string
  frame: number
  /** Integration in seconds; null when the frames say no duration. */
  secondi: number | null
  /** Width of the piece: the app's weight (seconds, or frames in a night without time). */
  peso: number
}

/**
 * Hours per filter (v76 `BarraFiltri`): coloured pieces, an unknown filter dashed, and with
 * `righe` a line per filter with name, frames and hours.
 */
export function BarraFiltri({
  filtri,
  altezza = 12,
  righe = false,
  anima = false,
  formato = "desktop",
}: {
  filtri: PezzoFiltro[]
  /** Bar height in px: 12, or 8 in a list row. */
  altezza?: number
  righe?: boolean
  /** The bar grows in from the left (`data-an="barra"`). */
  anima?: boolean
  formato?: Formato
}) {
  const { modo, accento } = useTema()
  const telefono = formato === "telefono"
  const pezzi = filtri.map((f) => ({
    ...f,
    variante: VARIANTE[f.banda] ?? VARIANTE["UNKNOWN"],
    fr: t("ui.filterBar.frames", { n: numero(f.frame) }),
    h: f.secondi === null ? t("ui.filterBar.untimed") : oreEMinuti(f.secondi),
  }))
  const detto = t("ui.filterBar.label", {
    filtri: pezzi.map((f) => `${f.nome} ${f.h}`).join(", "),
  })
  const barra = pezzi.map((f, i) => (
    <span
      key={i}
      className={`al-c-barra-filtri__blocco-2 ${f.variante}`}
      style={{ flex: f.peso }}
    />
  ))
  return (
    <div className="al-c-barra-filtri__blocco-1" data-modo={modo} data-accento={accento}>
      {anima ? (
        <span
          className="al-c-barra-filtri__riga-1"
          data-an="barra"
          role="img"
          aria-label={detto}
          style={{ height: `${altezza}px` }}
        >
          {barra}
        </span>
      ) : (
        <span
          className="al-c-barra-filtri__riga-2"
          role="img"
          aria-label={detto}
          style={{ height: `${altezza}px` }}
        >
          {barra}
        </span>
      )}
      {righe &&
        pezzi.map((f, i) => (
          <span
            key={i}
            className="al-c-barra-filtri__centro-1"
            style={{
              gridTemplateColumns: `12px minmax(0,1fr) auto ${telefono ? "66px" : "76px"}`,
              gap: telefono ? "8px" : "10px",
              fontSize: telefono ? "13px" : "14px",
            }}
          >
            <i className={`al-c-barra-filtri__blocco-3 ${f.variante}`} />
            <b className="al-c-barra-filtri__blocco-4">{f.nome}</b>
            <span
              className="al-c-barra-filtri__testo-1"
              style={{ fontSize: telefono ? "12px" : "13px" }}
            >
              {f.fr}
            </span>
            <span className="al-c-barra-filtri__testo-2">{f.h}</span>
          </span>
        ))}
    </div>
  )
}
