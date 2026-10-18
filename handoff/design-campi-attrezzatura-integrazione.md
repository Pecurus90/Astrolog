# Per Claude Design -- integrazione alla brief "i campi dell'attrezzatura: la lista nuova"

Da Claude Code, 18/10/2026. Due aggiunte alla brief di oggi: le formule, con un esempio, e il
dettaglio del campionamento in Meteo. Il resto della brief non cambia.

## Le regole dei conti del corredo (per i numeri d'esempio e `soglie.js`)

- Rapporto focale = focale effettiva / apertura.
- Scala prevista = 206,265 × pixel (µm) / focale effettiva (mm).
- Dimensione del sensore (mm) = pixel × risoluzione / 1000.
- Campo previsto, per lato = 2·atan(lato del sensore / (2 × focale effettiva)).
- Copertura: diagonale del sensore ≤ cerchio d'immagine del riduttore, o dell'ottica senza
  riduttore.
- Scala di guida = 206,265 × pixel di guida / focale di guida. Con l'OAG la focale di guida è la
  focale effettiva del corredo. Avviso fuori da 0,5-4 "/px (Bruce Waddington, PHD2).
- Rapporto guida/ripresa = scala di guida / scala prevista.
- Campionamento sul corredo: "ottimo con seeing fra {2 × scala} e {3 × scala}"" (Nyquist,
  Astronomy Tools).
- Backfocus = spessore di OAG + ruota + distanziali + camera, contro il richiesto del riduttore (o
  dell'ottica senza riduttore). Differenza in mm.
- Carico = somma dei pesi di ottica, camera, riduttore, ruota, focheggiatore, guida, camera di
  guida, distanziali / carico più alto della montatura × 100.
- Potere risolutore dell'ottica = 116 / apertura (mm) (Dawes, Astronomy Tools).

## Esempio: "Notte in quota" (Askar FRA400 + ZWO ASI2600MM Pro)

Dati: Askar FRA400, 72 mm, 400 mm. ASI2600MM Pro, 3,76 µm, 6248 × 4176 px. Guida: tubo da
120 mm, camera di guida da 3,75 µm.

- rapporto focale f/5,6
- scala 1,94 "/px
- sensore 23,5 × 15,7 mm
- campo 3,36° × 2,25°
- potere risolutore 1,61"
- campionamento: ottimo con seeing fra 3,9 e 5,8"
- scala di guida 6,45 "/px, fuori da 0,5-4: **avviso**
- rapporto guida/ripresa 3,3×
- con l'OAG al posto del tubo: scala di guida 1,93 "/px, rapporto 1,0×, niente avviso

## Meteo: il campionamento, nel dettaglio

Per ogni corredo, col seeing previsto della notte:

- **sottocampionato**: la scala supera metà del seeing;
- **sovracampionato**: la scala è sotto un terzo del seeing;
- **ottimo**: in mezzo.

Esempio, "Notte in quota" (1,94 "/px):

- seeing previsto 2,5": sottocampionato;
- seeing previsto 4,5": ottimo.

Il seeing è quello che Meteo mostra già per la notte: la media delle ore che hanno un numero.
Senza chiave Meteoblue il seeing non c'è, e la riga non compare.
