/**
 * Il banco delle prove che disegnano una pagina: risposte finte dell'API, e la pagina montata.
 *
 * Sta qui e non dentro un file di prova perche' lo usano in due -- la prova della pagina e
 * quella di accessibilita' -- e scriverlo due volte sarebbe lo stesso pezzo in due case.
 * Non e' un `*.test.tsx`, quindi vitest non lo raccoglie come suite.
 *
 * I due vincoli non ovvi, imparati tutti e due vedendo il banco rosso per la ragione sbagliata:
 *
 * - **Il client cattura `fetch` quando nasce**, e nasce all'import di `api/client`. Stubbare il
 *   globale dopo non cambia niente: qui si stubba PRIMA e si importa la pagina dopo, coi moduli
 *   azzerati.
 * - **jsdom non porta ne' `fetch` ne' `Request`**: restano quelli di Node, e quello di Node
 *   rifiuta un indirizzo relativo mentre quello del browser lo risolve sulla pagina. Il client
 *   ha `baseUrl: "/"` apposta, quindi il banco rimette il comportamento del browser invece di
 *   piegare il codice per farsi dire di si'. Provato togliendolo: senza, tutte e due le prove
 *   tornano rosse con "Failed to parse URL from /api/v1/review".
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react"
import axe from "axe-core"
import { vi } from "vitest"

import type { components } from "../src/api/schema"

export const SALUTE = {
  status: "ok",
  api_version: "0.1.0",
  schema_tables: 22,
  data_root: null,
  catalog_entries: 22080,
  catalog_version: "20260825-6ac5806f",
}

/** La risposta di `/api/v1/settings`, col timbro del primo avvio o senza.
 *
 * Sta qui perche' la chiedono **tutte** le prove che disegnano la pagina: l'app la interroga
 * sempre, prima di decidere se mostrare il primo avvio o se stessa. Scriverla in ogni file
 * sarebbe lo stesso pezzo in tre case -- e un banco che non la prevede fa cadere le prove per
 * la ragione sbagliata. */
export function impostazioni(fatto: boolean, manca?: readonly string[]) {
  return {
    values: {
      user_name: null,
      language: "it",
      onboarding_done_at: fatto ? "2026-09-14T12:00:00Z" : null,
      sky_service_key: null,
      astap_path: null,
      meteoblue_key: null,
      weather_model: "best_match",
    },
    wizard_done: fatto,
    // Cosa manca si puo' dire, perche' e' la risposta che **una scrittura** restituisce: chi
    // scrive il percorso del solver guarda li' per sapere se ha indovinato.
    missing: manca ?? (fatto ? [] : ["no_active_site"]),
  }
}

const ORIGINE = "http://localhost:3000"
const RequestVero = globalThis.Request

const richieste: string[] = []
const scritte: { url: string; metodo: string; corpo: unknown }[] = []

/** Le **scritture** che la pagina ha fatto: indirizzo, metodo e corpo.
 *
 * `chiamate()` non basta a provare che un campo sia stato salvato: la stessa rotta si legge e si
 * scrive, quindi un test che guarda solo l'indirizzo e' verde anche se la pagina non ha scritto
 * niente. Il corpo si legge da una **copia** della richiesta, perche' il corpo vero lo consuma
 * chi la manda. */
export function scritture() {
  return [...scritte]
}

/** Le rotte che la pagina ha davvero chiesto, in ordine.
 *
 * Serve a distinguere "il risultato si vede" da "il dato e' stato letto": un test che guarda
 * solo cio' che compare a schermo puo' essere verde anche quando l'app ignora del tutto la
 * risposta -- succede ogni volta che il ramo giusto e quello sbagliato mostrano la stessa cosa. */
export function chiamate() {
  return [...richieste]
}

/** Cosa il cielo ha trovato in un gruppo, quando al test non interessa: niente, e niente da guardare. */
export const SENZA_SOGGETTI = { found: [], not_found: 0, not_yet: 0 }

