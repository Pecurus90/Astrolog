import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import { App } from "./App"
// Il foglio della consegna: dentro, prima i token e poi i mattoni che li leggono.
import "./stili/astrolog.css"
// e in coda il poco che e' nostro: la catena delle altezze fino al nodo radice.
import "./stili/app.css"

// La casa dei dati che arrivano dall'API: una sola, e le pagine ci chiedono dentro. Senza,
// ogni schermo si porterebbe il suo stato di caricamento e le sue copie -- e due parti della
// stessa pagina potrebbero mostrare due versioni dello stesso numero.
const dati = new QueryClient()

const radice = document.getElementById("root")
if (!radice) {
  // La pagina la serve il backend da `index.html`: se questo nodo manca, il file servito non e'
  // quello costruito. Meglio dirlo che disegnare nel vuoto.
  throw new Error("manca il nodo radice: la pagina servita non e' quella costruita")
}

createRoot(radice).render(
  <StrictMode>
    <QueryClientProvider client={dati}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
