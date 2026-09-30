import { useEffect, useState } from "react"

import type { components } from "./api/schema"
import { type Fascia, curvaDellaNotte } from "./disegnoDellaLuna"
import { numero, oraDelSito, t } from "./i18n"

/**
 * Come sale la Luna stanotte, disegnato: la stessa tela in **due misure**.
 *
 * Sta in un file suo perche' la striscia della barra e il pannello mostrano **lo stesso disegno**
 * -- lo dichiara il foglio -- e due copie divergerebbero al primo ritocco. La scala verticale e'
 * una sola, da `PAVIMENTO_DEG` al tetto del sito: se cambiasse fra i due posti non sarebbero piu'
 * lo stesso grafico, e due notti non si confronterebbero piu' a occhio.
 *
 * - **In barra non ci sono ne' assi ne' etichette**: la tela e' alta quanto una riga di testo, e
 *   una scritta li' dentro coprirebbe la curva invece di spiegarla. Il dato per chi non vede la
 *   tela lo porta il nome della figura.
 * - **Le fasce del cielo stanno dietro la curva**, e arrivano **gia' divise** dalla rotta: qui
 *   diventano colonne e basta.
 */
type LunaDetta = components["schemas"]["MoonOut"]

export function GraficoDellaNotte({
  luna,
  fasce,
  larghezza,
  altezza,
  id,
  etichette = false,
}: {
  luna: LunaDetta
  /** Le fasce del cielo, come le manda la rotta. Vuote finche' il sito non ha un fuso: allora
   *  la tela resta senza fondo invece di inventarne uno piatto. */
  fasce: readonly Fascia[]
  larghezza: number
  altezza: number
  /** Serve al ritaglio, e due tele nella stessa pagina non possono chiamarlo uguale. */
  id: string
  /** I gradi a sinistra e le ore tonde in basso: solo dove c'e' spazio per leggerli. */
  etichette?: boolean
}) {
  const adesso = useOgniMinuto()
  const disegno = curvaDellaNotte(luna.track, luna.ceiling_deg, larghezza, altezza, adesso, fasce)
  if (!disegno) return null
  // Il buio e' **il dato** che le fasce mostrano, e in una notte ce n'e' al massimo uno: la
  // finestra va da mezzogiorno a mezzogiorno, quindi il Sole scende una volta sola.
  const buio = fasce.find((f) => f.kind === "dark")
  const iBuio = disegno.fasceDipinte.findIndex((f) => f.kind === "dark")
  const fasciaDelBuio = disegno.fasceDipinte[iBuio]
  // I capelli vanno sui confini **intermedi**: dove va l'accento del buio non va anche il capello,
  // o si sommano due segni e -- `--fascia-istante` e' semitrasparente -- ne esce una tinta che il
  // foglio non ha disegnato.
  //
  // Si contano per **posizione**, non confrontando le x: il bordo destro del buio, ricostruito
  // come `x + larghezza`, non e' sempre lo stesso numero della x della fascia dopo -- in virgola
  // mobile `da + (a - da)` puo' finire un ulp piu' in la', e succede sulle notti vere delle alte
  // latitudini, cioe' proprio dove il buio e' lungo. L'indice non ha decimali.
  const confini = disegno.fasceDipinte.filter((_, i) => i !== 0 && i !== iBuio && i !== iBuio + 1)

  return (
    <svg
      aria-label={
        // Il nome si compone **qui** e non nei due montaggi: e' lo stesso disegno, quindi e' lo
        // stesso dato, e scritto due volte divergerebbe. Col buio dentro, perche' senza questa
        // frase le fasce sarebbero solo un colore per chi non vede la tela.
        t("tonight.chart", {
          gradi: numero(luna.highest.altitude_deg),
          ora: oraDelSito(luna.highest.at),
        }) + (buio ? ` ${t("tonight.dark", { da: oraDelSito(buio.starts_at), a: oraDelSito(buio.ends_at) })}` : "")
      }
      className={
        // per esteso nei due rami, non composta: da un pezzo attaccato a un altro la guardia
        // della veste non legge nessuna classe, ed e' la forma in cui una sbagliata sfugge
        etichette
          ? "as-grafico__tela as-grafico__tela--alta"
          : "as-grafico__tela as-grafico__tela--bassa"
      }
      role="img"
      viewBox={`0 0 ${larghezza} ${altezza}`}
    >
      {/* La tela non taglia da sola (`overflow: visible` nel foglio) e la curva scende fino a
          settanta gradi sotto l'orizzonte: senza ritaglio finirebbe sopra cio' che le sta sotto. */}
      <defs>
        <clipPath id={id}>
          <rect height={altezza} width={larghezza} x="0" y="0" />
        </clipPath>
      </defs>
      {/* Il cielo sta **dietro tutto**: e' il fondo su cui passa la Luna, e disegnato dopo
          coprirebbe la curva che deve spiegare. */}
      {disegno.fasceDipinte.map((dipinta) => (
        <FasciaDipinta altezza={altezza} fascia={dipinta} key={dipinta.starts_at} />
      ))}
      {/* I confini, come li vuole il foglio: **capelli, non muri**. I due che chiudono il buio
          prendono l'accento, perche' sono i soli due momenti che si guardano -- e nel tema scuro
          la fascia del buio non dipinge niente (`--fascia-notte: transparent`), quindi senza
          questi segni la finestra che conta si leggerebbe solo dal bordo della fascia accanto. */}
      {confini.map((dipinta) => (
        <line
          className="as-grafico__confine"
          key={dipinta.starts_at}
          x1={dipinta.x}
          x2={dipinta.x}
          y1="0"
          y2={altezza}
        />
      ))}
      {fasciaDelBuio && (
        <>
          <line
            className="as-grafico__istante"
            x1={fasciaDelBuio.x}
            x2={fasciaDelBuio.x}
            y1="0"
            y2={altezza}
          />
          <line
            className="as-grafico__istante"
            x1={fasciaDelBuio.x + fasciaDelBuio.larghezza}
            x2={fasciaDelBuio.x + fasciaDelBuio.larghezza}
            y1="0"
            y2={altezza}
          />
        </>
      )}
      <rect
        className="as-grafico__terra"
        height={altezza - disegno.orizzonte}
        width={larghezza}
        x="0"
        y={disegno.orizzonte}
      />
      <path className="as-grafico__luna" clipPath={`url(#${id})`} d={disegno.curva} />
      <line
        className="as-grafico__orizzonte"
        x1="0"
        x2={larghezza}
        y1={disegno.orizzonte}
        y2={disegno.orizzonte}
      />
      {disegno.adesso !== null && (
        <line
          className="as-grafico__adesso"
          x1={disegno.adesso}
          x2={disegno.adesso}
          y1="0"
          y2={altezza}
        />
      )}
      {etichette && (
        <>
          <rect className="as-grafico__cornice" height={altezza} width={larghezza} x="0" y="0" />
          {/* Il tetto e l'orizzonte, che sono i due numeri che la scala promette. Lo zero si
              scrive a parole: "0 gradi" e' l'orizzonte, e la parola lo dice senza farlo dedurre. */}
          <text className="as-grafico__etichetta" x="4" y="12">
            {t("moon.panel.axisDeg", { n: numero(luna.ceiling_deg) })}
          </text>
          <text className="as-grafico__etichetta as-grafico__etichetta--testo" x="4" y={disegno.orizzonte - 4}>
            {t("moon.panel.horizon")}
          </text>
          {/* L'asse del tempo: le ore tonde lungo la notte. **Due sole etichette agli estremi
              direbbero "12:00" tutte e due** -- la notte va da mezzogiorno a mezzogiorno -- e non
              direbbero ne' quando ne' quanto dura. Le prime e l'ultima si ancorano al bordo, o
              escono dalla tela. */}
          {/* **Sopra la fascia**, non con l'inchiostro debole: le ore cadono sempre dentro il
              terreno -- l'orizzonte sta piu' in alto della loro riga a qualunque latitudine -- e
              li' il debole fa 4,30:1 su 4,5 (`tools/controlli_contrasto.SOPRA_VELO`). */}
          {disegno.tacche.map((tacca) => (
            <text
              className="as-grafico__etichetta as-grafico__etichetta--sopra-fascia"
              key={tacca.at}
              textAnchor={tacca.x === 0 ? "start" : tacca.x >= larghezza ? "end" : "middle"}
              x={tacca.x === 0 ? 4 : tacca.x >= larghezza ? larghezza - 4 : tacca.x}
              y={altezza - 5}
            >
              {oraDelSito(tacca.at)}
            </text>
          ))}
        </>
      )}
    </svg>
  )
}

