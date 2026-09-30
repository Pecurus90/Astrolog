import { useState } from "react"

import { Bottone } from "./Bottone"
import { CorreggiIlFiltro, CorreggiIlPezzo, MontaturaDelCorredo, NomeDelCorredo } from "./CorreggiLeRighe"
import { Dettaglio, Riga } from "./Riga"
import { TempoDellePose } from "./TempoDellePose"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Pezzo = components["schemas"]["InstrumentOnPage"]
type Corredo = components["schemas"]["RigOnPage"]
type Filtro = components["schemas"]["FilterOnPage"]
type Schede = components["schemas"]["GearList"]["cards"]

/**
 * Le **righe** dell'Attrezzatura: un pezzo, un corredo, un filtro.
 *
 * - **Qui non si calcola niente.** Ore, frame, notti, oggetti e la scala misurata arrivano gia'
 *   fatti dal backend, che sa quali pose escludere e in che ordine mettere le righe.
 * - **Cio' che l'app non sa non prende uno zero**: arrivano nulle le ore di una montatura, quelle
 *   di ogni genere che in questo archivio nessuna posa nomina, e la scala di un corredo che non
 *   ha ancora ripreso. La riga scrive **perche'** mancano, e chi decide e' il backend.
 */

/** Quanto un pezzo e' servito: le ore col pezzo di sempre, i frame, le notti. Dove il legame con
 *  le pose non esiste -- la montatura, o un genere che i tuoi file non nominano mai -- si scrive
 *  **perche'**, che e' un dato anche quello. */
function Uso({ pezzo }: { pezzo: Pezzo | Corredo | Filtro }) {
  // nato a meta' giro: i suoi numeri arrivano a fine giro, e non e' lo stesso di "non si sa"
  if (!pezzo.counted) return <Dettaglio>{t("gear.counting")}</Dettaglio>
  // il perche' lo decide il backend; corredi e filtri contati le ore le hanno sempre
  const perche = "no_hours" in pezzo ? pezzo.no_hours : null
  if (perche !== null || pezzo.frames === null || pezzo.integration_s === null) {
    return <Dettaglio>{t(perche === "no_rig" ? "gear.noHours.mount" : "gear.noHours")}</Dettaglio>
  }
  return (
    <>
      <Dettaglio>{t("gear.frames", { n: numero(pezzo.frames) })}</Dettaglio>{" "}
      <Dettaglio>
        <TempoDellePose secondi={pezzo.integration_s} senzaTempo={pezzo.untimed ?? 0} />
      </Dettaglio>{" "}
      {pezzo.nights !== null && pezzo.nights > 0 && (
        <Dettaglio>
          {t("gear.nights", { n: numero(pezzo.nights) })}
        </Dettaglio>
      )}
    </>
  )
}

/** Cosa hai ripreso con quel pezzo, dal piu' ripreso. Vuoto non si scrive: un pezzo senza ore
 *  non ha nemmeno oggetti, e una virgola sola sarebbe un dettaglio che non dice niente. */
function Ripreso({ oggetti }: { oggetti: Corredo["objects"] }) {
  if (oggetti.length === 0) return null
  return <Dettaglio>{oggetti.map((o) => o.name ?? o.key).join(", ")}</Dettaglio>
}

/** Le righe della scheda che **hanno un valore**: un campo vuoto non si scrive, o la scheda di
 *  chi non ha dichiarato niente sarebbe una griglia di trattini. */
function scheda(pezzo: Pezzo): string[] {
  const righe: string[] = []
  if (pezzo.aperture_mm !== null) righe.push(t("gear.aperture", { mm: numero(pezzo.aperture_mm) }))
  if (pezzo.focal_mm !== null) righe.push(t("gear.focalNative", { mm: numero(pezzo.focal_mm) }))
  if (pezzo.camera_type !== null) {
    righe.push(t(pezzo.camera_type === "mono" ? "gear.camera.mono" : "gear.camera.color"))
  }
  if (pezzo.pixel_size_um !== null) righe.push(t("gear.pixel", { um: numero(pezzo.pixel_size_um) }))
  // quello ricavato dal cielo solo dove i file e l'utente tacciono, e detto per quello che e'
  else if (pezzo.pixel_from_sky_um !== null) {
    righe.push(t("gear.pixelFromSky", { um: numero(pezzo.pixel_from_sky_um) }))
  }
  if (pezzo.payload_kg !== null) righe.push(t("gear.payload", { kg: numero(pezzo.payload_kg) }))
  if (pezzo.weight_kg !== null) righe.push(t("gear.weight", { kg: numero(pezzo.weight_kg) }))
  if (pezzo.slots !== null) righe.push(t("gear.slots", { n: numero(pezzo.slots) }))
  if (pezzo.reducer_factor !== null) {
    righe.push(t("gear.reducerFactor", { fattore: numero(pezzo.reducer_factor) }))
  }
  if (pezzo.backfocus_mm !== null) {
    righe.push(t("gear.backfocus", { mm: numero(pezzo.backfocus_mm) }))
  }
  return righe
}

