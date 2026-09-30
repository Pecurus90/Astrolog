import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { GraficoDellaNotte } from "./GraficoDellaNotte"
import { PannelloDellaLuna } from "./PannelloDellaLuna"
import { CLASSI, TINTE_IN_BARRA } from "./ScalaDelCielo"
import { type Fascia, tracciatoDellaLuna } from "./disegnoDellaLuna"
import { numero, oraDelSito, t } from "./i18n"
import { Accordo, type Breve, Giudizio, VentoInQuota } from "./NotteDelMeteo"

/**
 * Il piede della barra: da dove osservi, e che luna fa stanotte.
 *
 * Il contratto sta in `docs/domini/navigazione.md`; i numeri arrivano gia' fatti da
 * `GET /api/v1/tonight` (`docs/domini/effemeridi.md`).
 *
 * - **Qui non si calcola niente**: ne' la classe di Bortle, ne' da che parte e' illuminata la
 *   Luna. Solo il disegno, che sta in `disegnoDellaLuna.ts`.
 * - **Ogni vuoto e' una frase, mai un trattino.**
 * - **Niente bottone finche' non c'e' il pannello**: un comando che non apre niente e' una
 *   promessa che l'app non mantiene.
 */
const TELA = { larghezza: 227, altezza: 40 }

