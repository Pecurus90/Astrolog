import { useState } from "react"

import { CampoDelModulo, Modulo, TestoDelModulo, type TipoDelModulo } from "./componenti/Modulo"
import { PillolaScelta } from "./componenti/PillolaScelta"
import type { Formato } from "./componenti/Tema"
import { rifiutoDetto, useScrittura } from "./ModuloDelGesto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { t } from "./i18n"
import { misuraConVirgola } from "./scritto"

type Pezzo = components["schemas"]["InstrumentOnPage"]

/**
 * Un **setup** scritto a mano (tavola v82 `modulo`, tipo Setup): ottica e camera fra i tuoi strumenti,
 * a pillole, e la focale effettiva, che senza farebbe nascere un doppione il giorno che i file la
 * dicono. E' quello che la scansione trovera': il setup e' la sua impronta.
 */
export function NuovoSetup({
  pezzi,
  formato,
  scansione,
  tipo,
  onChiudi,
}: {
  pezzi: Pezzo[]
  formato: Formato
  scansione: boolean
  tipo: TipoDelModulo & { onCambia: () => void }
  onChiudi: () => void
}) {
  const [ottica, setOttica] = useState<number | undefined>()
  const [camera, setCamera] = useState<number | undefined>()
  const [focale, setFocale] = useState("")
  const mm = misuraConVirgola(focale)
  const scrivi = useScrittura(async () => {
    if (ottica === undefined || camera === undefined || mm === undefined) {
      throw new Error("il setup vuole ottica, camera e focale")
    }
    const { data, error } = await api.POST("/api/v1/gear/rigs", {
      body: { optics_id: ottica, camera_id: camera, focal_mm: mm },
    })
    if (error) throw error
    return data
  }, onChiudi)
  const perche = scansione
    ? t("gear.write.scanning")
    : ottica === undefined || camera === undefined || mm === undefined
      ? t("gear.write.needRig")
      : ""
  const scelta = (
    kind: "optics" | "camera",
    lab: string,
    v: number | undefined,
    on: (id: number) => void,
  ) => (
    <CampoDelModulo id={`aggiungi-${kind}`} etichetta={lab} largo>
      <PillolaScelta
        forma="risposta"
        fondo="vuoto"
        etichetta={lab}
        formato={formato}
        opzioni={pezzi
          .filter((p) => p.kind === kind)
          .map((p) => ({ l: p.name, sel: v === p.id, on: () => on(p.id) }))}
      />
    </CampoDelModulo>
  )
  return (
    <Modulo
      titolo={t("gear.write.add.title")}
      formato={formato}
      tipo={tipo}
      errore={rifiutoDetto(scrivi.error)}
      salva={{ onSalva: () => scrivi.mutate(), occupato: scrivi.isPending, spento: perche !== "" }}
      onAnnulla={onChiudi}
      perche={perche}
    >
      {scelta("optics", t("gear.write.optics"), ottica, setOttica)}
      {scelta("camera", t("gear.write.camera"), camera, setCamera)}
      <CampoDelModulo id="aggiungi-focal" etichetta={t("gear.write.focal")}>
        <TestoDelModulo id="aggiungi-focal" valore={focale} onValore={setFocale} />
      </CampoDelModulo>
    </Modulo>
  )
}