/** Il rettangolo di una fascia del cielo.
 *
 * Il nome arriva dal backend in inglese e la classe del foglio e' italiana: la traduzione fra i
 * due si scrive **un ramo per fascia, con la classe per esteso**. Da una mappa indicizzata la
 * guardia della veste non legge nessuna classe -- ed e' la forma in cui una sbagliata sfugge --
 * e questo `switch` su un elenco chiuso fa anche da guardia al contrario: una fascia nuova nel
 * backend non compila finche' non ha la sua tinta. Cinque righe sono il prezzo. */
function FasciaDipinta({
  fascia,
  altezza,
}: {
  fascia: { x: number; larghezza: number; kind: Fascia["kind"] }
  altezza: number
}) {
  const misura = { height: altezza, width: fascia.larghezza, x: fascia.x, y: 0 }
  switch (fascia.kind) {
    case "day":
      return <rect className="as-fascia--giorno" {...misura} />
    case "civil":
      return <rect className="as-fascia--civile" {...misura} />
    case "nautical":
      return <rect className="as-fascia--nautico" {...misura} />
    case "astronomical":
      return <rect className="as-fascia--astronomico" {...misura} />
    case "dark":
      return <rect className="as-fascia--notte" {...misura} />
  }
}

/** Adesso, che si muove da solo.
 *
 * La riga di *adesso* e' l'unica cosa del disegno che cambia da sola: al minuto basta, perche'
 * anche sulla tela grande un minuto e' meno di un pixel. Non si richiede niente al server -- la
 * finestra della notte e' gia' in mano. */
function useOgniMinuto() {
  const [quando, setQuando] = useState(() => new Date())
  useEffect(() => {
    const battito = setInterval(() => setQuando(new Date()), 60_000)
    return () => clearInterval(battito)
  }, [])
  return quando
}
