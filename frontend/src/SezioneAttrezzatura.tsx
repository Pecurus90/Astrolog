import { type ReactNode, useState } from "react"

import { Campo } from "./Campo"
import { Domanda, Risposta as Stato } from "./Domanda"
import { Scelte } from "./Scelte"
import { Sezione } from "./Sezione"
import { provaDeiSoggetti } from "./Soggetti"
import { TendinaDiScelta } from "./TendinaDiScelta"
import type { components } from "./api/schema"
import { type Chiave, numero, t } from "./i18n"

type Scheda = components["schemas"]["GearSignature"]
type Risposta = components["schemas"]["GearEdit"]
type Corredo = components["schemas"]["RigChoice"]
type Mio = components["schemas"]["FilterCandidate"]

// La scelta che apre i campi da scrivere, nella camera e nell'ottica.
const ALTRA = "altra"
const PARTI = { camera: "review.gear.camera", ottica: "review.gear.optics", filtro: "review.gear.filter" } as const
type Parte = keyof typeof PARTI

/** Cio' che l'utente ha scelto o scritto sulla scheda, parte per parte. */
type Mano = {
  camera: string | null
  nome: string
  focale: string
  conOttica: string
  ottica: string | null
  altraOttica: string
  filtro: Risposta["filter"]
  quale: number | undefined
}

/**
 * **L'attrezzatura da completare** (ADR 0014, S1): una scheda per gruppo di file che scrivono le
 * stesse intestazioni, quando non dicono la camera, l'ottica o il filtro.
 *
 * - **Chiede solo le parti che mancano**, e si risponde una alla volta: una parte non toccata non
 *   si manda, e la sua risposta di prima resta.
 * - **La camera e' un corredo dell'elenco oppure scritta a mano con la sua focale**: le due
 *   insieme il backend le rifiuta. Scritta a mano porta l'ottica, se serve.
 * - **L'ottica da sola si chiede solo quando la camera c'e'**, nei file o salvata: altrimenti la
 *   porta il corredo, o il campo accanto alla camera. Una camera cambiata porta la sua ottica e
 *   quella scelta a parte non parte; rimessa com'era salvata non e' un cambio, e l'ottica parte.
 * - **"A colori, senza filtro" si scrive sulla scheda della camera**: si sceglie quando la camera
 *   si sa, e non si manda se la camera torna a mancare.
 * - **Una scheda risposta resta in pagina**; conta fra le cose da confermare finche' non ha tutte
 *   le parti che chiede.
 */