/** Quali campi chiede la scheda di ogni genere: nell'app li manda il backend con la pagina
 *  dell'attrezzatura. Ci sono **tutti e otto** i generi, anche quelli che nessuna prova possiede:
 *  e' esattamente cio' che serve per scriverne il primo. Sta nel banco perche' la guardano in due
 *  -- la prova dell'Attrezzatura e quella di accessibilita' -- e scritta due volte, il giorno che
 *  il backend sposta un campo, una delle due resterebbe a dire un'altra cosa. */
export const SCHEDE: components["schemas"]["GearList"]["cards"] = {
  optics: ["brand", "model", "aperture_mm", "focal_mm", "weight_kg", "notes"],
  camera: ["brand", "model", "camera_type", "pixel_size_um", "weight_kg", "notes"],
  mount: ["brand", "model", "payload_kg", "weight_kg", "notes"],
  reducer: ["brand", "model", "reducer_factor", "weight_kg", "notes"],
  filter_wheel: ["brand", "model", "slots", "weight_kg", "notes"],
  guide_scope: ["brand", "model", "weight_kg", "notes"],
  guide_camera: ["brand", "model", "weight_kg", "notes"],
  focuser: ["brand", "model", "weight_kg", "notes"],
}

/** Una **lettura** com'e' fatta davvero, tipata dallo schema: un campo che il backend aggiunge o
 *  cambia fa rosso qui invece di passare inosservato. I numeri sono zero e ogni prova accende
 *  quelli che le servono. Sta nel banco perche' la guardano in due -- la prova della sezione e
 *  quella di accessibilita' -- e scritta due volte sarebbe lo stesso pezzo in due case. */
export const LETTURA: components["schemas"]["ScanRunOut"] = {
  id: 3,
  folder_id: 1,
  folder_path: "D:\\Astro\\2025",
  folder_retired: false,
  started_at: "2026-09-20T21:00:00.000Z",
  ended_at: "2026-09-20T21:02:14.000Z",
  duration_s: 134,
  status: "ok",
  reason: null,
  found: 0,
  new: 0,
  unchanged: 0,
  duplicates: 0,
  missing: 0,
  skipped: 0,
  errors: 0,
  online_only: 0,
  unreadable_dirs: [],
  hidden_dirs: [],
  linked_dirs: [],
  skipped_by_reason: [],
}

/** Le rotte che il banco conosce. Una rotta non prevista **fallisce**: un banco che risponde a
 *  tutto direbbe di si' anche a una chiamata che non doveva partire. */
let mappaCorrente: Record<string, Voce> = {}
/** Una risposta del banco. `attesa` la trattiene finche' la promessa non si risolve: il server
 *  vero ci mette qualche millisecondo, e cio' che la pagina fa **nel frattempo** si vede solo cosi'. */
export type Voce = { stato: number; corpo: unknown; attesa?: Promise<unknown> }

/** Cambia cio' che il banco risponde **senza rimontare la pagina**: serve a provare il dopo di
 *  una scrittura (timbro scritto -> le impostazioni ora dicono un'altra cosa). Non si puo' fare
 *  richiamando `rispondi`, perche' il client ha gia' catturato il `fetch` di allora. */
export function cambia(mappa: Record<string, Voce>) {
  mappaCorrente = mappa
}

/** Lo stato del lavoro quando non sta girando niente: la barra in alto lo chiede su ogni pagina
 *  dell'app, quindi le prove che la disegnano lo dichiarano. Sta qui perche' e' lo stesso pezzo
 *  in cinque file -- ma **non** si inietta da solo in ogni mappa: il banco rifiuta cio' che non
 *  e' dichiarato, ed e' cosi' che una prova si accorge se il primo avvio si mette a interrogare
 *  la spina prima del timbro. Chi prova il pulsante lo sovrascrive. */

export const FERMO = {
  worker: { state: "idle", stage: null, started_at: null, ended_at: null, stages: [] },
  scan: null,
  pending: {},
  action: "start",
}

export const SPINA = { "/api/v1/pipeline/status": { stato: 200, corpo: FERMO } }

