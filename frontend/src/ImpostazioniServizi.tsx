import { ChiaveMeteoblue } from "./ChiaveMeteoblue"
import { t } from "./i18n"

/**
 * La sezione **Servizi**: le chiavi personali dei servizi che l'app interroga. Oggi quella di
 * Meteoblue, per il seeing ora per ora; senza, il seeing non c'e' e il resto funziona uguale.
 */
export function Servizi() {
  return (
    <section className="as-carta">
      <div className="as-carta__intestazione">
        <div>
          <h2 className="as-carta__titolo">{t("settings.services.title")}</h2>
          <p className="as-carta__domanda">{t("settings.services.what")}</p>
        </div>
      </div>
      <div className="as-carta__corpo as-carta__corpo--colonna">
        <ChiaveMeteoblue id="settings-meteoblue-key" />
      </div>
    </section>
  )
}
