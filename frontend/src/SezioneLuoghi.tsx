import { useContext } from "react"
import { useNavigate } from "react-router"

import { Avviso } from "./componenti/Avviso"
import { FormatoConf, statoDi } from "./ConfermareGuscio"
import { Domanda, Parte, Risposte, righeDelleNotti, rigaDeiFrame, voce } from "./Domanda"
import { Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { coordinate, numero, t } from "./i18n"
import { provaDeiSoggetti } from "./Soggetti"

type Posto = components["schemas"]["UnclearCoordinates"]
type Risposta = components["schemas"]["CoordinatesEdit"]

/**
 * I frame ripresi a coordinate che non cadono in nessun sito dichiarato: **una domanda per posto**
 * (le coordinate arrotondate al chilometro), non per notte: la risposta vale anche per le notti
 * che verranno.
 *
 * - **I siti arrivano dal piu' vicino**, nell'ordine dell'API; il primo **non e' scelto**: una
 *   notte attribuita male e' un dato falso che nessuno rilegge.
 * - **Senza nessun sito** non si risponde: la frase approvata (Marco, 17/10/2026) e le Impostazioni.
 * - La distanza dal sito predefinito **solo se c'e'**: senza, non e' zero.
 */
export function SezioneLuoghi({
  posti,
  risposte,
  onRisposta,
}: {
  posti: Posto[]
  risposte: Record<string, Risposta>
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  return (
    <Sezione
      quale="unclear"
      domanda={t("review.unclear.why")}
      voci={posti}
      chiave={(p) => p.key}
      riga={(p) => <RigaLuoghi posto={p} risposta={risposte[p.key]} onRisposta={onRisposta} />}
    />
  )
}

function RigaLuoghi({
  posto,
  risposta,
  onRisposta,
}: {
  posto: Posto
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const vaiA = useNavigate()
  const formato = useContext(FormatoConf)
  // `site` c'e' solo se quel sito esiste ancora: una risposta che non aggancia piu' torna domanda
  const data = posto.candidates.find((c) => c.name === posto.site)
  const scelto = posto.candidates.find((c) => c.id === (risposta?.site_id ?? data?.id))
  const dove = coordinate(posto.latitude, posto.longitude)
  const senzaSiti = posto.candidates.length === 0
  const domanda = t("review.unclear.question", { posto: dove })
  return (
    <Domanda
      id={`unclear:${posto.key}`}
      voce={dove}
      nome={dove}
      frame={rigaDeiFrame(posto.frames)}
      prova={[
        ...provaDeiSoggetti(posto.subjects),
        ...(posto.distance_km === null
          ? []
          : [
              {
                nome: t("review.proof.distance"),
                righe: [t("review.unclear.fromHome", { km: numero(posto.distance_km) })],
              },
            ]),
        // Un elenco vuoto non e' una riga vuota: l'app non sa in che notte cadano, e lo dice.
        posto.nights.length === 0
          ? {
              nome: t("review.proof.nights"),
              righe: [t("review.unclear.nights.later")],
              tenue: true,
            }
          : { nome: t("review.proof.nights"), righe: righeDelleNotti(posto.nights) },
      ]}
      stato={statoDi(data !== undefined, risposta !== undefined)}
      era={data?.name}
      detta={scelto !== undefined}
      breve={scelto ? scelto.name : posto.candidates.map((c) => c.name).join(" \u00b7 ")}
    >
      <Parte capo={domanda} prima>
        {senzaSiti ? (
          <Avviso
            tipo="blocco"
            formato={formato}
            segno="?"
            titolo={t("review.unclear.noSites")}
            azione={t("review.unclear.noSites.action")}
            onAzione={() => void vaiA("/impostazioni/sito")}
          />
        ) : (
          <Risposte
            etichetta={domanda}
            opzioni={posto.candidates.map((c) =>
              voce(
                scelto?.id === c.id,
                t("review.unclear.site", { luogo: c.name, km: numero(c.distance_km) }),
                () =>
                  onRisposta(
                    posto.key,
                    c.id === data?.id ? null : { key: posto.key, site_id: c.id },
                  ),
              ),
            )}
          />
        )}
      </Parte>
    </Domanda>
  )
}
