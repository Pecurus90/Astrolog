import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Prova, Riga } from "./Riga"
import { CieloLetto } from "./ScalaDelCielo"
import { SchedaDelSito, TogliIlSito } from "./SchedaDelSito"
import { AzioniDelVuoto, NotaDelVuoto, Vuoto } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { coordinate, t } from "./i18n"

type Sito = components["schemas"]["SiteOut"]

/**
 * La sezione **Il sito**: da dove osservi, e che cielo ha.
 *
 * I campi e la scala del cielo stanno in `sito.tsx`, insieme al primo avvio; la carta che si
 * compila in `SchedaDelSito.tsx`. Qui c'e' cio' che e' della sezione:
 *
 * - **I siti sono piu' d'uno, e uno solo e' di casa**: e' quello che decide il fuso delle notti e
 *   la Luna che il piede della barra mostra. Gli altri servono alle uscite.
 * - **Il cielo si corregge**: cambia davvero -- un lampione nuovo, un quartiere che spegne -- e
 *   senza questa pagina si sceglieva una volta al primo avvio e restava li'.
 * - **Un sito che tiene delle notti non si toglie di nascosto**: la rotta rifiuta e dice quante,
 *   e quella frase si legge dove si e' premuto.
 */
export function Sito() {
  const cache = useQueryClient()
  const [daCorreggere, setDaCorreggere] = useState<Sito>()
  const [daAggiungere, setDaAggiungere] = useState(false)
  const [daTogliere, setDaTogliere] = useState<Sito>()
  const [casaRotta, setCasaRotta] = useState(false)

  const siti = useQuery({
    queryKey: ["sites"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/sites")
      if (error) throw new Error(t("settings.site.failed"))
      return data
    },
  })
  /** Dopo una scrittura: si rilegge l'elenco, e **solo se e' cambiato il sito di casa** anche il
   *  piede della barra. Quello sta fuori da questa pagina e tiene la sua risposta per un'ora --
   *  senza buttarla via, chi dichiara il sito qui continua a leggere "non so da dove osservi" fino
   *  a una ricarica (visto dal vivo). Ma **buttarla via sempre** costa: `GET /tonight` rifa' le
   *  effemeridi ed e' la rotta piu' cara che l'app abbia, mentre correggere un sito d'uscita non
   *  sposta di una virgola cio' che il piede mostra. */
  const rileggi = (toccaCasa: boolean) => {
    void siti.refetch()
    if (toccaCasa) void cache.invalidateQueries({ queryKey: ["tonight"] })
  }
  /** Quando a salvare e' stata **una scheda**: si rilegge, e quella scheda si chiude. Chiuderle
   *  anche su un gesto dell'elenco butterebbe via cio' che si stava scrivendo nell'altra. */
  const rinfresca = (toccaCasa: boolean) => {
    rileggi(toccaCasa)
    setDaCorreggere(undefined)
    setDaAggiungere(false)
  }
  const quanti = siti.data?.items.length ?? 0

  return (
    <>
      <section className="as-carta">
        <div className="as-carta__intestazione">
          <div>
            <h2 className="as-carta__titolo">{t("settings.site.title")}</h2>
            <p className="as-carta__domanda">{t("settings.site.what")}</p>
          </div>
          {quanti > 0 && !daAggiungere && (
            <div className="as-carta__azioni">
              <Bottone piccolo onClick={() => setDaAggiungere(true)}>
                {t("settings.site.add")}
              </Bottone>
            </div>
          )}
        </div>
        <div className="as-carta__corpo as-carta__corpo--stretto">
          {siti.isError && <Avviso esito="allarme">{t("settings.site.failed")}</Avviso>}
          {casaRotta && <Avviso esito="allarme">{t("settings.site.homeFailed")}</Avviso>}
          {quanti === 0 && !siti.isPending && !siti.isError && (
            <Nessuno onAggiungi={() => setDaAggiungere(true)} />
          )}
          {/* **Un sito di casa ci vuole**: la rotta che lo toglie non ne elegge un altro da sola
              (`backend/astrolog/api/sites.py`, `delete_site`) e `GET /tonight` senza quello non ha
              niente da dire -- il piede della barra torna a "non so da dove osservi" anche con
              altri siti in elenco. Chi l'ha tolto qui lo legge qui. */}
          {quanti > 0 && !siti.data?.items.some((s) => s.is_default) && (
            <Avviso esito="allarme" titolo={t("settings.site.noHomeTitle")}>
              {t("settings.site.noHome")}
            </Avviso>
          )}
          {quanti > 0 && (
            <ul className="as-elenco">
              {siti.data?.items.map((s) => (
                <li key={s.id}>
                  <Voce
                    onCorreggi={() => setDaCorreggere(s)}
                    onDiCasa={() => void diCasa(s, () => rileggi(true), setCasaRotta)}
                    onTogli={() => setDaTogliere(s)}
                    sito={s}
                  />
                </li>
              ))}
            </ul>
          )}
        </div>
        {quanti > 0 && (
          <div className="as-carta__piede as-carta__piede--prosa">{t("settings.site.keeps")}</div>
        )}
      </section>

      {daAggiungere && (
        <SchedaDelSito
          onAnnulla={() => setDaAggiungere(false)}
          // Il primo sito nasce di casa: quello il piede lo deve sapere, gli altri no.
          onSalvato={() => rinfresca(quanti === 0)}
          primo={quanti === 0}
        />
      )}
      {daCorreggere && (
        <SchedaDelSito
          // **La chiave e' il sito**: i campi nascono dal sito che la scheda riceve, e nascono una
          // volta sola. Senza, passando da *Correggi Cortina* a *Correggi Passo Giau* React tiene
          // lo stesso componente -- a schermo restano i valori di Cortina, e il salvataggio li
          // scrive sull'altro sito.
          key={daCorreggere.id}
          onAnnulla={() => setDaCorreggere(undefined)}
          onSalvato={() => rinfresca(daCorreggere.is_default)}
          onTogli={() => setDaTogliere(daCorreggere)}
          sito={daCorreggere}
        />
      )}
      {daTogliere && (
        <TogliIlSito
          onChiudi={() => setDaTogliere(undefined)}
          // Anche togliere si preme **dall'elenco**: si rilegge senza chiudere le schede, e si
          // chiude solo quella che stava correggendo il sito appena sparito.
          onTolto={() => {
            rileggi(daTogliere.is_default)
            if (daCorreggere?.id === daTogliere.id) setDaCorreggere(undefined)
          }}
          sito={daTogliere}
        />
      )}
    </>
  )
}

