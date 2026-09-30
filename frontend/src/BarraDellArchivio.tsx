import { type ReactNode, useEffect, useRef, useState } from "react"

import { Campo, EtichettaDiGruppo } from "./Campo"
import type { components, operations } from "./api/schema"
import { type Chiave, numero, t } from "./i18n"
import { costellazione, inOrdineDiNome } from "./costellazioni"

/**
 * La **barra dell'Archivio**: cerca, le tendine, ordina, e quanti ne hai trovati.
 *
 * - **Qui non si filtra niente.** Ogni controllo scrive nell'indirizzo, e chi disegna la pagina
 *   chiede al backend: cercare fra le cento righe gia' scaricate troverebbe solo quelle, e un
 *   archivio di seicento oggetti direbbe "non trovato" mentendo.
 * - **Le tendine offrono cio' che l'archivio ha**, non cio' che il catalogo conosce: l'elenco
 *   arriva gia' fatto dalla rotta.
 * - **La ricerca aspetta un attimo prima di partire.** Chi scrive `m31` batte tre tasti, e tre
 *   domande al backend per una parola sono due giri buttati: il campo tiene cio' che scrivi e lo
 *   consegna quando ti fermi, cosi' quello che vedi scritto e' sempre quello che hai battuto.
 * - **Mentre la risposta arriva la barra lo dice**, e lo **dichiara** (`aria-busy`): sotto ci
 *   sono ancora le righe e la conta di prima, e senza un segno l'utente le prenderebbe per la
 *   risposta a cio' che ha appena chiesto. Il segno sta sul **campo** e sulle **tendine** e non
 *   sulle righe, per due ragioni: le righe possono essere **zero** -- ed e' li' che serve di piu',
 *   perche' resta a schermo lo stato vuoto di prima -- e nel foglio i modificatori delle righe
 *   fanno altro, col perche' per esteso accanto alla tendina qui sotto. Niente si spegne mentre
 *   si aspetta: cambiare idea a meta' attesa e' legittimo.
 */

/** Cosa offrono le tendine, come la rotta le manda. */
export type ScelteDellaBarra = components["schemas"]["ArchiveChoices"]

/** I tre ordini, **presi dall'API**: e' il backend a ordinare, e i suoi sono quelli veri. Scritto
 *  a mano qui sarebbe un secondo posto dove decidere quali ordini esistono, e un refuso
 *  compilerebbe. */
export type Ordine = NonNullable<
  NonNullable<operations["archive_page"]["parameters"]["query"]>["sort"]
>

/** Cosa stai guardando: i valori che vivono nell'indirizzo, tolta la vista. */
export type Criteri = {
  q: string
  catalog: string
  constellation: string
  filter: string
  /** `SOLO_MOSAICI` o vuoto: nell'indirizzo come gli altri, cosi' un elenco di soli mosaici si
   *  manda a qualcuno. */
  mosaic: string
  sort: Ordine
}

/** Il valore che dice "solo i mosaici", nell'indirizzo e nella tendina. */
export const SOLO_MOSAICI = "1"

/** Quante righe ha trovato, divise come le manda la rotta: un mosaico non e' un oggetto. */
export type Trovati = components["schemas"]["ArchiveFound"]

/** I tre ordini con la parola che si legge, e **l'elenco di chi li conosce**: chi legge
 *  l'indirizzo si fa dire da qui quali esistono, invece di riscriverne la lista. */
export const ORDINI: { chiave: Ordine; testo: Chiave }[] = [
  { chiave: "name", testo: "archive.sort.name" },
  { chiave: "hours", testo: "archive.sort.hours" },
  { chiave: "frames", testo: "archive.sort.frames" },
]

