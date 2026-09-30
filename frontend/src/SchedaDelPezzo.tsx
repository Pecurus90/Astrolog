import { Campo } from "./Campo"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"
import { misura, testo } from "./scritto"

/**
 * La **scheda di uno strumento**: un campo per volta, disegnato da cio' che si chiama.
 *
 * Sta in una casa sola perche' la scrivono in due gesti dell'Attrezzatura -- il pezzo che nasce e
 * quello che si corregge. **Quali campi** chiedere non si decide qui: li manda l'API per genere
 * (`cards`), perche' si scrive anche il primo pezzo di un genere che non possiedi. Si percorrono
 * nell'ordine che arriva.
 */

type CampoScheda = components["schemas"]["GearList"]["cards"][string][number]
type Colore = NonNullable<components["schemas"]["InstrumentOnPage"]["camera_type"]>

export type { CampoScheda }

export function CampoDellaScheda({
  id,
  campo,
  valore,
  onValore,
}: {
  id: string
  campo: CampoScheda
  valore: string | number | null | undefined
  onValore: (v: string | number | undefined) => void
}) {
  const { etichetta, forma } = CAMPI[campo]
  if (forma === "colore") {
    return (
      <Campo id={id} etichetta={t(etichetta)}>
        <select
          className="as-scelta"
          id={id}
          value={valore ?? ""}
          onChange={(e) => onValore(e.target.value || undefined)}
        >
          <option value="">--</option>
          {Object.entries(COLORI).map(([valore, parola]) => (
            <option key={valore} value={valore}>
              {t(parola)}
            </option>
          ))}
        </select>
      </Campo>
    )
  }
  if (forma === "testo") {
    return (
      <Campo id={id} etichetta={t(etichetta)}>
        <input
          className="as-campo__input"
          id={id}
          defaultValue={valore ?? ""}
          onChange={(e) => onValore(testo(e.target.value))}
        />
      </Campo>
    )
  }
  return (
    <Campo id={id} etichetta={t(etichetta)}>
      <input
        className="as-campo__input"
        id={id}
        type="number"
        min={0}
        step={forma === "conto" ? 1 : "any"}
        defaultValue={valore ?? ""}
        onChange={(e) => onValore(misura(e.target.value, forma === "conto"))}
      />
    </Campo>
  )
}


/** Come si chiama **un** pezzo di ogni genere -- al singolare: e' il nome di una cosa sola, non
 *  del gruppo che la pagina Attrezzatura intitola. Un `Record` sul tipo generato, come i campi:
 *  un genere nuovo nello schema fa fallire la compilazione invece di sparire in silenzio. */
export const GENERE: Record<components["schemas"]["InstrumentOnPage"]["kind"], Chiave> = {
  optics: "review.kind.optics",
  camera: "review.kind.camera",
  mount: "review.kind.mount",
  reducer: "review.kind.reducer",
  filter_wheel: "review.kind.filter_wheel",
  guide_scope: "review.kind.guide_scope",
  guide_camera: "review.kind.guide_camera",
  focuser: "review.kind.focuser",
}

/** Ogni campo della scheda: la sua parola e **che forma ha** -- un testo, una misura (positiva),
 *  un conto (intero) o il colore. Un `Record` sul tipo generato: il giorno che il backend aggiunge
 *  un campo, qui non compila finche' qualcuno non dice come si scrive -- invece di comparire, in
 *  silenzio, come un numero. */
const CAMPI: Record<CampoScheda, { etichetta: Chiave; forma: "testo" | "misura" | "conto" | "colore" }> =
  {
    brand: { etichetta: "review.card.brand", forma: "testo" },
    model: { etichetta: "review.card.model", forma: "testo" },
    camera_type: { etichetta: "review.card.camera_type", forma: "colore" },
    pixel_size_um: { etichetta: "review.card.pixel_size_um", forma: "misura" },
    aperture_mm: { etichetta: "review.card.aperture_mm", forma: "misura" },
    focal_mm: { etichetta: "review.card.focal_mm", forma: "misura" },
    reducer_factor: { etichetta: "review.card.reducer_factor", forma: "misura" },
    weight_kg: { etichetta: "review.card.weight_kg", forma: "misura" },
    payload_kg: { etichetta: "review.card.payload_kg", forma: "misura" },
    slots: { etichetta: "review.card.slots", forma: "conto" },
    notes: { etichetta: "review.card.notes", forma: "testo" },
  }

/** I colori di una camera, presi dal tipo generato (`CameraType` nel backend). */
const COLORI: Record<Colore, Chiave> = {
  mono: "review.card.mono",
  color: "review.card.color",
}