/** Un sito di casa come lo manda `GET /api/v1/sites`, tipato dallo schema. */
export const SITO_DI_CASA: components["schemas"]["SiteOut"] = {
  id: 1,
  name: "Vicenza",
  latitude: 45.5455,
  longitude: 11.5354,
  elevation_m: 39,
  elevation_source: "declared",
  timezone: "Europe/Rome",
  sky_sqm: 20.8,
  sky_source: "measured",
  bortle: 4,
  is_default: true,
  nights: 0,
  unknown: [],
}

/** Il cielo di stanotte **senza sito**: lo stato quieto del piede della barra, che vive nello
 *  scheletro e quindi parla in ogni pagina. Si sparge come `SPINA`, e per la stessa ragione:
 *  **non** si inietta da solo, cosi' una prova puo' ancora accorgersi se `/tonight` viene chiesta
 *  dove non doveva -- per esempio dentro il primo avvio, dove il piede non e' montato. */
export const STANOTTE = {
  "/api/v1/tonight": { stato: 200, corpo: { night: null, site: null, moon: null, sky_bands: [], weather: null } },
  // Stanotte chiede i siti per la scelta; uno solo non apre la scelta, quindi non smentisce il
  // "senza sito" di sopra.
  "/api/v1/sites": { stato: 200, corpo: { items: [SITO_DI_CASA], total: 1, limit: 50, offset: 0 } },
}

export function rispondi(mappa: Record<string, Voce>) {
  mappaCorrente = mappa
  vi.stubGlobal(
    "Request",
    class extends RequestVero {
      constructor(input: RequestInfo | URL, init?: RequestInit) {
        super(typeof input === "string" && input.startsWith("/") ? ORIGINE + input : input, init)
      }
    },
  )
  vi.stubGlobal("fetch", (input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : (input as Request).url
    richieste.push(url)
    if (typeof input !== "string" && "method" in input && input.method !== "GET") {
      const metodo = input.method
      void input
        .clone()
        .json()
        .then(
          (corpo: unknown) => scritte.push({ url, metodo, corpo }),
          () => scritte.push({ url, metodo, corpo: null }),
        )
    }
    // Una rotta si puo' dichiarare col metodo davanti ("PATCH /api/v1/settings"): senza, la
    // stessa rotta non puo' rispondere BENE in lettura e MALE in scrittura -- e quella e' la
    // forma di meta' delle regole, perche' l'app legge le impostazioni per decidere cosa
    // mostrare e le scrive quando l'utente risponde. Le voci col metodo vanno dichiarate prima.
    const metodo = typeof input === "string" ? "GET" : (input as Request).method
    const voci = Object.entries(mappaCorrente)
    // Le voci col metodo vincono SEMPRE, in qualunque ordine siano dichiarate: farle dipendere
    // dalla posizione significa che aggiungere una riga altrove cambia in silenzio cosa risponde
    // il banco -- ed e' gia' successo, con un PATCH che riceveva il 200 della GET.
    const scelta =
      voci.find(([r]) => r.includes(" ") && metodo === r.slice(0, r.indexOf(" ")) && url.includes(r.slice(r.indexOf(" ") + 1))) ??
      voci.find(([r]) => !r.includes(" ") && url.includes(r))
    const voce = scelta?.[1]
    if (!voce) return Promise.reject(new Error(`rotta non prevista dal banco: ${url}`))
    return Promise.resolve(voce.attesa).then(
      () =>
        new Response(JSON.stringify(voce.corpo), {
          status: voce.stato,
          headers: { "Content-Type": "application/json" },
        }),
    )
  })
}

/** La pagina montata, coi moduli azzerati: `api/client` nasce adesso e cattura il `fetch` del
 *  banco invece di quello vero. */
export async function disegna() {
  vi.resetModules()
  const { App } = await import("../src/App")
  // `retry: false`: senza, la prova sull'errore aspetterebbe i tentativi di react-query, e il
  // rosso arriverebbe come un timeout invece che come l'asserzione che e' fallita davvero.
  const dati = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={dati}>
      <App />
    </QueryClientProvider>,
  )
}

