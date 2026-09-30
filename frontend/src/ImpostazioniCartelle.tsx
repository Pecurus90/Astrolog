import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Dialogo } from "./Dialogo"
import { Dettaglio, Riga } from "./Riga"
import { SfogliaCartelle } from "./SfogliaCartelle"
import { NotaDelVuoto, Vuoto } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { ScriviPercorso, VistaDellaSonda, useCartelle } from "./cartelle"
import { giorno, numero, t } from "./i18n"
import { useRadiceDati } from "./radiceDati"

type Cartella = components["schemas"]["FolderOut"]

/**
 * La sezione **Cartelle**: quelle che l'app legge, come aggiungerne una, come smettere.
 *
 * Guardare dentro e registrare stanno in `cartelle.tsx`, insieme al primo avvio. Qui c'e' cio'
 * che e' della sezione:
 *
 * - **Togliere e' un ritiro, non una cancellazione**: i frame gia' letti restano in archivio. Lo
 *   dice il dialogo prima, coi numeri veri che manda la rotta.
 * - **Se il ritiro non riesce il dialogo resta aperto**, con l'errore dentro: chiuderlo direbbe
 *   che e' andata, e la cartella e' ancora li'.
 * - **Una cartella irraggiungibile non ferma le altre**: lo dice la sua riga, e i frame che ne
 *   sono gia' entrati restano.
 */
export function Cartelle() {
  const [percorso, setPercorso] = useState("")
  const [daTogliere, setDaTogliere] = useState<Cartella>()
  const [nonTolta, setNonTolta] = useState(false)
  const [togliendo, setTogliendo] = useState(false)
  const cartelle = useCartelle("settings.folders.failed")
  const radice = useRadiceDati()

  const togli = async (quale: Cartella) => {
    setTogliendo(true)
    const { error } = await api.DELETE("/api/v1/folders/{folder_id}", {
      params: { path: { folder_id: quale.id } },
    })
    setTogliendo(false)
    setNonTolta(Boolean(error))
    if (error) return
    setDaTogliere(undefined)
    void cartelle.elenco.refetch()
  }

  const scrivi = (
    <ScriviPercorso
      id="cartella-nuova"
      onGuarda={() => void cartelle.guarda(percorso)}
      onScrivi={setPercorso}
      prefisso="settings.folders"
      valore={percorso}
    />
  )
  const quante = cartelle.elenco.data?.items.length ?? 0

  return (
    <>
      <section className="as-carta">
        <div className="as-carta__intestazione">
          <div>
            <h2 className="as-carta__titolo">{t("settings.folders.title")}</h2>
            <p className="as-carta__domanda">{t("settings.folders.what")}</p>
          </div>
          {quante > 0 && (
            <div className="as-carta__azioni">
              <span className="as-stato as-stato--conteggio">{numero(quante)}</span>
            </div>
          )}
        </div>
        <div className="as-carta__corpo as-carta__corpo--stretto">
          {cartelle.elenco.isError && (
            <Avviso esito="allarme">{t("settings.folders.failed")}</Avviso>
          )}
          {quante === 0 && !cartelle.elenco.isPending && !cartelle.elenco.isError && <Nessuna />}
          {quante > 0 && (
            <ul className="as-elenco">
              {cartelle.elenco.data?.items.map((c) => (
                <li key={c.id}>
                  <Voce cartella={c} onTogli={() => setDaTogliere(c)} />
                </li>
              ))}
            </ul>
          )}
        </div>
        {quante > 0 && (
          <div className="as-carta__piede as-carta__piede--prosa">
            {t("settings.folders.keeps")}
          </div>
        )}
      </section>

      <section className="as-carta">
        <div className="as-carta__intestazione">
          <div>
            <h2 className="as-carta__titolo">{t("settings.folders.add.title")}</h2>
            {/* Sul NAS il percorso non si scrive, si sceglie: dire "come lo vedi nel tuo
                computer" a chi gira in Docker lo porta a sbagliare. */}
            <p className="as-carta__domanda">
              {t(radice === null ? "settings.folders.add.what" : "settings.folders.add.what.nas")}
            </p>
          </div>
        </div>
        <div className="as-carta__corpo as-carta__corpo--colonna">
          {radice === null ? (
            scrivi
          ) : (
            <SfogliaCartelle onGuarda={cartelle.guarda} radice={radice} scrivi={scrivi} />
          )}
          {cartelle.vista && (
            <VistaDellaSonda
              inCorso={cartelle.inCorso}
              onAggiungi={() => {
                setPercorso("")
                void cartelle.aggiungi()
              }}
              prefisso="settings.folders"
              vista={cartelle.vista}
            />
          )}
          {cartelle.rotto && (
            <Avviso esito="allarme">
              {t(
                cartelle.rotto === "guarda"
                  ? "settings.folders.lookFailed"
                  : "settings.folders.addFailed",
              )}
            </Avviso>
          )}
        </div>
      </section>

      {daTogliere && (
        <Dialogo
          azioni={
            <>
              <Bottone verso="nudo" onClick={() => setDaTogliere(undefined)}>
                {t("settings.folders.cancel")}
              </Bottone>
              <Bottone
                disabled={togliendo}
                verso="distruttivo"
                onClick={() => void togli(daTogliere)}
              >
                {t("settings.folders.stop")}
              </Bottone>
            </>
          }
          onChiudi={() => setDaTogliere(undefined)}
          titolo={t("settings.folders.confirm", { percorso: daTogliere.root_path })}
        >
          <p className="as-dialogo__testo">{t("settings.folders.confirm.what")}</p>
          <ul className="as-dialogo__perdi">
            <li>
              <b>{numero(daTogliere.frames)}</b> {t("settings.folders.confirm.frames")}
            </li>
            <li>{t("settings.folders.confirm.files")}</li>
            <li>{t("settings.folders.confirm.stop")}</li>
          </ul>
          {nonTolta && <Avviso esito="allarme">{t("settings.folders.removeFailed")}</Avviso>}
        </Dialogo>
      )}
    </>
  )
}

/** Una cartella nell'elenco: dove sta, se si raggiunge, cosa ne e' entrato, da quando. */
function Voce({ cartella, onTogli }: { cartella: Cartella; onTogli: () => void }) {
  return (
    <Riga
      dettagli={
        <span
          className={["as-stato", cartella.reachable ? "as-stato--buono" : "as-stato--allarme"].join(
            " ",
          )}
        >
          {t(cartella.reachable ? "settings.folders.reachable" : "settings.folders.unreachable")}
        </span>
      }
      nome={cartella.root_path}
      perche={
        <>
          {t(cartella.reachable ? "settings.folders.frames" : "settings.folders.frames.kept", {
            n: numero(cartella.frames),
          })}
          {" \u00B7 "}
          <Dettaglio>
            {t("settings.folders.since", { quando: giorno(cartella.created_at) })}
          </Dettaglio>
        </>
      }
      stato={cartella.reachable ? undefined : "errore"}
    >
      <Bottone piccolo verso="tenue" onClick={onTogli}>
        {t("settings.folders.remove")}
      </Bottone>
    </Riga>
  )
}

/** Chi ha saltato il primo avvio: non e' un guasto, e' una cosa da fare. */
function Nessuna() {
  return (
    <Vuoto perche="settings.folders.none.why" titolo="settings.folders.none">
      <NotaDelVuoto>{t("settings.folders.none.safe")}</NotaDelVuoto>
    </Vuoto>
  )
}
