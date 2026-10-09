import { useQuery } from "@tanstack/react-query"
import { Fragment, type ReactNode, useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { api } from "./api/client"
import { t } from "./i18n"

/**
 * **Sfogliare** le cartelle di una radice dei dati: dove sei, cosa c'e' dentro, e come si sale.
 *
 * Esiste separato da chi **registra** perche' sono due mestieri: qui si cammina in un albero e
 * non si scrive niente, di la' si guarda dentro una cartella e la si mette in archivio. Stavano
 * in un file solo, e quel file aveva due ragioni per cambiare.
 *
 * Vincoli non ovvi:
 *
 * - **Dove sei lo sa chi sfoglia, non la risposta**: appena si clicca un nome la richiesta parte
 *   e per un istante l'elenco nuovo non c'e' ancora. Ripiegando su cio' che si aveva in mano, in
 *   quella finestra lo schermo diceva `/data` e "Usa questa cartella" **registrava `/data`**
 *   mentre l'utente credeva di aver scelto `/data/Notti`. Su un NAS lento e' un secondo intero.
 * - **Un 409 e' una risposta, non un incidente**: riprovarlo tre volte vorrebbe dire sette
 *   secondi di elenco vuoto senza una parola.
 * - **La radice e' una briciola come le altre**: e' il primo pezzo di ogni percorso assoluto, e
 *   buttarla via lascia strade relative dentro una schermata che parla di percorsi assoluti.
 */

// Un percorso spezzato nei suoi pezzi, con la strada che porta a ognuno. Serve alle briciole:
// separare col carattere sbagliato e' il modo di far sparire il primo pezzo su Windows (`C:`),
// quindi si accettano tutti e due i versi di barra.
export function briciole(percorso: string): { nome: string; strada: string }[] {
  // Una radice non e' un pezzo vuoto da scartare: su Linux e sul NAS il percorso comincia con la
  // barra, e `split` la lascia davanti come pezzo vuoto. Scartandola sparivano tutte e due le
  // cose che porta -- la briciola `/`, che il disegno mostra, e la barra iniziale di ogni strada,
  // che faceva di `/volume1/foto` la strada **relativa** `volume1/foto`.
  const daRadice = /^[/\\]/.test(percorso)
  let strada = daRadice ? "/" : ""
  const dentro = percorso
    .split(/[/\\]+/)
    .filter(Boolean)
    .map((nome) => {
      strada = strada === "" ? nome : strada === "/" ? `/${nome}` : `${strada}/${nome}`
      return { nome, strada }
    })
  return daRadice ? [{ nome: "/", strada: "/" }, ...dentro] : dentro
}

export function SfogliaCartelle({
  radice,
  onGuarda,
  scrivi,
  usa,
  dove = "wizard",
}: {
  radice: string
  /** Il testo del tasto che usa la cartella dove sei: al primo avvio dopo c'e' ancora Aggiungi,
   *  in Cambia percorso il clic sposta subito, e deve dirlo. */
  usa: string
  /** Prima parte degli id della pagina: il dialogo di Cambia percorso ne apre un secondo accanto a
   *  quello di Aggiungi, e due id uguali legherebbero un'etichetta all'elenco sbagliato. */
  dove?: string
  /** Guarda dentro la cartella dove si e' arrivati: e' l'altro mestiere, e lo fa chi registra. */
  onGuarda: (percorso: string) => void
  /** La strada a mano, che torna utile proprio quando l'elenco non arriva. */
  scrivi: ReactNode
}) {
  const [apri, setApri] = useState<string | undefined>(undefined)
  const qui = apri ?? radice
  const sfoglia = useQuery({
    queryKey: ["browse", apri ?? radice],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/folders/browse", {
        params: { query: apri === undefined ? {} : { path: apri } },
      })
      if (error) throw new Error(t("wizard.folders.lookFailed"))
      return data
    },
    retry: false,
  })

  return (
    <div className="as-sfoglia">
      <p className="as-soprattitolo as-soprattitolo--nudo" id={`${dove}-browse`}>
        {t("wizard.folders.choose")}
      </p>
      {/* Dove sei lo sa `apri`, non la risposta: appena si clicca un nome la query cambia chiave
          e `sfoglia.data` torna vuoto per un istante. Ripiegando sulla radice, in quella finestra
          lo schermo diceva `/data` e "Usa questa cartella" **registrava `/data`** mentre l'utente
          credeva di aver scelto `/data/Notti`. Su un NAS lento e' un secondo intero, e nessuno se
          ne accorgerebbe. */}
      {/* Dove sei, **a pezzi**: un percorso lungo scritto di fila si legge tutto o niente, e a
          briciole si vede da dove si viene. L'ultimo pezzo e' quello in cui sei, e porta la
          classe che lo dice.
          **Per chi ascolta il percorso resta intero**, scritto una volta sola: questa riga e'
          anche la descrizione del tasto che registra, e un nome accessibile costruito dai pezzi
          si appiattisce senza separatori (`Sei in/dataNotti`), perche' i chevron sono
          decorazione. Quindi la frase la porta il testo nascosto, e le briciole -- che nessuno
          puo' cliccare -- non si sentono due volte. */}
      <p className="as-percorso" id={`${dove}-dove`}>
        <span className="as-solo-lettori">{`${t("wizard.folders.here")} ${qui}`}</span>
        {briciole(qui).map((pezzo, i, tutte) => (
          <Fragment key={pezzo.strada}>
            {i > 0 && (
              <span className="as-percorso__separa" aria-hidden="true">
                {"\u203A"}
              </span>
            )}
            <span
              aria-hidden="true"
              className={i === tutte.length - 1 ? "as-percorso__qui" : undefined}
            >
              {pezzo.nome}
            </span>
          </Fragment>
        ))}
      </p>
      {/* Si **entra** nelle cartelle, e si registra quella dove sei: cliccare un nome per
          sondarlo lasciava vedere un livello solo, e la radice dei dati -- dove le foto stanno
          spesso -- non si poteva indicare affatto.
          Bloccato quando per questa cartella non si ha ancora niente (`isPending`), non a ogni
          riletta: rileggendo, cio' che e' a schermo e' gia' quello giusto, e bloccare il tasto
          costava ~200 ms per livello su un NAS -- oltre un secondo in una discesa di sei. */}
      <div className="as-sfoglia__azioni">
        {/* tenue e non primario: il primario di questo passo e' *Aggiungi*, che registra.
            Guardare cosa c'e' dentro una cartella e' il gesto prima, non l'azione. */}
        <Bottone
          descrittoDa={`${dove}-dove`}
          onClick={() => onGuarda(qui)}
          disabled={sfoglia.isPending}
        >
          {usa}
        </Bottone>
        {sfoglia.data?.parent != null && (
          <Bottone verso="nudo" onClick={() => setApri(sfoglia.data?.parent ?? undefined)}>
            {t("wizard.folders.up")}
          </Bottone>
        )}
      </div>
      {/* L'elenco sta in una **scatola che scorre**: una cartella con duecento sottocartelle
          spingerebbe il piede della pagina fuori dallo schermo, e cio' che serve per andare
          avanti sparirebbe sotto l'elenco. */}
      {sfoglia.data?.folders.length === 0 ? (
        <p className="as-sfoglia__niente">{t("wizard.folders.empty")}</p>
      ) : (
        <ul className="as-sfoglia__elenco" aria-labelledby={`${dove}-browse`}>
          {sfoglia.data?.folders.map((c) => (
            <li key={c.path} className="as-sfoglia__voce">
              {/* Il posto dell'icona, vuoto finche' l'icona non c'e': la riga del foglio ha tre
                  colonne, e con due figli il nome cade nella prima e "Apri" si allarga a tutta
                  la riga, fino a uscire dal pozzo con un nome lungo. */}
              <span aria-hidden="true" />
              <span className="as-sfoglia__nome">{c.name}</span>
              {/* Il nome che si **sente** porta dentro quale cartella: a vista tutti i bottoni
                  si chiamano "Apri", e chi comanda a voce non ne distingue venti. */}
              <Bottone
                piccolo
                verso="nudo"
                nome={t("wizard.folders.openOne", { nome: c.name })}
                onClick={() => setApri(c.path)}
              >
                {t("wizard.folders.open")}
              </Bottone>
            </li>
          ))}
        </ul>
      )}
      {/* Un elenco che non arriva non puo' lasciare senza strade: si dice, e si torna a scrivere
          il percorso a mano -- che sul NAS e' scomodo, ma e' meglio di niente. */}
      {sfoglia.isError && (
        <>
          {/* Se l'elenco cade DOPO essere scesi, `Sali` sparisce insieme alla risposta: il
              ritorno alla radice sta **dentro** l'avviso, che e' dove lo si cerca. */}
          <Avviso
            esito="allarme"
            titolo={t("wizard.folders.browseFailedTitle")}
            azioni={
              <>
                <Bottone piccolo onClick={() => void sfoglia.refetch()}>
                  {t("action.retry")}
                </Bottone>
                {apri !== undefined && (
                  <Bottone piccolo verso="nudo" onClick={() => setApri(undefined)}>
                    {t("wizard.folders.backToRoot")}
                  </Bottone>
                )}
              </>
            }
          >
            {t("wizard.folders.browseFailed")}
          </Avviso>
          {scrivi}
          <p className="as-campo-modulo__aiuto">{t("wizard.folders.pathHelp")}</p>
        </>
      )}
    </div>
  )
}
