import { useState } from "react"

import { type StatoParte, statoDi } from "./ConfermareGuscio"
import {
  Campi,
  type CampoConf,
  Domanda,
  Nota,
  Parte,
  Risposte,
  Sotto,
  rigaDeiFrame,
  sensore,
  voce,
} from "./Domanda"
import { Sezione } from "./Sezione"
import { provaDeiSoggetti } from "./Soggetti"
import type { components } from "./api/schema"
import { type Chiave, numero, numeroNelCampo, t } from "./i18n"

const campoDa = (n: number | null | undefined) => (n == null ? "" : numeroNelCampo(n))

type Scheda = components["schemas"]["GearSignature"]
type Risposta = components["schemas"]["GearEdit"]
type Corredo = components["schemas"]["RigChoice"]
type Mio = components["schemas"]["FilterCandidate"]

// La scelta che apre i campi da scrivere, nella camera e nell'ottica.
const ALTRA = "altra"
const PARTI = {
  camera: "review.gear.camera.question",
  ottica: "review.gear.optics.question",
  filtro: "review.gear.filter.question",
} as const satisfies Record<string, Chiave>
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
 * **L'attrezzatura da completare** (ADR 0014, S1; tavola v82, 200-209): una scheda per gruppo di
 * file che scrivono le stesse intestazioni, quando non dicono la camera, l'ottica o il filtro.
 *
 * - **Chiede solo le parti che mancano**, una alla volta: una parte non toccata non si manda, e la
 *   sua risposta di prima resta.
 * - **La camera e' un setup dell'elenco oppure scritta con la sua focale**. Con l'ottica data a
 *   parte nello stesso Applica, il setup parte **per pezzi scritti** (camera, focale, ottica): un
 *   setup dell'elenco e un'ottica insieme il backend li rifiuta (Issue #20).
 * - **Il filtro si sceglie quando la camera si sa**: "a colori" si scrive sulla sua scheda.
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

const corredoDi = (c: Corredo) => [c.optics, c.camera].filter(Boolean).join(" \u00b7 ")

/** Da dove si parte: dalla risposta in mano, se c'e' (la sezione si rimonta), poi dalla salvata. */
function partenza(
  scheda: Scheda,
  risposta: Risposta | undefined,
  corredi: Corredo[],
  ottiche: string[],
): Mano {
  const data = scheda.answer
  // la focale conta: la stessa ottica con e senza riduttore sono due setup
  const salvato = corredi.find(
    (c) =>
      c.camera === data?.camera &&
      (c.optics ?? null) === (data?.optics ?? null) &&
      (c.focal_mm ?? null) === (data?.focal_mm ?? null),
  )
  const scritta = risposta?.camera !== undefined && risposta.camera !== null
  // l'ottica della parte sua: in mano, poi salvata
  const mia = (scheda.asks_optics ? risposta?.optics : null) ?? data?.optics ?? null
  return {
    camera: risposta?.rig_id
      ? `${risposta.rig_id}`
      : scritta
        ? ALTRA
        : salvato
          ? `${salvato.id}`
          : data?.camera
            ? ALTRA
            : null,
    nome: risposta?.camera ?? (salvato ? "" : (data?.camera ?? "")),
    focale: campoDa(
      risposta?.focal_mm ?? data?.focal_mm ?? scheda.focal_mm ?? scheda.focal_suggested,
    ),
    conOttica: scheda.asks_optics ? "" : (risposta?.optics ?? data?.optics ?? scheda.optics ?? ""),
    ottica: !scheda.asks_optics || mia === null ? null : ottiche.includes(mia) ? mia : ALTRA,
    altraOttica: mia !== null && !ottiche.includes(mia) ? mia : "",
    filtro: risposta?.filter ?? data?.filter ?? null,
    quale: risposta?.filter_id ?? data?.filter_id ?? undefined,
  }
}

/** Le parti toccate di una risposta in mano: solo quelle ripartono, le altre tengono la loro. */
function toccateDi(scheda: Scheda, risposta: Risposta | undefined): Parte[] {
  if (!risposta) return []
  const camera = Boolean(risposta.rig_id || risposta.camera)
  return [
    ...(camera ? ["camera" as const] : []),
    ...(scheda.asks_optics && risposta.optics ? ["ottica" as const] : []),
    ...(risposta.filter ? ["filtro" as const] : []),
  ]
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
  const [mano, setMano] = useState<Mano>(() => partenza(scheda, risposta, corredi, ottiche))
  const [toccate, setToccate] = useState<readonly Parte[]>(() => toccateDi(scheda, risposta))
  const sens = sensore(scheda.width_px, scheda.height_px, scheda.pixel_um)
  const titolo = scheda.camera ?? scheda.telescope ?? sens ?? t("review.gear.unnamed")

  // Ogni parte, come risposta da mandare: `null` se non e' ancora una risposta.
  const diCamera = (m: Mano): Partial<Risposta> | null => {
    if (m.camera === null) return null
    if (m.camera !== ALTRA) return { rig_id: Number(m.camera) }
    const focale = Number(m.focale.replace(",", "."))
    // una camera senza la sua focale il backend la rifiuta, e con lei tutto l'Applica
    if (m.nome.trim() === "" || !Number.isFinite(focale) || focale <= 0) return null
    return {
      camera: m.nome.trim(),
      focal_mm: focale,
      ...(m.conOttica.trim() ? { optics: m.conOttica.trim() } : {}),
    }
  }
  const diOttica = (m: Mano): string | null => {
    const nome = m.ottica === ALTRA ? m.altraOttica.trim() : (m.ottica ?? "")
    return nome || null
  }
  const diFiltro = (m: Mano): Partial<Risposta> | null => {
    if (!m.filtro) return null
    if (m.filtro !== "filter") return { filter: m.filtro }
    // un filtro esistente senza dire quale non e' una risposta
    return m.quale === undefined ? null : { filter: "filter", filter_id: m.quale }
  }
  // La camera rimessa com'era salvata non e' un cambio.
  const prima = partenza(scheda, undefined, corredi, ottiche)
  const comeSalvata = (m: Mano) =>
    prima.camera !== null &&
    m.camera === prima.camera &&
    (m.camera !== ALTRA ||
      (m.nome.trim() === prima.nome &&
        m.focale === prima.focale &&
        m.conOttica.trim() === prima.conOttica))
  /** Camera e ottica insieme: un setup dell'elenco parte per pezzi scritti, l'ottica dentro. */
  const insieme = (camera: Partial<Risposta>, ottica: string): Partial<Risposta> => {
    if (!camera.rig_id) return { ...camera, optics: ottica }
    const setup = corredi.find((c) => c.id === camera.rig_id)
    // senza focale il setup non si scrive per pezzi: parte da solo, con la sua ottica
    return setup?.focal_mm != null
      ? { camera: setup.camera, focal_mm: setup.focal_mm, optics: ottica }
      : camera
  }
  const pezzi = (m: Mano, quali: readonly Parte[]) => {
    const camera = quali.includes("camera") && !comeSalvata(m) ? diCamera(m) : null
    const ottica = quali.includes("ottica") ? diOttica(m) : null
    // La camera si sa se i file la dicono, se e' salvata, o se e' appena stata data.
    const cameraNota = !scheda.asks_camera || Boolean(scheda.answer?.camera) || camera !== null
    const filtro = quali.includes("filtro") && cameraNota ? diFiltro(m) : null
    const montate =
      camera && ottica ? insieme(camera, ottica) : (camera ?? (ottica ? { optics: ottica } : null))
    // un setup senza focale non porta l'ottica scelta: la parte resta da dare, e lo dice
    const parte = camera && ottica && !montate?.optics ? null : ottica
    return { camera, ottica: parte, filtro, montate, cameraNota }
  }

  const cambia = (parte: Parte, nuovo: Partial<Mano>) => {
    const dopo = { ...mano, ...nuovo }
    const quali = toccate.includes(parte) ? toccate : [...toccate, parte]
    setMano(dopo)
    setToccate(quali)
    const p = pezzi(dopo, quali)
    const tutto = { ...p.montate, ...p.filtro }
    onRisposta(scheda.key, Object.keys(tutto).length > 0 ? { key: scheda.key, ...tutto } : null)
  }

  const inMano = pezzi(mano, toccate)
  const data = scheda.answer
  const scelto = corredi.find((c) => `${c.id}` === mano.camera)
  const filtroDetto = (parola: Risposta["filter"], quale: number | null | undefined) =>
    parola === "filter"
      ? t("review.filters.mine", { nome: filtri.find((f) => f.id === quale)?.name ?? "" })
      : parola
        ? t(FILTRI[parola])
        : ""

  // Le parti che la scheda chiede, con cio' che si legge di ognuna.
  const chieste: { parte: Parte; salvata: boolean; inMano: boolean; detto: string }[] = [
    ...(scheda.asks_camera
      ? [
          {
            parte: "camera" as const,
            salvata: Boolean(data?.camera),
            inMano: inMano.camera !== null,
            detto: inMano.camera
              ? (scelto?.name ?? scelto?.camera ?? mano.nome.trim())
              : (data?.camera ?? ""),
          },
        ]
      : []),
    ...(scheda.asks_optics
      ? [
          {
            parte: "ottica" as const,
            salvata: Boolean(data?.optics),
            inMano: inMano.ottica !== null,
            detto: inMano.ottica ?? data?.optics ?? "",
          },
        ]
      : []),
    ...(scheda.asks_filter
      ? [
          {
            parte: "filtro" as const,
            salvata: Boolean(data?.filter),
            inMano: inMano.filtro !== null,
            detto: inMano.filtro
              ? filtroDetto(mano.filtro, mano.quale)
              : filtroDetto(data?.filter ?? null, data?.filter_id),
          },
        ]
      : []),
  ]
  const tutte = chieste.every((c) => c.salvata || c.inMano)
  const statoDellaParte = (c: (typeof chieste)[number]): StatoParte =>
    c.inMano ? "ora" : c.salvata ? "salvata" : "indicare"
  const capo = (p: Parte) => t(PARTI[p], { nome: titolo })
  const id = (cosa: string) => `attrezzatura-${cosa}-${indice}`

  const corpo = (p: Parte) => {
    if (p === "camera") {
      const campi: CampoConf[] = [
        {
          id: id("nome"),
          etichetta: t("review.gear.camera"),
          valore: mano.nome,
          onValore: (nome) => cambia("camera", { nome }),
        },
        {
          id: id("focale"),
          etichetta: t("review.gear.focal"),
          valore: mano.focale,
          onValore: (focale) => cambia("camera", { focale }),
          numerico: true,
          ...(scheda.focal_suggested !== null && scheda.optics
            ? { aiuto: t("review.gear.focal.proposed", { ottica: scheda.optics }) }
            : {}),
        },
        // con la parte Ottica accanto, l'ottica si dice li': due campi per la stessa cosa no
        ...(scheda.asks_optics
          ? []
          : [
              {
                id: id("con-ottica"),
                etichetta: t("review.gear.optics"),
                valore: mano.conOttica,
                onValore: (conOttica: string) => cambia("camera", { conOttica }),
                aiuto: t("review.gear.optics.optional"),
              },
            ]),
      ]
      return (
        <>
          <Risposte
            etichetta={capo(p)}
            opzioni={[
              ...corredi.map((c) =>
                voce(
                  mano.camera === `${c.id}`,
                  c.name ?? corredoDi(c),
                  () => cambia("camera", { camera: `${c.id}` }),
                  c.name ? corredoDi(c) : undefined,
                ),
              ),
              voce(mano.camera === ALTRA, t("review.gear.camera.other"), () =>
                cambia("camera", { camera: ALTRA }),
              ),
            ]}
          />
          {mano.camera === ALTRA && <Campi campi={campi} />}
        </>
      )
    }
    if (p === "ottica") {
      return (
        <>
          <Risposte
            etichetta={capo(p)}
            opzioni={[
              ...ottiche.map((o) =>
                voce(mano.ottica === o, o, () => cambia("ottica", { ottica: o })),
              ),
              voce(mano.ottica === ALTRA, t("review.gear.optics.other"), () =>
                cambia("ottica", { ottica: ALTRA }),
              ),
            ]}
          />
          {mano.ottica === ALTRA && (
            <Campi
              campi={[
                {
                  id: id("altra-ottica"),
                  etichetta: t("review.gear.optics.name"),
                  valore: mano.altraOttica,
                  onValore: (altraOttica) => cambia("ottica", { altraOttica }),
                },
              ]}
            />
          )}
        </>
      )
    }
    const spento = !inMano.cameraNota
    return (
      <>
        <Risposte
          etichetta={capo(p)}
          opzioni={(Object.keys(FILTRI) as (keyof typeof FILTRI)[]).map((valore) =>
            voce(
              mano.filtro === valore,
              t(FILTRI[valore]),
              () => cambia("filtro", { filtro: valore }),
              undefined,
              spento,
            ),
          )}
        />
        {spento && <Nota>{t("review.gear.filter.colorLater")}</Nota>}
        {!spento && mano.filtro === "filter" && (
          <Sotto
            etichetta={t("review.gear.filter.mine")}
            opzioni={filtri.map((f) =>
              voce(mano.quale === f.id, f.name, () => cambia("filtro", { quale: f.id })),
            )}
          />
        )}
      </>
    )
  }

  return (
    <Domanda
      id={`gear:${scheda.key}`}
      voce={titolo}
      nome={titolo}
      frame={rigaDeiFrame(scheda.frames)}
      stato={statoDi(
        scheda.complete,
        chieste.some((c) => c.inMano),
      )}
      detta={tutte}
      breve={
        tutte
          ? chieste.map((c) => c.detto).join(" \u00b7 ")
          : chieste
              .map(
                (c) =>
                  `${capo(c.parte)}: ${c.inMano || c.salvata ? c.detto : t("review.gear.toGive")}`,
              )
              .join(" \u00b7 ")
      }
      prova={[
        {
          nome: t("review.proof.fileCamera"),
          righe: [scheda.camera ?? t("review.unknown.f")],
          tenue: scheda.camera === null,
        },
        {
          nome: t("review.proof.fileTelescope"),
          righe: [scheda.telescope ?? t("review.unknown.m")],
          tenue: scheda.telescope === null,
        },
        ...(sens ? [{ nome: t("review.proof.sensor"), righe: [sens] }] : []),
        {
          nome: t("review.proof.frameOptics"),
          righe: [
            [scheda.optics, scheda.focal_mm !== null && `${numero(scheda.focal_mm)} mm`]
              .filter(Boolean)
              .join(" \u00b7 ") || t("review.unknown.f"),
          ],
          tenue: scheda.optics === null && scheda.focal_mm === null,
        },
        ...provaDeiSoggetti(scheda.subjects),
      ]}
    >
      {chieste.map((c, i) => (
        <Parte key={c.parte} capo={capo(c.parte)} prima={i === 0} stato={statoDellaParte(c)}>
          {corpo(c.parte)}
        </Parte>
      ))}
    </Domanda>
  )
}

/** Cosa c'era davanti, sul tipo generato: una risposta nuova non compila finche' non ha un nome. */
const FILTRI: Record<NonNullable<Risposta["filter"]>, Chiave> = {
  color: "review.gear.filter.color",
  no_filter: "review.gear.filter.none",
  filter: "review.gear.filter.mine",
}
