import { Bottone } from "./Bottone"
import { Dialogo } from "./Dialogo"
import { GraficoDellaNotte } from "./GraficoDellaNotte"
import type { components } from "./api/schema"
import { type Fascia, tracciatoDellaLuna } from "./disegnoDellaLuna"
import { numero, oraDelSito, t } from "./i18n"

/**
 * Il **pannello della Luna**: cio' che in 227px non ci sta.
 *
 * - **E' un dialogo, non una comparsa**: la barra e' larga 252px e il pannello non ci sta dentro,
 *   quindi deve stare **sopra** la pagina -- lo dichiara il foglio, che gli da' anche la misura
 *   larga (una tela intera, che a 440px si rimpicciolirebbe insieme alle etichette).
 * - **I riquadri sono tre, non due**: *quanto sale* e' il numero che decide la notte -- una piena
 *   che resta bassa disturba meno di una mezza che passa allo zenit -- e in barra non ci sta. Si
 *   dice **"sale fino a"** e non "culmina", ed e' una parola decisa (`domini/glossario.md`).
 * - **Cio' che stanotte non succede e' una frase**, mai un trattino e mai un'ora finta.
 */
// Le misure vengono dal foglio, e **devono** restare le sue: 480 e' `--grafico-largo` e 180
// `--grafico-alto`. A una larghezza diversa da quella del riquadro la tela si scala, e con lei il
// corpo delle etichette -- che a quel punto non sono piu' quelle che il design ha misurato.
const TELA = { larghezza: 480, altezza: 180 }

type LunaDetta = components["schemas"]["MoonOut"]

export function PannelloDellaLuna({
  luna,
  fasce,
  onChiudi,
}: {
  luna: LunaDetta
  fasce: readonly Fascia[]
  onChiudi: () => void
}) {
  const illuminata = tracciatoDellaLuna(luna.illumination_pct, luna.lit_side === "right")
  return (
    <Dialogo
      azioni={
        <Bottone verso="tenue" onClick={onChiudi}>
          {t("moon.panel.close")}
        </Bottone>
      }
      largo
      onChiudi={onChiudi}
      testa={
        <div className="as-luna__testa">
          <svg className="as-luna__faccia as-luna__faccia--grande" viewBox="-12 -12 24 24" aria-hidden="true">
            <circle className="as-luna__disco" cx="0" cy="0" r="10" />
            {illuminata && <path className="as-luna__illuminata" d={illuminata} />}
          </svg>
          <div>
            <h2 className="as-luna__titolo-fase">{t(`moon.${luna.phase_key}`)}</h2>
            <p className="as-luna__percento">
              {t("tonight.illuminated", { pct: luna.illumination_pct })}
            </p>
          </div>
        </div>
      }
      titolo={t(`moon.${luna.phase_key}`)}
    >
      <div className="as-luna__cielo">
        <GraficoDellaNotte
          etichette
          altezza={TELA.altezza}
          fasce={fasce}
          id="pannello-luna-tela"
          larghezza={TELA.larghezza}
          luna={luna}
        />
      </div>
      {/* La legenda e' scritta, e i segni sono **gli stessi** della tela: le classi si scrivono
          qui per esteso, una per voce, perche' da una variabile la guardia della veste non
          leggerebbe nessuna classe -- ed e' la forma in cui una classe sbagliata passa. */}
      <ul className="as-luna__legenda">
        <li>
          <svg aria-hidden="true" height="10" viewBox="0 0 16 10" width="16">
            <line className="as-grafico__luna" x1="0" x2="16" y1="5" y2="5" />
          </svg>
          {t("moon.panel.legend.moon")}
        </li>
        <li>
          <svg aria-hidden="true" height="10" viewBox="0 0 16 10" width="16">
            <line className="as-grafico__adesso" x1="8" x2="8" y1="0" y2="10" />
          </svg>
          {t("moon.panel.legend.now")}
        </li>
        <li>
          <svg aria-hidden="true" height="10" viewBox="0 0 16 10" width="16">
            <rect className="as-grafico__terra" height="10" width="16" x="0" y="0" />
          </svg>
          {t("moon.panel.legend.ground")}
        </li>
        {/* La rampa del cielo: i cinque gradini scritti per esteso, come nella tela, perche' da
            una variabile la guardia della veste non leggerebbe nessuna classe. */}
        <li>
          <svg aria-hidden="true" height="10" viewBox="0 0 20 10" width="20">
            <rect className="as-fascia--giorno" height="10" width="4" x="0" y="0" />
            <rect className="as-fascia--civile" height="10" width="4" x="4" y="0" />
            <rect className="as-fascia--nautico" height="10" width="4" x="8" y="0" />
            <rect className="as-fascia--astronomico" height="10" width="4" x="12" y="0" />
            <rect className="as-fascia--notte" height="10" width="4" x="16" y="0" />
          </svg>
          {t("moon.panel.legend.sky")}
        </li>
      </ul>
      <div className="as-luna__quando">
        <Quando
          nome="moon.panel.rise"
          quando={luna.rise === null ? t("moon.panel.rise.never") : oraDelSito(luna.rise)}
          senza={luna.rise === null}
        />
        <Quando
          nome="moon.panel.set"
          quando={luna.set === null ? t("moon.panel.set.never") : oraDelSito(luna.set)}
          senza={luna.set === null}
        />
        {/* Il punto piu' alto **non manca mai**: una Luna che non sorge sale lo stesso, sotto
            l'orizzonte, e quanto poco sale e' proprio la risposta. Qui il numero grande sono i
            **gradi**, non l'ora: la domanda e' quanto sale, e l'ora e' il suo contorno. */}
        <Quando
          coda={t("moon.panel.at", { ora: oraDelSito(luna.highest.at) })}
          nome="moon.panel.highest"
          quando={t("moon.panel.degrees", { gradi: numero(luna.highest.altitude_deg) })}
          senza={false}
        />
      </div>
    </Dialogo>
  )
}

/** Un riquadro della notte: come si chiama, il numero grande, e -- se c'e' -- cio' che gli sta
 *  sotto. */
function Quando({
  nome,
  quando,
  coda,
  senza,
}: {
  nome: "moon.panel.rise" | "moon.panel.set" | "moon.panel.highest"
  quando: string
  coda?: string | undefined
  /** Stanotte non succede: la terza forma del dato, che il foglio veste da se'. */
  senza: boolean
}) {
  return (
    <div className={senza ? "as-luna__quando-voce as-luna__quando-voce--mai" : "as-luna__quando-voce"}>
      <span className="as-luna__quando-nome">{t(nome)}</span>
      <span className="as-luna__quando-ora">{quando}</span>
      {coda !== undefined && <span className="as-luna__quando-coda">{coda}</span>}
    </div>
  )
}

