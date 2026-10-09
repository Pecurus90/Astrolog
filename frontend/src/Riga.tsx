import type { ReactNode } from "react"

import { numero, t } from "./i18n"

/**
 * I pezzi di una riga di elenco: la riga stessa, il dettaglio che le sta accanto e la prova presa
 * dai file. Nasce per *Da confermare*, dove serve tutta; la usa anche chi elenca e basta.
 *
 * Vincolo non ovvio: le classi del foglio si scrivono **qui e in nessun altro posto**. Le dodici
 * sezioni le scrivevano a mano -- ventiquattro volte `as-riga__conteggio`, quattro
 * `as-riga__prova` -- e il giorno che il design ne rinomina una sarebbero state ventotto
 * correzioni, di cui nessuna macchina avrebbe segnalato le dimenticate.
 *
 * La forma di una riga, e cosa il foglio si aspetta, stanno nell'intestazione di `Riga`.
 */

// "errore" nasce con la sezione Cartelle: una riga che dice **non si raggiunge** porta il filo
// d'allarme a sinistra, e il colore non e' l'unico segno -- accanto al nome c'e' la parola.
type Stato = "risposta" | "errore"

/**
 * Il dettaglio secondario di una riga: quanti frame, che fuso ci si aspettava, cosa si e' gia'
 * risposto. Scritto piccolo e tenue, accanto al nome.
 *
 * Sta qui e non in dodici file perche' la classe e' una sola: scriverla a mano ogni volta voleva
 * dire dodici posti da correggere il giorno che il foglio la rinomina.
 */
export function Dettaglio({ children }: { children: ReactNode }) {
  return <span className="as-riga__conteggio">{children}</span>
}

/**
 * La **prova che viene dai file**: la sigla dell'header da cui la domanda nasce
 * (`TELESCOP = "80/480"`, `DATE-OBS` contro l'ora locale). E' cio' che rende una domanda
 * verificabile invece che un'imposizione, e per questo si scrive col carattere delle cifre su un
 * fondo incavato: si vede che e' un pezzo di file, non una frase dell'app.
 */
export function Prova({ children }: { children: ReactNode }) {
  return <span className="as-riga__prova">{children}</span>
}

/**
 * Una riga di elenco: un nome, cio' che si sa di lui, e cosa si puo' farci.
 *
 * Esiste perche' le dodici sezioni di *Da confermare* la scrivevano dodici volte -- e' li' che
 * serve tutta, con le risposte e il perche'. Una riga con il solo nome resta una riga valida, ma
 * chi elenca dentro il corpo di una carta non la usa: il padding sarebbe doppio.
 *
 * - **Il nome viene per primo, e nient'altro prima di lui.** Le prove trovano una riga dal testo
 *   con cui comincia (`tests/banco.tsx`), e chi usa un lettore di schermo la riconosce allo stesso
 *   modo: un conteggio o un'icona messi davanti la renderebbero irriconoscibile a tutti e due.
 * - **Fra il nome e il primo dettaglio c'e' uno spazio scritto**, non solo il `gap` della griglia:
 *   a vedersi sarebbero uguali, ma nel testo della riga -- che e' cio' che leggono le prove e chi
 *   ascolta -- senza quello spazio il nome e il conteggio si attaccano (`46.10,12.00391 frame`).
 * - **Lo stato non e' solo un colore** (WCAG 2.2, 1.4.1): *risposta* e' una **barra piena** a
 *   sinistra, una forma, non una tinta. Gli altri due stati che il foglio conosce -- l'errore a
 *   righe oblique e il caricamento velato -- nascono quando una sezione ne avra' bisogno: scriverli
 *   adesso vorrebbe dire tre rami che nessuno percorre.
 * - **Le risposte stanno nella loro colonna**: `.as-riga` e' una griglia, e cio' che si puo' fare
 *   va dentro `.as-riga__risposte` o finisce in mezzo alla prosa.
 * - **Il perche' e' un contenitore, non un paragrafo**: ci sta della prosa, ma anche un elenco di
 *   esempi presi dai file -- e un `<ul>` dentro un `<p>` il browser lo butta fuori dal paragrafo.
 */
export function Riga({
  nome,
  nomeDiCatalogo = false,
  frames,
  dettagli,
  perche,
  stato,
  children,
  comparsa,
}: {
  nome: ReactNode
  /** Un oggetto del cielo si scrive col colore freddo: e' un nome di catalogo, non una sigla. */
  nomeDiCatalogo?: boolean
  /** Quanti frame: la cosa che **ogni** domanda per gruppo mostra, e che dodici sezioni
   *  scrivevano uguale. Si passa il numero, non la frase gia' fatta. */
  frames?: number | undefined
  /** Cio' che quella domanda ha **di suo**, dopo i frame e il cielo. */
  dettagli?: ReactNode
  /** Perche' l'app lo chiede: prosa, o gli esempi presi dai file. */
  perche?: ReactNode
  // `| undefined` scritto a mano, come in `Scelte.tsx`: con `exactOptionalPropertyTypes` un
  // opzionale non accetta un `undefined` passato apposta, ed e' proprio cosi' che una riga dice
  // "nessuno stato".
  stato?: Stato | undefined
  /** Cosa si puo' fare: bottoni, scelte piccole. Sta nella colonna a destra. */
  children?: ReactNode
  /** Un pannello che si apre *dentro* la riga -- una scheda, una ricerca -- e che prende tutta la
   *  larghezza sotto le risposte. Sta nel flusso e non sopra: in posizione assoluta coprirebbe le
   *  righe sotto, e sull'ultima non ci sarebbe niente da coprire. */
  comparsa?: ReactNode
}) {
  return (
    <div
      className={
        stato === "risposta"
          ? "as-riga as-riga--risposta"
          : stato === "errore"
            ? "as-riga as-riga--errore"
            : "as-riga"
      }
    >
      <div className="as-riga__testa">
        <span className={nomeDiCatalogo ? "as-riga__nome as-riga__nome--oggetto" : "as-riga__nome"}>
          {nome}
        </span>{" "}
        {frames !== undefined && <Dettaglio>{t("review.frames", { n: numero(frames) })}</Dettaglio>}{" "}
        {dettagli}
      </div>
      {perche && <div className="as-riga__perche">{perche}</div>}
      {children && <div className="as-riga__risposte">{children}</div>}
      {comparsa}
    </div>
  )
}
