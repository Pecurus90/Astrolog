/**
 * La misura di molti frame su una riga (tavola v76, `componenti/Quartili.dc.html`): traccia,
 * banda dal primo al terzo quartile, segno della mediana. Le posizioni arrivano in %; colori e
 * misure stanno nel foglio.
 */
export function Quartili({
  q1,
  qw,
  m,
  misura = "normale",
}: {
  q1: string
  qw: string
  m: string
  misura?: "normale" | "piccola"
}) {
  return (
    <div className="al-c-quartili__blocco-1">
      <div
        aria-hidden="true"
        className={`al-quartili ${misura === "piccola" ? "al-quartili--piccolo" : ""}`}
      >
        <div className="al-quartili__traccia" />
        <div className="al-quartili__banda" style={{ left: q1, width: qw }} />
        <div className="al-quartili__mediana" style={{ left: m }} />
      </div>
    </div>
  )
}
