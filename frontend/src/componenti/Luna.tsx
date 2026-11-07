import { tracciatoDellaLuna } from "../disegnoDellaLuna"
import { numero, t } from "../i18n"
import { type Formato, useTema } from "./Tema"

/**
 * The Moon (v76 `Luna`): phase disc, and beside it title and line when given. The lit side comes
 * from the app (`lit_side`), so the southern hemisphere draws right too.
 */
export function Luna({
  percento,
  lato,
  misura = 30,
  piena = false,
  titolo,
  testo,
  formato = "desktop",
}: {
  /** Illuminated fraction, 0-100. */
  percento: number
  /** The lit limb, as the app sends it. */
  lato: "destra" | "sinistra"
  /** Side of the disc in px: 20, 22, 30, 34, 60, 76 in the delivery. */
  misura?: number
  /** The disc fills its box (Dashboard). */
  piena?: boolean
  titolo?: string
  testo?: string
  formato?: Formato
}) {
  const { modo, accento } = useTema()
  const m = piena ? 10.2 : 12
  // delivery's stroke: about 1 px on screen at any size
  const tratto = piena ? 24 / misura : misura <= 24 ? 1 : misura <= 34 ? 0.8 : 24 / misura
  const illuminata = tracciatoDellaLuna(percento, lato === "destra")
  const detto = t("ui.moon.lit", { pct: numero(percento) })
  const disco = (
    <svg
      className="al-c-luna__grafico-1"
      width={misura}
      height={misura}
      viewBox={`${-m} ${-m} ${2 * m} ${2 * m}`}
      role="img"
      aria-label={titolo ? `${titolo}, ${detto}` : detto}
    >
      <circle r="10" fill="var(--luna-scura)" stroke="var(--luna-linea)" strokeWidth={tratto} />
      {illuminata && <path d={illuminata} fill="var(--luna-chiara)" />}
    </svg>
  )
  return (
    <div className="al-c-luna__blocco-1" data-modo={modo} data-accento={accento}>
      {titolo || testo ? (
        <span className="al-c-luna__riga-1" style={{ gap: misura >= 34 ? "12px" : "10px" }}>
          {disco}
          <span className="al-c-luna__colonna-1">
            <b
              className="al-c-luna__testo-1"
              style={{ fontSize: formato === "telefono" ? "15px" : "14px" }}
            >
              {titolo}
            </b>
            <span className="al-c-luna__testo-2">{testo}</span>
          </span>
        </span>
      ) : (
        disco
      )}
    </div>
  )
}