export function Stanotte() {
  const stanotte = useQuery({
    queryKey: ["tonight"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/tonight")
      if (error) throw new Error(t("tonight.failed"))
      return data
    },
    // Questa rotta campiona una notte di cielo e costa cento volte una lettura: coi tempi di
    // riserva si richiederebbe a ogni ritorno sulla finestra. La Luna cambia una volta al giorno
    // e il meteo ogni tre ore, e chi li cambia a mano -- il Meteo, le Impostazioni -- la butta via;
    // la scadenza vera al mezzogiorno del sito sta in coda, e intanto un'ora larga basta. Finche'
    // la prima previsione non arriva la si richiede piu' spesso, per non dire "non e' arrivata"
    // un'ora dopo che e' arrivata.
    staleTime: 60 * 60 * 1000,
    refetchInterval: (q) => rileggiOgni(q.state.data),
  })
  const detto = stanotte.data

  return (
    <div className="as-lato__coda">
      <div className="as-luna">
        <p className="as-soprattitolo">{t("tonight.title")}</p>
        {stanotte.isPending && <p>{t("tonight.loading")}</p>}
        {stanotte.isError && <Avviso esito="allarme">{t("tonight.failed")}</Avviso>}
        {detto && detto.site === null && (
          <>
            <p>{t("tonight.nosite")}</p>
            {/* Adesso il rimando porta davvero dove si ripara: la sezione del sito esiste. */}
            <Bottone a="/impostazioni/sito" piccolo>
              {t("tonight.nosite.how")}
            </Bottone>
          </>
        )}
        {detto?.site && (
          <>
            <Cielo nome={detto.site.name} bortle={detto.site.bortle} />
            {detto.moon === null ? (
              <p>{t("tonight.notimezone")}</p>
            ) : (
              <>
                <Luna fasce={detto.sky_bands} luna={detto.moon} />
                {/* senza fuso la notte non si divide, e la previsione non arriva mai: lo dice gia'
                    la riga sopra, e il Meteo spiega perche' */}
                <MeteoDiStanotte meteo={detto.weather ?? null} />
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

/** Il sito e la sua classe di cielo, come rampa: la posizione dice **quanto e' buono**, che una
 *  cifra su nove da sola non dice. La misura in magnitudini qui non compare, ed e' una delle due
 *  eccezioni dichiarate nel foglio -- in 227px vince il promemoria di dov'e' puntata l'app. */
function Cielo({ nome, bortle }: { nome: string; bortle: number | null }) {
  return (
    <div className={["as-bortle-scala", bortle === null ? "as-bortle-scala--ignota" : ""].filter(Boolean).join(" ")}>
      <p className="as-bortle-scala__dice">
        <b>{nome}</b>
        {" \u00B7 "}
        {bortle === null ? (
          <span className="as-bortle-scala__ignota">{t("tonight.sky.none")}</span>
        ) : (
          t("tonight.sky", { n: bortle })
        )}
      </p>
      <div
        className="as-bortle-scala__scala"
        role="img"
        aria-label={
          bortle === null ? t("tonight.sky.none.label", { sito: nome }) : t("tonight.sky.label", { n: bortle, sito: nome })
        }
      >
        {CLASSI.map((classe) => (
          <span
            className={[
              "as-bortle-scala__voce",
              bortle === null ? "" : TINTE_IN_BARRA[classe],
              classe === bortle ? "as-bortle-scala__voce--qui" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            key={classe}
          >
            <span className="as-bortle-scala__banda" />
            {classe === bortle && <b>{numero(classe)}</b>}
          </span>
        ))}
      </div>
      <p className="as-bortle-scala__estremi">
        <span>{t("sky.low")}</span>
        <span>{t("sky.high")}</span>
      </p>
    </div>
  )
}

type LunaDetta = components["schemas"]["MoonOut"]

/**
 * La Luna in barra: **un bersaglio solo**, che apre il pannello.
 *
 * Disco, grafico e orari sarebbero tre soste di tabulatore per una cosa sola -- lo dichiara il
 * foglio. Il nome del bottone e' cio' che c'e' dentro, il grafico compreso: e' lungo, ma e' il
 * dato per intero, e il numero di quanto sale in barra non e' scritto da nessun'altra parte.
 */
function Luna({ luna, fasce }: { luna: LunaDetta; fasce: readonly Fascia[] }) {
  const [aperto, setAperto] = useState(false)
  const illuminata = tracciatoDellaLuna(luna.illumination_pct, luna.lit_side === "right")
  return (
    <>
      <button
        aria-haspopup="dialog"
        className="as-luna__apri"
        type="button"
        onClick={() => setAperto(true)}
      >
      <span className="as-luna__fase">
        <svg className="as-luna__faccia" viewBox="-12 -12 24 24" aria-hidden="true">
          <circle className="as-luna__disco" cx="0" cy="0" r="10" />
          {illuminata && <path className="as-luna__illuminata" d={illuminata} />}
        </svg>
        <span className="as-luna__dice">
          <span className="as-luna__nome">{t(`moon.${luna.phase_key}`)}</span>
          <span className="as-luna__quanto">
            {t("tonight.illuminated", { pct: luna.illumination_pct })}
          </span>
        </span>
      </span>
      <GraficoDellaNotte
        altezza={TELA.altezza}
        fasce={fasce}
        id="stanotte-tela"
        larghezza={TELA.larghezza}
        luna={luna}
      />
      <span className="as-luna__orari">
        <Orario quando={luna.rise} verbo="tonight.rise" mai="tonight.rise.never" />
        <Orario quando={luna.set} verbo="tonight.set" mai="tonight.set.never" />
      </span>
      </button>
      {aperto && <PannelloDellaLuna fasce={fasce} luna={luna} onChiudi={() => setAperto(false)} />}
    </>
  )
}

/** Un orario della notte, o la frase che dice che stanotte non succede.
 *
 * **Quanto sale non sta qui**: in 227px il grafico lo mostra gia', e il numero si legge nel
 * pannello accanto all'ora. E' una decisione del disegno, dichiarata nel foglio. */
function Orario({
  quando,
  verbo,
  mai,
}: {
  quando: string | null
  verbo: "tonight.rise" | "tonight.set"
  mai: "tonight.rise.never" | "tonight.set.never"
}) {
  if (quando === null) {
    return <span className="as-luna__orario as-luna__orario--mai">{t(mai)}</span>
  }
  return (
    <span className="as-luna__orario">
      {t(verbo)} <b>{oraDelSito(quando)}</b>
    </span>
  )
}

/** Il meteo della notte in corso, sotto la Luna: il verdetto, le nuvole, le ore utili, l'accordo e
 *  il vento in quota, e il collegamento al Meteo per il resto. Nudo: la veste arriva col design. */
function MeteoDiStanotte({ meteo }: { meteo: Breve | null }) {
  return (
    <div>
      {meteo === null ? (
        <p>{t("tonight.weather.none")}</p>
      ) : (
        <>
          <Giudizio breve={meteo} />
          <Accordo breve={meteo} />
          <VentoInQuota breve={meteo} />
        </>
      )}
      <Link to="/meteo">{t("tonight.weather.open")}</Link>
    </div>
  )
}

/** Ogni quanto rileggere Stanotte: spesso solo mentre c'e' una notte da dividere e la sua previsione
 *  non e' ancora arrivata; senza fuso non arrivera' mai, e con la previsione basta la scadenza. */
export function rileggiOgni(detto: { moon: unknown; weather?: unknown } | undefined) {
  return detto?.moon && !detto.weather ? 5 * 60 * 1000 : false
}
