import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Campo } from "./Campo"
import { Prova, Riga } from "./Riga"
import { type ClasseDiCielo, ScalaDelCielo, cosaSiVede, nomeDelCielo } from "./ScalaDelCielo"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Asse, coordinataDa, coordinate, numero, t } from "./i18n"
import { CAMPO_E_BOTTONE } from "./inLinea"

type Posto = components["schemas"]["PlaceOut"]

/**
 * Un sito: come lo si compila, come lo si cerca, che cielo ha.
 *
 * Sta in un modulo suo perche' lo fanno in due -- il primo avvio, dove il sito **nasce**, e la
 * sezione *Il sito* delle Impostazioni, dove si **corregge**. Le regole qui sotto sono le stesse
 * nei due posti, e scritte due volte una delle due sarebbe invecchiata da sola.
 *
 * - **La strada manuale e' sempre aperta**, non solo quando la ricerca fallisce: un sito buio
 *   puo' non avere rete, ed e' proprio dove si osserva. Per questo il **nome e' un campo suo**:
 *   prenderlo dalla casella di ricerca lascerebbe senza nome proprio chi non cerca.
 * - **Una coordinata scritta a mano la rilegge `coordinataDa`**, non `Number`: il segnaposto che
 *   l'app propone a un italiano porta la virgola, e `Number("46,4843")` e' `NaN`. Li' vive anche
 *   il campo vuoto, che non e' una coordinata: `Number("")` fa zero, e zero-zero e' un punto nel
 *   Golfo di Guinea.
 * - **Il motivo sta sotto il campo, e solo quando c'e' qualcosa da dire**: un campo ancora vuoto
 *   non e' sbagliato, e' solo vuoto. Spegnere il tasto e basta e' il difetto che questa schermata
 *   ha gia' pagato una volta.
 * - **Un cielo non dichiarato resta non dichiarato**: la classe 1 messa li' di partenza finirebbe
 *   nel database come una risposta.
 */

/** Cosa rende due posti **lo stesso posto**: il nome e il punto in cui sta. Col solo nome, una
 *  ricerca per "Verona" accendeva come scelte sia quella italiana sia quella di New York. */
const chiave = (p: Posto) => `${p.name}-${p.latitude}-${p.longitude}`

export type CampiDelSito = ReturnType<typeof useCampiDelSito>

export function useCampiDelSito(iniziale?: {
  nome: string
  lat: string
  lon: string
  cielo?: ClasseDiCielo
}) {
  const [nome, setNome] = useState(iniziale?.nome ?? "")
  const [lat, setLat] = useState(iniziale?.lat ?? "")
  const [lon, setLon] = useState(iniziale?.lon ?? "")
  const [cielo, setCielo] = useState<ClasseDiCielo | undefined>(iniziale?.cielo)
  // **Scelto adesso** o solo mostrato com'era. La classe che si vede correggendo un sito e' un
  // numero **derivato** dalla luminosita' salvata: rimandarla indietro la farebbe registrare come
  // una risposta ("scale"), spostando la misura al centro della classe e cancellando da dove
  // veniva -- un servizio, o uno strumento. E il backend, ricevendola, smette di riportare il
  // cielo quando le coordinate si spostano. Si manda solo cio' che l'utente ha toccato.
  const [cieloToccato, setCieloToccato] = useState(false)

  const fuoriScala = (scritto: string, asse: Asse, tetto: number) => {
    if (scritto.trim() === "") return undefined
    const n = coordinataDa(scritto, asse)
    if (!Number.isFinite(n)) return t("site.notANumber")
    if (Math.abs(n) <= tetto) return undefined
    return t("site.range", { tetto: numero(tetto) })
  }

  return {
    nome,
    lat,
    lon,
    cielo,
    setNome,
    setLat,
    setLon,
    setCielo: (c: ClasseDiCielo) => {
      setCieloToccato(true)
      setCielo(c)
    },
    fuoriScala,
    /** Il tasto guarda **anche** cio' che i campi stanno gia' dicendo: acceso sopra una
     *  latitudine di 120 gradi manderebbe una scrittura che il backend rifiuta, col motivo
     *  scritto a due centimetri da li'. */
    valido:
      nome.trim() !== "" &&
      Number.isFinite(coordinataDa(lat, "lat")) &&
      Number.isFinite(coordinataDa(lon, "lon")) &&
      fuoriScala(lat, "lat", 90) === undefined &&
      fuoriScala(lon, "lon", 180) === undefined,
    /** Cio' che si manda all'API. La **classe non si salva**: il backend ne ricava la luminosita'
     *  e registra quella. Assente se nessuno l'ha scelta **adesso**, anche quando a schermo ce
     *  n'e' una: quella e' il sito che si racconta, non una risposta. */
    corpo: () => ({
      name: nome.trim(),
      latitude: coordinataDa(lat, "lat"),
      longitude: coordinataDa(lon, "lon"),
      ...(cieloToccato && cielo !== undefined ? { bortle: cielo } : {}),
    }),
    prendiDa: (p: Posto) => {
      setNome(p.name)
      setLat(String(p.latitude))
      setLon(String(p.longitude))
    },
  }
}

