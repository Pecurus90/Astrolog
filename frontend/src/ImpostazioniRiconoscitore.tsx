import { useMutation } from "@tanstack/react-query"
import type { ReactNode } from "react"

import { Avviso, type SegnoAvviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Scheletro } from "./componenti/Scheletro"
import { Tema, type Formato } from "./componenti/Tema"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"
import { DOVE_SI_SCARICA, useDoveStaASTAP, useSolver } from "./riconoscitore"

type Solver = components["schemas"]["SolverOut"]

// What each star catalogue is for (tavola `CD`, ADR 0036); a code without a line shows none.
const CATALOGHI: Record<string, Chiave> = {
  d05: "settings.solver.cat.d05",
  d50: "settings.solver.cat.d50",
  d80: "settings.solver.cat.d80",
}

/**
 * **ASTAP** (tavola Impostazioni v82, 140-149 and 343-358): where it comes from, the path with
 * Verifica percorso and Cercalo tu, the catalogues found by file name.
 *
 * - **Verifica percorso writes it**: the backend tells whether the program is there only of the
 *   path it has; a wrong path stays declared and the outcome says so.
 * - **Cercalo tu proposes, it does not write**: Usa questo percorso is a gesture of its own.
 */
export function Riconoscitore() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const solver = useSolver()
  let corpo
  if (solver.isPending) {
    corpo = (
      <Scheletro
        formato={formato}
        testo={t("settings.solver.loading")}
        griglia={tel ? "minmax(0,1fr)" : "repeat(12,minmax(0,1fr))"}
        carte={[{ h: "420px", blocchi: [{ h: "24px", w: "200px" }, { flex: "1" }] }]}
        gap={tel ? "12px" : "16px"}
      />
    )
  } else if (solver.isError) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("settings.solver.failed")}
        azione={t("settings.retry")}
        onAzione={() => void solver.refetch()}
      />
    )
  } else {
    // mounted once the declared path is here: the field reads it once, at birth
    corpo = <CartaASTAP formato={formato} solver={solver.data} />
  }
  return (
    <Tema>
      <div className={tel ? "al-imp__colonna-18" : "al-imp__griglia-2"}>{corpo}</div>
    </Tema>
  )
}

function CartaASTAP({ formato, solver }: { formato: Formato; solver: Solver }) {
  const tel = formato === "telefono"
  // the field starts from what the user declared, not from what the app found
  const dove = useDoveStaASTAP(solver.declared ?? "")
  const cerca = useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST("/api/v1/solver/search", {})
      if (error) throw new Error(t("settings.solver.searchFailed"))
      return data
    },
  })
  const proposto = cerca.data
  const trovato =
    proposto?.path != null ? (
      <Avviso
        tipo="blocco"
        formato={formato}
        segno="?"
        titolo={t("settings.solver.searchedFound", { percorso: proposto.path })}
        testo={t("settings.solver.searchedKeeps")}
        azione={t("settings.solver.adopt")}
        onAzione={() => {
          dove.adotta(proposto.path as string)
          cerca.reset()
        }}
      />
    ) : proposto ? (
      <Avviso
        tipo="blocco"
        formato={formato}
        segno="!"
        titolo={t("settings.solver.searchedNothing")}
      />
    ) : cerca.error ? (
      <Avviso tipo="blocco" formato={formato} segno="!" titolo={cerca.error.message} />
    ) : null
  const esito = esitoDelPercorso(dove, solver)
  const riga = esito && <Avviso tipo="blocco" formato={formato} {...esito} />
  const campo = (
    <input
      value={dove.path}
      onChange={(e) => {
        dove.setPath(e.target.value)
        dove.dimentica()
        cerca.reset()
      }}
      onBlur={dove.manda}
      aria-label={t("solver.label")}
      placeholder={t("solver.placeholder")}
      spellCheck={false}
      className={tel ? "al-campo" : "al-campo al-imp__blocco-13"}
    />
  )
  const verifica = (
    <a
      href="#"
      role="button"
      onClick={gesto(dove.manda)}
      aria-disabled={dove.path && !dove.salva.isPending ? "false" : "true"}
      className={
        tel
          ? "al-bottone al-bottone--contorno al-bottone--blocco"
          : "al-bottone al-bottone--contorno al-bottone--blocco al-bottone--a-sinistra"
      }
    >
      {t(dove.salva.isPending ? "settings.solver.checking" : "solver.use")}
    </a>
  )
  const cercalo = (
    <a
      href="#"
      role="button"
      onClick={gesto(() => !cerca.isPending && cerca.mutate())}
      className={
        tel ? "al-bottone al-bottone--testo al-bottone--blocco" : "al-bottone al-bottone--testo"
      }
    >
      {t(cerca.isPending ? "settings.solver.searching" : "settings.solver.search")}
    </a>
  )
  // on a NAS only ASTROLOG_ASTAP picks it (#95): the path is read, not written
  const admin = solver.set_by_admin
  const sola = admin && solver.path !== null && (
    <span className="al-imp__testo-7">{solver.path}</span>
  )
  const canale = t(admin ? "settings.solver.channel.admin" : "settings.solver.channel")
  const canaleSotto = t(admin ? "settings.solver.channel.admin.sub" : "settings.solver.channel.sub")
  const cataloghi = solver.path !== null && <Cataloghi formato={formato} quali={solver.databases} />
  return (
    <Carta
      formato={formato}
      colonne={12}
      ritardo={0}
      padding={tel ? "20px" : "24px 28px"}
      gap={tel ? 12 : 14}
      etichetta={t("settings.solver")}
    >
      {tel ? (
        <>
          <span className="al-imp__testo-27">{t("settings.solver")}</span>
          <span className="al-imp__testo-5">{t("settings.solver.what")}</span>
          <span className="al-imp__colonna-1">
            <span className="al-imp__testo-5">{t("settings.solver.from")}</span>
            <b className="al-imp__testo-7">{canale}</b>
            <span className="al-imp__testo-8">{canaleSotto}</span>
          </span>
          <span className="al-imp__testo-5">{t("settings.solver.path")}</span>
          {admin ? (
            sola
          ) : (
            <>
              {campo}
              {verifica}
              {cercalo}
            </>
          )}
          {trovato}
          {riga}
          {cataloghi}
          <span className="al-imp__testo-8">{t("settings.solver.advice")}</span>
          <a className="al-imp__riga-38" href={DOVE_SI_SCARICA} target="_blank" rel="noopener">
            {t("settings.solver.site")}
          </a>
        </>
      ) : (
        <>
          <span className="al-imp__riga-6">
            <span className="al-imp__testo-3">{t("settings.solver")}</span>
            <span className="al-imp__testo-5">{t("settings.solver.sub.card")}</span>
          </span>
          <Voce etichetta={t("settings.solver.from")}>
            <span className="al-imp__colonna-1">
              <b className="al-imp__testo-7">{canale}</b>
              <span className="al-imp__testo-8">{canaleSotto}</span>
            </span>
          </Voce>
          <Voce etichetta={t("settings.solver.path")}>
            <span className="al-imp__colonna-9">
              {admin ? (
                sola
              ) : (
                <>
                  <span className="al-imp__riga-4">
                    {campo}
                    {verifica}
                    {cercalo}
                  </span>
                  <span className="al-imp__testo-8">{t("settings.solver.pathHelp")}</span>
                </>
              )}
              {trovato}
              {riga}
            </span>
          </Voce>
          {cataloghi}
          <span className="al-imp__testo-16">{t("settings.solver.advice")}</span>
          <a className="al-imp__blocco-14" href={DOVE_SI_SCARICA} target="_blank" rel="noopener">
            {t("settings.solver.site")}
          </a>
        </>
      )}
    </Carta>
  )
}

