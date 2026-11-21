import { Component, type ReactNode, Suspense } from "react"
import { useLocation } from "react-router"

import { Avviso } from "./componenti/Avviso"
import { Finestra } from "./componenti/Finestra"
import { useFormato } from "./componenti/formato"
import { Pagina } from "./componenti/Pagina"
import { t } from "./i18n"
import { PaginaNonArrivata } from "./pigra"
import { AvvisoDiAvvio } from "./PrimoAvvioCornice"

/**
 * Dove vanno a schermo i componenti di `pigra`: mentre il file arriva resta il telaio, e se non
 * arriva un riquadro lo dice, invece della pagina bianca (passo 6.17.1). Con `onChiudi` chi
 * l'ha chiesto e' una finestra: il riquadro e' una finestra anch'esso, sopra la pagina, e si chiude.
 *
 * Riprova ricarica l'app: dopo un aggiornamento il file ha un altro nome, e solo la pagina nuova
 * lo conosce (vite.dev/guide/build, "Load Error Handling"). Un'altra pagina toglie il riquadro.
 */
export function Pigre({
  children,
  attesa,
  onChiudi,
  fuoriDalTelaio = false,
}: {
  children: ReactNode
  attesa?: ReactNode
  onChiudi?: () => void
  /** The first start has no frame: the notice sits in its column, not on the window's edges. */
  fuoriDalTelaio?: boolean
}) {
  const dove = useLocation().pathname
  return (
    <Confine dove={dove} onChiudi={onChiudi} fuoriDalTelaio={fuoriDalTelaio}>
      <Suspense fallback={attesa}>{children}</Suspense>
    </Confine>
  )
}

type Dati = {
  dove: string
  onChiudi: (() => void) | undefined
  fuoriDalTelaio: boolean
  children: ReactNode
}

class Confine extends Component<Dati, { errore: unknown }> {
  override state: { errore: unknown } = { errore: undefined }

  static getDerivedStateFromError(errore: unknown) {
    return { errore }
  }

  override componentDidUpdate(prima: { dove: string }) {
    if (prima.dove !== this.props.dove && this.state.errore !== undefined)
      this.setState({ errore: undefined })
  }

  override render() {
    const { errore } = this.state
    if (errore === undefined) return this.props.children
    // a fault of the page itself goes on up: saying "network" here would hide it
    if (!(errore instanceof PaginaNonArrivata)) throw errore
    return <NonCaricata onChiudi={this.props.onChiudi} fuoriDalTelaio={this.props.fuoriDalTelaio} />
  }
}

function NonCaricata({
  onChiudi,
  fuoriDalTelaio,
}: {
  onChiudi: (() => void) | undefined
  fuoriDalTelaio: boolean
}) {
  const formato = useFormato()
  const riprova = () => window.location.reload()
  if (fuoriDalTelaio)
    return (
      <AvvisoDiAvvio
        titolo={t("lazy.failed")}
        testo={t("lazy.failed.why")}
        azione={t("lazy.retry")}
        onAzione={riprova}
      />
    )
  if (onChiudi)
    return (
      <Finestra
        titolo={t("lazy.failed")}
        segno="!"
        larghezza="stretta"
        formato={formato}
        onChiudi={onChiudi}
      >
        <p className="al-finestra__testo">{t("lazy.failed.why")}</p>
        <div className="al-finestra__gesti">
          <button type="button" className="al-bottone al-bottone--contorno" onClick={riprova}>
            {t("lazy.retry")}
          </button>
        </div>
      </Finestra>
    )
  return (
    <Pagina formato={formato}>
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("lazy.failed")}
        testo={t("lazy.failed.why")}
        azione={t("lazy.retry")}
        onAzione={riprova}
      />
    </Pagina>
  )
}
