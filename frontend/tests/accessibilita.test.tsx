// @vitest-environment jsdom
/**
 * La guardia di accessibilita': axe sulla pagina vera, a ogni giro del cancello.
 *
 * Una sezione e' fatta quando e' stata guidata nel browser **e passa questa guardia**: finche'
 * non esisteva, "fatta" non era una parola verificabile.
 *
 * La seconda prova e' la macchina che dimostra se stessa. Un elenco di violazioni vuoto direbbe
 * "tutto a posto" anche se axe non stesse guardando niente -- e una guardia mai vista rossa non
 * ha dimostrato nulla. Qui la dimostrazione resta nella suite per sempre, invece di essere un
 * esperimento fatto una volta e poi perso.
 */
import { fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SCHEDE,
  SENZA_SOGGETTI,
  SITO_DI_CASA,
  SPINA,
  STANOTTE,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  violazioni,
} from "./banco"
import { SCELTE, apriArchivioSu, archivio } from "./archivio-banco"

afterEach(pulisci)

describe("l accessibilita della prima pagina", () => {
  it("la pagina non ha violazioni", async () => {
    // Il piede della barra si monta **pieno**, non nel suo stato vuoto: con la riserva del banco
    // axe guarderebbe due righe di scuse, e il markup coi numeri -- quello che si vede quasi
    // sempre -- non passerebbe mai di qui.
    rispondi({
      "/api/v1/tonight": {
        stato: 200,
        corpo: {
          night: "2026-09-19",
          site: { name: "Vicenza", sky_sqm: 20.8, bortle: 4 },
          moon: {
            phase_key: "waxing_gibbous",
            illumination_pct: 60,
            rise: "2026-09-19T15:49:26+02:00",
            set: null,
            highest: { at: "2026-09-19T19:48:00+02:00", altitude_deg: 16.1 },
            // una traccia vera: con l'elenco vuoto il grafico non si disegna, e axe non
            // guarderebbe mai il markup che l'utente vede quasi sempre
            track: [
              { at: "2026-09-19T12:00:00+02:00", altitude_deg: -35.8 },
              { at: "2026-09-19T19:48:00+02:00", altitude_deg: 16.1 },
              { at: "2026-09-20T12:00:00+02:00", altitude_deg: -43.4 },
            ],
            ceiling_deg: 75,
            lit_side: "right",
          },
          // Il piede si monta **pieno**, fasce comprese: senza, axe guarda una tela che nessun
          // utente vedra' mai -- l'API le manda sempre.
          sky_bands: [
            { starts_at: "2026-09-19T12:00:00+02:00", ends_at: "2026-09-19T19:00:00+02:00", kind: "day" },
            { starts_at: "2026-09-19T19:00:00+02:00", ends_at: "2026-09-19T20:30:00+02:00", kind: "civil" },
            { starts_at: "2026-09-19T20:30:00+02:00", ends_at: "2026-09-20T05:00:00+02:00", kind: "dark" },
            { starts_at: "2026-09-20T05:00:00+02:00", ends_at: "2026-09-20T12:00:00+02:00", kind: "day" },
          ],
          weather: {
            verdict: "go",
            cloud_total_pct: 10,
            usable_hours: 6,
            window: "dark",
            window_hours: 8,
            agreement: { go: 3, marginal: 1, nogo: 0, unknown: 0, total: 4 },
            wind_700hpa_kmh: 30,
            wind_700hpa_tenths: 6,
          },
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 7 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    const { container } = await disegna()
    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno Stanotte, aperta", async () => {
    // Un pannello che si apre e' il markup dove si sbaglia di piu': il nome del pannello, il
    // titolo che non e' un titolo, la scelta del sito senza nome. Chiuso, axe non vede niente.
    rispondi({
      "/api/v1/tonight": {
        stato: 200,
        corpo: {
          night: "2026-09-19",
          site: { name: "Vicenza", sky_sqm: 20.8, bortle: 4 },
          moon: {
            phase_key: "waxing_gibbous",
            illumination_pct: 60,
            rise: "2026-09-19T15:49:26+02:00",
            set: null,
            highest: { at: "2026-09-19T19:48:00+02:00", altitude_deg: 16.1 },
            track: [
              { at: "2026-09-19T12:00:00+02:00", altitude_deg: -35.8 },
              { at: "2026-09-19T19:48:00+02:00", altitude_deg: 16.1 },
              { at: "2026-09-20T12:00:00+02:00", altitude_deg: -43.4 },
            ],
            ceiling_deg: 75,
            lit_side: "right",
          },
          // Il piede si monta **pieno**, fasce comprese: senza, axe guarda una tela che nessun
          // utente vedra' mai -- l'API le manda sempre.
          sky_bands: [
            { starts_at: "2026-09-19T12:00:00+02:00", ends_at: "2026-09-19T19:00:00+02:00", kind: "day" },
            { starts_at: "2026-09-19T19:00:00+02:00", ends_at: "2026-09-19T20:30:00+02:00", kind: "civil" },
            { starts_at: "2026-09-19T20:30:00+02:00", ends_at: "2026-09-20T05:00:00+02:00", kind: "dark" },
            { starts_at: "2026-09-20T05:00:00+02:00", ends_at: "2026-09-20T12:00:00+02:00", kind: "day" },
          ],
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      // due siti: con uno solo la scelta non si monta, e axe non la guarderebbe
      "/api/v1/sites": {
        stato: 200,
        corpo: { items: [SITO_DI_CASA, { ...SITO_DI_CASA, id: 2, name: "Passo Giau", is_default: false }], total: 2, limit: 50, offset: 0 },
      },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    const { container } = await disegna()
    fireEvent.click(await screen.findByRole("button", { name: /stanotte a vicenza/i }))
    const pannello = await screen.findByRole("complementary", { name: /stanotte/i })
    await within(pannello).findByRole("radio", { name: /passo giau/i })
    expect(within(pannello).getByText(/gibbosa crescente/i)).toBeDefined()
    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno Da confermare, che e la pagina dove si lavora", async () => {
    // La superficie piu' fitta dell'app: una tendina, un elenco di bottoni, campi e una select.
    // E' dove un'etichetta orfana o un bottone senza nome fa piu' danno, perche' qui non si
    // guarda e basta -- si risponde.
    rispondi({
      ...STANOTTE,
      "/api/v1/vocab/filter-models": {
        stato: 200,
        corpo: {
          items: [
            { id: "antlia-alp-t-3nm", brand: "Antlia", name: "ALP-T 3nm", passband: "DUO_HAOIII" },
          ],
        },
      },
      "/api/v1/review": {
        stato: 200,
        corpo: {
          to_confirm: 1,
          filters: [
            {
              id: 7,
              name: "H",
              brand: null,
              model: null,
              catalog_id: null,
              passband: "UNKNOWN",
              is_none: false,
              bands: [],
              frames: 120,
            },
          ],
          // due grafie della stessa camera: un gruppo di due scelte che nomina la coppia
          lookalikes: [
            { id: 7, name: "ATR 2600M", frames: 432, into_id: 4, into_name: "ATR2600M", into_frames: 6558 },
          ],
          rig_choices: [{ id: 2, name: null, optics: "Askar 103Apo", camera: "ATR2600M", focal_mm: 560 }],
          // **Con un oggetto vero**: la sezione porta liste annidate, un bottone per candidato e
          // una coppia etichetta/campo per riga -- cioe' tutto cio' che axe deve guardare. Con
          // `objects: []` la guardia collaudava una pagina che quella roba non ce l'aveva.
          // The object card waits for its design (ADR 0014 S3): the rows stay for when it lands.
          objects: [
            {
              key: "ngc-7023",
              name: "NGC 7023",
              slug: "ngc-7023",
              method: "coord_review",
              confidence: "low",
              frames: 60,
              integration_s: 9720,
              untimed: 2,
              group: null,
              candidates: [
                {
                  slug: "ldn-1174",
                  name: "LDN 1174",
                  common_name: null,
                  in_frame: false,
                },
              ],
              answer: null,
            },
            // a group of frames without a name: the object field and the "not an object" box
            {
              key: 'frames:["2024-06-01", null, null, null, null]',
              name: null,
              slug: null,
              method: null,
              confidence: null,
              group: { night: "2024-06-01", camera: null, telescope: null, ra_deg: null, dec_deg: null, first_frame: "2024-06-01T22:10:00+02:00", last_frame: "2024-06-02T01:40:00+02:00" },
              frames: 4,
              integration_s: 0,
              untimed: 4,
              candidates: [],
              answer: null,
            },
          ],
          // un mosaico e un posto: due gruppi di scelte da guardare. Che ognuno nomini la
          // sua riga axe non lo vede: lo provano i test delle sezioni (confermare-cielo-tempo)
          mosaics: [
            { key: "impronta-m42", ra_deg: 83.8, dec_deg: -5.4, object: "M 42", panels: 3, frames: 90, integration_s: 10800, untimed: 0, answer: null },
          ],
          unclear: [
            { key: "45.85,11.58", latitude: 45.85, longitude: 11.58, distance_km: 16.2, frames: 391, nights: ["2024-05-17"], site: null, candidates: [{ id: 1, name: "Casa", distance_km: 16.2 }], subjects: SENZA_SOGGETTI },
          ],
          filter_choices: [{ id: 3, name: "Lum", passband: "L" }],
          gear: [],
          optics_choices: ["Askar 103Apo"],
          // una cartella di file che non dicono che file sono: due scelte in un gruppo, una
          // risposta gia' data e una ancora da dare
          typeless: [
            { key: "D:/Astro/2024-05-17/dark", frames: 120, answer: null },
            { key: "D:/Astro/2024-06-01/M51", frames: 30, answer: "light" },
          ],
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    const { container } = await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    await screen.findByRole("region", { name: /filtri/i })
    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno l Archivio, con tutte le forme che una riga puo' avere", async () => {
    // Le righe scelte portano ognuna una forma diversa -- col catalogo e coi filtri, senza
    // catalogo e con frame senza tempo -- piu' il pulsante per le altre pagine. E si guardano
    // **tutte e due le viste**: le carte e la tabella disegnano cose diverse, e una sola
    // passata lascerebbe meta' pagina mai vista da axe.
    const riga = {
      key: "m-31",
      name: "M 31",
      slug: "m-31",
      frames: 120,
      integration_s: 43200,
      untimed: 0,
      constellation: "And",
      type_code: "GALAXY",
      filters: [
        { name: "Lum", passband: "L", frames: 80, integration_s: 28800 },
        { name: "Ha", passband: "HA", frames: 40, integration_s: 14400 },
      ],
      panels: null,
      panel_list: [],
    }
    // e un mosaico, coi suoi pannelli: uno col suo oggetto, uno di cui il cielo non ne sa
    const mosaico = {
      ...riga,
      key: "impronta-ic405", // gitleaks:allow
      name: "IC 405",
      panels: 2,
      panel_list: [
        { object: "IC 405", ra_deg: 79.07, dec_deg: 34.25, frames: 40, integration_s: 14400, untimed: 0 },
        { object: null, ra_deg: 79.9, dec_deg: 33.1, frames: 20, integration_s: 7200, untimed: 2 },
      ],
    }
    rispondi({
      ...STANOTTE,
      "/api/v1/archive": {
        stato: 200,
        corpo: {
          items: [
            riga,
            {
              ...riga,
              key: "NGC 7000",
              name: "NGC 7000",
              slug: null,
              untimed: 4,
              constellation: null,
              type_code: null,
              filters: [],
            },
            mosaico,
          ],
          total: 300,
          limit: 2,
          offset: 0,
          choices: SCELTE,
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    const { container } = await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /archivio/i }))
    await screen.findByRole("button", { name: /mostra altri/i })

    expect(await violazioni(container)).toEqual([])

    fireEvent.click(await screen.findByRole("tab", { name: /elenco/i }))
    await screen.findByRole("table")

    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno l Archivio quando un filtro non trova niente", async () => {
    // Uno stato che la barra ha creato: barra accesa, elenco vuoto, il "non ho trovato niente"
    // **dentro** il pannello della vista. Le schede restano e devono continuare a governare due
    // pannelli veri -- e finora axe l'Archivio lo vedeva solo pieno.
    archivio([])
    const { container } = await apriArchivioSu("/archivio?q=zzz")
    await screen.findByText(/nessun oggetto con questi filtri/i)

    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno le Notti, con le due righe che spiegano un elenco corto", async () => {
    // La pagina si monta **piena** e con tutti e due i cappelli accesi: l'avviso d'attesa e il
    // paragrafo con dentro un collegamento sono proprio le forme che axe guarda, e con l'elenco
    // vuoto non ci sarebbero.
    rispondi({
      ...STANOTTE,
      "/api/v1/nights": {
        stato: 200,
        corpo: {
          items: [
            {
              id: 7,
              night_date: "2024-05-18",
              site: "Cima Ekar",
              site_source: "declared",
              frames: 3,
              integration_s: 10800,
              untimed: 1,
              objects: [{ key: "m-51", name: "M 51", frames: 3, integration_s: 10800 }],
              filters: [{ name: "Ha", frames: 3, integration_s: 10800 }],
              weather: { state: "ok", verdict: "marginal", cloud_total_pct: 40, usable_hours: 3, window: "dark", window_hours: 8 },
            },
          ],
          total: 300,
          limit: 1,
          offset: 0,
          totals: { nights: 300, frames: 900, integration_s: 360000, untimed: 1 },
          waiting: [{ answer_at: "review", frames: 12 }],
          still_reading: 431,
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    const { container } = await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /notti/i }))
    await screen.findByRole("button", { name: /mostra altre/i })

    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno il Meteo, con la scheda di una notte aperta", async () => {
    // Piena, col fattore che dice l'ora e la tabella aperta: la tabella, le intestazioni di riga e
    // lo switch dei modelli sono proprio le forme che axe guarda.
    const ora = (at: string, sky: string) => ({
      at,
      sky,
      cloud_total_pct: 10,
      cloud_low_pct: 0,
      cloud_mid_pct: null,
      cloud_high_pct: 5,
      temperature_c: 12,
      humidity_pct: 60,
      dew_point_c: 4,
      wind_kmh: 5,
      wind_gust_kmh: 31,
      precip_mm: 0,
      wind_700hpa_kmh: 30,
      wind_250hpa_kmh: 120,
      wind_200hpa_kmh: null,
      seeing_arcsec: 1.25,
      aerosol_optical_depth: 0.1,
      dust_ugm3: 2,
      moon_pct: null,
      dew_spread_c: 8,
      shown: true,
      levels: {
        cloud: "go", cloud_low: "go", rain: "go", gust: "nogo", wind: "go", condensation: "go",
        jet: "go", seeing: "go", aerosol: null, moon: null,
      },
    })
    rispondi({
      ...STANOTTE,
      "/api/v1/weather": {
        stato: 200,
        corpo: {
          site: "Casa",
          missing: null,
          model: "best_match",
          models: ["best_match", "ecmwf_ifs025", "icon_seamless", "gfs_seamless"],
          fetched_at: "2026-09-25T15:00:00.000Z",
          full_nights: 3,
          seeing: { key: true, source: null, meteoblue: "refused" },
          scales: [],
          sources: [{ source: "cams", fetched_at: "2026-09-25T15:00:00.000Z" }],
          nights: [
            {
              night: "2026-09-26",
              trend: false,
              agreement: { go: 4, marginal: 0, nogo: 0, unknown: 0, total: 4 },
              wind_700hpa_kmh: 30,
              wind_700hpa_tenths: 6,
              verdict: "go",
              cloud_total_pct: 10,
              usable_hours: 2,
              usable_since: "2026-09-26T22:00:00+02:00",
              usable_until: "2026-09-27T00:00:00+02:00",
              window: "dark",
              window_hours: 2,
              shown_from: "2026-09-26T22:00:00+02:00",
              shown_until: "2026-09-26T23:00:00+02:00",
              measures: [
                {
                  code: "wind", level: "go", weighs: false, value: 5, peak: 5,
                  peak_at: "2026-09-26T22:00:00+02:00", peak_until: "2026-09-26T23:00:00+02:00",
                  spans: [], axis_min: 0, axis_max: 45, since: "2026-09-26T22:00:00+02:00",
                  until: "2026-09-27T00:00:00+02:00", hours: 2, known_hours: 2,
                  known_since: "2026-09-26T22:00:00+02:00", known_until: "2026-09-27T00:00:00+02:00",
                },
                {
                  code: "gust", level: "nogo", weighs: true, value: 31, peak: 31,
                  peak_at: "2026-09-26T22:00:00+02:00", peak_until: "2026-09-26T23:00:00+02:00",
                  spans: [{ level: "nogo", since: "2026-09-26T22:00:00+02:00", until: "2026-09-27T00:00:00+02:00", hours: 2 }],
                  axis_min: 0, axis_max: 45, since: "2026-09-26T22:00:00+02:00",
                  until: "2026-09-27T00:00:00+02:00", hours: 2, known_hours: 2,
                  known_since: "2026-09-26T22:00:00+02:00", known_until: "2026-09-27T00:00:00+02:00",
                },
              ],
              hours: [ora("2026-09-26T22:00:00+02:00", "dark"), ora("2026-09-26T23:00:00+02:00", "dark")],
            },
          ],
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    const { container } = await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /meteo/i }))
    // la scheda della notte, coi semafori, le carte e il loro grafico
    await screen.findByRole("tabpanel")
    await screen.findAllByRole("article")

    expect(await violazioni(container)).toEqual([])
  })

  it("e nemmeno l Attrezzatura, coi pezzi che non hanno numeri", async () => {
    // La pagina si monta **piena** e con dentro i casi che parlano: la montatura senza ore e il
    // corredo senza scala sono testo dentro una riga di dettagli, cioe' proprio il markup che
    // axe guarda -- e con l'elenco vuoto non ci sarebbero.
    const pezzo = {
      brand: null,
      model: null,
      camera_type: null,
      pixel_size_um: null,
      pixel_from_sky_um: null,
      aperture_mm: null,
      focal_mm: null,
      reducer_factor: null,
      weight_kg: null,
      payload_kg: null,
      slots: null,
      backfocus_mm: null,
      notes: null,
      detected: true,
      mergeable_into: [] as number[],
      frames: 120,
      integration_s: 36000,
      untimed: 2,
      nights: 7,
      objects: [{ key: "m-31", name: "M 31", frames: 120, integration_s: 36000 }],
      counted: true,
    }
    rispondi({
      ...STANOTTE,
      "/api/v1/gear": {
        stato: 200,
        corpo: {
          instruments: [
            { ...pezzo, id: 1, kind: "optics", name: "TS 130 APO", aperture_mm: 130, focal_mm: 910 },
            {
              ...pezzo,
              id: 2,
              kind: "mount",
              name: "EQ6-R",
              no_hours: "no_rig",
              payload_kg: 20,
              frames: null,
              integration_s: null,
              untimed: null,
              nights: null,
              objects: [],
              counted: true,
            },
          ],
          rigs: [
            {
              id: 10,
              name: "Il grande",
              optics: "TS 130 APO",
              camera: "ASI2600MM",
              focal_mm: 910,
              frames: 120,
              integration_s: 36000,
              untimed: 2,
              nights: 7,
              objects: [{ key: "m-31", name: "M 31", frames: 120, integration_s: 36000 }],
              counted: true,
              scale_arcsec_px: null,
              width_deg: null,
              height_deg: null,
            },
          ],
          filters: [
            {
              id: 3,
              name: "Ha",
              brand: null,
              model: null,
              bands: [{ band: "HA", width_nm: 3 }],
              frames: 60,
              integration_s: 18000,
              untimed: 0,
              nights: 4,
              objects: [{ key: "m-42", name: "M 42", frames: 60, integration_s: 18000 }],
              counted: true,
            },
          ],
          cards: SCHEDE,
        },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    const { container } = await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /attrezzatura/i }))
    await screen.findByRole("list", { name: /corredi/i })
    // Anche **i due gesti aperti**: una scheda che si corregge e una che nasce sono campi con le
    // loro etichette, ed e' li' che un modulo senza nomi farebbe danno a chi ascolta.
    fireEvent.click(screen.getAllByRole("button", { name: /correggi/i })[0] as HTMLElement)
    fireEvent.click(screen.getByRole("button", { name: /aggiungi un pezzo/i }))

    expect(await violazioni(container)).toEqual([])
  })

  it("e la guardia morde davvero quando una violazione c e", async () => {
    // Un bottone senza nome accessibile: chi usa un lettore di schermo sente "bottone" e basta.
    // Se questa prova diventasse verde, vorrebbe dire che axe non sta guardando -- e allora
    // anche il verde della prova qui sopra non varrebbe niente.
    const { container } = render(<button type="button" />)
    expect(await violazioni(container)).not.toEqual([])
  })
})