/** Nome, latitudine e longitudine. Le due coordinate stanno **sulla stessa riga**: sono una cosa
 *  sola, un punto sulla Terra, e incolonnate si compilano come due domande separate. */
export function CampiDelSito({ campi, id }: { campi: CampiDelSito; id: string }) {
  return (
    <>
      <Campo
        id={`${id}-name`}
        etichetta={t("site.name")}
        errore={
          campi.nome.trim() === "" && (campi.lat.trim() !== "" || campi.lon.trim() !== "")
            ? t("site.nameNeeded")
            : undefined
        }
      >
        <input
          className="as-campo-modulo__input"
          id={`${id}-name`}
          onChange={(e) => campi.setNome(e.target.value)}
          placeholder={t("site.namePlaceholder")}
          value={campi.nome}
        />
      </Campo>
      <div style={{ display: "flex", gap: "var(--spazio-3)", flexWrap: "wrap" }}>
        <Campo
          id={`${id}-lat`}
          etichetta={t("site.lat")}
          errore={campi.fuoriScala(campi.lat, "lat", 90)}
          tetto="var(--misura-coordinata)"
        >
          <input
            className="as-campo-modulo__input as-campo-modulo__input--cifre"
            id={`${id}-lat`}
            inputMode="decimal"
            onChange={(e) => campi.setLat(e.target.value)}
            placeholder={t("site.latPlaceholder")}
            value={campi.lat}
          />
        </Campo>
        <Campo
          id={`${id}-lon`}
          etichetta={t("site.lon")}
          errore={campi.fuoriScala(campi.lon, "lon", 180)}
          tetto="var(--misura-coordinata)"
        >
          <input
            className="as-campo-modulo__input as-campo-modulo__input--cifre"
            id={`${id}-lon`}
            inputMode="decimal"
            onChange={(e) => campi.setLon(e.target.value)}
            placeholder={t("site.lonPlaceholder")}
            value={campi.lon}
          />
        </Campo>
      </div>
    </>
  )
}

/** Che cielo hai: la scala, cosa ci si vede, e che si puo' non rispondere.
 *
 * Senza la riga di cosa si vede la scala sarebbe nove numeri senza significato; senza quella che
 * dice che e' facoltativa, nove voci sembrano una domanda obbligatoria e chi non sa che cielo ha
 * si ferma a indovinare. */