export function BarraDellArchivio({
  criteri,
  scelte,
  trovati,
  aspetta,
  onCriteri,
  children,
}: {
  criteri: Criteri
  scelte: ScelteDellaBarra
  /** Quanti ne sono stati trovati, o `null` quando non lo sappiamo -- dopo una richiesta
   *  andata in errore, per esempio. Zero sarebbe l'unica risposta che sappiamo falsa. */
  trovati: Trovati | null
  /** Le righe sotto sono ancora quelle di prima e la risposta sta arrivando. */
  aspetta: boolean
  onCriteri: (cambio: Partial<Criteri>) => void
  /** L'interruttore fra le due viste: il disegno lo mette in questa riga, ma non e' un criterio
   *  -- non stringe l'elenco -- quindi lo compone chi disegna la pagina. */
  children?: ReactNode
}) {
  return (
    <div className="as-barra" aria-busy={aspetta}>
      {children}
      <Cerca scritto={criteri.q} aspetta={aspetta} onScritto={(q) => onCriteri({ q })} />
      <Tendina
        id="archivio-catalogo"
        etichetta="archive.filter.catalog"
        tutti="archive.filter.catalog.any"
        valore={criteri.catalog}
        voci={scelte.catalogs}
        aspetta={aspetta}
        onScelto={(catalog) => onCriteri({ catalog })}
      />
      <Tendina
        id="archivio-costellazione"
        etichetta="archive.filter.constellation"
        tutti="archive.filter.constellation.any"
        valore={criteri.constellation}
        voci={inOrdineDiNome(scelte.constellations)}
        nome={costellazione}
        aspetta={aspetta}
        onScelto={(constellation) => onCriteri({ constellation })}
      />
      <Tendina
        id="archivio-filtro"
        etichetta="archive.filter.filter"
        tutti="archive.filter.filter.any"
        valore={criteri.filter}
        voci={scelte.filters}
        aspetta={aspetta}
        onScelto={(filter) => onCriteri({ filter })}
      />
      <Tendina
        id="archivio-mosaici"
        etichetta="archive.filter.mosaic"
        tutti="archive.filter.mosaic.any"
        valore={criteri.mosaic}
        voci={scelte.mosaics ? [SOLO_MOSAICI] : []}
        nome={() => t("archive.filter.mosaic.only")}
        aspetta={aspetta}
        onScelto={(mosaic) => onCriteri({ mosaic })}
      />
      <div className="as-barra__coda">
        <div className="as-barra__gruppo">
          <EtichettaDiGruppo>{t("archive.sort")}</EtichettaDiGruppo>
          {/* Niente segno d'attesa qui: nel foglio `as-segmentato--caricamento` mette
              `pointer-events: none` sulle voci, che spegne il mouse e **non** la tastiera. Un
              controllo morto per meta' delle mani e' peggio di uno vivo. Segnalato a Design. */}
          <div className="as-segmentato" role="group" aria-label={t("archive.sort")}>
            {ORDINI.map((o) => (
              <button
                key={o.chiave}
                type="button"
                className="as-segmentato__voce"
                aria-pressed={criteri.sort === o.chiave}
                onClick={() => onCriteri({ sort: o.chiave })}
              >
                {t(o.testo)}
              </button>
            ))}
          </div>
        </div>
        {/* Dopo un errore non sappiamo quanti siano, e zero sarebbe l'unica risposta che
            sappiamo falsa. **Si dice**, non si tace: togliere la conta accorcerebbe la coda --
            che sta a destra -- e i tre bottoni dell'ordine salterebbero sotto le dita nello
            stesso istante in cui uno di loro e' stato appena premuto. */}
        <span className="as-barra__conta">{laConta(trovati)}</span>
      </div>
    </div>
  )
}

/** Quanti ne sono stati trovati, come si legge, e "non so quanti" quando la risposta non e'
 *  arrivata. Un mosaico non si chiama oggetto: *3 oggetti e 1 mosaico*, e i mosaici si tacciono
 *  quando non ce ne sono. */
function laConta(trovati: Trovati | null) {
  if (trovati === null) return t("archive.count.unknown")
  const { objects: oggetti, mosaics: mosaici } = trovati
  const diOggetti = t("archive.count", { n: numero(oggetti) })
  if (mosaici === 0) return diOggetti
  const diMosaici = t("archive.count.mosaics", { n: numero(mosaici) })
  return oggetti === 0 ? diMosaici : t("archive.count.and", { prima: diOggetti, dopo: diMosaici })
}

/** Il campo di ricerca. Tiene cio' che scrivi e lo consegna quando ti fermi: senza, ogni tasto
 *  sarebbe un giro di rete, e la riga sotto ballerebbe mentre batti. */