/** Apre l'app, va su *Da confermare* e torna la sezione chiesta.
 *
 * Sta qui perche' ogni sezione della pagina fara' gli stessi due passi: scriverli in ogni file di
 * prova sarebbe lo stesso pezzo in undici case. */
export async function vaiASezione(nome: RegExp) {
  await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
  return screen.findByRole("region", { name: nome })
}

/** La riga su cui si sta rispondendo.
 *
 * Si cerca **dentro la riga** e non in tutta la sezione: un nome compare legittimamente due volte
 * -- il filtro gia' a posto che si chiama come un modello, il candidato che si chiama come
 * l'oggetto -- e una prova che pesca in giro cade su una pagina sana. Le righe annidate (i
 * candidati dentro l'oggetto) non ingannano: `find` torna la prima in ordine di documento, che e'
 * sempre quella che le contiene. */
export function riga(sezione: HTMLElement, nome: string) {
  const voci = within(sezione).getAllByRole("listitem")
  const trovata = voci.find((v) => v.textContent?.startsWith(nome))
  if (!trovata) throw new Error(`nessuna riga che comincia con "${nome}"`)
  return trovata
}

/** Cio' che a schermo **non passa dal suo mattone**: i controlli scritti a mano e i pezzi di un
 * campo lasciati senza involucro.
 *
 * Sta nel banco perche' lo guardano due superfici -- il primo avvio e *Da confermare* -- e scritto
 * due volte sarebbe il doppione che i mattoni esistono per togliere.
 *
 * **Si parte dagli elementi, non dalle classi.** Cercare gli orfani fra chi porta gia'
 * `.as-campo__input` vedrebbe solo chi il mattone lo usa a meta': un `<label>` con un `<input>`
 * nudi -- che e' esattamente cio' che questa fetta ha tolto da sette campi -- non ha nessuna di
 * quelle classi, non sarebbe fra i trovati, e la prova tornerebbe verde sulla regressione che
 * deve impedire.
 *
 * - **Un controllo senza la sua classe** (`.as-campo__input`, `.as-campo__area`, `.as-scelta`,
 *   `.as-bottone`) non ha ne' l'altezza dei mattoni ne' gli stati: si vede subito a schermo, ma
 *   nessuna prova cadrebbe.
 * - **Un campo senza `.as-campo`** non e' una griglia: l'etichetta e il controllo diventano due
 *   elementi affiancati, e lo stesso campo si dispone in due modi nella stessa pagina.
 *
 * Torna i **nomi** di cio' che ha trovato, non quanti sono: un elenco vuoto atteso si legge, un
 * numero no. */
