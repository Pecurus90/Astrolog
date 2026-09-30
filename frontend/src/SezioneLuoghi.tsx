import { Scelte } from "./Scelte"
import { Dettaglio, Riga } from "./Riga"
import { Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Posto = components["schemas"]["UnclearCoordinates"]
type Risposta = components["schemas"]["CoordinatesEdit"]

/**
 * Le pose riprese a coordinate che non cadono in nessun luogo dichiarato: **una domanda per posto**
 * (le coordinate arrotondate al chilometro), non per notte, perche' la risposta e' un fatto sul posto
 * e vale anche per le notti che verranno.
 *
 * - **I luoghi arrivano dal piu' vicino** a quelle coordinate, e l'ordine e' dell'API; il primo e'
 *   quasi sempre la risposta, ma **non e' scelto**: una notte attribuita male e' un dato falso che
 *   nessuno rilegge.
 * - **Un posto risposto resta in pagina** col suo luogo, e ridare lo stesso non manda niente.
 * - La distanza da casa **solo se c'e' una casa**: senza, non e' zero.
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
    <Sezione titolo={t("review.unclear")} domanda={t("review.unclear.why")}
      voci={posti}
      chiave={(p) => p.key}
      riga={(p) => (
        <RigaLuoghi posto={p} risposta={risposte[p.key]} onRisposta={onRisposta} />
      )}
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
  // `site` c'e' solo se quel luogo esiste ancora: una risposta che non aggancia piu' torna domanda,
  // e a deciderlo e' il backend, lo stesso che la conta
  const data = posto.candidates.find((c) => c.name === posto.site)
  return (
    <Riga
      frames={posto.frames}
      ripreso={posto.subjects}
      nome={posto.key}
      stato={risposta ? "risposta" : undefined}
      dettagli={
        <>
          {posto.distance_km !== null && (
            <Dettaglio>{t("review.unclear.fromHome", { km: numero(posto.distance_km) })}</Dettaglio>
          )}{" "}
          {/* Un elenco vuoto non e' una riga vuota: l'app non sa ancora in che notte cadano
              queste pose e non ne indovina una, e lo dice. */}
          <Dettaglio>
            {posto.nights.length === 0
              ? t("review.unclear.nights.later")
              : t("review.unclear.nights", { notti: posto.nights.join(", ") })}
          </Dettaglio>
        </>
      }
    >
      <Scelte
        domanda={t("review.unclear.question", { posto: posto.key })}
        nome={`luogo-${posto.key}`}
        opzioni={posto.candidates.map((c) => ({
          valore: c.id,
          etichetta: t("review.unclear.site", { luogo: c.name, km: numero(c.distance_km) }),
        }))}
        scelta={risposta?.site_id ?? data?.id}
        onScelta={(id) =>
          onRisposta(posto.key, id === data?.id ? null : { key: posto.key, site_id: id })
        }
      />
    </Riga>
  )
}