function Cerca({
  scritto,
  aspetta,
  onScritto,
}: {
  scritto: string
  aspetta: boolean
  onScritto: (q: string) => void
}) {
  const [testo, setTesto] = useState(scritto)

  // Chi chiama passa una funzione nuova a ogni suo disegno, e il genitore si ridisegna anche
  // mentre aspetta: senza fermarla qui, l'attesa ripartirebbe da capo a ogni suo giro e una
  // ricerca su rete lenta non partirebbe mai. L'effetto dipende da cio' che si e' scritto, non
  // dall'identita' di chi la riceve.
  const consegna = useRef(onScritto)
  useEffect(() => {
    consegna.current = onScritto
  })

  // `scritto` cambia anche da fuori -- il tasto indietro, un collegamento aperto -- e allora il
  // campo deve seguirlo: e' l'indirizzo a dire cosa stai guardando, non questo stato. Ma cambia
  // **anche per colpa nostra**, un attimo dopo ogni consegna, e fra i due momenti ci sta un tasto:
  // riallinearsi a quel ritorno lo cancellerebbe in silenzio. Si segue solo cio' che dice una cosa
  // diversa da cio' che abbiamo appena consegnato.
  const consegnato = useRef(scritto)
  useEffect(() => {
    if (scritto === consegnato.current) return
    consegnato.current = scritto
    setTesto(scritto)
  }, [scritto])

  useEffect(() => {
    if (testo === scritto) return
    const quando = setTimeout(() => {
      consegnato.current = testo
      consegna.current(testo)
    }, 250)
    return () => clearTimeout(quando)
  }, [testo, scritto])

  // Solo `as-barra__cerca`: `as-cerca` nel foglio e' il campo **con i suggerimenti** (`combobox`
  // piu' `listbox`), che qui non ci sono, e col suo `max-width` piu' largo cancellerebbe il tetto
  // che la barra da' al campo. Segnalato a Design.
  return (
    <div className="as-barra__cerca">
      <Campo id="archivio-cerca" etichetta={t("archive.search")} aspetta={aspetta}>
        <input
          className="as-campo__input"
          id="archivio-cerca"
          type="search"
          placeholder={t("archive.search.placeholder")}
          value={testo}
          onChange={(e) => setTesto(e.target.value)}
        />
      </Campo>
    </div>
  )
}

/** Una tendina che stringe l'elenco. Non compare se non c'e' niente da scegliere: una tendina con
 *  la sola voce "tutti" e' un controllo che promette di fare qualcosa e non fa niente. */
function Tendina({
  id,
  etichetta,
  tutti,
  valore,
  voci,
  nome = (v) => v,
  aspetta,
  onScelto,
}: {
  id: string
  etichetta: Chiave
  tutti: Chiave
  valore: string
  voci: string[]
  /** Come si legge una voce: il suo valore, se non e' una parola dell'app. */
  nome?: (voce: string) => string
  aspetta: boolean
  onScelto: (scelto: string) => void
}) {
  if (voci.length === 0) return null
  return (
    <div className="as-barra__campo">
      <Campo id={id} etichetta={t(etichetta)}>
        {/* Il segno dell'attesa sta **qui**, sui controlli, e non sulle righe: nel foglio
            `as-carta--caricamento` nasconde `as-carta__titolo` (dove sta il nome dell'oggetto:
            le carte resterebbero senza) e `as-tabella--caricamento` ha due sole regole, tutte e
            due sull'evidenziazione al passaggio, quindi **non dipinge niente** -- e le righe possono
            essere **zero**, ed e' proprio li' che il segno serve. `as-scelta--caricamento` anima
            e basta: non spegne il puntatore, quindi si puo' cambiare idea mentre si aspetta. */}
        <select
          className={aspetta ? "as-scelta as-scelta--caricamento" : "as-scelta"}
          id={id}
          value={valore}
          onChange={(e) => onScelto(e.target.value)}
        >
          <option value="">{t(tutti)}</option>
          {voci.map((v) => (
            <option key={v} value={v}>
              {nome(v)}
            </option>
          ))}
        </select>
      </Campo>
    </div>
  )
}
