import { type CSSProperties, type ReactNode, useState } from "react"

import {
  BloccoDelModulo,
  CampoDelModulo,
  Modulo,
  type RigaDelModulo,
  TendinaDelModulo,
  TestoDelModulo,
} from "./componenti/Modulo"
import type { Formato } from "./componenti/Tema"
import { EliminaDelModulo } from "./EliminaDelModulo"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Pagina = components["schemas"]["GearList"]

/** The "altra" value of the Marca drop-down: a maker not written yet. */
export const ALTRA = "__altra__"
const RIELABORA = "↻" // glifo-ok: board glyph

/** A block's count, "{n} di {m} scritti". */
export interface Conto {
  scritti: number
  di: number
}

/**
 * Il **guscio del modulo di una riga** dell'Attrezzatura (tavola v82 `modulo`, k `mod`), comune a
 * un pezzo e a un filtro: nome e marca in testa a "nome e modello", i due blocchi (sul telefono
 * uno aperto alla volta, `passo`), "Unisci a" con le sue righe, i rifiuti prima di Salva, ed
 * Elimina in fondo. I campi propri del tipo li porta chi lo usa.
 */
export function ModuloDellaRiga({
  base,
  titolo,
  disco,
  formato,
  pagina,
  scansione,
  nome,
  onNome,
  marca,
  nuovaMarca,
  origineMarca,
  onMarca,
  onNuovaMarca,
  chi,
  tecnici,
  manca,
  unibili,
  etichettaUnione,
  unione,
  onUnione,
  frame,
  scrittura,
  rifiuto,
  elimina,
  onChiudi,
  campiChi,
  campiTecnici,
}: {
  base: string
  titolo: string
  disco?: CSSProperties
  formato: Formato
  pagina: Pagina
  scansione: boolean
  nome: string
  onNome: (v: string) => void
  marca: string
  nuovaMarca: string
  origineMarca: string | undefined
  onMarca: (v: string) => void
  onNuovaMarca: (v: string) => void
  chi: Conto
  tecnici: Conto
  /** Why Salva waits besides the name ("serve almeno una banda"), empty for none. */
  manca: string
  unibili: { id: number; name: string }[]
  etichettaUnione: string
  unione: string
  /** Choosing or dropping the merge: the caller starts its draft over. */
  onUnione: (v: string) => void
  /** Its frames, which a merge moves. */
  frame: number | null
  scrittura: { onSalva: () => void; occupato: boolean }
  /** The write's refusal, in words. */
  rifiuto: string | null
  elimina: {
    rifiuto: components["schemas"]["DeleteRefused"] | null
    inSetup: components["schemas"]["PieceInRig"][]
    manda: () => Promise<{ error?: unknown }>
  }
  onChiudi: () => void
  campiChi: ReactNode
  campiTecnici: ReactNode
}) {
  const [passo, setPasso] = useState<"chi" | "dati" | null>("chi")
  const [nonEliminato, setNonEliminato] = useState<string | null>(null)
  const verso = unibili.find((o) => String(o.id) === unione)
  const righe: RigaDelModulo[] = []
  if (verso && frame) {
    const testo = t("gear.merge.moves", { n: numero(frame), nome: verso.name })
    righe.push({ segno: RIELABORA, testo, avviso: false })
  }
  if (verso) righe.push({ segno: "!", testo: t("gear.merge.final"), avviso: true })
  const perche = scansione
    ? t("gear.write.scanning")
    : verso
      ? ""
      : !nome.trim()
        ? t("gear.write.needName")
        : manca
  const unisciId = unibili.length > 0 ? `${base}-unisci` : null
  const blocco = (quale: "chi" | "dati", conto: Conto) => ({
    riassunto: t("gear.form.written", { n: numero(conto.scritti), m: numero(conto.di) }),
    formato,
    aperto: passo === quale,
    onApri: (si: boolean) => setPasso(si ? quale : null),
  })
  return (
    <Modulo
      titolo={titolo}
      formato={formato}
      dentro
      blocchi
      {...(disco ? { disco } : {})}
      righe={righe}
      errore={nonEliminato ?? rifiuto}
      salva={{ ...scrittura, spento: perche !== "" }}
      onAnnulla={onChiudi}
      perche={perche}
      elimina={
        <EliminaDelModulo
          nome={titolo}
          pagina={pagina}
          rifiuto={elimina.rifiuto}
          inSetup={elimina.inSetup}
          scansione={scansione}
          salvando={scrittura.occupato}
          unisci={unisciId}
          elimina={elimina.manda}
          onFatto={onChiudi}
          onErrore={setNonEliminato}
        />
      }
    >
      {!verso && (
        <BloccoDelModulo titolo={t("gear.form.who")} {...blocco("chi", chi)}>
          <CampoDelModulo id={`${base}-name`} etichetta={t("gear.write.name")} largo>
            <TestoDelModulo id={`${base}-name`} valore={nome} onValore={onNome} />
          </CampoDelModulo>
          <CampoDelModulo id={`${base}-brand`} etichetta={t("gear.f.brand")} origine={origineMarca}>
            <TendinaDelModulo
              id={`${base}-brand`}
              valore={marca}
              voci={[
                { valore: "", l: "--" },
                ...pagina.brands.map((m) => ({ valore: m, l: m })),
                { valore: ALTRA, l: t("gear.form.otherBrand") },
              ]}
              onValore={onMarca}
            />
          </CampoDelModulo>
          {marca === ALTRA && (
            <CampoDelModulo id={`${base}-newBrand`} etichetta={t("gear.f.newBrand")}>
              <TestoDelModulo id={`${base}-newBrand`} valore={nuovaMarca} onValore={onNuovaMarca} />
            </CampoDelModulo>
          )}
          {campiChi}
        </BloccoDelModulo>
      )}
      {!verso && (
        <BloccoDelModulo titolo={t("gear.form.tech")} {...blocco("dati", tecnici)}>
          {campiTecnici}
        </BloccoDelModulo>
      )}
      {unisciId && (
        <section
          className="al-c-modulo__colonna-4"
          style={{ gridColumn: "1 / -1", background: "transparent", padding: 0 }}
        >
          <div className="al-c-modulo__griglia-1">
            <CampoDelModulo id={unisciId} etichetta={etichettaUnione}>
              <TendinaDelModulo
                id={unisciId}
                valore={unione}
                voci={[
                  { valore: "", l: "--" },
                  ...unibili.map((o) => ({ valore: String(o.id), l: o.name })),
                ]}
                onValore={onUnione}
              />
            </CampoDelModulo>
          </div>
        </section>
      )}
    </Modulo>
  )
}