export function SezioneAttrezzatura({
  schede,
  corredi,
  ottiche,
  filtri,
  risposte,
  onRisposta,
}: {
  schede: Scheda[]
  corredi: Corredo[]
  ottiche: string[]
  filtri: Mio[]
  risposte: Record<string, Risposta>
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  return (
    <Sezione
      quale="gear"
      domanda={t("review.gear.why")}
      voci={schede}
      chiave={(s) => s.key}
      riga={(s, indice) => (
        <RigaAttrezzatura
          corredi={corredi}
          filtri={filtri}
          indice={indice}
          ottiche={ottiche}
          risposta={risposte[s.key]}
          scheda={s}
          onRisposta={onRisposta}
        />
      )}
    />
  )
}

/** L'ottica ha la sua parte: un corredo senza ottica, salvato, lascia la scheda a meta'. */
const otticaDaSola = (s: Scheda) => s.asks_optics && (!s.asks_camera || Boolean(s.answer?.camera))

const corredoDi = (c: Corredo) => [c.optics, c.camera].filter(Boolean).join(" \u00b7 ")

/** Da dove si parte: dalla risposta in mano, se c'e' (la sezione si rimonta), poi dalla salvata. */
function partenza(scheda: Scheda, risposta: Risposta | undefined, corredi: Corredo[]): Mano {
  const data = scheda.answer
  // la focale conta: la stessa ottica con e senza riduttore sono due corredi
  const salvato = corredi.find(
    (c) =>
      c.camera === data?.camera &&
      (c.optics ?? null) === (data?.optics ?? null) &&
      (c.focal_mm ?? null) === (data?.focal_mm ?? null),
  )
  return {
    camera: risposta?.rig_id ? `${risposta.rig_id}` : risposta?.camera ? ALTRA : salvato ? `${salvato.id}` : data?.camera ? ALTRA : null,
    nome: risposta?.camera ?? (salvato ? "" : (data?.camera ?? "")),
    focale: `${risposta?.focal_mm ?? data?.focal_mm ?? scheda.focal_mm ?? scheda.focal_suggested ?? ""}`,
    // una camera scritta in mano porta la sua ottica, anche vuota
    conOttica: scheda.asks_camera && risposta?.camera ? (risposta.optics ?? "") : (data?.optics ?? scheda.optics ?? ""),
    ottica: null,
    altraOttica: "",
    filtro: risposta?.filter ?? data?.filter ?? null,
    quale: risposta?.filter_id ?? data?.filter_id ?? undefined,
  }
}

function RigaAttrezzatura({
  scheda,
  indice,
  corredi,
  ottiche,
  filtri,
  risposta,
  onRisposta,
}: {
  scheda: Scheda
  indice: number
  corredi: Corredo[]
  ottiche: string[]
  filtri: Mio[]
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  // Con la camera in mano l'ottica della risposta e' la sua, non quella della parte Ottica.
  const cameraInMano = Boolean(risposta?.rig_id || risposta?.camera)
  const [mano, setMano] = useState<Mano>(() => {
    const inizio = partenza(scheda, risposta, corredi)
    const salvata = scheda.answer?.optics ?? null
    // l'ottica da sola: una delle proprie, o scritta
    const mia = (cameraInMano ? null : risposta?.optics) ?? salvata
    return !otticaDaSola(scheda)
      ? inizio
      : { ...inizio, ottica: mia === null ? null : ottiche.includes(mia) ? mia : ALTRA, altraOttica: mia !== null && !ottiche.includes(mia) ? mia : "" }
  })
  // Le parti toccate adesso: solo quelle entrano nella risposta, le altre tengono la loro.
  const [toccate, setToccate] = useState<readonly Parte[]>(() => [
    ...(risposta?.rig_id || risposta?.camera ? ["camera" as const] : []),
    ...(otticaDaSola(scheda) && !cameraInMano && risposta?.optics ? ["ottica" as const] : []),
    ...(risposta?.filter ? ["filtro" as const] : []),
  ])

  const sensore =
    scheda.width_px !== null && scheda.height_px !== null
      ? [`${numero(scheda.width_px)} \u00d7 ${numero(scheda.height_px)} px`, scheda.pixel_um !== null && `${numero(scheda.pixel_um)} \u00b5m`]
          .filter(Boolean)
          .join(" \u00b7 ")
      : null
  const titolo = scheda.camera ?? scheda.telescope ?? sensore ?? t("review.gear.unnamed")

  // Ogni parte, come risposta da mandare: `null` se non e' ancora una risposta.
  const diCamera = (m: Mano): Partial<Risposta> | null => {
    if (m.camera === null) return null
    if (m.camera !== ALTRA) return { rig_id: Number(m.camera) }
    const focale = Number(m.focale.replace(",", "."))
    // una camera senza la sua focale il backend la rifiuta, e con lei tutto l'Applica
    if (m.nome.trim() === "" || !Number.isFinite(focale) || focale <= 0) return null
    return { camera: m.nome.trim(), focal_mm: focale, ...(m.conOttica.trim() ? { optics: m.conOttica.trim() } : {}) }
  }
  const diOttica = (m: Mano): Partial<Risposta> | null => {
    const nome = m.ottica === ALTRA ? m.altraOttica.trim() : (m.ottica ?? "")
    return nome ? { optics: nome } : null
  }
  const diFiltro = (m: Mano, cameraNota: boolean): Partial<Risposta> | null => {
    // a colori senza camera il backend lo rifiuta, e con lui tutto l'Applica
    if (!m.filtro || (m.filtro === "color" && !cameraNota)) return null
    if (m.filtro !== "filter") return { filter: m.filtro }
    // un filtro esistente senza dire quale non e' una risposta
    return m.quale === undefined ? null : { filter: "filter", filter_id: m.quale }
  }
  // La camera rimessa com'era salvata non e' un cambio: rimandata, scarterebbe l'ottica accanto.
  const prima = partenza(scheda, undefined, corredi)
  const comeSalvata = (m: Mano) =>
    prima.camera !== null &&
    m.camera === prima.camera &&
    (m.camera !== ALTRA || (m.nome.trim() === prima.nome && m.focale === prima.focale && m.conOttica.trim() === prima.conOttica))
  const pezzi = (m: Mano, quali: readonly Parte[]) => {
    const camera = quali.includes("camera") && !comeSalvata(m) ? diCamera(m) : null
    // La camera si sa se i file la dicono, se e' salvata, o se e' appena stata data.
    const cameraNota = !scheda.asks_camera || Boolean(scheda.answer?.camera) || camera !== null
    return {
      camera,
      // una camera ridata porta la sua ottica: un corredo e un'ottica scritta insieme sono un 422
      ottica: quali.includes("ottica") && camera === null ? diOttica(m) : null,
      filtro: quali.includes("filtro") ? diFiltro(m, cameraNota) : null,
      cameraNota,
    }
  }

  const cambia = (parte: Parte, nuovo: Partial<Mano>) => {
    const dopo = { ...mano, ...nuovo }
    const quali = toccate.includes(parte) ? toccate : [...toccate, parte]
    setMano(dopo)
    setToccate(quali)
    const p = pezzi(dopo, quali)
    const tutto = { ...p.camera, ...p.ottica, ...p.filtro }
    onRisposta(scheda.key, Object.keys(tutto).length > 0 ? { key: scheda.key, ...tutto } : null)
  }

  const inMano = pezzi(mano, toccate)
  const data = scheda.answer
  const { cameraNota } = inMano
  const scelto = corredi.find((c) => `${c.id}` === mano.camera)
  const filtroDetto = (parola: Risposta["filter"], quale: number | null | undefined) =>
    parola === "filter" ? (filtri.find((f) => f.id === quale)?.name ?? "") : parola ? t(FILTRI[parola]) : ""

  // Le parti che la scheda chiede, con cio' che si legge di ognuna da chiusa.
  const chieste: { parte: Parte; salvata: boolean; inMano: boolean; detto: string }[] = [
    ...(scheda.asks_camera
      ? [{ parte: "camera" as const, salvata: Boolean(data?.camera), inMano: inMano.camera !== null, detto: inMano.camera ? (scelto?.camera ?? mano.nome.trim()) : (data?.camera ?? "") }]
      : []),
    ...(otticaDaSola(scheda)
      ? [{ parte: "ottica" as const, salvata: Boolean(data?.optics), inMano: inMano.ottica !== null, detto: inMano.ottica?.optics ?? data?.optics ?? "" }]
      : []),
    ...(scheda.asks_filter
      ? [{ parte: "filtro" as const, salvata: Boolean(data?.filter), inMano: inMano.filtro !== null, detto: inMano.filtro ? filtroDetto(mano.filtro, mano.quale) : filtroDetto(data?.filter ?? null, data?.filter_id) }]
      : []),
  ]
  const chiesta = (parte: Parte) => chieste.find((c) => c.parte === parte)
  const capo = (parte: Parte) => {
    const c = chiesta(parte)
    return (
      <p className="as-domanda-parte__capo">
        <span className="as-soprattitolo as-soprattitolo--nudo">{t(PARTI[parte])}</span>
        <Stato inMano={c?.inMano ?? false} salvata={c?.salvata ?? false} />
      </p>
    )
  }
  const parte = (quale: Parte, corpo: ReactNode) => chiesta(quale) && (
    <div className="as-domanda-parte">
      {capo(quale)}
      {corpo}
    </div>
  )
  const id = (cosa: string) => `attrezzatura-${cosa}-${indice}`

  return (
    <Domanda
      id={`gear:${scheda.key}`}
      voce={titolo}
      nome={titolo}
      cifre
      frames={scheda.frames}
      salvata={scheda.complete}
      inMano={chieste.some((c) => c.inMano)}
      breve={chieste
        .map((c) => `${t(PARTI[c.parte])}: ${c.inMano || c.salvata ? c.detto : t("review.gear.toGive")}`)
        .join(" \u00b7 ")}
      prova={[
        { nome: t("review.proof.fileCamera"), dato: scheda.camera ?? t("review.unknown.f") },
        { nome: t("review.proof.fileTelescope"), dato: scheda.telescope ?? t("review.unknown.m") },
        ...(sensore ? [{ nome: t("review.proof.sensor"), dato: sensore }] : []),
        {
          nome: t("review.proof.frameOptics"),
          dato:
            [scheda.optics, scheda.focal_mm !== null && `${numero(scheda.focal_mm)} mm`].filter(Boolean).join(" \u00b7 ") ||
            t("review.unknown.f"),
        },
        ...provaDeiSoggetti(scheda.subjects),
      ]}
    >
      <div className="as-domanda-parti">
        {parte(
          "camera",
          <Scelte
            domanda={t("review.gear.camera.question", { nome: titolo })}
            nome={id("camera")}
            opzioni={[
              ...corredi.map((c) =>
                c.name ? { valore: `${c.id}`, etichetta: c.name, sub: corredoDi(c) } : { valore: `${c.id}`, etichetta: corredoDi(c) },
              ),
              { valore: ALTRA, etichetta: t("review.gear.camera.other") },
            ]}
            scelta={mano.camera}
            onScelta={(camera) => cambia("camera", { camera })}
          >
            {mano.camera === ALTRA && (
              <div className="as-modulo">
                <Campo id={id("nome")} etichetta={t("review.gear.camera")}>
                  <input className="as-campo-modulo__input" id={id("nome")} value={mano.nome} onChange={(e) => cambia("camera", { nome: e.target.value })} />
                </Campo>
                <Campo id={id("focale")} etichetta={t("review.gear.focal")}>
                  <input
                    className="as-campo-modulo__input as-campo-modulo__input--cifre"
                    id={id("focale")}
                    inputMode="decimal"
                    value={mano.focale}
                    onChange={(e) => cambia("camera", { focale: e.target.value })}
                  />
                </Campo>
                <Campo id={id("con-ottica")} etichetta={t("review.gear.optics")}>
                  <input className="as-campo-modulo__input" id={id("con-ottica")} value={mano.conOttica} onChange={(e) => cambia("camera", { conOttica: e.target.value })} />
                  {!scheda.asks_optics && <p className="as-campo-modulo__aiuto">{t("review.gear.optics.optional")}</p>}
                </Campo>
              </div>
            )}
          </Scelte>,
        )}
        {parte(
          "ottica",
          <Scelte
            domanda={t("review.gear.optics.question", { nome: titolo })}
            nome={id("ottica")}
            opzioni={[...ottiche.map((o) => ({ valore: o, etichetta: o })), { valore: ALTRA, etichetta: t("review.gear.optics.other") }]}
            scelta={mano.ottica}
            onScelta={(ottica) => cambia("ottica", { ottica })}
          >
            {mano.ottica === ALTRA && (
              <Campo id={id("altra-ottica")} etichetta={t("review.gear.optics.name")}>
                <input
                  className="as-campo-modulo__input"
                  id={id("altra-ottica")}
                  value={mano.altraOttica}
                  onChange={(e) => cambia("ottica", { altraOttica: e.target.value })}
                />
              </Campo>
            )}
          </Scelte>,
        )}
        {parte(
          "filtro",
          <Scelte
            domanda={t("review.gear.filter.question", { nome: titolo })}
            nome={id("filtro")}
            opzioni={(Object.keys(FILTRI) as (keyof typeof FILTRI)[]).map((valore) => ({
              valore,
              etichetta: t(FILTRI[valore]),
              // si scrive sulla scheda della camera: prima serve sapere qual e'
              spenta: valore === "color" && !cameraNota,
            }))}
            scelta={mano.filtro}
            onScelta={(filtro) => cambia("filtro", { filtro })}
          >
            {(!cameraNota || mano.filtro === "filter") && (
              <>
                {!cameraNota && <p className="as-campo-modulo__aiuto">{t("review.gear.filter.colorLater")}</p>}
                {mano.filtro === "filter" && (
                  <TendinaDiScelta
                    id={id("quale-filtro")}
                    etichetta={t("review.gear.filter")}
                    altri={filtri}
                    valore={mano.quale}
                    onScelta={(quale) => cambia("filtro", { quale })}
                  />
                )}
              </>
            )}
          </Scelte>,
        )}
      </div>
    </Domanda>
  )
}

/** Cosa c'era davanti, sul tipo generato: una risposta nuova non compila finche' non ha un nome. */
const FILTRI: Record<NonNullable<Risposta["filter"]>, Chiave> = {
  color: "review.gear.filter.color",
  no_filter: "review.gear.filter.none",
  filter: "review.gear.filter.mine",
}
