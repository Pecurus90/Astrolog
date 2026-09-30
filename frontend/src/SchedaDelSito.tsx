import { useEffect, useRef, useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Dialogo } from "./Dialogo"
import type { ClasseDiCielo } from "./ScalaDelCielo"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"
import { CampiDelSito, CercaIlPosto, SceltaDelCielo, useCampiDelSito } from "./sito"

type Sito = components["schemas"]["SiteOut"]

/**
 * La scheda di **un** sito: quella con cui nasce e quella con cui si corregge, che sono la stessa.
 *
 * - **Nascere e correggere differiscono in tre punti** -- la ricerca del posto, il verbo dell'API,
 *   il tasto per toglierlo -- e scritte come due carte erano sessanta righe gemelle: il giorno che
 *   il piede cambia, una delle due resta indietro e nessuna macchina dice quale.
 * - **Un sito che tiene delle notti non si toglie di nascosto**: la rotta rifiuta dicendo quante,
 *   e quella frase si legge **dentro il dialogo**, dove si e' premuto.
 */
export function SchedaDelSito({
  sito,
  primo,
  onAnnulla,
  onSalvato,
  onTogli,
}: {
  /** Assente quando il sito nasce. */
  sito?: Sito
  /** Il primo sito e' di casa per forza: senza uno di casa le notti non nascono. */
  primo?: boolean
  onAnnulla: () => void
  onSalvato: () => void
  /** Solo su un sito che esiste gia'. */
  onTogli?: () => void
}) {
  const campi = useCampiDelSito(
    sito && {
      nome: sito.name,
      lat: String(sito.latitude),
      lon: String(sito.longitude),
      ...(sito.bortle === null ? {} : { cielo: sito.bortle as ClasseDiCielo }),
    },
  )
  const [rotto, setRotto] = useState(false)
  const [salvando, setSalvando] = useState(false)

  // **Il fuoco entra nella scheda.** Si apre in fondo alla sezione, fuori dalla vista e lontano
  // dal tasto che l'ha aperta: chi naviga col tabulatore o ascolta non saprebbe che e' comparsa,
  // e continuerebbe a scorrere l'elenco. Si porta sul titolo, che dice quale scheda e' -- non sul
  // primo campo, che direbbe solo "Nome del sito" senza dire di cosa.
  const titolo = useRef<HTMLHeadingElement>(null)
  useEffect(() => titolo.current?.focus(), [])

  // Due schede possono stare aperte insieme -- si corregge un sito mentre se ne aggiunge un altro
  // -- e due campi con lo stesso `id` darebbero il fuoco dell'etichetta a quello sbagliato.
  const quale = sito ? "sito-correggi" : "sito-nuovo"

  const salva = async () => {
    setSalvando(true)
    const { error } = sito
      ? await api.PATCH("/api/v1/sites/{site_id}", {
          params: { path: { site_id: sito.id } },
          body: campi.corpo(),
        })
      : await api.POST("/api/v1/sites", { body: { ...campi.corpo(), is_default: primo === true } })
    setSalvando(false)
    setRotto(Boolean(error))
    if (!error) onSalvato()
  }

  return (
    <section className="as-carta">
      <div className="as-carta__intestazione">
        <div>
          {sito && <p className="as-soprattitolo">{sito.name}</p>}
          <h2 className="as-carta__titolo" ref={titolo} tabIndex={-1}>
            {t(sito ? "settings.site.fix.title" : "settings.site.add.title")}
          </h2>
          <p className="as-carta__domanda">
            {t(sito ? "settings.site.fix.what" : "settings.site.add.what")}
          </p>
        </div>
      </div>
      <div className="as-carta__corpo as-carta__corpo--colonna">
        {/* Si cerca solo quando il sito nasce: correggendone uno, il punto c'e' gia' e una
            ricerca lo sostituirebbe invece di aggiustarlo. */}
        {!sito && (
          <CercaIlPosto
            aMano={() => document.getElementById(`${quale}-name`)?.focus()}
            id="sito-cerca"
            onScegli={campi.prendiDa}
          />
        )}
        <CampiDelSito campi={campi} id={quale} />
        <SceltaDelCielo cielo={campi.cielo} onScegli={campi.setCielo} />
        {rotto && <Avviso esito="allarme">{t("settings.site.saveFailed")}</Avviso>}
      </div>
      <div className="as-carta__piede">
        {onTogli && (
          <Bottone piccolo verso="distruttivo" onClick={onTogli}>
            {t("settings.site.remove")}
          </Bottone>
        )}
        {/* Salvare e annullare stanno **in coda**, lontano dal tasto che toglie: `auto` a sinistra
            li spinge li' qualunque sia la larghezza. */}
        <div style={{ marginLeft: "auto", display: "flex", gap: "var(--spazio-2)" }}>
          <Bottone verso="nudo" onClick={onAnnulla}>
            {t("settings.site.cancel")}
          </Bottone>
          <Bottone
            disabled={!campi.valido || salvando}
            verso="primario"
            onClick={() => void salva()}
          >
            {t("settings.site.save")}
          </Bottone>
        </div>
      </div>
    </section>
  )
}

/** Togliere un sito, col dialogo che dice cosa succede. */
export function TogliIlSito({
  sito,
  onChiudi,
  onTolto,
}: {
  sito: Sito
  onChiudi: () => void
  onTolto: () => void
}) {
  const [conNotti, setConNotti] = useState<number>()
  const [rotto, setRotto] = useState(false)
  const [togliendo, setTogliendo] = useState(false)

  const togli = async () => {
    setTogliendo(true)
    const { error } = await api.DELETE("/api/v1/sites/{site_id}", {
      params: { path: { site_id: sito.id } },
    })
    setTogliendo(false)
    if (!error) {
      onTolto()
      onChiudi()
      return
    }
    // La rotta rifiuta con quante notti lo tengono: e' un fatto da mostrare, non un guasto. Il
    // dialogo resta aperto -- chiuderlo porterebbe via la ragione insieme alla domanda.
    const quante = (error as { detail?: { nights?: number } }).detail?.nights
    setConNotti(quante)
    setRotto(quante === undefined)
  }

  return (
    <Dialogo
      azioni={
        <>
          <Bottone verso="nudo" onClick={onChiudi}>
            {t("settings.site.cancel")}
          </Bottone>
          <Bottone disabled={togliendo} verso="distruttivo" onClick={() => void togli()}>
            {t("settings.site.removeIt")}
          </Bottone>
        </>
      }
      onChiudi={onChiudi}
      titolo={t("settings.site.confirm", { nome: sito.name })}
    >
      <p className="as-dialogo__testo">{t("settings.site.confirm.what")}</p>
      {conNotti !== undefined && (
        <Avviso esito="allarme" titolo={t("settings.site.hasNightsTitle")}>
          {t("settings.site.hasNights", { n: numero(conNotti) })}
        </Avviso>
      )}
      {rotto && <Avviso esito="allarme">{t("settings.site.removeFailed")}</Avviso>}
    </Dialogo>
  )
}