function Voce({ etichetta, children }: { etichetta: string; children: ReactNode }) {
  return (
    <div className="al-imp__griglia-6">
      <span className="al-imp__blocco-12">{etichetta}</span>
      {children}
    </div>
  )
}

type Esito = { segno: SegnoAvviso; titolo: string; testo?: string }

/** The outcome under the path: of the write just made, else of where the app takes ASTAP now. */
function esitoDelPercorso(dove: ReturnType<typeof useDoveStaASTAP>, solver: Solver): Esito | null {
  if (dove.salva.error) return { segno: "!", titolo: dove.salva.error.message }
  if (dove.esito === "notThere") {
    return {
      segno: "!",
      titolo: t("settings.solver.notThere"),
      testo: t("settings.solver.notThere.why"),
    }
  }
  if (dove.esito) {
    return {
      segno: "\u2713",
      titolo: t("solver.foundTitle"),
      testo: t(dove.esito === "found" ? "solver.found" : "solver.foundNoDatabase"),
    }
  }
  if (dove.path !== (solver.declared ?? "")) return null
  if (solver.path === null && solver.wrong_env != null) {
    return {
      segno: "!",
      titolo: t("settings.solver.wrongEnv", { percorso: solver.wrong_env }),
      // on a NAS there is no Cercalo tu nor a path to choose: the variable is the admin's
      testo: solver.set_by_admin
        ? t("settings.solver.channel.admin.sub")
        : t("settings.solver.wrongEnv.why"),
    }
  }
  if (solver.path === null) {
    return solver.declared !== null
      ? {
          segno: "!",
          titolo: t("settings.solver.notThere"),
          testo: t("settings.solver.notThere.why"),
        }
      : { segno: "!", titolo: t("settings.solver.none"), testo: t("solver.without") }
  }
  return {
    segno: "\u2713",
    titolo: t("solver.foundTitle"),
    testo: t("settings.solver.foundAt", {
      percorso: solver.path,
      come: solver.source ? t(`settings.solver.from.${solver.source}`) : "",
    }),
  }
}

/** The catalogues found next to ASTAP, one a row; none is a row of its own. */
function Cataloghi({ formato, quali }: { formato: Formato; quali: readonly string[] }) {
  const tel = formato === "telefono"
  const righe = quali.length
    ? quali.map((q) => ({
        k: q,
        l: t("settings.solver.cat", { nome: q.toUpperCase() }),
        ok: true,
        d: CATALOGHI[q] ? t(CATALOGHI[q]) : "",
      }))
    : [{ k: "", l: t("settings.solver.cats"), ok: false, d: t("settings.solver.cats.none.why") }]
  return righe.map((r) => {
    const pillola = (
      <span
        className={tel ? "al-imp__pillola-3" : "al-imp__riga-13"}
        style={
          r.ok
            ? { background: "var(--buono-fondo)", color: "var(--buono-testo)" }
            : { background: "var(--carta-2)", color: "var(--testo)" }
        }
      >
        {t(r.ok ? "settings.solver.cat.found" : "settings.solver.cats.none")}
      </span>
    )
    return tel ? (
      <div key={r.k} className="al-imp__colonna-23">
        <span className="al-imp__riga-39">
          <span className="al-imp__testo-17">{r.l}</span>
          {pillola}
        </span>
        {r.d && <span className="al-imp__testo-8">{r.d}</span>}
      </div>
    ) : (
      <div key={r.k} className="al-imp__griglia-7">
        <span className="al-imp__testo-2">{r.l}</span>
        <span className="al-imp__riga-12">{pillola}</span>
        <span className="al-imp__testo-5">{r.d}</span>
      </div>
    )
  })
}
