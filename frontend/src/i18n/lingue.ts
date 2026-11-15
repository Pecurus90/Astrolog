/**
 * Le lingue attive dell'app, **in un posto solo**.
 *
 * La guardia delle traduzioni legge da qui: aggiungere una lingua e' cambiare questa riga e far
 * girare il `traduttore`, non toccare N file sparsi. Si costruisce in italiano -- e' la lingua
 * sorgente, quella che l'autore scrive -- e una pagina finita si traduce in un colpo.
 *
 * Le altre (de, fr, es) arrivano quando un utente le chiede: e' un giro del traduttore, non un
 * progetto.
 */
export const LINGUE = ["it", "en"] as const

export type Lingua = (typeof LINGUE)[number]

/** Each language by its own name, the same in every language: who cannot read the current one
 *  still finds theirs (Impostazioni, Lingua). */
export const NOMI_LINGUE: Record<Lingua, string> = { it: "Italiano", en: "English" }

/** La lingua in cui si scrive: i suoi valori sono la sorgente, le altre sono traduzioni. */
export const LINGUA_SORGENTE: Lingua = "it"
