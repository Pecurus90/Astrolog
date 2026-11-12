// @vitest-environment jsdom
/**
 * **Cosa hai ripreso**, accanto a ogni gruppo di pose su cui l'app chiede: per rispondere "quale
 * filtro" o "da dove" senza andare a memoria (Marco, 15/9/2026).
 *
 * - **Gli oggetti che il cielo ha trovato, con quante pose**, nell'ordine che manda l'API; oltre il
 *   terzo si dice quanti altri, perche' una camera copre anni di notti.
 * - **I due vuoti si dicono diversi**: una posa in cui il cielo non ha trovato niente non e' una posa
 *   che non ha ancora guardato o non e' riuscito a guardare. Un vuoto a zero non si scrive.
 * - **Vale in tutte le sezioni che chiedono per gruppo**: i luoghi, i filtri, l'attrezzatura, i
 *   frame senza data.
 */
import { screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  STANOTTE,
  cartellaSenzaData,
  daConfermare,
  filtroIgnoto,
  impostazioni,
  postoIgnoto,
  prove,
  pulisci,
  riga,
  rispondi,
  vaiASezione,
} from "./banco"

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
const CASA = [{ id: 1, name: "Casa", distance_km: 16.2 }]

const PAGINA = daConfermare({
  to_confirm: 5,
  unclear: [
    postoIgnoto({ key: "45.85,11.58", latitude: 45.85, longitude: 11.58, distance_km: 16.2, frames: 109, nights: ["2024-05-17"], candidates: CASA, subjects: MOLTI }),
    postoIgnoto({ key: "46.10,11.20", latitude: 46.1, longitude: 11.2, distance_km: 40.1, frames: 60, nights: ["2024-05-18"], candidates: CASA, subjects: TRE }),
    postoIgnoto({ key: "44.50,10.90", latitude: 44.5, longitude: 10.9, distance_km: 120.4, frames: 4, nights: ["2024-05-19"], candidates: CASA, subjects: NIENTE }),
  ],
  filters: [
    filtroIgnoto({
      id: 7,
      name: "H",
      frames: 120,
      subjects: MOLTI.found,
      rigs: [
        { optics: "RedCat 51", camera: "ASI294MC", frames: 100 },
        { optics: null, camera: "ASI533MC", frames: 20 },
      ],
    }),
  ],
  undated: [
    cartellaSenzaData({ key: "D:/Astro/senza-data", frames: 12, subjects: TRE.found, rigs: [{ optics: "RedCat 51", camera: null, frames: 12 }] }),
  ],
})

function aperta() {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review": { stato: 200, corpo: PAGINA },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

const SITI = /frame senza sito/i

describe("Da confermare -- cosa hai ripreso", () => {
  it("i primi tre oggetti con le loro pose, quanti altri, e i due vuoti detti diversi", async () => {
    aperta()
    const posto = riga(await vaiASezione(SITI), "45,8500 N - 11,5800 E")
    expect(prove(posto).slice(0, 2)).toEqual([
      "Oggetti nel campo=M 81 (68 frame), M 82 (12 frame), NGC 3077 (3 frame) + 2",
      "Altri frame=21 frame senza oggetti identificati · 3 frame non risolti",
    ])
  })

  it("un vuoto a zero non si scrive, e con tre oggetti nemmeno '+ N'", async () => {
    aperta()
    const posto = riga(await vaiASezione(SITI), "46,1000 N - 11,2000 E")
    expect(prove(posto)[0]).toBe("Oggetti nel campo=M 101 (56 frame), NGC 5474 (3 frame), NGC 5477 (1 frame)")
    expect(posto.textContent).not.toMatch(/\+ \d|senza oggetti|non risolti/)
  })

  it("se il cielo non ha niente da dire, la riga non dice 'Oggetti'", async () => {
    aperta()
    const posto = riga(await vaiASezione(SITI), "44,5000 N - 10,9000 E")
    expect(posto.textContent).not.toMatch(/Oggetti/)
  })

  it("un filtro dice gli oggetti e con quali ottica e camera e' stato usato", async () => {
    aperta()
    const filtro = riga(await vaiASezione(/^filtri$/i), "H")
    expect(prove(filtro)).toEqual([
      "Oggetti nel campo=M 81 (68 frame), M 82 (12 frame), NGC 3077 (3 frame) + 2",
      "Ottica e camera=RedCat 51 · ASI294MC | ASI533MC",
    ])
  })

  it("anche i frame senza data dicono cosa hai ripreso, e con cosa", async () => {
    aperta()
    const cartella = riga(await vaiASezione(/frame senza data/i), "D:/Astro/senza-data")
    expect(prove(cartella).slice(-2)).toEqual([
      "Oggetti nel campo=M 101 (56 frame), NGC 5474 (3 frame), NGC 5477 (1 frame)",
      "Ottica e camera=RedCat 51",
    ])
    expect(screen.queryByText(/review\./)).toBeNull() // nessuna chiave di traduzione grezza
  })
})
