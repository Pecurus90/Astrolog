import { BrowserRouter, Route, Routes } from "react-router"

import { Avviso } from "./Avviso"
import { RipristinoProposto, useBackup } from "./Backup"
import { Layout } from "./Layout"
import { PaginaCheNonCe } from "./PaginaCheNonCe"
import { Wizard } from "./Wizard"
import { t } from "./i18n"
import { APERTE, sezioniAperte } from "./pagine"
import { usePreferenze } from "./preferenze"

/**
 * Il portiere dell'app: prima il **cancelletto** del primo avvio, poi la navigazione.
 *
 * - Senza il timbro non c'e' niente da navigare, e una barra laterale al primo avvio inviterebbe
 *   a girare per un'app che non sa ancora da dove osservi.
 * - Le pagine sono **indirizzi**, non stati: e' l'indirizzo che fa funzionare il tasto indietro e
 *   un collegamento che si manda a qualcuno. Sul NAS l'app si apre da tablet, dove il gesto
 *   indietro **e'** la navigazione: senza, si esce dall'app.
 * - Le pagine **montano** solo dopo il cancelletto, quindi non serve spegnere le loro chiamate a
 *   mano: cio' che non e' montato non chiede niente.
 * - **Quali pagine esistono lo dice `pagine.tsx`**, che e' la casa sola dello scheletro: qui si
 *   montano le rotte di quelle aperte, e il `Layout` ne fa la barra.
 */

export function App() {
  const settings = usePreferenze()
  const backup = useBackup()

  // Finche' non si sa, non si sceglie: mostrare l'app e poi sostituirla col primo avvio sarebbe
  // uno sfarfallio che dice due cose diverse in mezzo secondo. E se la domanda non ha risposta
  // non si tira a indovinare: mostrare l'app direbbe "tutto configurato" senza saperlo.
  if (settings.isPending || backup.isPending) return <p>{t("app.loading")}</p>
  if (settings.error) return <Avviso esito="allarme">{settings.error.message}</Avviso>
  // Un database nuovo con le risposte accanto: prima si chiede se rimetterle, poi il primo avvio
  // (che, rimesse, non serve piu'). Se lo stato del backup non si sa, si va avanti senza.
  if (backup.data?.offer === "found") return <RipristinoProposto stato={backup.data} />
  if (settings.data && !settings.data.wizard_done) {
    // `missing` dice cosa manca all'app: il primo avvio guarda il **riconoscitore** -- il
    // programma, e il suo catalogo -- per decidere se fare la domanda in piu', e quale.
    return (
      <Wizard onDone={() => void settings.refetch()} manca={settings.data.missing} />
    )
  }

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          {APERTE.map((p) => (
            <Route key={p.a} path={p.a} element={p.elemento} />
          ))}
          {/* Le sezioni sono indirizzi veri, non ancore: il tasto indietro funziona e il
              collegamento si manda. Portano tutte alla stessa pagina, che legge dall'indirizzo
              quale sezione mostrare. */}
          {APERTE.flatMap((p) =>
            sezioniAperte(p.sezioni).map((s) => <Route key={s.a} path={s.a} element={p.elemento} />),
          )}
          <Route path="*" element={<PaginaCheNonCe />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
