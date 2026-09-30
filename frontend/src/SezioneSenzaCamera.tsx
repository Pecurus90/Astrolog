import { useState } from "react"
import { Campo } from "./Campo"
import { Bottone } from "./Bottone"

import { Dettaglio, Prova, Riga } from "./Riga"
import { Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { nomeDelGruppo, numero, t } from "./i18n"
import { misura, testo } from "./scritto"

type Gruppo = components["schemas"]["RiglessGroup"]
type Corredo = components["schemas"]["RigChoice"]
type Risposta = components["schemas"]["RiglessGroupEdit"]

/**
 * Le pose che non dicono con che camera sono state riprese: **una domanda per gruppo**, cioe' per
 * notte e valori dell'header, che la riga dice al posto di un percorso. La risposta vale anche per
 * le pose che arriveranno con la stessa notte e gli stessi valori.
 *
 * - **Un corredo dall'elenco oppure i pezzi scritti**, mai tutti e due (`RiglessGroupEdit`).
 *   Quali corredi si possono scegliere lo dice l'API (`rig_choices`): qui non si filtra.
 * - **Scrivendo i pezzi, l'ottica che le pose dicono e la focale nativa sono proposte nei campi**,
 *   e la risposta parte solo quando c'e' la camera -- che e' cio' che la domanda chiede -- con una
 *   focale: un corredo a focale ignota resterebbe il gemello di quello che i file diranno domani.
 * - **Un gruppo risposto resta in pagina** con la sua risposta, e si cambia.
 */
export function SezioneSenzaCamera({
  gruppi,
  corredi,
  risposte,
  onRisposta,
}: {
  gruppi: Gruppo[]
  corredi: Corredo[]
  risposte: Record<string, Risposta>
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  return (
    <Sezione titolo={t("review.rigless")} domanda={t("review.rigless.why")}
      voci={gruppi}
      chiave={(g) => g.key}
      riga={(g, indice) => (
        <RigaSenzaCamera
          gruppo={g}
          // l'id nasce dalla posizione e non dalla chiave: la chiave porta spazi e virgolette, e
          // un id con dentro uno spazio non e' un id valido
          id={`senza-camera-${indice}`}
          corredi={corredi}
          risposta={risposte[g.key]}
          onRisposta={onRisposta}
        />
      )}
    />
  )
}

function RigaSenzaCamera({
  gruppo,
  id,
  corredi,
  risposta,
  onRisposta,
}: {
  gruppo: Gruppo
  id: string
  corredi: Corredo[]
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const [aperta, setAperta] = useState(gruppo.answer === null)
  const [aMano, setAMano] = useState(false)
  // La tendina ricorda la scelta per conto suo: la risposta in mano puo' essere vuota anche dopo
  // un clic -- quando si sceglie il corredo che e' gia' la risposta -- e la tendina tornerebbe a
  // "--" come se il clic non fosse stato preso.
  const [scelta, setScelta] = useState("")
  const data = gruppo.answer
  const ricordato = corredi.find((c) => String(c.id) === scelta)
  const inTendina =
    risposta?.rig_id != null ? String(risposta.rig_id) : ricordato && uguale(ricordato, data) ? scelta : ""
  const nome = nomeDellaCamera(gruppo)

  return (
    <Riga
      frames={gruppo.frames}
      ripreso={gruppo.subjects}
      nome={nome}
      stato={risposta ? "risposta" : undefined}
      dettagli={
        <>
          {gruppo.optics && (
            <Prova>{t("review.rigless.posesSay", { ottica: gruppo.optics })}</Prova>
          )}{" "}
          {data && (
            <Dettaglio>{t("review.rigless.answer", {
                corredo: conFocale(pezziDelCorredo(data), data.focal_mm),
              })}</Dettaglio>
          )}{" "}
        </>
      }
    >
      {/* I bottoni si ripetono uguali su ogni gruppo: il nome accessibile dice quale, e comincia
          con la parola che si vede, cosi' chi lo pronuncia a voce lo trova. */}
      {!aperta && (
        <Bottone piccolo nome={t("review.rigless.changeFor", { gruppo: nome })} onClick={() => setAperta(true)}>
          {t("review.rigless.change")}
        </Bottone>
      )}
      {aperta && !aMano && (
        <>
          <Campo id={`${id}-corredo`} etichetta={t("review.rigless.rig", { gruppo: nome })}>
          <select
            className="as-scelta"
            id={`${id}-corredo`}
            value={inTendina}
            onChange={(e) => {
              setScelta(e.target.value)
              const scelto = corredi.find((c) => c.id === Number(e.target.value))
              onRisposta(
                gruppo.key,
                scelto && !uguale(scelto, data) ? { key: gruppo.key, rig_id: scelto.id } : null,
              )
            }}
          >
            <option value="">--</option>
            {corredi.map((c) => (
              <option key={c.id} value={c.id}>
                {descrizione(c)}
              </option>
            ))}
          </select>
          </Campo>{" "}
          <Bottone
              piccolo nome={t("review.rigless.byHandFor", { gruppo: nome })}
              onClick={() => {              setAMano(true)
              setScelta("")
              onRisposta(gruppo.key, null)}}
            >
            {t("review.rigless.byHand")}
          </Bottone>
        </>
      )}
      {aperta && aMano && (
        <AMano gruppo={gruppo} id={id} onRisposta={onRisposta} />
      )}
    </Riga>
  )
}

/** I pezzi scritti a mano. I campi sono loro e non dell'accumulatore: la risposta si ricompone a
 *  ogni tasto da tutti e tre, e parte solo quando c'e' una camera con una focale. */
function AMano({
  gruppo,
  id,
  onRisposta,
}: {
  gruppo: Gruppo
  id: string
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const proposta = gruppo.focal_mm ?? gruppo.focal_suggested
  const [campi, setCampi] = useState({
    ottica: gruppo.optics ?? "",
    camera: "",
    focale: proposta === null ? "" : String(proposta),
  })

  const scrivi = (campo: keyof typeof campi, valore: string) => {
    const dopo = { ...campi, [campo]: valore }
    setCampi(dopo)
    const camera = testo(dopo.camera)
    const focale = misura(dopo.focale, false)
    const ottica = testo(dopo.ottica)
    const scritta = { optics: ottica ?? null, camera: camera ?? "", focal_mm: focale ?? null }
    onRisposta(
      gruppo.key,
      camera && focale && !uguale(scritta, gruppo.answer)
        ? { key: gruppo.key, ...(ottica ? { optics: ottica } : {}), camera, focal_mm: focale }
        : null,
    )
  }

  return (
    <fieldset>
      <legend>{t("review.rigless.pieces", { gruppo: nomeDellaCamera(gruppo) })}</legend>
      <Campo id={`${id}-ottica`} etichetta={t("review.rigless.optics")}>
          <input
          className="as-campo__input"
          id={`${id}-ottica`}
          value={campi.ottica}
          onChange={(e) => scrivi("ottica", e.target.value)}
        />
      </Campo>
      <Campo id={`${id}-camera`} etichetta={t("review.rigless.camera")}>
          <input
          className="as-campo__input"
          id={`${id}-camera`}
          value={campi.camera}
          onChange={(e) => scrivi("camera", e.target.value)}
        />
      </Campo>
      <Campo id={`${id}-focale`} etichetta={t("review.rigless.focal")}>
          <input
          className="as-campo__input"
          id={`${id}-focale`}
          type="number"
          min={0}
          step="any"
          value={campi.focale}
          onChange={(e) => scrivi("focale", e.target.value)}
        />
      </Campo>
    </fieldset>
  )
}

/** Il gruppo come si legge: la notte, poi il telescopio, il sensore e il pixel quando i file li
 *  dicono -- tutti i valori della chiave, o due gruppi avrebbero lo stesso nome. */
function nomeDellaCamera(g: Gruppo) {
  const sensore = g.width_px !== null && g.height_px !== null
    ? t("review.rigless.sensor", { larghezza: g.width_px, altezza: g.height_px })
    : null
  const pixel = g.pixel_um === null ? null : t("review.rigless.pixel", { micron: numero(g.pixel_um) })
  return nomeDelGruppo(g.night, [g.telescope, sensore, pixel])
}

/** Un corredo come si sceglie: il nome se l'utente gliel'ha dato, e sempre i pezzi con la focale. */
function descrizione(c: Corredo) {
  const pezzi = conFocale(pezziDelCorredo(c), c.focal_mm)
  return c.name ? `${c.name} (${pezzi})` : pezzi
}

/** Se una scelta e' la risposta gia' data: stessi pezzi, stessa focale. Ridarla non si manda --
 *  rimetterebbe in coda tutte le pose del gruppo per non cambiarne nessuna -- ed e' la stessa
 *  regola della risposta sul filtro. */
function uguale(
  scelta: Pick<Corredo, "optics" | "camera" | "focal_mm">,
  data: Gruppo["answer"],
) {
  return (
    data !== null &&
    scelta.optics === data.optics &&
    scelta.camera === data.camera &&
    scelta.focal_mm === data.focal_mm
  )
}

/** I pezzi con la focale, **solo se si sa**: un corredo a focale ignota non e' a "? mm". */
function conFocale(pezzi: string, focale: number | null) {
  return focale === null ? pezzi : `${pezzi}, ${t("review.rigless.focalMm", { mm: numero(focale) })}`
}

/** I pezzi di un corredo come si leggono: `ottica + camera`, senza il buco di quello che manca. */
function pezziDelCorredo(corredo: Pick<Corredo, "optics" | "camera">) {
  return [corredo.optics, corredo.camera].filter(Boolean).join(" + ")
}