export function UnPezzo({
  pezzo,
  campi,
  tutti,
}: {
  pezzo: Pezzo
  campi: Schede[Pezzo["kind"]]
  tutti: Pezzo[]
}) {
  const [correggo, setCorreggo] = useState(false)
  const marca = [pezzo.brand, pezzo.model].filter(Boolean).join(" ")
  return (
    <Riga
      nome={pezzo.name}
      dettagli={
        <>
          {marca && <Dettaglio>{marca}</Dettaglio>} <Uso pezzo={pezzo} />{" "}
          {scheda(pezzo).map((riga) => (
            <Dettaglio key={riga}>{riga}</Dettaglio>
          ))}{" "}
          <Ripreso oggetti={pezzo.objects} />{" "}
          {!pezzo.detected && <Dettaglio>{t("gear.declared")}</Dettaglio>}
        </>
      }
      perche={pezzo.notes ?? undefined}
      comparsa={
        correggo && (
          <CorreggiIlPezzo
            pezzo={pezzo}
            campi={campi}
            unibili={tutti.filter((o) => pezzo.mergeable_into.includes(o.id))}
            onChiudi={() => setCorreggo(false)}
          />
        )
      }
    >
      {/* Il bottone **sparisce** aprendo la scheda, quindi non e' un interruttore e non dichiara
          `aria-expanded`: direbbe `false` per sempre. Chi ascolta raggiunge la scheda perche' e'
          una regione col suo nome. */}
      {!correggo && (
        <Bottone piccolo onClick={() => setCorreggo(true)}>
          {t("gear.write.edit")}
        </Bottone>
      )}
    </Riga>
  )
}

export function UnCorredo({ corredo, montature }: { corredo: Corredo; montature: Pezzo[] }) {
  const [apro, setApro] = useState<"nome" | "montatura" | null>(null)
  const montata = montature.find((m) => m.id === corredo.mount_id)
  const fatto = t("gear.rig", {
    ottica: corredo.optics ?? t("gear.rig.noOptics"),
    camera: corredo.camera ?? t("gear.rig.noCamera"),
  })
  return (
    <Riga
      nome={corredo.name ?? fatto}
      dettagli={
        <>
          {corredo.name && <Dettaglio>{fatto}</Dettaglio>}{" "}
          {corredo.focal_mm !== null && (
            <Dettaglio>{t("gear.focal", { mm: numero(corredo.focal_mm) })}</Dettaglio>
          )}{" "}
          {montata && <Dettaglio>{t("gear.rig.mount", { nome: montata.name })}</Dettaglio>}{" "}
          <Uso pezzo={corredo} /> <Ripreso oggetti={corredo.objects} />{" "}
          <QuantoInquadra corredo={corredo} />
        </>
      }
      comparsa={
        (apro === "nome" && <NomeDelCorredo corredo={corredo} come={fatto} onChiudi={() => setApro(null)} />) ||
        (apro === "montatura" && (
          <MontaturaDelCorredo corredo={corredo} come={fatto} montature={montature} onChiudi={() => setApro(null)} />
        ))
      }
    >
      {apro === null && (
        <>
          <Bottone piccolo onClick={() => setApro("nome")}>
            {t("gear.write.rig")}
          </Bottone>{" "}
          {/* senza montature da scegliere il bottone non si offre: la si scrive con "Aggiungi" */}
          {montature.length > 0 && (
            <Bottone piccolo onClick={() => setApro("montatura")}>
              {t("gear.write.mount")}
            </Bottone>
          )}
        </>
      )}
    </Riga>
  )
}

/** Quanto cielo inquadra un corredo, **misurato** sulle sue pose. Chi non ha ancora ripreso non
 *  ce l'ha, e lo dice invece di prendersi il numero che la scheda direbbe. */
function QuantoInquadra({ corredo }: { corredo: Corredo }) {
  if (corredo.scale_arcsec_px === null) return <Dettaglio>{t("gear.noScale")}</Dettaglio>
  return (
    <>
      <Dettaglio>{t("gear.scale", { n: numero(corredo.scale_arcsec_px) })}</Dettaglio>{" "}
      {corredo.width_deg !== null && corredo.height_deg !== null && (
        <Dettaglio>
          {t("gear.field", {
            larghezza: numero(corredo.width_deg),
            altezza: numero(corredo.height_deg),
          })}
        </Dettaglio>
      )}
    </>
  )
}

export function UnFiltro({ filtro, tutti }: { filtro: Filtro; tutti: Filtro[] }) {
  const [correggo, setCorreggo] = useState(false)
  return (
    <Riga
      nome={filtro.name}
      dettagli={
        <>
          {/* Le bande **dichiarate**, e basta: la banda che l'app ricava dal nome puo' essere
              `UNKNOWN`, che a schermo non vuol dire niente. Finche' non l'hai confermata, la
              riga tace. */}
          {filtro.bands.map((b) => (
            <Dettaglio key={b.band}>
              {b.width_nm === null
                ? t("gear.band.noWidth", { banda: b.band })
                : t("gear.band", { banda: b.band, nm: numero(b.width_nm) })}
            </Dettaglio>
          ))}{" "}
          <Uso pezzo={filtro} /> <Ripreso oggetti={filtro.objects} />
        </>
      }
      comparsa={
        correggo && (
          <CorreggiIlFiltro
            filtro={filtro}
            altri={tutti.filter((o) => filtro.mergeable_into.includes(o.id))}
            onChiudi={() => setCorreggo(false)}
          />
        )
      }
    >
      {!correggo && (
        <Bottone piccolo onClick={() => setCorreggo(true)}>
          {t("gear.write.edit")}
        </Bottone>
      )}
    </Riga>
  )
}