export function SceltaDelCielo({
  cielo,
  onScegli,
  facoltativo = true,
}: {
  cielo: ClasseDiCielo | undefined
  onScegli: (c: ClasseDiCielo) => void
  facoltativo?: boolean
}) {
  return (
    <>
      <p className="as-soprattitolo">{t("sky.label")}</p>
      <ScalaDelCielo scelta={cielo} onScegli={onScegli} />
      {cielo !== undefined && (
        <Avviso
          esito="neutro"
          titolo={t("sky.chosen", { n: numero(cielo), cielo: nomeDelCielo(cielo) })}
        >
          {cosaSiVede(cielo)}
        </Avviso>
      )}
      {facoltativo && <p className="as-campo-modulo__aiuto">{t("sky.optional")}</p>}
    </>
  )
}

/** Cercare il posto per nome.
 *
 * **Non si distingue "non trovato" da "non ho potuto cercare"**, perche' l'API non lo distingue:
 * senza rete `GET /places` risponde 200 con elenco vuoto, di proposito. Ma un **guasto** non e'
 * un elenco vuoto e non si traveste da "nessun posto": manderebbe a correggere un nome giusto. */
export function CercaIlPosto({
  id,
  onScegli,
  aMano,
}: {
  id: string
  onScegli: (p: Posto) => void
  /** Dove portare chi la rete non ce l'ha. Il guasto porta **dentro di se'** cosa farci:
   *  riprovare, o passare alla strada che non dipende dalla rete -- staccati, quei due gesti
   *  sarebbero da cercare proprio mentre qualcosa non ha funzionato. */
  aMano?: () => void
}) {
  const [domanda, setDomanda] = useState("")
  const [trovati, setTrovati] = useState<Posto[]>()
  const [postoScelto, setPostoScelto] = useState<string>()
  const [rotta, setRotta] = useState(false)

  const cerca = async () => {
    const { data, error } = await api.GET("/api/v1/places", {
      params: { query: { q: domanda } },
    })
    setRotta(Boolean(error))
    setTrovati(error ? undefined : data.items)
  }

  return (
    <>
      <div style={CAMPO_E_BOTTONE}>
        <Campo cresce="var(--misura-cerca)" etichetta={t("site.searchLabel")} id={id}>
          <input
            className="as-campo-modulo__input"
            id={id}
            onChange={(e) => setDomanda(e.target.value)}
            type="search"
            value={domanda}
          />
        </Campo>
        <Bottone disabled={domanda.trim() === ""} onClick={() => void cerca()}>
          {t("site.search")}
        </Bottone>
      </div>

      {trovati?.length === 0 && <p className="as-cerca__niente">{t("site.none")}</p>}
      {trovati && trovati.length > 0 && (
        <div className="as-carta as-carta--alta">
          <div className="as-carta__corpo as-carta__corpo--stretto">
            <ul className="as-elenco">
              {trovati.map((p) => (
                <li key={chiave(p)}>
                  <Riga
                    dettagli={<Prova>{coordinate(p.latitude, p.longitude)}</Prova>}
                    nome={p.name}
                    stato={postoScelto === chiave(p) ? "risposta" : undefined}
                  >
                    {postoScelto === chiave(p) ? (
                      <span className="as-stato as-stato--buono">{t("site.chosen")}</span>
                    ) : (
                      <Bottone
                        nome={t("site.chooseOne", { nome: p.name })}
                        piccolo
                        onClick={() => {
                          setPostoScelto(chiave(p))
                          onScegli(p)
                        }}
                      >
                        {t("site.choose")}
                      </Bottone>
                    )}
                  </Riga>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {rotta && (
        <Avviso
          azioni={
            <>
              <Bottone piccolo onClick={() => void cerca()}>
                {t("action.retry")}
              </Bottone>
              {aMano && (
                <Bottone piccolo verso="nudo" onClick={aMano}>
                  {t("site.writeByHand")}
                </Bottone>
              )}
            </>
          }
          esito="allarme"
          titolo={t("site.searchFailedTitle")}
        >
          {t("site.searchFailed")}
        </Avviso>
      )}
    </>
  )
}