export function fuoriDaiMattoni() {
  // Un gruppo di scelte e' ancora `input[type=radio]` dentro un `fieldset`, e nel foglio **non
  // esiste** una classe per un radio: il design lo vuole segmentato, che e' un cambio di
  // controllo e ha la sua fetta in coda. Finche' e' cosi', un radio e la parola che lo
  // accompagna non sono qualcosa che qualcuno ha dimenticato di vestire.
  const spunta = (e: Element | null) =>
    e instanceof HTMLInputElement && (e.type === "radio" || e.type === "checkbox")
  const daScelta = (e: Element) =>
    spunta(e) ||
    // la parola della scelta, che la contenga o che la nomini: `<label>` con dentro il controllo,
    // oppure accanto a lui con `htmlFor`
    e.querySelector("input[type=radio], input[type=checkbox]") !== null ||
    (e instanceof HTMLLabelElement && spunta(document.getElementById(e.htmlFor)))
  const nudi = [...document.querySelectorAll("input, textarea, select, button, label")].filter(
    (e) =>
      !daScelta(e) &&
      ![
        "as-campo__input",
        "as-campo__area",
        "as-scelta",
        "as-bottone",
        "as-campo__etichetta",
        // Le nove voci della scala del cielo: sono bottoni, ma non sono bottoni dell'app -- hanno
        // il loro mattone (`ScalaDelCielo`) e la loro classe nel foglio. Vestirle da `as-bottone`
        // vorrebbe dire dargli il bordo e il fondo di un'azione, che non sono.
        "as-bortle__voce",
        // I controlli del telaio, stessa ragione: la voce Altro del binario, la pastiglia di
        // Stanotte e il velo hanno la loro classe nel foglio (`51-telaio.css`), e da `as-bottone`
        // prenderebbero il bordo e il fondo di un'azione dentro il binario e la barra.
        "as-telaio__voce",
        "as-telaio__pastiglia",
        "as-telaio__velo",
        // Le voci di un segmentato -- le due viste dell'Archivio, i tre ordini: sono **una** scelta
        // fra poche, non tre azioni, e il foglio le veste da se' (bordo condiviso, quella accesa
        // piena). Vestirle da `as-bottone` darebbe tre pulsanti attaccati.
        "as-segmentato__voce",
      ].some((c) => e.classList.contains(c)),
  )
  const pezzi = document.querySelectorAll(".as-campo__etichetta, .as-campo__input, .as-scelta")
  // Fuori da `as-campo` c'e' una forma voluta: l'etichetta di un **gruppo** di controlli
  // (`EtichettaDiGruppo`), che nomina tre bottoni e non un campo -- un `as-campo` intorno le
  // darebbe la spaziatura di un campo che non c'e'. Dichiarata qui perche' questa guardia gira
  // **anche sull'Archivio**, dove quella forma vive.
  const orfani = [...pezzi].filter(
    (e) =>
      e.closest(".as-campo") === null &&
      !(e.classList.contains("as-campo__etichetta") && e.closest(".as-barra__gruppo")),
  )
  return [...nudi, ...orfani].map((e) => e.getAttribute("id") ?? e.textContent)
}

/** Quanti controlli ci sono da guardare. `fuoriDaiMattoni` torna vuoto anche su una pagina che di
 * campi e bottoni non ne ha nessuno: senza questo conto, una prova che non ha trovato la sua
 * schermata sarebbe verde per il motivo sbagliato. */
export function quantiControlli() {
  return document.querySelectorAll("input, textarea, select, button, label").length
}

/** I nomi delle tappe del binario del primo avvio, senza il segno ne' la parola per chi ascolta.
 *
 * Il `<li>` di una tappa contiene tre cose -- il segno (`aria-hidden`, una spunta o un numero), il
 * nome, e per la tappa fatta o corrente una parola che il segno non puo' dire a chi ascolta.
 * Leggere `textContent` le prenderebbe tutte e tre, e le prove che chiamano questa funzione
 * guardano **come si chiamano i passi**: quello sta nel suo pezzo. */
export function nomiDeiPassi() {
  return [...document.querySelectorAll(".as-passi__nome")].map((n) =>
    (n.firstChild?.textContent ?? "").trim(),
  )
}

export function pulisci() {
  cleanup()
  vi.unstubAllGlobals()
  richieste.length = 0
  scritte.length = 0
  mappaCorrente = {}
  // E l'indirizzo torna alla radice: le pagine sono indirizzi, quindi una prova che naviga
  // lascerebbe la prova dopo su un'altra pagina -- che e' un rosso difficile da spiegare.
  window.history.pushState({}, "", "/")
}

/** Le violazioni che axe trova in un pezzo di pagina, in forma leggibile: quando cade, il rosso
 *  dice **cosa** e' rotto invece di un conteggio da andare a interpretare. Sta qui perche' la
 *  guardia di accessibilita' vive in due file -- le pagine che si leggono e quelle dove si
 *  risponde -- e due copie di questa direbbero la stessa cosa in due modi. */
export async function violazioni(nodo: Element) {
  const esito = await axe.run(nodo, { resultTypes: ["violations"] })
  return esito.violations.map((v) => `${v.id}: ${v.help}`)
}
