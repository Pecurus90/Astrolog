// @vitest-environment jsdom
/**
 * **Cosa hai ripreso**, accanto a ogni gruppo di pose su cui l'app chiede: per rispondere "quale
 * filtro" o "da dove" senza andare a memoria (Marco, 15/9/2026).
 *
 * - **Gli oggetti che il cielo ha trovato, con quante pose**, nell'ordine che manda l'API; oltre il
 *   terzo si dice quanti altri, perche' una camera copre anni di notti.
 * - **I due vuoti si dicono diversi**: una posa in cui il cielo non ha trovato niente non e' una posa
 *   che non ha ancora guardato o non e' riuscito a guardare. Un vuoto a zero non si scrive.
 * - **Vale in tutte le sezioni che chiedono per gruppo**: oggi i luoghi.
 */
import { screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, impostazioni, pulisci, riga, rispondi, vaiASezione } from "./banco"

afterEach(pulisci)

const MOLTI = {
  found: [
    { name: "M 81", frames: 68 },
    { name: "M 82", frames: 12 },
    { name: "NGC 3077", frames: 3 },
    { name: "NGC 2976", frames: 2 },
    { name: "IC 2574", frames: 1 },
  ],
  not_found: 21,
  not_yet: 3,
}
// esattamente quanti se ne nominano: nessun "altri"
const TRE = {
  found: [
    { name: "M 101", frames: 56 },
    { name: "NGC 5474", frames: 3 },
    { name: "NGC 5477", frames: 1 },
  ],
  not_found: 0,
  not_yet: 0,
}
const NIENTE = { found: [], not_found: 0, not_yet: 0 }

const PAGINA = {
  to_confirm: 5,
  lookalikes: [],
  filters: [],
  rig_choices: [],
  objects: [],
  mosaics: [],
  filter_choices: [],
  gear: [],
  unclear: [
    {
      key: "45.85,11.58",
      latitude: 45.85,
      longitude: 11.58,
      distance_km: 16.2,
      frames: 109,
      nights: ["2024-05-17"],
      site: null,
      candidates: [],
      subjects: MOLTI,
    },
    {
      key: "46.10,11.20",
      latitude: 46.1,
      longitude: 11.2,
      distance_km: 40.1,
      frames: 60,
      nights: ["2024-05-18"],
      site: null,
      candidates: [],
      subjects: TRE,
    },
    {
      key: "44.50,10.90",
      latitude: 44.5,
      longitude: 10.9,
      distance_km: 120.4,
      frames: 4,
      nights: ["2024-05-19"],
      site: null,
      candidates: [],
      subjects: NIENTE,
    },
  ],
}

function aperta() {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review": { stato: 200, corpo: PAGINA },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

describe("Da confermare -- cosa hai ripreso", () => {
  it("i primi tre oggetti con le loro pose, quanti altri, e i due vuoti detti diversi", async () => {
    aperta()
    const notte = riga(await vaiASezione(/frame senza sito/i), "45.85,11.58")
    expect(notte.textContent).toMatch(
      /ripreso: M 81 \(68 frame\), M 82 \(12 frame\), NGC 3077 \(3 frame\) e altri 2/,
    )
    expect(notte.textContent).toMatch(/21 frame in cui il cielo non ha trovato niente/)
    // una posa su cui il lavoro si e' guastato non riparte da sola: "ancora" da solo farebbe aspettare
    expect(notte.textContent).toMatch(/3 frame che il cielo non ha ancora guardato o non e' riuscito a guardare/)
  })

  it("un vuoto a zero non si scrive, e con tre oggetti nemmeno 'altri'", async () => {
    aperta()
    const notte = riga(await vaiASezione(/frame senza sito/i), "46.10,11.20")
    expect(notte.textContent).toMatch(/ripreso: M 101 \(56 frame\), NGC 5474 \(3 frame\), NGC 5477 \(1 frame\)/)
    expect(notte.textContent).not.toMatch(/altri|non ha trovato|non ha ancora/)
  })

  it("se il cielo non ha niente da dire, la riga non dice 'ripreso'", async () => {
    aperta()
    const notte = riga(await vaiASezione(/frame senza sito/i), "44.50,10.90")
    expect(notte.textContent).not.toMatch(/ripreso/)
  })

  it.each([
    [/frame senza sito/i, "45.85,11.58"],
  ])("anche la sezione %s dice cosa hai ripreso", async (sezione, chiave) => {
    aperta()
    expect(riga(await vaiASezione(sezione), chiave).textContent).toMatch(/ripreso: M (81|101)/)
    expect(screen.queryByText(/review\./)).toBeNull() // nessuna chiave di traduzione grezza
  })
})
