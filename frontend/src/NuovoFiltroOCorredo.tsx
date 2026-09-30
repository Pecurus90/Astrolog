import { type ReactNode, useState } from "react"

import { Campo } from "./Campo"
import { Modulo, NomeDelPezzo, useScrittura } from "./ModuloDelGesto"
import { TendinaDellaBanda } from "./TendinaDellaBanda"
import { TendinaDiScelta } from "./TendinaDiScelta"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { t } from "./i18n"

type Pezzo = components["schemas"]["InstrumentOnPage"]
type Banda = components["schemas"]["BandIn"]["band"]

/**
 * Un **filtro** e un **corredo** scritti a mano, dal gesto *Aggiungi un pezzo* (Marco, 21/9/2026:
 * qualunque genere, compreso un corredo che non ha ancora ripreso). Sono quelli che la scansione
 * trovera': il filtro e' il suo nome, il corredo la sua impronta.
 *
 * - Il filtro chiede **la banda**, che e' cio' che sblocca le pose; il corredo **la focale**, che
 *   senza farebbe nascere un doppione il giorno che i file la dicono.
 * - La scelta del genere arriva da fuori (`scelta`): e' la stessa tendina degli strumenti.
 */
export function NuovoFiltro({ scelta, onChiudi }: { scelta: ReactNode; onChiudi: () => void }) {
  const [nome, setNome] = useState("")
  const [banda, setBanda] = useState<Banda | undefined>()
  const [marca, setMarca] = useState("")
  const [modello, setModello] = useState("")
  const scrivi = useScrittura(async () => {
    const { error } = await api.POST("/api/v1/gear/filters", {
      body: {
        name: nome.trim(),
        bands: banda ? [{ band: banda }] : [],
        ...(marca.trim() ? { brand: marca.trim() } : {}),
        ...(modello.trim() ? { model: modello.trim() } : {}),
      },
    })
    if (error) throw error
  }, onChiudi)
  return (
    <Modulo
      base="aggiungi"
      titolo={t("gear.write.add.title")}
      onManda={() => scrivi.mutate()}
      onAnnulla={onChiudi}
      salvando={scrivi.isPending}
      valido={nome.trim() !== "" && banda !== undefined}
      errore={scrivi.error}
    >
      {scelta}
      <NomeDelPezzo id="aggiungi-name" onNome={(n) => setNome(n ?? "")} />
      <TendinaDellaBanda
        id="aggiungi-band"
        etichetta={t("review.filters.band")}
        valore={banda}
        onBanda={(b) => setBanda(b || undefined)}
      />
      <Campo id="aggiungi-brand" etichetta={t("review.card.brand")}>
        <input className="as-campo__input" id="aggiungi-brand" onChange={(e) => setMarca(e.target.value)} />
      </Campo>
      <Campo id="aggiungi-model" etichetta={t("review.card.model")}>
        <input className="as-campo__input" id="aggiungi-model" onChange={(e) => setModello(e.target.value)} />
      </Campo>
    </Modulo>
  )
}

export function NuovoCorredo({
  scelta,
  pezzi,
  onChiudi,
}: {
  scelta: ReactNode
  pezzi: Pezzo[]
  onChiudi: () => void
}) {
  const [ottica, setOttica] = useState<number | undefined>()
  const [camera, setCamera] = useState<number | undefined>()
  const [focale, setFocale] = useState<number | undefined>()
  const scrivi = useScrittura(async () => {
    if (ottica === undefined || camera === undefined || focale === undefined) {
      throw new Error("il corredo vuole ottica, camera e focale")
    }
    const { error } = await api.POST("/api/v1/gear/rigs", {
      body: { optics_id: ottica, camera_id: camera, focal_mm: focale },
    })
    if (error) throw error
  }, onChiudi)
  return (
    <Modulo
      base="aggiungi"
      titolo={t("gear.write.add.title")}
      onManda={() => scrivi.mutate()}
      onAnnulla={onChiudi}
      salvando={scrivi.isPending}
      valido={ottica !== undefined && camera !== undefined && focale !== undefined}
      errore={scrivi.error}
    >
      {scelta}
      <TendinaDiScelta
        id="aggiungi-optics"
        etichetta={t("gear.write.optics")}
        altri={pezzi.filter((p) => p.kind === "optics")}
        valore={ottica}
        onScelta={setOttica}
      />
      <TendinaDiScelta
        id="aggiungi-camera"
        etichetta={t("gear.write.camera")}
        altri={pezzi.filter((p) => p.kind === "camera")}
        valore={camera}
        onScelta={setCamera}
      />
      <Campo id="aggiungi-focal" etichetta={t("gear.write.focal")}>
        <input
          className="as-campo__input"
          id="aggiungi-focal"
          type="number"
          min="1"
          // una focale che non va la rifiuta il backend, che ne ha la regola
          onChange={(e) => setFocale(e.target.value === "" ? undefined : Number(e.target.value))}
        />
      </Campo>
    </Modulo>
  )
}