/** Eleggere il sito di casa. E' il gesto che decide il fuso di **tutte** le notti, quindi se non
 *  riesce si dice: ricaricare l'elenco e basta lo mostrerebbe identico, e chi ha premuto crederebbe
 *  di aver cambiato posto. */
async function diCasa(sito: Sito, poi: () => void, rotto: (si: boolean) => void) {
  const { error } = await api.POST("/api/v1/sites/{site_id}/default", {
    params: { path: { site_id: sito.id } },
  })
  rotto(Boolean(error))
  if (!error) poi()
}

/** Un sito nell'elenco: dove sta, che cielo ha, e se e' quello di casa. */
function Voce({
  sito,
  onCorreggi,
  onDiCasa,
  onTogli,
}: {
  sito: Sito
  onCorreggi: () => void
  onDiCasa: () => void
  onTogli: () => void
}) {
  return (
    <Riga
      dettagli={
        sito.is_default ? (
          <span className="as-stato as-stato--buono">{t("settings.site.home")}</span>
        ) : undefined
      }
      nome={sito.name}
      perche={
        <>
          <Prova>{coordinate(sito.latitude, sito.longitude)}</Prova> <CieloLetto bortle={sito.bortle} sqm={sito.sky_sqm} />
        </>
      }
      stato={sito.is_default ? "risposta" : undefined}
    >
      {!sito.is_default && (
        <Bottone piccolo nome={t("settings.site.makeHomeOne", { nome: sito.name })} onClick={onDiCasa}>
          {t("settings.site.makeHome")}
        </Bottone>
      )}
      <Bottone
        nome={t("settings.site.fixOne", { nome: sito.name })}
        piccolo
        verso="tenue"
        onClick={onCorreggi}
      >
        {t("settings.site.fix")}
      </Bottone>
      <Bottone
        nome={t("settings.site.removeOne", { nome: sito.name })}
        piccolo
        verso="tenue"
        onClick={onTogli}
      >
        {t("settings.site.remove")}
      </Bottone>
    </Riga>
  )
}

/** Chi ha saltato il primo avvio: l'app cataloga lo stesso, ma non fa le notti. */
function Nessuno({ onAggiungi }: { onAggiungi: () => void }) {
  return (
    <Vuoto perche="settings.site.none.why" titolo="settings.site.none">
      <AzioniDelVuoto>
        <Bottone verso="primario" onClick={onAggiungi}>
          {t("settings.site.add")}
        </Bottone>
      </AzioniDelVuoto>
      <NotaDelVuoto>{t("settings.site.none.enough")}</NotaDelVuoto>
    </Vuoto>
  )
}
